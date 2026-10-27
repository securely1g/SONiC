---
name: azure-bazel-cache
description: Use, inspect, or maintain the existing bazel-remote cache in Azure subscription 1. Apply to PR read access, authenticated uploads, cache status, or changes to this specific deployment; use general Bazel guidance for unrelated caches.
---

# Azure Bazel cache

This skill describes the existing deployment and does not grant permission for a new deployment, resource deletion, credential change, or message to another person.

Start with the maintained [deployment notes](README.md) when the request needs details beyond client access. Treat the recorded configuration and verification reports as a baseline, not a live status check. Inspect Azure and the guest when current state matters.

For uploads or maintenance, set the absolute path to the existing deployment workspace on your host:

```sh
export BAZEL_REMOTE_DEPLOY_DIR="/absolute/path/to/bazel-remote-deployment"
```

Replace the placeholder with the workspace containing `scripts/`, `infra/`, `verification/`, and the existing private `secrets/`. Those files are not included in this documentation directory; do not use this directory as the deployment workspace. Documentation links resolve relative to this skill.

## Client access

The endpoint is `https://lgh-bazel-87263989.eastus.cloudapp.azure.com`.

For PRs or other clients that should only read, use [pr-readonly.bazelrc](generated/pr-readonly.bazelrc):

```text
build --remote_cache=https://lgh-bazel-87263989.eastus.cloudapp.azure.com
build --remote_upload_local_results=false
```

This configuration contains no credentials. The upload flag controls client behavior; the service independently rejects anonymous writes.

For authorized writers, run from the source repository you want to build and use the existing private configuration as a Bazel startup option:

```sh
bazel --bazelrc="${BAZEL_REMOTE_DEPLOY_DIR:?Set BAZEL_REMOTE_DEPLOY_DIR}/secrets/client.bazelrc" build //...
```

Do not copy the password, Basic authorization value, or password hash into source control, logs, reports, or this skill. Preserve the existing writer credentials unless the user requests a change. When adding CI access, distinguish credential-free PR reads from trusted uploads and use the repository's established secret mechanism for the latter.

## Deployment baseline

The last verified deployment uses:

- Azure subscription `87263989-4394-4cd2-904c-1ec2aec4bc4f`, resource group `rg-bazel-remote-eastus`, VM `vm-bazel-remote-eastus` in East US.
- `Standard_D2as_v4` with 2 vCPUs and 8 GiB RAM, a 64 GiB OS disk, and a 1024 GiB Standard SSD cache disk.
- A dedicated ext4 cache mount at `/var/lib/bazel-remote`, with entries in `/var/lib/bazel-remote/cache`; `max_size` is 920 GiB and `max_size_hard_limit` is 968 GiB.
- bazel-remote v2.6.4 with zstd storage and no proxy backend. The former Blob account was deleted. Explicit per-entry size limits remain omitted.
- Caddy for public HTTPS, forwarding to bazel-remote HTTP at `127.0.0.1:8080`. gRPC listens only at `127.0.0.1:9092`.
- Native `htpasswd_file` authentication with `allow_unauthenticated_reads: true`.

The current rendered application settings are in [bazel-remote.yaml](generated/bazel-remote.yaml). For resource changes, inspect `infra/main.bicep`, `infra/resources.bicep`, and the live resource before editing. Use the explicit subscription ID in Azure CLI commands rather than relying on the active CLI subscription.

## Authentication behavior

On the public HTTP cache path, anonymous GET and HEAD requests are allowed; PUT requires the existing writer credentials. Native anonymous-read mode also leaves `/status` and `/metrics` accessible without login. Reads with an incorrect Authorization header still bypass authentication. The loopback gRPC listener uses the native read-RPC allowlist and requires credentials for writes; HTTP method filtering does not describe gRPC authorization.

The existing cost-14 bcrypt hash is checked on each PUT using a known username. A prior loopback test measured 1.044 seconds median for a rejected PUT using the known username and an incorrect password; valid credentials use the same bcrypt comparison. Treat this as a recorded authentication cost, not a current throughput benchmark. Do not silently change the hash, authentication layer, or access semantics to optimize it. See [application details](app/README.md) and the [timing report](reports/anonymous-reads-auth-timing-local.json).

## Inspect or change the deployment

For status requests, read the public `/status` endpoint and use the relevant Azure or guest checks if the question needs more than application status. `MaxSize`, `CurrSize`, `ReservedSize`, and `UncompressedSize` are bytes; `MaxSize` is the configured cache eviction limit, not raw disk capacity.

For an authorized change, update the maintained sources and rendered configuration together. Preserve unrelated storage, listeners, credentials, and cache acceptance behavior. Set `BAZEL_REMOTE_CADDY` to the absolute path of an executable Caddy **2.11.7** binary for your host's OS and architecture, then regenerate from the deployment workspace:

```sh
export BAZEL_REMOTE_CADDY="/absolute/path/to/caddy"
(
  cd "${BAZEL_REMOTE_DEPLOY_DIR:?Set BAZEL_REMOTE_DEPLOY_DIR}" || exit
  python3 scripts/render_deployment.py \
    --caddy "${BAZEL_REMOTE_CADDY:?Set BAZEL_REMOTE_CADDY}" &&
  az bicep build --file infra/main.bicep --outfile generated/main.json
)
```

Choose deployment steps from the requested change and current state. The historical migration scripts and reports document completed operations; do not replay them as a general deployment command. If an external operation times out, inspect that operation or authoritative state before retrying.

## Verify relevant behavior

Use the existing verifiers when the change affects access or cache behavior:

```sh
(
  cd "${BAZEL_REMOTE_DEPLOY_DIR:?Set BAZEL_REMOTE_DEPLOY_DIR}" || exit
  python3 verification/verify_public_endpoint.py \
    --anonymous-reads \
    --output reports/public-validation.json &&
  python3 verification/verify_remote_cache.py --anonymous-read
)
```

The public verifier writes one unique 1 MiB cache entry using the existing credentials, then checks anonymous GET/HEAD and rejected anonymous or incorrect-password PUTs. The Bazel verifier uploads a unique action with the writer configuration, removes the full client output base, and requires a credential-free remote cache hit with matching output. Both retain sanitized evidence. Run them for a deployment change or requested live verification, rather than for a documentation-only question.

If the execution environment restricts Bazel's process metadata access, use its supported command escalation path; do not change global Bazel configuration or environment directories to work around it. The guest validation script contains hashes for the expected deployment, so update those expectations when the corresponding files legitimately change.

The last consolidated access verification is [anonymous-reads-completion-audit.json](reports/anonymous-reads-completion-audit.json). Report which checks actually ran and distinguish recorded behavior from current observations.
