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

from tecrax import profile_root as bundled_profile_root  # noqa: E402
from tecrax.contracts import FACTS_CONTRACTS  # noqa: E402


READ_ONLY_MODES = {"read_only", "dry_run"}
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
        if not modes or not modes <= READ_ONLY_MODES:
            errors.append(f"{intent_id}:non_readonly_modes:{sorted(modes)}")

        catalog = data.get("catalog")
        if not isinstance(catalog, dict):
            errors.append(f"{intent_id}:missing_catalog")
            continue
        if catalog.get("side_effect_class") != "none":
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
        if not runbook_ref or not (ROOT / "docs" / Path(runbook_ref).name).is_file():
            errors.append(f"{intent_id}:missing_runbook:{runbook_ref}")

        workflow = _load(workflow_path).get("workflow")
        if not isinstance(workflow, dict) or workflow.get("intent") != intent_id:
            errors.append(f"{intent_id}:workflow_intent_mismatch")
            continue
        if workflow.get("mode") != "read_only":
            errors.append(f"{intent_id}:workflow_not_read_only")
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
        for token in FORBIDDEN_ACTIVE_TOKENS:
            if token in active_text:
                errors.append(f"{intent_id}:forbidden_active_token:{token}")

    taxonomy_text = (profile / "taxonomy.yaml").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_ACTIVE_TOKENS:
        if token in taxonomy_text:
            errors.append(f"taxonomy:forbidden_future_token:{token}")

    return sorted(set(errors))


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
