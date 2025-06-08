import streamlit as st
import os
import json
import pandas as pd
import math
from typing import List, Dict, Any
from .state import State, parse_state_file
from .game import Game, GameError
from .laws import ModifierChange, LawChange, LawManager
from .config import (
    MAJOR_COUNTRIES, BUILDING_TYPES, BUILDING_COSTS, STATE_CATEGORIES,
    DEFAULT_MAX_BUILDINGS, TRADE_LAWS, MOBILIZATION_LAWS, ECONOMIC_LAWS,
    DEFAULT_SETTINGS, CIVILIAN_FACTORY_OUTPUT, MAX_FACTORIES_PER_PROJECT
)


def apply_css():
    st.markdown("""
        <style>
            .stNumberInput input { width: 80px !important; max-width: 100px !important; }
            .stTextInput input { width: 150px !important; max-width: 200px !important; }
            .stSelectbox { width: 200px !important; max-width: 250px !important; }
            .building-row { 
                display: flex; 
                align-items: center; 
                gap: 10px; 
                margin-bottom: 10px; 
                padding: 10px; 
                border: 1px solid #444; 
                border-radius: 5px; 
                background-color: #2a2a2a; 
            }
            .construction-container { 
                padding: 15px; 
                border: 2px solid #666; 
                border-radius: 8px; 
                background-color: #1e1e1e; 
            }
            .queue-item { 
                padding: 8px; 
                margin: 5px 0; 
                border-left: 4px solid #4CAF50; 
                background-color: #333; 
                border-radius: 4px; 
            }
            .stButton > button { 
                background-color: #4CAF50; 
                color: white; 
                border-radius: 5px; 
                padding: 5px 10px; 
            }
            .stButton > button:hover { 
                background-color: #45a049; 
            }
            .state-info { 
                font-size: 0.9em; 
                color: #ccc; 
                margin-bottom: 10px; 
            }
            .tooltip {
                position: relative;
                display: inline-block;
            }
            .tooltip .tooltiptext {
                visibility: hidden;
                width: 200px;
                background-color: #555;
                color: #fff;
                text-align: left;
                border-radius: 6px;
                padding: 5px;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                margin-left: -100px;
                opacity: 0;
                transition: opacity 0.3s;
            }
            .tooltip:hover .tooltiptext {
                visibility: visible;
                opacity: 1;
            }
        </style>
    """, unsafe_allow_html=True)

def state_to_dict(state: State) -> Dict[str, Any]:
    """Convert a State object to a dictionary."""
    return {
        "id": state.id,
        "name": state.name,
        "category": state.category,
        "total_slots": state.total_slots,
        "infrastructure": state.infrastructure,
        "buildings": state.buildings.copy(),
        "owner": state.owner,
        "state_bonus": state.state_bonus,
        "max_buildings": state.max_buildings.copy(),
        "provinces": state.provinces.copy(),
        "history": state.history.copy(),
        "manpower": state.manpower,
        "province_buildings": state.province_buildings.copy(),
        "has_dam": state.has_dam
    }

def initialize_session_state():
    if "settings" not in st.session_state:
        st.session_state.settings = DEFAULT_SETTINGS.copy()
    if "game" not in st.session_state:
        try:
            raw_states = st.session_state.settings["states"]
            # Convert any State objects to dictionaries
            dict_states = [
                state_to_dict(s) if isinstance(s, State) else s
                for s in raw_states
            ]
            # Validate each state dictionary
            states = []
            required_keys = {"id", "name", "category", "total_slots", "infrastructure", "buildings"}
            for s in dict_states:
                if not isinstance(s, dict):
                    st.error(f"Invalid state data: {s} is not a dictionary")
                    continue
                missing_keys = required_keys - set(s.keys())
                if missing_keys:
                    st.error(f"State {s.get('id', 'unknown')} is missing required keys: {missing_keys}")
                    continue
                s.setdefault("owner", "")
                s.setdefault("state_bonus", 0.0)
                s.setdefault("max_buildings", DEFAULT_MAX_BUILDINGS.copy())
                s.setdefault("provinces", [])
                s.setdefault("history", {"victory_points": [], "cores": []})
                s.setdefault("manpower", 0)
                s.setdefault("province_buildings", {})
                s.setdefault("has_dam", False)
                states.append(s)
            # Initialize Game with dictionary states
            valid_game_params = [
                "industry_level",
                "construction_level",
                "industry_days",
                "construction_days",
                "trade_law",
                "mobilization_law",
                "economic_law",
                "rubber_factory_max",
                "consumer_goods_percent",
                "stability",
                "war_support"
            ]
            game_settings = {
                k: v for k, v in st.session_state.settings.items()
                if k in valid_game_params
            }
            st.session_state.game = Game(states=states, **game_settings)
            st.session_state.settings["states"] = states
            st.success("Game initialized successfully!")
        except Exception as e:
            st.error(f"Failed to initialize game: {str(e)}")
            # Initialize with a default state to prevent empty state list
            st.session_state.settings["states"] = [{
                "id": 1,
                "name": "Placeholder State",
                "category": "rural",
                "total_slots": STATE_CATEGORIES["rural"].slots,
                "infrastructure": 0,
                "buildings": {bt: 0 for bt in BUILDING_TYPES},
                "state_bonus": 0.0,
                "max_buildings": DEFAULT_MAX_BUILDINGS.copy(),
                "provinces": [],
                "history": {"victory_points": [], "cores": []},
                "manpower": 0,
                "province_buildings": {},
                "has_dam": False
            }]
            game_settings = {
                k: v for k, v in st.session_state.settings.items()
                if k in valid_game_params
            }
            try:
                st.session_state.game = Game(states=st.session_state.settings["states"], **game_settings)
                st.success("Initialized game with placeholder state.")
            except Exception as e:
                st.error(f"Failed to initialize with placeholder state: {str(e)}")

def sanitize_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    settings = settings.copy()
    for state in settings["states"]:
        state["state_bonus"] = min(max(0.0, float(state.get("state_bonus", 0.0))), 0.5)
        state["name"] = state.get("name", f"State {state['id']}")[:50]
        state["total_slots"] = max(0, int(state.get("total_slots", STATE_CATEGORIES.get(state.get("category", "rural")).slots)))
        state["category"] = state.get("category", "rural") if state.get("category") in STATE_CATEGORIES else "rural"
        state["infrastructure"] = min(max(0, int(state.get("infrastructure", 0))), DEFAULT_MAX_BUILDINGS["infrastructure"])
        state["buildings"] = {
            bt: min(max(0, int(v)), DEFAULT_MAX_BUILDINGS[bt])
            for bt, v in state.get("buildings", {}).items()
        }
        state["max_buildings"] = state.get("max_buildings", DEFAULT_MAX_BUILDINGS.copy())
        state["province_buildings"] = state.get("province_buildings", {})
        state["has_dam"] = bool(state.get("has_dam", False))
        state.pop("owner", None)
    settings["consumer_goods_percent"] = max(0.0, float(settings.get("consumer_goods_percent", 0.35)))
    settings["cgff"] = max(0.0, float(settings.get("cgff", 0.0)))
    settings["industry_level"] = min(max(0, int(settings.get("industry_level", 0))), 5)
    settings["industry_days"] = [max(0, int(d)) for d in settings.get("industry_days", [0] * 5)]
    settings["construction_level"] = min(max(0, int(settings.get("construction_level", 0))), 5)
    settings["construction_days"] = [max(0, int(d)) for d in settings.get("construction_days", [0] * 5)]
    settings["trade_law"] = settings.get("trade_law", "free_trade") if settings.get("trade_law") in TRADE_LAWS else "free_trade"
    settings["mobilization_law"] = settings.get("mobilization_law", "volunteer_only") if settings.get("mobilization_law") in MOBILIZATION_LAWS else "volunteer_only"
    settings["economic_law"] = settings.get("economic_law", "civilian_economy") if settings.get("economic_law") in ECONOMIC_LAWS else "civilian_economy"
    settings["rubber_factory_max"] = max(1, int(settings.get("rubber_factory_max", 3)))
    return settings

def render_state_settings():
    st.subheader("State Settings")
    if not hasattr(st.session_state, "game") or not st.session_state.game:
        st.warning("No game state loaded. Please load states first.")
        return
    state_data = [
        {
            "ID": state.id,
            "Name": state.name,
            "Category": state.category,
            "Total Slots": state.total_slots,
            "Used Slots": state.used_slots,
            "Infrastructure": state.infrastructure,
            "State Bonus (%)": state.state_bonus * 100,
            "Has Dam": state.has_dam
        }
        for state in st.session_state.game.states.values()
    ]
    edited_df = st.data_editor(
        pd.DataFrame(state_data),
        column_config={
            "Name": st.column_config.TextColumn("Name", max_chars=50),
            "Category": st.column_config.SelectboxColumn("Category", options=list(STATE_CATEGORIES.keys())),
            "Total Slots": st.column_config.NumberColumn("Total Slots", min_value=0, max_value=50, step=1),
            "Infrastructure": st.column_config.NumberColumn("Infrastructure", min_value=0, max_value=5, step=1),
            "State Bonus (%)": st.column_config.NumberColumn("State Bonus (%)", min_value=0.0, max_value=100.0, step=0.1),
            "Has Dam": st.column_config.CheckboxColumn("Has Dam")
        },
        num_rows="dynamic"
    )
    if st.button("Update States"):
        try:
            for _, row in edited_df.iterrows():
                state = st.session_state.game.states[row["ID"]]
                state.name = row["Name"]
                state.category = row["Category"]
                state.total_slots = STATE_CATEGORIES[row["Category"]].slots
                if row["Has Dam"]:
                    state.total_slots = int(state.total_slots * 1.15)
                state.infrastructure = row["Infrastructure"]
                state.state_bonus = row["State Bonus (%)"] / 100
                state.has_dam = row["Has Dam"]
                for s in st.session_state.settings["states"]:
                    if s["id"] == state.id:
                        s.update({
                            "name": state.name,
                            "category": state.category,
                            "total_slots": state.total_slots,
                            "infrastructure": state.infrastructure,
                            "state_bonus": state.state_bonus,
                            "has_dam": state.has_dam,
                            "buildings": state.buildings
                        })
            st.success("States updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error updating states: {e}")

def render_save_load_settings():
    st.subheader("Save/Load Settings")
    if st.button("Save Settings"):
        try:
            settings = sanitize_settings(st.session_state.settings)
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
            st.success("Settings saved successfully!")
        except Exception as e:
            st.error(f"Error saving settings: {e}")
    uploaded_settings = st.file_uploader("Load Settings File", type="json")
    if uploaded_settings and st.button("Load Settings"):
        try:
            settings = json.load(uploaded_settings)
            settings = sanitize_settings(settings)
            st.session_state.settings = settings
            valid_game_params = [
                "industry_level",
                "construction_level",
                "industry_days",
                "construction_days",
                "trade_law",
                "mobilization_law",
                "economic_law",
                "rubber_factory_max",
                "consumer_goods_percent"
            ]
            game_settings = {
                k: v for k, v in settings.items()
                if k in valid_game_params
            }
            st.session_state.game = Game(states=settings["states"], **game_settings)
            st.session_state.settings["states"] = settings["states"]
            st.success("Settings loaded successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading settings: {e}")

def render_state_loader():
    st.subheader("Load State from HOI4 Game File")
    country_choice = st.selectbox("Select Country", options=["Manual Entry"] + list(MAJOR_COUNTRIES.keys()), index=0)
    country_tag = st.text_input("Enter Country Tag (e.g., GER)", value="") if country_choice == "Manual Entry" else MAJOR_COUNTRIES.get(country_choice, "")
    
    load_option = st.radio("Load Option", ["Upload Single File", "Scan States Folder"])
    
    clear_previous_states = st.checkbox("Clear Previous States on Scan", value=False, help="If checked, all previous states will be removed when scanning the states folder, keeping at least one state.")
    
    def update_game_states(new_states: List[Dict]):
        existing_ids = {s["id"] for s in st.session_state.settings["states"]}
        for state in new_states:
            if state["id"] not in existing_ids:
                st.session_state.settings["states"].append(state)
            else:
                for existing_state in st.session_state.settings["states"]:
                    if existing_state["id"] == state["id"]:
                        existing_state.update(state)
        valid_game_params = [
            "industry_level",
            "construction_level",
            "industry_days",
            "construction_days",
            "trade_law",
            "mobilization_law",
            "economic_law",
            "rubber_factory_max",
            "consumer_goods_percent"
        ]
        game_settings = {
            k: v for k, v in st.session_state.settings.items()
            if k in valid_game_params
        }
        st.session_state.game = Game(states=st.session_state.settings["states"], **game_settings)
        return len(new_states)

    if load_option == "Upload Single File":
        uploaded_file = st.file_uploader("Upload HOI4 state file (*.txt)", type="txt")
        if uploaded_file and st.button("Load State Data"):
            try:
                new_states = parse_state_file(uploaded_file.read(), country_tag if country_tag else None)
                if not new_states:
                    st.warning("No states loaded. Check country tag or file content.")
                else:
                    num_loaded = update_game_states(new_states)
                    st.success(f"Loaded {num_loaded} state(s) successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error loading state file: {e}")
    
    else:
        states_folder = st.text_input("Path to history/states/ folder", value=r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\history\states")
        if st.button("Scan and Load States"):
            if not os.path.isdir(states_folder):
                st.error("Invalid folder path!")
            else:
                try:
                    new_states = []
                    if not os.listdir(states_folder):
                        st.warning("No files found in the specified folder.")
                    else:
                        for filename in os.listdir(states_folder):
                            if filename.endswith(".txt"):
                                with open(os.path.join(states_folder, filename), "rb") as f:
                                    parsed_states = parse_state_file(f.read(), country_tag if country_tag else None)
                                    if parsed_states:
                                        new_states.extend(parsed_states)
                    if new_states:
                        if clear_previous_states:
                            removed_count = len(st.session_state.settings["states"])
                            st.session_state.settings["states"] = []
                            st.info(f"Cleared {removed_count} previous state(s).")
                        num_loaded = update_game_states(new_states)
                        if not st.session_state.settings["states"]:
                            st.session_state.settings["states"].append({
                                "id": 1,
                                "name": "Placeholder State",
                                "category": "rural",
                                "total_slots": STATE_CATEGORIES["rural"].slots,
                                "infrastructure": 0,
                                "buildings": {bt: 0 for bt in BUILDING_TYPES},
                                "state_bonus": 0.0,
                                "max_buildings": DEFAULT_MAX_BUILDINGS.copy(),
                                "provinces": [],
                                "history": {"victory_points": [], "cores": []},
                                "manpower": 0,
                                "province_buildings": {},
                                "has_dam": False
                            })
                            st.info("Added placeholder state to prevent empty state list.")
                        st.success(f"Loaded {num_loaded} state(s) from {states_folder}!")
                        st.rerun()
                    else:
                        st.warning("No valid states loaded from folder.")
                except Exception as e:
                    st.error(f"Error loading state files: {e}")
                    if not st.session_state.settings["states"]:
                        st.session_state.settings["states"].append({
                            "id": 1,
                            "name": "Placeholder State",
                            "category": "rural",
                            "total_slots": STATE_CATEGORIES["rural"].slots,
                            "infrastructure": 0,
                            "buildings": {bt: 0 for bt in BUILDING_TYPES},
                            "state_bonus": 0.0,
                            "max_buildings": DEFAULT_MAX_BUILDINGS.copy(),
                            "provinces": [],
                            "history": {"victory_points": [], "cores": []},
                            "manpower": 0,
                            "province_buildings": {},
                            "has_dam": False
                        })
                        st.info("Added placeholder state due to loading failure.")

from .config import TRADE_LAWS, ECONOMIC_LAWS, MOBILIZATION_LAWS

def render_law_settings():
    st.subheader("Law Settings")
    if not hasattr(st.session_state, "game") or not st.session_state.game:
        st.warning("No game state loaded. Please load states first.")
        return

    st.write("**Trade Law**")
    trade_law_options = list(TRADE_LAWS.keys())
    current_trade_law = st.session_state.settings["trade_law"]
    # Ensure current_trade_law is valid; default to first option if invalid
    if current_trade_law not in trade_law_options:
        current_trade_law = trade_law_options[0]
        st.session_state.settings["trade_law"] = current_trade_law
    trade_law_index = trade_law_options.index(current_trade_law)
    trade_law = st.selectbox(
        "Select Trade Law",
        options=trade_law_options,
        index=trade_law_index,
        format_func=lambda x: x.replace('_', ' ').title(),
        key="trade_law_select"
    )
    if trade_law != st.session_state.settings["trade_law"]:
        st.session_state.game.law_manager.apply_law_change(
            st.session_state.game.current_day, "trade", trade_law
        )
        st.session_state.settings["trade_law"] = trade_law
        st.session_state.game.trade_law = trade_law
        st.success(f"Trade law updated to {trade_law.replace('_', ' ').title()}")

    st.write("**Economic Law**")
    economic_law_options = list(ECONOMIC_LAWS.keys())
    current_economic_law = st.session_state.settings["economic_law"]
    if current_economic_law not in economic_law_options:
        current_economic_law = economic_law_options[0]
        st.session_state.settings["economic_law"] = current_economic_law
    economic_law_index = economic_law_options.index(current_economic_law)
    economic_law = st.selectbox(
        "Select Economic Law",
        options=economic_law_options,
        index=economic_law_index,
        format_func=lambda x: x.replace('_', ' ').title(),
        key="economic_law_select"
    )
    if economic_law != st.session_state.settings["economic_law"]:
        st.session_state.game.law_manager.apply_law_change(
            st.session_state.game.current_day, "economic", economic_law
        )
        st.session_state.settings["economic_law"] = economic_law
        st.session_state.game.economic_law = economic_law
        st.success(f"Economic law updated to {economic_law.replace('_', ' ').title()}")

    st.write("**Mobilization Law**")
    mobilization_law_options = MOBILIZATION_LAWS
    current_mobilization_law = st.session_state.settings["mobilization_law"]
    if current_mobilization_law not in mobilization_law_options:
        current_mobilization_law = mobilization_law_options[0]
        st.session_state.settings["mobilization_law"] = current_mobilization_law
    mobilization_law_index = mobilization_law_options.index(current_mobilization_law)
    mobilization_law = st.selectbox(
        "Select Mobilization Law",
        options=mobilization_law_options,
        index=mobilization_law_index,
        format_func=lambda x: x.replace('_', ' ').title(),
        key="mobilization_law_select"
    )
    if mobilization_law != st.session_state.settings["mobilization_law"]:
        st.session_state.game.law_manager.apply_law_change(
            st.session_state.game.current_day, "mobilization", mobilization_law
        )
        st.session_state.settings["mobilization_law"] = mobilization_law
        st.session_state.game.mobilization_law = mobilization_law
        st.success(f"Mobilization law updated to {mobilization_law.replace('_', ' ').title()}")

def render_tech_settings():
    st.subheader("Industry and Construction Technologies")
    if not hasattr(st.session_state, "game") or not st.session_state.game:
        st.warning("No game state loaded. Please load states first.")
        return
    col1, col2 = st.columns(2)
    with col1:
        industry_level = st.selectbox("Current Industry Tech Level", options=[0, 1, 2, 3, 4, 5], index=st.session_state.settings["industry_level"])
        st.write("Unlock Days for Future Industry Tech Levels:")
        industry_days = [st.number_input(f"Level {i+1} Unlock Day", min_value=0, max_value=10000, value=st.session_state.settings["industry_days"][i], step=1, key=f"industry_day_{i}") for i in range(5)]
    with col2:
        construction_level = st.selectbox("Current Construction Tech Level", options=[0, 1, 2, 3, 4, 5], index=st.session_state.settings["construction_level"])
        st.write("Unlock Days for Future Construction Tech Levels:")
        construction_days = [st.number_input(f"Level {i+1} Unlock Day", min_value=0, max_value=10000, value=st.session_state.settings["construction_days"][i], step=1, key=f"construction_day_{i}") for i in range(5)]
    rubber_factory_max = st.number_input("Max Rubber Factories per State", min_value=1, max_value=DEFAULT_MAX_BUILDINGS["synthetic_refinery"], value=st.session_state.settings["rubber_factory_max"], step=1)
    if st.button("Update Technologies"):
        try:
            st.session_state.settings.update({
                "industry_level": industry_level,
                "industry_days": industry_days,
                "construction_level": construction_level,
                "construction_days": construction_days,
                "rubber_factory_max": rubber_factory_max
            })
            st.session_state.game.industry_level = industry_level
            st.session_state.game.industry_days = industry_days
            st.session_state.game.construction_level = construction_level
            st.session_state.game.construction_days = construction_days
            st.session_state.game.rubber_factory_max = rubber_factory_max
            for state in st.session_state.game.states.values():
                state.max_buildings["synthetic_refinery"] = rubber_factory_max
            st.session_state.game.law_manager.update_modifiers(construction_level)
            st.success("Technologies updated successfully!")
        except Exception as e:
            st.error(f"Error updating technologies: {e}")

def render_construction_projects():
    st.subheader("Construction Projects")
    if not hasattr(st.session_state, "game") or not st.session_state.game:
        st.warning("No game state loaded. Please load states first.")
        return
    game = st.session_state.game
    state_options = [(s.id, s.name) for s in game.states.values()]
    if not state_options:
        st.warning("No states available for construction.")
        return

    # Initialize session state for Ctrl key detection
    if "ctrl_pressed" not in st.session_state:
        st.session_state.ctrl_pressed = False

    # JavaScript to detect Ctrl key
    st.markdown("""
        <script>
        document.addEventListener('keydown', function(event) {
            if (event.ctrlKey) {
                window.Streamlit.setComponentValue('ctrl_pressed', true);
            }
        });
        document.addEventListener('keyup', function(event) {
            window.Streamlit.setComponentValue('ctrl_pressed', false);
        });
        </script>
    """, unsafe_allow_html=True)

    state_id = st.selectbox(
        "Select State for Construction",
        options=[s[0] for s in state_options],
        format_func=lambda x: next(s[1] for s in state_options if s[0] == x),
        key="construction_state_select"
    )
    selected_state = game.states.get(state_id)
    
    if selected_state:
        speed_modifier = game.get_construction_speed_modifier(state_id, "generic")
        modifier_breakdown = (
            f"Infrastructure: +{selected_state.infrastructure * 20}%<br>"
            f"Dam: {'+15%' if selected_state.has_dam else '0%'}<br>"
            f"Trade Law: +{TRADE_LAWS[game.trade_law]['construction_speed']*100:.0f}%<br>"
            f"Economic Law: +{ECONOMIC_LAWS[game.economic_law]['civilian_factory_speed']*100:.0f}% (civilian), "
            f"+{ECONOMIC_LAWS[game.economic_law]['military_factory_speed']*100:.0f}% (military)<br>"
            f"Construction Tech: +{game.construction_level * 10}%"
        )
        st.markdown(f"""
            <div class='state-info tooltip'>
                <strong>{selected_state.name} (ID {selected_state.id})</strong><br>
                Category: {STATE_CATEGORIES[selected_state.category].name}<br>
                Total Slots: {selected_state.total_slots} | Used Slots: {selected_state.used_slots}<br>
                Has Dam: {'Yes' if selected_state.has_dam else 'No'}<br>
                Infrastructure: {selected_state.infrastructure}/{DEFAULT_MAX_BUILDINGS['infrastructure']}<br>
                Construction Speed Modifier: {speed_modifier:.2f}x
                <span class='tooltiptext'>{modifier_breakdown}</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='construction-container'>", unsafe_allow_html=True)
    st.write("**Add Buildings to Queue**")
    cols = st.columns(3)
    for i, bt in enumerate(BUILDING_TYPES):
        with cols[i % 3]:
            current_count = selected_state.infrastructure if bt == "infrastructure" else selected_state.buildings.get(bt, 0) if selected_state else 0
            max_count = selected_state.max_buildings.get(bt, DEFAULT_MAX_BUILDINGS[bt]) if selected_state else DEFAULT_MAX_BUILDINGS[bt]
            cost = BUILDING_COSTS.get(bt, 0)
            is_slot_occupying = bt in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"]
            available_slots = (selected_state.total_slots - selected_state.used_slots) if is_slot_occupying else max_count - current_count
            type_modifier = game.get_construction_speed_modifier(state_id, bt) if selected_state else 0.0
            st.markdown(f"""
                <div class='building-row tooltip'>
                    <div style='{{flex: 2}}'>{bt.replace('_', ' ').title()}</div>
                    <div style='{{flex: 1}}'>Current: {current_count}/{max_count}</div>
                    <div style='{{flex: 1}}'>Cost: {cost}</div>
                    <span class='tooltiptext'>Modifier: {type_modifier:.2f}x</span>
                </div>
            """, unsafe_allow_html=True)
            if available_slots <= 0:
                st.write("No slots available")
                st.button(f"+1 {bt.replace('_', ' ').title()}", key=f"add_{state_id}_{bt}", disabled=True)
            else:
                if st.button(f"+1 {bt.replace('_', ' ').title()}", key=f"add_{state_id}_{bt}"):
                    quantity = min(available_slots, max_count - current_count) if st.session_state.ctrl_pressed else 1
                    if game.add_to_queue(state_id, bt, quantity):
                        st.success(f"Queued {quantity} {bt.replace('_', ' ').title()} for {selected_state.name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to queue {bt.replace('_', ' ').title()} for {selected_state.name}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("**Construction Queue**")
    if not game.construction_queue:
        st.info("No construction projects in queue.")
    else:
        for i, project in enumerate(game.construction_queue):
            state = game.states[project.state_id]
            state_name = state.name
            speed_modifier = game.get_construction_speed_modifier(project.state_id, project.building_type)
            progress_percent = (project.progress / project.cost) * 100
            points_per_day = project.factories_assigned * CIVILIAN_FACTORY_OUTPUT * speed_modifier
            remaining_days = (project.cost - project.progress) / points_per_day if points_per_day > 0 else float('inf')
            remaining_days_display = '\u221E' if math.isinf(remaining_days) else f'{remaining_days:.1f}'
            st.markdown(f"""
                <div class='queue-item'>
                    {project.quantity} {project.building_type.replace('_', ' ').title()} in {state_name} (ID {project.state_id})<br>
                    Progress: {project.progress:.1f}/{project.cost:.1f} ({progress_percent:.1f}%)<br>
                    <div style='{{background-color: #4CAF50; width: {progress_percent}%; height: 10px}}'></div>
                    Points per Day: {points_per_day:.1f}<br>
                    Factories Assigned: {project.factories_assigned}<br>
                    Estimated Days Remaining: {remaining_days_display}
                </div>
            """, unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if i > 0 and st.button("Up", key=f"up_{i}_{project.state_id}_{project.building_type}"):
                    if st.session_state.ctrl_pressed:
                        game.construction_queue.pop(i)
                        game.construction_queue.insert(0, project)
                    else:
                        game.construction_queue[i], game.construction_queue[i-1] = game.construction_queue[i-1], game.construction_queue[i]
                    st.rerun()
            with col2:
                if i < len(game.construction_queue) - 1 and st.button("Down", key=f"down_{i}_{project.state_id}_{project.building_type}"):
                    if st.session_state.ctrl_pressed:
                        game.construction_queue.pop(i)
                        game.construction_queue.append(project)
                    else:
                        game.construction_queue[i], game.construction_queue[i+1] = game.construction_queue[i+1], game.construction_queue[i]
                    st.rerun()
            with col3:
                current_count = state.buildings.get(project.building_type, 0)
                max_count = state.max_buildings.get(project.building_type, DEFAULT_MAX_BUILDINGS[project.building_type])
                is_slot_occupying = project.building_type in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"]
                available_slots = (state.total_slots - state.used_slots) if is_slot_occupying else max_count - current_count
                if available_slots > 0 and st.button("+1", key=f"plus_{i}_{project.state_id}_{project.building_type}"):
                    if st.session_state.ctrl_pressed:
                        new_quantity = min(available_slots, max_count - current_count)
                    else:
                        new_quantity = 1
                    if new_quantity > 0:
                        project.quantity += new_quantity
                        project.cost += new_quantity * BUILDING_COSTS[project.building_type]
                        if is_slot_occupying:
                            state.used_slots += new_quantity
                        st.success(f"Increased {project.building_type.replace('_', ' ').title()} quantity by {new_quantity} in {state_name}")
                        st.rerun()
            with col4:
                if st.button("-1", key=f"minus_{i}_{project.state_id}_{project.building_type}"):
                    if st.session_state.ctrl_pressed:
                        game.construction_queue.pop(i)
                        if project.building_type in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"]:
                            state.used_slots -= project.quantity
                        st.success(f"Removed {project.building_type.replace('_', ' ').title()} from queue in {state_name}")
                    else:
                        if project.quantity > 1:
                            project.quantity -= 1
                            project.cost -= BUILDING_COSTS[project.building_type]
                            if project.building_type in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"]:
                                state.used_slots -= 1
                            st.success(f"Decreased {project.building_type.replace('_', ' ').title()} quantity by 1 in {state_name}")
                        else:
                            game.construction_queue.pop(i)
                            if project.building_type in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"]:
                                state.used_slots -= 1
                            st.success(f"Removed {project.building_type.replace('_', ' ').title()} from queue in {state_name}")
                    st.rerun()

        # Automatically assign factories, prioritizing top project
        available_factories = game.available_civ_factories()
        for project in game.construction_queue:
            project.factories_assigned = 0
        for project in game.construction_queue:
            factories_to_assign = min(available_factories, MAX_FACTORIES_PER_PROJECT)
            project.factories_assigned = factories_to_assign
            available_factories -= factories_to_assign

def render_simulation_controls():
    st.subheader("Simulation Controls")
    if not hasattr(st.session_state, "game") or not st.session_state.game:
        st.warning("No game state loaded. Please load states first.")
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        days_to_simulate = st.number_input("Days to Simulate", min_value=1, max_value=10000, value=1, step=1)
    with col2:
        if st.button("Simulate"):
            try:
                st.session_state.game.simulate_days(days_to_simulate)
                st.success(f"Simulated {days_to_simulate} days successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error during simulation: {e}")
    with col3:
        if st.button("Reset Simulation"):
            try:
                states = [State(**s) for s in st.session_state.settings["states"]]
                valid_game_params = [
                    "industry_level",
                    "construction_level",
                    "industry_days",
                    "construction_days",
                    "trade_law",
                    "mobilization_law",
                    "economic_law",
                    "rubber_factory_max"
                ]
                game_settings = {
                    k: v for k, v in st.session_state.settings.items()
                    if k in valid_game_params
                }
                st.session_state.game = Game(states=states, **game_settings)
                # Ensure settings["states"] contains dictionaries
                st.session_state.settings["states"] = [state_to_dict(s) for s in states]
                st.success("Simulation reset successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error resetting simulation: {e}")

def render_simulation_output():
    st.subheader("Simulation Output")
    if not hasattr(st.session_state, "game") or not st.session_state.game:
        st.warning("No game state loaded. Please load states first.")
        return
    game = st.session_state.game
    st.write(f"**Current Day**: {game.current_day}")
    st.write(f"**Total Civilian Factories**: {game.total_civ_factories}")
    st.write(f"**Total Military Factories**: {game.total_mil_factories}")
    st.write(f"**Total Dockyards**: {game.total_dockyards}")
    st.write(f"**Consumer Goods Factories**: {game.consumer_goods_factories():.2f}")
    st.write(f"**Available Civilian Factories**: {game.available_civ_factories()}")
    st.write(f"**Total Construction Points per Day**: {game.total_construction_points_per_day():.2f}")
    st.write(f"**Military Production**: {game.military_production:.2f}")
    st.write(f"**Naval Production**: {game.naval_production:.2f}")
    st.write("**State Details**:")
    state_data = [
        {
            "ID": state.id,
            "Name": state.name,
            "Category": STATE_CATEGORIES[state.category].name,
            "Total Slots": state.total_slots,
            "Used Slots": state.used_slots,
            "Infrastructure": state.infrastructure,
            "State Bonus": f"{state.state_bonus * 100:.1f}%",
            "Has Dam": "Yes" if state.has_dam else "No",
            **{bt.replace('_', ' ').title(): state.buildings.get(bt, 0) for bt in BUILDING_TYPES}
        }
        for state in game.states.values()
    ]
    st.table(pd.DataFrame(state_data))
    
    if game.construction_queue:
        chart_data = {
            "labels": [f"{p.building_type} in {game.states[p.state_id].name}" for p in game.construction_queue],
            "datasets": [{
                "label": "Construction Progress (%)",
                "data": [(p.progress / p.cost * 100) for p in game.construction_queue],
                "backgroundColor": "#4CAF50",
                "borderColor": "#45a049",
                "borderWidth": 1
            }]
        }
        st.markdown("**Construction Progress Chart**")
        st.markdown(f"""
            ```chartjs
            {{
                "type": "bar",
                "data": {json.dumps(chart_data)},
                "options": {{
                    "scales": {{
                        "y": {{ "beginAtZero": true, "max": 100, "title": {{ "display": true, "text": "Progress (%)" }} }}
                    }},
                    "plugins": {{ "legend": {{ "display": true }} }}
                }}
            }}""")