# Claude Code prompt — Day 3: LLM scorer (the agent core)

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 3. Then **load the `llm-judge-scoring` and `structured-outputs-anthropic` skills** by reading both `SKILL.md` files in full. Both skills apply heavily today and you should not start coding until you have read them.

After reading those, in your own words, give me a 4-5 sentence summary of what we're building today, how it uses the rubric, and which patterns from the two skills you'll be applying. Do not skip this step. This is the most important day of Week 1 and I want to confirm you have the right mental model before any code is written.

Once I confirm the summary, your task for Day 3 is to build the LLM-as-judge scorer. This is the agent core. It takes a (signal, system) pair plus the rubric and returns a structured score with reasoning, justification, and suggested action.

## What to build

1. **Add the `LLMScoreOutput` schema to `src/schemas.py`.** This is the Pydantic model the LLM fills via tool use. Follow the field-order rules from the `structured-outputs-anthropic` skill (reasoning first, then score, then justification, then action). Use `Field(..., ge=0, le=4, description="...")` to constrain the score. Every field gets a description.

2. **Build `src/scoring.py`** with the following structure:

   a. **A module-level constant `RELEVANCE_RUBRIC`** that contains the full rubric from `CLAUDE.md` verbatim. This is the single source of truth for the rubric in code. It must match `CLAUDE.md` exactly. If it ever drifts, that's a bug.

   b. **A module-level constant `BEDROCK_MODEL_ID`** set to `"us.anthropic.claude-haiku-4-5-v1"`. Also define `ANTHROPIC_MODEL_NAME = "claude-haiku-4-5"` for the fallback path. Make it easy to swap to Sonnet by changing one line.

   c. **A client factory function `get_llm_client()`** that reads `LLM_PROVIDER` from the environment (default: `"bedrock"`). If `"bedrock"`, return a `boto3` `bedrock-runtime` client. If `"anthropic"`, return an `Anthropic()` client. This is the only place in the codebase that branches on provider. See the `structured-outputs-anthropic` skill for the exact setup pattern.

   d. **A function `build_scoring_prompt(system: AISystem, signal: Signal) -> str`** that constructs the prompt. The prompt has the six sections from the `llm-judge-scoring` skill: role and task, the rubric verbatim, the asymmetric error costs reminder, the system card, the signal, and the output instructions. Each section is clearly delimited with a header. Use a multi-line f-string or template -- keep it readable.

   e. **A function `score_pair(system: AISystem, signal: Signal, client) -> LLMScoreOutput`** that calls the API using the tool-use-with-Pydantic pattern from the `structured-outputs-anthropic` skill. The `client` parameter is whatever `get_llm_client()` returned. If it's a boto3 client, use the Converse API with `toolConfig` and `toolChoice`. If it's an Anthropic client, use the direct SDK's `tools` and `tool_choice`. Force the model to use the tool. Parse the response into the Pydantic model. Temperature 0. Max tokens around 1024 (enough for reasoning + the structured fields). The `structured-outputs-anthropic` skill has code examples for both paths.

   f. **A retry wrapper** as described in the `structured-outputs-anthropic` skill: 3 attempts, exponential backoff, only retry on transport errors (`ClientError`, `ConnectionError`, `TimeoutError` for Bedrock; `APIError` for direct SDK), fail loudly on schema validation errors. Do not invent your own retry logic -- follow the skill's pattern exactly.

3. **Build `scripts/run_scoring.py`** as a CLI script that:
   - Loads the portfolio from `data/portfolio/systems.yaml`
   - Loads the signals from `data/signals/processed/aiid_signals.json`
   - Loads the similarities from `data/outputs/similarities.json`
   - Filters the similarity pairs to candidates: keep all pairs where `cosine_similarity >= 0.3` OR (per system) the top 8 highest-similarity signals, whichever produces more. The reason for the OR: if a system has nothing above 0.3, we still want to score its top candidates so we don't end up with zero-coverage systems.
   - For each candidate pair, calls `score_pair`
   - Logs progress as it goes (every 10 pairs: how many done, how many remaining, elapsed time)
   - Combines the LLM output with the cosine similarity into a `ScoredPair` (the schema from Day 1)
   - Writes results to `data/outputs/scored_pairs.json`
   - Logs a summary at the end: pairs scored, score distribution (count of 0s, 1s, 2s, 3s, 4s), total cost estimate if you can compute it from the response usage fields

4. **Add a `--limit N` CLI flag** to the script so you can run on a small subset (e.g. 5 pairs) for testing without burning API credits. Default is no limit.

5. **Sanity-check the output.** After the script runs on the full set, dump 5 scored pairs to the console (pick a mix: highest score, lowest score, and three random middle ones). Read them yourself before reporting back. The reasoning should make sense, the score should match the reasoning, and the suggested action should be specific to the pair, not generic. If any of those things fail, that's a failure mode from the `llm-judge-scoring` skill and you should diagnose it before declaring done.

## Implementation notes

- **The rubric copy in code must match `CLAUDE.md` exactly.** If you find a discrepancy, stop and ask. Do not silently fix one or the other.

- **Environment variables.** Load `.env` via `python-dotenv` at the top of `scripts/run_scoring.py`. The `LLM_PROVIDER` env var controls which client is used (default: `bedrock`). For Bedrock, AWS credentials resolve via the standard boto3 chain (`AWS_PROFILE`, env vars, IAM role). For the direct SDK fallback, `ANTHROPIC_API_KEY` is read from the environment.

- **Cost awareness.** With ~50 signals and 6-8 systems and the candidate filter, you should end up scoring something like 80-150 pairs. At Haiku prices that's pennies, but include a small "this will run N pairs, costing approximately $X, continue? [y/N]" prompt before the actual scoring loop runs. Skip the prompt if `--yes` flag is passed, so it can run unattended.

- **Logging:** Configure the root logger at the top of `scripts/run_scoring.py`. Log each API call's outcome (success, retry, fail). Don't log the full prompt or response, just summary info (pair ids, score, time taken).

- **Don't catch and swallow errors.** If a single pair fails after retries, log it loudly and continue with the rest. At the end, summarize how many pairs failed. Do not silently drop them.

## Definition of done

- `python scripts/run_scoring.py --limit 5` runs without errors and produces 5 scored pairs that look qualitatively reasonable
- Then `python scripts/run_scoring.py` runs the full set without errors
- `data/outputs/scored_pairs.json` exists and validates against the `ScoredPair` schema
- The score distribution is not pathological (not all 2s, not all 0s)
- Sanity check: 5 manually-read pairs have coherent reasoning, matching scores, and specific suggested actions
- The retry logic is in place but you have not had to invoke it manually

## Scope guardrails

- **Do not** modify the rubric. It is locked. If something about the rubric feels wrong, note it and ask, do not change it.
- **Do not** add any new dimensions to the score (no separate severity, no urgency timeline, nothing). The output schema is exactly: reasoning, score, justification, suggested_action.
- **Do not** add any caching of LLM responses. Re-running should produce fresh API calls.
- **Do not** start building the pipeline orchestration (Day 4) or the dashboard (Day 5).
- **Do not** call the API outside of the `score_pair` function. One function, one entry point.
- **Do not** parse responses with regex or string splitting. Use the Pydantic model. If parsing fails, the prompt is wrong and needs to be fixed, not worked around.

## Skills to load

- `llm-judge-scoring` — apply the rubric embedding rule, the reason-before-score field order, the temperature rule, and the failure mode list.
- `structured-outputs-anthropic` — apply the tool use pattern, the schema design rules, and the error handling rules exactly.

When you're done, give me a short summary of: (1) what you built, (2) any decisions you made that weren't in this prompt, (3) the score distribution from the full run, (4) the 5 sanity-check pairs you read, and (5) any concerns about Day 4. If any of the sanity-check pairs looked broken, do not say "done" — diagnose using the failure mode list in `llm-judge-scoring` and report what you found.
