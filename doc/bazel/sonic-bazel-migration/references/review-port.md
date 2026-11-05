# Accept migrations against the analyzed Make contract

Read the [shared contract](common-contract.md). Expectations come from completed component analysis: artifacts, sources/options, header/library interfaces, installation and metadata. Implementation defines Bazel targets/matrices; actual actions/artifacts supply evidence.

## Current verification scope

Use analyzed compile/install/consumer contracts and existing native/install interfaces. Native components deliver OCI-consumable TARs; Python distributions deliver wheels installed into TAR layers through shared wheel_layer; original package/co-production facts determine retained contents, not mandatory final DEBs. Add DEB packaging/export only on explicit request. A component wheel/TAR delivery checks its analyzed Make contract; the original Make artifacts are required for its consuming image comparison. Image archives and approved DEBs that replace Make outputs pass the [Make equivalence check](make-bazel-equivalence.md) against Make's artifacts built from the same tree.

Fully inspect Bazel artifacts/actions. Report analysis, implementation and validation separately. Derive support matrices from task contracts, not universal AMD64/ARM64 examples.

## Acquisition and commit boundaries

Check the [origin inventory](source-and-patches.md#handoff-from-make-analysis-to-bazel-acquisition), pinned sources/auxiliary packaging, acquisition rules, mappings and patch stages. Inspect every new file/overlay origin: external originals remain fixed fetched inputs; local adaptations are deltas; existing SONiC packaging retains ownership. Verify complete .dsc members and once-only Debian/SONiC patch phases. Reconstruct from declarations without analysis extraction/temporary paths and check prepared sources/resources.

## Acceptance plan

During implementation list component and modified shared-module entries. For shared build/export changes, read selected presubmit/CI and include its full module acceptance targets/tests/native architectures, limited to that module rather than all registry modules. Capability checks, component consumers and full shared acceptance remain separate evidence. Check local/remote native/cross/emulated execution prerequisites early; report resource gaps while continuing independent work. Explicit exclusions remain recorded, not PASS.

Before target ELF tests verify interpreter/libc/libraries/runfiles compatibility, using minimal side-effect-free startup checks where necessary. Cross-distribution runs use declared loaders/environments or agreed containers before full suites.

## Validation entries and identities

1. Record source/external entries, commits/uncommitted inputs, dependencies/infra/registry, effective rc/overrides/commands/environments. Preserve user configuration, freeze inputs and revalidate changes.
2. Validate independent source/root consumers separately and actual registered acquisition when preparing metadata. Root overrides do not prove independent entries or final recipes; see [modules](register-bazel-module.md).
3. query/cquery/aquery prove graph/selection/actions; record actual build/test independently, covering all required targets/unit/integration/runtime checks.
4. Save artifacts/evidence before switching suite/architecture/features/versions. Recheck affected inputs under [freezing](infrastructure.md#freeze-shared-versions-for-this-task).

Construct commands from [actual infra/rc](infrastructure.md), not borrowed aliases/versions/paths. Clean only task-created links/configuration, retaining user files and reproduction evidence.

## Test selection and failure attribution

Preserve upstream/SONiC defaults, enabling/skipping conditions, inputs and assertions. Built tests are not automatically default-executed tests. Classify required acceptance versus extra diagnostics beforehand. Optional normally skipped programs are diagnostics unless requested or necessary for affected functionality.

Determine causality from source/generation/compile/link/environment evidence before changing code. Optional status does not exclude regressions. Old Bazel outputs prove their own versions only. Without Make execution describe inference/evidence gaps rather than claiming measured Make failures. Do not add Make builds solely for failure attribution; Make artifacts built for the equivalence check remain usable evidence.

- Introduced differences or required-contract failures: fix owning layers and rerun.
- Independently evidenced existing defects exposed only by optional diagnostics: preserve upstream behavior, record trigger/cause/evidence/scope and hand off separately unless authorized.
- Insufficient attribution: retain unclassified failure and continue investigation.

Keep every FAIL/exit/raw error. Count required/diagnostic scopes separately; never relabel failures PASS/SKIP or retrospectively downgrade required checks. Report both groups, without weakening assertions/deleting tests/adding skips.

## Environment records

For actual probes/builds/tests distinguish:

| Layer | Record |
| --- | --- |
| Host | Real OS/distribution/CPU/kernel, including shared container kernel |
| Execution tools | Bazel/rc/platform/tool origins/versions/interpreters/libraries |
| Target userspace | Suite/CPU/sysroot/actual loader/runtime versions and launch/runfiles |
| Isolation/containers | Sandbox, actual image digest/ID, relevant mounts/settings |

Record actual applicable values or explicit gaps; retain only publishable relevant environment and redact secrets. Platform labels, sandboxes, explicit loaders and full-distribution containers are different evidence. A target label does not prove that distribution executed tests. Record any original-environment reproduction separately without making it a new baseline requirement.

## Artifact and evidence preservation

Bind evidence directories to suite/architecture/features/input identities. Save complete commands/directories/exits/logs/rc/overrides/resolved versions and execution versus cache status, referencing original execution for cache hits. Preserve older failures/versions with explicit applicability.

Save delivered/inspected manifests and SHA256 plus actual copies or readable checksum-pinned artifact references before switches/cleanup/overwrites. Paths/hashes alone do not replace artifacts; intermediate objects need not all be retained. Pair packages/symbols/sources by version/configuration/build-id, never mixing configuration headers/debug packages.

Resolve cquery-relative paths through this invocation's execution_root, not mutable convenience links. Check declared actual files rather than stale cache presence; distinguish archive lookup aliases from real action inputs and preserve both identities.

Before temporary inspection code, read install contracts/metadata schemas and derive expectations independently, including permissions/field locations/ELF-symbol relationships. Prove locating/saving/checking one actual artifact before extending the matrix, including read-only output copies. Use appropriate info arguments/reliable collectors rather than unrelated build aliases that can break repository mapping.

## Build design consistency

Recheck pre-coding declarations/necessity/ownership under the [boundary](implement-component.md#build-declarations-and-analysis-evidence-boundary). Acceptance confirms existing design decisions rather than deferring first wrapper decomposition/evidence relocation:

- Necessary values live in rule/platform/template declarations and consumers share their source.
- Native source/dependency/parameter data stays in builds; Make expressions/parsers stay temporary.
- Component parameters are declared at use sites; shared macros/data have real reuse; scripts/rules express actual missing semantics.
- Reuse generation/resource/archive/packaging APIs without unnecessary parsers/staging/TAR rewrites/duplicates. Remove newly unused tools/exports/references after changes while retaining complete behavior.
- Probe targets/results/audits stay temporary; production code/exports/archives retain required inputs/templates/interfaces only.
- Configuration/install/documentation/test consumers remain connected with required semantics.
- Every new macro/provider/helper has prior [necessity/reuse/ownership](infrastructure.md#rule-necessity-and-ownership) evidence. Shared mechanisms and producer exports serve direct consumers.
- Inspect actual copying: native compilation consumes declared files and include exports; no input-tree copying to repair isolation/path handling. Verify [layout](implement-component.md#file-references-and-layout) in real actions.

Preserve evidence for reproducibility. Reuse valid unaffected equivalence evidence and choose affected checks by impact.

## Native builds and host-tool acceptance

Inspect BUILD/helpers/actions for native generation/compile/link/packaging; reject ordinary foreign-build wrappers. Document kernel/special pipeline reasons/steps/boundaries and explicit approvals for other exceptions. Tool provenance remains independently checked. Inspect versions/origins/producer labels/exec platforms/closure and priority existing->BCR->source. Pinned DEB tools are allowed but version/function mismatches still fail. macOS is outside default scope. Separate target libraries/image packages/host tools and native-build acceptance.

## Itemized verification

### Source acquisition and patches

Follow [source checks](source-and-patches.md#6-updates-and-verification): original/patched identities, order/conditions/overlays, final behavior, declared-change reevaluation, explicit mismatch/missing failures, variants/consumers and separate source/registry entries.

### Compilation and linking contract

- Check per-target/configuration source identities/variants/relative paths, including same names in different directories and different macro compilations. Verify generators/inputs/versions/exec-target roles.
- Parse ordered actual -D/-U/forced includes/standard/optimization/security/ABI from aquery; interpret using toolchain/preprocessor evidence and analyzed evaluation rules. First list all compile/link producers required by this delivery and choose query roots covering them. Plugin installations must include plugin producers; an aggregate library query may omit them. Record coverage counts by target/configuration and check hardening, threading and dynamic-loading options against the original contract. BUILD definitions/diffs prove declarations; actual actions prove effective behavior. After option changes collect and recheck affected actions.
- Preserve -I/-isystem/-iquote/sysroot/forced-header categories/order/provenance. Incidental system/legacy paths do not satisfy declarations. Propagate public headers through providers.
- Check actual ordered libraries/versions/static-shared/link states including as-needed/whole-archive/groups. Direct symbol consumers declare direct deps; shared adapters retain linking context/runfiles.
- Verify all interface files reachable in actual configuration and source identities match Make injection. System libraries map to public APT per-library/header/link/runtime interfaces, without private extraction/import/CcInfo filtering or -l/-L substitutes. Necessary state flags still reference declared inputs.

Map actual values to fixed/expressed/probed Make semantics. Explain permitted differences and feature/ABI/security/layout effects. Unordered sets or removed path options cannot hide differences. Byte-identical objects are not required here; the [equivalence check](make-bazel-equivalence.md) compares the delivered ELF files with `elfcompare`.

### Configuration and fixed parameters

Review the evidence for [switch admission](configuration.md#admission-requirements-for-new-bazel-switches) and ensure public Bazel settings match the actual SONiC entry. Remove settings lacking entry-level configurability evidence and restore effective original parameters. Retain unused-branch experiments as historical diagnostics and correct their attribution, without expanding features or mandatory validation.

Verify [mappings](configuration.md), defaults/legal values/overrides/combinations through actions/deps/generated files/assembly. Keep fixed inputs fixed and platform differences derived. Check transitional Make and direct Bazel separately with shared build/cquery arguments and cross-module settings.

### Generation tools

Check [versions/closures](code-generation.md), actual transitives/plugins/templates, language consumers, conditional APIs/serialization and missing-input diagnostics. Verify Thrift realpath/staging; processwrapper success does not prove closure.

### Autoconf template generation

Map each value to controlled evidence/inputs/consumer across required matrices. Probe compiler/sysroot/headers/libraries/options must match actual Bazel configuration. Cross runs require target evidence/contracts. Check undef/zero/escaping/version/path and configure-driven source/options/link/install choices. Necessary values belong in attributes/templates with complete inputs. Keep evidence temporary and recheck values after source-input changes. Probing itself needs no Make artifact build.

### Bazel artifacts and installation contract

Verify [production/consumption](install-interfaces.md): Python owners build wheels and OCI/rootfs assembly installs the tested wheels through shared wheel_layer. Inspect aquery for the actual wheel producer and installer inputs. Source DEB installation consumes contents/metadata directly, without producing then unpacking a DEB; pinned distributions retain their managed paths. [Special images](image-recipes.md) retain stage/boot contracts.

- Inspect required native interfaces/runtime/development/tool TARs/symbols/metadata and missing/extra content; verify source wheel artifacts and their installed TARs together. Default presubmits avoid unsolicited DEB packaging/tests/export/bridges.
- Explicitly build public runtime/symbol/metadata and verify layout/closure/authority/real payload relationship. New DEBs must preserve existing TAR/image validation; packaging alone proves only that branch.
- Use existing image APIs or minimal real consumers with explicit proof scope. Full OCI tasks also validate assembly/required startup.
- Requested DEBs check control/members/types/modes/owners/links/scripts/configuration against analyzed transforms/versions/architecture/relations/dynamic rules, and pass the [equivalence check](make-bazel-equivalence.md) against Make's package of the same name.
- Wheels check contents/resources/METADATA/entries/RECORD/tags/ABI and Requires-Dist against the reviewed runtime lock; installed copies check payload bytes, metadata, interpreter/imports/entries and use of the same wheel artifacts by consuming images.
- ELF checks Machine/interpreter/SONAME/NEEDED/RPATH/RUNPATH/closure, installed versus runfiles paths, and build-id/debuglink/debug queries.
- Check scripts/upgrades/config retention in appropriate isolation. OCI checks base identity/source/APT/wheel/order/user/entry/config/startup, installed status/metadata/receipt/payload and precise coverage of later source layers. Check accounts/directories/modes/services/caches. Debug images match exact runtime/final symbols. Installation/disk images check partitions/rootfs/kernel/initramfs/container storage and actual installer/boot behavior; structure is not boot proof.

### OCI-specific acceptance

Derive applicable matrix from [OCI](oci.md)/analysis. Record identities/commands/exits/artifacts/first errors/status per check, separating syntax/structure/startup.

| Boundary | Required result | Applicable failure/recovery |
| --- | --- | --- |
| Prerequisites/inheritance | Real source/registry/PR/base digest/architecture and inherited producers | Missing API/wrong version fails at owner |
| Runtime set | Every native/APT/Python identity has installation inputs | Missing producer/TAR/transitives fail then recover after correction |
| Locks | Actual updates/checks/read-only builds and platform/extras/metadata binding | Input changes stale lock; update restores |
| Files/layers | Contract modes/numeric owners/links/architecture/overwrite/whiteout/opaque/xattr | Forbidden type/content conflicts fail |
| Metadata/state | TAR/hash/MODULE/control/status/receipt/final payload agree | Wrong base/TAR/missing paths rejected |
| Accounts/services | Inherited identities preserved and initialization effects correct | Duplicate conflicts rejected, actual permissions/startup verified |
| Runtime ABI | Loader/NEEDED/search/architecture, Python imports/entries/resources/metadata | Missing runtime revealed by installed copy, restored after fix |
| Real installation | Configured rootfs/raw DEBs/native tools/runtime, actual scripts/triggers/status | Deleted files stay deleted, failures do not publish success |
| Debug | Exact runtime, matching source/system symbols/tools | Wrong runtime/symbol identities detected |
| Make equivalence | Runtime/debug archives pass the [equivalence check](make-bazel-equivalence.md) against Make's archives from the same sources | Unaccepted differences fail; fix the owner or add a rule stating the cause |
| OCI/runtime | Layout/archive digest/config/user/entry/options/signals/services | Separate load/start/self-check/native/cross evidence |

Explain inapplicable branches from original contracts. OCI success does not prove whole-machine storage/install/boot acceptance.

### Locks and consumer versions

Every introduced dependency requires actual current update/exit/check evidence. Existing files/old logs/check-only do not replace updates. Preserve APT identities and verify Go ZIP updates/exact coverage; no-diff needs execution evidence. Verify [requests/locks/exports](dependency-locking.md), direct/transitive origins/hashes/features/platform/backend inputs and root/independent selection. Keep unrelated versions stable; use native read-only checks and real consumers, with stable production files. MODULE lock evidence does not replace package locks. Missing refresh/mismatch/unvalidated consumers retain pending status.

### Language and shared capabilities

Go follows [acceptance](go.md#8-installation-and-acceptance) for SDK/tags/version/resources/graph/vendor/CGo and actual native calls, exec generators/target configuration/independent/root/installed copies. Rust verifies SDK/locked crates/features/traits/build.rs/native links. Python verifies interpreter/SOABI/installed imports; mixed native code uses ELF checks. Fix missing shared capability at its owner with independently justified verification, preserving features and avoiding duplicate private mechanisms. Check affected shared consumers. Cache validation repeats identical commands immediately with unchanged inputs; changed configuration/entries are not same-input evidence.

## Results and fixes

Save verification.json/md and evidence/verification per component. [Connect](phase-handoff.md#1-carry-one-deliverable-through-all-phases) expectations, targets, commands and observations and update task progress. Record target/configuration/environment/analysis basis/result/exit/evidence/first error. Use PASS/FAIL/NOT_RUN/BLOCKED; explain inapplicable items outside required counts. Any required non-PASS means verification has not passed. [Attribute](#test-selection-and-failure-attribution), fix and rerun affected checks; report diagnostics/existing defects separately.

Retain original failures, causal evidence, changes and new results. Summaries use current identities. Lead review checks artifacts/unresolved items/versions without mechanically repeating valid evidence. completed means full task delivery/verification, not source analysis or a leaf build. Hand off component, module and final integration separately.

## Migration handoff checks

Deliver per-repository files/source/submodule/shared identities/public APIs/configurations/commands/evidence. Confirm scope and validated versus delivered inputs. Revalidate changes and synchronize identities/evidence. Analysis-only tasks deliver that scope; list done/remaining items for reproducible continuation.

## Code generation acceptance

For generators, record [applicable checks](code-generation.md#generator-specific-acceptance), languages/configurations/platforms/commands/artifact identities/results. Verify Bison/Flex parsing, protobuf/Thrift serialization, gRPC calls and SWIG Python/CGo calls separately. Connect generated and installed consumers; report cross builds and target execution separately.
