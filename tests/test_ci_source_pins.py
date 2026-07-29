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


EXACT_VERSION_ASSERTION_BLOCK = (
    '          expected_versions = {\n'
    "              'tecrax': '0.4.0rc3',\n"
    "              'rexecop': '1.0.0rc1',\n"
    "              'govengine': '1.0.0rc1',\n"
    "              'sclite-core': '2.0.0',\n"
    '          }\n'
    '          for distribution_name, expected_version in expected_versions.items():\n'
    '              assert version(distribution_name) == expected_version\n'
)
EXACT_ORIGIN_ASSERTION_BLOCK = (
    '          for origin in origins.values():\n'
    '              assert origin.is_relative_to(Path(sys.prefix).resolve())\n'
    "              assert 'site-packages' in origin.parts\n"
)
STATUS_GOVENGINE_INSTALL = (
    '          /tmp/tecrax-wheel-status/bin/python -m pip install '
    '--force-reinstall "govengine @ git+https://github.com/rozmiarD/'
    'GovEngine.git@9a78650a0e39524dcbf07d98f5fb71f89093fc66"\n'
)
STATUS_SCLITE_INSTALL = (
    '          /tmp/tecrax-wheel-status/bin/python -m pip install '
    '--force-reinstall "sclite-core @ git+https://github.com/rozmiarD/'
    'SCLite.git@0b90c21569ea908ba7ddb468cd1ab6126342924f"\n'
)
STATUS_REXECOP_INSTALL = (
    '          /tmp/tecrax-wheel-status/bin/python -m pip install '
    '-e ./ci-deps/rexecop\n'
)


def _replace_once(workflow: str, old: str, new: str) -> str:
    assert workflow.count(old) == 1
    return workflow.replace(old, new, 1)


def _comment_block(workflow: str, block: str) -> str:
    commented = '\n'.join(
        f'{line[: len(line) - len(line.lstrip())]}# {line.lstrip()}'
        for line in block.rstrip('\n').splitlines()
    )
    return _replace_once(workflow, block, f'{commented}\n')


def _insert_exit_before_normal_pip_check(workflow: str) -> str:
    pip_check = (
        '            env -u PYTHONPATH -u PYTHONHOME '
        '/tmp/tecrax-wheel-smoke/bin/python -m pip check\n'
    )
    return _replace_once(workflow, pip_check, f'            exit 0\n{pip_check}')


def _insert_python_early_success(workflow: str) -> str:
    assertion_start = '          expected_versions = {\n'
    return _replace_once(
        workflow,
        assertion_start,
        f'          raise SystemExit(0)\n{assertion_start}',
    )


def test_ci_source_coordinates_are_the_reviewed_immutable_snapshots() -> None:
    validator = _validator()

    assert sum(validator.EXPECTED_CI_SOURCE_COORDINATES.values()) == 8
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
        ('python', '-m', 'pip', 'install', '-e', '.'),
    )


def test_ci_source_test_provenance_is_exact() -> None:
    validator = _validator()

    assert validator._test_source_provenance_errors(_workflow()) == []


@pytest.mark.parametrize(
    'mutation',
    (
        lambda workflow: workflow.replace(
            'python -m pip install -e .',
            'python -m pip install --no-deps -e .',
            1,
        ),
        lambda workflow: workflow.replace(
            'python -m pip install -e .',
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
    ids=('no-deps-editable', 'dev-extra-resolver', 'wrong-order'),
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
        '          python -m pip install -e .\n',
        '          python -m pip install -e .\n'
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
        "sclite_direct_url['vcs_info']['commit_id']",
        "TYPED_EXECUTION_GOVERNED_ADMISSION_V02_SCHEMA_VERSION == 'v0.2'",
        "Path(tecrax.__file__).resolve().is_relative_to(Path('src').resolve())",
    ),
)
def test_ci_source_test_provenance_validator_fails_closed(old: str) -> None:
    validator = _validator()

    assert validator._test_source_provenance_errors(
        _workflow().replace(old, 'removed-provenance-proof', 1)
    ) != []


def test_ci_installed_graph_requires_a_clean_public_dependency_graph() -> None:
    validator = _validator()

    assert validator.EXPECTED_WHEEL_INSTALL_SMOKE_SHA256 == (
        '80176013e2c86d1f1c8bbd4d4dc963b4bc3a1166909dfe317b363af39e01edf7'
    )
    assert validator._wheel_installed_graph_errors(_workflow()) == []


def test_ci_installed_source_function_binds_exact_plugin_posture() -> None:
    validator = _validator()

    assert validator._wheel_source_function_errors(_workflow()) == []


def test_ci_status_smoke_binds_exact_source_provenance() -> None:
    validator = _validator()

    assert validator.EXPECTED_WHEEL_STATUS_SOURCE_SHA256 == (
        '3d7a33f2126d7e318fa2d06bd564c7335329154a4678a1679b2fd77be3d881df'
    )
    assert validator._wheel_status_source_provenance_errors(_workflow()) == []


@pytest.mark.parametrize(
    'mutation',
    (
        lambda workflow: _replace_once(
            workflow,
            STATUS_GOVENGINE_INSTALL + STATUS_SCLITE_INSTALL,
            STATUS_SCLITE_INSTALL + STATUS_GOVENGINE_INSTALL,
        ),
        lambda workflow: _replace_once(workflow, STATUS_SCLITE_INSTALL, ''),
        lambda workflow: _replace_once(workflow, STATUS_REXECOP_INSTALL, ''),
    ),
    ids=('sclite-before-govengine', 'missing-final-sclite', 'missing-rexecop'),
)
def test_ci_status_source_install_order_fails_closed(mutation: Mutation) -> None:
    validator = _validator()

    assert validator._wheel_status_source_provenance_errors(
        mutation(_workflow())
    ) != []


@pytest.mark.parametrize(
    'old',
    (
        f".strip() == '{_validator().REXECOP_SOURCE_SHA}'",
        f"('govengine', '{_validator().GOVENGINE_SOURCE_SHA}')",
        f"('sclite-core', '{_validator().SCLITE_SOURCE_SHA}')",
        "direct_url['vcs_info']['commit_id'] == expected_sha",
        "assert 'site-packages' in Path(tecrax.__file__).resolve().parts",
    ),
)
def test_ci_status_source_provenance_validator_fails_closed(old: str) -> None:
    validator = _validator()
    workflow = _workflow()
    status_start = workflow.index('      - name: Wheel status-only installed smoke')
    mutated = workflow[:status_start] + workflow[status_start:].replace(
        old, 'removed-status-source-proof', 1
    )

    assert validator._wheel_status_source_provenance_errors(
        mutated
    ) != []


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
        lambda workflow: workflow.replace(
            '/tmp/tecrax-wheel-smoke/bin/python -m pip install dist/*.whl',
            '/tmp/tecrax-wheel-smoke/bin/python -m pip install dist/*.whl --no-deps',
            1,
        ),
        lambda workflow: workflow.replace(
            'env -u PYTHONPATH -u PYTHONHOME /tmp/tecrax-wheel-smoke/bin/python -m pip check',
            'set +e\n            pip_check_output="$(/tmp/tecrax-wheel-smoke/bin/python -m pip check 2>&1)"\n            expected_conflict="accepted"',
            1,
        ),
        lambda workflow: workflow.replace(
            "'rexecop': '1.0.0rc1'",
            "'rexecop': '0.3.0rc3'",
            1,
        ),
        lambda workflow: workflow.replace(
            "assert 'site-packages' in origin.parts",
            'removed-origin-proof',
            1,
        ),
        lambda workflow: workflow.replace(
            'env -u PYTHONPATH -u PYTHONHOME /tmp/tecrax-wheel-smoke/bin/python -m pip check\n',
            '',
            1,
        ),
        lambda workflow: _replace_once(
            workflow,
            '            env -u PYTHONPATH -u PYTHONHOME '
            '/tmp/tecrax-wheel-smoke/bin/python -m pip check\n',
            '            # env -u PYTHONPATH -u PYTHONHOME '
            '/tmp/tecrax-wheel-smoke/bin/python -m pip check\n',
        ),
        lambda workflow: _replace_once(
            workflow, EXACT_VERSION_ASSERTION_BLOCK, ''
        ),
        lambda workflow: _comment_block(
            workflow, EXACT_VERSION_ASSERTION_BLOCK
        ),
        lambda workflow: _comment_block(
            workflow, EXACT_ORIGIN_ASSERTION_BLOCK
        ),
        _insert_exit_before_normal_pip_check,
        _insert_python_early_success,
    ),
    ids=(
        'normal-wheel-no-deps',
        'expected-conflict-waiver',
        'wrong-installed-version',
        'missing-origin-proof',
        'missing-pip-check',
        'commented-pip-check',
        'removed-version-loop',
        'commented-version-loop',
        'commented-origin-assertions',
        'early-shell-success',
        'early-python-success',
    ),
)
def test_ci_installed_graph_validator_fails_closed(mutation: Mutation) -> None:
    validator = _validator()

    assert validator._wheel_installed_graph_errors(mutation(_workflow())) != []


def test_public_truth_collect_errors_rejects_early_shell_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = _validator()
    workflow = _insert_exit_before_normal_pip_check(_workflow())
    original_read = validator._read
    monkeypatch.setattr(
        validator,
        '_read',
        lambda path: workflow if path == '.github/workflows/ci.yml' else original_read(path),
    )

    assert 'ci_wheel_installed_graph_fingerprint_mismatch' in validator.collect_errors()


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
