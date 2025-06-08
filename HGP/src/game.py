from typing import Dict, List
from .construction import ConstructionProject
from .laws import LawManager
from .state import State
from .config import (
    BUILDING_COSTS, CIVILIAN_FACTORY_OUTPUT, BUILDING_TYPES, 
    DEFAULT_MAX_BUILDINGS, MAX_FACTORIES_PER_PROJECT, 
    INFRASTRUCTURE_SPEED_BONUS, TECHNOLOGY_EFFECTS, ECONOMIC_LAWS
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
            # Reset factory assignments
            for project in self.construction_queue:
                project.factories_assigned = 0
            for project in self.construction_queue[:]:
                if available_factories <= 0:
                    break
                factories = min(available_factories, MAX_FACTORIES_PER_PROJECT)
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
        return sum(state.buildings.get("dockyard", 0) for state in self.states.values()) * (1.0 + factory_output_modifier)