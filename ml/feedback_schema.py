"""
Coping recommender training data: schema and helpers.
Feedback collected only when user opts in, after "Did this help?" (Yes / A little / Not really).
Model learns: which ACTION works best for which (scores, context). No PII.
"""

import csv
import io
from datetime import date
from typing import Any

# CSV columns for training (same order for export and training script)
FEEDBACK_CSV_COLUMNS = [
    "timestamp_date",
    "phq2_score",
    "gad2_score",
    "feeling_today",
    "workload_stress",
    "need_most",
    "text_emotion_label",
    "action_suggested",
    "action_taken",
    "helped_score",
    "ml_used",
    "confidence",
]

# helped_score: 2 = Yes, 1 = A little, 0 = Not really (used for sample_weight: 2, 1, 0.25)
HELPED_SCORE_MAP = {"yes": 2, "a_little": 1, "not_really": 0}


def build_feedback_row(
    phq2_score: int,
    gad2_score: int,
    feeling_today: str | None,
    workload_stress: str | None,
    need_most: str | None,
    text_emotion_label: str | None,
    action_suggested: str,
    action_taken: str,
    result_help: str,
    ml_used: bool,
    confidence: float,
) -> dict[str, Any]:
    """Build one feedback row for app session state. Use for CSV export and training."""
    return {
        "timestamp_date": date.today().isoformat(),
        "phq2_score": phq2_score,
        "gad2_score": gad2_score,
        "feeling_today": feeling_today or "",
        "workload_stress": workload_stress or "",
        "need_most": need_most or "",
        "text_emotion_label": text_emotion_label or "",
        "action_suggested": action_suggested,
        "action_taken": action_taken,
        "helped_score": HELPED_SCORE_MAP.get(result_help, 1),
        "ml_used": 1 if ml_used else 0,
        "confidence": round(confidence, 4) if confidence is not None else "",
    }


def feedback_rows_to_csv(feedback_rows: list[dict[str, Any]]) -> str:
    """Convert list of feedback dicts to CSV string (for download)."""
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=FEEDBACK_CSV_COLUMNS, extrasaction="ignore")
    w.writeheader()
    for row in feedback_rows:
        w.writerow({k: row.get(k, "") for k in FEEDBACK_CSV_COLUMNS})
    return out.getvalue()
