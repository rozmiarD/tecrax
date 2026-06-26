from __future__ import annotations

from rexecop.execution.backend import StepExecutionContext

from tecrax.internal_actions import (
    assess_network_device_management_posture,
    normalize_network_device_inventory,
)


def test_normalize_network_device_inventory_bounds_legacy_cli_output() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="network-device-01",
        mode="dry_run",
        step={"id": "normalize_network_device_inventory"},
        shared_state={
            "connector_results": {
                "read_network_device_system_info": {
                    "stdout": (
                        " System Description      : 48-Port Gigabit Smart Switch with 4 SFP Slots\n"
                        " System Name             : TL-SG2452\n"
                        " Hardware Version        : TL-SG2452 1.0\n"
                        " Software Version        : 1.0.4 Build 20151127 Rel.67331(s)\n"
                        " Ignored Extra Field     : omitted value\n"
                    )
                },
                "read_network_device_ssh_status": {
                    "stdout": (
                        " SSH Server              : Enabled\n"
                        " SSH Server Protocol V1  : Enabled\n"
                        " SSH Server Protocol V2  : Enabled\n"
                        " SSH Idle Timeout        : 120\n"
                        " SSH MAX Client          : 5\n"
                        " AES128-CBC              : Enabled\n"
                    )
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
    assert "omitted value" not in str(result)
    assert context.shared_state["network_device_inventory"] == result


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
