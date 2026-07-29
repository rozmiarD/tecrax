# Mutation entry criteria

Mutation candidates are limited to explicitly described single-action slices. Every new
candidate requires a separate architecture decision and all of the following:

- stable versioned read-only pre-state and diagnosis;
- one exact action contract and explicit side effect;
- GovEngine approval plus enforceable obligations/constraints and operator confirmation;
- post-state validation and feasible rollback or compensation;
- target lock, idempotency, bounded retry and lockout prevention;
- SCLite evidence chain and no-backend-before-admission tests;
- no unattended apply and no direct LLM execution.

Failure of any gate keeps the action outside executable runtime authority. The default
RExecOp posture is `stable_read_only`, which blocks apply before connector I/O; Tecrax is
not mutation_ready. This document is criteria, not a deployer design or implementation
backlog.

## First candidate: Proxmox chrony/NTP server

The first registered mutation candidate for a future read-only-boundary decision is a
bounded chrony/NTP server configuration on a freshly installed host.

Before live execution, `docs/proxmox-access-handoff.md` must be complete. In
particular, the target host identity must be verified as fresh, access must use
the `rexecop` account, and all real target bindings, keys and known-hosts files
must remain outside Git.

The candidate operation must not widen into generic Proxmox administration. It may only
describe the exact NTP server state transition declared by the profile. GovEngine
admission does not override default RExecOp `stable_read_only`, so it remains a
registered mutation candidate and Tecrax is not mutation_ready. Live execution,
live post-state validation, live rollback, crash recovery and worker recovery remain
unqualified; the narrow source-pinned fixture recovery proof is described below.

The Chrony connector delegates process execution to RExecOp's incrementally
bounded runtime capture. Its exact configured default is `16384` combined
stdout-plus-stderr bytes, and an exact positive integer request control can
only lower that bound. Overflow is an unsuccessful, raw-free result containing
only the effective limit, per-stream SHA-256 digests, truncation flags and
observed byte counts; timeout evidence also excludes raw or partial output.
This proves a local resource boundary, not live wrapper behavior or mutation
readiness. It does not claim bytes the child did not emit.

Automatic retry is disabled for this mixed read/apply mutation candidate:
F-017 profile alignment is covered by a zero automatic-retry budget without an
allowlist expansion. A post-I/O `outcome_indeterminate` result requires
reconciliation, and RExecOp intrinsically blocks manual retry of that
indeterminate operation independently of the profile budget.

T-205 now qualifies one source-pinned, deterministic fixture-only recovery path.
The profile declares exact fixture and operator-wrapper postures, while the public
environment selects `fixture_only` with no wrapper. An authority-owned GovEngine
v0.2 policy and signed decision bind only backend `tecrax_chrony_ntp` and egress
`no_network`; RExecOp owns the fresh recovery child, attempt, lease, claim, permit,
connector dispatch and conformant receipt. Repeating recovery reuses the completed
child without new authority or I/O. The actual plugin factory creates four distinct
backends for pre-read, apply, post-read and recovery. A Tecrax-owned, lock-guarded
process registry carries only the fixture's boolean applied state across those fresh
instances, isolated by connector, target and normalized subnet, and removes entries
when they return to the configured default.

This local proof does not make Tecrax mutation_ready and does not qualify the
operator wrapper, subprocess or network isolation, live or lab infrastructure,
exactly-once I/O, restart or multiprocess continuity, crash/power-loss or worker
recovery, release or publication. The registry is not SCLite truth, a receipt store
or RExecOp lifecycle persistence. The
production package now pins the exact public `rexecop==1.0.0rc1` artifact and its
normal installed graph is resolvable. That public artifact predates the latest
same-version source-head T-205 remediation, so installed-graph success does not claim
the source-only governed surface, mutation readiness, release or publication.
