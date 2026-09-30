[别再花冤枉钱了！Claude Code 接入 DeepSeek V4 完整教程（1%成本平替方案）_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1nL5L6EEq4/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

**关于用 DeepSeek V4 替代 Claude Code 降低编程成本的分析**

用 Claude Code 写项目，每次绘画可能花 6 美元，一天十几二十刀就没了。用同样的 Claude Code 框架换一个模型，成本直接降到原来的 1/10 甚至 1%。

**DeepSeek V4 是什么**

1.6 万亿参数，100 万上下文窗口，MIT 开源协议，跟 Claude Code 生态完全兼容。工具调用能力是同类开源模型里最强的，能稳定执行 Claude Code 的所有 skill、工具调用及自动化任务。类比：Claude 是请顶尖设计师，贵但品味好；DeepSeek V4 是请一整个工程队，便宜快能搬砖。

**CC switch**

开源免费桌面工具，跨平台 GUI 应用，用 Tauri + Rust 开发，专门管理 Claude Code 的模型供应商。不用手写配置、不用克隆仓、不用配代理服务器，装好后点一下就能在不同 AI 模型间切换。还支持 Codex 和 Gemini。

**安装与配置流程**

1. 去 GitHub release 页面下载对应平台安装包（Windows 用 MSI，macOS 用 DMG，Linux 用 DEB，macOS 也可用 Homebrew）。
2. 去 DeepSeek 开发平台创建 API Key。
3. 在 CC switch 新建供应商，选 DeepSeek 类型，粘贴 API Key，保存。
4. 终端正常输入 `claude` 启动 Claude Code，背后模型已切换到 DeepSeek V4。输入“确认你正在使用什么模型”验证。
5. 想切回 Claude 原版，在 CC switch 里切换供应商，重新打开 Claude Code，不需要重新配置环境变量。

CC switch 还能管理 MCP 服务器、一键安装社区 skills、查看 API 用量统计。

**实操分工模式**

建一个咖啡品牌网站：

**第一阶段：Claude Code 做设计**。在 CC switch 切换到 Claude 原版，给它一个设计参考仓库（Awesome designer，有宝马、苹果等品牌设计系统），让它用 Apple 设计风格构建整个网站框架。Claude 做出来干净有质感，视觉和创意方面没有对手。

**第二阶段：DeepSeek 做功能**。基础页面有了，增加一个 ROI 计算器。用户输入每天喝几杯咖啡、每小时工资、工作时长、咖啡因敏感度、睡眠时间，自动算出咖啡对生产力的年化 ROI。这不需要设计品味，纯粹是逻辑和代码量。在 CC switch 切换到 DeepSeek V4，贴同样的项目上下文，让它继续。速度非常快，因为不需要从零设计，只需在已有框架里做功能开发，准确率出乎意料地高，计算器逻辑完全正确，UI 完美复刻 Apple 风格。

**判断框架**

**适合用 DeepSeek**：自动化脚本、后端逻辑、单元测试、算法题目、数据处理、批量文件操作、代码审查和审计——一切不需要视觉品味的脏活累活。

**不建议用 DeepSeek**：UI/UX 设计（审美跟 Claude 顶配模型有差距）；除非先用 Claude 打好框架，否则不要用 DeepSeek 从零做视觉创意。

**安全原则**：绝对不要把裸着的 API Key 和未脱敏的公司代码粘贴到 DeepSeek。

**用 OpenRouter 白嫖免费模型**

1. 谷歌搜 OpenRouter，进官网注册账号。
2. 登录后弹窗调研，按实际选择（如选 YouTube）。
3. 提示创建 API Key，点主页蓝色按钮创建，name 填 test，其余默认，create。
4. 复制 API Key 保存。
5. 打开 CC switch，点加号添加新供应商，选 OpenRouter，填 API Key，点“获取模型列表”。
6. 选带后缀 `free` 的模型（如 Gemini 4 26B、Gemini 4 31B 带 FREE），点击添加。
7. 找到 test 选择启用，重新打开 Claude Code，模型已变成谷歌 Gemini 4 31B。

**优缺点**：免费但 token 速度慢，通常 20-30 token/秒就算不错，高峰时段更低。适合对时间敏感度不高的任务。

**总结**

DeepSeek V4 大幅降低 Claude Code 使用成本，从每次绘画几美元降到几分钱。CC switch 一键切换模型，Claude 原版做设计，DeepSeek 做脏活累活，一个终端无缝切换。知道什么时候该用哪个模型，比盲目追求便宜或最好更重要。Claude 是设计师，DeepSeek 是实施工程队，官方和第三方模型配合使用才是真正省钱又高效。OpenRouter 免费模型可进一步降低成本甚至完全免费。

Tags: #ClaudeCode #DeepSeekV4 #CCswitch #OpenRouter #多模型配合 #成本优化 #AI编程 
