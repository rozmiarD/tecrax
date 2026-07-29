from __future__ import annotations

import ipaddress
import json
from collections.abc import Mapping
from dataclasses import dataclass
from threading import RLock
from typing import Any

from rexecop.connectors import errors as connector_errors
from rexecop.connectors.base import ConnectorRequest, ConnectorResponse
from rexecop.connectors.errors import READ_ONLY_MODES
from rexecop.evidence.redaction import redact_payload, redact_text
from rexecop.execution import bounded_subprocess as capture_runtime
from tecrax.contracts import (
    CHRONY_NTP_SERVER_MUTATION_CONTRACT_ID,
    CHRONY_NTP_SERVER_MUTATION_SCHEMA_REF,
    finalize_facts,
)

# Preserve the existing connector test seam while routing it to bounded capture.
subprocess = capture_runtime

MANAGED_FILE = "/etc/chrony/conf.d/tecrax-ntp-server.conf"
MAX_WRAPPER_OUTPUT_BYTES = 16_384
_FIXTURE_STATE_LOCK = RLock()
_FIXTURE_STATE: dict[tuple[str, str, str], bool] = {}


def _reset_fixture_state_registry() -> None:
    """Clear process-local fixture state for deterministic test isolation."""

    with _FIXTURE_STATE_LOCK:
        _FIXTURE_STATE.clear()


def build_chrony_ntp_backend(**kwargs: Any) -> "ChronyNtpBackend":
    return ChronyNtpBackend(
        connector_name=str(kwargs.get("connector_name") or "chrony_ntp_server"),
        config=dict(kwargs.get("config") or {}),
        mutating_allowed=bool(kwargs.get("mutating_allowed")),
    )


@dataclass(frozen=True)
class DesiredChronyState:
    allowed_subnet: str

    @property
    def managed_config(self) -> str:
        return (
            "# Managed by Tecrax: bounded chrony/NTP server contract.\n"
            "# Serve NTP only to the declared subnet.\n"
            f"allow {self.allowed_subnet}\n"
        )


class ChronyNtpBackend:
    """Tecrax-owned connector for the bounded chrony NTP server mutation."""

    def __init__(
        self,
        *,
        connector_name: str,
        config: dict[str, Any],
        mutating_allowed: bool,
    ) -> None:
        self.connector_name = connector_name
        self.config = config
        self.mutating_allowed = mutating_allowed

    def invoke(self, request: ConnectorRequest) -> ConnectorResponse:
        if request.connector != self.connector_name:
            return self._failure(request, "connector mismatch", connector_errors.UNSUPPORTED)
        try:
            desired = DesiredChronyState(
                allowed_subnet=_validated_subnet(self.config.get("allowed_subnet"))
            )
        except ValueError as exc:
            return self._failure(request, str(exc), connector_errors.VALIDATION_FAILED)

        if request.action == "read_chrony_ntp_server_state":
            return self._read_state(request, desired)
        if request.action == "apply_chrony_ntp_server":
            return self._apply(request, desired)
        if request.action == "rollback_chrony_ntp_server":
            return self._rollback(request, desired)
        return self._failure(
            request,
            f"unsupported chrony action: {request.action}",
            connector_errors.UNSUPPORTED,
        )

    def _read_state(
        self,
        request: ConnectorRequest,
        desired: DesiredChronyState,
    ) -> ConnectorResponse:
        if self._fixture_only:
            with _FIXTURE_STATE_LOCK:
                applied = self._fixture_applied(request, desired)
                data = self._fixture_state(desired, applied=applied)
            return self._success(request, data)
        return self._wrapper(request, desired, "read-state")

    def _apply(
        self,
        request: ConnectorRequest,
        desired: DesiredChronyState,
    ) -> ConnectorResponse:
        if request.mode in READ_ONLY_MODES:
            return self._failure(
                request,
                "chrony apply refused in read-only mode",
                connector_errors.POLICY_DENIED,
            )
        if not self.mutating_allowed:
            return self._failure(
                request,
                "chrony apply blocked until GovEngine allows",
                connector_errors.POLICY_DENIED,
            )
        if self._fixture_only:
            before, after = self._transition_fixture_state(
                request,
                desired,
                applied=True,
            )
            return self._success(
                request,
                {
                    "changed": before != after,
                    "before_state": before,
                    "after_state": after,
                },
            )
        return self._wrapper(request, desired, "apply")

    def _rollback(
        self,
        request: ConnectorRequest,
        desired: DesiredChronyState,
    ) -> ConnectorResponse:
        if request.mode in READ_ONLY_MODES:
            return self._failure(
                request,
                "chrony rollback refused in read-only mode",
                connector_errors.POLICY_DENIED,
            )
        if not self.mutating_allowed:
            return self._failure(
                request,
                "chrony rollback blocked until GovEngine allows",
                connector_errors.POLICY_DENIED,
            )
        if self._fixture_only:
            before, after = self._transition_fixture_state(
                request,
                desired,
                applied=False,
            )
            return self._success(
                request,
                {
                    "changed": before != after,
                    "before_state": before,
                    "after_state": after,
                },
            )
        return self._wrapper(request, desired, "rollback")

    @property
    def _fixture_only(self) -> bool:
        return self.config.get("fixture_only") is True

    @property
    def _fixture_default(self) -> bool:
        return bool(self.config.get("fixture_initially_applied"))

    def _fixture_key(
        self,
        request: ConnectorRequest,
        desired: DesiredChronyState,
    ) -> tuple[str, str, str]:
        return (self.connector_name, request.target, desired.allowed_subnet)

    def _fixture_applied(
        self,
        request: ConnectorRequest,
        desired: DesiredChronyState,
    ) -> bool:
        return _FIXTURE_STATE.get(
            self._fixture_key(request, desired),
            self._fixture_default,
        )

    def _transition_fixture_state(
        self,
        request: ConnectorRequest,
        desired: DesiredChronyState,
        *,
        applied: bool,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        key = self._fixture_key(request, desired)
        with _FIXTURE_STATE_LOCK:
            current = self._fixture_applied(request, desired)
            before = self._fixture_state(desired, applied=current)
            after = self._fixture_state(desired, applied=applied)
            if applied == self._fixture_default:
                _FIXTURE_STATE.pop(key, None)
            else:
                _FIXTURE_STATE[key] = applied
            return before, after

    def _wrapper(
        self,
        request: ConnectorRequest,
        desired: DesiredChronyState,
        action: str,
    ) -> ConnectorResponse:
        wrapper = str(self.config.get("wrapper_command") or "").strip()
        if not wrapper:
            return self._failure(
                request,
                "chrony live mode requires wrapper_command",
                connector_errors.VALIDATION_FAILED,
            )
        command = [
            wrapper,
            action,
            "--target",
            request.target,
            "--allowed-subnet",
            desired.allowed_subnet,
        ]
        timeout = float(self.config.get("timeout_seconds") or 30)
        controls = request.metadata.get("execution_controls")
        if "execution_controls" in request.metadata and not isinstance(
            controls, Mapping
        ):
            return self._failure(
                request,
                "invalid max_output_bytes",
                connector_errors.VALIDATION_FAILED,
            )
        try:
            configured_output_bytes = (
                self.config["max_output_bytes"]
                if "max_output_bytes" in self.config
                else MAX_WRAPPER_OUTPUT_BYTES
            )
            if isinstance(controls, Mapping) and "max_output_bytes" in controls:
                max_output_bytes = subprocess.resolve_output_limit(
                    configured=configured_output_bytes,
                    policy=controls["max_output_bytes"],
                )
            else:
                max_output_bytes = subprocess.resolve_output_limit(
                    configured=configured_output_bytes,
                )
        except ValueError:
            return self._failure(
                request,
                "invalid max_output_bytes",
                connector_errors.VALIDATION_FAILED,
            )
        try:
            completed = subprocess.run(
                command,
                timeout=timeout,
                max_output_bytes=max_output_bytes,
            )
        except subprocess.TimeoutExpired:
            return self._failure(request, "chrony wrapper timeout", connector_errors.TIMEOUT)
        result = subprocess.normalize_result(
            completed,
            max_output_bytes=max_output_bytes,
        )
        if result.output_limit_exceeded:
            return self._failure(
                request,
                "chrony wrapper output limit exceeded",
                capture_runtime.OUTPUT_LIMIT_EXCEEDED,
                data={
                    "output_limit_exceeded": True,
                    "max_output_bytes": max_output_bytes,
                    "output_digests": {
                        "stdout": result.stdout.digest,
                        "stderr": result.stderr.digest,
                    },
                    "output_truncated": {
                        "stdout": result.stdout.truncated,
                        "stderr": result.stderr.truncated,
                    },
                    "output_sizes": {
                        "stdout_bytes": result.stdout.total_bytes,
                        "stderr_bytes": result.stderr.total_bytes,
                        "total_bytes": (
                            result.stdout.total_bytes + result.stderr.total_bytes
                        ),
                    },
                },
            )
        if result.returncode != 0:
            return self._failure(
                request,
                redact_text(result.stderr.text) or "chrony wrapper failed",
                connector_errors.TRANSIENT,
                data={"returncode": result.returncode},
            )
        try:
            payload = json.loads(result.stdout.text)
        except json.JSONDecodeError:
            return self._failure(
                request,
                "chrony wrapper must emit JSON",
                connector_errors.VALIDATION_FAILED,
            )
        if not isinstance(payload, dict):
            return self._failure(
                request,
                "chrony wrapper payload must be a JSON object",
                connector_errors.VALIDATION_FAILED,
            )
        payload.setdefault("target", request.target)
        payload.setdefault("allowed_subnet", desired.allowed_subnet)
        payload.setdefault("managed_file", MANAGED_FILE)
        return self._success(request, payload)

    def _fixture_state(self, desired: DesiredChronyState, *, applied: bool) -> dict[str, Any]:
        requested = ["managed_config", "chrony_service", "udp_123_listener"]
        observed = ["chrony_service"]
        not_observed = ["managed_config", "udp_123_listener"]
        if applied:
            observed = requested
            not_observed = []
        return finalize_facts(
            {
                "schema_ref": CHRONY_NTP_SERVER_MUTATION_SCHEMA_REF,
                "target_role": "host_chrony_ntp_server",
                "allowed_subnet": desired.allowed_subnet,
                "managed_file": MANAGED_FILE,
                "managed_config": desired.managed_config,
                "chrony_active": True,
                "chrony_synchronized": True,
                "udp_123_listening": applied,
                "config_present": applied,
                "desired_state_applied": applied,
                "rollback_available": True,
            },
            contract_id=CHRONY_NTP_SERVER_MUTATION_CONTRACT_ID,
            requested=requested,
            observed=observed,
            not_observed=not_observed,
            assessment="healthy" if applied else "degraded",
            non_claims=[
                "firewall_policy",
                "client_configuration",
                "upstream_server_identity",
                "external_reachability",
            ],
        )

    def _success(self, request: ConnectorRequest, data: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            connector=request.connector,
            action=request.action,
            success=True,
            data=redact_payload(data),
        )

    @staticmethod
    def _failure(
        request: ConnectorRequest,
        error: str,
        error_class: str,
        data: dict[str, Any] | None = None,
    ) -> ConnectorResponse:
        payload = {"error_class": error_class}
        payload.update(data or {})
        return ConnectorResponse(
            connector=request.connector,
            action=request.action,
            success=False,
            error=redact_text(error),
            data=payload,
        )


def _validated_subnet(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("allowed_subnet is required")
    try:
        network = ipaddress.ip_network(text, strict=True)
    except ValueError as exc:
        raise ValueError("allowed_subnet must be a strict CIDR network") from exc
    if network.version != 4:
        raise ValueError("allowed_subnet must be IPv4")
    if network.prefixlen < 24:
        raise ValueError("allowed_subnet must not be broader than /24")
    if network.is_loopback or network.is_multicast or network.is_unspecified:
        raise ValueError("allowed_subnet must be an operator LAN subnet")
    return str(network)
