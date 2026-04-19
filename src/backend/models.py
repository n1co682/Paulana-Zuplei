from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# Try to import from other team files
try:
    from .component_from_supplier import ComponentFromSupplier
except ImportError:
    try:
        from component_from_supplier import ComponentFromSupplier
    except ImportError:
        # Fallback for tests or unexpected structure
        class ComponentFromSupplier:
            pass

# Team's existing classes
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
    p_score: float # Price
    q_score: float # Quality
    r_score: float # Resilience
    s_score: float # Sustainability
    e_score: float # Ethics
    l_score: float # Lead Time
    c_score: float # Consolidation
    unique_suppliers: int

@dataclass
class RankedOption:
    component: ComponentFromSupplier
    total_score: float
    p_score: float
    q_score: float
    r_score: float
    s_score: float
    e_score: float
    l_score: float
    c_score: float

# Type aliases for the pipeline outputs
ReplacementMap = Dict[BOMEntry, List[ComponentFromSupplier]]
RankedMap      = Dict[BOMEntry, List[RankedOption]]

# Agnes Scraper/LLM Agent classes
class Component(BaseModel):
    id: Optional[str] = None
    supplier_id: Optional[str] = None
    name: str
    price_per_unit: Optional[int] = Field(None, description="Price per unit in cents or smallest currency unit")
    quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality rank from 0.0 to 1.0")
    text: Optional[str] = Field(None, description="Description or technical specifications")
    certificates: List[str] = Field(default_factory=list, description="Unique list of certificates like Non-GMO, Organic, etc.")
    allergens: List[str] = Field(default_factory=list, description="List of allergens")
    equivalence_class: str = Field(..., description="Category or class of the component (e.g., vitamins, oil)")
    lead_time: Optional[int] = Field(None, description="Lead time in hours")
    production_place: Optional[str] = None

class Supplier(BaseModel):
    id: Optional[str] = None
    name: str
    production_place: Optional[str] = None
    ethics: Optional[str] = Field(None, description="Description of ethics, scandals, or reputation")
    esg_score: Optional[int] = Field(None, description="Sustainability score")
    components: List[Component] = Field(default_factory=list)
