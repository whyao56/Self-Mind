# Obsidian 笔记同步 GitHub —— 全流程报告

> 排障日期：2026-10-01
> 仓库：`D:\Obsidian\Documents\MyDigitalBrain` → `https://github.com/whyao56/Self-Mind.git`
> 分支：本地 `master` → 远程 `20260930`

---

## 一、问题现象

- 昨天尝试 push 成功，今天再试在 push 环节出问题。
- 表现为：push 卡住 / 超时 / `401 Unauthorized`。
- Clash Verge 已开启。

---

## 二、根因诊断（真实原因）

**核心病根：`credential.helper` 配置冲突。**

排查中发现系统里存在**两个** credential helper 同时生效：

| 来源 | 值 | 后果 |
|---|---|---|
| `C:\Users\HP\.workbuddy\binaries\PortableGit\versions\1.2.0\etc\gitconfig`（系统级） | `helper-selector` | **先执行 → 弹图形选择窗口 → 无人值守时永久挂起** |
| `C:\Users\HP\.gitconfig`（用户级） | `manager` | 排在后面，轮不到执行 |

Git 会把所有 helper **串行调用**。系统级的 `helper-selector` 排在最前，它需要弹出图形窗口让用户选择凭据来源；在命令行 / 自动化 / 超时场景下窗口弹不出来，git 就一直等待 → 表现为"卡住"；拿不到凭据时 GitHub 返回 `401 Unauthorized`。

**次要因素：**
- 网络确认可用，Clash 代理 7897 正常（实测 HTTP 200，1.4~5 秒）。
- 仓库体积偏大（`.git` 约 223 MB，工作区 233 MB），主要来自 `图片、附件/` 下的 PNG（单个 1.5~2.6 MB），会拖慢 push。
- 已有凭据为 `gho_` 开头（GCM 浏览器 OAuth 生成的令牌），非手动 PAT，有效期较短，存在再次过期风险。

---

## 三、已执行的修复

### 1. 修复凭据链（关键）

在用户级配置中插入**空 helper**（作用是清空之前所有 helper），再挂 `manager`：

```bash
git config --global --unset-all credential.helper
git config --global credential.helper ""      # 置空 = 清空前面所有 helper
git config --global --add credential.helper manager
git config --global credential.https://github.com.provider github
git config --global credential.gitHubAuthModes browser
```

修复后配置链：
```
PortableGit/.../gitconfig   helper-selector
C:/Users/HP/.gitconfig      ""                ← 清空
C:/Users/HP/.gitconfig      manager           ← 唯一生效
```

验证：`git credential fill` 瞬间返回凭据（不再弹窗挂起）。

### 2. 优化大仓库传输参数

```bash
git config --global http.postBuffer 524288000   # 单次上传上限提到 500MB
git config --global http.lowSpeedLimit 0        # 关闭低速断连
git config --global http.lowSpeedTime 999999
git config --global core.compression 0          # 降低压缩，省 CPU
```

### 3. 推送验证成功

```
To https://github.com/whyao56/Self-Mind.git
   3803796..bb3e9eb  master -> 20260930
```

---

## 四、流程梳理（完整版）

### 本质：三件事

```
笔记 → [commit 打包] → [push 上传] → GitHub 云端
         ↑                 ↑
      obsidian-git      凭据（证明你是谁）
```

| 概念 | 是什么 | 类比 |
|---|---|---|
| commit | 给当前笔记拍快照，存在本地 `.git` | 本地存档 |
| push | 把本地快照上传到 GitHub | 上传云端 |
| 凭据 / PAT | 向 GitHub 证明身份 | 门禁卡 |
| credential.helper | 帮你保管凭据的程序 | 卡包 |
| 代理（Clash） | 帮你连上 GitHub 的通道 | 专用通道 |

### 五大组件

1. **Obsidian 笔记** —— `D:\Obsidian\Documents\MyDigitalBrain`
2. **obsidian-git 插件** —— 提供按钮 / 定时备份
3. **本地 git 仓库 `.git`** —— 记录快照
4. **凭据管理器** —— 保存 GitHub 令牌
5. **GitHub 远程仓库** —— `whyao56/Self-Mind`

---

## 五、日常使用：obsidian-git 操作

在 Obsidian 中按 `Ctrl+P` 打开命令面板：

| 命令 | 作用 |
|---|---|
| `Git: Commit all changes` | 只打包，不上传 |
| `Git: Push` | 上传到 GitHub |
| **`Git: Commit-and-sync`** | **一键打包 + 上传（最常用）** |
| `Git: Pull` | 从 GitHub 拉最新 |
| `Git: Open source control view` | 查看改动文件 |

右下角状态栏显示当前状态与分支。

---

## 六、插件配置完整对照表

### 配置入口在哪（关键）

**左下角 ⚙️ 设置 → 左侧列表向下滚动 → 在「社区插件」分组下面找到单独的「Git」一项。**

> 注意：不是点「第三方插件」里插件的齿轮按钮，而是设置侧栏里**单独的一项「Git」**。界面是全英文的，所以按英文原名对照。

### 【Automatic】自动备份

| 界面英文名 | 当前值 | 中文说明 |
|---|---|---|
| Auto backup interval (minutes) | **10** | 每 10 分钟自动 commit 一次 |
| Auto push interval (minutes) | **30** | 每 30 分钟自动 push |
| Auto pull interval (minutes) | **60** | 每 60 分钟自动 pull |
| Split timers for automatic commit and sync | 关 | 分开设定打包/同步计时器 |

### 【Commit】提交

| 界面英文名 | 当前值 | 中文说明 |
|---|---|---|
| Commit message on manual commit | `vault backup: {{date}}` | 手动提交信息模板 |
| Commit message on auto backup | `vault backup: {{date}}` | 自动提交信息模板 |
| `{{date}}` placeholder format | `YYYY-MM-DD HH:mm:ss` | 日期格式 |
| Stage all changes when nothing is staged | **开** | 未勾选文件时自动全选 |
| Merge strategy on conflicts | none | 冲突合并策略 |

### 【Commit-and-sync】一键同步

| 界面英文名 | 当前值 | 中文说明 |
|---|---|---|
| **Pull on startup** | **开** | 打开 Obsidian 时先拉取 |
| **Push on commit-and-sync** | 开 | 一键同步含 push |
| **Pull on commit-and-sync** | 开 | 一键同步先 pull |
| Squash commits before push | 关 | 推送前压缩提交 |
| Merge strategy | merge | 合并方式 |

### 【Authentication】认证

| 界面英文名 | 应填 | 中文说明 |
|---|---|---|
| Username on your git server | `whyao56` | GitHub 用户名 |
| Password/Personal access token | `ghp_...` | 你的 PAT（留空则用系统凭据库） |
| Author name for commit | `whyao56` | 提交署名 |
| Author email for commit | `2160444959@qq.com` | 提交邮箱 |

### 【Miscellaneous】杂项

| 界面英文名 | 当前值 | 中文说明 |
|---|---|---|
| Show status bar | 开 | 右下角显示同步状态 |
| Show branch status bar | 开 | 显示当前分支 |
| Diff view style | split | 差异对比样式 |
| Disable informative notifications | 关 | 关闭普通通知 |

### 已自动写入的配置（data.json）

以下项目已直接写入插件配置文件，打开 Obsidian 即生效：

- `autoSaveInterval`: 0 → **10**
- `autoPushInterval`: 0 → **30**
- `autoPullOnBoot`: false → **true**
- `disablePopupsForNoChanges`: false → **true**
- `autoPullInterval`: 60（保持）
- `pullBeforePush`: true（保持）
- `syncMethod`: merge（保持）

> 原配置已备份为 `data.json.bak.20261001`。

---

## 七、后续建议

### 1. 永久 PAT（已完成 ✅）

原本使用 `gho_` 开头的浏览器临时授权令牌，容易过期。现已更换为用户手动生成的永久 PAT（`ghp_...`，40 位），并存入 Windows 凭据管理器：

```bash
printf "protocol=https\nhost=github.com\nusername=whyao56\npassword=你的新PAT\n\n" | git credential-manager store
```

验证：`curl -H "Authorization: token <PAT>" https://api.github.com/user` 返回 `200`。

> 若日后仍需更换：GitHub → Settings → Developer settings → **Tokens (classic)** → Generate new token (classic)，Expiration 选 **No expiration**，Scopes 勾选 **`repo`**，复制 `ghp_...`（只显示一次）。

### 2. 缩减仓库体积

- 在仓库根目录添加 `.gitignore`，排除插件二进制：
  ```
  .obsidian/plugins/*/main.js
  .obsidian/workspace.json
  .obsidian/workspaces.json
  ```
- `图片、附件/` 下的 PNG 可先压缩再入库。

---

## 八、补充问题：分支名不匹配导致 push 被拒

### 现象

执行 `git push` 报错：

```
fatal: The upstream branch of your current branch does not match
the name of your current branch.
To push to the upstream branch on the remote, use
    git push Self-Mind HEAD:20260930
To push to the branch of the same name on the remote, use
    git push Self-Mind HEAD
```

### 原因

| 项目 | 名字 |
|---|---|
| 本地分支 | `master` |
| 远程分支 | `20260930` |

Git 默认策略 `push.default = simple` 要求**本地分支与上游分支同名**才肯推送。这里 `master ≠ 20260930`，所以被拒绝。结果是自动备份一直在 commit（积累了大量提交），但始终推不上去。

### 修复

**方案 A（推荐，保持分支名不变）**

```bash
git config push.default upstream
```

作用：允许「本地分支名与远程分支名不同」时也能推送。配置写入 `.git/config`，持久生效。

**方案 B（让两边同名）**

```bash
git branch -m master 20260930   # 本地分支改名
git push -u Self-Mind 20260930
```

### 验证

```bash
git push            # 应成功
git status -sb      # 应显示 master...Self-Mind/20260930，无 ahead/behind
```

本次修复结果：16 个积压提交全部推送成功（`af381e4..1f1d614`），`push.default = upstream` 已持久化。

---

## 九、快速排障口诀

| 症状 | 检查点 |
|---|---|
| push 卡住不动 | `git config --show-origin --get-all credential.helper` 是否有 `helper-selector` |
| 401 Unauthorized | 凭据是否有效：`printf "protocol=https\nhost=github.com\n\n" \| git credential fill` |
| 连不上 GitHub | Clash 是否开启；`curl -x http://127.0.0.1:7897 https://github.com` |
| push 特别慢 | 仓库体积；`http.postBuffer`、`core.compression` 设置 |
| 提示 non-fast-forward | 先 `git pull`，再 `git push` |
| **分支名不匹配 / upstream 报错** | `git config push.default upstream` |
| 长期没推上去 | `git status -sb` 看 ahead 数字；`git push` 补推 |
