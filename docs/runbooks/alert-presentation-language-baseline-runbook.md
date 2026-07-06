# Alert presentation language baseline runbook

This runbook defines the operator-facing language baseline for alert
presentation before GLPI ticket automation.

The target operator language for the current deployment is Polish. The baseline
does not translate upstream Zabbix templates, Zabbix item keys, Wazuh rules,
Wazuh decoders, raw logs or raw alert payloads. It controls the human-facing
layer: GLPI tickets, Grafana dashboard text, BookStack procedures and local
custom alerts.

## Scope

Allowed:

- define severity labels in Polish;
- define first alert categories in Polish;
- define GLPI ticket title and body templates;
- define Grafana dashboard wording rules;
- define what belongs in the Polish summary and what remains as technical
  appendix;
- require locally-owned custom alerts to use Polish operator-facing text.

Not allowed:

- fork or rewrite upstream Zabbix templates only to translate names;
- rewrite Wazuh upstream rules or decoders;
- translate raw payloads in-place;
- hide technical identifiers needed for debugging;
- include secrets, tokens, private URLs, raw logs or private inventories in
  presentation templates;
- send tickets before duplicate handling and rollback are defined.

## Ownership Boundary

Tecrax owns the presentation semantics for this profile:

- category vocabulary;
- severity label mapping;
- operator-facing template shape;
- non-claims and safety wording.

Zabbix, Wazuh and Grafana remain the source systems for telemetry and alerts.
GLPI remains the ticket destination. RExecOp may later execute a bounded routing
workflow. GovEngine owns admission and constraints for ticket creation. SCLite
owns evidence and receipts.

## Severity Labels

Use these labels when showing alert severity to an operator:

| Raw / source severity | Polish label |
| --- | --- |
| Disaster | Awaria krytyczna |
| High | Wysoki |
| Average | Średni |
| Warning | Ostrzeżenie |
| Information | Informacja |
| Not classified | Niesklasyfikowane |

For Wazuh, map numerical levels into the same operator vocabulary in the ticket
routing layer. Keep the original Wazuh rule level in the technical appendix.

Recommended first mapping:

| Wazuh level | Polish label |
| --- | --- |
| 15+ | Awaria krytyczna |
| 12-14 | Wysoki |
| 10-11 | Średni |
| 7-9 | Ostrzeżenie |
| 3-6 | Informacja |
| 0-2 | Niesklasyfikowane |

## Alert Categories

Use these first categories:

- Dostępność
- Wydajność
- Dysk / miejsce
- Backup
- Bezpieczeństwo
- Sieć
- DNS / domena
- Monitoring wizyjny
- Usługi administracyjne

These categories are intentionally broad. Avoid creating a new category for
every product or template. Use tags or a technical appendix for exact source
details.

## GLPI Ticket Template

Ticket title:

```text
[<Źródło>][<Priorytet>] <Krótki opis>: <Host albo usługa>
```

Examples:

```text
[Zabbix][Wysoki] Mało miejsca na dysku: frigate01
[Wazuh][Średni] Podejrzane zdarzenie bezpieczeństwa: workstation
```

Ticket body:

```text
System monitoringu wykrył problem wymagający uwagi.

Co wykryto:
<krótki opis po polsku>

Host/usługa:
<alias albo rola>

Kategoria:
<kategoria po polsku>

Priorytet:
<polski severity label>

Od kiedy:
<czas zdarzenia w lokalnej strefie czasu, jeśli dostępny>

Znaczenie:
<jedno lub dwa zdania o wpływie operacyjnym>

Sugerowany pierwszy krok:
<bezpieczna pierwsza czynność diagnostyczna>

Szczegóły techniczne:
- Źródło: <Zabbix/Wazuh/Grafana/manual>
- Raw severity / level: <oryginalna wartość>
- Raw trigger / rule: <oryginalna nazwa techniczna>
- Event ID: <id jeśli dostępne>
- Link do źródła: <link jeśli jest bezpieczny>

Uwagi:
Nie wykonywać działań destrukcyjnych bez potwierdzenia operatora.
```

Do not include passwords, tokens, private payloads, camera streams, recordings,
raw logs or full endpoint inventories.

## Grafana Language Rules

Dashboard and panel titles owned by this deployment should be Polish:

- Aktywne problemy
- Dostępność hostów
- Agenty monitoringu
- Serwerownia: temperatura
- Monitoring wizyjny: miejsce na nagrania
- Backup: status zadań
- Bezpieczeństwo: ostatnie alerty

Keep technical names where they are useful for troubleshooting:

- host aliases;
- item keys shown only in drill-down or technical panels;
- original trigger/rule names in detail views;
- upstream template names.

Do not create large explanatory text panels. Use compact Polish labels and keep
technical detail in drill-downs or linked source systems.

## BookStack and Procedures

Operational procedures, incident handling and handoff content intended for local
administrators should be written in Polish.

Public-safe Tecrax repo documentation may remain English unless it is explicitly
an operator-facing Polish presentation artifact.

For larger BookStack rewrites, a smaller model may be used only after explicit
operator approval and only with public-safe content. The operator-facing Polish
text still needs final review against live repo and infrastructure truth.

## Source-System Rules

Zabbix:

- keep upstream template names and item keys unchanged;
- write locally-owned custom triggers in Polish when practical;
- use tags/category mapping for routing;
- include raw trigger name in the technical appendix.

Wazuh:

- keep upstream rule names, IDs and decoders unchanged;
- do not translate raw logs;
- translate only the operator-facing summary and ticket body;
- include Wazuh rule ID and raw level in the technical appendix.

Grafana:

- local dashboard titles and panels should be Polish;
- preserve exact datasource and technical identifiers where needed.

GLPI:

- ticket title and body should be Polish first;
- technical appendix follows after the human-readable section.

## Stop Conditions

Stop before automating ticket creation if:

- duplicate suppression is not defined;
- ticket rollback/close behavior is not defined;
- Polish category or severity mapping is ambiguous;
- source payload would expose secrets or protected data;
- alert volume would flood GLPI;
- the system would translate or modify upstream rules/templates in-place.

## Sign-Off Shape

Use `../operator-signoff-template.md` and include:

- date;
- run class: `alert-presentation-language-baseline`;
- target operator language;
- severity mapping status;
- category mapping status;
- GLPI template status;
- Grafana language rule status;
- explicit non-claims.

Non-claims:

- no GLPI ticket creation yet;
- no upstream template/rule translation;
- no incident procedure finalization;
- no compliance hardening claim;
- no automatic remediation.

## Next Gate

After this baseline is accepted, implement GLPI alert ticket automation using
Polish title/body templates, duplicate suppression, bounded source payloads and
operator-owned GLPI credentials.
