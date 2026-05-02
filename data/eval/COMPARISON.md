| Metric | LLM Judge v1 | Logistic Regression |
|--------|-------------|---------------------|
| Exact match accuracy | 22.4% | 36.7% |
| Off-by-one accuracy | 65.3% | 69.4% |
| Recall @ score ≥ 3 (headline) | 33.3%  (6 of 18 high-relevance pairs caught) | 61.1%  (11 of 18 high-relevance pairs caught) |
| Confusion matrix | 11/49 on diagonal — per-class: [7, 1, 0, 0, 3] | 18/49 on diagonal — per-class: [2, 6, 2, 0, 8] |
| Eval set size | 49 pairs | 49 pairs (LOO CV) |
| Avg latency / pair | 5163 ms | 11.31 ms |
| Cost / 1k pairs | $1.68 | $0.00 |
| Model | us.anthropic.claude-haiku-4-5-20251001-v1:0 | logistic_regression |
