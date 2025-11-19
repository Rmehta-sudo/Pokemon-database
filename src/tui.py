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
# CONFIGURATION (ALL TABLES)
# =============================================================================

TABLE_CONFIG = {
    # --- LEVEL 0 (Independent) ---
    "Region": {
        "pk": "region_id", "prefix": "R",
        "columns": [
            {"col": "region_name", "type": "str"},
            {"col": "main_city", "type": "str"}
        ]
    },
    "Type": {
        "pk": "type_id", "prefix": "Y",
        "columns": [{"col": "type_name", "type": "str"}]
    },
    "Ability": {
        "pk": "ability_id", "prefix": "A",
        "columns": [{"col": "ability_name", "type": "str"}, {"col": "effect_description", "type": "str"}]
    },

    # --- LEVEL 1 ---
    "City": {
        "pk": "city_id", "prefix": "C",
        "columns": [
            {"col": "city_name", "type": "str"},
            {"col": "region_id", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"}
        ]
    },
    "Move": {
        "pk": "move_id", "prefix": "M",
        "columns": [
            {"col": "move_name", "type": "str"},
            {"col": "power", "type": "int"},
            {"col": "accuracy", "type": "int"},
            {"col": "pp", "type": "int"},
            {"col": "type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "category", "type": "enum", "choices": ["Physical", "Special", "Status"]}
        ]
    },
    "TypeStrength": {
        "pks": ["type_id", "strength"],
        "columns": [
            {"col": "type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "strength", "type": "str"}
        ]
    },
    "TypeWeakness": {
        "pks": ["type_id", "weakness"],
        "columns": [
            {"col": "type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
            {"col": "weakness", "type": "str"}
        ]
    },
    "PokemonSpecies": {
        "pk": "species_id", "prefix": "S",
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
    "Trainer": {
        "pk": "trainer_id", "prefix": "T",
        "columns": [
            {"col": "name", "type": "str"},
            {"col": "gender", "type": "enum", "choices": ["Male", "Female", "Other"]},
            {"col": "birth_date", "type": "date"},
            {"col": "contact_info_email", "type": "str"},
            {"col": "contact_info_phone", "type": "str"},
            {"col": "region_id", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"}
        ]
    },
    "LeagueSeason": {
        "pk": "season_id", "prefix": "L",
        "columns": [
            {"col": "year", "type": "int"},
            {"col": "region_id", "type": "fk", "ref_table": "Region", "ref_pk": "region_id"},
            {"col": "theme", "type": "str"},
        ]
    },

    # --- LEVEL 2 ---
    "PokemonSpeciesAbility": {
        "pks": ["species_id", "ability_id"],
        "columns": [
            {"col": "species_id", "type": "fk", "ref_table": "PokemonSpecies", "ref_pk": "species_id"},
            {"col": "ability_id", "type": "fk", "ref_table": "Ability", "ref_pk": "ability_id"}
        ]
    },
    "Gym": {
        "pk": "gym_id", "prefix": "G",
        "columns": [
            {"col": "gym_name", "type": "str"},
            {"col": "city_id", "type": "fk", "ref_table": "City", "ref_pk": "city_id"},
            {"col": "specialization_type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"},
        ]
    },
    "GymLeader": {
         "pk": "leader_id", 
         "columns": [
             {"col": "leader_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
             {"col": "specialty_type_id", "type": "fk", "ref_table": "Type", "ref_pk": "type_id"}, 
             {"col": "years_of_experience", "type": "int"}
         ]
    },
    "Champion": {
        "pk": "champion_id",
        "columns": [
            {"col": "champion_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "title_year", "type": "int"}
        ]
    },
    "RegisteredPokemon": {
        "pk": "pokemon_id", "prefix": "P",
        "columns": [
            {"col": "species_id", "type": "fk", "ref_table": "PokemonSpecies", "ref_pk": "species_id"},
            {"col": "trainer_id", "type": "fk", "ref_table": "Trainer", "ref_pk": "trainer_id"},
            {"col": "nickname", "type": "str"},
            {"col": "level", "type": "int"},
            {"col": "experience_points", "type": "int"},
            {"col": "registration_date", "type": "date"},
        ]
    },
    "Tournament": {
        "pk": "tournament_id", "prefix": "O",
        "columns": [
            {"col": "tournament_name", "type": "str"},
            {"col": "start_date", "type": "date"},
            {"col": "end_date", "type": "date"},
            {"col": "city_id", "type": "fk", "ref_table": "City", "ref_pk": "city_id"},
            {"col": "season_id", "type": "fk", "ref_table": "LeagueSeason", "ref_pk": "season_id"},
        ]
    },

    # --- LEVEL 3 ---
    "RegisteredPokemonMove": {
        "pks": ["pokemon_id", "move_id"],
        "columns": [
            {"col": "pokemon_id", "type": "fk", "ref_table": "RegisteredPokemon", "ref_pk": "pokemon_id"},
            {"col": "move_id", "type": "fk", "ref_table": "Move", "ref_pk": "move_id"}
        ]
    },
    "GymSeasonRegistry": {
        "pk": "registry_id", "prefix": "E",
        "columns": [
            {"col": "season_id", "type": "fk", "ref_table": "LeagueSeason", "ref_pk": "season_id"},
            {"col": "gym_id", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "leader_id", "type": "fk", "ref_table": "GymLeader", "ref_pk": "leader_id"},
        ]
    },
    "GymBattle": {
        "pk": "battle_id", "prefix": "B",
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
    "GymBadgeName": {
        "pk": "gym_id",
        "columns": [
            {"col": "gym_id", "type": "fk", "ref_table": "Gym", "ref_pk": "gym_id"},
            {"col": "badge_name", "type": "str"}
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
}

LOGO_ASCII = r"""
   ___      _                               
  / _ \___ | | _____ _ __ ___   ___  _ __   
 / /_)/ _ \| |/ / _ \ '_ ` _ \ / _ \| '_ \  
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

    def __init__(self, table_name, record_data=None, mode="add"):
        super().__init__()
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
                    
                    # Populate with old data
                    value = str(self.record_data.get(col_name, ""))
                    if value == "None": value = ""
                    
                    # DISABLE INPUT if it is a PK and we are in UPDATE mode
                    is_pk = (self.mode == "update" and col_name in pk_set)
                    
                    inp = Input(value=value, id=f"inp_{col_name}", disabled=is_pk)
                    
                    if is_pk:
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
    .search_row { height: auto; margin-bottom: 1; margin-top: 1; }
    #search_input, #filter_input { width: 80%; }
    #btn_do_search, #btn_filter { width: 20%; }
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

    def on_mount(self) -> None:
        self.title = "Pokemon League DB Manager"
        # Set Default Theme to Tokyo Night
        self.theme = "tokyo-night"
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
                # Increased width for sidebar to fit ASCII art
                with Container(id="sidebar"):
                    yield Static(LOGO_ASCII, id="logo")
                    yield Label("Tables:", classes="box_label")
                    
                    list_items = []
                    for t_name in TABLE_CONFIG.keys():
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
                    with TabbedContent(initial="tab_data"):
                        with TabPane("Data Browser", id="tab_data"):
                            yield Label("Select a table from the sidebar...", id="table_label")
                            yield DataTable(id="main_table", cursor_type="row")

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
                            yield Label("Available Reports:")
                            with Horizontal():
                                yield Button("Region Management", id="rep_1", classes="report_box")
                                yield Button("Assignments", id="rep_2", classes="report_box")
                                yield Button("Abilities", id="rep_3", classes="report_box")
                            yield DataTable(id="report_table")
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
                # Compare string values to be safe (handling IDs correctly)
                if str(row.get(pk_col)) == str(pk_val):
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
        if event.item and event.item.name:
            self.current_table = event.item.name
            self.query_one("#table_label").update(f"Browsing: [bold yellow]{self.current_table}[/]")
            self.load_table_data(self.current_table)

    def load_table_data(self, table_name, data=None, limit=100):
        if not self.conn: return
        table = self.query_one("#main_table", DataTable)
        table.clear(columns=True)
        
        if data is None:
            data = db_utils.view_table(self.conn, table_name, limit=limit)
        
        if not data:
            self.notify("No records found.")
            return

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
        table.misc_col_map = headers 

        for row in data:
            table.add_row(*[str(row.get(h, "")) for h in headers])
        
        self.current_table_data = data 
        
        # Clear filter input on fresh load/refresh
        self.query_one("#filter_input").value = ""

    # --- SELECTION & DRILL DOWN ---
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Capture the selected row for CRUD operations."""
        if event.data_table.id != "main_table": return
        if not self.current_table or not hasattr(self, 'current_table_data'): return
        
        row_index = event.cursor_row
        if row_index < len(self.current_table_data):
            self.current_row_data = self.current_table_data[row_index]
            
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle foreign key jump."""
        if event.data_table.id != "main_table": return
        if not self.current_table: return
        
        # Update selection tracking
        self.on_data_table_row_selected(DataTable.RowSelected(event.data_table, event.coordinate.row))

        col_index = event.coordinate.column
        raw_headers = getattr(event.data_table, "misc_col_map", [])
        if col_index >= len(raw_headers): return
        
        col_name = raw_headers[col_index]
        config = TABLE_CONFIG.get(self.current_table, {})
        col_def = next((c for c in config.get('columns', []) if c['col'] == col_name), None)

        if col_def and col_def['type'] == 'fk':
            ref_table = col_def['ref_table']
            val = event.value
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
            self.push_screen(RecordForm(self.current_table, mode="add"), self.handle_add_submit)
            
        elif bid == "btn_update":
            if not self.current_table:
                self.notify("Select a table first.", severity="warning")
                return
            
            table = self.query_one("#main_table", DataTable)
            row_index = table.cursor_row
            
            if row_index < 0 or row_index >= len(self.current_table_data):
                self.notify("Select a row to update!", severity="warning")
                return
            
            row_data = self.current_table_data[row_index]
            self.push_screen(RecordForm(self.current_table, row_data, mode="update"), self.handle_update_submit)
            
        elif bid == "btn_delete":
            if not self.current_table: return

            table = self.query_one("#main_table", DataTable)
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
        
        elif bid.startswith("rep_"):
            if self.conn: self.run_report(bid)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "filter_input":
            self.on_button_pressed(Button(id="btn_filter"))
        elif event.input.id == "search_input":
            self.on_button_pressed(Button(id="btn_do_search"))

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

        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)
        sql = f"INSERT INTO {self.current_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
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