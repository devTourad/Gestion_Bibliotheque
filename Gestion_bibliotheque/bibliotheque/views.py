# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import *
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.contrib import  messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,logout,login
from .forms import createNewuser

# views.py
# views.py
@login_required(login_url='login')
def liste_livres(request):
    categorie = request.GET.get('categorie')  # récupère la catégorie depuis l'URL
    if categorie:
        livres = Livre.objects.filter(categorie=categorie)
    else:
        livres = Livre.objects.all()
    categories = CategorieLivre.objects.all()  # pour générer la liste des catégories dans le template
    return render(request, 'bibliotheque/liste_livres.html', {'livres': livres, 'categories': categories, 'categorie_selected': categorie})



@login_required(login_url='login')
def detail_livre(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)
    return render(request, 'bibliotheque/detail_livre.html', {'livre': livre})


@login_required
def reserver_livre(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)
    utilisateur = request.user.utilisateur
    # Vérification si déjà réservé/emprunté
    if Reservation.objects.filter(utilisateur=utilisateur, livre=livre, active=True).exists():
        messages.info(request, "Vous avez déjà réservé ce livre.")
        return redirect('liste_livres')
    if livre.statut != 'Disponible':
        messages.error(request, "Ce livre n'est pas disponible.")
        return redirect('liste_livres')

    # Créer un paiement (montant fixe ou selon règle)
    montant = 2.0  # exemple : 2 euros pour réserver
    paiement = Paiement.objects.create(
        utilisateur=utilisateur,
        montant=montant,
        description='Paiement pour réservation du livre {}'.format(livre.titre)
    )

    # Créer la réservation
    Reservation.objects.create(utilisateur=utilisateur, livre=livre)
    livre.statut = 'Réservé'
    livre.save()

    messages.success(request, "Réservation enregistrée et paiement effectué.")
    return redirect('liste_livres')



def acheter_livre(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)
    utilisateur = request.user.utilisateur

    # Vérifier si déjà acheté
    if Achat.objects.filter(utilisateur=utilisateur, livre=livre).exists():
        messages.info(request, "Vous avez déjà acheté ce livre.")
        return redirect('liste_livres')

    if request.method == 'POST':
        montant = livre.prix
        paiement = Paiement.objects.create(
            utilisateur=utilisateur,
            montant=montant,
            description='Paiement pour achat du livre {}'.format(livre.titre)
        )
        # Créer achat
        Achat.objects.create(utilisateur=utilisateur, livre=livre, prix=livre.prix, paiement=paiement)
        livre.statut = 'Vendu'  # ou autre statut
        livre.save()

        messages.success(request, "Achat effectué avec paiement.")
        return redirect('liste_livres')
    return render(request, 'bibliotheque/confirmation_achat.html', {'livre': livre})

@login_required(login_url='login')
def emprunter_livre(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)
    utilisateur = request.user.utilisateur

    # Vérification si déjà emprunté
    if Emprunt.objects.filter(utilisateur=utilisateur, livre=livre, date_retour_effectue__isnull=True).exists():
        messages.info(request, "Vous avez déjà emprunté ce livre.")
        return redirect('liste_livres')

    if livre.statut != 'Disponible':
        messages.error(request, "Ce livre n'est pas disponible.")
        return redirect('liste_livres')

    if request.method == 'POST':
        date_retour_prevues_str = request.POST.get('date_retour')
        try:
            date_retour_prevues = timezone.datetime.strptime(date_retour_prevues_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Format de date invalide.")
            return redirect('emprunter_livre', livre_id=livre_id)

        # Calcul du nombre de jours
        date_emprunt = timezone.now().date()
        jours = (date_retour_prevues - date_emprunt).days
        if jours <= 0:
            messages.error(request, "La date de retour doit être dans le futur.")
            return redirect('emprunter_livre', livre_id=livre_id)

        # Calcul du montant
        montant = jours * 200  # 200 par jour

        # Création du paiement
        paiement = Paiement.objects.create(
            utilisateur=utilisateur,
            montant=montant,
            description='Paiement pour emprunt du livre {} pour {} jours'.format(livre.titre, jours)
        )

        # Créer l'emprunt
        emprunt = Emprunt.objects.create(
            utilisateur=utilisateur,
            livre=livre,
            date_retour_prevues=date_retour_prevues,
            paiement=paiement
        )

        # Modifier le statut du livre
        livre.statut = 'Emprunté'
        livre.save()

        messages.success(request, "Emprunt enregistré avec paiement.")
        return redirect('liste_livres')
    else:
        # Formulaire pour choisir la date de retour
        return render(request, 'bibliotheque/emprunter_livre.html', {'livre': livre})




def register(request):
        form = createNewuser()
        if request.method == "POST":
                form = createNewuser(request.POST)
                if form.is_valid():
                        user = form.save()
                        username = form.cleaned_data.get('username')
                        messages.success(request, username + '  Created successfuly !')
                        return redirect('login')
                    # else:
                    #   messages.error(request ,  ' invalid Recaptcha please try again!')
        context = {'form':form}
        return render(request,'authentication/register.html',context)



def Userlogin(request):
            username = request.POST.get('username' )
            password = request.POST.get('password' )
            user = authenticate(request, username=username ,password=password)
            if user is not None:
                    login(request,user)
                    return redirect('liste_livres')
            else:
                messages.info(request,' ')
            context = {}
            return render(request,'authentication/login.html',context)



def UserLogout(request):
    logout(request)
    return redirect('login')



