from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from scripts.validate_active_profile import collect_errors
from tecrax import profile_root


def _copy_profile(tmp_path: Path) -> Path:
    target = tmp_path / "profile"
    shutil.copytree(profile_root(), target)
    return target


def test_active_profile_passes_fail_closed_gate() -> None:
    assert collect_errors() == []


def test_active_profile_rejects_apply_intent(tmp_path: Path) -> None:
    root = _copy_profile(tmp_path)
    path = root / "intents" / "collect_basic_host_inventory.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["intent"]["modes"].append("apply")
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("non_readonly_modes" in item for item in collect_errors(root))


def test_active_profile_rejects_missing_runbook(tmp_path: Path) -> None:
    root = _copy_profile(tmp_path)
    path = root / "intents" / "collect_basic_host_inventory.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["intent"]["catalog"]["runbook_ref"] = "docs/missing.md"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("missing_runbook" in item for item in collect_errors(root))


def test_active_profile_rejects_unknown_facts_contract(tmp_path: Path) -> None:
    root = _copy_profile(tmp_path)
    path = root / "intents" / "collect_basic_host_inventory.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["intent"]["facts_contract"] = "tecrax.unknown@1.0"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("unknown_facts_contract" in item for item in collect_errors(root))


def test_active_profile_rejects_wrong_facts_contract_version(tmp_path: Path) -> None:
    root = _copy_profile(tmp_path)
    path = root / "intents" / "collect_basic_host_inventory.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["intent"]["facts_contract"] = "tecrax.basic_host_inventory@2.0"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("facts_contract_version_mismatch" in item for item in collect_errors(root))


def test_active_profile_rejects_undeclared_connector_action(tmp_path: Path) -> None:
    root = _copy_profile(tmp_path)
    path = root / "workflows" / "collect_basic_host_inventory.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["workflow"]["steps"][0]["action"] = "arbitrary_command"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("undeclared_connector_action" in item for item in collect_errors(root))


def test_active_profile_rejects_future_product_placeholder(tmp_path: Path) -> None:
    root = _copy_profile(tmp_path)
    path = root / "intents" / "collect_basic_host_inventory.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["intent"]["catalog"]["summary"] = "Future Proxmox placeholder"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("forbidden_active_token:proxmox" in item for item in collect_errors(root))


def test_active_profile_rejects_forbidden_network_connector_action(
    tmp_path: Path,
) -> None:
    root = _copy_profile(tmp_path)
    path = root / "connectors" / "network_device_cli.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["connector"]["capabilities"].append("vlan-summary")
    data["connector"]["command_shapes"]["vlan-summary"] = {
        "command": "tecrax-network-cli-readonly",
        "args": ["vlan-summary"],
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("forbidden_connector_action_token:vlan-summary" in item for item in collect_errors(root))
