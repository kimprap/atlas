Type: grilling
Parent: [Atlas v2 and portable skill plugins](../map.md)
Status: resolved

## Question

What must Atlas v2 do, observably? Settle the requirements for adding sources from any repository, neutral summaries with links, answers that combine several sources, followed topics with "new since last time" plus update, and organization without fixed labels. Also settle:

- **Duplicates:** re-adding a known link, with or without a tracking suffix such as X's `s=<digits>`, whose page has not changed does not summarize it again.
- **Scheduled discovery:** do followed topics get a daily search for new sources, or do they update only when asked?
- **Discovery sources:** is `last30days` (`mvanhorn/last30days-skill`; Reddit, X, Hacker News, YouTube, web) a source of new links? How it plugs in belongs to [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md).

Example workloads the requirements must cover (from [Atlas v1 notes](../inputs/atlas-v1-notes.md), notes 4 and 5):

- A topic built from a brief with several criteria and refined later (lean SEO frontend stack).
- A topic whose name and scope are agreed before it is created (TradingView technical-analysis setup).

## Answer

Settled by grilling with the user on 2026-10-19 over four rounds of questions plus two side discussions, and confirmed by the user ("approve"). Governing artifact: [the map](../map.md) and its standing decisions.

Cross-checked by Reconcile run `reconcile-20261019T090146Z-3511e2` (2 rounds, 0.99 USD). It corrected the round count. The user rejected its second change and restored "the user can set" trust notes, which matches the option the user picked.

### Scope and direction

- v2 is manual: no scheduler.
- End goal (not v2): a fully automated personal research assistant that collects new links on a schedule, updates the topics the user has agreed on, and notifies the user, first when asked, later by push. v2 must allow that without a redesign.

### Sources

- **Accepted input:** text web pages by link (articles, docs, GitHub repos/files, X posts, papers). For a video, the agent asks whether to try its transcript.
- **Unreadable pages** (paywall, login, error): the agent stops and reports; nothing is summarized. **A page that only lists other links:** the agent asks whether to summarize this page only, or each linked page.
- **When a source is summarized:** a link the user or an agent adds on purpose is summarized at once, so answers can use it. Links collected in bulk (later: by discovery) wait in an inbox, unsummarized, until reviewed.
- **Repeats:** the same link (with or without a tracking suffix such as X's `s=<digits>`) whose page is unchanged is not summarized again. A changed page is re-summarized; only the latest summary is kept, the previous date and content hash are recorded, and topics that cite it are flagged.
- **Removal:** archive on request; hidden from search and answers, kept, restorable. Agents never hard-delete.
- **Stored record** (read only by agents, never by the user):
  - Kept: link, title, author, publisher, published date, first seen, last checked, content hash, kind, how much of the page was read; claims and recommendations, each with a locator in the source; caveats; related links.
  - Dropped from the v1 shape: TL;DR (written at answer time), assessment ratings and recommended posture, domains/tags and other labels, routing notes, sequence numbers.
  - "Reuse cues" stay only if [Prototype retrieval on real summaries](08-prototype-retrieval-on-real-summaries.md) shows they help search.
  - Summaries are written from the page only, never from the asking repository's context.

### Answers

- Atlas answers from stored sources first and names what they do not cover. It fetches new sources only when research is asked for.
- v2 research uses the calling agent's web search. `last30days` is deferred to [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md); some of its lanes need API keys or browser sessions, and it matters most for later scheduled discovery.
- Three answer formats:
  - **About a source:** TL;DR, the claims that matter for the question, caveats, author and date, link.
  - **A question:** the answer first, then the claims behind it with their sources, disagreements with who says what, and gaps with an offer to research them.
  - **About a topic:** the agreed understanding with its version and date, then evidence that would change a conclusion, a count of other new sources, and a proposed revision to confirm.

### Topics

- **A topic holds** a name, a brief (scope and criteria), and the agreed understanding, kept as numbered versions. Which sources belong is found by search, not labels.
- **Versions:** new sources only produce a proposed revision; it becomes the next version when the user confirms. The agent drives the work with as few stops as possible and suggests next steps without being asked.
- **Following:** every active topic is followed. A topic can stop being followed without being archived.
- **What's new:** only new evidence that would change an agreed conclusion is shown, with who says it (e.g. rules specific and always-loaded → generic and loaded on demand). Other new sources appear as a count, listed on request. Later push notifications use the same filter.
- **Creating a topic:** the agent proposes the name, scope, brief, and a research plan (questions to answer, searches to run, stored sources to use, new sources to fetch) in one short message, then creates the topic and starts research on one confirm.
- **More research on an existing topic:** the proposal includes a research plan, the same as creation.

### Independent cross-check (Reconcile)

- Every research plan (topic creation and more research on an existing topic) is cross-checked before the user sees it.
- Every proposed revision, including a topic's first agreed understanding, is cross-checked before the user sees it.
- Never cross-checked: source summaries, read-only answers, and the inbox of collected links.
- How Atlas calls Reconcile, and how Atlas works when Reconcile is unavailable, belongs to [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md).

### Credibility (v2 minimum)

- Every source records its author and publisher.
- The user can set standing trust notes per author and subject (e.g. lean towards Matt Pocock on agent skills).
- When sources disagree, answers show who says what and which way they lean.
- Trust is re-judged over time, not fixed when a source is first seen.
- Whether and how to weight sources is a separate decision: [Decide how source credibility is weighted](09-decide-source-credibility-weighting.md). Too strict weighting causes false negatives; the user named both directions (an established company over an unknown X account, and a widely respected practitioner such as Matt Pocock over a company on his subject).

### How agents respond (all agent replies, not only Atlas)

- Concise, high-level, plain language and formatting, in the style of Reconcile and Retrace output. This governs formatting, not the content of the changes.
- **Changes** (add, research, create, revise, archive, unfollow): one short proposal with suggested next steps; the agent acts after one confirm. The user may remove these stops later when they prove redundant.
- **Read-only asks** (what's new, summarize a source or topic, questions): answered directly.

### Example workloads covered

- Lean SEO frontend stack: a topic from a multi-criteria brief, refined later.
- TradingView technical-analysis setup: a topic whose name and scope are agreed before creation.

### Rejected alternatives

- Video/audio and local files as inputs: transcripts are unreliable; local files break "every source has a public link" and complicate hosting.
- Topic as a saved search only: "new since last time" would have nothing to compare against.
- Fetching automatically from an answer: unpredictable cost and writes.
- Keeping every summary version: duplicate near-identical text in search.
- Daily, fully automatic summarizing and updating in v2: spends model budget daily and writes without review.
- Best-effort summaries of unreadable pages: weak summaries enter search.
- Hard delete: no undo.
- Showing every new source: noisy; the user called it brittle.
- Auto-updating topic conclusions: changes agreed conclusions without the user.
- Cross-checking only the revision on existing-topic research: sources the agent never looked at stay unseen.

### Unresolved, owned elsewhere

- Credibility weighting: ticket 09.
- Architecture, Reconcile integration, `last30days`: ticket 06.
- Retrieval method and whether reuse cues help: ticket 08.
- Source identity rules and quality judging: map fog.

**Later change:** [Decide source identity](12-decide-source-identity.md) (2026-11-08): the stored record gains the cleaned page text (compressed, unsearched), the source's other links and its scope choice. A changed page is no longer re-summarized: identity's check in code and the claim-level update replace that, and topics that cite it are flagged only when a claim changed. Accepted input gains images, read by a model after the user picks that option.

**Later change:** [Decide source summarization method](16-decide-source-summarization-method.md) (2026-11-09): in the stored record, each claim gains its quote, the quote's position and a basis tag, and each record gains its summary history (model, escalation, rubric version, rethink line, dropped-claim count, and Jev flags with the Jev model version).

**Later change:** [Prototype summary model quality vs cost](15-prototype-summary-model-quality-vs-cost.md) (2026-11-09): in the stored record, as changed by [Decide source summarization method](16-decide-source-summarization-method.md), each claim holds a list of 1–3 quotes and their positions instead of one quote and one position.

**Later change:** [Decide v2 additions](17-decide-v2-additions.md) (2026-11-09): the stops the user may remove later become per-profile `confirm.<change>` settings; version saves, cap and window yields, and decision stops always stop. What's-new offers "nothing to save" in Next, and a catch-up across followed topics is the manual step towards the end goal. A saved topic version keeps copies of the claims it cites. From 80% of a set monthly cap, a paid read-only ask yields first.

**Later change:** [Final map review](../reviews/final-reconcile-record.md) (2026-11-09, the user's choice "Your words approve"): a change the user asked for in so many words ("Add these links", "Summarize this link") runs on that request, as Reconcile already takes the user's words as approval. Changes the agent proposes (research-end source adds, notes and tally proposals, plan starts, version saves) and paid-at-scale ones (a redo, a batch of links) keep their one confirm.
