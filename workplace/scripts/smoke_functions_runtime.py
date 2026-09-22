"""Exercise a built Functions ZIP locally in Docker; no Azure login or resources."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'mcr.microsoft.com/azure-functions/python@sha256:ecdc82ecd47f144f5aa55c14086d6e67684bb3b4b5577ba00d11bb9a47dacd5e'


def check_runtime(package, output, operational=False, workload=False, guest=False):
    package, output = Path(package).resolve(), Path(output).resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Use a new private output directory outside the checkout')
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700)
    summary = {'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
               'image': IMAGE, 'checks': [], 'passed': False}
    name = 'cg-functions-smoke-' + secrets.token_hex(6)
    container_started = False
    try:
        with tempfile.TemporaryDirectory(prefix='cg-functions-smoke-') as temporary:
            root = Path(temporary)
            stage = root / 'app'
            stage.mkdir()
            with zipfile.ZipFile(package) as archive:
                for item in archive.infolist():
                    target = (stage / item.filename).resolve()
                    if not target.is_relative_to(stage):
                        raise ValueError('Invalid archive path')
                archive.extractall(stage)
            for item in stage.rglob('*'):
                item.chmod(0o755 if item.is_dir() else 0o644)
            function_key, master_key = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            key_file = root / 'local-keys.json'
            key_file.write_text(json.dumps({
                'masterKey': {'name': 'master', 'value': master_key, 'encrypted': False},
                'functionKeys': [{'name': 'default', 'value': function_key, 'encrypted': False}],
                'systemKeys': []}))
            command = ['docker', 'create', '--name', name, '--platform', 'linux/amd64',
                       '--memory', '2g', '--cpus', '1', '-p', '127.0.0.1::80',
                       '--mount', f'type=bind,src={stage},dst=/home/site/wwwroot,readonly',
                       '--mount', f'type=bind,src={key_file},dst=/etc/functionkeys/host.json,readonly']
            for setting in ['AzureWebJobsSecretStorageType=files', 'FUNCTIONS_SECRETS_PATH=/etc/functionkeys',
                            'FUNCTIONS_WORKER_RUNTIME=python', 'CG_COLLECTION_ENABLED=false',
                            'CG_REPORT_ENABLED=false', 'CG_COLLECTION_SCHEDULE=']:
                command += ['-e', setting]
            command += ['-e', 'CG_OPERATIONAL_ENABLED='+str(operational).lower()]
            command += ['-e', 'CG_WORKLOAD_ENABLED='+str(workload).lower(), '-e', 'CG_KUBERNETES_COLLECTION_ENABLED='+str(workload).lower(), '-e', 'CG_GUEST_ENABLED='+str(guest).lower()]
            command.append(IMAGE)
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
            container_started = True
            try:
                subprocess.run(['docker', 'start', name], check=True, capture_output=True, timeout=30)
                port = int(subprocess.check_output(['docker', 'port', name, '80/tcp'],
                                                  text=True, timeout=15).strip().rsplit(':', 1)[1])

                def request(method, path, body=None, key=None, timeout=10):
                    headers = {'Content-Type': 'application/json'}
                    if key:
                        headers['x-functions-key'] = key
                    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout)
                    started = time.monotonic()
                    try:
                        connection.request(method, path, body=json.dumps(body) if body is not None else None,
                                           headers=headers)
                        response = connection.getresponse()
                        data = response.read()
                        return response.status, data, round(time.monotonic() - started, 4)
                    finally:
                        connection.close()

                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    try:
                        status, _, _ = request('GET', '/', timeout=2)
                        if status == 200:
                            break
                    except (OSError, http.client.HTTPException):
                        pass
                    time.sleep(2)
                else:
                    raise RuntimeError('Local Functions host did not become ready within 90 seconds')

                status, data, _ = request('GET', '/admin/host/status', key=master_key)
                if status != 200:
                    raise RuntimeError(f'Local host status failed: HTTP {status}')
                summary['host_version'] = json.loads(data).get('version')
                status, data, _ = request('GET', '/admin/functions', key=master_key)
                if status != 200:
                    raise RuntimeError(f'Local function listing failed: HTTP {status}')
                summary['functions'] = sorted(item['name'] for item in json.loads(data))
                if not {'GenerateReport', 'GenerateEvidenceReport'} <= set(summary['functions']) or 'CollectEvidence' in summary['functions']:
                    raise RuntimeError('Expected report function and no collection timer')
                for label, key, expected in [('missing-key', None, 401), ('wrong-key', 'invalid-local-test-key', 401), ('invalid-body', function_key, 400)]:
                    status, body, elapsed = request('POST', '/api/evidence/reports', {}, key)
                    summary['checks'].append({'name': 'selected-report-' + label, 'status': status, 'expected': expected, 'seconds': elapsed})
                    if status != expected or (status == 400 and json.loads(body) != {'code': 'invalid_evidence_report_request'}):
                        raise RuntimeError('Selected evidence route validation failed')
                status, body, elapsed = request('POST', '/api/evidence/reports', {'run_id': 'r-' + 'a' * 32, 'topic': 'encryption-at-rest'}, function_key)
                summary['checks'].append({'name': 'selected-report-disabled', 'status': status, 'expected': 503, 'seconds': elapsed})
                if status != 503 or json.loads(body).get('state') != 'disabled':
                    raise RuntimeError('Selected evidence reporting was not disabled')
                cases = [('missing-key', None, 401), ('wrong-key', 'invalid-local-test-key', 401)]
                cases += [(f'authenticated-{i}', function_key, 400) for i in range(1, 21)]
                for label, key, expected in cases:
                    status, body, elapsed = request('POST', '/api/reports', {'run_id': 'latest'}, key)
                    summary['checks'].append({'name': label, 'status': status,
                                              'expected': expected, 'seconds': elapsed})
                    if status != expected or (status == 400 and json.loads(body) != {'code': 'exact_run_id_required'}):
                        raise RuntimeError(f'{label}: expected HTTP {expected}, received {status}')
                operational_names={'ImportOperationalEvidence','GenerateOperationalReport'}
                if operational_names.intersection(summary['functions']) != (operational_names if operational else set()):
                    raise RuntimeError('Unexpected operational route registration')
                if operational:
                    for route, code in [('import','invalid_operational_request'),('reports','exact_evidence_id_required')]:
                        for label,key,expected in [('missing-key',None,401),('wrong-key','invalid-local-test-key',401),('invalid-body',function_key,400)]:
                            status,body,elapsed=request('POST','/api/operational/'+route,{},key)
                            summary['checks'].append({'name':route+'-'+label,'status':status,'expected':expected,'seconds':elapsed})
                            if status!=expected or (status==400 and json.loads(body)!={'code':code}):
                                raise RuntimeError('Operational route validation failed')
                workload_names={'ImportKubernetesEvidence','GenerateKubernetesReport','CollectKubernetesEvidence'}
                if workload_names.intersection(summary['functions']) != (workload_names if workload else set()):
                    raise RuntimeError('Unexpected workload route registration')
                if workload:
                    for route,code in [('import','invalid_kubernetes_request'),('reports','exact_kubernetes_id_required'),('collect','exact_run_id_required')]:
                        for label,key,expected in [('missing-key',None,401),('wrong-key','invalid-local-test-key',401),('invalid-body',function_key,400)]:
                            status,body,elapsed=request('POST','/api/workloads/kubernetes/'+route,{},key)
                            summary['checks'].append({'name':'workload-'+route+'-'+label,'status':status,'expected':expected,'seconds':elapsed})
                            if status!=expected or (status==400 and json.loads(body)!={'code':code}):raise RuntimeError('Workload route validation failed')
                guest_names={'ImportGuestEvidence','GenerateGuestReport'}
                if guest_names.intersection(summary['functions']) != (guest_names if guest else set()):
                    raise RuntimeError('Unexpected guest route registration')
                if guest:
                    for route,code in [('import','invalid_guest_request'),('reports','exact_guest_id_required')]:
                        for label,key,expected in [('missing-key',None,401),('wrong-key','invalid-local-test-key',401),('invalid-body',function_key,400)]:
                            status,body,elapsed=request('POST','/api/guests/'+route,{},key)
                            summary['checks'].append({'name':'guest-'+route+'-'+label,'status':status,'expected':expected,'seconds':elapsed})
                            if status!=expected or (status==400 and json.loads(body)!={'code':code}):raise RuntimeError('Guest route validation failed')
                summary['passed'] = True
            finally:
                try:
                    logs = subprocess.run(['docker', 'logs', name], capture_output=True, text=True, timeout=15)
                    (output / 'host.log').write_text(logs.stdout + '\n' + logs.stderr)
                finally:
                    subprocess.run(['docker', 'rm', '-f', name], check=True, capture_output=True, timeout=30)
                    container_started = False
    except Exception as error:
        summary['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        summary['container_removed'] = not container_started
        (output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f"Passed {len(summary['checks'])} local runtime checks; container removed. Results: {output}")
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True, help='Linux amd64 Python 3.12 deployment ZIP')
    parser.add_argument('--output', type=Path, required=True, help='New private directory outside this checkout')
    parser.add_argument('--operational',action='store_true',help='Also verify opt-in operational endpoints')
    parser.add_argument('--workload',action='store_true',help='Also verify opt-in Kubernetes import/report endpoints')
    parser.add_argument('--guest',action='store_true',help='Verify opt-in guest evidence endpoints')
    args = parser.parse_args()
    check_runtime(args.package, args.output, args.operational, args.workload, args.guest)
