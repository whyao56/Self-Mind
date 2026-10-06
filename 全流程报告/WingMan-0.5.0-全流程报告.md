# WingMan 0.5.0「先填后补」· 全流程报告

> **交付日期**：2026-10-06
> **仓库**：<https://github.com/whyao56/WingMan>
> **Release**：<https://github.com/whyao56/WingMan/releases/tag/v0.5.0>
> **产物**：`WingMan-0.5.0-win64.zip`（221 个文件，33.8 MB，解压后约 77 MB）
> **SHA256**：`d96894fe2a41eb4091357c6938ebe87a84cbe0082f790c3ce698aadc93d0b184`
> **测试**：235 passed + 1 skipped（20 个测试文件）
> **起点**：`7f69240`（v0.4.0）→ **规模**：29 个文件，+2691 / −152 行
> **CI**：`318dba6` 全绿（Python 3.11 + 3.13 双矩阵）
>
> 本文自包含：所有关键结论都带根因与代码要点，不需要外部附件。

---

## 一、这一版在解决什么

上一版（0.4.0）把记忆的中心从「会话」换成了「对象」，但**顺序是固定的**：
必须先把聊天记录导进来，程序才会替你建出那个对象。

可是人的真实顺序常常是反的 —— 你先听说了一个人、先知道了一些情况
（她叫什么、你们是什么关系、你想走到哪一步），**过一阵子**才拿到聊天记录。
想先把「雷区：别提前任」记下来，却发现**没有地方写**，因为还没有任何一条记录。

这一版做两件事：

1. **把顺序解开** —— 先建对象、随时补、之后再用记录去完善它；
2. **补上「其他聊天」** —— Telegram / 钉钉 / 短信 / 贴吧里说的话，以前无处安放。

另外顺手挖出并修掉了**三个「静默坏了很久」的问题**，其中最严重的一个是
**「导入微信聊天记录」从项目第一个版本起就是崩的**。

---

## 二、需求对照表（逐条落点）

| # | 需求（原话要点） | 落点 | 状态 |
|---|---|---|---|
| 1 | 「布局你给我自行优化优化」 | 左栏 `232px → 248px`；新增「＋ 新建」与搜索框；对象项改两行（名字 + 关系/时间/渠道数）；对象页新增对象头 | ✅ |
| 2 | 「对象」可以先提前新建 | `POST /api/persons` **只校验名字非空**；左栏 `#obj-new` → `openPersonDialog()` | ✅ |
| 3 | 右键指定的对象可以「打开 / 设置 / 删除」等操作 | `openPersonMenu`：打开 / 设置… / 重命名… / 合并到… / 删除对象…；`ContextMenu` / `Shift+F10` 键盘等价 | ✅ |
| 4 | 提前新建，我可以自行填入部分数据 | 新建弹窗里关系 / 期望关系 / 阶段目标 / 备注**全部可选**；之后「设置…」是**局部更新**，只改填了的 | ✅ |
| 5 | 也可以再导入聊天数据后让大模型帮我优化数据 | `POST /api/persons/{id}/refine` + `profiler.build_person_profile`；对象页「记忆」Tab 的「让 AI 帮我整理」 | ✅ |
| 6 | 除了 QQ、微信聊天外，再加一个「其他聊天」 | 渠道类型 `other`；剪贴板采集白名单加 `other`；导入认 JSON/CSV；粘贴可显式声明来源 | ✅ |
| Bug 1 | 「检查更新你把 0.4.0 写错为 0.3.1 了」 | **真因不是文案**，是旧进程占着 8787 端口答话；另加三层防呆 | ✅ |
| 7 | 「整体再优化优化。更便捷方便，新手友好」 | 空状态重写、上手三步文案、导入标签不再夸大、失败提示改成一指路的话、粘贴框加「来源」下拉 | ✅ |

---

## 三、新增功能

### 3.1 对象可预建 + 右键菜单

新建弹窗与「设置…」共用同一个实现（`openPersonDialog(person = null)`），
**唯一的必填项是名字**：

```js
// frontend/index.html —— 新建：
//   只填名字也能建，之后随时在「设置…」里补。刻意不加任何必填校验，
//   因为「先记个名字、过两天再补」正是这个功能的全部意义。
openPersonDialog(person = null)
```

右键菜单项：

| 项 | 行为 | 为什么需要 |
|---|---|---|
| 打开 | 切到该对象的概览 | 左栏单击的等价物 |
| 设置… | 局部更新（`PATCH /api/persons/{id}`） | 只改填了的字段，**不会因为改名字把阶段目标清空** |
| 重命名… | 只改名字的快捷入口 | 高频操作 |
| 合并到… | `POST /api/persons/{id}/merge` | 「QQ 上的小鹿」和「微信上的鹿鹿」是同一个人 |
| 删除对象… | `DELETE /api/persons/{id}` | **只解除归属，不删聊天记录**（弹窗里写清了这一点，并用 `confirmWithCountdown`） |

### 3.2 「让 AI 帮我整理」——在你的草稿上补，而不是重写

`backend/app/memory/profiler.py` 新增 `build_person_profile(ctx, person_id, *, overwrite=False)`。
与渠道级 `build_profile` 的三处关键差别：

1. **跨渠道**：输入是这个人所有渠道的消息，每条标着来自哪个渠道；
2. **不吃掉用户手写稿**：默认只填空；
3. **先建索引**：顺手把每个渠道的向量索引补齐，导完就能直接分析。

核心合并策略：

```python
_USER_FIELDS = ("goal", "stage", "taboos", "my_style")   # 用户手写的，默认不动
_MODEL_FIELDS = ("peer_profile",)                        # 模型字段，允许改写

for field in _PERSONA_FIELDS:
    old = str(getattr(cur, field) or "").strip()
    new = str(data.get(field) or "").strip()
    if field in _USER_FIELDS and old and not overwrite:
        kept.append(field)
        continue
    if not new:
        continue
    patch[field] = new
    updated.append(field)
```

**`kept` 的判定刻意不看模型有没有给出新值。** 它是给用户的一句**保证**
（「你手写的这四项，我一项都没动」），不是模型这次的成绩单。
如果只在「模型恰好也想改这一项」时才列出来，用户拿到的就是一份随模型心情浮动的清单 ——
少了一项他就得自己去比对是不是被改掉了，反而更不敢按这个按钮。

两条容易被忽略的实现细节：

- **`before_ids` 必须在抽事实之前取**，否则 `facts_extracted` 永远是 0；
- **抽样按渠道配额**：`per_chat = max(10, PROFILE_SAMPLE // len(channels))`。
  不这么做的话，话多的渠道会把话少的整个盖掉 ——
  而「Ta 在 QQ 上很冷淡」这种结论恰恰只存在于那个话少的渠道里。

一个渠道读失败不拖垮其它渠道（逐渠道 try/except 收进 `warnings`）；
还没导入记录的「提前新建」对象按这个按钮**不报错**，而是返回一句「下一步该做什么」。

### 3.3 「其他聊天」渠道

除 QQ / 微信以外的来源，现在是一个**明确定义的位置**，不是「认不出来的东西」。
它有三个接缝，三处都改了：

```python
# backend/app/store.py —— 渠道映射
_CHANNEL_BY_PLATFORM = {
    "qq": "qq", "wechat": "wechat",
    "other": "other", "generic": "other",      # generic 是导入适配器的名字
    "call": "call", "voice": "call",
    "offline": "offline", "face": "offline",
}

def _channel_from_platform(platform: str) -> str:
    """platform → channel。**兜底是 `other`，不是 `generic`。**"""
    return _CHANNEL_BY_PLATFORM.get((platform or "").strip().lower(), "other")
```

```python
# backend/app/api/routes_collect.py —— 半自动采集白名单
# QQ/微信 之外的东西自动采不了，但半自动（剪贴板）采得了 —— 你复制什么它接什么。
# 若沿用 SUPPORT_MATRIX 当白名单，就等于「其他聊天」被自动采集的短板连坐了。
SEMI_CLIENTS: tuple[str, ...] = ("qq", "wechat", "wechat3", "other")
```

**为什么白名单不能复用 `SUPPORT_MATRIX`**：那张表回答的是「能不能读加密库」，
而「其他聊天」读不了加密库、却完全采得了剪贴板。复用会让这个渠道被连坐。

第三处是「显式传入的渠道名也要过映射」——新增 `_norm_channel(channel, platform)`。
原因是半自动采集靠 `channel == client` 认领已有渠道，库里同时存在 `generic` 与 `other`
两个写法时，它会给同一个对象重复建一个渠道。迁移里也把历史 `generic` 行 UPDATE 成 `other`。

### 3.4 导入侧：让用户说清「这话是在哪说的」

**文本排布长得像微信，不等于它来自微信。** 别的聊天工具导出的文本很容易被识别成微信格式。
所以 `import_file` / `import_text` 都新增了 `platform` 参数，用户声明的来源压过适配器猜测：

```python
plat = (str(platform or "").strip() or adapter.platform) or "other"
chat_id = make_chat_id(plat, name)
store.upsert_chat(chat_id, plat, name, peer_name, me_name)
```

粘错标签是静默的 —— 只会在之后某次分析答得不对时才隐约浮出来，很难回溯到导入这一步。
所以 `ImportResult` 也加了两个字段，让结果**当面回报归宿**：

```python
class ImportResult(BaseModel):
    ...
    platform: str = ""     # 这段记录最后归到了哪个平台
    channel: str = ""      # 以及哪个渠道（从库里读回来，不在这里重算一遍映射）
```

界面上（`#paste-platform`）给了「来源：自动判断 / QQ / 微信 / 其他聊天 / 通话 / 当面」，
导入完提示「成功导入 N 条 · 归到「其他聊天」」。

**不认得的平台：渠道兜底 `other`，平台原样保留。** 这是一个刻意的不对称，两边理由不同：
渠道名是给人看的归类，只允许有限几个值；平台名是**用户自己打的字**，
项目在 `openChatSettingsDialog` 里已经立过同一条规矩（认不出来就原样显示「（保持原样）」，
不许悄悄改掉）。

### 3.5 空对象接住之后的同名导入

```python
# backend/app/store.py::ensure_person_for_chat
placeholder = self.find_person_by_alias(name)
if placeholder is not None and self._channel_count(placeholder.id) == 0:
    log.info("「%s」是先前手建的空对象，这次的记录挂到它名下（%s）", name, placeholder.id)
    self.bind_chat(chat_id, placeholder.id)
    return placeholder.id
```

判据是「那个名字下**一段记录都没有**」，这一点是刻意的：

- 空对象里没有任何数据，接住它**不可能把谁的记忆混在一起**，没有猜错的风险；
- 那个名字下**已经有**记录时，退回原来的保守策略（新建，让用户显式合并）——
  因为「QQ 上的张三」和「微信上的张三」是不是同一人，程序无从判断。
  **猜错是静默的，而记忆混在一起比多建一个人严重得多。**

这条同时修掉了一个真实的用户工作流问题：按原来的写法，
「先建对象、后导记录」会得到**两个同名对象**。

---

## 四、三个「静默坏了很久」的问题

这一类问题的共同形状是：**编译不报、导入不报、界面照常打开**，
只有真走到那一条路时才出问题 —— 而那条路恰好没有测试。

| 问题 | 坏在哪 | 为什么没人发现 |
|---|---|---|
| 导入微信记录**必崩** | `wechat.py` 用了 `iter_blocks` 却从未导入它（从项目**第一个提交** `b452293` 起就这样） | 当时**没有任何测试跑过微信适配器**；自带的 `samples/wechat_sample_阿哲.txt` 也是这份坏代码的一部分 |
| 通用 JSON / CSV 列名匹配**失效** | `_resolve_map` 把「候选列名表」当成「数据里实际有的列名」传进去，于是永远只返回候选表的第一个名字 | 只测过「列名恰好等于候选表首项」的形状；模块文档里写的 `who` / `content` 从来没被测过 |
| 粘贴框**读不了自己写的格式** | 界面写着「`2024-01-01 12:00:00 昵称` + 内容」，默认适配器却是只认 JSON / CSV 的 `generic` | 前后端各测各的，没人把「界面上的示范格式」当成输入去跑一遍 |

### 4.1 微信适配器：`NameError: name 'iter_blocks' is not defined`

```python
# backend/app/adapters/wechat.py —— 修复前
from .base import (
    ChatSourceAdapter, RE_SENDER_FIRST, RE_TS_FIRST,
    block_to_parsed, clean_sender, guess_msg_type, is_noise,
    read_text,          # ← 少了 iter_blocks
)

def parse(self, path, options=None):
    ...
    for m, buf in iter_blocks(text, order=order):   # ★ 真跑到这里才炸
```

`iter_blocks` 在 `qq.py` 里是正常导入的，`wechat.py` 里少了这一行 ——
从 diff 上看只差一行 import，很容易被当成「多余」删掉或漏加。
实测确认：修复前 `samples/wechat_sample_阿哲.txt` 与 `samples/qq_sample_小鹿.txt`
**一个崩、一个正常**（62 条），这正是「只测了一条路」的后果。

### 4.2 `_resolve_map`：把候选表当成了实际列名

```python
# 修复前
def pick(role: str, keys: list[str]) -> str | None:
    ...
    for cand in DEFAULT_MAP[role]:
        if cand in keys:
            return cand

return {"sender": pick("sender", list(DEFAULT_MAP["sender"])) or "",
        "ts":     pick("ts",     list(DEFAULT_MAP["ts"]))     or "",
        "text":   pick("text",   list(DEFAULT_MAP["text"]))   or ""}
#                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                      传进去的「keys」是候选表自己，跟数据里有什么列毫无关系
```

于是永远只命中候选表的**第一项**：

```python
DEFAULT_MAP = {
    "sender": ("sender", "who", "from", "name", "speaker", "昵称", "发送者", "用户"),
    "ts":     ("ts", "time", "timestamp", "datetime", "date", "时间", "日期"),
    "text":   ("text", "content", "message", "body", "msg", "内容", "消息"),
}
```

- 时间字段叫 `time`（候选表里排第二）→ 选不中 → 一条都读不出来；
- 中文表头 `时间 / 内容 / 发送者` → 一个都不中 → 一条都读不出来。

**最坏的地方是嗅探和解析说两套话**：`sniff` 看到中文表头给 **0.85** 的高分，
用户看到「匹配度很高」，然后一条都没导进去。

修复：拿**真实列名**去挑（`_resolve_map(options, rows)`），
并且把按值推断的兜底也重写了 —— 它原来用 `set` 遍历列名（顺序不确定），
且「先定内容列再定说话人列」这个顺序是反的（短的说话人列容易被先认成正文，
消息就变成了发送者的名字）。现在：时间列取「能变 datetime 的取值最多」那一列，
内容列取剩下的里**平均最长**的，说话人列取再剩下的里**重复度最高**的。

### 4.3 粘贴框：界面上写的格式读不出来

```python
# registry.import_text —— 修复前：默认适配器是 generic
def import_text(store, text, *, chat_name, adapter_name: str = "generic", ...)
    tmp = ...f"wingman_paste_{...}{suffix}"   # 一律 .txt
```

而 `generic` 适配器**靠扩展名分支**（只有 `.json` / `.csv` / `.tsv` 才走结构化解析），
并且只认 JSON / CSV。所以照着界面上的说明粘贴，结果是一条都没读到。

修复两处：

1. 默认适配器改成 `auto`（交给嗅探）；
2. 后缀从**内容**推（新增 `_guess_paste_suffix`）：首个非空字符是 `[` / `{` → `.json`；
   首行能切出 ≥2 列且「含已知列名」或「每行列数一致」→ `.csv` / `.tsv`；其余 → `.txt`。

顺带修了一个相关的：**所有适配器都打 0 分时会静默落到注册顺序第一个适配器**（QQ）上，
于是提示词也一起说错（「「QQ 聊天记录」读不了这份内容」—— 可问题根本不在于它是 QQ）。
现在 `_pick` 在最高分为 0 时兜底 `GenericAdapter`。

---

## 五、Bug 1 的真根因：「检查更新显示 0.3.1」

**不是文案写错，是一个 0.3.1 时代的旧进程还在 8787 端口答话。**

前端 `index.html` 是 `StaticFiles` **每次从磁盘现读**的（所以是新的），
服务却是一个**一直在跑的进程**（所以是旧的）。于是用户看到「界面是 0.4.0，它说我装的是 0.3.1」。

排查过程（可复用）：

```text
端口 8787（旧进程）: version=0.3.1 → 检查更新：有新版本 v0.4.0（当前 v0.3.1）
端口 8801（新进程）: version=0.4.0 → 检查更新：已是最新（v0.4.0）
```

一开始按「文字写错」的方向找（grep `0.3.1`、看 `#about-ver`、看 `/api/update/check`、
查 GitHub Releases 侧的 `latest`），全部正常。改用
`Get-NetTCPConnection` 列出 87xx–89xx 的监听端口，发现 8787 上有一个 python 进程；
逐个端口打 `/api/health` 比对版本，才确认它就是旧进程。

### 三层防呆（不只满足于杀进程）

1. **前端自带版本号常量**，与 `/api/health` 报的版本比对：

```js
const BUILD = "0.5.0";
// 前端是**每次从磁盘现读**的，服务却是一个一直在跑的进程，两者可以来自不同版本。
```

不一致时在页面顶部弹红横幅 `#ver-warn`，写明「界面 vX，答话的本机服务 vY」+ 旧进程排查步骤。

2. **桌面壳自述**（`GET /api/desktop/state`）：

```python
{
  "version": __version__,
  "started_at": datetime.fromtimestamp(_STARTED_AT).astimezone().isoformat(timespec="seconds"),
  "uptime_seconds": int(max(0, time.time() - _STARTED_AT)),
  "mode": "exe" if IS_FROZEN else "source",
  "pid": os.getpid(),
}
```

旧进程一眼可辨（版本老、已运行很久、是 exe 还是源码、PID 是多少）。

3. **HTML 加 `Cache-Control: no-store`**（`NoStoreHtmlMiddleware`，
只给 `text/html` 补，不覆盖已有的 cache-control 头），界面不会被浏览器缓存钉住。

4. 另加一条测试盯着「前端 `BUILD` 必须等于后端 `__version__`」——
   否则这道检查会变成天天误报的噪音，用户很快学会无视它，那还不如没有。

> **为什么会有旧进程？** 常见来源是 0.4.0 加的「关闭弹窗（后台运行）」那个选项 ——
> 它刻意不结束服务，方便下次双击直接回来。选过它之后又升级程序，就会撞上这个。

---

## 六、验证方式

### 6.1 全量测试

```bash
cd backend && ./.venv/Scripts/python.exe -m pytest tests/ -q
# 235 passed, 1 skipped（20 个测试文件）
```

新增/扩写的守卫：

| 文件 | 项数 | 覆盖 |
|---|---|---|
| `test_adapter_import.py`（新） | 10 | 两份示例文件各经其适配器导入、界面写的粘贴格式真能用、粘 JSON 也能认、列名匹配拿真实列名、解析为空时提示能指路、回报归宿渠道、声明来源压过猜测、`symtable` 静态守卫 |
| `test_frontend_assets.py` | 11→13 | 新增：平台/来源下拉的取值必须在后端平台表里；粘贴框必须给出「来源」入口 |
| `test_persons.py` | 24→26 | 空对象接住同名导入（复用而非新建）+ 反例（已有记录时仍保守新建） |
| `test_objects_center.py` | 28→29 | `kept` 是保证不是成绩单（用「没有证据的字段就不写」的模型桩验证） |
| `test_version.py` | +1 | 前端 `BUILD` == 后端 `__version__` |

### 6.2 六条关键守卫的脚本化反证

标准是项目既有的那条：**新测试要能在旧代码上失败**。把修复逐条改回旧写法，
对应用例必须失败，跑完自动还原源码。六条全过：

| 改回旧写法 | 如期失败的用例 |
|---|---|
| 删掉 `wechat.py` 的 `iter_blocks` 导入 | `test_bundled_samples_import_through_their_own_adapter` |
| `_resolve_map` 拿候选表当实际列名 | `test_column_names_are_matched_against_the_real_columns` |
| `_pick` 直接取 `probes[0]` | `test_nothing_matches_falls_back_to_the_generic_parser` |
| `_guess_paste_suffix` 一律返回 `.txt` | `test_column_names_are_matched_against_the_real_columns` |
| `import_file` 忽略用户声明的 `platform` | `test_declaring_the_source_beats_the_adapter_guess` |
| `kept` 改成「模型也想改时才列入」 | `test_refine_still_reports_a_draft_field_the_model_said_nothing_about` |

**反证过程本身带来两个收获**（这才是它真正的价值）：

1. 「`kept` 只在模型也想改时才列出来」这条改动**本来没有任何测试盯着** ——
   旧测试用的是 Mock 引擎，而 Mock 会把全部字段都填满，所以新旧写法都能过。
   为此专门加了一个「没有证据的字段就不写」的模型桩，才把这件事钉住。
2. 第一次写的反证脚本里，「`_resolve_map`」那条改动**不够忠实**
   （改成了另一种坏法，恰好被别的修复兜住了），于是它「通过」了 ——
   说明**反证本身也要被怀疑**。

### 6.3 端到端冒烟（真实 HTTP，临时数据目录）

用临时服务器把 0.5.0 的整套新能力走了一遍真实 HTTP，全部通过。
最后几条结果（实测输出）：

```text
OK  导入「其他聊天」记录（粘贴文本那条路） —— {'chat_id': 'other-小鹿-4bcbeb', 'adapter': 'wechat',
     'parsed': 3, 'inserted': 3, 'platform': 'other', 'channel': 'other'}
OK  导入后没有冒出第二个同名对象 —— ['小鹿']
OK  导入的记录挂在手建的那个对象名下 —— p_bfd674543248 vs p_bfd674543248
OK  refine 保留了全部手写字段 —— kept=['goal', 'my_style', 'stage', 'taboos']
OK  refine 没把保留项算进 updated —— updated=['peer_profile']
OK  手写的目标没被改写 —— 想约她周末去看展
OK  半自动采集接受 client=other —— 200
OK  半自动采集拒绝名单外的 client —— 404（可选：qq、wechat、wechat3、other）
```

注意第一行：**适配器嗅探出的是 `wechat`**（文本排布像微信），
但用户声明了 `platform=other`，最终 `channel=other`、`chat_id` 前缀也是 `other` ——
这正是 3.4 节要解决的问题，端到端验证了它确实生效。

### 6.4 `symtable` 静态守卫

针对「用了没定义的名字」这一类（编译期/导入期都不报，只在执行到那行时炸）：

```python
def _undefined_globals(py: Path) -> set[str]:
    top = symtable.symtable(src, str(py), "exec")
    known = {s.get_name() for s in top.get_symbols()
             if s.is_assigned() or s.is_imported() or s.is_namespace()}
    ...
    # 找 is_global() 且被引用、但本模块既没赋值也没导入、又不是内置名的符号
```

Python 自己已经算出了这个事实，我们只是把它问出来。
**带 `import *` 的文件跳过**（星号导入会让符号表失真）。

---

## 七、发版

```text
仓库 whyao56/WingMan · tag v0.5.0 · 版本 0.5.0
221 个文件 -> WingMan-0.5.0-win64.zip  33.8 MB
SHA256 d96894fe2a41eb4091357c6938ebe87a84cbe0082f790c3ce698aadc93d0b184
```

- **校验和连跑三次一致**（`make_release.py --check` ×3），所以这个值是可核对的事实。
  注意：**zip 打包那步是确定的，PyInstaller 构建不是逐字节确定的** ——
  发行说明里印的校验和只能用来核对**下载**，不能用来核对**构建**。
- 打包版自报版本实测：`[OK] 运行环境：WingMan v0.5.0 · 打包版（exe） · Python 3.13.14 · Windows 11`。
- Release 页面与附件下载均实测 200。
- 提交链：`7f69240`（v0.4.0）→ `318dba6`（v0.5.0），CI 双矩阵全绿。

### 同步更新的文档

`CHANGELOG.md`（0.5.0 节）、`README.md`（版本行 + 下载链接 + 顶部提示）、
`docs/QUICKSTART.md`、`docs/TROUBLESHOOTING.md`（新增第 14 节，5 个问答）、
`docs/STATUS.md`（新增 §10.4「三个静默问题」与 §13）、`docs/ROADMAP.md`、
`docs/releases/v0.5.0.md`。

---

## 八、这一版**没有**做的

1. **自动采集取密钥在本机依然跑不通**，这不是这一版能修的：本机实测（QQ NT
   9.9.20.37051 / 微信 4.1.13.12）按 SQLCipher 规格穷举 8378 万候选未命中，
   十六进制候选 QQ 8 个全灭、微信 0 处。所以**半自动那条路仍是当下确定能跑通的通道**。
2. **`_pick` 兜底 `generic` 是一次有代价的取舍**：它能给出最能指路的失败提示，
   代价是极端情况下（某个适配器的 `sniff` 退化成 0 分而它本来能解析）会少一点容错。
   若将来出现这种退化，先修 `sniff`。
3. **粘贴 CSV 的判定依赖「首行 ≥2 列且列数一致或含已知列名」**。
   粘贴「完全自定义列名 + 只有一行数据」的表时可能退回 `.txt` 而读不出来 ——
   此时改走「导入文件」即可（那条路带真正的扩展名）。
4. **导出仍未覆盖 `engine_runs` / `activity_log`**（隐私要求只做了一半）。
5. `delete_person` 删对象级人物设定、但**不删**对象级事实（假设：事实属不可再生记忆资产）。
6. 仓库级「删库重建」的隐私清理未走完（旧 SHA 仍可被 GitHub 缓存视图取到；
   **注意现在删库会连带删掉已发布的 Release**）。
7. **Prompt 调优仍是最大的质量缺口** —— 默认 Mock 引擎让整条链路能跑，但建议内容是空的。
