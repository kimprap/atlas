# ADR 0009: The CLI decides every stop

## Status

Accepted; amended 2026-11-11 after stage 7 (the `version_save` id and the approvals rows that `topic nothing_to_save` and `plan mark` do not write).

## Context

Several Atlas steps must wait for the user: confirms for changes, the monthly spend cap, rate-window limits, choosing a scope for a large page, a failed summary, judge setup, and saving a topic version. An earlier design let the CLI reply only done, failed, bad input or not set up, and left the confirm policy, including which changes skip their confirm, in the front-door skill's prose, so every new host's front door would have to copy it. Separately, a confirm on every change by default asked a second time after the user had already said "add these links".

## Decision

- Every stop is one reply outcome: exit 4 with a non-empty `decisions` list. Each decision has a kind, a question and options whose `then` is typed (`resend` with body fields, `skill: atlas-init`, or `stop`), so any front door follows it without Atlas policy.
- A decision id binds to its change: a hash over the command, flags, the body without `approval`, and the kind; a `version_save` id also leaves out `review`, because Reconcile runs after the decision is returned and the front door adds the review on the resend. A resend carrying a different decision's id is bad input.
- The CLI enforces the profile's `confirm.<change>` settings (`always` by default, or `never`). The front door holds no confirm policy; it passes approvals and shows decisions.
- A change command takes `approval` with `by: "request"` (the user's own message asked for this change) or `by: "confirm"` (the user's answer to a returned decision). Agent proposals never travel as `request`. Under `always`, a `request` runs the change only when it is not paid at scale and every target it names (each link, each topic name, a note's `who`) appears in the words; otherwise the CLI returns a confirm.
- Fixed stops return a decision whatever the setting: version save, pick scope, summary failed, judge setup, and cap and window yields. A confirm and a cap or window yield on the same command merge into one decision, so no command stops twice.
- Every applied change writes one `approvals` row with the change kind, `by`, the words and the decision id. Steps with no stop write none: `topic nothing_to_save` (the user's pick of its Next line is its confirm) and `plan mark`.

## Consequences

The caller is trusted to label `request` honestly. The words check guards against acting on a vague "yes, add it"; it is not authentication. A wrong `request` runs a change the user did not ask for, and its `approvals` row keeps the words for audit. In return, any host's front door gets the same stops and settings without copying policy, and a change the user asked for in so many words needs no second confirm. Rejected: confirm policy in skill prose (each front door must copy it); a confirm on every change (asks twice after a plain request).
