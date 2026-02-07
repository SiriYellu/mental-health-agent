"""
Validated screening instruments: PHQ-9, GAD-7, PSS-4.
Not a diagnosis — for awareness and when to seek help only.
"""

# —— Response options (0–3 frequency, 4 = Prefer not to answer) ——
OPTIONS = [
    "Not at all",
    "Several days",
    "More than half the days",
    "Nearly every day",
    "Prefer not to answer",
]

# —— PHQ-2 (quick) ——
PHQ2_QUESTIONS = [
    "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
    "Over the last 2 weeks, how often have you been feeling down, depressed, or hopeless?",
]

# —— PHQ-9 (full depression screen, 0–27) ——
PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading the newspaper or watching television",
    "Moving or speaking so slowly that other people could have noticed — or the opposite; being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead or of hurting yourself in some way",
]
PHQ9_PREFIX = "Over the last 2 weeks, how often have you been bothered by the following?"

# —— GAD-2 (quick) ——
GAD2_QUESTIONS = [
    "Over the last 2 weeks, how often have you been feeling nervous, anxious, or on edge?",
    "Over the last 2 weeks, how often have you not been able to stop or control worrying?",
]

# —— GAD-7 (full anxiety screen, 0–21) ——
GAD7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it's hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen",
]
GAD7_PREFIX = "Over the last 2 weeks, how often have you been bothered by the following?"

# —— PSS-4 (Perceived Stress Scale, 4 items, 0–16) ——
PSS4_QUESTIONS = [
    "In the last month, how often have you felt that you were unable to control the important things in your life?",
    "In the last month, how often have you felt confident about your ability to handle your personal problems?",
    "In the last month, how often have you felt that things were going your way?",
    "In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
]
# PSS-4: Q0 and Q3 are positive-wording (higher = more stress); Q1 and Q2 are reverse-scored
PSS4_REVERSE = [False, True, True, False]  # reverse 1 and 2

# —— Self-harm question ——
SELF_HARM_QUESTION = "Are you having thoughts of harming yourself today?"
SELF_HARM_CHOICES = ["No", "Yes", "Prefer not to say"]

PREFER_NOT_ANSWER = 4

def _cap_score(a: int) -> int:
    """Score 0–3 for one item; Prefer not to answer is excluded from sum (not treated as numeric)."""
    return min(a, 3) if a != PREFER_NOT_ANSWER else 0

def _scored_items(answers: list[int]) -> list[int]:
    """Values to sum (only 0–3; exclude Prefer not to answer)."""
    return [_cap_score(a) for a in answers if a != PREFER_NOT_ANSWER]

# —— PHQ-2: partial scoring (0 answered → None; 1 or 2 answered → score from answered items) ——
def score_phq2(answers: list[int]) -> tuple[int | None, int, int]:
    """
    Returns (score, answered_count, total_items).
    If answered_count == 0, score is None. Else score is sum of answered items (0–3 each).
    """
    if len(answers) != 2:
        raise ValueError("PHQ-2 requires exactly 2 answers")
    total = 2
    scored = _scored_items(answers)
    answered = len(scored)
    if answered == 0:
        return (None, 0, total)
    return (sum(scored), answered, total)

# —— PHQ-9 (partial not used in main flow; keep simple: any skip → None for now) ——
def _has_skip(answers: list[int]) -> bool:
    return any(a == PREFER_NOT_ANSWER for a in answers)

def score_phq9(answers: list[int]) -> int | None:
    if len(answers) != 9:
        return None
    if _has_skip(answers):
        return None
    return sum(_cap_score(a) for a in answers)

def phq9_severity(score: int) -> str:
    if score <= 4: return "minimal"
    if score <= 9: return "mild"
    if score <= 14: return "moderate"
    if score <= 19: return "moderately_severe"
    return "severe"

# PHQ-9 item 9 (index 8) is suicidal ideation — critical for crisis
def phq9_has_suicidal_ideation(answers: list[int]) -> bool:
    return len(answers) >= 9 and answers[8] == 3  # "Nearly every day"

# —— GAD-2: partial scoring (same as PHQ-2) ——
def score_gad2(answers: list[int]) -> tuple[int | None, int, int]:
    """Returns (score, answered_count, total_items). If answered_count == 0, score is None."""
    if len(answers) != 2:
        raise ValueError("GAD-2 requires exactly 2 answers")
    total = 2
    scored = _scored_items(answers)
    answered = len(scored)
    if answered == 0:
        return (None, 0, total)
    return (sum(scored), answered, total)

# —— GAD-7 ——
def score_gad7(answers: list[int]) -> int | None:
    if len(answers) != 7:
        return None
    if _has_skip(answers):
        return None
    return sum(_cap_score(a) for a in answers)

def gad7_severity(score: int) -> str:
    if score <= 4: return "minimal"
    if score <= 9: return "mild"
    if score <= 14: return "moderate"
    return "severe"

# —— PSS-4 ——
def score_pss4(answers: list[int]) -> int | None:
    if len(answers) != 4:
        return None
    if _has_skip(answers):
        return None
    total = 0
    for i, a in enumerate(answers):
        val = _cap_score(a)
        if PSS4_REVERSE[i]:
            val = 3 - val  # 0->3, 1->2, 2->1, 3->0
        total += val
    return total

def pss4_level(score: int) -> str:
    if score <= 4: return "low"
    if score <= 8: return "moderate"
    return "high"

# —— Interpretations (human language, not clinical) ——
def interpret_phq2(score: int | None, partial_note: bool = False) -> dict:
    if score is None:
        return {"level": "unknown", "message": "You skipped one or more answers. That’s okay. If you’d like to talk to someone about how you’ve been feeling, that’s always an option.", "score": None}
    if score <= 2:
        return {"level": "minimal", "message": "Over the last 2 weeks, your answers don’t suggest much low mood. Small habits like staying connected and moving a little can still help keep things on track.", "score": score}
    return {"level": "worth_following_up", "message": "Over the last 2 weeks you’ve been having a tough time with mood. That’s a sign it could help to share with someone you trust or a professional—you don’t have to wait until things feel “bad enough.”", "score": score}

def interpret_gad2(score: int | None, partial_note: bool = False) -> dict:
    if score is None:
        return {"level": "unknown", "message": "You skipped one or more answers. If worry or anxiety is on your mind, talking to someone can help.", "score": None}
    if score <= 2:
        return {"level": "minimal", "message": "Over the last 2 weeks, your answers don’t suggest much anxiety. Keeping a simple routine and short check-ins with others can still help.", "score": score}
    return {"level": "worth_following_up", "message": "Over the last 2 weeks worry or anxiety has been showing up more. Reaching out to a professional or someone you trust is a good next step.", "score": score}

# Human-language understanding messages by PHQ-9 / GAD-7 severity (for "understanding first" results)
UNDERSTANDING_BY_PHQ9 = {
    "minimal": "Your answers don’t suggest much low mood lately. That’s a good sign. Small habits—sleep, connection, a bit of movement—can help keep things steady.",
    "mild": "You’ve been carrying a bit more emotional weight than usual. That doesn’t mean something is wrong with you—it means you’ve been under pressure. Reaching out to someone you trust can help.",
    "moderate": "You may be experiencing emotional fatigue. You’ve been carrying a lot. This doesn’t mean something is wrong with you—it means your system could use some support. Talking to a professional or someone you trust is a strong next step.",
    "moderately_severe": "You’ve been going through a lot. What you’re feeling is real and it’s heavy. You don’t have to handle it alone. Reaching out to a professional or someone you trust can make a real difference.",
    "severe": "You’ve been carrying more than anyone should have to. What you’re feeling is real. You deserve support. Please consider reaching out to a professional or someone you trust—and if you have thoughts of hurting yourself, 988 is there 24/7.",
}

UNDERSTANDING_BY_GAD7 = {
    "minimal": "Your answers don’t suggest much anxiety lately. Keeping a simple routine and short check-ins with others can help.",
    "mild": "It looks like your mind has been under a bit of pressure lately. This happens when we carry unresolved worries. Naming it and one small step (breathing, a walk, or sharing with someone) can help.",
    "moderate": "Your mind has been under real pressure. That’s exhausting. You’re not overreacting—you’re carrying a lot. Grounding, breathing, and talking to someone can help.",
    "severe": "Worry and anxiety have been taking up a lot of space. That’s really hard. You deserve support. Reaching out to a professional or someone you trust—and using 988 if things feel too heavy—can help.",
}

def get_understanding_phq9(score: int | None) -> str:
    if score is None:
        return "If you’d like to talk to someone about how you’ve been feeling, that’s always an option."
    return UNDERSTANDING_BY_PHQ9.get(phq9_severity(score), UNDERSTANDING_BY_PHQ9["minimal"])

def get_understanding_gad7(score: int | None) -> str:
    if score is None:
        return "If worry or anxiety is on your mind, talking to someone can help."
    return UNDERSTANDING_BY_GAD7.get(gad7_severity(score), UNDERSTANDING_BY_GAD7["minimal"])

# —— Crisis (only from full answer; skip not "nearly every day") ——
def is_crisis_by_score(phq2_answers: list[int]) -> bool:
    """Q2 (hopelessness) answered "Nearly every day" (3). Ignore Prefer not to answer (4)."""
    if len(phq2_answers) < 2:
        return False
    return phq2_answers[1] == 3

def is_crisis_phq9(phq9_answers: list[int]) -> bool:
    return phq9_has_suicidal_ideation(phq9_answers)

def is_elevated(phq2_score: int | None, gad2_score: int | None) -> bool:
    if phq2_score is not None and phq2_score >= 3:
        return True
    if gad2_score is not None and gad2_score >= 3:
        return True
    return False

def is_elevated_phq9_gad7(phq9_score: int | None, gad7_score: int | None) -> bool:
    if phq9_score is not None and phq9_score >= 10:
        return True
    if gad7_score is not None and gad7_score >= 10:
        return True
    return False

def is_crisis(phq2_answers: list[int]) -> bool:
    return is_crisis_by_score(phq2_answers)
