# Implement components from analysis

Read the entire [shared contract](common-contract.md), then applicable sections here and [infrastructure](infrastructure.md). Inputs are reviewed analysis.json/analysis.md. Default outputs are native builds, OCI-consumable TARs, metadata and consumer interfaces. Implement final DEBs only when explicitly requested under the [delivery boundary](../SKILL.md#consume-runtime-and-debug-tars-directly-for-oci).

Apply [native build/tool constraints](../SKILL.md#use-native-bazel-actions-and-declared-tools) and decide [source/build ownership](register-bazel-module.md#1-determine-source-and-build-ownership) before coding. Distinguish buildimage component directories, independent source repositories, registry and shared infrastructure. Record implementation ownership separately from independent-module necessity.

## Implementation plan and handoff

Create implementation.json and a concise implementation.md in the component task directory. Map analysis to public targets, real consumers and acceptance using [phase handoff](phase-handoff.md#1-carry-one-deliverable-through-all-phases). Record:

- Repository commits, uncommitted input identities, module selection and effective configuration.
- Source/infra versions, deliverables, module boundaries, platform/feature matrix and user exclusions.
- Original installed contents mapped to current runtime/development/tool/binding outputs; distinguish historical names, retained contents and explicitly requested final formats. Include existing libraries, runtime/symbol TARs, image metadata and actual consumers.
- Per-target original/generated sources, headers, libraries, parameters, layout and evidence.
- Concrete rules, labels, attributes, providers, toolchains, commands, shared interfaces and input configuration.
- Implementation prerequisites, status and acceptance: analyzed conclusions are expectations, Bazel outputs are observations.
- Files changed per repository, shared prerequisites and submodule relationships; maintain file/component/repository ownership and coordinate shared MODULE writers.

Before adding extensions, establish [necessity and ownership](infrastructure.md#rule-necessity-and-ownership). Separate parameters, tool calls and transformations before choosing files/actions rather than writing an all-in-one script first. Usually prepare generators/tools, then libraries/programs, then installation; use the real target graph. Newly discovered rule facts update analysis/evidence before implementation expectations. Follow [writing boundaries](component-workflow.md#4-review-existing-migration-and-coordinate-delegated-work), coordinate frozen validation inputs and keep evidence separate. [Freeze shared versions](infrastructure.md#freeze-shared-versions-for-this-task) before final consumer matrices; revalidate affected inputs after changes.

## Sources, patches and modules

Declare downloads, online/local patches, series and overrides under [source preparation](source-and-patches.md), including conditions/order/checksums. Follow [patch methods](source-and-patches.md#patch-application-methods); preserve local checkouts and original patches. Reuse actual rule semantics.

Pin sources, Debian packaging, generators and auxiliary inputs separately; local submodules and online archives may coexist. Preserve patch order/directories/strip and verify final code. Obtain paths/tool versions from declarations and checksums from actual inputs. Inherit the [origin inventory](source-and-patches.md#handoff-from-make-analysis-to-bazel-acquisition): acquisition rules, archive-to-label/tree mappings, patch stages and committed files. Pinned source packages supply external Debian files/patches; overlays maintain adaptation deltas rather than copies of extracted directories. Connect prepared files to compilation, installation or metadata consumers.

Keep component/shared code in owning repositories. Reuse [preparation rules](source-and-patches.md#choose-the-preparation-entry-before-the-rule); shared infrastructure owns generic mechanisms, MODULE/existing extensions declare fixed inputs/ordered recipes, and BUILD templates stay separate. MODULE declares actual direct dependencies/extensions/imports; simplification must preserve sources, patching and visibility. Choose independent modules versus root packages from delivery boundaries under [registry rules](register-bazel-module.md). After adding submodules, check recursive scans/.bazelignore and valid labels.

## Dependency updates and locking

Maintain APT/Go/Rust/pip inputs under [locking](dependency-locking.md). After additions, version changes or resolution-input changes, update owning declarations, re-resolve affected direct/transitive dependencies and synchronize locks/checksums/exports. Check root/independent selection before freezing. Record ownership, commands, tool versions and change scope; retain unrelated versions. The lead coordinates shared refreshes. Hand off locks with consumer changes.

## Library and header interfaces

Build a table for each consumer:

| Information | Contents |
| --- | --- |
| Origin | SONiC sources, pinned third-party sources, APT or toolchain sysroot; source/package/module version |
| Headers | Used files/public sets, original/generated paths, logical names, search categories/order |
| Libraries | Actual labels, static/shared form, SONAME, link files, development links, transitives |
| Parameters | Macros, forced includes, standards, ABI and ordered linker state |
| Role | Target compilation/runtime or exec tool; providers, files, runfiles |

Inspect actual rules, query build output, cquery files and necessary aquery. Package names, existing files and similar labels do not establish compilation/link contexts. Record exported header sets separately from consumed headers. Correctly configured actions provide generated/architecture headers. Propagate public headers through compilation contexts; verify static/shared linking and runtime libraries separately. For compile-only needs consume producer-exported header-only targets. Producers own headers, defines, include categories/directories and generated/platform headers; consumers must not trim CcInfo or infer include roots. See [APT](use-apt-libraries.md).

Preserve SONiC source dependency identity from original package injection; identically named APT packages are not substitutes. System Debian libraries use pinned APT public library targets, with per-library selection/contexts maintained by exporters. Consumers add deps directly without extraction/import/filter wrappers. Local rootfs APT repositories may select source-built packages; classify by actual injection path.

## File references and layout

Consume declared inputs directly under the [shared contract](common-contract.md#minimal-declarations-and-direct-file-consumption). Express header paths with includes/include_prefix/strip_include_prefix and producer exports; generated headers depend on producers. See [C/C++](native-cc.md). Directory views use declared files and applicable symlink interfaces, checking realpaths/closure. Fix tool/shared path handling instead of copying input trees. Generate actual installed layouts under [installation](install-interfaces.md).

## Language and artifact routes

Read concrete declarations/examples for [C/C++](native-cc.md), [language routes](language-recipes.md), [tools](hermetic-tools.md), [generation](code-generation.md), [installation](install-interfaces.md) and applicable [images](image-recipes.md). Design installation interfaces before distribution formats. Combining routes does not expand component scope.

| Object | Implementation requirements |
| --- | --- |
| C/C++ | Complete per-target sources/macros/include categories/order/standards/optimization/security and ordered linking; native rules and real CcInfo/shared interfaces; explicit generator actions |
| Go/CGo | Actual SDK/mod/sum/vendor patches/tags/generation/-X; actual rules_go/Gazelle; CGo follows native interfaces and must not be hidden by pure mode |
| Rust | Selected rules_rs/shared graph, versions/features/trait ownership/locks; build.rs/proc-macros exec, native libraries target; inspect actual rule attributes |
| Python/wheel | Patched package/resources/entry/metadata contract, library/wheel/install targets, target interpreter/ABI; shared source contents/metadata; pinned third-party wheel installation uses verified wheel_layer |
| Prebuilt | Preserve URL/version/architecture/checksum/contents/purpose and original identity; do not report as source rebuild; new DEBs use sonic_deb |
| Linux kernel | Sources/config merge order, architecture/cross tools/host generators, vmlinux/images/modules/headers, release/signing/compression; verify shared capability before pipelines, without copying unverified macros |

Handle each mixed-language target/binding. Preserve needed runtime/development/tool/symbol contents and TAR/native interfaces. Original primary/derived package lists guide contents, not automatic final DEB creation.

## Configuration and generators

Use [configuration](configuration.md) to preserve configurable versus fixed inputs and platform derivation. Before coding, apply [switch admission](configuration.md#admission-requirements-for-new-bazel-switches): record each proposed setting's actual entry, configurability evidence and effective argument propagation in the implementation plan for lead review. When only an upstream option or unused branch exists, retain original fixed behavior without adding a switch or acceptance combination. Model platforms, product features, defaults and debug/release separately. Select settings/transitions from actual rules; do not invent a component-global toolchain or make features switch compilers. Register required capabilities explicitly at root/independent entries and record selection.

### Build declarations and analysis evidence boundary

Apply [minimal declarations](common-contract.md#minimal-declarations-and-direct-file-consumption). Map analyzed sources, options, configuration and manifests to BUILD attributes/select/templates; record inputs, consumers, interfaces and source ownership. Keep analysis tools/raw probe data temporary. Maintain actual templates/delivery inputs with build code.

### Autoconf configuration generation

Probe under controlled inputs during migration and generate templates during normal builds. Use patched configure.ac/m4/config.h.in and other templates to identify all outputs and configure effects on selection, options and installation.

Use Bazel-selected compilers, target sysroot, dependency headers/libraries/options and original features. Containers may host probing without changing declared identities. Save source/patch/toolchain/dependency/platform/environment/command identities and config.log/config.status/generated-file evidence temporarily. This is migration analysis, without a Make artifact baseline build.

For each setting record value, origin, applicable inputs and consumer. Express only necessary values:

- Fixed toolchain/sysroot/dependency capabilities as confirmed attributes, with evidence.
- Sizes/endianness and architecture differences through target platform selection across the supported matrix.
- User features through configuration; versions/install paths derived from their authorities.
- Temporary tool/environment paths as declared tools/inputs while preserving installation semantics.

Generate config.h/other files with templates, preserving undef, define-zero and string escaping. Declare templates/settings/actual inputs with one source per value. Cross runtime answers require matching target execution or evidenced target contracts; executor results prove executor behavior only.

Recheck affected probes after source/patch/toolchain/sysroot/dependency/feature changes and add differences for new platforms. One probe proves only its input combination. Regular compilation/linking remains native; temporary configure entries stay temporary from creation. Record approved special exceptions under the main entry. Preserve equivalent CMake detection/platform/feature semantics.

Use [generation](code-generation.md) for Thrift/protoc/SWIG and actual Flex/Bison/Perl/Doxygen/custom/FRR-clippy requirements. Record inputs/outputs/commands/directories/macros/exec-target boundaries. Prefer existing shared/project tools including pinned DEB extraction, then BCR, then shared source-built tools. Record versions/platforms/origins/runtime closures; do not replace tools to add macOS support. Tools are exec; target headers/architecture descriptions remain target. Match generation/runtime ABI. Declare execution libraries/modules/templates/dictionaries/data. Bazel schedules concurrency; retained special make -j uses action capacity rather than client nproc. Avoid undeclared host/PATH inputs.

## Installation TARs and consumer handoff

Declare native targets, contents, identity and consumers under [installation](install-interfaces.md). Source Python wheel/install targets share contents/metadata; source installation does not unpack built wheels. Preserve separate pinned-third-party installation paths.

Generate runtime/development/tool/resource/symbol layouts from original rules. Implement configuration/licenses/entries/modes/links and applicable accounts/services. Default to installation TARs, matching symbols and image metadata, without sonic_deb, DEB exporters/tests or Make DEB bridges. Read [DEB rules](build-deb-with-sonic-deb.md) only when explicitly requested. ABI/Debian versions are separate from registry versions.

List public targets/real consumers separately for native libraries/programs, install layout, runtime/symbol TARs, metadata and requested DEBs. Preserve existing TAR/image interfaces across versions; new DEBs reuse them. OCI consumes runtime TARs; DEBs consume the same data layout. Runtime TARs independently cover paths/types/ownership/modes/links/resources/runtime closure. Runfiles do not replace installation. Preserve loader/interpreter search paths and pair symbols by build-id.

Producers own authoritative versions/dependencies/artifact relationships. Derive fields from recipes and actual payloads. Retain existing metadata-generation/TAR-validation capability; do not replace it with static copies. Images consume producer interfaces and implement account/service/configuration behavior beyond data extraction.

Where Make integration is explicitly requested, preserve names/paths through explicit labels, cquery outputs and exporters. TAR/OCI-only tasks do not add DEB export entries. Components deliver TARs; Bazel containers produce OCI/required Docker archives; Make image entries consume archives through existing BAZEL_TARGET selectors. Verify labels/dependencies/supported configurations per layer without automatically expanding to containers/full-image switching. See rules/docker-base-trixie.mk, docker-config-engine-trixie.mk and docker-orchagent.mk. BAZEL_MIN_READINESS defaults to bazel_disabled; a container is selected for the Bazel path only when it is registered in SONIC_BAZEL_DOCKER_IMAGES and declares a _BAZEL_READINESS level (experimental or stable) at or above that bar. Declaring readiness outside the group, or an invalid level, is a build error; debug images inherit their parent's readiness. Before adding integration read docker-orchagent.mk, slave.mk and tools/bazel/docker.mk for switching/cache/failure semantics.

## OCI and installation images

Follow [image procedures](image-recipes.md) for Docker, Linux kernel, rootfs, initramfs, ONE_IMAGE, KVM_IMAGE and RAW_IMAGE. ONE_IMAGE is ONIE; split rootfs/initramfs tasks only by actual production relationships.

Read current consumers such as dockers/docker-orchagent/BUILD.bazel before implementation. Declare base identity, source runtime/symbol TARs, pinned APT data/control, wheels and configuration separately. Under [OCI scope](../SKILL.md#build-oci-images-with-bazel-built-project-runtime-dependencies), complete migration covers inherited project components/transitives, reusing existing source producers and implementing missing producer support. Existing-input-only tasks record base identity/scope. Use contractual layer order/overwrite/preservation and APT policy/receipts, without copying reference whiteout macros.

Use oci/runtime_packages.bzl to derive metadata from authoritative recipes/real TARs. Merge producer-required paths and image requirements; verify MODULE, targets and payload. Where Debian state/query semantics matter, use oci/installed_packages.bzl and explicitly install generated status, retaining receipts. Selection receipts, labels and service manifests do not replace installed state. Include subsequently overlaid source TARs in final identity/dependency/file checks; base/APT checks do not prove the whole image.

Map configuration/startup/accounts/modes/directories/services/caches individually. Reuse Distroless accounts or compatible infrastructure, checking passwd/group, shadow, homes and service initialization separately. Data/account layers do not implement all maintainer scripts. Propagate symbols through runtime merges/filters and pair against deployed ELF. Debug images inherit matching runtime and check tool layers for ELF replacement. Report cross compilation, auxiliary-rule architectures and full-image matrices separately; full-image acceptance uses declared bases/platforms.

For ONE/KVM/RAW, distinguish rootfs/initramfs/kernel/modules/container storage/partitions/filesystems/bootloader/installer/compression/signing and reuse actual common outputs. APT extraction does not execute postinst/accounts/ldconfig/customization. Implement rule calls stage by stage from analysis. Use project evidence for rule names, disk parameters and architectures.

Build, inspect and fix each target under [acceptance](review-port.md), then complete registration and handoff.
