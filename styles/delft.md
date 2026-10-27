# 代尔夫特蓝瓷砖（delft）

- **实现**：`lib/delft.py` · `DelftTile`
- **范例**：`examples/delft_canal.py` 运河小镇 · 一阵风 De Windvlaag（一面锡釉砖墙：中间 11 × 7 块砖连成一幅砖画，四周是四角带角饰、圆框里画小图的单块砖。一阵西风吹过运河小镇：风车在转，平底帆船顺风驶来，烟、床单和衬衫都往右扬，郁金香一齐弯腰，一个人的帽子被吹到河面上，小狗腾空扑过去；藤蔓边框和卷轴题字 DE WINDVLAAG；每块砖单独画、单独烧，线条在砖缝处错开；开片、铁斑、崩瓷，云上一块窗户倒影在砖缝处断开错位）
- **耗时**：约 6 秒
- **内部构成**：代尔夫特蓝瓷砖（锡釉砖墙：刺孔粉印、钴蓝勾线与晕染、生坯到入窑、逐块错位、单块砖角饰、勾缝、开片、窗户倒影）

## 何时选用

荷兰、运河、风车、郁金香、帆船与航海，老派欧洲家居（厨房、壁炉、瓷砖墙），蓝白两色的典雅装饰，一组图标式的小图（单块砖可以一砖一个主题），讲解片里的「传统工艺 / 历史 / 一组图标」页 → 代尔夫特蓝瓷砖（要石子和玻璃拼的古代地面画用罗马马赛克；要普鲁士蓝的日光晒图用蓝晒）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from delft import DelftTile
```

- 思路：照作坊工序画一面锡釉砖墙——白坯砖排在一张从来不完全横平竖直的网格上；用刺孔纸样拍炭粉留下点线（粉印）；trek（勾线）用细长笔沿粉印勾轮廓；再用稀钴蓝大笔晕染（生釉吸水快，染色不能晕开，留下笔道、鬃毛丝、干边积色、叠染变深、和轮廓错位）；没烧之前颜料是灰黑色、釉是哑光粉白；入窑后釉面变亮，颜料按每通道 Beer–Lambert 吸收变成钴蓝，洇进釉里、带细颗粒。只有一种透明颜料，所以从前往后画，用 `occlude()` 留出前面的东西。每块砖单独画、单独烧：砖缝处线条错开一两像素，每块砖的白和蓝都不同；单块砖四角各画四分之一角饰，四块拼在一起才是一朵。墙面是高度场：每块砖略鼓、略斜，倒角打光，窗户倒影碎成弯曲的几片
- 构造：`DelftTile(W, H, seed, tile=128, joint=3.6, origin=(0, -36), ss=3, glaze=(冷白, 暖白), mortar, light)`；tile 是砖距（约 13 cm 一块），origin 让砖画对齐网格；`tableau(i0, k0, i1, k1)` 指定连成一幅画的砖（i0 ≤ i < i1），返回外框像素；`rect(i, k)`、`centre(i, k)`、`visible()`、`in_tableau(i, k)`
- 图层：`layer(名字)`，每层分 trek（线）和 wash（晕染）两份；`stage(name, hide=(…))` 可以隐藏层名（'single'）、种类（'wash'）、具体某份（'picture.wash'）、粉印（'pounce'）或全部（'*'），用来重演作坊工序
- 笔：
  - `trek(点列, width, dens, taper, wobble, smooth, pounce, bead)` 勾线：落笔有小墨珠、收笔变尖、往下走的笔画更粗、手有点抖，同时记下粉印点；`line(p0, p1, bend)`、`closed(点列)`、`dot(x, y, r)`；
  - `wash(形状, tone, angle, pool, ragged, slip, band, streak, grad, holes)` 晕染：形状可以是多边形、多边形列表或整幅遮罩；tone 约 0.1 淡到 0.5 深；angle 是笔道方向；`grad=((x0, y0), (x1, y1), f0, f1)` 沿一条线渐变；`holes=[多边形]` 留白；
  - `hatch(形状, angle, spacing, width, dens, wave)` 排线（阴面、帆、茅草、船身）；
  - `letters(字, x, y, size, font='serif', spacing)` 手绘字
- 遮挡：`occlude(形状, grow)` 把画好的东西的轮廓留出来，之后的线和晕染自动避开；`clear_occlusion()`
- 图案（代尔夫特常见题材，坐标都是画布像素）：`windmill(x, 地面y, 轮毂高, sails, squash, cloth)` 带回廊的罩式风车（squash < 1 让风叶转向左前方）；`sailboat(船尾x, 水线y, 船长, facing, belly, cargo, skipper, pennant, leeboard)` 平底帆船（斜桁主帆、前帆、披水板、桅顶三角旗、货袋、舵手），返回船体轮廓；`house(x0, x1, 地面y, 墙高, gable='step'|'bell'|'neck'|'spout', gable_h, floors, chimney, smoke=(dx, dy), vane=-1, shade='right')` 运河屋（十字窗、门、吊货梁、砖缝短线、烟、风向鸡）；`tree(x, 地面y, h, w, lean, clumps)`；`bushes(x0, x1, y, h, gap)` 地平线上的远树；`tulip(x, 地面y, h, lean)`；`cloud(cx, cy, w, h, lean)`；`birds([(x, y), …])`；`water(x0, x1, y0, y1, far, near, avoid)` 远密近疏的水纹；`reflection(x, 水面y, w, depth)`；`grass()`；`smoke()`；取点工具 `arc()`、`ellipse_pts()`
- 单块砖：`field(tiles=None, corners='spin'|'lelie'|'dot', medallion=True, motifs)` 给砖画以外的每块砖画四角的四分之一角饰、双圈圆框和小图（'tulip' 'ship' 'mill' 'boat' 'fish' 'bird' 'house' 'pot'，和左、上邻砖不重复）；也可以单独用 `corner()`、`medallion(i, k)`、`vignette(i, k, kind)`
- 边框：`border(rect, band, inset, tone, leaf, reserve=[卷轴形状])` 砖画外一圈蓝边框：藤蔓、叶子、浆果留白，四角玫瑰花，reserve 给题字卷轴留白
- 工序：`fire()` 入窑（灰黑颜料变钴蓝、釉面变亮、颜料洇开带颗粒、粉印烧掉、每块砖钴蓝浓淡不同）；`set_wall()` 石灰浆勾缝；`age(craze, chips, specks, nails, cracks=[点列])` 开片、铁斑和针孔、崩瓷、四角裁坯模板的钉孔、只在一块砖里的裂纹；`light(window=(x, y, w, h), strength=0.5, panes=(2, 3), soft=8)` 窗户在釉面上的倒影，x, y 是墙面完全平整时倒影所在的位置；倒影按滤色叠在釉面上，画面透得出来；放在画了东西的地方（云、边框）才看得出，纯白釉上几乎看不见
- `stage(name, hide)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度
- 常量 `COBALT_K`（烧成的钴蓝吸收系数）、`RAW_K`（生颜料）、`GLAZE_COOL GLAZE_WARM RAW_GLAZE MORTAR BED BODY`

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 钴蓝像荧光宝蓝，一看就是屏幕色 | 按 Beer–Lambert 逐通道吸收算颜色，k = (2.3, 1.95, 0.95)：淡染是灰蓝，浓线是紫藏青（`COBALT_K`） |
| 窗户倒影是一团闪烁的白碎点、边缘起毛，看不出是窗户 | 去掉小尺度橘皮纹，釉面起伏只留约 46 px、幅度 ±0.15 px 的缓波，再加每块砖的鼓起（±0.3 px）和倾斜；窗棂宽度要大于高光柔化宽度（soft 3.5），否则窗格糊成一片白 |
| 高度场求导把 x、y 写反，倒角打光和倒影按错的轴偏移 | `np.gradient` 返回的是 (d/dy, d/dx)，要写 `hy, hx = np.gradient(h)` |
| 开片满墙都是，像碎冰 | 每块砖的开片量取 Beta(1, 2.6)，线只压暗 13%，多数砖几乎看不见 |
| 一条裂纹穿过好几块砖，像钢笔线 | 裂纹按砖编号裁剪，只在一块砖里、到砖缝就停；只压暗 50% |
| 砖缝 5 px 太宽，整面墙像浮雕网格 | 砖缝 3.6 px（13 cm 砖约 3–4 mm），倒角 3.4 px、高 1.3 px |
| 云是一块扁长方形 | 云是一串圆凸起的上包络：左高右低（风从左来），每个凸起单独一笔、凸起之间留尖角；底线断成两三截，晕染从底边往上变淡 |
| 树冠像一串气球、花椰菜 | 只描外轮廓的扇贝边；里面在背光一侧画两圈缩小的扇贝短弧；第二遍晕染用渐变，不要每团一个月牙 |
| 船上的面粉袋像一排舷窗；披水板像挂着的布袋 | 袋子坐在甲板上、只描上半圈和扎口；披水板画成上窄下宽的扇形木板，先画并 `occlude`，船身排线不穿过它 |
| 远处的树林像一排鸡蛋；烟像电线 | `bushes()`：地平线上一簇簇小扇贝丘配淡晕染；烟是一串越来越大、越来越淡的卷 |
| 人像穿裙子的小孩，狗像腊肠 | 人：头发和发梢往前飘、张嘴、翻袖口、马裤、长袜、带扣鞋，上身前倾、后脚踢起；狗：四脚离地的飞扑，耳朵和尾巴往后飘，背上一块深色斑，不排线（排线像斑马纹） |
| 晾的衣服垂着不动，看不出有风 | 床单、衬衫的下摆几乎水平地往右扬，挪到近岸空地上，不要藏在树后 |
| 窗户倒影放在右侧单块砖上，是几块纯白、边缘锐利的碎片，远看像砖掉了或渲染出错 | 倒影改成按「滤色」叠在釉面上（`img + (白 − img) × s`，s 最大约 0.65），最亮处底下的蓝线仍透出来；柔化宽度 6、窗格缩小到 112 × 150；挪到画面里右上那朵云和天空上，跨两三块砖，在砖缝处断开错位，一眼看出是釉面反光 |
| 崩瓷是几个橙色小点，像锈斑 | 半径 5–11 px，露出灰褐坯体（`BODY`），靠光一侧被釉边投影、背光一侧的坑壁亮 |
| 动图 3.4 MB | 调色板样本里蓝色像素 ×3；和屏上已显示颜色相差 ≤ 10/255 的像素记透明 → 1.7 MB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
