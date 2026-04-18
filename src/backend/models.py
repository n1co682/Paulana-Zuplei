from typing import List, Optional
from pydantic import BaseModel, Field

class Component(BaseModel):
    id: Optional[str] = None
    supplier_id: Optional[str] = None
    name: str
    price_per_unit: Optional[int] = Field(None, description="Price per unit in cents or smallest currency unit")
    quality: Optional[int] = Field(None, ge=1, le=10, description="Quality rank from 1 to 10")
    text: Optional[str] = Field(None, description="Description or technical specifications")
    certificates: List[str] = Field(default_factory=list, description="Unique list of certificates like Non-GMO, Organic, etc.")
    allergens: List[str] = Field(default_factory=list, description="List of allergens")
    equivalence_class: str = Field(..., description="Category or class of the component (e.g., vitamins, oil)")
    lead_time: Optional[int] = Field(None, description="Lead time in hours")

class Supplier(BaseModel):
    id: Optional[str] = None
    name: str
    production_place: Optional[str] = None
    ethics: Optional[str] = Field(None, description="Description of ethics, scandals, or reputation")
    esg_score: Optional[int] = Field(None, description="Sustainability score")
    components: List[Component] = Field(default_factory=list)
