# Evaluation Framework

Patterns for building the labeled eval set, computing metrics, comparing scoring systems, and doing error analysis. Apply whenever working on evaluation, labeling, or measurement.

## Building a defensible eval set

### Sampling strategy

Do not just evaluate the top-scored pairs. A biased eval set produces biased metrics. Use stratified sampling on cosine similarity to get a mix:
- ~1/3 high cosine similarity (the pairs the retriever thinks are relevant)
- ~1/3 medium cosine similarity (the borderline cases)
- ~1/3 low cosine similarity (the pairs the retriever thinks are irrelevant but the LLM might disagree)

This ensures the eval set covers the full difficulty range and tests both the retriever's filtering and the scorer's judgment.

### Target distribution

Aim for roughly:
- 12-15 pairs at score 0-1 (unrelated/tangential)
- 12-15 pairs at score 2 (worth a glance)
- 12-15 pairs at score 3 (action recommended)
- 8-10 pairs at score 4 (urgent review)

If real data doesn't naturally produce enough high-relevance pairs, note this as a finding rather than manufacturing them. A sparse 4-bucket is an honest result about the signal corpus, not a flaw in the eval design.

### Labeling principles

- One labeler is acceptable for a portfolio project. Note this limitation explicitly in the README.
- Label against the rubric, not against your gut. Re-read the rubric before each labeling session.
- Use the optional note field to capture uncertainty: "could be 2 or 3, leaning 2 because..."
- Save after every label. The labeling script should be crash-safe.
- Do not look at the LLM's scores before labeling. That contaminates the eval.

## Metrics

### The four metrics (and why these four)

1. **Exact match accuracy.** Fraction where LLM score equals human label. The bluntest measure. Useful as a sanity check but not the headline because off-by-one errors on a 5-point scale are often acceptable.

2. **Off-by-one accuracy.** Fraction where `abs(prediction - label) <= 1`. More forgiving and often more informative for a graded scale. If this is high but exact match is low, the model understands the rubric but disagrees on boundaries.

3. **Recall at score >= 3 (the headline metric).** Of all pairs the human labeled 3 or 4 (real risks), what fraction did the model also score 3 or 4? This is the most operationally important metric because of the asymmetric error costs: missing a real risk is worse than over-flagging. Report as both a percentage and a count ("17 of 20 caught") so the reader understands the denominator.

4. **Confusion matrix (5x5).** Rows = predicted, columns = human label. Shows the full picture: where the model agrees, where it over-scores, where it under-scores. The diagonal is correct; off-diagonal cells tell you the specific failure modes.

### Metrics we deliberately skip

No ROC, F1, Cohen's kappa, or regression metrics. They add complexity without adding insight for this use case. The four above are enough to tell the story and defend the system in an interview.

## Comparing systems

When comparing the LLM judge against the baseline classifier:

- Use the same eval set for both. Never compare metrics computed on different data.
- Show all metrics side by side in a single table. Readers should be able to scan one table, not flip between two.
- Highlight the winner of each metric, but do not declare an overall winner unless one system dominates across all metrics. Mixed results are a legitimate and often more interesting finding.
- Include latency and cost as comparison dimensions. The baseline is free and fast; the LLM judge costs money and is slow. If they're close on accuracy, the baseline's cost advantage matters.

## Error analysis

After computing metrics, identify the "really wrong" pairs: `abs(prediction - label) >= 2`. For each:

- Show the signal title, system name, human label, LLM prediction, the LLM's reasoning, and the human note
- Sort by absolute error descending
- Look for patterns: Is the model consistently over-scoring a certain type of signal? Under-scoring cross-domain analogies? Confused by legal language?

The error analysis drives Day 9's prompt iteration. Each prompt change on Day 9 should target a specific pattern found here.

## The honest-eval principle

Report what you find, not what you want to find. Specific rules:

- If the baseline classifier beats the LLM judge on some metric, say so. "The baseline wins on consistency" is a better interview talking point than hiding the result.
- If a prompt change on Day 9 makes recall worse, document the regression. Do not cherry-pick metrics that improved.
- The eval set is small (50 pairs). Acknowledge this. Do not claim statistical significance. Say "on this eval set" rather than "the system achieves."
- If the LLM judge and the baseline are close, that is a finding worth reporting, not a failure. "With only 50 labeled pairs, a logistic regression on embeddings is competitive with an LLM judge" is a real insight about the data regime.

## File conventions

All eval artifacts go in `data/eval/`:
- `labeled_pairs.json` -- the hand-labeled eval set
- `metrics_llm_judge_v1.json`, `metrics_llm_judge_v2.json` -- metrics per version
- `predictions_llm_judge_v1.json`, etc. -- per-pair predictions for error analysis
- `metrics_baseline.json`, `predictions_baseline.json` -- baseline results
- `error_analysis_v1.md`, `error_analysis_v2.md` -- human-readable error reports
- `COMPARISON.md` -- side-by-side metrics table
- `PROMPT_CHANGELOG.md` -- what changed between v1 and v2 and why
- `REPORT_WEEK2.md` -- the human's (Tim's) written analysis. Claude does not fill in the prose sections.
