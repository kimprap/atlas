# Atlas v2 stage 1: cutover and plugin shell

- Datetime: 2026-11-09-1601
- Scope: Atlas v2 build stage 1 "Cutover and shell" (spec section 6), minus the records boundary and the push/tag/install effects
- Summary: v1 is removed in one cutover commit with its link cleanup and strict JSON handling carried into the v2 core, and the v2 omp plugin shell (package metadata, CLI shell, minimal `atlas-ask` and `atlas-init` skills, release tool, pre-push hook, setup task) is linked live on g10.
- Status: DONE
- Completed At: 2026-11-09-0954

## Outcome and authority

- Outcome: On g10, `~/dev/atlas` holds no v1 runtime, owners, scaffold, harness links, rules, command stub, tests or cassettes; carried link cleanup passes its v1 cases from `skills/atlas-ask/atlas/core/links.py`; the omp plugin `atlas` 2.0.0 is linked live, its CLI keeps strict JSON input and answers every one of the ten commands with exit 3 and a Next naming `atlas-init` while no `~/.config/atlas/config.toml` exists; `atlas-ask` reaches that CLI by the plugin path; the release tool, pre-push hook and setup task exist and are tested, ready for the `dev-shipping` stage's first push.
- Authority: Specification "Atlas v2 specification" `.agents/artifacts/atlas-v2-spec.md` revision r3, approved by the user on 2026-11-09, committed in `a976782` (blob `120a139f72a6e5568bb38d9c96bb0f1d6e1bc411`): sections 3 (architecture), 4.1 (CLI call and reply), 4.16 (release and install), 5 (effects), 6 (stage 1 row) and 7 (stage 1 acceptance and AC-X1). Route overview `~/.local/share/agent-workflow/route-20261109-atlas-v2-stage1/route-overview.md`, approved by the user's reply "approve" on 2026-11-09, which moves the spec's third stage 1 task (first push, tag, install smoke; AC-1.10, AC-1.11) to the route's `dev-shipping` stage and excludes the "1 records" boundary. Where this plan and the spec differ on anything other than those two route decisions, the spec governs and the difference is a stop.
- Assurance: standard

## Scope and effects

- Scope: T1 removes the v1 tracked tree and moves the two carried pieces into the v2 core: `scripts/atlas_url.py` becomes `skills/atlas-ask/atlas/core/links.py` (behavior unchanged; its 15 tests move to `tests/test_links.py`), and the strict JSON input of `scripts/atlas_cli.py` (duplicate keys, NaN/Infinity constants, non-object bodies, invalid UTF-8 are bad input) becomes `skills/atlas-ask/atlas/core/reply.py`, which also owns the v2 reply of spec section 4.1: exactly the six keys `ok`, `op`, `result`, `problems`, `next`, `decisions`, the `problems[]` and `next[]` item shapes, and exit codes 0–4, written as one line with `json.dumps` default separators so `"ok": false` appears as AC-1-3 reads it. v1's envelope keys (`version`, `disposition`, `findings`, `recovery`) and its exit 70 are not carried. T1 rewrites `.agents/AGENTS.md` (v2 package map, ownership, conventions and check commands for this repo) and `.agents/ARCHITECTURE.md` (v2 contract written from spec sections 3 and 4, without the Terms glossary, which belongs to the records boundary), `pyproject.toml` (name `atlas`, version `2.0.0`, basedpyright over `skills/atlas-ask/atlas`, no `[tool.uv]`) and `README.md` (what Atlas v2 is, link/install, setup through `atlas-init`, tests command), and adds `tests/__init__.py` so `python3 -m unittest discover -s tests -t .` runs; the tests reach the `atlas` package by putting `skills/atlas-ask` on `sys.path` once there. T2 adds `package.json` (`{"name":"atlas","version":"2.0.0","omp":{}}` plus description/license fields as needed), `skills/atlas-ask/cli.py` (entry `python3 cli.py <command> [<action>] [--redo|--reread|--wide|--detail]` with one JSON object on stdin, decoded strictly before anything else so a bad body is exit 2 even when Atlas is not set up; profile resolution is stage 2), `skills/atlas-ask/atlas/core/app.py` (`run(command, mode, body, host)`; stage 1 returns the not-set-up reply for each of the ten commands `status`, `add`, `inbox`, `find`, `ask`, `topic`, `plan`, `note`, `archive`, `restore` when `~/.config/atlas/config.toml` is absent, read through `HOME`; that reply is exit 3 with `result.needs_action` holding one item whose `what` says Atlas is not set up and whose `fix` says to run `atlas-init`, and `next` holding one item labelled "run `atlas-init`" whose `then` is `{"skill":"atlas-init"}`), the minimal `skills/atlas-ask/SKILL.md` (front door that runs `python3 "$(realpath skill://atlas-ask)/cli.py" <command>` with the body on stdin (`{}` when the command takes no fields, since the CLI reads one JSON object from stdin), shows `result`, `problems`, `decisions` and `next`, and turns a `{"skill":"atlas-init"}` Next into "run `atlas-init`") and `skills/atlas-init/SKILL.md` (stage 1 stub that states setup arrives in stage 2 and writes nothing), `tools/release/release.py` (`setup`, `shipped-paths <ref>`, `publish --after-push <pid> --background <sha>` with spec 4.16's wait, own clone, lock, pass cache `check-cache`, log, nice, origin check, tests and `check_skills.py skills` gates, tag rule, annotated message with `Omp-Version` (the bare version that `omp --version` reports, such as `18.18.2`, which is the form spec 4.13's comparison reads) and `Dotagents` trailers, `gh release create`, optional `notify`; `check_skills.py` is found from the `npm` entry named `dotagents` in `omp plugin list --json`, whose `path` is `/home/kim/.omp/plugins/node_modules/dotagents` on g10), `.githooks/pre-push` (dotagents' hook form: `~/.dotfiles/.githooks/pre-push` is the model), and the tests `tests/test_cli.py` and `tests/test_release.py`; it links the plugin and runs the stage 1 smoke. Boundary rationale: only `tests/test_atlas_url.py` (218 lines, 15 tests) pins behavior v2 keeps; the other 10 v1 test files are deleted, the rest is greenfield, so each task's spread is its own new tests. T1 and T2 are split at the cutover commit, which spec section 5 makes one commit holding the v1 deletion, the carried code and the four rewritten files; T2 keeps the CLI shell and the release tool together as the spec's one task because both are small, share the `tests/` bootstrap T1 adds, and the release run's gates call the suite T2 completes. The seam considered was CLI shell versus release tool as separate tasks; it was rejected because the route approved two tasks and neither half is large enough to need its own context. Acceptance IDs are the spec's with dots written as hyphens (the plan grammar admits no dot): AC-1-1 is spec AC-1.1, and so on.
- Effects: Repository changes on the targets of T1 and T2 only. T1 removes tracked files with `git rm` so the index matches, because AC-1-1 reads the index; children may stage but never commit. Deleting the untracked, ignored `tests/cassettes/` folder (v1 test cassettes) is allowed in T1. Main, not a child, makes two local commits under the route overview's Safety: the cutover commit after T1's Handoff is accepted, before T2 is dispatched, whose message records the archived v1 plans `2026-07-29-2056_atlas-evaluation-loop` and `2026-08-02-1332_atlas-topic-creation` as superseded; and the shell commit after T2's Handoff is accepted; review repairs become further local commits. T2 may run `omp plugin link /home/kim/dev/atlas` (user scope; undo `omp plugin uninstall atlas`), `python3 tools/release/release.py setup` (sets this repository's local `core.hooksPath`, after which a push of `main` to `origin` from this checkout starts a release run; only the route's `dev-shipping` stage pushes), and the AC-1-3 check and the AC-1-12 smoke, each as one live omp agent session in `/home/kim/dev/atlas` (subscription model use, expected 1–3 minutes each, an estimate). Tests run only in temporary directories with their own `HOME`, git repositories and bare origins, and stub `gh`/`omp`/`notify` on `PATH`; they never touch `~/.cache/atlas-release`, `origin`, GitHub or the real `HOME`. No push, tag, GitHub Release, plugin install, `~/.config/atlas/` write, `~/.local/share/atlas/` store, host config write or paid API call.
- Non-goals: The records boundary (ADRs 0008–0010, `docs/adr/INDEX.md` superseded marks, the Terms glossary); stage 2 and later work (ports, adapters, `host.py`, config and profile reading, store, real `status` content, `atlas-init` setup); AC-X2, whose import check needs the stage 2 adapters and composition module to have anything to block; the first push, `v1` tag push, `v2.0.0` tag, GitHub Release and throwaway-home install (AC-1.10, AC-1.11), which the route's `dev-shipping` stage performs and reads back; editing `.agents/plans/archive/`, `.scratch/`, `docs/adr/` or the spec.

## Tasks

- [x] T1. Cut over: remove v1, carry link cleanup and strict JSON into the v2 core, and rewrite the repo contracts
  completed 2026-11-09-0918
  - Owner: implementation child T1
  - Depends on: none
  - Targets: scripts/, .agents/skills/, .agents/rules/, .agents/commands/, scaffold/, .cursor/, .grok/, tests/test_atlas_*.py, tests/cassettes/, uv.lock, .gitignore, .agents/AGENTS.md, .agents/ARCHITECTURE.md, pyproject.toml, README.md, skills/atlas-ask/atlas/__init__.py, skills/atlas-ask/atlas/core/__init__.py, skills/atlas-ask/atlas/core/links.py, skills/atlas-ask/atlas/core/reply.py, tests/__init__.py, tests/test_links.py
  - Acceptance: AC-1-1, AC-1-2, AC-1-9
  - Receiver: dev-implementation controller (Main)
- [x] T2. Build the plugin shell: package metadata, CLI shell, minimal skills, release tool, hook and setup task, link and smoke
  completed 2026-11-09-0929
  - Owner: implementation child T2
  - Depends on: T1
  - Targets: package.json, skills/atlas-ask/cli.py, skills/atlas-ask/atlas/core/app.py, skills/atlas-ask/SKILL.md, skills/atlas-init/SKILL.md, tools/release/release.py, .githooks/pre-push, tests/test_cli.py, tests/test_release.py, plugin link ~/.omp/plugins/node_modules/atlas, git config core.hooksPath
  - Acceptance: AC-1-3, AC-1-4, AC-1-5, AC-1-6, AC-1-7, AC-1-8, AC-1-12, AC-X1
  - Receiver: dev-implementation controller (Main)

## Acceptance

- [x] AC-1-1. v1 tree removed (spec AC-1.1)
  Behavior: the v1 runtime, owners, scaffold, harness links, rules, command stub, tests and cassettes are gone.
  Check: `git ls-files scripts scaffold .cursor .grok .agents/skills .agents/rules .agents/commands tests/cassettes uv.lock`; expect no output.
- [x] AC-1-2. Link cleanup carried (spec AC-1.2)
  Behavior: carried link cleanup still passes its v1 cases.
  Check: `python3 -m unittest tests.test_links`; expect last line `OK`.
- [x] AC-1-9. No v1 terms in contracts (spec AC-1.9)
  Behavior: v2 contracts carry no v1 terms.
  Check: `grep -lE 'vault://|atlas_tool\.py|owner mode' .agents/AGENTS.md .agents/ARCHITECTURE.md; echo "exit=$?"`; expect only `exit=1`.
- [x] AC-1-3. Strict JSON through the plugin path (spec AC-1.3)
  Behavior: the CLI is reached through the plugin path and keeps strict JSON input.
  Check: in an omp session bash, `printf '{"a":1,"a":2}' | python3 "$(realpath skill://atlas-ask)/cli.py" status; echo "exit=$?"`; expect one JSON line with `"ok": false` and a problem naming duplicate key `a`, then `exit=2`.
- [x] AC-1-4. Plugin linked live (spec AC-1.4)
  Behavior: the plugin is linked live on g10.
  Check: `readlink ~/.omp/plugins/node_modules/atlas`; expect `/home/kim/dev/atlas`.
- [x] AC-1-5. Plugin metadata (spec AC-1.5)
  Behavior: plugin metadata is installable.
  Check: `python3 -c 'import json;d=json.load(open("package.json"));print(d["name"],d["version"],isinstance(d.get("omp"),dict))'`; expect `atlas 2.0.0 True`.
- [x] AC-1-6. Setup task (spec AC-1.6)
  Behavior: the setup task sets the hooks path.
  Check: `python3 tools/release/release.py setup >/dev/null && git config core.hooksPath`; expect `.githooks`.
- [x] AC-1-7. Release run decisions (spec AC-1.7)
  Behavior: the release run tags only shipped changes, bumps minor for a migration, ignores `v1`, retries untagged changes and writes both trailers.
  Check: `python3 -m unittest tests.test_release`; expect last line `OK`.
- [x] AC-1-8. Skills check (spec AC-1.8)
  Behavior: shipped skills pass the skills check.
  Check: `python3 ~/.omp/plugins/node_modules/dotagents/skills/craft-skill/scripts/check_skills.py skills; echo "exit=$?"`; expect only `exit=0`.
- [x] AC-1-12. Stage 1 smoke through atlas-ask (spec AC-1.12)
  Behavior: the stage 1 smoke through `atlas-ask` reaches the CLI by the plugin path and shows the not-set-up reply.
  Check: in an omp session in `~/dev/atlas`, ask "Is Atlas set up?"; expect the transcript shows one `python3 "$(realpath skill://atlas-ask)/cli.py" status` call exiting 3, and the reply says Atlas is not set up and ends with a Next naming `atlas-init`.
- [x] AC-X1. Core names no host
  Behavior: core names no host, repo or omp setting.
  Check: `grep -rniwE 'omp|openrouter|typesafe|modelroles' skills/atlas-ask/atlas/core; echo "exit=$?"`; expect only `exit=1`.

## Recovery and stops

- Recovery: Completed work is preserved by the cutover and shell commits and the accepted Handoffs; resume at the first unchecked task with its same child, under `skill://dev-implementation/references/execution-recovery.md` for execution-mechanism failures. Live and human-gated checks and the offline proof that stands if their live evidence predates a later repair of their target (spec section 10): AC-1-12 → AC-1-3 plus `tests/test_cli.py`'s exit-3 and strict-JSON cases; AC-1-4 has no offline proof and is rerun (one `readlink`). AC-1-3 and AC-1-12 need a session whose skill list includes the linked plugin: any session that started before the link, including every subagent of this route's Main session, runs them inside a fresh non-interactive omp session in `/home/kim/dev/atlas` (for example `omp -p --no-session --mode json "<prompt>"`, whose JSON event stream is the transcript); AC-1-3 there asks the session to run the check's exact bash command and report its output. AC-1-12 must find no `~/.config/atlas/config.toml`. Spec AC-1.10 and AC-1.11 are read back by the route's `dev-shipping` stage after the push, not by this plan.
- Stops: A needed change to a ticket or spec decision, to the approved acceptance text, or to the route's two decisions; any effect outside "Effects" (push, tag, release, install, a `~/.config/atlas/` or `~/.local/share/atlas/` write, the real `~/.cache/atlas-release`); `check_skills.py` or `omp plugin link` unavailable; a target outside the task's list; a direct check still failing after permitted recovery.

## Completion Summary

- Delivered: v1 removed in one cutover commit (d7ab181) with link cleanup and strict JSON carried into `skills/atlas-ask/atlas/core/`; the v2 omp plugin shell (043de31): package.json 2.0.0, CLI shell answering all ten commands with exit 3 and Next `atlas-init`, minimal atlas-ask and atlas-init skills, release tool, pre-push hook and setup task; review repairs c758892 (oversized numbers are bad input) and 84d8a9e (notify found in the dotfiles checkout).
- Checks: AC-1-1 through AC-1-9, AC-1-12 and AC-X1 VERIFIED by the independent verifier on 84d8a9e, plus closure checks CR-1 and CR-2; review loop ended APPROVED in round 2.
- Shipping: v1 and main pushed to origin; the release run passed its gates and created tag and GitHub Release v2.0.0 (spec AC-1.10); after the user made kimprap/atlas public, the fresh-home install `omp plugin install github:kimprap/atlas#v2.0.0` lists `atlas` (spec AC-1.11).
- Residual: the records boundary (ADRs 0008-0010, INDEX.md superseded marks, Terms glossary) is still to run; the AC ID grammar mismatch between specifications and the plan validator is a deferred learning proposal.
- Next: the stage 1 records boundary through /dev-ask, then stage 2.
