"""
AEROCOM 2025 - Interactive Prioritization Dashboard
====================================================

A comprehensive dashboard showing:
- TOP 50 priority delegates with scoring breakdown
- Material supplier intelligence (supplier-company relationships)
- Overview statistics and charts
- Methodology explanation

Run locally: streamlit run dashboard.py
"""

import re
import pandas as pd
from pathlib import Path

try:
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    print("Install required packages: pip install streamlit plotly")
    exit(1)

# Configuration
DATA_FILE = Path("output/AEROCOM_2025_FINAL_TOP50.xlsx")

# Known composite/polymer material suppliers for competitive intel parsing
KNOWN_SUPPLIERS = [
    "Hexcel", "Toray", "Solvay", "BASF", "DuPont", "Arkema", "Teijin",
    "Covestro", "Huntsman", "Cytec", "Mitsubishi Chemical", "SGL Carbon",
    "Zoltek", "Gurit", "Evonik", "Henkel", "3M", "Dow", "SABIC",
    "Lanxess", "Renegade Materials", "TenCate", "Park Electrochemical",
]

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================
def check_password():
    """Returns True if the user has entered the correct password."""

    def password_entered():
        try:
            correct_password = st.secrets["password"]
        except Exception:
            correct_password = "demo2026"

        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("## AEROCOM 2025 - Nyriom Technologies")
        st.markdown("*Delegate Prioritization Dashboard*")
        st.markdown("---")
        st.text_input(
            "Enter password to access:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.markdown("*Contact your team lead if you need access.*")
        return False

    elif not st.session_state["password_correct"]:
        st.markdown("## AEROCOM 2025 - Nyriom Technologies")
        st.markdown("---")
        st.text_input(
            "Enter password to access:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("Incorrect password. Please try again.")
        return False

    else:
        return True


# =============================================================================
# DATA HELPERS
# =============================================================================
def _has_display_data(value) -> bool:
    """Check if a research field has real displayable data."""
    v = str(value).strip()
    if not v or v.lower() in ["", "nan", "none", "not_found"]:
        return False
    if v.lower().startswith("not_found") or v.lower().startswith("not found"):
        return False
    return True


def _display_value(value) -> str:
    """Return cleaned display string for a research field."""
    if not _has_display_data(value):
        return ""
    return str(value).strip()


def _parse_suppliers(supplier_str: str) -> list:
    """Extract known supplier names from a current_material_suppliers string."""
    if not _has_display_data(supplier_str):
        return []
    supplier_lower = str(supplier_str).lower()
    found = []
    for s in KNOWN_SUPPLIERS:
        if s.lower() in supplier_lower:
            found.append(s)
    return found


# =============================================================================
# DATA LOADING
# =============================================================================
@st.cache_data
def load_data():
    """Load the AEROCOM prioritized data from the final Excel output."""
    if not DATA_FILE.exists():
        return None, None, None

    top50 = pd.read_excel(DATA_FILE, sheet_name="TOP_50")
    all_filtered = pd.read_excel(DATA_FILE, sheet_name="ALL_FILTERED")
    materials_targets = pd.read_excel(DATA_FILE, sheet_name="MATERIALS_TARGETS")
    return top50, all_filtered, materials_targets


# =============================================================================
# PAGE 1: TOP 50 DELEGATES
# =============================================================================
def render_top50(df):
    """Render the TOP 50 delegates page."""
    st.markdown("### Your Priority Engagement List")
    st.markdown("*AEROCOM 2025 — Advanced Composites Conference, Toulouse*")

    # Summary metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Delegates", len(df))
    with col2:
        key_contacts = len(df[df["Is_Key_Contact"] == "Y"])
        st.metric("Key Contacts", key_contacts)
    with col3:
        materials_adj = len(df[df["Materials_Adoption_Proximity"] > 0])
        st.metric("Materials-Adjacent", materials_adj)
    with col4:
        avg_score = df["Priority_Score"].mean()
        st.metric("Avg Score", f"{avg_score:.0f}")

    st.markdown("---")

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        bucket_labels = sorted(df["Company_Bucket_Label"].dropna().unique().tolist())
        company_filter = st.multiselect(
            "Company Type",
            options=bucket_labels,
            default=bucket_labels,
        )
    with col2:
        adoption_options = ["All"]
        if "materials_adoption_role" in df.columns:
            adoption_options += sorted(
                df["materials_adoption_role"].dropna().unique().tolist()
            )
        adoption_filter = st.selectbox("Materials Adoption Role", adoption_options)
    with col3:
        rank_min = int(df["Rank"].min()) if "Rank" in df.columns else 1
        rank_max = int(df["Rank"].max()) if "Rank" in df.columns else 50
        rank_range = st.slider(
            "Rank Range",
            min_value=rank_min,
            max_value=rank_max,
            value=(rank_min, rank_max),
        )
    with col4:
        search = st.text_input("Search name/company")

    # Apply filters
    filtered = df.copy()
    if company_filter:
        filtered = filtered[filtered["Company_Bucket_Label"].isin(company_filter)]
    if adoption_filter != "All":
        filtered = filtered[
            filtered["materials_adoption_role"].astype(str).str.upper() == adoption_filter.upper()
        ]
    if "Rank" in filtered.columns:
        filtered = filtered[
            (filtered["Rank"] >= rank_range[0]) & (filtered["Rank"] <= rank_range[1])
        ]
    if search:
        search_lower = search.lower()
        mask = (
            filtered["First Name"].str.lower().str.contains(search_lower, na=False)
            | filtered["Last Name"].str.lower().str.contains(search_lower, na=False)
            | filtered["Company Name"].str.lower().str.contains(search_lower, na=False)
        )
        filtered = filtered[mask]

    # Table display columns
    display_cols = [
        "Rank", "First Name", "Last Name", "Job Title", "Company Name",
        "Priority_Score", "Materials_Adoption_Proximity", "Company_Bucket_Label",
        "Is_Key_Contact", "Strategic_Value",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=400,
    )
    st.caption(f"Showing {len(filtered)} of {len(df)} delegates")

    # Delegate detail view
    st.markdown("---")
    st.markdown("### Delegate Detail")

    prospect_options = [
        f"#{int(row['Rank'])} — {row['First Name']} {row['Last Name']} @ {row['Company Name']}"
        if "Rank" in row.index
        else f"{row['First Name']} {row['Last Name']} @ {row['Company Name']}"
        for _, row in filtered.iterrows()
    ]

    if prospect_options:
        selected = st.selectbox("Select a delegate:", prospect_options)
        if selected:
            idx = prospect_options.index(selected)
            prospect = filtered.iloc[idx]
            render_prospect_detail(prospect)
    else:
        st.info("No delegates match your filters.")


def render_prospect_detail(p):
    """Render the 4-tab detail view for a single delegate."""

    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"## {p['First Name']} {p['Last Name']}")
        st.markdown(f"**{p.get('Job Title', '')}**")
        st.markdown(f"*{p.get('Company Name', '')}*")
    with col2:
        st.metric("Priority Score", int(p["Priority_Score"]))
    with col3:
        rank = int(p["Rank"]) if "Rank" in p.index else "—"
        st.metric("Rank", f"#{rank}")

    # Key flags
    flags = []
    if p.get("Is_Key_Contact") == "Y":
        flags.append("**KEY CONTACT**")
    if p.get("Lightweighting_Flag") == "Y":
        flags.append("Lightweighting Opportunity")
    if p.get("Sustainability_Flag") == "Y":
        flags.append("Sustainability Aligned")
    if p.get("RD_Budget_Flag") == "Y":
        flags.append("R&D Budget Identified")
    enhancement = str(p.get("Enhancement_Status", ""))
    if enhancement == "ENHANCED":
        flags.append("Enhanced with Deep Research")

    if flags:
        st.markdown(" | ".join(flags))

    st.markdown("---")

    # 4 Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Scoring Breakdown", "Research Data", "Company Context", "Outreach Notes",
    ])

    # --- TAB 1: SCORING BREAKDOWN ---
    with tab1:
        st.markdown("### How This Score Was Calculated")

        col1, col2 = st.columns(2)
        with col1:
            title_score = int(p.get("Title_Score", 0))
            st.markdown("**Title Score**")
            st.progress(min(title_score / 30, 1.0))
            st.markdown(f"{title_score}/30 points")
            st.caption(f"Reason: {p.get('Title_Reason', 'N/A')}")

            company_score = int(p.get("Company_Score", 0))
            st.markdown("**Company Score**")
            st.progress(min(company_score / 40, 1.0))
            st.markdown(f"{company_score}/40 points — {p.get('Company_Bucket_Label', 'Unknown')}")

        with col2:
            prox_score = int(p.get("Materials_Adoption_Proximity", 0))
            st.markdown("**Materials Adoption Proximity**")
            st.progress(min(prox_score / 25, 1.0))
            st.markdown(f"{prox_score}/25 points")
            st.caption(f"Reason: {p.get('Materials_Reason', 'N/A')}")

            research_boost = int(p.get("Research_Boost", 0))
            st.markdown("**Research Boosts**")
            st.progress(min(research_boost / 30, 1.0))
            st.markdown(f"+{research_boost} points")
            boost_detail = p.get("Boost_Details", "")
            if boost_detail:
                st.caption(boost_detail)

        if p.get("Is_Key_Contact") == "Y":
            st.markdown("**Key Contact Bonus:** +30 points (pre-identified target)")

        # Stacked bar chart
        components = {
            "Title": title_score,
            "Company": company_score,
            "Materials Proximity": prox_score,
            "Research Boosts": research_boost,
        }
        if p.get("Is_Key_Contact") == "Y":
            components["Key Contact"] = 30

        fig = go.Figure(data=[
            go.Bar(
                x=[v],
                y=["Score"],
                name=k,
                orientation="h",
                text=[f"{k}: {v}"],
                textposition="inside",
            )
            for k, v in components.items() if v > 0
        ])
        fig.update_layout(
            barmode="stack",
            title="Score Composition",
            xaxis_title="Points",
            yaxis_visible=False,
            height=120,
            margin=dict(l=0, r=20, t=40, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        sv = p.get("Strategic_Value", "")
        if sv:
            st.markdown(f"**Strategic Value:** {sv}")

    # --- TAB 2: RESEARCH DATA ---
    with tab2:
        st.markdown("### Research Findings")

        # Group 1: Company Intelligence
        st.markdown("#### Company Intelligence")
        _render_field(p, "company_type", "Company Type")
        _render_field(p, "program_count", "Program Count")
        _render_field(p, "region_focus", "Region Focus")
        _render_field(p, "production_scale", "Production Scale")

        # Group 2: Adoption Signals
        st.markdown("#### Adoption Signals")
        _render_field(p, "lightweighting_programs", "Lightweighting Programs")
        _render_field(p, "rd_budget", "R&D Budget")
        _render_field(p, "recent_acquisitions", "Recent Acquisitions")

        # Group 3: Materials & Procurement
        st.markdown("#### Materials & Procurement")
        _render_field(p, "materials_adoption_role", "Materials Adoption Role")

        suppliers_val = _display_value(p.get("current_material_suppliers", ""))
        if suppliers_val:
            st.info(f"**Current Suppliers:** {suppliers_val}")
        else:
            st.markdown("**Current Suppliers:** *Not found*")

        _render_field(p, "material_spec_influence", "Material Spec Influence")

        # Group 4: Sustainability
        st.markdown("#### Sustainability")
        _render_field(p, "sustainability_initiatives", "Sustainability Initiatives")
        _render_field(p, "bio_materials_interest", "Bio-Materials Interest")

        # Contact
        st.markdown("#### Contact")
        linkedin = _display_value(p.get("linkedin_url", ""))
        if linkedin and linkedin.startswith("http"):
            st.markdown(f"**LinkedIn:** [{linkedin}]({linkedin})")
        else:
            st.markdown("**LinkedIn:** *Not found*")

    # --- TAB 3: COMPANY CONTEXT ---
    with tab3:
        st.markdown("### Company & Classification")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Company Bucket**")
            bucket = p.get("Company_Bucket", "")
            label = p.get("Company_Bucket_Label", "")
            st.markdown(f"Bucket **{bucket}** — {label}")

            st.markdown("**Function Bucket**")
            fbucket = p.get("Function_Bucket", "")
            flabel = p.get("Function_Bucket_Label", "")
            st.markdown(f"Bucket **{fbucket}** — {flabel}")

        with col2:
            st.markdown("**Enhancement Status**")
            enh = str(p.get("Enhancement_Status", "N/A"))
            if enh == "ENHANCED":
                st.success("ENHANCED — Deep research found new data")
            elif enh == "NO_NEW_DATA":
                st.warning("NO NEW DATA — Research ran but no gaps filled")
            elif enh == "NO_GAPS":
                st.info("NO GAPS — All fields already populated")
            else:
                st.markdown(enh)

            gaps = _display_value(p.get("Enhancement_Gaps_Filled", ""))
            if gaps:
                st.caption(f"Gaps filled: {gaps}")

    # --- TAB 4: OUTREACH NOTES ---
    with tab4:
        st.markdown("### Outreach Planning")
        st.markdown("*These fields are read-only. The Excel file is the source of truth.*")

        st.text_area("Mutual Connections", "", help="People who could provide warm introductions")
        st.text_area("Personalization Hook", "", help="Specific talking point for outreach")
        st.text_input("Pre-Engagement Status", "", help="Not Started / Researched / LinkedIn Sent / Meeting Set")
        st.text_area("Notes", "")
        st.info("Changes here are NOT saved. Use the Excel file for tracking.")


def _render_field(prospect, field_key, label):
    """Render a single research field with NOT_FOUND handling."""
    val = _display_value(prospect.get(field_key, ""))
    if val:
        st.markdown(f"**{label}:** {val}")
    else:
        st.markdown(f"**{label}:** *Not found*")


# =============================================================================
# PAGE 2: MATERIAL SUPPLIER INTELLIGENCE
# =============================================================================
def render_supplier_intel(df):
    """Render the Material Supplier Intelligence page."""
    st.markdown("### Material Supplier Intelligence")
    st.markdown("*Composite/polymer supplier relationships extracted from research*")

    if "current_material_suppliers" not in df.columns:
        st.warning("No supplier data found in dataset.")
        return

    # Build supplier-company mapping
    supplier_companies = {}
    prospect_suppliers = []

    for _, row in df.iterrows():
        raw = str(row.get("current_material_suppliers", ""))
        suppliers = _parse_suppliers(raw)
        if suppliers:
            company = str(row.get("Company Name", ""))
            prospect_suppliers.append({
                "Rank": int(row["Rank"]) if "Rank" in row.index else "",
                "Name": f"{row['First Name']} {row['Last Name']}",
                "Company": company,
                "Job Title": str(row.get("Job Title", "")),
                "Suppliers": ", ".join(suppliers),
                "Raw Data": raw,
            })
            for s in suppliers:
                if s not in supplier_companies:
                    supplier_companies[s] = set()
                supplier_companies[s].add(company)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Delegates with Supplier Data", len(prospect_suppliers))
    with col2:
        st.metric("Unique Suppliers Identified", len(supplier_companies))
    with col3:
        total_relationships = sum(len(comps) for comps in supplier_companies.values())
        st.metric("Supplier-Company Relationships", total_relationships)

    st.markdown("---")

    # Supplier-Company Matrix
    st.markdown("#### Supplier-Company Relationships")
    st.markdown("*Which material suppliers serve which aerospace companies*")

    if supplier_companies:
        matrix_rows = []
        for supplier, companies in sorted(supplier_companies.items(), key=lambda x: -len(x[1])):
            matrix_rows.append({
                "Supplier": supplier,
                "Customer Companies": ", ".join(sorted(companies)),
                "# Companies": len(companies),
            })

        matrix_df = pd.DataFrame(matrix_rows)
        st.dataframe(matrix_df, use_container_width=True, hide_index=True)

        # Bar chart
        fig = px.bar(
            matrix_df.head(15),
            x="# Companies",
            y="Supplier",
            orientation="h",
            title="Top Suppliers by Customer Company Relationships",
            color="# Companies",
            color_continuous_scale="Blues",
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No supplier data found in the dataset.")

    st.markdown("---")

    # Delegates with supplier data
    st.markdown("#### Delegates with Supplier Data")
    if prospect_suppliers:
        pv_df = pd.DataFrame(prospect_suppliers)
        st.dataframe(
            pv_df[["Rank", "Name", "Company", "Job Title", "Suppliers"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No delegates have supplier data.")


# =============================================================================
# PAGE 3: OVERVIEW & STATS
# =============================================================================
def render_overview(top50, all_filtered):
    """Render the Overview & Stats page."""
    st.markdown("### Overview & Statistics")

    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Filtered", len(all_filtered))
    with col2:
        score_range = f"{int(top50['Priority_Score'].min())}–{int(top50['Priority_Score'].max())}"
        st.metric("TOP 50 Score Range", score_range)
    with col3:
        key_count = (all_filtered["Is_Key_Contact"] == "Y").sum()
        st.metric("Key Contacts", key_count)
    with col4:
        mat_count = (all_filtered["Materials_Adoption_Proximity"] > 0).sum()
        st.metric("Materials Targets", mat_count)
    with col5:
        companies = all_filtered["Company Name"].nunique()
        st.metric("Companies", companies)

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        if "Company_Bucket_Label" in top50.columns:
            bucket_counts = top50["Company_Bucket_Label"].value_counts()
            fig = px.pie(
                values=bucket_counts.values,
                names=bucket_counts.index,
                title="TOP 50 — Company Type Distribution",
            )
            fig.update_traces(textposition="inside", textinfo="value+label")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        avg_title = top50["Title_Score"].mean()
        avg_company = top50["Company_Score"].mean()
        avg_prox = top50["Materials_Adoption_Proximity"].mean()
        avg_boost = top50["Research_Boost"].mean()

        fig = go.Figure(data=[
            go.Bar(name="Title Score", x=["Avg Score"], y=[avg_title]),
            go.Bar(name="Company Score", x=["Avg Score"], y=[avg_company]),
            go.Bar(name="Materials Proximity", x=["Avg Score"], y=[avg_prox]),
            go.Bar(name="Research Boosts", x=["Avg Score"], y=[avg_boost]),
        ])
        fig.update_layout(
            barmode="stack",
            title="TOP 50 — Average Score Components",
            yaxis_title="Points",
        )
        st.plotly_chart(fig, use_container_width=True)

    # More charts
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        company_counts = top50["Company Name"].value_counts().head(15)
        fig = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation="h",
            title="Top 15 Companies by Delegate Count (TOP 50)",
            labels={"x": "Delegates", "y": "Company"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            all_filtered,
            x="Priority_Score",
            nbins=30,
            title=f"Score Distribution (All {len(all_filtered)} Filtered)",
            color_discrete_sequence=["#1e40af"],
        )
        cutoff = top50["Priority_Score"].min()
        fig.add_vline(
            x=cutoff,
            line_dash="dash",
            line_color="red",
            annotation_text=f"TOP 50 cutoff ({int(cutoff)})",
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

    # Materials Adoption Proximity distribution
    st.markdown("---")
    st.markdown("#### Materials Adoption Proximity Distribution (TOP 50)")
    prox = top50["Materials_Adoption_Proximity"]
    bins = {
        "25 (Direct Materials)": (prox == 25).sum(),
        "12-24 (Adjacent)": ((prox >= 12) & (prox < 25)).sum(),
        "1-11 (Partial)": ((prox >= 1) & (prox < 12)).sum(),
        "0 (None)": (prox == 0).sum(),
    }
    fig = px.bar(
        x=list(bins.keys()),
        y=list(bins.values()),
        title="How Close Are TOP 50 Delegates to Material Selection Decisions?",
        labels={"x": "Proximity Level", "y": "Count"},
        color=list(bins.keys()),
        color_discrete_map={
            "25 (Direct Materials)": "#1a7431",
            "12-24 (Adjacent)": "#3498db",
            "1-11 (Partial)": "#f39c12",
            "0 (None)": "#bdc3c7",
        },
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGE 4: METHODOLOGY
# =============================================================================
METHODOLOGY_TEXT = """
## Research Methodology

### Overview
This tool transforms ~500 AEROCOM 2025 delegates into a prioritized TOP 50 engagement list for Nyriom Technologies' NyrionPlex advanced bio-polymer composite system. The pipeline uses AI-powered research and multi-factor scoring to identify the people most likely to influence material adoption decisions.

### The 5-Step Pipeline

```
~500 delegates (AEROCOM conference roster)
  |
  +-- Step 1: Categorize by company type + job function, filter irrelevant
  |     Three-layer filter: company whitelist + role exclusion + score >= 40
  |
  v ~250 relevant delegates
  |
  +-- Step 2: AI-powered research (13 variables per delegate)
  |     Supports: Perplexity Sonar, Ollama (local LLM), or pre-generated demo data
  |
  +-- Step 3: Multi-factor scoring + ranking
  |
  v TOP 60 scored delegates
  |
  +-- Step 4: Deep research on TOP 60 (fill data gaps)
  |     Uses Sonar Pro, local LLM, or demo data
  |
  +-- Step 5: Re-score with enhanced data, produce TOP 50
  v
  FINAL TOP 50 deliverable
```

### Research Backend Architecture

The pipeline supports three interchangeable research backends:

| Backend | Model | Web Search | Cost | Use Case |
|---------|-------|------------|------|----------|
| **Perplexity Sonar** | sonar / sonar-pro | Yes | ~$1.85 | Production — verified web research |
| **Ollama** | mistral / llama3 | No | Free | Local inference — open-source showcase |
| **Demo** | Pre-generated JSON | N/A | Free | Portfolio demo — instant, no setup |

All backends implement a common `ResearchBackend` interface, making it easy to add new providers.

### Scoring Formula (max ~155 points)

**Priority Score = Title Score + Company Score + Materials Adoption Proximity + Research Boosts + Key Contact Bonus**

| Component | Max Points | What It Measures |
|-----------|-----------|-----------------|
| **Title Score** | 0-30 | Job title seniority (CEO=30, VP=22, Director=12) |
| **Company Score** | 0-40 | Company type relevance (Material Supplier=40, OEM=35, Tier 1=30) |
| **Materials Adoption Proximity** | 0-25 | How close to material selection decisions |
| **Research Boosts** | 0-30+ | Lightweighting +15, Sustainability +10, R&D +10, etc. |
| **Key Contact Bonus** | 0 or 30 | Pre-identified Nyriom targets |

### Materials Adoption Proximity (Key Differentiator)

Measures how close each person is to specifying or approving new materials:

| Signal | Points | Example |
|--------|--------|---------|
| Materials engineering title | +25 | "VP Materials & Processes" |
| Procurement title | +25 | "Director Composite Procurement" |
| Material supplier org | +20 | Hexcel, Toray, Solvay employees |
| Manufacturing title | +15 | "VP Manufacturing" |
| Sustainability title | +12 | "Head of Sustainable Materials" |
| Material spec influence | +10 | From research data |
| Materials adoption role | +10 | From research data |

### 13 Research Variables

| Category | Variables |
|----------|----------|
| **Company Intel** | company_type, program_count, region_focus, production_scale |
| **Adoption Signals** | lightweighting_programs, rd_budget, recent_acquisitions |
| **Materials & Procurement** | materials_adoption_role, current_material_suppliers, material_spec_influence |
| **Sustainability** | sustainability_initiatives, bio_materials_interest |
| **Contact** | linkedin_url |

### Disclosure

This is a portfolio demonstration project. AEROCOM 2025 is a fictional conference. Company names are real aerospace/composites industry participants; individual delegate names are generated. The pipeline architecture, scoring logic, and code are production-representative.
"""


def render_methodology():
    """Render the Methodology page."""
    st.markdown(METHODOLOGY_TEXT)


# =============================================================================
# MAIN
# =============================================================================
def main():
    st.set_page_config(
        page_title="AEROCOM 2025 - Nyriom Technologies",
        page_icon="N",
        layout="wide",
    )

    if not check_password():
        return

    st.title("AEROCOM 2025 — Delegate Prioritization")
    st.markdown("*Advanced Composites Conference, Toulouse | Nyriom Technologies / NyrionPlex*")

    # Load data
    top50, all_filtered, materials_targets = load_data()

    if top50 is None:
        st.error(f"Data file not found: {DATA_FILE}")
        st.info("Run the AEROCOM pipeline (steps 1-5) first to generate the prioritized list.")
        return

    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigation",
        ["TOP 50 Delegates", "Supplier Intelligence", "Overview & Stats", "Methodology"],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")
    st.sidebar.metric("Total Filtered", len(all_filtered))
    st.sidebar.metric("TOP 50", len(top50))

    mat_count = (all_filtered["Materials_Adoption_Proximity"] > 0).sum()
    st.sidebar.metric("Materials Targets", mat_count)

    key_count = (all_filtered["Is_Key_Contact"] == "Y").sum()
    st.sidebar.metric("Key Contacts", key_count)

    # Render selected page
    if page == "TOP 50 Delegates":
        render_top50(top50)
    elif page == "Supplier Intelligence":
        render_supplier_intel(top50)
    elif page == "Overview & Stats":
        render_overview(top50, all_filtered)
    else:
        render_methodology()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Research: Perplexity AI / Ollama / Demo*")
    st.sidebar.markdown("*Source: AEROCOM 2025 Delegate Roster*")
    st.sidebar.markdown("*Built with Streamlit*")


if __name__ == "__main__":
    main()
