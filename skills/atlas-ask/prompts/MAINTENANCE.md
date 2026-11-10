# atlas-rethink maintenance journal

This journal is append-only and provenance only. No prompt or code loads it. Later corrections append a new entry with `Supersedes`; they never rewrite an entry. Each entry records its kind, superseded entries, context, decision, applied paths, rejected alternatives, validation and revisit condition.

## ATLAS-RETHINK-MAINT-2026-11-10

- Kind: initial lens
- Supersedes: none
- Context: Atlas v2 stage 3 builds the summary pipeline of ticket 16 §4 ("Decide source summarization method", `.scratch/atlas-v2/issues/16-decide-source-summarization-method.md`) as the approved specification `.agents/artifacts/atlas-v2-spec.md` §4.9 states it. Ticket 16 §5 settles one same-conversation `atlas-rethink` turn after the draft, with a lean lens file and this journal, following the dev-workflow rethink pattern.
- Decision: `prompts/atlas-rethink.md` holds ticket 16 §5 item 1's six lenses word for word (page only, strength, attribution, main point, quote fit, lean), the instruction to fix the code-check failures listed with it in at most one correction pass, and the one report line `Rethink: corrected <what> | no change`. The summary pipeline (`atlas/core/summarize.py`) sends it as the user turn after the draft, with the failures and "Answer only by calling `record`", when the profile's `rethink` setting is true, and stores the report line as the source's `rethink_line`. The repair turn and the re-read update use the same lens only through this turn.
- Applied paths: `skills/atlas-ask/prompts/atlas-rethink.md`, `skills/atlas-ask/atlas/core/summarize.py`.
- Rejected alternatives (ticket 16, Rejected alternatives): a separate rethink turn; a rethink only when checks fail; a same-model rethink without lenses or checks after it; a stronger-model reviewer loop; v1's long guide with a self-graded checklist.
- Validation: `python3 -m unittest tests.test_summarize` runs the turn with the fake host, with the setting on and off, and checks that the report line is stored.
- Revisit condition: the quality check's summary lane (spec §4.15, ticket 13): `atlas-rethink` stays only if, across 3 runs, faithfulness or completeness is better and neither is worse; any other result removes it. Append an entry when that result or a change of lens wording lands.

| Source | Accessed | Use | Basis | Applied path | Local treatment |
|---|---|---|---|---|---|
| `.scratch/atlas-v2/issues/16-decide-source-summarization-method.md` §4, §5 | 2026-11-10 | adopted | resolved ticket | `skills/atlas-ask/prompts/atlas-rethink.md` | The six lenses, the one correction pass and the report line, word for word. |
| `.agents/artifacts/atlas-v2-spec.md` §4.9, §4.15 | 2026-11-10 | adopted | approved specification | `skills/atlas-ask/atlas/core/summarize.py` | The turn's place in the pipeline, the `rethink` setting, and the keep-or-remove test. |
