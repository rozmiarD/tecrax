from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


POLISH_SEVERITY_LABELS = {
    "disaster": "Awaria krytyczna",
    "high": "Wysoki",
    "average": "Sredni",
    "warning": "Ostrzezenie",
    "information": "Informacja",
    "not_classified": "Niesklasyfikowane",
}

ZABBIX_SEVERITY_MAP = {
    "5": "disaster",
    "4": "high",
    "3": "average",
    "2": "warning",
    "1": "information",
    "0": "not_classified",
    "disaster": "disaster",
    "high": "high",
    "average": "average",
    "warning": "warning",
    "information": "information",
    "not classified": "not_classified",
    "not_classified": "not_classified",
}


@dataclass(frozen=True)
class AlertEvent:
    source: str
    event_id: str
    host: str
    summary: str
    raw_severity: str
    raw_trigger: str
    started_at: str = ""
    source_url: str = ""
    category: str = ""

    @property
    def dedupe_key(self) -> str:
        return f"{self.source}:{self.event_id}"


@dataclass(frozen=True)
class TicketDraft:
    dedupe_key: str
    title: str
    content: str
    category: str
    urgency: int
    source: str
    source_event_id: str

    def glpi_payload(self) -> dict[str, dict[str, str | int]]:
        return {
            "input": {
                "name": self.title,
                "content": self.content,
                "urgency": self.urgency,
                "impact": self.urgency,
                "priority": self.urgency,
            }
        }


def zabbix_severity_key(value: object) -> str:
    raw = str(value).strip().lower()
    return ZABBIX_SEVERITY_MAP.get(raw, "not_classified")


def wazuh_severity_key(level: object) -> str:
    try:
        number = int(str(level).strip())
    except ValueError:
        return "not_classified"
    if number >= 15:
        return "disaster"
    if number >= 12:
        return "high"
    if number >= 10:
        return "average"
    if number >= 7:
        return "warning"
    if number >= 3:
        return "information"
    return "not_classified"


def polish_severity_label(severity_key: str) -> str:
    return POLISH_SEVERITY_LABELS.get(severity_key, POLISH_SEVERITY_LABELS["not_classified"])


def glpi_urgency(severity_key: str) -> int:
    return {
        "disaster": 5,
        "high": 4,
        "average": 3,
        "warning": 2,
        "information": 1,
        "not_classified": 1,
    }.get(severity_key, 1)


def infer_category(event: AlertEvent) -> str:
    if event.category:
        return _bounded_text(event.category, 80)
    text = f"{event.summary} {event.raw_trigger} {event.host}".lower()
    if any(token in text for token in ("wazuh", "security", "auth", "login", "sudo")):
        return "Bezpieczenstwo"
    if any(token in text for token in ("disk", "space", "filesystem", "storage", "miejsce")):
        return "Dysk / miejsce"
    if any(token in text for token in ("backup", "pbs", "restore")):
        return "Backup"
    if any(token in text for token in ("dns", "domain", "ad ", "samba")):
        return "DNS / domena"
    if any(token in text for token in ("camera", "frigate", "rtsp", "recording")):
        return "Monitoring wizyjny"
    if any(token in text for token in ("ping", "unavailable", "down", "icmp")):
        return "Dostepnosc"
    if any(token in text for token in ("cpu", "memory", "load", "performance")):
        return "Wydajnosc"
    return "Uslugi administracyjne"


def build_ticket_draft(event: AlertEvent) -> TicketDraft:
    severity_key = (
        wazuh_severity_key(event.raw_severity)
        if event.source.lower() == "wazuh"
        else zabbix_severity_key(event.raw_severity)
    )
    label = polish_severity_label(severity_key)
    category = infer_category(event)
    source = _bounded_text(event.source, 24)
    host = _bounded_text(event.host or "nieznany-host", 128)
    summary = _bounded_text(event.summary or event.raw_trigger, 180)
    raw_trigger = _bounded_text(event.raw_trigger, 240)
    started_at = _bounded_text(event.started_at or "brak danych", 80)
    source_url = _bounded_text(event.source_url or "brak bezpiecznego linku", 300)

    title = f"[{source}][{label}] {summary}: {host}"
    content = "\n".join(
        (
            "System monitoringu wykryl problem wymagajacy uwagi.",
            "",
            "Co wykryto:",
            summary,
            "",
            "Host/usluga:",
            host,
            "",
            "Kategoria:",
            category,
            "",
            "Priorytet:",
            label,
            "",
            "Od kiedy:",
            started_at,
            "",
            "Znaczenie:",
            _impact_hint(category, severity_key),
            "",
            "Sugerowany pierwszy krok:",
            _first_step_hint(category),
            "",
            "Szczegoly techniczne:",
            f"- Zrodlo: {source}",
            f"- Raw severity / level: {_bounded_text(event.raw_severity, 80)}",
            f"- Raw trigger / rule: {raw_trigger}",
            f"- Event ID: {_bounded_text(event.event_id, 120)}",
            f"- Link do zrodla: {source_url}",
            "",
            "Uwagi:",
            "Nie wykonywac dzialan destrukcyjnych bez potwierdzenia operatora.",
        )
    )

    return TicketDraft(
        dedupe_key=event.dedupe_key,
        title=_bounded_text(title, 255),
        content=content,
        category=category,
        urgency=glpi_urgency(severity_key),
        source=source,
        source_event_id=event.event_id,
    )


class TicketState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data = _load_state(path)

    def seen(self, dedupe_key: str) -> bool:
        return dedupe_key in self._data.get("routed", {})

    def mark(self, draft: TicketDraft, *, glpi_ticket_id: int | None = None) -> None:
        routed = self._data.setdefault("routed", {})
        routed[draft.dedupe_key] = {
            "source": draft.source,
            "source_event_id": draft.source_event_id,
            "glpi_ticket_id": glpi_ticket_id,
            "routed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, sort_keys=True), encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(self.path)
        os.chmod(self.path, 0o600)


class GlpiClient:
    def __init__(
        self,
        *,
        api_url: str,
        app_token: str,
        user_token: str,
        timeout_seconds: int = 15,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.app_token = app_token
        self.user_token = user_token
        self.timeout_seconds = timeout_seconds

    def create_ticket(self, draft: TicketDraft) -> int:
        session_token = self._init_session()
        ticket_id: int | None = None
        try:
            response = self._request_json(
                "POST",
                f"{self.api_url}/Ticket",
                draft.glpi_payload(),
                session_token=session_token,
            )
            if not isinstance(response, dict):
                raise RuntimeError("glpi_ticket_response_not_object")
            ticket_id = response.get("id")
            if not isinstance(ticket_id, int):
                raise RuntimeError("glpi_ticket_response_missing_id")
            return ticket_id
        finally:
            try:
                self._kill_session(session_token)
            except RuntimeError:
                if ticket_id is None:
                    raise

    def _init_session(self) -> str:
        response = self._request_json("GET", f"{self.api_url}/initSession", None)
        if not isinstance(response, dict):
            raise RuntimeError("glpi_init_session_response_not_object")
        session_token = response.get("session_token")
        if not isinstance(session_token, str) or not session_token:
            raise RuntimeError("glpi_init_session_missing_session_token")
        return session_token

    def _kill_session(self, session_token: str) -> None:
        self._request_json("GET", f"{self.api_url}/killSession", None, session_token=session_token)

    def _request_json(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None,
        *,
        session_token: str | None = None,
    ) -> Any:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "App-Token": self.app_token,
            "Author" + "ization": "user_token " + self.user_token,
        }
        if session_token:
            headers["Session-Token"] = session_token
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"glpi_http_error:{exc.code}:{_bounded_text(message, 200)}") from exc
        value = json.loads(data or "{}")
        return value


def load_events(path: Path) -> list[AlertEvent]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        raw = json.loads(text)
    else:
        raw = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(raw, list):
        raise ValueError("events_input_must_be_json_array_or_ndjson")
    return [event_from_mapping(item) for item in raw]


def event_from_mapping(value: object) -> AlertEvent:
    if not isinstance(value, dict):
        raise ValueError("event_must_be_object")
    return AlertEvent(
        source=_bounded_text(value.get("source"), 24),
        event_id=_bounded_text(value.get("event_id"), 120),
        host=_bounded_text(value.get("host"), 128),
        summary=_bounded_text(value.get("summary"), 180),
        raw_severity=_bounded_text(value.get("raw_severity"), 80),
        raw_trigger=_bounded_text(value.get("raw_trigger"), 240),
        started_at=_bounded_text(value.get("started_at"), 80),
        source_url=_bounded_text(value.get("source_url"), 300),
        category=_bounded_text(value.get("category"), 80),
    )


def route_events(
    events: list[AlertEvent],
    state: TicketState,
    *,
    client: GlpiClient | None = None,
    dry_run: bool = True,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for event in events:
        draft = build_ticket_draft(event)
        if state.seen(draft.dedupe_key):
            results.append({"dedupe_key": draft.dedupe_key, "status": "duplicate"})
            continue
        if dry_run:
            results.append(
                {
                    "dedupe_key": draft.dedupe_key,
                    "status": "dry_run",
                    "title": draft.title,
                    "category": draft.category,
                    "urgency": draft.urgency,
                }
            )
            continue
        if client is None:
            raise ValueError("client_required_when_dry_run_is_false")
        ticket_id = client.create_ticket(draft)
        state.mark(draft, glpi_ticket_id=ticket_id)
        results.append(
            {
                "dedupe_key": draft.dedupe_key,
                "status": "created",
                "glpi_ticket_id": ticket_id,
            }
        )
    return results


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"routed": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        return {"routed": {}}
    routed = value.get("routed")
    if not isinstance(routed, dict):
        value["routed"] = {}
    return value


def _bounded_text(value: object, limit: int) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.replace("\r", " ").splitlines()).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _impact_hint(category: str, severity_key: str) -> str:
    if severity_key in {"disaster", "high"}:
        return "Problem moze istotnie wplywac na ciaglosc pracy lub bezpieczenstwo uslugi."
    if category == "Dysk / miejsce":
        return "Rosnace zuzycie miejsca moze zatrzymac usluge albo przerwac zapis danych."
    if category == "Bezpieczenstwo":
        return "Zdarzenie wymaga weryfikacji, czy nie oznacza proby naruszenia bezpieczenstwa."
    return "Problem wymaga sprawdzenia, ale nie musi oznaczac natychmiastowej awarii."


def _first_step_hint(category: str) -> str:
    if category == "Dysk / miejsce":
        return "Sprawdz uzycie wolumenow i potwierdz, czy wzrost jest oczekiwany."
    if category == "Bezpieczenstwo":
        return "Zweryfikuj zdarzenie w Wazuh i sprawdz powiazany host/uzytkownika."
    if category == "Dostepnosc":
        return "Sprawdz dostepnosc hosta z monitoringu i z sieci administracyjnej."
    return "Otworz system zrodlowy i potwierdz aktualny stan alertu."
