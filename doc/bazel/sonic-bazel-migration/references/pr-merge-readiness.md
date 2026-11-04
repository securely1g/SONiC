# PR draft and review readiness

Apply this rule to every open SONiC Bazel migration PR within the authorized
scope. An unlanded dependency relevant to the proposed change keeps a PR in
Draft, regardless of which repository owns it. Registry PRs also have the base
requirement below. Do not rewrite published historical registry versions.

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

## Check landed commits mechanically

Squash and rebase merges land a new commit, and the PR-head commit that
consumers pinned during review never reaches the maintained branch. Check each
in-scope pin with Git rather than by comparing trees or file contents:

```sh
# pinned_sha must be the full 40-character commit ID.
git fetch origin main
git merge-base --is-ancestor "$pinned_sha" origin/main
git rev-list --first-parent origin/main | grep -qx "$pinned_sha"
```

The first command fails when the pin is not on the branch at all. The second
fails when the pin is reachable only through a merge's second parent, which the
landed-revision rule above also rejects. Then refresh the pin to the landed
commit and update every dependent version, URL, integrity value and CI
reference together.

Real examples from the sFlow review:

| Consumer | Pinned commit | Landed commit | Required action |
| --- | --- | --- | --- |
| registry #139 and buildimage #47 (kernel source) | `c894faf` (PR head before squash) | `34a53faa` (different tree) | Register and pin `34a53faa`; rerun validation |
| buildimage #146, #156, #158 (source mirror config) | `4f1b2b16` (registry #186 head) | `6974c59` (same file blob `a123e07c`) | Re-pin to `6974c59`, even though the file is identical |

Registry CI should run the ancestry check for every SONiC `source.json` commit
it adds. Babysitter cycles should run it for consumer pins after each
prerequisite merge.

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
| Dependency provenance, registry endpoint and any registry base/source requirements pass, and applicable CI branch-filter cleanup is complete | Ready for review, unless the user explicitly holds the PR in Draft for another reason |

An upstream merge triggers reassessment; it does not make a consumer ready
while an in-scope dependency still selects the former PR head. A head, base or
selected-dependency change invalidates the old assessment. Verify current inputs
before retaining Ready for review, and return the PR to Draft if required
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
merge requirements continue to gate merging. Keep CodeQL informational under
[the CodeQL policy](../SKILL.md#keep-codeql-informational), report its real results,
and do not make its status alone a reason to block merging or return a PR to
Draft. Report validation accurately and complete the required checks. This rule
does not enable auto-merge, merge a PR, or grant merge authority.
