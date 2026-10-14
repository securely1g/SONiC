# Source PR CI completion

Apply this guidance when implementing or assessing Bazel build support in a
component source repository. A documentation-only change or scoped investigation
does not require adding a native build matrix. Derive required configurations
from the component's declared contract and the user's task; do not copy another
repository's architectures or require an unrelated CodeQL migration.

## Establish source PR checks

Before declaring source CI complete:

1. Inspect the source PR's workflow changes and repository settings. Ensure the
   relevant source and build changes trigger PR jobs, including updates to the
   branch. Check branch/path filters, job conditions, disabled workflows, and
   pending workflow approvals. An enabled Actions setting or a workflow file
   alone does not prove that the jobs run.
2. Build explicit required targets and run the applicable tests in the source
   checkout. Verify every declared execution/target pair. For native AMD64 and
   ARM64 claims, record runner and userspace architecture evidence and the
   selected target configuration; cross-compilation or emulation is a separate
   configuration. A skipped, neutral, cancelled, or absent matrix job is not
   successful coverage.
3. Distinguish rebuilding or generating outputs from source from validating
   imported artifacts. A prebuilt library import, consumer link, or package
   inspection can validate an import contract without recompiling its producer.
   Apply the [component-source policy](source-builds-and-lockfiles.md): the
   migrated component must compile from its source, while external target/test
   dependencies may be pinned package imports, including native wheels. Verify
   their versions, integrity, ABI, architecture, and runtime closure. Describe
   those imports accurately; they do not prevent completion of the component
   migration or prove the dependency itself was compiled from source.
   Normal source CI may reuse caches once
   clean-build correctness is established; do not disable caches just to make
   each run appear fresh.
4. Read the actual check results on the current source PR. Record its head SHA,
   tested revision, workflow/run URLs, job names, and conclusions. If CI tests a
   synthetic merge commit, verify that it contains the current PR head and
   intended base. A green registry or downstream run, even against the exact
   source commit, validates that consumer and does not replace source PR checks.
5. When artifacts are in scope, download and inspect the source workflow's
   outputs, matching revision, architecture, configuration, and checksums to
   the claimed results. A link to artifacts from another repository or an older
   revision must be labelled as such.
6. Follow the skill's repository merge-gate instructions: derive required
   build/test check names and app identities from these runs, keep CodeQL
   informational, preserve other protections, and verify the required checks
   actually gate this PR. Avoid trigger filters that leave a
   required check permanently absent. Do not claim enforcement from workflow
   contents alone or describe configured checks as observed pending-check
   blocking without that evidence.

Generate `MODULE.bazel.lock` in the source checkout with update mode; keep it
ignored and retain it as generated CI evidence, separately from checked-in input
declarations. Follow the [lockfile validation steps](source-builds-and-lockfiles.md#generate-bazel-resolution-state-in-ci)
to prove the declared configurations work without a preexisting lock and leave
tracked files unchanged. Update artifact collectors that previously required a
tracked lock or used error mode.

Report source build coverage, source PR CI, consumer/registry validation, and
merge-gate verification separately so a passing result in one cannot conceal a
gap in another. Preserve existing analysis coverage; record unsupported or
deferred configurations explicitly.

## Detect missing CI during babysitting

After each complete successful collection, inspect every open in-scope component
implementation PR that adds or changes Bazel support, even when there are no new
comments, commits, or check events. Compare its declared configuration matrix
with current source PR checks and required-check settings. Do not treat an empty
check list, an old successful revision, or a green registry PR as healthy source
CI. Documentation-only and unrelated PRs should retain their applicable checks
without acquiring a build matrix from this rule.

For a gap, inspect workflow presence and triggers, the current tested revision,
matrix jobs, skip conditions, Actions/approval state, and branch protection or
rulesets before choosing a fix. Reuse a previously recorded assessment for an
unchanged head, workflow, and gate state; do not repeatedly rerun healthy builds.
An API failure means the state is unknown, not that CI is absent.

Apply [the CodeQL policy](../SKILL.md#keep-codeql-informational): report its real
status and findings separately from required build/test results. A failed or
pending CodeQL run, or a failure in the all-checks rollup caused only by CodeQL,
does not establish a merge blocker. Verify the current required checks and
applicable rules instead of inferring requirements from check names or the
rollup. Do not re-add CodeQL requirements when reconciling CI. Missing or failing
analysis still warrants investigation within scope; record it as an analysis
gap, not a passed scan or an unmet merge requirement. If CodeQL is still required,
record the conflicting rule and follow existing repository-settings authority
to remove it or report that specific pending action.

Repair missing or incorrect source workflows and validate the affected
configurations within the existing authorization. If settings or an external
approval prevent completion, continue authorized work and surface the precise
remaining action through the existing blocker-reporting workflow. This reference
adds no repository-setting, merge, or auto-merge authority and no new approval
step. Honor the controlling task's current grants and service limits.

Record the PR/head, expected and observed jobs, run URLs, build-versus-import
boundary, gate evidence, changes made, and outstanding gaps in triage. Recheck
after head or configuration changes. Keep unresolved gaps visible, and use the
existing blocker identity and deduplication rules instead of posting the same
alert every cycle.

## Keep current assessments internally consistent

Build a fresh current record from the current observation. Do not shallow-copy
or deep-copy a previous assessment and update only selected keys. That can pair
a new `head` and pending `jobs` with an old `collection_head`, `current_checks`,
pass flag, summary or artifact claim. This rule also applies to unchanged heads:
their checks may have advanced since the previous observation.

Reuse stable classification and the applicable-job policy only after verifying
their source, workflow and gate inputs. Keep prior execution and artifact
evidence in a separate historical section or linked report with its original
head, tested checkout, run IDs and observation time. Reuse validated artifacts
only after matching their provenance to the current inputs; do not relabel an
older execution as current. If a focused live read observes a newer head than
the supplied collection, distinguish those two observations explicitly.

Before persisting or acting on an assessment, verify:

- Current checks and jobs belong to the reported head or a verified synthetic
  merge containing that head and its intended base. Required-check metadata is
  separate from whether a job ran successfully.
- Missing, pending, failed, canceled, skipped, neutral and unknown results stay
  distinct. An API failure is unknown, not an empty successful inventory.
- A completion flag is true only when the applicable expected set is nonempty
  and every expected job has current successful execution evidence. Exclude
  inapplicable jobs only with a recorded scope/trigger reason. A downstream job
  awaiting an upstream job remains incomplete even before GitHub creates it.
- Summary text, completion flags, job lists and artifact claims describe the
  same observation. Never inherit `all_declared_jobs_pass`, `source_ci_result`,
  current-check aliases or artifact pointers from an older report.

For example, suppose head H1 passed all jobs and produced an image artifact.
After a push, H2 has a successful build, pending native tests and no downstream
VS job yet. The new record must report H2 as incomplete:

```json
{
  "head": "H2",
  "expected_jobs": ["build", "native tests", "VS"],
  "pending_jobs": ["native tests"],
  "missing_expected_jobs": ["VS"],
  "all_declared_jobs_pass": false,
  "source_ci_result": "incomplete: native tests pending; VS not started",
  "historical_evidence": [{"head": "H1", "report": "previous-cycle/report.json"}]
}
```

H1's artifact is historical; H2 has no current image-artifact claim. The same
incomplete result is required when the head is unchanged but an applicable job
is pending, missing or canceled. A later successful observation may replace the
current assessment, while retaining the earlier observation as evidence.
