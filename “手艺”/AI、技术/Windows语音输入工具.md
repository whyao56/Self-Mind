[有时候，动嘴比动手更快_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1tW4y1A7eA/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

一个Windows语音输入工具——CapsWriter-Offline。B站UP主淳帅二代开发，开源免费，完全离线，按住大写锁定说话，松手自动识别成文字，自动加标点。

地址：[HaujetZhao/CapsWriter-Offline: PC 端语音输入工具，离线识别，高准确率、低延迟，支持热词、LLM润色。按住CapsLock或鼠标侧键X2说话，松开自动上屏。](https://github.com/HaujetZhao/CapsWriter-Offline)

---
**自定义优化识别结果**

软件目录里有三个文本文件用于优化识别：

**hot-en**：英文专有名词。比如“Potplayer”被识别成“pot player”，在hot-en里添加后就能正确识别。

**hot-zh**：中文专有名词，同样添加进去就行。

**hot-rule**：查找替换。比如“120赫兹”想变成“120Hz”，写入“赫兹=HZ”即可。

这三个文件修改保存后实时刷新，不需要重启。化学式、表情包、回复内容都可以用这种方式快速输入。

---
**配置调整**

用文本编辑器打开`config.py`，注释很详细。`save_audio`的`true`改`false`就能关闭自动保存音频文件。

---
**其他功能**

把音频/视频文件拖到`client.exe`上，可生成字幕文件（.srt），识别速度和准确率都不错。

---
**系统要求**

Windows 10 64位或更高，安装对应运行库。下载`CapsWriter-Offline.zip`和`models.zip`，把models文件夹放到CapsWriter-Offline文件夹里。支持Linux和macOS但稍麻烦。

Windows自带语音输入（Win+H）需要联网，不能自动加标点，也不能自定义优化——不如这个好用。

Tags: #CapsWriter-Offline #语音输入 #离线 #开源 #字幕生成 #效率工具 