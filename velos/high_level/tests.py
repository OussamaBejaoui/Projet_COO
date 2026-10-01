# Create your tests here.

from django.test import TestCase

from .models import (
    Lieu,
    Machine,
    Pays,
    PointDeVente,
    PrixProduit,
    Produit,
    QuantiteMachine,
    QuantiteProduit,
    Stock,
    Ville,
)


class LieuCostsTests(TestCase):
    def test_lieu_costs(self):
        pays = Pays.objects.create(
            nom="France", tva=20, tarif_electrique=20, salaire_minimum=1800
        )
        ville = Ville.objects.create(
            nom="Labège", taxe_immobiliere=0, prix_m2=2000, pays=pays
        )
        m1 = Machine.objects.create(
            nom="M1", prix=1000, duree_de_vie=10, cout_maintenance=0, superficie=1
        )
        m2 = Machine.objects.create(
            nom="M2", prix=2000, duree_de_vie=10, cout_maintenance=0, superficie=1
        )
        lieu = Lieu.objects.create(
            nom="Usine", ville=ville, superficie=50, consommation_electrique=0
        )
        lieu.quantite_machines.add(
            QuantiteMachine.objects.create(machine=m1, nombre=1),
            QuantiteMachine.objects.create(machine=m2, nombre=1),
        )
        self.assertEqual(lieu.costs(), 103_000)


class PointDeVenteCostsTests(TestCase):
    def test_costs(self):
        pays = Pays.objects.create(
            nom="France", tva=20, tarif_electrique=20, salaire_minimum=1800
        )
        ville = Ville.objects.create(
            nom="Labège", taxe_immobiliere=0, prix_m2=2000, pays=pays
        )
        m1 = Machine.objects.create(
            nom="M1", prix=1000, duree_de_vie=10, cout_maintenance=0, superficie=1
        )
        m2 = Machine.objects.create(
            nom="M2", prix=2000, duree_de_vie=10, cout_maintenance=0, superficie=1
        )
        lieu = Lieu.objects.create(
            nom="Usine", ville=ville, superficie=50, consommation_electrique=0
        )
        lieu.quantite_machines.add(
            QuantiteMachine.objects.create(machine=m1, nombre=1),
            QuantiteMachine.objects.create(machine=m2, nombre=1),
        )
        sucre = Produit.objects.create(
            nom="Sucre", prix_de_vente=0, duree_de_vie=1, nombre_par_palette=1
        )
        eau = Produit.objects.create(
            nom="Eau", prix_de_vente=0, duree_de_vie=1, nombre_par_palette=1
        )
        PrixProduit.objects.create(produit=sucre, prix_achat=10)
        PrixProduit.objects.create(produit=eau, prix_achat=15)
        stock = Stock.objects.create(palettes_max=10)
        stock.quantite_produits.add(
            QuantiteProduit.objects.create(produit=sucre, nombre=1000),
            QuantiteProduit.objects.create(produit=eau, nombre=50),
        )
        pdv = PointDeVente.objects.create(
            nom="PDV", lieu=lieu, heures_de_travail=40, stock=stock
        )
        self.assertEqual(pdv.costs(), 113_750)
