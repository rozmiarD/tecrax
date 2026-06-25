from __future__ import annotations

from importlib import resources

from tecrax.contracts import (
    BASIC_HOST_INVENTORY_CONTRACT_ID,
    BASIC_HOST_INVENTORY_CONTRACT_VERSION,
    BASIC_HOST_INVENTORY_SCHEMA_REF,
    FACTS_CONTRACTS,
    build_basic_host_inventory_v1,
    finalize_facts,
    validate_basic_host_inventory_v1,
    validate_facts,
)


def test_all_active_results_have_static_contract_specs() -> None:
    assert set(FACTS_CONTRACTS) == {
        "tecrax.basic_host_inventory",
        "tecrax.ntp_local_health",
        "tecrax.docker_service_health",
        "tecrax.zabbix_api_reachability",
        "tecrax.adguard_reachability",
        "tecrax.portainer_reachability",
        "tecrax.network_device_inventory",
        "tecrax.monitoring_host_diagnosis",
        "tecrax.host_security_posture",
        "tecrax.ntp_server_observation",
        "tecrax.network_management_posture",
    }


def test_negative_health_is_valid_observation() -> None:
    facts = finalize_facts(
        {"synchronized": False, "service_state": "inactive"},
        contract_id="tecrax.ntp_local_health",
        requested=["local_synchronization", "daemon_state"],
        observed=["local_synchronization", "daemon_state"],
        assessment="unhealthy",
    )

    assert validate_facts(facts) == []
    assert facts["coverage"]["state"] == "complete"
    assert facts["assessment"]["state"] == "unhealthy"


def test_partial_and_unknown_are_distinct_from_unhealthy() -> None:
    facts = finalize_facts(
        {
            "schema_ref": BASIC_HOST_INVENTORY_SCHEMA_REF,
            "target": "fixture",
            "os": {"pretty_name": "", "id": "", "version_id": ""},
            "kernel": "",
            "hostname": "",
            "uptime": "",
            "load_average": {
                "one_minute": None,
                "five_minutes": None,
                "fifteen_minutes": None,
                "runnable_processes": None,
                "total_processes": None,
            },
            "root_filesystem": {
                "filesystem": "",
                "blocks_1024": None,
                "used_1024": None,
                "available_1024": None,
                "capacity": "",
                "mounted_on": "",
            },
            "memory_mib": {
                "total": None,
                "used": None,
                "free": None,
                "shared": None,
                "buff_cache": None,
                "available": None,
            },
            "complete": False,
        },
        contract_id=BASIC_HOST_INVENTORY_CONTRACT_ID,
        requested=["os", "kernel"],
        observed=[],
        not_observed=["os", "kernel"],
        assessment="unknown",
    )

    assert validate_facts(facts) == []
    assert facts["coverage"]["state"] == "partial"
    assert facts["assessment"]["state"] == "unknown"


def test_basic_host_inventory_v1_builds_contract_with_schema_ref() -> None:
    facts = build_basic_host_inventory_v1(
        target="monitoring-host-01",
        os={
            "pretty_name": "Ubuntu 24.04.4 LTS",
            "id": "ubuntu",
            "version_id": "24.04",
        },
        kernel="Linux 6.8.0-generic x86_64",
        hostname="monitoring-host",
        uptime="up 2 days",
        load_average={
            "one_minute": 0.1,
            "five_minutes": 0.2,
            "fifteen_minutes": 0.3,
            "runnable_processes": 1,
            "total_processes": 234,
        },
        root_filesystem={
            "filesystem": "/dev/mapper/root",
            "blocks_1024": 100000,
            "used_1024": 9000,
            "available_1024": 91000,
            "capacity": "9%",
            "mounted_on": "/",
        },
        memory_mib={
            "total": 32000,
            "used": 8000,
            "free": 4000,
            "shared": 100,
            "buff_cache": 2000,
            "available": 24000,
        },
    )

    assert facts["contract"] == {
        "id": BASIC_HOST_INVENTORY_CONTRACT_ID,
        "version": BASIC_HOST_INVENTORY_CONTRACT_VERSION,
    }
    assert facts["schema_ref"] == BASIC_HOST_INVENTORY_SCHEMA_REF
    assert facts["coverage"]["state"] == "complete"
    assert facts["assessment"]["state"] == "healthy"
    assert validate_basic_host_inventory_v1(facts) == []


def test_basic_host_inventory_v1_schema_file_is_packaged() -> None:
    schema = resources.files("tecrax").joinpath(
        *BASIC_HOST_INVENTORY_SCHEMA_REF.split("/")
    )
    text = schema.read_text(encoding="utf-8")

    assert "Tecrax basic host inventory facts v1" in text
    assert BASIC_HOST_INVENTORY_CONTRACT_ID in text


def test_basic_host_inventory_v1_rejects_malformed_payload() -> None:
    facts = build_basic_host_inventory_v1(
        target="monitoring-host-01",
        os={"pretty_name": "Ubuntu", "id": "ubuntu", "version_id": "24.04"},
        kernel="Linux",
        hostname="host",
        uptime="up",
        load_average={
            "one_minute": 0.1,
            "five_minutes": 0.2,
            "fifteen_minutes": 0.3,
            "runnable_processes": 1,
            "total_processes": 234,
        },
        root_filesystem={
            "filesystem": "/dev/root",
            "blocks_1024": 100000,
            "used_1024": 9000,
            "available_1024": 91000,
            "capacity": "9%",
            "mounted_on": "/",
        },
        memory_mib={
            "total": 32000,
            "used": 8000,
            "free": 4000,
            "shared": 100,
            "buff_cache": 2000,
            "available": 24000,
        },
    )
    facts["schema_ref"] = "schemas/other.schema.json"
    facts["memory_mib"]["total"] = -1

    errors = validate_basic_host_inventory_v1(facts)

    assert "basic_host_inventory.schema_ref_mismatch" in errors
    assert "basic_host_inventory.invalid_memory_mib:total" in errors


def test_raw_connector_output_is_rejected() -> None:
    facts = finalize_facts(
        {"synchronized": True, "service_state": "active"},
        contract_id="tecrax.ntp_local_health",
        requested=["local_synchronization"],
        observed=["local_synchronization"],
        assessment="healthy",
    )
    facts["stdout"] = "unbounded"

    assert "raw_output_forbidden" in validate_facts(facts)
