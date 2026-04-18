import itertools
from typing import List, Dict
from models import (BillOfMaterials, UserPreferences, RankedBOM, 
                    BOMConfiguration, ReplacementMap)
from component_from_supplier import ComponentFromSupplier

def find_replacements(bom: BillOfMaterials, db: List[ComponentFromSupplier]) -> ReplacementMap:
    result: ReplacementMap = {}
    for entry in bom:
        result[entry] = [
            c for c in db if c.equivalence_class == entry.equivalence_class
            and all(cert in c.certificates for cert in entry.required_certs)
            and not any(alg in c.allergents for alg in entry.forbidden_allergens)
        ]
    return result

def rank_configurations(replacements: ReplacementMap, prefs: UserPreferences) -> List[RankedBOM]:
    entries = list(replacements.keys())
    candidate_lists = [replacements[e] for e in entries]
    results = [evaluate_config(dict(zip(entries, combo)), prefs) 
               for combo in itertools.product(*candidate_lists)]
    return sorted(results, key=lambda x: x.total_score, reverse=True)

def evaluate_config(config: BOMConfiguration, p: UserPreferences) -> RankedBOM:
    comps = list(config.values())
    n = len(comps)
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