# AI Risk Signal Triage

**[Live dashboard →](https://ai-risk-signal-triage-g4uzxrceevwufku4smbu2h.streamlit.app/)**

An agentic system for continuous oversight of external AI risk signals against an AI portfolio.

---

## What this is

Governance teams need to know when external AI risk signals — incident reports, regulatory guidance, enforcement actions — are relevant to their own deployed systems. This system ingests real signals from the AI Incident Database and hand-curated regulatory sources, scores each signal against a portfolio of insurance AI systems using an LLM judge, and produces a prioritized digest with suggested actions for model owners.

## Why I built it

Portfolio project for a Data Scientist role on Allstate's AI Risk, Governance and Research team. Built to demonstrate the specific combination the role calls for: agentic AI engineering, rigorous quantitative evaluation, and a working understanding of enterprise AI governance.

## Architecture

```
1. Portfolio      systems.yaml — 6 fictional insurance AI systems
2. Ingestion      AI Incident Database (Algolia) + hand-curated governance signals
3. Retrieval      sentence-transformers embeddings + cosine similarity → candidate filter
4. LLM judge      Claude Haiku via AWS Bedrock → 0–4 relevance score + reasoning + action
5. Output         digest.json written to disk
6. Dashboard      Streamlit reads digest.json — no LLM calls at render time
7. Observability  CallMetadata captures tokens/latency/cost per call → run_metadata.json
```

Per-call metrics (tokens in/out, latency, estimated cost, model id, timestamp) are captured at the API response layer in `src/scoring.py` and aggregated into `data/outputs/run_metadata.json` by the pipeline. The dashboard's **Run Metadata tab** surfaces per-run totals and a cost trend chart. Instrumenting at the application layer means metrics travel with the artifact and don't depend on AWS-side invocation logging being enabled.

## Evaluation methodology

I hand-labeled 49 (signal, system) pairs across the full 0–4 score range using stratified sampling on cosine similarity. I then built a logistic regression baseline on sentence-transformer embeddings for comparison, and iterated the LLM judge prompt once based on error analysis. All artifacts are in `data/eval/`. The headline metric is **recall at score ≥ 3** — the share of high-relevance pairs the system actually catches — because in governance, missed urgent signals cost more than false alarms.

## Results

| Metric | LLM Judge v1 | LLM Judge v2 | Baseline Classifier |
|--------|-------------|-------------|---------------------|
| Exact match accuracy | 22.4% | 28.6% | **36.7%** |
| Off-by-one accuracy | 65.3% | **75.5%** | 69.4% |
| Recall at score ≥ 3 | 33.3% (6/18) | 44.4% (8/18) | **61.1% (11/18)** |
| Avg latency / pair | 5,163 ms | 4,094 ms | **11 ms** |
| Cost / 1k pairs | $1.68 | $1.68 | **$0.00** |

The baseline is ~450× faster and free, but misses more than half of urgent signals — the wrong error direction for governance. The LLM judge costs more but is better calibrated and produces human-readable reasoning alongside the score.

## Honest limitations

- **Eval set:** 49 pairs, single labeler. Production needs multiple labelers and inter-rater reliability scoring.
- **Signal sources:** AI Incident Database skews toward consumer AI. Production would pull from regulatory RSS feeds, vendor advisories, and internal reports.
- **Fictional portfolio:** Accurate system cards require model owner interviews, not fabrication.
- **No judge drift monitoring:** Prompt behavior shifts across model versions; an eval re-run on each update would catch regressions.
- **Generic embeddings:** `all-MiniLM-L6-v2` wasn't trained on governance text. A domain-specific model would likely improve retrieval recall.
- **Recommends, doesn't act.** By design — governance teams are rightly cautious — but worth naming.

## What I'd do with another month

- Expand eval to 200+ pairs with two labelers; report Cohen's kappa
- Add a regulatory document feed (NIST AI RMF, EU AI Act, NAIC bulletins)
- Build a model owner feedback loop to refine scoring over time
- Add drift monitoring: re-run eval on each model update, alert on recall drops
- Replace the static portfolio with a connector to a real model registry

## How this maps to the Allstate AI Risk role

| JD requirement | Where it shows up |
|----------------|------------------|
| Continuous AI risk monitoring | Signal triage pipeline + digest dashboard |
| Agentic solutions | LLM judge loop in `src/scoring.py` and `src/pipeline.py` |
| Evaluation rigor | Hand-labeled eval set, metrics, baseline comparison in `data/eval/` |
| AWS Bedrock | `boto3` Converse API with native tool use in `src/scoring.py` |
| Observability | `CallMetadata` in `src/scoring.py` → `run_metadata.json` → Run Metadata dashboard tab |
| CI/CD | `.github/workflows/ci.yml` |
| Docker | `Dockerfile` at project root |
| Insurance domain | Fictional insurance AI portfolio in `data/portfolio/systems.yaml` |
| Stakeholder communication | Streamlit dashboard with the Evaluation tab |

## Tech stack

Python 3.11 · Anthropic Claude Haiku via AWS Bedrock · `sentence-transformers` · scikit-learn · Pydantic · Streamlit · Docker · GitHub Actions CI · Streamlit Community Cloud

## Repo structure

```
src/        Business logic: ingestion, retrieval, scoring, pipeline, evaluation
app/        Streamlit dashboard (read-only)
scripts/    CLI entry points
data/
  portfolio/  systems.yaml
  outputs/    digest.json — pipeline output
  eval/       labels, metrics, error analysis, comparison
infra/      AWS CDK stack (IAM + S3)
.github/    CI workflow
```

## How to run locally

```bash
pip install -r requirements-pipeline.txt
python scripts/run_pipeline.py      # requires AWS credentials with Bedrock access
streamlit run app/streamlit_app.py
```

A precomputed `digest.json` is included so the dashboard runs without re-running the pipeline.

---

*Built with assistance from Claude Code (Anthropic).*
