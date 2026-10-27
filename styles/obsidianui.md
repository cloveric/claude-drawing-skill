# 笔记应用界面（obsidianui）

- **实现**：`lib/obsidianui.py` · `ObsidianUI`
- **范例**：`examples/obsidianui_reading_notes.py` 小王子 · 读书笔记 · Reading Notes（讲解片里的一帧笔记应用：#161616 的近黑页面，左上一团淡紫光晕；窗口里是标签栏「小王子 · 狐狸」（当前标签底边打开，和笔记连成一片）、细长图标栏、文件列表（展开的「2026 读书」挂一条缩进线，「小王子」高亮）、面包屑「2026 读书 / 小王子」和右侧边栏；笔记里粗黑 H1「小王子」下一道带辉光的紫色短条，属性块「标签 #童话 #读书笔记」「读完 2026-10-12」，两行正文：紫色的内部链接「狐狸」「驯养」、行内代码「建立联系」、加粗的「彼此需要」；一个 mermaid 代码块逐行敲出（语法色、紫色块状光标跟着行尾走），指针点「源码 / 阅读」切到阅读视图，渲染成流程图「陌生 —花时间→ 驯养 → 彼此需要 → 独一无二」，「驯养」亮紫并加一圈外环；下面是紫色左边的引用标注「狐狸说」；右栏「局部关系图谱」：书里的人物和地点是灰点灰线，这篇笔记链接到的四篇（小王子、狐狸、玫瑰、驯养）亮成紫色光点、连线变紫，下面三条反向链接，右下角浮着状态栏；`--accent` 可换强调色；`--stages` 出 93 个阶段加成品，会动的东西拆成中间姿态）
- **耗时**：约 0.5 秒（加 `--stages` 约 5 秒）
- **内部构成**：笔记应用界面（近黑页面与淡紫光晕；距离场抗锯齿的应用窗口：标签页、图标栏、带缩进线的文件列表、面包屑、分段开关、浮动状态栏；CSS 式多层阴影与零偏移辉光；苹方 / 兰亭黑 Heavy / SF Pro / SF Mono 自动分段，带底色描边的标签字；一行正文的富文本（加粗、内部链接、行内代码、高亮、#标签）与属性行；带语法色的代码块、逐行图层和块状光标；引用标注、任务勾选框；阅读视图的扁平流程图节点与带标签的箭头连线；关系图谱的灰点灰线与紫色亮点径向光；鼠标指针与点击环；可换的单一强调色；带姿态的图层：位移、缩放、不透明度、横向 / 纵向 / 圆形揭开）

## 何时选用

讲解片里讲「笔记 / 知识库 / 双链 / Markdown / 代码块怎么变成图」的那一页，或任何要「在一个像真的深色应用窗口里演示一个操作」的画面：文件列表、标题和正文、代码块切到阅读视图渲染、关系图谱亮起来，一屏讲清一件事 → 笔记应用界面（要明亮的粉彩底和白色窗口卡片用粉彩界面；要点阵白板上的卡片和连线用白板卡片；要暖白纸面上的图表用 Flexoki 纸面；要磨砂玻璃和弥散渐变用弥散玻璃；要绿屏荧光字符用绿屏终端 CRT）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from obsidianui import ObsidianUI
```

- 思路：讲解片里的一帧笔记应用（默认深色主题）。近黑页面（#161616）上一两团淡紫光晕；窗口是一整套深灰（笔记区 #1e1e1e、边栏和标题栏 #202020、发丝分隔线 #363636），只有一个强调色（默认紫 #8a5cf5，浅色字用 #a88bfa）：H1 下的短条、#标签、内部链接、开关选中的那一段、亮起的流程图节点、关系图谱里被链接的笔记。所有圆角矩形、圆、环、线和线性图标都是有符号距离场，1 px 解析抗锯齿（像素中心取 i + 0.5，整数坐标的边是锐利的）；自由多边形（鼠标指针、箭头、菱形节点）4 倍超采样再 BOX 缩小。阴影按 CSS box-shadow 的语义算（偏移、模糊半径 σ = blur / 2、扩展、颜色、不透明度，只画在元素外面），偏移为 0 就是亮卡片和 H1 短条的紫色辉光；`halo()` 是柔和的径向光（图谱亮点）
- 图层：和粉彩界面一样，一切画进有名字的图层（预乘 RGBA，收尾时裁到画过的范围），`layer(name, z)` 开始往某层画（再次调用会重新打开），z 小的在后面，`end()` 之后画在页面上。每层有姿态 `pose(name, dx, dy, scale, alpha, reveal, mode, origin, feather)`：位移、绕 origin 缩放、不透明度、揭开（reveal 0–1，软边 feather px）——`mode='x'` 从左往右（敲字）、`'y'` 从上往下、`'r'` 从 origin 往外长成一个圆（关系图谱从当前笔记长出来）；`show / hide` 只改不透明度；`bounds(name)`。同一样东西的两种状态（源码 / 阅读的开关、灰 / 亮的图谱、普通 / 亮起的节点）画成两层，用 show / hide 切换。`stage(name)` 按当前姿态合成快照（PNG 压缩存在内存里）
- 构造：`ObsidianUI(W, H, seed, keep_stages=True, accent='violet'|'blue'|'teal'|'amber'|'rose'|(强调色, 浅色字))`；`page(colour, glows=[(cx, cy, rx, ry, alpha), …])` 页面和光晕（closest-side 的线性衰减，用强调色）
- 形状：`rrect(x0, y0, x1, y1, r, fill, alpha, ring, inset)`（ring=w 只画边）、`circle(cx, cy, r, fill, alpha, ring)`、`line(pts, width, fill, alpha, closed)`、`poly(pts, fill, alpha)`、`shadow(x0, y0, x1, y1, r, dx, dy, blur_px, spread, colour, alpha, shape=(cx, cy, r))`、`soft_shadow(cov, box, dx, dy, blur_px, colour, alpha)`（任意遮罩的 drop-shadow）、`halo(cx, cy, r, colour, alpha, power)`、`with clip(x0, y0, x1, y1, r):` 把里面画的东西裁进圆角矩形
- 文字：`text(s, x, y, size, fill, weight='regular'|'medium'|'semibold'|'bold'|'heavy', anchor, alpha, spacing, family='sans'|'mono', halo, halo_fill)`，返回宽度；中英文自动分段（macOS：中文苹方、H1 的 heavy 用兰亭黑 Heavy、西文 SF Pro 可变字重、代码 SF Mono；其他系统 Noto Sans CJK / 微软雅黑；可用 `INKPAINT_FONT_OBSIDIAN_<CJK|HEAVY|LATIN|MONO>` 指定）；anchor 的第二个字母 s 基线 / m 中文字身中线 / t 字身顶；`halo=px` 先描一圈 halo_fill 色的边（图谱标签：连线到字前就断开）；`measure(…)` 量宽度；`rich(x, base, runs, size, fill)` 排一行笔记正文：runs 是 `[(文字, 样式), …]`，样式 None 正文 / 'b' 加粗提亮 / 'link' 内部链接（强调色字）/ 'code' 行内代码（等宽红字压在圆角深色小底上）/ 'hl' 强调色高亮 / 'faint' / 'accent' / 'tag'，返回行尾 x
- 窗口：`window(x, y, w, h, tabs, active, side=300, right=0, bar=52, ribbon=52, radius=14, ribbon_icons, lit_icon)` 返回 Box（`.bar`、`.explorer`、`.note`、`.right`、`.tabs`）：阴影和 1 px 外圈、标题栏红黄绿三点、标签页（当前标签上圆角、底边打开，和笔记区连成一片；后面一个 +）、图标栏（底部帮助和设置）、文件列表栏（side 含图标栏，0 = 没有）和右侧边栏（right 宽，0 = 没有）的底色与分隔线；`explorer(win, items, active, size, row)` 文件列表：顶上一排小工具图标，items 是 `(名字, 层级, 'open'|'folder'|'file')`，展开的文件夹下挂一条缩进线，`active` 那行高亮；`view_header(win, crumbs)` 前进后退箭头、居中的面包屑（最后一节提亮）和右端更多；`toggle(x, y, w, h, labels=('源码', '阅读'), on)` 分段开关；`sidebar_tools(win, icons, lit)` 右栏顶上的小图标，返回下面的 y；`status_bar(win, items)` 窗口右下角浮着的状态栏
- 笔记：`h1(x, base, s, size, bar, bar_w, bar_gap, draw_text)`（粗黑标题 + 带辉光的紫色短条，bar=False / draw_text=False 只画一样，好分两层）；`heading(x, base, s, size, marker)` H2（marker=True 带灰色 ##）；`tag(x, cy, s, size)` #标签胶囊，返回右边缘；`prop(x, cy, glyph, key, key_w)` 属性行的图标和键名，返回值的起点；`code_block(x, y, w, lines, size, lang='mermaid', pad, lh, draw)` 深色代码块（1 px 边、圆角 10、右上角语言名），返回 Box，带 `.bases`（各行基线）、`.tx`、`.lh`，`draw=False` 只画框；`code_line(x, base, toks, size)` 一行代码，toks 是 `[(文字, 'kw'|'str'|'num'|'op'|'cm'|'fence'|'text' 或 '#rrggbb'), …]`，返回行尾 x；`caret(x, base, size)` 块状光标；`callout(x, y, w, title, lines, size, title_size, colour, glyph='quote')` 引用标注（16 % 底色、4 px 左边、图标和粗体标题，正文每行是 rich 的 runs），返回 Box；`checkbox(x, y, size, checked)` 任务勾选框
- 阅读视图里的图：`dnode(cx, cy, w, h, label, shape='rect'|'round'|'stadium'|'diamond', hi, size, focus)` 扁平深色节点（2 px 灰边、文字居中；hi 是强调色那一个，focus 再加一圈外环和辉光），返回 Box；`dedge(pts, width, colour, head, label, size, label_at)` 灰线加小实心三角箭头，可在 label_at 处放一个深色小标签（mermaid 的 `-->|标签|`）
- 关系图谱：`graph(nodes, links, lit, label_size, only='grey'|'lit', bg)`：nodes 是 `(x, y, r, 名字)`，links 是 `(i, j)`，lit 里的节点亮成强调色、带径向光，两端都亮的连线才变紫、加粗；only 只画灰的或亮的那一半，放两层好淡入；单个用 `gnode(x, y, r, label, lit, label_size, glow, bg)`、`glink(a, b, lit)`
- 指针：`cursor(x, y, scale=1.4, click)` 白色鼠标指针（深色描边、软投影），click 0–1 画一圈扩散的点击环
- 线性图标：`glyph(name, cx, cy, size, fill, sw)`（`GLYPHS`：menu search file files plus grid graph canvas calendar terminal gear help back fwd chev_d chev_r edit folder_plus sort collapse list layout bars link tag hash book eye quote more check x star）
- 色板常量 `PAGE BG BG2 BG3 SIDE BORDER BORDER2 TEXT BRIGHT MUTED FAINT ACCENT ACCENT2 CODE_BG CODE_TEXT INLINE SYNTAX NODE_FILL NODE_EDGE NODE_LINE LINK GNODE ACCENTS`；`render()`、`composite()`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 关系图谱里连线从标签字上穿过去（「狐狸」「B612」「点灯人」），字发花 | 标签先描一圈 3 px 的栏底色再写字（`text(halo=3)`），连线到字前就断开；节点尽量摆在让连线从上方或侧面进来的地方 |
| 「六颗星球—小王子—蛇」两条边几乎在一条直线上，看着像一根线横穿中心节点 | 中心两侧的节点不要摆在同一条直线上：两边都往下挪（+40 / +22 px），两条边成一个浅 V |
| 关系图谱「长出来」时第二帧就铺满七成，像直接冒出来 | 圆形揭开的缓动从 ease-out 改成 ease-in-out，6 步 → 7 步，软边 40 px |
| 动图里点「阅读」看不出点了一下：紫色的点击环压在紫色按钮上 | 点击环改成很浅的淡紫白（#ece4ff）、半径 34、3.5 px，三帧从 0.4 倍放大到 1.15 倍渐隐；按钮同时轻压（0.97）再弹起（1.06） |
| 动图脚本自检报 EOFError | 最后一个阶段（状态栏）和成品完全一样，Pillow 把相同的帧合并了：量化后和屏上完全相同的帧不单独存，时长并到上一帧 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
