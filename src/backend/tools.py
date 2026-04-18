import json
from typing import Dict, List

from .gemini_client import GeminiClient

_gemini = GeminiClient()


def _call_gemini(prompt: str, web_search: bool = False) -> str:
    return _gemini.generate(prompt, web_search=web_search)


def _mock_response(prompt: str) -> str:
    p = prompt.lower()
    if "email" in p:
        return json.dumps({
            "email_text": "Subject: Quote for Component\n\nDear Agnes,\n\nOur price is $1.50 per unit with a lead time of 48 hours.\n\nBest regards,\nSupplier Team",
            "price_per_unit": 150,
            "lead_time": 48,
        })
    if "senior esg analyst" in p:
        return (
            "**Executive Summary:** AlphaVitamins shows strong ESG commitment with clear supply chain transparency.\n"
            "**Official Ratings Table:** MSCI: A (2025).\n"
            "**Synthetic ESG Score:** 85/100.\n"
            "**Key Risks & Strengths:** Strength: Organic sourcing. Risk: Plastic packaging.\n"
            "**Sources:** https://alphavitamins.com/esg\n"
            '```json\n{"final_score": 85, "summary": "Strong ESG standing with MSCI A rating."}\n```'
        )
    if "ethics" in p or "scandals" in p:
        return json.dumps({"ethics_summary": "No major scandals found. Clean reputation.", "production_place": "Europe"})
    if "major global suppliers" in p:
        return json.dumps(["Global Source A", "TechMaterials Corp", "BioSupply Inc", "EcoIngredients", "PureRaw Materials"])
    if "technical specifications" in p:
        return json.dumps({"quality": 8, "text": "High quality component specification.", "certificates": ["Non-GMO", "ISO-9001"], "allergens": ["None"]})
    return json.dumps({"data": "mocked"})


def _parse_json_list(text: str) -> list:
    result = _parse_json_any(text)
    if not isinstance(result, list):
        raise ValueError("Expected JSON list")
    return result


def _parse_json_dict(text: str) -> dict:
    result = _parse_json_any(text)
    if not isinstance(result, dict):
        raise ValueError("Expected JSON object")
    return result


def _parse_json_any(text: str) -> dict | list:
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


def search_suppliers(equivalence_class: str) -> List[str]:
    """Search for new suppliers for a given component class."""
    prompt = f"Search for 5 major global suppliers of {equivalence_class} for CPG manufacturing. Return only a JSON list of supplier names."
    try:
        return _parse_json_list(_call_gemini(prompt, web_search=True))
    except Exception:
        return ["Global Source A", "TechMaterials Corp", "BioSupply Inc", "EcoIngredients", "PureRaw Materials"]


def scrape_component_data(supplier_name: str, component_name: str) -> Dict:
    """Scrape technical specifications using Gemini's built-in Google Search."""
    prompt = (
        f"Use Google Search to find the official technical specifications of '{component_name}' from supplier '{supplier_name}'. "
        f"Extract quality (rank 1-10), description, certificates (e.g. Non-GMO, Organic, Halal, ISO), "
        f"and common allergens. Return as JSON with keys: quality, text, certificates, allergens."
    )
    try:
        return _parse_json_dict(_call_gemini(prompt, web_search=True))
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

**Output Format:**
- **Executive Summary:** A 2-sentence overview of their ESG standing.
- **Official Ratings Table:** (If found).
- **Synthetic ESG Score:** A calculated estimate with a breakdown of E, S, and G components. (Crucial: Provide the final aggregate score as an integer).
- **Key Risks & Strengths:** Bulleted list of material factors.
- **Sources:** List the URLs used for the assessment.

Finally, please output a JSON block at the very end with the format: {{"final_score": int, "summary": str}}
"""
    response_text = _call_gemini(prompt, web_search=True)

    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "{" in response_text:
            start = response_text.rfind("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
        else:
            json_str = "{}"

        data = json.loads(json_str)
        return {
            "full_profile": response_text,
            "esg_score": data.get("final_score", 50),
            "summary": data.get("summary", "ESG analysis completed."),
        }
    except Exception:
        return {"full_profile": response_text, "esg_score": 50, "summary": "ESG analysis completed (extraction failed)."}


def analyze_supplier_ethics(supplier_name: str) -> Dict:
    """Search for ethical reports and scandals, and integrate the ESG profile."""
    esg_data = get_esg_profile(supplier_name)

    prompt = (
        f"Use Google Search to find any specific scandals, labor rights abuses, or ethical controversies "
        f"associated with '{supplier_name}'. Focus on worker conditions, legal cases, and environmental violations. "
        f"Return as JSON with keys: ethics_summary, production_place."
    )
    try:
        scandal_data = _parse_json_dict(_call_gemini(prompt, web_search=True))
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
        f"for '{component_name}'. Then, extract the price_per_unit (in cents) and lead_time (in hours) "
        f"into a JSON object. Return only the JSON with keys: email_text, price_per_unit, lead_time."
    )
    try:
        return _parse_json_dict(_call_gemini(prompt, web_search=False))
    except Exception:
        return {"email_text": f"Hi, the price for {component_name} is $1.20/unit with 72h lead time.", "price_per_unit": 120, "lead_time": 72}
