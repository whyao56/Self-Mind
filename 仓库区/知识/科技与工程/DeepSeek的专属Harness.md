---
title: DeepSeek的专属Harness
tags: [领域/科技与工程, 类型/知识卡片]
---

[DeepSeek自己的Harness终于来了？专属Harness为何重要?能有多大提升？_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1WXuz6kEyL/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=68074f1132646c64dff4aca26e69ae02)

DeepSeek终于要做自己的Agent了——Harness。

放着现成的Agent框架不用，为什么非要自己写一套？

**核心逻辑就三条：**

**第一，兼容性灾难。** 每家模型的API规则都不一样，第三方框架为了兼容只能取最小公约数，最后模型满身技能，框架里能用上的只有最基础那点。跨家组合更是到处都是坑。

**第二，开箱即用。** 普通用户根本不知道什么是API Key、什么是请求地址。只有官方自己下场做，才能做到装完即用、零配置。AI普及阶段，这个体验差距是决定性的。

**第三，正向循环。** Harness用得越好，产出的真实任务轨迹越多，拿回去训练模型，模型就越强。模型越强，Harness就越聪明。模型侧万事俱备，就缺这个真实入口。这是一块关键拼图。

以后大模型厂商的竞争，不会只停留在谁的模型更强。**模型加上自己的Agent，合在一起才是完整的战斗力。**

Tags: #DeepSeek #Harness #Agent #正向循环 #AI