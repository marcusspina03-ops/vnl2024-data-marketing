# =============================================================================
# VNL 2024 - DASHBOARD PLOTLY DASH (VERSION DÉMO PUBLIQUE)
# Volleyball Nations League | MSc2 Manager Data Marketing
# =============================================================================
#
# Version adaptée pour déploiement public sur Plotly Cloud.
# Seule différence avec dashboard/app.py : les données sont lues depuis
# des CSV statiques (générés une fois depuis MySQL) plutôt qu'une connexion
# MySQL en direct, puisque Plotly Cloud héberge l'application mais pas de
# base de données. Layout, callbacks et logique métier sont identiques
# à la version originale — voir dashboard/app.py pour la version complète
# avec pipeline MySQL + API REST Countries.
#
# Lancement local :
#   python dashboard/app_demo.py
#   Puis ouvrir http://127.0.0.1:8050 dans le navigateur
#
# Structure du dashboard :
#   Section 1 : Filtres (équipe, position, PPS minimum)
#   Section 2 : KPIs (meilleur joueur, élites, PPS moyen)
#   Section 3 : Drapeaux des équipes sélectionnées
#   Section 4 : Graphiques (Top 20, segments, performance équipes)
#   Section 5 : Tableau interactif des joueurs avec tri natif
#
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table


# =============================================================================
# 1. CHARGEMENT DES DONNÉES (depuis CSV statiques, pas MySQL)
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_dashboard_data():
    """
    Charge les scores PPS calculés et les joint aux données équipes
    (pays, continent, drapeau). Équivalent statique de la jointure
    player_scores + teams faite en SQL dans la version originale.
    """
    scores = pd.read_csv(os.path.join(BASE_DIR, "player_scores_demo.csv"))
    teams = pd.read_csv(os.path.join(BASE_DIR, "teams_demo.csv"))
    df = scores.merge(
        teams[["code", "country", "continent", "population", "flag_url"]],
        left_on="team_code", right_on="code", how="left"
    ).drop(columns=["code"])
    df["age"] = 2024 - df["birth_year"]
    return df

def load_teams_data():
    """Charge les données équipes avec drapeaux depuis le CSV statique"""
    return pd.read_csv(os.path.join(BASE_DIR, "teams_demo.csv")).sort_values("code")

# Chargement au démarrage — une seule fois
df       = load_dashboard_data()
teams_df = load_teams_data()


# =============================================================================
# 2. CONFIGURATION DES FILTRES ET COULEURS
# =============================================================================

# Options du dropdown équipe : label lisible + valeur = code
team_options = [{'label': '🌍 Toutes les équipes', 'value': 'ALL'}] + [
    {'label': f"{row['code']} — {row['country']}", 'value': row['code']}
    for _, row in teams_df.iterrows()
]

# Options du dropdown position
position_options = [{'label': '🏃 Toutes les positions', 'value': 'ALL'}] + [
    {'label': pos, 'value': pos}
    for pos in sorted(df['position'].unique())
]

# Libellés complets des positions pour l'affichage dans les graphiques
position_labels = {
    'OH': 'Outside Hitter',
    'MB': 'Middle Blocker',
    'S':  'Setter',
    'O':  'Opposite',
    'L':  'Libero'
}

# Couleurs associées à chaque segment (cohérent avec le pipeline)
SEGMENT_COLORS = {
    'Elite':     '#FFD700',
    'Confirmed': '#4CAF50',
    'Average':   '#2196F3',
    'Low':       '#9E9E9E'
}


# =============================================================================
# 3. INITIALISATION DE L'APPLICATION DASH
# =============================================================================

app = Dash(__name__)
app.title = "VNL 2024 - Player Performance Dashboard"
server = app.server  # requis par la plupart des hébergeurs Dash (WSGI)


# =============================================================================
# 4. LAYOUT DU DASHBOARD
# =============================================================================
#
# Le layout définit la structure visuelle complète du dashboard.
# Il est décrit en Python avec des composants HTML (html.Div, html.H1...)
# et des composants Dash (dcc.Dropdown, dcc.Graph, dash_table.DataTable...).
#
# Les id= sur les composants sont essentiels : ce sont les identifiants
# que les callbacks utilisent pour lire les valeurs (Input) ou
# mettre à jour le contenu (Output).
#
# =============================================================================

app.layout = html.Div(
    style={
        'backgroundColor': '#0a0a1a',
        'minHeight': '100vh',
        'fontFamily': 'Arial, sans-serif',
        'color': 'white'
    },
    children=[

        # --- HEADER ---
        html.Div(
            style={
                'backgroundColor': '#111133',
                'padding': '24px 40px',
                'borderBottom': '2px solid #FFD700'
            },
            children=[
                html.H1(
                    "🏐 VNL 2024 — Player Performance Dashboard",
                    style={'margin': 0, 'fontSize': '26px', 'color': '#FFD700'}
                ),
                html.P(
                    "Volleyball Nations League · Analyse des performances · MSc2 Manager Data Marketing",
                    style={'margin': '6px 0 0 0', 'color': '#aaaacc', 'fontSize': '13px'}
                )
            ]
        ),

        # -----------------------------------------------------------------
        # SECTION 1 : FILTRES
        # -----------------------------------------------------------------
        # Les filtres sont des composants interactifs Dash.
        # Chaque changement déclenche le callback update_dashboard().
        # -----------------------------------------------------------------

        html.Div(
            style={
                'padding': '20px 40px',
                'backgroundColor': '#0d0d2b',
                'display': 'flex',
                'gap': '30px',
                'alignItems': 'flex-end'
            },
            children=[
                html.Div([
                    html.Label("🌍 Équipe",
                               style={'color': '#aaaacc', 'fontSize': '13px',
                                      'marginBottom': '6px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='filter-team',
                        options=team_options,
                        value='ALL',
                        clearable=False,
                        searchable=True,          # Permet de taper pour chercher
                        placeholder='Sélectionner une équipe...',
                        style={'width': '260px','color':'black'}
                    )
                ]),
                html.Div([
                    html.Label("🏃 Position",
                               style={'color': '#aaaacc', 'fontSize': '13px',
                                      'marginBottom': '6px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='filter-position',
                        options=position_options,
                        value='ALL',
                        clearable=False,
                        searchable=False,
                        style={'width': '220px','color':'black'}
                    )
                ]),
                html.Div([
                    html.Label(
                        id='pps-label',
                        children="📊 PPS minimum — 0 / 10",
                        style={'color': '#aaaacc', 'fontSize': '13px',
                               'marginBottom': '6px', 'display': 'block'}),
                    # Slider : l'utilisateur glisse pour définir un seuil de PPS
                    dcc.Slider(
                        id='filter-pps',
                        min=0, max=10, step=0.5, value=0,
                        marks={i: {'label': str(i), 'style': {'color': '#aaaacc'}}
                               for i in range(0, 11, 2)},
                        tooltip=None
                    )
                ], style={'width': '300px', 'paddingTop': '4px'})
            ]
        ),

        # -----------------------------------------------------------------
        # SECTION 2 : KPIs
        # -----------------------------------------------------------------
        # Mis à jour dynamiquement par le callback (id='kpi-section').
        # -----------------------------------------------------------------

        html.Div(
            id='kpi-section',
            style={'padding': '20px 40px', 'display': 'flex', 'gap': '20px'}
        ),

        # -----------------------------------------------------------------
        # SECTION 3 : DRAPEAUX DES ÉQUIPES
        # -----------------------------------------------------------------
        # Affiche les drapeaux des équipes dans la sélection courante,
        # avec le code pays et le PPS moyen en dessous de chaque drapeau.
        # Les URLs des drapeaux viennent de l'API REST Countries (pipeline.py).
        # -----------------------------------------------------------------

        html.Div(
            id='teams-flags-section',
            style={'padding': '0 40px 20px 40px'}
        ),

        # -----------------------------------------------------------------
        # SECTION 4 : GRAPHIQUES
        # -----------------------------------------------------------------

        # Ligne 1 : Top 20 joueurs (large) + Répartition segments (étroit)
        html.Div(
            style={'padding': '0 40px', 'display': 'flex', 'gap': '20px'},
            children=[
                html.Div(
                    dcc.Graph(id='graph-top20'),
                    style={'flex': 2, 'backgroundColor': '#111133',
                           'borderRadius': '10px', 'padding': '10px'}
                ),
                html.Div(
                    dcc.Graph(id='graph-segments'),
                    style={'flex': 1, 'backgroundColor': '#111133',
                           'borderRadius': '10px', 'padding': '10px'}
                ),
            ]
        ),

        # Ligne 2 : Performance moyenne par équipe
        html.Div(
            style={'padding': '20px 40px'},
            children=[
                html.Div(
                    dcc.Graph(id='graph-team-avg'),
                    style={'backgroundColor': '#111133',
                           'borderRadius': '10px', 'padding': '10px'}
                )
            ]
        ),

        # -----------------------------------------------------------------
        # SECTION 5 : TABLEAU INTERACTIF DES JOUEURS
        # -----------------------------------------------------------------
        # dash_table.DataTable permet d'afficher un tableau cliquable,
        # triable par colonne (sort_action='native') et paginé.
        #
        # style_data_conditional : colorie les lignes selon le segment,
        # comme dans le dashboard cours (même principe que les segments RFM).
        # -----------------------------------------------------------------

        html.Div(
            style={'padding': '0 40px 30px 40px'},
            children=[
                html.Div(
                    style={
                        'backgroundColor': '#111133',
                        'borderRadius': '10px',
                        'padding': '20px'
                    },
                    children=[
                        html.H3(
                            "📋 Détail des joueurs",
                            style={'color': '#FFD700', 'marginTop': 0, 'marginBottom': '6px'}
                        ),
                        html.Div(
                            id='table-count',
                            style={'color': '#aaaacc', 'fontSize': '13px', 'marginBottom': '15px'}
                        ),
                        dash_table.DataTable(
                            id='table-players',
                            columns=[
                                {'name': 'Joueur',    'id': 'name'},
                                {'name': 'Équipe',    'id': 'team_code'},
                                {'name': 'Position',  'id': 'position'},
                                {'name': 'Taille',    'id': 'height'},
                                {'name': 'Âge',       'id': 'age'},
                                {'name': 'Attaque',   'id': 'score_attack'},
                                {'name': 'Service',   'id': 'score_serve'},
                                {'name': 'Block',     'id': 'score_block'},
                                {'name': 'PPS',       'id': 'pps'},
                                {'name': 'Segment',   'id': 'segment'},
                            ],
                            sort_action='native',   # Tri natif en cliquant sur les en-têtes
                            page_size=15,           # 15 lignes par page
                            style_table={'overflowX': 'auto'},
                            style_header={
                                'backgroundColor': '#1a1a4e',
                                'color': '#FFD700',
                                'fontWeight': 'bold',
                                'textAlign': 'center'
                            },
                            style_cell={
                                'textAlign': 'center',
                                'padding': '8px',
                                'backgroundColor': '#111133',
                                'color': 'white',
                                'border': '1px solid #222244'
                            },
                            # Coloration des lignes selon le segment
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{segment} = "Elite"'},
                                    'backgroundColor': '#2a2a00',
                                    'color': '#FFD700'
                                },
                                {
                                    'if': {'filter_query': '{segment} = "Confirmed"'},
                                    'backgroundColor': '#0a2a0a',
                                    'color': '#4CAF50'
                                },
                                {
                                    'if': {'filter_query': '{segment} = "Average"'},
                                    'backgroundColor': '#0a1a2a',
                                    'color': '#2196F3'
                                },
                            ]
                        )
                    ]
                )
            ]
        ),

        # --- FOOTER ---
        html.Div(
            style={'textAlign': 'center', 'padding': '16px', 'color': '#555577', 'fontSize': '12px'},
            children="VNL 2024 Data Marketing Project · MSc2 Manager Data Marketing · Données : Kaggle + REST Countries API"
        )
    ]
)


# =============================================================================
# 5. CALLBACKS
# =============================================================================
#
# Les callbacks sont le cœur du dashboard interactif.
# Un callback se déclenche automatiquement quand une valeur Input change.
# Il met à jour les composants Output en retournant de nouvelles valeurs.
#
# Ici un seul callback gère tout : quand l'utilisateur change un filtre,
# les KPIs, drapeaux, graphiques ET le tableau se mettent à jour ensemble.
#
# Input  : lit la valeur d'un composant (ce que l'utilisateur a choisi)
# Output : met à jour le contenu d'un composant (ce qu'on affiche)
#
# =============================================================================

def filter_df(team, position, pps_min):
    """
    Filtre le DataFrame global selon les 3 critères sélectionnés.

    Paramètres :
        team     (str)   : code équipe ou 'ALL'
        position (str)   : code position ou 'ALL'
        pps_min  (float) : seuil minimum de PPS

    Retourne :
        DataFrame filtré
    """
    filtered = df.copy()
    if team != 'ALL':
        filtered = filtered[filtered['team_code'] == team]
    if position != 'ALL':
        filtered = filtered[filtered['position'] == position]
    filtered = filtered[filtered['pps'] >= pps_min]
    return filtered


@app.callback(
    Output('pps-label', 'children'),
    Input('filter-pps', 'value')
)
def update_slider_label(value):
    return f"📊 PPS minimum — {value} / 10"


@app.callback(
    Output('kpi-section',        'children'),   # Bloc KPIs
    Output('teams-flags-section','children'),   # Bloc drapeaux
    Output('graph-top20',        'figure'),     # Graphique Top 20
    Output('graph-segments',     'figure'),     # Graphique segments
    Output('graph-team-avg',     'figure'),     # Graphique équipes
    Output('table-players',      'data'),       # Données du tableau
    Output('table-count',        'children'),   # Compteur joueurs
    Input('filter-team',         'value'),      # Filtre équipe
    Input('filter-position',     'value'),      # Filtre position
    Input('filter-pps',          'value')       # Filtre PPS minimum
)
def update_dashboard(team, position, pps_min):
    """
    Callback principal : met à jour tout le dashboard quand un filtre change.
    Reçoit les 3 valeurs des filtres, retourne 7 éléments mis à jour.
    """

    # Application des filtres sur le DataFrame global
    filtered = filter_df(team, position, pps_min)

    # ── KPIs ─────────────────────────────────────────────────────────────

    if len(filtered) > 0:
        # Joueur avec le PPS le plus élevé dans la sélection
        top_player = filtered.loc[filtered['pps'].idxmax()]
        flag       = teams_df[teams_df['code'] == top_player['team_code']]['flag_url'].values
        flag_img   = flag[0] if len(flag) > 0 and pd.notna(flag[0]) else None

        kpi1_value = html.Div(
            style={'display': 'flex', 'alignItems': 'center', 'gap': '8px'},
            children=[
                # Drapeau récupéré via l'API REST Countries dans pipeline.py
                html.Img(src=flag_img,
                         style={'height': '20px', 'borderRadius': '2px',
                                'border': '1px solid #333366'}) if flag_img else None,
                html.Span(f"{top_player['name']} ({top_player['team_code']})")
            ]
        )
        kpi1_sub = f"PPS : {top_player['pps']:.2f} / 10"
    else:
        kpi1_value = "—"
        kpi1_sub   = ""

    # Nombre de joueurs classés Elite dans la sélection
    nb_elite   = len(filtered[filtered['segment'] == 'Elite'])
    kpi2_value = str(nb_elite)
    kpi2_sub   = f"sur {len(filtered)} joueurs filtrés"

    # PPS moyen de tous les joueurs sélectionnés
    avg_pps    = filtered['pps'].mean() if len(filtered) > 0 else 0
    kpi3_value = f"{avg_pps:.2f} / 10"
    kpi3_sub   = "Score moyen de performance"

    def kpi_card(icon, title, value, sub, color):
        """Génère une carte KPI avec bordure colorée à gauche"""
        return html.Div(
            style={
                'backgroundColor': '#111133',
                'borderRadius': '10px',
                'padding': '20px 24px',
                'flex': 1,
                'borderLeft': f'4px solid {color}'
            },
            children=[
                html.Div(f"{icon} {title}",
                         style={'color': '#aaaacc', 'fontSize': '12px', 'marginBottom': '8px'}),
                html.Div(value,
                         style={'fontSize': '20px', 'fontWeight': 'bold', 'color': color}),
                html.Div(sub,
                         style={'color': '#666688', 'fontSize': '11px', 'marginTop': '4px'})
            ]
        )

    kpis = [
        kpi_card("🥇", "Meilleur joueur", kpi1_value, kpi1_sub, "#FFD700"),
        kpi_card("⭐", "Joueurs Elite",   kpi2_value, kpi2_sub, "#FF6B6B"),
        kpi_card("📈", "PPS Moyen",       kpi3_value, kpi3_sub, "#4CAF50"),
    ]

    # ── Section drapeaux ─────────────────────────────────────────────────
    # On affiche le drapeau + code + PPS moyen de chaque équipe sélectionnée

    active_teams   = filtered['team_code'].unique()
    filtered_teams = teams_df[teams_df['code'].isin(active_teams)].copy()
    team_pps       = filtered.groupby('team_code')['pps'].mean().reset_index()
    team_pps.columns = ['code', 'avg_pps']
    filtered_teams = filtered_teams.merge(team_pps, on='code', how='left')

    flags_section = html.Div(
        style={'backgroundColor': '#111133', 'borderRadius': '10px', 'padding': '16px 24px'},
        children=[
            html.Div("🏳️ Équipes sélectionnées",
                     style={'color': '#aaaacc', 'fontSize': '13px', 'marginBottom': '12px'}),
            html.Div(
                style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '16px'},
                children=[
                    html.Div(
                        style={'textAlign': 'center', 'width': '70px'},
                        children=[
                            html.Img(
                                src=row['flag_url'],
                                style={'width': '50px', 'height': '33px',
                                       'objectFit': 'cover', 'borderRadius': '3px',
                                       'border': '1px solid #333366'}
                            ),
                            html.Div(row['code'],
                                     style={'color': 'white', 'fontSize': '11px',
                                            'marginTop': '4px', 'fontWeight': 'bold'}),
                            html.Div(f"{row['avg_pps']:.1f}",
                                     style={'color': '#FFD700', 'fontSize': '11px'})
                        ]
                    )
                    for _, row in filtered_teams.iterrows()
                    if pd.notna(row.get('flag_url')) and row.get('flag_url')
                ]
            )
        ]
    )

    # ── Graphique 1 : Top 20 joueurs par PPS (barres horizontales) ───────

    top20 = filtered.nlargest(20, 'pps').sort_values('pps')
    top20['pos_label'] = top20['position'].map(position_labels).fillna(top20['position'])

    fig_top20 = px.bar(
        top20,
        x='pps', y='name',
        orientation='h',
        color='segment',
        color_discrete_map=SEGMENT_COLORS,
        hover_data=['team_code', 'pos_label', 'score_attack', 'score_serve', 'score_block'],
        labels={'pps': 'Player Performance Score', 'name': '', 'segment': 'Segment'},
        title='🏆 Top 20 joueurs — Player Performance Score'
    )
    fig_top20.update_layout(
        plot_bgcolor='#111133', paper_bgcolor='#111133',
        font_color='white', title_font_color='#FFD700',
        legend=dict(bgcolor='#0d0d2b', font=dict(color='white')),
        xaxis=dict(gridcolor='#222244', range=[0, 10]),
        yaxis=dict(gridcolor='#222244'),
        height=480
    )

    # ── Graphique 2 : Répartition des segments (donut) ───────────────────

    seg_counts        = filtered['segment'].value_counts().reset_index()
    seg_counts.columns = ['segment', 'count']

    fig_segments = go.Figure(go.Pie(
        labels=seg_counts['segment'],
        values=seg_counts['count'],
        hole=0.55,      # Donut au lieu de camembert plein
        marker=dict(colors=[SEGMENT_COLORS.get(s, '#888') for s in seg_counts['segment']]),
        textinfo='label+percent',
        textfont=dict(color='white')
    ))
    fig_segments.update_layout(
        title='🎯 Répartition des segments',
        plot_bgcolor='#111133', paper_bgcolor='#111133',
        font_color='white', title_font_color='#FFD700',
        legend=dict(bgcolor='#0d0d2b', font=dict(color='white')),
        height=480
    )

    # ── Graphique 3 : PPS moyen par équipe (barres verticales) ──────────

    team_avg = filtered.groupby('team_code').agg(
        avg_pps   =('pps', 'mean'),
        nb_players=('player_id', 'count'),
        nb_elite  =('segment', lambda x: (x == 'Elite').sum())
    ).reset_index().sort_values('avg_pps', ascending=False)

    fig_team = px.bar(
        team_avg,
        x='team_code', y='avg_pps',
        color='avg_pps',
        color_continuous_scale='Viridis',
        hover_data=['nb_players', 'nb_elite'],
        labels={'avg_pps': 'PPS Moyen', 'team_code': 'Équipe'},
        title='🌍 Performance moyenne par équipe (PPS)'
    )
    fig_team.update_layout(
        plot_bgcolor='#111133', paper_bgcolor='#111133',
        font_color='white', title_font_color='#FFD700',
        coloraxis_showscale=False,
        xaxis=dict(gridcolor='#222244'),
        yaxis=dict(gridcolor='#222244', range=[0, 10]),
        height=380
    )

    # ── Tableau interactif ───────────────────────────────────────────────
    # On prépare les données pour le DataTable.
    # to_dict('records') convertit le DataFrame en liste de dictionnaires,
    # format attendu par dash_table.DataTable.

    table_cols = ['name', 'team_code', 'position', 'height', 'age',
                  'score_attack', 'score_serve', 'score_block', 'pps', 'segment']
    table_data = filtered[table_cols].copy()

    # Arrondi à 2 décimales pour les scores
    for col in ['score_attack', 'score_serve', 'score_block', 'pps']:
        table_data[col] = table_data[col].round(2)

    table_count = f"{len(table_data)} joueurs affichés"

    return kpis, flags_section, fig_top20, fig_segments, fig_team, \
           table_data.to_dict('records'), table_count


# =============================================================================
# 6. LANCEMENT
# =============================================================================

if __name__ == '__main__':
    print("\n=== VNL 2024 - Dashboard Player Performance (démo statique) ===")
    print(f"  {len(df)} joueurs chargés depuis les CSV")
    print(f"  {df['team_code'].nunique()} équipes | {df['position'].nunique()} positions")
    print("\n  Ouvrir http://127.0.0.1:8050 dans le navigateur")
    print("  Ctrl+C pour arrêter\n")
    app.run(debug=True)