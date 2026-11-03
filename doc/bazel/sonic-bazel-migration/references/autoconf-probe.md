# Controlled Autoconf probing during migration

Read the [shared contract](common-contract.md) and [configuration generation contract](implement-component.md#autoconf-configuration-generation). Convert original configure checks into migration inputs backed by target-toolchain evidence. Keep probe targets/workspaces/logs temporary; regular components retain native compilation and required templates.

## 1. Prepare actual inputs

From Make analysis obtain patched configure, complete sources/m4/templates, feature options, install paths and target dependencies. The source producer exposes configure and the complete probe file set; dependencies expose CcInfo and, if needed, target .pc inputs. Original repository rules prepare sources. Probes consume them directly and write separate output directories.

Expose target .pc files using existing filegroup/DefaultInfo interfaces, including Requires/Requires.private closure. pkg_config_files derives search roots from File.dirname; headers/libraries still use CcInfo. prefix/libdir/includedir use producer-relocatable, exec-root-relative or selected-sysroot target paths and authoritative versions. Check queried headers/libraries are declared and accessible. Declare execution pkg-config runtime separately; exclude host /usr/lib/pkgconfig.

When autoreconf is required, generate configure temporarily with managed autoconf/automake/M4/libtool and complete macros, then pass results/inputs to the rule. Run target programs only where required; cross-run answers need target provenance.

## 2. Declare probes in the temporary workspace

Reuse verified dependencies/registry. Declare component, target dependencies and infra in its MODULE, import [confirmed inputs](register-bazel-module.md#development-verification-and-final-registry-consumption) and verify selected platforms/toolchains. Replace example_source/example_dep with analyzed producers/interfaces.

```starlark
load("@sonic_build_infra//tools/autoconf:probe.bzl", "autoconf_probe")

autoconf_probe(
    name = "inspect",
    configure = "@example_source//:configure",
    srcs = ["@example_source//:configure_inputs"],
    deps = ["@example_dep//:library"],
    pkg_config_files = ["@example_dep//:pkgconfig"],
    configure_args = ["--prefix=/usr", "--enable-example"],
    build_triplet = "x86_64-pc-linux-gnu",
    host_triplet = "aarch64-linux-gnu",
    expected_outputs = ["config.h", "Makefile"],
)
```

Assumption: example enabled, AMD64 executor probing ARM64 target, and the two declared configure outputs. Replace triplets/options/outputs from actual analysis/toolchains. Native build/host retain original semantics. Components do not select C/C++ toolchains. Pass original extra options separately in copts/linkopts and use the same select for features. Declare individual argv elements rather than shell-command strings.

| Input/output | Execution contract |
| --- | --- |
| configure/srcs | Complete sources/generated headers in inputs; out-of-tree configuration from declared source root, writes only private directory |
| Platforms/CcInfo | Selected C/C++ toolchain, sysroot, all_files, actual headers/defines/include categories and full link context |
| Compile/link options | rules_cc feature configuration/variables produce real argv; preserve library order/transitives/linker options/runtime paths |
| argv launchers | Private CC/CXX/AR/RANLIB launchers use arrays and exec, appending configure arguments with spaces/quotes preserved |
| Shell/subtools | Declared execution runtime and FilesToRunProvider, tool-only PATH, complete interpreters/loaders/libraries/macros |
| pkg_config_files | Managed pkgconf; clear inherited PKG_CONFIG_PATH; derive PKG_CONFIG_LIBDIR from File.dirname; default PKG_CONFIG_SYSROOT_DIR to platform sysroot; declare alternate target directory through pkg_config_sysroot; queried files must be inputs |
| configure_args/triplets | argv, explicit CC/CXX/AR/RANLIB/CPPFLAGS/CFLAGS/CXXFLAGS/LDFLAGS/LIBS, applicable locale/timezone, isolated CONFIG_SITE/cache |
| expected_outputs | Check every required configuration output; one declared analysis directory retains full output/logs |
| Default output | <name>.probe/ with identity.json, commands.json, environment.json, launchers/ and configuration/ containing config.log/config.status/generated files |

The effective sysroot comes from actual CC argv produced by the selected feature configuration. CcToolchainInfo.sysroot may be empty while argv already contains --sysroot=PATH. The shared probe takes the last effective value in that form, falling back to the toolchain field; explicit pkg_config_sysroot has highest priority. Target identity and default PKG_CONFIG_SYSROOT_DIR use that same value. The shared probe makes temporary execution-root paths absolute. Check selected support before assuming other argument forms.

Verify that pkg-config's returned headers/library paths belong to declared target inputs. An absolute -L/usr/lib/TARGET_TRIPLET does not prove the library was resolved inside the target sysroot. Cross probes must align CC argv, pkg-config environment and actual query results.

identity records sources/patches/files/toolchains/dependencies/platforms/configuration; commands records actual arrays. Exclude credentials from environment reports. Export the full target environment without client PATH/CPATH/LIBRARY_PATH or host pkg-config fallbacks.

## 3. Verify the environment before configure

In the temporary workspace, with matching triplets/platforms:

```bash
bazel aquery 'deps(//:inspect)' \
  --platforms=@sonic_build_infra//platforms:aarch64_trixie \
  --host_platform=@sonic_build_infra//platforms:x86_64_trixie \
  --output=textproto > probe-actions.textproto
```

Inspect aquery for exec tools and declared target sysroot/headers/libraries/.pc files; build/host/features must match analysis. Then run:

```bash
bazel build //:inspect --sandbox_debug \
  --platforms=@sonic_build_infra//platforms:aarch64_trixie \
  --host_platform=@sonic_build_infra//platforms:x86_64_trixie
PROBE_REL=$(bazel cquery //:inspect --output=files \
  --platforms=@sonic_build_infra//platforms:aarch64_trixie \
  --host_platform=@sonic_build_infra//platforms:x86_64_trixie)
PROBE_EXECROOT=$(bazel info execution_root)
PROBE_DIR="$PROBE_EXECROOT/$PROBE_REL"
```

Before configure, the rule checks target pkg-config references, declared tools and full argv, failing explicitly on mismatch. Retain the sandbox for raw config.log on failure. Save needed task evidence, then clean temporary probe execution outputs.

After success, inspect identity.json, commands.json, environment.json and configuration/config.log. Confirm actual compile/link operations use the same target toolchain/dependencies and every expected output exists. Read raw failed probe diagnostics first; missing environment headers/libraries do not justify disabling product features.

For cross runtime checks, provide original configure cache answers via cache_answers string dictionaries, with target identity/provenance in analysis. Actual program runs require matching target environments and saved behavior evidence. Choose by original probe semantics.

## 4. Turn conclusions into native inputs

For each result map value -> original check/log -> determining inputs -> final consumer. Put fixed capability values in declarations, architecture differences in platform selection and user options in one build setting. Convert temporary paths to declared inputs. Preserve undef versus define-zero semantics.

Example original config.h.in has HAVE_EXAMPLE_DEFINE/PROJECT_VERSION placeholders, with confirmed capability and authoritative version:

```starlark
load("@bazel_skylib//rules:expand_template.bzl", "expand_template")
load("@rules_cc//cc:cc_library.bzl", "cc_library")
load(":version.bzl", "PROJECT_VERSION")

expand_template(
    name = "configuration",
    template = "config.h.in",
    out = "generated/config.h",
    substitutions = {
        "@HAVE_EXAMPLE_DEFINE@": "#define HAVE_EXAMPLE 1",
        "@PROJECT_VERSION@": PROJECT_VERSION,
    },
)
cc_library(
    name = "component",
    srcs = ["component.cc"],
    hdrs = [":configuration"],
    deps = ["@example_dep//:library"],
)
```

component.cc includes declared generated/config.h. The capability applies only to confirmed inputs. Express configurable/platform values under [configuration](configuration.md). If the original template uses #undef HAVE_EXAMPLE, replace that line directly without changing semantics.

Build under required configurations, compare aquery target inputs to probe records and execute the corresponding product feature. Reprobe affected checks after source/patch/toolchain/sysroot/dependency/feature changes and update mappings. Keep logs/entries temporary; regular targets consume necessary templates only.
