# 彩色玻璃花窗（stainedglass）

- **实现**：`lib/stainedglass.py` · `StainedGlass`
- **范例**：`examples/stainedglass_seasons.py` 四季之窗 · Window of the Seasons（石墙上四扇哥特尖拱窗，同一棵树的春夏秋冬：春花与燕子、夏天的苹果和一窝雏鸟、秋天金红树冠和离开的雁阵、冬天积雪的枝和知更鸟，太阳高度随季节变；VER / AESTAS / AVTVMNVS / HIEMS 银染题字带；铅条与焊点、横铁条、一处补过的裂片，窗侧斜面和窗台上的彩色光）
- **耗时**：约 4 秒
- **内部构成**：彩色玻璃花窗（玻璃切块、grisaille 彩绘与银染、铅条焊点、透光）

## 何时选用

教堂、中世纪、哥特、庄严而温暖的透光，节日与季节，「一年四季 / 时间流转」的分格叙事，讲解片里的「历史 / 传统工艺」页 → 彩色玻璃花窗（要现代霓虹发光用赛博朋克）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from stainedglass import StainedGlass
```

- 思路：照玻璃匠的工序——画稿分块 → 选料切玻璃 → grisaille 彩绘、刮白、银染 → 上铅焊接 → 装铁条 → 从室内看日光透进来。颜色全在玻璃里，颜料只有一种棕黑；铅条落在每两块玻璃的交界上
- 构造：`StainedGlass(W, H, seed, record=True, ambient=0.05)`；`stage(name, cartoon=False)`（cartoon=True 出纸上的切线画稿）；`save(path, stages_dir)`
- 石墙：`wall(colour, mortar, course, block)` 错缝方石墙（每块石料深浅不同、斜向凿痕、磨损的棱、凹进的灰缝）；`lancet(cx, top, bottom, width, arch=1, splay, sill, hood)` 开一个尖拱窗洞，返回 `Light`，带斜面窗侧（拱上是放射状楔石缝）、斜窗台、拱上的滴水线脚；`string_course(y, h)` 腰线
- `Light`：`pt(lx, ly)` / `P(点列)` 把局部坐标（原点在拱尖，y 向下）换成画面坐标；`inner(b)` 向内缩 b 的窗形遮罩；`band(b0, b1)` 沿窗边的一圈带（边框、白条）；`outline(b, step)` 沿窗边取点（给边框切块）；`sdf()`；`half(ly, b)` 某高度的半宽
- 玻璃：`glass(遮罩, 颜色或颜色列表, cell, streak, seeds, thick, vary, flashed, aspect, angle, around, spokes, sites, streak_dir)`。颜色是透光时的样子；给 cell 就按 Voronoi 切块，每块从列表里取一种颜色、深浅厚薄各不相同；sites 按给定点切（边框、长条）；aspect / angle 把块拉长；around 绕一点放射切；flashed 是红色套料那种强条纹。后铺的料从先铺的里切出来；太小太窄的碎块自动并进同料的邻块。`cut(点列)` 加一道切线
- 遮罩：`circle()`、`ellipse()`、`poly()`、`blob()`、`branch(点列, 起宽, 止宽)` 渐细的枝
- 彩绘：
  - `trace(点列, width, taper, opacity, clip)` 不透明描线（五官、叶脉、羽毛、细枝），clip 限定只画在某个遮罩里；
  - `matt(遮罩, strength, soft, stipple)` 半透明晕染，带点彩颗粒；`shade(遮罩, offset, strength, clip)` 背光一侧的月牙形 matt；
  - `scratch(点列, width)` / `scratch_mask(遮罩)` 用木签刮掉颜料，让光透出来；
  - `diaper(遮罩, spacing, motif='cross'|'dot'|'ring'|'flake'|'quatrefoil', jitter)` 底纹，默认从一层薄 matt 里刮出，jitter 撒开就是雪花；
  - `stain(遮罩, strength)` 银染：白料变柠檬黄到琥珀，蓝料变绿；
  - `inscribe(字, x, y, size, font='lombardic', scratched)` 题字（Luminari / Herculanum，可用 `INKPAINT_FONT_LOMBARDIC` 指定）
- 上铅与铁件：`lead(width=6, rim=10, solder=True)` 在每条交界上铅（按 H 形铅条打光，焊点更亮更鼓，窗边一圈宽铅）；`crack(点列, mend=True)` 裂片和修补用的细铅条，要在 `lead()` 之前；`saddle_bar(light, y, width)` 横铁条（y 是画面坐标），两端插进石头，扎几处铜丝结，要在 `lead()` 之后
- 光：`weather(grime, pits)` 铅条边和窗下部积灰、部分玻璃的腐蚀麻点；`daylight(strength, spill, halation, sky)` 打开室内光：墙上一层彩色溢光、窗侧斜面靠玻璃处发亮、斜窗台上倒过来的模糊投影、亮玻璃的光晕吃掉一点铅条（蓝色最明显）。`daylight()` 之前墙用固定的中性光，阶段快照之间石墙不变
- 颜色常量 `RUBY BLUE DEEP_BLUE SKY GREEN LEAF SPRING OLIVE GOLD AMBER ORANGE MURREY WHITE PALE BROWN FLESH`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 铅条像半透明的灰色铅笔线 | 光晕叠到铅条上只留约两成，铅的颜色压到 #2c2d31 左右（已处理） |
| 同一道条纹横穿相邻几块玻璃，像盖了一层滤镜 | 每块玻璃取自整张料的不同位置：条纹按块加随机相位，方向也按块随机（已处理） |
| 树冠每个圆团单独一块料，铅条围出一圈圈圆，像肥皂泡、像葡萄 | 整个树冠用一次 `glass()`（多种绿随机分给各块），团块的体积靠彩绘：背光侧月牙 `shade`、下缘一串扇贝形描线、受光侧从 matt 里刮出叶形 |
| 小叶子用描线勾轮廓，缩小后成了一团乱线 | 暗部画实心叶片（不透明度约 0.8）再刮出叶脉；亮部从 matt 里刮出叶形 |
| 细枝也切成玻璃，两条铅夹一道棕线像梯子；冬树成了一个「Y」 | 玻璃只切树干和宽 16 px 以上的大枝，大枝要弯；更细的枝和小枝用 `trace` 画在天空上 |
| 太阳周围另切一圈放射块，外沿多出一道圆形铅条 | 区域交界一定是铅条：同一片天空只用一次 `glass()` |
| 燕子像喷气式飞机 | 用从下往上看的雨燕剪影：镰刀形后掠弯翼、短身、深叉尾 |
| 横铁条正好横穿知更鸟的头和鸟巢 | 先定铁条高度（范例是 286 / 490 / 694），鸟、巢、太阳、字都避开 |
| 每个铅条交叉处都扎一个铜丝结，铁条像一排缝线 | 每根铁条只扎几个小结（已处理） |
| 题字带从中间切开，铅条正好穿过字 | 短题字的饰带用一整块料 |
| 树干被切成一节节竹子 | 树干和大枝用竖向拉长的块（`aspect=1.8, angle=π/2`） |
| 秋天透过树冠的画枝和画的叶子拼成像字母的黑块 | 画枝只画在露出天空的地方（`trace(..., clip=)`） |
| 上铅之后整扇窗发暗发闷 | 铅条下面的玻璃压暗只做 4.5 px、0.22（已处理） |
| 带 `--stages` 和不带出的图不一样 | 渲染时才生成的噪声和气泡改用构造时就定好的种子，阶段快照不再挪动随机序列（已处理） |
| 动图 3.3 MB：每个阶段墙面溢光都跟着窗变，整面墙在每次叠化里重编码 | `daylight()` 之前墙用固定的中性溢光；叠化帧里色差 ≤ 18（关键帧 ≤ 6）的像素沿用上一帧（1.8 MB） |
| 小形状也开整幅数组做模糊和遮罩：44 秒、1.6 GB | `matt / shade / circle / ellipse / poly / saddle_bar / lancet` 都只在包围盒里算（约 4 秒、约 1 GB） |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
