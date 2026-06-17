"""Tecrax local-fixture CLI."""

from __future__ import annotations

import argparse
import json

from .local_fixture import build_local_fixture_review


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='tecrax')
    parser.add_argument(
        'command',
        nargs='?',
        default='status',
        choices=('status', 'fixture-review'),
        help='status prints posture; fixture-review emits a public-safe dry-run review payload.',
    )
    parser.add_argument('--service', default='demo-web', help='Local fixture service label.')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == 'fixture-review':
        print(json.dumps(build_local_fixture_review(service_name=args.service), indent=2, sort_keys=True))
        return 0

    print(
        "Tecrax 0.3.0-alpha local-fixture profile: no live infrastructure "
        "connections, credentials, or operational changes are enabled."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
