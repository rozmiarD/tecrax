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
