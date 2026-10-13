# swss-common migration lessons (2026-09-27)

This case study records results verified on 2026-09-27 while carrying [upstream PR #1215](https://github.com/sonic-net/sonic-swss-common/pull/1215) into the fork. The migration, CodeQL, and README follow-ups were [PR #1](https://github.com/securely1g/sonic-swss-common/pull/1), [PR #2](https://github.com/securely1g/sonic-swss-common/pull/2), and [PR #3](https://github.com/securely1g/sonic-swss-common/pull/3). These links preserve the historical evidence. Future work must refresh the current branch, upstream changes, toolchains, CI results, and artifact availability. The versions, flags, and supported subset below are specific to this swss-common snapshot.

For the later YANG dependency and runtime-path cleanup, see the
[shared-dependency workflow and 2026-09-28 example](shared-dependency-workflow.md).
That follow-up does not change the historical coverage recorded below.

## Check source coverage against observed compilation

- A one-time local audit compared the configuration-aware source inventory with Bazel's execution log. It confirmed compilation of all 122 tracked no-YANG C/C++ sources and the generated Python SWIG wrapper.
- A manual `//tests:codeql_test_sources` target retained 48 legacy C++ test translation units for analysis without executing their Redis-dependent tests. This preserved analysis inputs while keeping service-dependent execution separate.
- Recalculate the inventory for each revision and configuration. Include conditional sources, generated bindings, tests, and tools; then check the compiler actions. The counts above were validation evidence, not a recurring CI coverage check. [CodeQL commit and validation](https://github.com/securely1g/sonic-swss-common/commit/9d8efbd2919d3e2a5cf3d7428408989e627c10ee)

## Validate the runtime and package contract

The original target set built successfully, but the ELF declared the runtime name (SONAME) `libswsscommon.so.0` while the archive only installed `libswsscommon.so`. A consumer could link and later fail to load the library. The new package test reproduced the missing `.so.0` entry before the fix.

The fix preserved the public Bazel target label, emitted `libswsscommon.so.0`, and packaged `libswsscommon.so.0.0.0` with relative `.so.0` and `.so` symlinks. Two regression tests cover distinct boundaries:

- A dynamically linked C API roundtrip exercises Bazel's normal runtime search without Redis or a custom `LD_LIBRARY_PATH`.
- A package test reads the built ELF's SONAME, finds that path in the archive, resolves the link inside the extracted package, and verifies the resolved ELF's SONAME.

Both tests passed on native AMD64 and ARM64; the runtime test also passed in a clean Trixie container. For another library, derive expected names from its ABI and packaging contract. [Filename fix](https://github.com/securely1g/sonic-swss-common/commit/968f39f9ca2f50c89a9dcaa048e8698f5de5d0f8) · [Regression tests](https://github.com/securely1g/sonic-swss-common/commit/fb39ce96f4a97d652f86be894e93a559fdb0350c)

## State CI coverage and inspect delivered archives

The verified standalone CI used Bazel 8.5.1 and native AMD64/ARM64 runners with a dated Debian Trixie container. The resolved GCC 14.2 toolchains required matching execution and target CPUs. CI explicitly selected the required libraries, binaries, bindings, packages, and seven test targets, avoiding silent omissions from incompatible wildcard targets. Both jobs passed formatting, builds, and tests.

Each job uploaded `libswsscommon_pkg.tar`, `sonic-db-cli_pkg.tar`, and `swsscommon_pkg.tar.gz` in an architecture-specific Actions artifact. Both uploads were downloaded and their archive contents and checksums inspected. Artifact collection required all three outputs. [CI and documentation commit](https://github.com/securely1g/sonic-swss-common/commit/22449651209a67a2e390381b00f2a377ca905ff4)

Historical coverage was **native AMD64/ARM64 with YANG disabled**. YANG generation remained unwired; the supported path used a schema stub and omitted YANG-dependent sources. ARMHF was unvalidated, and the Redis-backed Go integration test remained manual. These package checks did not establish full SONiC image or container behavior. Actions archives have retention limits, so locate and inspect a current successful run before consuming them.

## Make compiler execution visible to CodeQL

The C++ CodeQL job initialized tracing before creating a fresh Bazel output base, then forced local compilation with action, disk, and remote output reuse disabled. Download caches remained usable. The AMD64/Trixie job built six explicit targets; the Python CodeQL job kept its existing behavior. Hosted C++ and Python checks passed. [CodeQL workflow and evidence](https://github.com/securely1g/sonic-swss-common/pull/2)

The generated-wrapper audit found a separate reporting gap: local CodeQL extraction parsed the SWIG wrapper and a representative query produced findings, but normal SARIF interpretation omitted them because Bazel generated the file outside the repository source root. The hosted database was not retained, so hosted wrapper coverage could not be fully confirmed. Future validation should inspect extraction, query results, and source-path mapping in addition to the job result. No wrapper-reporting fix was implemented in this snapshot.

## Keep debug-symbol claims precise

One local AMD64 build used `--copt=-g --strip=never` with the existing build mode. For this toolchain, `-c dbg` alone did not emit debug information. The raw and packaged libraries were byte-identical, contained embedded DWARF, passed the package test, and resolved a source line with `addr2line`. The README follow-up documents the command. This verified an AMD64 package with embedded symbols; the ARM64 debug build and CI upload of debug artifacts were not validated. [README change and validation](https://github.com/securely1g/sonic-swss-common/pull/3)

Detached symbols and container integration remained planned. The package still used `tar`/`flatten`; it did not use `sonic_deploy_tar`, propagate `DebugSymbolsInfo`, collect `debug_symbols_layer`, or produce a debug OCI image. No detached `.debug` artifact, Debian debug package, or runtime/debug-image matching test was implemented. The proposed integration would split symbols from the same runtime ELF and collect them into a matching debug layer; recheck the resolved build-infra rules before adopting that design. The expanded proposal was recorded in the [fork HLD](https://github.com/securely1g/SONiC/blob/5fa3bccc482a778970759bc8372e8b2f8afd934d/doc/bazel/bazel_migration_hld.md#7b5-debuggability).
