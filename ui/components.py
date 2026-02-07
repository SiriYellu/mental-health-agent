"""
Reusable UI blocks for CalmCompass: glass cards, stepper, calm meter, breathing timer.
Pure Streamlit + HTML/CSS; no heavy JS or external assets.
Apple-like motion: motion_container for step transitions; respects prefers-reduced-motion via CSS.
"""

from __future__ import annotations

import time
from typing import Sequence

import streamlit as st


def motion_container(step_key: str, html_content: str, nonce: int = 0, extra_class: str = "") -> None:
    """
    Wrap main content in a div that gets fade+slide-up animation on appear.
    step_key identifies the screen; nonce forces re-animation when step changes.
    Use extra_class for e.g. cc-support-now (softer blur). Animation disabled by
    prefers-reduced-motion in global CSS.
    """
    classes = f"cc-motion-screen cc-motion-in {extra_class}".strip()
    st.markdown(
        f'<div class="{classes}" data-step="{step_key}" data-nonce="{nonce}">'
        f"{html_content}</div>",
        unsafe_allow_html=True,
    )


def glass_card(html_content: str, class_extra: str = "") -> None:
    """Render content inside a glassmorphism card (blur, soft border, shadow)."""
    st.markdown(
        f'<div class="cc-glass-card {class_extra}">{html_content}</div>',
        unsafe_allow_html=True,
    )


def card_section(title: str, body: str, icon: str = "💬") -> None:
    """One section block inside a result panel (icon + title + body)."""
    st.markdown(
        f'<div class="cc-card-section">'
        f'<span class="cc-card-icon" aria-hidden="true">{icon}</span>'
        f'<div class="cc-card-section-inner">'
        f'<div class="cc-card-section-title">{title}</div>'
        f'<div class="cc-card-section-body">{body}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def stepper_html(current: int, total: int, labels: Sequence[str] | None = None) -> str:
    """Build stepper HTML string (for embedding in motion_container)."""
    progress_pct = round((current / total) * 100) if total else 0
    steps = []
    for i in range(1, total + 1):
        active = "active" if i == current else ("done" if i < current else "")
        label = (labels[i - 1]) if labels and i <= len(labels) else f"Step {i}"
        steps.append(
            f'<span class="cc-step {active}" data-step="{i}">'
            f'<span class="cc-step-dot"></span><span class="cc-step-label">{label}</span>'
            f'</span>'
        )
    return (
        '<div class="cc-stepper" style="--cc-stepper-pct: ' + str(progress_pct) + ';">'
        '<div class="cc-stepper-progress" aria-hidden="true"></div>'
        + "".join(steps)
        + "</div>"
    )


def stepper(current: int, total: int, labels: Sequence[str] | None = None) -> None:
    """
    Left-to-right stepper with animated progress fill and current-step glow.
    Progress line fills from 0 to (current/total)*100%; active step has glow.
    """
    st.markdown(stepper_html(current, total, labels), unsafe_allow_html=True)


def calm_meter(phq2_score: int | None, gad2_score: int | None) -> None:
    """
    Gauge/bar showing mood+worry intensity (0–100). Fill animates from 0 to value via CSS.
    Never diagnostic; label as "How much you've been carrying."
    """
    # PHQ-2 max 6, GAD-2 max 6 → combined 0–12. Map to 0–100 for display.
    p = phq2_score if phq2_score is not None else 0
    g = gad2_score if gad2_score is not None else 0
    total = p + g  # 0–12
    percent = min(100, round((total / 12) * 100)) if (phq2_score is not None or gad2_score is not None) else 0
    if phq2_score is None and gad2_score is None:
        percent = 0
    st.markdown(
        '<div class="cc-calm-meter" style="--cc-meter-pct: ' + str(percent) + ';">'
        '<div class="cc-calm-meter-label">How much you\'ve been carrying</div>'
        '<div class="cc-calm-meter-track"><div class="cc-calm-meter-fill"></div></div>'
        '<div class="cc-calm-meter-note">Not a diagnosis — a reflection of recent answers.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def breathing_timer_placeholder(seconds: int = 60) -> None:
    """
    Run a visual countdown for breathing (e.g. 60 seconds).
    Timer card has a pulsing ring during countdown (CSS-only). Blocks for the duration.
    """
    placeholder = st.empty()
    for remaining in range(seconds, -1, -1):
        mins, secs = divmod(remaining, 60)
        # Pulsing ring only during countdown (not on "Done")
        pulse_class = " cc-timer-pulse" if remaining > 0 else ""
        placeholder.markdown(
            f'<div class="cc-timer-box{pulse_class}">'
            f'<div class="cc-timer-ring" aria-hidden="true"></div>'
            f'<div class="cc-timer-value">{mins}:{secs:02d}</div>'
            f'<div class="cc-timer-label">Breathe in 4 · Hold 7 · Breathe out 8</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if remaining > 0:
            time.sleep(1)
    placeholder.markdown(
        '<div class="cc-timer-box cc-timer-done">'
        '<div class="cc-timer-value">Done</div>'
        '<div class="cc-timer-label">You did it. Take a moment to notice how you feel.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def grounding_checkboxes() -> dict[str, bool]:
    """
    Render 5-4-3-2-1 grounding with checkboxes. Returns dict of step_id -> checked.
    """
    steps = [
        ("5", "See", "Name 5 things you can see"),
        ("4", "Touch", "Name 4 things you can feel"),
        ("3", "Hear", "Name 3 things you can hear"),
        ("2", "Smell", "Name 2 things you can smell"),
        ("1", "One thing", "One thing you're okay about right now"),
    ]
    out = {}
    for num, kind, label in steps:
        key = f"ground_{num}_{kind}".replace(" ", "_")
        out[key] = st.checkbox(f"**{num} – {kind}** — {label}", key=key)
    return out


def progress_ring(percent: float, label: str = "Complete") -> None:
    """Simple circular progress (CSS-only). percent 0–100."""
    percent = max(0, min(100, percent))
    st.markdown(
        f'<div class="cc-progress-ring">'
        f'<div class="cc-progress-ring-circle" style="--p:{percent}"></div>'
        f'<span class="cc-progress-ring-label">{label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
