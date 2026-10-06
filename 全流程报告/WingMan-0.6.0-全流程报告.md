# WingMan 0.6.0 全流程报告 —— 关窗死锁与内存瘦身

> 提交 `122ff93` · tag `v0.6.0` · 测试 240 passed / 1 skipped
> Release：<https://github.com/whyao56/WingMan/releases/tag/v0.6.0>

---

## 0. 一句话

**点 × 卡死不是界面问题，是关窗钩子在 UI 线程里做了一次同步的「执行 JavaScript」，
而那次调用在等一个只能由 UI 线程执行的回调 —— 两边互等，必然死锁。**

内存那笔是顺路的收获：`import numpy` 这一下就提交了 760 MB，
占整个程序内存的九成以上，而它换来的并行度**一点都用不上**。

---

## 1. 用户报了什么

> 我点击右上角叉的时候，总会卡住，显示"WingMan 未响应"。你给我把程序优化流畅一些。

拆成两件事：

| 诉求 | 性质 |
|---|---|
| 点 × 卡死 | 确定性故障 —— 「总会」说明每次都会中 |
| 程序内存整体优化 | 性能优化 —— 但得先知道内存花在哪 |

---

## 2. 第一步：先复现，不猜

这类「窗口卡死」的直觉答案通常是「主线程被某个耗时操作占住了」。
但那个方向会把整件事带偏。先拿数据说话。

### 复现手法

**`Process.CloseMainWindow()` 就是发 `WM_CLOSE`**（等价于点 ×）；
**`Process.Responding` 读的就是 Windows 判定「未响应」用的那个状态**
（内部即 `IsHungAppWindow`）。这两个 API 让复现和判定都能脚本化。

```powershell
$proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*WingMan*" } | Select-Object -First 1
[void]$proc.CloseMainWindow()          # 等价于点了 ×
for ($i = 1; $i -le 8; $i++) {
  Start-Sleep -Seconds 1
  $p = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
  Write-Output ("第 {0}s：Responding={1} CPU={2}s" -f $i, $p.Responding, $p.CPU)
}
```

> 一开始想用 `Add-Type` 调 P/Invoke 的 `SendMessage` + `IsHungAppWindow`，
> 但 `Add-Type` 在本机被安全策略拦下了。换成这两个 .NET 内置成员后**完全等价**，
> 而且不用编译 C#。

### 结果

| 时刻 | Responding | CPU |
|---|---|---|
| 发 WM_CLOSE 前 | `True` | 2.0625s |
| 之后 1 秒 | **`False`** | 2.0625s |
| 之后 2 秒 | **`False`** | 2.0625s |
| … | … | … |
| 之后 8 秒 | **`False`** | **2.0625s（纹丝不动）** |

**CPU 纹丝不动，是死锁的指纹。**

如果是「算不过来」，CPU 读数会往上走（那就是性能问题，该去优化算法）；
这里它**完全不动** —— 说明进程什么都不干，只是**在等**。

这一条把方向从「找耗时操作」直接扭到了「找互等」。

---

## 3. 根因：UI 线程里的同步 `evaluate_js`

顺着「在等」的线索去看关窗那一刻的调用栈：

```
用户点 ×
  → Windows 发 WM_CLOSE
  → pywebview 在 UI 线程上回调 FormClosing
  → 我们的 _on_closing()          ← 就在这个线程里
  → _ask_frontend_to_choose()      ← 想通知页面弹窗
  → _WINDOW.evaluate_js(...)       ← 同步阻塞
  → semaphore.acquire()            ← 死等
```

而 `evaluate_js` 的那一头（pywebview 6.2.1，`platforms/edgechromium.py:136`）：

```python
def evaluate_js(self, script: str, parse_json: bool):
    def _callback(res):
        ...
        semaphore.release()          # ← 只有它能让上面那句返回

    result = None
    semaphore = Semaphore(0)
    try:
        self.webview.Invoke(
            Func[Object](
                lambda: self.webview.ExecuteScriptAsync(script).ContinueWith(
                    Action[Task[String]](lambda task: _callback(json.loads(task.Result))),
                    self.syncContextTaskScheduler,      # ★ 投递到 UI 线程的同步上下文
                )
            )
        )
        semaphore.acquire()          # ← 无限等待，没有超时
    except Exception:
        ...
    return result
```

**关键就在 `syncContextTaskScheduler` 这个参数。**

`ExecuteScriptAsync(...)` 完成之后，回调 `_callback`（负责 `release()`）
被安排到 **UI 线程的同步上下文**上执行。而 UI 线程此刻正卡在
`_on_closing` 里等 `semaphore` —— **没有人在跑那个回调，也就永远没人 release。**

两边互等，`semaphore.acquire()` 没有超时，**永不解开**。

> 这也解释了为什么它是**必然**的而不是偶发的：只要走关窗这条路，
> `evaluate_js` 就一定是在 UI 线程上被调用的。用户说的「总会」，是准确的。

---

## 4. 修法：把「通知界面」挪出 UI 线程

### 核心改动

关窗钩子只做一件事：**置标志 + 起一个后台线程，然后立刻返回**。

```python
def _on_closing() -> bool:
    """pywebview 的关窗钩子。返回 False = 取消这次关闭。

    ⚠️ 这个函数跑在 UI 线程上（winforms 的 FormClosing 事件回调），
    所以这里绝不允许出现同步的 evaluate_js。
    """
    if _CLOSE["quitting"]:
        return True
    if _CLOSE["pending"]:
        return True                      # 再点一次 × → 直接放行
    _CLOSE["pending"] = True
    threading.Thread(
        target=_ask_frontend_or_close, name="wingman-close-ask", daemon=True
    ).start()
    return False
```

**为什么放到后台线程就好了**：`evaluate_js` 内部的 `self.webview.Invoke(...)`
在非 UI 线程调用时会**投递**到 UI 线程执行；而此刻 UI 线程已经从钩子里返回、
空闲下来了 —— 它能去跑那个回调，`release()` 得以执行，
`semaphore.acquire()` 正常返回。

### 三层兜底

这一版没有只修「卡死」就收工。改完之后，**每一条失败路径都得有出口**：

1. **超时**：`_ask_frontend_to_choose(timeout=5.0)` 起子线程调 `evaluate_js`，
   用 `Event.wait(5)` 等它；超时就按「通知失败」处理 —— 不把用户永远留在
   一个不动的窗口前。
2. **通知失败就补一刀**：`_on_closing` 已经返回 `False`（取消了这次关闭），
   如果通知界面又失败，用户再点 × 也还是关不掉 —— 就成了「点了没反应」。
   所以失败时必须**主动把窗口关掉**：

   ```python
   def _ask_frontend_or_close() -> None:
       if _ask_frontend_to_choose():
           return
       log.info("界面接不住关闭请求，直接关闭窗口。")
       _CLOSE["pending"] = False
       _CLOSE["quitting"] = True      # 让 destroy 触发的 _on_closing 放行
       _destroy_window()
   ```

3. **`quitting` 标志**：用户选了「关闭程序」之后，之后的所有关闭事件一律放行。
   不加这个的话，`_destroy_window()` 会**再触发一次** `FormClosing` → 又进协商
   → 又拦一次，转回去又关不掉。

### 顺带修出来的两个问题

#### 3.1 「关闭程序」从未让 uvicorn 收工

原代码：

```python
_STOP = threading.Event()
...
log.info("用户选择关闭程序，准备退出。")
_STOP.set()                                  # ← 谁在读它？
threading.Thread(target=_force_exit_soon, ...).start()
```

`grep -rn "_STOP" backend/app/` 的结果：**只有它自己的定义和这一处 set，
全仓没有任何消费者。** 注释里写的「先让 uvicorn 收工」是假的 ——
uvicorn 根本没收到信号，「优雅退出」全靠 1.2 秒后的 `os._exit(0)` 硬切。

后果：如果那一刻正好在写数据库（导入刚结束、画像刚存下来），就被掐断了。
SQLite 的 WAL 模式不会因此损坏数据，但会留下没 checkpoint 的 `-wal` 文件。

**修法**：保存 `uvicorn.Server` 引用，退出时置 `should_exit` 并**轮询等它收工**：

```python
def _ask_server_to_stop() -> None:
    server = _SERVER.get("server")
    if server is None:
        return
    server.should_exit = True

def _wait_server_stop(timeout: float) -> bool:
    t = _SERVER.get("thread")
    if t is None:
        return True
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not t.is_alive():
            return True
        time.sleep(0.05)
    return False

def _quit_soon(grace: float = 4.0) -> None:
    """收尾：先让服务体面收工，再关窗口，最后兜底强退。

    顺序不能反 —— 窗口一关，主线程就从 webview.start() 返回、
    一路走到进程退出；那时 uvicorn 若还在写库，就是被硬生生掐断的。
    """
    if _wait_server_stop(grace):
        log.info("服务已收工。")
    _destroy_window()
    time.sleep(1.5)
    os._exit(0)
```

现在日志里能看到完整链路（实测输出）：

```
已通知服务收工（uvicorn should_exit）。
WingMan 已退出
Application shutdown complete.
Finished server process [12460]
服务已收工。
正在退出，放行这次关闭。
界面已关闭，等后台服务收工…
已退出。
```

#### 3.2 `python -m app.desktop` 下窗口状态有两份

这个是排查时**意外撞见**的，很值得记下来。

用源码模式启动后，`/api/desktop/state` 报 `native_window: false`，
但 PowerShell 明明找得到那个标题为「WingMan · 聊天僚机」的窗口。
而且 `started_at` 比日志第一行**晚了 13 秒** —— 一个模块的启动时刻，
怎么会在它自己开始工作之后？

两个线索指向同一件事：**内存里有两个 `desktop` 模块**。

- `python -m app.desktop` 会让这个文件以 `__main__` 的名字执行；
- `app.api.routes_admin` 又 `from .. import desktop`，把它**按模块名再导入一次**。

于是 `_WINDOW` / `_CLOSE` / `_SERVER` / `_STARTED_AT` 各存一份：
主流程写的是 `__main__` 那份，接口读的是 `app.desktop` 那份（永远初始值）。

症状全都**像功能坏了，而不是像状态串了**：

- 窗口开着 → 接口说「没有原生窗口」→ 界面按「浏览器模式」措辞；
- 点「后台运行」→ 后端读到一个 `None` 窗口 → 回你「已关闭」**却什么都没做**。

**修法**（文件顶部，任何可能触发 api 导入的代码之前）：

```python
if __name__ == "__main__":      # pragma: no cover - 只有直接运行时才成立
    sys.modules.setdefault("app.desktop", sys.modules[__name__])
```

`exe` 与 `python run_wingman.py` 走的是 `from app.desktop import main`，
`__name__` 本来就是 `app.desktop`，**本来就没这个问题** ——
但排查问题时很容易被它带偏，所以一并修了。

---

## 5. 内存：一个 `import` 占了九成

### 先分层测量，别猜

内存问题的直觉答案通常是「前端 DOM 太重」或「后端缓存了太多数据」。
但正确做法是先量出**基线**。用几个最小对照进程（同机、同 venv）：

| 进程 | WorkingSet | Private（提交） | 线程 |
|---|---|---|---|
| 空 Python | 4.2 MB | **0.9 MB** | 1 |
| 只 `import` 依赖（numpy 等） | 57.1 MB | **782.3 MB** | 27 |
| WingMan 服务本身（`--no-window`） | 73.7 MB | **793.5 MB** | 28 |

**结论一目了然：WingMan 自己的代码只贡献了 11 MB。780 MB 是导入依赖时提交的。**

### 缩小到单一元凶

再单独测 `import numpy`，并且和「限制 BLAS 线程数」做对照：

| | 提交内存 | 线程 |
|---|---|---|
| 默认 | **760.6 MB** | 27 |
| `OPENBLAS_NUM_THREADS=1` | **19.4 MB** | 4 |

**760 MB 对 19 MB —— 差 39 倍，就差在一个环境变量上。**

原因是 OpenBLAS 会看机器**有多少个逻辑核**，然后开同样数量的线程，
并给每个线程预先把工作缓冲区留出来。这台机器 **24 个逻辑核** —— 于是 24 个线程。

而本项目用 numpy 只干一件事：几千条 512 维向量算**余弦相似度**。
这个规模连一次眨眼都用不到，多线程只会带来调度开销。
**那些预留的内存换来的并行度，一点都用不上。**

### 修法

放在 `backend/app/__init__.py` 的**顶层**：

```python
for _var in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_var, "1")
del _var
```

两个刻意的选择：

- **位置**：`app/__init__.py` 是最外层，在任何子模块之前执行。
  OpenBLAS 是在 `Import numpy` **那一刻**就把线程池建好的，
  之后再设环境变量**等于没设**。所以这里没有第二个可选位置。
- **`setdefault` 而不是硬赋值**：用户自己设过就听用户的，
  我们只是提供一个更省内存的默认值。

### 效果（带窗口，实测）

| | 提交内存 | 线程 |
|---|---|---|
| 修复前 | 844.9 MB | 43 |
| 修复后 | **107.0 MB** | **20** |

---

## 6. 一个坑：`GetProcessMemoryInfo` 静默返回 0

第一次写内存探针时，所有读数都是 `0.0 MB` —— **没报错，就是全 0**。

原因：`kernel32.GetCurrentProcess()` 返回的是伪句柄 `-1`。
不显式声明 `restype` 的话，ctypes 把它当 32 位 `int`，句柄被截断，
`GetProcessMemoryInfo` 于是失败并返回 0，结构体字段保持初始值。

```python
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_k32.GetCurrentProcess.restype = wintypes.HANDLE    # ★ 这一行不能省
_k32.GetCurrentProcess.argtypes = []
_psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PMC), wintypes.DWORD]
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
```

加上这一行之后拿到的正是 §5 里的数据。

> 这类「不报错但结果全错」的坑比崩溃更难查 —— 崩溃至少有栈，
> 它只会让你对着一个漂亮的全 0 表格怀疑自己。

---

## 7. 完整内存画像（打包版实测）

| 部分 | WorkingSet |
|---|---|
| `WingMan.exe` 主进程（Python + FastAPI + 本项目代码） | 162.1 MB |
| 6 个 `msedgewebview2.exe`（Edge 渲染引擎） | 400.8 MB |
| **合计** | **约 563 MB** |

那 6 个渲染进程是 Windows 自带 WebView2 的**标准结构**
（主控 / 图形 / 网络 / 渲染 / 工具 / 崩溃上报），不是泄漏 —— 关掉程序会一起消失。

**主进程那部分已经压到位**（0.6.0 之前光提交内存就 845 MB）。
剩下 400 MB 是 WebView2 的固有成本：压它需要限制渲染参数
（`--disable-gpu`、限制渲染进程数之类），**副作用不可控而收益不确定，这一版刻意没动**。

> 在意内存可以走浏览器模式：`WingMan.exe --browser`（或 `WINGMAN_USE_BROWSER=1`）。
> 它复用系统里已有的浏览器，不起 WebView2 进程组，主进程只剩约 74 MB。
> 代价是没有原生窗口（没有独立任务栏图标）。功能完全一样。

---

## 8. 守卫与反证

### 新增守卫

| 文件 | 项数 | 盯着什么 |
|---|---|---|
| `tests/test_memory_footprint.py` | 2（新） | 干净子进程里验证「限流早于 numpy」，并直接量提交内存 |
| `tests/test_objects_center.py` | 29 → 33 | 4 条桌面壳守卫，见下 |

`test_memory_footprint.py` 为什么**必须用子进程**：pytest 进程自己早就把 numpy
导进来了，那时候再去断言环境变量，「限流生效了没有」根本看不出来。

四条桌面壳守卫：

- `test_the_close_hook_never_blocks_on_evaluate_js` —— 把「UI 线程里同步调
  `evaluate_js` 会死锁」的语义照搬进测试（一旦在调用者线程上被调就不按时返回），
  要求关窗钩子仍然立刻返回；
- `test_desktop_close_quit_actually_tells_the_server_to_stop` —— 退出必须**真的**
  置 `should_exit`，不能只 `set()` 一个没人读的 Event；
- `test_when_the_page_cannot_be_reached_the_window_is_still_closed` —— 通知不到界面时
  必须补关窗；
- `test_state_is_shared_even_when_desktop_py_runs_as_main` —— 以 `__main__` 加载
  `desktop.py` 再 `import app.desktop`，两者必须是**同一个模块对象**。

### 反证：6 条，全过

把每一处修复逐条改回旧写法，对应用例**必须失败**（跑完自动还原源码）：

| 改回旧写法 | 如期失败的用例 |
|---|---|
| 删掉 BLAS 限流 | `test_the_package_caps_blas_threads_before_numpy_arrives` |
| 删掉 BLAS 限流（效果侧） | `test_importing_numpy_stays_within_a_sane_memory_budget` |
| 关窗钩子改回同步调 `evaluate_js` | `test_the_close_hook_never_blocks_on_evaluate_js` |
| 退出只 `set()` 没人读的 Event | `test_desktop_close_quit_actually_tells_the_server_to_stop` |
| 通知不到界面时不补关窗 | `test_when_the_page_cannot_be_reached_the_window_is_still_closed` |
| 去掉 `desktop.py` 顶部的自我登记 | `test_state_is_shared_even_when_desktop_py_runs_as_main` |

### 反证本身抓出的问题（这才是它的价值）

**第一次跑，「关窗死锁」那条没抓住。**

原因不是守卫太弱，而是**我的替换不够忠实**：我只把 `_on_closing` 改回了同步调用，
却留着新版 `_ask_frontend_to_choose` 内部的线程包装 ——
那是个**现实中不存在的混合状态**（旧代码里这两处是同一套写法），自然复现不出死锁。

改成「两处必须一起改回」之后才如期失败。

> **教训：一条通过了的反证，可能只是因为你复现旧代码复现得不够忠实。**
> 这和 0.5.0 那次（`_resolve_map` 改成了另一种坏法）是同一类问题的两个变体。

---

## 9. 验证（都是实测，不是推演）

### 修复前 vs 修复后（对进程发 WM_CLOSE，每秒采样）

| | 修复前 | 修复后 |
|---|---|---|
| 窗口是否响应 | **否**（连续 8 秒） | **是**（连续 8 秒） |
| CPU | 2.0625s 恒定不变 | 正常 |

### 关窗协商全流程（源码模式 + 打包版各跑一遍）

| 步骤 | 结果 |
|---|---|
| 点 × | 拦下 → `/api/desktop/state` 报 `pending_close: true` ✓ |
| 选「后台运行」 | 返回 `action: background` +「窗口已隐藏」 ✓（修复前会**错报成 `quit`**） |
| `/api/desktop/show` | 返回 `shown: true`，窗口调回 ✓ |
| 选「关闭程序」 | **1 秒内**干净退出，端口释放 ✓ |

打包版自检：`WingMan v0.6.0 · 打包版（exe）· 全部就绪`。

---

## 10. 交付物

| 项目 | 内容 |
|---|---|
| 测试 | **240 passed / 1 skipped**（0.5.0 是 235） |
| 包 | `WingMan-0.6.0-win64.zip` · 33.8 MB / 221 文件 |
| SHA256 | `3b5d97a5c4268c2afa35e6795d511febb59a2f5866992c164889289e29a9910f`（打包两遍一致） |
| Release | <https://github.com/whyao56/WingMan/releases/tag/v0.6.0> |
| 代码 | `backend/app/desktop.py`、`backend/app/__init__.py`、`frontend/index.html`（BUILD 常量） |
| 文档 | CHANGELOG / README / ROADMAP / STATUS（新增 §10.5、§14）/ TROUBLESHOOTING（新增 §15）/ docs/releases/v0.6.0.md |

---

## 11. 未做 / 存疑

- **WebView2 的 400 MB 刻意没动**。能压，但要改渲染参数，副作用面太大而收益不确定。
  **要压得先做一整轮界面回归。**
- **没有给用户一个「低内存模式」开关**。`--browser` 已经能省掉整个 WebView2 进程组
  （主进程 ~74 MB），但它是个命令行参数，界面上没有入口。要加得先想清楚
  怎么讲清代价（没有原生窗口、没有独立任务栏图标）。
- **关窗协商那 5 秒超时是拍的**。真实环境下 `evaluate_js` 通常在几十毫秒内返回；
  这个值只是「兜底别卡太久」的上界，没有实测依据。
- 「自动采集取密钥」在本机仍跑不通（按 SQLCipher 规格穷举未命中），
  半自动仍是确定能走通的通道 —— 与本次改动无关。
