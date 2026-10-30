import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Database:
    def __init__(self, db_name="erp.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # INITIALISATION + MIGRATION
    # ------------------------------------------------------------------
    @staticmethod
    def _ajouter_colonne_si_absente(conn, table, colonne, definition):
        """Ajoute une colonne à une table existante sans perdre les données."""
        colonnes = [row['name'] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if colonne not in colonnes:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {definition}")

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS utilisateurs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'admin'
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    devise TEXT DEFAULT 'Ar',
                    FOREIGN KEY (user_id) REFERENCES utilisateurs (id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS parametres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom_entreprise TEXT DEFAULT 'Mini-ERP Pro',
                    devise_defaut TEXT DEFAULT 'Ar',
                    tva REAL DEFAULT 20.0,
                    couleur_accent TEXT DEFAULT '#8B5CF6',
                    taux_ar REAL DEFAULT 5021.0,
                    logo TEXT
                )
            ''')
            # Migration : anciennes bases créées sans taux_ar / logo
            self._ajouter_colonne_si_absente(conn, 'parametres', 'taux_ar', 'REAL DEFAULT 5021.0')
            self._ajouter_colonne_si_absente(conn, 'parametres', 'logo', 'TEXT')
            conn.execute("UPDATE parametres SET taux_ar = 5021.0 WHERE taux_ar IS NULL")

            conn.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    email TEXT,
                    telephone TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS produits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prix REAL NOT NULL,
                    stock INTEGER NOT NULL,
                    seuil_alerte INTEGER DEFAULT 5
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ventes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total REAL NOT NULL,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS lignes_vente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vente_id INTEGER,
                    produit_id INTEGER,
                    quantite INTEGER NOT NULL,
                    prix_unitaire REAL NOT NULL,
                    sous_total REAL NOT NULL,
                    FOREIGN KEY (vente_id) REFERENCES ventes (id),
                    FOREIGN KEY (produit_id) REFERENCES produits (id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS depenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    categorie TEXT NOT NULL,
                    montant REAL NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            if not conn.execute("SELECT 1 FROM utilisateurs WHERE username = ?", ('admin',)).fetchone():
                conn.execute(
                    "INSERT INTO utilisateurs (username, password, role) VALUES (?, ?, 'admin')",
                    ('admin', generate_password_hash('admin123'))
                )
            if not conn.execute("SELECT 1 FROM parametres LIMIT 1").fetchone():
                conn.execute('''
                    INSERT INTO parametres (nom_entreprise, devise_defaut, tva, couleur_accent, taux_ar)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('Mini-ERP Pro', 'Ar', 20.0, '#8B5CF6', 5021.0))
            conn.commit()

    # ------------------------------------------------------------------
    # UTILISATEURS / PRÉFÉRENCES
    # ------------------------------------------------------------------
    def get_devise(self, user_id):
        with self.get_connection() as conn:
            pref = conn.execute("SELECT devise FROM preferences WHERE user_id = ?", (user_id,)).fetchone()
            return pref['devise'] if pref else 'Ar'

    def set_devise(self, user_id, devise):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO preferences (user_id, devise) VALUES (?, ?)", (user_id, devise))
            conn.commit()

    def verifier_utilisateur(self, username, password):
        with self.get_connection() as conn:
            user = conn.execute("SELECT * FROM utilisateurs WHERE username = ?", (username,)).fetchone()
            if user and check_password_hash(user['password'], password):
                return user
        return None

    def ajouter_utilisateur(self, username, password, role='vendeur'):
        hashed_pwd = generate_password_hash(password)
        with self.get_connection() as conn:
            try:
                conn.execute("INSERT INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",
                             (username, hashed_pwd, role))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    # ------------------------------------------------------------------
    # CLIENTS
    # ------------------------------------------------------------------
    def recuperer_clients(self, recherche=""):
        with self.get_connection() as conn:
            if recherche:
                return conn.execute("SELECT * FROM clients WHERE nom LIKE ? OR email LIKE ? ORDER BY nom",
                                    (f'%{recherche}%', f'%{recherche}%')).fetchall()
            return conn.execute("SELECT * FROM clients ORDER BY nom").fetchall()

    def ajouter_client(self, nom, email, telephone):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO clients (nom, email, telephone) VALUES (?, ?, ?)", (nom, email, telephone))
            conn.commit()

    def modifier_client(self, client_id, nom, email, telephone):
        with self.get_connection() as conn:
            conn.execute("UPDATE clients SET nom = ?, email = ?, telephone = ? WHERE id = ?",
                         (nom, email, telephone, client_id))
            conn.commit()

    def supprimer_client(self, client_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()

    # ------------------------------------------------------------------
    # PRODUITS
    # ------------------------------------------------------------------
    def recuperer_produits(self, recherche=""):
        with self.get_connection() as conn:
            if recherche:
                return conn.execute("SELECT * FROM produits WHERE nom LIKE ? ORDER BY nom",
                                    (f'%{recherche}%',)).fetchall()
            return conn.execute("SELECT * FROM produits ORDER BY nom").fetchall()

    def ajouter_produit(self, nom, prix, stock, seuil_alerte):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO produits (nom, prix, stock, seuil_alerte) VALUES (?, ?, ?, ?)",
                         (nom, prix, stock, seuil_alerte))
            conn.commit()

    def modifier_produit(self, produit_id, nom, prix, stock, seuil_alerte):
        with self.get_connection() as conn:
            conn.execute("UPDATE produits SET nom = ?, prix = ?, stock = ?, seuil_alerte = ? WHERE id = ?",
                         (nom, prix, stock, seuil_alerte, produit_id))
            conn.commit()

    def supprimer_produit(self, produit_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM produits WHERE id = ?", (produit_id,))
            conn.commit()

    def recuperer_produits_a_reapprovisionner(self):
        """Produits en rupture ou sous le seuil, les plus urgents d'abord."""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM produits WHERE stock <= seuil_alerte ORDER BY stock ASC, nom ASC"
            ).fetchall()

    # ------------------------------------------------------------------
    # VENTES
    # ------------------------------------------------------------------
    def recuperer_ventes(self, date_filtre=""):
        """Liste des ventes avec le nom du client (filtre optionnel sur la date)."""
        sql = '''
            SELECT v.*, c.nom AS client_nom
            FROM ventes v LEFT JOIN clients c ON v.client_id = c.id
        '''
        params = ()
        if date_filtre:
            sql += " WHERE v.date LIKE ?"
            params = (f"{date_filtre}%",)
        sql += " ORDER BY v.date DESC"
        with self.get_connection() as conn:
            return conn.execute(sql, params).fetchall()

    def recuperer_ventes_recentes(self, limite=5):
        with self.get_connection() as conn:
            return conn.execute(
                '''SELECT v.*, c.nom AS client_nom
                   FROM ventes v LEFT JOIN clients c ON v.client_id = c.id
                   ORDER BY v.date DESC LIMIT ?''', (int(limite),)
            ).fetchall()

    def creer_vente(self, client_id, lignes):
        """Crée la vente, ses lignes et baisse le stock dans UNE transaction.
        Si un stock est insuffisant, tout est annulé."""
        with self.get_connection() as conn:
            total_vente = sum(l['quantite'] * l['prix_unitaire'] for l in lignes)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ventes (client_id, total) VALUES (?, ?)", (client_id, total_vente))
            vente_id = cursor.lastrowid
            for ligne in lignes:
                sous_total = ligne['quantite'] * ligne['prix_unitaire']
                cursor.execute(
                    "INSERT INTO lignes_vente (vente_id, produit_id, quantite, prix_unitaire, sous_total) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (vente_id, ligne['produit_id'], ligne['quantite'], ligne['prix_unitaire'], sous_total))
                cursor.execute("UPDATE produits SET stock = stock - ? WHERE id = ? AND stock >= ?",
                               (ligne['quantite'], ligne['produit_id'], ligne['quantite']))
                if cursor.rowcount == 0:
                    conn.rollback()
                    raise ValueError("Stock insuffisant pour finaliser la vente.")
            conn.commit()
            return vente_id

    # ------------------------------------------------------------------
    # DÉPENSES
    # ------------------------------------------------------------------
    def recuperer_depenses(self):
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM depenses ORDER BY date DESC").fetchall()

    def ajouter_depense(self, description, categorie, montant):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO depenses (description, categorie, montant) VALUES (?, ?, ?)",
                         (description, categorie, montant))
            conn.commit()

    def supprimer_depense(self, depense_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM depenses WHERE id = ?", (depense_id,))
            conn.commit()

    def recuperer_depenses_par_categorie(self):
        """Regroupe 'charge', 'Charge ' et 'CHARGE' dans la même catégorie."""
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT LOWER(TRIM(categorie)) AS categorie, SUM(montant) AS total
                FROM depenses
                GROUP BY LOWER(TRIM(categorie))
                ORDER BY total DESC
            ''').fetchall()

    # ------------------------------------------------------------------
    # RAPPORT MENSUEL (6 derniers mois RÉELS, les mois vides valent 0)
    # ------------------------------------------------------------------
    @staticmethod
    def _derniers_mois(nb_mois):
        maintenant = datetime.now()
        annee, mois = maintenant.year, maintenant.month
        liste = []
        for _ in range(nb_mois):
            liste.append(f"{annee:04d}-{mois:02d}")
            mois -= 1
            if mois == 0:
                mois, annee = 12, annee - 1
        return list(reversed(liste))  # ordre chronologique

    def recuperer_rapport_mensuel(self, nb_mois=6):
        mois_liste = self._derniers_mois(nb_mois)
        data = {m: {'mois': m, 'ca': 0.0, 'nb_ventes': 0, 'depenses': 0.0, 'benefice': 0.0} for m in mois_liste}

        with self.get_connection() as conn:
            for v in conn.execute('''
                SELECT strftime('%Y-%m', date) AS mois, SUM(total) AS ca, COUNT(*) AS nb_ventes
                FROM ventes GROUP BY mois
            ''').fetchall():
                if v['mois'] in data:
                    data[v['mois']]['ca'] = v['ca'] or 0.0
                    data[v['mois']]['nb_ventes'] = v['nb_ventes']
            for d in conn.execute('''
                SELECT strftime('%Y-%m', date) AS mois, SUM(montant) AS depenses
                FROM depenses GROUP BY mois
            ''').fetchall():
                if d['mois'] in data:
                    data[d['mois']]['depenses'] = d['depenses'] or 0.0

        for m in data.values():
            m['benefice'] = m['ca'] - m['depenses']
        return [data[m] for m in mois_liste]