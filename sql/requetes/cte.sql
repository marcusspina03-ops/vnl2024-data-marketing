-- =============================================================================
-- CTE - Common Table Expressions (WITH)
-- Requêtes avec clauses WITH pour structurer des analyses complexes
-- VNL 2024 | MSc2 Manager Data Marketing
-- =============================================================================

USE vnl2024;


-- -----------------------------------------------------------------------------
-- CTE 1 : Classement des joueurs par efficacité d'attaque dans leur équipe
-- RANK() OVER (PARTITION BY) : classe les joueurs au sein de chaque équipe
-- La CTE calcule le rang, la requête principale filtre sur le rang 1
-- → Donne le meilleur attaquant de chaque équipe
-- -----------------------------------------------------------------------------

WITH attack_ranking AS (
    SELECT p.name,
           t.country,
           t.code                   AS team_code,
           ps.efficiency_pct,
           ps.total_points,
           -- RANK() numérote les joueurs du meilleur au moins bon
           -- PARTITION BY team_id : le classement repart à 1 pour chaque équipe
           RANK() OVER (
               PARTITION BY p.team_id
               ORDER BY ps.efficiency_pct DESC
           ) AS rang_dans_equipe
    FROM player_stats ps
    JOIN players p ON ps.player_id = p.player_id
    JOIN teams t   ON p.team_id    = t.team_id
    WHERE ps.stat_category = 'attack'
      AND ps.attempts > 50   -- On exclut les joueurs avec trop peu de tentatives
)
SELECT *
FROM attack_ranking
WHERE rang_dans_equipe = 1
ORDER BY efficiency_pct DESC;


-- -----------------------------------------------------------------------------
-- CTE 2 : Analyse des segments par continent
-- Première CTE : compte les joueurs par continent et segment
-- Deuxième CTE : calcule le total par continent
-- Résultat final : pourcentage de chaque segment par continent
-- -----------------------------------------------------------------------------

WITH segments_par_continent AS (
    SELECT t.continent,
           sc.segment,
           COUNT(*) AS nb_joueurs
    FROM player_scores sc
    JOIN teams t ON sc.team_code = t.code
    GROUP BY t.continent, sc.segment
),
total_par_continent AS (
    SELECT continent,
           SUM(nb_joueurs) AS total
    FROM segments_par_continent
    GROUP BY continent
)
SELECT s.continent,
       s.segment,
       s.nb_joueurs,
       t.total,
       ROUND(s.nb_joueurs * 100.0 / t.total, 1) AS pourcentage
FROM segments_par_continent s
JOIN total_par_continent t ON s.continent = t.continent
ORDER BY s.continent, s.nb_joueurs DESC;


-- -----------------------------------------------------------------------------
-- CTE 3 : Top 3 joueurs par position toutes équipes confondues
-- RANK() OVER (PARTITION BY position) : classe par position
-- Utile pour le scouting : meilleurs joueurs à chaque poste
-- -----------------------------------------------------------------------------

WITH top_par_position AS (
    SELECT name,
           team_code,
           position,
           pps,
           segment,
           RANK() OVER (
               PARTITION BY position
               ORDER BY pps DESC
           ) AS rang_position
    FROM player_scores
)
SELECT *
FROM top_par_position
WHERE rang_position <= 3
ORDER BY position, rang_position;