#!/usr/bin/env python3
"""
Parse an LLVM IR (.ll) file and print the source directory/file for every
function definition and global variable that has debug info.

Usage:
    python3 ll_source_map.py <path/to/file.ll>
"""

import re
import sys

def parse_metadata(ll_text):
    meta = {}
    for m in re.finditer(r'^(!(\d+))\s*=\s*(?:distinct\s+)?(.+)$', ll_text, re.MULTILINE):
        meta[int(m.group(2))] = m.group(3).strip()
    return meta

def get_meta_field(content, field):
    m = re.search(rf'\b{field}:\s*(!(\d+)|"([^"]*)")', content)
    if not m:
        return None
    if m.group(2):
        return int(m.group(2))
    return m.group(3)

def resolve_file(meta, file_id):
    content = meta.get(file_id, '')
    if 'DIFile' not in content:
        return '', ''
    return get_meta_field(content, 'directory') or '', \
           get_meta_field(content, 'filename')  or ''

def subprogram_source(meta, sp_id):
    content = meta.get(sp_id, '')
    file_ref = get_meta_field(content, 'file')
    if not isinstance(file_ref, int):
        return ''
    d, f = resolve_file(meta, file_ref)
    return (d.rstrip('/') + '/' + f) if (d or f) else ''

def global_source(meta, gve_id):
    content = meta.get(gve_id, '')
    if 'DIGlobalVariableExpression' in content:
        var_ref = get_meta_field(content, 'var')
        if not isinstance(var_ref, int):
            return ''
        content = meta.get(var_ref, '')
    if 'DIGlobalVariable' not in content:
        return ''
    file_ref = get_meta_field(content, 'file')
    if not isinstance(file_ref, int):
        return ''
    d, f = resolve_file(meta, file_ref)
    return (d.rstrip('/') + '/' + f) if (d or f) else ''

def main(ll_path):
    with open(ll_path) as f:
        text = f.read()

    meta = parse_metadata(text)
    results = []

    # --- Functions: match define lines, extract name / section / !dbg independently ---
    for line in text.splitlines():
        if not line.startswith('define '):
            continue
        # function name
        nm = re.search(r'@(\S+?)\s*\(', line)
        if not nm:
            continue
        name = nm.group(1)
        # section attribute
        sm = re.search(r'section\s+"([^"]+)"', line)
        section = sm.group(1) if sm else ''
        # debug metadata ref
        dm = re.search(r'!dbg\s+!(\d+)', line)
        if dm:
            source = subprogram_source(meta, int(dm.group(1)))
        else:
            source = ''
        results.append(('function', name, section, source))

    # --- Globals: lines starting with @ that have !dbg ---
    for line in text.splitlines():
        if not line.startswith('@'):
            continue
        nm = re.match(r'^(@\S+?)\s*=', line)
        if not nm:
            continue
        name = nm.group(1)
        dm = re.search(r'!dbg\s+!(\d+)', line)
        if not dm:
            continue
        source = global_source(meta, int(dm.group(1)))
        if source:
            results.append(('global', name, '', source))

    # --- Print ---
    col = '{:<10} {:<50} {:<20} {}'
    print(col.format('KIND', 'NAME', 'SECTION', 'SOURCE'))
    print('-' * 120)
    for kind, name, section, source in sorted(results, key=lambda r: (r[0], r[1])):
        print(col.format(kind, name[:50], section[:20], source))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: python3 {sys.argv[0]} <file.ll>')
        sys.exit(1)
    main(sys.argv[1])
