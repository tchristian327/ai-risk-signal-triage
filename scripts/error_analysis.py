#!/usr/bin/env python3
"""CLI: identify and report the worst-performing eval pairs (abs error >= 2).

Reads predictions_llm_judge_v1.json and labeled_pairs.json, then writes a
structured markdown report to data/eval/error_analysis_v1.md.

Usage:
    python scripts/error_analysis.py
    python scripts/error_analysis.py --threshold 1  # show all off-by-one errors too
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import load_all_signals
from src.portfolio import load_portfolio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

EVAL_DIR = PROJECT_ROOT / "data" / "eval"
PORTFOLIO_PATH = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run error analysis on LLM judge predictions.")
    parser.add_argument("--threshold", type=int, default=2,
                        help="Minimum abs error to include (default: 2)")
    parser.add_argument("--version", type=str, default="v1",
                        help="Prompt version to analyze (e.g. v1 or v2)")
    args = parser.parse_args()

    predictions_path = EVAL_DIR / f"predictions_llm_judge_{args.version}.json"
    analysis_out = EVAL_DIR / f"error_analysis_{args.version}.md"

    if not predictions_path.exists():
        logger.error("Predictions file not found at %s. Run run_eval.py --version %s first.",
                     predictions_path, args.version)
        sys.exit(1)

    records = json.loads(predictions_path.read_text())
    n_total = len(records)

    # Load signal and system metadata for display names
    signals = load_all_signals()
    systems = load_portfolio(PORTFOLIO_PATH)
    signal_map = {s.id: s for s in signals}
    system_map = {s.id: s for s in systems}

    # Filter to "really wrong" pairs
    bad = [r for r in records if r["abs_error"] >= args.threshold]
    bad.sort(key=lambda r: r["abs_error"], reverse=True)

    summary_line = f"{len(bad)} pairs with abs error >= {args.threshold} out of {n_total}"
    logger.info(summary_line)

    # --- Console output ---
    print(f"\n{summary_line}")
    for i, r in enumerate(bad):
        signal = signal_map.get(r["signal_id"])
        system = system_map.get(r["system_id"])
        signal_title = signal.title if signal else r["signal_id"]
        system_name = system.name if system else r["system_id"]
        print(f"\n[{i+1}] abs_error={r['abs_error']}  human={r['human_label']}  llm={r['llm_score']}")
        print(f"    Signal: {signal_title}")
        print(f"    System: {system_name}")
        if r.get("human_note"):
            print(f"    Human note: {r['human_note']}")
        print(f"    LLM reasoning: {r['llm_reasoning']}")

    # --- Markdown report ---
    lines: list[str] = [
        f"# Error analysis — LLM judge {args.version}",
        "",
        f"**{summary_line}**",
        "",
        "Sorted by absolute error descending. Pairs where the model was off by 2+ points.",
        "Human label is ground truth.",
        "",
    ]

    for i, r in enumerate(bad):
        signal = signal_map.get(r["signal_id"])
        system = system_map.get(r["system_id"])
        signal_title = signal.title if signal else r["signal_id"]
        system_name = system.name if system else r["system_id"]

        direction = "over-scored" if r["llm_score"] > r["human_label"] else "under-scored"

        lines += [
            f"## [{i+1}] {signal_title} / {system_name}",
            "",
            f"- **Abs error:** {r['abs_error']} ({direction})",
            f"- **Human label:** {r['human_label']}",
            f"- **LLM score:** {r['llm_score']}",
            f"- **Signal ID:** `{r['signal_id']}`",
            f"- **System ID:** `{r['system_id']}`",
        ]
        if r.get("human_note"):
            lines.append(f"- **Human note:** {r['human_note']}")

        lines += [
            "",
            "**LLM reasoning:**",
            "",
            f"> {r['llm_reasoning']}",
            "",
            "**LLM justification:**",
            "",
            f"> {r['llm_justification']}",
            "",
            "---",
            "",
        ]

    analysis_out.write_text("\n".join(lines))
    logger.info("Error analysis written to %s", analysis_out)


if __name__ == "__main__":
    main()
