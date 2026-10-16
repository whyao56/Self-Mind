---
tags: [领域/方法]
---

# GitHub @whyao56 · 开源呈现与个人作品集评审报告

> 评审视角：招聘方 / 潜在开源协作者 / 技术社区访客
> 评审对象：`github.com/whyao56` 全部公开仓库（实测 9 个，其中 7 个已克隆分析、2 个为空仓库）
> 分析方式：只读本地克隆（`git clone --depth 1`）+ 账号页 WebFetch + 全仓库文本扫描
> 编写：产品经理 许清楚　｜　日期：2026-10-13

---

## 0. 一页结论（TL;DR）

| 维度 | 现状评分 | 一句话诊断 |
|---|---|---|
| 旗舰工程质量 | ★★★★★ | WingMan / Etude / TideWatch 的工程完成度**明显高于个人账号平均水平**，有 CI、有 Release、有 187/161 项测试、有详尽的坑记录 |
| 账号第一印象 | ★★☆☆☆ | Profile 无 README、无身份说明，**最私密的个人日志仓库被 pin 在第 2 位**，首屏 30 秒全是减分项 |
| 仓库分层 | ★★☆☆☆ | 3 个旗舰 + 4 个学习笔记 + 1 个隐私库 + 2 个空壳，**全混在一起平铺**，没有叙事主线 |
| README 完整度 | ★★★★☆ | 旗舰仓库 README 内容极扎实（中文），但**全部为中文**、首屏过长、缺 GIF、缺目录、缺中英切换 |
| 隐私与合规 | ★☆☆☆☆ | **`Self-Mind`（Obsidian 个人知识库，Public）包含约 59 个个人日记/成长档案类文件 + 432 个附件**；另有 5 个仓库的 commit 元数据泄露 QQ 邮箱 |
| 国际可达性 | ★★☆☆☆ | 三个最强项目**没有任何英文内容**，中文 NLP / 本地 AI 工具的价值对英文社区完全不可见 |

**一句话总结**：这是一批「工程质量远好于账号包装」的作品。**最大的问题不是代码，而是账号首页在把一个隐私库当作品展示，且三个真正的旗舰没有任何英文入口。**

**必须立刻做的三件事（按紧急度）**：
1. 🔴 **把 `Self-Mind` 转为 Private**（今天内完成，详见第 4 节）。
2. 🟠 **删除/归档 2 个空仓库，重排 Pin**（WingMan → Etude → TideWatch），补 Profile README。
3. 🟡 **为三个旗舰仓库各加一份英文 README**（`README.en.md` + 顶部语言切换）。

---

## 1. 账号第一印象诊断

### 1.1 实测：招聘方 30 秒内看到什么

通过 WebFetch 抓取 `https://github.com/whyao56` 与 `/repositories`，首屏实际呈现如下：

| 首屏元素 | 实际内容 | 评价 |
|---|---|---|
| Profile README | **无** | 首屏顶部区域完全空白，没有自我介绍、没有项目导览、没有联系方式 |
| Bio（简介） | `Whyao_雾化药。 Confront yourself。` | 纯个人签名，**零技术信息、零角色定位**；`Confront yourself` 对访客无意义 |
| Pin #1 | WingMan（Python，1 fork） | ✅ 正确，最强项目打头 |
| Pin #2 | **Self-Mind —— 描述仅 `Obsidian日志`** | 🔴 **致命扣分**：一个描述为「Obsidian 日志」的个人知识库占据首屏第 2 位 |
| Pin #3 | TideWatch（Python） | ✅ 合理 |
| Pin #4 | Etude（Python） | ✅ 合理，但被排在 Self-Mind 之后 |
| 贡献图 | 179 contributions / 近一年；2026-10 单月 158 commits | ✅ 加分项，说明近三个月高频活跃 |
| 仓库列表排序 | 默认按更新时间：**`Self-Mind` 排在最前**（Updated Oct 12） | 🔴 打开 Repositories 页第一眼看到的仍是这个隐私库 |

### 1.2 具体扣分项清单（有证据）

| # | 扣分项 | 证据 | 影响 |
|---|---|---|---|
| D1 | **Pin 了个人日志库，且排第 2** | Profile 页 Pin #2 = `Self-Mind`「Obsidian日志」 | 访客对作者的第一专业印象被降级为「写日记的人」 |
| D2 | **仓库列表默认排序把隐私库顶到第一** | `?tab=repositories` 首条 = `Self-Mind` | 二次访问仍是同样的第一印象 |
| D3 | **2 个空壳仓库占据仓库列表** | `git-learning-journal`、`my-first-repo`：无描述、无 README、Aug 2026 后未更新 | 9 个仓库里 2 个是噪音，稀释了 3 个旗舰的占比 |
| D4 | **4 个学习笔记仓库描述带「DeepSeek V4.x 指导学习」** | `frontend-learning`「DeepSeek V4.1 Flash 指导学习…」、`Data-Structures-and-Algorithms`「DeepSeek V4 Pro 指导学习…」、`Python-Self-Learn` 同款 | 主动告诉访客「这些是 AI 带我做的练习」，**把加分项写成了减分项**；模型版本号还会随时间过时 |
| D5 | **Profile 无 README** | 首屏顶部无任何内容 | 缺少「我是谁 / 我在做什么 / 从哪个项目看起」的导览 |
| D6 | **无任何英文内容** | 3 个旗舰 README 全中文；TideWatch 描述是中英双语，正文 100% 中文 | 中文 NLP / 本地 AI 工具的价值对英文社区完全不可见，star 与协作机会被天然截断 |
| D7 | **WingMan 的 topics 与描述已过期** | topics 含 `whisper` / `asr`，描述含「支持双通道语音采集转写」；但 `grep -rn "asr\|whisper" WingMan/backend/app/` **返回空**（功能已下线，见其 README 第 16-17 行） | 主动承诺一个已删除的功能，属于**自我打脸的展示信息** |
| D8 | **5 个仓库的 commit 元数据泄露个人邮箱** | `git log -1 --format='%ae'` 在 `Data-Structures-and-Algorithms`、`Python-Self-Learn`、`Self-Mind`、`TideWatch`、`frontend-learning` 均返回 `2160444959@qq.com` | 个人 QQ 号随每个 commit 页公开（详见第 4 节） |

### 1.3 「黄金 30 秒」改造方案

目标：让访客在 30 秒内形成**「本地优先 AI 工具开发者，工程规范」**的印象，而不是「写日记的初学者」。

**第 1 步（0 分钟 · 只动设置）——清理首屏**
1. `Self-Mind` → Settings → 最底部 `Change visibility` → **Private**（消除 D1/D2）。
2. `git-learning-journal`、`my-first-repo` → Settings → **Archive this repository**（消除 D3）。
3. Pin 重排 + 补充：**WingMan → Etude → TideWatch → [预留一个空位]**（见第 3 步）。

**第 2 步（15 分钟）——新建 Profile README**
在同名仓库 `whyao56/whyao56` 建 `README.md`。骨架：

```markdown
# Whyao · 本地优先的 AI 工具开发者

做一个词 → 五通道语言训练器（Etude）｜把聊天记录变成对话参谋（WingMan）
可解释的中文水军识别引擎（TideWatch）

共同点：**本地优先、零 Key 可跑通、诚实标注「没做什么」**。

## 我做的三个东西
| 项目 | 一句话 | 技术亮点 |
|---|---|---|
| [WingMan](…) | 聊天记录 → 人物画像 + 回复参谋 | SQLCipher 解密 / 混合检索 / 可切换 LLM |
| [Etude](…) | 一个词 → 五种练法的语言训练器 | SRS / Edge TTS / 文生图并行 |
| [TideWatch](…) | 可解释的协同行为识别引擎 | 三层十信号 / AC 自动机 / SimHash |

## 我在学什么
- Python 工程化：CI、打包发版、端到端测试
- 中文 NLP：分词、抗规避折叠、SimHash 聚类
- 本地 LLM 应用：Ollama / OpenAI 兼容协议 / 隐私边界

📮 contact: [邮箱或社交链接]
```

**第 3 步（可选，第 4 位 Pin）**：把 4 个学习笔记**合并成 1 个** `dev-notes` 仓库（或挑最好的一份），补 README 后在 Pin 第 4 位放「学习轨迹」—— 把 D4 的减分项转成「持续学习者」的加分项。

---

## 2. 仓库分级与定位

### 2.1 四类分级总表

| 仓库 | 语言 | 体量 | 现状 | 定位建议 | 可见性 | 最小改动 |
|---|---|---|---|---|---|---|
| **WingMan** | Python | 147 文件 / 31.6k 行 | CI✅ Release✅ MIT✅ README 极详✅ | **旗舰 #1**｜「本地优先的对话参谋」 | Public | ① topic 删 `whisper`/`asr` ② 描述去掉「语音转写」 ③ 加 `README.en.md` ④ README 顶部加 TL;DR + TOC |
| **Etude** | Python | 109 文件 / 18.7k 行 | CI✅ Release✅ MIT✅ 8 张截图✅ | **旗舰 #2**｜「AI 生成内容 + 间隔重复的语言训练器」 | Public | ① 加 `README.en.md` ② 加 1 个 30 秒 GIF ③ README 顶部加 TL;DR + TOC ④ 补 topics |
| **TideWatch** | Python | 84 文件 / 6.5k 行 | CI✅ MIT✅ benchmark 表格✅ topics 齐✅ | **旗舰 #3**｜「可解释的中文协同行为识别引擎」 | Public | ① 加 `README.en.md`（作者已写双语描述，正文需补） ② 加一张架构图 SVG ③ 补 `LICENSE` 徽章一致性 |
| **frontend-learning** | HTML | 54 文件 | 无 README / 无 LICENSE | **学习笔记**｜合并进统一笔记仓库 | Public→合并 | 迁入 `dev-notes/frontend/` 后归档本仓库 |
| **Data-Structures-and-Algorithms** | Python | 53 文件 / 1.5k 行 | 无 README / 无 LICENSE | **学习笔记**｜同上 | Public→合并 | 同上 |
| **Python-Self-Learn** | Python | 76 文件 / 1.7k 行 | 无 README / 无 LICENSE | **学习笔记**｜同上 | Public→合并 | 同上 |
| **Self-Mind** | HTML/MD | 669 文件 / 182 md | **无 README / 无 LICENSE / 无 .gitignore** | **应私有**｜个人知识库，非作品 | Public→**Private** | 见第 4 节，**立即转 Private** |
| **git-learning-journal** | — | 空 | 无描述 / 无内容 | **应归档** | Public→归档 | Settings → Archive |
| **my-first-repo** | — | 空 | 无描述 / 无内容 | **应归档** | Public→归档 | Settings → Archive |

> 说明：任务说明里提到「7 个仓库」，实测账号下共 **9 个公开仓库**（多出 `git-learning-journal`、`my-first-repo` 两个空壳）。两者已通过 WebFetch 核实：均无描述、无 README、最后更新于 2026-08。

### 2.2 为什么建议把 3 个学习笔记合并

证据：三个笔记仓库的**内容组织方式高度雷同**，且描述格式一致：

| 仓库 | 描述模板 | 语言 | 文件数 |
|---|---|---|---|
| `frontend-learning` | `DeepSeek V4.1 Flash 指导学习的Web前端笔记` | HTML | 25 |
| `Data-Structures-and-Algorithms` | `DeepSeek V4 Pro 指导学习的数据结构与算法笔记` | Python | 24 |
| `Python-Self-Learn` | `DeepSeek V4 Pro 指导学习的Python笔记` | Python | 47 |

**问题**：3 个仓库各自没有 README、没有学习目标说明、没有学习时间线，单独看都无法证明「我真的学会了什么」。**合并 + 一份好的 README 的展示效果，远好于 3 个裸仓库。**

合并后的 `dev-notes` 建议结构：

```
dev-notes/
├── README.md          # 学习路线图 + 时间线 + 每科「学到了什么 / 还没学什么」
├── 01-python/         # 原 Python-Self-Learn
├── 02-dsa/            # 原 Data-Structures-and-Algorithms
├── 03-frontend/       # 原 frontend-learning
└── 04-algorithms-notes/
```

README 核心是一张**「学了 → 用在哪」的对照表**，把学习笔记和旗舰工程挂起来（例：`01-python/` 的 SQLite 练习 → WingMan 的 `memory/` 模块）。这一步能把 D4「AI 指导学习」的减分项，转化成「有方法、有产出」的加分项。

---

## 3. 逐个仓库 README 体检

### 3.1 体检总表

| 仓库 | README | 徽章 | 截图/GIF | TOC | 快速开始 | 架构图 | 英文 | 主要缺口 |
|---|---|---|---|---|---|---|---|---|
| WingMan | ✅ 950 行 | ✅ 3 个 | ✅ 4 张 PNG，**无 GIF** | ❌ | ✅ 三种跑法 | ✅ ASCII 图 | ❌ | 无 TOC、首屏过长、无 GIF、无英文 |
| Etude | ✅ 475 行 | ❌ 无徽章 | ✅ 十余张 PNG，**无 GIF** | ❌ | ✅ 两种 | ❌ 无架构图 | ❌ | 无徽章、无 TOC、无架构图、无英文 |
| TideWatch | ✅ 341 行 | ✅ 4 个 | ❌ 仅 ASCII 图 | ❌ | ✅ | ✅ ASCII 图 | 描述双语／正文中文 | 无位图、无 TOC、无英文正文 |
| 4 个笔记仓库 | ❌ 无 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 全缺 |
| Self-Mind | ❌ 无 | ❌ | — | — | — | — | — | 无 README 也是「应私有」的旁证 |

> 客观说明：三个旗舰的 README **内容质量已经远超个人仓库平均水平**——尤其 WingMan 的「踩坑记录」14 条，是极强的工程能力背书。下面的改进建议属于**「好 → 更好」**的优化，而非「不合格 → 合格」的补课。

### 3.2 三个旗舰仓库的**共性缺口**（先说共性，再给各自骨架）

| 共性缺口 | 问题 | 改法 |
|---|---|---|
| **首屏没有 TL;DR** | WingMan README 第 1 屏就被版本变更说明占满（第 19-32 行连续 4 段 `> v0.1.x 起…`） | 在标题后插入「3 行 TL;DR + 1 张图 + 1 条安装命令」，把版本变更折叠到 `<details>` |
| **无 TOC** | WingMan 950 行、Etude 475 行，无目录，只能滚动 | 用 `<!-- TOC -->` 或手写锚点目录 |
| **无 GIF** | 静态 PNG 无法传达「动画/交互」类产品的价值 | WingMan 录「导入→分析→建议」8 秒 GIF；Etude 录「翻卡→评分」5 秒 GIF |
| **全文中文** | 三个项目里 TideWatch（中文 NLP）、WingMan（SQLCipher/QQ 解密）**在国际上的稀缺性很高**，却无英文入口 | 新增 `README.en.md`，正文顶部加语言切换行（见 3.6） |
| **徽章不齐** | Etude 无徽章；WingMan/TideWatch 各 3-4 个 | 统一为 License / Python 版本 / CI / Release / 依赖数 五件套 |

### 3.3 WingMan —— 完整 README 改进大纲

现状：950 行，信息极全但**首屏即深水区**。目标：**首屏 30 秒看懂 + 想跑 → 折叠细节**。

```markdown
# WingMan · 聊天僚机
[徽章行：License | Python 3.11+ | CI | Release v0.2.0 | Zero-Key Demo]

> 一句话：把聊天记录交给大模型记忆，读懂 Ta 是个什么样的人，然后告诉你该怎么回。
> **本地优先 · 零 API Key 可跑通全流程 · 只建议不代发**

[🖼 8 秒 GIF：导入聊天记录 → 点「分析」→ 出现情绪/意图/四条候选回复]

**English** | 中文   ←（指向 README.en.md）

## TL;DR
- 想直接用 → 下载 [WingMan-0.2.0-win64.zip](…)，解压双击
- 想看代码 → `wingman.cmd`（Windows）/ `uvicorn app.main:app`（任意平台）
- 不想配模型 → 内置 Mock 引擎也能跑完整链路
> 完整状态矩阵见文末「版本与状态」

## 目录 (TOC)
<!-- TOC -->
- [它解决什么问题](#它解决什么问题)
- [30 秒上手](#30-秒上手)
- [三种跑法怎么选](#三种跑法怎么选)
- [采集聊天记录](#采集聊天记录)
- [架构总览](#架构总览)
- [文档索引](#文档索引)
- [踩坑记录](#踩坑记录)   ← 本文最有价值的章节
- [版本与状态 / 已知限制](#版本与状态)
<!-- /TOC -->

## 它解决什么问题          ← 【新增】2 段 + 1 张对比表，讲清 what/why
## 30 秒上手               ← 【合并】现有「直接下载」+「快速开始」压成一屏
## 三种跑法怎么选           ← 【保留】现有表格已很好（第 101-108 行）
## 界面预览                 ← 【前移】把第 211-244 行的截图提到这里，紧跟上手
## 采集聊天记录             ← 【保留】内容很好，建议加一个 <details> 折叠
## 架构总览                 ← 【保留】ASCII 图 + 建议补一张 SVG
## 权限与隐私边界           ← 【新增小节】摘要 COMPLIANCE.md 的 3 条红线
## 文档索引                 ← 【保留】现有表格已很好（第 445-456 行）
## 踩坑记录                 ← 【保留】14 条，建议改造成 <details> 折叠标题
## 版本与状态 / 已知限制     ← 【后移到底部】把第 19-32 行的四段版本说明搬到这里
## License
```

**截图/GIF/徽章清单**：

| 位置 | 物料 | 说明 |
|---|---|---|
| 标题下方 | **GIF（必需）** | 8 秒：采集→分析→四条建议。用 ScreenToGif 录制，控制在 2MB 内 |
| 「界面预览」 | 4 张现有 PNG | 已具备（`docs/images/ui-*.png`），保持 |
| 架构节 | **SVG 架构图** | 替换 ASCII 图，可缩放、可嵌入英文 README 复用 |
| 徽章行 | License / Python / CI / Release / Zero-Key | 前 3 个已有，补 Release 与 Zero-Key 徽章 |

**中英双语组织**：本仓库**必须双语**。理由：`SQLCipher 解密 QQ/微信本地库 + 本地优先 LLM` 在国际开源社区属于**高稀缺话题**，纯中文等于放弃全部外部曝光。组织方式见 3.6。

### 3.4 Etude —— 完整 README 改进大纲

现状：475 行，8 张截图已很好，但**无徽章、无架构图、无 TOC**。

```markdown
# Etude · 句子五通道语言训练器
[徽章行（新增）：License | Python 3.11+ | CI | Release 0.0.3 | Tests 187 passing]

> 一个把一句话练到「脱口而出」的本地工具：给一个词，生成 8 条不同上下文的例句，
> 铺成五种练法——阅读、听力、口语、打字、造句。
> *Etude*（/eɪˈtjuːd/）= 音乐里的「练习曲」。

[🖼 5 秒 GIF：翻面 → 点评分键 → 下一张]   ← 新增，补足「交互感」

**English** | 中文   ← 新增

## TL;DR
- 下载 exe → 解压 → 双击 → 设置里填模型 → 输入 `appreciate`
- 内容由大模型生成，语音用 Edge TTS，进度存在本机

## 目录 (TOC)
## 它和已有工具不一样在哪   ← 【保留】现有对比表极好，是本文灵魂（第 26-33 行）
## 界面                     ← 【保留】8 张截图，建议首图换成 GIF
## 三种练法怎么产生         ← 【保留】「两种建包方式」
## 快速开始                 ← 【保留】
## 配置模型                 ← 【保留】厂商表很好
## 配置场景配图（可选）       ← 【保留】
## 五种卡片怎么练           ← 【保留】核心方法章节
## 数据、备份与恢复          ← 【保留】
## 架构                     ← 【新增】目录树已有（第 371-396 行），补一张数据流 SVG
## 理论 → 代码映射           ← 【新增小节】摘要 THEORY.md，这是项目的差异化护城河
## 出问题了怎么办           ← 【保留】
## 路线图 / 已知限制         ← 【保留】
## License
```

**物料清单**：

| 位置 | 物料 | 说明 |
|---|---|---|
| 标题下方 | **GIF（必需）** | 5 秒：翻面→评分→下一张，突出「键盘 1234 顺手评」的产品感 |
| 徽章行 | License / Python / CI / Release / Tests | **当前一个都没有**，补齐 5 个 |
| 架构节 | **数据流 SVG** | `prompts.py → pipeline.py → providers/ → srs.py` 的流向图 |
| 「理论→代码」节 | 1 张对照表 | 从 `docs/THEORY.md` 摘 5 条，证明这不是「套壳 AI 造卡器」 |

**中英双语组织**：**强烈建议双语**。理由：项目直接对标 `mnemorai` / `han-flash` / `anki_ai`（README 第 17-21 行已列出）——**这些竞品全在英文社区**。不打英文，等于在自己的竞品列表里主动缺席。

### 3.5 TideWatch —— 完整 README 改进大纲

现状：341 行，benchmark 表格 + 消融实验 + 已知限制，**学术味最足、说服力最强**；但无位图、无 TOC、英文只有描述一行。

```markdown
# TideWatch · 观潮  |  Explainable CIB Detection Engine
[徽章行：License | Python 3.10-3.13 | CI | Deps: PyYAML only]

> 一个可解释、可插拔、可迭代的网络水军与协同行为识别引擎。
> 不用 GPU，不用 API Key，不用数据库；核心依赖只有一个 PyYAML。
> **对手可以伪造身份，但很难伪造「各自独立」。**

[🖼 架构/输出示意图]   ← 新增：把 ASCII 架构图做成 SVG，并附一张 CLI 输出截图

**English** | 中文   ← 新增（现有描述已是双语，正文补齐即可）

## TL;DR
- `pip install -e ".[zh]"` → `python scripts/gen_sample.py` → `tidewatch scan … --evidence`
- 十信号三层：文本层 / 账号层 / 协同层，每条结论可追溯到规则+证据+分值

## 目录 (TOC)
## 为什么这样做             ← 【保留】核心设计哲学，建议提为独立章节（现为第 45 行）
## 快速开始                 ← 【保留】
## 实测效果（消融实验）      ← 【保留】**最强背书**，建议加一句「合成数据只证明原理，不证明真实准确率」的显眼提示
## 怎么微调（三种粒度）      ← 【保留】插件化示范极好
## 项目结构                 ← 【保留】
## 架构与数据流             ← 【新增】SVG 图，替换/补充 ASCII
## 合规边界                 ← 【保留】提为一级标题，这是这个项目最需要的免责说明
## 已知限制                 ← 【保留】7 条，诚实度是加分项
## 迭代清单                 ← 【保留】
## 开发 / License
```

**物料清单**：

| 位置 | 物料 | 说明 |
|---|---|---|
| 标题下方 | **SVG 架构图（必需）** | 现 ASCII 图直接转 SVG，可嵌入英文版复用 |
| 「实测效果」节 | **CLI 输出截图** | 现有文字输出块已是真数据，配一张终端截图更直观 |
| 徽章行 | License / Python / CI / Deps | 4 个已有，保持 |
| 「合规边界」节 | 保持红色警示 | 中文水军检测易被误读为「监控工具」，此节必须显眼 |

**中英双语组织**：**最应该双语的一个**。理由：仓库描述**作者自己已经写了中英双语**（`… | Explainable, pluggable, iterative engine…`），但正文 100% 中文 —— 这是一个**已经铺好一半的国际化动作**，只差 `README.en.md`。`chinese-nlp` / `simhash` / `bot-detection` 在国际社区是高频检索词，双语是纯增量收益。

### 3.6 中英双语的组织方式（三仓库通用）

**推荐方案：主文件中文 + `README.en.md` 英文 + 顶部语言切换行**

```markdown
<!-- README.md 顶部 -->
**中文** | [English](README.en.md)
```

```markdown
<!-- README.en.md 顶部 -->
[中文](README.md) | **English**
```

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| A. 单文件双语上下半 | 无需切换 | 文件过长，读者被迫跳过一半 | ❌ |
| B. `README.md` + `README.en.md` | 简单、GitHub 自动识别、易维护 | 两份内容可能漂移 | ✅ **推荐** |
| C. `docs/i18n/en/` 完整镜像 | 结构最清晰 | 对 3 个项目过重 | 暂不需要 |

**英文版写什么**：不是逐句翻译。英文版**只保留四块**——What it is（3 行）、Quick start（1 条命令）、Architecture（1 张图）、Limitations（诚实清单）。**不翻译「踩坑记录」和版本变更史**（那是中文社区的资产，翻译成本高、对英文读者价值低）。

**维护约定**：在中文 README 的「开发」节写一句 —— 「改了安装步骤 / 架构图 / 已知限制，请同步 `README.en.md`」，防止两份漂移。

---

## 4. 隐私与合规风险专项

### 4.1 🔴 风险总表

| 风险 | 位置 | 等级 | 证据 |
|---|---|---|---|
| **个人日记 / 成长档案公开** | `Self-Mind`（Public） | 🔴 **严重** | 见 4.2 |
| **个人 QQ 邮箱随 commit 公开** | 5 个仓库的提交元数据 | 🟠 中 | `git log -1 --format='%ae'` |
| **本地路径 / 凭证残留** | `Self-Mind/.obsidian/` | 🟡 低 | 见 4.4 |
| 硬编码密钥 | 7 个仓库 | 🟢 无 | 全仓库扫描未发现 `sk-` / `api_key="…"`；三个旗舰的 `.gitignore` 均已排除 `.env` / `*.key` / `config.json` |

> ✅ **好消息**：三个旗舰仓库（WingMan / Etude / TideWatch）的密钥管理是**规范的**。`.env.example` 只有空占位（实测 `LLM_API_KEY=` 等全为空）；`WingMan/backend/tests/test_privacy_pseudonyms.py` 甚至写了一条**隐私守卫测试**，禁止仓库内出现真人姓名与真实邮箱。问题出在**作者对这个守卫的约束范围只覆盖了 WingMan 一个仓库**，其余仓库没有同等防护。

### 4.2 🔴 Self-Mind 专项（最高优先级）

**内容类别与数量统计**（按需求：只报类别与数量，不摘抄任何原文）：

| 内容类别 | 位置 | 数量 | 敏感度 |
|---|---|---|---|
| 每日日记（按日期命名） | `日志/` | **50 个 md**（2026-08 ~ 2026-10） | 🔴 高 |
| 个人成长档案 / 长期计划 / 目标 | `全流程报告/成长-军师/` | **4 个 md** | 🔴 高 |
| 成长军师系统（索引/任务复盘/进度台账） | `军师/` | **3 个 md** | 🔴 高 |
| 私人随笔 / 生活感想 | `快记、随笔/` | **2 个 md** | 🟠 中高 |
| **小计（个人隐私类）** | — | **≈ 59 个 md** | 🔴 |
| 技术学习笔记（AI / Office / Windows / 开发 / 网络 / 计算机理论） | `手艺/` | 95 个 md | 🟢 可公开 |
| 读书笔记 | `书/` | 5 个 md | 🟢 可公开 |
| 人造语言学习笔记 | `语言/` | 2 个 md | 🟢 可公开 |
| 项目全流程报告（Etude / WingMan / TideWatch 等） | `全流程报告/项目报告/` | 6 个 md | 🟠 中（含项目细节） |
| 方法与经验 | `全流程报告/方法与经验/` | 6 个 md | 🟠 中（其中 1 个含 QQ 邮箱原文） |
| 诊断与杂项 | `全流程报告/诊断与杂项/` | 8 个 md + 3 个选款文件 | 🟡 低（含消费决策记录） |
| 参考模板 | `参考模板/` | 1 个 md | 🟢 |
| **附件（图片）** | `图片、附件/` | **432 个文件**（423 png / 7 jpg / 1 gif / 1 jpeg） | 🟠 **未知** |

**风险判定**：

1. **仓库为 Public**（WebFetch 确认账户页标注 `Public`），任何人对 669 个文件可读、可 fork、可通过 Google 检索到。
2. **`图片、附件/` 的 432 个文件无法安全定性**：其中 9 个是 `jpg/jpeg/gif`（可能是照片或截图），423 个 png 多为粘贴的屏幕截图，但**无法排除其中含个人信息（聊天截图、证件、账单、位置）**。这一项本身就构成「必须人工复核」的理由。
3. **仓库无 `.gitignore`、无 LICENSE、无 README** —— 说明建立时未做任何「公开化」的准备，属于**误操作式公开**，而非有意发布。
4. **最强烈的信号**：该仓库被 **pin 在第 2 位**、且是**仓库列表默认第一**（更新最频繁，Oct 12）。这意味着作者是**有意识地在展示它**，却不了解它的暴露面 —— 这不是「藏着的小秘密被泄露」，而是「把保险箱摆在了门口」。

**建议动作（按优先级）**：

| 顺序 | 动作 | 说明 |
|---|---|---|
| **1（今天）** | **整个仓库转 Private** | Settings → Danger Zone → Change visibility → Private。**这一步立刻止损**，不需要任何技术操作 |
| **2（今天）** | **从 Pin 与 Profile 移除** | 转私有后 Pin 会自动消失；同时确认 Profile README 不再引用它 |
| **3（本周）** | **人工复核 `图片、附件/` 432 个文件** | 只做一件事：判断有没有需要永久删除的内容。这是唯一无法用命令替代的步骤 |
| **4（决定后）** | **拆分成「私有日记库 + 公开知识库」** | 只把 `手艺/`(95) + `书/`(5) + `语言/`(2) + `参考模板/`(1) 抽成新的公开仓库 `notes`；个人内容留在私有库。**这样既止损又保住了 103 篇有价值的技术笔记** |
| **5（若要坚持公开清洗）** | **按 4.5 重写历史** | 仅当明确要「清干净后再公开」时才做；否则第 1 步已经足够 |

### 4.3 🟠 commit 元数据邮箱泄露

**实测证据**：

| 仓库 | `git log -1 --format='%an <%ae>'` 结果 |
|---|---|
| `Data-Structures-and-Algorithms` | `whyao56 <2160444959@qq.com>` |
| `Python-Self-Learn` | `whyao56 <2160444959@qq.com>` |
| `Self-Mind` | `whyao56 <2160444959@qq.com>` |
| `TideWatch` | `Whyao <2160444959@qq.com>` |
| `frontend-learning` | `whyao56 <2160444959@qq.com>` |
| `WingMan` | `whyao56 <whyao56@users.noreply.github.com>` ✅ |
| `Etude` | `Whyao <190252643+whyao56@users.noreply.github.com>` ✅ |

**问题**：`2160444959@qq.com` 是**个人 QQ 号 + 邮箱**，随每个 commit 页公开可查。**WingMan / Etude 已正确使用 GitHub noreply 邮箱**，说明作者知道怎么做 —— 只是另外 5 个仓库没做。

**建议动作**：
1. **GitHub 全局设置**：Settings → Emails → 勾选 `Keep my email addresses private` + `Block command line pushes that expose my email`。这一步**防止未来**再泄露。
2. **本机 git 配置**（对以后所有新仓库生效）：
   ```bash
   git config --global user.email "whyao56@users.noreply.github.com"
   git config --global user.name "Whyao"
   ```
3. **历史邮箱**：如果介意旧提交里还印着 QQ 邮箱，需要重写历史（见 4.5）。**权衡**：QQ 号本身不是高敏信息（不像身份证/手机号），如果 `Self-Mind` 转私有 + 全局设置已做，**可以接受历史保留**——把精力放在第 1 项而不是历史清洗上。

### 4.4 🟡 `.obsidian/` 配置残留

| 文件 | 发现 | 风险 |
|---|---|---|
| `.obsidian/plugins/obsidian-git/data.json` + `.data.json.bak.20261001` | 仅含插件设置；`workspace.json` 中**未发现本机绝对路径**（`grep -oE "[A-Za-z]:[\\\\/]…"` 返回空） | 🟢 低 |
| `.obsidian/plugins/copilot/data.json` | 包含 `userId`、`isPaidUser`、`_keychainVaultId`（`caa7a120`）等账号元数据；**所有 `*ApiKey` 字段实测为空**（密钥存在操作系统钥匙串，未落盘） | 🟡 低 |
| `.obsidian/plugins/copilot/main.js` | 第三方插件源码被打包提交 | 🟡 低（无功能影响，但属于「不该进仓库的构建产物」） |

**结论**：`.obsidian/` 未泄露密钥或本机路径，但**属于「本机配置不该进公开仓库」的典型**。拆分仓库时应把 `.obsidian/` 加进 `.gitignore`。

### 4.5 如果坚持「清历史后再公开」：具体命令与权衡

> ⚠️ **先读这段再动手**：历史重写能清理**代码托管方**的副本，但**不能追回**已经被 fork / clone / star / 快照（Wayback Machine、搜索引擎缓存）的内容。**如果内容是真正的个人隐私，正确的心态是「视为已泄露」+ 止损，而不是「删干净当没发生」。** 这也是为什么 4.2 的第 1 步（直接转 Private）优先于历史清洗。

**方案对比**：

| 方案 | 工具 | 适用场景 | 风险 |
|---|---|---|---|
| **A. 直接转 Private** | GitHub 设置 | ✅ **绝大多数情况的最优解** | 无。历史原样保留在私有库，随时可查 |
| **B. 拆分后清历史再公开** | `git filter-repo` | 只想公开技术笔记、且要重开公开库 | 中。会改写全部 commit hash |
| **C. 单目录清除** | `git filter-repo --invert-paths` | 只想从现有库删掉几个目录 | 中。同上 |
| **D. BFG** | `bfg.jar` | 大仓库、只删大文件/密码 | 中。需 Java，功能比 filter-repo 窄 |

**方案 C 具体操作（清除私密目录并重写历史）**：

```bash
# 0. 先装 git-filter-repo（需要 Python 3.5+）
pip install git-filter-repo

# 1. 做一份完整镜像克隆（filter-repo 会拒绝在有未推送改动的仓库上操作）
git clone --mirror https://github.com/whyao56/Self-Mind.git selfmind-mirror.git
cd selfmind-mirror.git

# 2. 从所有历史中删除私密目录（--invert-paths = 保留「除下列路径"fs 外的所有内容）
git filter-repo \
  --path '日志/' \
  --path '军师/' \
  --path '全流程报告/成长-军师/' \
  --path '快记、随笔/' \
  --invert-paths

# 3.（可选）同时把历史提交邮箱统一改成 noreply，消除 QQ 号
git filter-repo --email-callback '
  return email if email.endswith(b"users.noreply.github.com") else b"whyao56@users.noreply.github.com"
' --force

# 4. 检查结果：私密目录应已从所有历史中消失
git log --all --oneline | head
git log --all --diff-filter=D --name-only | grep -E "日志|军师|快记" | head

# 5. 强推回 GitHub（会改写远端历史）
git push --force --all
git push --force --tags
```

**方案 D（BFG）备选**：

```bash
java -jar bfg.jar --delete-folders 日志 --delete-folders 军师 \
                  --delete-folders '快记、随笔' --no-blob-protection selfmind-mirror.git
cd selfmind-mirror.git && git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

**重写历史后的收尾**（缺一步都等于没删干净）：

| 步骤 | 命令 / 动作 | 为什么必须做 |
|---|---|---|
| 1 | 强推 `--force --all` + `--force --tags` | 否则旧对象仍在远端 |
| 2 | 联系 GitHub Support 请求清理悬空对象 | 重写后的旧 commit 在 GitHub 侧可能仍可通过 hash 访问一段时间 |
| 3 | 通知已有 fork / copy | **你删不掉别人的副本** —— 这一条决定了「删历史」永远不是完整方案 |
| 4 | 若曾泄露凭证 → **立刻轮换密钥** | 本仓库未发现凭证，但方法论要记住 |
| 5 | 复核 `图片、附件/` | 图片无法用 `--path` 精确排除时，宁可整库转私有 |

---

## 5. 作品集叙事

### 5.1 最适合打的标签

三个候选标签的评估：

| 候选标签 | 支撑证据 | 评估 |
|---|---|---|
| **A. 本地优先的 AI 应用开发者** | WingMan（零 Key 跑通 + Mock/云/Ollama 三档切换 + 隐私边界文档）、Etude（本地数据目录 + Edge TTS + 单文件前端零构建）、TideWatch（零 GPU 零 Key 零数据库） | ⭐ **最强**｜三个项目共享同一套高度一致的工程哲学，是**可被记住的差异化定位** |
| B. 中文 NLP 工程师 | TideWatch（分词/抗规避折叠/SimHash/AC 自动机/中文停用词） | ⭐⭐ 强，但只有 1 个项目支撑，单点 |
| C. 效率工具作者 | WingMan（聊天参谋）、Etude（语言训练器）都是「给自己用的工具」 | ⭐ 中等，偏生活方式、不够技术化 |

**结论：主打 A，「本地优先的 AI 应用开发者」，以 B（中文 NLP）作为技术纵深佐证。**

**为什么是 A**：三个旗舰仓库反复出现同一组设计信条——「本地优先」「零 Key 可跑通」「诚实标注没做什么」（Etude 有 `STATUS.md`、WingMan 有 14 条踩坑、TideWatch 有 7 条已知限制）。**这种一致性在个人账号里非常罕见，是最值得强化的记忆点。** 一个程序员能写出「没做什么」比写出「做了什么」更能证明工程成熟度。

**叙事线（Profile README 主线）**：
> 「我做本地优先的 AI 工具：数据不出本机、零 Key 可跑通、并且老实告诉你哪里还没做好。」

### 5.2 三条可执行的「作品集提升动作」（含验收标准）

| # | 动作 | 具体做法 | 验收标准 |
|---|---|---|---|
| **1** | **止损 + 重建首屏信任** | ① `Self-Mind` 转 Private；② 归档 2 个空仓库；③ Pin 顺序改为 WingMan → Etude → TideWatch；④ 新建 Profile README | ① 打开 `github.com/whyao56` **首屏看不到任何个人日记痕迹**；② 仓库列表从 9 个降到 ≤ 6 个；③ 打开首页 10 秒内能说出「这人是做本地 AI 工具的」；④ 无描述仓库数 = 0 |
| **2** | **给三个旗舰补英文入口** | 每个仓库新增 `README.en.md`（只含 What/Quick start/Architecture/Limitations 四块），正文顶部加语言切换行 | ① 3 个 `README.en.md` 存在且渲染正常；② 每个英文版**首屏能完整看懂「这是什么 + 怎么跑」**；③ 英文版不再出现「双通道语音转写」这类已下线功能 |
| **3** | **把「学习笔记」转成「学习轨迹」** | 4 个笔记仓库合并为 1 个 `dev-notes`（或挑 1 个最好的），写一份 README：学习路线 + 时间线 + 「学了→用在哪」对照表 | ① 合并后仓库数 ≤ 2；② README 里有至少 3 条「笔记 → 旗舰模块」的映射（例：SQLite 练习 → WingMan `memory/`）；③ 删除描述里的「DeepSeek V4.x 指导学习」字样 |

> **加分动作（不在三条之内，但收益高）**：给 WingMan 补一个 8 秒 GIF、给 Etude 补 5 个徽章、给 TideWatch 的 ASCII 架构图转 SVG。这三件事各 15-30 分钟，直接提升首屏专业感。

---

## 6. 优先级排序 Checklist（投入 vs 收益）

按「投入时间 ÷ 收益」从高到低排序。**前 5 项合计 ≤ 1 小时，能解决 80% 的问题。**

| # | 动作 | 投入 | 收益 | 收益/投入 | 关联风险 |
|---|---|---|---|---|---|
| 1 | `Self-Mind` → **转 Private** | 2 分钟 | 🔥🔥🔥🔥🔥 | ★★★★★ | D2 / 隐私 🔴 |
| 2 | 归档 `git-learning-journal` + `my-first-repo` | 5 分钟 | 🔥🔥🔥🔥 | ★★★★★ | D3 |
| 3 | GitHub 全局设置：邮箱私有 + 阻止暴露邮箱的推送 | 3 分钟 | 🔥🔥🔥🔥 | ★★★★★ | 隐私 🟠 |
| 4 | 重排 Pin：WingMan → Etude → TideWatch | 3 分钟 | 🔥🔥🔥🔥 | ★★★★★ | D1 |
| 5 | 新建 Profile README（用 1.3 的骨架） | 20 分钟 | 🔥🔥🔥🔥🔥 | ★★★★★ | D5 |
| 6 | WingMan：删掉 `whisper` / `asr` topics，描述去掉「语音转写」 | 3 分钟 | 🔥🔥🔥 | ★★★★★ | D7 |
| 7 | 三个旗舰各加语言切换行 + 建 `README.en.md` 空文件占位 | 10 分钟 | 🔥🔥🔥 | ★★★★☆ | D6 |
| 8 | WingMan：README 顶部加 TL;DR + TOC，版本说明折叠 | 25 分钟 | 🔥🔥🔥 | ★★★★☆ | 首屏过长 |
| 9 | Etude：补 5 个徽章（License/Python/CI/Release/Tests） | 15 分钟 | 🔥🔥🔥 | ★★★★☆ | 无徽章 |
| 10 | TideWatch：ASCII 架构图 → SVG | 30 分钟 | 🔥🔥🔥 | ★★★★☆ | 无位图 |
| 11 | 三个旗舰各录一个 5-8 秒 GIF，放在标题下方 | 1.5 小时 | 🔥🔥🔥🔥 | ★★★☆☆ | 无 GIF |
| 12 | 写完 WingMan 的 `README.en.md` 正文（四块内容） | 1 小时 | 🔥🔥🔥🔥 | ★★★☆☆ | D6 |
| 13 | 4 个笔记仓库合并为 `dev-notes`，写学习路线 README | 2 小时 | 🔥🔥🔥 | ★★★☆☆ | D4 |
| 14 | 人工复核 `Self-Mind/图片、附件/` 432 个文件 | 1 小时 | 🔥🔥🔥🔥 | ★★★☆☆ | 隐私 🟠 |
| 15 | Etude / TideWatch 的 `README.en.md` 正文 | 各 1 小时 | 🔥🔥🔥 | ★★☆☆☆ | D6 |
| 16 | 若坚持公开：`git filter-repo` 清洗 `Self-Mind` 历史 | 1 小时 + 风险 | 🔥🔥 | ★★☆☆☆ | 见 4.5 |

**执行批次建议**：

- **第 1 批（今天，≤ 35 分钟）**：#1 - #5。**这一步完成，账号第一印象从「★★☆☆☆」直接到「★★★★☆」**。
- **第 2 批（本周，≤ 3 小时）**：#6 - #11。补齐旗舰仓库的展示细节。
- **第 3 批（本月）**：#12 - #16。国际化与学习笔记整合。

---

## 7. 附：评审所用证据索引

| 结论 | 证据来源（绝对路径 / 命令） |
|---|---|
| Profile 无 README、Pin 顺序、Bio | `WebFetch https://github.com/whyao56` |
| 9 个仓库、描述、topics、排序 | `WebFetch https://github.com/whyao56?tab=repositories` |
| Self-Mind 内容类别与数量 | `find Self-Mind -name "*.md"`、`ls Self-Mind/日志/`、`ls Self-Mind/全流程报告/*/`、`ls Self-Mind/军师/`、`find "Self-Mind/图片、附件" -type f \| wc -l` |
| Self-Mind 无 README / LICENSE / .gitignore | `ls Self-Mind/ \| grep -iE "readme\|license\|gitignore"` |
| 邮箱泄露 | `git -C <repo> log -1 --format='%ae'` |
| 无硬编码密钥 | 全仓库 `grep -rniE "(sk-[a-zA-Z0-9]{20,}\|api_key\s*=\s*[\"'][^\"']{15,})"` |
| WingMan 无残留 ASR 代码 | `grep -rn "asr\|whisper" WingMan/backend/app/` → 空 |
| WingMan 隐私守卫测试 | `WingMan/backend/tests/test_privacy_pseudonyms.py` |
| 旗舰仓库 CI / LICENSE / 截图 | `ls <repo>/.github/workflows/`、`ls <repo>/LICENSE`、`ls WingMan/docs/images/`、`ls Etude/docs/images/` |
| `.obsidian` 无密钥落盘 | `python -c "json.load(open('.obsidian/plugins/copilot/data.json'))"` → 各 `*ApiKey` 为空 |

### 附注：本次评审的两个边界

1. **克隆为 `--depth 1`**：`git rev-list --count HEAD` 在各仓库均返回 1，**历史提交未纳入分析**。因此「历史中是否曾包含已删除的敏感内容」**未经验证**；第 4.5 节的历史清洗建议基于「假设历史可能含敏感内容」的保守立场。
2. **`图片、附件/` 的 432 个文件未做内容识别**：仅统计了文件类型与数量。是否含个人信息**需人工复核**，这也是第 4.2 节把它列为「必须人工处理」的原因。
