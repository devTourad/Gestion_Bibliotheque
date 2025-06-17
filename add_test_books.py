#!/usr/bin/env python
"""
Script pour ajouter des livres de test à la base de données
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from library.models import Book, Author, Genre, Publisher

def create_test_books():
    """Créer des livres de test"""
    print("🔄 Création de livres de test...")
    
    # Créer des auteurs
    authors_data = [
        {"first_name": "Victor", "last_name": "Hugo"},
        {"first_name": "Jules", "last_name": "Verne"},
        {"first_name": "Alexandre", "last_name": "Dumas"},
        {"first_name": "Émile", "last_name": "Zola"},
        {"first_name": "Marcel", "last_name": "Proust"},
    ]
    
    authors = {}
    for author_data in authors_data:
        author, created = Author.objects.get_or_create(
            first_name=author_data["first_name"],
            last_name=author_data["last_name"]
        )
        authors[f"{author_data['first_name']} {author_data['last_name']}"] = author
        if created:
            print(f"✅ Auteur créé: {author.first_name} {author.last_name}")
    
    # Créer des genres
    genres_data = ["Roman", "Aventure", "Classique", "Science-Fiction", "Littérature"]
    genres = {}
    for genre_name in genres_data:
        genre, created = Genre.objects.get_or_create(name=genre_name)
        genres[genre_name] = genre
        if created:
            print(f"✅ Genre créé: {genre_name}")
    
    # Créer un éditeur
    publisher, created = Publisher.objects.get_or_create(
        name="Éditions Classiques",
        defaults={"address": "Paris, France"}
    )
    if created:
        print(f"✅ Éditeur créé: {publisher.name}")
    
    # Créer des livres
    books_data = [
        {
            "title": "Les Misérables",
            "author": "Victor Hugo",
            "isbn": "978-2-07-036000-1",
            "publication_date": date(1862, 1, 1),
            "pages": 1488,
            "language": "fr",
            "genres": ["Roman", "Classique"],
            "description": "Un chef-d'œuvre de la littérature française qui raconte l'histoire de Jean Valjean et de sa quête de rédemption dans la France du XIXe siècle.",
            "total_copies": 3,
            "available_copies": 2,
            "is_for_sale": True,
            "purchase_price": 15.90
        },
        {
            "title": "Vingt mille lieues sous les mers",
            "author": "Jules Verne",
            "isbn": "978-2-07-036001-2",
            "publication_date": date(1870, 1, 1),
            "pages": 424,
            "language": "fr",
            "genres": ["Aventure", "Science-Fiction"],
            "description": "Les aventures extraordinaires du capitaine Nemo et de son sous-marin Nautilus dans les profondeurs océaniques.",
            "total_copies": 2,
            "available_copies": 1,
            "is_for_sale": True,
            "purchase_price": 12.50
        },
        {
            "title": "Le Comte de Monte-Cristo",
            "author": "Alexandre Dumas",
            "isbn": "978-2-07-036002-3",
            "publication_date": date(1844, 1, 1),
            "pages": 1276,
            "language": "fr",
            "genres": ["Roman", "Aventure"],
            "description": "L'histoire d'Edmond Dantès, injustement emprisonné, qui s'évade pour se venger de ceux qui l'ont trahi.",
            "total_copies": 2,
            "available_copies": 2,
            "is_for_sale": True,
            "purchase_price": 18.90
        },
        {
            "title": "Germinal",
            "author": "Émile Zola",
            "isbn": "978-2-07-036003-4",
            "publication_date": date(1885, 1, 1),
            "pages": 592,
            "language": "fr",
            "genres": ["Roman", "Classique"],
            "description": "Un roman puissant sur la condition ouvrière dans les mines du Nord de la France au XIXe siècle.",
            "total_copies": 2,
            "available_copies": 0,
            "is_for_sale": True,
            "purchase_price": 14.90
        },
        {
            "title": "Du côté de chez Swann",
            "author": "Marcel Proust",
            "isbn": "978-2-07-036004-5",
            "publication_date": date(1913, 1, 1),
            "pages": 544,
            "language": "fr",
            "genres": ["Littérature", "Classique"],
            "description": "Le premier tome de 'À la recherche du temps perdu', une œuvre majeure de la littérature française.",
            "total_copies": 1,
            "available_copies": 1,
            "is_for_sale": True,
            "purchase_price": 16.90
        }
    ]
    
    created_books = []
    for book_data in books_data:
        # Vérifier si le livre existe déjà
        if Book.objects.filter(isbn=book_data["isbn"]).exists():
            print(f"⚠️  Livre déjà existant: {book_data['title']}")
            book = Book.objects.get(isbn=book_data["isbn"])
            created_books.append(book)
            continue
        
        # Créer le livre
        book = Book.objects.create(
            title=book_data["title"],
            isbn=book_data["isbn"],
            publication_date=book_data["publication_date"],
            pages=book_data["pages"],
            language=book_data["language"],
            description=book_data["description"],
            total_copies=book_data["total_copies"],
            available_copies=book_data["available_copies"],
            publisher=publisher,
            is_for_sale=book_data["is_for_sale"],
            purchase_price=book_data["purchase_price"]
        )
        
        # Ajouter l'auteur
        author = authors[book_data["author"]]
        book.authors.add(author)
        
        # Ajouter les genres
        for genre_name in book_data["genres"]:
            genre = genres[genre_name]
            book.genres.add(genre)
        
        book.save()
        created_books.append(book)
        print(f"✅ Livre créé: {book.title}")
    
    print(f"\n🎉 {len(created_books)} livres disponibles dans la base de données")
    return created_books

def add_books_to_favorites():
    """Ajouter 3 livres aux favoris de l'utilisateur connecté"""
    from django.contrib.auth import get_user_model
    from library.models import Favorite
    
    User = get_user_model()
    
    # Obtenir le premier utilisateur actif
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return
    
    print(f"\n👤 Utilisateur: {user.username}")
    
    # Obtenir les livres disponibles
    books = Book.objects.all()[:3]  # Prendre les 3 premiers livres
    
    if len(books) < 3:
        print("❌ Pas assez de livres dans la base de données")
        return
    
    print(f"\n📚 Ajout de {len(books)} livres aux favoris...")
    
    favorites_added = 0
    for book in books:
        favorite, created = Favorite.objects.get_or_create(
            user=user,
            book=book,
            defaults={
                'notes': f'Ajouté automatiquement le {date.today()}'
            }
        )
        
        if created:
            print(f"✅ '{book.title}' ajouté aux favoris")
            favorites_added += 1
        else:
            print(f"⚠️  '{book.title}' déjà dans les favoris")
    
    print(f"\n🎉 {favorites_added} nouveaux favoris ajoutés !")
    
    # Afficher tous les favoris de l'utilisateur
    user_favorites = Favorite.objects.filter(user=user).select_related('book')
    print(f"\n📋 Favoris de {user.username}:")
    for i, favorite in enumerate(user_favorites, 1):
        print(f"  {i}. {favorite.book.title} (ajouté le {favorite.added_date.strftime('%d/%m/%Y')})")

def main():
    """Fonction principale"""
    print("🚀 Script d'ajout de livres aux favoris")
    print("=" * 50)
    
    # Créer des livres de test
    books = create_test_books()
    
    # Ajouter aux favoris
    add_books_to_favorites()
    
    print("\n" + "=" * 50)
    print("✅ Script terminé avec succès !")

if __name__ == '__main__':
    main()
