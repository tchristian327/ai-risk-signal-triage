# Week 2 evaluation report

## Day 7: LLM judge v1 baseline metrics

### Headline metrics
{
  "exact_match_accuracy": 0.22448979591836735,
  "off_by_one_accuracy": 0.6530612244897959,
  "recall_at_threshold_3": {
    "recall": 0.3333333333333333,
    "true_positives": 6,
    "total_positives": 18,
    "description": "6 of 18 high-relevance pairs caught"
  },
  "confusion_matrix": [
    [
      7,
      15,
      5,
      5,
      3
    ],
    [
      1,
      1,
      2,
      1,
      3
    ],
    [
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      3
    ],
    [
      0,
      0,
      0,
      0,
      3
    ]
  ],
  "n_pairs": 49,
  "run_metadata": {
    "timestamp": "2026-04-30T23:43:54.196976+00:00",
    "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "provider": "bedrock",
    "temperature": 0.0,
    "eval_set_size": 49,
    "n_scored": 49,
    "n_failed": 0,
    "elapsed_seconds": 253.0,
    "avg_latency_ms": 5163,
    "estimated_cost_usd": 0.0823
  }
}

### What I see
 
Recall at score >= 3 is 33%, meaning two-thirds of high-relevance signals were missed. That's the wrong direction for governance, where false negatives are worse than false positives. Off-by-one looks okay at 65% but is misleading because the LLM is concentrated at the extremes. The model is not calibrated to the rubric I gave it.
 
### Error patterns
 
- On review, ~4 of my 49 labels over-weighted surface domain match ("driving related" → 2). Leaving them in for eval consistency, flagging the pattern. The LLM failures below dominate this in magnitude.
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
| Recall @ score >= 3 (headline) | 33.3%  (6 of 18 high-relevance pairs caught) | 61.1%  (11 of 18 high-relevance pairs caught) |
| Confusion matrix | 11/49 on diagonal, per-class: [7, 1, 0, 0, 3] | 18/49 on diagonal, per-class: [2, 6, 2, 0, 8] |
| Eval set size | 49 pairs | 49 pairs (LOO CV) |
| Avg latency / pair | 5163 ms | 11.31 ms |
| Cost / 1k pairs | $1.68 | $0.00 |
| Model | claude-haiku-4-5 | logistic_regression |
 
### What I see
 
The classifier wins on every metric, but it's not a fair fight: LOO CV gives the classifier 48 labels per prediction while the LLM gets zero. The recall gap (33% vs 61%) is also mostly explained by the LLM's score collapse, since it only used score 3 or 4 six times out of 49. The non-quality numbers are real though: the classifier is ~450x faster and effectively free, which would matter at scale even after Day 9 narrows the gap.
 
### Why the baseline performs the way it does
 
Both systems struggle with the middle of the rubric. The classifier gets 0 of 6 score-3 examples right. That suggests part of the score-2-vs-3 confusion is inherent in this small eval set, not purely a prompting problem.
 
---
 
## Day 9: LLM judge v2
 
### Changes made
 
1. **Removed the downward-biasing paragraph** — deleted "score 0 is correct and expected for many pairs" from the asymmetric error costs section. It was the only concrete scoring guidance in v1 and it pointed down.
2. **Added a concrete risk-category rule** — "If a signal illustrates a risk category explicitly named in a system's known risks, assign at least a 3, even if the specific failure mechanism differs."
3. **Added anchoring examples for scores 2 and 3** — one generic illustrative example per level to calibrate the model on the vague middle of the rubric.
4. **Rewrote the role description** — shifted framing from "evaluate relevance" to "surface risks; your default is to flag, not filter."
 
### Comparison: v1 vs v2 vs baseline
 
| Metric | LLM Judge v1 | LLM Judge v2 | Logistic Regression |
|--------|-------------|-------------|---------------------|
| Exact match accuracy | 22.4% | 28.6% | 36.7% |
| Off-by-one accuracy | 65.3% | 75.5% | 69.4% |
| Recall @ score ≥ 3 (headline) | 33.3%  (6 of 18 high-relevance pairs caught) | 44.4%  (8 of 18 high-relevance pairs caught) | 61.1%  (11 of 18 high-relevance pairs caught) |
| Confusion matrix | 11/49 on diagonal — per-class: [7, 1, 0, 0, 3] | 14/49 on diagonal — per-class: [7, 2, 2, 0, 3] | 18/49 on diagonal — per-class: [2, 6, 2, 0, 8] |
| Eval set size | 49 pairs | 49 pairs | 49 pairs (LOO CV) |
| Avg latency / pair | 5163 ms | 4094 ms | 11.31 ms |
| Cost / 1k pairs | $1.68 | $1.68 | $0.00 |
 
### What I see
 
(3-5 sentences in your voice)
 
### Was iteration worth it?
 
(1-2 sentences — honest assessment of whether the v1 → v2 work paid off)