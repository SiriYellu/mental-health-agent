"""
Train the coping ACTION recommender from exported feedback CSV.

Run locally (not on Streamlit Cloud):
  python scripts/train_coping_recommender.py path/to/feedback.csv

Output:
  ml/coping_action_model.joblib  - sklearn pipeline (preprocessor + classifier)
  ml/coping_action_meta.json     - action_ids, feature names, MODEL_VERSION

Target: action_taken (which action the user did).
Sample weights: helped_score → 2 (Yes), 1 (A little), 0.25 (Not really) so model favors actions that help.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Add repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from ml.actions import ACTION_IDS
from ml.feedback_schema import FEEDBACK_CSV_COLUMNS

ML_DIR = os.path.join(REPO_ROOT, "ml")
MODEL_PATH = os.path.join(ML_DIR, "coping_action_model.joblib")
META_PATH = os.path.join(ML_DIR, "coping_action_meta.json")

MODEL_VERSION = "0.2"

# Sample weight: helped_score 2 -> 2, 1 -> 1, 0 -> 0.25
HELPED_TO_WEIGHT = {2: 2.0, 1: 1.0, 0: 0.25}


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    for c in ["phq2_score", "gad2_score", "action_suggested", "action_taken", "helped_score"]:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")
    # Drop rows where user did not complete the action (better training signal)
    if "action_completed" in df.columns:
        before = len(df)
        df = df[df["action_completed"].fillna(0).astype(int) == 1].copy()
        dropped = before - len(df)
        if dropped:
            print(f"Dropped {dropped} rows with action_completed=0 (kept {len(df)} completed).")
    return df


def train(csv_path: str, out_model: str = MODEL_PATH, out_meta: str = META_PATH) -> None:
    df = load_data(csv_path)
    df = df.dropna(subset=["action_taken", "helped_score"])
    # Map action_taken to class index (backward compat: "breathing" -> breathing_60s)
    action_alias = {"breathing": "breathing_60s"}
    df["action_taken"] = df["action_taken"].replace(action_alias)
    action_to_idx = {a: i for i, a in enumerate(ACTION_IDS)}
    df["action_idx"] = df["action_taken"].map(lambda x: action_to_idx.get(x, -1))
    df = df[df["action_idx"] >= 0].copy()
    df["action_idx"] = df["action_idx"].astype(int)

    if len(df) < 20:
        print(f"Warning: only {len(df)} rows. Recommend at least 200 for a useful model.")

    y = df["action_idx"]
    # Sample weights from helped_score
    df["_weight"] = df["helped_score"].map(lambda s: HELPED_TO_WEIGHT.get(int(s) if s != "" else 1, 1.0))
    sample_weight = df["_weight"].values

    feature_cols = ["phq2_score", "gad2_score", "feeling_today", "workload_stress", "need_most", "text_emotion_label"]
    X = df[[c for c in feature_cols if c in df.columns]].copy()
    for c in feature_cols:
        if c not in X.columns:
            X[c] = ""

    numeric_features = ["phq2_score", "gad2_score"]
    categorical_features = [c for c in ["feeling_today", "workload_stress", "need_most", "text_emotion_label"] if c in X.columns]

    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ],
        remainder="drop",
    )

    clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
    pipe = Pipeline([("preprocessor", preprocessor), ("classifier", clf)])

    try:
        pipe.fit(X, y, classifier__sample_weight=sample_weight)
    except TypeError:
        pipe.fit(X, y)

    meta = {
        "action_ids": ACTION_IDS,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "MODEL_VERSION": MODEL_VERSION,
        "n_samples": len(df),
    }

    os.makedirs(ML_DIR, exist_ok=True)
    joblib.dump(pipe, out_model)
    with open(out_meta, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Saved model to {out_model}")
    print(f"Saved metadata to {out_meta}")
    print(f"Trained on {len(df)} samples. MODEL_VERSION={MODEL_VERSION}")


def main():
    parser = argparse.ArgumentParser(description="Train coping action recommender from feedback CSV")
    parser.add_argument("csv", help="Path to feedback CSV (exported from CalmCompass)")
    parser.add_argument("--model", default=MODEL_PATH, help="Output model path")
    parser.add_argument("--meta", default=META_PATH, help="Output metadata JSON path")
    args = parser.parse_args()
    train(args.csv, args.model, args.meta)


if __name__ == "__main__":
    main()
