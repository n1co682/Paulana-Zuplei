import itertools
import logging
from typing import List, Dict
from models import (BillOfMaterials, UserPreferences, RankedBOM, 
                    BOMConfiguration, ReplacementMap)
from component_from_supplier import ComponentFromSupplier

logger = logging.getLogger("agnes.pipeline")

def find_replacements(bom: BillOfMaterials, db: List[ComponentFromSupplier]) -> ReplacementMap:
    logger.info(f"--- STAGE: PIPELINE | Finding replacements for {len(bom)} materials ---")
    result: ReplacementMap = {}
    for entry in bom:
        candidates = [
            c for c in db if c.equivalence_class == entry.equivalence_class
            and all(cert in c.certificates for cert in entry.required_certs)
            and not any(alg in c.allergents for alg in entry.forbidden_allergens)
        ]
        result[entry] = candidates
        logger.info(f"  • {entry.equivalence_class}: Found {len(candidates)} valid substitutes")
    return result

def rank_configurations(replacements: ReplacementMap, prefs: UserPreferences) -> List[RankedBOM]:
    entries = list(replacements.keys())
    candidate_lists = [replacements[e] for e in entries]
    
    # Calculate total combinations
    total_combos = 1
    for cl in candidate_lists:
        total_combos *= len(cl) if cl else 0
    
    logger.info(f"--- STAGE: PIPELINE | Evaluating {total_combos} possible BOM configurations ---")
    
    results = []
    for i, combo in enumerate(itertools.product(*candidate_lists)):
        config = dict(zip(entries, combo))
        results.append(evaluate_config(config, prefs))
        if (i + 1) % 100 == 0:
            logger.info(f"  Processed {i+1}/{total_combos} configurations...")

    sorted_results = sorted(results, key=lambda x: x.total_score, reverse=True)
    logger.info("--- STAGE: PIPELINE | Ranking complete ---")
    return sorted_results

def evaluate_config(config: BOMConfiguration, p: UserPreferences) -> RankedBOM:
    comps = list(config.values())
    n = len(comps)
    if n == 0:
        return RankedBOM(config, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    unique_suppliers = len(set(c.supplier_name for c in comps))
    cons_score = (n - unique_suppliers) / (n - 1) if n > 1 else 1.0

    avg_p = sum(c.price_scaled for c in comps) / n
    avg_q = sum(c.quality for c in comps) / n
    avg_r = sum(c.resilience_score for c in comps) / n
    avg_s = sum(c.esg_score for c in comps) / n
    avg_e = sum(c.ethics_score for c in comps) / n
    avg_l = sum(c.lead_time_score for c in comps) / n

    dims = [
        (p.price, avg_p), (p.quality, avg_q), (p.resilience, avg_r),
        (p.sustainability, avg_s), (p.ethics, avg_e), (p.lead_time, avg_l),
        (p.consolidation, cons_score)
    ]

    total_weight = sum(w for w, _ in dims)
    final_score = sum(w * v for w, v in dims) / total_weight if total_weight > 0 else 0.0

    return RankedBOM(
        config, final_score, avg_p, avg_q, avg_r, avg_s, avg_e, avg_l, 
        cons_score, unique_suppliers
    )
