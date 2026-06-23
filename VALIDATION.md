# Tecrax Validation

Tecrax validation is local and public-safe. It does not connect to hosts, load
credentials, run infrastructure commands, or call carrier adapters.

```bash
python scripts/validate_public_truth.py
python -m pytest -q
tecrax fixture-review --service demo-web
```

Expected result for `0.3.4a0`:

- `pyproject.toml`, `tecrax.__version__`, README, public status, and validators agree on `0.3.4a0` / `0.3.3-alpha`;
- PyPI publication remains a fixture-only alpha package claim, not an infrastructure runtime claim;
- dependency truth is `govengine>=0.15.0,<0.16`, `sclite-core>=1.0.4,<1.1`, and `rexecop>=0.2.5a0,<0.3`;
- RExecOp profile entry point `tecrax:profile_root` resolves to a valid profile bundle;
- `collect_basic_host_inventory` declares exact `ssh_readonly` command shapes and its
  parser tests use bounded fixture outputs without network access;
- the sanitized Ubuntu environment projects its B2 policy controls through GovEngine
  into a digest-bound enforcement plan and existing admission contract; unsupported
  controls remain fail-closed in GovEngine/RExecOp;
- NTP, Docker, Zabbix and AdGuard health fixtures validate deterministic normalization
  while preserving Docker inventory and AdGuard management API blockers documented in
  `docs/r2-readonly-status.md`;
- network device inventory fixtures validate bounded legacy CLI parsing without exposing
  target addresses, usernames, private keys, or operator-specific configuration;
- every profile intent has bounded catalog metadata, and the sanitized target catalog
  projects host and network-device applicability without environment paths or secrets;
- fixture review output validates GovEngine profile, planning, supervision, runtime snapshot, review result, and runtime contract proof objects;
- SCLite is used only for local artifact descriptors;
- non-claims remain explicit for mutation, credential management, carrier adapters,
  scheduler/storage, and production readiness.
