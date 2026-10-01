[Windows跑AI Agent，WSL才是终极答案，别羡慕Mac了， WSL保姆级全攻略，海量实战教程，一期视频精通_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1pYNm69EPm/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

**关于在 Windows 上用 WSL 运行 AI Agent 的完整攻略**

**为什么 WSL 对 AI Agent 更友好**

AI Agent 在 Windows 上表现不如 macOS，主要原因是 PowerShell 对 AI 不够友好。WSL（Windows Subsystem for Linux）只需一行命令就能在 Windows 上运行 Linux 子系统。三大好处：

1. **运行更稳、效率更高**：AI 大模型训练语料里的命令行操作大部分是 Linux/macOS 风格，在 Linux 环境里出错概率明显更低。PowerShell 命令频繁报错，不仅执行慢，还浪费 token。
2. **跟生产环境更一致**：AI 写的代码最终大概率部署到 Linux 服务器，一开始就在 WSL 里编写测试，后续部署环境差异更小。
3. **环境隔离更安全**：WSL 提供 Linux 虚拟机与 Windows 宿主机之间的隔离，Agent 误操作搞坏环境通常不影响 Windows 主系统，最坏删除 WSL 实例重建即可。

**一、安装 WSL**

前提：开启 CPU 虚拟化。任务管理器 → 性能 → CPU，显示“虚拟化：已启用”即可。未启用则进 BIOS 开启 Intel VMX 或 AMD SVM。

安装命令：

```
wsl --install
```

国内网络建议加 `--web-download` 提高下载速度。提示重启就先重启，重启后重新执行命令。

WSL 默认安装 Ubuntu（最流行的 Linux 发行版）。所谓发行版就是不同团队基于 Linux 内核打造的不同操作系统版本，类似安卓厂商基于安卓系统定制封装。

安装过程需填写 Linux 虚拟机用户名和密码（输入密码时屏幕不显示，实际已输入）。命令行颜色变了就进入 Linux 子系统，`exit` 退出。

**二、WSL 基础使用**

**列出可安装的发行版**：

```
wsl -l -o
```

**安装其他发行版**（如 Kali Linux）：

```
wsl --install kali-linux
```

**指定安装目录**（不想装 C 盘）：

```
wsl --install kali-linux --location D:\文件夹
```

**列出已安装的虚拟机**：

```
wsl -l
```

**同一发行版安装多个实例**：

```
wsl --install Ubuntu --name Ubuntu2
```

每个实例有独立文件系统和配置，互相隔离。

**升级 WSL 本体**：

```
wsl --update
```

**启动方式**：
- `wsl`：启动默认虚拟机
- `wsl -d kali-linux`：指定启动某个虚拟机
- `wsl --set-default kali-linux`：设置默认实例
- PowerShell 下拉窗口可直接选择 Linux 实例启动

关闭虚拟机：关掉 WSL 命令行窗口，对应 Linux 虚拟机自动关机。

**三、配置开发环境**

先安装开发三件套：git、Node.js、Python。

Ubuntu 自带 git（`git -v` 检查）。Python 自带 python3（`python3 --version`），但 `python` 命令未安装，需配置：

```
sudo apt update
sudo apt install python-is-python3
```

Node.js 未安装，去官网选 Linux + NVM 方式安装。

**四、安装 AI Agent**

**Pi（极简 code agent）**：安装命令复制后到 WSL 执行，输入 Y。`cd ~` 进主目录，`mkdir pi-test` 创建文件夹，进入后输入 `pi` 启动。`/login` 配置模型（选 API Key），支持 DeepSeek、Kimi 等。测试：用 Next.js 写坦克大战游戏，完成后用 Windows 浏览器访问提示的地址即可游玩。

**知识点**：WSL 里运行的服务用的是 Linux 虚拟机 IP 地址，Windows 的 localhost 指向宿主机 IP。理论上宿主机敲 localhost 不应访问到 WSL 服务，但 WSL 有**端口自动转发**功能——检测到 Linux 里有程序监听端口，自动转发到 Windows 宿主机 localhost 相同端口。

**五、在 VS Code 中修改调试**

确保 Windows 装了 VS Code。在 WSL 工作目录输入 `code .`，用 Windows 的 VS Code 打开当前目录。可直接查看修改源代码，浏览器同步改动。可在 VS Code 里做 git 操作（Source Control → Manage Trust → Initialize Repository → 填 commit message → Publish 上传 GitHub）。

也可让 AI 完成 git 操作：让 AI 读 Windows 宿主机的 git 设置并在 WSL 里配置，然后让 AI 修改标题并 commit、push。

**六、文件互访**

**Windows 访问 Linux 文件**：资源管理器左下角企鹅图标 → Ubuntu → 展示 Linux 子系统文件夹目录。或 WSL 里输入 `explorer.exe .` 用 Windows 资源管理器打开当前目录。

**Linux 访问 Windows 文件**：`df -h` 查看磁盘，C 盘 D 盘以挂载卷形式出现在 `/mnt/c`、`/mnt/d`。`cd /mnt/c` 进 C 盘，`ls` 列出内容。

**注意**：WSL 里开发项目，项目文件夹尽量放 Linux 原生目录，不要放 Windows 目录，跨系统读文件有额外 IO 开销。

**发送图片给 AI**：浏览器截图保存到桌面，直接拖拽进 WSL 窗口，图片以挂载卷目录形式显示，AI 可正确看到。

**七、安装 Hermes Agent、Claude Code、Codex**

**Hermes Agent**：安装方式选 Linux，复制命令到 WSL，输入 Y，输入 Linux 虚拟机密码，选完全设置，选模型厂商（如 DeepSeek），输入 API Key，选模型，选即时通信渠道（最简单的选第三个），配对完成后重启 WSL，输入 `hermes` 启动。

**Claude Code**：复制安装命令到 WSL，输入 `claude` 启动，用官方订阅，浏览器打开地址复制授权码粘贴回车。

**Codex**：推荐在 WSL 里运行 Codex CLI，复制 Linux 安装命令到 WSL，重启后输入 `codex` 启动，用 ChatGPT 登录。

如果习惯用 Codex APP，可在设置 → 常规 → 智能体环境切换为 WSL，终端也切 WSL，重启。但这种方式只能用 Windows 文件夹作为项目文件夹并挂载进 WSL，IO 效率低，更推荐直接用 Codex CLI。

**八、Docker**

WSL 最新发行版默认启用 systemd，运行 Docker 体验跟真正 Linux 电脑一致。去 Docker 官方部署指南，执行第一个和第四个命令，输入密码等待20秒。安装完成后启动 Redis：

```
sudo docker run -d -p 6379:6379 redis
```

Windows 的 Redis 客户端连 localhost:6379 即可。关闭 WSL 窗口 Docker 停止，重启 WSL 后 `sudo docker ps -a` 查看容器，`sudo docker start 容器ID` 重启。

**九、WSL1 vs WSL2**

WSL1 本质是翻译层，把 Linux 指令翻译成 Windows NT 内核能理解的指令，不运行真正 Linux 内核，有兼容性问题（无法运行 Docker），维护工作量大。

WSL2 基于 Hyper-V 虚拟化平台，有真正 Linux 内核，可与 Windows 在用户空间网络通信、文件共享。可运行 Docker，自带显卡直通，无需配置。

**十、显卡直通与本地部署模型**

WSL 里直接调用 Windows 宿主机显卡，无需配置。输入 `nvidia-smi` 查看 GPU 情况（驱动版本、CUDA 版本、显卡型号、显存）。

**不要往 Linux 系统里装任何驱动**，直接用 Windows 宿主机显卡驱动。

vLLM 是目前炙手可热的 AI 推理框架，官方文档全部基于 Linux，用 WSL 就是一等公民。安装 UV 后按文档执行命令，启动推理框架（如千问3.5），用 Postman 填推理端点测试。

**十一、图形界面**

**WSLG**：把 Linux 图形应用直接显示到 Windows 桌面。如安装 GIMP（类似 Photoshop 的开源图像编辑软件），`sudo apt install gimp` 后运行，Windows 界面打开。

**完整桌面**：Kali Linux 装 KEX 后输入 `kex` 启动桌面。Ubuntu 需依次执行命令，最后显示 IP 地址，Windows 搜索“远程桌面连接”，输入 IP:3389 连接。

**十二、网络模式**

WSL 默认用 NAT 网络模式，Linux 子系统有独立虚拟 IP，通过 localhost 端口转发在宿主机访问。

**虚拟机访问宿主机**：PowerShell 输入 `ipconfig` 找到宿主机局域网 IP，WSL 里用这个 IP 访问宿主机服务。

**局域网其他设备访问 WSL**：默认无法访问。修改 WSL 网络设置——C 盘用户目录新建 `.wslconfig` 文件，添加：

```
[wsl2]
networkingMode=mirrored
```

关闭所有 WSL 窗口等待一分钟重启。镜像模式下 Windows 网卡直接镜像给 WSL，两者处于相同网络环境，使用相同局域网 IP，其他设备可访问。镜像模式也让网络结构更简单，遇到奇怪网络问题可试试切换。

**十三、配置文件**

**`.wslconfig`**（Windows 文件，全局通用，对所有 WSL 虚拟机生效）：位于 C 盘用户目录，可修改内存、内核启动方式、网络模式等。

**`wsl.conf`**（Linux 文件，只对单个虚拟机生效）：位于 `/etc/wsl.conf`，可修改挂载卷、systemd、默认用户等。如关闭自动挂载（`[automount] enabled=false`），虚拟机里不再自动挂载 C 盘 D 盘，AI 操作时无法看到 Windows 文件，提高安全性。保存后关闭虚拟机等待8秒重启，`df -h` 确认挂载卷里没有 Windows 目录。

**十四、备份与克隆**

**导出**：

```
wsl --export Ubuntu ubuntu.tar
```

**导入**：

```
wsl --import Ubuntu D:\目录 ubuntu.tar
```

可用导入导出把虚拟机迁移到其他 Windows 电脑，也可克隆多份（导入时改名字和路径）。

**十五、命令行互通**

Windows 里可调用 Linux 命令。如 PowerShell 里 `Get-ChildItem | wsl grep video`——前半部分是 Windows 命令，后半部分是 Linux 命令，一样达成效果。

**Tags:** #WSL #Windows #Linux #AIagent #PowerShell #Docker #显卡直通 #vLLM #端口转发 #镜像网络 