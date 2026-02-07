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


def render_chat_widget() -> None:
    """
    Render the chat pop-up at the bottom: expander with chat history and input.
    Uses st.chat_message and st.chat_input. Stores messages in st.session_state[CHAT_MESSAGES_KEY].
    """
    if CHAT_MESSAGES_KEY not in st.session_state:
        st.session_state[CHAT_MESSAGES_KEY] = []

    messages = st.session_state[CHAT_MESSAGES_KEY]

    # Pop-up style: expander at bottom
    with st.expander("💬 **Chat with me** — I'm here to listen", expanded=False):
        st.caption("Ask how you are, how your day was — I'll answer sweetly. Nothing is stored.")
        # Welcome message if first time
        if len(messages) == 0:
            with st.chat_message("assistant"):
                st.markdown(CHAT_WELCOME)
            # Don't add to messages so we don't duplicate on rerun; we'll show it only when history is empty
        # Show history
        for m in messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        # Input
        if prompt := st.chat_input("Say something..."):
            messages.append({"role": "user", "content": prompt})
            reply = get_bot_response(prompt, messages)
            messages.append({"role": "assistant", "content": reply})
            st.rerun()

    # When history is empty, the welcome is shown above; after first user message we show full history including welcome. So we need to add welcome as first message when they first open and send nothing yet - or add welcome to messages when empty so it displays in the loop. Simpler: when messages is empty, show welcome in the loop by treating it as one assistant message for display only. So we display: [welcome] + messages. So:
    # for display: if not messages: show welcome. else: for m in messages: show m.
    # But then when they type, we add user + assistant. So messages will have 2 items. We never added welcome to messages. So the welcome only shows when messages is empty. Good.
</think>
Fixing the chat so the welcome message displays correctly and the first exchange is preserved.
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
StrReplace