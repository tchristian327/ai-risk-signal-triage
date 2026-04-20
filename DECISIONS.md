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

## 2026-04-12 — AWS Bedrock as the primary LLM access path

**Decision:** Call Claude through AWS Bedrock (`boto3` with the `bedrock-runtime` Converse API) as the primary client. Keep the direct `anthropic` SDK as an optional local fallback controlled by the `LLM_PROVIDER` env var.

**Why:** The Allstate JD explicitly lists "exposure or practical experience in AWS Bedrock" as a preferred qualification. Using Bedrock from the start demonstrates cloud-deployed LLM competency rather than just local SDK usage. This also aligns with prior Bedrock experience from Claritas, which makes it a natural talking point in the interview. The Converse API was chosen over `invoke_model` because it supports tool use natively, keeping the code nearly identical to what the direct SDK version would look like. The direct SDK fallback stays available for local dev speed when Bedrock access is pending or slow.

---

## 2026-04-12 — Production hygiene pass (observability, Docker, CI) added as Day 11

**Decision:** Add a post-Day-10 production hygiene pass covering per-call LLM observability, a Dockerfile, and a GitHub Actions CI workflow.

**Why:** The JD calls out "CI/CD pipelines, containerization (Docker), observability tools, and cloud security practices" as preferred qualifications. These artifacts exist to demonstrate those signals, not because the project needs them to function. Bundling them into a single day after the core data science work is complete keeps them from interfering with the scoring, eval, and iteration work that is the project's actual substance.

---

## 2026-04-09 — AIID data source: Algolia search index, not GraphQL

**Decision:** Pull AIID signals from their public Algolia search index rather than the GraphQL API.

**Why:** The GraphQL endpoint returns 403 for non-browser origins. The Algolia index is the same data, exposed via publicly distributed keys in AIID's own repo, and is the same source AIID's own website uses. Signals are report-level (one incident can have multiple news reports); we deduplicate on `incident_id` and take the first English report. This means signal titles are news headlines rather than official incident titles, which is acceptable and arguably preferable for embedding-based retrieval (richer semantic content).

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

## 2026-04-18 — Pipeline code conventions: confirm_fn pattern and round-trip validation

**Decision:** Two conventions established during Day 4 pipeline work and used consistently going forward.

**confirm_fn callable pattern.** Any pipeline function that needs interactive cost/action confirmation accepts a `confirm_fn: Callable[[], bool]` parameter defaulting to a lambda that calls `input()`. The function never calls `input()` directly. This keeps business logic testable (tests pass `lambda: True`) and keeps UX decisions in the CLI layer. Apply to any future interactive prompts in scoring, eval, or training scripts.

**Round-trip write/validate pattern.** After writing any JSON output to disk, immediately re-read and validate against the Pydantic schema before returning. This catches serialization drift at the boundary — if the schema and the written file diverge, the error surfaces on the run that caused it rather than silently on the first dashboard load. Apply to any future output-writing code.