# Build tools, sysroot, and execution configuration

Use this guidance when a migration adds a generator or another program that runs during a build. Classify each dependency by its consumer, including libraries and data needed to run the tool.

| Dependency role | Shared ownership | Configuration at the consuming edge |
| --- | --- | --- |
| Build-time executable, such as Doxygen or Aspell | Existing Bazel rule/toolchain when compatible; otherwise pinned `sonic-build-infra` `build_tools` packages | Execution configuration |
| Tool runtime libraries, dynamic loader, plugins, and dictionaries | The declared tool runtime or `build_tools` bundle | Same execution configuration as the tool |
| Minimal system ABI headers/libraries: libc, loader, compiler runtime, standard library | Pinned compiler `sysroot` | Target configuration |
| Ordinary component/third-party libraries, including native bindings and test libraries | Source targets or pinned package imports with reusable integration published through the registry | Target configuration |
| Files installed into the final image | Explicit runtime package/image targets | Target configuration |

`sysroot` is the compiler's view of the target system. `build_tools` is the shared package set for programs used while building. A Debian package's format does not determine its role. A library needed by both a generator and the resulting application can legitimately be selected in both configurations.

Apply the [component-source policy and dependency roles](source-builds-and-lockfiles.md#separate-execution-tools-from-target-dependencies) to each use independently. Pinned binary packages are allowed for both a generator's private runtime and an application's external libraries. Declare the target library separately in target configuration, even when it comes from the same package version as a generator dependency; an execution-side payload can have the wrong architecture. Ordinary protobuf or Boost target libraries belong in a target dependency set, rather than `build_tools`. Neither a package-set name nor `cfg = "exec"` establishes source provenance.

## Reuse shared inputs

First look for compatible Bazel rules, modules, and toolchains, including the Bazel Central Registry. When the migration needs pinned Debian tools, reuse or extend `sonic-build-infra`'s `build_tools` set and its shared APT sources and lock mechanism. Follow the [single build-tools set policy](../SKILL.md#use-one-shared-build-tools-package-set) before proposing another execution-tool dependency set. Keep target compiler packages in `sysroot`. Publish shared module changes through `sonic-bazel-registry`; component rules consume those inputs and own their generator actions.

Declare the tool's complete runtime dependencies: an executable alone may still load worker-installed libraries, invoke an interpreter from `PATH`, or read system dictionaries. Preserve the package payloads or runfiles required by the pinned implementation. Retire a component-local package lock and downloader after validating the replacement's tool versions and generated outputs.

Separating execution tools from the target sysroot clarifies ownership and prevents target compiler inputs from becoming the default home for unrelated generator packages. It does not by itself select an architecture, guarantee hermetic execution, or establish which packages the repository rule downloads. Verify those properties in the pinned rule version and configured graph.

## Put `cfg = "exec"` on the tool dependency

The execution platform is where an action runs, which may be a remote worker. The target platform is where the resulting library or program will run. For an AMD64 execution platform building ARM64 outputs, a generator and its runtime must run on AMD64 while generated C/C++ is compiled for ARM64.

In a custom Starlark rule, these illustrative attribute declarations express that boundary:

```starlark
attrs = {
    "generator": attr.label(executable = True, cfg = "exec"),
    "tool_bundle": attr.label(allow_single_file = True, cfg = "exec"),
    "srcs": attr.label_list(allow_files = True),
    "deps": attr.label_list(),
}
```

- `generator` refers to a runnable target. Pass its executable and required runfiles to the action using the rule's supported tool interface.
- `tool_bundle` refers to a file or directory artifact containing tools and their runtime. It needs execution configuration even though the artifact itself is not executable. Its package dependencies inherit that configuration unless another transition intervenes.
- `srcs` and target library `deps` remain in the consuming target's configuration. Declare generator input headers, schemas, scripts, and data as action inputs; running a generator during a build does not make all its input data execution-platform dependencies.

The transition belongs on the dependency edge; writing `cfg = "exec"` in `apt.install()` or naming a repository `build_tools` does not configure its consumers. The transition also cannot convert a hard-coded ARM64 executable into an AMD64 executable: its provider must offer a compatible tool for the selected platform.

Use existing rule/toolchain interfaces when they already make this selection. For reusable platform-selected tools, prefer Bazel toolchain resolution over ad-hoc CPU transitions. Keep a tool's configuration aligned with the action's toolchain or execution group; a tool from one execution platform must not be run by an action assigned to another. See Bazel's [configuration guidance](https://bazel.build/extending/rules#configurations), [attribute API](https://bazel.build/rules/lib/toplevel/attr#label), and [toolchain documentation](https://bazel.build/extending/toolchains).

## SAI example and validation

SAI metadata generation uses Doxygen, Aspell, and the English dictionary from `build_tools`, together with their runtime dependencies. Its `tool_bundle` edge uses `cfg = "exec"`; generated metadata sources then feed the target build. This layout is recorded in [build-infra #8](https://github.com/securely1g/sonic-build-infra/pull/8), [registry #22](https://github.com/securely1g/sonic-bazel-registry/pull/22), and [the SAI module](https://github.com/securely1g/sonic-bazel-registry/pull/17). The earlier shared-sysroot implementation already selected tools in execution configuration; the separate set clarified ownership rather than repairing that transition.

For the configurations in scope, inspect configured dependencies/actions to verify the selected tool architecture and declared inputs, exercise the tool without undeclared worker-installed copies, and compare generated outputs with the reference build. When claiming cross-compilation support, run the generator on the execution platform and compile its output for a different target architecture. Native AMD64 and native ARM64 tests can both pass while an incorrect target-configured tool edge remains hidden; record untested cross-platform pairs as gaps.
