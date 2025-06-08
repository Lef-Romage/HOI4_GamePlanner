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
        self.cost = BUILDING_COSTS.get(self.building_type, 0) * self.quantity