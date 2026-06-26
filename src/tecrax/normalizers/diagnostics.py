from __future__ import annotations

from typing import Any

from rexecop.execution.backend import StepExecutionContext

from tecrax.contracts import (
    MONITORING_HOST_DIAGNOSIS_CONTRACT_ID,
    MONITORING_HOST_DIAGNOSIS_REQUESTED,
    MONITORING_HOST_DIAGNOSIS_SCHEMA_REF,
)
from tecrax.normalizers.common import finalize_and_store

FINDINGS_BY_COMPONENT = {
    "host_inventory": {
        "kind": "monitoring.host_inventory_unhealthy",
        "reason_code": "host_inventory_unhealthy",
        "severity": "medium",
    },
    "ntp": {
        "kind": "monitoring.ntp_unhealthy",
        "reason_code": "ntp_unhealthy",
        "severity": "medium",
    },
    "zabbix": {
        "kind": "monitoring.zabbix_unhealthy",
        "reason_code": "zabbix_unhealthy",
        "severity": "medium",
    },
    "docker": {
        "kind": "monitoring.docker_services_unhealthy",
        "reason_code": "docker_services_unhealthy",
        "severity": "medium",
    },
    "adguard": {
        "kind": "monitoring.adguard_unhealthy",
        "reason_code": "adguard_unhealthy",
        "severity": "medium",
    },
    "portainer": {
        "kind": "monitoring.portainer_unhealthy",
        "reason_code": "portainer_unhealthy",
        "severity": "medium",
    },
    "host_security": {
        "kind": "monitoring.host_security_degraded",
        "reason_code": "host_security_degraded",
        "severity": "medium",
    },
    "ntp_server": {
        "kind": "monitoring.ntp_server_unhealthy",
        "reason_code": "ntp_server_unhealthy",
        "severity": "medium",
    },
}


def aggregate_monitoring_host_diagnosis(
    context: StepExecutionContext,
) -> dict[str, Any]:
    inventory = context.shared_state.get("basic_host_inventory")
    ntp = context.shared_state.get("ntp_health")
    docker = context.shared_state.get("docker_services_health")
    zabbix = context.shared_state.get("zabbix_health")
    adguard = context.shared_state.get("adguard_health")
    portainer = context.shared_state.get("portainer_health")
    security = context.shared_state.get("host_security_posture")
    ntp_server = context.shared_state.get("ntp_server_observation")
    continued = context.shared_state.get("continued_failures")
    failures = []
    if isinstance(continued, dict):
        for step_id, payload in sorted(continued.items()):
            error_class = payload.get("error_class") if isinstance(payload, dict) else ""
            failures.append(
                {"step_id": str(step_id)[:128], "error_class": str(error_class)[:64]}
            )

    components = {
        "host_inventory": _component_status(inventory, "complete"),
        "ntp": _component_status(ntp, "healthy"),
        "zabbix": _component_status(zabbix, "healthy"),
        "docker": _component_status(docker, "healthy", unavailable_reason="not_observed"),
        "adguard": _component_status(
            adguard,
            "healthy",
            unavailable_reason="not_observed",
        ),
        "portainer": _component_status(
            portainer,
            "healthy",
            unavailable_reason="not_observed",
        ),
        "host_security": _component_status(security, "healthy"),
        "ntp_server": _component_status(ntp_server, "healthy"),
    }
    observed = [
        components[name]["status"]
        for name in (
            *MONITORING_HOST_DIAGNOSIS_REQUESTED,
        )
    ]
    findings = _diagnosis_findings(components)
    assessment = "healthy" if all(item == "healthy" for item in observed) else "degraded"
    return finalize_and_store(
        context,
        "monitoring_host_diagnosis",
        {
            "schema_ref": MONITORING_HOST_DIAGNOSIS_SCHEMA_REF,
            "aggregation_completed": True,
            "coverage_status": "partial" if failures else "complete",
            "observed_health": (
                "healthy" if all(item == "healthy" for item in observed) else "degraded"
            ),
            "components": components,
            "findings": findings,
            "continued_failures": failures,
        },
        contract_id=MONITORING_HOST_DIAGNOSIS_CONTRACT_ID,
        requested=list(components),
        observed=[
            name for name, value in components.items() if value["status"] != "unavailable"
        ],
        not_observed=[
            name for name, value in components.items() if value["status"] == "unavailable"
        ],
        assessment=assessment,
        non_claims=["continuous_monitoring", "root_cause", "automatic_remediation"],
    )


def _component_status(
    value: Any, health_key: str, *, unavailable_reason: str = ""
) -> dict[str, str]:
    if not isinstance(value, dict):
        result = {"status": "unavailable"}
        if unavailable_reason:
            result["reason"] = unavailable_reason
        return result
    return {"status": "healthy" if value.get(health_key) is True else "unhealthy"}


def _diagnosis_findings(components: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for component, status in components.items():
        state = status.get("status")
        if state == "healthy":
            continue
        if state == "unavailable":
            findings.append(
                {
                    "kind": "monitoring.component_unavailable",
                    "component": component,
                    "reason_code": f"{component}_unavailable",
                    "severity": "low",
                }
            )
            continue
        template = FINDINGS_BY_COMPONENT.get(component)
        if template is None:
            findings.append(
                {
                    "kind": "monitoring.unclassified_state",
                    "component": component,
                    "reason_code": "unclassified_component_state",
                    "severity": "low",
                }
            )
            continue
        findings.append({"component": component, **template})
    if not findings:
        return [
            {
                "kind": "monitoring.observed_healthy",
                "component": "monitoring_host",
                "reason_code": "all_observed_components_healthy",
                "severity": "info",
            }
        ]
    return findings[:16]
