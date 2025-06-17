"""
Commande Django pour traiter les réservations
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import Reservation, Book
from library.reservation_services import ReservationService, NotificationService


class Command(BaseCommand):
    help = 'Traite les réservations : nettoie les expirées et active les nouvelles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )
        parser.add_argument(
            '--send-notifications',
            action='store_true',
            help='Envoie les notifications par email',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_notifications = options['send_notifications']
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS(f'=== Traitement des réservations - {timezone.now()} ===')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODE DRY-RUN : Aucune modification ne sera effectuée')
            )

        # 1. Nettoyer les réservations expirées
        self.stdout.write('\n1. Nettoyage des réservations expirées...')
        
        if not dry_run:
            expired_count, ready_count = ReservationService.cleanup_expired_reservations()
        else:
            # Simulation pour dry-run
            now = timezone.now()
            expired_active = Reservation.objects.filter(
                status='active',
                expiry_date__lt=now
            ).count()
            
            from datetime import timedelta
            from library.models import LibraryConfig
            expired_ready = Reservation.objects.filter(
                status='ready',
                ready_date__lt=now - timedelta(days=LibraryConfig.RESERVATION_HOLD_DURATION)
            ).count()
            
            expired_count = expired_active + expired_ready
            ready_count = 0

        self.stdout.write(
            self.style.SUCCESS(f'   ✓ {expired_count} réservation(s) expirée(s) traitée(s)')
        )

        # 2. Traiter les nouvelles réservations prêtes
        self.stdout.write('\n2. Traitement des nouvelles réservations prêtes...')
        
        if not dry_run:
            new_ready_count = Reservation.process_ready_reservations()
        else:
            # Simulation pour dry-run
            available_books = Book.objects.filter(available_copies__gt=0)
            new_ready_count = 0
            for book in available_books:
                next_reservation = Reservation.objects.filter(
                    book=book,
                    status='active'
                ).order_by('priority', 'reservation_date').first()
                if next_reservation:
                    new_ready_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'   ✓ {new_ready_count} nouvelle(s) réservation(s) prête(s)')
        )

        # 3. Envoyer les notifications
        if send_notifications and not dry_run:
            self.stdout.write('\n3. Envoi des notifications...')
            
            ready_reservations = Reservation.objects.filter(
                status='ready',
                notification_sent=False
            )
            
            notification_count = 0
            for reservation in ready_reservations:
                if NotificationService.send_book_ready_notification(reservation):
                    notification_count += 1
                    if verbose:
                        self.stdout.write(
                            f'   → Notification envoyée à {reservation.user.email} pour "{reservation.book.title}"'
                        )
            
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ {notification_count} notification(s) envoyée(s)')
            )

        # 4. Afficher les statistiques
        self.stdout.write('\n4. Statistiques actuelles...')
        
        stats = {
            'active': Reservation.objects.filter(status='active').count(),
            'ready': Reservation.objects.filter(status='ready').count(),
            'fulfilled': Reservation.objects.filter(status='fulfilled').count(),
            'expired': Reservation.objects.filter(status='expired').count(),
            'cancelled': Reservation.objects.filter(status='cancelled').count(),
        }
        
        self.stdout.write(f'   • Réservations actives: {stats["active"]}')
        self.stdout.write(f'   • Réservations prêtes: {stats["ready"]}')
        self.stdout.write(f'   • Réservations satisfaites: {stats["fulfilled"]}')
        self.stdout.write(f'   • Réservations expirées: {stats["expired"]}')
        self.stdout.write(f'   • Réservations annulées: {stats["cancelled"]}')

        # 5. Afficher les détails si verbose
        if verbose:
            self.stdout.write('\n5. Détails des réservations prêtes...')
            
            ready_reservations = Reservation.objects.filter(status='ready')
            if ready_reservations.exists():
                for reservation in ready_reservations:
                    expiry = reservation.get_expiry_date_display()
                    self.stdout.write(
                        f'   • {reservation.user.get_full_name()} - "{reservation.book.title}" '
                        f'(expire le {expiry.strftime("%d/%m/%Y")})'
                    )
            else:
                self.stdout.write('   Aucune réservation prête')

            self.stdout.write('\n6. Livres avec file d\'attente...')
            
            books_with_queue = Book.objects.filter(
                reservations__status='active'
            ).distinct()
            
            if books_with_queue.exists():
                for book in books_with_queue:
                    queue_info = ReservationService.get_queue_info(book)
                    self.stdout.write(
                        f'   • "{book.title}" - {queue_info["active_count"]} en attente, '
                        f'{queue_info["ready_count"]} prête(s), {book.available_copies} disponible(s)'
                    )
            else:
                self.stdout.write('   Aucune file d\'attente')

        # Résumé final
        self.stdout.write(
            self.style.SUCCESS(f'\n=== Traitement terminé ===')
        )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Total: {expired_count} expirées, {new_ready_count} nouvelles prêtes'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Mode dry-run : aucune modification effectuée')
            )

        # Recommandations
        if stats['ready'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  {stats["ready"]} réservation(s) prête(s) en attente de retrait'
                )
            )
        
        if stats['active'] > 10:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  {stats["active"]} réservation(s) active(s) - vérifiez les stocks'
                )
            )
