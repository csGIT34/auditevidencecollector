"""Create a standalone source directory with operational documentation only."""
import argparse
import ast
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from check_docs import LINK
from export_workplace_source import ROOT_FILES, SCRIPTS

ROOT = Path(__file__).resolve().parents[1]
GUIDES = ('EVIDENCE_REPORTS', 'WIZ_INTEGRATION', 'CONFIGURATION_ASSESSMENTS',
          'KUBERNETES_EVIDENCE', 'GUEST_EVIDENCE', 'OPERATIONAL_EVIDENCE',
          'AZURE_POLICY_EVIDENCE', 'AZURE_FUNCTIONS')


def replace(text, old, new):
    if old not in text:
        raise ValueError('Expected source fragment missing: ' + old)
    return text.replace(old, new)


def clean(output):
    output = Path(output).resolve()
    if output == ROOT or output in ROOT.parents or output.exists():
        raise ValueError('Use a new output directory')
    names = set(ROOT_FILES)
    names.update('scripts/' + name + '.py' for name in SCRIPTS if name != 'lab_probe')
    for directory, patterns in (
        ('cloud_governance', ('*.py', '*.json')), ('tests', ('*.py',)),
        ('examples', ('**/*.json',)), ('docs/audit', ('*.py', '*.json')),
        ('docs/schemas', ('*.json',)),
    ):
        for pattern in patterns:
            names.update(str(p.relative_to(ROOT)) for p in (ROOT/directory).glob(pattern))
    names.update('docs/' + name + '.md' for name in GUIDES)
    files = {}
    for name in sorted(names):
        path = ROOT/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Invalid input: ' + name)
        files[name] = path.read_text(encoding='utf-8')

    key = 'scripts/build_functions_package.py'
    text = files[key].replace('import shutil\n', '')
    text = replace(text, ', with_lab_probe=False', '')
    start = text.index('        if with_lab_probe:')
    end = text.index('        output.parent.mkdir', start)
    text = text[:start] + text[end:]
    text = replace(text, "; no Azure action performed. Lab probe included:', with_lab_probe)", "; no Azure action performed.')")
    text = '\n'.join(line for line in text.split('\n') if "parser.add_argument('--with-lab-probe'" not in line)
    files[key] = replace(text, ', with_lab_probe=args.with_lab_probe', '')

    text = files.pop('tests/test_lab_safety.py')
    tree = ast.parse(text)
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'test_probe_retains_only_new_synthetic_bytes_and_conflict_is_required')
    lines = text.splitlines(keepends=True)
    del lines[method.lineno-1:method.end_lineno]
    text = ''.join(lines)
    text = '\n'.join(line for line in text.split('\n') if line not in (
        'from contextlib import contextmanager', 'from datetime import datetime, timezone, timedelta',
        'import importlib.util', 'from tests.test_archive import MemoryStore',
        'from tests.test_azure_adapters import SUB,TENANT', 'from scripts.lab_probe import probe'))
    text = text.replace('LabSafetyTests', 'RuntimeSafetyTests').replace('excludes_infrastructure_and_lab_probe', 'contains_only_runtime_files')
    text = replace(text, "self.assertFalse(any('lab_probe' in n or n.startswith('infra/') for n in archive.namelist()))",
                   "self.assertTrue(all(n.startswith('cloud_governance/') or n in {'function_app.py', 'host.json', 'requirements.txt', 'constraints.txt'} for n in archive.namelist()))")
    files['tests/test_runtime_safety.py'] = replace(text, 'build(output, with_lab_probe=True)', 'build(output)')
    files['scripts/smoke_functions_runtime.py'] = files['scripts/smoke_functions_runtime.py'].replace("'CG_LAB_PROBE_ENABLED=false', ", '')
    files['scripts/check_docs.py'] = files['scripts/check_docs.py'].replace("'docs', 'infra/personal-lab', 'examples'", "'docs', 'examples'")
    files['.gitignore'] = files['.gitignore'].replace('# Terraform and personal lab data (lock file is deliberately tracked)', '# Local infrastructure state').replace('lab-private/\n', '')
    files['.funcignore'] = files['.funcignore'].replace('lab-private/\n', '').replace('lab-private\n', '')
    text = files['scripts/validate.py'].replace('import argparse\n', '')
    start = text.index('    parser = argparse.ArgumentParser')
    end = text.index("    for module in", start)
    text = text[:start] + text[end:]
    text = text.replace("script == 'validate_catalog.py' and workplace", "script == 'validate_catalog.py'")
    files['scripts/validate.py'] = text.replace("label = 'Workplace offline gate' if workplace else 'Offline gate'", "label = 'Offline gate'")
    files['docs/audit/validate_catalog.py'] = files['docs/audit/validate_catalog.py'].replace('lab research prose checks', 'reference prose checks')

    files['tests/test_resource_group_scope.py'] = files['tests/test_resource_group_scope.py'].replace("RG='lab-test'", "RG='scope-test'")
    files['cloud_governance/pdf_report.py'] = replace(
        files['cloud_governance/pdf_report.py'],
        '# Scope-inherited facts repeat across resources: 51 predicates in the first lab run\n        # held 14 distinct observations. Printing each one once keeps every leaf and stops',
        '# Scope-inherited facts repeat across resources. Printing each distinct\n        # observation once keeps every leaf and stops')

    # Replace historical documentation, retaining the operational contract sections.
    for name in GUIDES:
        key = 'docs/' + name + '.md'
        text = files[key]
        if name == 'AZURE_POLICY_EVIDENCE':
            text = text.split('## Current assignment')[0]
            text = text.replace('the reviewed lab configuration', 'an example configuration')
            text = text.replace(' — 499 of 531 in the first lab run —', '')
        text = text.replace('## Rehearse at home', '## Offline rehearsal')
        text = re.sub(r' See (?:the )?\[(?:home checkpoint|current checkpoint)\]\([^)]*\)\.', '', text)
        text = text.replace(' and the [baseline review](AZURE_POLICY_REVIEW.md)', '')
        paragraphs = text.split('\n\n')
        text = '\n\n'.join(
            p for p in paragraphs if not re.search(r'csGIT34|auditevidencecollector|home.lab|personal.lab|Home-lab|Terraform is home-only', p, re.I))
        files[key] = text
    for path in (ROOT/'scripts/standalone_docs').rglob('*.md'):
        files[str(path.relative_to(ROOT/'scripts/standalone_docs'))] = path.read_text()
    retained = set(files)
    for name, text in list(files.items()):
        if not name.endswith('.md'):
            continue
        def link(match):
            parsed = urlsplit(match[1].strip('<>'))
            if parsed.scheme or parsed.netloc or not parsed.path:
                return match[0]
            target = (ROOT / name).parent / unquote(parsed.path)
            relative = str(target.resolve().relative_to(ROOT))
            if relative in retained:
                return match[0]
            return re.match(r'\[([^\]]*)\]', match[0])[1]
        files[name] = LINK.sub(link, text).rstrip() + "\n"
    # Fail closed if identifying development-origin text remains in the copy.
    forbidden = re.compile(r'\blab\b|csGIT34|auditevidencecollector|home[ -]lab|personal[ -]lab|lab_probe|with-lab-probe|HOME_LAB|WORKPLACE_SOURCE_MANIFEST|d855930|519f8ca|83d39cd', re.I)
    for name, text in files.items():
        if forbidden.search(name + '\n' + text):
            raise ValueError('Development-origin reference remains in ' + name)
        if name.endswith('.py'):
            ast.parse(text)
    output.mkdir(parents=True)
    for name, text in files.items():
        path = output/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8', newline='\n')
    print(f'Created standalone source directory: {output} ({len(files)} files)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    clean(parser.parse_args().output)
