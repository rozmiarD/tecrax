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
registered mutation candidate and Tecrax is not mutation_ready; execution, post-state
validation, rollback, target locking and SCLite evidence are separately unqualified.
