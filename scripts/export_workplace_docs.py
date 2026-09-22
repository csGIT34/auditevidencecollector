"""Export the six workplace guides, excluding lab history and research prose."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import zipfile

from check_docs import LINK

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    'docs/WORKPLACE_AZURE_HANDOFF.md',
    'docs/prompts/AZURE_ADAPTER_IMPLEMENTATION.md',
    'docs/WORKPLACE_RUNTIME_CONTRACT.md',
    'docs/AZURE_FUNCTIONS.md',
    'docs/EVIDENCE_REPORTS.md',
    'docs/WIZ_INTEGRATION.md',
)


def render_documents(documents=DOCUMENTS, included_paths=None):
    retained = {(ROOT / name).resolve() for name in (included_paths or documents)}
    files = {}
    for name in documents:
        path = ROOT / name

        def rewrite(match):
            link = match[1].strip('<>')
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                return match[0]
            target = (ROOT / unquote(parsed.path.lstrip('/'))
                      if parsed.path.startswith('/')
                      else path.parent / unquote(parsed.path)).resolve()
            if target in retained:
                return match[0]
            label = re.match(r'\[([^\]]*)\]', match[0])[1]
            return f'{label} (`{link}`; optional reference, not bundled)'

        files[name] = LINK.sub(rewrite, path.read_text(encoding='utf-8')).encode('utf-8')
    return files


def export(output):
    files = render_documents()
    revision = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(
        ['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    manifest = {
        'kind': 'workplace-documentation-only',
        'source_revision': revision,
        'source_working_tree_dirty': dirty,
        'note': 'Exports current working files; omitted local links become plain-text references. '
                'This is not runnable source, a full source manifest, or a deployment package.',
        'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
    }
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr('WORKPLACE_DOCS_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    print(f'Exported {len(files)} workplace documents and provenance manifest to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New documentation ZIP path')
    export(parser.parse_args().output)
