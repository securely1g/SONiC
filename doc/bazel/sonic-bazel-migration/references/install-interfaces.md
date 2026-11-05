# Installation targets, distribution formats and consumers

Read the entire [shared contract](common-contract.md), then applicable sections here for installation, DEB, wheel, OCI or rootfs delivery. Design public contents/metadata interfaces before formats. Maintain runtime TAR, compilation interface, metadata and installation-behavior contracts separately. Enable final DEBs only under the [existing boundary](../SKILL.md#require-approval-before-adding-new-deb-package-definitions).

## 1. Map producers and consumers

For each item record producer, target path/type/mode/uid/gid/links, conditions, runtime/development/symbol layer and consumers. Derive installation from original contracts rather than runfiles. Record authoritative metadata/derivation once.

```text
Native programs/libraries/resources + component version/install declarations
  ├─ Native compilation interfaces (CcInfo/PyInfo, etc.)
  └─ Installation contents and metadata
       ├─ Runtime TAR/development contents/matching symbols -> OCI, rootfs
       ├─ Component package identity, runtime requirements, installation behavior -> OCI, rootfs
       └─ Requested final distribution format -> DEB
Python distribution owner source + packaging metadata
  └─ Wheel -> shared wheel_layer -> Installation TAR -> OCI, rootfs
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
| Source-built Python distribution | Owner source/metadata -> wheel -> shared wheel_layer installation TAR |
| Pinned third-party prebuilt wheel | Locked wheel -> shared wheel_layer installation TAR |
| Existing native/generated binding runtime TAR | Retain its declared native installation interface within the task's scope |

For sources determine py_library/extensions, package paths, .data categories, entries and dist-info. The owner builds the wheel; the shared installer maps purelib/platlib/scripts/headers/data to the target interpreter layout and generates the installation TAR from it. Installed RECORD must describe actual files; shebang matches the target interpreter. Add runtime requirements/native libraries to the runtime closure.

Evaluate distribution/version/Requires-Python/Requires-Dist/extras/markers/entries/licenses/resources/ABI/tags. Rules centrally generate METADATA/WHEEL/RECORD/entries; components provide values, consumers do not duplicate algorithms.

Use the owner's declared source wheel target and infra python/wheel_layer.bzl. Keep one authoritative content/metadata declaration; obtain installation and runtime metadata from the selected wheel. Do not replace this route with site_packages/source_package_install, source-file copies or private wheel extraction. Assemblers obtain the complete closure through metadata and lock checks; ordinary deps or a wheel filename do not establish it.

```text
Owner package file targets + authoritative metadata
    -> Source-built wheel -> shared wheel_layer -> Installation TAR -> OCI, rootfs
```

Wheel installation is the intended transformation, including for source-built Python distributions. See the [Python producer example](python.md). Existing native/generated binding TARs and loose scripts/assets need no unrelated conversion; preserve their installation and runtime checks. A wheel-derived TAR remains wheel-based regardless of a target name such as runtime or pkg.

## 4. OCI and rootfs consumption

Collect owner-wheel identity, Requires-Python/Dist and installation TAR relationships under [runtime locking](dependency-locking.md#python-runtime-locks-and-requires-dist). Resolve the complete entries/target environment and commit the runtime lock. Normal images read it and verify provenance against current wheel metadata. Refresh after changes before assembly. Consume owner wheels and locked third-party wheels through the shared installer; every applicable requirement needs a matching input/version.

Use wheel_layer to produce reusable OCI/rootfs installation TARs. This Python 3.13 example consumes the owner-wheel interfaces and locked external hub from the [runtime lock workflow](dependency-locking.md#pip-runtime-lock-generation-example):

```starlark
load("@example_runtime_pip//:requirements.bzl", "all_whl_requirements")
load("@sonic_build_infra//python:wheel_layer.bzl", "wheel_layer")

wheel_layer(
    name = "installed_python",
    wheels = [
        "@example_common//:common_wheel",
        "@example_service//:service_wheel",
    ] + all_whl_requirements,
    site_packages = "/usr/local/lib/python3.13/dist-packages",
    scripts = "/usr/local/bin",
    headers = "/usr/local/include",
    data_prefix = "/usr/local",
    interpreter = "/usr/bin/python3",
    visibility = ["//visibility:public"],
)
```

Replace illustrative owner labels with actual source targets and list the complete locked closure. wheel_layer does not resolve dependencies. Obtain paths from the image runtime, third-party wheels from committed locks, and owner-wheel provenance from the selected source actions. Its DefaultInfo contains the TAR; it does not supply PythonRuntimeInfo or accept runtime_deps. Integrate a supported shared wheel metadata/lock-check interface before treating this TAR as a checked runtime; the build alone does not validate dependency resolution. A checker consuming this combined TAR must classify owner/external identities from the selected wheels; use separate owner/external layers as in the locking example when its interface classifies whole TARs.

OCI includes TARs with oci_image(tars=[...]) and separately declares base/user/entrypoint/environment/platform. Shared interfaces carry metadata/symbols. TARs do not execute postinst; contractual ordering/conflicts remain explicit.

Rootfs consumes the same TARs and centrally handles overwrite/modes/accounts/services/caches before filesystems; see [rootfs example](image-assembly-examples.md#rootfs-and-squashfs). Consumers differ in assembly behavior, without duplicate equivalent component packages.

RuntimePackagesInfo transitive metadata supports native package analysis; every actual runtime TAR still needs assembly inputs. Python wheel metadata and checked locks must preserve source producer identities and wheel/TAR relationships. Consume verified shared interfaces rather than assuming wheel_layer provides PythonRuntimeInfo or that ordinary deps/oci_image install transitives. See [OCI example](oci.md#7-incremental-assembly-template).

For real APT/dpkg scripts use [apt_install](oci.md#5-choose-installation-branch-and-implement-behavior). Its complete rootfs TAR replaces the root; do not overlay the old OCI base with it. Distinguish installer receipt from incremental selection. After real installation, add source TARs to an intermediate OCI, select/check again against that base, then reuse installed_packages. Retain separate identities for source TAR, fixed-distribution installation and real package-manager installation.

## 5. Acceptance

Build runtime TAR, metadata and requested final packages explicitly and use minimal OCI/rootfs consumers. Check paths/types/modes/ownership/links/ABI/closure/identity/install behavior. Retain upstream Python tests and check imports/entries/resources/distribution metadata from installed payloads. aquery must show owner source -> wheel -> shared WheelLayer action -> installation TAR for wheel-packaged Python, and direct installation contents for native TARs without a DEB round trip. Distinguish pinned external wheels from source-built owner wheels. Minimal consumers do not prove complete image boot. Follow [acceptance](review-port.md).
