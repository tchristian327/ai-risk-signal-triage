# Claude Code prompt — Day 9: Iterate the LLM judge prompt

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 9. Then **load both the `llm-judge-scoring` and `eval-framework` skills** by reading their `SKILL.md` files in full.

After reading those, in your own words, give me a 4-5 sentence summary of what we're doing today, what the hard rule about the rubric is, and how we measure whether iteration helped. Do not skip this step.

Once I confirm the summary, your task for Day 9 is to use the Day 7 error analysis to make targeted improvements to the LLM judge prompt, then re-evaluate and document what changed.

## Prerequisites

Before starting, confirm these files exist:
- `data/eval/labeled_pairs.json`
- `data/eval/metrics_llm_judge_v1.json`
- `data/eval/predictions_llm_judge_v1.json`
- `data/eval/error_analysis_v1.md`
- `data/eval/REPORT_WEEK2.md` with my Day 7 and Day 8 sections filled in

If `REPORT_WEEK2.md` doesn't have my sections filled in, stop and ask me. Day 9 depends on me having formed opinions about what's wrong — the iteration is driven by my error analysis, not yours.

## What to do

1. **Read my notes.** Read `REPORT_WEEK2.md` carefully, especially the "What I see" and "What I'd want to fix" sections. Then read `error_analysis_v1.md` and `LABELING_NOTES.md` from Day 6. Form a list of the specific failure patterns I'm targeting for fixes.

2. **Propose changes.** Before writing any code, write a short markdown file at `data/eval/PROPOSED_PROMPT_CHANGES.md` listing each change you propose to the prompt and why. Format:

   ```markdown
   # Proposed prompt changes for v2

   ## Change 1: [short description]
   **Failure mode it targets:** [reference a specific pattern from the error analysis]
   **What changes in the prompt:** [specific sentence or section being added/modified]
   **Why this should help:** [your hypothesis]
   **Risk:** [what could go wrong, e.g. "might overcorrect and start scoring too high"]

   ## Change 2: ...
   ```

   Maximum 4 changes. If you find yourself wanting to make more, you're not being targeted enough — pick the 4 highest-leverage ones.

3. **Stop and wait for me to approve the proposed changes.** Do not modify `src/scoring.py` until I've read the proposal and said go. This is an interrupt point, not a checkpoint you blow through.

4. **After I approve**, modify `src/scoring.py` to implement the v2 prompt:
   - The rubric constant (`RELEVANCE_RUBRIC`) is **not changed**. It is locked.
   - The prompt scaffolding *around* the rubric is what changes. That includes the role description, the asymmetric error costs framing, examples (if you add any), and the output instructions.
   - Add a constant `PROMPT_VERSION = "v2"` at the top of the file so we can distinguish v1 from v2 outputs.
   - The client factory (`get_llm_client()`) and Bedrock/fallback invocation logic do not change. Only the prompt scaffolding changes.
   - Keep the v1 prompt accessible in the file as a comment block (or in a separate module-level constant) for reference. Do not delete it.

5. **Re-run the eval.** Use `scripts/run_eval.py` (the same script from Day 7) but write outputs to the v2 paths:
   - `data/eval/metrics_llm_judge_v2.json`
   - `data/eval/predictions_llm_judge_v2.json`
   - `data/eval/error_analysis_v2.md`

   You may need to add a `--version v2` flag to the eval script that controls the output filenames. Do that if it's clean; otherwise duplicate the script as `scripts/run_eval_v2.py`. The first option is cleaner.

6. **Update the comparison.** Re-run `scripts/compare_systems.py` (or extend it) so the comparison table now shows three columns: LLM judge v1, LLM judge v2, baseline classifier. Write the updated comparison to `data/eval/COMPARISON.md`.

7. **Build `data/eval/PROMPT_CHANGELOG.md`** that lists each change you made (post-implementation, in actual past tense):

   ```markdown
   # Prompt changelog

   ## v2 (date)

   ### Change 1: [description]
   - Failure mode targeted: ...
   - Specific change: ...
   - Rationale: ...
   - Result: [improved by X on metric Y, no change on metric Z, regressed on...]

   ### Change 2: ...
   ```

   Be honest in the "result" sections. If a change didn't help, say so. If it regressed something, say that too. The point of this file is the interview talking point: "I made these specific changes for these specific reasons and here's what each one moved."

8. **Stub the next section of `REPORT_WEEK2.md`** for me:

   ```markdown
   ## Day 9: LLM judge v2

   ### Changes made
   (paste from PROMPT_CHANGELOG.md)

   ### Comparison: v1 vs v2 vs baseline
   (paste the updated comparison table)

   ### What I see
   (3-5 sentences in my voice)

   ### Was iteration worth it?
   (1-2 sentences — honest assessment of whether the v1 -> v2 work paid off)
   ```

   Do not fill in the prose sections.

## Implementation notes

- **The hard rule, again: do not change the rubric.** If your error analysis suggests the rubric is the problem, that's a finding to report in the changelog ("I noticed pattern X but the right fix would be a rubric change, which is locked, so v2 does not address it"), not a license to modify the rubric.

- **One change at a time, on paper.** The proposed changes file lists multiple changes, but each one should be conceptually independent. You should be able to point at any one change in the PROMPT_CHANGELOG and say "this change targeted this failure mode and produced this metric movement."

- **Don't overfit to the error analysis.** If you read the error analysis and discover that the LLM made a particular type of mistake on 4 specific pairs, the right response is to update the prompt to address the *general failure mode*, not to add example text from those exact pairs. The eval set is the eval set — using its content in the prompt is contamination.

- **No retraining needed for the baseline.** The baseline doesn't change between Day 8 and Day 9. We're only iterating the LLM judge.

- **Cost.** Re-running the eval is another ~50 API calls. Pennies. Same `--yes` flag pattern as before.

- **Time the v2 eval too.** We want to confirm that the v2 prompt isn't dramatically slower than v1. If it is, that's a tradeoff to document in the changelog.

## Definition of done

- `data/eval/PROPOSED_PROMPT_CHANGES.md` exists, you stopped and waited for my approval
- After approval: `src/scoring.py` has the v2 prompt and a `PROMPT_VERSION` constant
- `data/eval/metrics_llm_judge_v2.json` exists with v2 metrics
- `data/eval/COMPARISON.md` shows three columns (v1, v2, baseline) side by side
- `data/eval/PROMPT_CHANGELOG.md` exists with each change documented honestly, including non-improvements and regressions
- `REPORT_WEEK2.md` has the Day 9 section stubbed for me

## Scope guardrails

- **Do not** modify the rubric.
- **Do not** make more than 4 prompt changes.
- **Do not** modify the schemas.
- **Do not** modify the baseline classifier or the eval set.
- **Do not** delete the v1 prompt — keep it accessible for reference.
- **Do not** start polishing the dashboard or writing the README. That's Day 10.
- **Do not** hide regressions. If v2 is worse on some metric, that goes in the changelog and the report.

## Skills to load

- `llm-judge-scoring` — apply the failure mode list and the "what to do if the scorer is bad" playbook to drive the changes.
- `eval-framework` — apply the honest-reporting principle when documenting results.

When you're done, give me a short summary of: (1) the proposed changes (before implementation, you'll stop here for my approval), then after I approve and you complete the work: (2) the v1-vs-v2-vs-baseline comparison numbers, (3) which changes helped and which didn't, and (4) any concerns about Day 10.
