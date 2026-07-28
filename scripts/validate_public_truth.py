#!/usr/bin/env python3
from __future__ import annotations

import sys
import tomllib
import subprocess
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import tecrax  # noqa: E402
from sclite.consumer_contracts import validate_consumer_imports  # noqa: E402
from tecrax.local_fixture import build_local_fixture_review  # noqa: E402


EXPECTED_VERSION = '0.4.0rc3'
PUBLISHED_VERSION = '0.3.21a0'
EXPECTED_GOVENGINE = 'govengine==1.0.0rc1'
EXPECTED_SCLITE = 'sclite-core==2.0.0'
EXPECTED_REXECOP = 'rexecop==0.3.0rc3'
PUBLIC_DOCS = (
    'README.md',
    'PUBLIC_STATUS.md',
    'VALIDATION.md',
)
CONTROL_PLANE_RECOVERY_RUNBOOK = (
    'docs/runbooks/infrastructure-control-plane-recovery-runbook.md'
)
FORBIDDEN_CLAIMS = (
    'production-ready',
    'connects to live infrastructure',
    'loads credentials',
    'stores credentials',
    'implements OpenClaw',
    'implements MCP',
    'implements A2A',
    'owns scheduler',
    'owns queue persistence',
    'owns host inventory',
)
ACTION_REF = re.compile(
    r'^\s*(?:-\s+)?uses:\s+([^@\s]+)@([^\s#]+)',
    re.MULTILINE,
)
FULL_SHA = re.compile(r'^[0-9a-f]{40}$')


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def _pyproject() -> dict:
    return tomllib.loads(_read('pyproject.toml'))['project']


def _dependency(project: dict, name: str) -> str:
    prefix = name
    for dependency in project.get('dependencies', []):
        text = str(dependency)
        if text.startswith(prefix):
            return text
    raise AssertionError(f'missing_dependency:{name}')


def _require(errors: list[str], path: str, expected: str) -> None:
    if expected not in _read(path):
        errors.append(f'{path}:missing:{expected}')


def _status_output() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, '-m', 'tecrax.cli', 'status'],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout


def _wheel_smoke_order_errors(workflow: str) -> list[str]:
    status_step = '      - name: Wheel status-only installed smoke'
    normal_step = '      - name: Wheel install smoke'
    normal_install = 'python -m pip install dist/*.whl'
    normal_check = 'python -m pip check'
    if workflow.count(status_step) != 1 or workflow.count(normal_step) != 1:
        return ['ci_wheel_status_smoke_step_count']
    status_index = workflow.index(status_step)
    normal_index = workflow.index(normal_step)
    install_index = workflow.find(normal_install, normal_index)
    check_index = workflow.find(normal_check, normal_index)
    if (
        status_index >= normal_index
        or install_index < normal_index
        or check_index < normal_index
        or install_index > check_index
    ):
        return ['ci_wheel_status_smoke_order']
    return []


def collect_errors() -> list[str]:
    errors: list[str] = []
    errors.extend(validate_consumer_imports('tecrax', ROOT))
    project = _pyproject()
    version = str(project['version'])
    govengine_dep = _dependency(project, 'govengine')
    sclite_dep = _dependency(project, 'sclite-core')
    rexecop_dep = _dependency(project, 'rexecop')

    if project['name'] != 'tecrax':
        errors.append(f'distribution_name_mismatch:{project["name"]}')
    if version != EXPECTED_VERSION:
        errors.append(f'pyproject_version_mismatch:{version}!={EXPECTED_VERSION}')
    if tecrax.__version__ != version:
        errors.append(f'package_version_mismatch:{tecrax.__version__}!={version}')
    if govengine_dep != EXPECTED_GOVENGINE:
        errors.append(f'govengine_dependency_mismatch:{govengine_dep}!={EXPECTED_GOVENGINE}')
    if sclite_dep != EXPECTED_SCLITE:
        errors.append(f'sclite_dependency_mismatch:{sclite_dep}!={EXPECTED_SCLITE}')
    if rexecop_dep != EXPECTED_REXECOP:
        errors.append(f'rexecop_dependency_mismatch:{rexecop_dep}!={EXPECTED_REXECOP}')

    for path in PUBLIC_DOCS:
        _require(errors, path, EXPECTED_VERSION)
        _require(errors, path, EXPECTED_GOVENGINE)
        _require(errors, path, EXPECTED_SCLITE)
        _require(errors, path, EXPECTED_REXECOP)
    _require(errors, 'README.md', f'Latest published PyPI baseline: `tecrax=={PUBLISHED_VERSION}`')
    _require(errors, 'PUBLIC_STATUS.md', f'`tecrax=={PUBLISHED_VERSION}`')
    _require(errors, 'VALIDATION.md', f'latest PyPI publication is `{PUBLISHED_VERSION}`')
    _require(errors, 'README.md', 'tecrax fixture-review --service demo-web')
    _require(errors, 'README.md', 'rexecop.profiles:tecrax')
    _require(errors, 'pyproject.toml', 'rexecop.profiles')
    _require(errors, 'pyproject.toml', 'tecrax:profile_root')
    if not (ROOT / CONTROL_PLANE_RECOVERY_RUNBOOK).is_file():
        errors.append(f'missing_public_runbook:{CONTROL_PLANE_RECOVERY_RUNBOOK}')
    else:
        _require(errors, 'README.md', 'infrastructure-control-plane-recovery-runbook.md')
        _require(errors, 'docs/operation-catalog.md', CONTROL_PLANE_RECOVERY_RUNBOOK)
        _require(errors, CONTROL_PLANE_RECOVERY_RUNBOOK, 'Current activation level: `L1')
        _require(errors, CONTROL_PLANE_RECOVERY_RUNBOOK, 'environment-bound operator helper')
    profile_root = Path(tecrax.profile_root())
    if not (profile_root / 'profile.yaml').is_file():
        errors.append('profile_bundle_missing:profile.yaml')
    _require(errors, 'VALIDATION.md', 'python scripts/validate_public_truth.py')
    _require(
        errors,
        '.github/workflows/ci.yml',
        'actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10',
    )
    _require(errors, '.github/workflows/ci.yml', 'branches: [main]')
    _require(
        errors,
        '.github/workflows/ci.yml',
        'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1',
    )
    _require(errors, '.github/workflows/ci.yml', "python-version: ['3.11', '3.12']")
    _require(errors, '.github/workflows/ci.yml', 'python scripts/validate_public_truth.py')
    _require(errors, '.github/workflows/ci.yml', 'python scripts/validate_active_profile.py')
    _require(errors, '.github/workflows/ci.yml', 'python scripts/validate_secret_topology.py')
    _require(errors, '.github/workflows/ci.yml', 'package-dry-run:')
    _require(errors, '.github/workflows/ci.yml', 'rm -rf dist build *.egg-info')
    _require(errors, '.github/workflows/ci.yml', 'python -m twine check dist/*')
    _require(errors, '.github/workflows/ci.yml', 'Wheel install smoke')
    _require(errors, '.github/workflows/ci.yml', 'python -m pip install dist/*.whl')
    _require(errors, '.github/workflows/ci.yml', 'python -m pip check')
    _require(errors, '.github/workflows/ci.yml', 'Wheel status-only installed smoke')
    _require(errors, '.github/workflows/ci.yml', 'python -m pip install --no-deps dist/*.whl')
    _require(errors, '.github/workflows/ci.yml', 'env -u PYTHONPATH -u PYTHONHOME')
    errors.extend(_wheel_smoke_order_errors(_read('.github/workflows/ci.yml')))
    _require(
        errors,
        '.github/workflows/ci.yml',
        'git clone --depth 1 --branch main https://github.com/rozmiarD/RExecOP.git',
    )
    _require(
        errors,
        '.github/workflows/ci.yml',
        'sclite-core @ git+https://github.com/rozmiarD/SCLite.git@main',
    )
    _require(
        errors,
        '.github/workflows/ci.yml',
        'govengine @ git+https://github.com/rozmiarD/GovEngine.git@main',
    )
    _require(errors, '.github/workflows/ci.yml', 'pip install -e ./ci-deps/rexecop')
    for workflow in sorted((ROOT / '.github' / 'workflows').glob('*.yml')):
        for action, reference in ACTION_REF.findall(
            workflow.read_text(encoding='utf-8')
        ):
            if not FULL_SHA.fullmatch(reference):
                errors.append(
                    f'{workflow.relative_to(ROOT)}:action_not_pinned:'
                    f'{action}@{reference}'
                )

    review = build_local_fixture_review('truth-fixture')
    if review.get('artifact_type') != 'tecrax_local_fixture_review':
        errors.append(f'fixture_review_artifact_mismatch:{review.get("artifact_type")}')
    if review.get('profile_conformance', {}).get('status') != 'passed':
        errors.append('fixture_profile_conformance_failed')
    if review.get('supervision_plan', {}).get('dry_run') is not True:
        errors.append('fixture_supervision_not_dry_run')
    if review.get('supervision_plan', {}).get('live_backend_enabled') is not False:
        errors.append('fixture_live_backend_enabled')
    public_safety = review.get('fixture_receipt', {}).get('public_safety', {})
    if public_safety.get('live_infrastructure_touched') is not False:
        errors.append('fixture_claims_live_infrastructure')
    if public_safety.get('credentials_included') is not False:
        errors.append('fixture_claims_credentials')
    if not review.get('sclite_fixture_receipt_descriptor', {}).get('digest'):
        errors.append('fixture_missing_sclite_descriptor_digest')
    status_code, status = _status_output()
    if status_code != 0:
        errors.append('cli_status:failed')
    for marker in (
        f'Tecrax {tecrax.__version__}',
        'registered mutation candidate',
        'stable_read_only',
        'not mutation_ready',
    ):
        if marker not in status:
            errors.append(f'cli_status:missing:{marker}')
    if '0.3.22-alpha' in status or 'active apply' in status or 'active mutating' in status:
        errors.append('cli_status:stale_or_active_mutation_claim')

    mutation_truth_docs = (
        *PUBLIC_DOCS,
        'docs/mutation-entry-criteria.md',
        'docs/runbooks/chrony-ntp-server-mutation-runbook.md',
    )
    for path in mutation_truth_docs:
        normalized = ' '.join(_read(path).lower().split())
        for marker in (
            'registered mutation candidate',
            'stable_read_only',
            'not mutation_ready',
        ):
            if marker not in normalized:
                errors.append(f'{path}:missing_mutation_truth:{marker}')
        text = _read(path).lower()
        if '0.3.22-alpha' in text or 'active apply' in text or 'active mutating' in text:
            errors.append(f'{path}:stale_or_active_mutation_claim')

    for path in PUBLIC_DOCS:
        lowered = _read(path).lower()
        for claim in FORBIDDEN_CLAIMS:
            claim_text = claim.lower()
            if claim_text in lowered and f'no {claim_text}' not in lowered and f'does not {claim_text}' not in lowered:
                errors.append(f'{path}:forbidden_claim:{claim}')

    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f'public_truth_ok:tecrax=={EXPECTED_VERSION}:{EXPECTED_GOVENGINE}:{EXPECTED_SCLITE}:{EXPECTED_REXECOP}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
