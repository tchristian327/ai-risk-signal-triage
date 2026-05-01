# Error analysis — LLM judge v1

**17 pairs with abs error >= 2 out of 49**

Sorted by absolute error descending. Pairs where the model was off by 2+ points.
Human label is ground truth. Review these before Day 9 prompt iteration.

## [1] Wrongfully arrested man sues Detroit police over false facial recognition match / Auto Claims Summarizer

- **Abs error:** 4 (under-scored)
- **Human label:** 4
- **LLM score:** 0
- **Signal ID:** `aiid-74`
- **System ID:** `auto_claims_summarizer`
- **Human note:** photo analysis is a data input for the summarizer.

**LLM reasoning:**

> The signal describes a facial recognition misidentification incident involving law enforcement, while the Auto Claims Summarizer is an LLM-based system that processes text notes, repair estimates, and vehicle damage photos to generate claim summaries. Although both systems involve AI and image processing, the signal's core risk mechanism—facial recognition accuracy and false positive identification in criminal justice—has no direct parallel in the claims summarization context. The Auto Claims Summarizer uses vision capabilities only to process vehicle damage photos for damage assessment, not for identity verification or person identification. The signal's relevance to insurance claims processing is tangential at best, as it addresses a fundamentally different use case (law enforcement identification) with different error consequences and no shared technical or operational risk pathway.

**LLM justification:**

> The signal describes a facial recognition misidentification incident in law enforcement, which has no meaningful connection to an LLM-based auto claims summarization system that processes adjuster notes, repair estimates, and vehicle damage photos for documentation purposes.

---

## [2] Consumer Reports Investigation: How Algorithmic Pricing Sets Auto Insurance Rates / Auto Claims Summarizer

- **Abs error:** 4 (under-scored)
- **Human label:** 4
- **LLM score:** 0
- **Signal ID:** `gov-018`
- **System ID:** `auto_claims_summarizer`
- **Human note:** definitely want to make sure the summarizer isn't showing any biases from the data inputs.

**LLM reasoning:**

> The signal describes algorithmic pricing models that use non-driving factors (education, occupation, homeownership, credit scores) as proxies for risk, creating disparate impact by race and income. The Auto Claims Summarizer, by contrast, is designed to generate structured summaries of claims from adjuster notes, photos, and repair estimates—it does not make pricing, underwriting, or coverage decisions. The system card explicitly states the summarizer is "not used for coverage decisions." While both involve algorithmic decision-making in insurance, the signal's core risk mechanism (proxy discrimination in pricing algorithms) does not apply to a summarization tool that processes claim documentation after a policy is already in force. The signal's concerns about fairness audits, explainability of adverse actions, and disparate impact relate to underwriting and pricing workflows, not claims summarization.

**LLM justification:**

> The signal addresses algorithmic fairness and disparate impact in auto insurance pricing models, which is structurally unrelated to the Auto Claims Summarizer's function of generating post-claim documentation summaries. The summarizer does not make coverage or pricing decisions and therefore does not face the proxy discrimination risks described in the Consumer Reports investigation.

---

## [3] Why Google 'Thought' This Black Woman Was a Gorilla / Auto Claims Summarizer

- **Abs error:** 4 (under-scored)
- **Human label:** 4
- **LLM score:** 0
- **Signal ID:** `aiid-16`
- **System ID:** `auto_claims_summarizer`
- **Human note:** concerns for vision model.

**LLM reasoning:**

> The signal describes Google's image classification system misidentifying a Black person as a gorilla, which is a computer vision model failure involving racial bias in image recognition. The Auto Claims Summarizer system uses a vision model to process vehicle damage photos as one of its data inputs. However, the specific failure mechanism—racial bias in human/animal classification—is fundamentally different from the risks in the Auto Claims Summarizer, which processes vehicle damage imagery for structural and material damage assessment. While both systems use vision models, the signal's risk (discriminatory misclassification of people) does not map to the documented risks in the system card (hallucination of damage amounts, grounding failures on low-quality scans, PII leakage). The Auto Claims Summarizer's vision component is narrowly scoped to vehicle damage detection, not human classification.

**LLM justification:**

> The signal describes racial bias in human image classification, which is unrelated to the Auto Claims Summarizer's documented risks and use case of summarizing vehicle damage from photos and adjuster notes.

---

## [4] CFPB Circular 2022-03: Adverse Action Notice Requirements for AI Credit Models / Auto Claims Summarizer

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `gov-008`
- **System ID:** `auto_claims_summarizer`
- **Human note:** i think what's important to remember about the summarizer is it is not making decisions like some of the machine learning models are.

**LLM reasoning:**

> The signal addresses CFPB requirements for adverse action notice and explainability in AI credit models, specifically requiring creditors to identify principal factors behind denials or adverse outcomes. The Auto Claims Summarizer is an LLM used to generate structured summaries of insurance claims for documentation purposes, not for making coverage decisions, pricing, underwriting, or adverse action determinations. The system card explicitly states "Not used for coverage decisions." While both involve AI and insurance, the signal's regulatory focus on adverse action explainability and credit/underwriting decisions does not apply to a summarization tool that produces documentation for adjuster review rather than autonomous decision-making that triggers adverse outcomes.

**LLM justification:**

> The CFPB circular addresses explainability requirements for AI models that make adverse credit or underwriting decisions; the Auto Claims Summarizer is explicitly not used for coverage decisions and serves only to document and summarize existing claim information for human review. The regulatory obligation described in the signal does not apply to this system's actual use case.

---

## [5] EU AI Act Article 6 and Annex III: Insurance and Credit Scoring Classified as High-Risk AI / Auto Claims Summarizer

- **Abs error:** 3 (under-scored)
- **Human label:** 4
- **LLM score:** 1
- **Signal ID:** `gov-010`
- **System ID:** `auto_claims_summarizer`

**LLM reasoning:**

> The EU AI Act signal describes high-risk classification for "insurance risk scoring" and "individual risk assessment in life and health insurance," with mandatory conformity assessments, non-discrimination requirements, and explainability obligations. The Auto Claims Summarizer is an LLM that generates structured summaries of claims from adjuster notes and repair estimates—it is explicitly not used for coverage decisions, underwriting, or risk scoring. While both involve insurance and AI, the system card states the output is "a structured summary surfaced in the claims management UI" for adjuster review, not a risk assessment or scoring mechanism. The regulatory signal targets decision-making systems that determine eligibility or pricing; the Auto Claims Summarizer is a documentation tool that supports human adjuster review but does not make or recommend coverage/underwriting decisions.

**LLM justification:**

> The EU AI Act's high-risk classification applies to insurance risk scoring and underwriting systems, not claims summarization tools. The Auto Claims Summarizer is explicitly not used for coverage decisions and serves only to standardize documentation for human review, placing it outside the regulatory scope of Annex III.

---

## [6] Why Twitter’s image cropping algorithm appears to have white bias / Customer Service Chatbot

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `aiid-103`
- **System ID:** `customer_chatbot`
- **Human note:** systemic racial biases in ai systems influencing decision making.

**LLM reasoning:**

> The signal describes Twitter's image cropping algorithm exhibiting potential racial bias in how it prioritizes content in images. The Customer Service Chatbot system is an LLM that processes text-based customer inquiries (policy questions, billing, claims status) and does not involve image processing, computer vision, or image cropping functionality. While both systems involve AI, the specific risk mechanism—algorithmic bias in image selection and framing—has no direct application to a text-based conversational system that handles insurance customer service through language interactions.

**LLM justification:**

> The signal concerns image cropping algorithm bias, which is unrelated to the Customer Service Chatbot's core function of handling text-based policy inquiries, billing questions, and claims status via conversation. The chatbot does not process, analyze, or crop images as part of its operation.

---

## [7] Why Google 'Thought' This Black Woman Was a Gorilla / Document OCR and Extraction Pipeline

- **Abs error:** 3 (under-scored)
- **Human label:** 4
- **LLM score:** 1
- **Signal ID:** `aiid-16`
- **System ID:** `doc_extractor`
- **Human note:** the signal - misclassifying a black couple as gorillas - creates concern for the vision model used in this system

**LLM reasoning:**

> The signal describes Google's image classification system misidentifying a Black woman as a gorilla, which is a well-documented case of demographic bias in computer vision models. The Document OCR and Extraction Pipeline is explicitly identified in the system card as having a "known risk" of "demographic bias in handwriting recognition — model accuracy degrades on handwriting styles associated with non-native English speakers or older writers." While the signal focuses on image classification bias and the system's known risk is specifically about handwriting recognition bias, both involve vision-based AI systems exhibiting differential performance across demographic groups. However, the signal does not directly address handwriting recognition, document extraction, or the specific context of insurance claims processing, making the connection indirect rather than direct.

**LLM justification:**

> While the signal illustrates demographic bias in computer vision systems, it addresses image classification rather than the handwriting recognition and document extraction tasks specific to this system. The signal is tangentially related to the system's known demographic bias risk but does not provide actionable insights for the OCR pipeline's particular vulnerability.

---

## [8] YouTube algorithm accidentally blocks 'black v white' CHESS strategy / Document OCR and Extraction Pipeline

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `aiid-144`
- **System ID:** `doc_extractor`

**LLM reasoning:**

> The signal describes YouTube's content moderation AI misinterpreting chess terminology ("black v white") as racist language, resulting in channel blocking. The Document OCR system extracts text from insurance documents (medical bills, police reports, estimates) and populates claim fields. While both systems involve AI and text/content interpretation, the risk mechanisms are fundamentally different: YouTube's issue stems from semantic misclassification in content moderation policy enforcement, whereas the OCR system's documented risks involve hallucination of missing data, adversarial document manipulation, and OCR errors on low-quality scans. The signal does not address document extraction, structured data population, or the specific failure modes listed in the system card.

**LLM justification:**

> The signal describes a content moderation misclassification incident unrelated to document extraction or structured data population. The Document OCR system's known risks (hallucination, adversarial manipulation, OCR errors) do not overlap with YouTube's semantic misinterpretation of chess terminology.

---

## [9] Yes, artificial intelligence can be racist / Claims Fraud Detector

- **Abs error:** 3 (under-scored)
- **Human label:** 4
- **LLM score:** 1
- **Signal ID:** `aiid-11`
- **System ID:** `fraud_detector`

**LLM reasoning:**

> The signal is a 2016 commentary asserting that AI can exhibit racial bias, citing Alexandria Ocasio-Cortez. The Claims Fraud Detector system card explicitly identifies "disparate impact on protected classes via proxy variables (zip code, vehicle age, repair shop) that encode race or income" as a known risk. While the signal is generic and does not describe a specific incident or mechanism, it directly validates a concern already documented in the system's risk profile. The signal's core claim—that AI systems can be racist—is not hypothetical for this system; it is a documented, acknowledged vulnerability that the model owner should ensure is being actively monitored and mitigated.

**LLM justification:**

> The signal makes a general claim about AI bias that aligns with a known risk in the Claims Fraud Detector (disparate impact via proxy variables), but it provides no new incident, mechanism, or regulatory development specific to this system. The model owner is already aware of this risk category.

---

## [10] Xsolla fires 150 employees using big data and AI analysis, CEO’s letter causes controversy / Telematics Pricing Model

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `aiid-119`
- **System ID:** `telematics_pricer`

**LLM reasoning:**

> The signal describes Xsolla's use of "big data and AI analysis" to make mass employment termination decisions, which raises concerns about algorithmic decision-making affecting individuals. However, the Telematics Pricing Model is a regression-based system that adjusts insurance premiums based on driving behavior data, not an HR/employment decision system. While both involve AI-driven decisions affecting people, the risk mechanisms are fundamentally different: employment termination involves workforce management and potential discrimination in hiring/firing, whereas the telematics system involves pricing adjustments based on driving patterns. The signal does not address insurance pricing, telematics data, driving behavior analysis, or the specific known risks documented in the system card (proxy discrimination via driving patterns, sensor spoofing, location tracking privacy, model drift, or adverse action explainability).

**LLM justification:**

> The signal concerns algorithmic employment termination decisions at a payment services company and has no direct connection to insurance premium pricing based on driving behavior. The risk mechanisms, data types, and decision contexts are entirely distinct.

---

## [11] Zhihu said that it has never installed a perception system to monitor employee behavior! Sangfor related cases are no longer visible / Underwriting Risk Scorer

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `aiid-204`
- **System ID:** `underwriting_scorer`
- **Human note:** both have to do with risk assessment

**LLM reasoning:**

> The signal describes an employee monitoring system at Zhihu that tracks turnover intention and sabotage behavior—a workplace surveillance application. The Underwriting Risk Scorer is a personal auto insurance underwriting system that processes applicant demographics, driving history, credit scores, and geographic data to assign pricing tiers and make coverage decisions. While both systems involve AI and data processing, they operate in completely different domains (employee monitoring vs. insurance underwriting) with different data types, purposes, and risk profiles. The signal contains no information about insurance practices, fairness in pricing, adverse action procedures, or any mechanism that would apply to auto insurance underwriting.

**LLM justification:**

> The signal concerns employee behavior monitoring at a tech company and has no connection to personal auto insurance underwriting, pricing, or the specific risks documented in the Underwriting Risk Scorer's system card (fairness in pricing, adverse action notices, label leakage from underwriting decisions).

---

## [12] Welfare recipients to blame for Centrelink debt system failures, Senate inquiry told / Auto Claims Summarizer

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-57`
- **System ID:** `auto_claims_summarizer`

**LLM reasoning:**

> The signal describes a 2017 Centrelink debt system failure in Australia where government officials blamed welfare recipients for not engaging with agency communications. This incident involves a government automated system that generated debt notices, but the core issue was about system failures and blame-shifting, not about the specific technical risks present in the Auto Claims Summarizer. The Auto Claims Summarizer is an LLM-based system designed to summarize insurance claims using adjuster notes, photos, and repair estimates, with known risks including hallucination, prompt injection, PII leakage, and grounding failures. The Centrelink incident does not directly address any of these specific technical failure modes, nor does it involve insurance claims processing, vision models for damage assessment, or the particular deployment context of claims management systems.

**LLM justification:**

> The Centrelink incident involves a government welfare system and administrative communication failures, which shares no meaningful connection to the Auto Claims Summarizer's specific technical risks (hallucination, prompt injection, PII leakage, grounding failures) or its insurance claims processing domain.

---

## [13] Worst Chatbot Fails / Auto Claims Summarizer

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-6`
- **System ID:** `auto_claims_summarizer`
- **Human note:** summarizer isn't a chatbot but still worth noting.

**LLM reasoning:**

> The signal is a 2016 article titled "Worst Chatbot Fails" that discusses general chatbot failures and notes that these systems "can be helpful for a business. But sometimes they're too smart for their own good." The Auto Claims Summarizer is an LLM-based system that generates structured summaries from adjuster notes and other documents, with known risks including hallucination, prompt injection, and grounding failures. While both involve AI systems that can fail, the signal provides no specific details about failure modes, incident types, or risk mechanisms. The signal's vague reference to chatbots being "too smart" does not connect to any of the documented risks in the system card (hallucination of damage amounts, prompt injection via claimant narratives, PII leakage, etc.). The signal lacks concrete incident details, technical specifics, or actionable information relevant to this claims summarization system.

**LLM justification:**

> The signal is a generic 2016 article about chatbot failures with no specific incident details, technical mechanisms, or concrete examples that would apply to the Auto Claims Summarizer's documented risks. Keyword overlap on "AI" and "chatbots" does not establish meaningful relevance to this system's particular failure modes or deployment context.

---

## [14] Why An AI-Judged Beauty Contest Picked Nearly All White Winners / Document OCR and Extraction Pipeline

- **Abs error:** 2 (under-scored)
- **Human label:** 3
- **LLM score:** 1
- **Signal ID:** `aiid-49`
- **System ID:** `doc_extractor`
- **Human note:** descrimination based on race by ai in article and demogrpahic bias is a known risk of system against non-native english speakers or older writers

**LLM reasoning:**

> The signal describes an AI bias incident in a beauty contest judging system where demographic bias led to skewed outcomes. The Document OCR system card explicitly identifies "demographic bias in handwriting recognition — model accuracy degrades on handwriting styles associated with non-native English speakers or older writers" as a known risk. However, the specific bias mechanism differs: the beauty contest involved visual appearance classification bias, while the OCR system's documented bias concern is about handwriting style recognition. The signal does not address OCR, document extraction, insurance claims, or handwriting recognition specifically. While both involve AI demographic bias, the signal provides no actionable insight into the particular handwriting recognition bias pathway already identified in this system's risk profile.

**LLM justification:**

> The signal illustrates a general AI demographic bias problem, which tangentially relates to the system's known handwriting recognition bias risk. However, the signal concerns visual appearance classification in a beauty contest, not document processing or handwriting recognition, and offers no specific insights applicable to the OCR extraction pipeline.

---

## [15] Who's driving? Autonomous cars may be entering the most dangerous phase / Claims Fraud Detector

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-67`
- **System ID:** `fraud_detector`
- **Human note:** i think we just want the fraud detector to be aware of situations like this.

**LLM reasoning:**

> The signal discusses autonomous vehicle autopilot safety risks and the gap between perceived and actual capability, focusing on human-machine interaction in driving contexts. The Claims Fraud Detector system scores auto insurance claims using structured metadata (claim amount, vehicle type, location) and historical patterns to flag fraud for investigator review. While both involve automobiles and insurance-adjacent domains, the signal's concern about autonomous vehicle safety and human oversight does not directly relate to the fraud detection model's risk mechanisms: disparate impact via proxy variables, explainability gaps for flagged claimants, training data poisoning from investigator bias, concept drift in fraud tactics, or adversarial evasion by fraud networks. The signal does not address claim fraud detection, model bias, or the specific operational risks documented in the system card.

**LLM justification:**

> The signal concerns autonomous vehicle safety and human-machine interaction in driving, which has no meaningful connection to the fraud detection model's core function of scoring insurance claims for fraud risk using claim metadata and historical patterns.

---

## [16] What we know so far about the fatal Tesla crash in Paris / Telematics Pricing Model

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-211`
- **System ID:** `telematics_pricer`
- **Human note:** driving related

**LLM reasoning:**

> The signal describes a fatal Tesla crash in Paris involving a cyclist, pedestrians, and a van, which appears to relate to autonomous vehicle safety. The Telematics Pricing Model, however, is a regression-based system that adjusts insurance premiums based on driving behavior data (speed, braking, cornering, phone distraction) captured from enrolled policyholders' trips via mobile apps or plug-in devices. The Tesla incident involves autonomous vehicle control systems, whereas the telematics model is a pricing/underwriting tool that analyzes human driving patterns after-the-fact for premium adjustment. There is no overlap in the risk mechanisms: the signal concerns autonomous vehicle safety failures, while the system card identifies risks like proxy discrimination, sensor spoofing, and model drift in a behavioral pricing context.

**LLM justification:**

> The signal describes an autonomous vehicle safety incident, which has no meaningful connection to a telematics-based premium pricing model that analyzes human driving behavior for insurance renewal decisions. The risk mechanisms are entirely distinct.

---

## [17] Why Oakland Police Turned Down Predictive Policing / Telematics Pricing Model

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-54`
- **System ID:** `telematics_pricer`
- **Human note:** driving related

**LLM reasoning:**

> The signal describes Oakland Police's rejection of predictive policing technology due to bias concerns. While both the signal and the Telematics Pricing Model involve algorithmic decision-making, the mechanisms and contexts differ substantially. The signal focuses on geographic/crime prediction bias in law enforcement, whereas the Telematics Pricing Model's documented bias risk is proxy discrimination through driving patterns (time-of-day, route density) correlating with protected characteristics. The signal does not address driving behavior analysis, telematics data, insurance pricing, or the specific technical vulnerabilities (sensor spoofing, location tracking, model drift) documented in the system card. The rejection rationale in predictive policing does not directly inform the risk profile of a vehicle-based behavioral pricing system.

**LLM justification:**

> The signal concerns bias in geographic crime prediction by police departments, which has no direct connection to driving behavior-based insurance pricing. The risk mechanisms, data types, and deployment contexts are fundamentally different.

---
