"""Contract: preserve conditions/evidence, read-only collection and separation of artifacts from source versions."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/analyze-make-component.py'


class CollectionContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / 'source'
        self.src.mkdir()
        (self.src / 'debian').mkdir()
        (self.src / 'debian/control').write_text('Source: example\nBuild-Depends: gcc, libz-dev\n\nPackage: example-dev\nArchitecture: any\n\nPackage: example\nArchitecture: any\n')
        (self.src / 'debian/changelog').write_text('example (7.2-3) unstable; urgency=low\n')
        (self.src / 'a.c').write_text('int main(void) { return 0; }\n')
        self.marker = self.root / 'executed'
        (self.src / 'Makefile').write_text(f'X := $(shell touch {self.marker})\nifeq ($(ARCH),one)\nCFLAGS += -DFIRST\nelse\nCFLAGS += -DSECOND\nendif\n')

    def invoke(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), 'component.a', '--repo', str(self.root),
                               '--source-dir', 'source', '--output-dir', str(self.root / 'out'), *extra],
                              text=True, capture_output=True)

    def result(self):
        return json.loads((self.root / 'out/components/component.a/analysis.json').read_text())

    def test_preserves_conditions_without_executing_make(self):
        p = self.invoke()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(self.marker.exists())
        report = self.result()
        ref = self.root / 'out/components/component.a/evidence/build-declarations.json'
        records = json.loads(ref.read_text())
        first = next(r for r in records if '-DFIRST' in r['text'])
        second = next(r for r in records if '-DSECOND' in r['text'])
        self.assertEqual(first['conditions'], ['ifeq ($(ARCH),one)'])
        self.assertIn('else of', second['conditions'][0])
        self.assertNotEqual(report['analysis_status'], 'analysis_complete')
        packages = [p for item in report['outputs']['value'] for p in item.get('packages', [])]
        self.assertEqual(set(packages), {'example', 'example-dev'})

    def test_compile_database_and_wheel_preserve_provenance(self):
        db = self.root / 'compile_commands.json'
        db.write_text(json.dumps([{'file': 'a.c', 'directory': str(self.src), 'arguments': ['gcc', '-DOBSERVED', '-c', 'a.c']}]))
        wheel = self.root / 'example.whl'
        with zipfile.ZipFile(wheel, 'w') as archive:
            archive.writestr('example/__init__.py', '')
            archive.writestr('example-7.2.dist-info/METADATA', 'Name: example\nVersion: 7.2\n')
        p = self.invoke('--compile-db', str(db), '--artifact', str(wheel), '--provenance', 'commit-abc', '--configuration', 'ARCH=two')
        self.assertEqual(p.returncode, 0, p.stderr)
        report = self.result()
        observed = next(x for x in report['compile_commands']['value'] if 'commands' in x)
        self.assertEqual(observed['provenance'], 'commit-abc')
        self.assertEqual(observed['configuration'], ['ARCH=two'])
        package = report['package_contents']['value'][0]
        self.assertEqual(package['source_version_match'], 'unconfirmed')
        evidence = json.loads((self.root / 'out/components/component.a/evidence/artifact-0.json').read_text())
        self.assertEqual({x['path'] for x in evidence['contents']}, {'example/__init__.py', 'example-7.2.dist-info/METADATA'})

    def test_existing_analysis_requires_explicit_overwrite(self):
        self.assertEqual(self.invoke().returncode, 0)
        before = self.result()
        p = self.invoke()
        self.assertEqual(p.returncode, 2)
        self.assertEqual(self.result(), before)

    def test_invalid_database_is_reported(self):
        db = self.root / 'invalid.json'
        db.write_text('[{"file":"a.c"}]')
        p = self.invoke('--compile-db', str(db))
        self.assertEqual(p.returncode, 2)
        self.assertIn('Invalid compilation database', p.stderr)


if __name__ == '__main__':
    unittest.main()
