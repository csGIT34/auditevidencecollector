"""Command line interface; the default offline path needs only Python."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import tempfile

from .workflow import assess_snapshot
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
    collect.add_argument("--resource-group", help="Limit inventory and hydration to one group; requires exactly one --subscription.")
    collect.add_argument("--subscription", action="append", help="Subscription UUID; repeat to select multiple. Default: discover accessible subscriptions in current tenant.")
    collect.add_argument("--fixture", type=Path, help="Offline HTTP response fixture. Makes no Azure or credential calls.")
    collect.add_argument("--snapshot", type=Path, help="Optional sanitized collection snapshot for replay.")
    collect.add_argument("--store", type=Path, help="Archive a unique complete run in this local storage root; no cloud writes.")
    collect.add_argument("--max-pages", type=int, default=1000, help="Per-list safety limit; reaching it records incomplete evidence.")
    replay = commands.add_parser("assess", help="Reassess a sanitized snapshot using the current rule version; no Azure calls.")
    replay.add_argument("--input", type=Path, required=True)
    for subparser in (collect, replay):
        subparser.add_argument("--json", type=Path, help="Optional loose JSON export (default without --store: evidence/audit.json).")
        subparser.add_argument("--report", type=Path, help="Optional loose Markdown export (default without --store: evidence/audit.md).")
    commands.add_parser("catalog", help="Print exact supported types, scopes, APIs and Microsoft sources as JSON.")
    runs = commands.add_parser("runs", help="List local run archive states; complete archive does not mean audit PASS.")
    runs.add_argument("--store", type=Path, required=True)
    pdf = commands.add_parser("pdf", help="Render and archive one self-contained PDF from one exact saved run. No recollection or reassessment.")
    pdf.add_argument("--store", type=Path, required=True)
    pdf.add_argument("--run-id", required=True, help="Exact r-... identifier printed by collect or runs; no implicit latest run.")
    pdf.add_argument("--export", type=Path, help="Optional additional PDF copy; must not already exist.")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "catalog":
            print(json.dumps({"rule_version": RULE_VERSION, "rules": {rt: asdict(rule) for rt, rule in sorted(RULES.items())}}, indent=2))
            return 0
        if args.command in {"runs", "pdf"}:
            from .archive import list_runs, publish_pdf, digest
            from .storage import FileStore
            store = FileStore(args.store)
            if args.command == "runs":
                print(json.dumps(list_runs(store), indent=2))
                return 0
            manifest = publish_pdf(store, args.run_id)
            print(f"PDF archived: {manifest['pdf']['key']}\nReport ID: {manifest['report_id']}\nGenerated: {manifest['generated_at']}")
            if args.export:
                data = store.read(manifest['pdf']['key'])
                if digest(data) != manifest['pdf']['sha256']:
                    raise ValueError("PDF integrity mismatch")
                try:
                    FileStore(args.export.parent).put_new(args.export.name, data)
                except (OSError, ValueError):
                    print("PDF is archived, but the extra export failed (existing/unsafe path or I/O error). No existing export was replaced.", file=sys.stderr)
                    return 3
                print(f"PDF export: {args.export}")
            return 0
        if not getattr(args, "store", None):
            args.json = args.json or Path("evidence/audit.json")
            args.report = args.report or Path("evidence/audit.md")
        outputs = [p for p in (args.json, args.report) if p]
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
            snapshot = Collector(transport, args.max_pages, mode).collect(args.subscription, resource_group=args.resource_group)
            if args.snapshot:
                write_private(args.snapshot, json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
        else:
            snapshot = json.loads(args.input.read_text(encoding="utf-8"))
            validate_snapshot(snapshot)
        report = assess_snapshot(snapshot, reassessed=args.command == "assess")
        if getattr(args, "store", None):
            from .archive import save_run
            from .storage import FileStore
            manifest = save_run(FileStore(args.store), snapshot, report)
            print(f"Run ID: {manifest['run_id']}\nLocal archive complete: runs/{manifest['run_id']}/manifest.json")
        if args.json:
            write_private(args.json, json.dumps(report, indent=2, sort_keys=True) + "\n")
        if args.report:
            write_private(args.report, markdown(report))
        summary = report["summary"]
        print(f"{summary['conclusion']}: {summary['resource_count']} resources; "
              f"{summary['counts']['FAIL']} failed; coverage incomplete={summary['coverage_incomplete']}.")
        if args.json:
            print(f"JSON: {args.json}")
        if args.report:
            print(f"Report: {args.report}")
        return exit_code(report)
    except RuntimeError as error:
        if str(error) == "PDF_DEPENDENCY_MISSING":
            print('PDF generation requires the optional dependency: install this project with its [pdf] extra. Collection and saved evidence are unchanged.', file=sys.stderr)
        else:
            print('Report generation failed. The selected evidence run is unchanged; inspect report publication state. No raw payload was printed.', file=sys.stderr)
        return 3
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        # Deliberately omit exception text: malformed input and API errors may contain secrets.
        print("Input/output error. Check paths, JSON schema, subscription UUIDs and positive page limit. No raw error payload was printed.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
