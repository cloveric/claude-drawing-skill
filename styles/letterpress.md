# 凸版印刷海报（letterpress）

- **实现**：`lib/letterpress.py` · `Letterpress`
- **范例**：`examples/letterpress_circus.py` 马戏团来了（1890 年代红黑两色马戏团海报：左栏每行木活字排满版心——THE GRAND TRAVELLING、带投影的红色大字 CIRCUS、宋体黑木活字「马戏团来了」、星号节目单；右边木刻：走钢丝的舞者端着平衡杆，下面戴非斯帽的大象踩在条纹鼓上扬鼻致意，40 FT. 尺寸线；红版色块与黑版轮廓错开几像素；三折折痕裂墨、贴上的日期条 SATURDAY · MAY 17、钉孔锈斑、泛黄与霉斑）
- **耗时**：约 6 秒
- **内部构成**：凸版印刷海报（木活字、红黑双色错版、木刻插图）

## 何时选用

活动 / 演出 / 开业 / 讲座的复古海报、「XX 来了」式的宣告、节目单与价目、旧时代广告、19 世纪美式或民国风的印刷品、讲解片里的「历史 / 老派做法」页 → 凸版印刷海报（要几何构成的现代海报用包豪斯几何，要剪报拼贴用报刊拼贴）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from letterpress import Letterpress
```

- 思路：每种油墨一块版（forme），先把要印这个颜色的东西都「锁」进版里，`press(ink)` 一次压印。每过一次机器纸张落得不一样：每块版有自己的平移和极小旋转（`register(ink, dx, dy, rot)`），红版和黑版永远对不齐。先红后黑
- 纸：`paper(colour, warm, tone)`：已经泛黄的廉价海报纸（云状纸浆、短纤维、杂点、纸齿、微微不平）
- 版：`lock(mask, ink, film)` 锁进任意遮罩；`clear(mask, ink, keep)` 刻掉（木刻高光、前后遮挡）；`with lp.layer('key'):` 把东西锁进版的某一部分，`press(ink, only=['key'])` 只压这一部分（阶段动图先出轮廓线、再出排线）；`press(ink, density)`：边缘随纸齿参差、边上积一圈深墨、大实地缺墨发花并露出纸齿白点、灰尘留下圆形漏印；黑压红更深
- 木活字：`type_line(s, x0, x1, base, cap, face, ink, align='justify', stretch, track, shade=(dx, dy, 另一版颜色, gap), inline=(inset, width), wear, grain, limits)`：默认把一行排满版心（字面横向压扁或拉宽、再加字距），每个字是一块木头：木纹条痕、一端偏浅、凹坑软斑、边角缺口、偶尔一道顺纹裂缝；shade 是印在另一块版上的投影，inline 是笔画中间刻一道白线。face 用 clarendon / antique / gothic / fatface / cjk（宋体黑）；`type_width()` 量宽度
- 铅字与花饰：`text(s, x, y, size, face='roman'|'roman_bold'|'italic'|…, ink, anchor, spacing, rot, stretch)`、`text_mask()`、`text_width()`；`rule(x0, x1, y, kind='single'|'double'|'thick_thin'|'thin_thick'|'dotted', ink, weight, joints)` 铜线（长线由几段拼成，接头有细缝和 1 像素错位）；`leaders()` 引线点；`star()`；`ornament(字符, ...)` 花饰字体（缺字体时画星）；`border()` 粗细双线框加方角
- 形状（整页浮点遮罩，可加减乘）：`shape(控制点)` 平滑闭合曲线、`poly()` 直边多边形、`tube(点列, widths=[...])` 变粗细的管子（腿、鼻、尾、绳）、`ellipse(cx, cy, rx, ry, rot, a0, a1)`、`rect()`、`outline_pts()`
- 木刻：`key(mask, width, heavy)` 轮廓线刻在形状内侧、背光一侧加粗；`hatch(mask, angle 或 centre+aspect, spacing, tone, lo, gain, wobble)` 线宽随明暗变化的排线，tone 低于 lo 处收尖消失、高处并成实地；`form_tone(mask, soft)` 把遮罩当成鼓起的体积打光得到 tone；`ramp(p0, p1)` 线性渐变 tone；`cast(mask, dx, dy, onto)` 投影；`line(pts, width, taper)` 两头收尖的刻线（皱纹、绳子）；`solid()`；`stipple(mask, density, size, tone)` 点刻；`tint(mask, ink=RED, loose, grow)` 另刻的套色块，边缘游走、比轮廓略胖
- 印后：`fold('v'|'h', pos, depth, crack)` 折痕（油墨裂开、积灰、两侧受光不同）；`tone_edges()` 边缘泛黄；`foxing(n)` 霉斑；`stain()` 水渍；`tack(x, y, r)` 钉孔和锈斑；`nicks(n, size)` 纸边缺口；`strip(x0, y0, x1, y1, rot, colour, draw=fn)` 另印一条日期条贴上去（fn 拿到一个小 Letterpress 往上排字，周围有浆糊印）
- 颜色常量 `RED BLACK PAPER`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 大面积实地满是白点，像加了噪点滤镜，木刻黑块发灰 | 漏白（salt）只出现在实地内部，纸齿阈值 0.975 以上，约占 1%–5%；边缘积墨处几乎不漏；木活字凹坑软斑浓度降到 0.15–0.35 |
| 大象前腿斜着伸到老远的鼓上，像撑地的肘 | 以髋为轴把身体整体抬起（约 22°），四条腿都竖直向下；鼓放在前肩正下方，鼓顶 = 前肩高度 + 前腿长（腿比后腿短 4%） |
| 大象像秃头圆球加一根水管，耳朵像第二个头、像垂耳狗、像兜帽 | 象鼻根部宽约一个头高（104→26 渐细），并进前额；耳朵是扇形：前缘弧形贴在眼后，顶端低于头顶让圆顶露出来，后缘波浪、下端收尖；加小象牙和张开的嘴 |
| 腿根在身体里画出一圈圆头轮廓，像插上去的柱子 | 先刻远侧两条腿；近侧身体、头、鼻、近侧腿、尾巴合成一个剪影只刻一圈外轮廓，内部只补大腿、肘几笔短轮廓线 |
| 排线整片一样密，大象像条纹木桶 | 排线线宽跟随明暗（`hatch` 的 tone），lo 约 0.3：背上最亮处线条自然收尖消失；身体用绕远处圆心的弧线，腿用竖线，鼻子斜线加横向皱纹 |
| 鼓上的条纹印成一整块红色楔形 | 条纹相位 = arcsin(u)·9 − y/9，一圈正面看到 4–5 条斜纹，上下各留出箍 |
| 象头上的小帽画成红色贝雷帽、像一颗樱桃 | 非斯帽用直边多边形 `poly`（不用平滑闭合曲线），流苏从帽顶垂到后面 |
| 象鼻尖碰到钢丝，看着像要去抓钢丝 | 鼻尖离钢丝留约 70 px，卷向演员 |
| 画面偏右，桅杆和大象之间空出一大片 | 大象放在两根桅杆正中；背后加雕版衬线：横向细线、椭圆向外渐隐，每样东西周围先 blur 出一圈白再清掉 |
| 舞者的站立腿是两根细线，平衡杆横穿胸口 | 腿加粗（17→9 px）、加黑色舞鞋；手肘弯下，杆放到腰的高度 |
| 马戏圈的圈沿伸出画面右边；锯末和地面投影太黑，像污渍 | 圈的半宽按两根桅杆间距算；锯末密度 0.0035、只在脚边，投影用横向排线（tone 0.55） |
| 纸边的小缺口是一颗颗黑点，像墨团 | 缺口只留 3 个、3–7 px |
| 峰值内存 1.5 GB | `press` 按 240 行一带处理；木刻印完就释放整页遮罩（1.19 GB） |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
