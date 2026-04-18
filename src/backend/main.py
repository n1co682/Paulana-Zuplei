from pipeline import find_replacements, rank_configurations, evaluate_config
from models import BOMEntry, UserPreferences
from component_from_supplier import ComponentFromSupplier

# ── Expanded Data Setup ───────────────────────────────────────────────────────
# Data Schema: (Name, Price, Qual, Resil, Rpt, Country, Sust, Eth, Rpt, LeadScore, Certs, Issues, LeadDays, Cap, Class)

db = [
    # --- Resistors (R_10K) ---
    ComponentFromSupplier("GlobalCorp", 0.08, 0.88, 0.95, "Rpt", "DE", 0.9, 0.9, "Rpt", 0.9, ["RoHS"], [], 7, 0.9, "R_10K"),
    ComponentFromSupplier("FastChips",  0.02, 0.70, 0.65, "Rpt", "CN", 0.4, 0.3, "Rpt", 0.3, ["RoHS"], [], 5, 0.95, "R_10K"),
    ComponentFromSupplier("NipponComp", 0.12, 0.98, 0.99, "Rpt", "JP", 0.8, 0.9, "Rpt", 0.9, ["RoHS", "Reach"], [], 10, 0.85, "R_10K"),

    # --- Microcontrollers (MCU_ARM) ---
    ComponentFromSupplier("GlobalCorp", 1.20, 0.85, 0.92, "Rpt", "FR", 0.8, 0.8, "Rpt", 0.7, ["RoHS"], [], 28, 0.4, "MCU_ARM"),
    ComponentFromSupplier("SpecUK",     0.95, 0.78, 0.88, "Rpt", "UK", 0.6, 0.7, "Rpt", 0.6, ["RoHS"], [], 14, 0.7, "MCU_ARM"),
    ComponentFromSupplier("NipponComp", 1.50, 0.99, 0.95, "Rpt", "JP", 0.9, 0.9, "Rpt", 0.8, ["RoHS"], [], 21, 0.6, "MCU_ARM"),

    # --- Capacitors (C_100nF) ---
    ComponentFromSupplier("FastChips",  0.01, 0.60, 0.50, "Rpt", "CN", 0.3, 0.2, "Rpt", 0.4, ["RoHS"], [], 3, 0.99, "C_100nF"),
    ComponentFromSupplier("GlobalCorp", 0.05, 0.90, 0.90, "Rpt", "DE", 0.8, 0.8, "Rpt", 0.8, ["RoHS"], [], 7, 0.9, "C_100nF"),
    ComponentFromSupplier("EuroLogis",  0.06, 0.85, 0.92, "Rpt", "NL", 0.8, 0.9, "Rpt", 0.9, ["RoHS"], [], 5, 0.8, "C_100nF"),

    # --- Voltage Regulators (LDO_3V3) ---
    ComponentFromSupplier("SpecUK",     0.45, 0.82, 0.80, "Rpt", "UK", 0.7, 0.8, "Rpt", 0.7, ["RoHS"], [], 10, 0.7, "LDO_3V3"),
    ComponentFromSupplier("GlobalCorp", 0.55, 0.88, 0.90, "Rpt", "DE", 0.8, 0.8, "Rpt", 0.8, ["RoHS"], [], 12, 0.8, "LDO_3V3"),
    ComponentFromSupplier("FastChips",  0.30, 0.65, 0.55, "Rpt", "CN", 0.4, 0.3, "Rpt", 0.4, ["RoHS"], [], 6, 0.9, "LDO_3V3"),

    # --- Connectors (USB_C) ---
    ComponentFromSupplier("EuroLogis",  0.75, 0.90, 0.85, "Rpt", "NL", 0.8, 0.9, "Rpt", 0.8, ["RoHS"], [], 14, 0.6, "USB_C"),
    ComponentFromSupplier("NipponComp", 0.90, 0.96, 0.92, "Rpt", "JP", 0.8, 0.8, "Rpt", 0.8, ["RoHS"], [], 20, 0.5, "USB_C"),
]

# A more complex BOM representing a small IoT device
bom = [
    BOMEntry("R1", "R_10K", ("RoHS",)),
    BOMEntry("R2", "R_10K", ("RoHS",)),
    BOMEntry("C1", "C_100nF", ("RoHS",)),
    BOMEntry("U1", "MCU_ARM", ("RoHS",)),
    BOMEntry("U2", "LDO_3V3", ("RoHS",)),
    BOMEntry("J1", "USB_C", ("RoHS",))
]

# Heavily favoring Quality and Consolidation (fewer suppliers)
prefs = UserPreferences(price=2, quality=8, consolidation=7)

# ── Analysis ──────────────────────────────────────────────────────────────────

# Define a "Legacy" selection using mostly FastChips and SpecUK
old_selection = {
    bom[0]: next(c for c in db if c.supplier_name == "FastChips" and c.equivalence_class == "R_10K"),
    bom[1]: next(c for c in db if c.supplier_name == "FastChips" and c.equivalence_class == "R_10K"),
    bom[2]: next(c for c in db if c.supplier_name == "FastChips" and c.equivalence_class == "C_100nF"),
    bom[3]: next(c for c in db if c.supplier_name == "SpecUK" and c.equivalence_class == "MCU_ARM"),
    bom[4]: next(c for c in db if c.supplier_name == "SpecUK" and c.equivalence_class == "LDO_3V3"),
    bom[5]: next(c for c in db if c.supplier_name == "EuroLogis" and c.equivalence_class == "USB_C"),
}

old_bom_ranked = evaluate_config(old_selection, prefs)

# Find all better alternatives
replacements = find_replacements(bom, db)
all_ranked = rank_configurations(replacements, prefs)
better_alternatives = [b for b in all_ranked if b.total_score > old_bom_ranked.total_score]

# ── Printing ──────────────────────────────────────────────────────────────────

def print_bom_table_row(label, rb, width=6):
    dims = (f"{rb.p_score:>{width}.2f} {rb.q_score:>{width}.2f} {rb.r_score:>{width}.2f} "
            f"{rb.s_score:>{width}.2f} {rb.e_score:>{width}.2f} {rb.l_score:>{width}.2f} {rb.c_score:>{width}.2f}")
    print(f"{label:<13} {rb.total_score:<7.3f} | {dims} | {rb.unique_suppliers:>10} unique")

W = 6
print(f"\n{'='*110}")
print(f"{'EXPANDED BOM PERFORMANCE COMPARISON':^110}")
print(f"{'='*110}")
header = (f"{'Configuration':<13} {'Score':<7} | {'Price':>{W}} {'Qual':>{W}} {'Resil':>{W}} "
          f"{'Sust':>{W}} {'Eth':>{W}} {'Lead':>{W}} {'Cons':>{W}} | {'Suppliers':>10}")
print(header)
print("-" * 110)

print_bom_table_row("OLD BOM", old_bom_ranked)
print("-" * 110)

if not better_alternatives:
    print("  (No better configurations found with current preferences)")
else:
    # Print top 5 better options to avoid flooding the console
    for i, alt in enumerate(better_alternatives[:5], 1):
        print_bom_table_row(f"Better #{i}", alt)

print(f"{'='*110}\n")

if better_alternatives:
    top = better_alternatives[0]
    print(f"RECOMMENDED OPTIMIZATION (Top Ranked Alternative):")
    for entry, comp in top.configuration.items():
        old_comp = old_selection[entry]
        status = "✓ [KEEP]" if old_comp.supplier_name == comp.supplier_name else f"→ [SWAP: {old_comp.supplier_name}]"
        print(f"  • {entry.component_id} ({entry.equivalence_class}): {comp.supplier_name:<15} {status}")