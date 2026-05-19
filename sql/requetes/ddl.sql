-- =============================================================================
-- DDL - Data Definition Language
-- Création de la base, des tables et des contraintes
-- VNL 2024 | MSc2 Manager Data Marketing
-- =============================================================================


-- Création de la base de données
CREATE DATABASE IF NOT EXISTS vnl2024;
USE vnl2024;


-- -----------------------------------------------------------------------------
-- Table 1 : teams
-- Contient les 16 équipes de la VNL 2024
-- Enrichie via l'API REST Countries (population, flag_url)
-- -----------------------------------------------------------------------------

CREATE TABLE teams (
    team_id     INT PRIMARY KEY AUTO_INCREMENT,
    code        VARCHAR(3)  NOT NULL UNIQUE,   -- Contrainte UNIQUE : pas deux fois le même code
    country     VARCHAR(50) NOT NULL,           -- Contrainte NOT NULL : obligatoire
    continent   VARCHAR(30) NOT NULL,
    population  BIGINT,
    flag_url    VARCHAR(200)
);


-- -----------------------------------------------------------------------------
-- Table 2 : players
-- Contient les 304 joueurs participant à la VNL 2024
-- Liée à teams via une FOREIGN KEY
-- -----------------------------------------------------------------------------

CREATE TABLE players (
    player_id   INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,          -- Contrainte NOT NULL
    team_id     INT NOT NULL,
    position    VARCHAR(5)   NOT NULL,          -- OH, MB, S, O, L
    height      INT,
    birth_year  INT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)  -- Contrainte FOREIGN KEY
);


-- -----------------------------------------------------------------------------
-- Table 3 : player_stats
-- Table de jonction MANY-TO-MANY entre players et catégories de stats
-- Un joueur peut avoir des stats dans plusieurs catégories :
-- attack, serve, block, score
-- -----------------------------------------------------------------------------

CREATE TABLE player_stats (
    stat_id         INT PRIMARY KEY AUTO_INCREMENT,
    player_id       INT         NOT NULL,
    stat_category   VARCHAR(20) NOT NULL,   -- 'attack', 'serve', 'block', 'score'
    total_points    FLOAT,
    error_count     FLOAT,
    attempts        FLOAT,
    match_avg       FLOAT,
    efficiency_pct  FLOAT,
    total_actions   FLOAT,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    CONSTRAINT uq_player_category UNIQUE (player_id, stat_category)  -- Un joueur ne peut pas avoir deux fois la même catégorie
);


-- -----------------------------------------------------------------------------
-- Table 4 : player_scores
-- Créée et alimentée par le pipeline Python (pipeline.py)
-- Contient les résultats de l'algorithme Player Performance Score (PPS)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS player_scores (
    score_id     INT PRIMARY KEY AUTO_INCREMENT,
    player_id    INT          NOT NULL,
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
);