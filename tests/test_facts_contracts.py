from __future__ import annotations

from importlib import resources

from tecrax.contracts import (
    BASIC_HOST_INVENTORY_CONTRACT_ID,
    BASIC_HOST_INVENTORY_CONTRACT_VERSION,
    BASIC_HOST_INVENTORY_SCHEMA_REF,
    DOCKER_SERVICE_HEALTH_CONTRACT_ID,
    DOCKER_SERVICE_HEALTH_SCHEMA_REF,
    FACTS_CONTRACTS,
    HOST_SECURITY_POSTURE_CONTRACT_ID,
    HOST_SECURITY_POSTURE_SCHEMA_REF,
    NETWORK_DEVICE_INVENTORY_CONTRACT_ID,
    NETWORK_DEVICE_INVENTORY_SCHEMA_REF,
    NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID,
    NETWORK_MANAGEMENT_POSTURE_SCHEMA_REF,
    NTP_LOCAL_HEALTH_CONTRACT_ID,
    NTP_LOCAL_HEALTH_SCHEMA_REF,
    NTP_SERVER_OBSERVATION_CONTRACT_ID,
    NTP_SERVER_OBSERVATION_SCHEMA_REF,
    build_basic_host_inventory_v1,
    build_docker_service_health_v1,
    build_host_security_posture_v1,
    build_network_device_inventory_v1,
    build_network_management_posture_v1,
    build_ntp_local_health_v1,
    build_ntp_server_observation_v1,
    finalize_facts,
    validate_basic_host_inventory_v1,
    validate_docker_service_health_v1,
    validate_facts,
    validate_host_security_posture_v1,
    validate_network_device_inventory_v1,
    validate_network_management_posture_v1,
    validate_ntp_local_health_v1,
    validate_ntp_server_observation_v1,
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
    facts = build_ntp_local_health_v1(
        synchronized=False,
        systemd_ntp_enabled=False,
        service="ntp",
        service_state="inactive",
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


def test_local_ssh_fact_contract_v1_builders_emit_schema_refs() -> None:
    ntp = build_ntp_local_health_v1(
        synchronized=True,
        systemd_ntp_enabled=True,
        service="ntp",
        service_state="active",
    )
    docker = build_docker_service_health_v1(
        {
            "observation_scope": "systemd_service_only",
            "service": "docker",
            "service_load_state": "loaded",
            "service_active_state": "active",
            "service_sub_state": "running",
            "service_unit_file_state": "enabled",
            "socket": "docker.socket",
            "socket_load_state": "loaded",
            "socket_active_state": "active",
            "socket_sub_state": "listening",
            "socket_unit_file_state": "enabled",
            "container_runtime_state": "not_observed",
        }
    )
    security = build_host_security_posture_v1(
        signals={
            "unattended_upgrades_enabled": True,
            "available_updates": {
                "regular": 0,
                "security": 0,
                "held_back_or_blocked": None,
                "unknown": 0,
            },
            "aslr_mode": 2,
            "dmesg_restrict": 1,
            "reboot_required": False,
        },
        complete=True,
        healthy=True,
    )
    ntp_server = build_ntp_server_observation_v1(
        daemon_state="active",
        serving_state="local_daemon_query_available",
        system_variables={
            "stratum": 3,
            "leap": 0,
            "offset_ms": -0.25,
            "root_delay_ms": 1.2,
            "root_dispersion_ms": 2.3,
        },
        healthy=True,
    )

    assert ntp["contract"]["id"] == NTP_LOCAL_HEALTH_CONTRACT_ID
    assert ntp["schema_ref"] == NTP_LOCAL_HEALTH_SCHEMA_REF
    assert docker["contract"]["id"] == DOCKER_SERVICE_HEALTH_CONTRACT_ID
    assert docker["schema_ref"] == DOCKER_SERVICE_HEALTH_SCHEMA_REF
    assert security["contract"]["id"] == HOST_SECURITY_POSTURE_CONTRACT_ID
    assert security["schema_ref"] == HOST_SECURITY_POSTURE_SCHEMA_REF
    assert ntp_server["contract"]["id"] == NTP_SERVER_OBSERVATION_CONTRACT_ID
    assert ntp_server["schema_ref"] == NTP_SERVER_OBSERVATION_SCHEMA_REF
    assert validate_ntp_local_health_v1(ntp) == []
    assert validate_docker_service_health_v1(docker) == []
    assert validate_host_security_posture_v1(security) == []
    assert validate_ntp_server_observation_v1(ntp_server) == []


def test_local_ssh_fact_contract_v1_schema_files_are_packaged() -> None:
    refs = [
        (NTP_LOCAL_HEALTH_SCHEMA_REF, NTP_LOCAL_HEALTH_CONTRACT_ID),
        (DOCKER_SERVICE_HEALTH_SCHEMA_REF, DOCKER_SERVICE_HEALTH_CONTRACT_ID),
        (HOST_SECURITY_POSTURE_SCHEMA_REF, HOST_SECURITY_POSTURE_CONTRACT_ID),
        (NTP_SERVER_OBSERVATION_SCHEMA_REF, NTP_SERVER_OBSERVATION_CONTRACT_ID),
    ]

    for schema_ref, contract_id in refs:
        schema = resources.files("tecrax").joinpath(*schema_ref.split("/"))
        text = schema.read_text(encoding="utf-8")
        assert contract_id in text


def test_local_ssh_fact_contract_v1_rejects_malformed_payloads() -> None:
    ntp = build_ntp_local_health_v1(
        synchronized=True,
        systemd_ntp_enabled=True,
        service="ntp",
        service_state="active",
    )
    ntp["schema_ref"] = "schemas/other.schema.json"
    ntp["healthy"] = "yes"

    docker = build_docker_service_health_v1(
        {
            "observation_scope": "systemd_service_only",
            "service": "docker",
            "service_load_state": "loaded",
            "service_active_state": "active",
            "service_sub_state": "running",
            "service_unit_file_state": "enabled",
            "socket": "docker.socket",
            "socket_load_state": "loaded",
            "socket_active_state": "active",
            "socket_sub_state": "listening",
            "socket_unit_file_state": "enabled",
            "container_runtime_state": "not_observed",
        }
    )
    docker["container_runtime_state"] = "observed"

    security = build_host_security_posture_v1(
        signals={
            "unattended_upgrades_enabled": True,
            "available_updates": {
                "regular": 0,
                "security": 0,
                "held_back_or_blocked": None,
                "unknown": 0,
            },
            "aslr_mode": 2,
            "dmesg_restrict": 1,
            "reboot_required": False,
        },
        complete=True,
        healthy=True,
    )
    security["signals"]["aslr_mode"] = -1

    ntp_server = build_ntp_server_observation_v1(
        daemon_state="active",
        serving_state="local_daemon_query_available",
        system_variables={
            "stratum": 3,
            "leap": 0,
            "offset_ms": -0.25,
            "root_delay_ms": 1.2,
            "root_dispersion_ms": 2.3,
        },
        healthy=True,
    )
    ntp_server["system_variables"]["stratum"] = -1

    assert "ntp_local_health.schema_ref_mismatch" in validate_ntp_local_health_v1(ntp)
    assert "ntp_local_health.invalid_healthy" in validate_ntp_local_health_v1(ntp)
    assert (
        "docker_service_health.container_runtime_must_be_not_observed"
        in validate_docker_service_health_v1(docker)
    )
    assert (
        "host_security_posture.invalid_signals:aslr_mode"
        in validate_host_security_posture_v1(security)
    )
    assert (
        "ntp_server_observation.invalid_system_variables:stratum"
        in validate_ntp_server_observation_v1(ntp_server)
    )


def test_network_fact_contract_v1_builders_emit_schema_refs() -> None:
    inventory = build_network_device_inventory_v1(
        {
            "target": "network-device-01",
            "observation_scope": "network_cli_readonly",
            "device": {
                "system_name": "TL-SG2452",
                "system_description": "48-Port Gigabit Smart Switch",
                "hardware_version": "TL-SG2452 1.0",
                "software_version": "1.0.4 Build",
            },
            "management_access": {
                "ssh_server_enabled": True,
                "ssh_protocol_v1_enabled": True,
                "ssh_protocol_v2_enabled": True,
                "idle_timeout_seconds": 120,
                "max_clients": 5,
            },
            "hardening_observations": {
                "legacy_ssh_v1_enabled": True,
                "legacy_crypto_observed": True,
                "mutations_observed": False,
            },
        }
    )
    posture = build_network_management_posture_v1(
        source_inventory_contract=inventory["contract"],
        findings=[
            {"reason_code": "legacy_ssh_v1_enabled", "severity": "high"},
            {"reason_code": "legacy_ssh_crypto_observed", "severity": "medium"},
        ],
        complete=True,
    )

    assert inventory["contract"]["id"] == NETWORK_DEVICE_INVENTORY_CONTRACT_ID
    assert inventory["schema_ref"] == NETWORK_DEVICE_INVENTORY_SCHEMA_REF
    assert posture["contract"]["id"] == NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID
    assert posture["schema_ref"] == NETWORK_MANAGEMENT_POSTURE_SCHEMA_REF
    assert posture["assessment"]["state"] == "degraded"
    assert validate_network_device_inventory_v1(inventory) == []
    assert validate_network_management_posture_v1(posture) == []


def test_network_fact_contract_v1_schema_files_are_packaged() -> None:
    refs = [
        (NETWORK_DEVICE_INVENTORY_SCHEMA_REF, NETWORK_DEVICE_INVENTORY_CONTRACT_ID),
        (NETWORK_MANAGEMENT_POSTURE_SCHEMA_REF, NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID),
    ]

    for schema_ref, contract_id in refs:
        schema = resources.files("tecrax").joinpath(*schema_ref.split("/"))
        text = schema.read_text(encoding="utf-8")
        assert contract_id in text


def test_network_fact_contract_v1_rejects_malformed_payloads() -> None:
    inventory = build_network_device_inventory_v1(
        {
            "target": "network-device-01",
            "observation_scope": "network_cli_readonly",
            "device": {
                "system_name": "TL-SG2452",
                "system_description": "48-Port Gigabit Smart Switch",
                "hardware_version": "TL-SG2452 1.0",
                "software_version": "1.0.4 Build",
            },
            "management_access": {
                "ssh_server_enabled": True,
                "ssh_protocol_v1_enabled": True,
                "ssh_protocol_v2_enabled": True,
                "idle_timeout_seconds": 120,
                "max_clients": 5,
            },
            "hardening_observations": {
                "legacy_ssh_v1_enabled": True,
                "legacy_crypto_observed": True,
                "mutations_observed": False,
            },
        }
    )
    inventory["schema_ref"] = "schemas/other.schema.json"
    inventory["hardening_observations"]["mutations_observed"] = True
    posture = build_network_management_posture_v1(
        source_inventory_contract=inventory["contract"],
        findings=[{"reason_code": "legacy_ssh_v1_enabled", "severity": "high"}],
        complete=True,
    )
    posture["findings"][0]["reason_code"] = ""

    assert (
        "network_device_inventory.schema_ref_mismatch"
        in validate_network_device_inventory_v1(inventory)
    )
    assert (
        "network_device_inventory.mutations_must_be_false"
        in validate_network_device_inventory_v1(inventory)
    )
    assert (
        "network_management_posture.invalid_finding:reason_code"
        in validate_network_management_posture_v1(posture)
    )


def test_raw_connector_output_is_rejected() -> None:
    facts = build_ntp_local_health_v1(
        synchronized=True,
        systemd_ntp_enabled=True,
        service="ntp",
        service_state="active",
    )
    facts["stdout"] = "unbounded"

    assert "raw_output_forbidden" in validate_facts(facts)
