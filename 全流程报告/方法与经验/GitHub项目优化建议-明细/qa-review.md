# QA 工程师评审报告：WingMan / Etude / TideWatch 测试与工程化质量

> 评审人：Edward（QA 工程师 / software-qa-engineer）
> 评审方式：静态阅读本地克隆仓库（`gh-repos/` 下），未修改任何文件、未执行 `pip install`、未真跑测试套件；对测试充分性做了 AST 层面的空断言扫描。
> 结论基于真实读到的文件内容，引用文件名与行号。不确定项标注「待确认」。

---

## 0. 一句话结论

三个项目的测试**质量远超同类个人项目**：几乎不存在「只断言不抛异常」的假测试（AST 扫描 637 个 test 函数，仅 1 个没有直接断言，且那 1 个是调用带断言的 helper）。真正的短板不在「写得对不对」，而在**工程化的三个缺口**：① 没有任何覆盖率度量与门槛；② WingMan（一个 Windows 桌面产品）在 CI 里从来不在 Windows 上跑；③ WingMan 完全没有 lint 关卡、Etude 的 ruff 装了但没接进 CI。这三条是「测试写了但防不住退化」的根因。

| 项目 | 质量等级 | 一句话 |
|---|---|---|
| **TideWatch** | **A** | 工程化最完整：有 lint 关卡、4×Python 矩阵、jieba 装/不装双跑、Makefile/Dockerfile、评测不退化断言 |
| **Etude** | **A-** | 双 OS CI（ubuntu+windows）、干净环境冒烟、隐私红线 job、夹具/桩设计优秀；缺 lint 关卡与覆盖率 |
| **WingMan** | **B+** | 守卫式测试密度最高（隐私/版本/配置契约），但 CI 只跑 Linux，Windows 专有能力零真机覆盖，且无 lint、无覆盖率 |

---

## 1. 质量现状矩阵

> 统计口径：Python 生产代码 = 应用源码 + 仓库内 `scripts/*.py` + 入口脚本；不含测试、不含前端 HTML 内联 JS。测试行数 = `tests/` 下 `.py` 总行数（含 conftest）。数据来自 `wc -l` 实际计数。

| 维度 | WingMan | Etude | TideWatch |
|---|---|---|---|
| 测试文件数 | **21**（`backend/tests/*.py`，+0 conftest） | **14**（`backend/tests/*.py`，含 conftest） | **9**（`tests/*.py`，含 conftest） |
| 测试代码行数 | **8,493** | **4,716** | **2,393** |
| 生产代码行数（Python） | **18,476**（app 15,266 + scripts 3,174 + 入口 36） | **7,946**（app 5,947 + scripts 1,830 + 入口 169） | **4,092**（src 3,223 + scripts/eval 869） |
| 测试:生产 比 | **0.46 : 1** | **0.59 : 1** | **0.58 : 1** |
| 仅比 app（不含 scripts） | 0.56 : 1 | 0.79 : 1 | 0.74 : 1 |
| test 函数数（AST 实测） | **233** | **249** | **155** |
| 无断言的 test 函数 | **1**（`test_smoke`，调用的 helper 内含断言） | **0** | **0** |
| 是否有测试分层 | 有（守卫 / 单元 / 集成 TestClient；`scripts/e2e_check.py` 未接入 CI） | **有**（单元 / 集成 / 真 HTTP e2e / 干净装 | 有（单元 / 集成 pipeline / eval 端到端冒烟） |
| 是否有 conftest / 夹具 | **无 conftest**，每文件自带 `sys.path.insert` + `_skip` + `main()` | 有（`conftest.py` 233 行，夹具丰富） | 有（`conftest.py` 190 行，`dataset` 夹具精心构造） |
| 是否配置覆盖率 | **否** | **否** | **否** |
| 是否有覆盖率门槛 | **否** | **否** | **否** |
| CI 是否跑测试 | **是**（pytest + smoke） | **是**（pytest，双 OS） | **是**（pytest 4×py + jieba 双跑） |
| CI 是否跑 lint | **否**（只有 `compileall` 语法检查 + node `vm.Script` 前端语法） | **否**（ruff 在 requirements-dev 里，但 CI 不调用；仅跑 `check_js.py`） | **是**（独立 `lint` job：`ruff check src tests scripts eval`） |
| 是否有 pre-commit | **否** | **否** | **否** |
| CI 平台矩阵 | **仅 ubuntu**（py 3.11 / 3.13） | **ubuntu + windows**（py 3.11 / 3.12） | **仅 ubuntu**（py 3.10–3.13 × jieba） |
| 是否有缓存 | 是（`cache: pip`，按 `requirements.lock.txt`） | 是（`cache: pip`，按 `requirements-dev.txt`） | **否**（setup-python 未开 `cache: pip`） |
| 阻塞合并 | `pull_request` 触发，可作保护分支必需检查 | 同左 | 同左 |
| README 徽章 | License/Python/CI | License/Python（**无 CI 徽章**） | License/Python/Dependencies/**CI** |

**读法**：
- 三个项目的**测试:代码比都在 0.5–0.8 之间**，对个人项目而言属于健康水位；Etude 的单测密度最高（0.79）。
- **没有任何一个项目配置了覆盖率**（`grep -i coverage` 在三个仓库全零命中，无 `.coveragerc`、无 `[tool.coverage]`、依赖里无 `pytest-cov`）。这是三项目共同的、最系统性的工程化缺口（见 §5）。
- **pre-commit 三个仓库都没有**。WingMan 有强隐私守卫（`test_privacy_pseudonyms.py` 扫真实姓名 + 提交邮箱），但**没有本地提交前拦截**，只能靠 CI 事后兜底。
- **WingMan 的 CI 与产品形态错配**：WingMan 是 Windows 桌面产品（读进程内存、读剪贴板、PyInstaller 出包），但 CI 只在 `ubuntu-latest` 跑（`ci.yml:16`），而 `test_collect_offwindows.py:203/219` 的反向守卫被 `skipif(sys.platform != "win32")` 挂在 Windows 上——**这些守卫在有 CI 的所有平台上永远不会执行**。

---

## 2. 三个 `ci.yml` 逐项体检

### 2.1 WingMan（`.github/workflows/ci.yml`，81 行，单 job）

| 项 | 现状 | 行号 |
|---|---|---|
| 触发 | `push: main`、`pull_request: main`、`workflow_dispatch` | 3–8 |
| 权限 | `contents: read`（最小权限，好） | 10–11 |
| 矩阵 | **仅 `ubuntu-latest`**；`python-version: ["3.11","3.13"]`；`fail-fast: false` | 15–20 |
| 缓存 | `cache: pip` + `cache-dependency-path: backend/requirements.lock.txt` | 30–32 |
| 依赖安装 | 运行锁定集 + `requirements-dev.txt`（只装 pytest） | 34–39 |
| 语法检查 | `python -m compileall -q backend/app backend/tests scripts` | 41–42 |
| 单元测试 | `working-directory: backend` → `python -m pytest tests/ -q` | 46–48 |
| e2e 冒烟 | `python tests/test_smoke.py`（Mock Provider，无需 Key） | 50–52 |
| 编码防护 | 无编码变量 + 纯 ASCII 流两种环境跑 smoke，并断言无非 ASCII 字节 | 54–65 |
| 前端语法 | 内联脚本灌入 `node` 的 `vm.Script` 做语法校验 | 67–80 |

**缺失环节**：
1. **无 Windows job** —— 产品本体是 Windows 桌面程序，`app/collect/winapi.py`（389 行）、`clipboard.py`（528 行）、`app/desktop.py`（613 行）在 CI 里从未在真实 Win32 上执行过一次。
2. **无 lint** —— 连 `ruff` 都没进 `requirements-dev.txt`（该文件只有 `pytest>=8.0`），全项目无 ruff/flake8 配置。
3. **无覆盖率** —— 无 `--cov`、无门槛。
4. **无 `concurrency`**（同分支连续 push 会并排跑）、**无 `timeout-minutes`**（跑飞时占用 runner 上限）。
5. **`timeout` 风险**：`test_collect_budget.py` / `test_memory_footprint.py`（子进程探针 `timeout=180`）这类时间敏感用例在共享 runner 上偶发不稳。
6. 无 `concurrency: group`、无 release/packaging 验证（README 已自述打包走本地脚本，可接受）。

### 2.2 Etude（`.github/workflows/ci.yml`，111 行，3 个 job）

| 项 | 现状 | 行号 |
|---|---|---|
| 触发 | `push: main/master`、`pull_request`、`workflow_dispatch` | 3–7 |
| 权限 | `contents: read`（注释说明打包/发版刻意留在本地） | 9–12 |
| job: test | **os = [ubuntu, windows] × python = 3.11/3.12**；`fail-fast: false` | 14–40 |
| └ 缓存 | `cache: pip` + `requirements-dev.txt` | 30–31 |
| └ 前端守卫 | `python scripts/check_js.py` 单独一步（为在日志里可见） | 45–46 |
| job: clean-install | windows，仅装运行依赖（不装 dev），`run_etude.py --check` + 版本一致性 | 51–77 |
| job: secrets | ubuntu；`git ls-files` 拒绝 `config.json`/`*.sqlite3`；`git grep` 拒绝 `sk-` 前缀真实 Key；`innerHTML` 拼接警告 | 79–110 |

**缺失环节**：
1. **lint 未接 CI** —— `requirements-dev.txt:15` 明确写着「项目里没有强制 lint 关卡」，ruff 可达但从未执行 → 风格/未用导入会静默漂移。
2. **无覆盖率**。
3. **`scripts/ui_smoke.js`（1,023 行）从未在 CI 运行** —— 这是前端交互冒烟脚本，目前只能人工跑，属「写了但没接进流水线」。
4. 无 `concurrency` / `timeout-minutes`。
5. `clean-install` 只在 windows 跑；若未来支持 Linux/macOS 需补。

### 2.3 TideWatch（`.github/workflows/ci.yml`，113 行，3 个 job）——**三项目里最规范**

| 项 | 现状 | 行号 |
|---|---|---|
| 触发 | `push: main/master`、`pull_request`、`workflow_dispatch` | 3–7 |
| job: lint | **独立 job**：`ruff check src tests scripts eval` | 10–19 |
| job: test | ubuntu；**py 3.10/3.11/3.12/3.13**；`jieba: with`，另 `include: 3.12 + without` 验证降级路径 | 21–51 |
| └ jieba=without 自检 | 断言 `import jieba` 确实失败，否则「这条矩阵失去意义」 | 45–49 |
| job: smoke | 生成合成数据 → 跑 `eval/run_eval.py` → **断言 `docs/benchmark.md` 里 itemF1/actorF1>0、信号数≥8、团伙纯度>0** → CLI 冒烟 | 53–113 |

**缺失环节**：
1. **无覆盖率**（`pyproject.toml` 无 `[tool.coverage]`，`dev` 不含 `pytest-cov`）。
2. **无 Windows 矩阵** —— `Makefile:6-7` 明写「Windows 上建议在 Git Bash 或 WSL 里执行」，说明作者在意 Windows，但 CI 未覆盖。
3. **无缓存** —— `setup-python` 未开 `cache: pip`（另外两个项目都开了），每次全量装依赖，可直接补一行。
4. `experiments/` 被排除在 ruff 外（`pyproject.toml:41`），属合理取舍。
5. 无 `concurrency` / `timeout-minutes`。

### 2.4 改进后的完整 `ci.yml` 示例（选 WingMan —— 缺口最多）

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

# 同分支连续 push 时取消上一次，省 runner 也省等待
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: 静态检查 (ruff)
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements-dev.txt
      - run: python -m pip install --upgrade pip ruff
      - name: Ruff（后端 + 脚本）
        run: ruff check backend/app backend/tests scripts

  test:
    name: 测试 (${{ matrix.os }} / py${{ matrix.python-version }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]      # ← 关键补丁：Windows 真机
        python-version: ["3.11", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: backend/requirements.lock.txt
      - name: 安装依赖
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.lock.txt
          pip install -r backend/requirements-dev.txt
      - name: 语法检查
        run: python -m compileall -q backend/app backend/tests scripts
      - name: 单元测试 + 覆盖率
        working-directory: backend
        shell: bash
        run: |
          python -m pytest tests/ -q \
            --cov=app --cov-report=term-missing --cov-report=xml \
            --cov-fail-under=55
      - name: 上传覆盖率
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.os }}-${{ matrix.python-version }}
          path: backend/coverage.xml
      - name: 端到端冒烟（Mock Provider）
        working-directory: backend
        shell: bash
        run: python tests/test_smoke.py

  encoding-guard:
    name: 冒烟编码防护
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: pip
          cache-dependency-path: backend/requirements.lock.txt
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.lock.txt
          pip install -r backend/requirements-dev.txt
      - name: 无编码变量 + 纯 ASCII 流都不得崩溃
        working-directory: backend
        run: |
          env -u PYTHONIOENCODING -u PYTHONUTF8 LANG=C LC_ALL=C python tests/test_smoke.py > /tmp/s1.txt
          PYTHONIOENCODING=ascii PYTHONUTF8=0 python tests/test_smoke.py > /tmp/s2.txt
          python -c "import sys;d=open('/tmp/s2.txt','rb').read();bad=[b for b in d if b>127 or (b<32 and b not in (9,10,13))];sys.exit(1 if bad else 0)"
      - name: 前端 JS 语法
        run: node scripts/check_frontend.js   # 把原来内联的脚本落成仓库文件，便于本地复用
```

> 要点：**新增 `os: [ubuntu-latest, windows-latest]`** 让 `skipif(win32)` 的反向守卫真正执行；新增 `lint` job；新增 `--cov` 与 `--cov-fail-under`（阈值从宽松起步，见 §5）；补 `concurrency` / `timeout-minutes`；`node` 检查落成仓库脚本而非内联 heredoc（当前 `ci.yml:67-80` 内联写法本地无法复用）。

---

## 3. 测试质量诊断

### 3.1 假测试 / 弱断言扫描结果

用 `ast` 遍历三个 `tests/` 目录（637 个 `test_*` 函数），统计「函数体内既无 `assert`、也无 `pytest.raises`、也无 `fail()`」的用例：

```
WingMan   : 233 test funcs, 1 without assert/raises  → test_smoke.py:236（调用 run_pipeline()，其内含大量断言）
Etude     : 249 test funcs, 0 without assert/raises
TideWatch : 155 test funcs, 0 without assert/raises
```

**结论：不存在「只断言不抛异常」的空测试。** 这与很多个人项目「一堆 `assert resp.status_code == 200` 敷衍」的常态截然相反。逐文件抽检（WingMan `test_privacy_pseudonyms.py`、`test_config_contract.py`、`test_collect_offwindows.py`；Etude `test_guards.py`、`test_core.py`、`test_e2e_stub.py`；TideWatch `test_eval.py`、`test_signals.py`、`test_pipeline.py`）均为**带「为什么」注释的针对性用例**，甚至包含「守卫的守卫」（反证测试）。

真正值得警惕的不是「假测试」，而是下面几类**看似通过、实则打折**的写法，需要点名：

| # | 反模式 | 位置（文件:行） | 说明 | 严重度 |
|---|---|---|---|---|
| A | **缺依赖即静默 skip** | WingMan `test_collect_api.py:49-52`、`test_collect_budget.py:49-52`、`test_collect_cipher.py:54`、`test_collect_clipboard.py:53`、`test_collect_reader.py:56`、`test_collect_semi.py:50`、`test_http_keepalive.py:59`、`test_loopback_proxy.py:48`、`test_objects_center.py:47`、`test_objects_s0.py:43`、`test_persons.py:47`、`test_preflight.py:47` | `_skip()` 在缺 `fastapi`/依赖时 `pytest.skip`。CI 里依赖齐全故无碍，但**本地/评审若少装一个包，整片用例变「跳过」，输出仍是绿的**，掩盖真实失败。 | 中 |
| B | **导入即通过式断言** | WingMan `test_collect_offwindows.py:131` `assert module is not None`、`:145` `assert routes.router is not None` | 只证明「import 没炸」，不证明任何行为。作者有意为之（该文件的职责就是 import 守卫），但它是**最容易被后人复制成假测试**的模板。 | 低 |
| C | **浅断言混在强断言里** | TideWatch `test_adapters.py:164/192/299` `assert ...created_at is not None` | 单看很弱；不过同文件其余断言（字段值、数量）足够强，属可接受。 | 低 |
| D | **`pytest.skip` 吞掉安全守卫** | WingMan `test_privacy_pseudonyms.py:117-120` | 浅克隆时「跳过而不是通过」——**作者注释里明确承认**「搜不到 ≠ 搜过且干净」。CI 默认 `fetch-depth: 1` 浅克隆，导致**隐私历史扫描在 CI 上恒为 skip**（形同废守卫）。 | 中 |
| E | **桩过宽会掩盖缺陷（已被作者自我警示）** | Etude `conftest.py:62-146`（`stub_llm`） | 桩同时认得「例句」和「大纲」两种请求，注释自述「什么都能做的桩会把问题盖住」。作者已用专门的残缺结构用例补偿，属**良性疾病**。 | 低 |

> 说明：上表 A/B/D 三处**不是作者疏忽**，而是「可移植性优先」的自觉取舍；但站在「防退化」角度，仍有可加固的空间（见 §3.3 的隔离建议与 §5）。

### 3.2 关键路径覆盖缺口（按生产代码最大的模块点名）

**WingMan**（最大文件优先）

| 模块 | 行数 | 测试现状 | 缺口 |
|---|---|---|---|
| `backend/app/store.py` | **1,940** | 无 `test_store.py`；仅被 `test_persons/test_objects_*/test_smoke` **间接**覆盖（`grep -rw store` 命中 9 处，但都是构造 Store 后用别的接口） | **P0**：facts 唯一键（`store.py:57-70` 明确记录过「喜欢猫被静默覆盖」的历史 bug）、老库回填/迁移、索引语义，均无**直接**回归锚点 |
| `scripts/preflight.py` | **1,679** | `test_preflight.py`（627 行）间接覆盖 | P1：脚本主流程的端到端路径 |
| `backend/app/collect/reader.py` | **1,169** | `test_collect_reader.py`（12 用例） | P1：解析分支多，用例数偏少 |
| `backend/app/collect/semi.py` | 688 | `test_collect_semi.py`（22 用例，734 行） | 覆盖尚可 |
| `backend/app/llm/mock.py` | 664 | 被 6 个文件用（作为 Provider） | 覆盖尚可，但缺「mock 输出契约」单测 |
| `backend/app/desktop.py` | 613 | **仅 2 处引用** | P1/P2：桌面壳（关闭协商/单实例）在 CI 无 Windows，无法真测 |
| `backend/app/api/routes_data.py` | 434 | **0 处直接引用** | P1：数据页 API 无专属契约测试（FastAPI 注解错→500 类 bug 无守卫） |
| `backend/app/api/routes_persons.py` | 350 | 间接（`test_persons.py` 走 TestClient） | P1 |
| `backend/app/engine/prompts.py` | 499 | **0 处直接引用** | P1：提示词拼装是「分析质量」的上游，无契约测试 |
| `backend/app/selfcheck.py` | 275 | 1 处弱引用 | P1 |
| `backend/app/llm/openai_compat.py` / `ollama.py` | 186 / 126 | 1–2 处弱引用 | P1：无「真实 HTTP 链路」测试（对比 Etude 有 `openai_stub` e2e） |
| `backend/app/engine/analyzer.py` / `planner.py` | 67 / 70 | **0 处直接引用** | P2 |

**Etude**（最大文件优先）

| 模块 | 行数 | 测试现状 | 缺口 |
|---|---|---|---|
| `backend/app/db.py` | **1,204** | 被 `test_api/test_storage_pipeline/test_anki_controls/test_data_location` 间接覆盖 | P1：缺 SQL/迁移的直接单测；`test_upgrade.py` 覆盖升级路径 |
| `backend/app/api.py` | **870** | `test_api.py`（26）+`test_edit_api.py`（27） | 覆盖较好 |
| `backend/app/providers/images.py` | 806 | `test_images.py`（18）+`test_image_parallel.py`（18） | 覆盖较好 |
| `backend/app/providers/llm.py` | 433 | `test_e2e_stub.py`（真 HTTP stub） | 覆盖好 |
| `backend/app/prompts.py` | 433 | **无 `test_prompts.py`** | **P0**：`build_messages/classify_target/language_profile`（`prompts.py:117/396/196`）零直测；「不支持语言必须抛 NotImplementedError」（`prompts.py:133-136`）是可测的硬契约 |
| `backend/app/pipeline.py` | 636 | `test_storage_pipeline.py`（24）+e2e | 覆盖较好 |
| `backend/app/selfcheck.py` | 403 | 部分（`test_upgrade`） | P2 |
| `backend/app/server.py` / `desktop.py` | 124 / 70 | 无 | P2 |

**TideWatch**（覆盖最完整）

| 模块 | 行数 | 测试现状 | 缺口 |
|---|---|---|---|
| `src/tidewatch/text.py` | 302 | `test_text_matching.py`（20） | 覆盖好 |
| `src/tidewatch/signals/coordination.py` | 330 | `test_signals.py`（17） | 覆盖好 |
| `src/tidewatch/matching.py`（AC 自动机） | 157 | `test_text_matching.py` | 覆盖好 |
| `src/tidewatch/config.py` / `rules.py` | 163 / 199 | 经 conftest 夹具使用 | 覆盖可 |
| `scripts/gen_sample.py` / `fetch_bilibili.py` | 296 / 215 | 无 | P2（合成数据生成器，`eval` 依赖它） |
| `src/tidewatch/io.py` | 70 | 经 `test_adapters` | 覆盖好 |

> **共性结论**：三项目**最该补的是「最大、最核心、却只被间接覆盖」的模块**——WingMan `store.py`（1,940 行数据层）与 Etude `prompts.py`（433 行提示词层）是各自最大的「无直测核心模块」。

### 3.3 环境依赖与可移植性

| 依赖类型 | 位置 | 风险 | 隔离建议 |
|---|---|---|---|
| **Win32 专有 API** | WingMan `collect/winapi.py`、`clipboard.py`、`desktop.py` | 在 Linux CI 上走替身/降级，真机行为零 CI 覆盖 | 加 Windows job；新增 `test_collect_windows_real.py`（`skipif(win32)` 反向），让 `clipboard` 读写往返、`list_processes` 在真机执行 |
| **模拟 Linux 的守卫** | `test_collect_offwindows.py:72-120`（打补丁 `builtins.__import__` 假造 Linux） | 已用「反向守卫」自证补丁有效（`:219-229`）；设计优秀，但只在 Windows 上跑才完整 | 依赖 Windows job |
| **真实 HTTP 服务** | Etude `test_e2e_stub.py:26-54`（后台线程起 uvicorn `openai_stub`） | 端口/线程启动有极小抖动风险，但用了 `_free_port()` + 20s 等待，可控 | 保持；建议加 `@pytest.mark.e2e` 便于分组 |
| **真实大模型/图库 API** | Etude `conftest.py:184-207`（`stub_image` 注释点明 Openverse 真联网） | **已被桩隔离**，属正确处理 | 保持 |
| **外部网络** | WingMan `test_loopback_proxy.py`、`test_http_keepalive.py` | 走 loopback，非公网 | 保持 |
| **时间敏感** | WingMan `test_collect_budget.py`（预算）、`test_memory_footprint.py:103`（`timeout=180`） | 共享 runner 上偶发不稳 | 标记 `@pytest.mark.slow`，允许重跑；内存探针在非 Windows 已 `return`（`:140-141`） |
| **git 元数据依赖** | WingMan `test_privacy_pseudonyms.py` | 浅克隆下恒 skip（见 §3.1-D） | CI 该 job 用 `fetch-depth: 0`，或接受其为「仅本地/发版前」守卫并显式标注 |

### 3.4 测试数据 / 夹具管理

- **TideWatch 最佳**：`tests/conftest.py:105-190` 的 `dataset` 夹具是「教科书级」——刻意加入**平缓正常活动作为背景速率**，并在注释里解释「没有背景，协同层就该弃权；夹具里没有背景，测的其实是弃权而不是检出，那是假测试」。`rng` 固定种子（`:42-43`）保证可复现。
- **Etude 优秀**：`conftest.py` 的 `isolated_data`（autouse，把数据目录指向 `tmp_path` + 每例关连接，注释记录「单跑绿、一起跑红」的历史教训）、`sync_pool`（把线程池换同步以去掉 sleep 依赖）都是高质量做法。
- **WingMan 偏弱**：**无 conftest**，每文件复制 `_tmp_dir()`、`_fresh_store()`、`_client_with_temp_data_dir()`、`_skip()`、`main()` 样板（如 `test_persons.py:41-78` 与 `test_objects_center.py:41-90` 高度重复）；临时目录用 `tempfile.mkdtemp` + `finally: shutil.rmtree` 手写清理由，而 pytest 的 `tmp_path` 内建清理更稳。**建议下沉到 `conftest.py`**。

---

## 4. 要补的测试清单（按优先级）

> 优先级定义：**P0** = 核心链路/历史 bug 无回归锚点，或产品形态在 CI 零覆盖；**P1** = 重要模块缺直接测试；**P2** = 增强项。目标模块均为真实文件路径。

| # | 目标模块（真实路径） | 测试场景 | 为什么重要 | 优先级 |
|---|---|---|---|---|
| 1 | `WingMan/backend/app/store.py` | `upsert_fact` 同一 key 不同 value **不得互相覆盖**（`UNIQUE(chat_id,subject,key,value)`） | `store.py:45-56` 明确记录过「喜欢猫被静默覆盖」的历史 bug，目前无直接回归 | **P0** |
| 2 | `WingMan/backend/app/store.py` | 老库回填/迁移：旧 schema → `init()` 后 person 归属完整（不丢数据） | 结构改造最怕「静默丢数据」，用户看到人物列表空会以为数据没了 | **P0** |
| 3 | `Etude/backend/app/prompts.py` | `build_messages` 契约：系统提示含「scene not translation」、用户消息含目标词与 examples 数；`language_profile("ja")["supported"] is False`；不支持语言抛 `NotImplementedError`（`prompts.py:133-136`） | 提示词是「学习效果」的上游；`prompts.py` 零直测 | **P0** |
| 4 | `WingMan/backend/app/collect/clipboard.py` | **真实 Win32**：`write_text(x)` → `sequence_number()` 递增 → `read_text()==x` 往返 | 产品核心采集能力在 CI 从未真机执行 | **P0** |
| 5 | `WingMan/backend/app/collect/winapi.py` | **真实 Win32**：`list_processes()` 非空且含 `pid/name`；`process_path(os.getpid())` 可读 | 同上；当前仅 Linux 替身路径被测 | **P0** |
| 6 | `WingMan/backend/app/api/routes_data.py` | TestClient 打数据页各端点，断言 200 + 响应体类型与注解一致（防 FastAPI 注解错→500） | 434 行无专属契约测试；同类 bug 在 `routes_collect` 已有先例（`test_collect_api.py:107`） | P1 |
| 7 | `WingMan/backend/app/engine/prompts.py` | 拼装分析/建议提示词，断言必含剧情要点、雷区、输出 JSON 约束 | 提示词是整个引擎的输入，零直测 | P1 |
| 8 | `WingMan/backend/app/llm/openai_compat.py` + `ollama.py` | 用本地 stub 服务跑真 HTTP：`response_format` 不支持时降级重试、401→auth 提示 | 对比 Etude 有 `openai_stub` e2e，WingMan 缺这层 | P1 |
| 9 | `WingMan/backend/app/selfcheck.py` | 自检在缺 Key/无网络下返回结构化「下一步」，不抛未捕获异常 | 用户排障入口 | P1 |
| 10 | `WingMan/backend/app/memory/embedder.py` + `profiler.py` | hash embedder 维度/确定性；`build_profile` facts 抽取在固定样例上的结果 | 仅被 smoke 间接覆盖 | P1 |
| 11 | `Etude/backend/app/db.py` | 迁移/建表幂等；`readiness` 在缺音频/图片时的判定 | 1,204 行数据层只有间接覆盖 | P1 |
| 12 | `Etude/scripts/ui_smoke.js` | **接入 CI**（puppeteer/playwright 或 `node` 无头） | 1,023 行前端冒烟脚本写了但从未在流水线跑 | P1 |
| 13 | `TideWatch/scripts/gen_sample.py` + `eval/run_eval.py` | 合成数据条数/正例比例稳定；`run_eval` 输出 schema 稳定 | eval 结论可信度的前提；当前仅 smoke 断言 F1>0 | P1 |
| 14 | `WingMan/backend/app/desktop.py` | 单实例锁、关闭协商在 Windows 真机行为 | 613 行桌面壳无 CI 覆盖 | P2 |
| 15 | `WingMan/backend/app/engine/analyzer.py` + `planner.py` | 空/超长输入的解析与降级 | 67/70 行，零直测 | P2 |
| 16 | `Etude/backend/app/server.py` + `desktop.py` | 端口占用时回退、webview 不可用回退浏览器 | 无测试 | P2 |
| 17 | `TideWatch/src/tidewatch/io.py` | 畸形 JSONL 行跳过而非崩溃 | 数据摄入健壮性 | P2 |
| 18 | 三项目 `conftest.py` / 共享夹具 | 把 WingMan 重复样板下沉；统一 `tmp_path`、加 `--cov` 组 | 可维护性 | P2 |

### 4.1 P0 测试完整代码示例

#### 例 1（P0-1）WingMan `store.py` facts 唯一键回归 —— `backend/tests/test_store_facts.py`

```python
"""store 层回归：同 key 不同 value 的事实不得互相覆盖。

历史 bug（见 app/store.py:45-56）：早期唯一键写成 (chat_id, subject, key)，
配合 INSERT OR REPLACE，把「喜欢火锅」静默覆盖掉「喜欢猫」——不报错。
这条测试把修复后的语义钉死。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


@pytest.fixture
def store(tmp_path):
    """每个用例一个全新的库，绝不碰真实 backend/data。

    Store 每次操作开新连接、没有 close()，故此夹具无需收尾。
    """
    from app.store import Store

    s = Store(tmp_path / "wingman.db")
    s.init()
    return s


def _chat(store, chat_id: str = "qq:xiaolu") -> str:
    store.upsert_chat(chat_id, "qq", name="小鹿", peer_name="小鹿")
    return chat_id


def test_same_key_different_values_do_not_overwrite(store):
    """「喜欢」是一对多：喜欢猫、喜欢火锅必须是两条并列事实。"""
    from app.schemas import Fact

    cid = _chat(store)
    store.upsert_fact(cid, Fact(subject="peer", key="喜欢", value="猫"))
    store.upsert_fact(cid, Fact(subject="peer", key="喜欢", value="火锅"))

    values = {f.value for f in store.list_facts(cid)}
    assert values == {"猫", "火锅"}, f"事实被静默覆盖了：{values}"


def test_upsert_same_value_is_idempotent(store):
    """同一条事实写两次不应产生重复行。"""
    from app.schemas import Fact

    cid = _chat(store)
    fact = Fact(subject="peer", key="喜欢", value="猫")
    store.upsert_fact(cid, fact)
    store.upsert_fact(cid, fact)

    rows = [f for f in store.list_facts(cid) if f.key == "喜欢"]
    assert len(rows) == 1, f"重复写入产生了 {len(rows)} 行"


def test_person_level_fact_without_chat_id_is_kept(store):
    """对象级事实（无具体渠道）也要能被唯一键保护，不能被反复插重。"""
    from app.schemas import Fact

    pid = store.create_person("小鹿")
    # chat_id 为空的对象级事实
    store.upsert_fact("", Fact(subject="peer", key="怕", value="黑", person_id=pid))
    store.upsert_fact("", Fact(subject="peer", key="怕", value="黑", person_id=pid))

    got = store.list_facts_for_person(pid)
    assert [f.value for f in got if f.key == "怕"] == ["黑"]
```

#### 例 2（P0-3）Etude `prompts.py` 契约 —— `backend/tests/test_prompts.py`

```python
"""提示词契约测试。

这一层没有网络、纯字符串拼装，但它是「学习效果」的上游：
scene 定义写错，口语卡就退化成中译英（见 app/prompts.py 文件头表格）。
"""
from __future__ import annotations

import pytest


def test_build_messages_has_system_and_user():
    from app.prompts import build_messages

    msgs = build_messages("appreciate", kind="word", examples=6, zh_variants=3)
    roles = [m["role"] for m in msgs]
    assert roles == ["system", "user"]
    system = msgs[0]["content"]
    # 最关键的一条约束（scene 不是逐字翻译）必须在系统提示里
    assert "not a translation" in system


def test_user_message_carries_target_and_counts():
    from app.prompts import build_messages

    user = build_messages("appreciate", kind="word", examples=6, zh_variants=3)[1]["content"]
    assert "appreciate" in user
    assert "6" in user  # examples 数写进了 schema 指令


@pytest.mark.parametrize("code", ["ja", "ko", "fr", "de", "es", "ru", "it", "pt", "ar"])
def test_unsupported_languages_raise_instead_of_faking_output(code):
    """未开放语言必须明确报错，不许默默生成质量未验证的素材。"""
    from app.prompts import build_messages, language_profile

    assert language_profile(code)["supported"] is False
    with pytest.raises(NotImplementedError):
        build_messages("こんにちは", kind="sentence", language=code)


def test_classify_target_separates_word_phrase_sentence():
    from app.prompts import classify_target

    assert classify_target("appreciate") == "word"
    assert classify_target("be about to") == "phrase"
    assert classify_target("I'd rather you didn't") == "sentence"
```

#### 例 3（P0-4/5）WingMan 采集层**真实 Win32** 守卫 —— `backend/tests/test_collect_windows_real.py`

```python
"""真实 Windows 上的采集层守卫。

只有 windows runner 会执行（ubuntu 上整体 skip）。
这条补的是最大的 CI 盲区：产品是 Windows 桌面程序，
但此前所有平台都只在 Linux 上验证过「模拟的 Windows」。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="真实 Win32 采集能力，仅 Windows runner 有效"
)


def test_winapi_reports_windows_and_lists_processes():
    from app.collect import winapi

    assert winapi.IS_WINDOWS is True
    procs = winapi.list_processes()
    assert procs, "真机上列不出任何进程，Win32 调用链断了"
    assert any(isinstance(getattr(p, "pid", None), int) for p in procs)
    # 当前进程必须能被列出（最稳的自证）
    assert any(getattr(p, "pid", -1) == os.getpid() for p in procs)


def test_process_path_of_self_is_readable():
    from app.collect import winapi

    path = winapi.process_path(os.getpid())
    assert path, "读不到自身进程路径 —— QueryFullProcessImageName 调用有问题"
    assert Path(path).exists()


def test_clipboard_roundtrip_on_real_windows():
    """写进去、读回来必须一致；这是「半自动采集」的地基。"""
    from app.collect import clipboard

    assert clipboard.IS_WINDOWS is True
    marker = "wingman-clipboard-roundtrip-" + os.urandom(3).hex()
    before = clipboard.sequence_number()

    assert clipboard.write_text(marker) is True
    assert clipboard.sequence_number() != 0
    assert clipboard.read_text() == marker, "剪贴板写回读不一致"

    # 收尾：不让测试污染用户剪贴板
    clipboard.write_text("")
```

> 配套 CI 改动：把 §2.4 里的 `os: [ubuntu-latest, windows-latest]` 加上，这 3 条用例才会生效。

---

## 5. 落地建议

### 5.1 把覆盖率抬到有意义的水位（三项目统一方案）

**第一步——度量（一周内）**

```bash
pip install pytest-cov
```

在**各项目自己的配置载体**里落配置（WingMan 目前**连 `pyproject.toml` 都没有**，建议先建一个最小 `backend/pyproject.toml`）：

```toml
# WingMan: backend/pyproject.toml（新建）
# Etude:   backend/pyproject.toml（新建）
# TideWatch: 追加到现有 pyproject.toml 的 [tool.coverage.*]
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"
markers = [
  "slow: 时间/内存敏感用例，允许单独跳过",
  "e2e: 需要真实 HTTP 服务或网络隔离",
]

[tool.coverage.run]
source = ["app"]            # TideWatch 改 "src/tidewatch"
branch = true               # 分支覆盖：比行覆盖更能发现「只走了 if」
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
show_missing = true
skip_covered = true
exclude_lines = [
  "pragma: no cover",
  "if TYPE_CHECKING:",
  "raise NotImplementedError",
  "if __name__ == .__main__.:",
]
```

**第二步——设门槛（渐进，别一上来卡死）**

| 阶段 | 门槛 | 说明 |
|---|---|---|
| 起步（现状~第 1 周） | `--cov-fail-under=0`，**只上传 XML 到 artifact/Codecov** | 先看到真实数字，不阻断任何人 |
| 第 2–3 周 | `--cov-fail-under=<当前-5>` | 用「比当前低 5 个点」做地板，先冻结退化 |
| 稳定期 | 核心模块单列门槛：`store.py`/`db.py`/`prompts.py` 逐个设 80% | 全局水位会被 Windows 专有代码和中立代码拉低，**按模块卡比按全局卡更公平也更有效** |

参考起点（基于 §1 的测试:代码比与用例密度，**为估计值，需实测校准**）：

| 项目 | 预估行覆盖（待确认） | 建议首个全局门槛 |
|---|---|---|
| TideWatch | 较高（~75–85%） | 70% |
| Etude | 中高（~65–75%） | 60% |
| WingMan | 中（Windows 专有代码在 Linux 上覆盖不到，~45–60%） | 45%，且**在 Linux/Windows 两个 job 分别上报**后再合并 |

**第三步——CI 接入**：见 §2.4 的 `--cov=app --cov-report=xml --cov-fail-under=NN`，并把 `coverage.xml` 作为 artifact 上传；如需 PR 注释可接 Codecov。

> **重要提醒**：WingMan 的覆盖率**不要只看 Linux 数字**。`winapi.py`/`clipboard.py`/`desktop.py` 在 ubuntu 上走替身分支，行覆盖会虚高或虚低；必须**两个 OS 的 coverage 合并**（`coverage combine`）后再看，否则数字没有意义。

### 5.2 双环境（Windows 本地 + Actions Linux）策略

**核心矛盾**：WingMan 是 Windows 桌面产品，但 Linux CI 跑不了 Win32；强行在 Linux 上 `skipif` 会让守卫形同虚设。策略是**「三条腿」**：

| 腿 | 环境 | 跑什么 | 作用 |
|---|---|---|---|
| A. 跨平台快测 | **Actions Linux**（每 PR） | 全部平台无关用例 + 模拟 Linux 守卫 + `compileall` + ruff | 快速反馈、拦 lint/语法/逻辑退化 |
| B. Windows 真机 | **Actions windows-latest**（每 PR，与 A 并行） | 真实 Win32 用例（§4.1 例 3）+ `skipif(win32)` 反向守卫 + 打包冒烟 | 覆盖产品本体平台 |
| C. 本地开发（Windows） | 开发者机器 | `pytest tests/ -m "not slow"`；提交前 `ruff check`（可挂 `pre-commit`） | 秒级反馈，不依赖 CI 排队 |

**具体做法**：

1. **标记化慢测**：给 `test_collect_budget.py`、`test_memory_footprint.py`、`test_e2e_stub.py` 打 `@pytest.mark.slow`/`e2e`；本地默认 `-m "not slow"`，CI 全跑。
2. **平台守卫用 `skipif` + 反向守卫配对**（WingMan `test_collect_offwindows.py:203-229` 已是范本）：正向测「非 Windows 降级」，反向测「Windows 上必须用真身」。反向守卫只有在 Windows job 里才有意义——这正是不加 Windows job 时它们恒被跳过的原因。
3. **临时目录统一用 `tmp_path`**（pytest 内建清理），替换 WingMan 里手写的 `mkdtemp`+`rmtree`，减少「清理失败污染下个用例」的风险。
4. **pre-commit 本地门（补三项目空缺）**：

```yaml
# .pre-commit-config.yaml（三项目均无，建议新增）
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-merge-conflict
```

> 对 WingMan 额外加一条本地 hook：运行 `test_privacy_pseudonyms.py`（它需要完整 git 历史，本地 clone 有；CI 浅克隆没有——这正是 §3.1-D 的成因）。这样「发版前必须过隐私守卫」既快又可靠，不必为它在 CI 拉全量历史。

5. **缓存对齐**：TideWatch 补 `cache: pip`（§2.3-3）；三项目统一 `cache-dependency-path` 指向各自的锁/开发依赖文件。

### 5.3 优先级路线图

| 周 | 动作 | 产出 |
|---|---|---|
| W1 | 三项目加 `pytest-cov` + `[tool.coverage]`；CI 上传 coverage.xml（不设门槛）；WingMan 建最小 `pyproject.toml` | 拿到真实覆盖率基线 |
| W1 | WingMan CI 加 `windows-latest` + `lint` job；Etude CI 加 ruff job | 补上两个最硬的 CI 缺口 |
| W2 | 补 §4 的 5 条 P0 测试；TideWatch 补 `cache: pip` | 核心链路有回归锚点 |
| W3 | 设 `--cov-fail-under` 地板（当前-5）；核心模块单列门槛；三项目加 pre-commit | 冻结退化 |
| W4+ | 补 P1 清单；Etude 把 `ui_smoke.js` 接入 CI | 覆盖率稳步上行 |

---

## 6. 风险与「待确认」项

1. **覆盖率数字为估计值**：本报告未运行测试套件（按任务约束），§5.1 的「预估行覆盖」为基于测试:代码比与用例密度的推断，标注为「待确认」，须以 `pytest-cov` 实测为准。
2. **WingMan `routes_persons.py`/`routes_data.py` 的「0 处引用」**：基于模块名 grep，可能因测试通过 TestClient（而非直接 import）而漏计；`test_persons.py`（767 行）大概率经 HTTP 端覆盖了 persons 路由，故标 P1 而非 P0。
3. **`scripts/preflight.py`（1,679 行）**：`test_preflight.py`（627 行）是否覆盖其全部子命令路径未逐条核对，标注待确认。
4. **Etude `ui_smoke.js` 的运行前置**（是否需 `cdp.js`/浏览器）未深入，接入 CI 前需确认依赖。

---

## 附：完成情况说明

- 已读：三项目全部 `ci.yml`、`conftest.py`（Etude/TideWatch）、`pyproject.toml`/`Makefile`/`Dockerfile`/`requirements*.txt`、按抽样精读 15+ 个测试文件（含三项目最大测试文件）、AST 全量空断言扫描（637 test 函数）、按模块名 grep 覆盖映射、`wc -l` 全量计数。
- 未做（遵约束）：未修改任何克隆文件、未 `pip install`、未执行测试套件。
- 本报告已落盘：`deliverables/software-company/review/qa-review.md`。
