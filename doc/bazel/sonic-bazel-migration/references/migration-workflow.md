# SONiC migration workflow and completion evidence

Use the sections matching the requested deliverables. Source compilation,
package production, image assembly and binary reuse are different responsibilities;
a successful result in one does not establish completion of another. An explicit
assembly-only task may leave producers unchanged. By default, a Docker/OCI build
request includes Bazel source builds for all project runtime dependencies under
the [OCI runtime policy](../SKILL.md#build-oci-images-with-bazel-built-project-runtime-dependencies);
pinned Debian APT packages remain allowed.

## Define the producer and consumer boundary

Record the source revision, old and new producers, consumer target/interface,
required artifacts, OS, execution and target architectures, feature settings and
required services. Identify inputs still supplied by Make or published binaries.
Derive the matrix from the product contract; two native architectures do not
establish cross-compilation support.

| Requested work | Implementation and acceptance |
| --- | --- |
| Compile a component | [Source build](#source-build): declared generation/compilation/link actions, source coverage and real consumers |
| Retain an external package's configure/Make build | [External source packages](external-source-packages.md): declared upstream source build, staged runtime/debug TARs, no DEB production |
| Produce Python wheels | [Python distributions](#python-distributions): source library plus complete wheel and installed-package checks |
| Build a Docker/OCI image | [Docker assembly](#docker-assembly): Bazel-built project runtime dependency closure, shared structure, checked payloads, installed runtime and exported archives |
| Reuse existing DEBs | [Debian import](#import-existing-debian-packages): pinned package set, producer provenance, cache and consumer checks |
| Produce new DEBs | [Debian production](#produce-debian-packages): source-built payloads and Debian installation behavior |

Components own their source targets, generators, packages and tests. Buildimage
owns image composition and Make integration. Shared build/toolchain/packaging
mechanisms belong in `sonic-build-infra`; reusable dependency integration is
published through `sonic-bazel-registry`. Follow the existing
[source and dependency policy](source-builds-and-lockfiles.md),
[execution-tool guidance](build-tools-and-sysroot.md) and
[registry workflow](shared-dependency-workflow.md). Preserve contributor credit
when adopting existing work, but assess the final graph before retaining an
earlier workaround or helper.

For Docker-to-Bazel work, [split dependency build changes from the container PR](docker-image-template.md#split-dependency-work-from-image-integration): one PR per dependency component for its source-build and runtime/debug TAR support. Image integration consumes those targets and records actual prerequisite links. Follow the [TAR-to-OCI output policy](../SKILL.md#consume-runtime-and-debug-tars-directly-for-oci); introduce new DEBs only for a separately scoped consumer that requires that format, while preserving the legacy Make build.

## Source build

Compare the legacy source, headers, feature conditions, generators, programs and
bindings with the Bazel graph. Keep maintained targets near their source, with
separate generation, compilation, payload and packaging actions where those
boundaries permit useful caching. Reuse existing generators; declare schemas,
tools, runtime data and expected outputs, write to Bazel outputs and exclude stale
checkout copies when the action owns generation.

Use owner-exported dependency targets. Preserve public headers, native ABI,
SONAME, consumer-visible filenames, symlinks, loading behavior and language entry
points. When public language types cross repositories, preserve a coherent
dependency graph under the existing ownership policy. Keep libraries consumed
by target code separate from the tools and private runtime used to generate it.

Require evidence of the migrated component's source actions, complete supported
tests, installed runtime/ABI checks and a real downstream consumer. Establish a
clean build and representative source-change invalidation; normal cached outputs
of declared source actions remain valid. Importing the component's finished
binary does not satisfy source migration. Pinned external binary dependencies
remain allowed.

For one external package, retaining its upstream configure/Make recipe through
declared `rules_foreign_cc` actions is a valid source build. Follow
[external source packages](external-source-packages.md) to prepare maintained
sources and patches, declare tools and dependencies, and produce runtime/debug
TARs without DEBs. Bazel caches the foreign build at action granularity; this
does not establish independently cached per-source compilation. An opaque
wrapper around a whole legacy product build remains an intermediate integration,
not evidence that its individual component inputs and producers are modeled.

## Python distributions

Keep libraries, CLI targets, direct requirements and wheel definitions with the
source owner. Use standard `py_wheel` support and an explicit owner payload, so
transitive dependencies do not become accidental wheel contents. Include
generated modules. Components sharing one Python environment should consume a
coherent reviewed lock; unrelated environments need not share one lock. Follow
the [canonical lock policy](source-builds-and-lockfiles.md#keep-canonical-package-locks-in-git).

Compare the built wheel with the existing distribution definition (`setup.py`,
`pyproject.toml` or its equivalent): version and dependency metadata, extras,
modules/packages, scripts/entry points, licenses, templates/data, executable
modes and installed paths. Preserve unusual paths only when the consumer
contract requires them. Supply versions through the producer's supported
interface when Git-tag discovery is unreliable in shallow checkouts; keep source
pins, actual metadata and expected filenames consistent rather than renaming an
incorrectly versioned package.

Run the complete original source suite under the selected interpreter, with
declared fixtures and writable copies where necessary. Preserve assertions,
existing mocks and justified skips. Keep focused checks of real native bindings
and CLI behavior alongside the full suite. Use the same selected interpreter
for child processes; restore test environment changes even after failure.

Install the exact produced wheels into a temporary environment. Remove owner
source paths, assert that owner imports and distribution metadata resolve inside
the installation, compare installed payload bytes, and execute installed
commands. If this test borrows declared external dependencies from Bazel
runfiles, record that limit. Independently installable distribution acceptance
also requires installing the declared dependency closure without borrowed paths.
Verify any consuming image actually installs and uses the tested wheel; a
standalone wheel check does not establish image integration.

Retain wheel hashes, interpreter/architecture, dependency evidence, full-suite
test inventory/results and an installation receipt tied to the same bytes.

## Docker assembly

For the default OCI scope, first audit and satisfy the [project runtime source-build requirement](docker-image-template.md#require-bazel-built-project-runtime-dependencies),
including inherited base components. Use the [common Docker template](docker-image-template.md)
for source-built project payloads and permitted imported packages. Keep
entrypoints, ordered layers, package lists
and platform settings visible in the image's BUILD definitions. Share the
selection, publication and validation mechanisms; preserve the distinct source
and imported-package contracts.

Completion requires the actual runtime/debug OCI outputs and consumer archives,
installed filesystem/loading checks, and the service checks required by the
requested product. Record helper fixtures, source layers, complete images,
installer construction, guest boot and forwarding as separate evidence. Do not
promote success in an earlier stage into a claim about a later one.

## Import existing Debian packages

For imports into OCI images, follow the [required upstream-component policy](../SKILL.md#reuse-upstream-components-for-deb-to-oci-assembly) and [local-DEB adapter guidance](docker-image-template.md#use-upstream-tools-for-imported-deb-layers). Declare upstream extraction and assembly directly in the consuming BUILD file; a shared importer or custom assembly wrapper requires explicit scoped approval. Keep package metadata and validation separate.

Describe this as binary reuse. Lock a coherent set of immutable artifact URLs,
hashes, sizes, Debian package names/versions, distribution and architecture,
with the source/configuration compatibility conditions needed by consumers.
Fetch through standard repository rules and validate the complete set before
staging it under the existing filenames and dependency relationships.

Keep actual producer/release provenance separate from consumer-source
fingerprints. A fingerprint can reject an incompatible checkout; it does not
prove that checkout produced the binary. Record imported artifact identity in
the software bill of materials. Distinguish a reviewed provenance document from
one fetched and verified during the import; do not imply an enforcement step
that does not exist.

Revalidate retained inputs and reject missing/corrupt packages, unsupported
overrides or incompatible configuration. Define transitions back to native
production so an imported output cannot masquerade as a local build. Validate
all package identities before publication; state whether replacement is atomic
per file or across the complete set. Preserve timestamps for unchanged bytes
and retain the prior usable outputs when preparation fails.

Prove cold retrieval and warm repository-cache reuse in independent output
directories; disable downloads for the warm check and test missing/corrupt
entries and wrong pins. Inspect package metadata and ELF architecture, then
exercise actual installation/loading and downstream consumers against the exact
package hashes. A version match or a previous image test with different bytes
does not establish compatibility. An import with no build actions proves no
source compilation or action-cache reuse.

## Produce Debian packages

First satisfy [source-build acceptance](#source-build). Keep source compilation,
runtime/development/debug payloads and package assembly separately declared.
Reuse shared packaging rules and extend shared infrastructure for verified gaps.

Inventory required control fields, package relationships and dependency
generation, maintainer scripts, conffiles, triggers, alternatives, ownership,
modes, links, multiarch paths and runtime/development/debug splits. Inspect the
pinned rule's actual interface; support for a data tar and `Depends` alone does
not supply every Debian feature or automatic shared-library dependency analysis.
Check the installed package and applicable upgrade/removal/configuration
behavior, then real consumers with the declared runtime closure.

Preserve the existing [DEB execution-approval boundary](../SKILL.md#require-explicit-approval-to-build-deb-packages-with-bazel).
Inspect direct and transitive selected actions, including fixtures and wrappers,
before execution. Fetching or extracting existing DEBs is the separate import
path; it does not authorize producing new ones. Keep unaffected validation
moving and report required checks that remain pending.

## Common integration and validation

- **Preserve Make entry points.** Register supported configurations through the
  shared bridge and keep the legacy producer for unsupported profiles. A failure
  in a selected Bazel path must remain a failure. Reuse existing manifest and
  configuration generators with explicit caller inputs, including separate
  runtime/debug metadata; preserve expansion, overlays and failure diagnostics.
- **Test retained outputs.** Exercise the outer command users run with existing
  and missing outputs, repeated requests, source changes and both directions of
  producer switching. Dispatch dependency checks without forcing unchanged
  outputs to acquire new timestamps. Check failure propagation and prior-output
  preservation, including package-cache restoration.
- **Keep caches independent of server state.** Preserve the established builder
  interface (`SONIC_BAZEL_CACHE_SOURCE`, `/bazel_cache`, system `slave.bazelrc`).
  Share repository/download, disk/action and Bazelisk caches as applicable;
  keep output directories and Bazel server state private. Honor explicit cache
  opt-out and validate the host cache directory before starting a container.
  Prove the cache layer claimed using fresh checkouts/output bases, then a
  changed input that must miss. A same-output-directory no-op is insufficient.
- **Model the build environment.** Include behavior-changing hook/tool sources
  in builder cache identities using stable source content rather than generated
  package timestamps. Preserve tool runtime data, such as fonts or dictionaries,
  even when final-image cleanup removes it. Use fixture paths instead of host
  kernel/device state, maintain useful stderr/exit status, and avoid unnecessary
  host mounts or privileges while preserving filesystem semantics.
- **Verify useful debug output.** Apply the existing
  [runtime/debug policy](../SKILL.md#build-debug-artifacts-from-the-deployed-binary).
  Check build IDs/debug links where applicable and real debugger source, line
  and type lookup. For split DWARF, test the packaged runtime/DWP pair in
  isolation and require lookup to fail without the required symbols; loose
  build-tree files must not mask missing packages. Choose debug format and
  packaging tools from the actual compatibility matrix, retaining optimization.
- **Bind evidence to delivered bytes.** Select required targets explicitly;
  reject missing/empty/failing reports, inconsistent collected inventories,
  wrong interpreter/architecture receipts and artifact hashes different from
  tested inputs. Retain revision/configuration, logs/XML, package manifests,
  hashes, dependency resolution and debug coverage together. Apply
  [source PR CI requirements](source-pr-ci.md) and report unavailable services,
  justified skips and unsupported configurations without broad completion claims.

Use the [migration checklist](migration-checklist.md) for the final completion
record and the skill's existing publication/readiness rules for delivery. These
references do not change merge, custom-module or DEB-execution authorization.
