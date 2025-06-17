#!/usr/bin/env python
"""
Script de test pour vérifier le fonctionnement des favoris
"""

import os
import sys
import django
import requests
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from library.models import Book, Favorite

def test_favorites_functionality():
    """Test de la fonctionnalité des favoris"""
    print("🧪 Test de la fonctionnalité des favoris")
    print("=" * 50)
    
    # Créer un client de test
    client = Client()
    
    # Obtenir un utilisateur et un livre pour le test
    User = get_user_model()
    try:
        user = User.objects.filter(is_active=True).first()
        book = Book.objects.first()
        
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
            
        if not book:
            print("❌ Aucun livre trouvé")
            return False
            
        print(f"👤 Utilisateur de test: {user.username}")
        print(f"📚 Livre de test: {book.title}")
        
        # Se connecter
        client.force_login(user)
        print("✅ Connexion réussie")
        
        # Vérifier l'état initial
        initial_favorites = Favorite.objects.filter(user=user, book=book).count()
        print(f"📊 Favoris initiaux: {initial_favorites}")
        
        # Test 1: Ajouter aux favoris
        print("\n🔄 Test 1: Ajouter aux favoris")
        response = client.post(
            f'/books/{book.id}/toggle-favorite/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse: {data}")
            
            if data.get('success'):
                print("✅ Ajout aux favoris réussi")
                
                # Vérifier en base
                favorites_count = Favorite.objects.filter(user=user, book=book).count()
                if favorites_count > initial_favorites:
                    print("✅ Favori créé en base de données")
                else:
                    print("❌ Favori non créé en base de données")
            else:
                print(f"❌ Erreur: {data.get('message', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Contenu: {response.content.decode()}")
        
        # Test 2: Retirer des favoris
        print("\n🔄 Test 2: Retirer des favoris")
        response = client.post(
            f'/books/{book.id}/toggle-favorite/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse: {data}")
            
            if data.get('success'):
                print("✅ Suppression des favoris réussie")
                
                # Vérifier en base
                favorites_count = Favorite.objects.filter(user=user, book=book).count()
                if favorites_count == initial_favorites:
                    print("✅ Favori supprimé de la base de données")
                else:
                    print("❌ Favori non supprimé de la base de données")
            else:
                print(f"❌ Erreur: {data.get('message', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Contenu: {response.content.decode()}")
        
        # Test 3: Test sans AJAX
        print("\n🔄 Test 3: Test sans AJAX (redirection)")
        response = client.post(f'/books/{book.id}/toggle-favorite/')
        print(f"Status code: {response.status_code}")
        
        if response.status_code in [302, 301]:
            print("✅ Redirection correcte pour requête non-AJAX")
        else:
            print(f"❌ Redirection attendue, reçu: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_favorites_view():
    """Test de la vue my_favorites"""
    print("\n🧪 Test de la vue my_favorites")
    print("=" * 50)
    
    client = Client()
    User = get_user_model()
    
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        client.force_login(user)
        
        response = client.get('/my-favorites/')
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page mes favoris accessible")
            
            # Vérifier le contenu
            content = response.content.decode()
            if 'Mes favoris' in content:
                print("✅ Titre de la page présent")
            else:
                print("❌ Titre de la page manquant")
                
        else:
            print(f"❌ Erreur d'accès à la page: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Démarrage des tests des favoris")
    print("=" * 50)
    
    # Test de la fonctionnalité AJAX
    success1 = test_favorites_functionality()
    
    # Test de la vue
    success2 = test_favorites_view()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 Tous les tests sont passés avec succès!")
    else:
        print("❌ Certains tests ont échoué")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
