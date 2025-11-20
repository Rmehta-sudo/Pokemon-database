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
    ("Unova", "Castelia City"), ("Kalos", "Lumiose City"),
    ("Alola", "Hau'oli City"), ("Galar", "Wyndon")
]

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

ABILITIES = ["Overgrow", "Blaze", "Torrent", "Static", "Levitate", "Intimidate", "Pressure", "Inner Focus", "Sand Stream", "Drought"]

# --- NEW: Meaningful Names for Gyms, Badges, Tournaments, Cities ---

# (Gym Name, Type, Badge Name)
GYM_LORE_DATA = [
    ("Pewter City Gym", "Rock", "Boulder Badge"),
    ("Cerulean City Gym", "Water", "Cascade Badge"),
    ("Vermilion City Gym", "Electric", "Thunder Badge"),
    ("Celadon City Gym", "Grass", "Rainbow Badge"),
    ("Fuchsia City Gym", "Poison", "Soul Badge"),
    ("Saffron City Gym", "Psychic", "Marsh Badge"),
    ("Cinnabar Island Gym", "Fire", "Volcano Badge"),
    ("Viridian City Gym", "Ground", "Earth Badge"),
    ("Violet City Gym", "Flying", "Zephyr Badge"),
    ("Azalea Town Gym", "Bug", "Hive Badge"),
    ("Goldenrod City Gym", "Normal", "Plain Badge"),
    ("Ecruteak City Gym", "Ghost", "Fog Badge")
]

TOURNAMENT_NAMES = [
    "Indigo Plateau Conference",
    "Silver Conference",
    "Ever Grande Conference",
    "Lily of the Valley Conference",
    "Vertress Conference",
    "Lumiose Conference",
    "Manalo Conference",
    "Masters Eight Tournament",
    "Coronation Series Finals",
    "World Pokemon Cup"
]

# Fallback city names if Faker isn't used or to mix in lore names
LORE_CITIES = [
    "Pallet Town", "Viridian City", "Lavender Town", "Celadon City", "Fuchsia City",
    "Cinnabar Island", "New Bark Town", "Cherrygrove City", "Violet City", "Azalea Town",
    "Ecruteak City", "Olivine City", "Cianwood City", "Mahogany Town", "Blackthorn City"
]

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
        
        # FIX: Use Faker, or fallback to Lore Cities, or Generic
        if fake:
            cname = fake.city()
        elif i <= len(LORE_CITIES):
            cname = LORE_CITIES[i-1]
        else:
            cname = f"CityLocation{i}"
            
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

    # TypeStrength & Weakness
    for tid in ids["type"]:
        # 2 types it is strong against
        targets = random.sample(ids["type"], 2)
        for t in targets:
            if t != tid:
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
    for i in range(1, NUM_TRAINERS + 1):
        if fake:
            tname = fake.name()
        else:
            tname = f"Ace Trainer {i}" # FIX: Better than "Trainer1"
        
        # 1. Sanitize Name for ID/Email
        raw_fname = tname.split()[0]
        clean_fname = "".join(c for c in raw_fname if c.isalnum())
        
        tid = get_id("T", clean_fname, i)
        ids["trainer"].append(tid)
        
        gender = random.choice(['Male', 'Female', 'Other'])
        
        if fake:
            bdate_obj = fake.date_of_birth(minimum_age=15, maximum_age=70)
            bdate = bdate_obj.isoformat()
        else:
            bdate = random_date_in_years(1985, 2008)
        
        email = f"{clean_fname}{i}@pokemail.com"
        phone = f"555-{i:04d}" 
        rid = random.choice(ids["region"])
        
        f.write(f"INSERT INTO Trainer VALUES ({escape_sql(tid)}, {escape_sql(tname)}, {escape_sql(gender)}, {escape_sql(bdate)}, {escape_sql(email)}, {escape_sql(phone)}, {escape_sql(rid)});\n")

    # LeagueSeason
    for i in range(1, 6):
        sid = get_id("L", "SEASON", i)
        ids["season"].append(sid)
        rid = ids["region"][i-1] if i-1 < len(ids["region"]) else ids["region"][0]
        f.write(f"INSERT INTO LeagueSeason VALUES ({escape_sql(sid)}, {2020+i}, {escape_sql(rid)}, 'Official League Circuit');\n")

    # =====================================================
    # LEVEL 2
    # =====================================================
    f.write("\n-- LEVEL 2: Dependent on Level 1\n")

    # PokemonSpeciesAbility
    for s_obj in ids["species"]:
        sid = s_obj["id"]
        aid = random.choice(ids["ability"])
        f.write(f"INSERT IGNORE INTO PokemonSpeciesAbility VALUES ({escape_sql(sid)}, {escape_sql(aid)});\n")

    # Gym & GymLeader (FIXED NAMES)
    gym_counter = 0
    # We use the first few cities for the gyms
    available_cities = ids["city"][:len(GYM_LORE_DATA)]
    
    for i, city_id in enumerate(available_cities):
        # Get Lore Data
        g_name, g_type_name, g_badge_name = GYM_LORE_DATA[i]
        
        gid = get_id("G", g_name, i+1)
        ids["gym"].append({"id": gid, "city": city_id})
        
        # Find the Type ID
        try:
            type_idx = TYPES.index(g_type_name)
            spec_type_id = ids["type"][type_idx]
        except ValueError:
            # Fallback if type mismatch
            spec_type_id = ids["type"][0]

        f.write(f"INSERT INTO Gym VALUES ({escape_sql(gid)}, {escape_sql(g_name)}, {escape_sql(city_id)}, {escape_sql(spec_type_id)});\n")
        
        # Assign Leader (reuse trainer)
        lid = ids["trainer"][i] 
        ids["leader"].append({"lid": lid, "gid": gid})
        f.write(f"INSERT INTO GymLeader VALUES ({escape_sql(lid)}, {escape_sql(spec_type_id)}, {random.randint(1,10)});\n")
        
        # Badge Name
        f.write(f"INSERT INTO GymBadgeName VALUES ({escape_sql(gid)}, {escape_sql(g_badge_name)});\n")
        
        gym_counter += 1

    # Champion
    for i in range(1, 4):
        champ_id = ids["trainer"][-i] 
        f.write(f"INSERT INTO Champion VALUES ({escape_sql(champ_id)}, {2020+i});\n")

    # RegisteredPokemon
    for i in range(1, NUM_POKEMON + 1):
        pid = get_id("P", "POKE", i)
        ids["pokemon"].append(pid)
        spec_obj = random.choice(ids["species"])
        spec_id = spec_obj["id"]
        trainer_id = random.choice(ids["trainer"])
        
        # Nickname
        if fake:
            nickname = fake.first_name()
        else:
            nickname = f"Buddy{i}"
            
        if random.random() > 0.7: 
            nickname = "NULL" 
        else: 
            nickname = f"'{nickname}'"

        level = random.randint(5, 100)
        exp = level * 100
        reg_date = random_date_in_years(2020, 2025)
        f.write(f"INSERT INTO RegisteredPokemon VALUES ({escape_sql(pid)}, {escape_sql(spec_id)}, {escape_sql(trainer_id)}, {nickname}, {level}, {exp}, {escape_sql(reg_date)});\n")

    # Tournament (FIXED NAMES)
    for i in range(1, 6):
        tr_id = get_id("O", "TOURN", i)
        cid = random.choice(ids["city"])
        sid = random.choice(ids["season"])
        
        # Use meaningful names
        if i <= len(TOURNAMENT_NAMES):
            t_name = TOURNAMENT_NAMES[i-1]
        else:
            t_name = f"Regional Cup {i}"
            
        start_date = random_date_in_years(2023, 2025)
        sd_obj = datetime.date.fromisoformat(start_date)
        end_obj = sd_obj + datetime.timedelta(days=random.randint(3, 10))
        end_date = end_obj.isoformat()
        
        ids["tournament"].append({"id": tr_id, "start": start_date, "end": end_date, "city": cid, "season": sid})
        f.write(f"INSERT INTO Tournament VALUES ({escape_sql(tr_id)}, {escape_sql(t_name)}, {escape_sql(start_date)}, {escape_sql(end_date)}, {escape_sql(cid)}, {escape_sql(sid)});\n")

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

    # GymSeasonRegistry
    registry_count = 1
    for season in ids["season"]:
        for g_obj in ids["leader"]:
            rid = get_id("E", "REG", registry_count)
            f.write(f"INSERT INTO GymSeasonRegistry VALUES ({escape_sql(rid)}, {escape_sql(season)}, {escape_sql(g_obj['gid'])}, {escape_sql(g_obj['lid'])});\n")
            registry_count += 1

    # GymBattle & GymBadge
    battle_count = 1
    badge_counters = {}
    for i in range(50): 
        g_obj = random.choice(ids["leader"]) 
        gid = g_obj['gid']
        leader_id = g_obj['lid']
        
        challenger = random.choice(ids["trainer"])
        while challenger == leader_id:
            challenger = random.choice(ids["trainer"])
            
        bid = get_id("B", "BATTLE", battle_count)
        result = random.choice(['Win', 'Loss', 'Draw'])
        battle_date = random_date_in_years(2022, 2025)
        f.write(f"INSERT INTO GymBattle VALUES ({escape_sql(bid)}, {escape_sql(challenger)}, {escape_sql(gid)}, {escape_sql(leader_id)}, {escape_sql(battle_date)}, {escape_sql(result)});\n")
        
        if result == 'Win':
            badge_number = badge_counters.get(gid, 0) + 1
            badge_counters[gid] = badge_number
            f.write(
                "INSERT IGNORE INTO GymBadge (gym_id, badge_number, date_earned, trainer_id) "
                f"VALUES ({escape_sql(gid)}, {badge_number}, {escape_sql(battle_date)}, {escape_sql(challenger)});\n"
            )
        
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
        
        entry_window_start = start_dt - datetime.timedelta(days=30)
        for p in participants:
            entry_date = random_date_between(entry_window_start, start_dt)
            f.write(f"INSERT IGNORE INTO TournamentEntry VALUES ({escape_sql(tourn_id)}, {escape_sql(p)}, {escape_sql(entry_date)});\n")
        
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

print(f"Successfully generated {FILE_NAME} covering all 23 tables with meaningful names.")