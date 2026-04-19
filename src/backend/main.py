import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline import rank_individual_candidates
from models import UserPreferences, Component as AgnesComponent
from component_from_supplier import ComponentFromSupplier
from agent import AgnesAgent, db
from tools import generate_replacement_reasoning

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agnes.main")

app = FastAPI(title="Agnes AI Supply Chain Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def ranked_option_to_dict(ro) -> dict:
    """Explicitly serialize RankedOption + ComponentFromSupplier (avoids _private attribute keys)."""
    c = ro.component
    return {
        "total_score": ro.total_score,
        "p_score": ro.p_score,
        "q_score": ro.q_score,
        "r_score": ro.r_score,
        "s_score": ro.s_score,
        "e_score": ro.e_score,
        "l_score": ro.l_score,
        "c_score": ro.c_score,
        "component": {
            "supplier_name": c.supplier_name,
            "price_per_unit": c.price_per_unit,
            "price_scaled": c.price_scaled,
            "quality": c.quality,
            "quality_report": c.quality_report,
            "production_place": c.production_place,
            "resilience_score": c.resilience_score,
            "ethics_score": c.ethics_score,
            "ethics_report": c.ethics_report,
            "esg_score": c.esg_score,
            "certificates": c.certificates,
            "allergents": c.allergents,
            "lead_time": c.lead_time,
            "lead_time_score": c.lead_time_score,
            "equivalence_class": c.equivalence_class,
        },
    }


class ReplacementRequest(BaseModel):
    selected_component_ids: List[str]
    preferences: UserPreferences

def agnes_to_pipeline_model(agnes_comp: AgnesComponent) -> ComponentFromSupplier:
    """Bridge: Convert Agnes Component model to Team's Pipeline model."""
    supp = db.get_supplier(agnes_comp.supplier_id)
    return ComponentFromSupplier(
        supplier_name=supp.name if supp else "Unknown",
        price_per_unit=agnes_comp.price_per_unit / 100.0 if agnes_comp.price_per_unit else 1.0,
        price_scaled=0.5, 
        quality=agnes_comp.quality or 0.5,
        quality_report=agnes_comp.text or "Enriched by Agnes",
        production_place=agnes_comp.production_place or "Global",
        resilience_score=0.7,
        ethics_score=(supp.esg_score / 100.0) if (supp and supp.esg_score) else 0.5,
        ethics_report=supp.ethics if (supp and supp.ethics) else "N/A",
        esg_score=(supp.esg_score / 100.0) if (supp and supp.esg_score) else 0.5,
        certificates=agnes_comp.certificates,
        allergents=agnes_comp.allergens,
        lead_time=float(agnes_comp.lead_time) if agnes_comp.lead_time else 72.0,
        lead_time_score=0.6,
        equivalence_class=agnes_comp.equivalence_class
    )

@app.get("/bom")
def get_bom():
    """Fetch current BOM for product_id=1."""
    product_id = 1
    logger.info(f"Fetching detailed BOM for product {product_id}")
    try:
        bom = db.get_bom_detailed(product_id)
        return bom
    except Exception as e:
        logger.error(f"Error fetching BOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/replacements")
def search_replacements(req: ReplacementRequest):
    """Search replacements for selected components and return top 3 with reasoning."""
    product_id = 1
    logger.info(f"Processing replacement search for components: {req.selected_component_ids}")
    
    try:
        full_bom = db.get_bom_detailed(product_id)
        bom_lookup = {b['component_id']: b for b in full_bom}
        
        results = {}
        for comp_id in req.selected_component_ids:
            if comp_id not in bom_lookup:
                logger.warning(f"Component {comp_id} not found in BOM")
                continue
                
            comp_info = bom_lookup[comp_id]
            eq_class = comp_info['equivalence_class']
            
            # Run Agnes Agent to get/enrich candidates
            agent = AgnesAgent(eq_class)
            agnes_pool = agent.run()
            
            # Convert to pipeline models
            candidates = [agnes_to_pipeline_model(ac) for ac in agnes_pool]
            
            # Identify "rest of BOM" for consolidation scoring
            rest_of_bom = [b for b in full_bom if b['component_id'] != comp_id]
            
            # Rank individual candidates
            ranked_options = rank_individual_candidates(candidates, rest_of_bom, req.preferences)
            
            # Get top 3
            top_3 = ranked_options[:3]
            
            # Prepare data for reasoning tool
            top_3_dicts = []
            for r in top_3:
                c = r.component
                top_3_dicts.append({
                    "supplier_name": c.supplier_name,
                    "total_score": r.total_score,
                    "p_score": r.p_score,
                    "q_score": r.q_score,
                    "r_score": r.r_score,
                    "c_score": r.c_score,
                    "production_place": c.production_place,
                    "quality_report": c.quality_report
                })
                
            reasoning = generate_replacement_reasoning(comp_info['component_name'], top_3_dicts, rest_of_bom)
            
            results[comp_id] = {
                "component_name": comp_info['component_name'],
                "candidates": [ranked_option_to_dict(r) for r in top_3],
                "reasoning": reasoning
            }
            
        return results
    except Exception as e:
        logger.error(f"Error searching replacements: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)