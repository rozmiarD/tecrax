from __future__ import annotations

from tecrax import build_local_fixture_review
from tecrax.cli import main


def test_local_fixture_review_binds_govengine_and_sclite_without_live_authority() -> None:
    review = build_local_fixture_review('api-fixture')

    assert review['artifact_type'] == 'tecrax_local_fixture_review'
    assert review['profile_conformance']['status'] == 'passed'
    assert review['supervision_plan']['dry_run'] is True
    assert review['supervision_plan']['live_backend_enabled'] is False
    assert review['fixture_receipt']['public_safety']['live_infrastructure_touched'] is False
    assert review['fixture_receipt']['public_safety']['credentials_included'] is False
    assert review['sclite_fixture_receipt_descriptor']['digest']
    assert review['govengine_contract_proof_id'] == 'fixture:service:api-fixture:contract-proof'
    assert 'password' not in str(review).lower()


def test_cli_status_keeps_local_fixture_posture(capsys) -> None:
    assert main(['status']) == 0

    stdout = capsys.readouterr().out
    assert 'local-fixture profile' in stdout
    assert 'no live infrastructure' in stdout
