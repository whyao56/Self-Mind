[windows为什么有两个命令行工具？命令提示符与PowerShell有什么区别？_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1Nx4y147n3/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

**关于 Windows CMD 与 PowerShell 区别的分析**

Windows 有两个命令行工具：CMD（命令提示符）和 PowerShell。

**官方定位**：CMD 是最早内置于 Windows 的 shell，用于执行 Windows 命令和批处理文件。PowerShell 的设计目的是扩展 CMD 功能，可以运行称为 cmdlet（command-let）的命令。cmdlet 类似 Windows 命令，但提供更多可扩展的脚本语言功能。可以在 PowerShell 中运行 Windows 命令和 PowerShell 专属 cmdlet，但 CMD 只能运行 Windows 命令。

**本质区别**

CMD 是老旧的 DOS 操作系统继承下来的产物，功能十分有限——输入命令，Windows 执行命令，仅此而已。PowerShell 除了能执行普通 Windows 命令，还是一个完整的脚本语言运行环境。

对比：在 CMD 输入 `1+1` 回车，完全报错，因为不是 Windows 命令。在 PowerShell 中输入 `1+1`，输出 2。PowerShell 中可以定义变量、对变量进行运算，很像高级编程语言的命令行交互环境（如 Python）。

**cmdlet**

cmdlet 是专门在 PowerShell 中使用的命令，由 .NET 库编写，命名规范是**动词-名词**格式，如 `Get-Process`（获取当前进程）、`Set-Location`（切换目录）。

Windows 已有 `CD` 命令，为什么还要发明 `Set-Location`？因为 PowerShell 的 `Set-Location` 不仅能更改文件目录，还能更改注册表目录、证书存储目录等，比传统 CMD 的 `CD` 更强大。

传统 Windows 命令返回纯文本输出，解析处理困难。cmdlet 返回的是 .NET 对象，允许更复杂精确的数据操作，对象模型使数据在管道中传递时保留其结构。

**别名机制**

为让 PowerShell 完全兼容旧版 CMD 命令，微软发明了 alias（别名）。旧版 CMD 命令在 PowerShell 中都通过别名链接到 cmdlet。如 PowerShell 中 `CD` 就是 `Set-Location` 的别名，二者完全等价。

注意：CMD 中的 `CD` 与 PowerShell 中的 `CD` 虽然长得一样、功能类似，但底层实现已有区别——前者是简单 Windows 命令，后者是用 .NET 库编写的 cmdlet。

用 `Get-Alias` 可查看所有别名关系。别名表中不全是旧 CMD 命令，还吸纳了一些 Linux 命令，如 `LS`（Linux 命令，CMD 中报错，PowerShell 中显示当前目录文件结构，与 `Get-ChildItem` 是别名关系）。Linux 用户学习 PowerShell 成本更低。`Get-Command` 可查看别名对应关系。

**管道符**

竖线 `|` 是管道符，把上个命令的输出结果作为下个命令的输入，像拼接管道一样把命令拼接成流水线。cmdlet 返回 .NET 对象，可以很方便地用管道符拼接。

例子：
- 获取前 5 个 CPU 占用率最高的进程：`Get-Process` → 管道 → 排序（按 CPU 占用时间）→ 管道 → 筛选前五个
- 计算 Windows 目录下所有 EXE 可执行文件大小：`Get-ChildItem` 列出 C:\Windows 目录下所有文件 → 管道 → 求和
- 读取 CSV 文件筛选年龄大于 30 岁的用户，转换成 HTML 格式输出：`Import-Csv` → 管道 → 筛选 → 管道 → `ConvertTo-Html` → 管道 → `Out-File`

**脚本语言**

CMD 脚本扩展名 `.bat`，PowerShell 扩展名 `.ps1`。

`.bat` 文件非常难用，局限性多，语法老旧，甚至不允许 `if` 嵌套。如 `.bat` 脚本中两个条件只能用 `goto` 语句连接，代码被 `goto` 扯得支离破碎，不符合人类阅读习惯，编码和调试都很痛苦。

`.ps1` 更像现代版编程语言，可以用括号和嵌套 `if` 表示代码层级，代码行数砍半。编写复杂 Windows 批处理程序建议直接用 PowerShell。

**PowerShell 独有功能**

- `Get-Command`：获取所有 PowerShell 支持的命令
- `Update-Help`：更新帮助文档
- `Get-Help` 后接命令类型：查看单个命令帮助文档

**与 Linux 相同的命令**

PowerShell 巧妙运用别名机制，兼容了一部分 Linux 命令：
- `PWD`：输出当前工作目录（`Get-Location` 的别名）
- `LS`：列出当前目录文件
- `Clear`：清屏
- `CAT`：查看文件内容
- `MKDIR`：新建文件夹
- `MV`：移动文件
- `CP`：复制文件
- `RM`：删除文件

这些命令与 Linux 几乎一模一样，非常容易学习。

**输出命令**

- `Export-Csv`：输出到 CSV 格式。如 `PS | Export-Csv` 把所有进程输出到 CSV 文件
- `ConvertTo-Html`：输出 HTML 格式，生成网页可用 Chrome 打开

**总结**

PowerShell 不仅能执行普通 Windows 命令，还是完整的脚本语言运行环境，是 CMD 的上位替代。CMD 用户可以无缝过渡，Linux 用户也能丝滑学习使用。

Tags: #CMD #PowerShell #命令行 #cmdlet #别名 #管道符 #脚本语言 #Windows 