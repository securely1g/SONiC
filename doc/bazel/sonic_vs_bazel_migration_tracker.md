# sonic-vs.bin Bazel Migration Tracker

## Overview

**Status snapshot:** 2026-10-29.
**Target:** `sonic-vs.bin`, AMD64, Debian Trixie, VS, Python 3, default features, runtime image.

A component is one source build: its main Make output and the derived or extra outputs identified by `_MAIN_DEB` are tracked in a single row. The component is named by its main output variable. The **Outputs** column lists all audited output identifiers belonging to it.

The tracker contains **127 components**, covering **167 outputs**, across **12 dependency layers**.

| Bazel status | DEB components | WHEEL components | Docker components | Installer components | Total components | Total outputs |
|---|---:|---:|---:|---:|---:|---:|
| Merged | 18 | 10 | 4 | 0 | 32 | 61 |
| PR | 4 | 0 | 1 | 1 | 6 | 11 |
| Not migrated | 41 | 22 | 26 | 0 | 89 | 95 |
| Total | **63** | **32** | **31** | **1** | **127** | **167** |

- **Merged:** the Bazel implementation is present in the maintained default branch or published registry. This status records implementation availability; build and runtime validation are separate evidence.
- **PR:** a Bazel implementation exists in an open pull request linked in the PR column.
- **Not migrated:** a Bazel artifact rule for the component is absent. Script exports alone do not count as a migrated wheel.

The PR column combines the source implementation, packaging, integration, and registry-publication PRs for all outputs of the component. Each link appears once per component. Repository-qualified labels distinguish PR numbers across repositories. Merged PRs are included; open follow-ups are marked `(open)`. A component can remain `Merged` while a follow-up PR is open. `—` means no corresponding Bazel PR is recorded.

Layers are calculated between components, after grouping co-produced outputs. The Dependencies column lists only components present in this document, with their layers shown as `L<n>`. Each dependency is in a lower layer. `—` denotes an empty in-list dependency set. Internal relationships between outputs of the same component do not add dependency layers.

For example, `LIBNL_CLI`, `LIBNL_CLI_DEV`, and the other libnl3 outputs belong to the `LIBNL3` component in layer 1. `LIBTEAM` depends on that component and is in layer 2.

The snapshot uses [buildimage master](https://github.com/securely1g/sonic-buildimage/tree/2dc503aaecfb0d3c317608aaeabc68a108e32b97) and the [maintained registry](https://github.com/securely1g/sonic-bazel-registry/tree/791f12022342f5439fb527ba03eca0225f8c772d/modules). Statuses describe the corresponding Bazel implementation and its actual interface, which may be an installation TAR rather than the original Make DEB.

## Layered Component List

### Layer 1 — 35 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `BASH` | `BASH` | DEB | Not migrated | — | — |
| `DOCKER_DASH_ENGINE` | `DOCKER_DASH_ENGINE` | DOCKER | Not migrated | — | — |
| `HSFLOWD` | `HSFLOWD` | DEB | Not migrated | — | — |
| `IFUPDOWN2` | `IFUPDOWN2` | DEB | Not migrated | — | — |
| `INITRAMFS_TOOLS` | `INITRAMFS_TOOLS` | DEB | Not migrated | — | — |
| `IPROUTE2` | `IPROUTE2` | DEB | Merged | [registry#64](https://github.com/securely1g/sonic-bazel-registry/pull/64); [registry#100](https://github.com/securely1g/sonic-bazel-registry/pull/100); [registry#134](https://github.com/securely1g/sonic-bazel-registry/pull/134) | — |
| `ISC_DHCP_RELAY` | `ISC_DHCP_RELAY` | DEB | Not migrated | — | — |
| `KDUMP_TOOLS` | `KDUMP_TOOLS` | DEB | Not migrated | — | — |
| `LIBFIB` | `LIBFIB`, `LIBFIB_DEV` | DEB | PR | [buildimage#51](https://github.com/securely1g/sonic-buildimage/pull/51) (open) | — |
| `LIBNL3` | `LIBNL3`, `LIBNL3_DEV`, `LIBNL_CLI`, `LIBNL_CLI_DEV`, `LIBNL_GENL3`, `LIBNL_GENL3_DEV`, `LIBNL_NF3`, `LIBNL_NF3_DEV`, `LIBNL_ROUTE3`, `LIBNL_ROUTE3_DEV` | DEB | Merged | [registry#1](https://github.com/securely1g/sonic-bazel-registry/pull/1); [registry#55](https://github.com/securely1g/sonic-bazel-registry/pull/55); [registry#103](https://github.com/securely1g/sonic-bazel-registry/pull/103); [registry#132](https://github.com/securely1g/sonic-bazel-registry/pull/132); [registry#142](https://github.com/securely1g/sonic-bazel-registry/pull/142); [registry#148](https://github.com/securely1g/sonic-bazel-registry/pull/148) (open) | — |
| `LIBNSS_RADIUS` | `LIBNSS_RADIUS` | DEB | Not migrated | — | — |
| `LIBPAM_RADIUS` | `LIBPAM_RADIUS` | DEB | Not migrated | — | — |
| `LIBTAC2` | `LIBTAC2`, `LIBPAM_TACPLUS`, `LIBTAC_DEV` | DEB | Not migrated | — | — |
| `LIBYANG3` | `LIBYANG3`, `LIBYANG3_DEV` | DEB | Merged | [registry#2](https://github.com/securely1g/sonic-bazel-registry/pull/2); [registry#6](https://github.com/securely1g/sonic-bazel-registry/pull/6); [registry#84](https://github.com/securely1g/sonic-bazel-registry/pull/84); [registry#101](https://github.com/securely1g/sonic-bazel-registry/pull/101); [registry#131](https://github.com/securely1g/sonic-bazel-registry/pull/131); [registry#143](https://github.com/securely1g/sonic-bazel-registry/pull/143); [registry#149](https://github.com/securely1g/sonic-bazel-registry/pull/149) (open) | — |
| `LIB_SONIC_DASH_API` | `LIB_SONIC_DASH_API` | DEB | Merged | [dash-api#1](https://github.com/securely1g/sonic-dash-api/pull/1); [dash-api#4](https://github.com/securely1g/sonic-dash-api/pull/4); [dash-api#5](https://github.com/securely1g/sonic-dash-api/pull/5); [dash-api#6](https://github.com/securely1g/sonic-dash-api/pull/6) (open); [registry#19](https://github.com/securely1g/sonic-bazel-registry/pull/19); [registry#140](https://github.com/securely1g/sonic-bazel-registry/pull/140) (open); [registry#156](https://github.com/securely1g/sonic-bazel-registry/pull/156) (open) | — |
| `LINUX_HEADERS_COMMON` | `LINUX_HEADERS_COMMON`, `LINUX_KBUILD`, `LINUX_KERNEL` | DEB | Merged | [linux-kernel#1](https://github.com/securely1g/sonic-linux-kernel/pull/1); [linux-kernel#2](https://github.com/securely1g/sonic-linux-kernel/pull/2); [linux-kernel#3](https://github.com/securely1g/sonic-linux-kernel/pull/3); [linux-kernel#4](https://github.com/securely1g/sonic-linux-kernel/pull/4); [linux-kernel#5](https://github.com/securely1g/sonic-linux-kernel/pull/5); [buildimage#6](https://github.com/securely1g/sonic-buildimage/pull/6); [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30); [buildimage#47](https://github.com/securely1g/sonic-buildimage/pull/47) (open); [registry#30](https://github.com/securely1g/sonic-bazel-registry/pull/30); [registry#124](https://github.com/securely1g/sonic-bazel-registry/pull/124); [registry#139](https://github.com/securely1g/sonic-bazel-registry/pull/139) (open) | — |
| `LLDPD` | `LLDPD` | DEB | Not migrated | — | — |
| `LM_SENSORS` | `LM_SENSORS`, `FANCONTROL`, `LIBSENSORS`, `SENSORD` | DEB | Not migrated | — | — |
| `MAKEDUMPFILE` | `MAKEDUMPFILE` | DEB | Not migrated | — | — |
| `MONIT` | `MONIT` | DEB | Not migrated | — | — |
| `P4LANG_PI` | `P4LANG_PI` | DEB | Merged | [registry#88](https://github.com/securely1g/sonic-bazel-registry/pull/88); [registry#107](https://github.com/securely1g/sonic-bazel-registry/pull/107) | — |
| `PDDF_PLATFORM_API_BASE_PY3` | `PDDF_PLATFORM_API_BASE_PY3` | WHEEL | Not migrated | — | — |
| `PSAMPLE` | `PSAMPLE` | DEB | Not migrated | — | — |
| `RASDAEMON` | `RASDAEMON` | DEB | Not migrated | — | — |
| `REDIS_DUMP_LOAD_PY3` | `REDIS_DUMP_LOAD_PY3` | WHEEL | Merged | [buildimage#9](https://github.com/securely1g/sonic-buildimage/pull/9); [buildimage#21](https://github.com/securely1g/sonic-buildimage/pull/21); [buildimage#27](https://github.com/securely1g/sonic-buildimage/pull/27); [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30) | — |
| `SCAPY` | `SCAPY` | WHEEL | Not migrated | — | — |
| `SEDUTIL` | `SEDUTIL` | DEB | Not migrated | — | — |
| `SFLOWTOOL` | `SFLOWTOOL` | DEB | Not migrated | — | — |
| `SOCAT` | `SOCAT` | DEB | Merged | [registry#62](https://github.com/securely1g/sonic-bazel-registry/pull/62); [registry#99](https://github.com/securely1g/sonic-bazel-registry/pull/99); [registry#133](https://github.com/securely1g/sonic-bazel-registry/pull/133) | — |
| `SONIC_DEVICE_DATA` | `SONIC_DEVICE_DATA` | DEB | Not migrated | — | — |
| `SONIC_HOST_SERVICES_DATA` | `SONIC_HOST_SERVICES_DATA` | DEB | Not migrated | — | — |
| `SONIC_NETTOOLS` | `SONIC_NETTOOLS` | DEB | Not migrated | — | — |
| `SYMCRYPT_OPENSSL` | `SYMCRYPT_OPENSSL`, `FIPS_KRB5`, `FIPS_KRB5_3`, `FIPS_KRB5_LIBGSSAPI`, `FIPS_KRB5_SUPPORT0`, `FIPS_OPENSSL`, `FIPS_OPENSSL_LIBSSL`, `FIPS_OPENSSL_LIBSSL_DEV` | DEB | Merged | [fips#4](https://github.com/securely1g/sonic-fips/pull/4); [fips#7](https://github.com/securely1g/sonic-fips/pull/7); [registry#67](https://github.com/securely1g/sonic-bazel-registry/pull/67); [registry#106](https://github.com/securely1g/sonic-bazel-registry/pull/106); [registry#136](https://github.com/securely1g/sonic-bazel-registry/pull/136); [fips#3](https://github.com/securely1g/sonic-fips/pull/3); [fips#1](https://github.com/securely1g/sonic-fips/pull/1); [fips#5](https://github.com/securely1g/sonic-fips/pull/5) | — |
| `SYSTEMD_SONIC_GENERATOR` | `SYSTEMD_SONIC_GENERATOR` | DEB | Not migrated | — | — |
| `VS_PLATFORM_MODULE` | `VS_PLATFORM_MODULE` | DEB | Not migrated | — | — |

### Layer 2 — 10 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `AUDISP_TACPLUS` | `AUDISP_TACPLUS` | DEB | Not migrated | — | `LIBTAC2` (L1) |
| `BASH_TACPLUS` | `BASH_TACPLUS` | DEB | Not migrated | — | `LIBTAC2` (L1) |
| `DOCKER_BASE_TRIXIE` | `DOCKER_BASE_TRIXIE` | DOCKER | Merged | [buildimage#9](https://github.com/securely1g/sonic-buildimage/pull/9); [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30); [buildimage#33](https://github.com/securely1g/sonic-buildimage/pull/33) (open); [buildimage#54](https://github.com/securely1g/sonic-buildimage/pull/54) (open) | `IPROUTE2` (L1); `SOCAT` (L1); `SYMCRYPT_OPENSSL` (L1) |
| `FRR` | `FRR`, `FRR_SNMP` | DEB | PR | [buildimage#51](https://github.com/securely1g/sonic-buildimage/pull/51) (open) | `LIBFIB` (L1); `LIBYANG3` (L1) |
| `LIBNSS_TACPLUS` | `LIBNSS_TACPLUS` | DEB | Not migrated | — | `LIBTAC2` (L1) |
| `LIBTEAM` | `LIBTEAM`, `LIBTEAMDCTL`, `LIBTEAM_DEV`, `LIBTEAM_UTILS` | DEB | PR | [buildimage#61](https://github.com/securely1g/sonic-buildimage/pull/61) (open) | `LIBNL3` (L1) |
| `LIBYANG3_PY3` | `LIBYANG3_PY3` | DEB | Merged | [registry#9](https://github.com/securely1g/sonic-bazel-registry/pull/9); [registry#53](https://github.com/securely1g/sonic-bazel-registry/pull/53); [registry#85](https://github.com/securely1g/sonic-bazel-registry/pull/85); [registry#102](https://github.com/securely1g/sonic-bazel-registry/pull/102); [registry#135](https://github.com/securely1g/sonic-bazel-registry/pull/135); [registry#144](https://github.com/securely1g/sonic-bazel-registry/pull/144) | `LIBYANG3` (L1) |
| `OPENSSH_SERVER` | `OPENSSH_SERVER` | DEB | Not migrated | — | `LIBNL3` (L1) |
| `P4LANG_BMV2` | `P4LANG_BMV2` | DEB | Merged | [registry#89](https://github.com/securely1g/sonic-bazel-registry/pull/89); [registry#108](https://github.com/securely1g/sonic-bazel-registry/pull/108) | `P4LANG_PI` (L1) |
| `SWSSSDK_PY3` | `SWSSSDK_PY3` | WHEEL | Merged | [buildimage#9](https://github.com/securely1g/sonic-buildimage/pull/9); [buildimage#21](https://github.com/securely1g/sonic-buildimage/pull/21); [buildimage#27](https://github.com/securely1g/sonic-buildimage/pull/27); [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30) | `REDIS_DUMP_LOAD_PY3` (L1) |

### Layer 3 — 2 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `P4LANG_P4C` | `P4LANG_P4C` | DEB | Merged | [registry#86](https://github.com/securely1g/sonic-bazel-registry/pull/86); [registry#109](https://github.com/securely1g/sonic-bazel-registry/pull/109) | `SCAPY` (L1); `P4LANG_BMV2` (L2) |
| `SONIC_YANG_MODELS_PY3` | `SONIC_YANG_MODELS_PY3` | WHEEL | Merged | [buildimage#27](https://github.com/securely1g/sonic-buildimage/pull/27); [buildimage#32](https://github.com/securely1g/sonic-buildimage/pull/32); [buildimage#47](https://github.com/securely1g/sonic-buildimage/pull/47) (open); [registry#13](https://github.com/securely1g/sonic-bazel-registry/pull/13); [registry#15](https://github.com/securely1g/sonic-bazel-registry/pull/15); [registry#70](https://github.com/securely1g/sonic-bazel-registry/pull/70) | `LIBYANG3` (L1); `LIBYANG3_PY3` (L2) |

### Layer 4 — 3 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `DASH_SAI` | `DASH_SAI` | DEB | Merged | [DASH#1](https://github.com/securely1g/DASH/pull/1); [DASH#2](https://github.com/securely1g/DASH/pull/2); [DASH#3](https://github.com/securely1g/DASH/pull/3); [registry#94](https://github.com/securely1g/sonic-bazel-registry/pull/94); [registry#112](https://github.com/securely1g/sonic-bazel-registry/pull/112) | `P4LANG_PI` (L1); `P4LANG_BMV2` (L2); `P4LANG_P4C` (L3) |
| `SONIC_MGMT_COMMON` | `SONIC_MGMT_COMMON`, `SONIC_MGMT_COMMON_CODEGEN` | DEB | Not migrated | — | `LIBYANG3` (L1); `SONIC_YANG_MODELS_PY3` (L3) |
| `SONIC_YANG_MGMT_PY3` | `SONIC_YANG_MGMT_PY3` | WHEEL | Merged | [buildimage#27](https://github.com/securely1g/sonic-buildimage/pull/27); [registry#14](https://github.com/securely1g/sonic-bazel-registry/pull/14) | `LIBYANG3` (L1); `LIBYANG3_PY3` (L2); `SONIC_YANG_MODELS_PY3` (L3) |

### Layer 5 — 2 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `LIBSWSSCOMMON` | `LIBSWSSCOMMON`, `LIBSWSSCOMMON_DEV`, `PYTHON3_SWSSCOMMON`, `SONIC_DB_CLI` | DEB | Merged | [swss-common#1](https://github.com/securely1g/sonic-swss-common/pull/1); [swss-common#2](https://github.com/securely1g/sonic-swss-common/pull/2); [swss-common#4](https://github.com/securely1g/sonic-swss-common/pull/4); [swss-common#6](https://github.com/securely1g/sonic-swss-common/pull/6); [swss-common#8](https://github.com/securely1g/sonic-swss-common/pull/8); [swss-common#11](https://github.com/securely1g/sonic-swss-common/pull/11); [swss-common#14](https://github.com/securely1g/sonic-swss-common/pull/14); [swss-common#16](https://github.com/securely1g/sonic-swss-common/pull/16); [swss-common#18](https://github.com/securely1g/sonic-swss-common/pull/18); [swss-common#19](https://github.com/securely1g/sonic-swss-common/pull/19); [swss-common#21](https://github.com/securely1g/sonic-swss-common/pull/21); [swss-common#22](https://github.com/securely1g/sonic-swss-common/pull/22); [swss-common#23](https://github.com/securely1g/sonic-swss-common/pull/23); [swss-common#27](https://github.com/securely1g/sonic-swss-common/pull/27); [swss-common#28](https://github.com/securely1g/sonic-swss-common/pull/28); [swss-common#30](https://github.com/securely1g/sonic-swss-common/pull/30); [swss-common#31](https://github.com/securely1g/sonic-swss-common/pull/31); [swss-common#32](https://github.com/securely1g/sonic-swss-common/pull/32); [swss-common#33](https://github.com/securely1g/sonic-swss-common/pull/33); [swss-common#34](https://github.com/securely1g/sonic-swss-common/pull/34); [swss-common#35](https://github.com/securely1g/sonic-swss-common/pull/35) (open); [swss-common#36](https://github.com/securely1g/sonic-swss-common/pull/36) (open); [swss-common#37](https://github.com/securely1g/sonic-swss-common/pull/37) (open); [registry#5](https://github.com/securely1g/sonic-bazel-registry/pull/5); [registry#16](https://github.com/securely1g/sonic-bazel-registry/pull/16); [registry#18](https://github.com/securely1g/sonic-bazel-registry/pull/18); [registry#40](https://github.com/securely1g/sonic-bazel-registry/pull/40); [registry#43](https://github.com/securely1g/sonic-bazel-registry/pull/43); [registry#57](https://github.com/securely1g/sonic-bazel-registry/pull/57); [registry#104](https://github.com/securely1g/sonic-bazel-registry/pull/104); [registry#145](https://github.com/securely1g/sonic-bazel-registry/pull/145); [registry#153](https://github.com/securely1g/sonic-bazel-registry/pull/153); [registry#161](https://github.com/securely1g/sonic-bazel-registry/pull/161) (open) | `LIBNL3` (L1); `LIBYANG3` (L1); `LIBYANG3_PY3` (L2); `SONIC_YANG_MODELS_PY3` (L3); `SONIC_YANG_MGMT_PY3` (L4) |
| `SONIC_MGMT_FRAMEWORK` | `SONIC_MGMT_FRAMEWORK` | DEB | Not migrated | — | `SONIC_MGMT_COMMON` (L4) |

### Layer 6 — 18 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `DASH_HA` | `DASH_HA` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `LIBSAIREDIS` | `LIBSAIREDIS`, `LIBSAIMETADATA`, `LIBSAIMETADATA_DEV`, `LIBSAIREDIS_DEV`, `LIBSAIVS`, `LIBSAIVS_DEV`, `SYNCD_VS` | DEB | Merged | [sairedis#1](https://github.com/securely1g/sonic-sairedis/pull/1); [sairedis#2](https://github.com/securely1g/sonic-sairedis/pull/2); [sairedis#3](https://github.com/securely1g/sonic-sairedis/pull/3); [sairedis#5](https://github.com/securely1g/sonic-sairedis/pull/5); [sairedis#6](https://github.com/securely1g/sonic-sairedis/pull/6); [sairedis#7](https://github.com/securely1g/sonic-sairedis/pull/7); [sairedis#8](https://github.com/securely1g/sonic-sairedis/pull/8) (open); [registry#20](https://github.com/securely1g/sonic-bazel-registry/pull/20); [registry#56](https://github.com/securely1g/sonic-bazel-registry/pull/56); [registry#105](https://github.com/securely1g/sonic-bazel-registry/pull/105); [registry#137](https://github.com/securely1g/sonic-bazel-registry/pull/137); [registry#154](https://github.com/securely1g/sonic-bazel-registry/pull/154); [registry#157](https://github.com/securely1g/sonic-bazel-registry/pull/157) (open) | `DASH_SAI` (L4); `LIBSWSSCOMMON` (L5) |
| `SONIC_BMPD` | `SONIC_BMPD` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SONIC_CTRMGRD_RS` | `SONIC_CTRMGRD_RS` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SONIC_DHCP4RELAY` | `SONIC_DHCP4RELAY` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SONIC_DHCPMON` | `SONIC_DHCPMON` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SONIC_DHCPRELAY` | `SONIC_DHCPRELAY` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SONIC_EVENTD` | `SONIC_EVENTD`, `SONIC_RSYSLOG_PLUGIN` | DEB | Merged | [buildimage#23](https://github.com/securely1g/sonic-buildimage/pull/23); [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30) | `LIBSWSSCOMMON` (L5) |
| `SONIC_HOST_SERVICES_RS` | `SONIC_HOST_SERVICES_RS` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SONIC_LINKMGRD` | `SONIC_LINKMGRD` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SONIC_P4RT` | `SONIC_P4RT` | DEB | Merged | [buildimage#2](https://github.com/securely1g/sonic-buildimage/pull/2) (open); [buildimage#8](https://github.com/securely1g/sonic-buildimage/pull/8) (open); [buildimage#9](https://github.com/securely1g/sonic-buildimage/pull/9); [buildimage#13](https://github.com/securely1g/sonic-buildimage/pull/13); [buildimage#36](https://github.com/securely1g/sonic-buildimage/pull/36) (open); [buildimage#42](https://github.com/securely1g/sonic-buildimage/pull/42) | `LIBSWSSCOMMON` (L5) |
| `SONIC_PY_COMMON_PY3` | `SONIC_PY_COMMON_PY3` | WHEEL | Merged | [buildimage#9](https://github.com/securely1g/sonic-buildimage/pull/9) | `SWSSSDK_PY3` (L2); `LIBSWSSCOMMON` (L5) |
| `SONIC_SUPERVISORD_UTILITIES_RS` | `SONIC_SUPERVISORD_UTILITIES_RS` | DEB | Merged | [buildimage#25](https://github.com/securely1g/sonic-buildimage/pull/25); [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30) | `LIBSWSSCOMMON` (L5) |
| `SONIC_TELEMETRY` | `SONIC_TELEMETRY` | DEB | Not migrated | — | `SONIC_MGMT_COMMON` (L4); `LIBSWSSCOMMON` (L5) |
| `STP` | `STP` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SYSLOG_COUNTER` | `SYSLOG_COUNTER` | DEB | Not migrated | — | `LIBSWSSCOMMON` (L5) |
| `SYSMGR` | `SYSMGR` | DEB | PR | [buildimage#2](https://github.com/securely1g/sonic-buildimage/pull/2) (open); [buildimage#5](https://github.com/securely1g/sonic-buildimage/pull/5) (open); [buildimage#7](https://github.com/securely1g/sonic-buildimage/pull/7) (open) | `LIBSWSSCOMMON` (L5) |
| `WPASUPPLICANT` | `WPASUPPLICANT` | DEB | Not migrated | — | `LIBNL3` (L1); `LIBSWSSCOMMON` (L5) |

### Layer 7 — 10 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `DBSYNCD_PY3` | `DBSYNCD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_CONFIG_ENGINE_PY3` | `SONIC_CONFIG_ENGINE_PY3` | WHEEL | Merged | [buildimage#9](https://github.com/securely1g/sonic-buildimage/pull/9); [buildimage#21](https://github.com/securely1g/sonic-buildimage/pull/21); [buildimage#27](https://github.com/securely1g/sonic-buildimage/pull/27); [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30) | `LIBYANG3` (L1); `LIBYANG3_PY3` (L2); `SONIC_YANG_MODELS_PY3` (L3); `SONIC_YANG_MGMT_PY3` (L4); `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_CONTAINERCFGD` | `SONIC_CONTAINERCFGD` | WHEEL | Merged | [buildimage#19](https://github.com/securely1g/sonic-buildimage/pull/19) | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_CTRMGRD` | `SONIC_CTRMGRD` | WHEEL | Not migrated | [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30) | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_DHCP_UTILITIES_PY3` | `SONIC_DHCP_UTILITIES_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_LEDD_PY3` | `SONIC_LEDD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_PCIED_PY3` | `SONIC_PCIED_PY3` | WHEEL | Not migrated | — | `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_STORMOND_PY3` | `SONIC_STORMOND_PY3` | WHEEL | Not migrated | — | `SONIC_PY_COMMON_PY3` (L6) |
| `SONIC_SUPERVISORD_UTILITIES` | `SONIC_SUPERVISORD_UTILITIES` | WHEEL | Merged | [buildimage#21](https://github.com/securely1g/sonic-buildimage/pull/21) | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6) |
| `SWSS` | `SWSS` | DEB | Merged | [swss#1](https://github.com/securely1g/sonic-swss/pull/1); [swss#4](https://github.com/securely1g/sonic-swss/pull/4); [swss#5](https://github.com/securely1g/sonic-swss/pull/5); [swss#7](https://github.com/securely1g/sonic-swss/pull/7); [swss#8](https://github.com/securely1g/sonic-swss/pull/8) (open) | `LIBFIB` (L1); `LIB_SONIC_DASH_API` (L1); `LIBTEAM` (L2); `LIBSWSSCOMMON` (L5); `LIBSAIREDIS` (L6); `STP` (L6) |

### Layer 8 — 5 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `DOCKER_CONFIG_ENGINE_TRIXIE` | `DOCKER_CONFIG_ENGINE_TRIXIE` | DOCKER | Merged | [buildimage#30](https://github.com/securely1g/sonic-buildimage/pull/30); [buildimage#33](https://github.com/securely1g/sonic-buildimage/pull/33) (open); [buildimage#54](https://github.com/securely1g/sonic-buildimage/pull/54) (open) | `LIBYANG3` (L1); `DOCKER_BASE_TRIXIE` (L2); `LIBYANG3_PY3` (L2); `SONIC_YANG_MODELS_PY3` (L3); `SONIC_YANG_MGMT_PY3` (L4); `LIBSWSSCOMMON` (L5); `SONIC_EVENTD` (L6); `SONIC_PY_COMMON_PY3` (L6); `SONIC_SUPERVISORD_UTILITIES_RS` (L6); `SONIC_CONFIG_ENGINE_PY3` (L7); `SONIC_CONTAINERCFGD` (L7); `SONIC_SUPERVISORD_UTILITIES` (L7) |
| `SONIC_BGPCFGD` | `SONIC_BGPCFGD` | WHEEL | Merged | [buildimage#58](https://github.com/securely1g/sonic-buildimage/pull/58) | `LIBYANG3` (L1); `LIBYANG3_PY3` (L2); `SONIC_YANG_MODELS_PY3` (L3); `SONIC_YANG_MGMT_PY3` (L4); `LIBSWSSCOMMON` (L5); `SONIC_CONFIG_ENGINE_PY3` (L7) |
| `SONIC_FRR_MGMT_FRAMEWORK` | `SONIC_FRR_MGMT_FRAMEWORK` | WHEEL | Merged | [buildimage#57](https://github.com/securely1g/sonic-buildimage/pull/57) | `SONIC_CONFIG_ENGINE_PY3` (L7) |
| `SONIC_PLATFORM_COMMON_PY3` | `SONIC_PLATFORM_COMMON_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_CONFIG_ENGINE_PY3` (L7) |
| `SYSTEM_HEALTH` | `SYSTEM_HEALTH` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_CONFIG_ENGINE_PY3` (L7) |

### Layer 9 — 26 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `ASYNCSNMP_PY3` | `ASYNCSNMP_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `DOCKER_BMP_WATCHDOG` | `DOCKER_BMP_WATCHDOG` | DOCKER | Not migrated | — | `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_DATABASE` | `DOCKER_DATABASE` | DOCKER | Not migrated | — | `LIB_SONIC_DASH_API` (L1); `LIBSWSSCOMMON` (L5); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_GBSYNCD_BASE` | `DOCKER_GBSYNCD_BASE` | DOCKER | Not migrated | — | `LIBNL3` (L1); `LIBSAIREDIS` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_GNMI` | `DOCKER_GNMI` | DOCKER | Not migrated | — | `SONIC_MGMT_COMMON` (L4); `SONIC_TELEMETRY` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_GNMI_SIDECAR` | `DOCKER_GNMI_SIDECAR` | DOCKER | Not migrated | — | `LIBYANG3_PY3` (L2); `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_GNMI_WATCHDOG` | `DOCKER_GNMI_WATCHDOG` | DOCKER | Not migrated | — | `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_LLDP` | `DOCKER_LLDP` | DOCKER | Not migrated | — | `LLDPD` (L1); `LIBSWSSCOMMON` (L5); `DBSYNCD_PY3` (L7); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_MGMT_FRAMEWORK` | `DOCKER_MGMT_FRAMEWORK` | DOCKER | Not migrated | — | `SONIC_MGMT_COMMON` (L4); `SONIC_MGMT_FRAMEWORK` (L5); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_MUX` | `DOCKER_MUX` | DOCKER | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_LINKMGRD` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_OTEL` | `DOCKER_OTEL` | DOCKER | Not migrated | — | `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_P4RT` | `DOCKER_P4RT` | DOCKER | Not migrated | — | `SONIC_P4RT` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_RESTAPI_SIDECAR` | `DOCKER_RESTAPI_SIDECAR` | DOCKER | Not migrated | — | `SONIC_PY_COMMON_PY3` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_ROUTER_ADVERTISER` | `DOCKER_ROUTER_ADVERTISER` | DOCKER | Not migrated | — | `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_SWSS_LAYER_TRIXIE` | `DOCKER_SWSS_LAYER_TRIXIE` | DOCKER | Not migrated | — | `SWSS` (L7); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_SYNCD_BASE` | `DOCKER_SYNCD_BASE` | DOCKER | Merged | [buildimage#13](https://github.com/securely1g/sonic-buildimage/pull/13); [buildimage#33](https://github.com/securely1g/sonic-buildimage/pull/33) (open); [buildimage#54](https://github.com/securely1g/sonic-buildimage/pull/54) (open); [buildimage#65](https://github.com/securely1g/sonic-buildimage/pull/65) (open) | `LIBNL3` (L1); `LIBSAIREDIS` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `DOCKER_SYSMGR` | `DOCKER_SYSMGR` | DOCKER | PR | [buildimage#2](https://github.com/securely1g/sonic-buildimage/pull/2) (open); [buildimage#5](https://github.com/securely1g/sonic-buildimage/pull/5) (open) | `DOCKER_BASE_TRIXIE` (L2); `SYSMGR` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8) |
| `SONIC_BMCCTLD_PY3` | `SONIC_BMCCTLD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_CHASSISD_PY3` | `SONIC_CHASSISD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_PSUD_PY3` | `SONIC_PSUD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_SENSORMOND_PY3` | `SONIC_SENSORMOND_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_SYSEEPROMD_PY3` | `SONIC_SYSEEPROMD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_THERMALCTLD_PY3` | `SONIC_THERMALCTLD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_UTILITIES_PY3` | `SONIC_UTILITIES_PY3` | WHEEL | Not migrated | — | `LIBYANG3` (L1); `LIBYANG3_PY3` (L2); `SONIC_YANG_MODELS_PY3` (L3); `SONIC_YANG_MGMT_PY3` (L4); `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_CONFIG_ENGINE_PY3` (L7); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_XCVRD_PY3` | `SONIC_XCVRD_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |
| `SONIC_YCABLED_PY3` | `SONIC_YCABLED_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_PLATFORM_COMMON_PY3` (L8) |

### Layer 10 — 14 components

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `DOCKER_DASH_HA` | `DOCKER_DASH_HA` | DOCKER | Not migrated | — | `DASH_HA` (L6); `DOCKER_SWSS_LAYER_TRIXIE` (L9) |
| `DOCKER_DHCP_RELAY` | `DOCKER_DHCP_RELAY` | DOCKER | Not migrated | — | `ISC_DHCP_RELAY` (L1); `LIBSWSSCOMMON` (L5); `SONIC_DHCP4RELAY` (L6); `SONIC_DHCPMON` (L6); `SONIC_DHCPRELAY` (L6); `SONIC_DHCP_UTILITIES_PY3` (L7); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8); `SONIC_UTILITIES_PY3` (L9) |
| `DOCKER_EVENTD` | `DOCKER_EVENTD` | DOCKER | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_EVENTD` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8); `SONIC_UTILITIES_PY3` (L9) |
| `DOCKER_FPM_FRR` | `DOCKER_FPM_FRR` | DOCKER | Not migrated | — | `LIBYANG3` (L1); `FRR` (L2); `SWSS` (L7); `SONIC_BGPCFGD` (L8); `SONIC_FRR_MGMT_FRAMEWORK` (L8); `DOCKER_SWSS_LAYER_TRIXIE` (L9) |
| `DOCKER_MACSEC` | `DOCKER_MACSEC` | DOCKER | Not migrated | — | `LIBYANG3_PY3` (L2); `LIBSWSSCOMMON` (L5); `WPASUPPLICANT` (L6); `DOCKER_SWSS_LAYER_TRIXIE` (L9); `SONIC_UTILITIES_PY3` (L9) |
| `DOCKER_NAT` | `DOCKER_NAT` | DOCKER | Not migrated | — | `SWSS` (L7); `DOCKER_SWSS_LAYER_TRIXIE` (L9) |
| `DOCKER_ORCHAGENT` | `DOCKER_ORCHAGENT` | DOCKER | Merged | [buildimage#2](https://github.com/securely1g/sonic-buildimage/pull/2) (open); [buildimage#5](https://github.com/securely1g/sonic-buildimage/pull/5) (open); [buildimage#9](https://github.com/securely1g/sonic-buildimage/pull/9); [buildimage#13](https://github.com/securely1g/sonic-buildimage/pull/13); [buildimage#15](https://github.com/securely1g/sonic-buildimage/pull/15); [buildimage#33](https://github.com/securely1g/sonic-buildimage/pull/33) (open); [buildimage#40](https://github.com/securely1g/sonic-buildimage/pull/40) (open); [buildimage#54](https://github.com/securely1g/sonic-buildimage/pull/54) (open) | `LIB_SONIC_DASH_API` (L1); `SCAPY` (L1); `SWSS` (L7); `DOCKER_SWSS_LAYER_TRIXIE` (L9) |
| `DOCKER_PLATFORM_MONITOR` | `DOCKER_PLATFORM_MONITOR` | DOCKER | Not migrated | — | `LM_SENSORS` (L1); `PDDF_PLATFORM_API_BASE_PY3` (L1); `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_CONFIG_ENGINE_PY3` (L7); `SONIC_LEDD_PY3` (L7); `SONIC_PCIED_PY3` (L7); `SONIC_STORMOND_PY3` (L7); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8); `SONIC_PLATFORM_COMMON_PY3` (L8); `SONIC_BMCCTLD_PY3` (L9); `SONIC_CHASSISD_PY3` (L9); `SONIC_PSUD_PY3` (L9); `SONIC_SENSORMOND_PY3` (L9); `SONIC_SYSEEPROMD_PY3` (L9); `SONIC_THERMALCTLD_PY3` (L9); `SONIC_XCVRD_PY3` (L9); `SONIC_YCABLED_PY3` (L9) |
| `DOCKER_SFLOW` | `DOCKER_SFLOW` | DOCKER | Not migrated | — | `HSFLOWD` (L1); `PSAMPLE` (L1); `SFLOWTOOL` (L1); `SWSS` (L7); `DOCKER_SWSS_LAYER_TRIXIE` (L9) |
| `DOCKER_SNMP` | `DOCKER_SNMP` | DOCKER | Not migrated | — | `SONIC_PY_COMMON_PY3` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8); `SONIC_PLATFORM_COMMON_PY3` (L8); `ASYNCSNMP_PY3` (L9) |
| `DOCKER_TEAMD` | `DOCKER_TEAMD` | DOCKER | Not migrated | — | `LIBTEAM` (L2); `DOCKER_SWSS_LAYER_TRIXIE` (L9) |
| `SONIC_BMPCFGD` | `SONIC_BMPCFGD` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_UTILITIES_PY3` (L9) |
| `SONIC_HOST_SERVICES_PY3` | `SONIC_HOST_SERVICES_PY3` | WHEEL | Not migrated | — | `LIBSWSSCOMMON` (L5); `SONIC_PY_COMMON_PY3` (L6); `SONIC_UTILITIES_PY3` (L9) |
| `SONIC_UTILITIES_DATA` | `SONIC_UTILITIES_DATA` | DEB | Not migrated | — | `SONIC_UTILITIES_PY3` (L9) |

### Layer 11 — 1 component

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `DOCKER_BMP` | `DOCKER_BMP` | DOCKER | Not migrated | — | `LIBYANG3_PY3` (L2); `LIBSWSSCOMMON` (L5); `SONIC_BMPD` (L6); `DOCKER_CONFIG_ENGINE_TRIXIE` (L8); `SONIC_BMPCFGD` (L10) |

### Layer 12 — 1 component

| Component | Outputs | Type | Bazel status | PR | Dependencies |
|---|---|---|---|---|---|
| `SONIC_ONE_IMAGE` | `SONIC_ONE_IMAGE` | INSTALLER | PR | [buildimage#2](https://github.com/securely1g/sonic-buildimage/pull/2) (open); [buildimage#70](https://github.com/securely1g/sonic-buildimage/pull/70) (open) | `BASH` (L1); `DOCKER_DASH_ENGINE` (L1); `IFUPDOWN2` (L1); `INITRAMFS_TOOLS` (L1); `KDUMP_TOOLS` (L1); `LIBNSS_RADIUS` (L1); `LIBPAM_RADIUS` (L1); `LIBTAC2` (L1); `LINUX_HEADERS_COMMON` (L1); `MAKEDUMPFILE` (L1); `MONIT` (L1); `PDDF_PLATFORM_API_BASE_PY3` (L1); `RASDAEMON` (L1); `SEDUTIL` (L1); `SOCAT` (L1); `SONIC_DEVICE_DATA` (L1); `SONIC_HOST_SERVICES_DATA` (L1); `SONIC_NETTOOLS` (L1); `SYMCRYPT_OPENSSL` (L1); `SYSTEMD_SONIC_GENERATOR` (L1); `VS_PLATFORM_MODULE` (L1); `AUDISP_TACPLUS` (L2); `BASH_TACPLUS` (L2); `LIBNSS_TACPLUS` (L2); `OPENSSH_SERVER` (L2); `SONIC_YANG_MODELS_PY3` (L3); `SONIC_YANG_MGMT_PY3` (L4); `LIBSWSSCOMMON` (L5); `SONIC_CTRMGRD_RS` (L6); `SONIC_EVENTD` (L6); `SONIC_HOST_SERVICES_RS` (L6); `SONIC_PY_COMMON_PY3` (L6); `SYSLOG_COUNTER` (L6); `SONIC_CONFIG_ENGINE_PY3` (L7); `SONIC_CTRMGRD` (L7); `SONIC_PLATFORM_COMMON_PY3` (L8); `SYSTEM_HEALTH` (L8); `DOCKER_BMP_WATCHDOG` (L9); `DOCKER_DATABASE` (L9); `DOCKER_GBSYNCD_BASE` (L9); `DOCKER_GNMI` (L9); `DOCKER_GNMI_SIDECAR` (L9); `DOCKER_GNMI_WATCHDOG` (L9); `DOCKER_LLDP` (L9); `DOCKER_MGMT_FRAMEWORK` (L9); `DOCKER_MUX` (L9); `DOCKER_OTEL` (L9); `DOCKER_P4RT` (L9); `DOCKER_RESTAPI_SIDECAR` (L9); `DOCKER_ROUTER_ADVERTISER` (L9); `DOCKER_SYNCD_BASE` (L9); `DOCKER_SYSMGR` (L9); `SONIC_UTILITIES_PY3` (L9); `DOCKER_DASH_HA` (L10); `DOCKER_DHCP_RELAY` (L10); `DOCKER_EVENTD` (L10); `DOCKER_FPM_FRR` (L10); `DOCKER_MACSEC` (L10); `DOCKER_NAT` (L10); `DOCKER_ORCHAGENT` (L10); `DOCKER_PLATFORM_MONITOR` (L10); `DOCKER_SFLOW` (L10); `DOCKER_SNMP` (L10); `DOCKER_TEAMD` (L10); `SONIC_HOST_SERVICES_PY3` (L10); `SONIC_UTILITIES_DATA` (L10); `DOCKER_BMP` (L11) |
