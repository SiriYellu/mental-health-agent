"""
Coping actions: 6 concrete actions the user can take. Used for recommendation and feedback.
Model recommends one action_id; rules fallback maps (phq2, gad2, context, emotion) → action_id.
"""

from typing import Any

# All action IDs (must match training and feedback schema)
ACTION_IDS = [
    "breathing_60s",
    "grounding_54321",
    "reframe_prompt",
    "tiny_task",
    "short_walk",
    "reach_out",
]

# For display and "Start now" flows
ACTIONS = [
    {"id": "breathing_60s", "label": "60-second breathing", "short": "Breathe 4-7-8 for 60 seconds.", "emoji": "🫁"},
    {"id": "grounding_54321", "label": "5-4-3-2-1 grounding", "short": "Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you're okay about.", "emoji": "🌿"},
    {"id": "reframe_prompt", "label": "Reframe prompt", "short": "What's one small step that would help right now? (Write or say it.)", "emoji": "💭"},
    {"id": "tiny_task", "label": "2-minute cleanup", "short": "Pick one small thing (e.g. clear the desk, fill water) and do it for 2 minutes.", "emoji": "🧹"},
    {"id": "short_walk", "label": "2-minute walk", "short": "Step outside or walk around the room for 2 minutes.", "emoji": "🚶"},
    {"id": "reach_out", "label": "Reach out", "short": "Copy a message to send to someone you trust.", "emoji": "💬"},
]


def get_action_by_id(action_id: str) -> dict[str, Any] | None:
    for a in ACTIONS:
        if a["id"] == action_id:
            return a
    return None


def suggest_action_rules(
    phq2_score: int,
    gad2_score: int,
    feeling_today: str | None,
    workload_stress: str | None,
    text_emotion_label: str | None,
) -> str:
    """
    Rule-based suggested action (fallback when no model or low confidence).
    Returns action_id.
    """
    elevated_phq = phq2_score >= 3
    elevated_gad = gad2_score >= 3
    feeling = (feeling_today or "").lower()
    workload = (workload_stress or "").lower()
    emotion = (text_emotion_label or "").lower()

    # Anxiety / worry → breathing or grounding
    if elevated_gad or "anxious" in emotion or "anxiety" in feeling:
        return "breathing_60s"
    if "overwhelm" in feeling or "overwhelmed" in feeling:
        return "reframe_prompt"
    if "low" in feeling or "sad" in feeling or elevated_phq:
        return "reach_out"
    if "stressed" in feeling or "stress" in workload:
        return "short_walk"
    if "burnout" in workload or "overwhelming" in workload:
        return "tiny_task"
    # Default
    return "breathing_60s"
