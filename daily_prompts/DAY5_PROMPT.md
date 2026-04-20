# Claude Code prompt — Day 5: Streamlit dashboard and deployment

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 5. Then **load the `streamlit-analytics-dashboard` skill** by reading its `SKILL.md` file in full. This skill applies heavily today and you should not start coding until you have read it.

After reading those, in your own words, give me a 4-5 sentence summary of what we're building today, what the architectural rule is (about what the app can and cannot do), and the three main views the dashboard needs. Do not skip this step.

Once I confirm the summary, your task for Day 5 is to build a clean, deployable Streamlit dashboard that loads `digest.json` and presents it in three views. Then deploy it to Streamlit Community Cloud and verify the public URL works.

## What to build

1. **Add `streamlit` to `requirements.txt`** if it isn't already there from Day 1.

2. **Build `app/streamlit_app.py`** as the entry point. The structure:

   a. **Page config at the very top.** `st.set_page_config(page_title="AI Risk Signal Triage", page_icon="🛡", layout="wide")`. This must be the first Streamlit call in the file, before any imports that might call Streamlit internally.

   b. **A cached data loader.** Use `@st.cache_data` on a function that loads `data/outputs/digest.json` from disk and validates it against the `Digest` Pydantic model. Return the validated `Digest` object. Wrap the load in try/except and show a clean error message if the file is missing or invalid — do not let a stack trace show in the deployed app.

   c. **A header section.** A title (the page title), a one-line subtitle ("Continuous oversight of external AI risk signals against an insurance company portfolio"), and a small metadata strip showing the run timestamp, model used, and pair counts pulled from `Digest.metadata`.

   d. **Three tabs using `st.tabs`.** The tabs are: "Overview", "By System", "By Signal". (The Evaluation tab gets added on Day 10. Do not add a placeholder for it today — leave it out entirely.)

3. **Build the Overview tab.** Top-down:
   - Three metrics in `st.columns(3)`: number of systems, number of signals, number of high-relevance pairs (score >= 3)
   - A "Top relevant pairs" leaderboard showing the 10 highest-scored pairs across the whole portfolio. For each pair: the score badge, the signal title, the system name, and the LLM justification (truncated to ~150 chars with an expander for the full reasoning)
   - At the bottom of the tab, a small "About this project" section (4 sentences max) with a link placeholder for the GitHub repo (you can use a TODO link, I'll fill it in when I push to GitHub)

4. **Build the By System tab.**
   - A `st.selectbox` to pick a system from the portfolio
   - The system card displayed: name, purpose, model type, data inputs, users, deployment context, known risks
   - Below the card, the top 10 signals for that system sorted by score descending. Same row layout as the Overview leaderboard (badge, title, justification, expander for full details)
   - If a system has no scored pairs (because nothing passed the retrieval filter), show a friendly "No scored signals for this system in the latest run" message

5. **Build the By Signal tab.**
   - A `st.selectbox` to pick a signal from the loaded signals (sort the dropdown alphabetically by title)
   - The signal details displayed: title, source, date, full description, source URL as a clickable link
   - Below, the systems that have scored pairs for this signal, sorted by score descending. For each: system name, score badge, justification, expander for full reasoning
   - Same empty-state handling as the By System tab

6. **Score badges.** Build a small helper function `render_score_badge(score: int)` that returns the right colored badge for each score per the `streamlit-analytics-dashboard` skill (0-1 muted gray, 2 yellow, 3 orange, 4 red). Use `st.markdown` with HTML and inline styles, or use Streamlit's native colored text features if they're cleaner. Don't reach for a charting library — these are just colored boxes with a number.

7. **Code organization.** All the rendering helpers (`render_score_badge`, `render_pair_row`, `render_system_card`, `render_signal_card`) live in `app/components.py`. The main `streamlit_app.py` imports them and orchestrates the layout. Do not put inline 50-line render functions in `streamlit_app.py` — it gets unreadable fast.

8. **Test locally.** Run `streamlit run app/streamlit_app.py` and click through every tab, every dropdown option, every expander. Catch any rendering bugs.

9. **Deploy to Streamlit Community Cloud.**
   - The repo must be public on GitHub. If it isn't yet, prompt me to push it and confirm the URL.
   - Connect the repo to Streamlit Community Cloud at https://share.streamlit.io
   - Set the app entry point to `app/streamlit_app.py`
   - Set the Python version to 3.11 in the deploy settings
   - Do *not* add any secrets or environment variables to the deploy — the app reads from `data/outputs/digest.json` which is already in the repo, and no API keys are needed at runtime
   - Verify the deploy succeeds and the public URL works
   - Update `README.md` with the public URL

   **Important:** test the deploy *mid-day*, not at the end. The first deploy almost always fails for one of the reasons listed in the `streamlit-analytics-dashboard` skill (missing dependency, hardcoded path, file too large). If you wait until the end of the day to deploy, you'll be debugging deploy issues in the dark.

## Implementation notes

- **The dashboard never imports from `src/scoring.py`, `src/retrieval.py`, or `src/pipeline.py`.** The only `src/` import the dashboard needs is `src/schemas.py` (for the Pydantic models). If you find yourself importing anything else, stop and ask — you're about to violate the architectural rule.

- **Caching scope.** `@st.cache_data` on the loader is enough. Don't cache anything else. Don't reach for `@st.cache_resource`.

- **No file writes from the app.** The app is read-only. If you find yourself wanting to write something to disk, stop.

- **No animations, no balloons, no progress bars on data loads.** The data loads in <1 second. A progress bar would be silly.

- **Hardcoded paths are deploy-killers.** Use `pathlib.Path` relative to the project root. The project root can be computed as `Path(__file__).parent.parent` from `streamlit_app.py`.

- **Test on a different browser before declaring done.** Streamlit's dev server can hide bugs that show up in the deployed version. Open the local app in an incognito window before deploying.

## Definition of done

- `streamlit run app/streamlit_app.py` runs locally and all three tabs work end-to-end
- Every dropdown option produces a valid view
- The deployed app at the Streamlit Community Cloud URL works and matches the local version
- README.md has the public URL added
- I can send the URL to someone and they will see scored signals against the portfolio without any explanation from me
- The data load is cached so interactions feel instant after the first load

## Scope guardrails

- **Do not** add any LLM calls, embedding calls, or pipeline calls to the app. Architectural rule.
- **Do not** add an "Evaluation" tab today. That's Day 10.
- **Do not** add authentication, user accounts, settings, or configuration UI. Out of scope.
- **Do not** use a charting library (no Plotly, Altair, Matplotlib) for the score badges. Plain HTML/CSS. Charts may come on Day 10 for the eval view, not today.
- **Do not** add a "refresh" or "re-run" button. The app is a viewer. The pipeline runs separately.
- **Do not** style with custom CSS beyond what's needed for the score badges. Streamlit's defaults are fine for layout.

## Skills to load

- `streamlit-analytics-dashboard` — apply the load-cache-display pattern, the layout rules, the things-to-avoid list, and the deployment notes.

When you're done, give me a short summary of: (1) what you built, (2) the public URL, (3) any deploy issues you hit and how you resolved them, (4) anything you'd want to improve in a polish pass on Day 10, and (5) any concerns about Week 2.
