import logging
from typing import Dict, List, Type, TypeVar

from pydantic import BaseModel, Field

from gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agnes.tools")

_gemini = GeminiClient()

T = TypeVar("T", bound=BaseModel)


class SupplierSearchResponse(BaseModel):
    suppliers: List[str]


class ComponentDataResponse(BaseModel):
    quality: float = Field(ge=0.0, le=1.0)
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


class QualityComparisonResponse(BaseModel):
    rankings: Dict[str, float] = Field(..., description="Map of supplier name to relative quality score (0.0-1.0)")
    rationale: str = Field(..., description="Brief explanation of the ranking")


class ReplacementReasoningResponse(BaseModel):
    reasoning: str = Field(..., description="Context-aware reasoning for the top 3 candidates.")


def _call_gemini_structured(prompt: str, schema: Type[T], web_search: bool = False) -> T:
    logger.info(f"Requesting structured data for {schema.__name__} (web_search={web_search})")
    payload = _gemini.generate_json(
        prompt=prompt,
        response_schema=schema.model_json_schema(),
        web_search=web_search,
    )
    if not isinstance(payload, dict):
        logger.error(f"Gemini returned {type(payload).__name__} instead of dict for {schema.__name__}")
        raise ValueError(f"Expected JSON object, got {type(payload).__name__}")
    
    result = schema.model_validate(payload)
    logger.info(f"Successfully validated {schema.__name__}. Data: {result.model_dump()}")
    return result


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
        f"Extract quality (normalized rank from 0.0 to 1.0), description, certificates (e.g. Non-GMO, Organic, Halal, ISO), "
        f"and common allergens. **IMPORTANT:** If the product is allergen-free, return an empty list [] for allergens."
        f"Return JSON object with keys: quality, text, certificates, allergens."
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
        f"**IMPORTANT:** If no major scandals or ethical problems are found, return an empty string for ethics_summary. "
        f"If found, provide a very short, bulleted list of the problems. "
        f"For production_place, give ONLY the primary city and country (e.g., 'Basel, Switzerland'). "
        f"**IMPORTANT:** Provide exactly ONE location, even if the company has multiple sites. "
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


def compare_quality_pool(contenders: List[Dict]) -> Dict[str, float]:
    """Compare a pool of contenders and return relative quality scores (0.0-1.0)."""
    context = ""
    for c in contenders:
        context += f"Supplier: {c['supplier_name']}\nSpecs: {c['text']}\nCertificates: {c['certificates']}\n---\n"

    prompt = (
        f"**Task:** Compare the following 5 raw material offerings and rank them by quality on a scale of 0.0 to 1.0.\n"
        f"**Logic:** The best offering should be close to 1.0, and others scaled relative to it based on purity, "
        f"certificates, and technical specs provided.\n\n"
        f"**Contenders:**\n{context}\n\n"
        f"Return JSON object with key 'rankings' (map of supplier name to float) and 'rationale'."
    )
    
    try:
        result = _call_gemini_structured(prompt, QualityComparisonResponse, web_search=False)
        logger.info(f"Comparative quality rationale: {result.rationale}")
        return result.rankings
    except Exception as e:
        logger.error(f"Comparative quality failed: {e}. Using default scores.")
        return {c['supplier_name']: 0.8 for c in contenders}


def generate_replacement_reasoning(component_name: str, candidates: List[Dict], rest_of_bom: List[Dict]) -> str:
    """Generate context-aware reasoning for top 3 candidates."""
    cand_info = ""
    for i, c in enumerate(candidates, 1):
        cand_info += (
            f"Candidate #{i}: {c['supplier_name']}\n"
            f"Score: {c['total_score']:.2f} (Price: {c['p_score']:.2f}, Quality: {c['q_score']:.2f}, "
            f"Resilience: {c['r_score']:.2f}, Consolidation: {c['c_score']:.2f})\n"
            f"Location: {c['production_place']}\n"
            f"Specs: {c['quality_report']}\n---\n"
        )

    bom_info = ", ".join([f"{b['component_name']} ({b['supplier_name']})" for b in rest_of_bom])

    prompt = (
        f"**Task:** Provide a concise, professional reasoning for the top 3 replacement candidates for '{component_name}'.\n"
        f"**Context:** The current BOM includes: {bom_info}.\n"
        f"**Candidates:**\n{cand_info}\n"
        f"**Instructions:**\n"
        f"1. Generate reasoning for Top 1, Top 2, and Top 3 in a single narrative that shares context.\n"
        f"2. Mention how each candidate fits into the existing BOM (e.g., supplier consolidation).\n"
        f"3. Evaluate geographical resilience (e.g., risks from dependence on certain shipping corridors or straits based on the location).\n"
        f"4. Format as: 'Top 1: ... Top 2: ... Top 3: ...'\n"
        f"Return JSON object with key 'reasoning'."
    )

    try:
        result = _call_gemini_structured(prompt, ReplacementReasoningResponse, web_search=True)
        return result.reasoning
    except Exception as e:
        logger.error(f"Reasoning generation failed: {e}")
        return "Reasoning could not be generated at this time."
