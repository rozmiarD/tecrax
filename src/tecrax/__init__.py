"""Tecrax governed infrastructure-operations profile and local-fixture runtime."""

from __future__ import annotations

from pathlib import Path

from .local_fixture import build_local_fixture_review

__version__ = "0.3.2a0"

__all__ = ["__version__", "build_local_fixture_review", "profile_root"]


def profile_root() -> str:
    """Entry point for rexecop.profiles — returns bundled RExecOp profile directory."""
    return str(Path(__file__).resolve().parent / "profile")
