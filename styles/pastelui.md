# 粉彩界面（pastelui）

- **实现**：`lib/pastelui.py` · `PastelUI`
- **范例**：`examples/pastelui_packing.py` 出发前，再查一遍行李 · Pack Check（产品发布片里的一帧：蓝色粉彩底、一大片柔光和几颗白色光斑；左上胶囊「旅行清单」和步骤条 证件 → 充电 → 雨具 → 出发，粗黑大标题「出发前，再查一遍行李」压一条浅蓝色条；macOS 窗口「打包清单 · 京都 4 天」：左栏目的地、三天天气预报（周一下雨）、已装好 11 / 12 进度条，右栏打包助手的话逐行写出——行首的引用标签「证件夹 ✓」、绿色色条压在已装好的东西下、粉色高亮「周一京都有小雨」配「伞还没装」小标签；右边「出门检查」面板三行：证件 ✓、充电 ✓、雨具 ✗，结论「还差一把伞」；放大镜停在周一的雨云上，镜里是真像素放大；紫色云朵 >_ 从窗口后面探头、奶油色圆里的橙色星芒从面板后面探头、橙色像素小怪站在面板上）
- **耗时**：约 0.5 秒（加 `--stages` 约 5 秒）
- **内部构成**：粉彩界面（纯色粉彩底与光斑、距离场抗锯齿的窗口卡片与部件、CSS 式多层阴影、带姿态的图层、真像素放大镜、圆形擦除、三个扁平小图标）

## 何时选用

产品发布片 / 科技讲解片的「界面 / 流程 / 检查结果」页，要明亮干净、像真产品截图的窗口卡片，一屏讲一件事（大标题 + 一个主窗口 + 一个侧面板 + 状态），一整部讲解片统一的主画面（每节换一种粉彩底、圆形擦除转场）→ 粉彩界面（要磨砂玻璃和弥散渐变用弥散玻璃；要等轴微缩模型用等轴 2.5D；要黑白早期界面用 1-bit 早期画图软件）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from pastelui import PastelUI
```

- 思路：产品发布片里的一帧界面。整片纯色粉彩底（蓝 / 粉 / 黄 / 淡紫 / 薄荷 / 桃，`FIELDS`）加一大片柔光和几颗白色光斑；上面是 macOS 窗口卡片和侧面板、胶囊、粗黑大标题压半透明色条、状态标签、✓ / ✗ 徽章、文字高亮、放大镜，三个扁平小图标从卡片边探头。所有圆角矩形、圆、环、胶囊和线性图标都是有符号距离场，1 px 解析抗锯齿（像素中心取 i + 0.5，整数坐标的边是锐利的）；只有自由多边形（小标签的尖角）是 4 倍超采样再 BOX 缩小。阴影按 CSS box-shadow 的语义算（偏移、模糊半径 σ = blur / 2、扩展、颜色、不透明度，只画在元素外面）：卡片叠两三层——一圈发丝描边、一层染着底色的宽阴影、一层中性的近阴影，所以卡片浮起来却没有灰边
- 图层：一切都画进有名字的图层（预乘 RGBA，收尾时裁到画过的范围）。`layer(name, z)` 开始往某层画（再次调用会重新打开），z 小的在后面：小图标的 z 比卡片小，就只露出探出卡片边的那一截；`end()` 之后画在底色上。每层有姿态 `pose(name, dx, dy, scale, alpha, reveal, origin, feather)`：位移、绕 origin 缩放、不透明度、从左往右揭开（reveal 0–1，软边 feather px）；`show / hide` 只改不透明度；`bounds(name)`。同一样东西的两种状态（检查行之前 / 之后）画成两层，用 show / hide 切换。`stage(name)` 按当前姿态合成快照（PNG 压缩存在内存里）
- 构造：`PastelUI(W, H, seed, keep_stages=True)`；`field(colour='blue', glow=(x, y), glow_size, glow_alpha, bokeh)` 底色（用 FIELDS 名字时同时设定强调色 `accent`、阴影色 `tint`、标题色条色 `mark_colour`）；`wipe(cx, cy, r, prev='lilac', rim, rim_width)` 圆形擦除：圆里显示一切，圆外是上一节的底色，圆边一道强调色的环，`wipe()` 清掉
- 形状：`rrect(x0, y0, x1, y1, r, fill, alpha, grad=(c0, c1), angle, ring, inset)`（ring=w 只画边，inset 决定在里还是在外）、`circle(cx, cy, r, fill, alpha, ring, grad)`、`line(pts, width, fill)`、`poly(pts, fill)`、`shadow(x0, y0, x1, y1, r, dx, dy, blur_px, spread, colour, alpha, shape=(cx, cy, r))`、`soft_shadow(cov_fn, box, …)`（任意形状的 drop-shadow）、`with clip(x0, y0, x1, y1, r):` 把里面画的东西裁进圆角矩形（窗格底色裁进窗体圆角）
- 文字：`text(s, x, y, size, fill, weight='regular'|'medium'|'bold'|'heavy', anchor, alpha, spacing, family='sans'|'mono')`，返回宽度；中英文自动分段（macOS：中文苹方、粗黑标题兰亭黑 Heavy、西文 SF Pro 可变字重、等宽 SF Mono；其他系统 Noto Sans CJK / 微软雅黑；可用 `INKPAINT_FONT_PASTELUI_<CJK|HEAVY|LATIN|MONO>` 指定）；anchor 的第二个字母 s 基线 / m 中文字身中线 / t 字身顶；`measure(…)` 量宽度；`marker(x0, x1, base, h, colour, alpha, drop)` 压在字下面的色条（文字高亮就是 h 盖满字高的 marker）
- 部件：`window(x, y, w, h, title, icon, sub, split, bar=50, radius=22, rim=9, tint)` 返回 Box（`.bar`、`.left`、`.right` 两个窗格）：55 % 白的磨砂外框、两层阴影、白色窗体、标题栏红黄绿三点、居中的应用小图标 + 粗体标题 + 等宽副标题、浅色左栏和发丝分隔线；`card(x, y, w, h, r=26)` 侧面板；`pill(x, cy, text, dot)` 带圆点的小胶囊，返回右边缘；`steps(x, cy, labels, lit, current)` 箭头连起来的步骤条；`headline(x, base, text, size, mark='关键词', draw_text, draw_mark)` 粗黑标题和色条（两者可分两层画，色条那层 z 放后面）；`chip(x, cy, text, colour, size, solid, glyph, anchor)` 状态标签；`mono_tag`；`callout(x, cy, text, colour, glyph)` 左边带尖角的实心小标签；`ref_chip(x, base, text, glyph, ok)` 嵌在正文行里的引用标签（右上角绿色 ✓ 小圆）；`badge(cx, cy, 'pass'|'fail', size)`；`spinner`；`bar(x0, x1, cy, frac)`；`tile(x, y, size, fill, glyph, grad)` 应用图标方块；`avatar`；`glyph(name, cx, cy, size, fill, sw)` 24 格线性图标（`GLYPHS`：more user code lens spark book inbox tag check x suitcase umbrella plug passport calendar pin sun bolt leaf）；`weather('sun'|'partly'|'cloud'|'rain', cx, cy, size)`；`check_row(x, y, w, h, label, tag, sub, glyph, tone, state='idle'|'active'|'pass'|'fail', result, status)` 检查行（status=False 时右端留空，用 `row_status(x1, cy, state, text)` 画到另一层，好单独弹出徽章）
- 放大镜：`magnifier(cx, cy, r, mag, colour, name='lens', z, handle=45)` 自成一层；合成时先把它下面**真实的像素**按 mag 倍双线性放大进镜片，再画白色镜框、淡紫内圈、高光和紫色渐变镜柄；用 `pose('lens', dx, dy, scale)` 移动，放大的内容跟着走
- 小图标（扁平矢量、无脸）：`spark(cx, cy, size, spin)` 奶油色圆里的橙色星芒（白圈、暖色投影）；`cloud(cx, cy, size, rot)` 紫色渐变云朵里的白色 >_（十一个圆平滑并集、径向渐变、光泽、投影）；`critter(x, y, px=9, blink)` 橙色像素小怪（10 × 6 格，整数像素对齐）
- 色板常量 `INK BLUE LILAC GREEN PINK YELLOW MINT PEACH CLAY LINE GREY FIELDS BOKEH`；`render()`、`composite()`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 放大镜压在四天天气预报上：一列只有 86 px，镜片盖住了「周一」、切掉半个「18°」，粉色选中框在镜里变成两道竖条 | 预报改成三天（每列 113 px），日期和温度离图标中心 66 / 76 px，正好在镜框外；镜片半径 47、放大 1.42 倍，镜里只看得到那朵雨云 |
| 绿色色条压在字的下半截，看着像删除线 | 色条下沿落到基线下约 0.22 em（32 px 字：drop 7、高 13），只垫在字脚下 |
| 两个窗格下面各空出约 100 px | 正文行距 70 → 72、首行下移 10 px，进度条贴着预报卡往下放 |
| 「根据 [证件夹]：护照、机票都在」读着别扭 | 引用标签放到行首：「[证件夹 ✓] 里，护照、机票都在；」 |
| 换成薄荷底，步骤条和胶囊跟着变绿，和「通过」的绿色撞在一起 | 有 ✓ / ✗ 的画面用蓝底（强调色是蓝），绿色只留给通过 |
| 回弹缓动前两步就走完 99 %，五步的弹出看着像直接冒出来 | 窗口和面板的弹出改成六步 |
| 动图里橙色像素小怪和星芒变成粉色、绿色徽章变成青色、奶油色圆盘抖成粉点 | 这些颜色面积小、最后几秒才出现，中值切分分不到色位：把整套界面色（47 个精确色值）强制放进调色板，最后一帧取样 ×8 |
| 84 张阶段快照留在内存里，峰值 1.27 GB | `stage()` 存成 PNG 压缩字节（compress_level=1），峰值约 0.54 GB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
