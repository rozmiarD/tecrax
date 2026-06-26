#!/usr/bin/env python3
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import tecrax  # noqa: E402
from tecrax.local_fixture import build_local_fixture_review  # noqa: E402


EXPECTED_VERSION = '0.3.5a0'
EXPECTED_RELEASE_LABEL = '0.3.5-alpha'
PUBLISHED_VERSION = '0.3.5a0'
EXPECTED_GOVENGINE = 'govengine>=0.16.0,<0.17'
EXPECTED_SCLITE = 'sclite-core>=1.0.4,<1.1'
EXPECTED_REXECOP = 'rexecop>=0.2.6a0,<0.3'
PUBLIC_DOCS = (
    'README.md',
    'PUBLIC_STATUS.md',
    'VALIDATION.md',
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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def _pyproject() -> dict:
    return tomllib.loads(_read('pyproject.toml'))['project']


def _dependency(project: dict, name: str) -> str:
    prefix = f'{name}>='
    for dependency in project.get('dependencies', []):
        text = str(dependency)
        if text.startswith(prefix):
            return text
    raise AssertionError(f'missing_dependency:{name}')


def _require(errors: list[str], path: str, expected: str) -> None:
    if expected not in _read(path):
        errors.append(f'{path}:missing:{expected}')


def collect_errors() -> list[str]:
    errors: list[str] = []
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
    _require(errors, 'PUBLIC_STATUS.md', EXPECTED_RELEASE_LABEL)
    _require(errors, 'README.md', f'Latest published PyPI baseline: `tecrax=={PUBLISHED_VERSION}`')
    _require(errors, 'PUBLIC_STATUS.md', f'`tecrax=={PUBLISHED_VERSION}`')
    _require(errors, 'VALIDATION.md', f'latest PyPI publication is `{PUBLISHED_VERSION}`')
    _require(errors, 'README.md', 'tecrax fixture-review --service demo-web')
    _require(errors, 'README.md', 'rexecop.profiles:tecrax')
    _require(errors, 'pyproject.toml', 'rexecop.profiles')
    _require(errors, 'pyproject.toml', 'tecrax:profile_root')
    profile_root = Path(tecrax.profile_root())
    if not (profile_root / 'profile.yaml').is_file():
        errors.append('profile_bundle_missing:profile.yaml')
    _require(errors, 'VALIDATION.md', 'python scripts/validate_public_truth.py')
    _require(errors, '.github/workflows/ci.yml', 'actions/checkout@v6')
    _require(errors, '.github/workflows/ci.yml', 'actions/setup-python@v6')
    _require(errors, '.github/workflows/ci.yml', "python-version: ['3.11', '3.12']")
    _require(errors, '.github/workflows/ci.yml', 'python scripts/validate_public_truth.py')
    _require(errors, '.github/workflows/ci.yml', 'python scripts/validate_active_profile.py')
    _require(errors, '.github/workflows/ci.yml', 'python scripts/validate_secret_topology.py')
    _require(errors, '.github/workflows/ci.yml', 'package-dry-run:')
    _require(errors, '.github/workflows/ci.yml', 'rm -rf dist build *.egg-info')
    _require(errors, '.github/workflows/ci.yml', 'python -m twine check dist/*')
    _require(errors, '.github/workflows/ci.yml', 'python -m pip check')
    _require(errors, '.github/workflows/ci.yml', 'sclite-core @ git+https://github.com/rozmiarD/SCLite.git@main')
    _require(errors, '.github/workflows/ci.yml', 'govengine @ git+https://github.com/rozmiarD/GovEngine.git@main')
    _require(errors, '.github/workflows/ci.yml', 'repository: rozmiarD/RExecOP')
    _require(errors, '.github/workflows/ci.yml', 'pip install -e ./ci-deps/rexecop')

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
    cli_text = _read('src/tecrax/cli.py')
    if EXPECTED_RELEASE_LABEL not in cli_text:
        errors.append(f'src/tecrax/cli.py:missing_current_release_label:{EXPECTED_RELEASE_LABEL}')
    if '0.2.0-alpha' in cli_text or '0.2.1-alpha' in cli_text:
        errors.append('src/tecrax/cli.py:stale_cli_status_release_label')

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
