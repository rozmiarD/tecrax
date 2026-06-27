from __future__ import annotations

from typing import Any

from rexecop.execution.backend import StepExecutionContext

from tecrax.contracts import (
    build_network_device_inventory_v1,
    build_network_management_posture_v1,
)
from tecrax.normalizers.common import (
    connector_results,
    store_facts,
    stdout,
)
from tecrax.normalizers.network_parsers import parse_network_device_cli


def normalize_network_device_inventory(context: StepExecutionContext) -> dict[str, Any]:
    results = connector_results(context)
    parsed = parse_network_device_cli(
        system_info_output=stdout(results, "read_network_device_system_info"),
        ssh_status_output=stdout(results, "read_network_device_ssh_status"),
    )
    device = parsed.device
    management = parsed.management_access
    complete = all(
        (
            parsed.supported,
            device["system_name"],
            device["hardware_version"],
            device["software_version"],
            management["ssh_server_enabled"] is not None,
            management["ssh_protocol_v2_enabled"] is not None,
        )
    )
    result = {
        "target": context.target,
        "observation_scope": "network_cli_readonly",
        "device": device,
        "management_access": management,
        "hardening_observations": parsed.hardening_observations,
        "complete": complete,
    }
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
    if management.get("ssh_server_enabled") is False:
        findings.append({"reason_code": "ssh_server_disabled", "severity": "medium"})
    if management.get("ssh_protocol_v2_enabled") is False:
        findings.append({"reason_code": "ssh_protocol_v2_disabled", "severity": "high"})
    if hardening.get("legacy_ssh_v1_enabled") is True:
        findings.append({"reason_code": "legacy_ssh_v1_enabled", "severity": "high"})
    if hardening.get("legacy_crypto_observed") is True:
        findings.append({"reason_code": "legacy_ssh_crypto_observed", "severity": "medium"})
    idle_timeout = management.get("idle_timeout_seconds")
    if not isinstance(idle_timeout, int) or idle_timeout <= 0:
        findings.append({"reason_code": "ssh_idle_timeout_unknown", "severity": "low"})
    max_clients = management.get("max_clients")
    if not isinstance(max_clients, int) or max_clients <= 0:
        findings.append({"reason_code": "ssh_max_clients_unknown", "severity": "low"})
    complete = bool(inventory.get("complete"))
    facts = build_network_management_posture_v1(
        source_inventory_contract=inventory.get("contract"),
        findings=findings,
        complete=complete,
    )
    return store_facts(context, "network_management_posture", facts)
