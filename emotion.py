"""
Light emotion/sentiment from one-sentence feeling (keyword/lexicon).
No heavy ML; use for "name what I'm feeling" + one action.
"""

import re

# Simple keyword → primary emotion (and optional secondary)
EMOTION_LEXICON = {
    "sadness": ["sad", "down", "low", "hopeless", "empty", "lonely", "grief", "crying", "tear", "miss", "lost"],
    "anxiety": ["anxious", "worry", "worried", "nervous", "panic", "scared", "afraid", "overwhelm", "overwhelmed", "can't focus", "racing"],
    "anger": ["angry", "mad", "frustrat", "irritat", "annoyed", "resent"],
    "fatigue": ["tired", "exhausted", "drain", "burnout", "no energy", "can't get up", "heavy"],
    "overwhelm": ["overwhelm", "too much", "can't cope", "drowning", "stuck", "paralyzed", "shut down"],
}

# Emotion → one simple action (evidence-informed, micro)
EMOTION_ACTION = {
    "sadness": "Reach out to one person—even a short text. You don’t have to explain everything; “I’ve been having a tough week” is enough.",
    "anxiety": "Try 4-7-8 breathing: breathe in for 4, hold for 7, out for 8. Do it 3–4 times. It can slow the nervous system.",
    "anger": "Step away for 2 minutes—get water, step outside, or stretch. Then name it: “I’m frustrated.” Sometimes naming it helps.",
    "fatigue": "One tiny step: get a glass of water, open the curtains, or step outside for 1 minute. You don’t have to do more.",
    "overwhelm": "Write down the one thing that would help most right now (even if it’s “rest”). Do only that, or a 5-minute version of it.",
}

DEFAULT_ACTION = "Take one small step that feels doable—a 2-minute walk, a glass of water, or one text to someone you trust."

def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower())

def detect_emotion(sentence: str) -> tuple[str | None, str]:
    """
    Returns (primary_emotion, suggested_action).
    primary_emotion can be None if no strong match.
    """
    if not sentence or not sentence.strip():
        return None, DEFAULT_ACTION
    normalized = _normalize(sentence)
    scores = {}
    for emotion, keywords in EMOTION_LEXICON.items():
        score = sum(1 for k in keywords if k in normalized)
        if score > 0:
            scores[emotion] = score
    if not scores:
        return None, DEFAULT_ACTION
    primary = max(scores, key=scores.get)
    action = EMOTION_ACTION.get(primary, DEFAULT_ACTION)
    return primary, action

def explain_emotion(emotion: str | None) -> str:
    """Short human-language explanation for the emotion."""
    if not emotion:
        return "Putting feelings into words can help. Try one small thing that feels doable."
    explanations = {
        "sadness": "You might be experiencing low mood or sadness. That’s real and it’s okay to need support.",
        "anxiety": "You might be experiencing worry or anxiety. Your mind may be under pressure—naming it and a small calming step can help.",
        "anger": "You might be feeling frustration or anger. Stepping back for a moment can help you choose how to respond.",
        "fatigue": "You might be experiencing emotional or physical fatigue. You’re not lazy—you may be overloaded.",
        "overwhelm": "You might be feeling overwhelmed. That happens when demands feel bigger than your resources. One small step is enough.",
    }
    return explanations.get(emotion, "What you’re feeling is valid. One small step can help.")
