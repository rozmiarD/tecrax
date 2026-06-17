from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rexecop.execution.backend import StepExecutionContext


def register_handlers() -> Mapping[str, Any]:
    return {
        "environment.resolve_targets": resolve_targets,
        "correlate_vm_backup_coverage": correlate_vm_backup_coverage,
        "capture_agent_state": capture_agent_state,
        "verify_agent_state": verify_agent_state,
    }


def resolve_targets(context: StepExecutionContext) -> dict[str, Any]:
    return {
        "target": context.target,
        "resolved_targets": ["vm-101", "vm-102"],
    }


def correlate_vm_backup_coverage(context: StepExecutionContext) -> dict[str, Any]:
    connector_results = context.shared_state.get("connector_results", {})
    vms: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    for payload in connector_results.values():
        if isinstance(payload, dict):
            vms.extend(payload.get("vms", []))
            snapshots.extend(payload.get("snapshots", []))
    covered = {item.get("vm_id") for item in snapshots}
    rows = []
    for vm in vms:
        vm_id = vm.get("id")
        rows.append(
            {
                "vm_id": vm_id,
                "name": vm.get("name"),
                "backup_status": "ok" if vm_id in covered else "missing",
            }
        )
    result = {
        "rows": rows,
        "all_critical_covered": all(row["backup_status"] == "ok" for row in rows),
    }
    context.shared_state["correlation"] = result
    return result


def capture_agent_state(context: StepExecutionContext) -> dict[str, Any]:
    state = {
        "target": context.target,
        "agent_status": "running",
        "vm_id": "vm-101",
    }
    context.shared_state["agent_before_state"] = dict(state)
    return {"before_state": state}


def verify_agent_state(context: StepExecutionContext) -> dict[str, Any]:
    mutation = context.shared_state.get("mutation_states", {}).get("restart_agent", {})
    after_state = mutation.get("after_state") if isinstance(mutation, dict) else None
    if not isinstance(after_state, dict):
        return {
            "verified": False,
            "reason": "missing restart mutation after_state",
        }
    context.shared_state["agent_after_state"] = dict(after_state)
    return {
        "verified": after_state.get("agent_status") == "restarted",
        "after_state": after_state,
        "before_state": context.shared_state.get("agent_before_state"),
    }
