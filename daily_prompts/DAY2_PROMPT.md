# Claude Code prompt — Day 2: Retriever (embeddings + cosine similarity)

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Also read `PLAN.md` at the section for Day 2 so you have the full context for what we're building today and how it fits into the rest of the week. Then, in your own words, give me a 3-4 sentence summary of what Day 2 produces and how it fits between Day 1 and Day 3. Do not skip this step.

Once I confirm the summary, your task for Day 2 is to build the retrieval stage of the scoring pipeline. This is the cheap filter that runs before the expensive LLM scorer. The retriever computes cosine similarity between every signal and every system using sentence-transformer embeddings, and writes the results to disk.

## What to build

1. **Add the dependencies.** Update `requirements.txt` to include any new packages needed for this day. You should already have `sentence-transformers` from Day 1. Add `numpy` if it's not already pulled in transitively.

2. **Build `src/retrieval.py`** with three things:

   a. **An embedding function.** Loads `sentence-transformers/all-MiniLM-L6-v2` once (lazily, the first time it's called) and caches the model in a module-level variable. Takes a string and returns a numpy array. Don't reload the model on every call.

   b. **A disk cache for embeddings.** Cache key is the SHA-256 hash of the input text. Cache location is `data/cache/embeddings/`. The cache should be created if it doesn't exist. On a cache hit, return the stored embedding without recomputing. On a miss, compute, store, and return. The cache is what makes reruns instant — that's the whole point.

   c. **A function `compute_similarities(systems, signals) -> list[SimilarityPair]`** that, for every (signal, system) pair, computes cosine similarity between the signal embedding and the system embedding and returns a list of `SimilarityPair` objects.

   For the system text, concatenate: `purpose + " " + " ".join(data_inputs) + " " + " ".join(known_risks)`. For the signal text, concatenate `title + " " + description`. Embed each of those once per system/signal — do not re-embed inside the pair loop.

3. **Add `SimilarityPair` to `src/schemas.py`** as a Pydantic model with: `signal_id: str`, `system_id: str`, `cosine_similarity: float`. Keep it minimal — this is the intermediate output, not the final scored output.

4. **Build `scripts/run_retrieval.py`** as a CLI script that:
   - Loads the portfolio from `data/portfolio/systems.yaml`
   - Loads the signals from `data/signals/processed/aiid_signals.json`
   - Calls `compute_similarities`
   - Sorts the result so that pairs are grouped by `system_id` and within each system are sorted by `cosine_similarity` descending (this makes the JSON file readable when you open it)
   - Writes the result to `data/outputs/similarities.json`
   - Logs a summary at the end: number of signals, number of systems, number of pairs, time taken

5. **Sanity-check the output.** After the script runs, log the top 3 highest-similarity pairs for one system as a manual check. Pick the LLM-based system (the auto claims summarizer or the chatbot, whichever is in your YAML) and show its top 3. We want to see qualitatively that LLM-related signals are scoring high against LLM-based systems. If they're not, something is wrong with the embedding logic or the system text construction.

## Implementation notes

- **Cosine similarity formula:** Use `numpy` directly. `dot(a, b) / (norm(a) * norm(b))`. Don't pull in scipy or scikit-learn just for this.

- **Cache file format:** Save each embedding as a `.npy` file named by the hash. Loading and saving `.npy` is fast and lossless.

- **Logging:** Use the `logging` module. Configure a root logger at the top of `scripts/run_retrieval.py` with a clean format. No `print` statements.

- **No global state.** The model cache lives inside `src/retrieval.py` as a module-level variable, but the actual embedding logic should be pure functions that take inputs and return outputs.

- **Type hints everywhere.** `from __future__ import annotations` at the top of every new file.

- **Comments:** Skip the obvious. Explain the cosine similarity choice, the cache key choice, and the system-text construction choice. Those are the non-obvious decisions.

## Definition of done

- `python scripts/run_retrieval.py` runs without errors and produces `data/outputs/similarities.json`
- The file contains all (signal, system) pairs with their cosine similarities
- Re-running the script is noticeably faster the second time (cache hit)
- The top-3 sanity check for the LLM system shows qualitatively reasonable matches
- No new dependencies beyond what's listed above

## Scope guardrails

- **Do not** call any LLMs. No Anthropic API calls. The retriever is purely embedding-based.
- **Do not** add any filtering or thresholding logic in this script. The full similarity matrix is the output. Filtering happens in Day 3 inside the scorer.
- **Do not** modify the Day 1 files (portfolio loader, signal ingestion, schemas) except to add `SimilarityPair` to `schemas.py`.
- **Do not** add scoring, justification, or any LLM-related fields to the output. Cosine similarity only.
- **Do not** start writing the Day 3 scorer.

## Skills to load

None today. Day 2 is straightforward enough that no skill files apply. If something feels uncertain, ask me before guessing.

When you're done, give me a short summary of: (1) what you built, (2) any decisions you made that weren't in this prompt, (3) the top-3 sanity check output for the LLM system, and (4) any concerns about Day 3.
