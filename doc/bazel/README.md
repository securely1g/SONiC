# Bazel migration

- [Migration HLD](bazel_migration_hld.md)
- [Incremental SWSS and VS build HLD](bazel_incremental_swss_vs_hld.md)
- [SONiC Bazel migration skill](sonic-bazel-migration/SKILL.md)

## Migration skill

`doc/bazel/sonic-bazel-migration` is the canonical source for the
`sonic-bazel-migration` skill, its references and its dashboard helper.
Keep future skill updates here alongside the Bazel design documents.

For a new Codex installation, run:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo securely1g/SONiC --ref master \
  --path doc/bazel/sonic-bazel-migration --method git
```

The skill is available on the next turn as `$sonic-bazel-migration`.
The installer refuses to overwrite an existing installation; preserve any local
edits before replacing one. Existing installed copies continue to work.

The skill was imported unchanged from
[agi-projects at `0d1b59a`](https://github.com/securely1g/agi-projects/tree/0d1b59a71539bcf43f68ac79c34f5b2afaf84a18/skills/sonic-bazel-migration).
Its [earlier history](https://github.com/securely1g/agi-projects/commits/0d1b59a71539bcf43f68ac79c34f5b2afaf84a18/skills/sonic-bazel-migration)
remains there. The old repository retains a compatibility snapshot for its
existing babysitter package; the babysitter stays in `agi-projects`.
