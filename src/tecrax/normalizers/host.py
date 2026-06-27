from __future__ import annotations

from typing import Any

from rexecop.execution.backend import StepExecutionContext

from tecrax.contracts import (
    build_basic_host_inventory_v1,
    build_host_security_posture_v1,
    build_ntp_server_observation_v1,
)
from tecrax.normalizers.common import (
    bounded_float,
    connector_results,
    float_value,
    integer,
    single_line,
    store_facts,
    stdout,
)


def normalize_basic_host_inventory(context: StepExecutionContext) -> dict[str, Any]:
    results = connector_results(context)

    os_release = _parse_os_release(stdout(results, "read_os_release"))
    filesystem = _parse_df(stdout(results, "read_filesystem_usage"))
    memory = _parse_free(stdout(results, "read_memory_summary"))
    load_average = _parse_loadavg(stdout(results, "read_load_average"))
    inventory = build_basic_host_inventory_v1(
        target=context.target,
        os=os_release,
        kernel=single_line(stdout(results, "read_kernel_identity")),
        hostname=single_line(stdout(results, "read_hostname")),
        uptime=single_line(stdout(results, "read_uptime")),
        load_average=load_average,
        root_filesystem=filesystem,
        memory_mib=memory,
    )
    return store_facts(context, "basic_host_inventory", inventory)


def normalize_host_security_posture(context: StepExecutionContext) -> dict[str, Any]:
    results = connector_results(context)
    unattended = single_line(stdout(results, "read_unattended_upgrades_state"), limit=32)
    available_updates = _parse_update_summary(
        _connector_text(results, "read_available_updates_summary")
    )
    aslr = integer(single_line(stdout(results, "read_aslr_state"), limit=8))
    dmesg = integer(single_line(stdout(results, "read_dmesg_restrict_state"), limit=8))
    reboot_marker = single_line(stdout(results, "read_reboot_required_marker"), limit=32)
    signals = {
        "unattended_upgrades_enabled": unattended == "enabled",
        "available_updates": available_updates,
        "aslr_mode": aslr,
        "dmesg_restrict": dmesg,
        "reboot_required": reboot_marker == "reboot-required",
    }
    unattended_upgrades_enabled = unattended == "enabled"
    reboot_required = reboot_marker == "reboot-required"
    complete = (
        unattended in {"enabled", "disabled", "static", "masked"}
        and available_updates["unknown"] == 0
        and aslr is not None
        and dmesg is not None
    )
    healthy = (
        complete
        and unattended_upgrades_enabled
        and available_updates["security"] == 0
        and not reboot_required
        and aslr == 2
        and dmesg == 1
    )
    facts = build_host_security_posture_v1(
        signals=signals,
        complete=complete,
        healthy=healthy,
    )
    return store_facts(context, "host_security_posture", facts)


def normalize_ntp_server_observation(context: StepExecutionContext) -> dict[str, Any]:
    results = connector_results(context)
    daemon_state = single_line(stdout(results, "read_ntp_service_state"), limit=32)
    variables = _parse_ntp_variables(stdout(results, "read_ntp_server_variables"))
    stratum = integer(variables.get("stratum", ""))
    leap = integer(variables.get("leap", ""))
    complete = daemon_state == "active" and stratum is not None and leap is not None
    healthy = (
        stratum is not None
        and leap is not None
        and complete
        and 1 <= stratum <= 15
        and leap != 3
    )
    facts = build_ntp_server_observation_v1(
        daemon_state=daemon_state,
        serving_state="local_daemon_query_available" if variables else "unknown",
        system_variables={
            "stratum": stratum,
            "leap": leap,
            "offset_ms": bounded_float(variables.get("offset")),
            "root_delay_ms": bounded_float(variables.get("rootdelay")),
            "root_dispersion_ms": bounded_float(variables.get("rootdisp")),
        },
        healthy=healthy,
    )
    return store_facts(context, "ntp_server_observation", facts)


def _parse_os_release(value: str) -> dict[str, str]:
    allowed = {"ID", "VERSION_ID", "PRETTY_NAME"}
    parsed: dict[str, str] = {}
    for line in value.splitlines():
        key, separator, raw = line.partition("=")
        if not separator or key not in allowed:
            continue
        parsed[key.lower()] = raw.strip().strip('"')[:256]
    return parsed


def _parse_ntp_variables(value: str) -> dict[str, str]:
    allowed = {"stratum", "offset", "rootdelay", "rootdisp", "leap"}
    parsed: dict[str, str] = {}
    for part in value.replace("\n", " ").split(","):
        key, separator, raw = part.strip().partition("=")
        if separator and key in allowed:
            parsed[key] = raw.strip()[:32]
    return parsed


def _connector_text(results: dict[str, Any], step_id: str) -> str:
    payload = results.get(step_id)
    if not isinstance(payload, dict):
        return ""
    return "\n".join(
        str(payload.get(key) or "")
        for key in ("stdout", "stderr")
        if payload.get(key) is not None
    )


def _parse_update_summary(value: str) -> dict[str, int | None]:
    text = single_line(value, limit=256)
    total: int | None = None
    security: int | None = None
    if ";" in text:
        parts = [part.strip() for part in text.split(";")]
        if len(parts) >= 2:
            total = integer(parts[0])
            security = integer(parts[1])
    else:
        tokens = text.lower().replace(".", "").split()
        for index, token in enumerate(tokens):
            number = integer(token)
            if number is None:
                continue
            suffix = " ".join(tokens[index + 1 : index + 5])
            if "packages can be updated" in suffix:
                total = number
            if "updates are security updates" in suffix:
                security = number
    if total is None or security is None:
        return {
            "regular": None,
            "security": None,
            "held_back_or_blocked": None,
            "unknown": 1,
        }
    return {
        "regular": max(int(total) - int(security), 0),
        "security": max(int(security), 0),
        "held_back_or_blocked": None,
        "unknown": 0,
    }


def _parse_df(value: str) -> dict[str, Any]:
    lines = [line.split() for line in value.splitlines() if line.strip()]
    if len(lines) < 2 or len(lines[-1]) < 6:
        return {}
    row = lines[-1]
    return {
        "filesystem": row[0][:256],
        "blocks_1024": integer(row[1]),
        "used": integer(row[2]),
        "available": integer(row[3]),
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
            "total": integer(parts[1]),
            "used": integer(parts[2]),
            "free": integer(parts[3]),
        }
        if len(parts) >= 7:
            result["available"] = integer(parts[6])
        break
    return result


def _parse_loadavg(value: str) -> dict[str, Any]:
    parts = value.split()
    if len(parts) < 5:
        return {}
    process_counts = parts[3].split("/", 1)
    return {
        "one_minute": float_value(parts[0]),
        "five_minutes": float_value(parts[1]),
        "fifteen_minutes": float_value(parts[2]),
        "runnable_processes": integer(process_counts[0]) if process_counts else None,
        "total_processes": integer(process_counts[1])
        if len(process_counts) == 2
        else None,
    }
