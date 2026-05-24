# Tecrax

Tecrax is a governed infrastructure-operations runtime/profile built on GovEngine and SCLite.

Current source/package baseline: `tecrax==0.2.2a0`, depending on
`govengine>=0.11.0a0,<0.12` and `sclite-core>=0.8.0a0,<0.9`.

This repository/package contains a dry-run/local-fixture profile slice. It still
does not execute infrastructure changes, connect to hosts, manage credentials,
or provide production operational capability.

Planned foundation:

```text
Tecrax -> GovEngine -> SCLite
```

- SCLite owns lifecycle/proof/review artifacts.
- GovEngine owns deterministic governed-runtime kernel mechanics.
- Tecrax owns the infrastructure-operations profile semantics, fixture review
  payloads, UX, and future host integrations when those boundaries are mature.

Current local fixture proof:

```bash
tecrax fixture-review --service demo-web
```

The command emits a public-safe fixture review payload. It uses GovEngine
profile/planning/supervision/runtime-review contracts and binds its fixture
receipt through an SCLite artifact descriptor. It has no live runner, host
inventory, credential path, or infrastructure adapter.

The `0.2.2-alpha` patch only aligns this fixture consumer with the curated
SCLite/GovEngine package chain. It does not add an infrastructure runtime or a
new contract surface.

## Validation

```bash
python scripts/validate_public_truth.py
python -m pytest -q
```

The validator keeps this package as a second-host proof surface only. Any future
infrastructure runner, inventory, credential, scheduler, or carrier-adapter
claim must be backed by code and tests before it becomes public truth.
