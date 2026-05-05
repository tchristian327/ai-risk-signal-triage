# DECISIONS.md

A running log of design decisions made on this project and the reasoning behind them. The point of this file is that six weeks from now, when I'm in an interview and someone asks "why did you do it this way," I have a written answer. Also useful for Claude Code to understand the *why* behind conventions in `CLAUDE.md`.

New decisions get appended to the bottom with a date. Do not edit old entries — if a decision is reversed, add a new entry that references the old one.

---

## 2026-04-08 — Project scope and framing

**Decision:** Build an agent that scores the relevance of external AI risk signals to a portfolio of fictional AI systems, and produces a ranked digest with suggested actions.

**Why:** The Allstate JD centers on "continuous, data-driven oversight" and "surfacing evidence of risk from external sources." This project is a concrete instance of that thesis, which matches the team's stated identity better than any of the alternatives (LLM production monitoring, agent auditing, auto-drafting risk assessments).

**Alternatives considered:**
- Production LLM monitoring — rejected because it requires a production LLM to monitor, which means most of the demo would be a fake target, not the monitoring logic itself.
- Agent auditing / red-teaming — rejected because it's more of a research project and harder to demo to a non-ML interviewer.
- Auto-drafting risk assessments — rejected because there's no agentic behavior or quantitative signal worth showing.

---

## 2026-04-08 — Relevance as a graded 0-4 score, severity folded in

**Decision:** Relevance is scored on a 0-4 integer scale. Severity is not a separate dimension.

**Why:** Simpler to label consistently, simpler to evaluate, and a graded score already captures "how much should I care" in a way users actually want. Splitting severity and relevance creates label ambiguity and doubles the labeling burden for marginal gain.

---

## 2026-04-08 — Real signals, hand-labeled eval set

**Decision:** Use real documents from the AI Incident Database (and a small number of real regulatory summaries) as the primary signal source and the eval set. Hand-label (signal, system) pairs. Use synthetic data only for augmenting adversarial edge cases in week 2.

**Why:** Pure synthetic eval data has a credibility problem — if I generate both the signals and the labels, I'm grading my own homework and an interviewer will clock it. Real signals are messy, heterogeneous, and force the system to handle realistic input. Hand-labeling is tedious but it's the only way to have a defensible eval set. Synthetic data is reserved for stress-testing specific failure modes (legal language, cross-domain analogies) that are rare in real data.

---

## 2026-04-08 — Two-stage scoring pipeline: embeddings retriever + LLM judge

**Decision:** The scoring pipeline has two stages. Stage 1 is cosine similarity on sentence-transformer embeddings, used as a cheap candidate filter. Stage 2 is an LLM-as-judge that scores the filtered candidates.

**Why:** Running an LLM on every (signal, system) pair is expensive and wasteful because most pairs are obviously unrelated. The retriever eliminates 70-90% of the workload cheaply. The LLM then spends its capacity on the interesting cases. This is the standard retrieve-then-rerank pattern used in production RAG systems, and it's worth showing that I know it.

---

## 2026-04-08 — Comparison baseline: trained classifier on embeddings

**Decision:** In week 2, build a second scoring system for comparison: a logistic regression (or lightGBM) trained on sentence-transformer embeddings of (signal, system) pairs, predicting the 0-4 relevance score.

**Why:** This is the data science move that makes the project a *data science* project and not just an engineering project. Comparing a hybrid LLM pipeline against a trained classifier baseline on the same hand-labeled eval set generates concrete metrics, forces honest analysis of where each approach wins, and gives me real talking points. "I built the production system as a hybrid retrieval and LLM-judge pipeline, and I benchmarked it against a trained classifier on the same eval set" is a sentence that makes this project unmistakably data science.

---

## 2026-04-08 — Human-in-the-loop posture (no auto-remediation)

**Decision:** The agent surfaces relevant signals and suggests next actions. It does not rewrite governance documents, update risk registers, or take any autonomous action on governance artifacts.

**Why:** Governance teams are extremely cautious about autonomous AI in governance workflows — it's exactly the kind of thing they exist to prevent. Framing the agent as a triage and recommendation layer matches the posture a governance team actually wants from AI tooling. Auto-remediation would be a credibility own-goal in the interview.

---

## 2026-04-08 — Streamlit for the dashboard

**Decision:** Use Streamlit for the frontend.

**Why:** Fastest path to a deployed, shareable app. Python-only, so it doesn't eat into time better spent on the core logic. Deployable to Streamlit Community Cloud for free. The "looks less polished" concern is real but manageable with simple, clean layout. Interviewers for data science roles expect Streamlit and don't hold it against candidates — in fact, many prefer it because it signals the candidate knew where to spend their time.

---

## 2026-04-08 — Anthropic Claude as the LLM judge

**Decision:** Use Anthropic's Claude (via the `anthropic` Python SDK) for the LLM-as-judge scorer.

**Why:** User has a Claude Pro subscription and existing familiarity with Anthropic models. No new billing or account setup required. Model choice (Haiku vs Sonnet) to be decided at build time based on cost and eval results.

---

## 2026-04-08 — Embeddings: local sentence-transformers, not OpenAI

**Decision:** Use `sentence-transformers/all-MiniLM-L6-v2` locally for embeddings.

**Why:** Free, deterministic, reproducible, and fast enough for a dataset this size. Avoids a second API dependency. Cache embeddings to disk keyed on content hash so reruns are free and iteration is fast.

---

## 2026-04-09 — AIID data source: Algolia search index, not GraphQL

**Decision:** Pull AIID signals from their public Algolia search index rather than the GraphQL API.

**Why:** The GraphQL endpoint returns 403 for non-browser origins. The Algolia index is the same data, exposed via publicly distributed keys in AIID's own repo, and is the same source AIID's own website uses. Signals are report-level (one incident can have multiple news reports); we deduplicate on `incident_id` and take the first English report. This means signal titles are news headlines rather than official incident titles, which is acceptable and arguably preferable for embedding-based retrieval (richer semantic content).

---

## 2026-04-12 — AWS Bedrock as the primary LLM access path

**Decision:** Call Claude through AWS Bedrock (`boto3` with the `bedrock-runtime` Converse API) as the primary client. Keep the direct `anthropic` SDK as an optional local fallback controlled by the `LLM_PROVIDER` env var.

**Why:** The Allstate JD explicitly lists "exposure or practical experience in AWS Bedrock" as a preferred qualification. Using Bedrock from the start demonstrates cloud-deployed LLM competency rather than just local SDK usage. This also aligns with prior Bedrock experience from Claritas, which makes it a natural talking point in the interview. The Converse API was chosen over `invoke_model` because it supports tool use natively, keeping the code nearly identical to what the direct SDK version would look like. The direct SDK fallback stays available for local dev speed when Bedrock access is pending or slow.

---

## 2026-04-12 — Production hygiene pass (observability, Docker, CI) added as Day 11

**Decision:** Add a post-Day-10 production hygiene pass covering per-call LLM observability, a Dockerfile, and a GitHub Actions CI workflow.

**Why:** The JD calls out "CI/CD pipelines, containerization (Docker), observability tools, and cloud security practices" as preferred qualifications. These artifacts exist to demonstrate those signals, not because the project needs them to function. Bundling them into a single day after the core data science work is complete keeps them from interfering with the scoring, eval, and iteration work that is the project's actual substance.

---

## 2026-04-16 — Similarity score range for all-MiniLM-L6-v2 on this domain

**Observation:** On the first real run, cosine similarities between system embeddings (purpose + data_inputs + known_risks) and signal embeddings (title + description) maxed out around 0.33 even for qualitatively strong matches. The full distribution runs roughly 0.10–0.33.

**Why it matters:** The 0.3 threshold in CLAUDE.md passes roughly the top third of signals per system (~20 of 60) into the LLM scorer. If Day 7 eval shows missed risks (false negatives), the first place to check is whether the retrieval threshold is cutting legitimate pairs before they reach the LLM — not whether the scoring prompt is wrong. Lower the threshold before blaming the prompt.

---

## 2026-04-18 — Corpus and portfolio vocabulary fix (Day 4.5)

**Decision:** Before building the Day 5 dashboard, expanded the signal corpus
with 18 hand-curated governance signals (NAIC model bulletins, NIST AI RMF 1.0,
EU AI Act articles, CFPB/FTC guidance, and public incidents in regulated
industries) and updated the portfolio's `known_risks` on all 6 systems to use
AI-safety-native terminology (adverse action, FCRA, disparate impact, fairness
audit, prompt injection, hallucination, concept drift, label leakage).

**Why:** The Day 4 diagnostic showed zero score-3 or score-4 pairs across 48
scored pairs. Root cause: the AIID corpus skews toward consumer AI incidents
(autonomous vehicles, social media, image generation) while the portfolio covers
internal insurance ML, and neither side's vocabulary was sharp enough to produce
high-relevance embedding matches.

**Result:** Cosine ceiling improved from 0.366 → 0.739. Pairs above the 0.3
retrieval threshold went from 9 → 118 out of 468 total (signal, system) pairs
in the similarity matrix. All 118 candidates were scored. Score ≥ 3 count went
from 0 → 67. The AIID signals still top out at score 2 after vocabulary
sharpening — confirming the corpus mismatch diagnosis. Governance signals produce
the full 0–4 range. This asymmetry is expected and informative: in insurance AI
governance, regulatory and investigative signals carry the acute risk load; AIID
incidents provide general AI safety awareness but don't directly map to internal
insurer workflows. Day 6 stratified sampling should plan around this asymmetry.

**Known finding — score-4 inflation on governance framework signals:** The v1
scoring prompt conflates "ongoing regulatory obligation" with "time-urgent
incident" on governance framework signals (NAIC bulletins, EU AI Act articles,
NIST AI RMF). A NAIC model bulletin applying to an underwriting system is real
and material, but it probably doesn't require model-owner action *this week* the
way a live enforcement action would. Several score-4s are more accurately score-3s
under strict rubric interpretation. This is a Day 9 prompt iteration target: add
a clarifying sentence distinguishing "direct and immediate implication" (active
incident, recent enforcement, imminent deadline) from "material ongoing compliance
obligation" (standing regulatory framework, guidance document). Documenting now
so Day 9 has a concrete objective, not a vague "tune the prompt."

**Interview story:** The system was mechanically correct from Day 4, but the
input data needed work. Diagnosing the vocabulary mismatch, designing a targeted
fix, and measuring the outcome is a data science story. The score-4 inflation
finding continues it: prompt calibration requires an eval set, and the eval set
exposed the next calibration problem.

---

## 2026-04-18 — Streamlit Cloud: sys.path insert for src/ importability

**Decision:** Add `sys.path.insert(0, str(PROJECT_ROOT))` at the top of `app/streamlit_app.py` so that `from src.schemas import Digest` resolves on Streamlit Cloud.

**Why:** Streamlit Cloud runs the entry point from a working directory that doesn't include the repo root on `sys.path`. The explicit insert is the standard pattern for Streamlit apps with local packages and is used throughout the Streamlit community.

**What was tried first and failed:** `pyproject.toml` + `-e .` in `requirements.txt`. The idea was to install the repo as a package so `src` would be importable without path manipulation. This failed because setuptools auto-discovery treated `src/` as a src-layout marker — it installed packages *inside* `src/` at the top level (making `schemas` importable, not `src.schemas`). Fixing this would require explicit `[tool.setuptools.packages.find]` config that names every package, which is more maintenance surface than the sys.path insert it was meant to replace. `pyproject.toml` is kept for local editable installs (`pip install -e .` for pipeline scripts) but is not the mechanism that makes Cloud imports work.

---

## 2026-04-18 — Pipeline code conventions: confirm_fn pattern and round-trip validation

**Decision:** Two conventions established during Day 4 pipeline work and used consistently going forward.

**confirm_fn callable pattern.** Any pipeline function that needs interactive cost/action confirmation accepts a `confirm_fn: Callable[[], bool]` parameter defaulting to a lambda that calls `input()`. The function never calls `input()` directly. This keeps business logic testable (tests pass `lambda: True`) and keeps UX decisions in the CLI layer. Apply to any future interactive prompts in scoring, eval, or training scripts.

**Round-trip write/validate pattern.** After writing any JSON output to disk, immediately re-read and validate against the Pydantic schema before returning. This catches serialization drift at the boundary — if the schema and the written file diverge, the error surfaces on the run that caused it rather than silently on the first dashboard load. Apply to any future output-writing code.

---

## 2026-04-20 — requirements.txt split into app-only and pipeline

**Decision:** `requirements.txt` contains only `streamlit` and `pydantic`. All pipeline deps (`boto3`, `anthropic`, `sentence-transformers`, etc.) live in `requirements-pipeline.txt`.

**Why:** Discovered during the Day 5 Streamlit Cloud deploy. `sentence-transformers` alone pulls PyTorch (~2GB installed), which blows the Cloud free-tier install. Splitting keeps the Cloud install to two lightweight packages. Local pipeline dev runs `pip install -r requirements-pipeline.txt`. Two files is marginally more maintenance, but getting the deploy right is worth it and the rule is enforced in `CLAUDE.md`.

---

## 2026-04-20 — By Signal dropdown shows only signals with scored pairs

**Decision:** The By Signal tab's dropdown shows only the 27 signals (of 78 total) that have at least one scored pair — not all signals in the digest.

**Why:** After loading the digest, 51 of 78 raw signals had zero scored pairs — filtered out at the retrieval stage (cosine similarity below 0.3). Showing all 78 would mean 65% of dropdown picks hit the "no pairs" empty state, making the tab feel broken. Only showing signals that made it through retrieval is the correct UX. A caption explains the count.

**Implication for Day 6:** Stratified sampling for the eval set should be drawn from these 27 signals, not the full 78. Trying to sample from signals with no pairs will produce an empty result.

---

## 2026-04-20 — Score distribution is 4-heavy going into Day 6 eval

**Observation:** 118 scored pairs distributed as {0:27, 1:17, 2:7, 3:38, 4:29}. Heavy weight on scores 3-4 (57% of pairs), thin middle (7 pairs at score 2).

**Implication for Day 6:** Stratified sampling on cosine similarity (per plan) is still correct, but the resulting eval set may be label-heavy in the 3-4 bucket and label-thin in the 2 bucket. If the labeled eval ends up concentrated at the extremes, the off-by-one and confusion-matrix metrics will be less informative in the middle of the rubric. Worth watching during labeling — if the score-2 bucket is visibly underrepresented, note it in `LABELING_NOTES.md` rather than trying to rebalance mid-labeling.

Not taking action now. Logged so the Day 7 report can reference this when interpreting metrics.

---

## 2026-04-21 — Eval sampling uses equal-rank terciles, not equal-width value buckets

**Decision:** `select_eval_pairs` in `src/eval_sampling.py` stratifies the 468-pair similarity list by index position (equal-rank terciles: indices 0-155 high, 156-311 medium, 312-467 low), not by equal-width cosine value buckets.

**Why:** The cosine similarity distribution across all pairs is tight, roughly 0.25-0.53. Equal-width value buckets (e.g., 0.25-0.34 / 0.34-0.43 / 0.43-0.53) would produce skewed strata because the distribution is not uniform across that range. Equal-rank terciles guarantee 16-17 candidates per stratum regardless of distribution shape. The high/medium/low labels remain meaningful relative to what the retriever actually produces — high means "top third of cosine scores this retriever assigned," which is the operationally relevant comparison.

---

## 2026-04-29 — Governance signal URL audit: fix vs. remove criteria

**Decision rule:**
- Never remove a signal whose ID appears in `pairs_to_label.json` or `labeled_pairs.json`. The labeling script looks up signals by ID and will crash on a missing reference. URL, title, description, and date can be corrected freely, but the ID and the signal's existence must be preserved.
- For signals not in the eval set: remove if the specific document cannot be verified after a reasonable search. Fix the URL in place if the underlying event or document is real but the URL is wrong.
- If governance signals are ever added or regenerated, run live URL verification before adding them to the file. Initial curation used real events as source material but produced some incorrect URLs and at least one wrong date — do not assume URL accuracy without checking.

**What triggered this:** Two broken URLs surfaced mid-labeling at pair 39, prompting a full audit of all 18 governance signal URLs.

**What was found and applied:**
- 9 URLs fixed in place
- gov-004 removed (specific California DOI bulletin on credit scores + COVID could not be verified as existing; was not in `pairs_to_label.json`)
- gov-009 title and description corrected (called a "report"; was actually an ANPR)
- gov-018 date corrected (was 2023-03-21; actual publication was 2021-01-28 — a 26-month metadata error despite correct substance)

Signal dates can have metadata errors even when the substance is right; interpret signal-date patterns in the eval with that caveat.

---

## 2026-04-30 — Two fabricated governance signals removed (gov-005, gov-017)

**What happened:** During Day 6 labeling, `gov-017` ("NAIC Report on Big Data and Artificial Intelligence in the Insurance Industry (2023)") and `gov-005` ("NAIC Big Data & AI Working Group: Guidance on Predictive Model Fairness Testing") were found to have URLs pointing to generic NAIC landing pages. Web search and URL verification confirmed no documents matching those titles and dates exist. The descriptions are plausible composites of real NAIC activity but are not specific real documents.

**Action taken:** Both signals deleted from all data files (`governance_signals.json`, `digest.json`, `similarities.json`, `pairs_to_label.json`). The eval set went from 50 to 49 pairs as a result. The April 29 URL audit entry covers the fix-vs-remove criteria that apply going forward.

**Implication:** The original governance signal set was likely generated with LLM assistance from real source material, producing some signals that are accurate in substance but fabricated as specific documents. Any future governance signal additions require URL verification before committing. This rule is now explicit in CLAUDE.md.

---

## 2026-04-30 — Day 7 eval finding: LLM judge underuses the rubric's middle tier

**Headline finding:** On the v1 eval run (49 pairs, Haiku, temperature=0), the LLM judge predicted score 2 exactly zero times. Predicted distribution: {0:35, 1:8, 2:0, 3:3, 4:3}. The model effectively uses 4 of the 5 rubric levels — it dismisses pairs (0-1) or flags them clearly (3-4), with nothing in the "Worth a glance" middle.

**Headline metrics:**
- Exact match: 22.4%
- Off-by-one: 65.3%
- Recall at score >= 3: 33.3% (6 of 18 high-relevance pairs caught)

The 65.3% off-by-one is partly inflated by the model being "close enough" when it under-scores true 3s as 1s, rather than being well-calibrated in the middle. A well-calibrated judge should use the full scale.

**Two error mechanisms behind the collapse:**

1. **Over-literalism on direct vs. analogous risk.** Cross-domain risk transfer (e.g., an image-bias incident scored against a system that uses a vision model in a different context) gets scored 0 or 1 because "the specific failure mechanism differs." Human labels these 3-4 because the risk pathway transfers even if surface context differs.

2. **System card disclaimers read as blanket exemptions.** When a system card includes language like "not used for coverage decisions," the model treats this as a general risk exemption — dismissing signals about bias or fairness in the system's actual inputs. This showed up most clearly on the Auto Claims Summarizer but the pattern likely generalizes.

**Implication for Day 9:** The asymmetric-error-cost language in the v1 prompt ("when uncertain, prefer the higher score") is not overcoming the model's conservative default. Day 9 prompt iteration should target: (a) explicit language that analogous risk transfer is sufficient for score 2-3, and (b) clarifying that operational disclaimers in system cards do not exempt a system from related risk categories. Rubric stays locked — only prompt scaffolding changes.

---

## 2026-05-01 — Day 9 eval results: v2 prompt iteration findings

**Headline results:** Four targeted prompt changes (remove downward prior, add risk-category rule, add score-2/3 anchor examples, rewrite role framing) moved: exact match 22.4% → 28.6%, off-by-one 65.3% → 75.5%, recall@>=3 33.3% → 44.4% (6 → 8 of 18 high-relevance pairs caught). Large errors (abs >= 2) dropped from 17 to 12.

**What worked:** Removing "score 0 is correct and expected for many pairs" (Change 1) was the highest-leverage change — it unblocked score 2 entirely (0 → 9 predictions) and collapsed the bimodal distribution. The anchor examples (Change 3) reinforced this. The risk-category rule (Change 2) had partial effect; the model applied it selectively rather than consistently.

**One regression:** The Obama/image-bias signal vs. Telematics Pricing Model was scored 2 by v2 (human label 0). The risk-category rule over-applied — the telematics model does list proxy discrimination as a known risk, but the LLM drew a category-level connection the human didn't endorse. One new false positive out of 49 is acceptable in the governance direction, but it confirms the risk that was flagged in the proposed changes.

**Unexpected finding:** v2 off-by-one accuracy (75.5%) beats the logistic regression baseline (69.4%), despite the classifier winning on recall (44.4% vs. 61.1%). The classifier's LOO CV advantage shows up primarily in recall; the LLM judge v2 is better-calibrated across the full scale. The interview story the comparison produces: the classifier is ~450x faster and effectively free, but misses ~55% of urgent signals — the wrong error direction for governance. The LLM judge is slower and costs ~$1.68/1k pairs but catches more urgent signals and is better-calibrated. This is the intended finding and it holds after prompt iteration.

---

## 2026-05-05 — Explicit text color required on HTML table cells with light backgrounds

**Decision:** `_TH` (header cells, `background:#f5f5f5`) and `_TD_WIN` (winner cells, `background:#e8f5e9`) in `app/components.py` pin explicit text colors: `color:#212121` on headers, `color:#1b5e20` on winner cells.

**Why:** Streamlit's dark theme defaults inherited text color to near-white. Without pinned colors, white text on a light green or light gray background is unreadable — discovered after the first deploy of the Evaluation tab. Cells without explicit backgrounds (`_TD`, `_TD_LABEL`) are left alone so they inherit correctly from whichever theme the user is on.

**Rule going forward:** Any `unsafe_allow_html` table cell with a light background must pin its text color explicitly.

---

## 2026-05-05 — App-layer observability instead of CloudWatch

**Decision:** Observability is implemented entirely at the application layer (`CallMetadata` captured in `src/scoring.py`, aggregated into `RunReport` by `src/pipeline.py`, written to `data/outputs/run_metadata.json`) rather than relying on AWS Bedrock CloudWatch metrics.

**Why:** Bedrock invocation logging must be explicitly enabled per-model in the AWS console; it is off by default and was never enabled during this project's pipeline runs, so CloudWatch metrics never published. The pivot to app-layer instrumentation turned out to be the better design regardless: metrics travel with the artifact, are interpretable without AWS console access, and work identically whether the caller is Bedrock or the direct Anthropic SDK. The Run Metadata dashboard tab surfaces the data.

**Alternatives considered:** Enable Bedrock invocation logging and re-run the full pipeline to generate CloudWatch metrics as a visible portfolio deliverable. Rejected because it would add another ~8-minute run, the dashboard tab already demonstrates the concept clearly, and app-layer instrumentation is more portable and portable as a pattern.

**Implication for future sessions:** Do not add a `docs/screenshots/` directory for CloudWatch screenshots — the README no longer references them. If Bedrock logging is ever enabled for another reason, the observability story doesn't change; it just gains a second artifact.