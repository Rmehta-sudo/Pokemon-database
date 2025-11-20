import pymysql
import re
import datetime

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


def get_searchable_columns(conn, table_name):
    """Return list of (column_name, data_type) for columns we can search across.
    This includes text, numeric and date/time types so the application can
    decide whether to use LIKE or equality comparisons based on the search term.
    """
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            sql = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """
            cursor.execute(sql, (clean_table,))
            rows = cursor.fetchall()
            return [(row.get('COLUMN_NAME') or row.get('column_name'), (row.get('DATA_TYPE') or row.get('data_type')).lower()) for row in rows]
    except pymysql.Error as e:
        print(f"Error fetching searchable columns for {table_name}: {e}")
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

        # Retrieve searchable columns and types
        cols = get_searchable_columns(conn, clean_table)

        if not cols:
            return []

        # Attempt to interpret search term as int/float/date to enable numeric/date searches
        is_int = False
        is_float = False
        is_date = False
        num_val = None
        date_val = None
        try:
            num_val = int(search_term)
            is_int = True
        except Exception:
            try:
                num_val = float(search_term)
                is_float = True
            except Exception:
                num_val = None

        # parse date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS or YYYY)
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y"):
            try:
                dt = datetime.datetime.strptime(search_term, fmt)
                is_date = True
                # normalize to YYYY-MM-DD for DATE comparisons; if format was year only, keep year
                date_val = dt.date().isoformat() if fmt != "%Y" else dt.year
                break
            except Exception:
                continue

        clauses = []
        params = []

        text_types = {'char', 'varchar', 'text', 'mediumtext', 'longtext', 'enum'}
        numeric_types = {'int', 'bigint', 'smallint', 'mediumint', 'decimal', 'float', 'double', 'tinyint'}
        date_types = {'date', 'datetime', 'timestamp', 'year', 'time'}

        for col, dtype in cols:
            try:
                clean_col = validate_identifier(col)
            except ValueError:
                continue

            if dtype in text_types:
                clauses.append(f"LOWER({clean_col}) LIKE LOWER(%s)")
                params.append(f"%{search_term}%")

            if dtype in numeric_types and (is_int or is_float):
                clauses.append(f"{clean_col} = %s")
                params.append(num_val)

            if dtype in date_types and is_date:
                # If search was year-only, compare YEAR(), else DATE()
                if isinstance(date_val, int):
                    clauses.append(f"YEAR({clean_col}) = %s")
                    params.append(date_val)
                else:
                    clauses.append(f"DATE({clean_col}) = %s")
                    params.append(date_val)

        if not clauses:
            return []

        where_clause = " OR ".join(clauses)
        sql = f"SELECT * FROM {clean_table} WHERE {where_clause}"

        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
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

def get_gym_leader_cheat_sheet(conn, limit=15):
    sql = """
        SELECT 
            G.gym_name,
            GL.leader_id,
            TR.trainer_id AS challenger_id,
            TR.name AS challenger_name,
            COUNT(GB.battle_id) AS battles_fought,
            SUM(CASE WHEN GB.result = 'Win' THEN 1 ELSE 0 END) AS challenger_wins,
            SUM(CASE WHEN GB.result = 'Loss' THEN 1 ELSE 0 END) AS challenger_losses,
            ROUND(
                SUM(CASE WHEN GB.result = 'Win' THEN 1 ELSE 0 END) / NULLIF(COUNT(GB.battle_id), 0),
                2
            ) AS win_rate,
            GROUP_CONCAT(DISTINCT CONCAT(PS.species_name, ' (', COALESCE(PT.type_name, 'Unknown'), ')')
                         ORDER BY PS.species_name SEPARATOR ', ') AS signature_pokemon
        FROM GymBattle GB
        JOIN Gym G ON GB.gym_id = G.gym_id
        JOIN GymLeader GL ON GB.leader_id = GL.leader_id
        JOIN Trainer TR ON GB.challenger_id = TR.trainer_id
        LEFT JOIN RegisteredPokemon RP ON RP.trainer_id = TR.trainer_id
        LEFT JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
        LEFT JOIN Type PT ON PS.primary_type_id = PT.type_id
        GROUP BY G.gym_name, GL.leader_id, TR.trainer_id, TR.name
        ORDER BY battles_fought DESC, win_rate DESC
        LIMIT %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET SESSION group_concat_max_len = 4096")
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_tournament_snapshot(conn):
    sql = """
        WITH species_usage AS (
            SELECT 
                T.tournament_id,
                T.tournament_name,
                T.start_date,
                PS.species_name,
                COUNT(*) AS usage_count,
                ROW_NUMBER() OVER (PARTITION BY T.tournament_id ORDER BY COUNT(*) DESC) AS rank_in_tournament
            FROM Tournament T
            JOIN TournamentEntry TE ON T.tournament_id = TE.tournament_id
            JOIN RegisteredPokemon RP ON RP.trainer_id = TE.trainer_id
            JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
            WHERE T.start_date >= CURDATE()
            GROUP BY T.tournament_id, T.tournament_name, T.start_date, PS.species_name
        )
        SELECT tournament_name, start_date, species_name, usage_count, rank_in_tournament
        FROM species_usage
        WHERE rank_in_tournament <= 5
        ORDER BY start_date, rank_in_tournament;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_underrated_trainer_report(conn):
    sql = """
        WITH match_stats AS (
            SELECT trainer_id,
                   SUM(win_flag) AS wins,
                   COUNT(*) AS matches_played
            FROM (
                SELECT trainer1_id AS trainer_id,
                       CASE WHEN winner_id = trainer1_id THEN 1 ELSE 0 END AS win_flag
                FROM Match_Table
                UNION ALL
                SELECT trainer2_id AS trainer_id,
                       CASE WHEN winner_id = trainer2_id THEN 1 ELSE 0 END AS win_flag
                FROM Match_Table
            ) s
            WHERE trainer_id IS NOT NULL
            GROUP BY trainer_id
        ),
        tour_counts AS (
            SELECT trainer_id, COUNT(*) AS tournaments_entered
            FROM TournamentEntry
            GROUP BY trainer_id
        )
        SELECT 
            TR.trainer_id,
            TR.name,
            COALESCE(MS.wins, 0) AS wins,
            COALESCE(MS.matches_played, 0) AS matches_played,
            COALESCE(TC.tournaments_entered, 0) AS tournaments_entered,
            ROUND(COALESCE(MS.wins, 0) / NULLIF(COALESCE(MS.matches_played, 0), 0), 3) AS win_ratio
        FROM Trainer TR
        LEFT JOIN match_stats MS ON TR.trainer_id = MS.trainer_id
        LEFT JOIN tour_counts TC ON TR.trainer_id = TC.trainer_id
        WHERE COALESCE(MS.matches_played, 0) >= 10
          AND COALESCE(MS.wins, 0) / NULLIF(COALESCE(MS.matches_played, 0), 0) >= 0.6
          AND COALESCE(TC.tournaments_entered, 0) <= 3
        ORDER BY win_ratio DESC, tournaments_entered ASC
        LIMIT 25;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_region_power_report(conn):
    sql = """
        WITH match_wins AS (
            SELECT TR.region_id, COUNT(*) AS match_wins
            FROM Match_Table MT
            JOIN Trainer TR ON MT.winner_id = TR.trainer_id
            GROUP BY TR.region_id
        ),
        badge_totals AS (
            SELECT R.region_id, COUNT(*) AS badges_awarded
            FROM GymBadge GB
            JOIN Gym G ON GB.gym_id = G.gym_id
            JOIN City C ON G.city_id = C.city_id
            JOIN Region R ON C.region_id = R.region_id
            GROUP BY R.region_id
        ),
        tournament_hosting AS (
            SELECT R.region_id, COUNT(DISTINCT T.tournament_id) AS tournaments_hosted
            FROM Region R
            JOIN City C ON C.region_id = R.region_id
            JOIN Tournament T ON T.city_id = C.city_id
            GROUP BY R.region_id
        )
        SELECT 
            R.region_name,
            COALESCE(MW.match_wins, 0) AS match_wins,
            COALESCE(BT.badges_awarded, 0) AS badges_awarded,
            COALESCE(TH.tournaments_hosted, 0) AS tournaments_hosted
        FROM Region R
        LEFT JOIN match_wins MW ON R.region_id = MW.region_id
        LEFT JOIN badge_totals BT ON R.region_id = BT.region_id
        LEFT JOIN tournament_hosting TH ON R.region_id = TH.region_id
        ORDER BY match_wins DESC, tournaments_hosted DESC;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_species_mvp_report(conn, limit=15):
    sql = """
        SELECT 
            PS.species_name,
            COUNT(*) AS registered_count,
            ROUND(AVG(RP.level), 2) AS avg_level,
            MAX(RP.level) AS max_level
        FROM RegisteredPokemon RP
        JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
        GROUP BY PS.species_id, PS.species_name
        HAVING COUNT(*) >= 5
        ORDER BY avg_level DESC, registered_count DESC
        LIMIT %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

# =============================================================================
# PARAMETERIZED QUERY LIBRARY
# =============================================================================

def query_trainers_with_min_wins(conn, tournament_name, min_wins=50):
    sql = """
        SELECT 
            TR.trainer_id,
            TR.name,
            TE.registration_date,
            COALESCE(W.total_wins, 0) AS total_wins
        FROM TournamentEntry TE
        JOIN Tournament T ON TE.tournament_id = T.tournament_id
        JOIN Trainer TR ON TE.trainer_id = TR.trainer_id
        LEFT JOIN (
            SELECT winner_id, COUNT(*) AS total_wins
            FROM Match_Table
            WHERE winner_id IS NOT NULL
            GROUP BY winner_id
        ) W ON TR.trainer_id = W.winner_id
        WHERE T.tournament_name = %s
          AND COALESCE(W.total_wins, 0) > %s
        ORDER BY total_wins DESC;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (tournament_name, min_wins))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_pokemon_by_trainer(conn, trainer_id):
    sql = """
        SELECT RP.pokemon_id, RP.nickname, RP.level, PS.species_name
        FROM RegisteredPokemon RP
        JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
        WHERE RP.trainer_id = %s
        ORDER BY RP.level DESC;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (trainer_id,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_average_level_for_tournament(conn, tournament_name):
    sql = """
        SELECT 
            T.tournament_name,
            ROUND(AVG(RP.level), 2) AS average_level,
            COUNT(*) AS pokemon_count
        FROM Tournament T
        JOIN TournamentEntry TE ON T.tournament_id = TE.tournament_id
        JOIN RegisteredPokemon RP ON RP.trainer_id = TE.trainer_id
        WHERE T.tournament_name = %s
        GROUP BY T.tournament_id, T.tournament_name;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (tournament_name,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_species_by_prefix(conn, prefix):
    sql = """
        SELECT species_id, species_name, base_attack, base_defense, base_speed
        FROM PokemonSpecies
        WHERE species_name LIKE %s
        ORDER BY species_name;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (f"{prefix}%",))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_badge_leaderboard(conn, limit=10):
    sql = """
        SELECT 
            T.trainer_id,
            T.name,
            COUNT(*) AS badges_collected,
            COUNT(DISTINCT GB.gym_id) AS gyms_conquered
        FROM GymBadge GB
        JOIN Trainer T ON GB.trainer_id = T.trainer_id
        GROUP BY T.trainer_id, T.name
        ORDER BY badges_collected DESC, gyms_conquered DESC
        LIMIT %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_elite_pokemon(conn, min_level=85):
    sql = """
        SELECT 
            RP.pokemon_id,
            COALESCE(RP.nickname, PS.species_name) AS display_name,
            PS.species_name,
            RP.level,
            T.name AS trainer_name
        FROM RegisteredPokemon RP
        JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
        JOIN Trainer T ON RP.trainer_id = T.trainer_id
        WHERE RP.level >= %s
        ORDER BY RP.level DESC
        LIMIT 50;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (min_level,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_active_region_insights(conn):
    sql = """
        SELECT 
            R.region_name,
            COUNT(DISTINCT T.tournament_id) AS tournaments_hosted,
            COUNT(DISTINCT TE.trainer_id) AS visiting_trainers,
            ROUND(AVG(LS.year), 1) AS average_season_year
        FROM Region R
        LEFT JOIN City C ON C.region_id = R.region_id
        LEFT JOIN Tournament T ON T.city_id = C.city_id
        LEFT JOIN TournamentEntry TE ON TE.tournament_id = T.tournament_id
        LEFT JOIN LeagueSeason LS ON T.season_id = LS.season_id
        GROUP BY R.region_id, R.region_name
        ORDER BY tournaments_hosted DESC, visiting_trainers DESC;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
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