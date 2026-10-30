"""
seed.py : remplit erp.db avec des données de démonstration réalistes.

UTILISATION (depuis le dossier du projet, avec le venv activé) :
    python seed.py

ATTENTION : efface les clients, produits, ventes et dépenses existants.
Les utilisateurs (admin) et les paramètres sont conservés.
Une copie de sécurité est créée : erp.db.bak

Les montants sont stockés en EUROS (comme le reste de l'application) et
calculés à partir de prix en ARIARY : ils s'affichent donc pile en Ariary.
"""
import os
import random
import shutil
import sys
from datetime import datetime, timedelta

from services.database import Database

DB_NAME = "erp.db"
random.seed(42)  # mêmes données à chaque exécution = captures reproductibles

# --------------------------------------------------------------------
# DONNÉES
# --------------------------------------------------------------------
CLIENTS = [
    ("Rakoto Andriamihaja", "rakoto.andriamihaja@gmail.com", "+261321234567"),
    ("Rasoa Randrianarisoa", "rasoa.randria@gmail.com", "+261331234568"),
    ("Hery Rabemananjara", "hery.rabe@yahoo.fr", "+261341234569"),
    ("Lalaina Ravelojaona", "lalaina.ravelo@gmail.com", "+261381234570"),
    ("Tiana Rakotomalala", "tiana.rakoto@outlook.com", "+261321234571"),
    ("Fanja Razafindrakoto", "fanja.razafi@gmail.com", "+261341234572"),
    ("Miora Andrianantenaina", "miora.andria@gmail.com", "+261331234573"),
    ("Njaka Rasolofoniaina", "njaka.rasolo@yahoo.fr", "+261381234574"),
    ("Soa Ravaoarisoa", "soa.ravaoarisoa@gmail.com", "+261321234575"),
    ("Boutique Tsiry", "contact@boutiquetsiry.mg", "+261341234576"),
]

# (nom, prix en Ariary, stock FINAL souhaité, seuil d'alerte)
# Stock final : 0 = Rupture, <= seuil = Stock bas, sinon OK
PRODUITS = [
    ("Riz local 5 kg", 14000, 85, 20),
    ("Huile de cuisine 1 L", 7500, 42, 15),
    ("Sucre 1 kg", 4200, 60, 20),
    ("Lait en poudre 400 g", 12500, 6, 10),      # stock bas
    ("Café moulu 250 g", 6800, 33, 10),
    ("Eau minérale 1,5 L", 1800, 150, 40),
    ("Savon de Marseille", 2500, 0, 10),          # rupture
    ("Lessive 1 kg", 9000, 28, 10),
    ("Cahier 96 pages", 2200, 120, 30),
    ("Stylos à bille (boîte de 50)", 25000, 9, 5),
    ("Ampoule LED 9 W", 6500, 31, 10),
    ("Chargeur USB", 15000, 5, 8),                # stock bas
    ("Écouteurs filaires", 18000, 19, 5),
    ("Clé USB 32 Go", 28000, 14, 5),
    ("Ventilateur de table", 85000, 3, 5),        # stock bas
]

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]

# (catégorie, description, montant mensuel en Ariary, variation en %, jour du mois)
DEPENSES_MENSUELLES = [
    ("Loyer", "Loyer boutique", 300000, 0, 1),
    ("Salaires", "Salaires du personnel", 450000, 0, 5),
    ("Électricité", "Facture JIRAMA", 85000, 12, 10),
    ("Transport", "Carburant et livraisons", 70000, 25, 12),
    ("Marketing", "Publicité et réseaux sociaux", 55000, 30, 15),
    ("Fournitures", "Sacs, étiquettes, petit matériel", 40000, 30, 18),
    ("Internet", "Abonnement internet", 45000, 0, 20),
]

VENTES_PAR_MOIS = [26, 29, 32, 35, 38, 42]  # croissance régulière sur 6 mois


# --------------------------------------------------------------------
def mois_precedent(annee, mois, n):
    """Renvoie (annee, mois) situé n mois avant."""
    total = annee * 12 + (mois - 1) - n
    return total // 12, total % 12 + 1


def jours_dans_mois(annee, mois):
    if mois == 12:
        return 31
    return (datetime(annee, mois + 1, 1) - datetime(annee, mois, 1)).days


def main():
    if "--yes" not in sys.argv:
        print("Ce script va EFFACER les clients, produits, ventes et dépenses de", DB_NAME)
        if input("Taper OUI pour continuer : ").strip().upper() != "OUI":
            print("Annulé.")
            return

    db = Database(DB_NAME)  # crée / migre les tables si besoin
    if os.path.exists(DB_NAME):
        shutil.copy(DB_NAME, DB_NAME + ".bak")
        print(f"Sauvegarde créée : {DB_NAME}.bak")

    conn = db.get_connection()
    taux = conn.execute("SELECT taux_ar FROM parametres LIMIT 1").fetchone()[0] or 5021.0

    for table in ("lignes_vente", "ventes", "depenses", "produits", "clients"):
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN "
                 "('lignes_vente','ventes','depenses','produits','clients')")

    # Clients
    for nom, email, tel in CLIENTS:
        conn.execute("INSERT INTO clients (nom, email, telephone) VALUES (?, ?, ?)", (nom, email, tel))
    nb_clients = len(CLIENTS)

    # Prix en euros (base de stockage) calculés depuis les prix en Ariary
    prix_eur = {i + 1: p[1] / taux for i, p in enumerate(PRODUITS)}
    vendus = {i + 1: 0 for i in range(len(PRODUITS))}

    # Ventes : générées d'abord, pour calculer ensuite le stock initial
    maintenant = datetime.now()
    ventes = []
    for decalage in range(5, -1, -1):  # du plus ancien au mois en cours
        annee, mois = mois_precedent(maintenant.year, maintenant.month, decalage)
        nb_ventes = VENTES_PAR_MOIS[5 - decalage]
        dernier_jour = jours_dans_mois(annee, mois)
        if decalage == 0:  # mois en cours : seulement jusqu'à aujourd'hui
            dernier_jour = maintenant.day
            nb_ventes = max(6, round(nb_ventes * maintenant.day / jours_dans_mois(annee, mois)))

        for _ in range(nb_ventes):
            jour = random.randint(1, dernier_jour)
            date = datetime(annee, mois, jour, random.randint(8, 18), random.randint(0, 59), random.randint(0, 59))
            if date > maintenant:
                date = maintenant - timedelta(minutes=random.randint(5, 600))
            client_id = None if random.random() < 0.12 else random.randint(1, nb_clients)

            lignes = []
            for pid in random.sample(range(1, len(PRODUITS) + 1), random.randint(1, 4)):
                prix_ar = PRODUITS[pid - 1][1]
                quantite = random.randint(1, 8) if prix_ar < 10000 else random.randint(1, 3)
                lignes.append((pid, quantite))
                vendus[pid] += quantite
            ventes.append((date, client_id, lignes))

    # Produits : stock initial = stock final voulu + quantités vendues
    for i, (nom, prix_ar, stock_final, seuil) in enumerate(PRODUITS, start=1):
        conn.execute(
            "INSERT INTO produits (id, nom, prix, stock, seuil_alerte) VALUES (?, ?, ?, ?, ?)",
            (i, nom, prix_eur[i], stock_final + vendus[i], seuil))

    # Insertion des ventes (ordre chronologique) puis du stock réel
    ventes.sort(key=lambda v: v[0])
    for date, client_id, lignes in ventes:
        total = sum(q * prix_eur[pid] for pid, q in lignes)
        cur = conn.execute("INSERT INTO ventes (client_id, date, total) VALUES (?, ?, ?)",
                           (client_id, date.strftime("%Y-%m-%d %H:%M:%S"), total))
        for pid, q in lignes:
            conn.execute(
                "INSERT INTO lignes_vente (vente_id, produit_id, quantite, prix_unitaire, sous_total) "
                "VALUES (?, ?, ?, ?, ?)", (cur.lastrowid, pid, q, prix_eur[pid], q * prix_eur[pid]))
            conn.execute("UPDATE produits SET stock = stock - ? WHERE id = ?", (q, pid))

    # CA par mois (en euros), pour calculer les achats de marchandises
    ca_par_mois = {}
    for date, _client, lignes in ventes:
        cle = (date.year, date.month)
        ca_par_mois[cle] = ca_par_mois.get(cle, 0) + sum(q * prix_eur[pid] for pid, q in lignes)

    # Dépenses mensuelles (6 mois)
    nb_depenses = 0
    for decalage in range(5, -1, -1):
        annee, mois = mois_precedent(maintenant.year, maintenant.month, decalage)

        # Achats de marchandises : environ 35 % du CA du mois (plus réaliste qu'une marge de 70 %)
        date_achat = datetime(annee, mois, 3, 10, 0, 0)
        if date_achat <= maintenant and (annee, mois) in ca_par_mois:
            montant_eur = ca_par_mois[(annee, mois)] * random.uniform(0.33, 0.38)
            conn.execute(
                "INSERT INTO depenses (description, categorie, montant, date) VALUES (?, ?, ?, ?)",
                (f"Réapprovisionnement stock - {MOIS_FR[mois - 1]}", "Achats", montant_eur,
                 date_achat.strftime("%Y-%m-%d %H:%M:%S")))
            nb_depenses += 1
        for categorie, desc, montant_ar, variation, jour in DEPENSES_MENSUELLES:
            date = datetime(annee, mois, jour, 9, 0, 0)
            if date > maintenant:
                continue
            facteur = 1 + random.uniform(-variation, variation) / 100
            montant_ar = round(montant_ar * facteur, -2)
            conn.execute(
                "INSERT INTO depenses (description, categorie, montant, date) VALUES (?, ?, ?, ?)",
                (f"{desc} - {MOIS_FR[mois - 1]}", categorie, montant_ar / taux, date.strftime("%Y-%m-%d %H:%M:%S")))
            nb_depenses += 1

    conn.commit()

    ca = conn.execute("SELECT SUM(total) FROM ventes").fetchone()[0] * taux
    dep = conn.execute("SELECT SUM(montant) FROM depenses").fetchone()[0] * taux
    conn.close()

    print("\nDonnées de démo créées avec succès :")
    print(f"  {nb_clients} clients, {len(PRODUITS)} produits, {len(ventes)} ventes, {nb_depenses} dépenses")
    print(f"  CA total       : {ca:,.0f} Ar".replace(",", " "))
    print(f"  Dépenses       : {dep:,.0f} Ar".replace(",", " "))
    print(f"  Bénéfice net   : {ca - dep:,.0f} Ar".replace(",", " "))
    print("\nLance maintenant : python app.py")


if __name__ == "__main__":
    main()