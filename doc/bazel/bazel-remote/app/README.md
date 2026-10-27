This document describes the bazel-remote application for the Azure deployment. The pinned executable is **v2.6.4**, source commit `7586516bfab045373eeece55048e441976fc8a27`, from the [official release](https://github.com/buchgr/bazel-remote/releases/tag/v2.6.4). The Linux amd64 binary is 24,318,062 bytes with SHA-256 `6a6b64666c2238ec6b49b7b29f5e41e4149de09417a0028897c9bffe40376876`. The downloaded bytes match the digest in [GitHub release metadata](https://api.github.com/repos/buchgr/bazel-remote/releases/418877486).

The files below live under `app/` in the existing external deployment workspace. They are not included in this documentation directory. Follow the [deployment workspace setup](../README.md#deployment-workspace) and set its absolute root path:

```sh
export BAZEL_REMOTE_DEPLOY_DIR="/absolute/path/to/bazel-remote-deployment"
```

Replace the placeholder with your deployment workspace, not this documentation checkout.

| File | Purpose |
|---|---|
| `artifacts/bazel-remote-2.6.4-linux-amd64` | Pinned official executable copied to the VM. |
| `artifacts/SHA256SUMS` | Digest for verifying the executable. |
| `release-pin.json` | Machine-readable release provenance and content pin. |
| `render-config.py` | Renders the current 920/968 GiB disk-only configuration, loopback listeners, and native write authentication. |

Verify the staged executable in the deployment workspace:

```sh
(
  cd "${BAZEL_REMOTE_DEPLOY_DIR:?Set BAZEL_REMOTE_DEPLOY_DIR}/app/artifacts" || exit
  sha256sum -c SHA256SUMS
)
```

The deployment owns Caddy, public HTTPS, client authentication, and service installation.

## Current configuration

```yaml
dir: "/var/lib/bazel-remote/cache"
max_size: 920
max_size_hard_limit: 968
storage_mode: zstd
zstd_implementation: go
http_address: "127.0.0.1:8080"
grpc_address: "127.0.0.1:9092"
enable_endpoint_metrics: true
access_log_level: all
htpasswd_file: "/etc/bazel-remote/htpasswd"
allow_unauthenticated_reads: true
```

The deployment invokes `render-config.py` with `--disk-only`, so the rendered configuration has no proxy backend or uploader settings. Caddy handles TLS, while bazel-remote uses the existing account through its htpasswd authentication. `max_blob_size` and `max_proxy_blob_size` are omitted, preserving the prior effective per-entry settings. [Configuration fields and defaults](https://github.com/buchgr/bazel-remote/blob/v2.6.4/config/config.go#L85-L128)

Run the renderer from the deployment workspace's `app/` directory:

```sh
(
  cd "${BAZEL_REMOTE_DEPLOY_DIR:?Set BAZEL_REMOTE_DEPLOY_DIR}/app" || exit
  python3 render-config.py \
    --output ../generated/bazel-remote.yaml \
    --cache-dir /var/lib/bazel-remote/cache \
    --max-size-gib 920 \
    --max-size-hard-limit-gib 968 \
    --disk-only \
    --htpasswd-file /etc/bazel-remote/htpasswd \
    --allow-unauthenticated-reads
)
```

When `--config_file` is used, bazel-remote ignores its other application flags and `BAZEL_REMOTE_*` environment settings. The current systemd unit starts the binary with `/etc/bazel-remote/config.yaml` and has no managed-identity environment file.

## Authentication

The native `allow_unauthenticated_reads` setting permits HTTP cache GET and HEAD requests without credentials and requires valid Basic credentials for PUT. It also leaves `/status` and enabled `/metrics` unauthenticated. The htpasswd file is owned by root, readable by the `bazel-remote` group, and mode 0640. The existing username, password, and bcrypt hash are reused. [HTTP authentication and route setup](https://github.com/buchgr/bazel-remote/blob/v2.6.4/main.go#L255-L339), [anonymous-read wrapper](https://github.com/buchgr/bazel-remote/blob/v2.6.4/main.go#L483-L502)

The loopback gRPC listener uses the same htpasswd provider: its allowlisted read RPCs remain anonymous and writes require credentials. Public clients continue using the HTTP cache protocol through Caddy. [gRPC read methods](https://github.com/buchgr/bazel-remote/blob/v2.6.4/server/grpc.go#L37-L55)

Native htpasswd authentication performs bcrypt verification on each PUT using a known username. With the existing cost-14 hash, three loopback rejected-PUT checks measured a median of 1.044 seconds, compared with 0.001 seconds for anonymous GET. The measurement is recorded in the [timing report](../reports/anonymous-reads-auth-timing-local.json). [Credential verification](https://github.com/abbot/go-http-auth/blob/e1cee1c72f2f/basic.go#L63-L95)

## Local capacity and eviction

`max_size` is measured in GiB; the executable multiplies the value by 1,073,741,824. The current value of 920 is 987,842,478,080 bytes. The LRU accounts for stored file lengths rounded up to 4 KiB and reservations for incoming entries. With zstd storage, committed CAS entries count their compressed stored size; incoming reservations use logical size. The status endpoint reports `MaxSize`, `CurrSize`, `ReservedSize`, and `UncompressedSize` in bytes. [GiB conversion](https://github.com/buchgr/bazel-remote/blob/v2.6.4/main.go#L147-L162), [LRU accounting](https://github.com/buchgr/bazel-remote/blob/v2.6.4/cache/disk/lru.go#L173-L231), [reservation rules](https://github.com/buchgr/bazel-remote/blob/v2.6.4/cache/disk/lru.go#L296-L372)

The 1024 GiB disk has 1,081,108,647,936 usable filesystem bytes, about 1006.9 GiB. The 968 GiB hard limit leaves room for filesystem overhead and delayed file removal. It rejects new reservations when current bytes, queued eviction bytes, and the new reservation would cross the guard. These settings are application limits, not filesystem quotas; physical usage can temporarily exceed `max_size` while evicted files are unlinked asynchronously. [Hard-limit accounting](https://github.com/buchgr/bazel-remote/blob/v2.6.4/cache/disk/lru.go#L71-L87), [asynchronous unlink](https://github.com/buchgr/bazel-remote/blob/v2.6.4/cache/disk/lru.go#L427-L467)

When capacity is needed, bazel-remote evicts least-recently-used local entries. The deployment has no remote storage copy. A later request for an evicted entry is a cache miss, and the client can rebuild and upload it again.

## Verification

Use the [portable verification commands](../SKILL.md#verify-relevant-behavior) for the external deployment workspace. The public verifier checks trusted HTTPS, anonymous reads, rejected anonymous writes, the existing writer credentials, and a unique 1 MiB CAS upload/download. The Bazel verifier checks that a new action uploads with the existing credentials and then returns a credential-free remote cache hit after the client's full local output base is removed. Recorded results are linked from the [deployment notes](../README.md#verification).
