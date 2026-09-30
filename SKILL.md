---
name: claude绘图
description: Claude 绘图 / Claude Drawing —— 不借助任何生图模型，由 Claude 用代码一笔一笔「画」出图片（程序化绘画）。内置二十七种画风：中国水墨、水彩、剪纸拼贴、韩国彩铅、日本动漫、编辑风手绘（Riso）、油画厚涂（梵高式流向笔触+颜料浮雕打光）、浮世绘木版画（晕色、木纹、墨线主版、青海波）、像素风（低分辨率+Bayer 抖动+像素字体）、黏土定格（高度图捏出的彩泥+影棚打光）、蓝晒（普鲁士蓝日光晒图，植物剪影透光）、十字绣（Aida 布十字绣+回针绣+缎面绣+法式结）、复古仪器面板（60 年代收音机/仪器正面：柚木、拉丝铝、旋钮、刻度窗、指示灯）、贴纸拼贴·小票（模切乙烯贴纸、热敏小票、和纸胶带、吊牌、橡皮章）、实验笔记本·贴纸（线圈方格本、铅笔图表、荧光笔、红笔圈、便利贴）、黑板板书（墨绿石板、粉笔颗粒、板擦残影、示意图与公式）、赛博朋克（雨夜霓虹街道、玻璃管霓虹招牌、全息广告、湿路面倒影）、卡通手绘（蓝铅笔稿、毛笔线、错位平涂、赛璐璐阴影、逐帧抖线）、等轴 2.5D（正等轴微缩模型、一个太阳照出三面明暗、悬浮数据卡）、单线画（一根不断开的线一笔画完、唯一点睛色）、柔光 3D（光线追踪的糖果色小球海和鼓鼓的软字、景深）、形变动画（一条轮廓依次变形、洋葱皮残影、缓动曲线）、报刊拼贴（牛皮纸、手撕旧报纸、网点老照片、勒索信拼贴字）、弥散玻璃（弥散渐变、磨砂玻璃卡片界面）、包豪斯几何（三原色几何、丝网印刷海报）、复古 Synthwave（切口落日、霓虹网格、镀铬字、录像带质感）、拼豆（钉板上的熔珠小管、熨烫熔合）。用户说「claude绘图」「用代码画」「你自己画」「不用生图模型画」「程序化绘画」，或点名以上任一画风（含黏土、彩泥、定格动画、蓝晒、晒图、十字绣、刺绣、复古面板、老式收音机、贴纸、小票、收据、手帐拼贴、实验笔记本、方格本、荧光笔、便利贴、黑板、板书、粉笔、赛博朋克、霓虹、雨夜街道、卡通、手绘卡通、逐帧手绘、抖线、等轴、2.5D、微缩模型、单线画、一笔画、线条动画、柔光 3D、3D 渲染、C4D 风、软糖字、小球海、形变、变形动画、报刊拼贴、剪报、达达、勒索信字、网点印刷、弥散渐变、玻璃拟态、毛玻璃、包豪斯、几何构成、丝网印刷、Synthwave、蒸汽波、合成器浪潮、80 年代复古、拼豆、拼拼豆、熔珠、熨豆、豆豆画、钉板、烫豆），或 "draw it yourself", "paint with code", "procedural painting", "watercolor / collage / colored pencil / anime / editorial / impasto oil / ukiyo-e / pixel art / clay / claymation / cyanotype / sun print / cross-stitch / embroidery / retro instrument panel / vintage radio / sticker collage / receipt / lab notebook / graph paper / chalkboard / blackboard / cyberpunk / neon city / cartoon / hand-drawn animation / isometric / 2.5D / continuous line / one-line drawing / soft 3D / 3D render / puffy letters / ball pit / shape morph / morphing / newspaper collage / Dada / ransom note / halftone / glassmorphism / aurora gradient / Bauhaus / geometric poster / screen print / synthwave / retrowave / outrun / perler beads / hama beads / artkal / fuse beads / melty beads / pegboard beads without an image model" 时使用；也用于需要逐步画出（draw-on）动画的插画。
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
| 卡通手绘（逐帧手绘） | `lib/cartoon.py` · `Cartoon` | `examples/cartoon_toaster.py` 早安吐司（薄荷绿吐司机笑着弹出两片举手的吐司、「叮！」爆炸框、盘子上打瞌睡的化黄油、窗外日出、墙上 7 点的钟；左侧 ①按下拉杆 ②电热丝烧红 3 分钟 ③弹起来 的图解；蓝铅笔稿留底、毛笔线、错位平涂、赛璐璐阴影、蜡笔天空与烤边、网点橱柜、抖线） | 约 4 秒 |
| 等轴 2.5D | `lib/isometric.py` · `Isometric` | `examples/isometric_weather_island.py` 岛上的气象站（漂浮的分层底座、一格一格的倒角地砖与台地、带双道浪花的海；观测场里的百叶箱、雨量筒、带风杯和风向标的风杆；看守小屋与卫星天线、太阳能板、石板路、栈桥小船、风袋、浮标、开花灌木；探空气球和平底云；四张悬浮数据卡用细引线指向各自仪器，地面上一个指北针） | 约 5 秒 |
| 单线画 | `lib/lineart.py` · `LineArt` | `examples/lineart_paper_plane.py` 从这扇窗到那扇窗（一根不断开的金线：圆树、小屋、从窗口穿墙飞出的纸飞机航迹与顶部翻圈、飞镖形纸飞机穿墙飞进对面小屋的窗；窗子亮起是全画唯一的点睛色；字距拉开的衬线标题） | 约 6 秒 |
| 柔光 3D | `lib/soft3d.py` · `Soft3D` | `examples/soft3d_rise.py` 浮出（糖果色小球海里顶出鼓鼓的软字 rise：被挤开的球堆在字脚、几颗骑在字肩上、几颗滚落，i 的点是一颗黄球；天光穹顶、柔光箱主光、粉色轮廓光、环境光遮蔽、软阴影、次表面色调、景深） | 约 46 秒 |
| 形变动画 | `lib/morph.py` · `Morph` | `examples/morph_water_cycle.py` 一滴水的旅程（一条 256 点轮廓线依次变成水滴→云→雪花→雪山→河→海浪，六块纯色背景随之切换；洋葱皮残影、挤压拉伸、虚线运动轨迹、中间帧标出对应点、缓动曲线时间轴） | 约 1 秒 |
| 报刊拼贴 | `lib/newscollage.py` · `NewsCollage` | `examples/newscollage_curiosity.py` 好奇心周刊 · 拆开看看（牛皮纸底、手撕旧报纸（程序生成的假文字栏）、被剪刀剪开并掀起上半的网点印刷闹钟照片、飞出的齿轮 / 发条 / 红色网点摆轮 / 螺丝各自剪下并配打字标签和引线、大红纸圆、勒索信拼贴字「拆开看看？」和 WHAT MAKES IT TICK、刊头、黑色邮戳、红色「附零件图」印章、美纹纸胶带） | 约 3 秒 |
| 弥散玻璃 | `lib/aurora.py` · `Aurora` | `examples/aurora_morning.py` 晨间计划（日出色弥散渐变与极光光带、光泽小球；磨砂玻璃卡片层叠：晨间计划时间线（3/5 完成，进行中那一行是玻璃叠玻璃）、专注倒计时圆环、光泽太阳躲在玻璃云后的天气卡、勿扰开关与白噪音滑块、近 7 天专注柱状图、9:00 站会提醒胶囊） | 约 2 秒 |
| 包豪斯几何 | `lib/bauhaus.py` · `Bauhaus` | `examples/bauhaus_form_colour.py` 形与色 · Form & Colour（奶油色纸上的丝网印刷讲座海报：黄三角、红方、蓝圆站在粗黑地线上，60° 弧、直角框、挖空的圆心和半径，下面大字角数 3 / 4 / 0；「形与色」大标题、挖空字的黑条论点「角越尖，色越亮」；构成网格、套准十字、裁切线、色标条、铅笔版号） | 约 2 秒 |
| 复古 Synthwave | `lib/synthwave.py` · `Synthwave` | `examples/synthwave_coastline.py` 海岸线 1987（横条切口的渐变落日沉入海面、倒影碎成一条条光带、线框小岛与线框山脉、霓虹网格地面、霓虹边线的海岸公路、灭点处亮灯的小城、带落日轮廓光的棕榈剪影、驶向城市的尾灯、镀铬大字 COASTLINE 与霓虹手写 Last Sunset、录像机 PLAY 与日期屏显、色度渗色、跟踪噪带和扫描线） | 约 4 秒 |
| 拼豆 | `lib/perler.py` · `Perler` | `examples/perler_strawberry_coaster.py` 草莓杯垫（方格图纸上的草莓图样与图例，铅笔勾掉已摆的颜色；透明方钉板上摆到一半：草莓摆完、天蓝底色一行行往下铺，镊子夹着下一颗悬在空钉上，旁边散豆；九格分色收纳盒；熨平的圆杯垫：豆子熔成一片蜡质平面、孔缩小、外沿扇贝形，压着揭下的熨烫纸） | 约 9 秒 |

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
- 夜景、城市、雨、霓虹、电影感氛围、讲解片的「未来 / 科技 / 城市」封面 → 赛博朋克（要复古小尺寸或像素动画仍用像素风）；
- 可爱的拟人小物件、日常小事讲故事、带表情的角色、讲解片里轻松的「步骤 / 原理」图解、要逐帧抖线的动画 → 卡通手绘（要立体手作感用黏土定格，要纸片感用剪纸拼贴）；
- 小世界、城市 / 园区 / 工厂 / 校园示意，系统或流程的「微缩模型」图解，围着场景放数据卡的信息图，讲解片的「全景 / 系统概览」页 → 等轴 2.5D（要霓虹夜景用赛博朋克；要复古小尺寸用像素风）；
- 高级克制、极简、品牌感封面、要看「一笔画出来」的过程、讲一段路线或旅程 → 单线画（深蓝底金线或奶油底墨线，只一个点睛色）；
- 产品感、软萌立体、糖果色、MG 片头大字、「3D 渲染」、讲解片封面的立体标题 → 柔光 3D（要手作、捏泥的质感仍用黏土定格）；
- 过程、变化、循环、「从 A 变成 B」的小故事，讲解片的转场、片头和「演变」页 → 形变动画（要真的动起来，用 `Morph.at` 逐帧出图）；
- 杂志封面、观点海报、达达 / 复古拼贴、「拆开看看 / 里面有什么」类讲解页、需要老照片质感又不能用真人照片 → 报刊拼贴（要童趣温暖的彩纸拼贴仍用剪纸拼贴）；
- 产品界面、App / 小组件展示、效率工具与数据面板、明亮通透的科技感、讲解片的「功能 / 界面」页 → 弥散玻璃（要暗夜霓虹氛围仍用赛博朋克）；
- 设计感海报、讲座 / 展览 / 活动海报、概念图解（形状、比例、对比、原则）、讲解片里的「定义 / 原理」页 → 包豪斯几何；
- 80 年代复古未来、怀旧、夏夜公路与海边、音乐和歌单封面、讲解片的「复古科技 / 回到过去」封面 → 复古 Synthwave（要雨夜城市用赛博朋克，要低分辨率游戏感用像素风）；
- 手作、DIY 教程、「从图纸到成品」的步骤图、把像素图案做成可爱实物（杯垫、挂件、冰箱贴）、讲解片里的「动手做」页 → 拼豆（要屏幕上的像素游戏感用像素风，要布上的针线用十字绣）。

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

**卡通手绘 `Cartoon`**：
- 思路：照动画师画一张原画的顺序——蓝铅笔起稿 → 勾线 → 平涂 → 赛璐璐阴影 → 蜡笔/网点 → 特效 → 字。每一笔按种类落进一个「组」：`rough` 铅笔、`ink` 墨线、`flat` 平涂、`shade` 阴影/高光/腮红、`texture` 蜡笔/网点/排线、`fx` 特效、`type` 字。`stage(name, show=[组...], rough=强度)` 只显示这些组，画完的一张图可以按作画顺序回放；`with c.group(ink='ink_bg'):` 把某一类改投到别的组，`with c.group('fx'):` 全部改投
- 遮挡：东西不透明，`fill` 会挖掉身后已画的墨线和颜色（隐藏线自动去掉），所以先远后近；`fx`、`type` 是最后叠上去的覆盖层，它们的挖空只在显示时生效，阶段快照不会出现空洞
- 墨线：`line(pts, width, taper)` 毛笔线（落笔细、中段粗、收笔尖，有手抖和压力起伏）；`outline(pts, width, weight, gaps)` 一笔画完的闭合轮廓，首尾两个尖头交叠，背光的右下侧按 weight 加粗，`gaps=n` 留几处小断口；`ink_fill()` 实心墨块、`dot()` 墨点。每条墨线会自动先起一遍蓝铅笔稿（`rough=False` 关掉），`sketch()` 只画铅笔辅助线
- 颜色：`fill(pts|mask, 颜色, slop)` 平涂，整体错开 slop 像素、边缘游走，返回 `Mask`，可作 clip；`shade(形状, 颜色, offset=(dx, dy), clip)` 硬边赛璐璐阴影（形状减去朝光源挪过的自己，得到背光侧的月牙），offset=None 时直接用给的形状；`glint(pts, width)` 白色高光笔；`shape(pts, 颜色, shade=(颜色, dx, dy), shade2=...)` 一次做完平涂、两层阴影和描边；`darker(颜色)` 取阴影色
- 质感：`crayon(形状, 颜色, pressure, angle)` 蜡笔（只挂在纸纹凸起上，顺着涂的方向有条纹，毛边；pressure 可以是整幅数组，做渐变）；`tone(形状, 颜色, cell, angle, amount)` 网点纸；`hatch(形状, angle, spacing)` 墨线排线（接触阴影）；`blush()` 腮红
- 角色：`face(cx, cy, size, mood, rot)`，mood 可选 happy（^ ^ 眼加张嘴吐舌）、wow（圆眼加 o 嘴）、sleepy、smile、wink，自带腮红；`arm(肩, 手, bend, hand, thumb)` 橡皮管手臂加带拇指的白手套（先画手臂再画身体）
- 特效（默认进 fx 覆盖层，`fx=False` 当普通物件画）：`sparkle()` 四角闪光星、`speed_lines(p0, p1, angle)` 速度线、`steam()` 热气、`puff()` 扇贝边烟团、`burst()` 爆炸星形框、`crumbs(..., avoid=遮罩)` 飞溅碎屑、`pop_lines()` 强调短线
- 字（默认进 type 覆盖层）：`letter(s, x, y, size, fill, depth, depth_colour)` 大标题字（中文圆体加漫画西文，每个字微转、上下跳，带挤出阴影、左上白边和粗墨描边）；`note()` 手写注释；`arrow()` 手绘箭头；`badge(x, y, r, '1')` 编号圆标；`pencil_note()` 纸角的蓝铅笔编号；`text_width()` 量宽度
- 形状：`Cartoon.rrect_pts(x0, y0, x1, y1, r 或 (左上, 右上, 右下, 左下))`、`ellipse_pts(cx, cy, rx, ry, rot, a0, a1)`（给 a0/a1 就是一段弧）、`densify()` 保留尖角的折线、`place(局部点, cx, cy, scale, rot)` 摆放在局部坐标里画好的物件；`mask(pts)` 整幅遮罩，可以用 numpy 相乘相减
- 抖线：`Cartoon(..., boil=2.0)`，每次 `stage()` 用一张新的平滑位移场重描墨线（1–2 像素），颜色和铅笔稿不动；`save()` 用第 0 次描线
- 角度都是逆时针为正（同 PIL）；颜色常量 `INK PAPER PENCIL WHITE RED YELLOW PINK ORANGE`

**等轴 2.5D `Isometric`**：
- 思路：一台正等轴正交相机加一个小光线追踪器。每个部件都是解析实体（平面围成的凸多面体、任意轴向的圆台、可被平面切开的椭球），逐像素求交写进 G-buffer（深度、法线、反照率、材质），画的先后不影响遮挡。同样的实体再从太阳方向画一张阴影图、从正上方画一张记录「柱子顶和底」的高度图，最后统一算光：天空环境光 × AO + 太阳 × N·L × 软阴影（PCSS，半影随遮挡距离变宽）
- 构造：`Isometric(W, H, seed, scale=每格像素, look=(x, y, z), at=(屏幕比例 x, y), sun=(x, y, z), ss=2, floor=-2.4, record=True)`。世界 x 朝屏幕左下、y 朝右下、z 朝上，一格 = 1。`iso(x, y, z)` 世界 → 屏幕；`unproject(sx, sy, z)` 屏幕 → 该高度平面上的世界点（按屏幕位置摆悬浮物）
- 地面：`backdrop(top, bottom, glow, centre)` 浅色渐变和底座下面看不见的地板（接住底座的影子）；`slab(x0, y0, x1, y1, z0, z1, layers)` 漂浮的分层底座；`tiles(levels, heights, colours, soil, gap, paved=(4,))` 倒角地砖（0 海、1 沙、2 草、3 台地、4 铺装）；`sea(shallow, deep, foam, waves)` 海面（岸边浪花、断续第二道浪线、深浅过渡、浪短线、透亮侧壁）；`top_z(x, y)` 取砖面高度；`road()` 带中心虚线的路；`path(cells)` 石板
- 基本体：`box(x0, y0, z0, x1, y1, z1, colour, side, bevel)` 倒角盒子；`obox(centre, size, yaw, pitch, roll)`；`prism(pts, z0, z1)`；`convex([(normal, d)], lo, hi)`；`cylinder(x, y, z0, z1, r, r1=None)`（给 r1 是圆锥 / 圆台）；`tube(p0, p1, r)`；`ellipsoid(centre, radii, yaw, pitch, roll, clip=[(normal, d)])`、`sphere()`、`dome()`。都接受 `paint(P, n, tag)`（按世界坐标上色：砖缝、土层、瓦行、百叶、电池片、卡面文字）、`mat='matte'|'water'|'glass'|'soft'|'gloss'|'card'`、`cast=`（投不投影）、`ao=`（进不进高度图：悬浮物和细线都关掉）
- 建筑：`building(x0, y0, x1, y1, z, h, wall, roof='gable'|'hip'|'shed'|'flat', roof_colour, axis, windows=(行, +x 墙几扇, +y 墙几扇), door=('+x', 位置), trim)`；`roof()`；`window(x, y, z, w, h, facing)`（白框、十字棂、斜向天光、窗台）；`door()`；`sign(x, y, z, w, h, '字', facing)`
- 自然与道具：`tree(x, y, z, size, kind='round'|'pine'|'poplar'|'bush', flowers=)`、`rock()`、`cloud()` 平底云、`windmill(x, y, z, h, yaw, spin)`、`windsock()`、`dish()` 卫星天线、`solar_panel()`、`fence(pts, z, h, closed)`、`pier()`、`boat()`、`balloon()`
- 信息图：`card(x, y, z, w, h, facing='+x', title, tag, value, unit, note, series, icon='wind'|'temp'|'rain'|'balloon'|'sun', anchor=(x, y, z), accent)` 竖在空中的数据卡（文字印在等轴平面上，带细引线和锚点）；`compass(x, y, z, r, north)` 平躺在地面上的指北针；`text()`、`rule()`、`dot()` 平面排版叠在最上层
- 光：太阳从左后上方来，顶面最亮，+x 面（左下）次之，+y 面（右下）只吃天光；`sun_c / sky_c / hor_c / gnd_c`、`soft`、`pen`（最小 / 最大半影）可调。不要霓虹发光、泛光和描边

**单线画 `LineArt`**：
- 思路：整幅画是一条路径。先把各个形状做成点列，再 `chain()` 按作画顺序串成一条线；线只栅格化一次成「时间图」（每个子像素记住笔第一次经过时走了多少像素），画到哪一步就是 `时间 <= s`
- 底：`backdrop('night'|'cream')`：深蓝丝绒底（中间亮、细颗粒）或奶油纸，同时设定默认线色（金 / 墨）和点睛色（琥珀 / 朱红）
- 形状（静态方法，返回点列）：`smooth(控制点)` 样条、`poly(点, r, sharp=(下标,))` 圆角折线、`arc(cx, cy, rx, ry, a0, a1)`、`scallop(cx, cy, r, a0, a1, bumps, depth)` 树冠灌木的扇贝边、`place(点, 原点, angle, scale)` 局部坐标摆放、`curl(P, s, r, span, side, aspect)` 在路径第 s 像素处插一个翻圈、`retrace(点)` 原路去再原路回
- 路径：`chain([(名字, 点列), ...])` 返回 `(P, marks)`，断开处自动用切线连续的三次曲线接上；`trim(P, s0, s1)` 按长度裁剪；`locate(P, (x, y))` 最近点的长度；`at(P, s)` 取点和方向；`length(P)`
- 画线：`line(P, width, pressure=[(s0, s1, 倍数)], sheen, glow, hot)`：起笔轻、收笔长尖、压力缓慢起伏、急转处变粗、原路折返处提笔收尖；深色底上是随角度变亮、只带一点柔光的金线
- 动画：`draw_to(s 或 marks 名字)` 移动笔头，没画完时笔头带光点、刚画的一段更亮；`stage(name)`
- 点睛：`accent(遮罩, 颜色, glow, warm)`，遮罩用 `rect()`、`disc()`；深色底上会发光，并把附近的线染暖
- 文字：`text(s, x, y, size, colour, font='display', spacing)`（Didot 类衬线，中文自动换细宋体）、`text_width()`、`hairline()` 细装饰线
- 颜色常量 `GOLD GOLD_HI GOLD_LO AMBER VERMILION NIGHT CREAM INK`；`save('x.jpg')` 默认 quality 88、4:4:4

**柔光 3D `Soft3D`**：
- 真 3D：`Soft3D(W, H, seed, eye, target, fov)` 针孔相机，世界坐标 X 右、Y 上、Z 远离镜头；每个像素一条光线，numpy 在 CPU 上算
- 球海 `ball_field(x0, x1, z0, z1, r, gap, colours, weights, mat)`：方格上成千上万颗球，光线逐格查找（DDA），每格只测一颗球，十万颗也不慢；`tint_balls(x, z, radius, colours, chance)` 局部换色；`floor(颜色)` 球缝里看到的地板
- 主体（有向距离场，只在自己的包围盒里步进）：`text(s, at, size, depth, colour, mat, yaw, spacing, bob, roll, turn, dot)` 鼓鼓的挤出字（字形→精确距离变换→挤出、整圈倒圆、再吹胀；`dot=颜色` 把 i/j 的点换成一颗球；返回 {'heroes', 'dots', 'centre'}）；`rbox()` 圆角盒、`capsule()` 胶囊、`cylinder()` 圆角圆柱、`torus()` 圆环
- `part(heap, reach, pile, pile_top)`：主体从球海里顶出来，被挤开的球落进最近的空窝、堆在脚边（pile 是被挤开球数的倍数，pile_top 是堆的最高高度，别让它挡住字的下半截），周围的球海微微隆起
- 散球：`ball(x, y, z, r, 颜色)` 指定位置；`drop(x, z, r, 颜色, roll)` 从上方落下碰到东西为止，再往低处滚进窝里（roll=0 停在落点，比如骑在字肩上）
- 灯光：`sky(top, horizon, strength, haze, haze_start)` 天光穹顶（背景渐变、地面反光、远处雾）；`key(azimuth, elevation, strength, size)` 大柔光箱主光，size 越大影子越软；`rim()` 轮廓光；`softbox()` 只出现在反光里的灯片。方位角从镜头算：0 从相机身后，−90 左，+90 右，180 主体背后
- 材质 `mat=`：candy（清漆糖果，锐利灯片高光）、satin（缎面小球）、jelly、matte、pearl；缝隙和阴影变深变饱和而不发灰
- `lens(focus, aperture)` 景深（focus 可传 text() 的返回值或一个点，最好和相机一起先设）；`film(bloom, vignette, grain)`
- `save(path, stages_dir, ss=1.5)` 成片超采样；`stage(name)` 是当前场景的真实预览渲染，还没调用 sky() 时是灰色白模

**形变动画 `Morph`**：
- 思路：每样东西都是**一条**闭合轮廓；两条轮廓重采样成同样点数（默认 `Morph.N = 256`）、统一绕向、对齐起点，再逐点插值，就是形变；背景色和形状颜色跟着切换
- 形状库 `shape(name, cx, cy, size, rot, flip, stretch)`：`SHAPES` 有 circle / square / triangle / star / heart / drop / cloud / snowflake / mountain / river / wave / sun / moon / leaf / bird / fish / pin / house；`union([('circle', x, y, r), ('line', 点列, 宽), ('poly', 点列), ('sub', 图元)], cx, cy, size)` 用图元拼出自己的形状，自动描出外轮廓
- 几何：`resample(P, n)` 按弧长等距重采样；`normalise(P)` 顺时针、从正上方起；`align(A, B)` 统一绕向并用 FFT 找最佳起点；`chain([...])` 整串依次对齐；`ease(t, 'inout'|'sine'|'quad'|'in'|'out'|'back'|'expo'|'linear')`；`tween(A, B, s, at=, stretch=, direction=, spin=, scale=)` 轮廓绕质心插值、质心单独走运动路径，stretch 是沿运动方向的挤压拉伸；`at(keys, T)` 整串关键帧在全局时间 T 的轮廓（逐帧做真动画用）；`mix(c0, c1, t)` 在 OKLab 里混色（蓝到黄不发灰）
- 背景：`paper(颜色)`；`panel(x0, y0, x1, y1, 颜色, ink=)` 一块纯色面板，ink 是画在这块面板上的残影和线条默认用的颜色；`wipe(cx, cy, r, 颜色, ink, clip_box)` 定格的圆形转场
- 形状层：`fill(P, 颜色, alpha, clip=另一轮廓, half=((x0, y0), (x1, y1)))`，half 只填直线右侧，用来做两色折面；`outline(P, 颜色, width, dash=(实, 虚))`；`stroke(点列, 颜色, width)` 圆头线（高光、水纹、热气）；`dot()`
- 定格动画：`ghost(P, fill, fill_alpha, line_alpha, width)` 洋葱皮残影，线色为 None 时取下面面板的 ink，跨面板自动换色；`points(P, every)` 标出对应点；`links(A, B, every)` 对应点连线；`path(点列)` 过质心的平滑路径，`along(路径, u)` 取点和方向；`trail(路径, dash=)` 运动轨迹；`chevron()` 方向箭头；`streaks()` 速度线
- 时间轴：`diamond(x, y, r, fill)` 关键帧菱形；`ease_curve(x0, y0, x1, y1, kind, ticks=帧时间)` 一段缓动曲线，带帧点和虚线投影
- 文字 `text(s, x, y, size, 颜色, font='sans'|'display'|'mono'|'mono_bold'|'cjk'|'cjk_bold', anchor='l'|'m'|'r', spacing, alpha)`：y 是基线，中西文自动换字体，返回宽度；`text_width()` 量宽度
- 坐标都是像素、y 向下；角度逆时针为正

**报刊拼贴 `NewsCollage`**：
- 思路：每样东西都是「先印好、再撕或剪、最后粘上去」的一张纸 `Sheet`；老照片不是贴图，而是 `Photo` 用高度图布光渲染出来，再印成网点
- 底板：`board()` 牛皮纸（云状纸浆、深浅短纤维、树皮碎屑）
- 纸片：`sheet(w, h, 颜色)` 返回 `Sheet`，可用 `text()`、`block(…, minus=文字遮罩)` 反白字、`ink()`、`rule()`；`tear('rtb', depth, rim)` 手撕（边线游走、露出白色纸芯、飞出纤维），其余边算剪刀剪；`cut_rect()` 歪一点的剪刀四边形；`cut(pts)`；`wrinkle()` 浆糊起皱；`age()` 泛黄和霉斑
- 报纸：`newsprint(w, h, columns, size, headline, picture, ad)` 返回一整版假报纸（伪词栏、刊头线、大标题、导语、小标题、栏线、框线广告、网点小照片、背面透印），接着 `tear()`
- 老照片：在 `Photo(w, h)` 上搭物件：`disc()`、`dome(…, rot, cut)`（钟铃、球）、`ring()`（表圈）、`rod()`、`poly()`（指针）、`gear(r, teeth, spokes, pinion)`、`spiral(r0, r1, turns, flare)`（发条、游丝）、`screw()`；`text()` / `lines()` 印在表面的字和刻度；`glare()` 玻璃反光。z 是底座高度，height 是自身厚度，albedo / metal / gloss 是材质
- 印成网点：`print_photo(photo, cell, angle, ink)` 显影并印成网点，返回 Sheet；`s.cutout(margin, centre)` 沿轮廓用剪刀剪下；`s.split(p0, p1)` 一剪两半
- 粘贴：`paste(sheet, cx, cy, rot, lift)` 返回 Frame，`f.pt(lx, ly)` 把局部坐标换成画面坐标；`disc(cx, cy, r, 颜色)` 剪刀剪的色纸圆
- 字：`ransom('拆开看看', x, y, size, faces=[…], styles=[…])` 勒索信拼贴字，返回 [(Frame, 字)]；`clipping(字, size, face, paper, block, fg, extra)` 单个剪字，extra 可选 'text'（带邻字）或 'tint'（网点底）；`label(文字, x, y, size, face, fg, bg, block)` 剪下的一条印刷字
- 其他：`tape(cx, cy, 长, rot)` 美纹纸胶带；`stamp(cx, cy, [(字, 字号)], shape='box'|'round', ring=环形字)` 橡皮章；`pen(pts, dash=(实, 虚), dot)` 墨线引线
- 字体：news / news_bold / news_italic / serif_bold / slab / clarendon / didone / poster / futura / grotesk / typewriter(_bold) / cjk_song / cjk_hei / cjk_round / cjk_kai；缺字自动换中文黑体
- 颜色常量 `INK BLACK RED MUSTARD KRAFT NEWS PAPER TAPE`；rot 逆时针为正

**弥散玻璃 `Aurora`**：
- 思路：一块明亮的「光屏」（弥散渐变）上面悬着几片真的磨砂玻璃。透过玻璃看到的是它下面**真实像素**的高斯模糊（背景、小球、后面的卡片和字都算），再蒙一层白纱，界面印在玻璃上。先画的在后面，后画的卡片会把前面画好的卡片连字一起模糊
- 背景：`backdrop(base, blobs=[(x, y, rx, ry, 颜色, 强度)], ribbons=[(点列, 宽, 颜色, 强度)], warp, grain)` 网格渐变：色团按权重在 OKLab 里混色，坐标扭曲成不规则形状，光带沿样条走，自带细颗粒；`sparkles(n)` 零星光点；`orb(cx, cy, r, (亮, 中, 暗))` 光泽小球：虹彩色阶、菲涅尔边缘映出背景色、高光、落在背景上的彩色投影
- 玻璃：`glass(x0, y0, x1, y1, radius, blur, tint, sat, shadow, elevation, bevel, rim, sheen)` 返回 `Card`（x0 y0 x1 y1 w h cx cy r）。blur 是磨砂程度（约 20–30）；tint 是白纱（约 0.24，近光源一侧厚）；sat 是透过来的颜色饱和度（约 1.5）；bevel 是边缘斜面，向外折射，各色通道偏移不同，带很淡的色散；rim 是朝光边的高光描边；阴影只落在卡片外，颜色取自下面的背景。`pill()` 是小玻璃胶囊（按钮、提醒、高亮行，玻璃叠玻璃），`cloud(cx, cy, w)` 是玻璃云
- 形状（带符号距离场，1 px 解析抗锯齿）：`rrect()`、`circle(ring=线宽)`、`line(点列, smooth)`，都可以传 `grad=色阶, angle=`；`divider()` 是蚀刻细线
- 控件：`toggle(x, y, on)`、`slider(x0, x1, y, value)`、`knob()`、`ring(cx, cy, r, width, frac)`（从 12 点顺时针，锥形渐变、圆头、光晕、末端白点）、`check(cx, cy, r, 'done'|'now'|'todo')`、`bars(x0, y0, x1, y1, values, labels=, highlight=)`、`spark(x0, y0, x1, y1, values, dots=)`（返回各点坐标）、`sun()`、`app_icon(x, y, size, grad, glyph)`
- 文字 `text(s, x, y, size, fill, weight='light'|'regular'|'medium'|'semibold'|'bold', anchor, alpha, spacing, grad)`：西文用 SF（按字号调光学尺寸），中文用苹方，自动分段；anchor 第二个字母 s 基线、m 居中、t 顶、b 底；`text_width()` 量宽度
- 颜色：`INK` 深靛文字；渐变色阶 `WARM`（杏→粉→紫）、`COOL`（天蓝→长春花→紫）、`MINT`；`ramp(t, stops)`、`mix()` 在 OKLab 里插值。一种渐变只代表一件事
- `save('x.jpg')` 默认 quality 88、4:4:4 色度

**包豪斯几何 `Bauhaus`**：
- 思路：画面是一张丝网印刷的印张，每种颜色一块网版，先浅后深逐版刮印；同一色版上的所有东西共享这块版的套准误差（平移加极小旋转），所以色块和黑线相接处会露出一丝纸白或压出一道深边
- 纸：`paper(colour, margin, module)` 奶油色未涂布纸（云状纸浆、短纤维、纸屑、纸齿、微微不平的受光），同时设定设计区和网格模数；`at(col, row)` 网格坐标转像素；`grid()` 用浅灰色版印构成网格
- 遮罩（全画布、抗锯齿，可以相加相减）：`circle()`、`ring()`、`sector(cx, cy, r, a0, a1)` 半圆和四分之一圆、`arc()`、`rect(x0, y0, x1, y1, rot)`、`bar(x0, y0, x1, y1, width, cap='butt'|'square'|'round')` 粗黑条和细线、`poly()`、`triangle(x0, x1, base_y)`（默认正三角）
- 印刷：`pull(mask, ink, knock, edge, density, opacity)` 刮一版：墨膜顺刮板方向有条纹、行程末端变薄，薄处露出纸齿坑点，网版灰尘留针孔，版边有网目锯齿、边缘略积墨；墨半透明（黄最透、黑最不透），叠印变深。`knock` 是挖空遮罩，`edge=0` 让细线保持干净
- 文字：`text(s, x, y, size, ink, font, anchor, spacing, rot, weight)` 直接印；`text_mask()` 取遮罩用来挖空；font 用 geo（Futura Bold）、geo_book、geo_cond（窄体特粗）、cjk（粗黑体）、cjk_book，中西文逐字换字体；`text_width()` 量宽度
- 印刷标记：`marks(targets, crop, bar, inks, overprints)` 套准十字、四角裁切线、色标条。登记后每块色版第一次刮印时自动印上自己那一份，所以十字会叠成几色错开的样子
- 印完之后：`pencil(s, x, y, size)` 页边铅笔版号，石墨只挂在纸齿凸起上
- 颜色常量 `YELLOW RED BLUE BLACK`，纸色 `PAPER`，网格色 `TINT`；角度逆时针为正，0° 指 3 点钟；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**复古 Synthwave `Synthwave`**：
- 思路：
  - 一台水平针孔相机看向无限平地（X 右、Y 上、Z 向前，单位米），颜色缓冲从远到近画；
  - 会发光的东西同时写进发光缓冲，后画的不透明物会挡掉身后的光；
  - 最后四个半径泛光，过曝的通道溢向白色，成片再「过一遍录像带」
- 构造：`Synthwave(W, H, seed, horizon=610, vp_x=1060, focal=1100, eye=3.5, record=True)`；相机工具 `project(X, Y, Z)`、`ground_row(Z)`
- 天空：`sky(stops, ground)` 暮色渐变，地平线下先铺没点亮的地面；`stars(n, bright)` 越近地平线越稀，最亮的带四角星芒；`streaks([(y, x0, x1, 厚)])` 底边被照亮的细条云
- `sun(x, y, r, bands=8, band_top, gaps=(0.2, 0.7), level, gain)`：黄→橙→粉渐变落日，横条切口越往下越厚，切口是真缺口；在地平线处截断
- 远景：
  - `mountains(x0, x1, z0, z1, height, cell, taper, edge=(MAGENTA, CYAN))`：世界坐标里的抖动网格高度场，三角面暗色平涂，边线从山脚品红渐变到山脊青色；
  - `skyline(X0, X1, Z, heights, widths, tall=(X, 高), windows)`：远处小城剪影、窗光、航空红灯
- 地面：
  - `floor(colour, spacing, width, fog, scroll, x_range)`：霓虹网格，逐像素解析线宽，远处换成平均值防摩尔纹，带粉色地雾和太阳光带；
  - `sea(coast, bar, spread, sky, glitter, stretch)`：X < coast 一侧的海，倒影碎成一条条光带；
  - `road(x0, x1, dash)`：光滑路面加霓虹边线和中心虚线；
  - `neon_line(X, colour, width, dash)`：地上任意一条纵向霓虹线（海岸线）
- 物件：
  - `palm(X, Z, height, lean, fronds)`：棕榈剪影，环节树干、仰角不一的叶柄、下垂小叶、椰子、朝太阳一侧的轮廓光；
  - `car(X, Z)`：背影跑车，整条尾灯和路面上的红色倒影
- 字：
  - `chrome_text(s, x, y, size, depth, glints=(字序号...))`：镀铬大字，深色描边、阶梯挤出、发光浅边，上映天空、下映地面，中间一道锐利地平线，左上打光的倒角和四角星闪；
  - `glint(x, y, length)`：单独一个四角星闪；
  - `neon_script(s, x, y, size, colour, rot)`：霓虹手写体；
  - `caption(s, x, y, size, colour, rules)`：字距拉开的小字加两侧细线
- 录像带：
  - `osd(s, x, y, px, anchor)`：5×7 块字的录像机屏显（PLAY ▶、日期）；
  - `vhs(bleed, shift_px, jitter, noise, scan, tracking, head)`：只作用于成片，包括 YIQ 色度模糊右移、重影振铃、逐行抖动、一条跟踪噪带、底部磁头噪声、掉磁白线、扫描线、黑位抬升；阶段快照保持干净
- 颜色常量 `MAGENTA CYAN VIOLET ORANGE YELLOW PINK RED WHITE`；字体用 `synth_font('chrome'|'script'|'caption', size)` 找系统字体（Avenir Next Heavy Italic / Brush Script / 冬青黑体），可用 `INKPAINT_FONT_CHROME` 等指定；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**拼豆 `Perler`**：
- 思路：整张桌面是高度图，每样东西都是实体（豆是带孔短管、钉板带钉子、纸有厚度），相机略向后仰：每个屏幕像素沿自己那一列找最近的表面，所以豆子露一条侧壁、缝里露出后排侧面、孔里看得到内壁和钉子。光是左上一个大灯箱：局部点光、沿高度图步进的软阴影、天光 AO，镜面反射里看得到灯箱（亮面上是锐利的弧，熔化后变成蜡质光泽）；线性空间着色，`ss` 倍超采样
- 构造：`Perler(W, H, seed, pitch=22, tilt=0.32, ss=2, light=(x, y, z))`；pitch 是珠距（像素），tilt 是后仰量
- 桌面与纸：`desk(颜色, kind='wood'|'mat')`；`chart(rows, key, cx, cy, cell, angle, title, subtitle, number, names, done)` 印好的图纸（格子、符号、行列号、每 5 格粗线、图例带颗数），返回对象的 `.done.update('RD')` 用铅笔勾掉已摆的颜色；`tape(字, cx, cy, angle, size, sub, badge='1')` 美纹纸标签；`sheet(draw, cx, cy, angle, thick, translucency, drape, cut, curl, bump)` 任意薄片
- 钉板与豆：`pegboard(cx, cy, cols, rows, shape='square'|'circle'|'hexagon', colour='clear'|'white'|颜色, angle)` 返回 `Board`（钉子都在方格点上，`xy(row, col)` 取钉子位置）；`place(board, rows, key, at=(行, 列), only='RDP', keep=lambda r, c: ...)` 按文字图样插豆，可按颜色、按区域分批；key 的值用 `BEADS` 色名（含 `pearl` 珠光、`clear` 透明、`glow` 夜光）或 '#rrggbb'
- 熨烫：`ironing_paper(cx, cy, w, h, angle, cut=((x, y), (nx, ny)), curl, wrinkle)` 盖在豆上的半透明熨烫纸，cut 表示揭开一半（卷边），wrinkle 是热皱；`iron(board, melt, where)`：0.4 半熔，0.7 成品，0.8 全平；`lift_off(board)` 取下成品
- 道具：`tray(cx, cy, [[色, ...], ...], cell, angle, fill)` 分色收纳盒（每格一堆豆）；`spill(cx, cy, colours, n, spread, standing)` 散豆；`bead(x, y, 颜色, pose='stand'|'side', angle, tilt)`；`tweezers(tip, angle, length, lift, rise, holding='sky', grip)` 悬空的镊子，尖端夹一颗豆，自带投影
- 层次与动画：`on_top(*objs)` 提到最上层，`remove(obj)` 拿走；`stage(name)` 只存快照，`save(path, stages_dir)` 时才按 1× 渲染各阶段
- 颜色常量 `BEADS`；角度逆时针为正；`save('x.jpg')` 默认 quality 88、4:4:4 色度

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

**卡通手绘**

| 问题 | 改法 |
|---|---|
| 窗外的太阳画到了墙上 | 窗里的东西都乘玻璃遮罩；被挡住的轮廓只画露出来的那段弧（`ellipse_pts` 给 a0/a1） |
| 手臂从头顶直直伸出、末端一个圆球，像触角或棒棒糖 | 肩膀放在身体侧面中部，先画手臂再画身体；bend 的正负让手肘朝外弯；手套加拇指、袖口和两道指缝 |
| 两个角色挨得太近，一个的手套落到另一个脸上 | 只画外侧那只手臂，内侧的藏在身后 |
| 烤色蜡笔涂在面包中间，像脸上的脏污 | 烤色只涂面包芯内缘一圈（轮廓遮罩减去内缩的轮廓），脸所在的中间保持干净 |
| 纸纹太粗，色块上像砂纸 | 纸纹受光约 0.026，颜料盖住的地方纹理减半（已处理） |
| 闪光星像菱形 | 用指数约 3 的星形线，竖向拉长（已处理） |
| 白字写在米色纸上看不见；白云、手套、烟团都是白色小圆团，挤在一起分不清 | 浅色字只写在深色块上；白色圆团之间拉开距离，背景里不放白云 |
| 飞溅的碎屑落到脸上 | `crumbs(..., avoid=角色遮罩)` |
| 动图 2.3 MB：铅笔稿每阶段换强度又跟着抖，网点和蜡笔也跟着抖，每次叠化都整片重编码 | 只抖墨线，颜色和铅笔稿留在纸上不动；铅笔稿强度在勾线之后固定；阴影和质感合成一个阶段（1.9 MB） |
| 黄油的嘴压在底边线上；滴落太小，水洼像一根黄条 | 脸按物件正面的高度缩放、上移；滴落画成从前沿挂下来连到水洼的一道，最后画，压在轮廓线上 |

**等轴 2.5D**

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

**单线画**

| 问题 | 改法 |
|---|---|
| 纸飞机画成小三角，像风筝或三角旗 | 用 3/4 俯视的飞镖形：近翼大、远翼透视缩小、中间一道折痕；笔从尾部缺口进、从机头出，四个角保持尖 |
| 航迹从谷底地面起飞又落回地面，看不出从哪飞到哪 | 线从 A 屋的窗里穿墙飞出，从机头穿墙飞进 B 屋的窗；两屋之间不画地面 |
| 翻圈放在爬升段，像挂在线上的气球或套索 | 翻圈放在轨迹顶部、路径接近水平处，`curl(..., aspect≈1.2)` 让圈更圆 |
| 航迹和房子一样粗、从地面附近起落，整条读成山丘或山脉轮廓 | 航迹段 `pressure=[(s0, s1, 0.62)]` 用轻手画细，从窗口直接上扬，不先下沉 |
| 轨迹末端急转直下，在飞机尾部勾出钩子，还和后翼边贴成细长条 | 把飞机尾部缺口的坐标作为轨迹最后一个控制点，入射角放缓到约 35° |
| 窗户、山肩这类要从里面够到的形状一笔连不过去；原路回来的短线头是钝圆头 | 用 `retrace()` 原路去再原路回（成图看不见）；原路折返处自动提笔收尖（已处理） |
| 树冠贴着屋檐，两样东西粘成一团 | 物件之间留出间隙 |
| 动图里深蓝渐变出现一圈圈色带，唯一的琥珀色窗被量化成米黄 | 调色板拆开：空底色 110 色、画出来的东西 145 色（饱和像素 ×6）；量化前加固定的 4×4 Bayer 抖动，每帧相同 |

**柔光 3D**

| 问题 | 改法 |
|---|---|
| 掉下去的球悬在字上方，字面上有莫名的暗斑 | AO、阴影、落球这类查询在包围盒外用了盒子距离，球停在了看不见的盒子上；字形距离网格覆盖的范围内一律用精确距离（已修） |
| 字脚一圈球发黑，字的下半侧有黑带 | 球海距离场只查 2×2 格、封顶半格，清空的格子旁边 AO 以为贴着球；改查 3×3 格、封顶一整格，AO 半径 0.3、强度 1.25、留 0.1 的底（已修） |
| 字从球海冒出来，脚下一圈空槽露出黑地板，像抠图 | 被挤开的球不删，按「落进最近的空窝、层层叠、要有三点支撑」堆到字脚：`part(pile=10, pile_top=0.3)` |
| 字埋得太深，s 只露出上半截像 c，整词读成 rice | s、e 用 bob 单独抬高，让它的下半弯露出来；part() 加 pile_top=0.3，只堆一层，堆起的球不能高过字母下半部 |
| 阴影里的薄荷球发青灰、发脏 | 淡紫天光乘薄荷色会发灰：阴影加按材质自身色调的次表面补光，天光调强、主光调弱 |
| 球排成直行一直通到远方，像条纹墙纸 | 整个场景转 30°，行列斜着走 |
| 清晰的字边有锯齿，高光一节一节 | 成片 1.5 倍超采样再 Lanczos 缩小；字形距离场模糊 2 像素，法线差分步长 2.5 个格（已处理） |
| 上三分之一一片惨白，远处和背景之间有一道硬地平线 | 雾色等于背景地平线色，雾距约 42；镜头稍抬，露出天空渐变 |
| 动图 3.4 MB，小黄球被量化成一块平色片 | 景深跟相机一起先设好（每个阶段都柔），曝光并进灯光强度，主光和轮廓光合成一个阶段；调色板样本里彩色像素 ×5 |

**形变动画**

| 问题 | 改法 |
|---|---|
| 起点、绕向没对齐，中间帧塌成一条条碎片 | 先 `normalise`（同样点数、顺时针、从正上方起），再 `align`（FFT 互相关找最佳起点）；一串关键帧用 `chain` 依次对齐 |
| 每段 5 个残影、关键帧又太大，雪花和云的花边残影叠成一片噪点 | 关键帧约占面板宽的六成；每段只画 3 个残影，中间那帧填色约 0.42，两侧只留细线和约 0.14 的淡填色 |
| 运动轨迹画成圆点，和中间帧上的对应点混在一起，看着像轨迹绕了个圈 | 轨迹用虚线（`trail(dash=)`），圆点只用来标对应点，图例里分开写 |
| 速度线等长等距，像梯子，落在河边还被当成水流线 | 海报里不画速度线，靠挤压拉伸和残影间距表现速度 |
| 纸纹把奶白色的云也盖成了砂纸 | 形状保持纯平：纸纹只加在露出的纸面上（`tooth` 遮罩），面板和形状只有极轻的印刷颗粒 |
| 闭合样条在直角处过冲，海浪底角鼓出一个包；太阳的细光芒是断开的小棍 | 只对曲线部分做样条，底边用直线接；光芒用楔形加圆头，和圆盘连成一体再描外轮廓 |
| 后一段的残影线压在前一个关键帧上；标签重复画了两遍，颜色变深 | 画完残影后重画前一个关键帧（只重画形状内的细节）；文字和形状外的点缀只画一次 |
| 「↺」在所用中文黑体里没有字形，显示成方框 | 循环箭头用 `outline` 画圆弧再加 `chevron`，方向取圆弧终点的切线 |

**报刊拼贴**

| 问题 | 改法 |
|---|---|
| 齿轮像一块灰饼：齿面和背景一样亮，窗口被投影压灰，齿比网点还细 | 齿面反照率约 0.56、metal 约 0.3，加车床纹的「领结」反光；抬起高度约 8，背景投影 0.35；齿距至少约 4 个网点（r=108 用 36 齿），剪边约 9 px |
| 发条画成一圈圈同心圆，像靶子 | 圈数 4–5，`flare` 约 1.6：里圈密、外圈松，才看得出是螺旋 |
| 打字机字体没有「→」，出现豆腐块 | 逐字检查字形，缺字自动换中文黑体（已处理） |
| 问号纸片压住主体表盘的数字 | 用上一个字的 Frame 算位置，整排标题缩小；主体整体右移给标题让位 |
| 红章盖在密密的报纸字上认不出 | 章盖在牛皮纸的空处 |
| 邮戳环形小字断成「CUR:OSTI」 | 环形字至少 18 px；橡皮漏印改成部分漏墨（0.3 + 0.7 × keep），细笔画不断（已处理） |
| 剪下的照片白边处处一样宽，像模切贴纸 | 白边宽度沿周长慢慢变宽变窄（`wander` 约 0.45），但永远不剪进物体（已处理） |
| 散落的零件看不出是从闹钟里飞出来的 | 先从缺口画几条虚线弧再贴零件，起点错开别汇成尖点；离缺口最近放一颗螺丝 |
| 带邻字的报纸剪字，邻字太大太黑，抢了主字 | 邻字字号约 0.075 倍、浓度 0.62，主字周围留一圈空 |
| 报纸透印太重，镜像标题像渲染错误 | 透印浓度约 0.045，模糊 1.4 px |
| 牛皮纸纤维太长太黑，像裂纹或头发 | 纤维 4–20 px，深色浓度 0.2 |
| 动图调色板被牛皮纸和报纸占满，芥末黄纸片变成土黄 | 调色板取样时高饱和像素算 5 倍（色差 24 → 2.7 / 255） |

**弥散玻璃**

| 问题 | 改法 |
|---|---|
| 前面的卡片压住后面卡片的字（「周三」「60%」被切掉一半） | 卡片只在对方的内边距里重叠（不超过内边距），文字离重叠区远一点 |
| 列表最后一行和底部按钮撞在一起 | 先按行距（约 84）算好列表总高，按钮从卡片底边往上放，不够就加高卡片 |
| 玻璃太「奶」，像磨砂塑料，后面的东西透不出来 | 白纱 tint 约 0.24（近光源一侧厚、另一侧薄），saturate 约 1.5；背景色团之间要有足够的色相差 |
| 小球刚好顶在卡片边上，像放在卡片上面 | 让小球三到四成真正压在玻璃后面，模糊的那一半才读得出「透过玻璃」；小球也别和卡片边相切 |
| 背景的色团和光带几乎全被卡片挡住 | 光带穿过卡片之间的空隙走，色团饱和度提一点 |
| 折线图的面积填充在末端成了一团紫雾 | 填充 alpha 约 0.16，两端各 22 px 渐隐（已处理） |
| 柱状图柱子太细，满高的空槽像幽灵柱，「一」看着像减号 | 柱宽取间距的一半，空槽 alpha 0.1；横轴用日期加「今天」 |
| 动图调色板被浅色背景占满，渐变控件量化成灰，小球出现等高线色带 | 调色板样本给饱和像素加权（×6 / ×3，暗色 ×4），每帧叠同一张 4×4 Bayer 抖动（约 ±2.4 级）：逐帧不变，「和上一帧相同」的透明差分照样有效 |

**包豪斯几何**

| 问题 | 改法 |
|---|---|
| 颗粒太重（约一成面积露纸），色块像砂纸、字像磨旧的橡皮章 | 露纸坑点控制在约 2%，只出现在墨膜偏薄的刮板条纹里；黑墨最少（GRAIN 0.4） |
| 坑点成团，像均匀撒了一层雪 | 纸齿用像素级白噪声加少量团块；墨膜另加约 ±2.5% 的浓淡微纹理，不全靠露白点 |
| 方块直角被磨圆 | 版边只做 3×3 轻模糊再加噪声阈值，不用大半径模糊 |
| 页边小字、铅笔版号、色标条压在裁切线上 | 左起 x≈86、右止 x≈1834，色标条末端离裁切线至少 40 px |
| 叠印色标全显示成上层颜色 | 丝网墨基本不透明，叠印色标默认关（`overprints=False`） |
| 黑色标注印在蓝色上看不清 | 深色块上的标注从该色版挖空（`knock=`），露出纸色 |
| 「60 °」度数符号离得太远 | 度数符号自动收紧 0.1 em（`_KERN`） |
| 标题和右上角讲座信息撞在一起 | 先按 120 px 模数排好每栏宽度，信息行写短 |

**复古 Synthwave**

| 问题 | 改法 |
|---|---|
| 太阳被泛光冲成一团白，横条切口被光晕填平 | 太阳底色先压到约 0.72、发光 level 约 0.4，让泛光提回来；切口厚度从条距的 0.2 递增到 0.7 |
| 横穿太阳的细条云像多出来的切口 | 有切口的太阳前面不加 `streaks`，细条云只放在太阳外 |
| 海面倒影是一团糊的圆，像水下还有一个太阳 | 按世界深度把水面切成横带，每带横移、以太阳所在列为中心随机拉伸或压缩（越近越乱），再用短划调制；光源的倒影比天空强约 2.4 倍 |
| 远处网格变成一大片平的橘色雾带 | 雾距 150 m，雾色压暗、偏品红；网格线按屏幕像素距离算覆盖，格子小于几个像素就换成平均值，不出摩尔纹 |
| 录像带噪点像画布纹理，线条满屏抖动打折 | 噪点约 0.014、横向拉长；逐行抖动约 0.35 像素，只留一条跟踪噪带和底部磁头噪声 |
| 霓虹手写字白芯太粗，整句像白字；随机断管像渲染错误 | 白芯只取笔画最中间，core 约 0.5；断管默认不加 |
| 棕榈冠像冷杉，改了又像平顶伞 | 叶柄仰角从陡到平均匀分配，加两片下垂枯叶；小叶在 3D 里朝叶尖前扫、向两侧展开再下垂后投影，不要一律竖直挂下 |
| 城市摆在线框山前面，暗对暗，高楼像幽灵 | 城市放在灭点旁、背靠落日余晖，山脉从城市右边才开始 |
| 小岛挡住太阳正下方，吃掉最亮的一段倒影 | 小岛只和太阳左缘略微相交 |
| 阶段快照里地平线下是整块橘色，太阳下半截露在地上 | `sky()` 先铺一层没点亮的暗色地面；太阳在地平线处截断 |

**拼豆**

| 问题 | 改法 |
|---|---|
| 钉板四周出现一整块深灰方框 | 豆子高度只写在豆子覆盖处（其余设 -1e3），别把整个窗口抬到板面高度 |
| 熨过的豆还是一颗颗分开的甜甜圈，和没熨的差不多 | melt 同时控制：外半径 +22%、smooth-min 融合宽度增到 0.55 倍珠距、孔缩 74%、高度降 40%，外沿和孔口分开倒圆；0.4 是半熔（孔在、珠粘、留菱形缝），0.7 是成品 |
| 熨平的杯垫像一块块六角螺母，表面像糖霜 | 接缝沟只在半熔时有（×(1 − m/0.7)²），顶面只留 5% 的枕形起伏，熨烫纸细纹 0.08 px |
| 收纳盒里的豆堆成一根根塔 | 散豆落在下面的东西上，但限高约一层豆（`cap`）；每格约 20 颗，按抖动网格铺开 |
| 镊子像两根筷子、像白纸条 | 两腿成 V 形，尾部合拢、尖端张开一颗豆宽，腿宽 1.5→4.9 px；钢色偏暗，靠拉丝纹和窄的灯箱反射显出金属；悬空层单独投影 |
| 白豆侧壁出现竖条纹、钟乳石状锯齿 | 侧壁的 AO 和阴影改从平滑图上、在墙脚和墙顶内侧取样；墙顶取最近几行的最大高度；太陡的抗锯齿斜坡按侧壁着色 |
| 熨烫纸（缓坡）上出现发丝状细线 | 朝镜头的缓坡会把一行拉成约 1.1 屏幕行，超过 1.5 行才算侧壁 |
| 高光要么看不见，要么每颗豆一圈白光环 | 用灯箱反射：镜面方向落在主光方向 8° 内（越粗糙越宽）才亮，得到左上沿和孔内远侧唇口两道弧；菲涅尔权重压到 0.08 |
| 熨烫纸盖住标签，字变半透明 | 后放的会盖住先放的，用 `on_top()` 把标签、杯垫提到最上层 |
| 图例铅笔勾挤到前一栏数量上；深绿、叶绿都印成 G | 勾直接打在豆子图标上；符号原样印，不转大写 |

## 四、做成动画

- 各画风都有 `stage(name)` 和 `save(path, stages_dir)`，按阶段依次淡入叠化，就是「一幅画被逐步画出来」。README 里的动图就是这样做的。
- 动图规格（多数现有动图和后来新增的都一致）：720×405；每个阶段停 900 毫秒，再用 5 帧（每帧 90 毫秒）叠化到下一阶段，最后一帧停 2600 毫秒，无限循环。后来新增的动图所有帧共用一张 256 色调色板，文件小、不闪烁。
- 调色板别只取最后一帧：满屏单色（黑板的墨绿、赛博朋克的夜色）会吃掉色位，彩色部分被量化成灰。黑板按加权像素样本做中值切分（彩色像素 ×5、亮色 ×2）；赛博朋克从全部关键帧的拼图取 255 色，留 1 个透明色标记「和上一帧相同」的像素，并去掉 Pillow 每帧重复写入的局部调色板（3.8 MB → 1.8 MB）。
- 调色板的另外几条经验（新增的几种里反复出现）：
  - 小面积的点睛色（报刊拼贴的芥末黄纸片、单线画的琥珀色窗、柔光 3D 的黄球）会被量化成土黄、米黄或平色片：取调色板样本时饱和像素 ×5 左右，限定色板的画风可以把色板色强制放进调色板。
  - 大片渐变（弥散玻璃的背景、单线画的深蓝底、Synthwave 的天空）出现一圈圈色带：量化前叠一张固定的 4×4 Bayer 抖动，每帧同一张，「和上一帧相同」的透明差分照样有效。
  - 标记「和上一帧相同」的透明占位色不要用黑色：最暗的阴影像素会被当成透明，自检时大批帧对不上，改用纯品红这类画面里没有的颜色。
  - 最后一个 `stage()` 和成品完全相同时，Pillow 会把相同的帧合并，按帧数自检会报 EOFError：`save()` 前不要紧挨着再调一次 `stage()`。
  - 卡通手绘的抖线动图只抖墨线，铅笔稿和颜色不动，否则每次叠化都整片重编码，体积翻倍。
- 形变动画可以直接出真动画：`Morph.at(keys, T)` 给出全局时间 T 的轮廓，逐帧渲染即可。
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
lib/cartoon.py         卡通手绘（逐帧手绘）
lib/isometric.py       等轴 2.5D
lib/lineart.py         单线画
lib/soft3d.py          柔光 3D
lib/morph.py           形变动画
lib/newscollage.py     报刊拼贴
lib/aurora.py          弥散玻璃（弥散渐变 · 玻璃拟态）
lib/bauhaus.py         包豪斯几何（丝网印刷海报）
lib/synthwave.py       复古 Synthwave
lib/perler.py          拼豆（钉板、熔珠小管、熨烫融合）
examples/*.py          范例脚本；*.jpg 成品；drawing_*.gif 逐步画出的动图
中文字体：自动找 Kaiti/Songti（macOS）、Noto CJK（Linux）、KaiTi/SimSun（Windows），或设 INKPAINT_FONT
西文字体（后来新增的画风用）：core.latin_font(style) 按 sans / sans_bold / rounded / script / hand / typewriter 等找系统字体，可用 INKPAINT_FONT_<STYLE> 指定；字体文件不要放进仓库
```
