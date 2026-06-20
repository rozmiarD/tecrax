from __future__ import annotations

from typing import Any


def build_http_api_connector_config(
    *,
    staging_paths: bool = False,
    base_url_secret_ref: str = "proxmox_base_url",
    api_token_secret_ref: str = "proxmox_api_token",
    timeout_seconds: int = 10,
    max_retry_attempts: int = 2,
) -> dict[str, Any]:
    """Build environment YAML connector config for Proxmox over generic http_api."""
    if staging_paths:
        list_action: dict[str, Any] = {
            "method": "GET",
            "path": "/proxmox/vms/paged",
            "pagination": {
                "items_path": "data.vms",
                "next_path": "data.next",
                "max_pages": 5,
            },
        }
        restart_path = "/proxmox/restart"
    else:
        list_action = {
            "method": "GET",
            "path": "/api2/json/cluster/resources",
            "unwrap": "data",
        }
        restart_path = "/api2/json/nodes/{node}/qemu/{vmid}/status/restart"

    actions: dict[str, Any] = {
        "list_vms": list_action,
        "restart": {
            "method": "POST",
            "path": restart_path,
            "mutating": True,
            "body": {"target": "{target}"},
        },
    }

    return {
        "enabled": True,
        "backend": "http_api",
        "base_url_secret_ref": base_url_secret_ref,
        "auth": {
            "secret_ref": api_token_secret_ref,
            "header": "Authorization",
            "prefix": "PVEAPIToken=",
        },
        "timeout_seconds": timeout_seconds,
        "retry": {
            "max_attempts": max_retry_attempts,
            "base_delay": 0.2,
            "max_delay": 2.0,
            "on": ["timeout", "transient_connector_error"],
        },
        "actions": actions,
    }
