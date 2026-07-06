#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tecrax.zabbix_glpi_events import (
    ZabbixProblemQuery,
    alert_event_to_mapping,
    fetch_zabbix_problems,
    zabbix_problems_to_alert_events,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect bounded Zabbix active problems as normalized GLPI alert events."
    )
    parser.add_argument("--api-url", required=True, help="Zabbix API URL ending with api_jsonrpc.php.")
    parser.add_argument(
        "--token-env",
        default="ZABBIX_API_TOKEN",
        help="Environment variable containing the Zabbix API token.",
    )
    parser.add_argument(
        "--min-severity",
        type=int,
        default=2,
        choices=range(0, 6),
        help="Minimum Zabbix severity to collect. Default: 2 (Warning).",
    )
    parser.add_argument("--limit", type=int, default=50, help="Maximum active problems to collect.")
    parser.add_argument(
        "--include-suppressed",
        action="store_true",
        help="Include suppressed Zabbix problems. Default: false.",
    )
    parser.add_argument("--source-url-base", default="", help="Optional Zabbix web base URL.")
    parser.add_argument("--json", action="store_true", help="Print a JSON array instead of NDJSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    api_token = os.environ.get(args.token_env, "")
    if not api_token:
        raise SystemExit(f"missing Zabbix API token in {args.token_env}")
    query = ZabbixProblemQuery(
        min_severity=args.min_severity,
        limit=max(args.limit, 0),
        include_suppressed=args.include_suppressed,
    )
    problems = fetch_zabbix_problems(api_url=args.api_url, api_token=api_token, query=query)
    events = [
        alert_event_to_mapping(event)
        for event in zabbix_problems_to_alert_events(problems, source_url_base=args.source_url_base)
    ]
    if args.json:
        print(json.dumps(events, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        for event in events:
            print(json.dumps(event, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
