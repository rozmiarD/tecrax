from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from tecrax.normalizers.common import integer, single_line


@dataclass(frozen=True)
class ParsedNetworkDeviceCli:
    device: dict[str, str]
    management_access: dict[str, bool | int | None]
    hardening_observations: dict[str, bool]
    supported: bool
    parser_family: str


def parse_network_device_cli(
    *, system_info_output: str, ssh_status_output: str
) -> ParsedNetworkDeviceCli:
    family = detect_network_device_parser_family(
        system_info_output=system_info_output,
        ssh_status_output=ssh_status_output,
    )
    if family == "tplink_sg2452_v1":
        return _parse_tplink_sg2452_v1(system_info_output, ssh_status_output)
    if family == "hpe_v1910_comware5":
        return _parse_hpe_v1910_comware5(system_info_output, ssh_status_output)
    return _unsupported()


def detect_network_device_parser_family(
    *, system_info_output: str, ssh_status_output: str
) -> str:
    text = f"{system_info_output}\n{ssh_status_output}".lower()
    fields = _parse_fields(system_info_output)
    identity = " ".join(
        str(
            fields.get(key)
            or fields.get(key.lower())
            or ""
        )
        for key in ("System Name", "Device Name", "System Description")
    ).lower()
    if "tl-sg2452" in text or "tl-sg2452" in identity:
        return "tplink_sg2452_v1"
    if "v1910" in text and ("hpe" in text or "hp " in text or "comware" in text):
        return "hpe_v1910_comware5"
    return "unsupported"


def _parse_tplink_sg2452_v1(
    system_info_output: str, ssh_status_output: str
) -> ParsedNetworkDeviceCli:
    system_info = _parse_fields(system_info_output)
    ssh_status = _parse_fields(ssh_status_output)
    protocol_v1 = _enabled_value(
        _field(ssh_status, "SSH Server Protocol V1", "Protocol V1")
    )
    protocol_v2 = _enabled_value(
        _field(ssh_status, "SSH Server Protocol V2", "Protocol V2")
    )
    return ParsedNetworkDeviceCli(
        device={
            "system_name": _bounded_field(_field(system_info, "System Name"), 128),
            "system_description": _bounded_field(
                _field(system_info, "System Description"), 256
            ),
            "hardware_version": _bounded_field(
                _field(system_info, "Hardware Version"), 128
            ),
            "software_version": _bounded_field(
                _field(system_info, "Software Version"), 128
            ),
        },
        management_access={
            "ssh_server_enabled": _enabled_value(_field(ssh_status, "SSH Server")),
            "ssh_protocol_v1_enabled": protocol_v1,
            "ssh_protocol_v2_enabled": protocol_v2,
            "idle_timeout_seconds": integer(
                _field(ssh_status, "SSH Idle Timeout", "Idle Timeout")
            ),
            "max_clients": integer(
                _field(ssh_status, "SSH MAX Client", "MAX Clients")
            ),
        },
        hardening_observations={
            "legacy_ssh_v1_enabled": protocol_v1 is True,
            "legacy_crypto_observed": _legacy_crypto_observed(ssh_status_output),
            "mutations_observed": False,
        },
        supported=True,
        parser_family="tplink_sg2452_v1",
    )


def _parse_hpe_v1910_comware5(
    system_info_output: str, ssh_status_output: str
) -> ParsedNetworkDeviceCli:
    system_info = _parse_fields(system_info_output)
    ssh_status = _parse_fields(ssh_status_output)
    description = _hpe_description(system_info_output, system_info)
    protocol_v1 = _enabled_value(
        _field(
            ssh_status,
            "SSH server compatible-ssh1x",
            "Compatible SSH1X",
            "Protocol V1",
        )
    )
    ssh_version = _field(ssh_status, "SSH version", "SSH Server Version")
    protocol_v2 = True if "2" in ssh_version else _enabled_value(
        _field(ssh_status, "SSH Server Protocol V2", "Protocol V2")
    )
    return ParsedNetworkDeviceCli(
        device={
            "system_name": _bounded_field(
                _field(system_info, "Device Name", "System Name") or description,
                128,
            ),
            "system_description": _bounded_field(description, 256),
            "hardware_version": _bounded_field(
                _field(system_info, "Hardware Version", "Hardware")
                or _hpe_hardware(system_info_output),
                128,
            ),
            "software_version": _bounded_field(
                _field(system_info, "Software Version")
                or _hpe_software(system_info_output),
                128,
            ),
        },
        management_access={
            "ssh_server_enabled": _enabled_value(
                _field(ssh_status, "SSH server", "SSH Server", "Stelnet server")
            ),
            "ssh_protocol_v1_enabled": protocol_v1,
            "ssh_protocol_v2_enabled": protocol_v2,
            "idle_timeout_seconds": integer(
                _first_number(
                    _field(
                        ssh_status,
                        "SSH authentication timeout",
                        "SSH Idle Timeout",
                    )
                )
            ),
            "max_clients": integer(
                _first_number(_field(ssh_status, "SSH max connections", "MAX Clients"))
            ),
        },
        hardening_observations={
            "legacy_ssh_v1_enabled": protocol_v1 is True,
            "legacy_crypto_observed": _legacy_crypto_observed(ssh_status_output),
            "mutations_observed": False,
        },
        supported=True,
        parser_family="hpe_v1910_comware5",
    )


def _unsupported() -> ParsedNetworkDeviceCli:
    return ParsedNetworkDeviceCli(
        device={
            "system_name": "",
            "system_description": "",
            "hardware_version": "",
            "software_version": "",
        },
        management_access={
            "ssh_server_enabled": None,
            "ssh_protocol_v1_enabled": None,
            "ssh_protocol_v2_enabled": None,
            "idle_timeout_seconds": None,
            "max_clients": None,
        },
        hardening_observations={
            "legacy_ssh_v1_enabled": False,
            "legacy_crypto_observed": False,
            "mutations_observed": False,
        },
        supported=False,
        parser_family="unsupported",
    )


def _parse_fields(value: str) -> dict[str, str]:
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


def _field(fields: dict[str, str], *names: str) -> str:
    lookup = {key.lower(): value for key, value in fields.items()}
    for name in names:
        value = lookup.get(name.lower())
        if value:
            return value
    return ""


def _bounded_field(value: Any, limit: int) -> str:
    return single_line(str(value or ""), limit=limit)


def _enabled_value(value: Any) -> bool | None:
    text = str(value or "").strip().lower()
    if text in {"enabled", "enable", "true", "yes", "on"}:
        return True
    if text in {"disabled", "disable", "false", "no", "off"}:
        return False
    return None


def _legacy_crypto_observed(value: str) -> bool:
    text = value.upper()
    return any(marker in text for marker in ("CBC", "SHA1", "GROUP1", "3DES", "DES"))


def _first_number(value: str) -> str:
    match = re.search(r"\d+", value)
    return match.group(0) if match else ""


def _hpe_description(output: str, fields: dict[str, str]) -> str:
    explicit = _field(fields, "Device Name", "System Description", "Product Name")
    if explicit:
        return explicit
    for line in output.splitlines():
        clean = " ".join(line.split())
        lowered = clean.lower()
        if "v1910" in lowered and "switch" in lowered:
            return clean
    return ""


def _hpe_hardware(output: str) -> str:
    match = re.search(r"\b(J[A-Z0-9]{3,8}A)\b", output)
    return match.group(1) if match else ""


def _hpe_software(output: str) -> str:
    match = re.search(
        r"(?:Comware Software,\s*)?Version\s+([^,\n]+(?:,\s*Release\s+\S+)?)",
        output,
        flags=re.IGNORECASE,
    )
    return " ".join(match.group(1).split()) if match else ""
