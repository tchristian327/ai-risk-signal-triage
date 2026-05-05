# Week 2 Evaluation Report

## Day 7: LLM judge v1 baseline metrics

### Headline metrics

| Metric | Value |
|--------|-------|
| Exact match accuracy | 22.4% |
| Off-by-one accuracy | 65.3% |
| Recall @ score >= 3 | 33.3% (6 of 18 high-relevance pairs caught) |
| Confusion matrix diagonal | 11 of 49, per-class: [7, 1, 0, 0, 3] |
| Eval set size | 49 pairs |
| Model | claude-haiku-4-5 via Bedrock |
| Avg latency / pair | 5,163 ms |
| Cost (full eval run) | $0.08 |

### What I see

Recall at score >= 3 is 33%, meaning two-thirds of high-relevance signals were missed. That's the wrong direction for governance, where false negatives are worse than false positives. Off-by-one looks okay at 65% but is misleading because the LLM is concentrated at the extremes. The model is not calibrated to the rubric I gave it.

### Error patterns

- On review, ~4 of my 49 labels over-weighted surface domain match ("driving related" -> 2). Leaving them in for eval consistency, flagging the pattern. The LLM failures below dominate this in magnitude.
- Score collapse: the LLM made zero predictions of score 2 across 49 pairs, and used 3 or 4 only six times. It's treating the rubric as binary instead of a gradient.
- Over-strict mechanism matching: when a signal illustrates a risk category named in the system card but the specific failure mode differs, the LLM scores 0 or 1 anyway. The Google/gorilla incident vs the doc OCR pipeline is the cleanest example.

### What I'd want to fix

- Delete the prompt paragraph telling the model "score 0 is correct and expected for many pairs." It's the only concrete scoring guidance in the prompt and it points downward.
- Add anchoring examples for rubric levels 2 and 3. Their language is vague compared to 0 and 4, so the model retreats to levels with sharper boundaries.
- Reframe the asymmetric-cost guidance to be concrete: signals that illustrate a risk category named in the system card are at least a 3, even if the specific failure mode differs.

---

## Day 8: Baseline comparison

| Metric | LLM Judge v1 | Logistic Regression |
|--------|-------------|---------------------|
| Exact match accuracy | 22.4% | 36.7% |
| Off-by-one accuracy | 65.3% | 69.4% |
| Recall @ score >= 3 (headline) | 33.3% (6/18) | 61.1% (11/18) |
| Confusion matrix diagonal | 11/49, per-class: [7, 1, 0, 0, 3] | 18/49, per-class: [2, 6, 2, 0, 8] |
| Eval set size | 49 pairs | 49 pairs (LOO CV) |
| Avg latency / pair | 5,163 ms | 11 ms |
| Cost / 1k pairs | $1.68 | $0.00 |
| Model | claude-haiku-4-5 | logistic regression |

### What I see

The classifier wins on every metric, but it's not a fair fight: LOO CV gives the classifier 48 labels per prediction while the LLM gets zero. The recall gap (33% vs 61%) is also mostly explained by the LLM's score collapse, since it only used score 3 or 4 six times out of 49. The non-quality numbers are real though: the classifier is ~450x faster and effectively free, which would matter at scale even after Day 9 narrows the gap.

### Why the baseline performs the way it does

Both systems struggle with the middle of the rubric. The classifier gets 0 of 6 score-3 examples right. That suggests part of the score-2-vs-3 confusion is inherent in this small eval set, not purely a prompting problem.

---

## Day 9: LLM judge v2

### Changes made

1. **Removed the downward-biasing paragraph.** Deleted "score 0 is correct and expected for many pairs" from the asymmetric error costs section. It was the only concrete scoring guidance in v1 and it pointed down.
2. **Added a concrete risk-category rule.** "If a signal illustrates a risk category explicitly named in a system's known risks, assign at least a 3, even if the specific failure mechanism differs."
3. **Added anchoring examples for scores 2 and 3.** One generic illustrative example per level to calibrate the model on the vague middle of the rubric.
4. **Rewrote the role description.** Shifted framing from "evaluate relevance" to "surface risks; your default is to flag, not filter."

### Comparison: v1 vs v2 vs baseline

| Metric | LLM Judge v1 | LLM Judge v2 | Logistic Regression |
|--------|-------------|-------------|---------------------|
| Exact match accuracy | 22.4% | 28.6% | 36.7% |
| Off-by-one accuracy | 65.3% | 75.5% | 69.4% |
| Recall @ score >= 3 (headline) | 33.3% (6/18) | 44.4% (8/18) | 61.1% (11/18) |
| Confusion matrix diagonal | 11/49, per-class: [7, 1, 0, 0, 3] | 14/49, per-class: [7, 2, 2, 0, 3] | 18/49, per-class: [2, 6, 2, 0, 8] |
| Eval set size | 49 pairs | 49 pairs | 49 pairs (LOO CV) |
| Avg latency / pair | 5,163 ms | 4,094 ms | 11 ms |
| Cost / 1k pairs | $1.68 | $1.68 | $0.00 |

### What I see

The v2 prompt moved every metric in the right direction. Off-by-one jumped from 65% to 76%, which tells me the model is landing closer to the right neighborhood even when it doesn't nail the exact score. Recall at >= 3 went from 33% to 44%, so 2 more high-relevance signals got caught. The score distribution also spread out: v1 made zero score-2 predictions, v2 made 9. The model is actually using the middle of the rubric now.

The classifier still wins on recall (61% vs 44%) and exact match (37% vs 29%), but the LLM now beats it on off-by-one (76% vs 69%). That's a meaningful distinction: the LLM is getting the general direction right more often, even if it doesn't land the precise score. The remaining recall gap is real, though. 10 of 18 high-relevance pairs are still missed, and several "risk category match" pairs are still scored 0 despite the explicit rule telling the model to score them at least 3. The rule helped but was applied inconsistently.

### Was iteration worth it?

Yes, but with a caveat. The v1-to-v2 delta (+11pp recall, +10pp off-by-one) came from four targeted prompt changes that each traced back to a specific failure mode in the error analysis. That's the right way to iterate, and the improvements are real. The caveat is that the classifier still wins on recall with zero prompt engineering and zero API cost, which reinforces the project's core finding: for governance triage with asymmetric error costs, a cheap model with labeled examples catches more of what matters than a zero-shot LLM judge. The LLM's value is in the reasoning and suggested actions it produces alongside the score, not in the score itself.
