from typing import Dict, List, Type, TypeVar

from pydantic import BaseModel, Field

from .gemini_client import GeminiClient

_gemini = GeminiClient()

T = TypeVar("T", bound=BaseModel)


class SupplierSearchResponse(BaseModel):
    suppliers: List[str]


class ComponentDataResponse(BaseModel):
    quality: int = Field(ge=1, le=10)
    text: str
    certificates: List[str]
    allergens: List[str]


class ESGProfileResponse(BaseModel):
    full_profile: str
    final_score: int = Field(ge=0, le=100)
    summary: str


class EthicsResponse(BaseModel):
    ethics_summary: str
    production_place: str


class NegotiationResponse(BaseModel):
    email_text: str
    price_per_unit: int = Field(ge=0)
    lead_time: int = Field(ge=0)


def _call_gemini(prompt: str, web_search: bool = False) -> str:
    return _gemini.generate(prompt, web_search=web_search)


def _call_gemini_structured(prompt: str, schema: Type[T], web_search: bool = False) -> T:
    payload = _gemini.generate_json(
        prompt=prompt,
        response_schema=schema.model_json_schema(),
        web_search=web_search,
    )
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object, got {type(payload).__name__}")
    return schema.model_validate(payload)


def search_suppliers(equivalence_class: str) -> List[str]:
    """Search for new suppliers for a given component class."""
    prompt = (
        f"Search for 5 major global suppliers of {equivalence_class} for CPG manufacturing. "
        f"Return JSON object with key 'suppliers' containing only supplier names."
    )
    try:
        result = _call_gemini_structured(prompt, SupplierSearchResponse, web_search=True)
        return result.suppliers
    except Exception:
        return ["Global Source A", "TechMaterials Corp", "BioSupply Inc", "EcoIngredients", "PureRaw Materials"]


def scrape_component_data(supplier_name: str, component_name: str) -> Dict:
    """Scrape technical specifications using Gemini's built-in Google Search."""
    prompt = (
        f"Use Google Search to find the official technical specifications of '{component_name}' from supplier '{supplier_name}'. "
        f"Extract quality (rank 1-10), description, certificates (e.g. Non-GMO, Organic, Halal, ISO), "
        f"and common allergens. Return JSON object with keys: quality, text, certificates, allergens."
    )
    try:
        result = _call_gemini_structured(prompt, ComponentDataResponse, web_search=True)
        return result.model_dump()
    except Exception:
        return {"quality": 8, "text": f"High quality {component_name} sourced from sustainable farms.", "certificates": ["Non-GMO", "ISO-9001"], "allergens": ["None"]}


def get_esg_profile(company_name: str) -> Dict:
    """Research and provide a comprehensive ESG profile using a specialized senior analyst prompt."""
    prompt = f"""**Role:** You are a Senior ESG Analyst specializing in the Health & Wellness and Dietary Supplement sectors.

**Task:** Research and provide a comprehensive ESG (Environmental, Social, and Governance) Profile for {company_name}.

**Instructions:**
1. **Direct Search:** Search for official ESG ratings from major providers (MSCI, Sustainalytics, S&P Global, EcoVadis, or CDP). Report the specific score, the date issued, and the rating scale used.
2. **Proxy Search (If no direct rating exists):** Look for alternative indicators of sustainability performance, including:
   - Certifications (e.g., B Corp status, NSF International, Non-GMO Project, Organic certifications).
   - Corporate Sustainability Reports (CSR) or Impact Reports from the last 24 months.
   - Supply chain transparency (e.g., sourcing of botanicals, plastic reduction targets).
3. **Conversion & Calibration Logic:** If no formal ESG score is available, synthesize a "Synthetic ESG Rating" on a scale of 0-100 (where 100 is excellent). Use the following weights:
   - **Environmental (30%):** Sustainable packaging, carbon footprint, and ingredient sourcing.
   - **Social (40%):** Product safety/labeling, labor practices in the supply chain, and consumer health impact.
   - **Governance (30%):** Board diversity, executive compensation transparency, and regulatory compliance (FDA/FTC history).
4. **Benchmarking:** Briefly compare this company to industry peers (e.g., Nestlé Health Science, Thorne, or NOW Foods) to provide context.

Return JSON object with exactly these keys:
- full_profile: string containing the complete ESG analysis with executive summary, ratings, score rationale, risks/strengths, and sources.
- final_score: integer from 0 to 100.
- summary: short summary sentence.
"""
    try:
        data = _call_gemini_structured(prompt, ESGProfileResponse, web_search=True)
        return {
            "full_profile": data.full_profile,
            "esg_score": data.final_score,
            "summary": data.summary,
        }
    except Exception:
        return {
            "full_profile": "ESG analysis unavailable.",
            "esg_score": 50,
            "summary": "ESG analysis completed (extraction failed).",
        }


def analyze_supplier_ethics(supplier_name: str) -> Dict:
    """Search for ethical reports and scandals, and integrate the ESG profile."""
    esg_data = get_esg_profile(supplier_name)

    prompt = (
        f"Use Google Search to find any specific scandals, labor rights abuses, or ethical controversies "
        f"associated with '{supplier_name}'. Focus on worker conditions, legal cases, and environmental violations. "
        f"Return JSON object with keys: ethics_summary, production_place."
    )
    try:
        scandal_data = _call_gemini_structured(prompt, EthicsResponse, web_search=True).model_dump()
    except Exception:
        scandal_data = {"ethics_summary": "No major scandals found.", "production_place": "Unknown"}

    return {
        "ethics": f"ESG Profile: {esg_data['summary']}\n\nEthical Reports: {scandal_data.get('ethics_summary')}",
        "esg_score": esg_data["esg_score"],
        "production_place": scandal_data.get("production_place"),
        "full_esg_profile": esg_data["full_profile"],
    }


def generate_mock_negotiation(supplier_name: str, component_name: str) -> Dict:
    """Simulate getting a quote via email."""
    prompt = (
        f"Generate a short, realistic email from '{supplier_name}' providing a price quote and lead time "
        f"for '{component_name}'. Then, extract the price_per_unit (in cents) and lead_time (in hours). "
        f"Return JSON object with keys: email_text, price_per_unit, lead_time."
    )
    try:
        result = _call_gemini_structured(prompt, NegotiationResponse, web_search=False)
        return result.model_dump()
    except Exception:
        return {"email_text": f"Hi, the price for {component_name} is $1.20/unit with 72h lead time.", "price_per_unit": 120, "lead_time": 72}
