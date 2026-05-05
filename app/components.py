from __future__ import annotations

import json

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


# ---------------------------------------------------------------------------
# Eval view helpers
# ---------------------------------------------------------------------------

_TH = (
    "padding:8px 14px; text-align:center; background:#f5f5f5; color:#212121; "
    "border:1px solid #e0e0e0; font-size:0.88rem;"
)
_TD = "padding:8px 14px; text-align:center; border:1px solid #e0e0e0; font-size:0.88rem;"
_TD_LABEL = "padding:8px 14px; text-align:left; border:1px solid #e0e0e0; font-size:0.88rem; font-weight:600;"
_TD_WIN = (
    "padding:8px 14px; text-align:center; border:1px solid #e0e0e0; "
    "font-size:0.88rem; font-weight:700; background:#e8f5e9; color:#1b5e20;"
)


def render_comparison_table(v1: dict, v2: dict, baseline: dict) -> None:
    """Render three-column comparison table. Highlights best value per row."""

    def pct(val: float) -> str:
        return f"{val * 100:.1f}%"

    def recall_str(d: dict) -> str:
        return f"{d['recall'] * 100:.1f}% ({d['true_positives']}/{d['total_positives']})"

    def latency_str(meta: dict) -> str:
        ms = meta.get("avg_latency_ms", 0)
        return f"{ms:,.0f} ms"

    def cost_str(meta: dict, n_pairs: int) -> str:
        cost = meta.get("estimated_cost_usd", 0.0)
        if cost == 0:
            return "$0.00"
        return f"${cost / n_pairs * 1000:.2f}"

    n = v1["n_pairs"]
    m1, m2, mb = v1["run_metadata"], v2["run_metadata"], baseline["run_metadata"]

    rows = [
        {
            "label": "Exact match accuracy",
            "vals": [pct(v1["exact_match_accuracy"]), pct(v2["exact_match_accuracy"]), pct(baseline["exact_match_accuracy"])],
            "scores": [v1["exact_match_accuracy"], v2["exact_match_accuracy"], baseline["exact_match_accuracy"]],
            "best_fn": max,
        },
        {
            "label": "Off-by-one accuracy",
            "vals": [pct(v1["off_by_one_accuracy"]), pct(v2["off_by_one_accuracy"]), pct(baseline["off_by_one_accuracy"])],
            "scores": [v1["off_by_one_accuracy"], v2["off_by_one_accuracy"], baseline["off_by_one_accuracy"]],
            "best_fn": max,
        },
        {
            "label": "Recall at score ≥ 3",
            "vals": [recall_str(v1["recall_at_threshold_3"]), recall_str(v2["recall_at_threshold_3"]), recall_str(baseline["recall_at_threshold_3"])],
            "scores": [v1["recall_at_threshold_3"]["recall"], v2["recall_at_threshold_3"]["recall"], baseline["recall_at_threshold_3"]["recall"]],
            "best_fn": max,
        },
        {
            "label": "Avg latency / pair",
            "vals": [latency_str(m1), latency_str(m2), latency_str(mb)],
            "scores": [m1.get("avg_latency_ms", float("inf")), m2.get("avg_latency_ms", float("inf")), mb.get("avg_latency_ms", float("inf"))],
            "best_fn": min,
        },
        {
            "label": "Cost / 1k pairs",
            "vals": [cost_str(m1, n), cost_str(m2, n), cost_str(mb, n)],
            "scores": [m1.get("estimated_cost_usd", float("inf")), m2.get("estimated_cost_usd", float("inf")), mb.get("estimated_cost_usd", 0.0)],
            "best_fn": min,
        },
    ]

    header = (
        f'<tr>'
        f'<th style="{_TH} text-align:left;">Metric</th>'
        f'<th style="{_TH}">LLM Judge v1</th>'
        f'<th style="{_TH}">LLM Judge v2</th>'
        f'<th style="{_TH}">Baseline Classifier</th>'
        f'</tr>'
    )

    body = ""
    for row in rows:
        best_score = row["best_fn"](row["scores"])
        cells = f'<td style="{_TD_LABEL}">{row["label"]}</td>'
        for i, val in enumerate(row["vals"]):
            is_best = row["scores"][i] == best_score
            style = _TD_WIN if is_best else _TD
            marker = " ★" if is_best else ""
            cells += f'<td style="{style}">{val}{marker}</td>'
        body += f"<tr>{cells}</tr>"

    html = (
        '<div style="overflow-x:auto; margin-bottom:16px;">'
        '<table style="border-collapse:collapse; width:100%;">'
        f"<thead>{header}</thead>"
        f"<tbody>{body}</tbody>"
        "</table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_confusion_matrix(matrix: list[list[int]]) -> None:
    """Render a 5x5 confusion matrix. Rows = predicted score, columns = human label.

    Diagonal cells are highlighted to show correct predictions.
    """
    labels = ["0", "1", "2", "3", "4"]

    col_headers = "".join(
        f'<th style="{_TH}">{lbl}</th>' for lbl in labels
    )
    header = (
        f'<tr>'
        f'<th style="{_TH} text-align:left;">Pred ↓ / Human →</th>'
        f'{col_headers}'
        f'</tr>'
    )

    body = ""
    for pred_idx, row in enumerate(matrix):
        cells = f'<td style="{_TD_LABEL}">{labels[pred_idx]}</td>'
        for human_idx, count in enumerate(row):
            is_diag = pred_idx == human_idx
            style = _TD_WIN if is_diag else _TD
            cells += f'<td style="{style}">{count}</td>'
        body += f"<tr>{cells}</tr>"

    html = (
        '<div style="overflow-x:auto; margin-bottom:8px;">'
        '<table style="border-collapse:collapse;">'
        f"<thead>{header}</thead>"
        f"<tbody>{body}</tbody>"
        "</table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)
