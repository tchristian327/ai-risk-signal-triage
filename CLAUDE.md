# CLAUDE.md

This file is read automatically by Claude Code at the start of every session in this repo. It contains the persistent context you need to work on this project effectively. Read it in full before doing anything.

## Project one-liner

An agentic triage system that scans external AI risk signals (incidents, regulations, research), scores their relevance to a company's AI portfolio, and produces a prioritized digest with suggested actions for model owners. Built as a portfolio project to demonstrate fit for a Data Scientist role on Allstate's AI Risk, Governance and Research team.

## Why this project exists

This is a job-search portfolio project, not a production system. The target audience is an interviewer on Allstate's AI Risk, Governance and Research team. The project needs to:

1. Demonstrate data science rigor (measurement, evaluation, comparison of approaches)
2. Demonstrate applied AI engineering (agent design, LLM orchestration, structured outputs)
3. Tell a clear governance story that an Enterprise Risk professional recognizes as legitimate
4. Be deployable and shareable via a public URL
5. Be intuitive enough that a non-technical governance lead could grasp its value in under a minute

Every design decision should be checked against those five goals. If a feature doesn't serve at least one of them, we don't build it.

## Core concept

The system has two kinds of inputs:

1. **Portfolio** — a static YAML file describing 5-8 fictional AI systems at an insurance company. Each system has a name, purpose, model type, data inputs, users, deployment context, and known risks. This is the "ground" the agent reasons against.

2. **Signals** — real documents from two sources: (1) AI Incident Database (AIID) incidents, fetched via their public Algolia index; and (2) hand-curated governance signals (regulatory guidance, enforcement actions, public investigations in regulated industries), authored from real public material. Signal ids are prefixed `aiid-` or `gov-` to distinguish source. Each signal has an id, title, description, date, source, and URL.

For each (signal, system) pair, the agent produces:
- A relevance score from 0 to 4
- A 1-2 sentence justification
- A suggested next action for the model owner

The final output is a ranked digest showing the highest-relevance pairs, viewable in a Streamlit dashboard.

## Relevance rubric

This rubric is the single source of truth for labeling and scoring. It must appear verbatim in the scoring prompt.

- **0 — Unrelated.** The signal has no meaningful connection to this system.
- **1 — Tangential.** The signal mentions a broadly related topic but has no direct implication for this system.
- **2 — Worth a glance.** The signal raises a concern that could apply to this system under some conditions. Model owner should be aware.
- **3 — Action recommended.** The signal describes a risk, incident, or regulatory change that plausibly affects this system. Model owner should review and decide whether to act.
- **4 — Urgent review.** The signal describes a risk, incident, or regulatory change with direct and immediate implications for this system. Model owner should review this week.

Severity is folded into relevance deliberately. We are not modeling severity as a separate dimension.

## Asymmetric error costs

In AI governance, a **false negative** (missing a real risk) is far more costly than a **false positive** (flagging something irrelevant). All design choices — thresholds, prompts, evaluation metrics — should reflect this asymmetry. When in doubt, prefer recall over precision.

## Architecture

The system is split into three concerns, and this separation must be preserved:

- `src/` — all business logic (portfolio loading, ingestion, retrieval, scoring, pipeline orchestration). No Streamlit imports here. No LLM calls inside Streamlit.
- `app/` — Streamlit dashboard only. Loads precomputed outputs from disk and displays them. Never calls the pipeline directly.
- `scripts/` — CLI entry points that wire `src/` modules together and produce outputs to disk.

The Streamlit app must be fast and cheap because Streamlit reruns on every interaction. All expensive work (embeddings, LLM calls) happens in the pipeline, runs once, and writes results to `data/outputs/`. The dashboard only reads. The `Digest` schema is the contract between pipeline (producer) and dashboard (consumer) — changes to it require updating both sides.

**App layer conventions (established Day 5):**
- `requirements.txt` contains only app runtime deps (`streamlit`, `pydantic`). All pipeline deps (`boto3`, `sentence-transformers`, etc.) live in `requirements-pipeline.txt`. Streamlit Community Cloud reads only `requirements.txt` — adding pipeline deps there will blow the install size limit or slow deploys dramatically.
- All rendering helpers (`render_score_badge`, `render_pair_row`, `render_system_card`, `render_signal_card`, and any future ones) live in `app/components.py`. Never put multi-line render logic inline in `streamlit_app.py`.
- Do not remove the `sys.path.insert` at the top of `app/streamlit_app.py`. It is required for Streamlit Cloud to resolve `from src.schemas import ...`. See DECISIONS.md for why `pyproject.toml` alone was insufficient.

## Scoring pipeline

Two stages, in this order:

1. **Retriever (embeddings + cosine similarity).** For each system, compute an embedding from its concatenated text representation (purpose + data inputs + known risks). For each signal, compute an embedding from title + description. For each (signal, system) pair, compute cosine similarity. Use this to filter: only pairs above a threshold (tunable, start with 0.3) or in the top N get passed to the scorer. This is the cheap filter.

2. **Scorer (LLM-as-judge).** For each candidate pair, send a structured prompt to Claude via AWS Bedrock (default: Claude Haiku, switchable to Sonnet). The prompt includes the full rubric, the system card, the signal, and asks for: a brief reasoning step, a score 0-4, a justification, and a suggested action. Output must be parsed JSON. Use the Bedrock Converse API's native tool use with a Pydantic schema (see the `structured-outputs-anthropic` skill).

Embeddings: prefer a local sentence-transformers model (`all-MiniLM-L6-v2`) for speed, cost, and reproducibility. Cache embeddings to disk keyed on content hash so reruns are free.

An optional baseline classifier path exists for evaluation purposes only (see "Stretch additions" below). It consumes the same retriever output and produces `ScoredPair` objects with the same interface, but uses trained classifiers instead of the LLM judge. This is strictly a comparison arm in the eval framework, not a production scorer.

## Tech stack (locked in)

- **Language:** Python 3.11+
- **LLM:** Anthropic Claude via AWS Bedrock (`boto3` with the `bedrock-runtime` Converse API) as the primary access path. The direct `anthropic` Python SDK is kept as an optional local fallback when Bedrock access is slow or pending. The `LLM_PROVIDER` env var controls which client is used (default: `bedrock`). See the `structured-outputs-anthropic` skill for client setup patterns.
- **Embeddings:** `sentence-transformers` with `all-MiniLM-L6-v2`.
- **Classical ML:** `scikit-learn` for the Day 8 logistic regression baseline.
- **Structured output:** Pydantic models. Use the Bedrock Converse API's native tool use for structured output (same conceptual shape as the direct SDK's tool use, different request envelope).
- **Dashboard:** Streamlit.
- **Deployment:** Streamlit Community Cloud.
- **Package management:** `uv` if available, otherwise `pip` with `requirements.txt`.
- **Data formats:** YAML for the portfolio (human-edited), JSON for everything else (machine-written).
- **Infrastructure:** `aws-cdk-lib` (Python) for provisioning AWS resources. Added on Day 12.
- **Agent framework:** `langgraph` for the scorer refactor. Optional, added on Day 13.
- **ML baseline (stretch):** `torch` is added only if the optional PyTorch/classical ML stretch addition is built. The sklearn baseline from Day 8 is already in the core stack above.

Do not add dependencies beyond this list without asking first.

## Code conventions

- Type hints everywhere. Use `from __future__ import annotations` at the top of every file.
- Pydantic for all data schemas (portfolio entries, signals, scored pairs).
- Comments should explain non-obvious choices, not describe what the code does. Skip comments on obvious code. Explain anything non-trivial, especially scoring logic, prompt design choices, and asymmetric-error tradeoffs.
- Functions should be short and do one thing. If a function is longer than ~30 lines and it's not a prompt template, it's probably doing too much.
- Logging via the `logging` module, not `print`. Configure a root logger in each CLI script.
- No hardcoded paths. Use `pathlib.Path` and define a `PROJECT_ROOT` constant.
- Secrets only in `.env`, never in code or committed files. Include a `.env.example`.

## Production hygiene

The project includes a production hygiene pass (Day 11) covering observability, containerization, and CI. These exist to demonstrate the JD's signals around CI/CD, Docker, observability, and efficient LLM utilization. They are not load-bearing for the project's core data science work.

**Observability.** Each pipeline run tracks per-LLM-call metadata: tokens in, tokens out, latency (ms), estimated cost, model id, and timestamp. This is written to `data/outputs/run_metadata.json` alongside the digest. The Streamlit dashboard has a section that loads run metadata and shows totals (total tokens, total cost, average latency) plus a simple bar chart of cost per run. A monitoring agent that monitors itself is thematically aligned with the project.

**Docker.** A `Dockerfile` at the project root builds a working image capable of running the pipeline CLI scripts. It does not deploy anywhere; it just needs to build cleanly and run. A `.dockerignore` excludes unnecessary files.

**CI.** `.github/workflows/ci.yml` runs on push and PR: install dependencies, `ruff check`, `pytest`, and `docker build` to verify the image builds. No pipeline execution in CI (no AWS credentials, no point).

**Screenshots.** After the observability code is in place and at least one full pipeline run is complete, take screenshots of the AWS Bedrock CloudWatch metrics dashboard and save them to `docs/screenshots/`. Reference them in the README. This is a real artifact from real usage that ties the Bedrock decision to a visible deliverable.

## What NOT to do

- Do not call LLMs or run embeddings inside Streamlit. All expensive work is precomputed.
- Do not add severity as a separate dimension. It's folded into relevance per the rubric.
- Do not build authentication, user accounts, or databases. Files on disk are enough.
- Do not auto-update or rewrite governance artifacts. The agent is a triage and recommendation layer. Humans decide what changes to make.
- Do not scrape websites that don't have an obvious public data export. Start with the AI Incident Database GitHub repo for real structured data.
- Do not over-engineer the Streamlit app. Clean, simple, readable. One color for emphasis. No fancy animations.
- Do not add features that weren't in the plan without flagging them first. Scope creep is the single biggest risk to this project.
- Do not use trained classifiers as a fallback scorer, an ensemble component, or a pre-filter. The classifier baseline exists for evaluation comparison only. It is not part of the production scoring pipeline.

## Working rhythm

This project is built in focused day-sized chunks. Each day has a specific goal. When you receive a prompt for "day N", work only on that day's scope. If you finish early, stop and ask what's next rather than starting the next day on your own.

When in doubt about scope, defaults, or a design decision: ask before building. A 30-second clarifying question is cheaper than rebuilding something wrong.

## Stretch additions

These are optional additions built after all planned days (including Day 13) are complete. They close specific gaps against the target JD without interfering with the core project.

**PyTorch / classical ML baseline.** This addition extends the Day 8 logistic regression baseline by adding a small PyTorch MLP (one hidden layer, dropout) as a second classifier in the eval comparison. It depends on Day 8 being complete -- the sklearn baseline, the cached embeddings, and the labeled eval set are all prerequisites. Both classifiers are trained on the cached sentence-transformer embeddings plus human labels from the eval set. The output is an expanded comparison table in the dashboard's eval section with rows for LLM judge, logistic regression, PyTorch MLP, and columns for accuracy, recall at threshold >= 3, precision at threshold >= 3, and cost per 100 pairs. The story the table tells: the classifier is much cheaper but misses urgent items, which is the wrong tradeoff for governance given the asymmetric error costs. Estimated effort: one focused half-day (4-6 hours). Prerequisites: the labeled eval set must exist and LLM judge metrics must be stable.

## Related files

- `PLAN.md` — the master build plan covering all days (1-13) and the stretch addition. Referenced throughout this doc. Read it first to understand the overall shape.
- `DECISIONS.md` — running log of design decisions and their reasoning. Read this to understand *why* things are the way they are. Update it whenever a non-obvious decision is made.
- `README.md` — public-facing project description. Written for an interviewer viewing the repo. Updated at the end of week 1 and again at the end of week 2.
- `daily_prompts/DAY11_PROMPT.md` — the production hygiene pass (observability, Docker, CI). Runs after Day 10's polish work is complete.
- `daily_prompts/DAY12_PROMPT.md` — Infrastructure as Code with AWS CDK. Runs after Day 11.
- `daily_prompts/DAY13_PROMPT.md` — LangGraph refactor of the scorer (optional). Runs after Day 12.
- `daily_prompts/STRETCH_PYTORCH_PROMPT.md` — optional stretch addition. PyTorch MLP baseline for head-to-head comparison against the LLM judge in the eval section. Runs after Day 13 if time permits.

## Skills available in this project

This repo has four project-level skills in `.claude/skills/`. Load and apply them when their area of responsibility comes up in the current task. These skills contain procedural knowledge that applies across multiple days of work and should not be re-derived each time.

- **`llm-judge-scoring`** — Patterns for the LLM-as-judge scorer: rubric design, reasoning-before-score, temperature, consistency, known failure modes. Apply whenever working on any code that asks an LLM to assign a score or label. Primary use: Day 3 (building the scorer) and Week 2 (iterating on prompts after eval).
- **`structured-outputs-anthropic`** — Patterns for getting reliable typed output from the Anthropic API using Pydantic and tool use. Apply whenever writing any code that calls the Anthropic API and expects a structured response. Primary use: Day 3 and any later work that adds new LLM calls.
- **`eval-framework`** — Patterns for building the labeled eval set, computing metrics, comparing scoring systems, and error analysis. Apply whenever working on any evaluation, labeling, or measurement work. Primary use: all of Week 2.
- **`streamlit-analytics-dashboard`** — Patterns for building the Streamlit dashboard: load-cache-display, layout, metric presentation, honest-metrics principle. Apply whenever writing or modifying any file in `app/`. Primary use: Day 5 and Week 2 dashboard updates.

Load a skill by reading its `SKILL.md` file before doing work in that area. If you are working on something that touches multiple skills, load all the relevant ones. If you are unsure whether a skill applies, read its frontmatter description first — if the description matches the task, load the full skill.
