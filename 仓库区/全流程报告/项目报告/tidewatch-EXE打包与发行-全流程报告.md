---
title: TideWatch 打包成 Windows 免安装版 — 全流程报告
date: 2026-10-16
tags: [项目, 开源, 打包, PyInstaller, Windows, 发行, 全流程, 领域/项目, 类型/报告]
status: 已完成
repo: whyao56/TideWatch
version: v0.0.1
---

# TideWatch 打包发行 全流程报告

> **一句话**：把 tidewatch 从「clone 下来 `pip install -e .` 才能跑」
> 变成「下载一个 zip、解压、双击命令就能用」。
>
> 而真正花时间的**不是打包本身**，是两件打包之后才会发生的事：
> 一类是**冻结之后才崩**的（编码、路径），另一类是**判不出来到底行不行**
> （配置加载成功 ≠ 能出结论）。这份报告的重点在后两件。
>
> **它由两轮写成，中间隔着一次真实的翻车：** 第一轮交付了打包能力，
> 但发布流水线在 CI 上是**红的**，而当时手上连日志都拿不到（见 [第 8 节](#8)）。
> 第二轮把它修到绿、发布成功，**并且回头改掉了第一轮写下的错误结论**——
> 那时报告里写着「CI 绿 + Release 带 zip 与校验和」，而 Release 其实是失败的。
> 这件事本身也是结论之一：**报告里每个 ✅ 都得来自一次真实的运行。**

| | |
|---|---|
| **起点** | 提交 `bcdd436` · 161 条测试 · CI 绿 · **没有任何 tag / Release** |
| **终点** | 提交 `1e0827d` + tag `v0.0.1` · 195 条测试 · **Release 已发布** |
| **规模** | 7 个提交（第一轮 4 + 第二轮 3）· 25 个文件 · +2764 / −21 行 |
| **产物** | `TideWatch-0.0.1-win64.zip` · 9.47 MB（解压后 22.3 MB / 55 个文件） |
| **Release** | https://github.com/whyao56/TideWatch/releases/tag/v0.0.1 |
| **项目路径** | `C:/Users/HP/WorkBuddy/2026-10-16-08-51-37/TideWatch/` |

**本文自包含**：所有关键结论都带根因、代码要点和实测输出，
不需要打开仓库或当年的截图就能读懂。

---

## 目录

1. [开工前先摸清现状](#1)
2. [三个决策，和为什么不是另外三个](#2)
3. [打包实现：spec、入口、图标、版本资源](#3)
4. [打包之后才会出现的三类失败](#4)
5. [自检：让「能不能用」变成一个能被回答的问题](#5)
6. [构建脚本：一条命令做四件事](#6)
7. [校验和的口径](#7)
8. [发行流水线：从红到绿](#8)
9. [验收：把已发布的包下载下来真跑一遍](#9)
10. [踩坑总表](#10)
11. [实测记录](#11)
12. [未验证项（诚实记账）](#12)
13. [用上了哪些既有经验](#13)
14. [复现全部结论](#14)

> 第 1～6 节是第一轮的内容（把 exe 做出来）；
> 第 7、8、9 节是第二轮补的（把发行做出去，并验收它）；
> 第 10 节起是两轮合并后的汇总表。

---

<a id="1"></a>
## 1. 开工前先摸清现状

### 1.1 先看远端，别按本地推断

`git clone` 之后第一条命令是**数清楚远端到底有什么**，而不是直接动手：

```bash
git log --oneline | head -10     # 只有 3 个提交
git tag                          # 空 —— 本地没有任何 tag
git branch -a                    # 只有 main
git ls-remote --tags origin      # 空 —— 远端也没有
```

结论：**这个项目从来没有发过版**。`pyproject.toml` 里写的 `0.1.0` 是一个
从没被发布过的开发版占位符。这一点很重要，因为它直接决定了后面那个决策
（见 [2.3](#2.3)）。

> 为什么这一步不能省：如果只按本地状态推断，就会得出「已经发过 0.1.0」，
> 然后为了「不降版本」去纠结编号 —— 而实际上根本没人见过那个号。

### 1.2 这个项目的「数据在哪」

打包形态的选择完全取决于这个问题，所以开工前必须答清楚：

| 问题 | 答案 |
|---|---|
| 程序自己写文件吗？ | **几乎不写**。只有 `--out` 指定的报告，路径由使用者给 |
| 有哪些必须先存在才能跑的文件？ | `configs/default.yaml` + `rules/` 下 4 个文件 |
| 使用者需要**改**哪些文件？ | 上面这些，以及未来他自己加的规则 |

第三条是全局最关键的一条。整个项目的卖点之一是「**别人可以微调**」——
改 YAML 就行，不用读代码。**这条承诺在打包形态上是有代价的**，
而它直接决定了不能选 onefile（见 [2.1](#2.1)）。

### 1.3 顺带确认的三件事

- **依赖只有一个** `PyYAML`（可选 jieba）。所以体积不是约束，不用为省几 MB
  去做危险的裁剪。
- **`PROJECT_ROOT` 是靠 `__file__` 反推的**：
  `Path(__file__).resolve().parents[2]`。打包时 `__file__` 会变，这是一个已知的雷。
- **CLI 有三个子命令** `scan` / `signals` / `rules`，都靠 `argparse`，
  没有参数时会抛 `SystemExit(2)` —— 双击场景下等于「窗口闪一下就没」。

---

<a id="2"></a>
## 2. 三个决策，和为什么不是另外三个

<a id="2.1"></a>
### 2.1 onedir 而不是 onefile

**这不是「文件数越少越好」的问题，是「数据会不会丢」的问题。**

onefile 每次启动把自己解压到一个**随机临时目录**（`_MEIxxxxxx`），退出即删。
对一个命令行工具来说这通常只是「慢一点」，但这个项目不一样：

> 它的核心用法是**改 `rules/*.yaml` 微调**。
> onefile 下那些文件每次运行都会被重新解压覆盖 —— 使用者改完，下一次就没了。

这不是「体验差」，这是**功能承诺被破坏**：使用者按 README 说的改规则，
改了没反应，而且没有任何报错。

代价：分发一个文件夹而不是单文件，压缩包大几十 KB。换来三件事——

1. 规则看得见、改得动；
2. 启动是秒级的（不用解压）；
3. 排错直观（文件都在那儿，不是藏在临时目录）。

顺带一个：这条决策也解释了为什么资源要放**两处**（见 [2.2](#2.2)）。

<a id="2.2"></a>
### 2.2 资源放两处，且查找顺序固定可打印

```
TideWatch-0.0.1-win64/
├── TideWatch.exe
├── configs/        ← 主用：使用者实际在改的那一份
├── rules/
├── data/sample/
├── _internal/      ← 兜底：同一份资源在这里也放一份
└── ...
```

查找顺序（`src/tidewatch/paths.py`）：

```
TIDEWATCH_HOME 环境变量  →  exe 同级目录  →  包内 _internal  →  用户目录
```

判据是「这个目录里有 `configs/` 或 `rules/`」。**刻意放宽到「存在」，
而不是「`configs/default.yaml` 存在」** —— 因为两种失败方式的好坏完全不同：

| 情况 | 行为 | 为什么这么定 |
|---|---|---|
| 目录**完全不在**（只解压了 exe） | 往下一级找兜底副本 | 让它先能跑起来 |
| 目录**在但不完整**（少了个 yaml） | **停在原地**，由 `doctor` 报 fail | 否则会安静地切到 `_internal` 里那份旧副本 |

第二行是这份设计里最值钱的一条。如果资源目录不完整就往下找，
会得到这样一个结果：**使用者改过的规则明明不生效，程序却一切正常**。
这类「不报错但结果不对」的失败，比崩溃难查得多 —— 崩溃至少有栈。

两处副本加起来 200 KB 左右，不构成负担；而「到底在用哪一份」由
`doctor` 明确打印，不会让人猜。

<a id="2.3"></a>
### 2.3 版本号收敛到 0.0.1，且只有一处

仓库里原来的版本号是 `0.1.0`（pyproject）。而**这次要发的是第一个 exe 发行版**，
编号按 `0.0.1`。

两种做法：

| 做法 | 后果 |
|---|---|
| pyproject 保持 0.1.0，Release tag 用 v0.0.1 | 两处各说一套，版本无法核对 |
| **全部改成 0.0.1，单一来源** | 一致，且以后不会再分叉 |

选第二种。理由不是「哪个号更对」，而是**版本号一旦分叉就彻底失去作用**：
使用者说「我装的是 0.1.0」，你没法知道他说的是哪个文件。

落地方式：

- `src/tidewatch/version.py` 是**唯一**写着版本号的地方；
- `pyproject.toml` 与 `configs/default.yaml` 由测试盯着必须一致；
- exe 文件属性里的 `FileVersion` 也由它派生。

> 这里有个容易忽略的点：一个「从没发布过的版本号」是可以自由重编的。
> 判断依据是「远端有没有人见过」，不是「本地文件里写的多少」。

---

<a id="3"></a>
## 3. 打包实现：spec、入口、图标、版本资源

### 3.1 spec 要进版本库

`packaging/tidewatch.spec` 提交进仓库。它**就是发行产物的定义** ——
不提交的话，「这一版 exe 到底是怎么打出来的」只能靠回忆，
而回忆不出 `exclude` 了哪些模块、隐藏导入了哪些东西。

版本号从 `pyproject.toml` 读，不在 spec 里另写一份：

```python
ROOT = Path(SPECPATH).parent          # noqa: F821 —— SPECPATH 由 PyInstaller 注入

VERSION = re.search(
    r'^version\s*=\s*"([^"]+)"',
    (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M
).group(1)
```

> spec 里**导入的是 PyInstaller 的工具模块，不是 tidewatch 自己**。
> 构建工具不该 import 它正在构建的东西。

关键配置：

```python
a = Analysis(
    [str(ROOT / "packaging" / "entry.py")],
    pathex=[str(SRC)],
    datas=[
        (str(ROOT / "configs"), "configs"),
        (str(ROOT / "rules"), "rules"),
        (str(ROOT / "data" / "sample"), "data/sample"),
    ],
    excludes=[],       # 不排除任何东西
    noarchive=False,
)

exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name=APP,
    upx=False,         # 见下
    console=True,      # 命令行工具必须留控制台
    icon=str(ROOT / "packaging" / "tidewatch.ico"),
    version=_version_resource(),
)

coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=APP)
```

**两个刻意的空白：**

- `excludes=[]`。这个项目的依赖只有 PyYAML，体积本来就不是问题；
  而 `exclude` 是「静默失败」的常见来源 —— 被排掉的模块要到运行时才报错，
  而打包后的报错是「双击没反应」。不值得为几十 MB 冒这个险。
- `upx=False`。UPX 压缩省不了多少体积，却显著提高被杀软误报的概率
  （自解压壳是恶意软件的常见特征）。第一版不值得为这点体积冒险。

### 3.2 入口用一个独立的薄壳

```python
# packaging/entry.py —— 全部内容
from tidewatch.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

为什么不直接把 `src/tidewatch/cli.py` 当入口：

> `python -m tidewatch.cli` / 冻结后以 `__main__` 执行时，
> 同一个文件会**同时以两个名字**存在于 `sys.modules` 里
> （`__main__` 和 `tidewatch.cli`），于是模块级状态各存一份。

这个项目现在没有模块级状态，但那是运气不是设计。用独立薄壳让这个坑永远不会出现。
薄壳里**只做 import 再调用**，不写任何逻辑 —— 逻辑写在包里，才测得到。

### 3.3 图标用代码画

不找图、不下载素材，30 行 Pillow 生成：

```python
def _draw_waves(draw, size):
    for index, (color, y_ratio, amp_ratio, width_ratio) in enumerate((
        (WAVE_SOFT, 0.56, 0.085, 0.072),
        (WAVE,      0.71, 0.105, 0.098),
    )):
        amp, base = size * amp_ratio, size * y_ratio
        width = max(1, round(size * width_ratio))
        left, right = size * 0.085, size * 0.915    # 左右留边距
        points = []
        for step in range(steps + 1):
            t = step / steps
            x = left + t * (right - left)
            # 两个频率叠加 → 「潮」的不规则感，而不是一条规整的波纹
            phase = math.sin(t * math.pi * 2 + index * 0.9) * amp
            phase += math.sin(t * math.pi * 4 + index * 1.7) * amp * 0.35
            points.append((x, base + phase))
        draw.line(points, fill=color, width=width, joint="curve")
        # 两端补圆头：line 的 joint 只管拐点，端点默认是平的
        for x, y in (points[0], points[-1]):
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
```

图案：深蓝圆角底 + 两道青色潮线 + 右上角一个红点（「被标出来的那一个」）。
不做文字 —— 16×16 下任何文字都是糊的。

**踩到的两个小坑：**

1. 一开始线画到画布边缘，圆角遮罩把两端切出**毛刺** —— 看起来像渲染坏了。
   改成左右各留 8.5% 边距。
2. `ImageDraw.line` 的 `joint="curve"` 只处理**拐点**，端点默认是平的，
   细线宽下显得像被截断。两端各补一个圆。

生成多尺寸（16/24/32/48/64/128/256）写进一个 `.ico`。少了 256 的话，
资源管理器大图标视图会把它拉伸到模糊。

`.gitattributes` 里本来就有 `*.ico binary`，所以图标进版本库不会被换行符处理破坏。

### 3.4 版本资源：不用运行就能核对版本

```python
def _version_resource() -> VSVersionInfo:
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=tuple(VERSION_PARTS[:4]), prodvers=..., mask=0x3F, ...),
        kids=[StringFileInfo([StringTable("080404B0", [          # 简体中文
            StringStruct("FileDescription", "TideWatch · 观潮 —— 网络水军与协同行为识别引擎"),
            StringStruct("FileVersion", VERSION),
            StringStruct("ProductVersion", VERSION),
            StringStruct("OriginalFilename", f"{APP}.exe"),
            StringStruct("LegalCopyright", "MIT License"),
        ])]), VarFileInfo([VarStruct("Translation", [2052, 1200])])],
    )
```

它的价值只有一个，但很实在：**右键 → 属性 → 详细信息**里能看到文件版本。
使用者报问题时说的版本号因此**可以被现场核对**，而不是只能靠他说。

实测（系统自带 `Get-Item`）：

```
FileVersion      : 0.0.1
ProductVersion   : 0.0.1
ProductName      : TideWatch
FileDescription  : TideWatch · 观潮 —— 网络水军与协同行为识别引擎
LegalCopyright   : MIT License
```

---

<a id="4"></a>
## 4. 打包之后才会出现的三类失败

**这一节是整份报告里最值钱的部分。**

打包是「问题放大器」：

| | 源码运行 | 打包成 exe |
|---|---|---|
| 报错 | 控制台红字 + traceback | **双击没反应** |
| 缺依赖 | `pip install` 一行 | 要么内置，要么使用者永远修不好 |
| 路径 | 就是当前目录 | `__file__` 指向解压出来的临时目录 |

所以下面三件事必须在这一轮里一起做掉。**每一条都做了反证**（把修复改回旧写法、
重新构建、在真实产物上跑），因为「我修了它」是一个没有信息量的说法。

<a id="4.1"></a>
### 4.1 控制台编码：一个 emoji 让打包版直接崩

**根因**：冻结之后 `stdout` 的编码由系统区域设置决定，简体中文 Windows 上是
GBK。而样例数据里有 `❤️`（U+2764）—— 一旦报告里把它带出来就是 `UnicodeEncodeError`。

先在源码态确认这个危险是真的：

```
$ PYTHONIOENCODING=gbk python -c "print('加薇❤️信')"
UnicodeEncodeError: 'gbk' codec can't encode character '\u2764' in position 2
```

**反证**：把 `_setup_console()` 改回空操作，重新构建，在打包产物上跑：

```
$ ./TideWatch.exe scan data/sample/sample.jsonl --limit 0 --min-level weak >out 2>err
exit=3

$ head -3 err
[error] 输出的编码异常…（乱码，因为 stderr 自己也是 GBK）
[error] 详细堆栈已写入：C:\Users\<用户>\AppData\Local\TideWatch\tidewatch-crash.log

$ grep -c "❤" out
0
```

崩溃日志（**注意这是打包版自己的日志，不是我在源码里加的断点**）：

```
时间: 2026-10-16T09:13:13+08:00
版本: 0.0.1
运行形态: 打包 exe
命令行: ...\TideWatch.exe scan data/sample/sample.jsonl --limit 0 --min-level weak
Python: 3.13.14 (main, Jun 11 2026, ...) [MSC v.1944 64 bit (AMD64)]
资源根: ...\TideWatch-0.0.1-win64

Traceback (most recent call last):
  File "tidewatch\cli.py", line 618, in main
  File "tidewatch\cli.py", line 582, in _run
UnicodeEncodeError: 'gbk' codec can't encode character '\u2764' in position 9663: illegal multibyte sequence
```

**修法**（`_setup_console()`，任何输出之前调用）：

```python
if os.name == "nt":
    with contextlib.suppress(Exception):
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)   # 让终端按 UTF-8 渲染
for stream in (sys.stdout, sys.stderr):
    with contextlib.suppress(Exception):
        stream.reconfigure(encoding="utf-8", errors="replace")   # 编码改不动也不崩
```

两步都做：只改代码页不改流编码，机器可读的输出仍然是 GBK；
只改流编码不改代码页，终端会把 UTF-8 字节按 GBK 渲染成乱码。

**恢复后同一命令**：`exit=0`，`grep -c "❤"` 得到 1。

> 一个工具因为「数据里有 emoji」而崩掉，是最冤的一类事故。
> 而它**只在打包版复现** —— 源码态跑测试永远发现不了。

<a id="4.2"></a>
### 4.2 资源路径：旧写法「碰巧是对的」

这是整份报告里最反直觉的一条。

原来的写法是：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
```

在 onedir 打包后：

```
exe:            <app>\TideWatch.exe
纯 Python 模块:  <app>\_internal\tidewatch\config.py   ← __file__
parents[0] =    <app>\_internal\tidewatch
parents[1] =    <app>\_internal
parents[2] =    <app>              ← 恰好命中！
```

**`_internal` 刚好比 exe 低一层，所以旧写法在「同级资源齐全」时是对的。**
如果我没做反证，会写成「我修复了一个打包后必然崩溃的路径 bug」——
而那是假的。

**反证**：把 `project_root()` 改回旧写法，重新构建，实测两种场景：

场景一（同级资源齐全）—— 旧写法**正常工作**：

```
[ok] 资源根        ...\TideWatch-0.0.1-win64
[ok] 配置文件      ...\TideWatch-0.0.1-win64\configs\default.yaml
结论：warn —— 可以正常使用
```

场景二（同级资源被删，触发兜底）—— **判断它的地方和使用它的地方各找到一个目录**：

```
[ok] 资源根        ...\TideWatch-0.0.1-win64\_internal
[ok] 配置文件      ...\TideWatch-0.0.1-win64\_internal\configs\default.yaml
[fail] 配置加载      找不到配置文件: ...\TideWatch-0.0.1-win64\configs\default.yaml
结论：fail —— 有项目不可用
```

上面两行 `[ok]` 来自新的 `paths.resource_root()`，那行 `[fail]` 来自旧的
`config.project_root()`。**同一份配置，同一个进程里，报出两个不同的路径** ——
这种输出比崩溃更难查，因为每一行单独看都是对的。

**再补一个反证**：onefile 形态（临时做一个探针 spec，只把 `COLLECT` 换成
`EXE(..., a.binaries, a.datas, ...)`）：

```
[ok] 包内解压目录  C:\Users\<用户>\AppData\Local\Temp\_MEI000040c42
[ok] 资源根        C:\Users\<用户>\AppData\Local\Temp\_MEI000040c42
[fail] 配置加载      找不到配置文件: C:\Users\<用户>\AppData\Local\Temp\configs\default.yaml
```

旧写法指到了**随机临时目录的父目录**。所以准确的说法是：

> 旧写法在 onedir 6.x + 同级资源齐全时碰巧对；
> 一旦回落到兜底副本、或者换成 onefile，就会指到别的地方。

**修法**：把判断收到一个模块里（`src/tidewatch/paths.py`），
`config.py` 里那句改成 `paths.resource_root()`，并且**每次调用重新解析**
而不是 import 时算一次（`TIDEWATCH_HOME` 和测试里的临时目录都要能立刻生效）。

```python
# src/tidewatch/config.py
def project_root() -> Path:
    """资源根：源码态是仓库根，冻结态是 exe 同级目录。
    每次调用都重新解析，而不是在 import 时算一次。"""
    return paths.resource_root()

PROJECT_ROOT = project_root()          # 兼容旧引用
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.yaml"
```

还有一个易感点一起改掉了：`config.py` 里原来写的是
`from tidewatch.paths import resource_root`（把名字钉死在导入时刻），
改成 `from tidewatch import paths` + `paths.resource_root()`
——**走模块属性**，否则测试里替换这一层是不生效的。

<a id="4.3"></a>
### 4.3 双击：不能「闪一下就关」

双击 exe 等于**无参数运行**。原来的行为是 `argparse` 报「缺少必需参数」
→ `SystemExit(2)` → 新开的控制台立刻关闭。使用者看到的是窗口闪了一下。

> 这是打包后**最糟的失败方式**：连「哪里错了」都看不到。
> 源码态下同一件事只是终端里一行红字，所以测试和本地调试都不会暴露它。

**修法**：判断这次是不是「双击」拉起来的，是的话打印用法并等一次回车。

```python
def _launched_from_explorer() -> bool:
    """判据是 Windows 的控制台进程表：新开一个控制台时里面只有我们自己，
    从已有终端启动时里面至少还有一个父 shell。"""
    if os.name != "nt":
        return False
    with contextlib.suppress(Exception):
        buf = (ctypes.c_uint * 8)()
        count = ctypes.windll.kernel32.GetConsoleProcessList(buf, 8)
        return 0 < count <= 1
    return False
```

**为什么不用「看有没有参数」**：在终端里敲一个光秃秃的 `tidewatch` 同样没有参数，
但那时候使用者就在终端前，停下来等回车只会烦人。

**实测**（用 `Start-Process` 模拟双击）：

```
结果: 仍在运行  ← 说明停在等回车（好）
```

对照：修复前，同一操作 4 秒后进程早就退出了。

### 4.4 顺带：异常出口

三层兜底，都在 `main()` 里：

```python
except SystemExit:
    raise                       # argparse 的正常退出路径，不当崩溃拦
except KeyboardInterrupt:
    print("\n[中断] 已取消", file=sys.stderr); return 130
except Exception as exc:
    print(f"\n[error] {_friendly_error(exc)}", file=sys.stderr)
    log = _write_crash_log(exc)          # 落到 %LOCALAPPDATA%\TideWatch\
    print(f"[error] 详细堆栈已写入：{log}", file=sys.stderr)
    print("[error] 运行 `tidewatch doctor` 可以看环境哪里不对。", file=sys.stderr)
    if not paths.is_frozen():
        raise                            # 源码态直接抛出去，开发时不被兜底掩盖
    return 3
```

`_friendly_error()` 的顺序是有讲究的 —— **先判「缺组件」，再判文件、编码，
最后兜底**：

```python
if isinstance(exc, ModuleNotFoundError):
    return "缺少运行组件 …。这是打包本身的问题，不是使用问题 ——
            请重新下载发行包，或改用源码方式运行。"
```

> 这里最容易犯的错是给一个**看起来合理但方向错误**的建议：
> 把「缺模块」翻译成「检查网络 / 换镜像」。镜像补不上一个没打进包的模块 ——
> 使用者会照着一个修不好的方向折腾很久。
> 这类建议比「没有建议」更糟：没有建议他会来问，错误建议会让他默默流失。

---

<a id="5"></a>
## 5. 自检：让「能不能用」变成一个能被回答的问题

新增 `tidewatch doctor`（三档结论 `ok` / `warn` / `fail`，`fail` 时退出码 1）：

```
tidewatch 0.0.1 · 自检
Python 3.13.14 · Windows 11

[ok]   运行形态      打包 exe
[ok]   程序目录      ...\TideWatch-0.0.1-win64
[ok]   包内解压目录  ...\TideWatch-0.0.1-win64\_internal
[ok]   资源根        ...\TideWatch-0.0.1-win64
[ok]   用户目录      C:\Users\<用户>\AppData\Local\TideWatch
[ok]   程序目录可写  是 —— configs/ 与 rules/ 可以直接改
[ok]   配置文件      ...\configs\default.yaml
[ok]   配置加载      指纹 c4cea6ed511a
[ok]   规则库        话术 5 组 / 55 条 · 折叠 21 条 · 正则 7 条 · 停用词 119 条；...（4 个文件齐全）
[ok]   信号          注册 10 个 · 启用 10 个
[warn] 中文分词      jieba 未安装 —— 已降级为字符 bigram，功能不受影响（发行包刻意不带它）
[ok]   样例数据      ...\data\sample\sample.jsonl（193 条）
[ok]   最小端到端    抓到 2 个可疑目标，正常样本未误报

结论：warn —— 可以正常使用，上面标 [warn] 的行只是提示。
```

### 5.1 「配置加载成功」≠「能出结论」

最后那行 `最小端到端` 是刻意加的。它真的拿两条探针数据跑一遍完整流水线：

```python
_DOCTOR_PROBE = [
    {"item_id": "probe-normal", "text": "这个思路挺清楚的，回头我也试试看效果怎么样", ...},
    {"item_id": "probe-spam",   "text": "需要的话加薇❤️信，详情私聊我，名额有限", ...},
]
```

一条正常、一条明显导流。断言有三层：

```python
if not flagged:
    record("最小端到端", _FAIL, "样本里的导流话术一条都没被抓到，引擎可能没在工作")
elif bad:   # 正常探针被误报了
    record("最小端到端", _WARN, f"…但正常样本也被误报（{bad[0].score:.1f} 分）")
else:
    record("最小端到端", _OK, f"抓到 {len(flagged)} 个可疑目标，正常样本未误报")
```

**为什么必须有这一项**：空的话术库、权重全部回落默认值、流水线没接上 ——
这些都能让「配置加载成功」，却什么都判不出来。
「对象造出来了」和「现在能干活」是两件事，它们的差集正是
「看着配好了、用起来没反应」的全部来源。

### 5.2 一个只会说 ok 的自检等于没有自检

所以测试里有一半是**验证它会报坏**：

```python
def test_doctor_warns_when_a_rule_file_is_missing(fake_root, capsys):
    """少一个规则文件不会崩，但对应的判断会静默失效 —— 必须报出来。
    这条测试的价值在于它**能报坏**：全绿的测试证明不了自检是活的。"""
    (fake_root / "rules" / "patterns.yaml").unlink()
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "patterns.yaml" in out
    assert "结论：warn" in out

def test_doctor_fails_when_rules_are_entirely_missing(...):
    assert main(["doctor"]) == 1
    assert "规则库整体缺失" in out and "结论：fail" in out
```

### 5.3 fail 时必须给出能修好的下一步

```
结论：fail —— 有项目不可用，请先处理上面标 [fail] 的行。
       最常见的两条原因是：压缩包没有解压完整、只把 exe 单独拷了出来。
       引擎需要 exe 同级的 configs/ 与 rules/ 一起存在。
```

### 5.4 只读安装位置：发现问题顺手给一条路

`doctor` 检测到「程序目录不可写」时，会把默认规则**复制到用户目录**并给出用法。
这不是顺手，是刻意的：**发现了问题但不给出能修好的方向，等于没发现。**

实测（用 ACL 拒绝写入 `%TEMP%` 下的副本）：

```
[warn] 程序目录可写  否 —— 已复制默认规则到 C:\Users\<用户>\AppData\Local\Temp\tw-seed4，
                     然后设 TIDEWATCH_HOME 指向它即可微调
结论：warn —— 可以正常使用，上面标 [warn] 的行只是提示。

--- 铺到用户目录的 ---
\configs\default.yaml
\data\sample\sample.jsonl
\rules\evasion.yaml
\rules\patterns.yaml
\rules\phrases.yaml
\rules\stopwords.txt
```

`seed_user_root()` 有一条硬规则：**已经存在的文件一律不覆盖**。
覆盖等于把使用者微调好的话术库吃掉，而且不报错。有测试守着。

---

<a id="6"></a>
## 6. 构建脚本：一条命令做四件事

```bash
python scripts/build_exe.py            # 或 make exe
```

四个步骤，缺一不可：

1. **构建** —— 调 PyInstaller，配置在已进版本库的 spec 里；
2. **补齐同级资源** —— `configs/` `rules/` `data/sample/` 和各份文档复制到 exe 旁边；
3. **对真实产物做冒烟** —— 不是断言「构建返回了 0」；
4. **打包 + 校验和** —— 确定性 zip。

### 6.1 冒烟必须打真实 exe

```python
def smoke(release: Path) -> None:
    exe = release / "TideWatch.exe"

    out = run([str(exe), "--version"], capture_output=True, text=True, encoding="utf-8").stdout
    assert version in out

    out = run([str(exe), "doctor"], ...).stdout
    assert "结论：" in out, ...
    assert "[fail]" not in out, ...
    assert "打包 exe" in out          # doctor 认出自己在跑打包版

    out = run([str(exe), "scan", str(sample), "--limit", "3", "--out", str(report)], ...).stdout
    assert "读取" in out and "团伙" in out
    assert report.is_file() and report.stat().st_size > 0     # 报告真的落盘了
```

三个细节：

- **`encoding="utf-8"` 显式给**。不指定的话 Windows 上会用 GBK 解码子进程输出，
  中文全部变成乱码，断言会以「找不到『结论：』」的形式失败 —— 看起来像功能坏了。
- **断言只卡在「能干活」的最低线**。卡太死会让合理的调参变成红叉，
  最后逼着后人把这套检查删掉，那还不如没有。
- **三条断言都打真实 exe，不是调函数**。要求 `--out` 的报告真的落到磁盘上 ——
  渲染逻辑曾经因为读了一个被改名的统计键而崩溃，只有真跑一次才会暴露。

### 6.2 确定性打包

```python
ZIP_STAMP = (1980, 1, 1, 0, 0, 0)     # zip 格式能表示的最早时间

def zip_dir(src: Path, dst: Path) -> str:
    files = sorted(p for p in src.rglob("*") if p.is_file())    # 顺序固定
    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            info = zipfile.ZipInfo(arcname, date_time=ZIP_STAMP)  # 时间戳写死
            ...
    return hashlib.sha256(dst.read_bytes()).hexdigest()
```

顺序 + 时间戳是「同一份目录连打两次 SHA 相同」的充分条件。
不这么做的话，校验和只能核对当次，没法印出来给别人用。

### 6.3 一个小坑：`with_suffix` 会吃掉目录名里的点

```python
release = DIST / "TideWatch-0.0.1-win64"
release.with_suffix(".zip")        # → TideWatch-0.0.zip   ← 错！
```

`Path.suffix` 把 `.1-win64` 当成了后缀。实测第一次构建产出的就叫
`TideWatch-0.0.zip`。改成显式拼字符串：

```python
archive = release.parent / f"{release.name}.zip"
```

> 这是 `pathlib` 的一个反直觉点：它按「最后一个点」切后缀，
> 而版本号里正好有不止一个点。

---

<a id="7"></a>
## 7. 校验和的口径

发行说明里必须写清**这个校验和能核对什么、不能核对什么**：

| | 是否逐字节确定 | 说明 |
|---|---|---|
| **打包（zip）这一步** | ✅ 确定 | 同一份 `dist/` 连打两次 SHA 相同（用 `--verify-reproducible` 实测） |
| **PyInstaller 构建本身** | ❌ 不确定 | 同一份源码连构建两次，产物的 SHA 通常不同 |

所以：

> **这个校验和用来核对下载，不能用来核对构建。**

不写这一句的后果：有人自己重跑一遍构建，发现 SHA 对不上，
然后来问「你们发的包是不是被人动过」—— 而那是正常现象。

<a id="7.1"></a>
### 7.1 「不确定」到什么程度：五份 SHA 实据

同一份源码（`v0.0.1`）的 zip 在不同轮次里的 SHA256：

| 来源 | SHA256 |
|---|---|
| 第一轮本机构建 | `92814a3e54aab3…` |
| 第二轮本机构建 | `51151950d33f62…` |
| 第二轮 cp1252 模拟构建 | `ec610f6bbe9f0e…` |
| 本地最新一次完整构建 | `e77b190206367f…` |
| **CI 构建（就是 Release 里那个）** | `410796b5da8d7d…` |

五个值全不一样 —— 这不是异常，是 PyInstaller 的常态：它把构建时间、
临时路径等信息写进了产物。**而 `--verify-reproducible` 每次都是通过的**，
因为那一条只承诺「同一份 `dist/` 连打两次相同」。两件事分开说清，
才不至于让使用者以为包被人动过。

<a id="7.2"></a>
### 7.2 `.sha256` 的行尾必须是 LF（v0.0.1 发出去了 CRLF）

这个文件的唯一用途是喂给校验工具，所以它得是标准 `sha256sum` 格式：
`<64 位十六进制><两空格><文件名><LF>`。

v0.0.1 发出去的那一份**是 CRLF 的**。这不是猜的，是把发布件下载下来跑出来的：

```
$ cat TideWatch-0.0.1-win64.zip.sha256
410796b5da8d7d56184d0591a6ae4562f2a9fc419bf73c7ac6c48c32295715b6  TideWatch-0.0.1-win64.zip

$ sha256sum TideWatch-0.0.1-win64.zip
410796b5da8d7d56184d0591a6ae4562f2a9fc419bf73c7ac6c48c32295715b6 *TideWatch-0.0.1-win64.zip
```

**哈希值本身完全一致**，但拿它去自动核对就炸：

```
$ sha256sum -c TideWatch-0.0.1-win64.zip.sha256
sha256sum: 'TideWatch-0.0.1-win64.zip'$'\r': No such file or directory
sha256sum: WARNING: 1 listed file could not be read
```

行尾那个 `\r` 被当成了文件名的一部分。

**根因**：`Path.write_text` 默认把 `\n` 翻译成 `os.linesep`。CI 的 runner 是
Windows，写出来就是 CRLF。这个翻译是「帮你适配本机」的设计，
但它在这里恰好把机器可读的文件弄成了机器读不了的。

**影响范围要说准，不能夸大**：发行说明里给的核验方式是 PowerShell
`Get-FileHash` + 人工比对，**那条路不受影响**，所以文档里的承诺仍然成立。
受影响的是 Linux / macOS / WSL / Git Bash 上标准的 `sha256sum -c` ——
而那是这份文件存在的全部意义。

**修法**（`write_checksum()`，显式指定行尾）：

```python
def write_checksum(archive: Path, digest: str) -> Path:
    checksum = archive.parent / f"{archive.name}.sha256"
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    return checksum
```

`newline="\n"` 不是可有可无的修饰。配一条**盯字节**的测试
（`test_checksum_file_uses_lf_not_crlf`）：文件里不许出现 `\r`。

> 「内容对」和「能用」是两码事，这个缺陷正好长在两者的缝里。
> 只断言「哈希值等于多少」的测试**永远抓不到它**。

**关于已发布的 v0.0.1**：这个修复**没有**随 v0.0.1 发布。改它要移动一个
已经发布的 tag，而那次发布的产物是可用的、哈希值也是对的 ——
**已发布的版本不该被改写**。修复留在 `main` 上，跟下一个版本走。

---

<a id="8"></a>
## 8. 发行流水线：从红到绿

**这一节记录的是第一轮报告写完之后的真实遭遇。**
第一轮结束时我以为流水线是通的（报告里当时写的就是「CI 绿 + Release 带 zip
与校验和」）—— 那是**错的**。实际跑出来是红的，而且当时手上什么线索都没有。

### 8.1 症状：只有一句「exit code 1」

```
run    38834400674   Release      failure
job    116760147053  构建 Windows 发行包   failure
step   [7] 构建发行包（含对产物的冒烟检查）  01:19:10 → 01:19:19   ← 9 秒
```

**9 秒。** 而本机单跑这一个构建步骤要 15.7 秒（PyInstaller 那一步）。
CI 的机器确实更快，但连构建都跑不完的量级是清楚的：**它死在很早的位置。**

更麻烦的是看不到原因：

- 作业日志的下载接口 `…/actions/jobs/{id}/logs` **需要仓库权限** → 403。
- 公开可读的只有 annotations，而里面只有一句
  `Process completed with exit code 1.`

也就是说：**知道它挂了，但不知道它说了什么。**

### 8.2 先把日志搬到公开可读的地方

不靠猜的第一步，是让这次的失败原因**下次一眼可见**。

GitHub 的 `::error::` 注解（annotation）是**公开可读**的，而作业日志不是。
所以把日志尾部、环境快照、依赖版本、文件清单全塞进注解：

```powershell
$log = python scripts/build_exe.py --verify-reproducible 2>&1 | Out-String -Stream
$code = $LASTEXITCODE
$log | ForEach-Object { Write-Output $_ }
if ($code -ne 0) {
  $snap = python -c "import sys,platform;print('py='+sys.version.split()[0]);…"
  $pi   = (python -m pip show pyinstaller 2>&1 | Select-String '^Version:').Line
  $tail = (($log | Select-Object -Last 40) -join ' ~~ ')
  Write-Output "::error::exit=$code | $($snap -join ' ; ') | $pi | … | TAIL: $tail"
  exit $code
}
```

**这里踩到一个必须处理的前提**：光加这段代码还不够 —— 它可能根本跑不到。
读了 `actions/runner` 里的 `ScriptHandlerHelpers.cs`，确认 GitHub 给每个
`pwsh` 步骤**自动预置**一句 `$ErrorActionPreference = 'stop'`，末尾再追加
`exit $LASTEXITCODE`：

```csharp
case "pwsh":
    var prepend = "$ErrorActionPreference = 'stop'";
    var append = @"if ((Test-Path -LiteralPath variable:\LASTEXITCODE)) { exit $LASTEXITCODE }";
```

原生命令一旦非零退出，整步当场中断，诊断块**没有机会执行**。
所以在步骤开头显式覆盖成「不中断、自己读 `$LASTEXITCODE`」：

```powershell
$ErrorActionPreference = 'Continue'
if ((Test-Path -LiteralPath variable:\PSNativeCommandUseErrorActionPreference)) {
  $PSNativeCommandUseErrorActionPreference = $false
}
```

另外两处补强，都是为了让「失败原因」不再被吞掉：

- `build_exe.py` 的 `run()` 里 `capture_output=True` 那几处，失败时把子进程的
  stdout/stderr **补印出来**。否则 `CalledProcessError` 只会告诉你
  「returned non-zero exit status 1」，而「exe 为什么退出码非 0」恰好是看不到的那个东西。
- 给构建脚本加 `[stage]` 阶段标记（`[stage] PyInstaller 构建（累计 0.3s）`），
  这样**光看日志尾部就知道死在哪一步**，不必把整份日志捞回来。
- 顺带把「exe 能不能构建」纳入 CI（`ci.yml` 新增 `package` 作业）。
  理由很直接：**打包坏掉的表现是「双击没反应」，源码侧的测试一个都不会红。**
  只在发版那一刻才第一次构建，等于把发现问题的时机推到了最不该出问题的时候。

### 8.3 拿到回溯：根因是 cp1252

诊断上线后，注解里给出了完整回溯：

```
[fail] 构建中断，完整回溯如下：
Traceback (most recent call last):
  File "D:\a\TideWatch\TideWatch\scripts\build_exe.py", line 268, in main
    stage("PyInstaller 构建")
  File "D:\a\TideWatch\TideWatch\scripts\build_exe.py", line 52, in stage
    print(f"\n[stage] {name}（累计 {…}s）", flush=True)
  File "C:\hostedtoolcache\windows\Python\3.13.16\x64\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input, self.errors, encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode characters in position 22-26: character maps to <undefined>
```

注解里还带了环境快照，一眼看清了差异：

```
py=3.13.16 ; exe=C:\hostedtoolcache\windows\Python\3.13.16\x64\python.exe
plat=Windows-2025Server-10.0.26100-SP0 | Version: 6.22.3
```

**根因**：GitHub 的 Windows runner 是 **en-US**，`stdout` 的编码是
**cp1252** —— 这个编码**根本表示不了汉字**。而构建脚本的每条提示都是中文。
脚本死在 `main()` 的第一条中文 print 上。

**为什么本地永远跑不出来**：简体中文 Windows 的 `stdout` 是 GBK，
而 **GBK 恰好能编码汉字**。所以同一个脚本在中文机器上跑一万次都正常。

> 这和第 [4.1](#4.1) 节那条是**同一个病根的两个面**：那边是运行时输出崩溃
> （数据里有 `❤️`），这边是**构建工具自己的输出**崩溃。
> 上一轮教会了 CLI 不要假设控制台能编码，这一轮才知道构建脚本也得守同一条规矩。
> 两处都只在「别人的机器上」复现。

顺带看清一个细节：`stderr` 默认是 `backslashreplace`（所以注解里那行
`[fail] 构建中断` 显示成了 `[fail] \u6784\u5efa\u4e2d\u65ad`），**不会崩**；
真正会崩的是 `stdout`（`strict`）。修复要把两个流一起切过去，
但**崩溃点只在 stdout**。

### 8.4 复现：把对方的机器搬过来

不等 CI 报信，本地直接构造敌意条件：

```bash
$ PYTHONIOENCODING=cp1252 python scripts/build_exe.py --skip-smoke --no-zip
UnicodeEncodeError: 'charmap' codec can't encode characters in position 22-26
  File ".../scripts/build_exe.py", line 52, in stage
  File ".../encodings/cp1252.py", line 19, in encode
```

**与 CI 的回溯逐字相同**——同一个文件、同一行、`cp1252.py` 第 19 行。
复现成立，结论才敢下。

修法（三个脚本各自在 `main()` 的第一条语句处调用）：

```python
def _setup_console() -> None:
    if os.name == "nt":
        with contextlib.suppress(Exception):
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)   # 让终端按 UTF-8 渲染
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            stream.reconfigure(encoding="utf-8", errors="replace")
```

**为什么三个脚本各写一份、不抽公共模块**：`scripts/` 下每个文件都是能直接
`python scripts/xxx.py` 跑起来的独立工具，一个跨文件的 import 会跟着
`sys.path` 一起变脆（测试用 importlib 直接加载脚本时就断过一次）。
十行的重复，换每个脚本都能单独拿走，这笔账划算。

修复后在**同一个敌意编码下**完整跑通：

```
$ PYTHONIOENCODING=cp1252 python scripts/build_exe.py --verify-reproducible
[stage] PyInstaller 构建（累计 0.3s）
构建完成，用时 15.6s
[stage] 对真实产物做冒烟（累计 15.9s）
  ok  --version → tidewatch 0.0.1
  ok  doctor → 结论：warn —— 可以正常使用，…
  ok  scan → 读取 193 条发言 · 160 个账号 · 10 个话题
发行目录 …：55 个文件 · 22.3 MB
压缩包   TideWatch-0.0.1-win64.zip · 8.9 MB
可复现   两次打包 SHA 一致 ✔
EXIT=0
```

### 8.5 反证：这些测试不是摆设

修的同时写了守卫（`tests/test_build_script.py`，12 条）。**每一条都做了反证**
（把修复摘掉，确认它真会红）：

| 反证 | 怎么摘 | 结果 |
|---|---|---|
| 行为 | `module._setup_console = lambda: None` | ✅ 探针在 cp1252 下 `UnicodeEncodeError`，退出码非 0 |
| 位置 | `main()` 第一条语句改成 `pass` | ✅ `--help` 直接崩；位置断言同时失败 |
| 行尾 | 去掉 `newline="\n"` | ✅ 打出的就是发布件里那份 `…zip\r\n` |
| 敌意条件本身 | —— | 断言里**先验证** `PYTHONIOENCODING=cp1252` 真的生效，否则这条反证无效 |

最后一条值得单说：反证的**前提条件**也要被验。如果某个 Python 版本忽略了
`PYTHONIOENCODING`，探针永远不会崩，那条「摘掉修复必须红」的断言就变成了
永不触发的摆设 —— 测试全绿，问题还在。

### 8.6 结果

```
run 38836403857   Release   success
  安装依赖 => success        静态检查 => success      测试 => success
  构建发行包（含对产物的冒烟检查） => success
  核对版本号与 tag 一致 => success
  存成 CI artifact => success                 准备发行说明 => success
  发布 Release => success
```

**10 个步骤全绿，Release 首次发布成功。**

### 8.7 tag 移动记录（诚实记账）

`v0.0.1` 这个 tag 在本次会话里**移动过一次**，理由是充分的：

| | 从 | 到 | 为什么可以移 |
|---|---|---|---|
| 移动 1 | `dad2282` | `a5d7d85` | 那次发布**没有产出任何 Release**（流水线在构建那步就挂了），所以没有已发布的产物会被改写 |

**第二次没有移**（尽管那时已经知道 `.sha256` 是 CRLF）：因为第二次的失败
**已经产出了 Release**，哈希值也是对的。**已经发布的版本不该被改写** ——
哪怕下载数是 0、哪怕只隔了几分钟。这条规矩一旦松动，tag 就不能再用来
指认「我给出去的是哪一份」。

移动的理由和范围写进了 tag 的注解里，不只存在于这次对话里。

---

<a id="9"></a>
## 9. 验收：把已发布的包下载下来真跑一遍

**「流水线是绿的」和「下载到的东西是好的」是两件事。** 前者只说明构建脚本
返回了 0；后者是使用者真正会遇到的东西。所以验收必须从 Release 页面开始，
而不是从 `dist/` 开始。

### 9.1 下载 + 按发布的校验和核对

```bash
$ base=https://github.com/whyao56/TideWatch/releases/download/v0.0.1
$ curl -sSL -O $base/TideWatch-0.0.1-win64.zip
$ curl -sSL -O $base/TideWatch-0.0.1-win64.zip.sha256
$ ls -l
-rw-r--r-- 9931466 TideWatch-0.0.1-win64.zip
-rw-r--r--      93 TideWatch-0.0.1-win64.zip.sha256
```

校验和的值**一致**（`410796b5da8d7d…`）—— 但就在这一步撞上了
[7.2](#7.2) 那个 CRLF 缺陷。**这个缺陷是验收带出来的，不是想出来的**：
如果验收只跑「构建脚本成功了没」，它永远浮不上来。

### 9.2 zip 结构审查

```python
顶层条目: ['TideWatch-0.0.1-win64']        # 单一顶层目录
条目总数: 79
  OK  TideWatch.exe            OK  configs/default.yaml
  OK  rules/ (4 个条目)         OK  data/sample/sample.jsonl
  OK  README.md                OK  LICENSE               OK  使用说明.md
可疑路径条目: 无                            # 没有绝对路径、没有 ../
非 ASCII 条目: ['TideWatch-0.0.1-win64/使用说明.md']
  UTF-8 标志位: [True]                      # 中文文件名在各平台都能正确解出
```

三件事都是刻意的：**单一顶层目录**（解压时不会把文件撒到当前目录）、
**没有上跳路径**（解压不会写出目标目录）、**中文文件名带 UTF-8 标志位**
（zip 规范里不带这个位，Linux 上会变成乱码名）。

### 9.3 实跑已发布的 exe

```
$ ./TideWatch.exe --version
tidewatch 0.0.1                                       EXIT=0

$ ./TideWatch.exe doctor
[ok]   运行形态      打包 exe
[ok]   程序目录      …\TideWatch-0.0.1-win64
[ok]   包内解压目录  …\TideWatch-0.0.1-win64\_internal
[ok]   资源根        …\TideWatch-0.0.1-win64
[ok]   用户目录      C:\Users\<用户>\AppData\Local\TideWatch
[ok]   程序目录可写  是 —— configs/ 与 rules/ 可以直接改
[ok]   配置文件      …\configs\default.yaml
[ok]   配置加载      指纹 c4cea6ed511a
[ok]   规则库        话术 5 组 / 55 条 · 折叠 21 条 · 正则 7 条 · 停用词 119 条
[ok]   信号          注册 10 个 · 启用 10 个
[warn] 中文分词      jieba 未安装 —— 已降级为字符 bigram…（发行包刻意不带它）
[ok]   样例数据      …\data\sample\sample.jsonl（193 条）
[ok]   最小端到端    抓到 2 个可疑目标，正常样本未误报
结论：warn —— 可以正常使用，上面标 [warn] 的行只是提示。   EXIT=0

$ ./TideWatch.exe scan data/sample/sample.jsonl --limit 3 --out acceptance-report.md
读取 193 条发言 · 160 个账号 · 10 个话题
判定对象 357 个（其中 271 个未触发任何信号）
结果：正常 302 · 弱嫌疑 27 · 强嫌疑 28
      单条 8 · 账号 43 · 团伙 4
── 【强嫌疑】 73.1 分 · group · coordination.cluster @ video-1001
   [协同] coordination.cluster  「video-1001」下有 8 条发言高度雷同（来自 8 个账号）
── 【强嫌疑】 62.1 分 · item · 需要的话加薇 信，详情私聊我
   [文本] text.keyword  命中话术/规则：导流(1)
   [文本] text.evasion  存在刻意规避写法：加微信
报告已写入 acceptance-report.md                    EXIT=0
                                                    文件 22430 字节
```

唯一的 `[warn]` 是 jieba 未安装 —— 而那是**刻意设计**的（发行包不带它，
降级路径有测试守着）。所以这个 `warn` 是预期结果，不是缺陷。

### 9.4 版本资源：不用运行就能核对

```
$ (Get-Item TideWatch.exe).VersionInfo
FileVersion      = 0.0.1        ProductVersion   = 0.0.1
ProductName      = TideWatch
FileDescription  = TideWatch · 观潮 —— 网络水军与协同行为识别引擎
CompanyName      = tidewatch contributors      LegalCopyright = MIT License
OriginalFilename = TideWatch.exe
```

exe 同级的目录树：

```
configs  data  rules  _internal  LICENSE  README.md  TideWatch.exe  使用说明.md
```

`configs/` 与 `rules/` 就摆在 exe 旁边 —— 也就是
[2.1](#2.1) 里承诺的「规则看得见、改得动」，在下载下来的包里真的成立。

### 9.5 验收带出来的三件事

| # | 发现 | 性质 |
|---|---|---|
| 1 | `.sha256` 是 CRLF，`sha256sum -c` 读不了 | **真缺陷**（已修，见 [7.2](#7.2)） |
| 2 | 哈希值与发布值逐字一致 | 通过 |
| 3 | 解压件 `--version` / `doctor` / `scan` 全 EXIT=0 | 通过 |

一条缺陷，两条通过。**验收的价值不在于拿到几个 ✅，而在于那一条**——
它是「构建脚本返回 0」这个信号**看不见**的东西。

---

<a id="10"></a>
## 10. 踩坑总表

| # | 坑 | 症状 | 类型 | 守着它的东西 |
|---|---|---|---|---|
| 1 | 冻结后 stdout 是 GBK，数据里有 `❤️` | 打包版 `exit 3` + `UnicodeEncodeError`，源码态完全正常 | **只在打包后复现** | 构建脚本的冒烟 + 反证实测 |
| 2 | `__file__` 反推的资源根 | onedir 下碰巧对；兜底/onefile 下指到别处，同一进程报出两个路径 | **安静地错** | `test_partial_resource_root_is_not_silently_skipped` |
| 3 | 资源目录不完整时往下一级找 | 使用者改的规则不生效，程序一切正常 | **安静地错** | 同上 |
| 4 | `seed_user_root` 覆盖已存在的文件 | 使用者微调好的话术库被「首次运行」吃掉 | **安静地错** | `test_seed_user_root_never_overwrites_user_edits` |
| 5 | 双击 = 无参数，`argparse` 退出 | 控制台闪一下就没，看不到任何提示 | 体验，但最糟 | `test_no_arguments_from_explorer_pauses_instead_of_flashing` |
| 6 | 版本号五处各写一个数 | 「检查更新说有新版，装完还是旧的」 | **安静地错** | `test_version_matches_pyproject` / `test_version_matches_default_config` |
| 7 | `Path.with_suffix(".zip")` 吃掉 `.1-win64` | 产物叫 `TideWatch-0.0.zip` | 命名错误 | 构建脚本输出人工核对时发现 |
| 8 | `from X import name` 把引用钉死 | 测试里替换 `paths.resource_root` 不生效 | 测试失效 | 改成 `import paths` + 属性访问 |
| 9 | 图标线画到画布边缘 | 圆角遮罩把两端切出毛刺，像渲染坏了 | 观感 | 看图发现 |
| 10 | `ImageDraw.line` 端点默认是平的 | 细线宽下像被截断 | 观感 | 看图发现 |
| 11 | 中文宽度按字符数对齐 | 自检输出列对不齐，看起来像坏了 | 观感 | `_display_width()` 按东亚字符双宽计算 |
| 12 | **构建脚本假设 stdout 能编码中文** | CI 上 9 秒即死，本地跑一万次都正常（GBK 恰好能编码汉字） | **只在别人的机器上复现** | `test_build_script.py` 的 12 条 + 反证 |
| 13 | **`pwsh` 步骤的 `$ErrorActionPreference = 'stop'`** | 原生命令一非零退出就中断整步，**诊断块根本没机会跑** | 排错工具自身失效 | 步骤开头显式覆盖 + 用 `$LASTEXITCODE` 自己判 |
| 14 | **`capture_output` 把失败原因吞掉** | `CalledProcessError` 只说「exit status 1」，「exe 为什么非 0」恰好看不到 | 排错盲点 | `run()` 失败时补印 stdout/stderr |
| 15 | **`Path.write_text` 把 `\n` 翻译成 CRLF** | `.sha256` 在 Git Bash / Linux / WSL 上 `sha256sum -c` 读不了 | **安静地错** | `test_checksum_file_uses_lf_not_crlf`（盯字节） |

**15 条里有 5 条是「安静地错」**（不报错、不崩溃，只是悄悄给出错误结果），
另有 **2 条只在打包后复现、1 条只在别人的机器上复现**。
这三类加起来占了过半 —— 这正好说明为什么打包与发行这一轮不能只交一个壳，
也说明了为什么「本地跑过了」和「CI 绿了」都不能当作验收。

第 12～15 条是**第二轮**才发现的，而它们全都有一个共同点：
**本地环境里看不出来。** 12 要有一台英文 Windows、13 要从 runner 源码里读、
14 要把子进程的输出接回去看、15 要换一个平台跑 `sha256sum -c`。
换句话说，它们都是**被「换个角度看」逼出来的**，不是被「更仔细地看」逼出来的。

---

<a id="11"></a>
## 11. 实测记录

全部在**解压出来的发行目录**里跑，不是源码。
「第一轮」= 提交 `dad2282`，「第二轮」= `1e0827d`。

| 项 | 结果 |
|---|---|
| 构建 | ✅ 22.3 MB / 55 个文件；单次 22 s（PyInstaller 单步 15.6~15.7 s，三次一致） |
| zip | ✅ 8.9 MB；两次打包 SHA 一致（`--verify-reproducible`） |
| `--version` | ✅ `tidewatch 0.0.1` |
| `doctor` | ✅ 结论 `warn`（唯一的 warn 是「jieba 未安装」，属可选依赖） |
| `scan` 样例数据 | ✅ 读取 193 条发言 / 160 个账号 / 10 个话题；报告落盘 22430 字节 |
| emoji 输出 | ✅ 重定向到文件后 `❤️` 正常出现（`grep -c` = 1） |
| 反证 1：去掉编码处理 | ✅ 重新构建后 `exit 3`，日志里是 `UnicodeEncodeError('\u2764')`，emoji 一行都打不出 |
| 反证 2：旧路径写法（同级资源齐全） | ✅ 旧写法可用（反证了「我没修复一个不存在的 bug」） |
| 反证 2b：旧路径写法（触发兜底） | ✅ `doctor` 同时打印 `_internal\configs\…` 和「找不到 `…\configs\…`」 |
| 反证 2c：onefile 探针 | ✅ 旧写法指到 `%TEMP%\configs` |
| 反证 3：版本守卫 | ✅ 把 pyproject 改成 9.9.9，`test_version_matches_pyproject` 如期失败 |
| 同级资源**全部**删除 | ✅ 自动回落到 `_internal`，功能正常 |
| 同级资源**部分**缺失 | ✅ 停在原地并报 `fail`，不静默切走 |
| 只读程序目录（ACL 拒绝写入） | ✅ 报 `warn` + 把默认规则铺到用户目录 + 给出 `TIDEWATCH_HOME` 用法 |
| 双击不闪退 | ✅ `Start-Process` 拉起 4 s 后进程仍存活（在等回车） |
| exe 版本资源 | ✅ `FileVersion 0.0.1` / `ProductName TideWatch`（右键属性可核对） |
| **第二轮** 复现 CI 的崩溃 | ✅ `PYTHONIOENCODING=cp1252` → 与 CI **逐字相同**的回溯（同一文件同一行、`cp1252.py:19`） |
| **第二轮** 修复后在敌意编码下跑通 | ✅ `EXIT=0`，55 文件 / 22.3 MB / zip 8.9 MB / 两次 SHA 一致 / 冒烟三条 ok |
| **第二轮** 反证：摘掉编码修复 | ✅ 行为测试与位置测试如期变红 |
| **第二轮** 反证：摘掉 `newline="\n"` | ✅ 测试变红，打出的字节与发布件里那份一致 |
| **第二轮** `gen_sample.py` / `make_icon.py` | ✅ 各自在 cp1252 下实跑 `EXIT=0` |
| **CI**：`a5d7d85` 与 `1e0827d` | ✅ 全绿（8 个作业，含新增的 `Windows 打包`） |
| **Release**：`v0.0.1` | ✅ 10 个步骤全绿；产物 `TideWatch-0.0.1-win64.zip`（9.47 MB）+ `.sha256` |
| **验收**：下载件校验和 | ✅ 哈希与发布值逐字一致 `410796b5da8d7d…` |
| **验收**：zip 结构 | ✅ 79 条目 / 单一顶层目录 / 无上跳路径 / 中文名带 UTF-8 标志位 |
| **验收**：解压件实跑 | ✅ `--version` / `doctor` / `scan` 全 `EXIT=0`；报告 22430 字节 |
| **验收**：`sha256sum -c` | ❌ 失败 —— 发布件是 CRLF（已定位并修在 `main`，见 [7.2](#7.2)） |
| 测试 | ✅ 195 条全绿（起点 161 → 第一轮 183 → 第二轮 195） |
| 静态检查 | ✅ `ruff` 全规则通过 |
| 规模 | 7 个提交 · 25 个文件 · +2764 / −21 行（其中第二轮 7 文件 +507 / −10） |

---

<a id="12"></a>
## 12. 未验证项（诚实记账）

**免得日后误以为验过了。**

| 项 | 状态 | 说明 |
|---|---|---|
| Windows 11 x64 | ✅ 实测 | 构建 + 冒烟 + 验收全过 |
| Windows 10 | ⚠️ 未测 | 手上只有一台机器。PyInstaller 产物对 10/11 兼容，但没有实测证据 |
| 没装 Python 的机器 | ✅ 间接验证 | 产物自带运行时，冒烟是在不依赖 `.venv` 的子进程里跑的 |
| 32 位 / ARM64 | ⚠️ 未测 | 脚本里有平台标签逻辑，只在 x64 上跑过 |
| 杀软误报 | ⚠️ 未测 | 本机没装第三方杀软。已关闭 UPX 以降低概率；**没有代码签名**，SmartScreen 首次运行会拦 —— 这是免签名程序的常态，已写进使用说明 |
| jieba 可选依赖 | ❌ 未在打包版实测 | 发行包刻意不带。降级路径有测试守着，但那是源码态 |
| macOS / Linux 发行包 | ❌ 未做 | 只做了 Windows 打包 |
| 中文路径（含空格/特殊字符）下的运行 | ⚠️ 未测 | 没有专门构造 |
| 输入数据含其他稀有字符（如其他 emoji、生僻字） | ⚠️ 未测 | 编码已统一为 UTF-8 + `errors="replace"`，理论上不会再崩，但没有逐个验证 |
| 从「有旧版本」的目录升级 | ⚠️ 未验证 | 本版是第一个发行版，没有旧版本可升 |
| **CI 的 pwsh 步骤语义** | ⚠️ 未在本地复现 | 「`$ErrorActionPreference='stop'` 会不会吞掉诊断块」是从 `actions/runner` 源码读出来的，本机没装 pwsh 7，**没有实测**。加固是防御性的（显式覆盖成 `Continue`），即使原判断有偏也不会更差 |
| **非英文 Windows 的构建** | ✅ 实测 | 中文 Windows（GBK）与 cp1252 模拟都跑通了；其他区域设置（如日文 cp932）未逐个测 |
| **发布件的 `sha256sum -c`** | ❌ 当前不可用 | v0.0.1 的 `.sha256` 是 CRLF；修复在 `main`，未随该版本发布（有意，见 [7.2](#7.2)） |
| **CI 上 PyInstaller 的构建耗时** | ⚠️ 未直接测 | 从「9 秒失败」反推它在 10 秒内，但没有干净的计时数据 |

---

<a id="13"></a>
## 13. 用上了哪些既有经验

这一轮不是从零想的，是把既有的项目经验清单逐条对照着做的。挑出真正影响决策的几条：

| 既有经验 | 怎么落地的 | 效果 |
|---|---|---|
| **打包是「问题放大器」，不能只交一个壳** | 打包这一轮连带做掉了「数据/资源往哪放」「每条错误路径都有出口」「状态自查三档」 | 直接决定了 `paths.py` 与 `doctor` 的存在 |
| **onedir 而不是 onefile；第一问是「数据在哪、会不会丢」** | 依据「微调入口必须可编辑」选了 onedir | 关键判断。按「文件数越少越好」会选 onefile，那会破坏核心承诺 |
| **校验和：说清「能核对下载、不能核对构建」** | zip 做成确定性；发行说明里写明口径；用五份 SHA 列成实据 | 免得有人重跑构建后误判「包被动过」 |
| **版本号要能被现场核对** | 单一来源 + exe 版本资源 + 测试守卫 | 右键属性即可核对；报问题时说的版本号可现场验证 |
| **守卫式测试必须先在旧代码上失败** | 对**七处**修复做了完整反证 | 直接推翻了一个错误结论：路径那条旧写法**碰巧是对的**。没有反证就会写出一句假话 |
| **反证本身也要被怀疑** | onefile 探针补上；敌意编码的生效性也写进断言 | 把结论从「必然崩」修正为「onedir 下碰巧对」；避免「永不触发的反证」 |
| **「不报错但结果不对」是最贵的一类 bug** | 15 条坑里 5 条属于这一类，每条都配了回归测试 | 见 [第 10 节](#10) |
| **诚实记账：写清「没做什么」「没验证什么」** | 第 12 节单独成表，含「CI pwsh 语义未实测」 | 免得日后误以为验过了 |
| **隐私有三条独立通道** | 提交前扫了文件内容（邮箱/路径/手机号形态）；提交元数据邮箱与仓库既有提交保持一致 | 未发现泄漏 |
| **先摸清远端现状，别按本地推断** | 开工第一条命令是数远端 tag / Release；第二轮第一条是拉失败的 run 详情 | 确定了「从未发过版」；也确认了「9 秒」这个关键量级 |
| **排错不该靠猜** | 拿不到日志就把日志搬到公开可读的地方（`::error::` 注解），而不是改代码碰运气 | 一轮就定位到根因；而且**这套诊断留在了流水线里**，下次不用再搭一遍 |
| **本地过了 ≠ 能跑** | 用 `PYTHONIOENCODING=cp1252` 把对方的环境搬过来复现 | 环境差异是被构造出来的，不是等 CI 报信 |

**两条没做到位的：**

1. 既有经验里有「CI 里加一条『构建后体积超过阈值就报警』（报警而不是失败，避免噪声）」。
   这一轮只是把体积打了、记了（22.3 MB / 8.9 MB），没有加进 CI 的自动报警。
   下一次动打包时补。
2. **第一轮报告写完就以为流水线通了**，实测记录里甚至写了「CI ✅ /
   Release 流水线」。而那时 Release 是失败的 —— 那是**没有验证就写下的结论**。
   这一条比任何技术坑都更值得记：报告里的每个 ✅ 都应当来自一次真实的运行，
   否则它只是「我认为」。

---

<a id="14"></a>
## 14. 复现全部结论

```bash
git clone https://github.com/whyao56/TideWatch.git && cd TideWatch
git checkout main          # 或 v0.0.1（注意：v0.0.1 不含后两个修复）

python -m venv .venv
./.venv/Scripts/python -m pip install -e ".[dev]" pyinstaller pillow

./.venv/Scripts/python -m pytest tests -q            # 195 条
./.venv/Scripts/python -m ruff check src tests scripts eval

./.venv/Scripts/python scripts/make_icon.py          # 重新生成图标
./.venv/Scripts/python scripts/build_exe.py --verify-reproducible
```

产物在 `dist/`：`TideWatch-0.0.1-win64/`（目录）+ `.zip` + `.zip.sha256`。

**验证发行包本身**（不用源码）：

```bash
cd dist/TideWatch-0.0.1-win64
./TideWatch.exe doctor
./TideWatch.exe scan data/sample/sample.jsonl --evidence
./TideWatch.exe --version
```

**复现「英文 Windows」这个条件**（本地就能做，不用等 CI）：

```bash
PYTHONIOENCODING=cp1252 python scripts/build_exe.py --verify-reproducible
#   修好前：UnicodeEncodeError: 'charmap' codec can't encode characters
#   修好后：EXIT=0
```

**重做七条反证**（每条都是「改回旧写法 → 重新构建 → 期望失败」）：

| 反证 | 改回什么 | 期望 |
|---|---|---|
| 编码 | `_setup_console()` 改空操作 | 打包版 `exit 3` + `UnicodeEncodeError('\u2764')` |
| 路径 | `project_root()` 改 `Path(__file__).resolve().parents[2]` | 删掉同级资源后，`doctor` 报出两个互相矛盾的路径 |
| 版本 | `pyproject.toml` 的 version 改成别的数 | `test_version_matches_pyproject` 失败 |
| 构建脚本编码 | `main()` 里 `_setup_console()` 改成 `pass` | `PYTHONIOENCODING=cp1252` 下 `--help` 崩；位置断言同时失败 |
| 校验和行尾 | 去掉 `newline="\n"` | `test_checksum_file_uses_lf_not_crlf` 失败，字节里出现 `\r` |
| 诊断块是否还能跑 | 去掉步骤开头那两行覆盖 | 失败时诊断注解不再产生（被 `$ErrorActionPreference='stop'` 拦掉） |
| 反证的前提 | 让 `PYTHONIOENCODING` 失效 | 反证自身应当报「敌意条件不成立」，而不是悄悄变绿 |

> **反证脚本要按 `git diff` 逐行还原，不是「改成一种看起来更差的写法」。**
> 这一轮里第一条反证第一次没抓住问题，原因就是替换不够忠实。

**验收已发布的包**（第二轮新增的一步）：

```bash
base=https://github.com/whyao56/TideWatch/releases/download/v0.0.1
curl -sSL -O $base/TideWatch-0.0.1-win64.zip
curl -sSL -O $base/TideWatch-0.0.1-win64.zip.sha256
sha256sum -c TideWatch-0.0.1-win64.zip.sha256     # v0.0.1 会在这一步因 CRLF 失败
python -c "import zipfile;zipfile.ZipFile('TideWatch-0.0.1-win64.zip').extractall('.')"
cd TideWatch-0.0.1-win64 && ./TideWatch.exe doctor
```

---

## 附录：新增/改动的文件

| 文件 | 行数 | 作用 |
|---|---|---|
| `src/tidewatch/paths.py` | 197 | 资源路径解析（源码态/冻结态同一套逻辑） |
| `src/tidewatch/version.py` | 13 | 版本号唯一来源 |
| `src/tidewatch/cli.py` | +452 | `doctor` / `--version` / 编码 / 双击兜底 / 异常出口 |
| `packaging/tidewatch.spec` | 145 | PyInstaller 配置（进版本库） |
| `packaging/entry.py` | 19 | 入口薄壳，避开 `__main__` 分裂 |
| `packaging/使用说明.md` | 143 | 随包分发的使用者文档 |
| `packaging/tidewatch.ico` | 24.8 KB | 7 个尺寸的程序图标 |
| `scripts/build_exe.py` | 380 | 构建 → 补资源 → 冒烟 → 确定性打包 → 校验和（第二轮 +114） |
| `scripts/make_icon.py` | 149 | 程序化生成图标（第二轮加控制台编码防护） |
| `scripts/gen_sample.py` | 321 | 合成数据集（第二轮加控制台编码防护） |
| `.github/workflows/release.yml` | 131 | tag 触发：lint → 测试 → 构建 → 发布（第二轮 +43：诊断包装） |
| `.github/workflows/ci.yml` | 183 | 第二轮 +71：新增 `Windows 打包` 作业 + 诊断包装 |
| `tests/test_paths.py` | 117 | 路径解析的守卫 |
| `tests/test_doctor.py` | 114 | 自检的守卫（含「能报坏」） |
| `tests/test_version.py` | 78 | 版本号一致性的守卫 |
| `tests/test_build_script.py` | 222 | **第二轮新增** 12 条：编码 / 反证 / 位置 / 校验和行尾 |
| `docs/packaging.md` | 247 | 打包设计与未验证项（第二轮 +20：校验和行尾口径） |
| `docs/release-notes/v0.0.1.md` | 123 | Release 正文 |

---

*报告生成时间：2026-10-16*
*起点 `bcdd436` → 终点 `1e0827d` + tag `v0.0.1`（`dad2282` → `a5d7d85` 移动过一次）*
*Release：https://github.com/whyao56/TideWatch/releases/tag/v0.0.1*
*发布件 SHA256：`410796b5da8d7d56184d0591a6ae4562f2a9fc419bf73c7ac6c48c32295715b6`（CI 构建）*
*本机构建 SHA256 与它不同，属正常 —— 见 [7.1](#7.1)*
