# Tecrax

Tecrax is a governed infrastructure-operations runtime/profile built on GovEngine and SCLite.

Current published baseline: `tecrax==0.3.0a0`, depending on
`govengine>=0.12.2a0,<0.15` and `sclite-core>=1.0.1,<1.1`.

This package provides:

- **RExecOp domain profile** — bundled YAML profile with intents, workflows, connectors,
  and validation rules (entry point `rexecop.profiles:tecrax`).
- **Local fixture review** — dry-run proof slice without live infrastructure.

It does not execute infrastructure changes, connect to hosts, manage credentials,
or provide production operational capability without explicit operator configuration.

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

The `0.3.0-alpha` release consolidates the RExecOp domain profile into this
package and aligns dependencies with RExecOp `0.1.x`. It does not add an
infrastructure runtime or a new contract surface beyond the bundled profile.

## Validation

```bash
python scripts/validate_public_truth.py
python -m pytest -q
```

The validator keeps this package as a second-host proof surface only. Any future
infrastructure runner, inventory, credential, scheduler, or carrier-adapter
claim must be backed by code and tests before it becomes public truth.
