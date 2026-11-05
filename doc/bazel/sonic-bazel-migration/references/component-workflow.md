# Component identification, dependencies and phased execution

Read the [shared contract](common-contract.md). Decompose requested outputs into components, analysis contracts, implementation targets and verification evidence. Task records use caller-selected directories; no user installation/local application branch is prescribed. PR/Project status follows the original main-entry collaboration policy.

## 1. Identify input components

Resolve user variables, package names or Make targets to registered objects, rules and sources. Read current code first; explain candidates when clarification is needed.

| Type | Identification |
| --- | --- |
| DEB | SONIC_MAKE_DEBS/SONIC_DPKG_DEBS and source/download/copy/derived package sets |
| WHEEL | SONIC_PYTHON_WHEELS |
| DOCKER | Runtime/debug/base/download/copy container sets |
| KVM_IMAGE | SONIC_KVM_IMAGE and producer |
| ONE_IMAGE | SONIC_ONE_IMAGE and producer |
| RAW_IMAGE | SONIC_RAW_IMAGE and producer |

Accept DEBS/WHEELS/DOCKERS collections; check SONIC_INSTALLERS/_IMAGE_TYPE. Record repository/commit/working changes. Types and collected names identify relationships, not Bazel archive formats. Boundaries follow independent production, often one .mk. Co-produced primary/development/debug outputs share a task; independent producers in one file may split. Retain component/variable/product/rule/source mapping.

## 2. Resolve prerequisite components

Recursively find SONiC package/wheel/container/image producers until closure, establishing which component must be ready before another. Read rules/platform/includes/slave.mk and interpret DEPENDS/DEBS_DEPENDS/WHEEL_DEPENDS/PYTHON_WHEELS/LOAD_DOCKERS/image installation by actual behavior. Keep RDEPENDS separately and derive scheduling impact from production/assembly.

Use the union of all branches with provenance. graph.json omits conditions; component analysis explains them. Any co-product pulls in its production task and combined prerequisites. Schedule shared components once; omit intra-task relations. Component analysis handles generators/compilers/system libraries/sources/options; registered produced tools remain components. Resolve only relationship gaps affecting scheduling here.

Use [dependency collection](build-dep-graph.md) from repository root:

```bash
python3 "${SKILL_DIR}/scripts/build-dep-graph.py" . \
  --component FRR \
  --output-dir /path/to/migration-records/FRR
```

The helper supports lead review of identities/edges and keeps output component-level. Report missing identities/edges/cycles only when they affect scheduling. Check Make parse-time effects before invoking Make; this helper reads statically.

## 3. Create task files

Select a temporary task directory, illustrated by /path/to/migration-records/<input-id>/. Preserve variable names; concrete targets use basename with extension, such as sonic-vs.img.gz. Combine multiple inputs deterministically, preserve mappings and distinguish collisions with parent paths. Check directory containment and report actual location.

| File | Responsibility |
| --- | --- |
| graph.json | Inputs, component identities/types/rules/sources, union edges/provenance and actual scheduling issues |
| tasks.json | Sole source of component tasks and manual progress |
| tasks.md | Derived concise layered scheduling/status view |

Keep package nodes, files, scans, expression diagnostics and progress out of graph.json/DOT. tasks.json owns products/progress. Record stable id/name/type/products/rules/build entry/real sources/prerequisites/layer/status/owner/analysis reference/existing coverage/evidence/blockers plus source/module/effective configuration. Record missing locations. Implementation tasks also track shared input versions, writers/scopes and per-repository changes, referencing implementation/verification rather than duplicating detail. The lead reviews owners/references/identities before updates and uses [handoff](phase-handoff.md) for recollection.

Topologically layer tasks. Same-layer parallelism requires nonoverlapping writes. Display components/types/rules/sources/prerequisites/progress, plus real issues and affected tasks.

```text
Batch 1: sonic-fib, libyang3, libnl3
Batch 2: snmpd (requires libnl3)
Batch 3: frr (requires sonic-fib, libyang3, snmpd)
```

This illustrates scheduling; derive real tasks from current code.

## 4. Review existing migration and coordinate delegated work

Read [infrastructure](infrastructure.md), verify selected infra version/APIs/toolchains/consumers and prepare applicable prerequisites. Inspect existing targets, outputs, every required condition and version-specific evidence. Mark satisfying implementations reused while retaining dependencies; record partial coverage. BUILD existence alone is insufficient.

When delegation is used, coordinate prerequisite/writing scopes. Independent implementers perform the same stages:

1. Choose ready tasks and check shared-file/directory conflicts.
2. Supply absolute shared/phase/topic paths and require recipients to read and record applicable constraints. Supply type/products/source/conditions/prerequisite results/write scope/independent task outputs and file-based handoffs. Assign one writer per shared file. Freeze source/rules/entry scripts before validation and use assigned evidence directories. Normal build/cache writes and independent implementation may continue. Notify consumers and wait for affected processes to exit or use independent copies before changing inputs, then revalidate. Separate output directories do not isolate shared scripts; serialize shared version switches.
3. Perform [Make analysis](analyze-make-component.md), producing component analysis.json/analysis.md/evidence. [Collection](component-analysis-script.md) is only a start: establish all 14 patched contracts, selection, parameters, generation, packaging and environment evaluation.
4. Review conclusions/evidence/completion. Continue unresolved rules or report concrete technical blockers. Track build execution separately from rule-analysis completeness.
5. Lead/implementer read [implementation](implement-component.md), save implementation.json/md and map current wheel/TAR/OCI delivery, original artifacts, generators, interfaces, configuration/layout and actual APIs. Implement in dependency order with per-repository ownership. Controlled target-toolchain Autoconf probes produce input-bound values/templates, with platform/features distinct and temporary evidence from creation. Decide extension necessity/reuse/ownership before coding. After shared capability tests, [freeze inputs](infrastructure.md#freeze-shared-versions-for-this-task) before final matrices.
6. Apply [acceptance](review-port.md), saving verification.json/md against analyzed expectations. Validate source modules/root consumers and registry recipes separately. Record host/exec/target/container environment and per-configuration artifact identity. Preserve upstream default tests/conditions/assertions. Separate [required checks from diagnostics](review-port.md#test-selection-and-failure-attribution), fix introduced failures at their owning layer and rerun.
7. Hand off identities, changes, matrix, commands and evidence. Lead review updates tasks and releases newly ready consumers, then confirms requested entry/delivery scope.

Read-only analysis may run ahead; implementation/verification follows actual prerequisite readiness. Keep detailed tools/sources/options in analyses and scheduling at component level.

## 5. Update progress and hand off

| Task status | Meaning |
| --- | --- |
| pending_review | Existing implementation/coverage not reviewed |
| pending_migration | Required migration work confirmed |
| in_progress | Implementation underway |
| pending_verification | Implementation ready; mandatory checks pending |
| completed | Required outputs/conditions evidenced |
| reused | Existing implementation satisfies this task |
| blocked | Concrete obstacle and recovery condition recorded |

Track analysis separately as pending_analysis/analyzing/analysis_complete/analysis_blocked. Update owner/time/evidence then render tasks.md. completed+reused counts as done; list ready and prerequisite-waiting tasks. Ordinary waiting remains pending; real failures/indeterminate relationships carry blockers.

Protect manual progress before recollection and merge by stable identity. List additions/removals/dependency changes; retain retired history outside active counts. Reassess completed evidence after source/product/condition changes under [handoff](phase-handoff.md).

At delivery check every requested/prerequisite task, product ownership and executable order; report finished/remaining items and evidence. Add Make switches/export only if requested. Ready prerequisites require implementation and evidence. Validate Bazel actions/artifacts against analyzed Make compile/install/interface contracts and existing native/install APIs. Image and DEB deliveries also pass the [Make equivalence check](make-bazel-equivalence.md); component wheels/TARs are compared through their consuming image.

Read [module registration](register-bazel-module.md) for independent modules or patched external modules; record direct-source and actual registry validation separately.
