# Structured Outputs via AWS Bedrock (Converse API)

Patterns for getting reliable typed output from Claude on AWS Bedrock using Pydantic and the Converse API's native tool use. Apply whenever writing code that calls Claude and expects a structured response.

## Client setup

The project supports two LLM providers controlled by the `LLM_PROVIDER` environment variable (default: `bedrock`). The client factory abstracts this so scoring code never branches on provider.

### Bedrock (primary)

```python
import boto3
import json
import os

def get_bedrock_client():
    """Build a bedrock-runtime client using env-based config."""
    return boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
```

AWS credentials resolve via the standard boto3 chain: `AWS_PROFILE`, env vars (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`), IAM role, etc. Never hardcode credentials.

### Direct Anthropic SDK (local fallback)

```python
from anthropic import Anthropic

def get_anthropic_client():
    """Fallback for local dev when Bedrock access is pending."""
    return Anthropic()  # reads ANTHROPIC_API_KEY from env
```

### Model ID format

Bedrock model IDs differ from direct SDK model names:

| Direct SDK | Bedrock model ID |
|---|---|
| `claude-haiku-4-5` | `us.anthropic.claude-haiku-4-5-v1` |
| `claude-sonnet-4-5` | `us.anthropic.claude-sonnet-4-5-v1` |

Store the Bedrock model ID as a module-level constant. When using the direct SDK fallback, map it back to the short name.

## Tool use pattern with Converse API

The Converse API supports tool use natively with the same conceptual shape as the direct Anthropic SDK. The differences are in the request/response envelope, not the tool definition or message structure.

### Defining the tool from a Pydantic model

```python
from pydantic import BaseModel, Field

class LLMScoreOutput(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning about relevance before committing to a score.")
    score: int = Field(ge=0, le=4, description="Relevance score per the rubric (0-4).")
    justification: str = Field(description="1-2 sentence justification for the score.")
    action: str = Field(description="Suggested next action for the model owner.")

def pydantic_to_converse_tool(model_class: type[BaseModel], tool_name: str) -> dict:
    """Convert a Pydantic model to a Converse API toolSpec."""
    schema = model_class.model_json_schema()
    # Remove $defs and other JSON Schema extras Converse doesn't expect
    schema.pop("$defs", None)
    schema.pop("title", None)
    return {
        "toolSpec": {
            "name": tool_name,
            "description": f"Record the structured output for {tool_name}.",
            "inputSchema": {"json": schema},
        }
    }
```

### Making the call (Bedrock Converse)

```python
def score_pair_bedrock(client, model_id: str, prompt: str, tool: dict) -> LLMScoreOutput:
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        toolConfig={
            "tools": [tool],
            "toolChoice": {"tool": {"name": tool["toolSpec"]["name"]}},
        },
        inferenceConfig={"temperature": 0.0, "maxTokens": 1024},
    )

    # Extract tool use result from the response
    for block in response["output"]["message"]["content"]:
        if "toolUse" in block:
            return LLMScoreOutput.model_validate(block["toolUse"]["input"])

    raise ValueError("Model did not return a tool use block.")
```

### Making the call (direct SDK fallback)

```python
def score_pair_anthropic(client, model_name: str, prompt: str, tool_schema: dict) -> LLMScoreOutput:
    response = client.messages.create(
        model=model_name,
        max_tokens=1024,
        temperature=0,
        tools=[{
            "name": tool_schema["toolSpec"]["name"],
            "description": tool_schema["toolSpec"]["description"],
            "input_schema": tool_schema["toolSpec"]["inputSchema"]["json"],
        }],
        tool_choice={"type": "tool", "name": tool_schema["toolSpec"]["name"]},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use":
            return LLMScoreOutput.model_validate(block.input)

    raise ValueError("Model did not return a tool use block.")
```

### Note on invoke_model

`invoke_model` is the lower-level Bedrock API. It works but requires manually constructing the Anthropic messages JSON body and parsing the raw response. Converse is preferred for anything involving tool use or structured output because it handles the tool protocol natively.

## Schema design rules

1. **Field order matters for reasoning quality.** Put `reasoning` first so the model thinks before committing to a score. The model fills fields in order.
2. **Every field gets a `description`.** The description is the model's instruction for that field. Vague descriptions produce vague output.
3. **Constrain numeric fields.** Use `ge=0, le=4` on score fields. The Converse API enforces the JSON Schema constraints.
4. **Keep the schema flat.** Nested objects add parse complexity with no quality gain for this use case.

## Error handling

```python
import time
from botocore.exceptions import ClientError

def score_with_retry(call_fn, max_attempts=3):
    """Retry on transient errors only. Fail loudly on schema validation."""
    for attempt in range(max_attempts):
        try:
            return call_fn()
        except (ClientError, ConnectionError, TimeoutError) as e:
            if attempt == max_attempts - 1:
                raise
            wait = 2 ** attempt
            logging.warning("Transient error (attempt %d/%d), retrying in %ds: %s",
                          attempt + 1, max_attempts, wait, e)
            time.sleep(wait)
        except (ValueError, ValidationError):
            # Schema validation failure = prompt is wrong, not a transient issue.
            raise
```

Key rules:
- Only retry on transport/throttling errors (`ClientError`, `ConnectionError`, `TimeoutError`).
- Never retry on `ValidationError` (Pydantic) or `ValueError` (missing tool block). These mean the prompt or schema is broken and retrying will just burn credits.
- 3 attempts, exponential backoff (1s, 2s, 4s).
- Log every retry so the pipeline operator can see what happened.

## Extracting usage metadata

For observability (Day 11), extract token counts and latency from the Converse response:

```python
usage = response.get("usage", {})
tokens_in = usage.get("inputTokens", 0)
tokens_out = usage.get("outputTokens", 0)
# Latency: measure wall-clock time around the converse() call
```

The direct SDK equivalent uses `response.usage.input_tokens` and `response.usage.output_tokens`.
