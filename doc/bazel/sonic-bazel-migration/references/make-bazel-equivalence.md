# Check equivalence with the Make build

While Make still builds an image or package, its Bazel replacement must ship
the same files. [sonic-net/sonic-buildimage#28005](https://github.com/sonic-net/sonic-buildimage/pull/28005)
implements this check for docker-sysmgr and states the policy in its
[Bazel primer](https://github.com/sonic-net/sonic-buildimage/blob/54eb0632ba9dc93e784665280ce4ec19c122cef1/tools/bazel/docs/README.bazel.md#equivalence-with-the-make-build):
build both versions, compare `.deb` files and container images file by file,
and allow a difference only when a rule names it and says why. Use that
checker, [`tools/bazel/test_equivalence.sh`](https://github.com/sonic-net/sonic-buildimage/blob/54eb0632ba9dc93e784665280ce4ec19c122cef1/tools/bazel/test_equivalence.sh)
with [`tools/bazel/equivalence_checker/`](https://github.com/sonic-net/sonic-buildimage/tree/54eb0632ba9dc93e784665280ce4ec19c122cef1/tools/bazel/equivalence_checker);
do not write another comparator. Links on this page point to the PR head
`54eb063`.

The checker adds to the existing checks rather than replacing them. It compares
file contents, symlink targets and ELF properties. It does not compare modes,
owners or directories, run binaries or start services, so keep the analyzed
layout, installed-runtime, service and debug checks.

## When to run it

Run the check in `sonic-buildimage` before merging a PR that adds or changes
Bazel image or DEB outputs, and before reporting such a migration complete.
Missing, pending, failed or stale equivalence results alone must not prevent
Ready for review or return a PR to Draft; retain the other
[Draft/Ready requirements](pr-merge-readiness.md).

Changes to their BUILD files, module versions or overrides,
APT locks, base images, configuration files and Make handoff count as output
changes. One run compares every pair the checker discovers:

- each Bazel image archive, runtime and `-dbg`, against Make's archive of the
  same name in `target/`, such as `target/docker-sysmgr.gz` and
  `target/docker-sysmgr-dbg.gz`;
- each approved `sonic_deb` target against Make's package of the same file name
  in `target/debs/<distribution>/`.

Do not add a DEB package definition only to feed the checker; the
[DEB approval rule](../SKILL.md#require-approval-before-adding-new-deb-package-definitions)
still applies. Component and registry PRs that deliver wheels or TARs do not change an
image until `sonic-buildimage` selects the new version, so the image PR that
selects it runs the check. A Bazel output with no Make counterpart carries the
`no-elf-equivalence` tag and a comment giving the reason; the checker reports it
as excluded instead of comparing it.

## Prepare both sides

1. **Start from a clean checkout of the PR head.** The script refuses a dirty
   tree because both sides must come from the same tree.
   `EQUIVALENCE_ALLOW_DIRTY=1` is for local experiments, not PR evidence.
2. **Build the same sources on both sides.** For each compared project
   component, the revision and patches that Make builds (the `src/<repository>`
   gitlink, or the tag or commit its recipe fetches) must be the ones Bazel
   selects (registry `source.json`, archive or override). The sonic-net PR gets
   this from `common --config=local-modules`, which overrides its in-tree
   modules to `src/`. In securely1g/sonic-buildimage at `7ebff36d3`,
   `sonic-sysmgr` already uses a `local_path_override` to `src/sonic-sysmgr`,
   but Make builds `src/sonic-swss-common` at `10d14ae5` while Bazel selects
   `sonic-swss-common@0.0.8-a0450924…`. Resolve such a mismatch first: the
   checker reports source drift as ordinary differences and cannot tell it from
   a build difference.
3. **Build Make's side with the Bazel path disabled.** Otherwise Make exports
   the Bazel archive and the run compares Bazel with itself. The script checks
   `BAZEL_MIN_READINESS=bazel_disabled`, the switch in the sonic-net PR; this
   repository's current Make bridge uses `BUILD_WITH_BAZEL_WHEN_AVAILABLE=n`.
4. **Read the package cache without writing to it.** The script's default
   `SONIC_DPKG_CACHE_METHOD=rcache` keeps packages built for the comparison out
   of the shared cache.

## Run it

```bash
BLDENV=trixie ./tools/bazel/test_equivalence.sh
```

The script:

1. runs `equivalence_checker.py --print-make-paths` to list the Make files that
   pair with the Bazel targets it discovers;
2. builds them with `make`, runtime archives before `-dbg` archives so that the
   two builds do not trample each other's cache;
3. runs `equivalence_checker.py` in the SONiC slave container. It builds the
   Bazel side, compares every pair, prints a summary, writes
   `target/equivalence-report.json`, and exits non-zero if any difference is
   not accepted.

Run the steps separately when debugging: `--print-sources` lists the pairs and
`--skip-build` reuses existing Bazel outputs. `elfcompare` calls `abidiff` for
shared libraries; inside the slave the script installs `abigail-tools` when it
is missing.

## What it compares

| Item | Paired by | Comparison | Reported as |
| --- | --- | --- | --- |
| Image archive | `//dockers/<image>:<image>.gz` and Make's `target/<image>.gz` | Each side's docker-save layers are applied in order, including whiteouts. Paths that both sides took from the same layer are skipped. | `NO_MAKE_ARTIFACT` or `NO_BAZEL_ARTIFACT` when a side is missing |
| DEB | A `sonic_deb` target in an `src/*` module that the root module depends on, and Make's file of the same name | Both data trees are extracted with `dpkg-deb -x` | `MODULE_UNREACHABLE` when that module is not a root dependency |
| Entry on one side only | Install path | Not compared | `MAKE_ONLY`, `BAZEL_ONLY` |
| Plain file | Install path | Byte for byte | `CONTENT_MISMATCH` |
| Symlink | Install path | Link text, without following it | `TARGET_MISMATCH` |
| ELF file | Install path | Identical bytes pass. If only one side keeps `.symtab`, the strip levels differ. Otherwise each `elfcompare` finding is reported. | `DIFFERENT_STRIP_LEVELS`; findings such as `dependency`, `abi`, `export-removed` and `security`; `INCOMPLETE`, `UNPARSEABLE`, `ERROR` |
| Debug file | Build ID of each runtime ELF on that side | `elfcompare` | `NO_DEBUG` when only one side has it |

## Accept only explained differences

Prefer removing a difference to accepting it. Accept one only when the Bazel
output is intentionally different or the difference cannot affect the image,
and add the rule in the PR that introduces the difference. Each rule in
[`rules.py`](https://github.com/sonic-net/sonic-buildimage/blob/54eb0632ba9dc93e784665280ce4ec19c122cef1/tools/bazel/equivalence_checker/rules.py)
has a unique `id`, a matcher, a `reason` stating the cause and an optional
`comment`:

```python
AcceptanceRule(
    id="accept-libexpat-drift",
    # The versioned sonames carry the version, so a different one stops matching.
    matcher=DiagnosticMatcher(
        codes=(Codes.EXTRACTION_BAZEL_ONLY, Codes.FILE_TARGET_MISMATCH),
        name=(
            literal("/usr/lib/x86_64-linux-gnu/libexpat.so.1"),
            literal("/usr/lib/x86_64-linux-gnu/libexpat.so.1.10.2"),
            # ...the libexpatw names...
        ),
    ),
    reason=(
        "Make ships libexpat1 2.8.3-1~deb13u1 where Bazel ships 2.7.1-2, "
        "so the sonames in the debug image point at the older library."
    ),
    comment=PIN_NOT_ENFORCED,
)
```

- Name paths one at a time with `literal()`, so a new difference in a nearby
  file still fails. Use a glob only for a whole class of build-machinery output,
  such as `/var/lib/dpkg/alternatives/*`, and limit image-only rules with
  `source="//dockers/*"`.
- For package version drift, name the affected paths and both versions. When
  the next drift changes a versioned file name, the rule stops matching and the
  run fails again. Fix the lock when Bazel's selection is the wrong one.
- Match ELF findings by their exact message where practical.
  `sysmgr-dynamic-needed-order` accepts two specific `DT_NEEDED` lists that
  differ only in order; any other change to those lists fails.
- Do not write catch-all rules from `ANY_CODE` or broad globs. Reserve the
  `no-elf-equivalence` exclusion for outputs without a Make counterpart; it
  must not hide differences.
- Remove a rule once its difference is gone. The printed summary lists only the
  rules that matched.

## Record the result

Run the check on the PR's current head, and again after any change to the
inputs listed above. In the PR description, record the checker revision,
distribution and architecture, the compared pairs from `--print-sources`, the
printed summary with the count for each accepted rule, and each new or changed
rule with its reason. Keep `target/equivalence-report.json` with the PR
evidence, for example as a CI artifact. A run that reports `FAIL`, skips a
pair, or uses a dirty tree, Bazel-built Make archives or different sources does
not satisfy this requirement.

The sonic-net PR also adds an Azure pipeline for the check,
[`.azure-pipelines/make-bazel-binary-equivalence.yml`](https://github.com/sonic-net/sonic-buildimage/blob/54eb0632ba9dc93e784665280ce4ec19c122cef1/.azure-pipelines/make-bazel-binary-equivalence.yml),
but leaves it off (`pr: none`, `trigger: none`, nightly schedule commented
out); contributors run the script, also through
[`tools/bazel/test_working_targets.sh`](https://github.com/sonic-net/sonic-buildimage/blob/54eb0632ba9dc93e784665280ce4ec19c122cef1/tools/bazel/test_working_targets.sh).
Run it yourself until a required job does. A job added here extends
`.github/workflows/bazel-oci.yml` under the
[OCI workflow reuse rule](docker-image-template.md#reuse-bazel-oci-for-image-ci).

## Example: docker-sysmgr in sonic-net/sonic-buildimage#28005

The PR compares `//dockers/docker-sysmgr:docker-sysmgr.gz` and
`docker-sysmgr-dbg.gz` with Make's archives, and its `sysmgr_deb` and
`sysmgr-dbg_deb` targets with Make's `sysmgr` packages. Nothing else in that PR
consumes the two DEB targets; in this repository they would still need DEB
approval. Among others, its `rules.py` accepts these differences:

| Rule | Difference | Stated cause |
| --- | --- | --- |
| `sysmgr-librebootgnoi-not-shipped` | Make-only `librebootgnoi.a` and `librebootgnoi.la` | libtool also emits a static archive and its metadata file; Bazel emits neither |
| `sysmgr-exit-handlers` | `atexit`, `at_quick_exit` and `__cxa_at_quick_exit@GLIBC_2.10` added to `librebootgnoi.so.0.0.0` and `rebootbackend` | The Bazel toolchain links `libc_nonshared.a` explicitly |
| `sysmgr-dynamic-needed-order` | The same `DT_NEEDED` libraries in a different order | The order cannot cause shadowing; both exact lists are named |
| `accept-openssl-provider-legacy-drift`, `accept-libexpat-drift` | `ossl-modules/legacy.so` and `libexpat*.so.1*` | Make ships `openssl-provider-legacy 3.5.7-1~deb13u2` and `libexpat1 2.8.3-1~deb13u1`; Bazel ships `3.5.6-1~deb13u2` and `2.7.1-2`. Make records its package versions but enforces them only when `SONIC_VERSION_CONTROL_COMPONENTS` contains `deb`. |
| `accept-dpkg-admin-state`, `accept-update-alternatives-not-replayed`, `accept-dpkg-diversions-not-replayed`, `accept-systemd-user-units-not-enabled` | `/etc/group`, debconf state, registered alternatives, diversion backups and systemd user units | Bazel runs no maintainer scripts; each rule names its files |
| `accept-build-machinery-residue` | Logs, `ld.so.cache`, buildinfo and dpkg status files | Bazel assembles layers and has no build history. The files are listed one by one, so a mismatch in a file such as `rsyslog.conf` still fails. |
| `accept-base-image-binaries-without-debug-symbols` | Inherited binaries such as `libswsscommon.so.0.0.0` and `sonic-db-cli` without debug files | Their debug files would have to come from Make's `target/debs` |

The same PR replaced BCR protobuf 33.4 and gRPC 1.56.3 with `sonic-protobuf`,
which wraps Debian's protobuf 3.21.12, "the release the Make-built base layer
carries" ([commit `26a22d01`](https://github.com/sonic-net/sonic-buildimage/commit/26a22d016038449e1a8aba349b269e863ed66b2e),
[`src/protobuf/MODULE.bazel`](https://github.com/sonic-net/sonic-buildimage/blob/54eb0632ba9dc93e784665280ce4ec19c122cef1/src/protobuf/MODULE.bazel)).
`rebootbackend` therefore needs `libprotobuf.so.32` like the Make binary, and
only the order of its `DT_NEEDED` entries remains different.

## Port the checker to this repository

securely1g/sonic-buildimage at
[`7ebff36d3`](https://github.com/securely1g/sonic-buildimage/tree/7ebff36d33fbc218c9c101e024749a36082f7c2b)
has neither `tools/bazel/test_equivalence.sh` nor
`tools/bazel/equivalence_checker/`. Port them from the sonic-net PR in a
separate PR that image PRs depend on:

- Bring the checker with its tests (`rules_engine_test`, `reporter_test`), the
  pinned compareELF archive and patch in `equivalence.MODULE.bazel` with the
  root `MODULE.bazel` `include()`, and the helpers it imports from
  `tools/bazel/registry/registry_lib.py`.
- Keep the comparison, rule format, exit status, and the clean-tree and
  Bazel-disabled guards. Start `rules.py` with only `excluded-by-tag`, and add
  other rules with this repository's evidence, even when the sonic-net PR
  accepts the same difference.
- Adapt the parts that discover pairs and tools:

| sonic-net/sonic-buildimage#28005 | This repository |
| --- | --- |
| The guard checks `BAZEL_MIN_READINESS` | Check `BUILD_WITH_BAZEL_WHEN_AVAILABLE` until the readiness switch is adopted |
| Images are `kind("gzip rule", //dockers/...)` targets of the PR's own `gzip` rule | [`sonic_docker_archive`](https://github.com/securely1g/sonic-buildimage/blob/7ebff36d33fbc218c9c101e024749a36082f7c2b/tools/bazel/oci/sonic_docker_archive.bzl) creates `gzip_compress` targets from `rules_gzip`, and VS images such as `docker-syncd-vs` live under `platform/vs/` |
| DEB owners are the `src/*/MODULE.bazel` modules, all overridden to `src/` by `--config=local-modules` | Root dependencies such as `sonic-swss-common` resolve to registry versions; apply the same-source step above to each discovered DEB |
| `readelf` comes from `@sonic_build_infra//toolchains/binutils:readelf`; `abidiff` and `dpkg-deb` from the slave | This fork's `sonic-build-infra` has the same `readelf` target |
