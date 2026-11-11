# Atlas architecture

Atlas is the omp plugin `atlas`: it reads web sources the user names, stores one checked summary per source in a local SQLite store, and searches and answers from those summaries. One skill, `atlas-ask`, is the front door; it calls one CLI, and the CLI decides everything that happens to data.

This file is the canonical v2 contract. Rationale lives in `docs/adr/`; the full design with its acceptance checks is the approved specification `.agents/artifacts/atlas-v2-spec.md`. v2 is built in stages (spec section 6); a part marked "(stage N)" applies once that stage lands. v1 is history at tag `v1`; no v1 data, command, alias or shim is carried.

## Layout

```text
package.json                      name atlas, version 2.0.0, "omp": {}
skills/atlas-ask/SKILL.md         front door (turns a request into one flow; shows decisions; runs Reconcile)
skills/atlas-ask/cli.py           entry: python3 "$(realpath skill://atlas-ask)/cli.py" <command> [--mode] < body.json
skills/atlas-ask/atlas/core/      host-neutral logic: reply, approvals, config, identity, summarize, search, answer, notes, topics, plans, marks, catchup, spend, status
skills/atlas-ask/atlas/store/     store interface + SQLite adapter + migrations/NNNN_<name>.sql
skills/atlas-ask/atlas/ports.py   read, call, judge, quota ports and host facts (Protocols and value types)
skills/atlas-ask/atlas/adapters/  omp.py (read, call, quota, host facts), jev.py (judge)
skills/atlas-ask/atlas/host.py    composition root: the only module that picks adapters
skills/atlas-ask/prompts/         summarize.md, atlas-rethink.md, MAINTENANCE.md, answer.md, draft.md, catchup.md, rerank.md, rewrite.md
skills/atlas-init/SKILL.md        setup skill; prices.default.toml
rules/atlas-research.md           dev-research rule
tests/                            unittest suite; tests/contract/ (adapter contract suite); tests/fakes/ (fake host)
tools/release/release.py          release run, setup task (repo-only)
tools/quality/quality.py          quality check: its commands; its modules sit beside it, replay_read.py is its read adapter (repo-only)
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
- `decisions[].id` = first 16 hex of SHA-256 over the command, flags, the canonical body without `approval`, and `kind`; a `version_save` id also leaves out `review`, which the front door adds on the resend because Reconcile runs after the decision is returned. A resend whose `approval.decision` differs is exit 2 ("this approval is for a different change").
- `result` leaves out hashes, timings, ids and schema versions. It carries the text the user asked for: each `add` item that names one stored source that is not archived carries its `abstract`.

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

Change kinds with a setting: `add`, `add_redo`, `add_reread`, `inbox_add`, `note`, `archive`, `restore`, `follow`, `unfollow`, `plan_start`. No stop: tally lines, query records, `plan mark`, `topic draft`, `topic nothing_to_save` (the user's pick of its Next line is its confirm). Every applied change writes one `approvals` row (command, kind, `by`, `words`, decision id, time); a saved version writes its row with kind `version_save`, and `nothing_to_save` and `plan mark` write none. The words check guards against acting on a vague "yes, add it"; it is not authentication.

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
  scope: None | "transcript" | "images" | {"sections": [...]}; "transcript" keeps the page's title line and its transcript section, else Unreadable("no_transcript")
  Unreadable: reason ∈ paywall | login | error | gone | no_transcript | no_reader, detail

image(link) -> bytes | Unreadable
  the bytes of one image (PNG, JPEG, GIF or WebP) for an image or mostly-images page; anything else is Unreadable

call(role, messages, tools, tool_choice, max_output, images=[]) -> Reply
  Reply: model, thinking, content, tool_input | None, tool_raw | None (stage 4), stop ∈ end | tool | cut_off | refused,
         usage{input, output, cache_read, cache_write}, cost{usd | None, kind ∈ billed | estimated | unknown}
  tool_input is None when the reply holds no usable tool call; tool_raw (stage 4) is then the host's raw tool text when it gave one
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

- `tests/contract/suite.py` holds one case class per port, parametrized by an adapter factory; each adapter's test module binds it (fake offline, recorded OMP and Jev offline from `tests/fixtures/`, the quality tool's replay read adapter offline from `tests/fixtures/quality/`, live OMP and Jev only with `ATLAS_LIVE=1`).
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
| read details | `Page` fields | one `omp read <link>` process per page (90 s timeout; up to 4 at once); header lines parsed and removed; `URL:` → `final_link`; `Method` → `kind_hint`, except that a GitHub `owner/repo` link is kind `repo` from the link itself (omp reports `Method: native` when GitHub's API refuses it); GitHub and X counter lines removed; an X post keeps only the post and its author's replies, numbered in page order; read scope `transcript` keeps the title line and the `## Transcript` section, else `Unreadable("no_transcript")`; repo `items` from the GitHub tree API (stdlib `urllib`; a failed file list makes the repo page unreadable). From stage 4 the request carries `Authorization: Bearer <token>` when `GITHUB_TOKEN`, else `GH_TOKEN`, holds a non-blank value in the command's environment (an empty or blank value counts as unset), and is unauthenticated otherwise; an unauthenticated HTTP 403 or 429 adds `set GITHUB_TOKEN or GH_TOKEN to raise GitHub's limit` to the `Unreadable("error")` detail. The token is read once per command, sent only to `api.github.com` (never on a redirect to another host), and never printed, logged, stored, put in a reply, problem or `Unreadable` detail, or passed in argv; Atlas never writes or loads it |
| image bytes | `read.image(link)` | one plain HTTP GET (30 s timeout), at most 5 MB, PNG, JPEG, GIF or WebP by its first bytes, else `Unreadable`; an image page lists its own link as its image |
| call details | `Reply` fields | a `tool_use` input carrying omp's `__parseError` placeholder (`{__parseError, __rawJson}`, sent when the model's tool JSON does not parse) is no tool call: `tool_input` is `None`, so core's one reminder runs; from stage 4 `tool_raw` holds its `__rawJson` text (omp cuts it to 512 characters) |
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
cache_read = 0.1
cache_write = 2.5
```

- Profiles: `smoke` (stages 2 and 3 and every later smoke run; deleted and recreated freely), `main` (real data from stage 4), `eval` (quality check, stage 5).
- The price table ships as `skills/atlas-init/prices.default.toml`; `atlas-init` copies missing rows and the user edits them by hand. A recorded model with no price row gets cost kind `unknown` and a `status` action item.
- `max_page_tokens` is capped at run time to 80% of `role_context(atlas_summarize)` minus `max_output` when the host reports a context.

## Store

- One SQLite file per profile, WAL mode, foreign keys on; each command is one transaction per item, so a stop keeps finished work. Archive sets `archived_at`; nothing is hard-deleted.
- Before stage 4 the schema is rebuilt from `schema_dev.sql` when it changes. Stage 4 freezes it into `migrations/0001_baseline.sql` with `PRAGMA user_version = 1`; every later schema change is the next numbered migration, applied in one transaction on open, and the release run bumps the minor version for it.
- A store whose `user_version` is newer than the code stops with exit 1 "store is newer than this Atlas; check out a newer tag".
- Tables arrive with the commands that first use them: stage 3 `sources`, `links`, `page_text`, `claims`, `quotes`, `claim_flags`, `related_links`, `copy_flags`, `summary_history`, `source_fts` (FTS5, BM25), `inbox`, `calls`, `approvals`; stage 4 `queries`, `tally`, `expansions`; stage 6 `notes` (migration `0002_notes.sql`, with an index on who and subject; `user_version` 2); stage 7 `topics`, `versions`, `version_claims`, `marks`, `plans`, `plan_items` (one migration, `0003_topics.sql`; `user_version` 3); stage 8 `citations`. Their key columns are in spec section 4.7.
- `links.kind` is `key` or `other`. `related_links.origin` (stage 4) is `page` when the page presents the link and `expansion` when the source is an item or link of that page. `expansions` (stage 4): link (the cleaned page link the user named), choice (`each_item`, `each_link` or `both`), time. One owner per fact: `links` maps a link to the source that holds it, `expansions` keeps the expanding choice per page link, and `related_links` with origin `expansion` keeps which sources that page produced.

## Commands

The ten commands; bodies list the fields beyond `profile` and `approval`.

| Command | Body | Result |
| - | - | - |
| `status [--detail]` | — | see "Status" |
| `add` | `items: [{link, text?, scope?}]`, `cited_in?` (8) | per item: `added` (with `title`, `abstract`, claim count, dropped and flagged claim counts), `already stored, last read <date>`, `already stored as <link>` and `joined near copy (<share>%)` (each with the stored source's `abstract`), `already added as <n> items` (stage 4; with the item sources' key links), `archived <date>`, `unreadable: <reason>`, `summary failed` (decision), `pick scope` (decision); dropped-claim counts; copy flags; `topics_marked` (the followed topics an added source was marked for) or `topics`: `topics not matched` (7); re-read offer in `next` |
| `add --reread` | `items: [{link}]` | per item: `re-read, no meaningful change`, `updated (<n> claims changed)` (with `topics_flagged` when a claim an agreed version cites changed or went, stage 7), `unreadable, kept`, `summary failed, old summary kept` (decision) |
| `add --redo` (5) | `links?` or `topic?` (7), `force?` | per item: `redone` (with `title`, `abstract`, claim count, dropped and flagged claim counts and `page`: read again or which stored text was used, and, from stage 7, `topics_marked` or `topics`: `topics not matched` when the claims changed, and `topics_flagged`), `redo failed, old summary kept` (decision), `kept: needs scope`, `skipped: already on the current rubric and summary model`; `redone` count |
| `inbox` | `add: [links]` or `list` | count added; listed links |
| `find [--wide]` | `question`, `original`, `phrasings?`, `context?`; `--wide` (7): `brief`, `context?`, `phrasings?`, `rest?` | ranked sources (key link, title, author, date, last read); ranker; question as searched; `--wide`: see "Topics, catch-up and marks" |
| `ask` | one of `question` (+`original`, `phrasings?`, `context?`), `source` (link), `topic` (a name; 7), `whats_new: true` (7) | answer formats; labels, Model view, backing, writing model, ranker; `next`; `topic` and `whats_new`: the catch-up, see "Topics, catch-up and marks" |
| `topic` | `create` (`name`, `brief`), `draft` (`name`, `context?`), `save` (`name`, `draft`, `review`), `follow`, `unfollow`, `nothing_to_save` (each `name`), `list` | `create`, `follow` and `unfollow`: the topic as stored and the outcome; `draft`: the ranked sources, the ranker and the draft revision (`draft`: text, claims with labels, reasons, backing and the stored claims each cites, disagreements, gaps, Model view, writing model); `save`: the version saved (number, cross-check status, reviewers, run, changes, diff, reviewed text, claims copied); `nothing_to_save`: the date stored and the marks cleared; `list`: every topic with its followed state, agreed version and `reviewed_up_to` |
| `plan` | `save` (`topic`, `text`, `items: [{kind, text}]`, `review`), `mark` (`plan`, `item`, `state`), `show` (`topic?`) | `save`: the plan as stored; `mark`: the item as marked; `show`: `plans`, newest first, each with `cross_check`, `run`, the reviewed text and its open items |
| `note` (6) | `who`, `subject`, `lean` (`towards` or `against`), `reason` | the note as saved (who, subject, lean, reason, date) and `saved new` or `changed (earlier lean: <lean>)` |
| `archive` / `restore` | exactly one of `link`, `note` (`{who, subject}`) (6), `topic` (a name) (7), `citation` (8) | per target: `archived`, `restored`, `already archived <date>`, `not archived`, `not restored` or `not stored` |

`review` (from `atlas-ask` after Reconcile): `{"status": "complete" | "not_cross_checked", "reason", "run", "reviewers", "changes", "diff", "text"}`; the CLI stores the reviewed `text` and shows `changes` as given.

## Sources in (stage 3)

Identity:

- Link cleanup lives in `atlas/core/links.py` (carried from v1): explicit HTTP(S) only, no userinfo; scheme and host lowercased (IDNA), default ports, trailing slashes, fragments, `utm_*` parameters and numeric X `s` parameters dropped; the X host aliases `twitter.com`, `www.twitter.com` and `www.x.com` fold to `x.com`. Stage 3 adds the tracking parameters `fbclid`, `gclid`, `igshid`, `mc_cid`, `mc_eid` and splits site rules into `core/sites.py` (one tested row per site: X, GitHub, YouTube; the same rows mark unchangeable sources). No `www.` or http→https folding.
- `add` matches every given link against `links`, then (stage 4) an item with no scope against `expansions`, before any read; a match is never read again.
- Content hash: SHA-256 of `Page.text` after NFC, line endings and whitespace runs normalized; for an image source it also covers each image's SHA-256 in page order.
- Near copy: word 5-gram shingles of the normalized text; candidates are stored sources whose 64-value MinHash estimate is ≥ 0.7; share = the smaller of the two exact containments. Share ≥ `near_copy` joins without a summary, and Next offers "store it separately instead".
- Copy flags: after a stored add, the 5 closest sources by BM25 on title plus abstract get one Jev noul each ("the same work?"); P ≥ 0.5 flags.

Pick scope (decisions resent as `{"items":[{"link", "scope"}]}`): a repo with 2+ items, `video`, `image` or mostly images, `link_list`, and a page over `max_page_tokens`. An "each link" or "each item" choice with 2+ links is paid at scale, so it gets a confirm. A page source keeps its choice in `scope_choice`, so a re-add of its key link does not ask again. Images are transcribed by `atlas_summarize` into `[image <n>, transcribed by <model>]` blocks appended to the page text.

Expanding choices (stage 4): an `each_item`, `each_link` or `both` choice writes one `expansions` row for the page link the user named in the transaction of the first child that leaves a source holding its link (stored, joined or already stored), and each such child gets one `related_links` row with that link and origin `expansion` (replacing a `page` row for the same link); a `both` page source is stored as usual and is not an item source. After `each_item` or `each_link`, a re-add of that link with no scope matches before any read (no read, question, `approvals` row or paid call) and reports `already added as <n> items` with their key links, n counting the unarchived sources with an `expansion` row for the link; `next` offers "read <link> again for items not yet added" (resend with the stored choice) and "summarize the page itself too" (resend with scope `page`). After `both`, or once `page` stores the page itself, the page's key link is in `links`, so a plain re-add reports `already stored, last read <date>`. A re-add with an explicit scope is read as that scope says; child links already stored match before their read, so no paid call repeats.

Summary pipeline:

- One `atlas_summarize` call with tool `record` (abstract; claims with section, text, basis and 1–3 word-for-word quotes; metadata; related links; X author replies), prompt `prompts/summarize.md` (rubric `r1`) as the cached system block, plus kind cues from `kind_hint` and the site table. `max_output` 64K tokens. A reply with no tool call gets one turn repeating "Answer only by calling `record`"; still none is a hard failure.
- Code checks: every quote is found in the normalized page text; claim, quote, abstract and claim-count bounds; no duplicate claims; basis in the enum; metadata and related links found on the page; X replies by the post's handle.
- Then the `atlas-rethink` turn (setting `rethink`), the checks again, Jev support, one repair turn listing exactly the remaining failures, Jev rechecks of changed claims, dropping of claims with a quote still missing, store. A hard failure escalates once through the same steps on `atlas_escalate`; still failing stores nothing and returns a `summary_failed` decision.
- Failed-summary log (stage 4): a summary that fails after its escalation (`add`, `add --reread` and `add --redo`) writes one JSON file `<state>/atlas/<profile>/failed-summaries/<UTC time>-<first 8 hex of SHA-256 of the key link>.json` through `atlas/core/failure_log.py`, `<state>` being `$XDG_STATE_HOME`, else `~/.local/state`. It holds the time, profile, command, key link, rubric version and failure reason, and per model turn the role, model, thinking, stop, usage, `content`, `tool_input` and `tool_raw` as received, with that turn's code-check failures; never request messages, settings, keys or headers. The newest 20 files per profile stay; folder mode 700, file mode 600. The failed item carries `replies_log: <path>`; a failed write adds the problem `replies not logged: <reason>` and changes nothing else. The store still gets no source, claim or summary (the failed calls keep their `calls` rows).
- Records keep model, thinking level, escalation, rubric version, rethink line, dropped count, and flags with P and Jev model.

Re-read (`add --reread`): if every cited quote is still found and the new text adds less than `reread_new_text` of new shingles, store the new hash and read date ("re-read, no meaningful change"). Otherwise diff by line, update only affected claims in one `atlas_summarize` call, and check changed claims only; unchanged claims keep their ids. Replies show `last_read`, and `next` offers one combined re-read of sources last read over `reread_days` ago, skipping unchangeable ones.

Redo (`add --redo`, stage 5, `atlas/core/redo.py`): body exactly one of `links?` (named links) and `topic?` (a topic name), `force?` (needs `links` or `topic`). The default scope is every unarchived record that is older: its rubric version differs from the current one, or it was written without escalation by a model other than the model of the `atlas_summarize` role (without its thinking suffix); an escalated record counts only on a rubric change. Named links skip records already on the current setup and say so unless `force`; named links that are all current return an `already_current` decision offering "redo anyway" (a resend with `force`); with nothing older and no scope named the reply is done with nothing to redo and no decision. A `topic` scope (stage 7) is the sources cited by the topic's saved versions (through `version_claims`) and is handled as named links are: an archived one is reported as `archived <date>`, one already on the current setup is skipped and said so unless `force`, and when every cited source is current the `already_current` decision offers "redo anyway" (a resend with `force`), which redoes them all; a topic that cites no unarchived source is done with nothing to redo, and a topic that is not stored is exit 1 "not stored; create it first". It always asks one confirm (`add_redo`, paid at scale) stating the count, "about $X at list price" from the stored page tokens, and the window use. Each page in scope is read again with its stored scope and the new text replaces the stored text, hash and read date; an unreadable or gone page and an unchangeable source use the stored text, and the item says so. A page that now needs a scope choice the record does not hold keeps its old summary (`kept: needs scope`). The summary is rebuilt from scratch through the full pipeline, and the old summary is dropped (its claims marked replaced) only after the new one passes, in one transaction with one `summary_history` line `redone` carrying the replaced summary's rubric version, model and escalation. A failed redo changes nothing except one `redo_failed` history line, keeps the old summary (`redo failed, old summary kept`), writes the failed-summary log and returns a `summary_failed` decision; one bad source never blocks the batch, and the cap and window guard run before each item.

## Search and answers (stage 4)

- Search: BM25 over `source_fts` for each phrasing (the agent's `phrasings`, else 3 `atlas_query` rewrites of `question`; a failed rewrite searches `question` and says so), merged by reciprocal rank fusion (k = 60), top 30 to the ranker over title plus the first 700 characters of abstract and claims. `ask` answers from the top 10.
- Answer: `atlas_answer` through tool `answer`: claims shown with source link, label and reason, disagreements, gaps, Model view and tally lines. Labels are checked fail-closed in code; backing counts are computed in code. From stage 6 the unarchived notes whose `who` equals, case-insensitively, the author, an author alias or the publisher of one of the top 10 sources go into the message with keys `N1`, `N2`, …, each claim may list the keys of the notes the model applied, and a claim shown with a note carries `notes` (who, subject, lean, reason, date) beside its label (see "Notes and archive").
- One query record per `ask` and `find`; `result.question_as_searched` appears when `question` differs from `original`.

## Notes and archive (stage 6)

`atlas/core/notes.py` holds `note`, `archive` and `restore`; `atlas/core/answer.py` holds notes in answers and note proposals. Notes act at answer time only: search and rerank never read them, and a note never changes a label.

- Store: migration `0002_notes.sql` creates `notes` (id, who, subject, lean `towards`/`against`, reason, at, archived_at) and an index on who and subject; `0001_baseline.sql` is unchanged. One unarchived note is held per who-and-subject pair, both trimmed and compared case-insensitively. No store method deletes a row.
- `note`: `who`, `subject`, `lean`, `reason` are required non-empty text after trimming and `lean` is `towards` or `against`; anything else is exit 2 naming the field. A pair with no unarchived note gets a new row; a held pair has that row's lean, reason and `at` updated in place. The change is kind `note` with the note's `who` as its one name target, so a `request` approval whose words hold the who runs it and other words return one `confirm` decision; each applied change writes one `approvals` row. It makes no model call.
- `archive` and `restore`: exactly one of `link`, `note`, `topic`, `citation`. A `link` is cleaned (`core/links.py`) and resolved through `links` to its source, whichever of the source's links it names; a `note` is `{who, subject}` matched as above; a `topic` is its name, trimmed and compared case-insensitively. `citation` replies exit 1 "… is not available in this Atlas build yet" until stage 8. The change is kind `archive` or `restore`, its target the cleaned link (a link target), the note's `who` or the topic's name (name targets). `archive` sets `archived_at` and `restore` clears it; no row is deleted, and a source's claims, links and page text stay, an archived topic keeps its versions, plans and marks, is not followed by the catch-up and is not matched (stage 7). A target that is not stored is a problem "not stored; add it first" (a note: "not stored; save it with `note` first"; a topic: "not stored; create it first"); an already archived or not archived target changes nothing and asks nothing. Restoring a note while another unarchived note holds its pair is a problem naming the pair and changes nothing.
- What archive hides: an archived source is left out of `find` and `ask` candidates and `add`, `add --reread` and `add --redo` report it as `archived <date>`; an archived note is never given to the answering model and never shown.
- Notes in answers: for `ask` with a `question`, `answer.py` passes the notes that may apply (author, author alias — a JSON list of names in `sources.author_aliases` — or publisher of a top-10 source equals the note's `who`) to the `atlas_answer` message as `N1`, `N2`, …. The model judges whether the question falls under a note's subject, applies only those that do by listing their keys on a claim's optional `notes`, and says so in `disagreements` when sources disagree; code shows each applied note beside its claim's label. A key that names no given note is a problem and is left out; when the label check fails and the claims are shown unlabelled, each applied note is still shown with its claim.
- Note proposals: after `ask` stores its tally lines, each who-and-subject pair with 3 or more lines whose `proposed_at` is empty gets one proposal in `result.note_proposals` (`who`, `subject`, `lean` (the majority direction; `null` on a tie, which the reason says), `reason` (the counts towards and against), `links`). `next` gains one item for all of them, with `then` `{"stop": true}`: "save a note …", "change the note …" when an unarchived note holds the pair, or, for two or more, the count and a pointer to `note_proposals`. The lines' `proposed_at` is set in the same transaction, so the pair's count starts again whether the user takes the proposal or not. The front door takes a proposal by calling `note` with no `approval`, so the CLI's one `confirm` decision is the one confirm; a proposal is never sent with `by: "request"`.

## Spend, cap and window guard (stage 3)

- One `calls` row per paid call: Jev cost is billed; omp roles get an estimate from the price table, or `unknown` without a row.
- Cap: the sum of billed `cost_usd` in the profile's current calendar month (local time). From `cap_warn` × cap, and past the cap, every paid command returns a `cap` decision before its first paid call; a batch returns it before its next item with done and not-started counts. Options: continue anyway (this command only), raise the cap in `config.toml`, stop here.
- Window guard (batches only): before each item, any window at or past `window_stop` for the batch's providers returns a `window` decision with done and not-started counts and the reset time.
- A batch confirm shows an estimate "about $X at list price" and each window's current percent; Atlas does not predict window percent.
- Rerun after a stop needs no queue: stored links report as already stored, and a scoped redo skips records already on the current setup unless `force`.

## Topics, catch-up and marks (stage 7)

- `atlas/core/topics.py` holds `topic` and `atlas/core/plans.py` holds `plan`. A topic name is unique, trimmed and compared case-insensitively over archived topics too; a topic that is not stored is exit 1 "not stored; create it first" for every action that needs it. `topic create` (`name`, `brief`) stores a new followed topic and `plan save` stores a reviewed plan; both are kind `plan_start` with the topic name as the one name target and the same question, so the plan's one confirm covers both: the front door sends both bodies with no approval, asks once, then resends `topic create` and after it `plan save`, each with the user's reply as the `confirm` approval of its own decision. `plan save` returns its decision before it checks that the topic is stored, and when the confirmed call applies a missing topic is the problem "not stored; create it first". `follow` and `unfollow` are their own change kinds and an already-in-state topic changes nothing and asks nothing. `topic list` and `plan show` are reads.
- `topic draft` (`name`, `context?`) stores nothing and asks no approval: it searches the topic's brief as `ask` searches a question (same stops, fallbacks and query record) and writes a draft revision through `atlas_answer` and tool `answer` (`answer.py`, prompt `draft.md`) with labels and a Model view as `ask` does, given the topic's agreed version when there is one. The writer is given each claim's key (`S<n>.<position>`), and each claim of the draft lists the stored claims it relies on as `cites: [{link, claim}]` (the source's key link and the claim's position); a key the writer was not given is a problem and left out. No tally line is stored.
- `topic save` (`name`, `draft`, `review`): `draft` is the `draft` object `topic draft` replied with (what the save reads of it: `writer_model`, `thinking` and each claim's `cites`); every cite must name a stored source's current claim, else exit 2. A call with no approval, or with a `request` one, returns a `version_save` decision whatever `confirm.*` says; a `confirm` approval of that decision with a `review` stores version N+1 in one transaction: the review's reviewed `text`, the draft's writer model and thinking, `cross_check`, reviewers, run, changes and diff, one `version_claims` row per distinct claim the draft cites holding that claim's text and quote texts as they are then, the clearing of the topic's marks (`cleared_at`), and one `approvals` row. A `confirm` resend with no `review` is exit 2. The decision id leaves out `review`.
- `review`: `{status, reason, run, reviewers, changes, diff, text}`, `text` the reviewed text. `status: "complete"` needs `run` (text), `reviewers` (a non-empty list of text) and `changes` (text; `diff` optional text) and stores `cross_check` `complete`; `status: "not_cross_checked"` needs `reason` and stores `not cross-checked: <reason>` with whichever of the other fields are given. Both `plan save` and `topic save` store the reviewed text, never the draft or plan text sent beside it, and show `changes` as given.
- `topic nothing_to_save` (`name`) stores `reviewed_up_to` (the time of the call, shown as a date) and sets `cleared_at` on the topic's open marks; it creates no version, asks for no approval and runs no Reconcile. `plan mark` (`plan`, `item`, `state` `done` or `skipped`) sets one item's state and time; a plan is named by the `plan` number `plan show` and `plan save` give, an item by its `item` number there.
- A plan's `items` are `{kind, text}` with `kind` one of `question`, `search`, `source`, `page`; each starts `open`. `plan show` lists plans newest first, with the plan number, topic name, date, `cross_check`, `run`, reviewers, changes, reviewed text, its `open_items` and the `done` and `skipped` counts.
- Reconcile runs in the `atlas-ask` front door only, never in the CLI, the ports or the core, and `atlas-ask` is its only trusted caller (`caller` `atlas-ask`). It reaches the dotagents skill `reconcile` through that skill's trusted-caller entry, and Atlas skill text writes `skill://reconcile` only inside code, which `check_skills` skips.
  - Readiness: `atlas-ask` runs `node "$(realpath skill://reconcile)/acp-controller/cli.mjs" ready atlas-ask` through bash beside `status`. It launches nothing and prints one JSON line: `{"ready":true}` (exit 0) or `{"ready":false,"reason":"…"}` (exit 2). A `reconcile` skill that does not resolve is not ready, with its own reason.
  - Request: when ready, `atlas-ask` writes one request to a fresh folder under `/tmp` (not named `acp-controller-…`): `caller` `atlas-ask`, `level` `direct`, `mode` `conversation`, `cap` `none`, `candidate.text` in two parts (a `**Summary**` of 1 to 7 points of at most 100 characters, then `**Details**`: the plan or the draft revision in full, with its labels and Model view), `intent` holding the user's own words exactly (the research request, or the yes to the `version_save` question) and this skill's `SKILL.md` by absolute path, `context` the sources and evidence, `approval` those same words with the time they were sent, and an absolute `record` and `output` in that folder. It runs `reconcile` on that file through bash with no time limit; a call that ends without a record is run again unchanged and attaches to the same run. The output counts only when its `status` matches the exit code (`0` `complete`, `1` `stopped` or `parked`, `2` `refused`, `3` `failed`).
  - Review: on `complete`, `atlas-ask` passes `review` `{status: "complete", text, run, reviewers, changes, diff}` from the output (`text` the reviewed text, `run` the run id, each reviewer as its role and model, `changes` the points as lines, `diff` when given) and shows the user the output's `summary` and `changes` as given. Atlas stores the run id, not the record: `atlas-ask` keeps the request folder, whose `reconcile-record.md` is the run's record, and tells the user its path.
  - Plan flow ("Create a topic on X"): `find --wide` with the brief; the agent writes the plan from it; Reconcile reviews the plan, with the user's request as its approval; `atlas-ask` shows the reviewed plan with Reconcile's changes; it sends `topic create` and then `plan save` (with the `review`) with no approval, shows the one `plan_start` question their two decisions carry, and after the user's yes resends each with its own decision's `confirm` approval, `topic create` first. Reconcile runs before the question, so the user answers once with the review, or the reason there is none, in view.
  - Save flow ("Save this as version N"): `topic save` with no approval and no review returns its `version_save` decision and the user answers it; only then does Reconcile review the draft revision, with the user's yes as its approval; `atlas-ask` resends `topic save` with the same body, the `review` and that decision's `confirm` approval. `topic nothing_to_save` runs no Reconcile.
  - Not cross-checked: when Reconcile is not ready, is refused, stops, parks, fails or leaves no output that counts, the reason is the readiness `reason`, the output's `reason`, or "Reconcile wrote no output (exit N)". `atlas-ask` then shows the reason and offers two Next lines of its own: "set up Reconcile first" (nothing more is sent and nothing is saved) and "go on without it", after which the flow goes on with `review` `{status: "not_cross_checked", reason, text}`, `text` the plan or draft revision as written, and the plan or version is stored with `not cross-checked: <reason>` (ADR 0008). A parked run is left for the human to repair or dispose; `atlas-ask` never goes on without Reconcile unless the user picks it.
- Wide gather (`find --wide`, a mode of `search.run`): body `brief` (the question and its own `original`), `context?`, `phrasings?`, `rest?`, `profile`, `approval` (the cap's), through the same gate (`judge_setup`, missing roles, cap) as `find`. With Jev set up, one noul per unarchived source ("Is this source about the same area as the brief?", over its title and the first 700 characters of its abstract and claims, concurrent) is asked, and every source at P ≥ 0.3 is added to the BM25 candidates (the phrasings, else 3 rewrites; reciprocal rank fusion, top 30). The shown set is those two together ordered by P; each source carries `p` and `found_by` (`jev`, `bm25` or `both`). Nothing is dropped: the rest of the library, ordered by P, is one Next away, a resend with `rest: true` whose reply holds only those sources (and judges again). The reply is `sources`, `ranker`, `page` (`first`, or `rest` for the resend) and `counts` (`shown`, `jev_set`, `bm25`, `rest`). When Jev fails after its backoff, or the profile chose Opus, the Opus path runs and the reply says so: BM25 top 100 for each phrasing, fused, ranked by `atlas_rerank` (the sources it leaves out follow in fusion order); `counts` holds `shown` and `rest` only, nothing is left to a resend, and a `rest` call replies with no sources. When Jev is not set up and no choice is saved the reply is the `judge_setup` decision before any search. One query record per call (op `find`: the `queries` table allows only `find` and `ask`), the brief as its question and original, with the Jev records of every source when Jev ranked.
- Marks: after `add` stores a source, and after a redo whose claims changed (the replaced and the new claims differ in text or quotes), one Jev noul per followed, unarchived topic ("Could this source change or add to a conclusion of this topic?") over the source's title, abstract and claims against the topic's brief and its agreed version's reviewed text (the brief alone when the topic has no agreed version); P ≥ 0.3 adds a mark with the P and the Jev model version (a source already marked open for the topic keeps one mark, which takes the new P). The source's `topics_status` becomes `checked`; with the profile on Opus, or Jev not set up, no judge call is made, no mark is made and `topics_status` stays empty; when Jev fails after its backoff the source gets `topics_status` `topics not matched` and the reply says so, and the next catch-up searches as it always does. With no followed topic there is no judge call at all. A re-read makes no marks. Marks clear when a version is saved or `nothing_to_save` is chosen.
- Flags: the flag is derived, never stored. After a redo or a re-read that changed a source's claims, each unarchived topic whose agreed version (its latest saved one) holds a `version_claims` copy of one of that source's claims is compared with the source's claims now, by quote: a copy with no current claim sharing one of its quotes is removed, one whose sharing claim differs in text or quote set is changed, and either flags the topic. The reply shows the flagged topic names as `topics_flagged` on the item.
- Catch-up (`ask` with `whats_new: true`, or `topic` for one stored, unarchived topic; `atlas/core/catchup.py`): every followed, unarchived topic is searched for the sources added after (`sources.first_seen`) its agreed version's `saved_at` or `reviewed_up_to`, whichever is later (a topic with neither has no lower bound); the search is BM25 over the brief (no rewrite call) and the ranker is Jev, else `atlas_rerank` for that topic, else the profile's Opus, and a not-set-up judge is the `judge_setup` decision before any search; one query record per topic search (op `ask`), with the Jev records when Jev ranked. The topic's set is the found sources plus its open marks, so marks add sources and order topics (marked first) and never remove one. An `atlas_answer` call (tool `answer` with `changes_conclusion`, prompt `catchup.md`, labels and the notes of `ask`) runs for a topic with a non-empty set, over its marked sources first and then the found ones, at most 10 (all marked ones when more); a topic whose set equals the set its last catch-up answered with no conclusion change skips the call and counts as no change. A catch-up with 2 or more answer calls is a batch for the window guard, checked before each call, and the cap is checked as for every paid command, so a limit stops it with a `cap` or `window` decision that states the done and not-started counts. One failed answer call leaves that topic unanswered (a problem, `unanswered` in the reply) and does not stop the others. Each answered topic stores in `topics.last_catchup` one JSON value `{"changed": <bool>, "sources": [ids of its set], "named": [ids of sources its answer's claims name], "at": <time>}`: a verdict and source sets, never the answer text. The reply: `changed` (the conclusion-changing topics, marked first, each with its answer, claims with labels, backing and the sources new and marked, its agreed `version` and `next_version`), `no_change` (`count` and `topics`: the "evidence changes no conclusion" line), `quiet` (`count` and `topics`), `unanswered`, `summary` (the three lines in words) and, on a stop, `not_started`; then `next`: "save as version N+1" per changed topic (a `topic draft`, then `topic save`, which stops as always) and "nothing to save" per changed topic (`topic nothing_to_save`), each one item naming its topics. Citation names in the reply wait for stage 8.

## Status

Default reply: action items first, then one line, then Next.

```json
{"needs_action": [{"what": "Role atlas_escalate is missing", "fix": ["modelRoles:", "  atlas_escalate: anthropic/claude-opus-5-5:medium"], "where": "/home/kim/.omp/agent/config.yml"}],
 "summary": "Profile main: 412 sources, inbox 3, judge Jev, Atlas v2.1.4",
 "detail": null}
```

- Action items, in order: no config or profile (run `atlas-init`); store newer than code; missing roles; the judge's setup problem; judge choice not saved; price row missing; cap at or past `cap_warn`; a window at or past `window_stop`; host version differs from the current tag's (warning, never blocks).
- Next adds the redo offer "<N> summaries on an older rubric or summary model" when the count of older records (as Redo defines them) is non-zero; its `then` is `{"stop": true}`, since no typed action names another command, and `atlas-ask` runs the redo when the user asks.
- `status --detail` adds profile, store path and size, roles and models, judge, counts, Atlas and host versions, this month's spend, windows, the redo count (`redo`), confirm settings and limits.
- Reconcile readiness is a front-door fact: `atlas-ask` checks it beside `status` (see "Topics, catch-up and marks") and adds one line, ready or not ready with its reason. It is not a `status` action item and does not change the `status` exit code.

## Repo citations and the research rule (stage 8)

`rules/atlas-research.md` applies where `ATLAS_PROFILE` is set: `dev-research` first runs `find` or `ask`, and at its end proposes adding every source the research relied on with `cited_in: {"repo", "file"}` as one confirm (never `request`). A later `add` with the same repo and file replaces that file's citations. Replies that change a claim, a topic's what's-new and the catch-up name the citing repos and files.

## Quality check (stage 5)

`tools/quality/quality.py` compares two versions of Atlas (a git ref plus setting overrides) on the `eval` profile across the summary, search and answers lanes, with user spot checks and paired bootstrap intervals. Commands: `build-library [--yes]`, `promote`, `promote-page`, `run <lane> --base <ref> … --cand <ref> …`, `spot`, `report` and `marks-report --profile <name>`. Without `--yes`, `build-library` and `run` print the estimated cost, make no read, model or judge call and write nothing.

- Versions: each ref runs from a `git worktree` under `~/.cache/atlas-quality/`, one case per process through `atlas.core.app.run`, with the overrides (a profile setting, `role.<role>=<model>` or `phrasings=own`) applied to an in-memory copy of the `eval` profile; scratch stores and worktrees are removed when a run ends.
- Reads: a version never reads a page. `tools/quality/replay_read.py` is a read port that answers from page records it is built with and never touches the network: a link a record holds, or one joined to it, returns the record's key link as `final_link`, its kind, items and kept text for the asked scope, an image link returns the recorded bytes and any other link is `Unreadable`. The store keeps cleaned page text and image hashes only, so records built from the `eval` store have no repo items and no image bytes; the contract suite binds the adapter in `tests/contract/test_replay_read.py` against records recorded under `tests/fixtures/quality/`.
- Rows: the tool-owned tables `cases`, `key_points`, `runs`, `measures`, `judgments`, `spot` and `comparisons` (spec 4.15's columns) are created in the `eval` store file when missing. They are not a numbered migration: migrations ship in the plugin and apply to every profile's store, and the tool is repo-only.
- Library: `build-library` adds the 516 pool ids of ticket 08's graded pool (515 distinct links) through `atlas.core.app.run("add", …)` with the real host, acting as the front door (`--yes` is the user's confirm for each batch; a `pick_scope` decision is answered with the page, transcript, images or first part, never an expanding scope; a cap, a window or any other decision stops the run with that decision's text and a non-zero exit, and a rerun continues from the stored links). A link that does not read or whose summary fails is dropped, counted and listed. Its last line is `library: <a> added, <u> unreadable, 47 queries, 1535 grades`, counting each pool id once (`a` the ids whose link the library holds, `u` the ids dropped). Queries and grades enter as `cases` with origin `ticket08`.
- Measures: Jev grades through the tool's own judge, so both versions are judged alike; code counts the rest. Only measures with a user sample can be marked unreliable (summary-lane faithfulness flags, search-lane Jev grades; more than 2 in 10 disagreements); completeness, conciseness, the planted-instruction Jev check and the answers lane's support flags are always reported "not spot-checked". Samples and bootstraps (10,000 paired resamples, 95% percentile interval) are seeded by the comparison id.

It reads a real profile only in `promote` and `promote-page` (one query record and its sources' page text, or one changed page's record) and in `marks-report` (below), and writes only `eval` (and the cache folder for worktrees and scratch stores).

- Search lane, stage 7: recall of the user's named source sets (a case with `gold_user`) is measured on the top-10 `find` as `recall` and also on `find --wide` as `recall_wide`, the share of the set found anywhere in the wide call's shown sources (its `rest` is not read). The worker runs the wide call only for a case with a named set, with the same fixed phrasings (or `phrasings=own`), its calls and cost counted in the run, and a cap, window or `judge_setup` stop in it stops the run like a stop in `find`.
- `marks-report --profile <name>` opens the named profile's store file read-only (an SQLite read-only URI), never through the migrating core open, and writes nothing. It prints a header and one row per mark, ordered by topic then time: P, topic, source link, and whether the topic's last catch-up answer named the source (`named in the catch-up answer`, `not named in the catch-up answer`, or `not yet answered` when the topic has no catch-up yet or the mark was made after it), then exits 0; a store with no marks prints no rows and exits 0; a profile that is not set up exits 3; a store file that does not exist, or that has no `marks` table (not yet migrated), exits 1 saying so. The user keeps or changes the 0.3 threshold from these rows.

### Deferred: the `eval` library build (spec AC-5.5)

The `eval` profile exists (`~/.local/share/atlas/eval.db`) and its library is not built: it holds no source, and the build has never run against a real read, model or judge call. The user deferred it on 2026-11-10 and on 2026-11-11 moved it to after every other stage (6 to 8) is complete, or as late as possible. Until then the quality tool's `run` lanes have no library to compare on; later stages go on without it, and do not propose the build in their plans. Run it only when the user asks for it, as its own request through `dev-ask`, with a separate ask before the paid run (`.agents/AGENTS.md`).

- What it does: re-reads and summarizes the 516 graded-pool source ids of ticket 08 (515 distinct links, found through the frozen v1 vault's `canonical_url`) into `eval`, and imports the 47 queries and 1,535 grades as `cases`. Nothing goes to `main` or any other profile.
- Commands: `python3 tools/quality/quality.py build-library` prints the count of links not stored yet and the estimate and makes no call; `python3 tools/quality/quality.py build-library --yes` builds. Stored links make no paid call, so a rerun continues where a stop or a kill left off (one kill loses at most the item in flight). A cap or window decision stops the run with a non-zero exit; wait for the window to reset, or ask the user about the cap, then rerun.
- Observed on 2026-11-10: the estimate printed `about $72.10 at list price (about $0.14 at list price per link)` for 515 links (the core's default token counts; the spec's $10 to 15 does not match it), plus Jev calls billed on the OpenRouter key. The wall time is an estimate, not measured: 2 to 5 minutes per link, serial, is about 17 to 43 hours over several window stops, so run it in slices (for example `timeout 3300 python3 tools/quality/quality.py build-library --yes`); a rerun reads the dropped links again. Of the 515 links, 288 are `github.com` (191 of them repo roots, whose file list needs GitHub's tree API) and 144 are `x.com`. Because the build has never run live, its first run may meet decisions or read failures the offline tests do not show. Its last line always counts each of the 516 ids once, so `a + u` is 516 whatever happens; judge the build by the dropped list on stderr (many repo roots dropped as `unreadable: error` probably mean no token was set) and take any high `u` to the user.
- GitHub token: Atlas sends the value of `GITHUB_TOKEN`, else `GH_TOKEN` (a blank value counts as unset), as `Authorization: Bearer` on its repo file-list request to `api.github.com`, and to no other origin, also after a redirect (`atlas/adapters/omp.py`, stage 4). GitHub documents 60 such requests an hour without a token and 5,000 with one (spec section 10, assumption revised by stage 3). It is not a `config.toml` key, `atlas-init` does not write it and Atlas stores it nowhere. It matters only for bulk repo reads such as this build, which makes about 191 such requests; without a token most of them will be refused. The user's steps: create a fine-grained personal access token with read-only access to public repositories, export it as `GITHUB_TOKEN` in the environment omp starts from (the build runs in the shell that runs `quality.py`, which an omp agent's shell inherits from omp), and start omp from that environment. Agents never create, read or store the token.

## Release and install

- `tools/release/release.py setup` sets `core.hooksPath` to `.githooks` (idempotent). `release.py shipped-paths <ref>` prints the shipped files at `<ref>`.
- `.githooks/pre-push`, for `origin` `refs/heads/main` only, starts `release.py publish --after-push <git push pid> --background <sha>` and exits 0 at once.
- The run waits for the push, works in its own clone under `~/.cache/atlas-release/` (lock, pass cache and log there, nice 19), so it makes no background write to the checkout. It proceeds only if `origin/main` is the pushed commit, runs the unittest suite and `check_skills.py skills` on that commit (found through `omp plugin list --json`), and tags only if both pass.
- Tags counted: `v2.<minor>.<patch>` only (`v1` ignored). Tag when the shipped paths changed since the last v2 tag, or always for the first (`v2.0.0`). Minor bump when that diff adds a migration; else patch.
- The annotated message holds `atlas v2.x.y`, the commit subjects since the last tag, and trailers `Omp-Version` and `Dotagents`; then a GitHub Release from it (a `gh` failure only logs).
- `status` version: in a checkout, `git describe --tags --match 'v2.*'`; else the `package.json` version, with no host version warning.
- Rollback: any earlier tag before stage 4; from stage 4, rolling back past a minor version leaves the store newer than the code (exit 1). Unlink: `omp plugin uninstall atlas`.

## Terms

- **source**: one web work Atlas has read and stored, with one checked summary; named by its key link.
- **key link**: the cleaned link that identifies a source. Other links that reach the same source (redirect targets, joined near copies) are stored beside it and resolve to it.
- **claim**: one self-contained sentence in a source's summary that states a finding, recommendation or caveat of the page, with its basis (`measured`, `demonstrated`, `cited` or `asserted`) and 1–3 quotes.
- **quote**: words copied word for word from the stored page text that back a claim. A quote must be found in the normalized page text; a claim whose quote is still missing after repair is dropped.
- **record**: the stored summary of one source: abstract, claims with quotes, metadata, related links, and how it was made (model, rubric version, flags). A query record and a call record are the stored traces of one search and one paid call.
- **topic**: a named subject with a brief that the user can follow; its agreed understanding is saved as versions.
- **version**: one numbered, saved understanding of a topic, with copies of the claims it cites and its cross-check status. It is saved only after a `version_save` decision.
- **mark**: the judge's flag that a newly added or redone source matters to a followed topic. Marks add sources to the topic's next catch-up and order it; they never remove anything.
- **catch-up**: `ask` with `whats_new: true` (or `topic`, for one topic): each followed topic is searched for sources added since its agreed version or `reviewed_up_to`, and answered when it has new or marked sources, except when its set equals the one its last catch-up found changed no conclusion.
- **profile**: a named entry in `config.toml` with its own store, judge choice, limits and confirm settings; chosen by body `profile`, else `ATLAS_PROFILE`, else `default_profile`.
- **port**: a host seam that core calls through a fixed shape in `atlas/ports.py` (read, call, judge, quota), with one contract suite that every adapter of it passes.
- **adapter**: code that implements a port or the store interface for one host or service, such as OMP, Jev, SQLite or the fake host. Only `atlas/host.py` picks adapters.
- **decision**: an entry in a reply's `decisions` list (exit 4) that stops a command for the user: a kind, a question, and options whose `then` the front door follows.
- **paid at scale**: a change that makes paid calls for several sources at once: `add --redo`, an `add` or `add --reread` that reads 2 or more links after stored links are matched, or an "each link"/"each item" scope with 2 or more links. Under `confirm = "always"` it needs a confirm even when the user asked for it in so many words.
