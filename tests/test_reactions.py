from __future__ import annotations

from pathlib import Path

import pytest

from rexecop.profile.loader import load_profile
from rexecop.reaction.compiler import compile_reaction_pack
from rexecop.reaction.evaluator import evaluate_reaction
from rexecop.reaction.model import ReactionContext

from tecrax import build_monitoring_host_observation, profile_root
from tecrax.contracts import finalize_facts


def _diagnosis(
    *,
    host: str = "healthy",
    ntp: str = "healthy",
    docker: str = "healthy",
    zabbix: str = "healthy",
    adguard: str = "healthy",
    portainer: str = "healthy",
    host_security: str = "healthy",
    ntp_server: str = "healthy",
) -> dict:
    component_states = {
        "host_inventory": host,
        "ntp": ntp,
        "docker": docker,
        "zabbix": zabbix,
        "adguard": adguard,
        "portainer": portainer,
        "host_security": host_security,
        "ntp_server": ntp_server,
    }
    payload = {
        "aggregation_completed": True,
        "schema_ref": "schemas/monitoring_host_diagnosis.v1.schema.json",
        "coverage_status": "partial",
        "observed_health": (
            "healthy" if set(component_states.values()) == {"healthy"} else "degraded"
        ),
        "components": {
            component: {"status": status} for component, status in component_states.items()
        },
        "findings": [
            {
                "kind": "monitoring.observed_healthy",
                "component": "monitoring_host",
                "reason_code": "all_observed_components_healthy",
                "severity": "info",
            }
        ],
        "continued_failures": [],
    }
    return finalize_facts(
        payload,
        contract_id="tecrax.monitoring_host_diagnosis",
        requested=list(payload["components"]),
        observed=list(payload["components"]),
        assessment=payload["observed_health"],
    )


def _evaluate(diagnosis: dict):
    profile = load_profile(Path(profile_root()))
    pack = compile_reaction_pack(profile)
    observation = build_monitoring_host_observation(
        operation_id="op-source",
        target_id="monitoring-host-01",
        diagnosis=diagnosis,
        observed_at="2026-06-22T20:00:00+00:00",
    )
    return observation, evaluate_reaction(pack, observation, ReactionContext())


def test_ntp_finding_selects_existing_readonly_intent() -> None:
    observation, result = _evaluate(_diagnosis(ntp="unhealthy"))
    assert observation["profile_ref"]["id"] == "tecrax"
    assert result.rule.finding_kind == "monitoring.ntp_unhealthy"
    assert result.outcome == "run_intent"
    assert result.intent_ref == "check_ntp_health"


def test_rule_priority_is_stable_when_multiple_components_are_unhealthy() -> None:
    _, result = _evaluate(
        _diagnosis(host="unhealthy", ntp="unhealthy", zabbix="unhealthy")
    )
    assert result.rule.rule_id == "monitoring.host-inventory-unhealthy"
    assert result.intent_ref == "collect_basic_host_inventory"


def test_docker_finding_selects_existing_readonly_intent() -> None:
    _, result = _evaluate(_diagnosis(docker="unhealthy"))

    assert result.rule.finding_kind == "monitoring.docker_services_unhealthy"
    assert result.outcome == "run_intent"
    assert result.intent_ref == "check_docker_services_health"


def test_adguard_finding_selects_existing_readonly_intent() -> None:
    _, result = _evaluate(_diagnosis(adguard="unhealthy"))

    assert result.rule.finding_kind == "monitoring.adguard_unhealthy"
    assert result.outcome == "run_intent"
    assert result.intent_ref == "check_adguard_health"


def test_portainer_finding_selects_existing_readonly_intent() -> None:
    _, result = _evaluate(_diagnosis(portainer="unhealthy"))

    assert result.rule.finding_kind == "monitoring.portainer_unhealthy"
    assert result.outcome == "run_intent"
    assert result.intent_ref == "check_portainer_health"


def test_healthy_implemented_coverage_is_an_explicit_no_op() -> None:
    _, result = _evaluate(_diagnosis())
    assert result.outcome == "no_op"
    assert result.intent_ref is None


@pytest.mark.parametrize(
    ("component_arg", "rule_id"),
    [
        ("host", "monitoring.host-inventory-unavailable"),
        ("ntp", "monitoring.ntp-unavailable"),
        ("zabbix", "monitoring.zabbix-unavailable"),
        ("docker", "monitoring.docker-unavailable"),
        ("adguard", "monitoring.adguard-unavailable"),
        ("portainer", "monitoring.portainer-unavailable"),
        ("host_security", "monitoring.host-security-unavailable"),
        ("ntp_server", "monitoring.ntp-server-unavailable"),
    ],
)
def test_unavailable_states_escalate_through_explicit_rules(
    component_arg: str,
    rule_id: str,
) -> None:
    _, result = _evaluate(_diagnosis(**{component_arg: "unavailable"}))
    assert result.rule.rule_id == rule_id
    assert result.rule.finding_kind == "monitoring.component_unavailable"
    assert result.outcome == "escalate"
    assert result.intent_ref is None
    assert result.matched is True
