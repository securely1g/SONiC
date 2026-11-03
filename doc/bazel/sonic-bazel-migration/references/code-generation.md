# Migrate code generation tools

Read the [shared contract](common-contract.md). Analyze original versions, commands, languages, plugins, macros, import paths, complete inputs and outputs before choosing real rules. Tools run in exec configuration; target language rules compile/package results. Apply [hermetic tool closure](hermetic-tools.md). For Bison/Flex/M4/Perl/compile_et/mk_cmds/project tools, read applicable [tool recipes](tool-recipes.md) and connect generation to real consumers using these steps/examples.

## Procedure

A generator reads .y/.l/.proto/.i/.thrift/templates/configuration and produces sources/headers/modules, such as Bison, Flex, protoc, SWIG, Thrift or a project program. Record plugins/templates/subtools separately. Start from effective analysis.json/md; fill missing fields by tracing patched rules, not by inferring relationships from incidental build-directory files. Every output identifies its producing program, inputs and arguments.

| Step | Action | Completion |
| --- | --- | --- |
| 1. Relations | Rule location, full command, direct/transitive inputs, generated headers, macros/language/plugins/templates/paths/consumers | Every analyzed output has a producer; retain original committed-versus-regenerated choice |
| 2. Configuration | Separate exec tools/plugins/templates from target runtimes; map original configurable options to one setting | Executable exec tools and target compilation; platform-selected C/C++ toolchain |
| 3. Interfaces | Inspect real labels/attributes/output groups/runfiles/version/import closure | Compatible producer/public APIs selected |
| 4. Actions | Existing rules or simple genrule; shared rules/FilesToRunProvider for complex closures | Complete declared inputs/tools/outputs, writes limited to outputs |
| 5. Consumers | Separate C/C++ sources/headers, native Python/Go targets and explicit target runtimes | Correct logical paths/symbols/ABI |
| 6. Delivery | Actual parser/binding/protocol execution, installation TAR/metadata | Evidence for applicable checks and separate complete tool/product closures |

| Tool | Route |
| --- | --- |
| Bison/Flex | [Two-source/two-header generation](tool-recipes.md#bison-and-flex), parser-to-lexer dependency and native library |
| C++ protoc | Below; prefer compatible ProtoInfo rules where available |
| Python/gRPC protoc | [Examples](code-generation-examples.md), prerequisites/runtime aliases |
| Go/gRPC protoc | [Go generation](go.md#7-generated-code-branches) |
| Python SWIG | Below: wrapper/extension/Python consumer |
| Go SWIG | [CGo example](code-generation-examples.md#swig-go-bindings-and-cgo) |
| Thrift | Below and [three-language wiring](code-generation-examples.md#thrift-three-consumers-for-one-idl) |
| M4/Perl/project tools | [Recipes](tool-recipes.md#m4-perl-and-project-generators); Go tools also use Go guidance |

Replace example labels/packages with verified tools/consumers and use task platform configuration:

```bash
bazel query --output=build '@sonic_build_infra//tools/build_tools:protoc'
bazel cquery --output=files '@sonic_build_infra//tools/build_tools:protoc'
bazel build //example:generated //example:consumer
bazel aquery 'deps(//example:consumer)' --output=textproto
```

query/cquery prove selection only. Inspect aquery tools/inputs/argv and actual generated behavior. Version changes may require coordinated runtime/plugin/output/install updates. Commit declarations/locks by ecosystem; APT tools use the common lock.

## Before generation: bind inputs and paths to rules

Complete these checks during implementation, before consumers build. Final acceptance retains results rather than postponing first checks.

### 1. Pin tools and execution files

1. Record labels/origins/locked versions/configurations for generator/plugins/templates/subtools/target runtimes. Compatibility comes from original declarations or version documentation.
2. Inspect executable/runfiles/launchers. Custom actions use executable=True,cfg=exec and DefaultInfo.files_to_run; genrule uses tools. Producers declare interpreters/loaders/libraries/data. Export source ELF generators compiled with the Trixie sysroot through infra source_build_tool, including component-owned generators; see [source tools](tool-recipes.md#add-source-tools-or-component-generators).
3. Declare subprocesses explicitly. Bison puts M4 in tools and passes its location; skeletons belong to Bison runtime closure. Use [joint generation](tool-recipes.md#bison-and-flex).
4. Generators/plugins run as exec; generated C/C++ uses target configuration. BUILD declares headers/libraries, while platforms select toolchains.

Trace each runtime producer and check query attributes, then actual aquery paths/plugins/templates/configuration.

### 2. Map logical paths to actual files

For every include/import record reference text -> label -> logical root -> producer. Connect files to srcs/hdrs/deps/transitive inputs and roots to tool arguments. Declare search roots and actual read files independently.

For proto/message.proto importing common/types.proto at proto/common/types.proto, logical root is proto and both files are action inputs. ProtoInfo propagates through deps; legacy macros without that capability require suitable shared rules. Keep generated imports/includes consistent with original references and consumer mappings.

- Parser headers enter Flex srcs and consumer hdrs.
- SWIG inputs include interfaces/transitive/config headers and complete matching language templates; pass actual CcInfo include categories and one feature source to parser defines/wrapper compilation.
- Thrift uses declared -I and original -r, with direct-file realpaths confined to action inputs.

Find every real file in aquery inputs and verify logical roots, rather than directory flags alone.

### 3. Determine actual outputs before outs

Derive outputs from selected version/entry/namespace/language/options and analyzed manifests. If unclear, run managed tools on minimal inputs temporarily, then write confirmed outputs into BUILD. Normal builds use fixed outs or supported directory artifacts.

- protoc: logical roots/output roots/imports, explicit output directory creation/plugins; use [examples](code-generation-examples.md).
- SWIG Python: align module, .py, extension and initializer. SWIG Go: declare director header only when actually generated; preserve original director requirements and choose rules supporting the real output set.
- Thrift: constants/services/Python initializer levels/Go auxiliaries; one producer for shared namespace outputs.

Build generation alone, compare cquery files and contents, then connect consumers. Update mappings with IDL/features/options.

### 4. Connect language consumers and installation together

1. C/C++ sources/headers use srcs/hdrs/path mappings and target-runtime deps. Python/Go outputs enter native libraries. Tool targets own execution closure; language consumers own product runtimes.
2. Compile SWIG wrappers with target Python headers/libraries/features; co-install Python/extension files. For Go compile C++ in cc_library and connect CGo/cdeps, verifying callbacks where required.
3. Map actual TAR paths and propagate Python/dynamic runtime metadata. Immediately run minimal consumer behavior, then repeat on extracted installed copies in matching target environments.

Record generation/compile/call/installed-copy commands and results separately, including cross build versus execution.

## General implementation contract

Record separate origins/versions/compatibility for tool/plugin/templates/target runtime. Executables use exec and complete FilesToRunProvider; verify toolchain-provided File closures. Declare direct/transitive IDL/headers/configuration/plugins/templates, not search strings alone. Verify output names/directories/logical imports/packages; directory artifacts require real consumer support. Export sources/headers/modules separately with runtime/ABI/layout. Configurable original options share one setting; fixed options remain fixed. Parser and wrapper macros are separately declared.

## protoc

### Tool and runtime selection

Derive versions/languages/plugins from the component. protobuf-legacy uses its cpp_proto_sources/python_proto_sources with compatible same-module compiler/libprotobuf. Infra //proto:protoc requires verified pinned APT origin/exec runtime/runfiles and explicit target-language runtimes. Different protobuf module names do not imply interchangeable compiler/runtime.

### Implementation checks

Preserve logical roots/transitive imports/well-known types. Legacy direct srcs are current-repository/current-package files. Cross-package imports use proto_library and matching language rules/ProtoInfo. Root/output/include paths jointly determine layout. Pass explicit exec plugins and plugin/output arguments, not PATH. Generate pyi/descriptors/gRPC only when required. Check C++/Python/Go runtime versions and real serialization behavior.

### Minimal C++ generation and consumption

For one proto message -> public C++ library, use verified legacy 3.21 support only when required, with repo_name protobuf_legacy:

```starlark
load("@protobuf_legacy//:defs.bzl", "cpp_proto_sources")
load("@rules_cc//cc:cc_library.bzl", "cc_library")

cpp_proto_sources(
    name = "message_generated",
    srcs = ["proto/message.proto"],
    strip_import_prefix = "proto",
    output_prefix = "generated",
)
filegroup(name = "message_cc", srcs = [":message_generated"], output_group = "sources")
filegroup(name = "message_h", srcs = [":message_generated"], output_group = "headers")
cc_library(
    name = "message",
    srcs = [":message_cc"],
    hdrs = [":message_h"],
    strip_include_prefix = "generated",
    deps = ["@protobuf_legacy//:libprotobuf"],
    visibility = ["//visibility:public"],
)
```

libprotobuf was verified against that overlay's sonic/targets.bzl; recheck after version changes. The macro declares protoc. A consumer includes message.pb.h and verifies fields/serialization for `syntax = "proto3"; message Example { string value = 1; }`.

This macro has no generic deps. Cross-package transitives use ProtoInfo; verify every IDL in the action. Existing ProtoInfo routes retain matched proto_library/cc_proto_library/compiler/runtime. Direct managed protoc declares all transitive files, outputs and exec closure with explicit --proto_path/--cpp_out; a tool label alone supplies no language runtime. Pass plugins via --plugin=protoc-gen-NAME=PATH.

## SWIG

### Existing rules

Infra swig/defs.bzl exports:

| Rule | Required attributes | Output groups |
| --- | --- | --- |
| swig_gen | interface, swig_lib, cpp_out, python_out | cpp, python |
| swig_gen_go | interface, swig_lib, go_out, cxx_out; hdr_out when directors generate it | go, cxx; hdr when present |

Both accept hdrs/deps(CcInfo)/defines without -D. The default tool entry is @sonic_build_infra//tools/build_tools:swig. Its program comes from the selected BCR SWIG module's source binary and uses the shared launcher with matching runtime in exec configuration. Python fixes -c++/-python/-Wall/-keyword/-DSWIGWORDSIZE64; Go fixes -go/-cgo/-c++/-intgosize 64/-DSWIGWORDSIZE64. Check architecture applicability.

Templates must match tools. Python may use @swig//:lib_python, including swig.swg/full language files. Go needs complete Go templates, not Python templates. swig_lib_deb retains old subset extraction calls. For extraction-time completeness checks confirm selected support before enabling require_entry_point=True. Default extraction success does not prove full language closure; run generation/consumers.

```starlark
load("@sonic_build_infra//swig:defs.bzl", "swig_gen")

swig_gen(
    name = "bindings",
    interface = "api.i",
    hdrs = ["api.h"],
    swig_lib = "@swig//:lib_python",
    cpp_out = "generated/api_wrap.cpp",
    python_out = "generated/api.py",
)
```

Declare swig directly and check selection. Align python_out with %module, extension/init/import names. Wrapper compilation explicitly adds public headers/libraries/Python/CGo inputs. Pass actual CcInfo header/include categories and contractual macros from one configuration to parsing/compilation, not every compiler define blindly. Custom tools pass FilesToRunProvider. hdr_out is optional according to actual director outputs. Required template omissions must fail; use full language targets. Other SWIG rules require checked language/output/closure contracts.

### Connect SWIG to C++ and Python

Minimal api.i:

```text
%module api
%{
#include "api.h"
%}
%include "api.h"
```

api.h declares add and api.cc implements addition. Separate generated output groups:

```starlark
load("@rules_cc//cc:cc_binary.bzl", "cc_binary")
load("@rules_cc//cc:cc_library.bzl", "cc_library")
load("@rules_python//python:py_library.bzl", "py_library")

filegroup(name = "wrapper_cc", srcs = [":bindings"], output_group = "cpp")
filegroup(name = "wrapper_py", srcs = [":bindings"], output_group = "python")
cc_library(name = "api_impl", srcs = ["api.cc"], hdrs = ["api.h"], strip_include_prefix = ".")
cc_binary(
    name = "_api.so",
    srcs = [":wrapper_cc"],
    deps = [":api_impl", "@rules_python//python/cc:current_py_cc_headers"],
    linkshared = True,
    linkstatic = True,
)
py_library(
    name = "api_python",
    srcs = [":wrapper_py"],
    data = [":_api.so"],
    imports = ["generated"],
)
```

python_out is generated/api.py; wrapper imports _api. Example imports expose package root/generated; production co-installs api.py/_api.so in target site-packages. Check interpreter, target current_py_cc_headers and PyInit__api. Python uses linkshared; public C++ shared libraries use cc_shared_library. Link libpython only if the original target contract requires it.

Apply one feature source to SWIG defines and wrapper local_defines/copts. Build api_python and run `import api; assert api.add(17, 20) == 37` through declared tests and installed copies; runfiles must not hide missing installed libraries. Go uses go/cxx/hdr groups and native CGo interfaces; verify fixed 64-bit semantics against platforms.

## Thrift

1. Establish compiler/runtime versions, languages/import roots/options/install purpose. Verify modules expose compiler separately from C++ runtimes; use actual [tool labels](tool-recipes.md).
2. Source-built compilers use cc_binary with exec Flex/Bison/M4/templates; generation consumes the full compiler closure.
3. Declare entry/transitive .thrift/import roots, preserving -r/language/options: managed thrift -I ROOT --gen OPTIONS -out ROOT ENTRY. Declare outputs rather than scanning workspace afterward.
4. Derive exact outputs from IDL/language/namespace/service/options temporarily, then export sources/headers/modules. Include skeleton main only when installed originally.
5. Directly consume declared files; fix realpath/symlink/import handling in the owning tool/shared rule instead of copying input trees. Use directory artifacts only with actual consumer support.
6. Match each language runtime separately from compiler linking. Validate every original language, not one on behalf of all.

## Generator-specific acceptance

Select used languages/platforms from analysis/current authorization. Valid/invalid inputs derive from tool/product contracts. Run missing-input checks in temporary isolated entries, preserving user files. Save evidence during each step.

| Boundary | Action/observation |
| --- | --- |
| Identity/platform | aquery exec tool/plugin/template/subtools/closure; platform-selected target compiler |
| Outputs/consumption | Complete files/groups/logical paths/consumer sources and target runtimes |
| Transitive inputs | Real import/header; changing consumed types/templates reruns generation with corresponding behavior |
| Missing input | Omit a required import/header/template in isolation; strict sandbox fails generation with first diagnostic |
| Bison/Flex | Valid parsing, original invalid-input errors, parser-header dependencies/prefixes/stability |
| protoc | Fields/serialization per used language; actual gRPC server/request/response when required |
| SWIG | Actual Python/CGo calls and consistent feature APIs/compilation |
| Thrift | Transitive types/constants/serialization per language and required service calls |
| Installation | Extracted TAR consumer runs with wrapper/extension/runtime/dynamic closure |
| Root/independent | Both cross-module entries; separate cross-generation and target-runtime results |

### Failure boundary

After these upfront checks, save actual command/identity/first raw error and locate tool production, declaration, generation, compilation or installation ownership. Fix and rerun affected checks. Deliver when all applicable checks are evidenced; additional languages/platforms require task scope. See [protocol tests](protocol-tests.md).

## Verification records

Choose original languages/imports/types/constants/services and verify complete outputs/consumers. Check SWIG configured APIs and target Python/CGo calls; protobuf/Thrift fields and serialization. Inspect exec tools/transitives/argv/templates/plugins/outputs. Missing required imports/headers fail explicitly. Validate supported cross configurations. Keep task results/logs in evidence directories, not skill text.
