"""User contract: inventory all branches, source every edge, order dependencies.

These miniature Makefiles are hand-checkable independent specifications of Make
relationships. Tests observe the exported graph, not parser implementation.
They catch branch exclusion, dropped debug/shared outputs, false topological
ordering and accidental execution of untrusted build expressions.
"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    'build_dep_graph', Path(__file__).resolve().parents[1] / 'scripts' / 'build-dep-graph.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DependencyInventoryTest(unittest.TestCase):
    def graph(self, files, roots):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'rules').mkdir()
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            inventory = MODULE.Inventory(root)
            inventory.scan()
            return inventory.graph(roots)

    def test_all_branches_and_dependency_first_layers(self):
        graph = self.graph({'rules/a.mk': '''A = a.deb
B = b.deb
C = c.deb
SONIC_MAKE_DEBS += $(A) $(B) $(C)
ifeq ($(ARCH),one)
$(A)_DEPENDS += $(B)
else
$(A)_DEPENDS += $(C)
endif
'''}, ['a.deb'])
        self.assertEqual(graph['inputs'], {'a.deb': ['A']})
        self.assertEqual(set(graph['deps']['A']), {'B', 'C'})
        edges = [e for e in graph['edges'] if e['from'] == 'A']
        self.assertTrue(all(e['conditions'] and e['source'].startswith('rules/a.mk:') for e in edges))
        self.assertEqual(graph['layers'], [['B', 'C'], ['A']])

    def test_platform_include_public_prerequisite_and_shared_outputs(self):
        graph = self.graph({
            'platform/test/image.mk': '''SONIC_KVM_IMAGE = test.img.gz
SONIC_INSTALLERS += $(SONIC_KVM_IMAGE)
$(SONIC_KVM_IMAGE)_INSTALLS += $(CHILD)
''', 'rules/a.mk': '''BASE = base.deb
CHILD = child.deb
KERNEL = kernel.deb
SONIC_MAKE_DEBS += $(BASE) $(KERNEL)
$(eval $(call add_derived_package,$(BASE),$(CHILD)))
include extra/requirements.mk
''', 'extra/requirements.mk': '$(BASE)_DEPENDS += $(KERNEL)\n',
            'slave.mk': '$(addprefix target/,$(SONIC_INSTALLERS)): target/%: $(KERNEL)\n',
        }, ['KVM_IMAGE'])
        self.assertEqual(set(graph['deps']['SONIC_KVM_IMAGE']), {'CHILD', 'KERNEL'})
        self.assertEqual(graph['product_to_task']['BASE'], graph['product_to_task']['CHILD'])
        self.assertIn('extra/requirements.mk', graph['files'])
        self.assertLess(next(t['layer'] for t in graph['tasks'] if t['id'] == 'KERNEL'),
                        next(t['layer'] for t in graph['tasks'] if t['id'] == 'BASE'))

    def test_conditional_cycle_and_downstream_are_blocked(self):
        graph = self.graph({'rules/a.mk': '''A = a.deb
B = b.deb
C = c.deb
SONIC_MAKE_DEBS += $(A) $(B) $(C)
ifdef X
$(A)_DEPENDS += $(B)
else
$(B)_DEPENDS += $(A)
endif
$(C)_DEPENDS += $(A)
'''}, ['C'])
        self.assertEqual(graph['blocked_tasks'], ['A', 'B', 'C'])
        self.assertEqual(graph['cycles'][0]['tasks'], ['A', 'B'])
        self.assertEqual(graph['layers'], [])
        self.assertTrue(graph['cycles'][0]['edges'])

    def test_debug_docker_and_runtime_relationship(self):
        graph = self.graph({'rules/a.mk': '''DOCKER = docker.gz
DBG = docker-dbg.gz
PKG = pkg.deb
RUNTIME = runtime.deb
SONIC_DOCKER_IMAGES += $(DOCKER)
SONIC_MAKE_DEBS += $(PKG) $(RUNTIME)
$(DOCKER)_DEPENDS += $(PKG)
$(PKG)_RDEPENDS += $(RUNTIME)
$(eval $(call add_dbg_docker,$(DOCKER),$(DBG)))
'''}, ['DBG'])
        self.assertIn('PKG', graph['deps']['DBG'])
        self.assertIn('RUNTIME', graph['deps']['PKG'])
        self.assertEqual(next(t for t in graph['tasks'] if t['id'] == 'PKG')['prerequisites'], [])

    def test_metadata_reference_means_dependencies_not_owner(self):
        graph = self.graph({'rules/a.mk': """A = a.deb
B = b.deb
C = c.deb
SONIC_MAKE_DEBS += $(A) $(B) $(C)
$(A)_DEPENDS += $(B)
$(C)_DEPENDS += $($(A)_DEPENDS)
"""}, ['C'])
        self.assertEqual(graph['deps']['C'], ['B'])
        self.assertNotIn('A', graph['product_to_task'])

    def test_any_output_selects_complete_production_group_and_dependency_closure(self):
        # User contract: a production task includes all declared outputs across
        # conditions, and dependencies contributed by any of those outputs.
        files = {'rules/packages.mk': """MAIN = main.deb
EXTRA = extra.deb
DERIVED = derived.deb
OPTIONAL = optional.deb
LEAF = leaf.deb
LEAF_DBG = leaf-debug.deb
UNRELATED = unrelated.deb
SONIC_MAKE_DEBS += $(MAIN) $(LEAF) $(UNRELATED)
$(eval $(call add_extra_package,$(MAIN),$(EXTRA)))
$(eval $(call add_derived_package,$(EXTRA),$(DERIVED)))
ifdef FEATURE
$(eval $(call add_extra_package,$(MAIN),$(OPTIONAL)))
$(OPTIONAL)_DEPENDS += $(LEAF)
endif
$(eval $(call add_extra_package,$(LEAF),$(LEAF_DBG)))
$(EXTRA)_DEPENDS += $(DERIVED)
"""}
        for root in ('MAIN', 'EXTRA', 'DERIVED', 'OPTIONAL', 'main.deb', 'derived.deb'):
            with self.subTest(root=root):
                graph = self.graph(files, [root])
                tasks = {task['id']: task for task in graph['tasks']}
                self.assertEqual(set(tasks), {'MAIN', 'LEAF'})
                self.assertEqual(tasks['MAIN']['products'], ['DERIVED', 'EXTRA', 'MAIN', 'OPTIONAL'])
                self.assertEqual(tasks['LEAF']['products'], ['LEAF', 'LEAF_DBG'])
                self.assertEqual(tasks['MAIN']['prerequisites'], ['LEAF'])
                self.assertEqual(graph['layers'], [['LEAF'], ['MAIN']])
                self.assertEqual(graph['cycles'], [])
                self.assertEqual(graph['product_to_task']['DERIVED'], 'MAIN')
                optional = next(edge for edge in graph['edges']
                                if edge['from'] == 'OPTIONAL' and edge['to'] == 'MAIN')
                self.assertEqual(optional['conditions'], ['ifdef FEATURE'])
                self.assertTrue(optional['source'].startswith('rules/packages.mk:'))

    def test_explicit_main_deb_field_preserves_all_outputs(self):
        graph = self.graph({'rules/packages.mk': """MAIN = main.deb
CHILD = child.deb
SONIC_MAKE_DEBS += $(MAIN)
$(CHILD)_MAIN_DEB = $(MAIN)
"""}, ['MAIN'])
        self.assertEqual(graph['tasks'][0]['products'], ['CHILD', 'MAIN'])
        self.assertEqual(graph['product_to_task'], {'CHILD': 'MAIN', 'MAIN': 'MAIN'})

    def test_file_inputs_remain_outside_component_tasks(self):
        graph = self.graph({'rules/packages.mk': """MAIN = main.deb
SONIC_MAKE_DEBS += $(MAIN)
$(MAIN)_FILES += config.template
"""}, ['MAIN'])
        self.assertIn('file:config.template', graph['deps']['MAIN'])
        self.assertEqual([task['id'] for task in graph['tasks']], ['MAIN'])
        self.assertNotIn('file:config.template', graph['product_to_task'])
        self.assertEqual(graph['tasks'][0]['prerequisites'], [])

    def test_same_rule_file_keeps_distinct_registered_components(self):
        # User contract: component identity is a registered build object, not a
        # Makefile or an arbitrary variable referenced in a metadata field.
        files = {'rules/packages.mk': """A = a.deb
B = b.deb
BISON = bison
VERSION = 99
SONIC_MAKE_DEBS += $(A) $(B)
$(BISON)_VERSION = $(VERSION)
$(A)_DEPENDS += $(B) $(BISON) $(VERSION)
"""}
        by_variable = self.graph(files, ['A'])
        by_alias = self.graph(files, ['a.deb'])
        self.assertEqual(by_variable['tasks'], by_alias['tasks'])
        self.assertEqual([task['id'] for task in by_variable['tasks']], ['A', 'B'])
        self.assertEqual([task['type'] for task in by_variable['tasks']], ['DEB', 'DEB'])
        self.assertEqual(by_variable['product_to_task'], {'A': 'A', 'B': 'B'})
        self.assertEqual(by_variable['layers'], [['B'], ['A']])

    def test_make_diagnostics_are_separate_from_component_scheduling(self):
        graph = self.graph({'rules/a.mk': """A = a_$(VERSION).deb
VERSION = 1
SRC_PATH = src
SONIC_MAKE_DEBS += $(A)
$(A)_SRC_PATH = $(SRC_PATH)/sonic-a
include $(DYNAMIC_RULE)
"""}, ['A'])
        self.assertTrue(graph['complete'])
        self.assertEqual(graph['issues'], [])
        self.assertTrue(graph['diagnostics'])
        self.assertEqual(graph['tasks'][0]['rule_files'], ['rules/a.mk'])
        self.assertEqual(graph['tasks'][0]['code_dirs'], ['src/sonic-a'])
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'graph'
            task_prefix = Path(directory) / 'tasks'
            MODULE.write_outputs(graph, prefix, task_prefix)
            checklist = task_prefix.with_suffix('.md').read_text()
            self.assertIn('src/sonic-a', checklist)
            self.assertNotIn('dynamic include', checklist)
            self.assertNotIn('blocked', checklist)
            self.assertNotIn('Scheduling issues', checklist)

    def test_external_graph_contains_only_component_scheduling_relations(self):
        # User contract: graph.json is the scheduler interface, with derived
        # inputs mapped to their production task and only cross-component edges.
        graph = self.graph({'rules/packages.mk': """MAIN = main.deb
EXTRA = extra.deb
DEP = dependency.deb
TOOL = bison
SONIC_MAKE_DEBS += $(MAIN) $(DEP)
$(TOOL)_VERSION = 1
$(eval $(call add_extra_package,$(MAIN),$(EXTRA)))
ifdef FEATURE
$(EXTRA)_DEPENDS += $(DEP) $(TOOL)
endif
$(MAIN)_DEPENDS += $(DEP)
$(MAIN)_FILES += config.template
"""}, ['EXTRA'])
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'graph'
            tasks_prefix = Path(directory) / 'tasks'
            MODULE.write_outputs(graph, prefix, tasks_prefix)
            output = json.loads(prefix.with_suffix('.json').read_text())
            self.assertEqual(set(output), {'schema_version', 'inputs', 'components', 'edges', 'issues'})
            self.assertEqual(output['inputs'], {'EXTRA': ['MAIN']})
            self.assertEqual({c['id'] for c in output['components']}, {'MAIN', 'DEP'})
            self.assertTrue(all(set(c) == {'id', 'name', 'type', 'types', 'rule_files', 'code_dirs'}
                                for c in output['components']))
            self.assertEqual(len(output['edges']), 1)
            edge = output['edges'][0]
            self.assertEqual((edge['from'], edge['to'], edge['kind']), ('MAIN', 'DEP', 'build'))
            self.assertEqual(len(edge['evidence']), 2)
            self.assertCountEqual(edge['evidence'],
                             [{'source': 'rules/packages.mk:9'},
                              {'source': 'rules/packages.mk:11'}])
            # The scheduling graph is the union of all branches; build
            # conditions belong to component analysis, not this interface.
            self.assertNotIn('conditions', prefix.with_suffix('.json').read_text())
            dot = prefix.with_suffix('.dot').read_text()
            self.assertIn('"MAIN" -> "DEP"', dot)
            self.assertNotIn('EXTRA', dot)
            self.assertNotIn('TOOL', dot)
            self.assertNotIn('file:', dot)
            tasks = json.loads(tasks_prefix.with_suffix('.json').read_text())
            self.assertEqual(tasks['product_to_task']['EXTRA'], 'MAIN')
            self.assertEqual(next(t for t in tasks['tasks'] if t['id'] == 'MAIN')['status'], 'pending')

    def test_shell_is_not_executed_and_unresolved_input_is_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / 'unsafe'
            graph = self.graph({'rules/a.mk': f'''A = a.deb
SONIC_MAKE_DEBS += $(A)
$(A)_DEPENDS += $(shell touch {sentinel}) $(MISSING)
'''}, ['A', 'unknown.deb'])
            self.assertFalse(sentinel.exists())
            self.assertFalse(graph['complete'])
            self.assertEqual(graph['inputs']['unknown.deb'], [])
            self.assertTrue(any(i.get('unknown_variables') == ['MISSING'] for i in graph['diagnostics']))


if __name__ == '__main__':
    unittest.main()
