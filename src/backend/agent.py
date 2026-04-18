from typing import List, Dict
from .models import Component, Supplier
from .database_mock import db
from . import tools

class AgnesAgent:
    def __init__(self, equivalence_class: str):
        self.equivalence_class = equivalence_class
        self.pool: List[Component] = []

    def run(self) -> List[Component]:
        print(f"--- Starting Agnes Agent for: {self.equivalence_class} ---")
        
        # 1. Get current DB info
        self.pool = db.get_components_by_equivalence_class(self.equivalence_class)
        print(f"Found {len(self.pool)} existing components in DB.")

        # 2. Enrich existing components if fields are missing
        for comp in self.pool:
            self._enrich_component(comp)

        # 3. If less than 5 suppliers, search for new ones
        if len(self.pool) < 5:
            needed = 5 - len(self.pool)
            print(f"Only {len(self.pool)} suppliers found. Searching for {needed} more...")
            new_supplier_names = tools.search_suppliers(self.equivalence_class)
            
            if not isinstance(new_supplier_names, list):
                print(f"Warning: Expected list of suppliers, got {type(new_supplier_names)}. Using empty list.")
                new_supplier_names = []

            for name in new_supplier_names[:needed]:
                # Create new supplier and component
                supplier = Supplier(name=name)
                db.add_supplier(supplier)
                
                component = Component(
                    name=f"{self.equivalence_class} from {name}",
                    equivalence_class=self.equivalence_class,
                    supplier_id=supplier.id
                )
                db.add_component(component)
                
                # Enrich new data
                self._enrich_component(component)
                self.pool.append(component)

        print(f"Final pool contains {len(self.pool)} options.")
        return self.pool[:5]

    def _enrich_component(self, component: Component):
        print(f"Enriching component: {component.name}...")
        
        # Get supplier
        supplier = db.get_supplier(component.supplier_id)
        if not supplier:
            return

        # Scrape specs if missing
        if not component.quality or not component.text:
            specs = tools.scrape_component_data(supplier.name, component.name)
            component.quality = specs.get("quality", component.quality)
            component.text = specs.get("text", component.text)
            component.certificates = list(set(component.certificates + specs.get("certificates", [])))
            component.allergens = list(set(component.allergens + specs.get("allergens", [])))

        # Enrich supplier info if missing
        if not supplier.ethics or not supplier.esg_score:
            ethics_data = tools.analyze_supplier_ethics(supplier.name)
            supplier.ethics = ethics_data.get("ethics", supplier.ethics)
            supplier.esg_score = ethics_data.get("esg_score", supplier.esg_score)
            supplier.production_place = ethics_data.get("production_place", supplier.production_place)

        # Mock negotiation for price and lead time (always do this for demo)
        negotiation = tools.generate_mock_negotiation(supplier.name, component.name)
        component.price_per_unit = negotiation.get("price_per_unit", component.price_per_unit)
        component.lead_time = negotiation.get("lead_time", component.lead_time)
        
        # In a real app, we'd save the email text somewhere
        print(f"Mock negotiation completed for {supplier.name}.")

def make_decision(components: List[Component]) -> Component:
    """Mock the decision system for now."""
    print("--- Decision System ---")
    if not components:
        return None
    # Just return the one with best quality/price ratio or first one
    return components[0]
