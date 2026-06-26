from __future__ import annotations

import json
from pathlib import Path

import pytest
from rexecop.errors import RExecOpValidationError
from rexecop.operation.controller import OperationController
from rexecop.reaction.service import ReactionService
from rexecop.storage.file_store import FileStore

from tecrax import (
    build_monitoring_host_escalation_proposal,
    profile_root,
    validate_monitoring_host_escalation_proposal,
)
from tecrax.contracts import finalize_facts
from tecrax.escalation import EscalationProposalValidationError


def _diagnosis(*, reason_code: str = "ntp_probe_unavailable") -> dict:
    payload = {
        "aggregation_completed": True,
        "schema_ref": "schemas/monitoring_host_diagnosis.v1.schema.json",
        "coverage_status": "partial",
        "observed_health": "degraded",
        "components": {
            "host_inventory": {"status": "healthy"},
            "ntp": {"status": "unavailable", "reason": reason_code},
            "docker": {"status": "healthy"},
            "zabbix": {"status": "healthy"},
            "adguard": {"status": "healthy"},
            "portainer": {"status": "healthy"},
        },
        "findings": [
            {
                "kind": "monitoring.ntp_unhealthy",
                "component": "ntp",
                "reason_code": reason_code,
                "severity": "medium",
            }
        ],
        "continued_failures": [{"step_id": "read_ntp_state", "error_class": "blocked"}],
    }
    return finalize_facts(
        payload,
        contract_id="tecrax.monitoring_host_diagnosis",
        requested=list(payload["components"]),
        observed=list(payload["components"]),
        assessment=payload["observed_health"],
    )


def _rexecop_validate(tmp_path: Path, proposal: dict) -> dict:
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    service = ReactionService(OperationController(store=FileStore(tmp_path / "runtime")))
    return service.validate_proposal(
        profile_path=Path(profile_root()),
        proposal_path=proposal_path,
    )


def test_monitoring_host_escalation_proposal_is_sclite_and_rexecop_compatible(
    tmp_path: Path,
) -> None:
    diagnosis = _diagnosis()

    proposal = build_monitoring_host_escalation_proposal(
        operation_id="op-source",
        reaction_id="reaction-source",
        diagnosis=diagnosis,
        created_at="2026-06-26T14:00:00+00:00",
    )

    validate_monitoring_host_escalation_proposal(proposal)
    result = _rexecop_validate(tmp_path, proposal)
    assert result["status"] == "valid_untrusted_proposal"
    assert result["may_execute"] is False
    assert result["requires_govengine_admission"] is True
    assert proposal["authority"] == {
        "trusted": False,
        "may_execute": False,
        "requires_profile_validation": True,
        "requires_govengine_admission": True,
    }
    assert proposal["suggested_outcome"] == "escalate"
    assert proposal["intent_ref"] is None
    assert "ntp_probe_unavailable" in proposal["explanation"]
    assert "password" not in json.dumps(proposal).lower()


def test_readonly_followup_proposal_still_requires_admission(tmp_path: Path) -> None:
    proposal = build_monitoring_host_escalation_proposal(
        operation_id="op-source",
        reaction_id="reaction-source",
        diagnosis=_diagnosis(),
        suggested_outcome="run_intent",
        intent_ref="check_ntp_health",
        created_at="2026-06-26T14:00:00+00:00",
    )

    result = _rexecop_validate(tmp_path, proposal)

    assert result["status"] == "valid_untrusted_proposal"
    assert result["may_execute"] is False
    assert result["requires_govengine_admission"] is True


def test_escalation_proposal_rejects_unknown_intent() -> None:
    with pytest.raises(EscalationProposalValidationError, match="unknown_intent"):
        build_monitoring_host_escalation_proposal(
            operation_id="op-source",
            reaction_id="reaction-source",
            diagnosis=_diagnosis(),
            suggested_outcome="run_intent",
            intent_ref="restart_zabbix_agent",
            created_at="2026-06-26T14:00:00+00:00",
        )


def test_escalation_proposal_rejects_intent_ref_for_plain_escalation() -> None:
    with pytest.raises(EscalationProposalValidationError, match="intent_ref"):
        build_monitoring_host_escalation_proposal(
            operation_id="op-source",
            reaction_id="reaction-source",
            diagnosis=_diagnosis(),
            suggested_outcome="escalate",
            intent_ref="check_ntp_health",
            created_at="2026-06-26T14:00:00+00:00",
        )


def test_escalation_proposal_rejects_raw_command_payload() -> None:
    proposal = build_monitoring_host_escalation_proposal(
        operation_id="op-source",
        reaction_id="reaction-source",
        diagnosis=_diagnosis(),
        created_at="2026-06-26T14:00:00+00:00",
    )
    proposal["command"] = "ssh target docker exec adguard printenv"

    with pytest.raises(EscalationProposalValidationError, match="invalid_escalation"):
        validate_monitoring_host_escalation_proposal(proposal)


def test_escalation_proposal_rejects_unsafe_evidence_ref() -> None:
    proposal = build_monitoring_host_escalation_proposal(
        operation_id="op-source",
        reaction_id="reaction-source",
        diagnosis=_diagnosis(),
        created_at="2026-06-26T14:00:00+00:00",
    )
    proposal["evidence_refs"] = ["/tmp/raw-output.log"]

    with pytest.raises(EscalationProposalValidationError, match="unsafe_evidence_ref"):
        validate_monitoring_host_escalation_proposal(proposal)


def test_escalation_proposal_rejects_secret_like_explanation() -> None:
    proposal = build_monitoring_host_escalation_proposal(
        operation_id="op-source",
        reaction_id="reaction-source",
        diagnosis=_diagnosis(),
        created_at="2026-06-26T14:00:00+00:00",
    )
    proposal["explanation"] = "token value observed in raw connector output"

    with pytest.raises(EscalationProposalValidationError, match="unsafe_explanation"):
        validate_monitoring_host_escalation_proposal(proposal)


def test_escalation_proposal_rejects_raw_diagnosis_extras() -> None:
    diagnosis = _diagnosis()
    diagnosis["stdout"] = "raw connector output docker exec something"

    with pytest.raises(EscalationProposalValidationError, match="raw_output_forbidden"):
        build_monitoring_host_escalation_proposal(
            operation_id="op-source",
            reaction_id="reaction-source",
            diagnosis=diagnosis,
            created_at="2026-06-26T14:00:00+00:00",
        )


def test_rexecop_rejects_mutated_proposal_after_profile_validation(tmp_path: Path) -> None:
    proposal = build_monitoring_host_escalation_proposal(
        operation_id="op-source",
        reaction_id="reaction-source",
        diagnosis=_diagnosis(),
        suggested_outcome="run_intent",
        intent_ref="check_ntp_health",
        created_at="2026-06-26T14:00:00+00:00",
    )
    proposal["intent_ref"] = "missing_intent"

    with pytest.raises(RExecOpValidationError, match="intent"):
        _rexecop_validate(tmp_path, proposal)
