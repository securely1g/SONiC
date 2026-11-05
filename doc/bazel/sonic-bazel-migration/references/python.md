# Python sources, wheels and installation TARs

Read the [shared contract](common-contract.md). Python distributions follow owner source -> wheel -> shared `wheel_layer` installation TAR -> OCI/rootfs. Producers own wheel contents and metadata; Docker/rootfs resolve complete runtime versions under [Python runtime locking](dependency-locking.md#python-runtime-locks-and-requires-dist). The installation TAR and runtime metadata derive from the selected wheel, without a parallel direct-source installation path.

## 1. Obtain inputs from Make analysis

Obtain packages, resources, generated sources, version origin, Requires-Python, Requires-Dist, extras/markers, entry points, licenses and installation layout. Read patched pyproject.toml/setup.py and distinguish backend generation/extension compilation from distribution metadata. Metadata is not resolution: requires preserves original ranges/conditions; assemblers choose runtime versions. Pin actual imports needed for building, generation and tests separately under the locking guide.

Check every file's origin, every entry point's module/function, target Python, extension ABI and installed interpreter path. Versions/constraints must come from original declarations.

## 2. Declare tools and two source packages

Declare selected rules_python and sonic-build-infra directly in MODULE. This example registers Python 3.13; select the actual version from producer/consumer contracts.

```starlark
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(python_version = "3.13")
use_repo(python, "python_3_13")
```

The toolchain supplies build/generation/test interpreters. Declare the installed script's target interpreter path separately. Archiving a pure Python wheel neither starts the product service nor requires installing the Requires-Dist runtime closure.

This module-root example has example_common/__init__.py, example_service/{__init__,cli}.py and example_service/default.json. common.answer() returns 37; cli.main prints it and reads its own resource using importlib.resources. Declare package contents and both dependency identities:

```starlark
load("@rules_python//python:py_library.bzl", "py_library")
load(":metadata.bzl", "source_packages")

py_library(
    name = "common_lib",
    srcs = ["example_common/__init__.py"],
)
py_library(
    name = "service_lib",
    srcs = ["example_service/__init__.py", "example_service/cli.py"],
    data = ["example_service/default.json"],
    deps = [":common_lib"],
)
source_packages()
```

Python deps supply source modules for build/tests; requires below declares distribution dependencies. service_wheel contains service only; common is a separate distribution with its own wheel.

## 3. Build owner wheels and install them through the shared rule

In root metadata.bzl:

```starlark
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

COMMON = dict(
    distribution = "example-common",
    version = "1.2",
    python_requires = ">=3.11",
    requires = ["PyYAML>=6,<7"],
    python_tag = "py3",
)
SERVICE = dict(
    distribution = "example-service",
    version = "2.0",
    python_requires = ">=3.11",
    requires = ["example-common>=1,<2", "requests>=2.32.3,<3; python_version >= '3.11'"],
    extra_requires = {"metrics": ["prometheus-client>=0.20,<1"]},
    entry_points = {"console_scripts": ["example-service = example_service.cli:main"]},
    python_tag = "py3",
)

def source_packages():
    py_package(name = "common_contents", packages = ["example_common"], deps = [":common_lib"])
    py_package(name = "service_contents", packages = ["example_service"], deps = [":service_lib"])
    py_wheel(
        name = "common_wheel",
        deps = [":common_contents"],
        visibility = ["//visibility:public"],
        **COMMON
    )
    py_wheel(
        name = "service_wheel",
        deps = [":service_contents"],
        visibility = ["//visibility:public"],
        **SERVICE
    )
```

Use actual generated-file targets for generated sources/extensions. For nested Bazel packages, py_package filters by short paths including Bazel directories: native/native_example uses packages=["native.native_example"], then py_wheel strip_path_prefixes=["native"] retains native_example as import root. Check selected sources/resources/extensions and wheel paths against the original package contract.

After generating and checking the runtime lock, register its `example_runtime_pip` hub as in the [locking example](dependency-locking.md#pip-runtime-lock-generation-example). A runtime/BUILD.bazel in this illustrative module installs both owner wheels and the complete locked external closure:

```starlark
load("@example_runtime_pip//:requirements.bzl", "all_whl_requirements")
load("@sonic_build_infra//python:wheel_layer.bzl", "wheel_layer")

wheel_layer(
    name = "installed_python",
    wheels = ["//:common_wheel", "//:service_wheel"] + all_whl_requirements,
    site_packages = "/usr/local/lib/python3.13/dist-packages",
    scripts = "/usr/local/bin",
    headers = "/usr/local/include",
    data_prefix = "/usr/local",
    interpreter = "/usr/bin/python3",
    visibility = ["//visibility:public"],
)
```

Use the actual consumer's interpreter and installation scheme. The shared installer reads wheel metadata, places purelib/platlib and .data contents, generates entry scripts and installed RECORD, and emits a TAR for OCI/rootfs. It does not resolve dependencies, download them, execute package code or compile bytecode. The example's wheel list must include the locked external requirements for the selected `example-service[metrics]` entry. Do not recreate installation with `site_packages`, `source_package_install`, ad hoc copies or custom wheel extraction.

The verified `wheel_layer` interface returns its TAR through DefaultInfo; it does not provide PythonRuntimeInfo or accept runtime_deps. Metadata export and lock checking must use a supported shared wheel-aware interface, as described below. This combined TAR requires the checker to classify distributions by the selected wheels' source or external origin. The locking example keeps separate owner/external wheel layers for checks that classify whole TARs. A successful wheel_layer build alone does not prove runtime closure or lock provenance.

## 4. Native extensions and generated files

For SWIG/protoc/Cython backend inputs, perform [generation](code-generation.md) first and feed native language rules. C/C++ extensions use target-platform Python headers and native libraries; see SWIG examples for linkshared.

For a wheel-packaged extension, the installation TAR comes from that wheel's extension files and metadata. For CPython 3.13 Linux, use python_tag/abi cp313 and a target-CPU platform such as linux_x86_64 or linux_aarch64. Use manylinux only when its compatibility requirements are met. Pure Python uses py3/none/any. CPU comes from platforms; ABI comes from the target interpreter. These are illustrative, not universal tags.

Place extensions in py_library.data and select through the same package's py_package. Check Root-Is-Purelib/tags against actual extension identity and the installed package path. Install dynamic dependencies through the runtime closure; generation tools/execution libraries stay outside it.

Existing native/generated binding outputs already exposed as runtime TARs, such as SWIG or protobuf/native bundles, do not require an unrelated wheel conversion. Preserve their build, metadata, ABI and installed-consumer checks. Apply the wheel route when Python distribution packaging is the work in scope; loose scripts/assets remain governed by their installation contract.

## 5. Handoff to assembly resolution and consumption

Collect the complete owner-wheel closure and its METADATA, including source identities, versions, Requires-Python/Dist, extras and markers. Resolve the entry example-service[metrics] for the target environment and index; keep owner distributions bound to their source-built wheels instead of resolving substitutes from PyPI. Generate and commit the runtime lock and provenance under the task's publishing authorization. Follow the [runtime lock workflow](dependency-locking.md#pip-runtime-lock-generation-example) for owner inputs, updates and checks. Refresh affected locks when source metadata or requirements change; normal builds read and check production locks only.

Before using python_runtime_plan/checked_python_runtime with wheels, verify that the selected shared implementation accepts wheel-derived metadata and installation TARs. Their direct-source PythonRuntimeInfo contract cannot be assumed to work with wheel_layer. Implement any missing reusable metadata/check adapter in sonic-build-infra and integrate it before claiming complete runtime validation; do not run a second direct-source installation just to obtain that provider. OCI/rootfs consume the checked wheel-derived installation TARs and the remaining native runtime closure.

## 6. Step verification and delivery

```sh
bazel build //:common_wheel //:service_wheel //runtime:installed_python
bazel cquery --output=files //runtime:installed_python
bazel aquery 'deps(//runtime:installed_python)' --output=textproto
```

Replace labels for the actual component package, using one platform/feature configuration. Check:

| Output | Observation |
| --- | --- |
| Wheel | Files, resources, METADATA, WHEEL, RECORD, entry_points; own contents separate from runtime requirements |
| Installation TAR | Paths, modes, shebang, dist-info, installed RECORD; WheelLayer action consumes the selected owner wheels and locked external wheels |
| Runtime metadata | Entry retains both service/common source producers, wheel identities, versions, dependencies and resulting TARs |
| Installed copy | Import both packages in target interpreter, read resources, run example-service, query distribution metadata |
| Native extension | ELF architecture, SOABI, initialization symbol, NEEDED and installed invocation |
| Runtime lock consumer | Successful update/check, unchanged normal-build lock, stale detection for source dependency/constraint changes |

Retain and run applicable upstream tests as well as installed-payload tests; a source-tree import test does not verify the installed wheel. Compare the installed file/resource selection with the original packaging inputs, including entry points and licenses. Execute installed copies in the declared matching runtime. Report cross builds and target execution separately.
