"""
Step 4: Deep Research on Top Delegates
======================================

Uses configurable research backend to fill gaps in expansion variables
for the top-scored delegates (buffer for final ranking).

Supports:
- Perplexity Sonar Pro (production, web-grounded deep research)
- Demo (pre-generated data, zero cost)

Priority gap-filling order:
1. materials_adoption_role (most valuable for re-ranking)
2. current_material_suppliers (competitive intelligence)
3. lightweighting_programs (active programs = immediate adoption opportunity)
4. rd_budget (budget availability signal)
5. bio_materials_interest (Nyriom's bio-polymer positioning)
6. linkedin_url (for outreach)

Usage:
    python step4_enhance.py --backend demo         # Zero-cost demo (default)
    python step4_enhance.py --backend perplexity   # Production
    python step4_enhance.py --test 5               # Test with first 5

Output:
    output/checkpoint3_enhanced.xlsx
    logs/enhance_log.json
"""

import json
import time
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from nyriom_config import (
    CHECKPOINT2_SCORED, CHECKPOINT3_ENHANCED,
    OUTPUT_DIR, LOGS_DIR, ENHANCE_LOG,
    ENHANCEMENT_PRIORITY_FIELDS, EXPANSION_VARIABLES, ENHANCE_TOP_N,
    COL_FIRST_NAME, COL_LAST_NAME, COL_JOB_TITLE, COL_COMPANY,
    validate_config,
)
from research_backends import get_backend


class AerocomEnhancer:
    """Enhancement pipeline for AEROCOM top delegates."""

    SYSTEM_PROMPT = (
        "You are a corporate research assistant specializing in the "
        "aerospace and advanced materials industry. You are researching "
        "executives on behalf of Nyriom Technologies, a Berlin-based "
        "bio-polymer composites startup. Find SPECIFIC, VERIFIABLE "
        "information about materials adoption, lightweighting programs, "
        "and R&D investments. Return responses in valid JSON format only."
    )

    def __init__(self, backend_name: str = "demo", **backend_kwargs):
        self.backend = get_backend(backend_name, **backend_kwargs)
        self.logs = []
        self.stats = {
            "total_processed": 0,
            "enhanced": 0,
            "no_gaps": 0,
            "no_new_data": 0,
            "failed": 0,
            "api_calls": 0,
        }

    def identify_gaps(self, row: dict) -> list:
        """Identify fields with missing data, prioritized for materials sales."""
        gaps = []
        for field in ENHANCEMENT_PRIORITY_FIELDS:
            value = str(row.get(field, "")).strip().lower()
            if not value or value in ["", "nan", "none", "not_found"]:
                gaps.append(field)
        return gaps

    def build_gap_prompt(self, row: dict, gaps: list) -> str:
        """Build focused prompt targeting specific gaps."""
        first_name = row.get(COL_FIRST_NAME, "")
        last_name = row.get(COL_LAST_NAME, "")
        title = row.get(COL_JOB_TITLE, "")
        company = row.get(COL_COMPANY, "")

        gap_questions = []

        if "materials_adoption_role" in gaps:
            gap_questions.append(f"""
MATERIALS ADOPTION ROLE: Does {first_name} {last_name} ({title} at {company}) have
any involvement in selecting, specifying, or approving new materials? Consider:
- Direct material specification authority
- Influence over qualified supplier lists
- Role in R&D material evaluation programs
- Connection to materials review boards
Answer: YES (with explanation), NO, or INDIRECT (with explanation)""")

        if "current_material_suppliers" in gaps:
            gap_questions.append(f"""
CURRENT MATERIAL SUPPLIERS: What composite/polymer suppliers does {company} work with?
Look for relationships with: Hexcel, Toray, Solvay, BASF, Cytec, Teijin, Huntsman,
Arkema, DuPont, Covestro, SGL Carbon, or specialty composite suppliers.
Also check if they've recently qualified new material suppliers.""")

        if "lightweighting_programs" in gaps:
            gap_questions.append(f"""
LIGHTWEIGHTING PROGRAMS: Search for any lightweighting, composite adoption, or
advanced materials programs at {company} between 2024-2027. Include:
- Specific aircraft programs or product lines
- Material transition initiatives (metal-to-composite)
- Next-generation material qualification efforts""")

        if "rd_budget" in gaps:
            gap_questions.append(f"""
R&D BUDGET: Find any announced R&D spending, innovation budget, or technology
investment plans for {company}. Include amounts, timelines, and focus areas.""")

        if "bio_materials_interest" in gaps:
            gap_questions.append(f"""
BIO-MATERIALS INTEREST: Does {company} have any interest in bio-based polymers,
sustainable composites, or natural fiber reinforcement? Look for:
- Bio-resin or bio-polymer research programs
- Sustainable composite material initiatives
- Partnerships with bio-materials companies
- Circular economy programs for composites""")

        if "linkedin_url" in gaps:
            gap_questions.append(f"""
LINKEDIN: Find the LinkedIn profile URL for {first_name} {last_name}, {title} at {company}.""")

        prompt = f"""
Research the company "{company}" and executive "{first_name} {last_name}" ({title}).

Context: Nyriom Technologies (Berlin bio-polymer composites startup) wants to
understand this prospect's relevance for NyrionPlex advanced composite adoption.

I need SPECIFIC, VERIFIED information on these gaps:
{"".join(gap_questions)}

IMPORTANT: Only report information you can verify. Use "NOT_FOUND" if unavailable.

Return ONLY valid JSON:
{{
  "materials_adoption_role": "value or NOT_FOUND",
  "current_material_suppliers": "value or NOT_FOUND",
  "lightweighting_programs": "value or NOT_FOUND",
  "rd_budget": "value or NOT_FOUND",
  "bio_materials_interest": "value or NOT_FOUND",
  "linkedin_url": "URL or NOT_FOUND",
  "sources": ["list of source URLs"],
  "confidence": "HIGH or MEDIUM or LOW"
}}
"""
        return prompt

    def enhance_prospect(self, row: dict, gaps: list) -> dict:
        """Enhance one prospect."""
        prompt = self.build_gap_prompt(row, gaps)
        response = self.backend.research(
            self.SYSTEM_PROMPT, prompt, model_tier="pro"
        )
        self.stats["api_calls"] += 1

        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "attendee": f"{row.get(COL_FIRST_NAME, '')} {row.get(COL_LAST_NAME, '')}",
            "company": row.get(COL_COMPANY, ""),
            "gaps_targeted": gaps,
            "backend": self.backend.name,
            "response": response,
        })

        try:
            if "error" in response:
                return {"_enhancement_status": "FAILED",
                        "_enhancement_error": response["error"]}

            content = response.get("content", "{}")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            new_findings = sum(
                1 for gap in gaps
                if data.get(gap) and str(data[gap]).upper() != "NOT_FOUND"
            )

            data["_enhancement_status"] = "ENHANCED" if new_findings > 0 else "NO_NEW_DATA"
            data["_gaps_filled"] = new_findings
            data["_gaps_targeted"] = len(gaps)
            return data

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {"_enhancement_status": "PARSE_ERROR",
                    "_enhancement_error": str(e)}

    def merge_enhancement(self, original: dict, enhancement: dict) -> dict:
        """Merge enhanced data into original row (only fill gaps)."""
        result = original.copy()

        for field in ENHANCEMENT_PRIORITY_FIELDS:
            orig_val = str(original.get(field, "")).strip().lower()
            new_val = enhancement.get(field, "")

            if (not orig_val or orig_val in ["", "nan", "none", "not_found"]) and \
               new_val and str(new_val).upper() != "NOT_FOUND":
                result[field] = new_val

        result["Enhancement_Status"] = enhancement.get("_enhancement_status", "")
        result["Enhancement_Gaps_Filled"] = enhancement.get("_gaps_filled", 0)
        return result

    def run(self, test_count: int = None):
        """Run the enhancement pipeline."""
        if not CHECKPOINT2_SCORED.exists():
            print(f"ERROR: Scored data not found: {CHECKPOINT2_SCORED}")
            print("Run step3_score.py first.")
            return

        # Load data
        print(f"\nLoading scored data from: {CHECKPOINT2_SCORED}")
        top_sheet = f"TOP_{ENHANCE_TOP_N}"
        try:
            top_df = pd.read_excel(CHECKPOINT2_SCORED, sheet_name=top_sheet)
        except Exception:
            # Fallback: read first sheet and take top N
            top_df = pd.read_excel(CHECKPOINT2_SCORED).head(ENHANCE_TOP_N)
        all_df = pd.read_excel(CHECKPOINT2_SCORED, sheet_name="ALL_FILTERED")
        print(f"Top {ENHANCE_TOP_N}: {len(top_df)} delegates to enhance")
        print(f"ALL_FILTERED: {len(all_df)} total delegates")

        if test_count:
            top_df = top_df.head(test_count)
            print(f"Test mode: enhancing first {test_count} only")

        print(f"\nBackend: {self.backend.name}")
        print(f"Web search: {'Yes' if self.backend.supports_web_search else 'No'}")

        # Gap analysis
        total_gaps = 0
        prospects_with_gaps = 0
        for _, row in top_df.iterrows():
            gaps = self.identify_gaps(row.to_dict())
            if gaps:
                prospects_with_gaps += 1
                total_gaps += len(gaps)

        print(f"\nGap analysis:")
        print(f"  Delegates with gaps: {prospects_with_gaps}/{len(top_df)}")
        print(f"  Total gaps to fill: {total_gaps}")

        # Process
        enhanced_rows = []
        for idx, (_, row) in enumerate(top_df.iterrows()):
            row_dict = row.to_dict()
            first_name = row_dict.get(COL_FIRST_NAME, "")
            last_name = row_dict.get(COL_LAST_NAME, "")
            company = row_dict.get(COL_COMPANY, "")

            gaps = self.identify_gaps(row_dict)

            print(f"[{idx + 1}/{len(top_df)}] {first_name} {last_name} @ {company}", end=" ... ")

            if not gaps:
                print("No gaps - skipping")
                row_dict["Enhancement_Status"] = "NO_GAPS"
                row_dict["Enhancement_Gaps_Filled"] = 0
                enhanced_rows.append(row_dict)
                self.stats["no_gaps"] += 1
                self.stats["total_processed"] += 1
                continue

            print(f"Gaps: {', '.join(gaps)}", end=" ... ")

            enhancement = self.enhance_prospect(row_dict, gaps)
            status = enhancement.get("_enhancement_status", "UNKNOWN")
            gaps_filled = enhancement.get("_gaps_filled", 0)

            merged = self.merge_enhancement(row_dict, enhancement)
            enhanced_rows.append(merged)

            self.stats["total_processed"] += 1
            if status == "ENHANCED":
                self.stats["enhanced"] += 1
                print(f"ENHANCED ({gaps_filled} gaps filled)")
            elif status == "NO_NEW_DATA":
                self.stats["no_new_data"] += 1
                print("No new data found")
            else:
                self.stats["failed"] += 1
                print(f"FAILED ({enhancement.get('_enhancement_error', '')[:40]})")

            time.sleep(self.backend.rate_limit_delay("pro"))

        # Build full output
        enhanced_top_df = pd.DataFrame(enhanced_rows)

        top_keys = set()
        for _, row in enhanced_top_df.iterrows():
            key = f"{row.get(COL_FIRST_NAME, '')}|{row.get(COL_LAST_NAME, '')}|{row.get(COL_COMPANY, '')}"
            top_keys.add(key)

        remaining_rows = []
        for _, row in all_df.iterrows():
            key = f"{row.get(COL_FIRST_NAME, '')}|{row.get(COL_LAST_NAME, '')}|{row.get(COL_COMPANY, '')}"
            if key not in top_keys:
                row_dict = row.to_dict()
                row_dict["Enhancement_Status"] = "NOT_PROCESSED"
                row_dict["Enhancement_Gaps_Filled"] = 0
                remaining_rows.append(row_dict)

        remaining_df = pd.DataFrame(remaining_rows) if remaining_rows else pd.DataFrame()
        full_df = pd.concat([enhanced_top_df, remaining_df], ignore_index=True)

        # Save
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving enhanced data to: {CHECKPOINT3_ENHANCED}")
        full_df.to_excel(CHECKPOINT3_ENHANCED, index=False)

        with open(ENHANCE_LOG, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)

        # Summary
        print(f"\n{'='*50}")
        print("ENHANCEMENT COMPLETE")
        print(f"{'='*50}")
        print(f"Backend:         {self.backend.name}")
        print(f"Total Processed: {self.stats['total_processed']}")
        print(f"Enhanced:        {self.stats['enhanced']}")
        print(f"No Gaps:         {self.stats['no_gaps']}")
        print(f"No New Data:     {self.stats['no_new_data']}")
        print(f"Failed:          {self.stats['failed']}")
        print(f"API Calls:       {self.stats['api_calls']}")
        print(f"\nOutput: {CHECKPOINT3_ENHANCED}")
        print(f"Logs:   {ENHANCE_LOG}")
        print(f"\nNext step: python step5_final_rank.py")


def main():
    parser = argparse.ArgumentParser(description="AEROCOM 2025 Enhancement")
    parser.add_argument("--backend", choices=["perplexity", "demo"],
                        default="demo", help="Research backend (default: demo)")
    parser.add_argument("--test", type=int, help="Test with first N delegates")
    args = parser.parse_args()

    enhancer = AerocomEnhancer(backend_name=args.backend)
    enhancer.run(test_count=args.test)


if __name__ == "__main__":
    main()
