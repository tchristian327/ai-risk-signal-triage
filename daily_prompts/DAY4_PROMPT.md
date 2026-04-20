# Claude Code prompt — Day 4: Pipeline orchestration and the Digest output

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 4. Then, in your own words, give me a 3-4 sentence summary of what Day 4 produces, why it exists as a separate day from Days 2-3, and what the `Digest` output makes possible for Day 5. Do not skip this step.

Once I confirm the summary, your task for Day 4 is to wire Days 1-3 together into a single runnable pipeline, and define the output schema that the dashboard will consume. The dashboard on Day 5 will be a pure load-and-display app. That's only possible if today's work produces a clean, complete, self-describing output file.

## What to build

1. **Define the `Digest` schema in `src/schemas.py`.** This is the top-level output object. It should contain everything the dashboard needs in one file:

   ```python
   class RunMetadata(BaseModel):
       run_timestamp: datetime
       model_name: str
       retrieval_threshold: float
       num_signals: int
       num_systems: int
       num_pairs_after_retrieval: int
       num_pairs_scored: int
       num_pairs_failed: int
       elapsed_seconds: float

   class Digest(BaseModel):
       metadata: RunMetadata
       systems: list[AISystem]
       signals: list[Signal]
       scored_pairs: list[ScoredPair]
   ```

   Including the full systems and signals lists in the Digest is intentional. The dashboard needs to render system cards and signal details, and we don't want it loading three separate files. One file, one load, one source of truth for what's displayed.

2. **Build `src/pipeline.py`** with a single function `run_pipeline(portfolio_path: Path, signals_path: Path, output_path: Path, retrieval_threshold: float = 0.3, top_k_per_system: int = 8) -> Digest`.

   The function should:
   - Start a timer
   - Load the portfolio (using `src/portfolio.py`)
   - Load the signals (using `src/ingest.py`)
   - Call the retriever from `src/retrieval.py` to get all similarity pairs
   - Apply the candidate filter (above threshold OR top-k per system)
   - Initialize the LLM client via `get_llm_client()` from `src/scoring.py`
   - Call the scorer from `src/scoring.py` for each candidate, collecting `ScoredPair` objects
   - Track failures (don't crash on a single failed pair)
   - Stop the timer
   - Build the `RunMetadata` object
   - Build the `Digest` object
   - Write the Digest to `output_path` as JSON
   - Return the Digest

   This function is the *one* place that orchestrates everything. Days 2 and 3's CLI scripts continue to work for individual stages, but `pipeline.py` is the canonical end-to-end entry point.

3. **Update `scripts/run_pipeline.py`** (which was a stub from Day 1) to call `run_pipeline()` with sensible defaults and write to `data/outputs/digest.json`. Add CLI flags: `--threshold`, `--top-k`, `--limit-signals` (for testing on a subset), `--yes` (skip the cost confirmation prompt).

4. **Cost confirmation prompt.** Before the scoring stage runs, the script should print: "About to score N pairs using model X. Estimated cost: $Y. Continue? [y/N]" and wait for input. Skip if `--yes` is passed. Compute the estimate from the number of pairs and a constant cost-per-call you hardcode at the top.

5. **Logging.** The pipeline should log clearly at each stage:
   - "Loaded N systems from portfolio"
   - "Loaded M signals"
   - "Computing similarity matrix... (NxM = K pairs)"
   - "After filtering: K pairs above threshold, scoring..."
   - "Scoring pair X of K: signal_id=... system_id=..." (every 10th pair, not every one)
   - "Scoring complete: N pairs scored, M failed, elapsed Xs"
   - "Wrote digest to data/outputs/digest.json"

6. **Validation.** After writing the Digest, immediately re-read it from disk and validate it against the `Digest` Pydantic model. If validation fails, log loudly and exit non-zero. The Day 5 dashboard depends on this file being well-formed, so we catch any drift here.

## Implementation notes

- **No new business logic.** Day 4 is glue. If you find yourself writing a function that does scoring or embedding work, stop — that work belongs in `src/scoring.py` or `src/retrieval.py`. Refactor it back to the right module.

- **The `Digest` is the API contract.** Treat its schema as a contract between the pipeline (producer) and the dashboard (consumer). Any change to the Digest schema requires updating both sides. Document this in a comment at the top of the schema.

- **Use the existing functions, don't duplicate.** Day 2 has `compute_similarities`. Day 3 has `score_pair`. Import them. Do not re-implement.

- **Filtering logic.** Pull the candidate filter into a small named function in `src/pipeline.py`, e.g. `select_candidates(similarities, threshold, top_k_per_system)`. This is the one new piece of business logic in Day 4 and it deserves to be testable on its own.

- **Don't fail the whole run if one pair fails.** Catch exceptions from `score_pair`, log them, increment a failure counter, and continue. The `RunMetadata.num_pairs_failed` field captures this.

- **Type hints, comments, logging via `logging`** — same conventions as previous days.

## Definition of done

- `python scripts/run_pipeline.py --limit-signals 10` runs end-to-end on a small subset and produces a valid `digest.json`
- Then `python scripts/run_pipeline.py` runs on the full set and produces a valid `digest.json`
- The Digest file loads cleanly into the `Digest` Pydantic model
- The metadata fields are all populated and sensible
- Pipeline logs are clean, readable, and free of clutter
- Days 2 and 3's individual scripts still work (you didn't break them)

## Scope guardrails

- **Do not** start the Streamlit app. That's Day 5.
- **Do not** add any new analytical features (no aggregations, no derived metrics). The Digest contains raw scored pairs; any aggregation happens in the dashboard.
- **Do not** add database support, caching layers, or any persistence beyond writing JSON to disk.
- **Do not** change the schemas from previous days except to add `Digest` and `RunMetadata`.
- **Do not** modify `src/scoring.py` or `src/retrieval.py` except for trivial fixes if you find a bug. Bug fixes should be reported in your summary.

## Skills to load

None today. Day 4 is plumbing. If something feels uncertain, ask before guessing.

When you're done, give me a short summary of: (1) what you built, (2) any bugs you found in the Day 2 or Day 3 code, (3) the metadata fields from the full pipeline run, (4) the size of the digest.json file, and (5) any concerns about Day 5.
