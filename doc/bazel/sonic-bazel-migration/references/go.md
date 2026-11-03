# Migrate Go and CGo programs

Read the [shared contract](common-contract.md). Follow analysis, prerequisite checks, modules, dependencies, targets, applicable branches, installation and acceptance, handing each step's output to the next. [Go locking](dependency-locking.md#go-modules) owns lock formats, updates and delivery.

## 1. Derive effective inputs from the original build

Read Make analysis and follow the patched Go entry. Source each fact below and mark absent inputs inapplicable. Original values are component-specific; do not substitute example versions.

| Input | Establish |
| --- | --- |
| Modules/programs | go.mod module, go.work members, entry packages, installed programs, default tests |
| SDK | Effective original Go version, go/toolchain directives, container SDK and automatic switching |
| Source selection | GOOS/GOARCH, filename suffixes, tags, CGo conditions, generation, fixed options |
| Dependency origins | go.mod/sum, replace/exclude, vendor/modules.txt, vendor patches, source-component identity |
| Version/resources | Full -ldflags -X symbols and value origins, go:embed, runtime/test data |
| Generation/native libraries | Generators/plugins/versions, inputs/outputs, C/C++ headers/libraries, expanded pkg-config |
| Installation/runtime | Paths, configuration/services/modes, loader/libraries, version and minimal functional checks |

Completion: every installed program has an entry, effective sources/options, dependency identities and installation path. Identify generation prerequisites first; native Go dependency maintenance also needs the original generation prerequisites.

## 2. Check prerequisites

Run [preflight](infrastructure.md#build-entry-and-cache-preflight) for Bazel, configuration and platforms. Check pinned rules_go, Gazelle and infra:

- rules_go supplies native rules, //go SDK runner, required settings and CGo support.
- Gazelle supplies go_deps.from_file, zip_lock, planned exports and required override APIs.
- Selected infra sources contain go/lock.py and documentation; project wrappers select the same pinned infra.
- Installation infra supplies sonic_deploy_tar and required runtime metadata APIs.

Use the common SDK runner for native Go maintenance and go/lock.py for ZIP lock update/check. Then execute the commands below. Completion: versions, repo_name, actual APIs, execution SDK and target/exec platforms are known.

## 3. Initialize the independent module

Complete minimal pure-Go MODULE example. Choose compatible rules/SDK from effective step-1 inputs under version policy. This example consistently uses io_bazel_rules_go and bazel_gazelle aliases.

```starlark
module(name = "example_service")
bazel_dep(name = "rules_go", version = "0.64.1-sonic.1", repo_name = "io_bazel_rules_go")
bazel_dep(name = "gazelle", version = "0.51.3.sonic.1", repo_name = "bazel_gazelle")
go_sdk = use_extension("@io_bazel_rules_go//go:extensions.bzl", "go_sdk")
go_sdk.download(version = "1.26.6")
go_deps = use_extension("@bazel_gazelle//:extensions.bzl", "go_deps")
go_deps.from_file(go_mod = "//:go.mod")
go_deps.zip_lock(file = "//:go.zip.sums.json")
use_repo(go_deps, go_zip_lock_plan = "bazel_gazelle_go_repository_config")
```

For go.work, replace from_file's go_mod with go_work="//:go.work" rather than specifying both. Members/local replace refer to real declared sources. Preserve source components' native targets instead of copying sources or downloading identically named packages. Reuse an existing root extension and check independent/root graphs and SDKs separately.

Retain original go.mod/go.sum. Initialize an absent ZIP lock to {} only once; update from existing locks. Prepare an empty go.sum only if originally absent and there are no external dependencies. Export real root inputs and register Gazelle:

```starlark
load("@bazel_gazelle//:def.bzl", "gazelle")
# gazelle:prefix example.invalid/service
exports_files(["go.mod", "go.sum", "go.zip.sums.json"])
gazelle(name = "gazelle")
```

Completion: independent MODULE, SDK, dependency entry, ZIP lock and Gazelle are declared; import used extension repositories with actual Bazel-provided use_repo names.

## 4. Update dependencies, generate and review declarations

From the owning module root, use rules_go's runner and its Bazel-selected host-compatible SDK with GOTOOLCHAIN=local. Confirm the version before changes. SONIC_GO_LOCK_UPDATE=1 is for explicit updates only; normal builds consume locks:

```sh
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- version
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- mod tidy
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- mod verify
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- list -m all
```

For new dependencies or approved targeted changes, run get MODULE_PATH@VERSION through the same runner before tidy, choosing original or confirmed compatible versions. Maintain modules in their directories, or use runner -C for subdirectories. If native Go cannot see generated Bazel packages, resolve generation/dependency-maintenance prerequisites first. Do not let tidy on incomplete sources delete required dependencies.

Actually update/check the ZIP lock under [locking steps](dependency-locking.md#go-dependency-update-steps), then generate BUILD. Project wrappers use the same tool; component roots may invoke it directly:

```sh
python3 "$INFRA_SOURCE/go/lock.py" --workspace "$PWD" --bazel "$BAZEL" \
  --plan '@go_zip_lock_plan//:zip-lock.json'
python3 "$INFRA_SOURCE/go/lock.py" --workspace "$PWD" --bazel "$BAZEL" \
  --plan '@go_zip_lock_plan//:zip-lock.json' --check
bazel run //:gazelle
bazel mod tidy
```

INFRA_SOURCE and BAZEL identify selected sources/entry points. Use one configuration/wrapper for registry/overrides across calls. Runner-requested bazel mod tidy requires reviewing repository imports and does not update ZIP locks.

Review generated programs/tests, complete sources, importpath, deps/embed, visibility, conditional sources, resources and generated targets. Generated declarations do not define product features. After corrections rerun Gazelle to ensure required directives/attributes remain. Map imports to source/proto producers through selected resolve/gazelle_override APIs and verify final deps use one producer.

### Vendor, replace and patch branches

| Original input | Bazel action |
| --- | --- |
| Ordinary module | Import graph with from_file; lock native content and ZIP SHA256 |
| Patched vendor | Identify original module/version; apply patch to the actual fetched dependency and verify contents |
| Local replace/workspace member | Preserve source ownership, verify go_deps behavior/public mapping and root/independent consumption |
| Registered source component | Reuse public Go targets; verify Gazelle mapping and final root selection |

Declare patches in the same go_deps extension:

```starlark
go_deps.module_override(
    path = "example.org/dependency",
    patches = ["//patches:dependency.patch"],
    patch_strip = 1,
)
```

Paths, patches and strip values come from actual inputs. In this Gazelle version patches apply after generation; if files/imports change, update BUILD too or fix producer ordering. Original checksums pin upstream inputs; patches are additional declared inputs. Inspect external sources and compile actions to prove vendor fixes reach the binary; retained vendor files alone do not prove consumption.

## 5. Declare programs, libraries and original tests

Example import root example.invalid/service: root service.go uses package service and exports Version; cmd/main.go uses package main and imports it. List original sources explicitly.

```starlark
load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library", "go_test")
go_library(
    name = "service_lib",
    srcs = ["service.go"],
    importpath = "example.invalid/service",
    visibility = ["//visibility:public"],
)
go_binary(
    name = "service",
    srcs = ["cmd/main.go"],
    deps = [":service_lib"],
    x_defs = {"example.invalid/service.Version": "1.2.3"},
)
go_test(
    name = "service_test",
    srcs = ["service_test.go"],
    embed = [":service_lib"],
)
```

Version must be a linker-settable string. Preserve full symbols/value sources from -X. Example constants only show syntax; derive component versions/commits and build-time reproducibility from the original contract. Use verified public external labels.

### Tags, resources and test data

- Platforms select GOOS/GOARCH and C/C++ toolchains; components do not select compiler paths/toolchains.
- The selected //go/config:tags accepts build tags. For an actual feature_a contract:

```sh
bazel run //:gazelle -- -build_tags=feature_a
bazel build //:service --@io_bazel_rules_go//go/config:tags=feature_a
bazel test //:service_test --@io_bazel_rules_go//go/config:tags=feature_a
```

- Keep fixed tags fixed and connect configurable tags to project configuration. Check suffixes, build constraints and tag combinations. Review Gazelle build_tags/select output.
- Add go:embed assets/default.json to its library embedsrcs. Put ordinary runtime/test files in data and locate through runfiles. Install files separately. Build tags and target tags have distinct purposes.
- Preserve internal/external package tests, data, working-directory contracts and default test selection.

## 6. CGo branches

For required CGo, also apply [C/C++](native-cc.md) and [tools](hermetic-tools.md). Map original #cgo headers/macros/pkg-config/link requests to public CcInfo. Express C, C++, preprocessor and link options through copts, cxxopts, cppopts and clinkopts. Libraries use cdeps, without incidental host pkg-config/CPATH/LIBRARY_PATH inputs.

native/BUILD.bazel example: api.go calls answer() declared in native.h; native.c returns 42:

```starlark
load("@io_bazel_rules_go//go:def.bzl", "go_library", "go_test")
load("@rules_cc//cc:cc_library.bzl", "cc_library")
cc_library(name = "native", srcs = ["native.c"], hdrs = ["native.h"])
go_library(
    name = "native_go",
    srcs = ["api.go"],
    importpath = "example.invalid/service/native",
    cgo = True,
    cdeps = [":native"],
    visibility = ["//visibility:public"],
)
go_test(name = "native_test", srcs = ["api_test.go"], embed = [":native_go"])
```

api.go imports C with the preceding header comment and exports Answer() as int(C.answer()); test Answer()==42. Compile native.c through :native, not duplicated in Go srcs. Declare compatible rules_cc. cgo=True permits inputs but still check effective CGo configuration. Use a suitable platform with pure=false and verify CGo/C/link actions in aquery. For cross builds, check target toolchain resolution, architecture and native libraries; generators use exec configuration. Tests and installed copies must call C. Include shared libraries/loader in installation closure.

## 7. Generated code branches

Determine whether the original uses committed generated sources or requires generation; preserve that choice/version. Declare inputs, exec tools/plugins, outputs and runtimes under [generation](code-generation.md).

- Build project generators with go_binary and invoke through tools or executable/cfg=exec. Generated .go targets enter library srcs; lock generator dependencies separately. For a generator accepting -in/-out:

```starlark
load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library")
go_binary(name = "schema_generator", srcs = ["tools/schema_gen/main.go"])
genrule(
    name = "schema_generated",
    srcs = ["schema.json"],
    outs = ["generated/schema.go"],
    tools = [":schema_generator"],
    cmd = '"$(location :schema_generator)" -in "$(location schema.json)" -out "$@"',
)
go_library(
    name = "schema",
    srcs = [":schema_generated"],
    importpath = "example.invalid/service/schema",
)
```

  tools selects exec configuration. Replace CLI, source list and output with the actual contract.
- protobuf uses matching proto_library and rules_go rules. Register compatible protobuf, plugin and Go runtime versions/mappings first:

```starlark
load("@protobuf//bazel:proto_library.bzl", "proto_library")
load("@io_bazel_rules_go//proto:def.bzl", "go_proto_library")
proto_library(name = "message_proto", srcs = ["message.proto"])
go_proto_library(
    name = "message_go",
    proto = ":message_proto",
    importpath = "example.invalid/service/api",
)
```

Match go_package/importpath and add :message_go to consumer deps. Reuse independent proto modules to avoid duplicate producers for one importpath. ProtoInfo uses its protobuf module's protoc toolchain; verify forwarded options and generator version. Select compatible versions separately for this route versus direct APT protoc/native-C++ runtime generation. A rule passing --retain_options needs a protoc supporting it; overriding with old APT protoc fails generation. For the newer original Go gRPC plugin:

```starlark
load("@io_bazel_rules_go//proto:def.bzl", "go_grpc_library")
go_grpc_library(
    name = "service_go",
    proto = ":service_proto",
    importpath = "example.invalid/service/rpc",
)
```

:service_proto declares services. The macro defaults to go_proto/go_grpc_v2 compilers. Check original plugin/runtime compatibility; for older semantics choose corresponding compilers and preserve versions/runtime. Acceptance includes serialization round trips and service calls.
- SWIG uses Go templates and go/cxx/hdr output groups. Go outputs enter native targets; wrappers/headers enter CGo inputs. For Thrift, declare Go package, complete outputs and runtime, then native compilation. Call actual bindings/protocols after generation.

## 8. Installation and acceptance

Map original program paths with [sonic_deploy_tar](install-interfaces.md#2-native-programs-and-deb-intermediate-layers), exporting runtime, matching symbols and package metadata. Configuration, resources, services and dynamic libraries follow installation analysis. OCI/rootfs consume TARs directly. Check actual go_binary default files with cquery before passing a single ELF.

Run applicable original configurations under the authorized platform/feature matrix:

| Object | Command or observation |
| --- | --- |
| SDK/graph | Runner version/list -m all; root/independent actual Bazel and Go selections agree |
| Locks | Actual update/check, native inputs/ZIP digests preserved across normal builds; missing entries fail |
| Native targets | Build service and test service_test with identical configuration |
| Options/features | -X version output, tags/program selection, CGo tests call real C |
| Resources/generation | Embedded/runfiles data, action inputs/plugins and actual binding/protocol calls |
| Installation | TAR paths/modes/architecture/dynamic closure and installed execution |
| Cross-module/platform | Independent/root builds; separate exec, target ELF and native-runtime evidence |

Locate failures at prerequisite, graph, generation, compile, link or installation boundaries and preserve first errors. Fix the owning layer and rerun affected checks. Completion requires evidence for every applicable check; report cross compilation and execution separately, using real build/runtime results.
