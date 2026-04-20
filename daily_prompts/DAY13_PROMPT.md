# Claude Code prompt — Day 13: LangGraph refactor of the scorer (optional)

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 13. Then read the LangGraph quickstart documentation (the official LangGraph Python docs). In your own words, give me a 3-4 sentence summary of what we're refactoring, what the graph looks like, and what the self-check node does. Do not skip this step.

Once I confirm the summary, your task for Day 13 is to refactor the LLM scorer from a plain Python function into a small LangGraph graph. The goal is interview signal: "I built the agent loop from scratch first, then refactored the orchestration into LangGraph to compare the two approaches."

**Hard prerequisite:** Day 12 must be fully complete before starting this day. If the CDK stack is not deployed, stop and finish Day 12 first. If the interview is within a week, skip this day entirely.

## Prerequisites

Confirm these exist before starting:
- A working pipeline with the from-scratch scorer in `src/scoring.py`
- Day 12 complete (CDK stack deployed)
- `data/eval/metrics_llm_judge_v2.json` exists (so we can compare pre/post refactor)

## What to build

1. **Add `langgraph` to `requirements.txt`.** This is the only new dependency.

2. **Refactor `src/scoring.py`** to implement the scorer as a LangGraph graph with two nodes:

   a. **`score` node.** This is the existing `score_pair` logic wrapped as a LangGraph node. It calls Bedrock (or the fallback client), produces the structured `LLMScoreOutput`, and writes it to the graph state. The prompt, rubric, model, and tool-use pattern are unchanged from the from-scratch version.

   b. **`self_check` node.** A new node that re-reads the score and reasoning from the graph state and flags low-confidence cases for human review. Flag conditions:
      - Score of 2 with justification shorter than 30 words (ambiguous middle-ground with thin reasoning)
      - Score of 4 with reasoning shorter than 50 words (urgent flag needs strong justification)
      - Score of 3 or 4 where the reasoning doesn't mention any specific attribute of the system (generic reasoning that could apply to any system)

      The self-check node does NOT call the LLM again. It's a deterministic rule-based check on the LLM's output. It sets a `confidence_flag` field on the output.

3. **Define the graph state** as a TypedDict or Pydantic model containing:
   - `system: AISystem`
   - `signal: Signal`
   - `score_output: LLMScoreOutput | None`
   - `confidence_flag: str` (one of: `"ok"`, `"low_confidence"`, `"needs_review"`)
   - `flag_reason: str` (empty if confidence is ok, otherwise a short explanation)

4. **Wire the graph:** `score` -> `self_check` -> END. No conditional edges, no loops, no retries within the graph. Keep it simple. The graph is a two-step sequence, not a complex DAG.

5. **Add `confidence_flag` and `flag_reason` fields to `ScoredPair` in `src/schemas.py`.** Make them optional with defaults (`confidence_flag: str = "ok"`, `flag_reason: str = ""`) so existing scored pairs without these fields still validate.

6. **Update `src/pipeline.py`** to use the new LangGraph-based scorer. The pipeline should call the graph instead of calling `score_pair` directly. The interface from the pipeline's perspective should be the same: give it a system and signal, get back a scored pair.

7. **Update the dashboard** to show the confidence flag where present:
   - In the pair row rendering (`app/components.py`), if `confidence_flag` is `"low_confidence"` or `"needs_review"`, show a small indicator next to the score badge (e.g., a yellow dot or a "⚠" character)
   - In the pair detail expander, show the flag reason if present
   - If confidence_flag is `"ok"` or missing, show nothing extra

8. **Run the full pipeline** with the LangGraph scorer and verify it produces valid output.

9. **Run the eval** on the refactored scorer and compare metrics against the pre-refactor v2 metrics. The scores should be identical or nearly identical (the prompt hasn't changed, only the orchestration). If metrics diverge significantly, something is wrong with the refactor.

10. **Update `DECISIONS.md`** with an entry explaining:
    - Why the refactor (JD mentions agent frameworks, this demonstrates hands-on LangGraph experience)
    - What LangGraph gave us that the raw SDK didn't (the self-check node as a composable, inspectable step; the graph structure as documentation of the agent's decision flow)
    - What it cost (added dependency, slightly more complex code for a simple two-node graph)
    - Honest assessment: for a two-node graph, LangGraph is arguably overkill. The value is in showing familiarity with the framework and having a structure that could grow (e.g., adding a retry node, a routing node for different model tiers, etc.)

11. **Update the README:**
    - Tech stack section: add LangGraph
    - Architecture section: mention the self-check node
    - Add a short paragraph in the "Why I built it" or architecture section about the comparison story: built from scratch first, then refactored into LangGraph

## Implementation notes

- **Preserve the from-scratch version.** Keep the original `score_pair` function in `src/scoring.py` (rename it to `score_pair_raw` or similar) so the comparison story is visible in the code. The LangGraph version wraps it, it doesn't replace it.

- **The self-check is deterministic.** No LLM calls in the self-check node. It's pattern matching on the LLM's output. This keeps the cost identical to the from-scratch version.

- **Graph compilation.** Compile the graph once at module level (not per-call). The compiled graph is reusable.

- **Error handling.** If the score node fails (API error after retries), the graph should propagate the error. Don't add a fallback node or a retry loop within the graph. The existing retry wrapper inside `score_pair` handles transient failures.

- **Type hints, logging, comments.** Same conventions. The LangGraph code should be readable to someone who knows Python and has read the LangGraph docs but hasn't used it before.

## Definition of done

- The pipeline runs end-to-end through the LangGraph-based scorer
- `data/outputs/digest.json` is populated with scored pairs that include confidence flags
- The eval produces metrics comparable to the pre-refactor v2 (no regression)
- The dashboard shows confidence flags where present
- `DECISIONS.md` has the LangGraph rationale entry
- The README reflects the refactor
- The from-scratch `score_pair` function is still in the codebase for reference

## Scope guardrails

- **Do not** add more than two nodes to the graph. Score and self-check. That's it.
- **Do not** add conditional routing, loops, or human-in-the-loop nodes. Keep the graph linear.
- **Do not** change the scoring prompt, the rubric, or the eval set
- **Do not** add a new LLM call in the self-check node
- **Do not** add LangSmith, LangChain, or any other LangChain ecosystem dependency beyond `langgraph` itself
- **Do not** modify the baseline classifier or the eval metrics
- **Do not** start stretch additions on this day

## Skills to load

None new. The `llm-judge-scoring` and `structured-outputs-anthropic` skills from Day 3 still apply to the score node's internals, but the LangGraph wrapping is new territory. Read the official LangGraph Python quickstart before starting.

When you're done, give me a short summary of: (1) the graph structure (nodes and edges), (2) the self-check flag conditions and how many pairs got flagged in the full run, (3) the pre-vs-post refactor metric comparison, (4) what you added to DECISIONS.md, and (5) any concerns about stretch additions.
