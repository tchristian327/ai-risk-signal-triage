# Score Distribution Comparison: Day 4 Baseline vs Day 4.5 Fix
*Generated 2026-04-18*

Two changes made before this run:
1. **Portfolio vocabulary sharpened** — all 6 systems' `known_risks` updated to use AI-safety-native terminology (adverse action, FCRA, disparate impact, prompt injection, hallucination, concept drift, fairness audit, label leakage, etc.)
2. **Governance signals added** — 18 hand-curated signals from NAIC, NIST, EU AI Act, CFPB, FTC, and public incidents in regulated industries. Combined corpus: 60 AIID + 18 governance = 78 signals.

---

## Cosine Similarity Distribution

| Stat | Old (360 pairs, AIID only) | New (468 pairs, AIID + gov) |
|------|---------------------------|------------------------------|
| Min | -0.119 | -0.113 |
| p25 | 0.037 | 0.077 |
| Median | 0.106 | 0.169 |
| Mean | 0.112 | 0.210 |
| p75 | 0.185 | 0.309 |
| p90 | 0.248 | 0.474 |
| p95 | 0.282 | 0.541 |
| **Max** | **0.366** | **0.739** |

| Threshold | Old | New |
|-----------|-----|-----|
| > 0.3 | 9 | 118 |
| > 0.4 | 0 | 85 |
| > 0.5 | 0 | 38 |

The entire distribution shifted right. The median doubled (0.106 → 0.169), the p90 almost doubled (0.248 → 0.474), and the maximum went from 0.366 to 0.739. 118 pairs now clear the 0.3 threshold — every single one of them was passed to the scorer.

---

## Per-System Max Cosine: Old vs New

| System | Old max | New max | Signal producing new max |
|--------|---------|---------|--------------------------|
| auto_claims_summarizer | 0.303 | **0.526** | gov-007 (NIST AI 600-1: Generative AI Risk Profile) |
| customer_chatbot | 0.329 | **0.552** | gov-002 (NAIC Model Bulletin on AI by Insurers) |
| doc_extractor | 0.299 | **0.538** | gov-007 (NIST AI 600-1: Generative AI Risk Profile) |
| fraud_detector | 0.303 | **0.699** | gov-011 (EU AI Act Art. 10: Training Data Quality) |
| telematics_pricer | 0.366 | **0.682** | gov-009 (FTC Commercial Surveillance Report) |
| underwriting_scorer | 0.305 | **0.739** | gov-018 (Consumer Reports: Algorithmic Insurance Pricing) |

Every system gained 0.2+ in maximum cosine similarity. The three systems with the sharpest vocabulary-governance alignment (underwriting_scorer, fraud_detector, telematics_pricer) reached 0.68–0.74.

---

## Score Distribution: Old vs New

| Score | Old (48 pairs) | New (118 pairs) |
|-------|----------------|-----------------|
| 0 | 42 (88%) | 27 (23%) |
| 1 | 4 (8%) | 17 (14%) |
| 2 | 2 (4%) | 7 (6%) |
| **3** | **0** | **38 (32%)** |
| **4** | **0** | **29 (25%)** |

Score ≥ 3 went from 0 to **67 pairs (57% of all scored pairs)**. This is the distribution we need for Day 6 stratified sampling and Day 7 eval.

Note: all 67 score-≥3 pairs are governance signals. The AIID-sourced pairs remain in the 0–2 range, consistent with the Day 4 diagnostic finding that AIID does not cover internal insurance ML well.

---

## Governance-to-System Pairs at Score ≥ 3

These are the pairs specifically requested: every governance signal match at score ≥ 3, sorted by score then cosine.

### Score 4 (Urgent review) — 29 pairs, all GOV

| System | Signal | Cosine | Reasoning excerpt |
|--------|--------|--------|-------------------|
| underwriting_scorer | gov-018 (Consumer Reports: Algorithmic Insurance Pricing) | 0.739 | Directly describes auto insurance pricing disparities via proxy variables — education, occupation, credit scores — that create disparate impact by race. Underwriting scorer has same risk documented explicitly. |
| fraud_detector | gov-011 (EU AI Act Art. 10: Training Data Quality) | 0.699 | EU AI Act explicitly names fraud detection in scope. Fraud detector uses historical investigator feedback as training labels — direct label leakage risk. |
| underwriting_scorer | gov-015 (ProPublica: Racial Disparities in Auto Insurance Pricing) | 0.696 | Investigation documents algorithmic pricing disparate impact via commute, homeownership, education proxies. Underwriting scorer system card lists "fairness audit failures" and geographic proxy risks explicitly. |
| telematics_pricer | gov-009 (FTC Commercial Surveillance Report) | 0.682 | FTC report directly addresses algorithmic pricing systems using continuous location tracking and behavioral data — exact mechanism of telematics pricing. Flags disparate impact from location proxies. |
| fraud_detector | gov-005 (NAIC Big Data WG: Predictive Model Testing) | 0.659 | NAIC framework addresses 4 of 5 fraud detector known risks directly: disparate impact testing, concept drift monitoring, adverse action explainability, training data bias. |
| underwriting_scorer | gov-001 (Colorado SB21-169) | 0.616 | Law prohibits algorithms that produce discriminatory effects and mandates ongoing fairness audits and adverse action explainability — two risks explicitly in the underwriting scorer system card. |
| underwriting_scorer | gov-005 (NAIC Big Data WG: Predictive Model Testing) | 0.607 | Framework directly addresses 5 risks in underwriting scorer: training data quality, label leakage from historical decisions, model drift, disparate impact testing, adverse action explainability. |
| underwriting_scorer | gov-008 (CFPB Circular 2022-03: Adverse Action for AI) | 0.601 | CFPB circular requires specific FCRA adverse action reasons even for opaque ML models. Underwriting scorer system card explicitly documents "adverse action notice inadequacy under FCRA." |
| underwriting_scorer | gov-010 (EU AI Act Art. 6: High-Risk AI in Insurance) | 0.591 | EU AI Act explicitly classifies insurance risk scoring as high-risk. Underwriting scorer is an insurance risk scoring system. |
| fraud_detector | gov-010 (EU AI Act Art. 6: High-Risk AI in Insurance) | 0.583 | EU AI Act classifies fraud detection models as high-risk requiring conformity assessments and discrimination monitoring. |
| fraud_detector | gov-002 (NAIC Model Bulletin on AI by Insurers) | 0.558 | NAIC bulletin requires disparate impact testing and adverse action explainability for AI claims systems. Fraud detector operates in claims processing. |
| underwriting_scorer | gov-011 (EU AI Act Art. 10: Training Data Quality) | 0.558 | Art. 10 mandates training data bias examination for high-risk insurance AI — directly implicates label leakage from historical underwriting decisions documented in the system card. |
| underwriting_scorer | gov-017 (NAIC Annual Report on Big Data & AI) | 0.548 | Report flags absence of mandatory disparate impact testing and concept drift monitoring — both documented risks in the underwriting scorer. |
| fraud_detector | gov-012 (EU AI Act Arts. 13-14: Human Oversight) | 0.547 | Arts. 13-14 require meaningful human oversight and transparency for fraud detection AI. Fraud detector flags are shown to adjusters without score or feature explanations. |
| underwriting_scorer | gov-002 (NAIC Model Bulletin on AI by Insurers) | 0.541 | NAIC bulletin directly addresses underwriting AI governance, calling for disparate impact testing and adverse action explainability. |
| auto_claims_summarizer | gov-007 (NIST AI 600-1: Generative AI Risk Profile) | 0.526 | NIST 600-1 explicitly names hallucination, prompt injection, and PII leakage as high-stakes failure modes for insurance claim summarization LLMs. All three are in the auto claims summarizer system card. |
| telematics_pricer | gov-001 (Colorado SB21-169) | 0.521 | Law prohibits discriminatory algorithmic pricing and requires adverse action explainability. Telematics pricing model has both proxy discrimination and adverse action explainability gap documented. |
| customer_chatbot | gov-007 (NIST AI 600-1: Generative AI Risk Profile) | 0.497 | NIST 600-1 names hallucination of coverage commitments and prompt injection via customer input as high-stakes failure modes for insurance chatbots — both explicitly in the chatbot system card. |
| underwriting_scorer | gov-012 (EU AI Act Arts. 13-14: Human Oversight) | 0.487 | Arts. 13-14 require transparency and human oversight in insurance underwriting AI adverse action decisions. Underwriting scorer auto-decline has no appeal mechanism. |
| fraud_detector | gov-008 (CFPB Circular 2022-03: Adverse Action for AI) | 0.474 | CFPB circular rejects model opacity as excuse for missing adverse action reasons. Fraud detector system card explicitly documents "adverse action explainability gap." |
| telematics_pricer | gov-005 (NAIC Big Data WG: Predictive Model Testing) | 0.472 | NAIC framework directly addresses concept drift, disparate impact testing, and adverse action explainability for telematics-style pricing models. |
| telematics_pricer | gov-002 (NAIC Model Bulletin on AI by Insurers) | 0.459 | NAIC bulletin requires ongoing disparate impact testing and adverse action explainability for insurance AI pricing systems. |
| telematics_pricer | gov-010 (EU AI Act Art. 6: High-Risk AI in Insurance) | 0.454 | EU AI Act classifies insurance individual risk scoring as high-risk — telematics model is an individual risk scoring system for premium setting. |
| telematics_pricer | gov-011 (EU AI Act Art. 10: Training Data Quality) | 0.447 | Art. 10 requires bias examination for training data and concept drift monitoring — telematics model's training on historical claims raises both concerns. |
| doc_extractor | gov-002 (NAIC Model Bulletin on AI by Insurers) | 0.445 | NAIC bulletin requires governance programs for AI systems in claims processing — document extractor is deployed in insurance claims. |
| doc_extractor | gov-012 (EU AI Act Arts. 13-14: Human Oversight) | 0.443 | Arts. 13-14 require human oversight for high-risk insurance AI. Document extractor's high-confidence extractions are "increasingly accepted without review." |
| telematics_pricer | gov-012 (EU AI Act Arts. 13-14: Human Oversight) | 0.423 | Arts. 13-14 require transparency and contestability for adverse action decisions. Policyholders receiving telematics surcharges cannot get specific auditable reasons. |
| telematics_pricer | gov-003 (NY DFS Circular Letter No. 1, 2019) | 0.417 | NY DFS requires insurers using algorithmic models to ensure no discriminatory effects and to explain adverse decisions — both documented gaps in telematics pricing. |
| telematics_pricer | gov-008 (CFPB Circular 2022-03: Adverse Action for AI) | 0.330 | CFPB circular requires specific adverse action reasons from AI models. Telematics scorer system card documents that policyholders "cannot get specific, auditable reasons for their score." |

### Score 3 (Action recommended) — 38 pairs, all GOV

| System | Signal | Cosine | Note |
|--------|--------|--------|------|
| underwriting_scorer | gov-004 (California DOI credit score bulletin) | 0.645 | Direct regulatory precedent for suspending credit-based insurance scores due to disparate impact |
| telematics_pricer | gov-018 (Consumer Reports: Algorithmic Insurance Pricing) | 0.613 | Same investigative signal as the underwriting scorer's score-4 match; slightly less direct for telematics |
| fraud_detector | gov-017 (NAIC Annual Report on Big Data & AI) | 0.609 | NAIC report flags absence of mandatory disparate impact testing and emerging state audit requirements |
| telematics_pricer | gov-004 (California DOI credit score bulletin) | 0.591 | Regulatory action on algorithmic pricing proxy discrimination — relevant but telematics uses behavioral not credit proxies |
| underwriting_scorer | gov-003 (NY DFS Circular Letter No. 1, 2019) | 0.582 | NY DFS adverse action explainability requirements apply to underwriting algorithms |
| fraud_detector | gov-018 (Consumer Reports: Algorithmic Insurance Pricing) | 0.577 | Proxy variable disparate impact in insurance — different product line but same mechanism as fraud detector |
| telematics_pricer | gov-015 (ProPublica: Racial Disparities in Auto Insurance) | 0.558 | Direct insurance pricing disparate impact investigation — same domain |
| customer_chatbot | gov-002 (NAIC Model Bulletin on AI by Insurers) | 0.552 | NAIC bulletin covers AI governance for customer-facing insurance systems |
| fraud_detector | gov-001 (Colorado SB21-169) | 0.541 | State law on algorithmic discrimination directly applicable to fraud scoring |
| fraud_detector | gov-014 (HUD/Facebook: Discriminatory Algorithmic Targeting) | 0.510 | ML optimization producing disparate impact through proxy learning — parallel to fraud detector mechanism |
| fraud_detector | gov-003 (NY DFS Circular Letter No. 1, 2019) | 0.509 | NY DFS external data and algorithm requirements apply to fraud detection inputs |
| underwriting_scorer | gov-013 (Apple Card gender discrimination investigation) | 0.508 | Canonical proxy discrimination via algorithmic credit underwriting — direct parallel to underwriting scorer |
| fraud_detector | gov-009 (FTC Commercial Surveillance Report) | 0.508 | FTC algorithmic disparate impact concerns via location and third-party data |
| underwriting_scorer | gov-009 (FTC Commercial Surveillance Report) | 0.493 | Geographic and behavioral data proxies in pricing decisions |
| fraud_detector | gov-013 (Apple Card gender discrimination investigation) | 0.487 | Proxy discrimination and adverse action explainability gap in algorithmic model |
| fraud_detector | gov-006 (NIST AI RMF 1.0) | 0.485 | AI RMF governance framework addresses fairness, disparate impact, and adverse action explainability |
| customer_chatbot | gov-017 (NAIC Annual Report on Big Data & AI) | 0.469 | Model drift monitoring and emerging fairness audit requirements for insurance AI |
| telematics_pricer | gov-014 (HUD/Facebook: Discriminatory Algorithmic Targeting) | 0.468 | ML optimization learning discriminatory behavioral proxies — parallel to telematics driving pattern proxies |
| auto_claims_summarizer | gov-002 (NAIC Model Bulletin on AI by Insurers) | 0.471 | NAIC AI governance requirements for claims processing AI systems |
| fraud_detector | gov-004 (California DOI credit score bulletin) | 0.471 | Regulatory intervention on algorithmic proxy discrimination in insurance pricing |
| customer_chatbot | gov-016 (UnitedHealth: AI Model Denying Claims) | 0.451 | AI model making high-stakes decisions with inadequate human oversight — chatbot not authorized for claims decisions but governs access to information |
| fraud_detector | gov-016 (UnitedHealth: AI Model Denying Claims) | 0.446 | AI model used for adverse action decisions at scale with inadequate human review — directly parallel to fraud flagging at scale |
| doc_extractor | gov-010 (EU AI Act Art. 6: High-Risk AI in Insurance) | 0.443 | EU AI Act classifies insurance claims AI as high-risk |
| underwriting_scorer | gov-016 (UnitedHealth: AI Model Denying Claims) | 0.435 | High-stakes AI adverse action with no appeal — parallel to underwriting scorer's hard cutoff |
| customer_chatbot | gov-006 (NIST AI RMF 1.0) | 0.422 | AI RMF governance framework for LLM deployment documentation and oversight |
| telematics_pricer | gov-017 (NAIC Annual Report on Big Data & AI) | 0.417 | NAIC flags disparate impact testing gaps and concept drift challenges |
| underwriting_scorer | gov-014 (HUD/Facebook: Discriminatory Algorithmic Targeting) | 0.417 | Proxy discrimination via learned behavioral proxies in ML systems |
| telematics_pricer | gov-013 (Apple Card gender discrimination investigation) | 0.412 | Proxy discrimination and adverse action explainability gap |
| telematics_pricer | gov-006 (NIST AI RMF 1.0) | 0.396 | NIST RMF model drift, fairness, and human oversight requirements |
| doc_extractor | gov-017 (NAIC Annual Report on Big Data & AI) | 0.393 | NAIC fairness audit and concept drift monitoring requirements |
| auto_claims_summarizer | gov-006 (NIST AI RMF 1.0) | 0.388 | NIST RMF governance framework for LLM lifecycle risks |
| telematics_pricer | gov-016 (UnitedHealth: AI Model Denying Claims) | 0.386 | AI-driven adverse action at scale with inadequate individual explainability |
| doc_extractor | gov-016 (UnitedHealth: AI Model Denying Claims) | 0.362 | AI claims processing with inadequate human review — parallel to doc extractor automation risk |
| doc_extractor | gov-006 (NIST AI RMF 1.0) | 0.332 | NIST RMF model drift and human oversight requirements for deployed AI |

---

## Honest Read

**The fix worked.** The core problem was confirmed: the AIID corpus has no signals above score 2 on this portfolio, even after vocabulary sharpening. The governance signals produced 67 of the 67 score-≥3 pairs. This isn't a surprise — it was the diagnosis.

**What worked particularly well:**
- `underwriting_scorer` and `fraud_detector` hit the highest cosines and most score-4 pairs. These systems have the most explicit regulatory risk vocabulary (FCRA, adverse action, disparate impact, fairness audit) and the governance signals — especially the NAIC bulletins, EU AI Act articles, and the Consumer Reports/ProPublica investigations — use the same vocabulary back.
- `gov-007` (NIST AI 600-1) is the best single signal for the LLM systems: it names hallucination, prompt injection, and PII leakage in the context of insurance chatbots and claims pipelines, which creates precise lexical matches with the updated chatbot and claims summarizer system cards.
- `gov-009` (FTC Commercial Surveillance) is the best single signal for telematics: it specifically addresses algorithmic pricing systems that use continuous location tracking, which is the exact mechanism.

**What to watch on Day 6 (labeling):**
- Several score-3 pairs for doc_extractor and customer_chatbot are borderline — the LLM is scoring them 3 but the connection is one step removed (e.g., EU AI Act general insurance scope applying to a document OCR pipeline). These pairs will be interesting to label by hand.
- The AIID corpus still produces 0s and 1s. This is correct behavior, not a bug. Day 6 should include a mix of governance (scores 3-4) and AIID (scores 0-1) pairs to get full rubric coverage.
- 29 score-4 pairs is arguably a lot. On Day 6, expect some of these to get downgraded to 3 during human labeling — the LLM may be assigning 4 for pairs where the regulatory signal applies but doesn't require action *this week* (the rubric's 4 criterion). Worth watching the auto_claims_summarizer and doc_extractor score-4s especially — the governance obligations there are real but less immediate than the underwriting/fraud pairs.

**Is the distribution viable for Day 6 stratified sampling?** Yes. We now have pairs at every rubric level, with meaningful counts at 3 and 4. The Day 7 recall-at-≥3 metric is now computable.

---

## Top 5 Demo Cases (governance × system, by score+cosine)

These are the strongest pairs to highlight in the dashboard and in an interview:

1. **underwriting_scorer × gov-018** (score=4, cos=0.739) — Consumer Reports' investigation directly documents the exact mechanism the Underwriting Risk Scorer is at risk for: algorithmic pricing proxy discrimination in auto insurance.

2. **fraud_detector × gov-011** (score=4, cos=0.699) — EU AI Act Article 10 explicitly names fraud detection systems as in scope for training data bias governance, and the fraud detector's training data loop is the first documented risk.

3. **underwriting_scorer × gov-015** (score=4, cos=0.696) — ProPublica's auto insurance pricing investigation is the field-defining public evidence of the exact risk the underwriting scorer carries.

4. **telematics_pricer × gov-009** (score=4, cos=0.682) — The FTC's commercial surveillance report specifically calls out algorithmic pricing systems that use continuous location tracking — the telematics model's exact architecture.

5. **fraud_detector × gov-005** (score=4, cos=0.659) — The NAIC Big Data Working Group framework directly addresses 4 of 5 documented fraud detector risks and will be cited by state examiners.
