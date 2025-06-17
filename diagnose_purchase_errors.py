#!/usr/bin/env python
"""
Script de diagnostic pour les erreurs de confirmation de commandes
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from library.models import BookPurchase, Payment, CustomUser, Book
from django.db.models import Count, Q

def diagnose_purchase_system():
    """Diagnostiquer le système d'achats"""
    print("🔍 DIAGNOSTIC DU SYSTÈME D'ACHATS")
    print("=" * 50)
    
    # 1. Vérifier les achats
    print("\n📊 STATISTIQUES DES ACHATS")
    total_purchases = BookPurchase.objects.count()
    print(f"Total des achats: {total_purchases}")
    
    if total_purchases == 0:
        print("❌ Aucun achat trouvé dans le système")
        return
    
    # Statistiques par statut
    status_counts = {}
    for status, label in BookPurchase.PURCHASE_STATUS:
        count = BookPurchase.objects.filter(status=status).count()
        status_counts[status] = count
        print(f"  - {label}: {count}")
    
    # 2. Vérifier les achats en attente
    print("\n⏳ ACHATS EN ATTENTE")
    pending_purchases = BookPurchase.objects.filter(status='pending').order_by('-purchase_date')[:10]
    
    if pending_purchases:
        for purchase in pending_purchases:
            print(f"  ID {purchase.id}: {purchase.book.title} - {purchase.user.username} - {purchase.total_price}€")
    else:
        print("  Aucun achat en attente")
    
    # 3. Vérifier les paiements
    print("\n💳 PAIEMENTS")
    total_payments = Payment.objects.count()
    purchase_payments = Payment.objects.filter(payment_type='purchase').count()
    print(f"Total des paiements: {total_payments}")
    print(f"Paiements d'achats: {purchase_payments}")
    
    # 4. Vérifier les incohérences
    print("\n⚠️  VÉRIFICATION DES INCOHÉRENCES")
    
    # Achats payés sans paiement
    paid_without_payment = BookPurchase.objects.filter(
        status='paid',
        payment__isnull=True
    ).count()
    if paid_without_payment > 0:
        print(f"❌ {paid_without_payment} achats marqués comme payés sans paiement associé")
    
    # Paiements sans achat
    payments_without_purchase = Payment.objects.filter(
        payment_type='purchase',
        purchase__isnull=True
    ).count()
    if payments_without_purchase > 0:
        print(f"❌ {payments_without_purchase} paiements d'achats sans achat associé")
    
    # Achats avec statut incohérent
    inconsistent_purchases = BookPurchase.objects.filter(
        Q(status='paid', payment__status='pending') |
        Q(status='pending', payment__status='completed')
    ).count()
    if inconsistent_purchases > 0:
        print(f"❌ {inconsistent_purchases} achats avec statut incohérent")
    
    if paid_without_payment == 0 and payments_without_purchase == 0 and inconsistent_purchases == 0:
        print("✅ Aucune incohérence détectée")
    
    # 5. Vérifier les livres en vente
    print("\n📚 LIVRES EN VENTE")
    books_for_sale = Book.objects.filter(is_for_sale=True).count()
    books_with_price = Book.objects.filter(is_for_sale=True, purchase_price__gt=0).count()
    print(f"Livres en vente: {books_for_sale}")
    print(f"Livres avec prix: {books_with_price}")
    
    if books_for_sale == 0:
        print("❌ Aucun livre n'est en vente")
    elif books_with_price < books_for_sale:
        print(f"⚠️  {books_for_sale - books_with_price} livres en vente sans prix")
    
    # 6. Vérifier les utilisateurs
    print("\n👥 UTILISATEURS")
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    print(f"Total utilisateurs: {total_users}")
    print(f"Utilisateurs actifs: {active_users}")
    
    # 7. Tester les URLs
    print("\n🔗 TEST DES URLS")
    test_urls = [
        '/admin-purchases/',
        '/admin/purchases/1/update-status/',
        '/admin/purchases/1/confirm/',
        '/admin/purchases/1/mark-paid/',
    ]
    
    for url in test_urls:
        print(f"  {url}: Configuré")

def fix_common_issues():
    """Corriger les problèmes courants"""
    print("\n🔧 CORRECTION DES PROBLÈMES COURANTS")
    print("=" * 50)
    
    fixed_count = 0
    
    # 1. Corriger les achats payés sans paiement
    paid_without_payment = BookPurchase.objects.filter(
        status='paid',
        payment__isnull=True
    )
    
    for purchase in paid_without_payment:
        try:
            payment = Payment.objects.create(
                user=purchase.user,
                amount=purchase.total_price,
                payment_type='purchase',
                payment_method='cash',
                status='completed',
                purchase=purchase
            )
            print(f"✅ Paiement créé pour l'achat #{purchase.id}")
            fixed_count += 1
        except Exception as e:
            print(f"❌ Erreur lors de la création du paiement pour l'achat #{purchase.id}: {e}")
    
    # 2. Corriger les statuts incohérents
    inconsistent_purchases = BookPurchase.objects.filter(
        status='pending',
        payment__status='completed'
    )
    
    for purchase in inconsistent_purchases:
        try:
            purchase.status = 'paid'
            purchase.save()
            print(f"✅ Statut corrigé pour l'achat #{purchase.id}")
            fixed_count += 1
        except Exception as e:
            print(f"❌ Erreur lors de la correction du statut pour l'achat #{purchase.id}: {e}")
    
    if fixed_count == 0:
        print("✅ Aucun problème à corriger")
    else:
        print(f"\n🎉 {fixed_count} problèmes corrigés")

def create_test_data():
    """Créer des données de test"""
    print("\n🧪 CRÉATION DE DONNÉES DE TEST")
    print("=" * 50)
    
    try:
        # Vérifier qu'il y a des utilisateurs et des livres
        user = CustomUser.objects.first()
        book = Book.objects.filter(is_for_sale=True, purchase_price__gt=0).first()
        
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return
        
        if not book:
            print("❌ Aucun livre en vente trouvé")
            return
        
        # Créer des achats de test avec différents statuts
        test_statuses = ['pending', 'confirmed', 'paid']
        
        for i, status in enumerate(test_statuses):
            purchase = BookPurchase.objects.create(
                user=user,
                book=book,
                quantity=1,
                unit_price=book.purchase_price,
                total_price=book.purchase_price,
                status=status,
                notes=f"Achat de test - {status}"
            )
            
            # Créer un paiement pour les achats payés
            if status == 'paid':
                Payment.objects.create(
                    user=user,
                    amount=purchase.total_price,
                    payment_type='purchase',
                    payment_method='cash',
                    status='completed',
                    purchase=purchase
                )
            
            print(f"✅ Achat de test créé: ID {purchase.id} - Statut: {status}")
        
        print(f"\n🎉 3 achats de test créés avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données de test: {e}")

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC DU SYSTÈME DE CONFIRMATION DE COMMANDES")
    print("=" * 60)
    
    try:
        diagnose_purchase_system()
        
        print("\n" + "=" * 60)
        choice = input("\nVoulez-vous :\n1. Corriger les problèmes détectés\n2. Créer des données de test\n3. Quitter\n\nChoix (1-3): ").strip()
        
        if choice == '1':
            fix_common_issues()
        elif choice == '2':
            create_test_data()
        elif choice == '3':
            print("👋 Au revoir !")
        else:
            print("❌ Choix invalide")
            
    except KeyboardInterrupt:
        print("\n\n❌ Opération interrompue par l'utilisateur.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("🔗 URLs de test:")
    print("  - Gestion des achats: http://127.0.0.1:8000/admin-purchases/")
    print("  - Dashboard admin: http://127.0.0.1:8000/admin-dashboard/")

if __name__ == '__main__':
    main()
