# Refresh shared dependencies and retire workarounds

Use this workflow when a component migration changes shared toolchains or registry
inputs, or when a proposed workaround may already be superseded. Apply the checks
at the affected boundary; this does not require a full migration or image build
for every dependency edit, or grant additional publishing or merge authority.

## Split features and identify their consumers

- Keep independent features in separate PRs. Include the implementation, regression
  coverage and necessary CI changes for that feature. Keep one logical commit per
  independent fix or feature; a single-feature build-infra or registry PR normally
  has one own commit relative to its actual base, including a stacked base. Fold
  corrections into their feature's commit. If the user authorizes consolidation,
  preserve the separate feature commits even when they update one unpublished
  version. Follow the [commit-boundary rule](../SKILL.md#keep-one-logical-commit-per-fix-or-feature).
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

## Carry forward published patches and tests

Treat a new module version as the previous published version plus the intended
changes. A higher version number does not automatically inherit registry patches
or tests.

1. Read the previous published entry from the current maintained registry branch,
   including its current test coverage. Record the baseline commit and compare
   patch and test inventories; an old PR snapshot can omit later fixes or tests.
2. Carry forward its patches and supporting overlays before adding the new
   feature. Preserve unchanged patch bytes, document necessary adaptations, and
   follow the [upstream-verification rule](../SKILL.md#verify-existing-patches-before-switching-upstream)
   before removing a patch. Retain applicable regression coverage. In a stack,
   also preserve the prerequisite PR's additional changes and tests.
3. Retain fixtures, integration modules, build/test targets and native architecture
   coverage. Keep inherited tests selected in `presubmit.json`; storing their
   files without running them is insufficient. Update the integration module's
   dependency to the new candidate and verify the resolved version.
4. Run inherited and new tests on the supported native architectures. Compare
   identities and behavior, not only test counts, and record any adaptations or
   verified upstream replacements in the PR.

For example, `rules_distroless@0.9.4.sonic.11` supplies locked APT imports and
25 tests. A `.sonic.12` candidate adding Debian installation must retain the
importer, its patches and all 25 tests, then add the two installer checks for 27
tests. Copying an older
installer branch and changing its version number would lose the lock-import
behavior or its coverage. The integration test module must select `.sonic.12`,
so passing tests establish the new candidate's behavior.

<a id="keep-one-current-version-in-an-unmerged-registry-pr"></a>

## Keep one unreleased candidate per module

Apply this rule to the combined affected open PR stack, not separately to each
PR's added directories. Publication means the version is on the registry's
maintained `main`/`master`, or has a verified explicit release independent of the
draft stack. A version inherited from an unmerged PR base, referenced by another
PR, or used in successful CI is still unreleased. The actual PR base determines
its review diff and commit count; it does not establish publication.

- Before choosing or replacing a candidate, fetch the maintained branch and the
  actual PR bases. Record the observed SHAs and each relevant version's publication
  evidence. Search other open registry PRs touching the same module, including
  independent branches, and inspect their cumulative changes and source revisions.
  Do not assume a clean one-version diff proves the whole stack complies.
- Preserve published version directories and their entries in module metadata. Keep
  one current unreleased candidate for the module: update it as the source
  changes and remove superseded draft directories and metadata together. Keep
  independent feature reviews separate, but coordinate their registrations rather
  than retaining an extra draft release for each PR boundary. An unmerged stacked
  feature can amend the same candidate supplied by its base. Do not delete another
  PR's work or rewrite its branch without applicable authority; identify the
  affected PRs and coordinate the update. Resolve a consumer compatibility need
  before cleanup; it is not an implicit exception to an explicit latest-only request.
- Inventory affected consumer PRs and standalone builds. Record each declared
  module version, effective selected version, registry endpoint, temporary draft
  registry/source revision, and required feature. Inspect `MODULE.bazel`, overrides,
  `.bazelrc`/CI flags, resolved graphs and applicable generated lockfiles. Update
  consumers that need the revised candidate or still select a superseded draft,
  including temporary validation source pins. Verify actual resolution and the
  affected native tests; a description link or a higher requested version is not
  selection evidence. Record an evidenced no-change decision for compatible
  consumers, and keep unresolved consumer updates visible before claiming completion.
- Keep the candidate's module declaration, exact source commit, archive integrity,
  patches, metadata and presubmit consistent. Retain previously referenced source
  commits for historical evidence without treating those snapshots as published
  registry versions. Rewrite PR descriptions around the final contents and current
  prerequisites; preserve one logical commit per independent fix or feature and
  follow the exact force-push lease rules. One candidate version does not mean
  one commit; same-feature corrections still belong in that feature's commit.
- Immediately before deleting a draft entry or publishing a rewrite, reread the
  maintained branch, explicit release evidence, and affected PR heads/bases. If a
  candidate has now published, preserve its bytes and use the next revision for
  further changes. Reassess rather than applying an earlier cleanup plan. After a
  prerequisite merges, [rebase away already-landed changes](base-branch-rebase.md)
  and [refresh consumers](upstream-merge-reassessment.md); do not retain duplicate
  registrations or obsolete stacked-dependency descriptions.
- Run the registry candidate-policy check and inspect the native CI plan for the
  final tree. The check must compare with the maintained publication baseline,
  not only the selected stacked PR base; there should be no jobs for removed
  drafts. A branch check can detect multiple candidates present in that tree and
  changes to published entries. It cannot discover other open PR branches,
  independently published releases, or stale consumer selections. The inventories
  above remain required even when registry CI is green.

Run the supported planner from the registry checkout, with freshly verified full
SHAs (the actual PR base may differ from the maintained branch):

```sh
python3 ci/registry_ci.py plan --published "$maintained_sha" \
  --base "$pr_base_sha" --head "$pr_head_sha" --output plan.json
```

For a push to the maintained branch, add `--push` and use its pre-push SHA as the
publication baseline. This checks rollbacks as well as forward changes; using the
new head would misclassify all new candidates as already published.
`--all` still needs a publication baseline. If the selected registry checkout does
not yet have this guard, record the missing coverage and check these invariants
manually; do not report candidate-policy CI as passing.

For example, consider `libyang-python/3.1.0.sonic.3` in
[Registry #85](https://github.com/securely1g/sonic-bazel-registry/pull/85) and
`.sonic.4` in [Registry #102](https://github.com/securely1g/sonic-bazel-registry/pull/102):

| Observed publication state | Required treatment |
| --- | --- |
| Both registrations are still unreleased; #102 inherits `.3` from #85 and adds `.4`. | Coordinate one current candidate across the stack; inheriting `.3` does not protect it as a release. Keep the feature reviews separate without retaining both draft versions in the combined tree. |
| #85 has merged and published `.3`; #102 still needs additional behavior. | Preserve published `.3` unchanged and keep `.4` as the single new candidate. Rebase #102 onto the maintained branch, remove redundant commits, and refresh consumers that need `.4`. |

Recheck the live state when applying this example. A merge between those two
observations changes which entries may be replaced.

### One candidate can have two feature commits

The following is an illustrative workflow, not a claim about the bugs or live
state of the linked PRs. Assume `main` has published `libyang-python@3.1.0.sonic.2`:

| Step | Candidate directories after the step | Logical commits above `main` |
| --- | --- | --- |
| Parent PR adds a fix for Python extension linking. | Published `.2`, unpublished `.3`. | A: Fix Python extension linking. |
| Child PR adds runtime package metadata as a separate feature in `.4`. | Published `.2`, unpublished `.3` and `.4`. The candidate check fails. | A, then B: Include runtime package metadata. |
| Repair the child PR to apply B to `.3`, retaining A's linking fix; remove unpublished `.4` and its metadata entry. | Published `.2`, one unpublished `.3` containing both changes. | A, then B. Keep two commits because these are independent changes. |

Complete the repair as follows:

1. Fetch the maintained branch, affected PR heads and bases. Verify that `.3` and
   `.4` are still unpublished, inventory other open registrations and consumers,
   and record the intended commit boundaries before rewriting.
2. Keep A's feature commit. Rewrite B so its implementation, tests and metadata
   update `.3` instead of creating `.4`, preserving A's behavior. Fold fixes to B
   into B; do not squash B into A merely because both touch the same directory.
   Preserve contributor attribution and verify the combined diff. If the two
   features remain separate stacked PRs, each has one own commit relative to its
   actual base; their combined history has two. If the user authorizes combining
   them into one PR, that PR has two commits relative to `main`.
3. Update consumers that selected `.4` to `.3`, including applicable overrides,
   temporary registry/source selections and package pins. Regenerate ignored
   Bazel resolution state and verify the selected `.3` actually contains both
   required changes; editing only the PR description is insufficient.
4. Recheck publication and remote heads immediately before cleanup or push. If
   `.3` has published meanwhile, preserve it unchanged and use `.4` for B. Keep
   published `.2` unchanged in either case. Use an exact force-push lease for an
   authorized rewrite, then verify the remote history and diff.
5. Run the candidate-policy planner against the maintained publication baseline.
   With unpublished `.3` retained, verify that CI selects `.3` and no removed
   `.4` jobs. Rerun the affected module and consumer checks on required native
   AMD64 and ARM64 configurations. Record current heads, actual selection and
   results; pending CI remains pending.

The registry check enforces candidate and publication rules. The migration agent
or babysitter preserves feature commits and updates consumers; the CI check does
not rewrite branches or enforce the number of Git commits.

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
