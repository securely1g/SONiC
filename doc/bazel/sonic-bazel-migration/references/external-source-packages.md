# External source packages with upstream configure/Make

Use this path when Bazel should build an external package from source while
retaining its upstream build system. A native per-file Bazel rewrite is separate
work; it is not required for this path. First apply the existing
[central-registry and upstream-support check](../SKILL.md#check-bazel-central-registry-before-custom-modules)
and reuse compatible integration.

The output contract is:

```text
Verified source + maintained patches
    -> declared configure/Make build -> staged installed files
    -> runtime TAR + matching debug TAR -> consuming image
```

## Prepare the maintained source

- Start with the actual SONiC Make baseline: source version, distribution
  revision, feature flags, patches and installed layout. Do not silently replace
  it with a newer upstream release or another fork's baseline.
- When Make uses Debian source, fetch the matching upstream archive and Debian
  source archive, with immutable URLs and verified checksums. Use the `.dsc` to
  cross-check archive identity. Reuse `debian/patches/series` in its recorded
  order, honoring its patch options, then apply the SONiC-specific patches.
  Reject unsupported patch semantics rather than silently skipping them.
- Read `debian/control` and `debian/rules` for the required dependencies and build
  behavior. Take copyright, license, changelog and applicable installation
  metadata from the fetched sources. Do not keep registry copies of Debian's
  patches or copyright, or invent Debian manifests absent from the source.
- For packages without Debian source packaging, use their maintained upstream
  source and license files instead. Keep only required SONiC integration changes
  in the overlay. Declare every archive, patch and preparation script that can
  change the prepared source.

Where source reconstruction changes, compare the prepared tree with the
distribution's normal extraction and patch application. Record revisions and
hashes; archive checksum verification alone is not signature verification.

## Run the upstream build through Bazel

Use the selected `rules_foreign_cc` version's `configure_make` or `make` rule as
appropriate. Inspect its supported API and the upstream recipe; avoid a custom
shell build framework when the standard rule suffices.

- Declare the complete source inputs, including Makefiles, configure templates,
  generated-input schemas and helper scripts. Declare installed outputs and keep
  useful configuration logs.
- Select the SONiC compiler toolchain explicitly. Preserve required configure
  options, hardening, optimization, ABI and feature settings. Inspect actual
  compiler/link commands: upstream recipes can override supplied tools or flags,
  and a successful build can silently omit an optional feature.
- Use declared execution tools for Make, autoconf/m4, pkg-config and generators
  as needed, together with their private runtime libraries/data. Reuse compatible
  toolchains or shared `build_tools`; custom tool edges use `cfg = "exec"`.
  Headers and linked libraries remain target dependencies. Although pkg-config
  executes on the build platform, it must read the selected target metadata.
  Follow [build tools and sysroots](build-tools-and-sysroot.md).
- Stage installation inside the action, normally with the required installed
  prefix and `DESTDIR`. Avoid host installation, undeclared host headers/tools,
  package-manager calls and downloads during compilation.
- For this TAR-producing path, select compile/install targets without adding
  `dpkg-buildpackage`, `sonic_deb` or another DEB producer. Inspect the transitive
  action graph and invoked scripts to verify that output contract. Adding a
  separately needed package definition follows the
  [DEB package-definition approval rule](../SKILL.md#require-approval-before-adding-new-deb-package-definitions);
  ordinary validation of existing approved package targets needs no new approval.

Bazel caches the declared foreign build action. A source change can rerun the
package's configure/Make build; do not claim per-source Bazel cache reuse.
Keep runtime/debug packaging and consuming image assembly as separately declared
targets so unchanged outputs can be reused at those boundaries.

## Package runtime files and matching symbols

Feed the staged binaries, libraries and required data into the existing
`sonic_deploy_tar` rules. Use the selected rule's debug-preserving configuration
and verify that flags such as `-g` actually reach the foreign compiler. Derive
runtime copies and detached symbols from the same linked ELF, retaining the
required optimization policy. Follow the existing
[runtime/debug contract](../SKILL.md#build-debug-artifacts-from-the-deployed-binary).

Preserve installed paths, ownership, modes, symlinks, configuration, helper
scripts, manuals and notices required by the consumer. Read notices directly
from the prepared source, such as `debian/copyright`. Publish stable runtime and
debug TAR labels and make the image consume the matching pair.

Debian source metadata does not require generating a `.deb`. A runtime TAR is a
filesystem payload; it does not provide Debian package installation, maintainer
scripts or dpkg records. Do not fabricate those records or add a separate
DEB-packaging module merely because control files are available. An independently
requested DEB deliverable follows the separate Debian workflow: obtain approval
before adding a new package definition, then validate the approved target normally.

## Validate and integrate the actual outputs

- Run relevant upstream tests and focused regressions for maintained patches or
  migration failures. Check required features and programs, not only a link or
  version command.
- Test extracted runtime files with their declared runtime dependencies: loader
  behavior, architecture, installed layout and a representative consumer.
  Check packaged notices against their source files.
- Verify runtime/debug build IDs, debug-link checksums and GDB source/line lookup.
  Retain paired artifacts and hashes, source provenance, configuration logs and
  resolved dependency evidence.
- Validate the required execution/target matrix. Native AMD64 and ARM64 runs are
  useful when those are the supported configurations; they do not prove
  cross-compilation. Report source-package and consuming-image results separately.
- Keep third-party integration in its registry module and generic mechanisms in
  build-infra under the existing [ownership policy](../SKILL.md#publish-reusable-dependency-support-through-the-registry).
  Consumers select the producer's public targets instead of duplicating its
  configure/Make recipe.
- Verify the consumer's actual selected module, source revision and recipe
  integrity. Updating a producer PR does not update pinned consumers. Reassess
  obsolete packaging follow-ups against the current consumer graph; close them
  only within existing authorization.
