"""
Step 3: Score + Rank AEROCOM 2025 Delegates
============================================

Multi-factor scoring (max ~155 points):
- Title Score (0-30): Job title seniority
- Company Score (0-40): Company bucket relevance
- Materials Adoption Proximity (0-25): How close to material selection decisions
- Research Boosts (0-30): Lightweighting, sustainability, R&D, etc.
- Key Contact Bonus (0 or 30): Pre-identified targets

Tiers: 1 (Must Meet >=75), 2 (High Priority 55-74),
       3 (Strategic 35-54), 4 (General <35)

Usage:
    python step3_score.py                          # Use researched data
    python step3_score.py --skip-research          # Score without research
    python step3_score.py --input custom.xlsx      # Custom input

Output:
    output/checkpoint2_scored.xlsx
        - TOP_60: Buffer for re-ranking after enhancement
        - ALL_FILTERED: All ~250 with scores
        - BY_COMPANY: Grouped view
        - MATERIALS_TARGETS: Materials/procurement people
        - SUMMARY: Statistics
"""

import re
import argparse
from pathlib import Path

import pandas as pd

from nyriom_config import (
    CHECKPOINT1_FILE, CHECKPOINT2_RESEARCHED, CHECKPOINT2_SCORED,
    OUTPUT_DIR, ENHANCE_TOP_N,
    TITLE_SCORES, MATERIALS_ADOPTION_TITLE_SCORES,
    COMPANY_BUCKET_SCORES, MATERIALS_SUPPLIER_ORG_BONUS,
    MATERIAL_SPEC_INFLUENCE_BONUS, MATERIALS_ADOPTION_ROLE_BONUS,
    LIGHTWEIGHTING_BOOST, SUSTAINABILITY_BOOST, CAPEX_BOOST,
    ACQUISITION_BOOST, MULTI_PROGRAM_BOOST,
    LARGE_PRODUCTION_BOOST, BIO_MATERIALS_BOOST,
    TIER_THRESHOLDS, TIER_NAMES,
    KEY_CONTACTS, KEY_CONTACT_BONUS,
    EXPANSION_VARIABLES,
    COL_FIRST_NAME, COL_LAST_NAME, COL_JOB_TITLE, COL_COMPANY,
)


def _has_data(value) -> bool:
    """Check if a research field has real data (not empty/NOT_FOUND)."""
    v = str(value).strip().lower()
    if not v or v in ["", "nan", "none"]:
        return False
    if v.startswith("not_found") or v.startswith("not found"):
        return False
    return True


class AerocomScorer:
    """Multi-factor scoring engine for AEROCOM 2025 delegates."""

    def get_title_score(self, title: str) -> tuple:
        """Calculate title score (0-30 points). Returns (score, reason)."""
        if not title or str(title).lower().strip() in ["", "nan", "none"]:
            return 0, "No title"

        title_lower = str(title).lower().strip()
        best_score = 0
        best_match = None

        # Longer matches first
        for title_key in sorted(TITLE_SCORES.keys(), key=len, reverse=True):
            if title_key in title_lower:
                if TITLE_SCORES[title_key] > best_score:
                    best_score = TITLE_SCORES[title_key]
                    best_match = title_key

        if best_match is None:
            return 0, "Title not recognized"

        return best_score, f"Matched '{best_match}'"

    def get_company_score(self, company_bucket: str) -> tuple:
        """Calculate company score (0-40 points). Returns (score, reason)."""
        score = COMPANY_BUCKET_SCORES.get(str(company_bucket), 0)
        if score > 0:
            return score, f"Bucket {company_bucket} ({score}pts)"
        return 0, "No company bucket match"

    def get_materials_adoption_proximity(self, row: dict) -> tuple:
        """
        Calculate Materials Adoption Proximity score (0-25 points).
        This is the key differentiator for composites/bio-polymer sales.
        Returns (score, reason).
        """
        title = str(row.get(COL_JOB_TITLE, "")).lower()
        company_bucket = str(row.get("Company_Bucket", ""))
        score = 0
        reasons = []

        # 1. Title-based materials adoption proximity
        best_title_score = 0
        best_title_match = None
        for pattern, pts in MATERIALS_ADOPTION_TITLE_SCORES.items():
            if pattern in title:
                if pts > best_title_score:
                    best_title_score = pts
                    best_title_match = pattern

        if best_title_match:
            score += best_title_score
            reasons.append(f"Title '{best_title_match}' +{best_title_score}")

        # 2. Material supplier organization bonus
        if company_bucket == "D":
            bonus = min(MATERIALS_SUPPLIER_ORG_BONUS, 25 - score)
            if bonus > 0:
                score += bonus
                reasons.append(f"Material supplier org +{bonus}")

        # 3. Research-based boosts
        adoption_role = str(row.get("materials_adoption_role", "")).lower()
        if _has_data(adoption_role) and "yes" in adoption_role:
            bonus = min(MATERIALS_ADOPTION_ROLE_BONUS, 25 - score)
            if bonus > 0:
                score += bonus
                reasons.append(f"Materials adoption role confirmed +{bonus}")

        spec_influence = str(row.get("material_spec_influence", "")).lower()
        if _has_data(spec_influence) and "yes" in spec_influence:
            bonus = min(MATERIAL_SPEC_INFLUENCE_BONUS, 25 - score)
            if bonus > 0:
                score += bonus
                reasons.append(f"Material spec influence +{bonus}")

        # Cap at 25
        score = min(score, 25)

        reason = "; ".join(reasons) if reasons else "No materials adoption proximity"
        return score, reason

    def get_research_boosts(self, row: dict) -> tuple:
        """Calculate research-based boosts (0-30+ points). Returns (total, details)."""
        boosts = []
        total = 0

        # Lightweighting programs
        lightweighting = str(row.get("lightweighting_programs", "")).lower()
        if _has_data(lightweighting):
            active_kw = ["2024", "2025", "2026", "2027", "planned", "underway",
                         "composite", "carbon fiber", "weight reduction",
                         "lightweighting", "new material"]
            if any(kw in lightweighting for kw in active_kw):
                total += LIGHTWEIGHTING_BOOST
                boosts.append(f"Lightweighting +{LIGHTWEIGHTING_BOOST}")

        # Sustainability initiatives
        sustainability = str(row.get("sustainability_initiatives", "")).lower()
        if _has_data(sustainability):
            sus_kw = ["sustainability", "green", "carbon", "environmental",
                      "certified", "net zero", "eco", "renewable", "circular"]
            if any(kw in sustainability for kw in sus_kw):
                total += SUSTAINABILITY_BOOST
                boosts.append(f"Sustainability +{SUSTAINABILITY_BOOST}")

        # R&D budget
        rd_budget = str(row.get("rd_budget", "")).lower()
        if _has_data(rd_budget):
            rd_kw = ["million", "billion", "r&d", "budget", "invest",
                     "research", "innovation", "$", "€"]
            if any(kw in rd_budget for kw in rd_kw):
                total += CAPEX_BOOST
                boosts.append(f"R&D Budget +{CAPEX_BOOST}")

        # Recent acquisitions
        acquisitions = str(row.get("recent_acquisitions", "")).lower()
        if _has_data(acquisitions):
            acq_kw = ["acqui", "partnership", "joint venture", "merged",
                      "expanded", "new facility", "new plant"]
            if any(kw in acquisitions for kw in acq_kw):
                total += ACQUISITION_BOOST
                boosts.append(f"Acquisition +{ACQUISITION_BOOST}")

        # Multi-program
        prog_count = str(row.get("program_count", ""))
        if _has_data(prog_count):
            numbers = re.findall(r'\d+', prog_count.replace(",", ""))
            if numbers and int(numbers[0]) >= 5:
                total += MULTI_PROGRAM_BOOST
                boosts.append(f"Multi-program +{MULTI_PROGRAM_BOOST}")

        # Large production scale
        production = str(row.get("production_scale", ""))
        if _has_data(production):
            numbers = re.findall(r'\d+', production.replace(",", ""))
            if numbers and int(numbers[0]) >= 1000:
                total += LARGE_PRODUCTION_BOOST
                boosts.append(f"Large production +{LARGE_PRODUCTION_BOOST}")

        # Bio-materials interest
        bio = str(row.get("bio_materials_interest", "")).lower()
        if _has_data(bio):
            bio_kw = ["bio", "natural fiber", "sustainable composite",
                      "green resin", "recycled", "circular", "plant-based"]
            if any(kw in bio for kw in bio_kw):
                total += BIO_MATERIALS_BOOST
                boosts.append(f"Bio-materials +{BIO_MATERIALS_BOOST}")

        return total, boosts

    def is_key_contact(self, first_name: str, last_name: str) -> bool:
        """Check if delegate is a pre-identified key contact."""
        if not first_name or not last_name:
            return False
        first_lower = str(first_name).lower().strip()
        last_lower = str(last_name).lower().strip()
        for kf, kl in KEY_CONTACTS:
            if first_lower == kf and last_lower == kl:
                return True
        return False

    def score_attendee(self, row: dict) -> dict:
        """Calculate total priority score for one delegate."""
        first_name = str(row.get(COL_FIRST_NAME, ""))
        last_name = str(row.get(COL_LAST_NAME, ""))

        # Component scores
        title_score, title_reason = self.get_title_score(
            row.get(COL_JOB_TITLE, "")
        )
        company_score, company_reason = self.get_company_score(
            row.get("Company_Bucket", "")
        )
        materials_score, materials_reason = self.get_materials_adoption_proximity(row)
        research_boost, boost_details = self.get_research_boosts(row)

        is_key = self.is_key_contact(first_name, last_name)
        key_bonus = KEY_CONTACT_BONUS if is_key else 0

        total = title_score + company_score + materials_score + research_boost + key_bonus

        # Assign tier
        if is_key or total >= TIER_THRESHOLDS[1]:
            tier = 1
        elif total >= TIER_THRESHOLDS[2]:
            tier = 2
        elif total >= TIER_THRESHOLDS[3]:
            tier = 3
        else:
            tier = 4

        return {
            "Priority_Score": total,
            "Priority_Tier": tier,
            "Tier_Name": TIER_NAMES[tier],
            "Title_Score": title_score,
            "Title_Reason": title_reason,
            "Company_Score": company_score,
            "Company_Reason": company_reason,
            "Materials_Adoption_Proximity": materials_score,
            "Materials_Reason": materials_reason,
            "Research_Boost": research_boost,
            "Boost_Details": "; ".join(boost_details) if boost_details else "",
            "Is_Key_Contact": "Y" if is_key else "N",
            "Key_Bonus": key_bonus,
        }

    def generate_strategic_value(self, row: dict, scoring: dict) -> str:
        """Generate human-readable strategic value statement."""
        parts = []

        if scoring["Is_Key_Contact"] == "Y":
            parts.append("KEY CONTACT — pre-identified target")

        if scoring["Materials_Adoption_Proximity"] >= 20:
            parts.append(f"DIRECT materials role ({scoring['Materials_Reason']})")
        elif scoring["Materials_Adoption_Proximity"] >= 12:
            parts.append(f"Materials-adjacent ({scoring['Materials_Reason']})")

        company_bucket = str(row.get("Company_Bucket", ""))
        company_label = str(row.get("Company_Bucket_Label", ""))
        if company_bucket in ["D", "A", "B"]:
            parts.append(f"{company_label}: {row.get(COL_COMPANY, '')}")

        if scoring["Title_Score"] >= 25:
            parts.append(f"Senior executive ({row.get(COL_JOB_TITLE, '')})")
        elif scoring["Title_Score"] >= 20:
            parts.append("VP/Director level")

        if scoring["Boost_Details"]:
            parts.append(scoring["Boost_Details"])

        return "; ".join(parts) if parts else "General prospect"

    def score_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score all delegates and return sorted DataFrame."""
        print(f"Scoring {len(df)} delegates...")

        results = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            scoring = self.score_attendee(row_dict)
            strategic_value = self.generate_strategic_value(row_dict, scoring)

            result = row_dict.copy()
            result.update(scoring)
            result["Strategic_Value"] = strategic_value

            # Convenience flags
            result["Sustainability_Flag"] = "Y" if "Sustainability" in scoring.get("Boost_Details", "") else "N"
            result["Lightweighting_Flag"] = "Y" if "Lightweighting" in scoring.get("Boost_Details", "") else "N"
            result["RD_Budget_Flag"] = "Y" if "R&D" in scoring.get("Boost_Details", "") else "N"

            results.append(result)

        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values("Priority_Score", ascending=False)
        return result_df


def create_output_workbook(df: pd.DataFrame, output_path: Path):
    """Create the scored Excel workbook with multiple sheets."""
    print(f"\nCreating output workbook: {output_path}")

    # Column order for priority sheets
    priority_cols = [
        COL_FIRST_NAME, COL_LAST_NAME, COL_JOB_TITLE, COL_COMPANY,
        "Priority_Score", "Priority_Tier", "Tier_Name",
        "Strategic_Value",
        "Title_Score", "Company_Score", "Materials_Adoption_Proximity",
        "Research_Boost", "Is_Key_Contact",
        "Company_Bucket", "Company_Bucket_Label",
        "Function_Bucket", "Function_Bucket_Label",
        "Materials_Reason", "Boost_Details",
        "Sustainability_Flag", "Lightweighting_Flag", "RD_Budget_Flag",
    ]

    # Add research columns if present
    research_cols = [c for c in EXPANSION_VARIABLES if c in df.columns]
    meta_cols = [c for c in ["Research_Status", "Verification_Confidence",
                              "source_urls"] if c in df.columns]

    all_cols = priority_cols + research_cols + meta_cols
    for c in df.columns:
        if c not in all_cols:
            all_cols.append(c)
    all_cols = [c for c in all_cols if c in df.columns]

    top_n = ENHANCE_TOP_N
    top_df = df.head(top_n)[all_cols]
    all_filtered = df[all_cols]

    # BY_COMPANY
    company_counts = df[COL_COMPANY].value_counts()
    multi = company_counts[company_counts > 1].index.tolist()
    by_company = df[df[COL_COMPANY].isin(multi)].sort_values(
        [COL_COMPANY, "Priority_Score"], ascending=[True, False]
    )[all_cols]

    # MATERIALS_TARGETS
    materials = df[df["Materials_Adoption_Proximity"] > 0].sort_values(
        "Priority_Score", ascending=False
    )[all_cols]

    # SUMMARY
    summary_rows = []
    summary_rows.append({"Metric": "Total Scored", "Value": len(df)})
    summary_rows.append({"Metric": "", "Value": ""})

    for tier in [1, 2, 3, 4]:
        count = (df["Priority_Tier"] == tier).sum()
        summary_rows.append({
            "Metric": f"Tier {tier} - {TIER_NAMES[tier]}",
            "Value": count,
        })

    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "Key Contacts Found", "Value": (df["Is_Key_Contact"] == "Y").sum()})
    summary_rows.append({"Metric": "Materials Targets", "Value": len(materials)})
    summary_rows.append({"Metric": "Sustainability Flagged", "Value": (df["Sustainability_Flag"] == "Y").sum()})
    summary_rows.append({"Metric": "Lightweighting Flagged", "Value": (df["Lightweighting_Flag"] == "Y").sum()})
    summary_rows.append({"Metric": "R&D Budget Flagged", "Value": (df["RD_Budget_Flag"] == "Y").sum()})
    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "Highest Score", "Value": df["Priority_Score"].max()})
    summary_rows.append({"Metric": "Median Score", "Value": df["Priority_Score"].median()})
    summary_rows.append({"Metric": "Average Score", "Value": round(df["Priority_Score"].mean(), 1)})

    summary_df = pd.DataFrame(summary_rows)

    # Write
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    top_sheet_name = f"TOP_{top_n}"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        top_df.to_excel(writer, sheet_name=top_sheet_name, index=False)
        all_filtered.to_excel(writer, sheet_name="ALL_FILTERED", index=False)
        by_company.to_excel(writer, sheet_name="BY_COMPANY", index=False)
        materials.to_excel(writer, sheet_name="MATERIALS_TARGETS", index=False)
        summary_df.to_excel(writer, sheet_name="SUMMARY", index=False)

    print(f"  - {top_sheet_name}: {len(top_df)} rows")
    print(f"  - ALL_FILTERED: {len(all_filtered)} rows")
    print(f"  - BY_COMPANY: {len(by_company)} rows")
    print(f"  - MATERIALS_TARGETS: {len(materials)} rows")
    print(f"  - SUMMARY: Statistics")


def main():
    parser = argparse.ArgumentParser(description="AEROCOM 2025 Scoring + Ranking")
    parser.add_argument("--skip-research", action="store_true",
                        help="Score without research data (use checkpoint 1)")
    parser.add_argument("--input", type=str, default=None,
                        help="Custom input file path")
    parser.add_argument("--output", type=str, default=None,
                        help="Custom output file path")
    args = parser.parse_args()

    # Determine input
    if args.input:
        input_file = Path(args.input)
    elif args.skip_research:
        input_file = CHECKPOINT1_FILE
        print("Using checkpoint 1 (no research data)")
    else:
        if CHECKPOINT2_RESEARCHED.exists():
            input_file = CHECKPOINT2_RESEARCHED
            print("Using researched data (checkpoint 2)")
        elif CHECKPOINT1_FILE.exists():
            input_file = CHECKPOINT1_FILE
            print("No research data found — using checkpoint 1")
            print("  (Run step2_research.py first for research-based scoring)")
        else:
            print("ERROR: No input data found.")
            print("Run step1_buckets.py first.")
            return

    # Load
    print(f"\nLoading data from: {input_file}")
    sheet = "FILTERED" if "checkpoint1" in str(input_file).lower() else 0
    try:
        df = pd.read_excel(input_file, sheet_name=sheet)
    except Exception:
        df = pd.read_excel(input_file)
    print(f"Loaded {len(df)} delegates")

    # Score
    scorer = AerocomScorer()
    scored_df = scorer.score_all(df)

    # Output
    output_path = Path(args.output) if args.output else CHECKPOINT2_SCORED
    create_output_workbook(scored_df, output_path)

    # Print summary
    print(f"\n{'='*50}")
    print("SCORING COMPLETE")
    print(f"{'='*50}")

    for tier in [1, 2, 3, 4]:
        count = (scored_df["Priority_Tier"] == tier).sum()
        print(f"  Tier {tier} ({TIER_NAMES[tier]}): {count}")

    key_count = (scored_df["Is_Key_Contact"] == "Y").sum()
    materials_count = (scored_df["Materials_Adoption_Proximity"] > 0).sum()
    print(f"\n  Key Contacts: {key_count}")
    print(f"  Materials Targets: {materials_count}")
    print(f"  Highest Score: {scored_df['Priority_Score'].max()}")

    # Show top 10
    print(f"\n--- Top 10 Delegates ---")
    for i, (_, row) in enumerate(scored_df.head(10).iterrows()):
        print(f"  #{i+1:2d} Score={row['Priority_Score']:3.0f} | "
              f"{row.get(COL_FIRST_NAME, '')} {row.get(COL_LAST_NAME, '')} | "
              f"{str(row.get(COL_JOB_TITLE, ''))[:35]} | "
              f"{str(row.get(COL_COMPANY, ''))[:25]}")

    print(f"\n  Output: {output_path}")
    print(f"\nNext step: python step4_enhance.py")


if __name__ == "__main__":
    main()
