---
tags: [领域/方法]
---

# 第二轮评审 · 协作体系与文档治理

> **评审视角**：未来协作者 / 三个月后的自己 / 想接手仓库的维护者
> **评审对象**：`github.com/whyao56` 全部 9 个公开仓库（3 旗舰 + 3 学习笔记 + 2 空壳 + 1 应私有库）
> **分析方式**：本地浅克隆（`--depth 1`）**只读静态核对**；未安装依赖、未运行被测程序、未修改任何仓库文件
> **编写**：协作体系与文档治理评审员 collab-docs　｜　日期：2026-10-13
> **口径声明**：所有行号均为实际读到的位置；无法确认的一律标「待确认」，集中在第 5 节。
> **隐私红线**：`Self-Mind` 全程**只统计文件数量与顶层目录名**，未读取、未摘抄其中任何内容。

---

## 0. 一页结论（最该做的 3 件事）

**一句话**：这批仓库的**代码工程质量很高**（第一轮已证），但**协作层是空的**——9 个仓库没有一份 `CONTRIBUTING.md` / `SECURITY.md` / `CODE_OF_CONDUCT.md` / `CODEOWNERS` / ISSUE 模板 / PR 模板 / `.editorconfig`；而**文档不是不够，是太多且各写各的**，同一件事在 README、STATUS、ROADMAP、CHANGELOG、DEVLOG 里各有一个版本，已经开始互相打架。

| 维度 | 现状 | 结论 |
|---|---|---|
| 协作文件覆盖 | ⬜ 0/9 仓库 | 全部缺失，连 GitHub 的一键模板都没用上 |
| 提交/分支规范 | ⬜ 仅存在于 CHANGELOG 的「参照」字样 | 有约定、无强制、无入口文档 |
| ADR（架构决策记录） | 🟡 只有 TideWatch 形似 | 单文件三合一，缺 ADR 标准字段 |
| 文档漂移 | 🟠 **已实际发生** | WingMan `STATUS.md` 头部快照停在 0.1.4，正文却在记 0.2.0 |
| 一键上手（onboarding） | 🟡 2/3 达标 | Etude 无任何一键脚本；TideWatch 仅 Makefile（Windows 需 Git Bash） |
| 文档站 / API 文档 | ⬜ 无 | 无 mkdocs/mdBook；FastAPI 自带 Swagger 一个没链接、一个被关闭 |
| 仓库元数据一致性 | 🟠 TideWatch 描述过度承诺 | 描述写「跨网络舆情分析」，`src/` 里零实现 |

**最该先做的三件事**（本轮新增，不重复第一轮）：

1. 🔴 **给三个旗舰补一套「最小协作基线」**：`CONTRIBUTING.md` + `SECURITY.md` + `.github/ISSUE_TEMPLATE/*` + `.github/PULL_REQUEST_TEMPLATE.md` + `.editorconfig`（本文 2.1/2.2 直接可粘贴）→ 让「怎么贡献、怎么报漏洞、怎么提 PR」有落点。
2. 🟠 **修 WingMan `docs/STATUS.md` 的自相矛盾**：头部快照写死 `0.1.4 / 208 passed`，同一个文件第 408 行却写 `240 passed（0.2.0）`；并把「目录地图」的行号改成脚本生成（本文 2.3）→ 这是当前**唯一已经发作的文档漂移**。
3. 🟡 **把第一轮的「合并学习仓库」方向落成可执行方案**：目标目录结构 + `git subtree` / `git filter-repo` 命令 + README 模板 + 迁移后留链接（本文 2.5，明确标注「第一轮给方向、本条给执行」）。

---

## 1. 现状矩阵（协作文件 × 仓库）

### 1.1 协作文件存在性矩阵（实测）

扫描命令：对每个仓库执行
`find <repo> -not -path "*/.git/*" \( -iname "CONTRIBUTING*" -o -iname "SECURITY*" -o -iname "CODE_OF_CONDUCT*" -o -iname "CODEOWNERS" -o -iname ".editorconfig" -o -iname "devcontainer.json" -o -iname "PULL_REQUEST_TEMPLATE*" -o -iname "ISSUE_TEMPLATE*" -o -iname "Makefile" -o -iname "*.ps1" -o -iname "*.sh" \)`

| 协作构件 | WingMan | Etude | TideWatch | frontend-learning | DSA | Python-Self-Learn | Self-Mind\* |
|---|---|---|---|---|---|---|---|
| `CONTRIBUTING.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `SECURITY.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `CODE_OF_CONDUCT.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `CODEOWNERS` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `.github/ISSUE_TEMPLATE/*` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `.github/PULL_REQUEST_TEMPLATE.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `.editorconfig` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `devcontainer.json` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `.gitattributes` | ✅ 27 行 | ✅ 36 行 | ✅ 25 行 | ❌ | ❌ | ❌ | ❌ |
| `LICENSE` | ✅ MIT | ✅ MIT | ✅ MIT | ❌ | ❌ | ❌ | ❌ |
| `CHANGELOG.md` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 一键/脚本 | ✅ `wingman.cmd`、`scripts/bootstrap.ps1`、`scripts/run_dev.bat`、`scripts/run_dev.sh` | ❌ **无** | 🟡 `Makefile`（Windows 需 Git Bash/WSL） | ❌ | ❌ | ❌ | ❌ |

\* `Self-Mind` 一列仅由**顶层目录名与文件计数**得出（顶层 9 个目录 / 182 个 md / 640 个文件），**未读取任何内容**。

**`.github/` 下的全部内容**（实测）：三个旗舰各自**只有一个 `workflows/ci.yml`**，没有任何 ISSUE/PR 模板、没有 `FUNDING.yml`、没有 `dependabot.yml`。

### 1.2 文档资产清单（三旗舰对比）

| 文档类型 | WingMan | Etude | TideWatch |
|---|---|---|---|
| `README.md` | ✅ 949 行 | ✅ 474 行 | ✅ 340 行 |
| 架构文档 | `docs/ARCHITECTURE.md` 480 行 | `docs/ARCHITECTURE.md` | `docs/architecture.md` 203 行 |
| 设计/决策 | `docs/ENGINE_DESIGN.md` 255 行（散文）+ `docs/PLAN-对象中心迭代.md` 422 行 | 无 | `docs/design-decisions.md` 636 行（D1–D16 / B1–B11 / H1–H5） |
| 现状快照 | `docs/STATUS.md` **880 行** | `docs/STATUS.md` | 无 |
| 路线图 | `docs/ROADMAP.md` 174 行 | 无独立文件（在 README） | 无（README「迭代清单」） |
| 变更记录 | `CHANGELOG.md` + `docs/releases/` 7 篇 | `CHANGELOG.md` + `docs/releases/` 3 篇 | ❌ **无 CHANGELOG、无 releases** |
| 开发日志 | `docs/DEVLOG.md` 269 行 | `docs/DEVLOG.md` | 无（设计决策第二部分承担此职能） |
| 上手 | `docs/QUICKSTART.md` 149 行 | `docs/QUICKSTART.md` | README「快速开始」 |
| 排错 | `docs/TROUBLESHOOTING.md` 761 行 | README「出问题了怎么办」 | 无 |
| 理论/依据 | 无 | `docs/THEORY.md` | `docs/benchmark.md` 70 行 |
| 合规 | `docs/COMPLIANCE.md` 131 行 | 无 | README「合规边界」 |

> **观察**：WingMan 的文档总量最大（`docs/` 合计 **4145 行**），但**越多越容易漂**；TideWatch 的文档最少却最"稳"，因为它把决策和踩坑**一次性写死在 `design-decisions.md`**，不随代码变。

---

## 2. 逐条发现（按 P0 → P2 排序）

> 每条六要素：【现象+证据】【为什么是问题】【改法】【优先级】【工作量】【验收标准】

### P0-1　九个仓库零协作文件，GitHub 的一键能力完全没用上

**现象+证据**：1.1 矩阵显示，9 个仓库**没有任何一个**包含 `CONTRIBUTING.md` / `SECURITY.md` / `CODE_OF_CONDUCT.md` / `CODEOWNERS` / `.github/ISSUE_TEMPLATE/*` / `.github/PULL_REQUEST_TEMPLATE.md` / `.editorconfig` / `devcontainer.json`。三个旗舰的 `.github/` 下**只有** `workflows/ci.yml`。

**为什么是问题**：
- 这三个仓库都**已有一个 fork**（WingMan 显示 `1 fork`），说明有外部人碰过代码，却没有任何「怎么提 PR」的指引；
- 「本地优先、数据不出本机」是这批项目的核心卖点，但**恰恰最需要 `SECURITY.md`** 告诉别人「如果你发现密钥/隐私问题该私密报告而不是开 Issue」——现在没有这个渠道，一旦有人发现隐私问题只能公开开 Issue（反而放大风险）；
- `CODE_OF_CONDUCT` 与 ISSUE/PR 模板是 GitHub 的**内置功能**，建一个文件即可生效，成本极低、收益是「看起来是可以一起干活的项目」。

**改法**：下面给出**可直接粘贴**的最小模板（不是空壳，已按本仓库语境填好）。

`WingMan/CONTRIBUTING.md` / `Etude/CONTRIBUTING.md` / `TideWatch/CONTRIBUTING.md`（三份基本一致，仅把「跑法」换成各自命令）：

```markdown
# 贡献指南

感谢你有兴趣贡献。这个项目**本地优先**，改动前请先读一句总原则：
**不要引入需要联网才能跑通的强依赖**（云端模型/图床必须是可选项）。

## 我能贡献什么

| 类型 | 怎么开始 |
|---|---|
| 报 Bug | 用 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug_report.md)，务必贴上 `--check` 自检输出 |
| 提功能 | 先开 Issue 讨论，避免白写。说明「解决什么问题」而不是「加什么按钮」 |
| 改代码 | 见下方「本地开发」，一个 PR 只做一件事 |
| 改文档 | 直接提 PR。若改了安装步骤，请同步 README 与 docs/QUICKSTART.md |

## 本地开发（三平台）

```bash
git clone https://github.com/whyao56/<repo>.git && cd <repo>
# 三旗舰的跑法各不同，见各自 README「快速开始」
```

## 提交规范

本项目使用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)：
`<type>(<scope>): <subject>`，type ∈ `feat|fix|docs|refactor|test|chore|perf|build|ci`。
示例：`fix(store): 统一在 conn() 里开启 PRAGMA foreign_keys`

- 一个 PR 只做一件事，主体改动尽量 < 400 行；
- 行为变更必须带测试；文档变更不需要；
- **不要**在提交里包含真实密钥、个人邮箱、本机绝对路径。

## 分支模型（单人项目够用版）

- 长期分支只有 `main`；
- 改动走短生命周期分支：`fix/xxx`、`feat/xxx`、`docs/xxx`；
- 合并方式：Squash Merge，PR 标题即最终 commit 主题。

## 我需要遵守的隐私红线

本项目处理的是**用户本机的私密数据**（聊天记录 / 学习记录）。
PR 中**禁止**包含任何真实用户数据、真实导出样本、真实密钥。
测试数据一律用 `samples/` 下的合成数据。
```

`WingMan/SECURITY.md` / `Etude/SECURITY.md` / `TideWatch/SECURITY.md`：

```markdown
# 安全策略

## 支持范围

只有 `main` 分支的最新版本接受安全修复。旧版本请在 Issue 里说明。

## 私下报告漏洞（不要开公开 Issue）

请通过 GitHub 的 **[Security Advisories](https://github.com/whyao56/<repo>/security/advisories/new)**
私下提交，或邮件联系维护者。**不要**在公开 Issue 里贴出漏洞细节、密钥、或任何真实用户数据。

## 我关心哪一类问题（按优先级）

1. **隐私边界被突破**：程序把本机数据（聊天记录 / 学习记录 / 密钥）外发到了配置之外的地址；
2. **密钥落盘或泄漏**：密钥出现在日志、自检报告、错误响应体、或仓库文件里；
3. **路径穿越 / 任意文件读写**：本地服务接口被构造请求读写预期外的文件；
4. **依赖供应链**：引入的依赖存在已知高危漏洞。

## 明确不属于漏洞

- 本工具**只读**用户自己机器上的数据库、**不绕过任何权限**（见 docs/COMPLIANCE.md）——这是设计，不是缺陷；
- 默认的 Mock / 演示引擎输出质量不高——这是已知取舍，见 docs/STATUS.md；
- 需要用户主动把自己的密钥和私密数据贴出来的「漏洞」。

## 我会怎么做

确认有效后我会：修复 → 在 CHANGELOG 的「安全」一节记录（不披露细节）→ 在 Release 说明里致谢（你可以选择匿名）。
```

`.github/ISSUE_TEMPLATE/bug_report.md`：

```markdown
---
name: Bug 报告
about: 报告一个可复现的问题
title: "[Bug] "
labels: bug
---

## 环境
- 系统：Windows 10/11 版本号
- 程序版本：（界面左下角或 `--version`）
- 安装方式：源码 / 打包版

## 自检输出（必填）
<!-- 源码路线：<repo> --doctor（WingMan）/ Etude.exe --check；打包版同理 -->

## 复现步骤
1.
2.

## 期望行为 / 实际行为

## 日志
<!-- 数据目录下的 logs/ 里对应文件；贴之前请确认没有密钥 -->
```

`.github/ISSUE_TEMPLATE/config.yml`（把「提问」引导到 Discussions，减少噪音）：

```yaml
blank_issues_enabled: false
contact_links:
  - name: 使用问题 / 提问
    url: https://github.com/whyao56/<repo>/discussions
    about: 使用、配置、接模型的问题请走 Discussions，不要开 Issue
```

`.github/PULL_REQUEST_TEMPLATE.md`：

```markdown
## 这个 PR 做了什么

## 为什么（关联 Issue）

## 自查
- [ ] 本地测试全绿
- [ ] 行为变更带了测试
- [ ] 未包含真实密钥 / 个人邮箱 / 本机绝对路径
- [ ] 若改了安装步骤，已同步 README / QUICKSTART

## 截图 / 输出（UI 改动必填）
```

`.editorconfig`（三旗舰通用，与已有 `.gitattributes` 互补：`.gitattributes` 管 Git 存取，`.editorconfig` 管编辑器即时行为）：

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.{md,yml,yaml,json}]
indent_size = 2

[*.py]
indent_size = 4

[*.{cmd,bat,ps1}]
end_of_line = crlf
```

**优先级**：P0　｜　**工作量**：约 2 小时（三仓库 × 7 个文件，直接粘贴）
**验收标准**：①三旗舰根目录出现 `CONTRIBUTING.md` / `SECURITY.md` / `.editorconfig`，`.github/` 下出现 3 个模板文件；②GitHub 仓库页「Issues → New issue」出现模板选择；③Security 标签页出现「Report a vulnerability」入口。

---

### P0-2　`SECURITY.md` 缺失，与「本地优先 / 隐私边界」定位直接冲突

**现象+证据**：三个旗舰都在 README 反复强调隐私（WingMan `README.md:207` 明确标注「验证过的环境」与数据边界，`docs/COMPLIANCE.md` 131 行专讲红线；Etude `docs/QUICKSTART.md` 写明密钥存在 `%LOCALAPPDATA%` 仓库外），但**没有任何一份文件告诉外部人如何私下报告安全问题**（1.1 矩阵全 ❌）。

**为什么是问题**：这是**叙事与机制脱节**——你花大力气在 README 里证明「我重视隐私」，却没有给愿意帮你守护隐私的人一个**私密报告入口**。对外部研究者来说，「没有 SECURITY.md」等同于「这个项目没想过安全披露」。

**改法**：见 P0-1 的 `SECURITY.md` 模板（已按本仓库的四类真实风险定制）。另建议在 GitHub 仓库设置里开启 **Private vulnerability reporting**（Settings → Security → Private vulnerability reporting → Enable）。

**优先级**：P0　｜　**工作量**：30 分钟（模板 20 分钟 + 三仓库设置 10 分钟）
**验收标准**：三旗舰 Security 页面出现可点击的「Report a vulnerability」。

---

### P0-3　WingMan `docs/STATUS.md` 自相矛盾：头部快照停在 0.1.4，正文已记到 0.2.0

**现象+证据**（同一文件内互相打架）：

| 位置 | 原文 | 与代码/CHANGELOG 对照 |
|---|---|---|
| `WingMan/docs/STATUS.md:4` | 「**快照**：2026-10-06 18:00，版本 `0.1.4`，全量 **208 passed + 1 skipped**」 | 与 `CHANGELOG.md` 的 `[0.2.0]` 节、`README.md:190`「当前版本：v0.2.0」**冲突** |
| `WingMan/docs/STATUS.md:408` | 「# 240 passed, 1 skipped（0.2.0）」 | 说明正文其实已升到 0.2.0 |
| `WingMan/docs/STATUS.md:410 / 427 / 456` | 分别记录「0.1.5 新增/扩写的守卫」「0.2.0 新增的守卫」 | 头部却仍写 0.1.4 |
| `WingMan/docs/STATUS.md:59` | 「tests/ **19 个测试文件**，全量 208 passed + 1 skipped（0.1.4）」 | 实测 `ls WingMan/backend/tests/*.py \| wc -l` = **21** |
| `WingMan/docs/STATUS.md:35` | 「store.py **1877**」 | 实测 `wc -l WingMan/backend/app/store.py` = **1940** |
| `WingMan/docs/STATUS.md:31` | 「main.py **209**」 | 实测 `wc -l WingMan/backend/app/main.py` = **247** |
| `WingMan/docs/STATUS.md:62` | 「frontend/index.html **4653**」 | 实测 = 4653 ✅（这一行是对的） |

**为什么是问题**：`STATUS.md` 的自我定位是「给全新上下文的窗口看的一份现状底稿，读完不用再通读代码就能动手改」（`STATUS.md:3`）。**一旦它的版本号和行号不可信，它就从资产变成了负债**——新窗口（包括未来的 AI 助手）会更相信文档而不是代码，于是拿着 1877 行的地图去改 1940 行的文件，第一句就错。文件本身在第 5 行也承认「文件行号会随改动漂移」，但**承认问题不等于解决问题**。

**改法**：把 `STATUS.md` 拆成「人写的叙述」+「机器生成的事实」两半。
1. 头部快照改为**只保留日期 + 探测命令**，不写死版本与测试数：

```markdown
> **现状底稿**：给全新上下文的窗口读。
> 快照由 `python scripts/gen_status.py` 生成（版本、测试数、文件行号一律自动取）。
> 人工只需维护下面的「现状叙述」。
```

2. 新增 `WingMan/scripts/gen_status.py`（骨架，纯只读）：

```python
"""生成 docs/STATUS.md 里的事实块（版本 / 测试数 / 关键文件行号）。
用法：python scripts/gen_status.py --check   # CI 用，发现过期则 exit 1
      python scripts/gen_status.py --write   # 本地刷新
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = [  # 想盯住的文件都在这里声明
    "backend/app/store.py", "backend/app/main.py",
    "backend/app/collect/reader.py", "frontend/index.html",
    "scripts/preflight.py",
]

def git_lines(rel: str) -> int:
    out = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                         cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        return 0
    return len((ROOT / rel).read_text(encoding="utf-8", errors="replace").splitlines())

def app_version() -> str:
    txt = (ROOT / "backend/app/__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', txt)
    return m.group(1) if m else "?"

if __name__ == "__main__":
    print(f"version: {app_version()}")
    for rel in WATCH:
        print(f"{rel}: {git_lines(rel)} 行")
```

3. 把 `STATUS.md` 的「目录地图」整块换成**占位标记**，由脚本注入：

```markdown
<!-- STATUS:FACTS:BEGIN -->
（此块由 scripts/gen_status.py 生成，请勿手改）
<!-- STATUS:FACTS:END -->
```

**优先级**：P0　｜　**工作量**：半天（写脚本 + 改写 STATUS 头部与地图）
**验收标准**：①`python scripts/gen_status.py --check` 在事实块过期时返回非零；②`STATUS.md` 头部不再出现手写的版本号/测试数；③CI 增加一步运行 `--check`。

---

### P0-4　TideWatch 的 GitHub 描述**过度承诺**了代码里不存在的功能

**现象+证据**：
- GitHub 仓库页实测描述：「TideWatch · 观潮：可解释、可插拔、可迭代的网络水军与协同行为识别**与跨网络舆情分析**引擎 | Explainable, pluggable, iterative engine for CIB detection **and cross-network public opinion analysis**.」
- 但代码与文档里**搜不到任何对应实现或表述**：对 `TideWatch/src`、`eval`、`configs`、`README.md` 执行
  `grep -rniE "舆情|跨网络|cross-network|public.opinion"` → **零命中**。
- 对照 `TideWatch/pyproject.toml:7` 的项目描述只有「可解释、可插拔、可迭代的网络水军与协同行为识别引擎」，**没有「跨网络舆情分析」**；`README.md:3` 的标题也只有「TideWatch · 观潮」+「网络水军与协同行为识别引擎」。

**为什么是问题**：这是**和 WingMan 的 `whisper`/`asr` 同类型的错误**（第一轮已点名 WingMan 的 topics 过期），只是发生在另一个仓库、且**更严重**——WingMan 是「删了功能没改元数据」，TideWatch 是「**加了一个从没做过的功能**」。对懂行的访客，「跨网络舆情分析」意味着多平台数据归并、跨源实体对齐、舆情演化建模——`src/` 里 12 个模块完全没有承载这些的代码。一旦有人冲着这个描述点进来，会立刻判定作者**夸大**，这比「没写」伤得多。

**改法**：二选一，我建议 A。
- **A（推荐，5 分钟）**：把 GitHub 描述改回与 `pyproject.toml:7` 一致 —— 删掉「与跨网络舆情分析」「and cross-network public opinion analysis」，只留引擎本身。若确实想保留「舆情」这个词，改成**已有事实**的表述，例如「可解释的中文水军识别引擎，可用于舆情分析场景」——注意是「可用于」而非「是…引擎」。
- **B（若真想保留）**：把「跨网络舆情分析」写进 `docs/design-decisions.md` 的「待验证的假设」（该文件已有 H1–H5 段），并明确它是**路线图**而非**现状**。

**优先级**：P0（对外自我打脸）　｜　**工作量**：5 分钟
**验收标准**：GitHub 描述、`pyproject.toml:7`、`README.md` 三处对「这个项目是什么」的说法**互相一致**。

---

### P0-5　学习仓库合并：从「方向」到「可执行方案」

> **定位声明（必读）**：合并为 `dev-notes` 这个**方向**由**第一轮**提出（`portfolio-review.md` 2.2 / 5.2 第 3 条、主报告 6.2）。**本条不声称是新发现**；本条的增量是**把它落成可执行方案**：目标目录结构、两种迁移命令（保历史 / 不保历史）、README 模板、迁移后如何留链接、以及合并后**不变成垃圾场**的维护规则。

**现象+证据**（本轮实测三个学习仓库的组织方式）：

| 仓库 | 文件数（非 .git） | 组织方式 | README | LICENSE | 命名特征 |
|---|---|---|---|---|---|
| `frontend-learning` | 25 | 扁平，19 个 `01–19` 前缀的 HTML + `css/` | ❌ | ❌ | 序号前缀 |
| `Data-Structures-and-Algorithms` | 24 | 扁平，21 个 `01–21` 前缀的 `.py` + `test.py`、`todo_manager.py` | ❌ | ❌ | 序号前缀 |
| `Python-Self-Learn` | 47 | 扁平，38 个 `练习01–38.py` + 7 个数据/文本文件 | ❌ | ❌ | 「练习」前缀 |

**三个仓库高度同构**：都是「序号 + 主题」的扁平堆积、都无 README / LICENSE、描述都用同一句模板（`DeepSeek V4.x 指导学习…`）。**合并在技术上没有障碍**（无构建系统、无互相 import），障碍只在「怎么保住历史」和「怎么不变成一个更大的扁平堆积」。

**改法（可执行）**：

**第 1 步：确定目标结构**（在三仓库**之外**新建空仓库 `dev-notes`）：

```
dev-notes/
├── README.md                 # 学习路线图 + 时间线 + 「学了→用在哪」对照表
├── CONTRIBUTING.md           # 一份「我自己怎么记笔记」的约定（防垃圾场，见第 4 步）
├── LICENSE                   # MIT（笔记也可授权）
├── .gitignore                # 统一一份
├── .editorconfig             # 复用 P0-1 的模板
├── 01-python/                # ← 原 Python-Self-Learn（38 个练习 + 数据文件）
├── 02-dsa/                   # ← 原 Data-Structures-and-Algorithms
├── 03-frontend/              # ← 原 frontend-learning
└── 99-scratch/               # 明确标注「随手写的，不保证质量」的收容区
```

> **为什么留一个 `99-scratch/`**：三个仓库里已经混着 `test.py`、`todo_manager.py`、`data_temp.csv`、`note.txt`、`poem.txt` 这类**既不是笔记也不是练习**的文件（实测存在于 `Data-Structures-and-Algorithms/` 与 `Python-Self-Learn/` 根目录）。与其假装它们不存在，不如给它们一个**显式的、低期望的**位置——这是避免「整个仓库都是垃圾场」的最便宜办法。

**第 2 步：迁移（二选一）**

**方案 A —— `git subtree`，保留各仓库完整历史（推荐）**

```bash
# 0. 新建空仓库 dev-notes（GitHub 上建，克隆到本地）
git clone https://github.com/whyao56/dev-notes.git && cd dev-notes
git checkout -b init

# 1. 逐个把旧仓库作为 subtree 拉进来，前缀即目标目录
git remote add py   https://github.com/whyao56/Python-Self-Learn.git
git fetch py --depth=1                 # 若不需要历史，depth=1 即可
git subtree add --prefix=01-python py main --squash

git remote add dsa  https://github.com/whyao56/Data-Structures-and-Algorithms.git
git fetch dsa --depth=1
git subtree add --prefix=02-dsa dsa main --squash

git remote add fe   https://github.com/whyao56/frontend-learning.git
git fetch fe --depth=1
git subtree add --prefix=03-frontend fe main --squash

# 2. 收尾：删掉三个临时 remote
git remote remove py dsa fe

# 3. 首次提交 + 推送
git add -A && git commit -m "chore: 初始化 dev-notes（合并三个学习仓库）"
git push -u origin init
```

> **`--squash` 的取舍**：`--squash` 会把每个旧仓库压成**一个** commit（历史最简、日志最干净）；去掉 `--squash` 则保留全部原始 commit（可 `git log --follow` 追溯单文件历史，但会让 3 个「序号连发」的提交灌进新仓库）。**对本例建议用 `--squash`**——这些笔记仓库的历史本来就是「一天写几个练习」的密集提交，保留它没有阅读价值，反而稀释了未来真正的提交。

**方案 B —— `git filter-repo`，把三个仓库的历史压进一个仓库（保留提交时间线）**

前提：`pip install git-filter-repo`（**注意：本评审禁止安装依赖，此处仅为给你本地执行用的指令，我未执行**）。

```bash
# 以体量最大的 Python-Self-Learn 为基底
git clone https://github.com/whyao56/Python-Self-Learn.git dev-notes && cd dev-notes

# 把它的顶层文件整体挪进 01-python/
git filter-repo --to-subdirectory-filter 01-python

# 再把另两个仓库的历史并进来（各自先挪进对应子目录）
git clone https://github.com/whyao56/Data-Structures-and-Algorithms.git dsa
git -C dsa filter-repo --to-subdirectory-filter 02-dsa

git clone https://github.com/whyao56/frontend-learning.git fe
git -C fe filter-repo --to-subdirectory-filter 03-frontend

cd dev-notes
git remote add dsa ../dsa && git fetch dsa
git remote add fe  ../fe  && git fetch fe
git merge --allow-unrelated-histories dsa/main fe/main -m "chore: 合并 DSA 与前端笔记"
```

> **风险提示**：`filter-repo` 会**改写全部 commit hash**。如果三个旧仓库要**归档（Archive）而非删除**，用方案 A 更稳；只有当你想「新仓库能一路 `git log` 追到第一条练习」时才用方案 B。

**第 3 步：迁移后留链接**（否则等于把旧仓库「藏起来」）
1. 三个旧仓库**不删**，改为 **Archive**；2. 各建一个 `README.md` 只写一段：

```markdown
> ⚠️ 本仓库已归档，内容与历史已并入 **[dev-notes](https://github.com/whyao56/dev-notes)** 的 `01-python/`。这里保留只读快照，不再更新。
```

**第 4 步：`dev-notes/README.md` 模板**（核心是一张「学了 → 用在哪」对照表，把笔记和三个旗舰挂起来）

```markdown
# dev-notes · 学习轨迹

不是「我学过的清单」，是「**学到的东西最后长成了什么**」。

## 学了 → 用在哪
| 笔记 | 学到的东西 | 用在了哪 |
|---|---|---|
| `01-python/练习20.py`（路径与文件 IO） | 路径处理、文件读写 | WingMan 的 `collect/reader.py` 认列逻辑 |
| `01-python/练习31.py`（异常处理） | try/except 边界 | Etude 的 `--check` 自检三档结论 |
| `02-dsa/07二叉树.py` | 树的遍历 | TideWatch 的共现图谱剪枝思路 |
| `03-frontend/14flex布局.html` | Flex 布局 | WingMan / Etude 单文件前端 |

## 时间线
2026-08~09 Python 基础（练习 01–38）｜2026-09 数据结构与算法（01–21）｜2026-10 Web 前端（01–19）

## 还没学什么（诚实清单）
并发模型、测试框架原理、HTTP 协议细节；`02-dsa` 的算法只做到「会写」，没做复杂度实测。

## 约定
见 [CONTRIBUTING.md](CONTRIBUTING.md)。一句话：**能跑通 ≥ 能讲清 ≥ 记了笔记**，三者缺一的文件放 `99-scratch/`。
```

**第 5 步：`dev-notes/CONTRIBUTING.md`（防垃圾场规则——本条增量核心）**

```markdown
# 我自己写笔记的约定

这个仓库是给我自己看的，但既然公开，就定三条硬规矩，防止它变成「什么都往里扔」的扁平堆积：
1. **每个顶层目录必须有 README**（这一科在学什么、学到哪、还差什么），没有的不允许存在。
2. **文件名一律 `<序号>-<主题>.<ext>`**；禁止 `test.py` / `tmp.py` / `副本.py`——它们只能进 `99-scratch/`。
3. **提交信息说人话**：`<topic>: <做了什么>`（如 `dsa: 补 20动态规划`），禁止 `更新`、`修改`、`1`。

## 每月一次的「除锈」
删掉 `99-scratch/` 里 30 天没动又没有复用价值的文件；检查各目录 README 是否还准确；
把已「用在哪」的笔记在 README 对照表里补一条回链。
```

**优先级**：P0（第一轮已定方向，本轮给执行，属于「可立刻动手」）
**工作量**：
- 步骤 1/3/4/5（结构与文档）：约 2 小时；
- 步骤 2 迁移（方案 A）：约 20 分钟；方案 B 约 1 小时。
**验收标准**：①`dev-notes` 存在且三个子目录内容完整；②三个旧仓库已 Archive 且各自 README 指向 `dev-notes`；③`dev-notes/README.md` 的「学了 → 用在哪」表**至少 4 条**能真实对应到旗舰模块；④仓库总数由 9 降到 ≤ 7（第一轮目标）。

---

### P1-1　三旗舰都没有 `pre-commit`，也没有任何提交信息校验

> ⚠️ 与第一轮的边界：第一轮已提「三项目加 pre-commit」作为覆盖率工程的一部分（主报告 5.3 W3）。**本条的增量**是把它落到**模板与命令**层面（Windows 可跑的 `commit-msg` hook + CI 校验），且**专指提交信息规范**，不是覆盖率。

**现象+证据**：
- `find WingMan Etude TideWatch -name ".pre-commit-config.yaml"` → **零命中**；
- 对三仓库全量文本 `grep -liE "commitlint|commitizen|husky|conventional|commit-msg"` → **零命中**；
- 三个 `ci.yml` 里 `grep -niE "commit-msg|conventional|check.*commit"` → **零命中**；
- 但 CHANGELOG 又明确声明了规范：`WingMan/CHANGELOG.md:3-4`「格式参照 Keep a Changelog，版本号遵循语义化版本」；`Etude/CHANGELOG.md:4-5` 同样。

**为什么是问题**：**规范写在了 CHANGELOG 里，却没有任何地方约束「提交信息」**。CHANGELOG 是人工维护的，与 commit message 是两条独立的线——也就是说，现在的状态是「有 SemVer 的**结果**，没有 SemVer 的**过程**」。对一个已经用 Keep a Changelog + SemVer 的项目，**提交信息不规范会让「下一版 CHANGELOG 该归到 Added 还是 Fixed」变成人工再判断一遍**，这正是该自动化掉的部分。

> **诚实标注待确认**：本地为 `--depth 1` 浅克隆（`git rev-list --count HEAD` 在三旗舰均返回 `1`），**无法读取真实提交历史**，故「当前提交风格是否一致」**无法核实**，列入第 5 节。下面的建议按「尚未规范」处理，若实际已一致则成本更低。

**改法**：

1. `.pre-commit-config.yaml`（三旗舰通用；本项目是 Python + 单文件前端，不需要 node 工具链）：

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
      - id: mixed-line-ending
        args: [--fix=lf]
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.4.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, refactor, test, chore, perf, build, ci]
```

> `conventional-pre-commit` 是**纯 Python**，Windows 上可直接跑，无需 Node——这是选它而不是 `commitlint`（需要 npm）的原因。
> **注意**：本评审禁止安装依赖，以上配置**未实际运行验证**，语义依据其官方文档；落地时请先 `pre-commit run --all-files` 试跑一次。

2. 本地安装（写进 `CONTRIBUTING.md` 的「本地开发」）：

```bash
pip install pre-commit
pre-commit install            # 装 pre-commit 钩子
pre-commit install --hook-type commit-msg   # 额外装 commit-msg 钩子
```

3. CI 兜底（防止有人 `--no-verify` 绕过）。在 `.github/workflows/ci.yml` 增加一个 job：

```yaml
  commit-lint:
    name: 提交信息规范
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }     # 必须取全历史才能逐条校验
      - name: 校验 PR 内每个 commit
        uses: webiny/action-conventional-commits@v1.3.0
```

**优先级**：P1　｜　**工作量**：2 小时（含一次试跑）
**验收标准**：①本地提交一条 `update` 被拒绝，`fix(x): ...` 通过；②PR 里出现不合规 commit 时 CI 变红。

---

### P1-2　ADR 缺位，且唯一形似 ADR 的文件「三合一」了

**现象+证据**：核实了三份「设计类」文档的**形式**：

| 文件 | 行数 | 形式核实 | 结论 |
|---|---|---|---|
| `TideWatch/docs/design-decisions.md` | 636 | 章节结构为：第一部分 设计取舍（**D1–D16**，每条含「背景 / 备选 / 决定 / 理由 / 代价」）→ 第二部分 踩坑记录（**B1–B11**：症状 / 根因 / 怎么修 / 哪条测试守着）→ 第三部分 待验证的假设（**H1–H5**）→ 附：实验记录索引 | **最接近 ADR，但是单片三合一** |
| `WingMan/docs/ENGINE_DESIGN.md` | 255 | 标题「参谋引擎设计」，正文是「一、记忆的三种粒度 / 二、分析器 Analyzer…」的**散文式**论述 | **不是 ADR**（无备选、无代价、无状态） |
| `WingMan/docs/PLAN-对象中心迭代.md` | 422 | 从文件名与结构看是**前向计划**（「要改成什么样」） | **不是 ADR**（是 PLAN，`STATUS.md:6` 已明确二者分工） |
| `Etude/docs/` | — | 只有 ARCHITECTURE / DEVLOG / QUICKSTART / STATUS / THEORY | **无任何决策记录文件** |

**为什么是问题**：
- **TideWatch 的问题**：`design-decisions.md` 内容质量极高（D1–D16 每条都有「备选」和「代价」，B1–B11 每条都能指到守它的那条测试），但**把三种生命周期完全不同的内容塞进一个文件**——「设计取舍」一旦定稿就**不该改**，「踩坑记录」是**只增不改**，「待验证假设」是**待办会变**。它们混在一起导致：①无法逐条标记状态（已采纳 / 已废弃 / 被取代）；②文件只会越来越长，读者找不到重点；③没有 `Status` / `Date` / `Decision-makers` 这些 ADR 标准字段，无法回答「这个决定现在还算数吗」。
- **WingMan 的问题**：`ENGINE_DESIGN.md` 讲了「怎么做」，但没讲「**为什么不做别的**」。第一轮已确认 WingMan 有若干结构性技术债（巨型文件、无迁移机制），而**恰恰是这类项目最需要 ADR**——因为「为什么当初把 13 张表塞进一个 `store.py`」这个问题的答案，直接决定重构时该拆哪里。
- **Etude 的问题**：`docs/THEORY.md` 承担了「理论→代码映射」，是**理论依据**而非**工程决策**。Etude 有一批很值得记录的决策（例如「为什么打包不进 CI」「为什么 `docs_url=None`」，见 P1-5 / P2-1）现在**没有任何地方记录**。

**改法**：
1. **统一命名约定**：`docs/adr/NNNN-<短横线标题>.md`，编号四位补零、单调递增、**永不复用**（即使某条被废弃）。
2. **ADR 模板**（`docs/adr/template.md`）：

```markdown
# NNNN. <一句话标题：做了什么决定>

- **状态**：提议 / 已采纳 / 已废弃 / 被 NNNN 取代
- **日期**：YYYY-MM-DD
- **决策人**：<名字>

## 背景
我们面对什么问题？有哪些硬约束（性能、隐私、成本、跨平台）？

## 备选方案
- A. …（优点 / 缺点）
- B. …
- C. …

## 决定
选 X。一句话说清选了什么。

## 后果
- 好处：…
- 代价：…（明确写下「接受了什么坏的」——这一节比好处更重要）
- 什么情况下该重新考虑这个决定：…

## 相关
- 守护它的测试：`tests/test_xxx.py::test_yyy`
- 相关代码：`app/xxx.py:NN`
```

3. **TideWatch 迁移（保守，不重写历史内容）**：
   - **保留** `design-decisions.md` 作为「**索引 + 叙事**」，但把它**切分为三个文件**：`docs/adr/`（把 D1–D16 逐条搬成 ADR 文件，编号 0001–0016，补上 `状态` / `日期` 字段）、`docs/pitfalls.md`（B1–B11 原样搬，**只增不改**）、`docs/hypotheses.md`（H1–H5，可勾选/关闭）；
   - `design-decisions.md` 本身**不删**，改成薄索引（每段一行链接 + 一句话），保住已有外链。
   - 至少**先把 D14（配置三级覆盖 + 配置指纹）、D15（不拿合成数据当性能背书）、D16（为什么删掉 `window_slices()`）三条**转成标准 ADR——这三条是读者最需要「为什么」的地方。
4. **WingMan 补三条 ADR**（针对第一轮点名的技术债，把「为什么当初这样」补上）：`store.py` 单类集中（重构前必须先写清）、无 schema 迁移机制的历史原因、`routes_persons.py` 前端未消费的缘由。
5. **Etude 起一个 `docs/adr/`**，首条建议记录「为什么打包与发布不进 CI」（`Etude/.github/workflows/ci.yml` 的 `clean-install` job 注释已给出理由，把它正规化成 ADR 即可，作者已经想清楚了，只差归档形式）。

**优先级**：P1　｜　**工作量**：TideWatch 迁移 半天；WingMan/Etude 各补 3–5 条 半天
**验收标准**：①三旗舰各自存在 `docs/adr/` 且首条 ADR 含状态/日期/备选/代价四要素；②TideWatch 至少 3 条 D 系列转成标准 ADR，且旧文件保留可访问；③每条 ADR 的「相关 → 守护它的测试」指向真实存在的测试函数。

---

### P1-3　文档漂移的**结构性风险**：五类文档信息重叠，职责未定义

**现象+证据**（以 WingMan 为例，同一件事在五处出现）：

| 信息 | README | STATUS.md | ROADMAP.md | CHANGELOG.md | DEVLOG.md |
|---|---|---|---|---|---|
| 当前版本号 | `README.md:190`「v0.2.0」 | `STATUS.md:4`「0.1.4」❌ | 阶段表里嵌 0.1.4/0.1.5/0.2.0 | `[0.2.0]` 节 | 版本一览表 |
| 「哪些没做」 | 「⏸️ 已撤下 / ⬜ 尚未实现」行 | §10 缺口表 | 阶段 1/2 的 ⬜ 项 | — | 每版「踩到什么」 |
| 测试数量 | — | `STATUS.md:4`「208」/`:59`「208」/`:408`「240」❌ | — | — | — |
| 下一步做什么 | 指向 ROADMAP | §「要改成什么样」指向 PLAN | 全文 | `[Unreleased]` 节 | — |
| 按钮/功能名 | 「4 个页签」 | 「4 个一级页签」+ 行号 | — | 修复条目描述 | 叙述 |

**为什么是问题**：
1. **同一条信息有 3–5 个副本，必然漂移**——WingMan 的版本号已经在 `STATUS.md` 内部打架（P0-3 已证）；
2. **没有「谁是权威源」的定义**：想知道「现在版本多少」，`README.md:190` 说 0.2.0、`STATUS.md:4` 说 0.1.4，读者无从判断该信谁；
3. **两类信息被写进了同一批文件**：`CHANGELOG.md` 是 **append-only（永不改历史）**，`STATUS.md` 是 **overwrite（每次全量重写）**——它们对「可维护性」的要求完全相反。把「当前状态」和「历史变更」混着写，就是在给未来的自己埋坑；
4. **`STATUS.md` 里连行号都写进去了**（`STATUS.md:62` 的 4653 这次碰巧对，`:35` 的 1877 已经错了）——凡是**能被代码自动推导的事实**都不该手写。

**改法**：确立「哪类信息该放在哪」的分工原则（**这是本条的核心产出**）：

| 文档 | 回答的问题 | 生命周期 | 谁写 | 权威性 |
|---|---|---|---|---|
| `README.md` | 这是什么 / 怎么跑起来 / 长什么样 | 低频精修 | 人 | 访客眼中的**唯一真相** |
| `CHANGELOG.md` | **变了什么**（面向使用者） | **只增不改** | 人（可由 commit 辅助） | 版本变更的**唯一真相** |
| `docs/DEVLOG.md` | **为什么变**、怎么发现、怎么验证 | **只增不改** | 人 | 过程叙事的唯一真相 |
| `docs/ADR/` | **为什么这么设计**（含备选与代价） | 定稿后不改，可被取代 | 人 | 设计决策的唯一真相 |
| `docs/STATUS.md` | **现在是什么样**（含版本/测试数/文件行号） | **每次全量重写** | **脚本生成事实块 + 人写叙述** | 无独立权威性，是 README 的**展开视图** |
| `docs/ROADMAP.md` | **要做什么**（含未完成项） | 高频更新 | 人 | 计划，**不承诺** |
| `docs/QUICKSTART.md` | 10 分钟内跑起来 | 随环境变 | 人 | 与 README 安装段**必须同步** |

**减少漂移的机制（三条，按性价比排序）**：

1. **能自动推导的，一律不手写**：版本号（`backend/app/__init__.py` 的 `__version__`）、测试数、文件行号、目录树 —— 全部由 `scripts/gen_status.py`（P0-3 已给骨架）生成，CI 加一步 `--check` 拦截过期提交。
2. **单一真相 + 单向引用**：README 不复制 CHANGELOG 的内容，只**指向**它（WingMan 现在做得对：`README.md:190` 写「变更记录见 CHANGELOG.md」）；反过来 `STATUS.md` 不重复 README 的功能清单，只**展开**它并标明「详见 README §x」。
3. **明确「必须同步」的清单**：在 `CONTRIBUTING.md` 里写死——「改安装步骤 → 同步 `README.md` + `docs/QUICKSTART.md`；改数据目录 / 环境变量 → 同步 `README.md` + `docs/TROUBLESHOOTING.md`；改已知限制 → 同步 `README.md` 与 `docs/STATUS.md`」。

**优先级**：P1　｜　**工作量**：分工原则落地（写进 CONTRIBUTING + 改 `STATUS.md` 头部）约 2 小时；脚本机制见 P0-3。
**验收标准**：①`STATUS.md` 头部不再手写版本/测试数；②`README.md` 与 `docs/QUICKSTART.md` 的「前置条件」一行**字面一致**；③同一版本号在仓库内**只有一个手写来源**。

---

### P1-4　开发环境重建：Etude 缺一键脚本，TideWatch 的 Makefile 对 Windows 不友好

**现象+证据**（静态核对 `README.md` / `docs/QUICKSTART.md` / `docs/DESKTOP.md`）：

| 环节 | WingMan | Etude | TideWatch |
|---|---|---|---|
| 一键脚本 | ✅ `wingman.cmd`（首次自动建 venv + 装依赖 + 自检 + 启动）；另有 `scripts/bootstrap.ps1`、`scripts/run_dev.bat`、`scripts/run_dev.sh` | ❌ `Etude/scripts/` 下只有 `build_exe.py` / `check_js.py` / `e2e_check.py` / `openai_stub.py` / `make_release.py` / `products.py` / `screenshots.js` / `ui_smoke.js` / `cdp.js`，**无任何启动或建环境脚本** | 🟡 仅 `Makefile`（`init` / `test` / `demo`） |
| README 里的装法 | 三种（一键 / exe / 手动 `uvicorn`）`README.md:97` | 两种（exe / 手动），手动需**手敲 5 条命令**（`docs/QUICKSTART.md` 方式 B：`python -m venv` → `activate` → `pip install -r requirements.txt` → `python run_etude.py`） | `pip install -e ".[zh]"` → `python scripts/gen_sample.py` → `tidewatch scan …`（`README.md:64-70`） |
| Python 版本声明 | ✅ `README.md:60`「Python 3.11+」；`QUICKSTART.md:5` 同 | 🟠 **README 未写任何 Python 版本**（`grep -nE "Python\|3\.1[0-9]" Etude/README.md` 只命中「不用装 Python」）；`QUICKSTART.md:13` 表格里才写「Python 3.10+」 | ✅ `pyproject.toml:8` `requires-python = ">=3.10"`；README 徽章写 `3.10\|3.11\|3.12\|3.13` |
| 干净机器上的卡点 | Python 版本（`README.md:60`）、WebView2（仅 `docs/DESKTOP.md` 提） | **①无一键脚本**；**②Python 版本声明与 CI 不一致**（见下）；**③WebView2**（`QUICKSTART.md`「需要 WebView2，Win10 1803+ 通常自带」——「通常」是无法验证的措辞）；**④`edge-tts` 必须联网**（`Etude/backend/requirements.txt` 注释承认） | **①Windows 上 `make` 默认不存在**（`Makefile` 头部自述「Windows 上建议在 Git Bash 或 WSL 里执行」）；**②无 `setup.ps1`** |

**为什么是问题**：
- **Etude 的 Python 版本声明不一致**：`docs/QUICKSTART.md:13` 说 3.10+，但 `Etude/.github/workflows/ci.yml:21` 的矩阵是 `python: ["3.11", "3.12"]` —— **3.10 从未被 CI 验证过**。这正是第一轮给 WingMan 指出的那个坑（宣称支持但没测），在 Etude 换了个形式复现：**宣称支持 3.10，却只测 3.11/3.12**。要么把 CI 矩阵加 `"3.10"`，要么把声明改成 3.11+。
- **Etude 的 onboarding 是这个账号里最长的**：三个旗舰里只有它**要求用户手敲 5 条命令**才能从源码跑起来，而它偏偏又是「想改代码的人」（`QUICKSTART.md:13` 方式 B）最可能用到的路径。
- **TideWatch 的 `make demo` 是很好的设计**（`Makefile` 注释：「别人 clone 下来第一件事就是 `make demo`，不该先读三页文档」），但**Windows 上的用户体验是断的**——`WingMan` 是 Windows 桌面程序、作者本人就在 Windows 开发，`TideWatch` 却只提供了 Unix 风格的入口。

**改法**：

1. **Etude 补 `backend/setup.ps1`**（Windows 一键骨架；语义参照 WingMan 的 `wingman.cmd`）：

```powershell
# Etude 一键环境准备 + 启动骨架（Windows PowerShell）
# 语义：幂等（venv 已存在不重建）、失败不留半成品、结束说清下一步。
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv"

# [1/4] 检查 Python 版本（需 >=3.11，与 CI 一致）
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "找不到 python，请安装并勾选 Add to PATH" }
$ver = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if ([version]$ver -lt [version]"3.11") { throw "Python 版本过低：$ver（需 >=3.11）" }

# [2/4] 虚拟环境    [3/4] 装依赖
if (-not (Test-Path $Venv)) { & python -m venv $Venv }
$vpy = Join-Path $Venv "Scripts\python.exe"
& $vpy -m pip install --upgrade pip | Out-Null
& $vpy -m pip install -r (Join-Path $Root "requirements.txt")

# [4/4] 启动前自检 —— 缺 WebView2 时这里报 warn 而非 fail
& $vpy (Join-Path $Root "run_etude.py") --check
Write-Host "完成。启动： .venv\Scripts\python.exe run_etude.py"
```

2. **TideWatch 补 `setup.ps1` + 在 README「快速开始」并列给 Windows 命令**（不删 Makefile，二者并存）：

```powershell
# TideWatch 一键环境（Windows）
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[zh,dev]"
.\.venv\Scripts\python.exe scripts\gen_sample.py
# 扫描示例： .\.venv\Scripts\python.exe -m tidewatch.cli scan data/sample/sample.jsonl --evidence
```

3. **Etude README 补一句 Python 版本**，并与 CI 对齐（推荐把 `docs/QUICKSTART.md:13` 的「3.10+」改成「3.11+」，或把 CI 矩阵加 `"3.10"`——**二选一，别两个都改**）：

```markdown
## 快速开始
> 前置条件：Windows 10/11 + **Python 3.11+**（与 CI 验证的版本一致）。
> 不想装 Python 就下载 [Releases](…) 的 exe。
```

4. **WebView2 / edge-tts 的「失败降级」写清**（Etude 已有降级逻辑，只是文档没讲透）：在 `docs/QUICKSTART.md` 的 WebView2 处补一句「缺 WebView2 → 自动退回浏览器，功能完全一样，`--check` 会报 `warn` 而非 `fail`」。

**优先级**：P1　｜　**工作量**：Etude setup.ps1 + README 更正 2 小时；TideWatch setup.ps1 1 小时
**验收标准**：①Etude 在干净 Windows 上「下载 → 解压 → 双击 `setup.ps1` → 跑起来」全程**不需要手敲 pip**；②三旗舰 README 的 Python 版本声明与各自 CI 矩阵**一致**；③TideWatch README 的「快速开始」在 Windows 上**有可直接复制的命令**（不依赖 `make`）。

---

### P1-5　文档站与 API 文档：FastAPI 自带的 Swagger，一个没链接、一个被关掉

**现象+证据**：
- **有没有文档站**：三旗舰均**无** mkdocs / mdBook / Docusaurus（无 `mkdocs.yml` / `book.toml` / `docusaurus.config.js`）。
- **WingMan**：`WingMan/backend/app/main.py:103` 用 `FastAPI(title=..., description=..., version=..., lifespan=...)` **未覆盖 `docs_url`**，因此默认的 `/docs`（Swagger UI）与 `/redoc`、`/openapi.json` **是开启的**；但 `grep -niE "/docs|swagger|api 文档" WingMan/README.md` → **零命中**，README 从未告诉读者「服务跑起来后可以打开 `http://127.0.0.1:8787/docs` 看接口」。
- **Etude**：`Etude/backend/app/api.py:51` 明确写 `app = FastAPI(title="Etude", version=__version__, docs_url=None, redoc_url=None)` —— **Swagger 与 ReDoc 都被关闭**（`openapi_url` 未覆盖，故 `/openapi.json` 仍可用，但无 UI）。
- **TideWatch**：不是 Web 服务（CLI + 库），API 文档面向的是「Python 库使用者」，README 的「开发」段（`:313`）只给 `make` 命令，未说明如何查看 `src/tidewatch` 的公开接口。

**为什么是问题**：
- 对 WingMan，「服务已经起来了、Swagger 就在 `/docs`」，**却没有任何一处提示**——这是**零成本的文档可得性浪费**。第一轮的痛点是「README 太长」，而 `/docs` 恰恰是**最适合把「接口细节」从 README 分流出去**的地方。
- 对 Etude，关闭 Swagger 可能有正当理由（本地工具、不希望暴露接口面），但**理由没有被记录下来**——按 P1-2 的 ADR 原则，这正是该写一条 ADR 的地方。而且 `docs_url=None` 也意味着**没有可分享的接口文档**，这对「想用它的 HTTP 接口做自动化」的用户是门槛。
- 对三旗舰而言，**没有一个「文档入口页」**把散落的 8–11 份 md 串起来（WingMan 有「文档索引」表，Etude 有「文档索引」，但都是 README 内的一个表格，且**不全**——见 P2-2）。

**改法**：

1. **立即可做（10 分钟）**：WingMan README 的「三种跑法」或「开发」节补一行：

```markdown
> 服务跑起来后，接口文档在 <http://127.0.0.1:8787/docs>（Swagger）/ `/redoc` / `/openapi.json`。
> README 只讲「怎么用」，接口字段以 `/docs` 为准。
```

2. **Etude 二选一**：
   - 若确实想关掉 UI，**保留 `/openapi.json`** 并在 README 写：「接口 schema 见运行时 `http://127.0.0.1:<port>/openapi.json`」；
   - 或改为**只在开发模式开启**：`docs_url="/docs" if __debug__ else None`（保持生产关闭、开发可见）。
   无论选哪个，**按 P1-2 补一条 ADR** 记录「为什么关」。

3. **不建议上完整文档站**（对 3 个项目过重）。**推荐的最小文档站方案 = README 内的「文档地图」+ `docs/README.md` 索引页**：

```markdown
<!-- docs/README.md —— 三旗舰通用的文档地图 -->
# 文档地图

> README 讲「是什么、怎么跑」；这里回答「想深入某个方向该看哪份」。

| 我想… | 看这份 |
|---|---|
| 10 分钟跑起来 | [QUICKSTART.md](QUICKSTART.md) |
| 理解系统怎么搭的 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 知道为什么这么设计 | [adr/](adr/) |
| 知道现在什么样 / 什么没做 | [STATUS.md](STATUS.md) |
| 知道接下来做什么 | [ROADMAP.md](ROADMAP.md) |
| 排查问题 | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| 看历史怎么变的 | [../CHANGELOG.md](../CHANGELOG.md) / [DEVLOG.md](DEVLOG.md) |
```

   并把 README 的「文档」表改为**只放 3–4 条**（QUICKSTART / 文档地图 / CHANGELOG / LICENSE），其余交给 `docs/README.md` —— 这就是第一轮「让 README 长文分流」在**文档治理层**的具体做法。

4. **可选进阶（P2，本项目暂不需要）**：若将来要发布到 PyPI 或做多语言文档，再引入 mkdocs-material。现在的体量（`docs/` 11 份 md）**上文档站是过度工程**，我明确不建议。

**优先级**：P1（第 1 条，10 分钟）　｜　**工作量**：第 1 条 10 分钟；`docs/README.md` 三仓库各 30 分钟
**验收标准**：①WingMan README 出现 `/docs` 链接；②三旗舰各有 `docs/README.md` 文档地图且**覆盖 docs/ 下所有 md**（见 P2-2 的验收）；③Etude 关闭 Swagger 的理由被记录（ADR 或 README 一行说明）。

---

### P2-1　文档里残留本机绝对路径（一处，真实泄漏）

**现象+证据**：
- `Etude/docs/THEORY.md:13`：「讲稿整理见 **`C:\Users\HP\Desktop\学习观07.txt`**）」
- 对照：WingMan 的 `docs/DESKTOP.md:140`、`docs/releases/v0.1.0.md:36` 等处的 `C:\Users\<用户>\…` 与 `C:\Users\你的用户名\…` 是**占位符**（无害）；`Python-Self-Learn/练习19.py:7` / `练习20.py:31` 的 `C:/Users/你的名字/…` 也是**教学示例**（无害）。

**为什么是问题**：**只有 `Etude/docs/THEORY.md:13` 是真实的用户名 `HP`**——它泄漏了「作者本机用户名叫什么」这一条低敏但真实的信息，且暴露了「讲稿文件放在桌面」这一习惯。它不属于第一轮 `Self-Mind`/邮箱那一类高敏隐私，但属于**同一类卫生问题**，而且**改起来只要 5 秒**。

**改法**：把该行改为不含本机路径的表述：

```markdown
来源：《学习观 07 · 我们十几年的外语教学的方法几乎全错了》（B 站 BV1TU4y197jU），
以及两篇配套的知乎文章
```

（删除「讲稿整理见 `C:\Users\HP\Desktop\学习观07.txt`」这一句，或改为「讲稿：见 B 站该视频」——因为原路径对读者**毫无用处**，讲稿在别人机器上不存在。）

**优先级**：P2（低敏，但零成本）　｜　**工作量**：5 分钟
**验收标准**：三旗舰全量文档 `grep -rn "C:\\\\Users\\\\[A-Za-z]"` **只命中占位符**（`<用户>` / `你的用户名` / `你的名字`），无真实用户名。

---

### P2-2　文档索引不全：README 的「文档」表漏掉了最长的两份文档

**现象+证据**：
- **WingMan**：`docs/` 下有 **11 份 md**（ARCHITECTURE / COMPLIANCE / DESKTOP / DEVLOG / ENGINE_DESIGN / MODELS / **PLAN-对象中心迭代** / QUICKSTART / ROADMAP / **STATUS** / TROUBLESHOOTING）。但 `WingMan/README.md:443` 起的「## 文档」表**只列了 9 项**（含 CHANGELOG）。执行 `grep -nE "STATUS\.md|PLAN-对象中心" WingMan/README.md` → **零命中** —— 也就是说 **`STATUS.md`（880 行，`docs/` 里最长的一份）** 与 **`PLAN-对象中心迭代.md`（422 行）** **从未在 README 里被引用**，只有「全新上下文的窗口」按 `STATUS.md:3` 的自述才可能找到它。
- **TideWatch**：`grep -nE "docs/" TideWatch/README.md` 只命中 `docs/benchmark.md`（2 处）和一句泛泛的目录注释（`:253`）。**`docs/design-decisions.md`（636 行，全仓库最有价值的文档）** 与 **`docs/architecture.md`（203 行）** 在 README 里**均无链接**。
- **Etude**：✅ 做得好——`README.md:430` 的「### 文档索引」完整列出 THEORY / ARCHITECTURE / QUICKSTART / STATUS / DEVLOG / releases / CHANGELOG。

**为什么是问题**：**读者找不到 = 文档不存在**。对 TideWatch 尤其可惜——它的 `design-decisions.md` 恰好是**最能证明「作者会做工程取舍」**的一份文件（D1–D16 每条都有备选与代价），却被埋在 README 从不提及的角落。第一轮的结论是「TideWatch 是全项 A 的标杆」，**而它的标杆文档现在藏在门后**。

**改法**：
1. WingMan 在 `README.md:443` 的表里补两行：

```markdown
| [docs/STATUS.md](docs/STATUS.md) | **现状底稿**：现在是什么样、哪些没做（含版本与文件地图） |
| [docs/PLAN-对象中心迭代.md](docs/PLAN-对象中心迭代.md) | 下一步的改版计划：要改成什么样 |
```

2. TideWatch 在 README「项目结构」（`:232`）之后新增一小节：

```markdown
## 文档
| 文档 | 内容 |
|---|---|
| [docs/architecture.md](docs/architecture.md) | 三层十信号的模块职责与数据流 |
| [docs/design-decisions.md](docs/design-decisions.md) | **16 条设计取舍（含备选与代价）+ 11 条踩坑记录 + 5 条待验证假设** |
| [docs/benchmark.md](docs/benchmark.md) | 消融实验实测数据 |
```

**优先级**：P2（10 分钟，收益直接）　｜　**工作量**：WingMan 5 分钟 / TideWatch 5 分钟
**验收标准**：**README 的文档索引覆盖 `docs/` 下的每一份 `.md`**（脚本校验：`diff <(ls docs/*.md) <(grep -o 'docs/[^)]*\.md' README.md)`）。Etude 已达标，作为参照。

---

### P2-3　`frontend-learning`：`.gitignore` 忽略 `.vscode/`，却提交了 `.vscode/settings.json`

**现象+证据**：`frontend-learning/.gitignore` 含 `.vscode/`，但 `frontend-learning/.vscode/settings.json`（内容 `{ "liveServer.settings.port": 5501 }`）**实际在仓库里**。同类问题在 `Python-Self-Learn` 更明显：`.gitignore` 未排除 `*.csv` / `*.txt`，于是 `data.csv` / `data_temp.csv` / `sales.csv` / `weather.csv` / `weather_forecast.csv` / `log.txt` / `note.txt` / `poem.txt` **8 个练习产物全被提交**。

**为什么是问题**：**规则与事实自相矛盾**——`.gitignore` 说「不要 `.vscode/`」，仓库里却有一个（它在写 `.gitignore` 前就已 tracked，而 `.gitignore` 对**已跟踪文件无效**）。说明这两个仓库没做过 `.gitignore` 生效性检查。

**改法**（随合并进 `dev-notes` 时顺手处理）：①删除 `.vscode` 的跟踪——`git rm -r --cached .vscode && git commit -m "chore: 停止跟踪本机编辑器配置"`；②`Python-Self-Learn` 产物的**判定标准**：练习**输入/输出样例**（读者靠它才能跑通练习 19 的 CSV 读写）→ 移入 `01-python/data/` 保留；**随手生成的**（`data_temp.csv`、`log.txt`）→ 删除并补进 `.gitignore`。**建议保留 `sales.csv` / `weather.csv`、删掉 `data_temp.csv` / `log.txt`**（前者让笔记可复现，后者只是垃圾）。

**优先级**：P2　｜　**工作量**：20 分钟（随合并做）
**验收标准**：`dev-notes` 里不存在「被 `.gitignore` 覆盖却仍被跟踪」的文件；每个保留的 `.csv` 都能对应到某个练习脚本的输入。

---

### P2-4　`Self-Mind` 的协作/文档缺口的**边界说明**（不评价内容）

**现象+证据**（**仅计数，未读取内容**）：顶层 **9 个目录**、**182 个 `.md`**、**640 个文件**；根目录**无 README / LICENSE / `.gitignore`**（与第一轮 `portfolio-review.md` 2.1 一致）。

**为什么单列**：第一轮已判定「立即转 Private」，**本轮不再重复**。只补一句文档治理相关边界：`Self-Mind` 的 640 个文件里**没有任何一份是协作意义上的文档**，182 个 md 全是个人笔记内容。因此 —— ①第 1 节矩阵中 `Self-Mind` 一列的所有 ❌ **不构成改进建议**（个人知识库不需要 `CONTRIBUTING.md`）；②若第一轮「拆分：私有日记库 + 公开知识库」被采纳，**只有拆出的公开那份**才需补 `LICENSE`（建议 MIT）与 `.gitignore`（必须，至少排除 `.obsidian/`）。

**优先级**：—（不适用）　｜　**工作量**：—　｜　**验收标准**：第一轮「转 Private」完成即可，本报告不对 `Self-Mind` 提额外动作。

---

## 3. 跨项目共性清单（C-1, C-2, …）

> 说明：编号从 **C-11** 起，**避开**第一轮已使用的 C-1 ~ C-10（主报告 4.3 节），防止混淆。

| 编号 | 问题 | 涉及项目 | 优先级 | 对应条目 |
|---|---|---|---|---|
| **C-11** | 协作文件零覆盖（CONTRIBUTING / SECURITY / CoC / CODEOWNERS / Issue&PR 模板 / .editorconfig） | 9 仓库全体 | **P0** | P0-1 |
| **C-12** | 无 SECURITY.md，与「本地优先/隐私」定位冲突 | WingMan / Etude / TideWatch | **P0** | P0-2 |
| **C-13** | 文档漂移已实际发作：`STATUS.md` 头部快照与正文版本矛盾 + 手写行号过期 | WingMan | **P0** | P0-3, P1-3 |
| **C-14** | 仓库元数据（description/topics）与代码不一致 / 过度承诺 | TideWatch（新）/ WingMan（第一轮已提） | **P0 / P1** | P0-4 |
| **C-15** | 提交规范只写在 CHANGELOG，未落到 commit 层（无 hook、无 CI 校验） | WingMan / Etude（TideWatch 无 CHANGELOG） | P1 | P1-1 |
| **C-16** | ADR 缺位或形式不标准（三合一 / 散文 / 完全没有） | TideWatch / WingMan / Etude | P1 | P1-2 |
| **C-17** | 五类文档职责未定义，同一条信息多处副本 | WingMan（最重）/ Etude / TideWatch | P1 | P1-3 |
| **C-18** | onboarding 一键化不齐（Etude 无脚本；TideWatch 仅 Makefile） | Etude / TideWatch | P1 | P1-4 |
| **C-19** | 文档站/API 文档入口缺失（Swagger 未链接或已关闭） | WingMan / Etude / TideWatch | P1 | P1-5 |
| **C-20** | README 文档索引不全（docs/ 下有文件从未被引用） | WingMan / TideWatch（Etude 达标） | P2 | P2-2 |
| **C-21** | 文档残留真实本机路径 | Etude | P2 | P2-1 |
| **C-22** | `.gitignore` 与已跟踪文件自相矛盾（规则失效） | frontend-learning / Python-Self-Learn | P2 | P2-3 |

---

## 4. 落地路线（3 周 + 验收标准）

> 按 1 名开发者、每周 2–3 人日估算；每个动作可独立成 commit。**与第一轮的四周路线并行、不冲突**（第一轮 W1 有「三项目加 pre-commit」的覆盖率支线，本轮 W1 的提交规范正好与它合并做）。

### 第 1 周 —— 协作基线 + 止血（约 1.5 人日）

| # | 动作 | 对应 | 产出 | 验收标准 |
|---|---|---|---|---|
| W1-1 | 三旗舰各加 `CONTRIBUTING.md` / `SECURITY.md` / `.editorconfig` + `.github/` 下 3 个模板 | P0-1, P0-2 | 21 个新文件 | GitHub Issues 出现模板选择；Security 出现私密报告入口 |
| W1-2 | 三旗舰各加 `.pre-commit-config.yaml`（含 `commit-msg` 钩子）并写进 CONTRIBUTING | P1-1 | 3 个配置 | 本地提交 `update` 被拒、`fix(x):…` 通过 |
| W1-3 | GitHub 仓库设置：开启 Private vulnerability reporting + 给 4 个学习/空壳仓库补 description | P0-2, C-14 | 设置变更 | 三旗舰 Security 页有入口；无描述仓库数 = 0 |
| W1-4 | 修 WingMan `STATUS.md` 头部（去掉手写版本/测试数）+ 补 `scripts/gen_status.py` | P0-3 | 脚本 + 文件 | `gen_status.py --check` 能拦过期；头部无手写版本 |
| W1-5 | 改 TideWatch GitHub 描述，删除「跨网络舆情分析」 | P0-4 | 描述变更 | 描述与 `pyproject.toml:7` 一致 |
| W1-6 | WingMan README 补 `/docs` 链接；三旗舰补 `docs/README.md` 文档地图 | P1-5, P2-2 | 4 处改动 | README 文档索引覆盖 `docs/` 全部 md |

### 第 2 周 —— ADR 与 onboarding（约 2 人日）

| # | 动作 | 对应 | 产出 | 验收标准 |
|---|---|---|---|---|
| W2-1 | 建立 `docs/adr/template.md` 与命名约定；TideWatch 把 D1–D16 迁移为 ADR（旧文件改为索引） | P1-2 | `docs/adr/` ×3 | 首条 ADR 含状态/日期/备选/代价；旧文件仍可访问 |
| W2-2 | WingMan / Etude 各补 3–5 条 ADR（含「为什么 store.py 集中」「为什么 Etude 关 Swagger」） | P1-2, P1-5 | 6–10 条 ADR | 每条 ADR 指向真实测试或代码 |
| W2-3 | Etude 加 `backend/setup.ps1`；README 补 Python 版本；CI 矩阵或声明二选一对齐 | P1-4 | 脚本 + 文档 | 干净 Windows 上不手敲 pip 可跑通 |
| W2-4 | TideWatch 加 `setup.ps1`；README「快速开始」并列 Windows 命令 | P1-4 | 脚本 + 文档 | Windows 上不依赖 `make` 可跑 `scan` |
| W2-5 | 把「哪类信息放哪 + 必须同步清单」写进三份 CONTRIBUTING | P1-3 | 3 处文档 | 同一版本号只有一个手写来源 |
| W2-6 | 修 `Etude/docs/THEORY.md:13` 本机路径 | P2-1 | 1 行 | 全量 grep 无真实用户名 |

### 第 3 周 —— 学习仓库合并（约 1.5 人日）

| # | 动作 | 对应 | 产出 | 验收标准 |
|---|---|---|---|---|
| W3-1 | 建 `dev-notes`，按 P0-5 目录结构迁移三个学习仓库（方案 A `git subtree`） | P0-5 | 新仓库 | 三个子目录内容完整、`git subtree` 历史可查 |
| W3-2 | 写 `dev-notes/README.md`（「学了→用在哪」≥4 条真实映射）与 `CONTRIBUTING.md`（防垃圾场三规则） | P0-5 | 2 份文档 | 每条映射能指到旗舰真实模块 |
| W3-3 | 三个旧仓库 Archive + 各补一段指向 `dev-notes` 的 README | P0-5 | 3 份 README | 旧仓库页显示「已归档」且有跳转 |
| W3-4 | 处理 `.vscode` 与练习产物（删 temp、留输入数据） | P2-3 | 清理提交 | 无「被忽略却已跟踪」的文件 |

**整体验收（第 3 周末）**：
1. 9 个仓库中**任意一个**打开 Issues，都能看到模板（学习仓库除外，因为它们不需要）；
2. 三旗舰的 `README.md` 与 `docs/` **完全互相可达**（无孤儿文档）；
3. 三旗舰的版本号在仓库内**只有一个手写来源**，且 CI 能拦住与 `__version__` 不一致的提交；
4. 三个学习仓库合并为 1 个 `dev-notes`，账号公开仓库数 ≤ 7；
5. 全仓库 `grep` 不到真实 QQ 邮箱（第一轮）、真实用户名（本轮 P2-1）、本机绝对路径（除占位符）。

---

## 5. 待确认项

> 以下均因**信息不可得**或**评审纪律（只读、不执行）**而未能核实，**未做任何推测性结论**。

1. **三旗舰真实提交历史与提交信息风格** —— 本地为 `--depth 1` 浅克隆（`git rev-list --count HEAD` 三仓库均返回 `1`），**无法读取历史**。P1-1 中「当前提交风格是否一致」**待确认**；建议作者本地执行 `git log --oneline -50` 自查。同理，第一轮提到的「commit 元数据 QQ 邮箱」在浅克隆下也无法复核（采信第一轮结论）。
2. **`conventional-pre-commit` 在 Windows + Python 3.11/3.13 上的实际可用性** —— 该配置**未实际安装运行**（评审禁止 `pip install`）。选它而非 `commitlint` 的理由是「纯 Python、无需 Node」，但**未验证**；落地前请 `pre-commit run --all-files` 试跑。
3. **TideWatch 是否真的没有「跨网络」相关代码** —— 本轮 `grep` 只覆盖 `src/`、`eval/`、`configs/`、`README.md`。若相关能力藏在 `scripts/`、`experiments/`、`rules/` 或 `docs/` 中，P0-4 的结论需要修正。**建议作者自查**：`grep -rniE "舆情|cross-network" TideWatch/`。
4. **Etude 关闭 Swagger（`api.py:51`）的真实理由** —— 代码只给了 `docs_url=None`，**没有注释说明原因**。P1-5 / P1-2 中「补一条 ADR 记录为什么关」是基于「理由应当被记录」的一般原则，**不代表我推断出具体原因**。
5. **`Self-Mind` 的 432 个附件性质** —— 与第一轮一致，**隐私红线，未做内容定性**，需作者人工复核（第一轮 `portfolio-review.md` 4.2 已列）。
6. **Etude 的 `--check` 自检在干净机器上的真实行为** —— 本轮只做**静态**核对（读了 `docs/QUICKSTART.md` 与 `requirements.txt` 注释），**未运行** `Etude.exe --check`。P1-4 中「WebView2 / edge-tts 会卡住」是基于文档与依赖声明的**推断**，需实测确认。
7. **WingMan `docs/STATUS.md:408` 的「240 passed」是否是当前真实值** —— 本轮**未运行 pytest**，无法确认 240 是 0.2.0 当时的数字还是当前数字；P0-3 的结论只依赖「头部 0.1.4/208 与正文 0.2.0/240 互相矛盾」这一**内部不一致**，不依赖具体数字的真伪。
8. **`frontend-learning` 的 `.vscode/settings.json` 与 `Python-Self-Learn` 的 csv/txt 各自的用途** —— 是否属于「练习必需输入」需作者判断，P2-3 只给了「保留输入、删除临时产物」的**判定标准**，未替作者决定。

---

## 6. 与第一轮报告的关系

### 6.1 本轮严格不重复的清单（第一轮已提，本轮**未再提**）

| 第一轮条目 | 位置 | 本轮处理 |
|---|---|---|
| `Self-Mind` 转 Private | 主报告 2.1 | **未重复**；仅在 P2-4 说明其文档缺口**不适用** |
| Profile README | 主报告 2.2 | 未提 |
| 重排 Pin | 主报告 2.2 | 未提 |
| 归档 2 个空壳 | 主报告 2.2 | 未提（P0-5 只涉及学习仓库） |
| README 英文版 / 首屏 / GIF / TOC / 架构图改造 | 主报告 6.3 | 未提 |
| 三旗舰 README 各自的差异化章节 | 主报告 6.3 | 未提 |
| 「4 个学习仓库合并为 dev-notes」**方向** | 主报告 6.2 / portfolio 2.2 | **只补执行方案**，已标注（P0-5） |
| commit 元数据 QQ 邮箱 | 主报告 2.3 | 未提（P2-1 是**另一处**：文档内的本机用户名路径） |
| 仓库分级与处置表 | 主报告 6.2 | 未提 |
| WingMan topics 含 `whisper`/`asr` 过期 | portfolio D7 | 未提；P0-4 是**另一个仓库**（TideWatch 描述**多写了**功能） |
| 三项目加 pre-commit（覆盖率支线） | 主报告 5.3 W3 | **本条 P1-1 特指「提交信息规范」**，与之互补而非重复 |

### 6.2 本轮与第一轮的**互补关系 + 三处增量**

- **互补**：第一轮视角是「架构 / QA / 产品」，覆盖代码与呈现；本轮视角是「协作 / 文档治理 / 可维护性」，覆盖「谁能来一起改」（协作文件、提交规范、分支模型）、「三个月后自己能不能看懂」（ADR、文档职责、漂移机制）、「新人能不能跑起来」（onboarding 一键化、Python 版本一致性）、「文档会不会烂」（五类文档分工、脚本生成事实块）——这四类第一轮**均未覆盖**或只作提示。
- **补充 1**：第一轮 5.3-W3 提到「三项目加 pre-commit」，但**未区分两种用途**（代码检查 vs 提交信息校验）。本轮 P1-1 把后者单独抽出并给出 Windows 可跑方案。
- **补充 2**：第一轮把学习仓库标为「合并」，但**未给合并后的维护规则**。本轮 P0-5 的 `CONTRIBUTING.md`（防垃圾场三规则 + 每月除锈）填补空白。
- **修正 1**：第一轮把「文档漂移」仅作风险**提示**，本轮**实证它已发生**（P0-3），并给出**根因**（C-17 五类文档职责未定义）与**机制性解法**（脚本生成事实块）。

---

## 附录：关键实证命令（全部只读）

```bash
# 1. 协作文件存在性矩阵（1.1）
for r in WingMan Etude TideWatch frontend-learning Data-Structures-and-Algorithms Python-Self-Learn; do
  find "$r" -not -path "*/.git/*" \( -iname "CONTRIBUTING*" -o -iname "SECURITY*" \
    -o -iname "CODE_OF_CONDUCT*" -o -iname "CODEOWNERS" -o -iname ".editorconfig" \
    -o -iname "devcontainer.json" -o -iname "PULL_REQUEST_TEMPLATE*" -o -iname "ISSUE_TEMPLATE*" \); done
# 2. 提交规范工具 / CI 校验（P1-1）
grep -rliE "commitlint|commitizen|husky|conventional|commit-msg" WingMan Etude TideWatch
grep -niE "commit-msg|conventional|check.*commit" */.github/workflows/ci.yml
# 3. 行号/计数核对（P0-3）
wc -l WingMan/backend/app/store.py WingMan/backend/app/main.py WingMan/frontend/index.html
ls WingMan/backend/tests/*.py | wc -l
# 4. TideWatch 跨网络舆情实现核查（P0-4）与 FastAPI 文档入口（P1-5）
grep -rniE "舆情|跨网络|cross-network|public.opinion" TideWatch/src TideWatch/eval TideWatch/configs TideWatch/README.md
grep -nE "docs_url|redoc_url|FastAPI\(" WingMan/backend/app/main.py Etude/backend/app/api.py
# 5. 本机路径残留（P2-1）与 README 文档索引完备性（P2-2）
grep -rniE "[A-Za-z]:\\\\Users\\\\" WingMan Etude TideWatch --include=*.md --include=*.py
grep -nE "docs/[^)]*\.md" TideWatch/README.md
```

**评审纪律声明**：本报告所有结论基于**本地浅克隆的只读静态核对**——未执行测试套件、未 `pip install`/`npm install`、未运行被测程序、未对 `gh-repos` 下任何文件做写操作、未执行任何 `git add/commit/push`。`Self-Mind` 全程**只统计文件数量与顶层目录名**（顶层 9 目录 / 182 md / 640 文件），**未读取、未摘抄其中任何内容**。凡未能核实之处已在第 5 节逐条标注为「待确认」。
