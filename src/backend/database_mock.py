import uuid
from typing import List, Dict, Optional
from .models import Supplier, Component

class MockDatabase:
    def __init__(self):
        self.suppliers: Dict[str, Supplier] = {}
        self.components: Dict[str, Component] = {}

    def add_supplier(self, supplier: Supplier) -> str:
        if not supplier.id:
            supplier.id = str(uuid.uuid4())
        self.suppliers[supplier.id] = supplier
        return supplier.id

    def add_component(self, component: Component) -> str:
        if not component.id:
            component.id = str(uuid.uuid4())
        self.components[component.id] = component
        if component.supplier_id and component.supplier_id in self.suppliers:
            self.suppliers[component.supplier_id].components.append(component)
        return component.id

    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        return self.suppliers.get(supplier_id)

    def get_components_by_equivalence_class(self, eq_class: str) -> List[Component]:
        return [c for c in self.components.values() if c.equivalence_class == eq_class]

    def get_suppliers_by_component_class(self, eq_class: str) -> List[Supplier]:
        supplier_ids = {c.supplier_id for c in self.components.values() if c.equivalence_class == eq_class and c.supplier_id}
        return [self.suppliers[sid] for sid in supplier_ids if sid in self.suppliers]

    def update_component(self, component_id: str, updates: Dict):
        if component_id in self.components:
            comp = self.components[component_id]
            for key, value in updates.items():
                if hasattr(comp, key):
                    setattr(comp, key, value)

    def update_supplier(self, supplier_id: str, updates: Dict):
        if supplier_id in self.suppliers:
            supp = self.suppliers[supplier_id]
            for key, value in updates.items():
                if hasattr(supp, key):
                    setattr(supp, key, value)

# Singleton instance for the mock DB
db = MockDatabase()
