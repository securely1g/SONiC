# Classify Project Area by Docker consumers

The SONiC Bazel Migration Project's **Area** column identifies which Docker
migrations need a PR. Use a native **multi-select** field with one option per
canonical Docker name, plus any explicitly tracked image areas. This replaces
the old work-type categories such as
`Build infrastructure`, `Dependency registry` and `Documentation`.

## Select every verified Docker consumer

- Use actual image-family names from the selected sonic-buildimage inventory,
  such as `docker-teamd`, `docker-lldp` and `docker-dhcp-relay`. An image PR
  selects its own Docker; a prerequisite PR selects every Docker that needs it.
- Include source packages, shared libraries, generators, parent images,
  registry entries, build rules, CI and guidance when their changes are
  required by those Docker migrations. Follow verified dependency chains
  through intermediate producers and registry PRs to the Docker consumers.
- For example, a prerequisite needed by both teamd and LLDP gets two separate
  selections: `docker-teamd` and `docker-lldp`. Never create a combined
  `docker-teamd, docker-lldp` option, choose only a primary consumer, or use
  a generic `Shared`/`All Dockers` tag instead of the individual names.
- Establish each assignment from the selected build graph, source ownership,
  PR changes and consumer links. Do not infer all Dockers from the repository
  name or from a generic shared-library relationship. Record supporting
  consumers/targets in triage. Assign each Docker or image area from its
  verified impact. Leave Area unset when no affected area is established;
  retain uncertain classifications for investigation rather than inventing
  an association.

Area is the set of affected Docker consumers, including transitive consumers.
**All upstream PRs** still records only direct prerequisite PRs. Do not reverse
or expand those dependency cells to implement Area classification.

## Track base image impact alongside Docker impact

For `securely1g` Project 1, **`base image`** identifies changes to SONiC's host
OS, kernel, root filesystem, installer and image assembly. It is independent
of the 31 tracked Dockers, including the separately named shared Docker bases.
A PR may select `base image` together with every Docker it affects.

- Establish base-image impact from the changed source, build rules and actual
  image consumers. This includes verified prerequisites of host/rootfs and
  installer producers. Name the relevant target, package or image-build step
  in the evidence and bind it to the reviewed PR revision.
- Preserve all verified Docker tags when adding `base image`, and preserve
  `base image` when a PR also gains Docker consumers. A shared dependency can
  serve both kinds of output.
- Do not infer base-image impact from an empty Docker selection, an unrelated
  documentation or dashboard change, or a missing classification. Container
  inclusion in the final installer alone does not establish a change to its
  host/rootfs or image-assembly producer.
- In babysitter evidence, keep the `base image` definition in
  `additional_areas`, separate from the actual `dockers` catalog. Record
  verified per-PR `areas` alongside `dockers`. No fake Docker path is needed.
- Propagate additional areas only through explicitly reviewed dependency-edge
  `areas` scopes, with both endpoint heads verified. A broad image-integration
  PR must not assign `base image` to every prerequisite automatically.
- Preserve valid manual and historical selections. Use `remove_areas` only
  when current evidence disproves an additional-area association, just as
  explicit Docker removals require evidence. An incomplete read or changed
  head alone does not authorize clearing saved selections.
- Count all native field choices toward GitHub's option limit, while retaining
  the actual Docker count separately. The current Project has 31 Docker
  choices plus the independent `base image` choice.

For example, [buildimage #64](https://github.com/securely1g/sonic-buildimage/pull/64)
changes `tools/bazel/ci/build_vs.sh` to build `target/sonic-vs.bin` and integrates
the container variants. Its reviewed image-build impact can receive
`base image` while retaining its affected Docker tags. Dashboard-only
[buildimage #87](https://github.com/securely1g/sonic-buildimage/pull/87) does not
receive `base image` merely because its Docker list is empty.

## Keep the full dropdown catalog available

Build the options from the complete Docker inventory **within the agreed
migration scope**, recording the image/profile and source revision. For a VS
runtime-container migration, enumerate the runtime Docker families selected
or explicitly planned for that profile, even without a current PR. Do not use
every Dockerfile in the repository as the dropdown: that also counts unrelated
vendor variants, legacy distributions, builder/test images and intermediate
bases. Record optional planned runtime families separately from those actually
included in the current image.

Classify base-layer, build-tool and shared-library PRs by their verified runtime
Docker consumers. Give a base or tooling image its own Area option only when
the agreed scope tracks it as a separate Docker deliverable. Reconcile additions
as that scope and its maintained baseline change; do not hard-code the initial
count or derive the catalog solely from open PRs. GitHub currently limits one
multi-select field to 100 options. If the agreed catalog exceeds that limit,
report it and resolve the layout with the user; do not silently drop images or
combine distinct families.

Reuse canonical names and existing option IDs. Treat runtime/debug variants
as one family unless they have distinct canonical image identities. Resolve
duplicate basenames with stable platform/path qualifiers and record the mapping
so distinct vendor images are not merged accidentally. Keep catalog ordering
stable and add missing verified Docker options. Preserve options referenced by
historical rows until an explicit retirement/mapping decision is recorded.

## Migrate and verify the field

GitHub supports [native multi-select Project fields](https://github.blog/changelog/2026-08-07-connecting-issues-and-multi-select-field-support/).
Discover the current field type and supported API before writing. A legacy
single-select Area field cannot hold multiple Docker selections. Do not write
comma-separated text or repeatedly replace its selected option and claim that
all tags were saved.

During authorized dashboard migration, save existing field definitions, item
values and view settings first. Use a supported in-place conversion if available.
Otherwise prepare a multi-select replacement, retain the original field and
values under an unambiguous legacy name, and put the new Area column in the
same visible position. Preserve unrelated columns, filters, grouping and manual
dependency ordering; translate any old Area-based filter/grouping explicitly.
Do not delete historical data or translate old work categories into guessed
Docker names. Record old/new field identities and coordinate active writers
before switching so an older babysitter cannot restore the previous schema.

Use the supported Projects API's complete option-ID set for each item. Check
current CLI/API support; a single-select CLI flag is insufficient. Read back the
saved field type, catalog, exact selected IDs/names and affected view settings.
Confirm a shared PR retains every intended tag and that other Docker options
remain selectable. Report unsupported operations or limits rather than
silently dropping tags or narrowing the catalog.

## Reconcile during babysitting

At enrollment and each authorized reconciliation cycle, reread the current
policy, Docker catalog and consumer evidence. Add newly verified consumers and
remove stale assignments only when evidence establishes that the dependency
changed. A consumer merging or closing alone does not erase its historical
association. Preserve valid manual selections and unrelated metadata; retain
uncertain selections for investigation instead of clearing them after a failed
or incomplete read. Verify the complete saved set after changes.

A skill-only edit changes this policy; it does not by itself migrate the live
Project schema or deploy a refreshed babysitter installation. Report those
outcomes separately.
