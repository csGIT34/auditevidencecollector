"""Offline acceptance gate: all tests and dependencies required, no skipped checks."""
import importlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    for module in ('reportlab', 'pypdf', 'jmespath', 'azure.functions', 'azure.identity', 'azure.storage.blob'):
        importlib.import_module(module)
    for line in (ROOT / 'constraints.txt').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        name, version = line.split('==')
        if importlib.metadata.version(name) != version:
            raise ValueError('Dependency differs from tested constraints: ' + name)
    host = json.loads((ROOT / 'host.json').read_text())
    if host.get('version') != '2.0' or host.get('functionTimeout') != '00:10:00':
        raise ValueError('Unexpected host configuration; review and update validation together')
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT / 'tests'), top_level_dir=str(ROOT)))
    if not result.wasSuccessful() or result.skipped:
        print('Gate failed: required tests failed or skipped.', file=sys.stderr)
        return 1
    for script in ('validate_catalog.py', 'export_program_scope.py', 'export_control_objectives.py', 'export_nist_catalog.py', 'export_control_index.py'):
        args = [sys.executable, str(ROOT / 'docs/audit' / script)]
        if script == 'validate_catalog.py':
            args.append('--data-only')
        if script.startswith('export'):
            args.append('--check')
        subprocess.run(args, check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / 'scripts/control_delivery_register.py'), '--check'], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_docs.py')], check=True, cwd=ROOT)
    label = 'Offline gate'
    print(f'{label} passed: {result.testsRun} tests, zero skips. No Azure validation implied.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
