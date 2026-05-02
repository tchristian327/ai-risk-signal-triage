# Prompt changelog

## v2 (2026-05-01)

All four changes were implemented together and evaluated as a bundle. The v1-to-v2 delta
is reported as a whole; individual attribution is estimated from the error analysis
rather than from ablation runs.

### Change 1: Removed the downward-biasing paragraph

**Failure mode targeted:**
Score collapse — v1 produced 0 score-2 predictions and only 6 at 3 or 4 across 49 pairs.
The v1 Asymmetric error costs section contained: "a score of 0 is correct and expected
for many pairs... Keyword overlap alone does not indicate relevance." This was the only
concrete scoring guidance and it pointed down, counteracting the "prefer the higher score"
framing immediately above it.

**Specific change:**
Removed that paragraph entirely. The Asymmetric error costs section now only contains
the "prefer the higher score when uncertain" rule and the new risk-category rule
(Change 2).

**Rationale:**
The retriever has already filtered out clearly unrelated pairs before the LLM ever sees
them. Reminding the model that zeros are expected on top of that filter double-punishes
uncertain candidates. The rubric defines score 0 adequately on its own.

**Result:**
Score distribution shifted upward. v2 used score 2 in 9 pairs (vs. 0 in v1) and score 3
in 7 pairs (vs. 3 in v1). Off-by-one accuracy improved from 65.3% to 75.5%. Recall at
score >= 3 improved from 33.3% (6/18) to 44.4% (8/18). One new over-score appeared
(Obama/image-bias signal scored 2 vs. human label 0 on Telematics Pricing Model), which
is consistent with the predicted risk. On balance, removing the downward bias improved
the metrics the project cares most about.

---

### Change 2: Added a concrete risk-category rule

**Failure mode targeted:**
Over-strict mechanism matching. In 7 of 17 large-error v1 pairs, the model acknowledged
that a signal illustrated a risk category present in the system card but scored 0 or 1
because the specific failure mechanism differed. The clearest case: Google/gorilla
(image misclassification) vs. Document OCR pipeline (known risk: demographic bias in
handwriting recognition). The LLM reasoned "image classification bias ≠ handwriting
recognition bias" and scored 1; human label was 4.

**Specific change:**
Added to the Asymmetric error costs section: "If a signal illustrates a risk category
that is explicitly named in a system's known risks, assign a score of at least 3, even
if the specific failure mechanism in the signal differs from the exact mechanism described
in the system card. Risk category match is sufficient for action-level relevance; exact
mechanism match is not required."

**Rationale:**
The triage system's purpose is to surface signals that a governance professional should
see — not to require exact mechanism matches. A model owner who sees "demographic bias
in computer vision" and knows their system has a documented demographic bias risk should
be prompted to review, even if the signal's specific manifestation differs.

**Result:**
Partially effective. The Google/gorilla vs. Doc OCR pair (abs error 3 in v1) was now
scored 2 by v2 (human label 4, abs error down from 3 to 2). The "Yes, AI can be racist"
vs. Claims Fraud Detector pair moved from score 1 to score 2 (human label 4, still
under-scored but less so). However, several pairs with category-matching signals that
were scored 0 in v1 were still scored 0 in v2 — the rule did not apply universally.
The instruction to apply this rule appears to have been followed selectively. The risk
predicted (over-generalization) appeared once: the Obama/image-bias signal vs. Telematics
Pricing Model was scored 2 when the human label was 0 (the telematics model's known
risks include proxy discrimination, but the LLM reasoned that "neutral technical features
can encode demographic bias" — a category-level stretch the human didn't endorse).

---

### Change 3: Added anchoring examples for scores 2 and 3

**Failure mode targeted:**
Bimodal score distribution driven by vague rubric language at levels 2 and 3. The model
had sharper intuitions for 0 ("no meaningful connection") and 4 ("direct and immediate
implications") than for the middle levels.

**Specific change:**
Added a "Score anchor examples" section between the rubric and system card, with one
generic illustrative example per level for 2 and 3. Examples were constructed to clarify
the distinction between "could apply under some conditions" (2) vs. "plausibly affects"
(3) without drawing from the eval set.

**Rationale:**
Concrete examples give the model a calibration anchor for the middle of the rubric.
The v1 bimodal distribution (36 predictions at 0–1, 6 at 3–4, 0 at 2) suggested the
model was retreating to the endpoints it understood best.

**Result:**
Score 2 usage went from 0 to 9 predictions. Score distribution is now more spread:
[27, 4, 9, 7, 3] across scores [0, 1, 2, 3, 4], vs v1's [36, 8, 0, 3, 3]. The exact
match accuracy improved (22.4% → 28.6%), suggesting the calibration helped. Hard to
isolate this change from Change 1 (removing the downward prior), which also pushed
scores upward. Most likely both contributed.

---

### Change 4: Rewrote the role description

**Failure mode targeted:**
The v1 role framing ("evaluate whether a signal is relevant") established a neutral
prior that the model resolved by finding reasons to score low. Governance context
requires a default toward surfacing, not pruning.

**Specific change:**
Replaced the role/task opening with: "You are an AI risk analyst at an insurance company
responsible for surfacing external AI risk signals that warrant review by internal model
owners. Your job is to flag signals that a risk-aware model owner should see — not to
filter them out. When a signal has a plausible connection to an internal system, your
default is to surface it."

**Rationale:**
Role priming is known to shift LLM behavior in ambiguous cases. Changing the default
action from "evaluate and prune" to "surface unless clearly irrelevant" should produce
higher scores on uncertain pairs — which is correct given the project's asymmetric error
cost principle.

**Result:**
Directionally positive but hard to isolate. The overall score distribution shifted upward
(consistent with this change), but so did Changes 1 and 3. The one clear regression
(Obama/image-bias vs. Telematics, scored 2 vs. human 0) could be attributed to either
the role framing or the risk-category rule (Change 2). In retrospect, this change and
Change 2 together may have over-corrected on a small number of pairs. Precision on
score-0 pairs held reasonably well (7 of 28 true-zero pairs were correctly scored 0 in
both v1 and v2), so the role reframe did not cause wholesale over-scoring.

---

## Summary: v1 → v2 movement

| Metric | v1 | v2 | Delta |
|--------|----|----|-------|
| Exact match accuracy | 22.4% | 28.6% | +6.2pp |
| Off-by-one accuracy | 65.3% | 75.5% | +10.2pp |
| Recall @ score >= 3 | 33.3% (6/18) | 44.4% (8/18) | +11.1pp |
| Large errors (abs >= 2) | 17 | 12 | -5 |
| Score-2 predictions | 0 | 9 | +9 |

The headline metric (recall at score >= 3) improved by 11pp. Off-by-one improved by 10pp.
Exact match improved but remains below the baseline classifier (28.6% vs. 36.7%), which
benefits from seeing labeled training examples via LOO CV.

**What v2 still gets wrong:**
- 10 of 18 high-relevance pairs are still missed (recall 44.4% vs. 61.1% for the classifier).
- Several "risk category match" pairs are still scored 0, suggesting the risk-category
  rule (Change 2) is applied selectively rather than consistently.
- Score 3 is underused on human-label-3 pairs (0 correct predictions at score 3),
  though score-4 pairs are caught at a higher rate (8/12 = 67% scored >= 3 in v2).
- The split between score 3 and score 4 remains imprecise: most v2 score-3 predictions
  are on human-label-4 pairs, not human-label-3 pairs.

**What these results mean for the project narrative:**
The iteration improved the LLM judge on the metrics that matter for governance (recall,
off-by-one). The gap vs. the classifier narrowed but didn't close, and the classifier
still wins on recall — consistent with the expected finding that a trained model with
labeled examples outperforms zero-shot prompting on this task, especially at the
cost of being wrong in the opposite direction (false negatives) that governance
penalizes most. This is the interview talking point the evaluation was built to produce.
