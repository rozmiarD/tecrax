from __future__ import annotations

from typing import Any

from rexecop.connectors.base import ConnectorRequest, ConnectorResponse
from rexecop.connectors.mock_runtime import MockConnectorRuntime
from rexecop.execution.backend import StepExecutionContext


class TecraxFixtureConnectorRuntime(MockConnectorRuntime):
    """Domain fixture mock for Tecrax offline/bootstrap workflows."""

    def invoke(self, request: ConnectorRequest) -> ConnectorResponse:
        base = super().invoke(request)
        if base.error and "unsupported mock" not in base.error:
            return base

        if request.connector == "proxmox" and request.action == "list_vms":
            return ConnectorResponse(
                connector=request.connector,
                action=request.action,
                success=True,
                data={
                    "vms": [
                        {"id": "vm-101", "name": "zabbix-proxy", "critical": True},
                        {"id": "vm-102", "name": "backup-gateway", "critical": True},
                    ]
                },
            )

        if request.connector == "proxmox" and request.action == "restart":
            before_state = {
                "vm_id": "vm-101",
                "agent_status": "running",
                "target": request.target,
            }
            after_state = {
                "vm_id": "vm-101",
                "agent_status": "restarted",
                "target": request.target,
            }
            return ConnectorResponse(
                connector=request.connector,
                action=request.action,
                success=True,
                data={
                    "before_state": before_state,
                    "after_state": after_state,
                    "mutation": "restart_zabbix_agent",
                },
            )

        if request.connector == "pbs" and request.action == "list_snapshots":
            return ConnectorResponse(
                connector=request.connector,
                action=request.action,
                success=True,
                data={
                    "snapshots": [
                        {"vm_id": "vm-101", "status": "ok"},
                        {"vm_id": "vm-102", "status": "ok"},
                    ]
                },
            )

        return base


def build_runtime() -> TecraxFixtureConnectorRuntime:
    return TecraxFixtureConnectorRuntime()
