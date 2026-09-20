"""Command line interface; the default offline path needs only Python."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import tempfile

from .workflow import assess_snapshot
from . import report_model
from .catalog import RULES, RULE_VERSION
from .collector import ArmTransport, Collector, FixtureTransport
from .report import exit_code, markdown
from .safety import subscription_id
from .snapshot import validate_snapshot


def write_private(path, value):
    """Replace atomically with an owner-only file, regardless of process umask."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".cloud-governance-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def parser():
    root = argparse.ArgumentParser(description="Read-only Azure technical evidence and configurable control assessments.")
    commands = root.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect", help="Collect live ARM evidence or exercise the same collector with a fixture.")
    collect.add_argument("--graph-fixture", type=Path, help="Opt-in offline Graph response fixture; requires --fixture and --tenant-id.")
    collect.add_argument("--graph", action="store_true", help="Opt-in live Graph metadata using tenant-bound Azure CLI authentication; requires --tenant-id.")
    collect.add_argument("--tenant-id", help="Explicit tenant UUID for opt-in Graph collection.")
    collect.add_argument("--resource-group", help="Limit inventory and hydration to one group; requires exactly one --subscription.")
    collect.add_argument("--subscription", action="append", help="Subscription UUID; repeat to select multiple. Default: discover accessible subscriptions in current tenant.")
    collect.add_argument("--fixture", type=Path, help="Offline HTTP response fixture. Makes no Azure or credential calls.")
    collect.add_argument("--snapshot", type=Path, help="Optional sanitized collection snapshot for replay.")
    collect.add_argument("--store", type=Path, help="Archive a unique complete run in this local storage root; no cloud writes.")
    collect.add_argument("--max-pages", type=int, default=1000, help="Per-list safety limit; reaching it records incomplete evidence.")
    replay = commands.add_parser("assess", help="Reassess a sanitized snapshot using the current rule version; no Azure calls.")
    replay.add_argument("--input", type=Path, required=True)
    for subparser in (collect, replay):
        subparser.add_argument("--criteria", type=Path, help="Versioned configuration criteria JSON; absent or draft criteria leave checks UNKNOWN.")
        subparser.add_argument("--json", type=Path, help="Optional loose JSON export (default without --store: evidence/audit.json).")
        subparser.add_argument("--report", type=Path, help="Optional loose Markdown export (default without --store: evidence/audit.md).")
    controls = commands.add_parser("control-register", help="Index one saved assessment by NIST control; no recollection or reassessment.")
    controls.add_argument("--input", type=Path, help="Saved assessment JSON from collect or assess.")
    controls.add_argument("--template", type=Path, help="Write a starter tailoring instead of indexing a run; defaults to the controls the deployed resource types implicate.")
    controls.add_argument("--template-scope", choices=("service", "candidate"), default="service", help="service: controls implicated by the collected Azure resource types. candidate: every organization-wide candidate control.")
    controls.add_argument("--tailoring", type=Path, help="Approved control tailoring JSON; absent or draft dispositions never exclude a control.")
    controls.add_argument("--operational", type=Path, help="Optional saved operational supplement contributing attributed records.")
    controls.add_argument("--json", type=Path, help="Optional register JSON export.")
    controls.add_argument("--report", type=Path, help="Optional register Markdown export.")
    commands.add_parser("catalog", help="Print exact supported types, scopes, APIs and Microsoft sources as JSON.")
    runs = commands.add_parser("runs", help="List local run archive states; complete archive does not mean audit PASS.")
    runs.add_argument("--store", type=Path, required=True)
    pdf = commands.add_parser("pdf", help="Render and archive one self-contained PDF from one exact saved run. No recollection or reassessment.")
    pdf.add_argument("--store", type=Path, required=True)
    pdf.add_argument("--run-id", required=True, help="Exact r-... identifier printed by collect or runs; no implicit latest run.")
    pdf.add_argument("--export", type=Path, help="Optional additional PDF copy; must not already exist.")
    wiz = commands.add_parser("wiz-import", help="Validate and archive a normalized Wiz evidence file; no network calls.")
    wiz.add_argument("--input", type=Path, required=True)
    wiz.add_argument("--store", type=Path, required=True)
    compare = commands.add_parser("wiz-reconcile", help="Compare one saved Azure run and one Wiz import without reassessment.")
    compare.add_argument("--store", type=Path, required=True)
    compare.add_argument("--run-id", required=True)
    compare.add_argument("--wiz-import-id", required=True)
    compare.add_argument("--as-of", required=True, help="Explicit timezone-aware comparison time.")
    compare.add_argument("--max-age-hours", type=float, required=True)
    compare.add_argument("--max-skew-hours", type=float, required=True)
    show = commands.add_parser("wiz-show", help="Verify and print one exact saved comparison; no recomputation.")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--comparison-id", required=True)
    diff = commands.add_parser("compare-runs", help="Archive changes between two exact saved runs; no reassessment.")
    diff.add_argument("--store", type=Path, required=True)
    diff.add_argument("--before", required=True)
    diff.add_argument("--after", required=True)
    diff_show = commands.add_parser("comparison-show", help="Verify and print an exact saved run comparison.")
    diff_show.add_argument("--store", type=Path, required=True)
    diff_show.add_argument("--comparison-id", required=True)
    operating = commands.add_parser("operational-import", help="Archive attributed operating records against one exact run; no reassessment.")
    operating.add_argument("--store", type=Path, required=True)
    operating.add_argument("--run-id", required=True)
    operating.add_argument("--input", type=Path, required=True)
    operating.add_argument("--as-of", required=True)
    operating.add_argument("--max-age-hours", type=float, required=True)
    for command in ("operational-show", "operational-pdf"):
        sub = commands.add_parser(command, help="Verify an exact operational supplement and show it or archive its PDF.")
        sub.add_argument("--store", type=Path, required=True)
        sub.add_argument("--evidence-id", required=True)
    kube=commands.add_parser('kubernetes-import',help='Project a Kubernetes export into an exact saved AKS run supplement; raw payload is not archived.')
    kube.add_argument('--store',type=Path,required=True)
    kube.add_argument('--run-id',required=True)
    kube.add_argument('--input',type=Path,required=True)
    kube.add_argument('--criteria',type=Path)
    kube.add_argument('--as-of',required=True)
    kube.add_argument('--max-age-seconds',type=int,required=True)
    for command in ('kubernetes-show','kubernetes-pdf'):
        sub=commands.add_parser(command)
        sub.add_argument('--store',type=Path,required=True)
        sub.add_argument('--evidence-id',required=True)
    kube=commands.add_parser('guest-import',help='Assess a typed guest/agent export against the saved VM population and archive its measurements.')
    kube.add_argument('--store',type=Path,required=True)
    kube.add_argument('--run-id',required=True)
    kube.add_argument('--input',type=Path,required=True)
    kube.add_argument('--criteria',type=Path)
    kube.add_argument('--as-of',required=True)
    kube.add_argument('--max-age-seconds',type=int,required=True)
    for command in ('guest-show','guest-pdf'):
        sub=commands.add_parser(command)
        sub.add_argument('--store',type=Path,required=True)
        sub.add_argument('--evidence-id',required=True)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command in ('kubernetes-import','kubernetes-show','kubernetes-pdf','guest-import','guest-show','guest-pdf'):
            from .storage import FileStore
            if args.command.startswith('guest-'):
                from .guest_evidence import MAX_BYTES,publish,load,publish_pdf
            else:
                from .kubernetes_evidence import MAX_BYTES,publish,load,publish_pdf
            from .wiz import decode
            store=FileStore(args.store)
            if args.command.endswith('-import'):
                with args.input.open('rb') as stream:data=stream.read(MAX_BYTES+1)
                criteria=None
                if args.criteria:
                    with args.criteria.open('rb') as stream:raw_criteria=stream.read(4097)
                    if len(raw_criteria)>4096:raise ValueError('Criteria too large')
                    criteria=decode(raw_criteria)
                print(json.dumps(publish(store,args.run_id,data,criteria=criteria,as_of=args.as_of,max_age_seconds=args.max_age_seconds),indent=2))
            elif args.command.endswith('-show'):print(load(store,args.evidence_id)['markdown'],end='')
            else:print(json.dumps(publish_pdf(store,args.evidence_id),indent=2))
            return 0
        if args.command in {"operational-import", "operational-show", "operational-pdf"}:
            from .storage import FileStore
            from .operational import MAX_BYTES, publish, load, publish_pdf
            store=FileStore(args.store)
            if args.command == "operational-import":
                with args.input.open('rb') as stream:data=stream.read(MAX_BYTES+1)
                print(json.dumps(publish(store,args.run_id,data,as_of=args.as_of,max_age_hours=args.max_age_hours),indent=2))
            elif args.command == "operational-show":
                print(load(store,args.evidence_id)['markdown'],end='')
            else:
                print(json.dumps(publish_pdf(store,args.evidence_id),indent=2))
            return 0
        if args.command in {"compare-runs", "comparison-show"}:
            from .storage import FileStore
            from .run_comparison import publish, load
            store = FileStore(args.store)
            if args.command == "compare-runs":
                print(json.dumps(publish(store, args.before, args.after), indent=2, sort_keys=True))
            else:
                print(load(store, args.comparison_id)['markdown'], end='')
            return 0
        if args.command == "wiz-show":
            from .storage import FileStore
            from .reconciliation import load_comparison
            print(load_comparison(FileStore(args.store), args.comparison_id)['markdown'], end='')
            return 0
        if args.command in {"wiz-import", "wiz-reconcile"}:
            from .storage import FileStore
            from .wiz import MAX_INPUT_BYTES, import_export
            from .reconciliation import publish_comparison
            store = FileStore(args.store)
            if args.command == "wiz-import":
                with args.input.open('rb') as stream:
                    data = stream.read(MAX_INPUT_BYTES + 1)
                manifest = import_export(store, data)
                print(json.dumps({'wiz_import_id':manifest['wiz_import_id'], 'input_sha256':manifest['input_sha256'],
                                  'source_mode':manifest['source_mode'], 'state':'complete'}, sort_keys=True))
            else:
                manifest = publish_comparison(store, args.run_id, args.wiz_import_id, as_of=args.as_of,
                                              max_age_hours=args.max_age_hours, max_skew_hours=args.max_skew_hours)
                print(json.dumps(manifest, indent=2, sort_keys=True))
            return 0
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
        if args.command == "control-register":
            from .control_register import build, markdown as control_markdown, template
            if args.template:
                write_private(args.template, json.dumps(template(args.template_scope), indent=2, sort_keys=True) + "\n")
                print("Starter tailoring written as a draft: review every disposition and owner, then set status to approved.")
                return 0
            if not args.input:
                raise ValueError("control-register requires --input or --template")
            report = json.loads(args.input.read_text(encoding="utf-8"))
            if not isinstance(report, dict) or report.get("schema_version") not in ("1.0", "1.1"):
                raise ValueError("Expected a saved assessment with schema_version 1.0 or 1.1")
            tailoring = json.loads(args.tailoring.read_text(encoding="utf-8")) if args.tailoring else None
            operational = json.loads(args.operational.read_text(encoding="utf-8")) if args.operational else None
            register = build(report, tailoring, operational)
            outputs = [p for p in (args.json, args.report) if p]
            if len({p.resolve() for p in outputs}) != len(outputs):
                raise ValueError("Output paths must be distinct")
            if args.input.resolve() in {p.resolve() for p in outputs}:
                raise ValueError("An output path must not overwrite the input")
            if args.json:
                write_private(args.json, json.dumps(register, indent=2, sort_keys=True) + "\n")
            if args.report:
                write_private(args.report, control_markdown(register))
            summary = register["summary"]
            print("Controls indexed: " + str(summary["controls"]) + "; with evidence: " + str(summary["with_evidence"]) +
                  "; " + json.dumps(summary["statuses"], sort_keys=True))
            if not register["tailoring"]["declared"]:
                print("Tailoring is NOT DECLARED: no control is excluded or inherited and coverage cannot be judged complete.", file=sys.stderr)
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
        if getattr(args,"graph_fixture",None) and args.graph_fixture.resolve() in {p.resolve() for p in outputs}:
            raise ValueError("Output must not overwrite Graph fixture")
        if args.criteria and args.criteria.resolve() in {p.resolve() for p in outputs}:
            raise ValueError("Output must not overwrite criteria")
        from .controls import decode_policy
        criteria = decode_policy(args.criteria.read_text()) if args.criteria else None
        if args.command == "collect":
            if args.tenant_id and not (args.graph or args.graph_fixture):
                raise ValueError("Tenant selection requires Graph opt-in")
            if (args.graph or args.graph_fixture) and (not args.tenant_id or subscription_id(args.tenant_id)!=args.tenant_id or args.graph and args.fixture or args.graph_fixture and not args.fixture or args.graph and args.graph_fixture):
                raise ValueError("Invalid Graph mode/scope")
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
            if args.graph:
                from .azure_adapters import verify_tenant
                verify_tenant(transport,[s['id'] for s in snapshot['inventory']['subscriptions']],args.tenant_id)
            if args.graph or args.graph_fixture:
                from .graph import GraphCollector, FixtureGraphTransport, GraphTransport, GraphCredential
                from .safety import now
                credential = None
                try:
                    if args.graph_fixture:
                        graph_data=json.loads(args.graph_fixture.read_text())
                        if graph_data.get('fixture_version')!='1.0' or not isinstance(graph_data.get('responses'),dict):raise ValueError('Invalid Graph fixture')
                        graph_transport=FixtureGraphTransport(graph_data['responses'])
                    else:
                        from azure.identity import AzureCliCredential
                        credential=AzureCliCredential(tenant_id=args.tenant_id,process_timeout=20)
                        graph_transport=GraphTransport(GraphCredential(credential))
                    snapshot['identity_evidence']=GraphCollector(graph_transport,args.tenant_id,args.max_pages).collect()
                    snapshot['completed_at']=now()
                finally:
                    if credential is not None:credential.close()
            if args.snapshot:
                write_private(args.snapshot, json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
        else:
            snapshot = json.loads(args.input.read_text(encoding="utf-8"))
            validate_snapshot(snapshot)
        report = assess_snapshot(snapshot, reassessed=args.command == "assess", criteria=criteria)
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
        print(f"{report_model.overall(report)['conclusion']}: {summary['resource_count']} resources; "
              f"{summary['counts']['FAIL']} failed; coverage incomplete={report_model.overall(report)['coverage_incomplete']}.")
        print("Configuration checks: " + json.dumps(report_model.configuration_summary(report), sort_keys=True))
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
