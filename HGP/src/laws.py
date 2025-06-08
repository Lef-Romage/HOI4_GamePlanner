from dataclasses import dataclass
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
            self.economic_law = new_law