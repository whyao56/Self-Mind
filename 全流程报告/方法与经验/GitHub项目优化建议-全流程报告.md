---
tags: [领域/方法, 类型/报告]
评审日期: 2026-10-13
评审对象: github.com/whyao56（9 个公开仓库）
评审方式: 三专家并行评审 + 主理人交叉验证
---

# GitHub 项目优化建议 · 全流程报告

**评审对象**：`github.com/whyao56` 全部 9 个公开仓库
**评审方式**：软件团队三位成员并行评审（架构师 / QA 工程师 / 产品经理）+ 主理人独立交叉验证
**方法与口径**：所有仓库本地浅克隆后**静态阅读**源码，未执行测试套件、未安装依赖；结论中的行号均为实际读到的代码位置；无法确认的项集中列在第 9 节。

---

## 0. 一页结论

**一句话**：这是一批「工程质量远好于账号呈现」的作品。真正的短板不是代码水平，而是 **1 个隐私风险 + 2 个正确性/成本 bug + 3 个巨型文件 + 零覆盖率 + 账号首页叙事**。

| 维度 | 现状评分 | 结论 |
|---|---|---|
| 旗舰工程质量 | ★★★★★ | 三个旗舰有 CI、有 Release、测试:代码比 0.46–0.59、637 个测试函数里假测试几乎为零 —— **明显高于个人账号平均水准** |
| 代码架构 | ★★★☆☆ | TideWatch 达 A 级；WingMan / Etude 均 B-，各有结构性技术债 |
| 测试与 CI | ★★★★☆ | TideWatch A / Etude A- / WingMan B+；**三项目零覆盖率、零 pre-commit**，且 WingMan CI 与产品形态错配 |
| 开源呈现 | ★★☆☆☆ | 旗舰 README 内容极扎实但**全中文、无英文入口**；账号无 Profile README；仓库平铺无主线 |
| 隐私与合规 | ★☆☆☆☆ | **`Self-Mind`（Public）含约 59 个个人日记/成长档案 + 432 个附件**；5 个仓库 commit 元数据泄露 QQ 邮箱 |

**最该先做的三件事**：
1. 🔴 **把 `Self-Mind` 转 Private**（今天，2 分钟）→ 见 2.1
2. 🟠 **修 WingMan 的 SQLite 外键失效**（半天）→ 见 3.1
3. 🟡 **给 WingMan / Etude 补 `pyproject.toml`**（半天）→ 见 5.3，这是一切"可复现"的地基

---

## 1. 全景盘点

| 仓库 | 类型 | 体量 | 架构 | 质量 | 可见性建议 |
|---|---|---|---|---|---|
| **WingMan** | 旗舰 · 聊天僚机 | 118 文件 / 31.6k 行 | B- | B+ | 保持 Public，补英文 README |
| **Etude** | 旗舰 · 词汇训练器 | 79 文件 / 18.7k 行 | B- | A- | 保持 Public，补英文 README |
| **TideWatch** | 旗舰 · 水军识别引擎 | 55 文件 / 6.5k 行 | **A** | **A** | 保持 Public，补英文 README + 视觉素材 |
| **Self-Mind** | ⚠️ 个人知识库 | 640 文件 / 182 md | — | — | 🔴 **立即转 Private** |
| frontend-learning | 学习笔记 | 25 文件 | — | — | 并入 `dev-notes` |
| Data-Structures-and-Algorithms | 学习笔记 | 24 文件 | — | — | 并入 `dev-notes` |
| Python-Self-Learn | 学习笔记 | 47 文件 | — | — | 并入 `dev-notes` |
| git-learning-journal | 空壳 | — | — | — | 归档或删除 |
| my-first-repo | 空壳 | — | — | — | 归档或删除 |

> **口径说明**：你的账号实际有 **9 个**公开仓库（比最初的 7 个多出两个空壳）。三个旗舰的**工程质量本身不是问题** —— 评审中发现的全部问题都不影响"作品值得看"这个判断，只影响"代码能活多久"。

---

## 2. 🔴 立即行动（今天完成，合计 < 30 分钟）

### 2.1 `Self-Mind` 转 Private —— 唯一有时效性的一件事

**实测事实**（主理人独立复核过）：

| 目录 | 内容 | 数量 |
|---|---|---|
| `日志/` | 按日期的个人日记（如 `2026-08-03.md`） | **50** |
| `全流程报告/` | 含个人成长/军师档案 | 22 |
| `军师/` | 进度台账、每日任务复盘 | **3** |
| `快记、随笔/` | 随手记录 | 2 |
| `图片、附件/` | 图片附件（内容未定性） | **432** |

该仓库同时**无 README、无 LICENSE、无 `.gitignore`**，并在账号首页被 pin 在第 2 位、是仓库列表默认第一项。基本可以判定属于误操作式公开。

**动作（按顺序）**：
1. `Settings → Danger Zone → Change visibility → Make private`（2 分钟，立刻止损）
2. 取消 Pin（30 秒）
3. 人工复核 432 个附件的性质，再决定去留
4. 若要「保住技术笔记、藏起日记」→ 拆成两个仓库：**私有日记库** + 公开知识库（可保住 `手艺/` 95 篇技术笔记 + `书/`、`语言/`）
5. 仅当坚持公开时才做历史清洗（`git filter-repo` / BFG）

> ⚠️ **重要权衡**：历史重写**追不回已被 fork / 缓存 / 搜索引擎收录的副本**。真隐私应当「视为已泄露 + 止损」，而不是「删了历史就没事」。所以第 1 步的转私有是必须的，第 5 步是可选的。

### 2.2 账号"黄金 30 秒"三件事

| 动作 | 具体做法 | 耗时 |
|---|---|---|
| 建 Profile README | 新建同名仓库 `whyao56/whyao56`，写「我是谁 + 三个旗舰 + 一句话各讲清楚」 | 20 分钟 |
| 重排 Pin | 顺序改为 **WingMan → Etude → TideWatch** | 2 分钟 |
| 归档 2 个空壳 | `git-learning-journal` / `my-first-repo` 设为 Archive 或删除 | 3 分钟 |

Profile README 可直接用这个骨架：

```markdown
# Whyao · 本地优先的 AI 工具开发者

做能在自己电脑上跑、不依赖云服务的 AI 工具。

## 三个作品
- **[WingMan](link)** — 把 QQ/微信聊天记录变成可检索记忆，实时分析情绪与意图，给出候选回复推演。
- **[Etude](link)** — 给一个词，生成 8 条不同语境的例句，铺成五种练法（阅读/听力/口语/打字/造句）。
- **[TideWatch](link)** — 可解释、可插拔的网络水军与协同行为识别引擎。

## 我在学什么
数据结构与算法 / Python / Web 前端 —— 笔记都在 [dev-notes](link)。
```

### 2.3 commit 元数据里的 QQ 邮箱

**5 个仓库**（Data-Structures-and-Algorithms、Python-Self-Learn、Self-Mind、TideWatch、frontend-learning）的提交历史里带真实 QQ 邮箱 `2160444959@qq.com`。WingMan 与 Etude 已正确使用 GitHub noreply 地址 —— 说明你会做，只是没做全。

```bash
# 全局设置，只影响今后提交（推荐先做这个）
git config --global user.email "whyao56@users.noreply.github.com"

# 想清理历史，需逐仓库 rebase，成本高且会改变所有 commit hash
# 建议：除非仓库要公开投递简历，否则不值得做
```

> 这一条**不影响功能**，是隐私卫生问题，优先级低于 2.1 但高于所有代码优化。

---

## 3. 🟠 第一周：止血 —— 正确性与成本

这两条是**改错时最贵**的问题，先修它们。

### 3.1 【P0 · 半天】WingMan：SQLite 外键在运行期全程失效

**现象**（`WingMan/backend/app/store.py`）：

```python
# 408-420 行 —— conn() 每次新建连接，只设了 row_factory
@contextmanager
def conn(self) -> Iterator[sqlite3.Connection]:
    with self._lock:
        c = sqlite3.connect(self.db_path, timeout=15.0)
        c.row_factory = sqlite3.Row      # ← 没有 PRAGMA foreign_keys
        ...

# 422-427 行 —— init() 里这行用完即随连接关闭失效
with self.conn() as c:
    c.execute("PRAGMA foreign_keys = ON")   # ← 连接一关就没了

# 804-806 行 —— delete_chat 只能自己临时补一句兜底
with self.conn() as c:
    c.execute("PRAGMA foreign_keys = ON")
```

**为什么是问题**：SQLite 的 `foreign_keys` 是**连接级**开关且**默认关闭**。schema 里大量声明了 `ON DELETE CASCADE`，但 `conn()` 建的新连接不带这个开关，于是**除了手工补 PRAGMA 的那几处，其余任何删除路径都不会触发级联**，会静默留下孤儿行（`messages` / `embeddings` / `engine_runs` / `activity_log`）。这类问题不会报错，只会让数据慢慢烂掉 —— 而且越晚发现越难修，因为已有脏数据。

**改法**：在 `conn()` 里统一设置，一处修全局好。

```python
@contextmanager
def conn(self) -> Iterator[sqlite3.Connection]:
    with self._lock:
        c = sqlite3.connect(self.db_path, timeout=15.0)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")   # ← 新增
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()
```

然后把 `init()` 第 426-427 行和 `delete_chat()` 第 806 行、第 1371 行的"临时 PRAGMA"删掉（已冗余）。

**验收标准**：新增测试 —— 删除一个会话后，断言 `messages` / `embeddings` / `engine_runs` / `activity_log` 中**无孤儿行**；既有 22 个测试全绿。

### 3.2 【P0 · 半天到一天】Etude：配图线程池导致成本泄漏

**现象**（`Etude/backend/app/providers/images.py` 的 `_provide_both`）：每张图都新建一个线程池，并发发起「检索」和「画图」两路，**败者的画图线程无法取消、会跑完**。

**为什么是问题**：即使检索已经命中、画图结果被丢弃，画图请求仍然会完整执行并**烧掉真实额度/费用**。属于"用户看不见但每月都在付"的泄漏。

**改法**：① 池改为共享（模块级或注入）；② 逻辑改为「检索优先，检索失败才发起画图」；③ 若确实要 `both` 语义，则在配置里明确标注成本。

**验收标准**：`test_image_parallel.py` 通过；新增用例用 stub **计数**，断言「检索命中时**不**发起画图请求」。

### 3.3 【P1 · 半天】WingMan：LLM 调用无重试

`Etude/backend/app/providers/llm.py` 的指数退避重试写得**比 WingMan 的 llm 层更健壮**。建议反向搬运：为 WingMan 的 `complete_json` 加瞬时错误（429 / 5xx / 超时）的指数退避。

**验收标准**：新增用例 —— stub 先返回一次 429 再成功，断言发生重试且最终拿到结果。

### 3.4 【P2 · 半天】低风险清理

- 抽 `net.py`：`_trust_env_for` 这段私有逻辑在 WingMan 里被**复制了 3 份**，合并为一处。
- Etude `images.py` 拆包（纯移动，行为零变化）。

**验收标准**：`grep` 确认无重复定义；测试全绿。

---

## 4. 架构与代码优化

### 4.1 成熟度对比

| 维度 | WingMan | Etude | TideWatch |
|---|---|---|---|
| 分层清晰度 | B- | B- | **A** |
| 模块耦合 | **C+** | **C+** | **A** |
| 依赖管理 | B | C | **A** |
| 配置管理 | B+ | B | **A** |
| 可扩展性 | B- | C | **A** |
| 错误处理 | B- | B+ | **A** |

**结论**：TideWatch **全项 A**，是三个项目里工程实践的标杆；从单文件体量看 WingMan 最需要重构，从分层性质看 Etude 的耦合更"结构性"。

### 4.2 三个结构性技术债

**① 巨型文件 —— 建议按周分两批拆**

| 项目 | 文件 | 行数 | 拆法 |
|---|---|---|---|
| WingMan | `backend/app/store.py` | **1940** | 单类约 90 方法的 god object，拆为 `store/` 包（门面转发），`__init__.py` < 200 行、各子模块 < 400 行 |
| WingMan | `scripts/preflight.py` | **1679** | 按子命令拆包 |
| WingMan | `backend/app/collect/reader.py` | **1169** | 拆包 + 重导出，各子模块 < 300 行 |
| Etude | `backend/app/db.py` | **1204** | 拆为 `db/` 包，并把 SRS 领域逻辑（`grade_card` / `undo_grade` / `push_cards`）下沉到 `services/review.py` |
| Etude | `backend/app/api.py` | **870** | 拆为 `api/` 包 + `jobs.py` |
| Etude | `backend/app/providers/images.py` | **806** | 拆包 |
| 前端 | WingMan `frontend/index.html` / Etude `frontend/index.html` | **4653 / 4519** | 零构建是可接受的取舍，建议渐进抽取，不要一步上打包器 |

> **为什么拆文件排这么高**：这不是审美问题。`store.py` 被所有层直接依赖，是**全系统唯一的横切耦合点** —— 任何并行开发都会在这里撞车，任何测试都要拖起半个应用。拆开它，后面每一步都变便宜。

**② Etude：存储层混入领域逻辑**

`db.py` 里既有存储原语，也有 SRS 复习算法的流程编排（算法本体在 `srs.py`，编排却在 `db.py`）；同时 `api.py` 存在两处**反向穿透**：
- `api.py:804` —— 路由里直接写裸 SQL：`db.execute("UPDATE examples SET scene_image = ? WHERE id = ?", ...)`
- `api.py:661` —— 反向调用存储层私有函数：`db._loads(...)`

**改法**：裸 SQL 下沉为 `db.set_example_scene_image()` 之类的方法；`_loads` 提升为公共 API；SRS 编排移出存储层。

**③ TideWatch：两处"面向未来规模"的问题**

- `config.py:26` 的 `PROJECT_ROOT = parents[2]` 让引擎**无法作为普通 wheel 安装**（Dockerfile 只能靠 editable + 显式 COPY 绕过）。改法：资源改用 `importlib.resources`。
- `CoOccurrenceSignal` 做账号两两比较是 **O(A²)** 且无上限。改法：topic 倒排剪枝。

### 4.3 跨项目共性清单（一次学会，三处受益）

| 编号 | 问题 | 涉及项目 | 优先级 |
|---|---|---|---|
| C-4 | LLM 调用缺重试退避 | WingMan | P1 |
| C-5 | **无 schema 迁移机制** —— 建议引入 `schema_meta(version)` + 有序迁移列表 | WingMan / Etude | P1 |
| C-6 | CORS 过于宽松 | WingMan / Etude | P2 |
| C-8 | **无 `pyproject.toml`**，不能 `pip install` | WingMan / Etude | **P1** |
| C-9 | 密钥与业务数据存在同一个库的 `kv` 表里 | WingMan | P2 |
| C-10 | Etude 无锁定文件 | Etude | P2 |
| W-8 | 500 响应回显原始异常（可能含堆栈） | WingMan / Etude | P2 |
| W-3/W-6 | `list_chats` 是 1+3N 次查询；`async def` 内直接同步调用 store，阻塞事件循环 | WingMan | P1 |

> **一处对最初侦察的修正**：我最初判断「WingMan / Etude 根目录没有依赖声明」**不准确** —— 两者依赖都放在 `backend/` 下。WingMan 有 `backend/requirements.txt` + **`requirements.lock.txt`（54 行锁定集，CI 实际消费）** + `-desktop` / `-dev` 分层，**依赖管理其实做得不错**；Etude 的 `requirements.txt` 带上下界约束（很好的习惯）。真正的缺口是**都没有 `pyproject.toml`**、不能 `pip install -e .`，以及 Etude 没有锁定文件。

### 4.4 值得反向移植的 TideWatch 实践

1. **`pyproject.toml` + 可选 extras**（`[project.optional-dependencies]` 的 `zh` / `dev`）—— 直接照抄到 WingMan / Etude
2. **`make freeze` 生成锁定集**并被 CI 消费
3. **独立 lint job**（`ruff check src tests scripts eval`）
4. **CI 矩阵含多 Python 版本 × 可选依赖装/不装双跑**（验证降级路径真的能跑）
5. **配置优先级链** CLI `--set` > 环境变量 > YAML，且带**配置指纹**（可复现实验）
6. **新增信号 = 继承 + `@register` + 写一段配置，改 0 处引擎代码** —— 插件化的正确示范

---

## 5. 测试与 CI 优化

### 5.1 质量现状矩阵

| 维度 | WingMan | Etude | TideWatch |
|---|---|---|---|
| 测试文件数 | 21 | 14 | 9 |
| 测试代码行数 | 8,493 | 4,716 | 2,393 |
| 生产代码行数（Python） | 18,476 | 7,946 | 4,092 |
| **测试:生产 比** | 0.46 | **0.59** | 0.58 |
| 仅比 app 部分 | 0.56 | **0.79** | 0.74 |
| test 函数数（AST 实测） | 233 | **249** | 155 |
| **无断言的 test 函数** | **1**（调用的 helper 内含断言） | **0** | **0** |
| conftest / 夹具 | ❌ 无 conftest | ✅ 233 行，夹具丰富 | ✅ 190 行，`dataset` 夹具精心构造 |
| **覆盖率配置 / 门槛** | ❌ / ❌ | ❌ / ❌ | ❌ / ❌ |
| CI 跑测试 | ✅ | ✅（双 OS） | ✅（4×py + jieba 双跑） |
| **CI 跑 lint** | ❌（仅 `compileall` 语法检查） | ❌（装了 ruff 但 CI 不调用） | ✅ 独立 lint job |
| pre-commit | ❌ | ❌ | ❌ |
| CI 平台矩阵 | **仅 ubuntu** | ubuntu + windows | 仅 ubuntu |
| 依赖缓存 | ✅ | ✅ | **❌ 未开** |

**两个罕见的优点**（先说好的，因为这两点比多数个人项目强）：
- **637 个测试函数，无断言的空测试只有 1 个**，而这个还调用了带断言的 helper —— 也就是说**三项目都不存在"假测试"**。这是很不容易的。
- 测试:代码比 0.46–0.59 属于健康水位，Etude 单测密度最高（0.79）。

### 5.2 三个最硬的缺口

**① WingMan：CI 与产品形态错配（最高危）**

WingMan 是 **Windows 桌面程序**（`winapi.py` 389 行读进程内存、`clipboard.py` 528 行读剪贴板、`desktop.py` 613 行、PyInstaller 出包），但 `ci.yml:16` 只跑 `ubuntu-latest`。后果是双向的：

- `test_collect_offwindows.py:203 / 219` 的守卫被 `skipif(sys.platform != "win32")` 挂在 Windows 上 —— **在所有 CI 平台上永远不会执行**；
- Windows 专有能力（读内存、读剪贴板）**零真机覆盖**。

**改法**：CI 加 `windows-latest` job。参考 Etude —— 它已经做到了双 OS。

**② 三项目零覆盖率度量**

`grep -i coverage` 在三个仓库**全零命中**：无 `pytest-cov`、无 `.coveragerc`、无 `[tool.coverage]`。测试写了 8,493 行却**防不住退化**，因为没有任何东西会在覆盖率掉下去时报警。

**改法**：先度量、再设地板。

```toml
# backend/pyproject.toml（WingMan / Etude 新建，TideWatch 追加到现有文件）
[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*"]

[tool.coverage.report]
show_missing = true
# 先不设 fail_under，跑两周拿到真实基线后再设「当前值 - 5」
```

```yaml
# ci.yml 中测试步骤
- run: pip install pytest-cov
- run: pytest --cov --cov-report=xml --cov-report=term-missing
- uses: actions/upload-artifact@v4
  with: { name: coverage, path: coverage.xml }
```

**③ lint 关卡只有 TideWatch 达标**

WingMan 连 ruff 都没装（`requirements-dev.txt` 只有 pytest）；Etude 装了 ruff 但 CI 不调用（其 `requirements-dev.txt:15` 自述"没有强制 lint 关卡"）。建议三项目统一加 ruff，再补 `pre-commit`。

**附带点名（会被忽略的两处）**：
- WingMan `test_privacy_pseudonyms.py:117-120` 的隐私历史扫描，在 CI 的**浅克隆下恒为 skip** —— 形同废守卫。
- 最大无直测模块：WingMan `store.py`（1940 行，历史上出过"事实静默覆盖"bug）与 Etude `prompts.py`（433 行，零直测）。

### 5.3 落地路径（四周）

| 周 | 动作 | 产出 |
|---|---|---|
| W1 | 三项目加 `pytest-cov` + `[tool.coverage]`；CI 传 coverage.xml（**先不设门槛**）；WingMan 建最小 `pyproject.toml` | 拿到真实覆盖率基线 |
| W1 | WingMan CI 加 `windows-latest` + `lint` job；Etude CI 加 ruff job；TideWatch 补 `cache: pip` | 补上最硬的 CI 缺口 |
| W2 | 补 5 条 P0 测试（见详细报告的 §4 清单） | 核心链路有回归锚点 |
| W3 | 设 `--cov-fail-under`（基线 -5），核心模块单列更高门槛；三项目加 pre-commit | 冻结退化 |
| W4+ | 补 P1 清单；Etude 把 `ui_smoke.js` 接入 CI | 覆盖率稳步上行 |

> **双环境策略**：本地 Windows 开发 + Actions Linux 跑。注意用 `skipif` 显式标注平台假设，别让守卫测试变成"两边都不跑"的死代码 —— 这正是 WingMan 现在的坑。

---

## 6. 开源呈现优化

### 6.1 账号第一印象诊断

| 扣分项 | 证据 |
|---|---|
| Profile 无 README、无身份说明 | 打开账号页无任何自我介绍 |
| **最私密的仓库被 pin 在第 2 位** | `Self-Mind` 是仓库列表默认第一项 |
| 三个旗舰 README **全中文、无英文入口** | 国际社区完全看不到；TideWatch 的 topic 有 `chinese-nlp` / `simhash`，本该双语 |
| 旗舰与学习笔记、隐私库、空壳**平铺混放** | 9 个仓库无叙事主线 |
| **描述把加分项写成减分项** | 4 个学习仓库写着"DeepSeek V4.x 指导学习"—— 学习本身是加分项，这样写反而像作业 |
| WingMan 展示信息过期 | topics 仍含 `whisper` / `asr`、描述仍写"双通道语音采集转写"，但代码里已搜不到相关实现 |

### 6.2 仓库分级与处置

| 分级 | 仓库 | 处置 |
|---|---|---|
| **旗舰作品** | WingMan、Etude、TideWatch | 保持 Public，各补 `README.en.md` + 顶部语言切换；Pin 顺序 WingMan → Etude → TideWatch |
| **可用工具** | （暂无） | — |
| **学习笔记** | frontend-learning、Data-Structures-and-Algorithms、Python-Self-Learn | **合并为 1 个 `dev-notes`**，加一张「学了 → 用在哪」对照表，把作业感转成成长叙事 |
| **应私有 / 应归档** | Self-Mind、git-learning-journal、my-first-repo | 见 2.1 与 2.2 |

### 6.3 README 改进要点（三旗舰共性）

现有 README 内容**极其扎实**（WingMan 949 行、Etude 474 行、TideWatch 340 行，含 14 条踩坑记录），问题在**信息顺序和可达性**：

1. **首屏太长** —— 把版本/状态说明后移到底部，前 20 行只留「它是什么 + 解决什么问题 + 一张截图/GIF」
2. **补 GIF** —— 三个项目都缺首屏动图，这是转化率最高的一项
3. **补架构 SVG** —— 现有 ASCII 图换成/补一张 SVG
4. **加 TOC** —— 长 README 必须有目录
5. **加英文版** —— `README.en.md` + 顶部语言切换（推荐这个方案，比单文件双语更好维护）
6. **各自的差异化章节**：
   - WingMan → 新增「权限与隐私边界」小节（摘要 `COMPLIANCE.md` 的 3 条红线）—— 这是这个项目最需要主动说明的地方
   - Etude → 新增「理论 → 代码映射」小节（摘要 `THEORY.md`）—— 这是它真正的护城河
   - TideWatch → 「合规边界」提为一级标题；「实测效果」的消融实验表加一句显眼提示：**合成数据只证明原理，不证明真实准确率**（诚实度是加分项）

---

## 7. 30 天合并路线图

> 按 1 名开发者、每周 2–3 人日投入估算。每个动作都可独立成 commit。

### 第 1 周 —— 止血

| # | 动作 | 验收标准 |
|---|---|---|
| A1 | **W-2**：`conn()` 统一 `PRAGMA foreign_keys=ON`，删掉各处临时 PRAGMA | 删除会话后 `messages`/`embeddings`/`engine_runs`/`activity_log` 无孤儿行；22 个测试全绿 |
| A2 | **E-3**：`_provide_both` 改共享池 + 「检索优先、失败才画图」 | 新增用例断言检索命中时不发起画图请求 |
| A3 | **C-4**：为 WingMan `complete_json` 加指数退避 | 429 后重试并成功的用例通过 |
| A4 | 三项目加 `pytest-cov` + coverage 配置；WingMan CI 加 windows + lint job；Etude CI 加 ruff；TideWatch 补 `cache: pip` | CI 产出 coverage.xml；Windows job 真的跑起来 |
| A5 | 低风险清理：抽 `net.py`、`images.py` 拆包 | 行为零变化，测试全绿 |
| — | 🔴 `Self-Mind` 转 Private（若尚未做） | 仓库不可公开访问 |

### 第 2 周 —— 拆分巨型文件（第一批）+ 打包

| # | 动作 | 验收标准 |
|---|---|---|
| B1 | **W-1**：`store.py` 拆为 `store/` 包（门面转发） | 公共 API 签名不变；`__init__.py` < 200 行，各子模块 < 400 行 |
| B2 | **E-1**：`db.py` 拆包 + `services/review.py` 下沉 SRS 领域逻辑 | `db.grade_card` 等公共名不变；复习测试独立通过 |
| B3 | **C-8**：WingMan / Etude 各加 `pyproject.toml`（PEP 621，参照 TideWatch） | `pip install -e ".[dev]"` 成功；CI 改用它 |
| B4 | **C-10**：Etude 生成 `requirements.lock.txt` 并让 CI 消费 | CI 安装步骤改为锁定集 |
| B5 | 账号改造：Profile README + 重排 Pin + 归档 2 个空壳 | 首屏 30 秒能看到三个作品 |

### 第 3 周 —— 拆分（第二批）与并发

| # | 动作 | 验收标准 |
|---|---|---|
| C1 | **E-2**：`api.py` 拆包 + `jobs.py`；裸 SQL 下沉、`_loads` 提公共 | 路由数量不变；`test_api.py` / `test_edit_api.py` 全绿 |
| C2 | **W-3 + W-6**：`list_chats` 改单查询；消除事件循环内的同步 store 调用 | SQL 数从 1+3N 降为 1；`grep` 守卫禁止 `async def` 内出现 `.store.` |
| C3 | **E-4**：图片/语音按例句并行（并发度可配，默认 2–3） | 新增测试断言并发上限不被突破 |
| C4 | **W-7**：`reader.py` 拆包 | 各子模块 < 300 行，测试全绿 |
| C5 | 覆盖率设地板 + 三项目加 pre-commit | `--cov-fail-under` 生效；本地提交前自动拦截 |

### 第 4 周 —— 演进能力与安全

| # | 动作 | 验收标准 |
|---|---|---|
| D1 | **C-5**：引入 `schema_meta(version)` + 有序迁移列表 | 构造老库 fixture 能升到最新且幂等重跑安全 |
| D2 | **T-1 + T-2**：TideWatch 资源改 `importlib.resources` + 共现剪枝 | 非 editable 安装后 CLI 可跑；大账号集耗时下降 |
| D3 | **W-8 + C-6 + C-9**：异常回显改 `error_code + request_id`；CORS 收紧；密钥与业务库分离 | 内部异常响应不含堆栈；CORS 为具体 origin；密钥不再在业务库 |
| D4 | **W-8 收尾**：`preflight.py` 拆包；修正 WingMan 过期 topics/描述 | ruff + pytest 全绿；展示信息与功能一致 |
| D5 | 三个旗舰各加 `README.en.md`；4 个学习仓库合并为 `dev-notes` | 英文入口可用；学习笔记有「学了→用在哪」对照表 |

---

## 8. 你已有的优势（别改坏）

评审中确认的正向资产，优化时注意保留：

- ✅ **无硬编码密钥**：全仓库扫描未发现明文 `sk-*` / `api_key="…"`；三旗舰 `.gitignore` 均已排除 `.env` / `*.key` / `config.json`
- ✅ **WingMan 的 `.env.example` 写得非常规范** —— 变量分组、注释说明降级行为、明确"留空即用 Mock Provider"
- ✅ **Etude 的 CI 有独立 `secrets` 隐私红线 job**（扫 `sk-` 前缀 + `innerHTML` XSS 守卫）—— 建议 WingMan 照抄
- ✅ **WingMan 有隐私守卫测试** `test_privacy_pseudonyms.py`（扫真实姓名 + 提交邮箱），甚至有"守卫的守卫"反证测试
- ✅ **测试质量健康**：637 个 test 函数，假测试几乎为零
- ✅ **WingMan README 有 14 条踩坑记录** —— 这类内容对读者价值极高，别删
- ✅ **TideWatch 的消融实验表格 + 已知限制 7 条** —— 诚实度是它最强的说服力
- ✅ **WingMan 的 `requirements.lock.txt` + 分层 requirements** —— 依赖管理已超出个人项目平均水准
- ✅ **Etude 的 `requirements.txt` 带上下界约束** —— 好习惯
- ✅ **TideWatch 的插件化设计** —— 新增信号改 0 处引擎代码，是三个项目里最值得推广的架构模式

---

## 9. 待确认项（未编造，需实测）

1. **覆盖率数字** —— 本报告未运行测试套件，所有覆盖率为基于测试密度与代码比的**推断值**，须以 `pytest-cov` 实测为准。
2. **WingMan `routes_persons.py` / `routes_data.py` 是否真的 0 处引用** —— 基于模块名 grep，可能因测试走 TestClient（而非直接 import）而漏计；`test_persons.py`（767 行）大概率已通过 HTTP 覆盖这些路由，故未列为 P0。
3. **`scripts/preflight.py`（1,679 行）** —— `test_preflight.py`（627 行）是否覆盖其全部子命令路径，未逐条核对。
4. **Etude `ui_smoke.js` 的运行前置**（是否需 `cdb.js` / 浏览器）未深入，接入 CI 前需确认依赖。
5. **`Self-Mind` 的 432 个附件性质** —— 未做内容定性（隐私红线），需你人工复核。

---

## 附录：证据与详细报告索引

本次评审的三份详细报告（含逐条行号证据、完整代码示例、可套用骨架）：

| 报告 | 行数 | 内容 |
|---|---|---|
| `architecture-review.md` | 668 | 三项目架构诊断（WingMan 8 条 / Etude 6 条 / TideWatch 5 条）、共性清单 C-1~C-10、文件规模热点表、待确认项 |
| `qa-review.md` | 654 | 质量矩阵、三个 `ci.yml` 逐项体检 + 改进版完整示例、假测试扫描、18 行补测清单 + 3 个 P0 pytest 代码、覆盖率落地 |
| `portfolio-review.md` | 572 | 账号诊断（8 条扣分项）、四类分级、三旗舰完整 README 骨架、隐私与合规专项（含 `filter-repo` / BFG 命令）、16 项优先级 checklist |

详细报告的本地路径：
`C:/Users/HP/WorkBuddy/2026-10-13-11-45-56/deliverables/software-company/review/`

**评审方法与局限声明**：全部结论基于本地浅克隆的**静态阅读**，未执行测试套件、未安装依赖、未运行被测程序。因此覆盖率、性能和"功能是否真的能跑"这三类结论未经运行验证，已在第 9 节逐条标注。所有引用的行号均为实际读到的代码位置。
