from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    CustomUser, Book, Author, Publisher, Genre, Loan, Reservation,
    BookPurchase, Payment, Deposit
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Administration des utilisateurs personnalisés"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'category', 'is_active_member', 'current_loans_count')
    list_filter = ('category', 'is_active_member', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('phone_number', 'address', 'date_of_birth', 'category', 'is_active_member', 'max_books_allowed')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('phone_number', 'address', 'date_of_birth', 'category', 'is_active_member', 'max_books_allowed')
        }),
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Administration des genres"""
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Administration des auteurs"""
    list_display = ('full_name', 'nationality', 'birth_date', 'death_date')
    list_filter = ('nationality',)
    search_fields = ('first_name', 'last_name', 'nationality')
    ordering = ('last_name', 'first_name')

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Nom complet'


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Administration des éditeurs"""
    list_display = ('name', 'website')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Administration des livres"""
    list_display = ('title', 'authors_display', 'publisher', 'isbn', 'language', 'total_copies', 'available_copies', 'is_available', 'has_cover_image')
    list_filter = ('language', 'genres', 'publisher', 'publication_date')
    search_fields = ('title', 'isbn', 'authors__first_name', 'authors__last_name')
    filter_horizontal = ('authors', 'genres')
    ordering = ('title',)
    date_hierarchy = 'publication_date'

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'authors', 'publisher', 'isbn')
        }),
        ('Détails', {
            'fields': ('genres', 'publication_date', 'language', 'pages', 'description')
        }),
        ('Gestion des exemplaires', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('Vente', {
            'fields': ('is_for_sale', 'purchase_price')
        }),
        ('Média', {
            'fields': ('cover_image', 'cover_image_preview')
        }),
    )

    readonly_fields = ('cover_image_preview',)

    def authors_display(self, obj):
        return obj.authors_list
    authors_display.short_description = 'Auteurs'

    def is_available(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green;">✓ Disponible</span>')
        else:
            return format_html('<span style="color: red;">✗ Indisponible</span>')
    is_available.short_description = 'Disponibilité'

    def has_cover_image(self, obj):
        if obj.cover_image:
            return format_html('<span style="color: green;">✓ Oui</span>')
        else:
            return format_html('<span style="color: red;">✗ Non</span>')
    has_cover_image.short_description = 'Image de couverture'

    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 150px;" />',
                obj.cover_image.url
            )
        return "Aucune image"
    cover_image_preview.short_description = 'Aperçu de la couverture'


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Administration des emprunts"""
    list_display = ('user', 'book_title', 'loan_date', 'due_date', 'return_date', 'status', 'is_overdue_display', 'days_overdue')
    list_filter = ('status', 'loan_date', 'due_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'book__title')
    ordering = ('-loan_date',)
    date_hierarchy = 'loan_date'

    fieldsets = (
        ('Informations principales', {
            'fields': ('user', 'book', 'status')
        }),
        ('Dates', {
            'fields': ('loan_date', 'due_date', 'return_date')
        }),
        ('Renouvellements', {
            'fields': ('renewal_count', 'max_renewals')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

    readonly_fields = ('loan_date',)

    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = 'Livre'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">✗ En retard</span>')
        else:
            return format_html('<span style="color: green;">✓ À jour</span>')
    is_overdue_display.short_description = 'Statut retard'

    actions = ['mark_as_returned']

    def mark_as_returned(self, request, queryset):
        for loan in queryset:
            if loan.status in ['borrowed', 'overdue']:
                loan.return_book()
        self.message_user(request, f"{queryset.count()} emprunt(s) marqué(s) comme rendu(s).")
    mark_as_returned.short_description = "Marquer comme rendu"


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Administration des réservations"""
    list_display = ('user', 'book_title', 'reservation_date', 'expiry_date', 'status', 'notification_sent')
    list_filter = ('status', 'reservation_date', 'notification_sent')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'book__title')
    ordering = ('-reservation_date',)
    date_hierarchy = 'reservation_date'

    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = 'Livre'

    actions = ['cancel_reservations']

    def cancel_reservations(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} réservation(s) annulée(s).")
    cancel_reservations.short_description = "Annuler les réservations"




@admin.register(BookPurchase)
class BookPurchaseAdmin(admin.ModelAdmin):
    """Administration des achats de livres"""
    list_display = ('user', 'book_title', 'quantity', 'unit_price', 'discount_percentage', 'total_price', 'status_badge', 'purchase_date', 'action_buttons')
    list_filter = ('status', 'purchase_date', 'book__genres')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'book__title', 'book__isbn')
    ordering = ('-purchase_date',)
    date_hierarchy = 'purchase_date'
    list_per_page = 25

    fieldsets = (
        ('Informations principales', {
            'fields': ('user', 'book', 'quantity', 'status')
        }),
        ('Prix', {
            'fields': ('unit_price', 'discount_percentage', 'total_price')
        }),
        ('Livraison', {
            'fields': ('delivery_address', 'notes')
        }),
        ('Métadonnées', {
            'fields': ('purchase_date',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('total_price', 'purchase_date')

    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = 'Livre'

    def status_badge(self, obj):
        """Affiche le statut avec un badge coloré"""
        colors = {
            'pending': '#6c757d',      # Gris
            'confirmed': '#007bff',    # Bleu
            'paid': '#17a2b8',         # Cyan
            'delivered': '#28a745',    # Vert
            'cancelled': '#dc3545',    # Rouge
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    def action_buttons(self, obj):
        """Affiche des boutons d'action rapide"""
        buttons = []

        if obj.status == 'pending':
            buttons.append(
                f'<a href="/admin/library/bookpurchase/{obj.id}/confirm/" '
                f'style="background-color: #007bff; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px; margin-right: 2px;" '
                f'onclick="return confirm(\'Confirmer cette commande ?\')">Confirmer</a>'
            )

        if obj.status in ['pending', 'confirmed']:
            buttons.append(
                f'<a href="/admin/library/bookpurchase/{obj.id}/mark_paid/" '
                f'style="background-color: #28a745; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px; margin-right: 2px;" '
                f'onclick="return confirm(\'Marquer comme payé ?\')">Payer</a>'
            )
            buttons.append(
                f'<a href="/admin/library/bookpurchase/{obj.id}/cancel/" '
                f'style="background-color: #dc3545; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px; margin-right: 2px;" '
                f'onclick="return confirm(\'Annuler cette commande ?\')">Annuler</a>'
            )

        if obj.status == 'paid':
            buttons.append(
                f'<a href="/admin/library/bookpurchase/{obj.id}/mark_delivered/" '
                f'style="background-color: #17a2b8; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px; margin-right: 2px;" '
                f'onclick="return confirm(\'Marquer comme livré ?\')">Livrer</a>'
            )

        return format_html(''.join(buttons))
    action_buttons.short_description = 'Actions'
    action_buttons.allow_tags = True

    actions = [
        'mark_as_pending', 'mark_as_confirmed', 'mark_as_paid',
        'mark_as_delivered', 'mark_as_cancelled', 'export_to_csv'
    ]

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme en attente.")
    mark_as_pending.short_description = "📋 Marquer comme en attente"

    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme confirmé(s).")
    mark_as_confirmed.short_description = "✅ Marquer comme confirmé"

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme payé(s).")
    mark_as_paid.short_description = "💳 Marquer comme payé"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme livré(s).")
    mark_as_delivered.short_description = "📦 Marquer comme livré"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme annulé(s).")
    mark_as_cancelled.short_description = "❌ Marquer comme annulé"

    def export_to_csv(self, request, queryset):
        """Exporter les achats sélectionnés en CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="achats.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Utilisateur', 'Livre', 'Quantité', 'Prix unitaire',
            'Remise %', 'Prix total', 'Statut', 'Date d\'achat'
        ])

        for purchase in queryset:
            writer.writerow([
                purchase.id,
                purchase.user.get_full_name() or purchase.user.username,
                purchase.book.title,
                purchase.quantity,
                purchase.unit_price,
                purchase.discount_percentage,
                purchase.total_price,
                purchase.get_status_display(),
                purchase.purchase_date.strftime('%d/%m/%Y %H:%M')
            ])

        return response
    export_to_csv.short_description = "📊 Exporter en CSV"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Administration des paiements"""
    list_display = ('user', 'payment_type', 'amount', 'payment_method', 'status', 'payment_date', 'processed_by')
    list_filter = ('payment_type', 'payment_method', 'status', 'payment_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'transaction_id')
    ordering = ('-payment_date',)
    date_hierarchy = 'payment_date'

    fieldsets = (
        ('Informations principales', {
            'fields': ('user', 'payment_type', 'amount', 'payment_method', 'status')
        }),
        ('Relations', {
            'fields': ('purchase',)
        }),
        ('Détails de transaction', {
            'fields': ('transaction_id', 'processed_by', 'notes')
        }),
    )

    readonly_fields = ('payment_date',)


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    """Administration des cautions"""
    list_display = ('user', 'amount', 'status', 'deposit_date', 'return_date', 'processed_by')
    list_filter = ('status', 'deposit_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    ordering = ('-deposit_date',)
    date_hierarchy = 'deposit_date'

    fieldsets = (
        ('Informations principales', {
            'fields': ('user', 'amount', 'status')
        }),
        ('Relations', {
            'fields': ('loan', 'payment')
        }),
        ('Traitement', {
            'fields': ('reason', 'processed_by')
        }),
    )

    readonly_fields = ('deposit_date', 'return_date')

    actions = ['return_deposits', 'forfeit_deposits']

    def return_deposits(self, request, queryset):
        for deposit in queryset.filter(status='active'):
            deposit.return_deposit(processed_by=request.user)
        self.message_user(request, f"Cautions rendues.")
    return_deposits.short_description = "Rendre les cautions"

    def forfeit_deposits(self, request, queryset):
        for deposit in queryset.filter(status='active'):
            deposit.forfeit_deposit(reason="Confisquée par admin", processed_by=request.user)
        self.message_user(request, f"Cautions confisquées.")
    forfeit_deposits.short_description = "Confisquer les cautions"



