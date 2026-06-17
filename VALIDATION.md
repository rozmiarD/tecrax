# Tecrax Validation

Tecrax validation is local and public-safe. It does not connect to hosts, load
credentials, run infrastructure commands, or call carrier adapters.

```bash
python scripts/validate_public_truth.py
python -m pytest -q
tecrax fixture-review --service demo-web
```

Expected result for `0.3.0a0`:

- `pyproject.toml`, `tecrax.__version__`, README, public status, and validators agree on `0.3.0a0` / `0.3.0-alpha`;
- PyPI publication remains a fixture-only alpha package claim, not an infrastructure runtime claim;
- dependency truth is `govengine>=0.12.2a0,<0.15` and `sclite-core>=1.0.1,<1.1`;
- RExecOp profile entry point `tecrax:profile_root` resolves to a valid profile bundle;
- fixture review output validates GovEngine profile, planning, supervision, runtime snapshot, review result, and runtime contract proof objects;
- SCLite is used only for local artifact descriptors;
- non-claims remain explicit for live infrastructure, credentials, adapters, scheduler/storage, and production readiness.
