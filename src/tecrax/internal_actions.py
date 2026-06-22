from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rexecop.execution.backend import StepExecutionContext


def register_handlers() -> Mapping[str, Any]:
    return {
        "environment.resolve_targets": resolve_targets,
        "correlate_vm_backup_coverage": correlate_vm_backup_coverage,
        "capture_agent_state": capture_agent_state,
        "verify_agent_state": verify_agent_state,
        "normalize_basic_host_inventory": normalize_basic_host_inventory,
        "normalize_ntp_health": normalize_ntp_health,
        "normalize_zabbix_health": normalize_zabbix_health,
    }


def resolve_targets(context: StepExecutionContext) -> dict[str, Any]:
    return {
        "target": context.target,
        "resolved_targets": ["vm-101", "vm-102"],
    }


def correlate_vm_backup_coverage(context: StepExecutionContext) -> dict[str, Any]:
    connector_results = context.shared_state.get("connector_results", {})
    vms: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    for payload in connector_results.values():
        if isinstance(payload, dict):
            vms.extend(payload.get("vms", []))
            snapshots.extend(payload.get("snapshots", []))
    covered = {item.get("vm_id") for item in snapshots}
    rows = []
    for vm in vms:
        vm_id = vm.get("id")
        rows.append(
            {
                "vm_id": vm_id,
                "name": vm.get("name"),
                "backup_status": "ok" if vm_id in covered else "missing",
            }
        )
    result = {
        "rows": rows,
        "all_critical_covered": all(row["backup_status"] == "ok" for row in rows),
    }
    context.shared_state["correlation"] = result
    return result


def capture_agent_state(context: StepExecutionContext) -> dict[str, Any]:
    state = {
        "target": context.target,
        "agent_status": "running",
        "vm_id": "vm-101",
    }
    context.shared_state["agent_before_state"] = dict(state)
    return {"before_state": state}


def verify_agent_state(context: StepExecutionContext) -> dict[str, Any]:
    mutation = context.shared_state.get("mutation_states", {}).get("restart_agent", {})
    after_state = mutation.get("after_state") if isinstance(mutation, dict) else None
    if not isinstance(after_state, dict):
        return {
            "verified": False,
            "reason": "missing restart mutation after_state",
        }
    context.shared_state["agent_after_state"] = dict(after_state)
    return {
        "verified": after_state.get("agent_status") == "restarted",
        "after_state": after_state,
        "before_state": context.shared_state.get("agent_before_state"),
    }


def normalize_basic_host_inventory(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}

    os_release = _parse_os_release(_stdout(results, "read_os_release"))
    filesystem = _parse_df(_stdout(results, "read_filesystem_usage"))
    memory = _parse_free(_stdout(results, "read_memory_summary"))
    inventory = {
        "target": context.target,
        "os": os_release,
        "kernel": _single_line(_stdout(results, "read_kernel_identity")),
        "hostname": _single_line(_stdout(results, "read_hostname")),
        "uptime": _single_line(_stdout(results, "read_uptime")),
        "root_filesystem": filesystem,
        "memory_mib": memory,
    }
    inventory["complete"] = all(
        (
            os_release.get("id"),
            inventory["kernel"],
            inventory["hostname"],
            inventory["uptime"],
            filesystem.get("mounted_on") == "/",
            memory.get("total") is not None,
        )
    )
    context.shared_state["basic_host_inventory"] = inventory
    return inventory


def normalize_ntp_health(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}
    properties = _parse_properties(_stdout(results, "read_ntp_sync_state"))
    service_state = _single_line(_stdout(results, "read_ntp_service_state"), limit=32)
    result = {
        "synchronized": properties.get("NTPSynchronized", "").lower() == "yes",
        "systemd_ntp_enabled": properties.get("NTP", "").lower() == "yes",
        "service": "ntp",
        "service_state": service_state,
    }
    result["healthy"] = result["synchronized"] and service_state == "active"
    context.shared_state["ntp_health"] = result
    return result


def normalize_zabbix_health(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    payload = results.get("read_zabbix_api_version") if isinstance(results, dict) else None
    if not isinstance(payload, dict):
        payload = {}
    version = str(payload.get("result") or "").strip()[:64]
    result = {
        "application_reachable": bool(version) and not payload.get("error"),
        "api_version": version,
        "container_runtime_state": "not_observed",
    }
    result["healthy"] = result["application_reachable"]
    context.shared_state["zabbix_health"] = result
    return result


def _stdout(results: dict[str, Any], step_id: str) -> str:
    payload = results.get(step_id)
    if not isinstance(payload, dict):
        return ""
    value = payload.get("stdout")
    return str(value) if value is not None else ""


def _single_line(value: str, *, limit: int = 512) -> str:
    return " ".join(value.split())[:limit]


def _parse_os_release(value: str) -> dict[str, str]:
    allowed = {"ID", "VERSION_ID", "PRETTY_NAME"}
    parsed: dict[str, str] = {}
    for line in value.splitlines():
        key, separator, raw = line.partition("=")
        if not separator or key not in allowed:
            continue
        parsed[key.lower()] = raw.strip().strip('"')[:256]
    return parsed


def _parse_properties(value: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in value.splitlines():
        key, separator, raw = line.partition("=")
        if separator and key in {"NTP", "NTPSynchronized"}:
            parsed[key] = raw.strip()[:32]
    return parsed


def _parse_df(value: str) -> dict[str, Any]:
    lines = [line.split() for line in value.splitlines() if line.strip()]
    if len(lines) < 2 or len(lines[-1]) < 6:
        return {}
    row = lines[-1]
    return {
        "filesystem": row[0][:256],
        "blocks_1024": _integer(row[1]),
        "used": _integer(row[2]),
        "available": _integer(row[3]),
        "capacity": row[4][:16],
        "mounted_on": row[5][:256],
    }


def _parse_free(value: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in value.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0] != "Mem:":
            continue
        result = {
            "total": _integer(parts[1]),
            "used": _integer(parts[2]),
            "free": _integer(parts[3]),
        }
        if len(parts) >= 7:
            result["available"] = _integer(parts[6])
        break
    return result


def _integer(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
