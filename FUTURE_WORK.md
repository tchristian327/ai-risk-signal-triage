# Future Work

Ideas deferred to keep the current build focused. Add entries here rather than
scope-creeping mid-day. Reference this file in the README's "what I'd do next"
section.

---

## LLM-generated signal summaries

The labeling UI currently shows the first ~1000 chars of each AIID news article
as signal context. An LLM-generated 2-3 sentence summary from the full article
body would produce cleaner, more information-dense previews at the cost of one
summarization API call per signal at ingest time. Deferred to keep the labeling
context fully deterministic and to avoid adding LLM-generated content to the
eval set pipeline.

---

## AIID incident-level curator descriptions

The AIID GraphQL endpoint at https://incidentdatabase.ai/api/graphql returned 403 on unauthenticated server-side requests during the Day 6 ingest. The `incident_description` field and its wiring in `src/ingest.py` and `scripts/label_eval_set.py` are in place and will activate automatically if the endpoint becomes accessible or if an authenticated API path is added. The labeling UI already falls back cleanly to showing only `full_text` when `incident_description` is empty.

Populating this field would produce shorter, more information-dense labeling previews (curator-written 1-2 sentence incident summaries vs. the current ~1000-char article extract). Worth revisiting if AIID makes the GraphQL API publicly accessible or if an API key becomes available.
