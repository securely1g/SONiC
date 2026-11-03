# protoc, SWIG Go and Thrift generation-to-consumer examples

Follow [generation steps](code-generation.md#procedure) first, then applicable languages. Examples show BUILD wiring; analysis determines versions/platforms/options/install paths. Retain [generator acceptance](code-generation.md#generator-specific-acceptance) evidence.

## Prerequisites and dependency identities

- Declare compatible infra/rules_cc/rules_python/protobuf or protobuf-legacy and required rules_go, with topic-specific MODULE/toolchains.
- //deps aliases belong to the caller, not predefined infra. Define verified producers in deps/BUILD.bazel. grpc_cpp/protobuf_cpp are target CcInfo; protobuf_python/grpc_python/thrift_python are compatible PyInfo; thrift_cpp is target CcInfo; thrift_go is github.com/apache/thrift/lib/go/thrift GoLibrary.
- Python runtimes reuse source identities or locked third-party inputs; assembly owns final pip resolution under [Python](language-recipes.md).
- Put same-named independent examples in separate packages. Complete prerequisites before building fragments; verify exec tool/target runtime identities independently.

## protoc: Python messages

### Existing legacy macros

Use only a contract requiring verified protobuf-legacy, as in C++. proto/message.proto has Example. The macro generates Python/pyi output groups:

```starlark
load("@protobuf_legacy//:defs.bzl", "python_proto_sources")
load("@rules_python//python:py_library.bzl", "py_library")

python_proto_sources(
    name = "message_generated",
    srcs = ["proto/message.proto"],
    strip_import_prefix = "proto",
    output_prefix = "generated",
)
filegroup(name = "message_py", srcs = [":message_generated"], output_group = "python")
filegroup(name = "message_pyi", srcs = [":message_generated"], output_group = "pyi")
py_library(
    name = "message_python",
    srcs = [":message_py"],
    data = [":message_pyi"],
    imports = ["generated"],
    deps = ["//deps:protobuf_python"],
)
```

Consumers depend on message_python and import message_pb2. Install stubs only where required; supported rules_python may use pyi_srcs. Apply [legacy import limits](code-generation.md#protoc).

### Existing ProtoInfo route

proto_library deps propagate imports:

```starlark
load("@protobuf//bazel:proto_library.bzl", "proto_library")
load("@protobuf//bazel:py_proto_library.bzl", "py_proto_library")

proto_library(name = "common_proto", srcs = ["common.proto"])
proto_library(
    name = "message_proto",
    srcs = ["message.proto"],
    deps = [":common_proto"],
)
py_proto_library(name = "message_python", deps = [":message_proto"])
```

message.proto imports common.proto. This is root-package wiring; nested packages set logical strip_import_prefix/import_prefix. Import actual generated module paths and choose one producer per logical module. See [Go](go.md#7-generated-code-branches) for messages/gRPC.

## protoc: C++ and Python gRPC

Root echo.proto:

```proto
syntax = "proto3";
package demo;
message Request { string value = 1; }
message Reply { string value = 1; }
service Echo { rpc Ping(Request) returns (Reply); }
```

Direct tools apply when explicit plugins are required and matching macros cannot express them; prefer compatible dedicated rules. Verify tools/build_tools compiler/plugins against target runtimes. This example has no transitives; add files/logical roots together and prefer ProtoInfo for cross-module closures.

```starlark
load("@rules_cc//cc:cc_library.bzl", "cc_library")
load("@rules_python//python:py_library.bzl", "py_library")

genrule(
    name = "echo_cpp_generated",
    srcs = ["echo.proto"],
    outs = [
        "generated/echo.pb.cc",
        "generated/echo.pb.h",
        "generated/echo.grpc.pb.cc",
        "generated/echo.grpc.pb.h",
    ],
    tools = [
        "@sonic_build_infra//tools/build_tools:protoc",
        "@sonic_build_infra//tools/build_tools:grpc_cpp_plugin",
    ],
    cmd = 'mkdir -p "$(RULEDIR)/generated" && ' +
          '"$(location @sonic_build_infra//tools/build_tools:protoc)" ' +
          '-I "$$(dirname "$(location echo.proto)")" ' +
          '--cpp_out="$(RULEDIR)/generated" --grpc_out="$(RULEDIR)/generated" ' +
          '--plugin=protoc-gen-grpc="$(location @sonic_build_infra//tools/build_tools:grpc_cpp_plugin)" ' +
          '"$(location echo.proto)"',
)
cc_library(
    name = "echo_cpp",
    srcs = ["generated/echo.pb.cc", "generated/echo.grpc.pb.cc"],
    hdrs = ["generated/echo.pb.h", "generated/echo.grpc.pb.h"],
    strip_include_prefix = "generated",
    deps = ["//deps:grpc_cpp", "//deps:protobuf_cpp"],
)
genrule(
    name = "echo_python_generated",
    srcs = ["echo.proto"],
    outs = ["generated/echo_pb2.py", "generated/echo_pb2_grpc.py"],
    tools = [
        "@sonic_build_infra//tools/build_tools:protoc",
        "@sonic_build_infra//tools/build_tools:grpc_python_plugin",
    ],
    cmd = 'mkdir -p "$(RULEDIR)/generated" && ' +
          '"$(location @sonic_build_infra//tools/build_tools:protoc)" ' +
          '-I "$$(dirname "$(location echo.proto)")" ' +
          '--python_out="$(RULEDIR)/generated" --grpc_out="$(RULEDIR)/generated" ' +
          '--plugin=protoc-gen-grpc="$(location @sonic_build_infra//tools/build_tools:grpc_python_plugin)" ' +
          '"$(location echo.proto)"',
)
py_library(
    name = "echo_python",
    srcs = [":echo_python_generated"],
    imports = ["generated"],
    deps = ["//deps:protobuf_python", "//deps:grpc_python"],
)
```

Each sandbox creates its declared output root and writes its own outputs only. Base shell tools follow shared policy. Message and RPC dependencies separately use matching protobuf/gRPC CcInfo; target platforms select compilation toolchains.

Build both language libraries, start local Echo services and call Ping with echoed-field assertions. Python imports echo_pb2/echo_pb2_grpc and checks installed modules/native grpc extensions. Import success is not RPC proof. Let tests allocate ports.

## SWIG: Go bindings and CGo

This contract needs Go overrides of C++ virtual methods and callbacks, hence directors. api.i:

```text
%module(directors="1") api
%feature("director") Adder;
%{
#include "api.h"
%}
%include "api.h"
```

api.h/api.cc:

```cpp
// api.h
#pragma once
class Adder {
public:
    virtual ~Adder() = default;
    virtual int add(int a, int b);
};
int invoke(Adder *object, int a, int b);
```

```cpp
// api.cc
#include "api.h"
int Adder::add(int a, int b) { return a + b; }
int invoke(Adder *object, int a, int b) { return object->add(a, b); }
```

This interface produces api_wrap.h, package api, on supported 64-bit targets. Without original directors, omit hdr_out, api_hdr and that wrapper dependency. Supply //tools:swig_go_lib with matching complete swig.swg/go templates. Prefer existing exports; for APT data use verified swig_lib_deb(data=...,strip_prefix=...) from infra swig/defs.bzl and actual locked paths. Check version compatibility; missing templates fail generation.

```starlark
load("@sonic_build_infra//swig:defs.bzl", "swig_gen_go")
load("@rules_cc//cc:cc_library.bzl", "cc_library")
load("@io_bazel_rules_go//go:def.bzl", "go_library", "go_test")

cc_library(name = "api_impl", srcs = ["api.cc"], hdrs = ["api.h"], strip_include_prefix = ".")
swig_gen_go(
    name = "api_generated",
    interface = "api.i",
    hdrs = ["api.h"],
    deps = [":api_impl"],
    swig_lib = "//tools:swig_go_lib",
    go_out = "generated/api.go",
    cxx_out = "generated/api_wrap.cxx",
    hdr_out = "generated/api_wrap.h",
)
filegroup(name = "api_go_src", srcs = [":api_generated"], output_group = "go")
filegroup(name = "api_cxx_src", srcs = [":api_generated"], output_group = "cxx")
filegroup(name = "api_hdr", srcs = [":api_generated"], output_group = "hdr")
cc_library(
    name = "api_wrapper",
    srcs = [":api_cxx_src"],
    hdrs = [":api_hdr"],
    deps = [":api_impl"],
)
go_library(
    name = "api_go",
    srcs = [":api_go_src"],
    importpath = "example.invalid/component/api",
    cgo = True,
    cdeps = [":api_wrapper"],
)
go_test(name = "api_test", srcs = ["api_test.go"], embed = [":api_go"])
```

api_test.go, verifying actual exported names:

```go
package api

import "testing"

type multiplyingAdder struct{}
func (multiplyingAdder) Add(a, b int) int { return a * b }

func TestAdd(t *testing.T) {
    native := NewAdder()
    defer DeleteAdder(native)
    if got := Invoke(native, 17, 20); got != 37 {
        t.Fatalf("native Invoke = %d, want 37", got)
    }
    director := NewDirectorAdder(multiplyingAdder{})
    defer DeleteAdder(director)
    if got := Invoke(director, 3, 4); got != 12 {
        t.Fatalf("Go override Invoke = %d, want 12", got)
    }
}
```

cc_library compiles wrappers; Go consumes Go outputs/CGo libraries. Declare any headers directly included by generated Go as CGo inputs after inspecting outputs. Check 64-bit options against targets while tools run on exec. Follow [Go](go.md) for CGo/runtime/installation.

## Thrift: three consumers for one IDL

Fixed outputs illustrate Apache Thrift 0.20.0, not a universal version/list. Actual contracts select compatible versions. Generator sources: [C++](https://github.com/apache/thrift/blob/v0.20.0/compiler/cpp/src/thrift/generate/t_cpp_generator.cc), [Python](https://github.com/apache/thrift/blob/v0.20.0/compiler/cpp/src/thrift/generate/t_py_generator.cc), [Go](https://github.com/apache/thrift/blob/v0.20.0/compiler/cpp/src/thrift/generate/t_go_generator.cc).

message.thrift:

```thrift
namespace cpp demo
namespace py demo
namespace go demo
const i32 ANSWER = 37
struct Message { 1: string value }
```

No service/transitive includes/nested namespaces here. Actions share one verified exec compiler and declare language outputs separately. -out selects declared language directories without extra default gen-* nesting. Tools come from managed APT.

```starlark
load("@rules_cc//cc:cc_library.bzl", "cc_library")
load("@rules_python//python:py_library.bzl", "py_library")
load("@io_bazel_rules_go//go:def.bzl", "go_library")

genrule(
    name = "message_cpp_generated",
    srcs = ["message.thrift"],
    outs = [
        "cpp/message_types.cpp", "cpp/message_types.h",
        "cpp/message_constants.cpp", "cpp/message_constants.h",
    ],
    tools = ["@sonic_build_infra//tools/build_tools:thrift"],
    cmd = 'mkdir -p "$(RULEDIR)/cpp" && ' +
          '"$(location @sonic_build_infra//tools/build_tools:thrift)" ' +
          '--gen cpp -out "$(RULEDIR)/cpp" "$(location message.thrift)"',
)
cc_library(
    name = "message_cpp",
    srcs = ["cpp/message_types.cpp", "cpp/message_constants.cpp"],
    hdrs = ["cpp/message_types.h", "cpp/message_constants.h"],
    strip_include_prefix = "cpp",
    deps = ["//deps:thrift_cpp"],
)
genrule(
    name = "message_py_generated",
    srcs = ["message.thrift"],
    outs = ["python/__init__.py", "python/demo/__init__.py", "python/demo/ttypes.py", "python/demo/constants.py"],
    tools = ["@sonic_build_infra//tools/build_tools:thrift"],
    cmd = 'mkdir -p "$(RULEDIR)/python" && ' +
          '"$(location @sonic_build_infra//tools/build_tools:thrift)" ' +
          '--gen py -out "$(RULEDIR)/python" "$(location message.thrift)"',
)
py_library(
    name = "message_python",
    srcs = [":message_py_generated"],
    imports = ["python"],
    deps = ["//deps:thrift_python"],
)
genrule(
    name = "message_go_generated",
    srcs = ["message.thrift"],
    outs = ["go/demo/message.go", "go/demo/message-consts.go", "go/demo/GoUnusedProtection__.go"],
    tools = ["@sonic_build_infra//tools/build_tools:thrift"],
    cmd = 'mkdir -p "$(RULEDIR)/go" && ' +
          '"$(location @sonic_build_infra//tools/build_tools:thrift)" ' +
          '--gen go -out "$(RULEDIR)/go" "$(location message.thrift)"',
)
go_library(
    name = "message_go",
    srcs = [":message_go_generated"],
    importpath = "example.invalid/component/demo",
    deps = ["//deps:thrift_go"],
)
```

This Python version also generates output-root __init__.py. Constants cause C++ constants files; Go additionally produces message-consts.go/GoUnusedProtection__.go. Re-establish outputs after IDL/version/option changes and retain real auxiliary consumers.

For actual projects:

1. Declare all includes and -I roots; preserve original -r. Separate dependency generators/libraries to avoid duplicate definitions.
2. Shared Go namespaces need one owner for GoUnusedProtection__.go, through merged actions or suitable shared rules.
3. Services add complete outputs. Deliver skeleton main/remotes only by original install contract; libraries consume library sources. Output-changing options such as skip_remote require original justification.
4. Match Go imports/importpath; pass package_prefix/thrift_import only as required. Lock matching runtime source dependencies.
5. Per language round-trip Message(value="hello") and check ANSWER. Required services perform real calls; included types also round-trip. Installed Python imports demo.ttypes/demo.constants with runtime closure in TAR.

## Connect acceptance to consumers

Add [protocol test sources/rules](protocol-tests.md), execute real language commands and reuse behavior assertions on installed copies. Only original languages/services enter scope; normal generators consume pinned inputs.
