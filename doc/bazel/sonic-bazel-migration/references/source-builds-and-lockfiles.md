# Source builds, generated lockfiles, and DASH lessons

Apply this policy when adding or assessing SONiC Bazel support. These are the
user's migration requirements for this workflow. Apply changes within the current
task's scope; an assessment or documentation update does not authorize an
unrelated migration sweep.

## Build the component from source

Build the component's libraries, programs, generated code, and language bindings
from its declared source. Downloading that component's finished DEB, ELF shared
library, static archive, native wheel, container layer, or previous CI output and
repackaging it with Bazel does not complete its source migration. For example,
DASH must generate and compile its schemas, utility library, and SWIG extension;
it must not substitute a downloaded DASH package for those actions.

Audit the selected dependency graph and actual artifacts, not filenames or
repository labels. A `source.json` entry or fetched source archive can coexist
with a target that only imports a binary. Trace the component's files to generator,
compiler, and linker actions; compare coverage with the legacy build. A
`cc_import` consuming a library produced by a declared source-build action is
valid: provenance, rather than the rule's name, decides. Establish clean-build
correctness and source-action coverage, then allow normal Bazel cache reuse;
cached outputs of declared source actions are not prebuilt-package substitutions.

## Allow pinned external binary dependencies

For an individual component, apply the dependency boundary below. A Docker/OCI
build request instead includes all project runtime components, including their
transitive dependencies and inherited base contents, under the
[OCI runtime policy](../SKILL.md#build-oci-images-with-bazel-built-project-runtime-dependencies).
Pinned Debian APT packages are allowed, but importing a project-produced binary
does not satisfy that component's source-build requirement.

The selected policy is a source-built component with declared, pinned external
dependencies. External libraries, native language extensions, test libraries,
compilers, and generators may come from APT packages or wheels; compatible
source-built modules are also valid. Using a binary dependency does not by itself
make the component migration incomplete. Do not expand this into rebuilding the
whole dependency graph unless the user requests that scope.

For each dependency, verify the exact version and integrity, package/source
origin, transitive requirements, execution or target architecture, and relevant
ABI/interpreter compatibility. Use shared dated APT snapshots and package pins,
or hashed requirements for wheels, and record the actual resolved inputs in CI.
Inspect native wheel contents and imported libraries so their runtime needs are
declared. Validate the delivered component package with its declared runtime
dependencies; compilation alone cannot establish installed compatibility.

Capturing a package's bytes and dependency closure does not model its producer's
source compilation in Bazel. Describe that boundary accurately without treating
it as an automatic blocker. If the requested migration unit is protobuf itself,
importing Debian's protobuf library does not implement that source migration;
if the requested unit is DASH, a pinned protobuf package is an allowed dependency.

Reuse compatible existing modules and shared package sets first. Put reusable
third-party source rules or package adapters, patches, overlays, language
bindings, and dependency-owned tests in `sonic-bazel-registry`; SONiC-owned
dependency source support belongs in its own repository and is then registered.
Shared toolchain/build/packaging logic belongs in `sonic-build-infra`. Follow the
existing one-module-per-registry-PR rule and keep
[one logical commit per independent fix or feature](../SKILL.md#keep-one-logical-commit-per-fix-or-feature).
A single-feature PR normally has one own commit; corrections stay with that
feature. User-authorized consolidations preserve separate feature commits even
when they update one unpublished module version. Preserve published registry
releases unchanged when introducing a successor. For unreleased entries
across the affected open stack, [keep one current candidate per module](shared-dependency-workflow.md#keep-one-unreleased-candidate-per-module)
instead of retaining every intermediate source revision.

## Separate execution tools from target dependencies

Programs run during the build and their private runtime libraries/data belong in
the execution configuration. Use the shared pinned `build_tools` set for APT
tools and select them with `cfg = "exec"`. Libraries and headers consumed by the
component remain explicit target dependencies. The compiler's system ABI
foundation belongs in its target sysroot. These roles apply whether inputs are
source-built or imported binaries.

The same package may be needed in both roles. An AMD64 builder generating code
for ARM64 needs AMD64 protoc and its private libraries, but ARM64 libprotobuf for
the application. Declare both uses; do not link the execution-side payload into
the target. Preserve matching generator/header/runtime versions and validate
cross-platform pairs separately from native builds. See [build tools and sysroot](build-tools-and-sysroot.md).

For DASH, keep protoc and the C++ runtime at 3.21.12. Pinned APT protoc and
libprotobuf are allowed; a protobuf 29 upgrade or source-building external
dependencies is not required for this migration. Python protobuf has its own
version and compatibility requirements; do not force its version number to match
the C++ release.

## Keep canonical package locks in Git

Classify lockfiles by their role, not whether a tool generates them. Keep the
reviewed package dependency selection in Git:

| File or role | Treatment |
| --- | --- |
| `requirements.in` or another direct dependency declaration | Commit it alongside the canonical lock; direct pins alone may leave transitive versions unresolved. |
| Canonical `requirements_lock.txt`, `uv.lock`, `Cargo.lock`, or APT package lock | Commit the resolved versions, sources, and package integrity information, including transitive dependencies. |
| `MODULE.bazel.lock` and, where used, `Cargo.Bazel.lock` | Generate and ignore them under the Bazel metadata policies below; retain them as CI evidence. |

For example, a pinned Python test framework can still allow several versions of
its dependencies. A generated requirements lock records the selected transitive
versions and artifact hashes. Regenerating it from direct requirements against
a changing package index during every build can change dependencies without a
Git change. Keep that lock checked in and update declarations and lock together
when intentionally changing dependencies. Document the regeneration command,
tool version, Python version, and relevant platform inputs.

A requirements file may instead be an export of another checked-in canonical
lock, such as `uv.lock`. In that case, generate the export during preparation
with pinned tooling before its consumer needs it. Verify that it preserves the
locked versions, sources, and integrity for the supported configurations and
leaves the canonical lock unchanged. Do not re-resolve unpinned dependencies or
add a second canonical lock solely to make the export untracked. Apply this
distinction consistently across source CI and downstream image builds.

## Generate Bazel resolution state in CI

Do not commit the workspace's generated `MODULE.bazel.lock`. Add it to
`.gitignore`, remove an existing tracked copy when updating that build, and let
each supported CI configuration generate its resolution state with
`--lockfile_mode=update` (or the verified equivalent default). Do not require a
checked-in lock with error mode, or disable generation when the lock is required
as CI evidence.

Keep the actual dependency inputs checked in: Bazel/module/toolchain versions,
immutable source revisions, source integrity hashes, dated package
snapshots, and applicable requirements/uv/Cargo/APT package locks. The Rust preparation policy below also excludes generated `Cargo.Bazel.lock`
from Git. Preserve `Cargo.lock` and other ecosystem/package input locks; neither
policy permits floating dependency versions. Inspect extension inputs
and pin their source and package dependencies. Registry URLs follow the
[maintained-branch policy for local builds and CI](../SKILL.md#use-main-registry-urls-for-local-builds-and-ci);
both use the canonical registry URL, such as `main`. Omitting the generated lock
from Git does not justify a registry commit pin.
An archived lock is evidence of the tested resolution, not by itself a guarantee
that mutable inputs resolve identically later.

When changing this policy in a repository:

1. Update ignore rules, CI commands, helper scripts, artifact collectors, and
   documentation together. Remove assumptions that the lock is tracked source.
2. Verify a fresh checkout without `MODULE.bazel.lock` builds the required
   targets and tests for each declared configuration. Use update mode
   consistently; do not depend
   on a developer's stale local lock.
3. Retain the generated lock and resolved graph with validation artifacts,
   identifying the tested revision, configuration, architecture, and hashes.
   Label generated evidence separately from checked-in input declarations.
4. Confirm `MODULE.bazel.lock` is ignored and not tracked, canonical package
   locks remain checked in, and the build has not changed tracked files.
   Recheck explicit input pins in the diff.

This is the SONiC migration convention selected for this workflow. Bazel itself
supports generated lockfiles and recommends committing them; see its
[lockfile documentation](https://bazel.build/external/lockfile). Do not present
this project policy as a universal Bazel requirement.

## Generate Rust Bazel metadata before dependency evaluation

`Cargo.lock` is the reviewed source dependency lock and stays in Git.
`Cargo.Bazel.lock` is JSON metadata for `rules_rust`'s crate generator; generate
it during preparation and ignore it alongside `MODULE.bazel.lock`.

Use the existing upstream generator in the pinned `rules_rust` version. Shared
preparation belongs in `sonic-build-infra`; thin component launchers pin and
verify its source revision and SHA256 before running it. Preparation happens
before the first command that evaluates Bazel's crate extensions, including
formatting or analysis helpers that can resolve the same graph.

For `rules_rust` 0.74.0, keep `skip_cargo_lockfile_overwrite = True` and the
configured metadata label. Generate as a root module with the supported
workspace repin operation, then consume the result. The helper must snapshot
`Cargo.lock`, reject mutation and compare every selected generated package's
name/version and source or registry checksum with that lock. Explicitly updating
a Cargo source pin alongside its matching Bazel module is a reviewed dependency
change, not preparation. Do not use unconstrained dependency updates to make
preparation succeed.

Non-root modules in this upstream version require the metadata file before
crate-extension evaluation. A `genrule` cannot meet this requirement. Prepare
owners before consumers: Common, SWSS, then sonic-buildimage. Resolve dependency
source from the declared module, prepare a private writable copy or an already
verified image checkout, and apply that exact copy through a module override.
Do not recreate Common's Rust target in SWSS, introduce a second source pin, or
write generated files into the repository cache. Refresh owned overrides before
resolving changed inputs so a previous staged copy cannot mask the new pin.

When implementing or auditing this policy:

1. Remove only the generated `Cargo.Bazel.lock` from tracked files; keep
   `Cargo.lock` tracked and unchanged during ordinary preparation.
2. Start without generated Cargo/Bazel metadata, prepare, then build/test on
   each supported native architecture. Validate Common's public Rust interface
   through SWSS as well as standalone library tests.
3. In an image build, verify the pristine source checkout first. Prepare Rust
   metadata in the actual writable Bazel source checkout afterward, before
   package and image commands. Do not rely on files generated before a fresh
   clone, which will discard ignored outputs.
4. Retain both Cargo locks and a receipt recording generator/source inputs,
   hashes, selected packages, exact source revisions and architecture with the
   matching run. Regenerate even when caches contain old metadata; caching
   compilation remains allowed after preparation validates current inputs.
5. Test failure on lock mutation or pin mismatch and ensure failed preparation
   cannot leave usable stale metadata. Update native source CI, CodeQL,
   downstream callers, artifact collectors and documentation together.
6. Distinguish validated source packages, container integration and full installer
   execution. Record blocked runner, capacity or missing-input requirements;
   passing helper tests alone does not establish AMD64/ARM64 or image success.

This is a SONiC workflow choice, not a claim that upstream Bazel or `rules_rust`
requires keeping generated lockfiles out of Git. Recheck the upstream behavior
when changing the selected rules version.

## Lessons from the DASH migration

The [DASH source-build PR](https://github.com/securely1g/sonic-dash-api/pull/1)
exposed the following boundaries. Recheck current revisions before treating this
historical snapshot as current status.

| Lesson | Required practice |
| --- | --- |
| A Bazel package/import target can pass without compiling the producer. | Verify source actions for the migrated component. Record external package imports separately; their presence does not prevent component migration completion. |
| Pinned dependencies and source-built dependencies are different properties. | Check package integrity, architecture, ABI, and runtime requirements. Require dependency compilation only when it is itself in the requested source-migration scope. |
| The earlier C++ prebuilt import covered only part of Make's installed contract. | Inventory generated headers, language bindings, helpers, CLI, package layout, ownership, and modes as well as the main library. |
| Bazel's runtime environment can hide package failures. | Install the real package with only declared runtime dependencies and test it without Bazel runfiles or extra library/Python search paths. |
| Native dependency packaging and installation can fail despite a successful link. | Exercise the installed loader/import path, SONAME/ABI, and package metadata, including parent-directory handling. Fix common packaging behavior in build-infra. |
| A downstream workspace can select a different Python default. | Declare the intended binding ABI/headers and validate a real external consumer as well as the source checkout. |
| Debug artifacts must match the deployed ELF. | Split runtime and symbols from the same linked output; verify build IDs, debug-link checksum, and debugger lookup in delivered artifacts. |
| Registry CI does not establish source PR health. | Require current-revision source PR CI for declared configurations, then validate the registered module separately. Inspect downloaded artifacts and their provenance. |
| Generated APT resolution data made the Bazel lock roughly 5.7 MB. | Keep explicit inputs pinned, regenerate the ignored Bazel lock, and archive resolution evidence in CI. Size is context; the no-check-in rule applies regardless of file size. |
| Commit-hash suffix order need not follow release order. | Follow the registry version policy, verify the intended successor wins resolution, and preserve published versions unchanged. |
| Keeping every draft registry revision turned one DASH proposal into four versions and eight native jobs. | Keep one unreleased candidate per module across the affected open stack; preserve published entries, recheck publication before cleanup, refresh consumer selections, and remove superseded draft metadata and CI jobs together. |

At DASH source revision
[`64985db`](https://github.com/securely1g/sonic-dash-api/commit/64985db0113ab06d9ae058fed53676e4c129d8c8),
DASH's generated C++, SWIG binding, library, and packages were source-built.
Its external target protobuf and Boost test libraries came from pinned Debian
packages, and Python protobuf included a pinned wheel's native extension (the
installed-package test used Debian's Python protobuf). These are permitted
external inputs under the selected policy, not unfinished source-migration work.
The protoc execution bundle and compiler foundation are also declared inputs.
Retain the distinction between the tested Python environments, and do not claim
that every dependency was compiled from source or that component CI establishes
full SWSS/image integration.
