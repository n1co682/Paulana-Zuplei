from dataclasses import dataclass, field
from typing import List, Dict
from component_from_supplier import ComponentFromSupplier

@dataclass(frozen=True)
class BOMEntry:
    component_id: str
    equivalence_class: str
    required_certs: tuple[str, ...] = field(default_factory=tuple)
    forbidden_allergens: tuple[str, ...] = field(default_factory=tuple)

BillOfMaterials = List[BOMEntry]

@dataclass
class UserPreferences:
    price: int = 0
    quality: int = 0
    resilience: int = 0
    sustainability: int = 0
    ethics: int = 0
    lead_time: int = 0
    consolidation: int = 0

BOMConfiguration = Dict[BOMEntry, ComponentFromSupplier]

@dataclass
class RankedBOM:
    configuration: BOMConfiguration
    total_score: float
    # Dim averages for insightful printing
    p_score: float # Price
    q_score: float # Quality
    r_score: float # Resilience
    s_score: float # Sustainability
    e_score: float # Ethics
    l_score: float # Lead Time
    c_score: float # Consolidation
    unique_suppliers: int

ReplacementMap = Dict[BOMEntry, List[ComponentFromSupplier]]