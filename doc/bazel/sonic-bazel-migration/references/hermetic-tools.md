# Host tools, analysis tools and hermetic actions

Read the entire [shared contract](common-contract.md), then applicable sections here before build-time tools, probes or tool rules. Host tools run on execution platforms but may process target headers/architecture descriptions and produce target outputs. Follow [tool selection](../SKILL.md#use-native-bazel-actions-and-declared-tools). Analysis tools do not automatically enter production builds.

## Shared interfaces and execution runtime

Host means execution-platform code. Source tools compiled on that machine can still use the pinned Trixie sysroot and need newer glibc/libstdc++ than the host provides. cfg="exec" selects execution configuration/architecture; matching loaders, libraries and tool data remain declared dependencies.

Infra tools/build_tools/defs.bzl provides two producer routes sharing build_tool and its launcher:

| Tool origin | Producer API | Consumer interface |
| --- | --- | --- |
| Pinned DEB | build_tools_runtime prepares closure; build_tool(tool=..., runtime=...) exports a manifest entry | Executable, FilesToRunProvider and runfiles |
| Pinned source or component generator | Native binary followed by source_build_tool(binary=...) | Same executable contract, retaining original binary runfiles |

The source route uses execution-side loader/libraries from the compiler's shared sysroot. Dynamic ELF runs through that loader; static ELF executes directly. Preserve each tool's actual linking contract. Tools using other SDKs/ABIs need their own verified compatible runtime closure. Infra owns execution mechanisms; producers declare source, arguments and component-specific data.

Confirm the selected infra revision provides these APIs. If the baseline predates source_build_tool, prepare the required shared revision under [module consumption](register-bazel-module.md#module-selection-and-registry-endpoints), record overrides and align published versions when publishing. See [tool integration](tool-recipes.md#add-and-consume-host-tools).

## APT host tools

Reuse infra public executables under [APT host tools](use-apt-libraries.md#consume-host-tools). Producers use global sources and lock exec-architecture DEBs plus transitive runtime closure, exporting launchers/FilesToRunProvider. Consumers pass the executable target through executable=True,cfg="exec" or tools. Declare interpreters, loaders, libraries, data and subprocesses. Select target/exec architectures independently through platforms. Images consume APT package files; target compilation consumes CcInfo; tool calls consume executable interfaces.

## Before invoking tools

Follow applicable [tool recipes](tool-recipes.md) for modules, public labels, toolchain references and calls; use [generation](code-generation.md) for versions/language consumers.

1. Record original versions, arguments, directory, environment, templates/plugins/data and subprocesses.
2. Inspect existing tools/toolchains, actual DefaultInfo.files_to_run, runfiles and launchers; an existing binary alone is insufficient.
3. Declare direct/transitive import/include inputs, outputs and search roots. Reference declared files instead of host /usr/include, PATH, HOME or network sources.
4. Separate exec tools and target libraries. In cross builds tools must run on the executor while headers/sysroot/libraries retain target identity.
5. Reuse existing rules; justify new rules and ownership under infrastructure guidance first.

## Minimal tool action rule

An existing native generator accepts --input, repeated --include and --output and produces one header. These arguments are illustrative, not protoc/SWIG syntax:

```starlark
def _generated_header_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name + ".h")
    args = ctx.actions.args()
    args.add("--input", ctx.file.src)
    args.add_all(ctx.files.includes, before_each = "--include")
    args.add("--output", out)
    tool = ctx.attr.tool[DefaultInfo].files_to_run
    ctx.actions.run(
        executable = tool,
        tools = [tool],
        inputs = depset([ctx.file.src] + ctx.files.includes),
        outputs = [out],
        arguments = [args],
        env = {"LC_ALL": "C", "TZ": "UTC"},
        use_default_shell_env = False,
        mnemonic = "GenerateExampleHeader",
    )
    return [DefaultInfo(files = depset([out]))]

generated_header = rule(
    implementation = _generated_header_impl,
    attrs = {
        "src": attr.label(allow_single_file = True, mandatory = True),
        "includes": attr.label_list(allow_files = True),
        "tool": attr.label(executable = True, cfg = "exec", mandatory = True),
    },
)
```

Use generated_header with src/includes/tool in BUILD; consume :schema in hdrs or private srcs. Build generators with native cc_binary/py_binary rules; export source-built ELF using the shared Trixie sysroot through source_build_tool. The tool declares its interpreter/imports/data; callers pass complete FilesToRunProvider. Declare subprocesses as exec tools with explicit paths and provide libraries/templates as runfiles or inputs. Source-built and prebuilt dynamic ELF both need matching execution loaders/libraries, resolved by the launcher from declared locations.

Launchers locate dependencies through their own .runfiles or an enclosing runfiles tree. Before changing directories, make tool paths absolute while preserving executable symlinks; Python may use Path(tool).absolute(). Resolving to the real file loses the invocation path's runfiles semantics.

For multiple execution implementations, register toolchain_type, ToolchainInfo and toolchain targets carrying tool Targets/data. exec_compatible_with constrains tool OS/CPU; target differences use target constraints. Consumers declare toolchain types and obtain closures through ctx.toolchains. Fixed tools need no ceremonial new toolchain.

## Hermeticity checks

| Boundary | Declaration or evidence |
| --- | --- |
| Identity | Pinned origins/checksums for generators, plugins, interpreters and libraries |
| Files | Direct/transitive inputs in action inputs; directory strings are not dependencies |
| Tool closure | FilesToRunProvider, runfiles, subprocesses, loaders, templates/plugins |
| Environment | Required values only; locale/timezone/timestamp/randomness contract, no whole client environment |
| Outputs | Fully declared; action-private temporary files, no source/shared fixed /tmp writes |
| Paths | File.path/Args with spaces/nesting handled, independent of workspace absolute position |
| Network | Pin repository inputs; generation/compilation performs no online dependency installation/download |
| Platforms | Independently resolve exec tools/target inputs; host tool CPU does not imply target CPU |

Inspect aquery textproto tools, inputs, arguments and environment, then use the project's strict sandbox. Verify success with complete inputs, failure for missing required inputs, and output/action changes after template/transitive-header changes. processwrapper proves only that execution mode. Fix realpath escapes in tools/shared interfaces rather than copying trees. Test remote/other platforms only when requested and report unexecuted checks accurately.

## Target-toolchain Autoconf analysis

Follow [controlled Autoconf probing](autoconf-probe.md): declare sources, target CcInfo/pkg-config files and original feature settings; autoconf_probe exports the selected full toolchain/dependency environment, builds argv launchers, isolates pkg-config and runs out-of-tree configure. Save environment/probe evidence, map necessary values to BUILD/templates and validate native consumers.

Keep probe workspace/entries/reports temporary from creation; regular components retain native targets/templates only. Cross runtime probes use matching target execution or sourced cache answers. Recheck affected probes when original inputs change. The complete example orders aquery, probing, templates and consumers.

References: [actions](https://bazel.build/rules/lib/builtins/actions), [toolchains](https://bazel.build/extending/toolchains), [Autoconf cross compilation](https://www.gnu.org/software/autoconf/manual/autoconf.html#Specifying-Target-Triplets).
