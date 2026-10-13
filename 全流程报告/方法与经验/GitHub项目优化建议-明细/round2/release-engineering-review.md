---
tags: [领域/方法, 类型/报告]
评审日期: 2026-10-13
评审轮次: 第二轮
评审维度: 发布分发与版本治理
评审对象: github.com/whyao56 三旗舰（WingMan / Etude / TideWatch）
评审方式: 本地浅克隆静态阅读（未安装依赖、未执行构建、未运行被测程序）
---

# 第二轮评审 · 发布分发与版本治理

**评审员**：release-eng　**覆盖**：Windows 桌面分发完整性、版本号单点定义、CHANGELOG/SemVer 一致性、发布自动化、可安装性路径、Docker 产物、构建产物卫生
**口径**：全部结论基于 `gh-repos/` 下**静态阅读**。仓库为 `depth=1` 浅克隆，**无 git 历史、无 tag**，故"远端 tag/Release 真实状态"类问题无法核实，一律进第 5 节。行号均为实际读到的位置；外部事实均给官方链接，不做无源断言。

---

## 0. 一页结论（最该做的 3 件事）

**一句话**：三个项目**发布内容的质量很高**（发行说明印 SHA256、点名包文件、写清升级会不会丢数据），但**发布动作本身是"一台机器 + 一个人 + 一张手工清单"**。内容越好，越说明短板不在写文档，而在**过程没自动化、产物没身份、升级没通道**。

| # | 事项 | 为什么排第一 | 优先级 |
|---|---|---|---|
| 1 | **把发版搬到 tag 触发的 windows runner 流水线** | 三仓库 `.github/workflows/` 下**只有 `ci.yml`、零发布流水线**，"发布"100% 依赖本机 Windows + 开发者 `git credential fill` 凭据。换机器/凭据过期/漏跑一步都会停摆或发错内容 | **P0** |
| 2 | **给 exe 注入版本资源（FileVersion/ProductVersion）+ 走通签名** | 两个 exe 的 spec 既无 `version=` 也无签名，产物**没有机器可读的身份**。这决定了 SmartScreen 拦截、"报 bug 说不清装了哪版"、以及未来自动更新的可行性 | **P0** |
| 3 | **版本号单点化**（TideWatch 两处硬编码；Etude 的 README/QUICKSTART 无守卫；WingMan 已做到 90%） | WingMan 用 6 条测试把"版本号漂移"钉死了，是三者中唯一做到的；"改了忘改"正是最典型的发错版本根因 | **P1** |

> **给主理人的话**：这三条的目标是把发布水准从"**人肉保证**"变成"**流水线保证**"，不是补短板。

---

## 1. 现状矩阵（三项目 × 发布维度）

| 发布维度 | WingMan | Etude | TideWatch |
|---|---|---|---|
| 形态 | Windows 桌面（onedir+pywebview） | Windows 桌面（onedir+pywebview） | CLI/引擎（Python 包 + Docker） |
| 打包配置 | ✅ `build/wingman.spec` | ✅ `build/etude.spec` | ✅ `pyproject.toml` + `Dockerfile` |
| 打包脚本 | ✅ `scripts/build_exe.py` | ✅ `scripts/build_exe.py`（更强：归档核对+冻结态冒烟+体积基线） | — |
| 发版脚本 | ✅ `scripts/make_release.py`（本地手工） | ✅ `scripts/make_release.py`（本地手工，**含产物版本自证**） | ❌ 无 |
| **CI 构建 Windows 产物** | ❌ | ❌（CI 注释明说不做） | — |
| **tag → Release 流水线** | ❌ | ❌ | ❌ |
| **代码签名** | ❌ `codesign_identity=None` | ❌ `codesign_identity=None` | — |
| **exe 版本资源注入** | ❌ 无 `version=` | ❌ 无 `version=` | — |
| **产物版本自证** | ❌ 无 | ✅ `assert_dist_version()` | — |
| 自动更新 | ⚠️ 仅"检查更新"（提示，不下载） | ❌ 无 | — |
| 安装包/卸载项 | ❌ 绿色 zip | ❌ 绿色 zip | ❌（pip 包） |
| 代码内版本来源 | ✅ 单点 `backend/app/__init__.py:41` | ✅ 单点 `backend/app/__init__.py:31` | ⚠️ **两处**：`pyproject.toml:7` + `src/tidewatch/__init__.py:34` |
| 一致性强校验 | ✅ 6 条（`test_version.py`） | ⚠️ 2 条（`test_guards.py`，仅后端↔前端） | ❌ 无（且**无 CHANGELOG**） |
| CHANGELOG | ✅ 7 节，Keep a Changelog + SemVer + Unreleased | ✅ 4 节，同源格式 | ❌ **无** |
| 发行说明留档 | ✅ `docs/releases/` 7 份 | ✅ 3 份 | ❌ 无 |
| 校验和进发行说明 | ✅ | ✅ | — |
| 产物入库 | ✅ 干净 | ✅ 干净（例外见 P2-3） | ✅ 干净 |
| Docker 镜像 | — | — | ⚠️ 单 stage（注释自称 multi-stage）、editable 安装 |
| 卸载残留注册表 | ✅ 已验证无 `winreg`/自启/schtasks/shortcut | ✅ 同 | — |

> **读法**：**"内容是绿的，过程是红的"** —— 凡是"写给人看"的都做得好；凡是"要机器替人保证"的都缺。

---

## 2. 逐条发现（P0 → P2）

### P0-1【P0 · 2–3 人日】发布 100% 单机手工，三项目都没有 tag 触发的发布流水线

**【证据】** ① 三仓库 `.github/workflows/` 下**只有 `ci.yml`**（逐目录 `find` 确认），无任何 `release*.yml`。② 凭据来自开发者本机：`WingMan/scripts/make_release.py:24-25`、`Etude/scripts/make_release.py:13` 均自述 `git credential fill`、不落盘（实现见 WingMan `:115-130`）。③ Etude CI 主动声明不打包：`Etude/.github/workflows/ci.yml:48-50`——"打包本身不在 CI 里做"。④ WingMan 发布是 12 步手工清单：`WingMan/docs/DESKTOP.md:252-288`，含"从公开地址下载核对 SHA256""确认 CI 在 tag 指向提交上是绿的"。

**【问题】** ① **单点故障**：换机器/重装/token 过期 → 发布能力归零。② **不可复现**：CI 只在 ubuntu 跑测试（`WingMan/.github/workflows/ci.yml:16`），**要发给用户的包从未在 CI 构建过一次**。③ **清单越长越易漏**：`DESKTOP.md:284-285` 的"先 commit/push，**再**建 tag"就是顺序陷阱，顺序反了 tag 指向不含版本提升的提交，而这一步无任何机器检查。

**【改法】** 新增 `.github/workflows/release.yml`（**PyInstaller 不能交叉编译，Windows 产物必须在 `windows-latest` 构建**）：

```yaml
name: Release
on:
  push: { tags: ["v*"] }
  workflow_dispatch:
    inputs: { tag: { description: "如 v0.2.0", required: true } }
permissions: { contents: write }
jobs:
  win-artifact:
    runs-on: windows-latest          # ⚠️ 必须 Windows，不做交叉编译
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }     # 供 CHANGELOG 抽取/校验
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip,
                cache-dependency-path: backend/requirements-dev.txt }
      - run: pip install -r backend/requirements-dev.txt
      - run: python scripts/build_exe.py
      - run: python scripts/make_version_file.py        # 见 P0-3
      - name: 签名（见 P0-2，未配置时跳过）
        if: ${{ vars.SIGNING_ENABLED == 'true' }}
        uses: azure/trusted-signing-action@v0
        with:
          azure-tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          azure-client-id: ${{ secrets.AZURE_CLIENT_ID }}
          azure-client-secret: ${{ secrets.AZURE_CLIENT_SECRET }}
          endpoint: ${{ vars.AZURE_SIGNING_ENDPOINT }}
          trusted-signing-account-name: ${{ vars.AZURE_SIGNING_ACCOUNT }}
          certificate-profile-name: ${{ vars.AZURE_SIGNING_PROFILE }}
          files-folder: dist/WingMan
          files-folder-filter: exe,dll
          timestamp-rfc3161: http://timestamp.acs.microsoft.com
      - run: python scripts/make_release.py --check     # 只打包+打印 SHA256
      - name: CHANGELOG → Release notes
        shell: bash
        run: python scripts/extract_notes.py --version "${GITHUB_REF_NAME#v}" > release_notes.md
      - uses: softprops/action-gh-release@v2
        with:
          body_path: release_notes.md
          files: |
            release/*.zip
            release/*.sha256
```

配套 `scripts/extract_notes.py`（约 25 行，零依赖）：

```python
"""从 CHANGELOG 抽某版本段落作 Release notes（只认 Keep a Changelog 的 ## [<ver>] 标题）。"""
import argparse, re, pathlib

def extract(text: str, version: str) -> str:
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines)
                  if re.match(rf"^##\s*\[{re.escape(version)}\]", l)), None)
    if start is None:
        raise SystemExit(f"CHANGELOG 里没有 `## [{version}]` —— 提了版本却没记变更（先补 CHANGELOG）")
    end = next((j for j in range(start + 1, len(lines))
                if re.match(r"^##\s*\[", lines[j])), len(lines))
    return "\n".join(lines[start:end]).strip()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--version", required=True)
    a = ap.parse_args()
    print(extract(pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8"), a.version))
```

> **取舍**：`make_release.py` 现在既打包又上传（WingMan `:190-297`、Etude `:266-364`），**不要删** —— 本地 `--dry-run/--check` 仍有用。只把"上传"交给 Actions，让凭据从"本机"变成"仓库 Secrets"，并把发布记录与 CI 日志绑定。

**【优先级/工作量】** P0 / 2–3 人日（骨架 1 天；改造两个 `make_release.py` 复用 `--check` 语义 0.5 天；`extract_notes.py` + 联调 1 天）
**【验收】** ① 推 `v0.x.y` tag → GitHub 出现 Release，**附件由 CI 构建**（非本地上传）；② 附件 SHA256 与流水线日志一致；③ **故意删掉 CHANGELOG 对应章节再推 tag → 流水线必红**。

---

### P0-2【P0 · 0.5 人日（含申请等待）】两个 exe 都无代码签名，而文档里的成本估算已过时

**【证据】** ① `WingMan/build/wingman.spec:141`、`Etude/build/etude.spec:157` —— 均为 `codesign_identity=None`。② WingMan 已在文档承认后果：`WingMan/docs/DESKTOP.md:129-135`——"未签名的 exe 首次运行会弹『Windows 已保护你的电脑』…消掉的唯一正规办法是买代码签名证书（**一年几百到上千元**）"，对策是"让用户点『更多信息』→『仍要运行』"。

**【问题】** ① 微软官方文档确认：未签名文件下载运行会弹「Windows protected your PC」，用户须主动选 "Run anyway"；且**未签名文件每发一个新版本都要从零累积信誉**（旧版信誉不转移）→ 签名是"**每版都付一次**"的成本。见 [SmartScreen reputation](https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation)。② **成本结论过时**：同一份官方文档推荐的 **Artifact Signing（原 Trusted Signing）起价 $9.99/月、无需硬件 token、可直接接入 CI/CD**，比"年付证书"更便宜且能进流水线。③ 签名还是 P0-1 的**前置**：发布搬进 CI 后签名也必须在 CI 做，GitHub 侧有官方 action [`azure/trusted-signing-action`](https://github.com/Azure/trusted-signing-action)（要求 Windows runner）。

**【改法】** 签名是**后置步骤**（spec 里的 `codesign_identity` 是 macOS 用的，别指望它）：`build_exe.py` 出包 → action 逐个签 `*.exe`/`*.dll` → 再打 zip。一次性配置：Azure 建 Artifact Signing 账号 + Public Trust 证书配置 → App Registration → **GitHub OIDC 联邦凭据**（无需长期 client secret）→ 授 "Trusted Signing Certificate Profile Signer" 角色。仓库侧把 tenant/client/endpoint/account/profile 配成 **Variables**（非密钥，可明文）。YAML 见 P0-1。
**降级方案（0 元，今天可做）**：把"首次运行会弹 SmartScreen，点『更多信息→仍要运行』"写进**给用户的** `使用说明.txt` 首屏 —— 现在只有开发者文档里有，而该文件由 `WingMan/scripts/make_release.py:51-82`、`Etude/scripts/make_release.py:47-80` 生成，**里面没有这一段**。

**【优先级/工作量】** P0 / Azure 侧 0.5 天（身份验证审核有数天等待，常被低估）+ 仓库侧 0.5 天
**【验收】** ① `Get-AuthenticodeSignature .\WingMan.exe` 输出 `Status: Valid`；② 属性 → 数字签名 标签页有签名实体；③ 首屏不再"未知发布者"或至少显示**已验证的发布者名**（官方说签名后仍可能弹窗直到信誉累积，以实测为准，见第 5 节）；④ `使用说明.txt` 首屏含 SmartScreen 说明（无论如何都要做）。

---

### P0-3【P0 · 0.5 人日】可执行文件没有版本资源 —— 产物对 Windows 没有"身份"

**【证据】** ① 两个 spec 的 `EXE(...)` **都没有版本资源参数**：`WingMan/build/wingman.spec:127-145`（参数为 `pyz,a.scripts,[],exclude_binaries,name,debug,bootloader_ignore_signals,strip,upx,console,disable_windowed_traceback,argv_emulation,target_arch,codesign_identity,entitlements_file,icon`，**无 `version=`**）、`Etude/build/etude.spec:141-159`（同）。② 全仓 `grep "version_file|VSVersionInfo|FileVersion|ProductVersion|CompanyName"` 在 **spec/脚本里零命中**（唯一命中是 `WingMan/backend/app/collect/winapi.py:171-213`，那是**读别人**的 exe 版本）。③ 无 `*.vsi`/`*.rc`/`*file_version*` 文件。

**【问题】** ① 属性 → 详细信息里"文件版本/产品版本"为空；任务管理器、进程清单、任何排查工具都无法从 exe 读出"这是 0.2.0 还是 0.1.5"。② **这正是你自己写下的痛点**：`WingMan/backend/tests/test_version.py:1-12` ——"用户报 bug 时说不清自己装的是哪个包"。现在只有"程序自己会说版本"（自检/日志/界面），缺"**文件本身携带版本**"这一半。③ 未来任何更新器都需要读产物版本；没有 `FileVersion` 只能靠文件名猜。④ **讽刺点**：`winapi.py:171-176` 用 `GetFileVersionInfoW` 读**别的程序**的版本并论证"比跑 exe --version 更可靠"——而自己的 exe 恰好没这个字段。

**【改法】** 官方文档确认 CLI `--version-file FILE`、`pyi-grab_version`/`pyi-set_version`，版本资源含 `filevers`/`prodvers` 四元组且须 UTF-8。见 [PyInstaller · Using PyInstaller](https://pyinstaller.org/en/stable/usage.html)。

新增 `scripts/make_version_file.py`（在 `build_exe.py` 调 PyInstaller **之前**跑；版本值取自唯一的 `__version__`，不新增第二个真源）：

```python
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
VER = re.search(r'__version__\s*=\s*"([^"]+)"',
                (ROOT / "backend/app/__init__.py").read_text(encoding="utf-8")).group(1)
MAJOR, MINOR, PATCH = (list(map(int, VER.split("."))) + [0, 0, 0])[:3]
TEMPLATE = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({MAJOR}, {MINOR}, {PATCH}, 0), prodvers=({MAJOR}, {MINOR}, {PATCH}, 0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('080404b0', [          # 0x0804=简中, 1200=Unicode
      StringStruct('CompanyName', 'whyao56'),
      StringStruct('FileDescription', 'WingMan 聊天僚机'),
      StringStruct('FileVersion', '{VER}'),
      StringStruct('InternalName', 'WingMan'),
      StringStruct('OriginalFilename', 'WingMan.exe'),
      StringStruct('ProductName', 'WingMan'),
      StringStruct('ProductVersion', '{VER}'),
      StringStruct('LegalCopyright', 'MIT License')])]),
    VarFileInfo([VarStruct('Translation', [2052, 1200])])])
"""
out = ROOT / "build" / "_version_info.txt"
out.write_text(TEMPLATE, encoding="utf-8")     # 必须 UTF-8
print(f"version resource -> {out} ({VER})")
```

spec 接上（两处各加 3 行）：
```python
_VERSION_INFO = PROJECT_ROOT / "build" / "_version_info.txt"
exe = EXE(..., version=str(_VERSION_INFO) if _VERSION_INFO.exists() else None, ...)
```
`build_exe.py` 里加闸门（比"忘了生成"可靠）：
```python
subprocess.run([sys.executable, str(ROOT / "scripts" / "make_version_file.py")], check=True)
if not (ROOT / "build" / "_version_info.txt").exists():
    log("版本资源没生成，拒绝出包 —— 否则发出去的 exe 没有文件版本"); return 1
```
`build/_version_info.txt` 是生成物，加入 `.gitignore`（与 `WingMan/.gitignore:64-65` 的 `build/_pyinstaller/` 同处）。

> **待确认**：spec 的 `EXE()` 参数名（本报告写 `version=`）**未在 PyInstaller 官方页面上直接列出**（该页只确认 CLI `--version-file`）。落地前以本机 PyInstaller 的 `EXE` 签名为准，或用 `pyi-makespec --version-file` 生成一份对照。

**【优先级/工作量】** P0 / 0.5 人日
**【验收】** ① 右键 exe → 详细信息：文件版本 = 产品版本 = `backend/app/__init__.py` 里的值；② 把 `__version__` 改成与版本资源文件不一致时**构建必须失败**；③ `git status` 里不出现 `build/_version_info.txt`。

---

### P1-1【P1 · 0.5 人日】WingMan 缺 Etude 已有的"产物版本自证"闸门，而它的 `dist/` 策略恰好容易发错包

**【证据】** ① Etude 有这道闸门，且注释写明怎么踩出来的：`Etude/scripts/make_release.py:145-157`——"`dist/` 下留着上次构建的目录时 `newest_output()` 会老实挑它…于是 0.0.3 的 zip 里装的是 0.0.2 的前端 —— **打包、算校验和、上传全部成功，只有内容是错的**"。判据取自冻结产物的前端常量（`:158-182`）。② WingMan **无**对应逻辑：`WingMan/scripts/make_release.py` 全文只在 `:97-112` 从源码读版本号、`:203-204` 用它拼 tag，**没有任何"产物版本 vs tag"比对**。③ WingMan 的 `dist/` 是**固定路径 + 改名归档**：`WingMan/scripts/build_exe.py:71-81`（已存在则归档为 `.prev-HHMMSS`，`stamp=time.strftime("%H%M%S")` 同一分钟会撞名，`except OSError` 时直接 `rmtree`）；`make_release.py:220-231` 只认死路径 `dist/WingMan`，不校验版本。

**【问题】** `dist/WingMan` 是固定路径且会留下历史产物。只要"构建了 0.1.5 → 改了版本号但没重建或构建失败 → 直接跑 make_release"，就会**打出一个 tag 是 v0.2.0、内容却是 0.1.5 的包**，全流程绿灯。Etude 正是踩过才写了闸门；而 WingMan **恰好具备现成判据**：`WingMan/frontend/index.html:1272` 有 `const BUILD = "0.2.0";`，且 `backend/tests/test_version.py:107-124` 已保证它 == `__version__`。**闸门所需的一切都是现成的。**

**【改法】** 把 Etude 的 `assert_dist_version` 移植进 `WingMan/scripts/make_release.py`，并在 `main()` 里、`pack_one(...)` 之前调用：

```python
def assert_dist_version(dist: str, tag_version: str) -> None:
    """确认要打进去的产物真的是这个版号（照抄 Etude 的踩坑结论）。"""
    marker = next((c for c in (os.path.join(dist, "_internal", "frontend", "index.html"),
                               os.path.join(dist, "frontend", "index.html"))
                   if os.path.isfile(c)), None)
    if marker is None:
        raise SystemExit(f"{dist} 里找不到 frontend/index.html，没法确认产物版本。先跑 build_exe.py。")
    m = re.search(r'^const BUILD\s*=\s*"([^"]+)"', open(marker, encoding="utf-8").read(), re.M)
    if not m:
        raise SystemExit(f"{marker} 里找不到 const BUILD。")
    if m.group(1) != tag_version:
        raise SystemExit(f"产物里的前端是 {m.group(1)}，而你要发的是 {tag_version}。\n"
                         f"  产物目录：{dist}\n先重跑 scripts/build_exe.py，再打包。")
```

> 搬到 CI 后这个问题会**自动消失**（runner 干净，`dist/` 天然一份），**但不能因此不修** —— 本地 `--dry-run` 路径仍在，代价又太高。**先修本地闸门（1 小时），再上流水线。**

**【优先级/工作量】** P1（在 CI 落地前实际风险 = P0）/ 0.5 人日
**【验收】** ① 构造"版本 0.2.1 / 产物 0.2.0"场景，`make_release.py --check --version 0.2.1` **报错退出**；② 正常场景 SHA256 与从前一致。

---

### P1-2【P1 · 1 人日】Etude 的打包目录**无法带版本号**，用"最新 mtime"当"要发的那个"——这是 P1-1 事故的根因

**【证据】** ① `Etude/scripts/products.py:25-31`——"PyInstaller 的 COLLECT 名字写死在 `build/etude.spec` 里（`name="Etude"`），传 `.spec` 时 `--name` 会被忽略。所以**目录名没法加版本号**，只能换父目录。**这是这个模块存在的直接原因。**"② 产物于是落在 `dist/Etude`、`dist/build2/Etude`…（`:53-65`），发版靠 **mtime 找"最新"**（`:68-84`，`exe.stat().st_mtime` 取 `max`）。③ `Etude/build/etude.spec:146` 确实写死 `name="Etude"`。

**【问题】** ① "最新构建"≠"我要发的那个版本"是**两个命题**，代码把它们合成了一个。`products.py:68-84` 的注释只证明了"mtime 比目录名可靠"，**没证明"mtime 最新 == 版本正确"**。② 产物目录不带版本号 → 人工核对变难（拿到 `dist/build7/Etude` 无法从路径判断版本）。

**【改法】** 让 spec 的 `COLLECT` 名可被环境变量覆盖（spec 就是 Python）：

```python
# build/etude.spec —— 顶部
import os
LEAF = os.environ.get("ETUDE_LEAF", "Etude")     # 例如 Etude-0.0.3
...
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, upx_exclude=[],
               name=LEAF)                        # ← 原 name="Etude"
```
```python
# scripts/products.py —— next_output() 改用版本号做叶名
def next_output() -> tuple[Path, Path, str]:
    leaf = f"{LEAF}-{lib_version()}"             # lib_version() 读 app/__init__.py
    out_dir = DIST / leaf
    if out_dir.exists():
        raise SystemExit(f"{out_dir} 已存在 —— 版本号没升，或上一版还没发完。")
    return DIST, out_dir, ""
```
**额外收获**：重复构建同版本会**直接报错**（而非静默生成 `build2`），把"忘了升版本号"变成一次构建失败；`newest_output()` 可废弃，`assert_dist_version()` 降级为"最后一道保险"。

**【优先级/工作量】** P1 / 1 人日（`products.py`/`build_exe.py`/`make_release.py` 三处联动 + `e2e_check.py` 路径核对）
**【验收】** ① 产出 `dist/Etude-0.0.3/Etude.exe`；② 不升版本号再跑一次 → **失败**并提示版本号未升；③ `make_release.py` 不再调 `newest_output()`；④ CI（`Etude/.github/workflows/ci.yml:51-77`）仍绿。

---

### P1-3【P1 · 0.5 人日】Etude 所有 Release 都被标成 prerelease，`/releases/latest` 没有"最新正式版"可指

**【证据】** ① `Etude/scripts/make_release.py:340-346` —— 建 Release 时 `"prerelease": ver.startswith("0.0.")`；当前版本 `0.0.3`（`Etude/backend/app/__init__.py:31`），历史 `v0.0.1~v0.0.3`（`Etude/docs/releases/`）**全部匹配** → **三个 Release 全是 prerelease**。② 对照 WingMan 固定 `False`：`WingMan/scripts/make_release.py:257-264`。

**【问题】** ① GitHub REST 文档对 `/releases/latest` 的定义是"The latest release is the most recent **non-prerelease, non-draft** release"，见 [GitHub REST · Releases](https://docs.github.com/en/rest/releases/releases)；**只有 prerelease 时该端点无对象可返回**（响应码列表含 `404`）。② 后果一：用户看仓库侧栏 Releases 默认看到的是 Pre-release 分组。③ 后果二：**未来一旦照 WingMan 的 `WingMan/backend/app/api/routes_admin.py:190`（`RELEASES_API=".../releases/latest"`）给 Etude 加检查更新，会长期 404/空**，甚至把"查不到"误报成"已是最新"——WingMan 在 `routes_admin.py:224-231` 特意规避过这个坑，说明它是真的。④ 语义也站不住：`CHANGELOG.md:6-9` 自述"0.0.x 阶段允许破坏性变更"，这是"**不保证兼容**"，不是"**未完成的预发布**"。

**【改法】** 方案 A（推荐，1 行）：`prerelease` 只反映"是否预发布"，与 0.0.x 无关。`Etude/scripts/make_release.py:345` 改为 `"prerelease": args.prerelease`，并加 `parser.add_argument("--prerelease", action="store_true")`。方案 B（不推荐）：保留现行为 + README 加一句"本仓库版本均为 Pre-release，属正常"。
**附带**：`Etude/README.md:156` 与 `docs/QUICKSTART.md:20` 指向的是 Releases **列表页**（非 `/releases/latest`），所以**现在没坏**；这条是为未来扫清障碍。

**【优先级/工作量】** P1 / 0.5 人日（含在网页上把已有 3 个 Release 取消 prerelease 标记）
**【验收】** ① `https://api.github.com/repos/whyao56/Etude/releases/latest` 返回 **200**，`tag_name` 为最新版本；② 仓库页 Releases 区块直接显示版本号。

---

### P1-4【P1 · 1 人日】版本号不是单点：TideWatch 两处硬编码；Etude 的 README/QUICKSTART 版本无守卫

**【证据】**

**(a) TideWatch：同一版本号写在两个文件，互不联动**
| 位置 | 值 |
|---|---|
| `TideWatch/pyproject.toml:7` | `version = "0.1.0"` |
| `TideWatch/src/tidewatch/__init__.py:34` | `__version__ = "0.1.0"` |

`pyproject.toml:5-7` 用的是**静态 `version =`**（非 `dynamic = ["version"]`）→ 两份值之间**无任何机制保证相等**。且 `tidewatch` CLI **没有 `--version` 开关**：`TideWatch/src/tidewatch/cli.py:51-91` 的 `add_argument` 列表里没有 version → 用户**无法从命令行问出版本**。当版本同时出现在**打包元数据**和**运行时模块**里，后果是 `pip show` 说 0.1.0、程序自认 0.1.1。

**(b) WingMan：已经做对（应作模板）** —— 单一真源 `WingMan/backend/app/__init__.py:41`，6 条守卫 `WingMan/backend/tests/test_version.py`：

| 行号 | 守卫 |
|---|---|
| `:35-38` | 版本号必须 `x.y.z` |
| `:41-55` | CHANGELOG 必须有对应章节**且有日期**（区分 Unreleased） |
| `:58-66` | README 的 `**当前版本：vX.Y.Z**`（`README.md:191`）必须一致 |
| `:69-91` | `docs/releases/v<ver>.md` 必须存在、**点名包文件名**、含 `SHA256` |
| `:94-104` | README/QUICKSTART **不得有过期下载链接**（`releases/download/vX.Y.Z/`） |
| `:107-124` | 前端 `const BUILD`（`frontend/index.html:1272`）== 后端 `__version__` |

**(c) Etude：只守了"后端↔前端"一段** —— `Etude/backend/tests/test_guards.py:32-57` 只断言前端 `APP_VERSION`（`Etude/backend/frontend/index.html:702`）== 后端 `__version__`（含一条"改了必须红的反证测试"）。**未覆盖**：`Etude/README.md:11`（`当前版本：**0.0.3**`）、`Etude/docs/QUICKSTART.md:20` 与 `README.md:156`（下载链接里的 `Etude-0.0.3-win64.zip`）、`Etude/docs/releases/v0.0.3.md:11`（下载表格文件名/体积）。

**【问题】** 三个项目里 **WingMan 已用测试解决**，Etude 解决一半，TideWatch 没解决 —— 典型的"**跨项目可复用资产没被复用**"。具体损失：Etude 下一版需人工改 **5 处**，仅 1 处有测试盯着；**漏改下载链接的代价是静默 404**（`WingMan/backend/tests/test_version.py:96-98` 原话："指向一个不存在的 tag 的链接不会报错，只会 404 —— 静默失效"）。

**【改法】** **TideWatch 用 dynamic version 把两处合一**（改 `pyproject.toml`，不动 `__init__.py`）：
```toml
[project]
name = "tidewatch"
dynamic = ["version"]              # ← 原 version = "0.1.0"
[tool.setuptools.dynamic]
version = { attr = "tidewatch.__version__" }
```
再补 CLI 开关（让"装了哪一版"可问）：
```python
# src/tidewatch/cli.py —— build_parser() 内
from importlib.metadata import version as _v, PackageNotFoundError
try:
    _VER = _v("tidewatch")
except PackageNotFoundError:                       # 源码直跑、未安装
    from tidewatch import __version__ as _VER
parser.add_argument("--version", action="version", version=f"tidewatch {_VER}")
```
**Etude 照抄 WingMan 的三条守卫**（放进已有的 `Etude/backend/tests/test_guards.py`）：
```python
def test_readme_advertises_current_version():
    """README 的「当前版本」要和代码一致（照抄 WingMan/test_version.py:58-66）。"""
    from app import __version__
    text = (REPO / "README.md").read_text(encoding="utf-8")
    m = re.search(r"当前版本：\*\*([0-9.]+)\*\*", text)
    assert m, "README 里找不到「当前版本：**X.Y.Z**」这一行"
    assert m.group(1) == __version__, f"README 写的是 {m.group(1)}，代码里是 {__version__}"

@pytest.mark.parametrize("rel", ["README.md", "docs/QUICKSTART.md"])
def test_no_stale_download_links(rel):
    """下载链接不能停在旧版本 —— 它不报错，只会静默 404。"""
    from app import __version__
    text = (REPO / rel).read_text(encoding="utf-8")
    stale = {v for v in re.findall(r"Etude-([0-9.]+)-win64\.zip", text) if v != __version__}
    assert not stale, f"{rel} 里有过期下载链接：{sorted(stale)}（当前 {__version__}）"

def test_release_notes_exist_for_current_version():
    """发行说明要留档 + 点名包文件 + 印校验和（照抄 WingMan/test_version.py:69-91）。"""
    from app import __version__
    p = REPO / "docs" / "releases" / f"v{__version__}.md"
    assert p.is_file(), f"缺少发行说明 {p}"
    body = p.read_text(encoding="utf-8")
    assert f"Etude-{__version__}" in body, "发行说明没点名包文件，用户不知道下哪个"
    assert "SHA256" in body or "sha256" in body, "发行说明没有校验和"
```
**WingMan 补一处**：QUICKSTART 正文的示例版本串无守卫（见 P2-4）。

**【优先级/工作量】** P1 / 1 人日（TideWatch 0.5、Etude 0.5；WingMan 无需改）
**【验收】** ① `pyproject.toml` 不再出现字面量版本号，`python -m tidewatch.cli --version` 有输出；② 把 Etude `__version__` 改成 `0.0.4`（不改 README）→ `pytest` **必红**且指明过期文件；③ 版本号出现位置清单中除真源外**每一处都有测试覆盖**。

---

### P1-5【P1 · 0.5 人日】WingMan 重排了已发布版本的编号，与"发布不可变"冲突；发版脚本又拒绝覆盖同名 Release

**【证据】** ① `WingMan/CHANGELOG.md:77-84`——"**版本编号统一**：原先按 0.2.0 … 0.5.0 递增的那几个发行版，现统一归入 0.1.x（`v0.1.0`~`v0.1.5`）；**本次这个版本就是 0.2.0**"；"**0.1.x 不再提供二进制**"。② 对照表见 `WingMan/docs/DEVLOG.md:7-9` 与 `:16-22`（"0.1.0↔0.2.0 / … / **0.2.0↔0.6.0**"），新旧编号完全错位。③ 发版脚本**刻意拒绝覆盖**：`WingMan/scripts/make_release.py:249-254`——"本脚本刻意不覆盖已发布的 Release（避免误删别人的下载记录）。要重发请先到网页上删掉，或换一个 tag。" ④ README 已同步：`WingMan/README.md:141-142`。

**【问题】** ① **SemVer 的隐含契约是"发布不可变"**：重排让 `v0.2.0` **先后指向两个不同产品**（旧 0.2.0 = 打包成桌面程序；新 0.2.0 = 关窗死锁与内存瘦身）。对缓存、镜像、别人文章里的截图/链接，这个编号已失去指代能力。② **脚本与变更互相冲突**：`:249-254` 的"拒绝覆盖"设计**本身是对的**，但配合重编号就变成：新 `v0.2.0` 若与旧 `v0.2.0` 撞名会**直接拒绝创建**（返回 1），而 `DESKTOP.md:286-287` 的手工流程里**没有"先删旧 tag/Release"这一步**。③ **影响面控制得不错**（须说清）：`0.1.x` 从未提供二进制（`CHANGELOG.md:84-85`），受影响的主要是**标签身份与说明文档**，不是"用户下到的包变了"→ 故 P1 而非 P0。④ **教训可复用**：正确做法是**不改历史编号、改前端展示**；编号错了可以写文档，**不能回收**。

**【改法】** ① **不回滚**（已发生，回滚会造出第三套编号），但把规则**写进文档并机器化**：在 `DESKTOP.md:266-288` 清单里补"若同名 Release 已存在 → 先处理它"，并把它写进 `make_release.py:249-254` 的报错信息（现在只说了"到网页上删掉或换 tag"，没说清重编号场景下这几乎必然发生）。② 加一条机器检查：建 Release 前除查同名 tag（`:248-249`）外，再查"历史 tag 是否已有同版本号"：
```python
st, rels = call("GET", f"{API}/repos/{repo}/releases?per_page=100", tok)
published = {r["tag_name"] for r in (rels if isinstance(rels, list) else [])}
if tag in published:
    print("!! 该 tag 已存在 —— 若这是重编号场景，请先在网页删除旧 Release 后再发（见 CHANGELOG 的『版本重编号』一节）")
```
③ 把"**版本号一旦发布不回收**"写进 `WingMan/CHANGELOG.md:1-4` 的格式声明段（追加一条，作制度性记录）。

**【优先级/工作量】** P1 / 0.5 人日
**【验收】** ① `make_release.py` 在目标 tag 已存在时的报错里明确写出"重编号场景需先删旧 Release"；② `CHANGELOG.md` 顶部含"版本号不回收"一条；③ （可选最稳）CI 加"tag 名必须等于 `v{__version__}`"检查，防止 `--tag` 手工传值绕过。

---

### P1-6【P1 · 1 人日】TideWatch 没有 CHANGELOG、没有发行说明，且"生成锁定集"的机制没有任何地方消费

**【证据】** ① **无 CHANGELOG**：`git ls-files | grep -iE "changelog|history|release|news"` 在 TideWatch **零命中**（对照 WingMan 51KB、Etude 24KB）。② **无发行说明目录**：WingMan/Etude 有 `docs/releases/v*.md`，TideWatch 的 `docs/` 只有 `architecture.md`/`benchmark.md`/`design-decisions.md`。③ **`make freeze` 无人消费**：`TideWatch/Makefile:73-75` 的 `freeze:` 写 `pip freeze > requirements-lock.txt`，但仓库跟踪的是手写的 `requirements.txt`（`TideWatch/requirements.txt:1-8`，内容为 `PyYAML>=6.0` + 注释），**没有 `requirements-lock.txt`**；CI 也完全不碰它 —— `TideWatch/.github/workflows/ci.yml:43`（`pip install -e ".[zh,dev]"`）、`:48`、`:61` 全是**无约束最新版**安装。④ `TideWatch/pyproject.toml:7` 的 `version="0.1.0"` 是唯一"这是一版"的痕迹。

**【问题】** ① TideWatch 是三者中**工程实践最强**的（第一轮全项 A），却在"发布可追溯性"上最弱：**没有任何地方能回答"0.1.0 相比上一版改了什么"**；对引擎类项目这条尤其重要（使用者关心"信号集变了没/评分口径变了没/指标掉了没"），而这恰恰是 `docs/benchmark.md` 已在精确记录的东西 —— **有数据、缺叙事**。② `make freeze` 是**好习惯但没闭环**：生成了却不提交、不消费，比"没有冻结点子"更危险（给人"我们已可复现"的错觉）。③ CI 每次装最新版 jieba/pytest/ruff → 上游发版导致 CI 变红时，无法区分"是我改坏了"还是"依赖变了"。

**【改法】** ① 补 `CHANGELOG.md`，结构对齐 WingMan（`## [Unreleased]` + `## [0.1.0] - <日期>`，内含"新增/已知限制"，已知限制直接引用 `README` 的 7 条）。② 锁文件闭环（三处小改）：
```yaml
# .github/workflows/ci.yml —— test job 安装步骤
- name: 安装（锁定集优先，缺失时回退）
  run: |
    if [ -f requirements-lock.txt ]; then
      pip install -r requirements-lock.txt && pip install -e . --no-deps
    else
      pip install -e ".[zh,dev]"
    fi
```
```makefile
# Makefile —— freeze 后提示提交
freeze:
	$(VENV_BIN)/python -m pip freeze > requirements-lock.txt
	@echo "已写入 requirements-lock.txt —— 记得一并提交（CI 会用它）"
```
③ 机器校验"版本号 ↔ CHANGELOG"：把 `WingMan/backend/tests/test_version.py:41-55` 抄成 `TideWatch/tests/test_version.py`，断言 `CHANGELOG.md` 里存在 `## [<__version__>]` 且带日期。
> **与第一轮的关系**：第一轮 §4.4 把"`make freeze` 生成锁定集**并被 CI 消费**"列为可反向移植的实践。本轮实测**更正：生成有、消费无**。见 6.3。

**【优先级/工作量】** P1 / 1 人日（CHANGELOG 0.5、锁文件闭环 0.25、测试 0.25）
**【验收】** ① 有 `CHANGELOG.md`（含 `## [0.1.0] - <日期>` 与 `## [Unreleased]`）；② `requirements-lock.txt` 已提交且 CI 日志显示**被优先消费**；③ 改版本号不更新 CHANGELOG → 测试**必红**。

---

### P1-7【P1 · 0.5 人日】可安装性核对：干净机器上哪些步骤会失败

**【证据】** 逐条静态核对 README/QUICKSTART 的命令：

| 项目 | 路径 | 干净机器是否成立 | 证据/失败点 |
|---|---|---|---|
| WingMan | A. 绿色 exe | ✅ 基本成立 | 无需 Python；WebView2 缺失退回浏览器（`backend/requirements-desktop.txt:9-11`、`build/wingman.spec:23`）。**唯一必踩**：SmartScreen（P0-2） |
| WingMan | B. `wingman.cmd` | ✅ 成立但有前置 | 需 PowerShell 5.1（`wingman.cmd:31-39` 保证存在）+ **Python 3.11+ 且在 PATH**（`README.md:60`、`docs/QUICKSTART.md:5`）。未勾选 "Add python.exe to PATH" 会失败，有 `TROUBLESHOOTING.md` 指引 |
| Etude | A. 绿色 exe | ✅ 基本成立 | 无 Python；WebView2 缺失退回浏览器（`backend/requirements.txt:24-28`）；exe **带控制台**（`build/etude.spec:151-153`，刻意保留作排错出口），`QUICKSTART.md:33-35` 已说明 |
| Etude | B. 源码 | ✅ 成立但有两处隐含依赖 | `requirements.txt` 含 `edge-tts>=6.1,<8.0`，注释明确"**必须联网才能合成**"（`:17-18`）；`pywebview` 带 `; sys_platform == "win32"`（`:30`） |
| TideWatch | `pip install -e ".[zh]"` | ⚠️ **只在 editable 下成立** | `README.md:66-72` 可用；但 `src/tidewatch/config.py:26` 的 `PROJECT_ROOT = Path(__file__).resolve().parents[2]` 只在"源码树内"才指向仓库根。**非 editable（wheel/pipx）安装后**，`DEFAULT_CONFIG_PATH`（`config.py:27`）、`configs/`、`rules/` 解析（`config.py:103`、`:153-155`）全指到 `site-packages` 之上 → 找不到 `configs/default.yaml` |
| TideWatch | `pipx install .` | ❌ **装出一个跑不起来的 CLI** | `pyproject.toml:29-30` 确有 `[project.scripts] tidewatch = "tidewatch.cli:main"`；但 pipx 装的是**非 editable** wheel → 一运行就撞上路径问题。**形式上有入口点、实质不可用**，比"没有入口点"更误导 |
| TideWatch | Docker | ✅ 成立 | `Dockerfile:12-39`；镜像内 `pip install -e .`（`:24`）是 editable → `parents[2]`=`/app` → `configs/`、`rules/` 找得到。**这是"能跑"的原因，不是巧合** |
| TideWatch | Python 版本 | ⚠️ 只在徽章 | `README.md:5` 徽章写 `3.10~3.13`，但"快速开始"正文（`:64-72`）**无一句文字前提**；真实约束在 `pyproject.toml:10` 的 `requires-python = ">=3.10"` |

**额外一条（三项目共有）**：**CI 从不验证"发布路径"**。WingMan/TideWatch 的 CI 只跑 `ubuntu-latest`（`WingMan/.github/workflows/ci.yml:16`；`TideWatch/.github/workflows/ci.yml:12/23/55`），**从不构建 exe**；TideWatch 更典型 —— 三次安装**全是 `-e`**（`:43/:48/:61`），`pip install .`（用户真会走的路径）从未被 CI 跑过。**这就是 `config.py:26` 这个 bug 能活到现在的原因。**
同一模式还有一个"真实网络路径"的版本：两仓库都写好了离线 `openai_stub.py` + `e2e_check.py`（存在性已核实），却都没接进 CI → 真实 LLM 客户端代码零覆盖（详见 R-10；分析归 ai-eng §A-12）。

**【问题】** ① TideWatch README 首屏给出的安装方式**必须 editable**，而 pipx/wheel 这些标准分发路径全部不可用，用户会得到"装成功但一跑就崩"，**且无任何文档预警**。② 三项目都缺"发布路径的 CI 覆盖"——"CI 绿 ≠ 用户能用"。

**【改法】** ① TideWatch 立刻补一条 job（预期**先红**，红了才有推动力）：
```yaml
  wheel-install:
    name: 非 editable 安装冒烟（用户真实路径）
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python -m pip install --upgrade build
      - run: python -m build --wheel
      - run: pip install dist/*.whl        # ★ 非 editable
      - run: tidewatch scan data/sample/sample.jsonl --limit 3   # 现在会失败
```
修复方向：按第一轮 §4.2 把资源改 `importlib.resources`（`configs/`、`rules/` 作为 package-data 打进 wheel，配 `[tool.setuptools.package-data]`），再让它变绿。② TideWatch README 补一句前提：
```markdown
> **前置**：Python 3.10+。安装方式**必须是 `pip install -e ".[zh]"`（在仓库目录内）** ——
> 本包目前尚未支持非 editable / wheel 安装（修复进度见 CI 的 `wheel-install` job）。
```
③ WingMan/Etude 的发布路径覆盖由 P0-1 的 `release.yml` 解决（它在 windows runner 上真的跑一次 `build_exe.py`）。

**【优先级/工作量】** P1 / 0.5 人日
**【验收】** ① `wheel-install` job 存在，修复前后分别为**红/绿**；② `pip install .` 后 `tidewatch scan data/sample/sample.jsonl` 能出结果；③ 修复前 README 明写"当前仅支持 editable"；④ WingMan/Etude `release.yml` 至少成功出包一次并挂到 Release。

---

### P1-8【P1 · 0.5 人日】TideWatch 的 Docker 镜像：注释自称 multi-stage 实为单 stage；镜像内用 editable 安装

**【证据】** ① **注释与实现不一致**：`Dockerfile:3` 写"刻意用 multi-stage 的最简形态"，但**全文只有一个 `FROM`**（`:12` 的 `FROM python:3.12-slim AS base`），**无第二个 stage、无 `COPY --from=`**。② **editable 安装进镜像**：`Dockerfile:24` —— `RUN python -m pip install --upgrade pip && python -m pip install -e .`；`:38` 的 `ENTRYPOINT ["tidewatch"]` 依赖它生成的 console script。③ **基础镜像未钉 digest**：`:12` 用浮动 tag `python:3.12-slim`。④ **`.dockerignore` 只排除 `data/raw` 与 `out`**（`.dockerignore:19-24`），未排除 `data/sample`、`data/eval`、`docs/`、`tests/`、`experiments/`。⑤ **镜像内不 COPY `data/`**（`Dockerfile:27-30` 只 COPY `configs`/`rules`/`scripts`/`eval`，`:34` 建空 `/app/data`）—— 这点做得对。⑥ **体积实测**：`data/` 172K、`experiments/` 24K、最大单文件 90KB → **当前不存在"镜像被大数据撑爆"的实际问题**。

**【问题】** ① **注释错了比没注释更糟**：读者会以为"体积小是因为多阶段裁剪掉了构建工具"，实际 `pip install -e .` 会把 build 依赖（`setuptools`/`wheel`）留在最终镜像里，**没有任何 stage 清掉它**。② **editable 进生产镜像**的代价：保留 `.egg-info`/`__editable__` 引导文件；运行时**强依赖 `/app/src` 目录树不能动**（镜像不自包含）；且与 P1-7 的路径问题**互为因果**。③ **浮动基础镜像** → 同一 Dockerfile 在不同时间构建出的镜像**内容不同**，与该项目其它部分（`pyproject.toml` 严格上下界、`make freeze`）的严谨程度不匹配。④ **`.dockerignore` 不全**：`docker build` 会把未被 ignore 的**整个构建上下文**传给 daemon（`experiments/`、`data/eval`、`tests/` 在内）。今天只有 200KB；一旦 `data/` 放了真实抓取数据，这条规则会**静默把数据传进上下文**（`data/raw` 被单独排除说明已意识到风险，只是规则没写全）。

**【改法】** ① 改真·多阶段（顺手解决 editable，并把 digest 钉死）。**⚠️ 必须先完成 P1-7 的 `importlib.resources` 改造，否则把镜像弄坏**：
```dockerfile
# ---- 构建阶段：只有这里装 build 工具 ----
FROM python:3.12-slim@sha256:<你的digest> AS build
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip build && python -m build --wheel

# ---- 运行阶段：只装 wheel，不带 build 工具与源码树 ----
FROM python:3.12-slim@sha256:<你的digest> AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY --from=build /app/dist/*.whl /tmp/
RUN python -m pip install /tmp/*.whl && rm -f /tmp/*.whl
COPY configs ./configs
COPY rules ./rules
RUN useradd --create-home --uid 10001 tidewatch \
 && mkdir -p /app/data /app/out && chown -R tidewatch:tidewatch /app
USER tidewatch
ENTRYPOINT ["tidewatch"]
CMD ["--help"]
```
（`docker pull python:3.12-slim && docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim` 一次性拿到 digest。）
② `.dockerignore` 补 `data/`、`experiments/`、`tests/`、`docs/`（**保留 `eval/`**，`:30` 要 COPY 它）。③ 加最小元数据：
```dockerfile
LABEL org.opencontainers.image.title="tidewatch" \
      org.opencontainers.image.source="https://github.com/whyao56/TideWatch" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.licenses="MIT"
HEALTHCHECK CMD tidewatch --help >/dev/null 2>&1 || exit 1
```

**【优先级/工作量】** P1（"注释与实现不一致"本身是 P2，**与 P1-7 绑定后整体升为 P1**）/ 0.5 人日（**依赖 P1-7 先完成**）
**【验收】** ① `docker build` 成功且 `docker image inspect` 有 Labels/版本；② `docker run --rm -v "$PWD/data:/app/data" tidewatch scan data/sample/sample.jsonl --limit 3` 出结果；③ 镜像内**不存在** `setuptools`/`/app/src`；④ `.dockerignore` 排除项补全；⑤ 注释不再声称 multi-stage。

---

### P2-1【P2 · 0.25 人日】构建产物命名规则在三个地方各不相同

**【证据】** `WingMan/scripts/build_exe.py:120-128`（`--zip` 产出 `WingMan-YYYYMMDD.zip`，名字里是**日期** `time.strftime("%Y%m%d")`）vs `WingMan/scripts/make_release.py:46-48`（`WingMan-{version}-win64.zip`，**版本号**）vs `Etude/scripts/make_release.py:201`（`Etude-{version}-win64.zip`，与后者一致 ✅，且 zip 内顶层目录也带版本 `:207-211`）。

**【问题】** ① `build_exe.py --zip` 产出的包名字里**没有版本号**，用户从群聊/网盘拿到 `WingMan-20261013.zip` 时**无法判断是哪一版**。② 它是 P1-1"标签对、内容错"的温床（两份同内容包混在同一人手里）。③ 与公开文档不一致：`WingMan/docs/releases/v0.2.0.md:127` 点名"唯一的包是 `WingMan-0.2.0-win64.zip`"。（本行是 `README` 侧同类，见 `WingMan/README.md:191`。）

**【改法】** `--zip` 输出名改为与发版一致（`{APP_NAME}-{version}-win64.zip`，版本号复用 `make_release.py:97-112` 的读法）；或**删掉 `--zip`**，把"打 zip"唯一化到 `make_release.py --check`（它已经是可复现打包）。
**【优先级/工作量】** P2 / 0.25 人日
**【验收】** `build_exe.py --zip` 产物名含版本号；`grep -rn 'strftime("%Y%m%d")' scripts/` 不再命中产物命名。

---

### P2-2【P2 · 0.25 人日】WingMan 的 exe 图标被静默丢弃

**【证据】** `WingMan/build/wingman.spec:143-144` 引用 `build/wingman.ico`，写法是 `icon=str(...) if (...).exists() else None`；而 `build/` 目录里**只有 `wingman.spec` 一个文件**，`git ls-files | grep -i ico` **零命中**，`.gitignore` 也**未忽略** `.ico`。全仓对 `.ico` 的引用只有这两行。`Etude/build/etude.spec:141-159` 则**完全没有 icon 参数**。

**【问题】** ① `if exists else None` 是"体贴的降级"，但这里**降级的不是功能，是产品的第一印象**：exe 用 PyInstaller 默认图标，任务栏/桌面/资源管理器里都是通用图标。② 更该修的是**静默**：既然 `.gitignore` 没忽略 `.ico`（说明预期它应在仓库里），"文件不在"就该**报警**而非静默 `None`。

**【改法】** ① 提交 `build/wingman.ico`（建议含 16/32/48/256 多尺寸，否则高 DPI 下被拉伸）。② 把静默降级改成显式报警（不打断构建）：
```python
# build/wingman.spec
_ICO = PROJECT_ROOT / "build" / "wingman.ico"
if not _ICO.exists():
    print("[warn] build/wingman.ico 不存在 —— 这个 exe 会用 PyInstaller 默认图标")
exe = EXE(..., icon=str(_ICO) if _ICO.exists() else None, ...)
```
③ Etude 同理补一个 icon。
**【优先级/工作量】** P2 / 0.25 人日（图标制作时间另计）
**【验收】** 重新构建后 exe 显示自定义图标；spec 里不再有静默 `else None`。

---

### P2-3【P2 · 0.25 人日】Etude 把构建产物 `size-baseline.json` 提交进仓库，每次构建都会弄脏工作区

**【证据】** ① `Etude/build/size-baseline.json` 内容 `{ "bytes": 53952949, "files": 144, "version": "0.0.3" }`，是**被跟踪的文件**，`.gitignore` 用 `!` 反选回来（`Etude/.gitignore:11-14`："但 build/ 下的这两个**要**提交…`build/size-baseline.json` 体积基线"）。② 它由 `build_exe.py` **每次构建重写**：`Etude/scripts/build_exe.py:204-207`（`json.dump(..., "version": version())`）。③ 同文件 `:199-203` 已处理过一个相关问题（Windows 换行导致 git 永远显示"已修改"，故用 `newline="\n"`）。④ `Etude/scripts/make_release.py:154-156` 特意声明**不用它当版本判据**——"不拿 `size-baseline.json` 当判据 —— 那个文件记的是『上次构建出过什么版本』"。

**【问题】** ① 即使解决换行，"`bytes`/`version` 每次构建都可能变"**注定**让该文件持续变脏，而 `WingMan/docs/DESKTOP.md:264` 的发布清单恰恰有"`git status` 里没有 `dist/`、`*.db`"——**"发布前工作区必须干净"与"构建必然弄脏一个受跟踪文件"冲突**。② 它带 `version` 字段（既有**被误用**的风险），又不承担正式职责（`make_release.py:154-156` 的注释正在防这个误解）——**一个会诱发误解的字段，最好删掉**。③ 它正是 P1-1 事故的"**近似答案**"：看起来能当版本判据，实际不能（是"上次构建"的快照，不是"本次待发产物"的版本）。

**【改法】** 三选一 —— A（推荐）：基线移出仓库改为构建产物（`.gitignore` 删掉 `!build/size-baseline.json` 那行取反，改写 `build/_size-baseline.json`；`check_size` 已对 `previous is None` 做了处理，见 `:185`，代价只是新机器首次构建不做对比）；B：保留跟踪但**去掉 `version` 字段**，只记"体积警戒线"；C（治标）：把"构建后提交体积基线"写进发布清单。
**【优先级/工作量】** P2 / 0.25 人日
**【验收】** 跑一次 `build_exe.py` 后 `git status --porcelain` 为空（或只剩预期内文件）。

---

### P2-4【P2 · 0.1 人日】WingMan QUICKSTART 的示例版本串停在 v0.1.5

**【证据】** `WingMan/docs/QUICKSTART.md:39`——"左下方显示类似 `v0.1.5 · 0 条消息`"；当前版本 0.2.0（`WingMan/backend/app/__init__.py:41`）。它是**示例文案、不是链接**，故不被 `test_version.py:94-104`（只扫 `releases/download/vX.Y.Z/`）抓到；也不在 `:58-66` 的范围内（那条只认 README 的 `**当前版本：vX.Y.Z**`）。
**【问题】** 影响很小。真正的问题不是这一行，而是"示例里出现版本号"没有约定：要么用 `vX.Y.Z` 占位，要么纳入守卫。注意同文件 `:45` 的"**v0.1.5 起**可以…"是**历史事实陈述、正确、不该改** —— 因此**不建议**加"QUICKSTART 不得出现非当前版本号"的守卫（会误伤历史陈述）。
**【改法】** 把 `:39` 的 `v0.1.5` 改成当前版本（或统一写 `v0.2.0`）。
**【优先级/工作量】** P2 / 0.1 人日
**【验收】** `grep -n "v0.1.5 · " WingMan/docs/QUICKSTART.md` 不再命中。

---

### P2-5【P2 · 0.5 人日（可选）】三项目都没有"卸载路径"，WingMan/Etude 无安装包

**【证据】** ① **无注册表写入（已验证）**：全仓 `grep -rniE "winreg|HKEY|Startup|autostart|开机自启|注册表"` 在 WingMan/Etude 的**代码**里零命中（命中项全是注释里讨论"Windows 注册表里的系统代理"，如 `WingMan/backend/app/llm/openai_compat.py:26`）；`schtasks`/`.lnk`/`CreateShortcut` 同样**零命中**。② WingMan 文档明确承诺：`WingMan/docs/DESKTOP.md:46-50`——"想彻底卸载：删掉这个文件夹 + 程序目录即可。**没有注册表、没有后台服务。**"③ 与给用户的说明一致：`WingMan/scripts/make_release.py:68-73`、`Etude/scripts/make_release.py:67-72`。

**【问题（以及为什么不是 P0/P1）】** 先说结论：**这不是缺陷，而是有意的、一致的取舍** —— 绿色免安装 + 数据在 `%LOCALAPPDATA%`，与"无注册表/无后台服务"的承诺自洽，**不该按"缺失"指责**。但有两个真实代价：① 无 Start Menu/桌面快捷方式（要从解压目录找 exe）；② "应用和功能"里无卸载项 → 不懂技术的用户根本想不到"删文件夹"。另外，"无注册表"这条**现在对，但没有任何东西保证将来还对**。

**【改法】** ① 加守卫（低成本，建议做）：像 WingMan 已有的隐私守卫那样，用测试禁止注册表/自启 API：
```python
# WingMan/backend/tests/test_no_registry.py
"""守住「没有注册表、没有后台服务」这条承诺（docs/DESKTOP.md:46-50）。"""
import pathlib, re
FORBIDDEN = re.compile(r"\b(winreg|win32api\.Reg|CreateService|schtasks|CreateShortcut)\b")

def test_no_registry_or_autostart():
    root = pathlib.Path(__file__).resolve().parents[1] / "app"
    hits = [f"{p.relative_to(root)}:{i}: {line.strip()}"
            for p in root.rglob("*.py")
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if FORBIDDEN.search(line)]
    assert not hits, "出现注册表/自启/服务写入 —— 与承诺冲突：\n" + "\n".join(hits)
```
② 可选：补一个 Inno Setup 安装包，一次解决"快捷方式 + 卸载项 + 版本资源 + 可选开机自启"。骨架（ISCC 官方站：https://jrsoftware.org/isinfo.php）：
```ini
; WingMan.iss
#define MyAppVersion GetEnv("WINGMAN_VERSION")
[Setup]
AppId={{7B3A1C2E-…}}            ; 生成一次后固定，换掉会导致重复安装
AppName=WingMan
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\WingMan
UninstallDisplayIcon={app}\WingMan.exe
OutputBaseFilename=WingMan-{#MyAppVersion}-setup
Compression=lzma2/max
ArchitecturesInstallIn64BitMode=x64compatible
[Files]
; 不要带 {app}\data —— 数据在 %LOCALAPPDATA%，不随安装目录走
Source: "dist\WingMan\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
[Icons]
Name: "{group}\WingMan";        Filename: "{app}\WingMan.exe"
Name: "{group}\卸载 WingMan";   Filename: "{uninstallexe}"
Name: "{autodesktop}\WingMan";  Filename: "{app}\WingMan.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked
[Run]
Filename: "{app}\WingMan.exe"; Description: "启动 WingMan"; Flags: nowait postinstall skipifsilent
```
> **关键取舍**：安装包**必须默认不删用户数据**（数据在 `%LOCALAPPDATA%\WingMan`，与安装目录分离 —— 该设计已在 `DESKTOP.md:1` 的目录树写清），故 `[UninstallDelete]` 里**不要**写用户数据目录。

**【优先级/工作量】** P2（守卫建议做；安装包可选）/ 守卫 0.2 人日；安装包 0.5 人日 + 首次联调
**【验收】** ① `test_no_registry.py` 通过；② （若做安装包）开始菜单/桌面有入口、"应用和功能"有卸载项，卸载后 `%LOCALAPPDATA%\WingMan` **仍在**。

---

### P2-6【P2 · 0.5 人日（级别 1）；1–2 人日（级别 2，可选）】WingMan 只有"检查更新"，没有"升级通道"；Etude 连检查都没有

**【证据】** ① WingMan **有**检查更新：`WingMan/backend/app/api/routes_admin.py:202-244`（`GET /update/check`），数据源 `:190`——`RELEASES_API = "https://api.github.com/repos/whyao56/WingMan/releases/latest"`；前端入口 `WingMan/frontend/index.html:1118`（按钮）、`:4540-4556`（渲染 `has_update` 与新版本说明）。设计克制有品：`:206-208`——"**只有你点按钮时才会联网**，平时不查"；`:224-231`——"查不到（断网、被墙、限流）不是错误…别把『查不到』说成『已是最新』"。② **但只到"提示"为止**：无下载、校验、替换、重启；用户仍要**手工**开页面→下载 zip→解压→记住别只拖 exe→**手动删旧目录**（`WingMan/scripts/make_release.py:51-82` 的"怎么用"正是这段）。③ Etude **完全没有**：`grep -rniE "检查更新|has_update|update.check|latest release"` 在 `Etude/backend`/`Etude/docs`/`Etude/README.md` **零命中**。

**【问题】** ① 检查更新是**半个功能**：它把问题从"不知道有新版"降级为"知道有新版但要自己装"；对"分发给不懂技术的朋友"这个目标，之后那 4 步手工操作才是真门槛。② **好消息**：升级**天然安全**，实现难度低 —— 数据在 `%LOCALAPPDATA%\WingMan`（`DESKTOP.md:1` 目录树：`data/wingman.db`/`logs/`/`.env`），与程序目录完全分离，文档反复强调"换个位置解压程序，数据不会丢"（`make_release.py:72-73`）→ **"整目录替换"是合法的升级实现**。③ **技术约束**：Windows 上**正在运行的 exe 不能被覆盖**，这是唯一必须处理的硬约束。

**【改法】** **级别 1（0.5 人日，性价比最高）**：把"提示"补成"**一键打开下载页 + 三步图文升级指引**"。后端已在 `:242` 返回 `page`、`:241` 返回 `notes`；前端 `:4556` 已在渲染"有新版本 v{latest}"，只需追加"打开下载页"按钮（`open(r.page)`）与"① 关掉本程序 ② 解压新包到新目录 ③ 删掉旧目录（数据在 AppData，不受影响）"。成本近零，收益是"知道有新版"→"知道怎么装"。
**级别 2（1–2 人日，可选）**：**版本化程序目录 + 指针文件**。布局 `%LOCALAPPDATA%\WingMan\app\<version>\` + `current.txt`；流程：下载 zip → 校验 SHA256（发行说明已有现成值，`WingMan/docs/releases/v0.2.0.md:152-161`）→ 解压到 `app\<新版本>\` → **原子写** `current.txt` → "下次启动生效"；**校验失败必须丢弃新目录、不切换**；旧版本目录在**下次启动时**（旧 exe 已不占用）清理。若要做"就地替换 exe"，用 Windows 通用做法：当前 exe 重命名 `.old` → 写入新文件 → 退出 → 下次启动清理 `.old`。
> **不要自己写"下载器 + 自解压 + 自我替换"全套逻辑** —— 那是最容易引入供应链风险之处（下载内容可执行）。**级别 2 的前置条件是 P0-2 的签名落地**，否则你在自动执行一个不可验证的产物。

**【优先级/工作量】** P2（级别 1 建议做；级别 2 可选且依赖 P0-2）/ 级别 1：0.5 人日；级别 2：1–2 人日
**【验收】** 级别 1：点"检查更新"→ 新版本号 + 可点下载页 + 三步说明；断网时显示"没查到 ≠ 已是最新"（现有行为）。级别 2：从 0.2.0 升到 0.2.1 后 `%LOCALAPPDATA%\WingMan\data\wingman.db` **未被改动**（比对 mtime/大小），旧版本目录被自动清理。

---

### P2-7【P2 · 正向记录，无需动作】构建产物卫生：三仓库都干净

**【核实方法与结果】** 用 `git ls-files`（只读）逐仓库核查是否有二进制/构建产物入库：

| 仓库 | `build/` 下被跟踪的文件 | exe/dll/zip/whl/msi | `git ls-files` 文件数 | `.git` 体积 |
|---|---|---|---|---|
| WingMan | 仅 `build/wingman.spec` | **0** | 118 | 2.2 MB |
| Etude | `build/etude.spec`、`build/size-baseline.json` | **0** | 79 | 3.1 MB |
| TideWatch | （无 `build/`） | **0** | 55 | 505 KB |

三个 `.gitignore` 都排得很干净：`WingMan/.gitignore:63-72`（`build/_pyinstaller/`、`build/_work/`、`dist/`、`*.exe`、`release/`，并**用注释说明为什么 `build/wingman.spec` 要提交**）、`Etude/.gitignore:2-14`（同样带解释）、`TideWatch/.gitignore`（含 `out`、`data/raw`）。`WingMan/scripts/make_release.py:7-11` 把这个决定讲得很清楚（"二进制产物不该进版本历史…GitHub 单文件硬限制 100MB…Release 附件就是官方为此设计的出口"）。

**【结论】** **不需要动作。** 本轮**没有**发现"二进制入库导致克隆体积膨胀"这类常见问题。唯一例外是 Etude 的 `size-baseline.json`（见 P2-3，仅 62 字节，问题不是体积而是"持续变脏"）。
**【优先级/工作量】** —（正向记录）/ 0
**【验收】** `git ls-files | grep -iE "\.(exe|dll|zip|whl|msi)$"` 在三仓库继续零命中。

---

## 3. 跨项目共性清单（R-1 … R-10）

> 按"一次学会、三处受益"重组。编号 R-x 为本轮新增（第一轮共性编号为 C-x，不冲突）。

| 编号 | 共性问题 | 涉及 | 关联发现 | 优先级 |
|---|---|---|---|---|
| **R-1** | **没有"发布路径"的 CI 覆盖**：测试在跑，但"用户拿到手之后的安装/打包路径"从未在干净环境跑过。WingMan 不构建 exe；TideWatch 只跑 `-e`；Etude 明确声明不在 CI 打包 | 三项目 | P0-1, P1-7 | **P0** |
| **R-2** | **产物没有机器可读的身份**：无版本资源（`version=`）、无签名 —— 两个 exe 一个都没有 | WingMan/Etude（TideWatch 缺 CLI `--version`） | P0-2, P0-3, P1-4 | **P0** |
| **R-3** | **"生成物/快照"被当成"真源"**：Etude 用 mtime 最新当"要发的那个"；`size-baseline.json` 带 `version` 却不是判据；TideWatch 的 `requirements-lock.txt` 生成了却不被消费 | Etude, TideWatch | P1-1, P1-2, P1-6, P2-3 | P1 |
| **R-4** | **版本号重复出现的每一处都须有守卫**：WingMan 已做到（6 条）；Etude 只做 1 处；TideWatch 两处硬编码且零守卫 | 三项目 | P1-4 | P1 |
| **R-5** | **发版是"人肉清单"而非"机器断言"**：WingMan 的 12 步清单最详尽，但依赖记性；Etude 把其中一条（产物版本）变成了断言 —— **这个模式应推广到全部清单项** | WingMan, Etude | P0-1, P1-1, P1-3 | P1 |
| **R-6** | **文档里的成本/行为结论会过期**：`DESKTOP.md:134` 说"买证书一年几百到上千元"，而官方推荐方案已降到 $9.99/月且可接 CI；`Dockerfile:3` 说"multi-stage"实际单 stage | WingMan, TideWatch | P0-2, P1-8 | P1 |
| **R-7** | **CLI/引擎型项目缺"发布叙事"**：TideWatch 有精确 benchmark 数据，却无 CHANGELOG、无版本化发行说明、无法从 CLI 问出版本 | TideWatch | P1-4, P1-6 | P1 |
| **R-8** | **缺"账号级"横向发布一致性检查**（版本徽章、README 首屏下载链接在多仓库间的统一） | 三项目 | P1-4, P0-1 | P2 |
| **R-9** | **给用户的说明书应覆盖安全提示**：`make_release.py` 生成的 `使用说明.txt` 没写 SmartScreen 那一句，而开发者文档里写了 | WingMan, Etude | P0-2 | P2 |
| **R-10** | **CI 只跑"简单路径"、跳过"真实路径"的**第三种**表现**：两仓库都写好了离线 `openai_stub.py` + `e2e_check.py`，却都没接进 CI —— 于是 CI 只跑 Mock 冒烟（模型输出永远干净），几百行真实网络代码（`OpenAICompatProvider` / `chat()`）的 `response_format` 降级、401/404 翻译、Bearer 校验**零覆盖**。与 R-1（TideWatch 只跑 `-e`、不跑 wheel）**是同一个失效模式**：CI 验证的是"最容易跑通的那条路"。 | WingMan, Etude | R-1, P1-7 | P1 |

> **R-1 / R-10 是同一根因，应合并成一次 CI 改造**：新增三类 job ——「发布路径」（windows runner 出包/装 wheel）、「真实网络路径」（起 stub 跑 e2e）、「离线降级路径」。三者的共同点是**零密钥、零外网、可在 PR 上跑**。
> **R-10 的证据与详细覆盖清单归 ai-eng（其报告 §A-12）**，本条只登记"同样的模式在发布链路上也成立"这一判断，不重复其分析。已核实：四个脚本均存在（`WingMan/scripts/openai_stub.py` 21KB、`WingMan/scripts/e2e_check.py` 14KB、`Etude/scripts/openai_stub.py` 18KB、`Etude/scripts/e2e_check.py` 11KB），而 `grep -rn "openai_stub\|e2e_check" */.github/` 的唯一命中是 **`Etude/.github/workflows/ci.yml:97` 的密钥扫描排除项**（写进去是为了**跳过扫描**，不是执行它）。

---

## 4. 落地路线（3 周 + 验收标准）

> 按 1 名开发者、每周 2–3 人日投入。每个动作可独立成 commit。

### 第 1 周 —— 让"发布"有机器保证（主角：P0）

| # | 动作 | 关联 | 验收标准 |
|---|---|---|---|
| **W1-1** | WingMan 移植 `assert_dist_version`（20 行，从 Etude 抄） | P1-1 | "版本 0.2.1 / 产物 0.2.0"场景下 `make_release.py --check` 报错退出 |
| **W1-2** | 两项目生成 + 注入版本资源（`make_version_file.py` + spec `version=` + `build_exe.py` 闸门） | P0-3 | 属性→详细信息：文件版本 = 产品版本 = `__version__` |
| **W1-3** | 新增 `release.yml`（tag 触发 / `windows-latest`）+ `extract_notes.py` | P0-1 | 推 tag → Release 出现、附件由 CI 构建、SHA256 与日志一致；CHANGELOG 缺章节时**必红** |
| **W1-4** | TideWatch 加 `wheel-install` CI job（预期先红）+ README 补"仅支持 editable" | P1-7 | job 稳定复现失败；README 有提示。**与 ai-eng 的 W2-3b（`llm-integration`）合并为同一次 CI 改造提出** —— 三类 job（发布路径 / 真实网络路径 / 离线降级路径）共享"零密钥、零外网、可上 PR"模板，比分三次省评审成本（见 R-10） |
| **W1-5** | `使用说明.txt` 补 SmartScreen 一段（0 元降级方案） | P0-2 | 重新打 zip 后首屏含"点『更多信息→仍要运行』" |

### 第 2 周 —— 版本治理与可安装性（主角：P1）

| # | 动作 | 关联 | 验收标准 |
|---|---|---|---|
| **W2-1** | TideWatch `dynamic=["version"]` + CLI `--version` | P1-4 | `pyproject.toml` 无字面量版本；`tidewatch --version` 有输出 |
| **W2-2** | Etude 补 3 条版本守卫（README/下载链接/发行说明） | P1-4 | 改 `__version__` 不改 README → pytest 必红且指明文件 |
| **W2-3** | TideWatch 补 `CHANGELOG.md` + 版本↔CHANGELOG 测试 + 锁文件闭环 | P1-6 | CI 显示锁文件被消费；改版本没写 CHANGELOG → 测试红 |
| **W2-4** | Etude `prerelease` 语义修正（1 行）+ 网页上取消已有 3 个 Release 的 prerelease | P1-3 | `/releases/latest` 返回 200 |
| **W2-5** | Etude 产物目录版本化（spec `ETUDE_LEAF` + `products.py`） | P1-2 | 产出 `dist/Etude-0.0.3/`；版本未升重复构建**失败** |
| **W2-6** | TideWatch `config.py` 资源改 `importlib.resources` | P1-7, P1-8 | `wheel-install` job 转绿 |

### 第 3 周 —— 分发体验与收尾（主角：P2 + 可选）

| # | 动作 | 关联 | 验收标准 |
|---|---|---|---|
| **W3-1** | TideWatch Dockerfile 改真·多阶段 + 钉 digest + LABEL + 补 `.dockerignore` | P1-8 | 镜像内无 `setuptools`/`/app/src`；`docker run` 能跑；注释与结构一致 |
| **W3-2** | WingMan 升级体验级别 1（检查更新 + 一键打开下载页 + 三步说明） | P2-6 | 点按钮 → 版本号 + 可点下载页 + 三步图文 |
| **W3-3** | WingMan/Etude 图标（提交 `.ico` + 去掉静默降级 + 报警） | P2-2 | exe 显示自定义图标 |
| **W3-4** | WingMan 产物命名统一 + `size-baseline.json` 移出跟踪 | P2-1, P2-3 | `--zip` 名含版本；构建后 `git status --porcelain` 为空 |
| **W3-5** | 可选：代码签名（Artifact Signing + `azure/trusted-signing-action`） | P0-2 | `Get-AuthenticodeSignature` 返回 `Valid` |
| **W3-6** | 可选：Inno Setup 安装包 + `test_no_registry.py` 守卫 | P2-5 | 卸载后 `%LOCALAPPDATA%\WingMan` 仍在；守卫测试通过 |
| **W3-7** | WingMan QUICKSTART 示例版本串更新 | P2-4 | `grep "v0.1.5 · "` 不再命中 |

### 做完之后，发布流程长这样

```
开发者：改代码 → 提 __version__ → 写 CHANGELOG 段 → 写 docs/releases/v<X>.md → commit + push
        ↓
       git tag -a vX.Y.Z && git push origin vX.Y.Z
        ↓
CI（windows-latest，标签触发）：
  build_exe.py ─► make_version_file.py ─► 重新出包（带版本资源）
        ├─► 签名（Artifact Signing）
        ├─► make_release.py --check（可复现 zip + SHA256）
        ├─► extract_notes.py（CHANGELOG → Release notes）
        └─► softprops/action-gh-release（建 Release + 挂 zip/sha256）
        ↓
用户：点「检查更新」→ 新版本号 + 下载页 + 三步升级说明（数据在 AppData，不会丢）
```

---

## 5. 待确认项

> 以下为本机浅克隆（depth=1、无 tag、未联网）**无法核实**的事项，**未做任何推测性断言**。

1. **远端 tag / Release 的真实状态** —— 无 git 历史与 tag，无法确认 WingMan 旧编号体系的 `v0.2.0~v0.6.0` 是否**仍存在**于远端。若仍在，会与 `make_release.py:249-254` 的"拒绝覆盖"**直接冲突**。请在网页 `Releases` 页逐条核对。**这是本轮唯一"可能有正在流血的问题"的待确认项。**
2. **Etude 的 3 个 Release 当前是否真的全部带 prerelease 标记** —— 由 `make_release.py:345` 与当前版本 `0.0.3` 推断为"是"，但**未联网核实远端实际标记**。请访问 `https://api.github.com/repos/whyao56/Etude/releases/latest` 验证（200 = 我的推断错，404 = 推断成立）。
3. **`EXE(version=...)` 的 spec 参数名** —— 官方页面只明确写了 CLI `--version-file`，spec 侧参数名未列出（见 P0-3 的标注）。落地前以本机 PyInstaller 的 `EXE` 签名为准。
4. **签名后的 SmartScreen 实际表现** —— 官方称"签名后仍可能弹窗直到信誉累积，但会显示已验证的发布者名"；另有第三方资料称 Artifact Signing 的 Public Trust 证书可直接获得信任。两者不一致，**以你签名后首次下载实测为准**。
5. **`WingMan/build/wingman.ico` 是否曾在别处存在** —— 本机 `build/` 下只有 `wingman.spec`，且 `.gitignore` 未忽略 `.ico`。无法判断图标是"丢了"还是"从未提交"。
6. **`Etude/build/size-baseline.json` 是否有其它取用方** —— 本机只看到 `build_exe.py` 写它、`make_release.py:154-156` 明确不用它。若有其它脚本依赖，P2-3 的"移出跟踪"需相应调整。
7. **TideWatch 的 `requirements-lock.txt` 是否在别处使用** —— 本机 `git ls-files` 无此文件、CI 不引用。若你的本地流程依赖它，P1-6 的改造需调整。
8. **两个项目是否已有配好的签名证书** —— 浅克隆看不到 Release 附件属性，无法确认你是否已在某个 Release 上签过名。
9. **发布流水线的 runner 配额** —— `windows-latest` 分钟数消耗显著高于 ubuntu。本账号为公开仓库，Actions 分钟数通常不计费（**以 GitHub 当前计费政策为准，本轮未联网核实**）。

---

## 6. 与第一轮报告的关系

> 第一轮：`.../deliverables/software-company/GitHub项目优化建议-全流程报告.md`（覆盖：代码架构 / 测试与CI / 开源呈现与隐私）；本轮：发布分发与版本治理。**本轮所有条目均为第一轮未覆盖的新条目。**

### 6.1 本轮明确**不重复**的第一轮条目

| 第一轮条目 | 位置 | 本轮处理 |
|---|---|---|
| 三个旗舰"有 Release" | §1 全景盘点 | 不评"有没有"，只评"**怎么产生的、能否复现、内容有没有身份**" |
| TideWatch `PROJECT_ROOT = parents[2]` 无法作为 wheel 安装 | §4.2 ③ | 从**发布工程角度**重新提出（P1-7/P1-8），新信息是"**CI 从不验证发布路径，所以这个 bug 才活着**"，并给出可先红的 CI job。**根因与第一轮相同，不复述。** |
| WingMan CI 只在 ubuntu | §5.2 ① | 不评"测试平台错配"（第一轮已述），只评"**发布产物从未在 CI 构建过**"（R-1/P0-1） |
| README 缺英文版/GIF/首屏过长 | §6.3 | 完全不涉及 |
| `Self-Mind` 转 Private、commit 邮箱 | §2.1/§2.3 | 完全不涉及 |
| 巨型文件拆分、SQLite 外键、覆盖率、pre-commit | §3/§4/§5 | 完全不涉及 |

### 6.2 相关但**不同角度**的条目

| 本轮条目 | 与第一轮 X 条的关系 |
|---|---|
| **P0-1 无发布流水线** | 与第一轮 §5.2 "WingMan CI 只在 ubuntu"**同源但不同问题**：第一轮问"测试跑在哪"，本轮问"**产物在哪构建、谁保证一致**"。即使按第一轮加了 windows job，**发布仍可不走 CI**（本轮的发现）。 |
| **P1-7 可安装性（TideWatch）** | 与第一轮 §4.2 ③"无法作为普通 wheel 安装"**同根因、不同切面**：第一轮从架构角度给根因与改法（`importlib.resources`）；本轮从**验证机制**角度指出"CI 从不跑非 editable 安装，所以承诺无从兑现"，并给出可立即落地的 CI job。**实施时应合并为一个 PR。** |
| **P1-4 版本号单点定义** | 与第一轮 §6.1"WingMan 展示信息过期（topics 仍含 whisper/asr）"**都是"信息一致性"问题**，但对象不同：第一轮管**对外描述与功能是否一致**，本轮管**版本号在多处出现是否一致**。第一轮未覆盖版本号维度。 |
| **P1-6 TideWatch 无 CHANGELOG** | 与第一轮 §6.1"旗舰 README 全中文、无英文入口"同属"对外呈现"，但第一轮评的是**语言可达性与首屏结构**，本轮评的是**版本化发布记录的有无**。 |
| **P2-5 无卸载路径** | 第一轮未触及。**注意本条结论是"设计自洽，无需大改"** —— 与第一轮"发现问题就要改"的基调不同。 |
| **P2-7 构建产物卫生（正向）** | 与第一轮 §8"你已有的优势"同属正向记录；第一轮列的 10 条优势**没有一条涉及 build/dist/.gitignore 的产物卫生** —— 本轮补上，结论是"三仓库全干净"。 |

### 6.3 本轮对第一轮的**修正**（2 处）

1. **第一轮 §4.4 第 2 条**把"`make freeze` 生成锁定集**并被 CI 消费**"列为 TideWatch 值得反向移植的实践。**本轮实测修正**：`TideWatch/Makefile:73-75` 确实生成 `requirements-lock.txt`，但（a）该文件**不在仓库**（`git ls-files` 零命中）、（b）CI 三次安装**全是 `-e` 无约束**（`ci.yml:43/48/61`）。**即"生成有、消费无"**，不具可移植性。见 P1-6。
2. **第一轮 §1 全景盘点**把"三个旗舰有 Release"记为一处正向。**本轮补充**：WingMan 实际 **7 个**（`docs/releases/v0.1.0~v0.2.0.md`）、Etude **3 个**（`v0.0.1~v0.0.3.md`）、TideWatch **0 个**（无任何发行说明）。即"三个旗舰都有 Release"**对 TideWatch 不成立** —— 它有 `docs/benchmark.md` 但无版本化发布记录。见 P1-6。

### 6.4 两份报告合并执行时的优先级建议

第一轮 P0 是"**正确性/成本 bug**"（SQLite 外键、图片线程池成本泄漏），本轮 P0 是"**分发可用性**"。建议顺序：

1. **第一轮 P0 的两条 bug**（0.5–1 天，影响正确性与成本，最贵）→ 立即做
2. **本轮 P0-3（版本资源）**（0.5 天，纯增量、零风险、立刻可见）→ 可与上面并行
3. **本轮 P0-1（发布流水线）**（2–3 天，含本轮 P1-1 的本地闸门）→ 紧接着做
4. **本轮 P0-2（签名）**（Azure 侧有审核等待，**建议在第 2 步之后立即启动申请**，因为到账有时间差）
5. 其余按 W2/W3 路线推进

---

## 附录 A：本轮只读核查命令（可复现）

```bash
# 有无发布流水线（预期只有 ci.yml）
find WingMan Etude TideWatch -path "*/.github/workflows/*" -type f
# 构建产物是否入库（预期零命中）
cd <repo> && git ls-files | grep -iE "\.(exe|dll|pyd|zip|whl|msi)$"
# 版本号出现位置
grep -rn "__version__" WingMan/backend Etude/backend TideWatch/src --include=*.py
grep -rn "APP_VERSION\|const BUILD" Etude/backend/frontend/index.html WingMan/frontend/index.html
# 有无版本资源注入（预期只有 winapi.py 读别人的版本）
grep -rn "version_file\|VSVersionInfo\|FileVersion\|ProductVersion" WingMan Etude --include=*.py --include=*.spec
# 有无注册表/自启（预期代码里零命中）
grep -rniE "winreg|HKEY|Startup|autostart|schtasks|CreateShortcut" WingMan/backend Etude/backend --include=*.py
# TideWatch 发布路径覆盖（预期全是 -e）
grep -n "pip install" TideWatch/.github/workflows/ci.yml
```

## 附录 B：外部资料（均为官方/项目方来源）

| 主题 | 链接 |
|---|---|
| SmartScreen 行为、签名影响、Artifact Signing(原 Trusted Signing) $9.99/月起 | https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation |
| GitHub REST · Get the latest release（"non-prerelease, non-draft"） | https://docs.github.com/en/rest/releases/releases |
| PyInstaller · `--version-file` / `pyi-grab_version` / `pyi-set_version` / 版本资源结构 | https://pyinstaller.org/en/stable/usage.html |
| PyInstaller · spec 文件（`EXE()` 等） | https://pyinstaller.org/en/stable/spec-files.html |
| Azure Trusted Signing Action for GitHub Actions（要求 Windows runner） | https://github.com/Azure/trusted-signing-action |
| Keep a Changelog 1.1.0（两个 CHANGELOG 已声明遵循） | https://keepachangelog.com/zh-CN/1.1.0/ |
| Semantic Versioning | https://semver.org/lang/zh-CN/ |
| Inno Setup（可选安装包方案） | https://jrsoftware.org/isinfo.php |

---

**方法与局限声明**：本报告基于 `gh-repos/` 下三个仓库的**本地浅克隆静态阅读**，**未安装依赖、未执行任何构建/打包、未运行被测程序、未联网访问远端 API**。因此以下结论**未经运行验证**：版本资源注入后的实际显示、签名后的 SmartScreen 表现、CI 流水线的可用分钟数与配额、远端 tag/Release 真实状态（已逐条列入第 5 节）。所有引用的行号均为实际读到的代码位置；所有外部事实均给出官方链接，未做无源断言。
