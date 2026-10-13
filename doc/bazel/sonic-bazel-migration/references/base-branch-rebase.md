# Keep open PRs current with their base

During authorized PR babysitting, assess every open in-scope PR each cycle,
including drafts and PRs without new activity. Necessary rebases and force
pushes within `securely1g` are authorized. Preserve existing owner, merge,
branch-deletion, and repository-settings limits.

## Observe and assess

Read each PR's current base and head repositories, refs, and SHAs. Fetch both
refs with the configured identity. Use the selected base (`master`, `main`, or
a stacked PR branch); do not retarget a stack merely to reach `master`.
Verify the live base tip from `baseRef.target.oid` against the fetched ref;
`baseRefOid` alone can describe an older PR base. A missing/deleted ref requires
investigation, not substitution of another branch. Verify action destinations
remain in scope.

Check ancestry, merge base, individual patches, and the cumulative PR diff.
Detect changes already merged into the base, including squash and cherry-pick
merges with different SHAs. Use patch equivalence and inspect relevant source
when partial overlap or conflict resolution prevents an exact match. Titles
and a merged PR label alone do not establish equivalence.

Rebase when it removes already-merged changes, resolves a demonstrated
integration conflict, incorporates a required base fix, or satisfies a required
up-to-date check or explicit user request. Unrelated base advancement alone
does not justify rewriting a clean independent PR.

Common PR #11 illustrates the rule: after Common #9's YANG fixture fix lands in
`master`, rebase to retain only the Rust binding commit. Drop the redundant
fixture commit and merge-only history. Do not retain an obsolete base or create
empty commits to preserve an old count. Keep independent remaining changes in
separate commits; apply the one-commit rule to updated infra/registry PRs.

If all changes are already in the base, record the PR as superseded and report
through the existing workflow. Do not push an empty replacement, close/merge
the PR, or delete its branch without applicable authorization.

## Rewrite and verify

1. Verify a clean matching linked worktree is not in use by another build or
   editor. Preserve local work and use an isolated worktree when needed. Retain
   a local backup of the original head and record the original base/head.
2. Inspect recorded consumers and registry pins before replacing a source
   revision. Preserve required source commits through an appropriate retained
   ref and verify availability. Preserve published registry entries; assess
   consumer updates through the shared-dependency workflow.
3. Replay only still-required changes on the freshly fetched selected base.
   Preserve attribution and useful messages. Remove merge-only history only
   when the surviving commits contain its intended behavior; preserve actual
   conflict-resolution changes. Resolve conflicts when the intended behavior
   is established; otherwise abort the local attempt, record the concrete
   conflict, and continue independent work.
4. Compare the new base-to-head diff and old/new patches (`git range-diff` where
   applicable). Prove dropped changes exist in the base and surviving changes
   remain complete. Verify commit counts, identities, and `git diff --check`.
   Identical final Git trees establish preserved file content for a history-only
   rewrite. Changed content or integration behavior needs focused build/test
   validation; avoid rebuilding an identical tree without another reason.
5. Immediately before pushing, reread PR state, target, remote head, and live
   base tip. Refresh and reassess if either ref moved. Verify the destination,
   then use `--force-with-lease=<full-head-ref>:<verified-old-SHA>`. Never bypass
   a failed lease or overwrite concurrent work. A head lease does not protect
   against movement of the base, so check both refs.
6. Read back published head, base, commit list, and cumulative diff. Update the
   PR description to its remaining scope. Record old/new SHAs, dropped changes,
   validation, and pending CI in triage. After interruption, inspect remote
   state before repeating a push that may already have succeeded.

Record every assessed base/head pair and its decision in triage. For unchanged
pairs with completed assessments, skip repeated diff analysis, builds, and
rebases; still retry unresolved work and react to new feedback/checks. Keep
no-op checks quiet and report material blockers/resolutions through the existing
blocker workflow without duplicate messages.
