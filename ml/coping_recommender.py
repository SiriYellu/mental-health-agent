"""
Coping recommender: recommend best ACTION (breathing_60s, grounding_54321, etc.)
given phq2, gad2, context. Uses trained model; fallback to rules. Crisis never driven by ML.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ml.actions import ACTION_IDS, suggest_action_rules

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(REPO_ROOT, "ml")
MODEL_PATH = os.path.join(ML_DIR, "coping_action_model.joblib")
META_PATH = os.path.join(ML_DIR, "coping_action_meta.json")

MIN_CONFIDENCE = 0.35  # Below this, use rule-based suggestion


def load_coping_model() -> tuple[Any, dict | None]:
    """Load action recommender pipeline and metadata. Call with @st.cache_resource in app."""
    if not os.path.isfile(MODEL_PATH) or not os.path.isfile(META_PATH):
        return None, None
    try:
        import joblib
        pipe = joblib.load(MODEL_PATH)
        with open(META_PATH) as f:
            meta = json.load(f)
        return pipe, meta
    except Exception:
        return None, None


def recommend_action(
    phq2_score: int,
    gad2_score: int,
    feeling_today: str | None,
    workload_stress: str | None,
    need_most: str | None,
    text_emotion_label: str | None,
    pipe=None,
    meta: dict | None = None,
) -> tuple[str, float]:
    """
    Recommend one action_id. Returns (action_id, confidence).
    If no model or confidence < MIN_CONFIDENCE, uses rule-based suggestion and returns (action_id, 0.0).
    """
    import pandas as pd

    action_ids = meta.get("action_ids", ACTION_IDS) if meta else ACTION_IDS

    if pipe is None or meta is None:
        pipe, meta = load_coping_model()

    if pipe is None or meta is None:
        suggested = suggest_action_rules(
            phq2_score, gad2_score, feeling_today, workload_stress, text_emotion_label
        )
        return suggested, 0.0

    row = pd.DataFrame([{
        "phq2_score": phq2_score,
        "gad2_score": gad2_score,
        "feeling_today": feeling_today or "",
        "workload_stress": workload_stress or "",
        "need_most": need_most or "",
        "text_emotion_label": text_emotion_label or "",
    }])

    try:
        pred = pipe.predict(row)[0]
        proba = pipe.predict_proba(row)[0]
        idx = int(pred) if hasattr(pred, "__int__") else 0
        if idx < len(action_ids):
            action_id = action_ids[idx]
        else:
            action_id = action_ids[0]
        conf = float(proba[idx]) if hasattr(proba, "__getitem__") else 0.5
        if conf < MIN_CONFIDENCE:
            action_id = suggest_action_rules(
                phq2_score, gad2_score, feeling_today, workload_stress, text_emotion_label
            )
            return action_id, 0.0
        return action_id, conf
    except Exception:
        suggested = suggest_action_rules(
            phq2_score, gad2_score, feeling_today, workload_stress, text_emotion_label
        )
        return suggested, 0.0
