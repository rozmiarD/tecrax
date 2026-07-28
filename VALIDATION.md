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

Expected result for source candidate `0.4.0rc3`:

- `pyproject.toml`, `tecrax.__version__`, CLI status, README, public status, and validators agree on `0.4.0rc3`;
- latest PyPI publication is `0.3.21a0`, including the coordinated B2 profile vector;
- dependency truth is `govengine==1.0.0rc1`, `sclite-core==2.0.0`, and `rexecop==0.3.0rc3`;
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
- the network-security-device syslog runbook and StoneOS Wazuh reference artifacts
  remain public-safe, exclude private topology and do not claim threat-specific
  coverage before a separately retained natural sample is validated;
- the Chrony regression proves a positive GovEngine plan reaches approved state while
  default RExecOp `stable_read_only` raises before connector I/O; Tecrax is not
  mutation_ready and the registered mutation candidate is not executable by default;
- focused Chrony tests use a small local executable to prove RExecOp-owned
  incremental capture enforces the exact `16384`-byte configured default and
  lower configured/request-policy limits across combined stdout and stderr.
  Overflow and timeout stay unsuccessful and raw-free; strict overflow evidence
  contains only limits, per-stream SHA-256 digests, truncation flags and byte
  counts before RExecOp's StepExecutor projection. This is not live-wrapper,
  retry, rollback, `lab_only`, permit, consume-once or mutation-readiness
  qualification, and emitted-byte digests do not claim bytes never emitted;
- every profile intent has bounded catalog metadata, and the sanitized target catalog
  projects host and network-device applicability without environment paths or secrets;
- active-profile gates reject future-product placeholders, undeclared mutating modes,
  undeclared connector actions and premature VLAN/port-security action names, while
  registering only the bounded chrony/NTP mutation candidate;
- secret/topology gates scan tracked text files for private IPs, MAC addresses,
  key material, private SSH paths and obvious token/password assignments;
- fixture review output validates GovEngine profile, planning, supervision, runtime snapshot, review result, and runtime contract proof objects;
- SCLite is used only for local artifact descriptors;
- CI resolves its external source inputs as ten immutable reviewed snapshots: two
  `rozmiarD/RExecOP` sibling checkouts at
  `1a20584ef1fa391f125e108822a7e439879a2e0b`, four `sclite-core` source
  installs at `0b90c21569ea908ba7ddb468cd1ab6126342924f`, and four
  `govengine` source installs at `0826accff407fdbc10df420803ff49cdd5818870`.
  The public-truth validator parses the workflow and compares this closed
  coordinate multiset by job and named step; a ref advance is an explicit new
  reviewed snapshot, not an implicit branch update;
- source identity only binds a CI input to a reviewed commit. It is not evidence
  of package compatibility, a resolvable public dependency line, or release
  qualification. F-001 remains open: the current Tecrax public dependency graph
  cannot yet be cleanly installed from the public index;
- non-claims remain explicit for arbitrary mutation, credential management, carrier
  adapters, scheduler/storage, and production readiness.
