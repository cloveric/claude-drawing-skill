# 等轴 2.5D（isometric）

- **实现**：`lib/isometric.py` · `Isometric`
- **范例**：`examples/isometric_weather_island.py` 岛上的气象站（漂浮的分层底座、一格一格的倒角地砖与台地、带双道浪花的海；观测场里的百叶箱、雨量筒、带风杯和风向标的风杆；看守小屋与卫星天线、太阳能板、石板路、栈桥小船、风袋、浮标、开花灌木；探空气球和平底云；四张悬浮数据卡用细引线指向各自仪器，地面上一个指北针）
- **耗时**：约 5 秒

## 何时选用

小世界、城市 / 园区 / 工厂 / 校园示意，系统或流程的「微缩模型」图解，围着场景放数据卡的信息图，讲解片的「全景 / 系统概览」页 → 等轴 2.5D（要霓虹夜景用赛博朋克；要复古小尺寸用像素风）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from isometric import Isometric
```

- 思路：一台正等轴正交相机加一个小光线追踪器。每个部件都是解析实体（平面围成的凸多面体、任意轴向的圆台、可被平面切开的椭球），逐像素求交写进 G-buffer（深度、法线、反照率、材质），画的先后不影响遮挡。同样的实体再从太阳方向画一张阴影图、从正上方画一张记录「柱子顶和底」的高度图，最后统一算光：天空环境光 × AO + 太阳 × N·L × 软阴影（PCSS，半影随遮挡距离变宽）
- 构造：`Isometric(W, H, seed, scale=每格像素, look=(x, y, z), at=(屏幕比例 x, y), sun=(x, y, z), ss=2, floor=-2.4, record=True)`。世界 x 朝屏幕左下、y 朝右下、z 朝上，一格 = 1。`iso(x, y, z)` 世界 → 屏幕；`unproject(sx, sy, z)` 屏幕 → 该高度平面上的世界点（按屏幕位置摆悬浮物）
- 地面：`backdrop(top, bottom, glow, centre)` 浅色渐变和底座下面看不见的地板（接住底座的影子）；`slab(x0, y0, x1, y1, z0, z1, layers)` 漂浮的分层底座；`tiles(levels, heights, colours, soil, gap, paved=(4,))` 倒角地砖（0 海、1 沙、2 草、3 台地、4 铺装）；`sea(shallow, deep, foam, waves)` 海面（岸边浪花、断续第二道浪线、深浅过渡、浪短线、透亮侧壁）；`top_z(x, y)` 取砖面高度；`road()` 带中心虚线的路；`path(cells)` 石板
- 基本体：`box(x0, y0, z0, x1, y1, z1, colour, side, bevel)` 倒角盒子；`obox(centre, size, yaw, pitch, roll)`；`prism(pts, z0, z1)`；`convex([(normal, d)], lo, hi)`；`cylinder(x, y, z0, z1, r, r1=None)`（给 r1 是圆锥 / 圆台）；`tube(p0, p1, r)`；`ellipsoid(centre, radii, yaw, pitch, roll, clip=[(normal, d)])`、`sphere()`、`dome()`。都接受 `paint(P, n, tag)`（按世界坐标上色：砖缝、土层、瓦行、百叶、电池片、卡面文字）、`mat='matte'|'water'|'glass'|'soft'|'gloss'|'card'`、`cast=`（投不投影）、`ao=`（进不进高度图：悬浮物和细线都关掉）
- 建筑：`building(x0, y0, x1, y1, z, h, wall, roof='gable'|'hip'|'shed'|'flat', roof_colour, axis, windows=(行, +x 墙几扇, +y 墙几扇), door=('+x', 位置), trim)`；`roof()`；`window(x, y, z, w, h, facing)`（白框、十字棂、斜向天光、窗台）；`door()`；`sign(x, y, z, w, h, '字', facing)`
- 自然与道具：`tree(x, y, z, size, kind='round'|'pine'|'poplar'|'bush', flowers=)`、`rock()`、`cloud()` 平底云、`windmill(x, y, z, h, yaw, spin)`、`windsock()`、`dish()` 卫星天线、`solar_panel()`、`fence(pts, z, h, closed)`、`pier()`、`boat()`、`balloon()`
- 信息图：`card(x, y, z, w, h, facing='+x', title, tag, value, unit, note, series, icon='wind'|'temp'|'rain'|'balloon'|'sun', anchor=(x, y, z), accent)` 竖在空中的数据卡（文字印在等轴平面上，带细引线和锚点）；`compass(x, y, z, r, north)` 平躺在地面上的指北针；`text()`、`rule()`、`dot()` 平面排版叠在最上层
- 光：太阳从左后上方来，顶面最亮，+x 面（左下）次之，+y 面（右下）只吃天光；`sun_c / sky_c / hor_c / gnd_c`、`soft`、`pen`（最小 / 最大半影）可调。不要霓虹发光、泛光和描边

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 白墙整面发灰，比同一面墙上方的山墙暗一截 | 高度图 AO 会把楼自己的高度算进墙面；侧面改为沿法线（及左右 40°）看地平线，只算挡在前面的东西（已处理） |
| 屋檐、树冠被当成实心柱子，墙顶一圈发黑 | 顶视图同时记录最高那根「柱子」的顶和底：相接的实体合并，悬空的单算，只挡它实际覆盖的那段仰角；檐下不算墙角折痕（已处理） |
| 平顶楼墙上出现一条锯齿状灰带 | 柱子的顶 / 底不能跨边插值：细檐口一插值就在墙边造出一块假悬空板；改最近邻采样（已处理） |
| 长投影的半影满是颗粒 | PCSS 每像素旋转采样之后，再做一遍按深度保边的可分离模糊（已处理） |
| 海面上的短浪线竖着立起来 | 等轴视角里世界 (1, 1) 是屏幕竖直方向；浪线沿世界 y − x 走才是屏幕水平（已处理） |
| 砖缝像棕色勾缝，沙滩缝像一根根圆木 | 草地砖侧面保持草色，只让台地露出土层；缝宽约 0.028 格 |
| 岛占满底座，沙滩一圈像棋盘，看不出是岛 | 屏幕左下、右下两条前边留 1.5–2 格海面；沙滩只放在部分岸边 |
| 卫星天线正对镜头，像棒棒糖或路牌 | 朝向和视线错开（yaw 约 125°、仰约 50°）；反射面中间暗、边缘一圈亮（已处理） |
| 数据卡字太小，折线图压到单位上 | 卡片约 2.9 × 1.65 格，大数字约 0.7 格高；折线图从「数值 + 单位」之后开始（已处理） |
| 引线横穿房顶，画面乱 | 卡片围着各自仪器摆，用 `unproject()` 按屏幕位置定点，引线短、不跨主体 |
| 草地上散落的小花像彩色糖珠 | 花开在灌木上：`tree(kind='bush', flowers=…)` |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
