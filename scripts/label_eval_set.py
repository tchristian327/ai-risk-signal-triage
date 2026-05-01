#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eval_sampling import select_eval_pairs
from src.portfolio import load_portfolio
from src.schemas import LabeledPair, SimilarityPair

SIMILARITIES_PATH = PROJECT_ROOT / "data" / "outputs" / "similarities.json"
PAIRS_TO_LABEL_PATH = PROJECT_ROOT / "data" / "eval" / "pairs_to_label.json"
LABELED_PAIRS_PATH = PROJECT_ROOT / "data" / "eval" / "labeled_pairs.json"
AIID_SIGNALS_PATH = PROJECT_ROOT / "data" / "signals" / "processed" / "aiid_signals.json"
GOV_SIGNALS_PATH = PROJECT_ROOT / "data" / "signals" / "processed" / "governance_signals.json"

WIDE_SEP = "═" * 52
NARROW_SEP = "─" * 52

RUBRIC = """\
  0 — Unrelated
  1 — Tangential
  2 — Worth a glance
  3 — Action recommended
  4 — Urgent review"""


def load_signals() -> dict[str, dict]:
    signals: dict[str, dict] = {}
    for path in [AIID_SIGNALS_PATH, GOV_SIGNALS_PATH]:
        with path.open() as f:
            for s in json.load(f):
                signals[s["id"]] = s
    return signals


def load_similarities() -> list[SimilarityPair]:
    with SIMILARITIES_PATH.open() as f:
        data = json.load(f)
    return [SimilarityPair(**d) for d in data]


def load_pairs_to_label() -> list[dict]:
    if not PAIRS_TO_LABEL_PATH.exists():
        return []
    with PAIRS_TO_LABEL_PATH.open() as f:
        return json.load(f)


def save_pairs_to_label(pairs: list[dict]) -> None:
    PAIRS_TO_LABEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PAIRS_TO_LABEL_PATH.open("w") as f:
        json.dump(pairs, f, indent=2)


def load_labeled_pairs() -> list[dict]:
    if not LABELED_PAIRS_PATH.exists():
        return []
    with LABELED_PAIRS_PATH.open() as f:
        return json.load(f)


def append_labeled_pair(pair: LabeledPair, existing: list[dict]) -> list[dict]:
    """Append pair to existing list, write entire file, return updated list."""
    updated = existing + [json.loads(pair.model_dump_json())]
    with LABELED_PAIRS_PATH.open("w") as f:
        json.dump(updated, f, indent=2)
    return updated


def overwrite_label(pair_info: dict, new_score: int, note: str, existing: list[dict]) -> list[dict]:
    """Replace the existing label for this pair in-place; rewrite file."""
    new_entry = LabeledPair(
        signal_id=pair_info["signal_id"],
        system_id=pair_info["system_id"],
        cosine_similarity=pair_info["cosine_similarity"],
        human_label=new_score,
        human_note=note,
        labeled_at=datetime.now(tz=timezone.utc),
    )
    updated = [
        json.loads(new_entry.model_dump_json())
        if p["signal_id"] == pair_info["signal_id"] and p["system_id"] == pair_info["system_id"]
        else p
        for p in existing
    ]
    with LABELED_PAIRS_PATH.open("w") as f:
        json.dump(updated, f, indent=2)
    return updated


def do_back_navigation(
    session_labeled: list[tuple[int, dict]],
    labeled: list[dict],
    signals: dict,
    systems: dict,
    total: int,
) -> list[dict]:
    """Walk backward through pairs labeled this session, allowing re-scoring.

    Multiple 'b' presses walk back one more pair each time. Enter keeps the
    existing label; a score (0-4) overwrites it. Returns when the user
    enters a score, presses Enter, or exhausts history.
    """
    back_idx = len(session_labeled) - 1

    while True:
        if back_idx < 0:
            print("No previous pair to revisit.")
            return labeled

        pair_number, pair_info = session_labeled[back_idx]
        existing = next(
            (
                p for p in labeled
                if p["signal_id"] == pair_info["signal_id"]
                and p["system_id"] == pair_info["system_id"]
            ),
            None,
        )

        render_pair(pair_info, signals, systems, pair_number, total)
        if existing:
            note_display = existing.get("human_note") or "(none)"
            print(f"Previously labeled: {existing['human_label']}")
            print(f"Previous note: {note_display}")
            print()

        while True:
            raw = input("New score (0-4), Enter to keep, or 'b' for earlier pair: ").strip().lower()
            if raw == "":
                return labeled
            if raw == "b":
                back_idx -= 1
                break  # go back one more in outer while
            if raw in ("0", "1", "2", "3", "4"):
                note = input("Note (optional, press Enter to skip): ").strip()
                labeled = overwrite_label(pair_info, int(raw), note, labeled)
                print(f"Label updated.")
                return labeled
            print("Invalid input. Enter 0-4, Enter to keep, or 'b' for earlier pair.")


def build_cosine_lookup(similarities: list[SimilarityPair]) -> dict[tuple[str, str], float]:
    return {(p.signal_id, p.system_id): p.cosine_similarity for p in similarities}


def render_pair(pair_info: dict, signals: dict, systems: dict, index: int, total: int) -> None:
    sig = signals[pair_info["signal_id"]]
    sys_ = systems[pair_info["system_id"]]

    print(f"\n{WIDE_SEP}")
    print(f"Pair {index} of {total}")
    print(WIDE_SEP)
    print()
    print(f"SYSTEM: {sys_.name}")
    print(f"Purpose: {sys_.purpose}")
    print(f"Model type: {sys_.model_type}")
    print(f"Data inputs: {', '.join(sys_.data_inputs)}")
    print("Known risks:")
    for risk in sys_.known_risks:
        print(f"  • {risk}")
    print()
    print(NARROW_SEP)
    print(f"SIGNAL: {sig['title']}")
    incident_desc = sig.get("incident_description", "")
    if incident_desc or sig.get("source") == "AI Incident Database":
        print(f"Source: AIID | Date: {sig['date']}")
        if incident_desc:
            print(f"Summary: {incident_desc}")
            print()
        details = sig.get("full_text") or sig.get("description", "")
        print(f"Details: {details}")
    else:
        print(f"Source: {sig['source']} | Date: {sig['date']}")
        display_text = sig.get("full_text") or sig["description"]
        print(f"Description: {display_text}")
    print()
    print(f"URL: {sig['source_url']}")
    print()
    print(NARROW_SEP)
    print("RUBRIC:")
    print(RUBRIC)
    print()


def print_distribution(labeled: list[dict]) -> None:
    counts = Counter(p["human_label"] for p in labeled)
    dist = ", ".join(f"{i}={counts.get(i, 0)}" for i in range(5))
    print(f"Labeled {len(labeled)} / 50 so far. Distribution: {dist}")


def main(dry_run: bool = False) -> None:
    similarities = load_similarities()
    signals = load_signals()
    portfolio_path = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"
    systems = {s.id: s for s in load_portfolio(portfolio_path)}
    cosine_lookup = build_cosine_lookup(similarities)

    if dry_run:
        selected = select_eval_pairs(similarities)
        pair_list = [
            {
                "signal_id": sig_id,
                "system_id": sys_id,
                "cosine_similarity": cosine_lookup[(sig_id, sys_id)],
                "skipped": False,
            }
            for sig_id, sys_id in selected
        ]
        for i, pair_info in enumerate(pair_list[:2], start=1):
            render_pair(pair_info, signals, systems, i, len(pair_list))
            print("[DRY RUN — no input collected, nothing saved]")
        return

    # Load or create the selected pair list
    pairs_to_label = load_pairs_to_label()
    if not pairs_to_label:
        selected = select_eval_pairs(similarities)
        pairs_to_label = [
            {
                "signal_id": sig_id,
                "system_id": sys_id,
                "cosine_similarity": cosine_lookup[(sig_id, sys_id)],
                "skipped": False,
            }
            for sig_id, sys_id in selected
        ]
        save_pairs_to_label(pairs_to_label)

    labeled = load_labeled_pairs()
    labeled_keys = {(p["signal_id"], p["system_id"]) for p in labeled}
    total = len(pairs_to_label)
    n_done = len(labeled) + sum(1 for p in pairs_to_label if p.get("skipped"))

    print(f"\n{WIDE_SEP}")
    print(f"Ready to label. {total} pairs queued, {n_done} already done.")
    print("Estimated time: ~60-90 minutes for all 50, you can stop and resume any time.")
    print(WIDE_SEP)

    remaining = [
        (i + 1, p)
        for i, p in enumerate(pairs_to_label)
        if not p.get("skipped") and (p["signal_id"], p["system_id"]) not in labeled_keys
    ]

    if not remaining:
        print("\nAll pairs labeled! Final distribution:")
        print_distribution(labeled)
        return

    # session_labeled tracks pairs labeled in this session, in order, for 'b' navigation.
    session_labeled: list[tuple[int, dict]] = []

    try:
        idx = 0
        while idx < len(remaining):
            pair_number, pair_info = remaining[idx]
            render_pair(pair_info, signals, systems, pair_number, total)

            while True:
                raw = input(
                    "Score (0-4, 's' to skip, 'b' to revisit previous, 'q' to quit and save): "
                ).strip().lower()

                if raw == "q":
                    print(f"\nSaved progress. {len(labeled)} pairs labeled.")
                    print("Rerun the script to continue.")
                    return

                if raw == "b":
                    if not session_labeled:
                        print("No previous pair to revisit.")
                        continue
                    labeled = do_back_navigation(session_labeled, labeled, signals, systems, total)
                    # Re-display the current forward pair before re-prompting.
                    render_pair(pair_info, signals, systems, pair_number, total)
                    continue

                if raw == "s":
                    for p in pairs_to_label:
                        if p["signal_id"] == pair_info["signal_id"] and p["system_id"] == pair_info["system_id"]:
                            p["skipped"] = True
                    save_pairs_to_label(pairs_to_label)
                    break

                if raw in ("0", "1", "2", "3", "4"):
                    note = input("Note (optional, press Enter to skip): ").strip()
                    entry = LabeledPair(
                        signal_id=pair_info["signal_id"],
                        system_id=pair_info["system_id"],
                        cosine_similarity=pair_info["cosine_similarity"],
                        human_label=int(raw),
                        human_note=note,
                        labeled_at=datetime.now(tz=timezone.utc),
                    )
                    labeled = append_labeled_pair(entry, labeled)
                    labeled_keys.add((pair_info["signal_id"], pair_info["system_id"]))
                    session_labeled.append((pair_number, pair_info))
                    print()
                    print_distribution(labeled)
                    break

                print("Invalid input. Enter 0-4, 's' to skip, 'b' to revisit previous, or 'q' to quit.")

            idx += 1

    except KeyboardInterrupt:
        print("\n\nSaved progress, you can resume by re-running the script.")
        return

    if all(
        p.get("skipped") or (p["signal_id"], p["system_id"]) in labeled_keys
        for p in pairs_to_label
    ):
        print(f"\n{WIDE_SEP}")
        print("All pairs done! Final distribution:")
        print_distribution(labeled)
        print(WIDE_SEP)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive labeling tool for the eval set.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the first 2 pairs to the terminal without prompting or saving.",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
