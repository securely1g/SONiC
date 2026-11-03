# Build final DEBs with sonic_deb

Read the [shared contract](common-contract.md). Use this route only for explicitly requested final DEBs. Default delivery is installation TARs, symbols and runtime metadata. Use shared sonic_deb; component owners retain source builds/layout/recipes, and OCI/rootfs reuse pre-packaging interfaces.

## 1. Derive packaging inputs from analysis

For primary/development/data/tool/symbol packages, obtain names, versions, architecture, manifests, relationships, scripts, conffiles, triggers and conditions. Build installation TARs first, declaring paths/types/modes/numeric uid/gid/links/conditions.

| Original content | Declaration |
| --- | --- |
| Data/ELF/resources/links/modes | sonic_deploy_tar/TAR; DEB preserves numeric metadata |
| Package/Version/Architecture/Maintainer/Description | Simple sonic_deb scalars or authoritative finalized control, not both |
| Relations/Multi-Arch/Section/Priority/Homepage/long description | Finalized control; calculate dynamic fields with runtime_packages first |
| preinst/postinst/prerm/postrm/config/conffiles/triggers/symbols/shlibs | control_files maps archive member names to file targets |
| md5sums/Installed-Size | Shared packager derives from real TAR |

Resolve shlibs:Depends with runtime_packages target-library analysis. Source libraries supply RuntimePackagesInfo; apt_packages pairs target data/control. Pass required symbols/substvars/debian_files. Inputs stay target-configured; analysis tools use exec. Expand required variables, preserve relations and fail unknown variables. Metadata and DEBs share finalized control/dependency calculation.

## 2. Shared packaging interface

```starlark
load("@sonic_build_infra//deb:sonic_deb.bzl", "sonic_deb")
```

| Attribute | Contract |
| --- | --- |
| data | One pre-packaging installation TAR; preserve legal numeric owners/modes/types/links |
| control | One finalized binary control with required/original optional fields |
| control_files | Archive member -> single-file label for scripts and control data |
| package/version/maintainer/description/depends | Simple mode only; control mode obtains them from its file |
| architecture | Simple mode defaults target, mapped from platforms; explicitly all for independent data |

Control mode derives name/version/architecture and filename. Duplicate field sources fail. With target ELF, Architecture must match target. Preserve Architecture: all semantics for ELF-free data. Shared platforms map scalar target architecture; components do not choose C/C++ toolchains.

Control scripts are executable/root-owned; conffiles/triggers/symbols/shlibs are data/root-owned. Data TAR owners remain independent. conffiles paths must exist. Reject escaping/duplicate members and overrides of generated control/md5sums. Preserve relationships, multiline descriptions, blank lines and continuations.

## 3. Simple runtime and symbols packages

In dist/BUILD.bazel, //:example is source-built. Substitute analyzed recipe identities:

```starlark
load("@sonic_build_infra//tar:sonic_deploy_tar.bzl", "sonic_deploy_tar")
load("@sonic_build_infra//deb:sonic_deb.bzl", "sonic_deb")

package(default_visibility = ["//visibility:public"])
sonic_deploy_tar(
    name = "example_runtime",
    binaries = {"./usr/bin/example type=file uid=0 gid=0 mode=0755 time=0": "//:example"},
    force_debug_build = True,
    mtree = [
        ". type=dir uid=0 gid=0 mode=0755 time=0",
        "./usr type=dir uid=0 gid=0 mode=0755 time=0",
        "./usr/bin type=dir uid=0 gid=0 mode=0755 time=0",
    ],
)
sonic_deb(
    name = "example_deb",
    data = ":example_runtime",
    package = "example",
    version = "1.0.0",
    maintainer = "SONiC <sonic@example.com>",
    description = "Example service",
    depends = ["libc6 (>= 2.34)"],
)
sonic_deb(
    name = "example_dbg_deb",
    data = ":example_runtime.debug_symbols",
    package = "example-dbg",
    version = "1.0.0",
    maintainer = "SONiC <sonic@example.com>",
    description = "Debug symbols for example",
    depends = ["example (= 1.0.0)"],
)
```

Pair runtime/symbols by build-id from the same ELF. force_debug_build preserves debug information while original optimization remains. Fixed example depends is recipe-defined; dynamically derived relations use the next route rather than copied scans.

## 4. Authoritative recipes, scripts and independent packages

Assume runtime/data_runtime and real control/changelog. example has original architecture/shlibs relations; example-data is Architecture: all. Declare data ownership with mtree; scripts/conffiles/triggers come from recipes/generated targets.

```starlark
load("@sonic_build_infra//oci:runtime_packages.bzl", "runtime_packages")
load("@sonic_build_infra//deb:sonic_deb.bzl", "sonic_deb")

runtime_packages(
    name = "packages",
    control = "debian/control",
    changelog = "debian/changelog",
    packages = {"example": ":runtime", "example-data": ":data_runtime"},
    module_name = "example-component",
    dependencies = ["@example_library//:runtime_metadata"],
)
sonic_deb(
    name = "example_deb",
    data = ":runtime",
    control = ":packages.example.control",
    control_files = {
        "postinst": "debian/example.postinst",
        "conffiles": "debian/example.conffiles",
        "triggers": "debian/example.triggers",
    },
)
sonic_deb(
    name = "data_deb",
    data = ":data_runtime",
    control = ":packages.example-data.control",
)
```

runtime_packages exports <name>.<package>.control per binary package, preserving all architecture. Control-mode sonic_deb defaults to a single directory <target>.debs/ containing exactly one control-named DEB; scalar mode outputs the DEB file directly. Obtain outputs with cquery, then select the unique DEB for dpkg-deb/Make export. Source-library metadata supplies RuntimePackagesInfo; system libraries expose [APT library targets](use-apt-libraries.md) plus matching metadata data/control. Declare original symbols explicitly.

Simple data packages may use scalar architecture=all. Omit absent scripts; preserve real scripts/conditions and verify install/upgrade/removal in isolated target environments. OCI implements script effects under its installation branch using shared contents/metadata rather than final DEB extraction.

## 5. Build, inspect and hand off to Make

MODULE selects infra/toolchains; root configuration selects platforms. Shared rules declare ar/bsdtar/Python/analysis tools; validation uses pinned dpkg-deb:

```bash
bazel build --platforms=@sonic_build_infra//platforms:x86_64_trixie \
  //dist:example_deb //dist:example_dbg_deb
bazel cquery --platforms=@sonic_build_infra//platforms:x86_64_trixie \
  --output=files //dist:example_deb
```

Obtain actual paths, then inspect --info/--contents/--control/--extract:

1. Identity, architecture, complete relations, descriptions/options and same-source metadata.
2. Full data, numeric ownership/modes/links/conffiles, script modes and triggers.
3. ELF architecture/runtime closure, runtime/debug build-id, no target ELF in all packages.
4. md5sums, Installed-Size, ar order/archive formats and read-only normal inputs.
5. Actual installation/upgrade/removal account/service/cache/trigger behavior where scripts exist.

Reuse deb/assert_deb.bzl checks with expectations from analysis/Debian contracts. Validate Bazel artifacts without a new original-Make artifact baseline. When Make DEB integration is requested, wrappers invoke Bazel, query outputs and export to original DEST/target/debs/<distribution>, preserving primary/derived relationships; sonic_deb still packages. Registry presubmits explicitly cover requested DEBs/tests. Default TAR delivery builds/checks runtime/symbols/metadata separately under [acceptance](review-port.md#bazel-artifacts-and-installation-contract).
