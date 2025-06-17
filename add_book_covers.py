#!/usr/bin/env python
"""
Script pour ajouter des images de couverture aux livres
"""

import os
import sys
import django
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from library.models import Book
from django.core.files.base import ContentFile
from django.db import models

def create_book_cover(title, author, width=400, height=600):
    """Créer une couverture de livre personnalisée"""
    
    # Couleurs pour différents genres
    colors = [
        ('#2C3E50', '#ECF0F1'),  # Bleu foncé / Blanc
        ('#8E44AD', '#F8F9FA'),  # Violet / Blanc
        ('#E74C3C', '#FFFFFF'),  # Rouge / Blanc
        ('#27AE60', '#FFFFFF'),  # Vert / Blanc
        ('#F39C12', '#2C3E50'),  # Orange / Bleu foncé
        ('#34495E', '#ECF0F1'),  # Gris / Blanc
        ('#16A085', '#FFFFFF'),  # Turquoise / Blanc
        ('#D35400', '#FFFFFF'),  # Orange foncé / Blanc
    ]
    
    # Choisir une couleur basée sur le hash du titre
    color_index = hash(title) % len(colors)
    bg_color, text_color = colors[color_index]
    
    # Créer l'image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        # Essayer d'utiliser une police système
        title_font = ImageFont.truetype("arial.ttf", 36)
        author_font = ImageFont.truetype("arial.ttf", 24)
        label_font = ImageFont.truetype("arial.ttf", 16)
    except:
        # Utiliser la police par défaut si arial n'est pas disponible
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    
    # Wrapper le texte du titre
    title_lines = textwrap.wrap(title, width=20)
    author_lines = textwrap.wrap(author, width=25)
    
    # Calculer la position du titre
    title_height = len(title_lines) * 45
    start_y = (height - title_height - 100) // 2
    
    # Dessiner le titre
    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = start_y + i * 45
        draw.text((x, y), line, fill=text_color, font=title_font)
    
    # Dessiner l'auteur
    author_y = start_y + title_height + 40
    for i, line in enumerate(author_lines):
        bbox = draw.textbbox((0, 0), line, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = author_y + i * 30
        draw.text((x, y), line, fill=text_color, font=author_font)
    
    # Ajouter un label "Bibliothèque GPI"
    label_text = "Bibliothèque GPI"
    bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_width = bbox[2] - bbox[0]
    label_x = (width - label_width) // 2
    label_y = height - 40
    draw.text((label_x, label_y), label_text, fill=text_color, font=label_font)
    
    # Ajouter une bordure décorative
    border_width = 10
    draw.rectangle([border_width, border_width, width-border_width, height-border_width], 
                  outline=text_color, width=3)
    
    return img

def download_cover_from_openlibrary(isbn):
    """Télécharger une couverture depuis Open Library"""
    try:
        # API Open Library pour les couvertures
        url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and len(response.content) > 1000:  # Vérifier que ce n'est pas une image vide
            return BytesIO(response.content)
    except:
        pass
    return None

def add_covers_to_books():
    """Ajouter des couvertures aux livres qui n'en ont pas"""

    # Filtrer les livres sans couverture (NULL ou vide)
    books_without_covers = Book.objects.filter(
        models.Q(cover_image__isnull=True) | models.Q(cover_image='')
    )

    print(f"🎨 Ajout de couvertures pour {books_without_covers.count()} livres...\n")
    
    for i, book in enumerate(books_without_covers, 1):
        print(f"📚 {i}/{books_without_covers.count()}: {book.title}")
        
        cover_added = False
        
        # Essayer d'abord de télécharger depuis Open Library
        if book.isbn:
            print(f"   🔍 Recherche sur Open Library (ISBN: {book.isbn})...")
            cover_data = download_cover_from_openlibrary(book.isbn)
            
            if cover_data:
                try:
                    filename = f"cover_{book.id}_{book.isbn}.jpg"
                    book.cover_image.save(filename, ContentFile(cover_data.getvalue()), save=True)
                    print(f"   ✅ Couverture téléchargée depuis Open Library")
                    cover_added = True
                except Exception as e:
                    print(f"   ❌ Erreur lors de la sauvegarde: {e}")
        
        # Si pas de couverture trouvée, créer une couverture personnalisée
        if not cover_added:
            print(f"   🎨 Création d'une couverture personnalisée...")
            try:
                # Créer une couverture personnalisée
                cover_img = create_book_cover(book.title, book.authors_list)
                
                # Sauvegarder l'image
                img_io = BytesIO()
                cover_img.save(img_io, format='JPEG', quality=90)
                img_io.seek(0)
                
                filename = f"generated_cover_{book.id}.jpg"
                book.cover_image.save(filename, ContentFile(img_io.getvalue()), save=True)
                print(f"   ✅ Couverture personnalisée créée")
                cover_added = True
                
            except Exception as e:
                print(f"   ❌ Erreur lors de la création: {e}")
        
        if not cover_added:
            print(f"   ⚠️  Aucune couverture ajoutée pour ce livre")
        
        print()
    
    print("🎉 Processus terminé!")
    
    # Statistiques finales
    total_books = Book.objects.count()
    books_with_covers = Book.objects.exclude(cover_image__isnull=True).exclude(cover_image='').count()
    
    print(f"📊 Statistiques:")
    print(f"   - Total de livres: {total_books}")
    print(f"   - Livres avec couverture: {books_with_covers}")
    print(f"   - Pourcentage: {(books_with_covers/total_books*100):.1f}%")

if __name__ == '__main__':
    try:
        add_covers_to_books()
    except KeyboardInterrupt:
        print("\n⏹️  Processus interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
