"""
Step 5: Final Ranking — AEROCOM 2025 TOP 50
============================================

Re-scores all delegates with enhanced data, then produces the final
deliverable: AEROCOM_2025_FINAL_TOP50.xlsx

Output sheets:
- TOP_50: Ranked #1 through #50 with full scoring breakdown
- ALL_FILTERED: All ~250 with updated scores
- BY_COMPANY: Grouped (e.g., "3 people from Airbus — approach together")
- MATERIALS_TARGETS: Materials-specific view
- SUMMARY: Stats and methodology
- CRM_READY: Formatted for CSV export + CRM import

Usage:
    python step5_final_rank.py
    python step5_final_rank.py --input custom.xlsx --output custom_output.xlsx
"""

import argparse
from pathlib import Path

import pandas as pd

from nyriom_config import (
    CHECKPOINT2_SCORED, CHECKPOINT3_ENHANCED, FINAL_OUTPUT,
    OUTPUT_DIR, TIER_NAMES, EXPANSION_VARIABLES,
    COL_FIRST_NAME, COL_LAST_NAME, COL_JOB_TITLE, COL_COMPANY,
)
from step3_score import AerocomScorer


def create_final_workbook(df: pd.DataFrame, output_path: Path):
    """Create the final deliverable Excel workbook."""
    print(f"\nCreating final deliverable: {output_path}")

    # Define column groups
    identity_cols = [
        COL_FIRST_NAME, COL_LAST_NAME, COL_JOB_TITLE, COL_COMPANY,
    ]

    scoring_cols = [
        "Rank", "Priority_Score", "Priority_Tier", "Tier_Name",
        "Strategic_Value",
        "Title_Score", "Company_Score", "Materials_Adoption_Proximity",
        "Research_Boost", "Is_Key_Contact",
    ]

    detail_cols = [
        "Company_Bucket", "Company_Bucket_Label",
        "Function_Bucket", "Function_Bucket_Label",
        "Materials_Reason", "Boost_Details",
        "Sustainability_Flag", "Lightweighting_Flag", "RD_Budget_Flag",
    ]

    research_cols = [c for c in EXPANSION_VARIABLES if c in df.columns]
    meta_cols = [c for c in ["Research_Status", "Verification_Confidence",
                              "Enhancement_Status", "Enhancement_Gaps_Filled",
                              "source_urls"] if c in df.columns]

    # Add Rank column
    df = df.copy()
    df["Rank"] = range(1, len(df) + 1)

    # Build ordered column list
    all_cols = identity_cols + scoring_cols + detail_cols + research_cols + meta_cols
    for c in df.columns:
        if c not in all_cols:
            all_cols.append(c)
    all_cols = [c for c in all_cols if c in df.columns]

    # ── TOP_50 ──
    top50 = df.head(50)[all_cols]

    # ── ALL_FILTERED ──
    all_filtered = df[all_cols]

    # ── BY_COMPANY ──
    company_counts = df[COL_COMPANY].value_counts()
    multi = company_counts[company_counts > 1].index.tolist()
    by_company = df[df[COL_COMPANY].isin(multi)].copy()
    by_company = by_company.sort_values(
        [COL_COMPANY, "Priority_Score"], ascending=[True, False]
    )
    by_company["People_at_Company"] = by_company[COL_COMPANY].map(company_counts)
    by_cols = [COL_COMPANY, "People_at_Company"] + [c for c in all_cols if c != COL_COMPANY]
    by_cols = [c for c in by_cols if c in by_company.columns]
    by_company = by_company[by_cols]

    # ── MATERIALS_TARGETS ──
    materials = df[df["Materials_Adoption_Proximity"] > 0].copy()
    materials = materials.sort_values("Priority_Score", ascending=False)
    materials = materials[all_cols]

    # ── SUMMARY ──
    summary_rows = []
    summary_rows.append({"Metric": "=== AEROCOM 2025 Final Results ===", "Value": ""})
    summary_rows.append({"Metric": "Total Delegates Scored", "Value": len(df)})
    summary_rows.append({"Metric": "", "Value": ""})

    summary_rows.append({"Metric": "--- Tier Distribution ---", "Value": ""})
    for tier in [1, 2, 3, 4]:
        count = (df["Priority_Tier"] == tier).sum()
        summary_rows.append({
            "Metric": f"  Tier {tier} - {TIER_NAMES[tier]}",
            "Value": count,
        })

    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "--- Key Metrics ---", "Value": ""})
    summary_rows.append({"Metric": "Key Contacts Found", "Value": (df["Is_Key_Contact"] == "Y").sum()})
    summary_rows.append({"Metric": "Materials Targets", "Value": len(materials)})
    summary_rows.append({"Metric": "Sustainability Flagged", "Value": (df.get("Sustainability_Flag", pd.Series()) == "Y").sum()})
    summary_rows.append({"Metric": "Lightweighting Flagged", "Value": (df.get("Lightweighting_Flag", pd.Series()) == "Y").sum()})
    summary_rows.append({"Metric": "R&D Budget Flagged", "Value": (df.get("RD_Budget_Flag", pd.Series()) == "Y").sum()})
    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "--- Score Distribution ---", "Value": ""})
    summary_rows.append({"Metric": "Highest Score", "Value": df["Priority_Score"].max()})
    summary_rows.append({"Metric": "#1 Delegate", "Value": f"{df.iloc[0].get(COL_FIRST_NAME, '')} {df.iloc[0].get(COL_LAST_NAME, '')} @ {df.iloc[0].get(COL_COMPANY, '')}"})
    summary_rows.append({"Metric": "Median Score (TOP 50)", "Value": round(df.head(50)["Priority_Score"].median(), 1)})
    summary_rows.append({"Metric": "Score of #50", "Value": df.iloc[49]["Priority_Score"] if len(df) >= 50 else "N/A"})
    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "--- Companies with Most People ---", "Value": ""})
    for comp, cnt in company_counts.head(10).items():
        summary_rows.append({"Metric": f"  {comp}", "Value": cnt})

    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "--- Scoring Methodology ---", "Value": ""})
    summary_rows.append({"Metric": "Title Score", "Value": "0-30 pts (seniority)"})
    summary_rows.append({"Metric": "Company Score", "Value": "0-40 pts (company relevance)"})
    summary_rows.append({"Metric": "Materials Adoption Proximity", "Value": "0-25 pts (materials decision closeness)"})
    summary_rows.append({"Metric": "Research Boosts", "Value": "0-30+ pts (lightweighting, sustainability, R&D, etc.)"})
    summary_rows.append({"Metric": "Key Contact Bonus", "Value": "+30 pts (pre-identified targets)"})
    summary_rows.append({"Metric": "Tier 1 Threshold", "Value": ">=75 or Key Contact"})
    summary_rows.append({"Metric": "Tier 2 Threshold", "Value": "55-74"})
    summary_rows.append({"Metric": "Tier 3 Threshold", "Value": "35-54"})

    summary_df = pd.DataFrame(summary_rows)

    # ── CRM_READY ──
    crm_cols = {
        COL_FIRST_NAME: "First Name",
        COL_LAST_NAME: "Last Name",
        COL_JOB_TITLE: "Job Title",
        COL_COMPANY: "Company Name",
    }

    crm_custom = {
        "Priority_Score": "AEROCOM Priority Score",
        "Priority_Tier": "AEROCOM Priority Tier",
        "Tier_Name": "AEROCOM Tier Name",
        "Strategic_Value": "AEROCOM Strategic Value",
        "Company_Bucket_Label": "AEROCOM Company Type",
        "Materials_Adoption_Proximity": "AEROCOM Materials Proximity",
        "Lightweighting_Flag": "AEROCOM Lightweighting Opportunity",
        "Sustainability_Flag": "AEROCOM Sustainability Aligned",
        "RD_Budget_Flag": "AEROCOM R&D Budget Signal",
        "Is_Key_Contact": "AEROCOM Key Contact",
    }

    for var in EXPANSION_VARIABLES:
        if var in df.columns:
            crm_custom[var] = f"AEROCOM {var.replace('_', ' ').title()}"

    # Build CRM DataFrame (TOP 50 only)
    crm_df = df.head(50).copy()
    rename_map = {}
    keep_cols = []
    for orig, new in {**crm_cols, **crm_custom}.items():
        if orig in crm_df.columns:
            rename_map[orig] = new
            keep_cols.append(orig)

    crm_df = crm_df[keep_cols].rename(columns=rename_map)

    # Write all sheets
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        top50.to_excel(writer, sheet_name="TOP_50", index=False)
        all_filtered.to_excel(writer, sheet_name="ALL_FILTERED", index=False)
        by_company.to_excel(writer, sheet_name="BY_COMPANY", index=False)
        materials.to_excel(writer, sheet_name="MATERIALS_TARGETS", index=False)
        summary_df.to_excel(writer, sheet_name="SUMMARY", index=False)
        crm_df.to_excel(writer, sheet_name="CRM_READY", index=False)

    print(f"  - TOP_50: {len(top50)} rows (ranked #1-#50)")
    print(f"  - ALL_FILTERED: {len(all_filtered)} rows")
    print(f"  - BY_COMPANY: {len(by_company)} rows")
    print(f"  - MATERIALS_TARGETS: {len(materials)} rows")
    print(f"  - SUMMARY: Stats + methodology")
    print(f"  - CRM_READY: {len(crm_df)} rows (for CSV export)")


def main():
    parser = argparse.ArgumentParser(description="AEROCOM 2025 Final Ranking")
    parser.add_argument("--input", type=str, default=None,
                        help="Custom input file path")
    parser.add_argument("--output", type=str, default=None,
                        help="Custom output file path")
    args = parser.parse_args()

    # Determine input — prefer enhanced data
    if args.input:
        input_file = Path(args.input)
    elif CHECKPOINT3_ENHANCED.exists():
        input_file = CHECKPOINT3_ENHANCED
        print("Using enhanced data (checkpoint 3)")
    elif CHECKPOINT2_SCORED.exists():
        input_file = CHECKPOINT2_SCORED
        print("No enhanced data found — using scored data (checkpoint 2)")
        print("  (Run step4_enhance.py first for deep research enhancement)")
    else:
        print("ERROR: No input data found.")
        print("Run step3_score.py first.")
        return

    # Load data
    print(f"\nLoading data from: {input_file}")
    try:
        df = pd.read_excel(input_file)
    except Exception:
        df = pd.read_excel(input_file, sheet_name="ALL_FILTERED")
    print(f"Loaded {len(df)} delegates")

    # Re-score with enhanced data
    print("\nRe-scoring with enhanced data...")
    scorer = AerocomScorer()
    scored_df = scorer.score_all(df)

    # Output
    output_path = Path(args.output) if args.output else FINAL_OUTPUT
    create_final_workbook(scored_df, output_path)

    # Print final summary
    print(f"\n{'='*60}")
    print("FINAL DELIVERABLE COMPLETE")
    print(f"{'='*60}")

    for tier in [1, 2, 3, 4]:
        count = (scored_df["Priority_Tier"] == tier).sum()
        print(f"  Tier {tier} ({TIER_NAMES[tier]}): {count}")

    print(f"\n--- TOP 15 Delegates ---")
    for i, (_, row) in enumerate(scored_df.head(15).iterrows()):
        key = "***" if row.get("Is_Key_Contact") == "Y" else "   "
        print(f"  #{i+1:2d} {key} Score={row['Priority_Score']:3.0f} | "
              f"{row.get(COL_FIRST_NAME, '')} {row.get(COL_LAST_NAME, '')} | "
              f"{str(row.get(COL_JOB_TITLE, ''))[:35]} | "
              f"{str(row.get(COL_COMPANY, ''))[:25]}")

    materials_count = (scored_df["Materials_Adoption_Proximity"] > 0).sum()
    print(f"\n  Materials Targets: {materials_count}")
    print(f"  Highest Score: {scored_df['Priority_Score'].max()}")
    if len(scored_df) >= 50:
        print(f"  Score of #50: {scored_df.iloc[49]['Priority_Score']}")

    print(f"\n  Output: {output_path}")


if __name__ == "__main__":
    main()
