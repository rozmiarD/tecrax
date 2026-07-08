# GLPI alert ticket routing runbook

This runbook covers the operator-owned GLPI ticket routing gate for normalized
Zabbix and Wazuh alerts.

It introduces deterministic Polish ticket drafts, duplicate suppression and a
small helper script. It does not store GLPI credentials, Zabbix tokens, Wazuh
raw alerts, private topology or real ticket contents in Tecrax.

## Scope

The gate covers:

- normalized Zabbix/Wazuh alert events as JSON or NDJSON input;
- Polish operator-facing ticket title and body;
- severity mapping for Zabbix severities and Wazuh levels;
- broad category mapping for the first GLPI routing layer;
- automatic links to public Tecrax runbooks when a matching category is
  available;
- duplicate suppression through a host-local state file;
- dry-run validation before live ticket creation;
- GLPI API ticket creation when operator-owned credentials are provided outside
  Git.

It does not configure Zabbix media actions, Wazuh integrations, mail ingestion,
LDAP/SSO, on-call escalation, compliance incident handling, automatic ticket
closure, asset inventory or full GLPI workflow policy.

## Public and Private Boundary

Safe in public docs and sign-offs:

- helper name and dry-run behavior;
- normalized event fields;
- Polish severity/category vocabulary;
- duplicate-suppression model;
- validation summary and non-claims.

Must remain outside Git and public sign-offs:

- GLPI API credentials and session tokens;
- Zabbix API tokens;
- Wazuh enrollment secrets and raw alert payloads;
- private endpoint inventories;
- real ticket contents if they include protected user/system data.

## Normalized Event Input

Use JSON array or NDJSON with one object per alert:

```json
{
  "source": "Zabbix",
  "event_id": "source-specific-event-id",
  "host": "host-alias",
  "summary": "short operator summary",
  "raw_severity": "3",
  "raw_trigger": "original technical trigger or rule",
  "started_at": "optional source timestamp",
  "source_url": "optional safe source link",
  "category": "optional Polish category override"
}
```

The helper intentionally expects normalized input. Wazuh source-specific
collection can be owned by existing local collectors or a future RExecOp
workflow.

For Zabbix shadow routing, use the bounded collector:

```sh
ZABBIX_API_TOKEN=... \
.venv/bin/python scripts/collect-zabbix-problems-for-glpi.py \
  --api-url https://zabbix.example.invalid/api_jsonrpc.php \
  --source-url-base https://zabbix.example.invalid \
  --min-severity 2 \
  --limit 20 \
  > /path/outside/repo/zabbix-shadow-events.ndjson
```

The collector reads active Zabbix problems and maps them to normalized alert
events for this helper. It is read-only, bounded by severity and limit, and must
be run with the Zabbix API token supplied from operator-owned secret custody.

Initial live-candidate filtering must stay conservative. In particular, host
unavailability is a live candidate only when the host is explicitly listed as
infrastructure:

```sh
ZABBIX_API_TOKEN=... \
.venv/bin/python scripts/collect-zabbix-problems-for-glpi.py \
  --api-url https://zabbix.example.invalid/api_jsonrpc.php \
  --source-url-base https://zabbix.example.invalid \
  --min-severity 2 \
  --limit 20 \
  --infra-host-file /path/outside/repo/alert-routing.yaml \
  --live-candidates-only \
  > /path/outside/repo/zabbix-live-candidates.ndjson
```

The operator context file may use this shape:

```yaml
alert_routing:
  zabbix:
    infrastructure_hosts:
      - pve01
      - zbx01
      - dc01
    host_down_policy:
      shadow_only_hosts:
        - pki01
```

Do not route ordinary staff PCs/laptops as host-down tickets. Users can power
them off, suspend them or leave the network, so endpoint availability belongs to
endpoint rollout/reporting policy, not infrastructure outage ticketing.

The first Zabbix live-candidate rules are intentionally narrow:

- infrastructure host unavailable, only for explicitly allowlisted
  infrastructure host aliases;
- critical disk pressure on infrastructure hosts;
- backup failures on infrastructure hosts;
- AD/DNS unavailable;
- core infrastructure service unavailable for Proxmox/PBS/Zabbix/Grafana/Wazuh/
  GLPI/BookStack-class services.

Known expected states remain shadow-only until source tuning is complete. The
first explicit exception is Frigate video-retention storage pressure on
`/mnt/monitoring`, which should not create live GLPI tickets by default.
On-demand hosts listed in `host_down_policy.shadow_only_hosts` are also
shadow-only for host-down routing. This is Tecrax profile/operator semantics,
not RExecOp runtime behavior.

## Procedure

### 1. Prepare Secret Custody

Store GLPI API credentials in an operator-owned secret path outside Tecrax.
Load them into the process environment only for the live run. Do not paste them
into Git, runbooks, command history examples or sign-offs.

### 2. Dry-Run Ticket Drafts

Run the helper in dry-run mode against a bounded sample of unresolved alerts:

```sh
.venv/bin/python scripts/route-glpi-alerts.py \
  --events /path/to/normalized-alerts.ndjson \
  --state /var/lib/tecrax/glpi-alert-routing/state.json \
  --dry-run
```

Validate that:

- titles are Polish and concise;
- category and severity are reasonable;
- the technical appendix keeps the original trigger/rule;
- no credential or raw private payload appears in output.

### 3. Live Ticket Creation

Only after dry-run validation, run live mode with operator-owned GLPI API
credentials in the environment:

```sh
.venv/bin/python scripts/route-glpi-alerts.py \
  --events /path/to/normalized-alerts.ndjson \
  --state /var/lib/tecrax/glpi-alert-routing/state.json \
  --api-url https://glpi.example.invalid/apirest.php
```

The helper creates one ticket for a new `source:event_id` pair and records the
GLPI ticket id in the state file. Re-running the same event is treated as a
duplicate.

Ticket content may include a `Powiązane runbooki` section. These links are
triage aids only. They do not prove that the procedure was executed and they do
not authorize destructive actions, credential changes, service restarts or data
cleanup.

### 4. Validate

Validate:

- dry-run output is bounded and public-safe;
- matching public runbook links appear for categories that have a known Tecrax
  runbook mapping;
- Zabbix shadow event snapshots and dry-run output are stored outside Git with
  private permissions;
- ordinary user endpoints are excluded from host-down live routing unless a
  separate endpoint policy explicitly changes that rule;
- first live ticket appears in GLPI;
- second run does not create a duplicate ticket for the same source event;
- state file is owned by the service/operator account and is not world-readable;
- GLPI web/API remains healthy;
- Zabbix and Wazuh source collectors continue to run.

## Stop Conditions

Stop before live ticket creation if:

- GLPI token custody is not operator-owned;
- duplicate suppression cannot write state safely;
- alert volume would flood GLPI;
- normalized events contain raw secrets, camera payloads, recordings or protected
  user data;
- category/severity mapping is ambiguous enough to mislead operators;
- live routing would require editing upstream Zabbix/Wazuh rules only for
  translation.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `glpi-alert-ticket-routing`;
- source systems included: Zabbix, Wazuh or both;
- dry-run validation summary;
- first live ticket proof without private ticket contents;
- duplicate-suppression proof;
- rollback/disable path;
- explicit non-claims.

Non-claims:

- no completed incident-response process;
- no automatic ticket closure;
- no mail ingestion;
- no LDAP/SSO;
- no compliance readiness;
- no raw Wazuh/Zabbix rule translation;
- no secret custody in Tecrax.
