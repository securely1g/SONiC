# SONiC Bazel migration checklist

Use this checklist for the configurations and deliverables included in the current task. Mark items as verified, pending, or not applicable, with evidence. A partial task can complete while other migration items remain pending.

Select the applicable [migration workflow](migration-workflow.md) sections before using this checklist. Record source compilation, Python wheel production, Docker assembly, and Debian package import/production separately. Container implementations use the [common Docker template](docker-image-template.md).

## 1. Scope and baseline

- Identify the repository, source revision, migration unit, downstream consumers, and applicable HLD phase.
- State which producer changes, which consumer interface it preserves, and which inputs remain supplied by Make or published binaries. Record the selected workflow's completion checks.
- Plan separate PRs for independent features. Identify each feature's concrete consumers, link their PRs when available, and explain the target/build path and need; follow the [feature-splitting workflow](shared-dependency-workflow.md#split-features-and-identify-their-consumers).
- Inventory existing Make/Autotools/CMake or other build commands and any existing Bazel port.
- Record required outputs: libraries, executables, generated files, bindings, tar archives, Debian packages, wheels, and images.
- Record any explicit approval to execute Bazel actions that create DEB packages and the scope it covers. Without it, do not run those actions.
- Record supported OS releases, execution/target architectures, feature flags, optional dependencies, and required services.
- Capture reference artifacts and test results tied to a known source revision and environment.
- For a PR refresh, record the current base and head and validate their combination; check whether the desired fix already exists before preserving a workaround.
- Preserve upstream authorship and useful commit history when adopting existing work.

**Completion evidence:** a declared configuration matrix, reproducible baseline commands, and an output/test inventory.

## 2. Toolchains and dependency inputs

- Align the Bazel version with the current SONiC consumer requirements.
- Check Bazel Central Registry and upstream Bazel support before developing a dependency module; record the modules/versions inspected and reuse a compatible central module.
- If BCR provides the dependency, require explicit approval for a custom alternative, including when its version, ABI or packaging differs. Record existing approval when it already covers that work.
- Before upgrading or replacing a patched dependency, complete [patch-by-patch verification](../SKILL.md#verify-existing-patches-before-switching-upstream): record upstream coverage for every patch and run its original regressions alongside consumer tests for the supported configurations.
- Pin module versions, source commits and checksums, toolchain, sysroot, and package inputs in the appropriate shared definitions.
- Use one endpoint per registry repository; separate SONiC and BCR registries are allowed. Local builds and CI use the same canonical maintained branch URL, such as `main`, in committed `.bazelrc` files and effective configuration. Follow the [registry URL policy](../SKILL.md#use-main-registry-urls-for-local-builds-and-ci) for any verified Bazel exception. Preserve module versions and source pins, and record the observed registry revision and native coverage. Follow the [registry workflow](shared-dependency-workflow.md#select-one-endpoint-per-registry-repository) for explicit temporary Draft validation of missing entries; never stack endpoints from the same registry as fallbacks.
- Before retaining or setting Ready, verify the [registry endpoint gate](shared-dependency-workflow.md#require-landed-registry-endpoints-before-review): canonical maintained branch for local builds and CI, no temporary override, all required entries and coherent sources, updated effective configuration/CI/docs, and current selection evidence. Any verified Bazel exception must select a landed registry commit. Missing prerequisites keep or return Draft. Include quiet Ready PRs in each babysitter audit.
- Verify each required execution/target pair, including any cross-compilation arrangement used by legacy CI.
- Map native libraries, headers, language packages, and generators to declared Bazel dependencies.
- Map every reusable SONiC Rust library to its owning repository and public target under the [Rust ownership rule](../SKILL.md#keep-reusable-rust-libraries-with-their-owners). Preserve ordinary third-party `crate_universe` resolution. Align the SONiC library's Cargo, module and registry source pins; share defining crate targets for public types/traits across repository boundaries, including third-party types.
- Verify the component's own outputs compile from source. Inventory external target/test dependencies as source-built or pinned package imports, including native wheels and ELF/static libraries; check versions, integrity, architecture, ABI, and transitive requirements under the [component-source policy](source-builds-and-lockfiles.md). Pinned external binaries are allowed and are not automatically migration gaps.
- Keep `MODULE.bazel.lock` ignored and CI-generated. Preserve actual input pins and canonical package locks, including `requirements_lock.txt`, `uv.lock`, `Cargo.lock`, and applicable APT locks, even when generated. Follow the [package-lock policy](source-builds-and-lockfiles.md#keep-canonical-package-locks-in-git): ordinary builds consume reviewed transitive versions and integrity; a generated export needs a checked-in canonical lock, pinned export tooling, and validation that the locked selection is preserved. Retain generated Bazel resolution state as validation evidence.
- For Rust, keep `Cargo.lock` tracked and generate ignored `Cargo.Bazel.lock` during preparation with the pinned shared helper. Validate unchanged Cargo pins and prepare owning libraries before external consumers; retain generated metadata and receipts.
- Classify execution tools and their runtime libraries/data separately from target headers and libraries. Reuse a compatible Bazel toolchain or the shared pinned `build_tools` set; keep the target system ABI foundation in `sysroot`. Ordinary target/test libraries remain explicit target dependencies and may come from pinned packages. See [build tools and sysroot guidance](build-tools-and-sysroot.md).
- Inspect custom rule tool and bundle edges for `cfg = "exec"`, keep target dependencies in the target configuration, and align tool selection with the action's execution platform. Verify tool runtime inputs are declared rather than taken from the worker's installation.
- Isolate compatibility paths that still depend on an older Bazel version or the SONiC slave environment.
- Compare compiler, linker, and feature options with the baseline; document intentional differences.
- For shared dependency changes, verify the source-to-registry-to-consumer chain and actual module resolution; prefer focused architecture checks for early feedback before expensive integration builds.
- For an unmerged registry PR, retain only its current candidate unless an evidenced compatibility need requires another. Preserve released and actual-base entries, check consumer pins, and remove superseded draft directories, metadata, and CI jobs together using the [draft-version workflow](shared-dependency-workflow.md#keep-one-current-version-in-an-unmerged-registry-pr).

**Completion evidence:** toolchain resolution and dependency analysis for each selected configuration, with remaining host dependencies identified.

## 3. Build graph and feature coverage

- Define targets for source libraries, linked binaries, generators, bindings, packages, and tests at useful cache boundaries.
- When retaining an external package's configure/Make build, follow [external source packages](external-source-packages.md): fetch the maintained source/patch set, declare execution tools and target dependencies, stage installation, and select runtime/debug TAR outputs without DEB-producing actions. Record foreign-action cache granularity separately from native per-source caching.
- Keep reusable SONiC Rust library and binding rules with the library owner. Verify that consumers depend on the owner's target and remove duplicate consumer compilation/binding definitions; normal transitive builds and cache reuse remain valid.
- Compare source and header inventories with the legacy build, including nested directories and conditional sources.
- Trace the component's required outputs to their generation, compilation, and link actions. Trace imported external libraries to pinned package inputs; fetching source alongside an import does not prove that dependency was compiled.
- Declare generated inputs and their dependencies. Make externally supplied generated files explicit interfaces when migration requires them.
- Preserve public include paths, target interfaces, link behavior, and feature selections needed by consumers.
- Use explicit required target lists for validation; inspect incompatible and manual targets deliberately.
- Identify direct and transitive actions that create DEBs, including test fixtures and wrappers, so validation target selections respect the execution approval rule.

**Completion evidence:** clean builds of every required target and a reviewed mapping from legacy inputs/outputs to Bazel targets.

## 4. Runtime and package contracts

- Verify library SONAMEs, exported interfaces, filenames, runtime search behavior, and dynamic dependencies.
- Verify installed paths, architecture directories, relative symlinks, ownership, permissions, and configuration files.
- Check that each required package format has the metadata and contents its consumers expect.
- Exercise a real consumer using the Bazel runtime environment and the extracted package.
- Install the actual package in a clean environment with only its declared runtime dependencies; exercise loading/imports and CLI behavior without Bazel runfiles or test-only search paths masking missing files or dependencies.
- Keep runtime package inputs visible in the downstream Bazel dependency graph.

**Completion evidence:** runtime-loading and package-layout checks plus consumer validation. State separately any Debian metadata or full package-equivalence work that remains.

## 5. Tests and CI

- Run existing unit and integration coverage for the selected configuration.
- For Rust ownership changes, run owner tests and a real downstream consumer on the declared architectures/features. Exercise native linkage and cross-repository public type/trait compatibility when applicable; retain resolved target and source-pin evidence.
- Add focused regression tests for failures introduced or exposed by the migration, such as missing sources, runtime names, or package entries.
- Record tests that need Redis, databases, hardware, or other services, and define where they run.
- Use a CI matrix matching the supported OS and execution/target combinations.
- For component implementation PRs, follow [source PR CI completion](source-pr-ci.md): verify PR-triggered source-repository jobs on the current revision for every declared configuration. Record source build/generation coverage separately from prebuilt-import validation; registry CI alone does not complete source PR CI.
- For claimed cross-compilation support, verify configured tool architectures, run the generator on the execution platform, and compile its output for the target. Native AMD64 and ARM64 builds alone do not establish cross-compilation correctness.
- Pin CI tools and userspace inputs according to repository conventions; check Bazel formatting.
- Build explicit output and test targets and make artifact collection fail on missing required files.
- Before executing Bazel builds, tests, runnable targets, or CI, verify that the selected targets do not create DEBs unless explicit approval covers them. Omit unapproved DEB-producing selections, continue unaffected validation, and record any required checks left pending.
- Inspect downloaded artifacts as consumers receive them.
- Before publishing or updating a build-infra or registry PR, verify it contains exactly one commit relative to its actual base. After a split, verify independent CI selection and reconcile source/consumer descriptions and Project dependency links for each feature.
- Verify a fresh checkout without `MODULE.bazel.lock` builds for each declared configuration, preserves canonical package locks and their dependency selections, produces the ignored Bazel lock as retained CI evidence, and leaves tracked files unchanged. Synchronize workflows, collectors, and documented commands.
- For Rust consumers, start without `Cargo.Bazel.lock`, prepare before dependency evaluation, and validate native AMD64/ARM64 plus downstream owner/consumer and image integration. Verify the actual image checkout is prepared after pristine-source verification; report any installer boundary that remains unvalidated.

### Repository auto-merge

- Enable the repository's `allow_auto_merge` setting for each repository in the authorized onboarding scope.
- Require the supported build/test checks on the target branch using check names and app identities observed in current PR runs. Keep CodeQL and its language analyses informational under [the CodeQL policy](../SKILL.md#keep-codeql-informational); preserve other required checks and unrelated branch protections.
- Verify CodeQL still runs and reports actual results in all PR checks, while no required check, workflow, aggregate, or code-scanning rule makes it a merge gate. Record failures and findings separately from required-check enforcement.
- Use the migration PR to verify that the intended checks appear in `gh pr checks --required`. While one is pending, confirm the normal merge state is blocked and an unscheduled PR reports `viewerCanEnableAutoMerge: true`.
- Record existing bypass permissions. If all checks finished before observation, record the configuration as verified and the waiting behavior as pending until an ordinary CI run provides evidence.
- Treat enabling auto-merge on a particular PR as a separate merge action requiring the user's authorization; repository setup alone does not schedule a merge.

**Completion evidence:** current source PR build/test jobs pass for the declared configurations, expected artifacts are downloadable, skipped or unsupported coverage is visible, and the repository setting and PR-level auto-merge eligibility are verified. Record the PR head, tested revision, run/check URLs, required check identities, and informational CodeQL results separately. Distinguish configuration evidence from an observed pending-check gate.

## 6. Security and generated-code analysis

- Inventory the source files and generated wrappers covered by the previous analyzer pipeline.
- Initialize compiler tracing before the Bazel build and prevent cached compiler actions from bypassing extraction.
- Keep dependency download caches only where they do not hide compilation from the analyzer.
- Compare extracted and reported source coverage, including generated files outside the source tree.
- Preserve undeclared-header and dependency checks while accommodating analyzer execution constraints.

**Completion evidence:** analyzer jobs pass and coverage differences are explained. Compilation of a file and reporting findings for that file are separate checks.

## 7. Debug artifacts

Apply this section to native ELF artifacts that require source-level debugging.

- Verify the selected `sonic-build-infra` rules before using `sonic_deploy_tar`, `force_debug_build`, or `debug_symbols_layer`.
- Derive the deployed runtime copy and detached debug information from one linked ELF.
- Retain the selected optimization policy while generating the required debug information.
- Verify build-ID agreement, debug-link checksum, useful DWARF sections, and GDB source-file and line lookup.
- Retain or publish runtime and symbol archives together with architecture, configuration, build IDs, and checksums.
- Record source-bundling or split-DWARF requirements separately; the existing detached-ELF collector does not supply those automatically.

**Completion evidence:** a matching runtime/symbol pair and a successful debugger lookup for each required configuration.

## 8. Downstream image integration

- Keep new or changed dependency build/packaging support in separate producer PRs, grouped by component: related DEBs from one component stay together; different components get separate PRs. Keep the container PR focused on consuming those targets and image integration, with actual prerequisite links recorded.
- For a Docker/OCI build request, inventory every project runtime component and transitive dependency, including base-image contents, and bind each to compatible Bazel source/package targets. Reuse existing owner targets and identify missing feature support before adding import adapters. Pinned Debian APT packages remain allowed; Make-produced project artifacts remain migration gaps under the [OCI runtime policy](../SKILL.md#build-oci-images-with-bazel-built-project-runtime-dependencies).
- For DEB-to-OCI assembly, record the selected `rules_distroless`, `tar.bzl` BSD tar toolchain and `rules_oci` roles/versions under the [upstream-component policy](../SKILL.md#reuse-upstream-components-for-deb-to-oci-assembly). Verify the consumer BUILD file declares upstream extraction and assembly directly, generic archive/OCI processing stays upstream, and no shared importer or custom assembly wrapper is introduced without explicit scoped approval. Preserve package metadata and order, and validate runtime/debug identity and reproducibility.
- Update the consumer's module dependencies and runtime package targets.
- Verify that the container loads the intended library or binary, especially when a base image already contains another copy.
- Build the debug variant from the same runtime image and add matching symbols and tools.
- For imported Make-built or prebuilt content, provide symbols from the matching producer build or record the coverage gap.
- Validate the user-facing Make/Bazel entry point required by the current migration phase.
- Follow the Docker template's locked APT selection, base-collision, installed-state, runtime/debug ancestry, archive and producer-transition checks; distinguish structural checks from actual image and service validation.

**Completion evidence:** project runtime source coverage, consuming-image behavior, package selection, and debugger lookup are verified in the actual image. Record explicit narrower user scope and any remaining Make producers; image assembly or installer CI alone does not complete a default OCI migration.

## 9. Documentation, performance, and rollout

- Document prerequisites, exact build/test commands, artifact paths or download steps, supported configurations, and known gaps.
- Record clean, no-op, and representative source-edit timings when required by the task or rollout criteria, including cache settings and machine details.
- Compare required runtime behavior, package layout, dependency versions, and relevant image characteristics with the baseline.
- Apply the project's migration phases and agreed exit criteria before changing defaults or retiring legacy paths.

**Completion evidence:** another developer can reproduce the declared configuration from a clean checkout, and the applicable rollout criteria have evidence.

## Suggested completion record

| Field | Record |
| --- | --- |
| Source | Repository and revision |
| Integration | Base and head revisions, tested merge or ancestry evidence, and resolved shared dependencies |
| Configuration | OS, toolchain, execution/target architecture, feature flags |
| Required outputs | Explicit target labels and package formats |
| Migration boundary | Source compilation, wheel/package production, image assembly or binary import; remaining producers |
| Validation | Tests, runtime/package checks, and service requirements |
| Analysis | Analyzer jobs and source-coverage result |
| Auto-merge | Repository setting, target branch, required checks, bypass permissions, and PR eligibility evidence |
| Artifacts | Locations, checksums, and matching debug information |
| Consumers | Module and image integrations verified |
| Performance | Environment, cache settings, and measured scenarios when applicable |
| Remaining work | Pending configurations, gaps, and downstream dependencies |
