-- =============================================================================
-- VIEWS - Vues SQL
-- CREATE VIEW pour simplifier les requêtes complexes
-- VNL 2024 | MSc2 Manager Data Marketing
-- =============================================================================

USE vnl2024;


-- -----------------------------------------------------------------------------
-- Vue 1 : v_player_overview
-- Vue synthétique de chaque joueur avec toutes ses stats par catégorie
-- Évite de réécrire la jointure complexe à chaque requête
-- Le dashboard et le pipeline peuvent l'utiliser directement
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_player_overview AS
SELECT
    p.player_id,
    p.name,
    t.code          AS team_code,
    t.country,
    t.continent,
    p.position,
    p.height,
    (2024 - p.birth_year)                                               AS age,
    -- MAX + CASE : pivot des stats par catégorie en colonnes
    MAX(CASE WHEN ps.stat_category = 'score'  THEN ps.total_points  END) AS score_pts,
    MAX(CASE WHEN ps.stat_category = 'attack' THEN ps.total_points  END) AS attack_pts,
    MAX(CASE WHEN ps.stat_category = 'attack' THEN ps.efficiency_pct END) AS attack_eff,
    MAX(CASE WHEN ps.stat_category = 'serve'  THEN ps.total_points  END) AS serve_pts,
    MAX(CASE WHEN ps.stat_category = 'block'  THEN ps.total_points  END) AS block_pts
FROM players p
JOIN teams t         ON p.team_id    = t.team_id
LEFT JOIN player_stats ps ON p.player_id = ps.player_id
GROUP BY p.player_id, p.name, t.code, t.country, t.continent, p.position, p.height, p.birth_year;


-- Utilisation de la vue
SELECT * FROM v_player_overview ORDER BY attack_pts DESC LIMIT 10;


-- -----------------------------------------------------------------------------
-- Vue 2 : v_team_summary
-- Vue agrégée par équipe avec les moyennes et comptages clés
-- Utile pour les comparaisons entre équipes
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_team_summary AS
SELECT
    t.code,
    t.country,
    t.continent,
    t.population,
    COUNT(DISTINCT p.player_id)                  AS nb_joueurs,
    ROUND(AVG(sc.pps), 2)                        AS avg_pps,
    ROUND(AVG(p.height), 1)                      AS avg_taille,
    SUM(CASE WHEN sc.segment = 'Elite'     THEN 1 ELSE 0 END) AS nb_elite,
    SUM(CASE WHEN sc.segment = 'Confirmed' THEN 1 ELSE 0 END) AS nb_confirmed,
    SUM(CASE WHEN sc.segment = 'Average'   THEN 1 ELSE 0 END) AS nb_average,
    SUM(CASE WHEN sc.segment = 'Low'       THEN 1 ELSE 0 END) AS nb_low
FROM teams t
JOIN players p       ON t.team_id    = p.team_id
JOIN player_scores sc ON p.player_id = sc.player_id
GROUP BY t.team_id, t.code, t.country, t.continent, t.population;


-- Utilisation de la vue
SELECT * FROM v_team_summary ORDER BY avg_pps DESC;