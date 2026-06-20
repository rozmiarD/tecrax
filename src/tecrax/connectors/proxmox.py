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


def merge_http_api_connector_config(
    template: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Merge operator overrides into a Proxmox http_api template."""
    merged: dict[str, Any] = dict(template)
    skip_keys = {"backend", "plugin", "staging_paths"}
    for key, value in overrides.items():
        if key in skip_keys:
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    merged["backend"] = "http_api"
    if "base_url" in overrides:
        merged.pop("base_url_secret_ref", None)
        if "auth" not in overrides:
            merged.pop("auth", None)
    auth = overrides.get("auth")
    if isinstance(auth, dict) and auth.get("secret_ref"):
        merged_auth = dict(merged.get("auth") or {})
        merged_auth.update(auth)
        merged["auth"] = merged_auth
    return merged
