import sys
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid, VerticalScroll
from textual.widgets import Header, Footer, Button, Static, DataTable, Input, Label, ListView, ListItem, TabbedContent, TabPane, SelectionList
from textual.screen import ModalScreen, Screen
from textual import on
from textual.binding import Binding
from textual.validation import Number, Function
from rich.text import Text
import db_utils

# =============================================================================
# CONFIGURATION
# =============================================================================

TABLE_CONFIG = {
    "Trainer": {
        "pk": "trainer_id",
        "prefix": "T",
        "columns": [
            {"col": "name", "type": "str"},
            {"col": "gender", "type": "enum", "choices": ["Male", "Female", "Other"]},
            {"col": "birth_date", "type": "date"},
            {"col": "contact_info_email", "type": "str"},
            {"col": "contact_info_phone", "type": "str"},
            {"col": "region_id", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"}
        ]
    },
    "PokemonSpecies": {
        "pk": "species_id",
        "prefix": "S",
        "columns": [
            {"col": "species_name", "type": "str"},
            {"col": "base_hp", "type": "int"},
            {"col": "base_attack", "type": "int"},
            {"col": "base_defense", "type": "int"},
            {"col": "base_speed", "type": "int"},
            {"col": "primary_type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "secondary_type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
        ]
    },
    "RegisteredPokemon": {
        "pk": "pokemon_id",
        "prefix": "P",
        "columns": [
            {"col": "species_id", "type": "fk", "ref_table": "PokemonSpecies", "ref_pk": "species_id"},
            {"col": "trainer_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "nickname", "type": "str"},
            {"col": "level", "type": "int"},
            {"col": "experience_points", "type": "int"},
            {"col": "registration_date", "type": "date"},
        ]
    },
    "Gym": {
        "pk": "gym_id",
        "prefix": "G",
        "columns": [
            {"col": "gym_name", "type": "str"},
            {"col": "city_id", "type": "fk", "ref_table": "City", "ref_pk": "city_id"},
            {"col": "specialization_type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
        ]
    },
    "LeagueSeason": {
        "pk": "season_id",
        "prefix": "L",
        "columns": [
            {"col": "year", "type": "int"},
            {"col": "region_id", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"},
            {"col": "theme", "type": "str"},
        ]
    },
    "GymSeasonRegistry": {
        "pk": "registry_id",
        "prefix": "E",
        "columns": [
            {"col": "season_id", "type": "fk", "ref_table": "LeagueSeason", "ref_pk": "season_id"},
            {"col": "gym_id", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "leader_id", "type": "fk", "ref_table": "GymLeader", "ref_pk": "leader_id"},
        ]
    },
    "Tournament": {
        "pk": "tournament_id",
        "prefix": "O",
        "columns": [
            {"col": "tournament_name", "type": "str"},
            {"col": "start_date", "type": "date"},
            {"col": "end_date", "type": "date"},
            {"col": "city_id", "type": "fk", "ref_table": "City", "ref_pk": "city_id"},
            {"col": "season_id", "type": "fk", "ref_table": "LeagueSeason", "ref_pk": "season_id"},
        ]
    },
    "TournamentEntry": {
        "pks": ["tournament_id", "trainer_id"],
        "columns": [
            {"col": "tournament_id", "type": "fk", "ref_table": "Tournament", "ref_pk": "tournament_id"},
            {"col": "trainer_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "registration_date", "type": "date"},
        ]
    },
    "Match_Table": {
        "pks": ["tournament_id", "match_number"],
        "columns": [
            {"col": "tournament_id", "type": "fk", "ref_table": "Tournament", "ref_pk": "tournament_id"},
            {"col": "match_number", "type": "int"},
            {"col": "trainer1_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "trainer2_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "winner_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "match_date", "type": "date"},
            {"col": "round_number", "type": "int"},
        ]
    },
    "GymBattle": {
        "pk": "battle_id",
        "prefix": "B",
        "columns": [
            {"col": "challenger_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "gym_id", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "leader_id", "type": "fk", "ref_table": "GymLeader", "ref_pk": "leader_id"},
            {"col": "battle_date", "type": "date"},
            {"col": "result", "type": "enum", "choices": ["Win", "Loss", "Draw"]},
        ]
    },
    "GymBadge": {
        "pks": ["gym_id", "badge_number"],
        "columns": [
            {"col": "gym_id", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "badge_number", "type": "int"},
            {"col": "date_earned", "type": "date"},
            {"col": "trainer_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
        ]
    },
    "Move": {
        "pk": "move_id",
        "prefix": "M",
        "columns": [
            {"col": "move_name", "type": "str"},
            {"col": "power", "type": "int"},
            {"col": "accuracy", "type": "int"},
            {"col": "pp", "type": "int"},
            {"col": "type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "category", "type": "enum", "choices": ["Physical", "Special", "Status"]}
        ]
    },
    "Region": {
        "pk": "region_id",
        "prefix": "R",
        "columns": [
            {"col": "region_name", "type": "str"},
            {"col": "main_city", "type": "str"}
        ]
    },
    "City": {
        "pk": "city_id",
        "prefix": "C",
        "columns": [
            {"col": "city_name", "type": "str"},
            {"col": "region_id", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"}
        ]
    },
    "Type": {
        "pk": "type_id",
        "prefix": "Y",
        "columns": [{"col": "type_name", "type": "str"}]
    },
    "Ability": {
        "pk": "ability_id",
        "prefix": "A",
        "columns": [{"col": "ability_name", "type": "str"}, {"col": "effect_description", "type": "str"}]
    },
    "GymLeader": {
         "pk": "leader_id",
         "columns": [{"col": "specialty_type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"}, {"col": "years_of_experience", "type": "int"}]
    }
}

LOGO_ASCII = r"""
   ___      _                             
  / _ \___ | | _____ _ __ ___   ___  _ __ 
 / /_)/ _ \| |/ / _ \ '_ ` _ \ / _ \| '_ \\
/ ___/ (_) |   <  __/ | | | | | (_) | | | |
\/    \___/|_|\_\___|_| |_| |_|\___/|_| |_|
                                          
   DB MANAGER v2.0 - [bold yellow]Phase 4[/bold yellow]
"""

# =============================================================================
# SCREENS & MODALS
# =============================================================================

class LoginScreen(ModalScreen):
    """Modal to prompt for database credentials."""
    
    CSS = """
    LoginScreen {
        align: center middle;
        background: $background 50%;
    }
    
    #login_dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto;
        padding: 2;
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
    }
    
    #login_label {
        column-span: 2;
        content-align: center middle;
        text-style: bold;
        margin-bottom: 1;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
        column-span: 2;
    }
    
    Input {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Database Login", id="login_label"),
            Label("Host:"),
            Input(placeholder="localhost", id="host", value="localhost"),
            Label("User:"),
            Input(placeholder="root", id="user", value="root"),
            Label("Password:"),
            Input(placeholder="", password=True, id="password"),
            Label("Database:"),
            Input(placeholder="pokemon_league_db", id="db_name", value="pokemon_league_db"),
            Button("Connect", variant="success", id="btn_connect"),
            id="login_dialog"
        )

    def on_mount(self) -> None:
        # Force focus to the first input field to ensure keyboard works immediately
        self.query_one("#host").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_connect":
            self.submit()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Allow pressing Enter to submit
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
    RecordForm {
        align: center middle;
        background: $background 80%;
    }
    
    #form_container {
        width: 70%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }
    
    #form_title {
        text-style: bold;
        border-bottom: solid $secondary;
        margin-bottom: 1;
        text-align: center;
    }
    
    .field_label {
        margin-top: 1;
    }
    
    #form_buttons {
        dock: bottom;
        height: auto;
        margin-top: 2;
    }
    
    Button {
        margin-right: 1;
    }
    """

    def __init__(self, table_name, record_data=None, mode="add"):
        super().__init__()
        self.table_name = table_name
        self.record_data = record_data or {}
        self.mode = mode # "add" or "update"

    def compose(self) -> ComposeResult:
        config = TABLE_CONFIG.get(self.table_name, {})
        columns = config.get("columns", [])
        
        title = f"{self.mode.upper()} Record: {self.table_name}"
        
        with Container(id="form_container"):
            yield Label(title, id="form_title")
            
            with VerticalScroll():
                for col_def in columns:
                    col_name = col_def['col']
                    col_type = col_def['type']
                    
                    # Determine label text
                    label_text = f"{col_name.replace('_', ' ').title()} ({col_type})"
                    if col_type == 'fk':
                        label_text += f" -> {col_def['ref_table']}"
                    elif col_type == 'enum':
                        label_text += f" [{', '.join(col_def.get('choices', []))}]"
                    
                    yield Label(label_text, classes="field_label")
                    
                    # Pre-fill value if updating
                    value = str(self.record_data.get(col_name, ""))
                    
                    # Don't allow editing PKs in Update mode usually, but here we might need to display them
                    # For this simple TUI, we'll just show inputs.
                    
                    inp = Input(value=value, id=f"inp_{col_name}")
                    yield inp
            
            with Horizontal(id="form_buttons"):
                yield Button("Save", variant="success", id="btn_save")
                yield Button("Cancel", variant="error", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        elif event.button.id == "btn_save":
            # Collect data
            data = {}
            config = TABLE_CONFIG.get(self.table_name, {})
            columns = config.get("columns", [])
            
            for col_def in columns:
                col_name = col_def['col']
                val = self.query_one(f"#inp_{col_name}", Input).value.strip()
                
                # Handle empty strings for non-required fields or numbers
                if val == "":
                    val = None
                data[col_name] = val
            
            self.dismiss(data)


class ConfirmationModal(ModalScreen):
    """Simple confirmation dialog."""
    CSS = """
    ConfirmationModal { align: center middle; background: $background 80%; }
    #confirm_box { width: 40; height: auto; background: $surface; border: thick $error; padding: 2; }
    #confirm_text { text-align: center; margin-bottom: 2; }
    """
    def __init__(self, message):
        super().__init__()
        self.message = message
        
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
    def __init__(self, table_name, data_row):
        super().__init__()
        self.table_name = table_name
        self.data_row = data_row

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
    #sidebar { dock: left; width: 30; height: 100%; background: $panel; border-right: tall $primary; }
    #main_content { height: 100%; width: 100%; padding: 1; }
    #logo { color: $accent; content-align: center middle; height: 10; margin-bottom: 1; }
    DataTable { height: 1fr; border: tall $primary; }
    Button { width: 100%; margin-bottom: 1; }
    #modal_container { padding: 2; background: $surface; border: thick $primary; width: 60%; height: auto; align: center middle; }
    #modal_title { text-style: bold; padding-bottom: 1; border-bottom: solid $secondary; width: 100%; text-align: center; }
    .report_box { border: solid $secondary; padding: 1; margin-bottom: 1; }
    .crud_buttons { height: auto; dock: bottom; margin-top: 1; }
    #search_row { height: auto; margin-bottom: 1; }
    #search_input { width: 80%; }
    #btn_do_search { width: 20%; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self):
        super().__init__()
        self.conn = None
        self.current_table = None
        self.current_row_key = None # Store PK of selected row
        self.current_row_data = None

    def on_mount(self) -> None:
        self.title = "Pokemon League DB Manager"
        self.push_screen(LoginScreen(), self.login_callback)

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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            with Horizontal():
                with Container(id="sidebar"):
                    yield Static(LOGO_ASCII, id="logo")
                    yield Label("Tables:", classes="box_label")
                    
                    list_items = []
                    for t_name in TABLE_CONFIG.keys():
                        list_items.append(ListItem(Label(t_name), name=t_name))
                    yield ListView(*list_items, id="table_list")
                    
                    yield Static("\n")
                    yield Button("Add New", id="btn_add", variant="success")
                    yield Button("Update", id="btn_update", variant="warning")
                    yield Button("Delete", id="btn_delete", variant="error")
                    yield Button("Refresh", id="btn_refresh", variant="primary")
                    yield Button("Recent 5", id="btn_recent", variant="default")
                    yield Button("Quit", id="btn_quit", variant="error")

                with Container(id="main_content"):
                    with TabbedContent(initial="tab_data"):
                        with TabPane("Data Browser", id="tab_data"):
                            yield Label("Select a table from the sidebar...", id="table_label")
                            yield DataTable(id="main_table", cursor_type="row")
                        
                        with TabPane("Global Search", id="tab_search"):
                            yield Label("Search Keywords:")
                            with Horizontal(id="search_row"):
                                yield Input(placeholder="Search term...", id="search_input", classes="search_box")
                                yield Button("Go", id="btn_do_search", classes="search_btn", variant="primary")
                            yield DataTable(id="search_results_table")
                        
                        with TabPane("Reports", id="tab_reports"):
                            yield Label("Available Reports:")
                            with Horizontal():
                                yield Button("Region Management", id="rep_1", classes="report_box")
                                yield Button("Assignments", id="rep_2", classes="report_box")
                                yield Button("Abilities", id="rep_3", classes="report_box")
                            yield DataTable(id="report_table")
        yield Footer()

    # --- TABLE LOADING ---
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.name:
            self.current_table = event.item.name
            self.query_one("#table_label").update(f"Browsing: [bold yellow]{self.current_table}[/]")
            self.load_table_data(self.current_table)

    def load_table_data(self, table_name, data=None):
        if not self.conn: return
        table = self.query_one("#main_table", DataTable)
        table.clear(columns=True)
        
        if data is None:
            data = db_utils.view_table(self.conn, table_name)
        
        if not data:
            self.notify("No records found.")
            return

        # Setup Columns
        config = TABLE_CONFIG.get(table_name, {})
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
        table.misc_col_map = headers # Save raw headers for lookups

        for row in data:
            # Store raw row data in the key if possible, or just handle selection
            # Textual keys are strings, so we rely on row index mapping or re-fetch
            # For simplicity, we will store the whole row dict in a list to access later
            table.add_row(*[str(row.get(h, "")) for h in headers])
        
        # We need a way to map the selected row back to data for Update/Delete
        # Textual DataTables don't store arbitrary objects easily.
        # We will rely on `data` being in sync with `table.rows`.
        self.current_table_data = data 

    # --- SELECTION & DRILL DOWN ---
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Capture the selected row for CRUD operations."""
        if not self.current_table or not hasattr(self, 'current_table_data'): return
        
        row_index = event.cursor_row
        if row_index < len(self.current_table_data):
            self.current_row_data = self.current_table_data[row_index]
            
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle foreign key drill-down."""
        if event.data_table.id != "main_table": return
        if not self.current_table: return
        
        # Update selection tracking first
        self.on_data_table_row_selected(DataTable.RowSelected(event.data_table, event.coordinate.row))

        # Check if FK column
        col_index = event.coordinate.column
        raw_headers = getattr(event.data_table, "misc_col_map", [])
        if col_index >= len(raw_headers): return
        
        col_name = raw_headers[col_index]
        config = TABLE_CONFIG.get(self.current_table, {})
        col_def = next((c for c in config.get('columns', []) if c['col'] == col_name), None)

        if col_def and col_def['type'] == 'fk':
            ref_table = col_def['ref_table']
            ref_pk = col_def['ref_pk']
            val = event.value
            
            try:
                with self.conn.cursor() as cursor:
                    sql = f"SELECT * FROM {ref_table} WHERE {ref_pk} = %s"
                    cursor.execute(sql, (val,))
                    result = cursor.fetchone()
                    if result:
                        self.push_screen(DetailModal(ref_table, result))
                    else:
                        self.notify("Referenced record not found.", severity="warning")
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

    # --- BUTTON HANDLERS ---
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        
        if bid == "btn_quit":
            self.exit()
        
        elif bid == "btn_refresh":
            if self.current_table:
                self.load_table_data(self.current_table)
                
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
            # Open Add Form
            self.push_screen(RecordForm(self.current_table, mode="add"), self.handle_add_submit)
            
        elif bid == "btn_update":
            if not self.current_table or not self.current_row_data:
                self.notify("Select a row to update!", severity="warning")
                return
            # Open Update Form
            self.push_screen(RecordForm(self.current_table, self.current_row_data, mode="update"), self.handle_update_submit)
            
        elif bid == "btn_delete":
            if not self.current_table or not self.current_row_data:
                self.notify("Select a row to delete!", severity="warning")
                return
            # Open Confirmation
            self.push_screen(ConfirmationModal("Delete this record?"), self.handle_delete_confirm)

        elif bid == "btn_do_search":
            term = self.query_one("#search_input").value
            if term and self.conn:
                res = db_utils.search_global(self.conn, term)
                self.populate_search_table(res)
        
        elif bid.startswith("rep_"):
            if self.conn: self.run_report(bid)

    # --- CRUD CALLBACKS ---
    def handle_add_submit(self, data):
        """Callback from Add Form."""
        if not data: return
        
        # Generate ID if auto_pk logic applies
        config = TABLE_CONFIG.get(self.current_table, {})
        pk = config.get('pk')
        prefix = config.get('prefix')
        
        if pk and prefix and pk not in data:
            new_id = db_utils.get_next_id(self.conn, self.current_table, pk, prefix)
            data[pk] = new_id
            self.notify(f"Generated ID: {new_id}")

        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)
        sql = f"INSERT INTO {self.current_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, list(data.values()))
            self.notify("Record Added!", severity="success")
            self.load_table_data(self.current_table) # Refresh
        except Exception as e:
            self.notify(f"Error adding record: {e}", severity="error")

    def handle_update_submit(self, data):
        """Callback from Update Form."""
        if not data: return
        
        config = TABLE_CONFIG.get(self.current_table, {})
        
        # Identify PKs to build WHERE clause
        pk_dict = {}
        if config.get('pk'):
            pk_val = data.get(config['pk'])
            pk_dict[config['pk']] = pk_val
        elif config.get('pks'):
            for k in config['pks']:
                pk_dict[k] = data.get(k)
        
        if not pk_dict:
            self.notify("Cannot update: No PK found.", severity="error")
            return
        
        # Everything else is updates
        updates = {k: v for k, v in data.items() if k not in pk_dict}
        
        if db_utils.update_record(self.conn, self.current_table, pk_dict, updates):
            self.notify("Record Updated!", severity="success")
            self.load_table_data(self.current_table)
        else:
            self.notify("Update failed.", severity="error")

    def handle_delete_confirm(self, confirmed):
        if not confirmed: return
        
        config = TABLE_CONFIG.get(self.current_table, {})
        pk_dict = {}
        
        # Reconstruct PK dict from current_row_data
        if config.get('pk'):
            pk_key = config['pk']
            pk_dict[pk_key] = self.current_row_data.get(pk_key)
        elif config.get('pks'):
            for k in config['pks']:
                pk_dict[k] = self.current_row_data.get(k)
                
        if db_utils.delete_record(self.conn, self.current_table, pk_dict):
            self.notify("Record Deleted!", severity="success")
            self.load_table_data(self.current_table)
        else:
            self.notify("Delete failed.", severity="error")

    # --- SEARCH & REPORTS HELPER ---
    def populate_search_table(self, results):
        table = self.query_one("#search_results_table", DataTable)
        table.clear(columns=True)
        if not results:
            self.notify("No matches.")
            return
        table.add_columns("Table", "Row Data")
        for t_name, rows in results.items():
            for row in rows:
                table.add_row(t_name, str(row))

    def run_report(self, rep_id):
        data = []
        if rep_id == "rep_1": data = db_utils.get_manages_report(self.conn)
        elif rep_id == "rep_2": data = db_utils.get_assigned_to_gym_report(self.conn)
        elif rep_id == "rep_3": data = db_utils.get_pokemon_abilities_report(self.conn)
        
        table = self.query_one("#report_table", DataTable)
        table.clear(columns=True)
        if data:
            headers = list(data[0].keys())
            table.add_columns(*headers)
            for row in data:
                table.add_row(*[str(v) for v in row.values()])
        else:
            self.notify("No data.")

if __name__ == "__main__":
    app = PokemonTUI()
    app.run()