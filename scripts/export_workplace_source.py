"""Export a reviewed workplace source tree without lab infrastructure or research prose."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from export_workplace_docs import DOCUMENTS, ROOT, render_documents

GUIDES = DOCUMENTS + (
    'docs/CONFIGURATION_ASSESSMENTS.md',
    'docs/KUBERNETES_EVIDENCE.md',
    'docs/GUEST_EVIDENCE.md',
)
ROOT_FILES = (
    '.gitignore', '.funcignore', 'pyproject.toml', 'requirements.txt',
    'requirements-dev.txt', 'constraints.txt', 'function_app.py', 'host.json',
    'local.settings.example.json', 'deploy/app-settings.example.json',
)
SCRIPTS = (
    'validate', 'check_docs', 'package_functions', 'build_functions_package',
    'smoke_functions_runtime', 'benchmark_pipeline', 'draft_criteria',
    'control_delivery_register', 'demo_audit_evidence', 'demo_controls', 'demo_wiz',
    'lab_probe',
)
README = """# Audit evidence collector — workplace source

Start with [the handover](docs/WORKPLACE_AZURE_HANDOFF.md) and
[the startup prompt](docs/prompts/AZURE_ADAPTER_IMPLEMENTATION.md).
This is source and test data, not an installed environment or deployment ZIP.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate.py --workplace
python scripts/demo_audit_evidence.py --output ../audit-rehearsal-work
```

Use a new private rehearsal directory outside the checkout. Python needs pip/venv
support and access to an approved package source. Keep constraints unchanged.
The workplace gate runs every transferred test with zero skips, validates catalog
data, checks packaged catalog consistency and delivery metadata, and checks retained
documentation links. Only the lab research-prose checks are omitted.

The six initial guides are accompanied by three permission/workload contracts used
by tests. `docs/audit/*.json` and its Python validators/exporters are required data
and build support, not a reading assignment. `scripts/lab_probe.py` is retained only
because existing safety tests exercise it; never build with `--with-lab-probe` for
workplace deployment. The normal Functions package excludes it.

Personal infrastructure, Git history, lab operations scripts, CI deployment choices,
research Markdown, historical reports, real evidence and credentials are excluded.
Configure CI using workplace infrastructure patterns; do not import personal Terraform.
The manifest records source provenance, transformations and every payload hash.
No successful offline, packaged-runtime or live validation is implied by export.
"""


def export(output):
    names = set(ROOT_FILES) | set(GUIDES)
    names.update('scripts/' + name + '.py' for name in SCRIPTS)
    for directory, patterns in (
        ('cloud_governance', ('*.py', '*.json')),
        ('tests', ('*.py',)),
        ('examples', ('**/*.json',)),
        ('docs/audit', ('*.py', '*.json')),
        ('docs/schemas', ('*.json',)),
    ):
        for pattern in patterns:
            names.update(str(path.relative_to(ROOT)) for path in (ROOT / directory).glob(pattern))
    files = {}
    for name in sorted(names):
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise ValueError('Invalid export input: ' + name)
        files[name] = path.read_bytes()
    source_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    # The Windows checkout uses CRLF; catalog hashes are pinned to Git's LF bytes.
    files = {name: data.replace(b'\r\n', b'\n') for name, data in files.items()}
    files.update(render_documents(GUIDES, included_paths=names))
    files['README.md'] = README.encode('utf-8')
    manifest = {
        'kind': 'workplace-source',
        'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'source_working_tree_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
        'validation_command': 'python scripts/validate.py --workplace',
        'transformations': ['Text line endings normalized to LF (catalog digests use Git bytes)',
                            'Generated workplace README', 'Omitted local documentation links rendered as labelled plain text'],
        'source_sha256': source_hashes,
        'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
        'excluded': ['.git', '.github', 'infra', 'research Markdown', 'historical documents',
                     'lab_preflight.py', 'lab_request.py', 'local environments/settings/evidence'],
    }
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(name, data)
        archive.writestr('WORKPLACE_SOURCE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    print(f'Exported {len(files)} source/test/documentation files and manifest to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New source ZIP path')
    export(parser.parse_args().output)
