# Tecrax Validation

Tecrax validation is local and public-safe. It does not connect to hosts, load
credentials, run infrastructure commands, or call carrier adapters.

```bash
python scripts/validate_public_truth.py
python -m pytest -q
tecrax fixture-review --service demo-web
```

Expected result for `0.2.2a0`:

- `pyproject.toml`, `tecrax.__version__`, README, public status, and validators agree on `0.2.2a0` / `0.2.2-alpha`;
- PyPI publication remains a fixture-only alpha package claim, not an infrastructure runtime claim;
- dependency truth is `govengine>=0.11.0a0,<0.12` and `sclite-core>=0.8.0a0,<0.9`;
- fixture review output validates GovEngine profile, planning, supervision, runtime snapshot, review result, and runtime contract proof objects;
- SCLite is used only for local artifact descriptors;
- non-claims remain explicit for live infrastructure, credentials, adapters, scheduler/storage, and production readiness.
