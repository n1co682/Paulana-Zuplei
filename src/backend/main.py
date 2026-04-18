from pipeline import find_replacements, rank_replacements
from models import BOMEntry, UserPreferences
from component_from_supplier import ComponentFromSupplier

# ── Supplier database ──────────────────────────────────────────────────────────
# Each entry is one component offered by a supplier.
# Scores are 0.0–1.0. price_scaled: lower price → higher score.

supplier_db = [
    # ── Resistors (equivalence class "R_10K_0805") ────────────────────────────
    ComponentFromSupplier(
        price_per_unit=0.05, price_scaled=0.95,
        quality=0.90, quality_report="IPC-A-610 Class 2 compliant",
        production_place="Germany",
        resilience_score=0.85, ethics_score=0.88, ethics_report="Fair wage certified, no violations on record", esg_score=0.80,
        certificates=["RoHS", "REACH", "ISO9001"],
        allergents=[],
        lead_time=7.0, lead_time_score=0.90,
        equivalence_class="R_10K_0805",
    ),
    ComponentFromSupplier(
        price_per_unit=0.02, price_scaled=0.99,
        quality=0.65, quality_report="Basic QC only",
        production_place="China",
        resilience_score=0.40, ethics_score=0.35, ethics_report="No third-party audit available",esg_score=0.30,
        certificates=["RoHS"],
        allergents=[],
        lead_time=45.0, lead_time_score=0.20,
        equivalence_class="R_10K_0805",
    ),
    ComponentFromSupplier(
        price_per_unit=0.08, price_scaled=0.88,
        quality=0.95, quality_report="AEC-Q200 automotive grade",
        production_place="Japan",
        resilience_score=0.92, ethics_score=0.80, ethics_report="Audited annually, meets EICC standards", esg_score=0.85,
        certificates=["RoHS", "REACH", "ISO9001", "AEC-Q200"],
        allergents=[],
        lead_time=14.0, lead_time_score=0.75,
        equivalence_class="R_10K_0805",
    ),

    # ── Capacitors (equivalence class "C_100N_0603") ──────────────────────────
    ComponentFromSupplier(
        price_per_unit=0.03, price_scaled=0.97,
        quality=0.78, quality_report="Standard SMD, meets spec",
        production_place="Taiwan",
        resilience_score=0.70, ethics_score=0.65, ethics_report="Self-reported, no independent audit", esg_score=0.60,
        certificates=["RoHS", "REACH"],
        allergents=[],
        lead_time=21.0, lead_time_score=0.55,
        equivalence_class="C_100N_0603",
    ),
    ComponentFromSupplier(
        price_per_unit=0.06, price_scaled=0.92,
        quality=0.88, quality_report="Low ESR, high temp rated",
        production_place="Germany",
        resilience_score=0.82, ethics_score=0.85, ethics_report="SA8000 certified, annual third-party audit", esg_score=0.78,
        certificates=["RoHS", "REACH", "ISO9001"],
        allergents=[],
        lead_time=10.0, lead_time_score=0.85,
        equivalence_class="C_100N_0603",
    ),

    # ── MCU (equivalence class "MCU_ARM_M0") ──────────────────────────────────
    ComponentFromSupplier(
        price_per_unit=1.20, price_scaled=0.70,
        quality=0.92, quality_report="STM32G0 series, production tested",
        production_place="France",
        resilience_score=0.75, ethics_score=0.80, ethics_report="EU supply chain due diligence compliant", esg_score=0.72,
        certificates=["RoHS", "REACH", "ISO9001"],
        allergents=[],
        lead_time=28.0, lead_time_score=0.45,
        equivalence_class="MCU_ARM_M0",
    ),
    ComponentFromSupplier(
        price_per_unit=0.95, price_scaled=0.78,
        quality=0.88, quality_report="RP2040, community-verified",
        production_place="UK",
        resilience_score=0.60, ethics_score=0.75, ethics_report="Conflict minerals policy in place", esg_score=0.65,
        certificates=["RoHS", "REACH"],
        allergents=[],
        lead_time=14.0, lead_time_score=0.72,
        equivalence_class="MCU_ARM_M0",
    ),
    # Disqualified for RoHS-required BOM entries — included to test filtering
    ComponentFromSupplier(
        price_per_unit=0.80, price_scaled=0.85,
        quality=0.80, quality_report="GD32E230, basic testing",
        production_place="China",
        resilience_score=0.45, ethics_score=0.30, ethics_report="No audit conducted", esg_score=0.28,
        certificates=["REACH"],          # missing RoHS → filtered out when required
        allergents=[],
        lead_time=60.0, lead_time_score=0.10,
        equivalence_class="MCU_ARM_M0",
    ),
]

# ── Bill of Materials ──────────────────────────────────────────────────────────
# Each BOMEntry describes one line item and its constraints.

bom = [
    BOMEntry(
        component_id="R1",
        equivalence_class="R_10K_0805",
        required_certs=("RoHS", "REACH"),   # must have both
        forbidden_allergens=(),
    ),
    BOMEntry(
        component_id="C3",
        equivalence_class="C_100N_0603",
        required_certs=("RoHS",),
        forbidden_allergens=(),
    ),
    BOMEntry(
        component_id="U1",
        equivalence_class="MCU_ARM_M0",
        required_certs=("RoHS",),           # filters out the GD32 entry above
        forbidden_allergens=(),
    ),
]

# ── User preferences ───────────────────────────────────────────────────────────
# 0 = ignore dimension, 1 = low priority, 5 = highest priority.

prefs = UserPreferences(
    price=2,
    quality=5,
    resilience=3,
    sustainability=4,
    ethics=3,
    lead_time=1,
)

# ── Run pipeline ───────────────────────────────────────────────────────────────

replacements = find_replacements(bom, supplier_db)
ranked       = rank_replacements(replacements, prefs)

# ── Print results ──────────────────────────────────────────────────────────────

DIM_WIDTH  = 7   # column width for dimension scores
SCORE_PAD  = 55  # chars before dimension columns start

header_dims = f"{'price':>{DIM_WIDTH}} {'qual':>{DIM_WIDTH}} {'resil':>{DIM_WIDTH}} {'sust':>{DIM_WIDTH}} {'eth':>{DIM_WIDTH}} {'lead':>{DIM_WIDTH}}"

for entry, options in ranked.items():
    print(f"\n{'─' * 72}")
    print(f"  BOM entry : {entry.component_id}  [{entry.equivalence_class}]")
    print(f"  Required  : certs={list(entry.required_certs)}  allergens blocked={list(entry.forbidden_allergens)}")
    print(f"  Candidates: {len(options)} found\n")
    print(f"  {'#':<3} {'Origin':<14} {'Score':>6}  {header_dims}")
    print(f"  {'─'*3} {'─'*14} {'─'*6}  {'─'*DIM_WIDTH} {'─'*DIM_WIDTH} {'─'*DIM_WIDTH} {'─'*DIM_WIDTH} {'─'*DIM_WIDTH} {'─'*DIM_WIDTH}")

    for rank, opt in enumerate(options, 1):
        c = opt.component
        dims = (f"{c.price_scaled:>{DIM_WIDTH}.2f} {c.quality:>{DIM_WIDTH}.2f} "
                f"{c.resilience_score:>{DIM_WIDTH}.2f} {c.esg_score:>{DIM_WIDTH}.2f} "
                f"{c.ethics_score:>{DIM_WIDTH}.2f} {c.lead_time_score:>{DIM_WIDTH}.2f}")
        print(f"  {rank:<3} {c.production_place:<14} {opt.score:>6.3f}  {dims}")

print(f"\n{'─' * 72}")
print("\nPreferences used:")
for field, val in vars(prefs).items():
    bar = "★" * val + "☆" * (5 - val)
    print(f"  {field:<14} {bar}  ({val}/5)")
