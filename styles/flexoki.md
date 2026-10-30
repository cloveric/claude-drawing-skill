# Flexoki 纸面（flexoki）

- **实现**：`lib/flexoki.py` · `FlexokiPaper`
- **范例**：`examples/flexoki_pour_over.py` 一杯手冲咖啡 · Pour-over, in Five Diagrams（暖白纸 #FFFCF0 上的一页图解：左上黑底胶囊「图解 · 手冲咖啡」、粗黑大标题「一杯手冲咖啡」和灰色英文 Pour-over, in five diagrams，右上灰胶囊「总时长」和大字 2:30；五张不描边的浅灰圆角卡片排成两行（右边一列和上一行共用一条缝），每张有粗黑中文标题、灰色英文类型名和等宽编号：① 流程图「从豆子到一杯」：称豆 15 g → 研磨 · 中细 → 冲洗滤纸 → 闷蒸 30 g 水，往下到菱形「鼓包平了？」，绿色「是」→ 分两段注水 → 胶囊形「出杯」，红色「否」沿一条倒圆角的折线绕回闷蒸；② 时序图「两分半里发生了什么」：水壶 / 滤杯 / 分享壶三条虚线生命线、滤杯上的激活条、左边一列等宽时间 0:00 0:45 1:15 2:30、三次注水、浅黄便签「排气 · 45 s」、虚线回复「约 210 g 咖啡液」；③ 柱状图「磨多细，滴多久」：粗 / 中 / 中细 / 细四根青色柱，选中的中细是橙色，柱顶写时间；④ 饼图「240 g 水分三次」：30 / 120 / 90 g 三块（橙、蓝、绿），块之间是纸色的缝，块上写 1/8 1/2 3/8，旁边图例；⑤ 对比表「三种冲法」：手冲 / 法压壶 / 意式（表头前橙、紫、青三个小圆点）× 方式、研磨、时间、口感，手冲一列套橙色圆角框；底下一行灰色小字写配方并注明数字是示意；`--stages` 出 151 个阶段加成品：标题升起，五张卡片暗着升起，再一张张亮起、套上橙色聚焦框，图一边一边画出来——框弹出，线画过去再落下箭头，消息飞过去，右上的计时器从 0:00 走到 2:30，柱子长高、数字跟着滚，饼图顺时针扫开，表格一行行滑进来）
- **耗时**：约 0.3 秒
- **内部构成**：Flexoki 纸面（Flexoki 色板与角色名、浅色 / 深色主题；有符号距离场的圆角矩形、圆、环、精确菱形、圆柱、扇形与折线，1 px 解析抗锯齿；带弧长的折线：按进度画出、沿弧长虚线、在箭头下截短，三次曲线、按切线出入的曲线、倒圆角折线；4 倍超采样的小三角箭头；先合成再放下的节点组；苹方加假粗的粗黑标题、SF Pro 可变字重、SF Mono；带姿态的图层与 fresh 重画；卡片、聚焦框、胶囊、步骤胶囊、大数字、轨道条、窗口、虚线框、宽度标注、代码行；流程图的框和边、时序图的生命线 / 激活条 / 消息 / 便签、饼图、图例、柱状图、表格）

## 何时选用

讲解片、文档、教程里的「图表页」：步骤和流程、时间线上的往来、占比、对比，要像文档站或技术博客里的图——暖白纸、墨黑字、浅灰圆角卡片，图像 Mermaid 渲染出来那样干净（灰边框、墨线小三角箭头、普通标签），一页放几张图讲清一件事（一份配方、一个工作流程、一次部署、一组产品数字），还能做成「图一边一边画出来、数字滚动」的动图 → Flexoki 纸面（要手写粉笔的示意图用黑板板书；要铅笔图表和便利贴的实验记录用实验笔记本；要彩色粉彩底和 macOS 窗口的产品界面用粉彩界面；要深色笔记应用窗口用笔记应用界面；要点阵白板上的卡片和连线用白板卡片；要系统的微缩模型用等轴 2.5D）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from flexoki import FlexokiPaper
```

- 思路：文档站式的图解页，配色是 Flexoki（「墨在纸上」的一套配色）：暖白纸 #FFFCF0、墨黑 #100F0F 的字、一串暖灰（50 #F2F0E5 卡片底、100 #E6E4D9 轨道和表头、150 #DAD8CE 细线、200 #CECDC3 边框、300 #B7B5AC 最淡的字、500 / 600 次要的字），八种强调色各两档（600 写字、400 填色）。纸上是不描边、不投影的浅灰圆角卡片（半径 28），粗黑中文标题、灰色英文类型名、等宽编号；卡片里的图照轻量图表渲染器（Mermaid 那一类）的画法：框比它的底色差一级、2 px 灰边，2.4 px 墨线末端一个小的实心三角箭头，普通半粗体标签。强调色只放在有意义的地方。
  - 形状：圆角矩形、圆、环、胶囊、菱形（精确的菱形距离场）、圆柱（身子加上下两个椭圆，顶上椭圆的下沿也描边）、饼图扇形和折线都是有符号距离场，1 px 解析抗锯齿（像素中心取 i + 0.5）；箭头和其他自由多边形 4 倍超采样再 BOX 缩小。
  - 线：折线带弧长——`p` 画到全长的几成（切口仍是圆头），`dash` 沿弧长画虚线（平头），在箭头下面截短一截，箭头的尖就是最后一个点。`curve(a, b, da, db, k)` 是渲染器那种按切线方向出入的三次曲线，`rounded(pts, r)` 是拐角倒圆的折线（回环边），`bezier(p0, p1, p2, p3)` 直接给控制点。
  - 组：一个框（底、边、字）先合成一组再按不透明度放下，弹出时（0.85 → 1 倍、淡入）字和框一起缩放、一起变淡，像 SVG 的 `<g opacity>`。
  - 字：中文苹方（粗黑用 Semibold 加 size/50 px 的描边假粗，接近思源黑 Black 那种标题），西文 SF Pro 可变字重（大数字字距收紧 0.03 em），等宽 SF Mono；其他系统冬青黑体 / Noto Sans CJK / 微软雅黑和 Helvetica / DejaVu；可用 `INKPAINT_FONT_FLEXOKI_<CJK|HEAVY|LATIN|MONO>` 指定。字重 regular / medium / semibold / bold / heavy。
  - 图层：和粉彩界面一样，一切画进有名字的图层（预乘 RGBA，收尾时裁到画过的范围），每层有姿态 `pose(name, dx, dy, scale, alpha, reveal, origin, feather)`、`show / hide`、`bounds(name)`、`with clip(...)`；`layer(name, z, fresh=True)` 先清空再画，用来按进度重画（线画到一半、数字滚到中间、饼图扫到一半、柱子长到一半），逐边画出的动图就是这样做的。`fresh=True` 不改姿态：开头 `hide()` 过的层要 `show()` 才看得见。
- 构造：`FlexokiPaper(W, H, seed, keep_stages=True, theme='light'|'dark')`，先 `paper()`。`ground` 是图画在什么颜色上（边上标签垫的底、饼图的缝、框的默认底色都看它）：`paper()` 设成纸色，`panel()` / `window()` 设成卡片色；框的默认底色比 `ground` 差一级（纸上用浅灰，浅灰卡片上用纸色）。
- 页面部件：`chip(x, cy, text, fg, bg, size, anchor, weight, glyph=None|'dot'|'check')` 胶囊（默认黑底纸色字），返回 Box；`heading(x, base, zh, en, size, en_size)` 粗黑中文加同一基线的灰色英文；`number(x, base, s, size=104, fill, anchor, track=-0.03)` 大数字（计数、计时、度量）；`panel(x, y, w, h, r=28, tone='surface'|'paper'|'dark', title, tag, num, title_size, pad)` 卡片和标题行，返回带 `.inner`（标题下面的内容区）的 Box；`focus(box, colour=ORANGE4, width=4, r, out)` 内嵌的聚焦框；`step(x, cy, label, lit, size, accent, mute)` 步骤胶囊（暗 → 亮，勾随 lit 画出来）；`meter(x0, x1, cy, frac, colour, h)` 胶囊轨道和填充；`window(x, y, w, h)` 纸色窗口（3 px 灰边、浅灰标题栏、三个灰点），返回带 `.body` 的 Box；`dashed_rect(x0, y0, x1, y1, r)` 虚线圆角框；`dimension(x0, x1, y, label)` 宽度标注（两端虚线，中间标签垫底色）；`code(x, base, tokens, size, mark)` 一行等宽代码（(文字, 颜色) 片段，mark 那段垫一块浅橙）。
- 渲染器：`node(cx, cy, w, h, label, shape='rect'|'round'|'stadium'|'diamond'|'cyl'|'circle', size=22, p, fill, stroke, sw=2, fg, weight)`，w × h 是整个外框（菱形是两条对角线），label 里 `\n` 换行，p 是弹出进度；返回 Node（`side('l'|'r'|'t'|'b', gap)` 边的中点 / 菱形的顶点，`toward(x, y, gap)` 朝某点出边的位置）。`edge(pts, p, head=True, dash, width=2.4, colour, head_len=11, head_w=10.4, label, label_t, label_size, label_fill, label_bg)`：线过了 label_t 才出标签，p 过 0.94 才落下箭头。另有 `head(x, y, deg)`、`line(pts, width, fill, alpha, p, dash, cap)`、`rrect`、`circle`、`poly`、`shadow`（CSS box-shadow，只给一张抬起的卡片用）、`text`、`measure`。
- 时序图：`lifeline(x, y0, y1, p)`、`activation(x, y0, y1, w=14, p)`、`message(x0, x1, y, label, p, reply)`（标签居中写在线上方，reply 是虚线）、`note(x0, y0, x1, y1, text, p)`（浅黄便签）。
- 图表：`pie(cx, cy, r, values, colours, sweep, gap=3, labels, label_r)` 从十二点顺时针，`sweep` 0–1 扫开，块之间是 gap px 的底色缝；`legend(x, y, items=[(颜色, 名字, 数值)], size, pitch, value_x, alpha)`（alpha 可以每行一个）；`bars(x0, y0, x1, y1, values, labels, colours, vmax, ticks, tick_fmt, p, value_fmt, bar_w, value_colours)`（p 可以每根一个，柱顶数值按 p 滚动）；`table(x, y, widths, n_rows, row_h, head_h, header, dots)` 画框和表头，返回 Table（`cell(i, j)`、`col(j)`、`box`），`table_row(t, i, cells, colours, weights)` 画一行（每行可以放一层）。
- 色板常量 `PAPER BG2 UI UI2 UI3 TX3 TX2 TX1B INK`、`BASE50 … BASE950 BLACK`、`RED RED4 ORANGE ORANGE4 YELLOW YELLOW4 GREEN GREEN4 CYAN CYAN4 BLUE BLUE4 PURPLE PURPLE4 MAGENTA MAGENTA4`、`ACCENTS SERIES THEMES PALETTE`；颜色也可以写强调色的名字（'orange' 是 400 档，'orange6' 是 600 档）；`mix(a, b, t)`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 粗黑标题用苹方 Semibold 太细，不像那种黑体 Black 的标题；兰亭黑 Heavy 够粗但字形不一样 | 苹方 Semibold 加 size/50 px 的描边假粗（62 px 的标题约 1.2 px），西文用 SF Pro 800 |
| 图例数值用 SF Mono，「30 g」读成「30  g」，数字和单位隔得太开 | 图例数值默认用普通字体，等宽只留给编号、时间刻度和代码 |
| 时序图左边的时间列用最淡的 #B7B5AC，像装饰而不是信息 | 改成 #878580、medium；最淡的灰只留给编号和坐标刻度 |
| 两行卡片的缝对不上（第一行分在 1000 / 1024，第二行分在 616 / 640 和 1136 / 1160），满屏的缝东一条西一条 | 时序图卡片和对比表卡片都做成 640 宽，右边一列共用 1136 / 1160 这一条缝；流程图卡片因此宽到 1016，第一行框间距从 50 px 放到约 89 px |
| 流程图第二行两条边一长一短（122 / 158 px） | 「分两段注水」放在「出杯」右边和菱形左顶点的正中，两条边一样长 |
| 动图自检报 EOFError：动作做完后的停留阶段和最后一个动作帧一模一样，Pillow 把相同的帧合并了 | 量化后整帧都没变的帧不单独发，把它的时长加到上一帧上 |
| 动图里大片纸色差几级（末帧误差中位数 2） | Pillow 按调色板量化时查的是缩减过的色立方：改成 numpy 精确找最近色（每种颜色算一次、缓存），离 Flexoki 色 2 级以内的直接用那个颜色 |
| 动图里红色「否」、浅黄便签、紫色小圆点的边缘变成橙色和灰色（单点误差到 49 级） | 这些饱和的中间色面积太小，中值切分分不到：留 60 个色位只从饱和、又不贴近 Flexoki 色的像素里切；误差超过 20 级的像素 478 → 166 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
