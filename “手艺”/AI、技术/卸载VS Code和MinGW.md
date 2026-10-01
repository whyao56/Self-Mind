[如何卸载VS Code和MinGW软件_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1YXtZzgE2r/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

**卸载MinGW：**
1. 系统属性 → 环境变量![[图片、附件/Pasted image 20260913182333.png]]
2. 分别选中用户变量和系统变量里的 Path
3. 点击编辑（**千万不要点删除**，删除 Path 会很麻烦）
4. 删除对应的 MinGW 变量（通常是 `你的磁盘:\mingw64\bin`）
5. 最后删除 MinGW 文件夹

**卸载VS Code：**
1. 控制面板 → 删除或更改程序
2. 找到 Microsoft Visual Studio Code，删除
3. 手动删除以下目录：
   - `C:\Users\用户名\.vscode`
   - `C:\Users\用户名\AppData\Roaming\Code`

Tags: #VSCode #MinGW #卸载 #环境变量 #教程