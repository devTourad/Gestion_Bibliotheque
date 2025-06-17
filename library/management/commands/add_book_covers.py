import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from library.models import Book


class Command(BaseCommand):
    help = 'Add cover images to books'

    def handle(self, *args, **options):
        self.stdout.write('Adding cover images to books...')
        
        # URLs d'images de couverture (utilisation d'images libres de droits)
        book_covers = {
            'Les Misérables': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=600&fit=crop',
            'Vingt mille lieues sous les mers': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&h=600&fit=crop',
            'Le Crime de l\'Orient-Express': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=600&fit=crop',
            'Foundation': 'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400&h=600&fit=crop',
            'Harry Potter à l\'école des sorciers': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=600&fit=crop',
            'Shining': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop',
            'Norwegian Wood': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&h=600&fit=crop',
            'L\'Étranger': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&h=600&fit=crop',
        }
        
        for book_title, image_url in book_covers.items():
            try:
                book = Book.objects.get(title=book_title)
                
                # Vérifier si le livre a déjà une image
                if book.cover_image:
                    self.stdout.write(f'Book "{book_title}" already has a cover image')
                    continue
                
                # Télécharger l'image
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    # Créer un nom de fichier sécurisé
                    filename = f"{book_title.replace(' ', '_').replace('\'', '').lower()}.jpg"
                    
                    # Sauvegarder l'image
                    book.cover_image.save(
                        filename,
                        ContentFile(response.content),
                        save=True
                    )
                    
                    self.stdout.write(f'Added cover image for: {book_title}')
                else:
                    self.stdout.write(f'Failed to download image for: {book_title}')
                    
            except Book.DoesNotExist:
                self.stdout.write(f'Book not found: {book_title}')
            except Exception as e:
                self.stdout.write(f'Error processing {book_title}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully added cover images!')
        )
