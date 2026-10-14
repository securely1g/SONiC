# Refresh shared dependencies and retire workarounds

Use this workflow when a component migration changes shared toolchains or registry
inputs, or when a proposed workaround may already be superseded. Apply the checks
at the affected boundary; this does not require a full migration or image build
for every dependency edit, or grant additional publishing or merge authority.

## Split features and identify their consumers

- Keep independent features in separate PRs. Include the implementation, regression
  coverage and necessary CI changes for that feature. Keep each build-infra or
  registry PR at one commit relative to its actual base, including stacked bases.
- Explain each feature's need in its PR description: link its consumer PRs when
  available, name the target or build path that uses it, and describe the failure
  or missing behavior it addresses. When no consumer PR exists, state that and
  name the verified consumer repository and target. Verify these relationships
  in the source and selected inputs; a general repository dependency is insufficient.
- Distinguish a source consumer from a registry registration that distributes the
  implementation. State whether the consumer selects the proposed revision or an
  older snapshot containing the change; a description link alone does not update
  its source or registry selection.
- Base independent features on the target branch. Use a stacked base only when
  one feature actually requires another. Make CI select each feature's tests
  independently, verify each PR on its actual base, and check their combined
  changes for conflicts. Preserve referenced prior snapshots during a rewrite.
- After a split, rewrite the source PR titles and descriptions around their final
  scope. Update affected consumer descriptions, registry prerequisite references,
  and Project canonical/derived links and README. Keep Project edges limited to
  direct prerequisites; explain transitive relationships in the descriptions.

Example: Python wheel installation and tar ownership are separate features within
the same `sonic-build-infra` module. [Wheel layers #9](https://github.com/securely1g/sonic-build-infra/pull/9)
serve [Buildimage #2](https://github.com/securely1g/sonic-buildimage/pull/2), which
installs Scapy and pyroute2 in the SWSS container. [Tar ownership #16](https://github.com/securely1g/sonic-build-infra/pull/16)
serves both Buildimage's runtime/debug layers and [SWSS #2](https://github.com/securely1g/sonic-swss/pull/2)'s
standalone debug archive, whose generated directories must be root-owned.
[Registry #23](https://github.com/securely1g/sonic-bazel-registry/pull/23) distributes
both helpers; standalone SWSS uses the ownership portion through that registry
history. Recheck current selections when applying this example to new work.

## Establish the need on the current base

Compare the proposed behavior with the current target branch, not just the old
PR branch. Inspect the implementation and its consumers before adding a feature
toggle or backport. If the target already contains the desired fix, determine
whether any real consumer still needs different behavior. An option's own tests
are not evidence of such a consumer. Avoid restoring an obsolete default while
refreshing an older patch.

Record the dependency chain as distinct inputs:

| Input | Evidence to inspect |
| --- | --- |
| Shared implementation | Source commit and cumulative changes from the consumer's baseline |
| Registry entry | Version, archive, integrity, patches, and overlays |
| Consumer selection | Registry URL and observed revision, module declarations, overrides, and checked-in ecosystem/package pins |
| Actual resolution | Resolved graph, fetched module declaration, and CI-generated `MODULE.bazel.lock` |

Search existing shared PRs and registrations before implementing another fix.
Choose a version for the required configuration set, not simply because it is
newest or merged. An upgrade can also change compiler hardening, optimization,
linking, deployment stripping, and debug rules. Follow the registry version policy;
preserve existing published entries and production patch bytes when they are not
the subject of the change.

Apply the [component-source and lockfile policy](source-builds-and-lockfiles.md):
the component being migrated must build from its declared source. External
dependencies may be compatible source modules or pinned binary packages with
declared ABI, architecture, integrity, and runtime requirements. Do not label
package imports as dependency source builds or require their replacement merely
to complete a component migration. Keep generated Bazel resolution state out of
Git without removing explicit declarations and package locks. When changing a
published registration's implementation, add a new version, verify actual
consumer resolution, and preserve the historical entry unchanged. Apply the
draft-version distinction below to entries introduced by an open PR.

## Select one endpoint per registry repository

Apply the skill's one-endpoint rule to the consumer's effective registry list,
including `.bazelrc` imports, CI flags, wrapper scripts, and documented commands.
Group endpoints by the repository they serve; different URL spellings do not
make branches or snapshots of the same repository independent registries. Keep
separate registries such as SONiC and Bazel Central Registry when required by the
graph. Local builds and CI follow the same
[maintained-branch policy](../SKILL.md#use-main-registry-urls-for-local-builds-and-ci).
Commit the canonical `main` URL in `.bazelrc`; do not maintain a separate local
registry SHA or a CI-only rewrite from that SHA to `main`.

When refreshing a consumer:

1. Record its current registry URL, required module versions, overrides,
   and supported native architecture and feature matrix. Inspect the registry's
   current canonical `main` and record its checked SHA as validation evidence.
   Both local builds and CI use the maintained branch URL, not that recorded SHA.
2. Verify that the candidate contains every required registration from that
   repository. Preserve compatible module versions and source pins. When changes
   are needed, update affected direct and transitive module selections together;
   inspect their declarations, source archives, integrity, patches, overlays and
   prerequisite source commits. Do not append an old PR endpoint as a fallback
   for a missing version.
3. If `main` lacks necessary unmerged work, leave the committed default on `main`.
   Draft validation, locally or in CI, may explicitly select one authorized,
   reviewed temporary branch containing those entries, such as a stack of
   one-module registry PRs. Name the missing module versions and prerequisite
   PRs, and record the branch's observed commit without putting that SHA in the
   URL. The temporary selection must replace the default endpoint, not append
   to it: Bazel's repeatable `--registry` option can retain `.bazelrc` entries
   when another is supplied on the command line. Inspect the effective options.
   If the combination cannot be prepared or validated, retain a blocker naming
   the missing entries. Do not combine unrelated modules in one registry PR or
   merge prerequisites without authorization.
4. Update the consumer's registry configuration, module declarations, related
   pins, CI, and documented commands together. Preserve historical registry
   entries and referenced commits; the rule concerns the active selection.
5. Regenerate ignored resolution state and inspect the resolved graph and fetched
   module declarations to prove which entries and source revisions Bazel chose.
   Validate the affected boundary on every required native architecture and
   feature mode under the existing execution permissions. Record exact inputs,
   results, and pending coverage; an AMD64 pass alone does not establish ARM64
   compatibility. A registry selection is only a candidate until these checks pass.

Keep claims of "latest compatible" tied to the inspected canonical `main`
revision and validation evidence. Identify temporary branches as Draft validation
inputs even when their consumer checks pass. Missing entries do not justify a
registry SHA; any verified Bazel exception must meet the separate policy above.

## Require landed registry endpoints before review

Before a consumer becomes or remains Ready for review, both local builds and CI
must use the registry's canonical maintained `main`/`master` endpoint. Remove
all temporary validation overrides, even after their entries merge. A verified
and documented Bazel exception must select a registry commit proven landed on
the maintained branch using the
[provenance checks](pr-merge-readiness.md#verify-the-selected-source-revisions).
There is no separate immutable-snapshot policy for local builds. An unlanded
snapshot does not qualify because its tree matches a landed commit. This gate
covers consumed dependencies, not a registry PR's own proposed entries under test.

Check every required direct and transitive registration at the chosen endpoint,
including module versions, source revisions, archive integrity, patches and
overlays. Refresh all effective `.bazelrc` imports, workflow flags, wrapper
scripts and documented commands together, then verify current consumer resolution
and validate the affected boundary before promotion. Report pending CI accurately
under the existing PR readiness rule.

Recheck this gate on updates, prerequisite merges and every complete successful
babysitter collection, including quiet Ready PRs. If required entries or their
provenance are missing or unverifiable, keep or return the consumer to Draft and
record the known prerequisite PRs. Retain an explicit reviewed temporary override
only for Draft validation; revisit it after those prerequisites land. Record
checked revisions, selection evidence and the verified Draft/Ready result without
repeated alerts.

## Keep one current version in an unmerged registry PR

Keep one current candidate for the module introduced by an unmerged registry PR.
When its source revision changes, replace the superseded draft registration;
do not accumulate a new retained directory for each PR push or successful CI run.
A draft entry being available at a PR commit does not by itself make it a release.

- Compare with the actual PR base, including a stacked base. Preserve versions
  already on that base and versions merged or explicitly released independently
  of the draft PR. This cleanup is limited to superseded candidates introduced
  by the PR; do not prune older entries elsewhere in the registry.
- Check affected consumers' module versions and registry revisions. Update
  consumers that need the revised PR contents and validate their selection.
  Move temporary Draft validation overrides to the reviewed branch containing
  the current candidate. Keep previously referenced commits reachable for
  historical evidence; do not retain an old registry SHA as a local-build policy.
  Record a concrete compatibility need before retaining an extra draft candidate,
  and honor an explicit latest-only request by resolving that need rather than
  silently retaining extra versions.
- Remove superseded draft directories and metadata entries together. Point the
  current entry at its exact source commit, keep its module declaration, source
  integrity, patches, and presubmit consistent, and rewrite documentation and the
  PR description around the final candidate.
- Validate the retained entry through its supported native consumer matrix and
  check the CI plan contains no jobs for removed drafts. Keep the shared PR at
  one commit relative to its actual base and follow the existing identity and
  exact force-push lease rules.

## Prove selection before extending the build machinery

Try ordinary module resolution first. Verify the selected shared dependency,
including its fetched declaration; a runner that checks only the module under
test does not necessarily check its dependencies. Keep an override when needed
for a demonstrated resolution, source-selection, or temporary validation purpose;
remove it when ordinary resolution satisfies that purpose. A failed consumer build is not by itself a
reason to extend the CI runner or add a feature switch: locate the owning layer.

## Validate the actual combination, starting with small probes

Refresh the branch against the intended current base. Changing the PR's base in
GitHub alone does not do this. Use the default integration branch when independent;
keep an explicit stack when an unmerged prerequisite supplies required contents.
Preserve the one-module-per-registry-PR boundary. Record the base and head SHAs,
and validate their merge result, or prove the base is already an ancestor of the
tested head. After a rewrite, verify the resulting diff and retained inputs.

For architecture-sensitive toolchain changes, prefer small real compile, link,
and runtime probes on affected supported execution/target pairs when they provide
faster feedback than downstream builds. Existing focused matrix checks can supply
the same evidence without a separate probe stage. These checks can expose
unsupported CPU flags early; they do not replace the required feature-mode,
binding, package, debug, and analyzer checks.
Do not infer ARM support from an AMD64 pass or hide a failure by dropping a
supported configuration.

Once a coherent candidate is ready for publication within existing authority,
overlap independent local, architecture, and analyzer checks where useful. Tie
each result to its exact inputs. Preserve before/after source evidence if a build
ran before the final commit; a comment-only delta can be shown explicitly, while
changed build inputs need new relevant validation. Record executed versus cached
tests, pending checks, and collected versus uploaded artifacts accurately.

## Attribute runtime behavior to the right artifact

Distinguish `-rpath` (embedded runtime search) from `-rpath-link` (link-time library
lookup). Inspect the link inputs and ELF, not only a removed flag in a toolchain
file: imported Debian or pkg-config dependencies can supply paths independently.
Compare the old and new raw ELF before calling a retained path a regression.

Inspect raw Bazel outputs, the deployment-transformed ELF, and the actual package
separately. Relative Bazel runfile paths can be necessary for build-time consumers;
the deployment rule can remove them before packaging and debug splitting. Record
the selected deployment mode and verify the resulting runtime/symbol pair. A
package check does not establish that an installed SONiC image boots or loads the
same library.

## Retire the obsolete chain after consumers move

Update the affected consumer pins and validate the replacement boundary before
closing a prerequisite they still select. Remove obsolete imports, feature
settings, overrides, and runner dependencies only where they are no longer
needed. Preserve released module entries and keep still-used source and registry
snapshots reachable through authorized history changes. Superseded entries
introduced only by the open PR follow the draft-version workflow above.

Within the task's authority, close the superseded proposal and rewrite affected
PR descriptions around the final implementation. Reconcile direct dependency
links using the skill's Project workflow: changed dependencies can be replaced;
a PR's merged or closed state alone does not erase a historical relationship.
Separate completed migration work from any remaining validation or external wait.

## Periodically review open PRs

After each complete successful babysitter collection, assess every open in-scope
PR for superseded or duplicate work, changes already on its current base, and
abandoned workarounds without a real consumer. A newer version, inactivity, or
green tests alone does not make a PR obsolete.
Reuse an evidenced assessment while its head, base and dependency inputs remain
unchanged; reassess changed inputs and continue pending migrations and blockers.

Compare the current base and head, concrete consumer selections, and stacked PR
bases. Follow the source, registry, and resolved-dependency checks above; Project
links alone are not a complete consumer inventory. Publish and validate needed
consumer migrations before retiring their prerequisite. Recheck current heads
and dependencies before closure. Keep the PR when it still supplies unique
behavior or a needed route for another PR to reach its integration branch.

Record `keep`, `migrate`, `close`, or `blocked` in the triage record with the
evaluated revisions, reason, consumer/stack evidence, replacement and validation
links, and pending work. Revisit pending migrations and blockers in later cycles;
keep unchanged decisions quiet.

For authorized closure, post a concise reason with replacement and test links,
verify the closed state, and reconcile Project fields and the README. Preserve
immutable sources, registry entries, branches and snapshots; retain accurate
historical dependency links. An explicit user instruction may retire a proposal
while named consumers retain historical snapshots. Record that exception, prove
their inputs remain reachable, and keep any unresolved integration work pending;
do not infer the same exception for other PRs.

## Historical example: runtime-path retirement, 2026-09-28

These are evidence from this task, not permanent version recommendations:

- The optional runtime-path proposal in [build-infra #4](https://github.com/securely1g/sonic-build-infra/pull/4)
  was unnecessary on the refreshed base. Its [registry entry #8](https://github.com/securely1g/sonic-bazel-registry/pull/8)
  remained a dependency until the consumers were migrated.
- Published infrastructure 0.0.5 passed AMD64 but applied x86 `-fcf-protection`
  to ARM64. The [failed native run](https://github.com/securely1g/sonic-bazel-registry/actions/runs/36442067755)
  disproved its suitability. Existing infrastructure 0.0.7 in [registry #4](https://github.com/securely1g/sonic-bazel-registry/pull/4)
  already included CPU-specific hardening and the required runtime-path behavior.
- [Registry #9](https://github.com/securely1g/sonic-bazel-registry/pull/9) and
  [Common #6](https://github.com/securely1g/sonic-swss-common/pull/6) selected 0.0.7
  without the old feature import or root version override. Registry #9 remained
  stacked on registry #4 to keep its diff limited to libyang-Python.
- Common's raw library retained pre-existing `/usr/lib*` paths from Debian import
  metadata; the validated package removed all runtime paths under
  `make_built_base=True`. Other deployment modes have different semantics.
- [Consumer CI](https://github.com/securely1g/sonic-swss-common/actions/runs/36445077519)
  tested current `master` plus Common head `9ad74e45` on native AMD64 and ARM64,
  with both YANG modes and matching debug archives. Registry #8 then closed
  unmerged; [C++ and Python CodeQL](https://github.com/securely1g/sonic-swss-common/actions/runs/36445077594)
  also passed. These results did not include an installed-image boot.
