# GitHub 上传完整操作手册 —— 全流程报告

> 整理日期：2026-10-04
> 适用场景：从零把本地项目上传到 GitHub，以及后续日常更新
> 目标：新建任何项目后，照本手册走一遍，10 分钟内完成上传

---

## 零、核心原则（先记住这一条）

> **Commit 提交 = 存到本地电脑**
> **Push 推送 = 上传到 GitHub**

只 `commit` 不 `push`，GitHub 上永远看不到你的代码。这是初学者最容易卡住的地方。

---

## 一、总览：完整链路

```
① GitHub 建空仓库
        ↓  拿到 HTTPS 地址
② VS Code 打开项目 → git init
        ↓
③ 建 .gitignore（必做）
        ↓
④ git add .  +  git commit -m "..."
        ↓  （首次需配置 user.name / user.email）
⑤ git remote add origin <地址>
        ↓  用 git remote -v 验证
⑥ git branch -M main
        ↓
⑦ git push -u origin main
        ↓  （弹窗授权则点 Authorize）
⑧ 刷新仓库页面 / git status 验证
```

---

## 二、第一阶段：在 GitHub 网页创建仓库

1. 浏览器打开 `https://github.com`，登录账号。
2. 点右上角 **+** → **New repository**。
3. 填写基本信息：
   - **Repository name**：仓库名，建议用英文，例如 `Data-Structures-and-Algorithms`。
   - **Description**：可选，一句话描述。
   - **Public / Private**：按需选择。
4. **重点：下面三个选项都不要勾选**，保持完全空的仓库：
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license
5. 点 **Create repository**。
6. 复制页面上的 HTTPS 地址，格式为：

```
https://github.com/你的用户名/仓库名.git
```

> 为什么必须保持空仓库？因为本地已经 `git init` 并提交过内容，如果远程已有提交，二者历史无关，push 时必然报 `refusing to merge unrelated histories`。

---

## 三、第二阶段：在 VS Code 里初始化本地仓库

1. VS Code → **文件 → 打开文件夹**，选中你的项目根目录。
2. 按 `` Ctrl + ` `` 打开终端，确认终端路径就是项目根目录。
3. 执行：

```bash
git init
```

> 注意：**每个项目一个独立文件夹**，不要在父目录里 `git init`，否则会把无关文件一起纳入版本控制。

---

## 四、第三阶段：创建 `.gitignore`（必做）

在项目根目录新建文件 `.gitignore`，按项目类型选一份写入：

**Python 项目：**

```gitignore
__pycache__/
*.pyc
.venv/
venv/
env/
.idea/
.vscode/
*.log
```

**Node.js / 前端项目：**

```gitignore
node_modules/
dist/
build/
.env
*.log
.DS_Store
.vscode/
```

保存文件。先建 `.gitignore` 再 `git add`，才能避免把缓存、依赖、密钥等垃圾文件一起提交上去。

---

## 五、第四阶段：暂存 + 提交

```bash
git add .
git commit -m "initial commit"
```

如果是第一次使用 Git，会提示需要配置用户名邮箱，执行一次即可（全局生效）：

```bash
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub注册邮箱"
```

配置完再重新执行上面的提交命令。

---

## 六、第五阶段：关联远程仓库

```bash
git remote add origin https://github.com/你的用户名/仓库名.git
```

检查是否关联成功：

```bash
git remote -v
```

期望输出：

```
origin  https://github.com/你的用户名/仓库名.git (fetch)
origin  https://github.com/你的用户名/仓库名.git (push)
```

---

## 七、第六阶段：统一分支名为 main

```bash
git branch -M main
```

`-M` 会把当前分支强制重命名为 `main`，与 GitHub 默认分支保持一致，避免后续 push 找不到分支。

---

## 八、第七阶段：推送到 GitHub

```bash
git push -u origin main
```

- `-u` 的作用是设置上游分支，设置过以后，后续直接 `git push` 即可，无需再写 `origin main`。
- 如果弹出 GitHub 登录授权，点允许，在浏览器里点 **Authorize** 完成授权。

---

## 九、第八阶段：验证

1. 刷新 GitHub 仓库页面，能看到文件内容即成功。
2. 终端执行 `git status`，若显示：

```
Your branch is up to date with 'origin/main'.
```

也说明本地和远程已经同步成功。

---

## 十、日常更新（只需三条命令）

每次写完代码，想要上传：

```bash
git add .
git commit -m "本次改了什么"
git push
```

**口诀：**

> 改代码 → `add` → `commit` → `push`

---

## 十一、常见错误速查

| 报错信息 | 原因 | 解决办法 |
| --- | --- | --- |
| `remote origin already exists` | 已经添加过远程仓库 | `git remote set-url origin 新地址` |
| `failed to push some refs` | 远程仓库不是空的 | `git pull origin main --allow-unrelated-histories` 再 push |
| `refusing to merge unrelated histories` | 本地和远程历史互不相关 | 加 `--allow-unrelated-histories` 参数 |
| `src refspec main does not match any` | 本地没有 main 分支，或还没提交 | 先 `git add .` 和 `git commit` |
| `Authentication failed` | 认证过期 | VS Code 左下角头像退出账号再重新登录 |
| 弹出编辑器要求写合并信息 | pull 时发生合并冲突 | 按 `Esc`，输入 `:wq` 回车保存退出 |

---

## 十二、完整命令速查版（可整段复制）

**新项目从零上传：**

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

**以后日常更新：**

```bash
git add .
git commit -m "更新说明"
git push
```

> 首次使用时，在 `git commit` 之前补一句配置：
> ```bash
> git config --global user.name "你的GitHub用户名"
> git config --global user.email "你的GitHub注册邮箱"
> ```

---

## 十三、习惯建议

1. **每个项目一个独立文件夹**，不要在父目录里 `git init`。
2. **`.gitignore` 一定要先建**，避免把垃圾文件、依赖、缓存传上去。
3. **提交信息写清楚**：`修复登录bug` 比 `update` 好，方便日后回溯。
4. **多设备协作时**，先 `git pull` 再改代码，改完再 `push`，减少冲突。
5. **别把密码、密钥、token 提交上去**，一旦推上 GitHub 很难彻底删除，等于泄露。

---

## 十四、一页速记卡

```
GitHub 建空仓库（三个勾选全不勾）→ 复制 HTTPS 地址
VS Code 打开项目 → git init
新建 .gitignore
git add . → git commit -m "initial commit"
git config --global user.name / user.email   ← 仅首次
git remote add origin <地址> → git remote -v 验证
git branch -M main
git push -u origin main
刷新仓库页面 或 git status 验证

日后更新：git add . → git commit -m "..." → git push
```

> 保存本手册，以后新建任何项目，从第一阶段照做到第八阶段，10 分钟内就能搞定上传。
