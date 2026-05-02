# Proposed prompt changes for v2

These changes are grounded in two sources: the error analysis in `error_analysis_v1.md`
(17 pairs with abs error >= 2, all under-scored) and the user's notes in `REPORT_WEEK2.md`
("What I'd want to fix").

The dominant failure mode in v1 is **score collapse**: the model produced zero score-2
predictions and only 6 predictions at score 3 or 4 across 49 pairs. All 17 large-error
pairs were under-scored — none were over-scored. The changes below are targeted at the
specific prompt mechanisms that caused this.

---

## Change 1: Remove the downward-biasing paragraph

**Failure mode it targets:**
Score collapse — the model produced 0 score-2 predictions and only 6 at 3 or 4.
The "score of 0 is correct and expected for many pairs" line in the Asymmetric error
costs section is the only concrete scoring guidance in the prompt, and it points down.
The retriever has already filtered to candidates that passed a similarity threshold;
telling the model to expect zeros on top of that double-punishes any uncertain pair.

**What changes in the prompt:**
Remove this paragraph from the Asymmetric error costs section:

> However: a score of 0 is correct and expected for many pairs. The candidate filter has
> already removed the obviously unrelated pairs, but many filtered candidates will still
> be 0 or 1. Keyword overlap alone does not indicate relevance — two systems can share a
> topic area without sharing the specific risk mechanism.

Keep the rest of the Asymmetric error costs framing (the "when uncertain, prefer the
higher score" guidance).

**Why this should help:**
Removing the downward nudge removes the dominant prior that produces score collapse.
The rubric already defines score 0 clearly — the model doesn't need a reminder that
zeros exist, especially one that counteracts the asymmetric-cost framing right above it.

**Risk:**
Could shift the model in the opposite direction, scoring too generously on weak
signal-system pairs. If recall improves but precision drops significantly, this is the
likely culprit.

---

## Change 2: Add a concrete risk-category rule to the asymmetric-cost framing

**Failure mode it targets:**
Over-strict mechanism matching. In 7 of 17 large-error pairs, the LLM acknowledged
that the signal illustrated a risk category present in the system card but still scored
0 or 1 because "the specific failure mechanism differs." The clearest case: the
Google/gorilla image classification incident vs. the Document OCR pipeline, which has
"demographic bias in handwriting recognition" as a documented known risk. The LLM
reasoned that image classification bias ≠ handwriting recognition bias and scored 1,
when the human label was 4.

**What changes in the prompt:**
Add this sentence to the Asymmetric error costs section:

> If a signal illustrates a risk category that is explicitly named in a system's known
> risks, assign a score of at least 3, even if the specific failure mechanism in the
> signal differs from the exact mechanism described in the system card. Risk category
> match is sufficient for action-level relevance; exact mechanism match is not required.

**Why this should help:**
The model's reasoning in the error cases is technically defensible but wrong for
governance. The purpose of the triage system is to surface signals that map to a known
risk area, not to require exact mechanism matches. Making this rule explicit gives the
model permission to score high on category-level matches.

**Risk:**
Could over-generalize — e.g., any bias signal matching any system that has "bias" as a
known risk gets a 3 regardless of how tangential it is. The "explicitly named in known
risks" language is intended to limit this, but it may not be tight enough.

---

## Change 3: Add anchoring examples for scores 2 and 3

**Failure mode it targets:**
The rubric definitions for levels 2 and 3 are vague relative to 0 ("no meaningful
connection") and 4 ("direct and immediate implications"). The model had sharp priors for
the endpoints but no anchor for the middle, causing it to skip 2 and 3 and fall back to
the endpoints it understood. This explains the bimodal distribution: 36 predictions at
0–1, 6 at 3–4, and zero at 2.

**What changes in the prompt:**
Add a short "Score anchor examples" section between the rubric and the system card,
with one generic example per level for 2 and 3:

> **Score 2 example:** A signal about a facial recognition false arrest in law
> enforcement, evaluated against an auto claims summarizer that uses a vision model to
> assess vehicle damage. The system processes vehicle photos, not faces or identities —
> the failure mechanism is different. But the signal raises a class of vision-model error
> (misclassification under distribution shift) that could manifest differently in the
> claims context. Worth a glance; no immediate action needed.
>
> **Score 3 example:** A regulatory guidance document requiring adverse action
> explainability for any AI model that influences insurance decisions, evaluated against
> a fraud detection model. The model flags claims for investigator review — that review
> outcome affects the claimant. The explainability requirement plausibly applies.
> Model owner should review whether current documentation satisfies the requirement.

Examples are generic (not drawn from the eval set) and are illustrative, not
prescriptive.

**Why this should help:**
Concrete examples give the model an anchor for what "could apply under some conditions"
(score 2) vs. "plausibly affects" (score 3) looks like in practice, without changing the
rubric definitions.

**Risk:**
The examples could over-constrain the model — if it interprets them as templates rather
than illustrations, it might only assign 2 or 3 when the scenario closely mirrors the
example. Framing them explicitly as examples ("for instance") should mitigate this.

---

## Change 4: Rewrite the role description to activate governance framing

**Failure mode it targets:**
The current role says "evaluate whether an external AI risk signal is relevant to a
specific internal AI system." That framing is neutral — it asks the model to judge
relevance, which it does by finding reasons to score low. The governance context
requires a different default: the analyst's job is to surface risks that humans should
see, not to prune a list.

**What changes in the prompt:**
Replace the current role/task paragraph with:

> You are an AI risk analyst at an insurance company responsible for surfacing external
> AI risk signals that warrant review by internal model owners. Your job is to flag
> signals that a risk-aware model owner should see — not to filter them out. When a
> signal has a plausible connection to an internal system, your default is to surface it.
> You will assign a relevance score from 0 to 4 using the rubric below.

**Why this should help:**
The reframe shifts the model's default action from "find reasons to score low" to "find
reasons to surface." The rubric still constrains the score — this change only affects the
prior that governs ambiguous cases.

**Risk:**
Could push the model toward systematic over-scoring if the role framing dominates the
rubric. The rubric definitions should act as a corrective, but role priming is known to
be sticky in LLMs. Monitor for precision regression in the v2 results.
