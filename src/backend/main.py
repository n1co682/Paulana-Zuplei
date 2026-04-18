import logging
import sqlite3
from typing import List, Dict
from pipeline import find_replacements, rank_configurations, evaluate_config
from models import BOMEntry, UserPreferences, Component as AgnesComponent
from component_from_supplier import ComponentFromSupplier
from agent import AgnesAgent, db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agnes.main")

def fetch_bom_from_db(product_id: int) -> List[BOMEntry]:
    """Fetch BOM for a specific product from SQLite."""
    bom = []
    with sqlite3.connect("data/db_new.sqlite") as conn:
        cursor = conn.cursor()
        query = """
            SELECT rm.Id, rm.Name, ec.Name 
            FROM BOM b
            JOIN RawMaterial rm ON b.Materiald = rm.Id
            JOIN "Equivalence Class" ec ON rm.EquivalenceClassId = ec.Id
            WHERE b.ProductID = ?
        """
        cursor.execute(query, (product_id,))
        for row in cursor.fetchall():
            bom.append(BOMEntry(
                component_id=str(row[0]),
                equivalence_class=row[2] # Agnes works with string names
            ))
    return bom

def agnes_to_pipeline_model(agnes_comp: AgnesComponent) -> ComponentFromSupplier:
    """Bridge: Convert Agnes Component model to Team's Pipeline model."""
    # Get supplier info from Agnes DB
    supp = db.get_supplier(agnes_comp.supplier_id)
    
    # Map Agnes values to Pipeline values
    return ComponentFromSupplier(
        supplier_name=supp.name,
        price_per_unit=agnes_comp.price_per_unit / 100.0 if agnes_comp.price_per_unit else 1.0,
        price_scaled=0.5, # Pipeline will re-scale this if needed
        quality=agnes_comp.quality or 0.5,
        quality_report=agnes_comp.text or "Enriched by Agnes",
        production_place=supp.production_place or "Global",
        resilience_score=0.7,
        ethics_score=(supp.esg_score / 100.0) if supp.esg_score else 0.5,
        ethics_report=supp.ethics or "N/A",
        esg_score=(supp.esg_score / 100.0) if supp.esg_score else 0.5,
        certificates=agnes_comp.certificates,
        allergents=agnes_comp.allergens,
        lead_time=float(agnes_comp.lead_time) if agnes_comp.lead_time else 72.0,
        lead_time_score=0.6,
        equivalence_class=agnes_comp.equivalence_class
    )

def main():
    logger.info("Starting Agnes AI Supply Chain Manager Integration")
    
    # 1. Fetch real BOM (e.g., Product ID 1)
    product_id = 1
    logger.info(f"Fetching BOM for Product ID: {product_id}")
    bom = fetch_bom_from_db(product_id)
    logger.info(f"BOM contains {len(bom)} materials.")

    # 2. Process each material with Agnes
    all_contenders: List[ComponentFromSupplier] = []
    processed_classes = set()
    
    for entry in bom:
        if entry.equivalence_class in processed_classes:
            continue
            
        logger.info(f"Processing category: {entry.equivalence_class}")
        agent = AgnesAgent(entry.equivalence_class)
        agnes_pool = agent.run()
        
        # Convert to pipeline models
        for ac in agnes_pool:
            all_contenders.append(agnes_to_pipeline_model(ac))
        
        processed_classes.add(entry.equivalence_class)

    # 3. Decision Logic Integration
    prefs = UserPreferences(price=3, quality=7, sustainability=5, ethics=5)
    logger.info("--- STAGE: DECISION PIPELINE ---")
    
    # The pipeline expects a ReplacementMap
    replacements = find_replacements(bom, all_contenders)
    
    # Rank configurations
    all_ranked = rank_configurations(replacements, prefs)
    
    if all_ranked:
        top = all_ranked[0]
        print(f"\n{'='*60}")
        print(f"{'AGNES FINAL RECOMMENDATION':^60}")
        print(f"{'='*60}")
        print(f"Total Score: {top.total_score:.3f}")
        print(f"Unique Suppliers: {top.unique_suppliers}")
        print("-" * 60)
        for entry, comp in top.configuration.items():
            print(f"  • {entry.equivalence_class}: {comp.supplier_name} (Qual: {comp.quality}, Price: ${comp.price_per_unit})")
        print(f"{'='*60}\n")
    else:
        print("No valid configurations found.")

if __name__ == "__main__":
    main()