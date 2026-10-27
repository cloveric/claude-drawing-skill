---
name: claude绘图
description: Claude Drawing — procedural illustration with Python, numpy, and Pillow in 74 styles.
---

# Claude 绘图

用 Python（只依赖 numpy + Pillow）按笔、墨、颜料、纸的物理规律「画」图，不调用生图模型。固定随机种子可复现，也可以用 `stage()` 输出逐步绘制动画。

## 启动规则

本文件只负责**选择画风和通用流程**。不要在选择画风前加载所有画风指南：先根据需求从下面的索引选择一个风格，再只读取对应的 `styles/<slug>.md`，然后编写场景脚本。

## 通用流程

1. 定构图：远景 → 中景 → 主体 → 前景；确定焦点、留白、点睛色和文字位置。
2. 画面要解释主题本身，而不是只生成一张泛化风景图。
3. 复制最接近的范例脚本，使用对应风格指南中的 API 和质量检查清单。
4. 运行脚本并查看输出；通常迭代 2–4 轮，每轮只修最显眼的问题。
5. 固定 seed 保证可复现；需要动画时使用 `stage('name')` 和 `--stages DIR`。
6. 默认优先输出 PNG；需要交付 JPG 时使用高质量设置。

## 全局约束

- 使用 `lib/core.py` 的公共工具时，通过脚本所在位置加入 `lib` 到 `sys.path`。
- 先画背景和远景，再画主体和前景；尊重每种风格的遮挡、材质和光照模型。
- 文本应服务于构图；中英文混排时使用库提供的字体回退机制。
- 不要凭空发明风格 API；选择风格后先读对应指南，必要时再查看 `lib/<module>.py` 和范例。

## 画风索引

选择最匹配的条目，然后读取链接中的详细指南。

| 画风 | 详细指南 | 实现 | 范例 | 适合 |
|---|---|---|---|---|
| 水墨 | [inkpaint](styles/inkpaint.md) | `lib/inkpaint.py` · `Painting` | `examples/bawansiqian.py` | 禅意、古典、山水 |
| 水彩 | [watercolor](styles/watercolor.md) | `lib/watercolor.py` · `Watercolor` | `examples/watercolor_autumn.py` | 风景、花卉、清新 |
| 剪纸拼贴 | [papercut](styles/papercut.md) | `lib/papercut.py` · `Collage` | `examples/papercut_balloons.py` | 童趣、故事、手作 |
| 韩国彩铅 | [colorpencil](styles/colorpencil.md) | `lib/colorpencil.py` · `ColorPencil` | `examples/colorpencil_dessert.py` | 甜点、日常、小物 |
| 日本动漫 | [anime](styles/anime.md) | `lib/anime.py` · `Anime` | `examples/anime_summer.py` | 青春、夏日、背景美术 |
| 编辑风手绘 | [editorial](styles/editorial.md) | `lib/editorial.py` · `Editorial` | `examples/editorial_ideas.py` | 概念、商业配图 |
| 油画厚涂 | [oilpaint](styles/oilpaint.md) | `lib/oilpaint.py` · `OilPainting` | `examples/oil_wheatfield.py` | 笔触、名画感 |
| 浮世绘木版画 | [ukiyoe](styles/ukiyoe.md) | `lib/ukiyoe.py` · `Ukiyoe` | `examples/ukiyoe_fuji.py` | 日式古典、海浪 |
| 像素风 | [pixelart](styles/pixelart.md) | `lib/pixelart.py` · `PixelArt` | `examples/pixel_rainy_cafe.py` | 复古游戏、像素动画 |
| 黏土定格 | [clay](styles/clay.md) | `lib/clay.py` · `Clay` | `examples/clay_lighthouse.py` | 立体手作、童趣 |
| 蓝晒 | [cyanotype](styles/cyanotype.md) | `lib/cyanotype.py` · `Cyanotype` | `examples/cyanotype_botanicals.py` | 植物、标本、自然科学 |
| 十字绣 | [stitch](styles/stitch.md) | `lib/stitch.py` · `Stitch` | `examples/stitch_sampler.py` | 家庭、贺卡、字母 |
| 复古仪器面板 | [panel](styles/panel.md) | `lib/panel.py` · `Panel` | `examples/panel_radio.py` | 设备、仪表、复古科技 |
| 贴纸拼贴·小票 | [sticker](styles/sticker.md) | `lib/sticker.py` · `Sticker` | `examples/sticker_market.py` | 清单、购物、市集 |
| 实验笔记本 | [notebook](styles/notebook.md) | `lib/notebook.py` · `Notebook` | `examples/notebook_brewing.py` | 数据、实验、复盘 |
| 黑板板书 | [chalk](styles/chalk.md) | `lib/chalk.py` · `Chalkboard` | `examples/chalk_lesson.py` | 课堂、公式、原理 |
| 赛博朋克 | [cyberpunk](styles/cyberpunk.md) | `lib/cyberpunk.py` · `Cyberpunk` | `examples/cyberpunk_neon_street.py` | 夜景、城市、霓虹 |
| 卡通手绘 | [cartoon](styles/cartoon.md) | `lib/cartoon.py` · `Cartoon` | `examples/cartoon_toaster.py` | 拟人、步骤、动画 |
| 等轴 2.5D | [isometric](styles/isometric.md) | `lib/isometric.py` · `Isometric` | `examples/isometric_weather_island.py` | 系统概览、微缩模型 |
| 单线画 | [lineart](styles/lineart.md) | `lib/lineart.py` · `LineArt` | `examples/lineart_paper_plane.py` | 极简、路线、一笔画 |
| 柔光 3D | [soft3d](styles/soft3d.md) | `lib/soft3d.py` · `Soft3D` | `examples/soft3d_rise.py` | 糖果色、立体标题 |
| 形变动画 | [morph](styles/morph.md) | `lib/morph.py` · `Morph` | `examples/morph_water_cycle.py` | 变化、循环、演变 |
| 报刊拼贴 | [newscollage](styles/newscollage.md) | `lib/newscollage.py` · `NewsCollage` | `examples/newscollage_curiosity.py` | 杂志、复古拼贴 |
| 弥散玻璃 | [aurora](styles/aurora.md) | `lib/aurora.py` · `Aurora` | `examples/aurora_morning.py` | App、界面、科技感 |
| 包豪斯几何 | [bauhaus](styles/bauhaus.md) | `lib/bauhaus.py` · `Bauhaus` | `examples/bauhaus_form_colour.py` | 海报、原则、几何 |
| 复古 Synthwave | [synthwave](styles/synthwave.md) | `lib/synthwave.py` · `Synthwave` | `examples/synthwave_coastline.py` | 80 年代、复古未来 |
| 拼豆 | [perler](styles/perler.md) | `lib/perler.py` · `Perler` | `examples/perler_strawberry_coaster.py` | DIY、像素实物 |
| 岩画 | [petroglyph](styles/petroglyph.md) | `lib/petroglyph.py` · `Petroglyph` | `examples/petroglyph_migration.py` | 史前、起源、迁徙 |
| 古埃及墓室壁画 | [tomb](styles/tomb.md) | `lib/tomb.py` · `TombPainting` | `examples/tomb_harvest.py` | 古文明、工序叙事 |
| 罗马马赛克 | [mosaic](styles/mosaic.md) | `lib/mosaic.py` · `Mosaic` | `examples/mosaic_harbor.py` | 古典、海洋、图鉴 |
| 彩色玻璃花窗 | [stainedglass](styles/stainedglass.md) | `lib/stainedglass.py` · `StainedGlass` | `examples/stainedglass_seasons.py` | 教堂、中世纪、季节 |
| 泥金手抄本 | [illuminated](styles/illuminated.md) | `lib/illuminated.py` · `Illuminated` | `examples/illuminated_starchart.py` | 古籍、典藏、天文 |
| 达·芬奇手稿 | [codex](styles/codex.md) | `lib/codex.py` · `Codex` | `examples/codex_ornithopter.py` | 发明、工程、研究笔记 |
| 剪影 | [silhouette](styles/silhouette.md) | `lib/silhouette.py` · `Silhouette` | `examples/silhouette_family.py` | 肖像、家族、纪念 |
| 凸版印刷海报 | [letterpress](styles/letterpress.md) | `lib/letterpress.py` · `Letterpress` | `examples/letterpress_circus.py` | 复古海报、活动 |
| 苏联构成主义 | [constructivism](styles/constructivism.md) | `lib/constructivism.py` · `Constructivism` | `examples/constructivism_radio.py` | 工业、技术、强对角线 |
| 装饰艺术 | [artdeco](styles/artdeco.md) | `lib/artdeco.py` · `ArtDeco` | `examples/artdeco_express.py` | 旅行、速度、黄金年代 |
| 黄金时代漫画 | [comic](styles/comic.md) | `lib/comic.py` · `ComicCover` | `examples/comic_rocket.py` | 冒险、角色、对白框 |
| 波普丝网 | [popart](styles/popart.md) | `lib/popart.py` · `PopSilkscreen` | `examples/popart_cat_moods.py` | 多版本、潮流海报 |
| ASCII 行式打印机 | [lineprinter](styles/lineprinter.md) | `lib/lineprinter.py` · `LinePrinter` | `examples/lineprinter_launch.py` | 计算机史、日志、打印 |
| 低多边形 | [lowpoly](styles/lowpoly.md) | `lib/lowpoly.py` · `LowPoly` | `examples/lowpoly_canyon.py` | 复古 3D、游戏感 |
| 喷漆模板涂鸦 | [stencil](styles/stencil.md) | `lib/stencil.py` · `Stencil` | `examples/stencil_kite.py` | 街头、口号、社区 |
| 刺绣徽章 | [patch](styles/patch.md) | `lib/patch.py` · `Patch` | `examples/patch_camping.py` | 成就、户外、社团 |
| 蓝图工程图 | [blueprint](styles/blueprint.md) | `lib/blueprint.py` · `Blueprint` | `examples/blueprint_lighthouse.py` | 建筑、机械、剖面 |
| 儿童蜡笔画 | [crayon](styles/crayon.md) | `lib/crayon.py` · `Crayon` | `examples/crayon_picnic.py` | 儿童、家庭、教育 |
| 绿屏终端 CRT | [crt](styles/crt.md) | `lib/crt.py` · `CRTTerminal` | `examples/crt_weather.py` | 终端、命令行、状态 |
| 热成像 | [thermal](styles/thermal.md) | `lib/thermal.py` · `Thermal` | `examples/thermal_kitchen.py` | 温度、检测、能耗 |
| 代尔夫特蓝瓷砖 | [delft](styles/delft.md) | `lib/delft.py` · `DelftTile` | `examples/delft_canal.py` | 荷兰、运河、蓝白装饰 |
| 洞穴壁画 | [cave](styles/cave.md) | `lib/cave.py` · `CavePainting` | `examples/cave_hunt.py` | 远古、火与动物 |
| 1-bit 早期画图软件 | [macpaint](styles/macpaint.md) | `lib/macpaint.py` · `MacPaint` | `examples/macpaint_garden.py` | 早期 GUI、黑白像素 |
| 古希腊黑绘陶瓶 | [blackfigure](styles/blackfigure.md) | `lib/blackfigure.py` · `BlackFigure` | `examples/blackfigure_games.py` | 古希腊、体育、博物馆 |
| 铅笔素描 | [graphite](styles/graphite.md) | `lib/graphite.py` · `Graphite` | `examples/graphite_bicycle.py` | 写生、观察、静物 |
| X 光片 | [xray](styles/xray.md) | `lib/xray.py` · `XRay` | `examples/xray_luggage.py` | 透视、内部构造、检测 |
| 黑白橡皮管动画 | [rubberhose](styles/rubberhose.md) | `lib/rubberhose.py` · `RubberHose` | `examples/rubberhose_morning.py` | 复古动画、拟人物件 |
| 黑白麻胶版画 | [linocut](styles/linocut.md) | `lib/linocut.py` · `Linocut` | `examples/linocut_snowy_village.py` | 冬夜、民间故事、强对比 |
| VHS 家庭录像 | [vhs](styles/vhs.md) | `lib/vhs.py` · `VHSCamcorder` | `examples/vhs_birthday.py` | 家庭回忆、found footage |
| 扁平矢量 | [flatvector](styles/flatvector.md) | `lib/flatvector.py` · `FlatVector` | `examples/flatvector_night_camp.py` | 风景、旅程、现代插画 |
| 绘本角色动画 | [storybook](styles/storybook.md) | `lib/storybook.py` · `Storybook` | `examples/storybook_acorn.py` | 角色旅程、成长、绘本 |
| 圆珠笔涂鸦 | [ballpoint](styles/ballpoint.md) | `lib/ballpoint.py` · `Ballpoint` | `examples/ballpoint_board_game.py` | 随手涂鸦、棋盘、日常 |
| 描图纸叠层 | [overlay](styles/overlay.md) | `lib/overlay.py` · `Overlay` | `examples/overlay_city_map.py` | 地图、路线、分层信息 |
| 粉彩界面 | [pastelui](styles/pastelui.md) | `lib/pastelui.py` · `PastelUI` | `examples/pastelui_packing.py` | 产品界面、功能页 |
| 阅卷批改 | [grading](styles/grading.md) | `lib/grading.py` · `Grading` | `examples/grading_math_quiz.py` | 检查、评分、验收 |
| 皮影戏 | [shadowpuppet](styles/shadowpuppet.md) | `lib/shadowpuppet.py` · `ShadowPuppet` | `examples/shadowpuppet_cuju.py` | 民间艺术、节庆、戏曲 |
| 钢笔淡彩 | [penwash](styles/penwash.md) | `lib/penwash.py` · `PenWash` | `examples/penwash_neighbours.py` | 街角速写、人物小景 |
| 复古水粉 | [gouache](styles/gouache.md) | `lib/gouache.py` · `GouachePortrait` | `examples/gouache_rainy_day.py` | 肖像、绘本、怀旧 |
| 蓝调绘本 | [bluebook](styles/bluebook.md) | `lib/bluebook.py` · `BlueBook` | `examples/bluebook_shared_umbrella.py` | 温柔故事、雨天 |
| 江南园林 | [jiangnan](styles/jiangnan.md) | `lib/jiangnan.py` · `JiangnanGarden` | `examples/jiangnan_spring_water.py` | 园林、江南、春景 |
| 干刷色块 | [drybrush](styles/drybrush.md) | `lib/drybrush.py` · `DryBrushBlocks` | `examples/drybrush_noodle_counter.py` | 海报、街坊、餐饮 |
| 暮色微缩绘本 | [twilight](styles/twilight.md) | `lib/twilight.py` · `TwilightStorybook` | `examples/twilight_paper_kite.py` | 黄昏、夜晚、童话 |
| 排线夜景 | [nocturne](styles/nocturne.md) | `lib/nocturne.py` · `Nocturne` | `examples/nocturne_lava_sea.py` | 夜景、版画、火光 |
| 笔记应用界面 | [obsidianui](styles/obsidianui.md) | `lib/obsidianui.py` · `ObsidianUI` | `examples/obsidianui_reading_notes.py` | 知识库、Markdown、代码 |
| 白板卡片 | [canvasboard](styles/canvasboard.md) | `lib/canvasboard.py` · `CanvasBoard` | `examples/canvasboard_moving_plan.py` | 计划、卡片、关系图 |
| Flexoki 纸面 | [flexoki](styles/flexoki.md) | `lib/flexoki.py` · `FlexokiPaper` | `examples/flexoki_pour_over.py` | 文档、教程、图表 |
| 暖调彩铅绘本 | [pencilbook](styles/pencilbook.md) | `lib/pencilbook.py` · `PencilStorybook` | `examples/pencilbook_tortoise_crossing.py` | 温暖童书、陪伴故事 |

## 选定画风后

读取对应的 `styles/<slug>.md`。该文件包含该风格的 API 速查、实现约束、范例入口和质量检查清单；如需更多细节，再查看对应的 Python 模块。
