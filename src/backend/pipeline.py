from models import (BillOfMaterials, ReplacementMap, RankedMap,
                    UserPreferences, RankedOption)
from component_from_supplier import ComponentFromSupplier
from typing import List

def find_replacements(
    bom: BillOfMaterials,
    supplier_db: List[ComponentFromSupplier],
) -> ReplacementMap:
    result: ReplacementMap = {}
    for entry in bom:
        result[entry] = [
            c for c in supplier_db
            if c.equivalence_class == entry.equivalence_class
            and all(cert in c.certificates for cert in entry.required_certs)
            and not any(alg in c.allergents for alg in entry.forbidden_allergens)
        ]
    return result


def rank_replacements(
    replacements: ReplacementMap,
    preferences: UserPreferences,
) -> RankedMap:
    return {
        entry: sorted(
            [RankedOption(c, _score(c, preferences)) for c in candidates],
            key=lambda o: o.score,
            reverse=True,
        )
        for entry, candidates in replacements.items()
    }


def _score(c: ComponentFromSupplier, p: UserPreferences) -> float:
    """Weighted average of normalised per-dimension scores."""
    dims = [
        (p.price,          c.price_scaled),
        (p.quality,        c.quality),
        (p.resilience,     c.resilience_score),
        (p.sustainability, c.esg_score),
        (p.ethics,         c.ethics_score),
        (p.lead_time,      c.lead_time_score),
    ]
    total_weight = sum(weight for weight, _ in dims)
    if total_weight == 0:
        return 0.0
    return sum(weight * value for weight, value in dims) / total_weight