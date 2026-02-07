"""
CalmCompass — Privacy-first mental health check-in.
Premium Streamlit UI: hero, glass cards, stepper, calm meter, guided flow.
One understanding + One action + One reassurance + One support option.
Crisis path: self-harm = Yes → only crisis panel + grounding + exit (no ML, no download).
"""

import html
import re
import time
from datetime import datetime

import streamlit as st


def _markdown_to_html_bold(text: str) -> str:
    """Convert **bold** to <strong> and newlines to <br> for safe HTML display."""
    if not text:
        return ""
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return s.replace("\n", "<br>")
from dotenv import load_dotenv

load_dotenv()

from screening import (
    PHQ2_QUESTIONS,
    GAD2_QUESTIONS,
    PHQ9_QUESTIONS,
    PHQ9_PREFIX,
    GAD7_QUESTIONS,
    GAD7_PREFIX,
    OPTIONS,
    SELF_HARM_QUESTION,
    SELF_HARM_CHOICES,
    score_phq2,
    score_gad2,
    interpret_phq2,
    interpret_gad2,
)
from context import CONTEXT_QUESTIONS, FEELING_TODAY_OPTIONS
from resources import (
    SUPPORT_NOW_HEADING,
    SUPPORT_NOW_CALMING,
    BREATHING_60_SEC,
    get_crisis_message_immediate,
    get_suggestion,
    GROUNDING_SCRIPT,
    WHEN_TO_SEEK_HELP,
    build_coping_plan_text,
    get_talk_draft,
)
from emotion import detect_emotion, explain_emotion
from plan_generator import get_coping_plan_enhanced
from ml.feedback_schema import (
    build_feedback_row,
    feedback_rows_to_csv,
    FEEDBACK_CSV_COLUMNS,
)
from ml.coping_recommender import load_coping_model as _load_coping_model_raw, recommend_action
from ml.actions import ACTIONS, get_action_by_id, suggest_action_rules

@st.cache_resource
def load_coping_model():
    """Load coping action recommender model once (cached). Returns (pipe, meta) or (None, None)."""
    return _load_coping_model_raw()
from ui.components import (
    glass_card,
    motion_container,
    stepper,
    stepper_html,
    calm_meter,
    breathing_timer_placeholder,
    grounding_checkboxes,
    survey_progress,
    survey_encouragement,
)
from ui.butterfly_bg import butterfly_background
from ui.chat import render_chat_widget
from games.breathing import render_breathing_game
from games.memory_match import render_memory_match
from games.shell_game import render_shell_game

# Inner weather (Step 1): tiles + supportive line + context mapping
WEATHER_TILES = [("☀", "Clear"), ("☁", "Cloudy"), ("🌬", "Windy"), ("🌫", "Foggy"), ("🌧", "Stormy")]
WEATHER_SUPPORTIVE = {
    "Clear": "Clear skies. We'll keep it light.",
    "Cloudy": "Cloudy is okay. One step at a time.",
    "Windy": "Windy days happen. We'll go step by step.",
    "Foggy": "Foggy can feel heavy. We're here.",
    "Stormy": "Stormy days happen. We'll do one step at a time.",
}
WEATHER_TO_CONTEXT = {"Clear": "Okay", "Cloudy": "Not sure", "Windy": "Stressed", "Foggy": "Not sure", "Stormy": "Overwhelmed"}

# Display options with friendly emoji for game-like survey (same order as OPTIONS: 0–4)
OPTIONS_DISPLAY = [
    "Not at all 🌱",
    "Several days 🍃",
    "More than half the days 🍂",
    "Nearly every day 🍁",
    "Prefer not to answer ✋",
]
SURVEY_TOTAL_STEPS = 6  # feel, mood_0, mood_1, worry_0, worry_1, safety
FEELING_TO_CONTEXT = {
    "Overwhelmed": "Overwhelmed",
    "Anxious": "Anxious",
    "Low": "Low energy",
    "Stressed": "Stressed",
    "Numb": "Not sure",
    "Okay": "Not sure",
}

# ML emotion model: load once per session. Set DISABLE_ML=1 to skip (e.g. memory limits).
@st.cache_resource
def load_emotion_model():
    import os
    if os.environ.get("DISABLE_ML") == "1":
        return None
    try:
        from transformers import pipeline
        return pipeline(
            "text-classification",
            model="bhadresh-savani/distilbert-base-uncased-emotion",
            top_k=1,
        )
    except Exception:
        return None


def _predict_emotion_cached(text: str):
    """Returns { understanding, action } or None. Uses cached model; guards label/state; fallback on failure."""
    from ml.inference import predict_emotion, state_from_emotion_label, get_emotion_tailored_response, MIN_CONFIDENCE
    label, conf = predict_emotion(text, pipe_loader=load_emotion_model)
    if not label or conf < MIN_CONFIDENCE:
        return None
    state = state_from_emotion_label(label)
    if state is None:
        return None
    tailored = get_emotion_tailored_response(state)
    if tailored:
        return {"understanding": tailored[0], "action": tailored[1]}
    return None


# ——— Page config ———
st.set_page_config(
    page_title="CalmCompass — 2-minute check-in",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ——— Global CSS: Apple-like liquid gradient, typography, glass cards, motion, prefers-reduced-motion ———
st.markdown("""
<style>
    /* ----- Base: system font stack, grid, reduced motion ----- */
    .stApp, .block-container, [class*="cc-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Inter, sans-serif;
    }
    .block-container { position: relative; z-index: 2; max-width: 640px; padding: 2rem 1.5rem 2.5rem; margin: 0 auto; color: #e2e8f0; }
    /* Butterfly background iframe: full viewport, behind all content (first iframe = our component) */
    .stApp iframe:first-of-type { position: fixed !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; min-height: 100vh !important; z-index: 0 !important; pointer-events: none !important; }
    .stApp p, .stApp label, .stApp .stMarkdown { color: #e2e8f0; }
    .stApp h1, .stApp h2, .stApp h3 { color: #f1f5f9; }

    @media (prefers-reduced-motion: reduce) {
        .stApp *, .cc-motion-in, .cc-stepper-progress, .cc-calm-meter-fill, .cc-timer-ring,
        .cc-glass-card, .cc-survey-progress-fill, .stButton > button, [data-testid="stRadio"] > label { animation: none !important; transition: none !important; }
        .cc-motion-in { opacity: 1; transform: none !important; }
        .cc-calm-meter-fill { width: calc(var(--cc-meter-pct, 0) * 1%) !important; }
        .cc-stepper-progress { width: calc(var(--cc-stepper-pct, 0) * 1%) !important; }
        .cc-survey-progress-fill { width: calc(var(--cc-survey-pct, 0) * 1%) !important; }
    }

    /* ----- Game-like palette: warm + calm (not plain) ----- */
    :root {
        --cc-bg-start: #f8f4f0;
        --cc-bg-mid: #eef5f2;
        --cc-bg-end: #e8f0ed;
        --cc-accent: #2d7a63;
        --cc-accent-soft: #4a9d82;
        --cc-mood: #5b7cba;
        --cc-worry: #c9a227;
        --cc-feel: #6b9080;
        --cc-card-bg: rgba(255,255,255,0.82);
        --cc-card-border: rgba(45,122,99,0.15);
    }

    /* ----- Realtime-style moving background: multiple layers, floating shapes ----- */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 20%, #334155 40%, #1e3a5f 60%, #0f172a 80%);
        background-size: 400% 400%;
        animation: cc-bg-realtime 15s ease infinite;
    }
    @keyframes cc-bg-realtime {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    .stApp::before {
        content: ""; position: fixed; top: -20%; left: -10%; width: 50%; height: 60%;
        background: radial-gradient(ellipse, rgba(56,189,248,0.15) 0%, rgba(14,165,233,0.08) 40%, transparent 70%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: cc-float1 18s ease-in-out infinite;
    }
    .stApp::after {
        content: ""; position: fixed; bottom: -25%; right: -15%; width: 55%; height: 55%;
        background: radial-gradient(ellipse, rgba(34,211,238,0.12) 0%, rgba(6,182,212,0.06) 45%, transparent 70%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: cc-float2 20s ease-in-out infinite;
    }
    @keyframes cc-float1 { 0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); opacity: 0.9; } 33% { transform: translate(12%, 8%) scale(1.1) rotate(5deg); opacity: 1; } 66% { transform: translate(-5%, 12%) scale(0.95) rotate(-3deg); opacity: 0.85; } }
    @keyframes cc-float2 { 0%, 100% { transform: translate(0, 0) scale(1); } 50% { transform: translate(-10%, -12%) scale(1.15); } }
    /* Floating accent orbs (via block-container) */
    .block-container::before {
        content: ""; position: fixed; top: 40%; left: 60%; width: 25%; height: 25%;
        background: radial-gradient(circle, rgba(251,191,36,0.08) 0%, transparent 70%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: cc-float3 12s ease-in-out infinite;
    }
    @keyframes cc-float3 { 0%, 100% { transform: translate(0, 0); opacity: 0.6; } 50% { transform: translate(15%, -15%); opacity: 1; } }
    .block-container > * { position: relative; z-index: 1; }
    /* Light noise overlay */
    .block-container::after {
        content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
    }

    /* ----- Step transition: fade + slide up ----- */
    .cc-motion-screen.cc-motion-in {
        animation: cc-fadeUp 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes cc-fadeUp {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .cc-support-now { background: rgba(255,255,255,0.4); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-radius: 24px; padding: 1.5rem; margin-bottom: 1rem; }

    /* ----- Typography & spacing ----- */
    .cc-hero { display: flex; align-items: center; gap: 0.875rem; margin-bottom: 0.5rem; letter-spacing: -0.03em; }
    .cc-hero-icon { font-size: 2.25rem; line-height: 1; }
    .cc-hero-title { font-size: 1.875rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.035em; }
    .cc-hero-tagline { color: #94a3b8; font-size: 1.0625rem; margin-bottom: 1.5rem; line-height: 1.45; font-weight: 400; }
    h1, h2, h3 { font-family: inherit; letter-spacing: -0.02em; }
    .block-container > * { margin-bottom: 0.75rem; }

    /* ----- Glass cards: true glassmorphism, elevation hover, 20–24px radius ----- */
    .cc-glass-card {
        background: rgba(30,41,59,0.75);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border-radius: 22px; padding: 1.5rem 1.75rem; margin: 1rem 0;
        border: 1px solid rgba(27,94,74,0.08);
        box-shadow: 0 4px 24px rgba(0,0,0,0.04), 0 0 0 1px rgba(255,255,255,0.5) inset;
        transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.3s ease;
    }
    .cc-glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(27,94,74,0.1), 0 0 0 1px rgba(255,255,255,0.6) inset;
    }

    /* ----- Stepper: animated progress fill + current step glow ----- */
    .cc-stepper { display: flex; align-items: center; justify-content: space-between; margin: 1.5rem 0; gap: 0.5rem; position: relative; }
    .cc-stepper-progress {
        position: absolute; left: 0; top: 50%; transform: translateY(-50%); height: 3px;
        background: linear-gradient(90deg, #1B5E4A, #2d7a63); border-radius: 3px;
        width: 0; max-width: calc(100% - 2rem);
        animation: cc-stepperFill 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes cc-stepperFill { to { width: calc(var(--cc-stepper-pct, 0) * 1%); } }
    .cc-step { display: flex; flex-direction: column; align-items: center; flex: 1; position: relative; z-index: 1; }
    .cc-step::before { content: ""; position: absolute; top: 11px; left: -50%; width: 100%; height: 3px; background: rgba(27,94,74,0.12); z-index: 0; border-radius: 2px; }
    .cc-step:first-child::before { display: none; }
    .cc-step.active .cc-step-dot {
        background: #1B5E4A; transform: scale(1.2);
        box-shadow: 0 0 0 4px rgba(27,94,74,0.18), 0 2px 8px rgba(27,94,74,0.2);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .cc-step.done .cc-step-dot { background: #2d7a63; }
    .cc-step-dot { width: 22px; height: 22px; border-radius: 50%; background: rgba(27,94,74,0.15); transition: all 0.25s ease; z-index: 1; }
    .cc-step-label { font-size: 0.8125rem; color: #94a3b8; margin-top: 0.5rem; font-weight: 500; letter-spacing: -0.01em; }
    .cc-step.active .cc-step-label { color: #f1f5f9; font-weight: 600; }

    /* ----- Result panel sections ----- */
    .cc-card-section { display: flex; gap: 0.875rem; align-items: flex-start; margin: 0.875rem 0; padding: 0.875rem 0; border-bottom: 1px solid rgba(27,94,74,0.06); }
    .cc-card-section:last-child { border-bottom: none; }
    .cc-card-icon { font-size: 1.25rem; opacity: 0.9; }
    .cc-card-section-title { font-weight: 600; color: #e2e8f0; font-size: 0.9375rem; margin-bottom: 0.25rem; letter-spacing: -0.01em; }
    .cc-card-section-body { color: #cbd5e1; font-size: 0.9375rem; line-height: 1.52; }

    /* ----- Calm meter: fill animates from 0 to value ----- */
    .cc-calm-meter { margin: 1.25rem 0; }
    .cc-calm-meter-label { font-size: 0.9375rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.5rem; letter-spacing: -0.01em; }
    .cc-calm-meter-track { height: 10px; background: rgba(27,94,74,0.1); border-radius: 10px; overflow: hidden; }
    .cc-calm-meter-fill {
        height: 100%; width: 0; background: linear-gradient(90deg, #2d7a63, #1B5E4A); border-radius: 10px;
        animation: cc-meterFill 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes cc-meterFill { to { width: calc(var(--cc-meter-pct, 0) * 1%); } }

    /* ----- Breathing timer: pulsing ring during countdown ----- */
    .cc-timer-box { position: relative; text-align: center; padding: 2.25rem 2rem; background: rgba(255,255,255,0.75); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border-radius: 22px; border: 1px solid rgba(27,94,74,0.1); margin: 1.25rem 0; box-shadow: 0 4px 24px rgba(0,0,0,0.04); }
    .cc-timer-ring { display: none; position: absolute; inset: -4px; border-radius: 26px; border: 2px solid rgba(27,94,74,0.2); pointer-events: none; }
    .cc-timer-box.cc-timer-pulse .cc-timer-ring { display: block; animation: cc-timerPulse 2.5s ease-in-out infinite; }
    @keyframes cc-timerPulse { 0%, 100% { transform: scale(1); opacity: 0.6; } 50% { transform: scale(1.02); opacity: 0.9; } }
    .cc-timer-value { font-size: 3rem; font-weight: 700; color: #38bdf8; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
    .cc-timer-label { font-size: 0.9375rem; color: #94a3b8; margin-top: 0.5rem; }
    .cc-timer-done .cc-timer-value { color: #22d3ee; }

    /* ----- Buttons: primary pill + gradient highlight; secondary outlined ----- */
    .stButton > button {
        font-family: inherit; font-weight: 600; letter-spacing: -0.01em;
        border-radius: 999px; padding: 0.6rem 1.25rem;
        transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s ease, background 0.2s ease;
    }
    .stButton > button[kind="primary"], .stButton > button:first-of-type {
        background: linear-gradient(180deg, #2d7a63 0%, #1B5E4A 100%) !important;
        box-shadow: 0 2px 12px rgba(27,94,74,0.35), 0 1px 0 rgba(255,255,255,0.15) inset !important;
        color: #fff !important; border: none !important;
    }
    .stButton > button[kind="primary"]:hover, .stButton > button:first-of-type:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(27,94,74,0.4), 0 1px 0 rgba(255,255,255,0.2) inset !important;
    }
    .stButton > button[kind="primary"]:active, .stButton > button:first-of-type:active { transform: translateY(0); }
    .stButton > button[kind="secondary"], .stButton > button:not([kind="primary"]):not(:first-of-type) {
        background: transparent !important; color: #1B5E4A !important; border: 2px solid rgba(27,94,74,0.3) !important;
    }
    .stButton > button[kind="secondary"]:hover, .stButton > button:not([kind="primary"]):not(:first-of-type):hover {
        background: rgba(27,94,74,0.06) !important; transform: translateY(-1px);
    }

    /* Chips / radio hover */
    [data-testid="stRadio"] > label { border-radius: 14px; padding: 0.65rem 1rem; transition: background 0.2s ease; }
    [data-testid="stRadio"] > label:hover { background: rgba(27,94,74,0.06) !important; }
    [data-testid="stRadio"] > label:has(input:checked) { background: rgba(27,94,74,0.1) !important; }

    .cc-divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(27,94,74,0.12), transparent); margin: 1.5rem 0; }

    /* Crisis panel */
    .cc-crisis-panel { background: rgba(220,53,69,0.12); border: 2px solid rgba(220,53,69,0.4); border-radius: 16px; padding: 1.25rem; margin: 1rem 0; color: #f1f5f9; }
    .cc-crisis-panel a { color: #f87171; font-weight: 600; }
    .cc-crisis-line { font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0; }
    .cc-disclaimer { font-size: 0.85rem; color: #94a3b8; margin-top: 1rem; }

    /* ----- Game-like survey: progress bar + step label ----- */
    .cc-survey-progress { margin-bottom: 1.25rem; }
    .cc-survey-progress-bar { height: 8px; background: rgba(45,122,99,0.15); border-radius: 8px; overflow: hidden; margin-bottom: 0.5rem; }
    .cc-survey-progress-fill { height: 100%; width: 0; background: linear-gradient(90deg, var(--cc-accent-soft), var(--cc-accent)); border-radius: 8px; animation: cc-surveyFill 0.5s ease-out forwards; }
    @keyframes cc-surveyFill { to { width: calc(var(--cc-survey-pct, 0) * 1%); } }
    .cc-survey-progress-label { font-size: 0.9rem; font-weight: 600; color: var(--cc-accent); letter-spacing: 0.02em; }
    .cc-survey-progress-sub { font-size: 0.85rem; color: #94a3b8; margin: 0.25rem 0 0 0; }

    /* ----- Big option cards for survey (radio labels as tappable cards) ----- */
    .block-container [data-testid="stRadio"] > label {
        display: block; padding: 1rem 1.25rem; margin: 0.5rem 0; border-radius: 16px;
        background: var(--cc-card-bg); border: 2px solid var(--cc-card-border);
        box-shadow: 0 2px 12px rgba(0,0,0,0.04); font-weight: 500; font-size: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
    }
    .block-container [data-testid="stRadio"] > label:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(45,122,99,0.12);
        border-color: rgba(45,122,99,0.35); background: rgba(255,255,255,0.95);
    }
    .block-container [data-testid="stRadio"] > label:has(input:checked) {
        border-color: var(--cc-accent); background: rgba(45,122,99,0.08);
        box-shadow: 0 4px 16px rgba(45,122,99,0.2);
    }
    .cc-survey-question { font-size: 1.1rem; font-weight: 600; color: #e2e8f0; margin-bottom: 1rem; line-height: 1.4; }
    .cc-survey-cheer { font-size: 0.95rem; color: #cbd5e1; margin-bottom: 1rem; }
    .cc-how-you-moved { border-left: 4px solid var(--cc-accent-soft); }
</style>
""", unsafe_allow_html=True)

# ——— Session state ———
def init_state():
    defaults = {
        "step": "intro",
        "render_nonce": 0,
        "feeling_chip": None,
        "phq2": [], "gad2": [],
        "phq9": [], "gad7": [], "pss4": [],
        "context": {},
        "one_sentence": "",
        "self_harm": None,
        "hardest": None,
        "save_session": False,
        "saved_summary": None,
        # Game / patience / thinking metrics (session only, not stored)
        "total_clicks": 0,
        "step_entered_at": None,
        "step_times": {},
        "game_clicks": [],
        "patience_game_done": False,
        "reset_style": None,
        "support_now_breathing_done": False,
        "need_most": None,
        "result_help": None,
        "inner_weather": None,
        "results_60_done": False,
        "chat_messages": [],
        "feedback_opt_in": False,
        "feedback_rows": [],
        "feedback_recorded_for_action": False,
        "results_suggested_action": None,
        "results_ml_used": False,
        "results_ml_confidence": 0.0,
        "results_action_taken": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()

# Interactive butterfly background (fixed layer behind UI; cursor-attraction)
butterfly_background(n=12, opacity=0.32, speed=1.0)


def run_question_set(questions, key_prefix, answers_list, prefix_text=None):
    if prefix_text:
        st.caption(prefix_text)
    for i, q in enumerate(questions):
        default_idx = answers_list[i] if i < len(answers_list) else 0
        default_idx = min(default_idx, len(OPTIONS) - 1)
        sel = st.radio(
            q, range(len(OPTIONS)), format_func=lambda x: OPTIONS[x],
            key=f"{key_prefix}_{i}", index=default_idx,
        )
        if len(answers_list) <= i:
            answers_list.append(sel)
        else:
            answers_list[i] = sel
    return answers_list[: len(questions)]


def _score_line(name: str, score: int | None, answered: int, total: int) -> str:
    if score is None:
        return f"  {name}: not scored"
    if answered < total:
        return f"  {name}: {score} (based on {answered}/{total} answers)"
    return f"  {name}: {score}"


def _go_to_step(step_name: str) -> None:
    """Change step, record time on previous step, count click, bump nonce, rerun."""
    now = time.time()
    old_step = st.session_state.get("step")
    step_entered = st.session_state.get("step_entered_at")
    if step_entered is not None and old_step:
        if "step_times" not in st.session_state:
            st.session_state.step_times = {}
        st.session_state.step_times[old_step] = round(now - step_entered, 1)
    st.session_state.step_entered_at = now
    st.session_state.step = step_name
    st.session_state["render_nonce"] = (st.session_state.get("render_nonce") or 0) + 1
    st.rerun()


def _render_how_you_moved() -> None:
    """Show a short, non-judgmental reflection on pace and game taps only (session only)."""
    step_times = st.session_state.get("step_times") or {}
    game_clicks = st.session_state.get("game_clicks") or []
    lines = []
    # Only count the 5 pause-game taps, not navigation clicks
    if len(game_clicks) > 0:
        lines.append(f"In the pause game you tapped <strong>{len(game_clicks)}</strong> times.")
    if step_times:
        survey_steps = ("feeling", "mood_0", "mood_1", "worry_0", "worry_1", "safety", "patience_game")
        times_on_survey = [step_times.get(s) for s in survey_steps if step_times.get(s) is not None]
        if times_on_survey:
            avg_sec = sum(times_on_survey) / len(times_on_survey)
            if avg_sec < 5:
                lines.append("You moved through the questions quickly.")
            elif avg_sec > 15:
                lines.append("You took your time on the questions.")
            else:
                lines.append("You moved at a steady pace.")
    if len(game_clicks) >= 2:
        intervals = [game_clicks[i + 1] - game_clicks[i] for i in range(len(game_clicks) - 1)]
        avg_gap = sum(intervals) / len(intervals)
        if avg_gap < 0.5:
            lines.append("You tapped quickly — no wrong answer.")
        elif avg_gap >= 1.0:
            lines.append("You paused between taps.")
    if not lines:
        return
    body = " ".join(lines) + " This is just for reflection, not a diagnosis."
    glass_card(f'<p class="cc-survey-cheer" style="margin:0;"><strong>How you moved</strong><br>{body}</p>', "cc-how-you-moved")


# ——— Landing: hero + two buttons ———
if st.session_state.step == "intro":
    nonce = st.session_state.get("render_nonce") or 0
    intro_html = (
        '<div class="cc-hero">'
        '<span class="cc-hero-icon" aria-hidden="true">🧭</span>'
        '<span class="cc-hero-title">CalmCompass</span></div>'
        '<p class="cc-hero-tagline">A short, gentle check-in — one question at a time. Like a quick game. Nothing stored unless you choose.</p>'
        '<div class="cc-glass-card"><p style="margin:0; color:#e2e8f0;">Choose how you want to start.</p></div>'
    )
    motion_container("intro", intro_html, nonce)
    with st.expander("What you'll get", expanded=False):
        st.markdown("**Understanding** · **Action** · **Reassurance** · **Support**")
        st.caption("One of each, tailored to your answers. Nothing stored unless you choose.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("**Start 2-Minute Check-In**", type="primary", use_container_width=True):
            _go_to_step("inner_weather")
    with col2:
        if st.button("**Support Now (60s Reset)**", type="secondary", use_container_width=True):
            _go_to_step("support_now")
    st.markdown(
        '<div class="cc-glass-card cc-disclaimer">Not medical advice. For reflection and when to reach out. If you\'re in crisis, use Support Now or call 988.</div>',
        unsafe_allow_html=True,
    )
    st.caption("Optional: save this session for export later (stored only in this browser tab).")
    st.session_state.save_session = st.checkbox("Save this session for later export", value=st.session_state.save_session, key="save_session_cb")
    if st.session_state.saved_summary or st.session_state.save_session:
        if st.button("Clear session data"):
            st.session_state.saved_summary = None
            st.session_state.save_session = False
            st.rerun()
    st.markdown("---")
    st.markdown("**🧩 Mental Reset Games**")
    st.caption("Quick focus tools — not tests. Pick one:")
    reset_cols = st.columns(4)
    with reset_cols[0]:
        if st.button("🫁 Breathe", key="reset_breathe"):
            _go_to_step("breathing_game")
    with reset_cols[1]:
        if st.button("🥚 Find the Egg", key="reset_shell"):
            _go_to_step("shell_game")
    with reset_cols[2]:
        if st.button("🧠 Memory Match", key="reset_memory"):
            _go_to_step("memory_game")
    with reset_cols[3]:
        st.button("🌤 More coming", key="reset_more_btn", disabled=True)
    st.caption("_More games coming: Focus Grid, Spot the Change, Tic-Tac-Toe._")

# ——— Calm Breathing Game (animated circle, 60s, “Did that help?”) ———
elif st.session_state.step == "breathing_game":
    render_breathing_game(return_step="intro")

# ——— Memory Match (thinking / memory game) ———
elif st.session_state.step == "memory_game":
    render_memory_match(return_step="intro")

# ——— Shell Game (Find the Egg — 3 cups, mix, guess) ———
elif st.session_state.step == "shell_game":
    render_shell_game(return_step="intro")

# ——— Support Now: interactive flow (chips → plan → breathing → grounding → done) ———
elif st.session_state.step == "support_now":
    nonce = st.session_state.get("render_nonce") or 0
    motion_container(
        "support_now",
        '<div class="cc-hero"><span class="cc-hero-icon">🫁</span><span class="cc-hero-title">Support Now</span></div>'
        '<p class="cc-hero-tagline">Choose your reset style. You\'ll get a tailored 60-second plan.</p>',
        nonce, "cc-support-now",
    )
    st.markdown("**I need…**")
    reset_cols = st.columns(4)
    for i, choice in enumerate(RESET_STYLE_CHOICES):
        with reset_cols[i]:
            if st.button(choice, key=f"reset_style_{i}", use_container_width=True):
                st.session_state.reset_style = choice
                _go_to_step("support_now_plan")
    st.markdown("---")
    _crisis_html = _markdown_to_html_bold(get_crisis_message_immediate("us"))
    st.markdown(f'<div class="cc-crisis-panel">{_crisis_html}</div>', unsafe_allow_html=True)
    if st.button("← Back to home", key="support_back"):
        _go_to_step("intro")

elif st.session_state.step == "support_now_plan":
    style = st.session_state.get("reset_style") or "Calm"
    script = RESET_STYLE_SCRIPTS.get(style, RESET_STYLE_SCRIPTS["Calm"])
    st.markdown("### 60 seconds. Follow along.")
    glass_card(f'<p style="margin:0; color:#e2e8f0;">{html.escape(script)}</p>', "")
    st.caption("Breathe in 4 · Hold 7 · Breathe out 8. Repeat 3–4 times.")
    if st.button("Start 60-second reset", type="primary", key="support_start_breath"):
        _go_to_step("support_now_breathing")
    if st.button("← Back", key="support_plan_back"):
        _go_to_step("support_now")

elif st.session_state.step == "support_now_breathing":
    st.markdown("### Live breathing")
    breathing_timer_placeholder(60)
    st.success("Great job.")
    if st.button("Continue to grounding", type="primary", key="support_to_grounding"):
        _go_to_step("support_now_grounding")
    if st.button("← Back to home", key="support_breath_back"):
        _go_to_step("intro")

elif st.session_state.step == "support_now_grounding":
    st.markdown("### Grounding (5-4-3-2-1)")
    st.caption("Check off as you go. Brings you into the present.")
    glass_card(
        _markdown_to_html_bold(GROUNDING_SCRIPT).replace("  ", " &nbsp; "),
        "",
    )
    checks = grounding_checkboxes()
    done_count = sum(1 for v in checks.values() if v)
    pct = round((done_count / 5) * 100) if checks else 0
    st.markdown(
        f'<div class="cc-survey-progress" style="--cc-survey-pct:{pct};">'
        '<div class="cc-survey-progress-bar"><div class="cc-survey-progress-fill"></div></div>'
        f'<div class="cc-survey-progress-label">{done_count} of 5 steps</div></div>',
        unsafe_allow_html=True,
    )
    if done_count == 5:
        st.success("You completed a reset ✅")
    st.markdown("---")
    st.markdown("**Support options (always here)**")
    _crisis_html = _markdown_to_html_bold(get_crisis_message_immediate("us"))
    st.markdown(f'<div class="cc-crisis-panel">{_crisis_html}</div>', unsafe_allow_html=True)
    if st.button("← Back to home", key="support_grounding_back"):
        _go_to_step("intro")

# ——— Game-like survey: inner weather (Step 1) then one question per screen (Steps 2–6) ———
elif st.session_state.step == "inner_weather":
    nonce = st.session_state.get("render_nonce") or 0
    survey_progress(1, SURVEY_TOTAL_STEPS, "Pick your inner weather")
    motion_container("inner_weather", '<p class="cc-survey-cheer">Pick what fits. No wrong answers.</p>', nonce)
    chosen_weather = st.session_state.get("inner_weather")
    cols = st.columns(5)
    for i, (emoji, label) in enumerate(WEATHER_TILES):
        with cols[i]:
            if st.button(f"{emoji} {label}", key=f"weather_{i}", use_container_width=True):
                st.session_state.inner_weather = label
                ctx = st.session_state.context
                ctx["feeling_today"] = WEATHER_TO_CONTEXT.get(label, "Not sure")
                st.session_state.context = ctx
                _go_to_step("mood_0")
    if chosen_weather:
        supportive = WEATHER_SUPPORTIVE.get(chosen_weather, "We'll do one step at a time.")
        st.info(supportive)
    col_b, col_n = st.columns([1, 2])
    with col_b:
        if st.button("← Back", key="weather_back"):
            _go_to_step("intro")
    with col_n:
        if st.button("Next →", key="weather_next"):
            if not st.session_state.get("inner_weather"):
                st.session_state.inner_weather = "Clear"
                ctx = st.session_state.context
                ctx["feeling_today"] = WEATHER_TO_CONTEXT.get("Clear", "Okay")
                st.session_state.context = ctx
            _go_to_step("mood_0")

elif st.session_state.step == "mood_0":
    survey_progress(2, SURVEY_TOTAL_STEPS, "About your mood (last 2 weeks)")
    left = SURVEY_TOTAL_STEPS - 2
    st.markdown(f'<p class="cc-survey-cheer">Thanks. {left} questions left.</p>', unsafe_allow_html=True)
    phq2 = st.session_state.phq2
    default = phq2[0] if len(phq2) >= 1 else 0
    default = min(default, len(OPTIONS) - 1)
    sel = st.radio(
        PHQ2_QUESTIONS[0],
        range(len(OPTIONS)),
        format_func=lambda i: OPTIONS_DISPLAY[i],
        key="mood_0_radio",
        index=default,
        label_visibility="collapsed",
    )
    st.session_state.phq2 = [sel] + (phq2[1:] if len(phq2) > 1 else [0])
    col_b, col_n = st.columns([1, 2])
    with col_b:
        if st.button("← Back", key="mood0_back"):
            _go_to_step("inner_weather")
    with col_n:
        if st.button("Next →", key="mood_0_next"):
            _go_to_step("mood_1")

elif st.session_state.step == "mood_1":
    survey_progress(3, SURVEY_TOTAL_STEPS, "One more about mood")
    st.markdown(f'<p class="cc-survey-cheer">{survey_encouragement(3, SURVEY_TOTAL_STEPS)}</p>', unsafe_allow_html=True)
    phq2 = st.session_state.phq2
    default = phq2[1] if len(phq2) > 1 else 0
    default = min(default, len(OPTIONS) - 1)
    sel = st.radio(
        PHQ2_QUESTIONS[1],
        range(len(OPTIONS)),
        format_func=lambda i: OPTIONS_DISPLAY[i],
        key="mood_1_radio",
        index=default,
        label_visibility="collapsed",
    )
    st.session_state.phq2 = (phq2[:1] if len(phq2) >= 1 else [0]) + [sel]
    col_b, col_n = st.columns([1, 2])
    with col_b:
        if st.button("← Back", key="mood1_back"):
            _go_to_step("mood_0")
    with col_n:
        if st.button("Next →", key="mood_1_next"):
            _go_to_step("worry_0")

elif st.session_state.step == "worry_0":
    survey_progress(4, SURVEY_TOTAL_STEPS, "About worry (last 2 weeks)")
    st.markdown(f'<p class="cc-survey-cheer">Thanks. {SURVEY_TOTAL_STEPS - 4} questions left.</p>', unsafe_allow_html=True)
    gad2 = st.session_state.gad2
    default = gad2[0] if len(gad2) >= 1 else 0
    default = min(default, len(OPTIONS) - 1)
    sel = st.radio(
        GAD2_QUESTIONS[0],
        range(len(OPTIONS)),
        format_func=lambda i: OPTIONS_DISPLAY[i],
        key="worry_0_radio",
        index=default,
        label_visibility="collapsed",
    )
    st.session_state.gad2 = [sel] + (gad2[1:] if len(gad2) > 1 else [0])
    col_b, col_n = st.columns([1, 2])
    with col_b:
        if st.button("← Back", key="worry0_back"):
            _go_to_step("mood_1")
    with col_n:
        if st.button("Next →", key="worry_0_next"):
            _go_to_step("worry_1")

elif st.session_state.step == "worry_1":
    survey_progress(5, SURVEY_TOTAL_STEPS, "One more about worry")
    st.markdown(f'<p class="cc-survey-cheer">Thanks. Almost there — 1 question left.</p>', unsafe_allow_html=True)
    gad2 = st.session_state.gad2
    default = gad2[1] if len(gad2) > 1 else 0
    default = min(default, len(OPTIONS) - 1)
    sel = st.radio(
        GAD2_QUESTIONS[1],
        range(len(OPTIONS)),
        format_func=lambda i: OPTIONS_DISPLAY[i],
        key="worry_1_radio",
        index=default,
        label_visibility="collapsed",
    )
    st.session_state.gad2 = (gad2[:1] if len(gad2) >= 1 else [0]) + [sel]
    col_b, col_n = st.columns([1, 2])
    with col_b:
        if st.button("← Back", key="worry1_back"):
            _go_to_step("worry_0")
    with col_n:
        if st.button("Next →", key="worry_1_next"):
            _go_to_step("safety")

elif st.session_state.step == "safety":
    survey_progress(6, SURVEY_TOTAL_STEPS, "Last step — your answer is private")
    st.markdown('<p class="cc-survey-cheer">Last step. Your answer stays private.</p>', unsafe_allow_html=True)
    st.session_state.self_harm = st.radio(
        SELF_HARM_QUESTION,
        SELF_HARM_CHOICES,
        key="self_harm_radio",
        index=0,
    )
    col_b, col_n = st.columns([1, 2])
    with col_b:
        if st.button("← Back", key="safety_back"):
            _go_to_step("worry_1")
    with col_n:
        if st.button("See my results", key="see_results"):
            if st.session_state.self_harm == "Yes":
                _go_to_step("results")
            else:
                _go_to_step("patience_game")

# ——— Patience game: 5 taps with pauses (tests pace / impulsivity; optional) ———
elif st.session_state.step == "patience_game":
    game_clicks = st.session_state.get("game_clicks") or []
    needed = 5
    st.markdown("### A quick pause game")
    st.markdown(
        "Tap the button below **5 times**, with a short pause between each tap. "
        "There's no right or wrong — we're just noticing how you like to move. You can skip if you prefer."
    )
    if len(game_clicks) < needed:
        st.caption(f"Tap {len(game_clicks) + 1} of {needed}")
        if st.button("Tap", type="primary", key="game_tap"):
            if "game_clicks" not in st.session_state:
                st.session_state.game_clicks = []
            st.session_state.game_clicks.append(time.time())
            st.rerun()
    else:
        # Compute average time between taps (seconds)
        clicks = st.session_state.game_clicks
        if len(clicks) >= 2:
            intervals = [clicks[i + 1] - clicks[i] for i in range(len(clicks) - 1)]
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval < 0.5:
                reflection = "You tapped quickly. Sometimes slowing down just a little between actions can help."
            elif avg_interval >= 1.2:
                reflection = "You took your time between taps. That kind of pacing is a strength."
            else:
                reflection = "You kept a steady pace. Nice."
        else:
            reflection = "You finished the taps. Ready for your results."
        st.session_state.patience_game_done = True
        glass_card(f'<p style="margin:0; color:#e2e8f0;">{reflection}</p>', "")
        if st.button("Continue to my results", type="primary", key="game_continue"):
            _go_to_step("results")
    st.markdown("---")
    if st.button("Skip and go to results", key="game_skip"):
        _go_to_step("results")  # no tap count added

# ——— Results ———
elif st.session_state.step == "results":
    self_harm = st.session_state.self_harm

    # — Crisis-only path: only crisis panel + grounding + Back. No ML, no scores, no download. —
    if self_harm == "Yes":
        nonce = st.session_state.get("render_nonce") or 0
        motion_container("results_crisis", '<h3>You\'re not alone. Reach out now.</h3>', nonce)
        st.markdown(
            f'<div class="cc-crisis-panel">{_markdown_to_html_bold(get_crisis_message_immediate("us"))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**If you're in immediate danger, call 911 or your local emergency number.**")
        st.markdown("**Grounding (30 seconds)**")
        glass_card(_markdown_to_html_bold(GROUNDING_SCRIPT), "")
        st.caption("This is not a substitute for professional care.")
        if st.button("← Back to home", key="crisis_back"):
            _go_to_step("intro")
    else:
        phq2_answers = st.session_state.phq2[:2]
        gad2_answers = st.session_state.gad2[:2]
        phq2_result = score_phq2(phq2_answers)
        gad2_result = score_gad2(gad2_answers)
        phq2_score, phq2_answered, phq2_total = phq2_result[0], phq2_result[1], phq2_result[2]
        gad2_score, gad2_answered, gad2_total = gad2_result[0], gad2_result[1], gad2_result[2]

        suggestion = get_suggestion(phq2_score, gad2_score, st.session_state.get("context"))
        display_understanding = suggestion["understanding"]
        display_action = suggestion["action"]
        one_sentence = (st.session_state.get("one_sentence") or "").strip()
        ml_used = False
        if one_sentence:
            try:
                with st.spinner("Preparing your suggestion…"):
                    ml_tailored = _predict_emotion_cached(one_sentence)
                if ml_tailored:
                    display_understanding = ml_tailored["understanding"]
                    display_action = ml_tailored["action"]
                    ml_used = True
            except Exception:
                pass

        # Results screen motion (fade + slide up)
        nonce = st.session_state.get("render_nonce") or 0
        motion_container("results", '<h3>Here\'s what might help</h3>', nonce)
        # How you moved: clicks, time per step, patience game (gentle reflection only)
        _render_how_you_moved()
        if suggestion.get("partial_note"):
            st.caption(suggestion["partial_note"])
        if ml_used:
            st.caption("**Tailored from your sentence (not saved)**")
        elif one_sentence:
            st.caption("ML tailoring unavailable right now; using general suggestions.")
        else:
            st.caption("**Using general suggestions**")
        if phq2_answered < phq2_total or gad2_answered < gad2_total:
            parts = []
            if phq2_answered < phq2_total:
                parts.append(f"Mood: based on {phq2_answered}/{phq2_total} answers")
            if gad2_answered < gad2_total:
                parts.append(f"Worry: based on {gad2_answered}/{gad2_total} answers")
            st.caption(" · ".join(parts))

        # R1) Calm meter (visual feedback — "How much you've been carrying")
        calm_meter(phq2_score, gad2_score)

        # Result Panel: Understanding, Reassurance, Support (no single "One action" — we show 6 actions below)
        u, r, s = html.escape(display_understanding), html.escape(suggestion["reassurance"]), html.escape(suggestion["support"])
        understanding_html = (
            f'<div class="cc-card-section">'
            f'<span class="cc-card-icon">💬</span><div class="cc-card-section-inner">'
            f'<div class="cc-card-section-title">Understanding</div>'
            f'<div class="cc-card-section-body">{u}</div></div></div>'
        )
        reassurance_html = (
            f'<div class="cc-card-section">'
            f'<span class="cc-card-icon">🌿</span><div class="cc-card-section-inner">'
            f'<div class="cc-card-section-title">Reassurance</div>'
            f'<div class="cc-card-section-body">{r}</div></div></div>'
        )
        support_html = (
            f'<div class="cc-card-section">'
            f'<span class="cc-card-icon">🆘</span><div class="cc-card-section-inner">'
            f'<div class="cc-card-section-title">Support</div>'
            f'<div class="cc-card-section-body">{s}</div></div></div>'
        )
        glass_card(understanding_html + reassurance_html + support_html, "")

        # Suggested action (ML or rules) — compute once per results view
        if st.session_state.get("results_suggested_action") is None:
            pipe, meta = load_coping_model()
            ctx = st.session_state.get("context") or {}
            suggested_id, conf = recommend_action(
                phq2_score, gad2_score,
                ctx.get("feeling_today"),
                ctx.get("workload_stress"),
                need_most=None,
                text_emotion_label=st.session_state.get("text_emotion_label"),
                pipe=pipe,
                meta=meta,
            )
            st.session_state.results_suggested_action = suggested_id
            st.session_state.results_ml_used = conf >= 0.35
            st.session_state.results_ml_confidence = conf

        suggested_id = st.session_state.results_suggested_action
        suggested_info = get_action_by_id(suggested_id) or ACTIONS[0]
        st.markdown(f"**Try an action — suggested for you: {suggested_info['emoji']} {suggested_info['label']}**")
        if st.session_state.get("results_ml_used"):
            st.caption("Personalization model active.")
        st.markdown("Pick any and click **Start now**. Then tell us if it helped.")

        # In-flow: user clicked "Start now" on an action — show that action then "Did this help?"
        action_taken = st.session_state.get("results_action_taken")
        if action_taken:
            act = get_action_by_id(action_taken)
            if act:
                st.markdown(f"**You chose: {act['emoji']} {act['label']}**")
                if action_taken == "breathing_60s":
                    breathing_timer_placeholder(60)
                elif action_taken == "grounding_54321":
                    glass_card(_markdown_to_html_bold(GROUNDING_SCRIPT).replace("  ", " &nbsp; "), "")
                    grounding_checkboxes()
                elif action_taken == "reframe_prompt":
                    st.markdown("What's one small step that would help right now? (Write or say it.)")
                    st.text_input("Optional: type it here", key="reframe_input", label_visibility="collapsed")
                elif action_taken == "tiny_task":
                    st.markdown("Pick one small thing (e.g. clear the desk, fill water) and do it for 2 minutes.")
                    breathing_timer_placeholder(120)  # 2 min
                elif action_taken == "short_walk":
                    st.markdown("Step outside or walk around the room for 2 minutes.")
                    breathing_timer_placeholder(120)
                elif action_taken == "reach_out":
                    st.caption("Copy this message to send to someone you trust:")
                    st.code(get_talk_draft(), language=None)

                st.success("Done ✅")
                st.markdown("**Did this help?**")
                help_choice = st.radio("", ["Yes", "A little", "Not really"], key="result_help_radio", label_visibility="collapsed", horizontal=True)
                if help_choice:
                    st.session_state.result_help = "yes" if help_choice == "Yes" else ("a_little" if help_choice == "A little" else "not_really")
                    if st.session_state.get("feedback_opt_in"):
                        _ctx = st.session_state.get("context") or {}
                        row = build_feedback_row(
                            phq2_score=phq2_score,
                            gad2_score=gad2_score,
                            feeling_today=_ctx.get("feeling_today"),
                            workload_stress=_ctx.get("workload_stress"),
                            need_most=None,
                            text_emotion_label=st.session_state.get("text_emotion_label"),
                            action_suggested=st.session_state.results_suggested_action or "",
                            action_taken=action_taken,
                            result_help=st.session_state.result_help,
                            ml_used=st.session_state.get("results_ml_used", False),
                            confidence=st.session_state.get("results_ml_confidence", 0.0),
                        )
                        if "feedback_rows" not in st.session_state:
                            st.session_state.feedback_rows = []
                        st.session_state.feedback_rows.append(row)
                    st.session_state.results_action_taken = None  # back to action list
                    st.rerun()
                if st.session_state.get("result_help"):
                    msg = DID_THIS_HELP_SUGGESTIONS.get(st.session_state.result_help, "")
                    if msg:
                        st.caption(msg)
            st.session_state.feedback_opt_in = st.checkbox(
                "Help improve suggestions (anonymous)",
                value=st.session_state.get("feedback_opt_in", False),
                key="feedback_opt_in_cb",
            )
            if st.button("← Back to actions", key="back_to_actions"):
                st.session_state.results_action_taken = None
                st.rerun()
        else:
            # 6 action cards with "Start now"
            for i, act in enumerate(ACTIONS):
                with st.container():
                    col_l, col_r = st.columns([3, 1])
                    with col_l:
                        st.markdown(f"**{act['emoji']} {act['label']}** — {act['short']}")
                    with col_r:
                        if st.button("Start now", key=f"action_{act['id']}", type="primary" if act["id"] == suggested_id else "secondary"):
                            st.session_state.results_action_taken = act["id"]
                            st.rerun()
            st.session_state.feedback_opt_in = st.checkbox(
                "Help improve suggestions (anonymous)",
                value=st.session_state.get("feedback_opt_in", False),
                key="feedback_opt_in_cb",
            )

        # Optional next steps
        st.markdown("**Optional next steps**")
        for step in suggestion["next_steps"]:
            st.markdown(f"- {step}")

        # Download summary
        summary_lines = [
            "CalmCompass — Check-in summary",
            "Date/time: " + datetime.now().strftime("%Y-%m-%d %H:%M"),
            "",
            "Answers (last 2 weeks):",
            _score_line("Mood (PHQ-2)", phq2_score, phq2_answered, phq2_total),
            _score_line("Worry (GAD-2)", gad2_score, gad2_answered, gad2_total),
            "",
            "Suggested action: " + (st.session_state.get("results_suggested_action") or "—"),
            "",
            "Next steps:",
        ]
        for s in suggestion["next_steps"]:
            summary_lines.append("  - " + s)
        summary_lines.extend(["", "Support: 988 (call or text), Crisis Text Line (text HOME to 741741).", "", WHEN_TO_SEEK_HELP])
        summary_text = "\n".join(summary_lines)
        st.download_button(
            "Download my summary (text)",
            data=summary_text,
            file_name=f"calmcompass-{datetime.now().strftime('%Y%m%d-%H%M')}.txt",
            mime="text/plain",
            key="dl_summary",
        )
        # Export feedback for training (anonymous; only if any rows collected)
        feedback_rows = st.session_state.get("feedback_rows") or []
        if feedback_rows:
            with st.expander("Export my feedback (for training)"):
                st.caption("Download a CSV of your anonymous \"Did this help?\" responses. Use it to train a better coping recommender (see scripts/).")
                st.download_button(
                    "Download feedback as CSV",
                    data=feedback_rows_to_csv(feedback_rows),
                    file_name=f"calmcompass-feedback-{datetime.now().strftime('%Y%m%d-%H%M')}.csv",
                    mime="text/csv",
                    key="dl_feedback",
                )
        if st.session_state.save_session:
            st.session_state.saved_summary = summary_text

        # Expander: Go deeper
        with st.expander("Optional: go deeper (more tailored suggestions)"):
            st.caption("Add context for refined suggestions. Nothing is stored.")
            do_phq9 = st.checkbox("Answer full mood questionnaire (PHQ-9)", key="go_phq9")
            do_gad7 = st.checkbox("Answer full anxiety questionnaire (GAD-7)", key="go_gad7")
            if do_phq9:
                st.caption(PHQ9_PREFIX)
                st.session_state.phq9 = run_question_set(PHQ9_QUESTIONS, "deep_phq9", st.session_state.phq9)
            if do_gad7:
                st.caption(GAD7_PREFIX)
                st.session_state.gad7 = run_question_set(GAD7_QUESTIONS, "deep_gad7", st.session_state.gad7)
            feel = st.selectbox("How are you feeling today? (optional)", [""] + list(FEELING_TODAY_OPTIONS), key="deep_feeling")
            if feel:
                st.session_state.context["feeling_today"] = feel
            st.markdown("**Quick context (optional)**")
            ctx = st.session_state.context
            for qid, spec in CONTEXT_QUESTIONS.items():
                opts = spec["options"]
                idx = opts.index(ctx[qid]) if ctx.get(qid) in opts else 0
                choice = st.selectbox(spec["label"], opts, key=f"deep_ctx_{qid}", index=idx)
                st.session_state.context[qid] = choice
            st.caption("Text is processed only to generate this response; nothing is stored.")
            one = st.text_input("In one sentence, how are you feeling? (optional)", key="deep_one_sentence", value=st.session_state.get("one_sentence") or "")
            st.session_state.one_sentence = (one or "").strip()
            if st.button("Update suggestions", key="update_suggest"):
                suggestion2 = get_suggestion(phq2_score, gad2_score, st.session_state.context)
                st.session_state.deep_suggestion = suggestion2
                st.rerun()
            if st.session_state.get("deep_suggestion"):
                s2 = st.session_state.deep_suggestion
                st.markdown("**Updated suggestion**")
                st.markdown(f'<div class="cc-glass-card"><p style="margin:0;">{s2["action"]}</p></div>', unsafe_allow_html=True)
                for ns in s2["next_steps"]:
                    st.markdown(f"- {ns}")
            if st.session_state.one_sentence:
                try:
                    ml_t = _predict_emotion_cached(st.session_state.one_sentence)
                    if ml_t:
                        st.caption("Your words were used to tailor the suggestion above. Nothing was saved.")
                    else:
                        emotion, _ = detect_emotion(st.session_state.one_sentence)
                        st.caption(explain_emotion(emotion))
                except Exception:
                    emotion, _ = detect_emotion(st.session_state.one_sentence)
                    st.caption(explain_emotion(emotion))

        # Copy talk-to-someone draft
        with st.expander("Copy talk-to-someone message"):
            st.caption("Draft you can send to a friend or family member.")
            st.code(get_talk_draft(), language=None)

        # Coping plan + when to seek help
        st.markdown("---")
        st.markdown("**Your coping plan**")
        phq_interp = interpret_phq2(phq2_score)
        gad_interp = interpret_gad2(gad2_score)
        plan = build_coping_plan_text(st.session_state.hardest, phq_interp["level"], gad_interp["level"])
        ai_plan = get_coping_plan_enhanced(st.session_state.hardest, phq_interp["level"], gad_interp["level"])
        st.markdown((ai_plan if ai_plan else plan).replace("\n", "  \n"))
        st.markdown("**When to consider reaching out**")
        st.markdown(WHEN_TO_SEEK_HELP)
        if st.button("Show grounding exercise", key="show_ground"):
            st.session_state.show_grounding = True
        if st.session_state.get("show_grounding"):
            glass_card(_markdown_to_html_bold(GROUNDING_SCRIPT), "")

        if st.button("← Start over", key="start_over"):
            keep = {"save_session", "saved_summary"}
            for key in list(st.session_state.keys()):
                if key not in keep:
                    del st.session_state[key]
            init_state()
            _go_to_step("intro")

# ——— Chat widget (bottom of page, every screen) ———
st.markdown("---")
render_chat_widget()
