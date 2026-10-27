# 圆珠笔涂鸦（ballpoint）

- **实现**：`lib/ballpoint.py` · `Ballpoint`
- **范例**：`examples/ballpoint_board_game.py` 蛇梯棋大冒险 · Snakes & Ladders, Round 7（午休时在复印纸上用蓝、红、黑三支圆珠笔画的 8×8 蛇梯棋，彩铅一行行涂成彩虹色格子；一局正在进行：骰子刚从页边弹过来、掷出 4，蜗牛从 10 跳四格到 14（红笔虚线弧标出 1-2-3-4），正顺着长梯子爬到 38（红圈、虚线箭头、+24!），小云从 47 被绿蛇滑下去，晕乎乎地喊 nooo~，骰子怪在 51 捂着脸；页边是彩旗、太阳、井字棋、纸飞机、星星串、山坡小房子、花盆，吐槽小纸条「who drew this snake so LONG?!」、记分卡、把 three 划掉改成 four、红笔结论 slow snail, fast ladder!；右下角还有上一页购物单压过来的无墨压痕）
- **耗时**：约 4 秒
- **内部构成**：圆珠笔涂鸦（复印纸纹、纤维与折痕；圆珠笔：干起笔、压力线宽、断墨、墨团、收笔小钩、描两遍、压痕；彩铅斜向排线出界；圆珠笔之字排线；字体骨架重描的手写、划掉重写、无墨压痕字）

## 何时选用

上课 / 午休走神的随手涂鸦、纸上正在进行的游戏或计划（手画棋盘、寻宝图、清单、路线、比分）、学生和办公室日常的轻松小故事、讲解片里「在草稿纸上推演一步」的页 → 圆珠笔涂鸦（要铅笔图表、荧光笔和贴纸的实验记录用实验笔记本；要没有线稿、柔和的彩铅小物用韩国彩铅；要小孩的蜡笔画用儿童蜡笔画；要黑白石墨写生用铅笔素描）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from ballpoint import Ballpoint
```

- 思路：圆珠笔墨是油性墨膏，靠滚珠压到纸上；颜色按光密度（比尔定律）叠加，描两遍、交叉、墨团都会更深更饱和（蓝色叠到深蓝紫，不会变成死黑）。每一笔：起笔头几像素滚珠是干的（细、淡、只挂在纸纹峰上）→ 压力 ±12% 漂移、线宽随之略变、手抖 → 偶尔断墨 2–9 px（墨断了，压痕还在）→ 停笔、急转弯、有时起笔处掉一个墨团 → 抬笔甩出 90–160° 的小钩。每一笔都在纸上压出凹槽，左上侧光下槽的左上壁暗、右下壁亮。彩铅是蜡，只挂在碰到的纸纹上：轻压颗粒发白，重压填进谷里；一块一块地斜向快速排线，出界、换方向，大面积浅、小面积重
- 构造：`Ballpoint(W, H, seed, ss=2, pen_width=2.5)`；`paper(tone, tooth=0.75, fibres=260, mottle, cockle=1.0, folds=[((x0, y0), (x1, y1))], vignette=0.09)` 灰米色复印纸：细纸纹、稀疏纤维、斑驳、低起伏和折痕（按左上光打光）、拍照的四角暗角
- 圆珠笔：`line(pts, pen='blue'|'red'|'black'|None, pressure, width, closed, smooth, wobble, bow, hook, gloop, skip, twice, start, clip, groove)`；`bow` 是徒手直线的侧弯（约 0.003–0.006 倍长度），`hook` / `gloop` / `skip` 是收笔小钩、墨团、断墨的几率，`twice` 是再描一遍（偏 0.6–1.6 px、只描一部分）的几率，`pen=None` 只压槽不出墨；`lines(paths, …)` 一批短笔画共用一次栅格化；`emboss(pts)` 无墨压痕
- 小件：`dot(x, y, r, pen)` 转一小圈压出的实心点；`eye(cx, cy, rx, ry, pen, look, shine)` 由外往里转圈涂实、留一个圆高光的眼睛；`face(cx, cy, size, mood='smile'|'grin'|'oh'|'dizzy'|'sleep'|'worry', pen, blush, look, rot)`；`dashes(pts, pen, dash, gap, pressure, smooth, clip)` 虚线（返回重采样后的路径，好接箭头）；`arrow(tip, direction, size, pen)`；`ring(cx, cy, rx, ry, pen, turns, rot)` 不闭合、越画越往外的随手圈
- 彩铅：`pencil(mask, colour, angle, pressure, spacing, length=(40, 90), overshoot, width=2.9, jitter, bow, cross, clip, groove)` 斜向排线（`length` 是一段手腕笔画的长度，接缝逐行错开；`overshoot` 出界像素；`cross` 再叠一层角度）；`pencil_line(pts, colour, pressure, width)` 单根彩铅线；颜色用 `PENCILS` 里的名字（leaf green lime mint teal sky blue violet lilac pink rose red orange peach yellow ochre brown tan grey cream）或 '#rrggbb'
- 圆珠笔排线：`pen_hatch(mask, pen, angle, spacing, pressure, length, overshoot, zigzag=0.85, cross, clip)` 来回不抬笔的之字排线，转折处带墨团（阴影、暗面、深色棋子）
- 手写：`write(s, x, y, size, pen, pressure, slant=7, spacing=1.04, jitter, anchor='l'|'m'|'r', rot, width, blind, hook, gloop)`，y 是基线，返回写出来的 (x0, y0, x1, y1)；字形取自细手写字体的骨架（Zhang-Suen 细化后描成笔路径，按字缓存），每个字母单独缩放、倾斜、上下浮动，有起笔、墨团、小钩；中文用细黑体骨架；`blind=True` 是上一页透过来的无墨压痕字；`strike(box, pen, passes)` 来回划掉一个词；`underline(x0, x1, y, pen, wavy)`
- 遮罩和点：`poly(pts)`、`ellipse(cx, cy, rx, ry, rot)`、`band(pts, width)`、`tube(pts, w0, w1)` 由粗到细的身体（蛇、尾巴），`Ballpoint.tube_sides(pts, w0, w1)` 它的左右两条边（一笔描下去绕过尾尖再描回来）；`circle_pts`、`star_pts`、`cloud_pts(cx, cy, w, h, bumps, seed, flat)`、`spiral_pts(cx, cy, r, turns, a0)`、`heart_pts`、`Ballpoint.resample(pts, step)`
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4；常量 `PENS PENCILS PAPER`；字体可用 `INKPAINT_FONT_BALLPOINT` / `INKPAINT_FONT_BALLPOINT_CJK` 指定（默认 macOS Noteworthy Light / 黑体-简 细体，Linux Kalam / Caveat / Noto Sans CJK，Windows Segoe Print / 微软雅黑）

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 蛇太细像蚯蚓，棋子小得读不出 | 蛇头宽 54 / 44 / 38 px（约半格到六成格），头比脖子宽；蜗牛、云放大 1.1–1.3 倍，云的脸 84 px |
| 梯子横档和格线从蜗牛、云身上穿过去 | 先画棋子，后画的蛇、梯子、格线都用棋子遮罩 `clip` 掉（笔走到已经画好的东西前就停住）；格子上色也绕开蛇和棋子 |
| 跳格的红虚线像一串锯齿 V | 每跳一格用一条 14 点的抛物线弧（高 24 px）配箭头，不用三点样条 |
| 跳格的计数 1–4 压在格子编号上，「1」落在竖格线上整个看不见 | 弧的起止放到格子下部 0.4 格，数字放在弧顶、往右偏 13 px，离开格线 |
| 「+24!」被竖格线劈开、「nooo~」被汗滴和云挤住 | 标注整块放进一个空格子里；云只留一颗汗滴放在侧面，去掉两只手 |
| 折痕成了贯穿全画的一道亮白线 | 折痕的谷只深 0.1、宽 3 px，沿线加一点摆动，主要靠两侧纸面坡度不同带出的明暗 |
| 上一页透过来的无墨压痕字像白色浮雕字 | 盲压的槽深 ×0.55，只在侧光下隐约可见 |
| 手写字母互相撞（slow 看成 dow） | 每个字母的步进按它自己抖动后的字号算，字距默认 1.04，步进抖动降到 2% |
| 冒号、i 和 ! 的点丢了 | 字形骨架里小于 0.11 字号的连通块全部当「点」画，单像素的也算 |
| 格子编号末尾的墨团像小数点 | 小号数字的 gloop 降到 0.15 |
| 蛇头背后缺一段轮廓；鼻孔和嘴像多出来的眼睛 | 头的弧画到 ±148°，身体两侧从路径第 4 个点开始；去掉鼻孔和嘴，只留墨眼、彩铅腮红和红舌头 |
| 红笔沿梯子的虚线箭头从蜗牛壳上穿过去 | 箭头放到梯子没有棋子的那一侧（+40 px），再用棋子遮罩 `clip` |
| 墨线旁边的压痕亮边太抢、像浮雕 | 压痕打光增益 0.16 → 0.13，上限 ±0.1 |
| 动图里蛇和格子的彩铅颜色被量化成土褐色 | 两段调色板：150 色从「有色像素 ×5」的样本里中值切分，另外 104 色只从有色像素（饱和度 > 0.12）里切；49 帧约 0.6 MB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
