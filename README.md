# Claude Drawing · Claude 绘图

**Claude paints with code — no image model.** Thirteen styles, from ink wash and impasto oil to clay, cyanotype and cross-stitch.
**不用生图模型，Claude 用代码一笔一笔作画。** 十三种画风，从水墨、油画到黏土、蓝晒和十字绣。

[English](#english) · [中文](#中文)

<p align="center"><img src="examples/drawing_bawansiqian.gif" width="100%"><br><sub><b>Ink wash · 水墨</b> — every style below is drawn stage by stage like this · 下面每种画风都是这样一步步画出来的</sub></p>

| Watercolour · 水彩 | Paper collage · 剪纸拼贴 | Coloured pencil · 韩国彩铅 | Anime · 日本动漫 |
|---|---|---|---|
| ![watercolour](examples/drawing_watercolor_autumn.gif) | ![collage](examples/drawing_papercut_balloons.gif) | ![pencil](examples/drawing_colorpencil_dessert.gif) | ![anime](examples/drawing_anime_summer.gif) |
| **Editorial · 编辑风手绘** | **Impasto oil · 油画厚涂** | **Ukiyo-e · 浮世绘木版画** | **Pixel art · 像素风** |
| ![editorial](examples/drawing_editorial_ideas.gif) | ![oil](examples/drawing_oil_wheatfield.gif) | ![ukiyoe](examples/drawing_ukiyoe_fuji.gif) | ![pixel](examples/drawing_pixel_rainy_cafe.gif) |
| **Stop-motion clay · 黏土定格** | **Cyanotype · 蓝晒** | **Cross-stitch · 十字绣** | **Retro panel · 复古仪器面板** |
| ![clay](examples/drawing_clay_lighthouse.gif) | ![cyanotype](examples/drawing_cyanotype_botanicals.gif) | ![stitch](examples/drawing_stitch_sampler.gif) | ![panel](examples/drawing_panel_radio.gif) |

### Gallery · 画廊

| | |
|---|---|
| **八万四千法门** · *Many Paths, One Summit*<br><sub>Ink wash · 水墨</sub> | **月印万川** · *One Moon in Ten Thousand Rivers*<br><sub>Ink wash · 水墨</sub> |
| <img src="examples/bawansiqian.jpg" width="100%"> | <img src="examples/moon_river.jpg" width="100%"> |
| **秋日湖畔** · *Autumn Lake*<br><sub>Watercolour · 水彩</sub> | **热气球小镇** · *Balloon Day*<br><sub>Paper collage · 剪纸拼贴</sub> |
| <img src="examples/watercolor_autumn.jpg" width="100%"> | <img src="examples/papercut_balloons.jpg" width="100%"> |
| **午后甜点** · *Afternoon Dessert*<br><sub>Coloured pencil · 韩国彩铅</sub> | **夏空** · *Summer Sky*<br><sub>Anime · 日本动漫</sub> |
| <img src="examples/colorpencil_dessert.jpg" width="100%"> | <img src="examples/anime_summer.jpg" width="100%"> |
| **灵感生长** · *Growing Ideas*<br><sub>Editorial · 编辑风手绘</sub> | **麦田星空** · *Swirling Sky over the Wheat Field*<br><sub>Impasto oil · 油画厚涂</sub> |
| <img src="examples/editorial_ideas.jpg" width="100%"> | <img src="examples/oil_wheatfield.jpg" width="100%"> |
| **富士曙** · *Fuji at Dawn*<br><sub>Ukiyo-e · 浮世绘</sub> | **雨夜咖啡店** · *Rainy Night Cafe*<br><sub>Pixel art · 像素风</sub> |
| <img src="examples/ukiyoe_fuji.jpg" width="100%"> | <img src="examples/pixel_rainy_cafe.png" width="100%"> |
| **灯塔岛** · *Lighthouse Island*<br><sub>Stop-motion clay · 黏土定格</sub> | **蓝晒植物** · *Sun-Print Botanicals*<br><sub>Cyanotype · 蓝晒</sub> |
| <img src="examples/clay_lighthouse.jpg" width="100%"> | <img src="examples/cyanotype_botanicals.jpg" width="100%"> |
| **家** · *Home Sampler*<br><sub>Cross-stitch · 十字绣</sub> | **Aurora 64 收音机** · *Aurora 64 Radio*<br><sub>Vintage instrument panel · 复古仪器面板</sub> |
| <img src="examples/stitch_sampler.jpg" width="100%"> | <img src="examples/panel_radio.jpg" width="100%"> |
| **水彩底纹** · *Watercolour Washes*<br><sub>Watercolour · 水彩 — a background for explainer videos · 讲解视频的背景</sub> | |
| <img src="examples/watercolor_washes.jpg" width="100%"> | |

Every mark above is computed: paper fibres, ink washes and mist, dry-brush strokes, pigment granulation and blooms, torn-paper edges, pencil wax on paper tooth, cel-shaded clouds, risograph grain and halftones, lit impasto relief, woodblock grain and bokashi, dithered pixels, plasticine lit like a film set, sunlight through leaves on Prussian blue, twisted thread on Aida cloth, machined knobs behind a backlit dial. No diffusion model, no API, no stock art. It is just Python with **numpy + Pillow** on a CPU: from 0.1 s (pixel art) to about 30 s per 1920×1080 image.

---

## English

### What it is

A [Claude Code](https://claude.com/claude-code) skill and a small painting library with thirteen styles:

| Style | Module | What makes it read as the real medium |
|---|---|---|
| **Ink wash (水墨)** | `lib/inkpaint.py` · `Painting` | rice paper; occluding washes with wet rims and mist; bristle brush with flying-white; texture strokes (皴); moss dots; pines, boats, reeds; calligraphy and seal |
| **Watercolour** | `lib/watercolor.py` · `Watercolor` | cold-press paper tooth; *transparent glazes* that mix subtractively; wet-edge darkening; granulation; blooms; wet-in-wet feathering; reflections; lifting |
| **Paper collage** | `lib/papercut.py` · `Collage` | torn edges with a white fibrous core; paper depth shadows; kraft, crayon, newsprint and ruled-notebook papers; waxy crayon lines; cute faces |
| **Coloured pencil (Korean style)** | `lib/colorpencil.py` · `ColorPencil` | short directional hatching; wax that catches on the paper tooth, with pressure reaching the valleys; soft layered blending; brown pencil outlines; gel-pen sparkles |
| **Anime (Japanese)** | `lib/anime.py` · `Anime` | gradient skies; cumulus with *crescent* cel shadows on every puff; bloom, god rays, lens flare; flat-shaded fields, perspective roads, power lines; line-art characters |
| **Editorial (risograph)** | `lib/editorial.py` · `Editorial` | 4–5 spot inks with grain, uneven density and mis-registration; overprinting; halftone shading; wobbly hand-drawn line; stylised figures |
| **Impasto oil** | `lib/oilpaint.py` · `OilPainting` | thousands of strokes following a *flow field*; each pixel knows its place inside its stroke → flat-topped paint ridges, bristle grooves, heavier paint where the brush lands; lit relief |
| **Ukiyo-e woodblock** | `lib/ukiyoe.py` · `Ukiyoe` | one block per colour on washi, with wood grain and registration drift; *bokashi* graded wipes; black key-block outlines; seigaiha waves; cloud bands; title cartouche and seal |
| **Pixel art** | `lib/pixelart.py` · `PixelArt` | a 320×180 canvas painted pixel by pixel; limited palette; ordered (Bayer) dithering for gradients, glows and reflections; 3×5 bitmap font; crisp ×6 upscale |
| **Stop-motion clay** | `lib/clay.py` · `Clay` | a *height map* of pressed pieces (pads, balls, rolled snakes, puffy letters, finger-smeared slabs, tool grooves, pokes) with lumps and fingerprints; lit like a photo of a set: wrap-diffuse key + cool fill, waxy sheen, shadows marched through the height field, ambient occlusion |
| **Cyanotype (sun print)** | `lib/cyanotype.py` · `Cyanotype` | emulsion brushed on in strokes with dry-brush ends; objects *block UV* (transmissions multiply): translucent leaves with whiter veins, fluff lifted off the paper with a soft penumbra, light scattering under edges; a Prussian-blue density curve; white handwriting printed in, pencil notes on the margin |
| **Cross-stitch embroidery** | `lib/stitch.py` · `Stitch` | Aida cloth with a hole at every block corner; one X per cell, lit as round twisted thread with a shadow, in hand-made variants; half stitches; back-stitch snapped hole to hole; padded glossy satin stitch; French knots; ASCII charts and a 5×7 sampler alphabet; a sewn-on woven label |
| **Vintage instrument panel** | `lib/panel.py` · `Panel` | teak veneer, brushed aluminium, moulded plastic, grille cloth with lurex floats, perforated metal; bevels, wells and drop shadows from one key light; machined knobs, piano keys, toggle switch, jewel lamp, magic-eye tube, meter; silkscreened scales and a backlit dial behind glass |

Ask Claude to *"draw it yourself"*, *"paint this with code"*, or *"claude绘图"*, and name a style if you like. Claude then:

1. **Plans the composition**: layers, a focal point, breathing space, and a subject that illustrates the idea.
2. **Writes a short scene script** using the library.
3. **Renders it, looks at the result, and fixes it** against a per-style checklist of real failure modes, usually over 2–4 rounds.

### Why code instead of an image model?

- **Directed composition**: placement, empty space and accents are exact, not sampled.
- **Reproducible**: the same seed gives the same picture.
- **Animatable**: `stage()` snapshots let a video show the picture *being made*. The GIFs above are exactly that; a generated bitmap can't do it.
- **Runs anywhere**: offline, on a CPU, with no GPU, key or quota.

### Install

```bash
git clone https://github.com/cloveric/claude-drawing-skill.git ~/.claude/skills/claude-drawing
pip install -r ~/.claude/skills/claude-drawing/requirements.txt   # numpy, Pillow
```

Titles and notes need a CJK font. macOS Kaiti/Songti, Linux Noto CJK and Windows KaiTi/SimSun are found automatically; you can also set `INKPAINT_FONT=/path/to/font`. The clay, cyanotype, cross-stitch and panel styles also look for common Latin system fonts (a sans, a rounded bold, a script and a handwriting face, via `core.latin_font`); override any of them with `INKPAINT_FONT_<STYLE>`, e.g. `INKPAINT_FONT_HAND`. No font files are bundled.

### Quick start

```python
import sys; sys.path.insert(0, "lib")

# ink wash
from inkpaint import Painting
p = Painting(1920, 1080, seed=7); p.paper()
far = p.ridge(560, peaks=[(420, 150, 330), (1650, 110, 260)]); p.wash(far, dens=0.16, decay=170, mist_y=700)
main = p.peak(1130, 252, shoulders=[(1380, 70, 90)]); p.wash(main, dens=0.46, decay=240, mist_y=920)
p.cun(main, 530, 1730, shadow_x=1130); p.trails(main, (1130, 252), n=16, red_index=7)
p.mist(960, 70, 0.8); p.sun(1500, 190, 46); p.save("ink.png")

# watercolour
from watercolor import Watercolor, hexc
from core import blob_pts
w = Watercolor(1920, 1080, seed=1); w.paper()
w.gradient_wash(0, 540, top=hexc('#8fb0cf'), bottom=hexc('#f2cfae'))
leaf = w.shape(blob_pts(900, 760, 260, 90, rough=0.1), soft=2.5)
w.glaze(leaf, hexc('#a9c46b'), 0.75, edge=0.55, gran=0.35, bloom=1); w.save("watercolour.png")

# paper collage
from papercut import Collage
c = Collage(1920, 1080, seed=2); c.background('#232d66', texture='kraft')
c.piece(mask=c.circle_mask(1360, 300, 150), colour='#f6d77a', texture='crayon')
c.face(1360, 310, 128, mood='sleep'); c.save("collage.png")
```

Every style has a complete example: `python3 examples/<name>.py out.png --stages stages/`. `--stages` also writes the draw-on snapshots.

### Principles (the checklist Claude uses)

- **Ink**: paint far to near, and each wash occludes what is behind it. Tie dab spacing to bristle size so strokes never look beaded. Paths should be few, smooth and emerge from mist. Texture strokes are long, follow the slope and sit on the shadow side.
- **Watercolour**: keep the paper tooth subtle. Pool shadows wet-in-wet on one side, not in bull's-eyes. Keep darker glazes inside the first crown. Use at most three glazes in one place.
- **Collage**: big areas use flat or kraft paper, and crayon texture is only for accents. Torn white rims are 5–8 px wide and appear on only part of an edge. Shadows use a zero-padded shift.
- **Coloured pencil**: hatch densely enough to saturate, and let pressure decide how deep the wax reaches. White objects are warm off-white with lavender or blue-grey shading, never white on white.
- **Anime**: clouds are many lumpy puffs, each with a hard crescent shadow (the puff minus itself shifted toward the sun). Keep character proportions right.
- **Editorial**: use 4–5 inks and overlap them on purpose. Every ink layer gets grain, uneven density and a few pixels of mis-registration.
- **Oil**: lay big strokes first, then smaller ones, then detail only where it matters. Keep the relief modest (flat-topped ridges, soft speculars), or strokes turn into plastic tubes.
- **Ukiyo-e**: flat colour blocks plus bokashi only on skies and seas. Clouds are opaque bands. The key block outlines everything, and a cartouche and seal sit in the empty sky.
- **Pixel art**: paint at the true low resolution and dither instead of blending. Keep glows small (a big dither glow turns into a square). Upscale with nearest-neighbour only.
- **Clay**: think in heights (px) and let pieces drape over what is below. Finger smears must be wide, soft and few, or the sky turns into crumpled foil. Never wrap non-tileable noise: it leaves straight seams.
- **Cyanotype**: think in UV transmission, not paint. Thin leaves ~0.85 opacity with fully blocking veins; lift fluff off the paper for a soft penumbra. A fern pinna is one lobed blade, not a row of separate leaflets. Dry-brush stroke ends are crisp broken streaks, not a blur.
- **Cross-stitch**: everything lives on the hole grid. Never lay half stitches over cross stitches (switch floss colour instead). A short diagonal back-stitch is one stitch from hole to hole, or it snaps into L-shaped steps.
- **Panel**: one key light for every part: lit upper-left edges, shadows to the lower right. Grille-cloth lurex needs long floats (short ones read as a perforated dot grid). Keep legends off busy textures and away from scale ends.

### Roadmap

- Per-stroke layer export, for stroke-by-stroke animation in Motion Canvas or Remotion.

---

## 中文

### 这是什么

一个 [Claude Code](https://claude.com/claude-code) skill，加上一个小巧的绘图库，内置十三种画风：

| 画风 | 模块 | 为什么看起来像真的 |
|---|---|---|
| **水墨** | `lib/inkpaint.py` · `Painting` | 宣纸纹理；会遮挡身后的墨染山体，带水痕边和雾；分笔毛的毛笔与飞白；皴擦、苔点；松、孤舟、芦苇；题字与印章 |
| **水彩** | `lib/watercolor.py` · `Watercolor` | 冷压水彩纸纹理；**透明罩染**，叠色像真颜料一样变深、混色；水痕边；颜料颗粒；水渍花；湿画晕开；倒影；提白 |
| **剪纸拼贴** | `lib/papercut.py` · `Collage` | 撕纸露出的白色纤维边；纸片层叠的阴影；牛皮纸、蜡笔、报纸、笔记本横线纸；蜡笔线条；可爱圆脸 |
| **韩国彩铅** | `lib/colorpencil.py` · `ColorPencil` | 细密的短排线；蜡挂在纸纹凸起上，用力越大越能压进凹处；柔和叠色；浅褐色铅笔勾线；白色高光笔 |
| **日本动漫** | `lib/anime.py` · `Anime` | 天空渐变；每个鼓包都带**月牙形**硬边暗面的积雨云；泛光、光束、镜头光斑；平涂田野、透视公路、电线；线稿角色 |
| **编辑风手绘** | `lib/editorial.py` · `Editorial` | 4–5 种专色，每层带颗粒、浓淡不匀和套色错位；叠印出新颜色；半调网点；歪扭的手绘墨线；几何人物 |
| **油画厚涂** | `lib/oilpaint.py` · `OilPainting` | 几万道笔触顺着**流向图**排列；每个像素都知道自己在笔触里的位置，算出平顶鼓边的颜料、笔毛沟、落笔处更厚的颜料，再打光出凸起 |
| **浮世绘木版画** | `lib/ukiyoe.py` · `Ukiyoe` | 每种颜色一块版，印在和纸上，带木纹和套印偏移；天空和海面用**晕色（bokashi）**；墨色主版勾线；青海波纹；横向云带；标题签和朱印 |
| **像素风** | `lib/pixelart.py` · `PixelArt` | 在 320×180 的小画布上逐像素作画；有限调色板；渐变、光晕、倒影都用 Bayer 抖动；3×5 像素字体；无插值放大 6 倍 |
| **黏土定格** | `lib/clay.py` · `Clay` | 用**高度图**一块块捏：压平的泥片、小球、搓条、鼓起的黏土字、手指抹开的泥面、刻线和戳洞，表面带小疙瘩和指纹；再像拍定格动画一样打光：暖色主光+冷色补光、蜡质光泽、沿光线步进算出的投影、缝隙里的环境光遮蔽 |
| **蓝晒** | `lib/cyanotype.py` · `Cyanotype` | 药水一笔笔刷上去，笔尾是干刷的断续刷丝；放上去的东西**挡紫外线**（透过率相乘）：薄叶透一点光、叶脉更白，蒲公英绒毛离纸有距离、边缘柔和，边缘下还有散射；按普鲁士蓝的显影曲线上色；白色手写字一起晒出来，纸边再加铅笔字 |
| **十字绣** | `lib/stitch.py` · `Stitch` | Aida 布，每个布块四角有孔；每格一个 X，线按扭绞的圆线打光并投下小影子，还有几种手工误差；半针；回针沿孔走、一针从孔到孔；鼓起有光泽的缎面绣；法式结；字符图样和 5×7 刺绣字母；缝上去的织标 |
| **复古仪器面板** | `lib/panel.py` · `Panel` | 柚木贴皮、拉丝铝、注塑塑料、带金丝的喇叭布、冲孔网；同一盏主光照出倒角、凹槽和投影；车削旋钮、琴键、拨杆开关、宝石指示灯、绿色魔眼管、指针表；丝印刻度、玻璃后面的背光刻度窗 |

对 Claude 说「claude绘图」「你自己画」「用代码画」，也可以指定画风。它会：
1. **先定构图**：层次、焦点、留白，而且画面要图解内容本身；
2. **写一段场景脚本**，调用绘图库；
3. **渲染并自己看图**，对照该画风的毛病清单修改，一般改 2–4 轮。

### 为什么用代码画，而不用生图模型

- **构图可控**：位置、留白、点睛色都精确可控，不靠抽卡。
- **可复现**：同一个随机种子，画出同一幅画。
- **能做「作画过程」动画**：用 `stage()` 存下每一步，视频里就能看到画被一步步画出来。上面的动图就是这样做的，生图模型只能给一整张画。
- **哪里都能跑**：离线、只用 CPU，不需要显卡、API Key 或额度。

### 安装

```bash
git clone https://github.com/cloveric/claude-drawing-skill.git ~/.claude/skills/claude-drawing
pip install -r ~/.claude/skills/claude-drawing/requirements.txt   # numpy、Pillow
```

题字和纸条需要中文字体。macOS 的楷体/宋体、Linux 的 Noto CJK、Windows 的楷体/宋体都会自动找到，也可以用 `INKPAINT_FONT=字体路径` 指定。黏土、蓝晒、十字绣、复古面板还会找常见的西文字体（无衬线、圆体、花体、手写体，见 `core.latin_font`），可用 `INKPAINT_FONT_<风格>` 指定，比如 `INKPAINT_FONT_HAND`。仓库里不附带任何字体文件。

### 快速上手

水墨、水彩、剪纸的最小示例见上方英文部分的代码。每种画风都有完整范例：

```bash
python3 examples/bawansiqian.py         out.png --stages stages/   # 水墨：八万四千法门
python3 examples/moon_river.py          out.png                    # 水墨：月印万川
python3 examples/watercolor_autumn.py   out.png                    # 水彩：秋日湖畔
python3 examples/watercolor_washes.py   out.png --layout cover     # 水彩：底纹背景（--layout bill、--seed N 出变体）
python3 examples/papercut_balloons.py   out.png                    # 剪纸：热气球小镇
python3 examples/colorpencil_dessert.py out.png                    # 韩国彩铅：午后甜点
python3 examples/anime_summer.py        out.png                    # 日本动漫：夏空
python3 examples/editorial_ideas.py     out.png                    # 编辑风：灵感生长
python3 examples/oil_wheatfield.py      out.png                    # 油画厚涂：麦田星空
python3 examples/ukiyoe_fuji.py         out.png                    # 浮世绘：富士曙
python3 examples/pixel_rainy_cafe.py    out.png                    # 像素风：雨夜咖啡店
python3 examples/clay_lighthouse.py     out.png                    # 黏土定格：灯塔岛
python3 examples/cyanotype_botanicals.py out.png                   # 蓝晒：蓝晒植物
python3 examples/stitch_sampler.py      out.png                    # 十字绣：家
python3 examples/panel_radio.py         out.png                    # 复古仪器面板：Aurora 64 收音机
```

### 作画要点（Claude 交图前逐条自查）

- **水墨**：先远后近，每层墨染遮挡身后；落笔间距跟笔毛挂钩，笔画不会一节一节；小路要少、平滑、从雾里伸出来；皴擦长而顺坡、集中在阴面。
- **水彩**：纸纹要细；阴影用湿画偏一侧积色，不要画成靶心；深色罩染只积在树冠内；同一处罩染不超过三层。
- **剪纸**：大色块用平纸或牛皮纸，蜡笔只做点缀；撕口白边宽 5–8 像素，只出现在部分边缘；阴影偏移要补零。
- **彩铅**：排线要够密，颜色才能叠到饱和，用力大小决定能压进多少纸纹；白色物体用暖奶白色配淡紫灰或淡蓝灰阴影。
- **动漫**：云要用许多不规则团块，每团带月牙形的硬边暗面；人物比例要对。
- **编辑风**：专色 4–5 种，刻意让它们重叠；每层油墨都要有颗粒、浓淡不匀和几像素的套色错位。
- **油画**：先大笔铺底，再中笔，细节笔只用在要紧处；颜料凸起要克制（平顶、弱高光），否则笔触像塑料管。
- **浮世绘**：平涂色块，晕色只用在天空和海面；云带不透明；墨线勾住一切；标题签和印章放在天空留白处。
- **像素风**：在真正的低分辨率上画，用抖动代替渐变；光晕要小（大面积抖动会变成方块）；放大只能用无插值。
- **黏土**：按高度（像素）思考，部件顺着下面的东西铺；手指抹痕要宽、要柔、要少，否则天空像揉皱的锡纸；不可平铺的噪声不能循环平移，会留下笔直的接缝。
- **蓝晒**：想的是挡紫外线，不是上颜料：薄叶不透明度约 0.85、叶脉完全挡光；绒毛要离纸，边缘才柔；蕨类羽片是一整片带圆齿的叶子，不是一排分开的小叶；干刷的笔尾是利落的断续刷丝，不是一片模糊。
- **十字绣**：一切都在布孔的格子上；半针不要叠在十字绣上（亮部换浅色线）；短的斜向回针一针从孔到孔，否则会被吸附成 L 形台阶。
- **复古面板**：所有部件同一盏主光：左上边亮、向右下投影；喇叭布的金丝要长浮，短了像冲孔板；丝印字别压在花纹上，也别挤到刻度末端。

### 计划

- 按笔画分层导出，方便在 Motion Canvas / Remotion 里做逐笔动画。

---

MIT License · Made by Claude (Opus 5.5) with [@cloveric](https://github.com/cloveric)

### 友链
本开源项目已链接并认可 LINUX DO 社区。https://linux.do/
