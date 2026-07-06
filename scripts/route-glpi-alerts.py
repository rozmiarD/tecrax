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

from tecrax.alert_routing import GlpiClient, TicketState, load_events, route_events


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Route normalized Zabbix/Wazuh alert events to GLPI tickets."
    )
    parser.add_argument("--events", type=Path, required=True, help="JSON array or NDJSON events file.")
    parser.add_argument("--state", type=Path, required=True, help="Duplicate-suppression state file.")
    parser.add_argument("--api-url", help="GLPI API base URL ending with apirest.php.")
    parser.add_argument("--dry-run", action="store_true", help="Render drafts without creating tickets.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    events = load_events(args.events)
    state = TicketState(args.state)
    dry_run = bool(args.dry_run)
    client = None
    if not dry_run:
        app_value = os.environ.get("GLPI_APP_TOKEN", "")
        user_value = os.environ.get("GLPI_USER_TOKEN", "")
        if not args.api_url or not app_value or not user_value:
            raise SystemExit("live mode requires --api-url plus GLPI_APP_TOKEN and GLPI_USER_TOKEN")
        client = GlpiClient(api_url=args.api_url, app_token=app_value, user_token=user_value)
    results = route_events(events, state, client=client, dry_run=dry_run)
    print(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
