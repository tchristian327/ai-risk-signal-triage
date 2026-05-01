# Labeling Notes

Observations from the Day 6 labeling session. These capture recurring patterns, rubric edge cases, and anything relevant to prompt iteration or the interview discussion.

## Decision-making vs. information-providing systems

The rubric applies differently depending on whether a system produces a consequential decision or a summary for a human to act on. The Auto Claims Summarizer doesn't make decisions -- it surfaces information for adjusters. This consistently pushed scores down by one relative to what a decision-making model would receive for the same signal. Adverse action signals (CFPB circular, FCRA explainability) are weaker fits for the summarizer than for the underwriting scorer or fraud detector, even when the underlying risk concept is similar.

## Vision model exposure is easy to underestimate

The Auto Claims Summarizer uses photo analysis as a data input. Several vision-related incidents (e.g., racial misclassification in image models) scored higher than expected because of this. The system description mentions vision as an input but it's easy to overlook when reading quickly -- the LLM judge may miss this connection too, which is worth checking in the error analysis.

## Chatbot incidents don't transfer cleanly to the summarizer

The summarizer is not a chatbot. Incidents about bots taking autonomous actions or producing harmful conversational outputs scored 1-2 rather than 3-4, even when the headline risk (hallucination, bias) was relevant in principle. The distinction between interactive and batch systems matters for scoring.

## Fairness signals are broadly relevant but system-specific in severity

Fairness and disparate impact signals came up frequently and applied across most systems, but severity varied a lot by system. The Underwriting Scorer and Doc Extractor had the strongest hits because demographic inputs or demographic-correlated features are explicit in their designs. Proxy discrimination through geographic or demographic inputs is a different mechanism than a vision model misclassifying by race, and the rubric should distinguish them.

## Telematics vs. underwriting for location/behavioral signals

The FTC commercial surveillance ANPR is a stronger fit for the Telematics Pricer (which explicitly collects location and behavioral driving data) than for the Underwriting Scorer (which uses demographic and credit inputs but not continuous behavioral monitoring). The signal's specific language about consent and location tracking pushed the telematics score to 4 and the underwriting score to 3. The rubric distinction between "plausibly affects" (3) and "direct and immediate implications" (4) did useful work here.

## Driving-related incidents score low outside telematics

Autonomous vehicle incidents and driving safety signals were noted as "driving related" but mostly irrelevant to systems other than the Telematics Pricer, and even there they were 2s (worth a glance) rather than 3-4s -- Allstate's telematics product monitors driving behavior, it doesn't operate an autonomous vehicle.

## Hallucination signals were hard to place

A few hallucination signals scored unexpectedly low (1) on structured ML models like the Underwriting Scorer and Fraud Detector. These are not generative models -- hallucination in the LLM sense isn't a real failure mode for them. The rubric's "direct implication" language for score 4 requires the failure mode to actually be possible in the system, not just thematically adjacent.

## Score distribution

Final distribution across 49 labeled pairs: 0=8, 1=16, 2=7, 3=6, 4=12. The 3-bucket is thin relative to the original target (12-15 at score 3). Score 4 is slightly high. This likely reflects genuine skew in the signal set toward high-severity regulatory and fairness signals, but slight inflation bias during labeling can't be ruled out -- worth flagging when interpreting recall metrics.
