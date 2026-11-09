# Model-call path and Jev claim support: evidence for ticket 16 (scout report, 2026-11-09)

Read-only survey of `omp auth-gateway stdio`, reachable models and prices, and Jev's claim-support recipe. Agent output kept as evidence; not a decision. Added by the session: `omp read <url>` (omp v18.18.0) prints the reader's output for a URL from a shell, with the `URL:`/`Method:` header (probe on the map's seed link, 38,987 bytes, 12 s).

**Method note.** No bash tool was available, so no command outputs exist for `--help` or `omp models`. What follows comes from docs, source and config.

## 1. `omp auth-gateway stdio`
**Protocol** (omp://auth-broker-gateway.md `### stdio`; stdio.ts header):
- Request line: `{"id":1,"path":"/v1/chat/completions","body":{"model":"@smol","messages":[...]}}`.
- First output line: `{"ready":true,"version":...}`.
- Reply line: `{"id":1,"status":200,"body":{...}}`.
- Requests run concurrently and answer in completion order, matched by `id`. The process exits when stdin ends.
- `model` accepts a role (`@smol`), `provider/id`, a bare fuzzy name, or a comma list. On a status above 400 (other than 499) it falls through `retry.fallbackChains`. The reply's `model` names the model that answered.
- Routes served: `/v1/chat/completions`, `/v1/messages`, `/v1/responses`, `/v1/pi/stream`, `/v1/systemone`, `/v1/models`, `/v1/usage` and others.
- stdio.ts `readResponse` returns only status and body, so response headers are lost. The `x-litellm-response-cost` header (doc line ~239) never reaches Atlas. Chat replies carry token usage only (openai-chat-server.ts:486-498). Atlas would compute cost from catalog prices [INFERENCE].

**Capabilities:**
- **JSON schema / structured output: no.**
  - Chat route: `response_format` is accepted as opaque, then dropped (`server.ts:262-281`, 'auth-gateway dropped unsupported typed options', debug log only).
  - Messages route: only `output_config.effort` and `task_budget` are mapped (`anthropic-messages-server.ts:441-447`); there is no `output_config.format`.
  - OpenAI tool `strict` is 'accepted, not enforced upstream' (openai-chat-server-schema.ts:97).
- **Tool-use forcing: yes.**
  - `tools` and `tool_choice` pass on Chat (`required` or a named function) and Messages (`any` or `{type:tool,name}`); see anthropic-messages-server.ts:`mapToolChoice` and omp://toolconv/anthropic.md:134-143.
  - Anthropic forced tool choice disables or pins thinking: 'Forced choices … remove explicit thinking configuration' (toolconv/anthropic.md:143).
  - The usual substitute for a JSON schema is therefore one forced tool whose `input_schema` is the record shape [INFERENCE].
- **System prompts: yes.** Chat `system` and developer messages; Messages `system` (`buildSystemPrompt`).
- **Prompt caching: partly.**
  - Messages: `cache_control` on blocks is scanned and the strongest TTL becomes `cacheRetention` (`anthropic-messages-server.ts:273-316`). The Anthropic provider then places breakpoints itself.
  - Chat: explicit `prompt_cache_options` and `prompt_cache_breakpoint` are rejected (`openai-chat-server.ts:47-50`).
  - A derived prompt-cache key is set automatically (`server.ts:236-242`).
  - Usage reports `cacheRead` and `cacheWrite`.
- **Thinking levels: yes.**
  - Chat `reasoning_effort` (`none` through `max`); Messages `output_config.effort` and `thinking`.
  - `normalizeGatewayThinking` clamps an unsupported effort to the nearest supported one.
  - Thinking off is not universal. Opus 5.5 keeps adaptive thinking; Sonnet 5.5 off = `between_tools` pinned to high (behavior.kdl:1469-1477). Haiku 5.5 accepts `disabled`.
- **Document citations (cited char spans): no.** Messages `document` blocks are flattened to a text placeholder `[document: {...}]` with a warning (`anthropic-messages-server.ts:~165-172`). The inbound schema models text, image and tool_result only. Chat file and input_audio parts are dropped (openai-chat-server.ts:239). Citations are not exposed on any route [INFERENCE, from the absence in grep of both servers].

**Reachable models/providers.**
- `GET /v1/models` lists 'registry catalog filtered to providers with credentials'. I could not call it.
- `~/.omp/agent/config.yml` modelRoles:
  - default `anthropic/claude-opus-5-5:high`
  - smol `anthropic/claude-sonnet-5-5:high`
  - tiny `anthropic/claude-haiku-5-5:high`
  - web `xai-oauth/grok-4.7`
  - judge `openrouter/~typesafe/jev-latest`
- `disabledProviders: [codex]`. There are no `atlas_*` roles yet.
- So Anthropic Opus, Sonnet and Haiku (5.5) and xai-oauth are on the login. The task agents already use Sonnet 5.5 and Opus.
- Judge models are not served by the gateway here (reviews/06-interview.md:8; decision-model.md:126-129).
- Anthropic list prices per Mtok in the bundled catalog (anthropic.kdl:31-41):
  - Sonnet 5.5: in 2, out 10, cache-read 0.2, cache-write 2.5
  - Haiku 5.5: in 0.1, out 0.5, cache-read 0.01, cache-write 0.125
  - Both: 1M context, 128k max output
  - Opus 5.5 is $4 in / $20 out per cursor.kdl:268-271 and snowflake.kdl; I did not see the first-party Anthropic entry [INFERENCE that it matches].

## 2. What Jev offers for claim support
**Jev input and output** (docs.typesafe.ai/api/system-one.md; models.md; systemone-server.ts):
- Input: one `state` (string, object or array) plus named `questions` of type `noul` (yes/no), `choice` or `score`. All questions in a request see the same state and are answered independently.
- Output:
  - noul: `noul`, P(yes) in 0–1.
  - choice: `choice`, `probabilities` summing to 1, and `confidence`.
  - score: `score`, `probabilities`, and `confidence`.
  - plus `usage {input_tokens, output_tokens, cost?}` and the answering `model`.
- Limits:
  - Jev 1.14: 64k tokens per request and 32k per question, where the state counts once against each. A `TypeSafe-Danger-Zone-Long-Context: true` header raises both to 262k, 'slower and less accurate'.
  - Body at most 32 MiB.
  - Price $0.042/Mtok input, output free.
  - No cap on question count.
  - 429/529 need backoff; rate limits are per organization.
- Weaknesses (model-jaggedness.md):
  - Reads literally, so write the exact condition.
  - Weak on counting, numbers and dates.
  - Accuracy falls with irrelevant state ('Filter first; send only what the question needs').
  - Can be steered by adversarial content in state.
  - Choice option order can bias the answer.
- Via OpenRouter Decisions (web_search, openrouter.ai skills doc): `POST /api/alpha/decisions`. The example response shows `usage.cost` 0.00002 for 476 input tokens. The endpoint is alpha, so shapes may change.

**Cookbook guidance** (docs.typesafe.ai/cookbooks/citation_check.md; jev-decision-model-research S4):
- Step 1 is a normalized string match of the quote in the source. A miss means 'fabricated', with no model call.
- Step 2 is one Choice question per surviving citation over `{claim, section}`: `supports`, `contradicts` or `says_nothing`. Confidence ≥ 0.8 stands; lower goes to a human.
- On 8 planted citations (jev-1.14.0, 2026-11-03), all 4 accurate ones scored ≥0.98, and all 4 planted failures were caught. One failure (0.56) went to human review.
- Quote matching is exact after normalization, so a truncated or reworded quote reads as 'fabricated'; fuzzy matching is up to the user.
- verify_llm_outputs.md uses 3 Noul questions in one request (answerable / declines / supported). Risk ≥ 0.2 goes to review. On 1,000 questions, 88.5% of the answers were right; the check passed 73% of the answers, and 95.7% of those were right; the flagged 27% held 84 of the 115 wrong answers.
- sde_cascade.md: the cheap model extracts, Jev asks one Noul per rule, and escalation happens only when a flag fires. The cheap model's output there was schema-valid but wrong, and Jev flagged the conflict at 0.97. The cookbook recommends one narrow question per rule rather than one 'is this right?' question.
- Parallel questions (S2) batch many questions into one request for '12.2x cheaper and 10.0x faster' (the docs index says 11.8x faster).

**Atlas constraints.**
- The map says Jev may only flag, never filter.
- Jev is not reachable through `auth-gateway stdio`, so a direct OpenRouter key is needed (ticket 06 §5.3; decision-model.md:126-129).
- Ticket 16 (issues/16-...md) says the add-time claim checks belong to it.

## 3. Jev cost/latency (ticket 11, issues/11-...md)
- Rerank: about 2.2–2.7 s and about $0.001 per search, against 4.7 s and about $0.04–0.07 for Opus (Opus cost estimated from tokens [INFERENCE]). Opus `:medium` equals `:high`.
- Whole library: one yes/no over all 673 sources costs $0.03 in 11 s.
- Ticket 08 (via the research file, S10): 1,535 pairs graded for $0.10; the user agreed with 20 of 20 spot checks.
- Caveat: Jev graded 4 of the user's 6 trading sources as not relevant, a case where its judgment diverged from the user's.
- No Jev claim-support latency or cost has been measured on Atlas data; the research file (S4) only reports cookbook accuracy.
