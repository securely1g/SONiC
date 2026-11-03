# Migrate rootfs, kernel, initramfs and complete images

Read the [shared contract](common-contract.md). Original production determines whether kernel/rootfs/initramfs are tasks or internal stages. Inputs/options come from analysis; record source/install/assembly/boot separately. [OCI](oci.md) produces layouts consumed here.

## 1. Build the stage graph from analysis

For each stage map original location -> inputs -> configuration -> Bazel target -> format -> next consumer. Distinguish install TAR/layer/full rootfs/Docker save/overlay2/SquashFS/initrd/installer/disk by contract, not extensions.

| Stage | Inputs | Outputs/consumers |
| --- | --- | --- |
| Kernel | Pinned sources/patches/config/exec tools/target settings | Runtime TAR/full boot tree/metadata/symbols/development |
| rootfs | System/source/checked Python/config/install effects | Full TAR for filesystem/initramfs/real installer |
| initramfs | Stage layers/kernel metadata/config/modules/firmware | initrd/audit for ONIE/disk/kdump |
| Docker store | OCI/tag/platform/tar-split | overlay2 TAR for installer/disk |
| SquashFS | Ordered layers/exclusions/compression | Filesystem for ONIE/disk |
| ONE_IMAGE | SquashFS/boot/initrd/platform/templates/signing | ONIE bin |
| KVM_IMAGE | System/layout/ONIE boot/GRUB/tools | Contractual virtual disk |
| RAW_IMAGE | Confirmed filesystem/disk | Contractual raw output |

Decompose script effects into files/directories/accounts/services/caches/state/partitions/signing. Installation effects become layers; actual scripts use real installers. Assemblers consume declared effects without ad hoc dependencies or legacy full builds.

## 2. Kernel production and public interfaces

1. Derive architecture/release/ABI/LOCALVERSION/base config/fragments/order/compression/signing/modules/headers. Pass original configurable inputs through kernel_config and save originals/effective .config. All outputs bind the same configuration.
2. Use source module tools/bazel:kernel.bzl kernel_packages and kernel_config. Declare sources/patches/tools. Retain kernel-specific Kbuild in private action output directories, separating HOSTCC from target CC/ARCH/CROSS_COMPILE/sysroot. Production rules enforce native-platform requirements.
3. Export pre-packaging contents below directly. Requested DEBs reuse them. Runtime includes matching modules/dependencies/licenses; symbols match ELF.

Module-root production with existing fixed kernel_orig/debian/dsc; AMD64 example, with other supported architecture/exec-target variants selected explicitly:

```starlark
load("//tools/bazel:kernel.bzl", "kernel_packages")

kernel_packages(
    name = "kernel_artifacts",
    srcs = glob(["config.local/**", "patches-debian/**", "patches-sonic/**"]) + [
        "Makefile", "manage-config",
        "//tools/bazel:kernel_arch.py", "//tools/bazel:stage_kernel.py",
        "//tools/bazel:export_kernel.py",
    ],
    makefile = "Makefile",
    architecture = "amd64",
    orig = "@kernel_orig//file",
    debian = "@kernel_debian//file",
    dsc = "@kernel_dsc//file",
    build_tools = "@sonic_build_infra//tools/build_tools:kernel_runtime",
    exec_compatible_with = ["@platforms//os:linux", "@platforms//cpu:x86_64"],
    target_compatible_with = ["@platforms//os:linux", "@platforms//cpu:x86_64"],
)
```

build_tools is the full managed kernel tool-runtime archive; ordinary tools use executables/FilesToRunProvider. Native constraints follow this recipe, without component-selected C/C++ toolchains. Reuse existing kernel_artifacts/source/version/config rather than duplicate production.

kernel_config accepts original Make variables as JSON, identically for build/query. Example Trixie/VS/AMD64 defaults:

```bash
bazel build @sonic_linux_kernel//:runtime \
  '--@sonic_linux_kernel//tools/bazel:kernel_config={"CONFIGURED_ARCH":"amd64","CONFIGURED_PLATFORM":"vs","BLDENV":"trixie"}'
```

4. Export specific output groups rather than guessing default aggregates:

```starlark
filegroup(name = "runtime", srcs = [":kernel_artifacts"], output_group = "runtime_tar")
filegroup(name = "boot_files", srcs = [":kernel_artifacts"], output_group = "boot_files")
filegroup(name = "kernel_metadata", srcs = [":kernel_artifacts"], output_group = "kernel_metadata")
filegroup(name = "development", srcs = [":kernel_artifacts"], output_group = "development_tar")
filegroup(name = "debug_symbols", srcs = [":kernel_artifacts"], output_group = "debug_symbols")
```

| Output | Contract |
| --- | --- |
| runtime_tar | One installation TAR with release modules/dependencies/config/runtime files |
| boot_files | One tree retaining complete boot/, vmlinuz/config/System.map and applicable EFI/DTB |
| kernel_metadata | Schema 1, release/architecture/module_directory and boot trio path/SHA256 |
| development_tar | Headers/generated headers/Module.symvers/external-module build inputs |
| debug_symbols | Matching build-id/release/source |

Metadata names boot/vmlinuz-release, config-release and System.map-release from the same production. Consumers validate boot/initrd without duplicating release values:

```bash
bazel build @sonic_linux_kernel//:runtime @sonic_linux_kernel//:boot_files \
  @sonic_linux_kernel//:kernel_metadata @sonic_linux_kernel//:development
bazel cquery --output=files @sonic_linux_kernel//:kernel_metadata
```

Check release/architecture/modules/vermagic/dependencies/effective config/signatures. Boot tasks check actual release/module loading. Kernel-only tasks stay scoped; Make/final DEB export is conditional.

## 3. rootfs: build installation layers before merging

1. Extract suite/architecture/order/skeleton/accounts/services/config/caches from build_debian.sh/sets/templates, with explicit overwrite/deletion.
2. Use common [APT](use-apt-libraries.md) data/control, source runtime and checked Python TAR. Bind metadata/payload/state and map full closure to inputs.
3. Skeleton supplies merged-/usr and /var/run links first. Later layers add packages/config/effects. Preserve whiteout/opaque deletion, directory merge/order, numeric owners/modes/hardlinks/required xattrs.
4. [merge_layers](image-assembly-examples.md#rootfs-and-squashfs) reads/writes TARs directly. sonic_squashfs may consume the same layers without an unused full TAR.
5. Required APT/dpkg behavior uses [real installation](oci.md#real-debian-package-installation) on configured rootfs/raw locked DEBs, replacing the root before later source/config layers.

Check complete paths/types/modes/owners/links/loaders/libraries/interpreters/accounts/services/state/entry. Inspect manifests then run installed programs in matching isolation. Distinguish container applications from full boot; provide contractual devices/mounts/network/permissions.

## 4. initramfs: select stage-specific inputs

Distinguish boot/kdump initrd, original hooks/config/init/early tools/drivers/firmware/MODULES/explicit modules/compression. Call sonic_initramfs per stage with then-available rootfs, not incidental final-root contents.

Use [example](image-assembly-examples.md#initramfs) layers/metadata/config/extra_config/applets/modules/compression/level/modprobe/depmod/optional zstd. Tools are exec; modules/init closure target. BusyBox producer supplies applet lists; metadata binds release. Build initrd/audit and check modules/dependencies/firmware/interpreters/loaders/modes/devices/compression and kernel CONFIG_RD support. Boot checks init-to-root handoff; kdump checks original memory/dump requirements.

## 5. ONE_IMAGE, KVM_IMAGE and RAW_IMAGE

Follow [assembly](image-assembly-examples.md):

- onie_installer consumes SquashFS/full boot/metadata/initrd/platform/resources/templates/signing. Supply every template variable and original Docker/signing branches.
- sonic_disk_image consumes shared system inputs/ONIE boot/GRUB/config/version/partition JSON, matching BIOS/UEFI resources. Derive sizes/sparse thresholds from recipes.
- Determine raw filesystem versus disk. Reuse SquashFS directly; convert actual disks through declared qemu-img. Other filesystems use managed format tools on the same rootfs.

Check actual single-file/tree types before each build and inspect format/capacity/partitions/labels/UUID/checksums/contents/boot/signatures with declared tools. Install/boot on agreed hardware/VM with original firmware/CPU/memory/disk/network/serial. Report bin creation, installation, disk assembly and boot separately.

## 6. One source for tools and configuration

buildimage tools/bazel/image:defs.bzl owns assembly; source modules export compile/install interfaces. Obtain [exec tools](tool-recipes.md#image-filesystem-and-signing-tools), never host PATH. image_inputs aliases belong to callers with analyzed producers/versions. Shared payload/squashfs/docker names/directories/mode come from one config; disk example differs from ram compression/consumers. Preserve signing/platform/capacity/layout configurability. Save [acceptance](review-port.md) commands/artifact identities/results by stage.
