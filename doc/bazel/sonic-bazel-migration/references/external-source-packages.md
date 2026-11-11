# External source packages with upstream configure/Make

Use this route to recover the SONiC source and packaging inputs, then compile ordinary packages
with [native language rules](implement-component.md). Apply the existing central-registry check.
An upstream configure/Make wrapper is only a separately approved specialized exception.

```text
Fixed source + packaging archives + ordered patches
    -> declared source preparation -> native generation/compile/link actions
    -> runtime TAR + matching debug TAR + metadata -> consuming image
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

## Keep Make and registry sources in lockstep

While Make still builds a package from `src/<package>/`, its recipe and the
registry entry describe the same source in two places. Keep them identical:
the tag or commit that Make checks out must resolve to the commit in
`source.json`, and the Make patch series must match the registry patches byte
for byte and in the same order. Add an automated check, in the consuming
repository or in registry CI, that runs when either recipe changes, and explain
any intentional difference in the PR.

For example, `src/sflow/hsflowd/Makefile` checks out tag `v2.1.26-1` and applies
`patch/series`, while `hsflowd@2.1.26.sonic.1` fetches commit `41f10e6a…` with
its own copies of the same two patches. They match today, but unless a check
compares them, a moved tag or an edit to one copy makes Make and Bazel build
different code without any failure.

## Express the build through native Bazel actions

Use the [14-group analysis](analyze-make-component.md) to derive complete source/header selections,
parameters, feature conditions, generated files, interfaces and install destinations. Follow
[source preparation](source-and-patches.md) through each original unpack/patch/overlay stage.
Use the [native C/C++ route](native-cc.md) or the appropriate language procedure.

- Derive each required static/shared library and program from Make analysis. Select the C/C++
  toolchain through the target platform; component targets do not name a compiler toolchain.
- Run configure capability probes only during migration with declared target-toolchain and library
  inputs, then express the results through native templates and configuration branches. Do not run
  configure/Make/CMake as the ordinary compile action.
- Declare every generator, schema, import/plugin/template and output before wiring native consumers.
  Tools use execution configuration; output headers/libraries use target configuration.
- Declare installation files and metadata directly, preserve modes/links/notices, and export runtime
  and matching symbol TARs. Keep optional approved DEBs separate from the compilation graph.

For an explicitly approved specialized exception, verify the selected adapter's API and toolchain
selection, declared inputs, DESTDIR, installed outputs, logs and actual compiler/linker flags. Use
declared tools and target libraries; do not install on the host or download during compilation.
A foreign action caches the package build as a unit and does not prove per-source compilation reuse.
Keep native install and downstream image targets separate where their contracts permit.

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
  source-build recipe.
- Verify the consumer's actual selected module, source revision and recipe
  integrity. Updating a producer PR does not update pinned consumers. Reassess
  obsolete packaging follow-ups against the current consumer graph; close them
  only within existing authorization.
