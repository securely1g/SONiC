# Download locations and GitHub mirrors

Use the existing approved private mirror for Debian package inputs. Use GitHub
for other mirrored package archives, sources and build tools. GitHub is already
a dependency of this project's source and CI, so this choice avoids adding
another independently operated download service. Integrity and availability
are separate: a matching hash does not make a new host approved, and GitHub can
still be unavailable.

## Apply the approval boundary

- Before adding or using a location outside GitHub and the existing approved
  private mirror, obtain explicit user approval for that location and purpose.
  Include new source URLs, backup mirrors, acquisition used to populate a mirror,
  redirects and fallback behavior. A retry or checksum does not waive approval.
- Keep existing explicit approvals within their scope. Do not reinterpret an
  upstream URL, a package manifest or a reachable endpoint as user approval.
  Verified local cached bytes can be reused without contacting their former host;
  that reuse does not authorize a new network request to it.
- Verify HTTPS destinations and every redirect hop. GitHub's verified asset
  delivery endpoints are part of GitHub transport; do not use an unrestricted
  wildcard, open redirect or arbitrary storage-service URL to broaden that scope.
- Preserve the approved private mirror's authentication and privacy boundary.
  Public manifests, logs and GitHub assets must not include its addresses,
  credentials or private payloads.
- Apply the policy to the downloads being introduced or changed. Record any
  remaining inherited paths separately; do not silently rewrite unrelated
  dependencies or published registry entries. Existing registry catalog choices
  are governed by the registry URL policy and do not authorize new payload hosts.

## Reuse one GitHub mechanism

Prefer existing upstream GitHub release assets that contain the required bytes.
Use a direct asset or select the needed members from its ZIP; do not create a new
repository or republish inputs merely because the reader is generic. Keep
package-specific data in a reviewed manifest, not a new downloader. Record the
package/version, consumed filenames, expected byte sizes and SHA256 values,
original provenance, GitHub asset identity and any selected archive member paths.
Do not rebuild, repack or substitute a newer input to change its download host.

Normal builds need read access only. A shared reader verifies cached files,
downloads missing files from the declared GitHub location through a strict
redirect allowlist, and checks each selected input's size and hash. Preflight the
complete requested set before exposing it through Bazel's supported download/cache
interface. Preserve the expected filenames, archive layout and module versions.
Use the same manifest and reader in local builds and CI. Never execute a fetched
input during verification or turn a failed download into an unapproved fallback.

Only when no suitable GitHub copy exists, consider a separate publication path.
Accept verified local files or acquire them from an explicitly authorized origin;
preserve applicable licenses and notices, verify the complete set, publish
versioned GitHub assets, and read them back to check the bytes. Keep published
identities immutable; mismatched existing assets are errors, not replacements.
Consumer SHA256 checks remain required. This conditional publisher is separate
from ordinary consumption and is not needed for the Cosmos example below.

Treat `--distdir` as a transport interface, not proof that all network access is
disabled: Bazel may try declared URLs when an entry is absent or fails integrity.
Validate the complete affected input set before invoking the consumer. If another
path can bypass that set or fall back to an unapproved host, constrain that path
or report the remaining gap; do not claim the reader enforces global no-egress.
Preserve unrelated approved network paths rather than imposing a new global ban.

## Cosmos example from registry #238

[Registry #238](https://github.com/securely1g/sonic-bazel-registry/pull/238) addressed
AMD64 `libteam@1.31.0.sonic.1` preparation failures fetching Cosmos 4.0.2 tools.
Its three inputs are `assimilate`, `ape-x86_64.elf` and `gzip.ape`. The proposal
already supplied their original bytes through `--distdir`, extracting them from
the official [Cosmos 4.0.2 GitHub ZIP](https://github.com/jart/cosmopolitan/releases/download/4.0.2/cosmos-4.0.2.zip)
and checking the individual pinned sizes and SHA256 values. The ZIP had no
upstream whole-file digest, so the member checks were its integrity boundary.
That GitHub location is already suitable; the remaining issue is the
package-specific downloader and workflow setup.

The generic replacement keeps the same GitHub ZIP, three member identities and
consumer filenames, and puts their data in the common manifest. It needs no new
repository or Cosmos asset publication. Adding another package with direct
GitHub assets or selected ZIP members should require manifest data, not another
package-specific fetcher or workflow branch. If no suitable approved source or
verified local bytes exist for a different package, report that input and obtain
approval before contacting another host.

Verify good-cache reuse, missing and corrupt inputs, interrupted downloads,
filename collisions and redirects; test repeated publication and mismatched
existing assets if a publisher is separately implemented. Confirm the real
libteam consumer receives the expected files and that
the inner registry runner retains its mirror/privacy settings. Distinguish these
transport checks from native libteam runtime/debug/SDK TAR validation: the former
do not establish a successful package or image build.
