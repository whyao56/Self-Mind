# B 站首页"滚动后导航变样"源码分析

> 实测环境：Chrome 154 headless + CDP，viewport 1440×900，2026-10-13。
> 目标：用 Elements 的思路对比 www.bilibili.com 首页滚动前后 nav 的变化，并找到对应源码。

## 一、Elements 里怎么对比

打开 DevTools → Elements，选中顶栏根节点 `<div class="bili-header ...">`，滚一下页面（DevTools 的 DOM 树会实时高亮变化），或者直接在 Console 跑：

```js
document.querySelector('.bili-header').className
```

## 二、滚动前后实测 diff

### 1. 根节点：多了一个类

```html
<!-- 滚动前 -->
<div class="bili-header bili-header--large">

<!-- 滚动后 -->
<div class="bili-header bili-header--large bili-header--slide-down">
```

**多了 `bili-header--slide-down` 这一个类**，其余类不变、无内联 style 变化。

### 2. `.bili-header__bar`（实际类名 `bili-header__menu is-zh bili-header__bar`）：position 变了

| 计算样式 | 滚动前 | 滚动后 |
|---|---|---|
| position | `absolute` | `fixed` |
| box-shadow | 无 | `0 2px 4px rgba(0,0,0,.08)` |
| 背景 | 透明 | `var(--bg1_float)`（白色） |
| top | 0 | 0 |

### 3. 频道栏 `.header-channel`：不是新建节点，是 display 切换

容易误判成"滚动后多出一块 DOM"。实测滚动前它**已经在 DOM 里**：

```html
<!-- 滚动前 -->
<div class="header-channel" style="display: none;">…</div>

<!-- 滚动后（第二行：动态/热门/番剧/国创/综艺…） -->
<div class="header-channel" style="">…</div>
```

即 Vue 的 `v-show` 式切换（内联 `display:none` ↔ `display:flex`），节点本身一直存在。

## 三、CSS 源码（命中这些变化的规则）

文件：`https://s1.hdslb.com/bfs/static/shanks/laputa-home/assets/index-3f345f9f.css`

```css
/* 默认：跟随文档流，压在大 banner 上 */
.bili-header .bili-header__bar {
  position: absolute; top: 0; z-index: 1002; width: 100%; height: 64px;
}

/* 滚动后：根类切换触发，整条变白色悬浮 */
.bili-header.bili-header--slide-down .bili-header__bar {
  position: fixed; top: 0;
  animation: biliHeaderSlideDown .3s linear forwards;
  background: var(--bg1_float);
  box-shadow: 0 2px 4px rgba(0,0,0,.08);
}
@keyframes biliHeaderSlideDown { 0% { opacity: 0 } to { opacity: 1 } }

/* 第二行频道栏：本身就是 fixed，只是被 display 控制 */
.header-channel {
  width: 100%; min-width: 1100px; max-width: 2560px;
  display: flex; justify-content: center; z-index: 1001;
  position: fixed; top: 63px;
  background: var(--bg1_float);
  box-shadow: 0 2px 4px rgba(0,0,0,.08);
  animation: fixedTopBarSlideDown .2s linear forwards;
}
```

## 四、JS 源码（谁在切这个类）

文件：`https://s1.hdslb.com/bfs/static/shanks/laputa-home/assets/index-558ee822.js`
（B 站首页是 Vue 3 应用，项目代号 laputa；以下是压缩代码还原后的可读版。）

**1) 滚动监听：scroll + 节流 200ms + 阈值 32px → 翻转一个 ref**

```js
// props
triggerHeight: { type: Number, default: 32 },

// setup 内
const isSlideDown = ref(false)

const bindSticky = () => {
  if (props.disableSticky) return
  const el = document.scrollingElement || document.documentElement
  const onScroll = throttle(() => {           // throttle(fn, 200, leading, trailing)
    if (el.scrollTop >  props.triggerHeight) isSlideDown.value = true
    if (el.scrollTop <= props.triggerHeight) isSlideDown.value = false
  }, 200, true, true)
  window.addEventListener('scroll', onScroll)
}
onMounted(() => bindSticky())
```

压缩前的原文（保留了变量名结构）：

```js
const o = x(!1), s = () => {
  if (e.disableSticky) return;
  const L = document.scrollingElement || document.documentElement,
        N = oo(() => {
          L.scrollTop > e.triggerHeight && (o.value = !0),
          L.scrollTop <= e.triggerHeight && (o.value = !1)
        }, 200, !0, !0);
  window.addEventListener("scroll", N)
};
```

**2) 渲染层：class 绑定消费这个 ref**

```js
I("div", {
  ref: "headerRef",
  class: Be(["bili-header", {
    "bili-header--large":      e.headerType === "large",
    "bili-header--mini":       e.headerType === "mini" && e.background !== "transparent",
    "bili-header--fixed":      !e.disableSticky && e.headerType === "mini",
    "bili-header--transparent": e.background === "transparent",
    "bili-header--slide-down": e.isSlideDown && !(e.headerType === "mini" && e.background !== "transparent")
  }])
})
```

**3) 频道栏的显隐：不是 scroll 监听，是 IntersectionObserver + 哨兵元素**

```js
const v = () => {
  f = new IntersectionObserver((entries) => {
    const bar = document.querySelector('.bili-header__bar')
    const shimVisible = entries[0].intersectionRatio <= 0   // 哨兵滚出视口？
    emit('FIXED_BANNER_VISIBLE', shimVisible)
    if (shimVisible) showChannel.value = true
    else showChannel.value = false
  })
}
onMounted(() => f.observe(props.shimHtml.$el))   // 观察页面里的 .fixed-channel-shim
```

页面骨架里有个高度为 0 的哨兵 `<div class="fixed-channel-shim">`（放在 header 正下方，y=265 处）。它一滚出视口，说明"用户已经把头部滚走了"，频道栏随之显示——这比监听 scroll 更语义化，也不用算阈值。

## 五、机制总结

```
scroll 事件 ──节流200ms──> scrollTop > 32 ? ──> isSlideDown = true/false
                                                  │
                                          :class 绑定（Vue 响应式）
                                                  ▼
                       <div class="bili-header … bili-header--slide-down">
                                                  │ CSS 级联
                    position:absolute → fixed ＋ 白底 ＋ 阴影 ＋ 淡入动画

.fixed-channel-shim（高度0的哨兵）──IntersectionObserver──> .header-channel 的 v-show 切换
```

一句话：**JS 只负责"加/去一个类 + 切一个 v-show"，所有视觉变化（fixed、白底、阴影、动画）全部由一条带 `.bili-header--slide-down` 前缀的 CSS 规则完成**。这是"状态类 + CSS 级联"实现吸顶导航的标准范式。

## 六、复现要点（自己实现同款）

```css
.nav { position: absolute; transition: background .2s, box-shadow .2s; }
.page.scrolled .nav { position: fixed; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,.08); }
```

```js
let ticking = false
addEventListener('scroll', () => {
  if (ticking) return
  ticking = true
  requestAnimationFrame(() => {
    root.classList.toggle('scrolled', scrollY > 32)
    ticking = false
  })
}, { passive: true })
```

## 附件

- `shot_before.png`：滚动前（透明 header 压在 banner 上，频道栏隐藏）
- `shot_after_full.png`：滚动后（白色 fixed 导航 + 第二行频道栏）
- 产物文件：`index-558ee822.js`（JS）、`index-3f345f9f.css`（CSS）已在 probe 目录留档
