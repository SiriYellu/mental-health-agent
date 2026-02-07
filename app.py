"""
CalmCompass — Privacy-first mental health check-in.
No data leaves your device. No backend. No storage by default.
Every user gets: 1 understanding, 1 action, 1 reassurance, 1 support option.
Not a substitute for professional care.
"""

from datetime import datetime

import streamlit as st
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

# ML emotion model: load once per session (Streamlit Cloud). Set DISABLE_ML=1 to skip (e.g. memory limits).
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

# ——— CSS: high contrast, clear hierarchy ———
st.markdown("""
<style>
    .hero { font-size: 1.5rem; color: #0F2A22; font-weight: 600; margin-bottom: 0.5rem; }
    .subhero { color: #1B5E4A; margin-bottom: 1rem; }
    .card { background: #E0EDE9; padding: 1rem 1.25rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #1B5E4A; }
    .disclaimer { font-size: 0.9rem; color: #2D4A42; }
    .grounding-box { background: #E8F2EF; padding: 1rem; border-radius: 8px; margin: 1rem 0; color: #0F2A22; }
    .one-action { background: #E0EDE9; padding: 1rem; border-radius: 8px; margin: 1rem 0; font-weight: 500; color: #0F2A22; }
    [data-testid="stRadio"] label { font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ——— Session state ———
def init_state():
    defaults = {
        "step": "intro",
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

# ——— Landing: two buttons only ———
if st.session_state.step == "intro":
    st.markdown('<p class="hero">🌿 CalmCompass</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subhero">A 2-minute check-in. One clear next step. Nothing stored unless you choose.</p>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("**2-Minute Check-In**", type="primary", use_container_width=True):
            st.session_state.step = "phq2"
            st.rerun()
    with col2:
        if st.button("**Support Now (60 seconds)**", type="secondary", use_container_width=True):
            st.session_state.step = "support_now"
            st.rerun()
    st.markdown(
        '<div class="card disclaimer">Not medical advice. For reflection and when to reach out. If you’re in crisis, use Support Now or call 988.</div>',
        unsafe_allow_html=True,
    )
    st.caption("Optional: save this session for export later (stored only in this browser tab).")
    st.session_state.save_session = st.checkbox("Save this session for later export", value=st.session_state.save_session, key="save_session_cb")
    if st.session_state.saved_summary or st.session_state.save_session:
        if st.button("Clear session data"):
            st.session_state.saved_summary = None
            st.session_state.save_session = False
            st.rerun()

# ——— Support Now (60 seconds): no screening ———
elif st.session_state.step == "support_now":
    st.markdown("### Support Now (60 seconds)")
    st.markdown(SUPPORT_NOW_CALMING)
    st.markdown("**60-second breathing** — Time yourself: about 60 seconds.")
    st.markdown(BREATHING_60_SEC)
    st.markdown("**Grounding (30 seconds)**")
    st.markdown(f'<div class="grounding-box">{GROUNDING_SCRIPT}</div>', unsafe_allow_html=True)
    st.markdown("**If things feel too heavy**")
    st.info(get_crisis_message_immediate("us"))
    st.caption("This is not a substitute for professional care.")
    if st.button("← Back to home"):
        st.session_state.step = "intro"
        st.rerun()

# ——— Check-In: PHQ-2 ———
elif st.session_state.step == "phq2":
    st.markdown("### How you’ve been feeling (mood)")
    st.session_state.phq2 = run_question_set(
        PHQ2_QUESTIONS, "phq2", st.session_state.phq2,
        "Last 2 weeks. You can choose “Prefer not to answer.”",
    )
    if st.button("Next →"):
        st.session_state.step = "gad2"
        st.rerun()

# ——— Check-In: GAD-2 ———
elif st.session_state.step == "gad2":
    st.markdown("### How you’ve been feeling (worry)")
    st.session_state.gad2 = run_question_set(
        GAD2_QUESTIONS, "gad2", st.session_state.gad2,
        "Last 2 weeks. You can choose “Prefer not to answer.”",
    )
    if st.button("Next →"):
        st.session_state.step = "self_harm"
        st.rerun()

# ——— Self-harm question (optional; direct) ———
elif st.session_state.step == "self_harm":
    st.markdown("### One more question")
    st.caption("Your answer is private. Used only to show the right resources.")
    st.session_state.self_harm = st.radio(
        SELF_HARM_QUESTION,
        SELF_HARM_CHOICES,
        key="self_harm_radio",
        index=0,
    )
    if st.button("See my results"):
        st.session_state.step = "results"
        st.rerun()

# ——— Results ———
elif st.session_state.step == "results":
    self_harm = st.session_state.self_harm

    # — Crisis-only path: if Yes, show ONLY crisis + grounding + support, then Back. No ML, no scores, no download. —
    if self_harm == "Yes":
        st.markdown("### You’re not alone. Reach out now.")
        st.error(get_crisis_message_immediate("us"))
        st.markdown("**If you’re in immediate danger, call 911 or your local emergency number.**")
        st.markdown("**Grounding (30 seconds)**")
        st.markdown(f'<div class="grounding-box">{GROUNDING_SCRIPT}</div>', unsafe_allow_html=True)
        st.caption("This is not a substitute for professional care.")
        if st.button("← Back to home"):
            st.session_state.step = "intro"
            st.rerun()
    else:
        phq2_answers = st.session_state.phq2[:2]
        gad2_answers = st.session_state.gad2[:2]
        phq2_result = score_phq2(phq2_answers)
        gad2_result = score_gad2(gad2_answers)
        phq2_score, phq2_answered, phq2_total = phq2_result[0], phq2_result[1], phq2_result[2]
        gad2_score, gad2_answered, gad2_total = gad2_result[0], gad2_result[1], gad2_result[2]

        # — Normal path: always 4 outputs —
        suggestion = get_suggestion(phq2_score, gad2_score, st.session_state.get("context"))
        # If user gave one-sentence feeling, try ML emotion and tailor understanding + action (no storage)
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
        st.markdown("### Here’s what might help")
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
        # 1) One understanding line
        st.info(display_understanding)
        # 2) One immediate action
        st.markdown("**Your one next step**")
        st.markdown(f'<div class="one-action">{display_action}</div>', unsafe_allow_html=True)
        # 3) One reassurance
        st.caption(suggestion["reassurance"])
        # 4) One support option
        st.markdown("**If things feel too heavy**")
        st.markdown(suggestion["support"])

        # Optional: 2 next steps
        st.markdown("**Optional next steps**")
        for step in suggestion["next_steps"]:
            st.markdown(f"- {step}")

        # — Download summary (no PII) —
        def _score_line(name: str, score: int | None, answered: int, total: int) -> str:
            if score is None:
                return f"  {name}: not scored"
            if answered < total:
                return f"  {name}: {score} (based on {answered}/{total} answers)"
            return f"  {name}: {score}"
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
        )
        if st.session_state.save_session:
            st.session_state.saved_summary = summary_text

        # — Expander: Optional go deeper ———
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
                st.markdown(f'<div class="one-action">{s2["action"]}</div>', unsafe_allow_html=True)
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

        # — Coping plan + talk draft (optional depth) —
        st.markdown("---")
        st.markdown("**Your coping plan**")
        phq_interp = interpret_phq2(phq2_score)
        gad_interp = interpret_gad2(gad2_score)
        plan = build_coping_plan_text(st.session_state.hardest, phq_interp["level"], gad_interp["level"])
        ai_plan = get_coping_plan_enhanced(st.session_state.hardest, phq_interp["level"], gad_interp["level"])
        st.markdown((ai_plan if ai_plan else plan).replace("\n", "  \n"))
        st.markdown("**Talk to someone** — copy a draft message:")
        st.code(get_talk_draft(), language=None)
        st.markdown("**When to consider reaching out**")
        st.markdown(WHEN_TO_SEEK_HELP)
        if st.button("Show grounding exercise", key="show_ground"):
            st.session_state.show_grounding = True
        if st.session_state.get("show_grounding"):
            st.markdown(f'<div class="grounding-box">{GROUNDING_SCRIPT}</div>', unsafe_allow_html=True)

        if st.button("← Start over"):
            keep = {"save_session", "saved_summary"}
            for key in list(st.session_state.keys()):
                if key not in keep:
                    del st.session_state[key]
            init_state()
            st.session_state.step = "intro"
            st.rerun()
