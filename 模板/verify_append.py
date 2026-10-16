# -*- coding: utf-8 -*-
"""追加块保真校验 —— 每批必跑。

用法：
    python verify_append.py <原文件> <写入后的文件>

比对三项，任一项出现丢失即视为失败（退出码 1）：
    ① 内联 Tags 行里的标签种类
    ② BV 号
    ③ 图片引用（文件名）

另外自查两项规范性：元叙述 0 处、层级前缀 0 处。

设计原则：只做比对，不修改任何文件。
"""
import re
import sys

# ── 笔记里"不许出现"的写法 ────────────────────────────────
BANNED = [
    (r"这条笔记|本记录|为将来|以备查阅|给将来的我|失忆", "元叙述"),
    (r"#(内容|精神|内核|本质)/", "层级前缀"),
]


def load(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def tags_of(txt):
    """取内联 Tags 行里的标签（不含 frontmatter 的 tags 数组）。

    注意：库里有笔记把 Tags 行折成多行（例如
        Tags: #a #b #c
        #d #e
    ），所以要吃续行。续行的判定是「以 # 开头且不是 markdown 标题」。
    """
    out = []
    lines = txt.split("\n")
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if re.match(r"^Tags[:：]", s):
            seg = [s]
            j = i + 1
            while j < len(lines) and re.match(r"^#[^\s#]", lines[j].strip()):
                seg.append(lines[j].strip())
                j += 1
            for line in seg:
                out += re.findall(r"#[^\s#]+", line)
            i = j
        else:
            i += 1
    return {t.rstrip("，。、）),；;") for t in out if t.strip("#")}


def bvs_of(txt):
    return set(re.findall(r"BV[A-Za-z0-9]+", txt))


def imgs_of(txt):
    """图片引用：取 ![[任意路径/文件名]] 里的文件名部分。"""
    return set(re.findall(r"!\[\[[^\]]*?([^/\]]+?)(?:\|[^\]]*)?\]\]", txt))


def main():
    if len(sys.argv) < 3:
        print("用法: python verify_append.py <原文件> <写入后的文件>")
        return 2

    src, dst = sys.argv[1], sys.argv[2]
    a, b = load(src), load(dst)

    failed = 0
    for label, fn in (("标签", tags_of), ("BV 号", bvs_of), ("图片引用", imgs_of)):
        sa, sb = fn(a), fn(b)
        miss = sorted(sa - sb)
        status = "OK" if not miss else "丢失 %d" % len(miss)
        print("%-6s 原 %3d → 新 %3d   %s" % (label, len(sa), len(sb), status))
        for m in miss:
            print("        ✗ %s" % m)
        failed += len(miss)

    print()
    for pat, desc in BANNED:
        hits = re.findall(pat, b)
        print("%-8s %d 处" % (desc, len(hits)))
        failed += len(hits)

    print()
    if failed:
        print("结果：不通过（%d 项问题），请修正后重跑。" % failed)
        return 1
    print("结果：通过 —— 内容零丢失、写法合规。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
