# Migrate OCI container assembly

Read the [shared contract](common-contract.md). Convert original inputs/install behavior to inspectable Bazel actions, then verify installed contents/startup. This page produces OCI layouts (directories/blobs). Receipts are rule-specific validation/install records with different schemas. For Docker storage/rootfs/full images use [image routes](image-recipes.md). Substitute analyzed targets/versions/paths.

## 1. Analyze the original image and scope

Read Dockerfiles/templates/base/install sets/customization from Make analysis. Distinguish complete source migration from existing-input assembly. Complete migration includes inherited project components. Record source lines/conditions/inputs/effects/Bazel owner/check for every operation:

| Operation | Contract | Implementation |
| --- | --- | --- |
| FROM | Suite/digest/platform/inherited files/accounts/packages/project components | Pinned OCI and inheritance checks |
| apt | Roots/full closure/sources/scripts/configuration | Common lock/public inputs/step-5 installation |
| pip/source install | Producers/Requires-Dist/Python/platform/extras/paths | Source-owner wheels/runtime lock/shared wheel_layer TARs |
| COPY/ADD | Origins/paths/overwrite/mode/uid/gid/links | Producer or resource/configuration TAR |
| RUN/customization | File/account/service/cache/state effects and stages | Explicit actions or dedicated real installer |
| USER/ENV/WORKDIR/entry | Numeric identity/expansion/directory/argv/signals | OCI config/startup checks |
| Debug | Exact runtime/tools/symbols/conditions | Separate debug layers/image |

Completion: every file/startup effect has an owner; distinguish build deps/exec tools/actual image runtimes.

## 2. Verify producers, versions and shared interfaces

Read selected module/registry recipes and record exact sources/patches/rules/locks. Prepare interfaces topologically and freeze before final checks. Version strings do not prove APIs.

| Capability | Interface | Boundary |
| --- | --- | --- |
| Source installation | sonic_deploy_tar/language installs | Native contents -> runtime/symbol TARs |
| Native metadata | runtime_packages/group | Recipes/TAR/deps -> identity/relations/payload |
| Incremental APT | apt_layer | Base/lock/data-control/policy -> layer/selection |
| Python closure | Source-owner wheels/shared wheel_layer plus verified metadata/check adapter | Wheels/metadata/lock -> checked installation TAR |
| Accounts | accounts/account_layer | Actual pre-change OCI -> passwd/group/receipt |
| State | installed_packages | Same base/selection/source metadata/TARs -> status/metadata |
| OCI/archive | oci_image/load | Ordered layers/config -> layout/Docker archive |
| Symbols | debug_symbols_layer/producer APIs | Exact runtime graph -> symbols |
| Real installation | apt_install | Configured rootfs/raw DEBs/native environment -> full TAR/receipt |

Explicitly build inputs/metadata/plans/records before final images. Record labels/versions/real outputs and compare full runtime set to analysis. Completion: every runtime component has a consumable target and all rules/inputs are declared.

## 3. Close runtime dependencies and bind install artifacts

Recursively close selected entries/original installation relations:

| Identity | Producer | Requirements | Installation | Verification |
| --- | --- | --- | --- | --- |
| Native source | Module/commit | control/runtime metadata | Public runtime TAR | Producer then complete image set |
| Python source | Source owner/wheel/version/metadata | Requires-Dist/markers/extras | Wheel -> shared wheel_layer TAR | Wheel metadata/plan/installed-closure checks |
| Third-party Python | Locked version/origin/hash | Resolver metadata | Full locked-wheel TAR | Closure/imports |
| APT | Common lock/set | Edges/control | data-control or raw DEBs | Selection/install/runtime |
| Inherited | Pinned base/metadata | Actual package/files | OCI layers | Identity/version/missing/conflicts |

Compile deps do not install files. RuntimePackagesInfo is analysis metadata, not implicit image layers; include public TARs explicitly. Associate metadata requirements with sources/APT/Python inputs. Fix missing producer/TAR, collisions or unsatisfied versions at their owners. Exec private libraries do not provide target runtime. Completion: unique identities and real install origins explain inherited/new closure.

## 4. Prepare locks, state inputs and configuration

Use infra common sources/requests/production APT lock and image set. Actually [update/check](dependency-locking.md#apt), then derive apt_inputs labels. [Python](dependency-locking.md#python-runtime-locks-and-requires-dist) collects metadata from the source-owner wheels and pins interpreter/platform/extras/index. Install those wheels with shared `wheel_layer`, and use `all_whl_requirements` for the locked external closure. Connect complete closure, installed-metadata and staleness checks to the final installation TAR.

Verify the selected shared API first. The inspected `wheel_layer` returns only a TAR;
`python_runtime_plan` and `checked_python_runtime` require a provider it does not emit.
Complete the [shared wheel metadata adapter](dependency-locking.md#pip-runtime-lock-generation-example)
before using those rules for wheel inputs. Wheel installation alone is not runtime validation.

Separate plans from final assembly packages so plans build independently. Initial empty requirements_lock may bootstrap pip.parse only when absent; formal update/check precedes images. Retain existing locks.

Producers derive native identity/relations/payload hashes. source_spec holds image-specific path requirements while producer required_paths remains enforced. source_modules binds actual selected MODULE, using infra exports if needed. Python dist-info is distinct from Debian state. Declare analyzed configuration/scripts/accounts/templates/paths/modes/conditions. Completion: deterministic lock/provenance/configuration, with updates separate from normal builds.

## 5. Choose installation branch and implement behavior

### Incremental layers

Where declared file/account/service/cache actions express original effects, consume source TARs, locked APT and Python TARs. apt_layer verifies actual OCI base/control/version/file selection; export selection receipts. Pass base_package_metadata for inherited selection lacking base status where supported. Implement/execute script-equivalent effects.

Accounts consume actual pre-change OCI, including prior account changes via intermediate images. They only manage passwd/group; homes/shadow/modes/services/certificates need their own actions. Original contracts decide script execution. installed_packages generates state, not scripts. Match state to real payload/effects and distinguish runtime metadata, selection and state.

### Real Debian package installation

For required APT/dpkg/scripts/triggers:

1. Provide complete configured rootfs with APT/dpkg. OCI conversion replays ordered whiteout/opaque/overwrite/link semantics, not concatenated layers.
2. Select raw DEBs/full dependencies from common lock. Declare bubblewrap/closure, native architecture, fixed execution-container digest and real namespace/root permissions.
3. Workers/CI actually provide that container. execution_environment is an action identity string, not environment provisioning. Match target/native executor requirements.
4. Consume the complete filesystem TAR as replacement root, without old base layers; otherwise deleted files reappear.
5. Inspect real dpkg state/installer receipt. It is not apt_layer selection. Before adding source TARs, form intermediate OCI from full rootfs, recheck locked sets with apt_layer against that base, then feed matching selection/base/source metadata to installed_packages. Existing packages should be inherited; new scripted packages return to installation. Build/check intermediate identities/payload before final OCI.

Source native components consume their installation TARs; Python distributions use source-owner wheels installed through shared `wheel_layer` under [installation](install-interfaces.md). This branch installs fixed distributions needing real scripts. Prepare rootfs/tools through [image routes](image-recipes.md#3-rootfs-build-installation-layers-before-merging), with the same native environment/digest/permissions. Completion: every original effect has inputs/actions/environment/observations.

## 6. Layer ordering and path semantics

List ordered stages and origins/purpose/checks for overwrite/deletion. Distinguish directory merges, identical files, permitted overwrites, conflicting contents and type changes. Use normalize_layer/receipts for required merged-/usr or /var/run normalization, sharing results with state validation. Do not copy extracted trees to repair paths.

Check contractual numeric owners/modes/hardlinks/symlinks/capabilities/xattrs. Members are safe root-relative paths; legal absolute links retain target-root semantics rather than host interpretation. OCI consumers handle whiteout/opaque. flatten is not a universal OCI rootfs replay engine. Generate status/metadata TAR before image inclusion and keep base/selection/source/layout aligned. Recheck later overwrites. Completion: explicit layer identities/order/final metadata agreement.

## 7. Incremental assembly template

Example contract: AMD64 Debian/Python 3.13, source exampled/libexample1, Python service[metrics]/transitive common, locked external requirements, /etc/example/config.json, uid/gid 21000, /var/lib/example. Example programs expose version/self-check; substitute real interfaces. Multiarchitecture work maps platform -> OCI architecture -> APT set -> Python plan/lock/provenance -> runtime/debug, rather than changing config architecture alone. Names are roles, not actual product lists.

This template assumes a completed shared wheel metadata/check adapter supplies
`//dockers/docker-example:python_plan` and `:python_runtime` in the runtime package.
The latter must validate and merge the two wheel-layer TARs shown below. Its definition is
intentionally omitted because the inspected shared API cannot provide it directly for wheels.
This is an assembly contract, not a ready-to-build recipe until that prerequisite is supplied.

### Inputs and MODULE

Select compatible rules/source versions, reusing root declarations. Dependencies include rules_oci/distroless/python, tar.bzl, infra and source owners example_native/library/python. Native module names are hyphenated, aliases underscored.

| Input | Public interface |
| --- | --- |
| Native program/library | @example_native//dist:runtime and @example_library//dist:runtime |
| Metadata | Each //:runtime_packages.json, original recipes/required_paths |
| Python | @example_python//:service_wheel and :common_wheel with source metadata and checked closure |
| APT | Common example_runtime set including target Python/libstdc++/closure |
| Base | Pinned example_base or original OCI |

Maintain/update infra requests before importing. MODULE fragment assumes selected versions/sets:

```starlark
oci = use_extension("@rules_oci//oci:extensions.bzl", "oci")
oci.pull(
    name = "example_base",
    image = "docker.io/library/debian",
    digest = "sha256:fac46bff2e02f51425b6e33b0e1169f55dfb053d83511ca28aa50c09fd5ed7a4",
    platforms = ["linux/amd64"],
)
use_repo(oci, "example_base")
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.import_lock(
    lock = "@sonic_build_infra//apt:apt.lock.json",
    sources = "@sonic_build_infra//apt:sources.json",
    requests = "@sonic_build_infra//apt:requests.json",
    dependency_sets = ["example_runtime"],
)
use_repo(apt, "example_runtime")
apt_inputs = use_repo_rule("@sonic_build_infra//apt:inputs_repository.bzl", "apt_inputs")
apt_inputs(name = "example_apt_inputs", lock = "@sonic_build_infra//apt:apt.lock.json")
source_modules = use_repo_rule("@sonic_build_infra//oci:source_modules.bzl", "source_modules")
source_modules(
    name = "example_source_modules",
    modules = {
        "@example_native//:MODULE.bazel": "example-native",
        "@example_library//:MODULE.bazel": "example-library",
    },
)
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(python_version = "3.13", is_default = True)
pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
pip.parse(
    hub_name = "example_runtime_pip",
    python_version = "3.13",
    requirements_lock = "//dockers/docker-example:python/requirements_lock.txt",
)
use_repo(pip, "example_runtime_pip")
```

### Independent runtime plan and update

Keep the parent plan independent of final pip/assembly imports. Export the three owner files:

```starlark
package(default_visibility = ["//visibility:public"])
exports_files([
    "python/requirements.in",
    "python/requirements_lock.txt",
    "python/lock-inputs.json",
])
```

The adapter's `python_plan` reads metadata from `service_wheel` and `common_wheel`, uses
root `example-service[metrics]`, and records both source identities, Python `3.13`, platform
`x86_64-unknown-linux-gnu`, uv `0.12.18`, target markers and resolver inputs. It must reject a
missing source producer or incompatible metadata. Do not pass raw wheels or wheel-layer TARs
to the existing provider-only `python_runtime_plan(packages = ...)` interface.

After the adapter and initial bootstrap are in place, run pinned uv against retained existing versions:

```sh
bazel build //dockers/docker-example:python_plan
PLAN=$(realpath bazel-bin/dockers/docker-example/python_plan.plan.json)
OWNER="$PWD/dockers/docker-example/python"
bazel run @sonic_build_infra//python:runtime_lock -- update \
  --plan "$PLAN" --requirements "$OWNER/requirements.in" \
  --lock "$OWNER/requirements_lock.txt" --inputs "$OWNER/lock-inputs.json" \
  --uv "$UV"
```

UV is verified uv 0.12.18 absolute path. Deliver lock/requests/provenance together. Resolve PLAN before bazel run configuration switches can change convenience links.

### Runtime, state, accounts and debug

runtime/BUILD uses actual producer APIs and buildimage apt_layer wrapper/selector. Independent repositories must provide equivalent declared interfaces rather than assume private workspace labels are shared APIs.

```starlark
load("@example_apt_inputs//:apt_inputs.bzl", "APT_INPUTS")
load("@example_runtime_pip//:requirements.bzl", "all_whl_requirements")
load("@rules_distroless//distroless:defs.bzl", "flatten")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_load")
load("@sonic_build_infra//oci:accounts.bzl", "account_layer")
load("@sonic_build_infra//oci:debug_symbols_layer.bzl", "debug_symbols_layer")
load("@sonic_build_infra//oci:installed_packages.bzl", "installed_packages")
load("@sonic_build_infra//python:wheel_layer.bzl", "wheel_layer")
load("@tar.bzl", "tar")
load("//tools/bazel/oci:apt_layer.bzl", "apt_layer")
load("//tools/bazel/oci:normalize_layer.bzl", "normalize_layer")
package(default_visibility = ["//visibility:public"])
_PACKAGES = APT_INPUTS["example_runtime"]["amd64"]
_UID = 21000
_GID = 21000
_SOURCES = {
    "example-native": "@example_native//dist:runtime",
    "libexample1": "@example_library//dist:runtime",
}
oci_image(name = "base", base = "@example_base")
apt_layer(
    name = "apt_runtime",
    base = ":base",
    dependency_set = "example_runtime",
    lock = "@sonic_build_infra//apt:apt.lock.json",
    packages = _PACKAGES,
    policy = {"schema": 1, "image": "docker-example", "architecture": "amd64", "distribution": "trixie", "retained_source": "none", "features": {}},
    variant = "runtime",
)
filegroup(name = "apt_selection", srcs = [":apt_runtime"], output_group = "selection")
flatten(name = "apt_files", tars = [":apt_runtime"], deduplicate = True)
wheel_layer(
    name = "source_python",
    wheels = [
        "@example_python//:common_wheel",
        "@example_python//:service_wheel",
    ],
    site_packages = "/usr/local/lib/python3.13/dist-packages",
    scripts = "/usr/local/bin",
    interpreter = "/usr/bin/python3",
)
wheel_layer(
    name = "external_python",
    wheels = all_whl_requirements,
    site_packages = "/usr/local/lib/python3.13/dist-packages",
)
# Prerequisite supplied by the completed shared adapter, not by wheel_layer:
# :python_runtime validates :source_python + :external_python against the plan,
# requirements, lock and provenance above, then exports their checked merged TAR.
# Stale-input diagnostics name tools/bazel/example-python-lock.
# Use the same base and normalization policy for every source layer.
normalize_layer(
    name = "native_files",
    src = _SOURCES["example-native"],
    base = ":base",
    expected_platform = "linux/amd64",
    tars = [_SOURCES["example-native"]],
)
normalize_layer(
    name = "library_files",
    src = _SOURCES["libexample1"],
    base = ":base",
    expected_platform = "linux/amd64",
    tars = [_SOURCES["libexample1"]],
)
_NORMALIZED_SOURCES = [":native_files", ":library_files"]
filegroup(name = "source_normalization", srcs = [":native_files"], output_group = "normalization")
installed_packages(
    name = "package_status",
    base = ":base",
    architecture = "amd64",
    apt_receipt = ":apt_selection",
    normalization_receipt = ":source_normalization",
    controls = [label + ":control" for label in _PACKAGES.values()],
    source_spec = "source_paths.json",
    sources = _SOURCES,
    owner_metadata = ["@example_native//:runtime_packages.json", "@example_library//:runtime_packages.json"],
    source_modules = {
        "example-native": "@example_source_modules//:example-native.MODULE.bazel",
        "example-library": "@example_source_modules//:example-library.MODULE.bazel",
    },
)
filegroup(name = "package_record", srcs = [":package_status"], output_group = "metadata")
tar(
    name = "state",
    srcs = [":package_status", ":package_record"],
    mtree = [
        "./var type=dir uid=0 gid=0 mode=0755 time=0",
        "./var/lib type=dir uid=0 gid=0 mode=0755 time=0",
        "./var/lib/dpkg type=dir uid=0 gid=0 mode=0755 time=0",
        "./var/lib/dpkg/status type=file uid=0 gid=0 mode=0644 time=0 content=$(location :package_status)",
        "./usr type=dir uid=0 gid=0 mode=0755 time=0",
        "./usr/share type=dir uid=0 gid=0 mode=0755 time=0",
        "./usr/share/sonic type=dir uid=0 gid=0 mode=0755 time=0",
        "./usr/share/sonic/packages.json type=file uid=0 gid=0 mode=0644 time=0 content=$(location :package_record)",
    ],
)
tar(
    name = "config",
    srcs = ["config.json"],
    mtree = [
        "./etc type=dir uid=0 gid=0 mode=0755 time=0",
        "./etc/example type=dir uid=0 gid=0 mode=0755 time=0",
        "./etc/example/config.json type=file uid=0 gid=0 mode=0644 time=0 content=$(location config.json)",
        "./var type=dir uid=0 gid=0 mode=0755 time=0",
        "./var/lib type=dir uid=0 gid=0 mode=0755 time=0",
        "./var/lib/example type=dir uid={} gid={} mode=0750 time=0".format(_UID, _GID),
    ],
)
oci_image(
    name = "content",
    base = ":base",
    tars = [":apt_files"] + _NORMALIZED_SOURCES + [":python_runtime", ":config", ":state"],
)
account_layer(
    name = "accounts",
    base = ":content",
    architecture = "amd64",
    users = [{"username": "example", "password": "x", "uid": _UID, "gid": _GID, "home": "/var/lib/example", "shell": "/usr/sbin/nologin"}],
    groups = [{"name": "example", "password": "x", "gid": _GID}],
)
oci_image(
    name = "runtime",
    base = ":content",
    tars = [":accounts"],
    user = "{}:{}".format(_UID, _GID),
    workdir = "/var/lib/example",
    env = {"EXAMPLE_CONFIG": "/etc/example/config.json"},
    entrypoint = ["/usr/local/bin/example-service"],
)
debug_symbols_layer(name = "symbols", image = ":runtime")
oci_image(name = "debug", base = ":runtime", tars = [":symbols"])
oci_load(name = "load", image = ":runtime", repo_tags = ["docker-example:verify"])
oci_load(name = "debug_load", image = ":debug", repo_tags = ["docker-example-debug:verify"])
```

source_paths may be schema-1 empty packages only when producers enforce required_paths. Add image-specific requirements only. flatten deduplicates package directories while selection binds origins. Both source normalize_layer calls share base/default aliases/ownership/modes. installed_packages reads original producer TARs for authoritative labels/version/payload and applies the common normalization policy; final content installs normalized TARs. Do not substitute private wrapper labels for original sources. Share a receipt only for identical policies; different policies need staged checks/intermediate OCI. normalize_layer retains producer edges for symbols. Build native/library normalization and receipt first, inspect aliases/owners/modes, then status. Regenerate after base/policy/source changes. Configuration comes from original/template; account rules verify example UID/GID conflicts.

The image owner maintains the executable updater named by stale diagnostics:

```sh
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
bazel_bin=${BAZEL:-bazel}
"$bazel_bin" build //dockers/docker-example:python_plan
plan=$(realpath bazel-bin/dockers/docker-example/python_plan.plan.json)
owner="$PWD/dockers/docker-example/python"
"$bazel_bin" run @sonic_build_infra//python:runtime_lock -- update \
  --plan "$plan" --requirements "$owner/requirements.in" \
  --lock "$owner/requirements_lock.txt" --inputs "$owner/lock-inputs.json" \
  --uv "${UV:?set UV to the fixed uv executable}"
```

Set executable permission and verified UV path; BAZEL may be a common wrapper. Updates are separate from assembly. The adapter's mandatory check must verify exact source/external installed sets, source metadata, locked versions, transitive requirements, target markers/extras and lock freshness before emitting `:python_runtime`. Preserve wheel `.dist-info`, entry points and resources; reject missing dependencies or source identities replaced by external wheels. Debug here adds source symbols. Required GDB/system symbols/tools need locked debug sets selected against exact runtime, state checks and ELF pairing. Preserve DebugSymbolsInfo/explicit interfaces through wrappers.

## 8. Real installation example

configured_debian/rootfs is a complete configured producer TAR; declared_tools/bwrap is a full exec closure. Verify actual producers and convert OCI first if needed. Import common example_install_runtime/apt_inputs. Redis and dependencies use the native execution architecture.

```starlark
load("@rules_distroless//apt:defs.bzl", "apt_install")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_load")
load("@example_apt_inputs//:apt_inputs.bzl", "APT_INPUTS")
apt_install(
    name = "configured_rootfs",
    base = "@configured_debian//:rootfs",
    packages = [label + "/amd64:deb" for label in APT_INPUTS["example_install_runtime"]["amd64"].values()],
    architecture = "amd64",
    bwrap = "@declared_tools//:bwrap",
    execution_environment = "docker.io/library/debian:trixie-20260918@sha256:9cc080028c43b27d2074d63a5f9caf7166d731494965616c1a6d2827a004585c",
)
filegroup(name = "installation_record", srcs = [":configured_rootfs"], output_group = "receipt")
oci_image(
    name = "installed_image",
    tars = [":configured_rootfs"],
    os = "linux",
    architecture = "amd64",
    entrypoint = ["/usr/bin/redis-server"],
)
oci_load(name = "installed_load", image = ":installed_image", repo_tags = ["installed-example:verify"])
```

### Execute in the actual install environment

Example requires native AMD64 Linux, root and the pinned Debian digest. Preflight BAZEL_BINARY; select task cache directories. Build infra kernel_runtime and locate its complete tree through cquery/execution_root as REPOSITORY_TOOLS. It supplies GNU tar/xz/loaders/libraries for repository extraction, which happens before actions; bwrap alone cannot supply that stage. Docker hosts execution; rule-internal bubblewrap isolates package scripts:

```sh
WORKER_IMAGE='docker.io/library/debian:trixie-20260918@sha256:9cc080028c43b27d2074d63a5f9caf7166d731494965616c1a6d2827a004585c'
: "${BAZEL_BINARY:?set the pinned native Bazel executable}"
: "${BAZEL_CACHE:?set the task cache directory}"
: "${REPOSITORY_TOOLS:?set the pinned native kernel_runtime tree}"
test "$(uname -m)" = x86_64
mkdir -p "$BAZEL_CACHE"
docker run --rm --platform linux/amd64 --user 0:0 \
  --cap-add SYS_ADMIN --cap-add NET_ADMIN \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  --mount "type=bind,src=$PWD,dst=/workspace" \
  --mount "type=bind,src=$BAZEL_BINARY,dst=/usr/local/bin/bazel,readonly" \
  --mount "type=bind,src=$BAZEL_CACHE,dst=/bazel-cache" \
  --mount "type=bind,src=$REPOSITORY_TOOLS,dst=$REPOSITORY_TOOLS,readonly" \
  --workdir /workspace "$WORKER_IMAGE" \
  bazel --output_user_root=/bazel-cache/user-root build \
    "--repo_env=PATH=$REPOSITORY_TOOLS/bin:/usr/local/bin:/usr/bin:/bin" \
    --@rules_python//python/config_settings:bootstrap_impl=script \
    //dockers/docker-example/runtime:installation_record \
    //dockers/docker-example/runtime:installed_image
```

Python uses the declared bootstrap runtime. Mount REPOSITORY_TOOLS at the same absolute path, provide writable isolated output_user_root and preserve other project rc. bwrap comes from BUILD, not container apt installation. Base rootfs supplies locked dpkg/APT/script tools; inputs cover missing dependencies. Verify exec architecture/closure. ARM64 uses native workers/matching digest/platform/locked sets. Preserve container identity, permissions and receipt separately. Use full outputs only after dependency/audit checks. CI reuses the same environment declaration.

Verify actual DEB labels. Check redis version/account/configuration/required directories, replacing with real package behavior. Digest strings alone do not prove execution environments. Source hashes stay locked and outputs preserve real status. For later source/Python layers, form OCI from full rootfs, derive new APT selection against its status and feed that base/selection to step-7 installed_packages, then add source/Python/state with final config. Preserve replacement-root semantics.

## 9. Build, load and accept

Build separate inputs first and fix failures at their boundary:

```sh
bazel build //dockers/docker-example/runtime:source_normalization \
  //dockers/docker-example/runtime:apt_selection \
  //dockers/docker-example/runtime:python_runtime \
  //dockers/docker-example/runtime:package_record \
  //dockers/docker-example/runtime:accounts.receipt
bazel build //dockers/docker-example/runtime:runtime \
  //dockers/docker-example/runtime:debug
bazel build //dockers/docker-example/runtime:load --output_groups=+tarball
bazel run //dockers/docker-example/runtime:load
```

Read OCI index/manifest digest and verify config platform/user/environment/entry/workdir. Docker image ID differs from OCI manifest digest; associate by actual diff IDs/effective config and record both. Run the example's real version/self-checks with declared inspection tools:

```sh
docker image inspect docker-example:verify
docker run --rm --network=none --read-only docker-example:verify --self-test
docker run --rm --network=none --read-only --entrypoint /usr/bin/exampled \
  docker-example:verify --version
```

Docker is external validation, not regular actions. Provide required writes/mounts/devices/network/privileges by original service contract; example isolation flags are not universal. Real installation builds record/image/load and checks commands/scripts/triggers/state. Rebuild with identical configuration and compare production locks/provenance for read-only behavior.

Apply [OCI acceptance](review-port.md#oci-specific-acceptance) and contract-derived missing-dependency/stale/architecture/conflict/wrong-receipt cases, then run the [Make equivalence check](make-bazel-equivalence.md) on the runtime and debug archives. Distinguish component/install/assembly/load/start/equivalence/full-machine storage/boot results.

## 10. Failure ownership

| First error | Inspect | Recovery |
| --- | --- | --- |
| Missing target/API mismatch | MODULE/registry/source/public API | Correct identity/arguments and rerun step |
| Stale runtime lock/conflict | Metadata/entries/platform/extras/provenance | Owner update, diff review, checked rebuild |
| Missing APT/relations | Common requests/lock/base state/closure | Preserve old identities, add correct requests/sets, update |
| Metadata/TAR mismatch | Producer targets/recipes/contents | Fix producer, regenerate both |
| Overwrite/account conflict | Actual prior OCI/policy/UID/GID/order | Fix actions/order and receipts |
| Loader/library failure | Architecture/loader/NEEDED/RPATH | Correct target closure and installed execution |
| Script/trigger failure | Branch/rootfs/tools/permissions/architecture | Fix installer inputs/environment, not fabricated state |
| Startup failure | Config/user/options/service conditions | Restore required inputs and rerun |

For SONiC storage, pass actual OCI to docker_overlay2_store. Docker save archives, overlay2-store TARs and full rootfs TARs are distinct interfaces selected by the next consumer.
