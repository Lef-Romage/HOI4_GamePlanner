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
}