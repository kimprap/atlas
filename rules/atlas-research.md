---
description: Use when researching an engineering question (dev-research or other web research) in a repository whose shell sets ATLAS_PROFILE.
---

# Atlas research

Run `printenv ATLAS_PROFILE` first. When it prints nothing, this rule does not apply: research as usual and read no further. Otherwise follow the four steps below. Call Atlas only through the `atlas-ask` skill's call forms (read `skill://atlas-ask`), leave the profile to `ATLAS_PROFILE` and never send `profile` in a body.

1. **Ask Atlas first.** Before any web search or fetch, run `find` or `ask` with the research question, written to stand on its own. Use the stored sources it returns as evidence, never as the only check of a claim that needs fresh evidence.
2. **Research as usual.**
3. **Collect what the result relied on.** At the end, list every source the result relied on, stored or not, and every topic version it relied on (the topic's name and the saved version's number). The repo is `git remote get-url origin` parsed to `owner/name` (for `https://github.com/owner/name.git` or `git@github.com:owner/name.git`, `owner/name`), else the folder name of `git rev-parse --show-toplevel`. The file is the repo-root-relative path of the file the research result is written into. When the result is written into no file, ask the user which file holds it; when none does, propose the add without `cited_in`.
4. **Propose one `add`.** Send one `add` with every link as an item and `"cited_in": {"repo": "<owner/name>", "file": "<path>"}` (plus `"topics": [{"topic": "<name>", "version": <n>}]` when topic versions were relied on), with no `approval` and no `join`. Atlas answers with one `confirm` decision: show it and wait for the user's answer; never answer it yourself. One proposal per research run.
