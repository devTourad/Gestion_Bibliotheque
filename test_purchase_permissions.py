#!/usr/bin/env python
"""
Script de test pour vérifier les permissions et les erreurs 403
"""

import os
import sys
import django
import requests
from django.test import Client

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from library.models import BookPurchase, Book

def test_permissions():
    """Tester les permissions utilisateur"""
    print("🔐 TEST DES PERMISSIONS")
    print("=" * 50)
    
    User = get_user_model()
    
    # Vérifier les utilisateurs
    users = User.objects.all()
    print(f"Total utilisateurs: {users.count()}")
    
    for user in users:
        print(f"\n👤 Utilisateur: {user.username}")
        print(f"   - is_authenticated: {user.is_authenticated}")
        print(f"   - is_staff: {user.is_staff}")
        print(f"   - is_superuser: {user.is_superuser}")
        print(f"   - is_super_admin: {getattr(user, 'is_super_admin', False)}")
        print(f"   - is_active: {user.is_active}")

def test_csrf_and_requests():
    """Tester les requêtes avec CSRF"""
    print("\n🔒 TEST DES REQUÊTES CSRF")
    print("=" * 50)
    
    client = Client()
    
    # Se connecter avec le premier utilisateur staff
    User = get_user_model()
    staff_user = User.objects.filter(is_staff=True).first()
    
    if not staff_user:
        print("❌ Aucun utilisateur staff trouvé")
        return
    
    print(f"🔑 Connexion avec: {staff_user.username}")
    
    # Forcer la connexion
    client.force_login(staff_user)
    
    # Tester l'accès à la page de gestion des achats
    print("\n📄 Test de la page de gestion des achats...")
    response = client.get('/admin-purchases/')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Accès autorisé")
        
        # Vérifier la présence du token CSRF
        content = response.content.decode()
        if 'csrfmiddlewaretoken' in content:
            print("   ✅ Token CSRF présent dans la page")
        else:
            print("   ⚠️  Token CSRF non trouvé dans la page")
    else:
        print(f"   ❌ Accès refusé: {response.status_code}")
    
    # Tester une requête AJAX de mise à jour de statut
    purchase = BookPurchase.objects.first()
    if purchase:
        print(f"\n🔄 Test de mise à jour de statut pour l'achat #{purchase.id}...")
        
        # Obtenir le token CSRF
        csrf_token = client.cookies.get('csrftoken')
        if csrf_token:
            csrf_token = csrf_token.value
        
        print(f"   Token CSRF: {csrf_token[:10]}..." if csrf_token else "   ❌ Pas de token CSRF")
        
        # Tester la requête POST
        response = client.post(
            f'/admin/purchases/{purchase.id}/update-status/',
            data={'status': 'confirmed'},
            HTTP_X_CSRFTOKEN=csrf_token,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Mise à jour réussie")
        elif response.status_code == 403:
            print("   ❌ Erreur 403 - Problème de CSRF ou permissions")
        else:
            print(f"   ⚠️  Autre erreur: {response.status_code}")
    else:
        print("\n❌ Aucun achat trouvé pour tester")

def test_direct_view_access():
    """Tester l'accès direct aux vues"""
    print("\n🎯 TEST D'ACCÈS DIRECT AUX VUES")
    print("=" * 50)
    
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    from library.views import admin_update_purchase_status, admin_purchases
    
    factory = RequestFactory()
    User = get_user_model()
    
    # Utilisateur staff
    staff_user = User.objects.filter(is_staff=True).first()
    
    if not staff_user:
        print("❌ Aucun utilisateur staff trouvé")
        return
    
    # Test avec utilisateur staff
    print(f"👤 Test avec utilisateur staff: {staff_user.username}")
    
    # Test de la vue admin_purchases
    request = factory.get('/admin-purchases/')
    request.user = staff_user
    
    try:
        response = admin_purchases(request)
        print(f"   admin_purchases: Status {response.status_code} ✅")
    except Exception as e:
        print(f"   admin_purchases: Erreur {e} ❌")
    
    # Test de la vue admin_update_purchase_status
    purchase = BookPurchase.objects.first()
    if purchase:
        request = factory.post(f'/admin/purchases/{purchase.id}/update-status/')
        request.user = staff_user
        request._body = b'{"status": "confirmed"}'
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.META['CONTENT_TYPE'] = 'application/json'
        
        try:
            response = admin_update_purchase_status(request, purchase.id)
            print(f"   admin_update_purchase_status: Status {response.status_code} ✅")
        except Exception as e:
            print(f"   admin_update_purchase_status: Erreur {e} ❌")

def create_test_purchase():
    """Créer un achat de test"""
    print("\n🛒 CRÉATION D'UN ACHAT DE TEST")
    print("=" * 50)
    
    User = get_user_model()
    user = User.objects.first()
    book = Book.objects.filter(is_for_sale=True).first()
    
    if not user or not book:
        print("❌ Utilisateur ou livre manquant")
        return None
    
    purchase = BookPurchase.objects.create(
        user=user,
        book=book,
        quantity=1,
        unit_price=book.purchase_price or 10.00,
        total_price=book.purchase_price or 10.00,
        status='pending',
        notes='Achat de test pour débogage'
    )
    
    print(f"✅ Achat créé: ID {purchase.id}")
    print(f"   Livre: {book.title}")
    print(f"   Utilisateur: {user.username}")
    print(f"   Prix: {purchase.total_price}€")
    print(f"   Statut: {purchase.status}")
    
    return purchase

def main():
    """Fonction principale"""
    print("🔍 TEST DES PERMISSIONS ET ERREURS 403")
    print("=" * 60)
    
    try:
        test_permissions()
        test_csrf_and_requests()
        test_direct_view_access()
        
        # Créer un achat de test si nécessaire
        if BookPurchase.objects.count() == 0:
            create_test_purchase()
        
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DES TESTS")
        print("=" * 60)
        print("1. Vérifiez que votre utilisateur a les permissions is_staff=True")
        print("2. Vérifiez que le token CSRF est présent dans les requêtes")
        print("3. Vérifiez que les vues sont correctement décorées avec @staff_member_required")
        print("4. Testez manuellement la confirmation d'achat sur: http://127.0.0.1:8000/admin-purchases/")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
