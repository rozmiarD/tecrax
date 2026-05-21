# Tecrax

Tecrax is a governed infrastructure-operations runtime/profile built on GovEngine and SCLite.

This repository/package now contains the first dry-run/local-fixture profile
slice. It still does not execute infrastructure changes, connect to hosts, manage
credentials, or provide production operational capability.

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
