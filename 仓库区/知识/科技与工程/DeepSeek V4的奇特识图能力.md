---
title: DeepSeek V4的奇特识图能力
tags: [领域/科技与工程, 类型/知识卡片]
---

[这……这也行? DeepSeek V4正式版奇特的“识图”能力_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1vnuA6ZEEt/?spm_id_from=333.1387.favlist.content.click&vd_source=68074f1132646c64dff4aca26e69ae02)

**关于 DeepSeek 用 ASCII 码“硬整”识图能力的分享**

DeepSeek V4 最近很火，官网的识图功能其实是外挂模型，本身模型不具备图像能力。

平时整理项目、翻译这类简单工作，用 DeepSeek 加 Claude Code 来做，效果不错，执行命令行也挺好。

今天下午有个新需求：有一个图标，想把安卓应用所有图标都配上，包括圆角、自适应方形、圆形等适配。任务交给 DeepSeek，它用 Claude Code，看了一眼图片发现自己看不了。然后做了一件很震惊的事——自己写了一个 Python 脚本，把图片读成 ASCII 码来看，尝试理解图标是什么。后期替换完成、自己验证的时候，也用 ASCII 码。

它没有识图能力，但没活硬整，硬给自己整出了一个识图能力。看到日志的时候很难描述那种心情，感觉挺好笑的，也挺震惊。

Tags: #DeepSeek #ClaudeCode #识图 #ASCII #安卓图标 #AI 