-- =============================================================================
-- FONCTIONS ET PROCÉDURES STOCKÉES
-- VNL 2024 | MSc2 Manager Data Marketing
-- =============================================================================

USE vnl2024;


-- -----------------------------------------------------------------------------
-- Procédure 1 : GetTeamTopScorers
-- Retourne les N meilleurs scoreurs d'une équipe donnée
--
-- Paramètres :
--   team_code (VARCHAR) : code de l'équipe (ex: 'FRA', 'ITA')
--   top_n     (INT)     : nombre de joueurs à retourner
--
-- Utilisation :
--   CALL GetTeamTopScorers('FRA', 5);
--   CALL GetTeamTopScorers('ITA', 3);
-- -----------------------------------------------------------------------------

DELIMITER $$

CREATE PROCEDURE GetTeamTopScorers(
    IN team_code VARCHAR(3),
    IN top_n     INT
)
BEGIN
    -- Retourne les N meilleurs scoreurs d'une équipe
    -- triés par points décroissants
    SELECT p.name,
           t.country,
           ps.total_points,
           ps.efficiency_pct,
           sc.pps,
           sc.segment
    FROM player_stats ps
    JOIN players p      ON ps.player_id = p.player_id
    JOIN teams t        ON p.team_id    = t.team_id
    JOIN player_scores sc ON p.player_id = sc.player_id
    WHERE ps.stat_category = 'score'
      AND t.code            = team_code
      AND ps.total_points  > 0
    ORDER BY ps.total_points DESC
    LIMIT top_n;
END$$

DELIMITER ;

-- Test de la procédure
CALL GetTeamTopScorers('FRA', 5);
CALL GetTeamTopScorers('ITA', 3);


-- -----------------------------------------------------------------------------
-- Procédure 2 : GetSegmentStats
-- Retourne les statistiques détaillées d'un segment PPS donné
--
-- Paramètres :
--   segment_name (VARCHAR) : nom du segment ('Elite', 'Confirmed', 'Average', 'Low')
--
-- Utilisation :
--   CALL GetSegmentStats('Elite');
-- -----------------------------------------------------------------------------

DELIMITER $$

CREATE PROCEDURE GetSegmentStats(
    IN segment_name VARCHAR(20)
)
BEGIN
    -- Stats globales du segment
    SELECT segment_name                        AS segment,
           COUNT(*)                            AS nb_joueurs,
           ROUND(AVG(pps), 2)                  AS pps_moyen,
           ROUND(AVG(score_attack), 2)         AS attaque_moyenne,
           ROUND(AVG(score_serve), 2)          AS service_moyen,
           ROUND(AVG(score_block), 2)          AS block_moyen,
           COUNT(DISTINCT team_code)           AS nb_equipes_representees
    FROM player_scores
    WHERE segment = segment_name;

    -- Liste des joueurs de ce segment triés par PPS
    SELECT name,
           team_code,
           position,
           ROUND(pps, 2) AS pps
    FROM player_scores
    WHERE segment = segment_name
    ORDER BY pps DESC;
END$$

DELIMITER ;

-- Test de la procédure
CALL GetSegmentStats('Elite');


-- -----------------------------------------------------------------------------
-- Fonction : GetPlayerSegment
-- Retourne le segment PPS d'un joueur à partir de son score
-- Même logique que dans pipeline.py — cohérence entre SQL et Python
--
-- Utilisation :
--   SELECT GetPlayerSegment(7.5);  -- Retourne 'Elite'
--   SELECT GetPlayerSegment(3.2);  -- Retourne 'Average'
-- -----------------------------------------------------------------------------

DELIMITER $$

CREATE FUNCTION GetPlayerSegment(pps_score FLOAT)
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    -- DETERMINISTIC : pour un même score, retourne toujours le même segment
    DECLARE result VARCHAR(20);

    IF pps_score >= 7 THEN
        SET result = 'Elite';
    ELSEIF pps_score >= 4 THEN
        SET result = 'Confirmed';
    ELSEIF pps_score >= 2 THEN
        SET result = 'Average';
    ELSE
        SET result = 'Low';
    END IF;

    RETURN result;
END$$

DELIMITER ;

-- Test de la fonction
SELECT GetPlayerSegment(8.5);   -- Elite
SELECT GetPlayerSegment(5.0);   -- Confirmed
SELECT GetPlayerSegment(1.5);   -- Low