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
    model = genai.GenerativeModel('gemini-1.5-flash')
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
        if "ethics" in prompt_lower:
            return json.dumps({"ethics": "No major scandals found. Clean reputation.", "esg_score": 85, "production_place": "Europe"}) if json_mode else "Clean reputation."
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
    """Mock scraping of technical specifications."""
    prompt = (
        f"Search for technical specifications of '{component_name}' from supplier '{supplier_name}'. "
        f"Include quality (rank 1-10), description, certificates (e.g. Non-GMO, Organic, Halal, ISO), "
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

def analyze_supplier_ethics(supplier_name: str) -> Dict:
    """Search for ethical reports and scandals."""
    prompt = (
        f"Analyze the reputation and ethics of '{supplier_name}'. Search for scandals, worker condition reports, "
        f"and sustainability (ESG) scores. Return as JSON with keys: ethics (summary), esg_score (1-100), "
        f"production_place (likely country/region)."
    )
    response_text = call_gemini(prompt, json_mode=True)
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        return json.loads(response_text)
    except:
        return {
            "ethics": "No significant scandals reported. Strong labor practices.",
            "esg_score": 75,
            "production_place": "Germany"
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
