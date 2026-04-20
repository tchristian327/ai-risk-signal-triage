# Claude Code prompt — Stretch: PyTorch MLP baseline

Before writing any code, re-read `CLAUDE.md` (especially the "Stretch additions" section) and `DECISIONS.md` in full. Read `PLAN.md` at the "Stretch additions" section. Then **load the `eval-framework` skill** by reading its `SKILL.md` file in full.

After reading those, in your own words, give me a 3-4 sentence summary of what we're adding, why a PyTorch MLP alongside the logistic regression (not instead of it), and what story the expanded comparison table should tell. Do not skip this step.

Once I confirm the summary, your task is to add a small PyTorch MLP to the eval comparison. This is a half-day task (~4-6 hours). The whole point is the expanded head-to-head comparison table in the dashboard, not a production scorer.

**Hard prerequisite:** All 13 planned days must be complete before starting this. If the interview is imminent, skip this entirely.

## Prerequisites

Confirm these exist before starting:
- `data/eval/labeled_pairs.json` with ~50 entries
- `data/eval/metrics_llm_judge_v2.json` (stable, no more prompt iteration)
- `data/eval/metrics_baseline.json` (Day 8 logistic regression)
- `src/baseline_classifier.py` (Day 8, with `build_features` and the embedding reuse pattern)
- The LLM judge metrics are stable (no more prompt iteration planned)

## What to build

1. **Add `torch` to `requirements.txt`.** `scikit-learn` is already present from Day 8.

2. **Build `src/pytorch_baseline.py`** with:

   a. **A small MLP class** inheriting from `torch.nn.Module`. Architecture:
      - Input: same feature vector as Day 8 (`build_features` output — signal_embedding + system_embedding + element-wise product)
      - One hidden layer (128 units, ReLU activation)
      - Dropout (0.3)
      - Output layer (5 units for classes 0-4)
      - No fancy architecture. The point is "I used PyTorch," not "I designed a novel neural net."

   b. **A training function** `train_mlp(X, y, n_epochs=100, lr=0.01, random_state=42)` that:
      - Converts X and y to tensors
      - Uses CrossEntropyLoss with class weights (same balanced weighting rationale as Day 8)
      - Uses Adam optimizer
      - Trains for n_epochs
      - Returns the trained model
      - Sets `torch.manual_seed(random_state)` for reproducibility

   c. **A cross-validated prediction function** `cross_validated_predictions_mlp(X, y, n_splits=5)` that mirrors Day 8's cross-validation approach. Returns out-of-fold predictions for every example.

   Reuse `build_features` from `src/baseline_classifier.py`. Do not duplicate the feature engineering.

3. **Build `scripts/train_pytorch_baseline.py`** that:
   - Loads `data/eval/labeled_pairs.json`
   - Looks up signal and system text, calls `build_features` on each pair
   - Runs `cross_validated_predictions_mlp`
   - Computes metrics using `src/evaluation.py` (same metrics as Day 7/8)
   - Writes to `data/eval/metrics_pytorch_mlp.json` and `data/eval/predictions_pytorch_mlp.json`
   - Prints metrics to console

4. **Add `precision_at_threshold` to `src/evaluation.py`:**

   ```python
   def precision_at_threshold(predictions: list[int], labels: list[int], threshold: int = 3) -> tuple[float, int, int]:
       """Of all items where prediction >= threshold, what fraction also have label >= threshold."""
       predicted_positive = [(p, l) for p, l in zip(predictions, labels) if p >= threshold]
       if not predicted_positive:
           return 0.0, 0, 0
       true_positives = sum(1 for p, l in predicted_positive if l >= threshold)
       return true_positives / len(predicted_positive), true_positives, len(predicted_positive)
   ```

   Update `compute_all_metrics` to include precision at threshold >= 3.

5. **Update `scripts/compare_systems.py`** to add a fourth column (PyTorch MLP) and two new rows (precision at >= 3, cost per 100 pairs). Write the updated table to `data/eval/COMPARISON.md`.

6. **Update the dashboard's Evaluation tab** (`app/streamlit_app.py`):
   - The comparison table now has 4 rows: LLM judge v1, LLM judge v2, logistic regression, PyTorch MLP
   - Add columns: precision at >= 3 and cost per 100 pairs alongside the existing metrics
   - Update `load_eval_data` to also load `metrics_pytorch_mlp.json` (with graceful fallback if it doesn't exist yet)

7. **Update the README:**
   - Results section: update the comparison table with the fourth row
   - Tech stack: add PyTorch
   - Add one sentence to the results summary about the classifier-vs-LLM tradeoff story

## Implementation notes

- **Reuse everything from Day 8.** The feature engineering, the cross-validation strategy, the metric computation — all of it comes from existing code. The only new thing is the PyTorch model class and its training loop.

- **Don't tune hyperparameters.** One hidden layer, 128 units, 0.3 dropout, 100 epochs, lr=0.01. These are reasonable defaults for a tiny dataset. Grid search on 50 examples is overfitting, not tuning.

- **The expected result:** The MLP will probably perform similarly to the logistic regression (maybe slightly better, maybe slightly worse) because 50 training examples isn't enough data for a neural net to outperform a linear model. That's fine. The story is: "I tried both, measured both, and the LLM judge still wins on recall for high-relevance items, which is what matters for governance."

- **Cost per 100 pairs:** For both classifiers, this is effectively $0 (in-process inference). For the LLM judge, compute from the per-pair cost in run_metadata.

- **Reproducibility.** Set `torch.manual_seed(42)` and `random.seed(42)`. Document the seeds.

- **This is strictly a comparison arm.** The MLP is not a production scorer, not a fallback, not an ensemble component. If you find yourself wiring it into `src/pipeline.py`, stop.

## Definition of done

- `python scripts/train_pytorch_baseline.py` runs end-to-end without errors
- `data/eval/metrics_pytorch_mlp.json` exists in the same schema as the other metrics files
- `data/eval/COMPARISON.md` shows four columns side by side
- The dashboard's Evaluation tab shows the expanded comparison table
- The README's results and tech stack sections are updated
- The asymmetric-error tradeoff story is clear: classifiers are cheaper but miss urgent items

## Scope guardrails

- **Do not** modify the LLM judge, the rubric, or the eval set
- **Do not** tune hyperparameters on the PyTorch model
- **Do not** add the MLP to the production pipeline. It's eval-only.
- **Do not** add additional ML frameworks (no TensorFlow, no JAX, no XGBoost)
- **Do not** retrain or modify the Day 8 logistic regression
- **Do not** add new views to the dashboard. Update the existing Evaluation tab only.

## Skills to load

- `eval-framework` — apply the comparison table format, honest-reporting standards, and the "classifiers are a comparison arm, not production" rule.

When you're done, give me a short summary of: (1) the MLP architecture, (2) the 4-way comparison table (just the numbers), (3) which scorer wins on which metric, (4) whether the asymmetric-error story lands clearly, and (5) any concerns.
