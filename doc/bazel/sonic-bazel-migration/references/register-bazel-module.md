# Bazel module ownership, metadata and consumption

Read the [shared contract](common-contract.md). Use for implementation ownership, independent modules, registry recipes and consumers. Deliver pinned inputs, metadata and consumption evidence.

## Authorities and entry points

- [Registry](https://github.com/securely1g/sonic-bazel-registry).
- Version/publishing policy: its README.md.
- Verification contract: ci/README.md and ci/registry_ci.py.

Read current policy, target entries and validator input contracts before preparation. Replace NAME/VERSION/COMMIT/BASE/SRI with actual values and verify current formats. [Source preparation](source-and-patches.md) owns fetching/patch execution; this page owns publishing/registration.

## Module selection and registry endpoints

Inspect compatible BCR/upstream/project support, versions/ABI/sources/patches/consumers. Reuse suitable support; [justify ownership](infrastructure.md#rule-necessity-and-ownership) for gaps. Replacing/wrapping BCR dependencies requires concrete user approval.

Root configuration chooses registries, with one effective endpoint per repository; dependency rc is not inherited. Prepare prerequisites first. Source overrides prove pointed-to sources only; registry checks prove actual download/patch/overlay/public interfaces. Record both. When switching endpoints inspect the full effective list/versions without drifting checksums/toolchains/APT/language locks.

## Development verification and final registry consumption

Pin the actual closure and separately validate independent/root entries. Remove the tested source override for registry acquisition checks. Prepare unpublished dependencies through the main Draft policy with one endpoint and formal final recipes. Preserve separate commands/inputs/results; no local branch/worktree application procedure is prescribed here.

## 1. Determine source and build ownership

Decide source ownership, implementation owner and independent publishing need before directories/registration. Paths, Make recipes, repository/fork names are clues only. buildimage-owned implementations stay at their actual directories; src/platform examples are not a whitelist or relocation requirement.

| Type | Implementation/fix owner | Registry responsibility |
| --- | --- | --- |
| buildimage-owned source | Actual component directory: BUILD/source/tests/install; root MODULE dependencies | No registration merely for Bazel/TAR; assess real cross-repository module demand |
| Independent SONiC repository/submodule | Owner MODULE/BUILD/fixes/tests/public APIs; buildimage pointers/integration | Pinned commit/identity/version alignment/external consumption, no second build implementation |
| Independent third-party or SONiC-hosted fork | Reuse BCR/upstream; registry owns needed recipes/patches/overlays/bindings/dependency tests | Reusable fixed module, consumers use public targets |
| Private internal source | Component-owned fetching/minimal transformation/internal targets under boundary below | Actual module boundary, not one module per fragment |
| Generic toolchains/build/packaging | Infra or upstream rules; component parameters remain BUILD | Shared module registration |

Examples: buildimage owns sonic-bgpcfgd/sonic-frr-mgmt-framework; libnl3/libyang adaptations belong in registry. Read actual sources/consumers rather than treating examples as exhaustive.

### Private input versus independent dependency

Private inputs co-evolve with internal implementation and expose no independently maintained/consumed module contract. Record identity/purpose/coupling/rationale. Independent releases/version/patch/ABI lifecycles and consumable libraries/programs evidence a dependency boundary. One consumer, existing src location or convenience does not make an independent dependency private.

Retain historical Make recipes/patches in their original role. Bazel dependency compilation/bindings/patches/dependency tests live with that module; buildimage keeps integration and consumer tests. Verify authority/full validation without duplicating implementations. This policy does not authorize out-of-scope Make changes.

### Registration and implementation are separate

Registration distributes versions without transferring ownership. SONiC fixes enter source repositories then register commits. Registry may validate consumers, while producers own implementation. Create MODULE only for real boundaries; do not hide independent dependencies in consumers to avoid registration. Hand off shared changes per owner.

## 2. File layout

```text
modules/NAME/
├── metadata.json
├── README.md                         # Optional module documentation
└── VERSION/
    ├── MODULE.bazel                  # Complete module identity, dependencies and extensions
    ├── source.json                   # Source, patch and overlay manifests/checksums
    ├── presubmit.json                # External consumer validation for this version
    ├── patches/                     # Optional changes to existing archive files
    │   └── 0001-module-version.patch
    ├── overlay/                     # Optional paths relative to extracted source root
    │   ├── BUILD.bazel
    │   └── ...
    ├── README.md                     # Optional version documentation
    └── PATCHES.md                    # Optional patch origins, purpose and upstream status
```

metadata.json versions lists releases:

```json
{
  "versions": ["VERSION"]
}
```

Retain existing fields/versions and append releases. Directory/metadata/MODULE name-version/acquired identity must agree.

## Versions and pinned inputs

Keep identity/version/origin/recipe consistent. ABI/SONAME/Debian versions differ from module versions. Follow the selected registry's actual format.

| Origin | Module version | Pinned inputs |
| --- | --- | --- |
| Independent SONiC source | BASE-COMMIT | Base version/full revision/archive checksum |
| Third-party adaptation | upstream.sonic.N | Upstream version/full patches/overlays/checksums |

Preserve fixed entries; document development combinations. Check actual mod graph and source/patch/overlay/entry/override identity. Configure root overrides explicitly. After source/recipe changes synchronize metadata/checksums/consumers, [check locks](dependency-locking.md) and revalidate. APT remains independently locked.

## 4. Register a new SONiC component

### 4.1 Prepare component sources

Implement/verify MODULE, BUILD, public targets/helpers/tests in the source owner. Declare component dependencies with bazel_dep. First verify direct sources/metadata; prepare complete registry versions topologically for final consumption.

Independent component root .bazelrc:

```text
common --registry=https://raw.githubusercontent.com/securely1g/sonic-bazel-registry/main
common --registry=https://bcr.bazel.build
```

Component MODULE example:

```starlark
bazel_dep(
    name = "sonic-swss-common",
    version = "0.0.4-db8f451c76fdc1135cd40f585c218e7d589a7223",
    repo_name = "sonic_swss_common",
)
```

BUILD uses the public common target. Replace example versions with verified ones. Consumer roots select registries; component rc applies only when that component is root. From the verified commit derive VERSION=BASE-COMMIT.

### 4.2 Create an entry

1. Create modules/NAME/VERSION with complete registered MODULE and aligned version.
2. Pin archive URL/checksum/actual root in source.json.
3. Add BASE->VERSION module-alignment patch.
4. Append metadata version and add presubmit.json.

GitHub commit archive template:

```json
{
  "url": "https://github.com/OWNER/NAME/archive/COMMIT.tar.gz",
  "strip_prefix": "NAME-COMMIT",
  "integrity": "SRI",
  "patches": {
    "0001-module-version.patch": "PATCH_SRI"
  },
  "patch_strip": 1
}
```

Verify archive root from actual contents. Alignment patch shape:

```diff
--- a/MODULE.bazel
+++ b/MODULE.bazel
@@ -3,1 +3,1 @@
-    version = "BASE",
+    version = "VERSION",
```

Generate from actual source/context. Reference: modules/sonic-sairedis/0.0.1-befd501a41549c9fedea9a116d081a6ad542cbe3/.

### 4.3 Distinguish validation entries

| Entry | Execution | Proves |
| --- | --- | --- |
| Independent source | Clean component checkout as root | Independent entry/registry/toolchain registration |
| Registered consumer | Fresh validator-generated consumer | Metadata/acquisition/patching/resolution/public targets |

Retain both. Registry overlays/alignment may make consumption work without proving standalone distributed sources. Verify actual distributed entry before claiming standalone builds.

## 5. Register a patched external module

1. Choose fixed upstream/version; inspect sources/license/existing module identity.
2. Derive upstream.sonic.N under policy and prepare development inputs.
3. Maintain complete registered MODULE with dependencies/compatibility level.
4. Put existing-file changes in patches and new BUILD/helpers/tests in overlay; align existing upstream MODULE via patch where appropriate.
5. Declare raw archive/full patch/overlay manifests and checksums.
6. Update metadata/presubmit and validate consumption.

source.json example:

```json
{
  "url": "https://UPSTREAM/RELEASE.tar.gz",
  "strip_prefix": "UPSTREAM-RELEASE",
  "integrity": "ARCHIVE_SRI",
  "patches": {
    "0001-module-version.patch": "VERSION_PATCH_SRI",
    "0002-fix-behavior.patch": "FIX_PATCH_SRI"
  },
  "patch_strip": 1,
  "overlay": {
    "registry_ci/BUILD.bazel": "BUILD_SRI",
    "registry_ci/consumer_test.cc": "TEST_SRI"
  }
}
```

Each version reconstructs independently from its raw archive and complete patch/overlay set. Record purpose/revision/link/upstream status/tests in patch headers or PATCHES.md. Reference rules_distroless/0.9.4.sonic.8.

### Generate MODULE overlays for upstream without MODULE

Set generated_module_overlay=true in presubmit and maintain the registered MODULE only:

```bash
python3 ci/registry_ci.py sync-module --module NAME --version VERSION
python3 ci/registry_ci.py sync-module --module NAME --version VERSION --check
```

Run `registry_ci.py` under a hermetic interpreter per the
[declared-tools policy](../SKILL.md#use-native-bazel-actions-and-declared-tools); the registry
checkout is not a Bazel workspace, so use another workspace's interpreter or a dedicated entry
point rather than a worker-provided `python3`.

The generator creates overlay/MODULE and updates its checksum. Registrants maintain all other manifests/checksums. Existing version-patch entries retain that mechanism; choose one appropriate MODULE-maintenance route.

## 6. Integrity

Current validator supports integrity-pinned HTTPS archives plus optional patches/overlays. Verify other types first. SRI is sha256- plus Base64 binary digest, computed separately for archive and each file:

```bash
python3 - /tmp/module-source.tar.gz <<'PY'
import base64
import hashlib
import pathlib
import sys

data = pathlib.Path(sys.argv[1]).read_bytes()
print("sha256-" + base64.b64encode(hashlib.sha256(data).digest()).decode())
PY
```

Hash raw downloaded archives and final saved patch/overlay bytes. The validator requires exact manifest/directory correspondence and checks each local file.

## 7. Local consumption verification

### presubmit.json

Provide configuration per new version using real targets:

```json
{
  "architectures": ["amd64", "arm64"],
  "consumer_deps": [
    {
      "name": "sonic-build-infra",
      "version": "INFRA_VERSION",
      "repo_name": "sonic_build_infra"
    }
  ],
  "platforms": {
    "amd64": "@sonic_build_infra//platforms:x86_64_trixie",
    "arm64": "@sonic_build_infra//platforms:aarch64_trixie"
  },
  "build_targets": ["@NAME//:PUBLIC_TARGET"],
  "test_targets": ["@NAME//:CONSUMER_TEST"]
}
```

- Architectures reflect module promises; verify native CI support first.
- consumer_deps are direct test-root dependencies; component MODULE still declares its own. Validator generates bazel_dep/version overrides for fixed selection.
- List public outputs/consumer tests/runtime/symbol package targets explicitly.
- Configure Go/Rust toolchains/features through documented optional fields.

### Local reproduction

Use native-target Debian Trixie, Bazel 8.5.1 and ci/README tools. From registry checkout, select a fresh empty work directory:

```bash
python3 ci/registry_ci.py run \
  --module NAME \
  --version VERSION \
  --architecture amd64 \
  --work-dir /tmp/registry-NAME-VERSION-amd64-work \
  --artifacts /tmp/registry-NAME-VERSION-amd64-artifacts \
  --bazel /path/to/bazel-8.5.1
```

Run ARM64 checks natively with matching arguments/directories. Validator creates an independent consumer using local file registry then BCR, actually acquires/patches/overlays/builds/tests and compares final/registered MODULE. It saves consumer MODULE/locks/artifacts/tests/evidence.

### Consumption handoff checks

1. Directory/metadata/identity/revision agree and every checksum matches.
2. Source/patch/overlay ownership and development changes are traceable.
3. Independent and registry entries separately cover required targets/architectures/configurations.
4. Deliver module/version/source/registry identities, commands/artifacts/results.
