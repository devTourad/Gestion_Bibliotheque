#!/usr/bin/env python
"""
Script pour créer ou promouvoir un super administrateur
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_super_admin():
    """Créer ou promouvoir un super administrateur"""
    print("👑 Création/Promotion d'un Super Administrateur")
    print("=" * 50)
    
    User = get_user_model()
    
    # Afficher les utilisateurs existants
    print("\n📋 Utilisateurs existants:")
    users = User.objects.all().order_by('username')
    
    for i, user in enumerate(users, 1):
        status = []
        if user.is_superuser:
            status.append("SUPERUSER")
        if user.is_super_admin:
            status.append("SUPER ADMIN")
        if user.is_staff:
            status.append("STAFF")
        if not status:
            status.append("UTILISATEUR")
        
        status_str = " | ".join(status)
        print(f"  {i}. {user.username} ({user.get_full_name()}) - {status_str}")
    
    print("\n" + "=" * 50)
    
    # Demander quel utilisateur promouvoir
    while True:
        try:
            choice = input("\nEntrez le numéro de l'utilisateur à promouvoir (ou 'q' pour quitter): ").strip()
            
            if choice.lower() == 'q':
                print("❌ Opération annulée.")
                return
            
            user_index = int(choice) - 1
            if 0 <= user_index < len(users):
                selected_user = users[user_index]
                break
            else:
                print("❌ Numéro invalide. Veuillez réessayer.")
        except ValueError:
            print("❌ Veuillez entrer un numéro valide.")
    
    print(f"\n👤 Utilisateur sélectionné: {selected_user.username} ({selected_user.get_full_name()})")
    
    # Afficher le statut actuel
    current_status = []
    if selected_user.is_superuser:
        current_status.append("Superutilisateur Django")
    if selected_user.is_super_admin:
        current_status.append("Super Administrateur")
    if selected_user.is_staff:
        current_status.append("Staff")
    if not current_status:
        current_status.append("Utilisateur régulier")
    
    print(f"📊 Statut actuel: {' | '.join(current_status)}")
    
    # Demander l'action à effectuer
    print("\n🔧 Actions disponibles:")
    print("1. Promouvoir en Super Administrateur")
    print("2. Promouvoir en Staff")
    print("3. Retirer tous les privilèges administratifs")
    print("4. Annuler")
    
    while True:
        try:
            action = input("\nChoisissez une action (1-4): ").strip()
            
            if action == '1':
                # Promouvoir en Super Admin
                if selected_user.is_super_admin:
                    print("⚠️  L'utilisateur est déjà Super Administrateur.")
                    return
                
                confirm = input(f"Confirmer la promotion de {selected_user.username} en Super Administrateur ? (o/N): ").strip().lower()
                if confirm in ['o', 'oui', 'y', 'yes']:
                    selected_user.is_super_admin = True
                    selected_user.is_staff = True  # Un super admin doit aussi être staff
                    selected_user.save()
                    print(f"✅ {selected_user.username} est maintenant Super Administrateur !")
                else:
                    print("❌ Opération annulée.")
                break
                
            elif action == '2':
                # Promouvoir en Staff
                if selected_user.is_staff and not selected_user.is_super_admin:
                    print("⚠️  L'utilisateur est déjà Staff.")
                    return
                
                confirm = input(f"Confirmer la promotion de {selected_user.username} en Staff ? (o/N): ").strip().lower()
                if confirm in ['o', 'oui', 'y', 'yes']:
                    selected_user.is_staff = True
                    selected_user.is_super_admin = False
                    selected_user.save()
                    print(f"✅ {selected_user.username} est maintenant Staff !")
                else:
                    print("❌ Opération annulée.")
                break
                
            elif action == '3':
                # Retirer privilèges
                if not selected_user.is_staff and not selected_user.is_super_admin:
                    print("⚠️  L'utilisateur n'a pas de privilèges administratifs.")
                    return
                
                if selected_user.is_superuser:
                    print("❌ Impossible de modifier un superutilisateur Django.")
                    return
                
                confirm = input(f"Confirmer la suppression des privilèges de {selected_user.username} ? (o/N): ").strip().lower()
                if confirm in ['o', 'oui', 'y', 'yes']:
                    selected_user.is_staff = False
                    selected_user.is_super_admin = False
                    selected_user.save()
                    print(f"✅ Privilèges administratifs retirés à {selected_user.username} !")
                else:
                    print("❌ Opération annulée.")
                break
                
            elif action == '4':
                print("❌ Opération annulée.")
                return
                
            else:
                print("❌ Choix invalide. Veuillez réessayer.")
                
        except ValueError:
            print("❌ Veuillez entrer un numéro valide.")
    
    # Afficher le nouveau statut
    print(f"\n📊 Nouveau statut de {selected_user.username}:")
    new_status = []
    if selected_user.is_superuser:
        new_status.append("Superutilisateur Django")
    if selected_user.is_super_admin:
        new_status.append("Super Administrateur")
    if selected_user.is_staff:
        new_status.append("Staff")
    if not new_status:
        new_status.append("Utilisateur régulier")
    
    print(f"   {' | '.join(new_status)}")
    
    # Afficher les permissions
    print(f"\n🔐 Permissions:")
    print(f"   - Accès administration: {'✅' if selected_user.is_staff or selected_user.is_super_admin else '❌'}")
    print(f"   - Gestion utilisateurs: {'✅' if selected_user.is_super_admin else '❌'}")
    print(f"   - Paramètres système: {'✅' if selected_user.is_super_admin else '❌'}")

def main():
    """Fonction principale"""
    try:
        create_super_admin()
    except KeyboardInterrupt:
        print("\n\n❌ Opération interrompue par l'utilisateur.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    print("\n" + "=" * 50)
    print("🔗 Accès Super Admin: http://127.0.0.1:8000/super-admin/")

if __name__ == '__main__':
    main()
