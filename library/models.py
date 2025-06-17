from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class CustomUser(AbstractUser):
    """Modèle utilisateur étendu pour la bibliothèque"""
    USER_CATEGORIES = [
        ('student', 'Étudiant'),
        ('teacher', 'Professeur'),
        ('staff', 'Personnel'),
        ('external', 'Externe'),
    ]

    phone_number = models.CharField(max_length=15, blank=True, verbose_name="Numéro de téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    category = models.CharField(max_length=10, choices=USER_CATEGORIES, default='student', verbose_name="Catégorie")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    is_active_member = models.BooleanField(default=True, verbose_name="Membre actif")
    is_super_admin = models.BooleanField(default=False, verbose_name="Super administrateur")
    max_books_allowed = models.IntegerField(default=3, verbose_name="Nombre max de livres autorisés")

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

    @property
    def current_loans_count(self):
        """Retourne le nombre d'emprunts actuels"""
        return self.loans.filter(status='borrowed').count()

    @property
    def can_borrow_more(self):
        """Vérifie si l'utilisateur peut emprunter plus de livres"""
        max_allowed = LibraryConfig.get_max_books(self.category)
        return self.current_loans_count < max_allowed

    @property
    def is_admin_user(self):
        """Vérifie si l'utilisateur est administrateur (staff ou super admin)"""
        return self.is_staff or self.is_super_admin

    @property
    def can_access_admin(self):
        """Vérifie si l'utilisateur peut accéder à l'administration"""
        return self.is_staff or self.is_super_admin

    @property
    def can_manage_users(self):
        """Vérifie si l'utilisateur peut gérer les autres utilisateurs"""
        return self.is_super_admin or self.is_superuser

    @property
    def can_manage_system(self):
        """Vérifie si l'utilisateur peut gérer le système complet"""
        return self.is_super_admin or self.is_superuser

    def get_admin_level(self):
        """Retourne le niveau d'administration"""
        if self.is_superuser:
            return 'superuser'
        elif self.is_super_admin:
            return 'super_admin'
        elif self.is_staff:
            return 'staff'
        else:
            return 'user'




class Genre(models.Model):
    """Modèle pour les genres de livres"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du genre")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    """Modèle pour les auteurs"""
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    death_date = models.DateField(null=True, blank=True, verbose_name="Date de décès")
    biography = models.TextField(blank=True, verbose_name="Biographie")
    nationality = models.CharField(max_length=100, blank=True, verbose_name="Nationalité")

    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Publisher(models.Model):
    """Modèle pour les éditeurs"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Nom de l'éditeur")
    address = models.TextField(blank=True, verbose_name="Adresse")
    website = models.URLField(blank=True, verbose_name="Site web")

    class Meta:
        verbose_name = "Éditeur"
        verbose_name_plural = "Éditeurs"
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """Modèle pour les livres"""
    BOOK_STATUS = [
        ('available', 'Disponible'),
        ('borrowed', 'Emprunté'),
        ('reserved', 'Réservé'),
        ('maintenance', 'En réparation'),
        ('lost', 'Perdu'),
    ]

    LANGUAGES = [
        ('fr', 'Français'),
        ('en', 'Anglais'),
        ('es', 'Espagnol'),
        ('de', 'Allemand'),
        ('it', 'Italien'),
        ('other', 'Autre'),
    ]

    title = models.CharField(max_length=300, verbose_name="Titre")
    authors = models.ManyToManyField(Author, verbose_name="Auteurs")
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Éditeur")
    isbn = models.CharField(max_length=17, unique=True, verbose_name="ISBN")
    genres = models.ManyToManyField(Genre, verbose_name="Genres")
    publication_date = models.DateField(verbose_name="Date de publication")
    language = models.CharField(max_length=10, choices=LANGUAGES, default='fr', verbose_name="Langue")
    pages = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Nombre de pages")
    total_copies = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Nombre total d'exemplaires")
    available_copies = models.IntegerField(default=1, validators=[MinValueValidator(0)], verbose_name="Exemplaires disponibles")
    description = models.TextField(blank=True, verbose_name="Description")
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, verbose_name="Image de couverture")

    # Informations d'achat
    purchase_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Prix d'achat (€)")
    is_for_sale = models.BooleanField(default=False, verbose_name="Disponible à la vente")

    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Livre"
        verbose_name_plural = "Livres"
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {', '.join([str(author) for author in self.authors.all()])}"

    @property
    def is_available(self):
        """Vérifie si le livre est disponible pour emprunt"""
        return self.available_copies > 0

    @property
    def authors_list(self):
        """Retourne la liste des auteurs sous forme de chaîne"""
        return ", ".join([author.full_name for author in self.authors.all()])

    @property
    def genres_list(self):
        """Retourne la liste des genres sous forme de chaîne"""
        return ", ".join([genre.name for genre in self.genres.all()])

    def save(self, *args, **kwargs):
        # S'assurer que available_copies ne dépasse pas total_copies
        if self.available_copies > self.total_copies:
            self.available_copies = self.total_copies
        super().save(*args, **kwargs)


class Loan(models.Model):
    """Modèle pour les emprunts"""
    LOAN_STATUS = [
        ('borrowed', 'Emprunté'),
        ('returned', 'Rendu'),
        ('overdue', 'En retard'),
        ('renewed', 'Renouvelé'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='loans', verbose_name="Utilisateur")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans', verbose_name="Livre")
    loan_date = models.DateTimeField(auto_now_add=True, verbose_name="Date d'emprunt")
    due_date = models.DateField(verbose_name="Date de retour prévue")
    return_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de retour effective")
    status = models.CharField(max_length=10, choices=LOAN_STATUS, default='borrowed', verbose_name="Statut")
    renewal_count = models.IntegerField(default=0, verbose_name="Nombre de renouvellements")
    max_renewals = models.IntegerField(default=2, verbose_name="Renouvellements maximum autorisés")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Emprunt"
        verbose_name_plural = "Emprunts"
        ordering = ['-loan_date']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"

    @property
    def is_overdue(self):
        """Vérifie si l'emprunt est en retard"""
        if self.status == 'returned':
            return False
        return timezone.now().date() > self.due_date

    @property
    def days_overdue(self):
        """Calcule le nombre de jours de retard"""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    @property
    def can_renew(self):
        """Vérifie si l'emprunt peut être renouvelé"""
        return (self.renewal_count < self.max_renewals and
                self.status == 'borrowed' and
                not self.is_overdue)

    def renew(self, days=14):
        """Renouvelle l'emprunt"""
        if self.can_renew:
            self.due_date += timedelta(days=days)
            self.renewal_count += 1
            self.status = 'renewed'
            self.save()
            return True
        return False

    def return_book(self):
        """Marque le livre comme rendu"""
        self.return_date = timezone.now()
        self.status = 'returned'
        self.book.available_copies += 1
        self.book.save()
        self.save()

    def save(self, *args, **kwargs):
        # Définir la date de retour selon les paramètres si pas définie
        if not self.due_date:
            duration = LibraryConfig.get_loan_duration(self.user.category)
            self.due_date = (self.loan_date + timedelta(days=duration)).date()

        # Mettre à jour le statut si en retard
        if self.is_overdue and self.status == 'borrowed':
            self.status = 'overdue'
        super().save(*args, **kwargs)




class Reservation(models.Model):
    """Modèle pour les réservations"""
    RESERVATION_STATUS = [
        ('active', 'En attente'),
        ('ready', 'Prête'),
        ('fulfilled', 'Satisfaite'),
        ('cancelled', 'Annulée'),
        ('expired', 'Expirée'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reservations', verbose_name="Utilisateur")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations', verbose_name="Livre")
    reservation_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de réservation")
    expiry_date = models.DateTimeField(verbose_name="Date d'expiration")
    ready_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de disponibilité")
    status = models.CharField(max_length=10, choices=RESERVATION_STATUS, default='active', verbose_name="Statut")
    notification_sent = models.BooleanField(default=False, verbose_name="Notification envoyée")
    priority = models.IntegerField(default=0, verbose_name="Priorité")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['priority', 'reservation_date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=models.Q(status__in=['active', 'ready']),
                name='unique_active_reservation_per_user_book'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.get_status_display()})"

    @property
    def is_expired(self):
        """Vérifie si la réservation a expiré"""
        if self.status == 'ready' and self.ready_date:
            # Pour les réservations prêtes, expiration après RESERVATION_HOLD_DURATION jours
            expiry = self.ready_date + timedelta(days=LibraryConfig.RESERVATION_HOLD_DURATION)
            return timezone.now() > expiry
        return timezone.now() > self.expiry_date

    @property
    def is_ready(self):
        """Vérifie si la réservation est prête"""
        return self.status == 'ready' and not self.is_expired

    @property
    def is_active(self):
        """Vérifie si la réservation est active"""
        return self.status == 'active'

    def get_position_in_queue(self):
        """Obtient la position dans la file d'attente"""
        if self.status != 'active':
            return 0

        return Reservation.objects.filter(
            book=self.book,
            status='active',
            reservation_date__lt=self.reservation_date
        ).count() + 1

    def estimate_wait_time(self):
        """Estime le temps d'attente en jours"""
        position = self.get_position_in_queue()
        if position <= 1:
            return 0

        # Estimation basée sur la durée moyenne d'emprunt
        avg_loan_duration = LibraryConfig.get_loan_duration(self.user.category)
        return (position - 1) * avg_loan_duration

    def mark_as_ready(self):
        """Marque la réservation comme prête"""
        if self.status == 'active':
            self.status = 'ready'
            self.ready_date = timezone.now()
            self.notification_sent = False  # Reset pour envoyer notification
            self.save()
            return True
        return False

    def mark_as_fulfilled(self):
        """Marque la réservation comme satisfaite"""
        if self.status in ['active', 'ready']:
            self.status = 'fulfilled'
            self.save()
            return True
        return False

    def mark_as_expired(self):
        """Marque la réservation comme expirée"""
        if self.status in ['active', 'ready']:
            self.status = 'expired'
            self.save()
            return True
        return False

    def cancel(self):
        """Annule la réservation"""
        if self.status in ['active', 'ready']:
            self.status = 'cancelled'
            self.save()
            return True
        return False

    def can_be_cancelled(self):
        """Vérifie si la réservation peut être annulée"""
        return self.status in ['active', 'ready']

    def get_expiry_date_display(self):
        """Retourne la date d'expiration appropriée selon le statut"""
        if self.status == 'ready' and self.ready_date:
            return self.ready_date + timedelta(days=LibraryConfig.RESERVATION_HOLD_DURATION)
        return self.expiry_date

    @classmethod
    def cleanup_expired_reservations(cls):
        """Nettoie les réservations expirées"""
        now = timezone.now()
        count = 0

        # Réservations actives expirées
        expired_active = cls.objects.filter(
            status='active',
            expiry_date__lt=now
        )

        for reservation in expired_active:
            if reservation.mark_as_expired():
                count += 1

        # Réservations prêtes expirées
        expired_ready = cls.objects.filter(
            status='ready',
            ready_date__lt=now - timedelta(days=LibraryConfig.RESERVATION_HOLD_DURATION)
        )

        for reservation in expired_ready:
            if reservation.mark_as_expired():
                count += 1

        return count

    @classmethod
    def process_ready_reservations(cls):
        """Traite les réservations qui peuvent devenir prêtes"""
        ready_count = 0

        # Trouver les livres avec des exemplaires disponibles
        available_books = Book.objects.filter(available_copies__gt=0)

        for book in available_books:
            # Trouver la première réservation active pour ce livre
            next_reservation = cls.objects.filter(
                book=book,
                status='active'
            ).order_by('priority', 'reservation_date').first()

            if next_reservation and next_reservation.mark_as_ready():
                ready_count += 1

        return ready_count

    def save(self, *args, **kwargs):
        # Définir la date d'expiration si pas définie (7 jours par défaut)
        if not self.expiry_date:
            self.expiry_date = timezone.now() + timedelta(days=7)

        # Mettre à jour le statut si expiré
        if self.is_expired and self.status == 'active':
            self.status = 'expired'

        super().save(*args, **kwargs)





class Favorite(models.Model):
    """Modèle pour les livres favoris"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorites', verbose_name="Utilisateur")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Livre")
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    notes = models.TextField(blank=True, verbose_name="Notes personnelles")

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
        unique_together = ['user', 'book']
        ordering = ['-added_date']

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Report(models.Model):
    """Modèle pour les rapports de la bibliothèque"""
    REPORT_TYPES = [
        ('loans', 'Rapport des emprunts'),
        ('reservations', 'Rapport des réservations'),
        ('purchases', 'Rapport des achats'),
        ('payments', 'Rapport des paiements'),
        ('users', 'Rapport des utilisateurs'),
        ('books', 'Rapport des livres'),
        ('overdue', 'Rapport des retards'),
        ('statistics', 'Rapport statistiques'),
        ('financial', 'Rapport financier'),
        ('inventory', 'Rapport d\'inventaire'),
    ]

    REPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel (XLSX)'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]

    REPORT_STATUS = [
        ('pending', 'En attente'),
        ('generating', 'En cours de génération'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('expired', 'Expiré'),
    ]

    title = models.CharField(max_length=200, verbose_name="Titre du rapport")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Type de rapport")
    format = models.CharField(max_length=10, choices=REPORT_FORMATS, default='pdf', verbose_name="Format")
    status = models.CharField(max_length=15, choices=REPORT_STATUS, default='pending', verbose_name="Statut")

    # Paramètres du rapport
    date_from = models.DateField(null=True, blank=True, verbose_name="Date de début")
    date_to = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    user_category = models.CharField(max_length=20, blank=True, verbose_name="Catégorie d'utilisateur")
    book_genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Genre de livre")
    include_details = models.BooleanField(default=True, verbose_name="Inclure les détails")

    # Métadonnées
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_reports', verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    generated_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de génération")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Date d'expiration")

    # Fichier généré
    file = models.FileField(upload_to='reports/', null=True, blank=True, verbose_name="Fichier du rapport")
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name="Taille du fichier (bytes)")

    # Statistiques
    total_records = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nombre total d'enregistrements")
    generation_time = models.DurationField(null=True, blank=True, verbose_name="Temps de génération")
    download_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de téléchargements")

    # Notes et erreurs
    description = models.TextField(blank=True, verbose_name="Description")
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")

    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_report_type_display()} ({self.get_status_display()})"

    @property
    def is_expired(self):
        """Vérifie si le rapport est expiré"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def file_size_human(self):
        """Retourne la taille du fichier en format lisible"""
        if not self.file_size:
            return "N/A"

        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def mark_as_generating(self):
        """Marquer le rapport comme en cours de génération"""
        self.status = 'generating'
        self.save()

    def mark_as_completed(self, file_path, total_records=None, generation_time=None):
        """Marquer le rapport comme terminé"""
        self.status = 'completed'
        self.file = file_path
        self.generated_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(days=30)  # Expire après 30 jours

        if total_records is not None:
            self.total_records = total_records
        if generation_time is not None:
            self.generation_time = generation_time

        # Calculer la taille du fichier
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size

        self.save()

    def mark_as_failed(self, error_message):
        """Marquer le rapport comme échoué"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()

    def increment_download_count(self):
        """Incrémenter le compteur de téléchargements"""
        self.download_count += 1
        self.save(update_fields=['download_count'])


# Configuration de la bibliothèque (constantes)
class LibraryConfig:
    """Configuration de la bibliothèque avec valeurs par défaut"""

    # Durées d'emprunt par catégorie (en jours)
    LOAN_DURATIONS = {
        'student': 14,
        'teacher': 30,
        'staff': 21,
        'external': 7,
    }

    # Limites d'emprunt par catégorie
    MAX_BOOKS = {
        'student': 3,
        'teacher': 10,
        'staff': 5,
        'external': 2,
    }

    # Remises d'achat par catégorie (en pourcentage)
    PURCHASE_DISCOUNTS = {
        'student': 10.0,
        'teacher': 15.0,
        'staff': 15.0,
        'external': 0.0,
    }

    # Frais d'emprunt par catégorie d'utilisateur (en euros)
    LOAN_FEES = {
        'student': 0.0,   # Gratuit pour les étudiants
        'teacher': 0.0,   # Gratuit pour les enseignants
        'staff': 0.0,     # Gratuit pour le personnel
        'external': 2.0,  # 2€ par emprunt pour les externes
    }

    # Frais de renouvellement par catégorie d'utilisateur (en euros)
    RENEWAL_FEES = {
        'student': 0.0,   # Gratuit pour les étudiants
        'teacher': 0.0,   # Gratuit pour les enseignants
        'staff': 0.0,     # Gratuit pour le personnel
        'external': 1.0,  # 1€ par renouvellement pour les externes
    }

    # Frais de retard par jour et par catégorie d'utilisateur (en euros)
    LATE_FEES_PER_DAY = {
        'student': 0.5,   # 0.50€ par jour pour les étudiants
        'teacher': 0.0,   # Pas de frais pour les enseignants
        'staff': 0.0,     # Pas de frais pour le personnel
        'external': 1.0,  # 1€ par jour pour les externes
    }

    # Caution par catégorie d'utilisateur (en euros)
    DEPOSIT_AMOUNTS = {
        'student': 10.0,  # 10€ de caution pour les étudiants
        'teacher': 0.0,   # Pas de caution pour les enseignants
        'staff': 0.0,     # Pas de caution pour le personnel
        'external': 20.0, # 20€ de caution pour les externes
    }

    # Autres paramètres
    RESERVATION_DURATION = 7  # jours
    RESERVATION_HOLD_DURATION = 3  # jours
    ENABLE_BOOK_PURCHASE = True
    REQUIRE_DEPOSIT = False
    DEPOSIT_AMOUNT = 20.00  # euros (valeur par défaut, remplacée par DEPOSIT_AMOUNTS)
    ACCEPT_CASH = True
    ACCEPT_CARD = True
    ACCEPT_ONLINE = False

    @classmethod
    def get_loan_duration(cls, user_category):
        """Retourne la durée d'emprunt selon la catégorie d'utilisateur"""
        return cls.LOAN_DURATIONS.get(user_category, 14)

    @classmethod
    def get_max_books(cls, user_category):
        """Retourne le nombre maximum de livres selon la catégorie d'utilisateur"""
        return cls.MAX_BOOKS.get(user_category, 3)

    @classmethod
    def get_purchase_discount(cls, user_category):
        """Retourne la remise d'achat selon la catégorie d'utilisateur"""
        return cls.PURCHASE_DISCOUNTS.get(user_category, 0.0)

    @classmethod
    def get_loan_fee(cls, user_category):
        """Retourne les frais d'emprunt selon la catégorie d'utilisateur"""
        return cls.LOAN_FEES.get(user_category, 0.0)

    @classmethod
    def get_renewal_fee(cls, user_category):
        """Retourne les frais de renouvellement selon la catégorie d'utilisateur"""
        return cls.RENEWAL_FEES.get(user_category, 0.0)

    @classmethod
    def get_late_fee_per_day(cls, user_category):
        """Retourne les frais de retard par jour selon la catégorie d'utilisateur"""
        return cls.LATE_FEES_PER_DAY.get(user_category, 0.0)

    @classmethod
    def get_deposit_amount(cls, user_category):
        """Retourne le montant de la caution selon la catégorie d'utilisateur"""
        return cls.DEPOSIT_AMOUNTS.get(user_category, 0.0)


class BookPurchase(models.Model):
    """Modèle pour les achats de livres"""
    PURCHASE_STATUS = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('paid', 'Payé'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    ]

    DELIVERY_PREFERENCES = [
        ('pickup', 'Retrait en bibliothèque'),
        ('home_delivery', 'Livraison à domicile'),
        ('post_office', 'Point relais'),
        ('express', 'Livraison express'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchases', verbose_name="Acheteur")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='purchases', verbose_name="Livre")
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Quantité")
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix unitaire (€)")
    discount_percentage = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('0.0'), verbose_name="Remise (%)")
    total_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix total (€)")
    status = models.CharField(max_length=10, choices=PURCHASE_STATUS, default='pending', verbose_name="Statut")
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name="Date d'achat")

    # Informations de livraison
    delivery_preference = models.CharField(max_length=15, choices=DELIVERY_PREFERENCES, default='pickup', verbose_name="Préférence de livraison")
    delivery_address = models.TextField(blank=True, verbose_name="Adresse de livraison")
    delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), verbose_name="Coût de livraison (€)")
    recipient_name = models.CharField(max_length=200, blank=True, verbose_name="Nom du destinataire")
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone du destinataire")
    delivery_instructions = models.TextField(blank=True, verbose_name="Instructions de livraison")

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Achat de livre"
        verbose_name_plural = "Achats de livres"
        ordering = ['-purchase_date']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.quantity}x)"

    def save(self, *args, **kwargs):
        # Calculer le prix total avec remise
        discount_percentage_decimal = Decimal(str(self.discount_percentage))
        discount_amount = (self.unit_price * discount_percentage_decimal / Decimal('100'))
        discounted_price = self.unit_price - discount_amount
        self.total_price = discounted_price * self.quantity
        super().save(*args, **kwargs)

    @property
    def discount_amount(self):
        """Calcule le montant de la remise"""
        discount_percentage_decimal = Decimal(str(self.discount_percentage))
        return (self.unit_price * discount_percentage_decimal / Decimal('100')) * self.quantity


class Payment(models.Model):
    """Modèle pour les paiements"""
    PAYMENT_TYPES = [
        ('purchase', 'Achat de livre'),
        ('loan_fee', 'Frais d\'emprunt'),
        ('deposit', 'Caution'),
        ('fine', 'Amende'),
        ('renewal_fee', 'Frais de renouvellement'),
        ('late_fee', 'Frais de retard'),
        ('damage_fee', 'Frais de dégradation'),
        ('refund', 'Remboursement'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Espèces'),
        ('card', 'Carte bancaire'),
        ('transfer', 'Virement'),
        ('online', 'Paiement en ligne'),
        ('check', 'Chèque'),
        ('mobile', 'Paiement mobile'),
        ('free', 'Gratuit'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'En attente'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
        ('cancelled', 'Annulé'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments', verbose_name="Utilisateur")
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPES, verbose_name="Type de paiement")
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Montant (€)")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, verbose_name="Méthode de paiement")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending', verbose_name="Statut")

    # Relations optionnelles (un paiement peut être lié à un achat OU un emprunt)
    purchase = models.ForeignKey(BookPurchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="Achat")
    loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="Emprunt")

    # Informations de paiement
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="ID de transaction")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de paiement")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Date d'échéance")
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments', verbose_name="Traité par")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-payment_date']

    def __str__(self):
        related_item = ""
        if self.purchase:
            related_item = f" (Achat: {self.purchase.book.title})"
        elif self.loan:
            related_item = f" (Emprunt: {self.loan.book.title})"
        return f"{self.user.username} - {self.get_payment_type_display()} - {self.amount}€{related_item}"

    @property
    def is_overdue(self):
        """Vérifie si le paiement est en retard"""
        if self.due_date and self.status == 'pending':
            return timezone.now() > self.due_date
        return False

    @property
    def related_object(self):
        """Retourne l'objet lié (achat ou emprunt)"""
        return self.purchase or self.loan

    def mark_as_completed(self, processed_by=None, transaction_id=''):
        """Marquer le paiement comme terminé"""
        self.status = 'completed'
        self.processed_by = processed_by
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

    def mark_as_failed(self, reason=''):
        """Marquer le paiement comme échoué"""
        self.status = 'failed'
        if reason:
            self.notes = f"{self.notes}\nÉchec: {reason}".strip()
        self.save()

    def refund(self, processed_by=None, reason=''):
        """Rembourser le paiement"""
        if self.status == 'completed':
            self.status = 'refunded'
            self.processed_by = processed_by
            if reason:
                self.notes = f"{self.notes}\nRemboursement: {reason}".strip()
            self.save()
            return True
        return False



class Deposit(models.Model):
    """Modèle pour les cautions"""
    DEPOSIT_STATUS = [
        ('active', 'Active'),
        ('returned', 'Rendue'),
        ('forfeited', 'Confisquée'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='deposits', verbose_name="Utilisateur")
    amount = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Montant (€)")
    status = models.CharField(max_length=10, choices=DEPOSIT_STATUS, default='active', verbose_name="Statut")

    # Relations
    loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True, related_name='deposits', verbose_name="Emprunt")
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Paiement")

    # Dates
    deposit_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de dépôt")
    return_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de retour")

    reason = models.TextField(blank=True, verbose_name="Raison")
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_deposits', verbose_name="Traité par")

    class Meta:
        verbose_name = "Caution"
        verbose_name_plural = "Cautions"
        ordering = ['-deposit_date']

    def __str__(self):
        return f"{self.user.username} - {self.amount}€ ({self.get_status_display()})"

    def return_deposit(self, processed_by=None):
        """Rendre la caution"""
        self.status = 'returned'
        self.return_date = timezone.now()
        self.processed_by = processed_by
        self.save()

    def forfeit_deposit(self, reason='', processed_by=None):
        """Confisquer la caution"""
        self.status = 'forfeited'
        self.reason = reason
        self.processed_by = processed_by
        self.save()


class Delivery(models.Model):
    """Modèle pour les livraisons d'achats"""
    DELIVERY_STATUS = [
        ('pending', 'En attente'),
        ('preparing', 'En préparation'),
        ('shipped', 'Expédié'),
        ('in_transit', 'En transit'),
        ('delivered', 'Livré'),
        ('failed', 'Échec de livraison'),
        ('returned', 'Retourné'),
        ('cancelled', 'Annulé'),
    ]

    DELIVERY_METHODS = [
        ('pickup', 'Retrait en bibliothèque'),
        ('home_delivery', 'Livraison à domicile'),
        ('post_office', 'Point relais'),
        ('express', 'Livraison express'),
        ('registered', 'Courrier recommandé'),
    ]

    # Relations
    purchase = models.OneToOneField(BookPurchase, on_delete=models.CASCADE, related_name='delivery', verbose_name="Achat")

    # Informations de livraison
    delivery_method = models.CharField(max_length=15, choices=DELIVERY_METHODS, default='pickup', verbose_name="Méthode de livraison")
    status = models.CharField(max_length=12, choices=DELIVERY_STATUS, default='pending', verbose_name="Statut")

    # Adresses
    delivery_address = models.TextField(verbose_name="Adresse de livraison")
    pickup_location = models.CharField(max_length=200, blank=True, verbose_name="Lieu de retrait")

    # Dates
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    estimated_delivery_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de livraison estimée")
    actual_delivery_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de livraison réelle")

    # Informations de suivi
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de suivi")
    carrier = models.CharField(max_length=100, blank=True, verbose_name="Transporteur")
    delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), verbose_name="Coût de livraison (€)")

    # Contact
    recipient_name = models.CharField(max_length=200, verbose_name="Nom du destinataire")
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone du destinataire")
    recipient_email = models.EmailField(blank=True, verbose_name="Email du destinataire")

    # Notes et instructions
    delivery_instructions = models.TextField(blank=True, verbose_name="Instructions de livraison")
    notes = models.TextField(blank=True, verbose_name="Notes internes")

    # Traitement
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_deliveries', verbose_name="Traité par")

    class Meta:
        verbose_name = "Livraison"
        verbose_name_plural = "Livraisons"
        ordering = ['-created_date']

    def __str__(self):
        return f"Livraison #{self.id} - {self.purchase.book.title} pour {self.recipient_name}"

    @property
    def is_overdue(self):
        """Vérifie si la livraison est en retard"""
        if self.estimated_delivery_date and self.status not in ['delivered', 'cancelled', 'returned']:
            return timezone.now() > self.estimated_delivery_date
        return False

    @property
    def days_since_creation(self):
        """Nombre de jours depuis la création"""
        return (timezone.now() - self.created_date).days

    @property
    def estimated_days_remaining(self):
        """Nombre de jours restants avant la livraison estimée"""
        if self.estimated_delivery_date:
            remaining = (self.estimated_delivery_date - timezone.now()).days
            return max(0, remaining)
        return None

    def mark_as_shipped(self, tracking_number='', carrier='', processed_by=None):
        """Marquer comme expédié"""
        self.status = 'shipped'
        if tracking_number:
            self.tracking_number = tracking_number
        if carrier:
            self.carrier = carrier
        self.processed_by = processed_by
        self.save()

    def mark_as_delivered(self, processed_by=None, delivery_date=None):
        """Marquer comme livré"""
        self.status = 'delivered'
        self.actual_delivery_date = delivery_date or timezone.now()
        self.processed_by = processed_by

        # Mettre à jour le statut de l'achat
        self.purchase.status = 'delivered'
        self.purchase.save()

        self.save()

    def mark_as_failed(self, reason='', processed_by=None):
        """Marquer comme échec de livraison"""
        self.status = 'failed'
        if reason:
            self.notes = f"{self.notes}\nÉchec: {reason}".strip()
        self.processed_by = processed_by
        self.save()

    def cancel_delivery(self, reason='', processed_by=None):
        """Annuler la livraison"""
        self.status = 'cancelled'
        if reason:
            self.notes = f"{self.notes}\nAnnulation: {reason}".strip()
        self.processed_by = processed_by
        self.save()

    def get_status_color(self):
        """Retourne la couleur Bootstrap selon le statut"""
        colors = {
            'pending': 'secondary',
            'preparing': 'info',
            'shipped': 'primary',
            'in_transit': 'warning',
            'delivered': 'success',
            'failed': 'danger',
            'returned': 'dark',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')

    def get_status_icon(self):
        """Retourne l'icône FontAwesome selon le statut"""
        icons = {
            'pending': 'fas fa-clock',
            'preparing': 'fas fa-box',
            'shipped': 'fas fa-shipping-fast',
            'in_transit': 'fas fa-truck',
            'delivered': 'fas fa-check-circle',
            'failed': 'fas fa-exclamation-triangle',
            'returned': 'fas fa-undo',
            'cancelled': 'fas fa-times-circle',
        }
        return icons.get(self.status, 'fas fa-question')
