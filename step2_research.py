"""
Step 2: Research AEROCOM 2025 Delegates
=======================================

Researches ~250 filtered delegates using configurable research backends:
- Perplexity Sonar (production, web-grounded)
- Demo (pre-generated data, zero cost)

13 expansion variables:
  company_type, program_count, region_focus, lightweighting_programs,
  sustainability_initiatives, production_scale, linkedin_url,
  materials_adoption_role, current_material_suppliers, rd_budget,
  material_spec_influence, recent_acquisitions, bio_materials_interest

Usage:
    python step2_research.py --backend demo       # Zero-cost demo (default)
    python step2_research.py --backend perplexity  # Production web research
    python step2_research.py --test 5              # Test with first 5
    python step2_research.py --resume              # Resume from last checkpoint

Output:
    output/checkpoint2_researched.xlsx
    logs/research_log.json
"""

import json
import time
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from nyriom_config import (
    CHECKPOINT1_FILE, CHECKPOINT2_RESEARCHED,
    OUTPUT_DIR, LOGS_DIR, RESEARCH_LOG,
    EXPANSION_VARIABLES, DUAL_PASS,
    COL_FIRST_NAME, COL_LAST_NAME, COL_JOB_TITLE, COL_COMPANY,
    validate_config,
)
from research_backends import get_backend


class AerocomResearchPipeline:
    """Research pipeline for AEROCOM 2025 delegates."""

    SYSTEM_PROMPT = (
        "You are a corporate research assistant specializing in the "
        "aerospace and advanced materials industry. You are researching "
        "companies and executives on behalf of Nyriom Technologies, a "
        "Berlin-based bio-polymer composites startup evaluating prospect "
        "fit for NyrionPlex adoption (advanced bio-polymer composite system). "
        "Focus on finding information relevant to materials procurement, "
        "lightweighting programs, and sustainability initiatives. "
        "Always provide citations. Return responses in valid JSON format only."
    )

    VERIFY_SYSTEM_PROMPT = (
        "You are a fact-checking research assistant specializing in aerospace "
        "and advanced materials. Verify research data for accuracy and completeness. "
        "Return responses in valid JSON format only."
    )

    def __init__(self, backend_name: str = "demo", dual_pass: bool = None, **backend_kwargs):
        self.backend = get_backend(backend_name, **backend_kwargs)
        self.dual_pass = dual_pass if dual_pass is not None else DUAL_PASS
        self.logs = []
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "partial": 0,
            "failed": 0,
            "api_calls": 0,
        }

    def _parse_json_response(self, response: dict) -> dict:
        """Extract and parse JSON from a backend response."""
        if "error" in response:
            return None

        content = response.get("content", "{}")

        # Strip markdown code fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())

    def _build_research_prompt(self, attendee: dict) -> str:
        first_name = attendee.get(COL_FIRST_NAME, "")
        last_name = attendee.get(COL_LAST_NAME, "")
        title = attendee.get(COL_JOB_TITLE, "")
        company = attendee.get(COL_COMPANY, "")

        return f"""
Research the company "{company}" and the person "{first_name} {last_name}"
who holds the title "{title}".

Context: We are Nyriom Technologies, a Berlin-based bio-polymer composites startup.
We want to understand this person's potential as an adopter of our NyrionPlex
advanced composite material system.

Find information on these 13 specific fields. For each, provide the data you find
or "NOT_FOUND" if unavailable:

1. company_type — aerospace OEM, tier 1/2/3 supplier, material supplier, airline/MRO, etc.
2. program_count — number of aircraft programs or product lines they work on (number or NOT_FOUND)
3. region_focus — geographic regions (Europe, Americas, APAC, Global)
4. lightweighting_programs — active lightweighting or composite adoption programs (2024-2027)
5. sustainability_initiatives — sustainability programs, certifications, carbon reduction goals
6. production_scale — production volume or manufacturing capacity
7. linkedin_url — this person's LinkedIn profile URL if findable
8. materials_adoption_role — does this person or their role involve selecting or specifying new materials? (YES/NO/INDIRECT with explanation)
9. current_material_suppliers — known composite/polymer suppliers (Hexcel, Toray, Solvay, etc.) or NOT_FOUND
10. rd_budget — announced R&D spending, innovation budget, or technology investment
11. material_spec_influence — does this person influence material specifications or qualified supplier lists? (YES/NO with explanation)
12. recent_acquisitions — new business acquisitions, partnerships, or joint ventures (2024-2025)
13. bio_materials_interest — interest in bio-based polymers, sustainable composites, natural fiber reinforcement

Return ONLY valid JSON in this exact format (no other text):
{{
  "company_type": "value or NOT_FOUND",
  "program_count": "value or NOT_FOUND",
  "region_focus": "value or NOT_FOUND",
  "lightweighting_programs": "value or NOT_FOUND",
  "sustainability_initiatives": "value or NOT_FOUND",
  "production_scale": "value or NOT_FOUND",
  "linkedin_url": "URL or NOT_FOUND",
  "materials_adoption_role": "value or NOT_FOUND",
  "current_material_suppliers": "value or NOT_FOUND",
  "rd_budget": "value or NOT_FOUND",
  "material_spec_influence": "value or NOT_FOUND",
  "recent_acquisitions": "value or NOT_FOUND",
  "bio_materials_interest": "value or NOT_FOUND",
  "sources": ["list of source URLs used"]
}}
"""

    def _build_verify_prompt(self, data: dict, attendee: dict) -> str:
        first_name = attendee.get(COL_FIRST_NAME, "")
        last_name = attendee.get(COL_LAST_NAME, "")
        title = attendee.get(COL_JOB_TITLE, "")
        company = attendee.get(COL_COMPANY, "")

        return f"""
Verify this research data about "{first_name} {last_name}" ({title}) at "{company}".

RESEARCH TO VERIFY:
{json.dumps(data, indent=2)}

Your task:
1. Check if each claim is accurate based on your knowledge and web search
2. Flag any claims that seem incorrect or outdated
3. Add any important missing information
4. Rate overall confidence: HIGH (>80% accurate), MEDIUM (50-80%), LOW (<50%)

Pay special attention to:
- materials_adoption_role accuracy
- lightweighting program timelines
- production scale figures

Return ONLY valid JSON:
{{
  "company_type": "verified or corrected value or NOT_FOUND",
  "program_count": "verified or corrected value or NOT_FOUND",
  "region_focus": "verified or corrected value or NOT_FOUND",
  "lightweighting_programs": "verified or corrected value or NOT_FOUND",
  "sustainability_initiatives": "verified or corrected value or NOT_FOUND",
  "production_scale": "verified or corrected value or NOT_FOUND",
  "linkedin_url": "verified URL or NOT_FOUND",
  "materials_adoption_role": "verified or corrected value or NOT_FOUND",
  "current_material_suppliers": "verified or corrected value or NOT_FOUND",
  "rd_budget": "verified or corrected value or NOT_FOUND",
  "material_spec_influence": "verified or corrected value or NOT_FOUND",
  "recent_acquisitions": "verified or corrected value or NOT_FOUND",
  "bio_materials_interest": "verified or corrected value or NOT_FOUND",
  "verification_confidence": "HIGH or MEDIUM or LOW",
  "corrections_made": ["list any corrections"],
  "sources": ["source URLs"]
}}
"""

    def research_attendee(self, attendee: dict) -> dict:
        """Research a single attendee, optionally with verification pass."""
        first_name = attendee.get(COL_FIRST_NAME, "")
        last_name = attendee.get(COL_LAST_NAME, "")
        company = attendee.get(COL_COMPANY, "")

        # ── PASS 1: Gather Research ──
        research_prompt = self._build_research_prompt(attendee)
        response1 = self.backend.research(
            self.SYSTEM_PROMPT, research_prompt, model_tier="standard"
        )
        self.stats["api_calls"] += 1
        time.sleep(self.backend.rate_limit_delay("standard"))

        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "attendee": f"{first_name} {last_name}",
            "company": company,
            "pass": 1,
            "backend": self.backend.name,
            "response": response1,
        })

        # Parse pass 1
        try:
            data = self._parse_json_response(response1)
            if data is None:
                return {"_error": response1.get("error", "Unknown"), "_status": "FAILED"}
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {"_error": f"Parse error pass 1: {e}", "_status": "FAILED"}

        # ── PASS 2: Verify (optional) ──
        if self.dual_pass:
            verify_prompt = self._build_verify_prompt(data, attendee)
            response2 = self.backend.research(
                self.VERIFY_SYSTEM_PROMPT, verify_prompt, model_tier="standard"
            )
            self.stats["api_calls"] += 1

            self.logs.append({
                "timestamp": datetime.now().isoformat(),
                "attendee": f"{first_name} {last_name}",
                "company": company,
                "pass": 2,
                "backend": self.backend.name,
                "response": response2,
            })

            try:
                verified = self._parse_json_response(response2)
                if verified:
                    for key in EXPANSION_VARIABLES:
                        if key in verified and verified[key] and str(verified[key]).upper() != "NOT_FOUND":
                            data[key] = verified[key]
                    data["_verification"] = verified.get("verification_confidence", "MEDIUM")
                    data["_corrections"] = verified.get("corrections_made", [])
                else:
                    data["_verification"] = "FAILED"
            except (json.JSONDecodeError, KeyError, IndexError):
                data["_verification"] = "PARSE_ERROR"

            time.sleep(self.backend.rate_limit_delay("standard"))
        else:
            data["_verification"] = "SKIPPED"

        # Determine status
        fields_found = sum(
            1 for k in EXPANSION_VARIABLES
            if data.get(k) and str(data[k]).upper() != "NOT_FOUND"
        )

        if fields_found >= 4:
            data["_status"] = "SUCCESS"
        elif fields_found >= 1:
            data["_status"] = "PARTIAL"
        else:
            data["_status"] = "NO_DATA"

        # Attach citations
        if "citations" in response1:
            data["_citations_pass1"] = response1["citations"]

        return data

    def flatten_result(self, research: dict) -> dict:
        """Flatten research result for Excel columns."""
        flat = {}

        for field in EXPANSION_VARIABLES:
            value = research.get(field, "")
            if value and str(value).upper() != "NOT_FOUND":
                flat[field] = str(value)
            else:
                flat[field] = ""

        # Sources
        sources = research.get("sources", [])
        if sources:
            flat["source_urls"] = "; ".join(sources[:3])

        flat["Research_Status"] = research.get("_status", "UNKNOWN")
        flat["Verification_Confidence"] = research.get("_verification", "")

        corrections = research.get("_corrections", [])
        if corrections:
            flat["Corrections_Made"] = "; ".join(corrections[:3])

        return flat

    def save_checkpoint(self, results: list, checkpoint_num: int):
        """Save intermediate checkpoint."""
        checkpoint_file = LOGS_DIR / f"research_checkpoint_{checkpoint_num}.json"
        with open(checkpoint_file, "w") as f:
            json.dump({
                "processed": len(results),
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats,
            }, f, indent=2)
        print(f"  [Checkpoint: {len(results)} rows saved]")

    def save_results_excel(self, results: list):
        """Save results to Excel checkpoint."""
        if not results:
            return
        df = pd.DataFrame(results)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df.to_excel(CHECKPOINT2_RESEARCHED, index=False)

    def load_resume_state(self) -> int:
        """Check for existing checkpoint to resume from."""
        if CHECKPOINT2_RESEARCHED.exists():
            try:
                df = pd.read_excel(CHECKPOINT2_RESEARCHED)
                return len(df)
            except Exception:
                return 0
        return 0

    def run(self, test_count: int = None, resume: bool = False):
        """Run the research pipeline."""
        # Validate (skip API key check for demo)
        if not CHECKPOINT1_FILE.exists():
            print(f"ERROR: Checkpoint 1 not found: {CHECKPOINT1_FILE}")
            print("Run step1_buckets.py first.")
            return

        print(f"\nLoading filtered data from: {CHECKPOINT1_FILE}")
        df = pd.read_excel(CHECKPOINT1_FILE, sheet_name="FILTERED")
        print(f"Loaded {len(df)} filtered delegates")

        # Resume handling
        start_index = 0
        existing_results = []
        if resume:
            start_index = self.load_resume_state()
            if start_index > 0:
                existing_df = pd.read_excel(CHECKPOINT2_RESEARCHED)
                existing_results = existing_df.to_dict("records")
                print(f"Resuming from row {start_index + 1}")

        if test_count:
            df = df.head(test_count)
            print(f"Test mode: processing first {test_count} delegates")

        total = len(df)
        remaining = total - start_index
        delay = self.backend.rate_limit_delay("standard")
        passes = 2 if self.dual_pass else 1

        print(f"\nBackend: {self.backend.name}")
        print(f"Web search: {'Yes' if self.backend.supports_web_search else 'No'}")
        print(f"Dual-pass: {'Yes' if self.dual_pass else 'No (single-pass)'}")
        print(f"Remaining: {remaining} delegates")
        est_time = remaining * delay * passes / 60
        print(f"Estimated time: ~{est_time:.0f} minutes\n")

        # Process
        results = existing_results.copy()
        for idx in range(start_index, total):
            row = df.iloc[idx]
            attendee = row.to_dict()
            first_name = attendee.get(COL_FIRST_NAME, "")
            last_name = attendee.get(COL_LAST_NAME, "")
            company = attendee.get(COL_COMPANY, "")

            print(f"[{idx + 1}/{total}] {first_name} {last_name} @ {company}", end=" ... ")

            research = self.research_attendee(attendee)
            status = research.get("_status", "UNKNOWN")
            verification = research.get("_verification", "")

            # Update stats
            self.stats["total_processed"] += 1
            if status in ["VERIFIED", "SUCCESS"]:
                self.stats["successful"] += 1
                print(f"{status} ({verification})")
            elif status == "PARTIAL":
                self.stats["partial"] += 1
                print(f"PARTIAL ({verification})")
            else:
                self.stats["failed"] += 1
                err = research.get("_error", "unknown")
                print(f"FAILED ({str(err)[:40]})")

            # Combine original + research
            enriched = attendee.copy()
            enriched.update(self.flatten_result(research))
            results.append(enriched)

            # Checkpoint every 25 rows
            if (idx + 1) % 25 == 0:
                self.save_checkpoint(results, idx + 1)
                self.save_results_excel(results)

        # Final save
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        result_df = pd.DataFrame(results)
        print(f"\nSaving results to: {CHECKPOINT2_RESEARCHED}")
        result_df.to_excel(CHECKPOINT2_RESEARCHED, index=False)

        # Save logs
        with open(RESEARCH_LOG, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)

        # Summary
        print(f"\n{'='*50}")
        print("RESEARCH COMPLETE")
        print(f"{'='*50}")
        print(f"Backend:         {self.backend.name}")
        print(f"Total Processed: {self.stats['total_processed']}")
        print(f"Successful:      {self.stats['successful']}")
        print(f"Partial Data:    {self.stats['partial']}")
        print(f"Failed:          {self.stats['failed']}")
        print(f"API Calls:       {self.stats['api_calls']}")
        print(f"\nOutput: {CHECKPOINT2_RESEARCHED}")
        print(f"Logs:   {RESEARCH_LOG}")
        print(f"\nNext step: python step3_score.py")


def main():
    parser = argparse.ArgumentParser(description="AEROCOM 2025 Research Pipeline")
    parser.add_argument("--backend", choices=["perplexity", "demo"],
                        default="demo", help="Research backend (default: demo)")
    parser.add_argument("--dual-pass", action="store_true",
                        help="Enable dual-pass verification (doubles API calls)")
    parser.add_argument("--test", type=int, help="Test with first N delegates")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last checkpoint")
    args = parser.parse_args()

    pipeline = AerocomResearchPipeline(
        backend_name=args.backend,
        dual_pass=args.dual_pass,
    )
    pipeline.run(test_count=args.test, resume=args.resume)


if __name__ == "__main__":
    main()
