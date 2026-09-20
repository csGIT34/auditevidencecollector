"""Build an allowlisted source package; never upload/deploy or copy local data."""
import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def write_readable_file(archive, path, root):
    # Private local build permissions must not restrict Azure's runtime user.
    # Normalize only ZIP metadata; local source/output permissions stay private.
    info = zipfile.ZipInfo.from_file(path, path.relative_to(root))
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, path.read_bytes())


def package(output):
    files = [ROOT / name for name in ('function_app.py', 'host.json', 'requirements.txt', 'constraints.txt')]
    modules = ('__init__', '__main__', 'archive', 'assessment', 'authorization', 'backup_population', 'backup_jobs', 'blob_containers', 'azure_adapters', 'catalog', 'cli', 'collector', 'compute_instances', 'container_revisions', 'controls', 'diagnostic_routes', 'graph',
               'hosting', 'kubernetes_evidence', 'kubernetes_collect', 'guest_evidence', 'vault_metadata', 'automation_assets', 'log_tables', 'operational', 'pdf_report', 'provenance', 'reconciliation', 'run_comparison', 'wiz', 'report', 'safety', 'snapshot', 'storage', 'verification', 'workflow')
    files += [ROOT / 'azure_at_rest' / (name + '.py') for name in modules]
    files += [ROOT / 'azure_at_rest/program_scope.json', ROOT / 'azure_at_rest/control_objectives.json']
    if any(not f.is_file() or f.is_symlink() for f in files):
        raise ValueError('invalid_deployment_input')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            write_readable_file(archive, path, ROOT)
    return len(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(f'Packaged {package(args.output)} reviewed source files. Dependencies require a Linux build before deployment.')
