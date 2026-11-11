# APT sources, locking and three consumption interfaces

Read the [shared contract](common-contract.md). Use for Debian files, compilation libraries or build tools. Infra supplies fixed snapshots/shared collections; integrated rules_distroless downloads/parses precompiled DEBs and exports C/C++ targets. Here source means APT repository. Dependencies needing apt-source modifications/recompilation use [source modules](register-bazel-module.md).

## Distinguish the three roles

| Role | Export | Configuration/consumption |
| --- | --- | --- |
| Docker/OCI/rootfs | data/control archives and metadata | Target architecture, assembly/install rules |
| Compilation/linking | Library CcInfo, headers/include/link contexts | Target deps |
| Host tools | Executable/launcher/FilesToRunProvider/runfiles | Exec tools or executable=True,cfg=exec |

Share sources/package identities while exposing separate interfaces. Reuse DEBs where suitable without confusing target libraries, exec runtime and image payload/CcInfo. See [assembly](#pass-package-files-to-docker-and-rootfs), [libraries](#1-reuse-shared-apt-collections), [tools](#consume-host-tools). Follow [tool priority](../SKILL.md#use-native-bazel-actions-and-declared-tools): compatible maintained BCR rulesets/toolchains, then existing project/shared tools, then pinned sources. Record fallback reasons; existing pinned DEB tools remain allowed under this order. Keep platform/role declarations separate.

## Global source configuration

One editable infra apt/sources.json declares ordinary/security sources, fixed snapshots, suites/components/architectures. Shared extensions read it; components request packages/sets/suites without copying URLs. Independent roots reuse the same baseline; alternate root baselines explicitly select one configuration across the graph. Conflicting same-suite sources fail.

Example showing the Trixie subset of the shared baseline. The selected infra
revision's apt/sources.json owns suites, architectures and snapshot identity.
It also supplies Bookworm and Trixie armhf where configured. Components reuse
that shared configuration rather than copying this subset.

For new or changed download wiring, follow the [download policy](../SKILL.md#use-github-or-the-approved-private-mirror-for-downloads):
use the approved private mirror. Replace the placeholders below with its actual
ordinary/security endpoints; their paths are mirror-specific. Keep private
addresses and credentials outside public source. Existing infra snapshot URLs
identify inherited inputs and provenance; they do not approve new public-host
downloads. A transport change requires the authorized source-change procedure
and lock review, preserving package bytes and hashes.

Snapshot provenance for this example is Debian `20260727T143429Z` and
Debian security `20260726T121236Z`.

```json
{
  "version": 1,
  "sources": [
    {
      "uris": ["https://APPROVED_PRIVATE_MIRROR/DEBIAN_SNAPSHOT_PATH"],
      "suites": ["trixie", "trixie-updates"],
      "components": ["main"],
      "architectures": ["amd64", "arm64"]
    },
    {
      "uris": ["https://APPROVED_PRIVATE_MIRROR/DEBIAN_SECURITY_SNAPSHOT_PATH"],
      "suites": ["trixie-security"],
      "components": ["main"],
      "architectures": ["amd64", "arm64"]
    }
  ]
}
```

Snapshot/distribution/architectures are illustrative baseline inputs. Resolver records Release/Packages/needed Contents identities/checksums. Infra registers apt.sources_file for its default; root alternatives use the same extension override:

```starlark
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.sources_file(file = "//apt:alternate-sources.json", override = True)
```

Bind alternate production locks/requests and all import_lock.sources to this selection. Normal consumption checks locked source identity. Choose once at root; components keep requests. Editing one source file still requires explicit affected-lock updates. Lock URLs/digests are generated committed resolution results; source edits do not silently rewrite old versions/URLs. Obtain authorization before source/existing-package changes and review identities/hashes afterward.

## One APT lock and multiple collections

| Collection | Locked content | Consumption |
| --- | --- | --- |
| Runtime | Source/roots/target architecture/direct-transitive versions/DEB URLs/SHA256/edges | import_lock data/control, apt_inputs labels |
| Development | Above plus export file maps/index identity | Public CcInfo deps |
| Host tools | Exec architecture and interpreter/loader/library/data/subtool closure | Public complete executable closure |

Infra apt/apt.lock.json owns one production lock. Docker/rootfs/development/tool sets reference package identities stored once by suite/name/architecture/version. Do not split by role/component/repository. Components own requests; the unified updater aggregates. Track sources/lock/requests/provenance together. Snapshot identity and resolved selection are distinct; MODULE locks/extension caches do not replace production locks. Normal builds read; update resolves/writes. Library read-only export retains header/file mapping; payload-only imports serve assembly. See [APT locking](dependency-locking.md#apt).

## Pass package files to Docker and rootfs

Root MODULE selects shared locked sets/repositories/mappings:

```starlark
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.import_lock(
    lock = "@sonic_build_infra//apt:apt.lock.json",
    sources = "@sonic_build_infra//apt:sources.json",
    requests = "@sonic_build_infra//apt:requests.json",
    dependency_sets = ["orchagent_debian", "orchagent_debug_debian"],
)
use_repo(apt, "orchagent_debian", "orchagent_debug_debian")

apt_inputs = use_repo_rule("@sonic_build_infra//apt:inputs_repository.bzl", "apt_inputs")
apt_inputs(
    name = "orchagent_apt_inputs",
    lock = "@sonic_build_infra//apt:apt.lock.json",
)
```

Actual targets resemble @orchagent_debian//tcpdump:data/control; verify with query. data is payload, control supplies identity/dependencies/install behavior. Extract once and reuse. OCI apt_layer consumes OCI directory bases and produces TARs for oci_image. Follow [base/selection/receipt checks](oci.md#5-choose-installation-branch-and-implement-behavior). Rootfs consumes the same public data/control through its own installation interface for modes/accounts/services/state, not as an apt_layer base tree. Locks/roots cover full runtime closure.

Choose extraction versus real installation under [OCI](oci.md#5-choose-installation-branch-and-implement-behavior). Incremental apt_layer produces TAR/selection from OCI base and data/control. For scripts/triggers, apt_install takes configured rootfs TAR, original locked DEBs, native bubblewrap and fixed execution environment, producing complete rootfs TAR/installer receipt. Distinguish filesystem semantics/receipt schemas and validate actual effects.

## Consume host tools

When the BCR-first check selects shared APT tools, use public infra executables such as build_tools:bison. Producers lock exec package identity, assemble runtime from data and expose launcher/loader/libraries/interpreter/templates/subtools. Follow [tool recipes](tool-recipes.md#bison-and-flex) and [hermetic actions](hermetic-tools.md#minimal-tool-action-rule):

```starlark
genrule(
    name = "parser_source",
    srcs = ["parser.y"],
    outs = ["parser.c"],
    tools = [
        "@sonic_build_infra//tools/build_tools:bison",
        "@sonic_build_infra//tools/build_tools:m4",
    ],
    cmd = 'M4="$(location @sonic_build_infra//tools/build_tools:m4)" ' +
          '"$(location @sonic_build_infra//tools/build_tools:bison)" -o "$@" "$(location parser.y)"',
)
```

Use exec configuration without hardcoded CPU/compiler paths. Platforms independently choose tools/libraries. Tool closure stays out of target images; target libraries do not come from host installations.

## Mandatory consumption contract

Original Debian system development libraries must use exported APT library deps, including optional libraries such as tcmalloc under original feature controls. Producers own headers/contexts/runtime closure. For multi-library packages consume actual per-library targets; for headers only use public header-only exports. Query first. Consumers must not unpack/import .so, reconstruct/filter CcInfo or replace target deps with handwritten -l/-L. Preserve necessary native order/state flags and explicitly declare linked files through public targets. SONiC-built dependencies retain source identity; changed-source/patch/configuration dependencies use source modules. Determine actual origin first.

## Inputs and entry points

Read selected infra/rules_distroless/registry patches for sources/versions/checksums/labels/CPU support. Apply [fixed APT inputs](common-contract.md#configuration-and-dependencies); export/rule fixes or rebuilds do not authorize upgrades.

Trace actual Make injection: source-built SONiC dependencies retain public producers/patches/ABI, regardless of same-named system packages. Inspect real headers/include categories/static-shared libraries/providers. Existing modules/packages alone prove no interface/closure.

Inspect pinned original DEB headers/libraries/development links/pkg-config, follow metapackages to actual owners and list required development/runtime packages/architectures. -l is a search request; effective flags/search paths/files determine static/shared choice. -dev names do not guarantee .so. If Make rebuilds/replaces installed libraries, trace final inputs; raw DEB listings prove raw contents only. Verify actual exports/link actions.

## 1. Reuse shared APT collections

Declare verified infra/rules_distroless modules under registry/version guidance. The common extension reads unique sources/lock and libraries=True exports development sets:

```starlark
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
use_repo(apt, "trixie")
```

Extension declarations aggregate across modules; use_repo exposes actual repositories. Reuse existing collections directly.

```starlark
load("@rules_cc//cc:cc_library.bzl", "cc_library")

cc_library(
    name = "example",
    srcs = ["example.cc"],
    deps = [
        "@trixie//libhiredis-dev:libhiredis",
        "@trixie//libzmq3-dev:libzmq3",
        "@trixie//uuid-dev:uuid",
    ],
)
```

Generated cc_deb_library/so_library interfaces provide applicable CcInfo. Consume them directly, preserving explicit dependencies. Producers export complete header-only compilation context without unrelated links and handle roots/generated/platform headers centrally.

Use package aggregates only when every link input belongs to the original contract. For mutually exclusive implementations, run managed pkgconf against target .pc closure, map actual -lNAME to owning libNAME_cc targets, aggregate component deps and retain other flags. Per-library interfaces directly link one library plus headers/runtime link inputs; .pc Requires does not automatically become direct linking. libNAME_shared supports original explicit-file contracts.

For gRPC secure/unsecure variants, aggregates may mix implementations. Inspect pinned pkgconf --libs grpc++, select grpc++/gRPC/Abseil per-library targets, execute RPC and inspect DT_NEEDED/variant. Link success alone is insufficient.

## 2. Add required development packages

Check infra apt/requests.json trixie first. Extend shared requests/lock with new packages/necessary closure while retaining old identities. Validate exports then consumers. Component-specific sets may use the same extension:

```starlark
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.install(
    dependency_set = "example_deps",
    packages = ["libhiredis-dev", "libzmq3-dev", "uuid-dev"],
    suites = ["trixie", "trixie-updates", "trixie-security"],
)
use_repo(apt, "example_deps")
```

Aggregate matching requests in infra and run unified update; normal consumption rejects stale requests. Query actual labels such as libhiredis. Choose noncolliding responsibility-based set names. Shared sources supply update preparation; components do not add URLs. Derive suites/CPU/snapshot/constraints from environment/baseline; use actual extension constraint syntax and verify results. Commit production locks, not historical snapshot assumptions.

For new packages/architectures follow [locking](dependency-locking.md#apt). Source changes require authorization. Update affected shared sets and consumers; import runtime with import_lock and generate labels through apt_inputs, without a second MODULE/version list. Development sets retain locked export inputs/CcInfo.

## 3. Verify exported targets and links

Package and target names may differ:

```bash
bazel query '@trixie//libhiredis-dev:*'
bazel cquery 'deps(@trixie//libhiredis-dev:libhiredis)'
```

Use actual selected exports, including per-library libNAME_cc/shared targets where supported. Historical aggregates do not authorize consumer-side filtering. Check platform/headers/pkg-config/static-shared selection/transitives through actual compile/link/target execution. Architecture support needs packages, toolchains and results.

## 4. Source build and packaging boundaries

| Need | Route |
| --- | --- |
| Reuse precompiled Debian libraries | Locked apt.install/exported library targets |
| Modify sources/patch/configuration | Pinned source BUILD/patch/registered module |
| Add Debian files to OCI | Package data/shared APT assembly/runtime checks |
| Explicit final component DEB | [sonic_deb](build-deb-with-sonic-deb.md); default OCI TAR |

Maintain linking, installed shared libraries and Debian Depends separately. Library targets solve compile/link inputs; images explicitly include runtime data. Payload assembly and maintainer-script execution require distinct validation.

## 5. Self-contained APT input wiring

After importing orchagent_debian/apt_inputs, declare apt-example/BUILD archives. The AMD64 set is illustrative; actual scope/platform comes from analysis. Pair data install inputs and control state inputs:

```starlark
load("@orchagent_apt_inputs//:apt_inputs.bzl", "APT_INPUTS")
load("@rules_distroless//distroless:defs.bzl", "flatten")

_PACKAGES = APT_INPUTS["orchagent_debian"]["amd64"]
filegroup(
    name = "debian_controls",
    srcs = [label + ":control" for label in _PACKAGES.values()],
)
flatten(
    name = "debian_payload",
    tars = [label + ":data" for label in _PACKAGES.values()],
    deduplicate = True,
)
```

```bash
bazel build //apt-example:debian_payload //apt-example:debian_controls
bazel cquery --output=files //apt-example:debian_payload
```

debian_payload exports files only. OCI performs [base selection/inheritance checks](oci.md#7-incremental-assembly-template); rootfs uses [full wiring](image-assembly-examples.md#rootfs-and-squashfs) and control checks. Scripted packages need real installation. Compare data/control identity/lock versions/full set/architecture before connecting downstream.
