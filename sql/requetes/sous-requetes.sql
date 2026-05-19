-- =============================================================================
-- SOUS-REQUÊTES - Requêtes imbriquées
-- VNL 2024 | MSc2 Manager Data Marketing
-- =============================================================================

USE vnl2024;


-- -----------------------------------------------------------------------------
-- Sous-requête 1 : Joueurs au-dessus de la moyenne de leur équipe
-- La sous-requête calcule le PPS moyen de l'équipe du joueur courant
-- La requête principale filtre ceux qui dépassent cette moyenne
-- -----------------------------------------------------------------------------

SELECT p.name,
       t.country,
       ps.total_points
FROM player_stats ps
JOIN players p ON ps.player_id = p.player_id
JOIN teams t   ON p.team_id    = t.team_id
WHERE ps.stat_category = 'score'
  AND ps.total_points > (
      -- Sous-requête : moyenne des points de l'équipe du joueur courant
      SELECT AVG(ps2.total_points)
      FROM player_stats ps2
      JOIN players p2 ON ps2.player_id = p2.player_id
      WHERE ps2.stat_category = 'score'
        AND p2.team_id = p.team_id
  )
ORDER BY t.country, ps.total_points DESC;


-- -----------------------------------------------------------------------------
-- Sous-requête 2 : Équipes dont le PPS moyen dépasse la moyenne globale
-- La sous-requête calcule le PPS moyen global de tous les joueurs
-- La requête principale garde seulement les équipes au-dessus
-- -----------------------------------------------------------------------------

SELECT team_code,
       ROUND(AVG(pps), 2) AS pps_moyen_equipe
FROM player_scores
GROUP BY team_code
HAVING AVG(pps) > (
    -- Sous-requête : PPS moyen global toutes équipes confondues
    SELECT AVG(pps) FROM player_scores
)
ORDER BY pps_moyen_equipe DESC;


-- -----------------------------------------------------------------------------
-- Sous-requête 3 : Joueurs Elite dans des équipes d'Europe
-- IN avec sous-requête pour filtrer sur une liste de valeurs
-- -----------------------------------------------------------------------------

SELECT name,
       team_code,
       position,
       pps
FROM player_scores
WHERE segment = 'Elite'
  AND team_code IN (
      -- Sous-requête : codes des équipes européennes
      SELECT code FROM teams WHERE continent = 'Europe'
  )
ORDER BY pps DESC;