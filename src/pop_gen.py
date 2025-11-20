import random
import datetime

# Try to import faker, else fallback
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None

# ---------------------------------------------------------
# CONFIGURATION & CONSTANTS
# ---------------------------------------------------------
NUM_TRAINERS = 150
NUM_POKEMON = 700
NUM_MATCHES = 1200
FILE_NAME = "populate.sql"

# Real World Data for Coherence
REGIONS = [
    ("Kanto", "Saffron City"), ("Johto", "Goldenrod City"), 
    ("Hoenn", "Mauville City"), ("Sinnoh", "Jubilife City"), 
    ("Unova", "Castelia City"), ("Kalos", "Lumiose City")
]

# ADDED 'Dark' to fix your error
TYPES = [
    "Normal", "Fire", "Water", "Grass", "Electric", "Ice", 
    "Fighting", "Poison", "Ground", "Flying", "Psychic", 
    "Bug", "Rock", "Ghost", "Dragon", "Steel", "Fairy", "Dark"
]

# (Name, HP, Atk, Def, Spd, Type1, Type2)
SPECIES_DATA = [
    ("Bulbasaur", 45, 49, 49, 45, "Grass", "Poison"),
    ("Charmander", 39, 52, 43, 65, "Fire", None),
    ("Squirtle", 44, 48, 65, 43, "Water", None),
    ("Pikachu", 35, 55, 40, 90, "Electric", None),
    ("Jigglypuff", 115, 45, 20, 20, "Normal", "Fairy"),
    ("Machop", 70, 80, 50, 35, "Fighting", None),
    ("Geodude", 40, 80, 100, 20, "Rock", "Ground"),
    ("Gastly", 30, 35, 30, 80, "Ghost", "Poison"),
    ("Onix", 35, 45, 160, 70, "Rock", "Ground"),
    ("Eevee", 55, 55, 50, 55, "Normal", None),
    ("Snorlax", 160, 110, 65, 30, "Normal", None),
    ("Mewtwo", 106, 110, 90, 130, "Psychic", None),
    ("Gyarados", 95, 125, 79, 81, "Water", "Flying"),
    ("Gengar", 60, 65, 60, 110, "Ghost", "Poison"),
    ("Dragonite", 91, 134, 95, 80, "Dragon", "Flying"),
    ("Lucario", 70, 110, 70, 90, "Fighting", "Steel"),
    ("Garchomp", 108, 130, 95, 102, "Dragon", "Ground"),
    ("Gardevoir", 68, 65, 65, 80, "Psychic", "Fairy"),
    ("Greninja", 72, 95, 67, 122, "Water", "Dark"),
    ("Rayquaza", 105, 150, 90, 95, "Dragon", "Flying")
]

MOVES_DATA = [
    ("Tackle", 40, 100, 35, "Normal", "Physical"),
    ("Thunderbolt", 90, 100, 15, "Electric", "Special"),
    ("Flamethrower", 90, 100, 15, "Fire", "Special"),
    ("Hydro Pump", 110, 80, 5, "Water", "Special"),
    ("Solar Beam", 120, 100, 10, "Grass", "Special"),
    ("Earthquake", 100, 100, 10, "Ground", "Physical"),
    ("Psychic", 90, 100, 10, "Psychic", "Special"),
    ("Shadow Ball", 80, 100, 15, "Ghost", "Special"),
    ("Brick Break", 75, 100, 15, "Fighting", "Physical"),
    ("Ice Beam", 90, 100, 10, "Ice", "Special"),
    ("Hyper Beam", 150, 90, 5, "Normal", "Special"),
    ("Protect", 0, 100, 10, "Normal", "Status"),
    ("Recover", 0, 100, 10, "Normal", "Status"),
    ("Swords Dance", 0, 100, 20, "Normal", "Status")
]

ABILITIES = ["Overgrow", "Blaze", "Torrent", "Static", "Levitate", "Intimidate", "Pressure", "Inner Focus"]

BADGE_NAMES = ["Boulder", "Cascade", "Thunder", "Rainbow", "Soul", "Marsh", "Volcano", "Earth"]

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def get_id(prefix, name, index):
    """
    Generates an ID strictly matching ^Prefix[A-Z]{3,16}[0-9]{3}$
    """
    clean_name = "".join(c for c in name if c.isalpha()).upper()
    if len(clean_name) < 3:
        clean_name = (clean_name + "XXX")[:16]
    if len(clean_name) > 16:
        clean_name = clean_name[:16]
    return f"{prefix}{clean_name}{index:03d}"

def escape_sql(val):
    if val is None:
        return "NULL"
    if isinstance(val, int):
        return str(val)
    return f"'{str(val).replace("'", "''")}'"


def random_date_between(start_date, end_date):
    """Return an ISO date string between two datetime.date objects (inclusive)."""
    if isinstance(start_date, str):
        start_date = datetime.date.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = datetime.date.fromisoformat(end_date)
    delta = (end_date - start_date).days
    if delta <= 0:
        return start_date.isoformat()
    pick = random.randint(0, delta)
    return (start_date + datetime.timedelta(days=pick)).isoformat()


def random_date_in_years(start_year=2000, end_year=2025):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return random_date_between(start, end)

# Storage for Referencing IDs
ids = {
    "region": [], "type": [], "ability": [], "city": [], 
    "move": [], "species": [], "trainer": [], "season": [],
    "gym": [], "leader": [], "pokemon": [], "tournament": []
}

# ---------------------------------------------------------
# GENERATION LOGIC
# ---------------------------------------------------------

with open(FILE_NAME, "w") as f:
    f.write("-- AUTO-GENERATED POPULATION SCRIPT\n")
    f.write("USE pokemon_league_db;\n\n")
    f.write("-- Disable checks for bulk loading\n")
    f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

    # =====================================================
    # LEVEL 0
    # =====================================================
    f.write("-- LEVEL 0: Region, Type, Ability\n")
    
    for i, (rname, main_city) in enumerate(REGIONS, 1):
        rid = get_id("R", rname, i)
        ids["region"].append(rid)
        f.write(f"INSERT INTO Region VALUES ({escape_sql(rid)}, {escape_sql(rname)}, {escape_sql(main_city)});\n")

    for i, tname in enumerate(TYPES, 1):
        tid = get_id("Y", tname, i)
        ids["type"].append(tid)
        f.write(f"INSERT INTO Type VALUES ({escape_sql(tid)}, {escape_sql(tname)});\n")

    for i, aname in enumerate(ABILITIES, 1):
        aid = get_id("A", aname, i)
        ids["ability"].append(aid)
        f.write(f"INSERT INTO Ability VALUES ({escape_sql(aid)}, {escape_sql(aname)}, 'Standard effect');\n")

    # =====================================================
    # LEVEL 1
    # =====================================================
    f.write("\n-- LEVEL 1: Dependent on Level 0\n")

    # City
    for i in range(1, 60):
        region_ref = random.choice(ids["region"])
        cname = fake.city() if fake else f"CityName{i}"
        cid = get_id("C", cname, i)
        ids["city"].append(cid)
        f.write(f"INSERT INTO City VALUES ({escape_sql(cid)}, {escape_sql(cname)}, {escape_sql(region_ref)});\n")

    # Move
    for i, (mname, pwr, acc, pp, tname, cat) in enumerate(MOVES_DATA, 1):
        mid = get_id("M", mname, i)
        ids["move"].append(mid)
        type_idx = TYPES.index(tname)
        tid = ids["type"][type_idx]
        f.write(f"INSERT INTO Move VALUES ({escape_sql(mid)}, {escape_sql(mname)}, {pwr}, {acc}, {pp}, {escape_sql(tid)}, {escape_sql(cat)});\n")

    # TypeStrength & TypeWeakness (Missing in prev version)
    # Logic: Create random effectiveness (just to populate table)
    for tid in ids["type"]:
        # 2 types it is strong against
        targets = random.sample(ids["type"], 2)
        for t in targets:
            if t != tid:
                # NOTE: Using updated schema names (target_type_id)
                f.write(f"INSERT IGNORE INTO TypeStrength VALUES ({escape_sql(tid)}, {escape_sql(t)});\n")
        
        # 2 types it is weak against
        weak_targets = random.sample(ids["type"], 2)
        for wt in weak_targets:
            if wt != tid:
                f.write(f"INSERT IGNORE INTO TypeWeakness VALUES ({escape_sql(tid)}, {escape_sql(wt)});\n")

    # PokemonSpecies
    for i, data in enumerate(SPECIES_DATA, 1):
        sid = get_id("S", data[0], i)
        ids["species"].append({"id": sid, "name": data[0]})
        t1_idx = TYPES.index(data[5])
        t1_id = ids["type"][t1_idx]
        t2_id = "NULL"
        if data[6]:
            t2_idx = TYPES.index(data[6])
            t2_id = f"'{ids['type'][t2_idx]}'"
        f.write(f"INSERT INTO PokemonSpecies VALUES ({escape_sql(sid)}, {escape_sql(data[0])}, {data[1]}, {data[2]}, {data[3]}, {data[4]}, {escape_sql(t1_id)}, {t2_id});\n")

    # Trainer
    # Trainer
    for i in range(1, NUM_TRAINERS + 1):
        tname = fake.name() if fake else f"Trainer{i}"
        
        # 1. Sanitize Name for Email (Remove ' and spaces)
        raw_fname = tname.split()[0]
        clean_fname = "".join(c for c in raw_fname if c.isalnum())
        
        tid = get_id("T", clean_fname, i)
        ids["trainer"].append(tid)
        
        gender = random.choice(['Male', 'Female', 'Other'])
        # realistic birthdate: age between 15 and 70
        if fake:
            bdate_obj = fake.date_of_birth(minimum_age=15, maximum_age=70)
            bdate = bdate_obj.isoformat()
        else:
            # fallback: random date between 1955 and 2010
            bdate = random_date_in_years(1955, 2010)
        
        # 2. Unique Email via index {i} + clean name
        email = f"{clean_fname}{i}@pokemail.com"
        
        # 3. Unique Phone via index {i}
        phone = f"555-{i:04d}" 
        
        rid = random.choice(ids["region"])
        
        # This is the single, correct write statement:
        f.write(f"INSERT INTO Trainer VALUES ({escape_sql(tid)}, {escape_sql(tname)}, {escape_sql(gender)}, {escape_sql(bdate)}, {escape_sql(email)}, {escape_sql(phone)}, {escape_sql(rid)});\n")

    # LeagueSeason
    for i in range(1, 6):
        sid = get_id("L", "SEASON", i)
        ids["season"].append(sid)
        rid = ids["region"][i-1]
        f.write(f"INSERT INTO LeagueSeason VALUES ({escape_sql(sid)}, {2020+i}, {escape_sql(rid)}, 'Standard Cup');\n")

    # =====================================================
    # LEVEL 2
    # =====================================================
    f.write("\n-- LEVEL 2: Dependent on Level 1\n")

    # PokemonSpeciesAbility (New)
    for s_obj in ids["species"]:
        sid = s_obj["id"]
        # Give every species 1 random ability
        aid = random.choice(ids["ability"])
        f.write(f"INSERT IGNORE INTO PokemonSpeciesAbility VALUES ({escape_sql(sid)}, {escape_sql(aid)});\n")

    # Gym & GymLeader
    gym_counter = 1
    # First 8 cities get gyms
    for cid in ids["city"][:8]:
        gid = get_id("G", "GYM", gym_counter)
        ids["gym"].append({"id": gid, "city": cid})
        
        spec_type = random.choice(ids["type"])
        f.write(f"INSERT INTO Gym VALUES ({escape_sql(gid)}, 'Gym {gym_counter}', {escape_sql(cid)}, {escape_sql(spec_type)});\n")
        
        # Use existing trainer as leader
        lid = ids["trainer"][gym_counter] 
        ids["leader"].append({"lid": lid, "gid": gid})
        f.write(f"INSERT INTO GymLeader VALUES ({escape_sql(lid)}, {escape_sql(spec_type)}, {random.randint(1,10)});\n")
        
        # GymBadgeName (Level 3 but dependent on Gym)
        bname = BADGE_NAMES[gym_counter-1] if gym_counter <= len(BADGE_NAMES) else f"Badge {gym_counter}"
        f.write(f"INSERT INTO GymBadgeName VALUES ({escape_sql(gid)}, {escape_sql(bname)});\n")
        
        gym_counter += 1

    # Champion (New) - Pick top 3 trainers as champions
    for i in range(1, 4):
        champ_id = ids["trainer"][-i] # Pick from end of list
        cid_key = get_id("C", "CHAMP", i) # Actually Champion Table uses TrainerID as FK, but schema says champion_id. 
        # Assuming Schema: Champion(champion_id PK, ...) where champion_id is FK to Trainer? 
        # Or Champion(champion_id PK, trainer_id FK)? 
        # Prompt Schema: champion_id PRIMARY KEY REFERENCES Trainer(trainer_id). So IDs must match Trainer IDs.
        f.write(f"INSERT INTO Champion VALUES ({escape_sql(champ_id)}, {2020+i});\n")

    # RegisteredPokemon (Updated with Nicknames)
    for i in range(1, NUM_POKEMON + 1):
        pid = get_id("P", "POKE", i)
        ids["pokemon"].append(pid)
        spec_obj = random.choice(ids["species"])
        spec_id = spec_obj["id"]
        trainer_id = random.choice(ids["trainer"])
        
        # NICKNAME GENERATION
        nickname = fake.first_name() if fake else f"Poke{i}"
        if random.random() > 0.7: nickname = "NULL" # 30% no nickname
        else: nickname = f"'{nickname}'"

        level = random.randint(5, 100)
        exp = level * 100
        # registration date between 2020-01-01 and today
        reg_date = random_date_in_years(2020, datetime.date.today().year)
        f.write(f"INSERT INTO RegisteredPokemon VALUES ({escape_sql(pid)}, {escape_sql(spec_id)}, {escape_sql(trainer_id)}, {nickname}, {level}, {exp}, {escape_sql(reg_date)});\n")

    # Tournament
    for i in range(1, 6):
        tr_id = get_id("O", "TOURN", i)
        cid = random.choice(ids["city"])
        sid = random.choice(ids["season"])
        # Tournament dates: pick start in 2023-2025 and length 3-10 days
        start_date = random_date_in_years(2023, 2025)
        # compute end date relative to start
        sd_obj = datetime.date.fromisoformat(start_date)
        end_obj = sd_obj + datetime.timedelta(days=random.randint(3, 10))
        end_date = end_obj.isoformat()
        # store tournament metadata as dict so matches/entries can reference dates
        ids["tournament"].append({"id": tr_id, "start": start_date, "end": end_date, "city": cid, "season": sid})
        f.write(f"INSERT INTO Tournament VALUES ({escape_sql(tr_id)}, {escape_sql(f'Grand Prix {i}')}, {escape_sql(start_date)}, {escape_sql(end_date)}, {escape_sql(cid)}, {escape_sql(sid)});\n")

    # =====================================================
    # LEVEL 3
    # =====================================================
    f.write("\n-- LEVEL 3: Complex Intersections\n")

    # RegisteredPokemonMove
    for pid in ids["pokemon"]:
        num_moves = random.randint(1, 4)
        chosen_moves = random.sample(ids["move"], num_moves)
        for mid in chosen_moves:
            f.write(f"INSERT INTO RegisteredPokemonMove VALUES ({escape_sql(pid)}, {escape_sql(mid)});\n")

    # GymSeasonRegistry (New)
    registry_count = 1
    for season in ids["season"]:
        # Register all gyms for every season
        for g_obj in ids["leader"]: # contains {lid, gid}
            rid = get_id("E", "REG", registry_count)
            f.write(f"INSERT INTO GymSeasonRegistry VALUES ({escape_sql(rid)}, {escape_sql(season)}, {escape_sql(g_obj['gid'])}, {escape_sql(g_obj['lid'])});\n")
            registry_count += 1

    # GymBattle & GymBadge (New)
    battle_count = 1
    for i in range(50): # 50 random gym battles
        g_obj = random.choice(ids["leader"]) # {lid, gid}
        gid = g_obj['gid']
        leader_id = g_obj['lid']
        
        # Challenger cannot be the leader
        challenger = random.choice(ids["trainer"])
        while challenger == leader_id:
            challenger = random.choice(ids["trainer"])
            
        bid = get_id("B", "BATTLE", battle_count)
        result = random.choice(['Win', 'Loss', 'Draw'])
        # battle date in 2022-2025
        battle_date = random_date_in_years(2022, 2025)
        f.write(f"INSERT INTO GymBattle VALUES ({escape_sql(bid)}, {escape_sql(challenger)}, {escape_sql(gid)}, {escape_sql(leader_id)}, {escape_sql(battle_date)}, {escape_sql(result)});\n")
        
        # If Win, give Badge (Ensure unique Gym+Trainer)
        if result == 'Win':
            # IGNORE to skip duplicates if challenger beat this gym before
            # NOTE: Updated Schema for Badge PK (gym_id, trainer_id) assumed
            badge_date = battle_date
            f.write(f"INSERT IGNORE INTO GymBadge VALUES ({escape_sql(gid)}, {escape_sql(challenger)}, 1, {escape_sql(badge_date)});\n")
        
        battle_count += 1

    # TournamentEntry & Match_Table
    total_matches = 0
    for tourn in ids["tournament"]:
        tourn_id = tourn["id"]
        t_start = tourn["start"]
        t_end = tourn["end"]
        start_dt = datetime.date.fromisoformat(t_start)
        end_dt = datetime.date.fromisoformat(t_end)
        participants = random.sample(ids["trainer"], 32)
        
        # Entries
        entry_window_start = start_dt - datetime.timedelta(days=30)
        for p in participants:
            entry_date = random_date_between(entry_window_start, start_dt)
            f.write(f"INSERT IGNORE INTO TournamentEntry VALUES ({escape_sql(tourn_id)}, {escape_sql(p)}, {escape_sql(entry_date)});\n")
        
        # Matches with per-tournament numbering and multiple rounds
        match_number = 1
        num_rounds = random.randint(4, 6)
        for round_no in range(1, num_rounds + 1):
            matches_this_round = random.randint(18, 32)
            for _ in range(matches_this_round):
                if total_matches >= NUM_MATCHES:
                    break
                t1, t2 = random.sample(participants, 2)
                winner = random.choice([t1, t2])
                match_date = random_date_between(start_dt, end_dt)
                f.write(
                    f"INSERT INTO Match_Table VALUES ("
                    f"{escape_sql(tourn_id)}, {match_number}, {escape_sql(t1)}, {escape_sql(t2)}, "
                    f"{escape_sql(winner)}, {escape_sql(match_date)}, {round_no});\n"
                )
                match_number += 1
                total_matches += 1
            if total_matches >= NUM_MATCHES:
                break
        if total_matches >= NUM_MATCHES:
            break

    f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")

print(f"Successfully generated {FILE_NAME} covering all 23 tables.")