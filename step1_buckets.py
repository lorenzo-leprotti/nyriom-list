"""
Step 1: Categorize + Filter AEROCOM 2025 Delegates
===================================================

NO API needed — instant processing of all ~500 delegates.

Assigns each delegate:
- Company-Type Bucket (A-J)
- Job-Function Bucket (1-10)
- Bucket Relevance Score

Then filters out irrelevant delegates (legal, media, academic, junior roles).

Usage:
    python step1_buckets.py

Output:
    output/checkpoint1_filtered.xlsx
        - FILTERED sheet: ~250-350 relevant prospects
        - EXCLUDED sheet: ~150-200 removed rows
        - SUMMARY sheet: Counts by bucket combination
"""

import re
from pathlib import Path

import pandas as pd

from nyriom_config import (
    INPUT_CSV, OUTPUT_DIR, CHECKPOINT1_FILE,
    COMPANY_BUCKETS, FUNCTION_BUCKETS,
    COMPANY_BUCKET_SCORES, FUNCTION_BUCKET_SCORES,
    COL_FIRST_NAME, COL_LAST_NAME, COL_JOB_TITLE, COL_COMPANY,
)


def assign_company_bucket(company_name: str) -> tuple:
    """
    Assign company-type bucket based on company name.
    Returns (bucket_letter, bucket_label, relevance).
    Checks buckets in priority order.
    """
    if not company_name or str(company_name).lower().strip() in ["", "nan", "none"]:
        return "X", "Unknown", "UNKNOWN"

    company_lower = str(company_name).lower().strip()

    # Check each bucket in defined order
    for bucket_id, bucket_def in COMPANY_BUCKETS.items():
        for pattern in bucket_def["patterns"]:
            if pattern in company_lower:
                return bucket_id, bucket_def["label"], bucket_def["relevance"]

    return "X", "Unclassified", "UNKNOWN"


def assign_function_bucket(job_title: str) -> tuple:
    """
    Assign job-function bucket based on job title.
    Returns (bucket_number, bucket_label, relevance).
    Checks buckets in priority order.
    """
    if not job_title or str(job_title).lower().strip() in ["", "nan", "none"]:
        return "X", "Unknown Title", "UNKNOWN"

    title_lower = str(job_title).lower().strip()

    # Check each bucket in defined order
    for bucket_id, bucket_def in FUNCTION_BUCKETS.items():
        for pattern in bucket_def["patterns"]:
            # Use word-boundary-aware matching for short patterns
            if len(pattern) <= 3:
                if re.search(r'\b' + re.escape(pattern.strip()) + r'\b', title_lower):
                    return bucket_id, bucket_def["label"], bucket_def["relevance"]
            else:
                if pattern in title_lower:
                    return bucket_id, bucket_def["label"], bucket_def["relevance"]

    return "X", "Unclassified Title", "UNKNOWN"


def calculate_bucket_relevance_score(company_bucket: str, function_bucket: str) -> int:
    """
    Calculate a combined relevance score from company + function buckets.
    Higher score = more relevant to Nyriom Technologies materials sales.
    """
    company_score = COMPANY_BUCKET_SCORES.get(company_bucket, 0)
    function_score = FUNCTION_BUCKET_SCORES.get(function_bucket, 0)
    return company_score + function_score


def should_exclude(company_bucket: str, function_bucket: str,
                   company_relevance: str, function_relevance: str,
                   relevance_score: int) -> tuple:
    """
    Determine if a delegate should be excluded.
    Returns (should_exclude: bool, reason: str).

    Three-layer filter:
    1. WHITELIST: only keep companies identified as aerospace/materials (A-G)
    2. ROLE: exclude junior/irrelevant titles (bucket 10)
    3. SCORE CUTOFF: minimum relevance score of 40
    """
    # Layer 1: Only keep companies in buckets A-G
    KEEP_COMPANY_BUCKETS = ["A", "B", "C", "D", "E", "F", "G"]

    if company_bucket not in KEEP_COMPANY_BUCKETS:
        return True, f"Company not identified as aerospace/materials ({company_bucket}: {company_relevance})"

    # Layer 2: Exclude junior/irrelevant roles
    if function_bucket == "10":
        return True, f"Function bucket 10 ({function_relevance})"

    # Layer 3: Minimum relevance score cutoff
    MIN_RELEVANCE_SCORE = 40
    if relevance_score < MIN_RELEVANCE_SCORE:
        return True, f"Below relevance cutoff (score {relevance_score} < {MIN_RELEVANCE_SCORE})"

    # Keep: identified aerospace company + relevant role + score >= 40
    return False, ""


def main():
    """Run the bucket categorization and filtering pipeline."""
    print("=" * 60)
    print("AEROCOM 2025 - Step 1: Categorize + Filter")
    print("=" * 60)

    # Load data
    print(f"\nLoading data from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} delegates")
    print(f"Columns: {list(df.columns)}")

    # Assign buckets to all delegates
    print("\nAssigning company-type and job-function buckets...")

    company_buckets = []
    company_labels = []
    company_relevances = []
    function_buckets_list = []
    function_labels = []
    function_relevances = []
    relevance_scores = []
    exclude_flags = []
    exclude_reasons = []

    for _, row in df.iterrows():
        company = str(row.get(COL_COMPANY, ""))
        title = str(row.get(COL_JOB_TITLE, ""))

        # Assign buckets
        cb, cl, cr = assign_company_bucket(company)
        fb, fl, fr = assign_function_bucket(title)

        company_buckets.append(cb)
        company_labels.append(cl)
        company_relevances.append(cr)
        function_buckets_list.append(fb)
        function_labels.append(fl)
        function_relevances.append(fr)

        # Calculate relevance score
        score = calculate_bucket_relevance_score(cb, fb)
        relevance_scores.append(score)

        # Check exclusion
        excluded, reason = should_exclude(cb, fb, cr, fr, score)
        exclude_flags.append(excluded)
        exclude_reasons.append(reason)

    # Add columns to dataframe
    df["Company_Bucket"] = company_buckets
    df["Company_Bucket_Label"] = company_labels
    df["Company_Relevance"] = company_relevances
    df["Function_Bucket"] = function_buckets_list
    df["Function_Bucket_Label"] = function_labels
    df["Function_Relevance"] = function_relevances
    df["Bucket_Relevance_Score"] = relevance_scores
    df["Excluded"] = exclude_flags
    df["Exclusion_Reason"] = exclude_reasons

    # Split into filtered and excluded
    filtered_df = df[~df["Excluded"]].copy()
    excluded_df = df[df["Excluded"]].copy()

    # Sort filtered by relevance score (highest first)
    filtered_df = filtered_df.sort_values("Bucket_Relevance_Score", ascending=False)

    # Print summary
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Total delegates:  {len(df)}")
    print(f"FILTERED (kept):  {len(filtered_df)}")
    print(f"EXCLUDED:         {len(excluded_df)}")

    # Company bucket distribution
    print(f"\n--- Company Bucket Distribution (FILTERED) ---")
    cb_counts = filtered_df["Company_Bucket"].value_counts().sort_index()
    for bucket, count in cb_counts.items():
        label = COMPANY_BUCKETS.get(bucket, {}).get("label", "Unknown")
        print(f"  {bucket} ({label}): {count}")

    # Function bucket distribution
    print(f"\n--- Function Bucket Distribution (FILTERED) ---")
    fb_counts = filtered_df["Function_Bucket"].value_counts().sort_index()
    for bucket, count in fb_counts.items():
        label = FUNCTION_BUCKETS.get(bucket, {}).get("label", "Unknown")
        print(f"  {bucket} ({label}): {count}")

    # Exclusion reasons
    print(f"\n--- Exclusion Breakdown ---")
    if len(excluded_df) > 0:
        reason_counts = excluded_df["Exclusion_Reason"].value_counts()
        for reason, count in reason_counts.head(10).items():
            print(f"  {reason}: {count}")

    # Top relevance scores
    print(f"\n--- Top 10 Highest Relevance Scores ---")
    top10 = filtered_df.head(10)
    for _, row in top10.iterrows():
        print(f"  Score {row['Bucket_Relevance_Score']:3d} | "
              f"{row.get(COL_FIRST_NAME, '')} {row.get(COL_LAST_NAME, '')} | "
              f"{row.get(COL_JOB_TITLE, '')[:40]} | "
              f"{row.get(COL_COMPANY, '')[:30]}")

    # Build summary dataframe
    summary_rows = []
    summary_rows.append({"Metric": "Total Delegates", "Value": len(df)})
    summary_rows.append({"Metric": "Filtered (Kept)", "Value": len(filtered_df)})
    summary_rows.append({"Metric": "Excluded", "Value": len(excluded_df)})
    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "--- Company Buckets (Filtered) ---", "Value": ""})
    for bucket, count in cb_counts.items():
        label = COMPANY_BUCKETS.get(bucket, {}).get("label", "Unknown")
        summary_rows.append({"Metric": f"  {bucket} - {label}", "Value": count})
    summary_rows.append({"Metric": "", "Value": ""})
    summary_rows.append({"Metric": "--- Function Buckets (Filtered) ---", "Value": ""})
    for bucket, count in fb_counts.items():
        label = FUNCTION_BUCKETS.get(bucket, {}).get("label", "Unknown")
        summary_rows.append({"Metric": f"  {bucket} - {label}", "Value": count})

    summary_df = pd.DataFrame(summary_rows)

    # Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Drop helper columns from output
    output_cols_filtered = [c for c in filtered_df.columns if c not in ["Excluded"]]
    output_cols_excluded = [c for c in excluded_df.columns]

    print(f"\nSaving to: {CHECKPOINT1_FILE}")
    with pd.ExcelWriter(CHECKPOINT1_FILE, engine="openpyxl") as writer:
        filtered_df[output_cols_filtered].to_excel(
            writer, sheet_name="FILTERED", index=False
        )
        excluded_df[output_cols_excluded].to_excel(
            writer, sheet_name="EXCLUDED", index=False
        )
        summary_df.to_excel(
            writer, sheet_name="SUMMARY", index=False
        )

    print(f"  - FILTERED: {len(filtered_df)} rows")
    print(f"  - EXCLUDED: {len(excluded_df)} rows")
    print(f"  - SUMMARY: Statistics")

    print(f"\n{'='*60}")
    print("CHECKPOINT 1 COMPLETE")
    print(f"{'='*60}")
    print(f"\nReview: {CHECKPOINT1_FILE}")
    print("  1. Check EXCLUDED sheet — no obvious materials/procurement people?")
    print("  2. Check FILTERED sheet — top scores look right?")
    print(f"\nNext step: python step2_research.py")


if __name__ == "__main__":
    main()
