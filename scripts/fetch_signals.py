from __future__ import annotations

import logging
import sys
from pathlib import Path

# Allow running as `python scripts/fetch_signals.py` from the project root.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import fetch_aiid_signals

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

OUTPUT_PATH = PROJECT_ROOT / "data" / "signals" / "processed" / "aiid_signals.json"


if __name__ == "__main__":
    print("Fetching signals from AI Incident Database...")
    signals = fetch_aiid_signals(OUTPUT_PATH, max_signals=60)
    print(f"\nSaved {len(signals)} signals to {OUTPUT_PATH}")
    print("\nSample signals:")
    for s in signals[:3]:
        print(f"  [{s.id}] {s.date} — {s.title[:70]}")
        print(f"    Tags: {s.tags[:3]}")
