from __future__ import annotations

import hashlib
import json
import stat
import subprocess as stdlib_subprocess
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from govengine.approvals import (
    ApprovalAttestation,
    ApprovalRevocationPort,
    ApprovalTrustPolicy,
    approval_attestation_digest,
)
from govengine.capabilities import (
    CapabilityInventoryBinding,
    OperationCapabilityRequirements,
    capability_inventory_binding_digest,
    operation_capability_requirements_digest,
)
from govengine.governance import (
    GovernanceRequest,
    execution_facts_digest,
    governance_subject_digest,
    requested_scope_digest,
)
from govengine.governance_decision import (
    ApprovalSignatureVerificationPort,
    PolicyActivationPort,
)
from govengine.governance_decision_signing import sign_governance_decision
from govengine.policy import PolicyCompiler, policy_pack_digest
from govengine.policy.activation import PolicyActivationBinding
from govengine.scope_policy import ScopePolicyBinding, scope_policy_binding_digest
from govengine.signing import (
    DemoDigestSigner,
    DemoDigestVerifier,
    SigningPolicy,
    TrustPolicy,
)
from govengine.typed_execution_governance import (
    TypedExecutionGovernanceRequest,
    typed_execution_governance_request_digest,
)
from govengine.typed_execution_governed_admission import (
    TypedExecutionGovernedAdmissionV02,
    evaluate_typed_execution_governed_admission_v02,
)

from rexecop.adapters.govengine_port.contracts import GovEngineDecisionType
from rexecop.adapters.govengine_port.runtime_authority import (
    RuntimeAttemptGovernanceFacts,
    SignedGovernedAttemptBundle,
)
from rexecop.adapters.govengine_port.static_adapter import StaticGovEngineAdapter
from rexecop.connectors.base import ConnectorRequest, ConnectorResponse
from rexecop.connectors.runtime import ConnectorDispatcher
from rexecop.errors import RExecOpMutationNotCertified, RExecOpValidationError
from rexecop.execution.backend import StepExecutionContext
from rexecop.execution.executor import StepExecutor
from rexecop.operation.controller import OperationController
from rexecop.operation.state import OperationState
from rexecop.runtime_ops.governance_facts import _runtime_inventory
from rexecop.storage.file_store import FileStore
from tecrax import profile_root
from tecrax.connectors import chrony
from tecrax.connectors.chrony import ChronyNtpBackend, build_chrony_ntp_backend

REPO_ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = REPO_ROOT / "examples/environments/chrony-ntp-server.apply.example.yaml"


@pytest.fixture(autouse=True)
def _reset_chrony_fixture_state() -> Iterator[None]:
    chrony._reset_fixture_state_registry()  # noqa: SLF001
    yield
    chrony._reset_fixture_state_registry()  # noqa: SLF001


class _ChronyEntryPoint:
    name = "tecrax_chrony_ntp"

    def load(self):
        return build_chrony_ntp_backend


def _entry_points(**_: object) -> list[_ChronyEntryPoint]:
    return [_ChronyEntryPoint()]


class _ApprovalRevocations(ApprovalRevocationPort):
    def __init__(self) -> None:
        self.lookups = 0

    def is_revoked(
        self,
        approval_id: str,
        *,
        approval_digest: str,
        revocation_ref: str,
    ) -> bool:
        assert approval_id
        assert approval_digest.startswith("sha256:")
        assert revocation_ref == "test-revocations:tecrax-chrony"
        self.lookups += 1
        return False


class _ApprovalSignatureVerifier(ApprovalSignatureVerificationPort):
    def verify_approval_signature(
        self,
        attestation: ApprovalAttestation,
        *,
        approval_digest: str,
        trust_policy_id: str,
    ) -> bool:
        return bool(attestation.signature_ref and approval_digest and trust_policy_id)


class _PolicyActivation(PolicyActivationPort):
    def __init__(self, request: dict[str, Any], *, now: datetime) -> None:
        self.request = request
        self.now = now

    def current_binding(self, policy_id: str) -> PolicyActivationBinding:
        return PolicyActivationBinding.from_mapping(
            {
                "schema_version": "v1",
                "binding_id": f"test-policy-activation:{policy_id}",
                "policy_id": policy_id,
                "policy_version": self.request["policy_pack"]["version"],
                "policy_pack_digest": self.request["policy_pack_digest"],
                "policy_epoch": self.request["policy_epoch"],
                "issuer_ref": self.request["policy_pack"]["issuer_ref"],
                "trust_ref": "test-policy-trust:tecrax-chrony",
                "status": "active",
                "not_before": (self.now - timedelta(minutes=1)).isoformat(),
                "expires_at": (self.now + timedelta(minutes=1)).isoformat(),
            }
        )


class _GovernedChronyAuthority:
    """Host adapter that delegates every allow/deny decision to GovEngine v0.2."""

    def __init__(self, *, revocations: _ApprovalRevocations) -> None:
        self.revocations = revocations
        self.requests: list[RuntimeAttemptGovernanceFacts] = []
        self.bundles: list[SignedGovernedAttemptBundle] = []

    def authorize_governed_attempt(
        self,
        facts: RuntimeAttemptGovernanceFacts,
        *,
        typed_execution_request: TypedExecutionGovernanceRequest,
        actual_operation_mode: str,
    ) -> SignedGovernedAttemptBundle:
        self.requests.append(facts)
        now = datetime.now(UTC).replace(microsecond=0)
        governance_request = self._governance_request(
            facts,
            typed_execution_request=typed_execution_request,
            actual_operation_mode=actual_operation_mode,
            now=now,
        )
        admission, decision = evaluate_typed_execution_governed_admission_v02(
            typed_execution_request,
            governance_request,
            actual_operation_mode=actual_operation_mode,
            policy_activation_port=_PolicyActivation(
                governance_request.as_dict(),
                now=now,
            ),
            evaluated_at=now,
            admitted_at=now,
            approval_trust_policy=ApprovalTrustPolicy(
                policy_id="test-runtime-approvers",
                trusted_roles=("runtime-test-approver",),
                trusted_domains=("tests:tecrax",),
                trusted_approver_refs=("test-operator",),
                require_signature_ref=True,
            ),
            approval_revocation_port=self.revocations,
            approval_signature_verifier=_ApprovalSignatureVerifier(),
            authorization_nonce=f"tecrax-chrony-nonce:{facts.attempt_id}",
            authorization_expires_at=now + timedelta(seconds=30),
            decision_id=f"tecrax-chrony-decision:{facts.attempt_id}",
        )
        bundle = SignedGovernedAttemptBundle(
            governance_request=governance_request,
            governed_admission=admission,
            decision=decision,
            signed_artifact=sign_governance_decision(
                decision,
                signer=DemoDigestSigner(signer_id="test-decision-signer"),
                payload_ref=f"artifact://tests/{decision.decision_id}",
            ),
        )
        self.bundles.append(bundle)
        return bundle

    def _governance_request(
        self,
        facts: RuntimeAttemptGovernanceFacts,
        *,
        typed_execution_request: TypedExecutionGovernanceRequest,
        actual_operation_mode: str,
        now: datetime,
    ) -> GovernanceRequest:
        compiled = PolicyCompiler().compile(
            {
                "policy_id": "test-tecrax-chrony-runtime-mutation",
                "version": "1",
                "schema_version": "v1",
                "issuer_ref": "tests:tecrax",
                "policy_epoch": 1,
                "validity": {
                    "not_before": (now - timedelta(minutes=1)).isoformat(),
                    "expires_at": (now + timedelta(minutes=1)).isoformat(),
                },
                "supersedes": [],
                "rules": [
                    {
                        "rule_id": "govern-exact-chrony-plugin",
                        "effect": "approval_required",
                        "conditions": [
                            {
                                "path": "action.mode",
                                "operator": "eq",
                                "value": "mutation",
                            }
                        ],
                        "reason_code": "mutation_requires_approval",
                        "obligations": [
                            {"obligation_id": "receipt", "kind": "receipt"}
                        ],
                        "constraints": [
                            {
                                "constraint_id": "bounded-output",
                                "kind": "output_limit",
                                "value": 4096,
                            },
                            {
                                "constraint_id": "exact-chrony-backend",
                                "kind": "allowed_backend_classes",
                                "value": ["tecrax_chrony_ntp"],
                            },
                            {
                                "constraint_id": "fixture-has-no-egress",
                                "kind": "allowed_network_egress",
                                "value": ["no_network"],
                            },
                        ],
                    }
                ],
            }
        )
        assert compiled.ok and compiled.policy_pack is not None
        policy_pack = compiled.policy_pack
        pack_digest = policy_pack_digest(policy_pack)
        execution_facts = {
            "schema_version": "v0.1",
            "request_id": f"test-governance:{facts.attempt_id}",
            "subject_ref": (
                f"governance:{facts.operation_id}:{facts.step_id}:{facts.attempt_id}"
            ),
            "principal": {"kind": "operator"},
            "action": {"mode": "mutation"},
            "resource": {"criticality": "low"},
            "context": {"environment": "test"},
            "evidence_refs": [],
            "runtime_attempt": facts.as_dict(),
            "metadata": {
                "actual_operation_mode": actual_operation_mode,
                "typed_execution_governance_request_digest": (
                    typed_execution_governance_request_digest(
                        typed_execution_request
                    )
                ),
            },
        }
        requested_scope = {"target_namespace": "chrony-host-01"}
        assert requested_scope_digest(requested_scope) == facts.requested_scope_digest
        inventory = _runtime_inventory(
            runtime_instance_id=facts.runtime_instance_id,
            inventory_epoch=facts.inventory_epoch,
        )
        inventory_payload = inventory.as_dict()
        inventory_payload["backend_classes"] = sorted(
            {*inventory.backend_classes, typed_execution_request.backend_class}
        )
        inventory_payload["capabilities"] = sorted(
            {
                *inventory.capabilities,
                *typed_execution_request.capability_descriptor.declared_capability_descriptors,
            }
        )
        inventory = CapabilityInventoryBinding.from_mapping(inventory_payload)
        assert facts.capability_inventory_digest == capability_inventory_binding_digest(
            inventory
        )
        scope_policy = ScopePolicyBinding.from_mapping(
            {
                "schema_version": "v1",
                "binding_id": "test-scope-policy:tecrax-chrony",
                "policy_pack_digest": pack_digest,
                "policy_epoch": 1,
                "source_ref": "test-policy:test-tecrax-chrony-runtime-mutation@1",
                "attestation_ref": "test-attestation:scope",
                "allowed_target_namespaces": ["chrony-host-01"],
                "network_allowed": False,
                "allowed_schemes": [],
                "allowed_ports": [],
                "allowed_address_classes": [],
                "redirect_policy": "same_origin",
                "private_networks_allowed": False,
            }
        )
        requirements = OperationCapabilityRequirements.from_mapping(
            {
                "schema_version": "v1",
                "requirements_id": f"test-requirements:{facts.attempt_id}",
                "operation_id": facts.operation_id,
                "step_id": facts.step_id,
                "execution_spec_digest": facts.execution_spec_digest,
                "required_backend_class": typed_execution_request.backend_class,
                "side_effect_class": "mutation",
                "required_capabilities": list(
                    typed_execution_request.required_capability_descriptors
                ),
            }
        )
        request: dict[str, Any] = {
            "schema_version": "v1",
            "transaction_id": f"test-governance:{facts.attempt_id}",
            "operation_id": facts.operation_id,
            "step_id": facts.step_id,
            "attempt_id": facts.attempt_id,
            "policy_pack": policy_pack.as_dict(),
            "policy_pack_digest": pack_digest,
            "policy_epoch": 1,
            "execution_facts": execution_facts,
            "execution_facts_digest": execution_facts_digest(execution_facts),
            "execution_spec_digest": facts.execution_spec_digest,
            "payload_digest": facts.payload_digest,
            "requested_scope": requested_scope,
            "requested_scope_digest": facts.requested_scope_digest,
            "scope_policy_binding": scope_policy.as_dict(),
            "scope_policy_binding_digest": scope_policy_binding_digest(scope_policy),
            "capability_requirements": requirements.as_dict(),
            "capability_requirements_digest": (
                operation_capability_requirements_digest(requirements)
            ),
            "capability_inventory": inventory.as_dict(),
            "capability_inventory_digest": facts.capability_inventory_digest,
            "side_effect_class": "mutation",
            "runtime_instance_id": facts.runtime_instance_id,
            "lease_id": facts.lease_id,
            "lease_epoch": facts.lease_epoch,
            "fencing_token_digest": facts.fencing_token_digest,
        }
        subject = GovernanceRequest.from_mapping(request)
        approval = ApprovalAttestation.from_mapping(
            {
                "schema_version": "v1",
                "approval_id": f"test-approval:{facts.attempt_id}",
                "subject_digest": governance_subject_digest(subject),
                "operation_id": facts.operation_id,
                "step_id": facts.step_id,
                "attempt_id": facts.attempt_id,
                "execution_spec_digest": facts.execution_spec_digest,
                "execution_facts_digest": request["execution_facts_digest"],
                "target_scope_digest": facts.requested_scope_digest,
                "policy_pack_digest": pack_digest,
                "policy_epoch": 1,
                "approved_side_effect_class": "mutation",
                "approver_ref": "test-operator",
                "approver_role": "runtime-test-approver",
                "trust_domain": "tests:tecrax",
                "issued_at": now.isoformat(),
                "not_before": (now - timedelta(seconds=1)).isoformat(),
                "expires_at": (now + timedelta(seconds=30)).isoformat(),
                "revocation_ref": "test-revocations:tecrax-chrony",
                "signature_ref": "test-signature:tecrax-chrony",
            }
        )
        request["approval_attestation"] = approval.as_dict()
        request["approval_attestation_digest"] = approval_attestation_digest(approval)
        return GovernanceRequest.from_mapping(request)


class _GovernedChronyEntryPoint:
    name = "tecrax_chrony_ntp"

    def __init__(self) -> None:
        self.load_calls = 0
        self.factory_calls = 0
        self.constructed_runtimes: list[ChronyNtpBackend] = []

    def load(self):  # type: ignore[no-untyped-def]
        self.load_calls += 1

        def factory(**kwargs: object) -> ChronyNtpBackend:
            self.factory_calls += 1
            runtime = build_chrony_ntp_backend(**kwargs)
            self.constructed_runtimes.append(runtime)
            return runtime

        return factory


def _governed_runtime_kwargs(
    authority: _GovernedChronyAuthority,
    revocations: _ApprovalRevocations,
) -> dict[str, object]:
    return {
        "governed_attempt_authority": authority,
        "approval_revocation_port": revocations,
        "governance_decision_verifier": DemoDigestVerifier(
            allowed_signer_ids=("test-decision-signer",)
        ),
        "governance_signing_policy": SigningPolicy(
            require_signature=True,
            allowed_modes=("detached_demo_digest",),
            required_signer_ids=("test-decision-signer",),
        ),
        "governance_trust_policy": TrustPolicy(),
    }


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


def test_chrony_fixture_state_persists_across_fresh_backend_instances() -> None:
    config = {"fixture_only": True, "allowed_subnet": "192.0.2.0/24"}

    applied = build_chrony_ntp_backend(
        connector_name="chrony_ntp_server",
        config=config,
        mutating_allowed=True,
    ).invoke(
        ConnectorRequest(
            connector="chrony_ntp_server",
            action="apply_chrony_ntp_server",
            target="chrony-host-01",
            mode="apply",
        )
    )
    observed = build_chrony_ntp_backend(
        connector_name="chrony_ntp_server",
        config=config,
        mutating_allowed=True,
    ).invoke(
        ConnectorRequest(
            connector="chrony_ntp_server",
            action="read_chrony_ntp_server_state",
            target="chrony-host-01",
            mode="apply",
        )
    )
    rolled_back = build_chrony_ntp_backend(
        connector_name="chrony_ntp_server",
        config=config,
        mutating_allowed=True,
    ).invoke(
        ConnectorRequest(
            connector="chrony_ntp_server",
            action="rollback_chrony_ntp_server",
            target="chrony-host-01",
            mode="recovery",
        )
    )
    restored = build_chrony_ntp_backend(
        connector_name="chrony_ntp_server",
        config=config,
        mutating_allowed=True,
    ).invoke(
        ConnectorRequest(
            connector="chrony_ntp_server",
            action="read_chrony_ntp_server_state",
            target="chrony-host-01",
            mode="recovery",
        )
    )

    assert applied.success is True
    assert applied.data["changed"] is True
    assert observed.data["desired_state_applied"] is True
    assert rolled_back.success is True
    assert rolled_back.data["changed"] is True
    assert restored.data["desired_state_applied"] is False
    with chrony._FIXTURE_STATE_LOCK:  # noqa: SLF001
        assert chrony._FIXTURE_STATE == {}  # noqa: SLF001


def test_chrony_fixture_initial_default_is_restored_and_registry_entry_removed() -> None:
    config = {
        "fixture_only": True,
        "fixture_initially_applied": True,
        "allowed_subnet": "192.0.2.0/24",
    }

    def invoke(action: str, mode: str) -> ConnectorResponse:
        return build_chrony_ntp_backend(
            connector_name="chrony_ntp_server",
            config=config,
            mutating_allowed=True,
        ).invoke(
            ConnectorRequest(
                connector="chrony_ntp_server",
                action=action,
                target="chrony-host-01",
                mode=mode,
            )
        )

    initial = invoke("read_chrony_ntp_server_state", "apply")
    rolled_back = invoke("rollback_chrony_ntp_server", "recovery")
    after_rollback = invoke("read_chrony_ntp_server_state", "recovery")
    reapplied = invoke("apply_chrony_ntp_server", "apply")
    restored_default = invoke("read_chrony_ntp_server_state", "apply")

    assert initial.data["desired_state_applied"] is True
    assert rolled_back.data["changed"] is True
    assert after_rollback.data["desired_state_applied"] is False
    assert reapplied.data["changed"] is True
    assert restored_default.data["desired_state_applied"] is True
    with chrony._FIXTURE_STATE_LOCK:  # noqa: SLF001
        assert chrony._FIXTURE_STATE == {}  # noqa: SLF001


def test_chrony_fixture_state_isolated_by_target_and_normalized_subnet() -> None:
    def invoke(
        *,
        action: str,
        target: str,
        subnet: str,
    ) -> ConnectorResponse:
        return build_chrony_ntp_backend(
            connector_name="chrony_ntp_server",
            config={"fixture_only": True, "allowed_subnet": subnet},
            mutating_allowed=True,
        ).invoke(
            ConnectorRequest(
                connector="chrony_ntp_server",
                action=action,
                target=target,
                mode="apply",
            )
        )

    assert invoke(
        action="apply_chrony_ntp_server",
        target="chrony-host-01",
        subnet="192.0.2.0/24",
    ).success
    same_key = invoke(
        action="read_chrony_ntp_server_state",
        target="chrony-host-01",
        subnet="192.0.2.0/24",
    )
    other_target = invoke(
        action="read_chrony_ntp_server_state",
        target="chrony-host-02",
        subnet="192.0.2.0/24",
    )
    other_subnet = invoke(
        action="read_chrony_ntp_server_state",
        target="chrony-host-01",
        subnet="198.51.100.0/24",
    )

    assert same_key.data["desired_state_applied"] is True
    assert other_target.data["desired_state_applied"] is False
    assert other_subnet.data["desired_state_applied"] is False


def test_chrony_concurrent_same_key_apply_has_one_state_change() -> None:
    workers = 12
    barrier = Barrier(workers)

    def apply_once(_: int) -> ConnectorResponse:
        backend = build_chrony_ntp_backend(
            connector_name="chrony_ntp_server",
            config={
                "fixture_only": True,
                "allowed_subnet": "192.0.2.0/24",
            },
            mutating_allowed=True,
        )
        barrier.wait(timeout=5)
        return backend.invoke(
            ConnectorRequest(
                connector="chrony_ntp_server",
                action="apply_chrony_ntp_server",
                target="chrony-host-01",
                mode="apply",
            )
        )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        responses = list(executor.map(apply_once, range(workers)))

    assert all(response.success for response in responses)
    assert sum(response.data["changed"] is True for response in responses) == 1
    assert sum(response.data["changed"] is False for response in responses) == workers - 1


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
def test_chrony_retry_policy_uses_runtime_classifier(
    _entry_points_mock,
    tmp_path: Path,
) -> None:
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

    persisted_plan = controller.store.load_plan(operation.id)
    assert persisted_plan.retry_policy_summary == {
        "max_attempts": 0,
        "allowed_on": [],
        "blocked_on": ["policy_denied", "validation_failed"],
    }
    for error_class in (
        "receipt_postcondition_failed",
        "outcome_indeterminate",
        "transient_connector_error",
    ):
        assert (
            controller.orchestrator._can_retry(  # noqa: SLF001
                persisted_plan,
                error_class=error_class,
                attempts=1,
            )
            is False
        )

    permissive_control = deepcopy(persisted_plan)
    permissive_control.retry_policy_summary = {
        "max_attempts": 1,
        "allowed_on": [],
        "blocked_on": [],
    }
    assert (
        controller.orchestrator._can_retry(  # noqa: SLF001
            permissive_control,
            error_class="outcome_indeterminate",
            attempts=1,
        )
        is False
    )
    assert (
        controller.orchestrator._can_retry(  # noqa: SLF001
            permissive_control,
            error_class="transient_connector_error",
            attempts=1,
        )
        is True
    )


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


def test_chrony_fixture_apply_failure_rollback_and_replay_are_governed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment = yaml.safe_load(ENVIRONMENT.read_text(encoding="utf-8"))[
        "environment"
    ]
    connector = environment["connectors"]["chrony_ntp_server"]
    assert connector["execution_posture"] == "fixture_only"
    assert connector["fixture_only"] is True
    assert "wrapper_command" not in connector
    assert all(
        "constraints" not in rule and "obligations" not in rule
        for rule in environment["policy_pack"]["rules"]
    )

    monkeypatch.setenv("REXECOP_MUTATION_POSTURE", "lab_only")
    store = FileStore(tmp_path / ".rexecop")
    revocations = _ApprovalRevocations()
    authority = _GovernedChronyAuthority(revocations=revocations)
    point = _GovernedChronyEntryPoint()
    real_invoke = ChronyNtpBackend.invoke
    io_calls: list[tuple[str, str]] = []
    post_io_failure_injected = False

    def invoke_with_post_io_failure(
        runtime: ChronyNtpBackend,
        request: ConnectorRequest,
    ) -> ConnectorResponse:
        nonlocal post_io_failure_injected
        response = real_invoke(runtime, request)
        io_calls.append((request.mode, request.action))
        if (
            not post_io_failure_injected
            and request.mode == "apply"
            and request.action == "read_chrony_ntp_server_state"
            and response.success
            and response.data.get("desired_state_applied") is True
        ):
            post_io_failure_injected = True
            return ConnectorResponse(
                connector=request.connector,
                action=request.action,
                success=False,
                error="deterministic post-I/O fixture failure",
                data={"error_class": "validation_failed"},
            )
        return response

    monkeypatch.setattr(ChronyNtpBackend, "invoke", invoke_with_post_io_failure)
    with patch(
        "rexecop.connectors.fixture_loader.entry_points",
        return_value=[point],
    ):
        controller = OperationController(
            store,
            **_governed_runtime_kwargs(authority, revocations),
        )
        parent = controller.plan(
            profile_path=Path(profile_root()),
            environment_path=ENVIRONMENT,
            intent="configure_chrony_ntp_server",
            target="chrony-host-01",
            mode="apply",
        )
        controller.approve(parent.id, approved_by="test-operator")
        failed = controller.start(parent.id)

        assert failed.state == OperationState.FAILED.value
        assert failed.metadata["step_results"]["apply_chrony_ntp_server"][
            "success"
        ] is True
        assert post_io_failure_injected is True
        assert point.factory_calls == 3
        assert len({id(runtime) for runtime in point.constructed_runtimes}) == 3

        pending = controller.rollback(parent.id)
        child_id = str(pending["rollback_operation_id"])
        child = controller.get_operation(child_id)
        child_plan = controller.store.load_plan(child_id)
        assert pending["success"] is False
        assert child.state == OperationState.WAITING_FOR_APPROVAL.value
        assert child_id != parent.id
        assert child_plan.mode == "recovery"
        assert [step["id"] for step in child_plan.planned_steps] == [
            "rollback_chrony_ntp_server"
        ]

        controller.approve(child_id, approved_by="test-rollback-operator")
        child = controller.start(child_id)
        assert child.state == OperationState.COMPLETED.value
        assert point.factory_calls == 4
        assert len({id(runtime) for runtime in point.constructed_runtimes}) == 4

        rollback_result = child.metadata["step_results"][
            "rollback_chrony_ntp_server"
        ]
        assert rollback_result["success"] is True
        assert rollback_result["output"]["after_state"][
            "desired_state_applied"
        ] is False
        assert rollback_result["receipt_conformance"]["conformant"] is True
        assert child.metadata["shared_state"]["execution_receipt"][
            "executed_steps"
        ] == ["rollback_chrony_ntp_server"]

        parent_permit = store.load_execution_permit(
            parent.id,
            "apply_chrony_ntp_server",
        )
        child_permit = store.load_execution_permit(
            child_id,
            "rollback_chrony_ntp_server",
        )
        parent_attempt = next(
            facts
            for facts in authority.requests
            if facts.operation_id == parent.id
            and facts.step_id == "apply_chrony_ntp_server"
        )
        child_attempt = next(
            facts for facts in authority.requests if facts.operation_id == child_id
        )
        assert parent_attempt.attempt_id != child_attempt.attempt_id
        assert (parent_attempt.lease_id, parent_attempt.lease_epoch) != (
            child_attempt.lease_id,
            child_attempt.lease_epoch,
        )
        assert parent_permit["permit_digest"] != child_permit["permit_digest"]
        for field in ("decision_digest", "authorization_id", "nonce_digest"):
            assert (
                parent_permit["governance_decision"][field]
                != child_permit["governance_decision"][field]
            )
        assert child_permit["mode"] == "recovery"
        assert child_permit["governed_admission_binding"][
            "actual_operation_mode"
        ] == "recovery"

        assert authority.bundles
        for bundle in authority.bundles:
            admission = bundle.governed_admission
            assert isinstance(admission, TypedExecutionGovernedAdmissionV02)
            assert admission.plugin_backend_class == "tecrax_chrony_ntp"
            assert admission.plugin_egress_class == "no_network"
            assert bundle.decision.controls.allowed_backend_classes == (
                "tecrax_chrony_ntp",
            )
            assert bundle.decision.controls.allowed_network_egress == (
                "no_network",
            )

        claim_count = len(list((store.root / "governance_claims").glob("*.json")))
        attempt_count = len(list((store.root / "attempts").glob("*/*.json")))
        counts_before_replay = (
            len(authority.requests),
            claim_count,
            attempt_count,
            point.load_calls,
            point.factory_calls,
            len(point.constructed_runtimes),
            len(io_calls),
        )
        replay = controller.rollback(parent.id)
        counts_after_replay = (
            len(authority.requests),
            len(list((store.root / "governance_claims").glob("*.json"))),
            len(list((store.root / "attempts").glob("*/*.json"))),
            point.load_calls,
            point.factory_calls,
            len(point.constructed_runtimes),
            len(io_calls),
        )

    assert replay["rollback_operation_id"] == child_id
    assert replay["success"] is True
    assert counts_after_replay == counts_before_replay
    assert io_calls == [
        ("apply", "read_chrony_ntp_server_state"),
        ("apply", "apply_chrony_ntp_server"),
        ("apply", "read_chrony_ntp_server_state"),
        ("recovery", "rollback_chrony_ntp_server"),
    ]
