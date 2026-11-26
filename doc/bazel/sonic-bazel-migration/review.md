# 技能修复与复核

2026-11-11。审查对象为当前技能工作区；实现基线为
`/home/songqing.sq/projects/guohan/sonic-build-infra`，HEAD 为
`4854fb00e85201701b566169ccf298de8ad4d1ed`，读取时工作区干净。
本轮仅修改技能，保留进入任务前已有的工作区修改。

初始本地复核结论：原始 5 项建议中，4 项确认并修复；Debian 私有镜像建议当时按本地 infra 配置纠正。发布前同步的新策略及调整见下段。
补充审查发现的 7 项差异或歧义也已修正。

发布前同步 securely1g/SONiC master `ee63839dbc662d30563d88a918021e74c7f7b501`，
该基线已合入 #49 的部分一致性修复，以及 #52 的下载策略。PR 保留这些主线变更。
新的 Debian 下载走批准的私有镜像；公开 snapshot 地址只说明所检查 infra 的继承配置和来源。
APT 示例改用私有镜像占位符并单独保留快照时间戳，实际路径由获批镜像接口决定。
这是对新基线的适配；初始工作区和 infra 保持原样。

## 原始建议复核

| 项目 | 证据与修复 | 状态 |
| --- | --- | --- |
| 构建证据身份 | 原 helper 接受 revision B／ARM64 任务引用 revision A／AMD64 验证。现 [completion](scripts/task-progress.py) 比较任务、实现、验证三方的 `inputs`，要求源码身份、操作系统、工具链、执行／目标架构、特性和依赖；缺失或不匹配时拒绝，保持任务文件。显式新身份进入 merge 时，使生产者及传递消费者失效。[交接契约](references/phase-handoff.md) 同步 schema、旧记录补全及收集责任。 | PASS |
| OCI 安装顺序 | [安装接口](references/install-interfaces.md) 与 [OCI 流程](references/oci.md#real-debian-package-installation) 统一：实际包安装、完整 rootfs 替换、中间 OCI、APT 检查、源码／Python 层、最终元数据和覆盖检查。 | PASS |
| CI 状态时效 | [source-pr-ci](references/source-pr-ci.md#detect-missing-ci-during-babysitting) 明确每轮读取当前作业结果，仅复用已核对输入的稳定分类及预期作业列表。 | PASS |
| Debian 下载源 | infra 的 `apt/sources.json` 使用公开固定快照：普通包 `20260727T143429Z`，安全包 `20260726T121236Z`。[APT 示例](references/use-apt-libraries.md#global-source-configuration) 明确 Trixie 子集和真实 infra 来源。同步当前主线后，示例的新增下载地址按 #52 改为私有镜像占位符，快照时间戳保留为 provenance。 | PASS |
| helper 工作目录 | [公共契约](references/common-contract.md)、[首次收集](references/build-dep-graph.md)、[组件流程](references/component-workflow.md) 和 [重新收集](references/phase-handoff.md) 统一使用绝对 `SKILL_DIR` 和显式 `BUILDIMAGE_ROOT`。 | PASS |

## 补充一致性与实现差异

| 项目 | 实现依据／原矛盾 | 已实施修复 |
| --- | --- | --- |
| APT 已有版本变更 | infra `apt/README.md` 和 `apt/lock.py:200` 支持 `--allow-version-change`；技能原来只允许源变更后重解析。 | 公共契约、版本选择和 APT 更新流程均加入明确授权的版本变更路径；保护同一 suite/name/architecture/version 键的身份字段与校验和。 |
| APT 库导出 | infra `MODULE.bazel:80` 使用 `apt.import_lock(libraries=True)`；APT README 明确支持锁定 filemaps 和 CcInfo。 | 删除“version-2 只支持 data/control”的过时说明；正常导入示例补齐 sources、requests。 |
| 调试符号权限 | infra `tar/debug_symbols_tar.bzl:41` 用 mtree mutation 设置 regular debug 文件 0644，后续 `root_owned_tar` 调用保留默认模式。 | 安装指南说明实际决策点，并区分 `root_owned_tar` 可独立选择的 `regular_file_mode`。 |
| 模块身份 | infra `oci/sonic_oci/owner_metadata.py:21` 精确比较实际 MODULE.name；技能安装示例与 DEB／OCI 示例混用下划线和连字符。 | 统一示例为 `example-component`，说明 `module_name` 与实际模块名一致，仓库别名单独处理。 |
| Rust 元数据 | 主入口及清单后半部区分 crate_universe 与 from_cargo；清单前半部却要求所有 Rust 生成 Cargo.Bazel.lock。 | 将生成要求限定到适用的 rules_rust/crate_universe 路线；from_cargo 直接消费 Cargo.lock。 |
| 外部包构建路线 | 主入口禁止普通 configure/Make 包装；检查清单的旧措辞缺少明确例外条件。 | 清单和外部包指南统一为普通组件使用原生规则，明确批准的特殊流水线才保留包装。 |
| 发布授权 | 主入口曾将必要共享仓库工作与推送／PR 权限一起表述；公共契约要求遵守当前任务授权。 | 区分仓库修改范围和发布权限，沿用已有明确授权，技能自身不授予远端发布权限。 |

## 实现比对覆盖

- 全部 `SKILL.md` 与 45 份 references 做交叉引用、示例语法和关键契约检索。
- 文档中直接 load 的 infra 接口共 20 次、13 个唯一符号，文件均存在。核对 TAR、DEB、accounts、debug symbols、runtime metadata、installed state、wheel_layer、SWIG、binutils、Autoconf probe、source_build_tool、shared_library_cc_info 的对应实现。
- 补充核对 APT sources/requests/production lock/updater/library inputs、prepared_source、Go ZIP lock CLI、Rust Cargo runner、Python runtime_lock。
- 明确保留 wheel_layer 只输出 TAR 的实现边界；wheel-aware metadata/check adapter 是文档已注明的集成前置，所检查版本的 PythonRuntimeInfo 路线与它分别描述。
- 镜像／内核指南中的 buildimage、kernel 和第三方 ruleset 接口按其所属仓库标记；本次 infra 比对结论限于本地 infra 源码。源码比对与示例语法检查属于静态证据，实际组件／镜像构建另按迁移任务执行。

## 验证台账

环境：当前 Linux 工作区，系统 Python 3；技能脚本测试使用 `python3 -B`，独立场景写入 `/tmp`。

| 验证对象 | 命令／证据 | 结果 |
| --- | --- | --- |
| 全部现有脚本回归 | `python3 -B -m unittest discover -s tests -v`；退出码 0；41 个测试，含本轮新增 5 个测试方法及参数子场景。[日志](/tmp/sonic-skill-tests.log) | PASS |
| 独立 CLI 复核 | 独立审查代理通过公开 CLI 验证 21 个场景：14 个字段不匹配、2 个匹配接受、1 个 merge 失效、4 个身份缺失或共同陈旧；21 PASS。见本会话独立复核记录。 | PASS |
| 文档链接与 JSON | 46 份文档，503 个本地链接／锚点、12 个 JSON 块；退出码 0。[结果](/tmp/sonic-skill-doc-check.json) | PASS |
| 可执行示例语法 | 30 个 bash、24 个 sh、92 个 Starlark、5 个 Python 块；shell 使用 `bash -n`，Python/Starlark 使用 Python AST 语法检查。2 个明确缩进属性片段在移除展示缩进后检查；退出码 0。[结果](/tmp/sonic-skill-example-check.json) | PASS |
| 技能结构 | `python3 -B /home/songqing.sq/.agents/skills/.system/skill-creator/scripts/quick_validate.py .`；退出码 0，`Skill is valid!`。 | PASS |
| diff 格式 | `git diff --check`；退出码 0。 | PASS |

台账共 6 项，PASS 6，非 PASS 0。示例语法检查仅验证语法；Starlark 规则解析和构建能力以所选仓库的实际 Bazel 验证为准。

一次性检查涵盖文档、链接、示例及接口比对。新增回归围绕交接契约，验证身份匹配、缺失拒绝、错误证据拒绝及输入变化后的状态失效；更换正确实现仍应满足这些公开 CLI 结果。

兼容性变化：已有完成记录再次更新为 completed/reused 前，须从真实证据补齐三方 inputs。静态依赖收集器仅提供图事实，重新收集的源码／配置身份由调用方核实并补全。
