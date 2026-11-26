# Phase handoff, task updates and resumption

Read the [shared contract](common-contract.md). Use this page for task records, analysis/implementation/verification handoffs, progress updates and resumption. Keep records in the task's temporary directory.

## 1. Carry one deliverable through all phases

EXAMPLE builds src/main.cc and installs /usr/bin/example. Substitute analyzed files/versions/platforms/commands. Evidence paths are component-relative; repository_state/inputs separately record actual source/toolchain/dependency identities.

A complete analysis.json contains [all groups](analyze-make-component.md#analysis-record-contents). This is one cross-phase item; record others likewise. Use confirmed/unconfirmed/not_applicable states rather than unexplained empty lists:

```json
{
  "task_id": "EXAMPLE",
  "analysis_status": "analysis_complete",
  "required_conditions": ["Selected platform and default features"],
  "package_contents": {
    "state": "confirmed",
    "value": [{"source": "example", "destination": "/usr/bin/example", "mode": "0755", "uid": 0, "gid": 0}],
    "conditions": ["Default features"],
    "evidence": ["evidence/install-rule.txt"]
  },
  "unresolved": [],
  "execution_validation": [{"object": "Original Make artifact build", "status": "NOT_RUN", "reason": "EXAMPLE delivers only a TAR; its consuming image's equivalence check builds the Make archive"}]
}
```

Map that fact into implementation.json before coding, retaining original sources/options/libraries/identities:

```json
{
  "task_id": "EXAMPLE",
  "inputs": {
    "source_revision": "Actual immutable source identity, including local changes when present",
    "configuration": {
      "os": "Actual distribution and version",
      "toolchain": "Actual toolchain version and digest",
      "execution_arch": "Actual execution architecture",
      "target_arch": "Actual target architecture",
      "features": {},
      "dependencies": {}
    }
  },
  "deliverables": [{
    "contract": "analysis.json#/package_contents/value/0",
    "native_target": "//:example",
    "install_target": "//:example_runtime",
    "rule": "@sonic_build_infra//tar:sonic_deploy_tar.bzl%sonic_deploy_tar",
    "destination": "/usr/bin/example",
    "consumer": "//acceptance:installed_example",
    "acceptance": ["runtime_layout"]
  }]
}
```

This checks the confirmed installation contract only. Add original tests/ABI/runtime acceptance with source/test-derived expectations. Minimal acceptance/BUILD.bazel consumer:

```starlark
load("@rules_distroless//distroless:defs.bzl", "flatten")
flatten(name = "installed_example", tars = ["//:example_runtime"], deduplicate = True)
```

It consumes source installation TAR directly and produces an assembly TAR. Use actual [native installation](install-interfaces.md#2-native-programs-and-deb-intermediate-layers) labels/attributes and one identity for build/cquery/checks.

verification.json connects expectations to actual evidence. It must contain its own top-level inputs object recording the source revision and effective configuration actually verified, using the same structure as implementation.json above. The inputs below illustrate the same configuration; populate them from the actual verification environment. Set PASS/FAIL/NOT_RUN/BLOCKED honestly; PASS requires executed commands and true assertions:

```json
{
  "task_id": "EXAMPLE",
  "inputs": {
    "source_revision": "Actual immutable source identity, including local changes when present",
    "configuration": {
      "os": "Actual distribution and version",
      "toolchain": "Actual toolchain version and digest",
      "execution_arch": "Actual execution architecture",
      "target_arch": "Actual target architecture",
      "features": {},
      "dependencies": {}
    }
  },
  "checks": [{
    "id": "runtime_layout",
    "required": true,
    "contract": "analysis.json#/package_contents/value/0",
    "target": "//acceptance:installed_example",
    "configuration": "verification.json#/inputs/configuration",
    "command": ["python3", "evidence/verification/check_layout.py", "evidence/verification/runtime.tar", "evidence/verification/runtime-files.json"],
    "status": "NOT_RUN",
    "exit_code": null,
    "artifact_manifest": "evidence/verification/runtime-files.json",
    "log": "evidence/verification/runtime-layout.log",
    "first_error": null
  }]
}
```

runtime_layout checks TAR type/mode/numeric ownership and missing/extra files. For native runtime contracts, execute installed copies with original inputs/expectations in a matching userspace. This file check assumes no extra CLI options. Save full commands/exits/SHA256/manifests; builds/checks are distinct outcomes. Save check_layout.py in task evidence; its expectations come independently from analysis and apply across configurations:

```python
import sys
import tarfile
import json
import hashlib
from pathlib import Path

with tarfile.open(sys.argv[1], "r:*") as archive:
    members = {}
    for item in archive.getmembers():
        name = item.name
        while name.startswith("./"):
            name = name[2:]
        if item.isdir():
            assert name in (".", "", "usr", "usr/bin"), name
            assert (item.uid, item.gid, item.mode) == (0, 0, 0o755), name
        else:
            assert name not in members, name
            members[name] = item
    assert set(members) == {"usr/bin/example"}, sorted(members)
    program = members["usr/bin/example"]
    assert program.isfile()
    assert (program.uid, program.gid, program.mode) == (0, 0, 0o755)
    manifest = {
        "sha256": hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),
        "files": [{"path": name, "uid": item.uid, "gid": item.gid,
                   "mode": oct(item.mode), "size": item.size}
                  for name, item in sorted(members.items())],
    }
Path(sys.argv[2]).write_text(json.dumps(manifest, indent=2) + "\n")
```

Build and save actual consumer artifacts/digests/manifests/logs using identical platform/feature arguments for build/cquery/info:

```bash
set -euo pipefail
example_evidence=/path/to/migration-records/EXAMPLE/components/EXAMPLE/evidence/verification
mkdir -p "$example_evidence"
bazel build //:example_runtime //acceptance:installed_example > "$example_evidence/build.log" 2>&1
example_output=$(bazel cquery //acceptance:installed_example --output=files)
example_execroot=$(bazel info execution_root)
python3 - "$example_execroot" "$example_output" "$example_evidence/runtime.tar" <<'PY'
from pathlib import Path
import shutil
import sys
outputs = sys.argv[2].splitlines()
assert len(outputs) == 1, outputs
source = Path(outputs[0])
if not source.is_absolute():
    source = Path(sys.argv[1]) / source
assert source.is_file(), source
shutil.copy2(source, sys.argv[3])
PY
python3 "$example_evidence/check_layout.py" "$example_evidence/runtime.tar" \
  "$example_evidence/runtime-files.json" > "$example_evidence/runtime-layout.log" 2>&1
```

Save check_layout.py first. Record exits/first errors in verification. set -e stops the command group on failure; preserve failure logs. On success read real digest/manifests. Report build/layout checks separately and apply [per-configuration isolation](review-port.md#artifact-and-evidence-preservation).

Each implementation deliverable's acceptance list defines required ids. verification.checks must cover every required id, and checks outside that set must explicitly declare required=false. Reject omitted required ids, required ids marked optional, and additional mandatory or unclassified checks before accepting completed/reused. Every required check must pass; explicitly optional diagnostics are reported separately. Derive Markdown from the same records and link evidence rather than maintaining conflicting conclusions.

## 2. Update status and render

tasks.json is the sole component-progress source. Use the component status table; normalize collected initial status to pending_review. analysis_status independently uses pending_analysis/analyzing/analysis_complete/analysis_blocked. Preserve owners/evidence/versions/manual notes by id.

Progress fields reference phase JSON; collection still owns graph facts:

```json
{
  "id": "EXAMPLE",
  "inputs": {
    "source_revision": "Actual immutable source identity, including local changes when present",
    "configuration": {
      "os": "Actual distribution and version",
      "toolchain": "Actual toolchain version and digest",
      "execution_arch": "Actual execution architecture",
      "target_arch": "Actual target architecture",
      "features": {},
      "dependencies": {}
    }
  },
  "status": "in_progress",
  "analysis_status": "analysis_complete",
  "owner": "port-example",
  "analysis": "components/EXAMPLE/analysis.json",
  "implementation": "components/EXAMPLE/implementation.json",
  "verification": null
}
```

Paths are relative to tasks.json; update normalizes absolute references. Update JSON then render Markdown:

```bash
python3 "${SKILL_DIR}/scripts/task-progress.py" update \
  --tasks /path/to/migration-records/EXAMPLE/tasks.json \
  --id EXAMPLE --status in_progress --analysis-status analysis_complete \
  --owner port-example \
  --analysis /path/to/migration-records/EXAMPLE/components/EXAMPLE/analysis.json \
  --implementation /path/to/migration-records/EXAMPLE/components/EXAMPLE/implementation.json
python3 "${SKILL_DIR}/scripts/task-progress.py" render \
  --tasks /path/to/migration-records/EXAMPLE/tasks.json \
  --markdown /path/to/migration-records/EXAMPLE/tasks.md
```

Before completion, populate task.inputs with the intended source_revision and a nonempty configuration object. configuration requires nonempty os, toolchain, execution_arch and target_arch strings, plus features and dependencies objects (empty only when inapplicable). Record resolved dependency revisions, lock digests, relevant flags and overrides in those objects; an immutable source identity must include patches and local changes when present. implementation.inputs and verification.inputs record their actual inputs independently as full resolved objects, not pointers to mutable records. Completion requires exact equality of all three inputs objects; missing identities or mismatches fail without changing tasks.json. This is provenance matching, not proof that the referenced commands executed truthfully.

update changes only explicit fields for the selected id. Missing/duplicate ids or invalid statuses fail without changing the file. completed requires --verification: implementation required acceptance must be nonempty, check ids unique and covering it, all required checks PASS and references readable. reused uses the same source/configuration and acceptance checks as completed. Legacy records without inputs must be populated from verified provenance before completion or reuse. render displays current owners/status sorted by layer without recollection.

Analysis completion is not component completion. Ready code becomes pending_verification; mandatory PASS checks permit completed. Concrete resource/external obstacles become blocked with recovery conditions.

## 3. Preserve manual progress during recollection

Collect into a fresh directory, then merge with existing tasks. EXAMPLE below illustrates the chosen identity:

```bash
set -euo pipefail
python3 "${SKILL_DIR}/scripts/build-dep-graph.py" "$BUILDIMAGE_ROOT" \
  --component EXAMPLE --output-dir /path/to/migration-records/EXAMPLE-refresh
python3 "${SKILL_DIR}/scripts/task-progress.py" merge \
  --tasks /path/to/migration-records/EXAMPLE/tasks.json \
  --fresh /path/to/migration-records/EXAMPLE-refresh/tasks.json \
  --output /path/to/migration-records/EXAMPLE/tasks.json \
  --markdown /path/to/migration-records/EXAMPLE/tasks.md
cp /path/to/migration-records/EXAMPLE-refresh/graph.json \
  /path/to/migration-records/EXAMPLE-refresh/graph.dot \
  /path/to/migration-records/EXAMPLE/
```

After merge, synchronize graph.json/DOT before scheduling; recover consistent graph versions on sync failure. Retain the refresh snapshot; active graph/tasks must match one collection. Choose a new refresh path before repeating.

merge behavior:

- New collection supplies identity/products/prerequisites/type/rules/sources/layer.
- Unchanged graph facts and unchanged supplied build inputs preserve status/owners/phase references/versions/notes.
- New tasks start pending_review; removed records enter retired_tasks outside active counts.
- Changed tasks/affected consumers return to pending_review; retain historical evidence and list changes. A fresh task with explicit changed inputs replaces the intended identity and invalidates that task and its transitive consumers. The static collector supplies graph facts, not build identities: enrich fresh task inputs from current source/configuration observations before merging when those inputs may have changed. Absent fresh inputs preserve the prior identity and do not establish its freshness; review it before resuming.
- Read/validate both inputs before atomic JSON writes; failures preserve records. Derive Markdown from successful JSON. Diagnose duplicate ids, missing prerequisites and read failures.

Review changes and next prerequisites after merging. Resume from recorded source/configuration identities only when prerequisite identities/interfaces/applicable evidence satisfy requirements.
