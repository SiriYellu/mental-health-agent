"""
CalmCompass chat widget: pop-up at bottom of page. Asks how you are, how your day was;
responds sweetly to lift mood. No external API; rule-based warm replies.
"""

import re
import random
import streamlit as st

CHAT_MESSAGES_KEY = "chat_messages"
CHAT_WELCOME = "Hi! I'm here if you want to chat. How are you today? 💙"

# Sweet, mood-lifting replies (keyword hints → responses)
REPLIES_LOW = [
    "I'm really glad you're here. Tough moments don't last forever — and you're not alone. Want to share a little more, or would you rather we just take a breath together?",
    "That sounds heavy. You don't have to have it all figured out. One small step at a time. I'm rooting for you. 🌱",
    "Sending you a virtual hug. It's okay to not be okay. Would it help to name one small thing that went right today, or would you rather just sit with this for a bit?",
]
REPLIES_GOOD = [
    "That's wonderful to hear! You deserve good moments. What made today a good day? I'd love to hear. ✨",
    "So happy for you! Little wins count. Keep that energy — you're doing great. 🌟",
    "Love that for you! Thanks for sharing. It really does help to notice the good stuff.",
]
REPLIES_OKAY = [
    "That's totally valid. Some days are just in-between — and that's okay. Want to talk about anything, or would you rather keep it light?",
    "I hear you. If you want to vent or share, I'm here. No pressure. 💙",
]
REPLIES_DAY = [
    "How was your day? Even one small good thing counts. ☀️",
    "I'd love to hear — how did today go for you?",
]
REPLIES_THANKS = [
    "Anytime. You matter, and I'm always here when you need a little lift. Take care of yourself. 💙",
    "So glad I could help a bit. Remember: you're doing better than you think. Big hug!",
]
REPLIES_GREETING = [
    "Hey! So nice to see you here. How are you feeling right now?",
    "Hi there! I'm here to listen. How's your day going?",
    "Hello! How are you doing today? 💙",
]
REPLIES_DEFAULT = [
    "I'm here with you. Whatever you're feeling, it's valid. Want to tell me more, or we can just take it one breath at a time. 🌿",
    "Thanks for sharing that with me. You're not alone in this. One small step at a time. 💙",
    "I hear you. Sometimes just saying it out loud helps a little. I'm glad you're here.",
]


def _normalize(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower().strip())


def get_bot_response(user_message: str, history: list) -> str:
    """
    Return a sweet, short reply to lift mood. Uses simple keyword/pattern matching.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    msg = _normalize(user_message)
    if not msg:
        return random.choice(REPLIES_DEFAULT)

    # Greetings
    if any(w in msg for w in ("hi", "hello", "hey", "hiya")):
        return random.choice(REPLIES_GREETING)

    # Positive
    if any(w in msg for w in ("good", "great", "fine", "ok", "okay", "better", "happy", "alright", "well", "lovely", "amazing")):
        if any(w in msg for w in ("not", "n't", "not really")):
            pass  # "not good" etc. — fall through
        else:
            return random.choice(REPLIES_GOOD)

    # Low / struggling
    if any(w in msg for w in ("bad", "sad", "terrible", "awful", "horrible", "stressed", "anxious", "overwhelmed", "lonely", "tired", "exhausted", "down", "depressed", "not good", "not great", "struggling", "hard", "difficult")):
        return random.choice(REPLIES_LOW)

    # Okay / meh
    if any(w in msg for w in ("meh", "so-so", "alright", "could be better", "in between")):
        return random.choice(REPLIES_OKAY)

    # Day
    if any(w in msg for w in ("day", "today", "yesterday")):
        if any(w in msg for w in ("good", "great", "fine", "ok", "lovely")):
            return random.choice(REPLIES_GOOD)
        if any(w in msg for w in ("bad", "rough", "hard", "tough", "long")):
            return random.choice(REPLIES_LOW)
        return random.choice(REPLIES_DAY)

    # Thanks / bye
    if any(w in msg for w in ("thank", "thanks", "bye", "goodbye", "talk later")):
        return random.choice(REPLIES_THANKS)

    return random.choice(REPLIES_DEFAULT)


def render_chat_widget(*, expanded_on_first_visit: bool = True, floating: bool = True) -> None:
    """
    Render the chat as a pop-up: floating card (or inline) with chat history and input.
    - expanded_on_first_visit: open the expander when there are no messages yet.
    - floating: use CSS so the chat appears as a fixed card (bottom-right); set False for inline.
    """
    if CHAT_MESSAGES_KEY not in st.session_state:
        st.session_state[CHAT_MESSAGES_KEY] = []

    messages = st.session_state[CHAT_MESSAGES_KEY]
    is_first_visit = len(messages) == 0
    expanded = expanded_on_first_visit and is_first_visit

    # Anchor for CSS: float the next sibling (the expander) as a pop-up card
    if floating:
        st.markdown(
            '<div class="cc-chat-popup-anchor" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )

    with st.expander("💬 **Chat with me** — I'm here to listen", expanded=expanded, key="cc_chat_expander"):
        st.markdown(
            '<p class="cc-chat-intro">Ask how you are, how your day was — I\'ll answer sweetly. Nothing is stored.</p>',
            unsafe_allow_html=True,
        )
        if is_first_visit:
            with st.chat_message("assistant"):
                st.markdown(CHAT_WELCOME)
        for m in messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        prompt = st.chat_input("Say something...")
        if prompt:
            messages.append({"role": "user", "content": prompt})
            reply = get_bot_response(prompt, messages)
            messages.append({"role": "assistant", "content": reply})
            st.rerun()