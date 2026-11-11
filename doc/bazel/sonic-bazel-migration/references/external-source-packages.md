# External source packages with native Bazel rules

Use this route to recover the SONiC source and packaging inputs, then compile ordinary packages
with [native language rules](implement-component.md). Apply the existing central-registry check.
An upstream configure/Make/CMake wrapper is only a separately approved specialized exception.

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

### Derive minimal configuration headers and native targets

Before running Autoconf probes or proposing a build-system exception, inspect `configure.ac`,
`Makefile.am`, `CMakeLists.txt`, and every `#if`/`#ifdef` guard in the pinned source tree. Many
third-party utilities and small libraries run Autotools or CMake upstream even though their Linux
build compiles only a few files and reads one or two header defines:

- **Single-binary Autotools package (`sflowtool`):** In
  [registry #301](https://github.com/securely1g/sonic-bazel-registry/pull/301) (`8ea421ba`),
  upstream `src/Makefile.am` compiles one translation unit (`src/sflowtool.c` plus four local
  headers) and `src/sflowtool.c` checks only `HAVE_BYTESWAP_H` and `VERSION` from `config.h`.
  Generating a minimal `config.h` with `@bazel_skylib//rules:write_file.bzl` and compiling directly
  with `cc_binary` + `drop_build_rpath` removes `rules_foreign_cc` and the `autoconf`, `m4`, and
  `make` execution toolchains while supporting both AMD64 and ARM64 Trixie.
- **Shared library and CLI CMake package (`libpsample`):** In
  [registry #302](https://github.com/securely1g/sonic-bazel-registry/pull/302) (`060c9db3`),
  upstream `CMakeLists.txt` compiles `src/mnlg.c` and `src/psample.c` into `libpsample.so.1.0`
  (`SONAME` `libpsample.so.1`) linked against `libmnl`, plus `psample_tool/psample.c` linked
  dynamically against `libpsample.so.1`. Expressing that directly with `cc_library`,
  `cc_shared_library`, `shared_library_cc_info`, and `cc_binary` preserves the exact exported
  dynamic symbol set, `DT_SONAME`, `DT_NEEDED`, and multiarch `/usr/lib/{x86_64,aarch64}-linux-gnu`
  layout without CMake or `rules_foreign_cc`.

### Migrate legacy `rules_foreign_cc` registry modules

When a component or container migration encounters an existing `sonic-bazel-registry` module that
still wraps `configure_make` or `cmake` without an approved specialized exception (for example,
`sflowtool@6.11.0.sonic.2` from [registry #191](https://github.com/securely1g/sonic-bazel-registry/pull/191)
or `libpsample@1.1.0.sonic.1` from [registry #189](https://github.com/securely1g/sonic-bazel-registry/pull/189)):

1. Publish a new `.sonic.<N+1>` registry version converting the overlay to native rules; leave all
   published version directories and their `metadata.json` entries untouched.
2. Remove `rules_foreign_cc` and obsolete foreign execution toolchains (`autoconf_toolchain`,
   `m4_toolchain`, `make_toolchain`) from `MODULE.bazel`, then regenerate `overlay/MODULE.bazel`
   with `python3 ci/registry_ci.py sync-module`.
3. Preserve public target labels (`:runtime`, `:runtime.debug_symbols`, `:runtime_packages.json`,
   and public `cc_library` SDK targets) so downstream images and C/C++ consumers upgrade without
   structural rewrites.
4. Compare `nm -D --defined-only` exported symbols, `DT_SONAME`, and `DT_NEEDED` against the
   Make-built `.deb` baseline, and enable both `amd64` and `arm64` in `presubmit.json` when the
   native rules remove architecture-specific foreign wrapper constraints.

For an explicitly approved specialized exception, verify the selected adapter's API and toolchain
selection, declared inputs, DESTDIR, installed outputs, logs and actual compiler/linker flags. Use
declared tools and target libraries; do not install on the host or download during compilation.
A foreign action caches the package build as a unit and does not prove per-source compilation reuse.
Keep native install and downstream image targets separate where their contracts permit.

## Package runtime files and matching symbols

Feed the compiled binaries, libraries and required data into the existing
`sonic_deploy_tar` rules. Retain debug symbols on the compiled native targets
(`-g`, `-Wl,--build-id`, `features = ["-strip_debug_symbols"]`) so `sonic_deploy_tar`
derives stripped runtime copies and detached `.build-id` symbols from the same
linked ELF while keeping optimization and hardening flags intact. Follow the existing
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
  Retain paired artifacts and hashes, source provenance, generated configuration
  headers and resolved dependency evidence.
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
