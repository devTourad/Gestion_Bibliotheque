# Guide de Contribution

Merci de votre intérêt pour contribuer au projet Bibliothèque GPI ! Ce guide vous aidera à comprendre comment participer au développement.

## 📋 Table des matières

- [Code de conduite](#code-de-conduite)
- [Comment contribuer](#comment-contribuer)
- [Configuration de l'environnement](#configuration-de-lenvironnement)
- [Standards de code](#standards-de-code)
- [Processus de développement](#processus-de-développement)
- [Tests](#tests)
- [Documentation](#documentation)
- [Signalement de bugs](#signalement-de-bugs)
- [Demandes de fonctionnalités](#demandes-de-fonctionnalités)

## 🤝 Code de conduite

Ce projet adhère au [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). En participant, vous vous engagez à respecter ce code.

## 🚀 Comment contribuer

### Types de contributions

Nous accueillons plusieurs types de contributions :

- **Corrections de bugs** 🐛
- **Nouvelles fonctionnalités** ✨
- **Améliorations de la documentation** 📚
- **Optimisations de performance** ⚡
- **Améliorations de l'interface utilisateur** 🎨
- **Tests** 🧪
- **Traductions** 🌍

### Première contribution

1. **Forkez** le repository
2. **Clonez** votre fork localement
3. **Créez** une branche pour votre contribution
4. **Faites** vos modifications
5. **Testez** vos changements
6. **Committez** avec un message descriptif
7. **Poussez** vers votre fork
8. **Ouvrez** une Pull Request

## 🛠️ Configuration de l'environnement

### Prérequis

- Python 3.8+
- Git
- Docker (optionnel mais recommandé)

### Installation

```bash
# Cloner le repository
git clone https://github.com/votre-username/bibliotheque-gpi.git
cd bibliotheque-gpi

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurer la base de données
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver
```

### Configuration avec Docker

```bash
# Construire et lancer les services
docker-compose up -d

# Exécuter les migrations
docker-compose exec web python manage.py migrate

# Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser
```

## 📝 Standards de code

### Style Python

Nous suivons [PEP 8](https://www.python.org/dev/peps/pep-0008/) avec quelques adaptations :

- **Longueur de ligne** : 88 caractères (Black)
- **Indentation** : 4 espaces
- **Quotes** : Guillemets doubles pour les chaînes
- **Imports** : Organisés avec isort

### Outils de formatage

```bash
# Formatter le code
black .

# Organiser les imports
isort .

# Vérifier le style
flake8 .

# Vérifier les types (optionnel)
mypy .
```

### Conventions de nommage

- **Variables et fonctions** : `snake_case`
- **Classes** : `PascalCase`
- **Constantes** : `UPPER_SNAKE_CASE`
- **Fichiers** : `snake_case.py`
- **Templates** : `snake_case.html`

### Structure des commits

Utilisez des messages de commit descriptifs :

```
type(scope): description courte

Description plus détaillée si nécessaire.

Fixes #123
```

**Types de commits :**
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage, style
- `refactor`: Refactorisation
- `test`: Tests
- `chore`: Maintenance

**Exemples :**
```
feat(auth): add password reset functionality
fix(loans): correct overdue calculation
docs(readme): update installation instructions
```

## 🔄 Processus de développement

### Workflow Git

1. **Créez une branche** depuis `main`
   ```bash
   git checkout -b feature/nom-de-la-fonctionnalite
   ```

2. **Développez** votre fonctionnalité
   - Faites des commits atomiques
   - Écrivez des tests
   - Mettez à jour la documentation

3. **Testez** vos changements
   ```bash
   python manage.py test
   ```

4. **Poussez** votre branche
   ```bash
   git push origin feature/nom-de-la-fonctionnalite
   ```

5. **Ouvrez une Pull Request**

### Revue de code

Toutes les contributions passent par une revue de code :

- **Fonctionnalité** : La fonctionnalité fonctionne comme attendu
- **Tests** : Tests appropriés inclus
- **Documentation** : Documentation mise à jour
- **Style** : Code conforme aux standards
- **Performance** : Pas de régression de performance

## 🧪 Tests

### Lancer les tests

```bash
# Tous les tests
python manage.py test

# Tests spécifiques
python manage.py test library.tests.test_models

# Avec couverture
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Écrire des tests

- **Tests unitaires** : Pour la logique métier
- **Tests d'intégration** : Pour les workflows complets
- **Tests de vues** : Pour les endpoints
- **Tests de formulaires** : Pour la validation

Exemple de test :

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from library.models import Book, Loan

User = get_user_model()

class LoanModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123'
        )

    def test_loan_creation(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book
        )
        self.assertEqual(loan.status, 'borrowed')
        self.assertIsNotNone(loan.due_date)
```

## 📚 Documentation

### Types de documentation

- **README** : Vue d'ensemble et installation
- **Docstrings** : Documentation du code
- **Comments** : Explications du code complexe
- **Wiki** : Guides détaillés
- **API Docs** : Documentation de l'API

### Standards de documentation

```python
def calculate_loan_fee(user_category, days_overdue=0):
    """
    Calcule les frais d'emprunt pour un utilisateur.
    
    Args:
        user_category (str): Catégorie de l'utilisateur
        days_overdue (int): Nombre de jours de retard
        
    Returns:
        Decimal: Montant des frais en MRU
        
    Raises:
        ValueError: Si la catégorie est invalide
        
    Example:
        >>> calculate_loan_fee('student', 5)
        Decimal('10.00')
    """
    pass
```

## 🐛 Signalement de bugs

### Avant de signaler

1. **Vérifiez** que le bug n'est pas déjà signalé
2. **Reproduisez** le bug de manière consistante
3. **Testez** sur la dernière version

### Template de bug report

```markdown
**Description du bug**
Description claire et concise du problème.

**Étapes pour reproduire**
1. Aller à '...'
2. Cliquer sur '...'
3. Faire défiler jusqu'à '...'
4. Voir l'erreur

**Comportement attendu**
Description de ce qui devrait se passer.

**Captures d'écran**
Si applicable, ajoutez des captures d'écran.

**Environnement**
- OS: [ex. Windows 10]
- Navigateur: [ex. Chrome 91]
- Version Python: [ex. 3.9]
- Version Django: [ex. 4.2]

**Contexte supplémentaire**
Toute autre information pertinente.
```

## ✨ Demandes de fonctionnalités

### Template de feature request

```markdown
**Problème à résoudre**
Description claire du problème que cette fonctionnalité résoudrait.

**Solution proposée**
Description claire de ce que vous voulez qui se passe.

**Alternatives considérées**
Description des solutions alternatives que vous avez considérées.

**Contexte supplémentaire**
Toute autre information ou capture d'écran pertinente.
```

## 🏷️ Labels

Nous utilisons des labels pour organiser les issues :

- `bug` : Problèmes à corriger
- `enhancement` : Nouvelles fonctionnalités
- `documentation` : Améliorations de la documentation
- `good first issue` : Bon pour les nouveaux contributeurs
- `help wanted` : Aide externe souhaitée
- `priority: high` : Priorité élevée
- `priority: low` : Priorité faible

## 🎉 Reconnaissance

Tous les contributeurs sont reconnus dans :

- Le fichier [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Les notes de version
- Le site web du projet

## 📞 Besoin d'aide ?

- **Discord** : [Rejoignez notre serveur](https://discord.gg/gpi-library)
- **Email** : dev@gpi.mr
- **Issues** : [Ouvrez une issue](https://github.com/votre-username/bibliotheque-gpi/issues)

---

Merci de contribuer au projet Bibliothèque GPI ! 🙏
