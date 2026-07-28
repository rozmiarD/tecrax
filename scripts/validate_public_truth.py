#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import shlex
import sys
import tomllib
import subprocess
from pathlib import Path
import re

import yaml

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
GIT_CLONE = re.compile(r'\bgit\s+clone\b')
GITHUB_VCS_FRAGMENT = re.compile(
    r'(?:git\+(?:https|ssh)://|(?:https?|ssh)://|git@)github\.com[/:]'
)
GITHUB_PIP_SOURCE = re.compile(
    r'(?P<distribution>[A-Za-z0-9][A-Za-z0-9_.-]*)\s*@\s*'
    r'git\+(?:https|ssh)://(?:git@)?github\.com[/:]'
    r'(?P<owner>[A-Za-z0-9_.-]+)/(?P<repository>[A-Za-z0-9_.-]+)(?:\.git)?'
    r'(?:@(?P<reference>.*))?'
)

REXECOP_SOURCE_SHA = '1a20584ef1fa391f125e108822a7e439879a2e0b'
SCLITE_SOURCE_SHA = '0b90c21569ea908ba7ddb468cd1ab6126342924f'
GOVENGINE_SOURCE_SHA = '0826accff407fdbc10df420803ff49cdd5818870'
SourceCoordinate = tuple[str, str, str, str, str]
EXPECTED_CI_SOURCE_COORDINATES: Counter[SourceCoordinate] = Counter(
    {
        ('test', 'Check out RExecOP', 'checkout', 'rozmiarD/RExecOP:ci-deps/rexecop', REXECOP_SOURCE_SHA): 1,
        ('package-dry-run', 'Check out RExecOP', 'checkout', 'rozmiarD/RExecOP:ci-deps/rexecop', REXECOP_SOURCE_SHA): 1,
        ('test', 'Install source dependencies', 'distribution', 'sclite-core', SCLITE_SOURCE_SHA): 1,
        ('test', 'Install source dependencies', 'distribution', 'govengine', GOVENGINE_SOURCE_SHA): 1,
        ('package-dry-run', 'Install source dependencies and build tooling', 'distribution', 'sclite-core', SCLITE_SOURCE_SHA): 1,
        ('package-dry-run', 'Install source dependencies and build tooling', 'distribution', 'govengine', GOVENGINE_SOURCE_SHA): 1,
        ('package-dry-run', 'Wheel status-only installed smoke', 'distribution', 'sclite-core', SCLITE_SOURCE_SHA): 1,
        ('package-dry-run', 'Wheel status-only installed smoke', 'distribution', 'govengine', GOVENGINE_SOURCE_SHA): 1,
        ('package-dry-run', 'Wheel install smoke', 'distribution', 'sclite-core', SCLITE_SOURCE_SHA): 1,
        ('package-dry-run', 'Wheel install smoke', 'distribution', 'govengine', GOVENGINE_SOURCE_SHA): 1,
    }
)
EXPECTED_DISTRIBUTION_REPOSITORIES = {
    'sclite-core': 'rozmiarD/SCLite',
    'govengine': 'rozmiarD/GovEngine',
}


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


def _wheel_smoke_gate_count_errors(workflow: str) -> list[str]:
    if workflow.count('python -m pip install --no-deps dist/*.whl') != 1:
        return ['ci_wheel_status_smoke_gate_count']
    if workflow.count('python -m pip install dist/*.whl') != 1:
        return ['ci_wheel_normal_install_count']
    if workflow.count('python -m pip check') != 1:
        return ['ci_wheel_normal_pip_check_count']
    return []


def _is_supported_python_pip_install(argv: list[str]) -> bool:
    if len(argv) < 4 or argv[1:4] != ['-m', 'pip', 'install']:
        return False
    executable = argv[0]
    return executable in {'python', 'python3'} or executable.endswith('/python')


def _ci_source_errors(workflow: object) -> list[str]:
    if not isinstance(workflow, dict):
        return ['ci_source_workflow_not_mapping']
    jobs = workflow.get('jobs')
    if not isinstance(jobs, dict):
        return ['ci_source_jobs_not_mapping']

    errors: list[str] = []
    observed: list[SourceCoordinate] = []
    for job_name, job in jobs.items():
        if not isinstance(job_name, str) or not isinstance(job, dict):
            errors.append('ci_source_job_not_mapping')
            continue
        steps = job.get('steps')
        if not isinstance(steps, list):
            errors.append(f'ci_source_steps_not_list:{job_name}')
            continue
        for step in steps:
            if not isinstance(step, dict):
                errors.append(f'ci_source_step_not_mapping:{job_name}')
                continue
            step_name = step.get('name')
            name = step_name if isinstance(step_name, str) else '<unnamed>'
            uses = step.get('uses')
            if isinstance(uses, str) and uses.partition('@')[0] == 'actions/checkout':
                checkout_options = step.get('with', {})
                if not isinstance(checkout_options, dict):
                    errors.append(f'ci_source_checkout_with_not_mapping:{job_name}:{name}')
                elif 'repository' in checkout_options or 'path' in checkout_options:
                    repository = checkout_options.get('repository')
                    path = checkout_options.get('path')
                    reference = checkout_options.get('ref')
                    if not all(isinstance(value, str) for value in (repository, path, reference)):
                        errors.append(f'ci_source_checkout_invalid:{job_name}:{name}')
                    else:
                        observed.append(
                            (job_name, name, 'checkout', f'{repository}:{path}', reference)
                        )
                        if not FULL_SHA.fullmatch(reference):
                            errors.append(f'ci_source_ref_not_full_sha:{job_name}:{name}')

            run = step.get('run')
            if not isinstance(run, str):
                continue
            for line in run.splitlines():
                try:
                    argv = shlex.split(line, comments=True)
                except ValueError:
                    errors.append(f'ci_source_shell_tokenization_failed:{job_name}:{name}')
                    argv = []
                if GIT_CLONE.search(line):
                    errors.append(f'ci_source_git_clone:{job_name}:{name}')

                if _is_supported_python_pip_install(argv):
                    for argument in argv[4:]:
                        source = GITHUB_PIP_SOURCE.fullmatch(argument)
                        if source is None:
                            if GITHUB_VCS_FRAGMENT.search(argument):
                                errors.append(
                                    f'ci_source_unrecognized_github_vcs:{job_name}:{name}'
                                )
                            continue
                        reference = source.group('reference')
                        distribution = source.group('distribution').lower()
                        repository = (
                            f'{source.group("owner")}/'
                            f'{source.group("repository").removesuffix(".git")}'
                        )
                        if EXPECTED_DISTRIBUTION_REPOSITORIES.get(distribution) != repository:
                            errors.append(
                                f'ci_source_distribution_repository_mismatch:{job_name}:{name}'
                            )
                        if reference is None:
                            errors.append(f'ci_source_ref_missing:{job_name}:{name}')
                            continue
                        observed.append(
                            (
                                job_name,
                                name,
                                'distribution',
                                distribution,
                                reference,
                            )
                        )
                        if not FULL_SHA.fullmatch(reference):
                            errors.append(f'ci_source_ref_not_full_sha:{job_name}:{name}')
                elif GITHUB_VCS_FRAGMENT.search(line):
                    errors.append(f'ci_source_unrecognized_github_vcs:{job_name}:{name}')

    if Counter(observed) != EXPECTED_CI_SOURCE_COORDINATES:
        errors.append('ci_source_coordinates_mismatch')
    return errors


def _ci_source_workflow_errors(workflow: str) -> list[str]:
    try:
        parsed = yaml.safe_load(workflow)
    except yaml.YAMLError:
        return ['ci_source_yaml_invalid']
    return _ci_source_errors(parsed)


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
    ci_workflow = _read('.github/workflows/ci.yml')
    errors.extend(_wheel_smoke_order_errors(ci_workflow))
    errors.extend(_wheel_smoke_gate_count_errors(ci_workflow))
    errors.extend(_ci_source_workflow_errors(ci_workflow))
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
