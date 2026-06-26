from __future__ import annotations

from rexecop.execution.backend import StepExecutionContext

from tecrax.internal_actions import (
    normalize_host_security_posture,
    normalize_ntp_server_observation,
)


def test_host_security_posture_normalizes_four_bounded_signals() -> None:
    context = StepExecutionContext(
        operation_id="op",
        target="host",
        mode="dry_run",
        step={"id": "normalize"},
        shared_state={
            "connector_results": {
                "read_unattended_upgrades_state": {"stdout": "enabled\n"},
                "read_available_updates_summary": {"stderr": "3;0\n"},
                "read_aslr_state": {"stdout": "2\n"},
                "read_dmesg_restrict_state": {"stdout": "1\n"},
                "read_reboot_required_marker": {"stdout": ""},
            }
        },
    )
    result = normalize_host_security_posture(context)
    assert result["complete"] is True
    assert result["healthy"] is True
    assert result["assessment"]["state"] == "healthy"
    assert result["signals"]["available_updates"] == {
        "regular": 3,
        "security": 0,
        "held_back_or_blocked": None,
        "unknown": 0,
    }
    assert result["schema_ref"] == "schemas/host_security_posture.v1.schema.json"
    assert "package_names" in result["non_claims"]


def test_host_security_posture_marks_unparsed_updates_unknown() -> None:
    context = StepExecutionContext(
        operation_id="op",
        target="host",
        mode="dry_run",
        step={"id": "normalize"},
        shared_state={
            "connector_results": {
                "read_unattended_upgrades_state": {"stdout": "enabled\n"},
                "read_available_updates_summary": {"stderr": "unexpected output\n"},
                "read_aslr_state": {"stdout": "2\n"},
                "read_dmesg_restrict_state": {"stdout": "1\n"},
                "read_reboot_required_marker": {"stdout": ""},
            }
        },
    )
    result = normalize_host_security_posture(context)
    assert result["complete"] is False
    assert result["assessment"]["state"] == "unknown"
    assert result["signals"]["available_updates"]["unknown"] == 1


def test_ntp_server_observation_drops_peer_identity() -> None:
    context = StepExecutionContext(
        operation_id="op",
        target="host",
        mode="dry_run",
        step={"id": "normalize"},
        shared_state={
            "connector_results": {
                "read_ntp_service_state": {"stdout": "active\n"},
                "read_ntp_server_variables": {
                    "stdout": "stratum=3, offset=-0.25, rootdelay=1.2, rootdisp=2.3, leap=0\n"
                },
            }
        },
    )
    result = normalize_ntp_server_observation(context)
    assert result["healthy"] is True
    assert result["schema_ref"] == "schemas/ntp_server_observation.v1.schema.json"
    assert result["system_variables"]["stratum"] == 3
    assert result["system_variables"]["offset_ms"] == -0.25
    assert "peer_address" in result["non_claims"]
    assert "refid" not in str(result).lower()
