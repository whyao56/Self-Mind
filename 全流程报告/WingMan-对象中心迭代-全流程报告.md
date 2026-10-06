# WingMan 对象中心迭代 · 全流程报告（v0.4.0）

> **交付日期**：2026-10-06
> **仓库**：<https://github.com/whyao56/WingMan>
> **Release**：<https://github.com/whyao56/WingMan/releases/tag/v0.4.0>
> **产物**：`WingMan-0.4.0-win64.zip`（221 个文件，33.8 MB，解压后约 77 MB）
> **SHA256**：`bb63f93b666fd9babcd6283ecc3326deaec9a5a61480976731a5af3a02c23657`
> **测试**：208 passed + 1 skipped（19 个测试文件）
> **起点**：`1e73d01`（v0.3.1）→ **规模**：27 个文件，+5804 / −593 行
>
> 本文自包含：所有关键结论都带根因与代码要点，不需要外部附件。

---

## 一、这一版在解决什么

旧版的数据模型没问题（`persons` 表早就有），**问题在界面的组织方式**：

一级导航是**按功能的来源**分的，不是按用户的意图分的：

```
指挥台 · 记忆 · 导入 · 采集 · 通话（敬请期待）· 自检 · 设置
```

要「导一段记录」得先自己想清楚「这算导入还是采集」；想「看看对她的了解」得知道那叫「记忆」；
而「通话」占着一个一级位置却什么都不能做。

同时，**同一个人不止一个会话**这件事没有被表达出来。一个人在微信、QQ、换过昵称的老号上都留下
记录时，旧版里它们是三个并列的「会话」，各有一份人物设定、各记各的事实。用户会不自觉地做这些事：

- 在微信那个会话里说过「她不喜欢被叫宝贝」，在 QQ 那个会话里又踩一次；
- 想整体看「她最近的状态」，得自己把两个会话的建议来回翻。

**这一版把「对象」提为第一层，会话降为「渠道」（第二层）。**

---

## 二、需求对照表（逐条落点）

| # | 需求 | 落点 | 状态 |
|---|---|---|---|
| 1 | 「对象」取代「会话」为中心；记忆的（会话信息/人物设定/已记住的事实）整合进对象；聊天记录支持二次编辑（删/增/改）与批量操作 | 左栏两级 + 对象页 5 Tab；`#ob-chat` 的批量选择/改角色/改时间/改发送者/手动加一条 | ✅ |
| 2 | 自行优化「导入」，并把优化后的导入整合进「采集」 | 采集页第 3 块 = 原导入页；新增拖放区 + 多文件（逐个导入，失败不拖垮后续） | ✅ |
| 3 | 自行优化「采集」；**半自动不要用抓取时刻，要记消息当时的回复时刻** | `ts_source` 五种来源；默认由 `assumed` 改为 `inferred`（按会话时间线推定） | ✅ |
| 4 | 「自检」整合到「设置」 | `#set-selfcheck` 移入设置页，8 项体检一字未改 | ✅ |
| 5 | 「设置」加「关于」，含「检查更新」「项目地址」等 | `#set-about`：版本 / 检查更新 / 项目地址 / 更新日志 / 许可证 | ✅ |
| 6 | 「通话」功能直接移除，放到「关于」里 | `#about-voice` 折叠区；不再占一级导航 | ✅ |
| 7 | 会话右键「会话设置」改名「设置」，且能改设置（选微信 / QQ） | `openChatMenu` 的「设置…」项 → `openChatSettingsDialog`，可改平台与称呼 | ✅ |
| 8 | 指挥台先选「对象」，再打勾单选/多选该对象的「会话」 | `#cp-persons` → `#cp-channels`；`state.cpChatIds` 有序（第 1 个是主渠道） | ✅ |
| 9 | 右上角 × 弹出小窗：「关闭程序」/「关闭弹窗（后台运行）」 | `POST /api/desktop/close` + `openCloseDialog` | ✅ |
| 10 | 功能间要有联动、去冗余（自行优化） | 导航 7→4；旧深链接重定向；失效选择自动清洗 | ✅ |
| 11 | 历史功能做好：指挥台输出要有历史留存，对应功能也要留存 | `engine_runs` / `sim_runs` / `activity_log`；对象页「历史」Tab 可回看/展开/删除 | ✅ |
| Bug 1 | 半自动第二次建数据集后点「开始监听」报 `AttributeError: 'PersonChannel' object has no attribute 'peer_name'` | `PersonChannel` 补 `peer_name`/`me_name` | ✅ |
| 外设 1 | 把「自检」的提醒信息放到侧边栏 | `#side-warn` + `renderSideWarn()`；全绿时整条隐藏 | ✅ |

### 附带说明

**「怎么找到密钥」这一条是「说清楚」而不是「能实现」。**
自动采集取密钥在本机实测走不通（QQ NT 9.9.20.37051 / 微信 4.1.13.12：按 SQLCipher 规格
穷举 8378 万候选未命中；十六进制候选 QQ 8 个全灭、微信 0 处）。界面重写了这一步的指引，
把「密钥在哪、为什么可能在、也可能不在、取不到时走哪条路」讲清楚，
**半自动仍是当下确定能跑通的通道**。

---

## 三、四个关键设计决策

### 3.1 时间语义：从「抓取时刻」改为「消息自己的时刻」（需求 3）

这是用户明确提出的一点：**复制一段上周的聊天记录，记成今天是没有意义的。**

现在时间来源分 5 类，每条消息都会标注，界面上可点开看解释：

| `ts_source` | 含义 |
|---|---|
| `clipboard` | 复制出来的文本自己带了年月日（最可信） |
| `relative` | 文本里是「昨天 21:03」这类相对时间，按复制那一刻往前推 |
| `inferred` | 完全没带时间，按该会话时间线推定（**新的默认**） |
| `assumed` | 旧的「抓取时刻」，**仅用于兼容已存在的数据** |
| `manual` | 用户手填 |

`inferred` 的算法：锚点取该会话库里**最后一条消息的时刻**，逐秒递增，
且**绝不越过复制时刻**（消息不可能来自未来）。

相对时间解析有两处刻意收紧，都是被真实文本打脸之后加的：

```python
# 1) 裸钟点只在「紧跟称呼之后」才认 —— 否则正文里的比分 3:1 会被当成时间
def _parse_ts(text, *, allow_bare_clock=False, now=None) -> ...

# 2) 算出来的时刻晚于当下就回退一天 —— 「21:03」在上午复制，指的是昨天晚上
```

> **为什么把这件事看得很重**：真时间轴上混进假时间，「她平时几点找我说话」这类结论
> 就是错的。而这个错误**不会报错**，只会安静地给出错误结论。

### 3.2 多渠道上下文合并（需求 8 的后端支撑）

`build_context(ctx, chat_ids, ...)` 现在接受一组渠道，`chat_ids[0]` 是**主渠道**：

- **人格 / 昵称 / 检索锚点**取自主渠道，**新消息也写进主渠道**；
- **事实**：对象级 + 该对象名下全部渠道级事实合并成一个视野，各带 `scope` 标注，
  **只合并视野、不做去重**；
- **摘要**：跨渠道按 `period` 排序取前 N；
- **近期消息**：跨渠道合并后**按 `ts` 归并**取尾部 N 条；
- **检索**：**逐渠道**做（`per_chat_k = max(5, top_k // len(ids))`），结果统一按 `score` 排序再截断。

最后一条是刻意的：如果合并成一个池子再检索，
**话多的那个渠道会把话少的整个盖掉** —— 而用户勾上第二个渠道，恰恰是因为那里有独有信息。

**单渠道的旧路径完全保留**，老用法不受影响。

### 3.3 事实的合并展示规则：分组、分别计数、不去重

对象页「记忆」Tab 里，事实按 **对象级** 与 **渠道级** 两组显示、**分别计数**。

这是**已定的**规则，也写在界面文案里。理由：同一条事实在两个视野里各出现一次是正常的 ——

- 对象级那条是「跨渠道成立」的判断；
- 渠道级那条是「在这段对话里说过」的记录。

合并掉就丢掉了**来源**，而来源恰恰是用户判断「这条可不可信」的依据。

### 3.4 「检查更新」：查不到就说不知道

```python
except Exception as exc:
    return {
        "ok": False, "current": __version__,
        "hint": "没查到不等于已是最新 —— 可能是断网、代理或 GitHub 访问不了。"
                "可以直接打开项目地址自己看一眼。",
        "repo": REPO_URL,
    }
```

**关键点是查不到时不给 `has_update` 字段。** 把「没查到」和「查到了、没有新版本」
合并成一句「已是最新」，是在替用户做一个他没法复核的结论。
这是 v0.3.1 那个 `Failed to fetch` 留下的教训。

---

## 四、修掉的三个 bug

### 4.1 Bug 1（用户报的）：半自动采集第二次选中就崩

```
AttributeError: 'PersonChannel' object has no attribute 'peer_name'
```

**根因**：`schemas.PersonChannel` 少了 `peer_name` / `me_name` 两个字段，
而 `semi._resolve_names` 读了两处。

**为什么看起来是「随机」的**：第一次跑时走的路径没碰到这两行，第二次才暴露。

**修法**（比「只改调用点」更稳）：字段补进 `PersonChannel`（**只加不删**，前端在用的响应模型
加字段是兼容的），并在 `store.person_detail` 里从 `ChatInfo` 填进去 ——
这样「渠道视图缺字段」这一类坑一次性消掉。

**守卫**：`test_collect_semi.py::test_start_works_when_the_person_already_has_a_channel`
**真的调 `start()`**（旧测试只调到内部函数，正好绕过了出事的那一段），
且**实测在旧代码上会复现原始 AttributeError**。

### 4.2 P0（本轮改版自己引入的）：`loadChats` 被调用但已不存在

重构把 `loadChats` 并进了 `loadObjects`（HEAD 里原本定义在 1372 行、被调用 11 次），
**但漏改了 5 个调用点**。

它本来是个编译期错误，但**单文件 HTML、无构建步骤，没有编译器帮忙**，
于是它一路来到了测试面前 —— 而那一轮全量测试是绿的。

实际后果**比「一个小按钮失效」严重得多**，两条路径表现完全不同：

| 调用点 | 后果 |
|---|---|
| `init()` 里那一次 | 抛 `ReferenceError` → 后面的**读设置、自检、深链接跳转全都不执行** |
| 指挥台分析成功后那一次 | 它在 `try` 里 → 异常被 `catch` 接住 → **刚渲染出的分析结果被覆盖成一句错误提示** |

第二条最坑：用户看到的是「分析坏了」，而真正的问题在刷新列表那一步；
`renderBundle()` 明明成功了，`catch` 却把它的成果擦掉。
**一个 `try` 包得太宽，会把「成功的结果」和「收尾时的失败」搅在一起。**

**修法两层**：① 改掉 5 个调用点；② 补上一条**会失败的测试**：

```python
def test_no_calls_to_undefined_functions(html: str) -> None:
    """脚本里调用的每个名字，最终都要有人定义它。"""
    script = html[html.index("<script>"):]
    called  = _called_function_names(script)     # 抠出所有 `名字(`
    defined = _defined_function_names(script)    # 函数声明 / var-let-const / for-of / 参数与解构
    unknown = sorted(n for n in called
                     if n not in defined and n not in _JS_KEYWORDS
                     and n not in _BROWSER_GLOBALS and n not in _CSS_FUNCS)
    assert not unknown, f"这些函数被调用了但没人定义：{unknown}"
```

减法里那三张表不是偷懒：关键字与浏览器内置对象天然不需要在本文件定义；
`_CSS_FUNCS` 是因为**模板串里的内联样式会长得像 JS 调用** ——
`style="width:min(680px,100%)"` 会带出 `min()`。这条只能显式排除，并写清楚为什么。

**这条守卫经过反证**：把调用点还原成修复前的写法，它会失败。

### 4.3 新功能自己带出来的：「后台运行」变成单向门

给窗口 × 加了「关闭弹窗（后台运行）」之后，问题变成：**怎么把窗口找回来？**

最自然的写法是「再双击一次 `WingMan.exe` 就再开一个窗口」——
代码里本来就有单实例检测 `_probe_wingman`，看起来天衣无缝。**但这个窗口是个空壳：**

- 服务在**第一个**进程里，第二个进程只负责渲染那个窗口；
- 页面上的请求全都打到老进程的服务上；
- 于是在新窗口里点「关闭程序」→ 请求发到老进程 → 老进程退出并销毁**它自己的**窗口 →
  新窗口变成一具对着死服务的躯壳，而**第二个进程还挂在那儿**。

用户看到的是「点了关闭程序，窗口还在」。

**修法**：第二次双击走 `POST /api/desktop/show`，由老进程执行 `window.show()`。

```python
def _ask_running_instance_to_show(port: int) -> bool:
    """请**已经在跑的那个实例**把它自己的窗口显示出来。

    为什么不是「在这里再开一个窗口」：服务只在一个进程里。第二个进程开出来的
    窗口只是一个空壳 —— 「关闭程序」关掉的是新壳，老进程连服务带窗口继续活着。
    """
```

`show()` 失败时（浏览器模式、老版本不认识这个接口）**如实返回 `shown=false`**，
调用方再退回「新开一个窗口」—— 这条路只有真的没有窗口可显示时才会走到。

> 教训：**多进程 + 单服务的组合里，「谁持有状态」比「谁能画出界面」重要得多。**
> 凡是出现「壳与本体分离」的可能，都要先问一句：**这个动作作用到哪个进程上了？**

---

## 五、验证记录（不是「测试通过」，是真跑）

### 5.1 单元/回归

```
cd backend && ./.venv/Scripts/python.exe -m pytest tests/ -q
→ 208 passed, 1 skipped（42 秒，19 个测试文件）
```

新增/扩写的守卫：

| 文件 | 项数 | 盯住什么 |
|---|---|---|
| `test_objects_center.py` | 20（新） | 多渠道合并 / 主渠道 / 单渠道兼容 / 空渠道报错 / `/persons/{id}/suggest` 四类路径 / 桌面壳关窗状态机 / `/desktop/show` 三条分支 / 检查更新 |
| `test_frontend_assets.py` | 9（+4） | 单文件前端的静态守卫：死链 `goView` 目标、旧深链接重定向、`$("#id")` 有没有人创建、**调用了没定义的函数** |
| `test_collect_clipboard.py` | 16（+5） | 相对时间解析（裸钟点不误判 / 昨天前天周三 / 下午上午晚上 / 未来回退一天 / `3:1` 不算时间） |
| `test_collect_semi.py` | 22（改 2） | 「缺时间」的断言从 `assumed` 改成 `inferred`（**实测旧行为会让它们失败**） |

### 5.2 真实服务端端到端

起服务（`uvicorn app.main:app --port 8877`），用 `curl --noproxy '*'` 实打：

```
health          http=200  version=0.4.0
desktop/state   http=200  {"native_window":false,"pending_close":false,"platform":"win32"}
desktop/show    http=200  {"ok":true,"shown":false,"hint":"当前没有原生窗口（浏览器模式）…"}
persons/{id}/suggest  http=200  run_id=5  chat_ids=['qq-小鹿-6cd819']  建议数=4
persons/{id}/history  http=200  runs=5    最新一条 chat_ids=['qq-小鹿-6cd819']
update/check    http=200  current=0.4.0  latest=0.3.1  has_update=False
```

`update/check` 的结果是**正确的**：本机已是 0.4.0，而 GitHub 上当时的最新发布还是 0.3.1。

`_ask_running_instance_to_show` 的三条分支也单独验过（有服务无窗口 / 端口没人听 /
端口通但不是我们），**都正确返回 False**，让调用方安全回退。

### 5.3 打包产物

```
dist/WingMan/WingMan.exe --check
→ 结论：全部就绪，可以直接用了。
   [OK] 运行环境：WingMan v0.4.0 · 打包版（exe） · Python 3.13.14 · Windows 11
```

**这一次运行还顺带实证了迁移**（在真实的老数据目录上）：

```
facts 表已升级：加列 person_id，chat_id 放开为可空（支持对象级事实）
messages 已加列：captured_at（历史数据留空，不编造采集时刻）
已为 7 条事实回填 person_id
```

### 5.4 发行包的确定性

```
bb63f93b666fd9babcd6283ecc3326deaec9a5a61480976731a5af3a02c23657  WingMan-0.4.0-win64.zip
```

同一份 `dist/` **连打两次 SHA 相同**（已实测）——
所以这个值可以用来核对**下载**。但**不能**用来核对**构建**：
PyInstaller 的构建不是逐字节确定的（同一份源码连构建两次，221 个文件里有 2 个不同），
自己重跑一遍构建得到不同 SHA 是正常的。这个口径差别写在发行说明里。

---

## 六、文件改动清单

### 后端

| 文件 | 改了什么 |
|---|---|
| `app/__init__.py` | `__version__` 0.3.1 → 0.4.0 |
| `app/engine/context.py` | `ContextPack.chat_ids`；`_as_ids()` / `self_chat_name()`；`build_context` 接受一组渠道 |
| `app/engine/pipeline.py` | `run_analysis(ctx, chat_ids, ...)`；`trace["chat_ids"]`；`save_run(chat_ids=...)` |
| `app/api/routes_engine.py` | 新增 `POST /persons/{id}/suggest`（四类错误路径都覆盖） |
| `app/api/routes_admin.py` | 新增 `/desktop/state`、`/desktop/close`、`/desktop/show`、`/update/check` |
| `app/desktop.py` | `_CLOSE` 状态机、`_on_closing()`、`close_action()`、`show_window()`、`_ask_running_instance_to_show()` |
| `app/collect/clipboard.py` | `_parse_relative_ts()`；`_parse_ts` 返回 5 元组（多 `source`）；`allow_bare_clock` |
| `app/collect/semi.py` | `_infer_iso()`、`_timeline_anchor()`；缺时间默认 `inferred` |
| `app/api/routes_collect.py` | `semi_start` 默认 `missing_time="inferred"` |

### 前端（`frontend/index.html`，2787 → 4042 行）

导航收敛为 4 项；左栏两级；对象页 5 Tab；指挥台对象+渠道多选；
采集页并入导入（拖放 + 多文件）；设置页并入体检与「关于」；侧栏自检提醒；
右上角 × 的关闭小窗；`LEGACY_VIEW` 旧深链接重定向。

### 测试

新增 `tests/test_objects_center.py`（20 项）；
`test_frontend_assets.py` +4；`test_collect_clipboard.py` +5；`test_collect_semi.py` 改 2。

### 文档

`CHANGELOG.md`（0.4.0 条目）、`README.md`（导航/版本/时间语义/两条新踩坑）、
`docs/STATUS.md`（§4 前端结构整节重写、§5.3 时间语义、§11/§12 版本与迭代记录）、
`docs/QUICKSTART.md`、`docs/TROUBLESHOOTING.md`（§12.5 改写 + 新增 §13 界面变化）、
`docs/ROADMAP.md`（1.1/1.2/1.3/1.4 勾掉已完成的）、
`docs/releases/v0.4.0.md`（新）。

---

## 七、遗留问题（明确没做的）

1. **自动采集取密钥在本机仍跑不通** —— 这不是这一版能修的（实测数据见上）。
   这一版改的是「取不到时，程序多快、多如实地说出来」。
2. **导出不覆盖分析留存**。`export_chat_json` 目前只导出消息/事实/画像，
   不含 `engine_runs` / `activity_log`。需求 11 的隐私要求是「导出/删除要覆盖历史输出」，
   目前只做到「历史 Tab 里能删单条 run」。
3. **跨渠道时间线接口前端仍未使用**（`routes_persons.py`），对象页概览走的是对象 overview。
4. **`delete_person` 删除对象级人物设定、但不删对象级事实**（假设：事实属不可再生记忆资产，
   与「删人不删消息」一致）。如需一起删，需要明确。
5. **仓库级「删库重建」的隐私清理未走完**。曾用 `git-filter-repo` 重写历史清掉真人姓名，
   旧 SHA 仍能被 GitHub 缓存视图取到；彻底清除需删库或联系 Support。
   **注意：现在删库会连带删掉已发布的 Release。**
6. **Prompt 调优仍是最大的质量缺口**。默认 Mock 引擎让整条链路能跑，但建议内容是空的。

---

## 八、可复用的经验

1. **守卫必须先在旧代码上失败过。** 不会失败的断言只是一条好看的注释。
   这一轮新增的每条关键守卫（`loadChats`、`inferred`、真 `start()`）都做过这个反证。
2. **「删除/重命名」是跨文件改动，而测试只记得「现有断言还成立」。**
   单文件、无构建步骤的前端没有编译器兜底，就得自己补静态守卫。
3. **一个 `try` 包得太宽，会把「成功的结果」和「收尾时的失败」搅在一起。**
   指挥台那次就是这个形态：结果渲染成功了，却在 `catch` 里被擦掉。
4. **多进程 + 单服务时，先问「这个动作作用到哪个进程上了」。**
```
