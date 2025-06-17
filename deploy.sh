#!/bin/bash

# Script de déploiement automatisé pour la Bibliothèque GPI
# Usage: ./deploy.sh [environment]
# Environments: development, staging, production

set -e  # Arrêter en cas d'erreur

# Configuration
PROJECT_NAME="bibliotheque-gpi"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deploy.log"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a $LOG_FILE
}

# Vérifier les prérequis
check_prerequisites() {
    log "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose n'est pas installé"
    fi
    
    if ! command -v git &> /dev/null; then
        error "Git n'est pas installé"
    fi
    
    log "Prérequis vérifiés ✓"
}

# Créer les répertoires nécessaires
create_directories() {
    log "Création des répertoires..."
    
    mkdir -p $BACKUP_DIR
    mkdir -p ./logs
    mkdir -p ./media/book_covers
    mkdir -p ./staticfiles
    mkdir -p ./ssl
    
    log "Répertoires créés ✓"
}

# Sauvegarder la base de données
backup_database() {
    if [ "$ENVIRONMENT" != "development" ]; then
        log "Sauvegarde de la base de données..."
        
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        if docker-compose ps db | grep -q "Up"; then
            docker-compose exec -T db pg_dump -U gpi_user bibliotheque_gpi > $BACKUP_FILE
            log "Sauvegarde créée: $BACKUP_FILE ✓"
        else
            warning "Base de données non accessible, sauvegarde ignorée"
        fi
    fi
}

# Mettre à jour le code
update_code() {
    log "Mise à jour du code..."
    
    if [ -d ".git" ]; then
        git fetch origin
        git pull origin main
        log "Code mis à jour ✓"
    else
        warning "Pas de repository Git détecté"
    fi
}

# Construire les images Docker
build_images() {
    log "Construction des images Docker..."
    
    docker-compose build --no-cache
    log "Images construites ✓"
}

# Démarrer les services
start_services() {
    log "Démarrage des services..."
    
    # Arrêter les services existants
    docker-compose down
    
    # Démarrer les services
    docker-compose up -d
    
    # Attendre que les services soient prêts
    log "Attente du démarrage des services..."
    sleep 30
    
    # Vérifier que les services sont en cours d'exécution
    if docker-compose ps | grep -q "Up"; then
        log "Services démarrés ✓"
    else
        error "Échec du démarrage des services"
    fi
}

# Exécuter les migrations
run_migrations() {
    log "Exécution des migrations..."
    
    docker-compose exec -T web python manage.py migrate
    log "Migrations exécutées ✓"
}

# Collecter les fichiers statiques
collect_static() {
    log "Collection des fichiers statiques..."
    
    docker-compose exec -T web python manage.py collectstatic --noinput
    log "Fichiers statiques collectés ✓"
}

# Créer un superutilisateur (développement uniquement)
create_superuser() {
    if [ "$ENVIRONMENT" = "development" ]; then
        log "Création du superutilisateur..."
        
        docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@gpi.mr', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"
        log "Superutilisateur configuré ✓"
    fi
}

# Charger les données de test (développement uniquement)
load_test_data() {
    if [ "$ENVIRONMENT" = "development" ]; then
        log "Chargement des données de test..."
        
        if [ -f "fixtures/sample_data.json" ]; then
            docker-compose exec -T web python manage.py loaddata fixtures/sample_data.json
            log "Données de test chargées ✓"
        else
            warning "Fichier de données de test non trouvé"
        fi
    fi
}

# Vérifier la santé de l'application
health_check() {
    log "Vérification de la santé de l'application..."
    
    # Attendre que l'application soit prête
    sleep 10
    
    # Tester la page d'accueil
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        log "Application accessible ✓"
    else
        error "Application non accessible"
    fi
    
    # Tester l'API
    if curl -f http://localhost:8000/api/ > /dev/null 2>&1; then
        log "API accessible ✓"
    else
        warning "API non accessible"
    fi
}

# Nettoyer les anciennes images
cleanup() {
    log "Nettoyage des anciennes images..."
    
    docker image prune -f
    docker volume prune -f
    
    log "Nettoyage terminé ✓"
}

# Afficher les informations de déploiement
show_info() {
    log "=== DÉPLOIEMENT TERMINÉ ==="
    info "Environnement: $ENVIRONMENT"
    info "Application: http://localhost:8000"
    info "Admin: http://localhost:8000/admin"
    
    if [ "$ENVIRONMENT" = "development" ]; then
        info "Superutilisateur: admin / admin123"
    fi
    
    info "Logs: docker-compose logs -f"
    info "Arrêter: docker-compose down"
    log "=========================="
}

# Fonction principale
main() {
    ENVIRONMENT=${1:-development}
    
    log "Début du déploiement - Environnement: $ENVIRONMENT"
    
    check_prerequisites
    create_directories
    backup_database
    update_code
    build_images
    start_services
    run_migrations
    collect_static
    create_superuser
    load_test_data
    health_check
    cleanup
    show_info
    
    log "Déploiement terminé avec succès! 🎉"
}

# Gestion des signaux
trap 'error "Déploiement interrompu"' INT TERM

# Exécution
main "$@"
