from __future__ import annotations

import logging
import os
import time

from pydantic import ValidationError

from src.schemas import AISystem, LLMScoreOutput, Signal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model constants — change one line to switch to Sonnet
# ---------------------------------------------------------------------------
BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
ANTHROPIC_MODEL_NAME = "claude-haiku-4-5"

# ---------------------------------------------------------------------------
# Rubric — verbatim copy of the single source of truth in CLAUDE.md.
# If this ever drifts from CLAUDE.md, that is a bug.
# ---------------------------------------------------------------------------
RELEVANCE_RUBRIC = """
- **0 — Unrelated.** The signal has no meaningful connection to this system.
- **1 — Tangential.** The signal mentions a broadly related topic but has no direct implication for this system.
- **2 — Worth a glance.** The signal raises a concern that could apply to this system under some conditions. Model owner should be aware.
- **3 — Action recommended.** The signal describes a risk, incident, or regulatory change that plausibly affects this system. Model owner should review and decide whether to act.
- **4 — Urgent review.** The signal describes a risk, incident, or regulatory change with direct and immediate implications for this system. Model owner should review this week.
""".strip()


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def get_llm_client():
    """Return a Bedrock or Anthropic client based on LLM_PROVIDER env var.

    This is the only place in the codebase that branches on provider.
    """
    provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
    if provider == "bedrock":
        import boto3
        return boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
    elif provider == "anthropic":
        from anthropic import Anthropic
        return Anthropic()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Must be 'bedrock' or 'anthropic'.")


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_scoring_prompt(system: AISystem, signal: Signal) -> str:
    """Construct the six-section scoring prompt per the llm-judge-scoring skill."""
    system_card = f"""Name: {system.name}
Purpose: {system.purpose}
Model type: {system.model_type}
Data inputs: {", ".join(system.data_inputs)}
Users: {", ".join(system.users)}
Deployment context: {system.deployment_context}
Known risks: {"; ".join(system.known_risks)}"""

    signal_block = f"""Title: {signal.title}
Date: {signal.date}
Source: {signal.source}
URL: {signal.source_url}
Description: {signal.description}"""

    return f"""## Role and task

You are an AI risk analyst at an insurance company. Your job is to evaluate whether an external AI risk signal is relevant to a specific internal AI system in the company's portfolio. You will assign a relevance score from 0 to 4.

## Relevance rubric

Use this rubric exactly. Do not invent intermediate scores.

{RELEVANCE_RUBRIC}

## Asymmetric error costs

Missing a real risk (false negative) is more costly than flagging something irrelevant (false positive). When genuinely uncertain between two adjacent scores, prefer the higher one.

However: a score of 0 is correct and expected for many pairs. The candidate filter has already removed the obviously unrelated pairs, but many filtered candidates will still be 0 or 1. Keyword overlap alone does not indicate relevance — two systems can share a topic area without sharing the specific risk mechanism.

## System card

{system_card}

## Signal

{signal_block}

## Output instructions

Use the provided tool to record your response. Reason step by step before committing to a score. Your reasoning must reference at least one specific detail from the signal and one specific detail from the system card — generic reasoning like "both involve AI" is not sufficient. After reasoning, assign a score, write a 1-2 sentence justification, and suggest a specific next action for the model owner."""


# ---------------------------------------------------------------------------
# Tool spec builder
# ---------------------------------------------------------------------------

def _pydantic_to_converse_tool(model_class: type, tool_name: str) -> dict:
    """Convert a Pydantic model to a Converse API toolSpec."""
    schema = model_class.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("title", None)
    return {
        "toolSpec": {
            "name": tool_name,
            "description": "Record the structured scoring output.",
            "inputSchema": {"json": schema},
        }
    }


# ---------------------------------------------------------------------------
# Provider-specific call implementations
# ---------------------------------------------------------------------------

def _call_bedrock(client, prompt: str) -> LLMScoreOutput:
    tool = _pydantic_to_converse_tool(LLMScoreOutput, "record_score")
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        toolConfig={
            "tools": [tool],
            "toolChoice": {"tool": {"name": "record_score"}},
        },
        inferenceConfig={"temperature": 0.0, "maxTokens": 1024},
    )
    for block in response["output"]["message"]["content"]:
        if "toolUse" in block:
            return LLMScoreOutput.model_validate(block["toolUse"]["input"])
    raise ValueError("Bedrock response did not contain a tool use block.")


def _call_anthropic(client, prompt: str) -> LLMScoreOutput:
    tool = _pydantic_to_converse_tool(LLMScoreOutput, "record_score")
    response = client.messages.create(
        model=ANTHROPIC_MODEL_NAME,
        max_tokens=1024,
        temperature=0,
        tools=[{
            "name": tool["toolSpec"]["name"],
            "description": tool["toolSpec"]["description"],
            "input_schema": tool["toolSpec"]["inputSchema"]["json"],
        }],
        tool_choice={"type": "tool", "name": "record_score"},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return LLMScoreOutput.model_validate(block.input)
    raise ValueError("Anthropic response did not contain a tool use block.")


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

def _score_with_retry(call_fn, max_attempts: int = 3) -> LLMScoreOutput:
    """Retry on transient transport errors only. Fail loudly on schema errors."""
    # Import here to avoid hard dependency when provider is "anthropic"
    try:
        from botocore.exceptions import ClientError as BotoClientError
    except ImportError:
        BotoClientError = None  # type: ignore[assignment,misc]

    # Only retry on throttling / connection errors. ValidationException means the
    # request itself is malformed (bad model ID, bad schema) — retrying won't help.
    TRANSIENT_BOTO_CODES = {"ThrottlingException", "ServiceUnavailableException", "InternalServerError"}

    for attempt in range(max_attempts):
        try:
            return call_fn()
        except (ValidationError, ValueError):
            # Pydantic schema failure or missing tool block — prompt is broken, not transient.
            raise
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_attempts - 1:
                raise
            wait = 2 ** attempt
            logger.warning(
                "Transient error (attempt %d/%d), retrying in %ds: %s",
                attempt + 1, max_attempts, wait, e,
            )
            time.sleep(wait)
        except Exception as e:
            # For ClientError, only retry on known transient error codes.
            if BotoClientError is not None and isinstance(e, BotoClientError):
                code = e.response.get("Error", {}).get("Code", "")
                if code in TRANSIENT_BOTO_CODES and attempt < max_attempts - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Throttling/service error (attempt %d/%d), retrying in %ds: %s",
                        attempt + 1, max_attempts, wait, e,
                    )
                    time.sleep(wait)
                    continue
            raise

    # Should be unreachable, but satisfies type checkers
    raise RuntimeError("Exceeded max retry attempts.")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def score_pair(system: AISystem, signal: Signal, client) -> LLMScoreOutput:
    """Score a single (signal, system) pair using the LLM-as-judge rubric.

    The client parameter is whatever get_llm_client() returned. Provider
    detection is based on the client's type, not a global flag, so this
    function stays stateless and testable.
    """
    prompt = build_scoring_prompt(system, signal)

    # Detect provider by client type to avoid importing both SDKs unconditionally
    client_type = type(client).__name__

    if client_type == "BedrockRuntime":
        call_fn = lambda: _call_bedrock(client, prompt)
    else:
        # Anthropic client (or any non-Bedrock client in tests)
        call_fn = lambda: _call_anthropic(client, prompt)

    return _score_with_retry(call_fn)
