#!/usr/bin/env python3
"""
Generate or update the first compartment list in a .policy file.

Scans an LLVM IR (.ll) file for all functions and global variables whose
debug info points to a given source directory, then writes them as the
first list in the policy file.  All other lists in the policy are preserved.

Usage:
    python3 gen_policy.py <file.ll> <source_dir> <policy_file>

Example:
    python3 gen_policy.py build/stm32App.elf.ll Sys/ comp/.policy
"""

import re
import sys
import os


def parse_metadata(text):
    meta = {}
    for m in re.finditer(r'^(!(\d+))\s*=\s*(?:distinct\s+)?(.+)$', text, re.MULTILINE):
        meta[int(m.group(2))] = m.group(3).strip()
    return meta


def get_meta_field(content, field):
    m = re.search(rf'\b{field}:\s*(!(\d+)|"([^"]*)")', content)
    if not m:
        return None
    return int(m.group(2)) if m.group(2) else m.group(3)


def resolve_file(meta, file_id):
    content = meta.get(file_id, '')
    if 'DIFile' not in content:
        return ''
    d = get_meta_field(content, 'directory') or ''
    f = get_meta_field(content, 'filename') or ''
    return (d.rstrip('/') + '/' + f) if (d or f) else ''


def collect_names(ll_path, src_dir):
    src_dir = os.path.abspath(src_dir)
    with open(ll_path) as fh:
        text = fh.read()

    meta = parse_metadata(text)
    names = set()

    for line in text.splitlines():
        if line.startswith('define '):
            nm = re.search(r'@(\S+?)\s*\(', line)
            dm = re.search(r'!dbg\s+!(\d+)', line)
            if not nm or not dm:
                continue
            sp = meta.get(int(dm.group(1)), '')
            file_ref = get_meta_field(sp, 'file')
            if not isinstance(file_ref, int):
                continue
            src = resolve_file(meta, file_ref)
            if os.path.abspath(src).startswith(src_dir):
                names.add(nm.group(1))

        elif line.startswith('@'):
            nm = re.match(r'^@(\S+?)\s*=', line)
            dm = re.search(r'!dbg\s+!(\d+)', line)
            if not nm or not dm:
                continue
            gve = meta.get(int(dm.group(1)), '')
            if 'DIGlobalVariableExpression' in gve:
                var_ref = get_meta_field(gve, 'var')
                if not isinstance(var_ref, int):
                    continue
                gve = meta.get(var_ref, '')
            if 'DIGlobalVariable' not in gve:
                continue
            file_ref = get_meta_field(gve, 'file')
            if not isinstance(file_ref, int):
                continue
            src = resolve_file(meta, file_ref)
            if os.path.abspath(src).startswith(src_dir):
                names.add(nm.group(1))

    return sorted(names)


def update_policy(policy_path, names):
    first_line = repr(names)

    if os.path.exists(policy_path):
        with open(policy_path) as fh:
            lines = fh.read().splitlines()
        rest = lines[1:] if lines else []
    else:
        rest = []

    with open(policy_path, 'w') as fh:
        fh.write(first_line + '\n')
        for line in rest:
            fh.write(line + '\n')


def main():
    if len(sys.argv) != 4:
        print(f'Usage: python3 {sys.argv[0]} <file.ll> <source_dir> <policy_file>')
        sys.exit(1)

    ll_path, src_dir, policy_path = sys.argv[1], sys.argv[2], sys.argv[3]

    names = collect_names(ll_path, src_dir)
    print(f'Found {len(names)} functions/globals from {src_dir}')

    update_policy(policy_path, names)
    print(f'Updated first list in {policy_path}')


if __name__ == '__main__':
    main()
