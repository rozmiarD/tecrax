from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rexecop.execution.backend import StepExecutionContext

from tecrax.contracts import build_basic_host_inventory_v1, finalize_facts


def register_handlers() -> Mapping[str, Any]:
    return {
        "normalize_basic_host_inventory": normalize_basic_host_inventory,
        "normalize_ntp_health": normalize_ntp_health,
        "normalize_docker_services_health": normalize_docker_services_health,
        "normalize_zabbix_health": normalize_zabbix_health,
        "normalize_adguard_health": normalize_adguard_health,
        "normalize_portainer_health": normalize_portainer_health,
        "normalize_network_device_inventory": normalize_network_device_inventory,
        "normalize_host_security_posture": normalize_host_security_posture,
        "normalize_ntp_server_observation": normalize_ntp_server_observation,
        "assess_network_device_management_posture": assess_network_device_management_posture,
        "aggregate_monitoring_host_diagnosis": aggregate_monitoring_host_diagnosis,
    }


def normalize_basic_host_inventory(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}

    os_release = _parse_os_release(_stdout(results, "read_os_release"))
    filesystem = _parse_df(_stdout(results, "read_filesystem_usage"))
    memory = _parse_free(_stdout(results, "read_memory_summary"))
    load_average = _parse_loadavg(_stdout(results, "read_load_average"))
    inventory = build_basic_host_inventory_v1(
        target=context.target,
        os=os_release,
        kernel=_single_line(_stdout(results, "read_kernel_identity")),
        hostname=_single_line(_stdout(results, "read_hostname")),
        uptime=_single_line(_stdout(results, "read_uptime")),
        load_average=load_average,
        root_filesystem=filesystem,
        memory_mib=memory,
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
    result = finalize_facts(
        result,
        contract_id="tecrax.ntp_local_health",
        requested=["local_synchronization", "daemon_state"],
        observed=["local_synchronization", "daemon_state"],
        assessment="healthy" if result["healthy"] else "unhealthy",
        non_claims=["server_serving_state", "peer_identity", "offset", "stratum"],
    )
    context.shared_state["ntp_health"] = result
    return result


def normalize_host_security_posture(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}
    unattended = _single_line(_stdout(results, "read_unattended_upgrades_state"), limit=32)
    aslr = _integer(_single_line(_stdout(results, "read_aslr_state"), limit=8))
    dmesg = _integer(_single_line(_stdout(results, "read_dmesg_restrict_state"), limit=8))
    reboot_marker = _single_line(_stdout(results, "read_reboot_required_marker"), limit=32)
    signals = {
        "unattended_upgrades_enabled": unattended == "enabled",
        "aslr_mode": aslr,
        "dmesg_restrict": dmesg,
        "reboot_required": reboot_marker == "reboot-required",
    }
    complete = unattended in {"enabled", "disabled", "static", "masked"} and aslr is not None and dmesg is not None
    healthy = complete and signals["unattended_upgrades_enabled"] and aslr == 2 and dmesg == 1
    result = finalize_facts(
        {"signals": signals, "complete": complete, "healthy": healthy},
        contract_id="tecrax.host_security_posture",
        requested=["unattended_upgrades", "aslr", "dmesg_restrict", "reboot_required"],
        observed=["unattended_upgrades", "aslr", "dmesg_restrict", "reboot_required"] if complete else [],
        not_observed=[] if complete else ["one_or_more_security_signals"],
        assessment="healthy" if healthy else ("degraded" if complete else "unknown"),
        non_claims=["cis_compliance", "users", "packages", "ports", "ssh_configuration"],
    )
    context.shared_state["host_security_posture"] = result
    return result


def normalize_ntp_server_observation(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}
    daemon_state = _single_line(_stdout(results, "read_ntp_service_state"), limit=32)
    variables = _parse_ntp_variables(_stdout(results, "read_ntp_server_variables"))
    stratum = _integer(variables.get("stratum", ""))
    leap = _integer(variables.get("leap", ""))
    complete = daemon_state == "active" and stratum is not None and leap is not None
    healthy = complete and 1 <= int(stratum) <= 15 and leap != 3
    result = finalize_facts(
        {
            "daemon_state": daemon_state,
            "serving_state": "local_daemon_query_available" if variables else "unknown",
            "system_variables": {
                "stratum": stratum,
                "leap": leap,
                "offset_ms": _bounded_float(variables.get("offset")),
                "root_delay_ms": _bounded_float(variables.get("rootdelay")),
                "root_dispersion_ms": _bounded_float(variables.get("rootdisp")),
            },
            "healthy": healthy,
        },
        contract_id="tecrax.ntp_server_observation",
        requested=["daemon_state", "stratum", "leap", "offset", "root_delay", "root_dispersion"],
        observed=["daemon_state", "stratum", "leap", "offset", "root_delay", "root_dispersion"] if complete else [],
        not_observed=[] if complete else ["one_or_more_ntp_server_fields"],
        assessment="healthy" if healthy else ("degraded" if complete else "unknown"),
        non_claims=["peer_identity", "peer_address", "remote_client_reachability", "firewall_state"],
    )
    context.shared_state["ntp_server_observation"] = result
    return result


def normalize_docker_services_health(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}
    service = _parse_systemctl_show(_stdout(results, "read_docker_service_state"))
    socket = _parse_systemctl_show(_stdout(results, "read_docker_socket_state"))
    result = {
        "observation_scope": "systemd_service_only",
        "service": "docker",
        "service_load_state": service.get("LoadState", ""),
        "service_active_state": service.get("ActiveState", ""),
        "service_sub_state": service.get("SubState", ""),
        "service_unit_file_state": service.get("UnitFileState", ""),
        "socket": "docker.socket",
        "socket_load_state": socket.get("LoadState", ""),
        "socket_active_state": socket.get("ActiveState", ""),
        "socket_sub_state": socket.get("SubState", ""),
        "socket_unit_file_state": socket.get("UnitFileState", ""),
        "container_runtime_state": "not_observed",
    }
    result["healthy"] = (
        result["service_load_state"] == "loaded"
        and result["service_active_state"] == "active"
    )
    result = finalize_facts(
        result,
        contract_id="tecrax.docker_service_health",
        requested=["docker.service", "docker.socket"],
        observed=["docker.service", "docker.socket"],
        not_observed=["containers", "images", "stacks"],
        assessment="healthy" if result["healthy"] else "unhealthy",
        non_claims=["container_health", "docker_socket", "container_logs"],
    )
    context.shared_state["docker_services_health"] = result
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
    result = finalize_facts(
        result,
        contract_id="tecrax.zabbix_api_reachability",
        requested=["api_reachability"],
        observed=["api_reachability"] if result["application_reachable"] else [],
        not_observed=["container_runtime", "problems", "hosts", "configuration"],
        assessment="healthy" if result["healthy"] else "unhealthy",
        non_claims=["container_health", "monitoring_health", "authenticated_api"],
    )
    context.shared_state["zabbix_health"] = result
    return result


def normalize_adguard_health(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}
    dns_stdout = _stdout(results, "read_adguard_dns_resolution")
    login_status = _single_line(_stdout(results, "read_adguard_login_status"), limit=16)
    dns_answer_count = sum(
        1
        for line in dns_stdout.splitlines()
        if line.strip() and not line.lstrip().startswith(";")
    )
    result = {
        "observation_scope": "dns_and_web_login_only",
        "dns_resolves": dns_answer_count > 0,
        "dns_answer_count": min(dns_answer_count, 32),
        "web_login_http_status": login_status,
        "management_api_state": "not_observed",
        "container_runtime_state": "not_observed",
    }
    result["web_login_reachable"] = login_status in {"200", "302"}
    result["healthy"] = result["dns_resolves"] and result["web_login_reachable"]
    result = finalize_facts(
        result,
        contract_id="tecrax.adguard_reachability",
        requested=["dns_resolution", "web_login_reachability"],
        observed=["dns_resolution", "web_login_reachability"],
        not_observed=["management_api", "configuration", "clients"],
        assessment="healthy" if result["healthy"] else "unhealthy",
        non_claims=["filter_effectiveness", "upstream_health", "container_health"],
    )
    context.shared_state["adguard_health"] = result
    return result


def normalize_portainer_health(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    payload = results.get("read_portainer_status") if isinstance(results, dict) else None
    if not isinstance(payload, dict):
        payload = {}
    version = str(payload.get("Version") or "").strip()[:64]
    result = {
        "observation_scope": "unauthenticated_status_only",
        "api_reachable": bool(version),
        "api_version": version,
        "instance_identity_state": "deliberately_not_collected",
        "management_objects_state": "not_observed",
        "container_runtime_state": "not_observed",
    }
    result["healthy"] = result["api_reachable"]
    result = finalize_facts(
        result,
        contract_id="tecrax.portainer_reachability",
        requested=["unauthenticated_status"],
        observed=["unauthenticated_status"] if result["api_reachable"] else [],
        not_observed=["environments", "stacks", "containers", "users"],
        assessment="healthy" if result["healthy"] else "unhealthy",
        non_claims=["management_plane_health", "container_health", "authenticated_api"],
    )
    context.shared_state["portainer_health"] = result
    return result


def normalize_network_device_inventory(context: StepExecutionContext) -> dict[str, Any]:
    results = context.shared_state.get("connector_results", {})
    if not isinstance(results, dict):
        results = {}
    system_info = _parse_colon_fields(_stdout(results, "read_network_device_system_info"))
    ssh_status = _parse_colon_fields(_stdout(results, "read_network_device_ssh_status"))
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
            "idle_timeout_seconds": _integer(
                str(ssh_status.get("SSH Idle Timeout") or ssh_status.get("Idle Timeout") or "")
            ),
            "max_clients": _integer(
                str(ssh_status.get("SSH MAX Client") or ssh_status.get("MAX Clients") or "")
            ),
        },
        "hardening_observations": {
            "legacy_ssh_v1_enabled": protocol_v1 is True,
            "legacy_crypto_observed": "CBC" in _stdout(
                results, "read_network_device_ssh_status"
            ).upper(),
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
    result = finalize_facts(
        result,
        contract_id="tecrax.network_device_inventory",
        requested=["device_identity", "ssh_management_posture"],
        observed=["device_identity", "ssh_management_posture"] if result["complete"] else [],
        not_observed=[] if result["complete"] else ["one_or_more_device_fields"],
        assessment="healthy" if result["complete"] else "unknown",
        non_claims=["running_configuration", "vlans", "ports", "snmp_telemetry"],
    )
    context.shared_state["network_device_inventory"] = result
    return result


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
    assessment = "degraded" if findings and complete else ("healthy" if complete else "unknown")
    result = finalize_facts(
        {
            "source_inventory_contract": inventory.get("contract"),
            "findings": findings[:16],
            "complete": complete,
        },
        contract_id="tecrax.network_management_posture",
        requested=["ssh_protocols", "ssh_crypto", "idle_timeout"],
        observed=["ssh_protocols", "ssh_crypto", "idle_timeout"] if complete else [],
        not_observed=[] if complete else ["one_or_more_management_fields"],
        assessment=assessment,
        non_claims=["running_configuration", "port_security", "vlans", "firmware_compliance"],
    )
    context.shared_state["network_management_posture"] = result
    return result


def aggregate_monitoring_host_diagnosis(
    context: StepExecutionContext,
) -> dict[str, Any]:
    inventory = context.shared_state.get("basic_host_inventory")
    ntp = context.shared_state.get("ntp_health")
    docker = context.shared_state.get("docker_services_health")
    zabbix = context.shared_state.get("zabbix_health")
    adguard = context.shared_state.get("adguard_health")
    portainer = context.shared_state.get("portainer_health")
    security = context.shared_state.get("host_security_posture")
    ntp_server = context.shared_state.get("ntp_server_observation")
    continued = context.shared_state.get("continued_failures")
    failures = []
    if isinstance(continued, dict):
        for step_id, payload in sorted(continued.items()):
            error_class = payload.get("error_class") if isinstance(payload, dict) else ""
            failures.append(
                {"step_id": str(step_id)[:128], "error_class": str(error_class)[:64]}
            )

    components = {
        "host_inventory": _component_status(inventory, "complete"),
        "ntp": _component_status(ntp, "healthy"),
        "zabbix": _component_status(zabbix, "healthy"),
        "docker": _component_status(docker, "healthy", unavailable_reason="not_observed"),
        "adguard": _component_status(
            adguard,
            "healthy",
            unavailable_reason="not_observed",
        ),
        "portainer": _component_status(
            portainer,
            "healthy",
            unavailable_reason="not_observed",
        ),
        "host_security": _component_status(security, "healthy"),
        "ntp_server": _component_status(ntp_server, "healthy"),
    }
    observed = [
        components[name]["status"]
        for name in (
            "host_inventory",
            "ntp",
            "docker",
            "zabbix",
            "adguard",
            "portainer",
            "host_security",
            "ntp_server",
        )
    ]
    assessment = "healthy" if all(item == "healthy" for item in observed) else "degraded"
    result = finalize_facts(
        {
        "aggregation_completed": True,
        "coverage_status": "partial" if failures else "complete",
        "observed_health": "healthy" if all(item == "healthy" for item in observed) else "degraded",
        "components": components,
        "continued_failures": failures,
        },
        contract_id="tecrax.monitoring_host_diagnosis",
        requested=list(components),
        observed=[name for name, value in components.items() if value["status"] != "unavailable"],
        not_observed=[name for name, value in components.items() if value["status"] == "unavailable"],
        assessment=assessment,
        non_claims=["continuous_monitoring", "root_cause", "automatic_remediation"],
    )
    context.shared_state["monitoring_host_diagnosis"] = result
    return result


def _component_status(
    value: Any, health_key: str, *, unavailable_reason: str = ""
) -> dict[str, str]:
    if not isinstance(value, dict):
        result = {"status": "unavailable"}
        if unavailable_reason:
            result["reason"] = unavailable_reason
        return result
    return {"status": "healthy" if value.get(health_key) is True else "unhealthy"}


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


def _parse_ntp_variables(value: str) -> dict[str, str]:
    allowed = {"stratum", "offset", "rootdelay", "rootdisp", "leap"}
    parsed: dict[str, str] = {}
    for part in value.replace("\n", " ").split(","):
        key, separator, raw = part.strip().partition("=")
        if separator and key in allowed:
            parsed[key] = raw.strip()[:32]
    return parsed


def _bounded_float(value: Any) -> float | None:
    try:
        result = float(str(value))
    except (TypeError, ValueError):
        return None
    return round(max(-1_000_000.0, min(result, 1_000_000.0)), 6)


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
    return _single_line(str(value or ""), limit=limit)


def _enabled_value(value: Any) -> bool | None:
    text = str(value or "").strip().lower()
    if text == "enabled":
        return True
    if text == "disabled":
        return False
    return None


def _parse_systemctl_show(value: str) -> dict[str, str]:
    allowed = {"LoadState", "ActiveState", "SubState", "UnitFileState"}
    parsed: dict[str, str] = {}
    for line in value.splitlines():
        key, separator, raw = line.partition("=")
        if separator and key in allowed:
            parsed[key] = raw.strip()[:64]
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


def _parse_loadavg(value: str) -> dict[str, Any]:
    parts = value.split()
    if len(parts) < 5:
        return {}
    process_counts = parts[3].split("/", 1)
    return {
        "one_minute": _float(parts[0]),
        "five_minutes": _float(parts[1]),
        "fifteen_minutes": _float(parts[2]),
        "runnable_processes": _integer(process_counts[0]) if process_counts else None,
        "total_processes": _integer(process_counts[1]) if len(process_counts) == 2 else None,
    }


def _integer(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
