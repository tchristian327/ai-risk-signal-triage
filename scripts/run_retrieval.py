from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import load_all_signals
from src.portfolio import load_portfolio
from src.retrieval import compute_similarities

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PORTFOLIO_PATH = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "outputs" / "similarities.json"

# LLM-based system used for the top-3 sanity check after each run
SANITY_CHECK_SYSTEM_ID = "customer_chatbot"


if __name__ == "__main__":
    start = time.time()

    systems = load_portfolio(PORTFOLIO_PATH)
    signals = load_all_signals()
    logger.info("Loaded %d systems, %d signals.", len(systems), len(signals))

    pairs = compute_similarities(systems, signals)

    # Sort by system_id then cosine_similarity descending — makes the JSON easy
    # to scan manually: all pairs for one system are together, best matches first.
    pairs_sorted = sorted(pairs, key=lambda p: (p.system_id, -p.cosine_similarity))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump([p.model_dump() for p in pairs_sorted], f, indent=2)

    elapsed = time.time() - start
    logger.info(
        "Done. %d systems x %d signals = %d pairs written to %s in %.1fs.",
        len(systems),
        len(signals),
        len(pairs),
        OUTPUT_PATH,
        elapsed,
    )

    # Sanity check: top-3 for an LLM system. We expect LLM-related incidents
    # (hallucination, chatbot failures, bias in language models) to score high.
    signal_lookup = {s.id: s for s in signals}
    llm_pairs = [p for p in pairs if p.system_id == SANITY_CHECK_SYSTEM_ID]
    llm_pairs.sort(key=lambda p: -p.cosine_similarity)
    logger.info("Top-3 pairs for '%s' (sanity check):", SANITY_CHECK_SYSTEM_ID)
    for pair in llm_pairs[:3]:
        sig = signal_lookup[pair.signal_id]
        logger.info(
            "  [%.4f] %s — %s",
            pair.cosine_similarity,
            pair.signal_id,
            sig.title[:70],
        )
