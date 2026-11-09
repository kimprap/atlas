# Ticket 14 interview: questions as shown and the human's answers

Ticket: ~/dev/atlas/.scratch/atlas-v2/issues/14-decide-atlas-plugin-release.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label is the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Facts shown before round 1 (checked on g10, 2026-11-09):

- `kimprap/atlas` is private and installs over SSH like dotagents; it has no `package.json` yet (stage 1 creates it); the Python CLI has no third-party dependencies (`pyproject` `dependencies = []`).
- The store is per machine (`~/.local/share/atlas/<profile>.db`) and host-backup is per host, so a Mac install would start a second library; the hosted store adapter is later.
- dotagents' daily sync extension upgrades only `dotagents` and reads only its tags; Atlas's architecture ships "no omp extension".
- The Mac is offline right now (SSH timed out), so its state was not checked.
- g10: omp 18.18.0, dotagents linked; dotagents is published at v0.5.1.

## Round 1

### mac
Question: "1. Does the Mac run Atlas v2?"
- g10 only in v2 (Recommended) — "Keeps one library. The Mac uses Atlas by working on g10. The plugin is still installable (package.json, git install tested in a throwaway home), and a Mac install comes with the hosted store."
- Mac installs, own store — "Atlas works on the Mac now, but with a second library. Sources added on one machine are missing on the other, and re-adding them costs summary calls again."
- Mac installs, reaches g10's store — "One library on both machines, but this needs a remote store adapter, which the architecture puts after v2. Adds scope."
Answer: g10 only in v2

### tags
Question: "2. How are Atlas releases tagged?"
- Hand tags at milestones (Recommended) — "v2.0.0 when stage 8 is done, then a minor tag for each later feature release. The package.json version matches the tag. Installs track main; a tag is a rollback point. No hook."
- Auto patch tag per push — "A pre-push hook in the atlas repo tags every push to main, like dotagents. More tags, and another hook to build."
- No tags after v1 — "Simplest. No named rollback points, and package.json carries a fixed version."
Answer: Auto patch tag per push, with this note, given exactly:

```text
optimize the push as well, like what ive done with dotagents.
```

### catalog
Question: "3. Does Atlas get a marketplace catalog entry?"
- No catalog (Recommended) — "Same as dotagents. A git install is enough; Atlas has no JS dependencies to vendor. A catalog would only add marketplace auto-update."
- Catalog entry — "Adds marketplace auto-update and per-repo scope, but there is a catalog repo to maintain."
Answer: No catalog

### compat
Question: "4. How strictly does Atlas tie itself to omp and dotagents versions?"
- Warn, don't block (Recommended) — "package.json and the tag message name the omp and dotagents versions Atlas was tested with. `status` warns on a mismatch. A Reconcile refusal already falls back to \"not cross-checked\"."
- Exact pin, refuse — "Like dotagents' controller, Atlas refuses to run on another omp version. Safer against gateway changes, but every omp update stops Atlas until the pin moves."
Answer: Warn, don't block

Facts shown before round 2 (read on g10, 2026-11-09): dotagents' publish (`.githooks/pre-push` → `dotagents.py publish --after-push --background`) never makes the push wait. It runs detached after the push exits, at nice 19, and goes ahead only if `origin/main` still equals the pushed commit. It caches each suite's pass by an input hash and skips the controller suite when its inputs haven't changed. It takes one lock per repo, reports the outcome through `notify`, and creates a GitHub Release for each new tag. With Atlas on g10 only through the link, v2 needs no upgrade mechanism.

## Round 2

### trigger
Question: "1. How does the per-push tag run?"
- Background after push (Recommended) — "Like dotagents: the pre-push hook starts a detached run and the push never waits. After the push lands, it runs Atlas's Python tests and check_skills on the pushed commit, then tags it only if they pass. Passes are cached by an input hash, it runs at nice 19 with one lock, and notify reports the result. A failure skips the tag; the next push retries."
- Blocking pre-push — "Checks run before the push, and a failure stops the push. Simpler, but every push waits for the tests."
Answer: Background after push

### which
Question: "2. Which pushes get a tag?"
- Only plugin changes (Recommended) — "A tag only when the push changes shipped plugin files (skills, rules, CLI, package.json). Pushes that only touch docs, .scratch or tests get no tag, and that includes these map commits."
- Every push to main — "Simpler rule, but you get tags that change nothing Atlas runs."
Answer: Only plugin changes

### ver
Question: "3. How are version numbers set?"
- v2.0.x; minor per migration (Recommended) — "The first tag is v2.0.0. Each tagged push bumps the patch. The minor bumps when a push adds a store migration (SQLite user_version), so rolling back across a minor tells you the store is newer than the code. package.json matches the tag."
- Patch only — "Every tag bumps the patch; minors and majors happen only by hand."
Answer: v2.0.x; minor per migration

### home
Question: "4. Where does the tagging tool live?"
- Atlas repo (Recommended) — "A small release script plus `.githooks/pre-push` in kimprap/atlas, with core.hooksPath set by a repo setup task. It copies dotagents' patterns (background, cache, lock, notify) without an export step. dotfiles stays unaware of Atlas."
- Generalize dotagents.py — "One shared publisher in dotfiles serves both plugins. Less duplicated code, but dotfiles then has to know about Atlas, which the architecture rejected for init-ask."
Answer: Atlas repo

### when
Question: "5. When is the tagging built?"
- Stage 1 (Recommended) — "Built with the plugin shell and package.json, so every stage's push is tagged and each stage has a rollback point."
- Stage 4 — "Built with first-usable Atlas. Pushes before real data get no tags, so stage 1 has less work."
Answer: Stage 1

### notes
Question: "6. What goes with each tag?"
- Tag message + GitHub Release (Recommended) — "Like dotagents: the annotated tag lists the commit subjects since the last tag and the omp and dotagents versions it was tested with (your 'warn, don't block'), and a GitHub Release is created from it. No CHANGELOG file."
- Tag message only — "No GitHub Release, so no gh step. Less visible on GitHub."
Answer: Tag message + GitHub Release

Facts shown before round 3: the tag goes on a commit that is already pushed, so that commit's `package.json` can't hold the new version, and making them match would need an extra release commit for every tag. On g10, dotagents is linked from dotfiles and reports `0.0.0` (`omp plugin list` → `dotagents@0.0.0`), so the linked plugin has no real dotagents version to record.

## Round 3

### pkgver
Question: "1. The tag goes on a commit that is already pushed, so that commit's package.json can't carry the new version. Which do we drop?"
- Tag is the version (Recommended) — "package.json stays at 2.0.0 and only changes by hand. The tag is the real version, and `status` shows `git describe` (e.g. v2.0.7) when Atlas runs from a checkout. Matching package.json to tags comes back when other machines install. No extra commits and no background writes to ~/dev/atlas."
- Release commit per tag — "The background run commits the package.json bump in its own clone, tags that commit and pushes both. The filter ignores the version field, so it doesn't loop. Cost: local main is one commit behind after every tag, so you pull before the next commit."
Answer: Tag is the version

### dotver
Question: "2. On g10, dotagents is linked and reports 0.0.0. What does Atlas record and warn on?"
- omp exact; dotagents by identity (Recommended) — "The tag message records the exact omp version and dotagents' identity: the dotfiles commit when linked, the version when installed. `status` warns on an omp mismatch only. dotagents problems already show up through Reconcile's `ready atlas-ask` check and the 'not cross-checked' fallback."
- omp only — "Record and warn on omp only; dotagents isn't mentioned. Simpler, but a regression caused by dotagents leaves no trace in the tag."
Answer: omp exact; dotagents by identity

## Final confirmation

Question: "Is the nine-item summary above the shared understanding for Decide Atlas plugin release?", asked after the nine-item summary was shown in full (the ticket's "Proposed answer" section at the time).
- Confirm (Recommended) — "Record the summary as the proposed answer. Next is the Reconcile run that the map's Notes require."
- Change something — "Say which item to change; I'll recompute and show the summary again."
Answer: Confirm, with this note, given exactly:

```text
reconcile no yield.
```

## After the Reconcile run

The run's front was shown first, then the changed item 7 quoted before and after (see the [Reconcile record](14-reconcile-record.md) diff).

### change
Question: "1. Keep the reviewers' change to item 7 (compare with the latest tag, so a failed run's shipped changes still get tagged on the next push)?"
- Accept the reviewers' change (Recommended) — "A tag goes on when shipped files differ from the latest tag, so after a failed run any next push, even a docs-only one, tags the untagged shipped changes."
- Keep the original item 7 — "Only pushes that themselves change shipped files get a tag. A failed run's changes wait for the next shipped change."
Answer: Accept the reviewers' change

### close
Question: "2. Record the reviewed answer and close the ticket?"
- Confirm (Recommended) — "Write the reviewed answer into Decide Atlas plugin release, close it, add its line to the map's Decisions so far, and add the stage-1 and status changes as notes on Decide Atlas build order and Decide Atlas v2 architecture."
- Change something — "Say what to change before the ticket closes."
Answer: Confirm
