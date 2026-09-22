"""Download only the standalone project files into a new directory."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from urllib.request import Request, urlopen

REPOSITORY = 'csGIT34/auditevidencecollector'


def fetch(url):
    request = Request(url, headers={'User-Agent': 'workplace-source-import'})
    with urlopen(request, timeout=60) as response:
        return response.read()


def download(output, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Supply the full 40-character commit SHA with --ref')
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError('Use a new project or staging directory')
    if not output.parent.is_dir():
        raise ValueError('The parent directory must already exist')
    base = f'https://raw.githubusercontent.com/{REPOSITORY}/{revision}'
    manifest = json.loads(fetch(base + '/docs/workplace-files.json'))
    if manifest.get('schema_version') != 1 or not isinstance(manifest.get('files'), dict) or not manifest['files']:
        raise ValueError('Invalid file list')
    for name, digest in manifest['files'].items():
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or str(path) != name
                or any(part in ('.', '..', '.git') for part in path.parts)
                or not re.fullmatch(r'[A-Za-z0-9_./-]+', name)
                or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise ValueError('Invalid file-list entry')
    # Stage beside the destination; a failed transfer never publishes a partial project.
    with tempfile.TemporaryDirectory(prefix='.project-download-', dir=output.parent) as temp:
        stage = Path(temp) / 'project'
        stage.mkdir()
        for name, expected in manifest['files'].items():
            payload = fetch(base + '/workplace/' + name)
            if hashlib.sha256(payload).hexdigest() != expected:
                raise ValueError('Downloaded file failed verification: ' + name)
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        if output.exists() or output.is_symlink():
            raise FileExistsError('Destination was created during download')
        stage.rename(output)
    print(f'Copied {len(manifest["files"])} verified project files to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ref', required=True, help='Exact 40-character Git commit SHA')
    args = parser.parse_args()
    download(args.output, args.ref)
