# Design: "How It Works" Dashboard Page

## Summary

Add an interactive pipeline explainer page to the existing Streamlit dashboard. Uses a horizontal step selector (Steps 1-5) with each step showing input/output metrics, a step-specific visualization, and (for Steps 2 & 4) a backend comparison panel contrasting Perplexity, Ollama, and Demo approaches.

## Audience

Both recruiters/hiring managers (clear visual story) and technical peers (architectural depth).

## Location

New page in existing dashboard sidebar, alongside TOP 50, Supplier Intelligence, Overview & Stats, Methodology.

## Page Layout

Horizontal step selector at top (5 buttons). Selected step renders below with consistent structure:
- Title + one-line description
- Input → Output metrics (styled containers)
- Step-specific visualization
- Backend comparison panel (Steps 2 & 4 only)

## Per-Step Content

### Step 1 — Filter & Categorize
- Metrics: 522 → 249 delegates (48% pass rate)
- Viz: horizontal bar chart of company bucket distribution, excluded buckets grayed out
- Text: "Three-layer filter: company whitelist + role exclusion + minimum score"

### Step 2 — AI Research
- Metrics: 249 delegates → 249 + 13 research variables
- Viz: fill rate bar chart (% of delegates with data for each variable)
- Backend comparison panel

### Step 3 — Scoring
- Metrics: 249 researched → ranked, top 60 selected
- Viz: score distribution histogram with top-60 cutoff line
- Score breakdown example for one delegate

### Step 4 — Enhancement
- Metrics: Top 60 → 60 with deeper research on 6 priority fields
- Viz: before/after fill rate comparison for 6 gap fields
- Backend comparison panel

### Step 5 — Final Ranking
- Metrics: Re-scored → TOP 50 deliverable
- Viz: top 10 mini-leaderboard with score bars
- Output summary

## Backend Comparison Panel

Three tabs (Perplexity / Ollama / Demo), each showing:

1. **Architecture flow** — styled containers showing the data path:
   - Perplexity: Delegate → API → Web Search → Verified JSON (cost, speed, web-grounded)
   - Ollama: Delegate → Local LLM → Model Knowledge → JSON (cost, speed, no web)
   - Demo: Delegate → Key Lookup → Pre-generated JSON (instant, free)

2. **Example output** — same delegate (Erik Lindstrom, Airbus) researched by each backend, showing 3-4 key fields side-by-side to make the quality/trade-off tangible.

## Data Sources

- Step 1: read checkpoint1_filtered.xlsx (FILTERED + EXCLUDED sheets)
- Steps 2-5: read final output AEROCOM_2025_FINAL_TOP50.xlsx
- Backend examples: hardcoded realistic examples for Perplexity/Ollama (demo data from JSON)
- Fill rates: computed from actual demo research data

## Non-Goals

- No live API calls from the dashboard
- No editable parameters or re-running steps
- No animation/transitions (keep it simple)
