from __future__ import annotations

from tecrax.zabbix_glpi_events import (
    ZabbixProblemQuery,
    alert_event_to_mapping,
    zabbix_problem_get_payload,
    zabbix_trigger_host_payload,
    zabbix_problem_to_alert_event,
)


def test_zabbix_problem_payload_is_bounded_and_warning_plus_by_default() -> None:
    payload = zabbix_problem_get_payload(ZabbixProblemQuery())

    assert payload["method"] == "problem.get"
    assert payload["params"]["severities"] == [2, 3, 4, 5]
    assert payload["params"]["limit"] == 50
    assert payload["params"]["suppressed"] is False
    assert "selectHosts" not in payload["params"]


def test_zabbix_trigger_host_payload_maps_problem_objectids_to_hosts() -> None:
    payload = zabbix_trigger_host_payload(["1002", "1001", "1001"])

    assert payload["method"] == "trigger.get"
    assert payload["params"]["triggerids"] == ["1001", "1002"]
    assert payload["params"]["selectHosts"] == ["host", "name"]


def test_zabbix_problem_to_alert_event_maps_glpi_fields() -> None:
    event = zabbix_problem_to_alert_event(
        {
            "eventid": "123",
            "name": "High disk usage on /mnt/monitoring",
            "severity": "4",
            "clock": "1783339200",
            "hosts": [{"host": "frigate01", "name": "Monitoring wizyjny"}],
        },
        source_url_base="http://zabbix.local",
    )

    assert event.source == "Zabbix"
    assert event.event_id == "123"
    assert event.host == "frigate01"
    assert event.summary == "High disk usage on /mnt/monitoring"
    assert event.raw_severity == "4"
    assert event.raw_trigger == "High disk usage on /mnt/monitoring"
    assert event.started_at.startswith("2026-07-06T")
    assert "filter_eventids%5B0%5D=123" in event.source_url


def test_alert_event_to_mapping_matches_glpi_router_input_shape() -> None:
    event = zabbix_problem_to_alert_event(
        {
            "eventid": "321",
            "name": "Host unavailable by ICMP",
            "severity": 3,
            "clock": "1783339200",
            "hosts": [{"name": "pve01"}],
        }
    )

    assert alert_event_to_mapping(event) == {
        "source": "Zabbix",
        "event_id": "321",
        "host": "pve01",
        "summary": "Host unavailable by ICMP",
        "raw_severity": "3",
        "raw_trigger": "Host unavailable by ICMP",
        "started_at": event.started_at,
        "source_url": "",
        "category": "",
    }
