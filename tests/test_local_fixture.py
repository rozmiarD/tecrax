from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tecrax import __version__, build_local_fixture_review
from tecrax.cli import main


ROOT = Path(__file__).resolve().parents[1]


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
    assert '0.3.12-alpha' in stdout
    assert 'read-only observations' in stdout
    assert 'one governed chrony/NTP apply slice' in stdout


def test_version_and_public_truth_validator_agree() -> None:
    assert __version__ == '0.3.12a0'
    result = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_public_truth.py')],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == (
        'public_truth_ok:tecrax==0.3.12a0:'
        'govengine==0.16.9:'
        'sclite-core==1.0.8:'
        'rexecop==0.2.17a0'
    )
