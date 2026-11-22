// Client C++ du backend Django (TP4).
// Chaque classe C++ reprend les attributs du modèle Django du même nom et
// possède trois constructeurs :
//   - un constructeur prenant directement les attributs,
//   - un constructeur prenant un `json` (réponse HTTP déjà parsée),
//   - un constructeur prenant un `int id` (requête HTTP vers le serveur).
// Les relations sont des std::unique_ptr<>, les attributs non requis des
// std::optional<>.
#include <cpr/cpr.h>

#include <iostream>
#include <memory>
#include <nlohmann/json.hpp>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using json = nlohmann::json;

static const std::string BASE_URL = "http://localhost:8000";

// ---------------------------------------------------------------- réseau

static json fetch(const std::string &route) {
  cpr::Response r = cpr::Get(cpr::Url{BASE_URL + route});
  if (r.status_code != 200)
    throw std::runtime_error("GET " + route + " : HTTP " +
                             std::to_string(r.status_code) + " " +
                             r.error.message);
  return json::parse(r.text);
}

static json fetch(const std::string &model, int id) {
  return fetch("/" + model + "/" + std::to_string(id) + "/");
}

// ------------------------------------------------------------ utilitaires

// Une relation arrive soit sous forme d'objet imbriqué (route /api/<pk>),
// soit sous forme d'id (routes /<modele>/<pk>/) : on gère les deux.
template <class T> static std::unique_ptr<T> make_rel(const json &v) {
  if (v.is_object())
    return std::make_unique<T>(v);
  return std::make_unique<T>(v.get<int>());
}

template <class T>
static std::vector<std::unique_ptr<T>> make_rels(const json &array) {
  std::vector<std::unique_ptr<T>> out;
  for (const json &v : array)
    out.push_back(make_rel<T>(v));
  return out;
}

static int id_of(const json &v) {
  return v.is_object() ? v.at("id").get<int>() : v.get<int>();
}

static std::string pad(int n) { return std::string(n, ' '); }

// ---------------------------------------------------------------- modèles

class Pays {
public:
  int id;
  std::string nom;
  int tva;
  double tarif_electrique;
  int salaire_minimum;

  Pays(int id, std::string nom, int tva, double tarif_electrique,
       int salaire_minimum)
      : id(id), nom(std::move(nom)), tva(tva),
        tarif_electrique(tarif_electrique), salaire_minimum(salaire_minimum) {}
  Pays(const json &data)
      : Pays(data.at("id"), data.at("nom"), data.at("tva"),
             data.at("tarif_electrique"), data.at("salaire_minimum")) {}
  Pays(int id) : Pays(fetch("pays", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Pays #" << id << " " << nom << " (tva " << tva
       << "%, " << tarif_electrique << " EUR/kWh, smic " << salaire_minimum
       << " EUR/h)\n";
  }
};

class Ville {
public:
  int id;
  std::string nom;
  int taxe_immobiliere;
  int prix_m2;
  std::unique_ptr<Pays> pays;

  Ville(int id, std::string nom, int taxe_immobiliere, int prix_m2,
        std::unique_ptr<Pays> pays)
      : id(id), nom(std::move(nom)), taxe_immobiliere(taxe_immobiliere),
        prix_m2(prix_m2), pays(std::move(pays)) {}
  Ville(const json &data)
      : Ville(data.at("id"), data.at("nom"), data.at("taxe_immobiliere"),
              data.at("prix_m2"), make_rel<Pays>(data.at("pays"))) {}
  Ville(int id) : Ville(fetch("ville", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Ville #" << id << " " << nom << " (taxe "
       << taxe_immobiliere << ", " << prix_m2 << " EUR/m2)\n";
    pays->print(os, indent + 2);
  }
};

class Machine {
public:
  int id;
  std::string nom;
  int prix;
  int duree_de_vie;
  int cout_maintenance;
  int superficie;

  Machine(int id, std::string nom, int prix, int duree_de_vie,
          int cout_maintenance, int superficie)
      : id(id), nom(std::move(nom)), prix(prix), duree_de_vie(duree_de_vie),
        cout_maintenance(cout_maintenance), superficie(superficie) {}
  Machine(const json &data)
      : Machine(data.at("id"), data.at("nom"), data.at("prix"),
                data.at("duree_de_vie"), data.at("cout_maintenance"),
                data.at("superficie")) {}
  Machine(int id) : Machine(fetch("machine", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Machine #" << id << " " << nom << " (" << prix
       << " EUR, " << superficie << " m2, maintenance " << cout_maintenance
       << " EUR)\n";
  }
};

class QuantiteMachine {
public:
  int id;
  std::unique_ptr<Machine> machine;
  int nombre;

  QuantiteMachine(int id, std::unique_ptr<Machine> machine, int nombre)
      : id(id), machine(std::move(machine)), nombre(nombre) {}
  QuantiteMachine(const json &data)
      : QuantiteMachine(data.at("id"), make_rel<Machine>(data.at("machine")),
                        data.at("nombre")) {}
  QuantiteMachine(int id) : QuantiteMachine(fetch("quantitemachine", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << nombre << " x\n";
    machine->print(os, indent + 2);
  }
};

// Le modèle Django s'appelle Lieu ; le TP parle de « Localisation ».
class Localisation {
public:
  int id;
  std::string nom;
  std::unique_ptr<Ville> ville;
  int superficie;
  std::vector<std::unique_ptr<QuantiteMachine>> quantite_machines;
  int consommation_electrique;

  Localisation(int id, std::string nom, std::unique_ptr<Ville> ville,
               int superficie,
               std::vector<std::unique_ptr<QuantiteMachine>> quantite_machines,
               int consommation_electrique)
      : id(id), nom(std::move(nom)), ville(std::move(ville)),
        superficie(superficie), quantite_machines(std::move(quantite_machines)),
        consommation_electrique(consommation_electrique) {}
  Localisation(const json &data)
      : Localisation(data.at("id"), data.at("nom"),
                     make_rel<Ville>(data.at("ville")), data.at("superficie"),
                     make_rels<QuantiteMachine>(data.at("quantite_machines")),
                     data.at("consommation_electrique")) {}
  // Route étendue : toutes les relations arrivent imbriquées en une requête.
  Localisation(int id) : Localisation(fetch("/api/" + std::to_string(id))) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Localisation #" << id << " " << nom << " ("
       << superficie << " m2, " << consommation_electrique << " kWh)\n";
    ville->print(os, indent + 2);
    for (const auto &qm : quantite_machines)
      qm->print(os, indent + 2);
  }
};

class Transport {
public:
  int id;
  int nombre_palettes;
  int cout;
  int delai;
  std::unique_ptr<Localisation> depart;
  std::unique_ptr<Localisation> arrivee;

  Transport(int id, int nombre_palettes, int cout, int delai,
            std::unique_ptr<Localisation> depart,
            std::unique_ptr<Localisation> arrivee)
      : id(id), nombre_palettes(nombre_palettes), cout(cout), delai(delai),
        depart(std::move(depart)), arrivee(std::move(arrivee)) {}
  Transport(const json &data)
      : Transport(data.at("id"), data.at("nombre_palettes"), data.at("cout"),
                  data.at("delai"), make_rel<Localisation>(data.at("depart")),
                  make_rel<Localisation>(data.at("arrivee"))) {}
  Transport(int id) : Transport(fetch("transport", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Transport #" << id << " (" << nombre_palettes
       << " palettes, " << cout << " EUR, " << delai << " j)\n";
    os << pad(indent + 2) << "depart : " << depart->nom << "\n";
    os << pad(indent + 2) << "arrivee : " << arrivee->nom << "\n";
  }
};

class Produit {
public:
  int id;
  std::string nom;
  int prix_de_vente;
  int duree_de_vie;
  int nombre_par_palette;
  // Produit -> Operation -> QuantiteProduit -> Produit est un cycle : on ne
  // garde ici que les ids des opérations, pour ne pas boucler à l'infini.
  std::vector<int> operations;

  Produit(int id, std::string nom, int prix_de_vente, int duree_de_vie,
          int nombre_par_palette, std::vector<int> operations)
      : id(id), nom(std::move(nom)), prix_de_vente(prix_de_vente),
        duree_de_vie(duree_de_vie), nombre_par_palette(nombre_par_palette),
        operations(std::move(operations)) {}
  Produit(const json &data)
      : Produit(data.at("id"), data.at("nom"), data.at("prix_de_vente"),
                data.at("duree_de_vie"), data.at("nombre_par_palette"),
                ids(data.at("operations"))) {}
  Produit(int id) : Produit(fetch("produit", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Produit #" << id << " " << nom << " (vente "
       << prix_de_vente << " EUR, " << nombre_par_palette
       << "/palette, operations:";
    for (int op : operations)
      os << " " << op;
    os << ")\n";
  }

private:
  static std::vector<int> ids(const json &array) {
    std::vector<int> out;
    for (const json &v : array)
      out.push_back(id_of(v));
    return out;
  }
};

class QuantiteProduit {
public:
  int id;
  std::unique_ptr<Produit> produit;
  int nombre;

  QuantiteProduit(int id, std::unique_ptr<Produit> produit, int nombre)
      : id(id), produit(std::move(produit)), nombre(nombre) {}
  QuantiteProduit(const json &data)
      : QuantiteProduit(data.at("id"), make_rel<Produit>(data.at("produit")),
                        data.at("nombre")) {}
  QuantiteProduit(int id) : QuantiteProduit(fetch("quantiteproduit", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << nombre << " x\n";
    produit->print(os, indent + 2);
  }
};

class Operation {
public:
  int id;
  std::string nom;
  // Seul attribut non requis du modèle (null=True) : std::optional<>.
  std::optional<std::unique_ptr<Operation>> operation_suivante;
  int cout;
  std::unique_ptr<Machine> machine;
  std::vector<std::unique_ptr<QuantiteProduit>> quantite_produits;
  int heures_de_travail;
  int consommation_electrique;

  Operation(int id, std::string nom,
            std::optional<std::unique_ptr<Operation>> operation_suivante,
            int cout, std::unique_ptr<Machine> machine,
            std::vector<std::unique_ptr<QuantiteProduit>> quantite_produits,
            int heures_de_travail, int consommation_electrique)
      : id(id), nom(std::move(nom)),
        operation_suivante(std::move(operation_suivante)), cout(cout),
        machine(std::move(machine)),
        quantite_produits(std::move(quantite_produits)),
        heures_de_travail(heures_de_travail),
        consommation_electrique(consommation_electrique) {}
  Operation(const json &data)
      : Operation(data.at("id"), data.at("nom"), suivante(data),
                  data.at("cout"), make_rel<Machine>(data.at("machine")),
                  make_rels<QuantiteProduit>(data.at("quantite_produits")),
                  data.at("heures_de_travail"),
                  data.at("consommation_electrique")) {}
  Operation(int id) : Operation(fetch("operation", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Operation #" << id << " " << nom << " (" << cout
       << " EUR, " << heures_de_travail << " h, " << consommation_electrique
       << " kWh)\n";
    machine->print(os, indent + 2);
    for (const auto &qp : quantite_produits)
      qp->print(os, indent + 2);
    if (operation_suivante.has_value()) {
      os << pad(indent + 2) << "suivante :\n";
      (*operation_suivante)->print(os, indent + 4);
    }
  }

private:
  static std::optional<std::unique_ptr<Operation>> suivante(const json &data) {
    const json &v = data.at("operation_suivante");
    if (v.is_null())
      return std::nullopt;
    return make_rel<Operation>(v);
  }
};

class PrixProduit {
public:
  int id;
  std::unique_ptr<Produit> produit;
  int prix_achat;

  PrixProduit(int id, std::unique_ptr<Produit> produit, int prix_achat)
      : id(id), produit(std::move(produit)), prix_achat(prix_achat) {}
  PrixProduit(const json &data)
      : PrixProduit(data.at("id"), make_rel<Produit>(data.at("produit")),
                    data.at("prix_achat")) {}
  PrixProduit(int id) : PrixProduit(fetch("prixproduit", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Prix #" << id << " : " << prix_achat << " EUR\n";
    produit->print(os, indent + 2);
  }
};

class Fournisseur {
public:
  int id;
  std::string nom;
  std::vector<std::unique_ptr<PrixProduit>> prix_produits;

  Fournisseur(int id, std::string nom,
              std::vector<std::unique_ptr<PrixProduit>> prix_produits)
      : id(id), nom(std::move(nom)), prix_produits(std::move(prix_produits)) {}
  Fournisseur(const json &data)
      : Fournisseur(data.at("id"), data.at("nom"),
                    make_rels<PrixProduit>(data.at("prix_produits"))) {}
  Fournisseur(int id) : Fournisseur(fetch("fournisseur", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Fournisseur #" << id << " " << nom << "\n";
    for (const auto &p : prix_produits)
      p->print(os, indent + 2);
  }
};

class Stock {
public:
  int id;
  std::vector<std::unique_ptr<QuantiteProduit>> quantite_produits;
  int palettes_max;

  Stock(int id, std::vector<std::unique_ptr<QuantiteProduit>> quantite_produits,
        int palettes_max)
      : id(id), quantite_produits(std::move(quantite_produits)),
        palettes_max(palettes_max) {}
  Stock(const json &data)
      : Stock(data.at("id"),
              make_rels<QuantiteProduit>(data.at("quantite_produits")),
              data.at("palettes_max")) {}
  Stock(int id) : Stock(fetch("stock", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Stock #" << id << " (max " << palettes_max
       << " palettes)\n";
    for (const auto &qp : quantite_produits)
      qp->print(os, indent + 2);
  }
};

class PointDeVente {
public:
  int id;
  std::string nom;
  std::unique_ptr<Localisation> lieu;
  int heures_de_travail;
  std::unique_ptr<Stock> stock;

  PointDeVente(int id, std::string nom, std::unique_ptr<Localisation> lieu,
               int heures_de_travail, std::unique_ptr<Stock> stock)
      : id(id), nom(std::move(nom)), lieu(std::move(lieu)),
        heures_de_travail(heures_de_travail), stock(std::move(stock)) {}
  PointDeVente(const json &data)
      : PointDeVente(data.at("id"), data.at("nom"),
                     make_rel<Localisation>(data.at("lieu")),
                     data.at("heures_de_travail"),
                     make_rel<Stock>(data.at("stock"))) {}
  PointDeVente(int id) : PointDeVente(fetch("pointdevente", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "PointDeVente #" << id << " " << nom << " ("
       << heures_de_travail << " h)\n";
    lieu->print(os, indent + 2);
    stock->print(os, indent + 2);
  }
};

class Facture {
public:
  int id;
  std::vector<std::unique_ptr<QuantiteProduit>> quantite_produits;
  int reduction;
  std::unique_ptr<PointDeVente> point_de_vente;
  std::string client;

  Facture(int id,
          std::vector<std::unique_ptr<QuantiteProduit>> quantite_produits,
          int reduction, std::unique_ptr<PointDeVente> point_de_vente,
          std::string client)
      : id(id), quantite_produits(std::move(quantite_produits)),
        reduction(reduction), point_de_vente(std::move(point_de_vente)),
        client(std::move(client)) {}
  Facture(const json &data)
      : Facture(data.at("id"),
                make_rels<QuantiteProduit>(data.at("quantite_produits")),
                data.at("reduction"),
                make_rel<PointDeVente>(data.at("point_de_vente")),
                data.at("client")) {}
  Facture(int id) : Facture(fetch("facture", id)) {}

  void print(std::ostream &os, int indent = 0) const {
    os << pad(indent) << "Facture #" << id << " client " << client
       << " (reduction " << reduction << "%)\n";
    for (const auto &qp : quantite_produits)
      qp->print(os, indent + 2);
    point_de_vente->print(os, indent + 2);
  }
};

// ------------------------------------------------------------------- main

template <class T> static void show(int id) { T(id).print(std::cout); }

// Usage : low_level [modele] [id]     (défaut : Localisation 1)
int main(int argc, char **argv) {
  const std::string modele = argc > 1 ? argv[1] : "lieu";
  try {
    const int id = argc > 2 ? std::stoi(argv[2]) : 1;
    if (modele == "lieu")
      show<Localisation>(id);
    else if (modele == "pays")
      show<Pays>(id);
    else if (modele == "ville")
      show<Ville>(id);
    else if (modele == "machine")
      show<Machine>(id);
    else if (modele == "quantitemachine")
      show<QuantiteMachine>(id);
    else if (modele == "transport")
      show<Transport>(id);
    else if (modele == "operation")
      show<Operation>(id);
    else if (modele == "produit")
      show<Produit>(id);
    else if (modele == "prixproduit")
      show<PrixProduit>(id);
    else if (modele == "fournisseur")
      show<Fournisseur>(id);
    else if (modele == "quantiteproduit")
      show<QuantiteProduit>(id);
    else if (modele == "stock")
      show<Stock>(id);
    else if (modele == "pointdevente")
      show<PointDeVente>(id);
    else if (modele == "facture")
      show<Facture>(id);
    else {
      std::cerr << "modele inconnu : " << modele << "\n";
      return 2;
    }
  } catch (const std::exception &e) {
    std::cerr << "erreur : " << e.what() << "\n";
    return 1;
  }
  return 0;
}
