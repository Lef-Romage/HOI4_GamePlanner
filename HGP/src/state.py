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
        return []