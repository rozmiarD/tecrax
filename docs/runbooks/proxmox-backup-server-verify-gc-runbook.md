# Proxmox Backup Server verification and garbage-collection runbook

This runbook covers the operator-owned lifecycle for scheduled PBS verification
and garbage collection after backup and restore proofs exist.

It keeps verification, retention and space reclamation as separate claims. Its
mere existence does not authorize a live schedule or add an active Tecrax backup
connector.

## Scope

The gate covers:

- preflight of PBS identity, datastore state and running tasks;
- one bounded weekly verification job;
- a non-overlapping garbage-collection schedule;
- first manual verification proof;
- explicit approval and first manual garbage-collection proof;
- configuration rollback and public-safe sign-off.

It does not define retention, prune snapshots, prove restore readiness, configure
external-copy protection, publish raw task logs or complete Zabbix/GLPI failure
routing.

## Public and Private Boundary

Safe in public docs and sign-offs:

- PBS and datastore aliases when non-sensitive;
- schedule class and bounded worker settings;
- counts of checked groups and errors;
- task result class such as `TASK OK`;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- addresses, machine identifiers and repository URLs;
- exact backup paths, namespaces and workload inventory;
- task UPIDs and raw logs;
- reclaimed byte/chunk details tied to the live datastore;
- credentials, API tokens and encryption keys.

## Safety Model

Verification is read-intensive but non-destructive. Keep the first scheduled job
bounded to one datastore, one read thread and two verification threads. Ignore
recently verified snapshots and treat verification older than 30 days as due.

Garbage collection is deletion-class work because it can permanently remove
unreferenced chunks. Its schedule may be configured during this gate, but the
schedule mutation requires explicit operator approval and the first manual run
requires separate approval immediately before execution. Never run it merely
because verification was scheduled.

## Procedure

### 1. Preflight

Confirm through supported PBS tooling:

- the expected PBS identity and version;
- the intended datastore exists, is mounted and is writable;
- no backup, restore, prune, sync, verify or garbage-collection task is active;
- recent backup and restore-proof results remain available;
- free space is sufficient for normal operation during the gate.

Stop on an unexpected host, datastore, task or degraded mount.

### 2. Preserve configuration

Back up the current verification-job and datastore scheduling configuration to
private operator evidence before mutation. Record checksums and permissions
without copying configuration contents into Git or chat.

Use the canonical PBS configuration names reported by the installed version.
Fail closed if the backup source name, checksum target or restore path does not
match exactly.

### 3. Configure bounded verification

Create or update one clearly named weekly verification job with:

- the intended datastore only;
- a weekly off-hours schedule;
- one read thread;
- two verification threads;
- already verified snapshots ignored;
- snapshots older than 30 days eligible for re-verification.

Perform the change outside the configured run window and immediately read the
rendered configuration back. Roll back before that window if any value differs
from the intended settings.

### 4. Configure non-overlapping garbage collection

After explicit approval for this deletion-class schedule mutation, configure
garbage collection for a separate off-hours window after the weekly verification
window. Allow enough separation that a slow verification cannot normally
overlap it.

Scheduling garbage collection does not authorize an immediate manual run and
does not replace retention or prune policy.

### 5. Prove verification

Start one manual verification through supported PBS tooling and monitor its exact
task identifier privately until completion.

The verification gate passes only when:

- the task ends with `TASK OK`;
- all selected groups complete;
- progress reaches 100 percent;
- the error count is zero;
- datastore and PBS services remain healthy.

Do not proceed to the first manual garbage collection after a failed, partial or
unobserved verification.

### 6. Approve and prove garbage collection

Immediately before the first manual garbage-collection run, present the target
datastore, preceding verification result and rollback limitation to the operator
and obtain explicit approval.

Start one manual run and monitor its exact task identifier privately. The gate
passes only when the task ends successfully, pending removals are zero, bad
chunks are zero and the datastore remains healthy.

Configuration can be rolled back, but chunks already removed by a completed
garbage-collection task cannot be restored by configuration rollback. Recovery
depends on valid remaining backups or a separately proven external copy.

### 7. Validate schedules and rollback

Read back both schedules and confirm they do not overlap. Validate that the next
run times match the intended maintenance windows.

If configuration validation fails before a task starts, restore the preserved
configuration and reload PBS through supported tooling. If a task has already
started, do not edit configuration underneath it; monitor or stop it only using
supported PBS task controls and record the result privately.

## Stop Conditions

Stop if any of these are true:

- host identity or datastore target is ambiguous;
- a conflicting datastore task is active;
- configuration backup or checksum validation fails;
- the verification job is unbounded or overlaps garbage collection;
- verification does not finish with 100 percent, zero errors and `TASK OK`;
- immediate approval for manual garbage collection is absent;
- the datastore reports pending removals, bad chunks or degraded health after
  garbage collection;
- success can be claimed only by publishing raw private task logs.

## Sign-Off Shape

Use `../operator-signoff-template.md` and include:

- date;
- generic PBS and datastore aliases;
- run class: `pbs-verify-gc`;
- verification schedule and worker-limit summary;
- verified-group count, progress, error count and result class;
- garbage-collection schedule and bounded result class;
- rollback/configuration-backup result;
- explicit non-claims.

Non-claims:

- no restore readiness beyond a separate restore proof;
- no external disaster recovery beyond a separate external-copy proof;
- no complete retention or prune policy;
- no automatic deletion authorization from this runbook;
- no Zabbix/GLPI failure visibility until separately implemented and proven;
- no NIS2/KSC2 compliance-readiness claim.

## Next Gate

Route failed verification and garbage-collection outcomes into the established
monitoring and GLPI workflow without exposing raw backup metadata. That
integration remains a separate gate with its own canary and duplicate proof.
