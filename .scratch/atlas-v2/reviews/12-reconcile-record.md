## Review rounds

| Step | Reviewer/event | Pass | Text | Outcome | Turn |
|---|---|---|---|---|---|
| 1 | A | post-rethink | 2dfe344e | edit<br>• The answer matches the human's choices and notes in all three rounds<br>• Its list of changes to earlier decisions misses two real conflicts<br>• Requirements re-summarize a changed page in full; this answer updates only affected claims<br>• Architecture reads every page before add; this answer never reads a stored link again | 124 s · 19 tools · 607k tokens · wait 3 s |
| 2 | B | post-rethink | 2dfe344e | edit · superseded<br>• Matches the human's answers; the earlier-decision section hides conflicts<br>• Never-read promise has no stated lookup before the read; ticket 06's add takes link plus text<br>• Ticket 02's re-summarize rule is changed but not listed<br>• Two unasked choices are unmarked; image reading has no model role | 164 s · 19 tools · 541k tokens · wait 3 s |
| 3 | B | later | 97112eb8 | edit<br>• The working changes to ticket 02 and 06 flags are right and match the human's answers<br>• Open build details are not passed on, so the spec route could lose them<br>• Adds the pre-read lookup, Jev flag settings and image handling to Passed on | 59 s · 1 tool · 109k tokens |
| 4 | A | later | 67544364 | accept<br>• Accepts the proposal with both conflict flags and the longer spec hand-off list<br>• The edits agree with each other and with the human's confirmed answers | 7 s · 1 tool · 104k tokens |
| 5 | apply | — | 67544364 | applied | — |
| 6 | cleanup | — | — | A, B disposed (observed exit) | — |

## Final proposal

**Proposal**

- **Summary**
  
  - Key: the reader's redirected link; every other link that led there is kept and matches
  - Cleanup: safe generic rules, a tested per-site table, redirects and text joins as safety net
  - Page text stored; same or ≥90%-same text joins with no summary; Jev flags copies after add
  - No automatic re-reads; one combined re-read offer past 30 days; code-checked minimal updates
  - Unclear scope (repo items, video, images, link pages) stops with options; clear pages never stop
  
  **Details**
  
  ## Decide source identity
  
  A source is keyed by the link the reader reports after redirects, and every other link that led there is kept with it. Links are cleaned by safe generic rules plus a small per-site table, with redirects and text matching as the safety net, so a missed rule costs one page read and never a summary. Atlas keeps the cleaned page text, so it can tell in code that a page is identical, nearly identical or changed, and skip or limit model work. Atlas stops only when a page's scope is unclear.
  
  Records: [interview, every question as shown and the user's exact answers](../reviews/12-interview.md). Settled by grilling over three rounds on 2026-11-08. Items marked "(Main)" were not asked.
  
  ### 1. Key and links
  
  1. The key is the cleaned link the reader reports after redirects; when it reports none, the cleaned given link. Every other cleaned link that led to the source is kept with it, and `ask`, `find` and `add` match any of them. Replies show the key link.
  2. A later re-read that reports a new redirected link keeps the key and adds the new link (Main).
  3. A GitHub link pinned to a commit and a branch link are different sources: a snapshot and a live page (Main). Identical text still joins them (section 3).
  
  ### 2. Link cleanup, in three layers
  
  1. Generic rules that never change the page: v1's (scheme and host case, IDNA, default port, fragment, trailing `/`, `utm_*`) plus known tracking parameters (`fbclid`, `gclid`, `igshid`, `mc_cid`, `mc_eid`). Unknown parameters are kept.
  2. A site table, one tested row per site: X (`twitter.com` alias, `s=`, handle case, `/photo/N`, `/video/N`), GitHub (owner and repo case, `ref`), YouTube (`si`, `feature`, short link). The same table marks sources that cannot change (an X post, a GitHub file pinned to a commit, a versioned arXiv paper).
  3. Safety net: the reader's redirected link and the text joins in section 3 catch what the rules miss.
  4. No blanket `www.` or http→https rule: redirects handle them on most sites, and the text joins catch the rest.
  5. v1's `atlas_url.py` is kept and refactored into the generic rules plus the site table (Main).
  
  ### 3. Repeats, near-copies and updates
  
  1. Content hash: SHA-256 of the cleaned page text: the reader's header lines removed; line endings, Unicode (NFC) and whitespace runs normalized; the reader's counter lines removed (GitHub `Stars · Forks · Issues`, X `Likes · Reposts · … · Views`). For X it covers the post plus the author's own replies and leaves out other people's replies.
  2. Atlas keeps the cleaned page text, compressed and unsearched, beside the summary. Search still reads only the summary.
  3. Same text under a new link: `add` reports "already stored as <link>", keeps the new link with that source, and does not summarize. Deterministic; no model, no confirm.
  4. Nearly the same text (90% or more, compared in code against stored page text; no model): joined the same way without a summary, reported with the share that matches. Next offers "store it separately instead".
  5. Below 90%: summarized as a new source. After `add` stores it, Atlas takes the 5 closest stored sources by BM25 on title and abstract, and Jev flags any that look like the same work (a repost, mirror, renamed repo or copy elsewhere): "may be a copy of <link>". Nothing is merged or dropped; the user may archive one with `archive`.
  6. A link already stored is never read again on its own. `add` reports "already stored, last read <date>".
  7. Re-read offer: replies show each source's last-read date where they already show its date. Next offers one combined re-read line only when sources the reply relies on (in `add`, `ask`, or the dev-research rule) were last read over 30 days ago, never counting sources the site table marks as unchangeable.
  8. A re-read that finds a changed page: Atlas compares stored and new text in code. If no passage a claim cites has changed and the page gained less than 5% new text, it records the new hash and read date, keeps the summary, and reports "re-read, no meaningful change". Otherwise the old summary and the changed parts go to the update method of [Decide source summarization method](16-decide-source-summarization-method.md), which revises only the affected claims. Topics citing the source are flagged only when a claim changed.
  9. The 30-day, 90% and 5% limits are settings with these defaults (Main).
  10. One `add` batch handles links that resolve to the same source once (Main). An archived source's link reports "archived <date>" with Next: restore; it is not read or summarized (Main).
  
  ### 4. Unclear scope
  
  1. `add` gains a "pick scope" outcome, extending ticket 06's "a page of links". Atlas detects it in code from the reader's `Method` line and simple counts; nothing is summarized until the user picks, and the choice is kept so a re-add does not ask again. Next carries options that fit Atlas:
     - a repo holding several separate items (2 or more skills, plugins or packages, from its full file list): the repo as one source, each item as its own source (N found), or both, with the items linked to the repo;
     - a video: summarize from the transcript, or skip;
     - an image, or a page that is mostly images: read the images with a model, or skip;
     - a page that mostly lists links: this page, or each link (N).
  2. Clear pages never stop. An X post is summarized right away: Atlas keeps the post plus the author's own replies, by handle, and drops other people's replies; the summarizing model keeps only the author replies that continue the post. A post with no such replies is an ordinary post.
  3. The agent may also stop on its own judgment for any other unclear page, with Next options.
  4. An item picked from a repo is keyed by its own link and records the repo as a related link (Main).
  
  ### Changes to earlier decisions
  
  - [Define Atlas v2 requirements](02-define-atlas-v2-requirements.md): the stored record gains the cleaned page text (compressed, unsearched), the source's other links and its scope choice. A changed page is no longer "re-summarized": the check in code and the claim-level update in section 3 item 8 replace that, and "topics that cite it are flagged" becomes "flagged when a claim changed". Accepted input gains images, read by a model after the user picks that option.
  - [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md): `add`'s outcomes gain "pick scope" (which absorbs "a page of links"), "already stored as <link>" for joins, and "re-read, no meaningful change". "Atlas normalizes the link (v1's `atlas_url.py`)" becomes the three-layer cleanup above. In its section 6 item 1, the agent reads each page and then gives `add` the link plus the text. That changes: a stored link is matched before any read and is never read again (section 3 item 6). A re-add no longer compares the hash or updates the source; only a re-read the user accepts does.
  
  ### Rejected alternatives
  
  - Key on the link as given (v1): a moved or redirected page becomes a second source.
  - Blanket `www.` and http→https folding: can merge two different pages on the rare site where they differ; redirects and the text joins already catch these.
  - Hashing the exact text (v1): counters and new replies make GitHub and X re-adds look changed.
  - Storing a same-text link separately, or summarizing near-copies: spends a summary on content already stored. Asking before summarizing: a stop in the middle of a batch.
  - A merge step for Jev's near-duplicate flags: an eleventh command; `archive` already covers it.
  - Re-reading known links on their own (always, or past 30 days): puts whole pages into the calling agent's context. Re-read offers on every re-add: noisy.
  - Hash only, without page text: changed pages summarized again from scratch, near-copies caught only after summarizing.
  - A model update on every change, or summarizing again from scratch: spends model calls on changes no claim depends on.
  - Scope by agent judgment only: varies by agent and model, and a later scheduled fetcher has no agent to stop.
  
  ### Passed on
  
  - To [Decide source summarization method](16-decide-source-summarization-method.md): the update method (revise only the claims affected by the changed parts); claim locators that point at the stored page text, which the change check in section 3 item 8 relies on; choosing which author replies continue an X post; and, as evidence for its token-cost aim, the page text reaches `add` through the calling agent's context today.
  - To the spec route: the repo's full file list (the reader shows only top-level files), the text-similarity method behind the 90% check, checking the three default limits against v1's known duplicate pairs, how the agent looks up a stored link before reading it (a link-only `add`, or `find` or `ask` by link; section 3 item 6 needs it), the threshold, probability record and not-set-up case of Jev's copy flags, which model reads images, and what an image source stores as page text and hash.
  

**Changes**

- Changes to earlier decisions name the claim-level update that replaces full re-summaries
- They also name the new add flow: stored links are matched before any read, re-adds never update
- Passes to the spec the pre-read lookup, Jev flag settings and how images are read and stored
- Summary: unchanged · Details: edited

## Diff

```diff
--- original
+++ final
@@ -54,8 +54,8 @@
 
 ### Changes to earlier decisions
 
-- [Define Atlas v2 requirements](02-define-atlas-v2-requirements.md): the stored record gains the cleaned page text (compressed, unsearched), the source's other links and its scope choice. "Topics that cite it are flagged" on a changed page becomes "flagged when a claim changed". Accepted input gains images, read by a model after the user picks that option.
-- [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md): `add`'s outcomes gain "pick scope" (which absorbs "a page of links"), "already stored as <link>" for joins, and "re-read, no meaningful change". "Atlas normalizes the link (v1's `atlas_url.py`)" becomes the three-layer cleanup above.
+- [Define Atlas v2 requirements](02-define-atlas-v2-requirements.md): the stored record gains the cleaned page text (compressed, unsearched), the source's other links and its scope choice. A changed page is no longer "re-summarized": the check in code and the claim-level update in section 3 item 8 replace that, and "topics that cite it are flagged" becomes "flagged when a claim changed". Accepted input gains images, read by a model after the user picks that option.
+- [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md): `add`'s outcomes gain "pick scope" (which absorbs "a page of links"), "already stored as <link>" for joins, and "re-read, no meaningful change". "Atlas normalizes the link (v1's `atlas_url.py`)" becomes the three-layer cleanup above. In its section 6 item 1, the agent reads each page and then gives `add` the link plus the text. That changes: a stored link is matched before any read and is never read again (section 3 item 6). A re-add no longer compares the hash or updates the source; only a re-read the user accepts does.
 
 ### Rejected alternatives
 
@@ -72,4 +72,4 @@
 ### Passed on
 
 - To [Decide source summarization method](16-decide-source-summarization-method.md): the update method (revise only the claims affected by the changed parts); claim locators that point at the stored page text, which the change check in section 3 item 8 relies on; choosing which author replies continue an X post; and, as evidence for its token-cost aim, the page text reaches `add` through the calling agent's context today.
-- To the spec route: the repo's full file list (the reader shows only top-level files), the text-similarity method behind the 90% check, and checking the three default limits against v1's known duplicate pairs.
+- To the spec route: the repo's full file list (the reader shows only top-level files), the text-similarity method behind the 90% check, checking the three default limits against v1's known duplicate pairs, how the agent looks up a stored link before reading it (a link-only `add`, or `find` or `ask` by link; section 3 item 6 needs it), the threshold, probability record and not-set-up case of Jev's copy flags, which model reads images, and what an image source stores as page text and hash.
```

## Spend

| Reviewer | Model | Tokens | Cost |
|---|---|---|---|
| A | anthropic/claude-opus-5-5 · medium | 711,342 | 1.226747 USD |
| B | anthropic/claude-sonnet-5-5 · high | 650,543 | 0.74523 USD |
| Total | | 1,361,885 | 1.971977 USD |
