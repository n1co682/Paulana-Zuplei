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

import sqlite3
from typing import List, Dict
from dataclasses import dataclass, field

def get_filtered_replacements(db_path: str, bom: BillOfMaterials):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    replacement_map = {}

    for entry in bom:
        # 1. Query by Equivalence Class (The "Sugar" vs "Flour" logic)
        query = "SELECT * FROM Supplier_Product WHERE Equivalence_Class = ?"
        cursor.execute(query, (entry.equivalence_class,))
        rows = cursor.fetchall()

        valid_options = []
        
        for row in rows:
            # 2. Database format handling
            # Parsing "Vegan, Organic" -> ["Vegan", "Organic"]
            db_certs = [c.strip() for c in row['Certificates'].split(',')] if row['Certificates'] else []
            db_allergens = [a.strip() for a in row['Allergens'].split(',')] if row['Allergens'] else []

            # 3. Apply your filter logic
            # Must have ALL required certs
            meets_certs = all(cert in db_certs for cert in entry.required_certs)
            # Must have ZERO forbidden allergens
            no_allergens = not any(alg in db_allergens for alg in entry.forbidden_allergens)

            if meets_certs and no_allergens:
                try:
                    # 4. Hydrate the ComponentFromSupplier class
                    # Note: Normalizing Quality to 0-1 range to satisfy the class setter
                    comp = ComponentFromSupplier(
                        price_per_unit=row['Price'],
                        price_scaled=row.get('Price_Scaled', 0.0), 
                        quality=row['Quality'] / 5.0,     
                        quality_report=row.get('Quality_Report', "N/A"),
                        production_place=row.get('Production_Place', "Unknown"),
                        resilience_score=row.get('Resilience_Score', 0.5),
                        ethics_score=row.get('Ethics_Score', 0.5),
                        ethics_report=row.get('Ethics_Report', "N/A"),
                        esg_score=row.get('ESG_Score', 0.5),
                        certificates=db_certs,
                        allergents=db_allergens,
                        lead_time=row.get('Lead_Time', 0.0),
                        lead_time_score=row.get('Lead_Time_Score', 0.5),
                        equivalence_class=row['Equivalence_Class']
                    )
                    valid_options.append(comp)
                except ValueError as e:
                    # This catches validation errors (e.g., if a score in the DB is > 1.0)
                    print(f"Skipping row {row.get('Id')} due to validation error: {e}")

        replacement_map[entry] = valid_options

    conn.close()
    return replacement_map


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