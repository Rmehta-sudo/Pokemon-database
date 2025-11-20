import sys
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid, VerticalScroll
from textual.widgets import Header, Footer, Button, Static, DataTable, Input, Label, ListView, ListItem, TabbedContent, TabPane
from pathlib import Path
import re
from textual.screen import ModalScreen, Screen
from textual import on
from textual.binding import Binding
from textual.validation import Number, Function
from rich.text import Text
import db_utils

# =============================================================================
# CONFIGURATION (AUTO-GENERATED FROM SCHEMA)
# =============================================================================

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

SQL_TYPE_CATEGORY = {
    "char": "str",
    "varchar": "str",
    "text": "str",
    "mediumtext": "str",
    "longtext": "str",
    "enum": "enum",
    "int": "int",
    "bigint": "int",
    "smallint": "int",
    "tinyint": "int",
    "mediumint": "int",
    "decimal": "int",
    "double": "int",
    "float": "int",
    "numeric": "int",
    "date": "date",
    "datetime": "date",
    "timestamp": "date",
    "time": "date",
    "year": "int"
}


def field_type_from_sql(sql_type: str) -> str:
    sql_type = (sql_type or "str").lower()
    return SQL_TYPE_CATEGORY.get(sql_type, "str")


def split_block_definitions(block_lines):
    text = "\n".join(block_lines)
    parts = []
    buf = []
    depth = 0
    for char in text:
        if char == '(':
            depth += 1
        elif char == ')':
            depth = max(depth - 1, 0)
        if char == ',' and depth == 0:
            part = ''.join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(char)
    tail = ''.join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_enum_choices(segment: str):
    start = segment.find('(')
    end = segment.rfind(')')
    if start == -1 or end == -1 or end <= start:
        return []
    body = segment[start + 1:end]
    choices = []
    for token in body.split(','):
        clean = token.strip().strip("'\"")
        if clean:
            choices.append(clean)
    return choices


def parse_column_definition(part: str):
    part = part.strip()
    if not part:
        return None
    match = re.match(r"`?(\w+)`?\s+(.*)", part)
    if not match:
        return None
    col_name = match.group(1)
    remainder = match.group(2).strip()

    enum_match = re.match(r"ENUM\s*(\([^)]*\))(.*)", remainder, re.IGNORECASE)
    if enum_match:
        type_decl = "enum"
        type_tail = enum_match.group(1)
        extras = enum_match.group(2).strip()
        choices = parse_enum_choices(enum_match.group(1))
    else:
        tokens = remainder.split(None, 1)
        type_decl = tokens[0]
        extras = tokens[1] if len(tokens) > 1 else ""
        choices = None

    base_type = type_decl.split('(')[0].lower()
    col_info = {
        "col": col_name,
        "field_type": field_type_from_sql(base_type),
        "sql_type": base_type,
        "choices": choices,
        "extras": extras.upper(),
        "is_primary": "PRIMARY KEY" in extras.upper()
    }
    return col_info


def parse_foreign_key(part: str):
    fk_regex = re.compile(r"FOREIGN KEY\s*\(([^)]+)\)\s*REFERENCES\s+`?(\w+)`?\s*\(([^)]+)\)", re.IGNORECASE)
    match = fk_regex.search(part)
    if not match:
        return []
    cols = [c.strip().strip('`') for c in match.group(1).split(',')]
    ref_table = match.group(2)
    ref_cols = [c.strip().strip('`') for c in match.group(3).split(',')]
    pairs = []
    for idx, col in enumerate(cols):
        ref_col = ref_cols[idx] if idx < len(ref_cols) else ref_cols[0]
        pairs.append((col, ref_table, ref_col))
    return pairs


def parse_prefix_constraint(part: str):
    check_regex = re.compile(r"CHECK\s*\(\s*([A-Za-z0-9_]+)\s+REGEXP\s*'\^([A-Za-z0-9]+)", re.IGNORECASE)
    match = check_regex.search(part)
    if match:
        return match.group(1), match.group(2)
    return None, None


def parse_primary_key_part(part: str):
    pk_regex = re.compile(r"PRIMARY KEY\s*\(([^)]+)\)", re.IGNORECASE)
    match = pk_regex.search(part)
    if not match:
        return []
    cols = [c.strip().strip('`') for c in match.group(1).split(',')]
    return cols


def parse_create_table_block(table_name: str, block_lines):
    definitions = split_block_definitions(block_lines)
    columns = []
    pk_columns = []
    fk_map = {}
    prefix_candidates = {}

    for part in definitions:
        upper = part.upper()
        if upper.startswith('CONSTRAINT'):
            col_name, prefix_val = parse_prefix_constraint(part)
            if col_name and prefix_val:
                prefix_candidates[col_name] = prefix_val
            if 'FOREIGN KEY' in upper:
                for col, ref_table, ref_col in parse_foreign_key(part):
                    fk_map[col] = {"ref_table": ref_table, "ref_pk": ref_col}
            continue
        if upper.startswith('PRIMARY KEY'):
            pk_columns.extend(parse_primary_key_part(part))
            continue
        if 'FOREIGN KEY' in upper:
            for col, ref_table, ref_col in parse_foreign_key(part):
                fk_map[col] = {"ref_table": ref_table, "ref_pk": ref_col}
            continue

        col_info = parse_column_definition(part)
        if not col_info:
            continue
        columns.append(col_info)
        if col_info.get('is_primary'):
            pk_columns.append(col_info['col'])

    # Deduplicate PK list preserving order
    seen = set()
    ordered_pks = []
    for pk in pk_columns:
        if pk not in seen:
            ordered_pks.append(pk)
            seen.add(pk)

    table_entry = {
        "columns": []
    }

    if len(ordered_pks) == 1:
        table_entry['pk'] = ordered_pks[0]
    elif len(ordered_pks) > 1:
        table_entry['pks'] = ordered_pks

    pk_name = table_entry.get('pk')
    if pk_name and pk_name in prefix_candidates:
        table_entry['prefix'] = prefix_candidates[pk_name]

    if 'pks' in table_entry and len(table_entry['pks']) > 1:
        table_entry['auto_pk'] = False

    for col in columns:
        entry = {"col": col['col']}
        field_type = col['field_type']
        if col['col'] in fk_map:
            field_type = 'fk'
            entry['ref_table'] = fk_map[col['col']]['ref_table']
            entry['ref_pk'] = fk_map[col['col']]['ref_pk']
        entry['type'] = field_type
        if field_type == 'enum' and col['choices']:
            entry['choices'] = col['choices']
        table_entry['columns'].append(entry)

    return table_entry


def load_table_config_from_schema(schema_path: Path):
    schema_path = Path(schema_path)
    if not schema_path.exists():
        return {}

    tables = {}
    in_create = False
    current_table = None
    block_lines = []

    with schema_path.open('r', encoding='utf-8') as fh:
        for raw_line in fh:
            line_no_comment = raw_line.split('--', 1)[0].rstrip()
            stripped = line_no_comment.strip()
            if not in_create:
                create_match = re.match(r"CREATE TABLE\s+`?(\w+)`?", stripped, re.IGNORECASE)
                if create_match:
                    current_table = create_match.group(1)
                    in_create = True
                    block_lines = []
                continue

            if stripped.startswith(')'):
                if current_table and block_lines:
                    tables[current_table] = parse_create_table_block(current_table, block_lines)
                in_create = False
                current_table = None
                block_lines = []
                continue

            if stripped:
                block_lines.append(stripped)

    return tables


TABLE_CONFIG = load_table_config_from_schema(SCHEMA_FILE)


LOGO_ASCII = r"""
   ___      _                               
  / _ \___ | | _____ _ __ ___   ___  _ __   
 / /_)/ _ \| |/ / _ \ '_ ` _ \ / _ \| '_ \  
/ ___/ (_) |   <  __/ | | | | | (_) | | | | 
\/    \___/|_|\_\___|_| |_| |_|\___/|_| |_| 
                                            
   DB MANAGER v2.0 - [bold yellow]Phase 4[/bold yellow]
"""

REPORT_DEFINITIONS = {
    "report_gym_cheat": {
        "label": "Gym Leader's Cheat Sheet",
        "description": "For each gym, surface recent challengers, their preferred species, and historical win rates to help leaders prepare.",
        "sql": """
            SELECT 
                G.gym_name,
                TR.trainer_id AS challenger_id,
                TR.name AS challenger_name,
                COUNT(GB.battle_id) AS total_battles,
                SUM(CASE WHEN GB.result = 'Win' THEN 1 ELSE 0 END) AS challenger_wins,
                SUM(CASE WHEN GB.result = 'Loss' THEN 1 ELSE 0 END) AS challenger_losses,
                ROUND(
                    SUM(CASE WHEN GB.result = 'Win' THEN 1 ELSE 0 END) / NULLIF(COUNT(GB.battle_id), 0),
                    2
                ) AS win_rate,
                GROUP_CONCAT(DISTINCT PS.species_name ORDER BY PS.species_name SEPARATOR ', ') AS signature_species
            FROM GymBattle GB
            JOIN Gym G ON GB.gym_id = G.gym_id
            JOIN Trainer TR ON GB.challenger_id = TR.trainer_id
            LEFT JOIN RegisteredPokemon RP ON RP.trainer_id = TR.trainer_id
            LEFT JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
            GROUP BY G.gym_name, TR.trainer_id, TR.name
            HAVING total_battles >= 2
            ORDER BY G.gym_name, win_rate DESC
            LIMIT 60;
        """
    },
    "report_tournament_snapshot": {
        "label": "Tournament Snapshot",
        "description": "Highlights the most popular Pokémon species appearing in tournaments happening now or soon to reveal the live meta.",
        "sql": """
            WITH species_usage AS (
                SELECT 
                    T.tournament_id,
                    T.tournament_name,
                    T.start_date,
                    PS.species_name,
                    COUNT(*) AS usage_count,
                    ROW_NUMBER() OVER (
                        PARTITION BY T.tournament_id 
                        ORDER BY COUNT(*) DESC
                    ) AS rank_in_tournament
                FROM Tournament T
                JOIN TournamentEntry TE ON T.tournament_id = TE.tournament_id
                JOIN RegisteredPokemon RP ON RP.trainer_id = TE.trainer_id
                JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
                WHERE T.start_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY T.tournament_id, T.tournament_name, T.start_date, PS.species_name
            )
            SELECT tournament_name, start_date, species_name, usage_count
            FROM species_usage
            WHERE rank_in_tournament <= 5
            ORDER BY start_date, usage_count DESC;
        """
    },
    "report_underrated_trainers": {
        "label": "Underrated Trainer Finder",
        "description": "Identifies trainers with stellar win ratios but very low tournament participation — perfect scouting targets.",
        "sql": """
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
                ) derived
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
                COALESCE(MS.matches_played, 0) AS matches_played,
                COALESCE(MS.wins, 0) AS wins,
                COALESCE(TC.tournaments_entered, 0) AS tournaments_entered,
                ROUND(COALESCE(MS.wins, 0) / NULLIF(COALESCE(MS.matches_played, 0), 0), 3) AS win_ratio
            FROM Trainer TR
            LEFT JOIN match_stats MS ON TR.trainer_id = MS.trainer_id
            LEFT JOIN tour_counts TC ON TR.trainer_id = TC.trainer_id
            WHERE COALESCE(MS.matches_played, 0) >= 10
              AND COALESCE(MS.wins, 0) / NULLIF(COALESCE(MS.matches_played, 0), 0) >= 0.6
              AND COALESCE(TC.tournaments_entered, 0) <= 3
            ORDER BY win_ratio DESC, tournaments_entered ASC
            LIMIT 30;
        """
    },
    "report_top_winners": {
        "label": "Top Win Percent Trainers",
        "description": "League table of trainers with the best overall win percentage with at least 20 matches played.",
        "sql": """
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
                ) derived
                WHERE trainer_id IS NOT NULL
                GROUP BY trainer_id
            )
            SELECT 
                TR.trainer_id,
                TR.name,
                MS.matches_played,
                MS.wins,
                ROUND(MS.wins / NULLIF(MS.matches_played, 0), 3) AS win_ratio
            FROM match_stats MS
            JOIN Trainer TR ON TR.trainer_id = MS.trainer_id
            WHERE MS.matches_played >= 20
            ORDER BY win_ratio DESC, MS.matches_played DESC
            LIMIT 25;
        """
    },
    "report_region_power": {
        "label": "Region Power Index",
        "description": "Cross-region comparison showing which regions dominate matches, badges, and hosted tournaments.",
        "sql": """
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
    },
    "report_species_mvp": {
        "label": "Species MVP Leaderboard",
        "description": "Shows the highest-performing Pokémon species by average level among frequently registered partners.",
        "sql": """
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
            LIMIT 25;
        """
    }
}

# Queries metadata to mirror the Reports UX
QUERY_DEFINITIONS = {
    "q_selection": {
        "label": "Selection – Trainers with > N wins in a tournament",
        "description": "Retrieve all trainers registered for a tournament with more than the given total wins.",
    },
    "q_projection": {
        "label": "Projection – Nickname and level by trainer",
        "description": "Show the nickname and level for all Pokémon owned by the specified trainer ID.\n\nExample: Trainer ID = TBRANDON102 ",
    },
    "q_aggregate": {
        "label": "Aggregate – Average level for a tournament",
        "description": "Calculate the average level of all Pokémon used in a tournament.\n\nExample: Tournament = Silver Conference ",
    },
    "q_badge_leaderboard": {
        "label": "Badge Leaderboard – Top trainers by badges",
        "description": "Show the top N trainers with the most badges.\n\nExample: Limit = 10 ",
    },
}

QUERY_DEFAULTS = {
    "tournament": "Indigo Plateau Conference",
    "min_wins": 5,
    "trainer_id": "TBRANDON102",
    "aggregate_tournament": "Silver Conference",
    "badge_limit": 10
}

# -----------------------------------------------------------------------------
# Custom DataTable with dual (row + cell) highlighting
# -----------------------------------------------------------------------------
class DualHighlightDataTable(DataTable):
    """
    A DataTable that paints a subtle background for the entire row and
    keeps cell-selection semantics for the active cell.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Keeps the cell-specific jumping logic working
        try:
            self.cursor_type = "cell"
        except Exception:
            pass
        self.last_highlighted_row = None
        self.last_highlighted_col = None

    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:
        """
        Fires when the cursor moves.
        1. Clears the background of the old row.
        2. Paints the background of the new row.
        """
        row_index = None
        try:
            row_index = event.coordinate.row
        except Exception:
            return

        col_index = None
        try:
            col_index = event.coordinate.column
        except Exception:
            col_index = None

        # If the cursor is still on the same cell, nothing to do
        if self.last_highlighted_row == row_index and self.last_highlighted_col == col_index:
            return

        # If the row is the same but the column changed, only update the two cells
        if self.last_highlighted_row == row_index and self.last_highlighted_col is not None:
            # Revert the old active cell to the row background
            try:
                old_col = self.last_highlighted_col
                old_val = self.get_row_at(row_index)[old_col]
                old_text = Text(str(old_val), style="bold white on #282828")
                try:
                    self.update_cell_at((row_index, old_col), old_text, update_width=False)
                except Exception:
                    try:
                        self.update_cell(row_index, old_col, old_text)
                    except Exception:
                        pass
            except Exception:
                pass

            # Apply the new active cell (no background so CSS can show through)
            try:
                new_val = self.get_row_at(row_index)[col_index]
                new_text = Text(str(new_val), style="bold white")
                try:
                    self.update_cell_at((row_index, col_index), new_text, update_width=False)
                except Exception:
                    try:
                        self.update_cell(row_index, col_index, new_text)
                    except Exception:
                        pass
            except Exception:
                pass

            self.last_highlighted_col = col_index
            return

        # 1. Clear old row highlight (Reset to normal string)
        if self.last_highlighted_row is not None:
            self._colorize_row(self.last_highlighted_row, remove_style=True)

        # 2. Apply new row highlight (Dark Grey Background), skipping the active cell's background so CSS cursor is visible
        self._colorize_row(row_index, remove_style=False, active_col=col_index)
        self.last_highlighted_row = row_index
        self.last_highlighted_col = col_index

    def _colorize_row(self, row_index, remove_style=False, active_col=None):
        """Helper to update the style of every cell in a row."""
        try:
            # Get raw data for the row
            row_data = self.get_row_at(row_index)

            for col_index, cell_val in enumerate(row_data):
                val_str = str(cell_val)

                if remove_style:
                    # Revert to plain string (removes background)
                    try:
                        self.update_cell_at((row_index, col_index), val_str, update_width=False)
                    except Exception:
                        try:
                            self.update_cell(row_index, col_index, val_str)
                        except Exception:
                            pass
                else:
                    # Apply Row Background: "on #282828" (Dark Grey)
                    # We use 'on' to strictly set the background color.
                    # Use a high-contrast foreground so text remains readable
                    # when the row background is painted.
                    # If this column is the active cell, don't paint the background
                    # so that the CSS cursor background can show through.
                    if active_col is not None and col_index == active_col:
                        styled = Text(val_str, style="bold white")
                    else:
                        styled = Text(val_str, style="bold white on #282828")
                    try:
                        self.update_cell_at((row_index, col_index), styled, update_width=False)
                    except Exception:
                        try:
                            self.update_cell(row_index, col_index, styled)
                        except Exception:
                            pass
        except Exception:
            # Handles cases where row data might not exist yet during a reload
            pass


# =============================================================================
# SCREENS & MODALS
# =============================================================================

class LoginScreen(ModalScreen):
    """Modal to prompt for database credentials."""
    
    CSS = """
    LoginScreen { align: center middle; background: $background 50%; }
    #login_dialog { grid-size: 2; grid-gutter: 1 2; grid-rows: auto; padding: 2; width: 60; height: auto; border: thick $primary; background: $surface; }
    #login_label { column-span: 2; content-align: center middle; text-style: bold; margin-bottom: 1; }
    Button { width: 100%; margin-top: 1; column-span: 2; }
    Input { width: 100%; }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Database Login", id="login_label"),
            Label("Host:"), Input(placeholder="localhost", id="host", value="localhost"),
            Label("User:"), Input(placeholder="root", id="user", value="root"),
            Label("Password:"), Input(placeholder="", password=True, id="password"),
            Label("Database:"), Input(placeholder="pokemon_league_db", id="db_name", value="pokemon_league_db"),
            Button("Connect", variant="success", id="btn_connect"),
            id="login_dialog"
        )

    def on_mount(self) -> None:
        self.query_one("#host").focus()

    def action_cancel(self):
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_connect": self.submit()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.submit()

    def submit(self):
        host = self.query_one("#host", Input).value
        user = self.query_one("#user", Input).value
        password = self.query_one("#password", Input).value
        db_name = self.query_one("#db_name", Input).value
        self.dismiss((host, user, password, db_name))


class RecordForm(ModalScreen):
    """Generic Form for Adding/Updating Records."""
    
    CSS = """
    RecordForm { align: center middle; background: $background 80%; }
    #form_container { width: 70%; height: 80%; background: $surface; border: thick $primary; padding: 2; }
    #form_title { text-style: bold; border-bottom: solid $secondary; margin-bottom: 1; text-align: center; }
    .field_label { margin-top: 1; }
    #form_buttons { dock: bottom; height: auto; margin-top: 2; }
    Button { margin-right: 1; }
    
    .pk_container { height: auto; margin-bottom: 1; }
    .pk_input { width: 80%; }
    .pk_unlock_btn { width: 20%; min-width: 10; margin-left: 1; }
    """
    
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, conn, table_name, record_data=None, mode="add"):
        super().__init__()
        self.conn = conn
        self.table_name = table_name
        self.record_data = record_data or {}
        self.mode = mode
        self.pk_cols = [] # Track PK columns to toggle them

    def action_cancel(self):
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        config = TABLE_CONFIG.get(self.table_name, {})
        columns = config.get("columns", [])
        
        # Identify PKs
        pk_set = set()
        if config.get('pk'): pk_set.add(config['pk'])
        if config.get('pks'): pk_set.update(config['pks'])
        self.pk_cols = list(pk_set)

        # PREPARE COLUMNS TO RENDER
        display_columns = list(columns) # Copy original list
        single_pk = config.get('pk')
        if single_pk and not any(c['col'] == single_pk for c in display_columns):
            display_columns.insert(0, {"col": single_pk, "type": "str"})

        # Auto-generate ID if in Add mode and table has auto-id config
        if self.mode == "add" and config.get('pk') and config.get('prefix'):
             generated_id = db_utils.get_next_id(self.conn, self.table_name, config['pk'], config['prefix'])
             if generated_id:
                 self.record_data[config['pk']] = generated_id

        title = f"{self.mode.upper()} Record: {self.table_name}"
        
        with Container(id="form_container"):
            yield Label(title, id="form_title")
            
            with VerticalScroll():
                for col_def in display_columns:
                    col_name = col_def['col']
                    col_type = col_def['type']
                    
                    label_text = f"{col_name.replace('_', ' ').title()} ({col_type})"
                    if col_type == 'fk':
                        label_text += f" -> {col_def['ref_table']}"
                    elif col_type == 'enum':
                        label_text += f" [{', '.join(col_def.get('choices', []))}]"
                    
                    yield Label(label_text, classes="field_label")
                    
                    # Populate with old data (or auto-generated ID)
                    value = str(self.record_data.get(col_name, ""))
                    if value == "None": value = ""
                    
                    # DISABLE INPUT if it is a PK and we are in UPDATE mode
                    is_pk_in_update = (self.mode == "update" and col_name in pk_set)
                    
                    inp = Input(value=value, id=f"inp_{col_name}", disabled=is_pk_in_update)
                    
                    if is_pk_in_update:
                        # Render input alongside a small "Unlock" button
                        with Horizontal(classes="pk_container"):
                            inp.classes = "pk_input"
                            yield inp
                            yield Button("Unlock", id=f"unlock_{col_name}", variant="warning", classes="pk_unlock_btn")
                    else:
                        yield inp
            
            with Horizontal(id="form_buttons"):
                yield Button("Save", variant="success", id="btn_save")
                yield Button("Cancel", variant="error", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        
        elif event.button.id.startswith("unlock_"):
            col_name = event.button.id.split("_", 1)[1]
            try:
                inp_widget = self.query_one(f"#inp_{col_name}", Input)
                inp_widget.disabled = False
                event.button.disabled = True 
                self.notify(f"Unlocked {col_name}")
            except Exception as e:
                self.notify(f"Error unlocking: {e}", severity="error")
            
        elif event.button.id == "btn_save":
            data = {}
            config = TABLE_CONFIG.get(self.table_name, {})
            
            display_columns = list(config.get("columns", []))
            single_pk = config.get('pk')
            if single_pk and not any(c['col'] == single_pk for c in display_columns):
                display_columns.insert(0, {"col": single_pk, "type": "str"})
            
            for col_def in display_columns:
                col_name = col_def['col']
                try:
                    val = self.query_one(f"#inp_{col_name}", Input).value.strip()
                    if val == "": val = None
                    data[col_name] = val
                except:
                    pass
            
            self.dismiss(data)


class ConfirmationModal(ModalScreen):
    """Simple confirmation dialog."""
    CSS = """
    ConfirmationModal { align: center middle; background: $background 80%; }
    #confirm_box { width: 40; height: auto; background: $surface; border: thick $error; padding: 2; }
    #confirm_text { text-align: center; margin-bottom: 2; }
    """
    BINDINGS = [("escape", "cancel", "Cancel")]
    
    def __init__(self, message):
        super().__init__()
        self.message = message
        
    def action_cancel(self):
        self.dismiss(False)

    def compose(self) -> ComposeResult:
        with Container(id="confirm_box"):
            yield Label(self.message, id="confirm_text")
            with Horizontal():
                yield Button("Yes", variant="error", id="btn_yes")
                yield Button("No", variant="primary", id="btn_no")
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn_yes")


class DetailModal(ModalScreen):
    """Detail view for drilling down."""
    
    BINDINGS = [("escape", "cancel", "Cancel")]
    
    def __init__(self, table_name, data_row):
        super().__init__()
        self.table_name = table_name
        self.data_row = data_row

    def action_cancel(self):
        self.dismiss()

    def compose(self) -> ComposeResult:
        with Container(id="modal_container"):
            yield Label(f"Drill-Down: {self.table_name}", id="modal_title")
            table = DataTable()
            table.add_columns("Field", "Value")
            for k, v in self.data_row.items():
                table.add_row(str(k), str(v))
            yield table
            yield Button("Close", variant="error", id="close_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_btn":
            self.dismiss()

# =============================================================================
# MAIN APPLICATION
# =============================================================================

class PokemonTUI(App):
    CSS = """
    Screen { align: center middle; }
    #sidebar { dock: left; width: 45; height: 100%; background: $panel; border-right: tall $primary; }
    #main_content { height: 100%; width: 100%; padding: 1; }
    #logo { color: $accent; content-align: center middle; height: 10; margin-bottom: 1; }
    DataTable { height: 1fr; border: tall $primary; }
    Button { width: 100%; margin-bottom: 1; }
    #modal_container { padding: 2; background: $surface; border: thick $primary; width: 60%; height: auto; align: center middle; }
    #modal_title { text-style: bold; padding-bottom: 1; border-bottom: solid $secondary; width: 100%; text-align: center; }
    .report_box { border: solid $secondary; padding: 1; margin-bottom: 1; margin-right: 1; }
    .search_row { height: auto; margin-top: 1; }
    #search_input, #filter_input { width: 80%; }
    #btn_do_search, #btn_filter { width: 20%; }

    /* 1. ACTIVE CELL HIGHLIGHT (The "Cursor") */
    /* This sits ON TOP of the row highlight we paint in Python */
    DataTable > .datatable--cursor {
        background: $primary;   /* Bright theme primary color */
        color: white;           /* Force white text for contrast */
        text-style: bold;
    }

    /* NEW: Ensure the search table looks good */
    #search_results_table {
        height: 1fr;
        border: tall $success;
    }

    #report_table {
        height: 1fr;
        border: tall $primary;
    }

    #report_grid {
        grid-size: 2;
        grid-columns: 1fr 1fr;
        grid-gutter: 1 1;
        width: 100%;
        margin-bottom: 1;
    }

    .query_card {
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
    }

    .section_header {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    #query_table {
        height: 1fr;
        border: tall $accent;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("t", "toggle_dark", "Toggle Theme"),
        Binding("a", "add_record", "Add"),
        Binding("d", "delete_record", "Delete"),
        Binding("u", "update_record", "Update"),
        Binding("r", "refresh_table", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "cursor_left", "Left", show=False),
        Binding("l", "cursor_right", "Right", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.conn = None
        self.current_table = None
        self.current_table_data = [] # Ensure initialized
        self.selected_report_key = None
        self.report_results = []
        # Queries UX state
        self.selected_query_key = None
        self.query_results = []

    def on_mount(self) -> None:
        self.title = "Pokemon League DB Manager"
        # Set Default Theme to Tokyo Night
        self.theme = "tokyo-night"
        self.push_screen(LoginScreen(), self.login_callback)
        self.call_after_refresh(self._prime_report_list)

    def login_callback(self, credentials):
        if not credentials:
            self.exit()
            return
        host, user, password, db_name = credentials
        self.conn = db_utils.get_db_connection(host, user, password, db_name)
        if self.conn:
            self.notify("Connected Successfully!", severity="success")
        else:
            self.notify("Connection Failed. Retrying...", severity="error")
            self.push_screen(LoginScreen(), self.login_callback)

    def _prime_report_list(self):
        try:
            report_list = self.query_one("#report_list", ListView)
            children = list(report_list.children)
            if not children:
                return
            report_list.index = 0
            first_item = children[0]
            if getattr(first_item, "name", None):
                self.update_report_description(first_item.name)
        except Exception:
            pass
        # Also preselect the first query for the Queries tab
        try:
            query_list = self.query_one("#query_list", ListView)
            q_children = list(query_list.children)
            if q_children:
                query_list.index = 0
                self.update_query_description(q_children[0].name)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            with Horizontal():
                # Increased width for sidebar to fit ASCII art
                with Container(id="sidebar"):
                    yield Static(LOGO_ASCII, id="logo")
                    yield Label("Tables:", classes="box_label")
                    
                    list_items = []
                    for t_name in sorted(TABLE_CONFIG.keys(), key=str.upper):
                        list_items.append(ListItem(Label(t_name), name=t_name))
                    yield ListView(*list_items, id="table_list")
                    
                    yield Static("\n")
                    yield Button("Add New (a)", id="btn_add", variant="success")
                    yield Button("Update (u)", id="btn_update", variant="warning")
                    yield Button("Delete (d)", id="btn_delete", variant="error")
                    yield Button("Refresh (r)", id="btn_refresh", variant="primary")
                    yield Button("Recent 5", id="btn_recent", variant="default")
                    yield Button("Quit (q)", id="btn_quit", variant="error")

                with Container(id="main_content"):
                    # Prepare dynamic items for the reports list view
                    report_items = [
                        ListItem(Label(defn["label"]), name=key)
                        for key, defn in REPORT_DEFINITIONS.items()
                    ]

                    with TabbedContent(initial="tab_data"):
                        with TabPane("Data Browser", id="tab_data"):
                            yield Label("Select a table from the sidebar...", id="table_label")
                            # Use our DualHighlightDataTable to get row+cell highlighting
                            yield DualHighlightDataTable(id="main_table")

                            # PER-TABLE SEARCH BAR MOVED BELOW TABLE
                            with Horizontal(id="data_search_row", classes="search_row"):
                                yield Input(placeholder="Filter current table...", id="filter_input")
                                yield Button("Filter", id="btn_filter", variant="primary")
                        
                        with TabPane("Global Search", id="tab_search"):
                            yield Label("Search Keywords:")
                            with Horizontal(id="search_row", classes="search_row"):
                                yield Input(placeholder="Search term...", id="search_input", classes="search_box")
                                yield Button("Go", id="btn_do_search", classes="search_btn", variant="primary")
                            yield DataTable(id="search_results_table")
                        
                        with TabPane("Reports", id="tab_reports"):
                            yield Label("Analysis Reports", classes="section_header")
                            with Horizontal(id="report_split"):
                                with Vertical(id="report_controls"):
                                    if report_items:
                                        yield ListView(*report_items, id="report_list")
                                    else:
                                        yield ListView(ListItem(Label("No reports configured"), name="none"), id="report_list")
                                    yield Button("Run Selected Report", id="btn_run_report", variant="success")
                                    yield Static("Select a report to preview its purpose.", id="report_description", classes="report_box")
                                with Vertical(id="report_results_panel"):
                                    yield DataTable(id="report_table")
                                    with Horizontal(id="report_search_row", classes="search_row"):
                                        yield Input(placeholder="Filter results...", id="report_search_input")
                                        yield Button("Filter", id="btn_report_search", variant="primary")
                                        yield Button("Reset", id="btn_report_reset", variant="warning")

                        with TabPane("Queries", id="tab_queries"):
                            yield Label("Queries", classes="section_header")
                            with Horizontal(id="query_split"):
                                # Left controls (exactly like Reports layout)
                                with Vertical(id="query_controls"):
                                    # List of queries
                                    query_items = [
                                        ListItem(Label(defn["label"]), name=key)
                                        for key, defn in QUERY_DEFINITIONS.items()
                                    ]
                                    yield ListView(*query_items, id="query_list")
                                    yield Button("Run Selected Query", id="btn_run_query", variant="success")
                                    yield Static("Select a query, tweak inputs below, and run.", id="query_description", classes="report_box")
                                    # Input panel (fixed inputs; run will read what it needs)
                                    with VerticalScroll(id="query_inputs_panel", classes="query_card"):
                                        yield Label("Tournament (Selection)")
                                        yield Input(placeholder="Tournament Name", id="input_query_tournament", value=QUERY_DEFAULTS["tournament"])
                                        yield Label("Min Wins (Selection)")
                                        yield Input(placeholder="50", id="input_query_min_wins", value=str(QUERY_DEFAULTS["min_wins"]))
                                        yield Label("Trainer ID (Projection)")
                                        yield Input(placeholder="TR102501", id="input_query_trainer", value=QUERY_DEFAULTS["trainer_id"])
                                        yield Label("Tournament (Aggregate)")
                                        yield Input(placeholder="Silver Conference", id="input_query_avg_tournament", value=QUERY_DEFAULTS["aggregate_tournament"])
                                        yield Label("Top N Trainers (Badge Leaderboard)")
                                        yield Input(placeholder="10", id="input_query_badge_limit", value=str(QUERY_DEFAULTS["badge_limit"]))
                                # Right results & filter
                                with Vertical(id="query_results_panel"):
                                    yield DataTable(id="query_table")
                                    with Horizontal(id="query_search_row", classes="search_row"):
                                        yield Input(placeholder="Filter results...", id="query_search_input")
                                        yield Button("Filter", id="btn_query_search", variant="primary")
                                        yield Button("Reset", id="btn_query_reset", variant="warning")
                                    # SQL Preview box
                                    yield Static("SQL preview will appear here after you run a query.", id="query_sql_preview", classes="report_box")
        yield Footer()

    def _is_input_focused(self):
        """Check if user is currently typing in an Input field."""
        return isinstance(self.focused, Input)

    # --- ACTIONS (KEY BINDINGS) ---
    def action_add_record(self):
        if not self._is_input_focused():
            self.on_button_pressed(Button(id="btn_add"))
            
    def action_update_record(self):
        if not self._is_input_focused():
            self.on_button_pressed(Button(id="btn_update"))

    def action_delete_record(self):
        if not self._is_input_focused():
            self.on_button_pressed(Button(id="btn_delete"))
            
    def action_refresh_table(self):
        if not self._is_input_focused():
            self.on_button_pressed(Button(id="btn_refresh"))

    def action_cursor_down(self):
        if not self._is_input_focused():
            if isinstance(self.focused, (DataTable, ListView)):
                self.focused.action_cursor_down()
    
    def action_cursor_up(self):
        if not self._is_input_focused():
            if isinstance(self.focused, (DataTable, ListView)):
                self.focused.action_cursor_up()

    def action_cursor_left(self):
        if not self._is_input_focused():
            if isinstance(self.focused, DataTable):
                self.focused.action_cursor_left()

    def action_cursor_right(self):
        if not self._is_input_focused():
            if isinstance(self.focused, DataTable):
                self.focused.action_cursor_right()

    # --- NAVIGATION ---
    def switch_to_table(self, table_name, pk_val):
        """Jumps to a table and highlights the row with the given PK."""
        self.current_table = table_name
        self.query_one("#table_label").update(f"Browsing: [bold yellow]{table_name}[/]")
        
        # Update Sidebar Selection for consistency
        try:
            list_view = self.query_one("#table_list", ListView)
            for i, item in enumerate(list_view.children):
                if item.name == table_name:
                    list_view.index = i
                    break
        except:
            pass

        # Load Data with higher limit to ensure jump targets are found
        self.load_table_data(table_name, limit=1000)
        
        # Find row index for PK
        config = TABLE_CONFIG.get(table_name, {})
        pk_col = config.get('pk')
        
        if pk_col and hasattr(self, 'current_table_data') and self.current_table_data:
            found = False
            for index, row in enumerate(self.current_table_data):
                # FIX: Case-insensitive comparison for robustness
                # Also handle integer/string types by casting to string and stripping whitespace
                row_val = str(row.get(pk_col, "")).strip().lower()
                target_val = str(pk_val).strip().lower()

                if row_val == target_val:
                    table = self.query_one("#main_table", DataTable)
                    table.move_cursor(row=index, animate=True)
                    self.notify(f"Jumped to {table_name}: {pk_val}")
                    found = True
                    break
            if not found:
                 self.notify(f"Switched to {table_name}, but row {pk_val} not in top 1000 results.", severity="warning")
        else:
            self.notify(f"Switched to {table_name} (Composite PK jump not supported)", severity="warning")

    # --- TABLE LOADING ---
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        list_widget = getattr(event, "list_view", None) or getattr(event, "control", None)
        list_id = getattr(list_widget, "id", None)

        if list_id == "table_list" and event.item and event.item.name:
            self.current_table = event.item.name
            self.query_one("#table_label").update(f"Browsing: [bold yellow]{self.current_table}[/]")
            self.load_table_data(self.current_table)
        elif list_id == "report_list" and event.item and event.item.name:
            self.update_report_description(event.item.name)
        elif list_id == "query_list" and event.item and event.item.name:
            self.update_query_description(event.item.name)

    def normalize_data_keys(self, data):
        """
        Recursively converts all dictionary keys in a list of dicts to lowercase.
        This handles the issue where some SQL drivers return UPPERCASE columns
        while TABLE_CONFIG uses lowercase.
        """
        if not data:
            return []
        
        normalized = []
        for row in data:
            new_row = {k.lower(): v for k, v in row.items()}
            normalized.append(new_row)
        return normalized

    def load_table_data(self, table_name, data=None, limit=100):
        if not self.conn: return
        table = self.query_one("#main_table", DataTable)
        table.clear(columns=True)
        # Clear any previous painted row highlight to avoid stale backgrounds
        try:
            table.last_highlighted_row = None
        except Exception:
            pass
        
        if data is None:
            data = db_utils.view_table(self.conn, table_name, limit=limit)
        
        if not data:
            self.notify("No records found.")
            return

        # FIX: Normalize keys to lowercase so they match TABLE_CONFIG
        data = self.normalize_data_keys(data)

        config = TABLE_CONFIG.get(table_name, {})
        
        # If we have data, use the keys from the first row as headers
        # This ensures we show all columns returned by the DB
        headers = list(data[0].keys())
        
        pks = set()
        if config.get('pk'): pks.add(config['pk'])
        if config.get('pks'): pks.update(config['pks'])
        fks = {col['col']: col for col in config.get('columns', []) if col['type'] == 'fk'}

        styled_headers = []
        for h in headers:
            label = h
            if h in pks: label += " 🔑"
            if h in fks: label += " 🔗"
            styled_headers.append(Text(label, style="bold cyan"))
            
        table.add_columns(*styled_headers)
        table.misc_col_map = headers 

        for row in data:
            table.add_row(*[str(row.get(h, "")) for h in headers])
        
        self.current_table_data = data 
        
        # Clear filter input on fresh load/refresh
        self.query_one("#filter_input").value = ""

    # --- SELECTION & DRILL DOWN ---
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Capture the selected row for CRUD operations."""
        # NOTE: When using cursor_type='cell', this may not fire on simple clicks.
        # Use on_data_table_cell_selected to capture row data instead.
        if event.data_table.id != "main_table": return
        if not self.current_table or not hasattr(self, 'current_table_data'): return
        
        row_index = event.cursor_row
        if row_index < len(self.current_table_data):
            self.current_row_data = self.current_table_data[row_index]
            
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle foreign key jump AND capture row selection for CRUD."""
        if event.data_table.id != "main_table": return
        if not self.current_table: return

        # 1. Capture Row Data (To ensure CRUD in Code 1 works with Cell Cursor)
        if hasattr(self, 'current_table_data'):
            row_index = event.coordinate.row
            if row_index < len(self.current_table_data):
                self.current_row_data = self.current_table_data[row_index]
        
        # 2. FK Navigation Logic (From Code 2)
        col_index = event.coordinate.column
        # Use the stored raw headers
        raw_headers = getattr(event.data_table, "misc_col_map", [])
        if col_index >= len(raw_headers): return
        
        col_name = raw_headers[col_index]
        config = TABLE_CONFIG.get(self.current_table, {})
        
        # Case-insensitive check for column definition in config
        col_def = None
        for c in config.get('columns', []):
            if c['col'].lower() == col_name.lower():
                col_def = c
                break

        if col_def and col_def['type'] == 'fk':
            ref_table = col_def['ref_table']
            val = str(event.value).strip() # Ensure we have a clean string value
            self.notify(f"Jumping to {ref_table}...", title="Navigation")
            self.switch_to_table(ref_table, val)

    # --- BUTTON HANDLERS ---
    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Create a pseudo-event object or handle string IDs if necessary, 
        # but Button.Pressed event has a .button attribute which is the widget.
        if isinstance(event, Button): # Handle manual calls from actions
            bid = event.id
        else:
            bid = event.button.id
        
        if bid == "btn_quit":
            self.exit()
        
        elif bid == "btn_refresh":
            if self.current_table:
                # Pass None to data to force a fresh fetch from DB
                self.load_table_data(self.current_table, data=None)
                self.notify("Table refreshed.")
        
        elif bid == "btn_filter":
            if not self.current_table: return
            term = self.query_one("#filter_input").value.strip()
            if term:
                results = db_utils.search_table(self.conn, self.current_table, term)
                # Manually update table with search results
                self.load_table_data(self.current_table, data=results)
                self.notify(f"Filter applied: {len(results)} records")
            else:
                self.load_table_data(self.current_table) # Clear filter

        elif bid == "btn_recent":
            if self.current_table:
                config = TABLE_CONFIG.get(self.current_table, {})
                pk = config.get('pk')
                data = db_utils.get_recent_records(self.conn, self.current_table, pk)
                self.load_table_data(self.current_table, data)
                self.notify(f"Showing last 5 entries for {self.current_table}")
        
        elif bid == "btn_add":
            if not self.current_table:
                self.notify("Select a table first!", severity="warning")
                return
            self.push_screen(RecordForm(self.conn, self.current_table, mode="add"), self.handle_add_submit)
            
        elif bid == "btn_update":
            if not self.current_table:
                self.notify("Select a table first.", severity="warning")
                return
            
            table = self.query_one("#main_table", DataTable)
            # Fetch row index safely
            row_index = table.cursor_row
            
            if row_index < 0 or row_index >= len(self.current_table_data):
                self.notify("Select a row to update!", severity="warning")
                return
            
            row_data = self.current_table_data[row_index]
            self.push_screen(RecordForm(self.conn, self.current_table, row_data, mode="update"), self.handle_update_submit)
            
        elif bid == "btn_delete":
            if not self.current_table: return

            table = self.query_one("#main_table", DataTable)
            # Fetch row index safely
            row_index = table.cursor_row
            
            if row_index < 0 or row_index >= len(self.current_table_data):
                self.notify("Select a row to delete!", severity="warning")
                return
            
            # Temporarily store for confirmation handler
            self.row_to_delete = self.current_table_data[row_index]
            self.push_screen(ConfirmationModal("Delete this record?"), self.handle_delete_confirm)

        elif bid == "btn_do_search":
            term = self.query_one("#search_input").value
            if term and self.conn:
                res = db_utils.search_global(self.conn, term)
                self.populate_search_table(res)
        
        elif bid == "btn_run_report":
            self.run_selected_report()
        
        elif bid == "btn_report_search":
            term = self.query_one("#report_search_input", Input).value
            self.apply_report_search(term)

        elif bid == "btn_report_reset":
            self.query_one("#report_search_input", Input).value = ""
            self.render_report_results(self.report_results, "Run a report first.")

        elif bid.startswith("btn_query_"):
            self.handle_query_action(bid)
        elif bid == "btn_run_query":
            self.run_selected_query()
        elif bid == "btn_query_search":
            term = self.query_one("#query_search_input", Input).value
            self.apply_query_search(term)
        elif bid == "btn_query_reset":
            self.query_one("#query_search_input", Input).value = ""
            self.render_query_results(self.query_results, "Run a query first.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "filter_input":
            self.on_button_pressed(Button(id="btn_filter"))
        elif event.input.id == "search_input":
            self.on_button_pressed(Button(id="btn_do_search"))
        elif event.input.id == "report_search_input":
            self.on_button_pressed(Button(id="btn_report_search"))
        # Make query inputs actionable with Enter
        elif event.input.id in {"input_query_tournament", "input_query_min_wins"}:
            # Run Selection query
            self.on_button_pressed(Button(id="btn_query_selection"))
        elif event.input.id == "input_query_trainer":
            # Run Projection query
            self.on_button_pressed(Button(id="btn_query_projection"))
        elif event.input.id == "input_query_avg_tournament":
            # Run Aggregate query
            self.on_button_pressed(Button(id="btn_query_average"))
        elif event.input.id == "input_query_species_prefix":
            # Run Search query
            self.on_button_pressed(Button(id="btn_query_species"))
        # Also allow Enter to trigger Run Selected Query (reports-like UX)
        elif event.input.id in {
            "input_query_tournament",
            "input_query_min_wins",
            "input_query_trainer",
            "input_query_avg_tournament",
            "input_query_species_prefix",
        }:
            self.on_button_pressed(Button(id="btn_run_query"))

    # --- CRUD CALLBACKS ---
    def handle_add_submit(self, data):
        if not data: return
        
        config = TABLE_CONFIG.get(self.current_table, {})
        pk = config.get('pk')
        prefix = config.get('prefix')
        
        if pk and prefix and (pk not in data or not data[pk]):
            new_id = db_utils.get_next_id(self.conn, self.current_table, pk, prefix)
            data[pk] = new_id
            self.notify(f"Generated ID: {new_id}")
        # Secure: validate identifiers (table and columns); values remain parameterized
        try:
            clean_table = db_utils.validate_identifier(self.current_table)
            columns = [db_utils.validate_identifier(col) for col in data.keys()]
        except ValueError as ve:
            self.notify(f"Security check failed: {ve}", severity="error")
            return

        placeholders = ["%s"] * len(columns)
        sql = f"INSERT INTO {clean_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, list(data.values()))
            self.notify("Record Added!", severity="success")
            self.load_table_data(self.current_table)
        except Exception as e:
            self.notify(f"Error adding record: {e}", severity="error")

    def handle_update_submit(self, data):
        if not data: return
        
        config = TABLE_CONFIG.get(self.current_table, {})
        
        table = self.query_one("#main_table", DataTable)
        row_index = table.cursor_row
        original_row_data = self.current_table_data[row_index]
        
        pk_dict = {}
        if config.get('pk'):
            pk_key = config['pk']
            pk_dict[pk_key] = original_row_data.get(pk_key)
        elif config.get('pks'):
            for k in config['pks']:
                pk_dict[k] = original_row_data.get(k)
        
        if not pk_dict or any(v is None for v in pk_dict.values()):
            self.notify(f"Update error: PKs missing in selected row. Keys: {list(pk_dict.keys())}", severity="error")
            return
        
        updates = {}
        display_columns = list(config.get("columns", []))
        single_pk = config.get('pk')
        if single_pk and not any(c['col'] == single_pk for c in display_columns):
            display_columns.insert(0, {"col": single_pk, "type": "str"})

        for col_def in display_columns:
             col_name = col_def['col']
             if col_name in data:
                 new_val = data[col_name]
                 old_val = original_row_data.get(col_name)
                 
                 old_str = str(old_val) if old_val is not None else ""
                 new_str = str(new_val) if new_val is not None else ""

                 if old_str != new_str:
                     updates[col_name] = new_val
        
        if not updates:
             self.notify("No changes detected.", severity="warning")
             return

        if db_utils.update_record(self.conn, self.current_table, pk_dict, updates):
            self.notify("Record Updated!", severity="success")
            self.load_table_data(self.current_table)
        else:
            self.notify("Update failed. Check database constraints.", severity="error")

    def handle_delete_confirm(self, confirmed):
        if not confirmed or not hasattr(self, 'row_to_delete'): return
        
        config = TABLE_CONFIG.get(self.current_table, {})
        pk_dict = {}
        
        if config.get('pk'):
            pk_key = config['pk']
            pk_dict[pk_key] = self.row_to_delete.get(pk_key)
        elif config.get('pks'):
            for k in config['pks']:
                pk_dict[k] = self.row_to_delete.get(k)
                
        if db_utils.delete_record(self.conn, self.current_table, pk_dict):
            self.notify("Record Deleted!", severity="success")
            self.load_table_data(self.current_table)
        else:
            self.notify("Delete failed.", severity="error")

    # --- HELPERS ---
    def populate_search_table(self, results):
        table = self.query_one("#search_results_table", DataTable)
        table.clear(columns=True)
        # Create two columns: Source and the Content
        table.add_columns(
            Text("Source Table", style="bold cyan"),
            Text("Matched Record Details", style="bold yellow")
        )

        if not results:
            self.notify("No matches found.")
            return

        # Iterate through the results and format each matched row
        for table_name, rows in results.items():
            for row in rows:
                formatted_parts = []
                for key, value in row.items():
                    clean_key = key.replace("_", " ").title()
                    part = f"[bold #888888]{clean_key}:[/] [white]{value}[/]"
                    formatted_parts.append(part)

                full_text = "  |  ".join(formatted_parts)
                table.add_row(table_name, Text.from_markup(full_text))

        self.notify(f"Found matches in {len(results)} tables.")

    def execute_sql(self, sql, params=None):
        if not self.conn:
            self.notify("Connect to the database first.", severity="warning")
            return []
        try:
            with self.conn.cursor() as cursor:
                # Print SQL and params for visibility in terminal when Queries/Reports use this path
                try:
                    print("Executing SQL (Generic):\n" + sql.strip())
                    if params:
                        print("Params:", params)
                except Exception:
                    pass
                cursor.execute(sql, params or ())
                return cursor.fetchall()
        except Exception as e:
            self.notify(f"Query failed: {e}", severity="error")
            return []

    def render_rows_to_table(self, table: DataTable, rows, empty_message="No data found."):
        table.clear(columns=True)
        if not rows:
            self.notify(empty_message, severity="warning")
            return
        headers = list(rows[0].keys())
        table.add_columns(*headers)
        for row in rows:
            table.add_row(*[str(row.get(h, "")) for h in headers])

    def render_report_results(self, rows=None, empty_message="Report returned no rows."):
        dataset = rows if rows is not None else self.report_results
        table = self.query_one("#report_table", DataTable)
        if dataset:
            self.render_rows_to_table(table, dataset, empty_message)
        else:
            table.clear(columns=True)
            self.notify(empty_message, severity="warning")

    def apply_report_search(self, term):
        term = (term or "").strip().lower()
        if not self.report_results:
            self.render_report_results([], "Run a report first.")
            return
        if not term:
            self.render_report_results(self.report_results, "Report returned no rows.")
            return
        filtered = []
        for row in self.report_results:
            if any(term in str(value).lower() for value in row.values()):
                filtered.append(row)
        self.render_report_results(filtered, "No results match that filter.")

    def update_report_description(self, report_key):
        report = REPORT_DEFINITIONS.get(report_key)
        desc_widget = self.query_one("#report_description", Static)
        if not report:
            desc_widget.update("Report metadata missing.")
            self.selected_report_key = None
            return
        self.selected_report_key = report_key
        desc_text = Text.from_markup(
            f"[bold]{report['label']}[/bold]\n{report['description']}"
        )
        desc_widget.update(desc_text)

    # --- QUERIES TAB HELPERS (Reports-like UX) ---
    def update_query_description(self, query_key):
        qdef = QUERY_DEFINITIONS.get(query_key)
        desc_widget = self.query_one("#query_description", Static)
        if not qdef:
            desc_widget.update("Query metadata missing.")
            self.selected_query_key = None
            return
        self.selected_query_key = query_key
        desc_text = Text.from_markup(
            f"[bold]{qdef['label']}[/bold]\n{qdef['description']}"
        )
        desc_widget.update(desc_text)

    def render_query_results(self, rows=None, empty_message="Query returned no rows."):
        dataset = rows if rows is not None else self.query_results
        table = self.query_one("#query_table", DataTable)
        if dataset:
            self.render_rows_to_table(table, dataset, empty_message)
        else:
            table.clear(columns=True)
            self.notify(empty_message, severity="warning")

    def set_query_sql_preview(self, sql: str, params=None):
        """Show the parameterized SQL and params in the Queries panel."""
        try:
            preview = f"[bold]SQL:[/bold]\n{sql.strip()}"
            if params is not None:
                preview += f"\n[bold]Params:[/bold] {repr(tuple(params if isinstance(params, (list, tuple)) else (params,)))}"
            self.query_one("#query_sql_preview", Static).update(Text.from_markup(preview))
        except Exception:
            # Fall back to a small toast
            self.notify("SQL preview not available.", severity="warning")

    def apply_query_search(self, term):
        term = (term or "").strip().lower()
        if not self.query_results:
            self.render_query_results([], "Run a query first.")
            return
        if not term:
            self.render_query_results(self.query_results, "Query returned no rows.")
            return
        filtered = []
        for row in self.query_results:
            if any(term in str(value).lower() for value in row.values()):
                filtered.append(row)
        self.render_query_results(filtered, "No results match that filter.")

    def run_selected_query(self):
        if not self.selected_query_key:
            self.notify("Select a query in the list first.", severity="warning")
            return
        key = self.selected_query_key
        rows = []
        if key == "q_selection":
            tournament = self.get_input_value("#input_query_tournament", "")
            min_wins_val = self.safe_int(self.get_input_value("#input_query_min_wins", ""), 0)
            rows = db_utils.query_trainers_with_min_wins(self.conn, tournament, min_wins_val) or []
            sql_preview = """
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
                ORDER BY total_wins DESC, TR.name;
            """
            self.set_query_sql_preview(sql_preview, (tournament, min_wins_val))
        elif key == "q_projection":
            trainer_id = self.get_input_value("#input_query_trainer", "")
            full = db_utils.query_pokemon_by_trainer(self.conn, trainer_id) or []
            rows = [{"nickname": r.get("nickname"), "level": r.get("level")} for r in full]
            sql_preview = """
                SELECT 
                    RP.nickname,
                    RP.level
                FROM RegisteredPokemon RP
                WHERE RP.trainer_id = %s
                ORDER BY RP.level DESC;
            """
            self.set_query_sql_preview(sql_preview, (trainer_id,))
        elif key == "q_aggregate":
            tour = self.get_input_value("#input_query_avg_tournament", "")
            rows = db_utils.query_average_level_for_tournament(self.conn, tour) or []
            sql_preview = """
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
            self.set_query_sql_preview(sql_preview, (tour,))
        elif key == "q_badge_leaderboard":
            limit_val = self.safe_int(self.get_input_value("#input_query_badge_limit", ""), 0)
            rows = db_utils.query_badge_leaderboard(self.conn, limit_val) or []
            sql_preview = """
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
            self.set_query_sql_preview(sql_preview, (limit_val,))
        else:
            self.notify("Unsupported query.", severity="error")
            return

        self.query_results = rows
        self.query_one("#query_search_input", Input).value = ""
        self.render_query_results(self.query_results, "Query returned no rows.")
        if rows:
            self.notify(f"Query ready: {len(rows)} rows.")

    def run_selected_report(self):
        if not self.selected_report_key:
            self.notify("Select a report in the list first.", severity="warning")
            return
        report = REPORT_DEFINITIONS.get(self.selected_report_key)
        if not report:
            self.notify("Report definition missing.", severity="error")
            return
        rows = self.execute_sql(report["sql"])
        self.report_results = rows or []
        search_input = self.query_one("#report_search_input", Input)
        search_input.value = ""
        self.render_report_results(self.report_results, "Report returned no rows.")
        if rows:
            self.notify(f"Report ready: {len(rows)} rows.")

    def safe_int(self, value, fallback):
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def get_input_value(self, selector, fallback=""):
        try:
            val = self.query_one(selector, Input).value
            return val.strip() if val else fallback
        except Exception:
            return fallback

    def handle_query_action(self, action_id):
        table = self.query_one("#query_table", DataTable)

        if action_id == "btn_query_selection":
            tournament = self.get_input_value("#input_query_tournament", QUERY_DEFAULTS["tournament"])
            min_wins_val = self.safe_int(self.get_input_value("#input_query_min_wins", str(QUERY_DEFAULTS["min_wins"])), QUERY_DEFAULTS["min_wins"])
            # Use secure helper in db_utils
            rows = db_utils.query_trainers_with_min_wins(self.conn, tournament, min_wins_val)
            sql_preview = """
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
                ORDER BY total_wins DESC, TR.name;
            """
            self.set_query_sql_preview(sql_preview, (tournament, min_wins_val))
            self.render_rows_to_table(table, rows, "No trainers matched that criteria.")
            if rows:
                self.notify(f"Selection query returned {len(rows)} trainers.")
            return

        if action_id == "btn_query_projection":
            trainer_id = self.get_input_value("#input_query_trainer", QUERY_DEFAULTS["trainer_id"])
            # Use helper and project to nickname + level only
            rows_full = db_utils.query_pokemon_by_trainer(self.conn, trainer_id)
            rows = []
            for r in rows_full or []:
                rows.append({"nickname": r.get("nickname"), "level": r.get("level")})
            sql_preview = """
                SELECT 
                    RP.nickname,
                    RP.level
                FROM RegisteredPokemon RP
                WHERE RP.trainer_id = %s
                ORDER BY RP.level DESC;
            """
            self.set_query_sql_preview(sql_preview, (trainer_id,))
            self.render_rows_to_table(table, rows, "No Pokémon found for that trainer.")
            if rows:
                self.notify(f"Projection query returned {len(rows)} Pokémon.")
            return

        if action_id == "btn_query_average":
            tour = self.get_input_value("#input_query_avg_tournament", QUERY_DEFAULTS["aggregate_tournament"])
            rows = db_utils.query_average_level_for_tournament(self.conn, tour)
            sql_preview = """
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
            self.set_query_sql_preview(sql_preview, (tour,))
            self.render_rows_to_table(table, rows, "No aggregate data for that tournament.")
            if rows:
                self.notify("Aggregate query complete.")
            return

        if action_id == "btn_query_species":
            prefix = self.get_input_value("#input_query_species_prefix", QUERY_DEFAULTS["species_prefix"])
            rows_full = db_utils.query_species_by_prefix(self.conn, prefix)
            # Keep simple columns for display
            rows = []
            for r in rows_full or []:
                rows.append({"species_id": r.get("species_id"), "species_name": r.get("species_name")})
            sql_preview = """
                SELECT species_id, species_name
                FROM PokemonSpecies
                WHERE species_name LIKE %s
                ORDER BY species_name;
            """
            self.set_query_sql_preview(sql_preview, (f"{prefix}%",))
            self.render_rows_to_table(table, rows, "No species matched that prefix.")
            if rows:
                self.notify(f"Found {len(rows)} species starting with {prefix}.")
            return

        if action_id == "btn_query_badges":
            limit_val = self.safe_int(self.get_input_value("#input_query_badge_limit", str(QUERY_DEFAULTS["badge_limit"])), QUERY_DEFAULTS["badge_limit"])
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
            rows = self.execute_sql(sql, (limit_val,))
            self.render_rows_to_table(table, rows, "No badge data available.")
            if rows:
                self.notify("Badge leaderboard ready.")
            return

        if action_id == "btn_query_elite":
            min_level = self.safe_int(self.get_input_value("#input_query_min_level", str(QUERY_DEFAULTS["min_level"])), QUERY_DEFAULTS["min_level"])
            sql = """
                SELECT 
                    RP.pokemon_id,
                    COALESCE(RP.nickname, PS.species_name) AS pokemon_name,
                    RP.level,
                    PS.species_name,
                    T.name AS trainer_name
                FROM RegisteredPokemon RP
                JOIN PokemonSpecies PS ON RP.species_id = PS.species_id
                JOIN Trainer T ON RP.trainer_id = T.trainer_id
                WHERE RP.level >= %s
                ORDER BY RP.level DESC, pokemon_name
                LIMIT 50;
            """
            rows = self.execute_sql(sql, (min_level,))
            self.render_rows_to_table(table, rows, "No elite Pokémon at that level yet.")
            if rows:
                self.notify("Elite roster ready.")
            return

        if action_id == "btn_query_region":
            sql = """
                SELECT 
                    R.region_name,
                    COUNT(DISTINCT T.tournament_id) AS tournaments_hosted,
                    COUNT(DISTINCT TE.trainer_id) AS visiting_trainers,
                    ROUND(AVG(LS.year), 1) AS avg_season_year
                FROM Region R
                LEFT JOIN City C ON C.region_id = R.region_id
                LEFT JOIN Tournament T ON T.city_id = C.city_id
                LEFT JOIN TournamentEntry TE ON TE.tournament_id = T.tournament_id
                LEFT JOIN LeagueSeason LS ON T.season_id = LS.season_id
                GROUP BY R.region_id, R.region_name
                ORDER BY tournaments_hosted DESC, visiting_trainers DESC;
            """
            rows = self.execute_sql(sql)
            self.render_rows_to_table(table, rows, "No regional data available.")
            if rows:
                self.notify("Region insights ready.")

if __name__ == "__main__":
    app = PokemonTUI()
    app.run()