# Wiring rootfs to installers and disks

Obtain inputs through [image analysis](image-recipes.md). Example images/example/BUILD.bazel is in buildimage. Caller image_inputs/BUILD aliases reference actual analyzed source/tool/platform producers.

| Alias | Required interface |
| --- | --- |
| skeleton/system/source/configuration/install_effects | Ordered single TARs; system locked data/control, source metadata |
| python_runtime | Checked complete installation TAR |
| boot_stage/kdump_stage | Stage-specific TAR with early tools/libraries/config/hooks |
| kernel_runtime/boot/metadata | Runtime TAR, boot tree, schema-1 metadata |
| busybox_applets | Target producer JSON |
| runtime_image | Runtime-validated OCI directory and declared blobs |
| platform_archive/onie_boot/grub_assets | Installation TAR/ONIE TAR/GRUB tree |
| install_sh/sharch_body/machine_conf/default_platform_conf/onie_image_conf/arch_image_conf/platforms_asic/efi_sbatlevel/grub_config/image_version_file | Actual recipe files/templates |
| mksquashfs/modprobe/depmod/zstd/mke2fs/debugfs/sgdisk/qemu_img/grub_mkimage/grub_editenv | Exec FilesToRunProvider including interpreters/loaders/libraries/data/subtools |

Use cquery for single TAR/tree contracts. Example values are AMD64/BIOS/4096 MiB/xz 128-KiB SquashFS/zstd-level-9 initrd/Docker disk/gzip store; derive real values from analysis/configuration rather than global defaults.

## rootfs and SquashFS

Confirm install_effects contains contractual accounts/services/caches/state and all runtime TARs, then declare ordered inputs:

```starlark
load("//tools/bazel/image:defs.bzl", "sonic_squashfs")

genrule(
    name = "rootfs",
    srcs = [
        "//image_inputs:skeleton", "//image_inputs:system",
        "//image_inputs:source", "//image_inputs:python_runtime",
        "//image_inputs:kernel_runtime", "//image_inputs:configuration",
        "//image_inputs:install_effects",
    ],
    outs = ["rootfs.tar"],
    tools = ["//tools/bazel/image:merge_layers"],
    cmd = '"$(location //tools/bazel/image:merge_layers)" --output-tar "$@" ' +
          '"$(location //image_inputs:skeleton)" "$(location //image_inputs:system)" ' +
          '"$(location //image_inputs:source)" "$(location //image_inputs:python_runtime)" ' +
          '"$(location //image_inputs:kernel_runtime)" "$(location //image_inputs:configuration)" ' +
          '"$(location //image_inputs:install_effects)"',
)
sonic_squashfs(
    name = "squashfs",
    layers = [":rootfs"],
    excludes = [],
    compression = "xz",
    block_size = 131072,
    mksquashfs = "//image_inputs:mksquashfs",
    out = "fs.squashfs",
)
```

merge_layers outputs a complete filesystem TAR with the same overwrite/delete/alias/hardlink/numeric-owner semantics as SquashFS. If only SquashFS is consumed, pass layers directly. Apply whiteouts rather than retaining deletion markers in full TARs. Build targets, obtain actual cquery paths and inspect managed tar/unsquashfs manifests, expected paths/deletions/modes/owners/links, then execute installed programs in matching environments.

## initramfs

boot/kdump stages carry their original-time config/init/hooks/early closure. Additional modules share kernel_runtime and directory merging.

```starlark
load("//tools/bazel/image:defs.bzl", "sonic_initramfs")

sonic_initramfs(
    name = "boot_initrd",
    layers = ["//image_inputs:boot_stage", "//image_inputs:kernel_runtime"],
    kernel_metadata = "//image_inputs:kernel_metadata",
    busybox_applets = "//image_inputs:busybox_applets",
    config_dir = "/etc/initramfs-tools",
    extra_config = [],
    modules = "most",
    compression = "zstd",
    compression_level = 9,
    modprobe = "//image_inputs:modprobe",
    depmod = "//image_inputs:depmod",
    zstd = "//image_inputs:zstd",
    out = "boot.initrd",
)
filegroup(name = "boot_initrd_audit", srcs = [":boot_initrd"], output_group = "audit")
sonic_initramfs(
    name = "kdump_initrd",
    layers = ["//image_inputs:kdump_stage", "//image_inputs:kernel_runtime"],
    kernel_metadata = "//image_inputs:kernel_metadata",
    busybox_applets = "//image_inputs:busybox_applets",
    config_dir = "/etc/initramfs-tools",
    extra_config = [],
    modules = "list",
    compression = "zstd",
    compression_level = 9,
    modprobe = "//image_inputs:modprobe",
    depmod = "//image_inputs:depmod",
    zstd = "//image_inputs:zstd",
    out = "kdump.initrd",
)
```

kdump_stage supplies its required modules file. Choose list/most from original config and get applets/drivers/firmware from producers. Inspect release/modules/dependencies/init/interpreters/devices/compression. Boot initrd feeds installer/disks; place kdump at original rootfs path using TAR.

## Docker storage

```starlark
load("//tools/bazel/image:defs.bzl", "docker_overlay2_store")

docker_overlay2_store(
    name = "docker_store",
    images = {"//image_inputs:runtime_image": "docker-example:runtime"},
    platform = "linux/amd64",
    compression = "gzip",
    out = "dockerfs.tar.gz",
)
```

Default source-built tar_split_metadata uses pinned tar-split, preserves original TAR bytes/diff IDs and handles duplicate zero-data directories. Go inputs use root ZIP update/checks. Real image sets come from LOAD_DOCKERS/inheritance. Check OCI/tag/diff/chain IDs/whiteout/layerdb, then validate full-machine loading/running with matching Docker. Docker save and store TAR are distinct.

## ONIE installer

Extract every template variable. Caller installer_values.bzl exports INSTALLER_VALUES for %%NAME%% from analysis/one configuration, sharing values with equivalent image attributes.

```starlark
load("//tools/bazel/image:defs.bzl", "onie_installer")
load(":installer_values.bzl", "INSTALLER_VALUES")

onie_installer(
    name = "installer",
    squashfs = ":squashfs",
    boot_files = "//image_inputs:kernel_boot",
    kernel_metadata = "//image_inputs:kernel_metadata",
    initrd = ":boot_initrd",
    platform_archive = "//image_inputs:platform_archive",
    dockerfs = ":docker_store",
    install_sh = "//image_inputs:install_sh",
    sharch_body = "//image_inputs:sharch_body",
    machine_conf = "//image_inputs:machine_conf",
    default_platform_conf = "//image_inputs:default_platform_conf",
    onie_image_conf = "//image_inputs:onie_image_conf",
    arch_image_conf = "//image_inputs:arch_image_conf",
    platforms_asic = "//image_inputs:platforms_asic",
    efi_sbatlevel = "//image_inputs:efi_sbatlevel",
    installer_variables = INSTALLER_VALUES,
    payload_name = "fs.zip",
    squashfs_name = "fs.squashfs",
    dockerfs_name = "dockerfs.tar.gz",
    docker_directory = "docker",
    docker_mode = "disk",
    dockerfs_compression = "gzip",
    platform_compression = "gzip",
    signing_mode = "no_sign",
    out = "sonic-example.bin",
)
```

For a template using only ARCH/IMAGE_VERSION/DEMO_TYPE:

```starlark
INSTALLER_VALUES = {
    "ARCH": "amd64",
    "IMAGE_VERSION": "example-1",
    "DEMO_TYPE": "SONiC",
}
```

Declare all other real variables; unresolved tokens fail explicitly. Dev signing needs openssl/cert/key; production needs signing_tool/inputs/args with input/output/mode expansion. Keys are authorized declared inputs; log identities/signature checks, not secrets. EFI signatures and installer CMS are distinct. Check header/payload boundaries/checksums/signatures/platform/boot/resources, then actual install/write/config/bootloader/upgrade behavior.

## KVM disks and RAW_IMAGE

Example BIOS/4096-MiB partition JSON derives from its recipe. EF02 partition and matching i386-pc assets receive GRUB core while retaining GPT and label-based boot configuration:

```json
{
  "firmware": "bios",
  "grub_platform": "i386-pc",
  "grub_modules": ["biosdisk", "part_gpt", "ext2", "normal", "linux", "search", "search_label"],
  "grub_prefix": "/grub",
  "grub_partition_role": "sonic",
  "grub_directory": "grub",
  "partitions": [
    {"number": 1, "role": "bios", "start_mib": 1, "size_mib": 1, "type": "EF02", "label": "BIOS-BOOT"},
    {"number": 2, "role": "onie", "start_mib": 2, "size_mib": 128, "type": "8300", "label": "ONIE-BOOT"},
    {"number": 3, "role": "sonic", "start_mib": 130, "type": "8300", "label": "SONiC-OS"}
  ]
}
```

```starlark
load("//tools/bazel/image:defs.bzl", "sonic_disk_image")

sonic_disk_image(
    name = "virtual_disk",
    squashfs = ":squashfs",
    boot_files = "//image_inputs:kernel_boot",
    kernel_metadata = "//image_inputs:kernel_metadata",
    initrd = ":boot_initrd",
    docker_store = ":docker_store",
    onie_boot = "//image_inputs:onie_boot",
    grub_assets = "//image_inputs:grub_assets",
    grub_assets_subdir = "",
    grub_config = "//image_inputs:grub_config",
    machine_conf = "//image_inputs:machine_conf",
    image_version_file = "//image_inputs:image_version_file",
    partition_layout = "partition_layout.json",
    platform_layers = ["//image_inputs:platform_archive"],
    payload_name = "fs.zip",
    squashfs_name = "fs.squashfs",
    dockerfs_name = "dockerfs.tar.gz",
    docker_directory = "docker",
    docker_mode = "disk",
    docker_store_compression = "gzip",
    disk_size_mib = 4096,
    sparse_threshold_bytes = 4096,
    mke2fs = "//image_inputs:mke2fs",
    debugfs = "//image_inputs:debugfs",
    sgdisk = "//image_inputs:sgdisk",
    qemu_img = "//image_inputs:qemu_img",
    grub_mkimage = "//image_inputs:grub_mkimage",
    grub_editenv = "//image_inputs:grub_editenv",
    out = "sonic-example.qcow2",
)
genrule(
    name = "raw_disk",
    srcs = [":virtual_disk"],
    tools = ["//image_inputs:qemu_img"],
    outs = ["sonic-example.raw"],
    cmd = '"$(location //image_inputs:qemu_img)" convert -f qcow2 -O raw ' +
          '"$(location :virtual_disk)" "$@"',
)
```

One JSON owns GPT types/labels/GRUB references. Verify pinned mke2fs supports TAR stdin/offset/numeric ownership/hardlinks/required xattrs before full builds. Match GRUB modules/tools/core/firmware. UEFI derives ESP/ONIE/SONiC partitions/filenames; AMD64 example:

```json
{
  "firmware": "uefi",
  "grub_platform": "x86_64-efi",
  "grub_modules": ["part_gpt", "fat", "ext2", "normal", "linux", "search", "search_label"],
  "grub_prefix": "/grub",
  "grub_partition_role": "sonic",
  "grub_directory": "grub",
  "partitions": [
    {"number": 1, "role": "efi", "start_mib": 1, "size_mib": 64, "type": "EF00", "label": "SONIC-ESP"},
    {"number": 2, "role": "onie", "start_mib": 65, "size_mib": 128, "type": "8300", "label": "ONIE-BOOT"},
    {"number": 3, "role": "sonic", "start_mib": 193, "type": "8300", "label": "SONiC-OS"}
  ],
  "efi_boot_filename": "BOOTX64.EFI",
  "efi_grub_filename": "grubx64.efi"
}
```

Replace layout and add parameters with matching x86_64-efi assets; FAT labels are limited to 11 characters:

```starlark
    partition_layout = "partition_layout_uefi.json",
    uefi_mode = "grub",
    mkfs_fat = "//image_inputs:mkfs_fat",
    mcopy = "//image_inputs:mcopy",
    mmd = "//image_inputs:mmd",
```

uefi_mode=grub builds EFI with declared tools. Required signed chains use signed mode, mapping original trusted files to ESP paths and selecting the mapped bootloader:

```starlark
    uefi_mode = "signed",
    efi_files = {
        "EFI/BOOT/BOOTX64.EFI": "//image_inputs:signed_shim",
        "EFI/BOOT/grubx64.efi": "//image_inputs:signed_grub",
    },
    efi_bootloader = "EFI/BOOT/BOOTX64.EFI",
```

Validate actual signatures/loading/kernel policy with original firmware/trust database. RAW filesystem reuses SquashFS; raw disks use raw_disk; other formats use corresponding tools with explicit input/output formats. Deliver only required formats.

## Step commands and boot

```bash
bazel build //images/example:rootfs //images/example:squashfs
bazel build //images/example:boot_initrd //images/example:boot_initrd_audit
bazel build //images/example:docker_store //images/example:installer
bazel build //images/example:virtual_disk
bazel cquery --output=files //images/example:virtual_disk
```

Check identity/type/manifests/modes/hashes/platform before handoff. Inspection tools come from declared validation environments. Example external BIOS/AMD64/serial/2048-MiB boot:

```bash
QCOW2=$(bazel cquery --output=files //images/example:virtual_disk)
qemu-system-x86_64 -m 2048 -nographic -no-reboot \
  -drive file="$QCOW2",format=qcow2,if=virtio
```

Use agreed QEMU/runtime and original network/CPU/firmware/devices. Save serial logs and check kernel/rootfs/container storage/login/services. Report installation, boot and business functionality separately.
