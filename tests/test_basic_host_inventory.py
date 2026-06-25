from __future__ import annotations

from rexecop.execution.backend import StepExecutionContext

from tecrax.contracts import validate_basic_host_inventory_v1
from tecrax.internal_actions import (
    aggregate_monitoring_host_diagnosis,
    normalize_adguard_health,
    normalize_basic_host_inventory,
    normalize_docker_services_health,
    normalize_ntp_health,
    normalize_portainer_health,
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
        "read_load_average": {"stdout": "0.10 0.20 0.30 1/234 5678\n"},
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
    assert result["load_average"] == {
        "one_minute": 0.10,
        "five_minutes": 0.20,
        "fifteen_minutes": 0.30,
        "runnable_processes": 1,
        "total_processes": 234,
    }
    assert result["memory_mib"]["available"] == 24000
    assert result["schema_ref"] == "schemas/basic_host_inventory.v1.schema.json"
    assert result["contract"] == {
        "id": "tecrax.basic_host_inventory",
        "version": "1.0",
    }
    assert validate_basic_host_inventory_v1(result) == []
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
    assert result["coverage"]["state"] == "partial"
    assert validate_basic_host_inventory_v1(result) == []


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

    assert result["application_reachable"] is True
    assert result["api_version"] == "7.2.14"
    assert result["container_runtime_state"] == "not_observed"
    assert result["healthy"] is True
    assert result["contract"]["id"] == "tecrax.zabbix_api_reachability"
    assert result["coverage"]["state"] == "partial"


def test_normalize_docker_services_health_is_systemd_only() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "normalize_docker_services_health"},
        shared_state={
            "connector_results": {
                "read_docker_service_state": {
                    "stdout": (
                        "LoadState=loaded\n"
                        "ActiveState=active\n"
                        "SubState=running\n"
                        "UnitFileState=enabled\n"
                    )
                },
                "read_docker_socket_state": {
                    "stdout": (
                        "LoadState=loaded\n"
                        "ActiveState=active\n"
                        "SubState=listening\n"
                        "UnitFileState=enabled\n"
                    )
                },
            }
        },
    )

    result = normalize_docker_services_health(context)

    assert result["observation_scope"] == "systemd_service_only"
    assert result["service_active_state"] == "active"
    assert result["socket_sub_state"] == "listening"
    assert result["container_runtime_state"] == "not_observed"
    assert result["healthy"] is True
    assert result["contract"]["id"] == "tecrax.docker_service_health"


def test_normalize_adguard_health_uses_dns_and_login_only() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "normalize_adguard_health"},
        shared_state={
            "connector_results": {
                "read_adguard_dns_resolution": {
                    "stdout": (
                        "example.com. 300 IN A 104.20.23.154\n"
                        "example.com. 300 IN A 172.66.147.243\n"
                    )
                },
                "read_adguard_login_status": {"stdout": "200"},
            }
        },
    )

    result = normalize_adguard_health(context)

    assert result["observation_scope"] == "dns_and_web_login_only"
    assert result["dns_resolves"] is True
    assert result["dns_answer_count"] == 2
    assert result["web_login_http_status"] == "200"
    assert result["management_api_state"] == "not_observed"
    assert result["healthy"] is True
    assert result["contract"]["id"] == "tecrax.adguard_reachability"


def test_normalize_portainer_health_discards_instance_identity() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "normalize_portainer_health"},
        shared_state={
            "connector_results": {
                "read_portainer_status": {
                    "Version": "2.33.5",
                }
            }
        },
    )

    result = normalize_portainer_health(context)

    assert result["observation_scope"] == "unauthenticated_status_only"
    assert result["api_reachable"] is True
    assert result["api_version"] == "2.33.5"
    assert result["instance_identity_state"] == "deliberately_not_collected"
    assert result["management_objects_state"] == "not_observed"
    assert result["healthy"] is True
    assert result["contract"]["id"] == "tecrax.portainer_reachability"
    assert "InstanceID" not in str(result)


def test_aggregate_diagnosis_preserves_failures_and_blockers() -> None:
    context = StepExecutionContext(
        operation_id="op-test",
        target="monitoring-host-01",
        mode="dry_run",
        step={"id": "aggregate_diagnosis"},
        shared_state={
            "basic_host_inventory": {"complete": True},
            "ntp_health": {"healthy": True},
            "docker_services_health": {"healthy": True},
            "zabbix_health": {"healthy": False},
            "adguard_health": {"healthy": True},
            "portainer_health": {"healthy": True},
            "continued_failures": {
                "read_zabbix_api_version": {
                    "error": "sensitive upstream detail",
                    "error_class": "transient_connector_error",
                }
            },
        },
    )

    result = aggregate_monitoring_host_diagnosis(context)

    assert result["aggregation_completed"] is True
    assert result["coverage_status"] == "partial"
    assert result["observed_health"] == "degraded"
    assert result["components"]["docker"]["status"] == "healthy"
    assert result["components"]["adguard"]["status"] == "healthy"
    assert result["components"]["portainer"]["status"] == "healthy"
    assert result["continued_failures"] == [
        {
            "step_id": "read_zabbix_api_version",
            "error_class": "transient_connector_error",
        }
    ]
    assert result["contract"]["id"] == "tecrax.monitoring_host_diagnosis"
    assert "sensitive upstream detail" not in str(result)
