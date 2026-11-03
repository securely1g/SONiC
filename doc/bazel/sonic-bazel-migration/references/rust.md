# Migrate Rust programs and libraries

Read the [shared contract](common-contract.md). Proceed through original analysis, MODULE/SDK, locks, native targets, applicable branches, installation and consumer verification.

## 1. Original inputs

From Make analysis and patched Cargo.toml, Cargo.lock, workspace and build.rs, record crate names/types, edition, minimum/original Rust SDK, entries, complete modules, default/optional features, target conditions, proc-macros, generated inputs, compile environment, native libraries and installation. Track Cargo default features/product switches separately from the locked version graph.

## 2. MODULE, SDK and dependency graph

Use public rules_rs rules, re-exported from one managed rules_rust implementation. SDK 1.90.0/edition 2021 below are existing shared-module examples; choose from the component contract. Target triples come from the authorized platform matrix.

```starlark
bazel_dep(name = "rules_rs", version = "0.1.0")
rust = use_extension("@rules_rs//rs:rules_rust_reexported_extensions.bzl", "rust")
rust.toolchain(
    edition = "2021",
    versions = ["1.90.0"],
    extra_target_triples = ["aarch64-unknown-linux-gnu", "x86_64-unknown-linux-gnu"],
)
use_repo(rust, "rust_toolchains")
register_toolchains("@rust_toolchains//:all")
```

Reuse an existing shared crate module through bazel_dep and public targets such as @sonic_rust_deps//:serde. Obtain actual version/repo_name from handoff. Shared-trait producers and consumers use the same graph. For an independent Cargo graph:

```starlark
crate = use_extension("@rules_rs//rs:extensions.bzl", "crate")
crate.from_cargo(
    name = "service_crates",
    cargo_toml = "//:Cargo.toml",
    cargo_lock = "//:Cargo.lock",
    platform_triples = ["aarch64-unknown-linux-gnu", "x86_64-unknown-linux-gnu"],
    use_legacy_rules_rust_platforms = True,
)
use_repo(crate, crates = "service_crates")
```

Export Cargo.toml/Cargo.lock in root BUILD. from_cargo reads the same manifest/lock to generate public aliases. Query @crates//:* and consume actual aliases such as :serde; use generated versioned aliases when versions coexist.

Use infra's Rust SDK runner for [Cargo updates](dependency-locking.md#rust-crates). It obtains Cargo, rustc, rustdoc, standard libraries and executables from the selected toolchain, retains the caller workspace, explicitly sets RUSTC/RUSTDOC and avoids rustup switching:

```sh
bazel run @sonic_build_infra//rust:cargo -- --version
bazel run @sonic_build_infra//rust:cargo -- metadata --locked --format-version 1
```

After dependency changes, run update/metadata through the same entry, then --locked checks. Retain the original lock and synchronize native/shared manifests. Inspect origins, versions, features, build-dependencies and proc-macros. Normal Bazel builds read locks; explicit Cargo updates are separate. Check SDK, triples, Cargo graph, Bazel targets and patch identities agree.

## 3. Libraries, programs and original tests

Module-root example: src/lib.rs exports answer()->i32 returning 37 and tests it; src/main.rs calls service_lib::answer(). List the analyzed complete sources.

```starlark
load("@rules_rs//rs:rust_library.bzl", "rust_library")
load("@rules_rs//rs:rust_binary.bzl", "rust_binary")
load("@rules_rs//rs:rust_test.bzl", "rust_test")

rust_library(
    name = "service_lib",
    crate_name = "service_lib",
    crate_root = "src/lib.rs",
    srcs = ["src/lib.rs"],
    edition = "2021",
    visibility = ["//visibility:public"],
)
rust_binary(
    name = "service",
    crate_root = "src/main.rs",
    srcs = ["src/main.rs"],
    edition = "2021",
    deps = [":service_lib"],
)
rust_test(name = "unit_tests", crate = ":service_lib")
```

Distinguish hyphenated Cargo names from underscore imports. Use aliases rather than editing upstream for dependency naming. Put include_str!/include_bytes! inputs in compile_data; runtime/test data belongs in data with declared paths/runfiles.

## 4. Features, build.rs and proc-macros

### Product feature switches

rules_rs targets use crate_features. List fixed features directly; connect original switches through one bool_flag/config_setting to sources, dependencies, features and installation:

```starlark
load("@bazel_skylib//rules:common_settings.bzl", "bool_flag")
bool_flag(name = "with_stats", build_setting_default = False)
config_setting(name = "stats_on", flag_values = {":with_stats": "true"})

rust_library(
    name = "configured_lib",
    crate_name = "configured_lib",
    crate_root = "src/lib.rs",
    srcs = ["src/lib.rs"],
    edition = "2021",
    crate_features = select({":stats_on": ["stats"], "//conditions:default": []}),
)
```

crate_features sets compilation cfg; select matching optional dependencies in deps. Explicitly map Cargo defaults; Cargo.lock does not enable them. Shared manifests/from_cargo determine third-party feature union. Synchronize that graph before consumers to preserve trait identity.

### build.rs

Separate read files, generated files, environment and subprocesses, then use the dedicated rule:

```starlark
load("@rules_rs//rs:cargo_build_script.bzl", "cargo_build_script")
cargo_build_script(
    name = "build_script",
    srcs = ["build.rs"],
    crate_root = "build.rs",
    edition = "2021",
    version = "1.2.3",
    data = ["schema.txt"],
    build_script_env = {"SCHEMA": "$(execpath schema.txt)"},
)
rust_library(
    name = "generated_lib",
    crate_name = "generated_lib",
    crate_root = "src/generated_lib.rs",
    srcs = ["src/generated_lib.rs"],
    edition = "2021",
    deps = [":build_script"],
)
```

Here build.rs reads SCHEMA and writes schema.rs under OUT_DIR; source uses `include!(concat!(env!("OUT_DIR"), "/schema.rs"));`. version comes from the component. rustc_env configures script compilation; build_script_env configures execution. Declare tools and pass execpaths; script Rust dependencies use deps. cargo_build_script.link_deps carries Rust dependencies' Cargo links metadata. Compile target native code with cc_library and consume CcInfo through final Rust link_deps. Pass probe results/generated inputs through data and explicit environment. The rule forwards its generated directory to the crate. Replace downloads/host probing during migration with pinned inputs/controlled evidence; regular actions retain explicit generation/parameter logic only.

### proc-macros and native libraries

```starlark
load("@rules_rs//rs:rust_proc_macro.bzl", "rust_proc_macro")
load("@rules_cc//cc:cc_library.bzl", "cc_library")
rust_proc_macro(
    name = "derive_impl",
    crate_root = "derive/src/lib.rs",
    srcs = ["derive/src/lib.rs"],
    edition = "2021",
)
cc_library(name = "native", srcs = ["native.c"], hdrs = ["native.h"])
rust_library(
    name = "ffi_lib",
    crate_root = "src/ffi.rs",
    srcs = ["src/ffi.rs"],
    edition = "2021",
    proc_macro_deps = [":derive_impl"],
    link_deps = [":native"],
)
```

proc_macro_deps builds macros in exec configuration; C libraries/final crates use target configuration. Rust link_deps consumes native CcInfo; deps retains Rust crates/build-script results. Declare original C ABI in ffi.rs, call it and assert results. Public CcInfo/platforms supply headers, libraries and toolchains. Declare bindgen-like [generators](code-generation.md) with headers and exec tools; consume Rust outputs or build-script OUT_DIR.

## 5. Installation and step verification

Use [sonic_deploy_tar](install-interfaces.md#2-native-programs-and-deb-intermediate-layers) to map ELF outputs to original paths and deliver runtime TAR, matching symbols and metadata. Dynamic libraries, configuration and services follow the install contract. Export FFI using rust_static_library/rust_shared_library plus headers and matching C/C++ link interfaces.

```sh
bazel build //:service
bazel test //:unit_tests
bazel build //:configured_lib --//:with_stats=true
bazel build //:configured_lib --//:with_stats=false
bazel aquery 'deps(//:service)' --output=textproto
```

Replace labels with applicable branches and use identical platform arguments for build/test/aquery. Check SDK, crate versions/origins, sources, features, build.rs outputs, proc-macro exec configuration and native links. Feature changes require API and installation checks. Extract the runtime TAR and execute installed programs/native calls in a matching environment. Native Cargo checks use --locked. Keep native and Bazel evidence separately; normal builds preserve locks.
