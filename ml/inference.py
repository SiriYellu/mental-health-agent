"""
Lightweight emotion classifier for one-sentence feeling.
Model loaded once with Streamlit cache. No external API; no storage.
Fallback to rule-based if model load fails.
"""

from __future__ import annotations

EMOTION_TO_STATE = {
    "sadness": "low_mood",
    "joy": "ok",
    "love": "ok",
    "anger": "stress",
    "fear": "anxiety",
    "surprise": "stress",
}

# Emotion-based tailoring: state -> (understanding_snippet, action_snippet)
# Used to slightly tailor the main suggestion when ML predicts an emotion.
EMOTION_TAILORED = {
    "low_mood": (
        "What you wrote sounds like it might reflect low mood or sadness. That’s real, and it’s okay to need support.",
        "Reach out to one person—even a short text. “I’ve been having a tough week” is enough.",
    ),
    "anxiety": (
        "What you wrote might reflect worry or anxiety. Your mind may be under pressure—a small calming step can help.",
        "Try 4-7-8 breathing: breathe in 4, hold 7, out 8. Do it 3–4 times. It can slow your nervous system.",
    ),
    "stress": (
        "What you wrote might reflect stress or frustration. Stepping back for a moment can help you choose how to respond.",
        "Step away for 2 minutes—get water, step outside, or stretch. Then name it: “I’m stressed.” Sometimes naming it helps.",
    ),
    "ok": (
        "It’s good you’re checking in. Small habits can help keep things on track.",
        "Do one small thing in the next 10 minutes: a short walk, a glass of water, or one text to someone you trust.",
    ),
}

# Minimum confidence to use ML result (otherwise fall back to rule-based)
MIN_CONFIDENCE = 0.35
# Skip ML for very short input (noisy)
MIN_WORDS_FOR_ML = 3


def _load_pipeline():
    """Load HuggingFace emotion pipeline. Cached by Streamlit."""
    try:
        from transformers import pipeline
        return pipeline(
            "text-classification",
            model="bhadresh-savani/distilbert-base-uncased-emotion",
            top_k=1,
            return_all_scores=False,
        )
    except Exception:
        return None


def predict_emotion(text: str | None, pipe_loader=None):
    """
    Predict emotion from one sentence.
    Returns (label, confidence) or (None, 0.0) on empty/failure.
    Skips ML if text has fewer than MIN_WORDS_FOR_ML words (noisy).
    pipe_loader: optional callable that returns the pipeline (for caching via st.cache_resource).
    """
    if text is None or not text.strip():
        return None, 0.0
    text = text.strip()[:512]
    if len(text.split()) < MIN_WORDS_FOR_ML:
        return None, 0.0
    try:
        if pipe_loader is not None:
            pipe = pipe_loader()
        else:
            pipe = _load_pipeline()
        if pipe is None:
            return None, 0.0
        out = pipe(text)
        if out and len(out) > 0:
            label = (out[0].get("label") or "").strip().lower()
            score = float(out[0].get("score", 0.0))
            if label not in EMOTION_TO_STATE:
                return None, 0.0
            return label, score
    except Exception:
        pass
    return None, 0.0


def get_emotion_tailored_response(state: str | None) -> tuple[str, str] | None:
    """
    Get (understanding_snippet, action_snippet) for internal state from emotion model.
    state: one of low_mood, anxiety, stress, ok. Returns None if state is None or unknown.
    """
    return EMOTION_TAILORED.get(state) if state else None


def state_from_emotion_label(label: str) -> str | None:
    """Map HuggingFace emotion label to internal state. Returns None if label not in mapping (→ fallback)."""
    return EMOTION_TO_STATE.get(label) if label else None
