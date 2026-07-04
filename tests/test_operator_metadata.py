from __future__ import annotations

from pathlib import Path

from scripts.validate_active_profile import collect_errors
from tecrax import profile_root


def test_active_profile_operator_metadata_is_complete() -> None:
    errors = [
        error
        for error in collect_errors(Path(profile_root()))
        if error.startswith("operator_metadata") or ":operator_metadata" in error
    ]

    assert errors == []


def test_operator_metadata_file_exists() -> None:
    path = Path(profile_root()) / "operator_metadata.yaml"

    assert path.is_file()