# Source acquisition and patch application

Read the [shared contract](common-contract.md). For online/local sources, patches or overrides, derive the chain original inputs -> extraction/mapping -> ordered patches -> necessary overlays -> native build from Make analysis. Repository rules manage preparation; compilation retains native-build constraints.

## 1. Source and patch ownership

- New SONiC fixes belong in component repositories and new registered source commits. Preserve existing Make patch directories/series as real inputs and record final-source relationships.
- Decide [ownership](register-bazel-module.md#1-determine-source-and-build-ownership) first: buildimage-owned code stays in its actual directory, independent SONiC code stays with its owner, third-party adaptation reuses modules or belongs in registry. Component-managed downloads must meet private-input boundaries; location/consumer count alone is insufficient.
- Pin local submodules through parent pointers and actual modifications. Direct compilation preserves user checkouts. Patching requires a separate Bazel-managed copy with declared originals; fetching/building must not mutate user sources or consume undocumented patched directories.
- Pin archives, Debian packaging, generators and patches independently. Analysis copies/logs remain temporary; production patches/templates belong to their owning repository as declared inputs.

## Handoff from Make analysis to Bazel acquisition

Before choosing rules/committed files, inventory each original Make location/command, origin type, full version, URL/revision, checksum, archive path, extraction destination, consumer, preparation stage and existing maintenance ownership. Download location does not establish local ownership.

| Origin | Bazel acquisition/consumption | Commit boundary |
| --- | --- | --- |
| Upstream archive/Git revision | Pinned acquisition and actual source paths | Declarations/adaptation; fetched contents remain external |
| External Debian source-package packaging/patches/resources | Pinned packages and original preparation order; external labels/prepared trees | External originals stay external; maintain sourced incremental patches |
| Existing SONiC sources/packaging/patches/series/templates | Preserve owner and declare labels | Existing maintained files plus necessary changes |
| New BUILD/adaptation templates/fixes | Ownership-selected repository | Actually used rules/templates/patches/metadata |
| Analysis extraction/patched copies | Evidence only; reproduce through declarations | Task temporary directory |

A debian/ name does not decide ownership. Reuse SONiC-maintained directories locally and fetched ones externally. Vendoring third-party sources requires explicit scope/update requirements.

### Debian source-package example

For dget pkg_VERSION.dsc, inspect the .dsc and all members/checksums. Recording only .dsc/orig.tar loses packaging inputs. Record source format and extraction/Debian/outer-patch/overlay stages.

For 3.0 (quilt):

1. Fetch fixed .dsc and verify all orig/debian/other members temporarily; record automatic extraction/patch behavior.
2. Read rules/control/install/series and derive effective build/install/patch contracts; distinguish analysis-only from actual Bazel inputs.
3. Pin needed archives and use repository rules, explicitly mapping merges/stages after checking multi-archive/overwrite/patch ordering.
4. Apply Debian/SONiC patches in original order, retaining upstream names/series. Execute automatic stages once. Keep externally supplied sources/configuration/scripts/resources connected to actual consumers.
5. Commit declarations/adaptation/local deltas. Re-fetch to prove independent reconstruction and remove copied external originals from overlays.

Apply the same handoff to Git/ordinary archives. Address actual [shared preparation gaps](infrastructure.md#rule-necessity-and-ownership); committing analysis trees cannot replace acquisition capability.

## 2. Online sources

### Choose the preparation entry before the rule

List downloads, mappings, ordered patches and nested extraction, then:

1. Inspect selected Bazel http_archive and existing preparation APIs/order/label tracking. Directly declare workflows they support.
2. For a concrete gap, record inputs/outputs/consumers and determine reusable ownership. Add generic preparation to sonic-build-infra; component MODULE/extensions declare fixed inputs/steps rather than private source.bzl for downloads/series/merges/nesting.
3. Keep genuinely component-specific, otherwise unexpressible transformations minimal and documented. Shared rules implement confirmed preparation operations, not arbitrary shell/build commands or extensible interpreters. Reuse does not authorize other component migrations.

Separate registry source.json/overlay acquisition from native-source preparation. Reuse prepared results with one producer per tree/patch stage. If module roots and independently writable patch trees are both needed, document responsibilities/limits. Cached equal archives still involve two extractions; do not claim their elimination. Do not patch symlinked source trees or change publishing models to save extraction. For different independent entries, share identities/recipes and validate both. Shared rules implement mechanisms; component recipes own URLs/checksums/paths/order/BUILD labels; separate BUILD templates own native actions.

Pin URLs, releases/full commits, raw sha256/integrity, archive types and real strip_prefix. Mirrors must match checksums. Pin Git commits/submodules and record resolved revisions; mutable branches/tags are descriptions only. Distinguish raw archive hashes from patched identity; recheck layouts/patches on upgrades.

Ordinary MODULE example, replacing placeholders:

```starlark
http_archive = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
http_archive(
    name = "component_source",
    urls = ["https://UPSTREAM/archive/COMMIT.tar.gz"],
    sha256 = "ARCHIVE_SHA256",
    strip_prefix = "UPSTREAM-COMMIT",
    patches = ["//component/patches:0001-fix.patch"],
    patch_strip = 1,
    build_file = "//component:source.BUILD.bazel",
)
```

### Shared ordered source preparation

For merging/ordered series/nested extraction unsupported by actual http_archive ordering, use source/prepared_source.bzl prepared_source. Read selected source/README.md and implementation before using attributes. Substitute actual inventory values:

```starlark
prepared_source = use_repo_rule(
    "@sonic_build_infra//source:prepared_source.bzl",
    "prepared_source",
)
prepared_source(
    name = "component_source",
    steps = [
        """{
            "op": "archive",
            "urls": ["https://UPSTREAM/component_VERSION.orig.tar.gz"],
            "sha256": "ORIG_SHA256",
            "strip_prefix": "component-VERSION"
        }""",
        """{
            "op": "archive",
            "urls": ["https://DISTRIBUTION/component_VERSION.debian.tar.xz"],
            "sha256": "DEBIAN_SHA256"
        }""",
        """{
            "op": "patch_series", "series": "debian/patches/series",
            "strip": 1, "format": "unified"
        }""",
        """{
            "op": "patch", "input": "local/0001-fix.patch",
            "strip": 1, "format": "unified"
        }""",
        """{
            "op": "patch_series",
            "series_input": "sonic/series",
            "patch_inputs": ["sonic/sub/0001-fix.patch"]
        }""",
        '{"op": "extract", "archive": "vendor/source.tar.gz", "output": "vendor"}',
    ],
    inputs = {
        "local/0001-fix.patch": "//patches:0001-fix.patch",
        "sonic/series": "//patches:series",
        "sonic/sub/0001-fix.patch": "//patches/sub:0001-fix.patch",
    },
    build_file = "//:source.BUILD.bazel",
)
```

steps are ordered JSON strings, written directly in MODULE or json.encode in .bzl. inputs maps logical relative paths to tracked file labels without reconstructing patch trees. build_file injects BUILD after preparation.

| Operation | Inputs/order |
| --- | --- |
| archive | Required urls/sha256; optional strip_prefix/output mapping |
| patch | input references inputs; strip defaults 1, format native; see [methods](#patch-application-methods) |
| patch_series | Repository series or mutually exclusive series_input plus complete ordered patch_inputs; strip=1/format=native defaults |
| extract | Archive from previous steps; optional output/strip_prefix |

The example explicitly selects unified for confirmed archive-series/single-label format compatibility; local series stays native. Match full paths such as sub/0001-fix.patch relative to series directories against patch_inputs, not basenames. Ignore blank/comment lines; require one path per remaining line. Reject duplicates/inline options. Different strip values use ordered patch steps, not expanded series syntax. Unknown operations/attributes, missing labels/order mismatches fail; paths remain repository-relative.

Check identical recipe identities at source/registry entries and [validate](#6-updates-and-verification) label-triggered reevaluation, diagnostics and real consumers. Derive mechanism validation from actual interfaces/changes, without expanding this example to every component.

## 3. Local patches

Name new/unpublished SONiC/registry patches 0001-description.patch, 0002-description.patch in actual application order, synchronizing lists/series. Names alone do not set order. Preserve upstream archive names/series and [fixed published identities](register-bazel-module.md#versions-and-pinned-inputs).

Renaming unpublished patches preserves bytes/provenance and updates references/series/source/overlay manifests/checksums. Refresh generated MODULE overlays through existing tools and verify unchanged ordering/final sources. Follow actual rule/repository patch format; no additional universal mail/DEP-3/format-patch requirement. Record purpose/origin/upstream status under owner rules.

Declare patch labels/lists/http_archive.patches and required visibility. Declare/read series as an input; do not rely on directory enumeration. Preserve full paths, reject missing/duplicate/unconsumed patches and explain conditions/disabled items. Discovery does not authorize automatic application.

### Patch application methods

Pin bytes, prerequisite source, stage, directory and strip first:

1. Prefer builtin ctx.patch for ordinary text. prepared_source defaults format=native and passes original input to it.
2. Preserve raw error/path/hunk before adjustments. Check identities/order/strip/content. CONTENT_DOES_NOT_MATCH does not establish unsupported format. A format gap needs original structure/parser location/minimal reproduction; context failures require source/stage/path correction.
3. For proven gaps inspect managed tools' versions/options/runtime. Repository rules cannot invoke action-generated exec outputs; action tools need [complete hermetic closure](hermetic-tools.md). Neither stage may discover tools through host PATH.
4. Implement necessary minimal compatibility in shared infrastructure under [ownership](infrastructure.md#rule-necessity-and-ownership). Components declare original bytes/order/strip/confirmed format, without patch-of-patch conversion or private duplicated mechanisms.

prepared_source format=unified handles ordinary unified-diff file segmentation. Shared code recognizes actual ---/+++ boundaries using @@ old/new counts to distinguish body prefixes, then delegates each segment to ctx.patch with strip. Original patches/series stay unchanged; remove private segments after success. This adapts format boundaries, not matching/newline semantics or a second patch engine. It uses no shell and never switches automatically after native failure. Git modes/renames require verified native support; unified rejects Git metadata/binary patches rather than discarding semantics. Native is not universal binary support: validate the declared tool separately. Unknown/incompatible formats fail explicitly.

Both methods retain context checks: no skipped hunks, ignored exits or permissive retries hiding version mismatch. After correction, prepare fresh pinned sources and verify all results/consumers. Track label bytes with ctx.read/ctx.patch, explicitly reading where needed. Verify patch/series changes cause reevaluation; no absolute-path substitutes or undeclared action-time downloads/patches. Git pins local patches; registry metadata additionally checks integrity. Existing custom source rules face the same necessity review and full path/order/parameter checks.

## 4. Online patches

Pin stable full-revision URLs and independent checksums with origin/purpose/upstream status. Maintained SONiC adaptations belong in owner patch directories; external inputs may be downloaded through declared repository operations.

Bazel 8.5.1 http_archive supports remote_patches URL->SRI and remote_patch_strip. Its order is remote patches, local patches, patch_cmds. Verify that order against Make. Check each patch independently. Interleaved sources/different strip values require suitable [ordered preparation](#choose-the-preparation-entry-before-the-rule), with generic gaps shared and explicit recipes; filename prefixes cannot alter fixed phases.

Custom repositories use ctx.download with checksum then explicit ctx.patch steps. No curl|patch, build-time Git fetch or untracked preprocessing. Preserve original identity when moving online patches into local maintenance.

## 5. Conditions, ordering and overlays

Trace quilt/Debian/StGit/wrappers in actual execution order, recording tree/path/strip/directory/condition/output. Avoid duplicate fixes across archives/registry/component/Debian. Overlays are transformations too: declare files/templates and before/after patch order. Published versions independently reconstruct complete patches/overlays from raw archives under [module policy](register-bazel-module.md#versions-and-pinned-inputs).

Repository fetching cannot use target select or infer target CPU/OS from executors. Prefer original configuration branches over conditional patches where valid; otherwise model pinned source variants and select compilation targets by target configuration. Preserve configurable/fixed semantics and mutually exclusive variants.

## 6. Updates and verification

After source/patch/series/overlay changes, [refresh affected inputs](dependency-locking.md), versions/checksums/exports under registry policy. Hand off preparation rules, maintained patches and repository relationships.

Before upgrades classify each prior patch as included/partial/missing by actual code, not applicability alone. Retain needed semantics and remove duplicate transformations. Inherit latest applicable tests/selection. Existing regressions check unpatched new upstream and retained fixes separately; absent tests require contract-based validation rather than ceremonial record tests. Synchronize names/references under section 3.

Verify applicable scope:

- Fresh pinned acquisition, declared order and effective patched functionality.
- Explicit mismatch/missing-input failures with first errors/identities, distinguishing format/context without fallback/skipping.
- Label patch/series changes reevaluate preparation and reach consumers, excluding stale caches/overrides; separate mechanism and consumer evidence.
- Required variants compile/consume; source-independent and registry entries validate separately.

Analysis owns original chains; implementation owns Bazel mappings; verification owns actual commands/identities/results/evidence. Keep experiments temporary and production code limited to used inputs. The [equivalence check](make-bazel-equivalence.md) later compares delivered files with Make's, so prepared sources and patches must match the ones Make builds.

References: [Bazel 8.5.1 http rules](https://github.com/bazelbuild/bazel/blob/8.5.1/tools/build_defs/repo/http.bzl), [patch ordering](https://github.com/bazelbuild/bazel/blob/8.5.1/tools/build_defs/repo/utils.bzl), [registry](register-bazel-module.md).
