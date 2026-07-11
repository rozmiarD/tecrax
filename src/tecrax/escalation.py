from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from rexecop.errors import RExecOpValidationError
from rexecop.profile.loader import load_profile
from rexecop.contracts.orchestration import validate_escalation_proposal

from tecrax.contracts import (
    MONITORING_HOST_DIAGNOSIS_CONTRACT_ID,
    validate_facts,
)

ESCALATION_PROPOSAL_SCHEMA_REF = "schemas/escalation_proposal.v0.1.schema.json"
READ_ONLY_MODES = frozenset({"read_only", "dry_run", "observe", "emergency_readonly"})
INTENT_OUTCOMES = frozenset({"run_intent", "retry_intent"})
UNSAFE_EXPLANATION_MARKERS = (
    "-----begin",
    "authorization:",
    "bearer ",
    "docker exec",
    "docker restart",
    "docker compose",
    "http://",
    "https://",
    "password",
    "passwd",
    "secret",
    "sudo ",
    "systemctl reload",
    "systemctl restart",
    "token",
)


class EscalationProposalValidationError(ValueError):
    """Raised when a Tecrax advisory escalation proposal is not bounded."""


def build_monitoring_host_escalation_proposal(
    *,
    operation_id: str,
    reaction_id: str,
    diagnosis: Mapping[str, Any],
    suggested_outcome: str = "escalate",
    intent_ref: str | None = None,
    evidence_refs: Sequence[str] = ("01_observation.json",),
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build one bounded, untrusted SCLite escalation proposal from diagnosis facts.

    The proposal is advisory only. It carries no command, connector payload,
    credential, target address, policy decision, or execution authority.
    """
    facts = dict(diagnosis)
    errors = validate_facts(
        facts,
        expected_contract_id=MONITORING_HOST_DIAGNOSIS_CONTRACT_ID,
    )
    if errors:
        raise EscalationProposalValidationError(
            "invalid_monitoring_host_diagnosis:" + ",".join(errors)
        )

    outcome = _bounded_text(suggested_outcome, limit=32)
    normalized_intent = _normalize_intent(outcome, intent_ref)
    if normalized_intent is not None:
        _validate_readonly_intent(normalized_intent)
    refs = tuple(_validate_evidence_ref(ref) for ref in evidence_refs)
    if not refs:
        raise EscalationProposalValidationError("evidence_refs must not be empty")

    proposal = {
        "artifact_type": "escalation_proposal",
        "schema_version": "v0.1",
        "schema_ref": ESCALATION_PROPOSAL_SCHEMA_REF,
        "proposal_id": _proposal_id(
            operation_id=operation_id,
            reaction_id=reaction_id,
            outcome=outcome,
            intent_ref=normalized_intent,
            diagnosis=facts,
        ),
        "reaction_id": _bounded_text(reaction_id, limit=128),
        "created_at": created_at or datetime.now(UTC).isoformat(),
        "suggested_outcome": outcome,
        "intent_ref": normalized_intent,
        "explanation": _monitoring_host_explanation(facts),
        "evidence_refs": list(refs),
        "authority": {
            "trusted": False,
            "may_execute": False,
            "requires_profile_validation": True,
            "requires_govengine_admission": True,
        },
    }
    validate_monitoring_host_escalation_proposal(proposal)
    return proposal


def validate_monitoring_host_escalation_proposal(proposal: Mapping[str, Any]) -> None:
    """Validate SCLite shape plus Tecrax profile constraints for an advisory proposal."""
    value = dict(proposal)
    try:
        validate_escalation_proposal(value)
    except Exception as exc:  # noqa: BLE001 - normalize foreign validation exceptions.
        raise EscalationProposalValidationError("invalid_escalation_proposal") from exc

    outcome = str(value.get("suggested_outcome") or "")
    intent_ref = str(value.get("intent_ref") or "").strip() or None
    _normalize_intent(outcome, intent_ref)
    if outcome in INTENT_OUTCOMES and intent_ref is not None:
        _validate_readonly_intent(intent_ref)
    for ref in value.get("evidence_refs") or []:
        _validate_evidence_ref(str(ref))
    _validate_explanation(str(value.get("explanation") or ""))


def _normalize_intent(outcome: str, intent_ref: str | None) -> str | None:
    normalized = _bounded_text(intent_ref, limit=128) if intent_ref else None
    if outcome in INTENT_OUTCOMES:
        if normalized is None:
            raise EscalationProposalValidationError("intent_ref is required")
        return normalized
    if normalized is not None:
        raise EscalationProposalValidationError("intent_ref is only valid for intent outcomes")
    return None


def _validate_readonly_intent(intent_ref: str) -> None:
    try:
        metadata = load_profile(Path(__file__).resolve().parent / "profile").intent_metadata(
            intent_ref
        )
    except RExecOpValidationError as exc:
        raise EscalationProposalValidationError(f"unknown_intent:{intent_ref}") from exc
    modes = {str(mode) for mode in metadata.get("modes") or []}
    if not modes or not modes <= READ_ONLY_MODES:
        raise EscalationProposalValidationError(f"non_readonly_intent:{intent_ref}")


def _validate_evidence_ref(ref: str) -> str:
    value = _bounded_text(ref, limit=256)
    path = PurePosixPath(value)
    if (
        not value
        or value.startswith("~")
        or "://" in value
        or "\\" in value
        or path.is_absolute()
        or ".." in path.parts
    ):
        raise EscalationProposalValidationError("unsafe_evidence_ref")
    return value


def _validate_explanation(explanation: str) -> None:
    if len(explanation) > 768:
        raise EscalationProposalValidationError("explanation_exceeds_profile_bound")
    lowered = explanation.lower()
    if any(marker in lowered for marker in UNSAFE_EXPLANATION_MARKERS):
        raise EscalationProposalValidationError("unsafe_explanation")


def _monitoring_host_explanation(facts: Mapping[str, Any]) -> str:
    observed = _bounded_text(facts.get("observed_health"), limit=32)
    coverage = _bounded_text(facts.get("coverage_status"), limit=32)
    findings = _summarize_findings(facts.get("findings"))
    failures = _summarize_failures(facts.get("continued_failures"))
    explanation = (
        "Bounded Tecrax monitoring-host escalation proposal. "
        f"observed_health={observed}; coverage_status={coverage}; "
        f"findings={findings}; continued_failures={failures}; "
        "advisory_only=true; no_connector_or_command_authority=true."
    )
    _validate_explanation(explanation)
    return explanation


def _summarize_findings(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "none"
    parts: list[str] = []
    for item in value[:8]:
        if not isinstance(item, Mapping):
            continue
        kind = _bounded_token(item.get("kind"), limit=96)
        reason = _bounded_token(item.get("reason_code"), limit=96)
        severity = _bounded_token(item.get("severity"), limit=32)
        component = _bounded_token(item.get("component"), limit=96)
        parts.append(f"{component}/{kind}/{reason}/{severity}")
    return ",".join(parts) or "none"


def _summarize_failures(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "none"
    parts: list[str] = []
    for item in value[:8]:
        if not isinstance(item, Mapping):
            continue
        step = _bounded_token(item.get("step_id"), limit=128)
        error = _bounded_token(item.get("error_class"), limit=128)
        parts.append(f"{step}/{error}")
    return ",".join(parts) or "none"


def _proposal_id(
    *,
    operation_id: str,
    reaction_id: str,
    outcome: str,
    intent_ref: str | None,
    diagnosis: Mapping[str, Any],
) -> str:
    canonical = json.dumps(
        {
            "operation_id": _bounded_text(operation_id, limit=128),
            "reaction_id": _bounded_text(reaction_id, limit=128),
            "outcome": outcome,
            "intent_ref": intent_ref,
            "diagnosis": diagnosis,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "tecrax-proposal-" + hashlib.sha256(canonical).hexdigest()[:24]


def _bounded_text(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _bounded_token(value: Any, *, limit: int) -> str:
    text = _bounded_text(value, limit=limit)
    allowed = [char if char.isalnum() or char in "._:-" else "_" for char in text]
    return "".join(allowed)[:limit] or "unknown"
