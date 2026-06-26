from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


COVERAGE_STATES = frozenset({"complete", "partial", "blocked"})
ASSESSMENT_STATES = frozenset({"healthy", "degraded", "unhealthy", "unknown"})
MAX_FACTS_BYTES = 16_384
MAX_SCOPE_ITEMS = 32
MAX_BLOCKERS = 16
MAX_NON_CLAIMS = 16
BASIC_HOST_INVENTORY_CONTRACT_ID = "tecrax.basic_host_inventory"
BASIC_HOST_INVENTORY_CONTRACT_VERSION = "1.0"
BASIC_HOST_INVENTORY_SCHEMA_REF = "schemas/basic_host_inventory.v1.schema.json"
BASIC_HOST_INVENTORY_REQUESTED = [
    "os",
    "kernel",
    "hostname",
    "uptime",
    "load",
    "root_filesystem",
    "memory",
]
NTP_LOCAL_HEALTH_CONTRACT_ID = "tecrax.ntp_local_health"
NTP_LOCAL_HEALTH_CONTRACT_VERSION = "1.0"
NTP_LOCAL_HEALTH_SCHEMA_REF = "schemas/ntp_local_health.v1.schema.json"
NTP_LOCAL_HEALTH_REQUESTED = ["local_synchronization", "daemon_state"]
DOCKER_SERVICE_HEALTH_CONTRACT_ID = "tecrax.docker_service_health"
DOCKER_SERVICE_HEALTH_CONTRACT_VERSION = "1.0"
DOCKER_SERVICE_HEALTH_SCHEMA_REF = "schemas/docker_service_health.v1.schema.json"
DOCKER_SERVICE_HEALTH_REQUESTED = ["docker.service", "docker.socket"]
HOST_SECURITY_POSTURE_CONTRACT_ID = "tecrax.host_security_posture"
HOST_SECURITY_POSTURE_CONTRACT_VERSION = "1.0"
HOST_SECURITY_POSTURE_SCHEMA_REF = "schemas/host_security_posture.v1.schema.json"
HOST_SECURITY_POSTURE_REQUESTED = [
    "unattended_upgrades",
    "aslr",
    "dmesg_restrict",
    "reboot_required",
]
NTP_SERVER_OBSERVATION_CONTRACT_ID = "tecrax.ntp_server_observation"
NTP_SERVER_OBSERVATION_CONTRACT_VERSION = "1.0"
NTP_SERVER_OBSERVATION_SCHEMA_REF = "schemas/ntp_server_observation.v1.schema.json"
NTP_SERVER_OBSERVATION_REQUESTED = [
    "daemon_state",
    "stratum",
    "leap",
    "offset",
    "root_delay",
    "root_dispersion",
]
NETWORK_DEVICE_INVENTORY_CONTRACT_ID = "tecrax.network_device_inventory"
NETWORK_DEVICE_INVENTORY_CONTRACT_VERSION = "1.0"
NETWORK_DEVICE_INVENTORY_SCHEMA_REF = "schemas/network_device_inventory.v1.schema.json"
NETWORK_DEVICE_INVENTORY_REQUESTED = ["device_identity", "ssh_management_posture"]
NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID = "tecrax.network_management_posture"
NETWORK_MANAGEMENT_POSTURE_CONTRACT_VERSION = "1.0"
NETWORK_MANAGEMENT_POSTURE_SCHEMA_REF = "schemas/network_management_posture.v1.schema.json"
NETWORK_MANAGEMENT_POSTURE_REQUESTED = ["ssh_protocols", "ssh_crypto", "idle_timeout"]


@dataclass(frozen=True)
class OsReleaseV1:
    pretty_name: str
    id: str
    version_id: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "OsReleaseV1":
        return cls(
            pretty_name=_bounded_text(value.get("pretty_name"), limit=256),
            id=_bounded_text(value.get("id"), limit=64),
            version_id=_bounded_text(value.get("version_id"), limit=64),
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "pretty_name": self.pretty_name,
            "id": self.id,
            "version_id": self.version_id,
        }


@dataclass(frozen=True)
class LoadAverageV1:
    one_minute: float | None
    five_minutes: float | None
    fifteen_minutes: float | None
    runnable_processes: int | None
    total_processes: int | None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "LoadAverageV1":
        return cls(
            one_minute=_optional_float(value.get("one_minute")),
            five_minutes=_optional_float(value.get("five_minutes")),
            fifteen_minutes=_optional_float(value.get("fifteen_minutes")),
            runnable_processes=_optional_non_negative_int(value.get("runnable_processes")),
            total_processes=_optional_non_negative_int(value.get("total_processes")),
        )

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "one_minute": self.one_minute,
            "five_minutes": self.five_minutes,
            "fifteen_minutes": self.fifteen_minutes,
            "runnable_processes": self.runnable_processes,
            "total_processes": self.total_processes,
        }


@dataclass(frozen=True)
class RootFilesystemV1:
    filesystem: str
    blocks_1024: int | None
    used_1024: int | None
    available_1024: int | None
    capacity: str
    mounted_on: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "RootFilesystemV1":
        return cls(
            filesystem=_bounded_text(value.get("filesystem"), limit=128),
            blocks_1024=_optional_non_negative_int(value.get("blocks_1024")),
            used_1024=_optional_non_negative_int(value.get("used_1024")),
            available_1024=_optional_non_negative_int(value.get("available_1024")),
            capacity=_bounded_text(value.get("capacity"), limit=16),
            mounted_on=_bounded_text(value.get("mounted_on"), limit=128),
        )

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "filesystem": self.filesystem,
            "blocks_1024": self.blocks_1024,
            "used_1024": self.used_1024,
            "available_1024": self.available_1024,
            "capacity": self.capacity,
            "mounted_on": self.mounted_on,
        }


@dataclass(frozen=True)
class MemoryMiBV1:
    total: int | None
    used: int | None
    free: int | None
    shared: int | None
    buff_cache: int | None
    available: int | None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "MemoryMiBV1":
        return cls(
            total=_optional_non_negative_int(value.get("total")),
            used=_optional_non_negative_int(value.get("used")),
            free=_optional_non_negative_int(value.get("free")),
            shared=_optional_non_negative_int(value.get("shared")),
            buff_cache=_optional_non_negative_int(value.get("buff_cache")),
            available=_optional_non_negative_int(value.get("available")),
        )

    def as_dict(self) -> dict[str, int | None]:
        return {
            "total": self.total,
            "used": self.used,
            "free": self.free,
            "shared": self.shared,
            "buff_cache": self.buff_cache,
            "available": self.available,
        }


@dataclass(frozen=True)
class BasicHostInventoryV1:
    target: str
    os: OsReleaseV1
    kernel: str
    hostname: str
    uptime: str
    load_average: LoadAverageV1
    root_filesystem: RootFilesystemV1
    memory_mib: MemoryMiBV1

    @classmethod
    def from_parts(
        cls,
        *,
        target: str,
        os: dict[str, Any],
        kernel: str,
        hostname: str,
        uptime: str,
        load_average: dict[str, Any],
        root_filesystem: dict[str, Any],
        memory_mib: dict[str, Any],
    ) -> "BasicHostInventoryV1":
        return cls(
            target=_bounded_text(target, limit=128),
            os=OsReleaseV1.from_mapping(os),
            kernel=_bounded_text(kernel, limit=256),
            hostname=_bounded_text(hostname, limit=128),
            uptime=_bounded_text(uptime, limit=256),
            load_average=LoadAverageV1.from_mapping(load_average),
            root_filesystem=RootFilesystemV1.from_mapping(root_filesystem),
            memory_mib=MemoryMiBV1.from_mapping(memory_mib),
        )

    @property
    def complete(self) -> bool:
        return all(
            (
                self.target,
                self.os.id,
                self.kernel,
                self.hostname,
                self.uptime,
                self.load_average.one_minute is not None,
                self.root_filesystem.mounted_on == "/",
                self.memory_mib.total is not None,
            )
        )

    def payload(self) -> dict[str, Any]:
        return {
            "schema_ref": BASIC_HOST_INVENTORY_SCHEMA_REF,
            "target": self.target,
            "os": self.os.as_dict(),
            "kernel": self.kernel,
            "hostname": self.hostname,
            "uptime": self.uptime,
            "load_average": self.load_average.as_dict(),
            "root_filesystem": self.root_filesystem.as_dict(),
            "memory_mib": self.memory_mib.as_dict(),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class NtpLocalHealthV1:
    synchronized: bool
    systemd_ntp_enabled: bool
    service: str
    service_state: str

    @classmethod
    def from_parts(
        cls,
        *,
        synchronized: bool,
        systemd_ntp_enabled: bool,
        service: str,
        service_state: str,
    ) -> "NtpLocalHealthV1":
        return cls(
            synchronized=bool(synchronized),
            systemd_ntp_enabled=bool(systemd_ntp_enabled),
            service=_bounded_text(service, limit=32),
            service_state=_bounded_text(service_state, limit=32),
        )

    @property
    def healthy(self) -> bool:
        return self.synchronized and self.service_state == "active"

    def payload(self) -> dict[str, Any]:
        return {
            "schema_ref": NTP_LOCAL_HEALTH_SCHEMA_REF,
            "synchronized": self.synchronized,
            "systemd_ntp_enabled": self.systemd_ntp_enabled,
            "service": self.service,
            "service_state": self.service_state,
            "healthy": self.healthy,
        }


@dataclass(frozen=True)
class DockerServiceHealthV1:
    observation_scope: str
    service: str
    service_load_state: str
    service_active_state: str
    service_sub_state: str
    service_unit_file_state: str
    socket: str
    socket_load_state: str
    socket_active_state: str
    socket_sub_state: str
    socket_unit_file_state: str
    container_runtime_state: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "DockerServiceHealthV1":
        return cls(
            observation_scope=_bounded_text(value.get("observation_scope"), limit=64),
            service=_bounded_text(value.get("service"), limit=64),
            service_load_state=_bounded_text(value.get("service_load_state"), limit=64),
            service_active_state=_bounded_text(value.get("service_active_state"), limit=64),
            service_sub_state=_bounded_text(value.get("service_sub_state"), limit=64),
            service_unit_file_state=_bounded_text(
                value.get("service_unit_file_state"), limit=64
            ),
            socket=_bounded_text(value.get("socket"), limit=64),
            socket_load_state=_bounded_text(value.get("socket_load_state"), limit=64),
            socket_active_state=_bounded_text(value.get("socket_active_state"), limit=64),
            socket_sub_state=_bounded_text(value.get("socket_sub_state"), limit=64),
            socket_unit_file_state=_bounded_text(
                value.get("socket_unit_file_state"), limit=64
            ),
            container_runtime_state=_bounded_text(
                value.get("container_runtime_state"), limit=64
            ),
        )

    @property
    def healthy(self) -> bool:
        return self.service_load_state == "loaded" and self.service_active_state == "active"

    def payload(self) -> dict[str, Any]:
        return {
            "schema_ref": DOCKER_SERVICE_HEALTH_SCHEMA_REF,
            "observation_scope": self.observation_scope,
            "service": self.service,
            "service_load_state": self.service_load_state,
            "service_active_state": self.service_active_state,
            "service_sub_state": self.service_sub_state,
            "service_unit_file_state": self.service_unit_file_state,
            "socket": self.socket,
            "socket_load_state": self.socket_load_state,
            "socket_active_state": self.socket_active_state,
            "socket_sub_state": self.socket_sub_state,
            "socket_unit_file_state": self.socket_unit_file_state,
            "container_runtime_state": self.container_runtime_state,
            "healthy": self.healthy,
        }


@dataclass(frozen=True)
class HostSecurityPostureV1:
    signals: dict[str, bool | int | None]
    complete: bool
    healthy: bool

    @classmethod
    def from_parts(
        cls,
        *,
        signals: dict[str, Any],
        complete: bool,
        healthy: bool,
    ) -> "HostSecurityPostureV1":
        return cls(
            signals={
                "unattended_upgrades_enabled": bool(
                    signals.get("unattended_upgrades_enabled")
                ),
                "aslr_mode": _optional_non_negative_int(signals.get("aslr_mode")),
                "dmesg_restrict": _optional_non_negative_int(
                    signals.get("dmesg_restrict")
                ),
                "reboot_required": bool(signals.get("reboot_required")),
            },
            complete=bool(complete),
            healthy=bool(healthy),
        )

    def payload(self) -> dict[str, Any]:
        return {
            "schema_ref": HOST_SECURITY_POSTURE_SCHEMA_REF,
            "signals": dict(self.signals),
            "complete": self.complete,
            "healthy": self.healthy,
        }


@dataclass(frozen=True)
class NtpServerVariablesV1:
    stratum: int | None
    leap: int | None
    offset_ms: float | None
    root_delay_ms: float | None
    root_dispersion_ms: float | None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "NtpServerVariablesV1":
        return cls(
            stratum=_optional_non_negative_int(value.get("stratum")),
            leap=_optional_non_negative_int(value.get("leap")),
            offset_ms=_optional_signed_float(value.get("offset_ms")),
            root_delay_ms=_optional_signed_float(value.get("root_delay_ms")),
            root_dispersion_ms=_optional_signed_float(value.get("root_dispersion_ms")),
        )

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "stratum": self.stratum,
            "leap": self.leap,
            "offset_ms": self.offset_ms,
            "root_delay_ms": self.root_delay_ms,
            "root_dispersion_ms": self.root_dispersion_ms,
        }


@dataclass(frozen=True)
class NtpServerObservationV1:
    daemon_state: str
    serving_state: str
    system_variables: NtpServerVariablesV1
    healthy: bool

    @classmethod
    def from_parts(
        cls,
        *,
        daemon_state: str,
        serving_state: str,
        system_variables: dict[str, Any],
        healthy: bool,
    ) -> "NtpServerObservationV1":
        return cls(
            daemon_state=_bounded_text(daemon_state, limit=32),
            serving_state=_bounded_text(serving_state, limit=64),
            system_variables=NtpServerVariablesV1.from_mapping(system_variables),
            healthy=bool(healthy),
        )

    @property
    def complete(self) -> bool:
        return (
            self.daemon_state == "active"
            and self.system_variables.stratum is not None
            and self.system_variables.leap is not None
        )

    def payload(self) -> dict[str, Any]:
        return {
            "schema_ref": NTP_SERVER_OBSERVATION_SCHEMA_REF,
            "daemon_state": self.daemon_state,
            "serving_state": self.serving_state,
            "system_variables": self.system_variables.as_dict(),
            "healthy": self.healthy,
        }


@dataclass(frozen=True)
class NetworkDeviceIdentityV1:
    system_name: str
    system_description: str
    hardware_version: str
    software_version: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "NetworkDeviceIdentityV1":
        return cls(
            system_name=_bounded_text(value.get("system_name"), limit=128),
            system_description=_bounded_text(value.get("system_description"), limit=256),
            hardware_version=_bounded_text(value.get("hardware_version"), limit=128),
            software_version=_bounded_text(value.get("software_version"), limit=128),
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "system_name": self.system_name,
            "system_description": self.system_description,
            "hardware_version": self.hardware_version,
            "software_version": self.software_version,
        }


@dataclass(frozen=True)
class NetworkManagementAccessV1:
    ssh_server_enabled: bool | None
    ssh_protocol_v1_enabled: bool | None
    ssh_protocol_v2_enabled: bool | None
    idle_timeout_seconds: int | None
    max_clients: int | None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "NetworkManagementAccessV1":
        return cls(
            ssh_server_enabled=_optional_bool(value.get("ssh_server_enabled")),
            ssh_protocol_v1_enabled=_optional_bool(value.get("ssh_protocol_v1_enabled")),
            ssh_protocol_v2_enabled=_optional_bool(value.get("ssh_protocol_v2_enabled")),
            idle_timeout_seconds=_optional_non_negative_int(
                value.get("idle_timeout_seconds")
            ),
            max_clients=_optional_non_negative_int(value.get("max_clients")),
        )

    def as_dict(self) -> dict[str, bool | int | None]:
        return {
            "ssh_server_enabled": self.ssh_server_enabled,
            "ssh_protocol_v1_enabled": self.ssh_protocol_v1_enabled,
            "ssh_protocol_v2_enabled": self.ssh_protocol_v2_enabled,
            "idle_timeout_seconds": self.idle_timeout_seconds,
            "max_clients": self.max_clients,
        }


@dataclass(frozen=True)
class NetworkHardeningObservationsV1:
    legacy_ssh_v1_enabled: bool
    legacy_crypto_observed: bool
    mutations_observed: bool

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "NetworkHardeningObservationsV1":
        return cls(
            legacy_ssh_v1_enabled=bool(value.get("legacy_ssh_v1_enabled")),
            legacy_crypto_observed=bool(value.get("legacy_crypto_observed")),
            mutations_observed=bool(value.get("mutations_observed")),
        )

    def as_dict(self) -> dict[str, bool]:
        return {
            "legacy_ssh_v1_enabled": self.legacy_ssh_v1_enabled,
            "legacy_crypto_observed": self.legacy_crypto_observed,
            "mutations_observed": self.mutations_observed,
        }


@dataclass(frozen=True)
class NetworkDeviceInventoryV1:
    target: str
    observation_scope: str
    device: NetworkDeviceIdentityV1
    management_access: NetworkManagementAccessV1
    hardening_observations: NetworkHardeningObservationsV1

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "NetworkDeviceInventoryV1":
        device = value.get("device")
        management = value.get("management_access")
        hardening = value.get("hardening_observations")
        return cls(
            target=_bounded_text(value.get("target"), limit=128),
            observation_scope=_bounded_text(value.get("observation_scope"), limit=64),
            device=NetworkDeviceIdentityV1.from_mapping(
                device if isinstance(device, dict) else {}
            ),
            management_access=NetworkManagementAccessV1.from_mapping(
                management if isinstance(management, dict) else {}
            ),
            hardening_observations=NetworkHardeningObservationsV1.from_mapping(
                hardening if isinstance(hardening, dict) else {}
            ),
        )

    @property
    def complete(self) -> bool:
        return all(
            (
                self.device.system_name,
                self.device.hardware_version,
                self.device.software_version,
                self.management_access.ssh_server_enabled is not None,
                self.management_access.ssh_protocol_v2_enabled is not None,
            )
        )

    def payload(self) -> dict[str, Any]:
        return {
            "schema_ref": NETWORK_DEVICE_INVENTORY_SCHEMA_REF,
            "target": self.target,
            "observation_scope": self.observation_scope,
            "device": self.device.as_dict(),
            "management_access": self.management_access.as_dict(),
            "hardening_observations": self.hardening_observations.as_dict(),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class NetworkManagementPostureV1:
    source_inventory_contract: dict[str, str] | None
    findings: tuple[dict[str, str], ...]
    complete: bool

    @classmethod
    def from_parts(
        cls,
        *,
        source_inventory_contract: Any,
        findings: list[dict[str, Any]],
        complete: bool,
    ) -> "NetworkManagementPostureV1":
        return cls(
            source_inventory_contract=_contract_ref(source_inventory_contract),
            findings=tuple(_bounded_finding(item) for item in findings[:16]),
            complete=bool(complete),
        )

    @property
    def assessment(self) -> str:
        if not self.complete:
            return "unknown"
        return "degraded" if self.findings else "healthy"

    def payload(self) -> dict[str, Any]:
        return {
            "schema_ref": NETWORK_MANAGEMENT_POSTURE_SCHEMA_REF,
            "source_inventory_contract": self.source_inventory_contract,
            "findings": list(self.findings),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class FactsContractSpec:
    contract_id: str
    version: str
    required_payload_keys: tuple[str, ...]


FACTS_CONTRACTS = {
    spec.contract_id: spec
    for spec in (
        FactsContractSpec(
            BASIC_HOST_INVENTORY_CONTRACT_ID,
            BASIC_HOST_INVENTORY_CONTRACT_VERSION,
            ("target", "os", "kernel"),
        ),
        FactsContractSpec(
            NTP_LOCAL_HEALTH_CONTRACT_ID,
            NTP_LOCAL_HEALTH_CONTRACT_VERSION,
            ("synchronized", "service_state"),
        ),
        FactsContractSpec(
            DOCKER_SERVICE_HEALTH_CONTRACT_ID,
            DOCKER_SERVICE_HEALTH_CONTRACT_VERSION,
            ("service_active_state",),
        ),
        FactsContractSpec(
            "tecrax.zabbix_api_reachability",
            "1.0",
            ("application_reachable",),
        ),
        FactsContractSpec(
            "tecrax.adguard_reachability",
            "1.0",
            ("dns_resolves", "web_login_reachable"),
        ),
        FactsContractSpec("tecrax.portainer_reachability", "1.0", ("api_reachable",)),
        FactsContractSpec(
            NETWORK_DEVICE_INVENTORY_CONTRACT_ID,
            NETWORK_DEVICE_INVENTORY_CONTRACT_VERSION,
            ("target", "device", "management_access"),
        ),
        FactsContractSpec("tecrax.monitoring_host_diagnosis", "1.0", ("components",)),
        FactsContractSpec(
            HOST_SECURITY_POSTURE_CONTRACT_ID,
            HOST_SECURITY_POSTURE_CONTRACT_VERSION,
            ("signals",),
        ),
        FactsContractSpec(
            NTP_SERVER_OBSERVATION_CONTRACT_ID,
            NTP_SERVER_OBSERVATION_CONTRACT_VERSION,
            ("daemon_state", "system_variables"),
        ),
        FactsContractSpec(
            NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID,
            NETWORK_MANAGEMENT_POSTURE_CONTRACT_VERSION,
            ("findings", "source_inventory_contract"),
        ),
    )
}


def build_basic_host_inventory_v1(
    *,
    target: str,
    os: dict[str, Any],
    kernel: str,
    hostname: str,
    uptime: str,
    load_average: dict[str, Any],
    root_filesystem: dict[str, Any],
    memory_mib: dict[str, Any],
) -> dict[str, Any]:
    model = BasicHostInventoryV1.from_parts(
        target=target,
        os=os,
        kernel=kernel,
        hostname=hostname,
        uptime=uptime,
        load_average=load_average,
        root_filesystem=root_filesystem,
        memory_mib=memory_mib,
    )
    complete = model.complete
    return finalize_facts(
        model.payload(),
        contract_id=BASIC_HOST_INVENTORY_CONTRACT_ID,
        requested=BASIC_HOST_INVENTORY_REQUESTED,
        observed=BASIC_HOST_INVENTORY_REQUESTED if complete else [],
        not_observed=[] if complete else ["one_or_more_inventory_fields"],
        assessment="healthy" if complete else "unknown",
        non_claims=["packages", "users", "processes", "network_listeners"],
    )


def validate_basic_host_inventory_v1(facts: dict[str, Any]) -> list[str]:
    return validate_facts(
        facts,
        expected_contract_id=BASIC_HOST_INVENTORY_CONTRACT_ID,
    )


def build_ntp_local_health_v1(
    *,
    synchronized: bool,
    systemd_ntp_enabled: bool,
    service: str,
    service_state: str,
) -> dict[str, Any]:
    model = NtpLocalHealthV1.from_parts(
        synchronized=synchronized,
        systemd_ntp_enabled=systemd_ntp_enabled,
        service=service,
        service_state=service_state,
    )
    return finalize_facts(
        model.payload(),
        contract_id=NTP_LOCAL_HEALTH_CONTRACT_ID,
        requested=NTP_LOCAL_HEALTH_REQUESTED,
        observed=NTP_LOCAL_HEALTH_REQUESTED,
        assessment="healthy" if model.healthy else "unhealthy",
        non_claims=["server_serving_state", "peer_identity", "offset", "stratum"],
    )


def validate_ntp_local_health_v1(facts: dict[str, Any]) -> list[str]:
    return validate_facts(facts, expected_contract_id=NTP_LOCAL_HEALTH_CONTRACT_ID)


def build_docker_service_health_v1(payload: dict[str, Any]) -> dict[str, Any]:
    model = DockerServiceHealthV1.from_mapping(payload)
    return finalize_facts(
        model.payload(),
        contract_id=DOCKER_SERVICE_HEALTH_CONTRACT_ID,
        requested=DOCKER_SERVICE_HEALTH_REQUESTED,
        observed=DOCKER_SERVICE_HEALTH_REQUESTED,
        not_observed=["containers", "images", "stacks"],
        assessment="healthy" if model.healthy else "unhealthy",
        non_claims=["container_health", "docker_socket", "container_logs"],
    )


def validate_docker_service_health_v1(facts: dict[str, Any]) -> list[str]:
    return validate_facts(facts, expected_contract_id=DOCKER_SERVICE_HEALTH_CONTRACT_ID)


def build_host_security_posture_v1(
    *,
    signals: dict[str, Any],
    complete: bool,
    healthy: bool,
) -> dict[str, Any]:
    model = HostSecurityPostureV1.from_parts(
        signals=signals,
        complete=complete,
        healthy=healthy,
    )
    return finalize_facts(
        model.payload(),
        contract_id=HOST_SECURITY_POSTURE_CONTRACT_ID,
        requested=HOST_SECURITY_POSTURE_REQUESTED,
        observed=HOST_SECURITY_POSTURE_REQUESTED if model.complete else [],
        not_observed=[] if model.complete else ["one_or_more_security_signals"],
        assessment="healthy" if model.healthy else ("degraded" if model.complete else "unknown"),
        non_claims=["cis_compliance", "users", "packages", "ports", "ssh_configuration"],
    )


def validate_host_security_posture_v1(facts: dict[str, Any]) -> list[str]:
    return validate_facts(facts, expected_contract_id=HOST_SECURITY_POSTURE_CONTRACT_ID)


def build_ntp_server_observation_v1(
    *,
    daemon_state: str,
    serving_state: str,
    system_variables: dict[str, Any],
    healthy: bool,
) -> dict[str, Any]:
    model = NtpServerObservationV1.from_parts(
        daemon_state=daemon_state,
        serving_state=serving_state,
        system_variables=system_variables,
        healthy=healthy,
    )
    return finalize_facts(
        model.payload(),
        contract_id=NTP_SERVER_OBSERVATION_CONTRACT_ID,
        requested=NTP_SERVER_OBSERVATION_REQUESTED,
        observed=NTP_SERVER_OBSERVATION_REQUESTED if model.complete else [],
        not_observed=[] if model.complete else ["one_or_more_ntp_server_fields"],
        assessment="healthy" if model.healthy else ("degraded" if model.complete else "unknown"),
        non_claims=[
            "peer_identity",
            "peer_address",
            "remote_client_reachability",
            "firewall_state",
        ],
    )


def validate_ntp_server_observation_v1(facts: dict[str, Any]) -> list[str]:
    return validate_facts(facts, expected_contract_id=NTP_SERVER_OBSERVATION_CONTRACT_ID)


def build_network_device_inventory_v1(payload: dict[str, Any]) -> dict[str, Any]:
    model = NetworkDeviceInventoryV1.from_mapping(payload)
    return finalize_facts(
        model.payload(),
        contract_id=NETWORK_DEVICE_INVENTORY_CONTRACT_ID,
        requested=NETWORK_DEVICE_INVENTORY_REQUESTED,
        observed=NETWORK_DEVICE_INVENTORY_REQUESTED if model.complete else [],
        not_observed=[] if model.complete else ["one_or_more_device_fields"],
        assessment="healthy" if model.complete else "unknown",
        non_claims=["running_configuration", "vlans", "ports", "snmp_telemetry"],
    )


def validate_network_device_inventory_v1(facts: dict[str, Any]) -> list[str]:
    return validate_facts(facts, expected_contract_id=NETWORK_DEVICE_INVENTORY_CONTRACT_ID)


def build_network_management_posture_v1(
    *,
    source_inventory_contract: Any,
    findings: list[dict[str, Any]],
    complete: bool,
) -> dict[str, Any]:
    model = NetworkManagementPostureV1.from_parts(
        source_inventory_contract=source_inventory_contract,
        findings=findings,
        complete=complete,
    )
    return finalize_facts(
        model.payload(),
        contract_id=NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID,
        requested=NETWORK_MANAGEMENT_POSTURE_REQUESTED,
        observed=NETWORK_MANAGEMENT_POSTURE_REQUESTED if model.complete else [],
        not_observed=[] if model.complete else ["one_or_more_management_fields"],
        assessment=model.assessment,
        non_claims=["running_configuration", "port_security", "vlans", "firmware_compliance"],
    )


def validate_network_management_posture_v1(facts: dict[str, Any]) -> list[str]:
    return validate_facts(facts, expected_contract_id=NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID)


def finalize_facts(
    payload: dict[str, Any],
    *,
    contract_id: str,
    requested: list[str],
    observed: list[str],
    not_observed: list[str] | None = None,
    blockers: list[str] | None = None,
    assessment: str,
    non_claims: list[str] | None = None,
) -> dict[str, Any]:
    spec = FACTS_CONTRACTS[contract_id]
    result = dict(payload)
    blocker_values = list(blockers or [])[:MAX_BLOCKERS]
    missing = list(not_observed or [])[:MAX_SCOPE_ITEMS]
    if blocker_values:
        coverage = "blocked"
    elif missing:
        coverage = "partial"
    else:
        coverage = "complete"
    result.update(
        {
            "contract": {"id": spec.contract_id, "version": spec.version},
            "scope": {
                "requested": list(requested)[:MAX_SCOPE_ITEMS],
                "observed": list(observed)[:MAX_SCOPE_ITEMS],
                "not_observed": missing,
            },
            "coverage": {"state": coverage, "blockers": blocker_values},
            "assessment": {"state": assessment},
            "non_claims": list(non_claims or [])[:MAX_NON_CLAIMS],
        }
    )
    errors = validate_facts(result, expected_contract_id=contract_id)
    if errors:
        raise ValueError("invalid_tecrax_facts:" + ",".join(errors))
    return result


def validate_facts(
    facts: dict[str, Any], *, expected_contract_id: str | None = None
) -> list[str]:
    errors: list[str] = []
    contract = facts.get("contract")
    contract_id = str(contract.get("id") or "") if isinstance(contract, dict) else ""
    spec = FACTS_CONTRACTS.get(contract_id)
    if spec is None:
        errors.append("unknown_contract")
        return errors
    if expected_contract_id and contract_id != expected_contract_id:
        errors.append("contract_id_mismatch")
    if contract.get("version") != spec.version:
        errors.append("contract_version_mismatch")
    for key in spec.required_payload_keys:
        if key not in facts:
            errors.append(f"missing_payload_key:{key}")

    coverage = facts.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("state") not in COVERAGE_STATES:
        errors.append("invalid_coverage_state")
    assessment = facts.get("assessment")
    if not isinstance(assessment, dict) or assessment.get("state") not in ASSESSMENT_STATES:
        errors.append("invalid_assessment_state")
    scope = facts.get("scope")
    if not isinstance(scope, dict):
        errors.append("invalid_scope")
    else:
        for key in ("requested", "observed", "not_observed"):
            value = scope.get(key)
            if not isinstance(value, list) or len(value) > MAX_SCOPE_ITEMS:
                errors.append(f"invalid_scope:{key}")
    if _contains_forbidden_key(facts):
        errors.append("raw_output_forbidden")
    encoded = json.dumps(facts, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_FACTS_BYTES:
        errors.append("facts_too_large")
    if contract_id == BASIC_HOST_INVENTORY_CONTRACT_ID:
        errors.extend(_validate_basic_host_inventory_v1_shape(facts))
    if contract_id == NTP_LOCAL_HEALTH_CONTRACT_ID:
        errors.extend(_validate_ntp_local_health_v1_shape(facts))
    if contract_id == DOCKER_SERVICE_HEALTH_CONTRACT_ID:
        errors.extend(_validate_docker_service_health_v1_shape(facts))
    if contract_id == HOST_SECURITY_POSTURE_CONTRACT_ID:
        errors.extend(_validate_host_security_posture_v1_shape(facts))
    if contract_id == NTP_SERVER_OBSERVATION_CONTRACT_ID:
        errors.extend(_validate_ntp_server_observation_v1_shape(facts))
    if contract_id == NETWORK_DEVICE_INVENTORY_CONTRACT_ID:
        errors.extend(_validate_network_device_inventory_v1_shape(facts))
    if contract_id == NETWORK_MANAGEMENT_POSTURE_CONTRACT_ID:
        errors.extend(_validate_network_management_posture_v1_shape(facts))
    return sorted(set(errors))


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in {"stdout", "stderr", "raw_output", "secret", "token"}:
                return True
            if _contains_forbidden_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _validate_basic_host_inventory_v1_shape(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    complete = facts.get("complete") is True
    if facts.get("schema_ref") != BASIC_HOST_INVENTORY_SCHEMA_REF:
        errors.append("basic_host_inventory.schema_ref_mismatch")
    if not isinstance(facts.get("complete"), bool):
        errors.append("basic_host_inventory.invalid_complete")
    if not _bounded_string(facts.get("target"), max_length=128, required=True):
        errors.append("basic_host_inventory.invalid_target")

    os_value = facts.get("os")
    if not isinstance(os_value, dict):
        errors.append("basic_host_inventory.invalid_os")
    else:
        for key in ("pretty_name", "id", "version_id"):
            if not _bounded_string(
                os_value.get(key),
                max_length=256,
                required=complete and key == "id",
            ):
                errors.append(f"basic_host_inventory.invalid_os:{key}")

    for key, limit in (("kernel", 256), ("hostname", 128), ("uptime", 256)):
        if not _bounded_string(facts.get(key), max_length=limit, required=complete):
            errors.append(f"basic_host_inventory.invalid_{key}")

    load = facts.get("load_average")
    if not isinstance(load, dict):
        errors.append("basic_host_inventory.invalid_load_average")
    else:
        for key in ("one_minute", "five_minutes", "fifteen_minutes"):
            if not _optional_number(load.get(key)):
                errors.append(f"basic_host_inventory.invalid_load_average:{key}")
        for key in ("runnable_processes", "total_processes"):
            if not _optional_non_negative_int_value(load.get(key)):
                errors.append(f"basic_host_inventory.invalid_load_average:{key}")

    filesystem = facts.get("root_filesystem")
    if not isinstance(filesystem, dict):
        errors.append("basic_host_inventory.invalid_root_filesystem")
    else:
        if not _bounded_string(
            filesystem.get("mounted_on"),
            max_length=128,
            required=complete,
        ):
            errors.append("basic_host_inventory.invalid_root_filesystem:mounted_on")
        for key in ("blocks_1024", "used_1024", "available_1024"):
            if not _optional_non_negative_int_value(filesystem.get(key)):
                errors.append(f"basic_host_inventory.invalid_root_filesystem:{key}")

    memory = facts.get("memory_mib")
    if not isinstance(memory, dict):
        errors.append("basic_host_inventory.invalid_memory_mib")
    else:
        for key in ("total", "used", "free", "shared", "buff_cache", "available"):
            if not _optional_non_negative_int_value(memory.get(key)):
                errors.append(f"basic_host_inventory.invalid_memory_mib:{key}")

    if complete:
        if isinstance(filesystem, dict) and filesystem.get("mounted_on") != "/":
            errors.append("basic_host_inventory.complete_requires_root_mount")
        if isinstance(memory, dict) and memory.get("total") is None:
            errors.append("basic_host_inventory.complete_requires_memory_total")
    return errors


def _validate_ntp_local_health_v1_shape(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if facts.get("schema_ref") != NTP_LOCAL_HEALTH_SCHEMA_REF:
        errors.append("ntp_local_health.schema_ref_mismatch")
    for key in ("synchronized", "systemd_ntp_enabled", "healthy"):
        if not isinstance(facts.get(key), bool):
            errors.append(f"ntp_local_health.invalid_{key}")
    for key in ("service", "service_state"):
        if not _bounded_string(facts.get(key), max_length=32, required=True):
            errors.append(f"ntp_local_health.invalid_{key}")
    return errors


def _validate_docker_service_health_v1_shape(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if facts.get("schema_ref") != DOCKER_SERVICE_HEALTH_SCHEMA_REF:
        errors.append("docker_service_health.schema_ref_mismatch")
    for key in (
        "observation_scope",
        "service",
        "service_load_state",
        "service_active_state",
        "service_sub_state",
        "service_unit_file_state",
        "socket",
        "socket_load_state",
        "socket_active_state",
        "socket_sub_state",
        "socket_unit_file_state",
        "container_runtime_state",
    ):
        if not _bounded_string(facts.get(key), max_length=64, required=True):
            errors.append(f"docker_service_health.invalid_{key}")
    if not isinstance(facts.get("healthy"), bool):
        errors.append("docker_service_health.invalid_healthy")
    if facts.get("container_runtime_state") != "not_observed":
        errors.append("docker_service_health.container_runtime_must_be_not_observed")
    return errors


def _validate_host_security_posture_v1_shape(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if facts.get("schema_ref") != HOST_SECURITY_POSTURE_SCHEMA_REF:
        errors.append("host_security_posture.schema_ref_mismatch")
    signals = facts.get("signals")
    if not isinstance(signals, dict):
        errors.append("host_security_posture.invalid_signals")
    else:
        for key in ("unattended_upgrades_enabled", "reboot_required"):
            if not isinstance(signals.get(key), bool):
                errors.append(f"host_security_posture.invalid_signals:{key}")
        for key in ("aslr_mode", "dmesg_restrict"):
            if not _optional_non_negative_int_value(signals.get(key)):
                errors.append(f"host_security_posture.invalid_signals:{key}")
    for key in ("complete", "healthy"):
        if not isinstance(facts.get(key), bool):
            errors.append(f"host_security_posture.invalid_{key}")
    return errors


def _validate_ntp_server_observation_v1_shape(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if facts.get("schema_ref") != NTP_SERVER_OBSERVATION_SCHEMA_REF:
        errors.append("ntp_server_observation.schema_ref_mismatch")
    for key, limit in (("daemon_state", 32), ("serving_state", 64)):
        if not _bounded_string(facts.get(key), max_length=limit, required=True):
            errors.append(f"ntp_server_observation.invalid_{key}")
    variables = facts.get("system_variables")
    if not isinstance(variables, dict):
        errors.append("ntp_server_observation.invalid_system_variables")
    else:
        for key in ("stratum", "leap"):
            if not _optional_non_negative_int_value(variables.get(key)):
                errors.append(f"ntp_server_observation.invalid_system_variables:{key}")
        for key in ("offset_ms", "root_delay_ms", "root_dispersion_ms"):
            if not _optional_number(variables.get(key)):
                errors.append(f"ntp_server_observation.invalid_system_variables:{key}")
    if not isinstance(facts.get("healthy"), bool):
        errors.append("ntp_server_observation.invalid_healthy")
    return errors


def _validate_network_device_inventory_v1_shape(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    complete = facts.get("complete") is True
    if facts.get("schema_ref") != NETWORK_DEVICE_INVENTORY_SCHEMA_REF:
        errors.append("network_device_inventory.schema_ref_mismatch")
    if not _bounded_string(facts.get("target"), max_length=128, required=True):
        errors.append("network_device_inventory.invalid_target")
    if not _bounded_string(
        facts.get("observation_scope"), max_length=64, required=True
    ):
        errors.append("network_device_inventory.invalid_observation_scope")
    device = facts.get("device")
    if not isinstance(device, dict):
        errors.append("network_device_inventory.invalid_device")
    else:
        for key in ("system_name", "hardware_version", "software_version"):
            if not _bounded_string(
                device.get(key), max_length=128, required=complete
            ):
                errors.append(f"network_device_inventory.invalid_device:{key}")
        if not _bounded_string(
            device.get("system_description"), max_length=256, required=False
        ):
            errors.append("network_device_inventory.invalid_device:system_description")
    management = facts.get("management_access")
    if not isinstance(management, dict):
        errors.append("network_device_inventory.invalid_management_access")
    else:
        for key in (
            "ssh_server_enabled",
            "ssh_protocol_v1_enabled",
            "ssh_protocol_v2_enabled",
        ):
            if not _optional_bool_value(management.get(key)):
                errors.append(f"network_device_inventory.invalid_management_access:{key}")
        for key in ("idle_timeout_seconds", "max_clients"):
            if not _optional_non_negative_int_value(management.get(key)):
                errors.append(f"network_device_inventory.invalid_management_access:{key}")
    hardening = facts.get("hardening_observations")
    if not isinstance(hardening, dict):
        errors.append("network_device_inventory.invalid_hardening_observations")
    else:
        for key in (
            "legacy_ssh_v1_enabled",
            "legacy_crypto_observed",
            "mutations_observed",
        ):
            if not isinstance(hardening.get(key), bool):
                errors.append(
                    f"network_device_inventory.invalid_hardening_observations:{key}"
                )
        if hardening.get("mutations_observed") is not False:
            errors.append("network_device_inventory.mutations_must_be_false")
    if not isinstance(facts.get("complete"), bool):
        errors.append("network_device_inventory.invalid_complete")
    return errors


def _validate_network_management_posture_v1_shape(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if facts.get("schema_ref") != NETWORK_MANAGEMENT_POSTURE_SCHEMA_REF:
        errors.append("network_management_posture.schema_ref_mismatch")
    source = facts.get("source_inventory_contract")
    if source is not None:
        if not isinstance(source, dict):
            errors.append("network_management_posture.invalid_source_inventory_contract")
        else:
            for key in ("id", "version"):
                if not _bounded_string(source.get(key), max_length=128, required=True):
                    errors.append(
                        f"network_management_posture.invalid_source_inventory_contract:{key}"
                    )
    findings = facts.get("findings")
    if not isinstance(findings, list) or len(findings) > 16:
        errors.append("network_management_posture.invalid_findings")
    else:
        for item in findings:
            if not isinstance(item, dict):
                errors.append("network_management_posture.invalid_finding")
                continue
            if not _bounded_string(item.get("reason_code"), max_length=64, required=True):
                errors.append("network_management_posture.invalid_finding:reason_code")
            if not _bounded_string(item.get("severity"), max_length=16, required=True):
                errors.append("network_management_posture.invalid_finding:severity")
    if not isinstance(facts.get("complete"), bool):
        errors.append("network_management_posture.invalid_complete")
    return errors


def _bounded_text(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _contract_ref(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    return {
        "id": _bounded_text(value.get("id"), limit=128),
        "version": _bounded_text(value.get("version"), limit=32),
    }


def _bounded_finding(value: dict[str, Any]) -> dict[str, str]:
    return {
        "reason_code": _bounded_text(value.get("reason_code"), limit=64),
        "severity": _bounded_text(value.get("severity"), limit=16),
    }


def _optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(result, 1_000_000.0)), 6)


def _optional_signed_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(-1_000_000.0, min(result, 1_000_000.0)), 6)


def _optional_non_negative_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(result, 1_000_000_000_000))


def _bounded_string(value: Any, *, max_length: int, required: bool) -> bool:
    if not isinstance(value, str):
        return False
    if required and not value:
        return False
    return len(value) <= max_length


def _optional_number(value: Any) -> bool:
    return value is None or isinstance(value, (float, int))


def _optional_non_negative_int_value(value: Any) -> bool:
    return value is None or (isinstance(value, int) and value >= 0)


def _optional_bool_value(value: Any) -> bool:
    return value is None or isinstance(value, bool)
