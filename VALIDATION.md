# Tecrax Validation

Tecrax validation is local and public-safe. It does not connect to hosts, load
credentials, run infrastructure commands, or call carrier adapters.

```bash
python scripts/validate_public_truth.py
python scripts/validate_active_profile.py
python scripts/validate_secret_topology.py
python -m pytest -q
tecrax fixture-review --service demo-web
```

Expected result for source candidate `0.4.0rc1`:

- `pyproject.toml`, `tecrax.__version__`, README, public status, and validators agree on `0.4.0rc1` / `0.3.22-alpha`;
- latest PyPI publication is `0.3.21a0`, including the coordinated B2 profile vector;
- dependency truth is `govengine==0.17.0rc1`, `sclite-core==2.0.0rc1`, and `rexecop==0.3.0rc1`;
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
- active-profile gates reject future-product placeholders, undeclared mutating modes,
  undeclared connector actions and premature VLAN/port-security action names, while
  admitting only the bounded chrony/NTP apply slice;
- secret/topology gates scan tracked text files for private IPs, MAC addresses,
  key material, private SSH paths and obvious token/password assignments;
- fixture review output validates GovEngine profile, planning, supervision, runtime snapshot, review result, and runtime contract proof objects;
- SCLite is used only for local artifact descriptors;
- non-claims remain explicit for arbitrary mutation, credential management, carrier
  adapters, scheduler/storage, and production readiness.
