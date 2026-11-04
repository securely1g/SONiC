# C/C++: from build contract to public interfaces

Read the entire [shared contract](common-contract.md), then the applicable sections here.

Use this route for C/C++ libraries, programs and native language bindings. Complete Make analysis first, identifying per-target sources, generated files, public headers, static/shared forms, ABI, configuration and installation. Examples use a module-root BUILD.bazel with module-relative source/template paths. Values are illustrative; pin rules_cc, bazel_skylib and shared infrastructure in MODULE.

Component declarations must not select C/C++ toolchains or compiler paths. Platform selection and Bazel toolchain resolution choose them. Select target platforms through build/validation platform arguments.

## 1. Generate sources, headers and configuration

For every generated file, identify the producing tool/action (such as protoc, a project script or template substitution), direct/transitive inputs, output path, arguments and consuming targets before choosing the implementation:

| Requirement | Implementation | Handoff check |
| --- | --- | --- |
| Fixed text template | Skylib expand_template | Explicit template, substitutions and output; preserve escaping and macro semantics |
| protobuf, SWIG, Thrift | Verified [generator rules](code-generation.md) | Tools in exec configuration, generated code compiled in target configuration |
| Existing tool producing fixed files | Existing action rule first; simple fixed calls may use genrule tools/outs | No PATH lookup; complex transitive inputs use the appropriate shared rule |
| Project generator | Native language executable invoked by a hermetic action | [Tool examples](hermetic-tools.md); complete tool sources and runtime data |

Example: analysis establishes a user-controlled feature macro and a component-declared version:

```starlark
load("@bazel_skylib//rules:common_settings.bzl", "bool_flag")
load("@bazel_skylib//rules:expand_template.bzl", "expand_template")

bool_flag(name = "with_stats", build_setting_default = False)
config_setting(name = "stats_on", flag_values = {":with_stats": "true"})

expand_template(
    name = "config_header",
    template = "config.h.in",
    out = "generated/config.h",
    substitutions = select({
        ":stats_on": {
            "@VERSION@": "1.2.3",
            "@STATS_DEFINE@": "#define HAVE_STATS 1",
        },
        "//conditions:default": {
            "@VERSION@": "1.2.3",
            "@STATS_DEFINE@": "/* #undef HAVE_STATS */",
        },
    }),
)
```

The minimal config.h.in contains `#define EXAMPLE_VERSION "@VERSION@"` and a separate `@STATS_DEFINE@` line. expand_template substitutions accepts select results. This switch comes from the requirements; obtain Autoconf values through [controlled probes](hermetic-tools.md#target-toolchain-autoconf-analysis).

## 2. Public headers and implementation libraries

With include/example/api.h consumed as `<example/api.h>`, implementation src/api.cc and private `"generated/config.h"`:

```starlark
load("@rules_cc//cc:cc_library.bzl", "cc_library")

cc_library(
    name = "api_headers",
    hdrs = ["include/example/api.h"],
    strip_include_prefix = "include",
    visibility = ["//visibility:public"],
)
cc_library(
    name = "api_objects",
    srcs = ["src/api.cc", ":config_header"],
    deps = [":api_headers"],
    linkstatic = True,
)
```

Put public headers in hdrs and propagate through deps. Put private and implementation-only generated headers in implementation srcs. Public generated headers belong in public hdrs with the declared include layout and dependencies on other public headers. Use propagating includes only when required. strip_include_prefix/include_prefix express logical names without copying trees. Obtain dependency headers through deps compilation contexts; global `-I` copts must not hide missing exports.

## 3. Static libraries, shared libraries and SONAME

Derive required .a/.so deliverables, shared filenames, SONAME, versions and install links from the per-target Make analysis output. Complete missing analysis before implementation. cc_library(linkstatic=True) provides this target's archive; transitive dependencies still link separately. To distribute the original recipe's separate .a files, inspect selected rules_cc output groups first. Where archive is supported, export it directly:

```starlark
filegroup(
    name = "api_archive",
    srcs = [":api_objects"],
    output_group = "archive",
    visibility = ["//visibility:public"],
)
```

Use cquery --output=files to verify archive count and identity, then map installed filenames. An output filename does not establish an identically named usable label. Use `@rules_cc//cc:cc_static_library.bzl` with `cc_static_library(name="api_archive", deps=[":api_objects"])` only when the original contract requires one archive merging transitive dependencies.

For Libtool linking, follow the selected version's argument translation and effective command. Libtool -static can prefer static Libtool libraries from the build tree while libc remains dynamically linked. Distinguish it from -all-static and compiler-level -static. Usually express the former with linkstatic=True and explicit library dependencies. Fully static linking needs original-rule evidence and actual ELF inspection.

A public alias to :api_objects does not require public visibility on the implementation target.

Example analyzed contract: release libexample.so.1.2.3, SONAME libexample.so.1, ABI soversion 1, file version 1.2.3 and development link libexample.so. Library versions are separate from module/Debian versions. Map to native cc_shared_library as follows:

```starlark
load("@rules_cc//cc:cc_shared_library.bzl", "cc_shared_library")
load("@sonic_build_infra//cc:shared_library.bzl", "shared_library_cc_info")

cc_shared_library(
    name = "api_shared",
    deps = [":api_objects"],
    shared_lib_name = "libexample.so.1.2.3",
    user_link_flags = ["-Wl,-soname,libexample.so.1"],
    visibility = ["//visibility:public"],
)
shared_library_cc_info(name = "api_link", shared_library = ":api_shared")
cc_library(
    name = "api",
    deps = [":api_headers", ":api_link"],
    visibility = ["//visibility:public"],
)
```

shared_lib_name sets the filename; user_link_flags `-Wl,-soname,...` sets SONAME. Express soversion through SONAME/install links. Declare runtime `libexample.so.1 -> libexample.so.1.2.3` and development `libexample.so -> libexample.so.1` links separately. Derive modes, directories and architecture paths from the installation contract and export runtime/development layers through [installation interfaces](install-interfaces.md).

The shared_library_cc_info adapter supplies linking CcInfo; the outer library adds header compilation context. Native shared consumers put producer :api_shared in dynamic_deps while retaining compilation dependencies in source-library deps. Verify each implementation object is exported once; avoid linking both static implementation and its dynamic interface. Preserve PIC, visibility, exported symbols, version scripts and --as-needed semantics. Declare version scripts in additional_linker_inputs and reference their location in user_link_flags.

For example, Common's `libswsscommon` used to embed libnl objects, so a consumer that linked Common together with the libnl shared libraries failed with Bazel's "Two shared libraries ... link same library statically" error; at run time, two copies of libnl in one process can also bind a library's calls to the wrong copy. [swss-common #41](https://github.com/securely1g/sonic-swss-common/pull/41) made Common depend on the libnl shared libraries instead, using `libnl3@3.7.0.sonic.7` from [registry #181](https://github.com/securely1g/sonic-bazel-registry/pull/181), whose output filenames match the `*.so.200` SONAMEs.

Establish separate expectations for archive symbols and shared dynamic exports. After a patch removes a function's static qualifier or restores its definition, trace later patches, visibility attributes and the final version script. A rule such as local: *; may still hide it from the shared library. Check archive symbols and required static consumers separately from dynamic symbols, symbol versions and shared consumers. Derive expectations from the complete patched link contract before inspecting outputs.

## 4. APT and component dependencies

Import pinned collections in MODULE under the [APT guide](use-apt-libraries.md), then query actual targets. Shared development collections use the common source configuration and APT lock. CcInfo supplies headers/libraries; target platforms choose architecture/toolchain. Components consume public library targets directly. For verified `@trixie//uuid-dev:uuid`, put that label in deps; query its package targets and inspect actual headers/link files with aquery. Runtime TAR/OCI/rootfs separately consume matching runtime layers: build deps do not automatically install dependencies. Fix excess library aggregation at the exporter.

Import other source components with verified bazel_dep versions/repo_name and public API/static labels. Obtain versions/labels from producer handoff and verify new modules under [registration](register-bazel-module.md). Follow module override guidance for local sources; keep local and registry consumption evidence separate.

Define a cc_binary consumer in an independent package with deps=["//:api"]; include the public header and call a real export. Also verify the external module label in an independent module, without producer-private include paths.

## 5. Optional configuration and completion

One bool_flag controls applicable srcs, local_defines/defines, deps and installation. Propagate only contractual macros. Keep fixed options fixed and select architecture capabilities through platforms under [configuration](configuration.md). Example invocation:

```sh
bazel build //:api --//:with_stats=true
bazel build //:api --//:with_stats=false
bazel aquery 'deps(//:api)' --//:with_stats=true --output=textproto
```

The producer is in the module root package; independent consumers have their own packages. Use identical platform/feature arguments for query/build/test. Inspect generated configuration, actual sources/macros/link files, readelf SONAME/NEEDED, independent header/link consumers and installed links/runtime behavior. Deliver runtime TAR, required development layer, matching symbols and metadata after successful builds. Keep [acceptance evidence](review-port.md).

References: [Bazel C/C++ rules](https://bazel.build/reference/be/c-cpp), [Skylib templates](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/expand_template.bzl).
