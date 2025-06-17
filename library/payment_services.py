"""
Services de gestion des paiements pour la bibliothèque
"""

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from .models import Payment, BookPurchase, Loan, LibraryConfig


class PaymentService:
    """Service pour gérer les paiements"""

    @staticmethod
    def create_purchase_payment(purchase, payment_method='cash', processed_by=None):
        """Créer un paiement pour un achat"""
        payment = Payment.objects.create(
            user=purchase.user,
            payment_type='purchase',
            amount=purchase.total_price,
            payment_method=payment_method,
            purchase=purchase,
            processed_by=processed_by,
            status='pending'
        )
        return payment

    @staticmethod
    def create_loan_payment(loan, payment_method='cash', processed_by=None):
        """Créer un paiement pour un emprunt (si des frais s'appliquent)"""
        loan_fee = LibraryConfig.get_loan_fee(loan.user.category)
        
        if loan_fee > 0:
            payment = Payment.objects.create(
                user=loan.user,
                payment_type='loan_fee',
                amount=Decimal(str(loan_fee)),
                payment_method=payment_method,
                loan=loan,
                processed_by=processed_by,
                status='pending'
            )
            return payment
        else:
            # Créer un paiement gratuit pour traçabilité
            payment = Payment.objects.create(
                user=loan.user,
                payment_type='loan_fee',
                amount=Decimal('0.00'),
                payment_method='free',
                loan=loan,
                processed_by=processed_by,
                status='completed'
            )
            return payment

    @staticmethod
    def create_renewal_payment(loan, payment_method='cash', processed_by=None):
        """Créer un paiement pour un renouvellement"""
        renewal_fee = LibraryConfig.get_renewal_fee(loan.user.category)
        
        payment = Payment.objects.create(
            user=loan.user,
            payment_type='renewal_fee',
            amount=Decimal(str(renewal_fee)),
            payment_method=payment_method if renewal_fee > 0 else 'free',
            loan=loan,
            processed_by=processed_by,
            status='completed' if renewal_fee == 0 else 'pending'
        )
        return payment

    @staticmethod
    def create_late_fee_payment(loan, days_late, payment_method='cash', processed_by=None):
        """Créer un paiement pour des frais de retard"""
        daily_fee = LibraryConfig.get_late_fee_per_day(loan.user.category)
        total_fee = Decimal(str(daily_fee)) * days_late
        
        if total_fee > 0:
            payment = Payment.objects.create(
                user=loan.user,
                payment_type='late_fee',
                amount=total_fee,
                payment_method=payment_method,
                loan=loan,
                processed_by=processed_by,
                status='pending',
                notes=f"Frais de retard: {days_late} jour(s) × {daily_fee}€"
            )
            return payment
        return None

    @staticmethod
    def create_deposit_payment(user, loan=None, payment_method='cash', processed_by=None):
        """Créer un paiement pour une caution"""
        deposit_amount = LibraryConfig.get_deposit_amount(user.category)
        
        if deposit_amount > 0:
            payment = Payment.objects.create(
                user=user,
                payment_type='deposit',
                amount=Decimal(str(deposit_amount)),
                payment_method=payment_method,
                loan=loan,
                processed_by=processed_by,
                status='pending'
            )
            return payment
        return None

    @staticmethod
    def process_payment(payment, transaction_id='', processed_by=None):
        """Traiter un paiement"""
        payment.mark_as_completed(processed_by=processed_by, transaction_id=transaction_id)
        
        # Mettre à jour le statut de l'objet lié
        if payment.purchase:
            payment.purchase.status = 'paid'
            payment.purchase.save()
        
        return payment

    @staticmethod
    def calculate_outstanding_fees(user):
        """Calculer les frais impayés d'un utilisateur"""
        pending_payments = Payment.objects.filter(
            user=user,
            status='pending'
        )
        
        total = sum(payment.amount for payment in pending_payments)
        return total, pending_payments

    @staticmethod
    def get_user_payment_history(user, limit=None):
        """Obtenir l'historique des paiements d'un utilisateur"""
        payments = Payment.objects.filter(user=user).order_by('-payment_date')
        if limit:
            payments = payments[:limit]
        return payments

    @staticmethod
    def can_user_borrow(user):
        """Vérifier si un utilisateur peut emprunter (pas de frais impayés)"""
        outstanding_amount, _ = PaymentService.calculate_outstanding_fees(user)
        return outstanding_amount == 0

    @staticmethod
    def get_payment_summary_for_loan(loan):
        """Obtenir un résumé des paiements pour un emprunt"""
        payments = Payment.objects.filter(loan=loan)
        
        summary = {
            'loan_fee': Decimal('0.00'),
            'renewal_fees': Decimal('0.00'),
            'late_fees': Decimal('0.00'),
            'deposit': Decimal('0.00'),
            'total_paid': Decimal('0.00'),
            'total_pending': Decimal('0.00'),
        }
        
        for payment in payments:
            if payment.status == 'completed':
                summary['total_paid'] += payment.amount
            elif payment.status == 'pending':
                summary['total_pending'] += payment.amount
            
            if payment.payment_type == 'loan_fee':
                summary['loan_fee'] += payment.amount
            elif payment.payment_type == 'renewal_fee':
                summary['renewal_fees'] += payment.amount
            elif payment.payment_type == 'late_fee':
                summary['late_fees'] += payment.amount
            elif payment.payment_type == 'deposit':
                summary['deposit'] += payment.amount
        
        return summary

    @staticmethod
    def get_payment_summary_for_purchase(purchase):
        """Obtenir un résumé des paiements pour un achat"""
        payments = Payment.objects.filter(purchase=purchase)
        
        summary = {
            'total_paid': Decimal('0.00'),
            'total_pending': Decimal('0.00'),
            'is_fully_paid': False,
        }
        
        for payment in payments:
            if payment.status == 'completed':
                summary['total_paid'] += payment.amount
            elif payment.status == 'pending':
                summary['total_pending'] += payment.amount
        
        summary['is_fully_paid'] = summary['total_paid'] >= purchase.total_price
        
        return summary


class PaymentCalculator:
    """Calculateur pour les différents types de frais"""

    @staticmethod
    def calculate_loan_fee(user_category):
        """Calculer les frais d'emprunt"""
        return Decimal(str(LibraryConfig.get_loan_fee(user_category)))

    @staticmethod
    def calculate_renewal_fee(user_category):
        """Calculer les frais de renouvellement"""
        return Decimal(str(LibraryConfig.get_renewal_fee(user_category)))

    @staticmethod
    def calculate_late_fees(loan):
        """Calculer les frais de retard pour un emprunt"""
        if loan.status != 'overdue':
            return Decimal('0.00')
        
        days_late = (timezone.now().date() - loan.due_date).days
        daily_fee = LibraryConfig.get_late_fee_per_day(loan.user.category)
        
        return Decimal(str(daily_fee)) * days_late

    @staticmethod
    def calculate_deposit_amount(user_category):
        """Calculer le montant de la caution"""
        return Decimal(str(LibraryConfig.get_deposit_amount(user_category)))

    @staticmethod
    def calculate_purchase_total(book, user_category, quantity=1):
        """Calculer le total d'un achat avec remise"""
        unit_price = book.purchase_price
        discount_percentage = LibraryConfig.get_purchase_discount(user_category)
        
        discount_amount = unit_price * Decimal(str(discount_percentage)) / Decimal('100')
        discounted_price = unit_price - discount_amount
        total_price = discounted_price * quantity
        
        return {
            'unit_price': unit_price,
            'discount_percentage': discount_percentage,
            'discount_amount': discount_amount,
            'discounted_price': discounted_price,
            'total_price': total_price,
            'quantity': quantity
        }


class PaymentValidator:
    """Validateur pour les paiements"""

    @staticmethod
    def validate_payment_amount(payment, expected_amount):
        """Valider le montant d'un paiement"""
        return payment.amount == expected_amount

    @staticmethod
    def validate_user_can_pay(user, amount):
        """Valider qu'un utilisateur peut effectuer un paiement"""
        # Ici on pourrait ajouter des vérifications comme :
        # - Limite de crédit
        # - Compte bloqué
        # - etc.
        return True

    @staticmethod
    def validate_payment_method(payment_method, amount):
        """Valider la méthode de paiement selon le montant"""
        if amount == 0 and payment_method != 'free':
            return False
        if amount > 0 and payment_method == 'free':
            return False
        return True
