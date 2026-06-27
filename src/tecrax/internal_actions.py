from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tecrax.normalizers.diagnostics import aggregate_monitoring_host_diagnosis
from tecrax.normalizers.host import (
    normalize_basic_host_inventory,
    normalize_host_security_posture,
    normalize_ntp_server_observation,
)
from tecrax.normalizers.network import (
    assess_network_device_management_posture,
    normalize_network_device_inventory,
)
from tecrax.normalizers.services import (
    normalize_adguard_health,
    normalize_docker_services_health,
    normalize_ntp_health,
    normalize_portainer_health,
    normalize_zabbix_host_availability_summary,
    normalize_zabbix_health,
    normalize_zabbix_problem_summary,
)
from tecrax.reactions import build_monitoring_host_observation


def build_monitoring_host_reaction_observation(context: Any) -> dict[str, Any]:
    diagnosis = context.shared_state.get("monitoring_host_diagnosis")
    if not isinstance(diagnosis, Mapping):
        raise ValueError("monitoring_host_diagnosis is required")
    observation = build_monitoring_host_observation(
        operation_id=context.operation_id,
        target_id=context.target,
        diagnosis=diagnosis,
    )
    context.shared_state["reaction_observation"] = observation
    return observation


def register_handlers() -> Mapping[str, Any]:
    return {
        "normalize_basic_host_inventory": normalize_basic_host_inventory,
        "normalize_ntp_health": normalize_ntp_health,
        "normalize_docker_services_health": normalize_docker_services_health,
        "normalize_zabbix_health": normalize_zabbix_health,
        "normalize_zabbix_problem_summary": normalize_zabbix_problem_summary,
        "normalize_zabbix_host_availability_summary": (
            normalize_zabbix_host_availability_summary
        ),
        "normalize_adguard_health": normalize_adguard_health,
        "normalize_portainer_health": normalize_portainer_health,
        "normalize_network_device_inventory": normalize_network_device_inventory,
        "normalize_host_security_posture": normalize_host_security_posture,
        "normalize_ntp_server_observation": normalize_ntp_server_observation,
        "assess_network_device_management_posture": assess_network_device_management_posture,
        "aggregate_monitoring_host_diagnosis": aggregate_monitoring_host_diagnosis,
        "build_monitoring_host_reaction_observation": (
            build_monitoring_host_reaction_observation
        ),
    }
