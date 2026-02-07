"""
Calm Breathing Game — animated circle (inhale/hold/exhale), 60s loop, progress ring.
Support tool, not a test. Ends with "Did that help?" for optional personalization.
"""

import time
import streamlit as st

# Session keys for feedback (set by this game, read by app if needed)
BREATHING_FEEDBACK_KEY = "breathing_feedback"

# CSS for breathing circle and progress (inject once)
BREATHING_CSS = """
<style>
.cc-breathe-wrap { text-align: center; padding: 1.5rem 0; }
.cc-breathe-circle {
    width: 140px; height: 140px; margin: 0 auto 1.5rem;
    border-radius: 50%;
    background: radial-gradient(circle at 30%% 30%%, rgba(255,255,255,0.9), rgba(45,122,99,0.25));
    box-shadow: 0 4px 24px rgba(45,122,99,0.2);
    animation: cc-breathe-cycle 10s ease-in-out infinite;
}
@keyframes cc-breathe-cycle {
    0%%, 100%   { transform: scale(0.85); opacity: 0.85; }
    40%         { transform: scale(1.35); opacity: 1; }
    50%         { transform: scale(1.35); opacity: 1; }
    90%         { transform: scale(0.85); opacity: 0.85; }
}
@media (prefers-reduced-motion: reduce) {
    .cc-breathe-circle { animation: none; transform: scale(1); }
}
.cc-breathe-progress-wrap { margin: 1rem auto; max-width: 280px; }
.cc-breathe-progress-bar { height: 8px; background: rgba(45,122,99,0.15); border-radius: 8px; overflow: hidden; }
.cc-breathe-progress-fill { height: 100%; background: linear-gradient(90deg, #4a9d82, #2d7a63); border-radius: 8px; transition: width 0.3s ease; }
.cc-breathe-time { font-size: 1.75rem; font-weight: 700; color: #1B5E4A; font-variant-numeric: tabular-nums; margin: 0.5rem 0; }
.cc-breathe-hint { font-size: 0.9rem; color: #2D4A42; margin-top: 0.25rem; }
.cc-breathe-done-title { font-size: 1.25rem; font-weight: 600; color: #0F2A22; margin-bottom: 0.5rem; }
.cc-breathe-feedback-btn { margin: 0.35rem; }
</style>
"""


def render_breathing_game(return_step: str = "intro") -> None:
    """
    Full Calm Breathing Game: intro → 60s animated breath → "Did that help?".
    Sets session_state[BREATHING_FEEDBACK_KEY] to "yes" | "a_little" | "not_really" when user answers.
    return_step: where to go when user clicks Back (or after feedback).
    """
    state = st.session_state
    feedback = state.get(BREATHING_FEEDBACK_KEY)

    # Already completed and gave feedback → show thank-you and back
    if feedback:
        st.markdown(BREATHING_CSS, unsafe_allow_html=True)
        st.markdown('<p class="cc-breathe-done-title">Thanks for trying the breathing exercise.</p>', unsafe_allow_html=True)
        labels = {"yes": "Yes, it helped", "a_little": "A little", "not_really": "Not really"}
        st.caption(f"You said: {labels.get(feedback, feedback)}. We’ll use this only to tailor suggestions.")
        if st.button("← Back to home", key="breathing_back_after"):
            _clear_and_go(return_step)
        return

    # Not started: show intro and Start button
    if not state.get("breathing_game_started"):
        st.markdown(BREATHING_CSS, unsafe_allow_html=True)
        st.markdown("### 🫁 Calm Breathing")
        st.markdown(
            "Follow the circle: it **expands** when you inhale and **contracts** when you exhale. "
            "One cycle is about 10 seconds. We’ll run for **60 seconds**."
        )
        if st.button("Start 60-second breath", type="primary", key="breathing_start"):
            state["breathing_game_started"] = True
            st.rerun()
        if st.button("← Back", key="breathing_back_intro"):
            _clear_and_go(return_step)
        return

    # Started: run 60-second loop with animated circle + progress
    st.markdown(BREATHING_CSS, unsafe_allow_html=True)
    placeholder = st.empty()
    total_sec = 60
    for remaining in range(total_sec, -1, -1):
        elapsed = total_sec - remaining
        pct = round((elapsed / total_sec) * 100)
        mins, secs = divmod(remaining, 60)
        placeholder.markdown(
            f'<div class="cc-breathe-wrap">'
            f'<div class="cc-breathe-circle" aria-hidden="true"></div>'
            f'<div class="cc-breathe-time">{mins}:{secs:02d}</div>'
            f'<div class="cc-breathe-progress-wrap">'
            f'<div class="cc-breathe-progress-bar"><div class="cc-breathe-progress-fill" style="width:{pct}%"></div></div>'
            f'</div>'
            f'<p class="cc-breathe-hint">Breathe with the circle — expand = inhale, contract = exhale</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if remaining > 0:
            time.sleep(1)

    # Done: show "Did that help?" and store feedback
    placeholder.empty()
    st.markdown(BREATHING_CSS, unsafe_allow_html=True)
    st.markdown("### You did it.")
    st.markdown("Take a moment to notice how you feel.")
    st.markdown("**Did that help?**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Yes", key="fb_yes"):
            state[BREATHING_FEEDBACK_KEY] = "yes"
            st.rerun()
    with col2:
        if st.button("A little", key="fb_little"):
            state[BREATHING_FEEDBACK_KEY] = "a_little"
            st.rerun()
    with col3:
        if st.button("Not really", key="fb_no"):
            state[BREATHING_FEEDBACK_KEY] = "not_really"
            st.rerun()
    if st.button("← Back to home", key="breathing_back_done"):
        _clear_and_go(return_step)


def _clear_and_go(return_step: str) -> None:
    """Clear breathing game state and navigate back."""
    for key in ("breathing_game_started", BREATHING_FEEDBACK_KEY):
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.step = return_step
    st.session_state["render_nonce"] = (st.session_state.get("render_nonce") or 0) + 1
    st.rerun()
