"""CLI contract for task updates, truthful progress and safe dependency refresh.

The independent requirements are phase-handoff.md sections 2/3 and SKILL.md's
status table. Fixtures are handwritten task graphs and evidence documents.
Tests observe public JSON/Markdown files and exit statuses, never script helpers.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "task-progress.py"


def task(name, prerequisites=(), layer=0, status="pending_review"):
    return {
        "id": name,
        "name": name,
        "products": [name.lower() + ".deb"],
        "prerequisites": list(prerequisites),
        "layer": layer,
        "type": "DEB",
        "types": ["DEB"],
        "rule_files": ["rules/" + name.lower() + ".mk"],
        "code_dirs": ["src/" + name.lower()],
        "status": status,
    }


class TaskProgressCLI(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="task-progress-contract-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.tasks = self.root / "tasks.json"
        self.markdown = self.root / "tasks.md"
        self.write(self.tasks, {"tasks": [task("SERVICE_A"), task("SERVICE_B", ["SERVICE_A"], 1)]})

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def load(self, path=None):
        return json.loads((path or self.tasks).read_text())

    def cli(self, command, *arguments, success=True):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), command, "--tasks", str(self.tasks),
             *map(str, arguments)], cwd=self.root, text=True, capture_output=True,
        )
        detail = result.stdout + result.stderr
        if success:
            self.assertEqual(result.returncode, 0, detail)
        else:
            self.assertNotEqual(result.returncode, 0, detail)
            self.assertTrue(detail.strip(), "failure must include a diagnostic")
        return result

    def tasks_by_id(self, value=None):
        return {entry["id"]: entry for entry in (value or self.load())["tasks"]}

    def evidence(self, required=("runtime_layout",), checks=None):
        component = self.root / "components" / "SERVICE_A"
        component.mkdir(parents=True, exist_ok=True)
        self.write(component / "analysis.json", {"task_id": "SERVICE_A", "package_contents": {"value": []}})
        implementation = {
            "task_id": "SERVICE_A",
            "deliverables": [{"install_target": "//:runtime", "acceptance": list(required)}],
        }
        self.write(component / "implementation.json", implementation)
        if checks is None:
            checks = [{"id": name, "required": True, "status": "PASS", "exit_code": 0,
                       "command": ["check-installation"],
                       "artifact_manifest": "evidence/" + name + ".json",
                       "log": "evidence/" + name + ".log"} for name in required]
        for check in checks:
            for field in ("artifact_manifest", "log"):
                if check.get(field):
                    destination = component / check[field]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text("{}\n" if field == "artifact_manifest" else "fixture evidence\n")
        verification = component / "verification.json"
        self.write(verification, {"task_id": "SERVICE_A", "checks": checks})
        record = self.load()
        record["tasks"][0].update({
            "status": "pending_verification",
            "analysis_status": "analysis_complete",
            "analysis": "components/SERVICE_A/analysis.json",
            "implementation": "components/SERVICE_A/implementation.json",
        })
        self.write(self.tasks, record)
        return component, verification

    def completion(self, verification, status="completed", success=True):
        return self.cli("update", "--id", "SERVICE_A", "--status", status,
                        "--verification", verification, success=success)

    def test_update_changes_only_explicit_fields(self):
        original = self.load()
        original["owner_policy"] = {"preserve": True}
        original["tasks"][0].update({"owner": "previous-owner", "notes": {"reason": "retain"},
                                     "inputs": {"commit": "source-v1"}, "analysis": "old-analysis.json"})
        original["tasks"][1].update({"owner": "unrelated-owner", "status": "blocked"})
        self.write(self.tasks, original)
        analysis = self.root / "components" / "SERVICE_A" / "analysis.json"
        self.write(analysis, {"task_id": "SERVICE_A"})
        self.cli("update", "--id", "SERVICE_A", "--status", "in_progress", "--analysis-status", "analysis_complete",
                 "--owner", "new-owner", "--analysis", analysis)
        updated = self.load()
        first = updated["tasks"][0]
        self.assertEqual(first["status"], "in_progress")
        self.assertEqual(first["analysis_status"], "analysis_complete")
        self.assertEqual(first["owner"], "new-owner")
        reference = Path(first["analysis"])
        self.assertEqual((reference if reference.is_absolute() else self.root / reference).resolve(), analysis)
        for field in ("products", "prerequisites", "layer", "notes", "inputs"):
            self.assertEqual(first[field], original["tasks"][0][field])
        self.assertEqual(updated["tasks"][1], original["tasks"][1])
        self.assertEqual(updated["owner_policy"], original["owner_policy"])

    def test_update_accepts_all_declared_nonfinal_states(self):
        for state in ("pending_review", "pending_migration", "in_progress", "pending_verification", "blocked"):
            with self.subTest(state=state):
                self.cli("update", "--id", "SERVICE_A", "--status", state)
                self.assertEqual(self.tasks_by_id()["SERVICE_A"]["status"], state)
        for state in ("pending_analysis", "analyzing", "analysis_complete", "analysis_blocked"):
            with self.subTest(analysis_state=state):
                self.cli("update", "--id", "SERVICE_A", "--analysis-status", state)
                self.assertEqual(self.tasks_by_id()["SERVICE_A"]["analysis_status"], state)

    def test_update_bad_id_or_state_preserves_original(self):
        for arguments in (("--id", "MISSING", "--status", "in_progress"),
                          ("--id", "SERVICE_A", "--status", "success"),
                          ("--id", "SERVICE_A", "--analysis-status", "PASS")):
            with self.subTest(arguments=arguments):
                before = self.tasks.read_bytes()
                self.cli("update", *arguments, success=False)
                self.assertEqual(self.tasks.read_bytes(), before)

    def test_update_duplicate_ids_preserves_original(self):
        self.write(self.tasks, {"tasks": [task("SERVICE_A"), task("SERVICE_A")]})
        before = self.tasks.read_bytes()
        self.cli("update", "--id", "SERVICE_A", "--status", "in_progress", success=False)
        self.assertEqual(self.tasks.read_bytes(), before)

    def test_completion_and_reuse_accept_valid_required_evidence(self):
        _, verification = self.evidence(required=("runtime_layout", "native_interface"))
        for state in ("completed", "reused"):
            with self.subTest(state=state):
                self.completion(verification, status=state)
                updated = self.tasks_by_id()["SERVICE_A"]
                self.assertEqual(updated["status"], state)
                reference = Path(updated["verification"])
                self.assertEqual((reference if reference.is_absolute() else self.root / reference).resolve(), verification)

    def test_completion_requires_verification_argument_and_implementation(self):
        before = self.tasks.read_bytes()
        self.cli("update", "--id", "SERVICE_A", "--status", "completed", success=False)
        self.assertEqual(self.tasks.read_bytes(), before)
        verification = self.root / "verification.json"
        self.write(verification, {"task_id": "SERVICE_A", "checks": [{"id": "layout", "status": "PASS"}]})
        self.completion(verification, success=False)
        self.assertEqual(self.tasks.read_bytes(), before)

    def test_completion_rejects_empty_acceptance(self):
        _, verification = self.evidence(required=())
        before = self.tasks.read_bytes()
        self.completion(verification, success=False)
        self.assertEqual(self.tasks.read_bytes(), before)

    def test_completion_rejects_missing_or_duplicate_check_ids(self):
        component, verification = self.evidence(required=("runtime_layout", "native_interface"))
        original = json.loads(verification.read_text())
        malformed = [original["checks"][:1], original["checks"] + [copy.deepcopy(original["checks"][0])]]
        for checks in malformed:
            with self.subTest(check_ids=[check["id"] for check in checks]):
                self.write(verification, {"task_id": "SERVICE_A", "checks": checks})
                before = self.tasks.read_bytes()
                self.completion(verification, success=False)
                self.assertEqual(self.tasks.read_bytes(), before)

    def test_completion_rejects_all_nonpass_required_states(self):
        _, verification = self.evidence()
        original = json.loads(verification.read_text())
        for state in ("FAIL", "NOT_RUN", "BLOCKED"):
            with self.subTest(state=state):
                value = copy.deepcopy(original)
                value["checks"][0]["status"] = state
                self.write(verification, value)
                before = self.tasks.read_bytes()
                self.completion(verification, success=False)
                self.assertEqual(self.tasks.read_bytes(), before)

    def test_completion_rejects_pass_with_nonzero_exit_code(self):
        _, verification = self.evidence()
        value = json.loads(verification.read_text())
        value["checks"][0]["exit_code"] = 1
        self.write(verification, value)
        before = self.tasks.read_bytes()
        self.completion(verification, success=False)
        self.assertEqual(self.tasks.read_bytes(), before)

    def test_completion_rejects_another_tasks_verification(self):
        _, verification = self.evidence()
        value = json.loads(verification.read_text())
        value["task_id"] = "SERVICE_B"
        self.write(verification, value)
        before = self.tasks.read_bytes()
        self.completion(verification, success=False)
        self.assertEqual(self.tasks.read_bytes(), before)

    def test_completion_rejects_missing_evidence_and_unreadable_records(self):
        component, verification = self.evidence()
        for field in ("artifact_manifest", "log"):
            with self.subTest(field=field):
                value = json.loads(verification.read_text())
                path = component / value["checks"][0][field]
                content = path.read_bytes()
                path.unlink()
                before = self.tasks.read_bytes()
                self.completion(verification, success=False)
                self.assertEqual(self.tasks.read_bytes(), before)
                path.write_bytes(content)
        before = self.tasks.read_bytes()
        self.completion(component / "absent-verification.json", success=False)
        self.assertEqual(self.tasks.read_bytes(), before)
        implementation = component / "implementation.json"
        implementation.write_text("{bad-json")
        self.completion(verification, success=False)
        self.assertEqual(self.tasks.read_bytes(), before)

    def test_extra_diagnostic_failure_does_not_replace_required_acceptance(self):
        checks = [
            {"id": "runtime_layout", "required": True, "status": "PASS", "exit_code": 0,
             "command": ["check-installation"], "log": "evidence/layout.log", "artifact_manifest": "evidence/layout.json"},
            {"id": "optional_debug", "required": False, "status": "FAIL", "exit_code": 1,
             "command": ["optional-debug"], "log": "evidence/diagnostic.log"},
        ]
        _, verification = self.evidence(checks=checks)
        self.completion(verification)
        self.assertEqual(self.tasks_by_id()["SERVICE_A"]["status"], "completed")

    def test_render_uses_saved_progress_and_dependency_layers(self):
        value = {"tasks": [task("SERVICE_B", ["SERVICE_A"], 1, "in_progress"),
                            task("SERVICE_A", status="reused"), task("SERVICE_C", status="blocked")]}
        value["tasks"][0]["owner"] = "owner-implementing"
        value["tasks"][1]["owner"] = "owner-reused"
        self.write(self.tasks, value)
        before = self.tasks.read_bytes()
        self.cli("render", "--markdown", self.markdown)
        markdown = self.markdown.read_text()
        for token in ("SERVICE_A", "SERVICE_B", "SERVICE_C", "reused", "in_progress", "blocked",
                      "owner-implementing", "owner-reused"):
            self.assertIn(token, markdown)
        self.assertLess(markdown.index("SERVICE_A"), markdown.index("SERVICE_B"))
        self.assertEqual(self.tasks.read_bytes(), before)

    def merge(self, fresh, output=None, success=True):
        return self.cli("merge", "--fresh", fresh, "--output", output or self.tasks,
                        "--markdown", self.markdown, success=success)

    def test_merge_preserves_manual_progress_adds_and_retires(self):
        retained = task("SERVICE_A", status="completed")
        retained.update({"owner": "maintainer", "analysis_status": "analysis_complete",
                         "analysis": "components/A/analysis.json", "implementation": "components/A/implementation.json",
                         "verification": "components/A/verification.json", "inputs": {"commit": "source-v1"},
                         "notes": ["retain manual decision"], "custom_progress": {"ticket": 42}})
        removed = task("REMOVED", status="reused")
        old = {"tasks": [retained, removed], "task_policy": {"preserve": "custom metadata"}}
        self.write(self.tasks, old)
        fresh = self.root / "refresh" / "tasks.json"
        self.write(fresh, {"tasks": [task("ADDED", ["SERVICE_A"], 1, "pending"),
                                    task("SERVICE_A", status="pending")]})
        self.merge(fresh)
        result = self.load()
        entries = self.tasks_by_id(result)
        self.assertEqual(set(entries), {"SERVICE_A", "ADDED"})
        for key, expected in retained.items():
            self.assertEqual(entries["SERVICE_A"][key], expected, key)
        self.assertEqual(entries["ADDED"]["status"], "pending_review")
        retired = {entry["id"]: entry for entry in result["retired_tasks"]}
        for key, expected in removed.items():
            self.assertEqual(retired["REMOVED"][key], expected, key)
        self.assertEqual(result["task_policy"], old["task_policy"])
        markdown = self.markdown.read_text()
        self.assertIn("ADDED", markdown)
        self.assertIn("completed", markdown)

    def test_merge_changed_component_invalidates_transitive_consumers_only(self):
        old_entries = [task("SERVICE_A", status="completed"),
                       task("SERVICE_B", ["SERVICE_A"], 1, "reused"),
                       task("SERVICE_C", ["SERVICE_B"], 2, "completed"),
                       task("INDEPENDENT", status="completed")]
        for entry in old_entries:
            entry.update({"owner": "assigned-" + entry["id"], "verification": "records/" + entry["id"] + ".json"})
        self.write(self.tasks, {"tasks": old_entries})
        new_entries = copy.deepcopy(old_entries)
        new_entries[0]["products"].append("service_a-dev.deb")
        for entry in new_entries:
            entry["status"] = "pending"
            entry.pop("verification", None)
            entry.pop("owner", None)
        fresh = self.root / "fresh.json"
        self.write(fresh, {"tasks": list(reversed(new_entries))})
        self.merge(fresh)
        entries = self.tasks_by_id()
        for identifier in ("SERVICE_A", "SERVICE_B", "SERVICE_C"):
            self.assertEqual(entries[identifier]["status"], "pending_review", identifier)
            self.assertEqual(entries[identifier]["owner"], "assigned-" + identifier)
            self.assertIn("records/" + identifier + ".json", json.dumps(entries[identifier]))
        self.assertEqual(entries["INDEPENDENT"]["status"], "completed")
        self.assertEqual(entries["SERVICE_A"]["products"], ["service_a.deb", "service_a-dev.deb"])

    def test_merge_invalid_input_preserves_existing_outputs(self):
        fresh = self.root / "fresh.json"
        output = self.root / "merged.json"
        malformed_inputs = [
            {"tasks": [task("DUPLICATE"), task("DUPLICATE")]},
            {"tasks": [task("SERVICE_A", ["ABSENT"])]},
            "malformed JSON",
            None,
        ]
        for value in malformed_inputs:
            with self.subTest(value=value):
                if value is None:
                    if fresh.exists():
                        fresh.unlink()
                elif isinstance(value, str):
                    fresh.write_text(value)
                else:
                    self.write(fresh, value)
                output.write_text("previous output\n")
                self.markdown.write_text("previous markdown\n")
                before = self.tasks.read_bytes()
                self.merge(fresh, output=output, success=False)
                self.assertEqual(self.tasks.read_bytes(), before)
                self.assertEqual(output.read_text(), "previous output\n")
                self.assertEqual(self.markdown.read_text(), "previous markdown\n")

    def test_merge_invalid_old_input_preserves_in_place_file(self):
        fresh = self.root / "fresh.json"
        self.write(fresh, {"tasks": [task("SERVICE_A")]})
        self.tasks.write_text("{not valid JSON\n")
        self.markdown.write_text("previous markdown\n")
        before = self.tasks.read_bytes()
        self.merge(fresh, success=False)
        self.assertEqual(self.tasks.read_bytes(), before)
        self.assertEqual(self.markdown.read_text(), "previous markdown\n")


if __name__ == "__main__":
    unittest.main()
