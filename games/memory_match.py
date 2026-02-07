"""
Memory Match — flip cards to find pairs. Reflects memory and focus.
Support tool; not a test. 4 pairs (8 cards).
"""

import random
import streamlit as st

SESSION_BOARD = "memory_board"
SESSION_REVEALED = "memory_revealed"
SESSION_MATCHED = "memory_matched"
SESSION_MOVES = "memory_moves"
SESSION_PENDING_FLIP = "memory_pending_flip"

# 4 pairs: each symbol twice
SYMBOLS = ["🌸", "🍀", "🌙", "⭐"]
PAIRS = 4
TOTAL_CARDS = 8


def _ensure_game_state():
    if SESSION_BOARD not in st.session_state:
        board = (SYMBOLS * 2)[:TOTAL_CARDS]
        random.shuffle(board)
        st.session_state[SESSION_BOARD] = board
        st.session_state[SESSION_REVEALED] = []
        st.session_state[SESSION_MATCHED] = set()
        st.session_state[SESSION_MOVES] = 0
        st.session_state[SESSION_PENDING_FLIP] = False


def _clear_game_state():
    for key in (SESSION_BOARD, SESSION_REVEALED, SESSION_MATCHED, SESSION_MOVES, SESSION_PENDING_FLIP):
        if key in st.session_state:
            del st.session_state[key]


def render_memory_match(return_step: str = "intro") -> None:
    """
    Memory Match: 4x2 grid of cards. Flip two at a time; match pairs.
    return_step: where to go when user clicks Back to home.
    """
    _ensure_game_state()
    board = st.session_state[SESSION_BOARD]
    revealed = list(st.session_state[SESSION_REVEALED])
    matched = st.session_state[SESSION_MATCHED]
    moves = st.session_state[SESSION_MOVES]
    pending_flip = st.session_state[SESSION_PENDING_FLIP]

    st.markdown("### 🧠 Memory Match")
    st.caption("Find matching pairs. Flip two cards at a time — good for focus and short-term memory.")

    # Not a match — show message and Continue
    if pending_flip and len(revealed) == 2:
        st.info("Not a match. They'll flip back.")
        if st.button("Continue", type="primary", key="mem_continue"):
            st.session_state[SESSION_REVEALED] = []
            st.session_state[SESSION_PENDING_FLIP] = False
            st.rerun()
        if st.button("← Back to home", key="mem_back_pending"):
            _clear_game_state()
            st.session_state["step"] = return_step
            st.session_state["render_nonce"] = (st.session_state.get("render_nonce") or 0) + 1
            st.rerun()
        return

    # Win
    if len(matched) == TOTAL_CARDS:
        st.balloons()
        st.success(f"You found all pairs in **{moves}** moves. Nice focus.")
        if st.button("← Back to home", key="mem_back_win"):
            _clear_game_state()
            st.session_state["step"] = return_step
            st.session_state["render_nonce"] = (st.session_state.get("render_nonce") or 0) + 1
            st.rerun()
        return

    # Grid: 4 columns x 2 rows
    st.markdown(f"**Moves:** {moves} &nbsp; **Pairs found:** {len(matched) // 2}")
    for row in range(2):
        cols = st.columns(4)
        for col in range(4):
            idx = row * 4 + col
            with cols[col]:
                is_revealed = idx in revealed or idx in matched
                label = board[idx] if is_revealed else "🂠"
                key = f"mem_{idx}"
                if st.button(label, key=key, use_container_width=True):
                    if pending_flip or idx in matched or idx in revealed:
                        st.rerun()
                        return
                    if len(revealed) >= 2:
                        st.rerun()
                        return
                    # New flip
                    new_revealed = revealed + [idx]
                    st.session_state[SESSION_REVEALED] = new_revealed
                    st.session_state[SESSION_MOVES] = moves + 1
                    if len(new_revealed) == 2:
                        if board[new_revealed[0]] == board[new_revealed[1]]:
                            st.session_state[SESSION_MATCHED] = matched | {new_revealed[0], new_revealed[1]}
                            st.session_state[SESSION_REVEALED] = []
                        else:
                            st.session_state[SESSION_PENDING_FLIP] = True
                    st.rerun()

    st.markdown("---")
    if st.button("← Back to home", key="mem_back"):
        _clear_game_state()
        st.session_state["step"] = return_step
        st.session_state["render_nonce"] = (st.session_state.get("render_nonce") or 0) + 1
        st.rerun()
