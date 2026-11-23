# ADR 0008: Host-neutral core behind ports

Status: ACTIVE

## Context

Atlas v2 is an omp plugin, and omp is its only host: pages come from `omp read`, model roles from `omp auth-gateway stdio`, and rate windows from the gateway's usage report. The judge, Jev, is a separate service reached through OpenRouter Decisions. The obvious build calls these directly from the code that summarizes, searches and answers. The user set a standing decision instead: Atlas's framework and shared core stay generic and host- and repo-agnostic, and omp is one adapter.

## Decision

- Core (`skills/atlas-ask/atlas/core/`) names no host, repo or host setting; the words `omp`, `openrouter`, `typesafe` and `modelRoles` never appear there. It imports only `atlas/ports.py` and the store interface, never an adapter or the composition root.
- Four ports carry everything host-shaped: read (a page as host-neutral facts), call (a model role, with usage and cost), judge (optional) and quota (optional), plus the optional host facts capability (roles, role fix lines, host version, and each role's provider and context). Every optional seam has one fixed fallback when absent.
- OMP and Jev are adapters under `atlas/adapters/`; `atlas/host.py` is the only module that picks them. Another host joins by adding adapters, not by changing core.
- One contract suite in `tests/contract/` holds one case class per port, and every adapter binds it: the fake host offline, the real adapters against recorded output offline and live on request. Core tests run on the fake host.
- The Reconcile cross-check is a front-door capability, not a CLI port: `atlas-ask` runs it and passes the review in. Without it, a save goes ahead marked "not cross-checked: <reason>".

## Consequences

Atlas carries one more layer than calling omp directly: every host fact crosses a port shape, and each adapter must pass the shared suite. In return, core behavior is tested without a host, a host change shows up as a failing adapter test rather than a core bug, and a later host joins by adapter. Host syntax such as role-config lines reaches the user only through host facts, so no skill hard-codes it.

## Rejected alternatives

- Calling omp from core: every rule would be tied to one host. Reopen when: the user drops the standing decision that Atlas's core stays host- and repo-agnostic.
- Letting the calling agent read pages and do the model work: every page would sit in the main model's context at its price, and automation would need a rewrite. Reopen when: page text in the calling agent's context costs no more than Atlas's own summary call, and Atlas no longer needs to run without an agent in front of it.
