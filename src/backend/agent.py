import logging
from typing import List, Dict
from models import Component, Supplier
from database_manager import DatabaseManager
import tools

logger = logging.getLogger("agnes.agent")

# Initialize DB Manager
db = DatabaseManager()

class AgnesAgent:
    def __init__(self, equivalence_class: str):
        self.equivalence_class = equivalence_class
        self.pool: List[Component] = []

    def run(self) -> List[Component]:
        logger.info(f"--- STAGE: INITIALIZING AGENT FOR {self.equivalence_class.upper()} ---")
        
        # 1. Get current DB info
        self.pool = db.get_components_by_equivalence_class(self.equivalence_class)
        logger.info(f"--- STAGE: DATABASE LOOKUP | Found {len(self.pool)} existing components ---")

        # 2. Enrich existing components if fields are missing (limit to top 5)
        for comp in self.pool[:5]:
            self._enrich_component(comp)

        # 3. If less than 5 suppliers, search for new ones
        if len(self.pool) < 5:
            eq_id = db.get_equivalence_class_id(self.equivalence_class)
            if not eq_id:
                logger.error(f"Cannot expand: Equivalence class '{self.equivalence_class}' ID not found.")
            else:
                needed = 5 - len(self.pool)
                logger.info(f"--- STAGE: EXPANSION | Searching for {needed} new suppliers ---")
                new_supplier_names = tools.search_suppliers(self.equivalence_class)
                
                for name in new_supplier_names[:needed]:
                    # Add to DB
                    supplier = Supplier(name=name)
                    db.add_supplier(supplier)
                    
                    component = Component(
                        name=f"{self.equivalence_class} from {name}",
                        equivalence_class=self.equivalence_class,
                        supplier_id=supplier.id
                    )
                    db.add_component(component, eq_id)
                    
                    # Enrich and add to pool
                    self._enrich_component(component)
                    self.pool.append(component)

        # 4. STAGE: COMPARATIVE QUALITY
        if len(self.pool) >= 2:
            logger.info("--- STAGE: COMPARATIVE QUALITY | Ranking contenders relative to each other ---")
            contenders_data = []
            for comp in self.pool:
                supp = db.get_supplier(comp.supplier_id)
                contenders_data.append({
                    "supplier_name": supp.name,
                    "text": comp.text or "No specs found",
                    "certificates": comp.certificates
                })
            
            rankings = tools.compare_quality_pool(contenders_data)
            
            # Update quality in pool and DB
            for comp in self.pool:
                supp = db.get_supplier(comp.supplier_id)
                if supp.name in rankings:
                    comp.quality = rankings[supp.name]
                    db.update_product_enrichment(comp)

        logger.info(f"Final pool contains {len(self.pool)} options.")
        return self.pool[:5]

    def _enrich_component(self, component: Component):
        logger.info(f"--- STAGE: ENRICHMENT | Starting enrichment for {component.name} ---")
        
        # Get supplier
        supplier = db.get_supplier(component.supplier_id)
        if not supplier:
            logger.warning(f"Supplier {component.supplier_id} not found for component {component.name}")
            return

        # Scrape specs if missing
        if not component.quality or not component.text:
            logger.info(f"Scraping technical specs for {component.name}...")
            specs = tools.scrape_component_data(supplier.name, component.name)
            component.quality = specs.get("quality", component.quality)
            component.text = specs.get("text", component.text)
            component.certificates = list(set(component.certificates + specs.get("certificates", [])))
            component.allergens = list(set(component.allergens + specs.get("allergens", [])))
            db.update_product_enrichment(component)

        # Enrich supplier info if missing
        if not supplier.ethics or not supplier.esg_score:
            logger.info(f"Analyzing ethics and ESG for supplier {supplier.name}...")
            ethics_data = tools.analyze_supplier_ethics(supplier.name)
            supplier.ethics = ethics_data.get("ethics", supplier.ethics)
            supplier.esg_score = ethics_data.get("esg_score", supplier.esg_score)
            supplier.production_place = ethics_data.get("production_place", supplier.production_place)
            db.update_supplier_enrichment(supplier)

        # Mock negotiation for price and lead time (always do this for demo)
        logger.info(f"Initiating mock negotiation with {supplier.name}...")
        negotiation = tools.generate_mock_negotiation(supplier.name, component.name)
        component.price_per_unit = negotiation.get("price_per_unit", component.price_per_unit)
        component.lead_time = negotiation.get("lead_time", component.lead_time)
        db.update_product_enrichment(component)
        
        logger.info(f"Enrichment complete for {component.name}.")
