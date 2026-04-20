End-of-session housekeeping. Walk through these steps in order and report back what you did or didn't do.

1. **Review what we worked on this session.** Briefly summarize what changed in the repo since the start of this session: what files were added or modified, what was the goal, what got done, what didn't.

2. **Check CLAUDE.md for drift.** Review what changed this session and ask: "would a future Claude Code session starting cold need to know this to work correctly in this repo?" This is distinct from DECISIONS.md — CLAUDE.md captures how to work with the codebase (conventions, patterns, stack changes, non-obvious file relationships), not why decisions were made. If anything warrants a CLAUDE.md update, propose the specific addition or edit and wait for confirmation before writing anything. If nothing needs to change, explicitly say so and briefly explain why.

3. **Check DECISIONS.md for gaps.** Look at the work from this session and identify any non-obvious decisions that aren't yet captured in DECISIONS.md. A "non-obvious decision" is anything where we picked one approach over another, hit an unexpected blocker and pivoted, made a tradeoff, or discovered something about the problem space that would matter to a future session. If you find a gap, propose the entry (date, title, decision, why, alternatives considered if relevant) and ask me to confirm before appending it.

4. **Check PLAN.md for divergence.** Look at what was supposed to happen this session per the day's prompt, and compare it to what actually happened. If anything diverged — scope shifted, finished early or late, hit a blocker that pushed work to the next day, added something not in the plan — note it. Do not silently update PLAN.md. Surface the divergence to me and ask whether to add a note.

5. **Surprises and learnings.** In one or two sentences, name anything from this session that surprised you, changed your understanding of the problem, or is worth remembering for future sessions. This goes at the bottom of DECISIONS.md as a dated note if it's substantive enough to matter.

6. **Report.** Tell me: (a) any proposed CLAUDE.md changes, (b) what you propose to add to DECISIONS.md, (c) any divergence from PLAN.md you noticed, (d) any surprises worth noting, and (e) anything you noticed that I should know but doesn't fit any of the above categories. Wait for me to confirm before writing anything to CLAUDE.md, DECISIONS.md, or PLAN.md.

Hard rules:
- Do not modify CLAUDE.md without explicit confirmation. Propose changes and wait.
- Do not modify the SKILL.md files or any daily prompt files. Those are locked.
- Do not modify PLAN.md without my explicit confirmation, even for small things.
- Do not summarize "what we built" in code comments or commit messages — the code is its own record. The point of this exercise is capturing the *why*, not the *what*.
- Do not invent decisions to fill the file. If nothing non-obvious happened this session, the right answer is "no new decisions to add."
