#!/usr/bin/env python
"""
Script de débogage pour les URLs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.urls import reverse, resolve
from django.conf import settings
from library.models import BookPurchase

def test_urls():
    """Tester les URLs liées aux achats"""
    print("🔗 TEST DES URLS")
    print("=" * 50)
    
    # URLs à tester
    url_tests = [
        ('admin_purchases', {}),
        ('admin_update_purchase_status', {'purchase_id': 1}),
        ('confirm_purchase', {'purchase_id': 1}),
        ('mark_purchase_paid', {'purchase_id': 1}),
        ('debug_permissions', {}),
    ]
    
    for url_name, kwargs in url_tests:
        try:
            url = reverse(url_name, kwargs=kwargs)
            print(f"✅ {url_name}: {url}")
            
            # Tester la résolution inverse
            try:
                resolved = resolve(url)
                print(f"   → Vue: {resolved.func.__name__}")
            except Exception as e:
                print(f"   ❌ Résolution inverse échouée: {e}")
                
        except Exception as e:
            print(f"❌ {url_name}: Erreur - {e}")
    
    # Tester avec un vrai ID d'achat
    purchase = BookPurchase.objects.first()
    if purchase:
        print(f"\n📋 Test avec achat réel ID {purchase.id}:")
        
        real_tests = [
            ('admin_update_purchase_status', {'purchase_id': purchase.id}),
            ('confirm_purchase', {'purchase_id': purchase.id}),
            ('mark_purchase_paid', {'purchase_id': purchase.id}),
        ]
        
        for url_name, kwargs in real_tests:
            try:
                url = reverse(url_name, kwargs=kwargs)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: Erreur - {e}")
    else:
        print("\n❌ Aucun achat trouvé pour tester avec un ID réel")

def list_all_urls():
    """Lister toutes les URLs disponibles"""
    print("\n📋 TOUTES LES URLS DISPONIBLES")
    print("=" * 50)
    
    from django.urls import get_resolver
    
    resolver = get_resolver()
    
    def print_urls(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                # C'est un include()
                print_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                # C'est une URL normale
                if hasattr(pattern, 'name') and pattern.name:
                    full_pattern = prefix + str(pattern.pattern)
                    print(f"  {pattern.name}: {full_pattern}")
    
    print_urls(resolver.url_patterns)

def test_specific_urls():
    """Tester des URLs spécifiques"""
    print("\n🎯 TEST D'URLS SPÉCIFIQUES")
    print("=" * 50)
    
    # URLs à tester directement
    test_urls = [
        '/admin-purchases/',
        '/admin/purchases/1/update-status/',
        '/admin/purchases/1/confirm/',
        '/admin/purchases/1/mark-paid/',
        '/debug/permissions/',
    ]
    
    for url in test_urls:
        try:
            resolved = resolve(url)
            print(f"✅ {url} → {resolved.func.__name__}")
        except Exception as e:
            print(f"❌ {url} → Erreur: {e}")

def check_url_configuration():
    """Vérifier la configuration des URLs"""
    print("\n⚙️  CONFIGURATION DES URLS")
    print("=" * 50)
    
    # Vérifier le fichier urls.py principal
    main_urls_file = os.path.join(settings.BASE_DIR, 'library_management', 'urls.py')
    print(f"Fichier URLs principal: {main_urls_file}")
    print(f"Existe: {os.path.exists(main_urls_file)}")
    
    # Vérifier le fichier urls.py de l'app
    app_urls_file = os.path.join(settings.BASE_DIR, 'library', 'urls.py')
    print(f"Fichier URLs app: {app_urls_file}")
    print(f"Existe: {os.path.exists(app_urls_file)}")
    
    # Vérifier les apps installées
    print(f"\nApps installées: {settings.INSTALLED_APPS}")
    
    # Vérifier ROOT_URLCONF
    print(f"ROOT_URLCONF: {settings.ROOT_URLCONF}")

def main():
    """Fonction principale"""
    print("🔍 DÉBOGAGE DES URLS")
    print("=" * 60)
    
    try:
        check_url_configuration()
        test_urls()
        test_specific_urls()
        list_all_urls()
        
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ")
        print("=" * 60)
        print("Si des URLs sont manquantes:")
        print("1. Vérifiez library/urls.py")
        print("2. Vérifiez que l'app 'library' est dans INSTALLED_APPS")
        print("3. Vérifiez que include('library.urls') est dans le fichier principal")
        print("4. Redémarrez le serveur Django")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du débogage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
