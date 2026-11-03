#!/usr/bin/env python3
"""Collect read-only evidence for a SONiC component; never evaluate Make."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

GROUPS = ('identity classification locations outputs package_contents package_metadata '
          'source_acquisition patches sources generated_files build_steps compile_commands '
          'host_tools dependency_interfaces').split()
SOURCE_SUFFIXES = {'.c', '.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.go', '.rs', '.py',
                   '.s', '.S', '.proto', '.y', '.l'}
BUILD_NAMES = {'Makefile', 'Makefile.am', 'Makefile.in', 'CMakeLists.txt', 'configure.ac',
               'configure.in', 'Cargo.toml', 'go.mod', 'setup.py', 'setup.cfg', 'pyproject.toml',
               'autogen.sh', 'meson.build'}


def run(argv, cwd=None):
    """Only called with fixed inspection tools, never input-derived executables."""
    try:
        p = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=False)
        return {'command': argv, 'cwd': str(cwd) if cwd else None,
                'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except OSError as exc:
        return {'command': argv, 'exit_code': None, 'error': str(exc)}


def paragraphs(text):
    result = []
    for paragraph in re.split(r'\n\s*\n', text):
        fields, key = {}, None
        for line in paragraph.splitlines():
            if line.startswith((' ', '\t')) and key:
                fields[key] += '\n' + line[1:]
            elif ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                fields[key] = value.strip()
        if fields:
            result.append(fields)
    return result


def records(path):
    """Retain raw expressions and conditional context, including recipes."""
    conditions, pending, start = [], '', 0
    for number, raw in enumerate(path.read_text(errors='replace').splitlines(), 1):
        if not pending:
            start = number
        if raw.endswith('\\'):
            pending += raw[:-1] + ' '
            continue
        text = pending + raw
        pending = ''
        stripped = text.strip()
        if re.match(r'^(ifeq|ifneq|ifdef|ifndef)\b', stripped):
            conditions.append(stripped)
        elif stripped.startswith('else') and conditions:
            conditions[-1] = 'else of (' + conditions[-1] + ') ' + stripped[4:].strip()
        elif stripped == 'endif' and conditions:
            conditions.pop()
        elif stripped and not stripped.startswith('#'):
            yield {'file': str(path), 'line': start, 'text': text,
                   'conditions': list(conditions), 'state': 'confirmed',
                   'meaning': 'Original declaration, not evaluated'}
    if pending:
        yield {'file': str(path), 'line': start, 'text': pending,
               'conditions': list(conditions), 'state': 'confirmed'}


def git_state(path):
    return {name: run(['git', '-C', str(path)] + args) for name, args in {
        'root': ['rev-parse', '--show-toplevel'], 'commit': ['rev-parse', 'HEAD'],
        'status': ['status', '--porcelain', '--untracked-files=no'],
        'remote': ['config', '--get-regexp', r'^remote\..*\.url$']}.items()}


def safe_id(value):
    # Percent-encoding preserves identity instead of merging punctuation into '_'.
    from urllib.parse import quote
    if not value or value in {'.', '..'}:
        raise ValueError('Component identity must not be empty, . or ..')
    return quote(value, safe='-_.').replace('/', '%2F')


def collect(args):
    root = args.repo.resolve()
    parent = args.output_dir.resolve() if args.output_dir else Path('/tmp/sonic-bazel-migration') / safe_id(args.component)
    out = parent / 'components' / safe_id(args.component)
    if out.exists() and (out / 'analysis.json').exists() and not args.overwrite:
        raise ValueError(f'Existing analysis files: {out}; review before using --overwrite')
    task = {}
    if args.tasks:
        data = json.loads(args.tasks.read_text())
        tasks = data.get('tasks', []) if isinstance(data, dict) else data
        matches = [item for item in tasks if item.get('id') == args.component]
        if len(matches) != 1:
            raise ValueError('Task file must contain exactly one task with the matching id')
        task = matches[0]
    def path(value):
        p = Path(value)
        return (root / p).resolve() if not p.is_absolute() else p.resolve()
    directories = [path(p) for p in args.source_dir]
    rules = [path(p) for p in args.rule]
    for directory in directories:
        if not directory.is_dir():
            raise ValueError(f'Source directory does not exist: {directory}')
    for item in rules + args.compile_db + args.log + args.artifact:
        if not item.is_file():
            raise ValueError(f'Input file does not exist: {item}')
    if not directories and not rules:
        raise ValueError('Specify at least one --source-dir or --rule to avoid guessing source ownership')
    evidence_dir = out / 'evidence'
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence = []
    def save(name, data, origins):
        target = evidence_dir / name
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        ref = {'path': 'evidence/' + name, 'sources': origins}
        evidence.append(ref)
        return ref['path']
    report = {'schema_version': 1, 'task_id': args.component,
              'repository_state': git_state(root),
              'required_conditions': task.get('required_conditions', []),
              'observed_configuration': args.configuration,
              'analysis_status': 'analyzing', 'evidence': evidence, 'unresolved': []}
    for name in GROUPS:
        report[name] = {'state': 'unconfirmed', 'value': [], 'conditions': [], 'evidence': [],
                        'reason': 'Collection proves listed declarations and observations only; manually review completeness and all conditions'}
    def add(group, value, ref):
        report[group]['value'].append(value)
        if ref not in report[group]['evidence']:
            report[group]['evidence'].append(ref)
    files = sorted(set(p for directory in directories for p in directory.rglob('*')
                       if p.is_file() and not p.is_symlink() and '.git' not in p.parts))
    inventories = [{'path': str(p), 'bytes': p.stat().st_size} for p in files]
    listing = save('files.json', inventories, [str(p) for p in directories])
    add('sources', {'state': 'confirmed', 'kind': 'Filesystem inventory (not proof of compilation)',
                    'files': [str(p) for p in files if p.suffix in SOURCE_SUFFIXES]}, listing)
    for directory in directories:
        add('locations', {'state': 'confirmed', 'source_location': str(directory),
                          'origin': 'Explicit input; actual build directories still require tracing',
                          'repository': git_state(directory)}, listing)
    add('locations', {'rule_locations': [str(p) for p in rules],
                      'build_directories': args.build_dir, 'write_scope': [],
                      'state': 'unconfirmed'}, listing)
    build_files = sorted(set(rules + [p for p in files if p.name in BUILD_NAMES or
                                      p.name.endswith('.mk') or p.as_posix().endswith('/debian/rules')]))
    declarations = [record for p in build_files for record in records(p)]
    declaration_ref = save('build-declarations.json', declarations, [str(p) for p in build_files])
    patterns = {
        'compile_commands': r'(?i)(?:\b(?:CFLAGS|CXXFLAGS|CPPFLAGS|LDFLAGS|RUSTFLAGS|GOFLAGS|CC|CXX|LD|configure_opts)\b|FLAGS_MAINT|--enable-|--disable-)',
        'source_acquisition': r'(?i)(?:\b(?:https?://|git clone|wget|curl|SRC_PATH|URL|SHA256|COMMIT|VERSION)\b)',
        'generated_files': r'(?i)(?:\b(?:protoc|bison|flex|swig|generate|generated|configure_file|add_custom_command)\b|BUILT_SOURCES)',
        'host_tools': r'(?i)(?:Build-Depends|\b(?:PKG_CHECK_MODULES|AC_PATH_PROG|find_program|cargo|rustc|go build|python[23]?|protoc|cmake|autoreconf|dh_auto_\w+)\b)',
        'dependency_interfaces': r'(?i)(?:_DEPENDS|_RDEPENDS|LDADD|LIBADD|LIBS|INCLUDES|pkg.config|target_link_libraries)',
        'patches': r'(?i)(?:\b(?:patch|quilt)\b|\.patch)',
    }
    for group, expression in patterns.items():
        add(group, {'state': 'confirmed', 'kind': 'Original declaration candidate; interpret its role and completeness',
                    'records': [r for r in declarations if re.search(expression, r['text'])]}, declaration_ref)
    add('build_steps', {'state': 'confirmed', 'kind': 'Original build entry text; no execution-order inference',
                        'files': [str(p) for p in build_files]}, declaration_ref)
    add('classification', {'state': 'unconfirmed', 'observed_suffixes': sorted({p.suffix for p in files}),
                           'build_declarations': [str(p) for p in build_files]}, listing)
    if task:
        task_ref = save('task-input.json', task, [str(args.tasks)])
        add('outputs', {'state': 'unconfirmed', 'kind': 'Upstream task record', 'outputs': task.get('outputs', [])}, task_ref)
        add('dependency_interfaces', {'state': 'unconfirmed', 'dependencies': task.get('dependencies', [])}, task_ref)
    for p in files:
        if p.as_posix().endswith('/debian/control'):
            data = paragraphs(p.read_text(errors='replace'))
            ref = save('control-' + hashlib.sha256(str(p).encode()).hexdigest()[:12] + '.json', data, [str(p)])
            add('package_metadata', {'state': 'confirmed', 'kind': 'Debian declaration', 'fields': data}, ref)
            add('outputs', {'state': 'unconfirmed', 'kind': 'Declared binary package; filenames and conditions not expanded',
                            'packages': [x['Package'] for x in data if 'Package' in x]}, ref)
            add('host_tools', {'state': 'confirmed', 'kind': 'Build dependency declaration; classify libraries and tools',
                               'fields': [x for x in data if 'Build-Depends' in x]}, ref)
        if p.as_posix().endswith('/debian/changelog'):
            first = p.read_text(errors='replace').splitlines()[:1]
            add('identity', {'state': 'confirmed', 'kind': 'First changelog declaration', 'text': first,
                             'source': str(p)}, listing)
        if p.name == 'series':
            add('patches', {'state': 'confirmed', 'kind': 'Declared series order; verify application conditions',
                            'file': str(p), 'entries': p.read_text(errors='replace').splitlines()}, listing)
    add('patches', {'state': 'confirmed', 'kind': 'Disk patch inventory, not proof of application order',
                    'files': [str(p) for p in files if p.suffix in {'.patch', '.diff'}]}, listing)
    for index, db in enumerate(args.compile_db):
        commands = json.loads(db.read_text())
        if not isinstance(commands, list) or any(not isinstance(c, dict) or 'directory' not in c or
            'file' not in c or not ('command' in c or 'arguments' in c) for c in commands):
            raise ValueError(f'Invalid compilation database: {db}')
        ref = save(f'compile-db-{index}.json', commands, [str(db)])
        add('compile_commands', {'state': 'confirmed', 'kind': 'Existing compilation database, not proof of this execution',
                                 'configuration': args.configuration, 'provenance': args.provenance,
                                 'commands': len(commands), 'source': str(db)}, ref)
        add('sources', {'state': 'confirmed', 'kind': 'Compilation database input declarations',
                        'files': [{'directory': c['directory'], 'file': c['file']} for c in commands]}, ref)
    for index, log in enumerate(args.log):
        lines = [{'line': n, 'text': line} for n, line in enumerate(log.read_text(errors='replace').splitlines(), 1)
                 if re.search(r'(?:^|\s)(?:\S*/)?(?:cc|gcc|g\+\+|clang\+\+|clang|rustc|ld)(?:\s|$)', line)]
        ref = save(f'log-commands-{index}.json', lines, [str(log)])
        add('compile_commands', {'state': 'unconfirmed', 'kind': 'Logged command candidates, possibly echoes or dry-run',
                                 'configuration': args.configuration, 'provenance': args.provenance}, ref)
    for index, artifact in enumerate(args.artifact):
        info = {'path': str(artifact), 'sha256': hashlib.file_digest(artifact.open('rb'), 'sha256').hexdigest(),
                'provenance': args.provenance, 'configuration': args.configuration,
                'source_version_match': 'unconfirmed'}
        contents, package = [], []
        inspection_ok = True
        if artifact.suffix == '.deb':
            package = run(['dpkg-deb', '--info', str(artifact.resolve())])
            contents = run(['dpkg-deb', '--contents', str(artifact.resolve())])
            if package.get('exit_code') != 0 or contents.get('exit_code') != 0:
                inspection_ok = False
                report['unresolved'].append({'artifact': str(artifact), 'reason': 'dpkg-deb inspection failed',
                                             'results': [package, contents]})
        elif zipfile.is_zipfile(artifact):
            with zipfile.ZipFile(artifact) as archive:
                contents = [{'path': i.filename, 'bytes': i.file_size, 'mode': i.external_attr >> 16}
                            for i in archive.infolist()]
                package = [{'path': i.filename, 'text': archive.read(i).decode(errors='replace')}
                           for i in archive.infolist() if i.filename.endswith(('/METADATA', '/WHEEL'))]
        elif tarfile.is_tarfile(artifact):
            with tarfile.open(artifact) as archive:
                contents = [{'path': i.name, 'type': i.type.decode(errors='replace'), 'mode': i.mode,
                             'uid': i.uid, 'gid': i.gid, 'link': i.linkname, 'bytes': i.size}
                            for i in archive]
        else:
            report['unresolved'].append({'artifact': str(artifact), 'reason': 'Unrecognized archive format'})
        ref = save(f'artifact-{index}.json', {'identity': info, 'contents': contents, 'metadata': package}, [str(artifact)])
        add('package_contents', {'state': 'confirmed' if contents and inspection_ok else 'unconfirmed', **info}, ref)
        add('package_metadata', {'state': 'confirmed' if package and inspection_ok else 'unconfirmed', **info}, ref)
    report['unresolved'].append({'reason': 'Static candidates are unevaluated; review sub-build chains, all conditions, product mappings, effective parameters and tool versions'})
    (out / 'analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    markdown = [f'# {args.component} Original build analysis', '', f'Output directory: `{out}`', '',
                'Status: analyzing. Confirmed items are declarations or existing observations; the complete build contract still requires review.', '']
    for group in GROUPS:
        item = report[group]
        markdown += [f'## {group} ({item["state"]})', '', item['reason'], '',
                     '```json', json.dumps(item['value'], ensure_ascii=False, indent=2), '```', '',
                     'Evidence: ' + ', '.join(f'[{p}]({p})' for p in item['evidence']), '']
    markdown += ['## Unconfirmed items', '', '```json', json.dumps(report['unresolved'], ensure_ascii=False, indent=2), '```', '']
    (out / 'analysis.md').write_text('\n'.join(markdown))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component', help='Stable task identity; provide explicit source or rule ownership')
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--output-dir', type=Path, help='Task directory containing components/<id>')
    parser.add_argument('--tasks', type=Path, help='JSON object containing tasks, or a task array')
    for name in ('source-dir', 'rule', 'compile-db', 'log', 'artifact'):
        parser.add_argument('--' + name, type=Path if name != 'source-dir' else str, action='append', default=[])
    parser.add_argument('--build-dir', action='append', default=[])
    parser.add_argument('--configuration', action='append', default=[], help='Configuration of existing evidence, KEY=VALUE')
    parser.add_argument('--provenance', help='Source version/run provenance of existing evidence; unconfirmed if omitted')
    parser.add_argument('--overwrite', action='store_true', help='Explicitly replace component analysis without modifying tasks.json')
    args = parser.parse_args()
    try:
        print(collect(args))
    except (ValueError, OSError, json.JSONDecodeError, tarfile.TarError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'Collection failed: {exc}\n')


if __name__ == '__main__':
    main()
