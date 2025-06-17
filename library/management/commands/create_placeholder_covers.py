import os
from PIL import Image, ImageDraw, ImageFont
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from library.models import Book
import io


class Command(BaseCommand):
    help = 'Create placeholder cover images for books without covers'

    def handle(self, *args, **options):
        self.stdout.write('Creating placeholder cover images...')
        
        # Couleurs pour les couvertures
        colors = [
            '#3498db',  # Bleu
            '#e74c3c',  # Rouge
            '#2ecc71',  # Vert
            '#f39c12',  # Orange
            '#9b59b6',  # Violet
            '#1abc9c',  # Turquoise
            '#34495e',  # Gris foncé
            '#e67e22',  # Orange foncé
        ]
        
        books_without_covers = Book.objects.filter(cover_image='')
        
        for i, book in enumerate(books_without_covers):
            try:
                # Créer une image de 400x600 pixels
                img = Image.new('RGB', (400, 600), color=colors[i % len(colors)])
                draw = ImageDraw.Draw(img)
                
                # Essayer d'utiliser une police par défaut
                try:
                    # Taille de police pour le titre
                    font_size = 24
                    font = ImageFont.load_default()
                except:
                    font = None
                
                # Ajouter le titre du livre
                title = book.title
                if len(title) > 30:
                    # Diviser le titre en plusieurs lignes si trop long
                    words = title.split()
                    lines = []
                    current_line = ""
                    
                    for word in words:
                        if len(current_line + word) < 25:
                            current_line += word + " "
                        else:
                            lines.append(current_line.strip())
                            current_line = word + " "
                    lines.append(current_line.strip())
                    
                    # Centrer le texte
                    y_start = 250
                    for line in lines:
                        bbox = draw.textbbox((0, 0), line, font=font)
                        text_width = bbox[2] - bbox[0]
                        x = (400 - text_width) // 2
                        draw.text((x, y_start), line, fill='white', font=font)
                        y_start += 30
                else:
                    # Centrer le titre
                    bbox = draw.textbbox((0, 0), title, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (400 - text_width) // 2
                    y = (600 - text_height) // 2
                    draw.text((x, y), title, fill='white', font=font)
                
                # Ajouter l'auteur
                author_text = book.authors_list
                if len(author_text) > 40:
                    author_text = author_text[:37] + "..."
                
                bbox = draw.textbbox((0, 0), author_text, font=font)
                text_width = bbox[2] - bbox[0]
                x = (400 - text_width) // 2
                draw.text((x, 500), author_text, fill='white', font=font)
                
                # Sauvegarder l'image en mémoire
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG', quality=85)
                img_io.seek(0)
                
                # Créer un nom de fichier
                filename = f"placeholder_{book.id}_{book.title.replace(' ', '_').replace('\'', '').lower()}.jpg"
                
                # Sauvegarder l'image dans le modèle
                book.cover_image.save(
                    filename,
                    ContentFile(img_io.getvalue()),
                    save=True
                )
                
                self.stdout.write(f'Created placeholder cover for: {book.title}')
                
            except Exception as e:
                self.stdout.write(f'Error creating cover for {book.title}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created placeholder covers!')
        )
