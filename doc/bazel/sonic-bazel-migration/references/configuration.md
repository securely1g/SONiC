# Migrate Make configuration and feature switches

Read the entire [shared contract](common-contract.md), then applicable sections here. Preserve the configuration surface actually exposed by the original SONiC entry: configurable inputs become settings; hardcoded parameters stay fixed. New product configuration requires explicit user requirements.

## Establish the original configuration contract

Trace rules/config, platform rules, slave.mk, wrappers and component sub-builds. A variable or upstream configure option is only a clue; actual accepted SONiC inputs and effective behavior define the boundary. A wrapper's fixed --enable-foo remains fixed even if upstream supports disabling it.

Record evidence in analysis.json build_steps/compile_commands/generated_files and mappings in implementation.json, with one source of truth. For each setting record:

- Original variable/entry, type/legal values, default, empty semantics, assignment and override order.
- Platform/distribution conditions, propagation, effective rule and evidence.
- Affected sources, macros, headers/libraries, generated files, packages, assembly and services.
- Classification as user setting, platform-derived, fixed or probed; corresponding Bazel label/declaration and consumers.

Interpret y/n, unset, empty and other values by actual Make conditions before choosing Bazel types. Global defaults/platform overrides jointly define behavior. Preserve dependencies, exclusions and invalid-combination diagnostics.

## Admission requirements for new Bazel switches

Before declaring bool_flag, string_flag, label_flag or another setting that changes component features, complete these checks. Reference analysis evidence in implementation's configuration mapping. The lead checks this before delegating implementation and at handoff; settings that fail admission stay outside implementation and mandatory acceptance.

1. **Identify the actual entry.** Trace this task's SONiC target through wrappers, Debian rules and final configure/compile/install calls. Record effective arguments, defaults and override order.
2. **Prove that the entry is configurable.** Identify an explicitly accepted interface and its propagation to the final consumer. An upstream option, a theoretically command-line-overridable Make variable or a possible environment override alone does not prove this capability is exposed by the actual entry.
3. **Establish both effective states.** Record enabled and disabled values and effects. Wrapper-fixed arguments and unpassed upstream options with fixed defaults remain fixed parameters. Architecture differences are platform-derived. Only genuinely exposed variation becomes a Bazel switch.
4. **Preserve one consumption chain.** List affected macros, sources, dependencies and installation for each state and their Bazel mapping. Trace feature switches, debug information, optimization and stripping separately; the word debug does not make them equivalent.

Record entry/source locations, input interface, propagation, effective states, classification, Bazel expression and acceptance. Continue analysis for missing evidence; report concrete gaps rather than inventing switches. Explicitly requested new capabilities have separately identified scope.

Unused upstream branches may remain analysis clues. Do not expose them as new settings or classify failures from voluntarily enabling them as regressions in the actual migrated flow or mandatory acceptance. If a switch was added incorrectly, remove it, its selection branches, documentation and mistaken acceptance cases, restoring original effective parameters. Preserve experiment records and correct attribution rather than changing component sources to make the unintended switch pass.

## Implement at the owning layer

| Original behavior | Bazel expression |
| --- | --- |
| Fixed macros/options/features | BUILD attributes or necessary shared constants; pass template substitutions |
| Accepted Boolean/enum inputs | bool_flag/string_flag, config_setting/select; constrain enum values |
| Selectable implementation | Existing label_flag or constrained mapping |
| Architecture/distribution/toolchain differences | Platform constraints and toolchain-derived attributes |
| Optional installed components | select in image dependencies/layers/manifests |
| Configurable startup defaults | Generated service lists/templates/runtime configuration |
| Capability probes | Confirmed rule attributes and native configuration generation under [Autoconf](implement-component.md#autoconf-configuration-generation) |

Derive original architecture-specific constants from platforms. Compute versions/paths from their original authority and bind probe results to inputs. Derived/platform/probed values do not require new user switches. Propagate settings through compilation and assembly consumers. Requested targets determine compilation; optional installation belongs to assembly while component targets remain independently buildable. The scheduling graph retains the union across conditions.

## Rule declarations

Inspect existing project/selected-version configuration. Reuse only matching semantics, defaults and consumers. Shared infrastructure owns global product settings; component modules own component settings. Keep one source per feature with valid cross-module labels and verify actual consumption even for matching names.

Example only where original ENABLE_FOO=y/n defaults to n and controls a macro/dependency:

```starlark
load("@bazel_skylib//rules:common_settings.bzl", "bool_flag")

bool_flag(name = "foo", build_setting_default = False)
config_setting(name = "foo_enabled", flag_values = {":foo": "true"})

# Place in actual compilation target attributes; retain fixed parameters in the constant portion.
# copts = ["-DFIXED_FEATURE=1"] + select({
#     ":foo_enabled": ["-DENABLE_FOO=1"],
#     "//conditions:default": [],
# })
# deps = select({
#     ":foo_enabled": ["//foo:library"],
#     "//conditions:default": [],
# })
```

Disabled behavior may omit a macro, define zero or select other sources; preserve exact original semantics. Put final values in BUILD attributes/template substitutions. Keep evidence under the [declaration boundary](implement-component.md#build-declarations-and-analysis-evidence-boundary). Declare actual template inputs and build-setting dependencies for custom rules. Named .bazelrc configurations combine existing parameters; actual entries ensure defaults.

## Complete cross-module compilation-to-assembly example

Assume original ENABLE_FOO=y/n defaults n and controls a native macro and container configuration. example-config owns the setting; example-component owns code; the image is the root. Substitute actual identities/defaults/conditions.

Public config/BUILD.bazel:

```starlark
load("@bazel_skylib//rules:common_settings.bzl", "bool_flag")
package(default_visibility = ["//visibility:public"])
bool_flag(name = "foo", build_setting_default = False)
config_setting(name = "foo_enabled", flag_values = {":foo": "true"})
```

Component and image MODULE both directly declare it with one alias:

```starlark
bazel_dep(name = "example-config", version = "CONFIG_VERSION", repo_name = "example_config")
```

Component BUILD applies the same condition to core.cc's original macro:

```starlark
load("@rules_cc//cc:cc_library.bzl", "cc_library")
cc_library(
    name = "library",
    srcs = ["core.cc"],
    local_defines = select({
        "@example_config//config:foo_enabled": ["ENABLE_FOO=1"],
        "//conditions:default": [],
    }),
    visibility = ["//visibility:public"],
)
```

Image package foo.conf has a fixed contractual TAR path/mode; the same condition controls installation:

```starlark
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")
load("@rules_oci//oci:defs.bzl", "oci_image")

pkg_tar(
    name = "foo_config",
    srcs = ["foo.conf"],
    package_dir = "/etc/example",
    mode = "0644",
    owner = "0.0",
)
oci_image(
    name = "image",
    base = "@debian//image",
    tars = ["@example_component//:runtime"] + select({
        "@example_config//config:foo_enabled": [":foo_config"],
        "//conditions:default": [],
    }),
)
```

Prepare @debian//image and component runtime TAR under [OCI](oci.md). The root directly declares example-component and its runtime builds this library. Complete OCI metadata/accounts/runtime closure under that route.

From the image root, use the same public setting and platform arguments:

```bash
bazel build //image:image --@example_config//config:foo=false
bazel aquery 'deps(//image:image)' --@example_config//config:foo=false --output=textproto
bazel cquery 'deps(//image:image)' --@example_config//config:foo=false
bazel build //image:image --@example_config//config:foo=true
bazel aquery 'deps(//image:image)' --@example_config//config:foo=true --output=textproto
bazel cquery 'deps(//image:image)' --@example_config//config:foo=true
```

Check default=false. true adds ENABLE_FOO=1 to compile actions, selects foo_config and installs /etc/example/foo.conf. false changes both according to original semantics. Build the independent component library with the same public setting label. Make maps y to true and n to false, sharing arguments between build/cquery; handle other values by original validation. Do not duplicate the setting in component/image.

## Transitional Make entry

Where requested, wrappers map Make inputs to explicit Bazel arguments and share them between build/cquery; direct Bazel settings give equivalent behavior. Explicit arguments preserve action/cache input identity. Apply the mapping only within the wrapper's supported matrix and diagnose unsupported combinations. Record native Bazel support separately.

## Acceptance

Check original defaults, legal values and necessary combinations through actual actions, templates, dependencies and contents. Verify each switch's enabled/disabled behavior and cross-module consumers; diagnose invalid combinations. Check fixed semantics, platform derivation and probe applicability. Record original settings, commands, selection and [acceptance evidence](review-port.md).
