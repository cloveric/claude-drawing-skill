# Claude Drawing · install & examples · 安装与范例

[← README](../README.md) · [Styles](STYLES.md) · [画风](STYLES.zh.md) · [Principles](PRINCIPLES.md) · [作画要点](PRINCIPLES.zh.md) · [Usage · 用法](USAGE.md) · [Gallery · 画廊](GALLERY.md) · [GIFs · 动图](GIFS.md)

## English

### Install

```bash
git clone https://github.com/cloveric/claude-drawing-skill.git ~/.claude/skills/claude-drawing
pip install -r ~/.claude/skills/claude-drawing/requirements.txt   # numpy, Pillow
```

Titles and notes need a CJK font. macOS Kaiti/Songti, Linux Noto CJK and Windows KaiTi/SimSun are found automatically; you can also set `INKPAINT_FONT=/path/to/font`. Many styles also look for common Latin system fonts (a sans, a rounded bold, a script and a handwriting face, via `core.latin_font`); override any of them with `INKPAINT_FONT_<STYLE>`, e.g. `INKPAINT_FONT_HAND`. No font files are bundled.

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

## 中文

### 安装

```bash
git clone https://github.com/cloveric/claude-drawing-skill.git ~/.claude/skills/claude-drawing
pip install -r ~/.claude/skills/claude-drawing/requirements.txt   # numpy、Pillow
```

题字和纸条需要中文字体。macOS 的楷体/宋体、Linux 的 Noto CJK、Windows 的楷体/宋体都会自动找到，也可以用 `INKPAINT_FONT=字体路径` 指定。不少画风还会找常见的西文字体（无衬线、圆体、花体、手写体，见 `core.latin_font`），可用 `INKPAINT_FONT_<风格>` 指定，比如 `INKPAINT_FONT_HAND`。仓库里不附带任何字体文件。

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
python3 examples/sticker_market.py      out.png                    # 贴纸拼贴 · 小票：周末市集
python3 examples/notebook_brewing.py    out.png                    # 实验笔记本 · 贴纸：咖啡萃取实验
python3 examples/chalk_lesson.py        out.png                    # 黑板板书：为什么天空是蓝的
python3 examples/cyberpunk_neon_street.py out.png                  # 赛博朋克：霓虹不夜城
python3 examples/cartoon_toaster.py     out.png                    # 卡通手绘：早安吐司
python3 examples/isometric_weather_island.py out.png               # 等轴 2.5D：岛上的气象站
python3 examples/lineart_paper_plane.py out.png                    # 单线画：从这扇窗到那扇窗
python3 examples/soft3d_rise.py         out.png                    # 柔光 3D：浮出
python3 examples/morph_water_cycle.py   out.png                    # 形变动画：一滴水的旅程
python3 examples/newscollage_curiosity.py out.png                  # 报刊拼贴：好奇心周刊 · 拆开看看
python3 examples/aurora_morning.py      out.png                    # 弥散玻璃：晨间计划
python3 examples/bauhaus_form_colour.py out.png                    # 包豪斯几何：形与色
python3 examples/synthwave_coastline.py out.png                    # 复古 Synthwave：海岸线 1987
python3 examples/perler_strawberry_coaster.py out.png              # 拼豆：草莓杯垫
python3 examples/petroglyph_migration.py out.png                   # 岩画：迁徙季
python3 examples/tomb_harvest.py        out.png                    # 古埃及墓室壁画：尼罗河丰收
python3 examples/mosaic_harbor.py       out.png                    # 罗马马赛克：港口渔获
python3 examples/stainedglass_seasons.py out.png                   # 彩色玻璃花窗：四季之窗
python3 examples/illuminated_starchart.py out.png                  # 泥金手抄本：星辰之书
python3 examples/codex_ornithopter.py   out.png                    # 达·芬奇手稿：扑翼机
python3 examples/silhouette_family.py   out.png                    # 剪影：剪影小像
python3 examples/letterpress_circus.py  out.png                    # 凸版印刷海报：马戏团来了
python3 examples/constructivism_radio.py out.png                   # 苏联构成主义：无线电
python3 examples/artdeco_express.py     out.png                    # 装饰艺术：夜行快车
python3 examples/comic_rocket.py        out.png                    # 黄金时代漫画：火箭小队
python3 examples/popart_cat_moods.py    out.png                    # 波普丝网：猫的六种心情
python3 examples/lineprinter_launch.py  out.png                    # ASCII 字符画（行式打印机）：发射记录
python3 examples/lowpoly_canyon.py      out.png                    # 低多边形：峡谷飞行
python3 examples/stencil_kite.py        out.png                    # 喷漆模板涂鸦：放风筝
python3 examples/patch_camping.py       out.png                    # 刺绣徽章：三晚露营
python3 examples/blueprint_lighthouse.py out.png                   # 蓝图工程图：灯塔剖面
python3 examples/crayon_picnic.py       out.png                    # 儿童蜡笔画：我的周末
python3 examples/crt_weather.py         out.png                    # 绿屏终端 CRT：今天带伞吗
python3 examples/thermal_kitchen.py     out.png                    # 热成像：厨房里的温度
python3 examples/delft_canal.py         out.png                    # 代尔夫特蓝瓷砖：运河小镇 · 一阵风
python3 examples/cave_hunt.py           out.png                    # 洞穴壁画：篝火旁的岩洞
python3 examples/macpaint_garden.py     out.png                    # 1-bit 早期画图软件：窗台花园
python3 examples/blackfigure_games.py   out.png                    # 古希腊黑绘陶瓶：赛跑与赛车
python3 examples/graphite_bicycle.py    out.png                    # 铅笔素描：老街角的自行车
python3 examples/xray_luggage.py        out.png                    # X 光片：行李安检
python3 examples/rubberhose_morning.py  out.png                    # 1930 年代黑白橡皮管动画：早晨的闹钟
python3 examples/linocut_snowy_village.py out.png                  # 黑白麻胶版画：雪夜归途
python3 examples/vhs_birthday.py        out.png                    # VHS 家庭录像：吹蜡烛
python3 examples/flatvector_night_camp.py out.png                  # 扁平矢量：山间夜营
python3 examples/storybook_acorn.py     out.jpg --gif out.gif      # 绘本角色动画：小橡果的秋天
python3 examples/ballpoint_board_game.py out.png                   # 圆珠笔涂鸦：蛇梯棋大冒险
python3 examples/overlay_city_map.py    out.jpg --stages stages/   # 描图纸叠层：海港步行图
python3 examples/pastelui_packing.py    out.jpg --stages stages/   # 粉彩界面：出发前，再查一遍行李
python3 examples/grading_math_quiz.py   out.jpg --stages stages/   # 阅卷批改：数学单元测验
python3 examples/shadowpuppet_cuju.py  out.jpg --stages stages/   # 皮影戏：蹴鞠
python3 examples/penwash_neighbours.py  out.jpg --stages stages/   # 钢笔淡彩：街角速写
python3 examples/gouache_rainy_day.py   out.jpg --stages stages/   # 复古水粉：雨天三人像
python3 examples/bluebook_shared_umbrella.py out.jpg --stages stages/   # 蓝调绘本：借伞
python3 examples/jiangnan_spring_water.py out.jpg --stages stages/   # 江南园林：春水园林
python3 examples/drybrush_noodle_counter.py out.jpg --stages stages/   # 干刷色块：面馆
python3 examples/twilight_paper_kite.py out.jpg --stages stages/   # 暮色微缩绘本：夜的边上
python3 examples/nocturne_lava_sea.py out.jpg --stages stages/   # 排线夜景：熔岩入海
python3 examples/obsidianui_reading_notes.py out.jpg --stages stages/   # 笔记应用界面：小王子读书笔记
python3 examples/canvasboard_moving_plan.py out.jpg --stages stages/   # 白板卡片：搬家计划
python3 examples/flexoki_pour_over.py out.jpg --stages stages/   # Flexoki 纸面：一杯手冲咖啡
python3 examples/pencilbook_tortoise_crossing.py out.jpg --stages stages/   # 暖调彩铅绘本：大龟过河
python3 examples/colortown_festival_steps.py out.jpg --stages stages/   # 彩色小镇：雨后的节日台阶街
python3 examples/pastelvignette_marmalade_scarf.py out.jpg --stages stages/   # 色粉小像：橘猫围巾
python3 examples/poetichalloween_ghost_jar.py out.jpg --stages stages/   # 诗意万圣夜：罐子里的小幽灵
python3 examples/oilpastel_warm_cup.py out.jpg --stages stages/   # 油画棒肖像：捧着一杯热的
python3 examples/sketchbook_reading_hour.py out.jpg --stages stages/   # 手账线描：读书的午后
python3 examples/sketchbook_kite_day.py out.jpg --stages stages/   # 手账线描：放风筝（16:9）
python3 examples/spotillo_rainy_saturday.py out.jpg --stages stages/   # 日系扁平小插画：雨天的星期六（--layout wide 出 16:9）
python3 examples/grainbook_snow_walk.py out.jpg --stages stages/   # 颗粒童书：雪夜遛狗（--layout wide 出 16:9）
python3 examples/grainbook_duck_pond.py out.jpg --stages stages/   # 颗粒童书：喂鸭子（16:9）
python3 examples/dreamhills_long_walk.py out.jpg --stages stages/   # 柔光草丘：走过草丘（1:2 竖版壁纸，--preset night 星夜、noon 正午）
python3 examples/dreamhills_long_walk.py out.jpg --layout wide      # 柔光草丘：同一幅画排成 16:9
python3 examples/sunlitgreen_window_seat.py out.jpg --stages stages/   # 夏日光绿：窗边的座位（9:16 竖版壁纸，--layout wide 出 16:9，--preset late 傍晚金光）
python3 examples/sunlitgreen_stream_steps.py out.jpg --stages stages/  # 夏日光绿：溪边石阶（9:16，--layout wide 出 16:9）
```
