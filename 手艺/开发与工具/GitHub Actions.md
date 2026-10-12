[Github的王炸功能，但很少人知道怎么用？免费运行程序，流水线编译部署，天气推送 签到薅羊毛 领京豆 CI/CD持续集成持续部署_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV11e411i7Xx/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

**关于 GitHub Actions 使用的分析**

每当我们打开 GitHub 项目，都会看到一个标签 Actions，很少人点进去看，也很少人知道这个功能做什么用。这是 GitHub 的王炸功能——借用 GitHub 提供的各种类型虚拟器，流水线式地完成程序的编译、测试、打包、部署。完全免费，每个账户每月可白嫖 2000 分钟使用时长。有了这些免费时长，甚至可以不购买服务器，用 Actions 执行定时小任务，如定时天气推送、签到、薅羊毛等。

**打开方式**：GitHub 打不开可下载 Watt Toolkit（原 Steam++），用里面的 GitHub 加速功能。微软商店可下载。

**样例一：编译打包（Actions 最主要的使用场景）**

用 Python 画爱心的程序，如何打包编译成 macOS、Ubuntu、Windows 上的可执行程序？不想每个系统都搭一遍 Python 环境再编译，就可以用 Actions。

操作：点击 fork 将项目保存到自己名下，点击 Actions，看到样例。点开“画爱心的 windows 版本”，右侧点“立即执行”，刷新页面看到 Actions 正在执行，有详细步骤。完成后亮绿灯，往下找 Artifacts 保存了执行结果，`love-heart` 就是编译结束的可执行文件，下载运行。

**Action 脚本配置项**：
- 名字：动作的名字
- `on`：触发条件。`workflow_dispatch` 指可手动触发，也可定时触发或有代码提交时触发
- `job`：任务，一个 workflow 可由多个 job 构成
- `runs-on`：申请虚拟机来执行任务，如最新版 Windows 虚拟机
- `step`：步骤。使用 `uses` 直接把别人写好的脚本拿过来用，`with` 传递参数（Python 版本 3.12、打包文件 love-heart、可执行文件名、打包成单文件、窗口化运行）

**编译 Ubuntu 版本**：跟 Windows 版本只有一点区别——申请 Ubuntu 系统虚拟机，其他配置一样。macOS 版本同理。

**样例二：天气推送**

申请微信测试版公众号，用 GitHub Action 每天早晨定时执行。这样不需要服务器、不用花钱，每天早晨收到微信天气推送。

配置：进入 Settings → Secrets and Variables → Actions → Repository Secrets，配置敏感数据（如 APPID、APP Secret、OpenID、Template ID）。

定时执行：Actions 里看天气预报推送文件，`on` 里定义了定时触发，用 cron 表达式（UTC 时间），晚 23 点对应北京时间早 7 点，每天早晨 7 点推送天气信息。申请 Ubuntu 虚拟机，step 里配置 Python 环境（3.12）、安装依赖（升级 pip，pip install requirements.txt）、执行 Python 脚本。`env` 把配置的环境变量从 GitHub 传递到代码里。Python 用 `os.environ.get` 接收环境变量。

手动执行测试：run workflow，执行完手机收到消息推送。

**样例三：签到薅羊毛（京东为例）**

Action 配置跟天气推送几乎一样：定义执行时间、申请 Ubuntu 虚拟机、设置 Python 环境、安装依赖、执行脚本。唯一不同是环境变量是一个京东 cookie。

获取 cookie：进入京东主页，F12，切换仿真设备为手机版，刷新页面，选择 Network，找 `m.jd.com` 的标头，往下找到 cookie，复制。进入 Settings → Secrets and Variables → Actions → New Repository Secret，加京东 cookie。这样每天早晨 8 点定时京东签到，获取京豆。

**Actions 市场**

进入 GitHub Marketplace，选择 Actions 选项卡，有很多别人写好的 GitHub Action 脚本可直接用。如：
- Python 自动编译成可执行文件（视频用的这个）
- 自动编译成 Docker 镜像
- 对项目自动进行安全检查
- 将项目自动编译发布到云服务器

一切可以想到的对程序的自动化行为几乎都能找到。

Tags: #GitHubActions #自动化 #编译打包 #天气推送 #签到 #薅羊毛 #Marketplace #教程 