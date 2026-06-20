from __future__ import annotations

from tecrax.connectors.proxmox import build_http_api_connector_config


def test_build_proxmox_http_api_config_staging_paths() -> None:
    config = build_http_api_connector_config(staging_paths=True)
    assert config["backend"] == "http_api"
    assert config["actions"]["list_vms"]["pagination"]["items_path"] == "data.vms"
    assert config["retry"]["base_delay"] == 0.2


def test_build_proxmox_http_api_config_production_paths() -> None:
    config = build_http_api_connector_config(staging_paths=False)
    assert "/api2/json/cluster/resources" in config["actions"]["list_vms"]["path"]
    assert config["actions"]["list_vms"]["unwrap"] == "data"
