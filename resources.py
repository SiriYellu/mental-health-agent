"""
Crisis resources, micro-actions, intervention mapping, coping plan, grounding.
Uses resources/*.json for region-specific crisis lines.
"""

import json
import os

# —— "I need support now" (skip screening) ——
SUPPORT_NOW_HEADING = "You’re not alone. Here’s something you can do right now."
SUPPORT_NOW_CALMING = (
    "It’s okay to pause. You don’t have to fix anything in the next few minutes. "
    "Try the breathing or grounding below. If things feel too heavy, 988 is there 24/7—call or text."
)
BREATHING_60_SEC = (
    "**60-second breathing**\n\n"
    "Breathe in for 4 counts, hold for 7, breathe out for 8. Repeat 3–4 times. "
    "This can help slow your nervous system and bring you into the present."
)

# —— "What do I need right now?" → one action ——
WHAT_DO_I_NEED_ACTIONS = {
    "Rest": "Give yourself permission to rest. Even 10 minutes with no phone, eyes closed or looking out a window, counts. You’re not lazy—you’re recharging.",
    "Clarity": "Write down the one thing that would help most right now (one sentence). You don’t have to do it yet—just name it. Sometimes clarity reduces the noise.",
    "Vent": "Say it out loud to an empty room, or write it in a note you don’t have to send. Getting it out can create a little space.",
    "Motivation": "One tiny step: stand up, get a glass of water, or step outside for 1 minute. You don’t have to do more than that.",
    "Calm": "Try 4-7-8 breathing: in 4, hold 7, out 8. Do it 3–4 times. Or name 5 things you can see—it can ground you in the present.",
}

# —— Intervention map: state (from feeling_today / severity) → primary support type ——
# Used to pick ONE micro-action and support block (evidence-based: CBT/ACT/DBT-informed)
INTERVENTION_MAP = {
    "anxiety": {"action": "Try 4-7-8 breathing (in 4, hold 7, out 8) a few times, then name one thing you can do in the next hour.", "block": "grounding_breathing"},
    "overwhelm": {"action": "Write down the one thing that would help most right now. Do a 5-minute version of it—nothing more.", "block": "prioritization"},
    "low_mood": {"action": "Reach out to one person—even a short text. “I’ve been having a tough week” is enough.", "block": "connection"},
    "stress": {"action": "Pick one thing to drop or postpone today. Block 10 minutes of break and treat it as non-negotiable.", "block": "boundaries"},
    "burnout": {"action": "You’re not lazy—you’re overloaded. Rest is not a reward; it’s a need. Do one thing that gives you a boundary (e.g. close the laptop for 30 min).", "block": "boundaries_rest"},
    "loneliness": {"action": "Send one message: “Hey, I’ve been feeling off lately. Can we talk for 10 minutes?” You don’t have to explain everything.", "block": "connection"},
}
BURNOUT_MESSAGE = "You’re not lazy. You’re overloaded. Rest and boundaries aren’t luxuries—they’re what keep you going."

# —— Talk to someone: draft messages ——
TALK_TO_SOMEONE_DRAFTS = [
    "Hey, I’ve been having a tough week. Can we talk for 10 minutes?",
    "I’ve been feeling off lately and could use a chat. Free sometime?",
    "No need to fix anything—I just need to vent for a bit. Are you around?",
]

def get_talk_draft(flavor: str | None = None) -> str:
    if flavor == "work":
        return "I’ve been under a lot of pressure lately and could use someone to talk to. Do you have a few minutes?"
    if flavor == "family":
        return "I’ve been struggling a bit and would love to talk. Can we find a time?"
    return TALK_TO_SOMEONE_DRAFTS[0]

# —— Crisis (two triggers) ——

CRISIS_MESSAGE_IMMEDIATE = """
**If you are in immediate danger, call 911 or your local emergency number.**

**You’re not alone. Reach out now.**

- **988 Suicide & Crisis Lifeline** — Call or text **988** (US, 24/7)
- **Crisis Text Line** — Text **HOME** to **741741** (24/7)

You don’t have to be in crisis to use these lines. They are there for support.
"""

CRISIS_MESSAGE_ELEVATED = """
Your answers suggest you’ve been having a really hard time. Reaching out to someone can help.

- **988 Suicide & Crisis Lifeline** — Call or text **988** (US, 24/7)
- **Crisis Text Line** — Text **HOME** to **741741** (24/7)
"""

# —— Suggestion engine: severity + context → 1 action + 2 next steps (structured, no hardcoding in app) ——
# Severity from PHQ-2/GAD-2: "minimal" (both 0–2) vs "elevated" (either 3+)
SUGGESTION_ENGINE = {
    "minimal": {
        "action": "Do one small thing in the next 10 minutes: a short walk, a glass of water, or one text to someone you trust.",
        "next_steps": [
            "This week: pick one consistent bedtime and stick to it.",
            "Save 988 and Crisis Text Line (741741) in your phone so they’re there if you need them.",
        ],
    },
    "elevated": {
        "action": "Right now: tell one person you trust that you’ve been having a tough time (even by text). You don’t have to explain everything.",
        "next_steps": [
            "This week: look up one therapist or counselor (your doctor, school, or workplace can refer).",
            "If you have thoughts of hurting yourself, call or text 988 anytime.",
        ],
    },
    "elevated_anxiety": {
        "action": "Try 4-7-8 breathing: breathe in 4, hold 7, out 8. Do it 3–4 times. It can slow your nervous system.",
        "next_steps": [
            "Name it: “I’m having a wave of worry.” Sometimes that alone helps.",
            "Write down the one thing that would help most right now—then do a 5-minute version of it.",
        ],
    },
    "elevated_mood": {
        "action": "Reach out to one person—even a short text. “I’ve been having a tough week” is enough.",
        "next_steps": [
            "One tiny step counts: get outside for 2 minutes, or open the curtains.",
            "This week: consider sharing how you feel with a professional or someone you trust.",
        ],
    },
    "burnout": {
        "action": "You’re not lazy—you’re overloaded. Do one thing that gives you a boundary: e.g. close the laptop for 30 minutes.",
        "next_steps": [
            "Pick one thing to drop or postpone this week.",
            "Block 15 minutes of break in your calendar and treat it as non-negotiable.",
        ],
    },
}
# One-line understanding (empathetic, non-clinical); key = minimal | elevated | incomplete
UNDERSTANDING_LINES = {
    "minimal": "Your answers suggest you’ve been doing okay lately. Small habits can still help keep things on track.",
    "elevated": "You’ve been carrying more than usual. That doesn’t mean something is wrong with you—it means you could use some support.",
    "incomplete": "You skipped some answers—that’s okay. Here’s something that might help regardless.",
}
REASSURANCE_LINE = "You don’t have to do everything. One small step is enough."
SUPPORT_LINE = "988 (call or text) and Crisis Text Line (text HOME to 741741) are there 24/7. This is not a substitute for professional care."

PARTIAL_NOTE = "Some questions were skipped, so this is a general guide."

def get_suggestion(phq2_score: int | None, gad2_score: int | None, context: dict | None) -> dict:
    """Returns { understanding, action, reassurance, next_steps, support, partial_note? }. No PII.
    Derive severity from whichever scale is available; if one is None, still use the other. Add partial_note when any score is missing."""
    ctx = context or {}
    elevated_phq = phq2_score is not None and phq2_score >= 3
    elevated_gad = gad2_score is not None and gad2_score >= 3
    both_unknown = phq2_score is None and gad2_score is None
    any_unknown = phq2_score is None or gad2_score is None
    severity = "incomplete" if both_unknown else ("elevated" if (elevated_phq or elevated_gad) else "minimal")
    elevated = elevated_phq or elevated_gad
    # Context overrides
    if ctx.get("workload_stress") in ("A bit much", "Overwhelming") and (
        ctx.get("feeling_today") in ("Low energy", "Overwhelmed", "Stressed") or elevated
    ):
        band = "burnout"
    elif elevated and elevated_gad and not elevated_phq:
        band = "elevated_anxiety"
    elif elevated and elevated_phq:
        band = "elevated_mood"
    elif elevated:
        band = "elevated"
    else:
        band = "minimal"
    entry = SUGGESTION_ENGINE.get(band, SUGGESTION_ENGINE["minimal"])
    out = {
        "understanding": UNDERSTANDING_LINES.get(severity, UNDERSTANDING_LINES["minimal"]),
        "action": entry["action"],
        "reassurance": REASSURANCE_LINE,
        "next_steps": entry["next_steps"],
        "support": SUPPORT_LINE,
    }
    if any_unknown and not both_unknown:
        out["partial_note"] = PARTIAL_NOTE
    return out

# —— Micro-actions by severity (1–3 doable steps) ——

MICRO_ACTIONS_MINIMAL = [
    "Today: Do one small thing you enjoy (e.g. 10 min walk, call a friend).",
    "This week: Pick one consistent time to sleep and stick to it.",
    "Optional: Save 988 and Crisis Text Line (741741) in your phone so they’re there if you need them.",
]

MICRO_ACTIONS_ELEVATED = [
    "Today: Tell one person you trust that you’ve been struggling (even by text).",
    "This week: Look up one therapist or counselor (your doctor, school, or workplace can refer).",
    "Right now: If you have thoughts of hurting yourself, call or text 988.",
]

# —— Follow-up: "What feels hardest?" → tailored suggestions ——

FOLLOW_UP_PROMPT = "What feels hardest right now? (Pick one—we’ll suggest next steps.)"
FOLLOW_UP_OPTIONS = [
    "Sleep",
    "Motivation",
    "Worry or anxiety",
    "Relationships",
    "Workload or stress",
]

FOLLOW_UP_TIPS = {
    "Sleep": [
        "Try a consistent bedtime and no screens 30–60 min before bed.",
        "Keep the room cool and dark; avoid caffeine after midday.",
        "If your mind races, try writing a short to-do list for tomorrow, then put it away.",
    ],
    "Motivation": [
        "One tiny step counts: get out of bed, open the curtains, or step outside for 2 minutes.",
        "Break one task into a 5-minute version and do just that.",
        "Tell someone you’re having a low-energy day so they don’t expect more than you can give.",
    ],
    "Worry or anxiety": [
        "Name it: “I’m having a wave of worry.” Sometimes that alone reduces the grip.",
        "Try 4-7-8 breathing: breathe in 4, hold 7, out 8 (a few times).",
        "Write down the worst-case and one small thing you can do today about it.",
    ],
    "Relationships": [
        "Send one short message: “Hey, I’ve had a tough week. Can we talk for 10 minutes?”",
        "You don’t have to explain everything—just “I’ve been stressed” is enough.",
        "If someone has offered to help, say yes to one small thing (e.g. a walk, a call).",
    ],
    "Workload or stress": [
        "Pick one thing to drop or postpone this week (even if it feels “wrong”).",
        "Block 15 minutes of break in your calendar and treat it as non-negotiable.",
        "Tell your manager or a colleague you’re at capacity if you can; one sentence can open the door to support.",
    ],
}

# —— Coping plan (1-page structure) ——

def build_coping_plan_text(hardest: str | None, phq2_level: str, gad2_level: str) -> str:
    """Build a 1-page coping plan (triggers, early signs, tools, contacts, when to seek help)."""
    minimal = ("minimal", "unknown")
    need_follow_up = phq2_level not in minimal or gad2_level not in minimal
    lines = [
        "—— Your CalmCompass coping plan ——",
        "",
        "1. Triggers to watch for",
        "   - Too little sleep, skipping meals, or no movement",
        "   - Long stretches without talking to anyone",
        "   - Taking on too much without saying no",
        "",
        "2. Early warning signs",
        "   - Irritability, restlessness, or feeling flat",
        "   - Avoiding people or tasks you usually do",
        "   - More negative thoughts about yourself or the future",
        "",
        "3. Three coping tools to use anytime",
        "   - Breathe: 4 counts in, 7 hold, 8 out (repeat 3–4 times)",
        "   - Move: 5 min walk, stretch, or step outside",
        "   - Connect: one short message or call to someone you trust",
        "",
        "4. Two people to contact when it’s hard",
        "   - Person 1: _______________________",
        "   - Person 2: _______________________",
        "",
        "5. When to seek help",
        "   - Mood or worry gets in the way of work, relationships, or daily life",
        "   - You’ve felt low or anxious most days for 2+ weeks",
        "   - You have thoughts of hurting yourself or others → 988 or 741741",
        "",
        "This tool is not a substitute for professional care.",
    ]
    if hardest and hardest in FOLLOW_UP_TIPS:
        lines.insert(-2, "")
        lines.insert(-2, "6. Extra focus: " + hardest)
        for t in FOLLOW_UP_TIPS[hardest]:
            lines.insert(-2, "   - " + t)
    return "\n".join(lines)

# —— Grounding (30-second script) ——

GROUNDING_SCRIPT = """
Find a comfortable place. You can do this in under a minute.

**5 – See**  
Name 5 things you can see (e.g. a window, your hands, the floor).

**4 – Touch**  
Name 4 things you can feel (e.g. your feet on the ground, the chair, your breath).

**3 – Hear**  
Name 3 things you can hear (e.g. traffic, a fan, your own breathing).

**2 – Smell**  
Name 2 things you can smell (or 2 breaths if nothing stands out).

**1 – One thing you’re okay about right now**  
(e.g. “I’m safe in this room,” “I got through the last hour.”)

You’re here. If you need to, repeat the 5-4-3-2-1 or call 988.
"""

# —— When to seek help (for summary and app) ——

WHEN_TO_SEEK_HELP = """
- Your mood or worry is getting in the way of work, relationships, or daily life  
- You’ve been feeling low or anxious most days for 2+ weeks  
- You have thoughts of hurting yourself or others  
- You want support even if things don’t feel “severe”  

This tool does not replace a doctor or therapist. A professional can help you understand what you’re feeling and suggest next steps.
"""

def load_crisis_resources(region: str = "us") -> dict:
    """Load crisis resources for region from resources/{region}.json."""
    path = os.path.join(os.path.dirname(__file__), "resources", f"{region}.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_crisis_message_immediate(region: str = "us") -> str:
    data = load_crisis_resources(region)
    crisis = data.get("crisis", {})
    immediate = crisis.get("immediate_danger", "If you are in immediate danger, call 911 or your local emergency number.")
    lifeline = crisis.get("lifeline", {})
    text_line = crisis.get("text_line", {})
    note = data.get("support_note", "You don't have to be in crisis to use these lines.")
    lines = [f"**{immediate}**", "", "**You’re not alone. Reach out now.**", ""]
    if lifeline:
        lines.append(f"- **{lifeline.get('name', '988 Suicide & Crisis Lifeline')}** — Call or text **{lifeline.get('phone', '988')}** (24/7)")
    if text_line:
        lines.append(f"- **{text_line.get('name', 'Crisis Text Line')}** — Text **{text_line.get('keyword', 'HOME')}** to **{text_line.get('number', '741741')}** (24/7)")
    lines.extend(["", note])
    return "\n".join(lines)

def get_one_micro_action(
    feeling_today: str | None,
    phq_level: str,
    gad_level: str,
    context: dict | None,
    hardest: str | None,
) -> str:
    """Return ONE micro-action based on state and context (evidence-informed mapping)."""
    elevated = phq_level in ("worth_following_up", "mild", "moderate", "moderately_severe", "severe") or gad_level in ("worth_following_up", "mild", "moderate", "severe")
    ctx = context or {}
    if context and ctx.get("workload_stress") in ("A bit much", "Overwhelming") and ctx.get("feeling_today") in ("Low energy", "Overwhelmed", "Stressed"):
        return INTERVENTION_MAP["burnout"]["action"]
    feeling_map = {
        "Overwhelmed": "overwhelm",
        "Anxious": "anxiety",
        "Low energy": "low_mood",
        "Sad": "low_mood",
        "Stressed": "stress",
        "Not sure": "stress",
    }
    state = feeling_map.get(feeling_today, "stress" if elevated else "low_mood")
    if hardest and hardest in FOLLOW_UP_TIPS:
        tips = FOLLOW_UP_TIPS[hardest]
        return tips[0] if tips else INTERVENTION_MAP.get(state, {}).get("action", MICRO_ACTIONS_MINIMAL[0])
    return INTERVENTION_MAP.get(state, {}).get("action", MICRO_ACTIONS_ELEVATED[0] if elevated else MICRO_ACTIONS_MINIMAL[0])

# Legacy names for compatibility
CRISIS_MESSAGE = CRISIS_MESSAGE_IMMEDIATE
COPING_MINIMAL = MICRO_ACTIONS_MINIMAL
COPING_FOLLOW_UP = MICRO_ACTIONS_ELEVATED
