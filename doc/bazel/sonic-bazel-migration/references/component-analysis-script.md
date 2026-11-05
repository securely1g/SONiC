# Original build evidence collector

Read the [shared contract](common-contract.md), then applicable sections here. Run from repository root:

```bash
python3 "${SKILL_DIR}/scripts/analyze-make-component.py" SWSS \
  --repo . --rule rules/swss.mk --source-dir src/sonic-swss
```

Without --output-dir, this writes analysis.json, analysis.md and evidence/ under `/tmp/sonic-bazel-migration/SWSS/components/SWSS/`. To select a task directory, pass `--output-dir /path/to/migration-records/<root-component>` explicitly. Component directories percent-encode identifiers while preserving dots and original task_id.

Provide explicit rules or source directories to avoid guessing similarly named sources. --rule/--source-dir/--build-dir repeat. Rule/source paths are relative to --repo; explicit compilation database/log/artifact/task paths are relative to the caller directory. --build-dir records inputs without executing commands.

Optional evidence:

```bash
python3 "${SKILL_DIR}/scripts/analyze-make-component.py" SWSS \
  --repo . --rule rules/swss.mk --source-dir src/sonic-swss \
  --tasks /path/to/migration-records/SWSS/tasks.json \
  --compile-db /path/to/compile_commands.json \
  --log /path/to/build.log --artifact /path/to/swss.deb \
  --configuration CONFIGURED_ARCH=amd64 --configuration BLDENV=trixie \
  --provenance 'commit=<source-commit>; run=<existing-run-id>'
```

Existing outputs are protected by default. After review, --overwrite replaces this analysis, not task progress. Tasks may be a top-level array or tasks object; select exact id. Retained task products/dependencies/conditions do not replace production-rule review.

## Automation scope

- Record Git identity/tracked changes/declaration/source paths; file manifests retain untracked sources.
- Collect original declarations/logical lines/Make condition contexts from explicit rules/source directories.
- Extract candidate parameters/acquisition/patch/generator/tool/dependency declarations, retaining original text for interpretation.
- Read Debian control/changelog, patch series and disk manifests.
- Preserve original compile database entries/configuration/provenance and candidate logged commands.
- Inspect existing DEB with dpkg-deb, ZIP/wheel and TAR contents/metadata without disk extraction.

The collector runs no Make, source commands, builds, downloads or installation. Git/dpkg-deb use fixed read-only arguments. It skips symlink declaration/source files and resolves explicit directories. Static conditions remain text; no Make evaluation or automatic include/sub-build traversal.

Manually establish build directories, complete install mappings, generation relations, host tool identities/roles and all branches. Original DEB names/formats do not mandate current output; native runtime TARs, Python wheels installed through shared wheel_layer, and explicit final-DEB scope follow the delivery contract. Disk files are not necessarily compiled; compile databases do not prove execution. Logs may be echoes/dry-runs. One configuration/version does not prove others; independently check measured package/source correspondence. Initial status is analyzing, requiring continued rule interpretation before conclusions.

ZIP/wheel records paths/sizes/modes; TAR adds owners/links; DEB retains raw listings. Licenses/scripts/response files/environment/linking/exact tool identity remain unconfirmed without evidence. Follow [analysis](analyze-make-component.md) through patched selection/parameters/generation/packaging before completing analysis. Store evaluation rules in groups and actual execution separately in execution_validation. Complete [environment/artifact identities](review-port.md#environment-records) manually; Git/options collection is not runtime evidence. Investigate unhandled rules and concrete blockers.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s "${SKILL_DIR}/tests" -p 'test_analyze_make_component.py' -v
```

Existing tests cover read-only boundaries, preserved conditions/evidence, configuration/version separation and output protection. Independent handwritten components/wheels verify package lists, both condition branches, nonexecution and contents.
