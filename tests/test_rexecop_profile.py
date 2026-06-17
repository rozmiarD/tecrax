from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import tecrax
from tecrax import profile_root


def test_profile_root_points_to_bundled_directory() -> None:
    root = Path(profile_root())
    assert root.is_dir()
    assert (root / "profile.yaml").is_file()
    assert (root / "intents").is_dir()
    assert (root / "workflows").is_dir()


def test_profile_yaml_loads_with_expected_contract() -> None:
    profile_path = Path(profile_root()) / "profile.yaml"
    text = profile_path.read_text(encoding="utf-8")
    assert "name: tecrax" in text
    assert 'version: "0.3.0"' in text


def test_rexecop_profiles_entry_point_registered() -> None:
    eps = entry_points(group="rexecop.profiles")
    names = {ep.name for ep in eps}
    assert "tecrax" in names
    tecrax_ep = next(ep for ep in eps if ep.name == "tecrax")
    assert tecrax_ep.value == "tecrax:profile_root"
    assert Path(tecrax_ep.load()()).is_dir()


def test_package_version_matches_profile_bundle() -> None:
    assert tecrax.__version__ == "0.3.0a0"
