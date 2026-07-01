# GLPI minimal operational baseline runbook

This runbook covers the first operator-owned operational baseline for GLPI after
deployment, monitoring, backup coverage and restore proof are complete.

It prepares GLPI to act as the helpdesk, inventory and incident-register layer,
and records the decision that GLPI is the future ticket channel for Zabbix and
Wazuh alerts. It does not activate final alert automation yet.

## Scope

The baseline covers:

- default application-account hygiene;
- operator administrative access sanity check;
- a minimal ITIL category baseline;
- a minimal request-source baseline;
- the future alert-routing decision for GLPI tickets;
- public-safe validation and sign-off.

It does not configure mail ingestion, LDAP/SSO, GLPI endpoint agents, full
inventory discovery, final alert automation, escalation policy, compliance
readiness or private PKI/HTTPS hardening.

## Public and Private Boundary

Safe in public docs and sign-offs:

- service alias: `glpi01`;
- category names and request-source names;
- decision that GLPI is the target channel for future alert tickets;
- bounded validation summary;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- GLPI passwords, API tokens and session cookies;
- database credentials;
- LDAP bind credentials;
- SMTP credentials;
- real ticket contents, user data and uploaded files;
- private topology dumps.

## Baseline Decisions

GLPI is the preferred channel for future Zabbix and Wazuh alert tickets.

The first baseline should remain small. Use a few durable categories instead of
building a complete ITSM process before the operator has real ticket history.

Initial ITIL categories:

- `Awaria`;
- `Prosba`;
- `Dostep`;
- `Infrastruktura`;
- `Bezpieczenstwo`;
- `Alerty monitoringu`.

Initial request sources:

- `Monitoring alert`;
- `Operator entry`;
- `User request`.

## Procedure

### 1. Verify Operator Access

Before disabling any default installer account, confirm that an operator-owned
account exists and has administrative access.

Do not store or print the password. If the operator has not rotated the
credential, stop and rotate it through an operator-owned path first.

### 2. Disable Installer Default Account

Disable the installer default administrative account only after operator
administrative access is confirmed.

Do not delete the account during the first baseline. Disabling is reversible and
keeps the audit trail clearer during early deployment.

### 3. Create Minimal Categories

Create the initial categories listed in this runbook if they do not already
exist.

Keep category names stable enough for later alert routing, dashboards and
documentation.

### 4. Create Minimal Request Sources

Create request-source values for manual operator entries, user requests and
future monitoring alerts.

Do not configure automated ticket creation until the final alert channel design
has an operator-owned credential and duplicate-suppression policy.

### 5. Validate

Validate:

- GLPI web endpoint still returns a successful response;
- database service is active;
- web service and PHP runtime are active;
- operator account remains active;
- default installer account is disabled;
- minimal ITIL categories exist;
- minimal request sources exist;
- Zabbix and Wazuh agents remain active on the GLPI host.

## Stop Conditions

Stop before sign-off if any of these are true:

- no operator-owned administrative account exists;
- disabling a default account would lock out the operator;
- the GLPI web endpoint fails after the baseline;
- database validation fails;
- category or request-source changes require exposing real ticket contents;
- final alert automation would require pasting secrets into Git, chat or
  public docs.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- service alias;
- run class: `glpi-minimal-operational-baseline`;
- account-hygiene result without passwords;
- category/request-source baseline summary;
- alert-channel decision;
- validation result summary;
- explicit non-claims.

Non-claims:

- no final alert automation;
- no mail ingestion;
- no LDAP/SSO;
- no endpoint-agent inventory rollout;
- no compliance readiness;
- no private PKI/HTTPS completion.

## Next Gate

After this baseline, the next GLPI-related gate is final alert ticket routing
from Zabbix and Wazuh through an operator-owned credential, with duplicate
suppression and a rollback path.
