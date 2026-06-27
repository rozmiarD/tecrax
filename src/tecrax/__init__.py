"""Tecrax governed infrastructure-operations profile and local-fixture runtime."""

from __future__ import annotations

from pathlib import Path

from .escalation import (
    build_monitoring_host_escalation_proposal,
    validate_monitoring_host_escalation_proposal,
)
from .local_fixture import build_local_fixture_review
from .reactions import build_monitoring_host_observation

__version__ = "0.3.6a0"

__all__ = [
    "__version__",
    "build_monitoring_host_escalation_proposal",
    "build_local_fixture_review",
    "build_monitoring_host_observation",
    "profile_root",
    "validate_monitoring_host_escalation_proposal",
]


def profile_root() -> str:
    """Entry point for rexecop.profiles — returns bundled RExecOp profile directory."""
    return str(Path(__file__).resolve().parent / "profile")
