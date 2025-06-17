"""
Services de gestion des réservations pour la bibliothèque
"""

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .models import Reservation, Book, Loan, LibraryConfig


class ReservationService:
    """Service pour gérer les réservations"""

    @staticmethod
    def create_reservation(user, book):
        """Créer une nouvelle réservation"""
        # Vérifications préalables
        if book.is_available:
            return False, "Ce livre est actuellement disponible. Vous pouvez l'emprunter directement."
        
        if Reservation.objects.filter(user=user, book=book, status__in=['active', 'ready']).exists():
            return False, "Vous avez déjà une réservation active pour ce livre."
        
        if Loan.objects.filter(user=user, book=book, status__in=['borrowed', 'overdue']).exists():
            return False, "Vous avez déjà emprunté ce livre."
        
        # Vérifier les emprunts en retard
        overdue_loans = Loan.objects.filter(user=user, status='overdue').count()
        if overdue_loans > 0:
            return False, f"Vous avez {overdue_loans} livre(s) en retard. Veuillez les retourner avant de faire de nouvelles réservations."
        
        # Créer la réservation
        expiry_date = timezone.now() + timedelta(days=LibraryConfig.RESERVATION_DURATION)
        reservation = Reservation.objects.create(
            user=user,
            book=book,
            expiry_date=expiry_date
        )
        
        return True, reservation

    @staticmethod
    def cancel_reservation(reservation):
        """Annuler une réservation"""
        if reservation.cancel():
            # Traiter la prochaine réservation si le livre est disponible
            ReservationService.process_next_reservation(reservation.book)
            return True, "Réservation annulée avec succès."
        return False, "Cette réservation ne peut pas être annulée."

    @staticmethod
    def process_next_reservation(book):
        """Traiter la prochaine réservation pour un livre"""
        if book.available_copies > 0:
            next_reservation = Reservation.objects.filter(
                book=book,
                status='active'
            ).order_by('priority', 'reservation_date').first()
            
            if next_reservation:
                if next_reservation.mark_as_ready():
                    # Envoyer notification
                    NotificationService.send_book_ready_notification(next_reservation)
                    return next_reservation
        return None

    @staticmethod
    def fulfill_reservation(reservation, processed_by=None):
        """Satisfaire une réservation en créant un emprunt"""
        if reservation.status != 'ready':
            return False, "Cette réservation n'est pas prête à être satisfaite."
        
        if reservation.book.available_copies <= 0:
            return False, "Ce livre n'est plus disponible."
        
        # Créer l'emprunt
        loan_duration = LibraryConfig.get_loan_duration(reservation.user.category)
        due_date = timezone.now().date() + timedelta(days=loan_duration)
        
        loan = Loan.objects.create(
            user=reservation.user,
            book=reservation.book,
            due_date=due_date,
            status='borrowed'
        )
        
        # Marquer la réservation comme satisfaite
        reservation.mark_as_fulfilled()
        
        # Mettre à jour le stock
        reservation.book.available_copies -= 1
        reservation.book.save()
        
        return True, loan

    @staticmethod
    def cleanup_expired_reservations():
        """Nettoyer les réservations expirées"""
        count = Reservation.cleanup_expired_reservations()
        
        # Traiter les nouvelles réservations qui peuvent devenir prêtes
        ready_count = Reservation.process_ready_reservations()
        
        return count, ready_count

    @staticmethod
    def get_user_reservations(user, status=None):
        """Obtenir les réservations d'un utilisateur"""
        reservations = Reservation.objects.filter(user=user)
        if status:
            reservations = reservations.filter(status=status)
        return reservations.order_by('-reservation_date')

    @staticmethod
    def get_queue_info(book):
        """Obtenir les informations de la file d'attente pour un livre"""
        active_reservations = Reservation.objects.filter(
            book=book,
            status='active'
        ).order_by('priority', 'reservation_date')
        
        ready_reservations = Reservation.objects.filter(
            book=book,
            status='ready'
        ).order_by('ready_date')
        
        return {
            'active_count': active_reservations.count(),
            'ready_count': ready_reservations.count(),
            'total_count': active_reservations.count() + ready_reservations.count(),
            'next_in_queue': active_reservations.first(),
            'ready_reservations': ready_reservations
        }

    @staticmethod
    def handle_book_return(book):
        """Gérer le retour d'un livre et traiter les réservations"""
        # Traiter la prochaine réservation
        next_reservation = ReservationService.process_next_reservation(book)
        if next_reservation:
            return f"Livre attribué à {next_reservation.user.get_full_name()} (réservation)"
        return "Livre remis en stock"


class NotificationService:
    """Service pour les notifications de réservation"""

    @staticmethod
    def send_book_ready_notification(reservation):
        """Envoyer une notification quand un livre est prêt"""
        if reservation.notification_sent:
            return False
        
        subject = f"Livre disponible : {reservation.book.title}"
        message = f"""
Bonjour {reservation.user.get_full_name()},

Bonne nouvelle ! Le livre "{reservation.book.title}" que vous aviez réservé est maintenant disponible.

Vous avez {LibraryConfig.RESERVATION_HOLD_DURATION} jours pour venir le retirer à la bibliothèque.

Détails de votre réservation :
- Livre : {reservation.book.title}
- Auteur(s) : {reservation.book.authors_list}
- Date de réservation : {reservation.reservation_date.strftime('%d/%m/%Y')}
- Date limite de retrait : {reservation.get_expiry_date_display().strftime('%d/%m/%Y')}

Merci de vous présenter à la bibliothèque avec votre carte d'étudiant/employé.

Cordialement,
L'équipe de la Bibliothèque GPI
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [reservation.user.email],
                fail_silently=False,
            )
            reservation.notification_sent = True
            reservation.save()
            return True
        except Exception as e:
            print(f"Erreur envoi email: {e}")
            return False

    @staticmethod
    def send_reservation_expiry_warning(reservation, days_before=1):
        """Envoyer un rappel avant expiration"""
        subject = f"Rappel : Réservation expire bientôt - {reservation.book.title}"
        message = f"""
Bonjour {reservation.user.get_full_name()},

Votre réservation pour le livre "{reservation.book.title}" expire dans {days_before} jour(s).

N'oubliez pas de venir retirer votre livre avant le {reservation.get_expiry_date_display().strftime('%d/%m/%Y')}.

Après cette date, votre réservation sera annulée et le livre sera proposé au prochain utilisateur dans la file d'attente.

Cordialement,
L'équipe de la Bibliothèque GPI
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [reservation.user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erreur envoi email: {e}")
            return False


class ReservationAnalytics:
    """Service d'analyse des réservations"""

    @staticmethod
    def get_reservation_stats():
        """Obtenir les statistiques des réservations"""
        total = Reservation.objects.count()
        active = Reservation.objects.filter(status='active').count()
        ready = Reservation.objects.filter(status='ready').count()
        fulfilled = Reservation.objects.filter(status='fulfilled').count()
        expired = Reservation.objects.filter(status='expired').count()
        cancelled = Reservation.objects.filter(status='cancelled').count()
        
        return {
            'total': total,
            'active': active,
            'ready': ready,
            'fulfilled': fulfilled,
            'expired': expired,
            'cancelled': cancelled,
            'success_rate': (fulfilled / total * 100) if total > 0 else 0
        }

    @staticmethod
    def get_most_reserved_books(limit=10):
        """Obtenir les livres les plus réservés"""
        from django.db.models import Count
        
        return Book.objects.annotate(
            reservation_count=Count('reservations')
        ).filter(
            reservation_count__gt=0
        ).order_by('-reservation_count')[:limit]

    @staticmethod
    def get_average_wait_time():
        """Calculer le temps d'attente moyen"""
        fulfilled_reservations = Reservation.objects.filter(
            status='fulfilled',
            ready_date__isnull=False
        )
        
        if not fulfilled_reservations.exists():
            return 0
        
        total_wait_time = 0
        count = 0
        
        for reservation in fulfilled_reservations:
            wait_time = (reservation.ready_date - reservation.reservation_date).days
            total_wait_time += wait_time
            count += 1
        
        return total_wait_time / count if count > 0 else 0


class ReservationValidator:
    """Validateur pour les réservations"""

    @staticmethod
    def can_user_reserve(user, book):
        """Vérifier si un utilisateur peut réserver un livre"""
        # Livre disponible
        if book.is_available:
            return False, "Ce livre est disponible, vous pouvez l'emprunter directement."
        
        # Réservation existante
        if Reservation.objects.filter(user=user, book=book, status__in=['active', 'ready']).exists():
            return False, "Vous avez déjà une réservation pour ce livre."
        
        # Emprunt existant
        if Loan.objects.filter(user=user, book=book, status__in=['borrowed', 'overdue']).exists():
            return False, "Vous avez déjà emprunté ce livre."
        
        # Emprunts en retard
        overdue_count = Loan.objects.filter(user=user, status='overdue').count()
        if overdue_count > 0:
            return False, f"Vous avez {overdue_count} livre(s) en retard."
        
        return True, "Réservation autorisée."

    @staticmethod
    def validate_reservation_limits(user):
        """Valider les limites de réservation"""
        active_reservations = Reservation.objects.filter(
            user=user,
            status__in=['active', 'ready']
        ).count()
        
        max_reservations = 5  # Limite configurable
        
        if active_reservations >= max_reservations:
            return False, f"Vous avez atteint la limite de {max_reservations} réservations actives."
        
        return True, "Limite respectée."
