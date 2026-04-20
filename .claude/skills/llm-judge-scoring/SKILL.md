# LLM-as-Judge Scoring

Patterns for using an LLM to assign rubric-based scores. Apply whenever working on code that asks Claude to score, label, or classify something against a defined rubric.

## Prompt structure (six sections)

The scoring prompt must have exactly these six sections, in this order, each clearly delimited with a header or XML-style tags:

1. **Role and task.** Tell the model it is an AI risk analyst evaluating whether an external signal is relevant to a specific AI system. One sentence. Do not over-elaborate the persona.

2. **The rubric, verbatim.** Copy the full 0-4 rubric from `CLAUDE.md` into the prompt. Do not paraphrase, summarize, or reorder it. The rubric is the single source of truth. If the rubric in code ever drifts from `CLAUDE.md`, that is a bug.

3. **Asymmetric error costs.** Remind the model that false negatives (missing a real risk) are more costly than false positives (flagging something irrelevant). One sentence is enough. This nudges the model toward recall without making it score everything high.

4. **The system card.** The full text of the AI system being evaluated: name, purpose, model type, data inputs, users, deployment context, known risks. Structured as a block the model can reference.

5. **The signal.** Title, description, date, source, and URL of the external signal being evaluated.

6. **Output instructions.** Tell the model to use the provided tool to record its response. Remind it to reason step by step before committing to a score. Do not repeat the rubric here; just reference it.

## Reasoning before score

The Pydantic schema puts `reasoning` as the first field. This forces the model to write its chain of thought before it commits to a numeric score. This is not optional; it is the single most important quality lever. Without it, the model anchors on a number early and post-hoc rationalizes.

The reasoning field should contain 2-4 sentences analyzing the connection between the signal and the system. It should reference specific details from both (not just "the signal is about AI" and "the system uses AI").

## Temperature

Always 0 for scoring. Non-zero temperature introduces variance between runs, which makes eval results non-reproducible and makes v1-vs-v2 comparisons unreliable.

## Consistency checks

After a scoring run, check these:
- **Score distribution.** If >60% of scores are the same value, the prompt is likely too vague or the rubric boundaries are not landing. A healthy distribution on real data with a candidate filter should spread across 0-3, with 4s being rare.
- **Reasoning matches score.** Read 5-10 pairs manually. The reasoning should logically support the score. If the reasoning says "this is tangential" but the score is 3, the prompt's rubric section is not constraining the model.
- **Actions are specific.** The suggested action should name what the model owner should do, not just "review this signal." Good: "Review your chatbot's PII handling procedures given this data leak incident." Bad: "Consider the implications."

## Known failure modes

These are the patterns that cause LLM judges to produce bad scores. Check for them during eval (Day 7) and target them during prompt iteration (Day 9).

1. **Score inflation.** The model gives 2s and 3s to everything because the asymmetric error nudge is too strong. Fix: tighten the rubric boundary language in the prompt scaffolding (not the rubric itself). Add a sentence like "A score of 2 means the model owner should be aware but no action is needed. Reserve 3 for cases where you would genuinely recommend the model owner spend time investigating."

2. **Generic reasoning.** The model writes "this signal is about AI risk and this system uses AI, so they are related" without engaging with specifics. Fix: add an instruction in the output section like "Your reasoning must reference at least one specific detail from the signal and one specific detail from the system card."

3. **Anchoring on keywords.** The model sees "bias" in the signal and "fairness" in the system's known risks and scores high without checking whether the actual mechanism is relevant. Fix: add a sentence in the asymmetric error section like "Keyword overlap alone does not indicate relevance. Two systems can both involve bias but in completely unrelated ways."

4. **Reluctance to score 0.** The model finds tenuous connections to avoid giving a zero. Fix: add to the rubric section "A score of 0 is correct and expected for most (signal, system) pairs. The candidate filter has already removed the obviously unrelated pairs, but many filtered candidates will still be 0 or 1."

5. **Cross-contamination between pairs.** Not a concern with single-pair-per-call architecture (which this project uses), but would be a problem with batched scoring. Do not batch multiple pairs in a single API call.

## Cost awareness

With the candidate filter reducing the scoring set to ~80-150 pairs and Haiku pricing, a full scoring run costs well under $1. Include a cost estimate before the scoring loop runs (pair count times approximate cost per call) so the operator can sanity-check before committing. The `--yes` flag skips the confirmation for automated runs.

## Model selection

Default to Claude Haiku for cost efficiency during development and eval iteration. Haiku is fast, cheap, and good enough for rubric-following tasks. Switch to Sonnet only if eval results show Haiku consistently fails on nuanced cases that Sonnet handles better. Document the model choice and any switch in `DECISIONS.md`.
