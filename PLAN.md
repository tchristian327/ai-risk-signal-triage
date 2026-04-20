# PLAN.md

The 10-day build plan for the AI risk signal triage agent. This document is the master arc. Each day has a specific goal, a specific output, and a specific definition of done. Days hand off to each other, so finishing a day means the next day can start without rework.

This plan is paired with per-day Claude Code prompts in `daily_prompts/`. Read this document first to understand the overall shape, then use the daily prompts to actually run each day.

## Guiding principles

1. **Each day is one focused chunk.** No day tries to do two things. If a day feels like it has two goals, it gets split.
2. **Each day ends with something runnable.** Even Day 1 ends with `python scripts/run_pipeline.py` working. Never leave the repo in a broken state overnight.
3. **Hard scope guardrails.** Each day's prompt explicitly says what *not* to do, because Claude Code's failure mode is doing too much and dragging in next-day work.
4. **Decisions are made here, not in Claude Code.** All the design choices live in `CLAUDE.md`, `DECISIONS.md`, and these prompts. Claude Code executes; it doesn't redesign.
5. **The eval is the product.** The whole project lives or dies on whether Week 2's measurement work is honest and clear. Week 1 exists to make Week 2 possible.

## Week 1 — Build the system

The goal of Week 1 is a working end-to-end pipeline plus a deployed dashboard. By the end of Day 5, you should be able to send someone a public URL and have them see scored signals against the portfolio. Quality of the scoring is *not* the goal of Week 1. Working plumbing is.

### Day 1 — Scaffold and plumbing

**Goal:** Repo exists, dependencies install, portfolio loads, signals load, end-to-end smoke test passes.

**Outputs:**
- Full repo structure per `CLAUDE.md`
- `data/portfolio/systems.yaml` with 6 fictional insurance AI systems
- `src/schemas.py` with `AISystem`, `Signal`, `ScoredPair` Pydantic models
- `src/portfolio.py` loader
- `src/ingest.py` with AI Incident Database fetcher
- `scripts/fetch_signals.py` and `scripts/run_pipeline.py`
- `data/signals/processed/aiid_signals.json` with 40-60 real signals

**Definition of done:** `python scripts/run_pipeline.py` prints a summary of loaded portfolio and signals. No scoring yet.

### Day 2 — Retriever (embeddings + cosine similarity)

**Goal:** For each (signal, system) pair, compute a cosine similarity score. This is the cheap filter that decides which pairs go to the LLM.

**Outputs:**
- `src/retrieval.py` with three things: an embedding function (using `sentence-transformers/all-MiniLM-L6-v2`), a disk cache keyed on content hash, and a function that computes the full similarity matrix between all signals and all systems
- `data/outputs/similarities.json` with one row per (signal, system) pair, containing both ids and the cosine score
- A small CLI in `scripts/run_retrieval.py` that runs the retriever and writes the similarities file
- The similarities are sorted within each system so it's easy to see which signals are most relevant

**Definition of done:** `python scripts/run_retrieval.py` produces the similarities file. Reruns are instant because of the cache. You can open the JSON and see that high-similarity pairs look qualitatively reasonable (an LLM-related incident scores high against the LLM-based systems).

**Key skills loaded:** none yet — retrieval is straightforward enough that no skill file is needed.

### Day 3 — LLM scorer (the agent core)

**Goal:** A function that takes a (signal, system) pair plus the rubric and returns a structured score with reasoning, justification, and suggested action. This is the most important day of Week 1.

**Outputs:**
- `src/scoring.py` with the scorer function and the prompt template
- The prompt embeds the full rubric verbatim from `CLAUDE.md`
- Uses Pydantic + the Bedrock Converse API's tool use feature for structured output, with the direct Anthropic SDK as a local fallback (no string parsing of LLM responses)
- A retry-with-backoff wrapper for transient API errors
- The scorer asks the model to reason *before* committing to a score, and the reasoning is captured in the output
- Default model is Claude Haiku for cost; the model name is a configurable constant at the top of the file
- A CLI in `scripts/run_scoring.py` that takes the similarities file, filters to candidates above a threshold (default 0.3) or top-N per system, scores them, and writes `data/outputs/scored_pairs.json`

**Definition of done:** `python scripts/run_scoring.py` produces a scored output file. Spot-check 5-10 scored pairs manually and confirm the reasoning makes sense, the scores feel directionally right, and the suggested actions are non-generic.

**Key skills loaded:** `llm-judge-scoring`, `structured-outputs-anthropic`. These two skills are doing real work on Day 3 — they encode the patterns that make the difference between a scorer that works and one that produces nonsense.

### Day 4 — Pipeline orchestration and output formatting

**Goal:** Wire Day 1, Day 2, and Day 3 together into a single runnable pipeline. Format the outputs so the dashboard can consume them with no transformation logic.

**Outputs:**
- `src/pipeline.py` with a `run_pipeline()` function that orchestrates portfolio loading, signal loading, retrieval, scoring, and output writing
- `scripts/run_pipeline.py` updated from its Day 1 stub to actually run the full pipeline
- The output is a single JSON file at `data/outputs/digest.json` containing: the portfolio (so the dashboard can render system cards), the full list of scored pairs, and run metadata (timestamp, model used, retrieval threshold, counts at each stage)
- The output schema is defined in `src/schemas.py` as a `Digest` Pydantic model
- Logging at each stage so you can see how many pairs survived retrieval, how many got scored, how long each stage took

**Definition of done:** `python scripts/run_pipeline.py` runs the full pipeline end to end and writes `digest.json`. The file loads cleanly into the `Digest` Pydantic model. Pipeline logs are clean and readable.

**Key skills loaded:** none — this is plumbing, not new logic.

### Day 5 — Streamlit dashboard and deployment

**Goal:** A clean, deployable dashboard that loads `digest.json` and presents it in a way that makes sense to a non-technical governance lead in under a minute. Deployed to Streamlit Community Cloud with a public URL.

**Outputs:**
- `app/streamlit_app.py` as the entry point
- The dashboard has three views: a top-line summary (counts, highest-scored pairs across the whole portfolio), a per-system view (pick a system, see its top signals), and a per-signal view (pick a signal, see which systems it's relevant to)
- All data loaded once via `@st.cache_data` from `digest.json` on disk — no LLM calls, no embeddings, no pipeline calls anywhere in the app
- Simple, restrained styling. One accent color. No animations. Score badges colored by severity (0-1 muted, 2 neutral, 3 warning, 4 alert)
- Reasoning and justification visible per pair, so the user can see *why* something was flagged
- A short "About this project" section explaining what it is and linking to the GitHub repo
- Deployed to Streamlit Community Cloud with the GitHub repo connected
- README updated with the public URL

**Definition of done:** You can send someone a URL and they can navigate the dashboard without any explanation from you. The UI is simple enough that a RevOps or governance lead immediately understands what they're looking at.

**Key skills loaded:** `streamlit-analytics-dashboard`.

**End of Week 1 checkpoint:** Working pipeline, deployed dashboard, real signals, no eval yet. If you stopped here you'd have a portfolio piece. Week 2 makes it a *data science* portfolio piece.

## Week 2 — Measure, compare, sharpen

The goal of Week 2 is to turn Week 1's working system into something you can defend with numbers. Three threads run through the week: building an eval set, building a comparison baseline, and using both to iterate on the LLM judge prompts.

### Day 6 — Build the eval set

**Goal:** A hand-labeled eval set of ~50 (signal, system) pairs covering the full 0-4 score range, that you and only you have labeled.

**Outputs:**
- A labeling helper script at `scripts/label_eval_set.py` that picks pairs to label using a stratified sampling strategy: not just the top-scored pairs from the LLM, but a mix of high, medium, and low cosine-similarity pairs so the eval set isn't biased toward easy positives
- A simple CLI labeling interface (prints the system, prints the signal, asks for a 0-4 score and an optional one-line note, saves to disk)
- `data/eval/labeled_pairs.json` with the labeled pairs in the same `ScoredPair` schema, but with a `human_label` field instead of (or alongside) the LLM's score
- A short `data/eval/LABELING_NOTES.md` where you write down anything you noticed during labeling that should inform prompt iteration — edge cases, ambiguous pairs, things the rubric doesn't quite cover
- The eval set should hit roughly: 12-15 pairs at score 0-1, 12-15 at score 2, 12-15 at score 3, 8-10 at score 4. If real data doesn't naturally cover the high-relevance bucket, pull a couple of synthetic adversarial cases for week 2 stress-testing.

**Definition of done:** `labeled_pairs.json` exists with ~50 entries spanning the full score range. Labeling notes file has at least a few observations.

**Key skills loaded:** `eval-framework`. This skill is the most important one for the whole second week — it encodes how to build a defensible eval set, not just how to compute metrics on one.

### Day 7 — Metrics and the LLM judge baseline

**Goal:** Compute honest metrics on the LLM judge against the eval set. Establish what "the system as it stands today" actually achieves.

**Outputs:**
- `src/evaluation.py` with metric functions: exact match accuracy, off-by-one accuracy, recall at score >= 3 (because of the asymmetric error costs from `DECISIONS.md` — missing real risks is worse than over-flagging), confusion matrix
- `scripts/run_eval.py` that runs the LLM judge on every pair in the eval set and writes a metrics report to `data/eval/metrics_llm_judge.json`
- A short `data/eval/REPORT_DAY7.md` written by you (the human, not Claude Code) summarizing what the metrics say, where the LLM is strong, where it's weak, and what you'd want to fix
- Confusion matrix saved as a CSV or JSON so it can be loaded into the dashboard later
- Per-pair error analysis: a list of every pair where the LLM was off by 2 or more, with both the LLM reasoning and the human label, so you can see *how* it failed, not just *that* it failed

**Definition of done:** Metrics file exists, error analysis file exists, you've read the errors and have an opinion about what's going wrong. Don't fix anything yet — that's Day 9. Day 7 is just measurement.

**Key skills loaded:** `eval-framework`.

### Day 8 — Trained classifier baseline

**Goal:** Build the comparison system. A logistic regression or LightGBM classifier trained on sentence-transformer embeddings of (signal, system) pairs, predicting the 0-4 score. Train on the labeled eval set with cross-validation since the eval set is small.

**Outputs:**
- `src/baseline_classifier.py` with the training and prediction code
- Feature engineering: concatenate signal embedding and system embedding (or use their element-wise product, or both — try a couple of options and document the choice)
- Cross-validated training (5-fold or LOOCV given the eval set size)
- `scripts/train_baseline.py` that trains the classifier and writes its predictions and metrics to `data/eval/metrics_baseline.json`
- The same metric set as Day 7 (exact match, off-by-one, recall at >= 3, confusion matrix) so the two systems are directly comparable
- A short `data/eval/COMPARISON.md` that shows the two systems' metrics side by side and discusses where each wins. Be honest. If the baseline is competitive, say so. If the LLM judge wins on recall but the baseline wins on consistency, say that.

**Definition of done:** Both systems have metrics computed on the same eval set. The comparison doc exists and is honest.

**Key skills loaded:** `eval-framework`.

### Day 9 — Iterate the LLM judge prompt

**Goal:** Use the Day 7 error analysis to make targeted improvements to the scoring prompt. Re-evaluate. Document what changed and why.

**Outputs:**
- An updated `src/scoring.py` with a v2 prompt
- Each prompt change is justified with a specific failure mode from Day 7 (e.g., "the model was scoring tangential mentions as 2 instead of 1 because the rubric language for level 1 wasn't sharp enough — added an example")
- Re-run the eval on the v2 prompt
- `data/eval/metrics_llm_judge_v2.json` and an updated `COMPARISON.md` showing v1 vs v2 vs baseline
- A `data/eval/PROMPT_CHANGELOG.md` that lists each change you made and its justification

**Hard rule:** Do not change the rubric. The rubric is locked for the entire project. If during Day 6 labeling the rubric feels imperfect, push through and label as consistently as you can — note ambiguities in `LABELING_NOTES.md` for the interview discussion, but do not edit the rubric. Changing it mid-project invalidates the eval set and forces re-labeling. Only the prompt scaffolding around the rubric changes on Day 9.

**Definition of done:** v2 metrics exist, v1 vs v2 vs baseline are compared in one place, the changelog is written.

**Key skills loaded:** `llm-judge-scoring`, `eval-framework`.

### Day 10 — Polish and the README

**Goal:** Get the project into "send this link to a recruiter" shape. Update the dashboard with the eval results. Write the README. Re-deploy.

**Outputs:**
- Dashboard updated with a fourth view: "Evaluation," which shows the eval set size, the metrics for both systems, the confusion matrix, and a short prose summary of what the metrics mean. This is the view that turns the project from "a dashboard" into "a defended system"
- The eval view shows the comparison clearly: side-by-side bars or a small table, not buried in text
- README written for an interviewer. Sections: what this is, why it exists, the architecture (with a small diagram or ASCII art), the eval methodology, the results, what you'd do next with more time, and a link to the live dashboard
- A short "honest limitations" section in the README. This is the move that lands well in interviews — listing what you know is wrong with the project signals self-awareness and is more impressive than overselling
- Final deploy to Streamlit Community Cloud
- Final commit, repo public on GitHub

**Definition of done:** You can paste a single GitHub link into a recruiter message and feel good about it. The dashboard URL is live. The README answers every reasonable question an interviewer would ask before they even talk to you.

**Key skills loaded:** `streamlit-analytics-dashboard`.

## Week 2 hygiene pass — Production signals

After the core data science work is complete, one additional day demonstrates the production engineering signals the JD calls for. This work comes after Day 10 and does not interfere with or delay any of the existing daily plan.

### Day 11 — Observability, Docker, CI

**Goal:** Add per-LLM-call observability, a working Dockerfile, and a CI pipeline. Then capture screenshots of real AWS Bedrock CloudWatch metrics as a visible deliverable.

**Phase 1: Observability.** Add per-LLM-call tracking to the scorer: tokens in, tokens out, latency (ms), estimated cost, model id, timestamp. Write this to `data/outputs/run_metadata.json` alongside each pipeline run's digest. Add a new section to the Streamlit dashboard that loads run metadata and shows totals (total tokens, total cost, average latency per call, total runs) plus a simple bar chart of cost per run.

**Phase 2: Docker.** Add a `Dockerfile` at the project root using a slim Python 3.11 base. The image must be able to run the pipeline CLI scripts. Add a `.dockerignore`. The image does not need to deploy anywhere; it just needs to build cleanly and run.

**Phase 3: CI.** Add `.github/workflows/ci.yml` with a single job on push and PR: install dependencies, `ruff check`, `pytest`, `docker build`. No pipeline execution in CI (no AWS credentials).

**Phase 4: Screenshots.** Run the full pipeline at least once, then take screenshots of the AWS Bedrock CloudWatch metrics dashboard. Save to `docs/screenshots/` and reference in the README.

**Definition of done:** `run_metadata.json` is populated after a pipeline run, the dashboard shows the observability section, `docker build` succeeds, CI passes on push, CloudWatch screenshots are in `docs/screenshots/`.

**Key skills loaded:** `streamlit-analytics-dashboard` (for the observability section in the dashboard).

### Day 12 — Infrastructure as Code with AWS CDK

**Goal:** Provision the project's AWS resources (Bedrock model access via IAM, S3 bucket for run artifacts) using AWS CDK in Python instead of manual console configuration. Deploy the stack once against the real AWS account so there's a real artifact, not just code.

**Outputs:**
- An `infra/` folder at the project root containing a minimal CDK app in Python (CDK in Python, not Terraform, to keep the whole project in one language)
- An IAM role/policy granting Bedrock invoke permissions for the Claude model used by the scorer
- An S3 bucket for storing pipeline run artifacts (`digest.json`, `run_metadata.json`) with sensible defaults (versioning on, public access blocked)
- A `cdk.json` and `requirements.txt` for the CDK app
- A short `infra/README.md` explaining how to synth, deploy, and destroy the stack
- A screenshot of the deployed CloudFormation stack in the AWS console saved to `docs/screenshots/`
- The main project README updated with a short "Infrastructure" section that references the CDK code and links to the screenshot

**Definition of done:** `cdk synth` runs cleanly, `cdk deploy` has been run successfully at least once against the real AWS account, the deployed stack screenshot is in `docs/screenshots/`, and the main README mentions the IaC piece. The pipeline does not need to be rewired to use the CDK-provisioned resources. Having them deployed and documented is enough.

**Key skills loaded:** none.

**Priority note:** This day is higher priority than Day 13. If time is short before the interview, do this and skip Day 13.

### Day 13 — LangGraph refactor of the scorer (optional)

**Goal:** Refactor the LLM scorer from a plain Python function into a small LangGraph graph, to demonstrate hands-on experience with a named agent framework from the JD. Keep the scope tight. This is interview signal, not a redesign.

**Outputs:**
- `langgraph` added to `requirements.txt`
- `src/scoring.py` refactored so the scorer is implemented as a LangGraph graph with two nodes: a "score" node that calls Bedrock and produces the structured output, and a "self_check" node that re-reads the score and reasoning and flags low-confidence cases (e.g., score of 2 with weak justification, or score of 4 with thin reasoning) for human review
- A new `confidence_flag` field on `ScoredPair` in `src/schemas.py` to capture the self-check result
- The dashboard updated to show the confidence flag where present
- A short section in the README explaining the LangGraph refactor and the comparison story (built from scratch first to understand the primitives, then refactored the orchestration into LangGraph to compare)
- `DECISIONS.md` updated with the rationale for the refactor and what LangGraph gave you that the raw Bedrock SDK didn't

**Definition of done:** The pipeline runs end to end through the LangGraph-based scorer, the eval set still produces metrics comparable to the pre-refactor version (no regression in scoring quality), and the README's tech stack and architecture sections reflect the change.

**Key skills loaded:** none new, but read the LangGraph quickstart docs before starting.

**Hard rule:** Do not start Day 13 until Day 12 is fully complete. If the interview is within a week, skip this day entirely.

## Stretch additions (optional, post Day 13)

These are optional additions that close specific gaps against the JD. They run after all 13 planned days are complete and do not interfere with the core project. If the interview is imminent, skip these entirely.

### PyTorch / classical ML baseline (half-day, ~4-6 hours)

**Goal:** Add a PyTorch MLP to the eval comparison alongside the existing Day 8 logistic regression, to demonstrate applied ML and PyTorch experience from the JD. The whole point is the head-to-head comparison table, not a production scorer.

**Prerequisites:**
- `data/eval/labeled_pairs.json` exists with ~50 entries
- `data/eval/metrics_llm_judge_v2.json` and `data/eval/metrics_baseline.json` exist and are stable
- The LLM judge metrics are stable (no more prompt iteration planned)
- Day 8's logistic regression baseline is complete

**Scope:**
- Add `torch` to `requirements.txt`. `scikit-learn` is already present from Day 8.
- Build `src/pytorch_baseline.py` with a small MLP (one hidden layer, dropout, nothing fancy). Train on the same cached embeddings the Day 8 logistic regression uses (signal_embedding + system_embedding + element-wise product) plus the human labels from the eval set. Use the same cross-validation strategy as Day 8 (leave-one-out or 5-fold).
- The logistic regression from Day 8 stays as-is. The PyTorch MLP is a new, additional comparison arm.
- Both classifiers produce `ScoredPair` objects with the same interface as the LLM judge. Same inputs (retriever output), same labels, different scorer.
- Build `scripts/train_pytorch_baseline.py` that trains the MLP, runs cross-validated predictions, computes metrics, and writes to `data/eval/metrics_pytorch_mlp.json` and `data/eval/predictions_pytorch_mlp.json`.
- Update `scripts/compare_systems.py` to add a fourth column (PyTorch MLP) to the comparison table. Update `data/eval/COMPARISON.md`.
- Update the dashboard's Evaluation tab to show a 4-row comparison table: LLM judge (best version), logistic regression, PyTorch MLP. Add columns for precision at threshold >= 3 and cost per 100 pairs alongside the existing metrics.
- Add a `precision_at_threshold` function to `src/evaluation.py` for the new column.
- The story the table tells: the classifiers are much cheaper but miss urgent items, which is the wrong tradeoff for governance given the asymmetric error costs. This is an expected and defensible result, not a failure.

**Success criteria:**
- The comparison table in the dashboard has rows for all four scorers (LLM v1, LLM v2, logistic regression, PyTorch MLP)
- The table includes accuracy, recall at >= 3, precision at >= 3, and cost per 100 pairs
- The README's results and tech stack sections are updated to mention PyTorch
- The asymmetric-error tradeoff story lands clearly: cheaper scorers sacrifice recall on high-relevance items

**Definition of done:** The expanded comparison table is visible in the deployed dashboard, the metrics files exist for the PyTorch MLP, and the README reflects the additional baseline.

**Key skills loaded:** `eval-framework`.

**Hard rule:** This is strictly a comparison arm in the eval framework. The PyTorch MLP is not a production scorer, not a fallback, not an ensemble component, not a pre-filter. If you find yourself wiring it into the pipeline, stop.

---

## What's NOT in this plan (and why)

- **Authentication, user accounts, multi-tenancy.** Out of scope per `CLAUDE.md`. A portfolio project doesn't need these and they'd eat days.
- **Real-time signal ingestion.** The pipeline is batch. A scheduled run would be a nice "future work" bullet in the README but not a Week 1-2 build.
- **Multiple LLM providers or model A/B testing beyond Haiku vs Sonnet.** One model family, one judge, accessed via Bedrock. The comparison work is LLM judge vs trained classifier, not LLM A vs LLM B.
- **A separate severity dimension.** Folded into relevance per `DECISIONS.md`. Do not add it back.
- **Automated remediation.** Human-in-the-loop only, per `DECISIONS.md`. The agent suggests; humans decide.

## Risks to watch

1. **Day 3 takes longer than a day.** The LLM scorer is the hardest single piece of work. If Day 3 spills into Day 4, that's fine — push everything back a day. Don't compromise the scorer to save time.
2. **The eval set turns out to be unbalanced or boring.** If after Day 6 your labeled set has 60 zeros and 5 fours, the metrics on Day 7 won't be informative. Spend more time on stratified sampling than feels necessary.
3. **The baseline classifier wins.** This is fine and even good — it's a real result and it makes the project more credible, not less. The story becomes "I built both, measured both, and learned that for this task with this much data, a trained classifier is competitive with an LLM judge." That's a *better* interview story than "my LLM thing won." With only 50 labeled pairs the classifier may also just be too data-starved to compete fairly — that's also a fine finding to report.
4. **Streamlit Community Cloud deploy issues on Day 5.** Common problems: missing dependencies in `requirements.txt`, hardcoded local paths, files too large for the free tier. Test the deploy mid-Day-5, not at the end.
5. **Scope creep mid-week.** If you find yourself wanting to add a feature, write it down in a `FUTURE_WORK.md` file and keep building. Don't touch the daily scope mid-day.
