import json
import pandas as pd

FEEDBACK_FILE = "feedback_logs.json"
OUTPUT_CSV = "feedback_summary.csv"

def load_feedback():
    """Load feedback logs into a DataFrame."""
    with open(FEEDBACK_FILE, "r") as f:
        data = json.load(f)

    if not data:
        print("No feedback data found.")
        return None

    df = pd.DataFrame(data)
    return df


def compute_descriptive_stats(df):
    """Compute mean, std, min, max for each Likert question."""
    numeric_cols = [
        "understands_serious_issues",
        "helped_manage_distress",
        "would_use_in_future",
        "easy_for_age_group",
        "easy_to_learn",
        "easier_than_in_person"
    ]

    stats = df[numeric_cols].astype(float).describe().T
    return stats


def compute_correlations(df):
    """Compute correlation matrix between feedback questions."""
    numeric_cols = [
        "understands_serious_issues",
        "helped_manage_distress",
        "would_use_in_future",
        "easy_for_age_group",
        "easy_to_learn",
        "easier_than_in_person"
    ]

    corr = df[numeric_cols].astype(float).corr()
    return corr


def export_csv(df):
    """Export raw feedback to CSV."""
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"CSV exported: {OUTPUT_CSV}")


def main():
    df = load_feedback()
    if df is None:
        return

    print("\n=== FEEDBACK DATA LOADED ===")
    print(df.head())

    print("\n=== DESCRIPTIVE STATISTICS ===")
    stats = compute_descriptive_stats(df)
    print(stats)

    print("\n=== CORRELATION MATRIX ===")
    corr = compute_correlations(df)
    print(corr)

    export_csv(df)


if __name__ == "__main__":
    main()