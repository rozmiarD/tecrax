#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
GITHUB_DOCS_PREFIX = "https://github.com/rozmiarD/tecrax/blob/main/"

from tecrax import profile_root as bundled_profile_root  # noqa: E402
from tecrax.contracts import FACTS_CONTRACTS  # noqa: E402


READ_ONLY_MODES = {"read_only", "dry_run"}
APPROVED_MUTATING_INTENTS = {"configure_chrony_ntp_server"}
APPROVED_MUTATING_SIDE_EFFECTS = {"bounded_config_file_and_service_restart"}
TRIGGER_DECISIONS = {"plan_operation", "ignore", "escalate"}
TRIGGER_OPERATORS = {"exists", "equals", "not_equals", "in"}
TRIGGER_RULE_KEYS = {
    "id",
    "priority",
    "event_type",
    "when",
    "decision",
    "operation",
    "cooldown_seconds",
}
TRIGGER_OPERATION_KEYS = {
    "intent",
    "target",
    "target_from",
    "catalog_target",
    "catalog_target_from",
    "mode",
    "auto_react",
}
REACTION_OBSERVATION_KEYS = {
    "shared_state_key",
    "schema_ref",
    "source_intent",
    "producer_step",
    "requires_completed_operation",
}
FORBIDDEN_ACTIVE_TOKENS = {
    "apply",
    "backup",
    "fixture",
    "frigate",
    "grafana",
    "hillstone",
    "mock",
    "pbs",
    "printer",
    "proxmox",
    "restart",
    "samba",
    "wazuh",
}
FORBIDDEN_CONNECTOR_ACTION_TOKENS = {
    "current-configuration",
    "port-security-summary",
    "running-config",
    "show-running",
    "startup-config",
    "vlan-summary",
}


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _runbook_path(runbook_ref: str) -> Path:
    if runbook_ref.startswith(GITHUB_DOCS_PREFIX):
        runbook_ref = runbook_ref.removeprefix(GITHUB_DOCS_PREFIX)
    return ROOT / runbook_ref


def collect_errors(profile_root: Path | None = None) -> list[str]:
    profile = (profile_root or Path(bundled_profile_root())).resolve()
    errors: list[str] = []
    taxonomy = _load(profile / "taxonomy.yaml").get("taxonomy") or {}
    allowed_domain_capabilities = {
        str(item) for item in taxonomy.get("domain_capabilities") or []
    }
    intents = sorted((profile / "intents").glob("*.yaml"))
    if not intents:
        return ["active_profile:no_intents"]
    intent_ids = {path.stem for path in intents}

    for intent_path in intents:
        data = _load(intent_path).get("intent")
        if not isinstance(data, dict):
            errors.append(f"{intent_path.name}:missing_intent_mapping")
            continue
        intent_id = str(data.get("id") or "")
        if intent_id != intent_path.stem:
            errors.append(f"{intent_path.name}:id_mismatch:{intent_id}")
        if data.get("enforce_declared_modes") is not True:
            errors.append(f"{intent_id}:declared_modes_not_enforced")
        modes = {str(item) for item in data.get("modes") or []}
        mutating_approved = intent_id in APPROVED_MUTATING_INTENTS
        allowed_modes = {"apply"} if mutating_approved else READ_ONLY_MODES
        if not modes or not modes <= allowed_modes:
            errors.append(f"{intent_id}:non_readonly_modes:{sorted(modes)}")

        catalog = data.get("catalog")
        if not isinstance(catalog, dict):
            errors.append(f"{intent_id}:missing_catalog")
            continue
        side_effect_class = str(catalog.get("side_effect_class") or "")
        if mutating_approved:
            if side_effect_class not in APPROVED_MUTATING_SIDE_EFFECTS:
                errors.append(f"{intent_id}:unexpected_mutating_side_effect")
        elif side_effect_class != "none":
            errors.append(f"{intent_id}:side_effect_not_none")
        for key in (
            "title",
            "summary",
            "target_kinds",
            "required_capabilities",
        ):
            if not catalog.get(key):
                errors.append(f"{intent_id}:missing_catalog_field:{key}")
        facts_contract = str(data.get("facts_contract") or "")
        if not facts_contract:
            errors.append(f"{intent_id}:missing_facts_contract")
        else:
            contract_id, separator, version = facts_contract.partition("@")
            spec = FACTS_CONTRACTS.get(contract_id)
            if not separator or not contract_id or not version:
                errors.append(f"{intent_id}:invalid_facts_contract_ref:{facts_contract}")
            elif spec is None:
                errors.append(f"{intent_id}:unknown_facts_contract:{contract_id}")
            elif spec.version != version:
                errors.append(
                    f"{intent_id}:facts_contract_version_mismatch:{facts_contract}"
                )
        domain_capabilities = {
            str(item)
            for item in catalog.get("required_capabilities") or []
            if str(item).startswith("tecrax.")
        }
        if len(domain_capabilities) != 1:
            errors.append(f"{intent_id}:expected_one_domain_capability")
        if not domain_capabilities <= allowed_domain_capabilities:
            errors.append(f"{intent_id}:unknown_domain_capability")

        workflow_ref = str(data.get("workflow") or "")
        validation_ref = str(catalog.get("validation_ref") or "")
        runbook_ref = str(catalog.get("runbook_ref") or "")
        workflow_path = profile / workflow_ref
        validation_path = profile / validation_ref
        if not workflow_path.is_file():
            errors.append(f"{intent_id}:missing_workflow:{workflow_ref}")
            continue
        if not validation_path.is_file():
            errors.append(f"{intent_id}:missing_validation:{validation_ref}")
        if not runbook_ref or not _runbook_path(runbook_ref).is_file():
            errors.append(f"{intent_id}:missing_runbook:{runbook_ref}")

        workflow = _load(workflow_path).get("workflow")
        if not isinstance(workflow, dict) or workflow.get("intent") != intent_id:
            errors.append(f"{intent_id}:workflow_intent_mismatch")
            continue
        expected_workflow_mode = "apply" if mutating_approved else "read_only"
        if workflow.get("mode") != expected_workflow_mode:
            errors.append(f"{intent_id}:workflow_mode_mismatch")
        reaction_observation = data.get("reaction_observation")
        if reaction_observation is not None:
            if not isinstance(reaction_observation, dict):
                errors.append(f"{intent_id}:reaction_observation_not_mapping")
            else:
                unknown = sorted(
                    str(key)
                    for key in reaction_observation
                    if key not in REACTION_OBSERVATION_KEYS
                )
                if unknown:
                    errors.append(
                        f"{intent_id}:reaction_observation_unknown_keys:{unknown}"
                    )
                if reaction_observation.get("shared_state_key") != "reaction_observation":
                    errors.append(f"{intent_id}:reaction_observation_shared_state_key")
                if (
                    reaction_observation.get("schema_ref")
                    != "schemas/observation_envelope.v0.1.schema.json"
                ):
                    errors.append(f"{intent_id}:reaction_observation_schema_ref")
                if reaction_observation.get("source_intent") != intent_id:
                    errors.append(f"{intent_id}:reaction_observation_source_intent")
                if reaction_observation.get("requires_completed_operation") is not True:
                    errors.append(
                        f"{intent_id}:reaction_observation_requires_completed_operation"
                    )
                producer_step = str(
                    reaction_observation.get("producer_step") or ""
                ).strip()
                workflow_steps = {
                    str(step.get("id") or ""): step
                    for step in workflow.get("steps") or []
                    if isinstance(step, dict)
                }
                producer = workflow_steps.get(producer_step)
                if producer is None:
                    errors.append(f"{intent_id}:reaction_observation_producer_missing")
                elif producer.get("type") != "internal":
                    errors.append(
                        f"{intent_id}:reaction_observation_producer_not_internal"
                    )
        for step in workflow.get("steps") or []:
            if not isinstance(step, dict) or step.get("type") != "connector":
                continue
            connector = str(step.get("connector") or "")
            action = str(step.get("action") or "")
            connector_path = profile / "connectors" / f"{connector}.yaml"
            if not connector_path.is_file():
                errors.append(f"{intent_id}:missing_connector:{connector}")
                continue
            connector_data = _load(connector_path).get("connector") or {}
            capabilities = {str(item) for item in connector_data.get("capabilities") or []}
            if action not in capabilities:
                errors.append(f"{intent_id}:undeclared_connector_action:{connector}:{action}")
            connector_text = connector_path.read_text(encoding="utf-8").lower()
            for token in FORBIDDEN_CONNECTOR_ACTION_TOKENS:
                if token in connector_text:
                    errors.append(f"{connector}:forbidden_connector_action_token:{token}")

        active_text = (intent_path.read_text(encoding="utf-8") + workflow_path.read_text(encoding="utf-8")).lower()
        forbidden_tokens = set(FORBIDDEN_ACTIVE_TOKENS)
        if mutating_approved:
            forbidden_tokens.discard("apply")
            forbidden_tokens.discard("restart")
        for token in forbidden_tokens:
            if token in active_text:
                errors.append(f"{intent_id}:forbidden_active_token:{token}")

    taxonomy_text = (profile / "taxonomy.yaml").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_ACTIVE_TOKENS:
        if token in taxonomy_text:
            errors.append(f"taxonomy:forbidden_future_token:{token}")
    errors.extend(_collect_trigger_errors(profile, intent_ids))
    errors.extend(_collect_operator_metadata_errors(profile, intent_ids))

    return sorted(set(errors))


def _collect_operator_metadata_errors(profile: Path, intent_ids: set[str]) -> list[str]:
    path = profile / "operator_metadata.yaml"
    if not path.is_file():
        return ["operator_metadata:missing"]
    data = _load(path).get("operator_metadata")
    if not isinstance(data, dict):
        return ["operator_metadata:missing_mapping"]
    schema_version = str(data.get("schema_version") or "")
    if schema_version != "v0.1":
        return [f"operator_metadata:unsupported_schema_version:{schema_version or 'missing'}"]
    profile_meta = data.get("profile")
    if not isinstance(profile_meta, dict) or not str(profile_meta.get("label") or "").strip():
        return ["operator_metadata.profile.label:required"]
    intents = data.get("intents")
    if not isinstance(intents, dict) or not intents:
        return ["operator_metadata.intents:required"]
    errors: list[str] = []
    unknown = sorted(set(intents) - intent_ids)
    missing = sorted(intent_ids - set(intents))
    if unknown:
        errors.append(f"operator_metadata.intents.unknown:{','.join(unknown)}")
    if missing:
        errors.append(f"operator_metadata.intents.missing:{','.join(missing)}")
    for intent_id, entry in sorted(intents.items()):
        if not isinstance(entry, dict):
            errors.append(f"{intent_id}:operator_metadata:not_mapping")
            continue
        if not str(entry.get("label") or "").strip():
            errors.append(f"{intent_id}:operator_metadata.label:required")
        if not str(entry.get("runbook_hint") or "").strip():
            errors.append(f"{intent_id}:operator_metadata.runbook_hint:required")
        if not isinstance(entry.get("safe_next_options"), list) or not entry.get("safe_next_options"):
            errors.append(f"{intent_id}:operator_metadata.safe_next_options:required")
        failure_mapping = entry.get("failure_mapping")
        if not isinstance(failure_mapping, dict) or not failure_mapping:
            errors.append(f"{intent_id}:operator_metadata.failure_mapping:required")
    return errors


def _collect_trigger_errors(profile: Path, intent_ids: set[str]) -> list[str]:
    path = profile / "triggers" / "trigger_rules.yaml"
    if not path.exists():
        return []
    errors: list[str] = []
    document = _load(path)
    trigger_rules = document.get("trigger_rules")
    if not isinstance(trigger_rules, dict):
        return ["trigger_rules:missing_mapping"]
    rule_set_id = str(trigger_rules.get("id") or "")
    version = str(trigger_rules.get("version") or "")
    rules = trigger_rules.get("rules")
    if not rule_set_id or not version:
        errors.append("trigger_rules:missing_id_or_version")
    if not isinstance(rules, list) or not rules:
        errors.append("trigger_rules:no_rules")
        return errors
    seen: set[str] = set()
    for item in rules:
        if not isinstance(item, dict):
            errors.append("trigger_rules:rule_not_mapping")
            continue
        rule_id = str(item.get("id") or "")
        if not rule_id or rule_id in seen:
            errors.append("trigger_rules:duplicate_or_missing_rule_id")
        seen.add(rule_id)
        unknown = sorted(str(key) for key in item if key not in TRIGGER_RULE_KEYS)
        if unknown:
            errors.append(f"{rule_id}:unknown_trigger_rule_keys:{unknown}")
        decision = str(item.get("decision") or "")
        if decision not in TRIGGER_DECISIONS:
            errors.append(f"{rule_id}:unsupported_trigger_decision:{decision}")
        if int(item.get("cooldown_seconds") or 0) < 0:
            errors.append(f"{rule_id}:negative_cooldown")
        conditions = item.get("when")
        if not isinstance(conditions, list) or not conditions:
            errors.append(f"{rule_id}:missing_trigger_conditions")
        else:
            for condition in conditions:
                if not isinstance(condition, dict):
                    errors.append(f"{rule_id}:condition_not_mapping")
                    continue
                operator = str(condition.get("operator") or "")
                path_ref = str(condition.get("path") or "")
                if not path_ref:
                    errors.append(f"{rule_id}:condition_missing_path")
                if operator not in TRIGGER_OPERATORS:
                    errors.append(f"{rule_id}:condition_unsupported_operator:{operator}")
        operation = item.get("operation") or {}
        if not isinstance(operation, dict):
            errors.append(f"{rule_id}:trigger_operation_not_mapping")
            continue
        unknown_operation_keys = sorted(
            str(key) for key in operation if key not in TRIGGER_OPERATION_KEYS
        )
        if unknown_operation_keys:
            errors.append(f"{rule_id}:unknown_trigger_operation_keys:{unknown_operation_keys}")
        if decision == "plan_operation":
            intent = str(operation.get("intent") or "")
            mode = str(operation.get("mode") or "")
            if intent not in intent_ids:
                errors.append(f"{rule_id}:unknown_trigger_intent:{intent}")
            if mode not in READ_ONLY_MODES:
                errors.append(f"{rule_id}:trigger_mode_not_readonly:{mode}")
            literal_target = str(operation.get("target") or operation.get("catalog_target") or "")
            dynamic_target = str(
                operation.get("target_from") or operation.get("catalog_target_from") or ""
            )
            if bool(literal_target) == bool(dynamic_target):
                errors.append(f"{rule_id}:trigger_requires_exactly_one_target_binding")
            if operation.get("catalog_target_from") != "subject":
                errors.append(f"{rule_id}:trigger_must_use_catalog_subject_binding")
        elif operation:
            errors.append(f"{rule_id}:non_plan_trigger_has_operation")
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("active_profile_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
