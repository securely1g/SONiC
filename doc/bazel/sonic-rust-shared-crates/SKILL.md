---
name: sonic-rust-shared-crates
description: Design or review how a SONiC Rust workspace selects shared Bazel crate targets from its Cargo.lock when syncing upstream dependencies.
---

# Select shared Rust crates from a consumer's Cargo.lock

**Status — proposal for review.** Use this skill when a component already consumes
`@sonic_rust_deps` and an upstream version update forces someone to edit its BUILD
labels. The resolver and consumer alias below are proposed interfaces.

## Start with the consuming crate

In DASH HA, `swbus-config` inherits the workspace requirement `thiserror = "2"`.
Its own entry in `Cargo.lock` selects `thiserror 2.0.21`. The same lock also
contains `1.0.65` for other dependencies. The pinned shared module exports
`:thiserror` for `1.0.69` and `:thiserror2` for `2.0.21`. Looking up the name
alone would select the wrong library for this member.
[Member manifest](https://github.com/securely1g/sonic-dash-ha/blob/ad699b4d52c39ffd44a2fa76e3d814af9b8d57c5/crates/swbus-config/Cargo.toml#L15) ·
[Workspace requirement](https://github.com/securely1g/sonic-dash-ha/blob/ad699b4d52c39ffd44a2fa76e3d814af9b8d57c5/Cargo.toml#L49) ·
[Member's locked dependency](https://github.com/securely1g/sonic-dash-ha/blob/ad699b4d52c39ffd44a2fa76e3d814af9b8d57c5/Cargo.lock#L2196) ·
[Shared exports](https://github.com/securely1g/sonic-build-infra/blob/4064a814e8530300a7acbad4a9aff0621e2fb98e/rust/deps/BUILD.bazel#L124-L125)

| | What the DASH HA maintainer does on a sync |
| --- | --- |
| Today | Updates the Cargo inputs from upstream and edits BUILD dependencies. PR #7 changed seven label uses in six files, including `:thiserror` to `:thiserror2` for `swbus-config`. [Actual changes](https://github.com/securely1g/sonic-dash-ha/commit/ad699b4d52c39ffd44a2fa76e3d814af9b8d57c5) |
| With the proposal | Adopts a stable member label once, for example `@dash_ha_crates//swbus-config:thiserror`. Bazel reads the Cargo inputs and forwards this label to `@sonic_rust_deps//:thiserror2`. A later version-only sync can keep the same BUILD file whenever the shared module exports the newly locked crate. |

## Review the proposed design

1. **Shared owner.** Put the resolver and the mapping from exact package identity
   to public target with `sonic-build-infra/rust/deps`. Reuse the public exports of
   the pinned `sonic-rust-deps` module. Forwarding aliases keep one set of shared
   crate targets, which matters when a public Rust type crosses SONiC repositories.
2. **Consumer inputs.** Register the resolver once in the consumer's `MODULE.bazel`.
   Declare the workspace and relevant member manifests and the tracked `Cargo.lock`
   as inputs to Bazel repository resolution. Follow each member's direct dependency,
   including its Cargo rename, to the resolved package name, version and source.
   Check integrity where recorded. Preserve the selected features, target conditions,
   and normal, dev, build and proc-macro roles when wiring the result. SONiC
   workspace or Git libraries continue to use their owner's public targets.
3. **Missing export.** Report the requesting member, dependency and exact locked
   identity. For example, a member requesting `thiserror 1.0.65` cannot use the
   shared `1.0.69` export. Add the missing version with the shared owner, publish
   the updated module and update the consumer pin. If the version exists but its
   features are incompatible, select a compatible shared target or report which
   feature requirements the available target cannot satisfy.

Bazel can remain the CI build and test entry point. Keep the Cargo manifests and
lock for upstream syncs, dependency updates and the existing native build. The
pinned `rules_rs` already uses Cargo for workspace metadata. Its `from_cargo`
support also works for independent graphs, as the gNMI and BMP watchdogs show.
The extra requirement here is to select a target from an existing shared graph.
[DASH HA Debian build](https://github.com/securely1g/sonic-dash-ha/blob/ad699b4d52c39ffd44a2fa76e3d814af9b8d57c5/debian/rules#L10) ·
[rules_rs metadata call](https://github.com/hermeticbuild/rules_rs/blob/v0.1.0/rs/extensions.bzl#L155-L163) ·
[Watchdog imports](https://github.com/securely1g/sonic-buildimage/blob/8bee1d6ef2845486d138938f271e962682b21aac/MODULE.bazel#L14-L29)

## Evidence for a future implementation

- Exercise the seven affected uses in DASH HA #7, including `syn` in
  `sonicdb-derive` and `serde_serializer_quick_unsupported` in `swss-serde`.
  Compare each member's locked dependency with the shared target in a configured
  Bazel query, then build and test the affected consumers on their supported platforms.
- Use two valid manifest/lock revisions that select different available versions
  of one dependency. Keep the BUILD file and alias identical and show the selected
  shared target changes. Include two members selecting different versions at once.
- Exercise a missing exact export. Check that resolution identifies the member
  and requested package before compilation and leaves the tracked lock intact.
- Cover a renamed dependency and a target-specific feature requirement. Check
  that the member can import the Cargo name and that an incompatible shared
  feature selection produces a diagnostic.
