# Create your tests here.

from django.test import TestCase

from .models import (
    Lieu,
    Machine,
    Operation,
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
            nom="France", tva=20, tarif_electrique=0.20, salaire_minimum=1800
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
        self.assertAlmostEqual(lieu.costs(), 103_000)


class PointDeVenteCostsTests(TestCase):
    def test_costs(self):
        pays = Pays.objects.create(
            nom="France", tva=20, tarif_electrique=0.20, salaire_minimum=12
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
        self.assertAlmostEqual(pdv.costs(), 114_230)


class JsonViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        pays = Pays.objects.create(
            nom="France", tva=20, tarif_electrique=0.20, salaire_minimum=12
        )
        cls.ville = Ville.objects.create(
            nom="Labège", taxe_immobiliere=6, prix_m2=2000, pays=pays
        )
        cls.machine = Machine.objects.create(
            nom="CNC", prix=10000, duree_de_vie=10, cout_maintenance=0, superficie=8
        )
        cls.lieu = Lieu.objects.create(
            nom="Usine", ville=cls.ville, superficie=50, consommation_electrique=5000
        )
        cls.lieu.quantite_machines.add(
            QuantiteMachine.objects.create(machine=cls.machine, nombre=2)
        )

    def test_ville_json(self):
        response = self.client.get(f"/ville/{self.ville.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.ville.pk,
                "nom": "Labège",
                "taxe_immobiliere": 6,
                "prix_m2": 2000,
                "pays": self.ville.pays_id,
            },
        )

    def test_lieu_json_has_relation_ids(self):
        data = self.client.get(f"/lieu/{self.lieu.pk}/").json()
        self.assertEqual(data["ville"], self.ville.pk)
        self.assertEqual(len(data["quantite_machines"]), 1)

    def test_missing_object_is_404(self):
        self.assertEqual(self.client.get("/lieu/9999/").status_code, 404)

    def test_api_extended_nests_relations(self):
        data = self.client.get(f"/api/{self.lieu.pk}").json()
        self.assertEqual(data["ville"]["nom"], "Labège")
        self.assertEqual(data["ville"]["pays"]["nom"], "France")
        qm = data["quantite_machines"][0]
        self.assertEqual(qm["nombre"], 2)
        self.assertEqual(qm["machine"]["nom"], "CNC")

    def test_extended_survives_cycles(self):
        produit = Produit.objects.create(
            nom="P", prix_de_vente=1, duree_de_vie=1, nombre_par_palette=1
        )
        op = Operation.objects.create(
            nom="Op",
            cout=1,
            machine=self.machine,
            heures_de_travail=1,
            consommation_electrique=1,
        )
        op.quantite_produits.add(
            QuantiteProduit.objects.create(produit=produit, nombre=1)
        )
        produit.operations.add(op)  # Produit -> Operation -> QuantiteProduit -> Produit
        data = produit.json_extended()
        inner = data["operations"][0]["quantite_produits"][0]["produit"]
        self.assertEqual(inner, {"id": produit.pk})


class LieuElectricityTests(TestCase):
    def test_lieu_costs_with_electricity(self):
        pays = Pays.objects.create(
            nom="France", tva=20, tarif_electrique=0.2, salaire_minimum=12
        )
        ville = Ville.objects.create(
            nom="Labège", taxe_immobiliere=0, prix_m2=2000, pays=pays
        )
        m1 = Machine.objects.create(
            nom="M1", prix=10_000, duree_de_vie=10, cout_maintenance=0, superficie=1
        )
        m2 = Machine.objects.create(
            nom="M2", prix=5_000, duree_de_vie=10, cout_maintenance=0, superficie=1
        )
        lieu = Lieu.objects.create(
            nom="Usine", ville=ville, superficie=50, consommation_electrique=5000
        )
        lieu.quantite_machines.add(
            QuantiteMachine.objects.create(machine=m1, nombre=1),
            QuantiteMachine.objects.create(machine=m2, nombre=1),
        )
        # 100 000 (terrain) + 15 000 (machines) + 5 000 kWh x 0.2 EUR
        self.assertAlmostEqual(lieu.costs(), 116_000)
