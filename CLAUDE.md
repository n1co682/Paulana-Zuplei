# Project: LLM-Driven Supply Chain Optimizer

Automates supplier discovery, enrichment, and selection for CPG manufacturing using Gemini + Google Search grounding.

## Architecture

```
AgnesAgent (orchestrator)
├── tools.py (Gemini-powered functions: search, scrape, ESG, ethics, negotiation)
└── GeminiClient (google-genai SDK, Vertex AI, gemini-3.1-pro-preview)
```

### Information Gathering
Given an `equivalence_class` (e.g. "vitamins"), the agent fetches existing components, enriches missing data via Gemini web search, finds new suppliers if <5 exist, and returns an enriched pool for decision-making.

### Decision Making
Rule-baed algorithm that evaluates suppliers based on enriched data, ESG scores, and ethical considerations to recommend the best options for procurement.

### Front End
A simple web interface for interacting with the agent and viewing results.

### Database
SQL database for storing supplier data, component details, and equivalence classes.

## LLM Integration

- **Model:** `gemini-3.1-pro-preview` via Vertex AI (`vertexai=True` in GeminiClient)
- **Grounding:** Google Search tool enabled for real-time supplier data

