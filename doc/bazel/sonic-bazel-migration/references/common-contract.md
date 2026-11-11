# Shared contract for every migration implementer

The lead agent, independent implementers and delegated agents must read this entire file before analysis, implementation or verification. Task summaries, analysis results and type examples do not replace it. This contract applies to every production type and language.

## Reading and handoff

Read this contract first, then the phase documents and applicable type routes and topics. Read only sections applicable to the task, without loading unrelated languages or image types.

| Responsibility or operation | Required reading |
| --- | --- |
| Original build analysis | [Analysis contract](analyze-make-component.md) |
| Implementation | [Implementation](implement-component.md), [infrastructure](infrastructure.md) and the applicable type route |
| Verification | [Acceptance contract](review-port.md) and the interface topic |
| Phase handoff, progress update or resumption | [Phase records and resumption](phase-handoff.md) |
| First Bazel invocation | [Build preflight](infrastructure.md#build-entry-and-cache-preflight) |
| New rules, macros, providers or helpers | [Necessity and ownership](infrastructure.md#rule-necessity-and-ownership) |
| Host tools, configuration probes or actions | [Tools and hermeticity](hermetic-tools.md) |
| Generation, documentation, archive, compression, ELF or image tools | Applicable [tool recipes](tool-recipes.md) |
| Sources, patches or source overrides | [Source preparation](source-and-patches.md) |
| APT libraries | [APT library interfaces](use-apt-libraries.md) |
| New dependencies or resolution inputs | [Dependency locking](dependency-locking.md); apply this contract's fixed APT input requirements |
| Source ownership, module selection or local consumption | Applicable [module rules](register-bazel-module.md) |
| Configuration and feature switches | [Configuration contract](configuration.md) |
| Installation, packaging or image consumption | [Installation interfaces](install-interfaces.md) |
| Explicitly requested final DEB | [Shared packaging](build-deb-with-sonic-deb.md) |

Record files read, applicable sections and constraints in the task's existing analysis, implementation and verification records. Delegations must include paths to this contract, the phase document and applicable topics; recipients must read them themselves. Before handoff, the lead checks reading records against implementation and evidence. Read newly triggered requirements when phases or inputs change; unchanged documents need not be reread.

## Scope and input identity

Follow the user's deliverables, modification scope and verification scope. Before changing a dependency, identify the requested deliverable and consumer target that require it, document the gap in the existing interface, and list the minimum files and repositories to modify. Include this necessary work under the [main entry's scope rule](../SKILL.md#establish-the-requested-outcome), honoring explicit user limits. Dependency discovery alone does not establish a need to modify its producer. Record independent defects or improvements separately and obtain explicit authorization before adding them to the task. Protect existing user changes and record source, dependencies and effective build configuration. Assign one writer to each shared file. Freeze inputs before validation; coordinate before changing frozen inputs and revalidate.

## Native builds and tools

Ordinary components must use native Bazel language rules and explicit actions for generation, compilation, linking, installation and packaging. Do not use rules_foreign_cc, configure_make, or shell/genrule/custom wrappers around configure, Make, CMake or dpkg-buildpackage. Retain the documented Linux kernel Kbuild/Make exception and record its procedure and verification scope under the [kernel route](image-recipes.md#2-kernel-production-and-public-interfaces). Other specialized build-system exceptions require explicit user approval of the concrete approach. Exceptions still require hermetic inputs. Migration-time controlled Autoconf probing is a separate analysis procedure; it does not authorize configure in regular builds.

Select tools in this order: maintained Bazel Central Registry (BCR) rulesets/toolchains that satisfy the analyzed version/feature contract, compatible existing project/shared tools, then pinned source-built tools. Record the BCR modules/versions checked and why each earlier option fails the contract before falling back. Follow the [custom-module approval rule](../SKILL.md#check-bazel-central-registry-before-custom-modules) when developing a BCR alternative. Reuse Bazel-managed pinned prebuilt tools where applicable. Declare tools, interpreters, execution-side libraries, plugins, templates and data. Tools use exec configuration; target headers and libraries use target configuration. Do not rely on host installations or client PATH discovery for undeclared tools. Use explicitly allowed Bash and GNU Coreutils under the project's base-tool contract. The execution scope is the project's Linux platforms; do not automatically add macOS support. Inspect rule source for actual attributes and capabilities.

## Minimal declarations and direct file consumption

Identify inputs, outputs, tool invocations and necessary transformations before selecting rules. Declare sources, configuration, compile/link options and install manifests directly at their BUILD use sites. Extract shared data only for a real reuse contract. Reuse existing rules whenever they express the operation. Before adding extensions, record the missing transformation and its owner: generic mechanisms in shared infrastructure, component-specific transformations in the component, dependency interfaces at the producer. Complete the split and integration in this task.

Compilation and generation must consume declared files, labels and providers directly. Do not copy input/header trees or reconstruct source trees to repair paths or input isolation. Fix the tool or owning shared interface when its path behavior cannot consume hermetic inputs. Source patching and installation/archive output layouts have separate production responsibilities; they cannot bypass direct consumption. Keep probe scripts, raw results, analysis reports and audits in the task's temporary directory from creation. Regular builds retain actual inputs, native actions and required templates only.

## Configuration and dependencies

Migrate configurable Make inputs to Bazel configuration, keep fixed parameters fixed and derive architecture differences from platforms. Propagate each configuration through generation, compilation, dependencies and installation consumers. Probe Autoconf components with the controlled target toolchain during migration, then generate required configuration from templates during regular builds. Regular actions must not run configure.

Consume APT packages by locked source, version, architecture and checksum. With unchanged sources, preserve locked versions and checksums. Extending a collection resolves only new packages and their necessary new dependencies; it must not upgrade existing packages incidentally. Report conflicts with the existing lock. Source changes require explicit authorization and --allow-source-change; an explicitly authorized existing-package version change under unchanged sources uses --allow-version-change. Neither switch permits changing the identity fields or checksum for an existing suite/name/architecture/version package key. Review all resulting lock differences. Shared-rule fixes, module upgrades and rebuilds do not justify APT refreshes. Keep source component identity; consume system libraries through public APT library targets.

The three APT roles export image/rootfs data/control, target-library CcInfo, and executable closures for exec tools. Maintain one global source configuration and one explicit production APT lock; multiple package collections for all three roles reference that lock. Propagate source changes through the update entry point. Normal builds read the lock and check input consistency.

For every ecosystem, inherit effective original dependencies and patches on first migration and retain existing locks. Prefer compatible shared versions for new dependencies; justify necessary changes and minimize scope. Follow [version selection](dependency-locking.md#version-selection-criteria), maintain requests, locks and derived exports in their owning repositories, and perform [version-control checks](dependency-locking.md#version-control-and-handoff-of-locks). Every new dependency or consumer entry requires running applicable locking/update operations, lock checks and consumer validation in this task, even with an existing lock, shared dependency or expected empty diff. Go requires native version/content checks and the root ZIP digest lock. Prepare missing tools or retain a blocked status.

## Installation and verification

Native image components export installation TARs, applicable symbols and metadata. Python distribution owners build wheels; OCI/rootfs assembly installs those wheels through shared wheel_layer into installation TARs, preserving metadata and the complete locked runtime closure. Do not require a parallel direct-source Python installation target. Existing native/generated bindings packaged with native runtime TARs may retain that interface. Source DEB installation branches consume contents and metadata directly, without producing then unpacking a DEB. Install pinned third-party distributions through their managed input path and reuse installed results. Produce a final DEB only when explicitly requested, using shared sonic_deb.

Validate actual Bazel actions, artifacts and consumers against the analyzed contract. Report analysis completion, successful builds, installation checks, registry consumption, image startup and Make equivalence separately. Image archives and approved DEBs that replace Make outputs pass the [Make equivalence check](make-bazel-equivalence.md); component wheels/TARs are compared through their consuming image. Record PASS/FAIL/NOT_RUN/BLOCKED with commands, input identities, artifacts and the first raw error. Completion requires every mandatory check to pass. Implement shared requirements rather than merely recording that they were read.

## Documentation boundary

Describe final usable interfaces, procedures, complete minimal examples and checks at each step. Track implementation status separately. Keep historical experiments, validation logs, temporary evidence paths and discussions out of skill instructions. Task evidence stays in the task directory.

## Publishing and PR policy integration

The main entry retains publishing identity, logical commits, version inheritance, CI, Project and Draft/Ready policies. Technical phase records neither replace them nor authorize extra publishing or history rewriting. Task JSON tracks component build phases; remote PR/Project dependencies and status follow the existing collaboration workflow.

Each PR must build with its complete changes and then-available dependencies. Compatible attribute, mode and output extensions may remain in one rule; introduce a separate interface only for incompatible changes. Same-repository producers and consumers may change together in one commit/PR. Verify the complete interfaces and existing calls; mixed old/new versions are not an additional completion requirement. Prepare cross-repository prerequisites in publishing order under the main entry's Draft and dependency provenance policies.

Locate helpers through the absolute `SKILL_DIR`, the selected skill directory. `TASK_DIR` is the selected task evidence directory, and `BUILDIMAGE_ROOT` is the absolute sonic-buildimage checkout path. Pass repository and evidence paths explicitly so helper invocation does not depend on the working directory. This document does not prescribe a machine installation path, build directory or local application branch.
