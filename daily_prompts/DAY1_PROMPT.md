# Claude Code kickoff prompt — Day 1

Copy everything below this line into your first Claude Code session. Paste it as a single message after you've already saved `CLAUDE.md` and `DECISIONS.md` into the repo root.

---

Before writing any code, read `CLAUDE.md` and `DECISIONS.md` in full. Then, in your own words, give me a 4-5 sentence summary of what we're building and why. Do not skip this step. I want to confirm you have the right mental model before you touch the filesystem.

Once I confirm the summary is correct, your task for Day 1 is to scaffold the repo and get a minimal end-to-end plumbing working. Specifically:

1. **Create the repo structure** exactly as described in `CLAUDE.md`:

   ```
   ├── data/
   │   ├── portfolio/
   │   ├── signals/
   │   │   ├── raw/
   │   │   └── processed/
   │   └── outputs/
   ├── src/
   │   └── agent/
   ├── app/
   ├── scripts/
   ├── .env.example
   ├── .gitignore
   ├── requirements.txt
   └── README.md
   ```

   Each directory that will eventually hold Python code should have an `__init__.py`. Add a short placeholder `README.md` that says this is a work in progress.

2. **Set up the Python environment.** Create `requirements.txt` with the minimum dependencies needed for Day 1 only: `boto3`, `anthropic`, `sentence-transformers`, `pydantic`, `pyyaml`, `python-dotenv`, `streamlit`. `boto3` is the primary LLM client (Bedrock); `anthropic` is kept as a local fallback. Do not add extras I didn't list. We'll add more as we need them.

3. **Write the portfolio YAML.** Create `data/portfolio/systems.yaml` with 6 fictional AI systems that a large insurance company might realistically run. Each system needs:
   - `id` (short slug)
   - `name`
   - `purpose` (1-2 sentences)
   - `model_type` (e.g., "LLM", "gradient boosted tree", "rules + ML ensemble")
   - `data_inputs` (list)
   - `users` (list — who interacts with the outputs)
   - `deployment_context` (1-2 sentences describing how outputs are used)
   - `known_risks` (list of 3-5 items)

   Make them realistic for an insurance company. Suggested systems (pick 6, feel free to substitute if you have better ideas):
   - Auto claims summarizer (LLM)
   - Fraud detection on auto claims (gradient boosted tree)
   - Underwriting risk scorer (ensemble)
   - Customer service chatbot (LLM)
   - Telematics-based pricing model (regression + ML)
   - Document OCR and extraction pipeline (vision + LLM)
   - Agent recommendation system (retrieval + ranker)
   - Call center sentiment analysis (fine-tuned classifier)

   Don't copy the name "Allstate" anywhere. These are fictional systems at a fictional insurance company. The flavor should be recognizable to an insurance professional without being a parody.

4. **Define the Pydantic data schemas.** In `src/schemas.py`, define:
   - `AISystem` — matches the YAML structure
   - `Signal` — id, title, description, date, source, source_url, tags (list[str])
   - `ScoredPair` — signal_id, system_id, cosine_similarity (float), relevance_score (int 0-4), justification (str), suggested_action (str), reasoning (str)

5. **Write a portfolio loader.** `src/portfolio.py` — a single function `load_portfolio(path: Path) -> list[AISystem]` that reads the YAML, validates against the Pydantic schema, and returns the list. Include a small CLI test at the bottom (`if __name__ == "__main__":`) that loads the portfolio and prints a summary.

6. **Write a stub signal loader.** `src/ingest.py` — for now, just a function `load_signals_from_json(path: Path) -> list[Signal]` that reads a JSON file of signals. Don't implement real ingestion yet; just the reader. We'll add the AI Incident Database fetcher on Day 1 as well in the next step.

7. **Write the AI Incident Database fetcher.** Still in `src/ingest.py`, add a function that fetches 40-60 real incidents from the AI Incident Database. Check if they have a public data export on GitHub (they do — look for `responsible-ai-collaborative/aiid`). Pull the incidents, normalize them into the `Signal` schema, and save to `data/signals/processed/aiid_signals.json`. Write a CLI script at `scripts/fetch_signals.py` that runs this fetcher.

   Important: if the GitHub repo is not structured how you expect, stop and ask me. Do not scrape the website as a fallback without confirming with me first.

8. **Write a stub pipeline runner.** `scripts/run_pipeline.py` — for Day 1, this just needs to load the portfolio and load the signals and print summary stats (number of systems, number of signals, a sample of each). It's just a plumbing check. Scoring comes on Days 2-3.

9. **Set up `.env.example` and `.gitignore`.** `.env.example` should have entries for: `LLM_PROVIDER=bedrock` (the toggle, default bedrock), `AWS_REGION=us-east-1`, `AWS_PROFILE=default`, and `ANTHROPIC_API_KEY=your_key_here` (for the fallback path). `.gitignore` should exclude `.env`, `.env.local`, `__pycache__/`, `.venv/`, `*.pyc`, and `data/signals/raw/` (raw data can be big, we only commit processed).

## Scope guardrails for Day 1

- **Do not** write any scoring logic. No embeddings, no LLM calls. That's Day 2 and Day 3.
- **Do not** write the Streamlit app yet. That's Day 5.
- **Do not** add dependencies beyond the list above.
- **Do not** skip the "summarize the project back to me" step at the start.
- **Do** ask before making any decision that isn't explicitly covered in `CLAUDE.md` or this prompt.
- **Do** stop and ask if the AI Incident Database structure doesn't match your expectations.

## Definition of done for Day 1

I should be able to:
1. Clone the repo
2. Run `pip install -r requirements.txt`
3. Run `python scripts/fetch_signals.py` and see 40-60 signals saved to disk
4. Run `python scripts/run_pipeline.py` and see a printed summary of the loaded portfolio and signals

That's it. End of Day 1 is plumbing. No magic yet.

When you're done, give me a short summary of what you built, any decisions you made that weren't in the prompt, and any questions or concerns about Day 2 and beyond.
