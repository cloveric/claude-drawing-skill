---
name: claude绘图
description: Claude 绘图 / Claude Drawing —— 不借助任何生图模型，由 Claude 用代码一笔一笔「画」出图片（程序化绘画）。内置九种画风：中国水墨、水彩、剪纸拼贴、韩国彩铅、日本动漫、编辑风手绘（Riso）、油画厚涂（梵高式流向笔触+颜料浮雕打光）、浮世绘木版画（晕色、木纹、墨线主版、青海波）、像素风（低分辨率+Bayer 抖动+像素字体）。用户说「claude绘图」「用代码画」「你自己画」「不用生图模型画」「程序化绘画」，或点名以上任一画风，或 "draw it yourself", "paint with code", "procedural painting", "watercolor / collage / colored pencil / anime / editorial / impasto oil / ukiyo-e / pixel art without an image model" 时使用；也用于需要逐步画出（draw-on）动画的插画。
---

# Claude 绘图

用 Python（只依赖 numpy + Pillow，系统自带的 `python3` 就能跑）按笔、墨、颜料、纸的物理规律「画」图，不调用任何生图模型。
- **构图可控**：每一笔都是算出来的，构图、留白、点睛色的位置都精确可控。
- **结果可复现**：固定随机种子，每次画出同一幅画。
- **适合做动画**：可以输出分阶段快照，做成「一幅画被逐步画出来」的动画；生图模型只能给一整张画。

## 画风与范例（质量基准）

| 画风 | 库 | 范例 | 耗时 |
|---|---|---|---|
| 水墨 | `lib/inkpaint.py` · `Painting` | `examples/bawansiqian.py` 八万四千法门；`examples/moon_river.py` 月印万川（烘云托月、孤舟、芦苇） | 约 4 秒 |
| 水彩 | `lib/watercolor.py` · `Watercolor` | `examples/watercolor_autumn.py` 秋日湖畔（秋树罩染、湖面倒影、红色小舟） | 约 15 秒 |
| 剪纸拼贴 | `lib/papercut.py` · `Collage` | `examples/papercut_balloons.py` 热气球小镇（条纹热气球、笑脸太阳、纸云、小房子） | 约 30 秒 |
| 韩国彩铅 | `lib/colorpencil.py` · `ColorPencil` | `examples/colorpencil_dessert.py` 午后甜点（草莓蛋糕、红茶、草莓） | 约 17 秒 |
| 日本动漫 | `lib/anime.py` · `Anime` | `examples/anime_summer.py` 夏空（积雨云、乡间公路、电线杆、草帽女孩背影） | 约 30 秒 |
| 编辑风手绘 | `lib/editorial.py` · `Editorial` | `examples/editorial_ideas.py` 灵感生长（浇水长出灯泡的概念插画） | 约 11 秒 |
| 油画厚涂 | `lib/oilpaint.py` · `OilPainting` | `examples/oil_wheatfield.py` 麦田星空（旋转的星空、麦田、柏树、乌鸦） | 约 2 秒 |
| 浮世绘木版画 | `lib/ukiyoe.py` · `Ukiyoe` | `examples/ukiyoe_fuji.py` 富士曙（晕色天空、富士、云带、青海波、帆船、崖松） | 约 7 秒 |
| 像素风 | `lib/pixelart.py` · `PixelArt` | `examples/pixel_rainy_cafe.py` 雨夜咖啡店（霓虹、路灯、雨、倒影、猫） | 约 0.1 秒 |

各画风共用 `lib/core.py` 里的底层工具：噪声、模糊、样条曲线、多边形遮罩、有机轮廓 `blob_pts`、毛笔 `bristle_stroke`、中文字体查找。

**用户没有指定画风时怎么选**：
- 禅意、古典、山水 → 水墨；
- 清新风景、花卉 → 水彩；
- 童趣、温暖、讲故事 → 剪纸拼贴；
- 甜点、小物、日常可爱 → 韩国彩铅；
- 青春、夏日、天空、背景美术 → 日本动漫；
- 观点、概念、商业文章配图 → 编辑风手绘；
- 浓烈、有笔触质感、名画感 → 油画厚涂；
- 日式古典、海浪、富士、东方装饰感 → 浮世绘；
- 复古游戏、夜景霓虹、小尺寸动画 → 像素风。

每种画风一幅范例作为质量基准；水墨另加一幅「月印万川」（留白托月、水面倒影）。

## 一、流程（每幅画都照做）

1. **定构图**，动笔前先想清楚这几项：
   - 层次：远 → 中 → 主体 → 前景；
   - 视觉焦点在哪里；
   - 留白够不够：水墨至少四成，水彩和剪纸也要有呼吸感；
   - 点睛色只用一两处：水墨用朱红，剪纸用一个亮色主角；
   - 题字或纸条放在哪里。
   - **画面要图解内容本身**，而不是随便一幅风景。
2. **写场景脚本**：复制最接近的范例改写。
3. **渲染并自己看图**：`python3 scene.py out.png`。
   - 用 Read 打开 PNG，对照第三节该画风的毛病清单逐条自查；
   - 一般改 2–4 轮，每轮只改最显眼的问题，旧版存成 `_v1/_v2` 以便对比。
4. **交付**：转成 JPG（quality 92），用当前对话渠道支持的方式发图。
   - 要做动画时加 `--stages DIR`，按 `stage('名字')` 输出各阶段快照。

## 二、接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask
```

**水墨 `Painting`**：
- `paper()`、`ridge(base, peaks=[(x,h,w)])`、`peak(SX, SY, shoulders=...)`
- `wash(ridge, dens, decay, tex, edge, mist_y)`：墨染山体，上浓下淡、带水痕边，会遮挡后面的层
- `cun()` 皴擦、`moss()` 苔点、`ridge_line()` 淡山脊线、`trails(ridge, summit, red_index)` 汇顶小路、`mist(y, h)` 雾带
- 毛笔 `stroke(pts, width, ink, dry, taper, red)`
- 物件：`pine()`、`rock()`、`sun()`、`birds()`、`pagoda()`、`traveller()`、`dot()`
- 题字印章：`title_vertical()`、`seal()`

**水彩 `Watercolor`**：
- `paper()`：冷压水彩纸纹理
- 遮罩：`shape(pts, soft, ragged)`，soft 取 1–4 是清晰的水痕边，15–40 是湿画晕开；`band(pts, width)` 是粗笔带状遮罩
- `glaze(mask, 颜色, strength, edge, gran, bloom, variation)`：透明罩染，叠加会像真颜料一样变深、混色
- `gradient_wash(y0, y1, top, bottom)`：湿画渐变天空
- 笔触：`stroke()` 彩色干笔、`line()` 细线勾勒、`lift(mask)` 提白、`splatter()` 甩点
- `soften(mask)` 任意遮罩水彩化边缘；`blobs([(cx, cy, rx, ry)])` 一组团块合成一片（树冠、灌木、云）；`mirror(mask, 水线y)` 水面倒影（带波纹断续）
- `Watercolor.petal_pts(x, y, 角度, 长, 宽)`：花瓣或叶片轮廓；`hexc('#rrggbb')` 转颜色

**剪纸 `Collage`**：
- `background(颜色, texture)`
- `piece(pts 或 mask, 颜色, texture, torn, rim, shadow)`：贴一张纸。torn 是撕边程度，rim 是撕口白边，shadow 是纸片阴影；texture 可选 paper / kraft / crayon / newsprint / notebook
- 形状遮罩：`circle_mask()`、`cloud_mask()`、`Collage.star_pts()`
- 蜡笔和光：`crayon(pts, width, 颜色)` 蜡笔线、`dot()`、`glow()`
- `face(cx, cy, r, mood='smile'|'sleep'|'dots')`：笑眼、嘴、腮红
- `text(s, x, y, size, 颜色, vertical)`

**韩国彩铅 `ColorPencil`**：
- `paper()`：细纸纹
- 遮罩：`mask_poly(pts)`、`mask_blob()`、`mask_ellipse()`
- `hatch(mask, 颜色, pressure, angle)`：短排线铺色。蜡只挂在纸纹凸起上，pressure 越大越能压进凹处；边缘自动变淡
- `shade(mask, 颜色, angle=另一个角度)`：交叉排线加阴影
- `outline(pts, '#8a6a5a')`：浅褐色铅笔勾线；`line(pts)` 用于不闭合的线
- `sparkle(x, y, r)` 白色高光笔；`dots(mask, 颜色)` 草莓籽、糖粒之类
- 白色物体不要用白色画（白纸上看不见）：用暖奶白色，配淡紫灰或淡蓝灰阴影

**日本动漫 `Anime`**：
- `sky(top, mid, horizon_col, horizon)`：天空渐变
- `cumulus(cx, base_y, w, h, light)`：积雨云。许多不规则团块从后往前叠，每团的暗面是「团块减去朝光源偏移的自身」形成的月牙形硬边
- `sun_flare(x, y)`：光晕、光束、镜头光斑；`sparkles()`；最后加 `bloom()` 泛光和 `vignette()` 暗角
- `field(top_y, colours)`：平涂分带的田野；`pole()` 电线杆、`wire(p0, p1, sag)` 下垂电线
- 平涂和线稿：`fill(mask, 颜色)`、`gradient()`、`screen()`；`lines(pts, width, 颜色)` 画干净线稿；`poly()`、`circle()`
- 角色：平涂两色（亮色和阴影色）加深色描边

**编辑风手绘 `Editorial`**：
- 形状：`circle()`、`ellipse()`、`rrect()` 圆角矩形、`blob()`、`poly()`
- `fill(mask, 专色)`：印一层专色油墨，带颗粒、浓淡不匀、套色错位，并**叠印**（重叠处颜色相乘）
- `halftone(mask, 专色, cell, angle, amount)`：半调网点做明暗
- `line(pts, 墨色, width, wobble, breaks)`：歪扭的手绘墨线；`dashes()` 虚线；`stars()` 小十字星
- 专色控制在 4–5 种，并刻意让它们互相重叠，叠出第三种颜色

**油画厚涂 `OilPainting`**：
- 先准备两张图：参考色 `ref`（H×W×3，画面要画成什么颜色）和流向图 `ang`（H×W，每个像素上笔触的角度，比如天空打旋、麦田横扫、树木向上）
- `layer(ref, ang, length, width, density, mask)`：铺一层笔触。先大笔铺底，再中笔，最后只在要紧处（`mask`）加细节笔
- `stroke_at(x, y, angle, length, width, 颜色)`：在指定位置画一笔（乌鸦、签名、点睛）
- `render()` 自动打光：颜料平顶鼓边、有笔毛沟，落笔处更厚

**浮世绘 `Ukiyoe`**：
- `block(mask, 颜色)`：印一块平涂色版，带木纹和套印偏移
- `bokashi(mask, 颜色, y_strong, y_fade)`：晕色，从某一边浓到另一边消失，用于天空和海面
- `key(pts, width)`：墨色主版勾线
- 物件：`cloud_band(x0, x1, y, h, glow)` 不透明云带、`seigaiha(mask, 颜色, r)` 青海波纹
- 标题签和朱印：`cartouche(x, y, w, h, '标题')`、`seal()`
- 形状：`poly()`、`rect()`、`circle()`

**像素风 `PixelArt`**：
- 在低分辨率上画（默认 320×180，放大 6 倍）。坐标都是整数像素
- 画形状：`rect()`、`poly()`、`circle()`、`line()`（Bresenham 直线）、`outline(mask)`、`put(x, y)`
- 抖动：`gradient(x0, y0, x1, y1, c0, c1, steps)` 分带渐变，带与带之间用抖动过渡；`dither(mask, 颜色, alpha)` 按 Bayer 矩阵抖动上色；`glow(cx, cy, r, 颜色)` 抖动光晕
- 其他：`text('CAFE', x, y, 颜色, size)` 3×5 像素字、`rain()` 雨丝
- 交付用 PNG（无损），像素才清晰

**顺序**：都是先远后近、先大后小，文字最后叠加。水墨的雾要画在它该吞没的东西之后；水彩的叶梗要先画，并且只画在叶子外面。

## 三、毛病清单（都真实出现过）

**水墨**

| 问题 | 改法 |
|---|---|
| 后面的远山透过主峰 | 先远后近，`wash` 默认会遮挡身后 |
| 笔画像梯子或串珠 | 落笔间距跟笔毛挂钩（`bristle_stroke` 已处理） |
| 小路像头发丝，或是折线像裂缝 | 16 条左右，用 `spline` 平滑，只画在山体上，从雾里伸出来 |
| 皴擦像撒逗号 | 约 150 笔，长而顺坡，集中在阴面 |
| 山脊像卡通描边 | 山脊线用淡墨（0.3）加飞白，边缘靠水痕 |
| 松针像海胆 | 扇形松针，下面垫一团淡墨晕 |
| 主峰像锥子 | 左右坡宽度不同，加山肩和起伏 |
| 远山被挖出方块、断边生硬 | 用「从水线以下升起的山包」来留出水面，不要直接挖空一段 |

**水彩**

| 问题 | 改法 |
|---|---|
| 纸纹像砂纸或拉毛墙 | 纸纹受光强度约 0.3，纸纹要细 |
| 叶子中间一圈深色像靶心 | 第二层深色用湿画（soft 约 16）偏向一侧积色，不要同心 |
| 叶梗画到了叶面上 | 先画梗，用 `*(1 - 叶遮罩)` 限制只在叶外 |
| 颜色发脏 | 同一处罩染不超过三层；亮部留白或用 `lift` 提白 |
| 深色团块漂到树冠外，成了孤立的圆点 | 后几层罩染乘以第一层树冠遮罩（稍微扩一点），深色只积在冠内 |
| 树枝乱成一团 | 只画 3–5 根，从树干向上向外伸进树冠，长度按树冠大小算 |

**剪纸拼贴**

| 问题 | 改法 |
|---|---|
| 大面积蜡笔纹像满屏刮痕 | 大色块用 paper / kraft，蜡笔只用在点缀或小物件上 |
| 撕纸白边看不见 | 白边要宽出 5–8 像素（大半径模糊加低阈值），并且只出现在部分边缘上 |
| 画面顶边或左边多出一条阴影 | 阴影偏移不能用会首尾相接的循环平移，要用补零平移（已修） |
| 月亮画了光芒，像太阳 | 月亮用蜡笔光圈加几颗闪光，不要放射线 |
| 脸的五官太粗太凶 | 线宽约 r×0.035，腮红用 `glow` |
| 小鸟画成了一团 | 小鸟用两道细弧线（线宽约 2.6），不要用很短的粗笔 |
| 纸片被画面边缘切掉 | 云、气球这类主体要完整留在画面内，留出边距 |

**韩国彩铅**

| 问题 | 改法 |
|---|---|
| 颜色淡得几乎看不见 | 排线要够密（叠加后趋于饱和）；颗粒阈值不要卡太狠，用 pressure 控制能压进多少纸纹 |
| 奶油、白瓷等白色物体消失 | 用暖奶白色铺底，配淡紫灰或淡蓝灰阴影，再加一点白色高光 |

**日本动漫**

| 问题 | 改法 |
|---|---|
| 云是一个个正圆泡泡，明暗交界是斜直线 | 用不规则团块，数量多、大小不一；暗面用「团块减去偏移的自身」做成月牙形 |
| 人物腿太长 | 裙摆到膝盖附近，露出的腿约为身高的三分之一 |

**编辑风手绘**

| 问题 | 改法 |
|---|---|
| 色块死板，像电脑矢量图 | 每层专色都要有颗粒、浓淡不匀和几像素的套色错位 |
| 颜色太多太杂 | 4–5 种专色，靠叠印得到其他颜色（比如青叠黄出绿） |

**油画厚涂**

| 问题 | 改法 |
|---|---|
| 笔触像一根根塑料管、橡皮泥 | 凸起要克制：平顶鼓边的截面，高光约 0.1，打光范围约 0.8–1.18 |
| 笔触之间大量露底 | 铺底笔加密（density 约 2），宽笔铺满后再上细笔 |

**浮世绘**

| 问题 | 改法 |
|---|---|
| 云带半透明，透出后面的轮廓线 | 云带用不透明的色版（strength 超过 1，确保完全盖住） |
| 标题签和云带、主体撞在一起 | 标题签放在天空的空白处，其他元素给它让位 |

**像素风**

| 问题 | 改法 |
|---|---|
| 背景底部露出一条黑带 | 天空渐变和楼群都要铺到地面线，不留缝 |
| 光晕变成一大块方形点阵 | 光晕半径要小（约 20 像素）、强度约 0.4–0.5；霓虹光晕压扁一些 |

## 四、做成动画

- 各画风都有 `stage(name)` 和 `save(path, stages_dir)`，按阶段依次淡入叠化，就是「一幅画被逐步画出来」。README 里的动图就是这样做的。
- 更细的逐笔动画：把一组笔画单独画到透明层上导出，再用 Motion Canvas 遮罩按顺序显现。这个还没做成现成接口。

## 五、文件

```
lib/core.py            公共底层（噪声、模糊、样条、遮罩、毛笔、字体）
lib/inkpaint.py        水墨
lib/watercolor.py      水彩
lib/papercut.py        剪纸拼贴
lib/colorpencil.py     韩国彩铅
lib/anime.py           日本动漫
lib/editorial.py       编辑风手绘
lib/oilpaint.py        油画厚涂
lib/ukiyoe.py          浮世绘木版画
lib/pixelart.py        像素风
examples/*.py          范例脚本；*.jpg 成品；drawing_*.gif 逐步画出的动图
中文字体：自动找 Kaiti/Songti（macOS）、Noto CJK（Linux）、KaiTi/SimSun（Windows），或设 INKPAINT_FONT
```
