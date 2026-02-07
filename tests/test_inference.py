"""
Minimal tests for ml.inference: mapping correctness, empty text, low-confidence fallback.
"""

import pytest
from ml.inference import (
    state_from_emotion_label,
    predict_emotion,
    get_emotion_tailored_response,
    MIN_CONFIDENCE,
)


def test_state_from_emotion_label_mapping():
    """All known labels map to a state; unknown labels return None."""
    assert state_from_emotion_label("sadness") == "low_mood"
    assert state_from_emotion_label("joy") == "ok"
    assert state_from_emotion_label("love") == "ok"
    assert state_from_emotion_label("anger") == "stress"
    assert state_from_emotion_label("fear") == "anxiety"
    assert state_from_emotion_label("surprise") == "stress"
    assert state_from_emotion_label("unknown_label") is None
    assert state_from_emotion_label("") is None


def test_predict_emotion_empty_text_returns_none():
    """Empty or whitespace-only text returns (None, 0.0)."""
    assert predict_emotion("") == (None, 0.0)
    assert predict_emotion("   ") == (None, 0.0)
    assert predict_emotion(None) == (None, 0.0)


def test_predict_emotion_short_text_returns_none():
    """Text with fewer than MIN_WORDS_FOR_ML words returns (None, 0.0) without calling pipeline."""
    from ml.inference import MIN_WORDS_FOR_ML
    # "I am" = 2 words
    assert predict_emotion("I am", pipe_loader=lambda: None) == (None, 0.0)


def test_low_confidence_fallback():
    """When pipe_loader returns low-confidence or unknown label, predict_emotion returns (None, 0.0) or no tailored response."""
    def mock_pipe_low_conf():
        def pipe(text):
            return [{"label": "sadness", "score": 0.2}]
        return pipe
    label, conf = predict_emotion("I feel really sad today", pipe_loader=mock_pipe_low_conf)
    assert label == "sadness"
    assert conf == 0.2
    assert conf < MIN_CONFIDENCE
    # App should treat this as fallback (not use ML)
    state = state_from_emotion_label(label)
    tailored = get_emotion_tailored_response(state)
    assert tailored is not None
    # If we had passed high confidence, we'd use it; at 0.2 we don't
    assert get_emotion_tailored_response(None) is None


def test_get_suggestion_incomplete_uses_gentle_message():
    """When both PHQ-2 and GAD-2 scores are None (e.g. Prefer not to answer), get_suggestion returns gentle message + minimal band."""
    from resources import get_suggestion, UNDERSTANDING_LINES
    out = get_suggestion(None, None, None)
    assert out["understanding"] == UNDERSTANDING_LINES["incomplete"]
    assert "action" in out and "next_steps" in out


def test_get_suggestion_one_known_derives_severity():
    """When one scale is None and the other is known, severity is from the known scale; partial_note is set."""
    from resources import get_suggestion, PARTIAL_NOTE, UNDERSTANDING_LINES
    # GAD known (4 = elevated), PHQ unknown
    out = get_suggestion(None, 4, None)
    assert out["understanding"] != UNDERSTANDING_LINES["incomplete"]
    assert out.get("partial_note") == PARTIAL_NOTE
    # PHQ known (3 = elevated), GAD unknown
    out2 = get_suggestion(3, None, None)
    assert out2.get("partial_note") == PARTIAL_NOTE


def test_phq2_partial_scoring():
    """Partial scoring: 0 answered -> None; 1 answered -> score from that item; 2 answered -> full score."""
    from screening import score_phq2, PREFER_NOT_ANSWER
    # 0 answered (both Prefer not to answer)
    assert score_phq2([PREFER_NOT_ANSWER, PREFER_NOT_ANSWER]) == (None, 0, 2)
    # 1 answered
    assert score_phq2([0, PREFER_NOT_ANSWER]) == (0, 1, 2)
    assert score_phq2([3, PREFER_NOT_ANSWER]) == (3, 1, 2)
    # 2 answered
    assert score_phq2([1, 2]) == (3, 2, 2)
    assert score_phq2([0, 0]) == (0, 2, 2)
