from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from datetime import timedelta, datetime
from decimal import Decimal
from .decorators import (
    super_admin_required, admin_required, staff_or_super_admin_required,
    user_management_required, check_user_permissions, get_user_admin_context
)
from .models import (
    Book, Loan, Reservation, CustomUser, Genre, Author,
    BookPurchase, Payment, Deposit, LibraryConfig, Favorite, Delivery
)
from .forms import (
    BookSearchForm, UserRegistrationForm, BookCoverUploadForm,
    BookPurchaseForm, PaymentForm, QuickLoanForm, DeliveryForm, DeliveryTrackingForm
)
from .payment_services import PaymentService, PaymentCalculator, PaymentValidator
from .reservation_services import ReservationService, NotificationService, ReservationValidator


def home(request):
    """Page d'accueil"""
    recent_books = Book.objects.filter(available_copies__gt=0).order_by('-added_date')[:6]
    popular_genres = Genre.objects.annotate(book_count=Count('book')).order_by('-book_count')[:5]

    context = {
        'recent_books': recent_books,
        'popular_genres': popular_genres,
    }
    return render(request, 'library/home.html', context)


def book_list(request):
    """Liste des livres avec recherche et filtres"""
    books = Book.objects.all().prefetch_related('authors', 'genres')
    form = BookSearchForm(request.GET)

    # Recherche
    if form.is_valid():
        query = form.cleaned_data.get('query')
        genre = form.cleaned_data.get('genre')
        author = form.cleaned_data.get('author')
        language = form.cleaned_data.get('language')
        available_only = form.cleaned_data.get('available_only')

        if query:
            books = books.filter(
                Q(title__icontains=query) |
                Q(authors__first_name__icontains=query) |
                Q(authors__last_name__icontains=query) |
                Q(isbn__icontains=query)
            ).distinct()

        if genre:
            books = books.filter(genres=genre)

        if author:
            books = books.filter(authors=author)

        if language:
            books = books.filter(language=language)

        if available_only:
            books = books.filter(available_copies__gt=0)

    # Pagination
    paginator = Paginator(books, 12)  # 12 livres par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Ajouter les informations de favoris pour l'utilisateur connecté
    if request.user.is_authenticated:
        user_favorites = set(
            Favorite.objects.filter(
                user=request.user,
                book__in=page_obj
            ).values_list('book_id', flat=True)
        )

        # Ajouter l'information de favori à chaque livre
        for book in page_obj:
            book.user_has_favorite = book.id in user_favorites
    else:
        # Pour les utilisateurs non connectés
        for book in page_obj:
            book.user_has_favorite = False

    context = {
        'form': form,
        'page_obj': page_obj,
        'books': page_obj,
    }
    return render(request, 'library/book_list.html', context)


def book_detail(request, book_id):
    """Détail d'un livre"""
    book = get_object_or_404(Book, id=book_id)
    user_has_reservation = False
    user_current_loan = None
    user_has_favorite = False
    user_reservation = None
    queue_info = {}
    estimated_wait_days = 7

    if request.user.is_authenticated:
        user_reservation = Reservation.objects.filter(
            user=request.user,
            book=book,
            status__in=['active', 'ready']
        ).first()

        user_has_reservation = user_reservation is not None

        user_current_loan = Loan.objects.filter(
            user=request.user,
            book=book,
            status__in=['borrowed', 'overdue']
        ).first()

        user_has_favorite = Favorite.objects.filter(
            user=request.user,
            book=book
        ).exists()

    # Obtenir les informations de la file d'attente pour tous les utilisateurs
    from .reservation_services import ReservationService
    queue_info = ReservationService.get_queue_info(book)

    # Calculer le délai d'attente estimé
    if not book.is_available and request.user.is_authenticated:
        estimated_position = queue_info['active_count'] + 1
        estimated_wait_days = estimated_position * LibraryConfig.get_loan_duration(request.user.category)

    context = {
        'book': book,
        'user_has_reservation': user_has_reservation,
        'user_current_loan': user_current_loan,
        'user_has_favorite': user_has_favorite,
        'user_reservation': user_reservation,
        'queue_info': queue_info,
        'estimated_wait_days': estimated_wait_days,
    }
    return render(request, 'library/book_detail.html', context)


@login_required
def dashboard(request):
    """Tableau de bord utilisateur enrichi"""
    user = request.user

    # Emprunts actuels
    current_loans = Loan.objects.filter(
        user=user,
        status__in=['borrowed', 'overdue']
    ).select_related('book').order_by('due_date')

    # Réservations actives
    active_reservations = Reservation.objects.filter(
        user=user,
        status='active'
    ).select_related('book').order_by('reservation_date')

    # Historique des emprunts récents
    recent_loans = Loan.objects.filter(
        user=user
    ).select_related('book').order_by('-loan_date')[:5]

    # Achats récents
    recent_purchases = BookPurchase.objects.filter(
        user=user
    ).select_related('book').order_by('-purchase_date')[:3]

    # Statistiques d'achats
    pending_purchases = BookPurchase.objects.filter(user=user, status='pending')
    total_spent = BookPurchase.objects.filter(
        user=user,
        status__in=['paid', 'confirmed']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Économies réalisées grâce aux remises (calculé manuellement)
    paid_purchases = BookPurchase.objects.filter(
        user=user,
        status__in=['paid', 'confirmed']
    )
    total_savings = sum(purchase.discount_amount for purchase in paid_purchases)

    # Statistiques personnelles
    total_loans_count = Loan.objects.filter(user=user).count()
    total_purchases_count = BookPurchase.objects.filter(user=user).count()

    # Emprunts en retard
    overdue_loans = current_loans.filter(status='overdue')

    # Réservations prêtes (livre disponible)
    ready_reservations = active_reservations.filter(book__available_copies__gt=0)

    # Livres favoris (les plus empruntés par l'utilisateur)
    favorite_books = Book.objects.filter(
        loans__user=user
    ).annotate(
        loan_count=Count('loans', filter=Q(loans__user=user))
    ).order_by('-loan_count')[:3]

    # Genres préférés
    favorite_genres = Genre.objects.filter(
        book__loans__user=user
    ).annotate(
        loan_count=Count('book__loans', filter=Q(book__loans__user=user))
    ).order_by('-loan_count')[:3]

    # Recommandations basées sur les genres préférés
    if favorite_genres.exists():
        recommended_books = Book.objects.filter(
            genres__in=favorite_genres,
            available_copies__gt=0
        ).exclude(
            loans__user=user
        ).distinct()[:4]
    else:
        # Recommandations générales (livres populaires)
        recommended_books = Book.objects.filter(
            available_copies__gt=0
        ).annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:4]

    # Limites et quotas
    max_books = LibraryConfig.get_max_books(user.category)
    current_books_count = current_loans.count()
    remaining_books = max_books - current_books_count

    # Calculs pour la barre de progression
    quota_percentage = (current_books_count * 100 // max_books) if max_books > 0 else 0
    quota_warning_threshold = max_books * 0.8 if max_books > 0 else 0

    # Prochaines échéances
    upcoming_due_dates = current_loans.filter(
        due_date__lte=timezone.now().date() + timedelta(days=3)
    ).order_by('due_date')

    # Vérifier les frais impayés
    outstanding_amount, outstanding_payments = PaymentService.calculate_outstanding_fees(user)

    context = {
        'current_loans': current_loans,
        'active_reservations': active_reservations,
        'recent_loans': recent_loans,
        'recent_purchases': recent_purchases,
        'pending_purchases': pending_purchases,
        'total_spent': total_spent,
        'total_savings': total_savings,
        'total_loans_count': total_loans_count,
        'total_purchases_count': total_purchases_count,
        'overdue_loans': overdue_loans,
        'ready_reservations': ready_reservations,
        'favorite_books': favorite_books,
        'favorite_genres': favorite_genres,
        'recommended_books': recommended_books,
        'max_books': max_books,
        'current_books_count': current_books_count,
        'remaining_books': remaining_books,
        'quota_percentage': quota_percentage,
        'quota_warning_threshold': quota_warning_threshold,
        'upcoming_due_dates': upcoming_due_dates,
        'user_category_display': user.get_category_display(),
        'outstanding_amount': outstanding_amount,
        'outstanding_payments': outstanding_payments,
    }
    return render(request, 'library/dashboard.html', context)


@login_required
def reserve_book(request, book_id):
    """Réserver un livre"""
    book = get_object_or_404(Book, id=book_id)
    user = request.user

    if request.method == 'POST':
        # Vérifier si c'est une requête AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Utiliser le service de réservation
        try:
            # Import local pour éviter les imports circulaires
            from .reservation_services import ReservationService

            success, result = ReservationService.create_reservation(user, book)

            if success:
                message = f"Votre réservation pour '{book.title}' a été enregistrée. Vous serez notifié quand le livre sera disponible."

                if is_ajax:
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'reservation_id': result.id if hasattr(result, 'id') else None
                    })
                else:
                    messages.success(request, message)
                    return redirect('my_reservations')
            else:
                if is_ajax:
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'message': result
                    })
                else:
                    messages.error(request, result)
                    return redirect('book_detail', book_id=book.id)

        except Exception as e:
            error_message = f"Erreur lors de la réservation: {str(e)}"
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('book_detail', book_id=book.id)

    # Vérifications pour l'affichage
    from .reservation_services import ReservationValidator, ReservationService

    can_reserve, message = ReservationValidator.can_user_reserve(user, book)
    if not can_reserve:
        messages.error(request, message)
        if "disponible" in message:
            return redirect('borrow_book', book_id=book.id)
        else:
            return redirect('book_detail', book_id=book.id)

    # Obtenir les informations de la file d'attente
    queue_info = ReservationService.get_queue_info(book)

    # Calculer la position estimée pour ce nouvel utilisateur
    estimated_position = queue_info['active_count'] + 1

    # Estimer le délai d'attente
    estimated_wait_days = estimated_position * LibraryConfig.get_loan_duration(user.category)

    context = {
        'book': book,
        'queue_position': estimated_position,
        'estimated_wait_days': estimated_wait_days,
        'queue_info': queue_info,
    }
    return render(request, 'library/reserve_confirm.html', context)


@login_required
def cancel_reservation(request, reservation_id):
    """Annuler une réservation"""
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if request.method == 'POST':
        # Vérifier si c'est une requête AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Utiliser le service de réservation
        from .reservation_services import ReservationService

        success, message = ReservationService.cancel_reservation(reservation)

        if success:
            success_message = f"Votre réservation pour '{reservation.book.title}' a été annulée."

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': success_message
                })
            else:
                messages.success(request, success_message)
        else:
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': message
                })
            else:
                messages.error(request, message)

    return redirect('my_reservations')


def register(request):
    """Inscription d'un nouvel utilisateur"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Votre compte a été créé avec succès!")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    """Déconnexion de l'utilisateur"""
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        logout(request)
        messages.success(request, f"Au revoir {username} ! Vous avez été déconnecté avec succès.")
    return redirect('home')


@staff_member_required
def upload_book_cover(request, book_id):
    """Télécharger une image de couverture pour un livre (réservé au staff)"""
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        form = BookCoverUploadForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f"Image de couverture ajoutée pour '{book.title}'")
            return redirect('book_detail', book_id=book.id)
    else:
        form = BookCoverUploadForm(instance=book)

    context = {
        'form': form,
        'book': book,
    }
    return render(request, 'library/upload_cover.html', context)


@staff_member_required
def bulk_upload_covers(request):
    """Interface pour l'upload en masse de couvertures"""
    books_without_covers = Book.objects.filter(cover_image__isnull=True).order_by('title')

    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        if book_id and 'cover_image' in request.FILES:
            try:
                book = Book.objects.get(id=book_id)
                book.cover_image = request.FILES['cover_image']
                book.save()
                messages.success(request, f"Couverture ajoutée pour '{book.title}'")
            except Book.DoesNotExist:
                messages.error(request, "Livre introuvable")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'upload: {str(e)}")

    context = {
        'books_without_covers': books_without_covers,
    }
    return render(request, 'library/bulk_upload_covers.html', context)


def book_gallery(request):
    """Galerie des livres avec leurs couvertures"""
    books = Book.objects.filter(cover_image__isnull=False).exclude(cover_image='').prefetch_related('authors', 'genres')

    # Filtrage par genre si spécifié
    genre_id = request.GET.get('genre')
    if genre_id:
        books = books.filter(genres__id=genre_id)

    # Pagination
    paginator = Paginator(books, 20)  # 20 livres par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Liste des genres pour le filtre
    genres = Genre.objects.annotate(book_count=Count('book')).filter(book_count__gt=0)

    context = {
        'page_obj': page_obj,
        'books': page_obj,
        'genres': genres,
        'selected_genre': genre_id,
    }
    return render(request, 'library/book_gallery.html', context)


@staff_member_required
def search_book_images(request, book_id):
    """Rechercher des images de couverture en ligne pour un livre"""
    book = get_object_or_404(Book, id=book_id)

    # Ici on pourrait intégrer une API comme Google Books API ou Open Library
    # Pour l'instant, on propose des images de placeholder
    suggested_images = [
        {
            'url': 'https://via.placeholder.com/400x600/3498db/ffffff?text=' + book.title.replace(' ', '+'),
            'source': 'Placeholder Blue',
            'description': 'Image de placeholder bleue'
        },
        {
            'url': 'https://via.placeholder.com/400x600/e74c3c/ffffff?text=' + book.title.replace(' ', '+'),
            'source': 'Placeholder Red',
            'description': 'Image de placeholder rouge'
        },
        {
            'url': 'https://via.placeholder.com/400x600/2ecc71/ffffff?text=' + book.title.replace(' ', '+'),
            'source': 'Placeholder Green',
            'description': 'Image de placeholder verte'
        },
    ]

    context = {
        'book': book,
        'suggested_images': suggested_images,
    }
    return render(request, 'library/search_images.html', context)


@staff_member_required
def download_image_from_url(request, book_id):
    """Télécharger une image depuis une URL"""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        image_url = request.POST.get('image_url')

        if image_url:
            try:
                import requests
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    from django.core.files.base import ContentFile

                    # Créer un nom de fichier
                    filename = f"downloaded_{book.id}_{book.title.replace(' ', '_').lower()}.jpg"

                    # Sauvegarder l'image
                    book.cover_image.save(
                        filename,
                        ContentFile(response.content),
                        save=True
                    )

                    messages.success(request, f"Image téléchargée avec succès pour '{book.title}'")
                else:
                    messages.error(request, "Impossible de télécharger l'image depuis cette URL")
            except Exception as e:
                messages.error(request, f"Erreur lors du téléchargement: {str(e)}")
        else:
            messages.error(request, "URL d'image manquante")

    return redirect('book_detail', book_id=book_id)


@login_required
def purchase_book(request, book_id):
    """Acheter un livre"""
    book = get_object_or_404(Book, id=book_id)

    # Vérifier si le livre est en vente
    if not book.is_for_sale or not book.purchase_price:
        messages.error(request, "Ce livre n'est pas disponible à la vente.")
        return redirect('book_detail', book_id=book.id)

    # Vérifier si l'achat de livres est activé
    if not LibraryConfig.ENABLE_BOOK_PURCHASE:
        messages.error(request, "L'achat de livres n'est pas activé.")
        return redirect('book_detail', book_id=book.id)

    if request.method == 'POST':
        form = BookPurchaseForm(request.POST, book=book, user=request.user)
        if form.is_valid():
            payment_method = request.POST.get('payment_method', 'cash')

            purchase = form.save(commit=False)
            purchase.user = request.user
            purchase.book = book
            purchase.unit_price = book.purchase_price

            # Calculer la remise selon la catégorie d'utilisateur
            discount = LibraryConfig.get_purchase_discount(request.user.category)
            purchase.discount_percentage = discount

            purchase.save()

            # Créer le paiement pour l'achat
            payment = PaymentService.create_purchase_payment(
                purchase=purchase,
                payment_method=payment_method,
                processed_by=request.user if request.user.is_staff else None
            )

            messages.success(request, f"Votre commande pour '{book.title}' a été enregistrée avec succès ! Rendez-vous en bibliothèque pour finaliser l'achat (montant: {purchase.total_price}€).")
            return redirect('purchase_detail', purchase_id=purchase.id)
    else:
        form = BookPurchaseForm(book=book, user=request.user)

    # Calculer le prix avec remise
    from decimal import Decimal
    discount = LibraryConfig.get_purchase_discount(request.user.category)
    discount_decimal = Decimal(str(discount))
    discounted_price = book.purchase_price * (Decimal('1') - discount_decimal / Decimal('100'))
    savings = book.purchase_price - discounted_price

    context = {
        'book': book,
        'form': form,
        'original_price': book.purchase_price,
        'discount_percentage': discount,
        'discounted_price': discounted_price,
        'savings': savings,
    }
    return render(request, 'library/purchase_book.html', context)


@login_required
def purchase_detail(request, purchase_id):
    """Détail d'un achat"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id, user=request.user)

    context = {
        'purchase': purchase,
    }
    return render(request, 'library/purchase_detail.html', context)


@login_required
def my_purchases(request):
    """Liste des achats de l'utilisateur"""
    purchases = BookPurchase.objects.filter(user=request.user).order_by('-purchase_date')

    # Ajouter les informations de paiement pour chaque achat
    for purchase in purchases:
        purchase.payment_summary = PaymentService.get_payment_summary_for_purchase(purchase)

    context = {
        'purchases': purchases,
    }
    return render(request, 'library/my_purchases.html', context)


@login_required
def cancel_purchase(request, purchase_id):
    """Annuler une commande d'achat"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id, user=request.user)

    # Vérifier que la commande peut être annulée
    if purchase.status not in ['pending', 'confirmed']:
        messages.error(request, "Cette commande ne peut pas être annulée.")
        return redirect('purchase_detail', purchase_id=purchase.id)

    if request.method == 'POST':
        # Vérifier si c'est une requête AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            # Annuler la commande
            purchase.status = 'cancelled'
            purchase.save()

            # Annuler aussi le paiement associé s'il existe
            if hasattr(purchase, 'payment') and purchase.payment:
                purchase.payment.status = 'cancelled'
                purchase.payment.save()

            success_message = f"Votre commande pour '{purchase.book.title}' a été annulée avec succès."

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': success_message
                })
            else:
                messages.success(request, success_message)
                return redirect('my_purchases')

        except Exception as e:
            error_message = f"Erreur lors de l'annulation: {str(e)}"

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)

    return redirect('purchase_detail', purchase_id=purchase.id)


@login_required
def my_payments(request):
    """Liste des paiements de l'utilisateur"""
    payments = PaymentService.get_user_payment_history(request.user)
    outstanding_amount, outstanding_payments = PaymentService.calculate_outstanding_fees(request.user)

    # Grouper les paiements par type
    payments_by_type = {}
    for payment in payments:
        payment_type = payment.get_payment_type_display()
        if payment_type not in payments_by_type:
            payments_by_type[payment_type] = []
        payments_by_type[payment_type].append(payment)

    context = {
        'payments': payments,
        'payments_by_type': payments_by_type,
        'outstanding_amount': outstanding_amount,
        'outstanding_payments': outstanding_payments,
    }
    return render(request, 'library/my_payments.html', context)


@staff_member_required
def process_payment(request, payment_type, object_id):
    """Traiter un paiement (achat, etc.)"""
    if payment_type == 'purchase':
        purchase = get_object_or_404(BookPurchase, id=object_id)
        amount = purchase.total_price
        user = purchase.user
        related_object = purchase
    else:
        messages.error(request, "Type de paiement invalide.")
        return redirect('admin:index')

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = user
            payment.payment_type = payment_type
            payment.amount = amount
            payment.status = 'completed'
            payment.processed_by = request.user

            if payment_type == 'purchase':
                payment.purchase = related_object
                related_object.status = 'paid'
                related_object.save()

            payment.save()

            messages.success(request, f"Paiement de {amount}€ enregistré avec succès.")
            return redirect('admin:index')
    else:
        form = PaymentForm()

    context = {
        'form': form,
        'payment_type': payment_type,
        'amount': amount,
        'user': user,
        'object': related_object,
    }
    return render(request, 'library/process_payment.html', context)


@staff_member_required
def quick_loan(request):
    """Créer rapidement un emprunt"""
    if request.method == 'POST':
        form = QuickLoanForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            book = form.cleaned_data['book']
            notes = form.cleaned_data['notes']

            # Plus de vérification de conditions spéciales

            # Créer l'emprunt
            duration = LibraryConfig.get_loan_duration(user.category)
            due_date = timezone.now().date() + timedelta(days=duration)

            loan = Loan.objects.create(
                user=user,
                book=book,
                due_date=due_date,
                notes=notes
            )

            # Mettre à jour la disponibilité du livre
            book.available_copies -= 1
            book.save()

            messages.success(request, f"Emprunt créé: {book.title} pour {user.get_full_name()}")
            return redirect('admin:library_loan_change', loan.id)
    else:
        form = QuickLoanForm()

    context = {
        'form': form,
    }
    return render(request, 'library/quick_loan.html', context)


def library_conditions(request):
    """Afficher les conditions de la bibliothèque"""
    # Créer un objet avec les paramètres pour le template
    class SettingsProxy:
        def __init__(self):
            self.student_loan_duration = LibraryConfig.LOAN_DURATIONS['student']
            self.teacher_loan_duration = LibraryConfig.LOAN_DURATIONS['teacher']
            self.staff_loan_duration = LibraryConfig.LOAN_DURATIONS['staff']
            self.external_loan_duration = LibraryConfig.LOAN_DURATIONS['external']
            self.student_max_books = LibraryConfig.MAX_BOOKS['student']
            self.teacher_max_books = LibraryConfig.MAX_BOOKS['teacher']
            self.staff_max_books = LibraryConfig.MAX_BOOKS['staff']
            self.external_max_books = LibraryConfig.MAX_BOOKS['external']
            self.reservation_duration = LibraryConfig.RESERVATION_DURATION
            self.reservation_hold_duration = LibraryConfig.RESERVATION_HOLD_DURATION
            self.purchase_discount_student = LibraryConfig.PURCHASE_DISCOUNTS['student']
            self.purchase_discount_staff = LibraryConfig.PURCHASE_DISCOUNTS['staff']
            self.enable_book_purchase = LibraryConfig.ENABLE_BOOK_PURCHASE
            self.require_deposit = LibraryConfig.REQUIRE_DEPOSIT
            self.deposit_amount = LibraryConfig.DEPOSIT_AMOUNT
            self.accept_cash = LibraryConfig.ACCEPT_CASH
            self.accept_card = LibraryConfig.ACCEPT_CARD
            self.accept_online = LibraryConfig.ACCEPT_ONLINE

    settings = SettingsProxy()

    context = {
        'settings': settings,
    }
    return render(request, 'library/conditions.html', context)


@staff_member_required
def admin_dashboard(request):
    """Tableau de bord administrateur personnalisé"""

    # Statistiques générales
    total_books = Book.objects.count()
    total_users = CustomUser.objects.filter(is_active_member=True).count()
    total_loans = Loan.objects.count()

    # Emprunts actuels
    current_loans = Loan.objects.filter(status__in=['borrowed', 'overdue']).count()
    overdue_loans = Loan.objects.filter(status='overdue').count()

    # Réservations actives
    active_reservations = Reservation.objects.filter(status='active').count()

    # Plus d'amendes dans le système
    total_unpaid_amount = 0

    # Achats récents
    recent_purchases = BookPurchase.objects.filter(
        purchase_date__gte=timezone.now() - timedelta(days=30)
    ).count()

    # Livres les plus empruntés (derniers 30 jours)
    popular_books = Book.objects.annotate(
        loan_count=Count('loans', filter=Q(loans__loan_date__gte=timezone.now() - timedelta(days=30)))
    ).order_by('-loan_count')[:5]

    # Utilisateurs les plus actifs
    active_users = CustomUser.objects.annotate(
        loan_count=Count('loans', filter=Q(loans__loan_date__gte=timezone.now() - timedelta(days=30)))
    ).order_by('-loan_count')[:5]

    # Emprunts en retard
    overdue_loans_list = Loan.objects.filter(status='overdue').select_related('user', 'book')[:10]

    # Réservations à traiter
    pending_reservations = Reservation.objects.filter(
        status='active',
        book__available_copies__gt=0
    ).select_related('user', 'book')[:10]

    # Achats en attente
    pending_purchases = BookPurchase.objects.filter(status='pending').select_related('user', 'book')[:10]

    # Statistiques de livraisons
    total_deliveries = Delivery.objects.count()
    pending_deliveries = Delivery.objects.filter(status='pending').count()
    in_transit_deliveries = Delivery.objects.filter(status__in=['shipped', 'in_transit']).count()
    overdue_deliveries = Delivery.objects.filter(
        estimated_delivery_date__lt=timezone.now(),
        status__in=['pending', 'preparing', 'shipped', 'in_transit']
    ).count()

    # Statistiques par mois (derniers 6 mois)
    monthly_stats = []
    for i in range(6):
        month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        loans_count = Loan.objects.filter(
            loan_date__gte=month_start,
            loan_date__lte=month_end
        ).count()

        purchases_count = BookPurchase.objects.filter(
            purchase_date__gte=month_start,
            purchase_date__lte=month_end
        ).count()

        monthly_stats.append({
            'month': month_start.strftime('%B %Y'),
            'loans': loans_count,
            'purchases': purchases_count
        })

    monthly_stats.reverse()

    context = {
        'total_books': total_books,
        'total_users': total_users,
        'total_loans': total_loans,
        'current_loans': current_loans,
        'overdue_loans': overdue_loans,
        'active_reservations': active_reservations,
        'unpaid_fines_count': 0,
        'total_unpaid_amount': total_unpaid_amount,
        'recent_purchases': recent_purchases,
        'popular_books': popular_books,
        'active_users': active_users,
        'overdue_loans_list': overdue_loans_list,
        'pending_reservations': pending_reservations,
        'pending_purchases': pending_purchases,
        'monthly_stats': monthly_stats,
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'in_transit_deliveries': in_transit_deliveries,
        'overdue_deliveries': overdue_deliveries,
    }

    return render(request, 'admin/custom_dashboard.html', context)


@staff_member_required
def admin_users_management(request):
    """Gestion des utilisateurs"""
    users = CustomUser.objects.all().annotate(
        active_loans_count=Count('loans', filter=Q(loans__status__in=['borrowed', 'overdue']))
    ).order_by('-date_joined')

    # Filtres
    category = request.GET.get('category')
    status = request.GET.get('status')
    search = request.GET.get('search')

    if category:
        users = users.filter(category=category)

    if status == 'active':
        users = users.filter(is_active_member=True)
    elif status == 'inactive':
        users = users.filter(is_active_member=False)

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'categories': CustomUser.USER_CATEGORIES,
        'current_category': category,
        'current_status': status,
        'current_search': search,
    }

    return render(request, 'admin/users_management.html', context)


@staff_member_required
def admin_books_management(request):
    """Gestion des livres"""
    books = Book.objects.all().prefetch_related('authors', 'genres').annotate(
        loan_count=Count('loans'),
        current_loans=Count('loans', filter=Q(loans__status__in=['borrowed', 'overdue']))
    ).order_by('-added_date')

    # Filtres
    genre = request.GET.get('genre')
    language = request.GET.get('language')
    availability = request.GET.get('availability')
    search = request.GET.get('search')

    if genre:
        books = books.filter(genres__id=genre)

    if language:
        books = books.filter(language=language)

    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'unavailable':
        books = books.filter(available_copies=0)

    if search:
        books = books.filter(
            Q(title__icontains=search) |
            Q(isbn__icontains=search) |
            Q(authors__first_name__icontains=search) |
            Q(authors__last_name__icontains=search)
        ).distinct()

    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'books': page_obj,
        'genres': Genre.objects.all(),
        'languages': Book.LANGUAGES,
        'current_genre': genre,
        'current_language': language,
        'current_availability': availability,
        'current_search': search,
    }

    return render(request, 'admin/books_management.html', context)


@staff_member_required
def admin_statistics(request):
    """Statistiques détaillées pour l'administration"""

    # Statistiques des emprunts
    loan_stats = {
        'total': Loan.objects.count(),
        'active': Loan.objects.filter(status__in=['borrowed', 'overdue']).count(),
        'overdue': Loan.objects.filter(status='overdue').count(),
        'returned': Loan.objects.filter(status='returned').count(),
        'avg_duration': None,  # Calcul de durée moyenne non supporté avec SQLite
    }

    # Statistiques des utilisateurs par catégorie
    user_stats = {}
    for category, label in CustomUser.USER_CATEGORIES:
        user_stats[category] = {
            'label': label,
            'count': CustomUser.objects.filter(category=category, is_active_member=True).count(),
            'loans': Loan.objects.filter(user__category=category).count(),
        }

    # Statistiques des livres
    book_stats = {
        'total': Book.objects.count(),
        'available': Book.objects.filter(available_copies__gt=0).count(),
        'unavailable': Book.objects.filter(available_copies=0).count(),
        'for_sale': Book.objects.filter(is_for_sale=True).count(),
        'most_popular': Book.objects.annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count').first(),
    }

    # Statistiques financières
    financial_stats = {
        'total_purchases': BookPurchase.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0,
        'pending_purchases': BookPurchase.objects.filter(status='pending').count(),
    }

    context = {
        'loan_stats': loan_stats,
        'user_stats': user_stats,
        'book_stats': book_stats,
        'financial_stats': financial_stats,
    }

    return render(request, 'admin/statistics.html', context)


@staff_member_required
def admin_purchases(request):
    """Gestion des achats pour l'administration"""
    purchases = BookPurchase.objects.all().select_related('user', 'book').order_by('-purchase_date')

    # Filtres
    status = request.GET.get('status')
    user_search = request.GET.get('user_search')
    book_search = request.GET.get('book_search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        purchases = purchases.filter(status=status)

    if user_search:
        purchases = purchases.filter(
            Q(user__username__icontains=user_search) |
            Q(user__first_name__icontains=user_search) |
            Q(user__last_name__icontains=user_search) |
            Q(user__email__icontains=user_search)
        )

    if book_search:
        purchases = purchases.filter(book__title__icontains=book_search)

    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            purchases = purchases.filter(purchase_date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            purchases = purchases.filter(purchase_date__lte=date_to_obj)
        except ValueError:
            pass

    # Statistiques pour la page
    total_purchases = purchases.count()
    pending_count = purchases.filter(status='pending').count()
    confirmed_count = purchases.filter(status='confirmed').count()
    paid_count = purchases.filter(status='paid').count()
    delivered_count = purchases.filter(status='delivered').count()
    cancelled_count = purchases.filter(status='cancelled').count()

    # Revenus
    total_revenue = purchases.filter(
        status__in=['paid', 'delivered']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    pending_revenue = purchases.filter(
        status__in=['pending', 'confirmed']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Pagination
    paginator = Paginator(purchases, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'purchases': page_obj,
        'purchase_statuses': BookPurchase.PURCHASE_STATUS,
        'current_status': status,
        'current_user_search': user_search,
        'current_book_search': book_search,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'total_purchases': total_purchases,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'paid_count': paid_count,
        'delivered_count': delivered_count,
        'cancelled_count': cancelled_count,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
    }
    return render(request, 'admin/purchases_management.html', context)


@staff_member_required
def admin_update_purchase_status(request, purchase_id):
    """Mettre à jour le statut d'un achat"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            import json
            if is_ajax:
                data = json.loads(request.body)
                new_status = data.get('status')
            else:
                new_status = request.POST.get('status')

            if not new_status:
                raise ValueError("Statut manquant")

            # Vérifier que le statut est valide
            valid_statuses = [choice[0] for choice in BookPurchase.PURCHASE_STATUS]
            if new_status not in valid_statuses:
                raise ValueError(f"Statut invalide: {new_status}")

            old_status = purchase.status
            purchase.status = new_status
            purchase.save()

            # Créer un paiement si le statut est "paid" et qu'il n'y en a pas
            if new_status == 'paid' and (not hasattr(purchase, 'payment') or not purchase.payment):
                from .models import Payment
                Payment.objects.create(
                    user=purchase.user,
                    amount=purchase.total_price,
                    payment_type='purchase',
                    payment_method='cash',
                    status='completed',
                    processed_by=request.user,
                    purchase=purchase
                )

            # Messages selon le statut
            status_messages = {
                'confirmed': f"Commande #{purchase.id} confirmée avec succès.",
                'paid': f"Commande #{purchase.id} marquée comme payée.",
                'delivered': f"Commande #{purchase.id} marquée comme livrée.",
                'cancelled': f"Commande #{purchase.id} annulée.",
            }

            success_message = status_messages.get(new_status, f"Statut de la commande #{purchase.id} mis à jour.")

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'old_status': old_status,
                    'new_status': new_status
                })
            else:
                messages.success(request, success_message)
                return redirect('admin_purchases')

        except Exception as e:
            error_message = f"Erreur lors de la mise à jour: {str(e)}"

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': error_message,
                    'debug_info': {
                        'user_authenticated': request.user.is_authenticated,
                        'user_staff': request.user.is_staff,
                        'csrf_token_present': 'csrfmiddlewaretoken' in request.POST or 'X-CSRFToken' in request.headers,
                        'request_method': request.method,
                        'content_type': request.content_type,
                    }
                }, status=500)
            else:
                messages.error(request, error_message)

    return redirect('admin_purchases')


@staff_member_required
def confirm_purchase(request, purchase_id):
    """Confirmer une commande d'achat"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    # Vérifier que la commande peut être confirmée
    if purchase.status != 'pending':
        messages.error(request, f"Cette commande ne peut pas être confirmée (statut actuel: {purchase.get_status_display()}).")
        return redirect('admin_purchases')

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            # Confirmer la commande
            old_status = purchase.status
            purchase.status = 'confirmed'
            purchase.save()

            success_message = f"Commande #{purchase.id} confirmée avec succès. Le client peut maintenant venir payer."

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'old_status': old_status,
                    'new_status': 'confirmed'
                })
            else:
                messages.success(request, success_message)
                return redirect('admin_purchases')

        except Exception as e:
            error_message = f"Erreur lors de la confirmation: {str(e)}"

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)
                return redirect('admin_purchases')

    # GET request - afficher la page de confirmation
    context = {
        'purchase': purchase,
    }
    return render(request, 'admin/confirm_purchase.html', context)


@staff_member_required
def mark_purchase_paid(request, purchase_id):
    """Marquer une commande comme payée"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    # Vérifier que la commande peut être marquée comme payée
    if purchase.status not in ['pending', 'confirmed']:
        messages.error(request, f"Cette commande ne peut pas être marquée comme payée (statut actuel: {purchase.get_status_display()}).")
        return redirect('admin_purchases')

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            # Marquer comme payé
            old_status = purchase.status
            purchase.status = 'paid'
            purchase.save()

            # Créer ou mettre à jour le paiement associé
            if hasattr(purchase, 'payment') and purchase.payment:
                payment = purchase.payment
                payment.status = 'completed'
                payment.processed_by = request.user
                payment.save()
            else:
                # Créer un nouveau paiement
                from .models import Payment
                payment = Payment.objects.create(
                    user=purchase.user,
                    amount=purchase.total_price,
                    payment_type='purchase',
                    payment_method='cash',  # Par défaut
                    status='completed',
                    processed_by=request.user,
                    purchase=purchase
                )

            success_message = f"Commande #{purchase.id} marquée comme payée. Paiement de {purchase.total_price}€ enregistré."

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'old_status': old_status,
                    'new_status': 'paid'
                })
            else:
                messages.success(request, success_message)
                return redirect('admin_purchases')

        except Exception as e:
            error_message = f"Erreur lors du marquage comme payé: {str(e)}"

            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)
                return redirect('admin_purchases')

    # GET request - afficher la page de confirmation
    context = {
        'purchase': purchase,
    }
    return render(request, 'admin/mark_purchase_paid.html', context)


@staff_member_required
def create_delivery(request, purchase_id):
    """Créer une livraison pour un achat"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    # Vérifier que l'achat est payé et n'a pas déjà de livraison
    if purchase.status != 'paid':
        messages.error(request, "L'achat doit être payé avant de créer une livraison.")
        return redirect('admin_purchases')

    if hasattr(purchase, 'delivery'):
        messages.warning(request, "Une livraison existe déjà pour cet achat.")
        return redirect('delivery_detail', delivery_id=purchase.delivery.id)

    # Vérifier si c'est une livraison express
    is_express = request.GET.get('express') == '1'

    if request.method == 'POST':
        form = DeliveryForm(request.POST, purchase=purchase)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.purchase = purchase
            delivery.processed_by = request.user

            # Configuration pour livraison express
            if is_express:
                delivery.delivery_method = 'express'
                delivery.notes = f"Livraison EXPRESS - {delivery.notes}" if delivery.notes else "Livraison EXPRESS"
                # Réduire le délai de livraison pour express
                if delivery.estimated_delivery_date:
                    delivery.estimated_delivery_date = delivery.estimated_delivery_date - timedelta(days=2)

            delivery.save()

            delivery_type = "express" if is_express else "standard"
            messages.success(request, f"Livraison {delivery_type} créée avec succès pour la commande #{purchase.id}")
            return redirect('delivery_detail', delivery_id=delivery.id)
    else:
        # Pré-remplir le formulaire selon le type de livraison
        initial_data = {}
        if is_express:
            initial_data['delivery_method'] = 'express'
            initial_data['notes'] = 'Livraison EXPRESS'
            # Date de livraison estimée plus rapide pour express
            initial_data['estimated_delivery_date'] = timezone.now().date() + timedelta(days=1)
        else:
            initial_data['estimated_delivery_date'] = timezone.now().date() + timedelta(days=3)

        form = DeliveryForm(purchase=purchase, initial=initial_data)

    context = {
        'form': form,
        'purchase': purchase,
        'is_express': is_express,
    }
    return render(request, 'admin/create_delivery.html', context)


@staff_member_required
def delivery_detail(request, delivery_id):
    """Détails d'une livraison"""
    delivery = get_object_or_404(Delivery, id=delivery_id)

    context = {
        'delivery': delivery,
        'purchase': delivery.purchase,
    }
    return render(request, 'admin/delivery_detail.html', context)


@staff_member_required
def update_delivery_status(request, delivery_id):
    """Mettre à jour le statut d'une livraison"""
    delivery = get_object_or_404(Delivery, id=delivery_id)

    # Traitement des actions rapides via GET
    quick_status = request.GET.get('status')
    if quick_status and request.method == 'GET':
        # Vérifier que le statut est valide
        valid_statuses = [choice[0] for choice in Delivery.DELIVERY_STATUS]
        if quick_status in valid_statuses:
            old_status = delivery.status
            delivery.status = quick_status
            delivery.processed_by = request.user

            # Actions spéciales selon le statut
            if delivery.status == 'delivered' and not delivery.actual_delivery_date:
                delivery.actual_delivery_date = timezone.now()
                # Mettre à jour le statut de l'achat
                delivery.purchase.status = 'delivered'
                delivery.purchase.save()

            delivery.save()

            status_labels = {
                'pending': 'En attente',
                'preparing': 'En préparation',
                'shipped': 'Expédiée',
                'in_transit': 'En transit',
                'delivered': 'Livrée',
                'failed': 'Échec'
            }

            messages.success(request, f"Livraison #{delivery.id} : {status_labels.get(quick_status, quick_status)}")
            return redirect('admin_purchases')
        else:
            messages.error(request, f"Statut invalide: {quick_status}")
            return redirect('admin_purchases')

    if request.method == 'POST':
        form = DeliveryTrackingForm(request.POST, instance=delivery)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.processed_by = request.user

            # Actions spéciales selon le statut
            if delivery.status == 'delivered' and not delivery.actual_delivery_date:
                delivery.actual_delivery_date = timezone.now()
                # Mettre à jour le statut de l'achat
                delivery.purchase.status = 'delivered'
                delivery.purchase.save()

            delivery.save()

            messages.success(request, f"Statut de livraison mis à jour: {delivery.get_status_display()}")
            return redirect('delivery_detail', delivery_id=delivery.id)
    else:
        form = DeliveryTrackingForm(instance=delivery)

    context = {
        'form': form,
        'delivery': delivery,
    }
    return render(request, 'admin/update_delivery.html', context)


@staff_member_required
def admin_deliveries(request):
    """Gestion des livraisons pour l'administration"""
    deliveries = Delivery.objects.all().select_related('purchase__user', 'purchase__book').order_by('-created_date')

    # Filtres
    status = request.GET.get('status')
    method = request.GET.get('method')
    user_search = request.GET.get('user_search')
    overdue_only = request.GET.get('overdue_only')

    if status:
        deliveries = deliveries.filter(status=status)

    if method:
        deliveries = deliveries.filter(delivery_method=method)

    if user_search:
        deliveries = deliveries.filter(
            Q(purchase__user__username__icontains=user_search) |
            Q(purchase__user__first_name__icontains=user_search) |
            Q(purchase__user__last_name__icontains=user_search) |
            Q(recipient_name__icontains=user_search)
        )

    if overdue_only:
        # Filtrer les livraisons en retard
        deliveries = deliveries.filter(
            estimated_delivery_date__lt=timezone.now(),
            status__in=['pending', 'preparing', 'shipped', 'in_transit']
        )

    # Statistiques
    total_deliveries = deliveries.count()
    pending_count = deliveries.filter(status='pending').count()
    preparing_count = deliveries.filter(status='preparing').count()
    shipped_count = deliveries.filter(status='shipped').count()
    in_transit_count = deliveries.filter(status='in_transit').count()
    delivered_count = deliveries.filter(status='delivered').count()
    failed_count = deliveries.filter(status='failed').count()

    # Livraisons en retard
    overdue_deliveries = Delivery.objects.filter(
        estimated_delivery_date__lt=timezone.now(),
        status__in=['pending', 'preparing', 'shipped', 'in_transit']
    ).count()

    # Pagination
    paginator = Paginator(deliveries, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'deliveries': page_obj,
        'delivery_statuses': Delivery.DELIVERY_STATUS,
        'delivery_methods': Delivery.DELIVERY_METHODS,
        'current_status': status,
        'current_method': method,
        'current_user_search': user_search,
        'current_overdue_only': overdue_only,
        'total_deliveries': total_deliveries,
        'pending_count': pending_count,
        'preparing_count': preparing_count,
        'shipped_count': shipped_count,
        'in_transit_count': in_transit_count,
        'delivered_count': delivered_count,
        'failed_count': failed_count,
        'overdue_deliveries': overdue_deliveries,
    }
    return render(request, 'admin/deliveries_management.html', context)


@super_admin_required
def super_admin_dashboard(request):
    """Tableau de bord super administrateur"""

    # Statistiques des utilisateurs
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    staff_users = CustomUser.objects.filter(is_staff=True).count()
    super_admin_users = CustomUser.objects.filter(is_super_admin=True).count()

    # Statistiques par catégorie
    user_categories = {}
    for category, label in CustomUser.USER_CATEGORIES:
        user_categories[category] = {
            'label': label,
            'count': CustomUser.objects.filter(category=category, is_active=True).count()
        }

    # Activité récente
    recent_registrations = CustomUser.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30)
    ).order_by('-date_joined')[:10]

    # Utilisateurs les plus actifs
    active_borrowers = CustomUser.objects.annotate(
        loan_count=Count('loans', filter=Q(loans__loan_date__gte=timezone.now() - timedelta(days=30)))
    ).filter(loan_count__gt=0).order_by('-loan_count')[:10]

    # Statistiques système
    system_stats = {
        'total_books': Book.objects.count(),
        'total_loans': Loan.objects.count(),
        'total_purchases': BookPurchase.objects.count(),
        'total_deliveries': Delivery.objects.count(),
        'active_loans': Loan.objects.filter(status__in=['borrowed', 'overdue']).count(),
        'overdue_loans': Loan.objects.filter(status='overdue').count(),
        'pending_purchases': BookPurchase.objects.filter(status='pending').count(),
        'pending_deliveries': Delivery.objects.filter(status='pending').count(),
    }

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'super_admin_users': super_admin_users,
        'user_categories': user_categories,
        'recent_registrations': recent_registrations,
        'active_borrowers': active_borrowers,
        'system_stats': system_stats,
    }

    return render(request, 'admin/super_admin_dashboard.html', context)


@super_admin_required
def manage_admin_users(request):
    """Gestion des utilisateurs administrateurs"""

    # Obtenir tous les utilisateurs avec privilèges
    admin_users = CustomUser.objects.filter(
        Q(is_staff=True) | Q(is_super_admin=True) | Q(is_superuser=True)
    ).order_by('-date_joined')

    # Obtenir les utilisateurs réguliers qui pourraient être promus
    regular_users = CustomUser.objects.filter(
        is_staff=False,
        is_super_admin=False,
        is_superuser=False,
        is_active=True
    ).order_by('-date_joined')[:20]  # Limiter à 20 pour la performance

    # Filtres
    user_type = request.GET.get('user_type')
    search = request.GET.get('search')

    if user_type == 'staff':
        admin_users = admin_users.filter(is_staff=True, is_super_admin=False)
    elif user_type == 'super_admin':
        admin_users = admin_users.filter(is_super_admin=True)
    elif user_type == 'superuser':
        admin_users = admin_users.filter(is_superuser=True)

    if search:
        admin_users = admin_users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # Pagination
    paginator = Paginator(admin_users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'admin_users': page_obj,
        'regular_users': regular_users,
        'current_user_type': user_type,
        'current_search': search,
        'user_categories': CustomUser.USER_CATEGORIES,
    }

    return render(request, 'admin/manage_admin_users.html', context)


@super_admin_required
def promote_user(request, user_id):
    """Promouvoir un utilisateur"""
    user_to_promote = get_object_or_404(CustomUser, id=user_id)

    # Vérifier que l'utilisateur actuel peut promouvoir
    if not request.user.can_manage_users:
        messages.error(request, "Vous n'avez pas les droits pour promouvoir des utilisateurs.")
        return redirect('manage_admin_users')

    # Vérifier que l'utilisateur n'est pas déjà superuser
    if user_to_promote.is_superuser:
        messages.error(request, "Impossible de modifier un superutilisateur.")
        return redirect('manage_admin_users')

    # Vérifier que l'utilisateur ne se modifie pas lui-même
    if user_to_promote == request.user:
        messages.error(request, "Vous ne pouvez pas modifier vos propres privilèges.")
        return redirect('manage_admin_users')

    # Traitement des actions GET (depuis les liens directs)
    action = request.GET.get('action') or request.POST.get('action')

    if request.method == 'POST' or (request.method == 'GET' and action):
        if action == 'make_staff':
            if user_to_promote.is_staff and not user_to_promote.is_super_admin:
                messages.info(request, f"{user_to_promote.get_full_name()} est déjà membre du staff.")
            else:
                user_to_promote.is_staff = True
                user_to_promote.is_super_admin = False
                user_to_promote.save()
                messages.success(request, f"✅ {user_to_promote.get_full_name()} est maintenant membre du staff.")

        elif action == 'make_super_admin':
            if user_to_promote.is_super_admin:
                messages.info(request, f"{user_to_promote.get_full_name()} est déjà super administrateur.")
            else:
                user_to_promote.is_staff = True
                user_to_promote.is_super_admin = True
                user_to_promote.save()
                messages.success(request, f"👑 {user_to_promote.get_full_name()} est maintenant super administrateur.")

        elif action == 'remove_privileges':
            if not user_to_promote.is_staff and not user_to_promote.is_super_admin:
                messages.info(request, f"{user_to_promote.get_full_name()} n'a pas de privilèges administratifs.")
            else:
                user_to_promote.is_staff = False
                user_to_promote.is_super_admin = False
                user_to_promote.save()
                messages.success(request, f"🔻 Privilèges administratifs retirés à {user_to_promote.get_full_name()}.")

        # Rediriger après l'action
        if request.method == 'GET' and action:
            return redirect('manage_admin_users')
        elif request.method == 'POST':
            return redirect('manage_admin_users')

    context = {
        'user_to_promote': user_to_promote,
    }

    return render(request, 'admin/promote_user.html', context)


@super_admin_required
def system_settings(request):
    """Paramètres système pour super admin"""

    # Statistiques système
    system_info = {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'staff_count': CustomUser.objects.filter(is_staff=True).count(),
        'super_admin_count': CustomUser.objects.filter(is_super_admin=True).count(),
        'total_books': Book.objects.count(),
        'available_books': Book.objects.filter(available_copies__gt=0).count(),
        'total_loans': Loan.objects.count(),
        'active_loans': Loan.objects.filter(status__in=['borrowed', 'overdue']).count(),
        'overdue_loans': Loan.objects.filter(status='overdue').count(),
        'total_purchases': BookPurchase.objects.count(),
        'pending_purchases': BookPurchase.objects.filter(status='pending').count(),
        'total_deliveries': Delivery.objects.count(),
        'pending_deliveries': Delivery.objects.filter(status='pending').count(),
    }

    # Configuration de la bibliothèque
    from .models import LibraryConfig
    library_config = {
        'loan_durations': LibraryConfig.LOAN_DURATIONS,
        'max_books': LibraryConfig.MAX_BOOKS,
        'purchase_discounts': LibraryConfig.PURCHASE_DISCOUNTS,
        'enable_book_purchase': LibraryConfig.ENABLE_BOOK_PURCHASE,
        'require_deposit': LibraryConfig.REQUIRE_DEPOSIT,
        'deposit_amount': LibraryConfig.DEPOSIT_AMOUNT,
        'reservation_duration': LibraryConfig.RESERVATION_DURATION,
        'reservation_hold_duration': LibraryConfig.RESERVATION_HOLD_DURATION,
    }

    context = {
        'system_info': system_info,
        'library_config': library_config,
    }

    return render(request, 'admin/system_settings.html', context)


@staff_member_required
def debug_permissions(request):
    """Vue de débogage pour tester les permissions"""
    from django.http import JsonResponse

    debug_info = {
        'user': {
            'username': request.user.username,
            'is_authenticated': request.user.is_authenticated,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'is_super_admin': getattr(request.user, 'is_super_admin', False),
            'permissions': list(request.user.get_all_permissions()),
        },
        'csrf_token': request.META.get('CSRF_COOKIE'),
        'headers': dict(request.headers),
        'method': request.method,
    }

    return JsonResponse(debug_info, indent=2)


@staff_member_required
def test_urls(request):
    """Vue de test pour vérifier les URLs"""
    from django.urls import reverse
    from django.http import JsonResponse

    urls_test = {}

    # Tester les URLs avec un ID d'exemple
    test_id = 1

    url_names = [
        'admin_purchases',
        'admin_update_purchase_status',
        'confirm_purchase',
        'mark_purchase_paid',
        'debug_permissions',
    ]

    for url_name in url_names:
        try:
            if url_name in ['admin_update_purchase_status', 'confirm_purchase', 'mark_purchase_paid']:
                url = reverse(url_name, kwargs={'purchase_id': test_id})
            else:
                url = reverse(url_name)
            urls_test[url_name] = {
                'status': 'success',
                'url': url
            }
        except Exception as e:
            urls_test[url_name] = {
                'status': 'error',
                'error': str(e)
            }

    return JsonResponse({
        'urls': urls_test,
        'test_id': test_id,
        'message': 'Test des URLs terminé'
    }, indent=2)


@staff_member_required
def update_payment_status(request, payment_id):
    """Modifier le statut d'un paiement"""
    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            import json
            if is_ajax:
                data = json.loads(request.body)
                new_status = data.get('status')
                notes = data.get('notes', '')
            else:
                new_status = request.POST.get('status')
                notes = request.POST.get('notes', '')

            if not new_status:
                raise ValueError("Statut manquant")

            # Vérifier que le statut est valide
            valid_statuses = [choice[0] for choice in Payment.PAYMENT_STATUS]
            if new_status not in valid_statuses:
                raise ValueError(f"Statut invalide: {new_status}")

            old_status = payment.status
            payment.status = new_status
            payment.processed_by = request.user

            # Ajouter des notes si fournies
            if notes:
                if payment.notes:
                    payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] {notes}"
                else:
                    payment.notes = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] {notes}"

            payment.save()

            # Mettre à jour l'achat associé si nécessaire
            if hasattr(payment, 'purchase') and payment.purchase:
                if new_status == 'completed' and payment.purchase.status in ['pending', 'confirmed']:
                    payment.purchase.status = 'paid'
                    payment.purchase.save()
                elif new_status in ['failed', 'cancelled'] and payment.purchase.status == 'paid':
                    payment.purchase.status = 'confirmed'
                    payment.purchase.save()

            success_message = f"Statut du paiement #{payment.id} mis à jour: {payment.get_status_display()}"

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'old_status': old_status,
                    'new_status': new_status
                })
            else:
                messages.success(request, success_message)
                return redirect('admin_payments')

        except Exception as e:
            error_message = f"Erreur lors de la mise à jour: {str(e)}"

            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)
                return redirect('admin_payments')

    # GET request - afficher la page de modification
    context = {
        'payment': payment,
        'payment_statuses': Payment.PAYMENT_STATUS,
    }
    return render(request, 'admin/update_payment_status.html', context)


@staff_member_required
def admin_payments(request):
    """Gestion des paiements pour l'administration"""
    payments = Payment.objects.all().select_related('user', 'processed_by').order_by('-payment_date')

    # Filtres
    status = request.GET.get('status')
    payment_type = request.GET.get('payment_type')
    user_search = request.GET.get('user_search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        payments = payments.filter(status=status)

    if payment_type:
        payments = payments.filter(payment_type=payment_type)

    if user_search:
        payments = payments.filter(
            Q(user__username__icontains=user_search) |
            Q(user__first_name__icontains=user_search) |
            Q(user__last_name__icontains=user_search) |
            Q(user__email__icontains=user_search)
        )

    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            payments = payments.filter(payment_date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            payments = payments.filter(payment_date__lte=date_to_obj)
        except ValueError:
            pass

    # Statistiques
    total_payments = payments.count()
    total_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    pending_count = payments.filter(status='pending').count()
    completed_count = payments.filter(status='completed').count()
    failed_count = payments.filter(status='failed').count()
    cancelled_count = payments.filter(status='cancelled').count()

    # Pagination
    paginator = Paginator(payments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'payments': page_obj,
        'payment_statuses': Payment.PAYMENT_STATUS,
        'payment_types': Payment.PAYMENT_TYPES,
        'payment_methods': Payment.PAYMENT_METHODS,
        'current_status': status,
        'current_payment_type': payment_type,
        'current_user_search': user_search,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'failed_count': failed_count,
        'cancelled_count': cancelled_count,
    }

    return render(request, 'admin/payments_management.html', context)


@login_required
def initiate_payment(request, purchase_id):
    """Initier le paiement d'un achat"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id, user=request.user)

    # Vérifier que l'achat peut être payé
    if purchase.status not in ['pending', 'confirmed']:
        messages.error(request, f"Cette commande ne peut pas être payée (statut actuel: {purchase.get_status_display()}).")
        return redirect('my_purchases')

    # Vérifier qu'il n'y a pas déjà un paiement en cours
    existing_payment = Payment.objects.filter(
        purchase=purchase,
        status__in=['pending', 'completed']
    ).first()

    if existing_payment:
        if existing_payment.status == 'completed':
            messages.info(request, "Cette commande a déjà été payée.")
            return redirect('my_purchases')
        else:
            # Rediriger vers le paiement existant
            return redirect('process_payment', payment_id=existing_payment.id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if not payment_method:
            messages.error(request, "Veuillez sélectionner une méthode de paiement.")
        else:
            # Créer le paiement
            payment = Payment.objects.create(
                user=request.user,
                payment_type='purchase',
                amount=purchase.total_price,
                payment_method=payment_method,
                status='pending',
                purchase=purchase,
                notes=f"Paiement pour la commande #{purchase.id} - {purchase.book.title}"
            )

            # Mettre à jour le statut de l'achat si nécessaire
            if purchase.status == 'pending':
                purchase.status = 'confirmed'
                purchase.save()

            messages.success(request, f"Paiement initié avec succès. Montant: {payment.amount}€")
            return redirect('process_payment', payment_id=payment.id)

    context = {
        'purchase': purchase,
        'payment_methods': Payment.PAYMENT_METHODS,
    }
    return render(request, 'payments/initiate_payment.html', context)


@login_required
def pay_all_loans(request):
    """Vue pour payer tous les frais d'emprunts en une seule fois"""
    user = request.user

    # Récupérer tous les emprunts actifs de l'utilisateur
    active_loans = Loan.objects.filter(
        user=user,
        status__in=['borrowed', 'overdue', 'renewed']
    )

    # Calculer les frais pour chaque emprunt
    loan_fees = []
    total_amount = Decimal('0.00')

    for loan in active_loans:
        # Vérifier s'il y a déjà un paiement pour cet emprunt
        existing_payment = Payment.objects.filter(
            loan=loan,
            payment_type='loan_fee',
            status='completed'
        ).first()

        if not existing_payment:
            # Calculer les frais d'emprunt
            loan_fee = Decimal(str(LibraryConfig.get_loan_fee(user.category)))

            # Calculer les frais de retard si applicable
            late_fee = Decimal('0.00')
            if loan.is_overdue:
                late_fee_per_day = Decimal(str(LibraryConfig.get_late_fee_per_day(user.category)))
                late_fee = late_fee_per_day * loan.days_overdue

            # Calculer les frais de renouvellement si applicable
            renewal_fee = Decimal('0.00')
            if loan.renewal_count > 0:
                renewal_fee_per_renewal = Decimal(str(LibraryConfig.get_renewal_fee(user.category)))
                renewal_fee = renewal_fee_per_renewal * loan.renewal_count

            total_loan_amount = loan_fee + late_fee + renewal_fee

            if total_loan_amount > 0:
                loan_fees.append({
                    'loan': loan,
                    'loan_fee': loan_fee,
                    'late_fee': late_fee,
                    'renewal_fee': renewal_fee,
                    'total': total_loan_amount,
                    'days_overdue': loan.days_overdue if loan.is_overdue else 0,
                })
                total_amount += total_loan_amount

    if request.method == 'POST':
        if total_amount > 0:
            # Créer les paiements pour tous les emprunts
            payments_created = []

            try:
                with transaction.atomic():
                    for fee_info in loan_fees:
                        loan = fee_info['loan']

                        # Créer le paiement principal pour l'emprunt
                        if fee_info['loan_fee'] > 0:
                            payment = Payment.objects.create(
                                user=user,
                                payment_type='loan_fee',
                                amount=fee_info['loan_fee'],
                                payment_method='cash',  # Par défaut, peut être modifié
                                status='completed',
                                loan=loan,
                                processed_by=request.user if request.user.is_staff else None,
                                notes=f"Frais d'emprunt pour {loan.book.title}"
                            )
                            payments_created.append(payment)

                        # Créer le paiement pour les frais de retard si applicable
                        if fee_info['late_fee'] > 0:
                            late_payment = Payment.objects.create(
                                user=user,
                                payment_type='late_fee',
                                amount=fee_info['late_fee'],
                                payment_method='cash',
                                status='completed',
                                loan=loan,
                                processed_by=request.user if request.user.is_staff else None,
                                notes=f"Frais de retard ({fee_info['days_overdue']} jours) pour {loan.book.title}"
                            )
                            payments_created.append(late_payment)

                        # Créer le paiement pour les frais de renouvellement si applicable
                        if fee_info['renewal_fee'] > 0:
                            renewal_payment = Payment.objects.create(
                                user=user,
                                payment_type='renewal_fee',
                                amount=fee_info['renewal_fee'],
                                payment_method='cash',
                                status='completed',
                                loan=loan,
                                processed_by=request.user if request.user.is_staff else None,
                                notes=f"Frais de renouvellement ({loan.renewal_count} renouvellements) pour {loan.book.title}"
                            )
                            payments_created.append(renewal_payment)

                messages.success(
                    request,
                    f"Paiement de {total_amount}€ effectué avec succès pour {len(loan_fees)} emprunt(s). "
                    f"{len(payments_created)} paiement(s) créé(s)."
                )
                return redirect('my_loans')

            except Exception as e:
                messages.error(request, f"Erreur lors du traitement des paiements: {str(e)}")
        else:
            messages.info(request, "Aucun frais d'emprunt à payer.")
            return redirect('my_loans')

    context = {
        'loan_fees': loan_fees,
        'total_amount': total_amount,
        'user_category': user.category,
        'has_fees': len(loan_fees) > 0,
    }

    return render(request, 'library/pay_all_loans.html', context)


@login_required
def pay_all_purchases(request):
    """Vue pour payer tous les achats en attente en une seule fois"""
    user = request.user

    # Récupérer tous les achats en attente de paiement
    pending_purchases = BookPurchase.objects.filter(
        user=user,
        status__in=['pending', 'confirmed']
    ).select_related('book')

    # Calculer le total et préparer les informations
    purchase_details = []
    total_amount = Decimal('0.00')

    for purchase in pending_purchases:
        # Vérifier s'il y a déjà un paiement complété pour cet achat
        existing_payment = Payment.objects.filter(
            purchase=purchase,
            status='completed'
        ).first()

        if not existing_payment:
            purchase_info = {
                'purchase': purchase,
                'amount': purchase.total_price,
                'original_price': purchase.unit_price * purchase.quantity,
                'discount_amount': purchase.discount_amount,
                'discount_percentage': purchase.discount_percentage,
            }
            purchase_details.append(purchase_info)
            total_amount += purchase.total_price

    if request.method == 'POST':
        if total_amount > 0:
            # Créer les paiements pour tous les achats
            payments_created = []
            purchases_updated = []

            try:
                with transaction.atomic():
                    for detail in purchase_details:
                        purchase = detail['purchase']

                        # Créer le paiement
                        payment = Payment.objects.create(
                            user=user,
                            payment_type='purchase',
                            amount=purchase.total_price,
                            payment_method='card',  # Par défaut, peut être modifié
                            status='completed',
                            purchase=purchase,
                            processed_by=request.user if request.user.is_staff else None,
                            notes=f"Paiement groupé pour {purchase.book.title} (Quantité: {purchase.quantity})"
                        )
                        payments_created.append(payment)

                        # Mettre à jour le statut de l'achat
                        purchase.status = 'paid'
                        purchase.save()
                        purchases_updated.append(purchase)

                messages.success(
                    request,
                    f"Paiement de {total_amount}€ effectué avec succès pour {len(purchase_details)} achat(s). "
                    f"{len(payments_created)} paiement(s) créé(s)."
                )
                return redirect('my_purchases')

            except Exception as e:
                messages.error(request, f"Erreur lors du traitement des paiements: {str(e)}")
        else:
            messages.info(request, "Aucun achat en attente de paiement.")
            return redirect('my_purchases')

    context = {
        'purchase_details': purchase_details,
        'total_amount': total_amount,
        'user_category': user.category,
        'has_purchases': len(purchase_details) > 0,
        'user_discount': LibraryConfig.get_purchase_discount(user.category),
    }

    return render(request, 'library/pay_all_purchases.html', context)


@login_required
def launch_all_deliveries(request):
    """Vue pour lancer toutes les livraisons des achats payés"""
    user = request.user

    # Récupérer tous les achats payés sans livraison
    paid_purchases = BookPurchase.objects.filter(
        user=user,
        status='paid'
    ).exclude(
        delivery__isnull=False
    ).select_related('book')

    # Préparer les informations de livraison
    delivery_details = []

    for purchase in paid_purchases:
        delivery_info = {
            'purchase': purchase,
            'delivery_method': purchase.delivery_preference or 'pickup',
            'delivery_address': purchase.delivery_address or '',
            'recipient_name': purchase.recipient_name or user.get_full_name() or user.username,
            'recipient_phone': purchase.recipient_phone or '',
            'delivery_instructions': purchase.delivery_instructions or '',
            'estimated_cost': purchase.delivery_cost or Decimal('0.00'),
        }
        delivery_details.append(delivery_info)

    if request.method == 'POST':
        if delivery_details:
            # Créer les livraisons pour tous les achats
            deliveries_created = []
            purchases_updated = []

            try:
                with transaction.atomic():
                    for detail in delivery_details:
                        purchase = detail['purchase']

                        # Calculer la date de livraison estimée
                        estimated_delivery_date = timezone.now()
                        if detail['delivery_method'] == 'pickup':
                            estimated_delivery_date += timedelta(hours=2)  # 2h pour préparation
                        elif detail['delivery_method'] == 'express':
                            estimated_delivery_date += timedelta(days=1)   # 24h
                        elif detail['delivery_method'] == 'home_delivery':
                            estimated_delivery_date += timedelta(days=3)   # 3 jours
                        elif detail['delivery_method'] == 'post_office':
                            estimated_delivery_date += timedelta(days=2)   # 2 jours

                        # Créer la livraison
                        delivery = Delivery.objects.create(
                            purchase=purchase,
                            delivery_method=detail['delivery_method'],
                            delivery_address=detail['delivery_address'] or 'Bibliothèque GPI - Retrait sur place',
                            recipient_name=detail['recipient_name'],
                            recipient_phone=detail['recipient_phone'],
                            recipient_email=user.email,
                            delivery_instructions=detail['delivery_instructions'],
                            delivery_cost=detail['estimated_cost'],
                            estimated_delivery_date=estimated_delivery_date,
                            status='preparing' if detail['delivery_method'] != 'pickup' else 'pending',
                            processed_by=request.user if request.user.is_staff else None
                        )
                        deliveries_created.append(delivery)

                        # Mettre à jour le statut de l'achat
                        if detail['delivery_method'] == 'pickup':
                            purchase.status = 'ready_for_pickup'
                        else:
                            purchase.status = 'preparing_delivery'
                        purchase.save()
                        purchases_updated.append(purchase)

                messages.success(
                    request,
                    f"Livraisons lancées avec succès pour {len(delivery_details)} achat(s). "
                    f"{len(deliveries_created)} livraison(s) créée(s)."
                )
                return redirect('my_purchases')

            except Exception as e:
                messages.error(request, f"Erreur lors de la création des livraisons: {str(e)}")
        else:
            messages.info(request, "Aucun achat payé en attente de livraison.")
            return redirect('my_purchases')

    context = {
        'delivery_details': delivery_details,
        'has_deliveries': len(delivery_details) > 0,
        'user': user,
    }

    return render(request, 'library/launch_all_deliveries.html', context)


@staff_member_required
def admin_launch_delivery(request, purchase_id):
    """Vue admin pour lancer une livraison individuelle"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if request.method == 'POST':
        # Vérifier si une livraison existe déjà
        if hasattr(purchase, 'delivery'):
            messages.warning(request, f"Une livraison existe déjà pour cette commande.")
            return redirect('admin_purchases')

        try:
            # Calculer la date de livraison estimée
            delivery_method = purchase.delivery_preference or 'pickup'
            estimated_delivery_date = timezone.now()

            if delivery_method == 'pickup':
                estimated_delivery_date += timedelta(hours=2)
                status = 'pending'
                purchase.status = 'ready_for_pickup'
            elif delivery_method == 'express':
                estimated_delivery_date += timedelta(days=1)
                status = 'preparing'
                purchase.status = 'preparing_delivery'
            elif delivery_method == 'home_delivery':
                estimated_delivery_date += timedelta(days=3)
                status = 'preparing'
                purchase.status = 'preparing_delivery'
            elif delivery_method == 'post_office':
                estimated_delivery_date += timedelta(days=2)
                status = 'preparing'
                purchase.status = 'preparing_delivery'
            else:
                estimated_delivery_date += timedelta(days=2)
                status = 'preparing'
                purchase.status = 'preparing_delivery'

            # Créer la livraison
            delivery = Delivery.objects.create(
                purchase=purchase,
                delivery_method=delivery_method,
                delivery_address=purchase.delivery_address or 'Bibliothèque GPI - Retrait sur place',
                recipient_name=purchase.recipient_name or purchase.user.get_full_name() or purchase.user.username,
                recipient_phone=purchase.recipient_phone or '',
                recipient_email=purchase.user.email,
                delivery_instructions=purchase.delivery_instructions or '',
                delivery_cost=purchase.delivery_cost or Decimal('0.00'),
                estimated_delivery_date=estimated_delivery_date,
                status=status,
                processed_by=request.user
            )

            purchase.save()

            messages.success(request, f"Livraison créée avec succès pour la commande #{purchase.id}")

        except Exception as e:
            messages.error(request, f"Erreur lors de la création de la livraison: {str(e)}")

    return redirect('admin_purchases')


@login_required
def debug_outstanding_fees(request):
    """Vue de débogage pour analyser les frais impayés"""
    user = request.user

    # Calculer les frais selon la méthode actuelle
    outstanding_amount, outstanding_payments = PaymentService.calculate_outstanding_fees(user)

    # Analyser en détail les emprunts et leurs frais
    active_loans = Loan.objects.filter(
        user=user,
        status__in=['borrowed', 'overdue', 'renewed']
    )

    loan_analysis = []
    calculated_total = Decimal('0.00')

    for loan in active_loans:
        # Vérifier les paiements existants pour cet emprunt
        existing_payments = Payment.objects.filter(
            loan=loan,
            status__in=['completed', 'pending']
        )

        # Calculer les frais théoriques
        loan_fee = Decimal(str(LibraryConfig.get_loan_fee(user.category)))
        late_fee = Decimal('0.00')
        renewal_fee = Decimal('0.00')

        if loan.is_overdue:
            late_fee_per_day = Decimal(str(LibraryConfig.get_late_fee_per_day(user.category)))
            late_fee = late_fee_per_day * loan.days_overdue

        if loan.renewal_count > 0:
            renewal_fee_per_renewal = Decimal(str(LibraryConfig.get_renewal_fee(user.category)))
            renewal_fee = renewal_fee_per_renewal * loan.renewal_count

        total_theoretical = loan_fee + late_fee + renewal_fee

        # Calculer les paiements effectués
        paid_amount = sum(p.amount for p in existing_payments if p.status == 'completed')
        pending_amount = sum(p.amount for p in existing_payments if p.status == 'pending')

        outstanding_for_loan = max(Decimal('0.00'), total_theoretical - paid_amount)
        calculated_total += outstanding_for_loan

        loan_analysis.append({
            'loan': loan,
            'loan_fee': loan_fee,
            'late_fee': late_fee,
            'renewal_fee': renewal_fee,
            'total_theoretical': total_theoretical,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount,
            'outstanding': outstanding_for_loan,
            'existing_payments': existing_payments,
            'days_overdue': loan.days_overdue if loan.is_overdue else 0,
        })

    # Analyser tous les paiements en attente
    all_pending_payments = Payment.objects.filter(
        user=user,
        status='pending'
    )

    context = {
        'user': user,
        'outstanding_amount': outstanding_amount,
        'outstanding_payments': outstanding_payments,
        'calculated_total': calculated_total,
        'loan_analysis': loan_analysis,
        'all_pending_payments': all_pending_payments,
        'active_loans': active_loans,
    }

    return render(request, 'library/debug_outstanding_fees.html', context)


@login_required
def fix_outstanding_fees(request):
    """Vue pour corriger les frais impayés en créant les paiements manquants"""
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_missing_payments':
            # Créer les paiements manquants pour les emprunts
            active_loans = Loan.objects.filter(
                user=user,
                status__in=['borrowed', 'overdue', 'renewed']
            )

            payments_created = []

            try:
                with transaction.atomic():
                    for loan in active_loans:
                        # Vérifier s'il y a déjà des paiements pour cet emprunt
                        existing_loan_payments = Payment.objects.filter(
                            loan=loan,
                            payment_type='loan_fee'
                        )

                        if not existing_loan_payments.exists():
                            loan_fee = Decimal(str(LibraryConfig.get_loan_fee(user.category)))
                            if loan_fee > 0:
                                payment = Payment.objects.create(
                                    user=user,
                                    payment_type='loan_fee',
                                    amount=loan_fee,
                                    payment_method='cash',
                                    status='pending',
                                    loan=loan,
                                    notes=f"Frais d'emprunt pour {loan.book.title}"
                                )
                                payments_created.append(payment)

                        # Créer les paiements pour les frais de retard
                        if loan.is_overdue:
                            existing_late_payments = Payment.objects.filter(
                                loan=loan,
                                payment_type='late_fee'
                            )

                            if not existing_late_payments.exists():
                                late_fee_per_day = Decimal(str(LibraryConfig.get_late_fee_per_day(user.category)))
                                late_fee = late_fee_per_day * loan.days_overdue

                                if late_fee > 0:
                                    payment = Payment.objects.create(
                                        user=user,
                                        payment_type='late_fee',
                                        amount=late_fee,
                                        payment_method='cash',
                                        status='pending',
                                        loan=loan,
                                        notes=f"Frais de retard ({loan.days_overdue} jours) pour {loan.book.title}"
                                    )
                                    payments_created.append(payment)

                        # Créer les paiements pour les renouvellements
                        if loan.renewal_count > 0:
                            existing_renewal_payments = Payment.objects.filter(
                                loan=loan,
                                payment_type='renewal_fee'
                            )

                            if not existing_renewal_payments.exists():
                                renewal_fee_per_renewal = Decimal(str(LibraryConfig.get_renewal_fee(user.category)))
                                renewal_fee = renewal_fee_per_renewal * loan.renewal_count

                                if renewal_fee > 0:
                                    payment = Payment.objects.create(
                                        user=user,
                                        payment_type='renewal_fee',
                                        amount=renewal_fee,
                                        payment_method='cash',
                                        status='pending',
                                        loan=loan,
                                        notes=f"Frais de renouvellement ({loan.renewal_count} renouvellements) pour {loan.book.title}"
                                    )
                                    payments_created.append(payment)

                messages.success(
                    request,
                    f"Correction effectuée : {len(payments_created)} paiement(s) créé(s) pour régulariser les frais."
                )

            except Exception as e:
                messages.error(request, f"Erreur lors de la correction : {str(e)}")

        elif action == 'clear_all_pending':
            # Supprimer tous les paiements en attente (attention !)
            pending_payments = Payment.objects.filter(
                user=user,
                status='pending'
            )
            count = pending_payments.count()
            pending_payments.delete()

            messages.warning(
                request,
                f"Tous les paiements en attente ont été supprimés ({count} paiement(s))."
            )

        return redirect('debug_outstanding_fees')

    return redirect('debug_outstanding_fees')


@login_required
def process_payment(request, payment_id):
    """Traiter le paiement"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    # Vérifier que le paiement peut être traité
    if payment.status not in ['pending']:
        if payment.status == 'completed':
            messages.success(request, "Ce paiement a déjà été effectué avec succès.")
            return redirect('payment_success', payment_id=payment.id)
        else:
            messages.error(request, f"Ce paiement ne peut pas être traité (statut: {payment.get_status_display()}).")
            return redirect('my_purchases')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'confirm_payment':
            # Simuler le traitement du paiement selon la méthode
            success = process_payment_method(payment, request)

            if success:
                payment.status = 'completed'
                payment.processed_by = request.user
                payment.save()

                # Mettre à jour l'achat
                if payment.purchase:
                    payment.purchase.status = 'paid'
                    payment.purchase.save()

                messages.success(request, f"Paiement de {payment.amount}€ effectué avec succès !")
                return redirect('payment_success', payment_id=payment.id)
            else:
                payment.status = 'failed'
                payment.save()
                messages.error(request, "Le paiement a échoué. Veuillez réessayer.")
                return redirect('payment_failed', payment_id=payment.id)

        elif action == 'cancel_payment':
            payment.status = 'cancelled'
            payment.save()
            messages.info(request, "Paiement annulé.")
            return redirect('my_purchases')

    context = {
        'payment': payment,
        'purchase': payment.purchase,
    }
    return render(request, 'payments/process_payment.html', context)


def process_payment_method(payment, request):
    """Traiter le paiement selon la méthode choisie"""
    method = payment.payment_method

    if method == 'cash':
        # Paiement en espèces - nécessite validation manuelle
        payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement en espèces - En attente de validation"
        return False  # Nécessite validation admin

    elif method == 'card':
        # Simulation de paiement par carte
        import random
        success_rate = 0.95  # 95% de réussite
        success = random.random() < success_rate

        if success:
            payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement par carte réussi"
            return True
        else:
            payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement par carte échoué"
            return False

    elif method == 'online':
        # Simulation de paiement en ligne
        import random
        success_rate = 0.90  # 90% de réussite
        success = random.random() < success_rate

        if success:
            payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement en ligne réussi"
            return True
        else:
            payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement en ligne échoué"
            return False

    elif method == 'transfer':
        # Virement - nécessite validation manuelle
        payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Virement initié - En attente de réception"
        return False  # Nécessite validation admin

    elif method == 'mobile':
        # Paiement mobile
        import random
        success_rate = 0.92  # 92% de réussite
        success = random.random() < success_rate

        if success:
            payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement mobile réussi"
            return True
        else:
            payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement mobile échoué"
            return False

    elif method == 'check':
        # Chèque - nécessite validation manuelle
        payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Chèque reçu - En attente d'encaissement"
        return False  # Nécessite validation admin

    elif method == 'free':
        # Gratuit
        payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Paiement gratuit"
        return True

    else:
        # Méthode inconnue
        payment.notes += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Méthode de paiement inconnue: {method}"
        return False


@login_required
def payment_success(request, payment_id):
    """Page de succès du paiement"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    context = {
        'payment': payment,
        'purchase': payment.purchase,
    }
    return render(request, 'payments/payment_success.html', context)


@login_required
def payment_failed(request, payment_id):
    """Page d'échec du paiement"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    context = {
        'payment': payment,
        'purchase': payment.purchase,
    }
    return render(request, 'payments/payment_failed.html', context)


@login_required
def create_test_purchase(request):
    """Créer un achat de test pour démonstration"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('home')

    # Prendre un livre au hasard qui est en vente
    book = Book.objects.filter(is_for_sale=True).first()

    if not book:
        messages.error(request, "Aucun livre en vente trouvé.")
        return redirect('admin_dashboard')

    # Créer un achat de test
    purchase = BookPurchase.objects.create(
        user=request.user,
        book=book,
        quantity=1,
        unit_price=book.purchase_price or 15.00,
        total_price=book.purchase_price or 15.00,
        status='pending',
        notes='Achat de test pour démonstration du système de paiement'
    )

    messages.success(request, f"Achat de test créé : #{purchase.id} - {book.title} ({purchase.total_price}€)")
    return redirect('my_purchases')


@login_required
def my_loans(request):
    """Liste des emprunts de l'utilisateur"""
    current_loans = Loan.objects.filter(
        user=request.user,
        status__in=['borrowed', 'overdue']
    ).select_related('book').order_by('due_date')

    loan_history = Loan.objects.filter(
        user=request.user,
        status__in=['returned', 'renewed']
    ).select_related('book').order_by('-return_date')[:20]

    context = {
        'current_loans': current_loans,
        'loan_history': loan_history,
    }
    return render(request, 'library/my_loans.html', context)


@login_required
def my_reservations(request):
    """Liste des réservations de l'utilisateur"""
    active_reservations = Reservation.objects.filter(
        user=request.user,
        status='active'
    ).select_related('book').order_by('reservation_date')

    reservation_history = Reservation.objects.filter(
        user=request.user,
        status__in=['fulfilled', 'cancelled', 'expired']
    ).select_related('book').order_by('-reservation_date')[:20]

    context = {
        'active_reservations': active_reservations,
        'reservation_history': reservation_history,
    }
    return render(request, 'library/my_reservations.html', context)


@login_required
def borrow_book(request, book_id):
    """Emprunter un livre directement"""
    book = get_object_or_404(Book, id=book_id)
    user = request.user

    # Vérifications
    if not book.is_available:
        messages.error(request, f"Le livre '{book.title}' n'est pas disponible pour l'emprunt.")
        return redirect('book_detail', book_id=book.id)

    # Vérifier les limites d'emprunt
    current_loans = Loan.objects.filter(
        user=user,
        status__in=['borrowed', 'overdue']
    ).count()

    max_books = LibraryConfig.get_max_books(user.category)
    if current_loans >= max_books:
        messages.error(request, f"Vous avez atteint votre limite d'emprunts ({max_books} livres).")
        return redirect('book_detail', book_id=book.id)

    # Vérifier s'il y a des emprunts en retard
    overdue_loans = Loan.objects.filter(
        user=user,
        status='overdue'
    ).count()

    if overdue_loans > 0:
        messages.error(request, f"Vous avez {overdue_loans} livre(s) en retard. Veuillez les retourner avant d'emprunter de nouveaux livres.")
        return redirect('my_loans')

    # Vérifier si l'utilisateur a déjà emprunté ce livre
    existing_loan = Loan.objects.filter(
        user=user,
        book=book,
        status__in=['borrowed', 'overdue']
    ).first()

    if existing_loan:
        messages.warning(request, f"Vous avez déjà emprunté '{book.title}'.")
        return redirect('book_detail', book_id=book.id)

    # Calculer les frais d'emprunt
    loan_fee = PaymentCalculator.calculate_loan_fee(user.category)
    deposit_amount = PaymentCalculator.calculate_deposit_amount(user.category)

    # Vérifier les frais impayés
    outstanding_amount, outstanding_payments = PaymentService.calculate_outstanding_fees(user)
    if outstanding_amount > 0:
        messages.error(request, f"Vous avez {outstanding_amount}€ de frais impayés. Veuillez les régler avant d'emprunter de nouveaux livres.")
        return redirect('my_loans')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')

        try:
            # Créer l'emprunt
            loan_duration = LibraryConfig.get_loan_duration(user.category)
            due_date = timezone.now().date() + timedelta(days=loan_duration)

            loan = Loan.objects.create(
                user=user,
                book=book,
                due_date=due_date,
                status='borrowed'
            )

            # Créer le paiement pour l'emprunt
            loan_payment = PaymentService.create_loan_payment(
                loan=loan,
                payment_method=payment_method,
                processed_by=request.user if request.user.is_staff else None
            )

            # Créer le paiement pour la caution si nécessaire
            deposit_payment = None
            if deposit_amount > 0:
                deposit_payment = PaymentService.create_deposit_payment(
                    user=user,
                    loan=loan,
                    payment_method=payment_method,
                    processed_by=request.user if request.user.is_staff else None
                )

            # Si c'est gratuit, marquer comme payé automatiquement
            if loan_fee == 0:
                PaymentService.process_payment(loan_payment, processed_by=request.user if request.user.is_staff else None)

            if deposit_payment and deposit_amount == 0:
                PaymentService.process_payment(deposit_payment, processed_by=request.user if request.user.is_staff else None)

            # Mettre à jour le stock
            book.available_copies -= 1
            book.save()

            # Message de succès avec informations de paiement
            success_message = f"Livre '{book.title}' emprunté avec succès ! À retourner avant le {due_date.strftime('%d/%m/%Y')}."

            if loan_fee > 0 or deposit_amount > 0:
                total_to_pay = loan_fee + deposit_amount
                success_message += f" Montant à régler: {total_to_pay}€"
                if loan_fee > 0:
                    success_message += f" (Frais d'emprunt: {loan_fee}€"
                    if deposit_amount > 0:
                        success_message += f", Caution: {deposit_amount}€)"
                    else:
                        success_message += ")"
                elif deposit_amount > 0:
                    success_message += f" (Caution: {deposit_amount}€)"

            messages.success(request, success_message)
            return redirect('my_loans')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'emprunt: {str(e)}")
            return redirect('book_detail', book_id=book.id)

    # Afficher la page de confirmation
    loan_duration = LibraryConfig.get_loan_duration(user.category)
    due_date = timezone.now().date() + timedelta(days=loan_duration)

    context = {
        'book': book,
        'due_date': due_date,
        'loan_duration': loan_duration,
        'current_loans': current_loans,
        'max_books': max_books,
        'loan_fee': loan_fee,
        'deposit_amount': deposit_amount,
        'total_cost': loan_fee + deposit_amount,
        'outstanding_amount': outstanding_amount,
        'outstanding_payments': outstanding_payments,
    }
    return render(request, 'library/borrow_confirm.html', context)


# ===== ACTIONS RAPIDES POUR L'ADMINISTRATION =====

@staff_member_required
def admin_purchase_confirm(request, purchase_id):
    """Action rapide : Confirmer un achat depuis l'admin"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status == 'pending':
        purchase.status = 'confirmed'
        purchase.save()
        messages.success(request, f"Commande #{purchase.id} confirmée avec succès.")
    else:
        messages.error(request, f"Cette commande ne peut pas être confirmée (statut: {purchase.get_status_display()}).")

    return redirect('admin:library_bookpurchase_changelist')


@staff_member_required
def admin_purchase_mark_paid(request, purchase_id):
    """Action rapide : Marquer un achat comme payé depuis l'admin"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status in ['pending', 'confirmed']:
        purchase.status = 'paid'
        purchase.save()

        # Créer un paiement si nécessaire
        if not hasattr(purchase, 'payment') or not purchase.payment:
            Payment.objects.create(
                user=purchase.user,
                amount=purchase.total_price,
                payment_type='purchase',
                payment_method='cash',
                status='completed',
                processed_by=request.user,
                purchase=purchase
            )

        messages.success(request, f"Commande #{purchase.id} marquée comme payée.")
    else:
        messages.error(request, f"Cette commande ne peut pas être marquée comme payée (statut: {purchase.get_status_display()}).")

    return redirect('admin:library_bookpurchase_changelist')


@staff_member_required
def admin_purchase_mark_delivered(request, purchase_id):
    """Action rapide : Marquer un achat comme livré depuis l'admin"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status == 'paid':
        purchase.status = 'delivered'
        purchase.save()
        messages.success(request, f"Commande #{purchase.id} marquée comme livrée.")
    else:
        messages.error(request, f"Cette commande ne peut pas être marquée comme livrée (statut: {purchase.get_status_display()}).")

    return redirect('admin:library_bookpurchase_changelist')


@staff_member_required
def admin_purchase_cancel(request, purchase_id):
    """Action rapide : Annuler un achat depuis l'admin"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status in ['pending', 'confirmed']:
        purchase.status = 'cancelled'
        purchase.save()

        # Annuler le paiement associé si il existe
        if hasattr(purchase, 'payment') and purchase.payment:
            purchase.payment.status = 'cancelled'
            purchase.payment.save()

        messages.success(request, f"Commande #{purchase.id} annulée avec succès.")
    else:
        messages.error(request, f"Cette commande ne peut pas être annulée (statut: {purchase.get_status_display()}).")

    return redirect('admin:library_bookpurchase_changelist')


# ===== ACTIONS RAPIDES POUR L'INTERFACE DE GESTION PERSONNALISÉE =====

@staff_member_required
def quick_confirm_purchase(request, purchase_id):
    """Action rapide : Confirmer un achat depuis l'interface de gestion"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status == 'pending':
        purchase.status = 'confirmed'
        purchase.save()
        messages.success(request, f"Commande #{purchase.id} confirmée avec succès.")
    else:
        messages.error(request, f"Cette commande ne peut pas être confirmée (statut: {purchase.get_status_display()}).")

    return redirect('admin_purchases')


@staff_member_required
def quick_mark_paid(request, purchase_id):
    """Action rapide : Marquer un achat comme payé depuis l'interface de gestion"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status in ['pending', 'confirmed']:
        purchase.status = 'paid'
        purchase.save()

        # Créer un paiement si nécessaire
        if not hasattr(purchase, 'payment') or not purchase.payment:
            Payment.objects.create(
                user=purchase.user,
                amount=purchase.total_price,
                payment_type='purchase',
                payment_method='cash',
                status='completed',
                processed_by=request.user,
                purchase=purchase
            )

        messages.success(request, f"Commande #{purchase.id} marquée comme payée.")
    else:
        messages.error(request, f"Cette commande ne peut pas être marquée comme payée (statut: {purchase.get_status_display()}).")

    return redirect('admin_purchases')


@staff_member_required
def quick_mark_delivered(request, purchase_id):
    """Action rapide : Marquer un achat comme livré depuis l'interface de gestion"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status == 'paid':
        purchase.status = 'delivered'
        purchase.save()
        messages.success(request, f"Commande #{purchase.id} marquée comme livrée.")
    else:
        messages.error(request, f"Cette commande ne peut pas être marquée comme livrée (statut: {purchase.get_status_display()}).")

    return redirect('admin_purchases')


@staff_member_required
def quick_cancel_purchase(request, purchase_id):
    """Action rapide : Annuler un achat depuis l'interface de gestion"""
    purchase = get_object_or_404(BookPurchase, id=purchase_id)

    if purchase.status in ['pending', 'confirmed']:
        purchase.status = 'cancelled'
        purchase.save()

        # Annuler le paiement associé si il existe
        if hasattr(purchase, 'payment') and purchase.payment:
            purchase.payment.status = 'cancelled'
            purchase.payment.save()

        messages.success(request, f"Commande #{purchase.id} annulée avec succès.")
    else:
        messages.error(request, f"Cette commande ne peut pas être annulée (statut: {purchase.get_status_display()}).")

    return redirect('admin_purchases')


@login_required
def renew_loan(request, loan_id):
    """Renouveler un emprunt"""
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)

    if request.method == 'POST':
        if loan.can_renew:
            # Calculer la nouvelle date de retour
            duration = LibraryConfig.get_loan_duration(request.user.category)
            loan.due_date = timezone.now().date() + timedelta(days=duration)
            loan.renewal_count += 1
            loan.status = 'renewed'
            loan.save()

            messages.success(request, f"Emprunt renouvelé jusqu'au {loan.due_date}")
        else:
            messages.error(request, "Ce livre ne peut pas être renouvelé.")

    return redirect('my_loans')





@staff_member_required
def admin_loans(request):
    """Gestion des emprunts pour l'administration"""
    loans = Loan.objects.all().select_related('user', 'book').order_by('-loan_date')

    # Filtres
    status = request.GET.get('status')
    user_search = request.GET.get('user_search')
    book_search = request.GET.get('book_search')
    overdue_only = request.GET.get('overdue_only')

    if status:
        loans = loans.filter(status=status)

    if user_search:
        loans = loans.filter(
            Q(user__username__icontains=user_search) |
            Q(user__first_name__icontains=user_search) |
            Q(user__last_name__icontains=user_search)
        )

    if book_search:
        loans = loans.filter(book__title__icontains=book_search)

    if overdue_only:
        loans = loans.filter(status='overdue')

    # Pagination
    paginator = Paginator(loans, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'loans': page_obj,
        'loan_statuses': Loan.LOAN_STATUS,
        'current_status': status,
        'current_user_search': user_search,
        'current_book_search': book_search,
        'current_overdue_only': overdue_only,
    }
    return render(request, 'admin/loans_management.html', context)


@staff_member_required
def admin_reservations(request):
    """Gestion des réservations pour l'administration"""
    reservations = Reservation.objects.all().select_related('user', 'book').order_by('-reservation_date')

    # Filtres
    status = request.GET.get('status')
    user_search = request.GET.get('user_search')
    book_search = request.GET.get('book_search')
    ready_only = request.GET.get('ready_only')

    if status:
        reservations = reservations.filter(status=status)

    if user_search:
        reservations = reservations.filter(
            Q(user__username__icontains=user_search) |
            Q(user__first_name__icontains=user_search) |
            Q(user__last_name__icontains=user_search)
        )

    if book_search:
        reservations = reservations.filter(book__title__icontains=book_search)

    if ready_only:
        reservations = reservations.filter(
            status='active',
            book__available_copies__gt=0
        )

    # Pagination
    paginator = Paginator(reservations, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'reservations': page_obj,
        'reservation_statuses': Reservation.RESERVATION_STATUS,
        'current_status': status,
        'current_user_search': user_search,
        'current_book_search': book_search,
        'current_ready_only': ready_only,
    }
    return render(request, 'admin/reservations_management.html', context)


@staff_member_required
def return_book(request, loan_id):
    """Marquer un livre comme retourné"""
    loan = get_object_or_404(Loan, id=loan_id)

    if request.method == 'POST':
        if loan.status in ['borrowed', 'overdue', 'renewed']:
            loan.status = 'returned'
            loan.return_date = timezone.now()
            loan.save()

            # Remettre le livre en stock
            loan.book.available_copies += 1
            loan.book.save()

            # Traiter les réservations en attente
            from .reservation_services import ReservationService
            reservation_message = ReservationService.handle_book_return(loan.book)

            messages.success(request, f"Livre '{loan.book.title}' retourné par {loan.user.get_full_name()}. {reservation_message}")
        else:
            messages.error(request, "Ce livre a déjà été retourné.")

    return redirect('admin_loans')


@staff_member_required
def fulfill_reservation(request, reservation_id):
    """Satisfaire une réservation (créer un emprunt)"""
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == 'POST':
        # Utiliser le service de réservation
        from .reservation_services import ReservationService

        success, result = ReservationService.fulfill_reservation(reservation, processed_by=request.user)

        if success:
            messages.success(request, f"Réservation satisfaite. Emprunt créé pour {reservation.user.get_full_name()}")
        else:
            messages.error(request, result)

    return redirect('admin_reservations')


# ===== VUES POUR LES FAVORIS =====

@login_required
def toggle_favorite(request, book_id):
    """Ajouter ou retirer un livre des favoris"""
    try:
        book = get_object_or_404(Book, id=book_id)
        user = request.user

        # Vérifier que la méthode est POST
        if request.method != 'POST':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': 'Méthode non autorisée'
                }, status=405)
            return redirect('book_detail', book_id=book.id)

        favorite, created = Favorite.objects.get_or_create(
            user=user,
            book=book
        )

        if created:
            messages.success(request, f"'{book.title}' ajouté à vos favoris.")
            action = 'added'
            message = f"'{book.title}' ajouté à vos favoris."
        else:
            favorite.delete()
            messages.success(request, f"'{book.title}' retiré de vos favoris.")
            action = 'removed'
            message = f"'{book.title}' retiré de vos favoris."

        # Retourner une réponse JSON pour les requêtes AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'success': True,
                'action': action,
                'message': message
            })

        # Redirection normale pour les requêtes non-AJAX
        return redirect(request.META.get('HTTP_REFERER', 'book_detail'), book_id=book.id)

    except Exception as e:
        error_message = f"Erreur lors de la gestion du favori: {str(e)}"

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=500)

        messages.error(request, error_message)
        return redirect('book_detail', book_id=book_id)


@login_required
def my_favorites(request):
    """Liste des livres favoris de l'utilisateur"""
    favorites = Favorite.objects.filter(user=request.user).select_related('book')

    # Pagination
    paginator = Paginator(favorites, 12)  # 12 favoris par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Ajouter des informations supplémentaires pour chaque favori
    for favorite in page_obj:
        # Vérifier si l'utilisateur a déjà emprunté ce livre
        favorite.user_has_loan = Loan.objects.filter(
            user=request.user,
            book=favorite.book,
            status__in=['borrowed', 'overdue']
        ).exists()

        # Vérifier si l'utilisateur a une réservation active
        favorite.user_has_reservation = Reservation.objects.filter(
            user=request.user,
            book=favorite.book,
            status__in=['active', 'ready']
        ).exists()

    context = {
        'favorites': page_obj,
        'total_favorites': favorites.count(),
    }
    return render(request, 'library/my_favorites.html', context)


@login_required
def add_favorite_note(request, favorite_id):
    """Ajouter une note à un favori"""
    favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)

    if request.method == 'POST':
        notes = request.POST.get('notes', '').strip()
        favorite.notes = notes
        favorite.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'success': True,
                'message': 'Note mise à jour avec succès.'
            })

        messages.success(request, 'Note mise à jour avec succès.')

    return redirect('my_favorites')


# ===== VUES AJAX POUR LES INFORMATIONS DE RÉSERVATION =====

def get_book_queue_info(request, book_id):
    """Obtenir les informations de file d'attente pour un livre (AJAX)"""
    book = get_object_or_404(Book, id=book_id)

    from .reservation_services import ReservationService
    queue_info = ReservationService.get_queue_info(book)

    # Calculer le délai d'attente estimé pour l'utilisateur connecté
    estimated_wait_days = 7
    if request.user.is_authenticated and not book.is_available:
        estimated_position = queue_info['active_count'] + 1
        estimated_wait_days = estimated_position * LibraryConfig.get_loan_duration(request.user.category)

    from django.http import JsonResponse
    return JsonResponse({
        'book_id': book.id,
        'book_title': book.title,
        'book_author': book.authors_list,
        'is_available': book.is_available,
        'available_copies': book.available_copies,
        'queue_info': queue_info,
        'estimated_wait_days': estimated_wait_days,
    })


@login_required
def test_favorites(request):
    """Page de test pour les favoris"""
    # Prendre le premier livre disponible pour le test
    book = Book.objects.first()
    if not book:
        messages.error(request, "Aucun livre disponible pour le test")
        return redirect('home')

    # Obtenir les favoris de l'utilisateur
    user_favorites = Favorite.objects.filter(user=request.user).select_related('book')[:5]

    context = {
        'book': book,
        'user_favorites': user_favorites,
    }
    return render(request, 'library/test_favorites.html', context)
