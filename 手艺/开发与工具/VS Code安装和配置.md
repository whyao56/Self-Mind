[vscode使用教程【2026最新】vscode安装教程vscode配置c/c++教程vscode怎么设置中文_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1tyAtetEd1/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

1. 点击官网：[Visual Studio Code - The open source AI code editor | Your home for multi-agent development](https://code.visualstudio.com/)
2. 点击下载：![[图片、附件/Pasted image 20260913173650.png]]
3. 安装注意：
	1. **不要**下载到C盘（系统盘）
	2. 附加任务：建议全部勾选![[图片、附件/Pasted image 20260913173931.png]]
4. 配置中文插件：
	1. 点击扩展
	2. 搜索Chinese![[图片、附件/Pasted image 20260913174206.png]]
	3. 重启一下即可
5. 配置运行插件：VS code本质还是一个轻量级的编辑器，是不能够直接运行代码的。所以要想写资源的代码的话，还需要一些额外的配置。
	1. 点击官网：[MinGW-w64 - for 32 and 64 bit Windows - Browse Files at SourceForge.net](https://sourceforge.net/projects/mingw-w64/files/)
	2. 点击Toolchains targetting Win64![[图片、附件/Pasted image 20260913175559.png]]
	3. 点击Personal Builds![[图片、附件/Pasted image 20260913175739.png]]
	4. 点击mingw-builds![[图片、附件/Pasted image 20260913175858.png]]
	5. 点击8.1.0![[图片、附件/Pasted image 20260913175941.png]]
	6. 点击threads-posix![[图片、附件/Pasted image 20260913180015.png]]
	7. 点击seh![[图片、附件/Pasted image 20260913180047.png]]
	8. 下载x86_64-8.1.0-release-posix-seh-rt_v6-rev0.7z![[图片、附件/Pasted image 20260913180120.png]]
	9. 解压
	10. 找到mingw64文件
	11. 找到bin文件![[图片、附件/Pasted image 20260913180511.png]]
	12. 复制路径：“你的磁盘”:\mingw64\bin
	13. 找到系统属性，打开环境变量![[图片、附件/Pasted image 20260913181211.png]]
	14. 找到系统变量的Path，点击编辑![[图片、附件/Pasted image 20260913181317.png]]
	15. 新建，复制D:\mingw64\bin![[图片、附件/Pasted image 20260913181457.png]]
	16. 点击确定
6. 配置C语言编译环境和其余教程：[链接][https://www.bilibili.com/video/BV1tyAtetEd1?t=350.1]

Tags: #VSCode #C语言 #MinGW #环境配置 #编译调试 #教程