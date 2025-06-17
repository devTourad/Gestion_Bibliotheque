#!/usr/bin/env python
"""
Script pour créer des livraisons de test
"""

import os
import sys
import django
from datetime import date, timedelta, datetime
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from library.models import Book, BookPurchase, Delivery

def create_test_deliveries():
    """Créer des livraisons de test avec différents statuts"""
    print("🚚 Création de livraisons de test...")
    
    User = get_user_model()
    
    # Obtenir des achats payés sans livraison
    paid_purchases = BookPurchase.objects.filter(
        status='paid'
    ).exclude(
        id__in=Delivery.objects.values_list('purchase_id', flat=True)
    )[:5]
    
    if not paid_purchases:
        print("❌ Aucun achat payé sans livraison trouvé")
        # Créer quelques achats payés pour les tests
        user = User.objects.filter(is_active=True).first()
        books = Book.objects.filter(is_for_sale=True)[:3]
        
        if user and books:
            print("📦 Création d'achats payés pour les tests...")
            for i, book in enumerate(books):
                purchase = BookPurchase.objects.create(
                    user=user,
                    book=book,
                    quantity=1,
                    unit_price=book.purchase_price or Decimal('15.00'),
                    total_price=book.purchase_price or Decimal('15.00'),
                    status='paid',
                    delivery_address=f"123 Rue de Test, Apt {i+1}\n75001 Paris\nFrance"
                )
                paid_purchases = [purchase] + list(paid_purchases)
                print(f"✅ Achat créé: #{purchase.id}")
    
    print(f"📋 Achats payés disponibles: {len(paid_purchases)}")
    
    # Créer des livraisons avec différents statuts
    deliveries_data = [
        {
            'status': 'pending',
            'method': 'home_delivery',
            'days_ago': 0,
            'estimated_days': 3,
            'description': 'Livraison en attente'
        },
        {
            'status': 'preparing',
            'method': 'home_delivery',
            'days_ago': 1,
            'estimated_days': 2,
            'description': 'Livraison en préparation'
        },
        {
            'status': 'shipped',
            'method': 'post_office',
            'days_ago': 2,
            'estimated_days': 1,
            'description': 'Livraison expédiée',
            'tracking': 'TR123456789FR',
            'carrier': 'La Poste'
        },
        {
            'status': 'in_transit',
            'method': 'express',
            'days_ago': 1,
            'estimated_days': 0,
            'description': 'Livraison en transit',
            'tracking': 'EX987654321FR',
            'carrier': 'Chronopost'
        },
        {
            'status': 'delivered',
            'method': 'pickup',
            'days_ago': 3,
            'estimated_days': -1,
            'description': 'Livraison terminée',
            'delivered_days_ago': 1
        }
    ]
    
    created_deliveries = []
    
    for i, delivery_data in enumerate(deliveries_data):
        if i >= len(paid_purchases):
            break
            
        purchase = paid_purchases[i]
        
        # Vérifier si une livraison existe déjà
        if hasattr(purchase, 'delivery'):
            print(f"⚠️  Livraison déjà existante pour l'achat #{purchase.id}")
            created_deliveries.append(purchase.delivery)
            continue
        
        # Calculer les dates
        created_date = timezone.now() - timedelta(days=delivery_data['days_ago'])
        estimated_date = timezone.now() + timedelta(days=delivery_data['estimated_days'])
        
        # Créer la livraison
        delivery = Delivery.objects.create(
            purchase=purchase,
            delivery_method=delivery_data['method'],
            status=delivery_data['status'],
            delivery_address=purchase.delivery_address or "Adresse de test\n75001 Paris",
            pickup_location="Bibliothèque centrale - Bureau d'accueil" if delivery_data['method'] == 'pickup' else "",
            estimated_delivery_date=estimated_date,
            recipient_name=purchase.user.get_full_name() or purchase.user.username,
            recipient_email=purchase.user.email,
            recipient_phone="+33 1 23 45 67 89",
            delivery_instructions="Sonner à l'interphone" if delivery_data['method'] != 'pickup' else "",
            delivery_cost=Decimal('5.00') if delivery_data['method'] == 'express' else Decimal('0.00'),
            tracking_number=delivery_data.get('tracking', ''),
            carrier=delivery_data.get('carrier', ''),
            created_date=created_date
        )
        
        # Mettre à jour la date de création manuellement
        Delivery.objects.filter(id=delivery.id).update(created_date=created_date)
        
        # Si livré, définir la date de livraison
        if delivery_data['status'] == 'delivered':
            delivered_date = timezone.now() - timedelta(days=delivery_data.get('delivered_days_ago', 0))
            delivery.actual_delivery_date = delivered_date
            delivery.save()
            
            # Mettre à jour le statut de l'achat
            purchase.status = 'delivered'
            purchase.save()
        
        created_deliveries.append(delivery)
        print(f"✅ Livraison créée: #{delivery.id} - {delivery.get_status_display()} - {delivery_data['description']}")
    
    print(f"\n🎉 {len(created_deliveries)} livraisons disponibles dans la base de données")
    
    # Afficher un résumé
    print("\n📊 Résumé des livraisons:")
    for status_code, status_label in Delivery.DELIVERY_STATUS:
        count = Delivery.objects.filter(status=status_code).count()
        if count > 0:
            print(f"  - {status_label}: {count}")
    
    # Livraisons en retard
    overdue_count = Delivery.objects.filter(
        estimated_delivery_date__lt=timezone.now(),
        status__in=['pending', 'preparing', 'shipped', 'in_transit']
    ).count()
    
    if overdue_count > 0:
        print(f"\n⚠️  {overdue_count} livraison(s) en retard")
    
    return created_deliveries

def main():
    """Fonction principale"""
    print("🚀 Script de création de livraisons de test")
    print("=" * 50)
    
    deliveries = create_test_deliveries()
    
    print("\n" + "=" * 50)
    print("✅ Script terminé avec succès !")
    print(f"🔗 Accédez à la gestion des livraisons: http://127.0.0.1:8000/admin/deliveries/")

if __name__ == '__main__':
    main()
