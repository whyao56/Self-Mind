---
tags: [领域/方法, 类型/报告, 轮次/二]
评审日期: 2026-10-13
评审维度: 数据层可靠性与性能
评审对象: github.com/whyao56 三个旗舰（WingMan / Etude / TideWatch）
评审方式: 本地浅克隆静态阅读 + 行号取证（未运行程序、未安装依赖、未打开任何真实数据库）
---

# 第二轮评审 · 数据层可靠性与性能

**口径**：行号来自本次实际读取的源码，未编造；性能量级标「估算」并写清推导；不能确认的写「待确认」。`gh-repos/` 下 `find` 实测**不存在任何 `*.db`/`*.sqlite*`**；`TideWatch/data/` 只有 `sample/sample.jsonl`（81266 B）与 `eval/synthetic_labeled.jsonl`（90981 B），只列名与大小、未打开。

**本轮不重复第一轮条目**：`conn()` 未开 `PRAGMA foreign_keys`（3.1）、`list_chats` 1+3N（W-3）、`async def` 内同步调 store（W-6）、无 schema 迁移（C-5）、TideWatch `CoOccurrenceSignal` O(A²)、密钥与业务数据同库（C-9）、明文落盘。角度不同者在条内标「与第一轮 X 的关系」。

---

## 0. 一页结论（最该做的 3 件事）

三个项目都把 SQLite 用对了「功能」，但都还没把它当成**用户唯一的一份资产**——WingMan 甚至没有任何备份出口，同时有一条「导入大聊天记录吃满内存」的路径。

| 序 | 动作 | 为什么排第一 | 工作量 |
|---|---|---|---|
| 🔴 1 | **WingMan 补「备份数据库 + 一键导出全部数据」**（照抄 Etude 已验证的 `VACUUM INTO` 方案） | 本地优先产品的核心责任。现在 `EXPORTS_DIR` 定义了却 0 处引用（config.py:70），用户只拿到「单会话导出 JSON」 | 1 天 |
| 🔴 2 | **WingMan 修导入路径的 I/O**：同一份文件被**完整读 3 次**，且 `read_head` 名叫「只读头部」实为全量读（registry.py:35-38） | 用户第一次用就遇到；200 MB 记录峰值内存约为文件 **5 倍**（估算），桌面版会卡死 | 半天 |
| 🟠 3 | **Etude 修复习队列与统计**：`substr(at,1,10)` 让 `idx_reviews_at` 失效，`cards` 缺状态索引 → 新卡队列全表扫 + 临时排序 | 这是产品的**核心循环**（每次开练/看首页都跑），且随使用时长的增长而线性变慢 | 半天 |

**紧随其后**：三项目**都只设了 `journal_mode=WAL`**，`synchronous`/`cache_size`/`temp_store`/`busy_timeout` 全空 —— 半天各一行，见 D-4。

**好消息**：Etude 的「备份 + 数据目录可搬迁 + 卸载说明」是三个项目最完整的一环（README.md:303-326、db.py:254-270、paths.py:104-134）。**WingMan 不需要发明方案，照抄 Etude。**

---

## 1. 现状矩阵（三项目 × 数据层维度）

| 维度 | WingMan | Etude | TideWatch |
|---|---|---|---|
| 存储 | SQLite `wingman.db`（冻结态 `%LOCALAPPDATA%\WingMan\data`） | SQLite `etude.sqlite3`（`%LOCALAPPDATA%\Etude`） | **无关系库**：YAML 规则 + JSONL |
| `journal_mode` | ✅ WAL（store.py:73，库级持久） | ✅ WAL（db.py:35） | N/A |
| `synchronous` | ⚠️ 未设置 | ⚠️ 未设置 | N/A |
| `busy_timeout` | 🟡 隐式 15 s（store.py:411 `timeout=15.0`） | ❌ 未设置 → 默认 5 s（db.py:184） | N/A |
| `cache_size`/`temp_store` | ❌ 未设置 | ❌ 未设置 | N/A |
| 连接模型 | 一把 `RLock` + **每次调用新建连接**（store.py:404-420） | **单例连接** + `check_same_thread=False` + `RLock`（db.py:176-200） | 一次性进程 |
| uvicorn worker | 1（desktop.py:425-437、main.py:234-243 无 `workers`） | 1（server.py:79-89） | N/A |
| 索引覆盖 | 11 个索引（store.py:103-235、464）；**`facts.person_id` 无独立索引** | 6 个（db.py:138-143）；**`cards(introduced/suspended)` 无索引** | N/A |
| 备份/全量导出 | ❌ **完全没有**（仅单会话 JSON，routes_data.py:220） | ✅ `POST /api/backup` + `VACUUM INTO`（api.py:824、db.py:254） | 不需要 |
| 备份 UI/文档 | ❌ 无；`EXPORTS_DIR` 悬空（config.py:70） | ✅ 按钮（frontend/index.html:3114）+ README 专章 | N/A |
| 数据目录可搬迁 | 🟡 固定（开发态在仓库内，config.py:64） | ✅ 指针文件 + 原子写（paths.py:104-134） | N/A |
| 「卸载会怎样」写明 | ❌ 未在 README/docs 找到 | ✅ README.md:321 | N/A |
| 完整性体检 | ❌ 仅 counts + 文件大小（selfcheck.py:152-186） | ❌ 仅「能不能查 stats」（selfcheck.py:78-96） | N/A |
| `integrity_check`/`VACUUM`/`ANALYZE` | ❌ 三样全无 | 🟡 仅备份用 `VACUUM INTO`；**无 `VACUUM` 回收、无 `ANALYZE`** | N/A |
| 只增不减 | `activity_log`/`engine_runs`/`sim_runs` | `reviews`/`_JOBS`/`logs/lesson-*.log` | 无 |
| 保留策略 | ❌ 全仓 0 命中 | ❌ 全仓 0 命中 | N/A |
| 日志轮转 | ✅ `RotatingFileHandler(2 MB × 3)`（main.py:49-54），**且与 data/ 分目录**（config.py:64-65） | ❌ 追加无上限、**每训练包一文件**、落在数据目录内（pipeline.py:630-636、paths.py:170） | 无 |
| 单实例保护 | ✅ 端口探测（desktop.py:491-504） | 待确认 | N/A |

---

## 2. 逐条发现（按 P0 → P2 排序）

### D-1 【P0 · 1 天】WingMan 没有任何备份或全量导出，而 `EXPORTS_DIR` 已定义却悬空

**现象+证据**
1. 唯一导出接口是**单会话**级：`GET /api/chats/{chat_id}/export`（routes_data.py:220-223）→ `store.export_chat_json`（store.py:1929-1940），内部 `all_messages()`（store.py:1939、1314-1319）全量物化。
2. `EXPORTS_DIR = APP_DIR / "exports"`（config.py:70）—— `grep -rn "EXPORTS_DIR"` 在 `backend/`、`scripts/`、`frontend/` **全 0 命中**：导出落盘这条路从未实现。
3. 无 `/api/backup`、无 `VACUUM INTO`、无 `backups/`；`grep -rni "integrity_check|vacuum|backup"` 在应用代码 0 命中。`docs/` 11 个 md **无「备份/恢复」章节**。
4. 唯一兜底是 `POST /api/runtime/open?which=data` 打开数据目录（routes_admin.py:48-70）。

**为什么是问题**
「本地优先」把用户全部资产压进**一个文件**，文件损坏/误删/换机器 = 失去一切，而程序里没有任何路径能把它安全交给用户。更糟的是第 4 条的兜底**有毒**：WAL 下直接复制主文件得到的是「打开看着正常、内容却是旧的」副本——这个坑 Etude 的注释已写清（db.py:257-259），WingMan 等于把坑留给用户还配了按钮。

**改法**（照抄 Etude db.py:254-270 与 api.py:824-837）
```python
# WingMan/backend/app/store.py 新增
def backup_to(self, dest: Path) -> Path:
    """导出一个自洽的单文件备份。不用 shutil.copy：WAL 下主文件可能缺着未 checkpoint 的写。"""
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists(): dest.unlink()
    with self._lock:                       # 复用现有 RLock
        c = sqlite3.connect(self.db_path, timeout=15.0)
        try:
            c.execute("PRAGMA busy_timeout = 15000")
            safe = str(dest).replace("'", "''")   # VACUUM INTO 不能绑变量
            c.execute(f"VACUUM INTO '{safe}'"); c.commit()
        finally: c.close()
    return dest
```
配 `POST /api/backup`（入参白名单 + 强制 `.sqlite3` 后缀，落 `EXPORTS_DIR/"backups"`）+ 设置页按钮（照抄 Etude `frontend/index.html:3114` 与 `doBackup` 3502-3524）；再补一个流式 `GET /api/export/all`（`json.JSONEncoder.iterencode` + `StreamingResponse`，**不要**在内存里拼总 dict）；README 对照 Etude README.md:303-326 补「数据在哪 / 怎么备份 / 卸载 = 删程序 + 删数据目录 / 不要直接复制 wingman.db」。

**验收**：备份文件 `PRAGMA integrity_check` = `ok` 且 `messages` 计数与源库一致（人工在测试环境执行，不在自动化里碰真实库）；备份期间新导入的消息**不**进入备份；README 有「卸载删什么」一句。

---

### D-2 【P0 · 半天】WingMan 导入一份文件**完整读 3 次**，`read_head` 实现与自己的注释相反

**现象+证据**
一次 `import_file`（registry.py:262-293）走三个都读全文件的环节：

| 序 | 环节 | 代码 | 实际行为 |
|---|---|---|---|
| 1 | `detect(path)`（:282） | → `read_head`（registry.py:35-38） | `Path(path).read_bytes()[:65536]` —— **先全量读入再切前 64 KB** |
| 2 | `adapter.meta(path)`（:287-291） | → `read_text`（wechat.py:153-158） | `read_bytes()` 全量 + 解码，**只用了 `text[:4000]`** |
| 3 | `adapter.parse(path)`（:293） | → `read_text`（wechat.py:90-91） | 全量 + 解码 + 解析 |

`read_head` 的 docstring 写着（registry.py:36）「**只读文件头部**……避免为了判定类型把几百 MB 全读进来」，实现恰恰就是它声称要避免的事。`read_text`（base.py:31-45）本身全量（`read_bytes()` base.py:36 → 试 6 种编码 base.py:28、37-45 → 完整 str）。拿到 str 后还会再拷两遍：`_layout_scores` 里 `text.splitlines()[:400]`（wechat.py:57-58，先生成**所有行**再切）与 `iter_blocks` 的 `for raw in text.splitlines()`（base.py:170）。

**为什么是问题**（估算，依据为代码路径本身：3 次全量读 + ≥2 次全量拷贝）
200 MB 的 QQ 导出：`read_bytes()` 200 MB + 解码 str 约 200-400 MB + 行列表约 200-400 MB → **进程峰值 ≈ 0.9-1.1 GB（≈ 文件大小 5 倍）**，磁盘同文件顺序读 3 遍。表现为「点了导入，界面无响应几十秒然后闪退」，用户第一反应是「软件坏了」。次要浪费：`detect()` 里 3 个适配器各自 `sniff(path, head)`（registry.py:56-58），`WeChatAdapter._layout_scores(head)` 对 64 KB 又 `splitlines()` 一次（wechat.py:79 → 57-63）。

**改法**（三处小改，不动解析逻辑）
```python
# ① registry.py:35-46 —— 真·只读头部
def read_head(path: Path, nbytes: int = 65536) -> str:
    try:
        with Path(path).open("rb") as fh:    # ← 关键：不读全文件
            raw = fh.read(nbytes)
    except OSError: return ""
    ...  # 解码逻辑不变

# ② base.py 新增 read_text_head(path, nbytes)，供 meta()/sniff() 用
# ③ wechat.py:90-102 —— parse 只 read_text 一次，score 与 parse 共用同一个 text
def _layout_scores(self, text, sample_lines=400):
    scores = {...}
    for i, ln in enumerate(text.split("\n")):   # ← 不再 splitlines() 全体
        if i >= sample_lines: break
        ...
```
并把 `import_file` 改为「先 `read_head` 一次，`meta` 接收 head 参数」（registry.py:287-291），避免 meta 再读全文件。

**验收**：新增单测断言「一次导入只发生 1 次全文件读取」；`read_head(5 MB 文件)` 的读取字节数 == 65536；现有 `test_collect_reader.py` 与适配器测试全绿。

---

### D-3 【P0 · 半天】Etude 复习队列与首页统计：`substr(at,1,10)` 让索引彻底失效，`cards` 又缺状态索引

**现象+证据**
① `due_cards()` 第一段统计「今天已复习多少张」，用函数包住了列：
```sql
-- db.py:867-873（stats() 里同款：db.py:611-615）
SELECT COUNT(*) AS n FROM reviews WHERE substr(at,1,10) = ?
```
`idx_reviews_at ON reviews(at)`（db.py:141）**存在但用不上**——表达式无法做索引范围定位 → 全表扫 `reviews`。`reviews` 一行一次评分（db.py:950-958），**只增不减**（唯一删除在 `undo_grade`，db.py:1024）。**估算**：100 张/天 × 1 年 = 36500 行；500 张/天 × 1 年 = 18 万行。这条**每次打开练习页都跑**。

② 「新卡」段（db.py:889-901）：
```sql
WHERE c.introduced = 0 AND c.suspended = 0
ORDER BY c.lesson_id, c.example_id, CASE c.channel WHEN 'read' THEN 0 ... END LIMIT ?
```
现有索引**一个都用不上**：`idx_cards_due(due_at, introduced)`（db.py:138）前导列未约束；`idx_cards_lesson(lesson_id)`（db.py:139）第三排序键是 `CASE` 表达式，索引序无法满足 → 仍需临时 B 树；`cards` 上**没有** `introduced`/`suspended` 索引。结果 = **全表扫 `cards` + JOIN + 临时排序**。行数 = 训练包 × 例句 × 5（db.py:716-726）→ **估算**：轻度 20×20×5=2000 行，重度 300×30×5=45000 行。这条**每次开始练习都跑**。

③ 同类：`stats()` 的 `introduced`/`suspended` 计数（db.py:595-610）、`list_cards` 的 `COUNT(*)`（db.py:1169-1178）。

**为什么是问题**
这是产品最核心的两个循环，全表扫 + 临时排序的费用随数据**线性上升**——本地优先应用最坏的模式：**用户越坚持用，软件越慢**。而第一轮已确认 Etude 有 249 个测试函数、单测密度 0.79，说明工程能力足够，只是没人从「数据会变大」的角度看过这两条 SQL。

**改法**
```python
# ① db.py:867-873 / 611-615 —— 换范围条件，索引立刻可用，行为等价
day = datetime.now(timezone.utc).date()
start = datetime.combine(day, time.min, tzinfo=timezone.utc).isoformat(timespec="seconds")
end   = datetime.combine(day, time.max, tzinfo=timezone.utc).isoformat(timespec="seconds")
one("SELECT COUNT(*) AS n FROM reviews WHERE at >= ? AND at < ?", (start, end))
# （at 存的就是 UTC ISO 字符串，db.py:164-166/936 —— 字典序与时间序一致）
```
```sql
-- ② 补索引 + 让 ORDER BY 不再依赖 CASE
CREATE INDEX IF NOT EXISTS idx_cards_state
    ON cards (introduced, suspended, lesson_id, example_id);
-- 推荐：加整数列替换 CASE（read/listen/speak/type/build 的字典序与 CASE 意图不同）
-- ALTER TABLE cards ADD COLUMN channel_ord INTEGER NOT NULL DEFAULT 4;
```
```sql
-- ③ stats() 的 6 遍表扫压成 1 遍
SELECT COUNT(*) AS total, SUM(introduced=1) AS introduced, SUM(suspended=1) AS suspended,
       SUM(introduced=1 AND suspended=0 AND due_at <= :now) AS due_now FROM cards
```

**验收**：造 5 万行 `cards` + 5 万行 `reviews` 夹具，断言 `EXPLAIN QUERY PLAN` 里**不出现 `SCAN cards`/`SCAN reviews`**；索引通过 `_MIGRATIONS`（db.py:154-161）落给老库且幂等（与第一轮 C-5 协同）；`test_upgrade.py` 与复习测试全绿。

---

### D-4 【P1 · 半天，三项目各一行】只设了 `journal_mode`，其余运行时参数全为默认

**现象+证据**（`grep -rn "PRAGMA"` 全仓）

| 参数 | WingMan | Etude | 现状 / 推荐 |
|---|---|---|---|
| `journal_mode` | ✅ WAL（store.py:73） | ✅ WAL（db.py:35） | **已达标**（库级持久，`init()` 跑一次即永久生效） |
| `synchronous` | ❌ 未设置 | ❌ 未设置 | **推荐 `NORMAL(1)`** |
| `busy_timeout` | 🟡 隐式 15 s（store.py:411 的 `timeout` → pysqlite 转 `sqlite3_busy_timeout`） | ❌ `sqlite3.connect(str(path), check_same_thread=False)`（db.py:184）无 timeout → **默认 5 s** | 显式声明 5000-15000 |
| `cache_size` | ❌ 默认 `-2000`（≈2 MB） | ❌ 默认 | `-16000`（16 MB）起 |
| `temp_store` | ❌ 默认（落盘） | ❌ 默认 | `MEMORY` |
| `mmap_size` | ❌ | ❌ | 可选 `268435456` |
| `PRAGMA optimize` / `ANALYZE` | ❌ 均无 | ❌ 均无 | 启动跑 `optimize`（廉价） |

`synchronous` 一句保守话：两项目都**未显式设置，取编译期默认**。SQLite 官方默认 `FULL(2)`，部分发行版编译成 `NORMAL(1)`——本机未运行程序，**具体值待确认**，请用 `python -c "import sqlite3;print(sqlite3.connect(':memory:').execute('PRAGMA synchronous').fetchone())"` 实测。但无论取哪个值，**必须显式写出来**，因为它决定「一次 commit 要不要 fsync」，直接决定 WingMan 上千次「开连接→写→commit」的导入耗时。

**为什么是问题**
- `synchronous=FULL` + WAL 是「安全但慢」：每次 commit 都 fsync WAL。WAL 下 `NORMAL` 是官方推荐——保证「断电可能丢最后几个事务、但库不会损坏」，对用户点保存这类动作完全够用。
- `cache_size` 2 MB 对 WingMan 的 `messages`（几十万行）、Etude 的 `cards`（几万行）明显偏小；`temp_store=MEMORY` 能让 D-3 那两条必然走临时排序的查询留在内存。
- Etude 的 `busy_timeout` 默认 5 s：单进程时无感，但只要用户用任何 SQLite 工具同开那个文件（排查问题时很常见），写操作会直接抛 `database is locked`——**典型的「明明能等一等却直接报错」**。

**改法**
```python
# WingMan store.py:409-413 / Etude db.py:184-186 —— 建连接后立刻设，此刻无活动事务
c.execute("PRAGMA busy_timeout = 15000")    # 显式化，不依赖 pysqlite 的 timeout 转换
c.execute("PRAGMA synchronous = NORMAL")    # WAL 下的标准配方
c.execute("PRAGMA cache_size = -16000")     # 16 MB
c.execute("PRAGMA temp_store = MEMORY")
# journal_mode 是库级持久设置，已在 SCHEMA 里设过，不必每条连接重复
```
> ⚠️ `synchronous`/`journal_mode` **不能在事务里改**；放在 `connect()` 之后安全。WingMan 的 `SCHEMA` 经 `executescript()` 执行（会先隐式提交），因此现有的 `PRAGMA journal_mode = WAL`（store.py:73）**一直是对的，不是 bug**。启动时加 `with self.conn() as c: c.execute("PRAGMA optimize")`。

**验收**：新增单测断言 `PRAGMA synchronous/busy_timeout/cache_size/temp_store` 返回期望值（`temp_store` 期望 2 = MEMORY）；WingMan `test_memory_footprint.py` 与既有测试全绿。

---

### D-5 【P1 · 半天】WingMan 每次检索全量载入整个会话的向量矩阵，且一次分析载入两遍

**现象+证据**
```python
# memory/retriever.py:132-133 —— search() 第一件事就是全量载入
ids, mat, _dim = self.store.load_embeddings(chat_id, model)
```
`load_embeddings`（store.py:1446-1465）取回该会话**所有**向量行，`np.vstack` 成 `N×D` 矩阵并 L2 归一化（1462-1464）。**无任何缓存**：`HybridRetriever` 每次 new（context.py:177、profiler.py:51），实例上的矩阵随之丢弃。

同一次分析、同一会话，矩阵被载入**两遍**：
```python
# engine/context.py:179-191
for cid in ids:
    stats = retriever.stats(cid)     # ← 第 1 次：retriever.py:206-209 也调 load_embeddings
    if stats["indexed"] == 0: ...
    pack.retrieved.extend(await retriever.search(cid, peer_message, ...))  # ← 第 2 次
```
`stats()` 只为拿 `len(ids)`。`search_multi`（retriever.py:196-204）按查询数循环调 `search` → 载入次数 = 查询数。

**为什么是问题**（估算：`512 × 4 B × N`，`embed_dim` 默认 512，config.py:155）
5000 条 ≈ 10 MB/次；20000 条 ≈ 40 MB/次；50000 条 ≈ 100 MB/次。一次分析是 `for cid in ids` 的**每个勾选渠道各 2 次**（`stats` + `search`，context.py:179-191），所以 M 个渠道的总量 = `2M × 单次矩阵`：3 个渠道各 2 万条 → 约 **240 MB 的矩阵读入量**，全部发生在一次 HTTP 请求内。矩阵之外还有 `fetchall()` 的 N 个 Row、逐行 `_to_np` 反序列化（store.py:1462）与 `np.vstack` 临时拷贝，峰值更高。仓里已有 `test_memory_footprint.py`，说明作者关心内存，但没覆盖这条路径。**检索质量（无切块/无 rerank/零评测）属 ai-eng 的 A-7，本条只谈内存与 I/O。**

**改法**
```python
class HybridRetriever:
    def __init__(self, store, embedder):
        self.store, self.embedder = store, embedder
        self._mat_cache = {}
    def _matrix(self, chat_id, model):
        key = (chat_id, model)
        if key not in self._mat_cache:
            self._mat_cache[key] = self.store.load_embeddings(chat_id, model)
        return self._mat_cache[key]
    # search() 用 _matrix()；stats() 用 _matrix()
```
实例缓存只能救「同一次分析内的两次调用」；跨请求复用需把缓存放到 `AppContext`（context.py:43-44 已有 `_llm`/`_embedder` 同款惰性缓存位），并在 `upsert_embeddings`（store.py:1415-1431）成功后打失效标记（用一个单调计数器作 key）。另加 `store.count_embeddings_for_chat()` 让 `context.py:180` 改走一条 COUNT，第 1 次载入彻底消失。长线（写 ROADMAP）：上到 10 万级换 `sqlite-vec`——store.py 模块 docstring 第 6-7 行已预留这条路。

**验收**：monkeypatch `load_embeddings` 计数，断言 `build_context` 对同渠道调用 **0 次**（stats 改 COUNT 后）/或 ≤1 次（缓存版）；连续两次 `search` 同 `chat_id` 只载入 1 次；`upsert_embeddings` 后缓存失效。

---

### D-6 【P1 · 半天】WingMan 为抽 8 行 / 80 行样本，把整段会话全量读进内存

**现象+证据**（三处同构，全部由 `all_messages()`（store.py:1314-1319，`SELECT * ... ORDER BY id` + `dict(r)` 全量物化）造成）

① **每次分析请求**（点分析/建议/推演都跑）：
```python
# engine/context.py:199-206；MAX_STYLE_SAMPLES = 8（context.py:40）
for cid in ids:
    peer_rows.extend(r for r in ctx.store.all_messages(cid) if r.get("role") == "peer")  # ← 201
```
② **逐渠道建画像**，同一次请求读两遍：
```python
# memory/profiler.py:216-225 —— 循环里 build_index + extract_facts（:60 又一次 all_messages）
# memory/profiler.py:247-252 —— 再循环一遍
rows = ctx.store.all_messages(ch.chat_id)   # ← 248
sample.extend(... _sample_evenly(lines, per_chat))   # per_chat = max(10, 80 // 渠道数)
```
③ `summarize_period`（profiler.py:320-324）读全量后只取 `rows[-200:]`。

**为什么是问题**（估算）
| 场景 | 实际需要 | 实际读取 |
|---|---|---|
| 分析一次（1 个 2 万条渠道） | 8 行 | 2 万行 × 全部列（含 `text`） |
| 整理一个人（3 渠道各 2 万条） | 每渠道 ≤27 行样本 | `all_messages` × 6 次 = **12 万行** |
| 生成周摘要（2 万条） | 最后 200 行 | 2 万行 |

一行 `messages` 的 dict 含 12 个字段（store.py:85-101 + 迁移列），CPython 下每行约 1 KB 量级 → **2 万行 ≈ 20 MB 常驻**，且每次重建、每次 `ORDER BY id` 全扫。这是「桌面程序长跑越来越卡」最可能的来源之一。难被发现的原因：`_sample_evenly`（profiler.py:41-46）需要 `len(lines)` 才算步长，看上去「必须先全量」——其实 SQL 侧先 COUNT 再按步长取即可。

**改法**
```python
# store.py 新增 —— SQL 侧均匀取样，不把整段会话读进内存
def style_sample(self, chat_id: str, limit: int = 8) -> list[str]:
    total = self._scalar("SELECT COUNT(*) FROM messages WHERE chat_id=? AND role='peer'"
                         " AND msg_type='text'", (chat_id,))
    if not total: return []
    step = max(1, total // limit) if total > limit else 1
    rows = self._query("""
        SELECT text FROM (
            SELECT text, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM messages
             WHERE chat_id=? AND role='peer' AND msg_type='text' AND length(text) BETWEEN 4 AND 60
        ) WHERE (rn - 1) % ? = 0 ORDER BY rn DESC LIMIT ?""", (chat_id, step, limit))
    return [r["text"] for r in rows]
```
- `profiler.py:60` 与 `:248` 合并为「一次读取、两边复用」（函数吃 `rows`），读取方式改同上；
- `summarize_period` 改 `recent_messages(chat_id, 200)`——**store.py:1277 已有这个方法，这是一行改动**；
- 加一条 `grep` 守卫：禁止 `engine/` 与 `api/` 直接出现 `store.all_messages(`。

**验收**：monkeypatch `all_messages` 抛异常后跑 `build_context` **必须不抛**；`style_sample` 在 1000 条假消息上返回 8 条且首尾各有；`summarize_period` 只读 ≤200 行。

---

### D-7 【P1 · 半天】`facts.person_id` 无独立索引，`list_facts_for_person` 的 `OR` 写法让部分唯一索引也用不上

**现象+证据**
```sql
-- store.py:1542-1547
SELECT * FROM facts WHERE (
  (person_id IS NOT NULL AND person_id <> '' AND (chat_id IS NULL OR chat_id = '')) AND person_id = ?
  OR chat_id IN (SELECT id FROM chats WHERE person_id = ?))
```
`facts` 上的索引只有 `UNIQUE(chat_id, subject, key, value)`（store.py:68）与**部分唯一索引** `ux_facts_person ... WHERE person_id IS NOT NULL AND ...`（store.py:641-647）。跨索引的 `OR` 优化要求每个分支各自能用索引；第一个分支虽带 `person_id = ?`，但索引是带 `WHERE` 谓词的**部分索引**，要命中它必须让规划器证明谓词被满足，而它被包在显式 `OR` 里 → 通常放弃 → **全表扫 `facts`**。此判断来自 SQLite 部分索引的匹配规则，**标注为推断（未跑 `EXPLAIN QUERY PLAN`）**。

调用密度才是关键：一次分析调 1 次（context.py:138）；一次画像整理调 **3 次**：
```python
# memory/profiler.py
before_ids = {f.id for f in ctx.store.list_facts_for_person(person_id)}   # 212
facts = ctx.store.list_facts_for_person(person_id)                        # 235
after_ids = {f.id for f in ctx.store.list_facts_for_person(person_id)}    # 296
```
而它 `SELECT *`（含 `evidence` 长文本）并 Python 侧逐行构对象（store.py:1555-1563）。

**为什么是问题**
`facts` 是画像与提示词的核心输入，写入路径多（`replace_facts`/`upsert_fact`/`upsert_person_fact`），store.py:45-56 的注释记录了「唯一键写错导致事实静默覆盖」的历史，说明这张表在真实使用中被反复重写 → 行数增长 → 全表扫代价增长。与 D-6 叠加：点一次「整理画像」，同一份 `facts` 全表扫 3 遍、整段会话全量读 6 遍。

**改法**
```sql
-- ① 补索引（最省事，立刻生效）
CREATE INDEX IF NOT EXISTS idx_facts_person ON facts (person_id);
CREATE INDEX IF NOT EXISTS idx_facts_chat   ON facts (chat_id);
```
```python
# ② OR 改 UNION ALL（两个分支各自走索引，且保持「同一条事实两处出现返回两条」的既有语义
#    —— store.py:1537-1541 明确要求不去重，所以不能用 UNION）
sql = f"""
    SELECT * FROM facts WHERE {_FACTS_PERSON_SCOPE} AND person_id = ?{extra}
    UNION ALL
    SELECT * FROM facts WHERE chat_id IN (SELECT id FROM chats WHERE person_id = ?){extra}"""
```
③ 新增轻量 `fact_ids_for_person()`，替掉 profiler.py:212/296 那两处「只要 id 集合」的调用。

**验收**：`EXPLAIN QUERY PLAN` 输出里不出现 `SCAN facts`（允许 `SEARCH facts USING INDEX`）并写成测试；既有 facts 测试全绿（含「两处都出现时返回两条」那条语义测试）。

---

### D-8 【P1 · 1 天】`find_person_by_alias` 为匹配一个名字把**每个人的 3 条聚合查询**跑一遍；采集主循环 2 次/会话

**现象+证据**
```python
# store.py:878-892
for p in self.list_persons():          # ← 894-897：全量拉取，内部逐人调 _person_with_stats
    if p.name.strip().lower() == key: return p
```
`_person_with_stats`（store.py:899-954）每次开连接跑 **3 条聚合查询**：`messages JOIN chats ... WHERE ch.person_id=?` 的 group-agg（:906-918）、渠道数（:924-926）、**两表 JOIN 的向量计数**（:927-932）。

调用密度——采集主路径每会话 2 次：
```python
# collect/pipeline.py:548（_collect_one_chat 内，由 _collect_table 按会话循环调）
person = store.find_person_by_alias(name) or store.find_person_by_alias(peer_key)
```
上层：`pipeline.py:494-496` → `for m in maps: _collect_table(...)`。

**为什么是问题**（估算）
设会话数 C、人数 P：**采集一次 ≈ 2·C × 3·P 条聚合查询**，外加 2·C 次「取 `_lock` + `connect()` + `close()`」。C=20/P=20 → 2400 条（无感）；C=200/P=200 → **24 万条**，其中 1/3 是两表 JOIN 计数——已不是「慢」而是「点一下采集等几分钟」。而它**只需要 `name` 和 `aliases` 两个字段**，却付了整套统计的代价。`ensure_person_for_chat` 里还有一次同样的调用（store.py:735），因 `_collect_one_chat` 传了 `person_id` 会在 store.py:717-720 提前返回而「暂时躲过」——任何调用方漏传即成本回归。

**改法**
```python
# ① 单条 SQL 精确查，不再借道 list_persons；命中时才付一次统计代价
def find_person_by_alias(self, name: str) -> Person | None:
    key = (name or "").strip()
    if not key: return None
    row = self._query_one(
        "SELECT id FROM persons WHERE name = ? COLLATE NOCASE OR aliases LIKE ? COLLATE NOCASE LIMIT 1",
        (key, f'%"{key}"%'))        # aliases 存 JSON 数组文本（store.py:867）
    return self.get_person(row["id"]) if row else None
# 索引：CREATE INDEX IF NOT EXISTS idx_person_name_nocase ON persons (name COLLATE NOCASE);
```
```sql
-- ② 确实需要「所有人的统计」时，一次 SQL 代替 P 次往返
SELECT ch.person_id, COUNT(m.id) AS total, SUM(m.role='peer') AS peer_cnt,
       SUM(m.role='me') AS me_cnt, MIN(m.ts), MAX(m.ts)
  FROM chats ch LEFT JOIN messages m ON m.chat_id = ch.id GROUP BY ch.person_id
```
（`list_persons` 用这条 + 渠道数 + 索引量各 1 条，把 3P 压成 3。）

**验收**：造 200 person × 100 条消息夹具，断言 `find_person_by_alias` 触发 SQL **≤2 条**（`set_trace_callback` 计数）；采集流程测试断言 SQL 条数与会话数**线性**（当前 N×P 量级）；精确匹配语义不变（`小明` 不匹配 `小明明`，大小写不敏感——保留 store.py:880-882 的承诺）。

---

### D-9 【P1 · 1 天】逐会话/逐人开连接：`list_chats`、`person_detail`、`_backfill_persons`、`merge_persons`

**现象+证据**（`conn()` 每次新建连接 + 提交 + 关闭，store.py:408-420；WAL 下每次 commit 都是一次写事务）

| # | 位置 | 循环内动作 | 连接/提交次数 |
|---|---|---|---|
| ① | `list_chats`（:794-802） | `for cid in ids: self.get_chat(cid)`（各一次 `with self.conn()`，:756，跑 3 条查询 757/760-770/771-775） | **N 次连接 + N 次 commit** |
| ② | `person_detail`（:1058-1081） | `for cid in ids: self.get_chat(cid)`（:1070） | N 次 |
| ③ | `_backfill_persons`（:519-537） | `for row in rows: self.ensure_person_for_chat(...)`（:535），后者 ≥1 次 `conn()`（:711）+ 可能 `find_person_by_alias`（:735）+ `bind_chat`（:719/:738）+ `create_person`（:741） | 每个无归属会话 **1-4 次**，**在 `init()` 启动路径上** |
| ④ | `merge_persons`（:1006-1042） | `for mid in merge_ids:` 内 `with self.conn()`（:1028-1031） | 每人 1 次 |

**为什么是问题**
- ①/② 是第一轮 **W-3**（`list_chats` 是 1+3N 次查询）的**另一半**：即使把查询合成一条，只要还在循环里 `with self.conn()`，就仍有 N 次「开库句柄 → 提交（fsync）→ 关闭」。**改法必须同时覆盖查询数与连接数**，否则用户感觉不到差别。
- ③ 在**启动路径**上，最容易被忽略：老库若 M 个会话都无归属，`init()` 会跑 M 次完整往返且每次持一次全局锁 → 「升级完第一次打开特别慢」。
- ④ 是**正确性**问题（性能之外）：整个循环**没包在一个事务里**。`merge_ids` 第 2 个 id 处理到一半失败 → 第 1 个 id 的 `chats.person_id` 已改、`persons` 行已删，第 2 个还没动 → **静默半成品**。Etude 的注释（db.py:1120-1123）明确要避免这类状态。

**改法**
```python
# ① 机制层：把「每次开连接」改成线程本地复用（保持现有串行语义，行为零变化）
self._local = threading.local()
def _connect(self):
    c = getattr(self._local, "conn", None)
    if c is None:
        c = sqlite3.connect(self.db_path, timeout=15.0); c.row_factory = sqlite3.Row
        for p in ("PRAGMA busy_timeout=15000", "PRAGMA synchronous=NORMAL",
                  "PRAGMA cache_size=-16000", "PRAGMA temp_store=MEMORY"):
            c.execute(p)
        self._local.conn = c
    return c
@contextmanager
def conn(self):
    with self._lock:
        c = self._connect()
        try: yield c; c.commit()
        except Exception: c.rollback(); raise
        # 不再 close()：连接随线程存活
```
（`asyncio.to_thread` 用的是 anyio 线程池、线程会复用 → 连接数有上界，不会泄漏；D-4 的 PRAGMA 只需在 `_connect()` 设一次。更彻底的做法是连接池 + `mode=ro` `query_only` 只读连接——WingMan `preflight.py:895-897` 已示范，但那是第二步。）
```python
# ② list_chats 一次连接一条 SQL（LEFT JOIN messages/embeddings + GROUP BY ch.id）
#    并把 get_chat 的单会话版本抽成 _chat_info_from_row 与之共用，避免两套口径
```
```python
# ③ merge_persons 包事务（正确性优先）
with self._lock:
    with self.conn() as c:                 # 一个连接、一个事务；conn() 退出时 commit
        for mid in merge_ids:
            if mid == keep_id: continue
            c.execute("UPDATE chats SET person_id=? WHERE person_id=?", (keep_id, mid))
            c.execute("UPDATE collect_cursors SET person_id=? WHERE person_id=?", (keep_id, mid))
            c.execute("DELETE FROM persons WHERE id=?", (mid,))
```
④ `_backfill_persons` 同样收敛成「一次读 → 一个事务内批量写」；`ensure_person_for_chat` 拆成纯计算 + 写两半。

**验收**：N=100 会话时 `list_chats` 的 SQL 条数 == 1、`conn` 调用 == 1；`merge_persons` 失败注入后 `chats.person_id` 与人行数**都回到合并前**（当前会留半成品）；`_backfill_persons` 在 500 会话老库夹具上 SQL 条数降一个数量级且结果集完全一致。

---

### D-10 【P1 · 1 天】Etude：长事务一直持着全局锁，批量操作逐行提交 / 逐行往返

**现象+证据**（连接模型是「单例连接 + 一把 RLock」，db.py:27-28、176-200；`query/execute` 都在锁里，:235-251）

| 函数 | 位置 | 事务内行级操作 | 后果 |
|---|---|---|---|
| `finish_lesson` | db.py:639-731 | 例句循环（:675-699）+ swaps（:701-714）+ **例句 × 5 通道**卡片循环（:716-726） | 一次生成落库全压在一个持锁事务里 |
| `add_example` / `rebuild_cards` / `delete_example` | :372-417 / :454-489 / :430-442 | 逐条 INSERT / 双层循环补卡 / 2 条 DELETE | 缺卡多时持锁时间长 |
| `push_cards` | :1092-1116 | **每张卡 1 次 SELECT + 1 次 UPDATE**（:1097-1110） | 批量推 5000 张 = 10000 次语句，全程持锁 |

写入方是后台线程池 `_POOL = ThreadPoolExecutor(max_workers=3)`（api.py:49），前台是 FastAPI 的同步 `def` 端点（也走线程池）——**两类线程抢同一把 `_LOCK`**。

另：`set_cards_srs`（db.py:1119-1129）**故意**逐张调 `set_card_srs`，而后者是 `one(...)` 读 + `execute(...)` 写、**每次写都 commit**（db.py:246-251）→ N 张卡 = N 次事务提交（WAL 下 N 次 fsync），**且没有包在同一事务**。作者理由在 db.py:1120-1123（任一张失败就整体报错），但「报错」≠「回滚」，现在是**报错了而前面若干张已提交**。

**为什么是问题**
- 用户可感知形态：**生成训练包的过程中，界面上点任何东西都要等**——后台任务在长事务里握着唯一的锁，前台读请求（哪怕只是 `stats()` 或 `due_cards()`）也拿不到锁。
- `push_cards` 本来就是为「批量」设计的（db.py:1086-1089），实现却是 N 次往返。
- `set_cards_srs` 的「报错不回滚」是**静默的数据半改**，与 D-9 ④ 同类。

**改法**
```python
# ① push_cards 集合式：1 次读取 + 1 次 executemany（原来 2N 次往返）
rows = conn.execute(f"SELECT id, due_at, interval FROM cards WHERE id IN ({q})", ids).fetchall()
payload = [...(算好的 (due_iso, interval+days, id))...]
conn.executemany("UPDATE cards SET due_at=?, interval=? WHERE id=?", payload); conn.commit()

# ② set_cards_srs 加外层事务（不再「报错但前面几张已改」）
with _LOCK:
    conn = connect()
    try:
        conn.execute("BEGIN")
        for card_id in card_ids: _apply_card_srs(conn, int(card_id), patch)  # 内核不 commit
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK"); raise

# ③ finish_lesson 的卡片插入改 executemany：150 次 execute → 1 次
conn.executemany("INSERT INTO cards (...) VALUES (?,?,?,?,0,2.5,0,0,0)",
                 [(lesson_id, eid, ch, ts) for eid in example_ids for ch in CHANNELS])
```
④ 结构调整（与第一轮 `api.py` 拆包一起做）：把「持锁长事务」拆成「组装数据（无锁）→ 一次短事务落库」。`finish_lesson` 的循环里没有任何依赖数据库的读，完全可以先在内存组好全部行再一个事务写入。

**验收**：`push_cards` 100 张卡只产生 **2 条语句**；`set_cards_srs` 第 3 张抛错时前 2 张的 `interval/due_at` **未改动**；并发测试断言一个线程跑 `finish_lesson` 时另一个线程的 `stats()` 等待时间 < 阈值（当前会等到事务结束）。

---

### D-11 【P1 · 半天】Etude 日志无轮转、每训练包一个只增文件，且落在**数据目录内部**

**现象+证据**
```python
# pipeline.py:630-636
def _append_log(name, lines):
    path = log_dir() / f"{name}.log"      # 调用点传 lesson-<id>（:625-627）→ 每训练包一个文件
    with path.open("a", encoding="utf-8") as fh: fh.write("\n".join(lines) + "\n")
```
追加写、**无上限、无轮转、无清理**；`log_dir()` 在**数据目录内**：`writable_root() / "logs"`（paths.py:170-173），而 `writable_root()` 就是 `%LOCALAPPDATA%\Etude` 或用户指定的搬迁目标（paths.py:126-134）。

对照 WingMan：`RotatingFileHandler(LOG_DIR/"wingman.log", maxBytes=2*1024*1024, backupCount=3)`（main.py:49-54），且 `LOG_DIR = APP_DIR/"logs"` 与 `DATA_DIR = APP_DIR/"data"` **是兄弟目录**（config.py:64-65）——**这两点 WingMan 都做对了**。

**为什么是问题**
1. **无限增长**：生成失败重试会追加，长跑一年 = 训练包数 × 每次生成的流水量；流水里含模型返回的原文片段（`_write_log` 调用点在生成流程内）——既是体积也是**隐私面**。
2. **落在数据目录内**三重后果：用户按 README 指引手动备份/搬迁整个数据目录（README.md:326）时日志被一起搬走、撑大备份；README.md:305-314 的目录清单把 `logs/` 与 `audio/`、`images/` 并列，用户会以为它是数据；按 500 提示（api.py:861-870「把这段连同数据目录里的 logs 一起反馈给作者」）打包发出时，可能连带发走**模型生成的例句原文**。

**改法**
```python
# 照抄 WingMan 已验证的写法；保留「每训练包一段」靠行首标记而非文件分割
from logging.handlers import RotatingFileHandler
_LOG_FH = None
def _append_log(name, lines):
    global _LOG_FH
    try:
        if _LOG_FH is None:
            _LOG_FH = RotatingFileHandler(log_dir() / "etude.log", maxBytes=2*1024*1024,
                                          backupCount=3, encoding="utf-8", delay=True)
        _LOG_FH.write(f"== {name} ==\n" + "\n".join(lines) + "\n"); _LOG_FH.flush()
    except OSError: pass
```
② 保留策略挂到已有的启动清理点 `pipeline.recover_stale()`（pipeline.py:68-84）：删 >30 天或总量 >20 MB 的旧日志。③ README.md:305-314 的 `logs/` 加一行「**排错用的流水，不是你的数据；备份时可以不要**」。

**验收**：连续写 10 MB 日志后 `logs/` 文件数 ≤4、总量 ≤8 MB；README 目录清单更新。

---

### D-12 【P1 · 1 天】无任何数据完整性体检：没有 `integrity_check`、没有孤儿行自检、没有 `VACUUM`/`ANALYZE`/`optimize`

**现象+证据**
- 全仓 `grep -rni "integrity_check"` 在 `WingMan/backend`、`WingMan/scripts`、`Etude/backend`、`Etude/scripts`、`TideWatch/src` → **0 命中**。
- WingMan 自检只做到「数得出来 + 看文件大小」：`counts = ctx.store.counts()`（6 个 `COUNT(*)`）+ `Path(db_path).stat().st_size`（selfcheck.py:152-186）。库损坏、页级错误、孤儿行、索引不一致——一项都查不出。Etude 自检（selfcheck.py:75-96）只到「`db.stats()` 能不能跑通」。
- `VACUUM`：WingMan 全无；Etude 只有备份用的 `VACUUM INTO`（db.py:268）——**导出副本 ≠ 回收本库空间**，删行后的空闲页仍留在文件里。`ANALYZE` / `PRAGMA optimize` 三项目全无。

**为什么是问题**（与第一轮 3.1 的关系）
第一轮修的是**增量**：改 `conn()` 后不再产生新孤儿。但用户手上**已经存在**的库里可能已有旧版本产生的孤儿行——修代码不会让它们消失，而**没有任何工具能告诉用户「你的库现在脏不脏」**。孤儿行不报错，只会让「这个人名下怎么多了几条查不到出处的记录」慢慢出现。

库文件长期只增不减：WingMan 的 `messages`/`embeddings` 在 `delete_chat`（:804-807）、`delete_messages`（:1364-1374）后页不回收；Etude 的 `reviews` 只增（唯一删除在 `undo_grade`，db.py:1024）。**估算**：导入过 3 次又重新导入的用户，库里可能有 2/3 是死页——而这个文件正是 `%LOCALAPPDATA%` 下用户唯一需要备份的东西。另：从未 `ANALYZE` → 规划器没有 `sqlite_stat1`，D-3/D-7 那两个「索引用不上」的判断在它眼里更没有依据。

**改法**
```python
# ① 自检加一项（WingMan selfcheck.py 新增；Etude 同构）
def _check_db_integrity(s, ctx):
    with ctx.store.conn() as c:
        res = c.execute("PRAGMA quick_check").fetchone()[0]     # 只读、跳过索引一致性，比 integrity_check 快
    orphans = {
        "messages（无主会话）": "SELECT COUNT(*) FROM messages m LEFT JOIN chats ch ON ch.id=m.chat_id WHERE ch.id IS NULL",
        "embeddings（无主消息）": "SELECT COUNT(*) FROM embeddings e LEFT JOIN messages m ON m.id=e.message_id WHERE m.id IS NULL",
        "facts（chat_id 指向不存在的会话）":
            "SELECT COUNT(*) FROM facts f LEFT JOIN chats ch ON ch.id=f.chat_id "
            "WHERE f.chat_id IS NOT NULL AND f.chat_id <> '' AND ch.id IS NULL",
    }
    ...   # status: ok / warn（有孤儿行）/ fail（quick_check != ok）
    # 文案：「库完好；发现 127 条孤儿记录（旧版本遗留）。点『清理』可修复 →」
    # 清理 = 上面三段 DELETE ... WHERE ... IS NULL，一个事务，**执行前先自动备份**
```
```python
# ② 加「压缩数据库」动作 + 按钮
def compact(self) -> dict[str, int]:
    """回收空闲页。必须先备份 —— VACUUM 会占用约 2× 磁盘，
    且是全库重写（几十万条要几十秒），该由用户决定什么时候做。"""
    before = self.db_path.stat().st_size
    with self._lock:
        c = self._connect(); c.execute("VACUUM"); c.execute("ANALYZE"); c.commit()
    return {"before": before, "after": self.db_path.stat().st_size}
```
③ 启动时 `PRAGMA optimize`（见 D-4）。

**验收**：注入 3 条孤儿行（绕过外键直接 INSERT）→ 自检 `warn` 且数量为 3，清理后为 0 且正常行数不变；`compact()` 在删 10 万行的库上使文件变小且 `quick_check` 仍 `ok`。

---

### D-13 【P1 · 半天】无数据保留策略，只增不减的结构没有任何出口

**现象+证据**：`grep -rni "retention|prune|cleanup|purge|保留.*天|定期删除"` 在三仓应用代码 → **0 命中**。

| 项目 | 只增不减 | 写入频率 | 证据 |
|---|---|---|---|
| WingMan | `activity_log` | 每次导入/采集/编辑/画像一行 | store.py:1833-1856 |
| WingMan | `engine_runs` | 每次指挥台运行一行，含**模型生成的回复原文** | store.py:1719-1751 |
| WingMan | `sim_runs` / `summaries` | 每次推演 / 每次摘要一行 | store.py:1797-1816 / 1614-1624 |
| Etude | `reviews` | 每次评分一行（唯一删除在 `undo_grade`） | db.py:950-958、1024 |
| Etude | `_JOBS` / `logs/lesson-*.log` | 每 lesson/plan 一个 dict 永不删 / 每包一个只增文件 | pipeline.py:36、61-65 / 630-636 |

WingMan 仅有单条/单次级清理：`delete_run`（:1789-1795）、`delete_fact`（:1608-1610）。

**为什么是问题**
`engine_runs` 存的是**模型生成的回复原文**（store.py:1732 注释自己写明了「隐私」），既占体积又是隐私面却**没有上限**。`activity_log` 是「有动作就有痕迹」的产品承诺（store.py:1843-1845），但没人会翻三年前的采集痕迹——一个只为「看最近发生了什么」存在的表却要永久保留。`reviews` 更微妙：它同时是历史记录**和**当天的配额依据（db.py:867-873），不能简单删——正确做法是保留最近 N 天 + 让配额查询只扫今天（D-3 修完后它本身就是范围查询）。

**改法**
```python
# WingMan store.py 新增（放在 init() 之后或「设置 → 维护」里手动触发）
RETENTION = {"activity_log_days": 180, "engine_runs_keep": 500, "sim_runs_keep": 2000}
def prune(self) -> dict[str, int]:
    """清理只增不减的痕迹表。**只删痕迹，不碰用户资产**（messages/facts/summaries）。"""
    cutoff = (datetime.now() - timedelta(days=RETENTION["activity_log_days"])).isoformat(" ", "seconds")
    with self.conn() as c:
        n_act = c.execute("DELETE FROM activity_log WHERE ts < ?", (cutoff,)).rowcount
        n_sim = c.execute("DELETE FROM sim_runs WHERE run_id NOT IN "
                          "(SELECT id FROM engine_runs ORDER BY id DESC LIMIT ?)",
                          (RETENTION["sim_runs_keep"],)).rowcount
        n_run = c.execute("DELETE FROM engine_runs WHERE id NOT IN "
                          "(SELECT id FROM engine_runs ORDER BY id DESC LIMIT ?)",
                          (RETENTION["engine_runs_keep"],)).rowcount
    return {"activity_log": n_act, "sim_runs": n_sim, "engine_runs": n_run}
```
（`engine_runs` 是「上次问过什么」的功能，不宜按时间删，按**条数保留最近 N 条**；删前提示「将删除最早的运行记录」。）Etude：删除训练包时顺手 `.pop(job_key_lesson(id))`（在 `api.py` 侧做，因为 `pipeline` 与 `db` 目前不互相引用）；`reviews` 保留最近 400 天（`last_review` 只取最近一条，db.py:983-986，不受影响）。全部默认开启但可关，设置页显示当前体积。

**验收**：造 1000 条一年前的 `activity_log` + 1000 条 `engine_runs`，`prune()` 后计数符合 `RETENTION` 且 `messages`/`facts`/`summaries` 行数**完全不变**；`prune()` 幂等；Etude 删训练包后 `_JOBS` 对应 key 消失。

---

### D-14 【P2 · 半天】`search_text` 的 `LIKE '%…%'` 与 `index_chat` 的重复从头扫

**现象+证据**
① 关键词召回用不可索引的 `LIKE`（store.py:1299-1311）：`where = " OR ".join(["text LIKE ?"] * len(terms))`，最多 8 个 `%term%`；`idx_msg_chat_ts` 只能把范围缩到一个会话，会话内**逐行 LIKE + 逐行排序取前 200**。它是混合检索的第二路（retriever.py:150，`limit=400`），**每次分析都跑**。

② 建索引的循环每轮从会话头部重扫（retriever.py:90-108）：
```python
while total < max_items:                      # max_items = 20000
    rows = self.store.unembedded(chat_id, model, limit=batch_size)   # batch_size = 256
```
`unembedded`（store.py:1433-1444）= `LEFT JOIN embeddings ... WHERE 缺失 ORDER BY m.id LIMIT 256` → **每轮都从头找「还没向量化的前 256 条」**。2 万条/256 ≈ 79 轮，每轮从会话起点扫到当前进度 → **估算 O(N²/批) ≈ 79 万行次扫描**。

**改法**
```python
# ① instr 替 LIKE（等价语义、通常更快）；正解是 FTS5 虚表（trigram 分词对中文子串友好）
conn.execute("SELECT ... WHERE chat_id=? AND instr(text, ?) > 0 ...", ...)
# 建议单独立 ROADMAP 项：CREATE VIRTUAL TABLE messages_fts USING fts5(text, content='messages', content_rowid='id')
```
```python
# ② index_chat 加游标，把「从头扫」变成「接着扫」
last_id = 0
while total < max_items:
    rows = self.store.unembedded_after(chat_id, model, after_id=last_id, limit=batch_size)
    if not rows: break
    last_id = int(rows[-1]["id"]); ...
# store.unembedded_after = 原 SQL 上加 AND m.id > ?
```

**验收**：`search_text` 结果集与改前**完全一致**（对照测试）；`index_chat` 在 5000 条未索引消息上的扫描行数随批次数**近似线性**而非平方。

---

### D-15 【P2 · 2 小时】Etude `readiness()` 对每条例句做两次磁盘 `exists()`

**现象+证据**（db.py:545-561，由 `lesson_detail()` 调用 db.py:506，**每次打开训练包详情都跑**）
```python
for row in examples:
    if not rel or not (audio_dir() / rel).exists():    # ← :556 一次 stat
        missing_audio.append(row["id"])
    if not img or not (images_dir() / img).exists():   # ← :560 又一次 stat
        missing_image.append(row["id"])
```
作者意图是好的（「记录里有路径、磁盘上没有」最阴，db.py:554-555），问题只在实现方式。**估算**：30 条例句 → 60 次 stat；若被用于列表则 100 包 × 60 = 6000 次。用户把数据目录搬到机械盘/移动盘/网络盘时（paths.py:11-21 **明确支持搬到别的盘**），stat 的毫秒级延迟会让打开详情等几百毫秒。

**改法**
```python
have_audio = {e.name for e in os.scandir(audio_dir())} if audio_dir().exists() else set()
have_image = {e.name for e in os.scandir(images_dir())} if images_dir().exists() else set()
for row in examples:
    if not rel or rel not in have_audio: missing_audio.append(row["id"])
    if not img or img not in have_image: missing_image.append(row["id"])
```
（一次 readdir 远小于 N 次 stat；目录文件极多时可加「N > 阈值才建集合」。）

**验收**：monkeypatch `exists/stat` 计数，断言 30 条例句的 `readiness` 触发 ≤2 次（目录级）；`missing_*_ids` 与改前一致。

---

### D-16 【P2 · 半天】TideWatch：`by_topic()` 每次调用重建整份分组，`KeywordSignal` 每个命中重建集合

**现象+证据**
① 分组无缓存（types.py:173-178；`by_actor()` :180-185 同构；`time_span` 是 property，每次访问构造完整 datetime 列表 :187-192）。单次 `run` 的调用：`coordination.py:69`、`coordination.py:153`、`pipeline.py:113`（`len(data.by_topic())`，**只为取一个数量**）、`cli.py:172/203`、`account_signals.py:56`（`time_span`）、`signals/base.py:133`（`by_actor()`）→ **同一次分析 `by_topic()` 重建 3 次**，每次都是 O(N) 遍历 + 新建 dict 与列表。

② 权重查询「每命中重建集合 + 线性扫描」（text_signals.py:149-153）：
```python
weights = [self.rules.group_weight(tag) if tag in {g.tag for g in self.rules.phrases}   # ← 每个 tag 重建一次集合
           else self.rules.regex_weight(tag) for tag in tags]
```
`group_weight`（rules.py:143-147）与 `regex_weight`（:149-153）都是**线性遍历**。

**为什么是问题**
TideWatch 是三个项目里架构最好的（第一轮评 A），且是一次性 CLI，所以这些开销**当前不致命**。但 `Pipeline.run` 是 `for signal in self.signals`（pipeline.py:78-82）——10 个信号各自遍历全量 items，任何一个顺手再调一次 `by_topic()` 就多一次 O(N)。这个项目明确「面向未来规模」（第一轮也点了 `CoOccurrenceSignal` 的 O(A²)），顺手摘掉这些白送的 O(N) 性价比很高。

**改法**
```python
# types.py —— Dataset 加惰性缓存字段（_by_topic/_by_actor，init=False + invalidate() 可选）
def by_topic(self):
    if self._by_topic is None:
        out = {}
        for item in self.items: out.setdefault(item.topic or "__all__", []).append(item)
        self._by_topic = out
    return self._by_topic
@property
def topic_count(self) -> int:      # pipeline.py:113 与 cli.py 用它，别再建整份分组
    return len({i.topic or "__all__" for i in self.items})
```
```python
# rules.py —— 加载时建好 tag→weight 映射，替掉两条线性扫描
@classmethod
def load(cls, directory):
    book = cls(phrases=..., fold_map=..., regexes=..., stopwords=...)
    book._group_w = {g.tag: g.weight for g in book.phrases}
    book._regex_w = {r.tag: r.weight for r in book.regexes}
    return book
def weight_of(self, tag: str) -> float:
    """一条 O(1) 权重查询。"""
    return self._group_w[tag] if tag in self._group_w else self._regex_w.get(tag, 1.0)
```
`text_signals.py:149-153` 改成 `weights = [self.rules.weight_of(t) for t in tags]`。

**验收**：`by_topic()` 连调 3 次只遍历 items 1 次（计数器桩）；`weight_of` 与旧两方法在所有 tag（含两个表都没有的 tag）上结果一致（对照测试）；`tests/` 全绿。

---

### D-17 【P2 · 2 小时】TideWatch `MappedAdapter.load` 与自己的类注释相反；库代码用 `print`

**现象+证据**
```python
# adapters/base.py:98-103（类注释）
"""...load() 接受任何可迭代的 dict 序列 —— 列表、生成器、Iterator 都行。
这样可以边读边转，不必把整份数据先读进内存。"""
# adapters/base.py:112-130（实际）
items: list[Item] = []
for index, record in enumerate(source):
    ...
    items.append(item)          # ← 全量累积
```
**注释承诺流式，实现是「解析流式、结果全量驻留」**。对水军识别引擎，输入就是上百万条评论，`Dataset.items` 全量 + 10 个信号各自的派生结构（token 列表、simhash、topic 倒排）必然同时驻留。这本身是可接受的取舍（协同信号需要跨记录视图），**问题是文档没如实说**——第一轮刚表扬过 TideWatch「消融实验 + 已知限制 7 条」的诚实度。

另一处：`io.py:41-48` 的 `read_jsonl` 用 `print(f"[warn] ...")` 而不是 logging（其余模块都用 logging）。CLI 无害，但 `pyproject.toml` 表明这是可安装的包，作为库被引用时会污染调用方 stdout。

**改法**
① 类注释与 README 改口径 + 给实测量级：「`load()` 流式读取来源，但**结果全量驻留内存**；每条评论约 X KB，10 万条约 Y MB，需同时容纳 10 个信号的视图；真要做流式需把协同类信号改成两遍扫描 + 磁盘中间态，超出当前版本范围。」（X/Y 待实测填入。）② `print` 换 `logging.getLogger("tidewatch.io").warning(...)`，保留「前 5 行行号」的信息量。

**验收**：注释/README 更新含实测量级；新增测试用 `caplog` 捕获 `tidewatch.io` 的 warning 且 stdout 无输出。

---

### D-18 【P2 · 2 小时】Etude `_JOBS` 只增不减；`_POOL` 没有 `shutdown`

**现象+证据**
① `_JOBS` 键为 `lesson:<id>` / `plan:<id>`（pipeline.py:40-45），`_set_job` 用 `setdefault`（:61-65），**全仓无任何删除**（`grep -rn "_JOBS"` 只有 :36、:50-51、:56-57、:62-63 四组访问）。删训练包（db.py:741-746）或计划（db.py:823-836）都不清它。
② `_POOL = ThreadPoolExecutor(max_workers=3, thread_name_prefix="etude-gen")`（api.py:49）**没有任何 `shutdown()` 调用**。Python 3.9+ 的 `ThreadPoolExecutor` 用**非 daemon** 工作线程并在 `atexit` 里 join；`EtudeServer.ask_stop`（server.py:70-98）正文路径只停 uvicorn，**是否等/关 `_POOL` 待确认**。

**为什么是问题**
`_JOBS` 每项很小但**永不释放**，且语义上会出问题：删掉训练包后 `GET /api/lessons/{id}/job`（api.py:356-364）可能返回一个**已不存在训练包的旧进度**。`_POOL` 若不 shutdown，用户在生成排队时点关闭 → `atexit` 等待线程池收工 → 「点了关闭，窗口没了但进程在任务管理器挂几十秒」。

**改法**
```python
# pipeline.py 新增；api.py 的删除端点里调用
def forget_job(key: str) -> None:
    with _JOBS_LOCK: _JOBS.pop(key, None)
# server.py 的停止路径：api._POOL.shutdown(wait=False, cancel_futures=True)（建议包成 api.shutdown_pool()）
```

**验收**：`_set_job` 后 `forget_job` 使 `job_status_of` 返回 `None`；`shutdown_pool()` 后 `_POOL._shutdown` 为 True 且再提交抛 `RuntimeError`。

---

### D-19 【P2 · 半天】Etude `list_cards` 的 `COUNT(*)` + 深 `OFFSET`，`stats()` 6 次独立表扫

**现象+证据**
① 每次翻页跑两遍全量条件（db.py:1169-1194）：`COUNT(*)` 与数据页各执行整段 `WHERE`（含 `LEFT JOIN examples` 与可能的 `LIKE` 搜索，:1163-1166）；深分页 `OFFSET` 是 O(offset)（`limit` 上限 1000，`offset` 无上限，:1193）。
② `stats()` 是 6 条独立 `COUNT(*)`（db.py:588-618），4 条扫 `cards`、1 条扫 `reviews`（还是 D-3 那个 `substr`），首页每次刷新都跑。

**改法**：`stats()` 合成一条条件聚合（D-3 ③ 已给 SQL）；`reviews_today` 换范围条件；翻页改游标分页（`WHERE (c.due_at, c.id) > (?, ?)`），或至少把 `total` 改成「滚动总数」（先返回 `has_more`，总数异步补）；`cards` 状态索引（D-3 ②）顺带加速常见筛选。

**验收**：`stats()` 的 SQL 条数从 6 降到 ≤2；`list_cards(offset=10000)` 的行扫描量不随 offset 线性增长（游标版），若保持 OFFSET 则在 PR 里如实记录该限制。

---

### D-20 【P2 · 2 小时】WingMan `preflight` 读到 `journal_mode` 却不判断；`busy_timeout` 未显式声明

**现象+证据**
```python
# scripts/preflight.py:895-900
conn = sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True, timeout=10.0)
conn.execute("PRAGMA query_only = ON")
data["journal_mode"] = str(conn.execute("PRAGMA journal_mode").fetchone()[0])   # ← 读了、存了
```
全文件 `grep -n "journal|wal|WAL"` 只命中这三行——**从未被判断**。若这个库没能进入 WAL（SQLite 在某些文件系统/网络盘/只读介质上会**静默退回 `delete`**，`PRAGMA journal_mode=WAL` 执行「成功」但返回 `delete`），体检报告里照样是一行数字，**用户不会知道读写已变成互斥、崩溃恢复也更脆弱**。`preflight.py` 在别处做得很好（`query_only=ON` 保证零写入 + sidecar 清理，:884-887、:934-942），只差最后一步判断。

**改法**
```python
# preflight.py 约 :950 之后
mode = str(data.get("journal_mode", "")).lower()
if mode != "wal":
    checks.append(Check("database_journal", "数据库日志模式", "database", STATUS_WARN,
        blocking=False, detail=f"当前是 {mode!r}，不是 WAL。读写会互斥，崩溃恢复也更脆弱。",
        hint="常见原因：数据目录在网盘/同步目录/只读介质上（WAL 需要同目录可写的共享内存）。"
             "把数据目录换到本机磁盘，或检查该目录权限。",
        hint_en=f"journal_mode is {mode!r}, expected 'wal'. WAL needs a local writable dir."))
```
同时把 `busy_timeout` 在三项目显式写出（WingMan 现在靠 store.py:411 的 `timeout=15.0` 隐式生效，Etude 完全没有，db.py:184）——见 D-4。

**验收**：构造 `journal_mode=delete` 夹具库 → 产出 `database_journal` 一条 `warn`，WAL 库产出 `ok`；三项目连接初始化断言含 `busy_timeout`（并入 D-4 验收）。

---

## 3. 跨项目共性清单

按「一次学会、三处受益」归并；⛔ = 与第一轮条目相邻但**角度不同**。

| 编号 | 问题 | 涉及 | 优先级 |
|---|---|---|---|
| **D-1** | 缺备份/全量导出；`EXPORTS_DIR` 定义未实现；「打开数据目录」在 WAL 下诱导用户直拷主文件 | WingMan（Etude 已达标可参照） | **P0** |
| **D-2** | 导入同一文件全量读 3 次；`read_head` 实现与注释相反 | WingMan | **P0** |
| **D-3** | 核心查询用表达式包列使索引失效；状态列缺索引致全表扫 + 临时排序 | Etude | **P0** |
| **D-4** | 只设了 `journal_mode`；`synchronous`/`cache_size`/`temp_store`/`busy_timeout` 未声明 | WingMan / Etude | P1 |
| **D-5** | 检索每次全量载入向量矩阵且无缓存（一次分析载入两遍） | WingMan | P1 |
| **D-6** | 为抽 8~80 行样本把整段会话 `all_messages` 全量读进内存（分析路径每请求一次） | WingMan | P1 |
| **D-7** | `facts.person_id` 缺索引 + `OR` 使部分索引失效 → 每次画像 3 次全表扫 | WingMan | P1 ⛔ |
| **D-8** | 「按名字找人」借道 `list_persons` → 每人 3 条聚合；采集主循环 2 次/会话 ⇒ ≈6·C·P 条 | WingMan | P1 |
| **D-9** | 循环内逐次 `conn()`（`list_chats`/`person_detail`/`_backfill_persons`/`merge_persons`，末者还缺事务） | WingMan | P1 ⛔ |
| **D-10** | 长事务持全局锁 + 批量逐行提交/逐行往返 | Etude | P1 |
| **D-11** | 日志无轮转、每训练包一只增文件、落在数据目录内 | Etude（WingMan 已达标） | P1 |
| **D-12** | 无 `integrity_check`/无孤儿行自检/无 `VACUUM` 回收/无 `ANALYZE`・`optimize` | WingMan / Etude | P1 ⛔ |
| **D-13** | 无保留策略，只增不减（`activity_log`/`engine_runs`/`sim_runs`/`reviews`/`_JOBS`） | WingMan / Etude | P1 |
| **D-14** | `LIKE '%…%'` 不可索引；`index_chat` 每轮从头重扫（O(N²/批)） | WingMan | P2 |
| **D-15** | `readiness()` 逐例句 2 次磁盘 `exists()`，由每次打开详情触发 | Etude | P2 |
| **D-16** | `by_topic/by_actor` 无缓存（单次 run 重建 3 次）；`KeywordSignal` 每命中重建集合 + 线性查权重 | TideWatch | P2 |
| **D-17** | `MappedAdapter.load` 全量驻留与类注释不符；库代码 `print` 非 logging | TideWatch | P2 |
| **D-18** | `_JOBS` 只增不减；`_POOL` 无 `shutdown` | Etude | P2 |
| **D-19** | `list_cards` 的 `COUNT(*)` + 深 `OFFSET`；`stats()` 6 次独立表扫 | Etude | P2 |
| **D-20** | `preflight` 记录 `journal_mode` 却不判断；`busy_timeout` 未显式声明 | WingMan / Etude | P2 |

**本轮确认做对了、别改坏的部分**

- ✅ **WingMan 日志轮转 + 日志与数据分目录**（main.py:49-54、config.py:64-65）—— 三项目唯一做对的，D-11 是照它改 Etude。
- ✅ **Etude 的备份三件套**：`VACUUM INTO`（db.py:254-270）+ 按钮（frontend/index.html:3114）+ README 专章（README.md:303-326）—— D-1 的参照物。
- ✅ **Etude 数据目录可搬迁**：指针文件原子写 + 「指针永不随数据搬走」写进 docstring（paths.py:11-28、104-134）。
- ✅ **WingMan 半自动采集 captures 队列已有 200 条上限**（semi.py:241-244）—— 只增不减类问题里唯一被主动堵住的。
- ✅ **WingMan 库文件改名迁移把 sidecar 一起搬**（store.py:364-394）—— 考虑到了 `-wal`/`-shm`。
- ✅ **WingMan `preflight` 自检零副作用**：`mode=ro` + `query_only=ON` + 只清本次新建的 sidecar（:884-887、:894-897、:934-942）。
- ✅ **TideWatch 规则库只加载一次 + AC 自动机懒构建并缓存**（pipeline.py:55、rules.py:134-141）；`read_jsonl` 是生成器（io.py:19-48）。
- ✅ **WingMan 有单实例保护**（desktop.py:491-504），uvicorn 明确单 worker ⇒ 不存在跨进程写争用。
- ✅ **三项目都没有**未关闭的连接（WingMan `finally: c.close()` store.py:419-420）、没有无界缓存（`lru_cache(maxsize=1)` config.py:169）。

---

## 4. 落地路线（3 周 + 验收标准）

> 按 1 名开发者、每周 2-3 人日估算；每条可独立成 commit。

### 第 1 周 —— 止血（先解决「会丢数据 / 会崩」）

| # | 动作 | 对应 | 验收标准 |
|---|---|---|---|
| W1-1 | WingMan 照抄 Etude：`store.backup_to()` + `POST /api/backup` + 设置页按钮 | D-1 | 备份文件 `integrity_check` = `ok`；备份期间新写入不进入备份 |
| W1-2 | WingMan README/docs 补「数据、备份与恢复」章节 | D-1 | 可检索到「卸载删什么」与「不要直接复制 wingman.db」 |
| W1-3 | WingMan 修 `read_head` 真·部分读；`meta` 复用头部；`_layout_scores` 只扫前 N 行；`parse` 单次读取 | D-2 | 单测断言「一次导入只 1 次全文件读取」；`read_head` 字节数 == 65536 |
| W1-4 | Etude `substr` → 范围条件；`cards` 状态索引 + 排序键落列；`stats()` 合并 | D-3 | `EXPLAIN QUERY PLAN` 无 `SCAN cards/reviews`；`test_upgrade.py` 绿 |
| W1-5 | 三项目补齐 PRAGMA + 启动 `PRAGMA optimize` | D-4 | 新增断言四项 PRAGMA 值的单测 |

### 第 2 周 —— 内存与查询（把「越用越慢」的线拉平）

| # | 动作 | 对应 | 验收标准 |
|---|---|---|---|
| W2-1 | WingMan 向量矩阵缓存 + `stats()` 改 COUNT | D-5 | 同渠道同分析内 `load_embeddings` ≤1 次；`upsert_embeddings` 后失效 |
| W2-2 | WingMan `style_sample` 落 SQL + `summarize_period` 改 `recent_messages(200)` + extract_facts/画像共用一次读取 | D-6 | monkeypatch `all_messages` 抛异常后分析路径不崩 |
| W2-3 | WingMan `facts` 补索引 + `UNION ALL` + `fact_ids_for_person` | D-7 | `EXPLAIN` 无 `SCAN facts`；「两处都出现返回两条」语义测试绿 |
| W2-4 | WingMan `find_person_by_alias` 改单条 SQL；`list_persons` 改 3 条聚合 | D-8 | 200 人夹具下 SQL ≤2 条；采集 SQL 与会话数线性 |
| W2-5 | WingMan `conn()` 改线程本地复用 + `list_chats` 单 SQL + `merge_persons` 包事务 | D-9 | N=100 时 SQL=1、`conn` 调用=1；失败注入后数据完整 |
| W2-6 | Etude `push_cards` 集合式 + `set_cards_srs` 加事务 + `finish_lesson` 卡片 `executemany` | D-10 | 100 张卡只 2 条语句；第 3 张失败时前 2 张未变 |

### 第 3 周 —— 治理与收尾（让「会坏」变成「能看见」）

| # | 动作 | 对应 | 验收标准 |
|---|---|---|---|
| W3-1 | 三项目自检加 `quick_check` + 孤儿行检查（清理前自动备份） | D-12 | 注入 3 条孤儿行 → `warn 3`；清理后 0 且正常行数不变 |
| W3-2 | 加「压缩数据库」（`VACUUM`+`ANALYZE`，前置备份）+ UI 提示 2× 磁盘 | D-12 | 删 10 万行后文件变小；`quick_check` 仍 `ok` |
| W3-3 | 三项目加保留策略（`prune()` / `forget_job`），默认开、可关、显示体积 | D-13 / D-18 | `prune()` 后 `messages`/`facts` 行数不变；幂等 |
| W3-4 | Etude 日志改 `RotatingFileHandler` + 清理；README 标注「logs 不是你的数据」 | D-11 | 写 10 MB 后文件数 ≤4、总量 ≤8 MB |
| W3-5 | WingMan `index_chat` 加游标；`search_text` 改 `instr`（FTS5 立 ROADMAP） | D-14 | 扫描行数随批量线性；结果集与改前一致 |
| W3-6 | Etude `readiness` 改 `scandir`；`list_cards` 深分页方案定稿 | D-15 / D-19 | `stat` ≤2 次；`stats()` SQL ≤2 条 |
| W3-7 | TideWatch `by_topic/by_actor` 缓存 + `RuleBook.weight_of`；`load` 注释如实标注内存；`print`→logging | D-16 / D-17 | 分组重建 1 次；权重查询对照测试一致 |
| W3-8 | WingMan `preflight` 对非 WAL 告警；`busy_timeout` 显式化 | D-20 | `delete` 模式夹具库 → 产出 `warn` |

---

## 5. 待确认项

1. **`PRAGMA synchronous` 的实际当前值** —— 两项目都未显式设置、取编译期默认，本机未运行程序**无法确认**。请实测：`python -c "import sqlite3;print(sqlite3.connect(':memory:').execute('PRAGMA synchronous').fetchone())"`（`cache_size`/`temp_store` 同理）。
2. **D-7 的「全表扫」是推断** —— 依据是 SQLite 部分索引的匹配规则与 `OR` 的优化行为，**未跑 `EXPLAIN QUERY PLAN` 实证**。可执行 `EXPLAIN QUERY PLAN SELECT * FROM facts WHERE ((person_id IS NOT NULL AND person_id<>'' AND (chat_id IS NULL OR chat_id='')) AND person_id=?) OR chat_id IN (SELECT id FROM chats WHERE person_id=?)`。
3. **各表实际行数量级** —— 本报告所有「N 万行」「几百个会话」均为**估算**，依据是代码里的写入路径与 `LIMIT` 常量（如 `index_chat(max_items=20000)` retriever.py:90、`person_messages` 上限 2000 store.py:1101）。真实行数需 `SELECT COUNT(*)` 确认，会直接决定 D-5/D-6/D-8 优先级是否上调。
4. **Etude 关窗是否会被 `_POOL` 的 non-daemon 线程拖住**（D-18）—— 需逐行读 `server.py:70-98` 与桌面入口的退出序列（本轮未完成）。
5. **Etude `busy_timeout` 缺失的实际影响面** —— 若确认用户从不用外部工具打开 `etude.sqlite3`，D-4 中该项可降为 P2。
6. **WingMan `_backfill_persons` 在真实老库上的会话数** —— 决定 D-9 ③ 是否提到 P0（若存在几百个无归属会话的历史库，首次升级的卡顿会很直观）。
7. **TideWatch 内存量级的具体数字**（D-17）—— 需在本地对 `data/sample/sample.jsonl`（81266 B）与 `data/eval/synthetic_labeled.jsonl`（90981 B）量测后填进注释。
8. **Etude `backups/` 是否有清理策略** —— `backups_dir()`（paths.py:176-179）下未读到保留逻辑，可能无限增长（本轮未展开为独立条目）。

---

## 6. 与第一轮报告的关系

**未再提的第一轮条目**（刻意避开，非遗漏）：`conn()` 未开 `PRAGMA foreign_keys`（3.1 / 头号 P0）、`list_chats` 的 1+3N（W-3）、`async def` 内同步调 store（W-6）、无 schema 迁移机制（C-5）、TideWatch `CoOccurrenceSignal` O(A²)、密钥与业务数据同在 `kv` 表（C-9）、明文落盘。

| 本轮 | 相关第一轮条目 | 关系（为什么不是重复） |
|---|---|---|
| **D-9**（循环内逐次 `conn()`） | **W-3**「`list_chats` 是 1+3N 次查询」 | 第一轮量**查询条数**，本轮量**连接与提交次数**。WAL 下每次 `conn()` 退出都 `commit()`（store.py:415）= 一次写事务——即使把 3N 条合成 1 条，只要还在循环里 `with self.conn()`，就仍有 N 次开库句柄 + N 次 fsync 级提交。改法因此要**同时**覆盖两者。本轮另补两处 W-3 未提的同类位置（`person_detail` :1070、`_backfill_persons` :535）与一个**正确性**问题（`merge_persons` 无事务 :1028-1031）。 |
| **D-7**（`facts` 索引 + `OR`） | **3.1** 同一张表（`facts` 曾因唯一键错误导致事实静默覆盖，store.py:45-56） | 第一轮讲**写入端约束**（唯一键应带 `value`），本轮讲**读取端索引**（`person_id` 无独立索引 + `OR` 让已有部分唯一索引也用不上）。同一链路，病灶不同。 |
| **D-12**（完整性体检/孤儿行/VACUUM） | **3.1**（级联失效静默留孤儿行） | 第一轮修**增量**（改 `conn()` 后不再产生新孤儿），本轮补**存量与可观测性**（老库里的孤儿怎么发现与清理、库文件是否完好、删行后空间怎么回收）。第一轮验收是「删除会话后无孤儿」，本轮是「**老库**里的孤儿能被查出并清理」。 |
| **D-9 ③**（`_backfill_persons` 启动路径） | **C-5**「无 schema 迁移机制」 | C-5 解决「老库怎么升到新结构」；本轮指出**已存在的那个迁移函数的执行成本**（for 循环里逐会话「开连接→写→提交」，M 个无归属会话 = M 次完整往返 + M 次持锁）。建议两条**一起改**（引入有序迁移列表时顺手把回填改成一次事务）。 |
| **D-6 / D-14** | **W-3 / W-6**（跨层的查询与阻塞） | W-6 讲「异步函数里同步调 store 阻塞事件循环」；本轮讲**被调用的那个 store 方法本身**读了远超所需的数据（`all_messages` 全量 vs 8 行样本）。即使把调用挪进线程池（W-6 的修法），内存与 I/O 的浪费依旧在。 |
| **D-10**（Etude 长事务 + 逐行提交） | **E-3**「`_provide_both` 每张图新建线程池导致**成本**泄漏」 | 第一轮是**钱**（败者线程仍烧额度），本轮是**锁与内存**（长事务持全局锁 → 前台卡；逐行提交 → 事务风暴）。同在「并发/资源」大类，病灶不同。 |
| **D-1**（备份） | **C-9**「密钥与业务数据同在 kv 表」 | C-9 诉求是**缩小/分离**这个库（把密钥拿出去），本轮诉求是**把库安全交还用户**。两件事都在处理「这个文件是什么」，一个讲分离、一个讲交还。**建议 C-9 先做**（做完后备份里不再含密钥），但 D-1 **不要等** C-9。 |
| **D-4**（`synchronous` 等参数） | **3.1**（`PRAGMA` 只设了一半） | 第一轮点 `foreign_keys`（正确性），本轮点 `synchronous`/`cache_size`/`temp_store`/`busy_timeout`（性能与耐久性配方）。两者都是「在 `conn()`/`connect()` 里补 PRAGMA」同一个动作，**建议合并成一次改动**，避免两次触碰同一段代码。 |

**第一轮未覆盖、本轮为空白领域的部分**

- **备份、导出、卸载与数据所有权**（D-1、D-12、D-13）—— 第一轮完全未涉及数据层，这三条是纯增量。
- **索引审计**（D-3、D-7、D-8、D-14、D-19）—— 第一轮只提 `list_chats` 的查询次数，没有把 schema 索引与代码里的 `WHERE/ORDER BY` 做过对照。
- **局部热点的量化**（D-2、D-5、D-6）—— 第一轮的性能结论只有「`list_chats` 1+3N」与「TideWatch O(A²)」；本轮补上另三处同量级甚至更大的：向量矩阵重复全量载入、`all_messages` 全量取样、导入重复全量读文件。
- **只增不减的表与日志**（D-11、D-13、D-18）—— 第一轮没有任何「长期运行会怎样」的评估。

**口径一致性**：沿用第一轮的方法声明（静态阅读、行号取证、未运行程序），性能量级明确标为**估算**并把推导依据写在条内。第一轮标注为「待确认」的事项，本轮不改变其状态。
