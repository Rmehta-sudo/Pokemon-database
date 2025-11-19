USE pokemon_league_db;

-- ============================================================
-- 1. BASIC LOOKUP DATA (Region, Type, Ability, Move)
-- ============================================================

-- REGIONS (Prefix R)
INSERT INTO Region (region_id, region_name, main_city) VALUES
('RAAA001', 'Kanto', 'Saffron City'),
('RAAA002', 'Johto', 'Goldenrod City'),
('RAAA003', 'Hoenn', 'Lilycove City'),
('RAAA004', 'Sinnoh', 'Jubilife City');

-- TYPES (Prefix Y)
INSERT INTO Type (type_id, type_name) VALUES
('YAAA001', 'Electric'),
('YAAA002', 'Water'),
('YAAA003', 'Fire'),
('YAAA004', 'Grass'),
('YAAA005', 'Psychic'),
('YAAA006', 'Rock'),
('YAAA007', 'Ground'),
('YAAA008', 'Normal'),
('YAAA009', 'Flying'),
('YAAA010', 'Dragon'),
('YAAA011', 'Ghost'),
('YAAA012', 'Fighting'),
('YAAA013', 'Ice'),
('YAAA014', 'Bug'),
('YAAA015', 'Poison');

-- ABILITIES (Prefix A)
INSERT INTO Ability (ability_id, ability_name, effect_description) VALUES
('AAAA001', 'Static', 'May paralyze attacker on contact'),
('AAAA002', 'Torrent', 'Powers up Water moves in a pinch'),
('AAAA003', 'Blaze', 'Powers up Fire moves in a pinch'),
('AAAA004', 'Overgrow', 'Powers up Grass moves in a pinch'),
('AAAA005', 'Levitate', 'Immune to Ground moves'),
('AAAA006', 'Intimidate', 'Lowers opponent Attack'),
('AAAA007', 'Keen Eye', 'Prevents accuracy loss'),
('AAAA008', 'Guts', 'Boosts Attack if status altered'),
('AAAA009', 'Synchronize', 'Passes on status problems'),
('AAAA010', 'Pressure', 'Raises opponent PP usage');

-- MOVES (Prefix M) - Expanded to 25
INSERT INTO Move (move_id, move_name, power, accuracy, pp, type_id, category) VALUES
('MAAA001', 'Thunderbolt', 90, 100, 15, 'YAAA001', 'Special'),
('MAAA002', 'Surf', 90, 100, 15, 'YAAA002', 'Special'),
('MAAA003', 'Flamethrower', 90, 100, 15, 'YAAA003', 'Special'),
('MAAA004', 'Earthquake', 100, 100, 10, 'YAAA007', 'Physical'),
('MAAA005', 'Tackle', 40, 100, 35, 'YAAA008', 'Physical'),
('MAAA006', 'Hydro Pump', 110, 80, 5, 'YAAA002', 'Special'),
('MAAA007', 'Psychic', 90, 100, 10, 'YAAA005', 'Special'),
('MAAA008', 'Wing Attack', 60, 100, 35, 'YAAA009', 'Physical'),
('MAAA009', 'Dragon Claw', 80, 100, 15, 'YAAA010', 'Physical'),
('MAAA010', 'Shadow Ball', 80, 100, 15, 'YAAA011', 'Special'),
('MAAA011', 'Karate Chop', 50, 100, 25, 'YAAA012', 'Physical'),
('MAAA012', 'Quick Attack', 40, 100, 30, 'YAAA008', 'Physical'),
('MAAA013', 'Razor Leaf', 55, 95, 25, 'YAAA004', 'Physical'),
('MAAA014', 'Rock Throw', 50, 90, 15, 'YAAA006', 'Physical'),
('MAAA015', 'Dig', 80, 100, 10, 'YAAA007', 'Physical'),
('MAAA016', 'Swift', 60, 100, 20, 'YAAA008', 'Special'),
('MAAA017', 'Fly', 90, 95, 15, 'YAAA009', 'Physical'),
('MAAA018', 'Outrage', 120, 100, 10, 'YAAA010', 'Physical'),
('MAAA019', 'Hypnosis', 0, 60, 20, 'YAAA005', 'Status'),
('MAAA020', 'Stone Edge', 100, 80, 5, 'YAAA006', 'Physical'),
('MAAA021', 'Body Slam', 85, 100, 15, 'YAAA008', 'Physical'),
('MAAA022', 'Thunder Wave', 0, 90, 20, 'YAAA001', 'Status'),
('MAAA023', 'Will-O-Wisp', 0, 85, 15, 'YAAA003', 'Status'),
('MAAA024', 'Bulk Up', 0, 100, 20, 'YAAA012', 'Status'),
('MAAA025', 'Recover', 0, 100, 10, 'YAAA008', 'Status');

-- ============================================================
-- 2. CITIES & SPECIES
-- ============================================================

-- CITIES (Prefix C) - Expanded to 15
INSERT INTO City (city_id, city_name, region_id) VALUES
('CAAA001', 'Pallet Town', 'RAAA001'),
('CAAA002', 'Cerulean City', 'RAAA001'),
('CAAA003', 'Pewter City', 'RAAA001'),
('CAAA004', 'Vermilion City', 'RAAA001'),
('CAAA005', 'Lavender Town', 'RAAA001'),
('CAAA006', 'Celadon City', 'RAAA001'),
('CAAA007', 'Fuchsia City', 'RAAA001'),
('CAAA008', 'Saffron City', 'RAAA001'),
('CAAA009', 'Cinnabar Island', 'RAAA001'),
('CAAA010', 'Viridian City', 'RAAA001'),
('CAAA011', 'New Bark Town', 'RAAA002'),
('CAAA012', 'Cherrygrove City', 'RAAA002'),
('CAAA013', 'Violet City', 'RAAA002'),
('CAAA014', 'Goldenrod City', 'RAAA002'),
('CAAA015', 'Ecruteak City', 'RAAA002');

-- POKEMON SPECIES (Prefix S) - Expanded to 25
INSERT INTO PokemonSpecies (species_id, species_name, base_hp, base_attack, base_defense, base_speed, primary_type_id, secondary_type_id) VALUES
('SAAA001', 'Pikachu', 35, 55, 40, 90, 'YAAA001', NULL),
('SAAA002', 'Squirtle', 44, 48, 65, 43, 'YAAA002', NULL),
('SAAA003', 'Charmander', 39, 52, 43, 65, 'YAAA003', NULL),
('SAAA004', 'Bulbasaur', 45, 49, 49, 45, 'YAAA004', NULL),
('SAAA005', 'Onix', 35, 45, 160, 70, 'YAAA006', 'YAAA007'),
('SAAA006', 'Staryu', 30, 45, 55, 85, 'YAAA002', NULL),
('SAAA007', 'Pidgey', 40, 45, 40, 56, 'YAAA008', 'YAAA009'),
('SAAA008', 'Rattata', 30, 56, 35, 72, 'YAAA008', NULL),
('SAAA009', 'Geodude', 40, 80, 100, 20, 'YAAA006', 'YAAA007'),
('SAAA010', 'Machop', 70, 80, 50, 35, 'YAAA012', NULL),
('SAAA011', 'Abra', 25, 20, 15, 90, 'YAAA005', NULL),
('SAAA012', 'Gastly', 30, 35, 30, 80, 'YAAA011', 'YAAA015'),
('SAAA013', 'Dratini', 41, 64, 45, 50, 'YAAA010', NULL),
('SAAA014', 'Magikarp', 20, 10, 55, 80, 'YAAA002', NULL),
('SAAA015', 'Eevee', 55, 55, 50, 55, 'YAAA008', NULL),
('SAAA016', 'Snorlax', 160, 110, 65, 30, 'YAAA008', NULL),
('SAAA017', 'Mewtwo', 106, 110, 90, 130, 'YAAA005', NULL),
('SAAA018', 'Gyarados', 95, 125, 79, 81, 'YAAA002', 'YAAA009'),
('SAAA019', 'Arcanine', 90, 110, 80, 95, 'YAAA003', NULL),
('SAAA020', 'Exeggutor', 95, 95, 85, 55, 'YAAA004', 'YAAA005'),
('SAAA021', 'Jigglypuff', 115, 45, 20, 20, 'YAAA008', NULL),
('SAAA022', 'Meowth', 40, 45, 35, 90, 'YAAA008', NULL),
('SAAA023', 'Psyduck', 50, 52, 48, 55, 'YAAA002', NULL),
('SAAA024', 'Growlithe', 55, 70, 45, 60, 'YAAA003', NULL),
('SAAA025', 'Mankey', 40, 80, 35, 70, 'YAAA012', NULL);

-- Link Species to Abilities
INSERT INTO PokemonSpeciesAbility (species_id, ability_id) VALUES
('SAAA001', 'AAAA001'), -- Pikachu Static
('SAAA002', 'AAAA002'), -- Squirtle Torrent
('SAAA003', 'AAAA003'), -- Charmander Blaze
('SAAA004', 'AAAA004'), -- Bulbasaur Overgrow
('SAAA005', 'AAAA006'), -- Onix Intimidate (using filler logic)
('SAAA006', 'AAAA009'), -- Staryu Synchronize (filler)
('SAAA007', 'AAAA007'), -- Pidgey Keen Eye
('SAAA008', 'AAAA008'), -- Rattata Guts
('SAAA009', 'AAAA006'), -- Geodude Intimidate (filler)
('SAAA010', 'AAAA008'), -- Machop Guts
('SAAA011', 'AAAA009'), -- Abra Synchronize
('SAAA012', 'AAAA005'), -- Gastly Levitate
('SAAA013', 'AAAA009'), -- Dratini
('SAAA014', 'AAAA002'), -- Magikarp
('SAAA015', 'AAAA008'), -- Eevee
('SAAA016', 'AAAA006'), -- Snorlax
('SAAA017', 'AAAA010'), -- Mewtwo Pressure
('SAAA018', 'AAAA006'), -- Gyarados Intimidate
('SAAA019', 'AAAA006'), -- Arcanine Intimidate
('SAAA020', 'AAAA004'), -- Exeggutor
('SAAA021', 'AAAA001'), -- Jigglypuff
('SAAA022', 'AAAA007'), -- Meowth
('SAAA023', 'AAAA002'), -- Psyduck
('SAAA024', 'AAAA006'), -- Growlithe
('SAAA025', 'AAAA008'); -- Mankey

-- ============================================================
-- 3. PEOPLE (Trainers, Leaders, Champions)
-- ============================================================

-- TRAINERS (Prefix T) - Expanded to 25
INSERT INTO Trainer (trainer_id, name, gender, birth_date, contact_info_email, contact_info_phone, region_id) VALUES
('TAAA001', 'Ash Ketchum', 'Male', '2010-05-22', 'ash@kanto.com', '555-0101', 'RAAA001'),
('TAAA002', 'Misty Waterflower', 'Female', '2008-11-15', 'misty@cerulean.gym', '555-0102', 'RAAA001'),
('TAAA003', 'Brock Stone', 'Male', '2006-03-10', 'brock@pewter.gym', '555-0103', 'RAAA001'),
('TAAA004', 'Lt. Surge', 'Male', '1985-07-04', 'surge@vermilion.gym', '555-0104', 'RAAA001'),
('TAAA005', 'Gary Oak', 'Male', '2010-06-01', 'gary@oaklab.com', '555-0105', 'RAAA001'),
('TAAA006', 'Erika Nature', 'Female', '2000-08-15', 'erika@celadon.gym', '555-0106', 'RAAA001'),
('TAAA007', 'Koga Ninja', 'Male', '1975-02-20', 'koga@fuchsia.gym', '555-0107', 'RAAA001'),
('TAAA008', 'Sabrina Psi', 'Female', '2002-11-01', 'sabrina@saffron.gym', '555-0108', 'RAAA001'),
('TAAA009', 'Blaine Hothead', 'Male', '1960-09-09', 'blaine@cinnabar.gym', '555-0109', 'RAAA001'),
('TAAA010', 'Giovanni Rocket', 'Male', '1970-01-01', 'gio@viridian.gym', '555-0110', 'RAAA001'),
('TAAA011', 'Lorelei Ice', 'Female', '1990-12-25', 'lorelei@league.com', '555-0111', 'RAAA001'),
('TAAA012', 'Bruno Fight', 'Male', '1985-05-05', 'bruno@league.com', '555-0112', 'RAAA001'),
('TAAA013', 'Agatha Ghost', 'Female', '1950-10-31', 'agatha@league.com', '555-0113', 'RAAA001'),
('TAAA014', 'Lance Dragon', 'Male', '1992-04-01', 'lance@league.com', '555-0114', 'RAAA001'),
('TAAA015', 'Red Master', 'Male', '2009-08-08', 'red@mt.silver', '555-0115', 'RAAA001'),
('TAAA016', 'Blue Oak', 'Male', '2009-11-22', 'blue@gym.com', '555-0116', 'RAAA001'),
('TAAA017', 'Leaf Green', 'Female', '2009-06-01', 'leaf@town.com', '555-0117', 'RAAA001'),
('TAAA018', 'Youngster Joey', 'Male', '2015-01-15', 'joey@rattata.com', '555-0118', 'RAAA002'),
('TAAA019', 'Lass Sally', 'Female', '2014-03-12', 'sally@school.com', '555-0119', 'RAAA002'),
('TAAA020', 'Bug Catcher Wade', 'Male', '2016-07-07', 'wade@forest.com', '555-0120', 'RAAA002'),
('TAAA021', 'Hiker Anthony', 'Male', '1980-05-20', 'anthony@mtmoon.com', '555-0121', 'RAAA001'),
('TAAA022', 'Swimmer Amanda', 'Female', '2005-08-30', 'amanda@pool.com', '555-0122', 'RAAA001'),
('TAAA023', 'Team Rocket Grunt A', 'Male', '2000-01-01', 'gruntA@rocket.net', '555-0123', 'RAAA001'),
('TAAA024', 'Team Rocket Grunt B', 'Female', '2001-02-02', 'gruntB@rocket.net', '555-0124', 'RAAA001'),
('TAAA025', 'Professor Oak', 'Male', '1955-10-10', 'prof@oaklab.com', '555-0125', 'RAAA001');

-- GYM LEADERS (Reference Trainers) - Expanded to 8 Kanto Leaders
INSERT INTO GymLeader (leader_id, specialty_type_id, years_of_experience) VALUES
('TAAA002', 'YAAA002', 5),  -- Misty
('TAAA003', 'YAAA006', 8),  -- Brock
('TAAA004', 'YAAA001', 15), -- Surge
('TAAA006', 'YAAA004', 6),  -- Erika
('TAAA007', 'YAAA015', 20), -- Koga
('TAAA008', 'YAAA005', 10), -- Sabrina
('TAAA009', 'YAAA003', 30), -- Blaine
('TAAA010', 'YAAA007', 25); -- Giovanni

-- CHAMPIONS (Reference Trainers)
INSERT INTO Champion (champion_id, title_year) VALUES
('TAAA005', 2024), -- Gary
('TAAA014', 2023); -- Lance

-- ============================================================
-- 4. GYMS & SEASONS
-- ============================================================

-- GYMS (Prefix G) - Expanded to 8 Kanto Gyms
INSERT INTO Gym (gym_id, gym_name, city_id, specialization_type_id) VALUES
('GAAA001', 'Pewter Gym', 'CAAA003', 'YAAA006'),
('GAAA002', 'Cerulean Gym', 'CAAA002', 'YAAA002'),
('GAAA003', 'Vermilion Gym', 'CAAA004', 'YAAA001'),
('GAAA004', 'Celadon Gym', 'CAAA006', 'YAAA004'),
('GAAA005', 'Fuchsia Gym', 'CAAA007', 'YAAA015'),
('GAAA006', 'Saffron Gym', 'CAAA008', 'YAAA005'),
('GAAA007', 'Cinnabar Gym', 'CAAA009', 'YAAA003'),
('GAAA008', 'Viridian Gym', 'CAAA010', 'YAAA007');

-- BADGE NAMES
INSERT INTO GymBadgeName (gym_id, badge_name) VALUES
('GAAA001', 'Boulder Badge'),
('GAAA002', 'Cascade Badge'),
('GAAA003', 'Thunder Badge'),
('GAAA004', 'Rainbow Badge'),
('GAAA005', 'Soul Badge'),
('GAAA006', 'Marsh Badge'),
('GAAA007', 'Volcano Badge'),
('GAAA008', 'Earth Badge');

-- LEAGUE SEASON (Prefix L)
INSERT INTO LeagueSeason (season_id, year, region_id, theme) VALUES
('LAAA001', 2025, 'RAAA001', 'Indigo Plateau Challenge');

-- GYM SEASON REGISTRY (Prefix E - Enrollment/Entry) - Linking Leaders to Gyms
INSERT INTO GymSeasonRegistry (registry_id, season_id, gym_id, leader_id) VALUES
('EAAA001', 'LAAA001', 'GAAA001', 'TAAA003'), -- Brock @ Pewter
('EAAA002', 'LAAA001', 'GAAA002', 'TAAA002'), -- Misty @ Cerulean
('EAAA003', 'LAAA001', 'GAAA003', 'TAAA004'), -- Surge @ Vermilion
('EAAA004', 'LAAA001', 'GAAA004', 'TAAA006'), -- Erika @ Celadon
('EAAA005', 'LAAA001', 'GAAA005', 'TAAA007'), -- Koga @ Fuchsia
('EAAA006', 'LAAA001', 'GAAA006', 'TAAA008'), -- Sabrina @ Saffron
('EAAA007', 'LAAA001', 'GAAA007', 'TAAA009'), -- Blaine @ Cinnabar
('EAAA008', 'LAAA001', 'GAAA008', 'TAAA010'); -- Giovanni @ Viridian

-- ============================================================
-- 5. POKEMON INSTANCES
-- ============================================================

-- REGISTERED POKEMON (Prefix P) - Expanded to 25+
INSERT INTO RegisteredPokemon (pokemon_id, species_id, trainer_id, nickname, level, experience_points, registration_date) VALUES
('PAAA001', 'SAAA001', 'TAAA001', 'Sparky', 35, 8000, '2024-01-10'), -- Ash's Pikachu
('PAAA002', 'SAAA002', 'TAAA001', 'Squirt', 20, 3000, '2024-02-15'), -- Ash's Squirtle
('PAAA003', 'SAAA003', 'TAAA001', 'Char', 22, 3500, '2024-02-20'), -- Ash's Charmander
('PAAA004', 'SAAA004', 'TAAA001', 'Bulba', 21, 3200, '2024-02-10'), -- Ash's Bulbasaur
('PAAA005', 'SAAA007', 'TAAA001', 'Birdy', 18, 2000, '2024-01-15'), -- Ash's Pidgey
('PAAA006', 'SAAA006', 'TAAA002', 'Star', 28, 5600, '2023-05-20'), -- Misty's Staryu
('PAAA007', 'SAAA023', 'TAAA002', 'Duck', 25, 4000, '2023-06-01'), -- Misty's Psyduck
('PAAA008', 'SAAA005', 'TAAA003', 'Rocky', 30, 6200, '2023-01-10'), -- Brock's Onix
('PAAA009', 'SAAA009', 'TAAA003', 'Geo', 15, 1500, '2023-01-15'), -- Brock's Geodude
('PAAA010', 'SAAA001', 'TAAA004', 'Zap', 45, 15000, '2020-08-15'), -- Surge's Pikachu/Raichu
('PAAA011', 'SAAA015', 'TAAA005', 'Vee', 25, 5000, '2024-01-01'), -- Gary's Eevee
('PAAA012', 'SAAA002', 'TAAA005', 'Blaster', 40, 12000, '2024-01-01'), -- Gary's Squirtle/Wartortle
('PAAA013', 'SAAA020', 'TAAA006', 'Egg', 35, 9000, '2022-03-15'), -- Erika's Exeggutor
('PAAA014', 'SAAA025', 'TAAA012', 'Punch', 50, 20000, '2020-01-01'), -- Bruno's Mankey/Primeape
('PAAA015', 'SAAA013', 'TAAA014', 'Wyrm', 55, 25000, '2019-01-01'), -- Lance's Dratini/Dragonair
('PAAA016', 'SAAA016', 'TAAA015', 'Sleepy', 60, 30000, '2018-01-01'), -- Red's Snorlax
('PAAA017', 'SAAA008', 'TAAA018', 'TopPercent', 10, 500, '2025-01-01'), -- Joey's Rattata
('PAAA018', 'SAAA021', 'TAAA019', 'Song', 12, 600, '2025-01-05'), -- Lass's Jigglypuff
('PAAA019', 'SAAA022', 'TAAA023', 'Payday', 18, 1800, '2024-12-01'), -- Grunt's Meowth
('PAAA020', 'SAAA012', 'TAAA013', 'Spook', 52, 22000, '2010-01-01'), -- Agatha's Gastly/Gengar
('PAAA021', 'SAAA017', 'TAAA010', 'Genetic', 70, 50000, '2025-01-01'), -- Giovanni's Mewtwo
('PAAA022', 'SAAA024', 'TAAA009', 'Pup', 42, 14000, '2021-06-01'), -- Blaine's Growlithe
('PAAA023', 'SAAA011', 'TAAA008', 'Mind', 45, 16000, '2021-07-01'), -- Sabrina's Abra/Kadabra
('PAAA024', 'SAAA010', 'TAAA021', 'Chop', 22, 2200, '2024-09-01'), -- Hiker's Machop
('PAAA025', 'SAAA014', 'TAAA022', 'Splash', 5, 100, '2025-02-01'); -- Swimmer's Magikarp

-- POKEMON MOVES (Simplified linkage)
INSERT INTO RegisteredPokemonMove (pokemon_id, move_id) VALUES
('PAAA001', 'MAAA001'), ('PAAA001', 'MAAA012'), -- Ash's Pikachu: Thunderbolt, Quick Attack
('PAAA002', 'MAAA006'), ('PAAA002', 'MAAA005'), -- Squirtle: Hydro Pump, Tackle
('PAAA003', 'MAAA003'), ('PAAA003', 'MAAA014'), -- Charmander: Flamethrower, Rock Throw (filler)
('PAAA004', 'MAAA013'), ('PAAA004', 'MAAA005'), -- Bulbasaur: Razor Leaf, Tackle
('PAAA005', 'MAAA008'), -- Pidgey: Wing Attack
('PAAA006', 'MAAA002'), -- Staryu: Surf
('PAAA007', 'MAAA007'), -- Psyduck: Psychic
('PAAA008', 'MAAA004'), -- Onix: Earthquake
('PAAA009', 'MAAA014'), -- Geodude: Rock Throw
('PAAA010', 'MAAA001'), -- Surge's Raichu: Thunderbolt
('PAAA021', 'MAAA007'), ('PAAA021', 'MAAA010'); -- Mewtwo: Psychic, Shadow Ball

-- ============================================================
-- 6. BATTLES, TOURNAMENTS, BADGES
-- ============================================================

-- GYM BATTLES (Prefix B) - Expanded to 25
INSERT INTO GymBattle (battle_id, challenger_id, gym_id, leader_id, battle_date, result) VALUES
('BAAA001', 'TAAA001', 'GAAA001', 'TAAA003', '2025-03-01', 'Loss'), -- Ash vs Brock
('BAAA002', 'TAAA001', 'GAAA001', 'TAAA003', '2025-03-03', 'Win'),  -- Ash vs Brock Rematch
('BAAA003', 'TAAA001', 'GAAA002', 'TAAA002', '2025-03-10', 'Win'),  -- Ash vs Misty
('BAAA004', 'TAAA001', 'GAAA003', 'TAAA004', '2025-03-20', 'Loss'), -- Ash vs Surge
('BAAA005', 'TAAA001', 'GAAA003', 'TAAA004', '2025-03-25', 'Win'),  -- Ash vs Surge Rematch
('BAAA006', 'TAAA001', 'GAAA004', 'TAAA006', '2025-04-05', 'Win'),  -- Ash vs Erika
('BAAA007', 'TAAA005', 'GAAA001', 'TAAA003', '2025-02-01', 'Win'),  -- Gary vs Brock
('BAAA008', 'TAAA005', 'GAAA002', 'TAAA002', '2025-02-15', 'Win'),  -- Gary vs Misty
('BAAA009', 'TAAA005', 'GAAA003', 'TAAA004', '2025-03-01', 'Win'),  -- Gary vs Surge
('BAAA010', 'TAAA015', 'GAAA008', 'TAAA010', '2024-12-01', 'Win'),  -- Red vs Giovanni
('BAAA011', 'TAAA018', 'GAAA001', 'TAAA003', '2025-05-01', 'Loss'), -- Joey vs Brock
('BAAA012', 'TAAA018', 'GAAA001', 'TAAA003', '2025-05-10', 'Loss'), -- Joey vs Brock again
('BAAA013', 'TAAA017', 'GAAA001', 'TAAA003', '2025-04-01', 'Win'),  -- Leaf vs Brock
('BAAA014', 'TAAA017', 'GAAA002', 'TAAA002', '2025-04-15', 'Win'),  -- Leaf vs Misty
('BAAA015', 'TAAA016', 'GAAA001', 'TAAA003', '2025-01-10', 'Win'),  -- Blue vs Brock
('BAAA016', 'TAAA023', 'GAAA001', 'TAAA003', '2025-06-01', 'Loss'), -- Grunt vs Brock
('BAAA017', 'TAAA001', 'GAAA005', 'TAAA007', '2025-04-20', 'Win'),  -- Ash vs Koga
('BAAA018', 'TAAA001', 'GAAA006', 'TAAA008', '2025-05-01', 'Loss'), -- Ash vs Sabrina
('BAAA019', 'TAAA001', 'GAAA006', 'TAAA008', '2025-05-05', 'Win'),  -- Ash vs Sabrina Rematch
('BAAA020', 'TAAA001', 'GAAA007', 'TAAA009', '2025-05-20', 'Win'),  -- Ash vs Blaine
('BAAA021', 'TAAA001', 'GAAA008', 'TAAA010', '2025-06-01', 'Win'),  -- Ash vs Giovanni (or placeholder)
('BAAA022', 'TAAA015', 'GAAA007', 'TAAA009', '2024-11-01', 'Win'),  -- Red vs Blaine
('BAAA023', 'TAAA005', 'GAAA008', 'TAAA010', '2025-04-01', 'Win'),  -- Gary vs Giovanni
('BAAA024', 'TAAA016', 'GAAA008', 'TAAA010', '2025-04-05', 'Win'),  -- Blue vs Giovanni
('BAAA025', 'TAAA017', 'GAAA003', 'TAAA004', '2025-04-20', 'Win');  -- Leaf vs Surge

-- EARNED BADGES (Corresponding to Wins above)
INSERT INTO GymBadge (gym_id, badge_number, date_earned, trainer_id) VALUES
('GAAA001', 1, '2025-03-03', 'TAAA001'), -- Ash Boulder
('GAAA002', 2, '2025-03-10', 'TAAA001'), -- Ash Cascade
('GAAA003', 3, '2025-03-25', 'TAAA001'), -- Ash Thunder
('GAAA004', 4, '2025-04-05', 'TAAA001'), -- Ash Rainbow
('GAAA001', 1, '2025-02-01', 'TAAA005'), -- Gary Boulder
('GAAA002', 2, '2025-02-15', 'TAAA005'), -- Gary Cascade
('GAAA003', 3, '2025-03-01', 'TAAA005'), -- Gary Thunder
('GAAA001', 1, '2025-01-10', 'TAAA016'), -- Blue Boulder
('GAAA001', 1, '2025-04-01', 'TAAA017'); -- Leaf Boulder

-- TOURNAMENT (Prefix O)
INSERT INTO Tournament (tournament_id, tournament_name, start_date, end_date, city_id, season_id) VALUES
('OAAA001', 'Indigo Conference', '2025-12-01', '2025-12-15', 'CAAA001', 'LAAA001'),
('OAAA002', 'Silver Conference', '2026-12-01', '2026-12-15', 'CAAA011', 'LAAA001');

-- TOURNAMENT ENTRY
INSERT INTO TournamentEntry (tournament_id, trainer_id, registration_date) VALUES
('OAAA001', 'TAAA001', '2025-11-01'), -- Ash
('OAAA001', 'TAAA005', '2025-11-02'), -- Gary
('OAAA001', 'TAAA015', '2025-11-01'), -- Red
('OAAA001', 'TAAA016', '2025-11-03'); -- Blue

-- MATCHES
INSERT INTO Match_Table (tournament_id, match_number, trainer1_id, trainer2_id, winner_id, match_date, round_number) VALUES
('OAAA001', 1, 'TAAA001', 'TAAA005', 'TAAA001', '2025-12-05', 1), -- Ash vs Gary (Ash wins)
('OAAA001', 2, 'TAAA015', 'TAAA016', 'TAAA015', '2025-12-05', 1), -- Red vs Blue (Red wins)
('OAAA001', 3, 'TAAA001', 'TAAA015', 'TAAA015', '2025-12-10', 2); -- Ash vs Red (Red wins)