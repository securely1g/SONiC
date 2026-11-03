# Python sources, wheels and installation TARs

Read the [shared contract](common-contract.md). This page covers producers; Docker/rootfs resolve complete runtime versions under [Python runtime locking](dependency-locking.md#python-runtime-locks-and-requires-dist). A package's wheel, installation TAR and runtime metadata must derive from one declaration.

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

Python deps supply source modules for build/tests; requires below declares distribution dependencies. service_wheel contains service only; common is a separate distribution or install target.

## 3. Generate distribution and installation from shared metadata

In root metadata.bzl:

```starlark
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")
load("@sonic_build_infra//python:site_packages.bzl", "site_packages")

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
    py_wheel(name = "common_wheel", deps = [":common_contents"], **COMMON)
    py_wheel(name = "service_wheel", deps = [":service_contents"], **SERVICE)
    site_packages(
        name = "common_install",
        files = {"example_common/__init__.py": "example_common/__init__.py"},
        site_packages = "/usr/local/lib/python3.13/dist-packages",
        scripts = "/usr/local/bin",
        headers = "/usr/local/include",
        data_prefix = "/usr/local",
        interpreter = "/usr/bin/python3",
        visibility = ["//visibility:public"],
        **COMMON
    )
    site_packages(
        name = "service_install",
        files = {
            "example_service/__init__.py": "example_service/__init__.py",
            "example_service/cli.py": "example_service/cli.py",
            "example_service/default.json": "example_service/default.json",
        },
        site_packages = "/usr/local/lib/python3.13/dist-packages",
        scripts = "/usr/local/bin",
        headers = "/usr/local/include",
        data_prefix = "/usr/local",
        interpreter = "/usr/bin/python3",
        runtime_deps = [":common_install"],
        visibility = ["//visibility:public"],
        **SERVICE
    )
```

files maps single-file labels to package-relative paths. Use actual generated-file targets for generated sources/extensions. Both branches generate their required metadata from shared identity/dependency declarations. For nested Bazel packages, py_package filters by short paths including Bazel directories: native/native_example uses packages=["native.native_example"], then py_wheel strip_path_prefixes=["native"] retains native_example as import root. Check selected sources/resources/extensions before wheel paths. Installation files map directly to target-relative layout.

site_packages defaults to this package's installation TAR only. PythonRuntimeInfo separately propagates source identities, metadata and transitive TARs. service_install.runtime_deps carries common's identity to assembly without duplicating common files in service's TAR. The rule generates entry scripts, dist-info and RECORD; shebang uses the declared target interpreter.

Build both branches. Check service-only wheel contents and separate common production; compare Requires-Dist, Requires-Python, extras and entry points.

## 4. Native extensions and generated files

For SWIG/protoc/Cython backend inputs, perform [generation](code-generation.md) first and feed native language rules. C/C++ extensions use target-platform Python headers and native libraries; see SWIG examples for linkshared.

Wheel and installation TAR share extension files and metadata. For CPython 3.13 Linux, use python_tag/abi cp313 and a target-CPU platform such as linux_x86_64 or linux_aarch64. Use manylinux only when its compatibility requirements are met. Pure Python uses py3/none/any. CPU comes from platforms; ABI comes from the target interpreter. These are illustrative, not universal tags.

Place extensions in py_library.data, select through the same package's py_package and map installation files to the same Python package. Check Root-Is-Purelib/tags against actual extension identity. Install dynamic dependencies through the runtime closure; generation tools/execution libraries stay outside it.

## 5. Handoff to assembly resolution and consumption

Collect the complete source closure from service_install's PythonRuntimeInfo. python_runtime_plan declares entry example-service[metrics], target environment and index. Generate and commit the runtime lock; checked_python_runtime validates it and provides source TARs plus locked wheel installation TARs. Follow the complete [runtime lock example](dependency-locking.md#pip-runtime-lock-generation-example) for actions, arguments and initial locking. Update affected runtime locks when sources or Requires-Dist change; normal builds read production locks only.

## 6. Step verification and delivery

```sh
bazel build //:common_wheel //:service_wheel //:common_install //:service_install
bazel cquery --output=files //:service_install
bazel aquery 'deps(//:service_install)' --output=textproto
```

Replace labels for the actual component package, using one platform/feature configuration. Check:

| Output | Observation |
| --- | --- |
| Wheel | Files, resources, METADATA, WHEEL, RECORD, entry_points; own contents separate from runtime requirements |
| Installation TAR | Paths, modes, shebang, dist-info, installed RECORD; source installation reads files directly |
| Runtime metadata | Entry collects both service/common producers, versions, dependencies and TARs |
| Installed copy | Import both packages in target interpreter, read resources, run example-service, query distribution metadata |
| Native extension | ELF architecture, SOABI, initialization symbol, NEEDED and installed invocation |
| Runtime lock consumer | Successful update/check, unchanged normal-build lock, stale detection for source dependency/constraint changes |

Execute installed copies in the declared matching runtime. Report cross builds and target execution separately.
