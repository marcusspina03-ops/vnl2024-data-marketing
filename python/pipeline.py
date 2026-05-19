# =============================================================================
# VNL 2024 - PIPELINE PYTHON
# Volleyball Nations League | MSc2 Manager Data Marketing
# =============================================================================
#
# Ce script réalise un pipeline complet en 4 étapes :
#   1. Connexion à la base MySQL via un fichier .env (sécurisé)
#   2. Chargement des données joueurs et stats avec Pandas
#   3. Enrichissement des équipes via l'API REST Countries
#   4. Calcul du Player Performance Score (PPS) par joueur
#   5. Écriture des résultats enrichis dans une nouvelle table MySQL
#
# Prérequis :
#   - MySQL installé avec la base vnl2024 (fichier init_db.sql exécuté)
#   - Fichier .env avec DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
#   - pip install mysql-connector-python pandas requests python-dotenv
#
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

import os           # Pour lire les variables d'environnement
import time         # Pour faire une pause entre les appels API
import requests     # Pour appeler l'API REST Countries
import pandas as pd # Pour manipuler les données en tableaux
import mysql.connector
from dotenv import load_dotenv  # Pour lire le fichier .env


# =============================================================================
# 1. CONNEXION À LA BASE DE DONNÉES
# =============================================================================
#
# On ne met jamais le mot de passe directement dans le code.
# load_dotenv() lit le fichier .env et charge les variables dans
# l'environnement. os.getenv() les récupère ensuite.
#
# Avantage : le fichier .env est dans .gitignore, donc le mot de passe
# ne sera jamais visible sur GitHub.
#
# =============================================================================

load_dotenv()

def get_connection():
    """
    Crée et retourne une connexion MySQL.
    Les identifiants sont lus depuis le fichier .env.
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# Test rapide de la connexion au démarrage
conn_test = get_connection()
cursor_test = conn_test.cursor()
cursor_test.execute("SELECT COUNT(*) FROM players")
nb_players = cursor_test.fetchone()[0]
print(f"Connexion OK — {nb_players} joueurs dans la base")
cursor_test.close()
conn_test.close()


# =============================================================================
# 2. CHARGEMENT DES DONNÉES DEPUIS MYSQL
# =============================================================================
#
# pd.read_sql() exécute une requête SQL et retourne directement
# un DataFrame pandas. C'est plus propre que fetchall() + pd.DataFrame().
#
# On charge deux tables :
#   - players : infos de chaque joueur (nom, équipe, position...)
#   - player_stats : stats par catégorie (attaque, service, block, score)
#
# =============================================================================

def load_data():
    """
    Charge les données joueurs et stats depuis MySQL.
    Retourne deux DataFrames : players_df et stats_df.
    """
    conn = get_connection()

    # Jointure players + teams pour avoir le nom du pays et le continent
    players_df = pd.read_sql("""
        SELECT p.player_id,
               p.name,
               p.position,
               p.height,
               p.birth_year,
               t.code    AS team_code,
               t.country,
               t.continent
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
    """, conn)

    # Toutes les stats par joueur et par catégorie
    stats_df = pd.read_sql("""
        SELECT ps.player_id,
               ps.stat_category,
               ps.total_points,
               ps.error_count,
               ps.attempts,
               ps.match_avg,
               ps.efficiency_pct,
               ps.total_actions
        FROM player_stats ps
    """, conn)

    # Toujours fermer la connexion après utilisation
    conn.close()

    print(f"✅ {len(players_df)} joueurs chargés")
    print(f"✅ {len(stats_df)} lignes de stats chargées")

    return players_df, stats_df


# =============================================================================
# 3. ENRICHISSEMENT VIA L'API REST COUNTRIES
# =============================================================================
#
# L'API REST Countries est gratuite et sans clé.
# Elle prend un code ISO de pays et retourne des infos : population,
# nom officiel, drapeau, région, etc.
#
# URL utilisée : https://restcountries.com/v3.1/alpha/{code_iso}
#
# Les codes VNL (ex: FRA, IRI) ne sont pas tous des codes ISO standard,
# donc on utilise un dictionnaire de correspondance COUNTRY_CODES.
#
# time.sleep(1) : on attend 1 seconde entre chaque appel pour ne pas
# surcharger le serveur. Bonne pratique avec toute API publique.
#
# =============================================================================

# Correspondance entre codes VNL et codes ISO pour l'API
COUNTRY_CODES = {
    'ARG': 'arg', 'BRA': 'bra', 'BUL': 'bgr', 'CAN': 'can',
    'CUB': 'cub', 'FRA': 'fra', 'GER': 'deu', 'IRI': 'irn',
    'ITA': 'ita', 'JPN': 'jpn', 'NED': 'nld', 'POL': 'pol',
    'SLO': 'svn', 'SRB': 'srb', 'TUR': 'tur', 'USA': 'usa'
}

def enrich_teams_with_api(team_codes):
    """
    Appelle l'API REST Countries pour chaque équipe.
    Récupère la population et l'URL du drapeau.

    Paramètres :
        team_codes (list) : liste des codes équipes VNL (ex: ['FRA', 'ITA'])

    Retourne :
        dict : {code_vnl: {'population': int, 'flag_url': str}}
    """
    enriched = {}

    print(f"\nEnrichissement de {len(team_codes)} équipes via REST Countries API...")

    for vnl_code in team_codes:

        # Récupère le code ISO correspondant au code VNL
        iso_code = COUNTRY_CODES.get(vnl_code)
        if not iso_code:
            print(f"  ⚠️  {vnl_code} : pas de code ISO trouvé, ignoré")
            continue

        url = f"https://restcountries.com/v3.1/alpha/{iso_code}"

        try:
            # Appel HTTP à l'API avec timeout de 5 secondes
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                # response.json() transforme la réponse en dictionnaire Python
                data = response.json()[0]

                enriched[vnl_code] = {
                    'population': data.get('population', None),
                    'flag_url':   data.get('flags', {}).get('png', None)
                }
                print(f"  ✅ {vnl_code} : population = {enriched[vnl_code]['population']:,}")

            else:
                print(f"  ⚠️  {vnl_code} : statut HTTP {response.status_code}")

        except Exception as e:
            # Si l'API ne répond pas, on continue sans bloquer le script
            print(f"  ❌ {vnl_code} : erreur — {e}")

        # Pause d'1 seconde entre chaque appel pour respecter l'API
        time.sleep(1)

    print(f"API terminée : {len(enriched)} équipes enrichies")
    return enriched


def update_teams_in_db(enriched_data):
    """
    Met à jour la table teams avec la population et l'URL du drapeau
    récupérées depuis l'API.

    Paramètres :
        enriched_data (dict) : résultat de enrich_teams_with_api()
    """
    conn = get_connection()
    cursor = conn.cursor()

    for vnl_code, info in enriched_data.items():
        # %s sont des placeholders : MySQL remplace avec les vraies valeurs
        # C'est plus sûr que de concaténer des strings (protection injections SQL)
        cursor.execute("""
            UPDATE teams
            SET population = %s,
                flag_url   = %s
            WHERE code = %s
        """, (info['population'], info['flag_url'], vnl_code))

    # commit() valide les modifications — sans ça, rien n'est sauvegardé
    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Table teams mise à jour dans MySQL")


# =============================================================================
# 4. ALGORITHME : PLAYER PERFORMANCE SCORE (PPS)
# =============================================================================
#
# Le PPS est notre algorithme de scoring, inspiré de la logique RFM.
# Comme le RFM score les clients sur 3 dimensions (Récence, Fréquence,
# Montant), le PPS score les joueurs sur 3 dimensions sportives :
#
#   - Score Attaque  (40%) : points marqués + efficacité en attaque
#   - Score Service  (30%) : points au service + moyenne par match
#   - Score Block    (30%) : points au block + moyenne par match
#
# Chaque dimension est normalisée entre 0 et 10 pour comparer
# des métriques qui n'ont pas les mêmes unités.
#
# Le PPS final est une moyenne pondérée → score entre 0 et 10.
#
# Segmentation finale (comme les segments RFM) :
#   Elite     : PPS >= 7   → joueurs à recruter en priorité
#   Confirmed : PPS >= 4   → joueurs solides et fiables
#   Average   : PPS >= 2   → joueurs dans la moyenne
#   Low       : PPS < 2    → joueurs peu performants sur la compétition
#
# =============================================================================

def normalize(series):
    """
    Normalise une série de valeurs entre 0 et 10.
    Formule : (valeur - min) / (max - min) * 10
    Permet de comparer des métriques d'unités différentes.
    """
    min_val = series.min()
    max_val = series.max()
    # Si toutes les valeurs sont identiques, on retourne 0 pour tout
    if max_val == min_val:
        return series * 0
    return (series - min_val) / (max_val - min_val) * 10


def compute_pps(players_df, stats_df):
    """
    Calcule le Player Performance Score (PPS) pour chaque joueur.

    Paramètres :
        players_df (DataFrame) : données des joueurs
        stats_df   (DataFrame) : stats par catégorie (attack, serve, block)

    Retourne :
        DataFrame avec player_id, name, team_code, position, pps, segment
    """

    # --- Séparation des stats par catégorie ---
    # On filtre les lignes selon la catégorie, puis on renomme les colonnes
    # pour éviter les conflits lors des fusions (merge)

    attack = stats_df[stats_df['stat_category'] == 'attack'][
        ['player_id', 'total_points', 'efficiency_pct', 'match_avg']
    ].copy()
    attack.columns = ['player_id', 'atk_pts', 'atk_eff', 'atk_avg']

    serve = stats_df[stats_df['stat_category'] == 'serve'][
        ['player_id', 'total_points', 'match_avg']
    ].copy()
    serve.columns = ['player_id', 'srv_pts', 'srv_avg']

    block = stats_df[stats_df['stat_category'] == 'block'][
        ['player_id', 'total_points', 'match_avg']
    ].copy()
    block.columns = ['player_id', 'blk_pts', 'blk_avg']

    # --- Fusion de tout sur le DataFrame joueurs ---
    # how='left' : on garde tous les joueurs, même ceux sans stats dans une catégorie
    # fillna(0) : les valeurs manquantes deviennent 0

    df = players_df[['player_id', 'name', 'team_code', 'position', 'height', 'birth_year']].copy()
    df = df.merge(attack, on='player_id', how='left')
    df = df.merge(serve,  on='player_id', how='left')
    df = df.merge(block,  on='player_id', how='left')
    df = df.fillna(0)

    # --- Calcul des scores normalisés par dimension ---
    # On combine les métriques avec des poids avant de normaliser

    df['score_attack'] = normalize(df['atk_pts'] * 0.6 + df['atk_eff'] * 0.4)
    df['score_serve']  = normalize(df['srv_pts'] * 0.7 + df['srv_avg'] * 0.3)
    df['score_block']  = normalize(df['blk_pts'] * 0.7 + df['blk_avg'] * 0.3)

    # --- PPS final : moyenne pondérée des 3 dimensions ---
    df['pps'] = (
        df['score_attack'] * 0.40 +
        df['score_serve']  * 0.30 +
        df['score_block']  * 0.30
    ).round(2)

    # --- Segmentation : on classe chaque joueur selon son PPS ---
    def segment(score):
        if score >= 7:   return 'Elite'
        elif score >= 4: return 'Confirmed'
        elif score >= 2: return 'Average'
        else:            return 'Low'

    df['segment'] = df['pps'].apply(segment)

    # Affichage du résumé par segment
    print(f"\n✅ PPS calculé pour {len(df)} joueurs")
    print("\n--- Répartition par segment ---")
    print(df['segment'].value_counts().to_string())
    print(f"\nTop 5 joueurs :")
    print(df.nlargest(5, 'pps')[['name', 'team_code', 'pps', 'segment']].to_string(index=False))

    return df


# =============================================================================
# 5. ÉCRITURE DES RÉSULTATS DANS MYSQL
# =============================================================================
#
# On crée une nouvelle table player_scores qui stocke les résultats
# de l'algorithme PPS. Cette table sera utilisée par le dashboard.
#
# CREATE TABLE IF NOT EXISTS : crée la table seulement si elle n'existe pas.
# DELETE FROM avant l'insert : permet de relancer le pipeline sans doublons.
# executemany() : insère toutes les lignes en une seule opération,
#   plus performant que d'appeler execute() en boucle.
#
# =============================================================================

def write_scores_to_db(scores_df):
    """
    Crée la table player_scores dans MySQL et insère les résultats du PPS.

    Paramètres :
        scores_df (DataFrame) : résultats avec PPS et segments
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Création de la table si elle n'existe pas encore
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_scores (
            score_id     INT PRIMARY KEY AUTO_INCREMENT,
            player_id    INT NOT NULL,
            name         VARCHAR(100),
            team_code    VARCHAR(3),
            position     VARCHAR(5),
            height       INT,
            birth_year   INT,
            score_attack FLOAT,
            score_serve  FLOAT,
            score_block  FLOAT,
            pps          FLOAT,
            segment      VARCHAR(20),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
    """)

    # Suppression des données existantes pour éviter les doublons
    # si on relance le pipeline plusieurs fois
    cursor.execute("DELETE FROM player_scores")

    # Préparation des données à insérer sous forme de liste de tuples
    rows = [
        (
            int(row['player_id']),
            row['name'],
            row['team_code'],
            row['position'],
            int(row['height']),
            int(row['birth_year']),
            float(row['score_attack']),
            float(row['score_serve']),
            float(row['score_block']),
            float(row['pps']),
            row['segment']
        )
        for _, row in scores_df.iterrows()
    ]

    # executemany() insère toutes les lignes en une seule opération
    cursor.executemany("""
        INSERT INTO player_scores
            (player_id, name, team_code, position, height, birth_year,
             score_attack, score_serve, score_block, pps, segment)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)

    # Validation des modifications — obligatoire pour sauvegarder
    conn.commit()

    print(f"\n✅ {len(rows)} joueurs insérés dans la table player_scores")

    # Toujours fermer le cursor et la connexion après utilisation
    cursor.close()
    conn.close()


# =============================================================================
# 6. EXÉCUTION DU PIPELINE
# =============================================================================
#
# Le bloc if __name__ == "__main__" garantit que ce code s'exécute
# seulement quand on lance le fichier directement (python pipeline.py),
# pas quand on l'importe depuis un autre script.
#
# =============================================================================

if __name__ == "__main__":

    print("\n🏐 VNL 2024 — Pipeline Data Marketing")
    print("=" * 45)

    # --- Étape 1 : Chargement des données ---
    print("\n📥 Étape 1 : Chargement des données depuis MySQL...")
    players_df, stats_df = load_data()

    # --- Étape 2 : Enrichissement via API ---
    print("\n🌍 Étape 2 : Enrichissement via REST Countries API...")
    team_codes = players_df['team_code'].unique().tolist()
    enriched   = enrich_teams_with_api(team_codes)
    update_teams_in_db(enriched)

    # --- Étape 3 : Calcul du PPS ---
    print("\n📊 Étape 3 : Calcul du Player Performance Score (PPS)...")
    scores_df = compute_pps(players_df, stats_df)

    # --- Étape 4 : Export dans MySQL ---
    print("\n💾 Étape 4 : Export des résultats dans MySQL...")
    write_scores_to_db(scores_df)

    print("\n" + "=" * 45)
    print("✅ Pipeline terminé avec succès !")
    print("   Table créée dans MySQL : player_scores")
    print("   Lancez maintenant le dashboard : python dashboard/app.py")
    print("=" * 45)