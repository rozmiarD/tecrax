from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import tecrax
from rexecop.operation.controller import OperationController
from rexecop.storage.file_store import FileStore
from tecrax import profile_root

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_profile_root_points_to_bundled_directory() -> None:
    root = Path(profile_root())
    assert root.is_dir()
    assert (root / "profile.yaml").is_file()
    assert (root / "reactions" / "reaction_pack.yaml").is_file()
    assert (root / "intents").is_dir()
    assert (root / "workflows").is_dir()
    assert (root / "intents" / "collect_basic_host_inventory.yaml").is_file()
    assert (root / "connectors" / "monitoring_host.yaml").is_file()
    assert (root / "intents" / "check_ntp_health.yaml").is_file()
    assert (root / "intents" / "check_docker_services_health.yaml").is_file()
    assert (root / "intents" / "check_zabbix_container_health.yaml").is_file()
    assert (root / "intents" / "check_adguard_health.yaml").is_file()
    assert (root / "intents" / "check_portainer_health.yaml").is_file()
    assert (root / "intents" / "diagnose_monitoring_host.yaml").is_file()
    assert (root / "intents" / "collect_network_device_inventory_readonly.yaml").is_file()
    assert (root / "connectors" / "zabbix_api.yaml").is_file()
    assert (root / "connectors" / "adguard_health.yaml").is_file()
    assert (root / "connectors" / "portainer_api.yaml").is_file()
    assert (root / "connectors" / "network_device_cli.yaml").is_file()


def test_profile_yaml_loads_with_expected_contract() -> None:
    profile_path = Path(profile_root()) / "profile.yaml"
    text = profile_path.read_text(encoding="utf-8")
    assert "name: tecrax" in text
    assert 'version: "0.3.3"' in text


def test_rexecop_profiles_entry_point_registered() -> None:
    eps = entry_points(group="rexecop.profiles")
    names = {ep.name for ep in eps}
    assert "tecrax" in names
    tecrax_ep = next(ep for ep in eps if ep.name == "tecrax")
    assert tecrax_ep.value == "tecrax:profile_root"
    assert Path(tecrax_ep.load()()).is_dir()


def test_package_version_matches_profile_bundle() -> None:
    assert tecrax.__version__ == "0.3.4a0"


def test_unverified_r2_intents_are_not_claimed_by_profile() -> None:
    intents = Path(profile_root()) / "intents"
    assert not (intents / "check_frigate_host_health.yaml").exists()


def test_ubuntu_inventory_example_projects_b2_runtime_controls(tmp_path: Path) -> None:
    controller = OperationController(store=FileStore(tmp_path / ".rexecop"))

    operation = controller.plan(
        profile_path=Path(profile_root()),
        environment_path=(
            REPO_ROOT / "examples/environments/ubuntu-host.readonly.example.yaml"
        ),
        intent="collect_basic_host_inventory",
        target="monitoring-host-01",
        mode="dry_run",
    )

    enforcement = operation.metadata["policy_enforcement"]
    controls = enforcement["plan"]["controls"]
    assert enforcement["plan"]["status"] == "ready"
    assert enforcement["admission"]["outcome"] == "allowed"
    assert enforcement["admission_digest"].startswith("sha256:")
    assert controls == {
        "timeout_seconds": 10.0,
        "max_steps": 9,
        "max_output_bytes": 8192,
        "receipt_required": True,
        "output_digest_required": True,
        "control_ids": [
            "inventory-max-steps",
            "inventory-output-digests",
            "inventory-output-limit",
            "inventory-receipt",
            "inventory-timeout",
        ],
    }
