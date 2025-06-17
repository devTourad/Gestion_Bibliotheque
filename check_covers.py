#!/usr/bin/env python
"""
Script pour vérifier les couvertures des livres
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from library.models import Book

def check_book_covers():
    """Vérifier l'état des couvertures"""
    
    all_books = Book.objects.all().order_by('title')
    books_with_covers = []
    books_without_covers = []
    
    print("📚 État des couvertures de livres:\n")
    
    for book in all_books:
        if book.cover_image and book.cover_image.name:
            books_with_covers.append(book)
            print(f"✅ {book.title} - {book.authors_list}")
            print(f"   📁 {book.cover_image.name}")
        else:
            books_without_covers.append(book)
            print(f"❌ {book.title} - {book.authors_list}")
            print(f"   📄 ISBN: {book.isbn}")
    
    print(f"\n📊 Résumé:")
    print(f"   - Total de livres: {all_books.count()}")
    print(f"   - Avec couverture: {len(books_with_covers)}")
    print(f"   - Sans couverture: {len(books_without_covers)}")
    print(f"   - Pourcentage avec couverture: {(len(books_with_covers)/all_books.count()*100):.1f}%")
    
    if books_without_covers:
        print(f"\n🎨 Livres sans couverture:")
        for book in books_without_covers:
            print(f"   - {book.title} (ID: {book.id})")

if __name__ == '__main__':
    check_book_covers()
