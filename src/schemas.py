from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AISystem(BaseModel):
    id: str
    name: str
    purpose: str
    model_type: str
    data_inputs: list[str]
    users: list[str]
    deployment_context: str
    known_risks: list[str]


class Signal(BaseModel):
    id: str
    title: str
    description: str
    date: str  # ISO 8601
    source: str
    source_url: str
    tags: list[str]
    # Full article text (AIID only). Empty string for governance signals and
    # legacy records. Used in the labeling UI; not used by the retriever.
    full_text: str = ""
    # Incident-level curator description from the AIID GraphQL API (AIID only).
    # More authoritative than the Algolia article description; used in labeling UI.
    incident_description: str = ""


class SimilarityPair(BaseModel):
    signal_id: str
    system_id: str
    cosine_similarity: float


class LLMScoreOutput(BaseModel):
    """Structured output the LLM fills via tool use. Field order is deliberate:
    reasoning first forces the model to think before committing to a score."""

    reasoning: str = Field(
        description=(
            "Step-by-step analysis of how the signal relates to this AI system. "
            "Must reference at least one specific detail from the signal and one "
            "specific detail from the system card. 2-4 sentences."
        )
    )
    score: int = Field(
        ge=0,
        le=4,
        description=(
            "Relevance score per the rubric: 0=Unrelated, 1=Tangential, "
            "2=Worth a glance, 3=Action recommended, 4=Urgent review."
        ),
    )
    justification: str = Field(
        description="1-2 sentence justification for the score, written for a model owner audience."
    )
    suggested_action: str = Field(
        description=(
            "Specific next action the model owner should take. Must name what to do, "
            "not just 'review this signal'. Example: 'Review your fraud model's "
            "threshold calibration given this incident involving similar demographic proxies.'"
        )
    )


class ScoredPair(BaseModel):
    signal_id: str
    system_id: str
    cosine_similarity: float
    # 0-4 per the relevance rubric in CLAUDE.md
    relevance_score: int = Field(ge=0, le=4)
    justification: str
    suggested_action: str
    reasoning: str


# ---------------------------------------------------------------------------
# Digest — the API contract between the pipeline and the dashboard.
# Any schema change here requires updating both the pipeline (producer)
# and the Streamlit app (consumer). Treat it like a versioned interface.
# ---------------------------------------------------------------------------

class RunMetadata(BaseModel):
    run_timestamp: datetime
    model_name: str
    retrieval_threshold: float
    num_signals: int
    num_systems: int
    num_pairs_after_retrieval: int
    num_pairs_scored: int
    num_pairs_failed: int
    elapsed_seconds: float
    # Aggregated observability fields (default 0 for backwards compat with older digest files)
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_estimated_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0


class Digest(BaseModel):
    metadata: RunMetadata
    systems: list[AISystem]
    signals: list[Signal]
    scored_pairs: list[ScoredPair]


class CallMetadata(BaseModel):
    """Per-LLM-call observability record. Written to run_metadata.json, not digest.json."""

    signal_id: str
    system_id: str
    model_id: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    estimated_cost_usd: float
    timestamp: str  # ISO 8601


class RunReport(BaseModel):
    """Full observability report written to data/outputs/run_metadata.json.

    Separates per-call details from digest.json to keep the digest clean.
    The dashboard reads run_metadata.json for the observability tab.
    """

    metadata: RunMetadata
    call_metadata: list[CallMetadata]


class LabeledPair(BaseModel):
    signal_id: str
    system_id: str
    cosine_similarity: float
    human_label: int = Field(..., ge=0, le=4)
    human_note: str = ""
    labeled_at: datetime
