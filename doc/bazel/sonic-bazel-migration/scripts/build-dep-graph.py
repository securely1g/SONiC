#!/usr/bin/env python3
"""Conservative, side-effect-free SONiC Make dependency inventory.

All conditional branches are collected. This is a static inventory, not a GNU
Make evaluator: candidate edges and unresolved expressions are explicit. No
shell command, recipe or Make include is executed. See --help for output paths.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re


REF = re.compile(r'\$[({]([A-Za-z_][\w.-]*)[)}]')
ASSIGN = re.compile(r'^(.*?)\s*(::=|:=|\+=|\?=|=)\s*(.*)$')
FIELD = re.compile(r'^\$\(([\w.-]+)\)_(\w+)$')
# Fields consumed by slave.mk's package, container and installer rules.
FIELDS = {
    'DEPENDS': 'build', 'DEBS_DEPENDS': 'build', 'WHEEL_DEPENDS': 'build',
    'DBG_DEPENDS': 'build', 'PYTHON_DEBS': 'assembly', 'PYTHON_WHEELS': 'assembly',
    'LOAD_DOCKERS': 'assembly', 'INSTALL_DEBS': 'assembly',
    'INSTALL_PYTHON_WHEELS': 'assembly', 'INSTALLS': 'assembly',
    'LAZY_INSTALLS': 'assembly', 'LAZY_BUILD_INSTALLS': 'assembly',
    'DOCKERS': 'assembly', 'INCLUDE_DOCKER': 'assembly', 'RFS_DEPENDS': 'build',
    'AFTER': 'order', 'PHONIES': 'build', 'FILES': 'file', 'RDEPENDS': 'runtime',
    'MAIN_DEB': 'co-produced',
}
CATEGORIES = {
    'DEBS': ('SONIC_MAKE_DEBS', 'SONIC_DPKG_DEBS', 'SONIC_COPY_DEBS',
             'SONIC_ONLINE_DEBS', 'SONIC_DERIVED_DEBS', 'SONIC_EXTRA_DEBS',
             'SONIC_PYTHON_STDEB_DEBS'),
    'WHEELS': ('SONIC_PYTHON_WHEELS',),
    'DOCKERS': ('SONIC_DOCKER_IMAGES', 'SONIC_DOCKER_DBG_IMAGES',
                'SONIC_SIMPLE_DOCKER_IMAGES', 'SONIC_COPY_DOCKERS',
                'SONIC_ONLINE_DOCKERS', 'SONIC_DBG_DOCKERS'),
    'ONE_IMAGE': ('SONIC_ONE_IMAGE',), 'KVM_IMAGE': ('SONIC_KVM_IMAGE',),
    'RAW_IMAGE': ('SONIC_RAW_IMAGE',),
}


def literal_words(expression):
    """Return top-level literal words; never tokenize inside a Make expression."""
    words, word, depth = [], '', 0
    for char in expression:
        if char.isspace() and depth == 0:
            if word:
                words.append(word)
                word = ''
            continue
        word += char
        if char == '(':
            depth += 1
        elif char == ')' and depth:
            depth -= 1
    if word:
        words.append(word)
    return [word for word in words if '$' not in word and word not in {'|', ':', '\\'}]


def logical_lines(path):
    """Preserve first physical line number when joining continuations."""
    pending, start = '', 0
    for number, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
        if not pending:
            start = number
        if line.endswith('\\'):
            pending += line[:-1] + ' '
            continue
        yield start, pending + line
        pending = ''
    if pending:
        yield start, pending


class Inventory:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.records = []
        self.assignments = defaultdict(list)
        self.nodes = {}
        self.edges = []
        self.unresolved = []
        self.files = set()
        self.registries = defaultdict(set)
        self._edge_keys = set()

    def issue(self, reason, record=None, **details):
        item = {'reason': reason, **details}
        if record:
            item.update(source=record['source'], conditions=record['conditions'])
        if item not in self.unresolved:
            self.unresolved.append(item)

    def scan(self):
        # Seed every platform, even those absent from the configured include path.
        seeds = [self.root / 'slave.mk', self.root / 'Makefile',
                 self.root / 'Makefile.work', self.root / 'rules/config',
                 self.root / 'rules/functions']
        seeds += sorted((self.root / 'rules').glob('*.mk'))
        seeds += sorted((self.root / 'platform').rglob('*.mk'))
        for path in seeds:
            if path.is_file():
                self.read(path)
        self.index()
        self.build_edges()

    def read(self, path):
        path = path.resolve()
        if path in self.files or not path.is_relative_to(self.root):
            return
        self.files.add(path)
        conditions = []
        platform = path.relative_to(self.root).parts
        if len(platform) > 2 and platform[0] == 'platform':
            conditions.append('platform directory: ' + platform[1])
        base = len(conditions)
        in_define = False
        for number, raw in logical_lines(path):
            if raw.startswith('\t') and not re.match(
                    r'\s*(?:[\w.-]+|\$\([\w.-]+\)_\w+)\s*(?:::?=|[+?]?=)', raw):
                continue
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            source = f'{path.relative_to(self.root)}:{number}'
            record = {'text': line, 'source': source, 'conditions': list(conditions)}
            if line.startswith('define '):
                in_define = True
                continue
            if line == 'endef':
                in_define = False
                continue
            if in_define:
                continue  # Handled macro semantics below; never execute definitions.
            if re.match(r'^(ifeq|ifneq|ifdef|ifndef)\b', line):
                conditions.append(line)
                continue
            if line.startswith('else') and len(conditions) > base:
                conditions[-1] = 'else of (' + conditions[-1] + ') ' + line[4:].strip()
                continue
            if line == 'endif':
                if len(conditions) > base:
                    conditions.pop()
                continue
            include = re.match(r'^(?:-?include|sinclude)\s+(.+)', line)
            if include:
                expression = include[1]
                if '$' not in expression:
                    for token in expression.split():
                        if Path(token).is_absolute() or '..' in Path(token).parts:
                            self.issue('include outside inventory root not scanned', record, expression=token)
                            continue
                        matches = list(self.root.glob(token))
                        if not matches:
                            self.issue('include not found', record, expression=token)
                        for match in matches:
                            if match.is_file():
                                self.read(match)
                else:
                    self.issue('dynamic include not evaluated; rules/platform trees scanned independently',
                               record, expression=expression)
                continue
            self.records.append(record)
            assignment = ASSIGN.match(line)
            if assignment and ':' not in assignment[1]:
                lhs, op, rhs = assignment.groups()
                record.update(lhs=lhs.strip(), op=op, rhs=rhs.split('#', 1)[0].strip())
                if re.fullmatch(r'[\w.-]+', record['lhs']):
                    self.assignments[record['lhs']].append(record)

    def node(self, name, record=None, category=None):
        result = self.nodes.setdefault(name, {'id': name, 'aliases': [], 'categories': [],
                                             'sources': [], 'production': []})
        if record and record['source'] not in result['sources']:
            result['sources'].append(record['source'])
        if category and category not in result['categories']:
            result['categories'].append(category)
        return result

    def component_refs(self, expression, seen=None):
        """Follow collection/helper variables, stopping at component identities."""
        seen = set() if seen is None else seen
        result = set()
        # A reference to another component's metadata means its dependencies,
        # rather than a dependency on the component owning that metadata.
        metadata = re.compile(r'\$\(\$\(([\w.-]+)\)_([\w]+)\)')
        for match in metadata.finditer(expression):
            key = f'$({match[1]})_{match[2]}'
            if key not in seen:
                seen.add(key)
                for record in self.records:
                    if record.get('lhs') == key:
                        result.update(self.component_refs(record['rhs'], seen))
        expression = metadata.sub('', expression)
        for name in REF.findall(expression):
            if name in self.nodes:
                result.add(name)
            elif name not in seen:
                seen.add(name)
                for record in self.assignments.get(name, []):
                    result.update(self.component_refs(record['rhs'], seen))
        return result

    def index(self):
        for record in self.records:
            if '$(call add_derived_package' in record['text'] or '$(call add_extra_package' in record['text'] or '$(call add_dbg_docker' in record['text']:
                for name in REF.findall(record['text']):
                    self.node(name, record, 'DOCKERS' if 'add_dbg_docker' in record['text'] else 'DEBS')
        for record in self.records:
            if 'lhs' not in record:
                continue
            field = FIELD.match(record['lhs'])
            if field:
                self.node(field[1], record)
        # Registered components may have no metadata fields at all.
        for registry in {r for values in CATEGORIES.values() for r in values} | {
                'SONIC_INSTALLERS', 'SONIC_MAKE_FILES', 'SONIC_COPY_FILES',
                'SONIC_ONLINE_FILES', 'SONIC_PHONIES', 'SONIC_RFS_TARGETS'}:
            for record in self.assignments.get(registry, []):
                for name in REF.findall(record['rhs']):
                    if not name.startswith('SONIC_') or name in self.nodes:
                        self.node(name, record)
        for category, registries in CATEGORIES.items():
            for registry in registries:
                if registry in self.nodes:
                    self.node(registry, category=category)
                for record in self.assignments.get(registry, []):
                    for name in self.component_refs(record['rhs']):
                        self.node(name, record, category)
                        self.nodes[name]['production'].append(registry)
        for registry, records in self.assignments.items():
            if registry.startswith('SONIC_'):
                for record in records:
                    self.registries[registry].update(self.component_refs(record['rhs']))
        for name, node in list(self.nodes.items()):
            for record in self.assignments.get(name, []):
                rhs = record['rhs']
                # Concrete literals are useful aliases; expressions remain visible.
                if '$' not in rhs:
                    node['aliases'].extend(rhs.split())
                elif rhs:
                    self.issue('symbolic product name', record, component=name, expression=rhs)
            node['aliases'] = sorted(set(node['aliases']))
            node['production'] = sorted(set(node['production']))

    def edge(self, owner, dependency, kind, field, record, candidate=True):
        self.node(owner, record)
        self.node(dependency)
        key = (owner, dependency, kind, field, record['source'], tuple(record['conditions']))
        if key in self._edge_keys:
            return
        self._edge_keys.add(key)
        self.edges.append({'from': owner, 'to': dependency, 'kind': kind, 'field': field,
                           'source': record['source'], 'conditions': record['conditions'],
                           'candidate': candidate})

    def dependencies(self, owner, expression, kind, field, record):
        found = self.component_refs(expression)
        for dependency in sorted(found):
            self.edge(owner, dependency, kind, field, record)
        # Preserve ordinary files even alongside variable/function prerequisites.
        for token in literal_words(expression):
            aliases = {name for name, node in self.nodes.items() if token in node['aliases']}
            if aliases:
                for name in sorted(aliases):
                    self.edge(owner, name, kind, field, record)
            else:
                name = 'file:' + token
                self.node(name, record, 'FILE')
                self.edge(owner, name, 'file' if kind == 'file' else kind, field, record)
        if '$' in expression:
            unknown = sorted(set(REF.findall(expression)) - set(self.nodes) -
                             set(self.assignments))
            if unknown or '$' in REF.sub('', expression):
                self.issue('expression retained as static candidate; Make evaluation required',
                           record, component=owner, field=field, expression=expression,
                           unknown_variables=unknown)

    def build_edges(self):
        macro = re.compile(r'\$\(call\s+(add_derived_package|add_extra_package|add_dbg_docker)\s*,?\s*'
                           r'\$\(([\w.-]+)\)\s*,\s*\$\(([\w.-]+)\)')
        for record in self.records:
            field = FIELD.match(record.get('lhs', ''))
            if field and field[2] in FIELDS:
                self.dependencies(field[1], record['rhs'], FIELDS[field[2]], field[2], record)
            match = macro.search(record['text'])
            if match:
                function, main, extra = match.groups()
                self.edge(extra, main, 'co-produced' if function != 'add_dbg_docker' else 'build',
                          function, record, candidate=False)
                if function == 'add_dbg_docker':
                    # add_dbg_docker copies these dependency fields from the base.
                    for inherited in ('DEPENDS', 'DBG_DEPENDS', 'PYTHON_DEBS',
                                      'PYTHON_WHEELS', 'LOAD_DOCKERS'):
                        for original in self.records:
                            if original.get('lhs') == f'$({main})_{inherited}':
                                self.dependencies(extra, original['rhs'], FIELDS[inherited],
                                                  'add_dbg_docker:' + inherited, original)
            elif '$(call ' in record['text'] and not record.get('lhs'):
                self.issue('macro invocation not expanded', record, expression=record['text'])
            # GNU Make static/pattern rule prerequisites, including slave.mk common inputs.
            text = record['text']
            if ':' not in text or 'lhs' in record or text.startswith(('export ', 'unexport ')):
                continue
            lhs, rhs = text.split(':', 1)
            if ':=' in text or 'private export' in rhs:
                continue
            if ':' in rhs:  # static pattern: targets : target-pattern : prerequisites
                rhs = rhs.split(':', 1)[1]
            owners = self.component_refs(lhs)
            if not owners and '$' not in lhs:
                for target in lhs.split():
                    owners.update(n for n, info in self.nodes.items()
                                  if target in info['aliases'] or Path(target).name in info['aliases'])
            for owner in sorted(owners):
                # $* fields are already captured from component metadata above.
                self.dependencies(owner, rhs, 'build', 'rule prerequisites', record)

    def registered_products(self):
        """Only Make production registrations define SONiC component products."""
        registered = set()
        for registries in CATEGORIES.values():
            for registry in registries:
                registered.update(self.registries.get(registry, ()))
        registered.update(self.registries.get('SONIC_INSTALLERS', ()))
        for name, node in self.nodes.items():
            if node['categories']:
                registered.add(name)
        for edge in self.edges:
            if edge['kind'] == 'co-produced':
                registered.update((edge['from'], edge['to']))
        return {name for name in registered if not name.startswith('file:')}

    def source_directories(self, products):
        """Resolve ordinary variable-based source paths without executing Make."""
        def expand(text, seen):
            def replace(match):
                name = match[1]
                if name in seen:
                    return match[0]
                values = {expand(r['rhs'], seen | {name})
                          for r in self.assignments.get(name, ())}
                return values.pop() if len(values) == 1 else match[0]
            return REF.sub(replace, text)

        directories = set()
        for record in self.records:
            field = FIELD.match(record.get('lhs', ''))
            if field and field[1] in products and field[2] in {'SRC_PATH', 'PATH'}:
                resolved = expand(record['rhs'], set())
                if resolved and '$' not in resolved:
                    directories.update(resolved.split())
        return sorted(directories)

    def component_type(self, products):
        types = set()
        categories = {'DEBS': 'DEB', 'WHEELS': 'WHEEL', 'DOCKERS': 'DOCKER',
                      'ONE_IMAGE': 'ONE_IMAGE', 'KVM_IMAGE': 'KVM_IMAGE',
                      'RAW_IMAGE': 'RAW_IMAGE'}
        for product in products:
            types.update(categories[c] for c in self.nodes[product]['categories'] if c in categories)
        for record in self.records:
            field = FIELD.match(record.get('lhs', ''))
            if field and field[1] in products and field[2] == 'IMAGE_TYPE':
                image_type = {'onie': 'ONE_IMAGE', 'kvm': 'KVM_IMAGE', 'raw': 'RAW_IMAGE'}.get(record['rhs'])
                if image_type:
                    types.add(image_type)
        return sorted(types)

    def graph(self, inputs):
        registered = self.registered_products()
        mappings = {}
        issues = []
        for value in inputs:
            category = {'DEB': 'DEBS', 'WHEEL': 'WHEELS', 'DOCKER': 'DOCKERS'}.get(value, value)
            if category in CATEGORIES:
                roots = {name for name in registered if category in self.nodes[name]['categories']}
            elif value in registered:
                roots = {value}
            else:
                roots = {name for name in registered
                         if value in self.nodes[name]['aliases'] or Path(value).name in self.nodes[name]['aliases']}
            mappings[value] = sorted(roots)
            if not roots:
                issues.append({'reason': 'SONiC component input not resolved', 'input': value})
        roots = set().union(*map(set, mappings.values())) if inputs else set(registered)
        adjacency = defaultdict(set)
        co_products = defaultdict(set)
        productions = []
        for edge in self.edges:
            if edge['from'] not in registered:
                continue
            if edge['to'] not in registered and not edge['to'].startswith('file:'):
                continue
            adjacency[edge['from']].add(edge['to'])
            if edge['kind'] == 'co-produced':
                main, extra = edge['to'], edge['from']
                productions.append((main, extra))
                # Selecting any output selects its entire production group.
                # Keep this traversal separate from directed dependency edges.
                co_products[main].add(extra)
                co_products[extra].add(main)
        selected, pending = set(), list(roots)
        while pending:
            name = pending.pop()
            if name not in selected:
                selected.add(name)
                pending.extend((adjacency[name] | co_products[name]) - selected)
        edges = [e for e in self.edges if e['from'] in selected and e['to'] in selected
                 and e['from'] in registered]
        # Only explicit co-production contracts justify collapsing output nodes.
        parent = {n: n for n in selected if n in registered}

        def find(n):
            while parent[n] != n:
                parent[n] = parent[parent[n]]
                n = parent[n]
            return n

        for main, extra in productions:
            if main in parent and extra in parent:
                parent[find(extra)] = find(main)
        groups = defaultdict(list)
        for node in parent:
            groups[find(node)].append(node)
        task_of = {node: main for main, members in groups.items() for node in members}
        prerequisites = {main: set() for main in groups}
        for edge in edges:
            a, b = task_of.get(edge['from']), task_of.get(edge['to'])
            if a and b and edge['kind'] not in {'runtime', 'co-produced'} and (a != b or edge['from'] == edge['to']):
                prerequisites[a].add(b)
        layers, remaining = [], set(groups)
        while remaining:
            ready = sorted(n for n in remaining if not prerequisites[n] & remaining)
            if not ready:
                break
            layers.append(ready)
            remaining.difference_update(ready)
        # Enumerate strongly connected sets without inventing an order for cycles.
        cycles = strongly_connected(prerequisites)
        diagnostics = [i for i in self.unresolved if 'component' not in i or i['component'] in selected]
        tasks = [{'id': main, 'products': sorted(members),
                  'prerequisites': sorted(prerequisites[main]), 'status': 'pending',
                  'layer': next((i for i, layer in enumerate(layers) if main in layer), None),
                  'blocked': main in remaining}
                 for main, members in sorted(groups.items())]
        for task in tasks:
            members = set(task['products'])
            task['name'] = task['id']
            task['types'] = self.component_type(members)
            task['type'] = task['types'][0] if len(task['types']) == 1 else None
            task['rule_files'] = sorted({r['source'].rsplit(':', 1)[0]
                                        for member in members
                                        for r in self.assignments.get(member, ())
                                        if r['source'].rsplit(':', 1)[0].endswith('.mk')}
                                       | {e['source'].rsplit(':', 1)[0] for e in edges
                                          if e['kind'] == 'co-produced' and e['from'] in members
                                          and e['source'].rsplit(':', 1)[0].endswith('.mk')})
            task['code_dirs'] = self.source_directories(members)
            if not task['rule_files']:
                issues.append({'reason': 'SONiC component rule ownership not found',
                               'component': task['id']})
            if not task['types']:
                issues.append({'reason': 'SONiC component type not resolved',
                               'component': task['id']})
        for cycle in cycles:
            issues.append({'reason': 'SONiC component dependency cycle', 'components': cycle})
        deps = {name: sorted(adjacency[name] & selected) for name in sorted(selected)}
        reverse = defaultdict(list)
        for name, values in deps.items():
            for dep in values:
                reverse[dep].append(name)
        return {'schema_version': 3, 'analysis': 'all-conditions registered SONiC component inventory',
                'complete': not issues,
                'completeness_scope': 'Registered SONiC product ownership, types and statically identified component relations.',
                'limitations': ['No Make evaluation or recipes executed.',
                                'Variable identities merge alternative platform/configuration products.',
                                'Dynamic SONiC component relationships may remain unresolved.',
                                'System build-tool requirements belong to component analysis, not this graph.',
                                'Conditions are declaration annotations, not satisfiability proofs.'],
                'inputs': mappings, 'files': sorted(str(p.relative_to(self.root)) for p in self.files),
                'nodes': [self.nodes[n] for n in sorted(selected)], 'edges': edges,
                'tasks': tasks, 'product_to_task': task_of, 'layers': layers,
                'cycles': [{'tasks': members, 'edges': [e for e in edges
                            if task_of.get(e['from']) in members and task_of.get(e['to']) in members]}
                           for members in cycles],
                'blocked_tasks': sorted(remaining), 'issues': issues, 'diagnostics': diagnostics,
                'deps': deps, 'rdeps': dict(reverse),
                'after': {n: sorted({e['to'] for e in edges if e['from'] == n and e['kind'] == 'order'})
                          for n in sorted(selected)}}


def strongly_connected(adjacency):
    """Tarjan SCC; include self-loops, exclude acyclic singleton nodes."""
    indices, low, stack, active, result = {}, {}, [], set(), []

    def visit(node):
        indices[node] = low[node] = len(indices)
        stack.append(node)
        active.add(node)
        for dep in sorted(adjacency[node]):
            if dep not in indices:
                visit(dep)
                low[node] = min(low[node], low[dep])
            elif dep in active:
                low[node] = min(low[node], indices[dep])
        if low[node] == indices[node]:
            group = []
            while True:
                member = stack.pop()
                active.remove(member)
                group.append(member)
                if member == node:
                    break
            if len(group) > 1 or node in adjacency[node]:
                result.append(sorted(group))

    for node in sorted(adjacency):
        if node not in indices:
            visit(node)
    return sorted(result)


def component_graph(graph):
    """Project the internal product inventory to the scheduler's component graph."""
    task_of = graph['product_to_task']
    inputs = {value: sorted({task_of[root] for root in roots if root in task_of})
              for value, roots in graph['inputs'].items()}
    fields = ('id', 'name', 'type', 'types', 'rule_files', 'code_dirs')
    components = [{key: task[key] for key in fields} for task in graph['tasks']]
    relations = {}
    for edge in graph['edges']:
        owner, dependency = task_of.get(edge['from']), task_of.get(edge['to'])
        if not owner or not dependency or owner == dependency:
            continue
        key = (owner, dependency, edge['kind'])
        relation = relations.setdefault(key, {
            'from': owner, 'to': dependency, 'kind': edge['kind'],
            'evidence': [],
        })
        evidence = {'source': edge['source']}
        if evidence not in relation['evidence']:
            relation['evidence'].append(evidence)
    for relation in relations.values():
        relation['evidence'].sort(key=lambda item: item['source'])
    return {'schema_version': 4, 'inputs': inputs, 'components': components,
            'edges': [relations[key] for key in sorted(relations)],
            'issues': graph['issues']}


def write_outputs(graph, prefix, task_prefix=None):
    task_prefix = task_prefix or prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    scheduling_graph = component_graph(graph)
    prefix.with_suffix('.json').write_text(json.dumps(scheduling_graph, indent=2, ensure_ascii=False) + '\n')
    dot = ['digraph sonic_build {', '  rankdir=LR;']
    for component in scheduling_graph['components']:
        dot.append('  ' + json.dumps(component['id']) + ';')
    for edge in scheduling_graph['edges']:
        label = edge['kind'] + '\\n' + ', '.join(item['source'] for item in edge['evidence'])
        dot.append(f'  {json.dumps(edge["from"])} -> {json.dumps(edge["to"])} '
                   f'[label={json.dumps(label)}];')
    dot.append('}')
    prefix.with_suffix('.dot').write_text('\n'.join(dot) + '\n')
    lines = ['# SONiC component migration tasks', '',
             '| Layer | Component | Type | Rule | Source directories | Prerequisites | Status |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for task in sorted(graph['tasks'], key=lambda item: (item['layer'] is None, item['layer'] or 0, item['id'])):
        values = [str(task['layer']) if task['layer'] is not None else 'blocked', task['name'],
                  ', '.join(task['types']), ', '.join(task['rule_files']),
                  ', '.join(task['code_dirs']) or 'unconfirmed',
                  ', '.join(task['prerequisites']) or 'None', 'pending']
        lines.append('| ' + ' | '.join(value.replace('|', '\\|') for value in values) + ' |')
    if graph['issues']:
        lines += ['', '## Scheduling issues', '']
        for issue in graph['issues']:
            lines.append('- ' + json.dumps(issue, ensure_ascii=False))
    if task_prefix != prefix:
        task_prefix.with_suffix('.json').write_text(json.dumps({
            'inputs': graph['inputs'], 'tasks': graph['tasks'],
            'product_to_task': graph['product_to_task'], 'layers': graph['layers'],
            'blocked_tasks': graph['blocked_tasks'], 'complete': graph['complete'],
            'issues': graph['issues'],
        }, indent=2, ensure_ascii=False) + '\n')
    task_prefix.with_suffix('.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base_dir', nargs='?', default='.', help='SONiC buildimage root (legacy positional argument)')
    parser.add_argument('--component', action='append', default=[], metavar='NAME',
                        help='variable, concrete target or DEBS/WHEELS/DOCKERS/ONE_IMAGE/KVM_IMAGE/RAW_IMAGE; repeatable')
    parser.add_argument('--output-prefix', type=Path,
                        help='output prefix for .json/.dot/.md; defaults to ROOT/target/build-dep-graph')
    parser.add_argument('--output-dir', type=Path,
                        help='write graph.json/graph.dot and tasks.json/tasks.md in this directory')
    args = parser.parse_args()
    if args.output_dir and args.output_prefix:
        parser.error('--output-dir and --output-prefix are mutually exclusive')
    inventory = Inventory(args.base_dir)
    if not (inventory.root / 'rules').is_dir():
        parser.error(f'{inventory.root}/rules not found')
    inventory.scan()
    graph = inventory.graph(args.component)
    prefix = (args.output_dir / 'graph' if args.output_dir else
              args.output_prefix or inventory.root / 'target/build-dep-graph')
    write_outputs(graph, prefix, args.output_dir / 'tasks' if args.output_dir else None)
    print(f'{len(graph["nodes"])} nodes, {len(graph["edges"])} candidate edges, '
          f'{len(graph["tasks"])} tasks, {len(graph["layers"])} layers, '
          f'{len(graph["cycles"])} cycles, {len(graph["issues"])} scheduling issues')
    print(f'Component inventory complete: {graph["complete"]}. Graph: {prefix}.json/.dot')
    print('Task checklist: ' + str(args.output_dir / 'tasks.md' if args.output_dir else prefix.with_suffix('.md')))
    return 2 if any(not roots for roots in graph['inputs'].values()) else 0


if __name__ == '__main__':
    raise SystemExit(main())
