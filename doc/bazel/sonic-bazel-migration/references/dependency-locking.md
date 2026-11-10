# Lock and refresh dependency inputs

Read the [shared contract](common-contract.md) when dependencies, versions, sources, patches, features/extras, interpreters/SDKs, platforms or repositories change. Resolve affected graphs in their owning repositories, maintain versions/checksums/derived files and verify consumers with pinned tools. APT preserves existing versions except under its explicit source-change policy. [Source/patch changes](source-and-patches.md) retain raw/patch checksums, full order and final identity.

## Three information layers

| Layer | Responsibility | Examples |
| --- | --- | --- |
| Requests | Direct dependencies/constraints/features/origins | apt.install, requirements.in, go.mod, Cargo.toml |
| Deterministic inputs | Resolved direct/transitive identities/checksums | apt.lock.json, requirements_lock.txt, go.mod/sum/ZIP sums, Cargo.lock |
| Bazel resolution/exports | Locked inputs -> repositories/targets and actual selection | apt.import_lock/apt_inputs, Go plans, from_cargo, MODULE lock/graph |

Check versions and hashes independently; module/language/APT versions differ. Relocking resolves/validates affected closure while preserving unrelated versions. New dependencies do not authorize graph-wide upgrades. Record real no-diff results and retain files. Never invent hashes or delete locks to upgrade implicitly. Pin Git/URL revision/content; local replacements need commits/change identity, not directory names alone.

## Version selection criteria

1. Inherit effective original direct/transitive versions, origins and patches. Inspect existing locks/consumers and distinguish declared ranges, actual resolutions and SONiC-patched inputs.
2. Preserve existing locks as starting points. No latest/unbounded upgrade or full regeneration merely for Bazel/rule/packaging changes.
3. Prefer compatible maintained shared versions after checking constraints/platform/SDK/ABI/features/patches/licenses and origin/content, not version equality alone.
4. Without reuse, choose fixed candidates from actual requirements and verify functionality/compile/link/runtime. Record indeterminate original versions and candidate rationale; one resolution is not automatically the original contract.
5. Prove real SDK/ABI/rule conflicts before minimal authorized changes. Explain every resolver-induced difference; out-of-scope upgrades require authorization and unrelated versions stay fixed.
6. APT keeps versions/checksums, adds only new closure, and re-resolves existing packages only after authorized source changes, not targeted ecosystem-style upgrades.

Record original/selected identities, rationale, affected consumers/configurations and no-diff outcomes in implementation.

## Common locking procedure

Every introduced dependency or consumer entry requires actual ecosystem update/locking, read-only checks and consumer validation in this task, including shared dependencies or expected unchanged locks. Update at the owning entry and inspect selection at new consumers. Existing files/logs do not replace execution. Record command/exit/no-diff evidence. Prepare missing prerequisites or remain blocked. Updating does not imply upgrading.

1. Locate owners, requests, locks, imports and real consumers; pin SDK/interpreter/platform/sources/resolver.
2. Select retained/new/necessary changes with reasons and planned scope.
3. Edit requests and resolve from existing locks; initialize only if absent. Cover runtime/backend/generator/proc-macro/native inputs.
4. Review direct/transitive identities/checksums/platform/features/vendor/build inputs. Investigate unexpected changes before acceptance.
5. Synchronize imports/public targets/derived files; exporting existing locks is not resolution.
6. Check native entries read-only and build/test real Bazel consumers, separately at independent/root entries. Repetition must not drift production files.
7. Check [version-controlled delivery](#version-control-and-handoff-of-locks), recording commands/tools/differences/results/blockers. Missing steps prevent dependency-ready status.

## APT

Apply [fixed inputs](common-contract.md#configuration-and-dependencies): retain existing identities, add new closure only, and require authorization before source changes/re-resolution. Rule/MODULE changes do not authorize APT upgrades.

### One APT lock and three collection roles

Under [APT interfaces](use-apt-libraries.md), images/rootfs consume files, target libraries consume CcInfo and exec tools consume executables. Maintain one infra apt/sources.json and committed apt/apt.lock.json. Unified updates aggregate component requests into multiple sets for runtime/development/tools. Store each package identity once with version/origin/checksum/dependency edges; sets reference it, without per-role/repository duplicate locks. Lock tools for exec and libraries/runtime for target architecture.

The lock records global source input identity and resolved sources. Normal builds read it/check identity; request/source/architecture changes refresh affected sets explicitly. Snapshots plus production locks ensure repeatability; MODULE locks/facts do not replace them. Library export also pins file maps/indexes.

Version-2 apt.import_lock supplies data/control only, without library export file mappings. Development collections expose CcInfo; apt.install declares requests whose production use must bind locked versions/checksums/export inputs. Tools expose launchers/execution runtimes from locked packages. base/Orchagent/syncd-vs use sets in the same lock. Pin sources/sets/package identities/architectures/versions/edges/raw DEB SHA256; extra payload/control hashes depend on actual schemas, not one image's fields universally.

### Lock on each introduction

1. Aggregate apt/requests.json and component apt.install requests with unique sources/production lock. Normal consumption checks request identity. Preserve existing versions/URLs/SHA256.
2. Run the shared updater from infra root. It creates an isolated preparation workspace, uses pinned Distroless apt.export_lock, actually builds @apt_lock_export//:lock, validates and atomically publishes. Facts/MODULE locks are not this output.
3. Review new roots/transitives/architectures/origins/versions/hashes/edges/file maps, preserving fixed-source and unrelated identities. Failed resolution preserves production locks.
4. Run read-only checks and three-role consumers/staleness gates. Normal builds preserve lock digests. Deliver requests/sources/lock/consumption together; generated labels are not a second version list.

After editing `apt/requests.json` or the approved sources, regenerate the lock from the infra
checkout root. The root Bazel workspace imports the previous lock and rejects its stale inputs
before the updater can run. Set `BOOTSTRAP_PYTHON` to the absolute path of a pinned interpreter
provisioned independently of that workspace and `BAZEL` to the absolute path of the selected
Bazel executable. The updater invokes Bazel in its isolated resolver workspace.

```sh
"$BOOTSTRAP_PYTHON" apt/lock.py update --bazel "$BAZEL"
```

Once the reviewed lock matches the inputs, check it through the declared interpreter in infra
revisions that expose the [APT entry point](https://github.com/securely1g/sonic-build-infra/pull/87).

```sh
"$BAZEL" run //apt:lock -- check
```

On earlier revisions use `"$BOOTSTRAP_PYTHON" apt/lock.py check`. This direct invocation also
reports stale inputs inside the checker when the root workspace cannot load the target.

To regenerate against a verified local registry, pass both endpoints in order.

```sh
"$BOOTSTRAP_PYTHON" apt/lock.py update --bazel "$BAZEL" \
  --registry "file://$REGISTRY_SOURCE" \
  --registry https://bcr.bazel.build/ \
  --bazel-startup-option=--batch \
  --bazel-startup-option=--output_base=/tmp/apt-lock-output \
  --work-dir /tmp/apt-lock-prepare
```

The updater generates this preparation MODULE; retain logs/resolution output:

```starlark
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.sources_file(file = "//:sources.json")
apt.install_file(file = "//:requests.json")
apt.export_lock(name = "apt_lock_export", previous_lock = "//:previous.lock.json")
use_repo(apt, "apt_lock_export")
```

After source-change authorization edit unique sources and pass --allow-source-change; it still forbids silent existing SHA256 changes. merge migrates old locks but still requires update. --resolved-lock checks saved real resolution, not a substitute for resolving.

Normal image consumption:

```starlark
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.import_lock(
    lock = "@sonic_build_infra//apt:apt.lock.json",
    dependency_sets = ["orchagent_debian", "orchagent_debug_debian"],
)
use_repo(apt, "orchagent_debian", "orchagent_debug_debian")

apt_inputs = use_repo_rule("@sonic_build_infra//apt:inputs_repository.bzl", "apt_inputs")
apt_inputs(
    name = "orchagent_apt_inputs",
    lock = "@sonic_build_infra//apt:apt.lock.json",
)
```

use_repo names match dependency_sets. import_lock resolves nothing new/writes no locks; apt_inputs only maps labels. Neither replaces actual locking. Synchronize export_inputs.py only for actual maintained consumers; direct-lock images need no extra generated MODULE/manual bzl.

## Go modules

### Version graphs, content verification and ZIP digests

Maintain both native inputs and Bazel ZIP locks. go.mod/work plus dependency declarations determine minimal version selection. go.sum/work.sum store h1 content checksums; ZIP sums map module@version to raw SHA256 for native Bazel download/cache. They are not interchangeable.

Use Gazelle zip_lock and import its structured update plan:

```starlark
go_deps = use_extension("@bazel_gazelle//:extensions.bzl", "go_deps")
# Retain the owning component's actual from_file(go_mod=...) or from_file(go_work=...) declaration.
go_deps.zip_lock(file = "//:go.zip.sums.json")
use_repo(go_deps, go_zip_lock_plan = "bazel_gazelle_go_repository_config")
```

Independent roots own locks; buildimage uses tools/bazel/go/go.zip.sums.json. Shared-extension graphs aggregate at root; isolated extensions/explicit repositories need additional plans. Never update a dependency's internal lock as root destination.

### Tool prerequisites

Read project tools/bazel/go/README and selected infra go/README. Use shared lock.py/zip_lock/structured exports. Record development and final recipe identities under module policy. The script needs Python >=3.11 and plan-selected exec rules_go SDK without automatic switching.

### Go dependency update steps

1. Edit owning module/workspace with pinned SDK, run actual native maintenance/verification, synchronize used vendor/modules.txt while preserving patches, and review members/workspace inputs.
2. Reevaluate go_deps and actual root/independent graphs; update BUILD/imports.
3. Initialize {} only for missing ZIP locks. Run updater, not check alone. It reads complete plans, downloads missing ZIP digests with declared SDK, verifies h1 and computes SHA256, preserves valid entries/removes obsolete ones. Failures retain the old lock.
4. Run --check for exact coverage/format/conflicts. It downloads nothing and does not replace updates. Update every independent root lock.
5. Build/test in ordinary mode: missing digests fail without silent updates. Native checks use readonly where applicable and locks remain stable.
6. Hand off mod/sum, applicable work/vendor, root ZIP locks and plan imports together.

Use the selected SDK runner after native changes; replace aliases/MODULE_PATH/VERSION consistently:

```sh
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- version
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- get MODULE_PATH@VERSION
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- mod tidy
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- mod verify
SONIC_GO_LOCK_UPDATE=1 bazel run @io_bazel_rules_go//go -- list -m all
```

Update flags are explicit-window only. Runner uses declared host-compatible SDK and GOTOOLCHAIN=local. See [Go](go.md) for workspace/generated-source maintenance. For multiple plans check SDK identity/compatibility, not implicit first-plan selection.

At buildimage root:

```sh
tools/bazel/go-lock
tools/bazel/go-lock --check
```

Independent lemming workspace:

```sh
tools/bazel/go-lock --workspace "$PWD/platform/alpinevs/src/libsai-grpc/lemming"
tools/bazel/go-lock --workspace "$PWD/platform/alpinevs/src/libsai-grpc/lemming" --check
```

Without project wrappers, run the selected infra script from the component root; add actual isolated/explicit plans:

```sh
python3 "$INFRA_SOURCE/go/lock.py" --workspace "$PWD" --bazel "$BAZEL" \
  --plan '@go_zip_lock_plan//:zip-lock.json'
python3 "$INFRA_SOURCE/go/lock.py" --workspace "$PWD" --bazel "$BAZEL" \
  --plan '@go_zip_lock_plan//:zip-lock.json' --check
```

Use one explicit HTTP(S) GOPROXY and documented private authentication, without credentials in locks. Compile caches do not replace ZIP locks/download caches. go mod verify checks content, not Bazel ZIP-lock updates.

## Rust crates

rules_rs/sonic-rust-deps from_cargo explicitly reads Cargo.toml/lock and platform_triples. Cargo.lock pins versions/registry checksums/Git revisions; manifests/configuration separately determine features/toolchains/options. Preserve them all.

Use the [selected SDK runner](language-recipes.md), owning workspace and explicit matching rustc, not host Cargo. Every crate/feature/target change requires actual resolution from the existing lock and graph review. For proven targeted changes:

```sh
bazel run @sonic_build_infra//rust:cargo -- update -p CRATE --precise VERSION
bazel run @sonic_build_infra//rust:cargo -- metadata --locked --format-version 1
```

After adding manifest dependencies, resolve then check read-only:

```sh
bazel run @sonic_build_infra//rust:cargo -- metadata --format-version 1
bazel run @sonic_build_infra//rust:cargo -- metadata --locked --format-version 1
```

generate-lockfile is initial-only. Synchronize manifest/lock/Bazel imports, target conditions/build-deps/proc-macros and shared manifest/public exports. Compare native/shared origins/versions/features and justify intentional differences. Shared-trait owners/consumers use one graph. After shared-version changes, update MODULE and validate shared/owner/affected targets. Native build/test uses --locked; validate actual Bazel from_cargo separately. This route uses no Cargo.Bazel.lock or unrelated crate_universe repin commands.

Authorities: selected infra rust/deps MODULE/README/Cargo inputs and [Cargo update](https://doc.rust-lang.org/cargo/commands/cargo-update.html).

## pip and Python

Distinguish distribution requirements, build/test tool locks and image runtime locks. Requires-Dist preserves constraints/extras/markers without resolving every runtime version merely to produce metadata. Lock actual build/test imports separately; assembly runtime locking follows below.

Root pip.parse consumes config-engine, Orchagent configuration and YANG requirements locks. config-engine requirements recursively include py-common/supervisor/YANG under one hub; Orchagent has separate exact hashed pyroute2. Preserve their generated versus small explicit ownership workflows.

Follow config-engine README with uv 0.12.18 and target Python. Check uv version and prepare the pinned tool before execution:

```sh
uv pip compile src/sonic-config-engine/requirements.in \
  --python-version 3.13 --generate-hashes --no-emit-index-url \
  --output-file src/sonic-config-engine/requirements_lock.txt
```

Existing outputs prefer retained versions. Use selected-version --upgrade-package only for necessary targeted changes, updating exact requests first. Pin direct/transitive versions and distribution hashes. Regenerate shared locks, not copies per consumer.

Check Python/platform markers/extras/index/URL/Git/wheel/sdist/patch identities. Native/sdist builds separately pin build-system.requires/toolchains/environments; runtime locks alone do not cover isolated backend downloads. Generate/check applicable platform locks and pip.parse configuration with real consumers.

Each actual build/test/image dependency introduction requires uv pip compile from existing output, then reevaluated pip.parse and wheel/install/import checks. uv.lock and requirements workflows differ; uv-project users synchronize actual Bazel exports.

Authorities: config-engine requirements/README, root pip.parse and [uv compile](https://docs.astral.sh/uv/pip/compile/).

### Python runtime locks and Requires-Dist

Assemblers own complete runtime resolution. Lock selected entries' full closure with versions/origins/distribution hashes, retaining source owner/wheel/installed-TAR relationships. Source owners produce wheels; the shared `wheel_layer` installs them and locked external wheels into TARs for OCI/rootfs. Share locks only for equivalent resolution inputs; verify environment applicability.

1. Collect entry/transitive source identity/Requires-Python/Dist from wheel METADATA or declarations verified against it. Preserve extras and markers. Pinned resolvers follow third-party metadata. Building source wheels and exporting their metadata must be independent of image runtime lock generation to avoid cycles.
2. Explicitly depend on metadata, entry set, target Python/platform/extras/index/constraints. Export requests from them rather than duplicate Requires-Dist manually.
3. Re-resolve affected locks with fixed tools/from existing locks after any input change, preserving unrelated versions. Record input digests; constraint/extras/marker changes update provenance even if versions stay equal.
4. Commit runtime lock, provenance, needed exports and consumer declarations in owning image/rootfs repositories as explicit normal inputs, associating cross-repository metadata versions. Updates are separate. Normal builds read/check digests and fail missing/stale locks with update instructions, never silently resolving/writing.
5. Check closure/constraints/markers/extras/hashes/input consistency, actual installs/imports and stable normal-build locks. Required version-controlled files do not themselves authorize commits/pushes.

### pip runtime lock generation example

Image-owner template: replace identities/directories. Normal builds/updates share one plan/production lock. Example Python 3.13/Linux AMD64 producers under [Python installation](install-interfaces.md#3-shared-python-source-and-wheel-inputs):

| Role | Public target/metadata |
| --- | --- |
| example-service | @example_service//:service_wheel, 2.0, Python >=3.11; example-common>=1,<2, requests>=2.32.3,<3 with Python marker, prometheus-client>=0.20,<1 for metrics extra |
| example-common | @example_common//:common_wheel, 1.2, Python >=3.11; PyYAML>=6,<7 |

These are illustrative modules. Both source wheels belong in the selected closure; a Python import dependency does not install its distribution automatically. The final dependency check must compare their installed `.dist-info/METADATA` with the source metadata used to resolve the lock.

**1. Verify the shared metadata/check interface before wiring the plan.** In the inspected
[infra snapshot 08e0956f](https://github.com/securely1g/sonic-build-infra/blob/08e0956f80574b27a9b68e72fe855cc0089058e5/python/runtime_lock.bzl),
`python_runtime_plan(packages = ...)` and `checked_python_runtime(sources = ...)` require
`PythonRuntimeInfo` from the direct-source installation path. `wheel_layer` returns a TAR
through `DefaultInfo` only. Neither a wheel label nor its TAR can replace that provider.
The shared wheel metadata adapter is a prerequisite for using those rules with owner wheels;
do not generate a parallel direct-source installation just to satisfy the old interface.

The existing `runtime_lock` CLI can construct a plan from declared metadata JSON and validate
wheel-derived TARs using `check --source-tar ... --third-party-tar ... --verify-installation`.
That capability does not supply the missing Bazel metadata/provider integration. Implement or
select a compatible shared adapter before treating this template as a complete image recipe;
do not replace dependency checks with a plain `wheel_layer` or copy resolver code into images.

The plan contract for the example is:

| Input | Value |
| --- | --- |
| Source wheels/metadata | service_wheel and common_wheel above |
| Roots | example-service[metrics] |
| Source distribution identities | example-service, example-common; never resolve these from PyPI |
| Interpreter/platform | Python 3.13, x86_64-unknown-linux-gnu |
| Resolver | Fixed uv 0.12.18, explicit index/find-links/constraints and target marker environment |
| Owner inputs | images/example/requirements.in, requirements_lock.txt, lock-inputs.json |

Keep planning independent of the final pip hub/assembly package. Validate source versions,
Requires-Python, extras and markers; resolve only the external closure. Include marker
environment/index/constraints/tool version in provenance, with credentials supplied outside
recorded inputs. Resource-only byte changes may retain resolution plans. The commands below
assume the completed adapter exposes `//images/example:runtime_plan` and its `.plan.json`
output; that target is a required implementation boundary, not an existing wheel-layer API.

**2. Save executable updater** tools/bazel/example-python-lock. Locate source root from script, share build/run flags and resolve plan paths before configuration changes:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
BAZEL_BIN=${BAZEL:-bazel}
mode=update
if [[ ${1:-} == --check ]]; then
    mode=check
    shift
fi
"$BAZEL_BIN" build "$@" //images/example:runtime_plan
plan=$(realpath bazel-bin/images/example/runtime_plan.plan.json)
owner="$PWD/images/example"
args=("$mode" --plan "$plan" --requirements "$owner/requirements.in"
      --lock "$owner/requirements_lock.txt" --inputs "$owner/lock-inputs.json")
if [[ $mode == update ]]; then
    UV_BIN=$(command -v "${UV:-uv}")
    args+=(--uv "$UV_BIN")
fi
"$BAZEL_BIN" run "$@" @sonic_build_infra//python:runtime_lock -- "${args[@]}"
```

Only for absent locks initialize an empty requirements_lock.txt for pip.parse bootstrap; retain existing locks. Then run:

```bash
chmod +x tools/bazel/example-python-lock
if [[ ! -e images/example/requirements_lock.txt ]]; then
    : > images/example/requirements_lock.txt
fi
UV=/absolute/path/to/uv-0.12.18 tools/bazel/example-python-lock
tools/bazel/example-python-lock --check
```

CLI checks exact uv version against plan before real compilation. From existing lock it pins versions/origins/SHA256 and jointly publishes requirements.in, requirements_lock.txt and lock-inputs.json. Failures preserve old files. Raw metadata digests stale old records even when external requests/versions stay equal. These three files are production inputs. Bootstrap emptiness is not image readiness; obtain/check formal lock/provenance first. Other owners reuse shared CLI with their own paths, not copied resolver code.

**3. MODULE reads the lock; runtime subpackage assembles closure.** Register selected rules_python 3.13 and pip, then:

```starlark
pip.parse(
    hub_name = "example_runtime_pip",
    python_version = "3.13",
    requirements_lock = "//images/example:requirements_lock.txt",
)
use_repo(pip, "example_runtime_pip")
```

images/example/runtime/BUILD.bazel:

```starlark
load("@example_runtime_pip//:requirements.bzl", "all_whl_requirements")
load("@sonic_build_infra//python:wheel_layer.bzl", "wheel_layer")

wheel_layer(
    name = "source_packages",
    wheels = [
        "@example_common//:common_wheel",
        "@example_service//:service_wheel",
    ],
    site_packages = "/usr/local/lib/python3.13/dist-packages",
    scripts = "/usr/local/bin",
    interpreter = "/usr/bin/python3",
)

wheel_layer(
    name = "external_packages",
    wheels = all_whl_requirements,
    site_packages = "/usr/local/lib/python3.13/dist-packages",
)
```

Use the actual target interpreter layout, not universal Debian paths. `wheel_layer` installs
the declared wheels, including metadata, resources and entry points; it does not resolve or
check `Requires-Dist`. Keep source and external TARs distinct when using the existing CLI's
installation checker, which assigns their origins by TAR input group.
The [combined wheel-layer example](python.md) instead requires an adapter that checks
source/external origins against the selected wheel identities within one TAR.

The completed shared adapter must bind `:source_packages`, `:external_packages`, the plan,
requests, lock and provenance to a mandatory read-only check, and export a checked merged
TAR as `:python_runtime`. Require exact source/external installed sets, matching source
metadata and locked external versions, no source distribution replaced by an external wheel,
and all transitive requirements satisfied under target markers/extras. Missing or stale
inputs must fail with the actual updater command. The two `wheel_layer` targets alone do
not satisfy this contract and must not bypass it on the final OCI/rootfs dependency path.

**4. Verify behavior:**

```bash
tools/bazel/example-python-lock --check
bazel build //images/example/runtime:python_runtime
```

Compare all three production digests around normal builds. Extract and import service/common/requests/yaml/prometheus_client in matching environments and read real resources. Check wheel Python/ABI/platform tags and native payloads against the target; resolution platform flags do not prove extension compatibility. Connect the checked TAR under [OCI](oci.md). Change Requires-Dist, observe stale failure, update and confirm recovery. Ordinary builds neither run uv nor modify locks. Missing packages/version conflicts/input mismatches fail at this consumer. Deliver metadata/files/updater/consumer declarations. For sdist/native extensions also pin backend/ABI/toolchain. Actual Git/remote actions still require authorization.

## Version control and handoff of locks

Requests and locks are delivery inputs owned together. This specifies file sets/checks, not automatic Git/remote actions.

| Entry | Version-controlled set | Owner |
| --- | --- | --- |
| Global APT | Sources/production lock/component requests/provenance/library maps/indexes/tool closure/consumption; no generated labels | Infra sources/lock, components requests/shared consumption |
| Requirements | Requests/requirements_lock/platform locks/pip.parse | Component/shared hub owner |
| Image Python runtime | Exported Requires-Dist requests/lock/provenance/consumption | Image/rootfs with producer versions |
| uv project | pyproject/uv.lock/actual Bazel exports | Project, no independently resolved duplicate graph |
| Go module | mod/sum/root ZIP lock/plans/BUILD | Module |
| Maintained Go workspace | work/actual work.sum/root ZIP lock/affected members | Workspace; personal temporary work stays local |
| Original vendor entry | modules.txt/maintained files/patches/mod/sum | Original module/workspace policy |
| Rust workspace | Manifests/Cargo.lock/imports/public aliases | Workspace/shared graph owner |
| Bazel module | MODULE/registry source/patch/overlay/checksums/consumers | Module; resolution lock policy below |

1. Check complete request/lock/export/consumer diffs per owner and cross-repository associations.
2. Inspect actual Git tracking. For ignored locks/mod files, use check-ignore and minimal contractual exceptions, not global artifact-ignore removal.
3. Review diffs and read new files directly. Check versions/origins/hashes/closure and exclude credentials/private paths/caches/unrelated upgrades.
4. Record fixed tools/commands, run consistency/readonly/consumer checks and confirm stable regeneration. Do not rewrite unrelated inputs to manufacture differences.
5. Hand off owner paths/new/changed/no-diff/results. Evidence-only logs/MODULE locks do not replace language locks.

## Bazel resolution and delivery

After registry changes verify actual inputs/recipes/resolution/consumers; equal version strings are insufficient. Synchronize revisions/integrity for deps/patches/overrides and record root/independent graphs.

Do not commit MODULE.bazel.lock in buildimage or independent repositories governed by this skill. Ignore it, generate it in CI with lockfile_mode=update, and retain it as validation evidence under the [Bazel resolution policy](../SKILL.md#keep-generated-bazel-lockfiles-out-of-git). Keep canonical package dependency locks, including applicable APT, Cargo, Go and pip locks, tracked in their owning repositories; generated Bazel resolution locks do not replace them. Applicable rules_rust/crate_universe consumers generate and ignore Cargo.Bazel.lock during preparation. from_cargo consumes tracked Cargo.lock without adding Cargo.Bazel.lock.

Deliver declarations/locks/exports/consumers together with owner/component mapping. Keep temporary logs/graphs in task evidence, production locks in consumer repositories. Record tools/commands/before-after identities/impact/results, verify actual new-lock use and stable rebuilds. Missing transitives, mismatches or unverified required platforms retain pending-verification status with concrete scope/blockers.

Authorities: .gitignore, tools/bazel/ci/resolution.py, [Bazel lockfiles](https://bazel.build/external/lockfile).

Existing rules_rust/crate_universe consumers requiring generated Cargo.Bazel.lock follow [their preparation flow](source-builds-and-lockfiles.md#generate-rust-bazel-metadata-before-dependency-evaluation) before evaluation. from_cargo needs no such file. Select update commands by actual rules, without mixing workflows.
