"""
Context / lifestyle micro-inputs (no sensors).
Feeds personalization: sleep, social, workload, activity.
"""

# —— "How are you feeling today?" (soft entry) ——
FEELING_TODAY_OPTIONS = [
    "Overwhelmed",
    "Anxious",
    "Low energy",
    "Sad",
    "Stressed",
    "Not sure",
]
FEELING_TODAY_PROMPT = "How are you feeling today?"

# —— "What do I need right now?" ——
WHAT_DO_I_NEED_OPTIONS = [
    "Rest",
    "Clarity",
    "Vent",
    "Motivation",
    "Calm",
]
WHAT_DO_I_NEED_PROMPT = "What do I need right now?"

# —— Context questions (1-tap) ——
CONTEXT_QUESTIONS = {
    "sleep_last_night": {
        "label": "Roughly how many hours did you sleep last night?",
        "options": ["Under 5", "5–6", "6–7", "7–8", "8+", "Prefer not to say"],
        "key": "sleep",
    },
    "social_today": {
        "label": "How much social connection have you had today?",
        "options": ["Almost none", "A little", "Some", "A lot", "Prefer not to say"],
        "key": "social",
    },
    "workload_stress": {
        "label": "How does your workload or stress feel right now?",
        "options": ["Manageable", "A bit much", "Overwhelming", "Prefer not to say"],
        "key": "workload",
    },
    "physical_activity": {
        "label": "Any physical activity today (walk, stretch, exercise)?",
        "options": ["None", "A little", "Some", "Yes, a good amount", "Prefer not to say"],
        "key": "activity",
    },
}

def detect_burnout_pattern(context: dict) -> bool:
    """Simple burnout signal: high workload + low motivation/energy (from feeling_today) + low activity."""
    workload = context.get("workload_stress")
    feeling = context.get("feeling_today", "")
    activity = context.get("physical_activity")
    low_energy = feeling in ("Low energy", "Overwhelmed", "Stressed")
    high_workload = workload in ("A bit much", "Overwhelming")
    low_activity = activity in ("None", "A little", None)
    return bool(high_workload and low_energy and low_activity)

def low_sleep(context: dict) -> bool:
    """Sleep under 6 hours."""
    s = context.get("sleep_last_night") or context.get("sleep")
    return s in ("Under 5", "5–6")

def low_social(context: dict) -> bool:
    s = context.get("social_today") or context.get("social")
    return s in ("Almost none", "A little")
