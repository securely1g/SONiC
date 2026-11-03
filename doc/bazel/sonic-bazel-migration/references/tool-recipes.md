# Tool references and invocations

Read the [shared contract](common-contract.md) and applicable sections. Apply [hermetic actions](hermetic-tools.md). This reference does not authorize old configure/Make pipelines in regular builds.

## Obtain correct tool targets

1. Declare actual required modules/repo aliases with pinned versions, including direct infra/SWIG/tar/rules_python dependencies.
2. Read pinned BUILD/rule sources and verify executable/FilesToRunProvider/interpreters/templates/libraries; selected versions determine APIs/tool availability.
3. Use tools or executable=True,cfg=exec. Target libraries belong in deps; data-only placement/copying is insufficient.
4. Prefer existing project/shared targets, then BCR, then pinned sources. Producers propagate closure.

```sh
bazel query '@sonic_build_infra//tools/build_tools:*'
bazel query --output=build '@sonic_build_infra//tools/build_tools:bison'
bazel cquery --output=files '@sonic_build_infra//tools/build_tools:bison'
```

Queries prove declarations, not executable closure. Check exec actions. This table locates APIs rather than prescribing upgrades/versions.

| Tools | Entry | Additional inputs |
| --- | --- | --- |
| Bison/Flex/M4/Perl/pkgconf | Infra tools/build_tools same-name targets | Skeletons/M4/modules/exec libraries |
| Autoconf/autoheader/autom4te | Same package | Macros/scripts/Perl |
| autoreconf/automake/aclocal/libtoolize | Same-name targets | Macros/auxiliaries/subtools |
| protoc/gRPC/Thrift | protoc/grpc_cpp_plugin/grpc_python_plugin/thrift or selected module | Compatible plugins/IDL/templates; [generation](code-generation.md) |
| SWIG | @sonic_build_infra//tools/build_tools:swig; language templates such as @swig//:lib_python | Source-tool launcher, SWIG_LIB, headers/macros/runtime |
| patchelf/gawk | @sonic_build_infra//tools/build_tools:patchelf and :gawk | Shared sysroot loader/libraries and original binary runfiles |
| Doxygen/Aspell/Graphviz | doxygen/aspell/dot | Dictionaries/fonts/plugins/config/runtime |
| Sphinx/makeinfo | sphinx-build/makeinfo | Python extensions/themes/Texinfo/locale/subtools |
| compile_et/mk_cmds | Same-name targets | Templates/actual awk/sed subtools |
| readelf/objcopy/objdump | Infra binutils toolchain_type | Target-aware tool/exec closure |
| TAR/compression | tar.bzl rule or tar_lib.toolchain_type | Archive toolchain/compressors/closure |
| Filesystem/partition/qemu/boot/signing | Actual image exec attributes/producers | Libraries/GRUB/certificates/platform data |

## Add and consume host tools

### Invoke existing tools

Prefer the public infra executables above. genrule uses tools; custom rules declare executable=True,cfg="exec" and pass DefaultInfo.files_to_run. A single-tool action may use that provider as executable; see the [minimal action](hermetic-tools.md#minimal-tool-action-rule). Drivers invoking several tools pass tool.executable as the path and the complete provider in tools. A bare File omits execution dependencies. Target headers/libraries remain target-configured consumer dependencies.

### Add source tools or component generators

Declare the source binary with original versions/patches, then export through the shared API. Reusable tools belong in infra; component generators stay in their source repository. Both use source_build_tool. Example tablegen.cc accepts an input path and writes generated output to stdout:

```starlark
load("@rules_cc//cc:cc_binary.bzl", "cc_binary")
load("@sonic_build_infra//tools/build_tools:defs.bzl", "source_build_tool")

cc_binary(
    name = "tablegen_binary",
    srcs = ["tablegen.cc"],
    # Put support libraries in deps; declare templates, data and plugins in data as actually read.
)
source_build_tool(
    name = "tablegen",
    binary = ":tablegen_binary",
)
genrule(
    name = "table_header",
    srcs = ["schema.txt"],
    outs = ["table.h"],
    tools = [":tablegen"],
    cmd = '"$(location :tablegen)" "$(location schema.txt)" > "$@"',
)
```

binary and its runtime use exec configuration/architecture. Cross builds run the generator on the executor and compile results for target. The interface retains binary runfiles and selects shared Trixie execution libraries, without private loader/LD_LIBRARY_PATH scripts. Producers still declare additional libraries/templates/plugins/subtools. Other languages follow actual SDK runtime contracts; rules_python still supplies py_binary interpreters/modules.

### Add DEB tools

1. Establish actual program/data packages from analysis. Extend infra apt/requests.json and the common lock under [locking](dependency-locking.md), preserving existing versions and adding only required closure.
2. Connect fixed exec packages in MODULE and tools/build_tools/BUILD. Select an appropriate runtime group and declare complete data/interpreter/library/subtool inputs.
3. Maintain executable entries, data paths and manifests in the corresponding prepare_runtime.py group. Shared launchers own special environment/search behavior. Declare required post-install alternatives/plugin indexes and check relocatability.
4. Once a manifest key exists, export build_tool in that package. tool is the key; runtime is its prepared tree. Package inputs alone do not create a public executable:

```starlark
load(":defs.bzl", "build_tool")

# First register example_tool and its closure in configure_runtime preparation.
build_tool(
    name = "example_tool",
    tool = "example_tool",
    runtime = ":configure_runtime",
    visibility = ["//visibility:public"],
)
```

### Select wrapped tools in third-party rules

Pass infra targets to executable attributes while retaining FilesToRunProvider. Shared tool selection may reuse the owning module's toolchain: infra registers a wrapped implementation and consumers use resolved tools/runfiles. Producers reference original binaries; only consumers reference wrapped/selected entries, preserving dependency direction.

For gawk, tar.bzl and rules_distroless use @gawk//:resolved_toolchain. Infra provides //tools/build_tools:gawk_toolchain. Consumer roots explicitly register it before the original fallback:

```starlark
register_toolchains("@sonic_build_infra//tools/build_tools:gawk_toolchain")
```

Verify selected gawk, tar.bzl and rules_distroless revisions provide these interfaces and propagate runfiles. Older private defaults may still select bare binaries. Inspect every real call path, repair the owning producer/consumer where needed, then validate actual root selection. Native language rules continue to produce binaries.

### Validate and hand off new tools

Run tools on the agreed execution platform, then inspect actual outputs/consumers. For source tools verify compilation sysroot and execution loader/libraries. If older host glibc is relevant, run there directly; success inside full Trixie proves that environment only. Cover actual arguments/paths/directories/data/subtools/failures/required cross configurations. Version output is startup evidence, separate from generation/modification/consumer checks. Recheck existing DEB consumers after shared launcher changes and record actual platform coverage/gaps. Preserve configuration/lock/registry identities and evidence under their respective policies.

## Bison and Flex

Follow [generation steps](code-generation.md#procedure). Extract language/prefix/header/location/reentrant options from original .y/.l. Bison templates/M4 are managed. Example two C sources/two headers:

```starlark
load("@rules_cc//cc:cc_library.bzl", "cc_library")

genrule(
    name = "parser_generated",
    srcs = ["parser.y"],
    outs = ["generated/parser.c", "generated/parser.h"],
    tools = [
        "@sonic_build_infra//tools/build_tools:bison",
        "@sonic_build_infra//tools/build_tools:m4",
    ],
    cmd = 'M4="$(location @sonic_build_infra//tools/build_tools:m4)" ' +
          '"$(location @sonic_build_infra//tools/build_tools:bison)" ' +
          '--defines="$(location generated/parser.h)" ' +
          '--output="$(location generated/parser.c)" "$(location parser.y)"',
)
genrule(
    name = "lexer_generated",
    srcs = ["lexer.l", "generated/parser.h"],
    outs = ["generated/lexer.c", "generated/lexer.h"],
    tools = ["@sonic_build_infra//tools/build_tools:flex"],
    cmd = '"$(location @sonic_build_infra//tools/build_tools:flex)" ' +
          '--header-file="$(location generated/lexer.h)" ' +
          '--outfile="$(location generated/lexer.c)" "$(location lexer.l)"',
)
cc_library(
    name = "parser",
    srcs = ["generated/parser.c", "generated/lexer.c"],
    hdrs = ["generated/parser.h", "generated/lexer.h"],
    strip_include_prefix = "generated",
    visibility = ["//visibility:public"],
)
```

Original noyywrap requires no libfl; otherwise declare real yywrap/libfl implementations. Declare includes/skeletons, align headers/prefix/ABI and verify compilation/valid parsing/invalid diagnostics/repeated output stability.

### Minimal joint-generation input and invocation

parser.y in the same package:

```text
%{
#include <stdio.h>
int yylex(void);
void yyerror(const char *message);
%}
%token NUMBER
%%
input: NUMBER '\n' ;
%%
void yyerror(const char *message) { fprintf(stderr, "%s\n", message); }
```

lexer.l:

```text
%option noyywrap
%{
#include "parser.h"
%}
%%
[0-9]+  return NUMBER;
[ \t]+  ;
\n      return '\n';
.       return yytext[0];
%%
```

parser_main.c:

```c
int yyparse(void);
int main(void) { return yyparse(); }
```

Add entry:

```starlark
load("@rules_cc//cc:cc_binary.bzl", "cc_binary")
cc_binary(name = "parser_check", srcs = ["parser_main.c"], deps = [":parser"])
```

Input 42 followed by newline succeeds; x followed by newline diagnoses syntax and exits nonzero. Connect behavior to existing tests. Real lexing/semantic values/locations/reentrancy/error recovery follow analysis.

## M4, Perl and project generators

Preserve original includes/macros/expansion order. Fixed expansion:

```starlark
genrule(
    name = "expanded_text",
    srcs = ["schema.m4", "common.m4"],
    outs = ["schema.txt"],
    tools = ["@sonic_build_infra//tools/build_tools:m4"],
    cmd = '"$(location @sonic_build_infra//tools/build_tools:m4)" ' +
          '"$(location common.m4)" "$(location schema.m4)" > "$@"',
)
genrule(
    name = "perl_generated",
    srcs = ["generate.pl", "schema.txt"],
    outs = ["generated.h"],
    tools = ["@sonic_build_infra//tools/build_tools:perl"],
    cmd = '"$(location @sonic_build_infra//tools/build_tools:perl)" ' +
          '"$(location generate.pl)" "$(location schema.txt)" > "$@"',
)
```

Perl example accepts an input path and writes stdout. Declare imported modules/runtime/include roots without inherited PERL5LIB. Declare M4 include files and logical roots. Shell only invokes declared tools/redirection, not downloads/scans/probes.

Project Python tools use py_binary srcs/deps/data/main and pass the target to [actions](hermetic-tools.md#minimal-tool-action-rule). C/C++/Go/Rust generators use native binaries with [source-tool execution closure](#add-source-tools-or-component-generators), then run in exec configuration. Trace FRR clippy's source production and create an independent exec target, not host names/target executables. Rust Clippy is distinct and uses matching SDK rules only when requested.

## pkg-config and pkgconf

Use infra pkgconf. Regular C/C++ consumes exported CcInfo, not host pkgconf stdout. Controlled analysis declares target .pc closure/sysroot/dependencies:

| Setting | Source |
| --- | --- |
| PKG_CONFIG | Declared executable |
| PKG_CONFIG_LIBDIR | Declared target search directories |
| PKG_CONFIG_PATH | Empty or contractual target overrides only |
| PKG_CONFIG_SYSROOT_DIR | Selected target sysroot |
| cflags/libs/static | Original link mode |

Save returned options/order and compare actual actions. Follow Requires/Requires.private/Libs.private; returned paths must be declared target inputs, not host libraries.

## Autotools analysis tools

Use declared autoconf/autoheader/autom4te/autoreconf/automake/aclocal/libtoolize/M4. Set corresponding environment variables to declared paths and tool-only search roots. Declare configure.ac/Makefile.am/aclocal.m4/macros/auxiliaries. Follow original bootstrap order and check whether existing configure requires regeneration. [Probe](hermetic-tools.md#target-toolchain-autoconf-analysis) with bound compiler/sysroot. Keep analysis temporary; regular builds retain native/template actions.

## Documentation tools and data

| Tool | Minimal invocation | Required inputs |
| --- | --- | --- |
| Doxygen | Generated Doxyfile | Sources/headers/version/layout/images/filters |
| Sphinx | sphinx-build -b html ROOT OUT | conf.py/docs/themes/extensions/templates/static |
| makeinfo | --no-split -o OUT INPUT | texi/transitive includes/images/options |
| Graphviz | dot -Tsvg INPUT -o OUT | Graph/fonts/plugins/libraries |
| Aspell | Original noninteractive list/check | Language/dictionaries/wordlists/config/input |

Use public labels and declared files/directories. Generate Doxygen paths from actual Files and declare dot/filters/closure. Executable Sphinx conf.py imports/themes/autodoc need exec Python; target native extensions cannot load into it directly. Declare compression separately for makeinfo. Use supported out_dirs; stdout/chdir may require the execution-wrapper toolchain. Pass full runfiles through FilesToRunProvider. Check page/info contents/resources/version, not file counts alone.

## compile_et and mk_cmds

Use public targets and original et/ct/prefix/templates/directory. Connect C/headers to srcs/hdrs with transitive includes/templates. If tools only write beside inputs, fix output-path APIs rather than copying source trees. Declare target libcom_err/libss through source/APT interfaces separately from exec libraries. Verify error-code/command-table behavior and ABI.

## binutils, archives and compression

Use target-compatible binutils toolchains; cfg=exec alone does not prove target understanding:

```starlark
load("@sonic_build_infra//toolchains/binutils:binutils_toolchain.bzl", "BINUTILS_TOOLCHAIN_TYPE")

def _elf_without_debug_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name + ".elf")
    tool = ctx.toolchains[BINUTILS_TOOLCHAIN_TYPE].binutils.objcopy
    ctx.actions.run(
        executable = tool,
        tools = [tool],
        inputs = [ctx.file.src],
        outputs = [out],
        arguments = ["--strip-debug", ctx.file.src.path, out.path],
        env = {"LC_ALL": "C"},
        use_default_shell_env = False,
    )
    return [DefaultInfo(files = depset([out]))]

elf_without_debug = rule(
    implementation = _elf_without_debug_impl,
    attrs = {"src": attr.label(allow_single_file = True, mandatory = True)},
    toolchains = [BINUTILS_TOOLCHAIN_TYPE],
)
```

This illustrates toolchain access only. Production runtime/symbols use sonic_deploy_tar/strip_binary. Manual readelf may use the infra runner with matching platform. ar/ranlib come from actual C++ toolchain; native cc builds archives. sonic_deb owns final DEB packaging.

Prefer existing archive/compression rules:

```starlark
load("@tar.bzl//tar:tar.bzl", "tar")

tar(
    name = "resources",
    srcs = ["default.conf"],
    compress = "gzip",
)
```

Declare mtree installation. Justified custom actions obtain tar and runtime through toolchains. Separate gzip/xz/zstd/pigz targets need verified versions/closure and original format/level/dictionary/timestamp/thread semantics. GNU cpio/newc may use existing newc rules directly rather than duplicate tools; see initramfs acceptance.

## Image, filesystem and signing tools

Inspect actual image executable/toolchain attributes and producers; roles below are not guessed labels.

| Role | Tool | Contract |
| --- | --- | --- |
| mke2fs/debugfs | e2fsprogs | Rootfs/config/population/filesystem parameters |
| sgdisk | GPT fdisk | Layout/offset/size/UUID/disk |
| mkfs_fat/mcopy/mmd | FAT/mtools | EFI files/FAT parameters |
| qemu_img | qemu-img | Explicit input/output format, e.g. raw->qcow2 |
| grub_mkimage/editenv | GRUB | Platform/modules/config/boot closure |
| depmod/modprobe | kmod | Target modules/release/explicit root, no host module tree |
| openssl/signing_tool | Selected implementation | Algorithm/cert/key/payload, signature/image |
| Compressors | Managed tools | Source layers/dictionaries/options/output |

Use existing pinned APT/BCR/source tools in priority order. New APT tools retain locked packages and add only new inputs. Export full loaders/libraries/data/subtools, GRUB modules/fonts/config, mke2fs.conf and OpenSSL providers/config as needed. Keys follow authorized execution contracts and never appear in logs. Pass exec attributes and continue [image assembly](image-recipes.md).

## Completion

Record module identity/public label/toolchain/attribute/closure/direct-transitive inputs/outputs/consumers in implementation. New tools must run on exec, process target files and fail missing-required inputs; inspect actual aquery data. Installed tools or matching labels alone do not establish completion.

Reference: [Flex output options](https://westes.github.io/flex/manual/Options-for-Specifying-Filenames.html).
