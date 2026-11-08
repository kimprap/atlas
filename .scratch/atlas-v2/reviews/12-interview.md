# Ticket 12 interview: questions as shown and the human's answers

Ticket: ~/dev/atlas/.scratch/atlas-v2/issues/12-decide-source-identity.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label is the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Facts shown before round 1 (checked on g10, 2026-11-08):

- v1's `atlas_url.py` (tag `v1`): lowercases scheme and host, IDNA, drops default port, trailing `/`, fragment, `utm_*`, X `s=<digits>`; `twitter.com` → `x.com`. Key = the link as given; the redirected link is recorded but not keyed. Hash = SHA-256 of the exact page text.
- v1 library (673 sources: 382 GitHub, 191 X): 5 same-text pairs under different links (renamed repo, owner case `EveryInc`/`everyinc`, repo root vs README, two moved docs pages); 2 `www.` pairs; tracking params v1 missed: YouTube `si=` ×4, `ref=` ×1; X `/video/1` ×2.
- omp reader probe: the `URL:` line shows the redirected link for web and docs pages, but the old name for a renamed GitHub repo. GitHub output includes `Stars · Forks · Issues`; X output includes `Likes · Reposts · Views` and a `## Replies` section; X text is relayed by a model (two reads matched). Exact-byte hashing would mark most GitHub and X re-adds as changed.

The first ask of round 1 was cancelled by the human, who then asked for ticket 16 (Decide source summarization method) and a new work order; round 1 was asked again unchanged.

## Round 1

### key
Question: "1. Which link is a source's key?"
- Redirected link, old links kept (Recommended) — "Store under the link the reader reports after redirects (the given link when it reports none). The cleaned given link is kept as another link for the same source, so re-adding it finds the source without reading the page. Catches moved pages (3 of v1's 5 same-text pairs). Renamed GitHub repos still slip through, because the reader shows the old name."
- Link as given (v1) — "Key on the cleaned link the user gave. Simpler: one link per source. A moved or redirected page becomes a second source unless another rule catches it."
Answer: Redirected link, old links kept, with this note, given exactly:

```text
sounds good. additionally, make sure we have a mechanic to support cases where the given link links to a generic github repo/a video/an image/an X link where the author extended their post with another post, as replies, under their main post, etc. Generally, when it is not obvious on what the summarization should be on, or the scope of it, it should yield to human, with Next for options on what the agent suggest it could do next, and they should be meaningful to what the Atlas framework is about. The above scenarios are just quick examples, not exhaustive. To build on the above examples first, for github repo, it could ask if human wants to traverse the repo and summarize all the skills or not, with a number on how many skills it found, etc. video/image, agent could suggest extracting the transcript or read the image, etc. X link where author provided more content in replies - this should be intelligently reviewed, determining if the author replies are relevant to the main post or not, or they are merely just ordinary replies author made on other people's replies on the main post, which in this case author replies shouldn't be covered, and the scenario would fall under the regular X post, not one that agent should yield, etc.
```

### cleanup
Question: "2. Which link cleanup rules?"
- v1 rules plus fixes from v1 data (Recommended) — "Keep v1's rules and add: drop `www.`; treat http as https; drop more tracking parameters (`fbclid`, `gclid`, `ref`, `ref_src`, `igshid`, `mc_cid`, `mc_eid`, YouTube `si` and `feature`); `youtu.be/ID` → `youtube.com/watch?v=ID`; lowercase GitHub owner and repo; X: lowercase the handle and drop `/photo/N` and `/video/N`. Each one fixes duplicates seen in v1. Risk: a rare site where `www.` or `ref` changes the page."
- v1 rules plus tracking parameters only — "Add only the extra tracking parameters and the YouTube short link. Keep `www.`/http and GitHub case as distinct links. Safer on odd sites, but leaves v1's 3 known duplicate pairs."
- v1 rules unchanged — "Keep exactly what v1 does. Leaves every duplicate listed above."
Answer: v1 rules plus fixes from v1 data, with this note, given exactly:

```text
revisit, refine, and refactor. don't make it brittle.
```

### hash
Question: "3. What does the content hash cover?"
- Cleaned page text (Recommended) — "Hash the page text after the reader's header lines, with line endings, Unicode (NFC) and whitespace runs normalized. Drop the reader's counter lines (GitHub `Stars · Forks · Issues`; X `Likes · Reposts · … · Views`) and X's `## Replies` section. Without this, almost every GitHub or X re-add counts as changed and is summarized again. A rare edit to the dropped parts is missed."
- Exact text (v1) — "Hash the text exactly as received. Never misses a change, but counters and new replies make GitHub and X re-adds look changed, and each one is summarized again."
Answer: Cleaned page text

### sametext
Question: "4. A new link has exactly the same cleaned text as a stored source. What happens?"
- Join as another link (Recommended) — "`add` reports \"already stored as <link>\", keeps the new link as another link for that source, and does not summarize. This is deterministic: no Jev and no confirm. It would have merged all 5 v1 pairs (renamed repo, case, README vs repo root, moved docs)."
- Store separately — "Store and summarize it as its own source. Simpler, but gives a duplicate summary in search; a near-duplicate flag may point it out."
Answer: Join as another link, with this note, given exactly:

```text
maek sure this kind of scenario, including duplicates, etc, are properly handled. if the source has been summarized before, agent shouldn't spend more tokens summarizing them. make sure all edge cases are properly handled, i.e. link differs to the vault by a bit but they're both the same, Atlas framework should know this and reuse from the vault without performing summarization work. Or another case where link is the same, or similar, but content has been updated or newer than when our summary was created, in this case it should margianlly update the vault summary from the source new content accordingly, etc. Generally, this mechanic should be refined so the framework work efficiently.
```

### neardup
Question: "5. How do Jev's near-duplicate flags work?"
- Flag after add, no merge (Recommended) — "After `add` stores a new source, Atlas takes the 5 closest stored sources by BM25 on title and abstract, and Jev flags any that look like the same work (a repost, mirror, renamed repo or copy elsewhere). The reply shows \"may be a copy of <link>\". Nothing is merged or dropped. If the user agrees, they archive one with the existing `archive` command. Costs one cheap Jev call per added source. No new command."
- Flag after add, plus a merge step — "Same flag, plus a confirm-gated merge that joins the two as one source with both links. Cleaner library, but adds an eleventh command or a new `add` option."
- Flag before summarizing — "Jev compares the new page with the closest stored abstracts first, and a flagged link waits for the user before it is summarized. Saves a summary per duplicate, but adds a stop in the middle of a batch."
Answer: Flag after add, no merge

Facts shown before round 2 (probe, 2026-11-08): the reader turns `youtu.be/…` into `youtube.com/watch?v=…` and already returns the auto-generated transcript; for a repo it lists only top-level files, so counting skills needs a deeper file listing.

## Round 2

### scope
Question: "1. When it's unclear what one source covers, what happens?"
- `add` returns "pick scope" with options (Recommended) — "Extends ticket 06's \"page of links\" outcome. Atlas checks the page in code from the reader's `Method` line and simple counts. Nothing is summarized until the user picks, and the choice is kept so a re-add doesn't ask again.
- Repo holding several separate items (≥2 skills, plugins or packages, from its full file list): the repo as one source, each item as its own source (N found), or both, with items linked to the repo.
- Video: summarize from the transcript, or skip.
- Image, or a page that is mostly images: read the images with a model, or skip. This adds images to ticket 02's accepted input.
- Page that mostly lists links: this page, or each link (N).
- X post: no stop. Atlas keeps the post plus the author's own replies (by handle) and drops other people's replies. The summarizing model keeps only the author replies that continue the post.

The agent may also stop on its own judgment for any other unclear page, with Next options."
- Agent judgment only — "The `atlas-ask` skill lists these cases and tells the agent to stop and offer options. `add` has no new outcome. More flexible, but it varies by agent and model, and a later scheduled fetcher has no agent to stop."
Answer: `add` returns "pick scope" with options, with this note, given exactly:

```text
sounds good - make sure happy path do not yield, i.e. a clear X link to a post with no author replies under the post that extend the content of the main post, etc. This should be able to proceed with summarization work right away.
```

### cleanup2
Question: "2. Refined cleanup, per your note \"don't make it brittle\": three layers instead of one growing list?"
- Safe rules, site table, safety net (Recommended) — "(1) Generic rules that never change the page: v1's (case, IDNA, port, fragment, trailing `/`, `utm_*`) plus known tracking parameters (`fbclid`, `gclid`, `igshid`, `mc_cid`, `mc_eid`). Unknown parameters are kept.
(2) A small table with one tested row per site: X (twitter alias, `s=`, handle case, `/photo/N`, `/video/N`), GitHub (owner and repo case, `ref`), YouTube (`si`, `feature`, short link).
(3) Safety net: the reader's redirected link and the same-text join catch whatever the rules miss. A miss costs one page read, never a summary.

Dropped from round 1: the blanket `www.` and http→https rules, because redirects already handle them on most sites (anthropic.com → www.anthropic.com seen) and the same-text join catches the rest."
- Round-1 list as chosen — "Keep every round-1 rule, including blanket `www.` and http→https folding. Catches those pairs without a read, but can merge two different pages on the rare site where they differ."
Answer: Safe rules, site table, safety net

### reread
Question: "3. Someone adds a link that's already stored. Does the agent read the page again to check for changes?"
- Only if last checked >30 days ago (Recommended) — "Checked within 30 days: report \"already stored, checked <date>\" with no read, and Next offers \"check for updates now\". Older: read, compare the hash, and update if changed. Reading puts the whole page into the calling agent's context, often the priciest tokens in the flow."
- Never on its own — "Always report \"already stored, checked <date>\". Next offers \"check for updates\". Cheapest, but updates are found only when someone asks."
- Always read — "Every re-add reads and compares. Always current, but each one costs a full page in the agent's context."
Answer: Never on its own, with this note, given exactly:

```text
let's never re-read, but show the last read date. additionally, it could ask to re-read as an optional next step human could let agent do. Evaluate what would make the final response less verbose with this optional reread, given this would be present in all dev-ask invocations. Maybe the 30 days threshold could be used for this case, to dynamically propose optional re-read when it's passed this threshold? How practical would this be though? Weigh between its practicallity and its brittleness.
```

### pagetext
Question: "4. Does Atlas keep the cleaned page text, unsearched, beside the summary?"
- Keep it, compressed, unsearched (Recommended) — "This makes possible: a near-identical check before summarizing (no tokens spent on a near-copy), updates that look only at what changed, ticket 16's claim-locator checks, and re-summarizing with a new method or model without reading again. Cost: about 7–23 KB per page in today's probes, roughly 15 MB per 700 sources before compression. Adds one field to ticket 02's stored record; search still reads only the summary."
- Hash only (ticket 02 as written) — "Smaller store. A changed page is summarized again from scratch, near-copies are caught only after summarizing, and a new method or model needs every page read again."
Answer: Keep it, compressed, unsearched

Shown before round 3: the 30-day check is practical and not brittle. It is one date comparison in code and one setting; the real risk is noise, not breakage. Noise stays low by showing the offer only for sources a reply relies on, as one combined line, and by never counting sources that can't change.

## Round 3

### stale
Question: "1. When does Next offer an optional re-read?"
- Past 30 days, one combined line (Recommended) — "Replies show each source's last-read date where they already show its date, so no extra line. Next offers a re-read only when a source the reply relies on (in `add`, `ask` or the dev-research rule) was last read over 30 days ago, as one line for all of them: \"Re-read 3 sources last read over 30 days ago\". Sources that can't change never count: an X post, a GitHub file pinned to a commit, a versioned arXiv paper (a column in the site table). Practical: one date comparison in code and one setting. Worst case is an unneeded offer, never a wrong answer."
- Only on re-add — "The offer appears only in `add`'s \"already stored\" reply when that source is past 30 days. Answers never offer it and only show dates. Quietest, but staleness in answers is easy to miss."
- Always offer on re-add — "Every already-stored link in `add` gets a re-read offer, whatever its age. Simple, but noisy on batches."
Answer: Past 30 days, one combined line

### nearident
Question: "2. A new link's text is nearly the same as a stored source's (not exact). What happens before any summary is written?"
- ≥90% same: join, no summary (Recommended) — "Atlas compares the new text with stored page text in code (no model). At 90% or more the same, it joins the link to that source without summarizing and reports \"already stored as <link> (N% same)\". Next offers \"store it separately instead\". Below 90%, it is summarized as new, and Jev's near-duplicate flag after `add` still applies."
- Report it, still summarize — "Store and summarize it as its own source, with the reply noting \"N% same as <link>\". Never joins wrongly, but spends a summary on near-copies."
- Ask before summarizing — "A near-copy waits for the user to choose join or separate. Never wrong, but adds a stop in the middle of a batch."
Answer: ≥90% same: join, no summary

### update
Question: "3. A re-read finds the page changed. How is the stored summary updated?"
- Check the change in code, then update only what changed (Recommended) — "Atlas compares the stored and new text. If no passage a claim cites has changed and the page gained less than 5% new text, it records the new hash and read date, keeps the summary, and reports \"re-read, no meaningful change\". Otherwise it gives the old summary plus the changed parts to ticket 16's update method, which revises only the affected claims. Topics citing the source are flagged only when a claim changed. This narrows ticket 02's \"topics flagged on any change\", and depends on ticket 16's claim locators."
- Always a model update — "Every change sends the old summary plus the changed parts to the model. One small call per change; topics flagged on any change (ticket 02 as written)."
- Summarize again from scratch — "Ticket 02 as written: a changed page is summarized again in full. Simplest, and spends the most."
Answer: Check the change in code, then update only what changed

## Final confirmation

Question: the ten-item summary of the proposed answer, shown in full with the options "Confirm" and "Change something" (the full text is the ticket's "Proposed answer" section).
Answer: Confirm
