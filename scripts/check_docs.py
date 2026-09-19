"""Check repository Markdown relative-link targets without network access."""
import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"\n]*")?\)')


def broken_links(root, paths):
    errors = []
    for path in paths:
        # Ignore fenced examples; anchors are not file targets and are not checked.
        text = re.sub(r'(^[ \t]*(`{3,}|~{3,}).*?^\s*\2[^\n]*$)', '', path.read_text(encoding='utf-8'), flags=re.M | re.S)
        for match in LINK.finditer(text):
            link = match[1].strip('<>')
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (root / unquote(parsed.path.lstrip('/')) if parsed.path.startswith('/')
                      else path.parent / unquote(parsed.path))
            if not target.exists():
                errors.append(f'{path.relative_to(root)}: missing relative target {parsed.path}')
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    paths = sorted(root.glob('*.md'))
    for directory in ('docs', 'infra/personal-lab', 'examples'):
        paths.extend(sorted((root/directory).rglob('*.md')))
    errors = broken_links(root, paths)
    for error in errors:
        print(error)
    print(f'Documentation link check: {len(paths)} files, {len(errors)} missing targets. External URLs/anchors are not checked.')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
