"""
CalmCompass — Privacy-first mental health check-in.
Premium Streamlit UI: hero, glass cards, stepper, calm meter, guided flow.
One understanding + One action + One reassurance + One support option.
Crisis path: self-harm = Yes → only crisis panel + grounding + exit (no ML, no download).
"""

import html
import re
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
from ui.components import (
    glass_card,
    motion_container,
    stepper,
    stepper_html,
    calm_meter,
    breathing_timer_placeholder,
    grounding_checkboxes,
)

# Feeling chips for Step 1 (map to context later)
FEELING_CHIPS = ["Overwhelmed", "Anxious", "Low", "Stressed", "Numb", "Okay"]
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
    .block-container { position: relative; z-index: 1; max-width: 640px; padding: 2rem 1.5rem 2.5rem; margin: 0 auto; }

    @media (prefers-reduced-motion: reduce) {
        .stApp *, .cc-motion-in, .cc-stepper-progress, .cc-calm-meter-fill, .cc-timer-ring,
        .cc-glass-card, .stButton > button, [data-testid="stRadio"] > label { animation: none !important; transition: none !important; }
        .cc-motion-in { opacity: 1; transform: none !important; }
        .cc-calm-meter-fill { width: calc(var(--cc-meter-pct, 0) * 1%) !important; }
        .cc-stepper-progress { width: calc(var(--cc-stepper-pct, 0) * 1%) !important; }
    }

    /* ----- Liquid gradient background + drifting orbs + noise ----- */
    .stApp {
        background: linear-gradient(160deg, #f0f7f4 0%, #e5f0ec 18%, #dcebe6 35%, #e2eeea 52%, #e8f2ef 70%, #f0f7f4 88%);
        background-size: 220% 220%;
        animation: cc-bg 20s ease-in-out infinite;
    }
    @keyframes cc-bg {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    .stApp::before {
        content: ""; position: fixed; top: -15%; left: -5%; width: 45%; height: 55%;
        background: radial-gradient(ellipse, rgba(27,94,74,0.06) 0%, transparent 65%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: cc-orb1 22s ease-in-out infinite;
    }
    .stApp::after {
        content: ""; position: fixed; bottom: -20%; right: -8%; width: 50%; height: 50%;
        background: radial-gradient(ellipse, rgba(45,74,66,0.05) 0%, transparent 65%);
        border-radius: 50%; pointer-events: none; z-index: 0;
        animation: cc-orb2 18s ease-in-out infinite;
    }
    @keyframes cc-orb1 { 0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.9; } 50% { transform: translate(8%, 5%) scale(1.05); opacity: 1; } }
    @keyframes cc-orb2 { 0%, 100% { transform: translate(0, 0) scale(1); } 50% { transform: translate(-5%, -8%) scale(1.08); } }
    /* Third/fourth orbs via main container pseudo (no extra element): use a wrapper in streamlit we don't have, so two orbs only */

    /* Noise overlay (CSS-only: fine repeating gradient as texture) */
    .block-container::before {
        content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
        opacity: 0.5;
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
    .cc-hero-title { font-size: 1.875rem; font-weight: 700; color: #0F2A22; letter-spacing: -0.035em; }
    .cc-hero-tagline { color: #1B5E4A; font-size: 1.0625rem; margin-bottom: 1.5rem; line-height: 1.45; font-weight: 400; }
    h1, h2, h3 { font-family: inherit; letter-spacing: -0.02em; }
    .block-container > * { margin-bottom: 0.75rem; }

    /* ----- Glass cards: true glassmorphism, elevation hover, 20–24px radius ----- */
    .cc-glass-card {
        background: rgba(255,255,255,0.68);
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
    .cc-step-label { font-size: 0.8125rem; color: #2D4A42; margin-top: 0.5rem; font-weight: 500; letter-spacing: -0.01em; }
    .cc-step.active .cc-step-label { color: #0F2A22; font-weight: 600; }

    /* ----- Result panel sections ----- */
    .cc-card-section { display: flex; gap: 0.875rem; align-items: flex-start; margin: 0.875rem 0; padding: 0.875rem 0; border-bottom: 1px solid rgba(27,94,74,0.06); }
    .cc-card-section:last-child { border-bottom: none; }
    .cc-card-icon { font-size: 1.25rem; opacity: 0.9; }
    .cc-card-section-title { font-weight: 600; color: #0F2A22; font-size: 0.9375rem; margin-bottom: 0.25rem; letter-spacing: -0.01em; }
    .cc-card-section-body { color: #2D4A42; font-size: 0.9375rem; line-height: 1.52; }

    /* ----- Calm meter: fill animates from 0 to value ----- */
    .cc-calm-meter { margin: 1.25rem 0; }
    .cc-calm-meter-label { font-size: 0.9375rem; font-weight: 600; color: #0F2A22; margin-bottom: 0.5rem; letter-spacing: -0.01em; }
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
    .cc-timer-value { font-size: 3rem; font-weight: 700; color: #1B5E4A; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
    .cc-timer-label { font-size: 0.9375rem; color: #2D4A42; margin-top: 0.5rem; }
    .cc-timer-done .cc-timer-value { color: #2d7a63; }

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
    .cc-crisis-panel { background: rgba(220,53,69,0.08); border: 2px solid rgba(220,53,69,0.3); border-radius: 16px; padding: 1.25rem; margin: 1rem 0; color: #0F2A22; }
    .cc-crisis-panel a { color: #b02a37; font-weight: 600; }
    .cc-crisis-line { font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0; }
    .cc-disclaimer { font-size: 0.85rem; color: #5a7a72; margin-top: 1rem; }
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


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
    """Change step and bump render nonce so motion container re-animates."""
    st.session_state.step = step_name
    st.session_state["render_nonce"] = (st.session_state.get("render_nonce") or 0) + 1
    st.rerun()


# ——— Landing: hero + two buttons ———
if st.session_state.step == "intro":
    nonce = st.session_state.get("render_nonce") or 0
    intro_html = (
        '<div class="cc-hero">'
        '<span class="cc-hero-icon" aria-hidden="true">🧭</span>'
        '<span class="cc-hero-title">CalmCompass</span></div>'
        '<p class="cc-hero-tagline">A 2-minute check-in. One clear next step. Nothing stored unless you choose.</p>'
        '<div class="cc-glass-card"><p style="margin:0; color:#2D4A42;">Choose what you need right now.</p></div>'
    )
    motion_container("intro", intro_html, nonce)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("**2-Minute Check-In**", type="primary", use_container_width=True):
            _go_to_step("feeling")
    with col2:
        if st.button("**Support Now (60 seconds)**", type="secondary", use_container_width=True):
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

# ——— Support Now: full-screen feel, 60s timer, grounding, crisis panel ———
elif st.session_state.step == "support_now":
    nonce = st.session_state.get("render_nonce") or 0
    support_html = (
        '<div class="cc-hero"><span class="cc-hero-icon">🫁</span><span class="cc-hero-title">Support Now</span></div>'
        '<p class="cc-hero-tagline">You don\'t have to fix anything in the next few minutes. Try the steps below.</p>'
        f'<div class="cc-glass-card"><p style="margin:0 0 0.5rem 0; font-weight:600; color:#0F2A22;">{html.escape(SUPPORT_NOW_CALMING)}</p></div>'
    )
    motion_container("support_now", support_html, nonce, "cc-support-now")
    st.markdown("**60-second breathing** — Start the timer and follow 4-7-8: breathe in 4, hold 7, out 8.")
    if st.button("Start 60-second breathing", type="primary", key="start_breath"):
        breathing_timer_placeholder(60)
    st.markdown(BREATHING_60_SEC)
    st.markdown("---")
    st.markdown("**Grounding (5-4-3-2-1)** — Check off as you go:")
    glass_card(
        _markdown_to_html_bold(GROUNDING_SCRIPT).replace("  ", " &nbsp; "),
        "",
    )
    grounding_checkboxes()
    st.markdown("---")
    st.markdown("**If things feel too heavy**")
    _crisis_html = _markdown_to_html_bold(get_crisis_message_immediate("us"))
    st.markdown(f'<div class="cc-crisis-panel">{_crisis_html}</div>', unsafe_allow_html=True)
    st.caption("This is not a substitute for professional care.")
    if st.button("← Back to home", key="support_back"):
        _go_to_step("intro")

# ——— Step 1: How are you feeling right now? (chips) ———
elif st.session_state.step == "feeling":
    nonce = st.session_state.get("render_nonce") or 0
    feeling_block = (
        stepper_html(1, 3, ["How you feel", "Mood & worry", "Results"])
        + '<h3>How are you feeling right now?</h3>'
        '<p class="cc-hero-tagline" style="margin-bottom:0.5rem;">Pick the one that fits best. This helps us tailor your next step.</p>'
    )
    motion_container("feeling", feeling_block, nonce)
    chosen = st.radio(
        "Choose one",
        FEELING_CHIPS,
        key="feeling_chip_radio",
        format_func=lambda x: x,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.feeling_chip = chosen
    if chosen:
        ctx = st.session_state.context
        ctx["feeling_today"] = FEELING_TO_CONTEXT.get(chosen, chosen)
        st.session_state.context = ctx
    if st.button("Next →", key="feeling_next"):
        _go_to_step("phq2")

# ——— Step 2: PHQ-2 ———
elif st.session_state.step == "phq2":
    nonce = st.session_state.get("render_nonce") or 0
    phq2_block = (
        stepper_html(1, 3, ["How you feel", "Mood & worry", "Results"])
        + '<h3>How you\'ve been feeling (mood)</h3>'
    )
    motion_container("phq2", phq2_block, nonce)
    st.session_state.phq2 = run_question_set(
        PHQ2_QUESTIONS, "phq2", st.session_state.phq2,
        "Last 2 weeks. You can choose \"Prefer not to answer.\"",
    )
    if st.button("Next →", key="phq2_next"):
        _go_to_step("gad2")

# ——— Step 2 (cont.): GAD-2 ———
elif st.session_state.step == "gad2":
    nonce = st.session_state.get("render_nonce") or 0
    gad2_block = (
        stepper_html(2, 3, ["How you feel", "Mood & worry", "Results"])
        + '<h3>How you\'ve been feeling (worry)</h3>'
    )
    motion_container("gad2", gad2_block, nonce)
    st.session_state.gad2 = run_question_set(
        GAD2_QUESTIONS, "gad2", st.session_state.gad2,
        "Last 2 weeks. You can choose \"Prefer not to answer.\"",
    )
    if st.button("Next →", key="gad2_next"):
        _go_to_step("self_harm")

# ——— Step 3: Safety question ———
elif st.session_state.step == "self_harm":
    nonce = st.session_state.get("render_nonce") or 0
    self_harm_block = (
        stepper_html(3, 3, ["How you feel", "Mood & worry", "Results"])
        + '<h3>One more question</h3>'
        '<p class="cc-hero-tagline" style="margin-bottom:0.5rem;">Your answer is private. Used only to show the right resources.</p>'
    )
    motion_container("self_harm", self_harm_block, nonce)
    st.session_state.self_harm = st.radio(
        SELF_HARM_QUESTION,
        SELF_HARM_CHOICES,
        key="self_harm_radio",
        index=0,
    )
    if st.button("See my results", key="see_results"):
        _go_to_step("results")

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

        # Calm meter (never diagnostic)
        calm_meter(phq2_score, gad2_score)

        # Result Panel: 4 outputs in card layout
        u, a, r, s = html.escape(display_understanding), html.escape(display_action), html.escape(suggestion["reassurance"]), html.escape(suggestion["support"])
        understanding_html = (
            f'<div class="cc-card-section">'
            f'<span class="cc-card-icon">💬</span><div class="cc-card-section-inner">'
            f'<div class="cc-card-section-title">Understanding</div>'
            f'<div class="cc-card-section-body">{u}</div></div></div>'
        )
        action_html = (
            f'<div class="cc-card-section">'
            f'<span class="cc-card-icon">🎯</span><div class="cc-card-section-inner">'
            f'<div class="cc-card-section-title">One action</div>'
            f'<div class="cc-card-section-body">{a}</div></div></div>'
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
        glass_card(understanding_html + action_html + reassurance_html + support_html, "")

        # Start 60-second reset button
        if st.button("Start 60-second reset", type="primary", key="reset_60"):
            breathing_timer_placeholder(60)

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
            "Chosen action: " + display_action,
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
