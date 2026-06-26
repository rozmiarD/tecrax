from __future__ import annotations

from pathlib import Path

from rexecop.execution.backend import StepExecutionContext

from tecrax.internal_actions import (
    assess_network_device_management_posture,
    normalize_network_device_inventory,
)
from tecrax.normalizers.network_parsers import detect_network_device_parser_family

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "network_devices"


def _fixture(family: str, name: str) -> str:
    return (FIXTURES / family / name).read_text(encoding="utf-8")


def test_tplink_sg2452_golden_fixture_normalizes_inventory() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="network-device-01",
        mode="dry_run",
        step={"id": "normalize_network_device_inventory"},
        shared_state={
            "connector_results": {
                "read_network_device_system_info": {
                    "stdout": _fixture("tplink_sg2452_v1", "system_info.txt")
                },
                "read_network_device_ssh_status": {
                    "stdout": _fixture("tplink_sg2452_v1", "ssh_status.txt")
                },
            }
        },
    )

    result = normalize_network_device_inventory(context)

    assert result["target"] == "network-device-01"
    assert result["observation_scope"] == "network_cli_readonly"
    assert result["device"]["system_name"] == "TL-SG2452"
    assert result["management_access"]["ssh_protocol_v1_enabled"] is True
    assert result["hardening_observations"] == {
        "legacy_ssh_v1_enabled": True,
        "legacy_crypto_observed": True,
        "mutations_observed": False,
    }
    assert result["complete"] is True
    assert result["contract"]["id"] == "tecrax.network_device_inventory"
    assert result["schema_ref"] == "schemas/network_device_inventory.v1.schema.json"
    assert "SANITIZED" not in str(result)
    assert context.shared_state["network_device_inventory"] == result


def test_hpe_v1910_golden_fixture_normalizes_inventory() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="network-device-02",
        mode="dry_run",
        step={"id": "normalize_network_device_inventory"},
        shared_state={
            "connector_results": {
                "read_network_device_system_info": {
                    "stdout": _fixture("hpe_v1910_comware5", "system_info.txt")
                },
                "read_network_device_ssh_status": {
                    "stdout": _fixture("hpe_v1910_comware5", "ssh_status.txt")
                },
            }
        },
    )

    result = normalize_network_device_inventory(context)

    assert result["target"] == "network-device-02"
    assert result["complete"] is True
    assert result["device"] == {
        "system_name": "HPE V1910-48G Switch JE009A",
        "system_description": "HPE V1910-48G Switch JE009A",
        "hardware_version": "JE009A",
        "software_version": "5.20.99, Release 1111",
    }
    assert result["management_access"] == {
        "ssh_server_enabled": True,
        "ssh_protocol_v1_enabled": False,
        "ssh_protocol_v2_enabled": True,
        "idle_timeout_seconds": 60,
        "max_clients": 5,
    }
    assert result["hardening_observations"] == {
        "legacy_ssh_v1_enabled": False,
        "legacy_crypto_observed": True,
        "mutations_observed": False,
    }
    assert "512900" not in str(result)
    assert "SANITIZED" not in str(result)


def test_network_device_parser_detects_supported_families() -> None:
    assert (
        detect_network_device_parser_family(
            system_info_output=_fixture("tplink_sg2452_v1", "system_info.txt"),
            ssh_status_output=_fixture("tplink_sg2452_v1", "ssh_status.txt"),
        )
        == "tplink_sg2452_v1"
    )
    assert (
        detect_network_device_parser_family(
            system_info_output=_fixture("hpe_v1910_comware5", "system_info.txt"),
            ssh_status_output=_fixture("hpe_v1910_comware5", "ssh_status.txt"),
        )
        == "hpe_v1910_comware5"
    )


def test_normalize_network_device_inventory_marks_missing_data_incomplete() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="network-device-01",
        mode="dry_run",
        step={"id": "normalize_network_device_inventory"},
        shared_state={"connector_results": {}},
    )

    result = normalize_network_device_inventory(context)

    assert result["complete"] is False
    assert result["hardening_observations"]["mutations_observed"] is False


def test_unsupported_network_device_output_fails_closed() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="network-device-unsupported",
        mode="dry_run",
        step={"id": "normalize_network_device_inventory"},
        shared_state={
            "connector_results": {
                "read_network_device_system_info": {
                    "stdout": _fixture("unsupported", "system_info.txt")
                },
                "read_network_device_ssh_status": {
                    "stdout": _fixture("unsupported", "ssh_status.txt")
                },
            }
        },
    )

    result = normalize_network_device_inventory(context)

    assert result["complete"] is False
    assert result["scope"]["not_observed"] == ["one_or_more_device_fields"]
    assert result["assessment"]["state"] == "unknown"
    assert result["device"]["system_name"] == ""
    assert result["management_access"]["ssh_server_enabled"] is None


def test_prompt_drift_without_device_fields_fails_closed() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="network-device-prompt-drift",
        mode="dry_run",
        step={"id": "normalize_network_device_inventory"},
        shared_state={
            "connector_results": {
                "read_network_device_system_info": {
                    "stdout": "<HPE> _cmdline-mode on\nAll commands can be displayed.\n"
                },
                "read_network_device_ssh_status": {"stdout": "<HPE>"},
            }
        },
    )

    result = normalize_network_device_inventory(context)

    assert result["complete"] is False
    assert result["hardening_observations"]["mutations_observed"] is False
    assert "_cmdline-mode" not in str(result)


def test_management_posture_emits_bounded_findings() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="network-device-01",
        mode="dry_run",
        step={"id": "assess"},
        shared_state={
            "network_device_inventory": {
                "contract": {"id": "tecrax.network_device_inventory", "version": "1.0"},
                "complete": True,
                "management_access": {"idle_timeout_seconds": 120},
                "hardening_observations": {
                    "legacy_ssh_v1_enabled": True,
                    "legacy_crypto_observed": True,
                },
            }
        },
    )
    result = assess_network_device_management_posture(context)
    assert result["assessment"]["state"] == "degraded"
    assert result["schema_ref"] == "schemas/network_management_posture.v1.schema.json"
    assert {item["reason_code"] for item in result["findings"]} == {
        "legacy_ssh_v1_enabled",
        "legacy_ssh_crypto_observed",
    }
    assert "running_configuration" in result["non_claims"]
