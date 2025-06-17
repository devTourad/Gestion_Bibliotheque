from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from library.models import (
    CustomUser, Genre, Author, Publisher, Book, Loan, Reservation
)


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Créer des genres
        genres_data = [
            ('Roman', 'Œuvres de fiction narrative'),
            ('Science-Fiction', 'Littérature d\'anticipation'),
            ('Fantasy', 'Littérature fantastique'),
            ('Thriller', 'Romans à suspense'),
            ('Histoire', 'Livres d\'histoire'),
            ('Biographie', 'Biographies et autobiographies'),
            ('Informatique', 'Livres techniques informatique'),
            ('Philosophie', 'Ouvrages philosophiques'),
            ('Poésie', 'Recueils de poèmes'),
            ('Jeunesse', 'Littérature pour enfants et adolescents'),
        ]
        
        for name, description in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Created genre: {name}')
        
        # Créer des auteurs
        authors_data = [
            ('Victor', 'Hugo', date(1802, 2, 26), date(1885, 5, 22), 'Française'),
            ('Jules', 'Verne', date(1828, 2, 8), date(1905, 3, 24), 'Française'),
            ('Agatha', 'Christie', date(1890, 9, 15), date(1976, 1, 12), 'Britannique'),
            ('Isaac', 'Asimov', date(1920, 1, 2), date(1992, 4, 6), 'Américaine'),
            ('J.K.', 'Rowling', date(1965, 7, 31), None, 'Britannique'),
            ('Stephen', 'King', date(1947, 9, 21), None, 'Américaine'),
            ('Haruki', 'Murakami', date(1949, 1, 12), None, 'Japonaise'),
            ('Marguerite', 'Yourcenar', date(1903, 6, 8), date(1987, 12, 17), 'Française'),
            ('Albert', 'Camus', date(1913, 11, 7), date(1960, 1, 4), 'Française'),
            ('Simone', 'de Beauvoir', date(1908, 1, 9), date(1986, 4, 14), 'Française'),
        ]
        
        for first_name, last_name, birth_date, death_date, nationality in authors_data:
            author, created = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={
                    'birth_date': birth_date,
                    'death_date': death_date,
                    'nationality': nationality
                }
            )
            if created:
                self.stdout.write(f'Created author: {first_name} {last_name}')
        
        # Créer des éditeurs
        publishers_data = [
            ('Gallimard', 'Paris, France'),
            ('Flammarion', 'Paris, France'),
            ('Seuil', 'Paris, France'),
            ('Hachette', 'Paris, France'),
            ('Penguin Random House', 'New York, USA'),
            ('HarperCollins', 'New York, USA'),
            ('Éditions du Masque', 'Paris, France'),
            ('Folio', 'Paris, France'),
            ('Pocket', 'Paris, France'),
            ('Le Livre de Poche', 'Paris, France'),
        ]
        
        for name, address in publishers_data:
            publisher, created = Publisher.objects.get_or_create(
                name=name,
                defaults={'address': address}
            )
            if created:
                self.stdout.write(f'Created publisher: {name}')
        
        # Créer des livres
        books_data = [
            {
                'title': 'Les Misérables',
                'isbn': '978-2-07-036194-1',
                'publication_date': date(1862, 1, 1),
                'pages': 1232,
                'language': 'fr',
                'description': 'Roman de Victor Hugo publié en 1862.',
                'total_copies': 3,
                'available_copies': 2,
                'author_names': ['Victor Hugo'],
                'genre_names': ['Roman', 'Histoire'],
                'publisher_name': 'Gallimard'
            },
            {
                'title': 'Vingt mille lieues sous les mers',
                'isbn': '978-2-07-036195-2',
                'publication_date': date(1870, 1, 1),
                'pages': 424,
                'language': 'fr',
                'description': 'Roman d\'aventures de Jules Verne.',
                'total_copies': 2,
                'available_copies': 1,
                'author_names': ['Jules Verne'],
                'genre_names': ['Science-Fiction', 'Jeunesse'],
                'publisher_name': 'Hachette'
            },
            {
                'title': 'Le Crime de l\'Orient-Express',
                'isbn': '978-2-07-036196-3',
                'publication_date': date(1934, 1, 1),
                'pages': 256,
                'language': 'fr',
                'description': 'Roman policier d\'Agatha Christie.',
                'total_copies': 4,
                'available_copies': 3,
                'author_names': ['Agatha Christie'],
                'genre_names': ['Thriller'],
                'publisher_name': 'Éditions du Masque'
            },
            {
                'title': 'Foundation',
                'isbn': '978-0-553-29335-0',
                'publication_date': date(1951, 1, 1),
                'pages': 244,
                'language': 'en',
                'description': 'Premier tome de la série Fondation d\'Isaac Asimov.',
                'total_copies': 2,
                'available_copies': 2,
                'author_names': ['Isaac Asimov'],
                'genre_names': ['Science-Fiction'],
                'publisher_name': 'Penguin Random House'
            },
            {
                'title': 'Harry Potter à l\'école des sorciers',
                'isbn': '978-2-07-054120-1',
                'publication_date': date(1997, 6, 26),
                'pages': 320,
                'language': 'fr',
                'description': 'Premier tome de la série Harry Potter.',
                'total_copies': 5,
                'available_copies': 4,
                'author_names': ['J.K. Rowling'],
                'genre_names': ['Fantasy', 'Jeunesse'],
                'publisher_name': 'Gallimard'
            },
            {
                'title': 'Shining',
                'isbn': '978-2-07-036197-4',
                'publication_date': date(1977, 1, 28),
                'pages': 688,
                'language': 'fr',
                'description': 'Roman d\'horreur de Stephen King.',
                'total_copies': 3,
                'available_copies': 1,
                'author_names': ['Stephen King'],
                'genre_names': ['Thriller'],
                'publisher_name': 'Flammarion'
            },
            {
                'title': 'Norwegian Wood',
                'isbn': '978-2-07-036198-5',
                'publication_date': date(1987, 1, 1),
                'pages': 296,
                'language': 'fr',
                'description': 'Roman de Haruki Murakami.',
                'total_copies': 2,
                'available_copies': 2,
                'author_names': ['Haruki Murakami'],
                'genre_names': ['Roman'],
                'publisher_name': 'Seuil'
            },
            {
                'title': 'L\'Étranger',
                'isbn': '978-2-07-036199-6',
                'publication_date': date(1942, 1, 1),
                'pages': 186,
                'language': 'fr',
                'description': 'Roman d\'Albert Camus.',
                'total_copies': 4,
                'available_copies': 3,
                'author_names': ['Albert Camus'],
                'genre_names': ['Roman', 'Philosophie'],
                'publisher_name': 'Gallimard'
            }
        ]
        
        for book_data in books_data:
            # Récupérer l'éditeur
            publisher = Publisher.objects.get(name=book_data['publisher_name'])
            
            # Créer le livre
            book, created = Book.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults={
                    'title': book_data['title'],
                    'publication_date': book_data['publication_date'],
                    'pages': book_data['pages'],
                    'language': book_data['language'],
                    'description': book_data['description'],
                    'total_copies': book_data['total_copies'],
                    'available_copies': book_data['available_copies'],
                    'publisher': publisher
                }
            )
            
            if created:
                # Ajouter les auteurs
                for author_name in book_data['author_names']:
                    first_name, last_name = author_name.split(' ', 1)
                    author = Author.objects.get(first_name=first_name, last_name=last_name)
                    book.authors.add(author)
                
                # Ajouter les genres
                for genre_name in book_data['genre_names']:
                    genre = Genre.objects.get(name=genre_name)
                    book.genres.add(genre)
                
                self.stdout.write(f'Created book: {book_data["title"]}')
        
        # Créer quelques utilisateurs de test
        users_data = [
            {
                'username': 'marie.dupont',
                'email': 'marie.dupont@email.com',
                'first_name': 'Marie',
                'last_name': 'Dupont',
                'category': 'student',
                'phone_number': '0123456789'
            },
            {
                'username': 'jean.martin',
                'email': 'jean.martin@email.com',
                'first_name': 'Jean',
                'last_name': 'Martin',
                'category': 'teacher',
                'phone_number': '0123456790'
            },
            {
                'username': 'sophie.bernard',
                'email': 'sophie.bernard@email.com',
                'first_name': 'Sophie',
                'last_name': 'Bernard',
                'category': 'staff',
                'phone_number': '0123456791'
            }
        ]
        
        for user_data in users_data:
            user, created = CustomUser.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'category': user_data['category'],
                    'phone_number': user_data['phone_number'],
                    'is_active_member': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user_data["username"]}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )
