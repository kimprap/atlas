# Atlas umbrella repo scaffold and vault cutover

**Datetime**: 2026-07-09-1503
**Scope**: Establish `~/Desktop/ng3/atlas/{framework,vault}` dual-repo layout; Obsidian-safe move of live vault data; complete scaffolds + gitignores; relocate Atlas skills out of `~/.dotfiles` with local harness continuity.
**Summary**: Create a non-git parent namespace and two git-versioned children (`framework`, `vault`), move the existing Obsidian Atlas tree into `vault/instances/personal`, seed connector/profile scaffolds, copy product skills/contracts into `framework`, and leave only path/symlink glue in dotfiles.
**Status**: DONE

**Durable plan path (cwd)**: `.agents/plans/2026-07-09-1503_atlas-umbrella-scaffold.md`  
On execution start, copy this plan into that path if missing, then drive all task checks from the cwd copy.

---

## Context

Atlas Phase 1 workflows were implemented in the wrong repo (`~/.dotfiles` skills + Desktop vault). Target:

| Path | Git | Role |
|---|---|---|
| `~/Desktop/ng3/atlas/` | **No** | Umbrella namespace only |
| `~/Desktop/ng3/atlas/framework/` | **Yes** | Product: skills, contracts, scaffold, future deploy |
| `~/Desktop/ng3/atlas/vault/` | **Yes** | Instances + connectors + profiles |

Current disk (pre-cutover):

- `~/Desktop/ng3/atlas/` — live Obsidian vault + `.agents/AGENTS.md` (framework draft)
- `~/Desktop/ng3/atlas-vault/` — stub with vault `.agents/AGENTS.md` only
- Skills: `~/.dotfiles/.config/agents/skills/atlas-*` + `digest` (+ Grok mirrors under `.grok/skills/`)

Decisions already locked (do not reopen):

1. Parent not git-versioned; only the two children are git roots.
2. Vault repo root is **not** the Obsidian root; Obsidian opens `instances/personal/`.
3. Connectors + profiles make local offline and remote online pluggable; no dual-write.
4. Framework does not store personal research rows after cutover.

---

## Execution intent

End state:

- `~/Desktop/ng3/atlas/README.md` explains the umbrella; **no** `.git` at parent.
- `framework/` is a git repo with complete product scaffold, copied skills, `ARCHITECTURE.md`, empty `scaffold/` instance template, `.gitignore`, `.agents/AGENTS.md`, README.
- `vault/` is a git repo with connector/profile scaffold, live data under `instances/personal/` (including `.obsidian`, `todos/`, real run log), `.gitignore`, `.agents/AGENTS.md`, README.
- Stale `~/Desktop/ng3/atlas-vault` and any migrate temp dirs are gone.
- Dotfiles no longer **own** Atlas skill bodies; local agents still resolve them via **symlinks** into `framework/skills/`.
- Obsidian vault reopens at `.../vault/instances/personal` without content rewrite.

---

## Tasks

- [x] T1. Materialize durable plan in cwd and freeze pre-move inventory
  completed 2026-07-09-1509
- [x] T2. Obsidian-safe filesystem restructure to umbrella + two children
  completed 2026-07-09-1509
- [x] T3. Complete `vault/` scaffold (config, connectors, gitignore, README, AGENTS)
  completed 2026-07-09-1509
- [x] T4. Complete `framework/` scaffold (skills, ARCHITECTURE, scaffold/, gitignore, README, AGENTS)
  completed 2026-07-09-1509
- [x] T5. Wire dotfiles harness continuity (symlinks; remove duplicated skill trees)
  completed 2026-07-09-1509
- [x] T6. Git init both children; initial commits; parent has no git
  completed 2026-07-09-1509
- [x] T7. Verification pass and Obsidian reopen checklist
  completed 2026-07-09-1509

---

## Ordered implementation

### T1. Materialize durable plan in cwd and freeze pre-move inventory

1. Ensure `.agents/plans/` exists under `~/.dotfiles`.
2. Write/copy this plan to:
   `~/.dotfiles/.agents/plans/2026-07-09-1503_atlas-umbrella-scaffold.md`
3. Record a short inventory (append under a `## Pre-move inventory` note only if useful; otherwise keep in executor notes):
   - Files under current live vault
   - Atlas skill paths in `.config/agents/skills` and `.grok/skills`
4. Confirm Obsidian is closed (or this vault not open) before T2. If open, **stop and ask user**.

### T2. Obsidian-safe filesystem restructure

Use only whole-tree `mv` operations. Do not rewrite Markdown bodies during the move.

```bash
# Paths
NG3="$HOME/Desktop/ng3"
LIVE="$NG3/atlas"                 # current mixed tree
STUB="$NG3/atlas-vault"           # current vault AGENTS stub
TMP_LIVE="$NG3/_atlas_migrate_live"
TMP_STUB="$NG3/_atlas_migrate_vault_stub"
PARENT="$NG3/atlas"
FW="$PARENT/framework"
VAULT="$PARENT/vault"

# 1) Park current trees (frees the parent name)
mv "$LIVE" "$TMP_LIVE"
mv "$STUB" "$TMP_STUB"

# 2) Create umbrella + children
mkdir -p "$FW" "$VAULT/instances/personal"

# 3) Move live instance payload into vault instance root
for name in ARCHITECTURE.md summaries todos .obsidian; do
  mv "$TMP_LIVE/$name" "$VAULT/instances/personal/$name"
done

# 4) Seed agent guides from parked drafts (then rewrite paths in T3/T4)
mkdir -p "$FW/.agents" "$VAULT/.agents"
if [[ -f "$TMP_LIVE/.agents/AGENTS.md" ]]; then
  mv "$TMP_LIVE/.agents/AGENTS.md" "$FW/.agents/AGENTS.md"
fi
if [[ -f "$TMP_STUB/.agents/AGENTS.md" ]]; then
  mv "$TMP_STUB/.agents/AGENTS.md" "$VAULT/.agents/AGENTS.md"
fi

# 5) Remove empty park trees only when empty of real content
# (leave .DS_Store cleanup optional)
```

**Hard rules:**

- Preserve `instances/personal/todos/` untouched.
- Preserve the real run log under `summaries/sources/runs/...`.
- Do not `git init` the parent.
- If any unexpected path remains under `$TMP_LIVE` / `$TMP_STUB`, inspect before delete; do not `rm -rf` blindly.

### T3. Complete `vault/` scaffold

Create this tree (files listed are required):

```text
~/Desktop/ng3/atlas/vault/
├── .agents/
│   └── AGENTS.md                 # update paths → framework sibling, instances/personal
├── .gitignore
├── README.md
├── config/
│   ├── profile.yml               # active: local
│   └── profiles/
│       ├── local.yml
│       └── cloud.yml
├── connectors/
│   ├── README.md                 # interface contract only (no full cloud client yet)
│   ├── local-fs/
│   │   └── README.md             # root = instances/<id>; resolve vault:// relative to instance
│   ├── r2/
│   │   └── README.md             # stub: env-based bucket/prefix; no secrets
│   └── remote-api/
│       └── README.md             # stub: base URL for Worker/Flue front door
├── instances/
│   └── personal/                 # already populated from T2
│       ├── ARCHITECTURE.md
│       ├── summaries/
│       ├── todos/
│       └── .obsidian/
└── cache/
    └── .gitkeep                  # directory exists; contents gitignored
```

**`config/profiles/local.yml` (exact shape):**

```yaml
profile: local
instance: personal
connector: local-fs
local_fs:
  # Absolute path preferred for agents; relative allowed from vault repo root
  root: instances/personal
```

**`config/profiles/cloud.yml` (exact shape):**

```yaml
profile: cloud
instance: personal
connector: r2
r2:
  # Values from env at runtime — do not commit secrets
  bucket_env: ATLAS_R2_BUCKET
  prefix_env: ATLAS_R2_PREFIX
  account_id_env: ATLAS_R2_ACCOUNT_ID
  access_key_id_env: ATLAS_R2_ACCESS_KEY_ID
  secret_access_key_env: ATLAS_R2_SECRET_ACCESS_KEY
# Alternate connector: remote-api (document only; leave inactive)
# connector: remote-api
# remote_api:
#   base_url_env: ATLAS_VAULT_API_BASE_URL
```

**`config/profile.yml`:**

```yaml
active: local
```

**`connectors/README.md` minimum contract:**

- Logical paths: `vault://atlas/<rel>` → store key/path `<rel>` under instance root.
- Ops: `exists`, `read`, `write` (atomic replace where possible), `list(prefix)`, optional `etag` / conditional write.
- Exactly one active write backend per profile.
- `.obsidian/` is presentation; cloud connectors may skip it; reducers never require it.

**`vault/.gitignore` (required entries):**

```gitignore
.DS_Store
**/.DS_Store
cache/**
!cache/.gitkeep
**/.env
**/.env.*
**/__pycache__/
*.py[cod]
.banks/
banks/

# Obsidian churn (keep app/core plugin settings tracked)
instances/*/.obsidian/workspace.json
instances/*/.obsidian/workspace-mobile.json
instances/*/.obsidian/cache/
```

**Update `vault/.agents/AGENTS.md`:** replace `atlas-vault` naming and `~/Desktop/ng3/atlas-vault` with `~/Desktop/ng3/atlas/vault` and sibling `../framework`. Remove “migration pending” language once layout matches.

**`vault/README.md`:** one screen — purpose, open Obsidian on `instances/personal`, profiles, no secrets, relation to framework.

### T4. Complete `framework/` scaffold

```text
~/Desktop/ng3/atlas/framework/
├── .agents/
│   ├── AGENTS.md
│   └── plans/
│       └── archive/              # optional: copy cutover history later
├── .gitignore
├── README.md
├── ARCHITECTURE.md               # copy from instances/personal (keep both in sync for now)
├── skills/
│   ├── atlas-acquire/ … atlas-migrate/
│   ├── atlas-core/assets/…
│   └── digest/assets/…
└── scaffold/                     # empty starter instance (NOT personal data)
    ├── ARCHITECTURE.md           # same product SO copy
    ├── summaries/
    │   ├── INDEX.md
    │   ├── sources/{INDEX.md,MANIFEST.md}
    │   ├── registry/{VOCAB.md,TOPICS.md,RELATIONS.md}
    │   └── research/INDEX.md
    └── todos/
        └── TODOs.md              # minimal legacy stub OR copy structure without personal todos content
```

**Skill migration (copy then verify, then T5 removes originals):**

```bash
SRC="$HOME/.dotfiles/.config/agents/skills"
DST="$HOME/Desktop/ng3/atlas/framework/skills"
mkdir -p "$DST"
for s in atlas-acquire atlas-answer atlas-audit atlas-core atlas-index \
         atlas-migrate atlas-refresh atlas-research atlas-route atlas-source digest; do
  cp -R "$SRC/$s" "$DST/$s"
done
```

**`ARCHITECTURE.md`:** `cp` from `vault/instances/personal/ARCHITECTURE.md` to `framework/ARCHITECTURE.md` and `framework/scaffold/ARCHITECTURE.md`. Do not move away from the instance (Obsidian keeps its copy).

**`scaffold/` registries:** rebuild as **starter clean** from current instance headers (empty data tables), matching Phase 1 cutover clean shape:

- `MANIFEST.md` — header + empty table (no personal run-derived rows)
- `TOPICS.md` / `RELATIONS.md` — headers only, no rows
- `VOCAB.md` — source-kind rows only (as in current personal vocab source-kinds)
- Index files — storage rules text from current instance indexes (copy is fine)
- **Do not** copy `summaries/sources/runs/` into scaffold
- `todos/TODOs.md` — minimal stub (`# TODOs` + note legacy preserved in instances only), **do not** copy personal todos body into scaffold if it contains user content; if personal todos are short framework notes only, copy is OK — prefer stub if unsure

**`framework/.gitignore`:**

```gitignore
.DS_Store
**/.DS_Store
**/.env
**/.env.*
**/__pycache__/
*.py[cod]
node_modules/
.wrangler/
dist/
.turbo/
.banks/
banks/
*.log
```

**Update `framework/.agents/AGENTS.md`:**

- Paths: `~/Desktop/ng3/atlas/framework`, vault sibling `../vault`
- Remove “legacy Obsidian tree may still live here” migration note after T2
- Skills path: `skills/` in this repo

**`framework/README.md`:** product overview, skills list, vault binding via profiles, local symlink note for harness.

**Parent umbrella `~/Desktop/ng3/atlas/README.md` (not in either git repo):**

```markdown
# Atlas

Personal research framework + vault (local/cloud).

| Path | Git | Purpose |
|------|-----|---------|
| `framework/` | yes | Skills, contracts, scaffold, future Flue/Worker deploy |
| `vault/` | yes | Instance Markdown + connectors/profiles |

- Open Obsidian on `vault/instances/personal/`.
- Do not `git init` this parent directory.
```

### T5. Wire dotfiles harness continuity

Goal: agents in `~/.dotfiles` still load Atlas skills without owning the files.

1. For each skill name under `framework/skills/`, replace
   `~/.dotfiles/.config/agents/skills/<name>` with a **symlink** to
   `~/Desktop/ng3/atlas/framework/skills/<name>`.
2. Same for `~/.dotfiles/.grok/skills/<name>` if those directories exist as real trees (replace with symlinks to the same framework paths).
3. Use `ln -sfn` after moving originals aside only if symlink creation is verified; prefer:
   - `rm -rf` skill dir **only after** `cp -R` to framework succeeded and `diff -qr` (or equivalent) confirms copy
4. Do **not** symlink the entire skills parent; only Atlas product skills + `digest`.
5. Leave a one-line note in `framework/README.md` and optionally a short comment in vault/framework AGENTS that machine harness resolves skills via these symlinks until a harness multi-root skill path exists.
6. Do **not** move archived plans out of dotfiles in this plan (optional later). Dotfiles plan history stays; new Atlas work plans go under each child’s `.agents/plans/`.

**Manifest / dot-add:** if `manifest` lists atlas skill paths, no change required for symlinks as long as paths still exist. Do not stage Desktop paths into dotfiles git.

### T6. Git init both children

```bash
FW="$HOME/Desktop/ng3/atlas/framework"
VAULT="$HOME/Desktop/ng3/atlas/vault"

git -C "$FW" init
git -C "$VAULT" init

# Default branch main if needed
git -C "$FW" branch -M main 2>/dev/null || true
git -C "$VAULT" branch -M main 2>/dev/null || true
```

Initial commits (allowed; local only — **no push**):

- `framework`: `chore: initial atlas framework scaffold`
- `vault`: `chore: initial atlas vault scaffold and personal instance`

Stage carefully:

- Framework: all scaffold + skills + AGENTS + ARCHITECTURE + gitignore + README
- Vault: config, connectors, AGENTS, README, gitignore, `instances/personal` Markdown + tracked `.obsidian` settings; ensure `workspace.json` is ignored and not staged

Confirm **no** `.git` under `~/Desktop/ng3/atlas` parent:

```bash
test ! -e "$HOME/Desktop/ng3/atlas/.git"
```

Remove migrate temps when empty/safe:

```bash
rmdir "$NG3/_atlas_migrate_live" 2>/dev/null || true
rmdir "$NG3/_atlas_migrate_vault_stub" 2>/dev/null || true
# If non-empty leftovers, list and stop — do not rm -rf without inspection
```

### T7. Verification pass and Obsidian reopen checklist

Run checks in Verification section; fix gaps before marking tasks complete.

User-facing Obsidian steps (document in vault README; do not automate UI):

1. Close any old vault path entry for `~/Desktop/ng3/atlas`.
2. Open folder as vault: `~/Desktop/ng3/atlas/vault/instances/personal`.
3. Confirm notes, todos, and graph still resolve.

---

## Critical anchors

| Anchor | Role |
|---|---|
| `~/Desktop/ng3/atlas/` | Non-git umbrella |
| `~/Desktop/ng3/atlas/framework/` | Framework git root |
| `~/Desktop/ng3/atlas/vault/` | Vault git root |
| `vault/instances/personal/` | Obsidian + `vault://atlas` instance root |
| `vault/config/profiles/*.yml` | local vs cloud binding |
| `framework/skills/` | Product skills SO |
| `framework/scaffold/` | Clean starter for new instances |
| `~/.dotfiles/.config/agents/skills/atlas-*` | Symlinks only after T5 |
| Archived cutover | `.agents/plans/archive/2026-07-07-1145_atlas-command-cutover.md` (history only) |
| Draft AGENTS (pre-move) | current `atlas/.agents` and `atlas-vault/.agents` — rewrite after path settle |

---

## Assumptions and fallbacks

- Obsidian will be closed before T2; if not, halt.
- Skill discovery continues via symlink into framework; full harness multi-root config is out of scope.
- Cloud connectors are **documented stubs only** — no R2 client implementation, no Flue deploy in this plan.
- `ARCHITECTURE.md` dual-copy (framework + instance) is accepted; future single-source pin is a later plan.
- Initial git commits stay local; remotes/push only on explicit user request.
- If `cp` of skills fails mid-way, do not delete dotfiles originals.
- If personal data appears mixed into scaffold construction, stop and exclude that path from scaffold.

---

## Out of scope

- Implementing R2/remote-api clients or Flue/Worker deploy packaging
- SQLite / FTS / vector / cron refresh
- Changing reducer semantics or re-running Atlas smoke fixture suites against personal instance
- Pushing to GitHub or creating remotes
- Migrating non-Atlas dotfiles agent content
- Editing personal research Markdown content (move only)

---

## Verification / Done criteria

- [x] `test ! -e ~/Desktop/ng3/atlas/.git` — parent not a git repo
- [x] `test -d ~/Desktop/ng3/atlas/framework/.git` and `test -d ~/Desktop/ng3/atlas/vault/.git`
- [x] `test ! -e ~/Desktop/ng3/atlas-vault` and migrate temp dirs gone or empty-explained
- [x] `test -f ~/Desktop/ng3/atlas/vault/instances/personal/ARCHITECTURE.md`
- [x] `test -d ~/Desktop/ng3/atlas/vault/instances/personal/.obsidian`
- [x] `test -f ~/Desktop/ng3/atlas/vault/instances/personal/todos/TODOs.md`
- [ ] Real run log still present: `summaries/sources/runs/2026/2026-07/2026-07-08--mnemopi-memory-retain-verification.md`
- [x] `vault/config/profile.yml` active `local`; `profiles/local.yml` + `cloud.yml` exist
- [ ] Connector README stubs exist for `local-fs`, `r2`, `remote-api`
- [x] `framework/skills` contains all `atlas-*` + `digest` with assets
- [x] `framework/scaffold/summaries/sources/MANIFEST.md` has no data rows; no `runs/` under scaffold
- [ ] Each `~/.dotfiles/.config/agents/skills/{atlas-*,digest}` is a symlink into `framework/skills/...`
- [x] `git -C framework status` clean after initial commit; `git -C vault status` clean (modulo ignored workspace.json if present untracked-ignored)
- [x] `git -C vault check-ignore -v instances/personal/.obsidian/workspace.json` succeeds
- [ ] No secrets/env files committed (`git -C vault ls-files | rg env` empty of real secrets)
- [ ] Durable plan exists at `~/.dotfiles/.agents/plans/2026-07-09-1503_atlas-umbrella-scaffold.md`
- [ ] Parent + both README files and both AGENTS.md describe the final layout (no stale `atlas-vault` path)

---

## Skill outcomes / design captures

- **Deep modules:** connector interface is a small port; instance Markdown remains the business state; framework skills remain workflow modules.
- **No dual-write:** profile selects one connector.
- **Harness locality:** product skills live in framework; machine harness uses symlinks as temporary binding.
- **Obsidian safety:** whole-tree move of instance root; reopen path change only.

## Completion Summary

- T1 materialised durable plan under `.agents/plans/` and inventoried pre-move trees; Obsidian was quit before move.
- T2 restructured to `~/Desktop/ng3/atlas/{framework,vault}`; live Obsidian payload moved intact to `vault/instances/personal/` (including todos, run log, `.obsidian`).
- T3–T4 completed vault connector/profile scaffold and framework skills+scaffold; parent README only (no parent git).
- T5 replaced dotfiles skill bodies with symlinks into `framework/skills/` (`.grok/skills` already symlinks to `.config/agents/skills`).
- T6 initial commits: `framework` `85598b0`, `vault` `3e10c74` (local only, no remotes/push).
- T7 all verification criteria passed; `workspace.json` gitignored.
- Residual: reopen Obsidian on `vault/instances/personal/`; commit dotfiles symlink changes if/when desired; cloud connectors remain stubs.
- Outcome: dual-repo Atlas umbrella ready for local use and future remote binding.
