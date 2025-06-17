"""
Décorateurs personnalisés pour les permissions de la bibliothèque
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def super_admin_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est un super administrateur
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.is_super_admin or request.user.is_superuser):
            messages.error(request, "Accès refusé. Vous devez être super administrateur pour accéder à cette page.")
            return HttpResponseForbidden("Accès refusé. Privilèges super administrateur requis.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est administrateur (staff, super admin ou superuser)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.is_staff or request.user.is_super_admin or request.user.is_superuser):
            messages.error(request, "Accès refusé. Vous devez être administrateur pour accéder à cette page.")
            return HttpResponseForbidden("Accès refusé. Privilèges administrateur requis.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_super_admin_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est staff ou super admin
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.is_staff or request.user.is_super_admin or request.user.is_superuser):
            messages.error(request, "Accès refusé. Vous devez être membre du personnel pour accéder à cette page.")
            return HttpResponseForbidden("Accès refusé. Privilèges du personnel requis.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_management_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur peut gérer les autres utilisateurs
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.is_super_admin or request.user.is_superuser):
            messages.error(request, "Accès refusé. Vous devez être super administrateur pour gérer les utilisateurs.")
            return HttpResponseForbidden("Accès refusé. Privilèges de gestion des utilisateurs requis.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def check_user_permissions(user, required_level='staff'):
    """
    Fonction utilitaire pour vérifier les permissions d'un utilisateur
    
    Args:
        user: L'utilisateur à vérifier
        required_level: Le niveau requis ('user', 'staff', 'super_admin', 'superuser')
    
    Returns:
        bool: True si l'utilisateur a les permissions requises
    """
    if not user.is_authenticated:
        return False
    
    if required_level == 'user':
        return True
    elif required_level == 'staff':
        return user.is_staff or user.is_super_admin or user.is_superuser
    elif required_level == 'super_admin':
        return user.is_super_admin or user.is_superuser
    elif required_level == 'superuser':
        return user.is_superuser
    
    return False


def get_user_admin_context(user):
    """
    Retourne le contexte d'administration pour un utilisateur
    
    Args:
        user: L'utilisateur
    
    Returns:
        dict: Contexte avec les permissions
    """
    return {
        'is_admin_user': user.is_staff or user.is_super_admin or user.is_superuser,
        'is_super_admin': user.is_super_admin or user.is_superuser,
        'is_superuser': user.is_superuser,
        'can_manage_users': user.is_super_admin or user.is_superuser,
        'can_manage_system': user.is_super_admin or user.is_superuser,
        'admin_level': user.get_admin_level() if hasattr(user, 'get_admin_level') else 'user',
    }


class PermissionMixin:
    """
    Mixin pour ajouter des vérifications de permissions aux vues basées sur les classes
    """
    required_permission_level = 'staff'
    
    def dispatch(self, request, *args, **kwargs):
        if not check_user_permissions(request.user, self.required_permission_level):
            if not request.user.is_authenticated:
                return redirect('login')
            else:
                messages.error(request, "Accès refusé. Permissions insuffisantes.")
                return HttpResponseForbidden("Accès refusé.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_user_admin_context(self.request.user))
        return context


class SuperAdminMixin(PermissionMixin):
    """
    Mixin pour les vues nécessitant des privilèges super admin
    """
    required_permission_level = 'super_admin'


class UserManagementMixin(PermissionMixin):
    """
    Mixin pour les vues de gestion des utilisateurs
    """
    required_permission_level = 'super_admin'
