# Claude Code prompt — Day 8: Trained classifier baseline

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 8. Then **load the `eval-framework` skill** by reading its `SKILL.md` file in full.

After reading those, in your own words, give me a 4-5 sentence summary of what we're building today, why this baseline exists, and how it gets compared to the LLM judge. Pay special attention to: this is the move that makes the project a *data science* project. Do not skip this step.

Once I confirm the summary, your task for Day 8 is to build a trained classifier that competes with the LLM judge on the same task and the same eval set, then compare the two systems honestly.

## Why this matters

From `DECISIONS.md`: "I built the production system as a hybrid retrieval and LLM-judge pipeline, and I benchmarked it against a trained classifier baseline on the same eval set." That sentence is the interview talking point. Today is when we make that sentence true.

The baseline is a logistic regression or LightGBM classifier trained on sentence-transformer embeddings of (signal, system) pairs, predicting the 0-4 score. It's intentionally simple. The point is not to beat the LLM judge — the point is to have an honest comparison so we know what each approach is good for.

With only ~50 labeled pairs, the classifier is data-starved. That's *expected* and *fine*. The honest finding might end up being "the LLM judge wins because the classifier doesn't have enough training data, which itself is a useful result for a real governance team to know."

## What to build

1. **Add `scikit-learn` to `requirements.txt`.** Use scikit-learn for the classifier (logistic regression). LightGBM is overkill for ~50 examples and adds a heavy dependency. Plain logistic regression is the right choice here.

2. **Build `src/baseline_classifier.py`** with the following structure:

   a. **A feature engineering function** `build_features(signal_text: str, system_text: str) -> np.ndarray`. This embeds both texts (using the same `all-MiniLM-L6-v2` model from Day 2 — reuse the cached embedder from `src/retrieval.py`, do not load the model twice) and produces a feature vector. Use the concatenation of (signal_embedding, system_embedding, element-wise product). The element-wise product is a cheap way to give the classifier interaction features. Document the choice in a comment.

   b. **A function `train_classifier(X: np.ndarray, y: np.ndarray) -> LogisticRegression`** that fits a multinomial logistic regression with `class_weight='balanced'` (because the labels are imbalanced — there are more low scores than high). Use `solver='lbfgs'`, `max_iter=1000`. Return the fitted model.

   c. **A function `cross_validated_predictions(X, y, n_splits) -> tuple[np.ndarray, dict]`** that runs leave-one-out cross-validation (since the eval set is so small) or 5-fold if leave-one-out is too slow. Returns the out-of-fold predictions for every example AND a dict with per-fold metrics.

   The reason for cross-validation rather than train/test split: we have 50 examples. A 80/20 split leaves 10 in the test set, which is too few to compute meaningful metrics. Cross-validation gives us a prediction for every example while still respecting the train/test boundary.

3. **Build `scripts/train_baseline.py`** as the script that trains and evaluates the baseline:

   - Loads `data/eval/labeled_pairs.json`
   - For each labeled pair, looks up the signal text and system text from the portfolio and signals files
   - Calls `build_features` on each pair, stacks them into an `X` matrix
   - Stacks the human labels into a `y` array
   - Calls `cross_validated_predictions`
   - Computes the same metrics as Day 7 (using `src/evaluation.py`) on the cross-validated predictions
   - Writes results to `data/eval/metrics_baseline.json` (same schema as the LLM judge metrics file so they're directly comparable)
   - Writes per-pair predictions to `data/eval/predictions_baseline.json`
   - Prints the metrics to console

4. **Build `scripts/compare_systems.py`** that loads both metrics files (LLM judge v1 and baseline) and produces a side-by-side comparison:

   - Loads `data/eval/metrics_llm_judge_v1.json` and `data/eval/metrics_baseline.json`
   - Prints a table to the console with rows = metrics, columns = systems
   - Writes the same table to `data/eval/COMPARISON.md` as a markdown table
   - Includes the latency and cost rows from the `eval-framework` skill's example. Latency for the baseline is ~5ms (in-process). Latency for the LLM judge is whatever you measure during the Day 7 eval (track this in the eval script and write it to the metrics file — go back and update Day 7's run_eval.py if you didn't capture it).
   - Cost for the baseline is effectively zero. Cost for the LLM judge is computed from the per-pair cost.

   The comparison file should be ready for me to read and form an opinion. Do not write commentary. The numbers tell the story.

5. **Update `data/eval/REPORT_DAY7.md`** to be `data/eval/REPORT_WEEK2.md` and add a section for the comparison:

   ```markdown
   ## Day 8: Baseline comparison
   (paste the comparison table from COMPARISON.md here)

   ### What I see
   (3-5 sentences about the comparison, in my voice)

   ### Why the baseline performs the way it does
   (1-2 sentences hypothesizing about whether the baseline is data-starved, has the wrong feature representation, etc.)
   ```

   Do not fill in the prose sections — that's for me.

## Implementation notes

- **Reuse the embedder.** Do not load `all-MiniLM-L6-v2` a second time. Import the embedding function from `src/retrieval.py`. The disk cache from Day 2 means embeddings for signals and systems will be cache hits.

- **Multiclass logistic regression.** scikit-learn's `LogisticRegression` handles multiclass automatically with `multi_class='multinomial'`. Set this explicitly. With 5 classes and 50 examples and ~1100-dimensional features, the model is heavily over-parameterized — that's fine, the L2 regularization will handle it.

- **Class imbalance.** Use `class_weight='balanced'`. If a particular class has 0 examples in a fold's training data (possible with leave-one-out on small data), the model can't predict that class — that's a known limitation, document it in the report.

- **Reproducibility.** Set `random_state=42` everywhere relevant. Document the seed.

- **Don't tune hyperparameters.** This is a baseline. Default scikit-learn settings (with the changes noted above) are correct. If you find yourself reaching for grid search, stop — that's overfitting on a 50-example eval set and would invalidate the comparison.

- **Latency measurement.** Time the cross-validated predictions and divide by the number of pairs. Per-pair latency for the baseline should be on the order of milliseconds. For the LLM judge, the per-pair time was logged during Day 7 eval (or should be — go fix Day 7 if you didn't track it).

## Definition of done

- `python scripts/train_baseline.py` runs end-to-end without errors
- `data/eval/metrics_baseline.json` exists in the same schema as `metrics_llm_judge_v1.json`
- `python scripts/compare_systems.py` produces a clear side-by-side comparison
- `data/eval/COMPARISON.md` exists with a clean markdown table
- `REPORT_WEEK2.md` has the comparison section stubbed for me to fill in
- The Day 7 eval script has been updated to capture per-pair latency if it wasn't already
- The baseline result is what it is — do not retroactively tune anything to make it look better or worse

## Scope guardrails

- **Do not** modify the LLM judge or its prompt. Day 9 is for prompt iteration.
- **Do not** modify the rubric.
- **Do not** add a second baseline on Day 8 (no LightGBM, no random forest, no neural net). One baseline, one comparison. A PyTorch MLP baseline may be added later as a stretch addition after Day 13.
- **Do not** do hyperparameter tuning. Defaults are correct for this task.
- **Do not** change the eval set. The labeled pairs are locked.
- **Do not** fill in the prose sections of the report.
- **Do not** modify the dashboard (the eval view comes on Day 10).

## Skills to load

- `eval-framework` — apply the cross-validation reasoning, the comparison table format, and the honest-reporting standards.

When you're done, give me a short summary of: (1) what you built, (2) the comparison table (just the numbers), (3) the per-pair latency for both systems, (4) the per-1k-pairs cost for both systems, and (5) any concerns about Day 9.
