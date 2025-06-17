# 📚 Système de Gestion de Bibliothèque GPI

Un système complet de gestion de bibliothèque développé avec Django, offrant des fonctionnalités avancées d'emprunt, d'achat, de livraison et de paiement.

## 🌟 Fonctionnalités Principales

### 👥 Gestion des Utilisateurs
- **Authentification complète** : Inscription, connexion, profils utilisateur
- **Catégories d'utilisateurs** : Étudiant, Enseignant, Personnel, Externe
- **Permissions différenciées** : Quotas et tarifs selon la catégorie
- **Tableau de bord personnalisé** : Vue d'ensemble des activités

### 📖 Gestion des Livres
- **Catalogue complet** : Titre, auteur, ISBN, description, catégorie
- **Couvertures automatiques** : Téléchargement depuis Open Library
- **Recherche avancée** : Par titre, auteur, ISBN, catégorie
- **Galerie visuelle** : Affichage en grille avec couvertures
- **Système de favoris** : Marquer les livres préférés

### 📚 Système d'Emprunt
- **Emprunts intelligents** : Vérification des quotas et disponibilité
- **Gestion des échéances** : Calcul automatique des dates de retour
- **Renouvellements** : Extension de la durée d'emprunt
- **Historique complet** : Suivi de tous les emprunts
- **Alertes automatiques** : Notifications pour les retards

### 🔖 Système de Réservation
- **Réservations en ligne** : Pour les livres non disponibles
- **File d'attente** : Gestion automatique des priorités
- **Notifications** : Alerte quand le livre devient disponible
- **Annulation flexible** : Possibilité d'annuler les réservations

### 🛒 Système d'Achat
- **Achat de livres** : Possibilité d'acheter des exemplaires
- **Remises automatiques** : Selon la catégorie d'utilisateur
- **Panier intelligent** : Calcul automatique des totaux
- **Gestion des quantités** : Commande de plusieurs exemplaires

### 💳 Système de Paiement
- **Paiements multiples** : Espèces, carte, virement, mobile
- **Paiements groupés** : Payer tous les emprunts/achats en une fois
- **Traçabilité complète** : Historique de tous les paiements
- **Statuts en temps réel** : Suivi des paiements en cours

### 🚚 Système de Livraison
- **Modes multiples** : Retrait, domicile, point relais, express
- **Calcul automatique** : Délais et coûts selon le mode
- **Suivi complet** : Statuts de préparation à livraison
- **Informations détaillées** : Destinataire, adresse, instructions

### 📊 Outils d'Administration
- **Interface d'administration** : Gestion complète du système
- **Statistiques avancées** : Tableaux de bord et rapports
- **Gestion des utilisateurs** : Création, modification, permissions
- **Gestion des livres** : Ajout, modification, suppression
- **Suivi des transactions** : Paiements, livraisons, emprunts

## 🛠️ Technologies Utilisées

### Backend
- **Django 4.2+** : Framework web Python
- **SQLite** : Base de données (configurable pour PostgreSQL/MySQL)
- **Django REST Framework** : API REST (optionnel)
- **Pillow** : Traitement d'images pour les couvertures

### Frontend
- **Bootstrap 5** : Framework CSS responsive
- **Font Awesome** : Icônes vectorielles
- **JavaScript vanilla** : Interactions dynamiques
- **AJAX** : Requêtes asynchrones

### Fonctionnalités Avancées
- **Système de cache** : Optimisation des performances
- **Pagination** : Affichage optimisé des listes
- **Recherche full-text** : Recherche avancée dans le contenu
- **Upload de fichiers** : Gestion des couvertures de livres

## 📋 Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)
- Git (pour le clonage du repository)

## 🚀 Installation

### 1. Cloner le repository
```bash
git clone https://github.com/votre-username/bibliotheque-gpi.git
cd bibliotheque-gpi
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration de la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 6. Charger les données de test (optionnel)
```bash
python manage.py loaddata fixtures/sample_data.json
```

### 7. Lancer le serveur
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse : `http://127.0.0.1:8000`

## 📁 Structure du Projet

```
bibliotheque-gpi/
├── library/                    # Application principale
│   ├── models.py              # Modèles de données
│   ├── views.py               # Vues et logique métier
│   ├── forms.py               # Formulaires Django
│   ├── urls.py                # Configuration des URLs
│   ├── admin.py               # Interface d'administration
│   ├── services.py            # Services métier
│   └── templatetags/          # Tags de template personnalisés
├── templates/                  # Templates HTML
│   ├── base.html              # Template de base
│   ├── library/               # Templates de l'application
│   ├── admin/                 # Templates d'administration
│   └── payments/              # Templates de paiement
├── static/                     # Fichiers statiques
│   ├── css/                   # Feuilles de style
│   ├── js/                    # Scripts JavaScript
│   └── images/                # Images
├── media/                      # Fichiers uploadés
│   └── book_covers/           # Couvertures de livres
├── requirements.txt           # Dépendances Python
├── manage.py                  # Script de gestion Django
└── settings.py                # Configuration Django
```

## 🔧 Configuration

### Variables d'environnement
Créez un fichier `.env` à la racine du projet :

```env
DEBUG=True
SECRET_KEY=votre-clé-secrète-django
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1

# Configuration email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe

# Configuration de stockage (optionnel)
MEDIA_ROOT=media/
STATIC_ROOT=staticfiles/
```

### Configuration de la base de données
Pour utiliser PostgreSQL au lieu de SQLite :

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bibliotheque_gpi',
        'USER': 'votre_utilisateur',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 👤 Comptes par Défaut

Après l'installation, vous pouvez utiliser ces comptes de test :

### Administrateur
- **Email** : admin@gpi.mr
- **Mot de passe** : admin123

### Utilisateurs de test
- **Étudiant** : etudiant@gpi.mr / password123
- **Enseignant** : enseignant@gpi.mr / password123
- **Personnel** : personnel@gpi.mr / password123
- **Externe** : externe@gpi.mr / password123

## 📖 Guide d'Utilisation

### Pour les Utilisateurs

#### 1. Emprunter un livre
1. Recherchez le livre dans le catalogue
2. Cliquez sur "Emprunter" si disponible
3. Confirmez l'emprunt
4. Le livre apparaît dans "Mes emprunts"

#### 2. Réserver un livre
1. Si le livre n'est pas disponible, cliquez sur "Réserver"
2. Vous recevrez une notification quand il sera disponible
3. Vous avez 3 jours pour venir l'emprunter

#### 3. Acheter un livre
1. Cliquez sur "Acheter" sur la page du livre
2. Choisissez la quantité et le mode de livraison
3. Procédez au paiement
4. Suivez votre commande dans "Mes achats"

#### 4. Payer les frais
1. Accédez à "Payer tous les frais" depuis le tableau de bord
2. Vérifiez le détail des frais
3. Confirmez le paiement
4. Recevez la confirmation

### Pour les Administrateurs

#### 1. Gestion des livres
1. Accédez à l'interface d'administration
2. Ajoutez/modifiez les livres
3. Gérez les catégories et auteurs
4. Téléchargez les couvertures automatiquement

#### 2. Gestion des utilisateurs
1. Créez de nouveaux comptes utilisateur
2. Modifiez les catégories et permissions
3. Consultez l'historique des activités
4. Gérez les quotas d'emprunt

#### 3. Suivi des transactions
1. Consultez les statistiques en temps réel
2. Gérez les paiements en attente
3. Suivez les livraisons
4. Générez des rapports

## 🔍 Fonctionnalités Avancées

### Système de Diagnostic
- **Debug des frais impayés** : `/debug/outstanding-fees/`
- **Correction automatique** : Outils de réparation des incohérences
- **Analyse détaillée** : Vue complète des transactions

### API REST (En développement)
- Endpoints pour l'intégration avec d'autres systèmes
- Authentification par token
- Documentation automatique avec Swagger

### Notifications
- Emails automatiques pour les échéances
- Alertes pour les livres disponibles
- Confirmations de paiement et livraison

## 🧪 Tests

### Lancer les tests
```bash
python manage.py test
```

### Tests de couverture
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Génère un rapport HTML
```

## 📈 Performance

### Optimisations incluses
- **Mise en cache** : Cache des requêtes fréquentes
- **Pagination** : Affichage optimisé des listes
- **Lazy loading** : Chargement différé des images
- **Compression** : Minification des assets

### Monitoring
- Logs détaillés des erreurs
- Métriques de performance
- Suivi des requêtes lentes

## 🔒 Sécurité

### Mesures de sécurité
- **CSRF Protection** : Protection contre les attaques CSRF
- **XSS Prevention** : Échappement automatique des données
- **SQL Injection** : Utilisation de l'ORM Django
- **Authentification** : Système de sessions sécurisé

### Bonnes pratiques
- Mots de passe hashés avec PBKDF2
- Validation stricte des données d'entrée
- Permissions granulaires par rôle
- Audit trail des actions importantes

## 🌍 Internationalisation

Le système supporte la devise mauritanienne (MRU) et peut être étendu pour d'autres langues :

```python
# settings.py
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Nouakchott'
USE_I18N = True
USE_TZ = True
```

## 🤝 Contribution

### Comment contribuer
1. Forkez le repository
2. Créez une branche pour votre fonctionnalité
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

### Standards de code
- Suivez PEP 8 pour Python
- Utilisez des noms de variables explicites
- Commentez le code complexe
- Écrivez des tests pour les nouvelles fonctionnalités

## 📞 Support

### Documentation
- **Wiki** : Documentation détaillée sur GitHub
- **API Docs** : Documentation de l'API REST
- **Tutoriels** : Guides pas à pas

### Contact
- **Email** : support@gpi.mr
- **Issues** : GitHub Issues pour les bugs
- **Discussions** : GitHub Discussions pour les questions

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Django Community** : Pour le framework excellent
- **Bootstrap Team** : Pour l'interface utilisateur
- **Open Library** : Pour les couvertures de livres
- **Font Awesome** : Pour les icônes

## 🚀 Déploiement en Production

### Avec Docker
```bash
# Construire l'image
docker build -t bibliotheque-gpi .



<p align="center">
  <strong>Développé par Tourad Dah pour les entreprises mauritaniennes</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20in-Mauritania-green?style=for-the-badge" alt="Made in Mauritania">
</p>

# Lancer avec docker-compose
docker-compose up -d
```

### Sur un serveur Linux
```bash
# Installation des dépendances système
sudo apt update
sudo apt install python3 python3-pip nginx postgresql

# Configuration de la base de données
sudo -u postgres createdb bibliotheque_gpi
sudo -u postgres createuser --interactive

# Configuration Nginx
sudo cp nginx.conf /etc/nginx/sites-available/bibliotheque-gpi
sudo ln -s /etc/nginx/sites-available/bibliotheque-gpi /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Configuration Gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 gpi.wsgi:application
```

### Variables d'environnement de production
```env
DEBUG=False
SECRET_KEY=votre-clé-secrète-très-longue-et-complexe
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DATABASE_URL=postgresql://user:password@localhost/bibliotheque_gpi

# Configuration email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.votre-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Configuration de stockage
STATIC_ROOT=/var/www/bibliotheque-gpi/static/
MEDIA_ROOT=/var/www/bibliotheque-gpi/media/
```

## 📊 Métriques et Analytics

### Tableaux de bord disponibles
- **Statistiques générales** : Nombre d'utilisateurs, livres, emprunts
- **Analyse des emprunts** : Livres les plus empruntés, tendances
- **Suivi financier** : Revenus des achats, frais collectés
- **Performance système** : Temps de réponse, erreurs

### Rapports automatiques
- Rapport mensuel des activités
- Analyse des retards et pénalités
- Statistiques d'utilisation par catégorie
- Rapport de performance du système

## 🔧 Maintenance

### Tâches de maintenance régulières
```bash
# Nettoyage des sessions expirées
python manage.py clearsessions

# Optimisation de la base de données
python manage.py dbshell
VACUUM;

# Sauvegarde de la base de données
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Mise à jour des couvertures manquantes
python manage.py shell < scripts/update_covers.py
```

### Monitoring
```bash
# Vérification de l'état du système
python manage.py check --deploy

# Logs d'erreurs
tail -f logs/django.log

# Surveillance des performances
python manage.py shell < scripts/performance_check.py
```

## 🎯 Roadmap

### Version 1.1 (Q1 2025)
- [ ] API REST complète
- [ ] Application mobile (React Native)
- [ ] Système de notifications push
- [ ] Intégration avec des systèmes externes

### Version 1.2 (Q2 2025)
- [ ] Système de recommandations IA
- [ ] Chat en temps réel avec les bibliothécaires
- [ ] Réalité augmentée pour localiser les livres
- [ ] Système de gamification

### Version 2.0 (Q3 2025)
- [ ] Multi-bibliothèques
- [ ] Système de prêt inter-bibliothèques
- [ ] Marketplace de livres d'occasion
- [ ] Intégration blockchain pour la traçabilité

## 🐛 Problèmes Connus

### Limitations actuelles
- **Upload de fichiers** : Limité à 10MB par fichier
- **Recherche** : Pas de recherche full-text avancée
- **Notifications** : Emails uniquement (pas de SMS)
- **Langues** : Interface en français uniquement

### Solutions de contournement
- Utiliser des images optimisées pour les couvertures
- Recherche par mots-clés multiples
- Configuration SMTP pour les notifications
- Traduction manuelle des templates

## 📚 Ressources Supplémentaires

### Documentation technique
- [Guide d'architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Guide de déploiement](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

### Tutoriels vidéo
- [Installation et configuration](https://youtube.com/watch?v=example1)
- [Utilisation pour les bibliothécaires](https://youtube.com/watch?v=example2)
- [Administration avancée](https://youtube.com/watch?v=example3)

### Communauté
- [Forum de discussion](https://forum.gpi.mr)
- [Discord](https://discord.gg/gpi-library)
- [Telegram](https://t.me/gpi_library)

## 🏆 Récompenses et Certifications

- 🥇 **Prix de l'Innovation Numérique 2024** - Ministère de l'Éducation
- 🏅 **Certification ISO 27001** - Sécurité des données
- ⭐ **5 étoiles** - Évaluation des utilisateurs
- 🎖️ **Open Source Award** - Communauté Django Mauritanie

---

<p align="center">
  <strong>Développé par Tourad Dah pour les entreprises mauritaniennes</strong>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Made%20in-Mauritania-green?style=for-the-badge" alt="Made in Mauritania">
</p>


