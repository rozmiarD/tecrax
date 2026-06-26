from __future__ import annotations

import json
from pathlib import Path

from rexecop.catalog.service import CatalogService, compile_profile_operations
from rexecop.profile.loader import load_profile
from tecrax import profile_root


ROOT = Path(__file__).resolve().parents[1]


def test_all_tecrax_intents_have_operator_catalog_metadata() -> None:
    profile = load_profile(Path(profile_root()))

    operations = compile_profile_operations(profile)

    assert len(operations) == 13
    assert {item.id for item in operations} == {
        "check_adguard_health",
        "check_docker_services_health",
        "check_ntp_health",
        "check_portainer_health",
        "check_zabbix_container_health",
        "collect_basic_host_inventory",
        "collect_zabbix_problem_summary_readonly",
        "collect_zabbix_host_availability_summary_readonly",
        "diagnose_monitoring_host",
        "collect_network_device_inventory_readonly",
        "collect_host_security_posture_readonly",
        "check_ntp_server_health",
        "assess_network_device_management_posture_readonly",
    }
    assert all(item.runbook_ref for item in operations)
    assert all(item.validation_ref for item in operations)
    assert all(len(item.digest) == 64 for item in operations)


def test_sanitized_target_catalog_projects_host_operations() -> None:
    service = CatalogService(
        ROOT / "examples" / "catalogs" / "targets.readonly.example.yaml"
    )

    results = service.list_operations_for_target("monitoring-host-01")
    by_id = {item["operation"]["id"]: item for item in results}

    assert by_id["diagnose_monitoring_host"]["applicability"]["status"] == (
        "admission_required"
    )
    assert by_id["collect_network_device_inventory_readonly"]["applicability"][
        "status"
    ] == "unsupported_target_kind"
    assert "restart_zabbix_agent" not in by_id
    assert by_id["collect_zabbix_problem_summary_readonly"]["applicability"][
        "status"
    ] == "admission_required"
    assert by_id["collect_zabbix_host_availability_summary_readonly"]["applicability"][
        "status"
    ] == "admission_required"


def test_sanitized_target_catalog_projects_network_device_operation() -> None:
    service = CatalogService(
        ROOT / "examples" / "catalogs" / "targets.readonly.example.yaml"
    )

    results = service.list_operations_for_target("network-device-01")
    by_id = {item["operation"]["id"]: item for item in results}

    assert by_id["collect_network_device_inventory_readonly"]["applicability"][
        "status"
    ] == "admission_required"
    assert by_id["assess_network_device_management_posture_readonly"]["applicability"][
        "status"
    ] == "admission_required"
    assert by_id["diagnose_monitoring_host"]["applicability"]["applicable"] is False


def test_sanitized_target_catalog_output_has_no_private_topology() -> None:
    service = CatalogService(
        ROOT / "examples" / "catalogs" / "targets.readonly.example.yaml"
    )

    rendered = json.dumps(service.list_targets(), sort_keys=True)

    assert "example.invalid" not in rendered
    assert "/home/" not in rendered
    assert "environment_ref" not in rendered
