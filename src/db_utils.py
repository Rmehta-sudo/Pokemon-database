import pymysql
import re

# =============================================================================
# SECURITY & VALIDATION HELPER
# =============================================================================

def validate_identifier(identifier):
    """
    Security Check: Prevents SQL Injection in table/column names.
    Ensures the string contains only alphanumeric characters and underscores.
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty.")
    # Strict regex: Only letters, numbers, and underscores allowed
    if not re.match(r'^[a-zA-Z0-9_]+$', identifier):
        raise ValueError(f"Security Alert: Invalid identifier detected: {identifier}")
    return identifier

# =============================================================================
# CONNECTION & ID GENERATION
# =============================================================================

def get_db_connection(host, user, password, db_name):
    """Establishes a connection to the MySQL database."""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def increment_alpha_part(alpha_str):
    chars = list(alpha_str)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] == 'Z':
            chars[i] = 'A'
            i -= 1
        else:
            chars[i] = chr(ord(chars[i]) + 1)
            return "".join(chars)
    return 'A' + "".join(chars)

def get_next_id(connection, table_name, id_column, prefix):
    """
    Generates the next ID. 
    SECURE: Validates table/column names, Parameterizes the LIKE clause.
    """
    # 1. Validate Identifiers (Cannot be parameterized)
    clean_table = validate_identifier(table_name)
    clean_col = validate_identifier(id_column)

    try:
        with connection.cursor() as cursor:
            # 2. Parameterize Values (%s)
            sql = f"SELECT {clean_col} FROM {clean_table} WHERE {clean_col} LIKE %s ORDER BY {clean_col} DESC LIMIT 1"
            cursor.execute(sql, (f"{prefix}%",))
            result = cursor.fetchone()

            if not result:
                return f"{prefix}AAA001"
            
            current_id = result[clean_col]
            match = re.search(r'([A-Z]+)(\d{3})$', current_id[len(prefix):])
            
            if not match:
                return f"{prefix}AAA001"

            alpha_part = match.group(1)
            number_part = int(match.group(2))
            
            next_number = number_part + 1
            next_alpha = alpha_part
            
            if next_number > 999:
                next_number = 1
                next_alpha = increment_alpha_part(alpha_part)
            
            return f"{prefix}{next_alpha}{next_number:03d}"
            
    except pymysql.Error as e:
        print(f"Error generating ID: {e}")
        return None
    except ValueError as ve:
        print(ve)
        return None

# =============================================================================
# VIEW, SEARCH & RECENT FUNCTIONALITY
# =============================================================================

def get_all_tables(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return [list(row.values())[0] for row in cursor.fetchall()]
    except pymysql.Error as e:
        print(f"Error fetching tables: {e}")
        return []

def get_text_columns(conn, table_name):
    # Validate table name before passing to query
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = %s 
                AND data_type IN ('char', 'varchar', 'text', 'mediumtext', 'longtext', 'enum')
            """
            cursor.execute(sql, (clean_table,))
            rows = cursor.fetchall()
            return [row.get('COLUMN_NAME') or row.get('column_name') for row in rows]
            
    except pymysql.Error as e:
        print(f"Error fetching columns for {table_name}: {e}")
        return []
    except ValueError as ve:
        print(ve)
        return []

def view_table(conn, table_name, limit=100):
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            # Table name is validated f-string, Limit is parameterized
            sql = f"SELECT * FROM {clean_table} LIMIT %s"
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except (pymysql.Error, ValueError) as e:
        print(f"Error viewing table: {e}")
        return []

def search_table(conn, table_name, search_term):
    try:
        clean_table = validate_identifier(table_name)
        text_cols = get_text_columns(conn, clean_table)
        
        if not text_cols:
            return []

        # Columns from Schema are safe, but good practice to validate
        clean_cols = [validate_identifier(col) for col in text_cols]

        # Construct Query
        like_clauses = [f"{col} LIKE %s" for col in clean_cols]
        where_clause = " OR ".join(like_clauses)
        
        sql = f"SELECT * FROM {clean_table} WHERE {where_clause}"
        
        # Create tuple of parameters (term repeated for each column)
        params = tuple([f"%{search_term}%"] * len(clean_cols))
        
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
            
    except (pymysql.Error, ValueError) as e:
        print(f"Error searching table: {e}")
        return []

def search_global(conn, search_term):
    tables = get_all_tables(conn)
    results = {}
    for table in tables:
        matches = search_table(conn, table, search_term)
        if matches:
            results[table] = matches
    return results

def get_recent_records(conn, table_name, pk_col=None, limit=5):
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            if pk_col:
                clean_pk = validate_identifier(pk_col)
                sql = f"SELECT * FROM {clean_table} ORDER BY {clean_pk} DESC LIMIT %s"
            else:
                sql = f"SELECT * FROM {clean_table} LIMIT %s"
                
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except (pymysql.Error, ValueError) as e:
        print(f"Error fetching recent records: {e}")
        return []

# =============================================================================
# UPDATE & DELETE FUNCTIONALITY (SECURE)
# =============================================================================

def update_record(conn, table_name, pk_dict, updates_dict):
    if not updates_dict or not pk_dict:
        return False

    try:
        clean_table = validate_identifier(table_name)
        
        # Validate Column Names (Identifiers)
        clean_set_cols = [validate_identifier(col) for col in updates_dict.keys()]
        clean_pk_cols = [validate_identifier(col) for col in pk_dict.keys()]

        # Build Query Strings
        set_clauses = [f"{col} = %s" for col in clean_set_cols]
        set_str = ", ".join(set_clauses)
        
        where_clauses = [f"{col} = %s" for col in clean_pk_cols]
        where_str = " AND ".join(where_clauses)

        sql = f"UPDATE {clean_table} SET {set_str} WHERE {where_str}"
        
        # Combine Values into Tuple
        params = tuple(list(updates_dict.values()) + list(pk_dict.values()))
        
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return True # Return True even if 0 rows updated (query succeeded)
            
    except (pymysql.Error, ValueError) as e:
        print(f"Error updating record: {e}")
        return False

def delete_record(conn, table_name, pk_dict):
    if not pk_dict:
        return False

    try:
        clean_table = validate_identifier(table_name)
        clean_pk_cols = [validate_identifier(col) for col in pk_dict.keys()]

        where_clauses = [f"{col} = %s" for col in clean_pk_cols]
        where_str = " AND ".join(where_clauses)
        
        sql = f"DELETE FROM {clean_table} WHERE {where_str}"
        params = tuple(pk_dict.values())
        
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return True
            
    except pymysql.Error as e:
        if e.args[0] == 1451:
            print("Cannot delete: This record is referenced by other tables.")
        else:
            print(f"Error deleting record: {e}")
        return False
    except ValueError as ve:
        print(ve)
        return False

# =============================================================================
# COMPLEX RELATIONSHIP QUERIES (Static SQL is safe)
# =============================================================================
# These functions use hardcoded SQL strings, so they are naturally safe 
# from injection unless you concatenate input into them (which we are not).

def get_manages_report(conn):
    sql = """
        SELECT R.region_name, LS.theme, T.tournament_name, G.gym_name
        FROM Region R
        JOIN LeagueSeason LS ON R.region_id = LS.region_id
        JOIN Tournament T ON LS.season_id = T.season_id
        JOIN City C ON T.city_id = C.city_id 
        JOIN Gym G ON C.city_id = G.city_id
        ORDER BY R.region_name, LS.year;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_assigned_to_gym_report(conn):
    sql = """
        SELECT LS.year, LS.theme, R.region_name, G.gym_name, TR.name
        FROM GymSeasonRegistry GSR
        JOIN LeagueSeason LS ON GSR.season_id = LS.season_id
        JOIN Gym G ON GSR.gym_id = G.gym_id
        JOIN GymLeader GL ON GSR.leader_id = GL.leader_id
        JOIN Trainer TR ON GL.leader_id = TR.trainer_id
        JOIN City C ON G.city_id = C.city_id
        JOIN Region R ON C.region_id = R.region_id
        ORDER BY LS.year DESC, R.region_name;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_pokemon_abilities_report(conn):
    sql = """
        SELECT RP.nickname, S.species_name, A.ability_name, A.effect_description
        FROM RegisteredPokemon RP
        JOIN PokemonSpecies S ON RP.species_id = S.species_id
        JOIN PokemonSpeciesAbility PSA ON S.species_id = PSA.species_id
        JOIN Ability A ON PSA.ability_id = A.ability_id
        LIMIT 50;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

# =============================================================================
# MATCH HELPERS
# =============================================================================

def validate_match_winner(trainer1_id, trainer2_id, winner_id):
    if winner_id is None:
        return True
    if trainer1_id is None and trainer2_id is None:
        raise ValueError("Both trainers are None")
    if winner_id != trainer1_id and winner_id != trainer2_id:
        raise ValueError("Winner must be one of the participants")
    return True

def insert_match(conn, match_record):
    required = ['tournament_id', 'match_number']
    for k in required:
        if k not in match_record:
            return False

    # Validation Logic
    try:
        validate_match_winner(match_record.get('trainer1_id'), 
                              match_record.get('trainer2_id'), 
                              match_record.get('winner_id'))
    except ValueError as e:
        print(e)
        return False

    # Secure Insert Logic
    cols = [validate_identifier(k) for k in match_record.keys()]
    vals = list(match_record.values())
    placeholders = ["%s"] * len(cols)

    sql = f"INSERT INTO Match_Table ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, vals)
            return True
    except pymysql.Error as e:
        print(f"Error inserting match: {e}")
        return False

def update_match_winner(conn, tournament_id, match_number, new_winner_id):
    try:
        with conn.cursor() as cursor:
            # Get participants
            cursor.execute(
                "SELECT trainer1_id, trainer2_id FROM Match_Table WHERE tournament_id = %s AND match_number = %s",
                (tournament_id, match_number)
            )
            row = cursor.fetchone()
            if not row:
                return False

            validate_match_winner(row['trainer1_id'], row['trainer2_id'], new_winner_id)

            # Secure Update
            cursor.execute(
                "UPDATE Match_Table SET winner_id = %s WHERE tournament_id = %s AND match_number = %s",
                (new_winner_id, tournament_id, match_number)
            )
            return cursor.rowcount > 0
    except (pymysql.Error, ValueError) as e:
        print(f"Error updating winner: {e}")
        return False