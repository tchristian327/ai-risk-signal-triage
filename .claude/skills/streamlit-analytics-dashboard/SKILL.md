# Streamlit Analytics Dashboard

Patterns for building and maintaining the Streamlit dashboard. Apply whenever writing or modifying any file in `app/`.

## Load-cache-display architecture

The dashboard is a pure display layer. It loads precomputed data from disk and renders it. No LLM calls, no embeddings, no pipeline logic. This rule is absolute.

```python
@st.cache_data
def load_digest() -> dict:
    path = PROJECT_ROOT / "data" / "outputs" / "digest.json"
    with open(path) as f:
        return json.load(f)
```

Every data load function uses `@st.cache_data`. Streamlit reruns the entire script on every interaction, so anything not cached runs again. Expensive loads without caching will make the app feel broken.

### Fallback pattern for optional data

Some data (eval metrics, run metadata) may not exist yet if the user hasn't run the corresponding scripts. Use try/except with a clean fallback:

```python
@st.cache_data
def load_eval_data() -> dict | None:
    try:
        # load metrics files
        return {...}
    except FileNotFoundError:
        return None
```

In the UI, check the return value and show a clean message ("Eval data not yet available. Run the eval scripts to populate.") instead of crashing the app.

## Layout principles

1. **Three-tab structure (Week 1), four tabs (Week 2).** Overview, By System, By Signal, and (after Day 10) Evaluation. Use `st.tabs()`. Do not use sidebar navigation; tabs are simpler and more discoverable.

2. **Score badges.** Every scored pair shows a colored badge next to its score. Color mapping:
   - 0-1: gray (muted, low relevance)
   - 2: yellow (worth a glance)
   - 3: orange (action recommended)
   - 4: red (urgent review)

   Implement as a small helper function in `app/components.py` that returns styled HTML.

3. **Expandable details.** Reasoning and justification are useful but verbose. Show a truncated version (first ~100 chars of justification) with an `st.expander` for the full text. Do not dump walls of LLM reasoning onto the main view.

4. **System cards and signal cards.** Helper functions in `app/components.py` that render structured info blocks. Keep them consistent across tabs.

5. **One accent color.** Do not use a rainbow palette. Pick one accent color and use it for all emphasis elements (score badges, metric highlights). Everything else is neutral.

## Metric presentation

### The honest-metrics principle

Every number shown in the dashboard should be understandable by a non-technical governance lead in under 5 seconds. Rules:

- Show counts alongside percentages: "85% (17 of 20)" not just "85%"
- Label metrics in plain language: "High-relevance signals caught" not "Recall at threshold >= 3"
- If a metric requires explanation, add a one-sentence tooltip or caption
- Do not show metrics without context. "Exact match: 62%" means nothing without "out of 50 hand-labeled pairs"

### The comparison table (eval view)

Rows = metrics, columns = scoring systems (LLM v1, LLM v2, Baseline). Highlight the best value in each row. Use `st.dataframe` or a simple HTML table. Do not use a charting library for this; a table is clearer.

### The headline metric callout

Use `st.metric` for exactly one metric: recall at score >= 3 for the best LLM version. This is the project's north star metric and deserves to be visually prominent. Show it as "X% (Y of Z caught)" with a delta if comparing v1 to v2.

## Run metadata display (Day 11)

After observability is added, the dashboard gets a new section (or tab) showing pipeline run metadata:
- Total tokens used, total estimated cost, average latency per LLM call
- Number of pipeline runs, most recent run timestamp
- A simple bar chart of cost per run (if multiple runs exist)

Use `st.bar_chart` or `st.pyplot` for the bar chart. Keep it simple.

## Deployment notes (Streamlit Community Cloud)

Common pitfalls:
- **Missing dependencies.** Every import must be in `requirements.txt`. Test the deploy mid-day, not at the end.
- **Hardcoded local paths.** Use `pathlib.Path` relative to the project root. Never use absolute paths.
- **Large data files.** The free tier has limited storage. `digest.json` and the eval files should be well under the limit, but don't commit raw data or large caches.
- **Python version.** Specify Python 3.11 in the Streamlit Cloud config.
- **No secrets needed.** The dashboard reads from disk. No API keys, no environment variables.
- **Auto-deploy on push.** Connect the GitHub repo to Streamlit Cloud. Every push to main triggers a redeploy. Verify after each push.

## File structure

```
app/
  __init__.py
  streamlit_app.py    # entry point, page config, tabs, data loading
  components.py       # render_score_badge, render_pair_row, render_system_card, etc.
```

Keep `streamlit_app.py` as the orchestrator (loads data, builds tabs) and `components.py` as the rendering helpers. Do not put business logic in either file.
