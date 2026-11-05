# Analyze the original Make build

Read the entire [shared contract](common-contract.md) first, then the applicable sections here.

Before implementation, establish the exact original build contract for every condition required by the task. Read sources and rules first; existing logs and artifacts support checks. Record actual build validation separately.

## Inputs and outputs

Inputs are the component task identity, artifact list, rule locations, source directories, dependency subgraph and prerequisite analyses. Check repository commits and working changes to identify the analyzed version. A single-component analysis records consumed dependency interfaces and remains within that component.

Store outputs under `components/<component-id>/` in the task's temporary directory. Follow [phase handoff](phase-handoff.md) for references and status updates:

- `analysis.json`: structured analysis source of truth.
- `analysis.md`: readable conclusions, environment inputs, evaluation rules and evidence derived from that record.
- `evidence/`: larger manifests, package metadata, compile commands and logs.

Use a safe directory representation of the stable task identity; retain the original mapping and check collisions. Keep all outputs inside the task directory.

## Directories and code ownership

Trace `rules/*.mk`, platform rules, `slave.mk` and invoked sub-builds to identify:

- `rule_locations`: files and lines declaring components and dependencies.
- `build_directories`: actual entry points and working directories, including wrapper Makefiles.
- `source_locations`: source/submodule paths or extracted directories and how they are determined.
- `repositories`: URLs, commits, submodule versions and local modifications.
- `write_scope`: planned files/directories, used to check concurrent writing conflicts.

For undownloaded sources, record their declarations, expected directories and current readable scope. Component type and registered production objects determine task identity; artifact lists retain co-production relationships. Original package names, formats and co-production are analysis facts. Map native contents to OCI-consumable TARs and native interfaces; map Python distributions to owner wheels installed through shared wheel_layer; produce final DEBs only when explicitly requested. A shared .mk file or source directory does not make independent production objects one component.

## Analysis record contents

At the top level, record `task_id`, `repository_state`, `required_conditions`, `analysis_status`, `evidence`, `unresolved`, `execution_validation` and the groups below. `unresolved` contains build-rule questions only. `execution_validation` records actual build/artifact checks separately and accurately retains unexecuted status. Facts/groups include `state` (confirmed, unconfirmed or not applicable), `value`, `conditions` and evidence references; explain inapplicability. Explain whether an empty list means confirmed absence or pending investigation.

| Group | Required information |
| --- | --- |
| `identity` | Component, primary package, component version and calculation, source version |
| `classification` | Languages, source/prebuilt/Linux-kernel classification, actual build system |
| `locations` | Rules, build/source directories, repository owners, planned write scope |
| `outputs` | Complete package/artifact list, names, formats and co-production of primary/development/debug packages, wheels and archives |
| `package_contents` | Per-package manifests, source-to-install mappings, glob selection, deletion/exclusion, modes, ownership and links; exact rule-defined contents |
| `package_metadata` | Name, version, architecture, dependencies, description, license, maintainer scripts/triggers; dynamic field generators, inputs and execution stages |
| `source_acquisition` | Online/local/submodule/prebuilt origin, URLs, versions, checksums, mirrors/fallbacks, download/extraction steps; each archive path, extraction destination, consumer and commit ownership; follow downloader auxiliary inputs |
| `patches` | Files, origins, order, conditions, stage and application method |
| `sources` | Complete per-target source/header/resource declarations, include chains, variable references, assignment order, selection/exclusion; original versus generated inputs |
| `generated_files` | Generators, inputs, outputs, commands, stages and conditions for intermediate sources, headers and configuration |
| `build_steps` | Actual prepare/configure/compile/install/package entry points, commands, environments and output handoffs |
| `compile_commands` | Compiler/linker selection and command formation, global/target options, override/append order, directories, environment, response-file formation and branches |
| `host_tools` | Build-time tools, versions, actual origins, stages, execution dependency closure and planned Bazel targets; target versus exec roles; existing-rule/BCR/source selection and base-tool contract |
| `dependency_interfaces` | Per-consumer headers/sets, generated headers, include names/search order; library names, static/shared forms, SONAME, link options/order; origin, role, version and use site |

Keep generated intermediates in `generated_files` and final deliverables in `outputs`, connected by mappings. Put large manifests in `evidence/`, with relative paths and provenance in JSON and linked conclusions in the report. Disk enumeration and keyword matches are clues; final sources/options must be tied to targets and effective rules.

## Analysis method

Check origins, ordering, conditions and input trees with [source and patch preparation](source-and-patches.md). Distinguish already merged fixes, registry patches and original Make patches; hand off the full production path.

1. Trace registration and production rules to actual compilation/packaging entries. Read invoked Makefiles and Debian, Autotools/CMake, Go, Cargo and Python declarations; explain each artifact's production path.
2. Pin program sources, Debian packaging, generators and auxiliary inputs independently. Local sources and online packaging may coexist. Build the [input origin inventory](source-and-patches.md#handoff-from-make-analysis-to-bazel-acquisition), separating external extracted files from repository-maintained files. For dget/.dsc, parse source-package members and automatic patch stages; hand off pinned inputs and reproducible preparation. Combine outer quilt, Debian patches, StGit and wrapper-applied patches in execution order. Analyze effective patched rules. If patch validation is needed, use a temporary copy, apply the original order and save individual results while preserving original sources. Patch titles are descriptions; derive behavior from final code, defaults and branches.
3. Follow actual include chains and source/header variables per target. Preserve assignment operators, ordering, conditions and selection. Trace generated inputs to producers/commands; distinguish generation, template expansion and copying.
4. Trace full compile/link option formation: outer environment/options, configuration calculations/probes, global options, target overrides/appends, final command templates and working directories. Separate execution tools and target code.
5. Trace primary/derived packages, install manifests/transformations, exclusions/deletions, permissions/accounts, metadata and maintainer scripts. Preserve dynamic-dependency/version substitution calculations. Distinguish built artifacts from delivered packages.
6. Establish defaults and optional behavior separately. For environment-dependent values, record inputs, origins, expressions/probe rules and consumers. Parameterized rules are valid conclusions; an unexecuted environment neither replaces analysis nor permits invented concrete values.
7. Record dependency headers/libraries per consumer: `-I`/`-isystem`/`-iquote`/sysroot, forced/generated/public header naming, actual link forms, SONAME and ordered linker state options. Follow injection paths to distinguish SONiC source components, system packages and toolchain inputs; equal names do not prove equivalent origins. Report newly discovered SONiC relationships to the lead. Keep single-component scope; record system tools/development libraries in that component's report.

For genuinely indeterminate rules, continue along the invocation chain and identify the exact expression, missing input or unreadable file and its effect. Report concrete blockers, continue independent work and retain incomplete status. A status change does not resolve a rule question.

Retain original host-tool origins as facts. Hand off preferred existing Bazel rules, versions, execution platforms and input closures. If unsuitable, record BCR investigation and source-build selection rationale. Pinned DEB extraction may be reused. Component steps still map to native generation, compile, link and packaging actions.

## Dependency locking inputs

Follow [dependency locking](dependency-locking.md) to identify original requests, resolved versions, checksum files, sources, SDK/interpreter/platform constraints, actual consumers and lock ownership. Record the Go version graph separately from go.sum verification. Hand off Cargo features and declarations with locks. Preserve original dependency identity during analysis; relock and validate implementation changes.

## Configuration boundary handoff

Follow [configuration](configuration.md) for original inputs, defaults, override order and consumers. Distinguish user configuration, platform derivation, fixed options and probe results, with sourced mappings. Wrapper-hardcoded upstream options remain fixed behavior; preserve the original configurable surface.

For Thrift, protoc and SWIG, follow [code generation](code-generation.md) to trace generators, plugins/templates, transitive IDL/headers, output paths and target runtimes. Derive versions/options from effective original Make configuration.

## Autoconf probe handoff

Use [target-toolchain Autoconf analysis](hermetic-tools.md#target-toolchain-autoconf-analysis) for environment preparation, toolchain extraction, configure options and result classification. Confirm real target compilation/link inputs before interpreting probes.

List configure.ac/m4, templates, configuration outputs and effects on sources, compile/link options and installation. Per setting, record probe rules, inputs and consumers; distinguish toolchain/dependency capability, architecture, user features and environment paths. Follow [implementation](implement-component.md#autoconf-configuration-generation) for controlled migration-time probing and template generation. Keep probe scripts, raw results, complete input identities, commands and config.log/config.status in the temporary analysis directory. Hand off necessary values separately from evidence under the [declaration boundary](implement-component.md#build-declarations-and-analysis-evidence-boundary). Distinguish host, execution tools, target userspace and containers under [environment records](review-port.md#environment-records); record execution in `execution_validation`. Hand off rule analysis and runtime probing separately; obtain applicable evidence before fixing template values.

## Information suitable for automated collection

Prefer existing tools/logs; add helpers only for real repeated collection. Attach commands, exit codes, source versions, conditions and evidence locations.

- Names, versions and dependencies: Make registration, Debian control/changelog, wheel metadata.
- Existing package contents/metadata: dpkg-deb, wheel ZIP and TAR format tools.
- Source identities/origins: submodule records, Git versions, download/checksum declarations.
- Patches: series, conditional rules and actual application order.
- Compile options: existing logs, compile_commands.json, verbose output or reviewed command collection.
- Sources/generated files: declarations, commands, generator rules and files.

Distinguish declared parameters from executed parameters. Record compile and link commands with directory, environment, response files and tool identity. Compile databases alone generally do not cover linking, configuration checks, generation and every language; verify these separately. One build proves execution for its configuration only; cover other conditions through rule analysis or additional execution.

Inspect side effects before build/probe commands, including Make parse-time shell calls. Record missing tools or blocked collection and continue independent static analysis.

## Analysis delivery and task updates

Successful collection yields clues only. Interpret rules and complete each group with confirmed conclusions or justified inapplicability. Tie every conclusion to current source, patch results and locations. Record command logs and measured packages as additional evidence, distinguishing declarations from execution facts.

Before delivery, check:

- All 14 groups are covered and entry points connect through every deliverable.
- Source selection, compile/link options, generation and packaging map to targets and complete references.
- Per-target header, include-search and library-link interfaces are explicit.
- All branches explain behavior and environment inputs/evaluation; file enumeration and candidates do not replace conclusions.
- Patched conclusions match sources; install declarations and metadata generation have provenance.
- No unresolved rule questions remain; JSON, Markdown and readable evidence agree.

Then set `analysis_status=analysis_complete` and `unresolved=[]`; after review, update the component task with analysis path/status. For real blockers, retain analyzing/analysis-blocked status, describe exact questions and continue feasible work. Vague unconfirmed lists are not an analysis delivery.

`execution_validation` records builds, generator runs, tracing and artifact checks. An unexecuted build does not block a completed contract analysis and does not count as build/artifact verification. Report analysis, migration and verification completion separately.
