"""Offline mixed-inventory/PDF benchmark; each size runs in an isolated process."""
import argparse
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SUB = '11111111-1111-1111-1111-111111111111'


def fixture(count):
    from azure_at_rest.catalog import RULES
    from azure_at_rest.collector import endpoint, INVENTORY_API
    kinds = ('Microsoft.Storage/storageAccounts', 'Microsoft.Kusto/clusters',
             'Microsoft.Web/sites', 'Microsoft.Network/networkSecurityGroups', 'Microsoft.Example/widgets')
    rows, responses = [], {}
    for i in range(count):
        kind = kinds[i % len(kinds)]
        name = 'synthetic-' + str(i).zfill(6)
        rid = f'/subscriptions/{SUB}/resourceGroups/benchmark/providers/{kind}/{name}'
        row = {'id':rid, 'type':kind, 'name':name, 'location':'eastus',
               'kind':'functionapp' if kind == 'Microsoft.Web/sites' else '',
               'properties':{'enableDiskEncryption':i % 2 == 0}}
        rows.append(row)
        rule = RULES.get(kind.lower())
        if rule and rule.mode != 'na':
            responses[endpoint(rid, rule.api)] = {'fixture_error':403} if i % 17 == 0 else row
            for suffix, _ in rule.children:
                responses[endpoint(rid + '/' + suffix, rule.api)] = {'value':[]}
    # Exercise real pagination without any live transport.
    url = endpoint(f'/subscriptions/{SUB}/resources', INVENTORY_API)
    for start in range(0, count, 100):
        page_url = url if start == 0 else url + '&$skiptoken=' + str(start)
        page = {'value':rows[start:start + 100]}
        if start + 100 < count:
            page['nextLink'] = url + '&$skiptoken=' + str(start + 100)
        responses[page_url] = page
    return responses


def worker(count, output):
    from azure_at_rest import __version__
    from azure_at_rest.archive import digest, load_run, publish_pdf
    from azure_at_rest.collector import FixtureTransport
    from azure_at_rest.storage import FileStore
    from azure_at_rest.workflow import collect_run
    from pypdf import PdfReader
    from io import BytesIO
    from unittest.mock import patch
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    store = FileStore(output / 'archive')
    started = time.perf_counter()
    with patch('socket.create_connection', side_effect=AssertionError('offline benchmark')):
        transport = FixtureTransport(fixture(count))
        run = collect_run(store, transport, [SUB], mode='offline_fixture')
        collected = time.perf_counter()
        before = {key:digest(store.read(key)) for key in store.keys('runs/')}
        render_started = time.perf_counter()
        pdf = publish_pdf(store, run['run_id'])
        rendered = time.perf_counter()
    # Report peak RSS before PDF inspection, including fixture, archive and rendering.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mib = peak / (1024 * 1024 if sys.platform == 'darwin' else 1024)
    saved = load_run(store, run['run_id'])
    assert len(saved['snapshot']['resources']) == count
    assert before == {key:digest(store.read(key)) for key in before}
    data = store.read(pdf['pdf']['key'])
    assert digest(data) == pdf['pdf']['sha256']
    pages = len(PdfReader(BytesIO(data)).pages)
    result = {'resources':count, 'collection_archive_seconds':round(collected-started, 3),
              'report_seconds':round(rendered-render_started, 3), 'peak_rss_mib':round(peak_mib, 2),
              'pdf_pages':pages, 'pdf_bytes':len(data), 'pdf_sha256':digest(data),
              'pdf_key':pdf['pdf']['key'], 'run_id':run['run_id'], 'fixture_requests':len(transport.calls),
              'counts':run['counts'], 'originals_preserved':True, 'tool_version':__version__}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sizes', type=int, nargs='+', default=[100, 1000, 2000])
    parser.add_argument('--max-report-seconds', type=float, default=120)
    parser.add_argument('--max-rss-mib', type=float, default=1536)
    parser.add_argument('--worker-timeout', type=int, default=300)
    parser.add_argument('--worker', type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    os.umask(0o077)
    target = args.output.resolve()
    if target == ROOT or ROOT in target.parents or target.exists():
        parser.error('Use a new output directory outside the checkout.')
    if args.worker is not None:
        if not 1 <= args.worker <= 10000:
            parser.error('worker size must be 1..10000')
        worker(args.worker, target)
        return 0
    if (not all(1 <= n <= 10000 for n in args.sizes) or len(set(args.sizes)) != len(args.sizes)
            or not 1 <= args.max_report_seconds <= 300 or not 64 <= args.max_rss_mib <= 8192
            or not 1 <= args.worker_timeout <= 1800):
        parser.error('Invalid sizes or benchmark thresholds.')
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    results = []
    for size in args.sizes:
        case = target / str(size)
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', str(size),
                                   '--output', str(case)], capture_output=True, text=True, timeout=args.worker_timeout)
            if proc.returncode:
                raise RuntimeError('worker_failed')
            row = json.loads((case / 'result.json').read_text())
            row['within_local_thresholds'] = row['report_seconds'] <= args.max_report_seconds and row['peak_rss_mib'] <= args.max_rss_mib
        except subprocess.TimeoutExpired:
            row = {'resources':size, 'within_local_thresholds':False, 'failure':'worker_timeout'}
        except (OSError, ValueError, RuntimeError):
            row = {'resources':size, 'within_local_thresholds':False, 'failure':'worker_failed'}
        results.append(row)
        print(json.dumps(row), flush=True)
    summary = {'synthetic':True, 'azure_calls':0, 'platform':platform.platform(), 'python':platform.python_version(),
               'machine':platform.machine(), 'cpu_count':os.cpu_count(),
               'thresholds':{'max_report_seconds':args.max_report_seconds, 'max_rss_mib':args.max_rss_mib},
               'passed':all(r['within_local_thresholds'] for r in results), 'results':results,
               'limitation':'Local CPU/RSS measurements; no cloud latency, quota, throughput or production capacity claim.'}
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
