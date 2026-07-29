from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _validator():
    path = ROOT / 'scripts' / 'validate_public_truth.py'
    spec = importlib.util.spec_from_file_location('tecrax_public_truth', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _workflow() -> str:
    return (ROOT / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')


def test_ci_source_coordinates_are_the_reviewed_immutable_snapshots() -> None:
    validator = _validator()

    assert sum(validator.EXPECTED_CI_SOURCE_COORDINATES.values()) == 10
    assert validator._ci_source_workflow_errors(_workflow()) == []


def test_ci_source_test_install_is_ordered_and_resolver_safe() -> None:
    validator = _validator()

    assert validator._test_source_install_errors(_workflow()) == []


def test_ci_source_test_install_argv_contract_is_exact() -> None:
    validator = _validator()

    assert validator.EXPECTED_TEST_SOURCE_PIP_INSTALL_ARGV == (
        ('python', '-m', 'pip', 'install', '--upgrade', 'pip'),
        (
            'python',
            '-m',
            'pip',
            'install',
            'sclite-core @ '
            f'git+https://github.com/rozmiarD/SCLite.git@{validator.SCLITE_SOURCE_SHA}',
        ),
        (
            'python',
            '-m',
            'pip',
            'install',
            'govengine @ '
            f'git+https://github.com/rozmiarD/GovEngine.git@{validator.GOVENGINE_SOURCE_SHA}',
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
        ('python', '-m', 'pip', 'install', '--no-deps', '-e', '.'),
    )


def test_ci_source_test_provenance_is_exact() -> None:
    validator = _validator()

    assert validator._test_source_provenance_errors(_workflow()) == []


@pytest.mark.parametrize(
    'mutation',
    (
        lambda workflow: workflow.replace(
            'python -m pip install --no-deps -e .',
            'python -m pip install -e .',
            1,
        ),
        lambda workflow: workflow.replace(
            'python -m pip install --no-deps -e .',
            "python -m pip install -e '.[dev]'",
            1,
        ),
        lambda workflow: workflow.replace(
            '          python -m pip install -e ./ci-deps/rexecop\n'
            '          python -m pip install "pytest>=8,<9" "ruff>=0.14,<1" "mypy>=1.18,<2"\n',
            '          python -m pip install "pytest>=8,<9" "ruff>=0.14,<1" "mypy>=1.18,<2"\n'
            '          python -m pip install -e ./ci-deps/rexecop\n',
            1,
        ),
    ),
    ids=('resolver-aware-editable', 'dev-extra-resolver', 'wrong-order'),
)
def test_ci_source_test_install_validator_fails_closed(mutation: Mutation) -> None:
    validator = _validator()

    assert validator._test_source_install_errors(mutation(_workflow())) != []


@pytest.mark.parametrize(
    'extra_install',
    (
        'python -m pip install -e ./',
        'python -m pip install .',
        'python -m pip install --editable .[dev]',
        'pip install .',
        'pip3 install .',
        '/opt/hostedtoolcache/Python/3.12.0/x64/bin/pip install .',
        'python -m pip --disable-pip-version-check install .',
    ),
    ids=(
        'extra-editable-slash',
        'extra-dot',
        'extra-dev-editable',
        'direct-pip',
        'direct-pip3',
        'path-pip',
        'python-pip-global-option',
    ),
)
def test_ci_source_test_install_validator_rejects_extra_install(
    extra_install: str,
) -> None:
    validator = _validator()
    workflow = _workflow().replace(
        '          python -m pip install --no-deps -e .\n',
        '          python -m pip install --no-deps -e .\n'
        f'          {extra_install}\n',
        1,
    )

    assert validator._test_source_install_errors(workflow) == [
        'ci_test_source_install_argv_mismatch'
    ]


def test_ci_source_installer_classifier_rejects_pip_prefixed_words() -> None:
    validator = _validator()

    assert validator._is_pip_install_invocation(['pipeline', 'install', '.']) is False


@pytest.mark.parametrize(
    'old',
    (
        "assert version('rexecop') == '1.0.0rc1'",
        "govengine_direct_url['vcs_info']['commit_id']",
        "TYPED_EXECUTION_GOVERNED_ADMISSION_V02_SCHEMA_VERSION == 'v0.2'",
        "Path(tecrax.__file__).resolve().is_relative_to(Path('src').resolve())",
    ),
)
def test_ci_source_test_provenance_validator_fails_closed(old: str) -> None:
    validator = _validator()

    assert validator._test_source_provenance_errors(
        _workflow().replace(old, 'removed-provenance-proof', 1)
    ) != []


def test_ci_installed_graph_records_only_the_known_production_pin_conflict() -> None:
    validator = _validator()

    assert validator._wheel_installed_graph_errors(_workflow()) == []


def test_ci_installed_source_function_binds_exact_plugin_posture() -> None:
    validator = _validator()

    assert validator._wheel_source_function_errors(_workflow()) == []


@pytest.mark.parametrize(
    'old',
    (
        'Source-pinned installed plugin posture smoke',
        "assert 'site-packages' in Path(tecrax.__file__).as_posix()",
        "'backend': 'tecrax_chrony_ntp'",
        "assert descriptor['egress_class'] == 'no_network'",
    ),
)
def test_ci_installed_source_function_validator_fails_closed(old: str) -> None:
    validator = _validator()

    assert validator._wheel_source_function_errors(
        _workflow().replace(old, 'removed-source-function-proof', 1)
    ) != []


@pytest.mark.parametrize(
    'mutation',
    (
        lambda workflow: workflow.replace(' dist/*.whl --no-deps', ' dist/*.whl', 1),
        lambda workflow: workflow.replace(
            'if [ "$pip_check_status" -eq 0 ]; then',
            'if [ "$pip_check_status" -eq 1 ]; then',
            1,
        ),
        lambda workflow: workflow.replace(
            'rexecop==0.3.0rc3',
            'rexecop>=0.3.0rc3',
            1,
        ),
        lambda workflow: workflow.replace(
            'if [ "$pip_check_output" != "$expected_conflict" ]; then',
            'if [ -z "$pip_check_output" ]; then',
            1,
        ),
    ),
    ids=(
        'resolver-substitution',
        'unexpected-success-accepted',
        'wrong-conflict',
        'additional-conflicts-accepted',
    ),
)
def test_ci_installed_graph_validator_fails_closed(mutation: Mutation) -> None:
    validator = _validator()

    assert validator._wheel_installed_graph_errors(mutation(_workflow())) != []


Mutation = Callable[[str], str]


@pytest.mark.parametrize(
    ('mutation', 'expected_error'),
    (
        (
            lambda workflow: workflow.replace(
                f'@{_validator().SCLITE_SOURCE_SHA}', '', 1
            ),
            'ci_source_ref_missing:test:Install source dependencies',
        ),
        (
            lambda workflow: workflow.replace(
                _validator().SCLITE_SOURCE_SHA, 'main', 1
            ),
            'ci_source_ref_not_full_sha:test:Install source dependencies',
        ),
        (
            lambda workflow: workflow.replace(
                _validator().SCLITE_SOURCE_SHA, 'v2.0.0', 1
            ),
            'ci_source_ref_not_full_sha:test:Install source dependencies',
        ),
        (
            lambda workflow: workflow.replace(
                _validator().SCLITE_SOURCE_SHA, '${{ github.sha }}', 1
            ),
            'ci_source_ref_not_full_sha:test:Install source dependencies',
        ),
        (
            lambda workflow: workflow.replace(
                _validator().SCLITE_SOURCE_SHA, '0b90c21', 1
            ),
            'ci_source_ref_not_full_sha:test:Install source dependencies',
        ),
        (
            lambda workflow: workflow.replace(
                _validator().SCLITE_SOURCE_SHA,
                '0000000000000000000000000000000000000000',
                1,
            ),
            'ci_source_coordinates_mismatch',
        ),
        (
            lambda workflow: workflow.replace(
                f'          python -m pip install "sclite-core @ '
                f'git+https://github.com/rozmiarD/SCLite.git@{_validator().SCLITE_SOURCE_SHA}"\n',
                f'          python -m pip install "sclite-core @ '
                f'git+https://github.com/rozmiarD/SCLite.git@{_validator().SCLITE_SOURCE_SHA}"\n'
                f'          python -m pip install "sclite-core @ '
                f'git+https://github.com/rozmiarD/SCLite.git@{_validator().SCLITE_SOURCE_SHA}"\n',
                1,
            ),
            'ci_source_coordinates_mismatch',
        ),
        (
            lambda workflow: workflow.replace('sclite-core @ git+', 'unexpected-core @ git+', 1),
            'ci_source_coordinates_mismatch',
        ),
        (
            lambda workflow: workflow.replace('  test:\n', '  renamed-test:\n', 1),
            'ci_source_coordinates_mismatch',
        ),
        (
            lambda workflow: workflow.replace(
                '- name: Install source dependencies\n', '- name: Unexpected source step\n', 1
            ),
            'ci_source_coordinates_mismatch',
        ),
        (
            lambda workflow: workflow.replace('github.com/rozmiarD/SCLite.git', 'github.com/other/SCLite.git', 1),
            'ci_source_distribution_repository_mismatch:test:Install source dependencies',
        ),
        (
            lambda workflow: workflow.replace('path: ci-deps/rexecop', 'path: ci-deps/other', 1),
            'ci_source_coordinates_mismatch',
        ),
        (
            lambda workflow: workflow.replace(
                '          python -m pip install -e ./ci-deps/rexecop\n',
                '          python -m pip install -e ./ci-deps/rexecop\n'
                '          git clone https://github.com/rozmiarD/RExecOP.git ci-deps/other\n',
                1,
            ),
            'ci_source_git_clone:test:Install source dependencies',
        ),
        (
            lambda workflow: workflow.replace(
                'sclite-core @ git+https://github.com/rozmiarD/SCLite.git',
                'git+https://github.com/rozmiarD/SCLite.git',
                1,
            ),
            'ci_source_unrecognized_github_vcs:test:Install source dependencies',
        ),
    ),
    ids=(
        'missing-reference',
        'main-reference',
        'tag-reference',
        'expression-reference',
        'short-reference',
        'wrong-sha',
        'duplicate-coordinate',
        'unexpected-distribution',
        'wrong-job',
        'wrong-step',
        'wrong-repository',
        'wrong-path',
        'leftover-git-clone',
        'unrecognized-github-vcs',
    ),
)
def test_ci_source_validator_rejects_every_source_pin_regression(
    mutation: Mutation,
    expected_error: str,
) -> None:
    validator = _validator()

    assert expected_error in validator._ci_source_workflow_errors(mutation(_workflow()))


def test_ci_source_validator_rejects_invalid_yaml() -> None:
    validator = _validator()

    assert validator._ci_source_workflow_errors('jobs: [') == ['ci_source_yaml_invalid']


@pytest.mark.parametrize(
    'line',
    (
        '          echo "sclite-core @ git+https://github.com/rozmiarD/SCLite.git@0b90c21569ea908ba7ddb468cd1ab6126342924f"',
        '          # sclite-core @ git+https://github.com/rozmiarD/SCLite.git@0b90c21569ea908ba7ddb468cd1ab6126342924f',
        '          python -c "print(\'sclite-core @ git+https://github.com/rozmiarD/SCLite.git@0b90c21569ea908ba7ddb468cd1ab6126342924f\')"',
    ),
    ids=('echo', 'comment', 'python-c'),
)
def test_ci_source_validator_rejects_non_executed_pep508_text(line: str) -> None:
    validator = _validator()
    workflow = _workflow().replace(
        '          python -m pip install -e ./ci-deps/rexecop\n',
        f'          python -m pip install -e ./ci-deps/rexecop\n{line}\n',
        1,
    )

    errors = validator._ci_source_workflow_errors(workflow)

    assert 'ci_source_unrecognized_github_vcs:test:Install source dependencies' in errors
