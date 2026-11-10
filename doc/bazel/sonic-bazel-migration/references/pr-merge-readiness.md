# PR draft and review readiness

Apply this rule to every open SONiC Bazel migration PR within the authorized
scope. An unlanded dependency relevant to the proposed change keeps a PR in
Draft, regardless of which repository owns it. Registry PRs also have the base
requirement below. Do not rewrite published historical registry versions.

## Check for merge conflicts

Before promoting a PR or reassessing an existing Ready PR, read the live PR
head, target repository and branch, current target tip, and GitHub's `mergeable`
field. Use the PR’s actual target, including a stacked base. Repeat the check if
the head, target repository or branch, or target tip changes. Earlier GitHub
and local results apply only to the recorded refs.

- `MERGEABLE` passes only the conflict check for those revisions. Evaluate the
  remaining readiness requirements before promoting or confirming readiness.
- `CONFLICTING` keeps a Draft PR in Draft. Return an already-Ready PR to Draft
  when authorized to manage readiness. Record the conflicting revisions, resolve
  the conflict within the task's scope, and check the resulting head against
  the latest target before restoring Ready.
- For `UNKNOWN`, retry the live query after GitHub recalculates. A Draft PR
  remains Draft. If `UNKNOWN` persists for a Ready PR after bounded retries,
  diagnose the exact current head and target-tip SHAs locally with
  `git merge-tree --write-tree`. A reproducible local conflict warrants Draft.
  A clean or inconclusive local result preserves the existing Ready flag while
  readiness remains unconfirmed pending another live query. Record the result
  and leave verification pending for a later authorized retry. A clean local
  merge is diagnostic only; it never substitutes for GitHub `MERGEABLE`.
  This preservation applies only to mergeability uncertainty; other Draft
  requirements still apply.

For example, a passing AMD64 build at the last PR head can coexist with a merge
conflict introduced by a later target update. Check GitHub’s mergeability
separately from required CI, review approvals and branch protection.
Publishing a conflict resolution or setting Ready still follows the task’s
existing authorization for those actions.

## Scope readiness to the proposed change

Unchanged, unrelated dependencies inherited from maintained `master` or `main`
must not keep a PR in Draft. Compare the current PR diff and effective inputs
with that branch. Gate on dependencies the PR introduces, changes, or needs for
its proposed behavior or validation, including relevant transitive inputs.
An unchanged dependency can still be relevant; absence from the diff alone is
not an exemption. A repository-wide CI trigger alone does not establish that
the change needs every dependency used by that job.

Record the checked head/base, unchanged selection and reason for excluding an
unrelated dependency. Keep baseline issues visible separately, without making
their repair a prerequisite for the unrelated PR. Reassess when the scope or
relevant inputs change. Unmerged stacked prerequisites are not part of the
maintained baseline and remain subject to the dependency checks below.

For example, [buildimage #82](https://github.com/securely1g/sonic-buildimage/pull/82)
changes dashboard job classification and upload timing in `collect.py` and its
README. Its metadata tests do not execute the runner manager. The unchanged
installer workflow inherited from `master` pins manager commit `549469b` from
[agi-projects #60](https://github.com/securely1g/agi-projects/pull/60); that pin
must not hold this dashboard-only change in Draft. A PR that changes or needs
that manager must still verify its provenance. Required CI, accurate result
reporting and merge protections remain in effect for both PRs.

## Identify the dependencies actually consumed

Within the scope above, inspect the current PR head and the inputs selected by
its build, tests, CI and published outputs. Check direct Git or archive pins,
module overrides,
submodules, external CI checkouts or workflow/action references, and consumed
artifacts. Resolve registry URLs and module versions through their selected
`source.json`, patches and overlays; a maintained registry branch can still
select an unlanded source commit. Follow relevant transitive selections rather
than treating the dependency names or PR descriptions as proof of provenance.
For consumed artifacts, verify the producer's source revision, not only the
artifact's checksum or successful CI run.

Apply the [registry endpoint gate](shared-dependency-workflow.md#require-landed-registry-endpoints-before-review)
before retaining or setting Ready: local builds and CI must use the canonical
maintained branch and have no temporary registry override. A verified documented
Bazel exception must select a landed registry commit; local builds have no
separate snapshot exemption. Temporary integration endpoints are for Draft
validation only, even when their entries have since merged. Verify all required
entries and selected sources after a refresh.

A prerequisite inherited through a stacked PR base is a consumed dependency,
including a prerequisite in the same repository. Distinguish those inherited
changes from the PR's own proposed delta. The PR's own implementation, checkout
and outputs under test do not cause a draft hold by themselves. Historical
metadata, unused examples and references that the current proposal does not
consume are not dependency pins. Third-party releases and package snapshots
retain their existing source and version policies; an unlanded fork or PR
snapshot does not qualify as a release merely because it has a version string.

## Verify the selected source revisions

For each in-scope dependency commit, record its repository, maintained `master`
or `main` branch, observed branch tip, selected SHA and corresponding source PR's landed
SHA when there is one. For SONiC registry registrations, include every proposed
source version in the current diff, even if no consumer selects it yet.

Use the resulting merge, squash or rebased integration commit that landed on
`master`/`main`, or a later compatible commit on that branch. Do not retain a
reviewed PR-head snapshot merely because its PR was merged, its contents match,
or its commit is reachable through a merge's second parent. Verify the landed
SHA in the maintained branch's first-parent history; a fast-forwarded source
commit may itself be that landed revision. A previously verified landed commit
remains eligible when unrelated commits advance the branch. Keep immutable
full-SHA source pins where the existing policy requires them; maintained branch
URLs still require checking the actual resolved revision.

When refreshing a pin, update all dependent version declarations, source URLs,
integrity values, patches and CI references coherently. For a registry module,
the source SHA in its version directory, `MODULE.bazel`, metadata and version
patch must agree with `source.json`. Follow the
[draft-version workflow](shared-dependency-workflow.md#keep-one-unreleased-candidate-per-module)
for registry candidates and preserve published historical entries. Verify
archive integrity, patched module contents and actual consumer resolution, then
rerun required validation for the changed boundary. Tree equality is useful
evidence but does not waive the landed-revision requirement.

## Verify the registry PR base

Every registry PR must target the registry's maintained `master` or `main`
before becoming Ready for review, including third-party registrations. Read the
live base repository, branch and revision. Keep Draft while it is stacked on
another PR or targets another branch. Do not retarget merely to change draft
state. After its prerequisite merges, follow the
[base-branch rebase workflow](base-branch-rebase.md) to preserve the intended
diff, retarget when appropriate and verify the new base.

## Restore temporary CI branch filters

As part of making a PR Ready for review after retargeting a stack to the
repository's maintained `main` or `master`, restore any `pull_request`
target-branch filters removed or widened only to validate that stack. Apply
the same cleanup when reassessing an already-Ready PR. Inspect workflow history
and the maintained-branch baseline to recover the original filters; do not
hardcode `master` or narrow intentionally broader coverage approved by the user.

Check every affected workflow, including native build/test and CodeQL workflows.
Keep the `pull_request` trigger and limit the cleanup to the temporary filter
change. Preserve unrelated triggers, job settings, path filters and analysis
coverage. If the original filters do not include the final target branch,
resolve that mismatch from the repository's current CI policy before claiming
cleanup is complete.

After publishing the cleanup, follow [source PR CI completion](source-pr-ci.md)
to verify the expected PR jobs still run for the final head and intended base.
Record the head, workflow/run URLs and observed jobs; prior runs or an empty
Checks tab do not verify the restored filters. Keep pending results distinct
from success and retain the existing informational CodeQL policy.

## Remove branch-specific CI exceptions

Do not mark or retain a PR as Ready while its resulting code contains temporary
branch-specific checks or skips. This includes branch-name, PR-number and
equivalent special cases that add checks as well as those that skip, replace
or weaken them. Inspect workflow conditions and the scripts they call,
including inherited special cases; green CI does not waive this gate. Preserve
legitimate default-branch, release and event triggers that implement the
maintained CI policy.

Assess the current checkout, not matches in deleted diff lines. A PR that
removes the special cases can be Ready when none remain and the other applicable
readiness requirements pass. Removing branch-specific checks is not itself a
reason to keep that PR in Draft.

Remove the special case rather than extending its branch allowlist or renaming
the branch to evade it. Put necessary checks in the normal suite with applicable
configuration-based selection. Run that suite, including existing
approved packaging tests and their temporary sample DEBs. The
[DEB approval rule](../SKILL.md#require-approval-before-adding-new-deb-package-definitions)
concerns new package definitions, not ordinary execution of existing tests.

For example, [infra #78](https://github.com/securely1g/sonic-build-infra/pull/78)
selected `//tools/build_tools:kernel_runtime` on `codex/dash-ha-rust-deps`
instead of `//tools/build_tools:kernel_runtime_test`. Building the tool bundle
omitted all of the test's execution checks, while `master` would run them.
Remove the special case and run the test on the PR as well.

Follow the task's validation requirements and
[source PR CI completion](source-pr-ci.md) for final-head checkout and result
provenance. Verify logs or test results show previously omitted checks actually
ran before claiming full coverage; earlier green runs with the exception do not
qualify. Honor an explicit request to wait for passing CI before setting Ready.
Reassess already-Ready PRs under the same code-state gate and return them to
Draft when special cases remain.

## Reconcile Draft and Ready for review

On authorized PR creation, refresh, base changes, upstream-merge reassessment
and every babysitter cycle, inspect the current inputs and GitHub draft state.
Apply the scope assessment above before this table:

| Current evidence | PR state |
| --- | --- |
| An unchanged, unrelated dependency is inherited from maintained `master`/`main` | No Draft hold from that dependency; assess the remaining applicable requirements |
| An in-scope dependency commit is unlanded or its required provenance cannot be verified | Draft |
| An in-scope registry selection uses a temporary endpoint or ineligible registry commit, or required entries are unavailable | Draft |
| A registry PR proposes an unlanded or unverifiable SONiC source version, is stacked, or does not target maintained `master`/`main` | Draft |
| Temporary CI branch-filter cleanup is still needed after retargeting a stack | Draft |
| Temporary branch- or PR-specific checks or skips remain in the resulting code | Draft |
| The PR removes branch-specific checks or skips and none remain | No Draft hold from their deleted diff lines; assess the remaining applicable requirements |
| Required Make equivalence results are missing, pending, failed or stale | No Draft hold from equivalence alone; a passing run on the current head is required before merge |
| GitHub reports `UNKNOWN` | Draft remains Draft. For Ready, retry and diagnose the exact refs locally: a reproducible conflict warrants Draft; a clean or inconclusive result preserves the existing Ready flag while readiness remains unconfirmed pending retry. Other Draft requirements still apply. |
| GitHub reports `MERGEABLE` for the current head and target tip, dependency provenance, registry endpoint and any registry base/source requirements pass, and applicable CI filter/exception cleanup is complete | Ready for review, unless the user explicitly holds the PR in Draft for another reason |

An upstream merge triggers reassessment; it does not make a consumer ready
while an in-scope dependency still selects the former PR head. A head, base or
selected-dependency change invalidates the old assessment. Verify current inputs
before confirming readiness, and return the PR to Draft if required
in-scope provenance cannot be established. Respect explicit user draft holds
until they are lifted.

Use GitHub's Draft/Ready for review state instead of readiness labels. When
applying this rule, remove `not-ready-to-merge` and `ready-to-merge` if present;
preserve other labels and repository label definitions. Record the concrete
reason, revisions and validation evidence in triage records. Keep PR descriptions
focused on implementation, provenance and validation; do not add readiness-reason
sections or recurring readiness comments. Recheck the head and base before
mutation and read back the head, base, draft state and labels afterward. If
inputs moved, reassess them.

Ready for review is not merge approval. Required CI may still be pending or
unsuccessful when dependency provenance passes; required checks and existing
merge requirements continue to gate merging. For affected image and DEB PRs,
the [Make equivalence check](make-bazel-equivalence.md) must pass every pair in
the PR's required comparison set on the current head before merge or migration
completion. Unrelated pairs remain separately reported diagnostics under that
procedure. Its
status alone must not keep or return a PR to Draft. Keep CodeQL informational under
[the CodeQL policy](../SKILL.md#keep-codeql-informational), report its real results,
and do not make its status alone a reason to block merging or return a PR to
Draft. Report validation accurately and complete the required checks. This rule
does not enable auto-merge, merge a PR, or grant merge authority.
