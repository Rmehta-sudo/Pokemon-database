import sys
from getpass import getpass
from datetime import datetime
import db_utils

# =============================================================================
# TABLE CONFIGURATION
# This dictionary defines how the TUI interacts with each table.
# It maps inputs to database columns so we don't need 20 different functions.
# =============================================================================

TABLE_CONFIG = {
    "1": {
        "name": "Trainer",
        "table": "Trainer",
        "pk": "trainer_id",
        "prefix": "T",
        "columns": [
            {"col": "name", "prompt": "Trainer Name", "type": "str"},
            {"col": "gender", "prompt": "Gender", "type": "enum", "choices": ["Male", "Female", "Other"]},
            {"col": "birth_date", "prompt": "Birth Date (YYYY-MM-DD)", "type": "date"},
            {"col": "contact_info_email", "prompt": "Email", "type": "str"},
            {"col": "contact_info_phone", "prompt": "Phone", "type": "str"},
            {"col": "region_id", "prompt": "Region ID (e.g., RAAA001)", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"}
        ]
    },
    "2": {
        "name": "Pokemon Species",
        "table": "PokemonSpecies",
        "pk": "species_id",
        "prefix": "S",
        "columns": [
            {"col": "species_name", "prompt": "Species Name", "type": "str"},
            {"col": "base_hp", "prompt": "Base HP", "type": "int"},
            {"col": "base_attack", "prompt": "Base Attack", "type": "int"},
            {"col": "base_defense", "prompt": "Base Defense", "type": "int"},
            {"col": "base_speed", "prompt": "Base Speed", "type": "int"},
            {"col": "primary_type_id", "prompt": "Primary Type ID", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "secondary_type_id", "prompt": "Secondary Type ID (Optional)", "type": "fk", "ref_table": "Type", "ref_pk": "type_id", "optional": True},
        ]
    },
    "3": {
        "name": "Registered Pokemon",
        "table": "RegisteredPokemon",
        "pk": "pokemon_id",
        "prefix": "P",
        "columns": [
            {"col": "species_id", "prompt": "Species ID", "type": "fk", "ref_table": "PokemonSpecies", "ref_pk": "species_id"},
            {"col": "trainer_id", "prompt": "Owner Trainer ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "nickname", "prompt": "Nickname", "type": "str"},
            {"col": "level", "prompt": "Level (1-100)", "type": "int"},
            {"col": "experience_points", "prompt": "Current XP", "type": "int"},
            {"col": "registration_date", "prompt": "Date Caught (YYYY-MM-DD)", "type": "date"},
        ]
    },
    "4": {
        "name": "Gym",
        "table": "Gym",
        "pk": "gym_id",
        "prefix": "G",
        "columns": [
            {"col": "gym_name", "prompt": "Gym Name", "type": "str"},
            {"col": "city_id", "prompt": "City ID", "type": "fk", "ref_table": "City", "ref_pk": "city_id"},
            {"col": "specialization_type_id", "prompt": "Specialty Type ID", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
        ]
    },
    "5": {
        "name": "Gym Battle",
        "table": "GymBattle",
        "pk": "battle_id",
        "prefix": "B",
        "columns": [
            {"col": "challenger_id", "prompt": "Challenger ID", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "gym_id", "prompt": "Gym ID", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "leader_id", "prompt": "Leader ID", "type": "fk", "ref_table": "GymLeader", "ref_pk": "leader_id"},
            {"col": "battle_date", "prompt": "Battle Date (YYYY-MM-DD)", "type": "date"},
            {"col": "result", "prompt": "Result", "type": "enum", "choices": ["Win", "Loss", "Draw"]},
        ]
    },
    "6": {
        "name": "Move",
        "table": "Move",
        "pk": "move_id",
        "prefix": "M",
        "columns": [
            {"col": "move_name", "prompt": "Move Name", "type": "str"},
            {"col": "power", "prompt": "Power", "type": "int"},
            {"col": "accuracy", "prompt": "Accuracy (0-100)", "type": "int"},
            {"col": "pp", "prompt": "PP", "type": "int"},
            {"col": "type_id", "prompt": "Type ID", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "category", "prompt": "Category", "type": "enum", "choices": ["Physical", "Special", "Status"]},
        ]
    },
    "7": {
        "name": "Region",
        "table": "Region",
        "pk": "region_id",
        "prefix": "R",
        "columns": [
            {"col": "region_name", "prompt": "Region Name", "type": "str"},
            {"col": "main_city", "prompt": "Main City Name", "type": "str"},
        ]
    },
    "8": {
        "name": "City",
        "table": "City",
        "pk": "city_id",
        "prefix": "C",
        "columns": [
            {"col": "city_name", "prompt": "City Name", "type": "str"},
            {"col": "region_id", "prompt": "Region ID", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"},
        ]
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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
                # Validate date format
                datetime.strptime(user_input, '%Y-%m-%d')
                return user_input
            
            elif input_type == "enum":
                # Case insensitive check
                for choice in choices:
                    if choice.lower() == user_input.lower():
                        return choice
                print(f"Error: Invalid choice. Must be one of: {', '.join(choices)}")
            
            elif input_type == "fk":
                # We assume the user enters a string ID.
                # In a full app, you might ping the DB here to check if it exists.
                return user_input
            
            else:
                return user_input

        except ValueError as e:
            print(f"Error: Invalid input format. {e}")

def insert_record(conn, table_key):
    """Generates inputs dynamically based on CONFIG and inserts into DB."""
    config = TABLE_CONFIG[table_key]
    table_name = config['table']
    prefix = config['prefix']
    pk_col = config['pk']

    print(f"\n--- Add New {config['name']} ---")
    
    # 1. Generate New ID
    new_id = db_utils.get_next_id(conn, table_name, pk_col, prefix)
    if not new_id:
        print("Error: Could not generate ID.")
        return
    print(f"Generated ID: {new_id}")

    # 2. Collect Data
    data_values = {pk_col: new_id}
    
    for col_def in config['columns']:
        is_optional = col_def.get('optional', False)
        prompt_text = f"{col_def['prompt']}{' (Optional)' if is_optional else ''}"
        
        val = get_validated_input(
            prompt_text, 
            col_def['type'], 
            col_def.get('choices'), 
            is_optional
        )
        data_values[col_def['col']] = val

    # 3. Construct Query
    columns = list(data_values.keys())
    placeholders = ["%s"] * len(columns)
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    values = list(data_values.values())

    # 4. Execute
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, values)
        print(f"Success! Added {config['name']} with ID {new_id}.")
    except Exception as e:
        print(f"Database Error: {e}")

# =============================================================================
# MAIN LOOP
# =============================================================================

def main():
    print("\n=== Pokemon League Database Manager ===")
    
    # Connection Setup
    host = input("DB Host (default: localhost): ").strip() or 'localhost'
    user = input("DB User (default: root): ").strip() or 'root'
    password = getpass("DB Password: ")
    db_name = 'pokemon_league_db'

    conn = db_utils.get_db_connection(host, user, password, db_name)
    if not conn:
        return

    while True:
        print("\nSelect a table to add an entry:")
        for key, conf in TABLE_CONFIG.items():
            print(f"{key}. {conf['name']}")
        print("Q. Quit")

        choice = input("\nEnter choice: ").strip().upper()

        if choice == 'Q':
            print("Exiting...")
            conn.close()
            break
        
        if choice in TABLE_CONFIG:
            insert_record(conn, choice)
        else:
            print("Invalid selection.")

if __name__ == "__main__":
    main()