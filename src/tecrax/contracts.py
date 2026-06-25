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
        FactsContractSpec("tecrax.ntp_local_health", "1.0", ("synchronized", "service_state")),
        FactsContractSpec("tecrax.docker_service_health", "1.0", ("service_active_state",)),
        FactsContractSpec("tecrax.zabbix_api_reachability", "1.0", ("application_reachable",)),
        FactsContractSpec("tecrax.adguard_reachability", "1.0", ("dns_resolves", "web_login_reachable")),
        FactsContractSpec("tecrax.portainer_reachability", "1.0", ("api_reachable",)),
        FactsContractSpec("tecrax.network_device_inventory", "1.0", ("target", "device", "management_access")),
        FactsContractSpec("tecrax.monitoring_host_diagnosis", "1.0", ("components",)),
        FactsContractSpec("tecrax.host_security_posture", "1.0", ("signals",)),
        FactsContractSpec(
            "tecrax.ntp_server_observation",
            "1.0",
            ("daemon_state", "system_variables"),
        ),
        FactsContractSpec(
            "tecrax.network_management_posture",
            "1.0",
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
    if len(json.dumps(facts, sort_keys=True, separators=(",", ":")).encode("utf-8")) > MAX_FACTS_BYTES:
        errors.append("facts_too_large")
    if contract_id == BASIC_HOST_INVENTORY_CONTRACT_ID:
        errors.extend(_validate_basic_host_inventory_v1_shape(facts))
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


def _bounded_text(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(result, 1_000_000.0)), 6)


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
