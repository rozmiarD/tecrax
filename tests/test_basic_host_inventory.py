from __future__ import annotations

from rexecop.execution.backend import StepExecutionContext

from tecrax.internal_actions import (
    normalize_basic_host_inventory,
    normalize_ntp_health,
    normalize_zabbix_health,
)


def test_normalize_basic_host_inventory_builds_bounded_complete_result() -> None:
    connector_results = {
        "read_os_release": {
            "stdout": 'PRETTY_NAME="Ubuntu 24.04.4 LTS"\nID=ubuntu\nVERSION_ID="24.04"\n'
        },
        "read_kernel_identity": {"stdout": "Linux 6.8.0-generic x86_64\n"},
        "read_hostname": {"stdout": "monitoring-host\n"},
        "read_uptime": {"stdout": "up 2 days, 3 hours\n"},
        "read_filesystem_usage": {
            "stdout": (
                "Filesystem 1024-blocks Used Available Capacity Mounted on\n"
                "/dev/mapper/root 100000 9000 91000 9% /\n"
            )
        },
        "read_memory_summary": {
            "stdout": "Mem: 32000 8000 4000 100 2000 24000\n"
        },
    }
    shared_state = {"connector_results": connector_results}
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "normalize_inventory"},
        shared_state=shared_state,
    )

    result = normalize_basic_host_inventory(context)

    assert result["complete"] is True
    assert result["os"] == {
        "pretty_name": "Ubuntu 24.04.4 LTS",
        "id": "ubuntu",
        "version_id": "24.04",
    }
    assert result["root_filesystem"]["mounted_on"] == "/"
    assert result["memory_mib"]["available"] == 24000
    assert shared_state["basic_host_inventory"] == result


def test_normalize_basic_host_inventory_marks_missing_data_incomplete() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "normalize_inventory"},
        shared_state={"connector_results": {}},
    )

    result = normalize_basic_host_inventory(context)

    assert result["complete"] is False


def test_normalize_ntp_health_requires_sync_and_discovered_service() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "normalize_ntp_health"},
        shared_state={
            "connector_results": {
                "read_ntp_sync_state": {
                    "stdout": "NTP=no\nNTPSynchronized=yes\n"
                },
                "read_ntp_service_state": {"stdout": "active\n"},
            }
        },
    )

    result = normalize_ntp_health(context)

    assert result["healthy"] is True
    assert result["synchronized"] is True
    assert result["systemd_ntp_enabled"] is False
    assert result["service"] == "ntp"


def test_normalize_zabbix_health_does_not_claim_container_runtime_state() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "normalize_zabbix_health"},
        shared_state={
            "connector_results": {
                "read_zabbix_api_version": {
                    "jsonrpc": "2.0",
                    "result": "7.2.14",
                    "id": 1,
                }
            }
        },
    )

    result = normalize_zabbix_health(context)

    assert result == {
        "application_reachable": True,
        "api_version": "7.2.14",
        "container_runtime_state": "not_observed",
        "healthy": True,
    }
