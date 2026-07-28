from __future__ import annotations

import hashlib
import json
import stat
import subprocess as stdlib_subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from rexecop.adapters.govengine_port.contracts import GovEngineDecisionType
from rexecop.adapters.govengine_port.static_adapter import StaticGovEngineAdapter
from rexecop.connectors.base import ConnectorRequest
from rexecop.connectors.runtime import ConnectorDispatcher
from rexecop.errors import RExecOpMutationNotCertified, RExecOpValidationError
from rexecop.execution.backend import StepExecutionContext
from rexecop.execution.executor import StepExecutor
from rexecop.operation.controller import OperationController
from rexecop.operation.state import OperationState
from rexecop.storage.file_store import FileStore
from tecrax import profile_root
from tecrax.connectors import chrony
from tecrax.connectors.chrony import ChronyNtpBackend, build_chrony_ntp_backend

REPO_ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = REPO_ROOT / "examples/environments/chrony-ntp-server.apply.example.yaml"


class _ChronyEntryPoint:
    name = "tecrax_chrony_ntp"

    def load(self):
        return build_chrony_ntp_backend


def _entry_points(**_: object) -> list[_ChronyEntryPoint]:
    return [_ChronyEntryPoint()]


def _live_backend(**config: object) -> ChronyNtpBackend:
    return ChronyNtpBackend(
        connector_name="chrony_ntp_server",
        config={
            "allowed_subnet": "192.0.2.0/24",
            "wrapper_command": "/fixture/chrony-wrapper",
            **config,
        },
        mutating_allowed=False,
    )


def _read_request(
    *,
    metadata: dict[str, object] | None = None,
) -> ConnectorRequest:
    return ConnectorRequest(
        connector="chrony_ntp_server",
        action="read_chrony_ntp_server_state",
        target="chrony-host-01",
        mode="dry_run",
        metadata=metadata or {},
    )


def _completed(
    *,
    returncode: int = 0,
    stdout: str | bytes = "{}",
    stderr: str | bytes = "",
) -> stdlib_subprocess.CompletedProcess[str | bytes]:
    return stdlib_subprocess.CompletedProcess(
        args=["/fixture/chrony-wrapper"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _write_output_producer(path: Path) -> None:
    path.write_text(
        f"#!{sys.executable}\n"
        "import os\n"
        "os.write(1, b'o' * 80)\n"
        "os.write(2, b'e' * 80)\n",
        encoding="utf-8",
    )
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def test_chrony_backend_refuses_apply_without_admission() -> None:
    backend = build_chrony_ntp_backend(
        connector_name="chrony_ntp_server",
        config={"fixture_only": True, "allowed_subnet": "192.0.2.0/24"},
        mutating_allowed=False,
    )

    response = backend.invoke(
        ConnectorRequest(
            connector="chrony_ntp_server",
            action="apply_chrony_ntp_server",
            target="chrony-host-01",
            mode="apply",
        )
    )

    assert not response.success
    assert response.data["error_class"] == "policy_denied"


def test_chrony_backend_validates_allowed_subnet() -> None:
    backend = build_chrony_ntp_backend(
        connector_name="chrony_ntp_server",
        config={"fixture_only": True, "allowed_subnet": "192.0.2.0/16"},
        mutating_allowed=True,
    )

    response = backend.invoke(
        ConnectorRequest(
            connector="chrony_ntp_server",
            action="read_chrony_ntp_server_state",
            target="chrony-host-01",
            mode="apply",
        )
    )

    assert not response.success
    assert response.data["error_class"] == "validation_failed"


def test_chrony_backend_records_before_after_when_runtime_authorizes_io() -> None:
    backend = build_chrony_ntp_backend(
        connector_name="chrony_ntp_server",
        config={"fixture_only": True, "allowed_subnet": "192.0.2.0/24"},
        mutating_allowed=True,
    )

    response = backend.invoke(
        ConnectorRequest(
            connector="chrony_ntp_server",
            action="apply_chrony_ntp_server",
            target="chrony-host-01",
            mode="apply",
        )
    )

    assert response.success
    assert response.data["before_state"]["desired_state_applied"] is False
    assert response.data["after_state"]["desired_state_applied"] is True


def test_chrony_real_producer_uses_runtime_combined_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrapper = tmp_path / "chrony-output-producer"
    _write_output_producer(wrapper)
    backend = _live_backend(wrapper_command=str(wrapper), max_output_bytes=96)
    real_run = chrony.capture_runtime.run
    observed: dict[str, object] = {}

    def spy_run(
        command: list[str],
        *,
        timeout: float,
        max_output_bytes: int,
    ) -> object:
        result = real_run(
            command,
            timeout=timeout,
            max_output_bytes=max_output_bytes,
        )
        observed.update(
            command=command,
            timeout=timeout,
            max_output_bytes=max_output_bytes,
            result=result,
        )
        return result

    monkeypatch.setattr(chrony.subprocess, "run", spy_run)
    response = backend.invoke(_read_request())

    assert response.success is False
    assert response.error == "chrony wrapper output limit exceeded"
    assert set(response.data) == {
        "error_class",
        "output_limit_exceeded",
        "max_output_bytes",
        "output_digests",
        "output_truncated",
        "output_sizes",
    }
    assert response.data["error_class"] == "output_limit_exceeded"
    assert response.data["output_limit_exceeded"] is True
    assert response.data["max_output_bytes"] == 96
    assert response.data["output_digests"] == {
        "stdout": "sha256:" + hashlib.sha256(b"o" * 80).hexdigest(),
        "stderr": "sha256:" + hashlib.sha256(b"e" * 80).hexdigest(),
    }
    assert response.data["output_sizes"] == {
        "stdout_bytes": 80,
        "stderr_bytes": 80,
        "total_bytes": 160,
    }
    truncation = response.data["output_truncated"]
    assert type(truncation["stdout"]) is bool
    assert type(truncation["stderr"]) is bool
    assert truncation["stdout"] or truncation["stderr"]
    assert observed["command"] == [
        str(wrapper),
        "read-state",
        "--target",
        "chrony-host-01",
        "--allowed-subnet",
        "192.0.2.0/24",
    ]
    assert observed["timeout"] == 30.0
    assert observed["max_output_bytes"] == 96
    raw_result = observed["result"]
    assert isinstance(raw_result, chrony.capture_runtime.BoundedSubprocessResult)
    retained = raw_result.stdout.retained_bytes + raw_result.stderr.retained_bytes
    assert retained <= 96
    assert raw_result.peak_retained_bytes <= 96
    assert raw_result.stdout.total_bytes + raw_result.stderr.total_bytes > 96
    assert {
        "stdout",
        "stderr",
        "argv",
        "raw_json",
        "peak_retained_bytes",
        "returncode",
    }.isdisjoint(response.data)


def test_chrony_normalizes_completed_process_like_success() -> None:
    backend = _live_backend()
    completed = _completed(
        stdout=json.dumps({"changed": False}),
        stderr="successful diagnostic must not be projected",
    )
    real_normalize = chrony.capture_runtime.normalize_result

    with (
        patch.object(chrony.subprocess, "run", return_value=completed) as run,
        patch.object(
            chrony.subprocess,
            "normalize_result",
            wraps=real_normalize,
        ) as normalize_result,
    ):
        response = backend.invoke(_read_request())

    assert response.success is True
    assert response.data == {
        "changed": False,
        "target": "chrony-host-01",
        "allowed_subnet": "192.0.2.0/24",
        "managed_file": "/etc/chrony/conf.d/tecrax-ntp-server.conf",
    }
    run.assert_called_once_with(
        [
            "/fixture/chrony-wrapper",
            "read-state",
            "--target",
            "chrony-host-01",
            "--allowed-subnet",
            "192.0.2.0/24",
        ],
        timeout=30.0,
        max_output_bytes=16_384,
    )
    normalize_result.assert_called_once_with(
        completed,
        max_output_bytes=16_384,
    )


@pytest.mark.parametrize(
    ("config", "metadata", "expected"),
    [
        ({}, {}, 16_384),
        ({"max_output_bytes": 1024}, {}, 1024),
        (
            {"max_output_bytes": 4096},
            {"execution_controls": {"max_output_bytes": 512}},
            512,
        ),
        (
            {"max_output_bytes": 512},
            {"execution_controls": {"max_output_bytes": 4096}},
            512,
        ),
    ],
)
def test_chrony_output_limit_default_config_and_policy_precedence(
    config: dict[str, object],
    metadata: dict[str, object],
    expected: int,
) -> None:
    backend = _live_backend(**config)

    with patch.object(
        chrony.subprocess,
        "run",
        return_value=_completed(),
    ) as run:
        response = backend.invoke(_read_request(metadata=metadata))

    assert response.success is True
    assert run.call_args.kwargs == {
        "timeout": 30.0,
        "max_output_bytes": expected,
    }


@pytest.mark.parametrize("invalid", [True, 1.5, "128", None, 0, -1])
def test_chrony_rejects_invalid_configured_output_limit_before_run(
    invalid: object,
) -> None:
    backend = _live_backend(max_output_bytes=invalid)

    with patch.object(chrony.subprocess, "run") as run:
        response = backend.invoke(_read_request())

    run.assert_not_called()
    assert response.success is False
    assert response.error == "invalid max_output_bytes"
    assert response.data == {"error_class": "validation_failed"}


@pytest.mark.parametrize("invalid", [True, 1.5, "128", None, 0, -1])
def test_chrony_rejects_invalid_policy_output_limit_before_run(
    invalid: object,
) -> None:
    backend = _live_backend()
    metadata = {"execution_controls": {"max_output_bytes": invalid}}

    with patch.object(chrony.subprocess, "run") as run:
        response = backend.invoke(_read_request(metadata=metadata))

    run.assert_not_called()
    assert response.success is False
    assert response.error == "invalid max_output_bytes"
    assert response.data == {"error_class": "validation_failed"}


@pytest.mark.parametrize("controls", [None, True, 1, 1.5, "limit", []])
def test_chrony_rejects_nonmapping_execution_controls_before_run(
    controls: object,
) -> None:
    backend = _live_backend()

    with patch.object(chrony.subprocess, "run") as run:
        response = backend.invoke(
            _read_request(metadata={"execution_controls": controls})
        )

    run.assert_not_called()
    assert response.success is False
    assert response.error == "invalid max_output_bytes"
    assert response.data == {"error_class": "validation_failed"}


def test_chrony_timeout_has_no_partial_output() -> None:
    backend = _live_backend()

    with patch.object(
        chrony.subprocess,
        "run",
        side_effect=chrony.subprocess.TimeoutExpired(("wrapper",), 30),
    ):
        response = backend.invoke(_read_request())

    assert response.success is False
    assert response.error == "chrony wrapper timeout"
    assert response.data == {"error_class": "timeout"}


def test_chrony_nonzero_is_transient_before_json_parsing() -> None:
    backend = _live_backend()

    with patch.object(
        chrony.subprocess,
        "run",
        return_value=_completed(
            returncode=7,
            stdout="not JSON",
            stderr="wrapper temporarily unavailable",
        ),
    ):
        response = backend.invoke(_read_request())

    assert response.success is False
    assert response.error == "wrapper temporarily unavailable"
    assert response.data == {
        "error_class": "transient_connector_error",
        "returncode": 7,
    }


def test_chrony_valid_json_applies_domain_defaults() -> None:
    backend = _live_backend()

    with patch.object(
        chrony.subprocess,
        "run",
        return_value=_completed(stdout='{"changed":true}', stderr="ignored"),
    ):
        response = backend.invoke(_read_request())

    assert response.success is True
    assert response.data == {
        "changed": True,
        "target": "chrony-host-01",
        "allowed_subnet": "192.0.2.0/24",
        "managed_file": "/etc/chrony/conf.d/tecrax-ntp-server.conf",
    }


@pytest.mark.parametrize("stdout", ["", "{not-json", "[]", '"value"', "null"])
def test_chrony_rejects_malformed_or_nonobject_json(stdout: str) -> None:
    backend = _live_backend()

    with patch.object(
        chrony.subprocess,
        "run",
        return_value=_completed(stdout=stdout),
    ):
        response = backend.invoke(_read_request())

    assert response.success is False
    assert response.data == {"error_class": "validation_failed"}
    if stdout in {"", "{not-json"}:
        assert response.error == "chrony wrapper must emit JSON"
    else:
        assert response.error == "chrony wrapper payload must be a JSON object"


def test_chrony_overflow_precedes_returncode_and_json() -> None:
    backend = _live_backend(max_output_bytes=8)

    with patch.object(
        chrony.subprocess,
        "run",
        return_value=_completed(
            returncode=9,
            stdout="not-json-overflow",
            stderr="failure-overflow",
        ),
    ):
        response = backend.invoke(_read_request())

    assert response.success is False
    assert response.error == "chrony wrapper output limit exceeded"
    assert set(response.data) == {
        "error_class",
        "output_limit_exceeded",
        "max_output_bytes",
        "output_digests",
        "output_truncated",
        "output_sizes",
    }
    assert response.data["error_class"] == "output_limit_exceeded"
    assert "returncode" not in response.data
    assert "stdout" not in response.data
    assert "stderr" not in response.data


def test_chrony_overflow_projects_through_step_executor(
    tmp_path: Path,
) -> None:
    wrapper = tmp_path / "chrony-step-output-producer"
    _write_output_producer(wrapper)
    backend = _live_backend(wrapper_command=str(wrapper), max_output_bytes=96)
    executor = StepExecutor(
        connector_dispatcher=ConnectorDispatcher(backend),
    )
    context = StepExecutionContext(
        operation_id="op-chrony-output-bound",
        target="chrony-host-01",
        mode="dry_run",
        step={
            "id": "read_chrony",
            "type": "connector",
            "connector": "chrony_ntp_server",
            "action": "read_chrony_ntp_server_state",
        },
        shared_state={"execution_controls": {"max_output_bytes": 96}},
    )

    result = executor.execute(context)

    assert result.success is False
    assert result.error == "connector output limit exceeded"
    assert result.output["error_class"] == "output_limit_exceeded"
    assert result.output["output_limit_exceeded"] is True
    assert result.output["max_output_bytes"] == 96
    assert result.output["output_sizes"]["stdout_bytes"] == 80
    assert result.output["output_sizes"]["stderr_bytes"] == 80
    assert result.output["output_sizes"]["total_bytes"] == 160
    assert result.output["output_digests"]["stdout"].startswith("sha256:")
    assert result.output["output_digests"]["stderr"].startswith("sha256:")
    assert result.output["output_digests"]["record"].startswith("sha256:")
    assert result.output["overflow_evidence_envelope"]["schema"] == (
        "rexecop.output_limit_evidence.v0.1"
    )
    assert "data" not in result.output
    assert "stdout" not in result.output
    assert "stderr" not in result.output


@patch("rexecop.connectors.fixture_loader.entry_points", side_effect=_entry_points)
def test_chrony_apply_blocked_before_backend(_entry_points_mock, tmp_path: Path) -> None:
    controller = OperationController(
        store=FileStore(tmp_path / ".rexecop"),
        govengine_adapter=StaticGovEngineAdapter(GovEngineDecisionType.BLOCKED),
    )

    operation = controller.plan(
        profile_path=Path(profile_root()),
        environment_path=ENVIRONMENT,
        intent="configure_chrony_ntp_server",
        target="chrony-host-01",
        mode="apply",
    )

    assert operation.state == OperationState.BLOCKED.value
    with pytest.raises(RExecOpValidationError):
        controller.start(operation.id)


@patch("rexecop.connectors.fixture_loader.entry_points", side_effect=_entry_points)
def test_chrony_allowed_plan_is_blocked_before_backend_in_stable_read_only(
    _entry_points_mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("REXECOP_MUTATION_POSTURE", raising=False)
    controller = OperationController(
        store=FileStore(tmp_path / ".rexecop"),
        govengine_adapter=StaticGovEngineAdapter(GovEngineDecisionType.ALLOWED),
    )

    operation = controller.plan(
        profile_path=Path(profile_root()),
        environment_path=ENVIRONMENT,
        intent="configure_chrony_ntp_server",
        target="chrony-host-01",
        mode="apply",
    )

    assert operation.state == OperationState.APPROVED.value
    with patch.object(ChronyNtpBackend, "invoke", autospec=True) as invoke:
        with pytest.raises(RExecOpMutationNotCertified):
            controller.start(operation.id)
    invoke.assert_not_called()


@patch("rexecop.connectors.fixture_loader.entry_points", side_effect=_entry_points)
def test_chrony_operation_admission_is_not_execution_approval(
    _entry_points_mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REXECOP_MUTATION_POSTURE", "lab_only")
    controller = OperationController(
        store=FileStore(tmp_path / ".rexecop"),
        govengine_adapter=StaticGovEngineAdapter(GovEngineDecisionType.ALLOWED),
    )

    operation = controller.plan(
        profile_path=Path(profile_root()),
        environment_path=ENVIRONMENT,
        intent="configure_chrony_ntp_server",
        target="chrony-host-01",
        mode="apply",
    )
    completed = controller.start(operation.id)

    assert completed.state == OperationState.FAILED.value
    shared = completed.metadata["shared_state"]
    assert "mutation_states" not in shared
    assert "post_chrony_ntp_state" not in shared.get("connector_results", {})
