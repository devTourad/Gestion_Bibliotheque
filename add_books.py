#!/usr/bin/env python
"""
Script pour ajouter 10 livres variés à la base de données
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from library.models import Book, Author, Genre, Publisher

def create_or_get_author(first_name, last_name):
    """Créer ou récupérer un auteur"""
    author, created = Author.objects.get_or_create(
        first_name=first_name,
        last_name=last_name
    )
    if created:
        print(f"✓ Auteur créé: {author}")
    return author

def create_or_get_genre(name):
    """Créer ou récupérer un genre"""
    genre, created = Genre.objects.get_or_create(name=name)
    if created:
        print(f"✓ Genre créé: {genre}")
    return genre

def create_or_get_publisher(name):
    """Créer ou récupérer un éditeur"""
    publisher, created = Publisher.objects.get_or_create(name=name)
    if created:
        print(f"✓ Éditeur créé: {publisher}")
    return publisher

def add_books():
    """Ajouter 10 livres variés"""
    
    books_data = [
        {
            'title': 'Le Petit Prince',
            'authors': [('Antoine', 'de Saint-Exupéry')],
            'genres': ['Fiction', 'Littérature française'],
            'publisher': 'Gallimard',
            'isbn': '9782070408504',
            'pages': 96,
            'publication_date': date(1943, 4, 6),
            'description': 'Un conte poétique et philosophique sous l\'apparence d\'un conte pour enfants.',
            'total_copies': 5,
            'available_copies': 5,
            'is_for_sale': True,
            'purchase_price': 8.50
        },
        {
            'title': '1984',
            'authors': [('George', 'Orwell')],
            'genres': ['Science-fiction', 'Dystopie'],
            'publisher': 'Secker & Warburg',
            'isbn': '9780451524935',
            'pages': 328,
            'publication_date': date(1949, 6, 8),
            'description': 'Un roman dystopique qui dépeint une société totalitaire.',
            'total_copies': 4,
            'available_copies': 3,
            'is_for_sale': True,
            'purchase_price': 12.90
        },
        {
            'title': 'Harry Potter à l\'école des sorciers',
            'authors': [('J.K.', 'Rowling')],
            'genres': ['Fantasy', 'Jeunesse'],
            'publisher': 'Gallimard Jeunesse',
            'isbn': '9782070541270',
            'pages': 320,
            'publication_date': date(1997, 6, 26),
            'description': 'Le premier tome de la saga Harry Potter.',
            'total_copies': 6,
            'available_copies': 4,
            'is_for_sale': True,
            'purchase_price': 16.90
        },
        {
            'title': 'L\'Étranger',
            'authors': [('Albert', 'Camus')],
            'genres': ['Littérature française', 'Philosophie'],
            'publisher': 'Gallimard',
            'isbn': '9782070360024',
            'pages': 186,
            'publication_date': date(1942, 5, 19),
            'description': 'Un roman existentialiste sur l\'absurdité de la condition humaine.',
            'total_copies': 3,
            'available_copies': 2,
            'is_for_sale': True,
            'purchase_price': 9.20
        },
        {
            'title': 'Dune',
            'authors': [('Frank', 'Herbert')],
            'genres': ['Science-fiction', 'Space opera'],
            'publisher': 'Chilton Books',
            'isbn': '9780441172719',
            'pages': 688,
            'publication_date': date(1965, 8, 1),
            'description': 'Un chef-d\'œuvre de la science-fiction se déroulant sur la planète Arrakis.',
            'total_copies': 4,
            'available_copies': 4,
            'is_for_sale': True,
            'purchase_price': 22.50
        },
        {
            'title': 'Pride and Prejudice',
            'authors': [('Jane', 'Austen')],
            'genres': ['Romance', 'Littérature anglaise'],
            'publisher': 'T. Egerton',
            'isbn': '9780141439518',
            'pages': 432,
            'publication_date': date(1813, 1, 28),
            'description': 'Un classique de la littérature anglaise sur l\'amour et les préjugés sociaux.',
            'total_copies': 3,
            'available_copies': 1,
            'is_for_sale': True,
            'purchase_price': 11.50
        },
        {
            'title': 'Le Seigneur des Anneaux : La Communauté de l\'Anneau',
            'authors': [('J.R.R.', 'Tolkien')],
            'genres': ['Fantasy', 'Aventure'],
            'publisher': 'Allen & Unwin',
            'isbn': '9782070612888',
            'pages': 576,
            'publication_date': date(1954, 7, 29),
            'description': 'Le premier tome de l\'épopée fantasy la plus célèbre au monde.',
            'total_copies': 5,
            'available_copies': 3,
            'is_for_sale': True,
            'purchase_price': 18.90
        },
        {
            'title': 'Sapiens : Une brève histoire de l\'humanité',
            'authors': [('Yuval Noah', 'Harari')],
            'genres': ['Histoire', 'Anthropologie'],
            'publisher': 'Albin Michel',
            'isbn': '9782226257017',
            'pages': 512,
            'publication_date': date(2011, 1, 1),
            'description': 'Une exploration fascinante de l\'histoire de l\'espèce humaine.',
            'total_copies': 4,
            'available_copies': 4,
            'is_for_sale': True,
            'purchase_price': 24.90
        },
        {
            'title': 'Les Misérables',
            'authors': [('Victor', 'Hugo')],
            'genres': ['Littérature française', 'Historique'],
            'publisher': 'A. Lacroix, Verboeckhoven & Cie',
            'isbn': '9782070409228',
            'pages': 1488,
            'publication_date': date(1862, 3, 30),
            'description': 'Un monument de la littérature française du XIXe siècle.',
            'total_copies': 3,
            'available_copies': 2,
            'is_for_sale': True,
            'purchase_price': 15.90
        },
        {
            'title': 'Steve Jobs',
            'authors': [('Walter', 'Isaacson')],
            'genres': ['Biographie', 'Technologie'],
            'publisher': 'Simon & Schuster',
            'isbn': '9781451648539',
            'pages': 656,
            'publication_date': date(2011, 10, 24),
            'description': 'La biographie officielle du cofondateur d\'Apple.',
            'total_copies': 2,
            'available_copies': 2,
            'is_for_sale': True,
            'purchase_price': 26.90
        }
    ]
    
    print("🚀 Début de l'ajout des livres...\n")
    
    for i, book_data in enumerate(books_data, 1):
        print(f"📚 Ajout du livre {i}/10: {book_data['title']}")
        
        # Créer ou récupérer l'éditeur
        publisher = create_or_get_publisher(book_data['publisher'])
        
        # Vérifier si le livre existe déjà
        if Book.objects.filter(isbn=book_data['isbn']).exists():
            print(f"⚠️  Le livre '{book_data['title']}' existe déjà (ISBN: {book_data['isbn']})")
            continue
        
        # Créer le livre
        book = Book.objects.create(
            title=book_data['title'],
            isbn=book_data['isbn'],
            pages=book_data['pages'],
            publication_date=book_data['publication_date'],
            description=book_data['description'],
            publisher=publisher,
            total_copies=book_data['total_copies'],
            available_copies=book_data['available_copies'],
            is_for_sale=book_data['is_for_sale'],
            purchase_price=book_data['purchase_price']
        )
        
        # Ajouter les auteurs
        for first_name, last_name in book_data['authors']:
            author = create_or_get_author(first_name, last_name)
            book.authors.add(author)
        
        # Ajouter les genres
        for genre_name in book_data['genres']:
            genre = create_or_get_genre(genre_name)
            book.genres.add(genre)
        
        print(f"✅ Livre '{book.title}' ajouté avec succès!")
        print(f"   - Auteur(s): {book.authors_list}")
        print(f"   - Genre(s): {', '.join([g.name for g in book.genres.all()])}")
        print(f"   - Exemplaires: {book.available_copies}/{book.total_copies}")
        print(f"   - Prix: {book.purchase_price}€\n")
    
    print("🎉 Tous les livres ont été ajoutés avec succès!")
    print(f"📊 Total de livres dans la base: {Book.objects.count()}")

if __name__ == '__main__':
    add_books()
