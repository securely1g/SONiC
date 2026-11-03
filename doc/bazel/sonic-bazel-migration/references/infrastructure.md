# Investigate and use project infrastructure

Read the entire [shared contract](common-contract.md), then applicable sections here before implementation. Locate selected sources, public interfaces and real consumers before BUILD/helpers. Recheck required APIs after infrastructure changes.

## Build entry and cache preflight

Before first Bazel use, check actual binary against .bazelversion/MODULE compatibility and inspect system/user/workspace/imported rc. Record registry/downloader/cache/exec-target platforms/output directories. Locate conflicting settings before isolating them with documented temporary configuration; preserve originals.

Reuse pinned tool images and verified source/DEB download caches under acceptance policy. Check lock/index provenance and refresh changed resolution inputs under [locking](dependency-locking.md). Fresh-consumer/output checks still use fresh directories. Distinguish download reuse from build/test cache hits. After interruption, confirm task processes stopped and output locks released; identify remaining processes by task identity.

## Confirm selected versions and interfaces

Resolve infrastructure identity through actual MODULE/registry/overrides, not example versions. Tables locate interfaces; inspect selected implementations. Read root/component MODULE, rc, overrides, registry entries and needed source. Verify actual copies with mod graph/query/cquery or checked downloads; cached same-name symlinks may point elsewhere. Record version, source, symbols/attributes, public labels, providers, limits and consumer examples in implementation.json.

## Rule necessity and ownership

Apply before .bzl/macros/rules/repository rules/providers/Python/shell helpers across acquisition, configuration, generation, installation, packaging, documentation and tests. Inventory existing extensions. Before coding, record proposed inputs/outputs, necessary transformations, real consumers, exact existing API gaps, selection and owner. Data files and helper scripts have the same requirement.

Split composite scripts into existing tool actions, BUILD parameters and remaining transformations. Reuse compression/templates/archives/mappings separately rather than wrapping them in a unified multimode script. Pass upstream-supported inputs/options directly. Fix owning tools/shared interfaces before private launchers, runtime module mutation or guessed paths.

| Responsibility | Owner/implementation |
| --- | --- |
| Versions/services/fragment order/features | Component BUILD attributes/arguments/environment |
| Existing tools/compression/templates/archives/mappings | Direct BUILD calls |
| Missing generic transformations/adapters | Minimal shared implementation with explicit component inputs |
| Missing component-specific transformation | Minimal component helper |
| Dependency compilation/link/header interfaces | Original package/source producer |

Documentation declares versions/builders/inputs/outputs in BUILD and calls Sphinx/makeinfo/compressors directly. Only necessary generic Bazel adaptation belongs in shared infrastructure. Likewise components declare service names/maintainer-fragment order; shared tools expand fragments only. Complete splitting, implementation and consumer integration together. Calls between private helpers do not establish necessity. Reconcile actual extensions against prior decisions in this change, without a deferred cleanup phase.

Check actual missing semantics after native attributes/deps/providers; forwarding/unifying paths is insufficient justification. Inspect existing project/infra/rules and consumers for real providers/platform limits, then applicable BCR rules. Compilation-context filtering, include roots and link/runtime exports belong to shared mechanisms and original producers; only unexpressible component-specific semantics remain local. Header-only exports propagate complete compilation context while omitting linking by contract; consumers directly reuse them instead of scanning roots or copying repairs.

## Freeze shared versions for this task

Pin source commits, module versions, registry recipes, toolchains and effective configuration in implementation records. Validate/publish shared fixes under the main PR/dependency policy; recheck affected consumers after identity changes.

Document temporary overrides during investigation. Once interfaces pass capability tests, freeze commits, uncommitted/untracked diff/manifests/digests, versions, registry entries, patch/overlay checksums, rc and overrides. Verify actual resolution before final downstream matrices. Local registry checks need recorded identity. The assigned writer merges shared files and coordinates consumers. Preserve old records when changing frozen inputs; list affected interfaces/components/configurations/checks and revalidate those. Reuse evidence only where inputs remain identifiable and unaffected. Keep override and actual registry-consumption evidence separate; compare sources after final identity changes.

## Interface locations

Paths below are relative to @sonic_build_infra; actual source attributes are authoritative.

| Capability | Entry | Contract |
| --- | --- | --- |
| C/C++ toolchain | //toolchains/gcc:extensions.bzl gcc -> @gcc_toolchains | Root import/registration; separate exec/target CPU/sysroot |
| Platforms | //platforms:x86_64_trixie, :aarch64_trixie | CPU/Linux/Trixie sysroot; separate target/exec settings |
| Shared linking | //cc:shared_library.bzl shared_library_cc_info | CcSharedLibraryInfo to link CcInfo; outer cc_library owns headers |
| Runtime/symbol TAR | //tar:sonic_deploy_tar.bzl | binaries maps mtree/ELF, srcs/mtree resources; .debug_symbols |
| Requested DEB | //deb:sonic_deb.bzl | data TAR; [explicit packaging](build-deb-with-sonic-deb.md) |
| Python native bindings | //python:py_native_library.bzl | native_so, optional native_py, cc_deps; wrapper/runtime propagation |
| Wheel installation | //python:wheel_layer.bzl | Full wheel closure; explicit site-packages/scripts/headers/interpreter |
| Python source installation | //python:site_packages.bzl site_packages/export_py_info | Target interpreter/paths; direct source installation interface |
| SWIG | //swig:defs.bzl swig_gen/swig_gen_go | Matching parser/wrapper defines; headers/template closure |
| protobuf | //proto:protoc, proto/README.md | Existing pinned APT tool; [version/consumer contract](code-generation.md) |
| Migration Autoconf | //tools/autoconf:probe.bzl autoconf_probe | Toolchain/CcInfo/sources/pkg-config -> [probe directory](autoconf-probe.md) |
| Exec tools | //tools/build_tools:{aspell,doxygen,make,m4,pkgconf,perl,bison,flex,autoconf,autoheader,autom4te} | Pinned APT source, exec architecture, version/runtime |
| configure/Make adapter | //tools/build_tools:{make,m4,pkgconfig,autoconf}_toolchain | Ordinary components forbidden; approved exceptions verify origins |
| APT | Common sources/lock, multiple collections, Distroless extension | [data/control, library, exec](use-apt-libraries.md); //apt:apt_layer.bzl |
| Runtime metadata | //oci:runtime_packages.bzl runtime_packages/runtime_packages_group | Authoritative control/changelog/real TAR; check selected required_paths support |
| Installed state | //oci:installed_packages.bzl | Base/APT receipt/source TAR/metadata/MODULE -> validated status/receipt; image explicitly installs status |
| Accounts | Distroless defs.bzl accounts or //oci:accounts.bzl account_layer | Preserve/validate/append passwd/group; separate homes/shadow/services |
| Symbols | //oci:debug_symbols_layer.bzl | Runtime symbol provider and actual pairing scope |

Locate selected versions and verify attributes/input/output contracts before integration.

## Practical consumption

### C/C++ and headers

Follow [C/C++](native-cc.md). Use @rules_cc native library/binary/shared rules. Arrange static deps/dynamic_deps by the link contract. shared_library_cc_info preserves links/runfiles; an outer cc_library adds public compilation context. Native shared consumers reference original producers in dynamic_deps. Verify SONAME/version/development links/install paths rather than assuming reference-macro _shared/_hdrs labels.

### Execution tools and native builds

Follow applicable [tool recipes](tool-recipes.md) for public labels/MODULE visibility/binutils toolchains. [Autoconf](autoconf-probe.md) uses real target toolchains/dependencies; [hermetic tools](hermetic-tools.md) supplies FilesToRunProvider/actions/environment. Verify [generators](code-generation.md) through language consumers rather than binary existence. Apply [shared tool requirements](common-contract.md#native-builds-and-tools) to actual actions.

### Root project, independent components and registry

Use maintained remote SONiC registry then BCR. Preserve published historical versions under [registration](register-bazel-module.md), not reference projects' single-version deletion policy. [Ownership](register-bazel-module.md#1-determine-source-and-build-ownership): buildimage-owned components stay in their owning directories; independent SONiC sources stay upstream; third-party adaptation reuses modules or lives in registry; private sources must satisfy internal-component boundaries. Record temporary override origins and separately test actual registered consumption. Root overrides/registration do not prove independent entries.

buildimage tools/bazel/common.bazelrc explicitly chooses Trixie and defaults to x86_64 execution. It defines no aarch64 config alias; infra's own alias is not inherited. After checking support, AMD64-to-ARM64 example:

```bash
bazel build --platforms=@sonic_build_infra//platforms:aarch64_trixie \
  --host_platform=@sonic_build_infra//platforms:x86_64_trixie //path:target
```

Replace //path:target. Platform syntax does not prove component support. Derive matrices from Make analysis, product requirements and actual rules.

## Consumer and image capability checks

Locate actual consumers from selected MODULE/rules and verify toolchains/language versions/shared dependencies/install interfaces. Current code informs requirements, not proof of correct design. Check root and independent entries separately; parent rc/registration is not inherited.

Before kernel/rootfs/initramfs/ONE/KVM/RAW, read [image routes](image-recipes.md) and original production chains. Existing TAR/APT/toolchains do not prove full-image build/boot capability. Shared infrastructure owns missing generic mechanisms; components own platform data. Do not invent unverified macro names/attributes.
