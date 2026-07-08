from __future__ import annotations

import json
from pathlib import Path
import stat

from tecrax.alert_routing import (
    AlertEvent,
    TicketState,
    build_ticket_draft,
    load_events,
    route_events,
    wazuh_severity_key,
    zabbix_severity_key,
)


def test_zabbix_ticket_draft_uses_polish_operator_layer() -> None:
    draft = build_ticket_draft(
        AlertEvent(
            source="Zabbix",
            event_id="42",
            host="frigate01",
            summary="Mało miejsca na dysku",
            raw_severity="4",
            raw_trigger="High disk usage on /mnt/monitoring",
            started_at="2026-07-06T10:00:00+02:00",
        )
    )

    assert draft.title == "[Zabbix][Wysoki] Mało miejsca na dysku: frigate01"
    assert draft.category == "Dysk / miejsce"
    assert draft.urgency == 4
    assert "System monitoringu wykrył problem wymagający uwagi." in draft.content
    assert "Nie wykonywać działań destrukcyjnych" in draft.content
    assert "High disk usage on /mnt/monitoring" in draft.content
    assert "Powiązane runbooki:" in draft.content
    assert "zabbix-first-targets-adoption-runbook.md" in draft.content
    assert "basic-incident-handling-runbook.md" in draft.content


def test_ticket_draft_links_category_runbooks_when_available() -> None:
    draft = build_ticket_draft(
        AlertEvent(
            source="Zabbix",
            event_id="dns-1",
            host="dc01",
            summary="DNS service unavailable",
            raw_severity="3",
            raw_trigger="Samba domain DNS service is down",
        )
    )

    assert draft.category == "DNS / domena"
    assert "Powiązane runbooki:" in draft.content
    assert "dns-authority-checkpoint-runbook.md" in draft.content
    assert "samba-ad-dc-deployment-runbook.md" in draft.content


def test_wazuh_level_mapping_keeps_technical_level() -> None:
    assert wazuh_severity_key(15) == "disaster"
    assert wazuh_severity_key(12) == "high"
    assert wazuh_severity_key(10) == "average"
    assert wazuh_severity_key(7) == "warning"
    assert zabbix_severity_key("Average") == "average"


def test_route_events_dry_run_does_not_mark_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state = TicketState(state_path)
    event = AlertEvent(
        source="Wazuh",
        event_id="abc",
        host="dc01",
        summary="Podejrzane zdarzenie bezpieczeństwa",
        raw_severity="12",
        raw_trigger="authentication failure",
    )

    result = route_events([event], state, dry_run=True)

    assert result == [
        {
            "category": "Bezpieczeństwo",
            "dedupe_key": "Wazuh:abc",
            "status": "dry_run",
            "title": "[Wazuh][Wysoki] Podejrzane zdarzenie bezpieczeństwa: dc01",
            "urgency": 4,
        }
    ]
    assert not state_path.exists()


class _FakeClient:
    def create_ticket(self, draft):  # noqa: ANN001
        assert draft.title.startswith("[Zabbix]")
        return 1001


def test_route_events_live_marks_duplicates(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    event = AlertEvent(
        source="Zabbix",
        event_id="event-1",
        host="zbx01",
        summary="Host niedostępny",
        raw_severity="3",
        raw_trigger="Unavailable by ICMP",
    )

    first = route_events([event], TicketState(state_path), client=_FakeClient(), dry_run=False)
    second = route_events([event], TicketState(state_path), client=_FakeClient(), dry_run=False)

    assert first == [
        {
            "dedupe_key": "Zabbix:event-1",
            "glpi_ticket_id": 1001,
            "status": "created",
        }
    ]
    assert second == [{"dedupe_key": "Zabbix:event-1", "status": "duplicate"}]
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["routed"]["Zabbix:event-1"]["glpi_ticket_id"] == 1001
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600


def test_load_events_accepts_ndjson(tmp_path: Path) -> None:
    events_path = tmp_path / "events.ndjson"
    events_path.write_text(
        '{"source":"Zabbix","event_id":"1","host":"pve01","summary":"x","raw_severity":"2","raw_trigger":"y"}\n',
        encoding="utf-8",
    )

    events = load_events(events_path)

    assert len(events) == 1
    assert events[0].dedupe_key == "Zabbix:1"
