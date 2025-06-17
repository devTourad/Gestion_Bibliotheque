from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Livre)
admin.site.register(Utilisateur)
admin.site.register(Emprunt)
admin.site.register(Commande)
admin.site.register(Reservation)
admin.site.register(Panier)
admin.site.register(ArticlePanier)
admin.site.register(ArticleCommande)
admin.site.register(ActionRecente)
