# Claude Code prompt — Day 7: Metrics and LLM judge evaluation

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 7. Then **load the `eval-framework` skill** by reading its `SKILL.md` file in full. This skill is the foundation for everything you'll do today.

After reading those, in your own words, give me a 4-5 sentence summary of what we're measuring today, why recall at score >= 3 is the headline metric for this project, and what error analysis will produce. Do not skip this step.

Once I confirm the summary, your task for Day 7 is to evaluate the LLM judge against the eval set I labeled on Day 6. This is pure measurement — no prompt iteration, no fixes. Today we find out where we stand and write down what we see.

## Prerequisites

Before starting, confirm `data/eval/labeled_pairs.json` exists and has ~50 entries. If it doesn't, stop and ask me — Day 7 cannot proceed without the labels.

## What to build

1. **Build `src/evaluation.py`** with the following functions:

   a. **`exact_match_accuracy(predictions: list[int], labels: list[int]) -> float`** — fraction where prediction equals label.

   b. **`off_by_one_accuracy(predictions: list[int], labels: list[int]) -> float`** — fraction where `abs(prediction - label) <= 1`.

   c. **`recall_at_threshold(predictions: list[int], labels: list[int], threshold: int = 3) -> tuple[float, int, int]`** — of all the items where `label >= threshold`, what fraction also have `prediction >= threshold`. Returns (recall, true_positives, total_positives) so the dashboard can show "17 of 20 caught" not just "85%".

   d. **`confusion_matrix(predictions: list[int], labels: list[int], num_classes: int = 5) -> list[list[int]]`** — a 5x5 nested list. Rows are predicted scores (0 at top, 4 at bottom), columns are human labels (0 on left, 4 on right). Cell `[i][j]` is the count of items where prediction=i and label=j.

   e. **`compute_all_metrics(predictions: list[int], labels: list[int]) -> dict`** — calls all of the above and returns a single dict with all the results, keyed by metric name. This is what gets serialized to JSON.

   Each function gets a 1-2 sentence docstring explaining what it computes. The recall function gets a longer comment explaining *why* it's the operationally important metric for this project (point at the asymmetric error costs in `DECISIONS.md`).

2. **Build `scripts/run_eval.py`** as the script that evaluates the LLM judge.

   Behavior:
   - Loads `data/eval/labeled_pairs.json`
   - Loads the portfolio and signals so we have full text for each labeled pair
   - Initializes the LLM client via `get_llm_client()` from `src/scoring.py`
   - For each labeled pair, calls `score_pair` from `src/scoring.py` (the same scorer used in production, using the same Bedrock or fallback client). Important: this is *not* reading from `digest.json` -- we want a fresh LLM call per eval pair so we're measuring the current state of the scorer, not the state at the time of the last pipeline run.
   - Collects (prediction, human_label) tuples
   - Computes all metrics via `compute_all_metrics`
   - Writes the metrics to `data/eval/metrics_llm_judge_v1.json` along with run metadata (timestamp, model used, eval set size)
   - Writes the per-pair predictions to `data/eval/predictions_llm_judge_v1.json` so they can be used for error analysis later
   - Prints all metrics to the console in a clean format
   - Adds `--limit N` and `--yes` flags as in Day 3

3. **Build `scripts/error_analysis.py`** to surface the worst-performing pairs:

   - Loads the eval predictions and the labeled pairs
   - Identifies pairs where `abs(prediction - label) >= 2` (the "really wrong" ones)
   - For each, prints: pair index, signal title, system name, human label, LLM prediction, the LLM's reasoning, and the human note (if any)
   - Writes the same content to `data/eval/error_analysis_v1.md` as a structured markdown file
   - Sorts by absolute error descending so the worst cases come first
   - Includes a count summary at the top: "12 pairs with abs error >= 2 out of 50"

4. **Create `data/eval/REPORT_DAY7.md`** as a stub for me to fill in:

   ```markdown
   # Day 7 evaluation report (LLM judge v1)

   ## Headline metrics
   (paste the metrics from metrics_llm_judge_v1.json here)

   ## What I see
   (3-5 sentences, in my own voice, about what the metrics say)

   ## Error patterns
   (after reading error_analysis_v1.md, list 2-3 patterns I notice)

   ## What I'd want to fix
   (2-3 specific things, will inform Day 9)
   ```

   Do not fill this in yourself. I'll write it after reading the metrics and error analysis. The point is that *I* form the opinions about what's working, not the LLM that's grading itself.

## Implementation notes

- **Use the existing `score_pair` function from Day 3.** Do not duplicate any scoring logic. If you find yourself rewriting prompt construction, stop — import from `src/scoring.py`.

- **The eval set is small (~50 pairs).** The whole eval should run in 1-2 minutes. No need for parallelization, batching, or async. Sequential calls are fine.

- **Confusion matrix display.** When printing to console, render it as a small grid with row and column labels. Example:

  ```
                          Human Label
                    0    1    2    3    4
              0  [  3,   1,   0,   0,   0]
  Predicted   1  [  1,   2,   1,   0,   0]
  Score       2  [  0,   1,   8,   3,   0]
              3  [  0,   0,   2,   9,   1]
              4  [  0,   0,   0,   2,   8]
  ```

  Use plain ASCII. The diagonal (correct predictions) should be visually distinguishable somehow — maybe surround diagonal cells with brackets, or print a separator line under each row. Don't reach for a library.

- **Reproducibility.** The LLM at temperature 0 should produce nearly-deterministic output, but document in `REPORT_DAY7.md` the exact model name, temperature, and timestamp of the eval run. This matters for the comparison on Day 9 — we want to be sure we're comparing v1 and v2 fairly.

- **Logging.** Same conventions as previous days. Log progress every 10 pairs.

- **Cost.** ~50 pairs at Haiku prices is pennies. Skip the cost confirmation prompt for the eval script — but log the total cost at the end so I can keep track.

## Definition of done

- `python scripts/run_eval.py` runs end-to-end and produces both the metrics file and the predictions file
- The metrics are printed clearly to the console
- `python scripts/error_analysis.py` runs and produces a readable error analysis file
- `REPORT_DAY7.md` exists as a stub for me to fill in
- All four metrics functions have docstrings and the recall function has a comment explaining why it's the headline
- I can read the error analysis and see the worst pairs in a useful format

## Scope guardrails

- **Do not** modify the LLM judge prompt. Today is measurement. Day 9 is iteration.
- **Do not** modify the rubric. It's locked.
- **Do not** start building the baseline classifier. That's Day 8.
- **Do not** add metrics that weren't in this prompt (no ROC, no F1, no Cohen's kappa). The four listed metrics are exactly what we need.
- **Do not** fill in `REPORT_DAY7.md` yourself. That file is for me.
- **Do not** modify the dashboard.

## Skills to load

- `eval-framework` — apply the metric definitions, the honest-eval principle, and the error analysis structure.

When you're done, give me a short summary of: (1) what you built, (2) the headline metrics from the eval run (just the numbers, no commentary — I'll form the opinions), (3) the count of "really wrong" pairs found in error analysis, and (4) any concerns about Day 8.
