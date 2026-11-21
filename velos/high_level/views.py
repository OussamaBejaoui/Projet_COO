# Create your views here.
from django.http import JsonResponse
from django.views.generic import DetailView

from . import models


class JsonDetailView(DetailView):
    """Renvoie object.json() au lieu de rendre un template."""

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(self.object.json(), **response_kwargs)


class PaysDetailView(JsonDetailView):
    model = models.Pays


class VilleDetailView(JsonDetailView):
    model = models.Ville


class MachineDetailView(JsonDetailView):
    model = models.Machine


class QuantiteMachineDetailView(JsonDetailView):
    model = models.QuantiteMachine


class LieuDetailView(JsonDetailView):
    model = models.Lieu


class TransportDetailView(JsonDetailView):
    model = models.Transport


class OperationDetailView(JsonDetailView):
    model = models.Operation


class ProduitDetailView(JsonDetailView):
    model = models.Produit


class PrixProduitDetailView(JsonDetailView):
    model = models.PrixProduit


class FournisseurDetailView(JsonDetailView):
    model = models.Fournisseur


class QuantiteProduitDetailView(JsonDetailView):
    model = models.QuantiteProduit


class StockDetailView(JsonDetailView):
    model = models.Stock


class PointDeVenteDetailView(JsonDetailView):
    model = models.PointDeVente


class FactureDetailView(JsonDetailView):
    model = models.Facture


class ApiView(DetailView):
    """Lieu avec toutes ses relations, pour le client C++ (TP4)."""

    model = models.Lieu

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(self.object.json_extended(), **response_kwargs)
