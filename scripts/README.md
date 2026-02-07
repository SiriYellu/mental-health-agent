# Training scripts (run locally, not on Streamlit Cloud)

## Coping action recommender

Trains a model that recommends the best **action** (breathing_60s, grounding_54321, reframe_prompt, tiny_task, short_walk, reach_out) based on PHQ-2, GAD-2, and context. Uses **helpfulness-weighted learning** (sample_weight: Yes=2, A little=1, Not really=0.25).

### 1. Collect data in the app

- Complete a check-in. On the results page you’ll see **6 actions** with **Start now**.
- Check **Help improve suggestions (anonymous)**.
- Click **Start now** on any action, do it, then answer **Did this help?** (Yes / A little / Not really).
- Open **Export my feedback (for training)** and download the CSV.

Repeat to build a dataset. **Aim for at least 200 rows** and a mix of actions.

### 2. Train locally

```bash
cd /path/to/ai agent
pip install -r requirements.txt
python scripts/train_coping_recommender.py path/to/calmcompass-feedback-YYYYMMDD-HHMM.csv
```

Output:

- `ml/coping_action_model.joblib` — sklearn pipeline (preprocessor + classifier)
- `ml/coping_action_meta.json` — action_ids, MODEL_VERSION, feature names

### 3. Deploy

Commit `ml/coping_action_model.joblib` and `ml/coping_action_meta.json`. The app loads with `@st.cache_resource` and suggests one action when confidence ≥ 0.35; otherwise uses rule-based suggestion.

### CSV schema

| Column              | Description |
|---------------------|-------------|
| timestamp_date      | YYYY-MM-DD  |
| phq2_score          | 0–6         |
| gad2_score          | 0–6         |
| feeling_today       | From context |
| workload_stress     | From context |
| need_most           | (optional)  |
| text_emotion_label  | (optional)  |
| action_suggested   | Action the app recommended |
| action_taken       | Action the user did (e.g. breathing_60s) |
| helped_score        | 0 = Not really, 1 = A little, 2 = Yes |
| ml_used            | 0 or 1      |
| confidence         | Model confidence (if ml_used) |

### Safety

- No medical claims; the model only picks which action to suggest.
- Crisis logic (self-harm, 988) is never driven by this model.
- If the model is missing or confidence is low, the app uses rule-based suggestion only.
