from __future__ import annotations

import sys
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
# Allow `python src/portfolio.py` from the project root.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.schemas import AISystem


def load_portfolio(path: Path) -> list[AISystem]:
    """Read systems.yaml, validate each entry against AISystem, return the list."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    systems = []
    for entry in raw["systems"]:
        systems.append(AISystem.model_validate(entry))
    return systems


if __name__ == "__main__":
    portfolio_path = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"
    systems = load_portfolio(portfolio_path)
    print(f"Loaded {len(systems)} AI systems:\n")
    for s in systems:
        print(f"  [{s.id}] {s.name} ({s.model_type})")
        print(f"    Purpose: {s.purpose[:80].strip()}...")
        print()
