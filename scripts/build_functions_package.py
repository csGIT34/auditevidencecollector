"""Build Linux runtime dependencies into the allowlisted source; never deploy."""
import argparse
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
if __package__:
    from .package_functions import package, ROOT
else:
    from package_functions import package, ROOT


def build(output, *, wheelhouse=None, with_lab_probe=False):
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
        if with_lab_probe:
            shutil.copyfile(ROOT/'scripts/lab_probe.py', stage/'lab_probe.py')
            with (stage/'function_app.py').open('a') as f:
                f.write('\n# Explicit temporary lab package only.\nfrom lab_probe import register\nregister(app)\n')
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(stage.rglob('*')):
                if file.is_symlink():
                    raise ValueError('No symlinks in deployment package')
                if file.is_file():
                    archive.write(file, file.relative_to(stage))
    print('Built Linux deployment package; no Azure action performed. Lab probe included:', with_lab_probe)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wheelhouse', type=Path)
    parser.add_argument('--with-lab-probe', action='store_true', help='Add disabled, expiring, key-protected lab probe; never use for workplace production.')
    args=parser.parse_args()
    build(args.output, wheelhouse=args.wheelhouse, with_lab_probe=args.with_lab_probe)
