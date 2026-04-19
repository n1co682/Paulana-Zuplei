# AI Supply Chain Manager

## The Problem

BOMs are created once and rarely revisited. Over time, better alternatives appear, but collecting the data needed to make a confident substitution decision is too expensive to do manually. So most BOMs accumulate hidden cost.

## Our Philosophy

Engineers and managers who built a BOM know their product best. They know which components are critical and which are commodity inputs where substitution is safe. Our system lets users explicitly scope which BOM entries are open to substitution. For those entries, our system does the heavy lifting.

## The Core Insight: Equivalence Classes

The hardest part of substitution is defining what "equivalent" even means. Our approach assigns every component an **equivalence class**: a label that captures its functional role, independent of brand or supplier.

For example, a BOM might list "Ascorbic Acid (DSM, 99% purity, food grade)" and separately "Vitamin C Powder (BASF)". These are the same functional input. By mapping both to the equivalence class `Vitamin C`, the system knows they compete in the same substitution pool. Similarly, "Amber PET Bottle 250ml" and "Brown HDPE Bottle 250ml" might both map to `250ml Dark Polymer Bottle` if compliance requirements allow it.

To populate these classes, we used a foundation model to extract equivalence class labels directly from component descriptions. This gave us a structured, consistent taxonomy across the database without any custom training.

The ideal long-term approach would go further: train a representation learning model on large volumes of historical BOM data, embedding each component into a shared functional space and clustering them automatically. This would allow the system to infer equivalence classes for components it has never seen before, purely from usage patterns across products. We consider this a key idea for making our system truly scalable, but it is not implemented in this prototype.

## System Architecture

```
[User] selects which BOM entries are open to substitution
         |
[Database] retrieves existing candidate components per equivalence class
         |
[AgnesAgent] enriches each candidate via LLM + web search
  - Scrapes technical specs, certificates, allergens (Gemini + Google Search)
  - Researches supplier ethics, ESG score, production location
  - Simulates price and lead time via mock negotiation
  - Ranks candidates against each other with a comparative quality pass
         |
[Pipeline] combinatorial evaluation of all valid BOM configurations
  - Filters by hard constraints (required certifications, forbidden allergens)
  - Scores each configuration across 7 dimensions
  - Weights scores by user-defined preferences
         |
[Output] ranked BOM configurations with per-dimension scores
```

## Scoring Dimensions

Each candidate component carries the following scores after enrichment, all normalized to [0, 1]:

| Dimension | Source |
|---|---|
| **Price** | Extracted from mock negotiation, scaled relative to pool |
| **Quality** | LLM-assessed from technical specs, comparatively ranked within pool |
| **Resilience** | Derived from production location (geographic risk proxy) |
| **Sustainability (ESG)** | Researched via Gemini from public ESG ratings and proxy indicators |
| **Ethics** | Summarized from public scandal and labor rights data |
| **Lead Time** | Extracted from negotiation simulation |
| **Consolidation** | Computed from the number of unique suppliers in the configuration |

Configurations are scored as a weighted average, with weights set by the user before the run.

## Why This Approach Is Trustworthy

The recommendation logic is entirely rule-based and deterministic. AI is used only in the **enrichment layer** to fill in missing fields from public sources, not in the ranking itself. Every score traces back to a specific data point, and every ranking reflects the user's stated priorities. The system surfaces ranked configurations with per-dimension breakdowns so the procurement team can make the final call with full visibility into the tradeoffs.

## What We Built

- **`models.py`** -- Core data model: `Component`, `Supplier`, `BOMEntry`, `UserPreferences`, `RankedBOM`, `ComponentFromSupplier`
- **`agent.py`** -- `AgnesAgent`: orchestrates enrichment for a given equivalence class, fetches existing components, searches for new suppliers if the pool is thin, and runs a comparative quality pass across all contenders
- **`tools.py`** -- LLM tool layer backed by Gemini with Google Search grounding: supplier search, spec scraping, ESG profiling, ethics research, mock negotiation, comparative quality ranking
- **`gemini_client.py`** -- Wrapper around the Gemini API with retry logic, timeout handling, and structured JSON output via Pydantic schemas
- **`database_manager.py`** -- SQLite interface for reading and writing components, suppliers, and enrichment data
- **`pipeline.py`** -- Filters candidates by hard constraints and evaluates all valid combinatorial configurations, sorted by weighted score
- **`main.py`** -- Entrypoint: fetches BOM from DB, runs our system per equivalence class, and prints the top 3 configurations with dimension scores

## What We Did Not Implement

- **Compliance inference from product context.** We handle hard constraints (certificates, allergens) as explicit filters, but do not yet reason about whether a substitute is acceptable given the regulatory context of the finished product.
- **Multimodal enrichment.** Label images, packaging text, and product page visuals are valuable signals. We scrape text-based sources but do not process images.
- **Persistent caching and incremental enrichment.** Each run re-enriches components from scratch. A production system would cache results and update them incrementally.