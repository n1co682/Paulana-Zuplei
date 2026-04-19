import os
from pathlib import Path
from typing import Optional

import fastapi
import fastapi.middleware.cors
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = fastapi.FastAPI()

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates directory
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# In-memory storage for demo purposes
# In production, this would be a database
analysis_data = {}
applied_recommendations = set()  # Track applied recommendation IDs


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def start_page(request: Request):
    """Render the start/input page"""
    return templates.TemplateResponse(
        request=request,
        name="start.html",
        context={"request": request}
    )


@app.post("/analyze")
async def analyze_sourcing(
    request: Request,
    materials: str = Form(""),
    compliance: str = Form("FDA / GRAS Standard"),
    bom_items: list[str] = Form([]),
):
    """
    Process the input data and redirect to results.
    In production, this would call your actual backend analysis service.
    """
    # Store the input data (simulating backend processing)
    analysis_id = "latest"
    
    # Simulate backend processing - in production, replace with actual API calls
    analysis_data[analysis_id] = {
        "materials": materials,
        "compliance": compliance,
        "bom_items": bom_items,
        # Simulated analysis results
        "critical_items": [
            {
                "type": "Supplier Change",
                "ingredient": "Sodium Benzoate",
                "current": "Apex Materials",
                "recommended": "NovaSil Industries",
                "improvement": "-10 days Lead Time",
                "considerations": "Requires new quality audit prior to onboarding."
            }
        ],
        "optimization_items": [
            {
                "type": "Product Replacement",
                "ingredient": "Texturizing Agent X",
                "current": "Guar Gum Standard",
                "recommended": "CelluTech Premium",
                "improvement": "+15% Price Efficiency",
                "considerations": "Slightly higher allergen risk profile. Review required."
            }
        ],
        "comparisons": [
            {
                "ingredient": "Industrial Grade Silicon",
                "current_supplier": {
                    "name": "GlobalTech Materials",
                    "price": "$14.50",
                    "scaled_price": "$142,000 / mo",
                    "quality_rate": 92,
                    "location": "Shenzhen, Guangdong, CN",
                    "resilience_score": 2.5,
                    "ethics_score": 3.0,
                    "esg_rating": "B-",
                    "certificates": ["ISO 9001"],
                    "lead_time": "45 Days",
                    "grade": "Grade B"
                },
                "recommended_supplier": {
                    "name": "Nordic Silicon AB",
                    "price": "$15.10",
                    "scaled_price": "$148,000 / mo",
                    "quality_rate": 99,
                    "location": "Malmö, Skåne, SE",
                    "resilience_score": 4.8,
                    "ethics_score": 4.9,
                    "esg_rating": "A+",
                    "certificates": ["Carbon Neutral", "Fair Trade"],
                    "lead_time": "14 Days",
                    "grade": "Grade A"
                }
            }
        ]
    }
    
    # Redirect to results page
    return RedirectResponse(url="/results/analysis", status_code=303)


@app.get("/results/analysis", response_class=HTMLResponse)
async def sourcing_analysis(request: Request):
    """Render the sourcing analysis results page"""
    analysis_id = "latest"
    data = analysis_data.get(analysis_id, {})
    
    # Add applied status to items
    critical_items = []
    for item in data.get("critical_items", []):
        item_copy = item.copy()
        item_id = f"critical-{item.get('ingredient', '').lower().replace(' ', '-')}"
        item_copy["id"] = item_id
        item_copy["applied"] = item_id in applied_recommendations
        critical_items.append(item_copy)
    
    optimization_items = []
    for item in data.get("optimization_items", []):
        item_copy = item.copy()
        item_id = f"optimization-{item.get('ingredient', '').lower().replace(' ', '-')}"
        item_copy["id"] = item_id
        item_copy["applied"] = item_id in applied_recommendations
        optimization_items.append(item_copy)
    
    return templates.TemplateResponse(
        request=request,
        name="analysis.html",
        context={
            "request": request,
            "critical_items": critical_items,
            "optimization_items": optimization_items,
        }
    )


@app.get("/results/comparison", response_class=HTMLResponse)
async def ingredient_comparison(request: Request):
    """Render the ingredient comparison page"""
    analysis_id = "latest"
    data = analysis_data.get(analysis_id, {})
    
    comparisons = data.get("comparisons", [])
    comparison = comparisons[0] if comparisons else None
    
    return templates.TemplateResponse(
        request=request,
        name="comparison.html",
        context={
            "request": request,
            "comparison": comparison,
        }
    )


@app.post("/api/apply-recommendation")
async def apply_recommendation(request: Request):
    """
    API endpoint to apply the recommendation.
    In production, this would update your procurement system.
    """
    body = await request.json()
    recommendation_id = body.get("recommendation_id", "")
    
    if recommendation_id:
        applied_recommendations.add(recommendation_id)
    
    return {"status": "success", "message": "Recommendation applied successfully"}
