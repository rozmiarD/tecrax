from __future__ import annotations

from typing import Any

from rexecop.connectors.base import ConnectorRuntime
from rexecop.connectors.http_api import HttpApiConnectorRuntime
from rexecop.secrets.port import SecretResolver
from rexecop.secrets.resolver import default_secret_resolver

from tecrax.connectors.proxmox import build_http_api_connector_config, merge_http_api_connector_config


def build_connector_runtime(
    *,
    connector_name: str,
    config: dict[str, Any],
    profile_root: str | None,
    mutating_allowed: bool,
    secret_resolver: SecretResolver | None = None,
) -> ConnectorRuntime:
    """Domain connector backend: Proxmox over generic http_api with Tecrax templates."""
    template = build_http_api_connector_config(
        staging_paths=bool(config.get("staging_paths")),
        base_url_secret_ref=str(config.get("base_url_secret_ref") or "proxmox_base_url"),
        api_token_secret_ref=str(config.get("api_token_secret_ref") or "proxmox_api_token"),
        timeout_seconds=int(config.get("timeout_seconds") or 10),
        max_retry_attempts=int((config.get("retry") or {}).get("max_attempts") or 2)
        if isinstance(config.get("retry"), dict)
        else int(config.get("max_retry_attempts") or 2),
    )
    merged = merge_http_api_connector_config(template, config)
    return HttpApiConnectorRuntime(
        connector_name=connector_name,
        config=merged,
        profile_root=profile_root,
        mutating_allowed=mutating_allowed,
        secret_resolver=secret_resolver or default_secret_resolver(),
    )
