import pymysql
import re

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
    """
    Increments a string of uppercase letters like a number (Base 26).
    AAA -> AAB, ... AAZ -> ABA, ... ZZZ -> AAAA
    """
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
    Generates the next ID based on the custom format: [Prefix][Letters][3 Digits]
    Example: TAAA022 -> TAAA023
    """
    try:
        with connection.cursor() as cursor:
            sql = f"SELECT {id_column} FROM {table_name} WHERE {id_column} LIKE %s ORDER BY {id_column} DESC LIMIT 1"
            cursor.execute(sql, (f"{prefix}%",))
            result = cursor.fetchone()

            if not result:
                return f"{prefix}AAA001"
            
            current_id = result[id_column]
            
            # Match format: Prefix + Letters + 3 Digits
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

# =============================================================================
# VIEW & SEARCH FUNCTIONALITY
# =============================================================================

def get_all_tables(conn):
    """Returns a list of all table names in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return [list(row.values())[0] for row in cursor.fetchall()]
    except pymysql.Error as e:
        print(f"Error fetching tables: {e}")
        return []

def get_text_columns(conn, table_name):
    """Returns a list of columns that are text-based (searchable)."""
    try:
        with conn.cursor() as cursor:
            # Query Information Schema to find text columns
            sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = %s 
                AND data_type IN ('char', 'varchar', 'text', 'mediumtext', 'longtext', 'enum')
            """
            cursor.execute(sql, (table_name,))
            return [row['column_name'] for row in cursor.fetchall()]
    except pymysql.Error as e:
        print(f"Error fetching columns for {table_name}: {e}")
        return []

def view_table(conn, table_name, limit=100):
    """
    Returns all rows from a specific table.
    Optionally limits results to prevent terminal flooding.
    """
    try:
        with conn.cursor() as cursor:
            sql = f"SELECT * FROM {table_name} LIMIT %s"
            cursor.execute(sql, (limit,))
            results = cursor.fetchall()
            return results
    except pymysql.Error as e:
        print(f"Error viewing table {table_name}: {e}")
        return []

def search_table(conn, table_name, search_term):
    """
    Searches for a term in ALL text columns of a specific table.
    Returns: List of matching rows (dictionaries).
    """
    text_cols = get_text_columns(conn, table_name)
    
    if not text_cols:
        return []

    # Build dynamic OR query: WHERE col1 LIKE %s OR col2 LIKE %s ...
    like_clauses = [f"{col} LIKE %s" for col in text_cols]
    where_clause = " OR ".join(like_clauses)
    
    sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
    
    # Parameter for every %s placeholder
    params = [f"%{search_term}%"] * len(text_cols)
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Error searching table {table_name}: {e}")
        return []

def search_global(conn, search_term):
    """
    Searches across ALL tables in the database.
    Returns: Dictionary {table_name: [list of matching rows]}
    """
    tables = get_all_tables(conn)
    results = {}
    
    for table in tables:
        matches = search_table(conn, table, search_term)
        if matches:
            results[table] = matches
            
    return results

# =============================================================================
# UPDATE & DELETE FUNCTIONALITY
# =============================================================================

def update_record(conn, table_name, pk_col, pk_val, updates_dict):
    """
    Updates a record identified by PK with values from updates_dict.
    updates_dict: {'column_name': 'new_value', ...}
    """
    if not updates_dict:
        print("No data provided for update.")
        return False

    # Build dynamic SQL: SET col1 = %s, col2 = %s ...
    set_clauses = [f"{col} = %s" for col in updates_dict.keys()]
    set_str = ", ".join(set_clauses)
    
    sql = f"UPDATE {table_name} SET {set_str} WHERE {pk_col} = %s"
    
    # Values for SET clauses + Value for WHERE clause
    params = list(updates_dict.values()) + [pk_val]
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if cursor.rowcount == 0:
                print(f"No record found with ID {pk_val} or no changes made.")
                return False
            return True
    except pymysql.Error as e:
        print(f"Error updating record: {e}")
        return False

def delete_record(conn, table_name, pk_col, pk_val):
    """
    Deletes a record identified by PK.
    (Suggestion: Useful for managing mistakes in data entry)
    """
    sql = f"DELETE FROM {table_name} WHERE {pk_col} = %s"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (pk_val,))
            if cursor.rowcount == 0:
                print(f"No record found with ID {pk_val}.")
                return False
            return True
    except pymysql.Error as e:
        # Check for foreign key constraint errors
        if e.args[0] == 1451:
            print("Cannot delete: This record is referenced by other tables.")
        else:
            print(f"Error deleting record: {e}")
        return False