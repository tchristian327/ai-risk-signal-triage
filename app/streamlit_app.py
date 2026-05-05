from __future__ import annotations

import json
import sys
from pathlib import Path

# Streamlit Cloud runs app/streamlit_app.py from a working directory that
# doesn't include the project root on sys.path. Add it explicitly so that
# `from src.schemas import ...` resolves correctly.
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    render_comparison_table,
    render_confusion_matrix,
    render_pair_row,
    render_signal_card,
    render_system_card,
)


@st.cache_data
def load_eval_data() -> dict | None:
    eval_dir = PROJECT_ROOT / "data" / "eval"
    try:
        v1 = json.loads((eval_dir / "metrics_llm_judge_v1.json").read_text())
        v2 = json.loads((eval_dir / "metrics_llm_judge_v2.json").read_text())
        baseline = json.loads((eval_dir / "metrics_baseline.json").read_text())
        return {"v1": v1, "v2": v2, "baseline": baseline}
    except FileNotFoundError:
        return None


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
tab_overview, tab_system, tab_signal, tab_eval = st.tabs(
    ["Overview", "By System", "By Signal", "Evaluation"]
)

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
        "[GitHub repo](https://github.com/tchristian327/ai-risk-signal-triage)"
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

# ── Evaluation ───────────────────────────────────────────────────────────────
with tab_eval:
    eval_data = load_eval_data()

    if eval_data is None:
        st.info(
            "Eval data not yet available. "
            "Run the eval scripts to populate: `python scripts/run_eval.py`"
        )
    else:
        st.markdown("## How well does this work?")
        st.markdown(
            "Measured against 49 hand-labeled (signal, system) pairs "
            "spanning the full 0–4 score range, using stratified sampling "
            "on cosine similarity to avoid biasing the eval set toward easy positives."
        )

        st.markdown("### System comparison")
        render_comparison_table(eval_data["v1"], eval_data["v2"], eval_data["baseline"])
        st.caption(
            "★ = best value in that row. "
            "Baseline uses leave-one-out cross-validation (48 labeled examples per prediction). "
            "LLM judge is zero-shot."
        )

        st.markdown("### Headline metric")
        v2_recall = eval_data["v2"]["recall_at_threshold_3"]
        v1_recall = eval_data["v1"]["recall_at_threshold_3"]
        delta_pp = (v2_recall["recall"] - v1_recall["recall"]) * 100
        col_left, col_mid, col_right = st.columns([1, 2, 1])
        with col_mid:
            st.metric(
                label="High-relevance signals caught — LLM judge v2 (score ≥ 3)",
                value=(
                    f"{v2_recall['recall'] * 100:.1f}% "
                    f"({v2_recall['true_positives']} of {v2_recall['total_positives']})"
                ),
                delta=f"+{delta_pp:.1f}pp vs v1",
            )

        st.markdown("### Confusion matrix — LLM judge v2")
        st.caption("Rows = predicted score · Columns = human label · Green diagonal = correct predictions")
        render_confusion_matrix(eval_data["v2"]["confusion_matrix"])

        st.markdown("### What these numbers mean")
        st.markdown(
            "The LLM judge v2 improved across every metric after four targeted prompt changes, "
            "each tracing back to a specific failure mode identified in the error analysis. "
            "Off-by-one accuracy jumped from 65% to 76%, showing the model is landing in the "
            "right neighborhood more often even when it doesn't nail the exact score; recall "
            "at score ≥ 3 rose from 33% to 44%, meaning 2 more high-relevance signals were "
            "caught. The baseline classifier still wins on recall (61%) and exact match (37%) "
            "— it's ~450× faster and costs nothing — but it misses more than half of urgent "
            "signals, and it runs under leave-one-out CV with 48 labeled examples per prediction "
            "while the LLM judge is zero-shot. For governance triage, where a missed urgent "
            "signal is far worse than a false alarm, the LLM judge's better calibration and "
            "human-readable reasoning justify its cost."
        )

        st.markdown("### Limitations")
        st.markdown(
            "- **Eval set size:** 49 pairs labeled by a single human. "
            "A production system would require multiple labelers and inter-rater reliability scoring.\n"
            "- **Signal sources:** Signals come primarily from the AI Incident Database. "
            "A production system would pull from regulatory feeds, vendor advisories, "
            "and internal incident reports.\n"
            "- **Fictional portfolio:** System cards are fictional. "
            "Real governance work would involve interviewing model owners "
            "to build accurate system cards."
        )
