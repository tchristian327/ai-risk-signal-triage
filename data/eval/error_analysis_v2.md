# Error analysis — LLM judge v2

**12 pairs with abs error >= 2 out of 49**

Sorted by absolute error descending. Pairs where the model was off by 2+ points.
Human label is ground truth.

## [1] Wrongfully arrested man sues Detroit police over false facial recognition match / Auto Claims Summarizer

- **Abs error:** 4 (under-scored)
- **Human label:** 4
- **LLM score:** 0
- **Signal ID:** `aiid-74`
- **System ID:** `auto_claims_summarizer`
- **Human note:** photo analysis is a data input for the summarizer.

**LLM reasoning:**

> The signal describes a facial recognition misidentification leading to wrongful arrest in law enforcement. The Auto Claims Summarizer is an LLM that processes adjuster notes, repair estimates, transcribed statements, and vehicle damage photos via a vision model—it does not perform identity matching or facial recognition. While both systems involve AI, the failure mechanism (biometric misidentification) and use case (criminal identification vs. claims documentation) are fundamentally different. The signal does not illustrate any of the system's known risks: hallucination of damage amounts, prompt injection, inconsistent summarization, PII leakage, or grounding failures on low-quality documents.

**LLM justification:**

> The signal concerns facial recognition misidentification in law enforcement, which has no meaningful connection to an LLM-based claims summarization system that does not perform identity matching or influence coverage decisions.

---

## [2] Why Twitter’s image cropping algorithm appears to have white bias / Customer Service Chatbot

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `aiid-103`
- **System ID:** `customer_chatbot`
- **Human note:** systemic racial biases in ai systems influencing decision making.

**LLM reasoning:**

> The signal describes Twitter's image cropping algorithm exhibiting bias in how it prioritizes content in images. The Customer Service Chatbot system card specifies that the chatbot uses a vision model for processing customer-supplied inputs and handles routine inquiries via web and mobile interfaces. However, the chatbot's stated purpose is to answer policy questions, billing inquiries, and claims status—text-based interactions—not to process or crop images as a core function. While the chatbot may receive images in customer conversations (e.g., photos of damage for claims), the system card does not indicate that image cropping or prioritization is a function the model performs. The signal's failure mechanism (algorithmic bias in visual content selection) does not map to the chatbot's documented risks, which focus on hallucination of policy details, prompt injection, escalation failures, and tone issues.

**LLM justification:**

> The signal describes bias in image cropping algorithms, which is unrelated to the Customer Service Chatbot's core function of answering text-based policy, billing, and claims inquiries. The chatbot does not perform image cropping or prioritization as part of its documented operations.

---

## [3] YouTube algorithm accidentally blocks 'black v white' CHESS strategy / Document OCR and Extraction Pipeline

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `aiid-144`
- **System ID:** `doc_extractor`

**LLM reasoning:**

> The signal describes YouTube's content moderation AI misinterpreting chess terminology ("black v white") as racist language, resulting in channel blocking. The Document OCR and Extraction Pipeline extracts structured data from insurance documents (medical bills, police reports, contractor estimates) using vision and LLM components. While both systems involve AI, the failure mechanism in the signal—semantic misclassification of benign domain-specific language—differs fundamentally from the known risks in the system card, which focus on hallucination of field values, adversarial document manipulation, handwriting recognition bias, OCR errors on low-quality scans, and data access controls. The signal does not involve document extraction, structured field population, or the specific modalities (OCR, medical/legal document processing) that characterize the insurance system.

**LLM justification:**

> The signal describes a content moderation misclassification on video platforms with no connection to document extraction, OCR, or insurance claim processing. The failure mechanism and system context are entirely distinct from the Document OCR and Extraction Pipeline.

---

## [4] Zhihu said that it has never installed a perception system to monitor employee behavior! Sangfor related cases are no longer visible / Underwriting Risk Scorer

- **Abs error:** 3 (under-scored)
- **Human label:** 3
- **LLM score:** 0
- **Signal ID:** `aiid-204`
- **System ID:** `underwriting_scorer`
- **Human note:** both have to do with risk assessment

**LLM reasoning:**

> The signal describes a workplace monitoring system designed to detect employee turnover intention and sabotage at a Chinese tech company (Zhihu/Sangfor). The Underwriting Risk Scorer is a personal auto insurance pricing model that uses applicant demographics, driving history, credit scores, and geographic factors to assign pricing tiers and make underwriting decisions. While both involve AI systems, the signal's focus on employee behavior monitoring has no connection to the underwriting model's inputs (driving records, credit scores, geographic risk), its purpose (insurance pricing), its users (underwriting teams, actuaries, agents), or its known risks (fairness in credit/geographic features, adverse action notices, label leakage from underwriting decisions, model drift, auto-decline mechanisms). The failure mode in the signal—workplace surveillance and potential privacy violations—does not map to any mechanism in the insurance underwriting context.

**LLM justification:**

> The signal concerns employee monitoring systems in a tech company and has no meaningful connection to an auto insurance underwriting model. The domains, data inputs, use cases, and risk categories are entirely distinct.

---

## [5] CFPB Circular 2022-03: Adverse Action Notice Requirements for AI Credit Models / Auto Claims Summarizer

- **Abs error:** 2 (under-scored)
- **Human label:** 3
- **LLM score:** 1
- **Signal ID:** `gov-008`
- **System ID:** `auto_claims_summarizer`
- **Human note:** i think what's important to remember about the summarizer is it is not making decisions like some of the machine learning models are.

**LLM reasoning:**

> The CFPB Circular 2022-03 requires that AI models producing adverse outcomes must provide explainable reasons for those outcomes under FCRA and ECOA, rejecting opacity as an excuse. The Auto Claims Summarizer is an LLM that generates structured summaries of claims and is "not used for coverage decisions" per the system card. However, the signal explicitly notes that the circular applies to "insurers using AI in underwriting, fraud flagging, or pricing decisions that produce adverse outcomes." The Claims Summarizer's output is reviewed by adjusters before finalization and is used to standardize documentation—it does not directly make coverage, pricing, or fraud flagging decisions that would trigger adverse action obligations. The system is a documentation tool, not a decision-making model that denies claims or imposes surcharges.

**LLM justification:**

> While the CFPB circular addresses AI explainability in insurance contexts, it targets models that make adverse decisions (underwriting, pricing, fraud flagging). The Auto Claims Summarizer is explicitly not used for coverage decisions and serves only to summarize and standardize claim documentation for adjuster review, placing it outside the direct scope of this regulatory requirement.

---

## [6] Worst Chatbot Fails / Auto Claims Summarizer

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-6`
- **System ID:** `auto_claims_summarizer`
- **Human note:** summarizer isn't a chatbot but still worth noting.

**LLM reasoning:**

> The signal is a 2016 article titled "Worst Chatbot Fails" from the AI Incident Database with a vague description about chatbots being "too smart for their own good," but provides no specific incident details, failure mechanisms, or concrete examples. The Auto Claims Summarizer is an LLM deployed in a structured claims processing workflow where adjusters review outputs before finalizing claims—not a conversational chatbot. While both involve language models, the signal lacks specificity about what failure modes it documents, making it impossible to connect to the system's known risks (hallucination, prompt injection, grounding failures, PII leakage). Without concrete incident details, there is no basis to assess whether the signal's failure mechanism relates to the summarizer's documented vulnerabilities.

**LLM justification:**

> The signal provides no specific incident details or failure mechanisms—only a generic title about chatbot failures. The Auto Claims Summarizer is a structured summarization tool with human review built in, not a conversational chatbot, and the vague description offers no actionable connection to the system's known risks.

---

## [7] Consumer Reports Investigation: How Algorithmic Pricing Sets Auto Insurance Rates / Auto Claims Summarizer

- **Abs error:** 2 (under-scored)
- **Human label:** 4
- **LLM score:** 2
- **Signal ID:** `gov-018`
- **System ID:** `auto_claims_summarizer`
- **Human note:** definitely want to make sure the summarizer isn't showing any biases from the data inputs.

**LLM reasoning:**

> The signal describes algorithmic pricing models that incorporate non-driving factors (education, occupation, homeownership, credit scores) as proxies for risk, creating disparate impact by race and income. The Auto Claims Summarizer is an LLM that generates structured summaries from adjuster notes, photos, and repair estimates—it does not make pricing or coverage decisions and is explicitly noted as "not used for coverage decisions." However, the signal raises a systemic concern about how insurers use algorithmic models to make consequential decisions affecting policyholders. The system card lists "PII leakage if generated summaries are logged, cached, or shared outside the claims management system" as a known risk. If summaries containing sensitive information (claimant recorded statements, adjuster notes) are inadvertently exposed or used downstream in pricing or underwriting systems, they could become inputs to discriminatory algorithmic decision-making. Additionally, the signal's emphasis on fairness audits and adverse action explainability for algorithmic systems is relevant to the broader ecosystem in which the Claims Summarizer operates, even though the summarizer itself is not a pricing model.

**LLM justification:**

> The signal addresses algorithmic fairness and disparate impact in insurance pricing, which is tangentially relevant to the Claims Summarizer. While the summarizer does not make pricing decisions, the signal highlights systemic risks in algorithmic decision-making within insurance and raises concerns about PII exposure and downstream use of model outputs—risks that could affect the summarizer if its outputs are shared beyond the claims management system or used to inform other algorithmic decisions.

---

## [8] Why Google 'Thought' This Black Woman Was a Gorilla / Auto Claims Summarizer

- **Abs error:** 2 (under-scored)
- **Human label:** 4
- **LLM score:** 2
- **Signal ID:** `aiid-16`
- **System ID:** `auto_claims_summarizer`
- **Human note:** concerns for vision model.

**LLM reasoning:**

> The signal describes a 2015 Google Photos incident involving misclassification of a Black person as a gorilla—a failure in image recognition/classification. The Auto Claims Summarizer uses a vision model to process vehicle damage photos as one of its data inputs. While the failure mechanism differs (identity misclassification vs. damage assessment), both involve vision models operating on images. The signal illustrates a class of vision-model error (systematic misclassification, potentially under distribution shift or bias) that could manifest in the claims context if the vision model fails to correctly identify damage types, severity, or vehicle components. The system card explicitly lists "Grounding failures when source documents are low-quality scans, causing the model to fabricate structured fields" as a known risk, and vision model failures on photos could contribute to such grounding failures.

**LLM justification:**

> The signal illustrates a vision model misclassification failure that, while different in domain, raises concerns about systematic bias and robustness in image processing—a class of error relevant to the vision component of the Auto Claims Summarizer. Model owner should be aware of potential vision model failure modes when processing vehicle damage photos.

---

## [9] Who's driving? Autonomous cars may be entering the most dangerous phase / Claims Fraud Detector

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-67`
- **System ID:** `fraud_detector`
- **Human note:** i think we just want the fraud detector to be aware of situations like this.

**LLM reasoning:**

> The signal discusses autonomous vehicle autopilot capabilities and the risks of incomplete automation creating false confidence in safety systems. The Claims Fraud Detector is a gradient boosted tree model that scores auto insurance claims for fraud using claim metadata and historical patterns. While both involve vehicles and AI systems, the signal addresses a vehicle safety/autonomy issue unrelated to insurance fraud detection. The signal contains no information about fraudulent claims, claim patterns, investigator bias, proxy variables, or any mechanism that would affect how the fraud model scores claims or flags suspicious activity.

**LLM justification:**

> The signal concerns autonomous vehicle safety and autopilot limitations, which has no meaningful connection to a fraud detection model that analyzes claim metadata and historical patterns to identify suspicious insurance claims.

---

## [10] Yes, artificial intelligence can be racist / Claims Fraud Detector

- **Abs error:** 2 (under-scored)
- **Human label:** 4
- **LLM score:** 2
- **Signal ID:** `aiid-11`
- **System ID:** `fraud_detector`

**LLM reasoning:**

> The signal is a 2016 commentary asserting that AI can exhibit racial bias, attributed to Alexandria Ocasio-Cortez. While the signal addresses AI bias as a general phenomenon, it provides no specific incident, mechanism, or evidence. The Claims Fraud Detector system card explicitly identifies "Disparate impact on protected classes via proxy variables (zip code, vehicle type, repair shop)" as a known risk. The signal's broad claim about AI bias potential is relevant to this known risk category, but the signal lacks concrete details about fraud detection, insurance claims, proxy variables, or any specific failure mode that would directly inform the model owner's mitigation efforts. The signal is too generic and dated to warrant immediate action, though it reinforces the importance of the already-documented bias risk.

**LLM justification:**

> The signal affirms that AI bias is real, which aligns with the system's documented risk of disparate impact via proxy variables, but provides no specific incident, mechanism, or evidence relevant to fraud detection or insurance claims. Model owner should be aware of the general concern but no immediate action is triggered by this signal alone.

---

## [11] What we know so far about the fatal Tesla crash in Paris / Telematics Pricing Model

- **Abs error:** 2 (under-scored)
- **Human label:** 2
- **LLM score:** 0
- **Signal ID:** `aiid-211`
- **System ID:** `telematics_pricer`
- **Human note:** driving related

**LLM reasoning:**

> The signal describes a fatal Tesla crash in Paris involving a vehicle hitting cyclists, pedestrians, and a van. The Telematics Pricing Model uses driving behavior data (speed, braking, cornering, time-of-day) from enrolled policyholders to adjust renewal premiums, with the explicit purpose of identifying and pricing risky driving patterns. While the Tesla incident involves autonomous vehicle control systems rather than telematics-based behavioral scoring, both systems attempt to assess and respond to driving risk. However, the failure mechanism in the signal (autonomous vehicle collision) is fundamentally different from the system's mechanism (behavioral pattern analysis for pricing). The signal does not directly implicate telematics data collection, driving score computation, or premium adjustment logic.

**LLM justification:**

> The signal concerns autonomous vehicle safety and collision investigation, which is unrelated to the telematics pricing model's core function of analyzing driving behavior patterns to adjust premiums. The systems operate on different technical principles and failure modes.

---

## [12] What a machine learning tool that turns Obama white can (and can’t) tell us about AI bias / Telematics Pricing Model

- **Abs error:** 2 (over-scored)
- **Human label:** 0
- **LLM score:** 2
- **Signal ID:** `aiid-165`
- **System ID:** `telematics_pricer`
- **Human note:** no racial element to the pricing model.

**LLM reasoning:**

> The signal describes a 2020 incident involving a low-resolution image processing algorithm that exhibited racial bias (misidentifying Barack Obama's race). The Telematics Pricing Model uses regression and ML on driving behavior data (speed, braking, cornering, time-of-day, phone distraction) to adjust renewal premiums. While both involve AI systems, the signal's failure mechanism—image classification bias in low-resolution facial recognition—differs fundamentally from the telematics model's input domain (driving sensor data and behavioral patterns). However, the signal illustrates a broader class of AI bias risk (demographic-correlated model errors) that connects to the telematics system's documented known risk of "proxy discrimination" where driving patterns correlate with protected-class status. The signal demonstrates how seemingly neutral technical features can encode demographic bias, which is directly relevant to understanding how the telematics model's inputs (time-of-day, route density) might similarly encode protected characteristics.

**LLM justification:**

> The signal illustrates AI bias in image processing, which differs mechanically from telematics-based pricing, but it exemplifies the broader bias risk category already identified in the system card (proxy discrimination). The model owner should be aware of how demographic bias can emerge through seemingly neutral features, though this specific incident does not directly implicate the telematics system's architecture.

---
