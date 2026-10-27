# Azure bazel-remote deployment

The service is deployed in **Azure subscription 1** (`87263989-4394-4cd2-904c-1ec2aec4bc4f`) and uses a dedicated **1 TiB Standard SSD local cache**. It runs on `Standard_D2as_v4` in East US at **https://lgh-bazel-87263989.eastus.cloudapp.azure.com** with public IPv4 **172.171.78.197**.

The October 26, 2026 storage migration expanded the existing cache disk and preserved its filesystem UUID and local cache files. After disk-only verification passed, the dedicated Blob account `stlghbazeleus87263989` and its container-scoped VM role assignment were deleted. The service passed another cache write/read after deletion.

The service now enables bazel-remote's native `allow_unauthenticated_reads` setting. PRs can read cache entries without credentials, while writes use the existing username and password through bazel-remote's htpasswd authentication. Caddy continues to provide HTTPS and forwards requests to the loopback HTTP listener.

## Configuration

| Component | Configuration |
|---|---|
| Region | East US |
| VM | Standard_D2as_v4, 2 vCPUs, 8 GiB RAM |
| OS | Ubuntu 24.04 LTS, image version 24.04.202610210 |
| OS disk | 64 GiB Standard SSD LRS |
| Cache disk | 1024 GiB Standard SSD LRS, dedicated ext4 filesystem on LUN 0 |
| Cache limits | 920 GiB LRU limit and 968 GiB reservation guard |
| Storage backend | Local managed disk only; no Blob or other proxy backend |
| Public endpoint | Standard static IPv4 with `lgh-bazel-87263989.eastus.cloudapp.azure.com` |
| Client access | Public HTTPS; anonymous reads and native htpasswd authentication for writes using the existing credentials |
| Application | bazel-remote v2.6.4, pinned by SHA-256, with zstd storage |
| HTTPS frontend | Caddy v2.11.7, pinned by SHA-256 |

The cache is mounted at `/var/lib/bazel-remote`, with entries under `/var/lib/bazel-remote/cache`. The filesystem has 1,081,108,647,936 usable bytes (about 1006.9 GiB). `max_size` is 920 GiB and `max_size_hard_limit` is 968 GiB. No explicit `max_blob_size` or `max_proxy_blob_size` setting was added. LRU eviction removes older cache entries as the local cache fills.

## Estimated cost

The East US pay-as-you-go base is **$155.33/month** using 730 hours, verified against the Azure Retail Prices API on October 26, 2026.

| Component | Rate | Monthly base |
|---|---:|---:|
| [Linux D2as v4 VM](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName+eq+%27Virtual+Machines%27+and+armRegionName+eq+%27eastus%27+and+armSkuName+eq+%27Standard_D2as_v4%27+and+productName+eq+%27Virtual+Machines+Dasv4+Series%27+and+meterName+eq+%27D2as+v4%27+and+priceType+eq+%27Consumption%27) | $0.096/hour | $70.08 |
| [E30 1024 GiB cache SSD](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName+eq+%27Storage%27+and+armRegionName+eq+%27eastus%27+and+productName+eq+%27Standard+SSD+Managed+Disks%27+and+skuName+eq+%27E30+LRS%27+and+meterName+eq+%27E30+LRS+Disk%27+and+priceType+eq+%27Consumption%27) | $76.80/month | $76.80 |
| [E6 64 GiB OS SSD](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName+eq+%27Storage%27+and+armRegionName+eq+%27eastus%27+and+productName+eq+%27Standard+SSD+Managed+Disks%27+and+skuName+eq+%27E6+LRS%27+and+meterName+eq+%27E6+LRS+Disk%27+and+priceType+eq+%27Consumption%27) | $4.80/month | $4.80 |
| [Standard static public IPv4](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName+eq+%27Virtual+Network%27+and+armRegionName+eq+%27eastus%27+and+productName+eq+%27IP+Addresses%27+and+contains%28meterName%2C+%27Standard+IPv4%27%29+and+priceType+eq+%27Consumption%27) | $0.005/hour | $3.65 |

Disk operations, outbound data transfer, taxes, and unrelated subscription resources are excluded. There is no ongoing Blob storage charge for the deleted account.

## Connect

The service status page is **https://lgh-bazel-87263989.eastus.cloudapp.azure.com/status** and is readable without credentials. The native setting also makes `/metrics` readable without credentials.

For PRs that should read the cache without credentials, use the contents of `generated/pr-readonly.bazelrc`:

```text
build --remote_cache=https://lgh-bazel-87263989.eastus.cloudapp.azure.com
build --remote_upload_local_results=false
```

The second option prevents upload attempts from the PR client. The server separately rejects anonymous PUT requests.

For clients that should upload results, pass the existing private Bazel configuration as a startup option:

```sh
bazel --bazelrc=/Users/lgh/bazel-remote-azure-20261025/secrets/client.bazelrc build //...
```

The private files in `secrets/` and the rendered `generated/htpasswd` file are mode 0600. The plaintext password is absent from cloud-init and Azure deployment parameters; the existing bcrypt hash is included for native write authentication. Public ingress is configured for TCP 80 and 443.

Native htpasswd authentication verifies the existing cost-14 bcrypt hash on every PUT using a known username. Three loopback checks using the known username with an incorrect password measured a median of 1.044 seconds per rejected PUT; valid credentials use the same bcrypt comparison. This adds authentication work to uploads. The measurement is in `reports/anonymous-reads-auth-timing-local.json`. [Credential verification](https://github.com/abbot/go-http-auth/blob/e1cee1c72f2f/basic.go#L63-L95)

## Verification

- Azure reports the cache disk as 1024 GiB Standard SSD LRS, attached to the same running VM. The public IP and hostname are unchanged.
- The guest reports the same ext4 UUID, both services active and enabled, the pinned bazel-remote binary, and the exact disk-only configuration. The cache limit is 920 GiB with a 968 GiB reservation guard.
- Public HTTPS passed certificate trust and hostname verification. Anonymous cache GET and HEAD requests succeeded; anonymous and incorrect-password PUT requests returned 401. The existing credentials successfully uploaded a unique 1 MiB CAS entry, which downloaded anonymously byte-for-byte. HTTP redirects to HTTPS.
- `/status` and `/metrics` returned 200 without credentials, matching the native setting.
- Bazel 9.3.1 built and uploaded a unique cacheable action with the existing credentials, removed its entire local output base, and then used the credential-free PR configuration to record `runner: remote cache hit` and `cacheHit: true` with identical output.
- The Blob account and its role assignment are absent. Temporary rollback copies and obsolete Blob validation configurations were removed after verification; the active local cache was preserved.

Current authentication evidence is in `reports/anonymous-reads-guest-final.json`, `reports/anonymous-reads-public-validation.json`, `reports/anonymous-reads-finalize-result.json`, and `verification/runs/20261026T153353Z-c1aba178/result.json`. The consolidated audit is `reports/anonymous-reads-completion-audit.json`. Storage migration evidence remains in `reports/disk-only-completion-audit.json`.

## Deployment files

- `infra/main.bicep` and `infra/resources.bicep` define the VM, disks, and networking. They contain no storage account or Blob role assignment.
- `infra/bootstrap.py` prepares an empty cache disk for a fresh VM and checks capacity before starting the services.
- `infra/Caddyfile.template` and the systemd units define HTTPS forwarding and loopback application listeners. Native write authentication is configured in `generated/bazel-remote.yaml` and `generated/htpasswd`.
- `app/README.md` documents the application configuration and local eviction behavior.
- `generated/` contains the current ARM template, parameters, cloud-init, rendered service configuration, and credential-free PR Bazel configuration.
- `verification/verify_public_endpoint.py --anonymous-reads` checks HTTPS, anonymous reads, protected writes, and a unique CAS round trip; `verification/verify_remote_cache.py --anonymous-read` proves a credential-free Bazel cache hit.

Regenerate the current deployment files while preserving the existing credentials:

```sh
python3 scripts/render_deployment.py --caddy tools/caddy-2.11.7-macos-arm64
az bicep build --file infra/main.bicep --outfile generated/main.json
```

The renderer validates Caddy and checks that the plaintext client password is absent from cloud-init. The current generated cloud-init is below Azure's 64 KiB custom-data limit.

Historical reports from the original Blob-backed deployment remain under `reports/` as audit evidence; they are not consumed by the service or renderer. The VM's initial cloud-init history still records the earlier unsupported `bazel-remote --version` probe. The corrected bootstrap and this migration completed through Azure Run Command, and current runtime checks pass.
