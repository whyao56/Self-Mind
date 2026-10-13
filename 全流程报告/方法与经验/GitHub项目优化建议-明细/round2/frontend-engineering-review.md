---
tags: [领域/方法, 类型/报告, 轮次/2, 维度/前端工程质量]
评审日期: 2026-10-13
评审对象: whyao56 · WingMan（frontend/index.html 4653 行）、Etude（backend/frontend/index.html 4519 行）
评审方式: 纯静态阅读（Read / Grep / rg / Python 正则解析），未运行、未安装依赖、未改任何文件
---

# 第二轮评审 · 前端工程质量

> **本报告的角度声明**：第一轮已经给出「单文件要不要拆、怎么拆」的判断（结论：零构建是可接受取舍，渐进抽取，不要一步上打包器）。本轮**不重复该判断**，转而做第一轮完全没做的、**前端工程本身的质量体检**——单文件内部结构、XSS 汇点、a11y、状态呈现、i18n、响应式、CSP 与资源、首屏性能。
>
> **所有行号均为实际读到的位置**；统计类结论在括号里给出统计方法（命令 + 命中数）。无法确认的集中在第 5 节。

---

## 0. 一页结论（最该做的 3 件事）

**一句话**：这两个前端**不是「代码写得烂」，而是「没有安全网」**——WingMan 用 85 个 `innerHTML` 汇点 + 256 次手工 `esc()` 维持着一条靠自觉的安全线，Etude 则干脆一个 `innerHTML` 都不用；两者的静态守卫（WingMan 藏在 pytest、Etude 藏在 `check_js.py`）都**只防「写错名字」，不防「忘了转义」**；两个前端的可访问性几乎为零（0 个 `aria-live`、配色对比度全线低于 WCAG AA）。

| 维度 | WingMan | Etude | 谁更好 |
|---|---|---|---|
| 单文件内部结构 | style 539 / body 706 / script 3399 行；**114 个全局函数**、4 个顶层 `let/var`、**无 module/IIFE 命名空间** | style 642 / body **仅 32 行** / script 3823 行；**140 个全局函数**、4 个顶层 `let/var` | 各有问题（都是"大全局作用域"），Etude 的 body 更薄 |
| XSS 汇点 | **`innerHTML` 85 次**（`grep -c`） | **`innerHTML` 0 次**（全走 `el()`+`textContent`） | **Etude 明显更稳** |
| XSS 守卫 | 仅 `vm.Script` **语法编译**（`ci.yml:67-80`），无转义守卫 | 有转义守卫，但**软警告不 fail**（`ci.yml:103-110`） | 都不合格 |
| 前端静态守卫 | **强**：`test_frontend_assets.py` 293 行 / 8 条守卫，跑在 CI | 中：`check_js.py` 367 行，只查未定义调用 | **WingMan 更全面** |
| a11y | 90 个按钮 / **0 个 `aria-label`** / aria-* 合计 1 / **0 aria-live** | 7 静态按钮 / aria-* 18 / **0 aria-live** | 都差，Etude 略好 |
| 配色对比度 | `.dim` 用 82 次，**3.10:1**（FAIL） | `--fg-faint` 用在 11.5px 小字，**2.50:1**（FAIL） | **都 FAIL** |
| 主题/动效偏好 | 无暗色、无 `prefers-reduced-motion` | 有 `prefers-color-scheme` + 3 套 `data-theme` + reduced-motion | **Etude 明显更好** |
| 状态呈现 | 空/加载/错误齐全 + 自建模态 | 空/加载/错误齐全，但用原生 `alert`/`confirm` | WingMan 略好 |
| CSP | 无 | 无 | 都不合格 |
| 离线/CDN | 0 CDN、0 外链字体 | 0 CDN、0 外链字体 | **两者都做得对** |

**最该先做的 3 件事**：

1. 🔴 **给 WingMan 的 85 个 `innerHTML` 汇点加一条"非转义即失败"的硬守卫**（P0）→ 见 2.1
   WingMan CI 对前端**只有** `ci.yml:67-80` 的 `vm.Script` 语法编译——它抓得到"写错语法"，抓不到"语义上漏了 `esc()`"，而后者是这里唯一可能的漏洞类型。第一轮说"建议 WingMan 照抄 Etude 的 innerHTML 守卫"——**实测证明照抄不可行**：Etude 的守卫是 `grep innerHTML=` 后排除 `=""`，套到 WingMan 上会把 85 处全部报红。WingMan 需要的是**另一种机制**。
2. 🟠 **修两个前端的"极淡文字"对比度**（P0）→ 见 2.2
   WingMan `--dim` 3.10:1、Etude `--fg-faint` 2.50:1，且 Etude 把它用在 11.5px 的辅助文字上。这是**全部主题、全部场景**的系统性不达标，改色板即可，收益立竿见影。
3. 🟡 **补 `aria-live` 与图标按钮标签**（P0/P1）→ 见 2.3
   两个前端都是"点了之后屏幕阅读器毫无反应"——异步加载、错误、toast 全部静默。WingMan 的 90 个按钮里 0 个有 `aria-label`。

---

## 1. 现状矩阵（WingMan / Etude 对比）

### 1.1 单文件内部结构与规模

| 指标 | WingMan | Etude | 统计方法 |
|---|---|---|---|
| 文件行数 | 4653 | 4519 | `wc -l` |
| 文件体积 | 231,680 B（≈226 KB） | 182,500 B（≈178 KB） | `ls -la` |
| `<head>` 静态区 | 1–6（6 行） | 1–19（19 行，含 12 行设计约定注释） | `grep -n` 标签 |
| `<style>` | 7–545（**539 行**） | 20–661（**642 行**） | `grep -n '<style>\|</style>'` |
| `<body>` 静态 HTML | 547–1252（**706 行**） | 663–694（**仅 32 行**） | `grep -n '<body>\|</body>'` |
| `<script>` | 1253–4651（**3399 行**） | 696–4518（**3823 行**） | `grep -n '<script>\|</script>'` |
| 顶层 `function` | **114** | **140** | `grep -cE '^(async )?function '` |
| 顶层 `const` | 25 | 17 | `grep -cE '^const '` |
| 顶层裸 `let`/`var` | 4 | 4 | `grep -cE '^(let\|var) '` |
| `type="module"` | 0 | 0 | `grep -c` |
| IIFE / 命名空间 | 1（仅 `init()` 自执行） | 0 | `grep -cE '^\s*\(\(' ` |
| `defer` / `async` | 0（靠 `<script>` 置于 body 末尾） | 0（同上） | `grep -cE '<script[^>]*(defer\|async)'` |

**读法**：两个前端都是**同一个大全局作用域**（114 / 140 个全局函数直接挂在 `window` 上），没有模块边界、没有命名空间、没有 `defer`。Etude 的 `<body>` 只有 32 行静态骨架——**整个界面由 JS 用 `el()` 现搭**；WingMan 则有 706 行静态 HTML 打底。这是两种截然不同的架构取向，直接决定了后面 XSS 面的差异。

### 1.2 事件绑定方式

| 指标 | WingMan | Etude |
|---|---|---|
| 内联 `onclick=` | **0** | **0** |
| 其他内联 `onXxx=` | **0** | **0** |
| `addEventListener` | **106** | 19 |
| `$("#id").addEventListener` 直接绑定 | **140** 处（其中**顶层 64 处**：49 处无 `?.`、15 处有 `?.`） | **0** |
| 事件委托 | 部分（`#obj-tabs` 等） | 主要方式（`el(..., {onClick})`） |

两边都**没有用内联事件**——这是很好的习惯（也为将来收紧 CSP 留了余地）。但 WingMan 的 64 处顶层直接绑定里，**49 处用 `$("#id").addEventListener(...)` 而不带 `?.`**（`grep -nE '^\s*\$\("#[a-zA-Z0-9_-]+"\)\.addEventListener'` → 49 命中）。脚本在 body 末尾执行，此刻元素都存在，所以**当前不会炸**；但这意味着**任何一个 id 被重命名，整段初始化的后半部分会因为 `null.addEventListener` 抛出 TypeError 而静默停摆**。这不是新问题——WingMan 自己就写过这个坑（`test_frontend_assets.py:87-102` 的 `test_js_only_references_dom_ids_that_exist` 注释里原话是"用户看到的是「某个按钮点了没反应」，控制台里才有一行错"）。

### 1.3 XSS 面

| 汇点 | WingMan | Etude |
|---|---|---|
| `innerHTML` | **85** | **0** |
| `insertAdjacentHTML` | 0 | 0 |
| `document.write` | 0 | 0 |
| `outerHTML` | 0 | 0 |
| 转义函数 | `esc()` 定义在 `WingMan/frontend/index.html:1260`，调用 **256** 次 | 不需要（`el()` 里走 `textContent` / `createTextNode`） |
| `eval` / `new Function` | 0 / 0 | 0 / 0 |

### 1.4 静态守卫与 lint

| 项目 | 机制 | 规模 | 内容 | 在 CI？ |
|---|---|---|---|---|
| WingMan | `backend/tests/test_frontend_assets.py`（pytest 模块） | 293 行 | 未定义函数调用、`$("#id")` 引用了不存在的 id、重复 CSS 顶层类、跨层平台白名单、版本号守卫 | ✅（走 pytest，CI 在 ubuntu 跑） |
| WingMan | `ci.yml:67-80` 前端 JS **语法**检查 | 12 行 | 用 `new (require('vm').Script)(m[1])` 编译 `<script>` 块——**只能抓语法错，抓不到"漏 `esc()`"** | ✅ |
| Etude | `scripts/check_js.py` | 367 行 | 仅"调用了但没定义的函数" | ✅（`ci.yml:46`） |
| Etude | CI 内联守卫 | 8 行 | `innerHTML` 非空赋值 → `::warning::`（**不 fail**） | ⚠️ 软警告 |
| 两者 | 转义守卫 / eslint / HTML 校验 / a11y 检查 | — | **全无**（`grep -inE 'innerHTML\|XSS' ci.yml` 0 命中；`grep -il eslint` 0） | ❌ |

> **这是本轮一个反直觉的结论**：WingMan 的前端静态守卫**比 Etude 更全面**（8 条 vs 1 条），只是它长在 pytest 里而不是 `scripts/` 下，容易被漏看。但两者都**不检查"拼 HTML 时有没有转义"**——而 WingMan 恰恰是那个有 85 个汇点的项目。

### 1.5 可访问性

| 指标 | WingMan | Etude |
|---|---|---|
| 静态 `<button>` | **90** | 7（其余由 `btn()` 动态生成） |
| `aria-label` | **0** | 0 |
| `aria-*` 合计 | **1**（`aria-modal`） | **18**（`aria-pressed` 13 / `aria-current` 3 / `aria-expanded` 2） |
| `role=` | 4 | 0 |
| `aria-live` | **0** | **0** |
| `tabindex` | 2（自定义 div 按钮） | 0 |
| `<label>` | 33（**全部为包裹式**，`for=` 0） | 动态 `el("label",{class:"field"})`（包裹式） |
| `<img>` / `alt=` | 0 / 0 | 真实 `<img>` 0（唯一命中在注释 `Etude:1088`） |
| `sr-only` / 视觉隐藏类 | 0 | 0 |
| `:focus-visible` 规则 | 3 条（**仅限类**：`.chatitem` `:107`、`.objitem` `:483`、`.chitem` `:497`） | **全局 1 条**（`Etude:120` `:focus-visible{outline:2px solid var(--accent);outline-offset:2px}`） |
| `outline:none` | 0 | 0 |
| `prefers-reduced-motion` | **0** | 2（`Etude:427`、`Etude:617`） |
| `prefers-color-scheme` | **0** | 1（`Etude:60`，含完整暗色变量） |
| 手动主题切换 | 无 | `data-theme="warm\|light\|dark"`（`Etude:72/82/92`） |

### 1.6 状态呈现与降级可见性

| 指标 | WingMan | Etude |
|---|---|---|
| 空态 | `empty-hint` 18 处 | `class:"empty"` 5 处 + "还没有…" 10 处 |
| 加载态 | "加载中…" 9 处 + `.spin` 3 处 | `class:"spin"` 8 处（`Etude:1169/1931/2002/2563/2660/2702/3344`） |
| 错误态 | `.note err` 11 处，`esc(e.message)` 55 处 | `errorBlock()` 定义于 `Etude:810`，调用 10 处 |
| 后端断开 | `WingMan:1763` → 显示"后端未连接" | `Etude:4502` → 显示"连不上后端" |
| 用了哪个模型 | `WingMan:2457` trace 显示 `${trace.llm}`；`WingMan:1751-1752` health 里 provider pill | `Etude:4488` badge 显示 `health.mode` |
| 原生 `alert()` | 7 | 12 |
| 原生 `confirm()` | 0（自建 `openModal` `:1382` + `confirmWithCountdown` `:1426`） | 6（`Etude:1963/1973/2216/2766/3463/4237`） |
| `aria-live`（供屏读播报） | **0** | **0** |

### 1.7 资源、CSP 与缓存

| 指标 | WingMan | Etude |
|---|---|---|
| CSP meta | **无**（`grep -ci 'Content-Security-Policy'` → 0） | **无** |
| 内联 `<script>` | 有（必须，CSP 收紧的障碍） | 有 |
| 外部 CDN / `<link>` / `@import` | 0 / 0 / 0 | 0 / 0 / 0 |
| `@font-face` / 外部字体 | 0（走 `system-ui` 栈，`WingMan:7` 后首个 `font-family`） | 0（`--sans:system-ui,…`，`Etude:55`） |
| 图片 base64 内联 | 0（`data:image` 0 命中） | 0 |
| `target="_blank"` / `rel="noopener"` | 6 / **6（全带上）** | 0 / — |
| HTML 缓存策略 | `WingMan/backend/app/main.py:148-182` `NoStoreHtmlMiddleware` → `Cache-Control: no-store` | `Etude/backend/app/api.py:843-858` `_NO_STORE` |
| 静态资源缓存 | 无 long-cache（只有一个 HTML） | 音频/图片 `max-age=31536000`（`Etude/backend/app/api.py:602/623`） |
| `localStorage` | 2（仅 wizard dismissed，`WingMan:3739/3806`） | 9（主题/字号/密度/侧栏，`Etude:4432-4453`） |
| 是否把密钥写进前端存储 | **否** | **否** |

### 1.8 首屏性能

- **无阻塞渲染的外部请求**：两文件均无 `<link rel=stylesheet>`、无外部 `<script src>`、无 `@import`、无 `@font-face`——首屏只需要一次本地 HTTP 读文件。
- **`<script>` 位于 `</body>` 之前**（WingMan `1253`、Etude `696`），不阻塞首屏解析；因为无外部依赖，也**不需要 `defer`**。
- **体积**：226 KB / 178 KB 单文件，本地磁盘读取，无网络往返。这是"本地优先单文件前端"的正确形态。
- **无 `<canvas>`、无 `devicePixelRatio`、无 `ResizeObserver`**——不存在高 DPI / 尺寸自适应的隐式开销，但反过来说**也没有为高 DPI 做任何处理**（当前无图形元素，暂不构成问题）。

---

## 2. 逐条发现（按 P0 → P2 排序）

### 2.1 【P0 · 2 人日】WingMan：85 个 `innerHTML` 汇点，只靠"人自觉转义"，CI 零守卫

**现象 + 证据**

- WingMan 有 **85 处 `innerHTML` 赋值**（`grep -c 'innerHTML' WingMan/frontend/index.html` → 85），其中 30+ 处是**把后端/AI 返回内容拼成 HTML 模板串**：
  - `WingMan:2342-2381` `analysisHTML()`——把 AI 分析的 `emotion` / `intent` / `subtext` / `signals` / `topics` 拼进 HTML；
  - `WingMan:2494-2521` `simHTML()`——把 AI 推演的分支 `label` / `s.text` / `note` / `outcome` / `advice` 拼进 HTML；
  - `WingMan:2398-2422` `optionHTML()`——把 AI 生成的候选回复 `o.text` 拼进 `data-text="${esc(o.text)}"` 与 `<div class="opttext">`；
  - `WingMan:4333-4373` `capHtml()`——把剪贴板抓来的文本 `it.text` 拼进 HTML。
- 目前**确实都走了 `esc()`**（`esc` 定义在 `WingMan:1260`，全文件调用 256 次）。我用正则解析器逐块抽出 `innerHTML = \`…\`` 模板后枚举 `${…}` 插值并筛掉含 `esc(` 的，剩余全是**数字或常量**（`${ins}` / `${skp}` / `${runs.length}` / `${Math.round(...)}`），以及内部**已用 `esc()` 构造好**的 `runsHtml` / `actsHtml`（`WingMan:3246-3269`）。**本轮没有找到一处当前可触发的未转义注入**（与安全维度 sec-supply 独立复核的结论一致，见 P1-S8）。
- **但系统性风险在于"没有安全网"——CI 存在感与防护力错位**：WingMan CI 对前端**只有一个步骤**——`ci.yml:67-80` 的「前端 JS 语法检查」，用 `new (require('vm').Script)(m[1])` 做**语法编译**。`grep -inE 'innerHTML|XSS' WingMan/.github/workflows/ci.yml` → **0 命中**。也就是说，**CI 能发现"写错语法"（`ci.yml` 里看起来有一道前端关卡），却完全发现不了"语义上漏了 `esc()`"**——而后者恰恰是这里唯一可能的漏洞类型。将来任何人新加一处 `innerHTML = \`<div>${x}</div>\``（忘了 `esc`），**语法检查会通过、测试不会拦、review 也未必看得见**。
- 对比：Etude **一个 `innerHTML` 都没有**（85 → 0 的差距），因为它的 `el()`（`Etude:760-782`）只走 `setAttribute` / `textContent` / `createTextNode`，`clear()`（`Etude:784`）走 `removeChild`。这不是"Etude 更小心"，而是**架构上就不存在这个汇点**。同时 Etude 的守卫（`ci.yml:103-110`）只打 `::warning::` **不 fail**——即"该有守卫的项目没有，有守卫的项目守卫是软的"。

**按"数据来源"给 85 处汇点分类（比只数 `innerHTML` 更有用）**

统计 `innerHTML` 数量的价值有限（85 里大半是加载态/空态/静态骨架）。真正该盯的是**渲染不可信数据的模板函数**，按来源分三档：

| 档 | 数据来源 | 渲染函数（证据） | 失守后果 |
|---|---|---|---|
| **A 最高** | **导入的第三方聊天记录**（QQ/微信导出 txt —— 别人写的字） | `previewHTML()` `WingMan:3290-3304`（回显 `m.sender` / `m.text` 前 60 字，调用点 `:3401`）；`capHtml()` `WingMan:4333-4373`（回显剪贴板抓取的 `it.text`）；导入结果表 `:3444-3448` | **stored XSS 的天然入口**：内容先落库、再每次渲染时执行。第三方记录是"用户无法审查的输入" |
| **B 高** | **AI 生成内容**（远端模型 / 受 prompt 注入影响） | `analysisHTML()` `:2342-2381`、`simHTML()` `:2494-2521`、`optionHTML()` `:2398-2422`、`simRunsHTML()` `:3222-3236` | 分析结果被当代码执行；可读 `localStorage` + 打同源 `/api/*`（删会话、改设置） |
| **C 低** | 本机用户自己的输入 / 服务端错误串 | `esc(state.objQuery)` `:1892`、`esc(e.message)` 55 处、`option value` 回填 | 影响面限于"用户自己坑自己" |

> **A 档是这张表里最该单列的一类**，也是本条 2.1 与安全维度 P1-S8 互补的地方：安全维度证明了"当前 A/B 档全都套了 `esc()`"；前端维度要补的是——**A 档的函数是"新字段最容易漏 `esc()`"的地方**（`previewHTML` 只回显 `sender`/`text` 两个字段，将来加"群名""转发来源""@提及"就等于加新的注入点，而它们都在同一个模板里，很容易在改动时漏掉）。所以落地守卫除了"全文件插值检查"，还应就 A 档函数**补一条针对性回归**（见下"改法"第 3 点）。

**为什么是问题**

AI 生成内容与**导入的第三方聊天记录**都是**不可信输入**——前者来自远端模型、受 prompt 注入影响；后者更隐蔽，是"别人写的字进了你的库"，且用户导入时不会逐字审查。这类内容一旦落进 `innerHTML`，等价于"把外部输入当代码执行"。WingMan 的目标用户跑的是**本地桌面程序**，XSS 的影响面虽然是本机，但它可以读 `localStorage`、发同源请求到 `/api/*`（**包括删除会话、改设置**）——对本地工具来说这仍是真实的权限提升。而 85 个汇点全靠 256 次手工 `esc()` 维持，**任一新增点失守就是一个静默漏洞**。

**改法（可执行）**

不能照抄 Etude 的 `grep innerHTML=` 禁令（会把 WingMan 85 处全报红）。给 WingMan 加一条**"每个 `innerHTML` 模板插值必须被 `esc()` 包裹或属于白名单"**的 pytest 守卫，放进它已有的 `test_frontend_assets.py`：

```python
# WingMan/backend/tests/test_frontend_assets.py（追加）
import re

# 允许"裸插值"的白名单：纯数字 / xxx.length / 内部已 esc 的聚合串 / 纯计算
_SAFE_EXPR = re.compile(
    r"^(\d+(\.\d+)?"
    r"|[a-zA-Z_$][\w$]*\.length"
    r"|(runsHtml|actsHtml|warn|saved|head|chans|line|prefs|branches)"
    r"|Math\.round\([^)]*\))$"
)

def _innerhtml_templates(js: str):
    """产出每个 `innerHTML = `...`` 模板串（正确处理模板内嵌套 ${}）。"""
    for m in re.finditer(r"innerHTML\s*=\s*`", js):
        i, nest = m.end(), 0
        while i < len(js):
            if js[i] == "\\":
                i += 2; continue
            if js.startswith("${", i):
                nest += 1; i += 2; continue
            if js[i] == "}" and nest:
                nest -= 1
            elif js[i] == "`" and nest == 0:
                break
            i += 1
        yield js[m.end():i]

def test_every_innerhtml_interpolation_is_escaped(html: str) -> None:
    """innerHTML 模板里的每个 ${...} 插值，必须过 esc() 或在白名单里。

    这个文件有 85 处 innerHTML，AI 生成内容流经其中 10 处以上；转义全靠手写，
    没有编译器、没有 lint 能替我们记住 —— 这条守卫就是那个"记住的人"。
    """
    script = html[html.index("<script>"):]
    bad: list[str] = []
    for tmpl in _innerhtml_templates(script):
        for e in re.finditer(r"\$\{([^{}]*)\}", tmpl):
            expr = e.group(1).strip()
            if "esc(" not in expr and not _SAFE_EXPR.match(expr):
                bad.append(expr)
    assert not bad, f"这些 innerHTML 插值没有转义，确认是否有 AI/用户输入：{sorted(set(bad))}"
```

> 说明：正式实现建议直接复用 Etude `check_js.py` 已写好的「先剥字符串与注释」逻辑（`Etude/scripts/check_js.py`，367 行），借它的解析器、只换最后一步判定规则。**"守卫会自己误报就会被删掉"是 Etude 作者的原话（该文件头注释）——这条守卫必须做到零误报**：白名单要先用现有 85 处跑一遍调稳，再进 CI。安全维度 sec-supply 的 P1-S8 已给出一份等价的 `check_innerhtml.py`（只允许清空赋值或每个插值都套 `esc()`，会 `exit 1`）——**两处不要各写一份，合并成同一个脚本、由两个报告共同指向它**。

**A 档针对性回归**（补在 `check_frontend_assets.py` 里，与全文件守卫互补）——把"渲染第三方导入数据的字段必须转义"钉成显式断言，这样将来给 `previewHTML` 加字段时会立刻变红：

```python
# 渲染第三方聊天记录的模板里，回显的字段必须过 esc()
_IMPORT_RENDER_FIELDS = ("m.sender", "m.text", "x.display_name", "x.note", "it.text", "who")

def test_imported_chat_fields_are_escaped(html: str) -> None:
    """导入的第三方聊天记录是 stored XSS 的天然入口：别人写的字进了你的库。

    这些字段一旦裸插进 innerHTML，就是"先落库、再每次渲染时执行"。
    将来给 previewHTML / capHtml 加「群名 / 转发来源 / @提及」时，
    这条断言会先红，逼你先套 esc()。
    """
    script = html[html.index("<script>"):]
    for field in _IMPORT_RENDER_FIELDS:
        # 允许出现，但每个出现处必须被 esc(...) 包裹
        for m in re.finditer(r"(?<!esc\()" + re.escape(field), script):
            ctx = script[max(0, m.start() - 12): m.end() + 8]
            assert "esc(" in ctx, f"{field} 在未被 esc() 包裹的上下文出现：…{ctx}…"
```

**优先级**：P0
**工作量**：2 人日（1 天写守卫 + 调白名单，1 天补测试与 CI）
**验收标准**：① 新守卫在**当前代码上必须全绿**（证明无既有漏洞、且零误报）；② 手工插入一处 `innerHTML = \`<b>${e.message}</b>\`` 后守卫必须报红；③ 在 `previewHTML` 里加一个裸 `${m.group_name}` 后 A 档回归必须报红；④ 写入 `WingMan/.github/workflows/ci.yml`（**补在 `ci.yml:67-80` 那条语法检查之后**，让"语法"与"转义"两道都有人守），PR 上可见。

---

### 2.2 【P0 · 1 人日】两个前端的"极淡文字"对比度系统性低于 WCAG AA

**现象 + 证据**

我用 WCAG 2.x 相对亮度公式逐对算了两个项目色板里"次要/极淡文字"与底色的对比度（脚本见第 5 节的复现口径）：

| 项目 · 变量 | 前景 / 背景 | 对比度 | 判定 | 用在哪 |
|---|---|---|---|---|
| WingMan `--dim:#8a93a2`（规则 `WingMan:188` `.dim{color:var(--dim)}`） | on `--panel:#ffffff` | **3.10:1** | ❌ FAIL AA | `.dim` 全文件用 **82 次**（`grep -o 'class="[^"]*\bdim\b[^"]*"'`） |
| 同上 | on `--bg:#f4f6f8` | **2.86:1** | ❌ FAIL AA | 表头、时间戳、次要说明 |
| 同上 | on `--panel2:#fafbfc` | **2.99:1** | ❌ FAIL AA | 卡片内次要行 |
| Etude `--fg-faint:#9a9184`（`Etude:48`） | on `--bg:#ebe6dc` | **2.50:1** | ❌ FAIL AA | `.faint` / "还没有…" 辅助文字 |
| 同上 | on `--panel:#f7f4ee` | **2.83:1** | ❌ FAIL AA | 卡片内辅助文字 |
| Etude light 主题 `--fg-faint:#8b93a4`（`Etude:86`） | on `--bg:#f5f6f8` | **2.85:1** | ❌ FAIL AA | — |
| Etude dark 主题 `--fg-faint:#78736c`（`Etude:65/96`） | on `--bg:#191a1c` | **3.70:1** | ❌ FAIL AA | — |
| 同上 | on `--panel:#232528` | **3.27:1** | ❌ FAIL AA | — |
| Etude `--warn:#96701c` | on `--panel:#f7f4ee` | **4.13:1** | ❌ FAIL AA | 警告文字 |
| WingMan `--accent:#2f6fed` | on `--accent-weak:#eef4ff` | **4.12:1** | ❌ FAIL AA | 选中态/高亮底上的强调文字（**待确认**是否真有此组合，见第 5 节第 1 条） |

**对照组（说明这不是"整体不行"，而是"极淡那一档不行"）**：
WingMan `--muted:#596374` on `--bg` = **5.60:1** ✅；`--ok`/`--ok-bg` = 4.86:1 ✅；`--danger`/`--danger-bg` = 4.85:1 ✅；`--peer`/`--peer-bg` = 4.76:1 ✅；`--warn`/`--warn-bg` = 5.22:1 ✅。
Etude `--fg-dim:#6c6558` on `--bg` = **4.64:1** ✅；`--accent`/`--accent-soft` = 4.66:1 ✅；dark `--fg-dim` on `--bg` = **6.38:1** ✅。

**为什么是问题**

失败的不是装饰色，而是**承载信息的文字**：时间戳、条数、适配器名、备注、"还没有…"这类引导语。WCAG 2.1 SC 1.4.3 对**正常字号**要求 ≥ 4.5:1。更要命的是 Etude 把 `--fg-faint` 用在 **11–11.5px** 的小字上（`Etude:138` `.brand span{font-size:11.5px;color:var(--fg-faint)}`、`Etude:163{font-size:11px;color:var(--fg-faint)}`、`Etude:179`）——**字号越小越需要高对比度，这里正好反了**。对 40+ 岁用户、低质量笔记本屏幕、或户外环境下，这些文字实际是"看得见轮廓但读不出内容"。

**改法（可执行）**

只改色板，不动结构。目标是把"极淡"档提到 ≥ 4.5:1（同时保持"比 `--muted`/`--fg-dim` 更淡"的层次）：

```css
/* WingMan/frontend/index.html:27  --dim:#8a93a2(3.10) → */  --dim:#6b7686;   /* on #fff ≈4.62 ✅，仍淡于 --muted:#596374 */

/* Etude/backend/frontend/index.html:48 warm --fg-faint:#9a9184(2.50) → */ --fg-faint:#7e7669;  /* on #ebe6dc ≈4.53 ✅ */
/* Etude:65 / :96 dark  --fg-faint:#78736c(3.27~3.70) → */                 --fg-faint:#8f897f;  /* on #191a1c ≈5.1 ✅ */
/* Etude:86 light       --fg-faint:#8b93a4(2.85) → */                      --fg-faint:#767e8f;  /* on #f5f6f8 ≈4.6 ✅ */
/* Etude:50             --warn:#96701c(4.13) → */                          --warn:#7d5c14;      /* on #f7f4ee ≈5.5 ✅ */
```

**优先级**：P0
**工作量**：1 人日（含用 axe DevTools 或 Lighthouse 复核其余未抽查配色）
**验收标准**：① 上述 5 个变量替换后，`axe` / Lighthouse 的 `color-contrast` 规则**0 违规**；② 目视确认层次感未丢（新旧色差 ΔE 可控）；③ 两个项目的 3 套 Etude 主题都核过。

---

### 2.3 【P0 · 1.5 人日】两个前端都缺 `aria-live`：所有异步状态对屏读用户静默

**现象 + 证据**

- WingMan：`grep -o 'aria-live' → 0`；`role=` 只有 4 处；唯一的 aria 属性是 `aria-modal`（`WingMan:1388`）。
  - 它的状态是**靠改文字**传达的：`toast()`（`WingMan:1332-1337`）直接 `n.textContent = msg`，节点上没有任何 live region 语义；
  - 按钮忙碌态 `busy()`（`WingMan:1339-1350`）把按钮 `innerHTML` 换成 `<span class="spin"></span> 处理中…`，屏幕阅读器不会主动播报；
  - 秒级进度 `busyClock()`（`WingMan:1354-1362`）每 1 秒重写一次按钮文本——**即使加了 `aria-live`，每秒一次的重写也会把屏读淹没**，这是设计层面要一起考虑的点。
- Etude：`grep -o 'aria-live' → 0`；`errorBlock()`（`Etude:810`）渲染错误块时同样没有 live 语义；加载态是 `class:"spin"`（8 处）。
- 两项目共有的后果：**"点了 → 屏幕阅读器一片安静 → 用户不知道在跑、跑完了、还是失败了"**。

**为什么是问题**

这是 a11y 里"投入产出比最高"的一条：只需在容器上加 `role="status"` / `aria-live="polite"`，就能把**已经存在的**文字更新变成可感知事件。缺了它，前面所有"空态/加载态/错误态做得很全"的努力对屏读用户等于零——**状态存在、但不可感知**。

**改法（可执行）**

```html
<!-- WingMan：给已有状态容器加 live 语义（#imp-msg / #op-msg / #s-msg …） -->
<div id="imp-msg" class="small" role="status" aria-live="polite"></div>
<div id="s-msg"  class="small" role="alert" aria-live="assertive"></div>  <!-- 仅错误用 assertive -->
```
```js
// WingMan:1339 busy()：新增一个全局 live 节点，把"长任务"状态播报一次（不每秒播）
function announce(msg) {
  let live = document.getElementById("a11y-live");
  if (!live) {
    live = document.createElement("div");
    Object.assign(live, { id: "a11y-live", className: "sr-only" });
    live.setAttribute("role", "status");
    live.setAttribute("aria-live", "polite");
    document.body.appendChild(live);
  }
  live.textContent = msg;
}
// busy() 的 on 分支里：b.innerHTML = `<span class="spin" aria-hidden="true"></span> ${esc(label||"处理中…")}`;
//                     announce(label || "处理中");      ← 新增这一行即可
```
```css
/* 两项目都缺这个工具类（grep sr-only/visually-hidden → 0） */
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;
  overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
```
> `busyClock()` 的每秒文本重写建议**不挂 live region**（只做视觉），否则屏读会被秒级播报刷屏——这条要在验收时专门确认。

**优先级**：P0
**工作量**：1.5 人日（两项目各 0.75 天，含补 `.sr-only` 工具类）
**验收标准**：① 用 NVDA / Windows 讲述人操作导入与"分析"，能听到"处理中/完成/失败"；② `busyClock` 的秒级更新**不**触发播报；③ Lighthouse a11y 分数不再因"live region 缺失"扣分。

---

### 2.4 【P1 · 0.5 人日】WingMan 的图标按钮没有可读名称

**现象 + 证据**

- WingMan 有 **90 个 `<button>`，`aria-label` 为 0**（`grep -o 'aria-label'` → 0）。多数按钮带可见文字（如"删除这条"），所以并非全部有问题。
- **确认无标签的一处**：`WingMan:2758` —— `<button class="btn sm ghost danger f-del" data-id="${f.id}">×</button>`，内容只有一个 `×`，既无 `title` 也无 `aria-label`。这是对象记忆里删除一条事实的按钮，屏读会念成"乘号"。
- `WingMan:553` 的 `<button class="closebtn" id="win-close" title="关闭">` 只靠 `title`。**`title` 不是可靠的可访问名**（触摸设备、部分屏读不播报，且键盘聚焦时不显示）。
- Etude 相对更好（18 个 aria-*），但它的两个纯图标按钮同样只用 `title`：`Etude:669`（`#collapse`，已有 `aria-expanded` 但无 `aria-label`）与 `Etude:686`（`#theme title="切换深浅色"`，无 `aria-label`）。

**为什么是问题**

图标按钮的可见内容为零，可访问名必须显式给出。这是 WCAG SC 4.1.2（Name, Role, Value）的直接要求，也是屏幕阅读器用户无法完成"删除/切换主题/收起侧栏"这几件事的唯一原因。

**改法（可执行）**

```html
<!-- WingMan:2758 -->
<button class="btn sm ghost danger f-del" data-id="${f.id}" aria-label="删除这条记忆">×</button>
<!-- WingMan:553 -->
<button class="closebtn" id="win-close" aria-label="关闭窗口" title="关闭">
```
```js
// Etude:686
el("button", { class: "iconbtn", id: "theme", "aria-label": "切换深浅色", title: "切换深浅色", onClick: toggleTheme })
```
> 更彻底的做法：给图标内容加 `aria-hidden="true"`（装饰性），名称只由 `aria-label` 提供——两项目目前 `aria-hidden` 命中数为 **0**，即**装饰性图标没有被排除在可访问树外**。

**优先级**：P1（`WingMan:2758` 单点可提到 P0，改动仅一行）
**工作量**：0.5 人日
**验收标准**：`axe` 的 `button-name` 规则 0 违规；键盘 Tab 到该按钮时屏读念出"删除这条记忆"。

---

### 2.5 【P1 · 1 人日】自定义弹窗缺焦点陷阱与焦点归还（WingMan）

**现象 + 证据**

- WingMan 自建了模态（`openModal` `WingMan:1382-1404`）：`role="dialog" aria-modal="true"`（`:1388`）、打开时把焦点给第一个输入框（`:1401-1402`）、`Esc` 关闭（`:1414-1418`）——**这些都是对的**。
- 但**没有焦点陷阱**：`Tab` 可以走到弹窗背后的页面元素上（`aria-modal="true"` 只是声明，浏览器/屏读不会自动限制）。`grep 'inert\|focusTrap\|trapFocus'` → 0 命中。
- **关闭后不归还焦点**：`closeModal()`（`WingMan:1374-1380`）只 `mask.remove()` 并跑清理钩子，**没有把焦点还给触发按钮**。删除操作（`confirmWithCountdown` `:1426`）走完一圈后，焦点落在 `document.body` 上，键盘用户必须重新 Tab 一整圈才能回到原位。
- Etude 用原生 `confirm()`（`Etude:1963/1973/2216/2766/3463/4237`）**回避了这个问题**——原生弹窗自带焦点管理，代价是样式不可控、不能放长文案（WingMan `:1366-1369` 的注释正好解释了它为什么自建）。**两条路各有代价，但 WingMan 选的那条路还没走完。**

**为什么是问题**

WCAG SC 2.4.3（Focus Order）与 2.1.2（No Keyboard Trap 的反面：**焦点不应逃出模态**）。这是纯正的前端交互缺陷，与后端无关。

**改法（可执行）**

```js
// ① WingMan:1382 openModal —— 记录打开者
function openModal({ title, sub = "", body = "", wide = false }) {
  closeModal();
  const opener = document.activeElement;      // ← 新增
  const mask = document.createElement("div");
  /* …既有代码不变… */
  mask.__opener = opener;                      // ← 挂到节点上
  /* … */

  // ② 焦点陷阱：把 Tab 关在模态内
  mask.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = card.querySelectorAll(
      'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'
    );
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
}

// ③ WingMan:1374 closeModal —— 归还焦点
function closeModal() {
  const mask = document.getElementById("modal-mask");
  const opener = mask && mask.__opener;
  if (mask) mask.remove();
  const hooks = _modalHooks; _modalHooks = [];
  for (const fn of hooks) { try { fn(); } catch (e) { /* 清理失败不该影响关闭 */ } }
  if (opener && document.contains(opener)) opener.focus();   // ← 新增
}
```

**优先级**：P1
**工作量**：1 人日
**验收标准**：① 打开模态后连续 `Tab` 只在模态内循环；② `Esc`/关闭后焦点回到触发按钮；③ 补一条 **DOM 级测试**（WingMan 目前无任何 DOM 测试，见 2.9）。

---

### 2.6 【P1 · 1 人日】两项目都没有 CSP；内联脚本是"AI 内容 XSS"的唯一最后防线

**现象 + 证据**

- `grep -ci 'Content-Security-Policy'` 在两个 HTML 里都是 **0**；后端也没有发送 CSP 响应头（`grep -rn 'Content-Security-Policy' WingMan/backend/app/*.py Etude/backend/app/*.py` → 0 命中）。
- 两个前端都有**内联 `<script>`**（WingMan `1253`、Etude `696`）——这是收紧 CSP 的主要障碍（需要 hash 或 nonce 才能允许内联）。
- 好消息：**两项目都零内联事件处理器**（`onclick=` 0 命中），也没有 `eval` / `new Function`——这意味着 CSP 里**不需要 `'unsafe-inline'`，也不需要 `'unsafe-eval'`**，可以直接上严格策略。

**为什么是问题**

在 2.1 那条守卫之外，CSP 是**纵深防御**：即使某天有一处 `innerHTML` 失守，`script-src` 也能挡住注入的 `<script>` 与外部脚本加载。对于"AI 输出是不可信输入"这个场景，这是唯一一道**不依赖工程师记性**的防线。缺了它，2.1 的手工守卫就是单点。

**改法（可执行）**

内联脚本 + 无内联事件 = 用 **SHA-256 hash** 放行，其余全禁：

```python
# WingMan/backend/app/main.py —— 新增中间件（与既有 NoStoreHtmlMiddleware 同风格）
import base64, hashlib, re
from pathlib import Path

def _inline_script_hashes(html_path: Path) -> list[str]:
    html = html_path.read_text(encoding="utf-8")
    return [
        "'sha256-" + base64.b64encode(hashlib.sha256(m.group(1).encode()).digest()).decode() + "'"
        for m in re.finditer(r"<script>(.*?)</script>", html, re.S)
    ]

class CSPMiddleware:
    def __init__(self, app, html_path: Path) -> None:
        self.app, self.script_hashes = app, _inline_script_hashes(html_path)  # 启动时算一次

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send); return
        async def send_csp(message) -> None:
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers") or [])
                ctype = next((v.decode("latin-1").lower() for n, v in headers
                              if n.lower() == b"content-type"), "")
                if ctype.startswith("text/html"):
                    policy = ("default-src 'none'; "
                              f"script-src {' '.join(self.script_hashes)}; "
                              "style-src 'unsafe-inline'; img-src 'self' data:; "
                              "connect-src 'self'; font-src 'self'; "
                              "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
                    headers.append((b"content-security-policy", policy.encode()))
                message["headers"] = headers
            await send(message)
        await self.app(scope, receive, send_csp)
```
Etude 同理加到 `Etude/backend/app/api.py:847-858` 的 `index()`（已有 `_NO_STORE`，就在旁边加）。

> ⚠️ 两点注意：① `style-src 'unsafe-inline'` 是因为两项目内联 `style="…"` 属性很多（`WingMan:2393` 就动态拼 `style="width:${…}%;background:${c}"`），**先放过样式、只锁脚本**，风险收益最划算；② 一旦上了 hash，**每次改 `<script>` 内容都要重算**——所以 hash 必须在**启动时**算（如上），不要写死在配置里。

**优先级**：P1（可与 2.1 同批做，两者互补）
**工作量**：1 人日（两项目各 0.5 天）
**验收标准**：① DevTools Console 无 CSP 违规报错、界面功能全通；② 在 `analysisHTML` 的输出里人为注入 `<script>alert(1)</script>` 后**不执行**；③ 改一次 `<script>` 内容后忘记重算 hash 会导致白屏——把"hash 在启动时算"写进注释避免这个坑。

---

### 2.7 【P1 · 0.5 人日】两项目都不响应"减少动态效果"，WingMan 完全没有暗色/字号偏好

**现象 + 证据**

- **`prefers-reduced-motion`**：WingMan **0 命中**，而它有 `@keyframes`/`animation`（`grep -cE '@keyframes|animation:'` → 2）与每秒刷新的 `busyClock`（`WingMan:1354`）；Etude 有 2 处正确实现（`Etude:427`、`Etude:617` 的 `.drawer{animation:none}`）。
- **主题与显示偏好**：
  - WingMan 只有单一浅色板（`WingMan:20 --bg:#f4f6f8`），**无 `prefers-color-scheme`、无 `data-theme`、无字号/密度设置**；`localStorage` 只存了一个"向导已关闭"标记（`WingMan:3739/3806`）。
  - Etude 有完整三套主题（`prefers-color-scheme: dark` + `data-theme="warm|light|dark"`，`Etude:60/72/82/92`），并把主题/字号/密度/侧栏状态持久化（`Etude:4432-4453`）——**这是 Etude 明显领先的一块**。

**为什么是问题**

"减弱动态效果"是前庭障碍用户的刚需；暗色/字号是长时间使用（WingMan 定位是"聊天参谋"，会长时间盯着看）的可读性需求。Etude 已经证明这套在单文件零构建下**完全做得出来**（纯 CSS 变量 + `localStorage`），WingMan 不做属于遗漏而非取舍。

**改法（可执行）**

```css
/* WingMan —— 先补最小的一份（复刻 Etude 的做法） */
@media (prefers-reduced-motion: reduce){
  *{animation:none !important;transition:none !important}
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#181a1c; --panel:#212325; --panel2:#26282b; --panel3:#2c2f33;
    --border:#34383d; --border2:#454a51;
    --text:#ded9d2; --muted:#a49e95; --dim:#7d786f;   /* 注意 ≥4.5:1 */
    --accent:#69a8f0; --accent-press:#8fbbf5; --accent-weak:#20293a; --accent-line:#2b3d5c;
    --ok:#5fbf8f; --warn:#d6ac5c; --danger:#e0837c;
  }
}
```
字号/密度切换照抄 Etude `Etude:4432-4453` 的"存 `localStorage` + 应用到 `:root`"三行模式即可。

**优先级**：P1
**工作量**：0.5 人日（reduced-motion 15 分钟；暗色板 0.5 天，需按 2.2 的口径核对比度）
**验收标准**：① 系统开启"减少动态效果"后 WingMan 无动画；② 系统暗色时 WingMan 自动切暗且所有文字仍 ≥4.5:1。

---

### 2.8 【P1 · 1 人日】单文件内部结构：114/140 个全局函数无边界，顶层绑定 49 处无空值保护

**现象 + 证据**

- **全局函数**：WingMan 顶层 `function` **114 个**（`grep -cE '^(async )?function '`）+ 顶层 `const` 25 + 顶层裸 `let/var` **4**；Etude 顶层 `function` **140 个** + `const` 17 + 裸 `let/var` 4。**全部挂在同一个全局作用域，无 `type="module"`、无 IIFE 命名空间**（`grep -c 'type="module"'` 两项目均 0）。
  - 好消息：我用 `uniq -d` 检查过，**两项目当前都没有同名函数冲突**（`grep -oE '^function name' | sort | uniq -d` → 空）。也就是说这是**潜在**风险而非既存 bug。
  - 风险点在于：`state`（`WingMan:1274`）是一个**全局可变单例**，被 114 个函数直接读写，其中包含 `messages` / `msgSel: new Set()`（`:1283`）这样的**可重入状态**。例如 `fetchObjMessages` 被 `#ob-refresh`/`#ob-more`（`WingMan:3132/3133`）两处触发，未见取消机制（`grep -c 'AbortController'` → 0），快速连点可能造成"后发先至"的渲染错乱。
- **顶层绑定**：49 处 `$("#id").addEventListener(...)` 无 `?.`（见 1.2）。WingMan 自己写了守卫测试断言"`$("#x")` 的 id 有人创建"（`test_frontend_assets.py:87`），但它**只证明 id 字符串在某处出现过，不证明绑定时元素已存在**——一个只在弹窗模板里出现的 id 能通过测试，却在顶层绑定时是 `null`。
- **零构建约束下的可选项**：既有的 `test_frontend_assets.py` 已经把"未定义调用""缺失 id"挡住了大半，所以这里不是为了"拆文件"而拆（第一轮已判定不必上打包器），而是**降低单点失效的面**。

**为什么是问题**

单文件前端的最大风险不是行数，而是**一个未捕获异常会让后面所有初始化停止**。WingMan 作者在 `test_frontend_assets.py:163-173` 的注释里已经完整描述过这个故障模式（"`init()` 里那个 `await loadChats()` 一抛 ReferenceError，后面的读设置、自检、深链接就全都不执行了"）。这是**已被理解但尚未结构化解决**的问题。

**改法（零构建、零依赖、不引入打包器）**

三件互相独立的小事，任选先做：

1. **把裸绑定换成"安全绑定"助手**（消除 49 处隐患，行为不变）：`WingMan:1258` 附近加
   `const on = (sel, ev, fn) => { const n = $(sel); if (n) n.addEventListener(ev, fn); else console.warn("[bind] 未找到", sel); };`
   然后把 `$("#cp-go").addEventListener("click", …)` 改为 `on("#cp-go", "click", …)`——**把"绑定失败"从静默变成一条 warn**，配合既有守卫测试即可定位。
2. **给 `init()`（`WingMan:4631`）加异常分片**，避免一处失败拖垮全部初始化：
```js
for (const [name, step] of [["health", loadHealth], ["objects", loadObjects],
                            ["settings", loadSettings], ["selfcheck", loadSelfCheck]]) {
  try { await step(); } catch (e) { console.error(`[init] ${name} 失败`, e); }
}
```
3. **给可重入请求加取消**（`AbortController`，两项目当前均 0 命中）：
```js
let _msgAbort = null;                       // 以 WingMan 的 fetchObjMessages 为例
async function fetchObjMessages(more) {
  _msgAbort?.abort();                       // 取消上一次
  _msgAbort = new AbortController();
  try { const d = await api(`…`, { signal: _msgAbort.signal }); /* … */ }
  catch (e) { if (e.name === "AbortError") return; /* 真正失败才提示 */ }
}
```
4. **若将来真要拆**（非本轮建议，仅为记录）：可拆成多个 `<script type="module">` + `defer` 保持无构建——代价是跨块调用必须显式 `import`/导出，且 `file://` 直开会被 CORS 拦住。当前前端由后端 `StaticFiles` 提供（`WingMan/backend/app/main.py:223-225`），所以可行；但收益**不如上面 1/2/3 的性价比**。第一轮"不要一步上打包器"的判断依然成立，本轮补的是"**不拆也能显著降风险**"。

**优先级**：P1（第 1、2 条各 20 分钟，可今天做；第 3 条 0.5 天）
**工作量**：1 人日
**验收标准**：① 全文件 `$("#id").addEventListener` 直接绑定数降为 0（`grep` 可验）；② 故意把某处 `on("#nonexistent", …)` 写错，控制台出现明确 warn 而界面其余部分照常工作；③ 快速连点"加载更多"不出现列表错乱。

---

### 2.9 【P1 · 1.5 人日】前端零 DOM 级测试：静态守卫挡不住"事件名大小写"这类运行期静默失效

**现象 + 证据**

- WingMan：前端相关测试只有 `backend/tests/test_frontend_assets.py`（**纯正则静态检查**，见 1.4）。**没有任何 DOM 级测试**（`grep -rln 'jsdom\|playwright\|puppeteer' WingMan/backend/tests/` → 0）。`scripts/e2e_check.py` 是对**运行中的服务**跑 HTTP 检查（不是前端），且 **`grep -n 'e2e_check' WingMan/.github/workflows/ci.yml` → 0 命中，未接入 CI**。
- Etude：有 `scripts/ui_smoke.js`（1023 行）+ `cdp.js`（214 行）+ `screenshots.js`，但 **`grep -n 'ui_smoke\|cdp.js\|screenshots' Etude/.github/workflows/ci.yml` → 0 命中，同样未接入 CI**。
- Etude 作者自己在 `Etude:12-18` 的文件头注释里点破了这个盲区，并且写下的正是**静态守卫抓不到**的那一类：
  > "改完要跑 `python scripts/check_js.py` 检查调用点"
  > "事件名走 `el()` 的 onXxx 通道，它会 `toLowerCase`（**大小写敏感，写错就静默失效**）"
  > "**任何按钮都不能「点了没反应」**"
  其中"大小写写错就静默失效"（`Etude:768-773` 的 `key.slice(2).toLowerCase()`）——`check_js.py` 只查"函数名是否存在"，**查不出 `{ OnClick: fn }` 这种大小写错误**。
- WingMan 的同类风险面更大：90 个静态按钮 + 49 处顶层直接绑定，全靠 id 字符串对齐；`test_frontend_assets.py:87` 的守卫**只保证 id 出现过**。

**为什么是问题**

两项目的作者都明确写出了"点了没反应"是**最伤用户的问题**（Etude 甚至把它写进 0.0.2 的修 bug 动机），但**都没有一台机器在 CI 里真的点一次按钮**。静态守卫 + 人工截图是这个盲区的现状。这是"单文件零构建"最贵的那部分代价，且已有现成工具可补（不需要引入打包器）。

**改法（可执行）**

用已有的 playwright（Etude 的 `ui_smoke.js` 已经是一套 CDP 脚本，说明这条路他们接受）在 CI 里跑最小 smoke：

```yaml
# Etude/.github/workflows/ci.yml（新增 job；WingMan 同理）
ui-smoke:
  name: 界面冒烟
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.11" }
    - run: pip install -e "backend[dev]" && pip install playwright && playwright install --with-deps chromium
    - run: |
        cd backend && python -m uvicorn app.main:app --port 8787 &
        sleep 3
        node scripts/ui_smoke.js http://127.0.0.1:8787
```
最小断言形态：**从"主按钮清单"出发逐个点击 → 断言 DOM 出现预期变化**（而非"无 console.error"），专门覆盖 `OnClick` 大小写写错、id 漂移这两类静态守卫抓不到的失效。

**优先级**：P1
**工作量**：1.5 人日（Etude 已有 `ui_smoke.js`，接入约 0.5 天；WingMan 需新写一份最小版约 1 天）
**验收标准**：① CI 里真的启动服务并点击主流程按钮；② 故意把 `WingMan:2524` 的 `"click"` 改成 `"Click"` 后 CI 变红；③ **与第一轮的关系**：第一轮 §5.3 已把"Etude 把 `ui_smoke.js` 接入 CI"列进 W4 —— 本轮补充的是 **WingMan 连 `ui_smoke` 都没有，且它的 `e2e_check.py` 同样未接入 CI**，这是第一轮未点明的对称缺口。

---

### 2.10 【P2 · 1 人日】i18n：15470 / 10776 个汉字全部硬编码，无任何抽离层

**现象 + 证据**

- 汉字计数（`len(re.findall(r'[\u4e00-\u9fff]', html))`）：**WingMan 15470 个、Etude 10776 个**。
- `lang="zh-CN"`（`WingMan:2`、`Etude:2`）。
- **无 i18n 层**：`grep -cE '\bt\(|i18n|locale|messages\['` 在两文件均近 0 命中；没有 `en.json` / 语言包，没有 `t("key")` 形式的取词函数。
- 文案直接写在**三种位置**：静态 HTML（WingMan `547-1252`）、JS 模板串（`innerHTML` / `el(...,{text})`）、以及**错误与提示文案**（如 `WingMan:3558-3559` 的"API Key 不对 / 去服务商后台重新复制一次"）。

**为什么是问题**

第一轮 §6 已经给出方向（补 `README.en.md` + 顶部语言切换，`README` 层双语）。**但界面本身的双语是另一件事**，且被第一轮默认跳过了。实话说：**对这两个项目，界面 i18n 的性价比很低**——它们是"本地优先、面向中文聊天场景（QQ/微信导出）"的工具，`WingMan` 还要读 QQ/微信的聊天记录，界面英文价值有限。所以我**不建议做完整 i18n**，而是建议把这条**降级为"有界投入"**，见改法。

**改法（可执行，按性价比排序）**

1. **不做 i18n 框架，只做"文案集中"**（0.5 天，一次性把散落的文案收敛到文件顶部一个常量对象，仍是中文）：
```js
// WingMan:1256 附近
const MSG = {
  loading: "加载中…",
  backendDown: "后端未连接",
  errNoChannel: "先在上面勾一个渠道",
  // …按 `grep -oE '"[^"]*[\u4e00-\u9fff][^"]*"' 抽出的高频文案逐条搬进来
};
```
   好处：将来**若**要做英文，只需替换这一个对象；同时它天然消除"同一个提示在 3 个地方各写一遍"的漂移。
2. **不要碰**：日期/数字格式化当前**没有问题**——两项目都在后端做本地化展示（`WingMan:2457` 的耗时、`Etude:1710` 的 `textContent = String(n)`），前端没有 `toLocaleDateString` 之类会随语言变化的调用。这一条**保持现状**。
3. 工作量估算（供第一轮"补英文 README"配套参考）：**界面英文 = 约 5–8 人日**（15470 汉字，其中约 40% 是注释与设计说明——注释不用译；实际可见文案约 600–900 条）。**结论：不值得，建议只做英文 README + 首屏截图**。

**优先级**：P2
**工作量**：0.5 人日（只做文案集中，不做翻译）
**验收标准**：① 高频提示文案集中到一个常量对象，`grep` 可验无重复字面量；② 明确记录"不做界面英文"的决定及理由，避免下一轮重复讨论。

---

### 2.11 【P2 · 0.5 人日】Etude 混用原生 `alert`/`confirm`，与它自己的定制 UI 不一致

**现象 + 证据**

- Etude 有 **12 处 `alert()`**（`Etude:1968/1979/2248/2252/2259/2260/2264/2279/2289/2586/2772/3136`…）与 **6 处 `confirm()`**（`Etude:1963/1973/2216/2766/3463/4237`）。
- 其中 `Etude:1963` 的删除确认文案极长："删除「X」？例句、语音、场景图和复习记录都会一并删掉，不可恢复。" —— 塞进原生 `confirm` 的一行里；`Etude:1973` 甚至用 `\n\n` 手动换行凑版式。
- 对比 WingMan：它**专门为此写了自建模态**，并在注释里给出了三条理由（`WingMan:1366-1369`）：
  > "1) 删除这种操作要说清「会连带失去什么」，原生弹窗只能塞一行字；2) 需要一个「读完声明、倒计时结束才能点」的按钮，原生做不到；3) 原生弹窗在自动化截图里根本不出现，等于没法回归验证。"
  也就是说，**WingMan 已经论证过这个问题并给出了方案**，Etude 还停在原生弹窗阶段。

**为什么是问题**

① 原生弹窗不能承载"删除会造成什么"的说明，而 Etude 的删除**真的会级联删掉例句/语音/场景图/复习记录**（`Etude:1963` 自述）——这正是最需要说清楚的场景；② 原生弹窗**在 headless 截图里不出现**，所以它同时也是 2.9 那条"UI 冒烟测试"的障碍（WingMan 的注释第 3 点说的就是这个）；③ 浏览器可屏蔽 `alert`（部分环境下静默失效）。

**改法（可执行）**

把 WingMan 的 `openModal` / `confirmWithCountdown`（`WingMan:1382` / `:1426`）移植到 Etude；或更省事——Etude 已有 `el()`（`Etude:760`），换成一个返回 Promise 的模态即可：

```js
// Etude:810 附近，与 errorBlock 并列
function confirmModal({ title, body, confirmLabel = "确认", danger = false }) {
  return new Promise((resolve) => {
    const mask = el("div", { class: "modal-mask" });
    const close = (v) => { mask.remove(); resolve(v); };
    const card = el("div", { class: "modal", role: "dialog", "aria-modal": "true" }, [
      el("h3", { text: title }),
      el("div", { class: "mbody" }, [el("p", { text: body })]),
      el("div", { class: "mfoot" }, [
        btn("取消", { class: "btn", onClick: () => close(false) }),
        btn(confirmLabel, { class: `btn ${danger ? "danger" : "primary"}`, onClick: () => close(true) }),
      ]),
    ]);
    mask.appendChild(card); document.body.appendChild(mask);
    card.querySelector("button")?.focus();
  });
}
// 用法：if (!await confirmModal({ title: "删除「" + target + "」？",
//         body: "例句、语音、场景图和复习记录都会一并删掉，不可恢复。",
//         confirmLabel: "删除", danger: true })) return;
```

**优先级**：P2
**工作量**：0.5 人日（先替换 6 处 `confirm()`；`alert()` 可分批）
**验收标准**：① 6 处 `confirm()` 全部替换，删除场景能看到完整风险说明；② 新模态在 Playwright 截图里可见（为 2.9 铺路）。

---

### 2.12 【P2 · 0.25 人日】细项清理（跨两项目，逐条 5–20 分钟）

| # | 现象 + 证据 | 改法 | 优先级 |
|---|---|---|---|
| a | 密钥输入框缺 `autocomplete`：WingMan 全文件 `autocomplete` 仅 1 命中，而 `WingMan:1042` `#s-llm_api_key`、`WingMan:1076` `#s-embed_api_key` 都是 `type="password"`（这点是对的）——密码管理器可能把站点密码填进 API Key 框 | 加 `autocomplete="new-password"` + `spellcheck="false"` | P2 |
| b | WingMan `<label>` 33 个但 `for=` **0 个**（全为包裹式）。包裹式**可用**，但 `WingMan:1041-1042` 这类"`<label><span>API Key</span><input…></label>`"在部分屏读下会把 `span` 与 `input` 一起念，冗长 | 统一为 `<label for="s-llm_api_key">` + `id`（id 已存在，改动很小） | P2 |
| c | 装饰性图标未被排除：两项目项目 `aria-hidden` 命中数为 **0**，而图文混排按钮很多（如 `WingMan:2758`、Etude 的 `<span class="ico">`） | 图标节点加 `aria-hidden="true"`，可访问名只由文字/`aria-label` 提供 | P2 |
| d | Etude 用 `data-icon` 占位后由 `paintIcons()`（`Etude:752`）补 SVG，**若它未跑到，按钮上就是一个空 `<span>`** —— 5 个主导航按钮的文字在 `<span class="label">` 里（`Etude:673-677`），所以不至于"点了没反应"，但图标会空着 | 无实害，仅记录；`ui_smoke` 可加一条"图标非空"断言 | P3 |
| e | WingMan `document.body.innerHTML = ` 清屏（`WingMan:4603`）——**已核对为纯静态字符串，无插值，安全**，仅记录为"审查过" | 无需改 | — |
| f | 两项目均无 `sr-only` 工具类（见 2.3） | 补 `.sr-only` | 含在 2.3 |

---

## 3. 跨项目共性清单（F-1 … F-8）

> 编号前缀 F = Frontend。给出"一次学会、两处受益"的清单。

| 编号 | 问题 | WingMan | Etude | 证据锚点 | 优先级 |
|---|---|---|---|---|---|
| **F-1** | **无 CSP 响应头**，但有内联脚本 | ❌ | ❌ | `WingMan/backend/app/main.py` 无 CSP（`grep` 0）；`Etude/backend/app/api.py:843-858` 无 CSP | P1 |
| **F-1b** | **无转义守卫**（有语法检查/软守卫，都不是硬守卫） | 仅 `vm.Script` 语法编译（`ci.yml:67-80`） | `innerHTML` 守卫但软警告（`ci.yml:103-110`） | 见 1.4、2.1 | P0 |
| **F-2** | **零 `aria-live`**：异步状态对屏读静默 | ❌ | ❌ | `grep -o 'aria-live'` 均 0 | P0 |
| **F-3** | **极淡文字对比度 < 4.5:1**（全部主题） | `--dim` 3.10:1 | `--fg-faint` 2.50:1 | `WingMan:188` / `Etude:48,65,86,96` | P0 |
| **F-4** | **零 `prefers-reduced-motion`**/动效偏好 | ❌（0） | ✅（`Etude:427/617`） | 见 1.5 | P1（WingMan）/ ✅（Etude） |
| **F-5** | **无 DOM 级前端测试接入 CI** | ❌（无脚本） | ⚠️（有 `ui_smoke.js` 但未接入） | `ci.yml` grep 0 命中 | P1 |
| **F-6** | **无 eslint / 无 HTML 校验 / 无 a11y 检查** | ❌ | ❌ | `grep -il eslint` 0 | P2 |
| **F-7** | **i18n 无抽离层**（文案硬编码三处） | 15470 汉字 | 10776 汉字 | 见 2.10 | P2 |
| **F-8** | **装饰性图标未 `aria-hidden`** | ❌ | ❌ | `grep aria-hidden` 均 0 | P2 |

**已在两项目都做对、不要改坏的**（评审中确认的正向资产）：

- ✅ **零外部依赖**：0 CDN / 0 `<link>` / 0 `@import` / 0 `@font-face`，字体走 `system-ui` 本地栈——"训练工具必须断网也能用"（`Etude:9-10` 的原话）在实现上确实成立。
- ✅ **零内联事件处理器**（`onclick=` 0 命中）——为将来收紧 CSP 省掉了 `'unsafe-inline'`。
- ✅ **零 `eval` / 零 `new Function`**。
- ✅ **无密钥写入前端存储**（`localStorage` 只放 UI 偏好/向导标记，`WingMan:3739/3806`、`Etude:4432-4453`）。
- ✅ **密钥输入框用 `type="password"`**（`WingMan:1042/1076`、`Etude:2917-2920/2975/3039-3041`）。
- ✅ **HTML 明确 `no-store`**，避免"界面是旧的、接口是新的"这一整类误判——WingMan `main.py:148-182` 的中间件注释把理由写得非常清楚。
- ✅ **脚本置于 body 末尾**，无阻塞渲染的外部请求；单文件 226/178 KB 本地读取。
- ✅ **`.objitem` / `.chitem` 自定义 div 按钮键盘可达**（`tabindex=0` + Enter/Space `WingMan:1922-1924` + Shift+F10 右键菜单 `:1933/:1951`）——这是很不容易做对的一处。
- ✅ **WingMan 的 `test_frontend_assets.py`**（293 行 / 8 条守卫）是**跨项目里最好的前端静态守卫**，含跨层白名单检查（前端下拉 vs 后端 `SEMI_CLIENTS`、`CHAT_PLATFORMS` vs `_CHANNEL_BY_PLATFORM`），值得 Etude 反向借鉴。
- ✅ **Etude 的 `el()` 架构**（`Etude:760-782`）从源头消灭了 `innerHTML` 汇点，是两项目里**最值得推广的前端安全模式**。
- ✅ **Etude 的 `check_js.py`**（367 行）对"守卫要先剥字符串与注释、否则会误报"的理解非常到位——这条经验应该写进 README 供后来者参考。
- ✅ **Etude 的三套主题 + 偏好持久化**（`Etude:60/72/82/92/4432-4453`），WingMan 可直接复刻。
- ✅ **`target="_blank"` 全部带 `rel="noopener"`**（WingMan 6/6）。
- ✅ **健康态/降级态对用户可见**：`WingMan:1763` "后端未连接"、`WingMan:1751-1752` provider pill、`WingMan:2457` trace 里的 `llm`；`Etude:4502` "连不上后端"、`Etude:4488` `health.mode`。

---

## 4. 落地路线（3 周 + 验收标准）

> 按 1 名开发者、每周 1.5–2 人日投入估算。每个动作可独立成 commit。**总工作量约 11 人日。**

### 第 1 周 —— 安全网 + a11y 底座（约 4 人日）

| # | 动作 | 对应发现 | 验收标准 |
|---|---|---|---|
| FE1 | **WingMan：`innerHTML` 插值转义守卫**（借 `Etude/scripts/check_js.py` 的解析器，换判定规则） | 2.1 / F-1 配套 | 现有代码全绿；人为插入未转义插值后 CI 变红；已进 `WingMan/.github/workflows/ci.yml` |
| FE2 | **两项目：修极淡文字对比度**（`--dim` / `--fg-faint` / `--warn`，含全部主题） | 2.2 / F-3 | `axe` / Lighthouse `color-contrast` 0 违规；层次感保留 |
| FE3 | **两项目：补 `aria-live` + `.sr-only` 工具类**；`busyClock` 不挂 live | 2.3 / F-2 | NVDA 能听到"处理中/完成/失败"；秒级更新不刷屏 |
| FE4 | **WingMan：图标按钮 `aria-label`**（先修 `WingMan:2758`、`:553`）；Etude 修 `:669/:686` | 2.4 / F-8 | `axe` `button-name` 0 违规 |

### 第 2 周 —— 纵深防御 + 交互正确性（约 4 人日）

| # | 动作 | 对应发现 | 验收标准 |
|---|---|---|---|
| FE5 | **两项目：CSP 中间件**（SHA-256 hash 放行内联脚本，`script-src` 收紧） | 2.6 / F-1 | 无 CSP 违规报错；注入 `<script>` 不执行；hash 启动时算 |
| FE6 | **WingMan：模态焦点陷阱 + 焦点归还** | 2.5 | 焦点在模态内循环；关闭后回到触发按钮 |
| FE7 | **WingMan：安全绑定 `on()` + `init()` 分片 + `AbortController`** | 2.8 | 直接绑定数降 0；改名 id 只丢一个按钮；连点不错乱 |
| FE8 | **WingMan：`prefers-reduced-motion` + 暗色板 + 字号/密度偏好持久化** | 2.7 / F-4 | 系统偏好生效；暗色下文字仍 ≥4.5:1 |

### 第 3 周 —— 回归防线 + 收尾（约 3 人日）

| # | 动作 | 对应发现 | 验收标准 |
|---|---|---|---|
| FE9 | **两项目：UI 冒烟接入 CI**（Etude 接 `ui_smoke.js`；WingMan 写最小版 + 接 `e2e_check.py`） | 2.9 / F-5 | CI 真启动服务并点主流程；改坏事件名后变红 |
| FE10 | **Etude：`confirm()` → 自建模态**（移植 WingMan 方案） | 2.11 | 6 处替换；删除场景有完整风险说明；弹窗可截图 |
| FE11 | **两项目：文案集中常量对象**（不做翻译） | 2.10 / F-7 | 高频文案无重复字面量；记录"不做界面英文"的决策 |
| FE12 | **细项清理**（`autocomplete`、`label for`、`aria-hidden`） | 2.12 | `axe` 无新增违规；`grep` 可验 |

---

## 5. 待确认项

1. **`--accent` on `--accent-weak` 的实际组合**：WingMan `--accent:#2f6fed` / `--accent-weak:#eef4ff` 算得 4.12:1（FAIL），但我**没有穷举所有把 accent 文字放在 accent-weak 底上的选择器**。需实测确认这是"真在用的组合"还是"两个变量恰好都定义了"。其余已列出的对比度问题都是逐对核对过的，"待确认"仅指这一对。
2. **`WingMan:2758` 以外的纯图标按钮**：我用正则 `<button[^>]*>(符号)</button>` 只命中 1 处，但**动态生成的按钮**（`innerHTML` 模板里含 `<button>×</button>` 之类）可能漏计。需人工过一遍 90 个 `<button>` 的实际可访问名（`axe` 一键可得）。
3. **`WingMan:1751-1752` 的 `h.providers` 是否包含"当前生效的 provider"**：界面显示了 provider 列表（带 available 状态），但我**未逐条核对** Mock/降级时是否有一个显眼的"当前用的是 Mock/降级"横幅。这关系到"AI 请求降级时用户能否分辨"——本轮只能确认"显示了 provider 名与可用性"，不能确认"是否足以让用户意识到结果不可信"。
4. **是否真有并发重入**：`fetchObjMessages` 未见取消机制是**静态推断**；实际是否会出现"后发先至"取决于后端响应顺序与用户手速，**未运行验证**。
5. **Etude `ui_smoke.js` 的运行前置**：需要什么浏览器/CDP 依赖、跑多久，**未深入**——第一轮 §9 第 4 条同样把它标为待确认。接入 CI 前必须先跑通一次。
6. **两个前端的实测首屏时间**：本轮只做了静态推断（无外部请求、脚本置尾），**未实测** First Paint / 大文件解析耗时（4653 行的 HTML 解析本身有成本，未量化）。
7. **`aria-pressed` 13 处是否都用在真正的 toggle 上**（Etude）：未逐处核对语义是否恰当。

---

## 6. 与第一轮报告的关系

> 第一轮覆盖【代码架构 / 测试与 CI / 开源呈现与隐私】。本轮**全部条目都是前端工程质量**，与第一轮无重叠；下面逐条说明"角度不同在哪"。

| 本轮条目 | 第一轮对应 | 关系 |
|---|---|---|
| **1.1 单文件内部结构诊断**（style/body/script 行数、114/140 全局函数、顶层绑定 64 处） | 4.2① 巨型文件表（把前端 4653/4519 列入拆分清单） | **第一轮只给"结论"（零构建可接受、渐进抽取、不要上打包器），本轮给出"诊断数据"**——第一轮没有区分 `<style>`/`<body>`/`<script>` 各占多少，也没统计全局函数数与绑定方式。本轮还证明 Etude 的 body 仅 32 行、两项目都是"大全局作用域" |
| **2.1 WingMan innerHTML 汇点 + 守卫** | §8「Etude 的 CI 有 innerHTML XSS 守卫——建议 WingMan 照抄」 | **角度不同且有修正**：第一轮说"照抄"，本轮实测**照抄不可行**（Etude 的守卫会把 WingMan 85 处全报红），并给出 WingMan 专用的白名单式判定规则。同时量化了汇点面（85 vs 0）与转义纪律现状（256 次 `esc()`，无既存漏洞）。**与第二轮安全维度 sec-supply 的 P1-S8 是同一条的两个面**：安全维度证明"当前无活漏洞"，前端维度补"按数据来源分档（第三方导入记录 / AI 输出 / 用户输入）+ 落成硬守卫"；**建议两人合并成同一个 `check_innerhtml.py`，不要在报告里各写一份** |
| **2.6 CSP** | 无 | **全新**：第一轮的架构评审未涉及响应头/CSP |
| **2.2 / 2.3 / 2.4 / 2.5 a11y** | 无 | **全新**：第一轮完全没做可访问性体检 |
| **2.7 主题/reduced-motion** | 无 | **全新** |
| **2.8 顶层绑定 / 可重入 / init 分片** | 4.2① 的"拆不拆"议论 | **角度不同**：第一轮讨论"拆文件的收益"，本轮讨论"**不拆也能降风险**"的三条具体手段（安全绑定、init 分片、AbortController），并指出第一轮未提的 `test_frontend_assets.py` 守卫的**能力边界**（只证明 id 出现过，不证明绑定时存在） |
| **2.9 前端无 DOM 测试** | §5.3 W4「Etude 把 `ui_smoke.js` 接入 CI」 | **补充对称缺口**：第一轮已提 Etude 一侧；本轮补充 **WingMan 连 `ui_smoke` 都没有，且它的 `scripts/e2e_check.py` 也未接入 CI**（`ci.yml` grep 0 命中） |
| **2.10 i18n** | 6.3 补英文 README / §6.1 全中文 | **给出被跳过的部分与量化结论**：第一轮只谈 README 双语；本轮量化界面 i18n 的成本（15470/10776 汉字 → 5–8 人日）并**建议不做**，只做文案集中 |
| **2.11 Etude 原生 alert/confirm** | 3.4/W-8 后端异常回显 | **不同层**：第一轮讲后端不回显堆栈；本轮讲前端**用什么控件呈现**（原生弹窗 vs 自建模态），并引用 WingMan `:1366-1369` 已给出的三条自建理由 |
| **1.4 前端静态守卫对比** | §5.2③ 三项目 lint 关卡（仅 TideWatch 达标） | **落实到了前端**：第一轮讲的 lint 是 Python 侧（ruff）；本轮对比的是**前端侧**的 `test_frontend_assets.py`（WingMan）vs `check_js.py`（Etude），并指出两者都不查 a11y/转义/eslint |

**一句话总结与第一轮的分工**：第一轮回答"**这两个前端要不要拆、拆了值不值**"（答案：不必上打包器，渐进抽取）；本轮回答"**不拆的前提下，这个前端还差哪些工程零件**"（答案：转义守卫、CSP、a11y 底座、DOM 测试、色板合规、零构建下的安全绑定/分片）。

---

## 附录 A：统计口径与复现命令

```bash
R="C:/Users/HP/WorkBuddy/2026-10-13-11-45-56/gh-repos"; W="$R/WingMan/frontend/index.html"; E="$R/Etude/backend/frontend/index.html"

# 结构分块（grep -n -iE '<!DOCTYPE|<html|<head|<style|</style>|<script|</script>|<body|</body>|<link'）
#   WingMan → 1,2,3,7,545,547,1253,4651,4652,4653   |  Etude → 1,2,3,20,661,663,696,4518,4519,4520  （link 均 0 命中）

grep -c 'innerHTML' "$W"                  # 85        ;  "$E" → 0
grep -o 'esc(' "$W" | wc -l               # 256
grep -o 'addEventListener' "$W" | wc -l   # 106       ;  "$E" → 19
grep -o 'onclick=' "$W" | wc -l           # 0         ;  "$E" → 0
grep -nE '^\s*\$\("#[a-zA-Z0-9_-]+"\)\.addEventListener' "$W" | wc -l   # 49（无 ?.）
grep -cE '^\s*\$\("#[a-zA-Z0-9_-]+"\)\?\.addEventListener' "$W"         # 15（有 ?.）
grep -cE '^(async )?function ' "$W"       # 114       ;  "$E" → 140
grep -c 'type="module"' "$W" "$E"         # 0 0
grep -o '<button' "$W" | wc -l            # 90
grep -o 'aria-label' "$W" | wc -l         # 0
grep -o 'aria-live' "$W" "$E" | wc -l     # 0（合计）
grep -oE 'aria-[a-z]+' "$E" | sort | uniq -c   # aria-pressed 13 / aria-current 3 / aria-expanded 2
grep -oE ':focus(-visible)?' "$W"         # 3 条（均限定类）；Etude 1 条全局（Etude:120）
grep -c '@font-face' "$W" "$E"            # 0 0
grep -ci 'Content-Security-Policy' "$W" "$E"   # 0 0
python -c "import re;s=open('$W',encoding='utf-8').read();print(len(re.findall(r'[\u4e00-\u9fff]',s)))"  # 15470
python -c "import re;s=open('$E',encoding='utf-8').read();print(len(re.findall(r'[\u4e00-\u9fff]',s)))"  # 10776
# https?:// → WingMan 16 命中（全为 placeholder / href / 预设 base_url，无 src / 无外链资源）
```

**对比度口径**（WCAG 2.x）：`L = 0.2126·R + 0.7152·G + 0.0722·B`（每通道先 sRGB 线性化）；`CR = (L_light + 0.05) / (L_dark + 0.05)`；正常字号阈值 4.5:1、大字 3:1。数值由本地 Python 脚本算出，未依赖外部工具。

---

## 附录 B：本轮未做的（明确边界，避免误读）

- **未运行任何浏览器或 DOM**：所有 a11y 结论基于静态属性统计与配色计算，**未用 `axe` 实测**——实际违规数可能多于/少于本报告列出的项（`axe` 的验收是所有 a11y 条目的最后一步）。
- **未实测首屏性能**：无 DevTools trace、无 Lighthouse。
- **未审 `Etude/scripts/ui_smoke.js`（1023 行）与 `cdp.js`（214 行）的内容质量**：仅在 2.9 中确认它们**未接入 CI**。
- **未审 `WingMan/scripts/e2e_check.py` 的覆盖面**。
- **未改任何文件、未执行 git 命令**（遵守只读约束）。

---

*报告完 · frontend-eng · 第二轮评审*
