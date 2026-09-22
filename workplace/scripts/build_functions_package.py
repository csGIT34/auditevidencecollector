"""Build Linux runtime dependencies into the allowlisted source; never deploy."""
import argparse
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import zipfile
if __package__:
    from .package_functions import package, ROOT, write_readable_file
else:
    from package_functions import package, ROOT, write_readable_file


def build(output, *, wheelhouse=None):
    if platform.system() != 'Linux' or platform.machine().lower() not in ('x86_64', 'amd64') or sys.version_info[:2] != (3, 12):
        raise RuntimeError('Build on Linux x86_64 Python 3.12; ARM wheels and Mac virtual environments are unsupported')
    output = Path(output)
    if output.exists():
        raise FileExistsError('Use a new output filename')
    with tempfile.TemporaryDirectory(prefix='functions-build-') as temporary:
        tmp = Path(temporary)
        package(tmp/'source.zip')
        stage = tmp/'stage'
        with zipfile.ZipFile(tmp/'source.zip') as source:
            source.extractall(stage)  # Generated locally from an exact source allowlist.
        command = [sys.executable, '-m', 'pip', 'install', '--ignore-installed', '-r', str(stage/'requirements.txt'),
                   '--target', str(stage/'.python_packages/lib/site-packages'), '--no-compile']
        if wheelhouse:
            command += ['--no-index', '--find-links', str(Path(wheelhouse).resolve())]
        subprocess.run(command, check=True, cwd=stage)
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(stage.rglob('*')):
                if file.is_symlink():
                    raise ValueError('No symlinks in deployment package')
                if file.is_file():
                    write_readable_file(archive, file, stage)
    print('Built Linux deployment package; no Azure action performed.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wheelhouse', type=Path)
    args=parser.parse_args()
    build(args.output, wheelhouse=args.wheelhouse)
