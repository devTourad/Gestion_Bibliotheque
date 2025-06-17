#!/usr/bin/env python
"""
Script pour gérer les favoris manuellement
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from library.models import Book, Favorite

def list_books():
    """Lister tous les livres disponibles"""
    books = Book.objects.all().order_by('title')
    print("\n📚 Livres disponibles:")
    print("-" * 50)
    for i, book in enumerate(books, 1):
        print(f"{i:2d}. {book.title}")
        print(f"    Auteur(s): {book.authors_list}")
        print(f"    ID: {book.id}")
        print()
    return books

def list_user_favorites(user):
    """Lister les favoris d'un utilisateur"""
    favorites = Favorite.objects.filter(user=user).select_related('book').order_by('added_date')
    print(f"\n❤️  Favoris de {user.username}:")
    print("-" * 50)
    if favorites:
        for i, favorite in enumerate(favorites, 1):
            print(f"{i:2d}. {favorite.book.title}")
            print(f"    Ajouté le: {favorite.added_date.strftime('%d/%m/%Y à %H:%M')}")
            print(f"    Notes: {favorite.notes or 'Aucune note'}")
            print(f"    ID livre: {favorite.book.id}")
            print()
    else:
        print("Aucun favori pour le moment.")
    return favorites

def add_favorite(user, book_id, notes=""):
    """Ajouter un livre aux favoris"""
    try:
        book = Book.objects.get(id=book_id)
        favorite, created = Favorite.objects.get_or_create(
            user=user,
            book=book,
            defaults={'notes': notes}
        )
        
        if created:
            print(f"✅ '{book.title}' ajouté aux favoris avec succès!")
        else:
            print(f"⚠️  '{book.title}' est déjà dans vos favoris.")
        
        return favorite
    except Book.DoesNotExist:
        print(f"❌ Livre avec l'ID {book_id} non trouvé.")
        return None

def remove_favorite(user, book_id):
    """Supprimer un livre des favoris"""
    try:
        book = Book.objects.get(id=book_id)
        favorite = Favorite.objects.filter(user=user, book=book).first()
        
        if favorite:
            favorite.delete()
            print(f"✅ '{book.title}' supprimé des favoris avec succès!")
            return True
        else:
            print(f"⚠️  '{book.title}' n'est pas dans vos favoris.")
            return False
    except Book.DoesNotExist:
        print(f"❌ Livre avec l'ID {book_id} non trouvé.")
        return False

def interactive_mode():
    """Mode interactif pour gérer les favoris"""
    User = get_user_model()
    
    # Obtenir l'utilisateur
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return
    
    print(f"👤 Utilisateur connecté: {user.username}")
    
    while True:
        print("\n" + "="*60)
        print("🔧 GESTIONNAIRE DE FAVORIS")
        print("="*60)
        print("1. Lister tous les livres")
        print("2. Lister mes favoris")
        print("3. Ajouter un livre aux favoris")
        print("4. Supprimer un livre des favoris")
        print("5. Ajouter 3 livres populaires aux favoris")
        print("6. Vider tous les favoris")
        print("0. Quitter")
        print("-" * 60)
        
        choice = input("Votre choix: ").strip()
        
        if choice == "0":
            print("👋 Au revoir!")
            break
        elif choice == "1":
            list_books()
        elif choice == "2":
            list_user_favorites(user)
        elif choice == "3":
            list_books()
            try:
                book_id = int(input("\nID du livre à ajouter: "))
                notes = input("Notes (optionnel): ").strip()
                add_favorite(user, book_id, notes)
            except ValueError:
                print("❌ ID invalide")
        elif choice == "4":
            list_user_favorites(user)
            try:
                book_id = int(input("\nID du livre à supprimer: "))
                remove_favorite(user, book_id)
            except ValueError:
                print("❌ ID invalide")
        elif choice == "5":
            # Ajouter 3 livres populaires
            popular_books = Book.objects.all()[:3]
            added_count = 0
            for book in popular_books:
                favorite, created = Favorite.objects.get_or_create(
                    user=user,
                    book=book,
                    defaults={'notes': 'Livre populaire ajouté automatiquement'}
                )
                if created:
                    added_count += 1
                    print(f"✅ '{book.title}' ajouté aux favoris")
                else:
                    print(f"⚠️  '{book.title}' déjà dans les favoris")
            print(f"\n🎉 {added_count} nouveaux favoris ajoutés!")
        elif choice == "6":
            confirm = input("⚠️  Êtes-vous sûr de vouloir supprimer TOUS vos favoris? (oui/non): ")
            if confirm.lower() in ['oui', 'o', 'yes', 'y']:
                count = Favorite.objects.filter(user=user).count()
                Favorite.objects.filter(user=user).delete()
                print(f"✅ {count} favoris supprimés")
            else:
                print("❌ Annulé")
        else:
            print("❌ Choix invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")

def quick_add_favorites():
    """Ajouter rapidement 3 favoris"""
    User = get_user_model()
    user = User.objects.filter(is_active=True).first()
    
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return
    
    print(f"👤 Utilisateur: {user.username}")
    
    # Prendre les 3 premiers livres
    books = Book.objects.all()[:3]
    
    print(f"\n📚 Ajout de {len(books)} livres aux favoris...")
    
    for book in books:
        favorite, created = Favorite.objects.get_or_create(
            user=user,
            book=book,
            defaults={'notes': f'Ajouté le {date.today()}'}
        )
        
        if created:
            print(f"✅ '{book.title}' ajouté aux favoris")
        else:
            print(f"⚠️  '{book.title}' déjà dans les favoris")
    
    # Afficher le résumé
    total_favorites = Favorite.objects.filter(user=user).count()
    print(f"\n🎉 Vous avez maintenant {total_favorites} favoris au total!")

def main():
    """Fonction principale"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_add_favorites()
    else:
        interactive_mode()

if __name__ == '__main__':
    main()
