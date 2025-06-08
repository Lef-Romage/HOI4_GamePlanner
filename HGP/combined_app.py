import streamlit as st
from src.ui import (
    apply_css,
    initialize_session_state,
    render_law_settings,
    render_save_load_settings,
    render_state_loader,
    render_state_settings,
    render_tech_settings,
    render_construction_projects,
    render_simulation_controls,
    render_simulation_output
)

st.set_page_config(page_title="HOI4 Planner", layout="wide")
apply_css()
st.title("Hearts of Iron IV Planner")
initialize_session_state()

tab1, tab2, tab3, tab4 = st.tabs(["State Management", "Law & Tech Settings", "Construction", "Simulation"])

with tab1:
    render_state_loader()
    render_state_settings()
    render_save_load_settings()

with tab2:
    render_law_settings()
    render_tech_settings()

with tab3:
    render_construction_projects()

with tab4:
    render_simulation_controls()

# Contents of src/config.py
from typing import Dict

# HOI4 building types
BUILDING_TYPES = [
    "infrastructure", "military_factory", "civilian_factory", "air_base", "dockyard",
    "anti_air", "synthetic_refinery", "fuel_silo", "radar_station", "rocket_site",
    "nuclear_reactor", "bunker", "coastal_bunker", "naval_base", "supply_node", "rail_way"
]

# Building costs from HOI4
BUILDING_COSTS: Dict[str, float] = {
    "infrastructure": 6000,
    "military_factory": 7200,
    "civilian_factory": 10800,
    "air_base": 1250,
    "dockyard": 6400,
    "anti_air": 2500,
    "synthetic_refinery": 14500,
    "fuel_silo": 5000,
    "radar_station": 3375,
    "rocket_site": 6400,
    "nuclear_reactor": 30000,
    "bunker": 500,
    "coastal_bunker": 500,
    "naval_base": 5000,
    "supply_node": 20000,
    "rail_way": 170
}

# Building caps
DEFAULT_MAX_BUILDINGS: Dict[str, int] = {
    "infrastructure": 5,
    "military_factory": 20,
    "civilian_factory": 20,
    "air_base": 10,
    "dockyard": 20,
    "anti_air": 5,
    "synthetic_refinery": 3,
    "fuel_silo": 5,
    "radar_station": 6,
    "rocket_site": 3,
    "nuclear_reactor": 1,
    "bunker": 10,
    "coastal_bunker": 10,
    "naval_base": 10,
    "supply_node": 1,
    "rail_way": 1
}

# State categories
STATE_CATEGORIES = {
    "rural": type("Category", (), {"slots": 4, "name": "Rural"})(),
    "town": type("Category", (), {"slots": 6, "name": "Town"})(),
    "large_town": type("Category", (), {"slots": 8, "name": "Large Town"})(),
    "city": type("Category", (), {"slots": 10, "name": "City"})(),
    "large_city": type("Category", (), {"slots": 12, "name": "Large City"})(),
    "metropolis": type("Category", (), {"slots": 16, "name": "Metropolis"})(),
    "megalopolis": type("Category", (), {"slots": 20, "name": "Megalopolis"})()
}

# Laws
# Laws
TRADE_LAWS = {
    "free_trade": {"construction_speed": 0.15, "factory_output": 0.10},
    "export_focus": {"construction_speed": 0.10, "factory_output": 0.05},
    "limited_exports": {"construction_speed": 0.05, "factory_output": 0.0},
    "closed_economy": {"construction_speed": 0.0, "factory_output": -0.05}
}

ECONOMIC_LAWS = {
    "civilian_economy": {"consumer_goods": 0.35, "civilian_factory_speed": -0.3, "military_factory_speed": -0.3},
    "early_mobilization": {"consumer_goods": 0.30, "civilian_factory_speed": -0.2, "military_factory_speed": -0.1},
    "partial_mobilization": {"consumer_goods": 0.25, "civilian_factory_speed": -0.1, "military_factory_speed": 0.0},
    "war_economy": {"consumer_goods": 0.20, "civilian_factory_speed": 0.0, "military_factory_speed": 0.1},
    "total_mobilization": {"consumer_goods": 0.10, "civilian_factory_speed": 0.0, "military_factory_speed": 0.2}
}

MOBILIZATION_LAWS = ["volunteer_only", "limited_conscription", "extensive_conscription", "service_by_requirement", "all_adults_serve"]

# Construction constants
CIVILIAN_FACTORY_OUTPUT = 5.0  # Construction points per day per factory
MAX_FACTORIES_PER_PROJECT = 15
INFRASTRUCTURE_SPEED_BONUS = 0.20  # +20% per infrastructure level

# Technology effects
TECHNOLOGY_EFFECTS = {
    "construction1": {"construction_speed": 0.10},
    "construction2": {"construction_speed": 0.10},
    "construction3": {"construction_speed": 0.10},
    "construction4": {"construction_speed": 0.10},
    "construction5": {"construction_speed": 0.10},
    "industry1": {"factory_output": 0.10},
    "industry2": {"factory_output": 0.10},
    "industry3": {"factory_output": 0.10},
    "industry4": {"factory_output": 0.10},
    "industry5": {"factory_output": 0.10}
}

MAJOR_COUNTRIES = {
    "Germany": "GER",
    "United Kingdom": "ENG",
    "France": "FRA",
    "Soviet Union": "SOV",
    "United States": "USA",
    "Italy": "ITA",
    "Japan": "JAP"
}

# Default settings
DEFAULT_SETTINGS = {
    "states": [
        {
            "id": 1,
            "name": "Placeholder",
            "category": "rural",
            "total_slots": 2,
            "infrastructure": 0,
            "buildings": {bt: 0 for bt in BUILDING_TYPES},
            "owner": "NONE",
            "state_bonus": 0.0,
            "max_buildings": DEFAULT_MAX_BUILDINGS.copy(),
            "provinces": [],
            "history": {"victory_points": [], "cores": []},
            "manpower": 0,
            "province_buildings": {},
            "has_dam": False
        }
    ],
    "consumer_goods_percent": 0.35,
    "cgff": 0.0,
    "modifiers": {"global": 0.0, "stability": 0.0, "war_support": 0.0, **{bt: 0.0 for bt in BUILDING_TYPES}},
    "industry_level": 0,
    "industry_days": [0] * 5,
    "construction_level": 0,
    "construction_days": [0] * 5,
    "trade_law": "free_trade",
    "mobilization_law": "volunteer_only",
    "economic_law": "civilian_economy",
    "rubber_factory_max": 3,
    "stability": 50.0,
    "war_support": 0.0

# Contents of src/construction.py
from dataclasses import dataclass
from typing import Optional
from .config import BUILDING_TYPES, BUILDING_COSTS

@dataclass
class ConstructionProject:
    state_id: int
    building_type: str
    quantity: int
    cost: float  # Total cost in construction points
    progress: float = 0.0  # Progress in construction points
    factories_assigned: int = 0  # Number of civilian factories working on this project

    def __post_init__(self):
        if self.building_type not in BUILDING_TYPES:
            raise ValueError(f"Invalid building type: {self.building_type}")

# Contents of src/game.py
from typing import Dict, List
from .construction import ConstructionProject
from .laws import LawManager
from .state import State
from .config import (
    BUILDING_COSTS, CIVILIAN_FACTORY_OUTPUT, BUILDING_TYPES, 
    DEFAULT_MAX_BUILDINGS, MAX_FACTORIES_PER_PROJECT, 
    INFRASTRUCTURE_SPEED_BONUS, TECHNOLOGY_EFFECTS
)

class GameError(Exception):
    pass

class Game:
    def __init__(
        self,
        states: List[dict],
        industry_level: int = 0,
        construction_level: int = 0,
        industry_days: List[int] = [0] * 5,
        construction_days: List[int] = [0] * 5,
        trade_law: str = "free_trade",
        mobilization_law: str = "volunteer_only",
        economic_law: str = "civilian_economy",
        rubber_factory_max: int = 3,
        current_day: int = 0,
        consumer_goods_percent: float = 0.35,
        stability: float = 50.0,
        war_support: float = 0.0,
        modifiers: Dict[str, float] = None
    ):
        self.states: Dict[int, State] = {s['id']: State(**s) for s in states}
        self.industry_level = min(max(0, industry_level), 5)
        self.construction_level = min(max(0, construction_level), 5)
        self.industry_days = industry_days
        self.construction_days = construction_days
        self.trade_law = trade_law
        self.mobilization_law = mobilization_law
        self.economic_law = economic_law
        self.rubber_factory_max = rubber_factory_max
        self.current_day = current_day
        self.consumer_goods_percent = consumer_goods_percent
        self.stability = stability
        self.war_support = war_support
        self.modifiers = modifiers or {"global": 0.0, "stability": 0.0, "war_support": 0.0, **{bt: 0.0 for bt in BUILDING_TYPES}}
        self.construction_queue: List[ConstructionProject] = []
        self.law_manager = LawManager(trade_law, mobilization_law, economic_law, stability, war_support)
        for state in self.states.values():
            state.max_buildings["synthetic_refinery"] = rubber_factory_max
        self._update_factory_totals()
        self._update_modifiers()

    def _update_modifiers(self):
        self.law_manager.update_modifiers(self.current_day)
        construction_modifier = 0.0
        for i in range(1, self.construction_level + 1):
            if self.construction_days[i-1] <= self.current_day:
                construction_modifier += TECHNOLOGY_EFFECTS[f"construction{i}"]["construction_speed"]
        self.modifiers["construction_speed"] = (
            self.law_manager.get_construction_speed_modifier("generic") + 
            construction_modifier + 
            self.modifiers.get("global", 0.0)
        )

    def get_construction_speed_modifier(self, state_id: int, building_type: str) -> float:
        state = self.states.get(state_id)
        if not state:
            return 0.0
        base_modifier = 1.0 + (state.infrastructure * INFRASTRUCTURE_SPEED_BONUS) + state.state_bonus
        if state.has_dam:
            base_modifier += 0.15
        total_modifier = base_modifier + self.law_manager.get_construction_speed_modifier(building_type)
        return max(0.0, total_modifier)

    def add_to_queue(self, state_id: int, building_type: str, quantity: int) -> bool:
        if building_type not in BUILDING_TYPES:
            return False
        state = self.states.get(state_id)
        if not state:
            return False
        current_count = state.buildings.get(building_type, 0)
        max_count = state.max_buildings.get(building_type, DEFAULT_MAX_BUILDINGS[building_type])
        if current_count + quantity > max_count:
            return False
        total_slots_needed = quantity if building_type in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"] else 0
        if state.used_slots + total_slots_needed > state.total_slots:
            return False
        base_cost = BUILDING_COSTS.get(building_type, 0)
        for _ in range(quantity):
            project = ConstructionProject(
                state_id=state_id,
                building_type=building_type,
                quantity=1,
                cost=base_cost
            )
            self.construction_queue.append(project)
        state.used_slots += total_slots_needed
        return True

    def simulate_days(self, days: int):
        if days <= 0:
            return
        for _ in range(days):
            self.current_day += 1
            self._update_modifiers()
            available_factories = self.available_civ_factories()
            if not self.construction_queue:
                continue
            for project in self.construction_queue:
                project.factories_assigned = 0
            for project in self.construction_queue[:]:
                if available_factories <= 0:
                    break
                factories = min(available_factories, project.factories_assigned or MAX_FACTORIES_PER_PROJECT)
                project.factories_assigned = factories
                speed_modifier = self.get_construction_speed_modifier(project.state_id, project.building_type)
                points_per_day = factories * CIVILIAN_FACTORY_OUTPUT * speed_modifier
                project.progress += points_per_day
                available_factories -= factories
                if project.progress >= project.cost:
                    state = self.states[project.state_id]
                    state.buildings[project.building_type] = state.buildings.get(project.building_type, 0) + 1
                    self.construction_queue.remove(project)
                    state.used_slots -= 1 if project.building_type in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"] else 0
                    available_factories += factories
                    self._update_factory_totals()
                    for next_project in self.construction_queue:
                        if available_factories <= 0:
                            break
                        next_factories = min(available_factories, MAX_FACTORIES_PER_PROJECT)
                        next_project.factories_assigned = next_factories
                        available_factories -= next_factories
            self._update_factory_totals()
        self._update_consumer_goods()

    def _update_factory_totals(self):
        self.total_civ_factories = sum(state.buildings.get("civilian_factory", 0) for state in self.states.values())
        self.total_mil_factories = sum(state.buildings.get("military_factory", 0) for state in self.states.values())
        self.total_dockyards = sum(state.buildings.get("dockyard", 0) for state in self.states.values())

    def _update_consumer_goods(self):
        total_factories = self.total_civ_factories + self.total_mil_factories + self.total_dockyards
        self.consumer_goods_percent = (
            ECONOMIC_LAWS[self.economic_law]["consumer_goods"] +
            (0.05 if self.stability < 50 else -0.05 if self.stability > 75 else 0.0)
        )

    def available_civ_factories(self):
        consumer_goods = (self.total_civ_factories + self.total_mil_factories + self.total_dockyards) * self.consumer_goods_percent
        return max(0, int(self.total_civ_factories - consumer_goods + 0.999))

    def total_construction_points_per_day(self):
        return sum(
            project.factories_assigned * CIVILIAN_FACTORY_OUTPUT * self.get_construction_speed_modifier(project.state_id, project.building_type)
            for project in self.construction_queue
        )

    def consumer_goods_factories(self):
        return (self.total_civ_factories + self.total_mil_factories + self.total_dockyards) * self.consumer_goods_percent

    @property
    def military_production(self):
        factory_output_modifier = self.law_manager.modifiers.get("factory_output", 0.0) + sum(
            TECHNOLOGY_EFFECTS[f"industry{i}"]["factory_output"] for i in range(1, self.industry_level + 1) if self.industry_days[i-1] <= self.current_day
        )
        return sum(state.buildings.get("military_factory", 0) for state in self.states.values()) * (1.0 + factory_output_modifier)

    @property
    def naval_production(self):
        factory_output_modifier = self.law_manager.modifiers.get("factory_output", 0.0) + sum(
            TECHNOLOGY_EFFECTS[f"industry{i}"]["factory_output"] for i in range(1, self.industry_level + 1) if self.industry_days[i-1] <= self.current_day
        )

# Contents of src/laws.py
from typing import List, Dict
from .config import TRADE_LAWS, MOBILIZATION_LAWS, ECONOMIC_LAWS

@dataclass
class ModifierChange:
    day: int
    value: float
    description: str

@dataclass
class LawChange:
    day: int
    law_type: str
    new_law: str

class LawManager:
    def __init__(self, trade_law: str, mobilization_law: str, economic_law: str, stability: float = 50.0, war_support: float = 0.0):
        self.trade_law = trade_law if trade_law in TRADE_LAWS else "free_trade"
        self.mobilization_law = mobilization_law if mobilization_law in MOBILIZATION_LAWS else "volunteer_only"
        self.economic_law = economic_law if economic_law in ECONOMIC_LAWS else "civilian_economy"
        self.stability = stability
        self.war_support = war_support
        self.modifiers: Dict[str, float] = {
            "global": 0.0,
            "construction_speed": 0.0,
            "civilian_factory_speed": 0.0,
            "military_factory_speed": 0.0
        }
        self.modifier_changes: List[ModifierChange] = []
        self.law_changes: List[LawChange] = []

    def update_modifiers(self, day: int):
        active_laws = {
            "trade": self.trade_law,
            "mobilization": self.mobilization_law,
            "economic": self.economic_law
        }
        for change in sorted(self.law_changes, key=lambda x: x.day):
            if change.day <= day:
                if change.law_type == "trade" and change.new_law in TRADE_LAWS:
                    active_laws["trade"] = change.new_law
                elif change.law_type == "mobilization" and change.new_law in MOBILIZATION_LAWS:
                    active_laws["mobilization"] = change.new_law
                elif change.law_type == "economic" and change.new_law in ECONOMIC_LAWS:
                    active_laws["economic"] = change.new_law
        
        self.modifiers["construction_speed"] = (
            TRADE_LAWS[active_laws["trade"]]["construction_speed"] +
            ECONOMIC_LAWS[active_laws["economic"]]["civilian_factory_speed"] +
            (0.0 if self.stability >= 50 else (self.stability - 50) / 50 * -0.2) +
            (self.war_support / 100 * 0.1)
        )
        self.modifiers["civilian_factory_speed"] = ECONOMIC_LAWS[active_laws["economic"]]["civilian_factory_speed"]
        self.modifiers["military_factory_speed"] = ECONOMIC_LAWS[active_laws["economic"]]["military_factory_speed"]
        self.modifiers["factory_output"] = TRADE_LAWS[active_laws["trade"]]["factory_output"]

    def get_construction_speed_modifier(self, building_type: str) -> float:
        base = self.modifiers["construction_speed"]
        if building_type in ["civilian_factory", "military_factory"]:
            base += self.modifiers[f"{building_type}_speed"]
        return max(0.0, base)

    def apply_modifier_change(self, day: int, value: float, description: str):
        self.modifier_changes.append(ModifierChange(day, value, description))
        relevant_changes = [c for c in self.modifier_changes if c.day <= day]
        self.modifiers["global"] = sum(c.value for c in relevant_changes)

    def apply_law_change(self, day: int, law_type: str, new_law: str):
        self.law_changes.append(LawChange(day, law_type, new_law))
        if law_type == "trade" and new_law in TRADE_LAWS:
            self.trade_law = new_law
        elif law_type == "mobilization" and new_law in MOBILIZATION_LAWS:
            self.mobilization_law = new_law
        elif law_type == "economic" and new_law in ECONOMIC_LAWS:

# Contents of src/state.py
import logging
import re
from typing import Dict, Optional, List
from .config import BUILDING_TYPES, DEFAULT_MAX_BUILDINGS, STATE_CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class StateError(Exception):
    pass

class State:
    def __init__(
        self,
        id: int,
        name: str,
        category: str,
        total_slots: int,
        infrastructure: int,
        buildings: Dict[str, int],
        owner: str = "",
        state_bonus: float = 0.0,
        max_buildings: Optional[Dict[str, int]] = None,
        provinces: Optional[List[int]] = None,
        history: Optional[Dict] = None,
        manpower: int = 0,
        province_buildings: Optional[Dict[str, Dict]] = None,
        has_dam: bool = False
    ):
        self.id = id
        self.name = name[:50]
        self.category = category if category in STATE_CATEGORIES else "rural"
        self.total_slots = STATE_CATEGORIES[self.category].slots
        self.infrastructure = min(max(0, infrastructure), DEFAULT_MAX_BUILDINGS["infrastructure"])
        self.buildings = {
            bt: min(max(0, buildings.get(bt, 0)), DEFAULT_MAX_BUILDINGS[bt])
            for bt in BUILDING_TYPES
        }
        self.owner = owner
        self.state_bonus = min(max(0.0, float(state_bonus)), 1.0)
        self.max_buildings = max_buildings or DEFAULT_MAX_BUILDINGS.copy()
        self.provinces = provinces or []
        self.history = history or {"victory_points": [], "cores": []}
        self.manpower = max(0, manpower)
        self.province_buildings = province_buildings or {}
        self.has_dam = has_dam
        self.used_slots = sum(self.buildings.get(bt, 0) for bt in BUILDING_TYPES 
                             if bt in ["civilian_factory", "military_factory", "dockyard", "synthetic_refinery", "fuel_silo", "rocket_site", "nuclear_reactor"])
        if self.has_dam:
            self.total_slots = int(self.total_slots * 1.15)
            logger.info(f"Initialized state {self.name} (ID {self.id}) with dam: +15% total_slots")


def parse_state_file(file_content: bytes, country_tag: str = None) -> List[Dict]:
    states = []
    current_state = None
    in_history = False
    in_buildings = False
    in_1939 = False
    in_victory_points = False
    in_province_block = False
    in_allowed_block = False
    in_date_block = False
    province_id = None
    state_depth = 0

    building_mappings = {
        "arms_factory": "military_factory",
        "industrial_complex": "civilian_factory",
        "anti_air_building": "anti_air",
        "air_base": "air_base",
        "dockyard": "dockyard",
        "naval_base": "naval_base",
        "synthetic_refinery": "synthetic_refinery",
        "fuel_silo": "fuel_silo",
        "radar_station": "radar_station",
        "rocket_site": "rocket_site",
        "nuclear_reactor": "nuclear_reactor",
        "bunker": "bunker",
        "coastal_bunker": "coastal_bunker",
        "supply_node": "supply_node",
        "rail_way": "rail_way",
        "landmark_berlin_reichstag": None,
        "land_facility": None,
    }

    re_state = re.compile(r"^\s*state\s*=\s*{", re.IGNORECASE)
    re_history = re.compile(r"^\s*history\s*=\s*{", re.IGNORECASE)
    re_buildings = re.compile(r"^\s*buildings\s*=\s*{", re.IGNORECASE)
    re_victory_points = re.compile(r"^\s*victory_points\s*=\s*{", re.IGNORECASE)
    re_province = re.compile(r"^\s*(\d+)\s*=\s*{", re.IGNORECASE)
    re_1939 = re.compile(r"^\s*1939\.1\.1\s*=\s*{", re.IGNORECASE)
    re_date = re.compile(r"^\s*\d{4}\.\d{1,2}\.\d{1,2}\s*=\s*{", re.IGNORECASE)
    re_allowed = re.compile(r"^\s*allowed\s*=\s*{", re.IGNORECASE)
    re_id = re.compile(r"^\s*id\s*=\s*(\d+)", re.IGNORECASE)
    re_name = re.compile(r"^\s*name\s*=\s*(?:\"(.+?)\"|STATE_(\d+))", re.IGNORECASE)
    re_category = re.compile(r"^\s*state_category\s*=\s*(\w+)", re.IGNORECASE)
    re_max_level = re.compile(r"^\s*buildings_max_level_factor\s*=\s*([\d.]+)", re.IGNORECASE)
    re_manpower = re.compile(r"^\s*manpower\s*=\s*(\d+)", re.IGNORECASE)
    re_owner = re.compile(r"^\s*owner\s*=\s*(\w+)", re.IGNORECASE)
    re_core = re.compile(r"^\s*add_core_of\s*=\s*(\w+)", re.IGNORECASE)
    re_infrastructure = re.compile(r"^\s*infrastructure\s*=\s*(\d+)")
    re_local_supplies = re.compile(r"^\s*local_supplies\s*=\s*([\d.]+)", re.IGNORECASE)
    re_provinces = re.compile(r"^\s*provinces\s*=\s*{", re.IGNORECASE)
    re_vp = re.compile(r"^\s*(\d+)\s+(\d+)(?:\s+#\s*(\w+))?", re.IGNORECASE)
    re_level = re.compile(r"^\s*level\s*=\s*(\d+)", re.IGNORECASE)
    re_dlc = re.compile(r"^\s*has_dlc\s*=\s*\"(.+?)\"", re.IGNORECASE)
    re_dam = re.compile(r"^\s*dam\s*=\s*(\d+)", re.IGNORECASE)

    try:
        content_str = file_content.decode("utf-8", errors="ignore")
        logger.info(f"Parsing file with content length: {len(content_str)}")
        lines = content_str.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line or line.startswith("#"):
                continue
            logger.debug(f"Processing line: {line}")

            if "{" in line:
                state_depth += 1
                if re_state.match(line):
                    if current_state is not None:
                        if current_state.get("id") is not None:
                            states.append(current_state)
                            logger.info(f"Appended state: ID {current_state['id']} - {current_state['name']}")
                        else:
                            logger.warning(f"Discarding state missing id: {current_state['name']}")
                    current_state = {
                        "id": None,
                        "name": "Unknown",
                        "category": "rural",
                        "total_slots": STATE_CATEGORIES["rural"].slots,
                        "infrastructure": 0,
                        "buildings": {bt: 0 for bt in BUILDING_TYPES},
                        "owner": "",
                        "state_bonus": 0.0,
                        "max_buildings": DEFAULT_MAX_BUILDINGS.copy(),
                        "provinces": [],
                        "history": {"victory_points": [], "cores": []},
                        "manpower": 0,
                        "province_buildings": {},
                        "has_dam": False
                    }
                    logger.info(f"New state initialized, state_depth: {state_depth}")
                elif re_history.match(line):
                    if current_state is None:
                        logger.error(f"history= before state initialization, skipping: {line}")
                        continue
                    in_history = True
                    logger.debug("Entered history block")
                elif re_buildings.match(line):
                    if current_state is None:
                        logger.error(f"buildings= before state initialization, skipping: {line}")
                        continue
                    in_buildings = True
                    logger.debug("Entered buildings block")
                elif re_victory_points.match(line):
                    if current_state is None:
                        logger.error(f"victory_points= before state initialization, skipping: {line}")
                        continue
                    in_victory_points = True
                    logger.debug("Entered victory_points block")
                elif re_province.match(line):
                    if current_state is None:
                        logger.error(f"Province block before state initialization, skipping: {line}")
                        continue
                    province_id = re_province.search(line).group(1)
                    current_state["province_buildings"][province_id] = {}
                    in_province_block = True
                    logger.debug(f"Entered province block: {province_id}")
                elif re_1939.match(line):
                    if current_state is None:
                        logger.error(f"1939.1.1= before state initialization, skipping: {line}")
                        continue
                    in_1939 = True
                    in_date_block = True
                    logger.debug("Entered 1939.1.1 block")
                elif re_date.match(line):
                    if current_state is None:
                        logger.error(f"Date block before state initialization, skipping: {line}")
                        continue
                    in_date_block = True
                    logger.debug(f"Entered date block: {line}")
                elif re_allowed.match(line):
                    if current_state is None:
                        logger.error(f"allowed= before state initialization, skipping: {line}")
                        continue
                    in_allowed_block = True
                    logger.debug("Entered allowed block")

            elif "}" not in line:
                if current_state is None:
                    logger.error(f"Line before state initialization, skipping: {line}")
                    continue
                if re_id.match(line):
                    match = re_id.search(line)
                    current_state["id"] = int(match.group(1))
                    logger.info(f"Set id: {current_state['id']}")
                elif re_name.match(line):
                    match = re_name.search(line)
                    current_state["name"] = match.group(1) or f"State {match.group(2) or 'unknown'}"
                    logger.info(f"Set name: {current_state['name']}")
                elif re_category.match(line):
                    match = re_category.search(line)
                    category = match.group(1)
                    if category in STATE_CATEGORIES:
                        current_state["category"] = category
                        current_state["total_slots"] = STATE_CATEGORIES[category].slots
                    else:
                        logger.warning(f"Invalid state_category '{category}', defaulting to 'rural'")
                        current_state["category"] = "rural"
                        current_state["total_slots"] = STATE_CATEGORIES["rural"].slots
                    logger.info(f"Set category: {current_state['category']}, total_slots: {current_state['total_slots']}")
                elif re_max_level.match(line):
                    match = re_max_level.search(line)
                    try:
                        current_state["total_slots"] = int(float(match.group(1)) * 10)
                        logger.info(f"Set total_slots: {current_state['total_slots']}")
                    except ValueError:
                        logger.warning(f"Invalid buildings_max_level_factor: {line}")
                elif re_manpower.match(line):
                    match = re_manpower.search(line)
                    try:
                        current_state["manpower"] = int(match.group(1))
                        logger.info(f"Set manpower: {current_state['manpower']}")
                    except ValueError:
                        logger.warning(f"Invalid manpower: {line}")
                elif in_history and not in_date_block and re_owner.match(line):
                    match = re_owner.search(line)
                    current_state["owner"] = match.group(1)
                    logger.info(f"Set owner: {current_state['owner']}")
                elif in_history and re_core.match(line):
                    match = re_core.search(line)
                    current_state["history"]["cores"].append(match.group(1))
                    logger.info(f"Added core: {match.group(1)}")
                elif in_buildings and re_infrastructure.match(line):
                    match = re_infrastructure.search(line)
                    if not in_1939:
                        try:
                            current_state["infrastructure"] = min(int(match.group(1)), DEFAULT_MAX_BUILDINGS["infrastructure"])
                            logger.info(f"Set infrastructure: {current_state['infrastructure']}")
                        except ValueError:
                            logger.warning(f"Invalid infrastructure: {line}")
                elif in_buildings and not in_province_block:
                    for src, dest in building_mappings.items():
                        if src in line and dest:
                            match = re.search(r"=\s*(\d+)", line)
                            if match and not in_1939:
                                try:
                                    current_state["buildings"][dest] = min(int(match.group(1)), DEFAULT_MAX_BUILDINGS[dest])
                                    logger.info(f"Set building {dest}: {current_state['buildings'][dest]}")
                                except ValueError:
                                    logger.warning(f"Invalid building count for {src}: {line}")
                            break
                elif in_province_block:
                    for src, dest in building_mappings.items():
                        if src in line and dest:
                            match = re.search(r"=\s*(\d+)", line)
                            if match:
                                try:
                                    current_state["province_buildings"][province_id][dest] = int(match.group(1))
                                    logger.info(f"Set province {province_id} building {dest}: {match.group(1)}")
                                except ValueError:
                                    logger.warning(f"Invalid province building count for {src}: {line}")
                            break
                    if re_dam.match(line):
                        match = re_dam.search(line)
                        try:
                            dam_level = int(match.group(1))
                            if dam_level > 0:
                                current_state["has_dam"] = True
                                current_state["province_buildings"][province_id]["dam"] = dam_level
                                logger.info(f"Set has_dam: True for state {current_state['name']} (ID {current_state['id']}) due to dam = {dam_level} in province {province_id}")
                        except ValueError:
                            logger.warning(f"Invalid dam level: {line}")
                    elif re_level.match(line):
                        match = re_level.search(line)
                        try:
                            current_state["province_buildings"][province_id]["level"] = int(match.group(1))
                            logger.info(f"Set province {province_id} level: {match.group(1)}")
                        except ValueError:
                            logger.warning(f"Invalid level: {line}")
                    elif re_dlc.match(line):
                        match = re_dlc.search(line)
                        current_state["province_buildings"][province_id].setdefault("dlc", []).append(match.group(1))
                        logger.info(f"Set province {province_id} DLC: {match.group(1)}")
                elif in_victory_points and re_vp.match(line):
                    match = re_vp.search(line)
                    try:
                        vp = [int(match.group(1)), int(match.group(2))]
                        current_state["history"]["victory_points"].append(vp)
                        if match.group(3) and current_state["name"].startswith("STATE_"):
                            current_state["name"] = match.group(3)
                            logger.info(f"Updated name from victory_points: {current_state['name']}")
                        logger.info(f"Added victory_points: {vp}")
                    except ValueError:
                        logger.warning(f"Invalid victory_points: {line}")
                elif re_provinces.match(line):
                    province_list = line.split("{")[1].strip()
                    if "}" not in province_list and i < len(lines):
                        province_list += " " + lines[i].strip()
                        i += 1
                    province_list = province_list.split("}")[0].strip().split()
                    try:
                        current_state["provinces"] = [int(p) for p in province_list if p.isdigit()]
                        logger.info(f"Set provinces: {current_state['provinces']}")
                    except ValueError:
                        logger.warning(f"Invalid provinces: {line}")
                
                elif re_local_supplies.match(line):
                    match = re_local_supplies.search(line)
                    try:
                        value = float(match.group(1))
                        if value > 1.0:
                            logger.warning(f"Invalid local_supplies value {value} in state {current_state['name']} (ID {current_state['id']}), setting state_bonus to 0.0")
                            current_state["state_bonus"] = 0.0
                        else:
                            current_state["state_bonus"] = min(max(0.0, value), 1.0)
                        logger.info(f"Set state_bonus: {current_state['state_bonus']} for state {current_state['name']} (ID {current_state['id']})")
                    except ValueError:
                        logger.warning(f"Invalid local_supplies: {line}")
                        current_state["state_bonus"] = 0.0

            if "}" in line:
                state_depth -= 1
                if state_depth < 0:
                    logger.warning("state_depth became negative, resetting to 0")
                    state_depth = 0
                if in_victory_points:
                    in_victory_points = False
                    logger.debug("Exited victory_points block")
                elif in_allowed_block:
                    in_allowed_block = False
                    logger.debug("Exited allowed block")
                elif in_province_block:
                    in_province_block = False
                    province_id = None
                    logger.debug("Exited province block")
                elif in_buildings and in_1939:
                    in_1939 = False
                    in_date_block = False
                    logger.debug("Exited 1939.1.1 block")
                elif in_buildings:
                    in_buildings = False
                    logger.debug("Exited buildings block")
                elif in_history and in_date_block:
                    in_date_block = False
                    logger.debug("Exited date block")
                elif in_history:
                    in_history = False
                    logger.debug("Exited history block")
                elif state_depth <= 0 and current_state is not None:
                    if current_state.get("id") is None:
                        logger.error(f"Discarding state missing id: {current_state['name']}")
                        current_state = None
                        continue
                    if country_tag and current_state["owner"] != country_tag:
                        logger.info(f"Skipping state {current_state['name']} (ID {current_state['id']}): owner {current_state['owner']} != {country_tag}")
                        current_state = None
                        continue
                    current_state["state_bonus"] = min(max(0.0, current_state["state_bonus"]), 1.0)
                    current_state["infrastructure"] = min(max(0, current_state["infrastructure"]), DEFAULT_MAX_BUILDINGS["infrastructure"])
                    current_state["total_slots"] = max(0, min(current_state["total_slots"], 50))
                    if current_state["has_dam"]:
                        current_state["total_slots"] = int(current_state["total_slots"] * 1.15)
                        current_state["max_buildings"] = {k: int(v * 1.15) for k, v in current_state["max_buildings"].items()}
                        logger.info(f"Applied dam effect in parse_state_file for state {current_state['name']} (ID {current_state['id']}): +15% total_slots")
                    logger.debug(f"State {current_state['name']} (ID {current_state['id']}): has_dam = {current_state['has_dam']}")
                    states.append(current_state)
                    logger.info(f"Appended state: ID {current_state['id']} - {current_state['name']}")
                    current_state = None
                    state_depth = 0

        if current_state is not None and current_state.get("id") is not None:
            current_state["state_bonus"] = min(max(0.0, current_state["state_bonus"]), 1.0)
            current_state["infrastructure"] = min(max(0, current_state["infrastructure"]), DEFAULT_MAX_BUILDINGS["infrastructure"])
            current_state["total_slots"] = max(0, min(current_state["total_slots"], 50))
            if current_state["has_dam"]:
                current_state["total_slots"] = int(current_state["total_slots"] * 1.15)
                current_state["max_buildings"] = {k: int(v * 1.15) for k, v in current_state["max_buildings"].items()}
                logger.info(f"Applied dam effect for final state {current_state['name']} (ID {current_state['id']}): +15% total_slots")
            if country_tag and current_state["owner"] != country_tag:
                logger.info(f"Skipping final state {current_state['name']} (ID {current_state['id']}): owner {current_state['owner']} != {country_tag}")
            else:
                states.append(current_state)
                logger.info(f"Appended final state: ID {current_state['id']} - {current_state['name']}")

        if states:
            logger.info(f"Parsed {len(states)} states")
        else:
            logger.warning("No states parsed from file")
        return states

    except Exception as e:
        logger.error(f"Parsing error: {e}")

# Contents of src/ui.py
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
            state_name = game.states[project.state_id].name
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
            col1, col2 = st.columns(2)
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

        # Automatically assign factories
        available_factories = game.available_civ_factories()
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

