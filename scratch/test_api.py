import httpx
import json

def test_agnes_api():
    base_url = "http://localhost:8000"
    
    # 1. Test /bom
    print("\n--- Testing /bom ---")
    response = httpx.get(f"{base_url}/bom")
    if response.status_code == 200:
        bom = response.json()
        print(f"BOM fetched successfully. Total components: {len(bom)}")
        for i, item in enumerate(bom[:3]):
            print(f"  [{i}] {item['component_id']}: {item['component_name']} (Eq: {item['equivalence_class']}, Supplier: {item['supplier_name']})")
            print(f"      Location: {item['production_place']}, Price: {item['price']}, Quality: {item['quality']}")
            
        # Select first component for replacement test
        selected_ids = [bom[0]['component_id']]
        
        # 2. Test /replacements
        print("\n--- Testing /replacements ---")
        payload = {
            "selected_component_ids": selected_ids,
            "preferences": {
                "price": 3,
                "quality": 7,
                "resilience": 5,
                "sustainability": 5,
                "ethics": 8,
                "lead_time": 4,
                "consolidation": 6
            }
        }
        
        # This might take a while due to LLM calls
        print(f"Requesting replacements for: {selected_ids}...")
        response = httpx.post(f"{base_url}/replacements", json=payload, timeout=120.0)
        
        if response.status_code == 200:
            results = response.json()
            for comp_id, data in results.items():
                print(f"\nResults for {data['component_name']} ({comp_id}):")
                print(f"Reasoning: {data['reasoning']}")
                print("Top Candidates:")
                for i, cand in enumerate(data['candidates'], 1):
                    # print(json.dumps(cand, indent=2)) # Debug
                    comp = cand.get('component', {})
                    # Handle the fact that some fields might be prefixed with _ due to setters/getters
                    s_name = comp.get('supplier_name') or comp.get('_supplier_name', 'Unknown')
                    print(f"  {i}. {s_name} - Score: {cand['total_score']:.3f}")
                    p_place = comp.get('production_place') or comp.get('_production_place', 'Unknown')
                    print(f"     Location: {p_place}, Consolidation Score: {cand['c_score']}")
        else:
            print(f"Replacements failed: {response.status_code} - {response.text}")
    else:
        print(f"BOM fetch failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_agnes_api()
