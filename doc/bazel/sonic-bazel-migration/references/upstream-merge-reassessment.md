# Reassess downstream PRs after an upstream merge

Use this workflow during authorized SONiC Bazel PR babysitting. The user requested
automatic downstream reassessment after prerequisite PRs merge, including the
`sonic-bazel-registry` dependencies. This workflow uses existing repository and
publishing authority; it does not grant merge, repository-setting, or new-owner
permission.

## What triggers work

The Project's **All upstream PRs** field records direct prerequisites. If B depends
on A, B's field links to A. The collector reads these links, collects in-scope
prerequisites even when they have no Project row, and observes their merged state
and merge commit. Only owners permitted by the controlling service are eligible.
Preserve valid historical links after a merge; deleting them would remove useful
dependency evidence.

Open-only saved views show the derived **Upstream PRs** field, which omits
merged and closed prerequisites. This is a display filter only. Continue using
canonical **All upstream PRs** to discover merge events and preserve queued consumer
work even when that prerequisite is absent from the open-only display.

For each merged prerequisite and open consumer, the babysitter queues a durable
assessment. This also covers already-merged prerequisites on initial deployment
or newly recorded links. It does not require fresh activity on the consumer.
Blank or incomplete fields cannot describe dependencies that have not yet been
recorded: continue reconciling links from PR and code evidence, without inventing
relationships or expanding them transitively.

The scheduled agent must process the exact collection's
`dependency_reassessments` entries alongside ordinary feedback. Pending and
blocked entries remain work even if `activity_since_acknowledged` is empty.
Closed consumers are retired by the collector's state reconciliation; do not
reopen or modify a closed PR to complete its old assessment.

## Assess the actual consumer

1. Verify the upstream merge commit, the consumer's current head and target
   branch, and the recorded dependency evidence. Refresh a moved consumer branch
   before preparing changes. Use the existing PR worktree and preserve local work.
2. Compare what the consumer selects with the merged contents. A consumer may
   already contain the relevant change, or the merge may produce a different
   commit without changing its tree. State which condition applies with concrete
   revisions or file evidence; a green old check is not sufficient by itself.
3. For a registry prerequisite, inspect the consumer's registry commit or URL,
   `MODULE.bazel` versions and overrides, applicable lockfiles, and the selected
   registry module's `MODULE.bazel`, `source.json`, archive URL, integrity,
   patches, and overlays. Follow the registry version policy. Check all affected
   direct inputs; do not assume changing a single pin completes a version change.
   Apply the [registry endpoint gate](shared-dependency-workflow.md#require-landed-registry-endpoints-before-review):
   remove a temporary validation override only after every required entry is
   available on the maintained branch, and verify its sources. Both local builds
   and CI then use the committed canonical registry URL; record the observed
   registry revision as evidence without pinning the URL to it.
4. When needed, make the smallest coherent consumer update, run validation for
   the changed dependency boundary, push the intended PR branch, and verify the
   published head. Reconcile the PR description and Project dependency evidence.
   Registry changes may require a separate PR per module under the skill's
   existing rule. Preserve established owner and action limits.
5. If no change is needed, record why the merged dependency is already satisfied
   and which revisions, selected inputs, and validation establish that result.
   If work is blocked, record the concrete obstacle and evidence, complete
   independent authorized work, and follow the blocker-reporting reference.

For example, after a registry PR merges, a consumer may still use its temporary
integration branch or pre-merge commit. Switch local builds and CI to the
canonical maintained branch, removing the temporary override. Update effective
configuration and reproduction docs together, validate
the selected modules and relevant consumer tests, and retain any tree comparison
as evidence. A consumer already selecting eligible merged inputs can finish with
an evidenced no-change decision. Missing or unverifiable required entries keep
or return the consumer to Draft. Audit quiet Ready consumers too, without waiting
for another merge event.

For every consumer PR, also apply the
[PR draft-state rule](pr-merge-readiness.md). Keep Draft while any selected
dependency commit is unlanded or unverifiable, including a stacked prerequisite,
sources resolved through a registry, external CI inputs and consumed artifacts.
A prerequisite PR's merged state or an identical tree does not make its retained PR-head snapshot
ready. Registry PRs additionally require a maintained `master`/`main` base
without stacking and verified landed SONiC source registrations. Refresh the
consumer coherently before marking it Ready for review; respect explicit user
draft holds. Rerun required validation for the changed boundary. CI still gates
merging and may be pending when the PR becomes Ready for review. A draft-state
change alone leaves an obsolete dependency pin unresolved.

## Record each decision

For this package, the machine-readable ledger is
`<state-dir>/dependency-reassessments.json`. Immutable collections capture the
tasks presented to each cycle. Return one `dependency_assessments` result entry
per task, with:

- `task_id`: the exact ID from the collection.
- `status`: `updated`, `no_update_needed`, or `blocked`.
- `evaluated_head`: the consumer head recorded in that collection's task.
- `resulting_head`: the verified published head after an update, or the same
  head when unchanged.
- `evidence`: nonempty concrete reasons, commit/file or PR links, and applicable
  validation results. Explain any head movement observed since collection.

Use `updated` only when the head changed and the resulting branch satisfies the
assessment. Use `no_update_needed` only when the head is unchanged and the
dependency is already satisfied. Use `blocked` when the assessment cannot yet
finish; do not disguise unfinished work as a no-change decision. If a previous
cycle pushed before it failed to save its result, inspect that published work
and finish against the current head rather than repeating the change.

The runner validates the structured result before persisting decisions and
acknowledging the collection. Omitting a queued task prevents acknowledgement.
Completed decisions remain in the ledger; blocked tasks appear again in later
collections. Global activity acknowledgement does not discard unfinished
dependency work.

Also retain a readable summary in `TRIAGE.md`: task ID, upstream PR and merge
commit, consumer PR and assessed/resulting heads, decision, validation, branch
or PR changes, and unresolved conditions. The structured result and ledger are
the processing record; prose alone does not complete a queued assessment.

For a real blocker, reconcile Project Attention and the managed blocker record.
Keep unchanged blockers visible without repeated comments, mentions, or status
updates. Clear Attention only when no blocker remains on that PR. An upstream
merge or a queued assessment alone is not a user decision and needs no alert.
