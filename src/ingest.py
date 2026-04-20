from __future__ import annotations

import json
import logging
import ssl
import urllib.request
from pathlib import Path

import certifi

from src.schemas import Signal

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent

# Public Algolia credentials from the AIID repo's .env.example — search-only, read-safe.
_ALGOLIA_APP_ID = "JD5JCVZEVS"
_ALGOLIA_SEARCH_KEY = "c5e99d93261645721a1765fe4414389c"
_ALGOLIA_INDEX = "instant_search"
_ALGOLIA_URL = (
    f"https://{_ALGOLIA_APP_ID}-dsn.algolia.net"
    f"/1/indexes/{_ALGOLIA_INDEX}/query"
)

# Attributes we actually need — avoids pulling the full text of every news article.
_ATTRIBUTES = [
    "incident_id",
    "title",
    "description",
    "incident_date",
    "url",
    "classifications",
    "language",
]


def load_signals_from_json(path: Path) -> list[Signal]:
    """Read a JSON array of signals from disk and validate against the Signal schema."""
    with open(path) as f:
        raw = json.load(f)
    return [Signal.model_validate(item) for item in raw]


def load_all_signals() -> list[Signal]:
    """Load and combine all signal sources: AIID incidents + hand-curated governance signals.

    This is the canonical loader for pipeline runs. Use load_signals_from_json
    directly only when you need a single source (e.g., during ingestion / testing).
    """
    aiid_path = PROJECT_ROOT / "data" / "signals" / "processed" / "aiid_signals.json"
    gov_path = PROJECT_ROOT / "data" / "signals" / "processed" / "governance_signals.json"

    aiid_signals = load_signals_from_json(aiid_path)
    gov_signals = load_signals_from_json(gov_path)

    logger.info(
        "Loaded %d AIID signals + %d governance signals = %d total",
        len(aiid_signals), len(gov_signals), len(aiid_signals) + len(gov_signals),
    )
    return aiid_signals + gov_signals


def fetch_aiid_signals(output_path: Path, max_signals: int = 60) -> list[Signal]:
    """
    Fetch incidents from the AI Incident Database via the public Algolia index,
    normalize them to Signal objects, and write to output_path as JSON.

    The AIID's GraphQL API is origin-restricted, but their Algolia search key is
    publicly distributed in the repo's .env.example for client-side use. We fetch
    report-level records and deduplicate by incident_id to get one Signal per incident.

    Args:
        output_path: Where to write the JSON array of signals.
        max_signals: Max number of unique incidents to return (default 60).

    Returns:
        List of Signal objects that were written to disk.
    """
    seen_incident_ids: set[int] = set()
    candidates: list[dict] = []

    # Fetch pages until we have enough unique incidents.
    # 100 hits/page typically yields ~60 unique incidents per page, so page 0 is enough.
    page = 0
    while len(seen_incident_ids) < max_signals:
        payload = json.dumps({
            "query": "",
            "hitsPerPage": 100,
            "page": page,
            "attributesToRetrieve": _ATTRIBUTES,
        }).encode()

        req = urllib.request.Request(
            _ALGOLIA_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Algolia-Application-Id": _ALGOLIA_APP_ID,
                "X-Algolia-API-Key": _ALGOLIA_SEARCH_KEY,
            },
            method="POST",
        )

        # macOS Python 3.13 doesn't ship root certs — use certifi's bundle.
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, context=ssl_ctx) as resp:
            data = json.loads(resp.read())

        hits = data.get("hits")
        nb_pages = data.get("nbPages", 0)

        if hits is None:
            # Unexpected response — stop immediately so the caller can investigate.
            raise RuntimeError(
                f"Unexpected Algolia response shape on page {page}. "
                f"Expected 'hits' key. Got keys: {list(data.keys())}. "
                f"Full response (truncated): {str(data)[:500]}"
            )

        if not hits:
            logger.info("No more hits at page %d, stopping.", page)
            break

        for hit in hits:
            iid = hit.get("incident_id")
            if iid is None or hit.get("language") != "en":
                continue
            if iid in seen_incident_ids:
                continue
            desc = hit.get("description", "")
            if not desc or len(desc) < 30:
                continue
            seen_incident_ids.add(iid)
            candidates.append(hit)
            if len(seen_incident_ids) >= max_signals:
                break

        logger.info(
            "Page %d processed — %d unique incidents collected so far.",
            page,
            len(seen_incident_ids),
        )

        page += 1
        if page >= nb_pages:
            break

    signals = [_normalize(h) for h in candidates]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump([s.model_dump() for s in signals], f, indent=2)

    logger.info("Saved %d signals to %s.", len(signals), output_path)
    return signals


def _normalize(hit: dict) -> Signal:
    """Map an Algolia hit (report-level) to a Signal (incident-level)."""
    iid = hit["incident_id"]
    # Extract human-readable tags from CSET classification strings like "CSET:Sector:Finance"
    tags = _extract_tags(hit.get("classifications", []))

    return Signal(
        id=f"aiid-{iid}",
        title=hit.get("title", "").strip(),
        description=hit.get("description", "").strip(),
        date=hit.get("incident_date", ""),
        source="AI Incident Database",
        source_url=f"https://incidentdatabase.ai/cite/{iid}",
        tags=tags,
    )


def _extract_tags(classifications: list[str]) -> list[str]:
    """
    Pull meaningful values from CSET classification strings.
    Format is "CSET:<category>:<value>" — we skip boolean-looking values and blanks.
    """
    tags = []
    skip_values = {"true", "false", "unclear", "unclear/unknown", ""}
    for c in classifications:
        parts = c.split(":", 2)
        if len(parts) == 3:
            value = parts[2].strip().lower()
            if value not in skip_values:
                tags.append(parts[2].strip())
    return tags
