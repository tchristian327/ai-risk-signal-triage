from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.schemas import Digest

# Page config must be the first Streamlit call in the file.
st.set_page_config(
    page_title="AI Risk Signal Triage",
    page_icon="🛡",
    layout="wide",
)

# Defer component imports until after page config to avoid any accidental
# early Streamlit calls inside the module.
from app.components import (  # noqa: E402
    render_pair_row,
    render_score_badge,
    render_signal_card,
    render_system_card,
)

PROJECT_ROOT = Path(__file__).parent.parent


@st.cache_data
def load_digest() -> Digest:
    path = PROJECT_ROOT / "data" / "outputs" / "digest.json"
    try:
        return Digest.model_validate_json(path.read_text())
    except FileNotFoundError:
        st.error(
            "digest.json not found at data/outputs/digest.json. "
            "Run the pipeline first: `python scripts/run_pipeline.py`"
        )
        st.stop()
    except Exception as exc:
        st.error(f"Failed to load digest: {exc}")
        st.stop()


# ---------------------------------------------------------------------------
# Load data and build lookup maps once per session
# ---------------------------------------------------------------------------
digest = load_digest()
signal_map = {s.id: s for s in digest.signals}
system_map = {s.id: s for s in digest.systems}

high_relevance = [p for p in digest.scored_pairs if p.relevance_score >= 3]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🛡 AI Risk Signal Triage")
st.caption(
    "Continuous oversight of external AI risk signals against an insurance company portfolio"
)

meta = digest.metadata
mc1, mc2, mc3 = st.columns(3)
mc1.markdown(
    f"**Last run:** {meta.run_timestamp.strftime('%-I:%M %p UTC, %b %-d %Y')}"
)
mc2.markdown(f"**Model:** {meta.model_name}")
mc3.markdown(
    f"**Pairs scored:** {meta.num_pairs_scored} total · "
    f"{len(high_relevance)} high-relevance (≥ 3)"
)

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_system, tab_signal = st.tabs(["Overview", "By System", "By Signal"])

# ── Overview ────────────────────────────────────────────────────────────────
with tab_overview:
    c1, c2, c3 = st.columns(3)
    c1.metric("AI Systems", meta.num_systems)
    c2.metric("Signals ingested", meta.num_signals)
    c3.metric("High-relevance pairs (≥ 3)", len(high_relevance))

    st.markdown("### Top relevant pairs")
    top_pairs = sorted(
        digest.scored_pairs, key=lambda p: p.relevance_score, reverse=True
    )[:10]

    for pair in top_pairs:
        render_pair_row(
            pair,
            signal_map,
            system_map,
            show_signal=True,
            show_system=True,
        )

    st.markdown("---")
    st.markdown("#### About this project")
    st.markdown(
        "This dashboard is a portfolio project demonstrating agentic AI risk triage for an "
        "insurance company context. It ingests real signals from the AI Incident Database and "
        "hand-curated governance sources, then uses an LLM judge to score each signal against a "
        "fictional AI portfolio. The goal is to surface actionable risk signals to model owners "
        "before they become incidents. "
        "[GitHub repo](https://github.com/TODO)"  # fill in after pushing to GitHub
    )

# ── By System ────────────────────────────────────────────────────────────────
with tab_system:
    system_options = {s.name: s for s in digest.systems}
    selected_system_name = st.selectbox(
        "Select a system", options=list(system_options.keys())
    )
    selected_system = system_options[selected_system_name]

    render_system_card(selected_system)

    st.markdown("### Signals for this system")
    system_pairs = sorted(
        [p for p in digest.scored_pairs if p.system_id == selected_system.id],
        key=lambda p: p.relevance_score,
        reverse=True,
    )[:10]

    if not system_pairs:
        st.info("No scored signals for this system in the latest run.")
    else:
        for pair in system_pairs:
            render_pair_row(
                pair,
                signal_map,
                system_map,
                show_signal=True,
                show_system=False,
            )

# ── By Signal ────────────────────────────────────────────────────────────────
with tab_signal:
    # Only show signals that passed the retrieval filter and have scored pairs.
    # 51 of 78 raw signals were filtered out at retrieval; showing them would
    # produce an empty state on the vast majority of dropdown picks.
    signal_ids_with_pairs = {p.signal_id for p in digest.scored_pairs}
    signal_options = sorted(
        [s for s in digest.signals if s.id in signal_ids_with_pairs],
        key=lambda s: s.title,
    )
    signal_titles = [s.title for s in signal_options]
    signal_by_title = {s.title: s for s in signal_options}

    st.caption(
        f"Showing {len(signal_options)} of {len(digest.signals)} signals "
        "that passed the retrieval filter and have at least one scored pair."
    )
    selected_signal_title = st.selectbox(
        "Select a signal", options=signal_titles
    )
    selected_signal = signal_by_title[selected_signal_title]

    render_signal_card(selected_signal)

    st.markdown("### Systems affected by this signal")
    signal_pairs = sorted(
        [p for p in digest.scored_pairs if p.signal_id == selected_signal.id],
        key=lambda p: p.relevance_score,
        reverse=True,
    )

    if not signal_pairs:
        st.info("No systems scored for this signal in the latest run.")
    else:
        for pair in signal_pairs:
            render_pair_row(
                pair,
                signal_map,
                system_map,
                show_signal=False,
                show_system=True,
            )
