---
type: 全流程报告
project: Etude
version: 0.0.1
date: 2026-10-08
repo: https://github.com/whyao56/Etude
tags: [项目, 语言学习, 大模型, PyInstaller, 间隔重复]
---

# Etude 句子五通道语言训练器 — 全流程报告

> 一句话：给它一个词，它生成 8 条**不同上下文**的例句，并把每一条铺成五种练法
> （阅读 / 听力 / 口语 / 打字 / 造句），自带间隔重复。
>
> 内容由大模型生成，语音走 Edge TTS 或 OpenAI 兼容 TTS，数据全在本机。
>
> *Etude*（/eɪˈtjuːd/）是音乐里的「练习曲」——专为练技巧而写的曲子，
> 不讲故事、不为演出，纯粹为了让手指形成本能。学语言是同一件事。

| 项 | 值 |
|---|---|
| 版本 | 0.0.1 |
| 仓库 | https://github.com/whyao56/Etude （公开，MIT） |
| 发行版 | https://github.com/whyao56/Etude/releases/tag/v0.0.1 |
| 发布包 | `Etude-0.0.1-win64.zip` · 23.4 MB（解压后 49.1 MB / 133 个文件） |
| SHA256 | `28b7507cf2a7d1b0edb77cbeac7798e29d568d6ff111c1d8d9ce7a50247240c8` |
| 源码规模 | 8,665 行（后端 + 前端 + 脚本 + 打包配置） |
| 测试 | 113 个用例（95 个测试函数 + 参数化） |
| 目标语言 | 英语（1 门） |

---

## 目录

- [§0 起点：需求与边界](#0-起点需求与边界)
- [§1 理论 → 设计：六条主张落到哪一行](#1-理论--设计六条主张落到哪一行)
- [§2 数据模型：一个不能合并的主键](#2-数据模型一个不能合并的主键)
- [§3 七个必须守住的不变量](#3-七个必须守住的不变量)
- [§4 打包与发版](#4-打包与发版)
- [§5 测试与守卫的分工](#5-测试与守卫的分工)
- [§6 踩坑清单（22 条）](#6-踩坑清单22-条)
- [§7 验证基线](#7-验证基线)
- [§8 明确没做的，和没验证的](#8-明确没做的和没验证的)
- [§9 可复用的方法](#9-可复用的方法)

---

## §0 起点：需求与边界

原始需求一句话：**「做一个学习自然语言的工具，可以接入大模型，做成 exe 上传到 GitHub
发行版，版号 0.0.1，先用英语为开头。」**

指定了理论基础（必须先读）：

- `D:\世界\语言\` 下的三份 docx（制卡学习模板 / 实例效果 / 实施步骤）
- `C:\Users\HP\Desktop\学习观07.txt`（B 站《学习观 07》讲稿整理）
- 配套知乎文章 `zhuanlan.zhihu.com/p/52208883`、`p/51717106`

### 开工前先问清的四件事

有歧义就问，别猜 —— 尤其是会决定架构的那种：

| 问题 | 答复 | 落成什么 |
|---|---|---|
| 复习方式要不要对接 Anki？ | 「先不用管 anki，那是以后要做的」 | 做**内置**训练器 + 内置间隔重复，不做 `.apkg` 导出 |
| 大模型接入怎么做？ | 「两者结合」 | 7 家预置厂商 **+** 自定义 base_url |
| 语音合成怎么做？ | 「两者都支持」 | Edge TTS（免密钥）**+** OpenAI 兼容 `/audio/speech` |
| 项目名？ | 「你自己给我取一个好听又好记的」 | **Etude** |

### 一个决定产品形态的判断

GitHub 上做「AI 生成语言卡片」的项目已经很多 ——
`mnemorai`、`han-flash`、`anki_ai`、`anki-cards-ai-generator` …

它们绝大多数是「**单词 → 卡片生成器**」：输入一个词，输出一张卡。

要做出区别只有一条路：**不做造卡器，做训练循环。**
所以形态定成「一个词 → 8 条例句 × 5 种练法 → 自带间隔重复」。

### 和常见做法的对比（这就是全部的差异）

| 常见做法 | Etude 的做法 | 为什么 |
|---|---|---|
| 一个词一张卡 | **一条例句五张卡**（听/说/读/写/造句） | 看得懂 ≠ 听得出 ≠ 说得出。合成一张卡等于假设它们能互相迁移 |
| 卡片正面给中文翻译 | 正面给**场景**：「什么情况下会说这句话」 | 给逐字翻译，练习就变成中译英 —— 你在做翻译，不是在建立表达 |
| 同一个中文解释反复出现 | 同一句话存 2~3 种**彼此不同**的中文说法，每次随机给一种 | 让大脑没法把英文锁死到某个固定中文上 |
| 依赖 Anki + AnkiConnect | **自带训练器和间隔重复**，双击就能练 | 少一层依赖就少一处「配好了但没反应」 |
| 例句要手动喂 | 给一个词，**自动生成 8 条不同上下文的句子** | 「用大量不同例子重塑连接」里，凑例子是最费时间的一步 |

---

## §1 理论 → 设计：六条主张落到哪一行

来源：《学习观 07》。这一节是整个项目**唯一真正重要的部分** ——
后面所有代码都是它的执行细节。

| # | 原文主张 | 原文里的说法 |
|---|---|---|
| 1 | 语言是**运动类知识**，不是思考类知识 | 靠意识思考学不会，得靠例子反复训练大脑自动找规律 |
| 2 | 以**句子**为单位，不是单词 | 语言的输入是句子，不是单词 |
| 3 | 同一句话要用**大量不同例子**重复 | 关键不是重复同一个句子，而是不同例子的重复 |
| 4 | 输入输出要**直接关联**，中间不能夹东西 | 图片、文字、声音、欲望、意思都是不一样的东西 |
| 5 | 中文解释**每次都要不同** | 每次中文解释都不同。就是「输出始终一致」的逆向应用 |
| 6 | 听说读写是**四种能力，分别练** | 第三步学阅读，第四步学打字，第五步学听力，第六步学口语 |

### 主张 1 → 五种通道各建一张卡

```python
# backend/app/db.py
CHANNELS = ("read", "listen", "speak", "type", "build")
...
for example_id in example_ids:
    for channel in CHANNELS:
        conn.execute("INSERT INTO cards (lesson_id, example_id, channel, ...)")
```

运动类知识的能力是**分化**的。把它们合成一张「认识这个词」的卡，
等于默认它们可以互相迁移，而原文明确说不行。
所以 8 条例句会产生 **40 张卡**，每张独立调度。

### 主张 2 + 3 → 主动丢弃重复例句

```python
# backend/app/pipeline.py   normalize()
for item in raw_examples:
    if not sentence or sentence.lower() in seen:
        # 重复的例句几乎没用 —— 理论要的是「不同例子的重复」。
        continue
```

提示词里也写成硬约束：

```
# backend/app/prompts.py   SYSTEM
7. Do not repeat the same sentence pattern with only the noun swapped;
   vary the situation, the register, and the sentence structure.
```

如果一个包里有 8 张卡但只有 3 个不同的句子，那 5 张重复的卡
只是在练「记住这一句」，而不是「让大脑自己找规律」。丢掉比留着更划算。

### 主张 4 → 「场景」的定义（**这是最容易做错的一处**）

```
# backend/app/prompts.py   SYSTEM
- "Scene" means THE SITUATION IN WHICH SOMEONE WOULD SAY THIS SENTENCE —
  not a translation of the sentence. This is critical: the app shows the
  scene as a prompt and asks the learner to produce the English. If your
  scene is just a literal translation, the exercise degrades into
  translation practice and the whole method fails.
```

如果把场景写成「任何人都能欣赏我们的音乐」，口语卡就变成了中译英练习 ——
学习者在做**翻译**（意识参与、慢、可思考），而不是从场景**直接到表达**
（自动、快、不思考）。整个方法废在这里。

所以有测试盯着这句话还在不在：

```python
def test_prompts_forbid_translation_shaped_scenes():
    assert "SITUATION" in SYSTEM
    assert "not a translation" in SYSTEM or "NOT a translation" in SYSTEM
```

**听力卡刻意不经过图片**：`listen` 通道的正面只有声音。
加图会引入「声音→图片→意思」这条转接，正是原文点名的错误。

### 主张 5 → 同一句话存多种中文说法，每次随机取一种

原文的例子很有说服力：
`I'm afraid I succumbed to temptation and had a piece of cheesecake.`
有三种都不一样的说法 ——「没忍住偷吃了」/「看着眼前的芝士蛋糕，我最终还是没能控制住
我自己，第二天胖了2斤」。

```sql
-- backend/app/db.py
zh_variants TEXT NOT NULL DEFAULT '[]',   -- JSON 数组
```

```javascript
// backend/frontend/index.html
state.variantIndex = variants.length > 1
  ? Math.floor(Math.random() * variants.length) : 0;
```

**为什么随机而不是全显示**：全显示的话，学习者会拿三种说法去**推导**英文怎么写，
又回到思考类知识。随机给一种，他就只能从场景本身出发。

**为什么同一张卡内保持不变**：每次翻面都变，读起来像界面在抖，用户会以为是 bug。
（这条是实机看过才发现的。）

### 主张 6 → 打字卡做逐词比对，不是「对/错」

```javascript
function diffWords(typed, target) { ... }
// 红色波浪线 = 漏掉或打错，黄色 = 多打的，绿色 = 对上的
```

**为什么不做相似度百分比**：学习工具里「哪几个词对了」比「相似度 73%」有用得多。
百分比不能告诉学习者下一步该干什么。

---

## §2 数据模型：一个不能合并的主键

四张表，全部在 `backend/app/db.py` 的 `SCHEMA` 里。
用扁平字典出入，**不引 ORM**：这些数据最终要原样变成 JSON 给前端，
字典省掉一次转换；而且没有编译器的项目里，ORM 的字段名拼错只会在运行时炸。

```
lessons ──┬── examples ──┬── cards ── reviews
          │              │
          └── swaps ─────┘（swaps 挂在 lesson 上，不挂 example）
```

| 表 | 一行是什么 | 关键字段 |
|---|---|---|
| `lessons` | 一个训练包 | `target`、`kind`、`status`、`error` |
| `examples` | 一条例句 | `sentence`、`scene_en`、`scene_zh`、`zh_variants`(JSON)、`audio_path`、`audio_voice` |
| `swaps` | 一组换词候选 | `role`(主/谓/宾)、`original`、`candidates`(JSON)、`samples`(JSON) |
| `cards` | 一张卡 = (例句, 通道) | `due_at`、`interval`、`ease`、`reps`、`lapses`、`introduced` |
| `reviews` | 一次评分 | `card_id`、`grade`、`seconds`、`at` |

### 主键是 `(例句, 通道)`，不是 `(单词)`

```sql
UNIQUE (lesson_id, example_id, channel)
```

这是整个数据模型里唯一一处「看着可以合并、其实不能」的设计。

### 时间戳一律 UTC ISO 字符串

刻意不用 `sqlite3` 的 `DATETIME` 类型：它没有时区概念，
而「今晚 8 点该复习了」这件事需要跨时区正确。

### 间隔重复：两处对 SM-2 的偏离

`backend/app/srs.py` 是**纯函数**，不碰数据库、不碰时间（`now` 由调用方传）。

```python
schedule(interval, ease, reps, lapses, grade)
    -> (interval, ease, reps, lapses, delay_minutes)
```

**偏离一：「没想起来」用分钟级重来，而不是推到明天。**

```python
RELEARN_MINUTES = 10.0
```

原文没提间隔重复，这是我加的判断：一张卡在当次会话里就再也见不到，
和「练三五次形成本能」是矛盾的。10 分钟足够让短时记忆退掉一点，
又不至于当场想起答案。

**偏离二：`delay_minutes` 和 `interval_days` 是两个返回值。**

「10 分钟后」和「0.007 天后」是同一个时刻，但只有一个能在界面上显示。
分成两个字段，`human_delay()` 才能给出「10 分钟后 / 1.0 天后 / 1.2 个月后」这种话。

（这两个数字都是**拍的**，没有实验支持。见 §8。）

---

## §3 七个必须守住的不变量

每一条都对应真实踩过的坑，并且都有测试盯着。

### 3.1 「在 exe 里吗」只在 `paths.py` 里判断

```python
# backend/tests/test_core.py
def test_frozen_check_happens_in_exactly_one_place():
    """其它模块一律调 audio_dir() / db_path()，不许自己看 sys.frozen。"""
```

一旦有两处判断，早晚会有一处漏掉，表现是「源码态好好的，打包后设置存不下去」——
而这类 bug 打包前测不出来。

### 3.2 `ready` ≠ `complete`

```python
readiness(lesson_id) -> {
    "ready": bool,      # 现在能不能练（有例句就行）
    "complete": bool,   # 素材齐不齐（音频也在）
    "problems": [...],  # 具体缺什么，直接给用户看
}
```

**为什么不能合成一个布尔值**：合成一个 → 语音挂了，整个包判定为「不可练」→
读写造句四个通道明明是好的却跟着被封掉。分开 → 语音挂了只影响听力卡，
其余照练，界面显示一条「有例句但没有声音，点这里补语音」。

而且 `readiness` **不看 `status` 字段**，一律从实际内容算。
`status='ready'` 只表示「生成任务跑完了」，不表示「能用」。
**这两者的差集，就是「看着配好了、用起来没反应」的全部来源。**

### 3.3 音频文件名是内容寻址的

```
<engine>-<sha256(engine|voice|text|rate)[:20]>.mp3
例：edge-3f8a1c9d2b4e5f6a7b8c.mp3
```

两个后果都是想要的：同一句话换音色生成新文件、换回来命中旧文件（不重复存）；
以及 `/api/audio/{name}` 可以用正则 `^[a-z]+-[0-9a-f]{20}\.mp3$` 校验，
**路径穿越在进入文件系统之前就被挡掉**。

**存相对路径而不是绝对路径**：绝对路径换个数据目录就是死链，
备份还原到另一台机器也全废。

### 3.4 一条失败不能拖垮整体

```python
try:
    rel = tts.synthesize(...)
except TTSError as exc:
    problems.append(...)   # 记录
    continue               # 不中断
```

8 条句子里有 2 条没合成出来，用户拿到的是「6 条能听、2 条要补」，
而不是「生成失败，请重试」。

### 3.5 前端事件名必须小写

```javascript
// backend/frontend/index.html   el()
else if (key.slice(0, 2) === "on") {
  node.addEventListener(key.slice(2).toLowerCase(), value);
}
```

**这是踩过的最大一个坑**：`addEventListener("Click", ...)` 既不报错也不触发。
界面照常画出来、截图看不出来、Python 测试也测不到 —— **所有按钮都是死的。**

### 3.6 端口被占用时先问「对面是不是自己」

| 对面是谁 | 做法 |
|---|---|
| 空闲 | 直接用 |
| 是 Etude（`/api/health` 应答） | **复用**，不抢端口。前端比对版本号和 pid，不一致就弹红条 |
| 是别的程序 | 换下一个端口，最多试 20 个 |

用户双击两次 exe 是最常见的情况。无脑换端口会让第二个实例悄悄起在随机端口上、
开新窗口、两个窗口互相盖同一个 sqlite，表现是「数据丢了」。

### 3.7 退出顺序：`ask_stop()` 只置标志，不 join

从窗口关闭回调里调 `server.join()` 会和 uvicorn 的线程互相等，直接死锁 ——
表现是「关了窗口，进程还在任务管理器里」。
现在的顺序是：窗口关闭 → 置标志 → 主线程 join(超时 5s)。

---

## §4 打包与发版

### onedir，不是 onefile

| | onedir | onefile |
|---|---|---|
| 启动 | 直接起 | 每次解压到临时目录，几百 MB 好几十秒 |
| 退出 | 正常 | **退出即删临时目录** —— 用户会以为数据丢了 |
| 杀毒软件 | 少误报 | 自解压行为经常被拦 |

`console=True`：`--check` 是「双击没反应」的**唯一出口**。关掉控制台，
用户遇到问题就只剩「它不动」这一条信息。

### 显式 `excludes` 不是可选的

```python
excludes = ["numpy", "scipy", "pandas", "matplotlib", "onnxruntime",
            "faster_whisper", "ctranslate2", "tokenizers", "huggingface_hub",
            "av", "soundcard", "PIL", "pymupdf", "tkinter", "PyQt5", ...]
```

开发用的 venv 里装着上个项目的 faster-whisper / onnxruntime / tokenizers，
PyInstaller 会顺着 import 图把它们全拉进来 —— 包会从 49 MB 涨到好几百 MB。

代价是：如果哪天代码真的 import 了 `PIL`，包会打出来但运行时报
`ModuleNotFoundError`。所以有一道**归档核对**：

```python
required = ["fastapi", "starlette", "uvicorn.protocols.http.h11_impl",
            "edge_tts", "httpx", "app.api", "app.pipeline",
            "app.providers.llm", "app.providers.tts", "app.selfcheck"]
```

用 PyInstaller 自己的归档读取器查，**不用 `grep` 二进制** ——
模块名真的在包里时内容是压缩的、grep 搜不到，而不在包里时
文档字符串里可能又恰好有这个名字。**两个方向都会给假结论。**

### 三个「发布前必须自动化」的理由

发版有 6 步（打包 → 算校验和 → 取凭据 → 建 release → 传附件 → 验证下载页），
手点容易漏掉校验和，或者把一个旧包传上去。脚本把
「包和校验和必须同源」变成默认行为：

```python
# 校验和要印在发行说明里。如果不一致，说明说明是旧版本留下的 ——
# 那正是「文档和产物对不上」的经典症状，宁可拦住也不要发出去。
if digest not in notes:
    raise SystemExit("发行说明和产物对不上，先改说明再发。")
```

**为什么 exe 走 Release 而不是提交进仓库**：
① 二进制不该进版本历史（仓库会膨胀，且历史再也瘦不回去）；
② GitHub 单文件硬限制 100 MB，而解压后的目录有 133 个文件。
Release 附件是官方为此设计的出口：可下载、有稳定 URL、可校验、不污染历史。

---

## §5 测试与守卫的分工

| 手段 | 覆盖什么 | 为什么不能用别的手段 |
|---|---|---|
| `pytest`（113 项） | 逻辑、边界、错误方向 | —— |
| `check_js.py` | 前端调用点、**事件名大小写** | 零构建项目没有编译器，这是补偿 |
| `ui_smoke.js` | 真浏览器里点一遍 + 收集控制台错误 | Python 测试测不到「点了没反应」 |
| `e2e_check.py` | 对**打包版**打真实 HTTP | 源码态跑通 ≠ 打包后跑通 |
| `build_exe.py` 归档核对 | 打包后模块到底在不在 | 只看 exit code 会漏掉「打出来了但是空的」 |
| 冻结态 `--check` | 打包后自检 | 同上 |

### 守卫式的测试要能证明自己会失败

`check_js.py` 里有一组 `_SELF_TEST_SAMPLES`，每次运行前先验探针本身；
`test_guards.py` 里也有反证用例（故意喂一个 `onClick` 进去，断言守卫会报）。

**为什么**：探针坏了会伪装成被测对象坏了。
这个项目上真发生过 —— `check_js.py` 的清洗器被一个正则字面量里的单引号骗了，
把一大段代码当成字符串吃掉，然后报了 **8 个「你的函数未定义」的假警报**。
没有探针自检的话，那 8 个警报会把人引到完全错误的方向。

### 不用真密钥跑通全流程

`scripts/openai_stub.py` 是一个本地假模型，按模型名模拟 10 种故障：

```
fault-401  fault-403  fault-404  fault-500  fault-429
fault-notjson  fault-fenced  fault-messy  fault-slow  fault-nokey
```

用来验证「错误提示有没有指向一个**能修好的方向**」——
比如 401 应该提示「检查密钥」，而不是「重试」（重试一百次还是 401）。

---

## §6 踩坑清单（22 条）

只列真的花过时间的。**「为什么不能那样写」比「应该怎么写」值得记。**

### 6.1 逻辑类

| # | 坑 | 怎么发现的 | 修法 |
|---|---|---|---|
| 1 | `extract_json` 遇到前面有干扰花括号就放弃 | 测试 | 遍历**每一个** `{` 逐个尝试配平 |
| 2 | `classify_target` 把 `in the long run`（4 词短语）判成句子 | 测试 | 不能简单用「词数 ≥ 4」→ 改用句子标志词 + 结尾标点 + `>= 6` 词 |
| 3 | 假模型服务把目标句硬塞模板产生病句 | 端到端看到 `I really I would rather stay home tonight.` | 按 `kind`（word/phrase/sentence）分开模板，`_shift()` 做人称时态变形 |
| 4 | `readiness()` 把音频缺失算作不可练 | 写测试时想清语义 | 拆成 `ready` / `complete` 两个字段 |
| 5 | `_synthesize_*` 成功返回但不写字节 | 想到「界面会画出一个点了没反应的播放按钮」 | 合成完检查文件真的存在且非空 |

### 6.2 前端类（这一组最值钱）

| # | 坑 | 怎么发现的 | 修法 |
|---|---|---|---|
| 6 | **所有按钮点击都是死的** | `ui_smoke.js` 报「等不到：例句列表」 | `el()` 里 `.toLowerCase()` |
| 7 | `pollLesson` 用单个共享定时器，同时生成多个包只有最后一个被轮询 | 读代码时想到 | `pollTimers = new Map()`，键是 lesson_id |
| 8 | `retryLesson` 会创建一个名叫 `__retry__` 的训练包 | 读代码 | 新增 `POST /api/lessons/{id}/regenerate` |
| 9 | `practiceOne` 靠推算卡片 id（依赖「id 连续」，重生成一次就废） | 想到「重生成一次这个前提就没了」 | `lesson_detail()` 返回 `cards` 清单，前端**查表** |
| 10 | 同一张卡内中文说法每次翻面都重新随机 | 实机看，像界面在抖 | `state.variantIndex` 在 `fetchCard()` 时定下来 |

关于 #6 的旁证很有意思：这个 bug 存在期间，`screenshots.js` 只能生成 **8 张**截图
（`04-listen-front.png` 一直缺失 —— 那一步要先点一个按钮才能到）。修好之后 9 张齐全。

### 6.3 守卫/测试自身出错

| # | 坑 | 教训 |
|---|---|---|
| 11 | `check_js.py` 被正则字面量 `/[^a-z0-9' ]/g` 里的单引号骗了，把一大段代码当字符串吃掉，报 8 个**假警报** | **探针坏了会伪装成被测对象坏了**，而它给出的错误方向会让你去改完全正确的代码 |
| 12 | 断言 `"重试" not in hint`，但 hint 里是「**重试也不会好**」 | 断言要盯**意思**不是**词面** —— 词面禁掉会把正确的话也误判 |
| 13 | 断言 `fault-403` 映射到 `http`，代码里有专门的 `forbidden` 分类 | **代码比我的测试更对**。改期望，并新增一条「三种故障说的话互不相同」 |
| 14 | `test_extract_json_survives_real_world_shapes` 失败，原因和它看起来的完全无关 | 一个测试失败可能和它看起来的原因无关（那次的真因是 #1） |

修法：`check_js.py` 加正则/除法判定 + 5 个样本的 `self_test()`，
**每次运行在给结论之前先验探针本身**。

### 6.4 打包与发版（全是「第二次才暴露」）

| # | 坑 | 症状 | 修法 |
|---|---|---|---|
| 15 | onedir vs onefile | onefile 退出即删临时目录，用户以为数据丢了 | onedir |
| 16 | `excludes` 没写全 | 包从 49 MB 涨到好几百 MB | 显式切断 |
| 17 | `grep` 二进制核对模块 | 两个方向都给假结论 | 用 PyInstaller 归档读取器 |
| 18 | 截图被系统显示缩放压小（`SHOT_WIDTH=1400` 实测 1080） | 图糊 | Chrome 加 `--force-device-scale-factor=1` |
| 19 | **第二次打包必定失败** | 只报一句含糊的「PyInstaller 失败了」 | 见下面展开 |
| 20 | **发布 zip 不可复现** | `--check` 的哈希印进说明后，正式发版又算出另一个值 | 见下面展开 |

### #19 展开：为什么第二次打包失败，且报错完全指错方向

PyInstaller 在 COLLECT 阶段会先 `_rmtree` 已存在的输出目录
（`PyInstaller/building/api.py`，注释写着
「will prompt for confirmation if --noconfirm is not given」）。

本机有一层批量删除保护：一次删 >50 个文件需要人工确认。
脚本里的确认传不进去，于是每次重建都在这里死掉，
而报出来的只有一句 **「PyInstaller 失败了」** ——
看这个提示会去查 spec、查依赖、查版本，**全都不相关**。

**修法**：`scripts/products.py` —— 不去删旧目录，**换一个空位写新产物**：

```
dist/Etude              第一次
dist/build2/Etude       第二次
dist/build3/Etude       第三次
```

`build_exe` / `make_release` / `e2e_check` 共用它的 `newest_output()`
去找最近一次的那份 —— 按 `Etude.exe` 的**修改时间**排序，不按目录名
（`build2` / `build10` 按字符串比大小会得到**错的顺序**）。

附带的好处正好是想要的：上一份产物还在，体积对比和回滚都不用重新打包。

**这个坑的一般形式值得记**：环境里有一层保护 → 脚本里的一步失败 →
报错信息指向一个和真因无关的方向。修的不是那一步，是让脚本不必做那一步。

### #20 展开：一个不可复现的产物，让「校验和」这件事变成空话

`--check` 算出的哈希是 `f374bcb6…`，印进发行说明，正式发版却算出 `26e077fe…`，
脚本拦住不让发。看起来像「说明是旧版本留下的」，但真因是：

```python
# zipfile 内部：writestr 用**打包那一刻**的时间建 ZipInfo
zinfo = ZipInfo(filename, date_time=time.localtime()[:6])
```

同一份产物、同一个文件名，两次打包得到两个不同的 SHA256 ——
那么「把校验和印在说明里，让用户核对」从根上就是**假的**。

**修法**：所有条目统一写一个固定时间戳。

```python
FIXED_TIME = (1980, 1, 1, 0, 0, 0)   # ZIP 的 DOS 时间最小年份就是 1980
                                      # 写更早的值会被钳成 1979，反倒让部分解压工具报错

def _add(zf, arcname, data):
    info = zipfile.ZipInfo(arcname, date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data, compresslevel=9)
```

改完连跑两次，哈希一致。

**这一条和 #11 是同一个形状**：一个检查报错时，**先确认检查本身是不是错的**。
如果当时直接「按提示把新哈希抄进说明」，就会把一个不可复现的产物发出去。

---

## §7 验证基线

改任何东西之后，这七个数字都要能复现。

| 项 | 值 | 命令 |
|---|---|---|
| 测试 | **113 passed** | `cd backend && python -m pytest tests/ -q` |
| 前端守卫 | **73 处调用全部有定义** | `python scripts/check_js.py` |
| 浏览器交互 | **21/21** | `node scripts/ui_smoke.js` |
| 端到端（打包版） | **18/18** | `python scripts/e2e_check.py --llm-base http://127.0.0.1:18999/v1` |
| 打包 | **49.1 MB / 133 个文件**；归档核对 **10/10** | `python scripts/build_exe.py` |
| 发布 zip | **23.4 MB**，SHA256 可复现 | `python scripts/make_release.py --check` |
| 下载页 | HTTP 200，实测哈希与说明一致，CRC 全过 | 从 Releases 页真拉一次 |

### 冻结态自检的实际输出（这就是「双击没反应」时会看到的东西）

```
Etude 0.0.1 自检
总体：WARN
[  OK  ] 数据目录：C:\Users\HP\AppData\Local\Temp\etude-smoke-xxx
[  OK  ] 界面文件：...\_internal\frontend\index.html（58 KB）
[  OK  ] 数据库：0 个训练包 / 0 张卡
[ WARN ] 大模型：https://api.deepseek.com/v1 · deepseek-chat · 还没填密钥
           → 本地 Ollama 之外的厂商都需要密钥。去「设置」里填。
[  OK  ] 语音引擎：edge-tts · 默认音色 en-US-AriaNeural
[  OK  ] 原生窗口：pywebview + 系统 WebView2
[  OK  ] 音频缓存：0 个文件
[  OK  ] 运行形态：打包版 exe · Python 3.13.14 · Etude 0.0.1
```

**三档 ok/warn/fail 的设计**：`warn` 不等于坏。
比如缺 WebView2 只报 `warn` —— 因为会退回浏览器打开界面，功能一模一样。
报 `fail` 会把一个「能用但没那么好看」的状态说成「不能用」，那是误导。

---

## §8 明确没做的，和没验证的

### 刻意不做（不是没来及）

| 没做 | 为什么 |
|---|---|
| 听力卡上放图片 | 原文明确禁止「声音→图片→意思」这条转接 |
| 语法讲解 / 语法笔记字段 | 原文：「声音这种多因素且对速度有要求的知识超出意识能力范围」。讲语法是在喂意识 |
| 「一个词一张卡」的模式 | 原文以句子为单位 |
| 中译英练习 | 那是翻译训练，属于思考类知识 |
| 发音打分 / 语音识别 | 需要参考音素序列 + 打分模型（几百 MB）。**范围决定，不是否定它的价值** |
| Anki 导出（`.apkg`） | 用户明确说「先不用管 anki，那是以后要做的」 |
| 英语以外的语言 | 用户说「先用英语为开头」 |

### **没有验证的** —— 这一节最重要

**真人长期使用效果完全没有验证。** 以下全部是**未经证实的假设**：

- **假设一**：8 条例句足以让大脑开始归纳出用法。
  **没有任何证据说明 8 这个数字是对的** —— 它只是「一次生成不贵、看起来够多」的折中。
- **假设二**：五种通道分开练比合成一张卡更有效。
  理论上是这么说的，但这个产品**没做过对照实验**。
- **假设三**：「没想起来 → 10 分钟后再来」比「推到明天」更有效。
  原文没提间隔重复，10 分钟这个数字是拍的。
- **假设四**：每次随机给一种中文说法能阻止「英文↔固定中文」的锁死。
  合理，但没验过。
- **假设五**：模型生成的例句质量够用。
  **这条最可能不成立** —— 弱模型给的句子平淡甚至不地道，而程序不做任何质量校验。

**这一节存在的意义**：如果三个月后发现效果不好，应该能从这里看出
**是哪个假设错了**，而不是笼统地觉得「这个方法不行」。

### 只在一台 Windows 机器上验证过

- **没测过**：中文用户名下的路径、没有写权限的目录、杀毒软件拦截、
  公司代理/防火墙环境、显示器缩放不是 100%。
- `paths.py` 里给非 Windows 留了兜底（`~/.etude`），
  **但那行代码从没被执行过**。
- 模型兼容性只测了「协议层」：真正跑通的只有本地假模型和端到端里的假 HTTP 服务。
  7 家预置的 base_url 和默认模型名是**照着各家文档填的**，没有逐个真机验证。
- 语音只测了「能用」，没测「好听」；音色没逐个听过。

### 已知问题

| 问题 | 影响 | 打算怎么办 |
|---|---|---|
| **语速设置在「大模型 TTS」下静默失效** | `_synthesize_openai()` 的 payload 里没有 `speed`，不报错只是没作用 | 0.0.2 映射成 OpenAI 的 `speed` 浮点数（0.25~4.0） |
| 大模型 TTS 的音频缓存被语速分叉 | `cache_name()` 把 `rate` 算进哈希，但 OpenAI 路径根本不用它 → 改语速会白合成一份相同内容 | 同上修复顺带解决 |
| Edge TTS 依赖在线接口 | 断网时**新生成的包**没有语音（已生成的包不受影响） | 无解，Edge 本来就是这个性质（已写进文档） |
| 严格 JSON 输出对弱模型不友好 | 弱模型会给出格式错的回复，或偷懒给逐字翻译的「场景」 | 三层解析兜底 + 错误提示说清方向。**换模型比改代码有效** |
| 一次生成超过 3 个包会排队 | 第 4 个及以后显示「正在生成」但还没开始 | 界面把「排队中」和「正在生成」分开显示 |
| 磁盘满了 / 数据库损坏 / 系统时间被改 | 没测 | 自检能发现查不了，但不能修 |

---

## §9 可复用的方法

这份报告里能抽出来下次直接用的：

### 1. 三层错误分诊：每层给一个**能修好的方向**

`explain_error()` 的判断顺序讲究：

```
① ImportError / ModuleNotFoundError   ← 必须排在最前
② 本机地址连不上（Ollama 没开）
③ HTTP 状态码分类（401/403/404/429/5xx）
④ 超时 / 网络
⑤ 未知
```

**为什么「缺组件」必须排在所有网络关键词之前**：如果排在后面，
用户会收到「重试 / 换网络 / 换镜像」——**这条建议永远修不好问题**，
因为真正的原因是 `ModuleNotFoundError`。

而且**每种故障说的话必须互不相同** —— 三种故障给同一句话等于没提示。
有测试专门断言这一点。

### 2. 前置检查 + 归档核对 + 冻结态自检：三件「很容易漏」的事脚本化

打包脚本不只是调 PyInstaller，它把三件容易漏的事变成默认行为：

- **打包前**：跑前端静态守卫 + 检查前端版本常量和后端 `__version__` 是否一致
- **打包后**：用归档读取器核对关键模块真的在包里
- **最后**：跑一次 `Etude.exe --check`

**为什么「版本号一致」要作为前置检查**：前后端两处各有一个版本常量，
不一致的表现是「界面上显示旧版本」，而这会让「有没有更新成功」这个判断失效。

### 3. 体积基线：只报警，不失败

```python
SIZE_WARN_BYTES = 260 * 1024 * 1024
```

体积增长有时候是合理的（加了功能），有时候是失误（漏了 excludes）。
**报警让人去看一眼，失败则会把合理的增长也拦下。**
一个会误报的检查，最后一定会被绕过。

### 4. 守卫式测试必须先在旧代码上失败

写守卫的时候，一定反问一句：**「如果我把这个 bug 改回去，守卫会不会报？」**

这个项目上真的验过：

```python
# test_guards.py
def test_event_name_guard_would_catch_the_old_writing():
    assert bad_event_type_literals('el("button", {onClick: go})')[0]  # 旧写法要能被逮到
```

手工也验过：把 `function reveal()` 改名成 `revealTheCard()`，
守卫报 `index.html:1366 reveal()`、退出码 1。

### 5. 不用真密钥验证全流程

假模型能模拟各种坏情况，让「错误提示对不对」这件事可以在 CI 里自动化。
**这比手工造错高效得多，而且不会漏。**

### 6. 截图要脚本化，不能手截

**旧图比没有图更糟。** 手工截的图在下一版就会开始说谎，
而脚本化的图跑一次就能跟上。

### 7. 文档分两份，目标相反

- `README.md` 要**说服人来看**；
- `STATUS.md` 要**说服人别误解**。

混在一起写必然有一边失真。所以单独有一份
「没做什么、没验证什么、哪些假设可能错」的诚实记账。

---

## 附：文件地图

```
etude/
├── backend/
│   ├── run_etude.py            入口（--check / --check-deep / --port / --no-window）
│   ├── app/
│   │   ├── __init__.py         ★ 版本号；BLAS 线程限流（必须在最前）
│   │   ├── paths.py            ★ 唯一判断「在不在 exe 里」的地方
│   │   ├── config.py           设置读写 + 厂商预置 + 密钥脱敏
│   │   ├── prompts.py          ★ 理论 → 提示词那一层
│   │   ├── providers/llm.py    OpenAI 兼容协议 + 错误分诊
│   │   ├── providers/tts.py    Edge TTS / OpenAI TTS + 内容寻址缓存
│   │   ├── pipeline.py         ★ 生成流水线（作业表 / 逐条失败不拖垮整体）
│   │   ├── db.py               四张表 + readiness
│   │   ├── srs.py              间隔重复（纯函数）
│   │   ├── api.py              22 个 HTTP 接口
│   │   ├── server.py           端口选择 + 优雅停止
│   │   ├── desktop.py          原生窗口，失败返回 False
│   │   └── selfcheck.py        八项自检
│   ├── frontend/index.html     单文件界面（1482 行，零构建零 CDN）
│   └── tests/                  113 个用例
├── scripts/
│   ├── build_exe.py            打包编排
│   ├── make_release.py         发版（含「校验和必须印在说明里」的硬约束）
│   ├── products.py             ★ 打包产物在哪（三个脚本共用的判断）
│   ├── e2e_check.py            对打包版打真实 HTTP
│   ├── ui_smoke.js             真浏览器点一遍
│   ├── screenshots.js          出文档截图
│   ├── openai_stub.py          本地假模型
│   ├── cdp.js                  自写 CDP 客户端（避免下几百 MB Chromium）
│   └── check_js.py             前端静态守卫
├── build/etude.spec            打包配置
└── docs/
    ├── THEORY.md               理论 → 代码的逐条映射
    ├── ARCHITECTURE.md         不变量清单
    ├── QUICKSTART.md           三种跑法 + 排错决策树
    ├── STATUS.md               没做什么、没验证什么
    └── DEVLOG.md               每一轮的起点 / 做法 / 踩坑 / 怎么验证
```

---

## 附：几个刻意的技术选择速查

| 选择 | 为什么 |
|---|---|
| 监听 `127.0.0.1` 而非 `0.0.0.0` | 本机单人工具，没有理由让同局域网的人读到你的数据、改你的配置 |
| 数据存 `%LOCALAPPDATA%\Etude` | 打包后程序目录可能只读；且「换个位置解压 = 丢数据」是最糟的体验 |
| 备份用 `VACUUM INTO` 而非复制文件 | 数据库开着 WAL，直接复制会丢掉未落盘的部分 —— 打开是好的、内容却是旧的 |
| 界面 HTML 带 `no-store` | 打包后界面从 `_internal/` 读，浏览器拿旧 HTML 会表现成「代码改了但没生效」 |
| 前端不用任何 CDN | **断网也要能练**。例句和语音都在本机，没道理打开界面还要等一个 CDN 请求 |
| 前端不用 `innerHTML` 拼接 | 例句里有用户输入的目标词，拼字符串就是 XSS 入口 |
| 自写 CDP 客户端（`cdp.js`） | 用 Node 22 自带 WebSocket 驱动本机 Chrome，避免下载几百 MB Chromium |
| 端口选 8977 | 刻意避开上个项目用过的 8787（那台机器上留着一堆旧进程，手工验证时 curl 会打到旧进程上） |
| 提交用匿名邮箱 | 公开仓库里不暴露 QQ 邮箱，同时仍正确关联到 GitHub 账号 |

---

## 许可

[MIT](https://github.com/whyao56/Etude/blob/main/LICENSE)
