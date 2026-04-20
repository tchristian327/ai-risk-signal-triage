# Claude Code prompt -- Day 11: Production hygiene (observability, Docker, CI)

Before writing any code, re-read `CLAUDE.md` (especially the new "Production hygiene" section) and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 11. Then **load the `streamlit-analytics-dashboard` skill** by reading its `SKILL.md` file in full (you will add a new section to the dashboard today).

After reading those, in your own words, give me a 3-4 sentence summary of what we're building today, why it exists (hint: JD alignment, not functional necessity), and what the three phases are. Do not skip this step.

Once I confirm the summary, your task for Day 11 is to add three production engineering signals to the project: per-call LLM observability, a Dockerfile, and a CI pipeline. Then capture screenshots of real AWS Bedrock CloudWatch metrics as a visible deliverable. This work demonstrates the JD's CI/CD, containerization, and observability requirements without interfering with the core data science work from Days 1-10.

## Prerequisites

Confirm these exist before starting:
- `data/outputs/digest.json` (from a recent full pipeline run)
- `src/scoring.py` with the working scorer
- `src/pipeline.py` with the working pipeline
- The Streamlit dashboard is deployed and working

## Phase 1: Observability

**Goal:** Track per-LLM-call metadata so the pipeline operator (and interviewer) can see exactly what resources each run consumed.

1. **Add a `CallMetadata` schema to `src/schemas.py`:**

   ```python
   class CallMetadata(BaseModel):
       signal_id: str
       system_id: str
       model_id: str
       tokens_in: int
       tokens_out: int
       latency_ms: float
       estimated_cost_usd: float
       timestamp: str  # ISO 8601
   ```

2. **Update `RunMetadata` in `src/schemas.py`** to include:
   - `total_tokens_in: int`
   - `total_tokens_out: int`
   - `total_estimated_cost_usd: float`
   - `avg_latency_ms: float`
   - `call_metadata: list[CallMetadata]`

3. **Update `score_pair` in `src/scoring.py`** to return both the `LLMScoreOutput` and a `CallMetadata` object. Measure wall-clock time around the API call. Extract token counts from the Bedrock Converse response (`response["usage"]["inputTokens"]` and `response["usage"]["outputTokens"]`). Compute estimated cost from token counts and a hardcoded cost-per-token constant at the top of the file (use current Haiku pricing; a comment noting the source is enough).

4. **Update `src/pipeline.py`** to collect `CallMetadata` objects from each `score_pair` call, aggregate them into `RunMetadata`, and write the full metadata alongside the digest.

5. **Write `data/outputs/run_metadata.json`** as a separate file (not inside `digest.json`) containing the `RunMetadata` with the full `call_metadata` list. This keeps the digest file clean for the dashboard while giving the observability view its own data source.

6. **Add an observability section to the Streamlit dashboard.** This can be a new tab ("Run Metadata") or a section within the existing Overview tab. It should show:
   - Total tokens (in + out), total estimated cost, average latency per call as `st.metric` widgets
   - Number of pipeline runs and most recent run timestamp
   - A simple bar chart of cost per run (if multiple `run_metadata.json` files exist; if only one, just show the single-run stats)
   - Load the data via a `@st.cache_data` function with a try/except fallback ("Run metadata not yet available")

**Checkpoint:** Run the full pipeline once to verify `run_metadata.json` is populated. Check that the dashboard displays the new section correctly. Do not proceed to Phase 2 until this works.

## Phase 2: Docker

**Goal:** A Dockerfile that builds a working image capable of running the pipeline CLI scripts.

1. **Create `Dockerfile` at the project root:**
   - Base image: `python:3.11-slim`
   - Copy `requirements.txt` and install dependencies
   - Copy the project source (`src/`, `scripts/`, `data/portfolio/`, `data/signals/`)
   - Do not copy `.env`, `data/outputs/`, or `data/eval/` into the image
   - Set a working directory
   - Default command: `python scripts/run_pipeline.py --help` (show usage, not run the pipeline)

2. **Create `.dockerignore`** at the project root:
   ```
   .env
   .env.local
   .venv/
   __pycache__/
   *.pyc
   data/outputs/
   data/eval/
   .git/
   docs/screenshots/
   ```

3. **Test the build:** Run `docker build -t allstate-risk-agent .` and verify it completes without errors. You do not need to run the container with real AWS credentials; just verify the image builds and the dependencies install.

**Checkpoint:** `docker build` succeeds. Move to Phase 3.

## Phase 3: CI

**Goal:** A GitHub Actions workflow that runs basic checks on every push and PR.

1. **Create `.github/workflows/ci.yml`:**

   ```yaml
   name: CI

   on:
     push:
       branches: [main]
     pull_request:
       branches: [main]

   jobs:
     check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: "3.11"
         - name: Install dependencies
           run: pip install -r requirements.txt
         - name: Lint
           run: ruff check .
         - name: Test
           run: pytest --tb=short -q
         - name: Docker build
           run: docker build -t allstate-risk-agent .
   ```

2. **Create a minimal test file** at `tests/test_schemas.py` (or wherever makes sense) that imports the Pydantic schemas and validates a simple round-trip. This gives pytest something to run. Do not write extensive tests -- one or two that verify the schemas load and validate is enough for CI to have a real check.

3. **Create a `ruff.toml` or `pyproject.toml` `[tool.ruff]` section** with sensible defaults (line length 100, target Python 3.11). Run `ruff check .` locally and fix any issues before the CI config is finalized.

**Checkpoint:** `ruff check .` passes locally. `pytest` passes locally. CI config is committed.

## Phase 4: CloudWatch screenshots

**Goal:** Capture real evidence of AWS Bedrock usage from the pipeline run in Phase 1.

1. **Create `docs/screenshots/` directory.**

2. **Open the AWS Console**, navigate to CloudWatch, and find the Bedrock metrics for the region you ran the pipeline in. Take screenshots showing:
   - Invocation count over time
   - Token usage (input/output)
   - Latency distribution
   Save these as PNGs to `docs/screenshots/`.

3. **Reference the screenshots in the README.** Add a short line in the architecture or observability section like: "See `docs/screenshots/` for CloudWatch metrics from a real pipeline run."

This is a 15-minute task at the end of the day. It ties the Bedrock decision back to a visible, real-world artifact and is worth a lot in the interview.

## Implementation notes

- **Do not change the scoring logic, the rubric, the eval set, or the eval metrics.** Day 11 is pure infrastructure. If you find yourself modifying how scores are computed, stop.
- **The observability code instruments the existing pipeline.** It does not add a new pipeline or change the pipeline's behavior. It only adds measurement around what already exists.
- **Keep the Dockerfile simple.** No multi-stage builds, no health checks, no entrypoint scripts. Slim base, install deps, copy source. That's it.
- **Keep the CI simple.** One job, four steps. No matrix builds, no caching, no deployment. The point is to show the pattern exists, not to build production CI.
- **Type hints, comments, logging** -- same conventions as previous days.

## Definition of done

- `run_metadata.json` is populated after a pipeline run with per-call token counts, latencies, and costs
- The Streamlit dashboard shows the observability section with totals and a cost chart
- `docker build` succeeds locally
- `ruff check .` passes
- `pytest` passes with at least one real test
- `.github/workflows/ci.yml` exists and is syntactically valid
- `docs/screenshots/` contains at least one CloudWatch screenshot
- README references the screenshots

## Scope guardrails

- **Do not** add IaC (Terraform, CDK, CloudFormation) on Day 11. The Dockerfile is the only infrastructure artifact for this day. IaC is handled separately on Day 12.
- **Do not** add an agent framework (LangGraph, Strands, etc.) on Day 11. The from-scratch agent loop stays for this day. LangGraph is handled separately on Day 13.
- **Do not** add M365/low-code anything.
- **Do not** add deployment to ECS, Lambda, or any cloud runtime. The Docker image just needs to build.
- **Do not** modify the scoring prompt, the eval set, or the baseline classifier.
- **Do not** add features that weren't in this prompt. If you think of something, write it in `FUTURE_WORK.md`.

## Skills to load

- `streamlit-analytics-dashboard` -- for the observability section in the dashboard.

When you're done, give me a short summary of: (1) what you built in each phase, (2) the contents of `run_metadata.json` from the pipeline run, (3) whether CI passes locally, and (4) what CloudWatch screenshots you captured.
