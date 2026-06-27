"""Tecrax local-fixture CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .local_fixture import build_local_fixture_review
from .reactions import build_monitoring_host_observation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tecrax")
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=("status", "fixture-review", "reaction-observation"),
        help="status prints posture; fixture-review emits a public-safe dry-run review payload.",
    )
    parser.add_argument(
        "--service", default="demo-web", help="Local fixture service label."
    )
    parser.add_argument("--input", type=Path, help="Bounded diagnosis JSON input.")
    parser.add_argument("--operation", help="Source RExecOp operation id.")
    parser.add_argument("--target", help="Source environment target id.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "fixture-review":
        print(
            json.dumps(
                build_local_fixture_review(service_name=args.service),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "reaction-observation":
        if args.input is None or not args.operation or not args.target:
            parser = _parser()
            parser.error("reaction-observation requires --input --operation --target")
        diagnosis = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(diagnosis, dict):
            raise SystemExit("diagnosis input must be a JSON object")
        print(
            json.dumps(
                build_monitoring_host_observation(
                    operation_id=args.operation,
                    target_id=args.target,
                    diagnosis=diagnosis,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(
        "Tecrax 0.3.6-alpha read-only profile: operator-configured live access "
        "runs through RExecOp; infrastructure mutation remains unavailable."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
