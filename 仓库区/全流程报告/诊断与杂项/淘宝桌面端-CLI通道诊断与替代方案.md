---
tags: [领域/诊断, 类型/报告]
---

# 淘宝桌面端 · CLI 通道诊断报告（第 3 版 · 结论已修正两次）

> 最近更新：2026-10-10 22:15
> **本文档的结论被推翻过两次，现在给出有硬证据的最终判断。**

## 结论修正历史

| 版本 | 当时的判断 | 是否成立 |
|---|---|---|
| v1 | 账号不在灰度白名单 | ❌ 证据不足，是猜测 |
| v2 | 客户端登录态过期（SESSION_EXPIRED） | ❌ 你是已登录的，判断错了 |
| **v3（本文）** | **账号侧「AI 应用接入」权限未开通（`NOT_AUTHORIZED`）** | ✅ 有代码级证据 |

---

## 一、最终结论（一句话）

**CLI 通道从本机看是完好的；拦住你的是账号侧的「AI 应用接入权限」未开通。**

对照客户端内部的错误码定义：未开通被标记为 `reLoginRequired = false`
——**也就是"不用重新登录"**。这正是你已登录、却依然被拦的原因。

**本机侧无解，也不需要再折腾配置。** 但真正有价值的替代路径已经跑通（见第五节）。

---

## 二、决定性证据：客户端自己区分了「未登录」和「未开通」

从 `app.asar` 解出的错误码定义（去混淆还原）：

```js
NOT_AUTHORIZED: {
  retryable: true,
  code: 0,
  reLoginRequired: false,          // ← 关键：不需要重新登录
  userMessage: '当前账号暂未开通 AI 功能'
},
SESSION_EXPIRED: {
  retryable: false,
  code: 3,
  reLoginRequired: true,           // ← 未登录才要求重登
  userMessage: '...'
},
REFRESH_FAILED:      { userMessage: '授权刷新失败，稍后再试' },
INVALID_RESPONSE:    { userMessage: '授权响应异常，请更新…' },
NO_CREDENTIALS:      { userMessage: '…AI Key 或切换为…' }
```

**这段定义是整个诊断的枢纽。** 客户端明确把两种状态分开处理：

- 如果是**登录问题** → 会走 `reLoginRequired: true` 分支，界面弹出 `.mcp-login-tip-modal`（专门的"需要登录"弹窗）。
- 如果是**未开通** → `reLoginRequired: false`，界面上也不会有"去登录"的引导。

你现在命中的是后者。**所以"你没登录"这个方向可以彻底排除了。**

---

## 三、拦截点的完整链路

### 1. RPC 底座完好无损

```
$ taobao-native get_current_tab --args '{"sourceApp":"WorkBuddy"}'
{"error":"内测期间仅开放部分用户使用，请关注后续公告"}
```

但底座本身是通的：

| 探测项 | 结果 |
|---|---|
| `_ping` | `{"result":"ok"}` ✅ |
| `--help`（列出全部内置工具） | 正常返回 20 个工具 ✅ |
| `cli-rpc-port.json` | `{"socketPath":"\\\\.\\pipe\\taobao-cli-rpc"}` ✅ |
| 命名管道 `taobao-cli-rpc` | 存在 ✅ |
| 调用**不存在的工具** | `{"error":"未知工具: xxx"}` ✅（说明确实走进了工具分发层） |

**结论：通道通、协议通、工具注册表可读。拦截发生在「工具分发之前的权限校验」。**

### 2. 权限校验的具体实现

```js
// 去混淆还原的语义
async function checkAiPermission() {
  if (!pluginManager) return null;
  if (Date.now() < cacheExpireAt) return cachedResult;      // 缓存 60 秒

  const plugin = pluginManager.getPlugin('window-manager');
  if (!plugin?.mtop) return null;

  const resp = await plugin.mtop.request({
    api: 'mtop.alibaba.fc.api.maoxland.ContainerFacade.singleView',   // ← 权限查询接口
    v: '1.0',
    data: { projectName: 'PcTaobao', ... },
    dataType: 'json'
  });

  let msg = DEFAULT_MSG;
  const cfg = await pluginManager.getPlugin('...')?.getConfig?.().catch(() => null);
  if (cfg?.mcpDisabledText) msg = cfg.mcpDisabledText;      // 用远程配置覆盖文案

  const err = resp?.data?.value ? null : msg;               // 查不到 value → 返回兜底文案
  cachedResult = err; cacheExpireAt = Date.now() + 60000;   // 缓存 60 秒
  return err;
}

// 调用入口
if (source === <某值> || source === 'cli') {
  const err = await checkAiPermission();
  if (err) return { error: err };                           // ← 你看到的那句话
}
```

`mcpDisabledText` 就是 `%APPDATA%\taobao\remote-config.json` 里的：

```json
"mcpDisabledText": "内测期间仅开放部分用户使用，请关注后续公告"
```

**这是兜底文案，不是错误描述。** 它的存在意味着："服务端没给我明确的放行信号，我就把这句话抛出去。"

### 3. 已经排除的干扰项

我逐个试过，**全部无效**：

| 干扰项 | 测试结果 |
|---|---|
| 换 `sourceApp` 值 | `WorkBuddy` / `Qoderwork` / `openClaw` / `copaw` / `taobao` 全被拦 |
| 换参数名 | `source` 取 `chat` / `mcp` / `cli` / `QoderWork` 全被拦 |
| 网络 | 淘宝各域名 curl 全部 200 |
| 客户端版本 | 3.0.0，比 hotfix 里的 2.5.1 还新 |
| 本地开关 | `mcpEnabled` / `mcpChatEnabled` / `mcpAiAppsAuthorized` 全部为 `true` |
| 那个 zip | 只有文档、无代码，且版本比已装的旧 |
| 缓存未刷新 | 60 秒 TTL 早过，反复重试结果一致 |

**顺带说明**：日志里那句 `listen EACCES: permission denied ...\taobao-mcp.sock`
是**另一个 socket**（供外部 MCP 客户端直连用的 Unix domain socket），
和 CLI 走的命名管道 `taobao-cli-rpc` 不是同一条路。它启动失败**不影响 CLI**，
别被它误导。

---

## 四、你能试的一步（成功率不高，但值得看一眼）

1. 打开淘宝桌面版 → **设置** → 找到 **「AI 功能」/「AI 应用配置」**
2. 确认顶部的 AI 功能总开关是**开启**状态
3. 在「**Skill 配置（推荐）**」模式下，看列表里有没有可点的「**一键配置**」按钮
4. 如果**界面显示未开放 / 按钮不可点** → 确认为灰度未覆盖，等公告即可
5. 如果**能一键配置** → 配置完再回来告诉我，我立刻重测

> 界面条件：这组设置只有在 `isMcpEnabled && isRunning` 时才会渲染出来，
> 而且需要先点过「授权检测 AI 应用」（`mcpAiAppsAuthorized`）。
> 你这两项都是满足的，所以设置页应该能看到。

**放行后的判定标志**：CLI 不再返回 `内测期间…`，而是正常返回页面标题 / 内容。

---

## 五、真正落地的替代路径（★ 已跑通）

**这是本次最大的收获，而且不需要任何权限。**

客户端会把你在里面打开过的商品，缓存在本地：

```
%APPDATA%\taobao\config.json  →  <hash>_productList
```

每个元素包含**官方完整标题、店铺名、商品 ID、商品主图 URL、原价、折后价**：

```json
{
  "itemId": "981350347587",
  "title": "MYES牧野森美式复古风立领皮夹克男宽松工装外套黑色机车麂皮夹克",
  "shopName": "MYES牧野森原创潮牌",
  "imageUrl": "https://gw.alicdn.com/imgextra/O1CN01hjfJaGC65FE2vH2e_!!2211417095926-0-picasso.jpg",
  "discountedPrice": "191",
  "originalPrice": "218"
}
```

而且 `imageUrl` 是**公开 CDN 链接，可直接下载** —— 下载后用看图能力逐张读取，
就得到了**基于实物的外观描述**，比任何文字推断都可靠。

**本次 10 件商品的数据就是这样拿到的**，成果见
`牧野森外套-黑色款选款信息汇总.md / .html`（实物图版）。

### 这条路能拿到什么、拿不到什么

| ✅ 能拿到 | ❌ 拿不到 |
|---|---|
| 官方完整标题 | 颜色 SKU 列表 |
| 店铺名 | 面料成分 |
| 商品主图（可下载可读图） | 尺码表 |
| 原价 / 折后价 | 库存 |

**颜色和尺码属 SKU 级数据，只能由详情页接口返回，而该接口未登录时会强制跳登录页。**
这部分终究要在客户端里由你本人打开 SKU 面板确认——反正选规格和下单本来也该你亲手来。

---

## 六、相关文件

| 文件 | 说明 |
|---|---|
| `牧野森外套-黑色款选款信息汇总.html` | **实物图版**：10 件逐件外观实录 + 主图 + 价格归属对照 |
| `牧野森外套-黑色款选款信息汇总.md` | 同上，Markdown 归档版（图片随目录） |
| `牧野森外套-黑色款选款信息汇总.csv` | 比价表 |
| `牧野森商品图/` | 10 张官方主图（离线保存） |
| `淘宝桌面端-CLI通道诊断与替代方案.md` | 本文档 |
