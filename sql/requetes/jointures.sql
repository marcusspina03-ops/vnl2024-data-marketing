-- =============================================================================
-- JOINTURES - Requêtes avec jointures sur 3 tables ou plus
-- VNL 2024 | MSc2 Manager Data Marketing
-- =============================================================================

USE vnl2024;


-- -----------------------------------------------------------------------------
-- Jointure 1 : Stats d'attaque par continent (3 tables)
-- teams → players → player_stats
-- Permet de comparer les continents sur leurs performances offensives
-- -----------------------------------------------------------------------------

SELECT t.continent,
       AVG(ps.total_points)    AS avg_points_attaque,
       AVG(ps.efficiency_pct)  AS avg_efficacite,
       COUNT(DISTINCT p.player_id) AS nb_joueurs
FROM teams t
JOIN players p      ON t.team_id    = p.team_id
JOIN player_stats ps ON p.player_id = ps.player_id
WHERE ps.stat_category = 'attack'
GROUP BY t.continent
ORDER BY avg_points_attaque DESC;


-- -----------------------------------------------------------------------------
-- Jointure 2 : Vue complète joueur + équipe + PPS (4 tables)
-- teams → players → player_stats → player_scores
-- Donne une vue synthétique de chaque joueur avec toutes ses infos
-- -----------------------------------------------------------------------------

SELECT p.name                               AS joueur,
       t.country                            AS pays,
       t.continent,
       p.position,
       p.height                             AS taille,
       (2024 - p.birth_year)               AS age,
       ps.total_points                      AS points_attaque,
       ps.efficiency_pct                    AS efficacite_attaque,
       sc.pps                               AS performance_score,
       sc.segment
FROM players p
JOIN teams t         ON p.team_id    = t.team_id
JOIN player_stats ps ON p.player_id  = ps.player_id
JOIN player_scores sc ON p.player_id = sc.player_id
WHERE ps.stat_category = 'attack'
ORDER BY sc.pps DESC
LIMIT 20;


-- -----------------------------------------------------------------------------
-- Jointure 3 : Meilleur joueur par équipe (3 tables)
-- Utilise MAX pour trouver le PPS maximum par équipe
-- puis rejoint pour récupérer le nom du joueur correspondant
-- -----------------------------------------------------------------------------

SELECT t.country,
       t.code,
       sc.name       AS meilleur_joueur,
       sc.position,
       sc.pps,
       sc.segment
FROM teams t
JOIN player_scores sc ON t.code = sc.team_code
WHERE sc.pps = (
    SELECT MAX(sc2.pps)
    FROM player_scores sc2
    WHERE sc2.team_code = t.code
)
ORDER BY sc.pps DESC;