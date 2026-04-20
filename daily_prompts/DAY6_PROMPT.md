# Claude Code prompt — Day 6: Build the hand-labeled eval set

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 6. Then **load the `eval-framework` skill** by reading its `SKILL.md` file in full. This skill is the foundation for all of Week 2 and you should not start coding until you have read it.

After reading those, in your own words, give me a 4-5 sentence summary of what we're building today, why stratified sampling matters, and what the labeling workflow looks like from my perspective as the human labeler. Do not skip this step.

Once I confirm the summary, your task for Day 6 is to build the labeling tool and help me produce a hand-labeled eval set of ~50 (signal, system) pairs spanning the full 0-4 score range. The tool you build will be used by me — you will not be doing any labeling. Your job is to make labeling fast and pleasant so I actually finish it.

## What to build

1. **Build `src/eval_sampling.py`** with a function `select_eval_pairs(similarities, n_pairs=50) -> list[tuple[str, str]]` that returns a list of `(signal_id, system_id)` tuples to label.

   The sampling strategy is stratified on cosine similarity:
   - 1/3 from the high-similarity bucket (top of the cosine distribution across all pairs)
   - 1/3 from the medium-similarity bucket (middle third)
   - 1/3 from the low-similarity bucket (bottom third)

   Within each bucket, sample randomly. Use a fixed random seed (`random.seed(42)`) so the eval set is reproducible. Document the seed in a comment.

   The function should return exactly `n_pairs` tuples, distributed as evenly as possible across buckets (e.g., 17/17/16 for 50 pairs).

2. **Add the `LabeledPair` schema to `src/schemas.py`:**

   ```python
   class LabeledPair(BaseModel):
       signal_id: str
       system_id: str
       cosine_similarity: float
       human_label: int = Field(..., ge=0, le=4)
       human_note: str = ""
       labeled_at: datetime
   ```

3. **Build `scripts/label_eval_set.py`** as the CLI labeling tool. This is the script I will run interactively. Make it pleasant.

   Behavior:
   - On first run, calls `select_eval_pairs` and saves the list of pairs to label to `data/eval/pairs_to_label.json`. If that file already exists, skip selection and use the existing list (so I can resume).
   - Loads any existing `data/eval/labeled_pairs.json` to find which pairs I've already labeled.
   - Iterates through unlabeled pairs one at a time. For each pair, prints to the terminal:
     ```
     ════════════════════════════════════════════════
     Pair 17 of 50
     ════════════════════════════════════════════════

     SYSTEM: [system name]
     Purpose: [purpose]
     Model type: [model type]
     Data inputs: [data inputs as comma-separated]
     Known risks: [known risks as bullet list]

     ────────────────────────────────────────────────
     SIGNAL: [signal title]
     Source: [source] | Date: [date]
     Description: [full description]
     URL: [source URL]

     ────────────────────────────────────────────────
     RUBRIC:
       0 — Unrelated
       1 — Tangential
       2 — Worth a glance
       3 — Action recommended
       4 — Urgent review

     Score (0-4, or 's' to skip, 'q' to quit and save):
     ```
   - After I enter a score, prompt for an optional one-line note: `Note (optional, press Enter to skip):`
   - Save the labeled pair to `data/eval/labeled_pairs.json` immediately (after every single label, not at the end). This means if I quit halfway through I lose nothing.
   - Print a small running summary: "Labeled X / 50 so far. Distribution: 0=A, 1=B, 2=C, 3=D, 4=E"
   - If I type `q`, save and exit cleanly.
   - If I type `s`, skip this pair and move on (saves a "skipped" marker so it isn't shown again).
   - When all pairs are labeled, exit with a final summary.

4. **Build `data/eval/LABELING_NOTES.md`** as an empty template:

   ```markdown
   # Labeling notes

   Notes I wrote during the labeling session. These capture cases where the rubric was ambiguous,
   surprising patterns in the data, or anything I want to remember for the eval discussion in interviews.

   ## Format
   - One bullet per observation
   - Include the pair index if relevant
   - Be specific about what was confusing

   ## Notes

   (notes go here as I label)
   ```

   I will fill this in by hand as I label.

5. **Print a "ready to label" summary at the start of the script** that tells me how many pairs are queued, how many I've already done, and gives me a sense of what I'm in for ("Estimated time: ~60-90 minutes for all 50, you can stop and resume any time").

6. **Do not run the labeling tool yourself.** Build it, do a dry-run with `--dry-run` flag that shows the first 2 pairs without saving anything (to verify the rendering looks right), then stop and tell me to take over.

## Implementation notes

- **Save after every label.** This is non-negotiable. Each label triggers a write to `labeled_pairs.json`. JSON serialization for ~50 small objects is fast — don't try to "optimize" this with batching.

- **Append-safe save format.** When writing labeled pairs back, load the existing file, append the new entry, write the whole thing back. Don't try to be clever with append-mode JSON.

- **Graceful Ctrl+C.** Catch `KeyboardInterrupt` and save before exiting. Print "Saved progress, you can resume by re-running the script."

- **Terminal rendering.** Use plain ASCII or simple Unicode for separators. No color libraries (no `rich`, no `colorama`). The terminal output should look clean in any terminal.

- **The dry-run flag** should render the first 2 pairs exactly as the real labeler would, but without prompting for input or saving anything. I want to see what the rendering looks like before I commit to labeling 50.

- **Random seed.** Document in a comment that the random seed is fixed at 42 and what changing it would mean (different eval set, not directly comparable to previous runs).

## Definition of done

- `python scripts/label_eval_set.py --dry-run` shows the first 2 pairs rendered cleanly and exits without writing anything
- The rendering is readable and not cluttered
- The script is ready for me to run interactively
- `data/eval/LABELING_NOTES.md` exists as a template
- You have *not* labeled any pairs yourself

After I finish labeling (separately, on my own time), I'll come back and tell you how many pairs I labeled, what the distribution looked like, and whether the rubric felt fuzzy anywhere. That conversation will inform Day 7.

## Scope guardrails

- **Do not** label any pairs yourself. The whole point of Day 6 is that *I* hand-label them.
- **Do not** call the LLM scorer to "pre-label" or "suggest" labels. That would defeat the purpose — the human label needs to be uncontaminated by what the model thinks.
- **Do not** add any analysis or metrics today. Day 7 is metrics day.
- **Do not** modify the rubric. It's locked.
- **Do not** start building the trained classifier baseline. That's Day 8.
- **Do not** modify the dashboard.

## Skills to load

- `eval-framework` — apply the stratified sampling rule, the labeling-one-at-a-time rule, and the "label distribution after labeling" check.

When you're done, give me a short summary of: (1) what you built, (2) the dry-run output for the first 2 pairs, (3) any decisions you made that weren't in this prompt, and (4) anything you noticed about the cosine distribution that I should know going into labeling.
