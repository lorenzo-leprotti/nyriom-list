# nyriom-list

**AI-Powered Conference Delegate Prioritization Pipeline**

A 5-step Python pipeline that transforms ~500 conference delegates into a ranked TOP 50 engagement list using AI-powered research and multi-factor scoring. Built for [Nyriom Technologies](https://github.com/lollo408/nyriom-intel-hub) — a fictional Berlin-based bio-polymer composites startup used across my portfolio projects.

## What It Does

```
522 delegates (AEROCOM 2025 roster)
  │
  ├── Step 1: Categorize + filter (instant, $0)
  │     Company-type buckets (A-J) + job-function buckets (1-10)
  │     Three-layer filter: whitelist + role exclusion + score cutoff
  │     Result: 249 relevant delegates
  │
  ├── Step 2: AI research — 13 variables per delegate
  │     Configurable backend: Perplexity / Ollama / Demo
  │
  ├── Step 3: Multi-factor scoring + ranking
  │     Title + Company + Materials Proximity + Research Boosts
  │
  ├── Step 4: Deep research on TOP 60 (fill data gaps)
  │
  └── Step 5: Final ranking → TOP 50 deliverable
        Excel output with 6 sheets + interactive Streamlit dashboard
```

## Quick Start (Demo Mode — No API Key Required)

```bash
# Clone and set up
git clone https://github.com/lollo408/nyriom-list.git
cd nyriom-list
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline (uses pre-generated demo data)
python step1_buckets.py
python step2_research.py --backend demo
python step3_score.py
python step4_enhance.py --backend demo
python step5_final_rank.py

# Launch the dashboard
streamlit run dashboard.py
# Password: demo2026
```

## Research Backends

The pipeline supports three interchangeable research backends via a common `ResearchBackend` interface:

| Backend | Command | Web Search | Cost | Best For |
|---------|---------|------------|------|----------|
| **Demo** | `--backend demo` | N/A | Free | Quick demo, no setup needed |
| **Perplexity** | `--backend perplexity` | Yes | ~$1.85 | Production — verified web research |
| **Ollama** | `--backend ollama` | No | Free | Local LLM, open-source showcase |

### Using Perplexity (Production)

```bash
cp .env.example .env
# Edit .env with your Perplexity API key

python step2_research.py --backend perplexity --test 5  # Test first
python step2_research.py --backend perplexity            # Full run (~$1.25, ~22min)
python step4_enhance.py --backend perplexity             # Enhancement (~$0.60, ~5min)
```

### Using Ollama (Local LLM)

```bash
# Install Ollama: https://ollama.ai
ollama pull mistral

python step2_research.py --backend ollama --model mistral
python step4_enhance.py --backend ollama --model mistral
```

## Scoring Algorithm

**Priority Score = Title + Company + Materials Proximity + Research Boosts + Key Contact Bonus**

| Component | Max | What It Measures |
|-----------|-----|------------------|
| Title Score | 30 | Seniority (CEO=30, VP=22, Director=12, Engineer=5) |
| Company Score | 40 | Company type relevance to materials sales |
| Materials Adoption Proximity | 25 | Closeness to material selection decisions |
| Research Boosts | 30+ | Lightweighting, sustainability, R&D budget signals |
| Key Contact Bonus | 30 | Pre-identified targets |

## Architecture

```
nyriom_config.py          ← Master config: buckets, scoring rules, thresholds
research_backends.py      ← Backend abstraction (Perplexity / Ollama / Demo)
step1_buckets.py          ← Categorize + filter (no API)
step2_research.py         ← AI research: 13 variables per delegate
step3_score.py            ← Multi-factor scoring engine
step4_enhance.py          ← Deep research on top prospects
step5_final_rank.py       ← Final ranking + CRM export
dashboard.py              ← Interactive Streamlit dashboard
generate_data.py          ← Generate fictional delegate roster
generate_demo_data.py     ← Generate pre-baked research data
input/
  aerocom_2025_delegates.csv    ← Input roster (~500 delegates)
  demo_research_data.json       ← Pre-generated research results
```

## Fictional Context Disclosure

This is a portfolio demonstration. **AEROCOM 2025** is a fictional aerospace composites conference. Company names (Airbus, Hexcel, Safran, etc.) are real aerospace industry participants; individual delegate names are generated. The pipeline architecture, scoring logic, and Python code are production-representative — adapted from a real client engagement with all proprietary data removed.

## Related Projects

| Project | Description |
|---------|-------------|
| [nyriom-dashboard](https://github.com/lollo408/nyriom-dashboard) | Sustainability impact simulator |
| [nyriom-intel-hub](https://github.com/lollo408/nyriom-intel-hub) | AI market intelligence platform |

## Tech Stack

- **Python 3.10+** — Pipeline scripts
- **Pandas** — Data processing
- **Perplexity Sonar API** — Web-grounded AI research
- **Ollama** — Local open-source LLM inference
- **Streamlit + Plotly** — Interactive dashboard
