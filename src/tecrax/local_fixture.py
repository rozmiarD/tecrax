from __future__ import annotations

from typing import Any

from govengine.contract_proofs import validate_runtime_contract_proof
from govengine.execution.supervision import GovSupervisionPlan, validate_supervision_plan
from govengine.planning import GovPlanIntentContract, GovTaskContract, validate_plan_intent_contract
from govengine.profiles import tecrax_infra_ops_profile, validate_profile_conformance
from govengine.review import GovReviewResult, validate_review_result
from govengine.runtime_shell import GovControlAction, GovRuntimeSnapshot, validate_runtime_snapshot
from sclite.integrity import artifact_descriptor


NON_CLAIMS = (
    'Does not connect to live infrastructure.',
    'Does not load or store credentials.',
    'Does not authorize or execute infrastructure changes.',
    'Does not make GovEngine own infrastructure semantics.',
)


def build_local_fixture_review(service_name: str = 'demo-web') -> dict[str, Any]:
    """Build a public-safe fixture review across Tecrax, GovEngine, and SCLite."""

    fixture_ref = _fixture_ref(service_name)
    profile = tecrax_infra_ops_profile()
    conformance = validate_profile_conformance(profile)
    task = GovTaskContract(
        contract_id=f'{fixture_ref}:task',
        task_family='dry_run_change',
        objective='Review a proposed local fixture service change.',
        capability='dry_run_infra_change_review',
        target_ref=fixture_ref,
        target_kind='service',
        evidence_goal='fixture_receipt_required',
        constraints={'change_scope': 'local_fixture', 'execution_mode': 'dry_run'},
        metadata={'fixture': True, 'live_infrastructure': False},
    )
    intent = validate_plan_intent_contract(GovPlanIntentContract(
        intent_id=f'{fixture_ref}:intent',
        profile=profile.name,
        planner_id='tecrax-local-fixture',
        goal='Validate a fixture-only infrastructure change handoff.',
        task_contracts=(task,),
        non_claims=('Intent does not authorize infrastructure changes.',),
    ))
    supervision = validate_supervision_plan(GovSupervisionPlan(
        plan_id=f'{fixture_ref}:supervision',
        request_id=task.contract_id,
        runner_profile='local_fixture_only',
        dry_run=True,
        live_backend_enabled=False,
        metadata={'fixture': True, 'host_connection': 'none'},
    ))
    runtime_snapshot = validate_runtime_snapshot(GovRuntimeSnapshot(
        snapshot_id=f'{fixture_ref}:snapshot',
        run_id=f'{fixture_ref}:run',
        state='running_dry_run',
        control_actions=(
            GovControlAction(
                action_id=f'{fixture_ref}:record',
                run_id=f'{fixture_ref}:run',
                action='record_only',
                profile=profile.name,
            ),
        ),
        profile=profile.name,
        non_claims=('Snapshot is local-fixture only and storage-neutral.',),
    ))
    fixture_receipt = {
        'artifact_type': 'tecrax_local_fixture_receipt',
        'service_ref': fixture_ref,
        'change_mode': 'dry_run',
        'observations': [
            'fixture_plan_parsed',
            'fixture_change_rendered',
            'rollback_plan_present',
        ],
        'public_safety': {
            'live_infrastructure_touched': False,
            'credentials_included': False,
            'private_inventory_included': False,
        },
    }
    review = validate_review_result(GovReviewResult(
        review_id=f'{fixture_ref}:review',
        subject_ref=intent.intent_id,
        verdict='passed',
        qualification_refs=(artifact_descriptor(fixture_receipt)['digest'],),
    ))
    proof = validate_runtime_contract_proof(
        _proof_with_fixture_ref(fixture_ref)
    )

    return {
        'artifact_type': 'tecrax_local_fixture_review',
        'profile': profile.as_dict(),
        'profile_conformance': conformance.as_dict(),
        'intent': intent.as_dict(),
        'supervision_plan': supervision.as_dict(),
        'runtime_snapshot': runtime_snapshot.as_dict(),
        'fixture_receipt': fixture_receipt,
        'sclite_fixture_receipt_descriptor': artifact_descriptor(fixture_receipt),
        'review_result': review.as_dict(),
        'govengine_contract_proof_id': proof.proof_id,
        'non_claims': list(NON_CLAIMS),
    }


def _proof_with_fixture_ref(fixture_ref: str):
    from govengine.contract_proofs import tecrax_contract_proof

    proof = tecrax_contract_proof()
    return proof.__class__(
        proof_id=f'{fixture_ref}:contract-proof',
        profile=proof.profile,
        profile_conformance=proof.profile_conformance,
        intent=proof.intent,
        policy_constraints=proof.policy_constraints,
        supervision_plan=proof.supervision_plan,
        runtime_snapshot=proof.runtime_snapshot,
        review_result=proof.review_result,
        change_order=proof.change_order,
        evidence_refs=(f'sclite:artifact_descriptor:{fixture_ref}',),
        vocabulary=proof.vocabulary,
        non_claims=proof.non_claims,
        metadata={'runtime_family': 'infra_ops', 'proof_scope': 'local_fixture'},
    )


def _fixture_ref(service_name: str) -> str:
    label = ''.join(ch if ch.isalnum() or ch in {'-', '_'} else '-' for ch in str(service_name).strip().lower())
    return f'fixture:service:{label or "demo-web"}'
