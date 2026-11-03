# Installation targets, distribution formats and consumers

Read the entire [shared contract](common-contract.md), then applicable sections here for installation, DEB, wheel, OCI or rootfs delivery. Design public contents/metadata interfaces before formats. Maintain runtime TAR, compilation interface, metadata and installation-behavior contracts separately. Enable final DEBs only under the [existing boundary](../SKILL.md#require-approval-before-adding-new-deb-package-definitions).

## 1. Map producers and consumers

For each item record producer, target path/type/mode/uid/gid/links, conditions, runtime/development/symbol layer and consumers. Derive installation from original contracts rather than runfiles. Record authoritative metadata/derivation once.

```text
Native programs/libraries/Python modules/resources + component version/install declarations
  ├─ Native compilation interfaces (CcInfo/PyInfo, etc.)
  └─ Installation contents and metadata
       ├─ Runtime TAR/development contents/matching symbols -> OCI, rootfs
       ├─ Component package identity, runtime requirements, installation behavior -> OCI, rootfs
       └─ Requested distribution formats -> DEB, wheel
```

Components choose public names. runtime, runtime.debug_symbols, development and runtime_metadata illustrate roles, not mandatory targets. Consumers declare payload, runtime dependencies, metadata and service/account behavior separately.

## 2. Native programs and DEB intermediate layers

Declare ELF/manifests using sonic_deploy_tar, providing runtime and symbol TARs:

```starlark
load("@sonic_build_infra//tar:sonic_deploy_tar.bzl", "sonic_deploy_tar")

sonic_deploy_tar(
    name = "runtime",
    binaries = {
        "./usr/bin/example type=file uid=0 gid=0 mode=0755 time=0": "//:example",
    },
    mtree = [
        ". type=dir uid=0 gid=0 mode=0755 time=0",
        "./usr type=dir uid=0 gid=0 mode=0755 time=0",
        "./usr/bin type=dir uid=0 gid=0 mode=0755 time=0",
    ],
    visibility = ["//visibility:public"],
)
```

Use actual TAR srcs/mtree/path mappings for libraries/resources/configuration/links. cquery verifies a single ELF rather than a target producing archives/link files too. Follow C/C++ for SONAME layout.

Bazel output processing may normalize TreeArtifact permissions. Express final installation modes at the archive-metadata boundary and inspect actual TAR members; an action's chmod proves that execution stage only. Debug data modes follow the install contract. debug_symbols_tar uses root_owned_tar's optional regular_file_mode="0644" for regular files. Its default preserves original modes; directories, symlinks and hardlinks retain their respective contracts. Changes to shared archive rules require checking default-call compatibility, explicit modes and actual symbol TAR contents/build-id/debuglink pairing.

When DEB output is requested, sonic_deb(data=":runtime",...) reuses the TAR; see [complete examples](build-deb-with-sonic-deb.md#3-simple-runtime-and-symbols-packages). OCI/rootfs consume runtime directly, without unpacking example_deb.

| Metadata | Source/use |
| --- | --- |
| Package/Version/Architecture | Recipes, version rules, target platform or architecture-independent contract |
| Maintainer/Description | Original declarations and long-description formatting |
| Depends/Pre-Depends/Provides/Conflicts/Breaks/Replaces | Original applicable relationships/calculations |
| Section/Priority/Multi-Arch/Homepage/license | Original and consumer requirements, judged individually |
| conffiles/scripts/triggers | Install/upgrade behavior, generation inputs/stages/conditions |
| Manifests/digests/Installed-Size | Actual contents, not copied historical values |

Pass TAR, finalized control and control_files through [shared packaging](build-deb-with-sonic-deb.md#2-shared-packaging-interface). Producer runtime_packages declares authoritative control/changelog, real TARs and dependency metadata. Debian relations, Bazel deps and runtime file closures are different contracts. Downstream installers explicitly implement account/service behavior.

Minimal producer metadata:

```starlark
load("@sonic_build_infra//oci:runtime_packages.bzl", "runtime_packages")

runtime_packages(
    name = "runtime_metadata",
    control = "debian/control",
    changelog = "debian/changelog",
    module_name = "example_component",
    packages = {"example": ":runtime"},
    visibility = ["//visibility:public"],
)
```

packages keys match binary packages in control; changelog source/version rules match recipes. Inspect selected implementation for default module mappings/architecture/platform support. Declare APT data/control, dependency metadata, substvars/symbols through public attributes only when needed. Consumers use generated identity/payload relationships rather than final DEBs. Per-package <name>.<package>.control single-file targets share dependency calculation/architecture/control provenance with final packaging.

## 3. Shared Python source and wheel inputs

| Identity | Installation route |
| --- | --- |
| Source-built Python | Shared files/resources/extensions/metadata generate wheel and installation TAR |
| Pinned third-party prebuilt wheel | Assembly generates installation TAR, below |

For sources determine py_library/extensions, package paths, .data categories, entries and dist-info. Wheel/install branches share content declarations. Map purelib/platlib/scripts/headers/data to target interpreter layout, generate scripts/metadata/TAR and expose directly to OCI/rootfs. Installed RECORD must describe actual files; shebang matches the target interpreter. Add runtime requirements/native libraries to runtime closure.

Evaluate distribution/version/Requires-Python/Requires-Dist/extras/markers/entries/licenses/resources/ABI/tags. Rules centrally generate METADATA/WHEEL/RECORD/entries; components provide values, consumers do not duplicate algorithms.

Use infra python/site_packages.bzl. files maps sources/resources explicitly. Share distribution/version/requires/extras/entries with py_wheel. runtime_deps points to source dependency install targets. Default output is this package's TAR; PythonRuntimeInfo propagates source/dependency metadata and TAR relationships. Assemblers obtain closure through plans/checks, not ordinary deps alone.

```text
Package file targets + one shared metadata declaration
    ├─ py_wheel -> .whl
    └─ site_packages -> This package's installation TAR + PythonRuntimeInfo -> OCI, rootfs
```

Both branches may generate their required metadata; avoiding one ordinary archive is not a reason to invent an unused provider. Source installation must not unpack the final wheel. See [Python](language-recipes.md#python-and-wheels); prebuilt wheel installation belongs to assembly below.

## 4. OCI and rootfs consumption

Collect source identity, Requires-Python/Dist and TAR relationships under [runtime locking](dependency-locking.md#python-runtime-locks-and-requires-dist). Resolve the complete entries/target environment and commit the runtime lock. Normal images read it and verify provenance against current metadata. Refresh after changes before assembly. Consume source TARs and locked third-party wheels; every applicable requirement needs a matching input/version.

Use wheel_layer at assembly to produce reusable OCI/rootfs installation TARs. Python 3.13 example:

```starlark
load("@sonic_build_infra//python:wheel_layer.bzl", "wheel_layer")

wheel_layer(
    name = "third_party_runtime",
    wheels = ["@locked_distribution//:wheel"],
    site_packages = "/usr/local/lib/python3.13/site-packages",
    scripts = "/usr/local/bin",
    headers = "/usr/local/include",
    data_prefix = "/usr/local",
    interpreter = "/usr/bin/python3",
    visibility = ["//visibility:public"],
)
```

Replace @locked_distribution//:wheel with actual locked targets and list the complete closure. wheel_layer does not resolve dependencies. Obtain paths from the image runtime and wheels from committed locks.

OCI includes TARs with oci_image(tars=[...]) and separately declares base/user/entrypoint/environment/platform. Shared interfaces carry metadata/symbols. TARs do not execute postinst; contractual ordering/conflicts remain explicit.

Rootfs consumes the same TARs and centrally handles overwrite/modes/accounts/services/caches before filesystems; see [rootfs example](image-assembly-examples.md#rootfs-and-squashfs). Consumers differ in assembly behavior, without duplicate equivalent component packages.

RuntimePackagesInfo transitive metadata supports native package analysis; every actual runtime TAR still needs assembly inputs. PythonRuntimeInfo/checks propagate Python source TARs. Consume real fields rather than assuming ordinary deps or oci_image installs transitives. See [OCI example](oci.md#7-complete-incremental-assembly-example).

For real APT/dpkg scripts use [apt_install](oci.md#5-choose-installation-branch-and-implement-behavior). Its complete rootfs TAR replaces the root; do not overlay the old OCI base with it. Distinguish installer receipt from incremental selection. After real installation, add source TARs to an intermediate OCI, select/check again against that base, then reuse installed_packages. Retain separate identities for source TAR, fixed-distribution installation and real package-manager installation.

## 5. Acceptance

Build runtime TAR, metadata and requested final packages explicitly and use minimal OCI/rootfs consumers. Check paths/types/modes/ownership/links/ABI/closure/identity/install behavior. Python checks imports/entries/resources/distribution metadata. aquery must show source installation directly consumes files without DEB/wheel repack/unpack; classify fixed-third-party extraction separately. Minimal consumers do not prove complete image boot. Follow [acceptance](review-port.md).
