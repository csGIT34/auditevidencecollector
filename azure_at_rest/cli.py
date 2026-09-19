"""Command line interface; the default offline path needs only Python."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from .assessment import assess
from .catalog import RULES, RULE_VERSION
from .collector import ArmTransport, Collector, FixtureTransport
from .report import exit_code, markdown
from .safety import subscription_id
from .snapshot import validate_snapshot


def write_private(path, value):
    """Replace atomically with an owner-only file, regardless of process umask."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".azure-at-rest-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def parser():
    root = argparse.ArgumentParser(description="Read-only Azure encryption-at-rest technical evidence; provider-managed keys accepted.")
    commands = root.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect", help="Collect live ARM evidence or exercise the same collector with a fixture.")
    collect.add_argument("--subscription", action="append", help="Subscription UUID; repeat to select multiple. Default: discover accessible subscriptions in current tenant.")
    collect.add_argument("--fixture", type=Path, help="Offline HTTP response fixture. Makes no Azure or credential calls.")
    collect.add_argument("--snapshot", type=Path, help="Optional sanitized collection snapshot for replay.")
    collect.add_argument("--max-pages", type=int, default=1000, help="Per-list safety limit; reaching it records incomplete evidence.")
    replay = commands.add_parser("assess", help="Reassess a sanitized snapshot using the current rule version; no Azure calls.")
    replay.add_argument("--input", type=Path, required=True)
    for subparser in (collect, replay):
        subparser.add_argument("--json", type=Path, default=Path("evidence/audit.json"), help="JSON report destination.")
        subparser.add_argument("--report", type=Path, default=Path("evidence/audit.md"), help="Markdown report destination.")
    commands.add_parser("catalog", help="Print exact supported types, scopes, APIs and Microsoft sources as JSON.")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "catalog":
            print(json.dumps({"rule_version": RULE_VERSION, "rules": {rt: asdict(rule) for rt, rule in sorted(RULES.items())}}, indent=2))
            return 0
        outputs = [args.json, args.report]
        if args.command == "collect" and args.snapshot:
            outputs.append(args.snapshot)
        if len({p.resolve() for p in outputs}) != len(outputs):
            raise ValueError("Output paths must be distinct")
        input_path = getattr(args, "input", None) or getattr(args, "fixture", None)
        if input_path and input_path.resolve() in {p.resolve() for p in outputs}:
            raise ValueError("An output path must not overwrite the input")
        if args.command == "collect":
            if args.subscription and any(not subscription_id(s) for s in args.subscription):
                raise ValueError("Each subscription must be a UUID")
            if args.fixture:
                data = json.loads(args.fixture.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or data.get("fixture_version") != "1.0" or not isinstance(data.get("responses"), dict):
                    raise ValueError("Expected fixture_version 1.0 and a responses object")
                transport, mode = FixtureTransport(data["responses"]), "offline_fixture"
            else:
                transport, mode = ArmTransport(), "azure_live"
            snapshot = Collector(transport, args.max_pages, mode).collect(args.subscription)
            if args.snapshot:
                write_private(args.snapshot, json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
        else:
            snapshot = json.loads(args.input.read_text(encoding="utf-8"))
            validate_snapshot(snapshot)
        report = assess(snapshot)
        snapshot_bytes = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
        report["snapshot_sha256"] = hashlib.sha256(snapshot_bytes).hexdigest()
        report["reassessed_from_snapshot"] = args.command == "assess"
        write_private(args.json, json.dumps(report, indent=2, sort_keys=True) + "\n")
        write_private(args.report, markdown(report))
        summary = report["summary"]
        print(f"{summary['conclusion']}: {summary['resource_count']} resources; "
              f"{summary['counts']['FAIL']} failed; coverage incomplete={summary['coverage_incomplete']}.")
        print(f"JSON: {args.json}\nReport: {args.report}")
        return exit_code(report)
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        # Deliberately omit exception text: malformed input and API errors may contain secrets.
        print("Input/output error. Check paths, JSON schema, subscription UUIDs and positive page limit. No raw error payload was printed.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
