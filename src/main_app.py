import sys
import os
from getpass import getpass
from datetime import datetime
import db_utils

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================

TABLE_CONFIG = {
    # --- CORE PEOPLE & POKEMON ---
    "1": {
        "name": "Trainer", "table": "Trainer", "pk": "trainer_id", "prefix": "T",
        "columns": [
            {"col": "name", "prompt": "Trainer Name", "type": "str"},
            {"col": "gender", "prompt": "Gender", "type": "enum", "choices": ["Male", "Female", "Other"]},
            {"col": "birth_date", "prompt": "Birth Date (YYYY-MM-DD)", "type": "date"},
            {"col": "contact_info_email", "prompt": "Email", "type": "str"},
            {"col": "contact_info_phone", "prompt": "Phone", "type": "str"},
            {"col": "region_id", "prompt": "Region ID", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"}
        ]
    },
    "2": {
        "name": "Pokemon Species", "table": "PokemonSpecies", "pk": "species_id", "prefix": "S",
        "columns": [
            {"col": "species_name", "prompt": "Species Name", "type": "str"},
            {"col": "base_hp", "prompt": "Base HP", "type": "int"},
            {"col": "base_attack", "prompt": "Base Attack", "type": "int"},
            {"col": "base_defense", "prompt": "Base Defense", "type": "int"},
            {"col": "base_speed", "prompt": "Base Speed", "type": "int"},
            {"col": "primary_type_id", "prompt": "Primary Type ID", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "secondary_type_id", "prompt": "Secondary Type ID", "type": "fk", "ref_table": "Type", "ref_pk": "type_id", "optional": True},
        ]
    },
    "3": {
        "name": "Registered Pokemon", "table": "RegisteredPokemon", "pk": "pokemon_id", "prefix": "P",
        "columns": [
            {"col": "species_id", "prompt": "Species ID", "type": "fk", "ref_table": "PokemonSpecies", "ref_pk": "species_id"},
            {"col": "trainer_id", "prompt": "Owner Trainer ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "nickname", "prompt": "Nickname", "type": "str"},
            {"col": "level", "prompt": "Level (1-100)", "type": "int"},
            {"col": "experience_points", "prompt": "Current XP", "type": "int"},
            {"col": "registration_date", "prompt": "Date Caught (YYYY-MM-DD)", "type": "date"},
        ]
    },
    # --- GYMS & SEASONS ---
    "4": {
        "name": "Gym", "table": "Gym", "pk": "gym_id", "prefix": "G",
        "columns": [
            {"col": "gym_name", "prompt": "Gym Name", "type": "str"},
            {"col": "city_id", "prompt": "City ID", "type": "fk", "ref_table": "City", "ref_pk": "city_id"},
            {"col": "specialization_type_id", "prompt": "Specialty Type ID", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
        ]
    },
    "5": {
        "name": "League Season", "table": "LeagueSeason", "pk": "season_id", "prefix": "L",
        "columns": [
            {"col": "year", "prompt": "Year (YYYY)", "type": "int"},
            {"col": "region_id", "prompt": "Region ID", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"},
            {"col": "theme", "prompt": "Season Theme", "type": "str"},
        ]
    },
    "6": {
        "name": "Gym Season Registry (Assignment)", "table": "GymSeasonRegistry", "pk": "registry_id", "prefix": "E",
        "columns": [
            {"col": "season_id", "prompt": "Season ID", "type": "fk", "ref_table": "LeagueSeason", "ref_pk": "season_id"},
            {"col": "gym_id", "prompt": "Gym ID", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "leader_id", "prompt": "Leader ID", "type": "fk", "ref_table": "GymLeader", "ref_pk": "leader_id"},
        ]
    },
    # --- TOURNAMENTS ---
    "7": {
        "name": "Tournament", "table": "Tournament", "pk": "tournament_id", "prefix": "O",
        "columns": [
            {"col": "tournament_name", "prompt": "Name", "type": "str"},
            {"col": "start_date", "prompt": "Start Date", "type": "date"},
            {"col": "end_date", "prompt": "End Date", "type": "date"},
            {"col": "city_id", "prompt": "Host City ID", "type": "fk", "ref_table": "City", "ref_pk": "city_id"},
            {"col": "season_id", "prompt": "Season ID", "type": "fk", "ref_table": "LeagueSeason", "ref_pk": "season_id"},
        ]
    },
    "8": {
        "name": "Tournament Entry", "table": "TournamentEntry", "auto_pk": False,
        # Added pks list for composite key display
        "pks": ["tournament_id", "trainer_id"],
        "columns": [
            {"col": "tournament_id", "prompt": "Tournament ID", "type": "fk", "ref_table": "Tournament", "ref_pk": "tournament_id"},
            {"col": "trainer_id", "prompt": "Trainer ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "registration_date", "prompt": "Registration Date", "type": "date"},
        ]
    },
    "9": {
        "name": "Match", "table": "Match_Table", "auto_pk": False,
        # Added pks list for composite key display
        "pks": ["tournament_id", "match_number"],
        "columns": [
            {"col": "tournament_id", "prompt": "Tournament ID", "type": "fk", "ref_table": "Tournament", "ref_pk": "tournament_id"},
            {"col": "match_number", "prompt": "Match Number (Int)", "type": "int"},
            {"col": "trainer1_id", "prompt": "Trainer 1 ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "trainer2_id", "prompt": "Trainer 2 ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "winner_id", "prompt": "Winner ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "match_date", "prompt": "Date", "type": "date"},
            {"col": "round_number", "prompt": "Round", "type": "int"},
        ]
    },
    # --- BATTLES & BADGES ---
    "10": {
        "name": "Gym Battle", "table": "GymBattle", "pk": "battle_id", "prefix": "B",
        "columns": [
            {"col": "challenger_id", "prompt": "Challenger ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "gym_id", "prompt": "Gym ID", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "leader_id", "prompt": "Leader ID", "type": "fk", "ref_table": "GymLeader", "ref_pk": "leader_id"},
            {"col": "battle_date", "prompt": "Battle Date (YYYY-MM-DD)", "type": "date"},
            {"col": "result", "prompt": "Result", "type": "enum", "choices": ["Win", "Loss", "Draw"]},
        ]
    },
    "11": {
        "name": "Gym Badge (Award)", "table": "GymBadge", "auto_pk": False,
        # Added pks list for composite key display
        "pks": ["gym_id", "badge_number"],
        "columns": [
            {"col": "gym_id", "prompt": "Gym ID", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "badge_number", "prompt": "Badge Number", "type": "int"},
            {"col": "date_earned", "prompt": "Date Earned", "type": "date"},
            {"col": "trainer_id", "prompt": "Trainer ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
        ]
    },
    # --- LOOKUP TABLES ---
    "12": { "name": "Move", "table": "Move", "pk": "move_id", "prefix": "M", "columns": [ {"col": "move_name", "prompt": "Name", "type": "str"}, {"col": "power", "prompt": "Power", "type": "int"}, {"col": "accuracy", "prompt": "Accuracy", "type": "int"}, {"col": "pp", "prompt": "PP", "type": "int"}, {"col": "type_id", "prompt": "Type", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"}, {"col": "category", "prompt": "Cat", "type": "enum", "choices": ["Physical", "Special", "Status"]} ] },
    "13": { "name": "Region", "table": "Region", "pk": "region_id", "prefix": "R", "columns": [ {"col": "region_name", "prompt": "Name", "type": "str"}, {"col": "main_city", "prompt": "Main City", "type": "str"} ] },
    "14": { "name": "City", "table": "City", "pk": "city_id", "prefix": "C", "columns": [ {"col": "city_name", "prompt": "Name", "type": "str"}, {"col": "region_id", "prompt": "Region", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"} ] }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def enrich_headers(table_key, data):
    """
    Renames keys in the data dict to include (PK) and (FK) labels
    based on the TABLE_CONFIG. Supports composite primary keys.
    """
    if not data or table_key not in TABLE_CONFIG:
        return data
        
    config = TABLE_CONFIG[table_key]
    
    # Gather all PK columns (single 'pk' or composite 'pks')
    pk_cols = set()
    if config.get('pk'):
        pk_cols.add(config['pk'])
    if config.get('pks'):
        pk_cols.update(config['pks'])
    
    # Gather all FK columns
    fk_cols = set()
    for col_def in config['columns']:
        if col_def['type'] == 'fk':
            fk_cols.add(col_def['col'])

    # Create mapping for header transformation
    key_map = {}
    
    # We inspect the keys from the first row of data
    # (Assuming data is consistent)
    row_keys = data[0].keys()
    
    for col in row_keys:
        is_pk = col in pk_cols
        is_fk = col in fk_cols
        
        if is_pk and is_fk:
            key_map[col] = f"{col} (PK, FK)"
        elif is_pk:
            key_map[col] = f"{col} (PK)"
        elif is_fk:
            key_map[col] = f"{col} (FK)"
        else:
            key_map[col] = col

    # Apply mapping to a NEW list of dicts
    enriched_data = []
    for row in data:
        new_row = {}
        for k, v in row.items():
            new_key = key_map.get(k, k)
            new_row[new_key] = v
        enriched_data.append(new_row)
        
    return enriched_data

def print_table(data):
    """
    Formats a list of dictionaries as a neat ASCII table.
    """
    if not data:
        print("No data found.")
        return

    # Extract headers
    headers = list(data[0].keys())
    
    # Calculate column widths
    widths = {h: len(h) for h in headers}
    for row in data:
        for h in headers:
            val_str = str(row.get(h, ""))
            widths[h] = max(widths[h], len(val_str))

    # Create format string
    # e.g., "{:<10}  {:<20} ..."
    fmt = "  ".join([f"{{:<{widths[h]}}}" for h in headers])

    # Print Separator
    separator = "-" * (sum(widths.values()) + 2 * (len(headers) - 1))
    
    print("\n" + separator)
    print(fmt.format(*headers))
    print(separator)
    
    for row in data:
        row_values = [str(row.get(h, "")) for h in headers]
        print(fmt.format(*row_values))
    print(separator + "\n")

def print_help():
    """Displays the help menu describing all available commands."""
    print("\n================= COMMAND HELP =================")
    print("A - Add New Record: Prompts to create a new entry in a selected table.")
    print("    Automatically handles ID generation for most tables.")
    print("\nV - View Table Data: Displays all records from a selected table.")
    print("    Useful for checking data or finding IDs.")
    print("\nU - Update Record: Modifies an existing record.")
    print("    Requires the Primary Key (ID) of the record you want to change.")
    print("\nD - Delete Record: Permanently removes a record.")
    print("    Requires the Primary Key (ID). May fail if other data depends on it.")
    print("\nL - Last 5 Entries: Shows the 5 most recently added records.")
    print("    Can be run for a single table or ALL tables at once.")
    print("\nR - Reports: Access complex queries like 'Manages' or 'Assigned To'.")
    print("\nS - Search: keyword search.")
    print("    Search across the entire database OR a specific table.")
    print("\nCLS - Clear Screen: Clears the terminal window.")
    print("================================================")

def get_validated_input(prompt, input_type="str", choices=None, optional=False):
    """Generic input handler with validation."""
    while True:
        user_input = input(f"{prompt}: ").strip()

        if optional and not user_input:
            return None

        if not optional and not user_input:
            print("Error: This field is required.")
            continue

        try:
            if input_type == "int":
                return int(user_input)
            elif input_type == "date":
                datetime.strptime(user_input, '%Y-%m-%d')
                return user_input
            elif input_type == "enum":
                for choice in choices:
                    if choice.lower() == user_input.lower():
                        return choice
                print(f"Error: Invalid choice. Must be one of: {', '.join(choices)}")
            elif input_type == "fk":
                return user_input
            else:
                return user_input
        except ValueError as e:
            print(f"Error: Invalid input format. {e}")

def select_table_prompt():
    """Helper to display table menu and get selection."""
    print("\nSelect table (or 'B' to Back):")
    for k, v in TABLE_CONFIG.items():
        print(f"{k}. {v['name']}")
    
    choice = input("Choice: ").strip().upper()
    if choice == 'B':
        return None
    return choice

# =============================================================================
# ACTION HANDLERS
# =============================================================================

def insert_record(conn):
    choice = select_table_prompt()
    if not choice or choice not in TABLE_CONFIG:
        if choice != 'B': print("Invalid table.")
        return

    config = TABLE_CONFIG[choice]
    table_name = config['table']
    print(f"\n--- Add New {config['name']} ---")
    
    data_values = {}

    if config.get('auto_pk', True):
        prefix = config['prefix']
        pk_col = config['pk']
        new_id = db_utils.get_next_id(conn, table_name, pk_col, prefix)
        if not new_id:
            print("Error: Could not generate ID.")
            return
        print(f"Generated ID: {new_id}")
        data_values[pk_col] = new_id
    else:
        print("Note: This table uses a manual or composite Primary Key.")
    
    for col_def in config['columns']:
        is_optional = col_def.get('optional', False)
        val = get_validated_input(f"{col_def['prompt']}{' (Optional)' if is_optional else ''}", col_def['type'], col_def.get('choices'), is_optional)
        data_values[col_def['col']] = val

    columns = list(data_values.keys())
    placeholders = ["%s"] * len(columns)
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, list(data_values.values()))
        print(f"Success! Record added to {config['name']}.")
    except Exception as e:
        print(f"Database Error: {e}")

def handle_view_table(conn):
    choice = select_table_prompt()
    if not choice or choice not in TABLE_CONFIG:
        if choice != 'B': print("Invalid table.")
        return

    rows = db_utils.view_table(conn, TABLE_CONFIG[choice]['table'])
    print(f"\n--- Data for {TABLE_CONFIG[choice]['name']} ---")
    # Enrich headers with PK/FK
    enriched_rows = enrich_headers(choice, rows)
    print_table(enriched_rows)

def handle_update_record(conn):
    choice = select_table_prompt()
    if not choice or choice not in TABLE_CONFIG:
        if choice != 'B': print("Invalid selection.")
        return

    config = TABLE_CONFIG[choice]
    # We can only robustly update simple PK tables via this generic tool
    if not config.get('auto_pk', True) and 'pk' not in config:
        print("Update not supported for composite key tables in this CLI.")
        return

    pk_col = config['pk']
    pk_val = input(f"Enter {pk_col} to update: ").strip()
    if not pk_val: return # allow escape here too

    print("Leave fields empty to keep current value.")
    updates = {}
    
    for col_def in config['columns']:
        val = input(f"New {col_def['prompt']}: ").strip()
        if val:
            updates[col_def['col']] = val
    
    if updates:
        if db_utils.update_record(conn, config['table'], pk_col, pk_val, updates):
            print("Update Successful.")
        else:
            print("Update Failed (ID not found or no changes).")
    else:
        print("No changes entered.")

def handle_delete_record(conn):
    choice = select_table_prompt()
    if not choice or choice not in TABLE_CONFIG:
        if choice != 'B': print("Invalid selection.")
        return

    config = TABLE_CONFIG[choice]
    if not config.get('auto_pk', True) and 'pk' not in config:
        print("Delete not supported for composite key tables in this CLI.")
        return

    pk_col = config['pk']
    pk_val = input(f"Enter {pk_col} to delete: ").strip()
    if not pk_val: return 
    
    confirm = input(f"Are you sure you want to delete {pk_val}? (y/n): ").lower()
    if confirm == 'y':
        if db_utils.delete_record(conn, config['table'], pk_col, pk_val):
            print("Delete Successful.")
        else:
            print("Delete Failed.")

def handle_recent_entries(conn):
    print("\n--- Recent Entries ---")
    print("1. Specific Table")
    print("2. All Tables")
    print("B. Back")
    sub = input("Choice: ").strip().upper()

    if sub == 'B':
        return

    if sub == '1':
        choice = select_table_prompt()
        if choice and choice in TABLE_CONFIG:
            conf = TABLE_CONFIG[choice]
            pk = conf.get('pk', None)
            rows = db_utils.get_recent_records(conn, conf['table'], pk)
            print(f"\nLatest 5 in {conf['name']}:")
            print_table(enrich_headers(choice, rows))
        elif choice != 'B':
            print("Invalid.")

    elif sub == '2':
        print("\n--- Latest 5 Entries for ALL Tables ---")
        for k, conf in TABLE_CONFIG.items():
            pk = conf.get('pk', None)
            rows = db_utils.get_recent_records(conn, conf['table'], pk)
            if rows:
                print(f"\n>>> {conf['name']} <<<")
                print_table(enrich_headers(k, rows))
    else:
        print("Invalid.")

def handle_search(conn):
    print("\n--- Search Database ---")
    print("1. Search specific table")
    print("2. Search entire database")
    print("B. Back")
    choice = input("Choice: ").strip().upper()
    
    if choice == 'B': return

    term = input("Enter search term: ").strip()
    if not term:
        print("Search term cannot be empty.")
        return

    if choice == '1':
        t_choice = select_table_prompt()
        if t_choice and t_choice in TABLE_CONFIG:
            table_name = TABLE_CONFIG[t_choice]['table']
            rows = db_utils.search_table(conn, table_name, term)
            if rows:
                print(f"\n--- Results in {TABLE_CONFIG[t_choice]['name']} ---")
                print_table(enrich_headers(t_choice, rows))
            else:
                print("No matches found.")
        elif t_choice != 'B':
            print("Invalid table choice.")
            
    elif choice == '2':
        print("Searching all tables... (this might take a moment)")
        res = db_utils.search_global(conn, term)
        if res:
            for t, rows in res.items():
                print(f"\n--- Results in {t} ({len(rows)} matches) ---")
                # Find key for this table name
                key = next((k for k, v in TABLE_CONFIG.items() if v['table'] == t), None)
                if key:
                    print_table(enrich_headers(key, rows))
                else:
                    print_table(rows)
        else:
            print("No matches found.")
    else:
        print("Invalid choice.")

def show_reports_menu(conn):
    while True:
        print("\n--- Complex Relationship Reports ---")
        print("1. MANAGES Report (Region -> Gym -> Tournament -> Season)")
        print("2. ASSIGNED TO Report (Trainer -> Gym -> Season)")
        print("3. POKEMON ABILITIES (Derived from Species)")
        print("B. Back")
        
        choice = input("Choice: ").strip().upper()
        
        results = []
        if choice == '1': results = db_utils.get_manages_report(conn)
        elif choice == '2': results = db_utils.get_assigned_to_gym_report(conn)
        elif choice == '3': results = db_utils.get_pokemon_abilities_report(conn)
        elif choice == 'B': break
        else: print("Invalid choice."); continue
            
        if results:
            print(f"\nFound {len(results)} records:")
            print_table(results)
        else:
            print("No data found.")

# =============================================================================
# MAIN LOOP
# =============================================================================

def main():
    clear_screen()
    print("\n=== Pokemon League Database Manager ===")
    
    host = input("DB Host (default: localhost): ").strip() or 'localhost'
    user = input("DB User (default: root): ").strip() or 'root'
    password = getpass("DB Password: ")
    db_name = 'pokemon_league_db'

    conn = db_utils.get_db_connection(host, user, password, db_name)
    if not conn:
        return

    while True:
        print("\n--- Main Menu ---")
        print("A. Add New Record")
        print("V. View Table Data")
        print("U. Update Record")
        print("D. Delete Record")
        print("L. Last 5 Entries")
        print("R. Reports & Complex Queries")
        print("S. Search Database")
        print("H. Help")
        print("CLS. Clear Screen")
        print("Q. Quit")

        main_choice = input("\nEnter choice: ").strip().upper()

        if main_choice == 'Q': print("Exiting..."); conn.close(); break
        elif main_choice == 'CLS' or main_choice == 'C': clear_screen()
        elif main_choice == 'H': print_help()
        elif main_choice == 'A': insert_record(conn)
        elif main_choice == 'V': handle_view_table(conn)
        elif main_choice == 'U': handle_update_record(conn)
        elif main_choice == 'D': handle_delete_record(conn)
        elif main_choice == 'L': handle_recent_entries(conn)
        elif main_choice == 'R': show_reports_menu(conn)
        elif main_choice == 'S': handle_search(conn)
        else: print("Invalid selection.")

if __name__ == "__main__":
    main()