#!/usr/bin/env python3
"""Validate style-guide links and implementation references in SKILL.md."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
index = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
links = re.findall(r'\[([^]]+)\]\((styles/([a-z0-9]+)\.md)\)', index)
if not links:
    raise SystemExit('No style links found')
seen = set()
errors = []
for label, rel, slug in links:
    if slug in seen:
        errors.append(f'duplicate slug: {slug}')
    seen.add(slug)
    if not (ROOT / rel).exists():
        errors.append(f'missing guide: {rel}')
    row = next((line for line in index.splitlines() if f'({rel})' in line), '')
    module = re.search(r'`lib/([^`]+)`', row)
    example = re.search(r'`(examples/[^`]+)`', row)
    if module and not (ROOT / 'lib' / module.group(1)).exists():
        errors.append(f'missing module for {slug}: {module.group(1)}')
    if example and not (ROOT / example.group(1)).exists():
        errors.append(f'missing example for {slug}: {example.group(1)}')
if len(seen) != 74:
    errors.append(f'expected 74 styles, found {len(seen)}')
for error in errors:
    print(error)
if errors:
    raise SystemExit(1)
print(f'validated {len(seen)} style guides')
