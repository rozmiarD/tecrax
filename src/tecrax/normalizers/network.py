from __future__ import annotations

from typing import Any

from rexecop.execution.backend import StepExecutionContext

from tecrax.contracts import (
    build_network_device_inventory_v1,
    build_network_management_posture_v1,
)
from tecrax.normalizers.common import (
    connector_results,
    integer,
    single_line,
    store_facts,
    stdout,
)


def normalize_network_device_inventory(context: StepExecutionContext) -> dict[str, Any]:
    results = connector_results(context)
    system_info = _parse_colon_fields(stdout(results, "read_network_device_system_info"))
    ssh_status = _parse_colon_fields(stdout(results, "read_network_device_ssh_status"))
    protocol_v1 = _enabled_value(
        ssh_status.get("SSH Server Protocol V1") or ssh_status.get("Protocol V1")
    )
    protocol_v2 = _enabled_value(
        ssh_status.get("SSH Server Protocol V2") or ssh_status.get("Protocol V2")
    )
    result = {
        "target": context.target,
        "observation_scope": "network_cli_readonly",
        "device": {
            "system_name": _bounded_field(system_info.get("System Name"), 128),
            "system_description": _bounded_field(
                system_info.get("System Description"), 256
            ),
            "hardware_version": _bounded_field(system_info.get("Hardware Version"), 128),
            "software_version": _bounded_field(system_info.get("Software Version"), 128),
        },
        "management_access": {
            "ssh_server_enabled": _enabled_value(ssh_status.get("SSH Server")),
            "ssh_protocol_v1_enabled": protocol_v1,
            "ssh_protocol_v2_enabled": protocol_v2,
            "idle_timeout_seconds": integer(
                str(
                    ssh_status.get("SSH Idle Timeout")
                    or ssh_status.get("Idle Timeout")
                    or ""
                )
            ),
            "max_clients": integer(
                str(ssh_status.get("SSH MAX Client") or ssh_status.get("MAX Clients") or "")
            ),
        },
        "hardening_observations": {
            "legacy_ssh_v1_enabled": protocol_v1 is True,
            "legacy_crypto_observed": "CBC"
            in stdout(results, "read_network_device_ssh_status").upper(),
            "mutations_observed": False,
        },
    }
    device = result["device"]
    management = result["management_access"]
    result["complete"] = all(
        (
            device["system_name"],
            device["hardware_version"],
            device["software_version"],
            management["ssh_server_enabled"] is not None,
            management["ssh_protocol_v2_enabled"] is not None,
        )
    )
    facts = build_network_device_inventory_v1(result)
    return store_facts(context, "network_device_inventory", facts)


def assess_network_device_management_posture(
    context: StepExecutionContext,
) -> dict[str, Any]:
    inventory = context.shared_state.get("network_device_inventory")
    if not isinstance(inventory, dict):
        inventory = {}
    management = inventory.get("management_access")
    hardening = inventory.get("hardening_observations")
    management = management if isinstance(management, dict) else {}
    hardening = hardening if isinstance(hardening, dict) else {}
    findings: list[dict[str, str]] = []
    if hardening.get("legacy_ssh_v1_enabled") is True:
        findings.append({"reason_code": "legacy_ssh_v1_enabled", "severity": "high"})
    if hardening.get("legacy_crypto_observed") is True:
        findings.append({"reason_code": "legacy_ssh_crypto_observed", "severity": "medium"})
    idle_timeout = management.get("idle_timeout_seconds")
    if not isinstance(idle_timeout, int) or idle_timeout <= 0:
        findings.append({"reason_code": "ssh_idle_timeout_unknown", "severity": "low"})
    complete = bool(inventory.get("complete"))
    facts = build_network_management_posture_v1(
        source_inventory_contract=inventory.get("contract"),
        findings=findings,
        complete=complete,
    )
    return store_facts(context, "network_management_posture", facts)


def _parse_colon_fields(value: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in value.splitlines():
        key, separator, raw = line.partition(":")
        if not separator:
            key, separator, raw = line.partition("-")
        if not separator:
            continue
        normalized_key = " ".join(key.split())
        if normalized_key:
            parsed[normalized_key] = " ".join(raw.split())[:512]
    return parsed


def _bounded_field(value: Any, limit: int) -> str:
    return single_line(str(value or ""), limit=limit)


def _enabled_value(value: Any) -> bool | None:
    text = str(value or "").strip().lower()
    if text == "enabled":
        return True
    if text == "disabled":
        return False
    return None
