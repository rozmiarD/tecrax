# Network security device syslog to Wazuh runbook

This runbook defines a bounded onboarding gate for security events emitted by a
network security device and ingested by a Wazuh manager through syslog.

The goal is to centralize actionable security events without turning Wazuh into
an unrestricted traffic-log archive, duplicating availability monitoring from
Zabbix or changing an existing Grafana dashboard during transport onboarding.

## Scope

The procedure covers:

- an exact source-device and destination-manager allowlist;
- a TCP syslog transport canary;
- a restricted initial log-type set;
- source identity and timestamp validation;
- representative-sample collection outside Git;
- vendor decoder and local-rule development after transport proof;
- bounded noise, storage and service-health checks;
- rollback of each side independently.

It does not enable session, NAT, traffic or debug logging, change firewall
forwarding policy, suppress existing Zabbix problems, modify Grafana dashboards,
route events to GLPI or claim encrypted transport.

## Ownership Boundaries

- The security device owns event generation and event-category selection.
- Wazuh owns security-event ingestion, decoding, correlation and alert storage.
- Zabbix continues to own availability and health telemetry.
- Grafana may later visualize a controlled read-only Wazuh view. It is not an
  ingestion or correlation layer.
- GLPI routing is a separate gate after noise and actionability are measured.

## Public and Private Boundary

Safe in public documentation:

- generic transport class;
- exact gate sequence;
- decoder and rule validation method;
- aggregate event counts and severity classes;
- rollback and non-claims.

Keep outside Git and public sign-offs:

- private addresses and topology;
- raw firewall, IPS, URL, user or session logs;
- source and destination identifiers from events;
- credentials, certificates and secret paths;
- raw device configuration and security policy;
- vendor serial, licence and signature metadata.

## Design Baseline

Use TCP for the initial internal canary when the device and Wazuh manager
support it. Bind the listener to the approved management address and allow only
the exact source address of the security device.

The initial event set should contain only:

- event and alarm logs needed to prove management and device-state visibility;
- security and threat logs;
- IPS, antivirus, reputation, botnet or sandbox findings when available.

Exclude initially:

- session start and end logs;
- NAT logs;
- full traffic logs;
- debug logs;
- binary or vendor-proprietary bulk formats.

The initial TCP transport is not encrypted. Accept it only on an internal,
bounded path with an exact source allowlist and record the confidentiality risk.
If encrypted syslog is required, introduce a supported TLS receiver and
certificate-custody gate separately. Do not disable certificate verification to
create a nominally encrypted but unauthenticated path.

## Preconditions

Before any mutation, prove:

- exact device identity, management address, OS/version and source interface;
- exact Wazuh hostname, address and service role;
- current Wazuh configuration checksum and a restorable backup;
- current listener state and local firewall state;
- Wazuh manager, indexer and shipper health;
- free space and current alert-ingestion rate;
- current Grafana dashboard fingerprint when it must remain unchanged;
- a device-side configuration backup and rollback command;
- exact vendor syntax from the running device or matching official manual.

Stop if the vendor command syntax, log-category name or rollback command is
ambiguous. A roadmap example is not mutation authority.

## Stage 1: Wazuh Transport Canary

Add one `remote` block to the Wazuh manager configuration:

```xml
<remote>
  <connection>syslog</connection>
  <port>514</port>
  <protocol>tcp</protocol>
  <allowed-ips>&lt;EXACT_DEVICE_SOURCE_IP&gt;</allowed-ips>
  <local_ip>&lt;WAZUH_MANAGEMENT_IP&gt;</local_ip>
</remote>
```

Requirements:

- `allowed-ips` contains one exact source, not a broad subnet;
- `local_ip` is the approved internal management address;
- no UDP listener is added unless the device cannot use TCP and the operator
  accepts the delivery-loss risk;
- the existing secure agent listener remains unchanged.

Validate configuration before restart using the supported Wazuh configuration
check for the installed version. Take a fresh backup immediately before the
edit. Restart only `wazuh-manager`, then prove:

- the service returns active;
- the existing agent listener still exists;
- the new TCP listener is bound only as designed;
- existing Wazuh agents remain active;
- indexer and shipper health did not regress.

If the manager does not return healthy, restore its exact backup and restart it.
Do not continue to the device.

### Framing-normalization fallback

Do not treat an established TCP session as continuous-ingestion proof. If the
first event after reconnect is processed but later events on the same session
are not, capture only enough private traffic to determine record boundaries and
test an extracted record with `wazuh-logtest`. When the record itself decodes
correctly but the device emits a non-standard terminator such as `LF+NUL`, use a
parallel normalization canary instead of weakening rules or switching blindly
to UDP.

The fallback shape is:

1. retain the direct Wazuh listener as rollback;
2. add a separate rsyslog TCP input bound to the approved internal address and
   restricted to the exact device source;
3. configure the observed additional delimiter and emit exactly one
   LF-terminated, control-character-free line per record;
4. write to a non-world-readable file readable by the Wazuh service account;
5. add that exact file as a Wazuh `localfile` with `syslog` format;
6. keep bounded rotation and prove two or more events on the same TCP session.

For rsyslog `imtcp`, validate the installed version's support for
`AddtlFrameDelimiter` and `DisableLFDelimiter`. Older releases may require the
legacy `$AllowedSender TCP, <EXACT_SOURCE>` directive. That directive applies
globally to rsyslog TCP inputs, so reassess it before adding another TCP input;
prefer an input-scoped source restriction or a host firewall rule when the
installed version supports one safely.

Account for rsyslog privilege dropping before selecting file ownership. The
daemon must be able to traverse the parent directory and write the file, while
Wazuh needs read access only. Do not make the normalized log world-readable.
Use bounded `copytruncate` rotation when the receiver keeps the file open, and
validate the rotation policy without forcing a live rotation during onboarding.

Before promotion, prove all of the following:

- the original and normalization paths are both available for rollback;
- line count increases after at least two separate events on one connection;
- normalized output contains no delimiter NUL bytes and ends each record once;
- Wazuh alert count increases for multiple records, not only after reconnect;
- existing agent listeners, agent health, indexer and shipper remain healthy;
- bulk traffic, session, NAT and debug categories remain absent.

Parallel paths may duplicate the first event after a direct-listener reconnect.
Remove the direct path only after an observation gate and separate approval.

## Stage 2: Device-Side Canary

Configure exactly one syslog destination:

- destination: the approved Wazuh management address;
- source: the approved device interface/address;
- transport: TCP;
- port: the Wazuh canary listener;
- encoding: UTF-8 when selectable;
- categories: the restricted initial set only.

Do not enable traffic, session, NAT or debug logs. Do not alter security-policy
actions merely to manufacture an event.

Save persistent device configuration only after:

- the Wazuh listener accepts a connection from the exact source;
- one normal management event is received;
- the device reports no syslog transport error;
- there is no material CPU, memory or log-rate regression.

If the transport fails, remove only the newly added syslog destination. Do not
change routing, VLANs or firewall policy as an improvised workaround.

## Stage 3: Decoder and Rule Gate

Transport proof does not mean useful detection.

Collect a minimal representative sample outside Git:

- one management event;
- one device alarm if naturally available;
- one security or threat event already generated by normal operation;
- one IPS/AV/reputation event when naturally available.

Redact identities before using a sample in development. Keep the original raw
sample only in private operator custody.

Use `wazuh-logtest` against candidate decoders and local rules. The decoder
should extract only stable vendor fields such as:

- vendor/device family;
- vendor severity;
- module or event class;
- stable event or signature identifier when present;
- action class such as detected, blocked or allowed.

Do not make IP addresses, URLs or user identifiers part of a rule identity.
Keep them as event context subject to retention and access controls.

Local rule levels should distinguish:

- informational management telemetry;
- warnings and configuration changes;
- suspicious security detections;
- confirmed block/prevention actions;
- critical device or security failures.

Unknown vendor messages must remain visible for review during the canary. Do not
silence them globally.

For the StoneOS canary, the public-safe decoder and local-rule candidates are
stored in:

- `deploy/wazuh/hillstone-stoneos-decoders.xml`;
- `deploy/wazuh/hillstone-stoneos-rules.xml`.

They cover the management-event envelope plus stable fields from naturally
occurring threat records retained in private custody. Threat events receive a
general detection rule, while the narrower child rule covers only the observed
`log-only` protocol-exception shape. It does not claim coverage for block,
prevention, malware or other unobserved actions. The private natural-sample gate
must pass `wazuh-logtest`; a post-deployment natural hit may remain explicitly
pending when no new source event occurs during the bounded observation window.

The files are reference deployment artifacts, not an unattended installer;
local rule-ID availability, backups, pre-restart validation and regression
tests for existing management events remain mandatory.

## Noise and Capacity Gate

Measure aggregate counts rather than publishing raw events:

- messages by category and severity;
- decoded versus unknown messages;
- Wazuh alerts created;
- index growth;
- manager queue or drop indicators;
- CPU, memory and disk pressure.

Success is event-based, not merely time-based. Require:

- a received management event;
- a received naturally occurring security event or an explicit pending marker
  if none occurs during the controlled observation;
- stable Wazuh services and existing agent flow;
- no traffic/session/NAT/debug flood;
- a tested decoder for every category promoted to production alerting.

## Grafana and GLPI Gates

Do not modify an established Grafana dashboard during syslog onboarding.

After Wazuh ingestion and rules are stable:

1. create a separate controlled read-only Wazuh/OpenSearch access path;
2. build a separate security-events dashboard or row first;
3. preserve the existing infrastructure dashboard and its fingerprint;
4. route only deduplicated, actionable Wazuh findings to GLPI in a separate
   approved gate.

Grafana must query Wazuh directly through the approved read-only path. Do not
convert security events into fake Zabbix availability problems.

## Stop Conditions

Stop before or during the change if:

- exact device identity or source address does not match the approved plan;
- Wazuh configuration validation fails;
- the manager, indexer or shipper is unhealthy;
- an existing agent listener changes unexpectedly;
- device syntax or rollback is ambiguous;
- enabling the destination requires a routing, VLAN or broad firewall change;
- traffic, session, NAT or debug logs enter the canary unexpectedly;
- log volume, CPU, memory, disk or queue pressure exceeds the recorded baseline;
- raw security events would enter Git, chat or public documentation;
- the Grafana dashboard changes during this gate.

## Rollback

Rollback Wazuh and the device independently.

Wazuh rollback:

- restore the exact pre-change configuration backup;
- validate configuration;
- restart `wazuh-manager`;
- prove the original secure agent listener and active-agent state.

Normalization-canary rollback:

- remove only the added device destination on the canary port;
- remove the matching Wazuh `localfile` block after configuration validation;
- remove the rsyslog input, bounded output and rotation policy;
- restore any parent-directory permission changed solely for the receiver;
- prove the original listener, services and agent state before closing rollback.

Device rollback:

- remove only the newly added syslog destination and category bindings;
- validate local logging remains intact;
- save only after the live configuration matches the pre-state.

Rollback does not delete events already indexed by Wazuh. Retention or deletion
is a separate data-governance decision.

## Sign-Off Shape

Record:

- run class: `network-security-device-syslog-to-wazuh`;
- exact approved scope represented by private references;
- pre/post configuration checksums;
- source/destination/transport class without public topology;
- enabled and explicitly excluded event categories;
- received, decoded and unknown aggregate counts;
- Wazuh service and agent-health smoke;
- Grafana fingerprint equality;
- rollback readiness and result;
- residual plaintext-transport risk;
- pending TLS, Grafana and GLPI gates.

Non-claims:

- no full SIEM tuning;
- no encrypted transport unless separately proven;
- no complete vendor-event coverage;
- no automatic remediation;
- no live GLPI routing;
- no Grafana dashboard mutation;
- no NIS2/KSC compliance claim from transport onboarding alone.
