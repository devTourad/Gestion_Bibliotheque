/**
 * Gestion des actions de réservation
 * Inclut : réservation rapide, annulation, renouvellement
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeReservationActions();
});

function initializeReservationActions() {
    // Gestion des boutons de réservation rapide
    initQuickReservation();
    
    // Gestion des annulations de réservation
    initCancelReservation();
    
    // Gestion des renouvellements d'emprunt
    initLoanRenewal();
    
    // Gestion des favoris
    initFavoriteActions();
    
    // Gestion des statuts de réservation
    initReservationStatus();
}

/**
 * Initialise la réservation rapide
 */
function initQuickReservation() {
    const quickReserveButtons = document.querySelectorAll('.quick-reserve-btn');
    const confirmReserveButton = document.querySelector('.confirm-reserve-btn');
    const modal = document.getElementById('quickReserveModal');
    
    quickReserveButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const bookId = this.dataset.bookId;
            const bookTitle = this.dataset.bookTitle || this.closest('.card').querySelector('.card-title')?.textContent || 'Livre sélectionné';
            const bookAuthor = this.dataset.bookAuthor || this.closest('.card').querySelector('.text-muted')?.textContent || '';
            const queueCount = this.dataset.queueCount || '0';
            const waitTime = this.dataset.waitTime || '7';
            
            // Mettre à jour le modal
            updateReservationModal(bookId, bookTitle, bookAuthor, queueCount, waitTime);
            
            // Afficher le modal
            if (modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        });
    });
    
    // Confirmation de réservation
    if (confirmReserveButton) {
        confirmReserveButton.addEventListener('click', function() {
            const bookId = this.dataset.bookId;
            if (bookId) {
                confirmReservation(bookId);
            }
        });
    }
}

/**
 * Met à jour le contenu du modal de réservation
 */
function updateReservationModal(bookId, title, author, queueCount, waitTime) {
    const modal = document.getElementById('quickReserveModal');
    if (!modal) return;
    
    // Mettre à jour les informations du livre
    const titleElement = modal.querySelector('#modal-book-title');
    const authorElement = modal.querySelector('#modal-book-author');
    const queueElement = modal.querySelector('#modal-queue-count');
    const waitElement = modal.querySelector('#modal-wait-time');
    const confirmButton = modal.querySelector('.confirm-reserve-btn');
    
    if (titleElement) titleElement.textContent = title;
    if (authorElement) authorElement.textContent = author;
    if (queueElement) queueElement.textContent = queueCount;
    if (waitElement) waitElement.textContent = `~${waitTime} jours`;
    if (confirmButton) confirmButton.dataset.bookId = bookId;
}

/**
 * Confirme une réservation
 */
function confirmReservation(bookId) {
    const confirmButton = document.querySelector('.confirm-reserve-btn');
    const originalText = confirmButton.innerHTML;
    
    // Afficher le loading
    confirmButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Réservation...';
    confirmButton.disabled = true;
    
    // Envoyer la requête
    fetch(`/books/${bookId}/reserve/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'quick_reserve': true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Fermer le modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('quickReserveModal'));
            if (modal) modal.hide();
            
            // Afficher le succès
            showToast(data.message || 'Réservation confirmée avec succès !', 'success');
            
            // Mettre à jour l'interface
            updateBookActionButtons(bookId, 'reserved');
            
            // Rediriger vers les réservations après un délai
            setTimeout(() => {
                window.location.href = '/my-reservations/';
            }, 2000);
        } else {
            showToast(data.message || 'Erreur lors de la réservation', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur de connexion lors de la réservation', 'error');
    })
    .finally(() => {
        // Restaurer le bouton
        confirmButton.innerHTML = originalText;
        confirmButton.disabled = false;
    });
}

/**
 * Initialise l'annulation de réservation
 */
function initCancelReservation() {
    const cancelButtons = document.querySelectorAll('.cancel-reservation-btn');
    
    cancelButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const reservationId = this.dataset.reservationId;
            const bookTitle = this.closest('.alert').querySelector('strong').textContent;
            
            if (confirm(`Êtes-vous sûr de vouloir annuler votre réservation pour "${bookTitle}" ?`)) {
                cancelReservation(reservationId);
            }
        });
    });
}

/**
 * Annule une réservation
 */
function cancelReservation(reservationId) {
    fetch(`/reservations/${reservationId}/cancel/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Réservation annulée avec succès', 'success');
            
            // Recharger la page ou mettre à jour l'interface
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showToast(data.message || 'Erreur lors de l\'annulation', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur de connexion', 'error');
    });
}

/**
 * Initialise le renouvellement d'emprunt
 */
function initLoanRenewal() {
    const renewButtons = document.querySelectorAll('.renew-btn');
    
    renewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const loanId = this.dataset.loanId;
            const bookTitle = this.closest('.alert').querySelector('strong').textContent;
            
            if (confirm(`Renouveler l'emprunt de "${bookTitle}" ?`)) {
                renewLoan(loanId);
            }
        });
    });
}

/**
 * Renouvelle un emprunt
 */
function renewLoan(loanId) {
    fetch(`/loans/${loanId}/renew/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Emprunt renouvelé avec succès', 'success');
            
            // Mettre à jour la date d'échéance affichée
            if (data.new_due_date) {
                const dueDateElement = document.querySelector(`[data-loan-id="${loanId}"]`)
                    ?.closest('.alert')
                    ?.querySelector('small');
                if (dueDateElement) {
                    dueDateElement.innerHTML = `Retour prévu le ${data.new_due_date}`;
                }
            }
        } else {
            showToast(data.message || 'Erreur lors du renouvellement', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur de connexion', 'error');
    });
}

/**
 * Initialise les actions de favoris
 */
function initFavoriteActions() {
    const favoriteButtons = document.querySelectorAll('.favorite-btn');

    favoriteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const bookId = this.dataset.bookId;
            const icon = this.querySelector('i');

            // Vérifier que nous avons un bookId
            if (!bookId) {
                console.error('Book ID manquant sur le bouton favori');
                showToast('Erreur: ID du livre manquant', 'error');
                return;
            }

            // Obtenir le token CSRF
            const csrfToken = getCsrfToken();
            if (!csrfToken) {
                console.error('Token CSRF manquant');
                showToast('Erreur: Token de sécurité manquant', 'error');
                return;
            }

            // Désactiver le bouton pendant la requête
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            fetch(`/books/${bookId}/toggle-favorite/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Mettre à jour l'apparence du bouton
                    if (data.action === 'added') {
                        icon.className = 'fas fa-heart';
                        this.title = 'Retirer des favoris';
                        this.classList.remove('btn-outline-danger');
                        this.classList.add('btn-danger');
                        this.innerHTML = '<i class="fas fa-heart"></i>';
                    } else {
                        icon.className = 'far fa-heart';
                        this.title = 'Ajouter aux favoris';
                        this.classList.remove('btn-danger');
                        this.classList.add('btn-outline-danger');
                        this.innerHTML = '<i class="far fa-heart"></i>';
                    }

                    showToast(data.message, 'success');
                } else {
                    // Erreur côté serveur
                    console.error('Erreur serveur:', data.message || 'Erreur inconnue');
                    showToast(data.message || 'Erreur lors de la gestion du favori', 'error');
                    this.innerHTML = originalText;
                }
            })
            .catch(error => {
                console.error('Erreur réseau:', error);
                showToast(`Erreur de connexion: ${error.message}`, 'error');
                this.innerHTML = originalText;
            })
            .finally(() => {
                // Réactiver le bouton
                this.disabled = false;
            });
        });
    });
}

/**
 * Initialise les statuts de réservation
 */
function initReservationStatus() {
    const statusButtons = document.querySelectorAll('.reservation-status-btn');
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const reservationId = this.dataset.reservationId;
            
            // Afficher les détails de la réservation
            showReservationDetails(reservationId);
        });
    });
}

/**
 * Affiche les détails d'une réservation
 */
function showReservationDetails(reservationId) {
    // Rediriger vers la page des réservations avec focus sur cette réservation
    window.location.href = `/my-reservations/#reservation-${reservationId}`;
}

/**
 * Met à jour les boutons d'action d'un livre
 */
function updateBookActionButtons(bookId, newStatus) {
    const bookActions = document.querySelectorAll(`[data-book-id="${bookId}"]`);
    
    bookActions.forEach(element => {
        // Logique de mise à jour selon le nouveau statut
        if (newStatus === 'reserved') {
            // Mettre à jour pour afficher le statut "réservé"
            const actionButton = element.querySelector('.quick-reserve-btn, .borrow-btn');
            if (actionButton) {
                actionButton.className = 'btn btn-warning btn-sm';
                actionButton.innerHTML = '<i class="fas fa-bookmark"></i> Réservé';
                actionButton.disabled = true;
            }
        }
    });
}

/**
 * Utilitaires
 */
function getCsrfToken() {
    // Essayer plusieurs méthodes pour obtenir le token CSRF
    let token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) {
        return token.value;
    }

    // Essayer de récupérer depuis les cookies
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }

    // Essayer de récupérer depuis les meta tags
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }

    console.warn('Token CSRF non trouvé');
    return '';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            <div>${message}</div>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Animation d'entrée
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Suppression automatique après 4 secondes
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

// Exporter les fonctions pour utilisation externe
window.ReservationActions = {
    confirmReservation,
    cancelReservation,
    renewLoan,
    showToast,
    updateBookActionButtons
};
