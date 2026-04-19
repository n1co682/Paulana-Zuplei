# Project: LLM-Driven Supply Chain Optimizer

Automates supplier discovery, enrichment, and selection for CPG manufacturing using Gemini + Google Search grounding.

## Architecture

Two separate FastAPI services that must both be running:

| Service | Entry point | Default port |
|---------|-------------|--------------|
| Backend | `src/backend/main.py` | 8000 |
| Frontend | `src/frontend/backend/main.py` | 8001 |

The frontend is a thin adapter: it renders Jinja2 HTML templates and proxies all real work to the backend. It reads `BACKEND_URL` from the environment (default `http://localhost:8000`).

```
Browser → Frontend (8001)
              ├── GET /bom          → Backend GET  /bom
              └── POST /replacements → Backend POST /replacements
```

### Backend (`src/backend/`)
```
AgnesAgent (orchestrator)
├── tools.py       (Gemini functions: search, scrape, ESG, ethics, negotiation)
├── pipeline.py    (rule-based ranking across 7 dimensions)
├── database_manager.py  (SQLite: products, suppliers, BOM)
└── GeminiClient   (google-genai SDK, Vertex AI, gemini-3.1-pro-preview)
```

Backend API:
- `GET /bom` — returns full BOM for product_id=1 from SQLite
- `POST /replacements` — runs AgnesAgent per selected component, returns top-3 ranked candidates with LLM reasoning

### Frontend (`src/frontend/backend/`)
```
main.py       — FastAPI routes; proxies backend via httpx
transforms.py — field conversions (0-1 scores → display values, hours → days, etc.)
templates/
  start.html      — sourcing config form with radar chart and live BOM checkboxes
  analysis.html   — results split into critical / optimization sections
  comparison.html — side-by-side current vs recommended supplier
```

Key data mapping decisions (applied in `transforms.py`):
- `price_per_unit` (dollars float) → `"$X.XX"` — **not** `price_scaled` (internal 0-1 score, not shown)
- `esg_score` (0-1 or 0-100) → letter grade via `esg_to_letter()`
- `resilience_score / ethics_score` (0-1) → 0-5 display scale via `to_five()`
- `lead_time` (hours) → `"X Days"` via `hours_to_days_str()`
- `quality` (0-1) → percentage and grade letter via `to_rate()` / `quality_to_grade()`
- Vector weights from radar chart (0-1 floats) → `UserPreferences` ints (×100) via `vectors_to_prefs()`
- Critical vs optimization: critical if any dimension score improves >0.20 vs current BOM entry

### Information Gathering
Given an `equivalence_class` (e.g. "vitamins"), the agent fetches existing components, enriches missing data via Gemini web search, finds new suppliers if <5 exist, and returns an enriched pool for decision-making.

### Decision Making
Rule-based algorithm that evaluates suppliers based on enriched data, ESG scores, and ethical considerations to recommend the best options for procurement.

### Database
SQLite. `get_bom_detailed(product_id)` returns rows where `price` is in **dollars** (not cents). The `Component` model uses cents internally; `database_manager.py` converts on read/write.

## Dependencies

All dependencies are in `pyproject.toml` at the repo root. Install with:
```bash
pip install -e .
```
`requirements.txt` and `src/frontend/backend/pyproject.toml` are stubs that redirect here.

## LLM Integration

- **Model:** `gemini-3.1-pro-preview` via Vertex AI (`vertexai=True` in GeminiClient)
- **Grounding:** Google Search tool enabled for real-time supplier data
- **Timeout:** Frontend allows 180s for `/replacements` calls (LLM-heavy)

## Running

```bash
# Terminal 1
cd src/backend && uvicorn main:app --port 8000 --reload

# Terminal 2
cd src/frontend/backend && uvicorn main:app --port 8001 --reload
```
