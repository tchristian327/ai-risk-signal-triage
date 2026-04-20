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


class Digest(BaseModel):
    metadata: RunMetadata
    systems: list[AISystem]
    signals: list[Signal]
    scored_pairs: list[ScoredPair]
