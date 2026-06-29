# Tecrax

Tecrax is a governed infrastructure-operations profile for RExecOp, using
GovEngine governance and SCLite artifact truth.

Current source line: `tecrax==0.3.9a0`, depending on
`govengine==0.16.5`, `sclite-core==1.0.8`, and `rexecop==0.2.11a0`.
Latest published PyPI baseline: `tecrax==0.3.8a0`; it contains the coordinated
B2 dependency floor and read-only policy vector.

This package provides:

- **RExecOp domain profile** — bundled YAML profile with intents, workflows, connectors,
  and validation rules (entry point `rexecop.profiles:tecrax`).
- **Local fixture review** — dry-run proof slice without live infrastructure.
- **Read-only host inventory profile** — fixed SSH command shapes and bounded
  normalization for operator-configured Ubuntu inventory, with a sanitized
  GovEngine B2 policy-control example for receipt, digest, timeout, step and output bounds.
- **Verified read-only service slices** — NTP synchronization and Docker systemd service
  health over fixed SSH commands, plus bounded Zabbix API version health through RExecOp
  `http_api`, AdGuard DNS/login reachability, and unauthenticated Portainer status through
  verified TLS.
- **Read-only network device inventory slice** — bounded legacy CLI inventory through an
  operator-managed local wrapper; target addresses, keys and wrapper implementation stay
  outside the repository.
- **Bounded chrony/NTP mutation slice** — the first deterministic `apply`
  operation, limited to a single managed chrony server config and admitted before
  execution.
- **Monitoring-host reaction pack** — deterministic domain findings map only to
  existing read-only intents; unknown states escalate without a free-form action.
- **Bounded escalation proposal vectors** — `diagnose_monitoring_host` facts can be
  projected into untrusted SCLite proposal artifacts that never grant execution.
- **Source-line trigger rules** — bounded `network.host_observed` events can map a
  known catalog target to `collect_basic_host_inventory` planning, while unknown hosts
  escalate without execution.
- **Operator catalog metadata** — target kinds, required capabilities, side-effect
  classes, validation references and runbook references projected by RExecOp from
  the profile; sanitized target-catalog example included.

It does not manage credentials or accept arbitrary infrastructure commands. Live SSH
execution is performed by RExecOp only from explicit operator configuration outside
this package. The active mutation surface is limited to the governed chrony/NTP
server slice.

Stack ownership:

```text
Tecrax profile -> RExecOp plan -> GovEngine admission -> RExecOp execution -> SCLite evidence
```

- SCLite owns canonical evidence, receipts and review artifacts.
- GovEngine owns governance, PolicyEngine and admission decisions.
- RExecOp owns domain-neutral lifecycle, execution and deterministic reaction mechanics.
- Tecrax owns infrastructure intent, connector, normalization, validation and runbook semantics.

## RExecOp profile

Install the coordinated published line to register the current domain profile:

```bash
pip install "tecrax==0.3.8a0"
tecrax status
```

For an explicit cross-stack pin, `pip install "rexecop[tecrax]==0.2.11a0"`
resolves the same coordinated release line.

The profile root is exposed via `tecrax:profile_root` (directory `src/tecrax/profile/`).
For network devices, see `docs/network-device-readonly-runbook.md`; real target
configuration and legacy SSH compatibility wrappers stay outside this repository.
For the fresh Proxmox host deployment baseline, see
`docs/proxmox-host-readiness-runbook.md`; it is an operator-owned readiness
procedure, not an active Tecrax intent.
For the private live-run substrate used by Proxmox deployment, see
`docs/admin-tools-substrate-runbook.md`; it defines wrapper, environment,
runtime and sign-off boundaries without storing private topology in Git.
For local backup planning, see `docs/proxmox-backup-server-readiness-runbook.md`;
it defines PBS readiness gates and keeps backup-job success, restore proof and
external-copy coverage as separate claims.

## Target and operation catalog

Tecrax intent files contain profile-owned operator catalog metadata. RExecOp derives
the operation list from those same intent and workflow files; there is no second
manually maintained operation registry.

Use the sanitized template in `examples/catalogs/targets.readonly.example.yaml` as
the shape for an operator-owned catalog outside Git:

```bash
rexecop targets list --catalog /path/outside/repo/targets.yaml
rexecop operations list --catalog /path/outside/repo/targets.yaml \
  --target monitoring-host-01
```

An `admission_required` result means only that target kind, capabilities and
connectors match. GovEngine still decides whether a concrete plan may execute.
See `docs/operation-catalog.md`.

## Deterministic reactions

Tecrax owns the monitoring vocabulary and rules in
`src/tecrax/profile/reactions/reaction_pack.yaml`. Build a canonical observation
from a bounded `diagnose_monitoring_host` result, then pass it to RExecOp:

```bash
tecrax reaction-observation \
  --input diagnosis.json \
  --operation op-source \
  --target monitoring-host-01 > observation.json

rexecop reaction-plan \
  --profile tecrax \
  --env /path/outside/repo/environment.yaml \
  --observation observation.json \
  --target monitoring-host-01
```

The first reaction release is deliberately read-only. It can re-run bounded host inventory,
NTP, Docker service, Zabbix, AdGuard, Portainer, or network device inventory checks; a
healthy observation is `no_op`, and an unclassified state is `escalate`. RExecOp owns
deterministic mechanics and lifecycle, GovEngine owns admission, and SCLite owns the
evidence chain.
For operator review, Tecrax can also build a bounded untrusted escalation proposal from
the diagnosis facts. Validate it with `rexecop reaction-proposal-validate`; a valid proposal
still has `may_execute=false` and requires GovEngine admission before any future follow-up.
See `docs/escalation-proposal-vectors.md`.

## Trigger rules

Tecrax declares domain trigger mappings in
`src/tecrax/profile/triggers/trigger_rules.yaml`. The initial source-line rule family
handles bounded `network.host_observed` events: a known host subject maps to a dry-run
`collect_basic_host_inventory` plan through an operator-owned target catalog; an unknown
host escalates and does not execute anything. RExecOp owns event intake, dedupe,
cooldown and planning mechanics. See `docs/trigger-rules.md`.

## Local fixture proof

```bash
tecrax fixture-review --service demo-web
```

The command emits a public-safe fixture review payload. It uses GovEngine
profile/planning/supervision/runtime-review contracts and binds its fixture
receipt through an SCLite artifact descriptor. It has no live runner, host
inventory, credential path, or infrastructure adapter.

The source `0.3.9-alpha` line combines the profile-owned read-only reaction pack,
B2 policy vector, and the first governed chrony/NTP apply slice over RExecOp
`0.2.11a0`, GovEngine `0.16.5`, and SCLite `1.0.8`. It does not add a second
policy engine, lifecycle runner, or truth layer.

The Ubuntu environment example uses profile-owned policy semantics, but GovEngine
compiles and admits the controls and RExecOp enforces them. Tecrax does not claim
that writing obligations in YAML alone satisfies them.

`configure_chrony_ntp_server` is the only active mutating intent. It is deterministic,
requires GovEngine admission, uses the `tecrax_chrony_ntp` connector backend, and is
documented in `docs/chrony-ntp-server-mutation-runbook.md`.

## Validation

```bash
python scripts/validate_public_truth.py
python scripts/validate_active_profile.py
python scripts/validate_secret_topology.py
python -m pytest -q
```

The validator keeps domain semantics in Tecrax and lifecycle/execution in
RExecOp. Any future mutation, credential, scheduler, discovery, or
carrier-adapter claim must be backed by code and tests before it becomes public
truth.
