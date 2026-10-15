# 代码与架构层面优化评审报告

**评审对象**：GitHub 用户 `whyao56` 的三个真实项目 — WingMan / Etude / TideWatch
**评审视角**：架构分层、模块耦合、巨型文件、并发与 IO、大模型调用层、数据存储与 schema 演进、安全与隐私、依赖管理与可复现构建
**评审方式**：全部结论基于对克隆仓库源码的实际阅读（`Read` / `Grep` / `Glob`）。每条问题均标注**文件名 + 行号**；无法确证之处显式标注「待确认」。
**克隆路径**：`gh-repos/{WingMan,Etude,TideWatch}` （只读分析，未做任何修改）

---

## 0. 方法与整体印象

| 维度 | WingMan | Etude | TideWatch |
|---|---|---|---|
| 语言 / 规模 | Python，~26969 行 / 118 文件 | Python，~14204 行 / 79 文件 | Python，~6485 行 / 55 文件 |
| 定位 | 聊天僚机（聊天记录→记忆→回复推演） | 词汇例句训练器（LLM 例句 + 五种练法） | 网络水军/协同行为识别引擎 |
| 形态 | FastAPI + 单文件前端（WebView2 桌面） | FastAPI + 单文件前端（WebView2 桌面） | 纯 CLI 库（src-layout） |
| 最大文件 | `backend/app/store.py` **1940 行** | `backend/app/db.py` **1204 行** | `signals/coordination.py` 330 行 |
| 测试文件数 | 22 | 13 | 8 |
| 依赖声明 | `backend/requirements{,-desktop,-dev}.txt` + `requirements.lock.txt` | `backend/requirements{,-dev}.txt` | `pyproject.toml`（PEP 621）+ `requirements.txt` |
| 注释风格 | 大量「为什么这么做」的取舍说明，信息密度高 | 同左，且带「上一个项目踩的坑」的迁移经验 | 精确、克制的工程注释 |

**总体判断**：
- **TideWatch 是三者中最成熟的工程**（A 级）。它在软件工程意义上是一个「教科书级」的可插拔分析引擎：src-layout、PEP 621 打包、三级配置覆盖、装饰器注册表、三层信号插件、可复现的实验指纹、`make` 驱动的标准工作流。它应当成为另两个项目的**参照实现**。
- **WingMan 是功能最丰富、但内核最臃肿的项目**（B 级）。它有全项目最好的「失败可解释」文案与迁移容错，但 `store.py` 是一个 1940 行、约 90 个方法的单一类，是三个项目中**单文件聚合度最高的横切点**，且存在多处分层穿透与重复逻辑。
- **Etude 的 provider 层写得比 WingMan 更好，但核心 db/api 层的耦合与职责混杂最严重**（B- / C+ 级）：`db.py` 把 SRS 领域逻辑混进了存储层，`api.py` 把全部路由、Pydantic 模型、后台线程池塞进一个模块。

**一句话结论**：TideWatch 做对了「边界」；WingMan 应该向它学习「拆边界」，Etude 应该向它学习「分清存储与领域」。

---

## 1. 总览：架构成熟度对比表

评分标准：**A** = 达到可复用库/工程标准；**B** = 结构合理但有明显技术债；**C** = 存在结构性风险，需优先整改。

| 维度 | WingMan | 等级 | Etude | 等级 | TideWatch | 等级 |
|---|---|---|---|---|---|---|
| **分层清晰度** | `adapters/api/collect/engine/llm/memory` 目录划分清晰，但 `store.py` 被所有层直接依赖，API 层有同步穿透事件循环 | **B-** | provider 层干净（`providers/{llm,images,tts}`），但 `db.py` 混入 SRS 领域逻辑、`api.py` 是应用god模块 | **B-** | `adapters / signals / scoring / pipeline / report` 职责单一，pipeline 只编排不判定 | **A** |
| **模块耦合** | 私有逻辑被复制 3 份（`_trust_env_for`）；API→Store 同步穿透；单类 1940 行 | **C+** | `api.py` 调用 `db._loads` 私有函数；连接为全局单例 + 全局锁 | **C+** | 信号通过注册表解耦、可通过配置注入子集做消融 | **A** |
| **依赖管理** | 有锁定集 + 分层 requirements，但**无 pyproject.toml**、非 src-layout | **B** | 有上下界约束（很好），但**无锁定文件、无 pyproject.toml** | **C** | `pyproject.toml` + 可选 extras + `make freeze` 生成锁 | **A** |
| **配置管理** | `.env` → SQLite kv 运行时覆盖，密钥读取掩码 | **B+** | `config.json` 深合并 + bootstrap 数据目录指针 | **B** | CLI `--set` > 环境变量 > YAML，且带 **配置指纹** | **A** |
| **可扩展性** | 有 adapter 注册表，但新增客户端需改多处硬编码 | **B-** | 无插件概念，provider 与路由硬编码 | **C** | 新增信号 = 继承 + `@register` + 配置一段，**改 0 处引擎代码** | **A** |
| **错误处理** | `LLMError`→502 全局处理；但**LLM 无重试**、500 响应回显原始异常 | **B-** | 有指数退避重试 + `hint` 可修方向；但 500 回显原始异常 | **B+** | 错误上下文完整，实验可复现性优先 | **A** |

**结论**：
- **最成熟**：**TideWatch**（全 A）。
- **最需要重构**：
  - 从**单文件体量**看 → **WingMan**：`store.py`(1940) + `preflight.py`(1679) + `collect/reader.py`(1169) 三个 >1000 行的文件，是全仓最大的聚合面。
  - 从**分层性质**看 → **Etude**：`db.py`（存储混领域）与 `api.py`（应用 monolith）的耦合比 WingMan 更"结构性"。

---

## 2. 逐项目诊断

> 每条格式：【现象】（文件名 + 行号）→【为什么是问题】→【改法】→【优先级 / 工作量】

### 2.1 WingMan

#### W-1【P0】`store.py` 1940 行的单类 god object，是整个系统的横切耦合点

**【现象】**
`backend/app/store.py` 全文 1940 行，只有一个 `class Store`（第 397 行起），包含约 90 个方法，横跨：
- schema DDL 与 6 个手写迁移：`SCHEMA`(72-251)、`_migrate_person_columns`(445)、`_migrate_message_columns`(492)、`_migrate_facts_unique`(539)、`_migrate_facts_person`(569)、`_backfill_*`(519/600)；
- 连接与锁：`conn`(408-420)、`init`(422-436)；
- 会话 `chats`/游标 `collect_cursors`(655-1210)；
- 人物 `persons`/`person_personas`(858-1109)；
- 消息 `messages`/`embeddings`(1243-1476)；
- 记忆 `facts`/`summaries`/`personas`(1477-1718)；
- 引擎输出 `engine_runs`/`sim_runs`/`activity_log`(1719-1891)；
- 杂项 `kv`/`counts`/`export_chat_json`(1892-1940)。

**【为什么是问题】**
1. **任何一处改动都要在 1940 行里定位**，且 6 张业务域共享一个 `RLock`（404 行）——加一个索引/迁移会影响所有域的心理模型；
2. 每个使用方（`api/*`、`engine/*`、`collect/*`、`memory/*`）都直接 import 同一个 `Store`，**无法按域单独测试或替换**；
3. 迁移函数与业务读写混在一起，「schema 演进」这条最需要独立审计的路径被淹没在业务方法中。

**【改法】** 按「连接 / schema+迁移 / 域仓储」三类拆分，保留 `store/__init__.py` 的 `Store` 门面以**不破坏现有调用点**：

```
backend/app/store/
  __init__.py        # class Store: 组合各 repo，保持既有公共方法签名（门面）
  db.py              # conn()/init()/RLock/PRAGMA/路径迁移（原 397-436, 368-394）
  schema.py          # SCHEMA / FACTS_DDL / 常量（原 43-251）
  migrations.py      # _migrate_* / _backfill_*（原 440-654）
  chat_repo.py       # chats + collect_cursors（原 655-1210）
  person_repo.py     # persons + person_personas（原 858-1109）
  message_repo.py    # messages + embeddings（原 1243-1476）
  memory_repo.py     # facts + summaries + personas（原 1477-1718）
  engine_repo.py     # engine_runs + sim_runs + activity_log（原 1719-1891）
  kv_repo.py         # kv + counts + export（原 1892-1940）
```
门面示例（关键：改动对调用方透明）：
```python
class Store:
    def __init__(self, db_path: Path):
        self.db = Database(db_path)          # conn/init/migrations
        self.chats = ChatRepo(self.db)
        self.persons = PersonRepo(self.db)
        self.messages = MessageRepo(self.db)
        self.memory = MemoryRepo(self.db)
        self.engine = EngineRepo(self.db)
        self.kv = KvRepo(self.db)
    # 兼容层：老代码 self.get_chat(...) 继续可用
    def get_chat(self, chat_id): return self.chats.get(chat_id)
```

**【优先级】** P0　**【工作量】** 1.5–2 人日（纯移动代码 + 门面转发，测试可回归）

---

#### W-2【P0】SQLite 外键在运行期**默认关闭**，级联删除依赖「临时开 PRAGMA」的脆弱约定

**【现象】**
- `conn()`（第 408-420 行）每次新建连接，**未设置 `PRAGMA foreign_keys`**；SQLite 的外键开关是**按连接**生效且默认 OFF。
- `SCHEMA` 里却声明了 `ON DELETE CASCADE`（如 `messages.chat_id`，第 87 行；`embeddings.message_id`，第 107 行），并在 `init()` 里对**另一个一次性连接**设了 `PRAGMA foreign_keys = ON`（第 427 行）后立即关闭——该设置不会延续到后续 `conn()`。
- 因此运行期只有显式加 PRAGMA 的少数删除路径才真正级联：`delete_chat`(806)、`delete_messages`(1371)；`delete_person` 明确放弃级联并手写删除（第 1054 行注释：「连接默认没开 foreign_keys，指望级联会漏删」）。

**【为什么是问题】**
1. **正确性**：任何**新增**的删除路径只要忘了在连接里 `PRAGMA foreign_keys = ON`，就会静默留下孤儿行（`messages`/`embeddings` 残留）。这是"不报错但数据脏"的典型。
2. `engine_runs.chat_ids` 是 JSON 数组、`activity_log.chat_id` 无外键——删除会话后**这两张表不会被清理**，历史输出里会引用已删会话。此为**待确认**（未找到针对它们的级联清理代码）。
3. schema 声明与运行行为不一致，会误导后来的维护者。

**【改法】** 在 `conn()` 里**统一开启外键**，删掉散落的临时 PRAGMA：
```python
@contextmanager
def conn(self):
    with self._lock:
        c = sqlite3.connect(self.db_path, timeout=15.0)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")   # 每个连接都必须设，且建议在 create
        c.execute("PRAGMA busy_timeout = 5000")
        ...
```
并补一张 `engine_runs`/`activity_log` 对 `chats` 的显式清理或在 `delete_chat` 中手写删除，用测试断言「删除会话后不存在任何孤儿行」。

**【优先级】** P0（正确性）　**【工作量】** 0.5 人日

---

#### W-3【P1】`list_chats` 是 N+1 查询，每次列会话开 N+1 条连接、跑 3N 条 SQL

**【现象】**
`list_chats`（第 794-802 行）先取全部 id，再对每个 id 调 `get_chat`；而 `get_chat`（第 755-793 行）每次 `with self.conn()` 新建连接，并执行 3 条查询（chat 行 + 消息聚合统计 + embedding 计数）。

**【为什么是问题】**
N 个会话 = **1 + 3N 条 SQL + (N+1) 次连接 open/close**，每次都过全局 `RLock`。会话多时列表页首屏显著变慢，并且把全局锁的争用放大 3N 倍。

**【改法】** 用一条 `LEFT JOIN` 聚合一次性取回：
```sql
SELECT c.*,
       COUNT(m.id) AS total,
       SUM(m.role='peer') AS peer_cnt,
       SUM(m.role='me')   AS me_cnt,
       MIN(m.ts) AS first_ts, MAX(m.ts) AS last_ts,
       (SELECT COUNT(*) FROM embeddings e JOIN messages m2 ON m2.id=e.message_id
          WHERE m2.chat_id=c.id) AS indexed
FROM chats c LEFT JOIN messages m ON m.chat_id=c.id
GROUP BY c.id ORDER BY c.id;
```
包一层 `asyncio.to_thread`（现有 `routes_data.py:164` 已是这个模式）。

**【优先级】** P1（性能）　**【工作量】** 0.5 人日

---

#### W-4【P1】LLM 调用层缺少统一的**重试/退避/成本计量**，且每次请求新建 httpx client

**【现象】**
- `llm/openai_compat.py`：`chat_raw`（97-155）仅对 `response_format` 400 做一次降级重试（119-126），对 **429/5xx/网络错误一律直接抛 `LLMError`**（114-117、128-129），无退避。
- 每次调用都 `async with httpx.AsyncClient(...)` 新建客户端（111-112、124-125），`list_models` 同理（177-178）——**无连接复用，每次 LLM 调用重建 TCP/TLS**。
- usage 只在 debug 打印（152-154），**无 token/成本累计**、无超时分层（仅一个总 `timeout`）。
- 对比：Etude 的 `providers/llm.py:chat`（300-368）**已有** `_RETRYABLE_STATUS` + 指数退避（363-365），说明同一作者在另一项目里已实现更好的方案，WingMan 这边是短板。

**【为什么是问题】**
1. **成本**：一次分析链要多次模型调用（analyzer→planner→suggestor→simulator），无退避的重试策略在限流下会造成「整条链一次性失败」；
2. **性能**：无连接池 → 每次调用多一次握手延迟；
3. **可观测性**：无 token 累计，用户无法知道一次推演花了多少。

**【改法】**
1. 在 `llm/base.py` 的 `complete_json` 外层增加**统一的瞬时错误重试**（网络/408/409/425/429/5xx，退避 1→2→4s + 抖动），把 Etude 的 `_RETRYABLE_STATUS` 策略搬过来；
2. 在 `AppContext` 内**持有一个长生命周期 `httpx.AsyncClient`**（随 `invalidate()` 关闭重建），provider 注入该 client；
3. 在 `complete_json` 返回值旁增加 `usage` 透出，`engine/pipeline` 累加后写入 `engine_runs`。

**【优先级】** P1（可靠性 + 成本）　**【工作量】** 1 人日

---

#### W-5【P1】`_trust_env_for` 逻辑被复制 3 份，注释自认「不允许新增共用模块」

**【现象】**
同一段「回环地址不继承代理」的判断分别出现在：
- `llm/openai_compat.py:22`（`_trust_env_for`）
- `llm/ollama.py:25`（同名函数）
- `memory/embedder.py:29`（同名函数）

`openai_compat.py` 的 docstring（32-33 行）明确写了：「同一份判断在 ollama.py / memory/embedder.py 各有一份（**本任务的写范围不允许新增共用模块**）」，靠 `tests/test_loopback_proxy.py` 断言三份行为一致来兜底。

**【为什么是问题】** 三处复制 + 一份测试来保证一致，是典型的「测试在替重构还债」：任一处修 bug 而漏改另两处，测试会红——但那本该是不可能发生的。这是**加一个共用模块就能消除的持续风险**。

**【改法】** 新建 `llm/net.py`（或 `app/net.py`），导出 `trust_env_for(url)`，三处改为 import；保留 `tests/test_loopback_proxy.py` 但对单函数做参数化测试即可。

**【优先级】** P1（可维护性）　**【工作量】** 0.3 人日

---

#### W-6【P1】异步边界穿透：部分 API 端点直接在事件循环里做同步 SQLite 调用

**【现象】**
项目对耗时阻塞调用大量使用了 `asyncio.to_thread`（如 `routes_collect.py:72,126,152,175,183`，`routes_data.py:164,215,244`），思路正确。但存在**不一致的漏网**：
- `routes_engine.py:26`（`_require_chat`）、`:34`、`:73`、`:82`、`:91`、`:97`；
- `routes_data.py:59`；`routes_persons.py:29`；`routes_collect.py:292`；`routes_health.py:194`（`ctx.store.counts()`）。

这些在 `async def` 里**同步**调用 `Store`，会占用事件循环线程并争抢全局 `RLock`。

**【为什么是问题】** 分析链路本身要多次调用 store；若并发请求下某个阻塞调用恰好等在锁上，会**卡住整个事件循环**（界面「点了没反应」）。这与项目在 `routes_collect.py` 顶部（16-21 行）刻意写下的「所有耗时动作都走 to_thread」原则自相矛盾。

**【改法】** 统一封装异步适配（如 `store_call(fn, *args)` = `asyncio.to_thread`），把这些零散的同步调用全部替换；或在 `context.get_ctx()` 暴露 `astore` 代理。加一个 lint 规则/grep 守卫（TideWatch 的 CI 已有类似守卫思路）禁止 `async def` 内出现 `store.` 直接调用。

**【优先级】** P1（并发正确性）　**【工作量】** 0.5 人日

---

#### W-7【P2】`preflight.py` 1679 行 / `collect/reader.py` 1169 行：按职责拆分

**【现象】**
- `scripts/preflight.py` 1679 行，单一脚本内串联 12 个自检项（`check_project_layout` 622、`check_python_version` 655、`check_backend_deps` 691、`check_database` 855、`check_port` 969 ... 到 `check_optional_modules` 1297），外加输出编码层（123-243）、数据模型（245-303）、CLI（1576-1679）。
- `backend/app/collect/reader.py` 1169 行，混装：数据结构（71-190）、文本抽取（256-390）、列画像打分（390-560）、映射推断（614-817）、称呼索引（817-996）、读消息（996-1123）、探测报告（1123-1169）。

**【为什么是问题】** 二者都属「高内聚但过载」：没有互相纠缠，但单文件承担 5-6 个职责，阅读与并发开发都受限；`reader.py` 尤其——它是采集层最需要单测的部分。

**【改法（拆分清单）】**

`scripts/preflight/`：
```
preflight/__init__.py, __main__.py
preflight/console.py     # 输出编码/打印（原 123-243）
preflight/state.py       # Check / State / env 解析（原 245-460）
preflight/probes.py      # 超时/可写/端口/TCP 探测（原 495-618）
preflight/checks_env.py  # layout/python/deps/data_dir（原 622-733）
preflight/checks_runtime.py  # database/port/frontend/samples（原 855-1090）
preflight/checks_provider.py # provider/config/可选模块（原 1090-1345）
preflight/render.py      # 渲染（原 1468-1572）
preflight/cli.py         # 参数与 main（原 1576-1679）
```
`collect/reader/`：
```
reader/__init__.py   # 重导出，保持 `from .collect.reader import read_messages` 不变
reader/structures.py # Column/Scored/Mapping/RawMessage/ReadResult（71-190）
reader/text_extract.py # 文本抽取与编排（256-390）
reader/profile.py    # 列画像与打分（390-560）
reader/infer.py      # infer_mapping/pick_message_tables（614-817）
reader/nameindex.py  # NameIndex/build_name_index（817-996）
reader/read.py       # read_messages/_guess_msg_type（996-1123）
reader/probe.py      # probe（1123-1169）
```

**【优先级】** P2　**【工作量】** 各 0.5–1 人日

---

#### W-8【P2】安全与隐私：敏感数据落盘明文、异常回显、CORS 组合非法

**【现象】**
1. **密钥明文落盘**：控制台写入的 `llm_api_key`/`embed_api_key` 存进 SQLite `kv` 表（`context.py:81` `self.store.kv_set(k, sval)`），且库文件是**未加密**的普通 SQLite（`config.py:166` `DATA_DIR/"wingman.db"`）；`.env` 中同样明文。读取时做了掩码（`config.py:198` `mask_secret`），但**存储层无加密**。
2. **异常回显**：`main.py:212-218` 的兜底 500 handler 把 `f"{type(exc).__name__}: {exc}"` 原样返回给客户端。
3. **CORS 组合非法**：`main.py:188-194` 在 `allow_origins` 回退为 `["*"]` 时仍 `allow_credentials=True`——浏览器会拒绝该组合，且语义上不安全。
4. **敏感内容日志**：`store.py` 注释（193-195 行）承认 `engine_runs` 存的是「模型生成的回复原文，属隐私数据」，但与消息同库同目录、明文。

**【为什么是问题】** 本项目处理 QQ/微信**聊天记录**与**剪贴板**，属高敏感数据；用户机器上的明文库一旦被同步/备份/取证读取，等同于聊天记录与 API Key 全部泄露。回显原始异常会把内部路径/结构暴露给任何能访问该端口的一方（虽默认仅 127.0.0.1，但 CORS 可达面被放大了）。

**【改法】**
1. 给出「可选加密」：复用项目**自己已有的** `collect/sqlcipher.py` 解密能力不现实（那是读别人库），但可用 `sqlcipher3`/`pysqlcipher3` 或对 `kv` 中的密钥用 OS 级 DPAPI（Windows）加密；至少**把密钥从业务库挪到单独的、权限 600 的凭据文件**。
2. 500 handler 改为**回显稳定错误码 + request_id**，详细堆栈只进日志。
3. CORS：默认 `allow_origins=["http://127.0.0.1:8787"]`，`allow_credentials` 仅在非通配时开启（附代码见共性清单 C-6）。

**【优先级】** P2（安全）　**【工作量】** 2 人日（加密）/ 0.3 人日（回显 + CORS）

---

### 2.2 Etude

#### E-1【P0】`db.py` 1204 行：存储层内混入 SRS **领域逻辑**，职责边界被破坏

**【现象】**
`backend/app/db.py`（1204 行）除连接/查询外，直接实现了完整的间隔复习算法与卡片状态机：
- `due_cards`(861)、`card_payload`(905)、`grade_card`(920)、`_srs_snapshot`(969)、`last_review`(983)、`undo_grade`(989)、`set_card_srs`(1029)、`push_cards`(1083)、`set_cards_srs`(1119)、`list_cards`(1132)。

而**纯算法**其实已单独放在 `srs.py`（`schedule` 32、`preview` 82、`human_delay` 98）。也就是说：**算法在 `srs.py`，而调用算法、读写卡片的业务编排被塞回了 `db.py`**。

**【为什么是问题】**
1. 存储层本应只关心「读写」，现在却决定了「复习间隔怎么算、撤销怎么回滚、新卡配额怎么算」——**换存储或换 SRS 策略都要动同一个 1204 行的文件**；
2. `grade_card`/`undo_grade` 有非平凡的事务语义（写 reviews + 更新 cards + 存快照），与其它纯查询混在一起，难以独立测试「复习事务」；
3. 违反项目自己在文件头（7-12 行）写的「status vs readiness」职责分离精神。

**【改法】** 拆成「连接/schema + 域仓储 + 领域服务」：

```
backend/app/db/               # 保持 db.query/db.execute 等公共名以不破坏调用方
  __init__.py                 # 重导出 connect/query/execute/backup_to 等
  conn.py                     # connect/close/query/one/execute/backup_to/now/parse_ts（176-270）
  schema.py                   # SCHEMA + _MIGRATIONS + _migrate（34-220）
  lessons.py                  # lessons/examples/swaps（276-509）
  plans.py                    # plans（753-860）
  cards.py                    # cards/reviews 的纯读写（861-1197）
backend/app/services/review.py  # grade_card/undo_grade/set_card_srs/push_cards 等
                                #   编排 srs.schedule + cards 仓储（领域逻辑，非存储）
```
对于调用方，`db/__init__.py` 继续导出 `db.grade_card` 等，**迁移零破坏**。

**【优先级】** P0　**【工作量】** 1.5 人日

---

#### E-2【P0】`api.py` 870 行：应用 god 模块（全部路由 + 模型 + 线程池 + 异常处理）

**【现象】**
`backend/app/api.py` 单文件包含：全部 Pydantic 模型（57-172）、`ThreadPoolExecutor`（49）、FastAPI app 实例（51）、**约 60 个路由**（health 178 到 backup 825）、前端 index 服务（846）、500 处理器（861-870）。此外 `_POOL.submit` 与 `_run_generation`/`_run_plan`（338/523）在同一文件内定义。

**【为什么是问题】**
1. 一个文件承担「路由/传输模型/后台任务编排/应用装配」四类职责，**新增一个领域端点都要进这个文件**；
2. 业务逻辑泄漏进 API 层：如 `redo_example_image`（795-805）在路由里**直接写 SQL** `db.execute("UPDATE examples SET scene_image=?...")`——传输层干了仓储层的活；
3. `api.py` 反向依赖 `db._loads`（661 行调用 `db._loads(...)` 私有函数）——**API 层伸手到存储层内部**。

**【改法】** 拆为 `app/api/` 包 + `app/services/`：

```
backend/app/api/__init__.py     # create_app() 装配 + include_router
backend/app/api/models.py       # 全部 Pydantic（57-172）
backend/app/api/routes_meta.py  # health/selfcheck/config/catalog/tests（178-297）
backend/app/api/routes_lessons.py # lessons/examples（298-425, 733-814）
backend/app/api/routes_plans.py # plans（426-554）
backend/app/api/routes_study.py # queue/cards/grade/undo（629-732, 816）
backend/app/api/routes_media.py # audio/image（587-624）
backend/app/api/routes_admin.py # data-location/backup/index（555-584, 824-858）
backend/app/jobs.py             # _POOL + _run_generation/_run_plan/recover（pipeline.py 40-90）
```
并把 `redo_example_image` 里的裸 SQL 下沉为 `db.set_example_image(example_id, name)`；把 `db._loads` 提升为公共 `db.loads_json`。

**【优先级】** P0　**【工作量】** 1.5 人日

---

#### E-3【P0】`_provide_both`：每个图都新建线程池，且**败者线程无法取消、继续跑完烧钱**

**【现象】**
`providers/images.py` `_provide_both`（678-724）：
- 第 705 行**每次调用**都 `ThreadPoolExecutor(max_workers=2)`；
- 第 712 `as_completed` 拿到第一个成功结果后 `return`，第 721-722 `finally: pool.shutdown(wait=False, cancel_futures=True)`；
- 但 `cancel_futures=True` **只能取消尚未开始的任务**；两条路在第 708-711 行已**同时 submit**，画图任务必然已启动——`cancel_futures` 对它无效。

**【为什么是问题】**
1. **成本/资源泄漏**：当「检索」先返回（注释 689-691 行承认「绝大多数时候检索赢」），**画图那条 LLM 请求仍在后台跑完**，消耗 API 额度、占用一个线程。一个训练包配 8 张图 → 最多 8 个被抛弃的在途画图请求；
2. **线程/池抖动**：每个图都创建并丢弃一个池（8 张图 = 8 个池）。

**【改法】**
1. 模块级**共享池**（`_IMG_POOL = ThreadPoolExecutor(max_workers=4)`），复用；
2. 无法真正取消线程是 Python 限制，但可**降低放弃成本**：给两条路加「先到先用」的显式策略——若检索路径命中率足够高，默认只跑检索，仅在检索失败时才触发画图（把"并行"改为"回退"，见下代码），从而**避免绝大多数白白发起画图**：
```python
def _provide_both(*, query, prompt, gen_cfg, timeout, force):
    if hit := (None if force else cached("search", key_of("search"))):
        return hit
    try:
        raw, ext = _fetch("search", query, prompt, gen_cfg or {}, timeout)
        return _store("search", key_of("search"), raw, ext)
    except Exception as search_err:
        raw, ext = _fetch("llm", prompt or query, gen_cfg or {}, timeout)  # 仅此时才画图
        return _store("llm", key_of("llm"), raw, ext)
```
若产品上确实需要"先到先用"，则保留并行但**给线程池设上限并复用**，且接受"败者跑完"的成本（需在配置中明确 `both` 的代价）。

**【优先级】** P0（成本/正确性）　**【工作量】** 0.5–1 人日

---

#### E-4【P1】图片/语音生成在**例句维度串行**，逐条等待

**【现象】**
`pipeline.py` `_make_images`（277-317）与 `_make_audio`（252-266）都是 `for i, ex in enumerate(examples)` 的顺序循环，每条 `await` 式阻塞等待（`images_mod.provide` / `tts.synthesize_cfg`）。配图本身支持 8–25s/张（见 `images.py` 注释 685），串行 8 张 = 最多 ~200s。

**【为什么是问题】** 生成是纯 I/O 等待型（等模型/等图库），串行把总时长线性累加，而 CPU 完全空闲；用户侧「一个包要等好几分钟」。

**【改法】** 用**已有**的生成线程池（`api.py:49` 的 `_POOL` 或专门的 IO 池）在例句维度并行，保持「失败只记不抛」语义：
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
def _make_images(key, examples, img_cfg, failures, pool=None):
    ...
    with ThreadPoolExecutor(max_workers=config.IMAGE_CONCURRENCY) as pool:
        futures = {pool.submit(images_mod.provide, query=..., prompt=..., ...): i
                   for i, ex in enumerate(examples[:budget])}
        for fut in as_completed(futures):
            i = futures[fut]
            try: out[i] = fut.result()
            except Exception as exc: failures.append(f"配图 · …：{exc}")
```
并发度必须可配置（免费额度下默认 2–3，避免限流——项目在 `api.py:44-48` 已认识到这一点）。同时把进度 `_set_job` 改为**完成计数**而非"第 i/N"。

**【优先级】** P1（性能，直接改善体感）　**【工作量】** 1 人日

---

#### E-5【P1】`db.py` 全局单连接 + 全局锁，schema 迁移**只能加列**，无版本表

**【现象】**
- `connect()`（176-200）维护**进程级单连接** `_CONN` + `_LOCK`（27-28），`check_same_thread=False`；`query/execute`（235-251）全程持锁。
- 迁移 `_migrate`（203-220）遍历 `_MIGRATIONS`（154-161），仅支持 `ALTER TABLE ADD COLUMN`，**无版本号表**，靠 `PRAGMA table_info` 试探。

**【为什么是问题】**
1. 单连接 + 全局锁 → 所有 DB 访问串行；对单机单用户尚可，但 `_POOL`(3) + FastAPI 线程池 + `_provide_both` 的线程会**争抢同一把锁**，长事务会阻塞整个服务；
2. 迁移框架无法表达「改列类型/加约束/回填数据/删列」，一旦需要（如把 `cards.suspended` 从 int 改为 enum 语义、或拆表）就得绕；
3. 无版本表 → 无法回答"这个库是从哪个版本升上来的"，只能逐列试探。

**【改法】**
1. 短期保留单连接（有 `check_same_thread=False` + 锁是安全的），但把**只读查询**与**写事务**分池，或改用 `sqlite3` 的 WAL + 短事务（已有 WAL，35-36 行）；
2. 引入**最小版本表** `schema_meta(version INT)` 与有序迁移列表 `(version, sql_fn)`，把现有 5 条加列迁移登记为 v1→v2、v2→v3……，`connect()` 里按版本推进；保留 `PRAGMA table_info` 作为幂等兜底。这样将来支持改约束/回填就有落点。

**【优先级】** P1（schema 演进）　**【工作量】** 0.5–1 人日

---

#### E-6【P2】`providers/images.py` 806 行：按「提示词 / 缓存 / 检索 / 生成 / 编排」拆分

**【现象】**
`providers/images.py`（806 行）混合：提示词构造（`build_prompt` 143、`build_query` 207）、内容寻址缓存（`cache_name` 262、`cached` 269、`_sniff` 279）、图库检索（`_search_openverse` 333、`_search_commons` 366、`pick_candidate` 418、`search_image` 448）、LLM 画图（`_generate_llm` 500、`_extract_image` 580）、编排（`provide` 751、`_provide_both` 678）。

**【为什么是问题】** 缓存/检索/生成三条路径各有独立失败模式，混在一个文件里使 E-3 那类"编排 bug"难以被发现；且它已是 providers/ 下最大文件，与 `llm.py`(433)/`tts.py`(261) 的粒度不一致。

**【改法】**
```
providers/images/__init__.py   # 重导出 provide / check / source_catalog / valid_name
providers/images/prompt.py     # build_prompt/build_query（143-260）
providers/images/cache.py      # cache_name/cached/_sniff/_reject_unknown（262-332）
providers/images/search.py     # 图库检索（333-480）
providers/images/generate.py   # LLM 画图（500-630）
providers/images/service.py    # provide/_provide_both/_fetch/_store（655-806）
```

**【优先级】** P2　**【工作量】** 0.5 人日

---

### 2.3 TideWatch

> TideWatch 是三者中最干净的。它的"问题"多数是**面向未来规模**的增强点，而非缺陷。

#### T-1【P1】`PROJECT_ROOT = parents[2]` 使引擎**无法作为普通 wheel 安装**运行

**【现象】**
`src/tidewatch/config.py:26-27`：
```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.yaml"
```
`configs/`、`rules/` 不是 package data（`pyproject.toml` 无 `[tool.setuptools.package-data]`，仓库无 `MANIFEST.in`）。`Dockerfile:24` 用 `pip install -e .`（editable，`parents[2]` 指向源码树）并**显式** `COPY configs ./configs`/`COPY rules ./rules`（27-28）来绕过。

**【为什么是问题】** 一旦某人 `pip install tidewatch`（非 editable）后在其项目里 `from tidewatch import Pipeline; Pipeline.from_config()`，`parents[2]` 会指向 `site-packages` 上层 → **找不到 `configs/default.yaml` 而崩溃**。可复现性依赖"必须用 editable + 显式 COPY"，是隐性约束。

**【改法】**
1. 用 `importlib.resources` 解析包内资源，并把 `configs/` 作为 package data 打包；或
2. 引入环境变量 `TW_CONFIG_DIR` / 参数显式传入，`from_config` 优先取显式路径，找不到时给出可执行提示（项目风格）。
```toml
[tool.setuptools.package-data]
tidewatch = ["configs/*.yaml", "rules/*.yaml", "rules/*.txt"]
```
并在 CI 增加一条「非 editable 安装后 `tidewatch signals` 能跑」的用例。

**【优先级】** P1（可复现构建）　**【工作量】** 0.5 人日

---

#### T-2【P1】`CoOccurrenceSignal` 账号两两比较 **O(A²)** 且无规模上限

**【现象】**
`signals/coordination.py` `CoOccurrenceSignal.run`（222-279）在 `actors`（第 232 行 `sorted(actor_topics)`）上做**双重循环**（236-247）。对比：同文件 `TextClusterSignal`（154 行）有 `[: _MAX_PER_TOPIC]` 上限，而共现信号**没有**任何上限。

**【为什么是问题】** 账号数 A 增长时是 A²/2 次集合交集；1 万账号 ≈ 5000 万次，即使每次很快也会成为明显瓶颈。而"同一话题下的账号才可能共现"这一点完全可以用来剪枝。

**【改法】** 用**倒排（topic → actors）**代替全对比较：
```python
topic_actors: dict[str, set[str]] = defaultdict(set)
for actor, topics in actor_topics.items():
    for t in topics:
        topic_actors[t].add(actor)
pair_shared: dict[tuple[str,str], int] = Counter()
for t, members in topic_actors.items():
    ms = sorted(members)
    for i in range(len(ms)):
        for j in range(i+1, len(ms)):
            pair_shared[(ms[i], ms[j])] += 1   # 只枚举"同话题内"的账号对
```
复杂度降为 Σ_topic C(n_t,2)，通常远小于 A²。另加可配置 `max_actors` 上限与告警日志。

**【优先级】** P1（可扩展性）　**【工作量】** 0.5 人日

---

#### T-3【P2】`MappedAdapter.load` 的注释宣称流式，但实现把整批读进内存

**【现象】**
`adapters/base.py:98-134`：docstring（101-102 行）称「可以边读边转，不必把整份数据先读进内存」，但 `load`（112-134）把全部 `Item` 累积进 `items: list`，最终 `Dataset(items=items, ...)` 持有全部对象。

**【为什么是问题】** 注释与实现不符，会给使用者错误的规模预期；对超大 JSONL 会产生内存峰值。（协同层确实需要全量数据，因此"全量"本身可接受——问题是**注释**在说谎。）

**【改法】** 二选一：① 修正注释，明确"引擎需全量数据以做协同分析，故数据集常驻内存"；② 若确需支持超大输入，提供 `iter_mode` 让 item 级信号流式处理、协同层走采样。推荐①（成本最低、最诚实）。

**【优先级】** P2　**【工作量】** 0.1 人日

---

#### T-4【P2】`make freeze` 目标与实际锁定文件名不一致

**【现象】**
`Makefile:73-75` 的 `freeze` 目标写出 `requirements-lock.txt`，而仓库内存在的是 `requirements.txt`（内容为 `PyYAML>=6.0`，`pyproject.toml:20-22` 亦有同依赖）。**待确认**：是否存在 `requirements-lock.txt` 的引用（`grep` 未见），若无则 `freeze` 产出的文件无人消费。

**【为什么是问题】** 轻量但典型的"构建脚本与约定漂移"——`make freeze` 看似可用，实际产出的锁文件没有进入任何安装路径，可复现性承诺落空。

**【改法】** 统一为 `requirements.lock.txt` 并在 CI/文档引用；或在 `pyproject.toml` 用 `uv lock`/`pip-tools` 生成标准锁文件。

**【优先级】** P2　**【工作量】** 0.1 人日

---

#### T-5【P2】信号**串行执行**，且无单信号超时/隔离

**【现象】**
`pipeline.py:78-82` 顺序遍历信号：`for signal in self.signals: produced = signal.run(data)`。

**【为什么是问题】** 8 个信号中，协同层（`TextClusterSignal`/`CoOccurrenceSignal`）在大数据量下最慢；串行时总时长是各信号之和，且**任一信号异常会中断整条流水线**（未做 per-signal 捕获）。

**【改法】** ① 至少在 `run` 层对每个信号做 `try/except` 隔离并记录到 `timings`（避免"一个信号挂掉全盘无结果"）；② 对纯 CPU 的信号可并行（`ProcessPoolExecutor`，因涉 GIL）——但需权衡可复现性（项目高度重视确定性），建议**先做①隔离**，②作为可选优化。

**【优先级】** P2　**【工作量】** 0.3 人日

---

## 3. 跨项目共性优化清单（「一次学会、三处受益」）

| 编号 | 共性问题 | 出现位置 | 统一改法 | 优先级 |
|---|---|---|---|---|
| **C-1** | **巨型文件 / god module**：单文件承载 5+ 职责 | W: `store.py`1940 / `preflight.py`1679 / `reader.py`1169；E: `db.py`1204 / `api.py`870 / `images.py`806 | 按"连接/仓储/领域/传输"分层拆包，`__init__.py` 重导出保持调用点不变（见 W-1/E-1/E-2/E-6/W-7 的清单） | **P0** |
| **C-2** | **分层穿透**：上层直接调用下层内部/私有实现 | W: API 层多数端点同步调 store（`routes_engine.py:26,34,...`）；E: `api.py:661` 调 `db._loads`；E: `api.py:804` 路由内写裸 SQL | 建立"传输层不碰 SQL、不碰私有名"的约定 + CI grep 守卫；私有函数提升为公共 API | **P0** |
| **C-3** | **重复实现**：同一逻辑复制多份靠测试保一致 | W: `_trust_env_for` ×3（`openai_compat.py:22`/`ollama.py:25`/`embedder.py:29`） | 抽公共模块 `net.py`，测试改为对单函数的参数化测试 | **P1** |
| **C-4** | **LLM 调用层缺统一策略**：无重试/退避/成本计量；每请求新建 httpx client | W: `openai_compat.py:97-155,111,124,177`（无重试）；E: `llm.py:291-297,341`（有重试但每尝试建 client） | 统一封装：瞬时错误指数退避（搬运 Etude 的 `_RETRYABLE_STATUS` 到 WingMan）、长生命周期 client 复用、usage 透出与累计 | **P1** |
| **C-5** | **存储层 schema 演进脆**：手写迁移、无版本表、外键开关不一致 | W: 6 个 `_migrate_*` + 运行期 FK 默认关（`store.py:408,806,1371`）；E: 仅加列 + 单连接全局锁（`db.py:154,203,176`） | 引入 `schema_meta(version)` 版本表 + 有序迁移列表；连接层统一 `PRAGMA foreign_keys=ON` | **P0/P1** |
| **C-6** | **500 响应回显原始异常**（信息泄露） | W: `main.py:212-218`；E: `api.py:861-870` | 对外返回 `{error_code, request_id}`，堆栈只进日志 | **P2** |
| **C-7** | **敏感数据明文落盘**：聊天记录/密钥/剪贴板内容与业务库同库明文 | W: `context.py:81` + `config.py:166`（kv 存 key，库未加密）；E: `config.json` 明文 | 密钥与业务数据分离存储并限权（600/DPAPI）；提供可选整库加密；文档明确"数据在哪、加密到什么程度" | **P2** |
| **C-8** | **无打包元数据 / 非 src-layout**：不可 `pip install`，依赖靠 requirements | W、E 均无 `pyproject.toml`；T 有 | 参照 TideWatch 的 `pyproject.toml`：PEP 621 元数据 + `[project.optional-dependencies]` + `[project.scripts]` + ruff/pytest 配置；后端不重构目录也可先加 pyproject | **P1** |
| **C-9** | **CORS 通配 + 凭据组合非法** | W: `main.py:188-194`（`allow_credentials=True` 且 origins 回退 `*`） | 默认绑定本机具体 origin；`allow_credentials` 仅在非通配时开启 | **P2** |
| **C-10** | **可复现性缺锁定文件** | W 有 `requirements.lock.txt`（好）；E 无锁；T `make freeze` 文件名漂移 | 统一 `requirements.lock.txt`（由 `pip freeze` 或 `uv lock` 生成）并让 CI/安装脚本消费它 | **P1** |

**C-6 / C-9 的具体代码（两项目通用）**：
```python
# main.py / api.py 兜底异常处理
@app.exception_handler(Exception)
async def unhandled(request, exc):
    rid = uuid.uuid4().hex[:12]
    logger.exception("unhandled rid=%s %s %s", rid, request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error_code": "internal", "request_id": rid})

# CORS
app.add_middleware(CORSMiddleware,
    allow_origins=["http://127.0.0.1:8787"],   # 不用 "*"
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```

---

## 4. 30 天优化路线图

> 目标：在不影响功能的前提下，把「最大单文件」和「最脆的正确性点」清掉，并把 TideWatch 的工程实践反向移植到 WingMan/Etude。
> 每周 2–4 个动作；每个动作都是**可独立成 commit** 的最小单元，附验收标准。

### 第 1 周 —— 止血：正确性与成本

| 动作 | 内容 | 验收标准 |
|---|---|---|
| A1 | **W-2**：`conn()` 统一 `PRAGMA foreign_keys=ON`；补 `engine_runs`/`activity_log` 的会话清理 | 新增测试：删除会话后 `messages/embeddings/engine_runs/activity_log` 无孤儿行；既有 22 个测试全绿 |
| A2 | **E-3**：`_provide_both` 改为共享池 + 「检索优先、失败才画图」（或明确 `both` 成本） | `test_image_parallel.py` 通过；新增用例断言「检索命中时**不**发起画图请求」（用 stub 计数） |
| A3 | **C-4（WingMan 侧）**：为 `complete_json` 加瞬时错误指数退避 | 新增用例：stub 返回一次 429 后成功，断言发生重试且最终返回结果 |
| A4 | **E-6 + W-5（低风险清理）**：抽 `net.py`；`images.py` 拆包（纯移动） | 行为零变化，`grep` 确认无重复 `_trust_env_for` 定义；测试全绿 |

### 第 2 周 —— 拆分「最大单文件」（第一批）

| 动作 | 内容 | 验收标准 |
|---|---|---|
| B1 | **W-1**：`store.py` 拆为 `store/` 包（门面转发） | 公共 API 签名不变；`pytest` 全绿；`store/__init__.py` 行数 < 200，各 repo 文件 < 400 行 |
| B2 | **E-1**：`db.py` 拆为 `db/` 包 + `services/review.py`（SRS 领域下沉） | `db.grade_card` 等公共名不变；复习相关测试独立通过 |
| B3 | **C-8**：为 WingMan、Etude 各加 `pyproject.toml`（PEP 621，参照 TideWatch），声明 `[project.optional-dependencies]` 与 dev 工具 | `pip install -e .` 成功；CI 改为 `pip install -e ".[dev]"`；`python -m app.main`/`run_*.py` 仍可启动 |
| B4 | **C-10**：Etude 生成 `backend/requirements.lock.txt` 并让 CI 消费 | CI 安装步骤改为锁定集；`make`/脚本引用一致 |

### 第 3 周 —— 拆分（第二批）与并发

| 动作 | 内容 | 验收标准 |
|---|---|---|
| C1 | **E-2**：`api.py` 拆为 `api/` 包 + `jobs.py`；裸 SQL 下沉、`_loads` 提公共 | 路由数量不变（`/openapi.json` 对比）；`test_api.py`/`test_edit_api.py` 全绿 |
| C2 | **W-3 + W-6**：`list_chats` 改单查询；消除事件循环内的同步 store 调用 | 新增/更新基准：某会话集下 `list_chats` 的 SQL 数从 1+3N 降为 1；`grep` 守卫禁止 `async def` 内出现 `.store.` |
| C3 | **E-4**：图片/语音生成按例句并行（并发度可配置，默认 2–3） | 新增测试断言并发度上限不被突破；手工验证 8 张图耗时显著下降 |
| C4 | **W-7**：`reader.py` 拆包（纯移动，重导出） | `test_collect_reader.py` 全绿；每个子模块 < 300 行 |

### 第 4 周 —— 演进能力与安全

| 动作 | 内容 | 验收标准 |
|---|---|---|
| D1 | **C-5**：WingMan/Etude 各引入 `schema_meta(version)` + 有序迁移列表 | 老库（构造 fixture）能升到最新且幂等重跑安全；新增"从 v1 升到 vN"用例 |
| D2 | **T-1 + T-2**：TideWatch 资源改 `importlib.resources` + topic 倒排剪枝共现 | 新增"非 editable 安装后 `tidewatch signals` 可跑"用例；共现在大账号集下耗时下降 |
| D3 | **W-8 + C-6 + C-9**：异常回显改为 `error_code+request_id`；CORS 收紧；密钥与业务库分离存储 | 手动验证：构造内部异常返回不含堆栈；CORS 头为具体 origin；密钥不再出现在业务库 `kv` 中 |
| D4 | **T-3 + T-4 + T-7(D/E 逐项目收尾)**：修正注释、统一锁文件名、`preflight.py` 拆包 | `ruff`/`pytest` 全绿；`make freeze` 产出的文件被 CI 引用 |

**路线图总时长**：约 4 周（按 1 名开发者、每周 2–3 人日投入估算）。

**建议的执行顺序原则**：
1. 先做「正确性」（A1 外键、A2 成本）——它们在改错时最贵；
2. 再做「最大单文件拆分」（B1/B2）——它们解锁后续所有并行开发；
3. 打包/锁定（B3/B4）紧随其后——让后续每一步都可复现；
4. 安全与演进（D 系列）放最后——此时结构已清晰，改动面最小。

---

## 附录 A：文件规模热点表（>400 行）

| 项目 | 文件 | 行数 | 处理建议 |
|---|---|---|---|
| WingMan | `backend/app/store.py` | **1940** | 拆 9 模块（W-1） |
| WingMan | `scripts/preflight.py` | **1679** | 拆包（W-7） |
| WingMan | `backend/app/collect/reader.py` | **1169** | 拆包（W-7） |
| WingMan | `collect/pipeline.py` | 732 | 保持（编排为主） |
| WingMan | `collect/semi.py` | 688 | 保持（状态机内聚） |
| WingMan | `llm/mock.py` | 664 | 建议移入 `tests/fixtures/`（演示用，非生产路径） |
| WingMan | `desktop.py` | 613 | 保持 |
| WingMan | `collect/clipboard.py` | 528 | 保持 |
| WingMan | `engine/prompts.py` | 499 | 保持（纯模板） |
| WingMan | `frontend/index.html` | **4653** | 单文件前端（HTML+CSS+JS 内联），见 B-1 |
| Etude | `db.py` | **1204** | 拆包 + 领域下沉（E-1） |
| Etude | `scripts/ui_smoke.js` | 1023 | 保持（E2E 脚本） |
| Etude | `api.py` | **870** | 拆包（E-2） |
| Etude | `providers/images.py` | **806** | 拆包（E-6） |
| Etude | `pipeline.py` | 636 | 部分下沉到 `jobs.py`（E-2） |
| Etude | `frontend/index.html` | **4519** | 单文件前端，见 B-1 |
| TideWatch | `signals/coordination.py` | 330 | 保持（已是最优粒度附近） |

**B-1（补充共性项，P2）单文件前端**：WingMan `frontend/index.html`（4653 行）与 Etude `backend/frontend/index.html`（4519 行）把 HTML+CSS+JS 全部内联在单个文件。这是**刻意的零构建**取舍（`main.py:223-225` 用 `StaticFiles` 直接挂载），优点是发布简单、无 node 工具链、桌面打包无额外依赖；代价是**无法按模块组织、无法 tree-shaking、巨型 diff**。建议：不强行引入 Vite（会破坏桌面打包流程），但可把内联 `<script>` 抽为同目录 `app.js`/`styles.css` 并用 `<link>/<script src>` 引用——仍是零构建，但可读性/可 diff 性显著提升，且 `StaticFiles` 天然支持。**待确认**：需评估打包 spec（`build/*.spec`）是否已收集这些文件。

---

## 附录 B：TideWatch 值得反向移植的工程实践

| # | TideWatch 实践 | 位置 | 移植到 WingMan/Etude 的价值 |
|---|---|---|---|
| 1 | **PEP 621 `pyproject.toml` + 可选依赖分组** | `pyproject.toml:1-56` | 解决两项目"无打包元数据"；`pip install -e ".[dev,zh]"` 一条命令建环境 |
| 2 | **装饰器注册表 + 配置驱动插件** | `signals/base.py:35-45,159-167` | WingMan 的 adapter/Etude 的 provider 都可用同款：新增插件 = 继承 + `@register`，改 0 处引擎代码 |
| 3 | **三级配置覆盖 + 配置指纹** | `config.py:32-41,128-131` | 让"参数变了→结果变了"可追溯；WingMan 已有 kv 覆盖，缺的是**指纹** |
| 4 | **`make` 固化标准工作流** | `Makefile:1-76` | `make test/lint/fmt/eval/demo` 让陌生人 clone 后一条命令上手 |
| 5 | **CI 矩阵：多 Python × 可选依赖两条路径都测** | `.github/workflows/ci.yml` | "装了 jieba / 没装 jieba" 两条路都测——把"降级承诺"变成可验证事实；Etude 可类比"装了 webview / 没装" |
| 6 | **确定性优先**：标签传播按 id 排序、平票取字典序最小 | `signals/coordination.py:282-319` | 让实验可复现——WingMan/Etude 的随机策略（温度、候选洗牌）也应可播种 |
| 7 | **隐私红线 CI 守卫** | Etude `.github/workflows/ci.yml` `secrets` job | 已在 Etude 落地（密钥前缀扫描 + `innerHTML` XSS 守卫）——建议 WingMan 也照抄一份 |
| 8 | **Dockerfile 非 root + `.dockerignore` 排除原始数据** | `Dockerfile:32-36` | 供 Etude/WingMan 未来服务化参考 |

---

## 附录 C：不确定项（待确认，未编造）

1. WingMan 删除会话后，`engine_runs.chat_ids` / `activity_log.chat_id` 是否被清理——**未找到对应代码**，需运行时验证。
2. Etude `_MIGRATIONS` 之外，是否存在手工执行的「一次性修复」SQL（未在 `db.py` 内发现，但可能在其他脚本中）——**待确认**。
3. TideWatch `requirements-lock.txt` 是否被任何文档/CI 引用（`grep` 未见引用）——**待确认**，若确无则 `make freeze` 产出无人消费。
4. 两项目单文件前端是否被 PyInstaller spec 以通配收集（未逐行核对 `build/*.spec`）——**待确认**。
5. WingMan 桌面版（WebView2）与 FastAPI 的并行度实测（`KEEP_ALIVE_S=600` 的设计动机已读到，但未做压测）——**待确认**。

---

*报告完毕。所有代码引用均来自对克隆仓库的实际阅读；行号以评审时点为准，重构移动代码后需重新校准。*
