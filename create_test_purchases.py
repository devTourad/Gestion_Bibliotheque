#!/usr/bin/env python
"""
Script pour créer des achats de test
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from library.models import Book, BookPurchase, Payment

def create_test_purchases():
    """Créer des achats de test avec différents statuts"""
    print("🔄 Création d'achats de test...")
    
    User = get_user_model()
    
    # Obtenir un utilisateur
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return
    
    # Obtenir des livres
    books = Book.objects.filter(is_for_sale=True)[:5]
    if not books:
        print("❌ Aucun livre en vente trouvé")
        return
    
    print(f"👤 Utilisateur: {user.username}")
    print(f"📚 Livres disponibles: {len(books)}")
    
    # Créer des achats avec différents statuts
    purchases_data = [
        {
            'book': books[0],
            'status': 'pending',
            'days_ago': 0,
            'description': 'Commande récente en attente'
        },
        {
            'book': books[1] if len(books) > 1 else books[0],
            'status': 'confirmed',
            'days_ago': 1,
            'description': 'Commande confirmée hier'
        },
        {
            'book': books[2] if len(books) > 2 else books[0],
            'status': 'paid',
            'days_ago': 3,
            'description': 'Commande payée il y a 3 jours'
        },
        {
            'book': books[3] if len(books) > 3 else books[0],
            'status': 'delivered',
            'days_ago': 7,
            'description': 'Commande livrée il y a une semaine'
        },
        {
            'book': books[4] if len(books) > 4 else books[0],
            'status': 'cancelled',
            'days_ago': 2,
            'description': 'Commande annulée il y a 2 jours'
        }
    ]
    
    created_purchases = []
    
    for purchase_data in purchases_data:
        book = purchase_data['book']
        status = purchase_data['status']
        days_ago = purchase_data['days_ago']
        description = purchase_data['description']
        
        # Calculer la date d'achat
        purchase_date = date.today() - timedelta(days=days_ago)
        
        # Vérifier si un achat similaire existe déjà
        existing_purchase = BookPurchase.objects.filter(
            user=user,
            book=book,
            status=status
        ).first()
        
        if existing_purchase:
            print(f"⚠️  Achat similaire déjà existant: {book.title} ({status})")
            created_purchases.append(existing_purchase)
            continue
        
        # Créer l'achat
        purchase = BookPurchase.objects.create(
            user=user,
            book=book,
            quantity=1,
            unit_price=book.purchase_price or Decimal('15.00'),
            total_price=book.purchase_price or Decimal('15.00'),
            status=status,
            purchase_date=purchase_date
        )
        
        # Créer un paiement associé si nécessaire
        if status in ['paid', 'delivered']:
            payment = Payment.objects.create(
                user=user,
                amount=purchase.total_price,
                payment_type='purchase',
                purchase=purchase,  # Relation directe vers l'achat
                status='completed',
                payment_method='cash'
            )
            print(f"✅ Paiement créé pour l'achat #{purchase.id}")
        
        created_purchases.append(purchase)
        print(f"✅ Achat créé: #{purchase.id} - {book.title} ({status}) - {description}")
    
    print(f"\n🎉 {len(created_purchases)} achats disponibles dans la base de données")
    
    # Afficher un résumé
    print("\n📊 Résumé des achats:")
    for status_code, status_label in BookPurchase.PURCHASE_STATUS:
        count = BookPurchase.objects.filter(user=user, status=status_code).count()
        if count > 0:
            print(f"  - {status_label}: {count}")
    
    # Calculer les revenus
    paid_purchases = BookPurchase.objects.filter(user=user, status__in=['paid', 'delivered'])
    if paid_purchases:
        total = sum(p.total_price for p in paid_purchases)
        print(f"\n💰 Revenus générés: {total}€")
    
    return created_purchases

def main():
    """Fonction principale"""
    print("🚀 Script de création d'achats de test")
    print("=" * 50)
    
    purchases = create_test_purchases()
    
    print("\n" + "=" * 50)
    print("✅ Script terminé avec succès !")
    print(f"🔗 Accédez à la gestion des achats: http://127.0.0.1:8000/admin-purchases/")

if __name__ == '__main__':
    main()
