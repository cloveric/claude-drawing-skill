# 白板卡片（canvasboard）

- **实现**：`lib/canvasboard.py` · `CanvasBoard`
- **范例**：`examples/canvasboard_moving_plan.py` 搬家计划 · Moving Plan（深色页面左上一片淡紫光，一扇深色应用窗口：标签栏上红黄绿三点和标签页「搬家计划.canvas ×」，左边一列线性图标，右上角一列缩放按钮 + − 适合窗口 ?；窗口里是灰点阵的无限白板，三个分组框，组名浮在框上方。「收拾 · 第 1 周」：紫边、带淡紫光圈的选中卡片「搬家计划」——老城区 → 河边新家，「11 月 8 日 · 周六 · 还有 12 天」里后半句压着紫色高亮，三个紫色标签胶囊；红边清单「先清掉的东西」，三项打了紫色勾、变灰加删除线，两项还空着；组外一张散放的采购卡和紫色进度条「已买 2/3」。「搬家当天 · 11/8」：时间线卡，一根竖线串起 08:00 → 13:30 四个时间点，最后一个是紫点、「新家卸货」压紫色高亮；黄边卡片「箱子编号」，四个颜色胶囊 厨房 K1–K6（橙）、书房 S1–S9（青）、卧室 B1–B5（绿）、易碎 ×4（红）。「新家 · 河边 3 楼」：图片卡片「新家平面图.png」，深色方格纸上手绘的平面图——墙、门的开启弧线、窗、卧室里绿色的床、客厅里青色的书桌、厨房橙色的台面、手写体房间名，一条紫色虚线从大门画到床边，旁边手写「床先进卧室」；紫色竖条的引用卡「先把床装好，其他的明天再说。」；绿边清单「第一晚要用的」，底下一行「都装在 `B1` 箱」。四条弯曲连线带箭头和标签：紫色「当天」、灰色「装箱」「13:30」、绿色「B1 先开」；`--stages` 出 121 个阶段加成品：卡片一张张掉落、打勾、连线画出、镜头平移到下一组、平面图一笔笔画出、指针点「适合窗口」后拉远到整块白板）
- **耗时**：约 0.6 秒（`--stages` 约 26 秒）
- **内部构成**：白板卡片（保留式绘制：所有形状按白板坐标记进有名字的节点，每次按镜头重画；距离场抗锯齿的圆角矩形、圆、环，逐段只算包围盒的折线和虚线，4 倍超采样的多边形，CSS box-shadow；节点的位姿和进度变量（fade / draw / reveal / pop），tween 出中间阶段，drop 缓动；随镜头移动缩放的点阵；应用窗口、标签栏、图标栏、缩放按钮、鼠标指针和点击波纹；分组框、卡片色边和淡色底、选中光圈、举起的大阴影、图片卡片和方格纸；行内 Markdown（高亮、行内代码、粗体）、会打勾的清单、引用、标签胶囊、颜色胶囊、进度条；沿法线出入的三次曲线连线、箭头和标签；手绘抖线、椭圆和弧、箭头；苹方 + SF Pro + SF Mono + 手札体，浮点字号）

## 何时选用

计划和想法之间的关系，「把几张卡片摆在一块白板上、用箭头连起来」的整理：旅行 / 搬家 / 活动计划、读书和研究笔记的脉络、头脑风暴、项目拆解、评论区里的一问一答，讲解片里「白板上一步步摆出来、镜头跟着移过去」的页 → 白板卡片（要笔记正文、文件列表和关系图谱用笔记应用界面；要暖白纸上的流程图和图表用 Flexoki 纸面；要明亮的粉彩产品界面用粉彩界面；要一层层叠起来的图解用描图纸叠层）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from canvasboard import CanvasBoard
```

- 思路：深色笔记应用的白板视图（片子里那种 Canvas 的样子，不画任何官方 logo）。和别的画风不同，调用画图方法时什么都不栅格化：每个形状都按**白板坐标**记进一个有名字的节点（分组、卡片、连线……），`render()` 时按镜头把所有节点重画一遍，所以任意平移缩放都是锐利的矢量和字。点阵长在白板上（跟着镜头移动、缩放），窗口、标签栏、图标栏和右上角的缩放按钮不动。圆角矩形、圆、环和线条是有符号距离场、1 px 解析抗锯齿；折线逐段只算自己的包围盒，一条 64 段的连线、几百段的手绘草图也很快；箭头和指针是 4 倍超采样的多边形；阴影按 CSS box-shadow 的语义算。
- 节点和动画：`node(name, kind, z)` 开始往某节点记（再次调用就重新打开；z 默认 分组 0、连线 5、卡片 10、其他 20）。`pose(name, dx, dy, scale, alpha, origin)`：位移（白板像素）、绕中心缩放、不透明度（小于 1 时整个节点先画进一层再合成）；`set(name, **vars)` 设进度变量、`reset(name)` 清掉（没设的变量默认 1 = 已完成，卡片的 `lift` 默认 0）；`show / hide`。每个形状都可以带 `var='名字'` 或 `var=('名字', a, b)`（变量从 a 到 b 映射成它自己的 0–1），`mode` 决定进度做什么：fade 淡入 / draw 沿长度画出 / reveal 从左往右揭开 / pop 回弹放大。
- `tween(tag, n, ease, moves=[(节点, 起, 止)], cam=(起镜头, 止镜头), cam_ease='io', between, last)` 出 n 个阶段：中间帧 `mv_<tag>1 …` 和最后的 `<tag>`；起止字典里位姿键（dx dy scale alpha）和变量混着写，止为 None 就是归位、完成；镜头 x、y 线性，缩放按几何插值。缓动 `EASE`：linear out io back drop（drop 先加速落下、再回弹 6 % 落定，卡片掉落用它）。
- 构造：`CanvasBoard(W, H, seed, keep_stages=True, stages_dir=None, window=(x, y, w, h), tab='xx.canvas', ribbon=True, controls=True, glow=True)`（给了 `stages_dir`，`stage()` 当场写 PNG）；`camera(x, y, z)` 白板上的点 (x, y) 在窗格正中、缩放 z；`fit(x0, y0, x1, y1, pad, right)` 返回刚好装下这块区域的镜头（right 给缩放按钮多留的像素）；`to_screen(x, y)` 白板点 → 画布像素；`control(i)` 第 i 个缩放按钮的中心（0 加、1 减、2 适合窗口、3 问号），`hover = i` 高亮它；`cursor(x, y, click, alpha, press)` 鼠标指针（click 0–1 是紫色点击波纹），`cursor()` 收起。
- 白板对象：`group(name, x, y, w, h, label, colour)` 分组框（圆角 20、2 px 线、极淡的一层白，组名浮在左上角上方；变量 frame / label）；`card(name, x, y, w, h, colour, label, selected, pad=(24, 22), fill, tint=0.05)` 卡片：圆角 12、2 px 卡片色边（`CARD_COLOURS`：red orange yellow green cyan purple，也可以 'accent' 或十六进制，None 是灰边）加 5 % 同色底、软阴影，`label` 是写在卡片上方的文件名；`selected=True` 紫边加一圈淡紫光（变量 sel）；变量 `lift` 加一层「举在白板上方」的大阴影。`image_card(name, x, y, w, h, label, bg, grid)` 图片卡片（没有内边距、深色方格纸），画里面的图：`cb.node(name)` 后 `with cb.clip(card):`。`edge(name, a, b, colour, width=4, label, dashed, arrow, bend)` 连线：锚点是 (卡片名, 'l' 'r' 't' 'b'[, 沿边的位置 0–1]) 或 (x, y, 边)，三次曲线沿两条边的法线出入（控制距离 = 两端距离 × 0.45，夹在 50–240），末端实心箭头，正中一块白板底色的标签；变量 p 把它画出来，最后 14 % 长出箭头，过半后标签淡入。
- 卡片里的 Markdown（`card()` 返回 `Card`，从上往下排，`Card.y` 是下一块的顶）：`h1`、`h2(glyph=)`、`p(s, size, fill, weight, hl, x)` 一行行内 Markdown（`==高亮==` 是紫色底、`` `代码` `` 是深底等宽、`**粗体**`；`hl=` 一个变量让高亮扫过去）、`task(s, done, key, lh)` 勾选清单（key 变量 0 → 1：紫色方框弹出、对勾画出、删除线划过、文字变灰）、`quote(lines, size, by)` 紫色竖条的引用、`tags([...])` 紫色标签胶囊、`chips([(名, 编号, 颜色)])` 颜色编号胶囊、`bar(frac, label)` 进度条、`rule()` 分隔线、`gap(px)`。这些也能用 `cb.rich / task / tag / chip` 直接画在任意位置（比如时间线卡里自己排）。
- 形状（白板坐标，记进当前节点）：`rrect(x0, y0, x1, y1, r, fill, alpha, ring, inset)`（拉远时细线不细过 1 屏幕像素）、`circle`、`line(pts, width, fill, dash=(实, 虚))`、`poly`、`shadow`、`text(s, x, y, size, fill, weight, anchor, family='sans'|'mono'|'hand')`（anchor 第二个字母 s 基线 / m 中文字身中线 / t 顶，返回宽度）、`glyph(name, cx, cy, size)`（`GLYPHS`：menu search file plus minus grid fit help check x link image）、`measure`、`with clip(...)`。手绘：`rough(pts, width, fill, closed, rough, passes=2, dash)` 每段是一条略弯、两头出头一点的线，画两遍（第二遍淡一些）；`rough_rect`、`rough_ellipse(cx, cy, rx, ry, a0, sweep)`（圆或弧，收笔处略微搭过头）、`arrow_head(tip, 方向角)`。
- 字体：苹方 + SF Pro 可变字重 + SF Mono，中西文自动分段；family='hand' 用手札体（Hannotate SC，没有就退回苹方）；字号是浮点的，镜头拉近拉远时字连续变大变小；可用 `INKPAINT_FONT_CANVASBOARD_<CJK|BOLD|LATIN|MONO|HAND>` 指定。
- 色板常量 `PAGE BG BG2 BG3 SIDE BORDER BORDER2 TEXT BRIGHT MUTED FAINT ACCENT ACCENT2 BOARD DOT EDGE CODE_BG CODE_FG DONE CARD_COLOURS`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 红边卡片的底发褐，像一块旧木板 | 卡片色底从 7 % 降到 5 %（`tint`），边框才是颜色的主角 |
| 卡片下半截空着一大块，另一张卡的最后一行压到了边框外 | 卡片高度跟着内容走：`Card` 每块返回顶边、`Card.y` 是下一块的位置，先排内容再定高度；清单行距 1.62 → 1.72 |
| 时间线的竖线看不见 | #4a4a4a、2.5 px 拉远到 0.72 倍就没了：改成 #4d4d4d、3 px，灰点 #6a6a6a，最后一个点紫色加一圈淡紫 |
| 「13:30 到」这样的连线标签盖住了大半条短连线 | 组和组之间只有 120–160 白板像素：标签缩成「13:30」，连线两端挪到卡片边的 0.84 / 0.7 处，让它弯出一段 S 形 |
| 平面图的手写批注「床先进卧室」压在虚线路线的弯道上；挪到书桌旁边，又像在说书桌 | 放到路线起点旁边（大门外、平面图底边下面），和左下角的「约 68 m²」排在同一行 |
| 卡片「掉落」用回弹缓动，第一张中间帧就走完 78 %，看着是弹出来不是掉下来 | 新缓动 drop：先按 (u / 0.72)² 加速落下，再回弹 6 % 落定；起点抬高 110、放大 5 %、半透明、带大阴影 |
| 散放卡片掉落时镜头一起下移，镜头也跟着回弹 | `tween()` 的镜头单独用 `cam_ease`（默认 io） |
| 引用卡的字跟着回弹一起揭开，回弹那一下字又缩回去一点 | 卡片落定后再单独把两行字写出来（`quote` 阶段） |
| 动图里镜头平移的帧留下一块块淡淡的残影和竖条 | 分组框的底（#212121）、卡片的影子和白板（#1c1c1c）只差约 5 级，落在「没变」的 7 级容差里，镜头移开后这些像素没重发：镜头在动的帧容差 1 级，其他中间帧 6 级、关键帧 2 级 |
| 动图 1.51 MB，超了 | 固定 Bayer 抖动让每个镜头帧整片重编：白板是平的、没有色带，去掉 Bayer；平移 7 → 6 帧、下移 5 → 4 帧、拉远 8 → 7 帧，1.36 MB；修残影后 1.47 MB |
| 出阶段时峰值内存 0.78 GB | 拉远时每一帧都要一个新的浮点字号，字体缓存一直长：超过 160 个就清空，峰值约 0.62 GB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
