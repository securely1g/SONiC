# SONiC component dependencies and scheduling

Read the [shared contract](common-contract.md). The helper collects SONiC dependencies across all conditional branches and generates layered component tasks. Types are DEB, WHEEL, DOCKER, KVM_IMAGE, ONE_IMAGE and RAW_IMAGE. Types/products preserve Make production relationships for identification/scheduling; current delivery contracts select Bazel formats. Default output is OCI-consumable TAR, including DEB-classified components. Registered objects and explicit co-production determine identity; independent objects in one .mk may be distinct components.

## Invocation

From the repository root, replace component/output directory:

```bash
python3 "${SKILL_DIR}/scripts/build-dep-graph.py" . \
  --component FRR \
  --output-dir /path/to/migration-records/FRR
```

Repeat --component for variables, resolvable products/paths or DEBS/WHEELS/DOCKERS/ONE_IMAGE/KVM_IMAGE/RAW_IMAGE collections. Prefer component variables for symbolic filenames. Pass --output-dir explicitly to generate graph.json, graph.dot, tasks.json and tasks.md.

Initial collection creates tasks. Recollect into a new directory and [merge safely](phase-handoff.md#3-preserve-manual-progress-during-recollection) through task-progress, retaining progress/versions/owners/evidence by stable id. render derives tasks.md from tasks.json. Default output/--output-prefix remain legacy interfaces; use explicit task directories here. Exit 0 means generation succeeded; unresolved input exits 2.

## Component boundaries and dependencies

- Scan rules/platform/entry/include files with all branches and provenance.
- Identify registered production objects; versions/directories/tool settings are metadata.
- Co-produced primary/development/debug products share a task and the group's combined dependencies.
- Independently produced debug/base containers retain separate tasks and runtime-container dependencies.
- Internal product links form component edges directed consumer -> prerequisite.
- Build/assembly/order relations determine layering; runtime relationships stay separate. Intra-task relations are not scheduling edges.
- Display type/name/rule/source/prerequisites/layer/progress.

Component analysis owns Bison/Flex/compiler/system-development/Build-Depends details. Ordinary files/templates/parser infrastructure are not tasks; registered SONiC-produced tools are components.

## Outputs

graph.json contains input mappings, component identity/type/rule/source, cross-component typed/source-attributed edges merged across conditions and real scheduling issues. Omit build conditions and intra-component edges. Co-products map to one component. Ordinary files/system tools are not nodes; DOT matches this view.

Keep package-product mappings/layers/progress in tasks.json and a concise layered tasks.md. Do not duplicate package nodes, scan logs, expression diagnostics, progress or adjacency tables in graph.json. Report only real unresolved identity/producer/dependency/cycle issues; normal output is the layered task list. Keep symbolic/dynamic-include parsing details internal rather than large attachments.

Static collection is not full GNU Make evaluation. Investigate expressions/cycles affecting relationships against original rules. Conditions belong in component analyses; graph.json schedules the union. Collection is read-only; the lead assesses existing migration coverage and uses phase handoff for progress merges.

## Verification

```bash
python3 -B -m unittest discover \
  -s "${SKILL_DIR}/tests" -p test_build_dep_graph.py -v
```

Check input mapping, types, co-products, dependencies, layers and concise output under the main workflow.
