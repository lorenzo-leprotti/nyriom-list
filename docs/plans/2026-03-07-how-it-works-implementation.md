# "How It Works" Page — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an interactive "How It Works" page to the Streamlit dashboard that walks users through the 5-step pipeline with visualizations and a backend comparison panel.

**Architecture:** Single new function `render_how_it_works()` added to `dashboard.py`, plus sidebar nav update. Uses existing pipeline output data for real metrics. Backend comparison uses hardcoded example data (no live API calls). All in one file — no new dependencies.

**Tech Stack:** Streamlit, Plotly, Pandas (all already installed)

**Design doc:** `docs/plans/2026-03-07-how-it-works-page-design.md`

---

### Task 1: Add page skeleton and sidebar nav

**Files:**
- Modify: `dashboard.py:778-802` (sidebar nav + page routing)
- Modify: `dashboard.py:748-750` (add new render function)

**Step 1: Add the `render_how_it_works()` stub**

After `render_methodology()` (line 750), add:

```python
def render_how_it_works(top50, all_filtered):
    """Render the How It Works page — interactive pipeline explainer."""
    st.markdown("### How It Works")
    st.markdown("*A 5-step AI pipeline from raw conference roster to prioritized engagement list*")
    st.info("Pipeline explainer coming soon.")
```

**Step 2: Update sidebar nav**

In `main()`, update the sidebar radio (line 778-780) to add the new page:

```python
    page = st.sidebar.radio(
        "Navigation",
        ["How It Works", "TOP 50 Delegates", "Supplier Intelligence", "Overview & Stats", "Methodology"],
    )
```

And update the page routing (lines 794-802) to add the new branch:

```python
    if page == "How It Works":
        render_how_it_works(top50, all_filtered)
    elif page == "TOP 50 Delegates":
        render_top50(top50)
    elif page == "Supplier Intelligence":
        render_supplier_intel(top50)
    elif page == "Overview & Stats":
        render_overview(top50, all_filtered)
    else:
        render_methodology()
```

**Step 3: Verify**

Run: `streamlit run dashboard.py` — navigate to "How It Works", should show placeholder text.

**Step 4: Commit**

```bash
git add dashboard.py
git commit -m "feat: add How It Works page skeleton to dashboard"
```

---

### Task 2: Build step selector and input/output metrics

**Files:**
- Modify: `dashboard.py` — expand `render_how_it_works()`

**Step 1: Replace the stub with the step selector and metrics display**

Replace the `render_how_it_works` function with:

```python
def render_how_it_works(top50, all_filtered):
    """Render the How It Works page — interactive pipeline explainer."""
    st.markdown("### How It Works")
    st.markdown("*A 5-step AI pipeline from raw conference roster to prioritized engagement list*")

    # Step definitions
    steps = {
        "Step 1: Filter": {
            "title": "Filter & Categorize",
            "desc": "Assign company-type and job-function buckets, then apply a three-layer filter to remove irrelevant delegates.",
            "input_label": "Raw Delegates",
            "input_count": 522,
            "output_label": "Filtered",
            "output_count": len(all_filtered),
        },
        "Step 2: Research": {
            "title": "AI Research",
            "desc": "Enrich each filtered delegate with 13 research variables using an AI backend.",
            "input_label": "Filtered",
            "input_count": len(all_filtered),
            "output_label": "Researched",
            "output_count": len(all_filtered),
            "has_backend_panel": True,
        },
        "Step 3: Score": {
            "title": "Multi-Factor Scoring",
            "desc": "Score each delegate on Title + Company + Materials Proximity + Research Boosts, then rank.",
            "input_label": "Researched",
            "input_count": len(all_filtered),
            "output_label": "Top 60 Selected",
            "output_count": 60,
        },
        "Step 4: Enhance": {
            "title": "Deep Research",
            "desc": "Fill data gaps for the top 60 delegates on 6 priority fields using a deeper AI pass.",
            "input_label": "Top 60",
            "input_count": 60,
            "output_label": "Enhanced",
            "output_count": 60,
            "has_backend_panel": True,
        },
        "Step 5: Rank": {
            "title": "Final Ranking",
            "desc": "Re-score with enhanced data and produce the TOP 50 deliverable.",
            "input_label": "Re-scored",
            "input_count": len(all_filtered),
            "output_label": "TOP 50",
            "output_count": len(top50),
        },
    }

    # Horizontal step selector
    step_keys = list(steps.keys())
    selected = st.radio("Pipeline Step", step_keys, horizontal=True, label_visibility="collapsed")
    step = steps[selected]

    st.markdown(f"## {step['title']}")
    st.markdown(step["desc"])

    # Input → Output metrics
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.metric("Input", f"{step['input_count']} delegates", label_visibility="visible")
        st.caption(step["input_label"])
    with col2:
        st.markdown("<div style='text-align:center; font-size:2rem; padding-top:1rem;'>→</div>", unsafe_allow_html=True)
    with col3:
        st.metric("Output", f"{step['output_count']} delegates", label_visibility="visible")
        st.caption(step["output_label"])

    st.markdown("---")
```

**Step 2: Verify**

Run: `streamlit run dashboard.py` — click through all 5 steps, each should show title, description, and input/output metrics.

**Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: add step selector and input/output metrics to How It Works"
```

---

### Task 3: Step 1 visualization — bucket distribution chart

**Files:**
- Modify: `dashboard.py` — add visualization logic inside `render_how_it_works()`

**Step 1: Add Step 1 visualization**

After the `st.markdown("---")` at the end of `render_how_it_works`, add:

```python
    # Step-specific visualizations
    if selected == "Step 1: Filter":
        _render_step1_viz(all_filtered)

# Place this as a new top-level function before render_how_it_works:
def _render_step1_viz(all_filtered):
    """Step 1 visualization: bucket distribution + filter explanation."""
    st.markdown("#### Company Bucket Distribution")

    # Count delegates per bucket in filtered set
    bucket_order = ["A", "B", "C", "D", "E", "F", "G"]
    bucket_labels = {
        "A": "Aerospace OEM",
        "B": "Tier 1 Supplier",
        "C": "Tier 2-3 Specialty",
        "D": "Material Supplier",
        "E": "Airline / MRO",
        "F": "Investment / PE",
        "G": "Engineering / Research",
    }
    excluded_labels = {
        "H": "Legal / Consulting",
        "I": "Media / Events",
        "J": "Academic",
    }

    bucket_counts = all_filtered["Company_Bucket"].value_counts()
    chart_data = []
    for b in bucket_order:
        count = bucket_counts.get(b, 0)
        chart_data.append({"Bucket": f"{b}: {bucket_labels[b]}", "Count": count, "Status": "Included"})
    for b, label in excluded_labels.items():
        chart_data.append({"Bucket": f"{b}: {label}", "Count": 0, "Status": "Excluded"})

    import pandas as pd
    chart_df = pd.DataFrame(chart_data)
    color_map = {"Included": "#1e40af", "Excluded": "#d1d5db"}
    fig = px.bar(
        chart_df, x="Count", y="Bucket", orientation="h",
        color="Status", color_discrete_map=color_map,
        title="Delegates per Company Bucket (after filtering)",
    )
    fig.update_layout(showlegend=True, height=350, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    # Filter explanation
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Layer 1: Company Whitelist**")
        st.markdown("Only keep buckets A–G (aerospace-related)")
    with col2:
        st.markdown("**Layer 2: Role Exclusion**")
        st.markdown("Remove junior/irrelevant roles (bucket 10)")
    with col3:
        st.markdown("**Layer 3: Minimum Score**")
        st.markdown("Relevance score must be ≥ 40")
```

**Step 2: Verify**

Run: `streamlit run dashboard.py` → How It Works → Step 1. Should show horizontal bar chart with company buckets and three-column filter explanation.

**Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: add Step 1 bucket distribution chart"
```

---

### Task 4: Step 3 visualization — score distribution + breakdown

**Files:**
- Modify: `dashboard.py` — add `_render_step3_viz()`

**Step 1: Add Step 3 visualization**

Add routing in `render_how_it_works` after the Step 1 block:

```python
    elif selected == "Step 3: Score":
        _render_step3_viz(all_filtered, top50)
```

Add new function:

```python
def _render_step3_viz(all_filtered, top50):
    """Step 3 visualization: score distribution histogram + breakdown example."""
    st.markdown("#### Score Distribution")

    # Histogram of all scores with top-60 cutoff
    scores = all_filtered["Priority_Score"].dropna()
    top60_cutoff = scores.nlargest(60).min()

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=scores, nbinsx=25, marker_color="#1e40af", name="All Delegates"))
    fig.add_vline(x=top60_cutoff, line_dash="dash", line_color="red",
                  annotation_text=f"Top 60 cutoff: {int(top60_cutoff)}", annotation_position="top right")
    fig.update_layout(
        xaxis_title="Priority Score", yaxis_title="Count",
        title="Score Distribution (249 delegates)", height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Score breakdown example — pick the #1 ranked delegate
    st.markdown("#### Score Breakdown Example")
    example = top50.iloc[0]
    name = f"{example['First Name']} {example['Last Name']}"
    st.markdown(f"**{name}** — {example['Job Title']}, {example['Company Name']}")

    components = {
        "Title Score": example.get("Title_Score", 0),
        "Company Score": example.get("Company_Score", 0),
        "Materials Proximity": example.get("Materials_Adoption_Proximity", 0),
        "Research Boost": example.get("Research_Boost", 0),
        "Key Contact Bonus": example.get("Key_Bonus", 0),
    }
    comp_df = pd.DataFrame({"Component": components.keys(), "Points": components.values()})
    fig2 = px.bar(comp_df, x="Points", y="Component", orientation="h",
                  color_discrete_sequence=["#1e40af"], title=f"Score Breakdown: {int(example['Priority_Score'])} total")
    fig2.update_layout(height=280, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, use_container_width=True)
```

**Step 2: Verify**

Run dashboard → How It Works → Step 3. Should show histogram with cutoff line and score breakdown for #1 delegate.

**Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: add Step 3 score distribution and breakdown chart"
```

---

### Task 5: Step 5 visualization — top 10 leaderboard

**Files:**
- Modify: `dashboard.py` — add `_render_step5_viz()`

**Step 1: Add Step 5 visualization**

Add routing:

```python
    elif selected == "Step 5: Rank":
        _render_step5_viz(top50)
```

Add function:

```python
def _render_step5_viz(top50):
    """Step 5 visualization: top 10 leaderboard + output summary."""
    st.markdown("#### Top 10 Delegates")

    top10 = top50.head(10).copy()
    top10["Name"] = top10["First Name"] + " " + top10["Last Name"]
    top10["Label"] = top10["Name"] + " — " + top10["Company Name"]

    fig = px.bar(
        top10, x="Priority_Score", y="Label", orientation="h",
        color_discrete_sequence=["#1e40af"],
        title="Top 10 by Priority Score",
    )
    fig.update_layout(height=400, yaxis=dict(autorange="reversed"), xaxis_title="Score")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Final Output")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Excel Workbook** — 6 sheets:")
        st.markdown("- TOP_50 — ranked engagement list")
        st.markdown("- ALL_FILTERED — full 249 scored")
        st.markdown("- BY_COMPANY — grouped view")
        st.markdown("- MATERIALS_TARGETS — materials-adjacent roles")
        st.markdown("- SUMMARY — statistics")
        st.markdown("- CRM_READY — import-ready format")
    with col2:
        st.markdown("**Interactive Dashboard** — this app:")
        st.markdown("- Sortable/filterable delegate table")
        st.markdown("- Prospect detail cards")
        st.markdown("- Supplier intelligence mapping")
        st.markdown("- Overview statistics & charts")
```

**Step 2: Verify**

Run dashboard → How It Works → Step 5. Should show top 10 bar chart and output summary.

**Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: add Step 5 top 10 leaderboard"
```

---

### Task 6: Steps 2 & 4 — fill rate charts

**Files:**
- Modify: `dashboard.py` — add `_render_step2_viz()` and `_render_step4_viz()`

**Step 1: Add Step 2 fill rate chart**

Add routing:

```python
    elif selected == "Step 2: Research":
        _render_step2_viz(all_filtered)
```

Add function:

```python
def _render_step2_viz(all_filtered):
    """Step 2 visualization: research variable fill rates."""
    st.markdown("#### Research Variable Fill Rates")
    st.markdown("Each delegate is enriched with 13 variables. Fill rate = % of delegates where data was found.")

    research_vars = [
        ("company_type", "Company Type"),
        ("program_count", "Program Count"),
        ("region_focus", "Region Focus"),
        ("lightweighting_programs", "Lightweighting Programs"),
        ("sustainability_initiatives", "Sustainability Initiatives"),
        ("production_scale", "Production Scale"),
        ("linkedin_url", "LinkedIn URL"),
        ("materials_adoption_role", "Materials Adoption Role"),
        ("current_material_suppliers", "Current Suppliers"),
        ("rd_budget", "R&D Budget"),
        ("material_spec_influence", "Material Spec Influence"),
        ("recent_acquisitions", "Recent Acquisitions"),
        ("bio_materials_interest", "Bio-Materials Interest"),
    ]

    fill_data = []
    for col, label in research_vars:
        if col in all_filtered.columns:
            total = len(all_filtered)
            filled = all_filtered[col].apply(
                lambda x: bool(x) and str(x).strip() != "" and not str(x).lower().startswith("not_found")
            ).sum()
            fill_data.append({"Variable": label, "Fill Rate": round(filled / total * 100, 1)})

    fill_df = pd.DataFrame(fill_data)
    fig = px.bar(
        fill_df, x="Fill Rate", y="Variable", orientation="h",
        color_discrete_sequence=["#1e40af"],
        title="Fill Rate by Research Variable (%)",
        range_x=[0, 100],
    )
    fig.update_layout(height=450, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    # Backend comparison panel
    _render_backend_panel("research")
```

**Step 2: Add Step 4 fill rate before/after chart**

Add routing:

```python
    elif selected == "Step 4: Enhance":
        _render_step4_viz(all_filtered)
```

Add function:

```python
def _render_step4_viz(all_filtered):
    """Step 4 visualization: enhancement fill rate improvement on 6 gap fields."""
    st.markdown("#### Enhancement Impact — 6 Priority Fields")
    st.markdown("Deep research targets data gaps in the top 60 delegates.")

    gap_fields = [
        ("materials_adoption_role", "Materials Adoption Role"),
        ("current_material_suppliers", "Current Suppliers"),
        ("lightweighting_programs", "Lightweighting Programs"),
        ("rd_budget", "R&D Budget"),
        ("bio_materials_interest", "Bio-Materials Interest"),
        ("linkedin_url", "LinkedIn URL"),
    ]

    # Compare enhanced (top 60) vs non-enhanced
    enhanced = all_filtered[all_filtered["Enhancement_Status"] == "ENHANCED"]
    not_enhanced = all_filtered[all_filtered["Enhancement_Status"] != "ENHANCED"]

    comparison_data = []
    for col, label in gap_fields:
        if col in all_filtered.columns:
            def fill_rate(df):
                if len(df) == 0:
                    return 0
                filled = df[col].apply(
                    lambda x: bool(x) and str(x).strip() != "" and not str(x).lower().startswith("not_found")
                ).sum()
                return round(filled / len(df) * 100, 1)

            comparison_data.append({"Field": label, "Rate": fill_rate(enhanced), "Group": "After Enhancement"})
            comparison_data.append({"Field": label, "Rate": fill_rate(not_enhanced), "Group": "Before Enhancement"})

    comp_df = pd.DataFrame(comparison_data)
    fig = px.bar(
        comp_df, x="Rate", y="Field", color="Group", orientation="h",
        barmode="group", color_discrete_map={"After Enhancement": "#1e40af", "Before Enhancement": "#93c5fd"},
        title="Fill Rate Before vs After Enhancement (%)",
        range_x=[0, 100],
    )
    fig.update_layout(height=350, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    # Backend comparison panel
    _render_backend_panel("enhance")
```

**Step 3: Verify**

Run dashboard → Steps 2 and 4. Should show fill rate charts (Step 2: all 13 vars, Step 4: before/after on 6 fields).

**Step 4: Commit**

```bash
git add dashboard.py
git commit -m "feat: add Steps 2 and 4 fill rate visualizations"
```

---

### Task 7: Backend comparison panel

**Files:**
- Modify: `dashboard.py` — add `_render_backend_panel()`

**Step 1: Add the backend comparison panel function**

```python
def _render_backend_panel(context):
    """Render the backend comparison panel (used in Steps 2 and 4)."""
    st.markdown("---")
    st.markdown("#### Research Backend Comparison")
    st.markdown("The pipeline supports three interchangeable backends. Each produces the same 13-variable JSON output.")

    tab_perplexity, tab_ollama, tab_demo = st.tabs(["Perplexity (Web Search)", "Ollama (Local LLM)", "Demo (Pre-generated)"])

    # Example delegate for side-by-side
    example_name = "Erik Lindstrom — VP Materials & Processes, Airbus"

    with tab_perplexity:
        st.markdown("##### How It Works")
        cols = st.columns(5)
        flow_items = [
            ("Delegate", "Name, title, company"),
            ("→ API Call", "Perplexity Sonar"),
            ("→ Web Search", "Live internet results"),
            ("→ JSON Parse", "Extract 13 variables"),
            ("→ Output", "Verified research data"),
        ]
        for col, (title, desc) in zip(cols, flow_items):
            with col:
                st.markdown(f"**{title}**")
                st.caption(desc)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cost", "~$0.005/call")
        with col2:
            st.metric("Speed", "~4-6 sec")
        with col3:
            st.metric("Web-grounded", "Yes")

        st.markdown(f"##### Example Output: {example_name}")
        st.json({
            "company_type": "Aerospace OEM — global leader in commercial aircraft manufacturing",
            "program_count": "14 active programs including A350 XWB, A320neo, A220, RACER demonstrator",
            "lightweighting_programs": "Wing of Tomorrow program targeting 20% weight reduction via advanced composites; bio-composite research with NLR",
            "materials_adoption_role": "YES — VP Materials & Processes directly oversees material qualification and selection for all Airbus programs",
            "current_material_suppliers": "Hexcel (carbon fiber prepreg), Toray (T800/T1100), Solvay (CYCOM resins), Teijin (Tenax fiber)",
        })

    with tab_ollama:
        st.markdown("##### How It Works")
        cols = st.columns(5)
        flow_items = [
            ("Delegate", "Name, title, company"),
            ("→ Local LLM", "Ollama (Mistral, Llama, etc.)"),
            ("→ Model Knowledge", "Training data only"),
            ("→ JSON Parse", "Extract 13 variables"),
            ("→ Output", "Knowledge-based estimates"),
        ]
        for col, (title, desc) in zip(cols, flow_items):
            with col:
                st.markdown(f"**{title}**")
                st.caption(desc)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cost", "Free")
        with col2:
            st.metric("Speed", "~2-10 sec")
        with col3:
            st.metric("Web-grounded", "No")

        st.markdown(f"##### Example Output: {example_name}")
        st.json({
            "company_type": "Aerospace OEM",
            "program_count": "Multiple commercial and defense aircraft programs",
            "lightweighting_programs": "Airbus is known to invest in composite structures and weight reduction technologies",
            "materials_adoption_role": "INDIRECT — VP-level role likely influences material decisions",
            "current_material_suppliers": "NOT_FOUND",
        })
        st.caption("Note: Without web search, Ollama relies on general knowledge from training data. Results are plausible but less specific.")

    with tab_demo:
        st.markdown("##### How It Works")
        cols = st.columns(5)
        flow_items = [
            ("Delegate", "Name, title, company"),
            ("→ Key Lookup", "\"First|Last|Company\""),
            ("→ JSON File", "demo_research_data.json"),
            ("→ Direct Load", "No parsing needed"),
            ("→ Output", "Instant pre-baked data"),
        ]
        for col, (title, desc) in zip(cols, flow_items):
            with col:
                st.markdown(f"**{title}**")
                st.caption(desc)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cost", "Free")
        with col2:
            st.metric("Speed", "Instant")
        with col3:
            st.metric("Web-grounded", "N/A")

        st.markdown(f"##### Example Output: {example_name}")
        st.caption("Demo data is pre-generated to simulate realistic Perplexity output, including realistic NOT_FOUND gaps (~43% rate).")

        # Load actual demo data for this delegate
        import json
        demo_path = Path("input/demo_research_data.json")
        if demo_path.exists():
            with open(demo_path) as f:
                demo_data = json.load(f)
            key = "Erik|Lindstrom|Airbus"
            if key in demo_data:
                display = {k: v for k, v in list(demo_data[key].items())[:5]}
                st.json(display)
        else:
            st.info("Demo data file not found. Run generate_demo_data.py first.")
```

**Step 2: Verify**

Run dashboard → Steps 2 or 4. Should show three tabs with architecture flows, metrics, and example JSON output for each backend.

**Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: add backend comparison panel with architecture + examples"
```

---

### Task 8: Final integration and cleanup

**Files:**
- Modify: `dashboard.py` — ensure all routing is connected, remove any dead code

**Step 1: Ensure all step routing is complete**

The final routing block inside `render_how_it_works` should be:

```python
    # Step-specific visualizations
    if selected == "Step 1: Filter":
        _render_step1_viz(all_filtered)
    elif selected == "Step 2: Research":
        _render_step2_viz(all_filtered)
    elif selected == "Step 3: Score":
        _render_step3_viz(all_filtered, top50)
    elif selected == "Step 4: Enhance":
        _render_step4_viz(all_filtered)
    elif selected == "Step 5: Rank":
        _render_step5_viz(top50)
```

**Step 2: Verify end-to-end**

Run: `streamlit run dashboard.py`
- Click through all 5 steps — each should render its visualization
- Steps 2 and 4 should show the backend comparison tabs
- No errors in terminal

**Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: complete How It Works page with all 5 steps"
```
