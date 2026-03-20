from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from plotly.offline.offline import get_plotlyjs


ROOT = Path(__file__).resolve().parent
SOURCE_CSV = ROOT / "StudentsPerformance.csv"
ENRICHED_CSV = ROOT / "StudentsPerformance_enriched.csv"
DASHBOARD_HTML = ROOT / "student_performance_dashboard.html"
TEMPLATE_HTML = ROOT / "dashboard_template.html"


def load_and_enrich_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    df.insert(0, "student_id", range(1, len(df) + 1))

    score_columns = ["math score", "reading score", "writing score"]
    df["average score"] = df[score_columns].mean(axis=1).round(2)
    df["total score"] = df[score_columns].sum(axis=1)
    df["pass math"] = df["math score"] >= 60
    df["pass reading"] = df["reading score"] >= 60
    df["pass writing"] = df["writing score"] >= 60
    df["pass all"] = df[["pass math", "pass reading", "pass writing"]].all(axis=1)
    df["performance band"] = pd.cut(
        df["average score"],
        bins=[-1, 59.99, 69.99, 79.99, 100],
        labels=["At Risk", "Average", "Good", "Excellent"],
    )
    df["best subject"] = df[score_columns].idxmax(axis=1).str.replace(" score", "", regex=False).str.title()
    df["reading-writing gap"] = (df["reading score"] - df["writing score"]).round(2)
    df["reading-math gap"] = (df["reading score"] - df["math score"]).round(2)
    df["writing-math gap"] = (df["writing score"] - df["math score"]).round(2)
    return df


def build_dashboard_html(df: pd.DataFrame) -> str:
    records_json = json.dumps(df.to_dict(orient="records"), ensure_ascii=False)
    filters = {
        "gender": sorted(df["gender"].unique().tolist()),
        "race_ethnicity": sorted(df["race/ethnicity"].unique().tolist()),
        "parental_education": sorted(df["parental level of education"].unique().tolist()),
        "lunch": sorted(df["lunch"].unique().tolist()),
        "prep_course": sorted(df["test preparation course"].unique().tolist()),
    }
    filters_json = json.dumps(filters, ensure_ascii=False)
    html = TEMPLATE_HTML.read_text(encoding="utf-8")
    plotly_js = get_plotlyjs()
    return (
        html.replace("__PLOTLY_JS__", plotly_js)
        .replace("__DATA_JSON__", records_json)
        .replace("__FILTERS_JSON__", filters_json)
    )


def main() -> None:
    df = load_and_enrich_data(SOURCE_CSV)
    df.to_csv(ENRICHED_CSV, index=False)
    DASHBOARD_HTML.write_text(build_dashboard_html(df), encoding="utf-8")
    print(f"Enriched CSV written to: {ENRICHED_CSV}")
    print(f"Dashboard written to: {DASHBOARD_HTML}")


if __name__ == "__main__":
    main()
