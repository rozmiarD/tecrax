from __future__ import annotations

from importlib.metadata import entry_points

from tecrax.connectors.proxmox import build_http_api_connector_config, merge_http_api_connector_config
from tecrax.connectors.proxmox_runtime import build_connector_runtime


def test_tecrax_proxmox_connector_backend_entry_point() -> None:
    eps = entry_points(group="rexecop.connector_backends")
    names = {ep.name for ep in eps}
    assert "tecrax_proxmox" in names


def test_merge_http_api_connector_config_drops_secret_ref_when_base_url_set() -> None:
    template = build_http_api_connector_config(staging_paths=True)
    merged = merge_http_api_connector_config(
        template,
        {"base_url": "http://example.test"},
    )
    assert merged["base_url"] == "http://example.test"
    assert "base_url_secret_ref" not in merged


def test_build_connector_runtime_returns_invokeable_backend() -> None:
    runtime = build_connector_runtime(
        connector_name="proxmox",
        config={"staging_paths": True, "base_url": "http://127.0.0.1:9"},
        profile_root=None,
        mutating_allowed=False,
    )
    assert hasattr(runtime, "invoke")
