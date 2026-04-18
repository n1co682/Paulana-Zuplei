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
                equivalence_class=row[2]
            ))
    return bom

def agnes_to_pipeline_model(agnes_comp: AgnesComponent) -> ComponentFromSupplier:
    """Bridge: Convert Agnes Component model to Team's Pipeline model."""
    supp = db.get_supplier(agnes_comp.supplier_id)
    return ComponentFromSupplier(
        supplier_name=supp.name,
        price_per_unit=agnes_comp.price_per_unit / 100.0 if agnes_comp.price_per_unit else 1.0,
        price_scaled=0.5, 
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

def print_dimension_scores(label: str, rb, width=8):
    """Print a row of scores across dimensions."""
    headers = ["Price", "Qual", "Resil", "Sust", "Eth", "Lead", "Cons"]
    scores = [rb.p_score, rb.q_score, rb.r_score, rb.s_score, rb.e_score, rb.l_score, rb.c_score]
    
    score_line = " | ".join([f"{headers[i]}: {scores[i]:.2f}" for i in range(len(headers))])
    print(f"\n[{label}] Total Score: {rb.total_score:.3f}")
    print(f"  Dimensions -> {score_line}")
    print(f"  Unique Suppliers: {rb.unique_suppliers}")

def main():
    logger.info("Starting Agnes AI Supply Chain Manager Integration")
    
    # 1. Input Section
    product_id = 2
    prefs = UserPreferences(price=3, quality=7, sustainability=5, ethics=8, consolidation=4)
    
    print(f"\n{'='*80}")
    print(f"{'AGNES SUPPLY CHAIN OPTIMIZATION REPORT':^80}")
    print(f"{'='*80}")
    
    # 2. Original BOM
    bom = fetch_bom_from_db(product_id)
    print(f"\n[ORIGINAL BOM] Product ID: {product_id}")
    for entry in bom:
        print(f"  • {entry.component_id}: {entry.equivalence_class}")
        
    # 3. User Priorities
    print(f"\n[USER PRIORITIES]")
    print(f"  Quality: {prefs.quality} | Ethics: {prefs.ethics} | Price: {prefs.price} | "
          f"Sustainability: {prefs.sustainability} | Consolidation: {prefs.consolidation}")
    print("-" * 80)

    # 4. Enrichment (Agnes)
    all_contenders: List[ComponentFromSupplier] = []
    processed_classes = set()
    
    for entry in bom:
        if entry.equivalence_class in processed_classes:
            continue
        agent = AgnesAgent(entry.equivalence_class)
        agnes_pool = agent.run()
        for ac in agnes_pool:
            all_contenders.append(agnes_to_pipeline_model(ac))
        processed_classes.add(entry.equivalence_class)

    # 5. Decision Logic
    replacements = find_replacements(bom, all_contenders)
    
    # Identify a "Baseline" (e.g., the first supplier found for each material)
    baseline_config = {}
    for entry in bom:
        if replacements[entry]:
            baseline_config[entry] = replacements[entry][0]
    
    baseline_ranked = evaluate_config(baseline_config, prefs) if baseline_config else None
    
    all_ranked = rank_configurations(replacements, prefs)
    
    # 6. Results Output
    print(f"\n{'='*80}")
    print(f"{'BASELINE vs OPTIMIZED CONFIGURATIONS':^80}")
    print(f"{'='*80}")
    
    if baseline_ranked:
        print_dimension_scores("ORIGINAL BOM (Baseline)", baseline_ranked)
        print("  Current Suppliers:")
        for entry, comp in baseline_ranked.configuration.items():
            print(f"    - {entry.equivalence_class}: {comp.supplier_name:<20} (Qual: {comp.quality:.2f}, Price: ${comp.price_per_unit:.2f})")
        print("-" * 80)

    print(f"\n{'TOP 3 OPTIMIZED ALTERNATIVES':^80}")
    print(f"{'-'*80}")
    
    for i, top in enumerate(all_ranked[:3], 1):
        if baseline_ranked and top.total_score <= baseline_ranked.total_score:
            if i == 1: print("  (No better alternatives found than baseline)")
            break
            
        print_dimension_scores(f"OPTIMIZED OPTION #{i}", top)
        print("  Selected Suppliers:")
        for entry, comp in top.configuration.items():
            print(f"    - {entry.equivalence_class}: {comp.supplier_name:<20} (Qual: {comp.quality:.2f}, Price: ${comp.price_per_unit:.2f})")
        print("-" * 40)
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()