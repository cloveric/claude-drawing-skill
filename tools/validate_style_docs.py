#!/usr/bin/env python3
"""Check that SKILL.md, styles/, lib/ and examples/ stay consistent.

Dependency-free; run from anywhere:  python3 tools/validate_style_docs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(
    r'^\| (?P<name>.+?) \| \[(?P<slug>[a-z0-9]+)\]\((?P<guide>styles/[a-z0-9]+\.md)\) '
    r'\| `lib/(?P<module>[a-z0-9_]+\.py)` · `(?P<cls>\w+)` '
    r'\| `(?P<example>examples/[^`]+)` \| .+ \|$'
)
SECTIONS = ('## 何时选用', '## 接口速查', '## 毛病清单')


def main() -> int:
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    errors = []

    rows = []
    for line in skill.splitlines():
        if '](styles/' in line:
            m = ROW.match(line)
            if m:
                rows.append(m)
            else:
                errors.append(f'malformed index row: {line[:60]}')
    if not rows:
        errors.append('no style rows found in SKILL.md')

    slugs = [r['slug'] for r in rows]
    for dup in {s for s in slugs if slugs.count(s) > 1}:
        errors.append(f'duplicate slug: {dup}')

    declared = re.search(r'in (\d+) styles', skill)
    if declared and int(declared.group(1)) != len(rows):
        errors.append(f'description says {declared.group(1)} styles, index has {len(rows)}')

    for r in rows:
        slug, guide = r['slug'], ROOT / r['guide']
        if r['guide'] != f'styles/{slug}.md':
            errors.append(f'{slug}: guide path must be styles/{slug}.md')
        module = ROOT / 'lib' / r['module']
        if not module.exists():
            errors.append(f'{slug}: missing module lib/{r["module"]}')
        elif not re.search(rf'^class {r["cls"]}\b', module.read_text(encoding='utf-8'), re.M):
            errors.append(f'{slug}: class {r["cls"]} not defined in lib/{r["module"]}')
        if not (ROOT / r['example']).exists():
            errors.append(f'{slug}: missing example {r["example"]}')
        if not guide.exists():
            errors.append(f'{slug}: missing guide {r["guide"]}')
            continue
        text = guide.read_text(encoding='utf-8')
        for heading in SECTIONS:
            body = text.split(heading, 1)
            if len(body) < 2 or not re.split(r'\n## ', body[1], maxsplit=1)[0].strip():
                errors.append(f'{slug}: guide has no content under "{heading}"')
        if f'`lib/{r["module"]}` · `{r["cls"]}`' not in text:
            errors.append(f'{slug}: guide does not match the index implementation')

    orphans = {p.stem for p in (ROOT / 'styles').glob('*.md')} - set(slugs)
    for slug in sorted(orphans):
        errors.append(f'orphan guide not in index: styles/{slug}.md')

    indexed = {r['module'] for r in rows} | {'core.py'}
    for p in sorted((ROOT / 'lib').glob('*.py')):
        if p.name not in indexed:
            errors.append(f'lib/{p.name} is not in the SKILL.md index')

    for rel in re.findall(r'\]\(((?!https?:|styles/)[^)#]+)\)', skill):
        if not (ROOT / rel).exists():
            errors.append(f'SKILL.md links to missing file: {rel}')

    for error in errors:
        print(error)
    if errors:
        return 1
    print(f'validated {len(rows)} style guides')
    return 0


if __name__ == '__main__':
    sys.exit(main())
