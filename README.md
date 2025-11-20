

# Pokémon League Database Manager

---

## Project Overview

<span style="color:#2b6cb0;font-weight:bold;">Pokémon League Database Manager</span> is a feature-rich, terminal-based application for managing, querying, and analyzing a relational database of Pokémon tournaments, trainers, and related entities. Developed in Python using the Textual TUI framework, it provides a robust, secure, and visually appealing interface for all database operations, analytics, and data integrity enforcement.

---

## Features and Functionality


### 1. Table Browser and CRUD Operations

<span style="color:#3182ce;font-weight:bold;">Table Listing and Browsing</span>  
All tables in the database are listed in a sidebar. Selecting a table displays its contents in a scrollable, filterable data grid. By default, the first 100 rows are shown for performance. Table-specific search returns all matching records, regardless of count.

<span style="color:#3182ce;font-weight:bold;">Add, Update, Delete Records</span>  
Users can add new records, update existing ones, or delete records using auto-generated forms that respect schema constraints. All operations use parameterized SQL (`INSERT`, `UPDATE`, `DELETE`) to ensure security and correctness.

<span style="color:#3182ce;font-weight:bold;">Table Navigation and Cell-to-Cell Jumping</span>  
Navigate seamlessly through table cells using keyboard shortcuts (arrow keys: <kbd>j</kbd>, <kbd>k</kbd>, <kbd>h</kbd>, <kbd>l</kbd> or arrow keys). The active cell is highlighted for clarity. Selecting a foreign key cell allows instant navigation ("table junction") to the referenced table and record, making relational exploration intuitive and efficient.

<span style="color:#3182ce;font-weight:bold;">Referential Integrity and Constraints</span>  
All foreign key relationships are enforced at the database level. Attempts to insert or update with invalid references are rejected. Cascading actions (`ON DELETE CASCADE`, `ON UPDATE CASCADE`) are used where appropriate to maintain data consistency. Unique constraints and check constraints are enforced as defined in the schema.


### 2. Search and Filtering

<span style="color:#38a169;font-weight:bold;">Table Search</span>  
Each table view includes a search bar for filtering records by any field. Results are not limited to the initial 100-row display.  
<span style="color:#718096;">SQL: <code>SELECT ... WHERE ... LIKE ...</code></span>

<span style="color:#38a169;font-weight:bold;">Global Search</span>  
A dedicated tab allows searching for a keyword across all tables and fields. Results display the table name and matching record details.  
<span style="color:#718096;">SQL: Iterates over all tables with <code>SELECT ... WHERE ... LIKE ...</code> for each.</span>


### 3. Reports Tab

<span style="color:#d69e2e;font-weight:bold;">Predefined Analytical Reports</span>  
The Reports tab provides a set of curated, complex SQL reports (e.g., top trainers by win percentage, region power index, species MVP leaderboard). Users select a report and view results with a single action. Reports use advanced SQL features such as <code>JOIN</code>, <code>GROUP BY</code>, <code>WITH</code> (CTEs), and aggregation. Results can be filtered using a search bar within the report view.


### 4. Queries Tab

<span style="color:#805ad5;font-weight:bold;">Parameterized Queries</span>  
The Queries tab offers a set of interactive queries where users provide input parameters (e.g., minimum wins, trainer ID, tournament name). All queries are parameterized to prevent SQL injection and ensure safe execution. The exact SQL statement and parameters are displayed after each query for transparency.

**Example Query Usage:**

1. **Trainers with more than N wins in a tournament**
  - Enter a tournament name and minimum win count, then run the query to see all qualifying trainers.
  - SQL: Uses <code>SELECT ... WHERE tournament_name = ? AND total_wins > ?</code>

2. **Pokémon owned by a specific trainer**
  - Enter a trainer ID to list all Pokémon registered to that trainer.
  - SQL: Uses <code>SELECT ... WHERE trainer_id = ?</code>

3. **Average level of Pokémon in a tournament**
  - Enter a tournament name to compute the average level of all Pokémon used in that tournament.
  - SQL: Uses <code>SELECT ... AVG(level) ... WHERE tournament_name = ?</code>

4. **Badge leaderboard (top N trainers by badges)**
  - Enter a number N to see the top N trainers with the most badges.
  - SQL: Uses <code>SELECT ... ORDER BY badges_collected DESC LIMIT ?</code>


### 5. Data Integrity and Schema Enforcement

<span style="color:#e53e3e;font-weight:bold;">Foreign Keys</span>  
All relationships between tables are enforced using foreign key constraints. Invalid references are not permitted.

<span style="color:#e53e3e;font-weight:bold;">Cascading Actions</span>  
Where specified, deleting or updating a parent record cascades changes to dependent records (e.g., deleting a trainer removes their Pokémon if <code>ON DELETE CASCADE</code> is set).

<span style="color:#e53e3e;font-weight:bold;">Unique and Check Constraints</span>  
Unique constraints ensure that key fields (such as IDs and emails) are not duplicated. Check constraints enforce value ranges and formats (e.g., level between 1 and 100, ID patterns).

<span style="color:#e53e3e;font-weight:bold;">Composite Keys and Junction Tables</span>  
Many-to-many relationships are managed using composite primary keys in junction tables, ensuring uniqueness and referential integrity.

---


---

## Usage Instructions


### Connecting to the Database

On startup, the application prompts for database credentials (host, user, password, database name). Upon successful connection, the schema is loaded and all features become available.

### Table Operations

1. **Viewing Data:** Select a table from the sidebar to view its data. The first 100 rows are shown by default.
2. **Adding Records:** Click "Add" to open a form. Fill in the required fields and submit. All constraints are enforced.
3. **Updating Records:** Select a row, click "Update", edit the fields, and save. Only valid changes are accepted.
4. **Deleting Records:** Select a row, click "Delete", and confirm. Cascading deletes occur if defined in the schema.
5. **Table Navigation:** Use arrow keys or <kbd>j</kbd>, <kbd>k</kbd>, <kbd>h</kbd>, <kbd>l</kbd> to move cell-to-cell. Click on foreign key values to jump to related tables and records.
6. **Table Search:** Use the search bar to filter records. All matching records are shown, even if the result set exceeds 100 rows.

### Global Search

Access the Global Search tab to search for a keyword across all tables. Results display the table and the matching record(s).

### Reports Tab

Select the Reports tab to access predefined analytical reports. Choose a report and click "Run Selected Report" to view results. Use the report search bar to filter within the report output.

### Queries Tab

Select the Queries tab to run parameterized queries. Enter values in the input fields for each query and execute to see results. The SQL preview panel displays the exact query and parameters used. All input fields are user-editable; no query uses hardcoded parameters.

---


---

## Schema Design and Data Integrity

- **Foreign Key Example:**
  ```sql
  FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE
  ```
- **Unique Constraint Example:**
  ```sql
  UNIQUE (email)
  ```
- **Check Constraint Example:**
  ```sql
  CHECK (level BETWEEN 1 AND 100)
  ```
- **Composite Key Example:**
  ```sql
  PRIMARY KEY (tournament_id, trainer_id)
  ```

All constraints are enforced by the database and respected by the application.

---


---

## SQL Command Examples

- **Select with Join:**
  ```sql
  SELECT RP.nickname, RP.level, PS.species_name
  FROM RegisteredPokemon RP
  JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
  WHERE RP.trainer_id = ?;
  ```
- **Aggregate Query:**
  ```sql
  SELECT T.tournament_name, ROUND(AVG(RP.level), 2) AS average_level
  FROM Tournament T
  JOIN TournamentEntry TE ON T.tournament_id = TE.tournament_id
  JOIN RegisteredPokemon RP ON RP.trainer_id = TE.trainer_id
  WHERE T.tournament_name = ?
  GROUP BY T.tournament_id;
  ```
- **Delete with Cascade:**
  ```sql
  DELETE FROM Trainer WHERE trainer_id = ?;
  -- Dependent records in RegisteredPokemon are deleted automatically if ON DELETE CASCADE is set
  ```

---


---

## Extensibility

- New queries and reports can be added by defining functions in `db_utils.py` and updating the configuration in `tui.py`.
- The application automatically adapts to schema changes on restart.
- All code is modular and documented for maintainability and extension.

---


---

## Security Considerations

All user input is handled using parameterized queries, which prevents SQL injection attacks. The application never concatenates user input directly into SQL statements. All schema constraints (foreign keys, unique, check, cascading) are enforced at the database level, ensuring that only valid and consistent data can be entered or modified.

---

## Summary

This application provides a robust, secure, and user-friendly interface for managing and analyzing a complex relational database. It enforces all data integrity constraints, supports advanced analytics, and offers a range of features for both database administrators and analysts. All SQL operations are parameterized, and the design emphasizes both usability and correctness.
