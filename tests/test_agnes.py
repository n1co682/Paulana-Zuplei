import json
from src.backend.agent import AgnesAgent, make_decision
from src.backend.database_mock import db
from src.backend.models import Supplier, Component

def test_agnes_workflow():
    print("Initializing test data...")
    # Add one existing supplier/component to DB
    s1 = Supplier(name="AlphaVitamins")
    db.add_supplier(s1)
    c1 = Component(
        name="Vitamin C Powder",
        equivalence_class="vitamins",
        supplier_id=s1.id,
        quality=9,
        certificates=["Organic"]
    )
    db.add_component(c1)

    # Run Agnes for "vitamins"
    agent = AgnesAgent(equivalence_class="vitamins")
    results = agent.run()

    print("\n--- Final Results Pool ---")
    for comp in results:
        supp = db.get_supplier(comp.supplier_id)
        print(f"Supplier: {supp.name} | Production: {supp.production_place}")
        print(f"  Component: {comp.name} | Price: {comp.price_per_unit} | Lead Time: {comp.lead_time}h")
        print(f"  Quality: {comp.quality}/10 | Certs: {comp.certificates}")
        print(f"  Ethics: {supp.ethics[:100]}...")
        print("-" * 30)

    # Mock decision
    best = make_decision(results)
    if best:
        print(f"\nRecommended Solution: {best.name} from {db.get_supplier(best.supplier_id).name}")

if __name__ == "__main__":
    test_agnes_workflow()
