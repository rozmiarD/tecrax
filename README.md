# Tecrax

Tecrax is a governed infrastructure-operations runtime/profile built on GovEngine and SCLite.

Current published baseline: `tecrax==0.3.3a0` ([PyPI](https://pypi.org/project/tecrax/0.3.3a0/)), depending on
`govengine>=0.15.0,<0.16`, `sclite-core>=1.0.1,<1.1`, and `rexecop>=0.2.4a0,<0.3`.

This package provides:

- **RExecOp domain profile** — bundled YAML profile with intents, workflows, connectors,
  and validation rules (entry point `rexecop.profiles:tecrax`).
- **Local fixture review** — dry-run proof slice without live infrastructure.
- **Read-only host inventory profile** — fixed SSH command shapes and bounded
  normalization for operator-configured Ubuntu inventory.
- **Verified read-only service slices** — NTP synchronization over fixed SSH commands
  and bounded Zabbix API version health through RExecOp `http_api`.

It does not execute infrastructure changes or manage credentials. Live SSH execution
is performed by RExecOp only from explicit operator configuration outside this package.

Planned foundation:

```text
Tecrax -> GovEngine -> SCLite
```

- SCLite owns lifecycle/proof/review artifacts.
- GovEngine owns deterministic governed-runtime kernel mechanics.
- Tecrax owns the infrastructure-operations profile semantics, fixture review
  payloads, UX, and future host integrations when those boundaries are mature.

## RExecOp profile

Install `tecrax` alongside `rexecop` to register the domain profile:

```bash
pip install rexecop tecrax
rexecop profile list
```

The profile root is exposed via `tecrax:profile_root` (directory `src/tecrax/profile/`).

## Local fixture proof

```bash
tecrax fixture-review --service demo-web
```

The command emits a public-safe fixture review payload. It uses GovEngine
profile/planning/supervision/runtime-review contracts and binds its fixture
receipt through an SCLite artifact descriptor. It has no live runner, host
inventory, credential path, or infrastructure adapter.

The `0.3.2-alpha` line aligns dependency pins with GovEngine `0.15.0` (PolicyEngine MVP)
and RExecOp `0.2.4a0`. The `0.3.1-alpha` release consolidated the RExecOp domain profile
into this package. Neither line adds a live infrastructure runtime or a new contract
surface beyond the bundled profile.

## Validation

```bash
python scripts/validate_public_truth.py
python -m pytest -q
```

The validator keeps this package as a second-host proof surface only. Any future
infrastructure runner, inventory, credential, scheduler, or carrier-adapter
claim must be backed by code and tests before it becomes public truth.
