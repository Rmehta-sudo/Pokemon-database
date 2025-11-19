-- Drop database if it exists to start fresh
DROP DATABASE IF EXISTS pokemon_league_db;
CREATE DATABASE pokemon_league_db;
USE pokemon_league_db;

-- ---------------------------------------------------
-- INDEPENDENT TABLES (Level 0)
-- ---------------------------------------------------

-- 11. REGION
CREATE TABLE Region (
    region_id VARCHAR(25) PRIMARY KEY, 
    region_name VARCHAR(100) NOT NULL,
    main_city VARCHAR(100),
    CONSTRAINT chk_region_id CHECK (region_id REGEXP '^R[A-Z]{3,16}[0-9]{3}$')
);

-- 11. TYPE
CREATE TABLE Type (
    type_id VARCHAR(25) PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    CONSTRAINT chk_type_id CHECK (type_id REGEXP '^Y[A-Z]{3,16}[0-9]{3}$')
);

-- 11. ABILITY
CREATE TABLE Ability (
    ability_id VARCHAR(25) PRIMARY KEY,
    ability_name VARCHAR(100) NOT NULL,
    effect_description TEXT,
    CONSTRAINT chk_ability_id CHECK (ability_id REGEXP '^A[A-Z]{3,16}[0-9]{3}$')
);

-- ---------------------------------------------------
-- LEVEL 1 TABLES (Dependencies on Level 0)
-- ---------------------------------------------------

-- 0. CITY
CREATE TABLE City (
    city_id VARCHAR(25) PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    region_id VARCHAR(25),
    -- Added ON UPDATE CASCADE
    FOREIGN KEY (region_id) REFERENCES Region(region_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_city_id CHECK (city_id REGEXP '^C[A-Z]{3,16}[0-9]{3}$')
);

-- 11. MOVE
CREATE TABLE Move (
    move_id VARCHAR(25) PRIMARY KEY,
    move_name VARCHAR(100) NOT NULL,
    power INT,
    accuracy INT,
    pp INT,
    type_id VARCHAR(25),
    -- CHANGED: Use ENUM for strict category control
    category ENUM('Physical', 'Special', 'Status') NOT NULL,
    FOREIGN KEY (type_id) REFERENCES Type(type_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_move_id CHECK (move_id REGEXP '^M[A-Z]{3,16}[0-9]{3}$'),
    -- ADDED: Logical constraints for game stats
    CONSTRAINT chk_accuracy CHECK (accuracy >= 0 AND accuracy <= 100),
    CONSTRAINT chk_power CHECK (power >= 0),
    CONSTRAINT chk_pp CHECK (pp > 0)
);

-- 11. TYPE STRENGTH
CREATE TABLE TypeStrength (
    type_id VARCHAR(25),
    strength VARCHAR(50),
    PRIMARY KEY (type_id, strength),
    FOREIGN KEY (type_id) REFERENCES Type(type_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 11. TYPE WEAKNESS
CREATE TABLE TypeWeakness (
    type_id VARCHAR(25),
    weakness VARCHAR(50),
    PRIMARY KEY (type_id, weakness),
    FOREIGN KEY (type_id) REFERENCES Type(type_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 2. POKEMON SPECIES
CREATE TABLE PokemonSpecies (
    species_id VARCHAR(25) PRIMARY KEY,
    species_name VARCHAR(100) NOT NULL,
    base_hp INT NOT NULL,
    base_attack INT NOT NULL,
    base_defense INT NOT NULL,
    base_speed INT NOT NULL,
    primary_type_id VARCHAR(25),
    secondary_type_id VARCHAR(25),
    FOREIGN KEY (primary_type_id) REFERENCES Type(type_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (secondary_type_id) REFERENCES Type(type_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_species_id CHECK (species_id REGEXP '^S[A-Z]{3,16}[0-9]{3}$'),
    -- ADDED: Stat validation
    CONSTRAINT chk_base_stats CHECK (base_hp > 0 AND base_attack > 0 AND base_defense > 0 AND base_speed > 0)
);

-- 1. TRAINER (Supertype)
CREATE TABLE Trainer (
    trainer_id VARCHAR(25) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    -- CHANGED: Use ENUM for Gender
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    birth_date DATE,
    contact_info_email VARCHAR(150) UNIQUE, -- ADDED: Email should be unique
    contact_info_phone VARCHAR(50),
    region_id VARCHAR(25),
    FOREIGN KEY (region_id) REFERENCES Region(region_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_trainer_id CHECK (trainer_id REGEXP '^T[A-Z]{3,16}[0-9]{3}$')
);

-- 7. LEAGUE SEASON
CREATE TABLE LeagueSeason (
    season_id VARCHAR(25) PRIMARY KEY,
    year INT NOT NULL,
    region_id VARCHAR(25),
    theme VARCHAR(100),
    FOREIGN KEY (region_id) REFERENCES Region(region_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_season_id CHECK (season_id REGEXP '^L[A-Z]{3,16}[0-9]{3}$')
);

-- ---------------------------------------------------
-- LEVEL 2 TABLES (Dependencies on Level 1)
-- ---------------------------------------------------

-- 2. POKEMON SPECIES ABILITY
CREATE TABLE PokemonSpeciesAbility (
    species_id VARCHAR(25),
    ability_id VARCHAR(25),
    PRIMARY KEY (species_id, ability_id),
    FOREIGN KEY (species_id) REFERENCES PokemonSpecies(species_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES Ability(ability_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 4. GYM
CREATE TABLE Gym (
    gym_id VARCHAR(25) PRIMARY KEY,
    gym_name VARCHAR(100) NOT NULL,
    city_id VARCHAR(25),
    specialization_type_id VARCHAR(25),
    FOREIGN KEY (city_id) REFERENCES City(city_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (specialization_type_id) REFERENCES Type(type_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_gym_id CHECK (gym_id REGEXP '^G[A-Z]{3,16}[0-9]{3}$')
);

-- 5. GYM LEADER (Profile only)
CREATE TABLE GymLeader (
    leader_id VARCHAR(25) PRIMARY KEY,
    specialty_type_id VARCHAR(25),
    years_of_experience INT CHECK (years_of_experience >= 0),
    FOREIGN KEY (leader_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (specialty_type_id) REFERENCES Type(type_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- 6. CHAMPION
CREATE TABLE Champion (
    champion_id VARCHAR(25) PRIMARY KEY,
    title_year INT,
    FOREIGN KEY (champion_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. REGISTERED POKEMON
CREATE TABLE RegisteredPokemon (
    pokemon_id VARCHAR(25) PRIMARY KEY,
    species_id VARCHAR(25),
    trainer_id VARCHAR(25),
    nickname VARCHAR(100),
    level INT CHECK (level BETWEEN 1 AND 100), -- ADDED: Valid level range
    experience_points INT CHECK (experience_points >= 0),
    registration_date DATE,
    FOREIGN KEY (species_id) REFERENCES PokemonSpecies(species_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_pokemon_id CHECK (pokemon_id REGEXP '^P[A-Z]{3,16}[0-9]{3}$')
);

-- 9. TOURNAMENT
CREATE TABLE Tournament (
    tournament_id VARCHAR(25) PRIMARY KEY,
    tournament_name VARCHAR(150) NOT NULL,
    start_date DATE,
    end_date DATE,
    city_id VARCHAR(25),
    season_id VARCHAR(25),
    FOREIGN KEY (city_id) REFERENCES City(city_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (season_id) REFERENCES LeagueSeason(season_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_tournament_id CHECK (tournament_id REGEXP '^O[A-Z]{3,16}[0-9]{3}$'),
    CONSTRAINT chk_dates CHECK (end_date >= start_date) -- ADDED: Date logic
);

-- ---------------------------------------------------
-- LEVEL 3 TABLES (Dependencies on Level 2)
-- ---------------------------------------------------

-- 3. REGISTERED POKEMON MOVE
CREATE TABLE RegisteredPokemonMove (
    pokemon_id VARCHAR(25),
    move_id VARCHAR(25),
    PRIMARY KEY (pokemon_id, move_id),
    FOREIGN KEY (pokemon_id) REFERENCES RegisteredPokemon(pokemon_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (move_id) REFERENCES Move(move_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 7. GYM SEASON REGISTRY
CREATE TABLE GymSeasonRegistry (
    registry_id VARCHAR(25) PRIMARY KEY,
    season_id VARCHAR(25),
    gym_id VARCHAR(25),
    leader_id VARCHAR(25),
    FOREIGN KEY (season_id) REFERENCES LeagueSeason(season_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (leader_id) REFERENCES GymLeader(leader_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_registry_id CHECK (registry_id REGEXP '^E[A-Z]{3,16}[0-9]{3}$')
);

-- 8. GYM BATTLE
CREATE TABLE GymBattle (
    battle_id VARCHAR(25) PRIMARY KEY,
    challenger_id VARCHAR(25),
    gym_id VARCHAR(25),
    leader_id VARCHAR(25),
    battle_date DATE,
    -- CHANGED: Use ENUM for results
    result ENUM('Win', 'Loss', 'Draw') NOT NULL,
    FOREIGN KEY (challenger_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (leader_id) REFERENCES GymLeader(leader_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_battle_id CHECK (battle_id REGEXP '^B[A-Z]{3,16}[0-9]{3}$')
);

-- 8. GYM BADGE
CREATE TABLE GymBadge (
    gym_id VARCHAR(25),
    badge_number INT,
    date_earned DATE,
    trainer_id VARCHAR(25),
    PRIMARY KEY (gym_id, badge_number),
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 8. GYM BADGE NAME
CREATE TABLE GymBadgeName (
    gym_id VARCHAR(25) PRIMARY KEY,
    badge_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (gym_id) REFERENCES Gym(gym_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 9. TOURNAMENT ENTRY
CREATE TABLE TournamentEntry (
    tournament_id VARCHAR(25),
    trainer_id VARCHAR(25),
    registration_date DATE,
    PRIMARY KEY (tournament_id, trainer_id),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 10. MATCH
CREATE TABLE Match_Table (
    tournament_id VARCHAR(25),
    match_number INT,
    trainer1_id VARCHAR(25),
    trainer2_id VARCHAR(25),
    winner_id VARCHAR(25),
    match_date DATE,
    round_number INT,
    PRIMARY KEY (tournament_id, match_number),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (trainer1_id) REFERENCES Trainer(trainer_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (trainer2_id) REFERENCES Trainer(trainer_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (winner_id) REFERENCES Trainer(trainer_id) ON DELETE SET NULL ON UPDATE CASCADE
);