# Score Distribution Diagnostic Note
*Generated 2026-04-16 after Day 4 pipeline run*

---

## Cosine Similarity Distribution (all 360 pairs)

| Stat | Value |
|------|-------|
| Min | -0.119 |
| p25 | 0.037 |
| p50 (median) | 0.106 |
| Mean | 0.112 |
| p75 | 0.185 |
| p90 | 0.248 |
| p95 | 0.282 |
| Max | 0.366 |

| Threshold | Pairs above |
|-----------|-------------|
| > 0.3 | 9 |
| > 0.4 | 0 |
| > 0.5 | 0 |

The distribution is extremely compressed. The absolute maximum across 360 pairs is 0.366. Nothing exceeds 0.4.

### Per-system: count above 0.3, max similarity

| System | Above 0.3 | Max cosine |
|--------|-----------|-----------|
| auto_claims_summarizer | 1 | 0.3028 |
| customer_chatbot | 1 | 0.3285 |
| doc_extractor | 0 | 0.2992 |
| fraud_detector | 1 | 0.3025 |
| telematics_pricer | 4 | 0.3660 |
| underwriting_scorer | 2 | 0.3047 |

`telematics_pricer` dominates the top of the distribution because AIID skews heavily toward autonomous vehicle incidents, and "driving" vocabulary creates surface-level lexical overlap with the telematics system. But as the LLM scorer correctly identified, these are different domains.

---

## Score Distribution (48 scored pairs)

The pipeline scored the top 8 pairs per system (8 × 6 = 48), using top-N logic rather than strict threshold filtering, since only 9 pairs cleared 0.3 and many systems would have had zero candidates otherwise.

| Score | Count |
|-------|-------|
| 0 | 42 |
| 1 | 4 |
| 2 | 2 |
| 3 | 0 |
| 4 | 0 |

---

## The 6 Non-Zero Pairs

**score=2 pairs (2):**

1. **fraud_detector + aiid-54** (cos=0.3025)
   - Signal: "Why Oakland Police Turned Down Predictive Policing"
   - Reasoning: Both systems use historical data patterns to flag individuals; the algorithmic bias / civic pushback dynamic transfers across domains despite the law enforcement vs. insurance gap.

2. **underwriting_scorer + aiid-54** (cos=0.3016)
   - Signal: "Why Oakland Police Turned Down Predictive Policing"
   - Reasoning: Same signal; the underwriting system also makes high-stakes algorithmic decisions that expose the company to the same reputational and regulatory risk pattern.

**score=1 pairs (4):**

3. **customer_chatbot + aiid-149** (cos=0.2882)
   - Signal: "Zillow's home-buying debacle shows how hard it is to use AI to value real estate"
   - Reasoning: Both involve AI overconfidence, but the chatbot's risk is tone/escalation failure, not valuation accuracy.

4. **fraud_detector + aiid-119** (cos=0.2619)
   - Signal: "Xsolla fires 150 employees using big data and AI analysis"
   - Reasoning: Algorithmic decision-making at scale, but employment vs. fraud flagging is a domain stretch.

5. **underwriting_scorer + aiid-49** (cos=0.1945)
   - Signal: "Why An AI-Judged Beauty Contest Picked Nearly All White Winners"
   - Reasoning: Illustrates algorithmic bias in high-stakes decisions; relevant but generic.

6. **doc_extractor + aiid-165** (cos=0.2031)
   - Signal: "What a machine learning tool that turns Obama white can (and can't) tell us"
   - Reasoning: Image processing bias; the OCR pipeline touches image inputs, but the risk vector is different.

---

## Top-5 Highest-Cosine Pairs Scored 0

These are the pairs where the retriever was most confident but the LLM said "no." The question: correctly 0, or conservative?

| System | Signal (id) | Title (truncated) | Cosine | Score |
|--------|-------------|-------------------|--------|-------|
| telematics_pricer | aiid-8 | "Witness says self-driving Uber ran red light..." | 0.3660 | 0 |
| customer_chatbot | aiid-148 | "Website Accessibility Overlay False Claims" | 0.3285 | 0 |
| telematics_pricer | aiid-145 | "We tried Tesla's 'full self-driving'..." | 0.3242 | 0 |
| telematics_pricer | aiid-71 | "Who's Responsible When a Self-Driving Car Crashes?" | 0.3186 | 0 |
| telematics_pricer | aiid-20 | "Who's to blame when robot cars kill?" | 0.3133 | 0 |

**Read on each:**

- **telematics_pricer / AV incidents (4 of the 5):** Scorer reasoning correctly distinguishes "the telematics system scores *human driver behavior* from telemetry data; autonomous vehicle incidents concern *AI systems controlling vehicles*." The word "driving" appears in both contexts but the domain is completely different. These 0s are **correct**.

- **customer_chatbot / aiid-148 (accessibility overlays):** The chatbot is an LLM on web/mobile; "accessibility overlay" triggered a surface-level web/UI match. The signal is about false advertising by accessibility vendor companies. Scorer says no connection to chatbot behavior or risk. Also **correctly 0**.

The LLM scorer is not being conservative. These are genuine non-matches that the embedding model couldn't distinguish.

---

## Hypothesis Assessment

Four candidate explanations were considered:

**(a) AIID signals genuinely don't overlap with this portfolio.**
**(b) Retrieval threshold of 0.3 is passing through unrelated pairs; scorer is correctly calling them 0.**
**(c) Scorer is miscalibrated and underscoring real matches.**
**(d) System text construction doesn't match AIID vocabulary.**

**My read: (a) is the primary cause. (d) is a real contributing factor. (b) is partially true but not the root problem. (c) is not supported by the evidence.**

The AIID corpus skews heavily toward consumer-facing AI products: autonomous vehicles, social media recommenders, image generation, chatbots at tech companies, hiring algorithms, facial recognition in consumer contexts. This portfolio is an insurance company's *internal* ML stack: fraud detection on claims data, actuarial underwriting models, document OCR, telematics regression. These are different sectors, different incident vocabularies, and different failure modes.

The embedding model (`all-MiniLM-L6-v2`) captures semantic similarity at a general level. It sees "vehicle" and "driving" in telematics and matches it to AV incidents. It sees "image processing" in the OCR system and matches it to facial recognition incidents. The retriever is surfacing the nearest AIID neighbors, which happen to be wrong neighbors because the AIID data just doesn't cover internal insurance ML the way it covers consumer AI.

Against (c): the LLM reasoning on every 0 is well-grounded, concise, and demonstrates the model correctly read the domain mismatch. The scorer is working. The inputs it's receiving are the problem.

Against (b): the threshold letting through weak pairs is fine given the data. The alternative is zero candidates per system for most systems.

---

## Optional follow-up actions (not doing now)

These are paths available if we decide the distribution matters before Day 6. None of these are on the plan.

1. **Lower retrieval threshold to 0.2, increase top-N to 15-20 per system.** Would score more pairs and give a denser eval set. The ones added would mostly score 0-1, but we'd have better coverage for labeling. Risk: more LLM calls, more cost.

2. **Expand `known_risks` in the portfolio YAML to include LLM-era terminology.** Add phrases like "prompt injection," "hallucination," "model drift," "data poisoning," "fairness auditing" to the system cards. This would close the vocabulary gap with AIID's AI-safety-native language and improve retrieval quality. Low cost, high impact. Best candidate if we want to shift the distribution.

3. **Add 5-10 targeted adversarial signals to the eval set on Day 6.** Signals that *should* score 3-4 against specific systems (e.g., an NAIC bulletin on algorithmic underwriting bias, an AIID incident about LLM hallucination in insurance context, a regulatory guidance on adverse action explanations). These would give the eval set coverage at the high end of the rubric. Day 6 already plans some synthetic signal seeding; this just makes it intentional.

4. **Swap AIID corpus for a broader signal set.** Include regulatory summaries (NAIC model bulletins, EU AI Act articles relevant to insurance) alongside AIID incidents. These would use governance-native vocabulary and match the portfolio much more directly. Meaningful scope increase.

**If choosing one:** option 2 (expand `known_risks` vocabulary) has the best effort/impact ratio and is reversible. Do it as a targeted edit to the YAML before Day 6 labeling, not as a Day 5 task.
