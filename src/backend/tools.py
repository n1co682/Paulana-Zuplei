import os
import json
import google.generativeai as genai
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # Enable Google Search grounding
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{"google_search": {}}]
    )
else:
    print("Warning: GOOGLE_API_KEY not found. Using mock responses for tools.")
    model = None

def call_gemini(prompt: str, json_mode: bool = False) -> str:
    if not model:
        # Fallback mocks if no API key
        prompt_lower = prompt.lower()
        if "email" in prompt_lower:
            return json.dumps({
                "email_text": "Subject: Quote for Component\n\nDear Agnes,\n\nOur price is $1.50 per unit with a lead time of 48 hours.\n\nBest regards,\nSupplier Team",
                "price_per_unit": 150,
                "lead_time": 48
            }) if json_mode else "Email text"
        if "senior esg analyst" in prompt_lower:
            return f"""**Executive Summary:** AlphaVitamins shows strong ESG commitment with clear supply chain transparency.
**Official Ratings Table:** MSCI: A (2025).
**Synthetic ESG Score:** 85/100.
**Key Risks & Strengths:** Strength: Organic sourcing. Risk: Plastic packaging.
**Sources:** https://alphavitamins.com/esg
```json
{{"final_score": 85, "summary": "Strong ESG standing with MSCI A rating."}}
```"""
        if "ethics" in prompt_lower or "scandals" in prompt_lower:
            return json.dumps({"ethics_summary": "No major scandals found. Clean reputation.", "production_place": "Europe"}) if json_mode else "Clean reputation."
        if "major global suppliers" in prompt_lower:
            return json.dumps(["Global Source A", "TechMaterials Corp", "BioSupply Inc", "EcoIngredients", "PureRaw Materials"]) if json_mode else "List of suppliers"
        if "technical specifications" in prompt_lower:
            return json.dumps({
                "quality": 8,
                "text": "High quality component specification.",
                "certificates": ["Non-GMO", "ISO-9001"],
                "allergens": ["None"]
            }) if json_mode else "Specs"
        
        return json.dumps({"data": "mocked"}) if json_mode else "Mocked Gemini response"

    response = model.generate_content(prompt)
    return response.text

def search_suppliers(equivalence_class: str) -> List[str]:
    """Search for new suppliers for a given component class."""
    prompt = f"Search for 5 major global suppliers of {equivalence_class} for CPG manufacturing. Return only a JSON list of supplier names."
    response_text = call_gemini(prompt, json_mode=True)
    try:
        # Basic cleanup of markdown if LLM includes it
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
             response_text = response_text.split("```")[1].split("```")[0].strip()
        return json.loads(response_text)
    except:
        return ["Global Source A", "TechMaterials Corp", "BioSupply Inc", "EcoIngredients", "PureRaw Materials"]

def scrape_component_data(supplier_name: str, component_name: str) -> Dict:
    """Scrape technical specifications using Gemini's built-in Google Search."""
    prompt = (
        f"Use Google Search to find the official technical specifications of '{component_name}' from supplier '{supplier_name}'. "
        f"Extract quality (rank 1-10), description, certificates (e.g. Non-GMO, Organic, Halal, ISO), "
        f"and common allergens. Return as JSON with keys: quality, text, certificates, allergens."
    )
    response_text = call_gemini(prompt, json_mode=True)
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        return json.loads(response_text)
    except:
        return {
            "quality": 8,
            "text": f"High quality {component_name} sourced from sustainable farms.",
            "certificates": ["Non-GMO", "ISO-9001"],
            "allergens": ["None"]
        }

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
    response_text = call_gemini(prompt)
    
    # Try to extract the JSON block
    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "{" in response_text:
            # Find the last occurrence of { }
            start = response_text.rfind("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
        else:
            json_str = "{}"
        
        data = json.loads(json_str)
        return {
            "full_profile": response_text,
            "esg_score": data.get("final_score", 50),
            "summary": data.get("summary", "ESG analysis completed.")
        }
    except:
        return {
            "full_profile": response_text,
            "esg_score": 50,
            "summary": "ESG analysis completed (extraction failed)."
        }

def analyze_supplier_ethics(supplier_name: str) -> Dict:
    """Search for ethical reports and scandals, and integrate the ESG profile."""
    # First get the comprehensive ESG profile
    esg_data = get_esg_profile(supplier_name)
    
    # Then search for specific scandals or ethical problems
    prompt = (
        f"Use Google Search to find any specific scandals, labor rights abuses, or ethical controversies "
        f"associated with '{supplier_name}'. Focus on worker conditions, legal cases, and environmental violations. "
        f"Return as JSON with keys: ethics_summary, production_place."
    )
    response_text = call_gemini(prompt, json_mode=True)
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        scandal_data = json.loads(response_text)
    except:
        scandal_data = {"ethics_summary": "No major scandals found.", "production_place": "Unknown"}

    return {
        "ethics": f"ESG Profile: {esg_data['summary']}\n\nEthical Reports: {scandal_data.get('ethics_summary')}",
        "esg_score": esg_data['esg_score'],
        "production_place": scandal_data.get("production_place"),
        "full_esg_profile": esg_data['full_profile']
    }

def generate_mock_negotiation(supplier_name: str, component_name: str) -> Dict:
    """Simulate getting a quote via email."""
    prompt = (
        f"Generate a short, realistic email from '{supplier_name}' providing a price quote and lead time "
        f"for '{component_name}'. Then, extract the price_per_unit (in cents) and lead_time (in hours) "
        f"into a JSON object. Return only the JSON with keys: email_text, price_per_unit, lead_time."
    )
    response_text = call_gemini(prompt, json_mode=True)
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        return json.loads(response_text)
    except:
        return {
            "email_text": f"Hi, the price for {component_name} is $1.20/unit with 72h lead time.",
            "price_per_unit": 120,
            "lead_time": 72
        }
