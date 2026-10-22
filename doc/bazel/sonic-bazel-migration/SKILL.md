---
name: sonic-bazel-migration
description: "Add or assess Bazel support for SONiC component repositories, including build contracts, packaging, CI coverage, and downstream image integration. Use for migration work and completion audits."
---

# SONiC Bazel Migration

Use the existing build contract as the baseline, model it explicitly in Bazel, and validate the installed artifacts through their consumers. Apply the stages relevant to the user's requested scope; a scoped fix or audit does not require completing an entire repository migration.

## Establish the requested outcome

- Identify the component, source revision, requested configurations, and whether the task is a proposal, implementation, validation, or downstream integration.
- Read applicable repository instructions and current build documentation. Inspect existing Bazel work before designing replacements, and preserve useful upstream history when adopting it.
- Treat design documents and historical examples as evidence. Verify current rule behavior and supported configurations in the versions selected by the task.
- Honor the user's current request and previously established authorization. For an implementation job invoking this workflow, necessary common work in `sonic-build-infra` and `sonic-bazel-registry` is part of the component migration, including the commits, branch pushes, and pull requests needed to submit that work. Do not request separate approval solely because this necessary work is in either shared repository. Honor narrower user limits, such as a request for local edits only. Follow the onboarding and merge instructions below; unrelated repository changes require their own user request.

For migration planning, implementation or completion review, read [the migration workflow](references/migration-workflow.md). Select source compilation, Python wheels, Docker assembly, or Debian package import/production explicitly; each has its own completion evidence. For container work, apply the runtime source-build requirement below and use [the common Docker template](references/docker-image-template.md). Its imported-package adapter is for allowed external inputs or an explicitly narrower task; it does not waive source-build coverage. Use [the migration checklist](references/migration-checklist.md) to record scope and results. Read [the swss-common lessons](references/swss-common-lessons.md) when working with native libraries, bindings, packaging, or CodeQL, or when a similar failure needs diagnosis.

## Use the SONiC workspace layout

Use the `sonic-public` directory under the workspace selected by the controlling task. In the paths below, `<sonic-public>` means that resolved directory; do not infer a new workspace from a PR worktree's current directory.

- Keep each base repository at `<sonic-public>/<repository-name>`. The directory name must exactly match the public GitHub repository name, including case, such as `sonic-swss-common` or `SONiC`. Do not add owner, branch, or task suffixes to the base repository name.
- For every PR, create or reuse a linked Git worktree at `<sonic-public>/wks/<repository-name>-<branch-abbrev>`. Make PR changes in that worktree; keep the base checkout available for repository management.
- Use a short, stable, filesystem-safe abbreviation of the PR head branch. Omit routine prefixes such as `codex/` or `docs/` and replace remaining slashes with hyphens. For example, `sonic-swss-common` branch `codex/bazel-armhf` uses `<sonic-public>/wks/sonic-swss-common-bazel-armhf`. If abbreviations collide, append `-pr<PR-number>`.
- Before reusing a worktree, verify its repository, full branch name, and commit against the intended PR. Record the PR URL, full branch, and working directory in the handoff or triage record.

Existing checkouts outside this layout require an inventory before migration: inspect registered worktrees, local changes, and active builds. Preserve branches, uncommitted files, and retained build state. Move linked worktrees with `git worktree move` when supported, and repair worktree registrations if a base repository is relocated. Do not discard existing work to enforce the naming convention.

## Use the correct publishing identity

For SONiC migration work published through `securely1g`, create PRs with the authenticated GitHub account `securely1g`. GitHub authentication does not set Git commit metadata: all new agent-authored commits must use `securely1g@gmail.com` for both author and committer email, and for the agent's `Signed-off-by` trailer when a sign-off is included.

After verifying the destination repository, set `git config --local user.email securely1g@gmail.com` in its checkout. Preserve the user's configured name and unrelated global Git identity. Check the effective author and committer with `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`; environment variables, worktree configuration, and command-line overrides can supersede repository configuration. Do not override the required email when committing.

Before pushing, inspect the actual new commits' author, committer, and sign-off metadata, not just configuration or the GitHub login. Correct mismatched commits created by the agent within the authorized branch before publishing. Preserve original authorship and trailers on imported contributor commits; this rule is not permission to relabel upstream history. For an authorized rewrite of an unmerged branch, verify the current remote SHA and use an exact `--force-with-lease`. Report already merged mistakes without rewriting the shared target branch unless the user explicitly authorizes that history change.

## Use clear, simple language in PRs and commit messages

Use clear, simple language for PR titles, descriptions, and commit messages. Explain the problem, what changes, and who needs it. Replace jargon with familiar words or explain it at first use; for example, explain "fixture DEBs" as "sample Debian packages used in tests."

Always include a concrete example in each PR description when possible. Lead with the specific problem and affected consumer, then show an input or action and the behavior before and after the change. Avoid abstract summaries such as "improve package handling" without explaining what changes for the consumer. Base examples on code, tests, or observed output; clearly label illustrative examples and do not present them as reproduced failures.

For example: "Debian libpcap's quoted variables made Bazel record the include path `""/usr"/include"` for BMv2's dependency; the parser now produces `/usr/include`." Keep titles short and straightforward changes brief; put examples and supporting explanations in the description or commit body.

Keep the PR title, description, and commit messages aligned with the final change. Give each new agent-authored commit an imperative summary and a short body explaining the need and resulting behavior without relying on the conversation. Retain useful consumer and prerequisite links, validation evidence, and material limitations. Omit repetition, file-by-file inventories, and routine branch, rebase, or archive history; link detailed evidence when needed.

Review this wording before publishing. When a history rewrite is authorized, improve messages only on unmerged agent-authored commits within that scope; preserve imported contributor commits, their authorship, and shared history.

## Keep separate features in separate pull requests

Put independently useful features in separate PRs, even when they share a Bazel module or downstream image. Keep each feature's implementation, tests, documentation and necessary CI changes together. Use behavior and consumer needs to choose the boundary; separate directories do not require separate registry modules.

For each shared feature, the PR description must identify the concrete consumers that need the change, link their PRs when available, and explain the target or build path that uses it, why it is needed, and the resulting behavior. When no consumer PR exists, name the verified consumer repository and target and state that limitation. Distinguish direct consumers from registry-mediated use and identify when consumers still select an older snapshot containing the implementation. When splitting a PR, update affected consumer descriptions and Project dependency links to match each feature. Follow the [feature-splitting workflow](references/shared-dependency-workflow.md#split-features-and-identify-their-consumers) for independent validation and the wheel-layer/ownership example.

## Keep shared infrastructure pull requests to one commit

Keep every open `sonic-build-infra` or `sonic-bazel-registry` PR created or updated by this workflow at exactly one commit relative to its current PR base, including a stacked base branch. Apply this to each resulting feature PR after a split. Updating an existing open PR includes consolidating its current commits; fold later changes into the same commit. Verify the commit count and cumulative diff after each update.

Follow the existing authorization and identity rules for rewrites, verify the current remote SHA, and use an exact `--force-with-lease`. Preserve truthful contributor attribution in the resulting commit, including appropriate `Co-authored-by` trailers. Do not rewrite merged target branches or sweep untouched PRs to enforce this rule.

## Preserve the build contract

Inventory the legacy and existing Bazel paths before editing: sources and headers, generated inputs, compiler and linker options, feature conditionals, dependencies, package formats, installed paths, and tests. Record the OS, execution and target architectures, and required services for each supported configuration.

Start from the repository's current SONiC Bazel version, registry, toolchains, and target OS inputs; update shared inputs only as needed for the requested migration. Keep transitional compatibility paths isolated. Model libraries, executables, generators, language bindings, packages, and tests as separate targets with declared inputs so Bazel can cache their actions independently.

Check source coverage explicitly. A successful library link can hide omitted source directories, generated files, or feature-specific code. Compare the Bazel graph with the existing build definitions and inspect the resulting consumer interfaces.

## Keep Bazel builds readable and maintainable by humans

Write build definitions that a SONiC maintainer can understand and edit directly.

- **Keep targets near their source code:** use component-level `BUILD.bazel` files, following established SWSS Common and sairedis patterns.
- **Make the build easy to trace:** each target should clearly show its sources, dependencies, relevant compiler settings and outputs.
- **Share meaningful repetition:** use small macros for common build settings and named lists for shared source groups.
- **Keep abstractions simple:** reuse standard Bazel rules and existing shared SONiC rules; introduce custom helpers only when they make maintenance easier.
- **Maintain component BUILD files directly:** avoid large generated source maps or mechanically expanded target definitions. Generating required source code or bindings remains appropriate.
- **Separate validation from normal build execution:** CI may compare Bazel definitions against Automake. Normal Bazel builds should work directly from the maintained definitions without running those comparison helpers. Keep tests and necessary CI changes with the feature they validate.
- **Remove unused machinery:** delete unused generators, wrappers, macros and dependencies in the changed build path.
- **Document routine changes:** explain how to add a source file, dependency or executable, and how CI detects drift.

**Review criterion:** A maintainer should be able to make a routine build change in the owning component's BUILD file, using documented shared settings, without understanding an additional custom build framework.

## Require approval before adding new DEB package definitions

Obtain explicit user approval before introducing a new DEB package definition or packaging target into the build system. This includes new `sonic_deb` targets, Debian package recipes, and wrappers that add a new DEB output. Explain the package's consumer and why an existing output or runtime/debug TAR does not satisfy it before implementation. A general migration, build, validation or CI request does not authorize adding a new package producer.

This approval concerns the package definition, not each `.deb` file produced from it. Once the package-producing scope is approved, ordinary builds, rebuilds, tests and CI of those existing targets do not require another DEB approval. A request to build or validate an existing approved target authorizes its normal package instances, including test fixtures and transitive outputs. For example, rerunning an approved kernel package target to validate a toolchain change needs no new DEB approval; adding a new development-package target does. Honor earlier approval while it remains in force and stay within the requested task.

Before adding package support, distinguish a new producer from execution or maintenance of an existing approved one. Do not stop an authorized validation run solely because it executes `dpkg-deb`, `dpkg-buildpackage`, Make or another packaging tool. Fetching, verifying or extracting existing DEBs and producing runtime/debug TARs do not introduce new DEB package definitions. Preserve existing Make package paths unless the user requests changes to them.

## Build OCI images with Bazel-built project runtime dependencies

A request to build a Docker/OCI image with Bazel includes building all SONiC/project runtime components and their transitive project runtime dependencies with Bazel. Image assembly alone is insufficient. This includes executables, shared libraries, native bindings, Python packages and project-maintained or patched third-party runtime components, including those inherited from the base image.

Pinned Debian APT packages remain allowed external dependencies; rebuilding Debian itself is not required. Do not relabel a project's Make-built DEB, wheel or published binary as an external dependency to avoid migrating its producer. Normal reuse of cached outputs from declared Bazel source actions remains valid.

Before implementation, inventory the final runtime dependency closure and map project components to their source owners, selected features, Bazel source/package targets and actual producer. Reuse compatible owner targets; extend missing source support with its owner. Check feature parity, such as ordinary VS versus DASH-enabled Syncd, rather than assuming any similarly named target is sufficient. Follow the [Docker template's runtime dependency audit](references/docker-image-template.md#require-bazel-built-project-runtime-dependencies).

Make may still orchestrate the rest of the VS installer and the agreed metadata/archive handoff. A successful OCI build or full installer CI does not prove that its runtime components were built by Bazel. Remaining Make-produced project runtime files are migration gaps, including inherited files; report them and do not claim this requirement complete. Honor an explicit user request for a narrower assembly/import task, and label its completion accordingly. A skill edit or read-only audit does not itself authorize migrating unrelated repositories.

### Consume runtime and debug TARs directly for OCI

For TAR-to-OCI work, consume the owner's source-built runtime TAR directly, with matching debug TARs for native ELF outputs. Add missing source/TAR support with that owner. Do not introduce new DEB production, or the CI, registry entries and shared helpers supporting it, merely to reproduce legacy Make outputs, provide debug symbols, or feed OCI assembly.

Before proposing new DEB packaging, identify a concrete consumer repository and target or build step that requires an installable `.deb`, and explain why the TAR interface cannot satisfy it. Keep that separately scoped package work independent of OCI consumers that only need TARs. The existence of a legacy Debian recipe or another optional packaging proposal alone does not establish this need. A genuine DEB consumer does not waive the explicit approval requirement for adding a new DEB package definition.

Preserve the legacy Make build, Debian recipes/control files/scripts, package outputs, default selection, and legacy CI unless the user separately requests changes to that path. Adding a Bazel TAR path does not authorize removing or rewiring the Make package producer. Existing pinned Debian binary inputs and host/kernel installer interfaces that genuinely consume DEBs remain valid separate paths.

Preserve required runtime installation behavior and metadata when composing TARs; do not fabricate dpkg installation state or silently drop that contract. Follow the [Docker template](references/docker-image-template.md#split-dependency-work-from-image-integration) for target selection and actual prerequisite tracking. Missing unrequested DEB packaging is not unfinished TAR-to-OCI migration work.

### Keep dependency build changes out of the container PR

For Docker-to-Bazel migration, put new or changed dependency source-build and runtime/debug TAR support in separate dependency PRs, one per producing component. For example, libnl3's source/TAR support belongs in one PR, libyang3's in another, and their OCI integration in the container PR. When a separately scoped consumer requires DEBs, keep related runtime, development and debug packages from the same component together.

Keep each dependency's build targets, packaging, tests and documentation with its owner. The container PR consumes those targets/versions and contains image composition, Make handoff and image validation. Reuse existing compatible dependency targets without creating unnecessary producer PRs. Link actual prerequisites and follow the existing registry and dependency-readiness rules. Splitting the work does not waive the runtime source-build requirement or require new DEB outputs when runtime/debug TARs already satisfy the consumer; adding a new DEB package definition still requires explicit approval.

## Reuse upstream components for DEB-to-OCI assembly

When adding existing Debian packages to OCI images, use the following upstream components for their applicable roles:

- [`rules_distroless`](https://github.com/bazel-contrib/rules_distroless) for Debian repository resolution, public package payload/control targets, and TAR flattening when needed.
- [`tar.bzl`'s BSD tar toolchain](https://github.com/bazel-contrib/tar.bzl) for extracting local Make-built or otherwise supplied DEBs and composing PAX TARs through declared Bazel actions. Use the toolchain executable for extraction; do not assume the `tar()` creation rule extracts archives.
- [`rules_oci`](https://github.com/bazel-contrib/rules_oci) for assembling the extracted filesystem TARs into OCI images.

Declare extraction and image assembly directly in the consuming BUILD file with public upstream rules and tools. A small declared action, such as `genrule` with the upstream BSD tar toolchain, may connect local DEBs to TAR inputs. Do not introduce a shared `deb_import` facade, a new importer module, or a custom assembly wrapper in either infrastructure or the consumer merely to hide these steps. Such wrappers are deviations and require explicit user approval. Keep SONiC-specific package metadata, architecture, collision and runtime/debug consistency checks separate from extraction and assembly. Do not implement another archive parser, decompressor, TAR assembler or OCI converter. Not every input path needs all three components; local DEBs need not be published to an APT repository first.

**Any deviation requires explicit user approval before implementation.** Verify the pinned upstream APIs, explain the concrete gap and smallest proposed alternative, and record the approved scope in the PR or migration evidence. Missing upstream features, an existing custom implementation, or general migration/CI approval do not waive this requirement. Honor already-granted approval for the same specific deviation. Continue unaffected work while approval is pending.

Importing existing DEBs remains separate from DEB generation and does not authorize running maintainer scripts or claiming full package installation. Follow the [Docker template's import guidance](references/docker-image-template.md#use-upstream-tools-for-imported-deb-layers) and obtain approval before adding a new DEB package definition.

## Build the component from source with pinned external dependencies

Compile the component being migrated from its declared source, including its generated code, libraries, programs, and native language bindings. Downloading and repackaging that component's existing DEB, shared library, wheel, container layer, or CI output does not complete its source migration. Verify its generation, compilation, and link actions; a source archive in a registry entry alone is not proof of compilation. Normal Bazel reuse of cached source-action outputs remains valid.

For an individual component migration, external dependencies may be pinned APT packages, native wheels, or compatible source-built modules. An OCI image request has the broader project runtime scope defined above; its project components are not exempt external binaries. Declare their versions, integrity, transitive requirements, ABI, and execution/target roles; validate the selected files and installed runtime behavior. A pinned binary dependency is an intentional input, not automatically unfinished migration work. Apply the source requirement to an external dependency when that dependency itself is the requested migration unit; do not expand a component migration into rebuilding all its dependencies. Read [component-source and external-dependency policy](references/source-builds-and-lockfiles.md) for the audit and DASH examples. Publish reusable dependency integration through the registry as described below.

### Retain upstream configure/Make for external source packages

When migrating an external source package while retaining its build system, use declared `rules_foreign_cc` actions for its upstream configure/Make build and stage the installed files into runtime and matching debug TARs. Follow [external source packages](references/external-source-packages.md) for source preparation, declared tools and dependencies, cache boundaries, and validation. Reuse Debian-maintained patches and copyright from the pinned Debian source archive when that is the SONiC baseline; do not duplicate them in registry overlays. This source-build path does not produce DEBs or require a separate DEB-packaging module. Preserve the existing central-registry check, dependency ownership and approval rule for new DEB package definitions.

## Keep reusable Rust libraries with their owners

Apply this rule throughout SONiC Rust bazelization: **each reusable SONiC Rust library's owning source repository defines and exposes its Bazel target, and consumers depend on that target.** For example, SWSS Common owns `swss_common`; SWSS uses Common's public target.

Keep the library's source selection, generated FFI bindings, replacements for Cargo build scripts, native link dependencies, features and library tests with its owner. Consumers must not recreate another SONiC repository's Rust library or binding rules in their own BUILD files or Cargo-to-Bazel annotations. A Cargo Git/path dependency does not establish Bazel ownership if the consumer still defines the library's compilation.

For ordinary third-party crates, standard external targets generated by `crate_universe` from pinned Cargo metadata remain valid. Reuse compatible upstream/BCR targets or shared integration under the existing dependency policy where applicable. This rule does not require upstream edits or a separate registry module for each crates.io package. The public type/trait compatibility checks below also apply to third-party crates.

A consumer build may compile the owner's target transitively and reuse its cached outputs. Separate prebuilt library publication is not required. Preserve the needed feature and platform contract; distinct supported configurations may legitimately produce distinct compiled artifacts.

- Map each reusable SONiC crate to its owning repository and public Bazel label before implementing consumer integration. Add missing targets in that owner and publish the required registry entry.
- Route generated Cargo dependencies to the owner's target where needed, then remove obsolete consumer definitions, bindings and native-link wiring. Preserve the consumer's own crate rules and ecosystem locks.
- Align Cargo source pins, Bazel module versions and registry source revisions when they select the same library. Verify actual resolution, including transitive requests.
- When public Rust types or traits cross the repository boundary, share their defining crate targets and compatible features. Matching version strings alone does not make separately compiled Rust crates interchangeable; Common's exported Serde/`serde_core` targets are one example.
- Validate the owner's library/tests and a real downstream consumer for the declared architectures and features. Inspect the resolved graph for the owner target and duplicate consumer definitions; test native linkage and public type/trait compatibility where applicable.

Treat a consumer-owned redefinition of another SONiC repository's reusable Rust library as an ownership gap during implementation and review, even when that consumer builds successfully.

## Keep package dependency locks in Git

Keep the canonical package dependency locks checked in, including `requirements_lock.txt`, `uv.lock`, `Cargo.lock`, and applicable APT package locks, even when a tool generates them. They record reviewed direct and transitive versions and package integrity; direct declarations such as `requirements.in` alone may not fix that selection. Ordinary builds must consume the reviewed locks rather than resolve unpinned dependencies again.

A requirements export may be generated during preparation when another checked-in canonical lock supplies the same versions, sources, and integrity for the supported configurations. Follow the [package-lock and export guidance](references/source-builds-and-lockfiles.md#keep-canonical-package-locks-in-git); do not add a second canonical lock merely to avoid committing a generated file.

## Keep generated Bazel lockfiles out of Git

For SONiC migrations governed by this skill, do not commit `MODULE.bazel.lock`. Ignore it, generate it in CI using Bazel's update mode, and retain it with resolved-dependency evidence as a CI artifact. A clean checkout must build without an existing `MODULE.bazel.lock`; do not require a checked-in file with `--lockfile_mode=error`. Preserve checked-in module versions, immutable source revisions, integrity hashes, toolchain/package snapshots, and separate ecosystem/package locks. Registry URLs follow the [registry URL policy](#use-main-registry-urls-for-local-builds-and-ci) below. Update workflows, artifact collectors, and documentation together; follow the [lockfile validation steps](references/source-builds-and-lockfiles.md#generate-bazel-resolution-state-in-ci).

### Generate Rust Bazel metadata during build preparation

Keep `Cargo.lock` in Git. Generate and ignore `Cargo.Bazel.lock` before Bazel
evaluates crate dependencies, using the pinned upstream `rules_rust` generator
through the shared preparation helper in `sonic-build-infra`. Pin and verify the
helper source, reject unexpected Cargo lock changes, and compare generated
versions, sources and checksums with the tracked lock.

Prepare owning libraries before consumers (Common, SWSS, then the image), using
verified writable checkouts and explicit module overrides. In `rules_rust`
0.74.0, non-root modules need existing metadata; an ordinary build action runs
too late. Update source CI, CodeQL, image preparation, artifacts and commands
together. Validate clean preparation, declared native architectures and actual
downstream integration, retaining generated locks and receipts. Follow the
[Rust preparation checklist](references/source-builds-and-lockfiles.md#generate-rust-bazel-metadata-before-dependency-evaluation).

## Separate build tools from the target sysroot

Classify dependencies by how they are consumed. Programs run by build actions, together with their private runtime libraries and data, belong to the execution side. The target system ABI foundation belongs to the compiler's sysroot; ordinary component and third-party libraries remain explicit target dependencies, whether source-built or imported from pinned packages. Prefer a compatible existing Bazel rule or toolchain; when pinned Debian packages supply execution tools, reuse or extend `sonic-build-infra`'s shared `build_tools` set instead of maintaining a component-local downloader and package lock.

### Use one shared build-tools package set

Use only the existing `sonic-build-infra` `build_tools` APT dependency set for packaged execution tools. Add required tools to that set. Consumers may select subsets and define runtime targets, such as `kernel_runtime` or `foreign_runtime`, from the shared packages; those targets do not require separate APT dependency sets.

**Obtain explicit user approval before introducing another build-tools dependency set**, including a component-specific set such as `kernel_build_tools` or `p4_build_tools`. Explain the concrete requirement, why extending or selecting from `build_tools` cannot satisfy it, and the proposed additional set before implementation. General migration, build or CI approval does not authorize this exception. Honor approval already granted for that specific scope. This rule does not combine target-library or compiler-sysroot dependencies with execution tools.

For custom rule attributes, use `cfg = "exec"` on the edge selecting a tool or its runtime bundle. Set `executable = True` only for an executable target, not a bundle or package payload. Keep target library dependencies in the consuming target's configuration. The `build_tools` name expresses ownership; the dependency transition selects execution configuration. Read [build tools and sysroot guidance](references/build-tools-and-sysroot.md) when adding generators, package-backed tools, or cross-compilation support, including the SAI example and validation requirements.

## Check Bazel Central Registry before custom modules

Before developing a dependency module or build rules, check [Bazel Central Registry](https://registry.bazel.build/) and the dependency's upstream Bazel support. Reuse a compatible central module and validate it with the actual consumer.

If BCR already provides that dependency, **explicit user approval is required before developing a custom alternative**. This includes a separate SONiC module, renamed copy, wrapper or replacement rules. A missing required version, ABI mismatch or packaging difference does not waive approval: explain the central option, the verified gap and the smallest proposed adaptation first. General migration or build authorization alone is insufficient. Honor explicit approval already granted for that specific custom work; do not ask again within its scope.

When a custom module is approved, or no BCR entry exists, reuse upstream build definitions and add only the missing integration. Record the central modules/versions checked, the decision, and any required approval in the PR or migration evidence. Do not duplicate upstream rules merely because a SONiC registry entry is convenient.

### Verify existing patches before switching upstream

Before upgrading or replacing a patched dependency with a public module:

- Compare every existing patch's behavior with the exact candidate upstream release. Record each as **included**, **partially included**, or **missing**, with source evidence; mark unresolved cases as unverified.
- Run the original regressions against the unpatched candidate, then rerun them with any retained fixes. Also run actual consumer tests on the supported Bazel/toolchain versions and architectures. Passing consumer CI or a newer version alone does not prove that the patches are included.
- Record tested revisions, commands and results. Document any minimal test-harness adaptations without weakening the original assertions; report unavailable tests as validation gaps.
- Drop patches only when their behavior is verified upstream or their need is demonstrably obsolete. Retain only proven missing fixes, reuse upstream build definitions, and follow the custom-module approval rule above.

## Publish reusable dependency support through the registry

After the central-registry check and any required approval, check `sonic-bazel-registry` for compatible existing integration. When a third-party dependency needs additional Bazel support, put its reusable source definitions, patches, build overlays, language bindings, and dependency-owned regression and integration tests in its own registry module. Reuse existing support or add only what is missing; do not add or retain that dependency implementation in the consuming repository.

Have `sonic-build-infra` consume the published module. Keep the third-party patch set and its regression and integration tests in the registry; do not maintain duplicate patches, a second patched-upstream test archive or a duplicate test suite in build-infra. Retain build-infra's tests for its own SONiC rules, toolchains and adapters. When moving existing coverage, validate the registry tests on the supported architectures before removing the duplicate patches and tests from build-infra.

For a SONiC-owned dependency, keep its source fixes and Bazel build support in the dependency's own repository, then publish and consume its module through `sonic-bazel-registry`. Keep the consuming repository focused on targets for its own source and outputs, dependency declarations, and consumer integration. Common toolchain, build, and packaging rules belong in `sonic-build-infra`.

## Reassess shared dependencies before adding workarounds

Check the proposed behavior against the current target branch and existing shared fixes. Before adding a compatibility option, identify a real consumer that needs the alternate behavior; tests of the option alone do not establish that need. Retargeting a PR does not refresh its source or validate the combined result.

Trace the shared source commit, registry entry, consumer pin, and resolved module separately. Reuse an existing compatible implementation and prefer ordinary module resolution when it satisfies the graph. A merged or newer version is not proof that it supports the required architectures and features.

When changing toolchain dependencies, refreshing a stacked PR, or retiring a workaround, use [the shared-dependency workflow](references/shared-dependency-workflow.md). It covers early architecture checks, validation against the actual base, runtime-path attribution, and retiring obsolete dependencies after consumers move.

## Use main registry URLs for local builds and CI

Use the registry's canonical maintained URL for both local builds and CI. For `securely1g/sonic-bazel-registry`, commit this configuration in `.bazelrc`:

```text
common --registry=https://raw.githubusercontent.com/securely1g/sonic-bazel-registry/main
common --registry=https://bcr.bazel.build
```

For other Git-hosted registries, use their maintained branch, such as `main` or `master`. Apply the same choice to `.bazelrc` imports, workflows, wrapper scripts, local build instructions and CI reproduction commands. Remove separate local snapshot settings and CI-only rewrites that merely switch a registry SHA to `main`.

This rule changes where Bazel reads the registry catalog, not the selected dependency versions. Keep module versions, source commits and checksums, toolchain and APT snapshots, and package locks pinned. Retain the generated resolution lock and the observed registry revision with validation evidence. A general reproducibility preference or the absence of a committed `MODULE.bazel.lock` does not justify a registry commit pin.

A verified Bazel requirement may justify an explicitly documented exception. Record the affected Bazel version and configuration, the concrete failure or documented constraint, and why the maintained branch URL cannot satisfy it. There is no separate exception for local builds. Missing unmerged entries use the temporary Draft workflow below, not a registry SHA.

## Use one registry endpoint per repository

For each consumer configuration, use one endpoint for each registry repository. Distinct registries, such as `sonic-bazel-registry` and Bazel Central Registry, may coexist. Do not mix branches or commits of the same registry as ordered fallbacks to recover missing entries.

Check every required module at the canonical maintained branch before changing active configuration. Update affected module versions and related pins together only when needed for compatibility; do not float or upgrade dependency versions merely because the registry URL uses `main`. Verify resolved modules, source revisions and integrity, and the required native architecture and feature coverage. Record the checked registry revision as evidence without substituting it into the URL.

If `main` lacks required unmerged entries, keep the committed default `.bazelrc` on `main`. Local or CI Draft validation may explicitly select one authorized, reviewed temporary branch containing those entries. Name the missing module versions and prerequisite PRs, record the branch's observed commit, and replace the default endpoint rather than appending another endpoint for the same registry. If this cannot be prepared or validated, report the missing entries as a blocker. Preserve the one-module-per-registry-PR boundary and existing merge authority; this rule does not authorize merging prerequisites. Follow [registry selection and validation](references/shared-dependency-workflow.md#select-one-endpoint-per-registry-repository) when refreshing a consumer.

Before a consumer becomes or remains Ready for review, remove temporary registry overrides and verify that local builds and CI both use the canonical maintained `main`/`master` URL. Any documented Bazel exception must also use a registry commit verified landed on that branch. Verify every required entry and its selected sources, and update effective configuration, workflows and documentation together. Apply the [registry readiness checks](references/shared-dependency-workflow.md#require-landed-registry-endpoints-before-review) to quiet Ready PRs too; missing or unverifiable prerequisites keep or return the consumer to Draft.

## Validate runtime and package behavior

For native libraries, verify the ABI-facing contract: SONAME, exported interfaces, consumer-visible filename, runtime search behavior, multiarch path, symlink chain, and required runtime dependencies. Test a real dynamic consumer and the extracted package; building a target alone does not establish these properties.

Match the required installed layout, ownership, permissions, configuration files, and package formats. Distinguish a runtime tar from a Debian package or wheel. Preserve each format that remains part of the declared consumer contract.

Use existing functional tests where practical, and add focused regression tests for demonstrated migration boundaries. Record service-dependent or unsupported tests explicitly. Required targets should be named explicitly in validation and CI so platform incompatibility cannot silently remove an expected output from a wildcard build.

## Build debug artifacts from the deployed binary

For native ELF packages using the SONiC debug rules, derive the runtime copy and detached debug file from the same linked ELF. In the reviewed implementation, `sonic_deploy_tar` with `force_debug_build = True` retains debug information before splitting by applying `--copt=-g`, `--strip=never`, and a linker build ID while preserving the selected compilation mode and optimization settings. Verify these semantics in the pinned rule version before relying on them.

Validate build IDs, the debug-link checksum, and GDB source-file and line lookup. Publish or retain the matching runtime and symbol artifacts together when artifact delivery is in scope. A shared source revision alone does not prove that independently built symbols match a runtime binary.

The debug image should extend the exact runtime image whose symbols were collected. The reviewed collector traverses `base` and `tars` edges and collects `DebugSymbolsInfo`; imported Make-built images and prebuilt libraries need an explicit matching symbol payload or a documented coverage gap. Move a component's runtime and symbol outputs into Bazel together when migrating that boundary.

## Validate CI and analysis coverage

- A component implementation PR that adds or changes Bazel support needs PR-triggered CI in its source repository for the declared supported configurations. Registry or downstream CI is additional consumer evidence; it does not supply checks on the source PR. Follow [source PR CI completion](references/source-pr-ci.md) to verify triggers, current-revision results, artifact provenance, and required merge checks before claiming this stage complete.
- Select and validate each required execution/target architecture pair. Reuse the repository's supported matrix; swss-common's native AMD64/ARM64 configuration is an example, not a default for every repository.
- Normal CI may reuse Bazel caches after clean builds establish correctness. Artifact collection should name required outputs and fail when one is absent.
- CodeQL and similar compiler-tracing analyzers must observe compilation after initialization. Use a fresh build configuration that prevents action-cache reuse from bypassing extraction, then compare analyzed source coverage with the previous pipeline.
- Verify generated-code reporting as well as compilation. A generated wrapper can compile successfully while its findings remain outside the analyzer's reported source roots.

### Keep CodeQL informational

Keep CodeQL running and report its actual results, including each language analysis and the aggregate CodeQL check. CodeQL is not a required PR merge check in this workflow. Require supported build/test checks; exclude CodeQL from required status checks, required workflows, code-scanning merge rules, and any required aggregate that would make its result block merging. Preserve other checks and protections.

Informational means non-blocking, not forced success: preserve failures, findings, logs, and run links. Do not add `continue-on-error`, swallow failures, disable analysis, or report a pending/skipped/cancelled run as passed to implement this policy. A successful analysis job does not establish that there are no findings. Verify CodeQL remains visible in all PR checks and absent from required checks after an authorized settings change.

During babysitting, keep reporting and investigating CodeQL failures within the task's scope, without adding a CodeQL requirement or treating its status alone as a merge blocker. Follow [source PR CI completion](references/source-pr-ci.md#detect-missing-ci-during-babysitting) to separate advisory analysis from required build/test evidence. Existing merge authority and repository-settings limits still apply.

## Configure and verify repository auto-merge

For each repository in the user's authorized onboarding scope, enable GitHub's repository-level `allow_auto_merge` setting and require the supported build/test jobs on the target branch. Derive check names and app identities from that repository's current PR runs. Keep CodeQL informational as described above; preserve other required checks and unrelated branch rules. A historical repository check list is not a universal matrix.

Verify that the requirements actually gate the migration PR. While a required check is pending, confirm GitHub reports it as required, the PR is blocked from normal merging, and `viewerCanEnableAutoMerge` is true for an unscheduled PR. Record any existing bypass permissions. If every requirement has already passed, GitHub may hide the auto-merge button because the PR can merge immediately; verify the waiting behavior during the next ordinary CI run before marking it observed. See [GitHub's auto-merge documentation](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/automatically-merging-a-pull-request).

Repository-level auto-merge enables a capability; each PR still needs its own auto-merge request. Activate that request or merge a PR only within the user's merge authorization. Configuring CI requirements must not silently add review requirements, administrator enforcement, bypass changes, or a merge-method policy.

## Track created pull requests

After creating a Bazel migration PR within the user's authorized task, add it to [SONiC Bazel Migration](https://github.com/users/securely1g/projects/1) when the PR's destination repository is owned by `securely1g`. Include draft PRs and PRs for build support, CI, packaging, shared dependencies, or migration documentation. This standing instruction authorizes Project enrollment, Area classification, and the canonical and derived upstream fields below for a qualifying PR; it does not authorize creating the PR itself.

Use the available authorized GitHub tooling. For skill-initiated migrations in the existing workspace, use the saved `gh-securely1g` account selector and verify that its `api user --jq .login` result is `securely1g` before publishing:

```bash
/home/dev-user/.local/bin/gh-securely1g project item-add 1 --owner securely1g --url "PR_URL" --format json
```

When the controlling task explicitly supplies a different executable, use that command for every GitHub operation and example in this skill and its references, and verify its expected account. Do not fall back to a different account implicitly.

Set and verify both metadata fields when enrolling a PR. During authorized PR babysitting or Project reconciliation, reconcile them when PRs are created, updated, retargeted, merged, or closed. Preserve accurate existing values and unrelated fields.

- **Area:** Read the current Project field definitions and select an existing option matching the PR's main purpose. The current choices are `Build support`, `CI and analysis`, `Packaging and debug`, `Documentation`, `Build infrastructure`, and `Dependency registry`. Skill and workflow guidance belongs under `Documentation`; shared toolchain or rule changes belong under `Build infrastructure`. For a PR spanning several areas, choose its primary outcome. Do not create field options as part of enrollment.
- **All upstream PRs:** This text field lists the **direct prerequisite PRs that the current row's PR depends on**. If PR B depends on PR A, put A's compact reference on B's row. For example, `sairedis#1` lists `swss-common#6`. Here upstream describes the dependency direction, not the repository owner. Use `repo#number` labels for `securely1g` PRs and `owner/repo#number` labels for other owners within the controlling task's scope. Remove only a leading `sonic-` from the repository portion of displayed labels in both upstream columns; leave other repository names unchanged. Preserve the full owner, repository and PR number in URLs and stored dependency identities. Separate multiple references with ` · `, deduplicate by full PR URL, and use a stable order. Store each reference as an HTML anchor to its full PR URL, such as `<a href="https://github.com/securely1g/sonic-swss-common/pull/6">swss-common#6</a>`. Escape labels and attribute values, and join multiple anchors with ` · `. Project custom text fields display Markdown link syntax literally; do not use `[label](URL)` there or raw URL labels. Use the compact fallback below when the complete anchors do not fit. Do not put B's downstream dependents on B, include B itself, or expand transitive chains. Establish each link from PR descriptions, review discussions, or inspected changes and pinned revisions; a general dependency between repositories is insufficient. Record full PR URLs and supporting evidence in triage. A blank value means no verified upstream PR is recorded; it does not establish that none exists. Record incomplete investigation or uncertainty in triage instead of inventing links or a `None` value.

Measure the complete serialized cell against GitHub's 1,024-character text-field limit before writing. Prefer HTML anchors when all fit. If they exceed the limit, use a plain compact list such as `buildimage#19 · bazel-registry#57`, preserving every dependency, stable order and deduplication. Resolve shortened unqualified names through a verified Project repository catalog or an explicit alias map; never blindly prepend `sonic-`. Reject ambiguous aliases, and use `owner/full-repository#number` for references not safely represented by that catalog. Deploy this parsing support in the collector and dashboard-ordering helper before writing compact cells. Do not truncate the dependency list, replace it with `+N more`, or clear it after a rejected write. If the complete compact list also exceeds the limit, retain the saved field and report the display limitation; keep the complete linked record in the README and triage.

Maintain an **Upstream PR links** table in the Project README for navigation, with one row per consumer PR and compact Markdown links to it and its verified upstream PRs. Keep that table consistent with the All upstream PRs cells, preserving unrelated README content. The README supports Markdown links and must retain every full destination, including dependencies represented by plain compact references in the text cells. Apply the same shortened display labels to its links. Read back both after changes and verify each saved destination against the dependency evidence. To verify cell rendering, discover the numeric field ID through `GET /users/securely1g/projectsV2/1/fields`, then fetch Project items with `fields=<id>` and inspect that field's `value.html` as well as `value.raw`. Confirm its rendered text contains only the intended compact labels and separators, and each anchor points to the correct PR. For a compact fallback, verify that the parsed full PR identities and their count exactly match the dependency evidence and the README links; the cell is plain text and the README supplies navigation. Paginate as needed. A GraphQL raw-text readback, generic Markdown API rendering, or frontend anchor support alone does not verify actual field display. The user's readability and clickability updates authorize linked labels in the cells and this table.

Links describe required contents, not automatic merge ordering or merge blockers; a consumer may already pin those contents before its prerequisite PR merges. Recheck existing dependency evidence before adding or removing links. Preserve valid cross-repository and historical links: merging or closing a PR alone does not invalidate its relationship. Remove or replace a link when the underlying dependency changes or was disproved; an incomplete investigation is not a reason to clear it. New or retargeted PRs can require updates to their own and other affected consumer rows, including merged PRs. This tracking does not expand the repositories or PR actions authorized by the controlling task.

Discover field and option IDs with `gh-securely1g project field-list 1 --owner securely1g --format json`, then use the same executable's `project item-edit` to set Area and All upstream PRs. Read the item back and verify its nonempty ID, type `PullRequest`, PR URL, and both field values, including an intentionally blank All upstream PRs value after checking available evidence. Include the Project link in the handoff. If enrollment, field updates, or verification fails, report the PR URL and the specific pending operation with the error; do not claim that tracking is complete.

### Dashboard columns

The Project uses two text fields but displays exactly one upstream column per view: **All upstream PRs** is the complete canonical dependency record; **Upstream PRs** is its open-only display. GitHub field names and values are shared across views, so this split supplies the requested heading in Open work without hiding historical links in All PRs. Before each dashboard write, reread the current dashboard instructions, field definitions, values, and relevant saved view settings. A long-running cycle must not restore an older layout or field meaning from its initial prompt or snapshot.

For this Project, preserve these field identities across renames:

| Role | Final field name | Field ID |
| --- | --- | --- |
| Complete canonical dependencies | All upstream PRs | `PVTF_lAHOD5OsO84Bk3xLzhjpYx4` |
| Derived open-only dependencies | Upstream PRs | `PVTF_lAHOD5OsO84Bk3xLzhjsH9A` |

The legacy layout named those same fields `Upstream PRs` and `Open upstream PRs`, respectively. Identify roles from the saved IDs and verified migration evidence, not a name alone. Save the original definitions and values, rename the canonical field to `All upstream PRs` first, then rename the derived field to `Upstream PRs`; preserve both IDs and their values. Read back each write and resume interrupted migrations by identity. Do not create duplicate fields or overwrite conflicts. If identities or types differ, resolve the evidence before changing them. During this transition, coordinate active writers and configure the capable collector with `project.upstream_prs_field: "All upstream PRs"` before another collection; it must never read the newly derived `Upstream PRs` as canonical.

For migration from the old downstream convention, save the original values and supporting evidence before any write. Convert each verified relationship once: an old A-row link to B becomes a B-row link to A, retaining all verified relationships and rebuilding the README table in the same direction. Record the target per-row values and completed writes so an interrupted migration resumes from that saved mapping. Do not reverse already-upstream values, infer direction solely from a renamed field, or clear links merely because evidence is incomplete. Recheck pending writes against current state before resuming and report conflicting changes.

Keep **All PRs** filtered to `is:pr`, displaying **All upstream PRs**. **Open work** and **Ready for review** retain their open-only filters and display **Upstream PRs**. For other saved views, use the derived field only when the actual filter provably restricts results to open PRs; mixed-state, history, and ambiguous filters use the canonical field. Do not infer open-only behavior from a view name. Replace the other dependency column or Architecture in place, preserving column order, other visible columns, grouping, sorting, layout, and unrelated settings. Apart from the authorized All PRs correction, preserve saved filters. If the selected dependency column is already visible, retain its position and hide the other dependency column and Architecture. Add the selected column if none is visible. Read back every changed view and verify exactly one of the two upstream columns is visible.

Keep any existing Architecture field and its historical values hidden; stop maintaining or reintroducing that dashboard column. Continue recording execution/target architectures, emulators, and validated versus planned coverage in PR descriptions and validation evidence.

### Order prerequisites before consumers

Keep this dashboard in dependency order: if B depends on A, A appears above B. After PR enrollment or dependency edits, and at the end of every babysitter or Project reconciliation cycle, run the bundled [dashboard ordering helper](scripts/order_dashboard.py) against current Project data:

```bash
python3 <skill-directory>/scripts/order_dashboard.py --github-cli /home/dev-user/.local/bin/gh-securely1g --apply
```

Use the controlling task's configured GitHub executable when it overrides the standalone default. Omitting `--apply` previews the order. The helper uses the canonical **All upstream PRs** field and a stable topological sort, preserving existing order when dependencies permit. Include merged and closed Project rows in the graph so filtered views inherit a consistent order; never derive ordering from the open-only display or guess links from repository names. This is display ordering, not permission to merge or a claim that a PR is ready.

Keep saved views on manual ordering so the Project's item positions control display. Preserve filters, columns, and grouping. Ungrouped views, including All PRs, Open work, and Ready for review, show the full dependency order; By repository retains its groups and applies that order within each group. A saved field sort overrides manual positions: detect and report it, and restore manual sorting through supported tooling before claiming that view follows dependency order. Do not replace or recreate views to clear their sorts.

Verify the saved order after applying it. On a cycle, concurrent graph change, or failed read/write, retain dependency records, report the incomplete ordering, and retry from fresh data in a later reconciliation; continue independent work. Report linked prerequisites without a Project row as outside the displayed graph rather than silently enrolling or dropping them from canonical metadata. Ordering covers the verified links currently recorded; a blank canonical cell is not proof that a PR has no dependencies.

### Open-only upstream display

Use the derived **Upstream PRs** field identified above for open-only views. Preserve merged Project items, canonical historical links, and the README's complete Upstream PR links table. The collector must read **All upstream PRs** for merge-triggered consumer reassessment. Verify its explicit configured field name and Project definition; a missing canonical field or an intentionally blank canonical cell must never trigger fallback to the derived field. Older deployments that omit `project.upstream_prs_field` retain the legacy `Upstream PRs` name and must be configured before the field rename takes effect.

At enrollment and every babysitter or reconciliation cycle, derive Upstream PRs from each item's current canonical references. Independently verify every referenced PR's current GitHub state, including prerequisites without their own Project item. Include exactly references whose state is `OPEN`, including open drafts; omit merged and closed-unmerged references only from this derived field. Preserve the canonical identities, shortened display labels, deduplication and stable order. Use the grouped clickable format below for this derived field. Clear the derived cell when the verified open subset is empty. A blank derived value says nothing about historical dependencies or unfinished integration. If any prerequisite state cannot be verified within the authorized scope, retain the previous derived value, record the failed refresh, and do not claim it is current. Read back both raw and actual rendered HTML values using the same checks as the canonical field.

Group the derived **Upstream PRs** display by repository: `buildimage: #19 · #21 | bazel-registry: #62`. Keep one repository label per group and make **every PR number clickable**, using HTML anchors to the full PR URLs, such as `buildimage: <a href="https://github.com/securely1g/sonic-buildimage/pull/19">#19</a>`. Preserve repository order by first appearance and PR order within each group, deduplicate by full identity, shorten only the leading `sonic-`, and qualify other owners. This presentation rule does not change canonical **All upstream PRs**, its parsing format, or the complete README links.

Use [the grouped display formatter](scripts/format_grouped_upstream.py) with a JSON list of verified full PR URLs on stdin. Check the complete serialized value against the 1,024-character limit. If all linked PRs cannot fit, retain the saved cell and report the limitation; never drop links, use `+N more`, or fall back to non-clickable text in this derived field. Verify actual `value.raw` and `value.html` after writing, including every destination and group label. Babysitter refreshes must preserve this format while recalculating the OPEN subset from canonical data.

Inspect all saved view filters each cycle and reconcile their visible dependency column using the rule above. An ad-hoc query change cannot switch columns dynamically: choose the appropriate column manually, or save the view's changed filter and let the next reconciliation select it. Do not promise that typing an open-only query immediately changes dependency cells. The derived display never authorizes deleting Project items, clearing canonical links, or cancelling downstream work.

## Surface blockers during PR babysitting

During each complete successful collection, assess open component implementation PRs for missing or stale source CI using [source PR CI completion](references/source-pr-ci.md#detect-missing-ci-during-babysitting), even when no check event or new PR activity exists. An empty Checks tab is missing evidence, not a successful run. Apply the current task's scope and reporting rules to any gap.

During authorized PR babysitting, read [the blocker-reporting workflow](references/blocker-reporting.md) each cycle. Use it to surface decisions and external blockers on the migration Project, link the affected PR discussion, and reconcile unresolved items without duplicate alerts. The workflow records the user's reporting authorization for the `securely1g` migration Project; it does not grant permission to perform the blocked action. Preserve established permissions and continue independent authorized work.

## Reassess consumers after upstream merges

During authorized PR babysitting, follow [the upstream-merge reassessment workflow](references/upstream-merge-reassessment.md). A merged prerequisite must trigger a fresh assessment of each open direct consumer, including consumers without new comments, checks, or commits. Check whether the consumer needs a branch change, especially registry pins, module versions, source archives and integrity, overrides, and lockfiles. Publish and validate necessary changes within existing authority. Record an explicit evidenced decision for each queued consumer; a merge alone does not establish either that an update is required or that the dependency is already satisfied.

## Rebase open PRs when their base absorbs changes

During authorized PR babysitting, check every open PR's live base branch on every cycle, even without new PR activity. Follow [the base-branch rebase workflow](references/base-branch-rebase.md) to identify already-merged patches and necessary integration updates, replay only remaining changes, validate the result, and publish with a freshly verified exact force-push lease. Respect stacked bases, preserve referenced source revisions and contributor attribution, and avoid repeated rewrites merely because a base advanced. Once a prerequisite is in the base, remove its redundant commit instead of preserving an obsolete base to maintain an old commit count.

## Review whether open PRs are still needed

On every complete successful babysitter cycle, assess each open in-scope PR using [the shared-dependency workflow](references/shared-dependency-workflow.md#periodically-review-open-prs), even without new activity. Record whether to keep it, migrate its consumers, close it, or retain a blocker. Close obsolete proposals only within the user's authorization and after checking their remaining integration needs.

## Follow the registry version policy

Before adding or updating registry module versions, read and follow the [SONiC registry version policy](https://github.com/securely1g/sonic-bazel-registry/blob/main/README.md#module-version-convention), including its publishing and migration guidance. Use that policy as the source of truth for source classification, version naming, patch revisions, source commit IDs, and dependency-resolution checks.

Keep one current unreleased candidate per module across the affected open PR stack. Inventory other open registrations of that module; a separate feature PR or unmerged stacked base does not establish a published version. Preserve entries published on the maintained registry branch or by a verified explicit release unchanged. Recheck publication before draft cleanup, then update affected consumers' declared and resolved versions and temporary source pins together. Use [the draft-version workflow](references/shared-dependency-workflow.md#keep-one-unreleased-candidate-per-module) for coordinated edits, registry CI coverage, and reassessment after a merge.

## Set PR draft state from dependency provenance

Keep every in-scope migration PR in Draft while it consumes an unlanded dependency commit or the selected dependency's provenance cannot be verified. This applies to component, infrastructure, registry, image, and CI PRs, including stacked prerequisites, direct pins, resolved registry sources, submodules, overrides, external CI checkouts and consumed artifacts. A merged prerequisite PR or an identical tree does not make its former PR-head commit a landed dependency. The PR's own proposed implementation and its test checkout are not external dependencies. Third-party releases retain their existing version policy.

Every registry PR must also target the registry's maintained `master` or `main` without a stacked base before becoming Ready for review. Reassess dependencies on creation or update, base changes, prerequisite and source merges, and every authorized babysitter cycle, including quiet PRs. Follow [PR draft and review readiness](references/pr-merge-readiness.md) for exact revision checks, coherent pin refreshes, temporary CI branch-filter cleanup, Draft/Ready transitions and readback. Remove obsolete readiness labels when applying this rule and preserve other labels. Keep reasons in triage evidence. Respect explicit user draft holds; Ready for review does not merge a PR, enable auto-merge or replace required CI and merge checks.

## Integrate and report completion

The two shared infrastructure repositories are `sonic-build-infra` and `sonic-bazel-registry`. Put common toolchain, build, and packaging logic in `sonic-build-infra`, and shared module versions and registry metadata in `sonic-bazel-registry`. Use the forks selected by the user or the component's current configuration, and verify their upstream relationships and pinned revisions before editing or creating a pull request; do not assume the component already consumes a particular fork. Component repositories own build targets, packages, tests, and local CI for their own source and outputs, plus consumer integration; consuming image assembly belongs in `sonic-buildimage`. Keep shared changes limited to the common work needed by the component migration.

For module registration or update work in `sonic-bazel-registry`, scope each PR to one module. Keep that module's required metadata, version entries, source definitions, patches, overlays, and validation together. When a migration changes multiple modules, use a separate PR for each module.

Follow the migration phase and exit criteria selected by the project. The [SONiC Bazel migration HLD](https://github.com/sonic-net/SONiC/blob/master/doc/bazel/bazel_migration_hld.md) describes the upstream phases; inspect a fork's HLD when it carries applicable design changes. Preserve the legacy path for configurations whose migration phase still requires it.

Report completion by configuration rather than by repository name alone. Include the source revision, OS/toolchain, execution and target architectures, features, required targets, test coverage, artifact formats, debug coverage, and downstream consumer validation. Distinguish verified results, planned work, and unresolved gaps. Record clean and representative incremental timings when performance evaluation is requested or part of the project's exit criteria.
