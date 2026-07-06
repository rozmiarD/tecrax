# Changelog

All notable Tecrax profile changes are documented here.

## Unreleased

- Hardened the GLPI alert-ticket routing helper around private duplicate state,
  live API session cleanup and venv-based operator execution.
- Added the alert-source hygiene checkpoint before live GLPI routing, including
  a Wazuh alert aggregation helper, routing classes and an operator runbook.
- Added a public-safe GLPI alert-ticket routing helper and runbook. The helper
  accepts normalized Zabbix/Wazuh events, renders Polish operator-facing ticket
  drafts, applies duplicate suppression and keeps GLPI credentials outside Git.

## [0.3.17a0-0.3.21a0] - 2026-07-05

- **Current supported line:** `tecrax==0.3.21a0`, aligned to
  `rexecop==0.2.24a0`, `govengine==0.16.11` and `sclite-core==1.0.9`.
- **Profile delta:** none since `0.3.11a0`. `0.3.12a0`-`0.3.21a0`
  are coordinated stack repair artifacts only: dependency pins, public-truth
  markers and the `0.3.21a0` wheel packaging repair for public `examples/`.
- `0.3.19a0` was a source-only intermediate during release-train repair and was
  not published to PyPI.

### Publish follow-up repair line (superseded, pin-only)

| Tecrax | RExecOp extra pin | GovEngine | SCLite | Commit | Note |
| --- | --- | --- | --- | --- | --- |
| `0.3.21a0` | `0.2.24a0` | `0.16.11` | `1.0.9` | `07a55e2` | Current line; includes public `examples/` in the wheel. |
| `0.3.20a0` | `0.2.24a0` | `0.16.11` | `1.0.9` | `c526a5c` | Superseded; dependency/public-truth repair, missing wheel examples. |
| `0.3.18a0` | `0.2.23a0` | `0.16.9` | `1.0.8` | `08aeb41` | Superseded; coordinated public line before automation-chain release train. |
| `0.3.17a0` | `0.2.22a0` | `0.16.9` | `1.0.8` | `341e231` | Superseded; pin repair. |
| `0.3.16a0` | `0.2.21a0` | `0.16.9` | `1.0.8` | `48d8e87` | Superseded; pin repair. |
| `0.3.15a0` | `0.2.20a0` | `0.16.9` | `1.0.8` | `26eab3e` | Superseded; pin repair. |
| `0.3.14a0` | `0.2.19a0` | `0.16.9` | `1.0.8` | `e7b8260` | Superseded; pin repair. |
| `0.3.13a0` | `0.2.18a0` | `0.16.9` | `1.0.8` | `e281e88` | Superseded; pin repair. |
| `0.3.12a0` | `0.2.17a0` | `0.16.9` | `1.0.8` | `b50f1b1` | Superseded; pin repair. |

## [0.3.11a0] - 2026-07-04

- Published `tecrax==0.3.11a0` on PyPI aligned to `rexecop==0.2.16a0`,
  `govengine==0.16.8` and `sclite-core==1.0.8` (`9fdc216`).
- **Profile delta:** none — dependency pin and public-truth markers only.
- Repaired coordinated stack pin after `rexecop==0.2.15a0` published with a stale
  `tecrax==0.3.9a0` extra.

## [0.3.10a0] - 2026-07-04

- Published `tecrax==0.3.10a0` on PyPI aligned to `rexecop==0.2.15a0`,
  `govengine==0.16.8` and `sclite-core==1.0.8` (`6ffaa61`).
- **Profile delta:** none — dependency pin and public-truth markers only.

## [0.3.9a0] - 2026-07-04

- Published `tecrax==0.3.9a0` on PyPI aligned to `govengine==0.16.8`,
  `rexecop==0.2.14a0` and `sclite-core==1.0.8` (`8e3267e`).
- `a9e4038`, `d8198ab`: align dependency pins and public-truth markers with
  GovEngine `0.16.6` / `0.16.8` and RExecOp `0.2.12a0` / `0.2.14a0` before release.

### Added

- `eefe5d1`: first governed mutating slice `configure_chrony_ntp_server` with
  `tecrax_chrony_ntp` connector backend, mutation facts contract, active-profile
  gates and negative apply tests.
- `10b82f1`: profile-owned operator catalog metadata for all 14 active intents in
  `operator_metadata.yaml`, validated by `validate_active_profile.py`.
- Operator runbooks under `docs/runbooks/` (Proxmox/PBS, admin-tools, Samba AD,
  Windows pilots, AdGuard, Zabbix, Grafana, Wazuh, alerting, BookStack, GLPI,
  network devices, chrony/NTP); `27358b3` moved them from repo-root layout.
- `759ab0f`: Synology Zabbix community template runbook.

### Changed

- Kept the public documentation boundary explicit: operator-owned live wrappers,
  credentials, target addresses and private topology remain outside the repository.

### Deferred

- No active claims were added for arbitrary host management, CMDB sync, automatic
  discovery, production readiness or a second truth layer.

## [0.3.8a0] - 2026-06-29

- Declared the single supported alpha stack line for the current solo-development
  phase: `tecrax==0.3.8a0`, `rexecop==0.2.11a0`, `govengine==0.16.5`, and
  `sclite-core==1.0.8`.
- Replaced broad cross-stack dependency ranges with exact pins so fresh installs
  use one coherent current stack line instead of mixing older alpha wheels.
- Removed historical tag compatibility selection from CI; source checks now test
  the current `main` stack line only while older PyPI artifacts remain archived.

## [0.3.7a0] - 2026-06-28

- `diagnose_monitoring_host` now persists a profile-owned SCLite
  `reaction_observation` envelope in workflow shared state so RExecOp can plan
  deterministic reactions from a completed operation without constructing
  Tecrax domain facts in core.
- Declared the `diagnose_monitoring_host` reaction-observation contract in
  intent metadata and extended the active-profile gate to reject drift between
  the declaration and workflow producer step.
- Added source-line Tecrax trigger rules for bounded `network.host_observed`
  events: known catalog hosts plan `collect_basic_host_inventory` in dry-run
  mode, while unknown hosts escalate without execution.
- Published the coordinated trigger/reaction profile line over
  `govengine>=0.16.2,<0.17`, `sclite-core>=1.0.6,<1.1`, and
  `rexecop>=0.2.8a0,<0.3` without moving event intake, execution, governance,
  scheduler ownership or evidence truth into Tecrax.

## [0.3.6a0] - 2026-06-27

- Added stack-quality developer gates for `ruff` and `mypy`, plus the PEP 561
  `py.typed` marker, so Tecrax profile code participates in the same typed
  tooling baseline as RExecOp, GovEngine and SCLite.
- Added active-profile gates that keep fixture-only operations out of the active
  Tecrax profile and validate declared facts contract references.
- Added the versioned `tecrax.basic_host_inventory@1.0` facts contract with a
  packaged schema artifact, bounded model builder, and pure validator.
- Added versioned local SSH/systemd facts contracts for NTP local health, Docker
  service health, host security posture, and NTP server observation.
- Added versioned network-device inventory and network-management posture facts
  contracts for existing bounded legacy CLI observations.
- Extended the host security posture slice with a bounded available-update count summary
  while continuing to exclude package names, repositories, changelogs and paths.
- Added authenticated, read-only Zabbix T4 summaries for bounded problem counts
  and host/agent availability counts, using an operator-owned token outside git.
- Recorded the T5 AdGuard, Portainer and Docker boundary decision: keep Docker
  systemd-only, AdGuard DNS/login-only and Portainer `/api/status`-only until a
  constrained read-only projection is proven.
- Added the monitoring-host diagnosis v1 schema and deterministic bounded findings
  with stable reason codes over existing read-only component observations.
- Added explicit monitoring-host `unavailable` reaction rules so unavailable
  component states escalate through traceable profile-owned findings instead
  of falling through to the unclassified fallback.
- Added bounded monitoring-host escalation proposal vectors with negative tests
  for unknown intents, raw command payloads, unsafe evidence refs and secret-like
  explanations; proposals remain untrusted and never grant execution.
- Split network-device CLI parsing into explicit TP-Link SG2452 and HPE V1910
  parser families with sanitized golden fixtures and fail-closed unsupported
  output tests.
- Activated the network management-posture read-only lite slice over existing
  inventory facts, with bounded SSH findings and example policy admission.
- Added the VLAN and port-security read-only design checkpoint, keeping those
  observations out of the active profile until separate contracts and fixtures exist.
- Expanded future-product activation gates for Proxmox, PBS, Wazuh, Samba,
  Grafana, Frigate, Hillstone, printers and future backup support while keeping
  placeholder intents out of the active profile.
- Added CI/profile hardening for active-profile drift, future-product placeholders,
  premature VLAN/port-security actions and tracked secret/topology leak patterns.
- Documented the HTTP action identity checkpoint for future Zabbix, AdGuard and
  Portainer API expansion while preserving RExecOp core neutrality.
- Refactored fact normalizer storage so active normalizers share the same
  `finalize_facts` and `shared_state` write path.
- Split active normalizers into host, services, network, diagnostics, and common
  modules while preserving the `tecrax.internal_actions` RExecOp entrypoint.
- Published the coordinated domain-profile line over
  `govengine>=0.16.1,<0.17`, `sclite-core>=1.0.5,<1.1`, and
  `rexecop>=0.2.7a0,<0.3` without adding mutation, credential management,
  scheduler ownership, a second policy engine, or a second truth layer.

## [0.3.5a0] - 2026-06-24

- Published the profile after GovEngine `0.16.0` and RExecOp `0.2.6a0` passed
  their public-index install gates.
- Raised the GovEngine/RExecOp floors to the coordinated B2 release lines.
- Removed the obsolete `fixture` extra that required RExecOp `<0.2` while the
  package itself required RExecOp `>=0.2.5a0`.

### B2 policy enforcement vector

- The sanitized Ubuntu `collect_basic_host_inventory` example now declares
  profile-owned receipt, output-digest, timeout, step-count, and output-size
  policy controls.
- Cross-repository tests verify that GovEngine projects those controls into a
  digest-bound admission consumed by RExecOp.
- Tecrax still owns only the intent, workflow, connector shapes, validation, and
  policy-pack semantics. Runtime enforcement remains in RExecOp, governance in
  GovEngine, and canonical evidence/receipt truth in SCLite.

## [0.3.4a0] - 2026-06-23

- Added profile-owned target/operation catalog metadata and sanitized operator
  catalog examples.
- Added bounded read-only Ubuntu monitoring-host and legacy network-device
  inventory/health slices with private runtime configuration kept outside Git.
- Added deterministic profile-owned reaction vectors over existing read-only
  intents.
