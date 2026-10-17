---
tags: [领域/诊断, 类型/报告]
---

# WorkBuddy 连淘宝 · 可行方案对比

> 2026-10-17 ｜ 目标：让 WorkBuddy 能搜淘宝、读商品、拿 SKU（颜色/尺码/材质）
> 结论：官方通道被账号权限拦住，第三方 MCP 可以绕过去，代价是要本机跑一个有头浏览器

---

## 一、官方通道为什么不行（已实测）

淘宝桌面版 v2.5.0（2026-03-11）上线了 AI 插件，支持"一键配置 OpenClaw、QoderWork 等多种 AI 智能体"，走 MCP 协议，本机端口配对。这本来是最省事的路。

但你本机命中的是 `NOT_AUTHORIZED`——账号侧的"AI 应用接入"权限未开通。判定依据来自客户端内部错误码定义（详见 `淘宝桌面端-CLI通道诊断与替代方案.md`）：`reLoginRequired: false`，意思是**不需要重新登录**，是权限没开。

| 探测 | 结果 |
|---|---|
| `taobao-native _ping` | `{"result":"ok"}`，通道完好 |
| `taobao-native get_current_tab` | `内测期间仅开放部分用户使用` |
| `s.taobao.com/search` | 200 但返回登录页 |

所以官方这条路只能等灰度，你这边做不了什么。

---

## 二、三条可行路径（按推荐度排序）

### 方案 A · taobao-mcp-server（推荐）

**地址**：`github.com/fanqi99-creator/taobao-mcp-server`（MIT，2026-09-07 首次提交）

Node + TypeScript + Playwright，跑**有头 Chromium**（真实浏览器窗口，非无头）。核心价值是 `view_taobao_item` 这个工具**直接返回 SKU 规格选项（材质/颜色/尺码）**——正好补上之前一直拿不到的那部分数据。

工具清单：

| 工具 | 能干什么 |
|---|---|
| `login_taobao` | 弹出浏览器窗口，你手动扫码登录 |
| `complete_taobao_login` | 保存登录态 |
| `check_taobao_auth` | 检查登录是否还有效 |
| `search_taobao_item` | 关键词搜索，返回标题/价格/链接 |
| **`view_taobao_item`** | **商品详情 + SKU 规格（材质/颜色/尺码）** |
| `view_taobao_item_image` | 截主图 |
| `add_to_cart_taobao` | 加购物车（不下单） |
| `buy_now_taobao` / `pay_now_taobao` | **会真花钱，可以不用** |

**优点**：拿得到 SKU；登录态存在真实浏览器 Profile 里（不是 cookie 快照），风控不敏感；MIT 开源，代码可自己看。

**缺点**：只有一个 commit，实际稳不稳要跑了才知道；每次操作随机延迟 5–10 秒（防风控），慢；浏览器窗口必须保持开着。

---

### 方案 B · WorkBuddy 自带浏览器控制（最省事，零安装）

不装任何第三方服务，用 WorkBuddy 的浏览器控制能力，在你已登录的浏览器里直接操作淘宝网页。

**前提**：设置 → Agent → 浏览器控制 打开，并装好对应浏览器的 WorkBuddy 扩展（Chrome / Edge / QQ 浏览器）。

**优点**：零安装、零第三方代码、用自己的登录态。
**缺点**：靠页面操作，拿不到结构化的 SKU 数据；淘宝页面改动会失效；速度慢。

---

### 方案 C · ali-mcp（不推荐）

**地址**：`github.com/Tsinglung-Tseng/ali-mcp`（MIT，Go + go-rod，4 个 commit）

同时支持淘宝和闲鱼，`taobao_get_item_detail` 声明返回 SKU。

**为什么不推荐**：README 自己写着"所有 DOM 选择器为初版假设，需实机校正才能可靠工作"，每个 `.go` 文件顶部都有 `TODO(selectors)`。也就是说作者还没在真机上跑通。另外要装 Go 环境。**投入产出比不如方案 A。**

---

### 方案 D · 淘宝客 MCP（明确不合适）

`taoke-mcp` 需要淘宝联盟 PID + 授权 session，功能是转推广链接、拿佣金。你是要选衣服，不是做淘客，排除。

---

## 三、方案 A 的完整配置

Node 22.22.2 已就绪，18070/8787 端口空闲，环境这一侧没有障碍。

### 步骤

```bash
# 1. 克隆到一个固定目录（不要放临时目录，浏览器 Profile 要留着）
cd C:/Users/HP/tools
git clone https://github.com/fanqi99-creator/taobao-mcp-server.git
cd taobao-mcp-server

# 2. 安装依赖（会下载 Playwright 的 Chromium，约 150MB，国内可能慢）
npm install
npm run build
```

### 写入 `~/.workbuddy/mcp.json`

```json
{
  "mcpServers": {
    "taobao": {
      "command": "node",
      "args": ["C:/Users/HP/tools/taobao-mcp-server/dist/server.js"]
    }
  }
}
```

如果文件里已有其他 server，把 `taobao` 这一段合并进 `mcpServers`，别覆盖。

### 启用

配置文件写完**不会自动生效**。要去连接器管理页右上角的"自定义连接器"入口，找到新出现的 server，点"信任"。

### 首次使用

1. 对话里让我调 `login_taobao` → 弹出一个 Chromium 窗口
2. 你在窗口里扫码登录淘宝（程序不接触账号密码）
3. 我调 `complete_taobao_login` 保存状态
4. 之后就能搜商品、读 SKU 了

---

## 四、风险与代价（必须知道）

**隐私**：淘宝官方自己在 v2.5.0 更新说明里写过，启用 AI 接入后客户端会向 AI 工具暴露昵称、头像、收货地址、联系人、历史订单、购物车、浏览记录、关注店铺、旺旺聊天记录。第三方方案虽然走的是浏览器页面而不是官方接口，暴露面小一些，但**登录态本身在你的机器上**，代码是第三方写的——建议装之前自己扫一眼 `src/` 目录，或者只用它搜索、不给它加购权限。

**风控**：自动化访问淘宝可能触发验证。作者自己加了 5–10 秒随机延迟，仍然可能被要求重新扫码。**不要高频反复跑**。

**稳定性**：淘宝前端模板经常改，`view_taobao_item` 读规格的部分对天猫页面做了兼容，但仍可能失效。

**别用的工具**：`pay_now_taobao` 会真的付款。`add_to_cart_taobao` / `buy_now_taobao` 可以留着，但不必要。

---

## 五、我的建议

**装方案 A。** 理由很直接：你卡了一整轮的问题就是拿不到 SKU（颜色/尺码/材质），方案 A 是唯一能结构化拿到这个数据且不用改淘宝账号设置的路。装完之后，选外套这件事就变成：你说一句"搜立领夹克 正肩 短款"，我拉 20 件，带尺码表和颜色库存，直接按你的 168/65/45 肩宽对数字筛。

如果只是想先试试水，走方案 B，五分钟能验证可行性，但拿不到尺码表。

要我现在就把方案 A 装上吗？克隆和编译我可以做，登录那一步必须你自己扫码。

---

## 五点五、实操：走方案 B 已跑通（2026-10-17 实测）

用户装了 Edge 扩展，但该扩展没有对应工具暴露出来。改用 **Edge 远程调试端口 + Playwright** 直接驱动，已验证可行。

### 环境准备（已完成，可复用）

```bash
# 目录：C:/Users/HP/tools/browser-agent
npm init -y
npm i agent-browser --registry=https://registry.npmmirror.com
npm i playwright-core --registry=https://registry.npmmirror.com
```

`agent-browser install` 不要跑——它去 storage.googleapis.com 下 Chromium，本机超时三次必失败。
本机 Chrome/Edge 已装，直接用系统浏览器即可。

### 启动浏览器（关键：必须常驻）

```bash
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/HP/tools/edge-cdp-profile" \
  --no-first-run --no-default-browser-check "https://www.taobao.com"
```

三个坑，全部实测踩过：

1. **必须指定 `--user-data-dir`**。Edge/Chrome 136+ 禁止默认配置文件开远程调试，端口不会起来。
2. **必须用后台常驻任务启动**。用 PowerShell `Start-Process` 启动的进程会被会话回收，
   起来几十秒就 ECONNREFUSED。改用后台 bash 任务（起进程后 `sleep 1800` 挂住）才稳定。
3. **必须绕开本机代理**。本机 `HTTP_PROXY=http://127.0.0.1:7582` 会劫持发往 127.0.0.1:9222 的请求，
   报 `Unexpected status 502 ... does not look like a DevTools server`。
   运行脚本前执行：

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NODE_OPTIONS
export NO_PROXY="127.0.0.1,localhost"
```

### 脚本

| 文件 | 作用 |
|---|---|
| `tb-check.js` | 连 CDP，打开淘宝首页，判断是否登录 |
| `tb-login.js` | 跳登录页并截图，**不关闭浏览器**（留给你扫码） |
| `tb-search.js` | 搜索关键词，抽取 `item.taobao.com` / `detail.tmall.com` 链接与周边文字 |

连接方式：`chromium.connectOverCDP('http://127.0.0.1:9222')`，取 `contexts()[0].pages()[0]`。

### 登录是硬门槛

未登录时 `s.taobao.com/search` 能打开，但结果区停在「加载中...」，`count = 0`。
**淘宝目前强制登录才出搜索结果**，这一步绕不过去，必须扫码。

登录态存在 `C:/Users/HP/tools/edge-cdp-profile` 里，扫一次之后长期有效，除非 cookie 过期。

---

## 六、参考来源
| 来源 | 内容 |
|---|---|
| 淘宝桌面版 v2.5.0 更新日志 | AI 插件支持一键配置 OpenClaw / QoderWork |
| 亿邦动力 / BlockBeats 报道 | MCP 协议本地部署、付款需本人确认、隐私暴露范围 |
| `github.com/fanqi99-creator/taobao-mcp-server` | 方案 A 源码与 README |
| `github.com/Tsinglung-Tseng/ali-mcp` | 方案 C 源码，含"选择器待校正"自述 |
| `github.com/shopmeskills/mcp` | cn-ecommerce-search（npx 零配置，依赖第三方 API，未采用） |
| `淘宝桌面端-CLI通道诊断与替代方案.md` | 本机 `NOT_AUTHORIZED` 的代码级证据 |
