# Changelog

All notable Tecrax profile changes are documented here.

## Unreleased

## [0.3.22a0] - 2026-07-10

- **Unpublished source candidate:** aligns the profile package to
  `rexecop==0.2.25a0`, `govengine==0.16.12rc1`, and `sclite-core==1.0.10rc1`
  for the SCLite P0 integrity/lifecycle hardening train.
- **Publication boundary:** `tecrax==0.3.21a0` remains the latest published PyPI
  package until the candidate artifacts pass the complete local release gates.

- Added the Synology NAS domain-home and GPO drive-mapping runbook for moving
  from a one-user AD-auth pilot to a neutral staff `home` mapping model without
  storing credentials, deleting NAS data or hand-building GPO objects.
- Extended the Synology NAS domain-home runbook with the DSM user-home-service
  check after domain rejoin or NAS rename, plus the known-good GPP Drive Maps
  shape for credential-free `home` mapping.
- Added the Wazuh Dashboard RBAC operator-access runbook and a read-only RBAC
  audit helper for detecting missing administrator role-mapping rules without
  printing password hashes.
- Added the Wazuh source noise hygiene runbook for bounded source-side
  suppression of routine successful operational telemetry before ticket routing,
  including manager alert-level and shared agent scan-cadence baseline guidance.
- Added automatic public Tecrax runbook links to GLPI alert-ticket drafts when a
  matching alert category is available.
- Added the Synology NAS AD-auth pre-change runbook for the planned service
  window, defining the member-file-server model, one-user pilot scope,
  AD-group-based access, rollback boundaries and no-delete guardrails.
- Added the Samba AD delegated domain-join runbook for narrowing routine
  workstation joins from broad transitional rights toward OU-specific ACLs,
  with fallback removal kept behind a live join test.
- Added Vaultwarden bootstrap and backup/restore-proof runbooks, keeping the
  service in bootstrap custody status until restore, offline break-glass, PKI
  restore and Proxmox root-of-trust hardening gates are complete.
- Added the Vaultwarden application-backup and break-glass baseline runbook for
  root-owned SQLite/data archives, private checksum evidence and offline
  recovery boundaries without exporting vault contents.
- Tightened the Vaultwarden bootstrap runbook to require HTTPS-only operator
  browser access even before final PKI material is available.
- Added the PKI Center bootstrap runbook for an on-demand VM substrate, keeping
  production CA material, trust distribution and final HTTPS migration out of
  scope until custody and restore gates are defined.
- Added the host-down routing policy runbook and Zabbix GLPI collector support
  for keeping selected on-demand host-down alerts shadow-only.
- Recorded the PKI Center CA architecture decision as offline root plus
  on-demand intermediate without generating or documenting private CA material.
- Recorded OpenSSL as the selected PKI Center CA engine while deferring final
  CA policies, issuance, renewal, revocation and autorotation procedure to
  hardening.
- Added the PKI certificate lifecycle planning runbook for future CSR/SAN/FQDN,
  issuance, renewal, revocation, trust distribution and private inventory work
  without generating CA material.
- Added the PKI HTTPS rollout planning runbook for future administrative
  service FQDN/SAN naming, migration order, TLS placement and trust-root
  dependencies without live TLS changes.
- Added the Wazuh backup/restore decision runbook, keeping app-aware index
  export deferred until retention, custody and isolated restore gates exist.
- Added the GLPI inventory scope runbook, defining a conservative Phase 1
  infrastructure inventory baseline and deferring agents, endpoint discovery
  and network sweeps.
- Added the basic incident-handling runbook for GLPI incident intake, triage,
  classification, containment, evidence custody, closure and follow-up without
  claiming compliance readiness or automatic containment.
- Extended the admin-tools substrate runbook with the dedicated runtime-node
  model: admin-tools is the target for operator wrappers, policy files, private
  state and controlled Tecrax/RExecOp runtime, while development stays on the
  operator workstation.
- Added operator-context file support for Zabbix GLPI live-candidate
  infrastructure host allowlists.
- Extended the conservative Zabbix live-candidate allowlist with critical disk,
  backup failure, AD/DNS unavailable and core service unavailable classes while
  keeping known Frigate retention storage pressure shadow-only.
- Added conservative Zabbix live-candidate filtering so host-down ticketing only
  applies to explicitly allowlisted infrastructure hosts, not ordinary endpoints.
- Added a bounded Zabbix active-problem collector for GLPI shadow routing. It
  exports normalized alert events without storing API tokens or creating tickets.
- Updated GLPI alert-ticket drafts and helper output to use Polish diacritics in
  operator-facing labels, categories and guidance.
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
