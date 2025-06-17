import os
from PIL import Image
from django.core.management.base import BaseCommand
from django.conf import settings
from library.models import Book


class Command(BaseCommand):
    help = 'Optimize book cover images and create thumbnails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-width',
            type=int,
            default=400,
            help='Maximum width for optimized images (default: 400px)'
        )
        parser.add_argument(
            '--max-height',
            type=int,
            default=600,
            help='Maximum height for optimized images (default: 600px)'
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='JPEG quality (default: 85)'
        )

    def handle(self, *args, **options):
        max_width = options['max_width']
        max_height = options['max_height']
        quality = options['quality']
        
        self.stdout.write(f'Optimizing images with max size {max_width}x{max_height} and quality {quality}...')
        
        books_with_images = Book.objects.exclude(cover_image='')
        optimized_count = 0
        error_count = 0
        
        for book in books_with_images:
            try:
                if book.cover_image and os.path.exists(book.cover_image.path):
                    # Ouvrir l'image
                    with Image.open(book.cover_image.path) as img:
                        # Convertir en RGB si nécessaire (pour les PNG avec transparence)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            # Créer un fond blanc pour les images avec transparence
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Calculer les nouvelles dimensions en gardant le ratio
                        original_width, original_height = img.size
                        ratio = min(max_width / original_width, max_height / original_height)
                        
                        # Ne redimensionner que si l'image est plus grande
                        if ratio < 1:
                            new_width = int(original_width * ratio)
                            new_height = int(original_height * ratio)
                            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            self.stdout.write(f'Resized {book.title}: {original_width}x{original_height} -> {new_width}x{new_height}')
                        
                        # Sauvegarder l'image optimisée
                        img.save(book.cover_image.path, 'JPEG', quality=quality, optimize=True)
                        optimized_count += 1
                        
                        self.stdout.write(f'Optimized: {book.title}')
                
            except Exception as e:
                error_count += 1
                self.stdout.write(f'Error optimizing {book.title}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Optimization complete! {optimized_count} images optimized, {error_count} errors.'
            )
        )


class ThumbnailCommand(BaseCommand):
    """Commande pour créer des miniatures"""
    help = 'Create thumbnails for book cover images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--thumb-width',
            type=int,
            default=150,
            help='Thumbnail width (default: 150px)'
        )
        parser.add_argument(
            '--thumb-height',
            type=int,
            default=225,
            help='Thumbnail height (default: 225px)'
        )

    def handle(self, *args, **options):
        thumb_width = options['thumb_width']
        thumb_height = options['thumb_height']
        
        self.stdout.write(f'Creating thumbnails with size {thumb_width}x{thumb_height}...')
        
        books_with_images = Book.objects.exclude(cover_image='')
        created_count = 0
        error_count = 0
        
        # Créer le dossier des miniatures s'il n'existe pas
        thumb_dir = os.path.join(settings.MEDIA_ROOT, 'book_covers', 'thumbnails')
        os.makedirs(thumb_dir, exist_ok=True)
        
        for book in books_with_images:
            try:
                if book.cover_image and os.path.exists(book.cover_image.path):
                    # Nom du fichier miniature
                    filename = os.path.basename(book.cover_image.path)
                    name, ext = os.path.splitext(filename)
                    thumb_filename = f"{name}_thumb{ext}"
                    thumb_path = os.path.join(thumb_dir, thumb_filename)
                    
                    # Créer la miniature si elle n'existe pas
                    if not os.path.exists(thumb_path):
                        with Image.open(book.cover_image.path) as img:
                            # Convertir en RGB si nécessaire
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Créer la miniature en gardant le ratio
                            img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                            
                            # Sauvegarder la miniature
                            img.save(thumb_path, 'JPEG', quality=90, optimize=True)
                            created_count += 1
                            
                            self.stdout.write(f'Created thumbnail for: {book.title}')
                    else:
                        self.stdout.write(f'Thumbnail already exists for: {book.title}')
                
            except Exception as e:
                error_count += 1
                self.stdout.write(f'Error creating thumbnail for {book.title}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Thumbnail creation complete! {created_count} thumbnails created, {error_count} errors.'
            )
        )
