from __future__ import annotations

import streamlit as st

from src.schemas import AISystem, Signal, ScoredPair


# Score -> (background color, text color, label)
_BADGE_STYLES: dict[int, tuple[str, str, str]] = {
    0: ("#e0e0e0", "#616161", "0 — Unrelated"),
    1: ("#e0e0e0", "#616161", "1 — Tangential"),
    2: ("#fff8e1", "#f9a825", "2 — Worth a glance"),
    3: ("#fff3e0", "#f57c00", "3 — Action recommended"),
    4: ("#ffebee", "#c62828", "4 — Urgent review"),
}


def render_score_badge(score: int) -> None:
    """Render a colored inline badge for the given 0-4 relevance score."""
    bg, fg, label = _BADGE_STYLES.get(score, ("#e0e0e0", "#616161", f"{score}"))
    html = (
        f'<span style="'
        f"background-color:{bg}; color:{fg}; font-weight:600; "
        f"padding:3px 10px; border-radius:4px; font-size:0.85rem; "
        f'border:1px solid {fg}33;">{label}</span>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_pair_row(
    pair: ScoredPair,
    signal_map: dict[str, Signal],
    system_map: dict[str, AISystem],
    *,
    show_signal: bool = True,
    show_system: bool = True,
) -> None:
    """Render one scored pair as a badge + title(s) + truncated justification + expander."""
    signal = signal_map.get(pair.signal_id)
    system = system_map.get(pair.system_id)

    col_badge, col_body = st.columns([1, 9])
    with col_badge:
        render_score_badge(pair.relevance_score)

    with col_body:
        # Build the title line
        parts: list[str] = []
        if show_signal and signal:
            parts.append(f"**{signal.title}**")
        if show_system and system:
            parts.append(f"*{system.name}*")
        st.markdown(" — ".join(parts) if parts else "*(unknown)*")

        # Truncated justification on the main row
        truncated = (
            pair.justification[:150] + "…"
            if len(pair.justification) > 150
            else pair.justification
        )
        st.caption(truncated)

        with st.expander("Full details"):
            st.markdown("**Justification**")
            st.write(pair.justification)
            st.markdown("**Reasoning**")
            st.write(pair.reasoning)
            st.markdown("**Suggested action**")
            st.write(pair.suggested_action)
            st.caption(f"Cosine similarity: {pair.cosine_similarity:.3f}")

    st.divider()


def render_system_card(system: AISystem) -> None:
    """Render a structured info block for an AI system."""
    st.subheader(system.name)
    st.markdown(f"**Model type:** {system.model_type}")
    st.markdown(f"**Purpose:** {system.purpose}")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Data inputs**")
        for item in system.data_inputs:
            st.markdown(f"- {item}")
        st.markdown("**Users**")
        for u in system.users:
            st.markdown(f"- {u}")

    with col_right:
        st.markdown("**Deployment context**")
        st.write(system.deployment_context)

    st.markdown("**Known risks**")
    for risk in system.known_risks:
        st.markdown(f"- {risk}")


def render_signal_card(signal: Signal) -> None:
    """Render a structured info block for a signal."""
    st.subheader(signal.title)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(f"**Source:** {signal.source}")
    with col_right:
        st.markdown(f"**Date:** {signal.date}")

    st.write(signal.description)

    if signal.source_url:
        st.markdown(f"[Source link]({signal.source_url})")
