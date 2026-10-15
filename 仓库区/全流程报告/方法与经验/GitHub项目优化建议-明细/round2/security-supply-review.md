---
tags: [领域/方法, 类型/报告, 轮次/二]
评审日期: 2026-10-13
评审维度: 安全与软件供应链
评审员: sec-supply
评审对象: github.com/whyao56 / WingMan · Etude · TideWatch
---

# 第二轮评审 · 安全与软件供应链

**范围**：仅覆盖第一轮未涉及的面。第一轮已提过的（工作区明文密钥扫描无发现、缺 `pyproject.toml`、SQLite 外键失效、`_provide_both` 成本泄漏、LLM 无重试、CORS 过宽、500 回显堆栈、密钥与业务数据同在 kv 表、覆盖率缺失、lint 缺关卡、commit 元数据 QQ 邮箱、`Self-Mind` 转私有、README 英文版）**一律不重复**；相关的均在条目内显式标注「与第一轮 X 条的关系」。

**口径**：全部结论基于本地浅克隆的**只读静态阅读**（`git ls-files` / `Read` / `rg`）。未安装依赖、未运行被测程序、未修改 `gh-repos` 下任何文件。行号为实际读到的位置。CVE 与许可证结论均标注「查询日期 2026-10-13」并给可核验链接；无充分来源的写「未找到充分来源」，不做推测。

---

## 0. 一页结论（最该做的 3 件事）

**一句话**：三个仓库的**代码本身没有发现可利用漏洞**（无硬编码密钥、已跟踪文件无敏感文件、Etude 的路径穿越已被正则白名单挡住、WingMan 前端插值逐处都套了 `esc()`），但**安全工程化几乎是空白**——没有依赖漏洞监控、没有漏洞上报通道、TideWatch 的 CI 权限甚至没声明、本地 HTTP 服务**零鉴权**。短板不在"写错了什么"，而在"没有任何机制在出错时拦住你"。

| 排序 | 事项 | 优先级 | 工作量 |
|---|---|---|---|
| 1 | **本地服务零鉴权 + 无 Host 校验**：WingMan 还支持 `--host 0.0.0.0` 且无任何警告 → 同机任意网页（DNS rebinding）或局域网设备可读写全部聊天数据 | 🔴 P0 | 0.5–1 天 |
| 2 | **Etude 发布包内含 GPL-3.0 的 `edge-tts`，却整体声明 MIT** → 已发布的 exe 存在许可证冲突 | 🔴 P0 | 0.5 天（决策）+ 1 天 |
| 3 | **三仓库零依赖漏洞监控 + 零漏洞上报通道**：无 `dependabot.yml`、无 `SECURITY.md`、无任何 SAST/SCA 工具 | 🟠 P1 | 1 天 |

**最该先做的一件事**：三仓库各加一份 `dependabot.yml` + 一个 `pip-audit` CI 关卡（合计半天）。它把"依赖有没有新 CVE"从"偶然想起"变成"每周自动说"，是本轮性价比最高的一项。

---

## 1. 现状矩阵（三列对比）

| # | 检查项 | WingMan | Etude | TideWatch |
|---|---|---|---|---|
| 1 | 已跟踪文件中的密钥/配置/数据文件 | ✅ 仅 `.env.example` | ✅ 无 | ✅ 无 |
| 2 | `.gitignore` 拦 `.env` / `*.key` | ⚠️ 有 `.env`、`.env.local`、`*.key`，**不拦 `.env.*`**（`:22-25`） | ✅ `.env`、`.env.local`（`:39-40`）+ `config.json`（`:30`） | ✅ `.env`、`.env.*`、`*.key`、`cookies.txt`（`:29-32`） |
| 3 | 推送级密钥拦截（pre-commit/hook） | ❌ 无 | ❌ 无 | ❌ 无 |
| 4 | CI 中的密钥扫描 | ❌ 无 | ✅ greps job（`ci.yml:79-101`） | ❌ 无 |
| 5 | 依赖声明带上界 | ❌ 只有下界（`requirements.txt:2-9`） | ✅ 上下界齐全（`:14-29`） | ✅ 仅 1 个依赖 |
| 6 | 依赖锁定 | ✅ `requirements.lock.txt`（无哈希） | ❌ 无 | ⚠️ `Makefile:73-75` 有 `freeze`，产出是否被消费**待确认** |
| 7 | 锁定哈希（`--require-hashes`） | ❌ 无 | ❌ 无 | ❌ 无 |
| 8 | 依赖漏洞扫描 / SBOM | ❌ 无 | ❌ 无 | ❌ 无 |
| 9 | Dependabot 配置 | ❌ 无 | ❌ 无 | ❌ 无 |
| 10 | SECURITY.md（漏洞上报通道） | ❌ 无 | ❌ 无 | ❌ 无 |
| 11 | CodeQL / SAST | ❌ 无 | ❌ 无（仅 greps + `innerHTML` 守卫） | ❌ 无 |
| 12 | CI `permissions:` 最小化 | ✅ `contents: read`（`ci.yml:10-11`） | ✅ `contents: read`（`ci.yml:11-12`） | ❌ **未声明**（`ci.yml:1-9` 无该键） |
| 13 | 使用 `pull_request_target` | ✅ 无 | ✅ 无 | ✅ 无 |
| 14 | 把 secrets 暴露给 PR | ✅ 未使用任何 secrets | ✅ 未使用 | ✅ 未使用 |
| 15 | 第三方 Action 版本固定 | ⚠️ 仅 tag | ⚠️ 仅 tag | ⚠️ 仅 tag（另 `ruff` 未固定） |
| 16 | 本地服务监听地址 | ⚠️ 默认 `127.0.0.1`（`config.py:158`），但 `--host` 可改 `0.0.0.0` 且**无警告**（`desktop.py:460`） | ✅ 硬编码 `127.0.0.1`（`server.py:81`） | — 无 HTTP 服务 |
| 17 | 本地服务鉴权 / Token | ❌ 零鉴权 | ❌ 零鉴权 | — |
| 18 | Host 头校验（TrustedHost） | ❌ 无 | ❌ 无 | — |
| 19 | CORS 配置 | ⚠️ `allow_origins=["*"]` + `allow_credentials=True`（`main.py:188-194`） | ❌ 完全没有 CORS 中间件 | — |
| 20 | 静态文件目录穿越 | ✅ Starlette `StaticFiles`（`main.py:225`） | ✅ 音频/图片正则白名单（`api.py:590,595,617`） | — |
| 21 | 上传大小/类型校验 | ❌ 无（`routes_data.py:68-109`） | — 无上传接口 | — |
| 22 | 敏感数据落盘（日志/临时文件） | ⚠️ 2 处（`registry.py:373`、`analyzer.py:66`） | ✅ 未发现 | ✅ 未发现 |
| 23 | 容器运行时最小权限 | — 无容器 | — 无容器 | ✅ 非 root（`Dockerfile:33-36`） |
| 24 | 基础镜像 digest 固定 | — | — | ❌ `python:3.12-slim` 未固定（`Dockerfile:12`） |
| 25 | 许可证 / 依赖兼容性 | MIT ✅ 未发现冲突 | MIT ⚠️ **`edge-tts` = GPL-3.0** | MIT ✅ 未发现冲突 |

**图例**：✅ 无问题 / ⚠️ 部分 / ❌ 缺口 / — 不适用。

---

## 2. 逐条发现（按 P0 → P2 排序）

### 🔴 P0-S1 · 本地 HTTP 服务零鉴权，WingMan 还可无警告地监听 `0.0.0.0`；上传接口也无上限

**【现象 + 证据】**

1. **两个后端都没有任何入站鉴权**。在 `WingMan/backend/app` 与 `Etude/backend/app` 搜索 `authorization` / `bearer` / `x-api-key` / `Depends(` / `HTTPBasic` / `OAuth2` / `csrf`，**命中全是"出站调用大模型时加 Authorization"**（`WingMan/backend/app/llm/openai_compat.py:94`、`memory/embedder.py:184`），无一处校验入站身份。
2. **两个后端都没有 Host 头校验**：全仓搜索 `TrustedHost` → **零命中**（WingMan / Etude 均无）。
3. **Etude 连 CORS 中间件都没有**：`grep -rn "CORS\|add_middleware\|middleware" --include=*.py Etude/backend` → **零命中**。
4. **WingMan 的 CORS 对任意站点开放且允许凭据**：`WingMan/backend/app/main.py:188-194`

   ```python
   app.add_middleware(CORSMiddleware,
       allow_origins=[o.strip() for o in _settings.cors_origins.split(",") if o.strip()] or ["*"],
       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
   ```
   默认值见 `config.py:160` `cors_origins: str = "*"`，`.env.example` 服务段亦为 `CORS_ORIGINS=*`。
5. **WingMan 可把服务开到局域网且无任何警告**：`desktop.py:459-463`

   ```python
   p.add_argument("--host", default=None, help="监听地址（默认 127.0.0.1，仅本机可访问）")
   ```
   该值一路透传到 `uvicorn.Config(host=host, ...)`（`desktop.py:425-428`）。全仓搜索 `局域网`/`外网`/`公网`/`暴露` → 只命中无关业务文案，**没有一处提示"改成 0.0.0.0 等于把聊天库公开给整个网段"**。
6. **被保护的数据**：服务直接暴露 `/api/chats`、`/api/chats/{id}`、`/api/messages/*`、`DELETE /api/persons/{id}`（`routes_data.py:162-169`、`routes_persons.py`），背后是用户**全部聊天记录、人物画像、事实库**。
7. **上传接口无大小/类型上限**（同一暴露面的加深）：`routes_data.py:68-86` 与 `:89-109` 都用 `tmp.write_bytes(await file.read())` 一次性读全量，**无字节上限**；`suffix = Path(file.filename or "upload.txt").suffix` 直接取自用户输入且**无扩展名白名单**。对照 Etude **没有上传接口**，其文件入口已用正则白名单封死（`api.py:590` `_AUDIO_NAME = re.compile(r"^[a-z]+-[0-9a-f]{20}\.mp3$")`、`:595-596`、`:617-618`）——**这是做对的地方，本轮记为无发现**。

**【为什么是问题（最坏后果）】**

浏览器不区分"本机服务"与"远端服务"，只认**同源策略**，于是留下两条真实攻击路径：

- **DNS rebinding（读）**：用户访问任意恶意网页，该域名数秒内被重解析到 `127.0.0.1`，浏览器便认为"服务与我同源"，Page 可以**完整读取** `GET /api/chats` 的响应体——因为后端既不校验 `Host` 头，也不要求任何令牌。攻击者拿到的是**全部私密聊天记录**。CORS 白名单在这里**帮不上忙**：CORS 只管"跨源读取"，而 rebinding 后浏览器认定它是**同源**。
- **CSRF（写）**：即使读不到响应，`POST /api/messages/bulk {"action":"delete"}`、`DELETE /api/persons/{id}` 这类状态变更请求用 `text/plain` 或表单编码即可绕过预检直接发出，后果是**聊天记录与人物画像被批量删除且不可恢复**（这些接口的设计本身就是"不可撤销"）。

一旦用户按直觉把 `--host` 改成 `0.0.0.0`（"我想在手机上看看"是很自然的诉求），攻击面从"本机浏览器"扩到**整个局域网**：同一 Wi-Fi 下任何人都能拉走全部记录，连 rebinding 都不需要。上传无上限则让这条链多一个"占满磁盘 / OOM"的收尾。

**必须先说清一个事实**：`allow_origins=["*"]` + `allow_credentials=True` 在浏览器端是被拒绝的组合（规范禁止 `*` 与凭据共存，Starlette 会退化为回显请求 Origin），所以它**不会**直接等价于"任意站点可带 Cookie 读接口"。**但它也完全没有防护作用**——真正的防护是"校验 Host / 校验来源 / 要求令牌"，而这三者一个都没有。请不要误读为"因为浏览器会拒绝，所以安全"。

**【改法】**

```python
# 第一层（10 分钟）：Host 白名单，直接掐死 DNS rebinding
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

# 第二层（0.5 天）：本地一次性令牌
import secrets
from fastapi import HTTPException
_LOCAL_TOKEN = secrets.token_urlsafe(32)

@app.middleware("http")
async def require_local_token(request, call_next):
    if request.url.path.startswith("/api/") and request.url.path != "/api/health":
        if not secrets.compare_digest(request.headers.get("x-local-token", ""), _LOCAL_TOKEN):
            raise HTTPException(status_code=403, detail="missing local token")
    return await call_next(request)

# 第三层（15 分钟）：非回环地址默认拒绝启动
if host not in ("127.0.0.1", "localhost", "::1"):
    log.warning("监听地址 %s 不是回环地址：本服务没有用户鉴权，同网段任何人都能读写全部聊天数据。", host)
    # 建议默认 fail-fast，需要时用 --allow-lan 显式放行

# 第四层（15 分钟）：CORS_ORIGINS 默认值改回环地址
# .env.example: CORS_ORIGINS=http://127.0.0.1:8787
```

上传接口加白名单与上限（`routes_data.py`）：

```python
ALLOWED_EXT = {".txt", ".json", ".csv", ".md", ".log", ".mht", ".eml", ".html"}
MAX_UPLOAD = 64 * 1024 * 1024
def _validated_suffix(name: str | None) -> str:
    s = Path(name or "upload.txt").suffix.lower() or ".txt"
    if s not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型：{s}")
    return s
# 读取时按 1 MB 分块累加，超限即 413（不要先 read() 全量）
```

与第一轮 C-6 的关系：C-6 说的是**配置值本身过宽松**；本条补的是①它**不构成防护**的原因（且第一轮对 Etude "CORS 过宽"的描述与事实不符——Etude 没有 CORS 中间件），②真正能拦住攻击链的是 **Host 校验 + 令牌**，③WingMan 另有一条 `--host 0.0.0.0` 无警告的路径。

**【优先级】** P0
**【工作量】** 第一层 10 分钟；第二层 0.5 天（含前端取令牌）；第三、四层各 15 分钟；上传上限 0.5 小时
**【验收标准】** ① `client.get("/api/chats", headers={"host":"evil.com"})` → 400；② 不带 `x-local-token` → 403，带上 → 200；③ `--host 0.0.0.0` 未加 `--allow-lan` 时不启动并给出提示；④ `grep -c "CORS_ORIGINS=\*" .env.example` → 0；⑤ 上传 `.exe` → 400，超 64 MB 流 → 413 且临时目录被清理。

---

### 🔴 P0-S2 · Etude 发布包内含 GPL-3.0 的 `edge-tts`，但项目整体声明 MIT

**【现象 + 证据】**

1. Etude **直接声明**该依赖：`Etude/backend/requirements.txt:22` → `edge-tts>=6.1,<8.0`。
2. 它是**进程内 `import`**（不是子进程）：`Etude/backend/app/providers/tts.py:134` `import edge_tts`，`:143` `edge_tts.Communicate(...)`；`selfcheck.py:162` 也 `import edge_tts` 做自检。
3. Etude **发布 PyInstaller 二进制**：`build/etude.spec` 与 `build/size-baseline.json` 均被 git 跟踪（`git ls-files build`），且 `scripts/build_exe.py:149` 显式把 `"edge_tts"` 列入打包模块。
4. Etude 自身声明 MIT：`Etude/LICENSE:3` → `Copyright (c) 2026 Etude contributors`；README/徽章同样按 MIT 呈现。
5. `edge-tts` 是 **GPL-3.0**。**查询日期 2026-10-13**，来源：https://pypi.ac.cn/project/edge-tts （「许可证: GNU通用公共许可证v3 (GPLv3)」，分类器含 `License :: OSI Approved :: GNU General Public License v3 (GPLv3)`）；https://licensie.com/python/packages/edge-tts/6.1.13 （`GPL-3.0-only`，从包内 LICENSE 文件检测）；上游 https://github.com/rany2/edge-tts 。

**已核实"没问题"的两项（避免误伤）**：`pywebview` = **BSD-3-Clause**（2026-10-13，https://pypi.org/project/pywebview/6.2.1/ ）→ 与 MIT 兼容；`PyInstaller` = **GPL-2.0-or-later WITH Bootloader-exception**，其官方文档 1.2 节明确"你打包出的可执行文件可以用任何许可证发布"（2026-10-13，https://pyinstaller.org/_/downloads/en/v4.0/pdf/ ）→ **打包工具本身不污染产物，这不是问题**。

**【为什么是问题（最坏后果）】**

GPL-3.0 是**强传染**许可。GPL 代码以 `import`（链接）方式成为程序一部分并被**整体打包分发**时，分发包整体应满足 GPL-3.0：提供完整对应源码、附 GPL-3.0 全文、不得追加额外限制。当前状态是 **exe 里含 GPL-3.0 代码，但 LICENSE / README / Release 附件只声明 MIT**——这正是"license laundering"的表象。最坏后果按现实概率排序：① 若将来上架任何**分发渠道**（应用市场会做许可证审查），会因声明与内容不符被拒/下架；② **给下游使用者错误的授权预期**——有人以为可整体按 MIT 闭源商用，实际继承的是 GPL-3.0 义务，**你无意中给人埋了法律坑**，这是最伤名誉的一类开源失信；③ 即便最终可争辩为 "mere aggregation"，**举证成本远高于现在花半天处理**。

**必须诚实说明的不确定性**：GPL 的"聚合 vs 衍生"边界存在解释空间，最终定性属法律判断。本报告**不**下"已经违法"的结论，只下这个结论：**"整体 MIT"的声明与"进程内链接 GPL-3.0 组件"的事实存在明显张力，必须显式处理，不能默认忽略。**

**【改法（三选一，按推荐度排序）】**

- **A（推荐，彻底解除传染）**：TTS 从"进程内 import"改为**独立可执行/子进程**调用，并把 `edge-tts` 从运行依赖移到"文档化的可选外部工具"：
  ```python
  # providers/tts.py
  import shutil, subprocess
  def synth(text: str, voice: str, out_path: str) -> None:
      exe = shutil.which("edge-tts")
      if not exe:
          raise RuntimeError("缺少 edge-tts 命令行（pip install edge-tts）")
      subprocess.run([exe, "--voice", voice, "--text", text, "--write-media", out_path],
                     check=True, timeout=30)
  ```
  这样 Etude 自身仍是 MIT，`edge-tts` 是用户自装的独立程序，GPL 传染链在分发环节被切断。**注意必须同步删除 `build_exe.py:149` 的 `"edge_tts"`**，否则打包仍会把它塞进 exe。
- **B（坚持内置语音）**：保留进程内使用，但**移出 PyInstaller 打包集**（删 `build_exe.py:149`），改为**运行时由用户安装**，并在 `selfcheck.py` 把"缺 edge-tts"从"降级提示"升级为"功能不可用"的明确说明。
- **C（最省事、代价最大）**：Etude **整体改为 GPL-3.0**（替换 LICENSE、README 许可章节、`pyproject.toml` 的 license 字段）。代价是与"MIT 徽章"叙事及潜在商用预期冲突。

无论选哪个，都补 `THIRD_PARTY_NOTICES.md`（列 `edge-tts` GPL-3.0 与 `pywebview` BSD-3-Clause），并在 README 写明"exe 是否包含 GPL 组件"。

**【优先级】** P0（已是发布状态；一旦对外分发即产生实际义务）
**【工作量】** A 1 天（含打包改造与回归）／B 0.5 天／C 0.5 天；另加 0.5 天写声明文件
**【验收标准】** ① 选 A/B 时 `grep -rn "import edge_tts" Etude/backend` → 0；② `grep -n edge_tts Etude/scripts/build_exe.py` 不再出现在 `hiddenimports`；③ `THIRD_PARTY_NOTICES.md` 存在且含上述两个依赖；④ 解包 exe（`pyi-archive_viewer`）确认 GPL 组件的存在/不存在与所选方案一致。

---

### 🟠 P1-S3 · 三仓库零依赖漏洞监控与零完整性校验（无 Dependabot / SCA / SBOM / 哈希）

**【现象 + 证据】**

1. 三个仓库的 `.github/` 下**只有 `workflows/ci.yml` 一个文件**（`find WingMan/.github -type f` 结果唯一）。全仓搜索 `dependabot.yml` / `CODEOWNERS` / `.gitleaks*` / `.pre-commit-config.yaml` → **全部不存在**。
2. 全仓（`*.txt`/`*.toml`/`*.yml`/`Makefile`）搜索 `pip-audit` / `safety` / `bandit` / `semgrep` / `osv-scanner` / `trivy` / `grype` / `cyclonedx` / `sbom` → **零命中**。即：**没有任何机制会在依赖出现新 CVE 时告诉你**。
3. **锁定无哈希**：`grep -rn "require-hashes\|sha256:" WingMan/backend/*.txt Etude/backend/*.txt TideWatch/requirements.txt` → **零命中**。WingMan 锁定集是**手工 `pip freeze` 粘贴**（`requirements.lock.txt:17-19` 自述流程），TideWatch 的 `Makefile:73-75` 同样是 `pip freeze > requirements-lock.txt`——**`pip freeze` 输出不含哈希**。
4. 规模：WingMan 锁定 33 条（`requirements.lock.txt:22-54`）、Etude 直接依赖 6 条、TideWatch 1 条。WingMan 传递依赖含 `cryptography`、`httpx`、`starlette`、`anyio` 等**历史 CVE 高发组件**（仅陈述其为常见受影响组件，不指认任何具体未修复漏洞）。

**【为什么是问题（最坏后果）】**

两个层次叠加：① **版本固定防不了"同版本内容被换掉"**——这是 PyPI 上确实发生过的一类事件（恶意发布者覆盖同名同版本，或账号被盗后重传）。没有哈希时 `pip install -r lock.txt` **不比对任何字节**，装什么都算通过，供应链投毒在 CI 与用户机器上都无法被发现，因为**校验对象根本不存在**。② **没有监控则漏洞只能靠偶然**——一个已修复的高危漏洞可以在锁定文件里躺一年而 CI 永远绿着，用户拿到的是**已知可被利用**的版本而你毫不知情。`python-multipart` 就是一个具体例子（见 P1-S5）。

**【改法（三层，一天内可全落地）】**

```yaml
# 第一层：.github/dependabot.yml（三仓库各一份；WingMan/Etude 的 directory 为 "/backend"）
version: 2
updates:
  - package-ecosystem: pip
    directory: "/backend"
    schedule: { interval: weekly, day: monday }
    open-pull-requests-limit: 5
    groups:
      pip-minor-patch: { patterns: ["*"], update-types: ["minor", "patch"] }
  - package-ecosystem: github-actions
    directory: "/"
    schedule: { interval: weekly, day: monday }
  - package-ecosystem: docker        # 仅 TideWatch
    directory: "/"
    schedule: { interval: weekly, day: monday }
```

```yaml
# 第二层：现有 ci.yml 追加（先只观察，不 fail；换用带哈希的锁定集后可加 --require-hashes 强制校验）
  audit:
    name: 依赖漏洞扫描
    runs-on: ubuntu-latest
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@<SHA>
      - uses: actions/setup-python@<SHA>
        with: { python-version: "3.12" }
      - run: python -m pip install pip-audit cyclonedx-bom
      - run: pip-audit -r backend/requirements.lock.txt || true
      - run: cyclonedx-py requirements -i backend/requirements.lock.txt -o sbom.json   # 同时产出 SBOM
      - uses: actions/upload-artifact@<SHA>
        with: { name: sbom, path: sbom.json }
```

```yaml
# 第三层：.github/workflows/codeql.yml（Python 数据流 SAST）
name: CodeQL
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
  schedule: [{ cron: "0 3 * * 1" }]
permissions: { contents: read, security-events: write }
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<SHA>
      - uses: github/codeql-action/init@v3
        with: { languages: python }
      - uses: github/codeql-action/analyze@v3
```

哈希锁定（一次性，**不要用 `pip freeze`**）：

```bash
python -m pip install pip-tools
pip-compile --generate-hashes --output-file backend/requirements.lock.txt backend/requirements.txt
# TideWatch 的 Makefile:73-75 改为：
#   $(VENV_BIN)/python -m piptools compile --generate-hashes --output-file requirements.lock.txt pyproject.toml
```

与第一轮 C-8 / C-10 的关系：那两条是**可复现性**视角（"能不能装出一样的版本"）；本条是**安全视角**——没有锁定/没有 SCA 就无法建立漏洞扫描基线，也无法做哈希校验。Etude 的增量不只是"补锁定"，而是"**生成时必须 `--generate-hashes`、安装时必须 `--require-hashes`**"。

**【优先级】** P1（最高性价比）
**【工作量】** dependabot + audit 0.5 天（三仓库）；CodeQL 0.5 天；哈希锁定 0.5–1 天
**【验收标准】** ① 三仓库均有 `.github/dependabot.yml` 且 Dependabot 页面可见生效；② CI 日志出现 `audit` job 并打印当前依赖漏洞清单（哪怕"未发现"）；③ 锁定文件每条依赖带 `--hash=sha256:`，CI 用 `--require-hashes` 安装成功、故意改哈希后安装失败；④ CI 产物中存在 `sbom.json`。

---

### 🟠 P1-S4 · TideWatch 的 CI 未声明 `permissions:`（另两个仓库都声明了）

**【现象 + 证据】** `TideWatch/.github/workflows/ci.yml` 全文 113 行，`on:`（`:3-7`）之后**直接进入 `jobs:`（`:9`）**，**没有 `permissions:` 键**。对照组：`WingMan/.github/workflows/ci.yml:10-11` → `permissions: { contents: read }`；`Etude/.github/workflows/ci.yml:11-12` → 同，且 `:9-10` 的注释还解释了为什么只要读权限。

**【为什么是问题（最坏后果）】**

未声明时 `GITHUB_TOKEN` 会拿到**仓库默认权限集**（GitHub 对新建仓库长期默认"读+写全部"，除非账号层改为 read-only）。后果是 **CI 里跑的任意代码（含来自 fork 的 PR 中改过的测试代码）都持有一个可写仓库的令牌**。虽然三个 CI 都只用 `pull_request`、且未使用 secrets（§1 第 13/14 项，这两点是对的），但一旦将来某个 step 把 token 用出去、或某个 Action 被投毒，写权限就是实打实的破坏面。而**修复成本是加三行 YAML**。

顺带一处不一致：TideWatch 是"工程规范最好"的项目（第一轮全项 A），却是三仓库里**唯一**缺 CI 权限声明的——说明"规范好"不等于"安全默认好"。

**【改法】** 在 `on:` 之后、`jobs:` 之前插入：

```yaml
permissions:
  contents: read
```

**【优先级】** P1
**【工作量】** 5 分钟
**【验收标准】** `grep -n "permissions" TideWatch/.github/workflows/ci.yml` 命中；Actions 运行日志的 "GITHUB_TOKEN Permissions" 显示只读。

---

### 🟠 P1-S5 · WingMan `requirements.txt` 的下界覆盖 CVE-2024-53981 的受影响区间

**【现象 + 证据】**

1. `WingMan/backend/requirements.txt:8` → `python-multipart>=0.0.9`，**只有下界无上界**，语义上包含 `0.0.9`~`0.0.17`。
2. `python-multipart` 有已公开的 **DoS 漏洞 CVE-2024-53981**：畸形 `multipart/form-data` boundary 会让解析器逐字节记录日志，在 ASGI 应用里**阻塞事件循环**，一个恶意上传即可让服务停止响应；CVSS 3.1 **7.5（High）**；**修复版本 0.0.18**。**查询日期 2026-10-13**，来源：https://github.com/Kludex/python-multipart/security/advisories/GHSA-59g5-xgcq-4qw3 ；https://nvd.nist.gov/vuln/detail/CVE-2024-53981 （受影响 `< 0.0.18`，修复提交 `c4fe4d3cebc08c660e57dd709af1ffa7059b3177`）。
3. WingMan 的锁定集本身**是安全的**：`requirements.lock.txt:28` → `python-multipart==0.0.32`（> 0.0.18），且 `ci.yml:37` 与本地启动器消费的都是锁定集。**所以 CI 与默认启动路径不受影响。**

**【为什么是问题（最坏后果）】**

风险落在"不走锁定集"的路径上：项目同时维护 `requirements.txt`（面向人类、README/手动安装会用）与 `requirements.lock.txt`（面向启动器），两套声明的**安全底线不一致**。最坏后果：① 有用户/贡献者按 `requirements.txt` 手动建环境，装到 `0.0.9~0.0.17`，**本地服务暴露在 DoS 下**——而 P0-S1 已说明该服务还可能是零鉴权、甚至监听 `0.0.0.0` 的；② 自动化工具以 `requirements.txt` 为准做升级建议时，可能把你**降级**回带漏洞的版本。

同族问题在 Etude 侧换了形态：Etude 的 `requirements.txt` 里**完全没有** `python-multipart`，靠 `fastapi` 的传递约束兜底；而 Etude **无锁定文件**（第一轮 C-10），连"最终解析到哪个版本"都不固定。与 C-10 的关系：本条不是重复"Etude 无锁定文件"，而是补它的**安全面**——无锁定不仅影响可复现，还直接导致"无法做哈希校验、无法建立漏洞扫描基线"。

**【改法】**

```diff
 # WingMan/backend/requirements.txt：补上界 + 抬高安全下界（示例）
-python-multipart>=0.0.9
+python-multipart>=0.0.18,<1.0   # 下界必须 >= 0.0.18：更低版本存在 CVE-2024-53981
-fastapi>=0.110
+fastapi>=0.110,<1.0
-numpy>=1.26
+numpy>=1.26,<3.0
```

Etude 侧：在 `requirements.txt` 里**显式**加 `python-multipart>=0.0.18,<1.0`（不依赖传递约束），并配合 P1-S3 建立基线。

**【优先级】** P1（默认路径不受影响，但声明层与安全底线不一致）
**【工作量】** 0.5 小时（改声明）+ 0.5 小时（干净 venv 复验锁定集仍可装）
**【验收标准】** ① `grep -n "python-multipart" WingMan/backend/requirements.txt Etude/backend/requirements.txt` → 两处均带 `>=0.0.18` 与上界；② 干净 venv 装出的版本 ≥ 0.0.18；③ `pip-audit` 对两条路径均无 `python-multipart` 告警。

---

### 🟠 P1-S6 · WingMan 的 `.gitignore` 拦不住 `.env.*`，且三仓库均无推送级拦截

**【现象 + 证据】** `WingMan/.gitignore:22-25`：

```
# ---- 环境与密钥 ----
.env
.env.local
*.key
```

只枚举两个**字面量**。而 TideWatch 用通配：`TideWatch/.gitignore:29-31` → `.env` / `.env.*` / `*.key`。三仓库均无 `.pre-commit-config.yaml`（§1 第 3 项）。

**【为什么是问题（最坏后果）】**

`.env.production`、`.env.dev`、`.env.bak`、`.env.old` 全部**不在忽略范围内**。这类文件名极常见（调试时 `cp .env .env.bak`、部署时写 `.env.prod`、编辑器生成 `.env.local.example`）——只要有人 `git add -A`，**一个带真实 API Key 的配置就进了公开仓库**。而 WingMan 的 `.env` 明确包含 `LLM_API_KEY` / `EMBED_API_KEY`（`.env.example:16,37`），是**用户要付费的凭据**。

**与第一轮的关系（含一处更正）**：第一轮 §8 写「三旗舰 `.gitignore` 均已排除 `.env` / `*.key` / `config.json`」——**这句对 WingMan 不成立**：`WingMan/.gitignore` 里没有 `config.json`（WingMan 也不用它，用的是 SQLite `kv` 表，故无现实风险），且 `.env` 只覆盖两个字面量而非通配。第一轮的扫描结论"工作区未发现明文密钥"**是准确的**（本轮 `git ls-files` 复核仍成立）。本条补的是**将来**这一面：第一轮查"现在有没有"，本条查"以后进门时有没有人拦"。

**【改法】**

```diff
 # WingMan/.gitignore
 .env
-.env.local
+.env.*                 # 覆盖 .env.local / .env.prod / .env.bak / .env.*.bak
+!.env.example
 *.key
+*.pem
+*.p12
+*.pfx
+*.token
```

```yaml
# .pre-commit-config.yaml（三仓库各一份）
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks: [{ id: gitleaks }]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks: [{ id: ruff }]
```

> `rev` 请以两仓库当时最新 tag 为准（此处按 2026-10-13 既有发布写，落地前核对一次）——这与 P2-S9"版本固定"是同一思路。

**【优先级】** P1（防复发机制；当前无实际泄露）
**【工作量】** `.gitignore` 5 分钟；pre-commit 0.5 天（三仓库 + README 说明）
**【验收标准】** ① `touch .env.prod` 后 `git status --porcelain` 不显示该文件；② 受控测试分支上提交假 `sk-` 字符串 → `git push` 被 gitleaks 拦下。

---

### 🟠 P1-S7 · 三仓库都没有 `SECURITY.md`（无漏洞上报通道）

**【现象 + 证据】** `find WingMan Etude TideWatch -iname "SECURITY.md"` → **三仓库均无**（`.github/` 下也只有 `workflows/ci.yml`）；同时无 `CODEOWNERS`。

**【为什么是问题（最坏后果）】**

WingMan 这种"读进程内存/剪贴板、持有全部聊天记录"的工具，被研究者发现漏洞的概率是存在的（尤其 P0-S1 这类）。没有 `SECURITY.md` 时：① 研究者找不到私下上报途径，只能开 **public issue**——对 WingMan 而言，一条公开的"如何利用本地服务读走聊天记录"等于**把利用方法连同受害面一起公开**，而修复往往需要几天；② GitHub 的 **Private Vulnerability Reporting** 默认关闭，这个开关通常就写在 `SECURITY.md` 旁边；③ 首次遇到这类情况的人不会临场想清楚，第一反应常是错的（公开讨论、在 issue 里贴 PoC）。

**【改法】** 新建 `SECURITY.md`（三仓库各一份）：

```markdown
# 安全策略
## 上报漏洞
请**不要**开公开 issue。使用 GitHub 私密漏洞上报：仓库页 → Security → Report a vulnerability。
或邮件到 <你的地址>。
## 本项目的安全边界（重要）
- 服务默认只监听 127.0.0.1，**没有用户鉴权**。请勿改为 0.0.0.0 或暴露到公网。
- 数据目录（含聊天记录与 API Key）位于本地，不随仓库分发。
## 响应
初次回复目标 72 小时内；修复发布时致谢（除非你要求匿名）。
```

并在仓库 `Settings → Security` 开启三项：**Private vulnerability reporting**、**Dependabot alerts**、**Secret scanning + push protection**（与 P1-S3 互补：前者管"告警"，后者管"自动 PR"）。

**【优先级】** P1
**【工作量】** 0.5 小时（三份文件 + 三个仓库设置）
**【验收标准】** 三仓库 Security 页出现 policy 条目；三项开关均为 Enabled。

---

### 🟠 P1-S8 · WingMan 前端有 85 处 `innerHTML`，却没有任何自动化守卫

**【现象 + 证据】**

1. `grep -c "innerHTML" WingMan/frontend/index.html` → **85**；`grep -c "innerHTML" Etude/backend/frontend/index.html` → **0**。**需要守卫的恰好是没守卫的那一方。**
2. WingMan 有转义函数且本轮**逐处抽查未发现活的 XSS**：定义在 `index.html:1260`（`const esc = (s) => String(s ?? "").replace(/[&<>"']/g, ...)`）；对象列表 `:1896-1904`、对象/渠道选择器 `:2219-2237` 每个插值都套 `esc()`；唯一裸插值的 `body`（`:1390` `openModal` 里 `${body}`）经 5 个调用点（`:1640`/`:2141`/`:2764`/`:2997`/`:3275`）逐个核查，确认动态部分**只含数字与静态文案**，用户可控的 `title`/`sub` 都走了 `esc()`（`:1387-1388`）。
3. WingMan 的 CI **无任何前端安全守卫**：`ci.yml:67-80` 只用 `vm.Script` **编译** `<script>` 块查语法，不检查 `innerHTML` 转义。
4. Etude 有守卫但有两处局限：`Etude/.github/workflows/ci.yml:103-110` 只打 `::warning::`（**不是 error**，`exit` 未触发），且只扫 `backend/frontend/index.html` 一个文件。

**【为什么是问题（最坏后果）】**

当前**安全**，但这是"靠人每次记得写 `esc()`"换来的，不是"靠机制"。WingMan 的业务特性放大了风险：它渲染的是**从第三方导入的聊天记录**——`previewHTML`（定义 `index.html:3290-3306`，调用点 `:3401`）回显发件人与消息前 60 字（`esc(m.sender)` / `esc(m.text.slice(0, 60))`），`capHtml`（定义 `:4333`）同理。**同一函数下若将来新增字段（群名 / 转发来源 / @提及）忘了 `esc`，就是 stored XSS**——攻击者可以是"你给我发一条消息，我第一次导入你的记录时执行你的脚本"，而在本地服务 + 零鉴权的语境下（P0-S1），这条链通向读取 `/api/chats` 全量数据。85 个插值点漏一个的概率不低，而**漏了不会有任何东西报警**。

> **行号更正说明**：本报告初稿曾把 `previewHTML` 引作 `:3280-3285`，该区间实为上文确认弹窗的收尾与 `catch` 块。已由 **frontend-eng** 在交叉核对中指出并更正为定义 `:3290`、调用 `:3401`、`capHtml:4333`（本轮已实测复核）。**[待协作] 落地时应与 frontend-eng 的 `round2/frontend-engineering-review.md`（F-1b）合并为同一个守卫脚本，不要各写一份**；其 F-1b 额外给出了 A 档（第三方导入渲染）的针对性白名单断言，与本条的"全文件插值检查"是正交关系，两者叠加才完整。

**与第一轮的关系**：第一轮注意到"Etude 的 `innerHTML` 守卫值得 WingMan 照抄"。**本条是对那条建议的修正——照抄 Etude 那份不够用**：它 (a) 只 warning 不 fail，(b) 只扫一个文件；而 WingMan 是 85 处 `innerHTML` 的一方。真正需要的是**会 fail 的、覆盖整个 `frontend/` 的**版本。

**【改法】**

```python
# WingMan/scripts/check_innerhtml.py（新增，CI 调用）
"""只允许两种 innerHTML 赋值：清空（= ""），或整条模板里每个插值都套了 esc()/encodeURIComponent()。"""
import re, sys
from pathlib import Path
ALLOW_CLEAR = re.compile(r'=\s*(""|\'\')\s*;')
INTERP = re.compile(r"\$\{([^}]*)\}")

def main() -> int:
    bad = []
    for f in Path("frontend").glob("*.html"):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if "innerHTML" not in line or ALLOW_CLEAR.search(line):
                continue
            for expr in INTERP.findall(line):
                if not re.search(r"\b(esc|encodeURIComponent)\s*\(", expr) \
                   and not re.fullmatch(r"[\s\d+\-*/%().,]*", expr):
                    bad.append(f"{f}:{i}: 未转义的插值 ${{{expr}}}")
    print("\n".join(bad) if bad else "innerHTML 转义守卫通过")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
```

```yaml
# WingMan/.github/workflows/ci.yml 末尾追加
      - name: 前端转义守卫（禁止未转义的 innerHTML 插值）
        run: python scripts/check_innerhtml.py
```

顺手把 Etude 的守卫从 `::warning::` 升级为 `exit 1`（`ci.yml:108-109`）。**落地提示**：先在本机跑一遍把 85 处里"跨多行模板"的少量误报加白名单，再设为 CI 必过——否则会变成又一个"红了就绕过"的关卡。

**【优先级】** P1
**【工作量】** 0.5 天（含误报调平）
**【验收标准】** ① 故意加 `el.innerHTML = `<b>${x}</b>`;` → CI 该步骤失败并指行号；② 改回 `esc(x)` → CI 通过；③ 脚本在真实文件上 `exit 0`（无假阳性）。

---

### 🟡 P2-S9 · 供应链加固：所有第三方 Action / 工具未按 commit SHA 固定

**【现象 + 证据】** 三个 CI 全部只写**可变的 major tag**：`WingMan/ci.yml:24,27`（`actions/checkout@v4`、`actions/setup-python@v5`）；`Etude/ci.yml:25,27,56,58,84` 同上；`TideWatch/ci.yml:14-15,36-37,57-58` 同上，另 `:18` `python -m pip install --upgrade pip ruff`——`ruff` 亦未固定版本。

**【为什么是问题（最坏后果）】**

`@v4` 是**可被移动的引用**：仓库维护者（或拿到其账号的攻击者）可把该 tag 重定向到新 commit。这是 `tj-actions/changed-files`（2025-03）那类事件的成因——所有引用 `@v45` 的仓库在**下一次 CI 运行时**即被注入并可能泄露 token/密钥。最坏后果是**供应链投毒**：你没改任何代码，但 CI 里跑的代码不是你写的。

严重性差异须说清：这三处用的是 **GitHub 官方 Action** 而非第三方，风险显著更低，所以本条是**加固**而非"正在被利用的漏洞"。但对将来要接 Release 发布的仓库，提前固定是零成本的。

**【改法】**

```yaml
# 用 SHA 固定，右侧保留可读版本号；dependabot 会自动帮你更新 SHA
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683   # v4.2.2
- uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b # v5.3.0
```

```bash
# 查 tag 对应 SHA（只读）
git ls-remote https://github.com/actions/checkout refs/tags/v4.2.2
git ls-remote https://github.com/actions/setup-python refs/tags/v5.3.0
```

`ruff` 固定为 `ruff==<具体版本>`，与 `TideWatch/pyproject.toml:27` 的 `dev` extra 保持一致。

**【优先级】** P2（官方 Action，风险低；纯加固）
**【工作量】** 0.5 小时（三仓库）
**【验收标准】** 三份 `ci.yml` 中所有 `uses:` 均带 40 位 SHA，且与注释的 tag 一致。

---

### 🟡 P2-S10 · WingMan 把用户原文写进 `%TEMP%` 的固定文件名（CWE-377），且 debug 日志可能落盘分析结果

**【现象 + 证据】**

1. `WingMan/backend/app/adapters/registry.py:373-384`：

   ```python
   tmp = Path(tempfile.gettempdir()) / f"wingman_paste_{hashlib.md5(text.encode('utf-8','ignore')).hexdigest()[:8]}{suffix}"
   tmp.write_text(text, encoding="utf-8")   # 固定名 + 打开即截断
   ```
   对照同仓库**做对了**的地方：`routes_data.py:77,99` 用 `tempfile.mkdtemp(prefix=...)` 建**随机**目录。同一个人两处两种写法，其中一种不安全。

2. 日志**写文件且滚动保留**：`main.py:47-58` 的 `RotatingFileHandler(LOG_DIR/"wingman.log", maxBytes=2*1024*1024, backupCount=3, ...)` → 上限约 **8 MB 明文长期保留**；`LOG_DIR` 见 `config.py:65`（`BACKEND_DIR/"logs"`）。

3. 有一处**把分析结果整体打出**：`WingMan/backend/app/engine/analyzer.py:66` → `log.debug("分析结果：%s", result.model_dump())`，该 `result` 是 `PeerAnalysis`，即**对聊天内容推理之后的产出**。默认 `log_level=info`（`config.py:161`、`.env.example`）**所以默认不落盘**；但排障时会改——`.env.example` 服务段直接给出 `LOG_LEVEL=info` 这一行，且 `desktop.py:121` 的错误提示直接引导用户去看 `wingman.log`。

**【为什么是问题（最坏后果）】**

- **临时文件**：文件名 = 用户粘贴原文的 MD5 前 8 位，属**可预测的内容寻址名**。① 攻击者可通过字典反推判断"用户是否粘贴过某段特定文本"（在"读剪贴板"类产品的语境下，这个侧信道比看起来敏感）；② `write_text` 是"打开即截断"语义且路径完全可预测，同用户下另一进程可抢先创建**硬链接**指向别处（Windows 创建硬链接通常不需特殊权限），于是**私密聊天内容被写到攻击者指定位置**，`finally` 的 `unlink` 只能删链接、删不掉副本；③ 崩溃/强杀时文件留在 `%TEMP%` 且为明文。风险等级说明：`%TEMP%` 按用户隔离且有默认 ACL，主要威胁来自"同一用户会话下的其他进程"，故为 P2 而非 P0。
- **日志**：后果不是"立刻泄露"，而是**制造用户不知情的持久副本**。用户以为数据只在被 `.gitignore` 明确保护、且在 README 里被讲述的 `backend/data/` 里；一旦按排障指引开 `debug`，**聊天推理结果就被复制到 `backend/logs/wingman.log`** 并滚动保留 8 MB。后续两条放大路径：用户把 `logs/` 打包发给别人排障（`desktop.py:121` **正在引导这件事**）；或备份时压缩整个目录上传——而 `logs/` 恰好被 `.gitignore:51` 忽略，**忽略列表反而给了他"这目录不重要/不敏感"的错觉**。

**【改法】**

```python
# 临时文件：mkstemp —— 原子创建 + 随机名 + 收紧权限
import os, tempfile
fd, name = tempfile.mkstemp(prefix="wingman_paste_", suffix=suffix)
tmp = Path(name)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return import_file(store, tmp, ...)
finally:
    tmp.unlink(missing_ok=True)
```

```python
# 日志：analyzer.py:66 改为只记形状，不记内容
log.debug("分析结果：kind=%s options=%d branches=%d",
          getattr(result, "kind", "?"),
          len(getattr(result, "options", []) or []),
          len(getattr(result, "branches", []) or []))
```

再在 `_setup_logging` 里对 debug 级别加一条醒目的一次性警告（"已开启 debug 日志：日志文件可能含聊天内容，排障完成后请改回 info"），并在 `docs/TROUBLESHOOTING.md` 与 `desktop.py:121` 注明"发日志前先打开确认没有聊天内容"。

**【优先级】** P2（默认配置不触发日志问题；临时文件为同用户内威胁）
**【工作量】** 0.5 小时 + 2 条测试
**【验收标准】** ① 以同一文本连续两次调用粘贴导入 → 两次临时路径**不同**，且结束后 `%TEMP%` 无 `wingman_paste_*` 残留；② 以 `LOG_LEVEL=debug` 跑一次 `analyze`，断言 `wingman.log` 中**不出现**被测消息文本，且启动时打印了隐私提示。

---

### 🟡 P2-S11 · 版权人写法不一致、且无第三方声明

**【现象 + 证据】** 三份 LICENSE 除署名行外完全一致（同为标准 MIT 全文）：

| 仓库 | 署名行 | 证据 |
|---|---|---|
| WingMan | `Copyright (c) 2026 WingMan Contributors` | `WingMan/LICENSE:3` |
| Etude | `Copyright (c) 2026 Etude contributors` | `Etude/LICENSE:3` |
| TideWatch | `Copyright (c) 2026 tidewatch contributors` | `TideWatch/LICENSE:3` |

差异有两处：`Contributors`（首字母大写）vs `contributors`（全小写），以及项目名大小写 `tidewatch` vs `TideWatch`。同时 `TideWatch/pyproject.toml:12` 又写了一遍 `authors = [{ name = "tidewatch contributors" }]`——**元数据里始终没有出现自然人作者这一层，也没有年份之外的联系方式**。三仓库均无 `THIRD_PARTY_NOTICES.md`。

**【为什么是问题（最坏后果）】**

严重度确实低（MIT 不要求署名统一），但有两个实际影响：① **归属清晰度**——机器扫描（GitHub license detection、SPDX 工具、企业 OSS 审查流水线）会把三份文件解析为**三个不同的版权主体**；若将来需要"这批项目出自同一作者"的证据链，现在没有任何一份文件把它写清楚，**你自己的名字在三个仓库里一次都没出现过**。这与第一轮"commit 元数据泄露 QQ 邮箱"正好相反：那条是"暴露太多"，本条是"署名太少"。② **无第三方声明**——Etude 因 P0-S2 的 GPL 依赖，这已是**硬需求**；WingMan 也依赖 `cryptography`（Apache-2.0/BSD）、`numpy`（BSD-3）、`starlette`（BSD-3）、`python-multipart`（Apache-2.0）等，随二进制分发正常应附许可文本（SBOM 已在 P1-S3 落地）。

【改法】① 三仓库统一署名并显式署自然人，与 `pyproject.toml` 的 `authors` 保持一致：

```
Copyright (c) 2026 <你的名字或 GitHub handle> and WingMan Contributors
```

② 新增 `THIRD_PARTY_NOTICES.md`（至少 Etude 必做），列直接依赖的包名/版本/许可证/上游链接（SBOM 已在 P1-S3 落地）。

**【优先级】** P2
**【工作量】** 署名统一 0.5 小时；`THIRD_PARTY_NOTICES.md` 0.5 天
**【验收标准】** 三份 LICENSE 署名行一致；`THIRD_PARTY_NOTICES.md` 存在且覆盖全部直接依赖。

---

### 🟡 P2-S12 · TideWatch 的 Docker 基础镜像未按 digest 固定（其余容器实践是正面的）

**【现象 + 证据】** `TideWatch/Dockerfile:12` → `FROM python:3.12-slim AS base`，只有 tag，没有 `@sha256:...`。

**同时必须记下这个仓库做对的**（不重复，但不该被忽略）：`Dockerfile:33-36` 创建 `uid 10001` 的 `tidewatch` 用户并 `USER tidewatch`，注释明确写了理由"这个工具会读外部数据，不该以 root 身份跑"——**这是三个仓库里唯一的容器运行时最小权限实践**；`TideWatch/.dockerignore:19-21` 还把 `data/raw` 排除并注明"可能含个人信息，绝不能被打进镜像分发出去"，**镜像层的数据边界也守住了**。

**【为什么是问题（最坏后果）】**

`python:3.12-slim` 是**可变引用**：上游重新发布（哪怕只是补丁级）会改变你构建出的镜像内容。没有 digest 时 `docker build` **无法复现**，也无法证明"今天构建的镜像和昨天是同一个"。对 TideWatch 这种"以可复现实验为卖点"的项目（`pyproject.toml` + `make freeze` + 配置指纹），这是叙事与实现的落差。最坏后果：某个被投毒/被回滚的基镜像在你不知情的情况下进入构建产物。

**【改法】**

```dockerfile
FROM python:3.12-slim@sha256:<digest> AS base
```

```bash
docker buildx imagetools inspect python:3.12-slim | grep Digest   # 取 digest
```

配合 P1-S3 的 `dependabot.yml`（已含 `package-ecosystem: docker`），让 digest 能被自动更新。

**【优先级】** P2
**【工作量】** 15 分钟
**【验收标准】** `Dockerfile:12` 含 `@sha256:`；`docker build` 成功；dependabot 能识别 docker ecosystem。

---

## 3. 跨项目共性清单（S-1 … S-15）

| 编号 | 条目 | 优先级 | WingMan | Etude | TideWatch | §2 |
|---|---|---|---|---|---|---|
| **S-1** | 本地服务零鉴权 + 无 Host 校验（DNS rebinding / CSRF）；WingMan 另可 `--host 0.0.0.0` | **P0** | ✅ + 可开 0.0.0.0 | ✅（连 CORS 都没有） | ⊘ 无 HTTP 服务 | P0-S1 |
| **S-2** | 分发包含 GPL 组件但声明 MIT | **P0** | ⊘ | ✅ `edge-tts` GPL-3.0 | ⊘ | P0-S2 |
| **S-3** | 无依赖漏洞监控 / 无 SCA / 无哈希锁定 / 无 SBOM | P1 | ✅ | ✅ | ✅ | P1-S3 |
| **S-4** | CI 未声明 `permissions:` | P1 | ⊘ 已声明 | ⊘ 已声明 | ✅ **缺** | P1-S4 |
| **S-5** | 依赖下界低于已知 CVE 修复版本 | P1 | ✅ `>=0.0.9` | ⚠️ 靠传递约束兜底 | ⊘ 仅 PyYAML | P1-S5 |
| **S-6** | `.gitignore` 不拦通配 env / 无推送级拦截 | P1 | ✅ `.env.*` 缺失 | ⚠️ 无通配、无拦截 | ⚠️ 有通配但无拦截 | P1-S6 |
| **S-7** | 无 `SECURITY.md` / 无私密漏洞上报 | P1 | ✅ | ✅ | ✅ | P1-S7 |
| **S-8** | 前端渲染无自动化转义守卫（且 `innerHTML` 用最多的一方恰好无守卫） | P1 | ✅ 85 处零守卫 | ⊘ 0 处且已有守卫（建议升级为 fail） | ⊘ 无前端 | P1-S8 |
| **S-9** | 第三方 Action / 工具未按 SHA 固定 | P2 | ✅ | ✅ | ✅（另 `ruff` 未固定） | P2-S9 |
| **S-10** | 敏感数据写入可预测名临时文件 + debug 日志可能落盘 | P2 | ✅ | ⊘ 未发现 | ⊘ 未发现 | P2-S10 |
| **S-11** | 版权署名不一致 / 无第三方声明 | P2 | ✅ | ✅（且有 GPL 依赖，属硬需求） | ✅（`pyproject.toml:12` 同样未署自然人） | P2-S11 |
| **S-12** | 容器基础镜像未按 digest 固定 | P2 | ⊘ 无容器 | ⊘ 无容器 | ✅ | P2-S12 |
| **S-13** | 上传接口无大小/类型上限 | P2 | ✅ | ⊘ 无上传接口 | ⊘ | 并入 S-1 |
| **S-14** | 静态文件目录穿越 | — | ✅ 安全（`StaticFiles`） | ✅ 安全（正则白名单） | ⊘ | §6.3（无发现） |
| **S-15** | TideWatch 的 HTTP 服务面 | — | — | — | ✅ **不存在**（纯 CLI） | §6.3（无发现） |

**图例**：✅ 命中 / ⚠️ 部分 / ⊘ 不适用或已做对。

**一句话读法**：**WingMan 是 S-1/S-6/S-8/S-10/S-13 的集中地**（"能读用户隐私数据"的那一方，安全面也最需加固）；**Etude 唯一的 P0 是许可证**（S-2），但它是三仓库里唯一"有 CI 安全 job"的；**TideWatch 的代码与容器实践最好，短板集中在"供应链机制层"**（S-3/S-4/S-9/S-12）而非代码层。

---

## 4. 落地路线（2 周，每个动作可独立成 commit）

### 第 1 周 —— 止血与最高性价比机制

| # | 动作 | 涉及 | 工作量 | 验收标准 |
|---|---|---|---|---|
| **A1** | **S-1**：`TrustedHostMiddleware` + 本地一次性令牌 + `--host` 非回环默认拒绝（需 `--allow-lan`）+ `CORS_ORIGINS` 改回环 + 上传白名单与 64 MB 上限 | WingMan / Etude | 0.5–1 天 | Host 为 `evil.com` → 400；无令牌 → 403；`--host 0.0.0.0` 未加 `--allow-lan` 不启动；`.exe` 上传 → 400 |
| **A2** | **S-2**：定方案（A/B/C）并执行；打包脚本同步处理 `edge_tts`；新增 `THIRD_PARTY_NOTICES.md` | Etude | 0.5–1 天 | `build_exe.py:149` 与方案一致；声明文件存在 |
| **A3** | **S-4**：TideWatch CI 加 `permissions: contents: read` | TideWatch | 5 分钟 | `grep -n permissions` 命中 |
| **A4** | **S-3（一、二层）**：三仓库加 `dependabot.yml`（pip + actions，TideWatch 另加 docker）；CI 加 `audit` job（先不 fail） | 三仓库 | 0.5 天 | 三份 dependabot 生效；CI 日志出现漏洞清单 |
| **A5** | **S-7**：三仓库加 `SECURITY.md` + 开启三项 Security 设置 | 三仓库 | 0.5 小时 | Security 页出现 policy；三项开关 Enabled |
| **A6** | **S-6（一层）**：WingMan `.gitignore` 补 `.env.*`、`!.env.example`、`*.pem/*.p12/*.pfx/*.token` | WingMan | 5 分钟 | `touch .env.prod` 后 `git status` 不显示 |
| **A7** | **S-5**：`requirements.txt` 补上界，`python-multipart` 下界抬到 `>=0.0.18`；Etude 显式声明该依赖 | WingMan / Etude | 1 小时 | 两处均带 `>=0.0.18` 与上界；干净 venv 装出的版本 ≥ 0.0.18 |
| — | 🔴 若第一轮"`Self-Mind` 转 Private"尚未做，本周必须完成 | 账号 | 2 分钟 | 仓库不可公开访问 |

### 第 2 周 —— 机制补齐与精细化

| # | 动作 | 涉及 | 工作量 | 验收标准 |
|---|---|---|---|---|
| **B1** | **S-8**：新增 `scripts/check_innerhtml.py` 并接入 CI；Etude 守卫升级为 fail。**与 frontend-eng 的 `frontend-engineering-review.md` F-1b 合并为同一个脚本**（其 A 档导入渲染白名单断言与本条的全文件插值检查正交，叠加使用） | WingMan / Etude | 0.5 天 | 故意插入未转义插值 → CI 失败并给行号；真实文件无假阳性；给 `previewHTML`（`:3290`）新增一个字段而漏 `esc` 时，F-1b 断言先变红 |
| **B2** | **S-3（三层）**：CodeQL workflow | 三仓库 | 0.5 天 | Actions 出现 CodeQL 任务且首次分析完成 |
| **B3** | **S-3（哈希层）**：`pip-compile --generate-hashes` 重建锁定集；CI 改 `--require-hashes`；TideWatch `Makefile:73-75` 同步 | WingMan / TideWatch | 0.5 天 | 锁定集含 `--hash=sha256:`；改哈希后安装失败 |
| **B4** | **S-6（二层）**：三仓库加 `.pre-commit-config.yaml`（gitleaks + ruff），README 加 "首次 clone 后 `pre-commit install`" | 三仓库 | 0.5 天 | 受控分支提交假 `sk-` → `git push` 被拦 |
| **B5** | **S-10 + S-13**：`registry.py` 改 `mkstemp`；`analyzer.py:66` 日志改只记形状 + debug 提示；上传上限（若 A1 未含） | WingMan | 0.5 天 | §2 P2-S10 两条测试通过 |
| **B6** | **S-9**：三仓库 `ci.yml` 的 `uses:` 全改 40 位 SHA；`ruff` 固定版本 | 三仓库 | 0.5 小时 | 所有 `uses:` 带 SHA 且与注释 tag 一致 |
| **B7** | **S-11 + S-12**：统一三处版权署名；Etude 补 `THIRD_PARTY_NOTICES.md`；TideWatch 基础镜像固定 digest | 三仓库 | 0.5 天 | 署名一致；`Dockerfile:12` 含 `@sha256:` |

**排序说明**：A3/A4/A6 加起来不到 1 小时，却把"CI 权限""依赖漏洞""密钥进门"三类最常见入口一次性补上——**时间只够做三件事就做这三件**。B1/B5 修的是"WingMan 特有、与用户隐私直接相邻"的面，因为不影响当前正确性，放在第二周。

---

## 5. 待确认项

1. **TideWatch `make freeze` 产出的文件是否被任何人消费** —— `Makefile:73-75` 写出 `requirements-lock.txt`，但仓库内跟踪的是 `requirements.txt`（`PyYAML>=6.0`）。与第一轮架构报告的同一条待确认相关；本轮安全侧判断是：若无人消费，则哈希锁定在 TideWatch 上"没有落点"。**待确认**
2. **WingMan `requirements.lock.txt` 中部分版本号无法离线验证** —— 例如 `fastapi==0.142.2`、`starlette==1.7.0`、`cryptography==50.0.2`、`numpy==2.4.6`。本次为只读静态评审、未联网解析 PyPI，**不对其真伪下结论**。落地 A7/B3 时请在干净环境 `pip install --dry-run` 复验。**待确认**
3. **P0-S2 的 GPL 定性属法律判断** —— 本报告只断言"MIT 声明与进程内链接 GPL-3.0 组件的事实存在张力"，**未断言"已违法"**。若 Etude 曾有商业化/商业许可计划，建议就"聚合 vs 衍生"咨询一次法律意见；方案 A/B 是可执行的工程应对，但不替代法律咨询。**待确认**
4. **`Etude/ci.yml:103-110` 的守卫为何只 warning 不 fail** —— 是刻意（怕误报阻断）还是疏漏？影响 S-8 中"顺手升级为 fail"这条建议的可行性。**待确认**
5. **Etude 是否真把 `edge-tts` 打进了已发布的 Release 二进制** —— 本次只读到打包配置的意图（`build/etude.spec`、`scripts/build_exe.py:149`），**未验证 Release 附件实际内容**。建议用 `pyi-archive_viewer` 实测确认后再定 S-2 的紧急程度。**待确认**
6. **WingMan 是否存在 `.env.*` 变体文件** —— S-6 基于"文件名模式可被创建"；本次 `git ls-files` 复核**未发现任何已提交的 `.env.*`**。**当前无泄露，属预防性发现。**
7. **三仓库的账号级安全开关状态**（Dependabot alerts / Secret scanning / Private vulnerability reporting）—— 属**账号侧设置而非代码**，浅克隆无法读取。若这些开关**已经**打开，则 S-3 / S-7 的严重度可相应下调。建议作者在 `Settings → Security` 逐项确认。**待确认**

---

## 6. 与第一轮报告的关系

### 6.1 全新条目（第一轮完全未涉及）

- **S-1** 本地服务零鉴权 + DNS rebinding / CSRF + `--host 0.0.0.0` 无警告 → **服务暴露面**
- **S-2** Etude 的 GPL-3.0 依赖与 MIT 声明冲突 → **许可证兼容性**
- **S-3** 无 dependabot / SCA / 哈希锁定 / SBOM → **依赖漏洞治理 + 完整性校验**
- **S-4** TideWatch CI 缺 `permissions:` → **CI 权限最小化**
- **S-5** 依赖下界低于 CVE 修复版本 → **依赖版本安全性**（第一轮只查"有没有上下界"）
- **S-6** `.gitignore` 通配覆盖度 + pre-commit 拦截 → **防复发机制**（第一轮只做"现在有没有"的静态扫描）
- **S-7** 无 `SECURITY.md` / 无私密漏洞上报 → **漏洞披露通道**
- **S-8** 前端 85 处 `innerHTML` 零守卫 → **前端回归守卫**（与第一轮建议同主题但结论不同，见 6.2）
- **S-9** Actions 未 SHA 固定 → **CI 供应链**
- **S-10** 可预测临时文件名 + debug 日志落盘 → **敏感数据落盘边界**
- **S-11** 版权署名不一致 / 无第三方声明 → **许可归属与合规**
- **S-12** 容器基础镜像 digest 固定 → **容器供应链**
- **S-13** 上传接口无大小/类型上限 → **服务输入边界**
- **S-14 / S-15** 静态目录穿越与 TideWatch 无服务面 → **正面结论**（供后续回归参照）

### 6.2 与第一轮条目的关系（补充角度，非重复）

| 本报告 | 相关第一轮条目 | 增量 |
|---|---|---|
| **S-1** | **C-6「CORS 过于宽松」** | C-6 描述的是**配置值本身**；本条补①**它不构成防护**（CORS 管不了同源的 DNS rebinding，且 **Etude 根本没有 CORS 中间件——第一轮对 Etude 的这一句与事实不符**，见 §1 第 19 项）；②真正能拦住攻击链的是 **Host 校验 + 令牌**；③WingMan 另有 **`--host 0.0.0.0` 无警告**这条路径 |
| **S-3** | **C-8「无 `pyproject.toml`」**、**C-10「Etude 无锁定文件」** | 那两条是可复现性视角；本条是安全视角——没有锁定/SCA 就无法建立漏洞扫描基线、无法做哈希校验 |
| **S-5** | **C-10** + 第一轮对"Etude `requirements.txt` 带上下界（好习惯）"的**正面评价** | 第一轮确认了"有上下界"，但**未检验下界取值是否安全**。本条指出 Etude 的好习惯在 `python-multipart` 上靠传递依赖兜底，而 WingMan 的 `>=0.0.9` 明确低于 CVE 修复线 |
| **S-6** | §8「无硬编码密钥」+「三旗舰 `.gitignore` 均已排除 `.env` / `*.key` / `config.json`」 | 那条是**静态扫描结论**（正确，本轮复核仍成立）；本条是机制面，并**更正**了第一轮对 WingMan `.gitignore` 的描述 |
| **S-7** | §8「Etude CI 有独立 `secrets` 隐私红线 job」+「建议 WingMan 照抄」 | **不可互相替代**：CI greps 是"事后扫描"，`SECURITY.md` 解决的是"研究者先找谁"，两个不同问题 |
| **S-8** | §8「Etude 有 `innerHTML` XSS 守卫」+「建议 WingMan 照抄」 | **对那条建议的修正**：照抄不够用——它 (a) 只 warning 不 fail（`Etude/ci.yml:108-109` 未 exit），(b) 只扫单文件；而 WingMan 恰是 **85 处**的一方、Etude 是 **0 处**。需要的是**会 fail 且覆盖 `frontend/`** 的版本 |
| **S-11** | §2.3「commit 元数据泄露 QQ 邮箱」 | 那条是**隐私过度暴露**，本条是**署名不足**（两个相反的偏差）；另 `TideWatch/pyproject.toml:12` 同样未署自然人 |
| **S-14/S-15** | — | 纯**正面结论**，记录在案以避免后续改动把这层保护删掉 |

### 6.3 本轮明确"无发现"的项（不为凑数编造）

1. **已跟踪的敏感文件** —— `git ls-files` 审计：WingMan 仅 `.env.example`，Etude / TideWatch 无任何 `.env` / `*.key` / `config.json` / `*.db` / `*.sqlite3` / cookie / 私钥。与第一轮静态扫描结论一致。
2. **`pull_request_target`** —— 三个 `ci.yml` 全部只用 `pull_request`（各自 `:6`），**零命中**。
3. **secrets 暴露给 PR** —— 三份 `ci.yml` **完全未使用 `secrets.*`**；Etude `ci.yml:9-10` 还注释了"发布凭据永远不经过第三方"。
4. **WingMan 前端存在活的 XSS** —— **未发现**。85 处 `innerHTML` 逐处抽查（对象列表 `:1896-1904`、选择器 `:2219-2237`、`openModal` 的 `title`/`sub` `:1387-1388`、5 个 `confirmWithCountdown` 调用点）**全部套了 `esc()`**；唯一裸插值的 `body` 其动态部分只含数字与静态文案。**当前安全，缺的是回归守卫（即 S-8）。**
5. **静态文件目录穿越 / TideWatch 的 HTTP 服务面** —— 前者**未发现**（WingMan 用 Starlette `StaticFiles`；Etude 用正则白名单）；后者**不存在**（全仓搜索 `uvicorn`/`fastapi`/`Flask`/`http.server`/`socketserver` → 零命中，TideWatch 是纯 CLI 工具）。
6. **TideWatch 容器权限** —— **已做对**（`Dockerfile:33-36` 非 root；`.dockerignore:19-21` 排除 `data/raw`）。
7. **`pywebview` 与 `PyInstaller` 许可证** —— **与 MIT 兼容**（BSD-3-Clause；GPL-2.0 + Bootloader-exception），详见 P0-S2。

---

## 附录：本轮证据清单（可复核）

以下命令均为**只读**，未修改任何文件：

```bash
# 已跟踪文件审计 → 三仓库无 .env / *.key / config.json / *.db / cookies（仅 WingMan 的 .env.example）
for r in WingMan Etude TideWatch; do git -C $r ls-files; done
# 供应链防护配置 → 全部不存在
find WingMan Etude TideWatch -iname "SECURITY.md" -o -iname "dependabot.yml" -o -iname "CODEOWNERS" \
     -o -iname ".gitleaks*" -o -iname ".pre-commit-config.yaml"
# 安全工具 / 哈希锁定 → 均零命中
grep -rniE "pip-audit|safety|bandit|semgrep|osv-scanner|trivy|grype|syft|cyclonedx|sbom" WingMan Etude TideWatch
grep -rn "require-hashes\|sha256:" WingMan/backend/*.txt Etude/backend/*.txt TideWatch/requirements.txt
# 入站鉴权搜索（命中全是出站 Authorization）→ 无入站校验；Host 校验 → 零命中
grep -rniE "authorization|bearer|x-api-key|Depends\(|HTTPBasic|OAuth2|csrf" WingMan/backend/app Etude/backend/app
grep -rn "TrustedHost" WingMan Etude
# Etude 中间件 → 零命中（无 CORS / 无任何 add_middleware）
grep -rn "CORS\|add_middleware\|middleware" --include=*.py Etude/backend
```

**涉及的外部来源（查询日期均为 2026-10-13）**：

| 用途 | 链接 |
|---|---|
| CVE-2024-53981（`python-multipart` DoS，修复于 0.0.18） | https://github.com/Kludex/python-multipart/security/advisories/GHSA-59g5-xgcq-4qw3 · https://nvd.nist.gov/vuln/detail/CVE-2024-53981 |
| `edge-tts` = GPL-3.0 | https://pypi.ac.cn/project/edge-tts · https://licensie.com/python/packages/edge-tts/6.1.13 · https://github.com/rany2/edge-tts |
| `pywebview` = BSD-3-Clause（兼容） | https://pypi.org/project/pywebview/6.2.1/ |
| PyInstaller = GPL-2.0 + Bootloader-exception（不污染产物） | https://pyinstaller.org/_/downloads/en/v4.0/pdf/ |

**方法与局限声明**：本轮为**只读静态评审**，未安装依赖、未运行被测程序、未联网解析 PyPI 元数据、未验证已发布二进制的实际内容。因此"GPL 冲突是否已在分发包中实际发生"（待确认 #5）、"锁定集版本号是否真实存在"（待确认 #2）两类结论**未经运行验证**，已逐条标注为待确认。§6.3 的"无发现"仅代表**在所检查的静态范围内未发现**，不等于"不存在问题"。
