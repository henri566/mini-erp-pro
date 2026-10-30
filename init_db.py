import sqlite3
import os

DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Table Paramètres de l'entreprise
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parametres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_entreprise TEXT DEFAULT 'Mini-ERP Pro',
            devise_defaut TEXT DEFAULT 'Ar',
            tva REAL DEFAULT 20.0,
            couleur_accent TEXT DEFAULT '#8B5CF6'
        )
    ''')

    # Vérifier si la table parametres contient au moins une ligne, sinon l'insérer
    cursor.execute("SELECT COUNT(*) FROM parametres")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO parametres (nom_entreprise, devise_defaut, tva, couleur_accent)
            VALUES (?, ?, ?, ?)
        ''', ('Mini-ERP Pro Madagascar', 'Ar', 20.0, '#8B5CF6'))

    # 2. Table Utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        )
    ''')

    # 3. Table Clients
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT,
            telephone TEXT
        )
    ''')

    # 4. Table Produits & Stocks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prix REAL NOT NULL,
            stock INTEGER NOT NULL,
            seuil_alerte INTEGER DEFAULT 5
        )
    ''')

    # 5. Table Ventes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            date TEXT NOT NULL,
            total REAL NOT NULL,
            statut TEXT DEFAULT 'Payé',
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')

    # 6. Table Lignes de Vente
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lignes_vente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vente_id INTEGER,
            produit_id INTEGER,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            sous_total REAL NOT NULL,
            FOREIGN KEY(vente_id) REFERENCES ventes(id),
            FOREIGN KEY(produit_id) REFERENCES produits(id)
        )
    ''')

    # 7. Table Dépenses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            categorie TEXT NOT NULL,
            date TEXT NOT NULL,
            montant REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Base de données initialisée et table 'parametres' créée avec succès !")

if __name__ == '__main__':
    init_db()