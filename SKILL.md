---
name: claude绘图
description: Claude 绘图 / Claude Drawing —— 不借助任何生图模型，由 Claude 用代码一笔一笔「画」出图片（程序化绘画）。内置十七种画风：中国水墨、水彩、剪纸拼贴、韩国彩铅、日本动漫、编辑风手绘（Riso）、油画厚涂（梵高式流向笔触+颜料浮雕打光）、浮世绘木版画（晕色、木纹、墨线主版、青海波）、像素风（低分辨率+Bayer 抖动+像素字体）、黏土定格（高度图捏出的彩泥+影棚打光）、蓝晒（普鲁士蓝日光晒图，植物剪影透光）、十字绣（Aida 布十字绣+回针绣+缎面绣+法式结）、复古仪器面板（60 年代收音机/仪器正面：柚木、拉丝铝、旋钮、刻度窗、指示灯）、贴纸拼贴·小票（模切乙烯贴纸、热敏小票、和纸胶带、吊牌、橡皮章）、实验笔记本·贴纸（线圈方格本、铅笔图表、荧光笔、红笔圈、便利贴）、黑板板书（墨绿石板、粉笔颗粒、板擦残影、示意图与公式）、赛博朋克（雨夜霓虹街道、玻璃管霓虹招牌、全息广告、湿路面倒影）。用户说「claude绘图」「用代码画」「你自己画」「不用生图模型画」「程序化绘画」，或点名以上任一画风（含黏土、彩泥、定格动画、蓝晒、晒图、十字绣、刺绣、复古面板、老式收音机、贴纸、小票、收据、手帐拼贴、实验笔记本、方格本、荧光笔、便利贴、黑板、板书、粉笔、赛博朋克、霓虹、雨夜街道），或 "draw it yourself", "paint with code", "procedural painting", "watercolor / collage / colored pencil / anime / editorial / impasto oil / ukiyo-e / pixel art / clay / claymation / cyanotype / sun print / cross-stitch / embroidery / retro instrument panel / vintage radio / sticker collage / receipt / lab notebook / graph paper / chalkboard / blackboard / cyberpunk / neon city without an image model" 时使用；也用于需要逐步画出（draw-on）动画的插画。
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
| 水彩 | `lib/watercolor.py` · `Watercolor` | `examples/watercolor_autumn.py` 秋日湖畔（秋树罩染、湖面倒影、红色小舟）；`examples/watercolor_washes.py` 水彩底纹（大片定向晕染、干边、回流水渍、颗粒、飞溅，中间留白，给讲解片当背景、上面叠界面卡片） | 约 15 秒 / 4 秒 |
| 剪纸拼贴 | `lib/papercut.py` · `Collage` | `examples/papercut_balloons.py` 热气球小镇（条纹热气球、笑脸太阳、纸云、小房子） | 约 30 秒 |
| 韩国彩铅 | `lib/colorpencil.py` · `ColorPencil` | `examples/colorpencil_dessert.py` 午后甜点（草莓蛋糕、红茶、草莓） | 约 17 秒 |
| 日本动漫 | `lib/anime.py` · `Anime` | `examples/anime_summer.py` 夏空（积雨云、乡间公路、电线杆、草帽女孩背影） | 约 30 秒 |
| 编辑风手绘 | `lib/editorial.py` · `Editorial` | `examples/editorial_ideas.py` 灵感生长（浇水长出灯泡的概念插画） | 约 11 秒 |
| 油画厚涂 | `lib/oilpaint.py` · `OilPainting` | `examples/oil_wheatfield.py` 麦田星空（旋转的星空、麦田、柏树、乌鸦） | 约 2 秒 |
| 浮世绘木版画 | `lib/ukiyoe.py` · `Ukiyoe` | `examples/ukiyoe_fuji.py` 富士曙（晕色天空、富士、云带、青海波、帆船、崖松） | 约 7 秒 |
| 像素风 | `lib/pixelart.py` · `PixelArt` | `examples/pixel_rainy_cafe.py` 雨夜咖啡店（霓虹、路灯、雨、倒影、猫） | 约 0.1 秒 |
| 黏土定格 | `lib/clay.py` · `Clay` | `examples/clay_lighthouse.py` 灯塔岛（手指抹开的天空、条纹灯塔、喷水的鲸鱼、搓条浪花、小帆船） | 约 6 秒 |
| 蓝晒 | `lib/cyanotype.py` · `Cyanotype` | `examples/cyanotype_botanicals.py` 蓝晒植物（蕨叶、银杏、蒲公英、飘散的种子、白色手写标注） | 约 6 秒 |
| 十字绣 | `lib/stitch.py` · `Stitch` | `examples/stitch_sampler.py` 家（H♥ME 字母、缎面绣爱心、小屋、苹果树、松树、花边、缝上的布标） | 约 20 秒 |
| 复古仪器面板 | `lib/panel.py` · `Panel` | `examples/panel_radio.py` Aurora 64 收音机（柚木机壳、喇叭布、背光刻度窗、琴键、魔眼管、拨杆、旋钮） | 约 7 秒 |
| 贴纸拼贴 · 小票 | `lib/sticker.py` · `Sticker` | `examples/sticker_market.py` 周末市集（热敏小票、模切贴纸：酸种面包/传家番茄/郁金香花束/咖啡豆、贴纸大字、波浪边促销贴、麻绳吊牌、和纸胶带、「已付」橡皮章） | 约 3 秒 |
| 实验笔记本 · 贴纸 | `lib/notebook.py` · `Notebook` | `examples/notebook_brewing.py` 咖啡萃取实验（线圈方格笔记本、铅笔表格与折线图、排线标出最佳区间、荧光笔、没闭合的红笔圈、便利贴结论、模切贴纸、标签机日期、桌上的六棱铅笔） | 约 3 秒 |
| 黑板板书 | `lib/chalk.py` · `Chalkboard` | `examples/chalk_lesson.py` 为什么天空是蓝的（墨绿石板、半擦掉的上节课残影与板擦痕、越往下越厚的粉笔灰；白黄粉蓝粉笔写的标题、太阳→大气层→眼睛示意图、长短波浪线、手写 ∝ 与圈出的 1/λ⁴、光谱条与散射曲线、带缺口的「小结」框；木框和粉笔槽里的粉笔、板擦） | 约 5 秒 |
| 赛博朋克 | `lib/cyberpunk.py` · `Cyberpunk` | `examples/cyberpunk_neon_street.py` 霓虹不夜城 · Neon District（雨夜街道峡谷、真玻璃管霓虹竖招牌（坏管与闪烁管）、背光灯箱、过街天桥「不夜城」、全息海月水母广告、电线、飞车光轨、井盖蒸汽、透明伞背影、湿路面与水洼倒影、胶片颗粒与一道撕裂扫描线） | 约 10 秒 |

各画风共用 `lib/core.py` 里的底层工具：噪声、模糊、样条曲线、多边形遮罩、有机轮廓 `blob_pts`、毛笔 `bristle_stroke`、中文字体查找；新四种还用到补零平移 `shift`、文字遮罩 `text_mask`、西文字体查找 `latin_font`/`load_font`，以及高度图打光 `height_normals`、`height_shadow`（沿光线步进的投影）、`ambient_occlusion`。

**用户没有指定画风时怎么选**：
- 禅意、古典、山水 → 水墨；
- 清新风景、花卉 → 水彩；
- 童趣、温暖、讲故事 → 剪纸拼贴；
- 甜点、小物、日常可爱 → 韩国彩铅；
- 青春、夏日、天空、背景美术 → 日本动漫；
- 观点、概念、商业文章配图 → 编辑风手绘；
- 浓烈、有笔触质感、名画感 → 油画厚涂；
- 日式古典、海浪、富士、东方装饰感 → 浮世绘；
- 复古游戏、夜景霓虹、小尺寸动画 → 像素风；
- 童趣立体、讲故事、手作感、定格动画 → 黏土定格；
- 植物、标本、自然科学、复古工艺感的蓝色海报 → 蓝晒；
- 家、温馨、手作礼物、贺卡、名字和字母 → 十字绣；
- 设备、仪表、音响收音机、复古科技与产品感 → 复古仪器面板；
- 清单、账单、价格、购物、市集、活动海报、轻松但成熟的讲解片封面 → 贴纸拼贴 · 小票；
- 实验记录、数据对比、复盘笔记、讲解片里的「算账 / 结论」页 → 实验笔记本 · 贴纸；
- 讲课、知识点、公式推导、原理示意图、讲解片里的「板书 / 课堂」页 → 黑板板书；
- 夜景、城市、雨、霓虹、电影感氛围、讲解片的「未来 / 科技 / 城市」封面 → 赛博朋克（要复古小尺寸或像素动画仍用像素风）。

每种画风一幅范例作为质量基准（范例都不用禅意主题）；水墨另加一幅「月印万川」（留白托月、水面倒影）。

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

**黏土定格 `Clay`**：
- 同时维护高度图（像素为单位）和颜色图，最后用影棚光一次性打光。部件默认「铺」在下面的东西上（`base=None`），先远后近、后铺的在上
- `backdrop(颜色)` 底板；`gradient(top, bottom, y0, y1)` 生成颜色场，可传给 `pad`/`smear`
- 部件：`pad(mask, 颜色, height, round)` 压平的一片（round 小是硬边薄片，大是鼓鼓的枕头形）、`ball(x, y, r)` 小球、`snake(pts, r, taper=(起, 止))` 搓条（线条、浪花、嘴、茎）、`text(s, x, y, size)` 鼓起的黏土字
- 工具痕：`groove(pts, width, depth)` 刻线、`poke(x, y, r, depth)` 戳洞；`smear(mask, 颜色场)` 手指抹开的一大片（会把相邻颜色拖混，留下柔和的指痕脊）
- `marble=('#颜色', 0.25)` 两色没揉匀的纹路；表面自动带小疙瘩和指纹
- 遮罩：`circle()`、`ellipse()`、`poly()`、`blob()`、`rrect()`

**蓝晒 `Cyanotype`**：
- 思路是「挡紫外线」而不是「上颜料」：放上去的东西按不透明度挡光，透过率相乘；最后显影成普鲁士蓝
- `coat(x0, y0, x1, y1)` 刷涂药水：一笔笔横刷，笔尾是干刷的断续刷丝，边上会甩几滴药水
- `place(mask, opacity, lift, texture)`：opacity 薄叶约 0.85、叶脉 1.0、绒毛约 0.3；lift 是离纸的高度（0 压平清晰，1–3 柔和半影）；texture 是叶肉的不均匀
- 批量画遮罩：`shapes([轮廓...])` 一次画很多片叶子，`lines([折线...], width, taper)` 一次画很多茎、叶脉、绒毛；`Cyanotype.leaf_pts(x, y, 角度, 长, 宽, tip, blunt)` 叶片轮廓
- 文字：`label()` 白色手写字（写在透明片上一起晒）、`pencil()` 晒完后写在纸边的铅笔字

**十字绣 `Stitch`**：
- 一切都在布孔的格子上（`cell` 像素一格）。`cells(mask)` 把像素遮罩变成格子，`at(gx, gy)` 取格子中心
- 针法：`cross(格子, 颜色)` 十字绣、`half(格子, 颜色)` 半针（天空、云、烟）、`back(pts, 颜色, step)` 回针（路径吸附到孔上，一针约 step 格）、`running(pts)` 平针虚线、`satin(mask, 颜色, angle)` 缎面绣（鼓起、有光泽）、`satin_text(s, x, y, size)`、`knot(x, y, 颜色)` 法式结
- 图样：`chart(['..#..', '.###.'], gx, gy, {'#': 颜色})` 按字符图绣；`letters('HOME', gx, gy, 颜色, scale)` 5×7 字母
- `label(x0, y0, x1, y1, 'EST. 2026')` 缝上去的织标

**复古仪器面板 `Panel`**：
- 所有部件都由同一盏左上方的主光照亮：朝光的边亮、背光的边暗、凸起的部件向右下投影
- 材质：`surface(mask, 材质, 颜色, height)`，材质可选 wood（柚木）、brushed（拉丝铝）、plastic、painted、fabric（喇叭布，`lurex=` 金丝）；`recess(mask, 材质, 颜色, depth)` 下凹的窗口；`background()`、`paint()`、`glow()`、`drop_shadow()`
- 控件：`knob(x, y, r, angle)` 车削旋钮、`button()` 琴键（`pressed=True` 按下）、`toggle()` 拨杆开关、`lamp()` 宝石指示灯、`magic_eye()` 绿色魔眼调谐管、`meter()` 指针表、`screw()` 螺丝、`grille()` 冲孔网、`badge()` 镀铬草书铭牌
- 印刷：`text(s, x, y, size, spacing=)` 丝印字、`scale_arc()` 圆弧刻度、`scale_linear()` 直尺刻度、`glass(mask)` 玻璃反光

**贴纸拼贴 · 小票 `Sticker`**：
- 思路：每样东西先在自己的透明小画纸 `Art` 上画成平面矢量图，再决定材质：`stick()` 做成模切贴纸，`lay()` 当纸平放
- `board(颜色, kind='cream'|'kraft')`：奶油色或浅牛皮纸底板，带纸纹、斑驳、纤维和杂点
- `art(w, h)` 返回 `Art`：遮罩 `circle/ring/ellipse/rrect/poly/blob/line/text`（中西文混排，`stroke` 加粗）；上色 `fill(mask, 颜色, alpha, clip)`、`gradient()`、`radial()`；`crescent(mask, dx, dy)` 明暗月牙；`speckle()` 撒面粉、籽粒；`cut()` 打孔；`texture('kraft')` 牛皮纸纹
- `stick(art, cx, cy, rot, border=14, peel='tr'|'tl'|'br'|'bl', peel_size, lift, gloss)`：模切贴纸。白边按圆角外扩，有切口厚度、覆膜高光和斜向反光，贴地阴影加柔和投影；`peel` 翻起一角，露出浅色背面和它自己的影子
- `lay(art, cx, cy, rot, curl, lift)`：纸张平放（小票、吊牌），两端微翘、翘起处影子更长；返回局部→画面坐标映射 `T(x, y)`，用来在纸上落笔、盖章
- `receipt(w, h)` 返回 `Receipt`：锯齿撕边、热敏灰字（断针竖纹、走纸浓淡、小掉点）；`centre()` 居中打印、`row(y, 名称, 金额, was='旧价')` 带点线引导和删除线、`rule('dash'|'stars'|'double')`、`barcode()`、`crease(y)` 折痕
- `tape(cx, cy, 长, rot, 颜色, pattern='stripe'|'dot'|'grid'|'plain')` 半透明和纸胶带，两头手撕锯齿；`tag_art(w, h, 颜色, 金属扣颜色)` 吊牌（`.hole` 是孔位），`twine(点列)` 双色面包师麻绳
- `stamp(cx, cy, r, 环形字, 中心字, 小字, 颜色, rot)` 圆形橡皮章（油墨半透明、压力不匀、字边积墨、漏印小坑）；`pen(点列, 颜色, width)` 红色圆珠笔（打勾、圈总价、划掉）
- 现成贴纸：`lettering_art([(文字, 颜色), ...], size)` 大字、`label_art()` 胶囊标签、`badge_art(r, 颜色, '-20%', top, bottom)` 波浪边促销贴

**实验笔记本 · 贴纸 `Notebook`**：
- 场景：`desk()` 石墨蓝灰桌面；`notebook(x0, y0, x1, y1, tabs, stack, ear, margin, header, grid, major)` 一整本笔记本（硬封底、分隔标签、错开的页边、青色方格纸、红色双边线、打孔、折角）；`binding()` 线圈（按金属管打光，带投影）
- 铅笔：`pencil(pts, width, pressure, jitter)` 手绘一笔（样条平滑、手抖、起笔轻收笔提）；`pencils([...])`；`rule(x0, y0, x1, y1)` 靠尺直线；`hatch(mask, angle, spacing, pressure)` 排线；`checkbox(x, y, size, checked)`；`arrowhead(tip, 方向)`；`axes(x0, y0, x1, y1, xlim, ylim, xticks, yticks, xlabels, ylabels)` 返回 `to_px(x, y)`
- 石墨只挂在纸纹凸起上：pressure 小是颗粒状浅灰，大才填满；线宽约 2–3.5 px
- 荧光笔 `highlight(x0, x1, y, h, tilt, alpha)`：正片叠底，斜切起笔并积墨、边缘毛、纵向纤维条纹、尾部断续，两遍重叠处更深
- 红笔：`pen(pts, width)`、`pen_loop(cx, cy, rx, ry, rot, turns=1.12)` 不闭合的圈、`pen_arrow(pts, head)`、`pen_underline(x0, x1, y, double)`
- 文字 `text(s, x, y, size, colour, font, anchor, rot, spacing, weight, medium)`：font 用 sans / sans_bold / typewriter / cjk_sans（中英混排自动换字体），medium 可选 ink、print、typed（打字机，每字浓淡和基线略不同）、pencil、opaque；`text_width()` 量宽度
- 纸片：`sticky(cx, cy, w, h, rot, colour)` 便利贴（上端平贴、下端翘起投影），返回 Frame，用 `f.pt(lx, ly)` 和 `rot=f.rot` 往上写字；`sticker(cx, cy, w, h, rot, colour, shape='rrect'|'circle', lines=[...])` 模切贴纸；`label_tape(s, x, y, size, rot)` 标签机胶带；`stain(cx, cy, r)` 咖啡杯印
- 道具：`pencil_prop(x, y, angle, length, width, label, end='eraser'|'plain')` 六棱铅笔
- 角度：`rot` 逆时针为正（同 PIL）；`angle`（铅笔、箭头方向）是屏幕角度，顺时针为正。常用色：`INK SOFT LEAD RED HI MINT MINTD`

**黑板板书 `Chalkboard`**：
- 分层：石板漆 → 粉笔层（预乘颜色 + 透明度，板擦能擦掉）→ 板前物件（木框、粉笔槽、粉笔、板擦及其投影）→ 室内光与暗角
- 板面：`slate()` 云状不匀的墨绿石板漆；`dust(amount, specks, haze)` 沉降的粉笔灰，越往下越厚；`frame(rail, top, ledge)` 斜接木框加粉笔槽，会设置写字区 `area` 和槽面高度 `tray_y`。默认尺寸构造时就已知，dust 和擦痕可以先于画框画
- 板擦：`swipe(pts, width, strength, haze, smear, keep)` 沿路径擦一遍：带走粉笔、顺擦向拖出残迹、毡面梳出细纹、毡面两端积灰；`smudge(cx, cy, w, h, rot)` 短擦一下；`with cb.erased(keep, angle, smear):` 块里画的一切都变成擦过没洗的旧课残影
- 笔尖：`stroke(pts, colour, width, pressure, jitter)` / `strokes([...])`；`line()` 徒手直线、`rule()` 靠尺直线；`box(x0, y0, x1, y1, gap=(xa, xb))` 四边出头，上边可留缺口写标签；`loop(cx, cy, rx, ry, rot, turns)` 不闭合的圈、`circle()`；`arrow(pts, head)` 两笔箭头在尖端叠厚；`underline(x0, x1, y, double)`；`wave(p0, p1, wavelength, amplitude)` 光波曲线带箭头；`dashed()` 一段段画的虚线；`dot()`；`hatch(mask, angle, spacing)` 排线；`propto(x, y, size)` 手写 ∝，返回宽度
- 侧锋：`side(p0, p1, stick, pressure)` 粉笔横躺拖一笔；`shade(mask, colour, angle, stick, pressure, overlap, weight)` 侧锋铺色，weight 是全画布 0–1 的压力图，可做渐变
- 粉笔只挂在板面「齿」的凸起上：pressure 0.2–0.4 颗粒稀疏（铺色），0.8–0.95 写字画线
- 文字 `text(s, x, y, size, colour, font, anchor, pressure, weight, rot, spacing, hand, grain)`：font 用 sans / sans_bold / cjk_sans，某套字体缺字自动换另一套；每个字各自微转、错位、轻重不一（hand=0 为排版体）；`text_width()` 量宽度
- 道具：`chalk_stick(x, cb.tray_y, length, colour, rot, worn='right'|'left'|None)` 粉笔，一端磨斜；`eraser(x, cb.tray_y + 2)` 板擦；`crumbs(x0, x1, n)` 碎粉笔
- 颜色：`WHITE YELLOW PINK BLUE` 为主，`RED ORANGE GREEN VIOLET` 用于光谱和彩色粉笔，另有 `DUST`；所有 angle 和 rot 都是逆时针为正

**赛博朋克 `Cyberpunk`**：
- 思路：一台水平的针孔相机看向街道深处，世界坐标 X 右、Y 上、Z 向前，单位是米。所有东西写进 HDR 缓冲（反照率、自发光、z-buffer 深度、倒影镜像行），调用顺序不影响遮挡；`render` 时统一算光：环境光 + 光源外溢照明、深度雾（雾色是城市光的散射）、地面倒影、蒸汽、雨、胶片
- 构造：`Cyberpunk(W, H, seed, focal=1150, vp=(x, y), eye=1.7, fog=125, wall=9.5, road=6, record=True)`；`record=False` 时 `stage()` 不出快照，渲染更快。相机工具：`project(X, Y, Z)`、`ground_row(Z)`、`near_z(side)`
- 远景：`sky()` 被街灯从下面照亮的低云；`skyline(z, x_range, heights, widths)` 远处塔楼剪影、针点窗光、红色航空灯；`light(x, y, r, 颜色, z)` 小点光源
- 楼：`building(side, z0, z1, height, wall, colour, lit, shops=(亮店, 卷帘门, 暗店, 自动售货机))` 透视楼块，正面加沿街立面贴图（窗格、空调外机、雨痕、底商、招牌字，右侧立面的字会自动镜像）
- 霓虹：`blade_sign(side, z, Y0, Y1, '字', 颜色, reach, border=颜色, latin='BAR', dead=[序号], flicker=[序号], kind='neon'|'box', text_colour, level)` 伸向街心、面向镜头的竖招牌；`sign(z, X0, X1, Y0, Y1, ..., vertical=False)` 横招牌或立式灯箱；`neon_text(s, x, y, size, 颜色, z, vertical, dead, flicker)`、`neon_path(点列, 颜色, z)` 任意灯管
- 全息：`hologram(z, X0, X1, Y0, Y1, '海月', 'SEA MOON', level, jelly=(x, y), sub_y)` 半透明投影广告（海月水母、竖排明朝标题、扫描线、撕裂切片、色边、投影边框），只加光，还会照亮雾和墙
- 街道：`street(crossing=(z, 宽), puddles)` 湿沥青、路缘、铺砖、斑马线、积水；`puddle(X, Z, rx, rz)` 指定水洼（放在近处招牌的倒影位置上，能倒映出整块招牌）；`grate(X, Z)` 井盖格栅
- 空中：`walkway(z, Y, thick, deep, windows=None)` 过街天桥（正面可再挂 `neon_text`）；`cables(n, z=(近, 远), Y=(低, 高))` 电线；`light_trail(三维控制点, 颜色, pair, strobe, fade)` 飞车光轨（左行交通：尾灯红、头灯暖白）
- 氛围：`steam(X, Z, height, width, drift, density)` 井盖蒸汽；`mist()` 只躺在远处街面的薄雾；`figure(X, Z, umbrella='clear'|'dark'|None)` 打伞背影（两侧霓虹轮廓光，无脸）；`rain(far, mid, near, slant, rings)` 三层雨和溅落圈；`glitch(y, h, shift, split)` 一道撕裂扫描线，只在成片里出现，用一次就够
- 颜色常量 `MAGENTA CYAN AMBER RED WHITE`；`save('x.jpg')` 默认 quality 88、4:4:4 色度，霓虹边缘不糊

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

**黏土定格**

| 问题 | 改法 |
|---|---|
| 手指抹开的天空像揉皱的锡纸 | 指痕要宽（40–70 像素）、数量适中（200–350 笔）、脊线柔和低矮（`smear` 的 height 约 4）；先铺几种颜色再抹，拖色才看得出来 |
| 天空里出现笔直的矩形色块边 | 不可平铺的噪声不能取模循环平移，要在噪声图内部取窗口（已修） |
| 预先铺的色块边缘太硬，抹完还是一块一块 | 色块之间用 smoothstep 柔和过渡，再用手指抹 |
| 浪花像一排排一模一样的墙纸花纹 | 每朵浪的长短、高低、间距都随机；只排两三行，近大远小 |
| 鲸鱼像一条面包，尾鳍像两根分开的香肠 | 头要圆、身体向后收窄入水；尾鳍用一整片带中间缺口的翼形轮廓 |
| 前景水面在藏在下面的尾柄处鼓起一个包 | 部件默认顺着下面的高度铺；被遮住的部分别伸进水面太深，或在水线处用泡沫盖住 |

**蓝晒**

| 问题 | 改法 |
|---|---|
| 蕨叶像一串箭头或锯齿（鱼骨状） | 每片羽片做成一整片带圆齿边的叶片，加淡色小叶脉；不要一颗颗分开的小叶 |
| 小叶改成椭圆后又像含羞草 | 同上，蕨类的羽片是连在一起的 |
| 蒲公英绒毛几乎看不见 | 细丝不透明度约 0.3、lift 约 1；抬得太高会被半影模糊掉 |
| 刷涂边缘像毛刺、撕纸或动态模糊 | 按一笔笔横刷建模：每根刷毛在自己的位置干净利落地停住，干刷的断续用横向拉长的噪声（已修） |
| 茎穿过白色题字 | 题字放在留白处，茎的走向给题字让路 |
| 飘散的种子被涂布边缘裁掉，只剩一根线 | 小物件要完整落在涂布区域以内 |

**十字绣**

| 问题 | 改法 |
|---|---|
| 斜向的短线（太阳光芒）被吸附成一串 L 形台阶 | 短斜线就绣一针，从孔到孔（`step` 设大） |
| 半针叠在十字绣上，像贴了一层纹理 | 真实绣法不会这样叠：亮部直接换浅一号的线绣十字 |
| 烟囱被屋顶整个盖住、烟线穿过标题 | 先算好屋顶轮廓再定烟囱高度；烟用半针小烟团，往留白处飘 |
| 布面格子太黑，像方格纸 | 布孔暗度约 0.34，布块起伏约 0.065 |
| 花朵和松树重叠 | 摆放前按格子算好每样东西占的列 |

**复古仪器面板**

| 问题 | 改法 |
|---|---|
| 喇叭布上的金丝像一排点点，看着像冲孔板 | 金丝纬线要长浮（压过三根经线再钻下一根），闪光沿线缓慢变化 |
| 刻度单位和最后一个数字挤在一起 | 单位放到刻度末端外侧，或者直接写完整数值（530…1600 kHz） |
| 浅色字印在浅色喇叭布上看不见 | 丝印颜色要和底材拉开明度 |
| 一大片喇叭布太平、太假 | 布是半透明的：把后面喇叭的圆形暗影淡淡透出来 |

**贴纸拼贴 · 小票**

| 问题 | 改法 |
|---|---|
| 面包只有一道长割口，像红薯或叶脉 | 三道斜向交叠的割口：浅色裂口加深色翘边，再撒面粉 |
| 花束的花用同心圆画，像靶心或棒棒糖 | 侧面郁金香：两片带尖的外瓣，前面一片浅色瓣 |
| 印章小字压在内圈线上 | 中心字上移，分隔线放在 +0.16r，小字写短，全部收在内圈以内 |
| 小票字太黑，像打字机不像热敏纸 | 灰色油墨 #4f525a、浓度约 0.8、边缘微糊，加断针竖纹和走纸浓淡 |
| 小票右半边整条发灰 | 横向卷曲压到很小，只让长边两端翘起 |
| 纸边的贴地阴影像描了一圈黑线 | 纸张接触阴影降到约 0.26 |
| 印章盖在条码上看不清 | 盖在金额和星号一带的稀疏处，只压一点字，更像真的 |
| 印章墨色太匀，像电脑填色 | 加压力倾斜、大块浓淡和漏印小坑 |
| 标签上的字溢出圆标 | 文字改短、字号调小 |
| 右下角空出一大块 | 加摊位号圆贴纸，第二个吊牌用长绳垂下来 |

**实验笔记本 · 贴纸**

| 问题 | 改法 |
|---|---|
| 铅笔线像干净的矢量墨线：细、匀、太黑 | 手绘线宽约 3 px、抖动约 1.6；石墨只挂在纸纹凸起上，重压也保留一点颗粒 |
| 轻压的排线、表格横线断成一串点点 | 覆盖率保留约四成连续的浅灰，颗粒只调制剩下的部分（`_graphite` 已处理） |
| 折线图数据点画成小圆圈，像字母 o、c | 用压实的小铅笔点（很小的螺旋，pressure 1） |
| 曲线一笔画成，太完美 | 分两笔画，接头处稍错开、稍重叠 |
| 标注字压在曲线上，单位和刻度撞在一起 | 标注放到曲线下方空白处，用铅笔小箭头指过去；单位放到轴端上方 |
| 贴纸孤零零浮在图下面，看不出指什么 | 从最佳点画铅笔虚线到横轴，贴纸贴在同一个 x 上 |
| 标签机胶带两端剪成 V 形缺口，像彩带横幅 | 两端直剪、略斜、小圆角 |
| 咖啡渍像肥皂泡或透镜 | 外缘一圈细而深的水痕线，内部几乎均匀的淡色；圈有断口、一侧更深 |
| 红笔箭头被后贴的便利贴盖住 | 箭头停在便利贴边缘外，或先贴便利贴再画箭头 |
| 标题上的荧光笔起笔压到了前一个字 | 起点按字宽算，落在目标字的左边缘 |

**黑板板书**

| 问题 | 改法 |
|---|---|
| 粉笔线像干净的矢量线：满压几乎实心、边缘光滑 | 满压也要留约 15% 的坑点（阈值 0.98 − 0.86 × 压力）；笔尖接触面按线宽的 0.26 倍模糊，边缘才会毛、才会断 |
| 中文（黑体）比 Helvetica Bold 细一截；加粗后 30 px 的复杂字糊成一团 | 中文按字号加粗，小字加粗减弱；40 px 以下自动加压、减轻颗粒和边缘扭曲（已处理） |
| 字体的粗体 ∝ 被粉笔加粗后闭合，看着像 ∞ | 用 `propto()` 手写一笔：双纽线的左瓣加两条向右的尾巴 |
| 大气层用侧锋铺色，成了一整块发闷的矩形，压住上面的波浪和标注 | 压力约 0.3、strength 约 0.6，用 `weight` 做渐变（近地面浓、往上淡），左右两端长距离渐隐 |
| 上节课的残影被后来的大擦痕又擦没了，或者压在新板书下面影响阅读 | 残影 keep 取 0.26–0.34，大擦痕 strength 不超过 0.6；残影放在空白处（上沿、角落、标题和图之间） |
| 动图调色板只取最后一帧，满屏绿色吃掉色位，粉彩粉笔、光谱条发灰 | 调色板用加权像素样本做中值切分（彩色像素 ×5、亮色 ×2），所有帧仍共用这一张 |

**赛博朋克**

| 问题 | 改法 |
|---|---|
| 倒影按一条地平线整体翻转，位置全错；被近处天桥挡住的远景在倒影里成了黑洞 | 每个物体按自己的着地行（mirror row）翻转，最近者优先；被挡住的空洞用对应行的雾色填 |
| 一楼店面发光太亮太大，近处成了过曝的纯色墙，货物画成色块像霉斑或柱状图 | 店内亮度 0.2–0.45，从天花板往下衰减、两侧变暗，加货架侧影和人影；最近的街区多放卷帘门和自动售货机 |
| 雨丝统一提亮成满屏灰帘，溅落圈太大像气泡 | 每根雨丝按周围光照上色，只在霓虹附近看得见；溅落圈半径 3–11 厘米，只在水洼里亮 |
| 蒸汽用背后的暗画面照亮，完全看不见 | 蒸汽按光源外溢光照明（像一块浅色表面），再加前向散射 |
| 光轨沿街飞，全都汇向灭点，像激光或钢丝 | 让飞车横穿街道：从一侧墙后出现，拱形掠过，消失在另一侧墙后；加频闪点 |
| 全息水母的 1 像素线被雾和扫描线吃掉；C 形生殖腺像数字「93」，后排两个像一双眼睛（成了脸） | 线宽至少 2 像素；生殖腺放在伞内的水平面上，侧视压成一条柔和的粉带；副标用 Light 字重，撕裂切片别落在字上 |

## 四、做成动画

- 各画风都有 `stage(name)` 和 `save(path, stages_dir)`，按阶段依次淡入叠化，就是「一幅画被逐步画出来」。README 里的动图就是这样做的。
- 动图规格（多数现有动图和新增四幅一致）：720×405；每个阶段停 900 毫秒，再用 5 帧（每帧 90 毫秒）叠化到下一阶段，最后一帧停 2600 毫秒，无限循环。新增四幅的所有帧共用一张 256 色调色板，文件小、不闪烁。
- 调色板别只取最后一帧：满屏单色（黑板的墨绿、赛博朋克的夜色）会吃掉色位，彩色部分被量化成灰。黑板按加权像素样本做中值切分（彩色像素 ×5、亮色 ×2）；赛博朋克从全部关键帧的拼图取 255 色，留 1 个透明色标记「和上一帧相同」的像素，并去掉 Pillow 每帧重复写入的局部调色板（3.8 MB → 1.8 MB）。
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
lib/clay.py            黏土定格
lib/cyanotype.py       蓝晒
lib/stitch.py          十字绣
lib/panel.py           复古仪器面板
lib/sticker.py         贴纸拼贴 · 小票
lib/notebook.py        实验笔记本 · 贴纸
lib/chalk.py           黑板板书
lib/cyberpunk.py       赛博朋克
examples/*.py          范例脚本；*.jpg 成品；drawing_*.gif 逐步画出的动图
中文字体：自动找 Kaiti/Songti（macOS）、Noto CJK（Linux）、KaiTi/SimSun（Windows），或设 INKPAINT_FONT
西文字体（新四种用）：core.latin_font(style) 按 sans / sans_bold / rounded / script / hand / typewriter 等找系统字体，可用 INKPAINT_FONT_<STYLE> 指定；字体文件不要放进仓库
```
