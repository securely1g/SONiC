#!/usr/bin/env python3
"""Update and merge migration task progress without rerunning collection."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import tempfile

STATUSES = ('pending_review', 'pending_migration', 'in_progress', 'pending_verification', 'completed', 'reused', 'blocked')
ANALYSIS_STATUSES = ('pending_analysis', 'analyzing', 'analysis_complete', 'analysis_blocked')
GRAPH_FIELDS = ('id', 'name', 'type', 'types', 'products', 'prerequisites',
                'rule_files', 'code_dirs', 'layer', 'blocked')
GRAPH_ROOT_FIELDS = ('inputs', 'product_to_task', 'layers', 'blocked_tasks',
                     'complete', 'issues')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def status(value):
    value = 'pending_review' if value == 'pending' else value
    if value not in STATUSES:
        raise ValueError(f'Invalid task status: {value!r}')
    return value


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get('tasks'), list):
        raise ValueError('Task file must be a JSON object containing a tasks array')
    tasks = {}
    for task in data['tasks']:
        if not isinstance(task, dict) or not isinstance(task.get('id'), str) or not task['id']:
            raise ValueError('Every task requires a nonempty string id')
        key = task['id']
        if key in tasks:
            raise ValueError(f'Duplicate task id: {key}')
        status(task.get('status', 'pending'))
        if task.get('analysis_status', 'pending_analysis') not in ANALYSIS_STATUSES:
            raise ValueError(f'{key}: Invalid analysis status')
        prerequisites = task.get('prerequisites', [])
        if not isinstance(prerequisites, list) or any(not isinstance(x, str) for x in prerequisites):
            raise ValueError(f'{key}: prerequisites must be an array of strings')
        tasks[key] = task
    for key, task in tasks.items():
        missing = set(task.get('prerequisites', [])) - tasks.keys()
        if missing:
            raise ValueError(f'{key}: Dependencies reference missing tasks: {sorted(missing)}')
    return tasks


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def save(path, data):
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def reference(value, directory):
    path = Path(value)
    return path if path.is_absolute() else directory / path


def normalize_reference(value, directory):
    return os.path.relpath(reference(value, directory).resolve(), directory.resolve())


def readable(path):
    if not path.is_file():
        raise ValueError(f'Evidence file is not readable: {path}')
    with path.open('rb') as stream:
        stream.read(1)


def completion(task, task_directory):
    for field in ('implementation', 'verification'):
        if not isinstance(task.get(field), str) or not task[field]:
            raise ValueError(f'{task["id"]}: Completion requires a {field} reference')
    implementation_path = reference(task['implementation'], task_directory)
    verification_path = reference(task['verification'], task_directory)
    implementation = read_json(implementation_path)
    verification = read_json(verification_path)
    for name, record in [('implementation', implementation), ('verification', verification)]:
        if not isinstance(record, dict) or record.get('task_id') != task['id']:
            raise ValueError(f'{task["id"]}: {name} task_id mismatch')
    required = set()
    deliverables = implementation.get('deliverables', [])
    if not isinstance(deliverables, list):
        raise ValueError('implementation.deliverables must be an array')
    for deliverable in deliverables:
        if not isinstance(deliverable, dict):
            raise ValueError('deliverables entries must be objects')
        ids = deliverable.get('acceptance', [])
        if not isinstance(ids, list) or any(not isinstance(x, str) or not x for x in ids):
            raise ValueError('acceptance must be an array of nonempty string identifiers')
        required.update(ids)
    if not required:
        raise ValueError('Completion requires a nonempty mandatory acceptance list')
    checks = verification.get('checks')
    if not isinstance(checks, list):
        raise ValueError('verification.checks must be an array')
    by_id = {}
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get('id'), str) or not check['id']:
            raise ValueError('Each acceptance check requires a nonempty id')
        if check['id'] in by_id:
            raise ValueError(f'Duplicate acceptance id: {check["id"]}')
        by_id[check['id']] = check
    missing = required - by_id.keys()
    if missing:
        raise ValueError(f'Missing mandatory acceptance checks: {sorted(missing)}')
    for key in sorted(required):
        check = by_id[key]
        if check.get('required') is False or check.get('status') != 'PASS' or check.get('exit_code') != 0:
            raise ValueError(f'{key}: Mandatory acceptance did not pass or exit code is nonzero')
        if not check.get('command'):
            raise ValueError(f'{key}: Missing executed command')
        for field in ('log', 'artifact_manifest'):
            value = check.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(f'{key}: Missing {field} evidence reference')
            readable(reference(value, verification_path.parent))
        for value in check.get('evidence', []):
            if isinstance(value, str):
                readable(reference(value, verification_path.parent))


def update(args):
    data = read_json(args.tasks)
    tasks = validate(data)
    if args.id not in tasks:
        raise ValueError(f'Task id does not exist: {args.id}')
    task = tasks[args.id]
    if args.status in ('completed', 'reused') and args.verification is None:
        raise ValueError('Setting completed or reused requires explicit --verification')
    directory = args.tasks.resolve().parent
    for field in ('status', 'analysis_status', 'owner', 'analysis', 'implementation', 'verification'):
        value = getattr(args, field)
        if value is not None:
            task[field] = normalize_reference(value, directory) if field in (
                'analysis', 'implementation', 'verification') else value
    validate(data)
    if status(task.get('status', 'pending')) in ('completed', 'reused'):
        completion(task, directory)
    save(args.tasks, data)


def markdown(data):
    tasks = validate(data)
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    def order(task):
        layer = task.get('layer')
        if layer is not None and (type(layer) is not int or layer < 0):
            raise ValueError(f'{task["id"]}: layer must be a nonnegative integer or null')
        return (layer is None, layer or 0, task['id'])
    lines = ['# SONiC component migration tasks', '',
             '| Layer | Component | Type | Rule | Source directories | Prerequisites | Status | Owner |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for task in sorted(tasks.values(), key=order):
        values = [task.get('layer') if task.get('layer') is not None else 'blocked',
                  task.get('name', task['id']), ', '.join(task.get('types', [])),
                  ', '.join(task.get('rule_files', [])), ', '.join(task.get('code_dirs', [])),
                  ', '.join(task.get('prerequisites', [])) or 'None',
                  status(task.get('status', 'pending')), task.get('owner', '')]
        lines.append('| ' + ' | '.join(cell(x) for x in values) + ' |')
    if data.get('changes'):
        lines += ['', '## Graph changes', '', '```json',
                  json.dumps(data['changes'], ensure_ascii=False, indent=2), '```']
    return '\n'.join(lines) + '\n'


def render(args):
    atomic_write(args.markdown, markdown(read_json(args.tasks)))


def facts(task):
    result = {}
    for field in GRAPH_FIELDS:
        if field in ('layer', 'blocked'):
            continue
        value = task.get(field)
        result[field] = sorted(value) if isinstance(value, list) else value
    return result


def merge(args):
    old = read_json(args.tasks)
    fresh = read_json(args.fresh)
    previous = validate(old)
    current = validate(fresh)
    added = set(current) - previous.keys()
    removed = set(previous) - current.keys()
    changed = {key for key in current.keys() & previous.keys()
               if facts(current[key]) != facts(previous[key])}
    invalid = changed | added
    while True:
        affected = {key for key, task in current.items()
                    if set(task.get('prerequisites', [])) & invalid}
        expanded = invalid | affected
        if expanded == invalid:
            break
        invalid = expanded
    result = copy.deepcopy(old)
    result['tasks'] = []
    for key, task in current.items():
        record = copy.deepcopy(previous.get(key, {}))
        for field in GRAPH_FIELDS:
            record.pop(field, None)
            if field in task:
                record[field] = copy.deepcopy(task[field])
        if key not in previous or key in invalid:
            record['status'] = 'pending_review'
        else:
            record['status'] = status(record.get('status', 'pending'))
        result['tasks'].append(record)
    retired = {task['id']: copy.deepcopy(task) for task in old.get('retired_tasks', [])
               if task['id'] not in current}
    retired.update({key: copy.deepcopy(previous[key]) for key in removed})
    result['retired_tasks'] = list(retired.values())
    for field in GRAPH_ROOT_FIELDS:
        if field in fresh:
            result[field] = copy.deepcopy(fresh[field])
    result['changes'] = {'added': sorted(added), 'removed': sorted(removed),
                         'changed': sorted(changed), 'invalidated': sorted(invalid & previous.keys())}
    validate(result)
    output = markdown(result)
    save(args.output, result)
    if args.markdown is not None:
        atomic_write(args.markdown, output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('update')
    command.add_argument('--tasks', type=Path, required=True)
    command.add_argument('--id', required=True)
    command.add_argument('--status', choices=STATUSES)
    command.add_argument('--analysis-status', choices=ANALYSIS_STATUSES)
    for name in ('owner', 'analysis', 'implementation', 'verification'):
        command.add_argument('--' + name)
    command.set_defaults(action=update)
    command = commands.add_parser('render')
    command.add_argument('--tasks', type=Path, required=True)
    command.add_argument('--markdown', type=Path, required=True)
    command.set_defaults(action=render)
    command = commands.add_parser('merge')
    command.add_argument('--tasks', type=Path, required=True)
    command.add_argument('--fresh', type=Path, required=True)
    command.add_argument('--output', type=Path, required=True)
    command.add_argument('--markdown', type=Path)
    command.set_defaults(action=merge)
    args = parser.parse_args(argv)
    try:
        args.action(args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'task-progress: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
