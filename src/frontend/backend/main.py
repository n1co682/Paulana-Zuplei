import logging
import os
from pathlib import Path
from typing import Optional

import httpx
import fastapi
import fastapi.middleware.cors
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from transforms import (
    best_improvement,
    classify,
    dollars_to_str,
    esg_to_letter,
    hours_to_days_str,
    parse_quality,
    quality_to_grade,
    to_five,
    to_rate,
    vectors_to_prefs,
)

logger = logging.getLogger("frontend")
logging.basicConfig(level=logging.INFO)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

app = fastapi.FastAPI()

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

analysis_data: dict = {}
applied_recommendations: set = set()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def start_page(request: Request):
    bom_items = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{BACKEND_URL}/bom")
            resp.raise_for_status()
            bom_items = resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch BOM from backend: {e}")

    # De-duplicate: keep first row per component_id (one row per supplier in the JOIN)
    seen: dict = {}
    for item in bom_items:
        if item["component_id"] not in seen:
            seen[item["component_id"]] = item
    bom_items = list(seen.values())

    return templates.TemplateResponse(
        request=request,
        name="start.html",
        context={"request": request, "bom_items": bom_items},
    )


@app.post("/analyze")
async def analyze_sourcing(
    request: Request,
    materials: str = Form(""),
    compliance: str = Form("FDA / GRAS Standard"),
    bom_items: list[str] = Form([]),
    vector_price: float = Form(0.7),
    vector_quality: float = Form(0.6),
    vector_resilience: float = Form(0.5),
    vector_sustainability: float = Form(0.8),
    vector_ethics: float = Form(0.65),
    vector_leadtime: float = Form(0.55),
):
    analysis_id = "latest"

    # Fetch full BOM for current-supplier context
    bom_items_full = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{BACKEND_URL}/bom")
            resp.raise_for_status()
            bom_items_full = resp.json()
        except Exception as e:
            logger.error(f"BOM pre-fetch failed: {e}")
    bom_lookup = {entry["component_id"]: entry for entry in bom_items_full}

    payload = {
        "selected_component_ids": bom_items,
        "preferences": vectors_to_prefs(
            vector_price, vector_quality, vector_resilience,
            vector_sustainability, vector_ethics, vector_leadtime,
        ),
    }

    replacements_raw: dict = {}
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            resp = await client.post(f"{BACKEND_URL}/replacements", json=payload)
            resp.raise_for_status()
            replacements_raw = resp.json()
        except Exception as e:
            logger.error(f"Replacements call failed: {e}")

    critical_items = []
    optimization_items = []
    comparisons = []

    for comp_id, result in replacements_raw.items():
        bom_entry = bom_lookup.get(comp_id, {})
        candidates = result.get("candidates", [])
        if not candidates:
            continue

        top = candidates[0]
        top_comp = top.get("component", {})
        component_name = result.get("component_name", comp_id)
        current_supplier_name = bom_entry.get("supplier_name") or "Current Supplier"
        improvement_str = best_improvement(bom_entry, top_comp, top.get("total_score", 0.0))
        category = classify(bom_entry, top)

        item = {
            "id": comp_id,
            "type": "Supplier Change",
            "ingredient": component_name,
            "current": current_supplier_name,
            "recommended": top_comp.get("supplier_name", "—"),
            "improvement": improvement_str,
            "considerations": result.get("reasoning", "See full report for details."),
        }

        if category == "critical":
            critical_items.append(item)
        else:
            optimization_items.append(item)

        # Build current supplier profile from BOM entry
        cur_price_raw = float(bom_entry.get("price") or 0.0)
        cur_quality = parse_quality(bom_entry.get("quality"))
        cur_esg = bom_entry.get("esg_score") or 50
        cur_lead = bom_entry.get("lead_time")

        current_profile = {
            "name": current_supplier_name,
            "price": dollars_to_str(cur_price_raw),
            "quality_rate": to_rate(cur_quality),
            "location": bom_entry.get("production_place") or "Unknown",
            "resilience_score": 2.5,
            "ethics_score": to_five(float(cur_esg) / 100.0),
            "esg_rating": esg_to_letter(cur_esg),
            "certificates": bom_entry.get("certificates") or [],
            "lead_time": hours_to_days_str(cur_lead),
            "grade": quality_to_grade(cur_quality),
        }

        recommended_profile = {
            "name": top_comp.get("supplier_name", "—"),
            "price": dollars_to_str(top_comp.get("price_per_unit") or 0.0),
            "quality_rate": to_rate(top_comp.get("quality") or 0.5),
            "location": top_comp.get("production_place") or "Unknown",
            "resilience_score": to_five(top_comp.get("resilience_score") or 0.5),
            "ethics_score": to_five(top_comp.get("ethics_score") or 0.5),
            "esg_rating": esg_to_letter(top_comp.get("esg_score") or 0.5),
            "certificates": top_comp.get("certificates") or [],
            "lead_time": hours_to_days_str(top_comp.get("lead_time")),
            "grade": quality_to_grade(top_comp.get("quality") or 0.5),
        }

        comparisons.append({
            "comp_id": comp_id,
            "ingredient": component_name,
            "current_supplier": current_profile,
            "recommended_supplier": recommended_profile,
        })

    analysis_data[analysis_id] = {
        "materials": materials,
        "compliance": compliance,
        "bom_items": bom_items,
        "critical_items": critical_items,
        "optimization_items": optimization_items,
        "comparisons": comparisons,
        "backend_error": None if replacements_raw else "Backend analysis returned no results.",
    }

    return RedirectResponse(url="/results/analysis", status_code=303)


@app.get("/results/analysis", response_class=HTMLResponse)
async def sourcing_analysis(request: Request):
    analysis_id = "latest"
    data = analysis_data.get(analysis_id, {})

    critical_items = []
    for item in data.get("critical_items", []):
        item_copy = item.copy()
        item_copy["applied"] = item["id"] in applied_recommendations
        critical_items.append(item_copy)

    optimization_items = []
    for item in data.get("optimization_items", []):
        item_copy = item.copy()
        item_copy["applied"] = item["id"] in applied_recommendations
        optimization_items.append(item_copy)

    return templates.TemplateResponse(
        request=request,
        name="analysis.html",
        context={
            "request": request,
            "critical_items": critical_items,
            "optimization_items": optimization_items,
            "backend_error": data.get("backend_error"),
        },
    )


@app.get("/results/comparison", response_class=HTMLResponse)
async def ingredient_comparison(request: Request, id: Optional[str] = None):
    analysis_id = "latest"
    data = analysis_data.get(analysis_id, {})
    comparisons = data.get("comparisons", [])

    comparison = None
    if id and comparisons:
        for c in comparisons:
            if c.get("comp_id") == id:
                comparison = c
                break
    if comparison is None and comparisons:
        comparison = comparisons[0]

    return templates.TemplateResponse(
        request=request,
        name="comparison.html",
        context={"request": request, "comparison": comparison},
    )


@app.post("/api/apply-recommendation")
async def apply_recommendation(request: Request):
    body = await request.json()
    recommendation_id = body.get("recommendation_id", "")
    if recommendation_id:
        applied_recommendations.add(recommendation_id)
    return {"status": "success", "message": "Recommendation applied successfully"}
