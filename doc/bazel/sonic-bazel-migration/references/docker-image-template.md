# Common Docker image template

Use this structure when adding or aligning Bazel image assembly in
`sonic-buildimage`. Reuse existing `oci_base_layout`, shared `apt_layer`,
`sonic_layer`, `oci_image`, manifest-label and `sonic_docker_archive` interfaces;
verify their behavior and availability at the pinned revisions. Keep owner
settings and layer order readable instead of adding an all-purpose macro that
hides them. This template specifies the shared contract, not one fixed package
list or architecture.

## Require Bazel-built project runtime dependencies

For a Docker/OCI build request, the migration unit includes all project runtime
components in the final image, not only its image-assembly target. Apply the
[OCI runtime source-build requirement](../SKILL.md#build-oci-images-with-bazel-built-project-runtime-dependencies).
Pinned Debian APT packages may remain binary inputs.

Before choosing layers:

- Inventory project executables, libraries, Python packages/native bindings and
  runtime data, including transitive dependencies and inherited base contents.
  Record each source owner, revision, required features, actual producer and
  public Bazel runtime/debug target or missing support.
- Inspect existing owner and registry targets before declaring a gap. Check that
  they cover the requested architecture and features. A VS package that excludes
  the DASH daemon is not a replacement for the DASH-enabled package.
- Consume compatible Bazel source targets and add missing support with the
  owning component. Keep dependency metadata and install declarations with their
  owners; image policy should describe image-specific choices.
- Trace installed project files to declared Bazel generation/compilation and
  packaging actions. A Bazel action extracting a Make-built DEB, or invoking the
  entire legacy Make build, does not satisfy source migration. Cached outputs of
  genuine Bazel source actions do.
- Audit retained base files too. A Make-built base is not an implicit exemption
  for its project runtime components. Reusing the SWSS layout does not prove
  source coverage, because an example may itself retain transitional inputs.
- Keep allowed pinned Debian inputs distinct from project-built or SONiC-patched
  artifacts. Preserve the required ABI/features; do not substitute an ordinary
  Debian package merely to remove a Make prerequisite.

An explicit assembly-only or package-import request can use a narrower boundary.
Record that scope and every remaining producer. Without such a scope, unresolved
Make-built project runtime dependencies mean the OCI migration is incomplete,
even when its image and installer tests pass. Existing import helpers remain
usable for permitted inputs; their existence does not change this criterion.

## Split dependency work from image integration

Keep dependency build migrations out of the container PR. Group dependency
DEBs by their producing component: one PR can cover that component's runtime,
development and debug packages, while different components use separate PRs.
For example, `libnl-3-200`, `libnl-route-3-200` and their related development/debug
DEBs share one libnl3 PR; libyang3 has another. Keep each producer's source
support, packaging, tests and documentation in its own PR.

The container PR consumes the resulting public targets and versions, assembles
the image and validates the Make/installer handoff. Reuse already available
targets directly. Link required producer/registry PRs and keep readiness tied to
the actual selected dependencies. Pending producer work remains a source-build
gap; dividing it into PRs does not make the overall OCI migration complete.

## BUILD file sections

| Section | Owner declaration and shared interface |
| --- | --- |
| Supported configuration | Target constraints and the Make selector/input validator enforcing OS, architecture and features for normal and direct Bazel entry points |
| Base and metadata | Complete checked OCI base, expected platform and separate runtime/debug labels from Make's existing manifest generator |
| Runtime inputs | Locked APT selection, component payload adapter, Python payload when required, configuration and required installation state |
| Runtime image and archive | Visible `oci_image` with entrypoint, environment, labels and explicit ordered layers; `sonic_docker_archive` for the existing consumer format |
| Debug inputs | Locked tool selection and symbols checked against the deployed runtime |
| Debug image and archive | `oci_image(base = runtime)` plus tools/symbols and debug metadata; matching archive export |
| Validation references | Named owner contract tests and complete-image checks; long tool/test definitions may live in owner subpackages |

```text
checked base + selected APT + component payload + configuration/state
    -> runtime OCI -> runtime Docker-save archive
    -> debug OCI (base = that runtime, plus tools and matching symbols)
       -> debug Docker-save archive
```

Keep common helper tests with the shared mechanism, component behavior tests
with their source, and image inventories/acceptance checks with the image owner.
Different file placement or entrypoints do not require different assembly rules.

## Select APT payloads through the shared rule

Route runtime and debug APT payloads through the shared locked `apt_layer`
selection before image-specific `sonic_layer` filtering. Each image owns its
requested package list and retained-base policy. Select against the actual base
and retained package state; reject incompatible identities and unintended
overwrites of inherited libraries, including patched or FIPS variants. Retain
the selected/retained package identities, hashes and collision decisions in the
selection receipt. Check that retained package versions and ABI satisfy their
consumers; keeping a package by name alone does not establish compatibility.
Do not duplicate selection logic in the image.

Inspect the pinned API and available registry entry before use; publish and
consume necessary common support through the normal shared-dependency workflow.
If the pinned implementation lacks required behavior, record and fix that gap
in the shared mechanism rather than silently bypassing the selection checks.
Debug selection must account for the runtime's final package set, since it
extends that image. Preserve legacy include/exclude behavior and required
licenses when filtering the selected payload.

## Use upstream tools for imported DEB layers

Apply the [required upstream-component policy](../SKILL.md#reuse-upstream-components-for-deb-to-oci-assembly) before adding or retaining an imported-package adapter:

```text
Debian repository -> rules_distroless payload/control targets --+
                                                              +-> rules_oci image
Local existing DEB -> declared BSD tar extraction -> data TAR --+
```

Keep APT inputs on the shared selection path below. For local DEBs, inspect the
pinned public APIs: a URL-based repository importer cannot be assumed to accept
local build-action labels. Declare a small action directly in the consuming
BUILD file, using the pinned `tar.bzl` BSD tar toolchain to expose the data and
control archives as declared outputs. Keep the ordered TAR inputs and
`oci_image` visible there. Do not add a shared importer or move this assembly
behind a custom local wrapper; that requires explicit approval under the policy.
Use public rules/toolchains, not private Distroless internals or ambient host
`ar`, `tar` or `dpkg` commands. Reuse upstream decompression. When combining
payloads, use Distroless `flatten` if its pinned output format preserves the
required metadata, or the approved BSD tar toolchain's PAX composition when GNU
TAR would discard extended attributes. Pass ordered payload TARs to
`oci_image(tars = ...)` in an OCI-supported compression format.

Keep SONiC metadata and policy checks as separate concerns. Preserve and verify
package control facts, hashes, architecture, owners, modes, links, required
extended metadata and package/layer order. Check runtime/debug identity,
installed behavior and reproducibility with actual input packages. Do not
silently drop metadata to fit an upstream API; report the verified gap and
obtain explicit approval before implementing a deviation. The same approval
boundary covers an existing custom parser or assembler proposed for reuse.
This policy does not itself authorize changing or closing existing PRs.

## Keep two intentional component input adapters

Use source-owned outputs for project runtime components under the default OCI
migration scope. The imported adapter applies to permitted external packages or
an explicitly narrower assembly/import task; it does not satisfy the project
source-build requirement.

| Source-owned outputs | Imported package outputs |
| --- | --- |
| Consume public runtime tar targets from the repositories that compile the component. | Accept an explicitly prepared Make/release handoff with exact package identities, architecture, content hashes and ordered payloads. |
| Preserve source provenance, owner install declarations and debug providers through intermediate layer rules. | Validate the full handoff before assembly; declare every consumed payload and metadata file. The Bazel action must not refresh undeclared inputs by secretly invoking Make. |
| Collect matching symbols from the source targets, for example through `DebugSymbolsInfo`. | Validate separately supplied debug packages against the exact runtime bytes; imported packages need not invent source-provider metadata. |

Keep native package ownership and modes where the imported contract requires
them. Do not force source-built outputs through DEBs or erase imported ownership
merely to make BUILD files identical. Distinguish an image-assembly migration
from source migration of its still-external producers.

## Preserve base, metadata and installation behavior

- Validate the base's expected platform, index/manifest descriptors, blob
  hashes/sizes and complete file inputs. Make preparation should publish a
  checked generation before Bazel consumes it; changed bytes must invalidate
  the consumer even when the source timestamp is misleading. Preserve unchanged
  timestamps and the prior usable generation when preparation fails.
- Reuse Make's manifest expansion, service discovery and optional overlays.
  Pass the requested container explicitly rather than relying on ambient Make
  pattern variables. Declare distinct runtime/debug metadata inputs, including
  the runtime prerequisite when only a debug output is requested.
- Reuse the source-owned configuration renderer as an execution tool with
  declared templates/includes and safely encoded arguments. Preserve build-time
  versus container-startup discovery. Declared files alone do not isolate a
  renderer that searches ambient template directories; validate its lookup in
  the documented execution environment.
- Account for installation behavior as well as extracted package files.
  Required alternatives, symlinks, package database, caches and generated state
  need explicit inputs/actions and checks. Do not equate DEB extraction with
  running maintainer scripts or complete package installation.
- Keep startup/supervisor files, entrypoint, environment, labels, modes,
  ownership and links aligned with the supported legacy image. Make overlapping
  paths and layer order intentional and reviewable.

## Register the producer and preserve the consumer

Use the shared Make build/query/export bridge. Owners declare archive targets,
complete OCI targets when consumed by final assembly, prerequisites, input
paths, attribution and supported selectors. Keep runtime/debug archive names
and tags compatible with Make and the installer. Unsupported profiles retain
their existing producer; failures in a selected Bazel path remain visible.

Register switchable outputs in both modes so retained files cannot bypass
producer-transition checks. Validate changes through the outer Make command,
including no-op requests, existing outputs, switches in both directions,
parallel runtime/debug goals and package-cache restoration. Publish completed
archives atomically at the supported boundary and preserve old outputs on
failed preparation, queries or copies. Follow the
[common cache and evidence requirements](migration-workflow.md#common-integration-and-validation).

## Completion checks

Require the following for each claimed configuration, recording pending items
for a narrower task:

1. **Runtime source coverage:** every project runtime component, including
   transitive and inherited base contents, maps to compatible Bazel source
   actions and the installed outputs. List allowed pinned Debian packages and
   any user-defined scope exceptions separately.
2. **Selection and payload:** checked base and APT receipts; source/import
   provenance; intended package identities, dependency closure and collision
   decisions; legacy paths, bytes, modes, owners and links, including inherited
   files and required installation state.
3. **Actual images and archives:** build and inspect both runtime/debug OCI
   outputs and the exported archives. Verify platform, labels, tags, ordered
   layers and exact runtime ancestry; compare archive and OCI payloads.
4. **Installed behavior:** exercise actual loader/import paths and expected
   commands in the resulting filesystem with declared dependencies. Add the
   required service checks. Fixture/structural success does not establish these
   results; installer construction, boot and forwarding are separate stages.
5. **Debug correspondence:** verify matching runtime/symbol artifacts with
   applicable build IDs, debug links and debugger lookup. Record inherited or
   imported binaries without matching symbols as explicit coverage gaps.
6. **Integration and evidence:** exercise Make selection/transitions and source
   invalidation; retain source/configuration, package and image hashes, receipts,
   test results and resolved dependencies together. Revalidate consumers when
   package hashes change even if names and versions do not.

The structure generalizes the distinct source-payload and imported-package
adapters in [orchagent](https://github.com/securely1g/sonic-buildimage/blob/7bbc035673798b44fd372e5b28bad086c0919d65/dockers/docker-orchagent/BUILD.bazel)
and [syncd-vs](https://github.com/securely1g/sonic-buildimage/blob/7bbc035673798b44fd372e5b28bad086c0919d65/dockers/docker-syncd-vs/BUILD.bazel).
Those revisions are design evidence, not current dependency pins or a claim
that either example implements every completion check above.
