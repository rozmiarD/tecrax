from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from tecrax.alert_routing import AlertEvent


ZABBIX_SEVERITY_NAMES = {
    0: "not_classified",
    1: "information",
    2: "warning",
    3: "average",
    4: "high",
    5: "disaster",
}


@dataclass(frozen=True)
class ZabbixProblemQuery:
    min_severity: int = 2
    limit: int = 50
    include_suppressed: bool = False


def zabbix_problem_get_payload(query: ZabbixProblemQuery) -> dict[str, Any]:
    severities = [level for level in sorted(ZABBIX_SEVERITY_NAMES) if level >= query.min_severity]
    return {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": ["eventid", "objectid", "name", "severity", "clock", "suppressed"],
            "severities": severities,
            "suppressed": query.include_suppressed,
            "sortfield": "eventid",
            "sortorder": "DESC",
            "limit": query.limit,
        },
        "id": 1,
    }


def zabbix_trigger_host_payload(trigger_ids: Iterable[str]) -> dict[str, Any]:
    ids = sorted({_bounded_text(trigger_id, 64) for trigger_id in trigger_ids if str(trigger_id)})
    return {
        "jsonrpc": "2.0",
        "method": "trigger.get",
        "params": {
            "output": ["triggerid"],
            "triggerids": ids,
            "selectHosts": ["host", "name"],
        },
        "id": 2,
    }


def fetch_zabbix_problems(
    *,
    api_url: str,
    api_token: str,
    query: ZabbixProblemQuery,
    timeout_seconds: int = 15,
) -> list[dict[str, Any]]:
    problems = _zabbix_request(
        api_url=api_url,
        api_token=api_token,
        payload=zabbix_problem_get_payload(query),
        timeout_seconds=timeout_seconds,
        result_name="problem",
    )
    trigger_ids = [str(problem.get("objectid") or "") for problem in problems]
    if not trigger_ids:
        return problems
    triggers = _zabbix_request(
        api_url=api_url,
        api_token=api_token,
        payload=zabbix_trigger_host_payload(trigger_ids),
        timeout_seconds=timeout_seconds,
        result_name="trigger",
    )
    hosts_by_trigger = _hosts_by_trigger_id(triggers)
    return [
        {**problem, "hosts": hosts_by_trigger.get(str(problem.get("objectid") or ""), [])}
        for problem in problems
    ]


def _zabbix_request(
    *,
    api_url: str,
    api_token: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    result_name: str,
) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {api_token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"zabbix_http_error:{exc.code}:{_bounded_text(message, 200)}") from exc
    decoded = json.loads(data or "{}")
    if not isinstance(decoded, dict):
        raise RuntimeError("zabbix_response_not_object")
    if decoded.get("error"):
        raise RuntimeError(f"zabbix_api_error:{_bounded_text(decoded['error'], 240)}")
    result = decoded.get("result")
    if not isinstance(result, list):
        raise RuntimeError(f"zabbix_{result_name}_result_not_list")
    return [item for item in result if isinstance(item, dict)]


def zabbix_problem_to_alert_event(
    problem: dict[str, Any],
    *,
    source_url_base: str = "",
) -> AlertEvent:
    event_id = _bounded_text(problem.get("eventid") or "unknown", 120)
    name = _bounded_text(problem.get("name") or "Zabbix problem", 180)
    severity = _int(problem.get("severity"))
    host = _problem_host(problem)
    started_at = _zabbix_clock_to_iso(problem.get("clock"))
    source_url = _source_url(source_url_base, event_id)
    return AlertEvent(
        source="Zabbix",
        event_id=event_id,
        host=host,
        summary=name,
        raw_severity=str(severity),
        raw_trigger=name,
        started_at=started_at,
        source_url=source_url,
        category="",
    )


def zabbix_problems_to_alert_events(
    problems: Iterable[dict[str, Any]],
    *,
    source_url_base: str = "",
) -> list[AlertEvent]:
    return [
        zabbix_problem_to_alert_event(problem, source_url_base=source_url_base)
        for problem in problems
    ]


def alert_event_to_mapping(event: AlertEvent) -> dict[str, str]:
    return {
        "source": event.source,
        "event_id": event.event_id,
        "host": event.host,
        "summary": event.summary,
        "raw_severity": event.raw_severity,
        "raw_trigger": event.raw_trigger,
        "started_at": event.started_at,
        "source_url": event.source_url,
        "category": event.category,
    }


def _problem_host(problem: dict[str, Any]) -> str:
    hosts = problem.get("hosts")
    if isinstance(hosts, list) and hosts:
        first = hosts[0]
        if isinstance(first, dict):
            return _bounded_text(first.get("host") or first.get("name") or "unknown", 128)
    return "unknown"


def _hosts_by_trigger_id(triggers: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for trigger in triggers:
        trigger_id = str(trigger.get("triggerid") or "")
        hosts = trigger.get("hosts")
        if trigger_id and isinstance(hosts, list):
            result[trigger_id] = [host for host in hosts if isinstance(host, dict)]
    return result


def _zabbix_clock_to_iso(value: object) -> str:
    try:
        timestamp = int(str(value))
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _source_url(base: str, event_id: str) -> str:
    if not base:
        return ""
    return f"{base.rstrip('/')}/zabbix.php?action=problem.view&filter_eventids%5B0%5D={event_id}"


def _bounded_text(value: object, limit: int) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.replace("\r", " ").splitlines()).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
