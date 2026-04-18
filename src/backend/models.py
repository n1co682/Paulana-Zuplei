from dataclasses import dataclass, field
from typing import List, Dict
from component_from_supplier import ComponentFromSupplier

@dataclass(frozen=True)           # frozen=True makes it hashable → usable as dict key
class BOMEntry:
    component_id: str
    equivalence_class: str
    required_certs: tuple[str, ...] = field(default_factory=tuple)
    forbidden_allergens: tuple[str, ...] = field(default_factory=tuple)

BillOfMaterials = List[BOMEntry]  # simple type alias, no wrapper class needed

@dataclass
class UserPreferences:
    price: int = 0          # 0 = ignore, 1–5 = priority
    quality: int = 0
    resilience: int = 0
    sustainability: int = 0
    ethics: int = 0
    lead_time: int = 0

@dataclass
class RankedOption:
    component: ComponentFromSupplier
    score: float             # 0.0–1.0, higher is better

# Type aliases for the pipeline outputs
ReplacementMap = Dict[BOMEntry, List[ComponentFromSupplier]]
RankedMap      = Dict[BOMEntry, List[RankedOption]]