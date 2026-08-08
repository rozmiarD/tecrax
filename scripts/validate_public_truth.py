#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from hashlib import sha256
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
EXPECTED_GOVENGINE = 'govengine==1.0.0rc2'
EXPECTED_SCLITE = 'sclite-core==2.0.1'
EXPECTED_REXECOP = 'rexecop==1.0.0rc2'
STALE_CURRENT_DEPENDENCY_PINS = {
    'rexecop==0.3.0rc3': 'old_rexecop_production_truth',
    'rexecop==1.0.0rc1': 'old_rexecop_production_truth',
    'govengine==1.0.0rc1': 'old_govengine_production_truth',
    'sclite-core==2.0.0': 'old_sclite_production_truth',
}
DEFERRED_PUBLIC_INDEX_MARKER = (
    'RExecOp `1.0.0rc2` is not yet published; public-index resolution is '
    'mandatory before Tecrax publication.'
)
PUBLIC_DOCS = (
    'README.md',
    'PUBLIC_STATUS.md',
    'VALIDATION.md',
)
CURRENT_DEPENDENCY_TRUTH_PATHS = (
    'pyproject.toml',
    *PUBLIC_DOCS,
    'docs/mutation-entry-criteria.md',
    'docs/runbooks/chrony-ntp-server-mutation-runbook.md',
)
CURRENT_RELEASE_TRUTH_DOCS = CURRENT_DEPENDENCY_TRUTH_PATHS[1:]
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
PIP_EXECUTABLE = re.compile(r'^pip(?:\d+(?:\.\d+)*)?$')
PYTHON_EXECUTABLE = re.compile(r'^python(?:\d+(?:\.\d+)*)?$')
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
REXECOP_RANGE = re.compile(
    r'\brexecop(?:\[[^\]]+\])?\s*(?:~=|>=|<=|!=|>|<)',
    re.IGNORECASE,
)
FALSE_PUBLIC_RESOLUTION_CLAIM = re.compile(
    r'\bpublicly resolvable\b|\bnormally resolvable public-index\b|'
    r'\b(?:already|currently) (?:fully )?resolvable (?:from|on) '
    r'(?:pypi|the public index)\b',
    re.IGNORECASE,
)

REXECOP_SOURCE_SHA = '8a8609150388866a21afddca5bf773cd6ec120cd'
SCLITE_SOURCE_SHA = 'c065d7a157665351054bacc7b5e3ae12b7cc9d98'
GOVENGINE_SOURCE_SHA = 'e65ad22ec25d74bbbb4969bd614981a8ed5e47c8'
EXPECTED_WHEEL_INSTALL_SMOKE_SHA256 = (
    '3f7e376b61ec8473f1cf22f3abd9680ded2de0279de41cb25ed988aab1a0acf8'
)
EXPECTED_WHEEL_STATUS_SOURCE_SHA256 = (
    '1a17cb418e6686fbd6c557fba98ed9aa0cc25941c74b57a915b15e9b4dfa24be'
)
PipInstallArgv = tuple[str, ...]
EXPECTED_TEST_SOURCE_PIP_INSTALL_ARGV: tuple[PipInstallArgv, ...] = (
    ('python', '-m', 'pip', 'install', '--upgrade', 'pip'),
    (
        'python',
        '-m',
        'pip',
        'install',
        'sclite-core @ '
        f'git+https://github.com/rozmiarD/SCLite.git@{SCLITE_SOURCE_SHA}',
    ),
    (
        'python',
        '-m',
        'pip',
        'install',
        'govengine @ '
        f'git+https://github.com/rozmiarD/GovEngine.git@{GOVENGINE_SOURCE_SHA}',
    ),
    ('python', '-m', 'pip', 'install', '-e', './ci-deps/rexecop'),
    (
        'python',
        '-m',
        'pip',
        'install',
        'pytest>=8,<9',
        'ruff>=0.14,<1',
        'mypy>=1.18,<2',
    ),
    ('python', '-m', 'pip', 'install', '-e', '.'),
)
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


def _dependency_truth_drift_errors() -> list[str]:
    errors: list[str] = []
    for path in CURRENT_DEPENDENCY_TRUTH_PATHS:
        text = _read(path)
        normalized_text = ' '.join(text.split())
        for stale_pin, reason in STALE_CURRENT_DEPENDENCY_PINS.items():
            if stale_pin in text:
                errors.append(f'{path}:{reason}:{stale_pin}')
        if REXECOP_RANGE.search(text):
            errors.append(f'{path}:ranged_rexecop_production_truth')
        if FALSE_PUBLIC_RESOLUTION_CLAIM.search(normalized_text):
            errors.append(f'{path}:false_public_index_resolution_claim')
        if (
            path in CURRENT_RELEASE_TRUTH_DOCS
            and DEFERRED_PUBLIC_INDEX_MARKER not in normalized_text
        ):
            errors.append(f'{path}:missing_deferred_public_index_gate')
    return errors


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
    normal_install = (
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install --force-reinstall'
    )
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
    if workflow.count(
        '/tmp/tecrax-wheel-status/bin/python -m pip install --no-deps dist/*.whl'
    ) != 1:
        return ['ci_wheel_status_smoke_gate_count']
    for distribution, repository, source_sha in (
        ('govengine', 'GovEngine', GOVENGINE_SOURCE_SHA),
        ('sclite-core', 'SCLite', SCLITE_SOURCE_SHA),
    ):
        install = (
            '/tmp/tecrax-wheel-smoke/bin/python -m pip install '
            f'--force-reinstall "{distribution} @ '
            f'git+https://github.com/rozmiarD/{repository}.git@{source_sha}"'
        )
        if workflow.count(install) != 1:
            return [f'ci_wheel_normal_{distribution}_install_count']
    if workflow.count(
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install ./ci-deps/rexecop'
    ) != 1:
        return ['ci_wheel_normal_rexecop_install_count']
    if workflow.count(
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install --no-deps dist/*.whl'
    ) != 1:
        return ['ci_wheel_normal_tecrax_install_count']
    if workflow.count('python -m pip check') != 1:
        return ['ci_wheel_normal_pip_check_count']
    return []


def _wheel_installed_graph_errors(workflow: str) -> list[str]:
    try:
        parsed = yaml.safe_load(workflow)
    except yaml.YAMLError:
        return ['ci_wheel_installed_graph_yaml_invalid']
    if not isinstance(parsed, dict):
        return ['ci_wheel_installed_graph_step_count']
    jobs = parsed.get('jobs')
    package_job = jobs.get('package-dry-run') if isinstance(jobs, dict) else None
    steps = package_job.get('steps') if isinstance(package_job, dict) else None
    if not isinstance(steps, list):
        return ['ci_wheel_installed_graph_step_count']
    matches = [
        step.get('run')
        for step in steps
        if isinstance(step, dict) and step.get('name') == 'Wheel install smoke'
    ]
    if len(matches) != 1 or not isinstance(matches[0], str):
        return ['ci_wheel_installed_graph_step_count']
    step_run = matches[0]
    if sha256(step_run.encode('utf-8')).hexdigest() != EXPECTED_WHEEL_INSTALL_SMOKE_SHA256:
        return ['ci_wheel_installed_graph_fingerprint_mismatch']

    active_lines = tuple(
        line.rstrip()
        for line in step_run.splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    )
    expected_lines = (
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install --force-reinstall '
        '"govengine @ git+https://github.com/rozmiarD/GovEngine.git@'
        f'{GOVENGINE_SOURCE_SHA}"',
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install --force-reinstall '
        '"sclite-core @ git+https://github.com/rozmiarD/SCLite.git@'
        f'{SCLITE_SOURCE_SHA}"',
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install ./ci-deps/rexecop',
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install --no-deps dist/*.whl',
        '  cd /tmp/tecrax-wheel-smoke-empty',
        '  env -u PYTHONPATH -u PYTHONHOME '
        '/tmp/tecrax-wheel-smoke/bin/python -m pip check',
        "  env -u PYTHONPATH -u PYTHONHOME /tmp/tecrax-wheel-smoke/bin/python - <<'PY'",
        'PY',
    )
    if any(active_lines.count(line) != 1 for line in expected_lines):
        return ['ci_wheel_installed_graph_gate_mismatch']

    version_block = (
        'expected_versions = {',
        "    'tecrax': '0.4.0rc3',",
        "    'rexecop': '1.0.0rc2',",
        "    'govengine': '1.0.0rc2',",
        "    'sclite-core': '2.0.1',",
        '}',
        'for distribution_name, expected_version in expected_versions.items():',
        '    assert version(distribution_name) == expected_version',
    )
    origin_block = (
        'origins = {',
        "    'tecrax': Path(tecrax.__file__).resolve(),",
        "    'rexecop': Path(rexecop.__file__).resolve(),",
        "    'govengine': Path(govengine.__file__).resolve(),",
        "    'sclite': Path(sclite.__file__).resolve(),",
        '}',
        'for origin in origins.values():',
        '    assert origin.is_relative_to(Path(sys.prefix).resolve())',
        "    assert 'site-packages' in origin.parts",
    )

    def has_block(block: tuple[str, ...]) -> bool:
        width = len(block)
        return any(
            active_lines[index : index + width] == block
            for index in range(len(active_lines) - width + 1)
        )

    if not has_block(version_block) or not has_block(origin_block):
        return ['ci_wheel_installed_graph_python_assertion_mismatch']

    active_step = '\n'.join(active_lines)
    source_provenance = (
        f".strip() == '{REXECOP_SOURCE_SHA}'",
        f"('govengine', '{GOVENGINE_SOURCE_SHA}')",
        f"('sclite-core', '{SCLITE_SOURCE_SHA}')",
        "direct_url['vcs_info']['commit_id'] == expected_sha",
        "Path(os.environ['REXECOP_SOURCE_ROOT']).resolve()",
    )
    if any(active_step.count(fragment) != 1 for fragment in source_provenance):
        return ['ci_wheel_installed_graph_source_provenance_mismatch']

    forbidden = (
        'expected_conflict',
        'pip_check_output',
        'pip_check_status',
        'set +e',
    )
    if any(fragment in active_step for fragment in forbidden):
        return ['ci_wheel_installed_graph_forbidden_waiver']
    positions = [active_lines.index(line) for line in expected_lines]
    if positions != sorted(positions):
        return ['ci_wheel_installed_graph_gate_order']
    return []


def _wheel_status_source_provenance_errors(workflow: str) -> list[str]:
    try:
        parsed = yaml.safe_load(workflow)
    except yaml.YAMLError:
        return ['ci_wheel_status_source_provenance_yaml_invalid']
    if not isinstance(parsed, dict):
        return ['ci_wheel_status_source_provenance_step_count']
    jobs = parsed.get('jobs')
    package_job = jobs.get('package-dry-run') if isinstance(jobs, dict) else None
    steps = package_job.get('steps') if isinstance(package_job, dict) else None
    if not isinstance(steps, list):
        return ['ci_wheel_status_source_provenance_step_count']
    matches = [
        step.get('run')
        for step in steps
        if isinstance(step, dict)
        and step.get('name') == 'Wheel status-only installed smoke'
    ]
    if len(matches) != 1 or not isinstance(matches[0], str):
        return ['ci_wheel_status_source_provenance_step_count']
    step_run = matches[0]
    if sha256(step_run.encode('utf-8')).hexdigest() != EXPECTED_WHEEL_STATUS_SOURCE_SHA256:
        return ['ci_wheel_status_source_provenance_fingerprint_mismatch']

    active_lines = tuple(
        line.rstrip()
        for line in step_run.splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    )
    install_lines = (
        '/tmp/tecrax-wheel-status/bin/python -m pip install --force-reinstall '
        f'"govengine @ git+https://github.com/rozmiarD/GovEngine.git@{GOVENGINE_SOURCE_SHA}"',
        '/tmp/tecrax-wheel-status/bin/python -m pip install --force-reinstall '
        f'"sclite-core @ git+https://github.com/rozmiarD/SCLite.git@{SCLITE_SOURCE_SHA}"',
        '/tmp/tecrax-wheel-status/bin/python -m pip install -e ./ci-deps/rexecop',
    )
    if any(active_lines.count(line) != 1 for line in install_lines):
        return ['ci_wheel_status_source_install_mismatch']
    positions = [active_lines.index(line) for line in install_lines]
    if positions != sorted(positions):
        return ['ci_wheel_status_source_install_order']

    active_step = '\n'.join(active_lines)
    expected = (
        f".strip() == '{REXECOP_SOURCE_SHA}'",
        "assert version('rexecop') == '1.0.0rc2'",
        "Path(rexecop.__file__).resolve().is_relative_to(rexecop_root / 'src')",
        f"('govengine', '{GOVENGINE_SOURCE_SHA}')",
        f"('sclite-core', '{SCLITE_SOURCE_SHA}')",
        "direct_url['vcs_info']['commit_id'] == expected_sha",
        "assert version('tecrax') == '0.4.0rc3'",
        "assert 'site-packages' in Path(tecrax.__file__).resolve().parts",
    )
    if any(active_step.count(fragment) != 1 for fragment in expected):
        return ['ci_wheel_status_source_provenance_mismatch']
    return []


def _wheel_source_function_errors(workflow: str) -> list[str]:
    marker = '      - name: Source-pinned installed plugin posture smoke'
    if workflow.count(marker) != 1:
        return ['ci_wheel_source_function_step_count']
    start = workflow.index(marker)
    end = workflow.index('      - name: Wheel install smoke', start)
    step = workflow[start:end]
    expected = (
        'from govengine.typed_execution_governed_admission import '
        'TYPED_EXECUTION_GOVERNED_ADMISSION_V02_SCHEMA_VERSION',
        "assert 'site-packages' in Path(tecrax.__file__).as_posix()",
        "'backend': 'tecrax_chrony_ntp'",
        "'execution_posture': 'fixture_only'",
        "assert descriptor['live_backend_posture'] == 'fixture_only'",
        "assert descriptor['egress_class'] == 'no_network'",
    )
    if any(step.count(fragment) != 1 for fragment in expected):
        return ['ci_wheel_source_function_gate_mismatch']
    return []


def _test_source_install_errors(workflow: str) -> list[str]:
    marker = '      - name: Install source dependencies\n'
    provenance = '      - name: Verify source candidate provenance\n'
    if workflow.count(marker) != 1 or workflow.count(provenance) != 1:
        return ['ci_test_source_install_step_count']
    start = workflow.index(marker)
    end = workflow.index(provenance, start)
    step = workflow[start:end]
    observed: list[PipInstallArgv] = []
    for line in step.splitlines():
        try:
            argv = shlex.split(line, comments=True)
        except ValueError:
            return ['ci_test_source_install_tokenization_failed']
        if _is_pip_install_invocation(argv):
            observed.append(tuple(argv))
    if tuple(observed) != EXPECTED_TEST_SOURCE_PIP_INSTALL_ARGV:
        return ['ci_test_source_install_argv_mismatch']
    return []


def _test_source_provenance_errors(workflow: str) -> list[str]:
    marker = '      - name: Verify source candidate provenance'
    end_marker = '      - name: Validate public truth'
    if workflow.count(marker) != 1 or workflow.count(end_marker) != 1:
        return ['ci_test_source_provenance_step_count']
    start = workflow.index(marker)
    end = workflow.index(end_marker, start)
    step = workflow[start:end]
    expected = (
        f".strip() == '{REXECOP_SOURCE_SHA}'",
        "assert version('rexecop') == '1.0.0rc2'",
        "Path(rexecop.__file__).resolve().is_relative_to(rexecop_root / 'src')",
        f"govengine_direct_url['vcs_info']['commit_id'] == '{GOVENGINE_SOURCE_SHA}'",
        f"sclite_direct_url['vcs_info']['commit_id'] == '{SCLITE_SOURCE_SHA}'",
        "TYPED_EXECUTION_GOVERNED_ADMISSION_V02_SCHEMA_VERSION == 'v0.2'",
        "assert version('tecrax') == '0.4.0rc3'",
        "Path(tecrax.__file__).resolve().is_relative_to(Path('src').resolve())",
    )
    if any(step.count(fragment) != 1 for fragment in expected):
        return ['ci_test_source_provenance_mismatch']
    return []


def _is_canonical_python_pip_install(argv: list[str]) -> bool:
    if len(argv) < 4 or argv[1:4] != ['-m', 'pip', 'install']:
        return False
    executable = argv[0]
    return executable in {'python', 'python3'} or executable.endswith('/python')


def _is_pip_install_invocation(argv: list[str]) -> bool:
    if not argv:
        return False
    executable = argv[0].rsplit('/', 1)[-1]
    if PIP_EXECUTABLE.fullmatch(executable):
        subcommand_tokens = argv[1:]
    elif PYTHON_EXECUTABLE.fullmatch(executable) and argv[1:3] == ['-m', 'pip']:
        subcommand_tokens = argv[3:]
    else:
        return False
    for token in subcommand_tokens:
        if token == 'install':
            return True
        if not token.startswith('-'):
            return False
    return False


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

                if _is_canonical_python_pip_install(argv):
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
    errors.extend(_dependency_truth_drift_errors())
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
    _require(
        errors,
        '.github/workflows/ci.yml',
        '/tmp/tecrax-wheel-smoke/bin/python -m pip install --force-reinstall',
    )
    _require(errors, '.github/workflows/ci.yml', 'python -m pip check')
    _require(errors, '.github/workflows/ci.yml', 'Wheel status-only installed smoke')
    _require(errors, '.github/workflows/ci.yml', 'python -m pip install --no-deps dist/*.whl')
    _require(errors, '.github/workflows/ci.yml', 'env -u PYTHONPATH -u PYTHONHOME')
    ci_workflow = _read('.github/workflows/ci.yml')
    errors.extend(_wheel_smoke_order_errors(ci_workflow))
    errors.extend(_wheel_smoke_gate_count_errors(ci_workflow))
    errors.extend(_wheel_installed_graph_errors(ci_workflow))
    errors.extend(_wheel_status_source_provenance_errors(ci_workflow))
    errors.extend(_wheel_source_function_errors(ci_workflow))
    errors.extend(_test_source_install_errors(ci_workflow))
    errors.extend(_test_source_provenance_errors(ci_workflow))
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
