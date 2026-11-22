from django.db import models


class JsonMixin:
    """Serialisation JSON partagée par tous les modèles."""

    def json(self):
        """Tous les champs du modèle ; les relations sont données par id."""
        data = {"id": self.pk}
        for field in self._meta.concrete_fields:
            if field.primary_key:
                continue
            data[field.name] = getattr(self, field.attname)
        for field in self._meta.many_to_many:
            manager = getattr(self, field.name)
            data[field.name] = list(manager.values_list("pk", flat=True))
        return data

    def json_extended(self, _path=frozenset()):
        """Comme json(), mais les relations sont sérialisées récursivement.

        _path contient les objets déjà en cours de sérialisation : en cas de
        cycle (Produit -> Operation -> QuantiteProduit -> Produit), on se
        contente de l'id pour éviter une récursion infinie.
        """
        path = _path | {(self._meta.label, self.pk)}
        data = {"id": self.pk}
        for field in self._meta.concrete_fields:
            if field.primary_key:
                continue
            if field.is_relation:
                related = getattr(self, field.name)
                data[field.name] = (
                    None if related is None else related._nested_json(path)
                )
            else:
                data[field.name] = getattr(self, field.name)
        for field in self._meta.many_to_many:
            data[field.name] = [
                obj._nested_json(path) for obj in getattr(self, field.name).all()
            ]
        return data

    def _nested_json(self, path):
        if (self._meta.label, self.pk) in path:
            return {"id": self.pk}
        return self.json_extended(path)


# Create your models here.


class Pays(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    tva = models.IntegerField()
    tarif_electrique = models.FloatField()
    salaire_minimum = models.IntegerField()

    def __str__(self):
        return self.nom


class Ville(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    taxe_immobiliere = models.IntegerField()
    prix_m2 = models.IntegerField()
    pays = models.ForeignKey(Pays, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.nom} ({self.pays})"


class Machine(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    prix = models.IntegerField()
    duree_de_vie = models.IntegerField()
    cout_maintenance = models.IntegerField()
    superficie = models.IntegerField()

    def costs(self):
        return self.prix

    def __str__(self):
        return self.nom


class QuantiteMachine(JsonMixin, models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    nombre = models.IntegerField()

    def costs(self):
        return self.nombre * self.machine.prix

    def __str__(self):
        return f"{self.nombre} x {self.machine}"


class Lieu(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    ville = models.ForeignKey(Ville, on_delete=models.PROTECT)
    superficie = models.IntegerField()
    quantite_machines = models.ManyToManyField(QuantiteMachine, blank=True)
    consommation_electrique = models.IntegerField()

    def costs(self):
        terrain = self.superficie * self.ville.prix_m2
        machines = sum(qm.costs() for qm in self.quantite_machines.all())
        electricite = self.consommation_electrique * self.ville.pays.tarif_electrique
        return terrain + machines + electricite

    def __str__(self):
        return f"{self.nom} ({self.ville})"


class Transport(JsonMixin, models.Model):
    nombre_palettes = models.IntegerField()
    cout = models.IntegerField()
    delai = models.IntegerField()
    depart = models.ForeignKey(Lieu, on_delete=models.PROTECT, related_name="departs")
    arrivee = models.ForeignKey(Lieu, on_delete=models.PROTECT, related_name="arrivees")

    def __str__(self):
        return f"{self.depart} -> {self.arrivee}"


class Operation(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    operation_suivante = models.ForeignKey(
        "self", on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )
    cout = models.IntegerField()
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    quantite_produits = models.ManyToManyField("QuantiteProduit", blank=True)
    heures_de_travail = models.IntegerField()
    consommation_electrique = models.IntegerField()

    def __str__(self):
        return self.nom


class Produit(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    prix_de_vente = models.IntegerField()
    duree_de_vie = models.IntegerField()
    nombre_par_palette = models.IntegerField()
    operations = models.ManyToManyField(Operation, blank=True)

    def __str__(self):
        return self.nom


class PrixProduit(JsonMixin, models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    prix_achat = models.IntegerField()

    def __str__(self):
        return f"{self.produit} à {self.prix_achat}"


class Fournisseur(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    prix_produits = models.ManyToManyField(PrixProduit, blank=True)

    def __str__(self):
        return self.nom


class QuantiteProduit(JsonMixin, models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    nombre = models.IntegerField()

    def costs(self):
        prix = self.produit.prixproduit_set.order_by("prix_achat").first()
        return self.nombre * (prix.prix_achat if prix else 0)

    def __str__(self):
        return f"{self.nombre} x {self.produit}"


class Stock(JsonMixin, models.Model):
    quantite_produits = models.ManyToManyField(QuantiteProduit, blank=True)
    palettes_max = models.IntegerField()

    def costs(self):
        return sum(qp.costs() for qp in self.quantite_produits.all())

    def __str__(self):
        return f"Stock {self.pk} (max {self.palettes_max} palettes)"


class PointDeVente(JsonMixin, models.Model):
    nom = models.CharField(max_length=100)
    lieu = models.ForeignKey(Lieu, on_delete=models.PROTECT)
    heures_de_travail = models.IntegerField()
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)

    def costs(self):
        salaires = self.heures_de_travail * self.lieu.ville.pays.salaire_minimum
        return self.lieu.costs() + self.stock.costs() + salaires

    def __str__(self):
        return self.nom


class Facture(JsonMixin, models.Model):
    quantite_produits = models.ManyToManyField(QuantiteProduit, blank=True)
    reduction = models.IntegerField()
    point_de_vente = models.ForeignKey(PointDeVente, on_delete=models.PROTECT)
    client = models.CharField(max_length=100)

    def __str__(self):
        return f"Facture {self.pk} - {self.client}"
