from django.contrib import admin

# Register your models here.
from . import models

for model in (
    models.Pays,
    models.Ville,
    models.Machine,
    models.QuantiteMachine,
    models.Lieu,
    models.Transport,
    models.Operation,
    models.Produit,
    models.PrixProduit,
    models.Fournisseur,
    models.QuantiteProduit,
    models.Stock,
    models.PointDeVente,
    models.Facture,
):
    admin.site.register(model)
