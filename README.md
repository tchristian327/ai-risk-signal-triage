# AI Risk Signal Triage Agent

**Live demo:** https://ai-risk-signal-triage-g4uzxrceevwufku4smbu2h.streamlit.app/

An agentic triage system that scans external AI risk signals — incidents, regulatory guidance, enforcement actions — scores their relevance to a portfolio of insurance AI systems, and produces a prioritized digest with suggested actions for model owners.

Built as a portfolio project demonstrating fit for a Data Scientist role on Allstate's AI Risk, Governance and Research team.

---

## What it does

1. **Ingests signals** from two sources: real incidents from the [AI Incident Database](https://incidentdatabase.ai/) and hand-curated governance signals (NAIC bulletins, NIST AI RMF, EU AI Act, CFPB/FTC guidance).
2. **Retrieves candidates** using sentence-transformer embeddings and cosine similarity to filter down to signal-system pairs worth scoring.
3. **Scores each pair** with an LLM judge (Claude Haiku via AWS Bedrock) using a 0–4 relevance rubric. Score 3 = action recommended, score 4 = urgent review.
4. **Surfaces a digest** in a Streamlit dashboard with three views: top pairs across the portfolio, signals by system, and systems affected by a given signal.

## Portfolio

Six fictional insurance AI systems: Auto Claims Summarizer, Claims Fraud Detector, Underwriting Risk Scorer, Customer Service Chatbot, Telematics Pricing Model, and Document OCR and Extraction Pipeline.

## Relevance rubric

| Score | Meaning |
|-------|---------|
| 0 | Unrelated |
| 1 | Tangential |
| 2 | Worth a glance |
| 3 | Action recommended |
| 4 | Urgent review |

Severity is folded into relevance deliberately. False negatives (missed risks) are far more costly than false positives in a governance context, so the system is calibrated toward recall.

## Tech stack

- **LLM:** Anthropic Claude (Haiku / Sonnet) via AWS Bedrock Converse API
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`), cached to disk
- **Structured output:** Pydantic + Bedrock native tool use
- **Dashboard:** Streamlit, deployed to Streamlit Community Cloud
- **ML baseline (Week 2):** scikit-learn logistic regression for eval comparison

## Running locally

```bash
# Install pipeline dependencies
pip install -r requirements-pipeline.txt

# Run the full pipeline (requires AWS credentials with Bedrock access)
python scripts/run_pipeline.py

# Launch the dashboard
streamlit run app/streamlit_app.py
```

The dashboard reads from `data/outputs/digest.json`. A precomputed digest is included in the repo so the dashboard runs without re-running the pipeline.

## Project structure

```
src/          Business logic: ingestion, retrieval, scoring, pipeline
app/          Streamlit dashboard (read-only, no LLM calls)
scripts/      CLI entry points
data/
  portfolio/  systems.yaml — the fictional AI portfolio
  signals/    ingested signals
  outputs/    digest.json — pipeline output read by the dashboard
```
