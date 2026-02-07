"""
Shell Game — 3 cups, egg hidden under one. Mix (true shuffle), then guess.
Attention/focus mini-game. Calming messages, no scores.
"""

import random
import time
import streamlit as st

PREFIX = "shell_"
EGG_AT = PREFIX + "egg_at"      # 0, 1, 2
MIXED = PREFIX + "mixed"
REVEAL = PREFIX + "reveal"
MESSAGE = PREFIX + "message"
NUM_SWAPS = 6


def _true_shuffle(egg_at: int) -> int:
    """Apply NUM_SWAPS random position swaps; return new egg position (0, 1, or 2)."""
    for _ in range(NUM_SWAPS):
        i, j = random.sample([0, 1, 2], 2)
        if egg_at == i:
            egg_at = j
        elif egg_at == j:
            egg_at = i
    return egg_at


def _clear_state():
    for key in (EGG_AT, MIXED, REVEAL, MESSAGE):
        if key in st.session_state:
            del st.session_state[key]


def render_shell_game(return_step: str = "intro") -> None:
    """
    Shell Game: 3 cups, egg under one. Mix (with "Mixing…") then guess.
    True shuffle: egg position is tracked through swaps.
    return_step: where to go when user clicks Back to home.
    """
    state = st.session_state

    # Initialize
    if EGG_AT not in state:
        state[EGG_AT] = random.randint(0, 2)
        state[MIXED] = False
        state[REVEAL] = False
        state[MESSAGE] = ""

    egg_at = state[EGG_AT]
    mixed = state[MIXED]
    reveal = state[REVEAL]
    message = state.get(MESSAGE) or ""

    st.markdown("### 🥚 Find the Egg")
    st.caption("Try to track the egg while the cups are mixed. Nice little focus reset.")

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        if st.button("🔁 New round", key="shell_new_round"):
            state[EGG_AT] = random.randint(0, 2)
            state[MIXED] = False
            state[REVEAL] = False
            state[MESSAGE] = ""
            st.rerun()

    # Mix step
    if not mixed:
        if st.button("🌀 Mix cups", type="primary", key="shell_mix"):
            with st.spinner("Mixing…"):
                time.sleep(1.0)
            state[EGG_AT] = _true_shuffle(state[EGG_AT])
            state[MIXED] = True
            state[REVEAL] = False
            state[MESSAGE] = "Cups mixed! Now pick a cup."
            st.rerun()
        st.caption("Click **Mix cups** first, then guess which cup has the egg.")
        st.markdown("---")
        if st.button("← Back to home", key="shell_back_intro"):
            _clear_state()
            state["step"] = return_step
            state["render_nonce"] = (state.get("render_nonce") or 0) + 1
            st.rerun()
        return

    if message:
        st.info(message)

    # Cup buttons (positions 0, 1, 2 → Cup 1, 2, 3)
    c1, c2, c3 = st.columns(3)
    disabled = reveal

    def guess(cup_num: int):
        idx = cup_num - 1  # 1→0, 2→1, 3→2
        state[REVEAL] = True
        if idx == state[EGG_AT]:
            state[MESSAGE] = "✅ You found it! Nice focus."
        else:
            state[MESSAGE] = f"Not there — the egg was under Cup {state[EGG_AT] + 1}. Try another round?"
        st.rerun()

    with c1:
        if st.button("Cup 1", key="shell_cup1", disabled=disabled):
            guess(1)
    with c2:
        if st.button("Cup 2", key="shell_cup2", disabled=disabled):
            guess(2)
    with c3:
        if st.button("Cup 3", key="shell_cup3", disabled=disabled):
            guess(3)

    if reveal:
        st.success(state[MESSAGE])
        st.caption("Mini reset: take one slow breath in… and out. Ready for another round?")

    st.markdown("---")
    if st.button("← Back to home", key="shell_back"):
        _clear_state()
        state["step"] = return_step
        state["render_nonce"] = (state.get("render_nonce") or 0) + 1
        st.rerun()
