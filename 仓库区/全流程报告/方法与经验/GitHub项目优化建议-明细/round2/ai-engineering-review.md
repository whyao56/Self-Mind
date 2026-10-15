---
tags: [领域/方法, 类型/报告, 轮次/第二轮]
评审日期: 2026-10-13
评审对象: github.com/whyao56 · WingMan / Etude / TideWatch
评审维度: AI/LLM 工程化与成本
评审员: ai-eng（AI/LLM 工程化与成本评审员）
方法: 本地浅克隆静态阅读（未执行、未安装依赖、未真实调用任何 LLM API）
---

# 第二轮评审 · AI/LLM 工程化与成本

> **本轮定位**：第一轮覆盖了【代码架构 / 测试与 CI / 开源呈现与隐私】。AI 是这三个项目真正的业务内核，却几乎没被评审过。本轮只写**第一轮未覆盖的新条目**；与第一轮相关但角度不同的，逐条标注「与第一轮 X 条的关系」。
>
> **口径**：所有行号均为实际读到的代码位置。凡涉及外部定价数字，均已标注查询日期与出处，未查出的一律写「待确认」，绝不编造。
>
> **一句话前提**：WingMan 与 Etude 是"把 LLM 当产品内核"的项目，TideWatch **不调用任何 LLM**（`grep -riE "llm|openai|prompt|chat_completion" TideWatch/src TideWatch/eval` 零命中）——它是一个规则/信号引擎。因此 TideWatch 在本轮的角色是**正面样板**（它有唯一一套真正的离线评测），而不是被批评对象。

---

## 0. 一页结论（最该做的 3 件事）

**一句话**：这三个项目把 LLM"接进来了、兜底写得比多数人认真"，但**没有把 LLM 当被测、被计量、被版本管理的工程对象**——提示词改了很多轮却没有版本号，一条链路上花了多少 token 完全不知道，模型返回"长得像但字段全错"时会静默补默认值。真正稀缺的不是代码能力，**AI 工程化的"可度量性"**。

| 优先级 | 事项 | 一句话理由 | 主要涉及 |
|---|---|---|---|
| 🔴 P0 | **给提示词加版本号 + 建最小 golden set 回归** | CHANGELOG 里已有多次提示词重写，但没有任何机制能证明"改完没变差" | WingMan / Etude |
| 🟠 P0 | **加 token 计量与成本护栏 + 一次点击的成本上限** | 全仓库零 token 计数、零成本估算；Etude 一次"生成计划"可触发 21 次 chat + 最多 160 次 TTS + 160 次生图 | WingMan / Etude |
| 🟡 P1 | **结构化输出"静默降级"要可见 + Mock 降级要附着在结果上** | 模型返回可解析但字段全错时，`coerce` 会静默补默认值，用户看到一份"太平无事"的假分析 | WingMan |

**最容易被忽略、但性价比最高的一件事**：两个项目**都已经**有离线 OpenAI stub（`WingMan/scripts/openai_stub.py`、`Etude/scripts/openai_stub.py`），却**都没有接进 CI**。把"成本护栏 + golden set 回归"挂在这套已有的 stub 上，是这条路线里投入产出比最高的一步（见 §4）。

---

## 1. 现状矩阵（三项目 × AI 工程化维度）

| 维度 | WingMan | Etude | TideWatch |
|---|---|---|---|
| **1. 提示词资产化** | 集中在 `engine/prompts.py`（500 行），`[TASK:XXX]` 首行充当伪 ID；**无版本号、无回滚** | 集中在 `prompts.py`（433 行），**无版本号**；生图提示词另硬编码在 `providers/images.py` | 无提示词 |
| **2. 结构化输出健壮性** | `parse_json_loose()` 容错解析（去围栏/配平/修尾逗号）；`coerce()` 手工补默认值；**解析器零测试** | `extract_json()` 三层兜底 + `test_guards.py` 有真实形状用例；`normalize()` 手工收敛 | 不适用 |
| **3. 成本与额度控制** | ❌ 无 token 计数 / 无成本估算 / ❌ 无结果缓存 / ❌ 无模型路由（单一 `llm_model` 跑全部 8 类任务） | ❌ 无 token 计数（`chat()` 丢弃 `usage`）/ ❌ 无文本结果缓存（图/音有内容寻址缓存）/ ❌ 无模型路由 | 无 LLM |
| **4. 离线评测与回归** | ❌ 无评测集；CI 用 Mock 跑冒烟 | ❌ 无评测集；有 `openai_stub.py` 但未进 CI | ✅ `eval/run_eval.py` + 消融实验 + **CI 断言不退化** |
| **5. Mock/降级链风险** | 默认 `mock`；自检面板报 `warn`；**结果 payload 不带"这是假结果"标记** | 无 Mock 概念，默认 deepseek（空 key 直接报错）——**不会静默造假** | 不适用 |
| **6. embedding 与检索质量** | 三路混合（语义/关键词/新鲜度）；**暴力线性 `mat@qv`**；无切块、无 rerank、无检索评测 | 不适用 | 不适用 |
| **7. 数据飞轮** | ❌ 不记录"用户选了哪条回复 / 发出去后结果如何" | ❌ 评分/手工修正/新增例句全部只落本地，无回流 | 不适用 |

---

## 2. 逐条发现（按 P0 → P2 排序）

> 每条六要素：【现象+证据】【为什么是问题】【改法】【优先级】【工作量】【验收标准】

### A-1【P0】提示词改了很多轮，却没有版本号，也没有 golden set 能证明"改完没变差"

**【现象+证据】**
- WingMan 全部提示词集中在 `WingMan/backend/app/engine/prompts.py`（1–500 行）。每个 system prompt 首行是 `[TASK:XXX]`（`prompts.py:33-34` 的 `_sys()` 工厂），但这个标记的用途被注释明确写成"Mock 分派 / 日志追踪 / **后期做** prompt 版本管理"（`prompts.py:5-6`）——也就是说，**版本管理是"计划中的事"，现在没做**。
- Etude 同理：`Etude/backend/app/prompts.py:22-54`（`SYSTEM`）、`prompts.py:267-301`（`SYLLABUS_SYSTEM`），同样无版本号。
- **提示词确实在频繁迭代**，证据在 CHANGELOG：`Etude/CHANGELOG.md:84` 记录"文生图提示词重写成四段"；`Etude/CHANGELOG.md:208` 记录"提示词里写死了一句……"; `WingMan/CHANGELOG.md:9` 直接写"目前最大的缺口是 **Prompt 调优**"。
- Etude 自己承认没有质量校验：`Etude/CHANGELOG.md:422`——"例句质量取决于所配模型，**程序不做质量校验**。"

**【为什么是问题】**
提示词是这三个项目**唯一真正的"产品逻辑"**，但它比代码更脆弱：改一个形容词就可能让模型全局换风格，而这种回归**不会让任何测试变红**。现在改提示词的流程是"改字符串 → 手动跑一次看感觉 → 提交"，产出物里**没有任何东西记录"这次结果由哪一版提示词产生"**。因此：
1. 无法归因——同一个聊天包，两周前效果好、今天变差，你无法判断是提示词改了、还是模型侧升级了；
2. 无法回滚——想退回上一版，只能翻 git diff 逐行比对字符串；
3. 无法度量——CHANGELOG 说"重写了"，但"重写后准确率从 X 到 Y"永远说不出来，简历上这句话经不起追问（这一点 TideWatch 做得完全相反，见 A-12）。

**【改法】**
第一步（半天，零依赖）：给每个提示词一个**显式版本常量**，并把它写进调用与留存里。

```python
# Etude/backend/app/prompts.py —— 在文件顶部集中声明
PROMPT_VERSION = "2026-10-13.a"          # 只改字符串就顺带 bump 它

SYSTEM_SHA = __import__("hashlib").sha256(SYSTEM.encode("utf-8")).hexdigest()[:8]
# 更省事的机器版：只在启动时算一次全文件指纹，改任何提示词都会变
```

```python
# Etude/backend/app/pipeline.py —— 在 llm.chat 调用点旁边记进 job/lesson
_set_job(key, step="正在等模型返回例句",
         prompt_version=prompts.PROMPT_VERSION)   # 新增字段
```

```python
# WingMan：把 [TASK:XXX] 升级成带版本的标记，零侵入
def _sys(task: str, body: str, version: str = PROMPT_VERSION) -> str:
    return f"[TASK:{task}@{version}]\n{body}\n\n{RED_LINE}"
# task_tag() 用 r"\[TASK:([A-Z_]+)" 匹配，前缀不变，Mock 分派不受影响（llm/base.py:108-111）
```

第二步（1–2 天）：建**最小 golden set**，格式见 §4 的 `golden/cases.jsonl`，断言是**结构级 + 关键词级**（不比对逐字文本，否则模型一升级就全红）。

**【优先级】** P0
**【工作量】** 版本化 0.5 天；golden set 骨架 1 天
**【验收标准】** `git grep "PROMPT_VERSION"` 命中声明与消费点；每次 `lesson`/`run` 的留存记录里能看到 `prompt_version`；新增 `tests/test_prompt_golden.py` 能对 ≥8 条 golden case 跑结构断言且不联网。

---

### A-2【P0】全链路零 token 计量、零成本估算——"每月花了多少"没人知道

**【现象+证据】**
- WingMan 的 OpenAI 兼容 provider 拿到了 `usage` 却只用 `log.debug` 打了一行就丢弃：`WingMan/backend/app/llm/openai_compat.py:152-155`

  ```python
  usage = data.get("usage") or {}
  if usage:
      log.debug("usage=%s", usage)     # ← 只进调试日志，不返回、不累计
  return str(content or "")
  ```
- Etude 更彻底：`Etude/backend/app/providers/llm.py:348-349` —— `data = resp.json()` 之后直接 `return _content_of(data)`，**连 debug 都没有**。
- 全仓 `grep -rniE "token_count|tiktoken|cost|pricing" WingMan/backend/app Etude/backend/app` 零命中（唯一的 `budget` 命中是 `collect/keys.py` 的**扫描超时**预算，与 LLM 无关）。`grep -rn "usage"` 只有上面那一处。
- 界面层也不显示：WingMan 结果头只显示 `trace.llm`（provider 名）与各步耗时（`frontend/index.html:2457`），没有 token / 费用。

**【为什么是问题】**
这是一个**本地优先、用户自付 API 费**的产品。用户最常问的问题不是"准不准"，而是"我这么用一个月要花多少钱"。现在这个数字**整个项目里无法回答**——不是没做界面，是底层连一次调用的 token 数都没留。连带后果：无法做成本回归（改了提示词之后单次成本是否暴涨）、无法设额度护栏、无法定位"哪个任务最贵"。

**【改法】**
最小实现：让 provider 把 usage 带出来，在 pipeline 层累加，写进已有的 `trace` 与 `job` 结构（两边都已有现成的留存通道，不用新建表）。

```python
# WingMan/backend/app/llm/base.py —— 增加一个可选返回 usage 的口子
@dataclass
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
```

```python
# pipeline.py:89 附近，把用量并进已有的 trace
trace["llm"] = getattr(ctx.llm, "name", "unknown")
trace["tokens"] = {"prompt": ctx.usage.prompt, "completion": ctx.usage.completion}
```

```python
# Etude/backend/app/providers/llm.py:348 —— 顺手把 usage 交给调用方
return _content_of(data), (data.get("usage") or {})
```

```python
# Etude/backend/app/config.py —— 加一行单价，界面直接算钱
"llm": {
    "price_in_per_mtok": 0.0,    # 用户自己填，程序不预设厂商价格
    "price_out_per_mtok": 0.0,
}
```

**【优先级】** P0
**【工作量】** 采集 1 天；界面显示 0.5 天
**【验收标准】** 单次"分析并给建议"的留存记录里出现 `tokens.prompt/completion`；Etude 设置页显示"本次预计/累计花费"；新增用例用 stub 返回固定 `usage`，断言累加值正确。

---

### A-3【P0】没有 LLM 结果缓存，也没有模型路由——贵模型被用在最轻的活上

**【现象+证据】**
- **无结果缓存**：WingMan 的 `run_analysis`（`engine/pipeline.py:46-119`）每次都重新调 3 次 `complete_json`（`analyzer.py:61`、`planner.py:58`、`suggestor.py:234`），对**完全相同的输入**（同一句 peer_message + 同一份上下文）不会复用上次结果。Etude 也只在"同目标正在 generating"时才复用（`api.py:323-329`），一旦生成完成，再次点同一个词仍会重新调模型（`api.py:331-334`）。
- 对照：Etude 的**图片和音频**是内容寻址缓存的（`providers/images.py:262-276`、`providers/tts.py:49`），说明作者知道怎么做缓存——只是**没把同一招用到最贵的文本 LLM 上**。
- **无模型路由**：WingMan 只有单一的 `llm_model` 配置（`WingMan/backend/app/config.py:142`），`build_llm` 把它灌给唯一一个 provider（`llm/factory.py:32-47`）。于是**8 类任务共用一个模型**：

  | 调用点 | 任务 | 温度 | 相对成本 |
  |---|---|---|---|
  | `analyzer.py:61` | ANALYZE：解读一句话 | 0.4 | 低 |
  | `planner.py:58` | STRATEGY：定本轮策略 | 0.4 | 低 |
  | `suggestor.py:234` | SUGGEST：生成 4 条候选回复 | 0.9 | **高**（输出长） |
  | `simulator.py:91` | SIMULATE：推演 3 个分支 × 2–3 轮对话 | 0.85 | **最高** |
  | `memory/profiler.py:71` | FACTS：抽取事实，**分批最多 10 次** | 0.2 | 中（调用次数多） |
  | `memory/profiler.py:145/263` | PROFILE / PERSON_PROFILE | 0.4 | 中 |
  | `memory/profiler.py:328` | SUMMARY | 0.4 | 低 |

  最"重"的 SUGGEST/SIMULATE 与最"轻"的 SUMMARY/FACTS 走同一个模型、同一个价格。

**【为什么是问题】**
两件事叠加：**重复付费**（同一输入反复调用）+ **错配付费**（简单任务用贵模型）。这不是理论风险——`extract_facts` 对 600 行记录切 60 行/批（`profiler.py:23-24,66-76`）就是**最多 10 次串行调用**，而 `build_person_profile` 又对**每个渠道**各跑一次 `extract_facts`（`profiler.py:216-225`），一个有 3 个渠道的对象一次"让 AI 整理"就是 30+ 次调用。

**【改法】**
1. 缓存：对 `(prompt_version, model, temperature, 输入哈希)` 做键，落 SQLite 表 `llm_cache`；只缓存**确定性任务**（FACTS / PROFILE / SUMMARY，temp ≤ 0.4），**不缓存** SUGGEST/SIMULATE（temp 高，用户期望每次不同）。
2. 路由：配置里加 `llm_model_cheap` / `llm_model_strong`，按任务类别选。

```python
# WingMan/backend/app/engine/pipeline.py —— 任务级模型选择
_LIGHT = {"FACTS", "SUMMARY", "STRATEGY"}
model = ctx.cfg("llm_model_cheap") if task_tag(system) in _LIGHT else None
```

**【优先级】** P0（缓存）/ P1（路由）
**【工作量】** 缓存 1 天；路由 0.5 天
**【验收标准】** 相同输入连续调两次，第二次命中缓存、不再发起 HTTP（用 stub 计数断言）；`grep` 确认 FACTS/SUMMARY 走 cheap 模型。

---

### A-4【P1】Etude 一次点击的最坏成本没有护栏——"生成计划"可触发 21 次 chat + 最多 160 次 TTS + 160 次生图

**【现象+证据】**
- 默认一份计划 20 个条目：`Etude/backend/app/config.py:77`（`plan_default_count: 20`）、每包 8 条例句（`config.py:69`）、每包最多 8 张图（`config.py:58`）。
- `POST /api/plans/{id}/start`（`api.py:509-520`）**只需一次调用**就触发 `generate_plan`，无成本提示、无二次确认，只有"是否正在跑"的状态守卫（`api.py:516-517`）。
- `generate_plan` 串行地对每个条目调 `generate()`（`pipeline.py:438-451`），每个 `generate()` = **1 次 chat**（`pipeline.py:194-202`）+ 最多 8 次 TTS（`pipeline.py:259-265`）+ 最多 8 次配图（`pipeline.py:295-316`）。
- 配图默认来源是 `both`（`config.py:56`）——即"检索与画图并行"。按 `images.py:678-724` 的实现，**画图那一路会被真的发起**（`_provide_both` 同时 submit 两路，`images.py:708-711`），即便检索通常先返回（`images.py:685-691` 的注释明确说"多数情况是检索胜出"）。

**最坏一次点击（20 条计划）**：21 次 chat 调用 + 160 次 TTS + **160 次付费生图**。

**【为什么是问题】**
这是"用户看不见但一次就在付"的成本。第一轮已指出 `_provide_both` 的线程泄漏会烧钱（见 3.2 / E-3）——**本条目是它未覆盖的"总量面"**：即使把泄漏修好，"默认 both + 默认 20 包 + 无确认"这个**组合**本身就会让一次点击把额度打满。用户点下去之前，界面上没有"这次大约要花 X"的任何提示。

**【改法】**
1. 前端在"开始生成"按钮旁显示预算估算：`条数 ×（1 次文本 + 8 次语音 + 8 次生图）`，图片非 off 时给出"按张计费"的显式警告。
2. 默认把 `images.source` 从 `both` 改为 `search`（免费），把 `both` 降为"用户明确知道要花钱时才开"的选项。
3. 后端加软护栏：`plan` 启动前若 `count × max_per_lesson` 超过阈值，要求 `confirm=true` 参数。

```python
# api.py:509 附近
if plan_cost_estimate(plan) > cfg["llm"].get("max_cost_per_plan", 0) and not payload.confirm:
    raise HTTPException(409, detail=f"本次预计发起 {n} 次生成，请确认后重试。")
```

**【优先级】** P1
**【工作量】** 1 天
**【验收标准】** 界面在开启生图时显示预估张数；`POST /start` 在超阈值且未确认时返回 409；新增用例断言默认 `images.source != "both"` 或断言护栏生效。

---

### A-5【P1】结构化输出"静默补默认值"——模型返回"长得像 JSON 但字段全错"时，用户看到一份假分析

**【现象+证据】**
- WingMan 的 `parse_json_loose()` 对**顶层是数组**的情况会包一层：`llm/base.py:94-95`

  ```python
  if isinstance(data, list):
      return {"items": data}     # 顶层数组被包成 {"items": [...]}
  ```
- 而 `analyzer.coerce()` 只认 `emotion` / `intent` / `subtext` / `topics` … 这些顶层键（`engine/analyzer.py:35-47`）。当模型返回顶层数组（`{"items":[...]}`）时，`data.get("emotion")` 全是 `None`：

  ```python
  emotion=str(data.get("emotion") or "平静")[:20],           # → "平静"
  emotion_intensity=_int(data.get("emotion_intensity"), 5, 0, 10),  # → 5
  subtext=str(data.get("subtext") or "")[:500],              # → ""
  ```
- 结果：`coerce` **不抛异常、不告警**，返回一个字段全为默认值的 `PeerAnalysis`。`analyzer.analyze()` 里只有 `log.debug`（`analyzer.py:66`），没有 warning 回传。
- 对比 `suggestor.suggest()` 是有告警意识的：选项为空或不足 3 条时会 append warning（`suggestor.py:256-259`）——**analyzer/planner 没有这道防线**。

**【为什么是问题】**
这正中项目自己反复强调的雷区。`Etude/backend/app/images.py:286-289` 的注释写得很清楚："不报错，但结果不对……是安静地产生一个残缺的训练包"——Etude 为图片做了防线，**WingMan 的分析链路却没有**。用户会看到"情绪：平静（5/10）、潜台词：（空）"这种**看似正常实则全空**的分析，并据此做真实决策。更糟的是，`warnings` 数组明明存在（`SuggestionBundle.warnings`，`pipeline.py:117`），却只装了检索层的告警。

**【改法】**
在 `coerce` 里做**关键字段存在性校验**，缺失即回传 warning（不改异常流程，只让问题可见）：

```python
# engine/analyzer.py
REQUIRED = ("emotion", "intent", "subtext")
missing = [k for k in REQUIRED if not str(data.get(k) or "").strip()]
if missing:
    # 返回 (分析结果, warnings)，让 pipeline 合并进 bundle.warnings
    ...
```

配套：加一个**可选**的轻量 jsonschema/pydantic 校验（不入主流程，只在 `WINGMAN_STRICT_JSON=1` 时开启），用于本地调提示词时立刻暴露结构漂移。

**【优先级】** P1
**【工作量】** 0.5 天
**【验收标准】** 新增用例：`parse_json_loose('[{"a":1}]')` → `coerce` 后 `warnings` 非空；前端结果显示"本次模型输出结构异常"提示。

---

### A-6【P1】Mock 降级链：自检面板报了，但**结果 payload 不带"这是假结果"标记**

**【现象+证据】**
- 默认 provider 是 `mock`：`WingMan/backend/app/config.py:139`、`llm/factory.py:21`；`.env.example` 顶部写明"留空即使用内置 Mock Provider"。
- **部分配置错误会静默退回 Mock**：`factory.py:36-39`

  ```python
  if not base_url or not model:
      log.warning("llm_provider=%s 但 base_url/model 未配置完整，已退化为 Mock。", kind)
      return MockProvider()      # ← 用户点"分析"照样返回 200
  ```
- 自检**确实**会把 mock 报成 `warn`：`WingMan/backend/app/selfcheck.py:193-201`，文案也很重（"**不能当真实建议用**"）；前端据此在引导卡上显示"现在跑的是演示模式"（`frontend/index.html:3780-3783`）。
- **但**：`llmOk` 只用来控制引导卡是否隐藏（`index.html:3768`）。分析结果本身**不含**"这是 Mock 结果"的信号——`SuggestionBundle` 里没有该字段，`warnings` 里也没有；唯一的线索是结果头那行 `trace.llm`（`index.html:2457`），混在"耗时 XXms（检索… · 分析… · 建议…）· **mock** · 召回 N 条"里，且**只在用户没配 key 时**才等于 `mock`——一旦用户配了 key、但 base_url 或 model 漏填，`selfcheck` 会**同步地**再报一次 warn，可结果仍会照常返回。

**【为什么是问题】**
第一轮把"`.env.example` 写得规范"列进了优势清单（全流程报告 §8）。本条从其**反面**补充风险：Mock 的兜底设计是正确的（产品不该起不来），风险在于**兜底结果与真实结果的区分只发生在"启动自检"这一刻，而不是发生在"每一次结果"上**。用户截一张图发出去、或隔了几天忘了自己没配 key，界面不会在结果里提醒他"这条是模板套的"。而且自检是 `warn` 不是 `fail`，`SuggestionBundle.warnings` 这条**已有的**可见通道被浪费了。

**【改法】**（最小改动，顺着已有通道走）
```python
# engine/pipeline.py:117 附近 —— Mock 结果必须自带可见标记
if getattr(ctx.llm, "name", "") == "mock":
    warnings = warnings + ["⚠️ 本次结果由内置演示引擎（Mock）生成，是规则套模板，不可作为真实建议使用。"]
```

并在 `SuggestionBundle` 加一个 `engine: "mock" | "real"` 字段，前端在结果卡片顶部常驻一个徽标（而非只在引导卡出现）。

**【优先级】** P1
**【工作量】** 0.5 天
**【验收标准】** 在 mock 模式下调用 `/suggest`，响应 `warnings` 含演示引擎提示且 `engine=="mock"`；真实 provider 下该字段为 `"real"` 且无该 warning。

---

### A-7【P1】WingMan 检索：暴力线性扫描 + 无切块 + 无 rerank + 零评测

**【现象+证据】**
- **暴力线性召回**：`memory/retriever.py:133` 取全部向量，`retriever.py:140` 直接 `mat @ qv` 算余弦。
- **每次检索把整个矩阵从 SQLite 读出并解码**：`store.py:1446-1466`（`load_embeddings` 里 `np.vstack([_to_np(...)])`）。按 `index_chat` 的上限 20000 条（`retriever.py:90`）× 512 维 × float32 ≈ **40 MB/次**，且在**每次分析**里都重来一遍（`engine/context.py:177-196` 对每个渠道各建一个 `HybridRetriever` 并检索一次）。
- **无切块策略**：一条消息 = 一个向量（`retriever.py:114-117` 的 `_index_text`），长消息不切、短消息不合并、无窗口重叠。
- **有阈值、无 rerank**：`min_score=0.12` 固定阈值（`retriever.py:127`），召回头之后只剩三路加权排序（`retriever.py:178`），没有 cross-encoder 或任何二次精排。
- **无检索质量评测**：全仓 `grep -riE "recall@|mrr|ndcg|retrieval.*eval"` 零命中。
- **默认退化为字面哈希向量**：`build_embedder` 在无云端配置时返回 `HashEmbedder`（`embedder.py:212-239`），其自述是"无语义泛化"（`embedder.py:102`）。这会让"语义召回"那 0.60 权重（`retriever.py:30`）基本失效。
- **上限静默截断**：`index_chat(max_items=20000)` 超出即停（`retriever.py:90-105`），最早的对话永远不会进索引，且没有告警说"这段历史没被索引"。
- 附带：`context.py:201` 为凑 few-shot 风格样本会 `ctx.store.all_messages(cid)` **取全量消息**进内存。
  > **分工口径（避免与 data-perf 重复）**：本条只负责**检索质量面**（零评测 / 无切块 / 无 rerank / 线性复杂度本身）。上述"矩阵全量载入 + 无缓存""`all_messages` 全量取样"两处的**内存与 I/O 成本**已由 data-perf 报告 **D-5 / D-6** 详述（含 `context.py:180` 的 `stats()` 二次载入、3 渠道 ≈ 240 MB 读入量、实例级/AppContext 级缓存与 `stats` 改 COUNT 的改法），本报告不重复展开。

**【为什么是问题】**
"把聊天记录变成可检索记忆"是 WingMan 的立身叙事（README 首屏卖点）。但检索质量**一个字都没被量过**：改权重、改阈值、改 embedder，全凭手感。线性扫描 + 全量加载在"几千条"规模上够用，但这个项目定位是"长期把聊天记录攒起来"，规模一上来就是 O(N) 内存 + O(N) 点积 × 每渠道 × 每次分析——`build_context` 甚至对**每个勾选渠道各来一次**。

**【改法（可测量）】**
1. **可测量的第一件事**：建一个 50–100 条的人工标注 retrieval set（query → 期望命中的 message_id），输出 `recall@5 / recall@10 / MRR`。这是唯一能把"改进"变成"数字上升"的办法。
2. 矩阵缓存：见 data-perf 报告 **D-5**（实例级 + `AppContext` 级缓存、`upsert_embeddings` 失效标记、`stats` 改 COUNT），本报告不重复展开。
3. 索引：`sqlite-vec` 或 `hnswlib` 做 ANN；短期退路是把矩阵常驻为 `np.memmap`，至少不再每次 `_to_np` 反序列化。
4. 切块：长消息按句切 + 相邻 1 句重叠；短消息（<8 字）合并前后各一条。

**【优先级】** P1（评测）/ P1（性能）
**【工作量】** 评测集 1 天；矩阵缓存 0.5 天；切块 1 天；ANN 2 天
**【验收标准】** `eval/retrieval_eval.py` 输出 recall@k 数字；同一会话第二次检索不再触发 `_to_np`（用探针断言）；超出 `max_items` 时产生可见告警。

---

### A-8【P1】WingMan 的容错 JSON 解析器**零测试**——Etude 有，WingMan 没有

**【现象+证据】**
- WingMan 的 `parse_json_loose()`（`llm/base.py:71-105`）与辅助的 `_extract_balanced()`（`base.py:33-58`）、`_repair()`（`base.py:61-68`）承担了全部脏活：去 markdown 围栏、找 `{`/`[` 起点、按括号配平（跳过字符串内括号）、修中文引号、修尾逗号、最后一搏 rfind。
- `grep -rniE "parse_json_loose|LLMFormatError" WingMan/backend/tests` → **只有 1 处命中，且是 `complete_json` 的替身实现**（`tests/test_objects_center.py:807`），**没有一个测试直接喂脏字符串给解析器**。
- 对照 Etude：`tests/test_guards.py:257-278` 有三条真实形状用例（围栏、嵌套括号、纯中文无 JSON）；`tests/test_e2e_stub.py:82,124` 也覆盖了 `extract_json`。
- 更值得注意：WingMan 的 CI **用 Mock 做端到端冒烟**（`WingMan/.github/workflows/ci.yml` 的"端到端冒烟测试（Mock Provider）"步骤）。而 `MockProvider.chat_raw` 永远返回 `json.dumps(...)` 的**干净 JSON**（`llm/mock.py:361-366`）——也就是说，**CI 里的"model output"永远不含围栏、不含截断、不含多余说明文字，解析器最该被验证的分支从来没被走过**。

**【为什么是问题】**
这段代码是"真实模型输出"和"内部结构"之间唯一的闸门，而它的注释自己就说"各家模型在这个问题上可靠程度差别巨大"（`base.py:4-5`）。恰恰这段最脆、最容易写错（`_extract_balanced` 的字符串转义状态机、`_repair` 的正则）的代码，测试覆盖是三个项目里最差的之一。

**【改法】** 直接照抄 Etude 的用例形状，补一组参数化测试。

```python
# WingMan/backend/tests/test_llm_json.py（新增）
@pytest.mark.parametrize("raw,expect_keys", [
    ('```json\n{"emotion":"开心"}\n```', {"emotion"}),           # 围栏
    ('好的，结果是 {"emotion":"累"}\n希望有帮助', {"emotion"}),      # 前后夹带
    ('{"a":"}"}', {"a"}),                                        # 字符串内括号
    ('{"a":1,}', {"a"}),                                         # 尾逗号
    ('[{"emotion":"x"}]', {"items"}),                            # 顶层数组（A-5 触发的形状）
])
def test_parse_json_loose(raw, expect_keys):
    from app.llm.base import parse_json_loose
    assert expect_keys <= set(parse_json_loose(raw).keys())
```

**【优先级】** P1
**【工作量】** 0.5 天
**【验收标准】** `tests/test_llm_json.py` 覆盖围栏/夹带/嵌套括号/尾逗号/顶层数组/空内容≥6 类，全绿；对截断输入断言抛 `LLMFormatError`（而非静默返回半个对象）。

---

### A-9【P2】Etude 承诺"8 条例句"，但 `normalize` 会**安静地接受更少**

**【现象+证据】**
- 请求 8 条：`config.py:69`（`examples_per_lesson: 8`）、`pipeline.py:190-191`。
- 但 `normalize()` 只要求"非空"，不校验条数：`pipeline.py:106-138`，最后 `"examples": examples[: max(want_examples, 1) * 2]`（`pipeline.py:163`）——**上限是 2 倍，没有下限**。模型给 3 条，就落 3 条。
- 真正暴露问题是在 **suggestor** 那一侧：WingMan 会告警"只生成了 N 条（期望 4 条）"（`suggestor.py:258-259`）；Etude 的 `normalize` **没有等价告警**。

**【为什么是问题】**
理论要求是"多例子的重复"（`Etude/backend/app/prompts.py:29-30` 明确写"meeting many DIFFERENT examples"）。当模型只给 3 条时，训练包**看起来是成功的**（`status=done`），用户不会知道这次素材量只有承诺的 37%。这与项目自己"不报错但结果不对最忌讳"的立场直接冲突。

**【改法】** 在 `normalize` 里比较 `len(examples)` 与 `want_examples`，不足时：(a) 记一条 `warnings`；(b) 可选地再发一次"补齐 K 条"的追问（一次，不递归）。

**【优先级】** P2
**【工作量】** 0.5 天
**【验收标准】** stub 返回 3 条时，`lesson` 详情页可见"本次只生成 3/8 条"提示；新增用例断言该提示存在。

---

### A-10【P2】数据飞轮缺口：用户的修正与选择全部只落在本地，从不回流

**【现象+证据】**
- **Etude 有丰富的"用户修正"数据，但没有回路**：
  - 逐次评分落库：`db.py:920-956`（`grade_card` 写 `cards.last_grade` 并 `INSERT INTO reviews`，含 `grade / seconds / prev_state`）。
  - 但 `reviews` 表只被用于"今天练了多少张"的计数（`db.py:611-613`、`db.py:869`）和 undo（`db.py:985`、`db.py:1024`）——**没有一处把它当质量信号**。
  - 用户能改 AI 生成的例句（`PATCH /api/examples/{id}`，`api.py:732-737`）、能删（`api.py:745`）、能自己加（`api.py:753`）——这些"人工纠正"是最珍贵的标注，但只写在本地库，无导出、无聚合、无回流。
- **WingMan 连"用户选了哪条"都没记**：`store.save_run`（`pipeline.py:99-107`）保存了分析/策略/4 条候选，但没有任何字段记录"用户实际用了 A 还是 B"；`save_sim_run`（`simulator.py:111-114`）同理。全仓 `grep -rniE "chosen|selected|feedback|采纳"` 在 app 层零命中。
  - Etude 的 `config.py` 里甚至没有一个"反馈"相关的开关。

**【为什么是问题】**
这是**产品护城河**层面的缺口，而不是工程缺陷。WingMan 的核心问题"哪条建议真的有用"、Etude 的核心问题"哪条例句让人卡住"，**只有用户能给答案**——而这些答案现在每天都在产生（用户选了某条回复、用户改了某条例句、用户在某个例句上反复失败），却**全部被丢掉**。没有这个回路，提示词调优只能靠作者的主观感觉（回到 A-1），模型也无法做任何个性化。TideWatch 恰恰相反：它有标注数据、有指标、有消融——**同一个账号下的三种工程成熟度**。

**【改法（先记录，后利用）】**
1. WingMan：在 `runs` / `sim_runs` 上加 `chosen_option_id` 与可选 `outcome`（"用了/没用/对方反应"），前端在候选卡片上给一个"我用这条"按钮。零成本，先攒数据。
2. Etude：加 `POST /api/feedback/export`，把"被手工修改/删除的例句 + 反复 grade=1 的卡片"导出成**匿名化**的 JSONL，作为 A-1 的 golden set 候选来源（正好复用现成的修正数据）。
3. 注意隐私：WingMan 导出的是聊天内容，**默认不导出**，只在用户显式点击时、且带脱敏（复用 `test_privacy_pseudonyms.py` 已有的姓名/邮箱规则）。

**【优先级】** P2（记录）/ P1（Etude 反馈导出，因为它直接服务于 A-1）
**【工作量】** 记录 0.5 天；导出 1 天
**【验收标准】** WingMan 选中某条候选后，该 run 记录里出现 `chosen_option_id`；Etude 导出文件不含 api_key/绝对路径，且带 `prompt_version` 字段。

---

### A-11【P2】提示词资产**分散**：生图提示词硬编码在 provider 里，Mock 又复制了 prompt 的尾部指令

**【现象+证据】**
- Etude 的"例句生成"提示词在 `prompts.py`，但**文生图提示词**在另一个文件、以函数返回字符串的形式硬编码：`providers/images.py:143-181`（`build_prompt`），并且它同样在 CHANGELOG 里被"重写过"（`Etude/CHANGELOG.md:84`）。改它要动 provider 代码，且版本管理（A-1）覆盖不到。
- WingMan 的 `MockProvider` **复制了一份提示词尾部指令**：`llm/mock.py:58-65` 硬编码了 `"请分析这条消息。"` / `"请给出 4 条候选回复。"` 等 6 行，这些字符串**原文来自 `engine/prompts.py`**（如 `prompts.py:274,416,490`）。一旦有人改了 `prompts.py` 里的指令句而忘了同步 `mock.py`，Mock 就会把指令当成对方的话（`mock.py:42-57` 的注释正是在描述这个已发生过的 bug）。

**【为什么是问题】**
提示词被当成"代码里的字符串"而不是"资产"，所以它散落在多个文件、被跨文件复制。A-1 的版本化如果只覆盖 `prompts.py`，就会漏掉 images.py 和 mock.py 里的两份。

**【改法】** 把"提示词"统一到一个可枚举的注册表（哪怕仍是 Python 常量），让版本指纹覆盖**全部** file：`prompts.py` + `images.build_prompt` + `mock.PROMPT_TAIL_LINES`。mock 的尾部指令改为从 `prompts` 导入（消除复制）。

**【优先级】** P2
**【工作量】** 0.5 天
**【验收标准】** 启动时打印/暴露一个覆盖全部提示词来源的指纹；`grep "请分析这条消息"` 只在 `prompts.py` 出现一次。

---

### A-12【P2】两个项目都**已有**离线 LLM stub 与端到端脚本，却都没接进 CI

**【现象+证据】**
- WingMan：`scripts/openai_stub.py`（标准库实现的离线 OpenAI 兼容服务，带 401/404/400 故障注入，回复复用 `MockProvider`，见其 docstring `openai_stub.py:1-32`）；`scripts/e2e_check.py`（15 处断言）。
- Etude：`scripts/openai_stub.py`（FastAPI 实现，带 `FAULTS` 故障注入）+ `scripts/e2e_check.py`（真实 HTTP、临时数据目录、断言打印成 `12/12`）。
- WingMan CI（`.github/workflows/ci.yml`）只有：语法检查 + pytest + **Mock** 冒烟 + 前端 JS 语法检查——**没有一步起 stub**。Etude CI（`.github/workflows/ci.yml`）有 test/clean-install/secrets 三个 job，**也没有一步跑 `e2e_check.py --llm-base ...`**。
- `grep -n "openai_stub" WingMan/scripts/e2e_check.py` 零命中——连本地脚本之间都没串起来。
- **最硬的一条证据**（与 release-eng 交叉核实）：`grep -rn "openai_stub\|e2e_check" */.github/` 的**唯一命中**是 `Etude/.github/workflows/ci.yml:97`——它出现在密钥扫描的**排除项**里（`':!scripts/openai_stub.py'`），也就是"写进去是为了**跳过**扫描"，**从未被执行**。这比"没出现在 CI 里"更能证明"从未跑过"。
  > **与 release-eng 报告的关系**：本条是他 **R-10**（"CI 只跑简单路径、跳过真实路径"）的**第三种表现**，与 **R-1**（TideWatch 只跑 `-e` 不跑 wheel；WingMan 不在 CI 出包）是**同一失效模式**——三者共享"零密钥、零外网、可上 PR"的解法。他的 R-10 侧重「CI job 结构与发布链路」，本条侧重「LLM 集成面覆盖」。

**【为什么是问题】**
"接真实模型这条路走不走得通"（HTTP 拼装、`response_format` 降级、401/404 翻译、`Bearer` 校验）是这两个项目**最核心的集成风险**，而作者已经**写好了一个不花钱就能验证它的工具**，只是让它躺在 scripts 里。第一轮已提 CI 缺 lint/coverage——**本条目是它未覆盖的"LLM 集成面"**：CI 从未验证过 `OpenAICompatProvider` / Etude `chat()` 这几百行真实网络代码。

**【改法】**
```yaml
# 两个仓库都加一个 job（无需任何密钥、不联网外部）
llm-integration:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.12" }
    - run: pip install -r backend/requirements-dev.txt
    - run: python scripts/openai_stub.py --port 18999 &   # 后台起桩
    - run: sleep 2
    - run: python scripts/e2e_check.py --llm-base http://127.0.0.1:18999/v1
```

**【优先级】** P2
**【工作量】** 0.5 天
**【验收标准】** CI 新增 job 全绿；把 stub 的 `--model` 改成错误值能复现 404 分支并被断言捕获。

---

### A-13【P2】温度与 max_tokens 的选择没有依据，且格式重试会**偷偷改温度**

**【现象+证据】**
- WingMan `complete_json` 在格式解析失败重试时，把温度从调用方给的值**硬改到 0.2**：`llm/base.py:175-178`

  ```python
  raw2 = await self.complete(system, fix, json_mode=True,
                             temperature=0.2, max_tokens=max_tokens,   # ← 覆盖原温度
  ```
  这对 SUGGEST（原温度 0.9，`suggestor.py:236`）意味着：**一次格式失败会把创意任务拉回 0.2**，四次候选可能突然变得雷同、且用户完全不知道发生了这次重试。
- `max_tokens` 两侧默认值不同且无按任务区分：WingMan `config.py:144` 默认 2048，Etude `config.py:34` 默认 4096。SUGGEST（要写 4 条各 5–30 字 + 4 段 rationale）与 FACTS（每条事实很短）用同一个上限。

**【为什么是问题】**
温度是**产品行为参数**（0.9 → 发散、0.2 → 保守），不是"重试时的技术细节"。悄悄改温度会让"同一次操作的结果质量"变得不可复现，也破坏 A-1 的可归因性（留存里记不到"这次其实用了 0.2"）。

**【改法】** 重试时保留原温度（或至少把"重试已改为 0.2"记进 `warnings`/日志）；`max_tokens` 按任务分档配置。

**【优先级】** P2
**【工作量】** 0.5 天
**【验收标准】** 新增用例：SUGGEST 首次格式失败触发重试时，断言第二次请求的 `temperature` 仍为 0.9（或响应里带"已降温度重试"提示）。

---

### A-14【P2】（正面样板）TideWatch 的评测体系——三个项目里唯一值得反向移植的 AI 工程实践

**【现象+证据】**（列出是为了让 A-1 的"最小方案"有可抄的形状）
- 独立评测脚本：`TideWatch/eval/run_eval.py`，三层指标（item / actor / group，`run_eval.py:104-171`），**消融实验矩阵**（7 组配置开关，`run_eval.py:59-67`），评测报告自动生成到 `docs/benchmark.md`（`run_eval.py:214-284`）。
- **CI 里断言不退化**：`.github/workflows/ci.yml:53-105` 的 `smoke` job 生成合成数据 → 跑 `eval/run_eval.py` → 解析 `docs/benchmark.md` → 断言 `item_f1 > 0`、`actor_f1 > 0`、团伙数 > 0。注释还写明"阈值刻意只卡在'功能还在'的最低线上"——这与 A-1 需要的"防退化但不误伤调参"完全一致。
- 上游还有 `experiments/*.md` 记录基线实验。

**【为什么是问题（对 WingMan/Etude 而言）】**
同一个作者、同样的自律，TideWatch 有"数据 → 指标 → 消融 → CI 门禁"的完整闭环（因为它是规则引擎，天然可复现）；而两个 LLM 项目反而**一个指标都没有**。差距不在能力，在于**没意识到 LLM 也可以离线评测**——而这正是本轮最重要的结论。

**【改法】** 见 §4，把 TideWatch 的形状套到 LLM 上，关键差别是：**用录制回放替代真实调用**。

**【优先级】** —（样板，不单独排期）
**【工作量】** —
**【验收标准】** —

---

## 3. 跨项目共性清单（一次学会，三处受益）

| 编号 | 问题 | 涉及项目 | 优先级 |
|---|---|---|---|
| A-1 | 提示词无版本号 + 无 golden set 回归 | WingMan / Etude | **P0** |
| A-2 | 零 token 计量 / 零成本估算 | WingMan / Etude | **P0** |
| A-3 | 无 LLM 结果缓存 + 无模型路由 | WingMan / Etude | **P0**/P1 |
| A-4 | 单次用户操作的 LLM 成本无护栏 | Etude（WingMan 的 `build_person_profile` 同类） | P1 |
| A-5 | 结构化输出静默补默认值、无存在性校验 | WingMan | P1 |
| A-6 | Mock 降级只落在自检，不附着在结果上 | WingMan | P1 |
| A-7 | 检索暴力线性 + 无切块/rerank/评测 | WingMan | P1 |
| A-8 | 容错 JSON 解析器零测试（Etude 有） | WingMan | P1 |
| A-9 | 生成条数不足时静默接受 | Etude | P2 |
| A-10 | 数据飞轮缺口（选择/修正不回流） | WingMan / Etude | P2/P1 |
| A-11 | 提示词资产分散（provider + mock 复制） | WingMan / Etude | P2 |
| A-12 | 离线 stub 与 e2e 脚本已存在但未进 CI | WingMan / Etude | P2 |
| A-13 | 重试偷偷改温度 / max_tokens 未按任务分档 | WingMan（Etude 同理） | P2 |
| A-14 | 唯一完整的离线评测体系（正面样板） | TideWatch | — |

---

## 4. 落地路线（3 周 + 验收标准）

> 前提：不新增任何云依赖，全部基于**已有的** `scripts/openai_stub.py` + pytest，做到"本地零成本、CI 零成本"。

### 第 1 周 —— 让 AI 的产出"可归因"

| # | 动作 | 对应 | 验收标准 |
|---|---|---|---|
| W1-1 | 加 `PROMPT_VERSION` 常量，覆盖 `prompts.py` + `images.build_prompt` + `mock.PROMPT_TAIL_LINES` 三处来源；写进 `run`/`job` 留存 | A-1 / A-11 | 每次运行记录里可见 `prompt_version`；指纹随任一提示词改动而变 |
| W1-2 | 搭 golden set 骨架与 runner | A-1 | `tests/test_prompt_golden.py` 对 ≥8 条 case 跑结构断言，全绿 |
| W1-3 | provider 回传 `usage`，pipeline 累加进 `trace`；Etude 设置页加单价字段 | A-2 | 单次操作的留存里出现 token 数；界面显示累计花费 |
| W1-4 | 补 `tests/test_llm_json.py`（WingMan） | A-8 | 围栏/夹带/嵌套/尾逗号/顶层数组/空内容 ≥6 类全绿 |

**golden case 格式（可直接用）**：
```jsonl
{"id":"wingman-an-001","task":"ANALYZE","prompt_version":"2026-10-13.a",
 "input":{"peer_message":"哈哈哈今天好累啊，刚加完班","recent":["...","..."]},
 "expect":{"emotion_in":["疲惫","低落","平静"],"intensity_range":[3,8],
           "topics_has_any":["加班","累"],"must_have_keys":["subtext","signals","risk"]}}
```
```jsonl
{"id":"etude-ex-001","task":"EXAMPLES","prompt_version":"2026-10-13.a",
 "input":{"target":"appreciate","kind":"word","examples":8},
 "expect":{"min_examples":8,"every_sentence_contains":"appreciate",
           "no_chinese_in":"sentence","scene_not_translation":true}}
```
> 断言原则：**只断言"必须成立的结构性事实"**（条数、必含词、禁含字符、字段存在），**绝不断言逐字文本**——否则模型一升级就全红，CI 会被删掉（TideWatch 的注释正是这个教训，`ci.yml:70-71`）。

### 第 2 周 —— 让 AI 的产出"可计量、可回放"

| # | 动作 | 对应 | 验收标准 |
|---|---|---|---|
| W2-1 | 加确定性任务缓存（FACTS/PROFILE/SUMMARY） | A-3 | 相同输入第二次不再发 HTTP（stub 计数断言） |
| W2-2 | 加 `llm_model_cheap` / `llm_model_strong` 路由 | A-3 | FACTS/SUMMARY 走 cheap 模型 |
| W2-3 | 把 `scripts/openai_stub.py` 接进 CI（新增 job） | A-12 | CI 拉起 stub + 跑 e2e，全绿；错误模型名能复现 404 分支 |
| W2-3b | **与 release-eng 的 R-10/R-1 合并成同一次 CI 改造**：三类 job（发布路径 / 真实网络路径 / 离线降级路径）一次提出 | A-12 / R-10 / R-1 | 一次评审通过；三类 job 共享"零密钥、零外网、可上 PR"的模板 |
| W2-4 | golden runner 依赖 stub 跑进 CI | A-1 / A-12 | CI 里 golden 用例全绿，无任何外部网络 |

### 第 3 周 —— 让"变差"能被拦住

| # | 动作 | 对应 | 验收标准 |
|---|---|---|---|
| W3-1 | Etude 计划生成加成本护栏 + 默认改 `search` | A-4 | 超阈值未确认返回 409；默认生图来源非 `both` |
| W3-2 | 结构化输出存在性校验 + `warnings` 回传 | A-5 | 结构异常时 `warnings` 非空、前端可见 |
| W3-3 | Mock 结果附带可见标记 | A-6 | mock 模式响应含演示引擎 warning |
| W3-4 | 建 retrieval set + `eval/retrieval_eval.py`，输出 recall@k | A-7 | 输出 recall@5/@10/MRR；矩阵缓存命中 |
| W3-5 | Etude 反馈导出（复用已有的手工修正数据） | A-10 | 导出 JSONL 带 `prompt_version`、不含密钥 |

**里程碑验收（一句话）**：三周后，能做到"**改一版提示词 → 跑一次离线 golden → 看到 recall/结构断言与 token 成本三个数字 → 决定是否保留**"。这就是这一轮要补上的核心能力。

---

## 5. 待确认项（未验证，需实测，绝不编造）

1. **Token 与成本量级为估算值**。文中"单次分析约 0.6–1.2 万 token 输入"是按 `context.py:37-40` 的 `MAX_FACTS=60 / MAX_SUMMARIES=5 / MAX_RECENT=24 / top_k≤80` 与各段截断长度（每条 fact ~20 字、retrieved 每条 ≤300 字、recent 每条 ≤200 字）**按中文约 1.5 字/token 粗估**，非实测。需以 A-2 的 `usage` 采集落地后回填真实值。
2. **外部定价数字**。§0/§2 未写死任何厂商单价。查询日期 2026-10-13，检索到两个第三方汇总页（llmprice.cn、cloudmart.dev/blog/llm-api-pricing-2026）给出的量级大致为"budget 档 $0.1–0.6 / 1M，frontier 档 $3–15 / 1M"，但两份来源彼此不一致、且与 DeepSeek 官方页未必同步。**具体单价一律以各厂商官方定价页为准**，本报告不作为依据。
3. **Etude `_provide_both` 在"检索先赢"时，画图那一路是否真的跑完并计费**——取决于具体厂商是否在连接关闭后仍计费。`images.py:721-722` 用 `wait=False, cancel_futures=True`，`cancel_futures` 只对**尚未开始**的任务有效，已在跑的线程无法取消（作者在 `images.py:693-695` 也承认了）。**计费口径待确认**。
4. **WingMan `extract_facts` 的实际调用次数**取决于会话长度与 `FACT_MAX_LINES=600`（`profiler.py:24`）。若某会话消息数 < 60，则只 1 次调用；"最多 10 次/渠道"是上限而非均值。
5. **检索召回率基线未知**。没有 retrieval set 前，无法判断当前 `W_SEMANTIC=0.60` 与 `min_score=0.12` 是偏高还是偏低——这正是 A-7 要先建评测的原因。
6. **`HashEmbedder` 的 512 维默认值**（`embedder.py:97`）与云端 1024/1536 维不一致，切换 embedder 后旧向量自然失效（`retriever.py:110-112` 用 `name:dim` 做 key），但**重建索引的耗时**与是否需要重新向量化全部历史，未实测。
7. **TideWatch 是否真的完全不调用任何 LLM**——基于 `grep -riE "llm|openai|prompt|chat_completion" src eval` 零命中判断；未逐文件通读 `report.py`（可能有人工撰写模板），故写"未调用 LLM"，不写"无任何 AI 成分"。

---

## 6. 与第一轮报告的关系

> 本轮严格不重复第一轮条目。以下逐条说明重叠处的**新增角度**。

| 第一轮条目 | 本轮对应 | 本轮新增（第一轮未覆盖的面） |
|---|---|---|
| 3.3 / C-4：WingMan `complete_json` 无重试 | A-13 | 第一轮看的是"网络瞬时错误无退避"。本轮指出**格式重试路径存在，但会偷偷把温度从 0.9 改到 0.2**（`base.py:177`）——是"重试语义"问题，不是"缺重试"问题。 |
| 3.2 / E-3：`_provide_both` 线程池成本泄漏 | A-4 | 第一轮是"单张图"层面的泄漏。本轮是**总量面**："默认 both + 默认 20 包 + 无确认"= 一次点击最坏 160 次付费生图，且无任何预算提示。 |
| 5.2③：最大无直测模块 Etude `prompts.py`（433 行零直测） | A-1 | **更正**：`prompts.py` 并非零直测——`tests/test_plans.py:97-100`、`tests/test_storage_pipeline.py:433-455` 有**字符串存在性断言**（`assert "FAILED syllabus" in SYLLABUS_SYSTEM`）。本轮指出：这类断言只能防"文案被删"，**防不住"提示词变差"**——需要 golden set（A-1）。 |
| 5.1：三项目零覆盖率 | A-8 | 覆盖率是全局指标。本轮点名**具体哪个高风险函数零测试**：`parse_json_loose`（`base.py:71`）——三个项目里最脆的一段解析代码。 |
| 4.3 C-6：CORS 过宽 / W-8：异常回显 | A-5 / A-6 | 第一轮是"信息泄露"。本轮是"**信息缺失**"：结果里缺"这是 Mock""这次结构异常"的提示——方向相反的同一类问题（可观测性）。 |
| §8 优势清单：`.env.example` 写得好、Mock 兜底 | A-6 | 第一轮把 Mock 兜底列为优点。本轮从**反面**补风险：兜底结果与真实结果的区分只在自检面板，不附着在每次结果上。 |
| 4.4：推荐反向移植 TideWatch 的 CI/插件化 | A-14 | 第一轮把 TideWatch 当"代码工程"样板。本轮指出它**同时是 AI 工程样板**：唯一的离线评测 + CI 防退化门禁，并把它改造成 LLM 版（录制回放）。 |
| 4.2②：Etude 存储层混入领域逻辑 | A-10 | 第一轮是"分层"。本轮指出 `reviews` 表（`db.py:920-956`）**只有计数与 undo 在用**，其质量信号从未回流——是"数据价值"问题。 |
| 7 节路线图（未含任何 AI 项） | §4 | 第一轮 30 天路线图**全部是工程项，无一条 AI 工程化**。本轮给出独立的三周 AI 路线，且全部零云成本。 |

**一句话总结两轮的关系**：第一轮修的是"这堆代码能不能长期活下去"；本轮补的是"**这堆 AI 到底有没有效果、花了多少钱、改了东西怎么知道变没变差**"——后者才是这三个项目真正的产品内核。

---

## 附录：本轮证据索引（关键文件与行号）

| 主题 | 证据位置 |
|---|---|
| WingMan 解析与重试 | `WingMan/backend/app/llm/base.py:71-105`（解析）、`base.py:146-179`（重试/改温度）、`base.py:152`（retries=1） |
| WingMan 静默退化 Mock | `WingMan/backend/app/llm/factory.py:21,36-39,49-51` |
| WingMan usage 丢弃 | `WingMan/backend/app/llm/openai_compat.py:152-155` |
| WingMan 手工 coerce | `WingMan/backend/app/engine/analyzer.py:35-47`、`planner.py:29-39`、`suggestor.py:195-204` |
| WingMan 提示词与 TASK 标记 | `WingMan/backend/app/engine/prompts.py:5-6,33-34` |
| WingMan 检索实现 | `WingMan/backend/app/memory/retriever.py:90,114-117,127,133,140,176`、`store.py:1446-1466` |
| WingMan embedder 降级 | `WingMan/backend/app/memory/embedder.py:94-102,212-239` |
| WingMan 分批抽事实/跨渠道 | `WingMan/backend/app/memory/profiler.py:23-25,66-76,216-225` |
| WingMan Mock 复制指令 | `WingMan/backend/app/llm/mock.py:42-65` |
| WingMan Mock 自检与前端 | `WingMan/backend/app/selfcheck.py:193-201`、`frontend/index.html:2457,3768,3780-3783` |
| WingMan 离线 stub/e2e | `WingMan/scripts/openai_stub.py:1-32`、`scripts/e2e_check.py` |
| Etude LLM 调用与重试 | `Etude/backend/app/providers/llm.py:79-80,336-368,348-349` |
| Etude 解析与规范化 | `Etude/backend/app/providers/llm.py:216-285`、`pipeline.py:90-165,323-372` |
| Etude 计划成本面 | `Etude/backend/app/pipeline.py:412-473`、`api.py:49,509-520`、`config.py:56,58,69,77` |
| Etude 生图提示词硬编码 | `Etude/backend/app/providers/images.py:143-181,678-724` |
| Etude 评分/修正未回流 | `Etude/backend/app/db.py:611-613,869,920-956,985,1024`、`api.py:732-757` |
| Etude 离线 stub | `Etude/scripts/openai_stub.py:1-60`、`scripts/e2e_check.py:1-30` |
| Etude 自承认无质量校验 | `Etude/CHANGELOG.md:422` |
| TideWatch 评测样板 | `TideWatch/eval/run_eval.py:59-67,104-171,184-211`、`.github/workflows/ci.yml:53-105` |

**方法与局限声明（同第一轮口径）**：全部结论基于本地浅克隆的**静态阅读**，未执行测试套件、未安装依赖、未运行被测程序、未调用任何 LLM API。因此"成本数字""调用次数""检索质量"这三类结论均为**基于代码的推算**，已在第 5 节逐条标注为待确认；所有引用行号均为实际读到的代码位置。
