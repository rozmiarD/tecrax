from __future__ import annotations

import subprocess
import sys
import importlib.util
from pathlib import Path

import pytest

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
    assert f'Tecrax {__version__}' in stdout
    assert 'registered mutation candidate' in stdout
    assert 'stable_read_only' in stdout
    assert 'not mutation_ready' in stdout
    assert '0.3.22-alpha' not in stdout
    assert 'active apply' not in stdout


def _public_truth_validator():
    path = ROOT / 'scripts' / 'validate_public_truth.py'
    spec = importlib.util.spec_from_file_location('tecrax_public_truth', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    'status',
    (
        'Tecrax 0.3.22-alpha: active apply mutation_ready\n',
        'Tecrax 0.4.0rc3: active mutating intent\n',
    ),
)
def test_public_truth_rejects_stale_or_active_status_claim(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    validator = _public_truth_validator()
    monkeypatch.setattr(validator, '_status_output', lambda: (0, status))

    assert any('cli_status' in error for error in validator.collect_errors())


def test_public_truth_requires_status_smoke_before_normal_wheel_gate() -> None:
    validator = _public_truth_validator()
    ordered = (
        '      - name: Wheel status-only installed smoke\n'
        '      - name: Wheel install smoke\n'
        '        run: python -m pip install dist/*.whl\n'
        '        run: python -m pip check\n'
    )

    assert validator._wheel_smoke_order_errors(ordered) == []
    reversed_order = (
        '      - name: Wheel install smoke\n'
        '        run: python -m pip install dist/*.whl\n'
        '        run: python -m pip check\n'
        '      - name: Wheel status-only installed smoke\n'
    )
    assert validator._wheel_smoke_order_errors(reversed_order) == [
        'ci_wheel_status_smoke_order'
    ]


def test_version_and_public_truth_validator_agree() -> None:
    assert __version__ == '0.4.0rc3'
    result = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_public_truth.py')],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == (
        'public_truth_ok:tecrax==0.4.0rc3:'
        'govengine==1.0.0rc1:'
        'sclite-core==2.0.0:'
        'rexecop==1.0.0rc1'
    )


@pytest.mark.parametrize(
    'dependency',
    (
        'rexecop==0.3.0rc3',
        'rexecop>=1.0.0rc1',
        'rexecop~=1.0.0rc1',
    ),
    ids=('old-pin', 'minimum-range', 'compatible-range'),
)
def test_public_truth_rejects_old_or_ranged_rexecop_dependency(
    monkeypatch: pytest.MonkeyPatch,
    dependency: str,
) -> None:
    validator = _public_truth_validator()
    project = validator._pyproject()
    project['dependencies'] = [
        dependency if str(item).startswith('rexecop') else item
        for item in project['dependencies']
    ]
    monkeypatch.setattr(validator, '_pyproject', lambda: project)

    assert any(
        error.startswith('rexecop_dependency_mismatch:')
        for error in validator.collect_errors()
    )


@pytest.mark.parametrize(
    ('path', 'drift', 'expected_error'),
    (
        (
            'README.md',
            'rexecop==0.3.0rc3',
            'README.md:old_rexecop_production_truth',
        ),
        (
            'PUBLIC_STATUS.md',
            'rexecop>=1.0.0rc1',
            'PUBLIC_STATUS.md:ranged_rexecop_production_truth',
        ),
        (
            'VALIDATION.md',
            'rexecop~=1.0.0rc1',
            'VALIDATION.md:ranged_rexecop_production_truth',
        ),
    ),
)
def test_public_truth_rejects_old_or_ranged_rexecop_doc_truth(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    drift: str,
    expected_error: str,
) -> None:
    validator = _public_truth_validator()
    original_read = validator._read
    monkeypatch.setattr(
        validator,
        '_read',
        lambda candidate: (
            f'{original_read(candidate)}\n{drift}\n'
            if candidate == path
            else original_read(candidate)
        ),
    )

    assert expected_error in validator._rexecop_truth_drift_errors()
