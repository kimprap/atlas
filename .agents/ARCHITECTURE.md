# Atlas architecture

Atlas is the omp plugin `atlas`: it reads web sources the user names, stores one checked summary per source in a local SQLite store, and searches and answers from those summaries. One skill, `atlas-ask`, is the front door; it calls one CLI, and the CLI decides everything that happens to data.

This file is the canonical v2 contract. Rationale lives in `docs/adr/`; the full design with its acceptance checks is the approved specification `.agents/artifacts/atlas-v2-spec.md`. v2 is built in stages (spec section 6); a part marked "(stage N)" applies once that stage lands. v1 is history at tag `v1`; no v1 data, command, alias or shim is carried.

## Layout

```text
package.json                      name atlas, version 2.0.0, "omp": {}
skills/atlas-ask/SKILL.md         front door (turns a request into one flow; shows decisions; runs Reconcile)
skills/atlas-ask/cli.py           entry: python3 "$(realpath skill://atlas-ask)/cli.py" <command> [--mode] < body.json
skills/atlas-ask/atlas/core/      host-neutral logic: reply, approvals, config, identity, summarize, search, answer, topics, spend, status
skills/atlas-ask/atlas/store/     store interface + SQLite adapter + migrations/NNNN_<name>.sql
skills/atlas-ask/atlas/ports.py   read, call, judge, quota ports and host facts (Protocols and value types)
skills/atlas-ask/atlas/adapters/  omp.py (read, call, quota, host facts), jev.py (judge)
skills/atlas-ask/atlas/host.py    composition root: the only module that picks adapters
skills/atlas-ask/prompts/         summarize.md, atlas-rethink.md, MAINTENANCE.md, answer.md, rerank.md, rewrite.md
skills/atlas-init/SKILL.md        setup skill; prices.default.toml
rules/atlas-research.md           dev-research rule
tests/                            unittest suite; tests/contract/ (adapter contract suite); tests/fakes/ (fake host)
tools/release/release.py          release run, setup task (repo-only)
tools/quality/quality.py          quality check (repo-only)
tools/calibrate/near_copy.py      near-copy calibration (repo-only, stage 3)
.githooks/pre-push
```

- Python 3.11+ standard library only, so a link or git install needs no dependency install.
- Shipped plugin paths: `package.json`, `skills/`, `rules/`. Everything else is repo-only.
- Tests use stdlib `unittest`: `python3 -m unittest discover -s tests -t .`.

## Dependency direction

`cli.py` → `host.py` → (`core`, `store`, `adapters`).

- `core` imports `ports` and `store`'s interface only; it never imports `adapters` or `host`. `adapters` import `ports`.
- Core text, code and identifiers name no host, repo or host setting: the words `omp`, `openrouter`, `typesafe` and `modelRoles` never appear under `atlas/core/`. `jev` may appear there as the judge choice in `config.toml` and the ranker label in replies; the Jev endpoint, model id and key file live only in `adapters/jev.py`.
- `host.py` builds one `Host` value: `read`, `call`, `judge` (or none), `quota` (or none), `facts` (or none), and the store for the resolved profile. It picks the OMP and Jev adapters for `ATLAS_HOST=omp`, the default and only v2 value.
- Tests and the quality tool pass their own `Host` to `atlas.core.app.run(command, mode, body, host)`, the same function `cli.py` calls.

## Ownership

| Owner | Owns |
| - | - |
| `atlas-ask` skill | Talking to the user, writing the self-contained `question` and `context`, passing approvals, showing `decisions` and `next`, running Reconcile through its trusted-caller entry. It holds no confirm policy. |
| CLI core | Every rule that decides what happens to data: confirms, limits, fallbacks and outcomes. |
| `atlas-init` skill | The only writer of `~/.config/atlas/config.toml`, the key file instructions and the host's role lines, with one approval. The CLI never writes settings. |
| `atlas-research` rule | The dev-research entry (stage 8). |
| Release and quality tools | Repo-only; never shipped, never reached through `atlas-ask`. |

## CLI call and reply

Call: `python3 "$(realpath skill://atlas-ask)/cli.py" <command> [<action>] [--redo|--reread|--wide|--detail]` with one JSON object on stdin. `<action>` is the sub-step word of `inbox`, `topic` and `plan` (for example `plan show`). Profile: body `profile`, else `ATLAS_PROFILE`, else `default_profile` in `config.toml`.

Input is strict: invalid UTF-8, duplicate keys, `NaN` or `Infinity`, and any body that is not one JSON object are bad input (exit 2). `atlas/core/reply.py` owns this check and the reply.

Reply: one JSON object on one stdout line with exactly these keys:

```json
{"ok": true, "op": "add", "result": {}, "problems": [], "next": [], "decisions": []}
```

| Exit | Meaning | `ok` |
| - | - | - |
| 0 | done (a batch may still list per-item problems) | true |
| 1 | failed (store or adapter error not tied to one item) | false |
| 2 | bad input (includes an approval that does not match its decision) | false |
| 3 | not set up (no config, profile, store path, or a missing role); `result.needs_action` carries the fix | false |
| 4 | needs a decision: `decisions` is non-empty; `result` holds any work already done | false |

- `problems[]`: `{"link": <key link or null>, "field": <name>, "problem": <plain text>}`. One bad item never blocks a search or batch.
- `next[]`: 1–3 `{"label": <plain text>, "then": <action>}`; the skill shows the labels as Next.
- `decisions[]`: `{"id", "kind", "question", "options": [{"id", "label", "then"}]}`, `kind` ∈ `confirm`, `cap`, `window`, `pick_scope`, `summary_failed`, `judge_setup`, `version_save`, `already_current`.
- `then` is typed, so any front door follows it without Atlas policy: `{"resend": {<body fields to merge>}}` calls the same command again with these fields; `{"skill": "atlas-init"}` runs setup; `{"stop": true}` changes nothing.
- `decisions[].id` = first 16 hex of SHA-256 over the command, flags, the canonical body without `approval`, and `kind`. A resend whose `approval.decision` differs is exit 2 ("this approval is for a different change").
- `result` leaves out hashes, timings, ids and schema versions.

## Approvals

Every change command takes an optional `approval`:

```json
{"approval": {"by": "request", "words": "<the user's message, verbatim>"}}
{"approval": {"by": "confirm", "decision": "<decisions[].id>", "choice": "<option id>", "words": "<the user's reply, verbatim>"}}
```

- `by: "request"`: the user asked for this change in so many words. The caller sends it only for a change the user's own message requests, never for an agent proposal (research-end adds, tally note proposals, plan starts, version saves).
- `by: "confirm"`: the user's answer to a `confirm`, `cap` or `window` decision Atlas returned.

The CLI decides, per change, in this order:

1. Fixed stops always return a decision, whatever the setting: `version_save`, `pick_scope`, `summary_failed`, `judge_setup`, and cap and window yields.
2. `confirm.<change> = "never"`: run without approval.
3. `confirm.<change> = "always"` (default): run on `confirm`. Run on `request` only when the change is not paid at scale (not `add --redo`, and not an `add` or `add --reread` that would read 2 or more links after stored links are matched) and every target it names appears in `words` (each link after link cleanup, each topic name, a note's `who`, case-insensitive); else return a `confirm` decision.
4. A confirm and a cap or window yield on the same command merge into one decision whose question states the limit; going ahead counts as "continue anyway". A `never` change with a cap or window yield gets that one yield only, so no command makes two stops.

Change kinds with a setting: `add`, `add_redo`, `add_reread`, `inbox_add`, `note`, `archive`, `restore`, `follow`, `unfollow`, `plan_start`. No stop: tally lines, query records, `plan mark`, `topic draft`. Every applied change writes one `approvals` row (command, kind, `by`, `words`, decision id, time). The words check guards against acting on a vague "yes, add it"; it is not authentication.

## Ports and capabilities

| Seam | Kind | v2 adapters | Required by | When absent |
| - | - | - | - | - |
| store | module interface (records + BM25) | SQLite | every command | not set up (exit 3) |
| read | port | OMP (`omp read`), replay (quality tool), fake | `add` of a link | link-only `add` reports "no reader"; text given by the agent still works |
| call | port | OMP (`omp auth-gateway stdio`), fake | summaries, answers, rewrite, Opus rerank | not set up (exit 3) |
| judge | port, optional | Jev (OpenRouter Decisions), fake | rerank, wide gather, support, copies, marks | see "Judge" |
| quota | port, optional | OMP (`/v1/usage`), fake | window guard, `status` windows | guard off; batch confirm says "window use unknown"; status shows "windows unknown" |
| host facts | capability | OMP, fake | role check and fix lines, host version, role model context | fix lists role names and models without host syntax; no version warning; context taken as unknown |
| cross-check | front-door capability, not a CLI seam | `atlas-ask` + dotagents Reconcile trusted-caller entry | `plan save`, `topic save` | saved "not cross-checked: <reason>" |

Port shapes (`atlas/ports.py`; value types are frozen dataclasses):

```text
read(link, scope=None) -> Page | Unreadable
  Page: final_link, title, author, publisher, published, kind_hint, text, images[], links[], counts{words, links, images}, items[]
  kind_hint ∈ article | repo | docs | x_post | paper | video | image | link_list | unknown
  items[]: repo sub-items {path, link, kind} (skills, plugins, packages) from the full file list
  scope: None | "transcript" | "images" | {"sections": [...]}
  Unreadable: reason ∈ paywall | login | error | gone | no_transcript | no_reader, detail

call(role, messages, tools, tool_choice, max_output, images=[]) -> Reply
  Reply: model, thinking, content, tool_input | None, stop ∈ end | tool | cut_off | refused,
         usage{input, output, cache_read, cache_write}, cost{usd | None, kind ∈ billed | estimated | unknown}
  errors: RoleMissing(role), CallFailed(status, detail)

judge(state, questions) -> Judgments
  questions: [{id, type: noul | choice, text, options?}]
  Judgments: model, answers{id: {p} | {probabilities, confidence}}, cost{usd, kind: billed}
  errors: JudgeNotSetUp, JudgeFailed(status, detail) after backoff
  setup_problem() -> {what, fix: [lines], where} | None

quota.windows(providers) -> [{provider, window_id, duration_s, used_fraction, resets_at}]

facts: name, version() -> str | None, roles() -> {role: selector}, role_fix(missing{role: selector}) -> [lines],
       role_provider(role) -> str | None, role_context(role) -> int | None
```

- `tests/contract/suite.py` holds one case class per port, parametrized by an adapter factory; each adapter's test module binds it (fake offline, recorded OMP and Jev offline from `tests/fixtures/`, live OMP and Jev only with `ATLAS_LIVE=1`).
- The fake host (`tests/fakes/fake_host.py`) implements every port and capability from in-memory scripts and records each call, so core tests assert outcomes and call counts without a host.

## What the OMP adapter supplies

Core names roles and suggested models only: `atlas_summarize` → `anthropic/claude-sonnet-5-5:high`; `atlas_query`, `atlas_rerank`, `atlas_answer`, `atlas_escalate` → `anthropic/claude-opus-5-5:medium`. Everything host-shaped comes from `facts`:

| Fact | Used by | OMP adapter source |
| - | - | - |
| `roles()` | missing-role check before a paid call; `status` roles | `omp config get modelRoles` (JSON) |
| `role_fix(missing)` | exit 3 `needs_action[].fix`; `atlas-init` role setup | the lines `modelRoles:` / `  <role>: <selector>` plus the target file from `omp config path` + `/config.yml` |
| `version()` | `status` host version warning | `omp --version` |
| `role_provider(role)` | window guard: which windows a batch uses | provider prefix of the role's selector |
| `role_context(role)` | page-length guard | `context_length` from gateway `/v1/models` |
| read details | `Page` fields | one `omp read <link>` process per page (90 s timeout; up to 4 at once); header lines parsed and removed; `URL:` → `final_link`; `Method` → `kind_hint`; GitHub and X counter lines removed; an X post keeps only the post and its author's replies, numbered in page order; repo `items` from the GitHub tree API (unauthenticated, stdlib `urllib`) |
| windows | quota port | gateway `/v1/usage` limits: `durationMs`, `resetsAt`, `usedFraction` |

`atlas-init` takes `role_fix` lines from `status` and applies them with its one approval, so no skill hard-codes host syntax. On omp the target file is a link into the dotfiles repo; `atlas-init` names that and leaves committing to the user.

## Judge

Jev is one dependency: OpenRouter Decisions `POST https://openrouter.ai/api/alpha/decisions`, model `~typesafe/jev-latest`, key `OPENROUTER_API_KEY` from `~/.config/atlas/openrouter.env` (mode 600; another mode is a `status` action item and the adapter refuses to read it). The key is read once per command and never printed, logged, stored or passed in argv.

| Use (stage) | Jev set up, call ok | Jev call fails after backoff | Profile chose Opus | Jev not set up, no choice saved |
| - | - | - | - | - |
| rerank in `find`, `ask` (4) | Jev noul per candidate over BM25 top 30; ranker `jev` | `atlas_rerank` ranks that search; reply says so | `atlas_rerank` | `judge_setup` decision before searching |
| wide gather `find --wide` (7) | Jev P ≥ 0.3 set added to the BM25 candidates; rest by P one Next away | Opus path; reply says so | Opus path | `judge_setup` decision |
| claim support in `add` (3) | flags at < 0.8 "supports" | record "support not checked" | "support not checked" | "support not checked"; `add` does not stop |
| copy flags after `add` (3) | "may be a copy of <link>" at P ≥ 0.5 | "copies not checked" | "copies not checked" | "copies not checked" |
| topic marks after `add`, redo (7) | mark at P ≥ 0.3 | "topics not matched"; next catch-up searches | no marks | no marks |
| catch-up search rerank (7) | Jev | Opus for that topic | Opus | `judge_setup` decision |

- Claim support: one request per claim, sent concurrently; its state holds only the claim and the passages around its quotes; one `choice` question, supports | contradicts | says nothing; any answer other than supports at P ≥ 0.8 flags the claim. A "supports" probability within 0.1 of 0.8 is asked once more with the option order reversed, and the flag uses the mean. Rerank and marks are not rerun.
- Backoff: 429 and 529 retried after 1, 2, 4 and 8 s, then `JudgeFailed`. Concurrency: `judge_concurrency`, default 8, one kept-open HTTPS connection per worker.
- Every judgment records its probability and the Jev model version.

## Configuration

`~/.config/atlas/config.toml` is written only by `atlas-init`; each key ships in the stage that first reads it:

```toml
default_profile = "main"                      # stage 2

[profiles.main]
store = "~/.local/share/atlas/main.db"        # stage 2
judge = "jev"                                 # stage 2: "jev" | "opus"
max_page_tokens = 150000                      # stage 3
judge_concurrency = 8                         # stage 3
rethink = true                                # stage 3
near_copy = 0.90                              # stage 3
reread_days = 30                              # stage 3
reread_new_text = 0.05                        # stage 3
cap_usd = 20.0                                # stage 3, optional, unset by default
cap_warn = 0.80                               # stage 3
window_stop = 0.90                            # stage 3
[profiles.main.confirm]                       # stage 3: "always" | "never"; all default "always"
add = "always"                                # also add_redo (5), add_reread, inbox_add (3), note, archive, restore (6), follow, unfollow, plan_start (7)

[prices."anthropic/claude-sonnet-5-5"]        # stage 3; USD per million tokens
input = 2.0
output = 10.0
cache_read = 0.2
cache_write = 2.5
```

- Profiles: `smoke` (stages 2 and 3 and every later smoke run; deleted and recreated freely), `main` (real data from stage 4), `eval` (quality check, stage 5).
- The price table ships as `skills/atlas-init/prices.default.toml`; `atlas-init` copies missing rows and the user edits them by hand. A recorded model with no price row gets cost kind `unknown` and a `status` action item.
- `max_page_tokens` is capped at run time to 80% of `role_context(atlas_summarize)` minus `max_output` when the host reports a context.

## Store

- One SQLite file per profile, WAL mode, foreign keys on; each command is one transaction per item, so a stop keeps finished work. Archive sets `archived_at`; nothing is hard-deleted.
- Before stage 4 the schema is rebuilt from `schema_dev.sql` when it changes. Stage 4 freezes it into `migrations/0001_baseline.sql` with `PRAGMA user_version = 1`; every later schema change is the next numbered migration, applied in one transaction on open, and the release run bumps the minor version for it.
- A store whose `user_version` is newer than the code stops with exit 1 "store is newer than this Atlas; check out a newer tag".
- Tables arrive with the commands that first use them: stage 3 `sources`, `links`, `page_text`, `claims`, `quotes`, `claim_flags`, `related_links`, `copy_flags`, `summary_history`, `source_fts` (FTS5, BM25), `inbox`, `calls`, `approvals`; stage 4 `queries`, `tally`; stage 6 `notes`; stage 7 `topics`, `versions`, `version_claims`, `marks`, `plans`, `plan_items`; stage 8 `citations`. Their key columns are in spec section 4.7.

## Commands

The ten commands; bodies list the fields beyond `profile` and `approval`.

| Command | Body | Result |
| - | - | - |
| `status [--detail]` | — | see "Status" |
| `add` | `items: [{link, text?, scope?}]`, `cited_in?` (8) | per item: `added`, `already stored, last read <date>`, `already stored as <link>`, `joined near copy (<share>%)`, `archived <date>`, `unreadable: <reason>`, `summary failed` (decision), `pick scope` (decision); dropped-claim counts; copy flags; topics flagged (7); re-read offer in `next` |
| `add --reread` | `items: [{link}]` | per item: `re-read, no meaningful change`, `updated (<n> claims changed)`, `unreadable, kept` |
| `add --redo` (5) | `links?` or `topic?`, `force?` | per item: `redone`, `redo failed, old summary kept`, `kept: needs scope` |
| `inbox` | `add: [links]` or `list` | count added; listed links |
| `find [--wide]` | `question`, `original`, `phrasings?`, `context?`; `--wide`: `brief`, `context?` | ranked sources (key link, title, author, date, last read); ranker; question as searched |
| `ask` | one of `question` (+`original`, `phrasings?`, `context?`), `source` (link), `topic`, `whats_new: true` | answer formats; labels, Model view, backing, writing model, ranker; `next` |
| `topic` | `create`/`draft`/`save`/`follow`/`unfollow`/`nothing_to_save`/`list` with `name`, `brief`, `draft`, `review` | topic or version saved; draft text |
| `plan` | `save` (`topic`, `text`, `items`, `review`), `mark` (`plan`, `item`, `state`), `show` (`topic?`) | plan saved; `show`: plans with `cross_check`, `run` and open items |
| `note` | `who`, `subject`, `lean`, `reason` | note as saved |
| `archive` / `restore` | `link` or `note` (6), `topic` (7), `citation` (8) | item hidden or restored |

`review` (from `atlas-ask` after Reconcile): `{"status": "complete" | "not_cross_checked", "reason", "run", "reviewers", "changes", "diff", "text"}`; the CLI stores the reviewed `text` and shows `changes` as given.

## Sources in (stage 3)

Identity:

- Link cleanup lives in `atlas/core/links.py` (carried from v1): explicit HTTP(S) only, no userinfo; scheme and host lowercased (IDNA), default ports, trailing slashes, fragments, `utm_*` parameters and numeric X `s` parameters dropped; the X host aliases `twitter.com`, `www.twitter.com` and `www.x.com` fold to `x.com`. Stage 3 adds the tracking parameters `fbclid`, `gclid`, `igshid`, `mc_cid`, `mc_eid` and splits site rules into `core/sites.py` (one tested row per site: X, GitHub, YouTube; the same rows mark unchangeable sources). No `www.` or http→https folding.
- `add` matches every given link against `links` before any read; a match is never read again.
- Content hash: SHA-256 of `Page.text` after NFC, line endings and whitespace runs normalized; for an image source it also covers each image's SHA-256 in page order.
- Near copy: word 5-gram shingles of the normalized text; candidates are stored sources whose 64-value MinHash estimate is ≥ 0.7; share = the smaller of the two exact containments. Share ≥ `near_copy` joins without a summary, and Next offers "store it separately instead".
- Copy flags: after a stored add, the 5 closest sources by BM25 on title plus abstract get one Jev noul each ("the same work?"); P ≥ 0.5 flags.

Pick scope (decisions resent as `{"items":[{"link", "scope"}]}`): a repo with 2+ items, `video`, `image` or mostly images, `link_list`, and a page over `max_page_tokens`. An "each link" or "each item" choice with 2+ links is paid at scale, so it gets a confirm. The choice is stored, so a re-add does not ask again. Images are transcribed by `atlas_summarize` into `[image <n>, transcribed by <model>]` blocks appended to the page text.

Summary pipeline:

- One `atlas_summarize` call with tool `record` (abstract; claims with section, text, basis and 1–3 word-for-word quotes; metadata; related links; X author replies), prompt `prompts/summarize.md` (rubric `r1`) as the cached system block, plus kind cues from `kind_hint` and the site table. `max_output` 64K tokens. A reply with no tool call gets one turn repeating "Answer only by calling `record`"; still none is a hard failure.
- Code checks: every quote is found in the normalized page text; claim, quote, abstract and claim-count bounds; no duplicate claims; basis in the enum; metadata and related links found on the page; X replies by the post's handle.
- Then the `atlas-rethink` turn (setting `rethink`), the checks again, Jev support, one repair turn listing exactly the remaining failures, Jev rechecks of changed claims, dropping of claims with a quote still missing, store. A hard failure escalates once through the same steps on `atlas_escalate`; still failing stores nothing and returns a `summary_failed` decision.
- Records keep model, thinking level, escalation, rubric version, rethink line, dropped count, and flags with P and Jev model.

Re-read (`add --reread`): if every cited quote is still found and the new text adds less than `reread_new_text` of new shingles, store the new hash and read date ("re-read, no meaningful change"). Otherwise diff by line, update only affected claims in one `atlas_summarize` call, and check changed claims only; unchanged claims keep their ids. Replies show `last_read`, and `next` offers one combined re-read of sources last read over `reread_days` ago, skipping unchangeable ones.

Redo (`add --redo`, stage 5): read each page in scope again (stored text when unreadable, gone or unchangeable, and the reply says so), rebuild the summary from scratch through the full pipeline, and drop the old summary only after the new one passes.

## Search and answers (stage 4)

- Search: BM25 over `source_fts` for each phrasing (the agent's `phrasings`, else 3 `atlas_query` rewrites of `question`; a failed rewrite searches `question` and says so), merged by reciprocal rank fusion (k = 60), top 30 to the ranker over title plus the first 700 characters of abstract and claims. `ask` answers from the top 10.
- Answer: `atlas_answer` through tool `answer`: claims shown with source link, label and reason, disagreements, gaps, Model view and tally lines. Labels are checked fail-closed in code; backing counts are computed in code.
- One query record per `ask` and `find`; `result.question_as_searched` appears when `question` differs from `original`.

## Spend, cap and window guard (stage 3)

- One `calls` row per paid call: Jev cost is billed; omp roles get an estimate from the price table, or `unknown` without a row.
- Cap: the sum of billed `cost_usd` in the profile's current calendar month (local time). From `cap_warn` × cap, and past the cap, every paid command returns a `cap` decision before its first paid call; a batch returns it before its next item with done and not-started counts. Options: continue anyway (this command only), raise the cap in `config.toml`, stop here.
- Window guard (batches only): before each item, any window at or past `window_stop` for the batch's providers returns a `window` decision with done and not-started counts and the reset time.
- A batch confirm shows an estimate "about $X at list price" and each window's current percent; Atlas does not predict window percent.
- Rerun after a stop needs no queue: stored links report as already stored, and a scoped redo skips records already on the current setup unless `force`.

## Topics, catch-up and marks (stage 7)

- `topic create` and `plan save` run on the plan's one confirm after Reconcile (`plan_start`). `topic draft` stores nothing. `topic save` is always a `version_save` decision first; on yes, `atlas-ask` runs Reconcile and resends with the review and the confirm. A version keeps copies of the claims it cites. `nothing_to_save` stores `reviewed_up_to` and clears marks.
- Reconcile runs in `atlas-ask` only; when it is not ready or refused, the user may go on and the save carries `not cross-checked: <reason>`.
- Catch-up (`ask` with `whats_new: true`): each followed topic is searched for sources added since its agreed version or `reviewed_up_to`; an answer call runs for a topic with new or marked sources, except when the set equals the one its last catch-up found changed no conclusion.
- Marks: after `add` and after a redo whose claims changed, one Jev noul per followed topic; P ≥ 0.3 marks. A redo or re-read that changes a claim cited by an agreed version flags that topic.

## Status

Default reply: action items first, then one line, then Next.

```json
{"needs_action": [{"what": "Role atlas_escalate is missing", "fix": ["modelRoles:", "  atlas_escalate: anthropic/claude-opus-5-5:medium"], "where": "/home/kim/.omp/agent/config.yml"}],
 "summary": "Profile main: 412 sources, inbox 3, judge Jev, Atlas v2.1.4",
 "detail": null}
```

- Action items, in order: no config or profile (run `atlas-init`); store newer than code; missing roles; the judge's setup problem; judge choice not saved; price row missing; cap at or past `cap_warn`; a window at or past `window_stop`; host version differs from the current tag's (warning, never blocks).
- `status --detail` adds profile, store path and size, roles and models, judge, counts, Atlas and host versions, this month's spend, windows, redo count, confirm settings and limits.
- Reconcile readiness is a front-door fact: `atlas-ask` checks it beside `status`.

## Repo citations and the research rule (stage 8)

`rules/atlas-research.md` applies where `ATLAS_PROFILE` is set: `dev-research` first runs `find` or `ask`, and at its end proposes adding every source the research relied on with `cited_in: {"repo", "file"}` as one confirm (never `request`). A later `add` with the same repo and file replaces that file's citations. Replies that change a claim, a topic's what's-new and the catch-up name the citing repos and files.

## Quality check (stage 5)

`tools/quality/quality.py` compares two refs of Atlas on the `eval` profile across the summary, search and answers lanes, with user spot checks and paired bootstrap intervals. Without `--yes`, `build-library` and `run` print the estimated cost and make no call. It reads a real profile only in `build-library` (none) and `promote` (one query record and its sources' page text), and writes only `eval`.

## Release and install

- `tools/release/release.py setup` sets `core.hooksPath` to `.githooks` (idempotent). `release.py shipped-paths <ref>` prints the shipped files at `<ref>`.
- `.githooks/pre-push`, for `origin` `refs/heads/main` only, starts `release.py publish --after-push <git push pid> --background <sha>` and exits 0 at once.
- The run waits for the push, works in its own clone under `~/.cache/atlas-release/` (lock, pass cache and log there, nice 19), so it makes no background write to the checkout. It proceeds only if `origin/main` is the pushed commit, runs the unittest suite and `check_skills.py skills` on that commit (found through `omp plugin list --json`), and tags only if both pass.
- Tags counted: `v2.<minor>.<patch>` only (`v1` ignored). Tag when the shipped paths changed since the last v2 tag, or always for the first (`v2.0.0`). Minor bump when that diff adds a migration; else patch.
- The annotated message holds `atlas v2.x.y`, the commit subjects since the last tag, and trailers `Omp-Version` and `Dotagents`; then a GitHub Release from it (a `gh` failure only logs).
- `status` version: in a checkout, `git describe --tags --match 'v2.*'`; else the `package.json` version, with no host version warning.
- Rollback: any earlier tag before stage 4; from stage 4, rolling back past a minor version leaves the store newer than the code (exit 1). Unlink: `omp plugin uninstall atlas`.
