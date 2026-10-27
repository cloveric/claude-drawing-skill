# 暮色微缩绘本（twilight）

- **实现**：`lib/twilight.py` · `TwilightStorybook`
- **范例**：`examples/twilight_paper_kite.py` 夜的边上 · The Kite at the Edge of Night（2000×1100 的一页黄昏绘本：一个穿蓝色毡子斗篷、软帽尖带绒球、圆脸点点眼、戴黄手套的原创小角色坐在野花坡顶上，把一只纸风筝放向天空入夜的地方；左边是粉彩黄昏：薰衣草紫、玫瑰、蜜桃、暖金，柔和的云带、细细的光线，一轮淡日正落到雾紫色的远山后面，一群飞鸟、几颗飘着的蒲公英种子；右边已经入夜：满天星、带暗带的银河、弯月、一颗流星，远山上一间小屋亮着一扇窗；中间是粉彩条纹的拼布山丘和小圆树，前景几万朵野花，入夜的一侧变成月光蓝，坡顶衬着天空几丛带穗的高草，花间有蝴蝶和蜻蜓；角色身边一罐萤火虫照亮一圈草，萤火虫往暗处飘；天空中间一个圆形「detail a」放大图，引线连到风筝上，用细技术图的画法画风筝骨架交叉处的绑扎和提线结（排线、ø 6 标注、标签、比例尺）；两行小写手写字「the evening waits for us.」「just a little further.」；照顺序画：黄昏天空 → 夜 → 山 → 花坡 → 角色和风筝 → 萤火虫 → 图版和手写字；`--stages` 出 6 个阶段加成品：黄昏天空、夜、山、花坡、角色和风筝、萤火虫）
- **耗时**：约 2 秒
- **内部构成**：暮色微缩绘本（被噪声扰动成软层的六段黄昏渐变、透镜形云带、光线和淡日；羽化的夜度场：按它铺夜空、银河、星星和月亮，交界补饱和度，后面受光的东西按它压成月光蓝，发光的东西不受影响；解析的银河带和暗带、幂律星场、亚像素溅射、四芒星、弯月、流星；远山、拼布条纹山丘、细垄、树篱、小圆树；按透视拒绝采样的花坡：八种花和草叶，按根部排序一次光栅化进 id 图；小斗篷角色、萤火虫罐、风筝和随天色变色的风筝线、萤火虫、蝴蝶、蜻蜓、蒲公英种子、飞鸟、带穗高草；3 倍图上的细墨线、排线、尺寸标注、比例尺、淡彩、圆形放大图；逐字母抖动的手写小字；柔化、光晕、颗粒、暗角、撕纸边）

## 何时选用

温柔、怀旧、带一点点孤独的小故事和情绪（「一天结束了」「出发」「再走一点点」），晚安故事、童书封面和插页，季节和节日的夜晚（夏夜、萤火虫、星空、七夕、中秋），原创小角色或吉祥物的「远方」主视觉，要在一张画里同时放「风景 + 一个零件 / 一个结 / 一处构造的放大图 + 手写小字」的讲解页 → 暮色微缩绘本（要软蓝限色、乱线墨线的绘本跨页用蓝调绘本；要真的动起来的小角色用绘本角色动画；要赛璐璐天空和夏日少年感用日本动漫；要大片松散晕染的风景用水彩；要整页的机械分解手稿用达·芬奇手稿）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from twilight import TwilightStorybook
```

- 思路：照绘本的顺序画：黄昏天空 → 夜 → 山 → 花坡 → 角色和风筝 → 发光的东西 → 图版和手写字；先定一块「夜度」场，后面受光的东西都按它着色。
  - 黄昏天空：六段渐变（薰衣草紫 → 丁香 → 玫瑰 → 蜜桃 → 杏 → 金，按地平线定位），分段位置被横向拉长的低频噪声扰动，颜色是一层层软的，不是尺子拉的直色带，再叠几个百分点的细斑驳。云是透镜形的带：一条扁透镜加几团圆块（中间高），轮廓模糊，底部更平更清，越往下越浓，半透明；云下有细光线；太阳是带两层光晕的淡圆，先于山画，山把它切掉。
  - 夜：`night_split()` 由一条游走的边界线定出整幅画的夜度场 N（0 黄昏 – 1 夜），过渡带很宽、带羽化；夜空渐变、银河、星星、月亮都按 N 当透明度铺上去，星星越过边界慢慢变稀、变淡，不会停在一条线上；靠近边界时夜色偏靛蓝，交界带再补饱和度（`richness`），黄昏 → 淡紫 → 靛蓝 → 黑，不发灰。
  - 之后所有「受光」的东西（山、花草、人物）都按同一个 N 着色：颜色经一个 3×3 线性变换（先降饱和、再偏冷）按 N 混过去，白雏菊在夜的一侧成了淡淡的月光蓝，草成了深石板色。自发光的（星星、萤火虫、灯、流星）和图版放在 `with t.unlit():` 里画，不受影响。
  - 银河：两点之间、带弯曲和游走中心线的解析带，密度是横截面的高斯 × 两个尺度的云状噪声，中间一条更窄的暗带；几千颗暗星按带的密度抽样。星星：均匀位置、幂律亮度（多数暗、少数亮），少数偏暖或偏蓝，亚像素精度地溅到画布上（大星用圆盘覆盖核，小星用保质量的高斯，bincount 累加）；最亮的几颗加四芒星（长的渐细光芒加短对角线），只放在夜深处、离地平线远的地方。
  - 山：远山是填充的山脊（每列解析抗锯齿的边），越往山脚越淡（谷里积雾）；条纹山丘是顺着山脊的一层层带，越近越宽（透视），每条带切成斜的拼布田，部分田有平行的细垄，带与带、田与田之间一道深一点的树篱线，坡顶一道淡亮边；`trees()` 放小圆树（影子、树干、树冠、左上亮面）。
  - 花坡：地面是鼠尾草绿到橄榄绿的渐变加斑驳和细点，坡顶一道亮边（越过交界从金变银）。花和草按透视用拒绝采样放：大小随离坡顶的深度按幂次增长（默认 t²），密度 ≈ 覆盖率 / (π · 大小²)，所以坡顶是几千个色点、最底下是几十朵大花；花种按低频噪声成片漂移（一片雏菊、一片矢车菊）；远处的花沉进带雾的地色。按大小是一个色点、一朵带花心的小花或一朵完整的花头（雏菊、矢车菊、虞美人、波斯菊、金盏花、毛茛、羽扇豆、勿忘我），各有细茎，大的带一片叶；花头按透视压扁，朝后的花瓣先画。所有多边形按根部的 y 排序，一次光栅化进超采样的整数 id 图（画家顺序 = id 顺序），查色表再缩回来，几万个抗锯齿形状不到一秒。
  - 角色：扁平可爱的绘本角色，用平滑多边形拼：`wanderer()` 是坐着的小斗篷角色（毡子质感的斗篷、软塌的帽尖和绒球、奶油色圆脸、带高光的点点眼、腮红、手套和靴子，夕阳一侧一道暖色柔边，一圈断续的深色细轮廓）；`jar_lantern()` 是一罐萤火虫，会发光、照亮周围的草；`kite()` 四片的菱形风筝，有骨架、提线和一串蝴蝶结尾巴；`kite_string()` 略下垂，跟着身后的天空从深（黄昏）变银（夜）。`fireflies()`、`butterfly()`、`dragonfly()`、`seeds()`（蒲公英种子）、`birds()` 是留给细看的小东西。
  - 图版：细墨线在 3 倍图上画成折线（略带手抖、可渐细）再缩回来，0.8 px 的发丝线也是平滑的；`hatch()` 在形状里排平行的手绘线（换个角度再调一次就是交叉排线），`dimension()` 画延伸线、带建筑式斜短线的尺寸线和小标签（`across=True` 横跨一根伸出画外的杆件，引到外面写「ø 6」这类），`ruler()` 小比例尺，`wash()` 平的水彩底色加一道深边；`inset()` 是圆形放大图：带淡阴影的纸圆片、裁在里面的 `draw(t, cx, cy, r)` 回调、细双圈、目标上的标记圈和引线、标签。
  - 手写字：细手写体（macOS 上是 Noteworthy Light，或设 `INKPAINT_FONT_HAND_LIGHT`）逐个字母排：每个字母各有一点旋转、基线起伏、间距和轻重，在 2 倍图上画再缩小，叠一层淡淡的铅笔纹。
  - 收尾 `finish()`：轻微柔化、亮处光晕、细颗粒加大一点的柔和斑驳、偏梅紫的淡暗角，可选底边一道米色撕纸边；只记参数、在 render 里加，所以在画第一笔之前调用，每张阶段快照都和成品一致。
- 构造：`TwilightStorybook(W, H, seed, keep_stages=True, stages_dir=None)`（总像素不超过 4096²）；`with t.clipped(mask):` 只画在遮罩里（放大图里面），`with t.unlit():` 不受夜度着色。画布坐标是像素；角度除注明外用弧度（`hatch()` 用度）。
- 底层：`lines(paths, width, colour, alpha, wobble, taper)`；`fill(mask, colour, alpha)`；`shapes(polys, colours, alpha)`；`poly(pts)`、`ellipse(cx, cy, rx, ry)` 返回遮罩；`glow(x, y, r, colour, strength)`；`splat(xs, ys, rad, colours, alpha)`。
- 天空：`dusk_sky(stops, horizon, mottle)`；`cloud(x0, x1, y, h, colour, alpha)`；`streak(x0, x1, y)`；`sun(x, y, r)`；`mist(y0, y1, y2, colour, strength)`；`birds(pts, size)`；`seeds(pts, size)`。
- 夜：`night_split(edge, soft, ground)`（edge 是从上到下的折线，夜在它右边；在 `dusk_sky()` 之后调）；`night_sky(top, low, indigo, richness)`；`milky_way(p0, p1, width, bend, rift, stars)`；`stars(n, region, sparkles, dusk)`；`sparkle(x, y, size)`；`moon(x, y, r, phase, tilt)`；`shooting_star(p0, p1)`。
- 地面：`hills(ridge, colour, base, fade, rim)`；`striped_hill(ridge, colours, stripe, grow, fields, rows, hedge)` 返回 info（ridge、bounds，用来放树）；`trees(pts, size)`；`meadow(crest, size, density, grass, kinds, drifts, haze)` 返回 info（crest）；`grass_heads(x0, x1, base, n, height, lean)` 坡顶衬着天空的带穗高草。
- 角色和小东西：`wanderer(x, y, s, facing, reach)` 返回手的位置；`jar_lantern(x, y, s)`；`kite(cx, cy, size, tilt, tail)` 返回提线结的位置；`kite_string(p0, p1, sag)`；`nightline(path, width)` 跟着天色变色的细线；`fireflies(pts, size, trails)`；`butterfly(x, y, s, colour)`；`dragonfly(x, y, s)`。
- 图版和字：`hatch(shape, angle, spacing, width)`；`dimension(p0, p1, text, offset, across, lead)`；`ruler(x0, y, x1, labels)`；`wash(pts, colour)`；`leader(p0, p1)`；`inset(cx, cy, r, draw, target, label, sub, leader_colour)`；`caption(x, y, text, size, colour, anchor, rot)`。
- 收尾：`finish(grain, vignette, bloom, soft, edge)`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。
- 颜色用 `COLOURS` 里的名字（天空 lavender lilac rose peach apricot gold sun cloud cloud_low streak；夜 night night_low indigo star moon milk；地面 mauve mauve_dark haze rim silver meadow meadow_far meadow_near grass tree tree_light trunk field_sage field_lav field_wheat field_green field_rose；线和纸 ink pencil caption paper pale；花 daisy cornflower poppy cosmos marigold buttercup lupine forgetmenot eye stem；角色 cloak cloak_dark face cheek boot mitten kite kite_cream spar string lantern firefly glass）或 '#rrggbb'；花种见 `SPECIES`。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 第一版天空里漏出 NaN | 云的包络 `sin(πu)` 在两端略小于 0，再开 0.55 次方：先截到 0..1 |
| 云是一条条细线 | 重写成透镜形：一条扁透镜加 4–5 团圆块（中间高），轮廓模糊，底部更平更清，上浅下浓 |
| 昼夜交界是一片灰雾 | 交界带补饱和度（`richness`），夜空靠边界的一侧偏靛蓝（靛蓝提亮），边界羽化的噪声尺度 90 → 170、幅度减半：黄昏 → 淡紫 → 靛蓝 → 黑 |
| 补了饱和度以后，交界成了一堵霓虹紫墙 | `richness` 0.9 → 0.5，靛蓝压回一点 |
| 昼夜边界是一条直的斜线 | 边界折线改成六个点的弧（夜像穹顶一样压过来），过渡带 150 → 185 px |
| 天空的薰衣草紫太深太艳，云融进天里 | 六个色标都提亮、降饱和；云色压暗一点，云顶往浅色混的比例 0.4 → 0.22 |
| 银河的暗带太弱 | 加一个更亮更窄的内核，暗带收窄、加深（`rift` 0.65 → 0.8）；交付时银河仍偏烟雾、暗带仍比参考图弱 |
| 四芒星太多、太大，靠近交界和地平线也有 | 9 颗 → 6 颗，大小 9–17 → 7–13 px，只放在夜度 > 0.8、离地平线 180 px 以上的地方 |
| 远处坡顶的花是一条又密又亮的带 | 覆盖率改成越远越低（0.24 + 0.32 t，t 从坡顶 0 到底边 1），远处的花沉进带雾的地色（`haze`） |
| 风筝在深夜里，被夜度着色压成了灰蓝 | 风筝挪进交界带，珊瑚色才保得住 |
| 角色夕阳一侧的边光是灰的；改暖以后又成了一道硬的棕色带 | 边光用暖杏色，从轮廓往里 3 px、模糊 1.4 px、最多 0.6，越往下越淡 |
| 放大图的目标标记圈落在珊瑚色风筝上看不见 | 标记圈和引线固定用深墨色（`leader_colour`） |
| 放大图的标签越出圆片，尺寸数字压在线上 | `dimension()` 的数字按字的「上方」放到背离物体的一侧；横跨杆件的「14」还撞上提线：去掉，改成 `across=True` 的「ø 6」直径标注，引到杆件外面写 |
| 拼布条纹田像一面面旗 | 田的颜色降饱和、彼此更接近，山脊起伏加大，树篱线 0.45，底部渐隐 |
| 阶段快照没有颗粒、暗角和撕纸边，和成品对不上 | `finish()` 只记参数、在 render 里加，改到画第一笔之前调用 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
