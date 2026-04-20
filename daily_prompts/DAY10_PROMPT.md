# Claude Code prompt — Day 10: Polish, evaluation view, and the README

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 10. Then **load the `streamlit-analytics-dashboard` skill** by reading its `SKILL.md` file in full.

After reading those, in your own words, give me a 4-5 sentence summary of what we're doing today, what the evaluation view in the dashboard should communicate, and what the README is for. Do not skip this step.

Once I confirm the summary, your task for Day 10 is to bring everything together into a project I can send to a recruiter or interviewer with confidence. Three things: add an evaluation view to the dashboard, write the README, and re-deploy.

## Prerequisites

Confirm these files exist before starting:
- `data/outputs/digest.json` (from a recent pipeline run)
- `data/eval/metrics_llm_judge_v1.json`
- `data/eval/metrics_llm_judge_v2.json`
- `data/eval/metrics_baseline.json`
- `data/eval/COMPARISON.md`
- `data/eval/PROMPT_CHANGELOG.md`
- `data/eval/REPORT_WEEK2.md` with all my prose sections filled in

If any are missing, stop and ask. The eval view depends on having all the metrics files.

## What to build

### Part 1: The evaluation view in the dashboard

1. **Build a new view** in `app/streamlit_app.py`. Add a fourth tab to `st.tabs`: "Overview", "By System", "By Signal", "Evaluation".

2. **Build the eval view contents.** Top-down structure:

   a. **Headline at the top**: "How well does this work?" as a section header. Below it, one sentence in plain language: "Measured against 50 hand-labeled (signal, system) pairs across the full 0-4 score range."

   b. **The comparison table.** A `st.dataframe` or styled HTML table with rows = metrics and columns = (LLM judge v1, LLM judge v2, Baseline classifier). Include the same metrics from `COMPARISON.md`: exact match, off-by-one, recall at score >= 3, latency per pair, cost per 1k pairs. Highlight the winner of each row somehow (bold the value, or add a small marker). Be honest — if the baseline wins on cost, show that.

   c. **The headline metric, called out.** Below the table, a single `st.metric` or large-text element showing "Recall at score ≥ 3 (LLM judge v2): X% (Y of Z high-relevance pairs caught)". This is the most important number for this project's stated values, and it deserves to be visually prominent.

   d. **The confusion matrix.** Show the v2 confusion matrix as a 5x5 grid. Build a small helper function in `app/components.py` that renders it as a styled HTML table with the diagonal highlighted. Rows = predicted score, columns = human label, cells = counts.

   e. **A "what these numbers mean" prose section.** ~3-4 sentences in my voice (you'll write a draft, I'll edit). Cover: what the recall metric tells us about the project's stated value (catching high-relevance signals), where the LLM judge wins vs the baseline, and the tradeoff (LLM judge is slower and costs money, baseline is fast and free but less accurate). Pull from `REPORT_WEEK2.md`.

   f. **A "limitations" subsection.** Three bullets, condensed from the README's honest-limitations section (which you'll write in Part 2). Examples: "Eval set is 50 pairs labeled by a single human", "Signals come from one source", "The portfolio is fictional". Bullets should be 1 line each.

3. **Add a `load_eval_data` cached function** to `app/streamlit_app.py` that loads all three metrics files plus the comparison markdown. Cache it with `@st.cache_data`. Wrap in try/except — if any file is missing, show a clean "Eval data not yet available, run the eval scripts to populate" message in the eval tab and don't crash the rest of the app.

### Part 2: The README

Write `README.md` for an interviewer. They will read this in 2 minutes and decide whether to look at the dashboard. Sections in this exact order:

1. **Title and one-line description.** "AI Risk Signal Triage — an agentic system for continuous oversight of external AI risk signals against an AI portfolio."

2. **Live dashboard link.** Right at the top, prominently. The interviewer should not have to scroll to find it. Use the public Streamlit Community Cloud URL.

3. **What this is** (3-4 sentences). Plain language. Explain the problem (governance teams need to know when external AI risk signals affect their own systems) and the solution (this system scans signals, scores their relevance, and produces a prioritized digest).

4. **Why I built it.** Two sentences. Cover: it's a portfolio project for a data science role on an AI risk and governance team, and it's designed to demonstrate fit for that specific kind of work.

5. **Architecture.** A short section with either a small ASCII diagram or a numbered list showing the pipeline: (1) Portfolio loaded from YAML, (2) Signals fetched from AI Incident Database, (3) Cosine similarity retrieval filters candidates, (4) LLM judge (Claude Haiku) scores survivors against the rubric, (5) Outputs written to JSON, (6) Streamlit dashboard renders the digest.

6. **Evaluation methodology.** One paragraph. Explain: hand-labeled 50 pairs across the full score range using stratified sampling on cosine similarity, computed metrics on the LLM judge, built a trained-classifier baseline for comparison, iterated the LLM judge prompt once based on error analysis. Reference the `data/eval/` folder.

7. **Results.** A small table showing the same comparison from the dashboard's eval view. Just the numbers. Two sentences after the table summarizing the takeaway in plain language.

8. **Honest limitations.** A bulleted list. ~5-7 bullets. Examples (write your own, these are illustrative):
   - "Eval set is 50 hand-labeled pairs from a single labeler. A real production system would need multiple labelers and inter-rater reliability scoring."
   - "Signals come from one public source (AI Incident Database). A production system would pull from regulatory feeds, vendor advisories, and internal incident reports."
   - "The portfolio is fictional. Real governance work would involve interviewing model owners to build accurate system cards."
   - "No drift detection on the LLM judge over time."
   - "The retriever uses generic sentence embeddings. A domain-specific embedding model trained on AI governance text would likely improve recall."
   - "The agent surfaces and recommends but does not act. By design, but worth naming."

   This section is the move that makes the project read as senior. Spend time on it. Be specific. Generic limitations like "could be more accurate" are worse than nothing.

9. **What I'd do with another month.** ~4-5 bullets. The point of this section is to show I understand the full path from prototype to production. Examples:
   - Expand the eval set to 200+ pairs with multiple labelers
   - Add a regulatory document feed (e.g., NIST AI RMF updates, EU AI Act commentary)
   - Build a feedback loop where model owners can mark suggestions as useful or not
   - Add drift monitoring on the LLM judge
   - Replace the static portfolio with a connector to a real model registry

10. **Tech stack.** A short bulleted list: Python 3.11, Anthropic Claude (Haiku) via AWS Bedrock (Converse API), sentence-transformers for embeddings, scikit-learn for the baseline, Pydantic for schemas, Streamlit for the dashboard, Docker, GitHub Actions CI, deployed on Streamlit Community Cloud.

11. **How this project maps to the Allstate AI Risk, Governance and Research role.** A short table or bulleted list connecting each major JD requirement to the specific part of the repo where it shows up. Cover at minimum:
    - Continuous AI risk monitoring -> the signal triage pipeline and dashboard
    - Agentic solutions -> the from-scratch agent loop in `src/scoring.py` and `src/pipeline.py`
    - Evaluation rigor -> hand-labeled eval set, metrics, baseline comparison in `data/eval/`
    - AWS Bedrock -> LLM access via `boto3` Converse API in `src/scoring.py`
    - Observability -> per-call token/latency tracking, `run_metadata.json`, dashboard section
    - CI/CD -> `.github/workflows/ci.yml`
    - Docker -> `Dockerfile`
    - Insurance domain -> fictional insurance AI portfolio in `data/portfolio/systems.yaml`
    - Stakeholder communication -> the Streamlit dashboard and its evaluation view

12. **Repo structure.** A small tree showing the top-level directories with one-line descriptions of each. Don't dump every file -- just enough so a reader knows where to look.

13. **How to run it locally.** Three commands: clone, install, run pipeline, run dashboard. Brief.

14. **Acknowledgements.** Optional one-line note: "Built with assistance from Claude Code (Anthropic)." This is honest and reads well -- interviewers know AI-assisted development is the norm now and respect candidates who name it explicitly.

The README should be tight. ~400-600 words total. Anything longer and the interviewer stops reading.

### Part 3: Re-deploy

1. **Push everything to GitHub.** Confirm the repo is public.
2. **Trigger a re-deploy** on Streamlit Community Cloud. It should auto-deploy on push, but verify.
3. **Test the deployed app.** Click through every tab including the new eval view. Confirm the eval data loads.
4. **Add the public URL** to the README if it isn't already there.
5. **Final commit.** Commit message: "Day 10: eval view, README, polish".

## Implementation notes

- **The eval view uses cached data only.** Same architectural rule as the rest of the app. No LLM calls, no recomputation.

- **Don't use a charting library for the comparison table or confusion matrix.** Plain HTML/CSS or `st.dataframe` is enough. The bar for visual polish is "professional, not flashy."

- **Headline metric callout.** Use Streamlit's native `st.metric` widget for this — it's the one place in the app where `st.metric` is exactly the right tool because it's literally one big number.

- **README review.** After you write the README, re-read it as if you were an interviewer who has 2 minutes. Would you want to click the dashboard link? If not, fix the top.

- **Don't add new features.** Day 10 is polish. If you find yourself wanting to add a new view, a new metric, or a new section to the dashboard, write it down in `FUTURE_WORK.md` and move on.

## Definition of done

- The Evaluation tab works in the local app and on the deployed app
- The comparison table shows three columns clearly
- The headline metric callout is prominent
- The confusion matrix renders cleanly
- README.md is written in the structure above, between 400-600 words
- The deployed app at the Streamlit Community Cloud URL works end-to-end
- The repo is public on GitHub
- All my prose sections in `REPORT_WEEK2.md` are referenced or quoted appropriately in the README
- I can paste a single GitHub link into a recruiter message and feel good about it

## Scope guardrails

- **Do not** add any new analytical features. Polish, not new work.
- **Do not** modify the LLM judge, the rubric, the eval set, or the baseline.
- **Do not** add charts, animations, or fancy visualizations.
- **Do not** write more than ~600 words of README.
- **Do not** add new dependencies.
- **Do not** rewrite the prose sections of `REPORT_WEEK2.md` — they're mine.
- **Do not** delete any of the eval artifacts. Everything stays in `data/eval/` for the interviewer to inspect if they want to dig in.

## Skills to load

- `streamlit-analytics-dashboard` — apply the eval view structure from the skill, the metric presentation rules, and the deployment notes.

When you're done, give me a short summary of: (1) what changed in the dashboard, (2) the README in full so I can read it before you push, (3) a screenshot or text description of the deployed eval view, and (4) anything you'd recommend I do before sending this to a recruiter.
