"""Build an allowlisted source package; never upload/deploy or copy local data."""
import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(output):
    files = [ROOT / name for name in ('function_app.py', 'host.json', 'requirements.txt', 'constraints.txt')]
    modules = ('__init__', '__main__', 'archive', 'assessment', 'azure_adapters', 'catalog', 'cli', 'collector',
               'hosting', 'pdf_report', 'provenance', 'report', 'safety', 'snapshot', 'storage', 'verification', 'workflow')
    files += [ROOT / 'azure_at_rest' / (name + '.py') for name in modules]
    files += [ROOT / 'azure_at_rest/program_scope.json']
    if any(not f.is_file() or f.is_symlink() for f in files):
        raise ValueError('invalid_deployment_input')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
    return len(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(f'Packaged {package(args.output)} reviewed source files. Dependencies require a Linux build before deployment.')
