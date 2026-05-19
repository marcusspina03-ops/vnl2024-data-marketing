-- =============================================================================
-- SELECT - Requêtes de consultation
-- WHERE, GROUP BY, HAVING, ORDER BY, LIMIT
-- VNL 2024 | MSc2 Manager Data Marketing
-- =============================================================================

USE vnl2024;


-- -----------------------------------------------------------------------------
-- Requête 1 : Top 10 scoreurs toutes équipes confondues
-- WHERE filtre les joueurs avec au moins 1 point
-- ORDER BY trie du plus grand au plus petit
-- LIMIT garde seulement les 10 premiers
-- -----------------------------------------------------------------------------

SELECT p.name,
       t.country,
       ps.total_points
FROM player_stats ps
JOIN players p ON ps.player_id = p.player_id
JOIN teams t   ON p.team_id    = t.team_id
WHERE ps.stat_category = 'score'
  AND ps.total_points  > 0
ORDER BY ps.total_points DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- Requête 2 : Nombre de joueurs par équipe
-- GROUP BY regroupe les joueurs par équipe
-- ORDER BY trie par nombre de joueurs décroissant
-- -----------------------------------------------------------------------------

SELECT t.country,
       t.code,
       COUNT(p.player_id) AS nb_joueurs
FROM teams t
JOIN players p ON t.team_id = p.team_id
GROUP BY t.team_id, t.country, t.code
ORDER BY nb_joueurs DESC;


-- -----------------------------------------------------------------------------
-- Requête 3 : Équipes avec plus de 5 attaquants (OH + O)
-- WHERE filtre sur les positions offensives
-- HAVING filtre sur le résultat du GROUP BY (après agrégation)
-- Différence avec WHERE : HAVING s'applique après le regroupement
-- -----------------------------------------------------------------------------

SELECT t.country,
       COUNT(p.player_id) AS nb_attaquants
FROM teams t
JOIN players p ON t.team_id = p.team_id
WHERE p.position IN ('OH', 'O')
GROUP BY t.team_id, t.country
HAVING nb_attaquants > 5
ORDER BY nb_attaquants DESC;


-- -----------------------------------------------------------------------------
-- Requête 4 : Stats moyennes par position
-- GROUP BY sur la position pour comparer les profils de joueurs
-- -----------------------------------------------------------------------------

SELECT p.position,
       COUNT(DISTINCT p.player_id)      AS nb_joueurs,
       AVG(ps.total_points)             AS avg_points,
       AVG(ps.efficiency_pct)           AS avg_efficacite,
       ROUND(AVG(p.height), 1)          AS taille_moyenne
FROM players p
JOIN player_stats ps ON p.player_id = ps.player_id
WHERE ps.stat_category = 'attack'
GROUP BY p.position
ORDER BY avg_points DESC;


-- -----------------------------------------------------------------------------
-- Requête 5 : Joueurs français avec leur PPS
-- WHERE filtre sur l'équipe France
-- ORDER BY trie par PPS décroissant
-- -----------------------------------------------------------------------------

SELECT ps.name,
       ps.position,
       ps.pps,
       ps.segment
FROM player_scores ps
WHERE ps.team_code = 'FRA'
ORDER BY ps.pps DESC;