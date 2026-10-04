---
name: claude绘图
description: Claude 绘图 / Claude Drawing —— 不借助任何生图模型，由 Claude 用代码一笔一笔「画」出图片（程序化绘画）。内置六十种画风：中国水墨、水彩、剪纸拼贴、韩国彩铅、日本动漫、编辑风手绘（Riso）、油画厚涂（梵高式流向笔触+颜料浮雕打光）、浮世绘木版画（晕色、木纹、墨线主版、青海波）、像素风（低分辨率+Bayer 抖动+像素字体）、黏土定格（高度图捏出的彩泥+影棚打光）、蓝晒（普鲁士蓝日光晒图，植物剪影透光）、十字绣（Aida 布十字绣+回针绣+缎面绣+法式结）、复古仪器面板（60 年代收音机/仪器正面：柚木、拉丝铝、旋钮、刻度窗、指示灯）、贴纸拼贴·小票（模切乙烯贴纸、热敏小票、和纸胶带、吊牌、橡皮章）、实验笔记本·贴纸（线圈方格本、铅笔图表、荧光笔、红笔圈、便利贴）、黑板板书（墨绿石板、粉笔颗粒、板擦残影、示意图与公式）、赛博朋克（雨夜霓虹街道、玻璃管霓虹招牌、全息广告、湿路面倒影）、卡通手绘（蓝铅笔稿、毛笔线、错位平涂、赛璐璐阴影、逐帧抖线）、等轴 2.5D（正等轴微缩模型、一个太阳照出三面明暗、悬浮数据卡）、单线画（一根不断开的线一笔画完、唯一点睛色）、柔光 3D（光线追踪的糖果色小球海和鼓鼓的软字、景深）、形变动画（一条轮廓依次变形、洋葱皮残影、缓动曲线）、报刊拼贴（牛皮纸、手撕旧报纸、网点老照片、勒索信拼贴字）、弥散玻璃（弥散渐变、磨砂玻璃卡片界面）、包豪斯几何（三原色几何、丝网印刷海报）、复古 Synthwave（切口落日、霓虹网格、镀铬字、录像带质感）、拼豆（钉板上的熔珠小管、熨烫熔合）、岩画（沙漠漆上凿出的凹坑图形、新旧凿痕、剥落）、古埃及墓室壁画（灰泥墙、红格起稿、分栏叙事、象形文字、剥落）、罗马马赛克（石子与玻璃沿轮廓一排排铺、灰缝、燕尾铭牌）、彩色玻璃花窗（哥特尖拱窗、通体着色玻璃、grisaille 彩绘与银染、铅条、透光）、泥金手抄本（羊皮纸、鹅毛笔哥特体、朱红标题、打磨金箔首字母）、达·芬奇手稿（铁胆墨水、左手排线、红粉笔、镜像手写、机械分解图）、剪影（黑纸剪出的侧影小像、薄金粉、椭圆金框）、凸版印刷海报（木活字、红黑双色错版、木刻插图）、苏联构成主义（红黑两版、斜条与楔形、西里尔大字、网点照片拼贴）、装饰艺术 Art Deco（1930 年代喷枪流线型海报、交替射线、阶梯高楼、金色 Deco 字）、黄金时代漫画（毛笔墨线、Ben-Day 网点、四色错版、新闻纸）、波普丝网（多格撞色平涂 + 错位的照相黑版）、ASCII 字符画（行式打印机、绿条连续纸、叠打）、低多边形（1999 年代 3D：平面着色、仿射贴图、逐顶点雾、15 位色抖动）、喷漆模板涂鸦（混凝土墙上多层卡纸模板喷绘、雾化与滴痕）、刺绣徽章（牛仔布上的机绣徽章：填充绣、缎面绣、锁边）、蓝图工程图（描图墨线晒成蓝底白线）、儿童蜡笔画（小孩在糙纸上的蜡笔涂抹）、绿屏终端 CRT（荧光字符画、扫描线、余辉）、热成像（先画温度场再上伪彩色）、代尔夫特蓝瓷砖（锡釉砖上的钴蓝手绘）、洞穴壁画（火光下的赭石、吹喷手印）、1-bit 早期画图软件（黑白整屏、8×8 图案填充）、古希腊黑绘陶瓶（黑釉剪影、刻线、饰带展开图）、铅笔素描（石墨排线、擦笔、边缘只剩线稿）、X 光片（安检透视、轮廓发亮、伪彩）、1930 年代黑白橡皮管动画（白手套、饼切眼、老胶片）、黑白麻胶版画（刻刀减法、手拓发花、套色错版）、VHS 家庭录像（钨丝灯偏色、色度渗色、REC）、扁平矢量（分层几何色块、七色、层间投影）、绘本角色动画（小角色挤压拉伸的真动画）、圆珠笔涂鸦（蓝红圆珠笔线稿、墨团、彩铅、页边涂鸦）、描图纸叠层（灯箱上的黑线底图 + 一张张单色描图纸叠片：正片叠底、套准十字、定位钉、绘图胶带）。用户说「claude绘图」「用代码画」「你自己画」「不用生图模型画」「程序化绘画」，或点名以上任一画风（含黏土、彩泥、定格动画、蓝晒、晒图、十字绣、刺绣、复古面板、老式收音机、贴纸、小票、收据、手帐拼贴、实验笔记本、方格本、荧光笔、便利贴、黑板、板书、粉笔、赛博朋克、霓虹、雨夜街道、卡通、手绘卡通、逐帧手绘、抖线、等轴、2.5D、微缩模型、单线画、一笔画、线条动画、柔光 3D、3D 渲染、C4D 风、软糖字、小球海、形变、变形动画、报刊拼贴、剪报、达达、勒索信字、网点印刷、弥散渐变、玻璃拟态、毛玻璃、包豪斯、几何构成、丝网印刷、Synthwave、蒸汽波、合成器浪潮、80 年代复古、拼豆、拼拼豆、熔珠、熨豆、豆豆画、钉板、烫豆、岩画、岩刻、凿刻、石刻、沙漠漆、史前壁刻、大角羊、古埃及、埃及壁画、墓室壁画、法老时代、象形文字、尼罗河、底比斯、罗马马赛克、马赛克镶嵌、镶嵌画、石子拼画、地砖画、古罗马地板、彩色玻璃、彩绘玻璃、花窗、玻璃花窗、教堂花窗、哥特花窗、铅条玻璃、泥金手抄本、手抄本、彩饰手抄本、中世纪手稿、羊皮纸、哥特体、花体首字母、泥金、贴金、星盘、达芬奇、达·芬奇、达芬奇手稿、手稿风、文艺复兴手稿、发明手稿、镜像字、镜像书写、扑翼机、红粉笔、钢笔排线、机械草图、分解图、剪影、剪影肖像、侧影、侧面像、黑纸剪影、剪影小像、椭圆金框、乔治时代肖像、摄政时期肖像、凸版印刷、活版印刷、木活字、铅字海报、马戏团海报、复古海报、老海报、19 世纪海报、双色套印、错版、套色错位、木刻插图、构成主义、苏联海报、苏联构成主义、俄国先锋派、罗德琴科风、红黑海报、照片蒙太奇、照片拼贴海报、西里尔字、装饰艺术、装饰风、流线型、流线型海报、1930 年代海报、旅行海报、铁路海报、火车海报、喷枪画、喷笔画、阶梯高楼、射线背景、盖茨比风、黄金时代漫画、老漫画、复古漫画、美漫封面、漫画封面、Ben-Day 网点、本戴点、网点上色、四色印刷、四色错版、新闻纸、对白框、拟声字、1940 年代漫画、波普、波普艺术、波普丝网、沃霍尔风、丝网版画头像、撞色头像、多格重复头像、六宫格撞色头像、ASCII、字符画、字符艺术、文字画、行式打印机、绿条纸、连续打印纸、针孔打印纸、老电脑打印、叠打、低多边形、低面数、低模、多边形风、千禧年 3D、90 年代 3D、复古 3D 游戏、老游戏截图、PS1 风、N64 风、平面着色、线框、游戏 HUD、飞行游戏、穿环、喷漆、模板涂鸦、镂空模板、喷漆模板、模板喷绘、街头涂鸦、街头艺术、墙绘、滴漆、班克西风格、刺绣徽章、徽章、布章、臂章、刺绣贴、绣标、锁边、牛仔外套徽章、户外徽章、营地徽章、弧形条章、蓝图、工程图、施工图、蜡笔画、儿童画、绿屏终端、CRT、显像管、热成像、热像仪、温度图、代尔夫特、荷兰蓝瓷砖、洞穴壁画、史前壁画、赭石、1-bit、黑白画图软件、MacPaint 风、黑绘、古希腊陶瓶、希腊瓶画、铅笔素描、素描、铅笔画、X 光、X 光片、安检图像、橡皮管动画、黑白卡通、老动画、麻胶版画、黑白版画、藏书票、VHS、家庭录像、录像带、扁平插画、扁平风、矢量插画、绘本动画、角色动画、挤压拉伸、圆珠笔、圆珠笔涂鸦、原子笔、页边涂鸦、课本涂鸦、手画棋盘、描图纸、硫酸纸、叠片、叠层、分色片、灯箱、拷贝台、透光台、套准、定位钉），或 "draw it yourself", "paint with code", "procedural painting", "watercolor / collage / colored pencil / anime / editorial / impasto oil / ukiyo-e / pixel art / clay / claymation / cyanotype / sun print / cross-stitch / embroidery / retro instrument panel / vintage radio / sticker collage / receipt / lab notebook / graph paper / chalkboard / blackboard / cyberpunk / neon city / cartoon / hand-drawn animation / isometric / 2.5D / continuous line / one-line drawing / soft 3D / 3D render / puffy letters / ball pit / shape morph / morphing / newspaper collage / Dada / ransom note / halftone / glassmorphism / aurora gradient / Bauhaus / geometric poster / screen print / synthwave / retrowave / outrun / perler beads / hama beads / artkal / fuse beads / melty beads / pegboard beads / petroglyph / rock art / rock carving / desert varnish / Egyptian tomb painting / ancient Egypt / hieroglyphs / Theban tomb / Roman mosaic / floor mosaic / tesserae / opus vermiculatum / Pompeii mosaic / stained glass / leaded glass / church window / Gothic window / grisaille / illuminated manuscript / medieval manuscript / book of hours / gold leaf / illuminated initial / blackletter / vellum / astrolabe / da Vinci notebook / Leonardo codex / Renaissance sketchbook / mirror writing / iron-gall ink / red chalk / sanguine / ornithopter / exploded view / inventor's sketch / silhouette / silhouette portrait / cut-paper profile / shade portrait / Georgian portrait / Regency portrait / oval gilt frame / letterpress / wood type / playbill / circus poster / Victorian poster / two-colour misregistration / woodcut poster / constructivism / constructivist poster / Soviet avant-garde / Russian avant-garde / Rodchenko style / photomontage poster / art deco / streamline moderne / 1930s travel poster / railway poster / airbrush poster / sunburst rays / Gatsby style / golden age comic / vintage comic book / comic cover / Ben-Day dots / four-color printing / newsprint / speech balloon / pulp cover / pop art / Warhol-style / pop silkscreen / silkscreen portrait / repeated pop portrait grid / ASCII art / text art / typewriter art / line printer / greenbar / fanfold paper / tractor feed / overstrike / printer plot / low poly / low-poly / retro 3D / 90s 3D game / PS1 style / N64 style / software rasterizer / flat shading / affine texture mapping / vertex fog / game HUD / stencil / stencil graffiti / spray paint stencil / street art / drips and overspray / Banksy-style stencil / embroidered patch / embroidery patch / iron-on patch / sew-on patch / merit badge / camp badge / merrow border / rocker patch / denim jacket patches / blueprint / technical drawing / crayon / kid's drawing / CRT terminal / green screen / thermal camera / thermal imaging / Delft tiles / Delft blue / cave painting / ochre / Lascaux-style / 1-bit / MacPaint-style / black-figure / Greek vase / pencil drawing / graphite / X-ray / baggage scanner / rubber hose / 1930s cartoon / linocut / lino print / VHS / home video / flat vector / flat illustration / storybook animation / squash and stretch / ballpoint / biro / ballpoint doodle / margin doodles / hand-drawn board game / overlay sheets / tracing-paper overlays / light box / colour separations / registration marks / acetate overlay without an image model" 时使用；也用于需要逐步画出（draw-on）动画的插画。单独说「剪纸」指剪纸拼贴、「刺绣」指十字绣、「丝网印刷 / screen print」指包豪斯几何；「打马赛克」是打码，不是马赛克画风；单说「蓝图」指蓝图工程图，「蓝晒 / 晒图」仍指蓝晒；「铅笔 / 素描」指铅笔素描，「彩铅」指韩国彩铅；「像素」仍指像素风，「1-bit / 黑白画图软件」指 1-bit 早期画图软件；「霓虹」仍指赛博朋克；「喷漆 / 街头涂鸦」仍指喷漆模板涂鸦，「圆珠笔 / 随手涂鸦 / 页边涂鸦」指圆珠笔涂鸦；「描图纸 / 硫酸纸 / 叠片 / 灯箱」指描图纸叠层（蓝图工程图那张描图布是晒成蓝图的，不是叠片）。
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
| 岩画（凿刻砂岩） | `lib/petroglyph.py` · `Petroglyph` | `examples/petroglyph_migration.py` 迁徙季（带沙漠漆的砂岩岩面：一群大角羊朝同一方向往上走，一串偶蹄印通向同心圆水源，弓手和举投矛器的猎人等在后面；新月和一个月的计日刻痕、螺旋太阳、岩檐下一大一小两只手印；新、中、旧三档凿痕，几乎被漆盖回的旧符号；渗漆的裂缝、鲜橙色剥落疤、壳状地衣；左上低角度侧光） | 约 10 秒 |
| 古埃及墓室壁画 | `lib/tomb.py` · `TombPainting` | `examples/tomb_harvest.py` 尼罗河丰收（底比斯墓室的一面墙，三栏讲一件事：犁地播种（并轭的牛、扶犁人、撒种人、挥锄人），割二粒小麦（弯腰的割麦人、拾穗的女人、挂水囊的无花果树），书吏点数粮袋（蹲坐的书吏、堆成 5-4-3 的 12 袋粮和上方的象形数字 12、用量斗倒粮的人）；按身份放大的庄园总管、伪象形文字栏、凯凯尔饰带、墙脚的尼罗河；剥落处露出红格和红稿，灰泥脱落、裂缝、潮痕、烟熏） | 约 4 秒 |
| 罗马马赛克 | `lib/mosaic.py` · `Mosaic` | `examples/mosaic_harbor.py` 港口渔获 · The Day's Catch（赭红起稿的灰浆床上铺约一万六千块石子与玻璃：黑白奔浪纹边框、火焰灯塔、船首画眼的渔船和鼓起的方帆、挑在杆上的渔网、把鱼从网里拖走的章鱼、游鱼和海鸥；燕尾铭牌 CAPTVRA · DIEI / ET POLYPVS FVR「今日渔获——以及章鱼小偷」；人物沿轮廓一排排铺，背景平铺并留光环；脱落处露出石子方坑，沉降裂缝，灰缝积灰） | 约 12 秒 |
| 彩色玻璃花窗 | `lib/stainedglass.py` · `StainedGlass` | `examples/stainedglass_seasons.py` 四季之窗 · Window of the Seasons（石墙上四扇哥特尖拱窗，同一棵树的春夏秋冬：春花与燕子、夏天的苹果和一窝雏鸟、秋天金红树冠和离开的雁阵、冬天积雪的枝和知更鸟，太阳高度随季节变；VER / AESTAS / AVTVMNVS / HIEMS 银染题字带；铅条与焊点、横铁条、一处补过的裂片，窗侧斜面和窗台上的彩色光） | 约 4 秒 |
| 泥金手抄本 | `lib/illuminated.py` · `Illuminated` | `examples/illuminated_starchart.py` 星辰之书 · Liber Stellarum（暗色书桌上摊开的天文书。左页「行星的次序」：打磨贴金方框里的玫瑰色 Q 首字母，字腔里是夜空和观星塔；鹅毛笔哥特体伪拉丁正文、朱红标题、长出常春藤花枝的条形边框、一幅诸天圆图。右页「怎样量一颗星的高度」：蓝色首字母 O 配红色花笔卷须，按纬度 48° 投影的尺规星盘，规尺瞄向页边的贴金星。羊皮纸毛孔、针孔与打格线、背面透字、破洞、狐斑、金箔剥落露出红色底料） | 约 9 秒 |
| 达·芬奇手稿 | `lib/codex.py` · `Codex` | `examples/codex_ornithopter.py` 扑翼机（裱在卡纸上、缺一角的泛黄帘纹纸；一串飞鸟画出一次振翅，红粉笔鸢翼写生和一根大羽毛；中间是蝙蝠翼扑翼机仰视图：右翼用左手「\」排线画完，左翼只起了头、露着铅笔稿；尖笔圆规画的比例圆，曲柄、灯笼齿轮、冠齿轮、滑轮的传动分解图，腕关节特写，划掉的废稿；右到左的镜像伪文笔记、墨点、霉斑、水渍） | 约 8 秒 |
| 剪影 | `lib/silhouette.py` · `Silhouette` | `examples/silhouette_family.py` 剪影小像（木版印花条纹墙纸上，挂镜线铜钩的绞丝绳吊着三幅椭圆金框剪影：中间是戴鸵鸟羽毛宽檐帽、螺旋垂卷的女主人，右边一艘满帆回家的双桅横帆船，左边坐在流苏垫子上望着她的猫；单独剪下的羽枝、睫毛、胡须和缆绳，剪空的猫眼和蕾丝孔；薄金粉、铁胆墨圆体题签、玻璃背面的金线圈、凸面玻璃反光、棱顶磨出红色底漆的旧金框） | 约 3 秒 |
| 凸版印刷海报 | `lib/letterpress.py` · `Letterpress` | `examples/letterpress_circus.py` 马戏团来了（1890 年代红黑两色马戏团海报：左栏每行木活字排满版心——THE GRAND TRAVELLING、带投影的红色大字 CIRCUS、宋体黑木活字「马戏团来了」、星号节目单；右边木刻：走钢丝的舞者端着平衡杆，下面戴非斯帽的大象踩在条纹鼓上扬鼻致意，40 FT. 尺寸线；红版色块与黑版轮廓错开几像素；三折折痕裂墨、贴上的日期条 SATURDAY · MAY 17、钉孔锈斑、泛黄与霉斑） | 约 6 秒 |
| 苏联构成主义 | `lib/constructivism.py` · `Constructivism` | `examples/constructivism_radio.py` 无线电 · РАДИО（虚构的 1920 年代无线电爱好者杂志封面，红黑两版：仰拍的双曲面网格广播塔印成网点、叠在红色圆盘上，塔尖射出红色楔形和越传越细的黑色波前，送进剪刀剪下的网点照片——带号角喇叭的电子管收音机；黑色斜条里反白 СЛУШАЙТЕ ВЕСЬ МИР（收听全世界），粗体压缩西里尔大字 РАДИО，三个编号标注；对折两次的折痕裂墨、霉斑、水渍潮线、图钉锈孔） | 约 6 秒 |
| 装饰艺术（Art Deco） | `lib/artdeco.py` · `ArtDeco` | `examples/artdeco_express.py` 夜行快车 · Night Express（1930 年代喷枪流线型铁路海报：午夜蓝长渐变天空、满月外一圈交替射线、探照灯；雾中远城和阶梯退台高楼，钟楼的钟停在 11:40；河面把城市和月亮反射成横向波纹；栗红流线型列车从城里驶上拱桥迎面而来，金色速度线收拢在车鼻上，头灯照亮铁轨；Deco 金字 NIGHT EXPRESS、阶梯角双金线边框；全画没有一根描边，形体全靠明暗） | 约 12 秒 |
| 黄金时代漫画 | `lib/comic.py` · `ComicCover` | `examples/comic_rocket.py` 火箭小队 No. 3（1940 年前后的报摊漫画封面：朝灭点挤出的立体刊名 ROCKET SQUAD、价格框和黄色旁白框；暮色天空分档网点、大月亮；红色火箭起飞，June 舰长指着月亮喊「NEXT STOP -- THE MOON!」，后座小狗 Pip 戴着护目镜；没赶上的机修工 Sparky 吊在绳梯上喊「HEY!! WAIT FOR ME!!」；拟声字 WHOOOSH!；毛笔墨线与羽状排线、Ben-Day 网点、三色版错位、泛黄新闻纸、书脊裂纹和生锈订书钉） | 约 5 秒 |
| 波普丝网 | `lib/popart.py` · `PopSilkscreen` | `examples/popart_cat_moods.py` 猫的六种心情（白底漆帆布用胶带隔出 3×2 六格，同一只虎斑猫按顺序讲一件小事：歪头好奇 → 馋得吐舌头 → 吃到了眯眼笑 → 被抓包瞪圆眼 → 压耳哈气 → 歪头睡着；每格先手涂一套撞色、描得很松，再刮印同一块照相黑版，中间调成 45° 粗网点；六格放版的位置、角度和墨量各不相同：糊版、缺墨、横刮、印了两次留灰影、干版露底） | 约 3 秒 |
| ASCII 字符画（行式打印机） | `lib/lineprinter.py` · `LinePrinter` | `examples/lineprinter_launch.py` 发射记录（桌上一整张 1970 年代 132 列绿条连续纸，两侧导孔、微孔撕线；左边整幅火箭发射的字符画：尖拱头锥、. : + % # 侧光箭身、叠打 #@ 的滚转标记、从喷口往下变宽的尾焰亮柱扎进翻滚的烟云，旁边是桁架勤务塔、塔吊、远处水塔、清晨太阳和人字形鸟群；右栏是事件日志、高度-时间打印机绘图和通道状态表；鼓式打印机的上下跳字、弱锤淡列、色带渐淡；读的人用红圆珠笔打勾、圈点、写了 on plan） | 约 2.3 秒 |
| 低多边形（1999 年代 3D） | `lib/lowpoly.py` · `LowPoly` | `examples/lowpoly_canyon.py` 峡谷飞行 · Canyon Run（一帧虚构的 1999 年飞行游戏：小特技飞机在沙漠峡谷的右弯处压坡度，对准九个金环里的第五个，第六个挂在天然石拱下；阶梯状分层岩壁、起伏小面的河、十字插片杜松、雾里化开的方山；半透明螺旋桨盘、金环闪光、镜头光晕；384×216 帧缓冲、15 位色 4×4 有序抖动、无平滑放大 5 倍；HUD：金环计数 04/09、单圈时间、阶梯速度条、赛道小地图） | 约 0.2 秒 |
| 喷漆模板涂鸦 | `lib/stencil.py` · `Stencil` | `examples/stencil_kite.py` 放风筝 · Hold On（木纹模板清水混凝土墙：木纹、浆棱、对拉螺栓孔、锈水雨痕、返潮泛碱、发丝裂缝；三张卡纸模板白 → 灰 → 黑喷出的小孩：毛线帽、羽绒服、往前飘的条纹围巾，身子后仰攥着线轮；徒手喷的风筝线连到左上角的红色菱形风筝；同一张小模板转着角度喷的燕子和树叶；带桥的 HOLD ON 模板字；清晰核心、外溢雾化、飞沫、滴痕；滚筒灰漆盖掉的旧签名、被水枪冲淡的粉色签名） | 约 6 秒 |
| 刺绣徽章 | `lib/patch.py` · `Patch` | `examples/patch_camping.py` 三晚露营（牛仔夹克后背，过肩缝压着双道明线，一晚一枚徽章：第一晚是热切缎面边的拱形异形章——日落分层天空、远山、湖面倒影、亮灯的帐篷；第二晚是金色锁边圆章——雪峰、松林、营火与火星、弯月，缎面字 HIGH CAMP / NIGHT 2，上方弧形条章 THREE NIGHTS OUT；第三晚是正在手缝的指南针章，针和线还留在牛仔布上；一条刺子绣虚线把三枚徽章串成路线） | 约 6 秒 |
| 蓝图工程图 | `lib/blueprint.py` · `Blueprint` | `examples/blueprint_lighthouse.py` 灯塔剖面 · Halvard Rock Light（1911 年一套灯塔施工图，描图布上墨后晒成蓝图：南立面的花岗岩砌层和背光一侧的明暗线；A–A 剖面里越往上越薄的石墙、绕空心中柱盘上去的悬挑石阶、值守室的钟表机构；+6.50 平面和指北针；详图 1 讲灯焰、棱镜和透镜怎样送出一束平行光；总说明、比例尺、修改栏、中英文标题栏；折成六折、朝外那格褪色、碱性水渍、图钉孔，工地工程师用红蜡笔圈出楼梯批注） | 约 5 秒 |
| 儿童蜡笔画 | `lib/crayon.py` · `Crayon` | `examples/crayon_picnic.py` 我的周末（六岁小孩在糙纸上用蜡笔画的一家人野餐：戴墨镜的笑脸太阳、四种颜色写的歪扭标题「我的周末!」、风筝和彩虹，天空绕着东西涂、越往下越稀；冒卷烟的小房子和苹果树；爸爸、妈妈和我手拉手站在红格子野餐布后面，小狗扑向皮球；郁金香、蝴蝶和签名「朵朵 6岁」；纸上还躺着一根用秃的红蜡笔、一截断了的蓝蜡笔和蜡屑） | 约 8 秒 |
| 绿屏终端 CRT（荧光字符画） | `lib/crt.py` · `CRTTerminal` | `examples/crt_weather.py` 今天带伞吗 · Bring an Umbrella?（80 年代米色机壳的视频终端上敲了一条 forecast 命令，回来一屏绿色 P1 荧光字符画：一整天从左到右画成一条——清晨的太阳、积云、14:00–17:30 在小镇上下雨的雷暴云（闪电、带余辉的雨丝）、雨后碎云、夜里的月牙和灯塔光；下面同一条时间轴上的扫描线气温曲线、八分块雨量柱和反白的「umbrella? YES」；双倍高标题、方框线、烧着旧字的状态栏；扫描线、光晕、桶形畸变，机壳斜面映着绿光） | 约 7 秒 |
| 热成像 | `lib/thermal.py` · `Thermal` | `examples/thermal_kitchen.py` 厨房里的温度 · Kitchen Heat Map（晚饭时分厨房的热像仪画面：汤锅的蒸汽卷进抽油烟机，抛光锅盖因发射率低读数低一档；水壶喷出一道蒸汽；烤箱门封漏热，把手上的湿抹布比室温还凉；刚出炉的面包冒热气；冰箱门没关，冷气顺着抽屉淌到地砖上铺成冷舌；猫踩过冷坑又回到暖砖上，留下一串越早越淡的暖脚印；点测温、区域框、沿脚印的线剖面，读数全从画面上读出来；480×270 传感器、噪声与竖条纹、铁红色板） | 约 2 秒 |
| 代尔夫特蓝瓷砖 | `lib/delft.py` · `DelftTile` | `examples/delft_canal.py` 运河小镇 · 一阵风 De Windvlaag（一面锡釉砖墙：中间 11 × 7 块砖连成一幅砖画，四周是四角带角饰、圆框里画小图的单块砖。一阵西风吹过运河小镇：风车在转，平底帆船顺风驶来，烟、床单和衬衫都往右扬，郁金香一齐弯腰，一个人的帽子被吹到河面上，小狗腾空扑过去；藤蔓边框和卷轴题字 DE WINDVLAAG；每块砖单独画、单独烧，线条在砖缝处错开；开片、铁斑、崩瓷，云上一块窗户倒影在砖缝处断开错位） | 约 6 秒 |
| 洞穴壁画（赭石颜料） | `lib/cave.py` · `CavePainting` | `examples/cave_hunt.py` 篝火旁的岩洞（只靠篝火和石油灯照亮的石灰岩洞壁讲一次狩猎：野牛画在岩壁天然的鼓包上，背插两支矛，转身对着两个红色猎人；马、雄鹿和母鹿往反方向跑，上方一匹只起了炭稿的马；火堆上方四只吹喷手印，墙脚一排掌印红点；地上放着三堆研磨赭石和炭条的石板、一根吹颜料的骨管；钟乳石帘、钙华薄膜、零星掉色、熊爪抓痕、熏黑的顶壁） | 约 7 秒 |
| 1-bit 早期画图软件 | `lib/macpaint.py` · `MacPaint` | `examples/macpaint_garden.py` 窗台花园 · Windowsill Garden（一台 1984 年式黑白画图软件的整屏：菜单栏、工具栏、图案板、条纹标题栏窗口；画布上一扇窗，格子布窗帘画好左边再翻转复制出右边，窗外是图案分带的天空和山坡小屋；窗台上种子袋和三盆向日葵讲 40 天：发芽、长叶、开花，喷壶还对着第 2 天那盆滴水；黑猫盯着一只被选框行军蚁框住的白蝴蝶；Shadow 样式标题 watch it grow!；全画只有黑白两值，色调全靠 8×8 图案） | 约 0.4 秒 |
| 古希腊黑绘陶瓶 | `lib/blackfigure.py` · `BlackFigure` | `examples/blackfigure_games.py` 赛跑与赛车 · Games on a Vase（博物馆展台上一只阿提卡黑绘颈柄双耳瓶，旁边展板把两圈饰带展开成平面：上圈四马战车赛，正面是领先的两辆，转到瓶背才看得见折返柱、落后的第三辆、奖品三足鼎和裁判；下圈短跑，背面是终点柱和摆着奖品的桌子；棕榈叶莲花链、舌纹、回纹、放射纹、古希腊字母题字；赤陶橙底、黑釉剪影、刻线、加红加白，黑釉上一条柔光箱反光；加白剥落、钙质结壳、缺口和修补） | 约 7 秒 |
| 铅笔素描 | `lib/graphite.py` · `Graphite` | `examples/graphite_bicycle.py` 老街角的自行车 · The Bread Run（素描纸上的石墨写生：女式城市自行车靠在老街转角的灰泥墙上，前筐里一根法棍和一束纸包的郁金香；阴影里的侧墙挂着只画了面包的铁艺招牌，左边一扇深门洞，麻雀在啄面包屑；起形辅助线、轮廓、侧锋铺调、分层排线、纸擦笔、橡皮提亮一步步做完；只有中间画完，越往纸边越只剩线稿；页边铅笔笔记、2H–8B 试笔色阶和一枚石墨指纹） | 约 11 秒 |
| X 光片 | `lib/xray.py` · `XRay` | `examples/xray_luggage.py` 行李安检 · Security Check（双能 X 光安检机俯视图：传送带上的硬壳拉杆箱，箱壳轮廓发亮、铝拉杆是两层套管；箱里一把折叠伞、一个旅行吹风机（电机、双重螺旋电热丝）、一台仰面躺着的相机、钥匙和硬币、叠好的衣服、一瓶水，还有一副脊柱里穿着钢销的石膏恐龙骨架玩具；侧栏是同一只包的材料伪彩视图和 1 号物体放大，操作员结论：1 是玩具放行，2 超过 100 ml 要取出；Zeff 和毫升数都是从画面上量出来的） | 约 2 秒 |
| 1930 年代黑白橡皮管动画 | `lib/rubberhose.py` · `RubberHose` | `examples/rubberhose_morning.py` 早晨的闹钟（7 点整的小卧室：双铃闹钟蹦上床头柜摇铃，一只鞋踮着脚，挥着白手套指着床，「RRRING!」在头顶蹦跳；戴条纹睡帽的枕头还在打呼，举起手套「再睡五分钟」；窗外的太阳在两座山之间打哈欠伸懒腰，阳光落在地毯上，一双拖鞋已经跳起舞；灰色水粉背景、描线上色的赛璐璐、饼切眼、橡皮管四肢，拍成老胶片：柔焦、颗粒、片门晃动、圆角片门、划痕、灰尘和片门里的一根头发） | 约 3 秒 |
| 黑白麻胶版画（linocut） | `lib/linocut.py` · `Linocut` | `examples/linocut_snowy_village.py` 雪夜归途 · Homeward, First Snow（两块版的麻胶版画：V 口刀刻出的风雪流线、刻出来的满月和断续光环、两缕炊烟；雪坡的黑色等高线、山脚积雪的云杉林、五座积雪木屋；一个人提着灯笼、拖着一雪橇劈柴走回家，脚印和雪橇辙从画外进来，那家的门敞着、暖光洒在雪上，小狗跑出来迎他；灯黄套色版只印亮窗、门前的光和灯笼，略微错版；实地发花、残刀印、压印，页边铅笔版次 7/30、题名、签名和一枚钢印） | 约 9 秒 |
| VHS 家庭录像 | `lib/vhs.py` · `VHSCamcorder` | `examples/vhs_birthday.py` 吹蜡烛 · Blow Out the Candles（一家人生日录像里的一帧：70 年代客厅的圆环墙纸、胡桃木护墙板、兔耳天线电视、牛油果绿丝绒沙发、长毛地毯；彩带、HAPPY BIRTHDAY 三角小旗、戴派对帽的泰迪熊；茶几上的蛋糕四根蜡烛刚吹灭冒着烟、两根还亮着，过生日的孩子戴着尖帽从背后凑近、离镜头太近而虚焦；白平衡停在「室外」拍钨丝灯、烛焰过曝和 CCD 竖向拖影、点阵 OSD；录像带的色度渗色、跟踪噪带、磁头切换噪声、掉磁白点） | 约 6 秒 |
| 扁平矢量 | `lib/flatvector.py` · `FlatVector` | `examples/flatvector_night_camp.py` 山间夜营（七色限定色板，无描边的大块几何形一层层叠起来，层与层之间一道柔和投影，加极细颗粒；夜蓝天空里一轮带橙色光芒的月亮，紫色雪山分出亮面和折线暗面，品红、橙色两种山丘带，黄沙地；下午插在山顶的小旗下，一条虚线小路走之字形下山、穿过山丘，尽头是戴头灯走最后一段路的小小背包客；营地已经亮了：橙色 A 字帐篷门口透出光，篝火的光在沙地上铺成一圈圈平涂光环；几何松树、圆冠树、两朵平底云、一颗流星） | 约 1 秒 |
| 绘本角色动画 | `lib/storybook.py` · `Storybook` | `examples/storybook_acorn.py` 小橡果的秋天（真动画 + 旅程总图：米色纸上，枝头打盹的小橡果被晃醒、拉长掉下、落地压扁再弹起，追着一片红橡叶滚下山坡，山坡、小花、远山随它经过一笔笔画出来；跳上漂在小河上的橡叶，撞岸后空翻上岸，钻进土里发芽长成一棵还戴着橡果帽的小橡树；最后「hello, little oak」按笔顺写出来，彩纸屑飞起。总图把六个关键姿态多次曝光在铅笔运动弧上；加 `--gif out.gif` 出 15 fps 的真动画） | 约 1 秒（总图）/ 约 3 秒（151 帧动图） |
| 圆珠笔涂鸦 | `lib/ballpoint.py` · `Ballpoint` | `examples/ballpoint_board_game.py` 蛇梯棋大冒险 · Snakes & Ladders, Round 7（午休时在复印纸上用蓝、红、黑三支圆珠笔画的 8×8 蛇梯棋，彩铅一行行涂成彩虹色格子；一局正在进行：骰子刚从页边弹过来、掷出 4，蜗牛从 10 跳四格到 14（红笔虚线弧标出 1-2-3-4），正顺着长梯子爬到 38（红圈、虚线箭头、+24!），小云从 47 被绿蛇滑下去，晕乎乎地喊 nooo~，骰子怪在 51 捂着脸；页边是彩旗、太阳、井字棋、纸飞机、星星串、山坡小房子、花盆，吐槽小纸条「who drew this snake so LONG?!」、记分卡、把 three 划掉改成 four、红笔结论 slow snail, fast ladder!；右下角还有上一页购物单压过来的无墨压痕） | 约 4 秒 |
| 描图纸叠层 | `lib/overlay.py` · `Overlay` | `examples/overlay_city_map.py` 海港步行图 · Larkhaven on Foot（暖白灯箱上，定位钉挂着一张黑线灰调的海边小城底图：递归切出的街区、沿街一圈房屋和分户墙、深色地标、海岸与防波堤、铁路、城堡山和岬角的等高线；三张单色叠片对着套准十字落下——蓝片（沿岸一圈圈水线、河、港湾、渡轮航线、2 路电车）、黄片（公园、集市广场、海滩）、品红片（六站步行路线，坐渡轮去灯塔）；不同叠片的油墨正片叠底：植物园的池塘叠成绿、路线压过公园成红、压过海面成紫；描图纸背光下的纤维云纹、卷角、打孔、绘图胶带，旁边一张透明胶片上的图例卡） | 约 7 秒 |

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
- 手作、DIY 教程、「从图纸到成品」的步骤图、把像素图案做成可爱实物（杯垫、挂件、冰箱贴）、讲解片里的「动手做」页 → 拼豆（要屏幕上的像素游戏感用像素风，要布上的针线用十字绣）；
- 远古、史前、起源、「人类最早的记录」、狩猎与迁徙、动物群、天文与历法、讲解片里的「历史开端 / 最早怎么记事」页 → 岩画（凿刻砂岩）；
- 古代文明、历史与考古、农业和劳动场面、「一步一步」的工序或流程讲成分栏连环画、讲解片里的「最早的记录 / 起源 / 古人怎么做」页 → 古埃及墓室壁画；
- 古典、地中海、古罗马 / 古希腊题材，海洋生物、港口与渔猎、动物图鉴，门槛或地面铭文，讲解片里的「历史 / 起源 / 古代」页 → 罗马马赛克（要屏幕上的像素格子感用像素风，要熔珠小管的手作感用拼豆）；
- 教堂、中世纪、哥特、庄严而温暖的透光，节日与季节，「一年四季 / 时间流转」的分格叙事，讲解片里的「历史 / 传统工艺」页 → 彩色玻璃花窗（要现代霓虹发光用赛博朋克）；
- 中世纪、古籍、典藏感、「古老的学问」（天文、历法、草药、炼金这类老知识）的图解、书名页和章节首页、讲解片里的「历史 / 起源」页 → 泥金手抄本（一页里要有字：正文、红字标题和首字母是它的主体）；
- 发明、机械原理、「这东西是怎么动的」、从自然到设计（仿生）、工程手稿感的讲解页、「草图 / 构思 / 研究笔记」页、复古科学插图 → 达·芬奇手稿（要现代实验记录用实验笔记本，要讲课推导用黑板板书）；
- 人物小传、宠物、家族与纪念、复古肖像、「这个人 / 这只猫 / 这条船是谁」的介绍页、怀旧礼物卡片，不能用真人照片时 → 剪影（要童趣的彩纸故事用剪纸拼贴；要老照片拼贴感用报刊拼贴）；
- 活动 / 演出 / 开业 / 讲座的复古海报、「XX 来了」式的宣告、节目单与价目、旧时代广告、19 世纪美式或民国风的印刷品、讲解片里的「历史 / 老派做法」页 → 凸版印刷海报（要几何构成的现代海报用包豪斯几何，要剪报拼贴用报刊拼贴）；
- 工业、技术、发明史，「从 A 传到 B」的原理图解（广播、电报、铁路、流水线），强对角线的海报和杂志封面，讲解片里的「年代 / 历史 / 先驱」页，需要老照片质感又不能用真人照片 → 苏联构成主义（不写政治口号；要三原色几何讲座海报用包豪斯几何，要剪报和勒索信字用报刊拼贴）；
- 旅行、交通、城市主题海报，复古而有高级感的主视觉（开业、晚会、发布会、酒店、邮轮、列车），「速度 / 现代 / 黄金年代」主题，讲解片里「历史上的未来 / 1930 年代」的封面 → 装饰艺术（要 80 年代霓虹复古用复古 Synthwave，要几何构成和三原色用包豪斯几何）；
- 复古漫画、冒险故事的「出发 / 登场 / 大事件」、怀旧玩具与少儿读物感、讲解片的「故事开场 / 角色介绍」封面、需要对白框和拟声字的画面 → 黄金时代漫画（要现代日漫用日本动漫，要拟人小物件的轻松图解用卡通手绘，要红黑两色木刻海报用凸版印刷海报）；
- 同一个东西的几种状态、情绪、版本或配色并排对比，系列头像（宠物、角色、吉祥物），「一图多版」的潮流海报，讲解片里的「同一个东西的几副面孔 / 变体对比」页，要有名人肖像的波普感又不能用真人 → 波普丝网（要单张几何海报的套色印刷用包豪斯几何；要剪报和网点老照片用报刊拼贴）；
- 计算机史、老机房、复古科技、数据和日志、「当年的电脑怎么画画」、程序员 / 极客向的配图、讲解片里的「输出结果 / 运行日志 / 打印报告」页 → ASCII 字符画（行式打印机）（要屏幕上的低分辨率游戏感用像素风，要手写板书用黑板板书）；
- 游戏感、复古 3D、「90 年代末 / 千禧年」怀旧、飞行 / 赛车 / 闯关、带 HUD 的「关卡 / 进度 / 任务」页、讲解片里的「早期 3D 图形是怎么画出来的」（线框 → 平面着色 → 贴图 → 雾）→ 低多边形（要 2D 小尺寸游戏感用像素风，要柔和现代的 3D 渲染用柔光 3D，要正交微缩模型用等轴 2.5D）；
- 街头、城市、态度与幽默、一句短口号配一个小人物的海报、公益与社区宣传、「一个人 + 一件小事」的极简故事、讲解片的「观点 / 金句」页 → 喷漆模板涂鸦（要霓虹夜景用赛博朋克；要设计感的丝网海报用包豪斯几何；要剪报拼贴用报刊拼贴）；
- 徽章、勋章、打卡 / 成就 / 里程碑、旅行与户外、社团与活动标志、讲解片里的「收集 / 解锁 / 第 N 关」页 → 刺绣徽章（要手作布艺的十字格子感用十字绣；要贴纸质感用贴纸拼贴）；
- 工程、建筑、机械和设备的结构与原理（剖面、零件、尺寸、「里面是怎么造的 / 怎么动起来的」），产品或建筑的技术说明页，讲解片里的「结构 / 设计图 / 原理图 / 施工图」页 → 蓝图工程图（要植物和自然物的蓝色剪影用蓝晒；要发明构思和手绘草图感用达·芬奇手稿；要讲课推导用黑板板书）；
- 童趣、家庭与亲子、「我的一天 / 我的家 / 我的周末 / 长大想当什么」这类孩子口吻的小故事、节日与生日贺卡、儿童教育和绘本感、讲解片里「用孩子的眼光看」的页 → 儿童蜡笔画（要精致柔和的成人手绘用韩国彩铅；要彩纸拼贴的童趣用剪纸拼贴；要成熟的卡通角色用卡通手绘）；
- 终端、命令行、黑客 / 程序员向、老电脑屏幕、「敲一条命令得到结果」、复古版的数据面板，讲解片里的「查询 / 运行结果 / 系统状态」页 → 绿屏终端 CRT（荧光字符画）（要打印在纸上的日志和报表用 ASCII 字符画（行式打印机）；要低分辨率的游戏画面用像素风；要 80 年代霓虹用复古 Synthwave）；
- 温度、冷热、保温与漏热、散热、能耗，「看不见的东西」的可视化（热量、气流、体温、余温留下的痕迹），夜视 / 侦测 / 检测报告感，讲解片里的「数据告诉你哪里热、哪里漏」页 → 热成像（要霓虹夜景氛围用赛博朋克；要手写的实验数据与图表用实验笔记本；要复古仪表盘用复古仪器面板）；
- 荷兰、运河、风车、郁金香、帆船与航海，老派欧洲家居（厨房、壁炉、瓷砖墙），蓝白两色的典雅装饰，一组图标式的小图（单块砖可以一砖一个主题），讲解片里的「传统工艺 / 历史 / 一组图标」页 → 代尔夫特蓝瓷砖（要石子和玻璃拼的古代地面画用罗马马赛克；要普鲁士蓝的日光晒图用蓝晒）；
- 史前、人类起源、「最早的艺术 / 人类最早怎么画画」、狩猎与动物群、火与夜晚、讲解片里的「艺术的起源 / 远古的一个夜晚」页 → 洞穴壁画（赭石颜料）（要在日晒岩面上凿出来的符号用岩画；要分栏叙事、有文字的古文明壁画用古埃及墓室壁画）；
- 复古电脑、「第一代图形界面 / 早期个人电脑」怀旧、黑白像素插画、软件和工具的「界面 / 操作步骤」图解、讲解片里的「当年的电脑怎么画画」页 → 1-bit 早期画图软件（要彩色的低分辨率游戏感用像素风；要打印纸上的字符画用 ASCII 字符画）；
- 古希腊、古代奥运与体育比赛、「古人怎么比赛 / 劳动 / 过日子」，绕一圈又回到起点的事（跑道、循环、四季、流程），博物馆展品感、「一件器物 + 它的展开图」式的图解，讲解片里的「历史 / 起源 / 古代」页 → 古希腊黑绘陶瓶（要分栏的多彩墙画用古埃及墓室壁画；要石子铺成的地面画用罗马马赛克；要红黑两色的印刷海报用凸版印刷海报）；
- 写实而安静的日常一角（街角、老物件、静物、交通工具）、旅行写生、怀旧、「先画个草图 / 观察细节」的构思页、讲解片里的「观察 / 写生 / 手稿」页、要黑白高级感又不要漫画感 → 铅笔素描（要彩色可爱的小物用韩国彩铅；要发明与机械原理的手稿用达·芬奇手稿；要讲课推导用黑板板书）；
- 「里面有什么」「看穿」「拆开看结构」、透视 / 内部构造 / 原理图解（电器、工具、机械里面长什么样），安检、体检、检测、质检、排查问题，讲解片里的「真相 / 揭秘 / 一眼看穿」页 → X 光片（要手绘的机械分解图用达·芬奇手稿；要「拆开看看」的剪报拼贴用报刊拼贴；要冷热分布用热成像）；
- 复古动画、老电影 / 默片 / 黑白卡通的感觉、拟人的日常物件又唱又跳、起床 / 闹钟 / 上班这类节奏感强的小场面、讲解片里的「很久以前 / 第一代动画 / 老片头」页 → 1930 年代黑白橡皮管动画（要彩色、蓝铅笔稿的现代手绘卡通用卡通手绘；要网点和对白框的漫画书用黄金时代漫画）；
- 冬天、夜晚、乡村与小镇、民间故事和童话、节日贺卡和藏书票、「回家 / 守夜 / 一盏灯」这类温暖的小故事、要手作感又要强烈黑白对比的封面、讲解片里的「过去的冬夜 / 手工年代」页 → 黑白麻胶版画（要红黑两色的木活字海报用凸版印刷海报；要日式多色套印和晕色用浮世绘；要喷漆模板的街头感用喷漆模板涂鸦）；
- 家庭回忆、怀旧、「当年的那一天」（生日、过年、毕业、第一次……）、童年和老房子、found footage 式的悬念开场、讲解片里的「回到 80 年代 / 那时候的家 / 老录像里的证据」页 → VHS 家庭录像（要霓虹落日的 80 年代复古未来用复古 Synthwave；要老照片和剪报用报刊拼贴；要屏幕上的字符用 ASCII 字符画）；
- 风景、户外、旅行与露营、MG 动画式的场景背景和转场、讲解片的「场景 / 旅程 / 夜晚」页、要干净现代又有层次的插画 → 扁平矢量（要撕纸边和蜡笔的手作感用剪纸拼贴；要正等轴的微缩模型用等轴 2.5D；要 80 年代霓虹用复古 Synthwave）；
- 要「真的动起来」的小故事、一个可爱小角色的旅程或成长（从 A 到 B、出发—遇到—到达）、讲解片的片头片尾和转场、品牌吉祥物小动画、「一路走一路画出来」的过程感 → 绘本角色动画（`Storybook.gif()` 出真动画，`journey()` 出一张旅程总图；只要一条轮廓的变形用形变动画；要逐帧抖线的静态卡通插画用卡通手绘）；
- 上课 / 午休走神的随手涂鸦、纸上正在进行的游戏或计划（手画棋盘、寻宝图、清单、路线、比分）、学生和办公室日常的轻松小故事、讲解片里「在草稿纸上推演一步」的页 → 圆珠笔涂鸦（要铅笔图表、荧光笔和贴纸的实验记录用实验笔记本；要没有线稿、柔和的彩铅小物用韩国彩铅；要小孩的蜡笔画用儿童蜡笔画；要黑白石墨写生用铅笔素描）；
- 地图、路线与导览、城市 / 园区 / 校园平面图，「一层一层把信息加上去」的图解（底图 → 水系 → 绿地 → 路线），设计稿或方案的分层、叠加与对照，讲解片里「把几层信息叠起来看」的页 → 描图纸叠层（要正等轴的微缩模型用等轴 2.5D；要剖面、尺寸和施工说明用蓝图工程图；要三原色丝网海报用包豪斯几何）。

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

**岩画 `Petroglyph`**：
- 思路：岩画不是画上去的，是把岩面的深色皮（沙漠漆）敲掉。一切都是高度（px）和颜色场，最后用左上一盏低角度侧光照亮：法线明暗、沿光线步进的投影（每个凹坑左上壁暗、右下壁亮）、凹处的 AO
- 构造：`Petroglyph(W, H, seed, light=(-0.62, -0.5, 0.6))`
- 岩石：
  - `rock(colour, relief, bedding, grain)`：砂岩高度图（大起伏、时有时无的层理、砂粒、浅凹坑）和漆下的石色；
  - `ledge(y, drop=34)`：一道折线岩檐，下面的岩面退后一个台阶、漆更薄；
  - `varnish(strength, streaks, top, scour, patches)`：沙漠漆，近乎均匀的深色漆膜 + 清晰的蓝黑流痕 + 浅色流痕，顶部更厚、近地面被风沙磨薄；
  - `fracture(pts, width, depth, seep, branches)`：裂缝，锯齿窄槽、圆肩、分叉，往下渗出深色漆痕
- 起稿：`draft()` 返回 `Draft`（`stroke(pts, w, end_w)`、`fill(pts)`、`dot`、`ring`、`add(mask)`）；现成图形都返回 Draft，可用 `into=` 合成一个：
  - `bighorn(x, y, size, facing, kind='ram'|'ewe'|'lamb', gait, rot)` 大角羊（扭转透视的角）；
  - `hunter(x, y, size, facing, weapon='bow'|'atlatl')` 拉弓 / 举投矛器的猎人；
  - `sun_spiral(x, y, r, turns, rays)`、`crescent(x, y, r, thick, rot)`、`concentric(x, y, r, rings)` 水源；
  - `hand(x, y, size, rot, outline, spread)`、`hoofprints(pts, size, every)` 偶蹄印、`meander(pts, width, smooth)` 任意线
- 凿与磨：
  - `peck(glyph, density, size, depth, age, scatter)`：用成百上千个不规则凹坑把图形敲出来，打穿漆层、碾白砂粒；
  - `abrade(pts, width, depth, age)`：磨出 V 形槽（比凿点光滑、发亮，带顺向擦痕）；
  - `abrade_tally(x, y, counts, gap, length, width, row_gap, slant, age, strike_every)`：成排计日刻痕
- 年代：`age` 0 新凿（亮、锐），0.3 几百年，0.6–0.8 几乎被漆重新盖住；新图凿在旧图上自然更亮、更深
- 风化：`spall(pts, depth, impact, age)` 剥落（小贝壳弧唇口、台阶投影、贝壳状波纹、鲜橙石面，带走上面的图）；`lichen(x, y, r, kind='green'|'orange'|'grey', n)` 壳状地衣
- 顺序：rock → ledge → varnish → fracture → 旧图（age 大）→ 新图 → spall → lichen
- 颜色常量 `STONE SCAR CRUSH VARNISH_FE VARNISH_MN LICHEN`；`stage(name)` 立即合成快照；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**古埃及墓室壁画 `TombPainting`**：
- 思路：先「声明」整面墙上的东西，再按古代画工的工序一遍遍画：`wall()` 草筋泥上抹一层石膏灰泥 → `grid(box, cell, base)` 红赭石弹线的比例格（一格是人物的一个比例单位，脚底到发际 18 格）、`guide(p0, p1)` 分栏线 → `sketch()` 红稿 → `ground(颜色)` 绕开人物刷底色 → `colour([颜料…])` 一罐颜料画一遍、`ink()` 最后勾线 → `colour(layer='text')`、`ink(layer='text')` 写字 → `age()`。每一层都留在内存里，剥落时按层露出来
- 部件：`part(pts 或 [多边形…], 颜料, paths=, ink=, width=, z=, alpha=, clip=, layer=)`；颜料名见 `PIGMENTS`（skin 男子红赭、skin_f 女子黄赭、linen、white、yellow 雌黄、blue 埃及蓝、lblue、green、dkgreen、lgreen、red、brown、ochre、black）；按逐像素 z 图叠放，所以按颜料分批画也不会叠错；勾线被上层遮住的部分自动不画
- 人物：`figure(x, 地线y, 身高, pose, facing, sex='m'|'f', wig='short'|'long'|'woman'|'cap', dress='kilt'|'long'|'loin'|'dress', collar)`；`POSES` 有 stand / walk / staff / plough / reap / sow / hoe / glean / carry / hold / scoop / squat，任一关键字都可覆盖（髋 hip、前倾 lean、膝 kf/kb、踝 af/ab、腕 wf/wb、肘弯向 bf/bb、手型 hf/hb、`turn`、脚镜像 `mb`）；返回手、腕、肩、耳的画面坐标和 z（`hand_f`、`z_hand_b`…），`S((x, y))` 把比例单位换成画面坐标，用来挂道具
- 道具：`staff()`、`sickle()`、`hoe(fig)`、`rod()`、`basket(full=)`、`sack(lean=)`、`heap()`、`measure(tilt=)`、`grain_stream()`、`scoop()`、`papyrus()`、`palette()`；拿在手里的东西 z 给 `fig['z_hand_x'] - 0.01`（从拳头后面穿过）
- 动植物：`ox(x, 地线, 长度, facing, colour, patches)` 长角牛（远侧两条腿错开一步，四条腿都看得见），返回 `poll`（架轭处）；`wheat(x0, x1, 地线, 顶, stubble=[(xa, xb)], grab=[(拳x, 拳y, (xa, xb))])` 麦田、留茬和被攥住的麦秆；`sheaf()`、`tree(waterskin=(dx, 长))`、`papyrus_clump()`
- 边饰：`block_border()` 色块边框、`kheker()` 凯凯尔饰带、`band(x0, x1, y, [(颜料, 高), ('rule', 2), …])` 分栏底带、`river()` 尼罗河
- 文字：`column(x0, y0, x1, y1, facing, n, seed)` 按方块（quadrat）排一栏伪象形文字（高窄的并排、扁的上下叠）；`glyph(名字, x, y, 字号, facing)` 单个符号（`SIGNS` 里 23 个，另有 hoe、stroke、heel、coil）；`numerals(12, x, y, 字号)` 象形数字
- 岁月：`age(losses=[(x, y, rx, ry)], zones=[(x, y, r)], cracks, flake, soot, fade, salt, tide, wear_amt)`：成簇剥落（蓝色和裂缝边先掉）、剥到灰泥露出红格红稿、颜料磨薄、灰泥脱落到草筋泥（断续白边、台阶、投影）、裂缝、埃及蓝发灰绿、顶部烟熏、墙脚潮痕和盐霜、蝇斑、灯光暗角
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**罗马马赛克 `Mosaic`**：
- 思路：工匠先画一张谁也看不见的「底稿」（cartoon，平涂和渐变的颜色图），再一块块铺石子：每块石子取自己脚下底稿的平均色，从石料盒 `STONES` 里挑最接近的一种（先比色相再比亮度，带一点抖动，色阶交界像工匠混用两种石子）。石子的排向（andamento）就是画法：每种铺法都沿某个标量场（距离场或坐标）的等值线走一排（marching squares），把一排切成整数块，所以每块略长略短；弯处每块自动成小楔形，急转角处断开换一块；靠近图形脊线的石子停在距离场的脊上，两侧在中线会合。后铺的石子大半压在已铺的上面就不要，压一点就「切掉」并留灰缝（先铺的优先）。渲染是 `ss` 倍超采样的高度场：石面微拱、边缘磨圆（每块石子自己的有符号距离做倒角），灰缝更低、带砂，灰浆床再低；左上方一盏斜光，按材质的漫反射 + 高光，每块石子略有倾斜，所以同色石子明暗不一；石子在灰缝里投影、灰缝有 AO
- 构造：`Mosaic(W, H, seed, tile=13, gap=1.8, ss=2, light, bed, grout, stones=None)`；tile 是背景石子边长，gap 是灰缝宽（px）；图形里用更小的石子（size 约 6–8）
- 底稿与起稿：`paint(mask, 颜色)`；`shade(mask, c0, c1, p0, p1, gamma)` 线性渐变（鱼背深、肚白）；`sinopia(mask=… 或 pts=…)` 在湿灰浆上用赭红起稿，没铺到的地方一直看得见（动画第一帧）
- 遮罩：`poly_mask(pts)`、`ellipse(cx, cy, rx, ry, rot)`、`rect()`、`band(pts, w0, w1)` 渐细粗线（触手、船尾柱、浪尖）；`everything()` 已铺的，`free(region)` 还空着的
- 铺石子（按调用顺序，先铺的优先，要保持完整的先铺）：
  - `point(x, y, 颜色, size, 'round'|'square'|'tri', angle)`：单块（眼珠、隔字点）；
  - `line(pts, 颜色=None, size, across)`：沿路径一排（字的笔画、鳍线、桅杆、索具、网线）；颜色 None 时从底稿取色，做触手的中脊；
  - `outline(mask, 'black', rows, size)`：图形内侧的第一排深色轮廓；
  - `fill(mask, size, stones, wrap=True)`：沿轮廓往里一排排铺（opus vermiculatum）；wrap 让石子也绕着已铺的眼睛、鳃线一圈圈排；`figure()` = outline + fill；
  - `halo(region, rows, size, stones, around)`：背景里贴着图形外轮廓的一两圈「光环」；
  - `rows(region, size, angle, wobble, field, stones)`：背景平铺（opus tessellatum）；给 `field`（H×W）就沿它的等值线排，海水用波浪场；
  - `frame(x0, y0, x1, y1, width, size, stones)`：平行于矩形四边的边框排，转角斜接；带宽取排距的整数倍，黑白镶边就和排对齐；
  - `tuck(region, size, small)`：剩下的洞用切小的碎石补上，大洞先补
- 铭文：`letters(文字, x, y, 字高, 颜色)` 罗马大写（A–Y 常用字母，U 写作 V，无 J K W Z），每一笔一排石子，`·` 是三角隔字点；`tabula(x0, y0, x1, y1, [(文字, 字高, 颜色)], ear, frame=('black', 'red'))` 带燕尾耳的铭牌（tabula ansata）：字、黑框、红框、白底横排、红耳
- 岁月（最后做）：`lacuna(mask)` 一片石子脱落，露出旧灰浆床和石子留下的方坑；`crack(pts)` 沉降裂缝（穿过石子和灰缝的黑细线，带凹陷）；`patina()` 灰缝成片积灰、局部失光
- 石料：`STONES` 名字 → (颜色, 材质)，材质 stone（石灰石，哑光、斑驳、麻点）/ marble（纹理、微光）/ glass（smalti 玻璃，饱和、亮、带气泡）/ terracotta；`stones=[…]` 限定这一步能用的石料（天空只用 white / bone / cream，海只用蓝色玻璃）
- 工具函数：`edt(mask)` 跳步泛洪欧氏距离场、`iso_lines(f, step)` 一次求出所有等值线、`maxfilt()`；`STONES MATERIALS LETTERS SINOPIA`
- 动画：`stage(name)` 只记进度，`save(path, stages_dir)` 时按 `stage_ss`（默认 1×）渲染各阶段和收尾帧；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**彩色玻璃花窗 `StainedGlass`**：
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

**泥金手抄本 `Illuminated`**：
- 思路：
  - 按作坊顺序作画：打格 → 抄写（红字和首字母留空）→ 朱笔 → 画图 → 贴金 → 上色 → 勾线；
  - 字是一支模拟的宽头鹅毛笔写的：笔尖是一段约 40° 斜握的短线段，笔画就是它扫过的面积，所以粗细随行笔方向变；菱形的头脚和发丝般的连笔都来自笔，不来自字体；
  - 打磨金箔是凸起石膏底上的一面镜子：每个像素按自己的法线（石膏底的鼓面、打孔、金箔接缝、打磨纹）反射相机光线，去查一间左上方有大窗的房间；
  - 壳金是哑光的颗粒；
  - 先贴金后上色，后画的颜料和墨会盖住金。
- 书和皮：
  - `desk()` 胡桃木书桌；
  - `codex(x0, y0, x1, y1, cover, squares, stack, dip)` 摊开的书（皮面封板、书口纸叠、页面在书脊处下陷变暗），返回左右两页的矩形；
  - `flaw(cx, cy, rx, ry, rot)` 羊皮上的天然破洞；
  - `rule(x0, x1, ys, prick_x)` 针孔、每行 x 高处的打格线、上下贯通的边框竖线；
  - `show_through(x0, x1, ys, xh, opacity)` 背面的字透过来。
- 文字：
  - `column(text, x0, x1, y, xh, leading, indent=[(行数, 左边 x)], align, filler)` 排一栏，返回 Block：
    - 标记 `*红字*`（留给朱笔）、`^词`（首字母点红）、`¶` 段落符、`|` 段落结束；
    - 自动长 s / 圆 s、断词加连字号、行尾填充；
    - `7` 写成提罗速记的 et（⁊），`ꝑ` 是 per。
  - `scribe(blk, dip)` 抄写黑字：每隔若干字重新蘸墨，铁胆墨由黑变褐，笔画边缘积墨；
  - `rubricate(blk, blue_first)` 朱红字、首字母点红、红蓝交替的段落符、行尾红锯齿加蓝点；
  - `write(s, x, y, xh, kind, rot, load)` 写一行，返回行尾 x；
  - `arc_text(s, cx, cy, r, at, xh, kind)` 沿圆弧书写；
  - `text_width()` 量宽度；
  - kind 可选 'iron' / 'red' / 'blue' / 'white' / 'diagram'。
- 金和颜料：
  - `gild(mask, cushion)` 红色底料上的凸起打磨金；
  - `punch(pts, r, depth)` 打孔装饰；
  - `shell_gold(mask)` 壳金；
  - `paint(mask, 颜色, mix=(颜色2, 0..1 场), granular)` 蛋彩，边缘积色，石青有颗粒；
  - `wash(mask, 颜色, opacity)` 透明淡彩；
  - `pen(paths, width, kind, dash)` 圆头笔线；
  - `outline(mask, width)` 沿形状描墨边。
- 遮罩：`mask(polys, lines, dots, holes)`、`circle()`、`ring()`、`ellipse()`、`star()`。
- 装饰物件（按作坊顺序调用各自的 `.draw()`、`.gild()`、`.paint()`、`.pen()`）：
  - `initial('Q'|'O', x0, y0, size, body)` 历史化首字母：伦巴第体字身配白线描、打孔金底、字腔里的夜景；
  - `border(path, width, avoid, bounds, seed, every, reach)` 金 / 群青 / 玫瑰色条形边框，递归长出常春藤花枝（金叶、花、金珠、卷须），避开 avoid 矩形；
  - `versal('O', x, y, size, colour, flourish, reach)` 两行高的分裂伦巴第字配红色花笔；
  - `astrolabe(cx, cy, R, lat, rete, rule, star)` 星盘；`.pen(labels=[(字, (x, y), (指向的 x, y))])` 加红色标注；
  - `spheres(cx, cy, R, angles, label_at)` 诸天圆图。
- 收尾和输出：
  - `age(foxing, soil, flakes, halo)` 六百年：铁胆墨晕、狐斑、翻页手印、金箔剥落露出红色底料、石青崩口；
  - `stage(name)`、`save(path, stages_dir)`。
- 颜色常量 `VELLUM INK RED AZURE ROSE GREEN WHITE SILVER LEAD OCHRE BOLE`；角度逆时针为正；`save('x.jpg')` 默认 quality 88、4:4:4 色度。

**达·芬奇手稿 `Codex`**：
- 纸：`sheet(tone, mount, margin, laid, chain, lost_corner='br', fold=x, stains=[(x, y, r)], foxing, edges, age)`：裱在卡纸上的帘纹碎布纸（帘纹、链线、纤维、纸齿），自带边缘氧化、缺角、泛黄云斑、霉斑、水渍潮线、可选旧折痕、手翻处的污渍；`show_through(x, y, width, lines)` 背面的字透过纸，左右反过来（所以是正着读的）
- 铁胆墨水和鹅毛笔：`quill(pts, width, ink)` / `quills([...])`，笔宽随宽笔尖方向变、落笔重收笔尖；笔里的墨会用完：越画越淡，再蘸一次又变浓，偶尔在落笔处积一个小墨珠；`contour(pts, searching=2)` 先轻轻找两三遍再定线（修改痕）；`ruled(p0, p1)` 靠尺直线；`dotted(pts, dot_dash=True)` 虚线 / 点划线（轴线）；`arrow(pts)`
- 排线：`hatch(mask, shade, angle=55, spacing, levels=(…), cross=0.76, cross_angle=-38, length, origin, medium='ink'|'chalk')`。55° 是左撇子的「\」；shade 0 亮 1 暗，每多一级 level 就在两线之间再插一层，超过 cross 加一层「/」交叉；按「排」下笔。明暗场：`between(a0, a1, b0, b1)`（从一条线到另一条线 0→1，蒙皮、圆杆）、`radial_shade(cx, cy, r)`；遮罩：`poly_mask(pts)`、`disc_mask(cx, cy, r)`、`Codex.arc(cx, cy, r, a0, a1)` 取弧上的点
- 红粉笔和铅笔：`sanguine(pts, width, pressure)` / `sanguines([...])` 只挂在纸齿上，`rub(mask, amount)` 用手指揉开；`leadpoint(pts)` 淡灰的铅笔起稿
- 尖笔和圆规：`incise(pts)` 无色的刻痕（侧光下一边亮一边暗），`compass(cx, cy, r, a0, a1)` 刻圆弧并在圆心留针孔，`prick(x, y)`
- 常画的东西：`cane(p0, p1, w0, w1, bend, lashings)` 两条线画的藤杆 / 木杆加绑绳，返回轮廓用来挖掉排线；`feather(base, angle, length, width, medium, side, overlapped)` 羽毛（返回轮廓、羽轴、宽羽片外缘）；`bird(x, y, size, phase)` 背视的小飞鸟，phase 从 π/2（翅膀最高）到 −π/2（最低）
- 镜像手写：`write(文本或行列表, x, y, width, size, mirror=True, max_lines)`，mirror 时 x 是右边距、每行从右往左写、左边参差；`prose(n)` 生成意大利语伪文；`label('a', x, y)` 字母标注（`mirror=False` 写正字，如收藏者的页码）
- 意外：`blot(x, y, r)` 带深色潮线和小溅点的墨点、`spatter(x, y, n)`、`strike(x0, y0, x1, y1)` 划掉废稿
- 机械零件（笔绘渲染）：`Camera(cx, cy, scale, azim, elev)` 正交相机；零件 `gear(r, teeth, depth, h, hub)`、`lantern(r, h, staves)` 灯笼齿轮、`crown(r, h, teeth)` 冠齿轮、`crank(arm, r_axle, handle_len, handle_r)`、`pulley(r, h)`、`cylinder()`、`box()`、`extrude()`；`.place(origin, axis, spin)` 摆放、`.named('wheel')` 命名表面组、`merge(...)` 合成一个网格；`solid(mesh, cam, hatch=dict(...), hatch_groups={'wheel.face': dict(...) 或 None})`：z-buffer 去掉被挡住的线、先擦掉身后的墨、按每个面背光的程度排线、只描轮廓 / 折边 / 开口边并连成长笔画；分解图就是把零件沿轴拉开再画点划线
- 颜色常量 `INK_DARK INK_LIGHT SANGUINE LEADPOINT PAPER MOUNT`；字体自动找 Apple Chancery / URW Chancery（Linux）/ Segoe Script（Windows），可用 `INKPAINT_FONT_CHANCERY` 指定；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**剪影 `Silhouette`**：
- 思路：剪影是黑纸用小剪刀剪出来的，贴在象牙白卡纸上，用薄金粉描几笔，装进玻璃椭圆金框挂到墙上。墙纸、金框、玻璃都按真实材料做，左上方一扇窗照亮整面墙
- 墙：`wallpaper(ground, ink, tint, period, repeat, length)` 木版印花条纹墙纸（刷涂的胶彩底、两块印版、错版、干斑、定位针点、每幅纸对花略错、拼纸接缝）；`picture_rail(y, h)` 挂镜线；`chair_rail(y, h, dado)` 护墙线和下面的墙裙
- 框：`frame(cx, cy, rx, ry, width, pearls, twist, eglomise, card, hook, cord, spread)` 返回 `Frame`。按线脚剖面建高度图（内口圆珠、凹槽、一圈珠饰、大圆脚、平条、外圆边；`twist` 把大圆脚做成绳纹），金面反射房间环境（窗亮、屋暗、地黑），所以出现一圈圈明暗环；有金箔方块接缝，棱顶磨出红色底漆，凹处积灰；墙上有接触阴影和柔影。`hook=True` 从挂镜线铜钩垂下两股丝绳（V 形，伸进框后面）；卡纸边缘泛黄、带霉斑；`eglomise` 是玻璃背面的黑底金线圈
- 剪纸：`sheet(f, at, scale, flip, warp)` 返回 `Sheet`，坐标用设计单位（px = at + scale × 点）；`warp` 是一个函数，可以整体改比例（头大一点、身子短一点）：
  - 贴平的主体：`shape(pts)` 主轮廓（只有一丝影子，边缘重采样成一小段一小段剪口）、`disc(x, y, r)`；`hole(pts)` 剪空，露出卡纸（眼睛、腿间、蝴蝶结的缝）
  - 单独剪下、微微翘起、影子更长的细条：`snip(pts, w0, w1)` 渐细的条（睫毛、胡须、发丝、飘带，宽度可传数组）；`line(pts, w)` 等粗的条（缆绳、桅杆）；`fringe(pts, n, length, angle, width, side, bend)` 沿曲线一排细丝（鸵鸟羽毛的羽枝、胸前的毛）；`scallop(pts, r, outset)` 一排鼓出的小圆（卷发团、帽冠抽褶、收起的帆）；`ringlet(x, y, length, width, turns, sway)` 螺旋垂卷，返回中线给金粉用；`lace(pts, depth, step)` 带一排穿孔的蕾丝花边
- `paste(sheet)` 把剪好的纸贴到卡纸上：4× 超采样再缩小，1 px 的细丝也留得住；黑纸带纤维和光泽，朝光的剪边有一道细亮线
- `bronze(sheet, strokes, width, tip, bright)` 薄金粉：每笔渐细、亮度各不相同、带颗粒，只留在黑纸上
- 字：`caption(f, 文字, x, y, size, style='roundhand'|'italic')` 铁胆墨手写题签（`sil_font` 找 Snell Roundhand / Baskerville Italic，可用 `INKPAINT_FONT_ROUNDHAND`、`INKPAINT_FONT_ITALIC` 指定）；`pen(f, pts)` 墨线
- `glaze()` 装上玻璃：凸面玻璃的柔光和窗户倒影；`smooth(pts, per, closed)` 闭合或开放的 Catmull-Rom 曲线
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**凸版印刷海报 `Letterpress`**：
- 思路：每种油墨一块版（forme），先把要印这个颜色的东西都「锁」进版里，`press(ink)` 一次压印。每过一次机器纸张落得不一样：每块版有自己的平移和极小旋转（`register(ink, dx, dy, rot)`），红版和黑版永远对不齐。先红后黑
- 纸：`paper(colour, warm, tone)`：已经泛黄的廉价海报纸（云状纸浆、短纤维、杂点、纸齿、微微不平）
- 版：`lock(mask, ink, film)` 锁进任意遮罩；`clear(mask, ink, keep)` 刻掉（木刻高光、前后遮挡）；`with lp.layer('key'):` 把东西锁进版的某一部分，`press(ink, only=['key'])` 只压这一部分（阶段动图先出轮廓线、再出排线）；`press(ink, density)`：边缘随纸齿参差、边上积一圈深墨、大实地缺墨发花并露出纸齿白点、灰尘留下圆形漏印；黑压红更深
- 木活字：`type_line(s, x0, x1, base, cap, face, ink, align='justify', stretch, track, shade=(dx, dy, 另一版颜色, gap), inline=(inset, width), wear, grain, limits)`：默认把一行排满版心（字面横向压扁或拉宽、再加字距），每个字是一块木头：木纹条痕、一端偏浅、凹坑软斑、边角缺口、偶尔一道顺纹裂缝；shade 是印在另一块版上的投影，inline 是笔画中间刻一道白线。face 用 clarendon / antique / gothic / fatface / cjk（宋体黑）；`type_width()` 量宽度
- 铅字与花饰：`text(s, x, y, size, face='roman'|'roman_bold'|'italic'|…, ink, anchor, spacing, rot, stretch)`、`text_mask()`、`text_width()`；`rule(x0, x1, y, kind='single'|'double'|'thick_thin'|'thin_thick'|'dotted', ink, weight, joints)` 铜线（长线由几段拼成，接头有细缝和 1 像素错位）；`leaders()` 引线点；`star()`；`ornament(字符, ...)` 花饰字体（缺字体时画星）；`border()` 粗细双线框加方角
- 形状（整页浮点遮罩，可加减乘）：`shape(控制点)` 平滑闭合曲线、`poly()` 直边多边形、`tube(点列, widths=[...])` 变粗细的管子（腿、鼻、尾、绳）、`ellipse(cx, cy, rx, ry, rot, a0, a1)`、`rect()`、`outline_pts()`
- 木刻：`key(mask, width, heavy)` 轮廓线刻在形状内侧、背光一侧加粗；`hatch(mask, angle 或 centre+aspect, spacing, tone, lo, gain, wobble)` 线宽随明暗变化的排线，tone 低于 lo 处收尖消失、高处并成实地；`form_tone(mask, soft)` 把遮罩当成鼓起的体积打光得到 tone；`ramp(p0, p1)` 线性渐变 tone；`cast(mask, dx, dy, onto)` 投影；`line(pts, width, taper)` 两头收尖的刻线（皱纹、绳子）；`solid()`；`stipple(mask, density, size, tone)` 点刻；`tint(mask, ink=RED, loose, grow)` 另刻的套色块，边缘游走、比轮廓略胖
- 印后：`fold('v'|'h', pos, depth, crack)` 折痕（油墨裂开、积灰、两侧受光不同）；`tone_edges()` 边缘泛黄；`foxing(n)` 霉斑；`stain()` 水渍；`tack(x, y, r)` 钉孔和锈斑；`nicks(n, size)` 纸边缺口；`strip(x0, y0, x1, y1, rot, colour, draw=fn)` 另印一条日期条贴上去（fn 拿到一个小 Letterpress 往上排字，周围有浆糊印）
- 颜色常量 `RED BLACK PAPER`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**苏联构成主义 `Constructivism`**：
- 思路：一张纸、两块版。红的都在红版上，黑的（色块、字、每张照片的每个网点）都在黑版上。画东西就是「把遮罩印到某块版上」或「从某几块版上挖掉、露出纸」。合成时每块版整体带一个套准误差（平移加极小旋转），所以红黑相接处一边露纸、一边叠出深色。墨是透明滤色，相乘叠印，黑压红是暖黑
- 构造：`Constructivism(W, H, seed, misreg=2.4, red=RED, black=BLACK)`
- 纸：`paper(colour, aged, yellow)`：便宜的奶油色海报纸（云状纸浆、纤维、纸屑、微微不平、边缘发黄）
- 遮罩（全画布、抗锯齿，可加减）：`circle()`、`ring()`、`arc(cx, cy, r, a0, a1, width)`、`sector()`、`rect(x0, y0, x1, y1, rot)`、`bar(x0, y0, x1, y1, width)` 斜条或细线、`wedge(apex, angle, half, length)` 楔形、`poly()`；`along(p, angle, d, side)`：从 p 沿某个角度走 d、再往左偏 side，用来摆斜排的字和标注
- 印：
  - `ink(mask, 'red'|'black', knock=, density)`：印一版，knock 是从这块色里挖掉的字；
  - `knock(mask, plates)`：从这几块版上挖空；
  - `tint(mask, plate, level, cell, angle)`：平网；
  - `waves(cx, cy, r0, r1, step, width, a0, a1, plates, grow)`：限定角度内的同心波前，grow 为负时越传越细
- 字：`text(s, x, y, size, plate, font_style='grotesk'|'din'|'narrow'|'futura', anchor, spacing, rot, wobble, scale_x, knock)`；`text_mask()` 用来反白；`text_width()` 量宽度。grotesk 是 Helvetica Neue Condensed Black（退回 Impact / DejaVu Sans Condensed Bold），din 是 DIN Condensed（退回 Arial Narrow / PT Sans Narrow）；缺西里尔字形的字体自动跳过；`wobble` 给大字一点手绘的抖动
- 照片 `Photo(w, h, eye, target, fov, ss, key, fill, haze, shift, ...)`：小型透视 z-buffer 光栅器，单位米，Z 朝上：
  - `material(albedo, gloss, shine, metal, tex, interior)` 返回材质号，tex 是按世界坐标算的程序纹理（木纹、刻度、线圈绕线）；
  - `cylinder()`、`lathe(base, axis, [(t, r), ...])` 旋转体、`sweep(path, radii)` 变径管（鹅颈、喇叭、软线）、`box()`、`hyperboloid(z0, z1, r0, r1, n, twist, mid)` 双曲面网格塔的一节；
  - `project()` 把世界坐标点换成照片像素，用来让海报上的其他元素对准照片里的东西（如楔形对准喇叭口）；
  - `render()` 只调一次：只给有物体的像素着色，渲染后释放缓冲
- 拼贴：`montage(photo, cx, cy, rot, scale, plate, cut, close, backdrop, cell, angle, contrast, soften)`：缩放、旋转、放上去，再在海报坐标里统一加 45° 网点（所有照片共用一张网）。
  - `cut=` 沿轮廓留边剪下：盖住下面已印的东西，露出纸色白边和背景的高光小点；
  - `close=` 桥接剪刀剪不进的窄缝；
  - 不给 cut 就是去了底的照片，网点直接叠印在红色上；
  - `soften` 是加网前的模糊（单位：网格），网格塔这类细杆用 0.12
- 做旧：`age(folds=(竖, 横), foxing, stain, pins, crack, grime)`：折痕裂墨与磨损、霉斑、水渍潮线、磨旧的角、图钉锈孔
- 顺序：paper → 红版色块（圆、楔形、色块）→ 黑色波线、斜条（`knock` 掉下面的红）→ 照片 → 字和标注 → age
- 颜色常量 `RED BLACK PAPER AGED`；角度逆时针为正，0° 指 3 点钟；`stage(name)` 立即合成快照；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**装饰艺术 `ArtDeco`**：
- 思路：画家不画线。每个形状都是一张用刀刻出来的遮片（frisket），盖在板上用喷枪喷色，所以边缘锐利、里面是一段平滑渐变；形体只靠明暗：楼是一张平剪影、一侧喷暗一侧喷亮，圆柱体上肩一道高光、下腹一条反光
- 喷枪：`spray(mask, 颜色或整幅颜色场, density, grain, blend='paint'|'screen'|'add')` 一次喷涂；薄涂处有雾滴颗粒（固定噪声 × d(1−d)），实涂处没有；`fade(mask, stops, p0, p1)` 线性渐变，`glow(cx, cy, r, 颜色)` 径向光晕；遮片 `rect()`、`poly()`、`disc()`（都抗锯齿）；`ramp(t, stops)` 色阶
- 天空：`sky(stops, top, bottom)` 长渐变；`burst(cx, cy, rays, contrast, reach, colour, dark, glow, phase, taper, bottom)` 明暗交替射线（亮楔靠近中心略宽，对比随距离衰减，bottom 处截止）；`moon(cx, cy, r)` 偏心径向渐变的球形月亮、光晕、柔边月海；`searchlight(x, y, angle, length, spread)` 探照灯光束
- 城市：`tower(x, base, [(宽, 高), ...], body, rim, light=±1, flutes, windows, slits, far, spire, spire_w, mast, ledge, top_windows)` 阶梯退台高楼，返回顶层顶部中心；`far` 0..1 推进雾里（变浅变蓝变平）；`crown(x, y, w, steps)` 扇形阶梯冠顶（放射窗），返回顶点 y；`clock(cx, cy, r, 时, 分)` 钟面
- 河：`water(horizon, stops, reflect)` 先喷河面渐变，再把地平线以上已经画好的东西镜像进来，打碎成横向波纹，亮的东西反射更强
- 3D 列车：`camera(f, cx, horizon, height)` 水平针孔相机；`express(nose=(X, Z), vp_x, deck, cars, loco, car, gap, nose_len, rake, light, moon)` 在拱桥上渲染流线型列车（距离场 + numpy 球面步进，只对边缘像素 3×3 超采样），返回分层结果 `r`；按画家的顺序叠上去：`frisket(r)` 遮片平涂底色 → `model(r)` 明暗塑形（半朗伯色阶、上肩喷枪高光带、月光轮廓光、下腹反光、远处雾色）→ `lights(r, beam, beam_len, bloom, reflect)` 车窗（卧铺窗帘拉下一半）、头灯、光束、辉光、灯照铁轨、可选的河面倒影；`project(X, Y, Z)` 世界坐标转像素
- 字：`lettering(s, x, base, cap, fill, track, shadow, anchor)` 库内自建的 Deco 展示字母 A–Z（粗竖笔、发丝横笔、高腰线、椭圆字碗），金属渐变填色（中线一道硬分界），可加块状投影；`deco_width()` 量宽度；`caption(s, x, y, size, colour, track, anchor)` 宽字距几何无衬线小字（返回宽度）；`rule()` 金线；`border(inset, gap, width, step)` 阶梯角双金线边框
- 印刷：`finish(paper, tooth, warm, vignette)` 纸纹、微颗粒、暖色偏、轻微暗角
- 颜色常量 `NAVY MIDNIGHT TEAL JADE GOLD BRASS IVORY CREAM MAROON CRIMSON WARM`；坐标像素、y 向下，3D 世界单位米、y 向上；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**黄金时代漫画 `ComicCover`**：
- 思路：先按当年的分工把封面「做」出来，再按当年的印法「印」出来。墨线师在黑版上勾 key 线；上色师在色稿上给每块区域指定三原色的 Ben-Day 网点比例（0 / 20 / 40 / 70 / 100%），整张封面只有几十种颜色；印刷时每版按自己的角度加网、各自错开几像素，新闻纸吸墨让网点变毛、小点丢失、实地发花；油墨透明相乘。网点和错版都不手画
- 构造：`ComicCover(W, H, seed, screen=11, misreg=4, slop=1.6, light=(-0.6, -0.8))`：screen 是网点间距（px），misreg 是各色版的错位量，slop 是手绘分色的游走量；`register(plate, dx, dy, rot)` 手动指定某版的落点
- 纸：`paper(colour, tone, fibres, flecks)` 泛黄新闻纸（云状纸浆、深浅短纤维、树皮屑、不吃墨的纸坑）
- 形状（整页抗锯齿遮罩，可加减乘）：`mask(pts, smooth)`、`circle()`；静态方法 `ellipse_pts()`、`smooth()`（闭合样条）、`tube_pts(路径, 宽度列表)`（四肢、绳子、围巾、耳朵）、`burst_pts()`（星星、爆炸框）、`edge_normals(pts)`（轮廓点和外法线，给 `feather` 用）；`grow()` / `shrink()`
- 色稿：`flat(shape, 颜色)`，颜色是 (蓝, 红, 黄, 黑) 四个网点比例；`graded(shape, [颜色…], p0, p1, edges=[…])` 沿手裁波浪边分档的色带；`rings()` 同心色环；`knock()` 挖白
- 黑版：`part(pts, 颜色, width, heavy)` 是放前景物件的标准做法：擦掉身后的墨线和颜色、铺色、勾一圈背光侧加粗的轮廓；`brush(pts, width, taper, swell)` 两头尖、中段鼓的毛笔线；`pen()` 细笔；`outline()` / `edge()` 闭合 / 开放轮廓；`ink()` 实黑块；`erase()`；`mask_outline(mask, width, heavy)` 给任意遮罩（圆的并集、字）描边；`feather(P, N, length, width, spacing, clip, along, toward, curl)` 从阴影边长出来的羽状排线；`hatch()` 平行排线；`speed()` 速度线；`dot()`
- 字：`letter(text, x, y, size, face, colour)` 手写字，逐字微转、微跳（face：letter 漫画手写体 / logo 窄粗体 / bold / slab / heavy）；`text_mask()`；`balloon(text, x, y, size, tail, kind='speech'|'yell'|'thought')` 对白框 / 喊叫爆炸框 / 想法云；`caption(x0, y0, x1, y1, text, colour)` 旁白框；`sfx(text, x, y, size, colour, rot, shade)` 拟声字；`logo(text, quad, vp, depth, colours, shade, shadow, glints)` 透视立体刊名：四个角点定透视，朝灭点挤出 depth 像素，正面上浅下深分档，加挤出面、投影、粗黑外框和高光斜纹
- 做旧（印完以后再加，只作用在各自区域）：`brown_edges()` 边缘泛黄；`spine(ticks, staples)` 书脊折痕、白色应力裂纹、两枚生锈订书钉；`corner('br', radius)` 角上磨掉油墨、折角；`crease(p0, p1)` 折痕处油墨裂开露白；`foxing(n)` 霉斑
- 阶段：`stage(name, plates='CMYK')` 记下当时的各版，出图时只印列出的版：先用 'K' 出黑版线稿，再依次 'YK'、'YMK'、'CMYK'，就是印刷厂的「渐进打样」
- 颜色常量（色稿比例）：`WHITE CREAM PALE YELLOW GOLD ORANGE DEEP_ORANGE RED CRIMSON PINK SKIN TAN BROWN DARK_BROWN SKY LIGHT_BLUE BLUE NAVY VIOLET MAUVE LILAC GREEN LIME GREY LIGHT_GREY SILVER`；油墨颜色 `INK`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**波普丝网 `PopSilkscreen`**：
- 思路：重做 60 年代「工厂」的做法。一张照片做成黑色照相丝网版；一张画布用胶带隔出几格，每格先手涂撞色平涂（底色，再是脸、眼、鼻、项圈……），形状照着照片描得很松、对不准；然后把同一块黑版逐格刮印上去，每格放版的位置、角度和墨量都不同
- 构造：`PopSilkscreen(W, H, seed, light=(-0.55, -0.8))`；`canvas(gesso, thread=3.8, slub=0.18)`：刷了白底漆的棉帆布（平纹布纹高度场、粗节、均匀布光）
- 分格：`grid(cols, rows, gap, margin, origin=(0.5, 0.53), unit=0.285)` 返回 `Panel` 列表。每格里用「单位」作画：origin 是单位原点在格内的位置（宽、高的比例），unit 是每单位占格高的比例
- `Panel` 上取遮罩（局部窗口，四周留 pad 像素，方便渗边和错位）：
  - `shape(pts)`：闭合样条
  - `stroke(pts, w0, w1, profile=)`：渐细笔画，宽度用单位；`profile(t)` 自定粗细
  - `ellipse(u, v, ru, rv, rot)`、`dots([(u, v, r)])`
  - `soft(mask, sigma)`：柔化成给网点用的调子；`blank()`
  - 坐标换算：`at(u, v)` 单位 → 局部像素，`xy(u, v)` 单位 → 画布像素
  - 模块函数：`turn(pts, deg, about)` 屏幕上逆时针转（歪头用）、`mirror(pts)` 左右镜像、`closed_spline()`
- 手涂丙烯：
  - `ground(p, 颜色, direction, bleed)`：一格的底色，刷到胶带为止，有几处渗进胶带下的毛边
  - `paint(p, mask, 颜色, direction, wobble, drift, opacity, dry, streak)`：手涂一块平涂色。wobble 是边缘手抖（px），drift 是这块颜色描偏了多少（px）；顺笔方向有轻微明暗，边缘有干笔拖痕和一道受光的漆脊；只涂在本格里
- 黑版 `key(p, solid, tone, ink, shift, rot, density, flood, starve, pull, nicks, ghost, cell, angle)`，返回印上的覆盖率：
  - solid 是实黑的阴影块；tone 是中间调，印成 45° 粗网点（cell 约 7 px）；照相阈值的颗粒边和膜上的灰尘点自动加；`stencil()` 可以单独取照相版遮罩
  - shift、rot：这一格放版的偏移（px）和转角（度）
  - density：墨量，0.92 缺墨、1.0 正常、1.15 墨多，低于约 0.9 就印不出脸
  - flood：墨多糊版，形状变胖、细缝填死、挤出墨团
  - starve：干在网上的一块墨斑；pull：刮板方向（90 自上而下，0 自左向右）；nicks：刮板缺口留下的细白线
  - ghost=(dx, dy, 强度)：版放了两次，留下一层灰影
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度
- 颜色常量（60 年代丙烯撞色）：`HOT_PINK PINK BLUSH RED ORANGE TANGERINE LEMON YELLOW CREAM LIME GREEN MINT TURQUOISE SKY BLUE ULTRA VIOLET LILAC WHITE`，底漆 `GESSO`，黑墨 `INK`

**ASCII 字符画（行式打印机） `LinePrinter`**：
- 思路：画面不直接画在纸上，而是画进一张隐藏的「角色图」（每个字符格 6×10 个采样）：每块区域带一个角色（用哪套字符）和一个调子（要多少墨），后画的盖住先画的；`compose()` 再逐格决定打哪个字：线条格按线的方向和在格里的位置选 \| / \\ _ - . ' X +，剪影转折处同样处理，填色格按调子从角色的字符阶梯里选（同角色内误差扩散），最暗的格用叠打。最后模拟鼓式行式打印机逐行击打
- 构造：`LinePrinter(W, H, seed, cols=132, top=40, cpi=10, lpi=6, form_in=14.875, ss=2, weight='bold', ppi=None, page_in=11.0)`；`top` 是撕线的位置，`ppi=None` 让纸宽撑满画面，调小就整张纸躺在桌上、左右露出桌面；`page_in` 是纸深（11 英寸 66 行，8.5 英寸 51 行，配合 ppi 能让上下两道撕线都入画），`page_rows` 是一页的行数；`rows` 是看得见的行数，坐标一律用（列, 行），可以是小数；`xy(col, row)` / `centre(col, row)` 换算成像素
- 纸：`form(white, green, desk, band=3, first_green, holes)`：14 7/8 英寸宽的绿条连续纸，每 3 行一条浅绿带，两侧导孔（孔里看得到桌面和纸的投影，偶有被拉长的破孔）、微孔撕线、每 `page_rows` 行一道横向撕线和折痕；纸比画面窄时两侧是桌面和纸的投影。要留页边就在 `compose()` 前 `erase(rect(0, page_rows − 2, cols, rows))`
- 角色：`role(name, ramp, edge='outer'|'all'|None, outline='straight'|'round'|dict, dither, noise, group, inner_max)`；ramp 从浅到深，如 `['', '.', ':', '%', '@', '#', '#@']`，`'#@'` 表示 # 上再叠打 @；`group` 相同的角色之间不描边；`inner_max` 只在亮处给同角色的块与块之间描边
- 形状（子格遮罩）：`circle(col, row, 半径列数)`（自动按格子比例变圆）、`ellipse()`、`poly(点列)`、`shape(控制点)` 平滑闭合曲线、`rect()`、`blob()`
- 调子：`sphere_tone(col, row, r, light, amb)` 球（烟团）、`cylinder_tone(c0, c1, light, amb)` 竖圆柱（箭身）、`ramp_tone(p0, p1, t0, t1)` 线性渐变
- 作画：`fill(mask, role, tone)`；`erase(mask)` 挖回白纸；`stroke(点列, width, glyphs=None|'round'|单个字符, smooth)` 画线（单个字符如 `'='` 强制用它，平台、横梁用）；`billow([(col, row, r), ...], role, light, amb, shadow, glow=(col, row, r, 强度), lift=调子场)` 一团云：每团按球打光、给身后的云团投接触阴影，glow 是火焰从里面照亮，lift 给云底加暗
- 文字：`text(s, col, row, strike=2)` 原样打字（strike=2 两次叠打成粗体，opaque 让空格挖掉底下的画）、`text_v()` 竖排；`plot(col, row, w, h, xlim, ylim, [(xs, ys, 字符), ...], xticks, yticks)` 打印机绘图（I 纵轴、- 横轴、+ 刻度），返回把数据坐标换成格子坐标的函数（好在上面圈点）
- 打印：`compose()` 出字符网格（`listing(path)` 存成纯文本）；`print_rows(r0, r1)` 逐行击打（同一行所有叠打在走纸前打完）：同一个字符总是偏高或偏低一点（鼓的相位）、每列锤子力度不同（有一两列弱锤）、叠打的那一遍整行错开零点几像素、色带随作业变淡并沿宽度磨损、偶有色带偏低的行字头发虚、磨损的字模每次都缺同一块、墨往纸里洇、锤子压出极浅的凹痕
- 批注：`pen(点列, colour, width)` 圆珠笔（起落笔略积墨、快处变淡、在纸纹上断续）、`ring(x, y, rx, ry)` 顺手画的不闭合圈、`tick(x, y, size)` 打勾、`pen_text(s, x, y, size)` 手写字；这些用像素坐标
- 层次与动画：先 `fill`/`stroke`/`text` 摆完整张画，再 `compose()`，然后分几段 `print_rows` 并各 `stage(name)`，就是一行行打出来的动画；`save('x.jpg')` 默认 quality 88、4:4:4 色度
- 颜色常量 `INK`；`save(path, stages_dir)` 时按 1× 输出各阶段

**低多边形 `LowPoly`**：
- 思路：一个只用 numpy 写的软件光栅化器，照 1999 年代主机的做法画：小帧缓冲（默认 384×216）、顶点吸附到整像素、背面剔除、整个场景的三角形按平均深度排成一张表从远到近画（画家算法 / ordering table）、近平面裁剪；每个三角形一个颜色（平面着色），贴图仿射插值、不做透视校正，逐顶点雾；最后 15 位色加 4×4 有序抖动，最近邻放大。调用顺序不影响遮挡
- 构造：`LowPoly(W, H, scale=5, seed, record=True, zbuffer=False, near=0.6, far=260)`；世界坐标 X 右、Y 上、Z 向前，单位米；`zbuffer=True` 是 N64 式逐像素深度
- 相机：`camera(eye, target 或 yaw=, pitch=, fov, roll)`；`aim(世界点, at=(fx, fy))` 转动相机让这个点落在画面的指定比例位置（构图用）；`project(p)`、`ray(sx, sy)`
- 天与光：`sky(zenith, horizon, glow, bands)` 按仰角渐变、太阳周围暖光晕、可选细条云；`sun(screen=(fx, fy) 或 direction=)` 画太阳并定光照方向；`light(lift=度)` 着色光单独抬高；`ambient(sky, ground)` 半球环境光；`fog(near, far)` 逐顶点雾，颜色默认等于地平线
- 地形：`path([(x, z), ...])` 中心线，`along(path, s, u, y)` 取点、`heading(path, s)` 取方向；`canyon(path, step, height, width, wobble, strata, buried)` 沿中心线放样的峡谷（河床、沙岸、碎石坡、两级悬崖和台阶、崖顶、台地；岩壁按高度贴岩层，平面俯贴沙地 / 灌丛）；`river(path, half, ripple, spec)` 起伏小面的河；`mesa(x, z, r, h, base)` 方山；`arch(path, s, span, rise, base)` 天然石拱；`boulder(x, y, z, r)`；`tree(x, y, z, height)` 十字插片杜松（贴图 alpha 硬裁切）
- 物件：`ring(centre, facing, radius, tube)` 多面金环；`aircraft(pos, heading, roll, pitch, size, body, trim, canopy, spinner)` 约 230 个三角形的小特技飞机加半透明螺旋桨盘；`torus()`；`mesh(V, F, colour, uv, tex, lit, spec, shine, blend, alpha, two_sided, fog, bias, cutout, glow)` 任意网格：blend 用 'opaque' | 'half' | 'add' | 'sub' | 'quarter'（当年的四种半透明模式），bias 是排序偏置（负数后画），glow 把面往全亮拉（拾取物）
- 特效：`shadow(x, z, y, radius)` 正下方的圆斑影子（'sub' 混合）；`sparkle(p, size)` 加色四角星；`flare()` 屏幕空间镜头光晕（太阳被挡住就不画）
- 贴图：`texture('strata'|'ledge'|'sand'|'water'|'rock'|'juniper'|'spark')` 32–64 像素的程序贴图，最近邻取样
- HUD（帧缓冲像素坐标）：`text(s, x, y, scale, fill=颜色或自上而下的渐变列表, italic, anchor)` 5×7 点阵字（加粗、斜切、1 px 黑描边加投影）；`counter(label, value, x, y, icon, anchor)` 小标签加大号斜体数字；`icon('ring'|'plane'|'clock')`；`gauge(x, y, value, number, unit)` 阶梯速度条；`panel()` 半透明框；`minimap(x0, y0, x1, y1, path, s0, s1, rings, done, plane, heading, finish, title)` 转到机头朝上的赛道小地图
- 动画：`stage(name)`；`stage(name, wire=True)` 隐藏线线框；`stage(name, fog=False, textures=False)` 平面着色预览（每个面取中心那个纹素）
- 颜色常量 `GOLD WHITE BLACK HUD_YELLOW HUD_ORANGE HUD_RED HUD_GREEN HUD_CYAN`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**喷漆模板涂鸦 `Stencil`**：
- 思路：一面真的墙，一张张真的卡纸模板，一罐喷漆。墙是反照率加高度图、左上方一个低太阳照亮；模板是卡纸上刻开的洞，被刻断的卡纸（O 的中间、手臂和身体之间、轮辐之间）会掉，所以要留「桥」，桥在漆上是一道道露墙的细缝；喷漆是罐子来回扫，每扫一道落下一个高斯锥，漆膜就是这些笔画的和；漆是一颗颗雾滴，厚的地方连成实色，薄的地方是散点，所以所有软边都是麻点而不是模糊；漆盖不进小孔、贴着墙面起伏、带缎面光泽；漆太厚的下边缘会往下流成滴痕
- 墙：`wall(colour, planks, ties, ground, damp, crack)` 木纹模板清水混凝土：一条条木板压出的色带和木纹（绕着树节走）、板头接缝、板缝挤出的断续水泥浆棱、对拉螺栓孔（锈铁头 / 灰浆堵头 / 空孔）、气泡孔、雨痕和锈水、返潮水线与泛碱、发丝裂缝；`pavement(colour)` 墙脚的沥青人行道（骨料、补缝沥青、口香糖渍、油渍、墙脚灰土和杂草）
- 旧痕迹：`buff(x0, y0, x1, y1, colour, roller, ragged)` 市政灰漆滚筒覆盖（竖向滚道、台阶状上下边、发干的两头、重叠处偏深，底下的东西透一点出来）；`freehand(..., wash=0.7)` 被高压水枪冲掉一半的旧签名
- 模板：`card(x0, y0, x1, y1, origin, scale, tape, material='manila'|'board')` 返回 `Card`，形状用设计单位（px = origin + scale × 点），返回局部遮罩，可以用 numpy 相加相减：
  - `poly(pts, smooth, facet)`（facet 是刀沿曲线一小段一小段切的抖动）、`capsule(p0, p1, r0, r1)`、`ellipse(c, rx, ry, rot)`、`ring(c, 外, 内)`、`stroke(pts, w0, w1)` 渐变宽度的带子
  - `text(s, x, y, size, font='stencil'|'slab'|'block', anchor, spacing, bridge)` 模板字：每个字腔自动上下各一座桥
  - `cut(mask)` 刻开；`keep(mask)` 留住卡纸（反白字、细节）；`bridge(p0, p1, width)` 手放一座桥；`bridges(width)` 自动找出所有会掉的孤岛、补最短的桥（大孤岛两座、方向相反）；`islands()` 还剩多少像素的卡纸会掉（0 才算刻好）
- 明暗分版：`shade_side(mask, light, depth, soft, wobble, seed)` 背光一侧 depth 像素宽的月牙，多层模板的灰版、黑版用它切；wobble 让边像手刻的
- 喷：`spray(card, colour, coats, cone, angle, misreg, at, rot, lift, mist, drips, drip_len, wet, linger, ghost)`。cone 是喷幅（像素）；misreg 是贴歪的随机误差（多版套色用约 2）；at / rot 把同一张小模板挪到别处、转个角度再喷（燕子、树叶、蝴蝶结）；lift 卡纸翘起量（软边和渗漆）；mist 外溢雾化；drips 滴痕多少，wet 起滴的漆膜厚度
- 徒手：`freehand(pts, colour, width, coats, speed, spits, drips, mist, wash)` 细喷嘴：线宽和浓淡跟着手速（speed 每个控制点一个系数，慢 = 重），起笔一团、停顿处滴、旁边几颗喷嘴吐出的大漆点
- `stage(name, card=c)` 快照里模板还贴在墙上（胶带、卡纸上积的漆、切口一侧亮一侧暗、卡纸投影），动图用；`save(path, stages_dir)` 默认 quality 88、4:4:4 色度
- 颜色常量 `BLACK WHITE GREY RED CONCRETE`；`HIDE` 各色遮盖力（白最差），`GLOSS` 光泽；字体 `stencil_font(style, size)` 找 DIN Condensed Bold / Impact、Rockwell、Arial Black，可用 `INKPAINT_FONT_STENCIL` 等指定

**刺绣徽章 `Patch`**：
- 思路：像绣花机那样绣：每块形状按自己的针向切成平行的行（扫描线），每行再切成针，所以形状的边缘就是一排针脚。每根线按圆柱打光，两头扎进布里（针孔是小凹坑），高光是各向异性的（Kajiya-Kay），同一种颜色换个针向亮度就不同，这正是「绣出来」而不是「印出来」的关键。徽章先是一块裁好的斜纹底布放在牛仔布上（有厚度、有投影），再绣、再包边，最后手缝上去
- 牛仔布：`denim(colour, weft, warp_px, pick_px, fade)` 3/1 右斜纹（经密纬疏，斜纹约 60°，露白纬点、竹节纱、磨白），2× 渲染；`seam(pts, thread, rows, stitch, gap, fold)` 双明线的折边缝，折棱磨白
- 底布：`blank(pts, 颜色)` 返回 `Blank`（`.pts` 轮廓、`.mask` 遮罩）；轮廓：`circle_pts(cx, cy, r)`、`arch_pts(cx, top, w, h, corner)` 拱形异形章、`rocker_pts(cx, cy, r0, r1, span, centre)` 弧形条章；遮罩：`circle()`、`ring()`、`poly(pts, smooth)`、`text_mask()`，用 `*`、`np.maximum`、`1 - m` 组合
- 填充：`fill(mask, 颜色, angle, kind='tatami'|'satin', pitch, length, stagger, maxlen)`：tatami 是大面积底色（短针约 15 px，每行错开 0.3 针）；satin 一行一根长线（字、雪顶、火焰、细长形），超过 maxlen 自动拆成交错的分段缎面；angle 是针向（度，逆时针，0 = 左右走）
- 沿路径：`column(pts, 颜色, width, closed)` 缎面柱，针和路径垂直（圆环分隔线、木柴、帐篷杆）；`run(pts, 颜色, stitch, gap, width, clip=)` 平针 / 刺子绣虚线 / 明线；`knot(x, y, 颜色, r)` 法式结（星点、火星）；`star(x, y, r, 颜色)` 四角缎面小星
- 包边：`merrow(blank, 颜色, width)` 锁边：斜着一圈圈绕过布边的圆绳，用于圆、椭圆、弧形条章；`satin_border(blank, 颜色, width)` 热切缎面边，用于其他异形轮廓
- 字：`text(s, x, y, size, 颜色)`、`arc_text(s, cx, cy, r, size, 颜色, centre=90, bottom=False)` 缎面字，每个字母斜着走针；bottom=True 沿下弧读、字头朝里
- 手缝：`whip(blank, 颜色, frm, to)` 卷边针，按轮廓长度的比例缝一段，返回最后一针的位置；`thread(pts, 颜色, lift)` 散落的缝线（有捻度，抬起越高影子越远）；`needle(eye, tip)` 躺在布上的钢针（先画线：线会从针眼里露出来）
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**蓝图工程图 `Blueprint`**：
- 思路：先在描图布上用几种固定粗细的鸭嘴笔上墨（轮廓、剖面线、尺寸、单笔画字全是「墨」），再像真的晒图那样接触曝光：有墨的地方挡住弧光灯，药面不变蓝，冲洗后是白线；其余地方生成普鲁士蓝。曝光 = 透光 × 灯的照度，显影按 S 曲线（有阈值）——粗线纯白、发丝线发浅蓝、底色饱和；线的边缘有爬光（压得紧的地方锐、接触不良的地方软）和一圈淡淡的光晕；灯在中间强、四周弱，药面有涂布条纹、斑驳和晾干时自上而下的流痕；颜色按普鲁士蓝在纸上的比尔–朗伯吸收计算，纸纤维透出来。晒好之后再过它的「一生」：折叠、褪色、手摸、水渍、图钉，最后工地上的人拿红蜡笔批注
- 构造：`Blueprint(W, H, seed, ss=3, tracing=(x0, y0, x1, y1))`；`expose(time, contact)`：曝光时间（0.8 欠曝发浅、1.3 过曝）和压框接触不均的程度
- 笔：`line(pts, pen, closed)`，pen 为 `'heavy' 'thick' 'medium' 'thin' 'fine'` 或像素宽，线头有一点积墨；`dashed(pts, pen, dash)` 虚线；`centerline(pts)` 点划线；`circle`、`arc`、`box`；`fill(pts)` 涂实（薄金属剖面、箭头、比例尺黑格）；`dot`；`erase(pts)` 用刀片刮掉墨；`pencil(pts)` 留在描图布上的铅笔线（晒出来是很淡的浅线）；`Blueprint.arc_pts(...)` 取弧线点（角度逆时针、纸面 y 向上）
- 剖面线：`hatch(polys, angle, spacing, pen, holes, kind)`，kind 为 `'lines'` 石材 / 通用、`'cross'` 金属、`'glass'` 三短线玻璃、`'rock'` 岩石裂纹、`'stipple'` 混凝土点、`'solid'` 涂实；`ground(pts)` 自然地面线加短斜线组；`breakline(p0, p1)` 折断线
- 字：`text(s, x, y, size, anchor, pen, slant, spacing, rot, guide, clear)` 内置单笔画大写字体（字模板样式：A–Z、0–9、Ø ± ° × ℄ ✓ → 等），size 是大写字高，anchor 如 `'ls' 'mm' 'rs'`（s = 基线），slant 约 0.22 是斜体字，guide=True 留下铅笔导线，clear=True 先刮掉字后面的剖面线，`\n` 换行；`text_width(s, size)`；`cjk(s, x, y, size, anchor, condense)` 中文长仿宋（压窄，找 STFangsong / FangSong，找不到用中文字体，可用 `INKPAINT_FONT_FANGSONG` 指定）
- 制图符号：`dim(p0, p1, offset, text, size, arrows, scale, fmt, text_off, shift, clear)` 尺寸（尺寸界线、箭头、数字顺着尺寸线写，短尺寸自动把箭头放到外面；offset=0 时不画界线，可以自己画链式尺寸）；`level(x, y, text, side, length, mark_at)` 标高符号；`leader(pts, text, end='arrow'|'dot'|None)` 引出线；`cut_mark(p0, p1, label, view)` 剖切符号；`bubble(x, y, r, top, bottom)` 详图索引圈；`view_title(x, y, title, sub, size, bubble)` 图名（粗细双下划线 + 比例）；`north(x, y, r)` 指北针；`scale_bar(x, y, px_per_unit, units, label)` 比例尺；`border(x0, y0, x1, y1, zones)` 图框和分区编号；`table(x0, y0, widths, heights)` 标题栏 / 修改栏，返回每格坐标 `[行][列]`；`revision(x, y, mark)` 修改三角
- 图纸的一生（只作用在晒好的图上）：`fold(xs, ys, wear)` 折成档案尺寸（折痕处药面裂白、两侧一明一暗、交叉处磨损）；`fade(x0, y0, x1, y1, amount)` 朝外那一格褪色；`grime(...)` 手摸发灰；`stain(x, y, r)` 碱性水渍（蓝变锈褐、两道潮线）；`tack(x, y)` 图钉孔与锈圈；`tear(x, y, direction, length)` 折痕碰到纸边处的小裂口
- 红蜡笔：`red(pts, width)`、`cloud(pts, bump)` 修改云线、`red_text(s, x, y, size, rot)` 手写批注；红色是全图唯一不属于晒图本身的颜色
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**儿童蜡笔画 `Crayon`**：
- 思路：糙纸是一张纸纹高度图，均衡成 [0, 1] 的均匀分布，所以「1 − 阈值」就是蜡能挂上的纸面比例；蜡只挂在纸纹凸起上：`纸纹 + 0.35 × 已有的蜡 > 1 − 接触 × 压力` 才上蜡，轻涂露出一片白点，重涂压进凹处，后涂的颜色更容易挂在先涂的蜡上（蜡层堆积）。蜡笔沿笔道被拖着走，所以露白的小坑被拉成顺着笔道的短条。用秃的笔头是一个带棱的平面：一笔 = K（≈ 宽 / 3）条强弱不一的平行细线，笔道里有白色细纹。颜色是半透明的乘性混合：`新 = lerp(底, 颜色 × 底^0.6, 覆盖)`，黄上涂蓝变绿、黑线涂不掉、同色重复越涂越深。最后纸纹和蜡层一起当高度图，左上低角度光打光，厚蜡处有一点蜡光
- 构造：`Crayon(W, H, seed, paper='#f7f3e9')`；`paper(tone, grain, fibres, scan)` 糙纸（纸纹、纸浆纤维、不匀的扫描光）；颜色常量 `c.C`（24 色蜡笔盒：red orange yellow yellowgreen green darkgreen sky blue navy violet purple pink magenta brown tan peach apricot black grey white …）
- 小孩的手画的形状（返回点列）：`circle(cx, cy, rx, ry, rot, lumpy)`、`rect(x0, y0, x1, y1, skew)`（四个角各歪一点）、`poly(pts)`、`wobble(pts, amp)`；遮罩：`mask(pts)`、`stroke_mask(pts, width)`、`grow(mask, px)`、`drawn()`（纸上已经画了的地方）
- 涂色：
  - `scribble(mask, 颜色, angle, width, density, pressure, reach, mess, angle_jitter, avoid, halo, fade)`：来回涂。reach 是胳膊够得着的长度，大片按块涂、每块各自的角度（None = 一块）；density 低时两道之间留三角形白缝；mess 是在轮廓处的过冲 / 没涂到；avoid + halo 绕着涂、留一圈白（绕开处转折小心，不进比 0.7 × 笔宽窄的缝）；fade=(y 满, y 无) 越往下越稀（涂烦了的天空）；
  - `loops(mask, 颜色, r, width, density)`：一圈圈的绕圈涂（树冠、太阳、皮球、斑点）；
  - `follow(pts, 颜色, width, passes, crayon)`：顺着一条带子涂（彩虹的每一道、路）；
  - `burnish(mask, strength)`：使劲压着涂：已有的蜡压进纸坑，白点合上，颜色变深发亮
- 线和点：`line(pts, 颜色, width, pressure, closed, avoid)` 一根蜡笔线，落笔重、收笔轻；closed=True 时尾巴越过起点、差几像素对不上；avoid 让线停在东西背后；`dab(x, y, r, 颜色)` 拧进纸里的实心点（眼睛、苹果、西瓜籽）
- 写字：`write(s, x, y, size, 颜色或颜色列表, width, tilt, jumble, spacing, anchor)`：细字体字形细化成中心线，再用圆头蜡笔描；每个字各自歪 ±tilt°、大小和基线乱跳 jumble、按列表轮换颜色。字体按 STHeiti Light / Hiragino Sans GB / Noto Sans CJK Light / 微软雅黑 Light 找，可用 `INKPAINT_FONT_CRAYON` 指定
- 纸上的东西：`crumbs(x0, y0, x1, y1, colours, n)` 蹭下来的蜡屑（凸起、带小影子）；`stick(x, y, angle, 颜色, length=360, radius=22, tip='worn'|'new'|'broken', wrap, peel, label)` 一根真蜡笔（哑光蜡、印花包装纸、伪文字标签、断口、撕掉的纸），合成时画、带柔和投影
- 顺序：先勾线（东西的内部遮罩收进一个 OBJ），再涂大片并绕开 `U(OBJ, drawn())`，最后在白纸上给东西上色；字和签名写在涂天空 / 草地之前
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度；底层 `deposit(cover, box, 颜色)` 把任意接触场按纸纹上蜡

**绿屏终端 CRT（荧光字符画） `CRTTerminal`**：
- 思路：重做一台字符终端，不在屏幕上「画图」：
  - 屏幕上的一切都是字符内存里的字：每格带亮度属性（dim / normal / bold）、反白、下划线，行可以是双倍宽或双倍高；
  - 字库 ROM 是 7×10 点阵格里的 5×7 字，小写字母带两行下伸部；另有一套图形字符：框线 ─│┌┐└┘├┤┬┴┼、画曲线用的五档扫描线横条 ⎺⎻─⎼⎽（`SCAN`）、八分块 ▁▂▃▄▅▆▇█（`EIGHTHS`）、░▒▓、° ·、▲▼◆、箭头；
  - 字符画先画进一张隐藏的「材质 + 调子」图（每格 7×10 个采样），`compose()` 逐格选字：里面的格子按材质的阶梯和调子选字，同组之内做误差扩散；剪影穿过的格子按边的方向和位置选 _ . - ' / \ ( ) |；笔画格子按笔画方向选字。屏幕上「密 = 亮」：暗的东西要稀、要 dim；
  - 电子束每行字扫 10 条扫描线：点拉伸半个点，视频放大器有拖尾，光斑随电流变粗（bold 时扫描线之间的缝被填满）；
  - P1 荧光粉亮到饱和时发白；之后依次是余辉、烧屏、桶形畸变、边缘变暗、玻璃里的光晕，以及房间的倒影
- 构造：`CRTTerminal(W, H, seed, cols=120, rows=36, phosphor='green'|'amber'|'white', opening=(88, 60, 1832, 958), radius=62, raster=(0.955, 0.93), curve=0.065)`；opening 是机壳开口，raster 是未畸变的光栅占开口的比例，curve 是桶形强度；`cw`、`ch` 是一格的像素宽高
- 字符内存：`write(col, row, s, attr)`，attr 取 `'dim'`、`'normal'` 或 `'bold'`，可加 `'+rev'` 反白、`'+ul'` 下划线；`big(col, row, s)` 双倍高双倍宽，占 row 和 row+1 两行（这两行只能放大字，每个字占两列）；`wide()` 双倍宽；`box(c0, r0, c1, r1, attr, title)`、`hline()`、`vline()`；`cursor(col, row, 'block'|'ul')`；`clear()`；`listing(path)` 存成纯文本
- 字符画（隐藏图）：
  - `material(name, ramp, attrs, outline, group, edge, dither)`：ramp 从暗到亮，如 `' .:+*%#@'`；attrs 每档一个亮度，提亮优先靠它，不靠更花的字；outline 取 `'cloud'`（斜坡一律 ( )）、`'round'`、`'straight'` 或 `None`（只按调子，不描边）；group 相同的材质之间不描边；edge 固定轮廓字的亮度
  - 形状：`circle(col, row, r)`（r 按列数，自动按格子比例变圆）、`ellipse()`、`poly()`、`shape()`（平滑闭合）、`rect()`；调子：`sphere_tone()`、`radial_tone()`、`ramp_tone()`
  - 作画：`fill(mask, 材质, tone)`、`erase(mask)`、`stroke(点列, 材质, width, glyph)`；`puffs([(col, row, r), ...], 材质, light, amb, base, flat, base_dark)` 一朵云，base 用整数行，平底打成一根 _
  - `compose(region)` 选字，`reveal(r0, r1)` 把选好的字一段段放进屏幕；`put(col, row, s, attr)`、`sprite(col, row, 行列表, attr, attrs, swap)` 手摆的小件（星、雨、房子、灯塔、开灯的窗），sprite 行内的空格不透明
- 图表：`plot(col, row, w, h, xs, ys, xlim, ylim, attr)` 每列一个扫描线横条、每行 5 档高度，返回 `at(x, y)` 把数据坐标换成格子坐标，方便标注；`bars(col, row, h, values, vmax, attr)` 八分块柱
- 显像管：`trail(col, row, s, level)` 余辉（前一帧约 0.32、再前一帧约 0.10）；`burn(col, row, s, depth)` 烧屏，放在反白条的空白处最好认；`tear(row, dx, lines)` 行同步错位；`power(on)` 关机时只剩玻璃和倒影；`brightness` 光栅底亮
- 动图阶段：关机 → 开机光栅 → 敲命令 → 标题 → 字符画一段段出来 → 曲线 → 柱和轴 → 结论；`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度
- 常量 `LEVELS PHOSPHORS SCAN EIGHTHS PUTTY ROM_CHARS`

**热成像 `Thermal`**：
- 思路：热像仪看不见颜色和光，只看见每个表面有多热，所以不画 RGB，分三步：先画一张温度场（°C，传感器分辨率的 2 倍）；再让它经过一台非制冷热像仪（镜头模糊、按像元采样、噪声和竖条纹、中心偏凉、细节增强、自动增益）；最后用伪彩色板上色，叠清晰的 OSD。坐标都用画布像素，温度用摄氏度
- 构造：`Thermal(W, H, sensor=(640, 360), ss=2, seed, ambient=21)`；sensor 越小越有热像仪的糊，范例用 480×270
- 形状 → 遮罩：`poly(pts)`、`shape(pts)` 闭合样条、`rect(x0, y0, x1, y1, r)`、`ellipse(cx, cy, rx, ry, rot)`、`blob()`、`line(pts, width)`；用 `*`、`1 - m`、`np.clip(a + b, 0, 1)` 组合
- 温度场：`ramp(p0, t0, p1, t1, ease)` 线性渐变、`radial(cx, cy, rx, ry, t0, t1, power)`、`texture(scale, seed)` 噪声；`room(top, bottom, y_top, y_bottom)` 背景空气分层（上暖下凉）
- 物体：`surface(mask, temp, emissivity, reflected, grain, soft, fuzz, limb, limb_px)`：temp 可以是数或 ramp / radial 场；emissivity < 1 的抛光金属读数被拉向反射温度（默认室温）；grain 材料不匀（°C）；fuzz 毛边；limb 圆形物体在轮廓处变凉。`warm(mask, dT)` 加减热；`seam(pts, dT, width)` 门缝、砖缝、折线
- 热往外走：
  - `soak(mask, temp, reach, strength, onto)`：热晕渗进周围表面（先 soak 再画物体本身，onto 限定承受的表面）
  - `plume(path, temp, w0, w1, opacity, cool, eddy, wisp, puffs, seed, fade_out)`：沿路径的热气 / 蒸汽 / 冷气，越走越宽、越凉、越碎；temp 低于室温就是冷气（路径朝下）；`rise(x, y, height, sway, lean)` 生成一条往上飘的路径
  - `pool(x, y, temp, reach, spread, tongues, squash, width)`：落到地上铺开的冷（暖）气舌，spread 是地面上的方向范围（0 = 向右，90 = 朝镜头）
  - `prints(steps, temp, size, squash, spread)`：余温脚印，steps = [(x, y, 朝向°, 比例, 年龄 0 新 .. 1 没了)]，越旧越淡越散；`paw()` 单个爪印遮罩
  - `reflect(region, axis_y, strength, blur_px, fade)`：釉面地砖倒映上方更热的东西
- 相机：`camera(palette, span, agc, plateau, curve, netd, fpn, optics, dde, dde_clip, narcissus, pixel, saturate)`
  - palette：iron / rainbow / white_hot / black_hot / arctic；span=None 时按画面自动定上下限
  - agc：直方图均衡（平台限幅）占的比例；curve=[(°C, 0..1), ...] 是手调色调曲线，替代线性 span，要让房间、猫、灶台各占一段颜色时用它
  - netd、fpn：时间噪声和竖条纹（°C）；optics：镜头模糊；dde：细节增强（只放大小温差）；narcissus：中心偏凉；pixel：保留多少传感器像素格
- OSD（调用时记下，出图时按该阶段的传感器图像读数，数字和颜色永远对得上）：
  - `statusbar(rec, date, clock, battery, emissivity, mode, height, reflected)`
  - `scalebar(x0, y0, x1, y1, ticks, height)`：宽 > 高是横向；刻度按增益曲线的非线性位置放，挤在一起的自动跳过；给 height 时底部加半透明条
  - `spot(x, y, label, name, side, r)`、`box(x0, y0, x1, y1, label, name)`、`hottest(region)`、`coldest(region)`、`profile(p0, p1, inset=(x, y, w, h), label, name)` 线剖面 + 插图、`results(x, y, width)` 读数表、`reticle()`、`text()`
- `level(v)` 某个温度落在色板的哪个位置；`stage(name)` 只存温度场和 OSD 条数，`save(path, stages_dir)` 统一用最终的增益出所有快照，颜色不会在阶段之间跳；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**代尔夫特蓝瓷砖 `DelftTile`**：
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

**洞穴壁画 `CavePainting`**：
- 思路：颜料是涂上去的，不是凿出来的（和岩画相反）：浅色石灰岩高度图 + 一层层颜料覆盖场（乘进 albedo，石头的斑驳透出来），最后只用地上的篝火和油灯照：每盏都是点光源，半 Lambert 明暗 + 平方反比衰减 + 逐像素沿光线步进的投影（掠射光让每个鼓包都显形）、湿钙华上的高光、凹处一点冷色环境光；再叠火焰发光、泛光、烟和色调曲线。光照缓存，只有高度图变了才重算
- 构造：`CavePainting(W, H, seed)`
- 洞壁：`wall(colour, relief, scallops, grain)` 石灰岩（大起伏、岩脊、溶蚀扇贝纹、颗粒、小坑、赭色和灰色斑、凸处钙华皮）；`boss(x, y, rx, ry, height, rot)` 鼓包（把野牛的肚子、马的侧腹画在上面）；`fold(pts, height, soft, side)` 岩面转折；`flowstone(x0, x1, top, length)` 钟乳石帘（橙色条纹、湿亮）；`crack(pts, width, depth, branches)`；`floor(y, tilt)` 朝观者倾斜的泥地；`floor_h(x, y)` 地面高度
- 火与道具：`fire(x, y, size)` 篝火（石圈、灰、辐射状的柴、火舌、火星、烟柱 + 主光源）；`lamp(x, y, size)` 红砂岩油灯（碗、柄、油面、灯芯小火 + 第二光源）；`stone(pts, colour, height)` 石板 / 石子；`heap(x, y, r, pigment)` 研磨颜料堆；`stick(p0, p1, width, colour, hollow, tip)` 炭条 / 空心骨管（hollow=True，tip 是管口的颜料）
- 起稿（单位坐标，facing 1 朝右 / −1 朝左，size 是身长）：`bison(x, y, size, facing, head_drop)`、`horse(…, gait='run'|'gallop'|'stand')`、`deer(…, kind='stag'|'hind', gait='leap'|'stand')`、`hunter(x, 脚底y, 身高, facing, pose='throw'|'run')`（`anchors['grip']`、`['spear_dir']` 挂矛）、`spear(p0, p1, width)`、`hand(x, y, size, rot, side, spread, fold=(3, 4))`（腕部为原点、手指朝上，fold 是弯下去的手指）、`shape(...)` 自定义；返回 `Figure`：部件 body / legs（只算身体轮廓以下）/ tail / horns / antlers / mane / ears，区域 head / hump / belly / back / front；`fig.sel('head', 'mane')` 取一部分，`fig.anchors['eye']` 等
- 上色（都接受 Figure 或 `fig.sel(...)`）：
  - `sketch(fig, width, passes, strength)` 炭条找形线（每遍沿略微游移的轮廓）；
  - `blow(t, 颜料, density, edge, halo, speckle, rim, gradient, relief, clip, exclude)` 吹喷：软边、晕、雾点、不匀；rim 靠轮廓更浓，gradient 背上更深，relief 在背向火光的岩面上更浓（借岩面起伏），clip 不出界，exclude 留出浅色肚子；
  - `daub(t, 颜料)` 毛皮垫拍涂；`paint(fig, 颜料, kind)` 把猎人、矛整形涂实；`line(pts, width, 颜料, kind='charcoal'|'finger'|'brush')`；
  - `outline(fig, 颜料, width, top, gaps, kind='charcoal'|'blow')` 收边：轮廓内侧一条带，背上和上沿粗、肚子细、有断笔；
  - `dots(pts, r, 颜料)` 掌印点；`stencil(hand, 颜料, spread, puffs)` 吹喷负手印；`handprint(hand, 颜料)` 正手印
- 颜料：`PIGMENTS` 的 red 赤铁矿红赭 / darkred / orange / yellow 针铁矿黄赭 / brown / black 炭黑 / manganese 锰黑 / white 高岭土，或 '#rrggbb'
- 岁月：`calcite(x, y, rx, ry, amount)` 钙华乳白薄膜（盖在画上）；`flake(n, size, min_load)` 零星掉色；`claws(x, y, angle, n, length, spread)` 洞熊爪痕（新鲜浅色沟，划穿颜料）；`soot(x, y, amount, drift, spread)` 篝火熏出的烟柱和顶壁
- 顺序：wall → boss / fold / flowstone / crack → floor → fire / lamp / 道具 → sketch → 红、黄（blow / daub）→ 黑（blow / outline / line）→ 猎人、手印、点 → calcite / flake / claws / soot
- `stage(name)` 立即合成快照，`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**1-bit 早期画图软件 `MacPaint`**：
- 思路：画的不是「像素风插画」，是一台 1984 年式黑白画图软件的整屏。640×360 帧缓冲只有黑白两值，×3 最近邻放大到 1920×1080。文档位图 `doc`（1 = 黑）里的一切都按当年工具的规矩画：8×8 图案贴着文档原点平铺（同一图案的两块天然对缝，图案不随形状弯）；线是方笔头 Bresenham；形状 = 图案填充 + 画在轮廓内侧的边框；油漆桶是 4 连通泛填；文字关掉抗锯齿，样式是对字形遮罩做位运算。界面在渲染时才画，所以每个 `stage()` 都能换工具、图案、光标、菜单
- 构造：`MacPaint(seed, title='untitled', menus=(...), screen=(640, 360), scale=3, ink, paper, doc=None, scroll=(0, 0))`；文档坐标原点是窗口内容区左上角，默认 554×246
- 图案：`PATTERNS` 共 41 种（white / black / gray 50% / light 25% / lighter 12.5% / mist / faint / dark / darker，dots、polka、hlines、vlines、diag、rdiag、thick_diag、grid、xhatch、bricks、scales、weave、basket、diamonds、shingles、waves、zigzag、stars、sprigs、checker、gingham、hstripes、vstripes、wood、grass、pebbles、circles……），图案板显示其中 `PALETTE` 38 种；`paint(mask, 图案, mode='opaque'|'or'|'erase'|'invert')`；`bands(mask, [图案…], y0, y1)` 用几条图案带做「渐变」，接缝处交错打散
- 形状工具（都返回遮罩）：`rect(x0, y0, x1, y1, fill, line, radius)`、`oval(cx, cy, rx, ry, fill, line)`、`shape(点, fill, line, smooth)` 自由形 / 多边形；`line(p0, p1, width)`、`pencil(点, mode)`、`brush(点, size, shape='round'|'square'|'slash'|'backslash'|'bar'|'vbar'|'dot', pat)`、`spray(点, radius, density, pat, clip)`、`bucket(x, y, 图案)`、`dotted(点, gap, size)`；遮罩：`mask_rect / mask_oval / mask_poly / mask_path`、`border(mask, w)` 内侧边框、`pen(mask, w)` 方笔加粗
- 编辑：`copy(rect, to, flip, mask)` 选取 + 拖动复制（flip 是左右翻转，mask 相当于套索选取，背景不跟着走）、`invert(rect 或 mask)` XOR、`erase(rect 或 mask)`
- 文字：`text(s, x, y, size, font='system'|core 字体风格, style=('bold', 'italic', 'underline', 'outline', 'shadow'), anchor='l'|'m'|'r', opaque)`；'system' 是自带的粗体点阵字（大写 9 px 高、2 px 竖笔，只有拉丁字母、数字和少量符号），其他字体走 `core.load_font` 并关掉抗锯齿；outline / shadow 是空心字
- 界面状态（下一次 `stage()` 生效）：`use(tool, pattern, line)` 反白工具（`MacPaint.TOOLS` 里 20 个名字）、当前图案、线宽打勾；`cursor(kind, x, y)`（arrow / cross / ibeam / bucket / spray / brush / pencil，kind=None 隐藏）；`select(rect=…)` 或 `select(lasso=mask)` 行军蚁；`menu(名字, items, checked, hilite, styled)` 下拉菜单，styled=True 时每项按自己的样式写，`menu(None)` 收起；`zoom(x, y, w, h, at, fat)` 放大镜窗，`zoom(None)` 关掉；`retitle(标题)` 存盘改名
- `render()` 返回 640×360 的 0/1 屏幕，`image()` 放大后的 PIL 图；`stage(name)`、`save(path, stages_dir)`（JPG 默认 quality 88，纯黑白时存灰度）
- 动图：帧是纯黑白，缩到 720 宽用 BOX、配固定灰阶调色板（不要用默认的 LANCZOS + 中值切分）

**古希腊黑绘陶瓶 `BlackFigure`**：
- 思路：先在轮上拉出一只陶瓶（轮廓 r(y) 加两只圆把手），所有彩绘都画在「展开面」上（绕瓶一周的弧长 × 高度），同一张展开面既包到曲面瓶上，也能平铺成展开图，两边永远一致。工序照古代作坊：轮上画饰带 → 泥釉画剪影 → 刻线 → 加红加白 → 三段烧成（泥釉这时才变成亮黑）→ 做旧 → 按博物馆照片打光
- 构造：`BlackFigure(W, H, seed)`；`museum(wall, plinth, spot, plinth_x)` 深色展墙、聚光、浅色展台；`pot = throw(cx, foot, height, rmax=None, shape='neck_amphora', eye=0.42)`：foot 是瓶底落在展台上的屏幕 y
- 瓶上的坐标：`y` 是从口沿往下的像素；饰带里的 `x` 是该圈半径处的弧长像素，0 在左把手，正面（看得见的半圈）是 0 .. C/2，背面 C/2 .. C；`pot.TW` 是展开面宽度（按最大半径），`pot.radius(y)`
- 轮制与纹样：`pot.paint_handles()`；`pot.band(y0, y1)` 转着画的黑带（水平、收笔处有一点搭接）；`pot.palmettes(y0, y1, n)` 棕榈叶 + 莲花垂花链；`pot.tongues(y0, y1, n, red_every=2)` 肩部舌纹；`pot.meander(y0, y1, n)` 回纹；`pot.rays(y0, y1, n)` 瓶脚放射纹
- 人物：`z = pot.zone(y0, y1)`，`z.C` 是这一圈的周长；`z.quadriga(x, hw, white_horse, red_manes, bends)` 四马战车（x = 最近那匹马的肚带，hw = 马高）；`z.runner(x, height, phase, beard, back_arm)`；`z.column(x, height, red)` 多立克柱（折返柱 / 终点柱）；`z.judge(x, height, facing=-1, holds='wreath'|'rod')`；`z.tripod(x, height)` 奖品三足鼎；`z.prize_table(x, height)` 摆着小双耳瓶和花冠的桌子；`z.bird(x, y, size, facing, flap)`；`z.letters(text, x, y, size, vertical, retro)` 古阿提卡字母（细笔泥釉写，可反写）
- 自己画新人物：建一个 `blackfigure._Fig()`，用局部单位（脚在 (0, 0)，朝 +x，y 向下）按由远到近调 `slip(poly)` / `cut(pts, w)` / `red(poly)` / `white(poly)` / `reserve(poly)` / `line(pts, w)`，再 `z.emit(fig, X, G, scale, facing)`；线宽是像素（刻刀和细笔的宽度不随人物缩放）
- 三遍上色：`pot.paint()` 刷泥釉剪影（只画新声明的）；`pot.incise()` 刻线；`pot.add_colour()` 加红加白。后两遍按声明顺序重放：近处的黑剪影会盖掉远处的刻线和加彩，再刻出自己的轮廓——四匹马叠在一起也分得清
- `pot.fire()` 烧成；`pot.age(mend=(u, v, rx, ry), misfire=(u, v, r), chips=7, roots=14)`：u, v 是展开面像素（正面中心 u = TW/4）
- 展板：`panel(box, title, subtitle, english, greek)`；`rollout(pot, bands, x, y, scale, half=0|1, caption, ticks)` 把几圈饰带按各自周长展开成上下居中的几条（half 0 = 正面，1 = 背面）；`legend(x, y, [(label, 'clay'|'black'|'incision'|'red'|'white')])`
- `stage(name)` / `save(path, stages_dir)`；每次 stage 都按陶瓶当时的状态重新打光渲染（几何只算一次）

**铅笔素描 `Graphite`**：
- 思路：石墨是一张「质量场」`m`，看到的深浅是 Dmax·(1 − e^−m)，层层叠加但永远到不了黑；石墨是冷灰不是黑，重压处被压亮（`b`），在斜光下带一点银灰的反光。铅笔只在笔尖碰到纸的地方留下石墨：轻压只擦过纸纹的峰（灰里透着白点），重压和软铅才填进纸纹的谷。每一笔都有起笔、加力、收笔，越往纸边画得越少
- 构造：`Graphite(W, H, seed, ss=2)`；`paper(tone, tooth=1.6, felt, mottle)` 素描纸（纸纹高度场、斜光下的微浮雕、左上亮的光线落差）
- 铅笔硬度 `GRADES`：'4H' 'H' 'HB' '2B' '4B' '6B' '8B'，决定每笔多少石墨、能压进纸纹多深、线多宽；越硬越淡越细、纸纹越白
- 遮罩和调子场：`poly(pts)`、`ellipse(cx, cy, rx, ry, rot)`、`ring(cx, cy, r0, r1)`、`band(pts, width)` 粗线（管子、杆）、`lines_mask(lines, width)` 一批细线、`rect()`；`linear(p0, p1)` 从 0 到 1 的渐变、`radial(cx, cy, r)`；`circle_pts(cx, cy, rx, ry, a0, a1, rot)` 椭圆弧上的点（度，屏幕顺时针）
- 完成区：`focus(cx, cy, rx, ry, soft, rough)`：参差的椭圆里画完，往外调子按 finish^0.6 变淡、排线和侧锋整笔整笔地丢，线条变淡，纸边只剩线稿；各方法 `finish=False` 时不受它影响
- 起形：`guide(p0, p1, grade='2H', overshoot)` 两头出头的长辅助线（视平线、透视线、铅垂线）；`guide_ellipse(cx, cy, rx, ry, rot, loops=2)` 绕两三圈的松椭圆加轴线
- 线：`line(pts, grade, pressure, closed, searching, lost, weight, fade=0.35)`：压力沿线起伏；`lost` 让亮面的边断开；`weight` 是一张场（如背光面），高的地方线更重更粗；`searching` 先轻轻找几遍；`strokes(lines, grade, pressure, width, taper, clip, fade)` 一批自由笔画（辐条、链节、篮子的编条）
- 排线：`hatch(mask, tone, angle, grade, spacing, length, layers=(0, 0, 58, -38), pressure, zigzag, edge)`：tone 0 纸白 .. 1 最暗（数或场）；layers 是每层的角度偏移，同一角度重复一次就插在前一层的两线之间，第 k 层只在 tone > k/层数 的地方下笔，越暗压得越重；一块一块地排（每块共用略有漂移的接缝），手腕弧让每笔同向微弯，起笔重收笔挑；`zigzag` 来回不抬笔的连笔排线。`contour_hatch(lines, mask, tone, grade, pressure)` 顺着形体走的笔画（绕车胎、沿管子、沿面包）
- 侧锋：`shade(mask, tone, angle, grade='4B', width=9, pressure, passes=3)` 钝软铅的侧面，宽而软的笔触三遍交叠，只挂在纸纹峰上——晕染前的底色
- 纸擦笔：`smudge(mask, amount, radius, direction, length, pickup, contain=True)` 把石墨推进纸纹谷、往旁边匀开（可顺一个方向拖），颗粒消失；contain 时只在遮罩里匀，不把旁边的空白抹进来
- 橡皮：`lift(mask, amount)` 可塑橡皮按出柔和的亮；`erase(pts, width, amount, soft)` 硬橡皮边擦出清楚的白线（轮圈、管子高光、转角亮边、玻璃反光），会留一点残影
- 页边：`write(s, x, y, size, grade, pressure, font='hand')` 铅笔手写；`value_scale(x, y, w, h, grades)` 试笔色阶（每格一种硬度、下面写标号）；`fingerprint(x, y, r, rot, amount)` 石墨指纹；`smear(pts, width, amount)` 手侧蹭过的灰
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度；颜色常量 `PAPER GRAPHITE SHEEN`

**X 光片 `XRay`**：
- 思路：不画物体的样子，只建「沿射线方向有多厚的什么材料」。每样东西往两张衰减图里累加 μ(材料, 能量) × 密度 × 沿射线的长度（双能：低能约 60 keV、高能约 120 keV），没有先后遮挡，重叠就相加；再按比尔定律 I = e^(−A) 让射线穿过去，经过探测器（散射雾、焦点模糊、线阵探测器逐行增益条纹和每 64 行的模块缝、光子噪声），最后进显示（胶片：越密越亮；或安检伪彩：按 Zeff 分有机橙 / 无机绿 / 金属蓝 / 穿不透黑）。轮廓发光不是画上去的：空心壳体在轮廓处被射线沿侧壁穿过，路径最长
- 构造：`XRay(W, H, px_cm=17, seed)`；所有长度都是画布像素，包括沿射线的深度，`px_cm` 定物理比例。材料表 `MATERIALS`：organic、water、rubber、pvc、pcb、magnesium、mica、glass、aluminium、bone、plaster、ferrite、zinc、steel、brass、copper、tin、lead
- 轮廓：`rrect(cx, cy, w, h, r, rot)`、`ellipse(cx, cy, rx, ry, rot)`、`poly(pts, cx, cy, rot, scale)`（局部坐标搬到画布）、`closed(ctrl)` 闭合样条、`path(ctrl)` 开放样条（点可带第三维深度 z）、`offset(P, d)` 侧移
- 物体：
  - `slab(outline, material, depth, edge, holes, density, tag, texture)`：实心，边缘按半径 edge 倒圆（默认 depth/2 像卵石，0 是锯切边）；holes 打穿的孔；density 可以为负（钥匙上铣出的槽）
  - `shell(outline, material, depth, wall, edge)`：空心壳（箱子、吹风机外壳、相机机身），轮廓发亮、中间淡
  - `rod(P, material, r, wall, ribs, flat)`：沿路径的圆线 / 圆棒，r 可逐点渐变；wall 变管子（两边亮中间暗）；P 带 z 时沿射线潜下去的段更亮；ribs=(幅度, 周期) 螺纹、双重螺旋、绞合线的起伏；flat 扁带（可以是弧长的函数）。`tube(P, m, r, wall)` 同上
  - `coil(p0, p1, R, turns, material, r_wire)` 弹簧 / 电热丝（侧看：转折点亮、前后两半成之字）；`edgeon(p0, p1, thick, material)` 侧看的圆片（风扇、格栅、滤网）；`disc(cx, cy, r, material, depth, hole, rim, dome)` 正看的圆片（硬币带凸边、垫圈、镜片 dome>0 中厚、镜筒圆环正对射线全是壁）；`ball()` 滚珠
  - `zipper(P, material, tooth, pitch, depth, tape)`、`screw(p0, p1, r, head, pitch)`、`cable(P, r, cores, core_r)`
  - `fabric(outline, depth, layers, sheet, density, weave, scale, angle, creases)`：叠好的衣服，折边处布翻过去成软亮边；`weave('plain' | 'twill' | 'knit', scale, angle, amount)` 也可单独给 `slab(texture=)`
  - `belt(y0, y1, lacing=x)`：传送带（纵向帘线纹）、两侧钢导轨和螺栓、钢钩接头；它的衰减记作空气校准，伪彩视图里自动扣掉
- 探测器和显示：`scan(kv, ma, flux=(低能, 高能光子数), scatter, scatter_px, focal, streak, module)`；`film(a0, amax, mix, edge=(细, 粗), glow, vignette, stops)`；`detect()` → (A'_lo, A'_hi)，`show_film(Lo, Hi)`、`show_material(Lo, Hi)`、`zeff(Lo, Hi)` 可单独用
- OSD：`status(left_lines, right_lines)` 顶栏；`footer(left, right)` 底栏（(文字, 颜色)，琥珀 / 绿 / 红自动加底色块）；`flag(x0, y0, x1, y1, n, label, note, side)` 编号报警框；`panel(x0, y0, x1, y1, title)`；`inset(src, dst, 'material' | 'film', title)` 任意区域的插图；`legend(x, y, w)`；`scale(x0, y0, x1, y1, [(标签, 材料, 厚度px)], title)` 衰减标尺（刻度按同一条显示曲线算）；`text()`、`line(pts, dash=)`
- 读数：给物体加 `tag='名字'`，OSD 文字里写 `{名字.z:.1f}`（Zeff）、`{名字.ml:.0f}`（按水折算的体积）、`{名字.cm2}`；出图时从该阶段的探测器图像上量（物体外一圈扣背景），数字和画面永远对得上；`x.readings` 留着最后一次的读数
- `stage(name)` 存 float16 的两张衰减图和 OSD 条数；`save(path, stages_dir)` 每个阶段用同一张噪声出图，阶段之间只有新加的东西在变；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**1930 年代黑白橡皮管动画 `RubberHose`**：
- 思路：照 1930 年代动画厂做一格画面的方式：背景师在板上用灰色水粉画一次背景（平涂 + 干笔刷纹、喷枪光斑和接触阴影，背景线细而灰）；动画师铅笔起稿（两遍、略错开，带结构圆、十字线和动势线）；描线员用黑墨描到赛璐璐上（粗而均匀，压力略有起伏）；上色员在背面涂几档平灰（白、浅、中、深、黑，赛璐璐上不画明暗）；叠在背景上用黑白胶片拍下、印成拷贝、放映很多遍。赛璐璐不透明、从后往前画，后画的挡住先画的；角色要从「后面」经过的背景部分（窗外近山、窗横档、窗帘、被子）存成 clip 遮罩
- 构造：`RubberHose(W, H, seed, ss=2, ink_w=5.5)`（内部 2 倍超采样）；灰阶常量 `WHITE LIGHT PALE MID DARK BLACK INK`
- 背景（画在板上）：`wash(pts, value, value2, axis, tex, line, dark)` 平涂 / 渐变水粉 + 细灰轮廓；`blob(circles, value)` 圆的并集（云、树冠），只描外轮廓；`line(pts, width, dark)`；`airbrush(cx, cy, rx, ry, amount)` 喷枪光斑（正提亮、负压暗）；`light(pts, amount, soft)` 软边光块（地上的阳光、窗档影子）；`pattern(pts, draw_fn, dark)` 小花样（壁纸、波点；dark < 0 提亮）
- 房间：`wall(y1)` 渐变墙纸 + 竖条 + 小枝花 + 踢脚板；`floor(y0, board, vp)` 透视地板、接缝、木纹；`window(x0, y0, x1, y1, bars='sash'|'cross', horizon, valley)` 窗外的早晨（天空、云、远山、树、近山；近山和窗档进 'window' clip），返回几何；`curtain(...)`、`valance(...)` 窗帘和帘头（也从 clip 里减掉）；`nightstand(x0, x1, top, bottom, floor_y)` 返回桌面 y；`bed(x0, x1, head_top, sheet_y, front_y, floor_y)` 从床尾看的床（拱形床头、球形柱头、绗缝被、垂下的被边；被子进 'bed' clip）；`rug(cx, cy, rx, ry)` 编织地毯；`sampler(x0, y0, x1, y1, lines)` 挂墙的格言框
- clip：`clip(name, add, sub, full)` 建遮罩；角色方法的 `clip=`，或 `using(name)` … `using(None)` 把之后的赛璐璐都放进某个 clip
- 赛璐璐基本件：`shape(pts, fill, ow)`（墨线只在填色外侧；fill=None 只描线）；`union(subs, fill, ow)` 几块拼成一块、中间不出线（`('poly', pts)` / `('cap', pts, r)`）；`hose(pts, width)` 等粗、没有肘和膝的橡皮管；`stroke(pts, width, taper)`；`text(s, x, y, size, fill, ow, rot)`；`shadow(cx, cy, rx, ry, amount)` 角色脚下的灰影；`guide(pts)` 只出现在铅笔稿里的结构线
- 橡皮管词汇：`hose_path(p0, p1, bend, bend2)` C 形 / S 形四肢；`glove(x, y, angle, size, pose='open'|'point'|'fist'|'palm', flip)` 四指白手套（三道缝线、外翻袖口；(x, y) 是手腕，angle 是手指方向）；`shoe(x, y, size, facing, tilt)` 大圆鞋（白高光、灰鞋底）；`pie_eye(cx, cy, rx, ry, look, wedge, lid)` 白眼眶 + 切掉一角的黑瞳，lid 是半闭的眼皮；`grin(F, x0, x1, y_top, y_bot)` 张大的笑嘴带舌头；`star()`；`Frame(x, y, s, rot, flip)` 局部坐标
- 角色：`alarm_clock(cx, cy, r, tilt, look, time=(7, 0), arms=[...], legs=[...])` 双铃闹钟（黑表壳、白表盘上的脸、指针、两只铃和甩动的铃锤；arms / legs 给手腕 / 脚踝位置和 bend、pose、facing、tilt），返回局部 Frame，`rh.bells` 是两只铃的位置；`sun(cx, cy, r, arms, ray_style='wavy'|'spiky', clip)` 半睁眼打哈欠、伸懒腰的太阳；`pillow(cx, cy, w, h, arm, clip)` 戴条纹睡帽打呼、举起手套的枕头；`slipper(x, y, size, facing, tilt)` 跳舞的拖鞋
- 特效：`vibration(cx, cy, r, a0, a1, n)` 同心震动弧；`speed_lines([pts])`；`lettering(s, path, size)` 沿曲线蹦跳的粗衬线字（白字黑边，单双号反向倾斜、上下错开）；`zzz(x, y, size)`；`slab_font(size)` 找 Superclarendon / Rockwell 这类粗衬线字体（可用 `INKPAINT_FONT_SLAB` 指定）
- 顺序与快照：背景 → `stage('layout', view='layout')`（纸上的背景铅笔稿）→ `stage('background', view='background')` → 画角色（此时是铅笔稿）→ `stage('pencil')` → `ink()` → `stage('ink')` → `paint()` → `stage('paint')` → 特效 → `film(grain, soft, halation, tone='silver'|'sepia'|'neutral', vignette, weave, gate)` → `age(scratches, dust, specks, fibres, hair, stains, flicker)` → `save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**黑白麻胶版画 `Linocut`**：
- 思路：减法。整块麻胶版滚上墨，印出来是一整块黑；画里所有白的地方都是刻刀挖掉的。每块版是一张 ss 倍分辨率的浮雕图（255 = 没刻、吃墨，0 = 刻掉了）：黑版一开始是满的，套色版一开始是清空的，只「留下」要印颜色的形状；黑版外圈一道边永远不刻，印出来就是手刻版那圈微微起伏的黑框。每一刀都是一个两头收尖、边缘带碎口的多边形；明暗不靠灰色，靠刀痕的疏密和粗细（黑里刻白线，或白里留黑线）。印的时候按真的手拓算：墨辊滚出的墨层不匀、带几道停辊横纹，木蘑菇压出一圈圈压力；墨层 × 压力压不过纸纹的地方露白（大片实地「发花」），墨被挤到形状边缘，所以边缘始终是实的；先印套色、再叠黑版，两版错开几像素；纸被压进版里，刻掉的地方和页边微微鼓起
- 构造：`Linocut(W, H, block=(x0, y0, x1, y1), seed, paper, ink, ss=2, rim=7)`；`colour_block(颜色, offset=(dx, dy), mottle)` 加一块套色版（颜色写印在这张纸上的样子），返回 `Block`，各工具用 `on=` 指定刻哪块版（默认黑版）
- 遮罩：`poly(pts, smooth)`、`disc(cx, cy, r)`、`rect()` 给 1× 浮点遮罩（可以用 numpy 加减）；区域参数也可以直接给多边形点列；`mask_of(polys)` 把一组刀痕多边形变成遮罩
- 一刀：`stroke(pts, width, tool, taper, end)` 返回刀痕多边形；`gouge(pts, width, tool='v'|'u'|'knife'|'brush', cut=True, on, region)`：v 是 V 口刀（尖入、渐宽、提刀收尖），u 是 U 口刀（圆头、碎尾），knife 是等宽刻刀，brush 的宽度从 width 线性变到 end（树枝、留下的线）；`cut=False` 是留下一条不刻（白地里的黑线）；`jab(x, y, size)` U 刀戳一下
- 成片：`clear(形状, chatter, angle)` 用大 U 刀清掉一片，留下顺下刀方向的残刀印（靠边更多）；`leave(形状)` 留住一片；`hatch(region, angle, spacing, width, dash, gap, tool, cut, density, bend)` 一排排平行刀痕：density(x, y) 决定一刀留不留、多粗（这就是明暗），bend(x, y) 把行推弯（漂雪、等高线、衣褶）；`flow(region, field, n, length, width)` 沿方向场 field(x, y)→角度 的长刀痕（风、水、毛）；`speckle(region, n, size, stars)` 落雪：U 刀戳点加少量三刀交叉的六角雪花，只刻在还有墨的地方；`rings(cx, cy, radii, width, arc, gap, cut, squash)` 断续同心环（月晕、年轮）；`outline(形状, width, cut=True)` 在形状外刻一圈白边，黑东西才能从黑底里分出来（cut=False 是留一圈黑边，白东西穿过白底）
- 物件：`moon(cx, cy, r, rings)`；`pine(x, y, h, w, tiers, snow, halo, nicks, region)` 积雪云杉；`bare_tree(x, y, h, lean, spread, width, depth, halo, snow, seed)` 枯树（返回遮罩）；`cottage(x, base, fw, wall, roof, side, rise, windows, side_windows, door=(u, w, h, 开着), chimney=(位置, 宽, 高), lit=套色版, attic)` 积雪木屋，返回 `{'apex', 'windows', 'door', 'chimney'}`；`smoke(x, y, rise, drift, width)` 一串卷着飘的烟团；`footprints(path, step, size, side, start, stop, paws)` 脚印 / 爪印
- 印：`pull(blocks)` 印出 PIL 图；`sign(edition, title, name, y)` 页边铅笔：左版次、中题名、右签名；`chop(x, y, size)` 不上墨的钢印
- `stage(name, blocks=None)` 快照（`blocks=[]` 是白纸，`blocks=[L.key]` 只印黑版）；`save(path, stages_dir)` 默认 quality 88、4:4:4 色度
- 顺序：和画家算法一样，后刻的盖前面：先清大块白（山、雪野、月亮）→ 天空刀痕 → 远景 → 房子 → 雪地 → 近景人物 → 落雪 → 套色版 → 铅笔

**VHS 家庭录像 `VHSCamcorder`**：
- 思路：不是在画面上盖一层「复古滤镜」（Synthwave 的录像带质感就是这么做的），而是照家庭录像真实的三步出图，每种瑕疵都来自其中一步：
  1. 房间：颜色画进反照率缓冲，灯罩、烛焰、窗外天空画进自发光缓冲；出图时反照率乘上房间的光（暖色环境光 + 点光源 + 画上去的光斑）再加自发光；镜头前太近的东西画在离焦图层上
  2. 摄像机：手持微倾和变焦、白平衡停在「室外」拍钨丝灯、软膝高光、泛光、CCD 竖向拖影、拖尾、镜头柔化、暗角、暗处增益噪声；摄像机的字符发生器在这里把 OSD 混进信号，所以 OSD 也跟着上带、跟着糊
  3. 录像带：降到 480 行 × 760 采样点，分成亮度 Y 和色度 I/Q；亮度低通再加回放锐化（一边亮一边暗的光晕），色度约 6 倍宽的低通、隔行平均、往右延迟（红色往右渗）；回放再加条状亮度噪声、横向色度噪声、逐行时基抖动、顶部偏摆、跟踪噪带、磁头切换噪声、掉磁白点、抬高的黑电平，最后放大回输出尺寸
- 构造：`VHSCamcorder(W, H, seed, lines=480, samples=760, ss=2, keep_stages=True)`；`keep_stages=False` 时 `stage()` 不出快照（快）
- 形状 → 遮罩：`poly(pts)`、`shape(pts)` 闭合样条、`rect(x0, y0, x1, y1, r)`、`ellipse(cx, cy, rx, ry, rot)`、`line(pts, width)`、`text(s, x, y, size, style, anchor, rot)`；颜色场 `lin(p0, c0, p1, c1)`、`rad(cx, cy, rx, ry, c0, c1)`
- 上色与光：
  - `paint(mask, colour, alpha, form, form_r, light)`：colour 可以是颜色场；form > 0 把形状打圆（边缘暗、迎光一侧亮）
  - `emit(mask, colour, level)` 自发光（不受房间光影响）；`glow(mask, colour, level)` 落在表面上的光斑（乘反照率）；`shadow(mask, strength, soft, dx, dy)`；`rim(mask, toward, colour, level, width)` 朝光源一侧的轮廓光
  - `ambient(colour, level)`、`light(x, y, radius, colour, power)` 点光源，1 / (1 + (d/r)²) 衰减
  - `with v.layer(defocus=4.5): ...` 里画的东西整体虚焦（离镜头太近的前景）
- 70 年代客厅：`wallpaper(mask, tile, contrast)` 圆环墙纸带纸幅接缝、`paneling(mask, grooves)` 胡桃木护墙板、`ceiling()` 喷涂天花板、`shag()` 长毛地毯、`window(x0, y0, x1, y1)` 黄昏的窗（剪影、对面一扇亮窗）、`rod()` + `curtain(x0, x1, y0, y1, folds)` 花朵窗帘、`console_tv()` 落地电视柜、`rabbit_ears()`、`floor_lamp(x, y_floor, y_shade)`（自带灯光和墙上的光斑）、`sofa(x0, x1, y_back, y_seat, y_front, y_floor, colour)`
- 派对：`streamer(p0, p1, sag, colour, twists)` 扭转的皱纹纸彩带、`pennants(p0, p1, sag, letters, colours, size)` 字母三角旗（浅色旗自动换深色字）、`balloon(x, y, r, colour, string_to)`、`coffee_table(quad, thick, legs, gloss)`、`cake(cx, cy, rx, ry, h, candles, sprinkles, lean)`（candles = [(角度, 颜色, 'lit' 或 0–1 烟量)]，返回火苗位置，每个放一盏 `light`）、`smoke()`、`present()`、`cup()`、`plates()`、`blower()`、`confetti()`、`teddy()`；`child_back(hx, hy, s, lean, glow_from)` 背影的孩子（尖帽、发旋、耳朵、肘），画在离焦图层里
- 三步开关（调用之后的每个阶段都生效）：
  - `camera(tilt, zoom, white_balance, exposure, knee, bloom, smear, lag, soft, vignette, gain_noise)`：white_balance 是 RGB 增益，默认 (1.08, 0.94, 0.70) 即「室外档拍钨丝灯」；smear 只对远超满阱的点光源起作用；lag = (dx, dy, 强度) 是高光身后的拖尾
  - `record(luma, chroma, chroma_v, delay, sharpen, sharp_r, saturation)`：亮度 / 色度带宽（采样点 σ）、色度延迟、锐化光晕
  - `wear(noise, chroma_noise, jitter, flagging, tracking=(中心比例, 高度比例), head_switch, dropouts, black, lines)`
- OSD（点阵字、黑边，混进信号上带）：`rec(x, y)` 红点 + REC、`battery(x, y, level, of)`、`counter(s, x, y)`、`datestamp(时间, 日期, x, y)`、`zoom_bar(x, y, pos, width)`、`osd_text(s, x, y, px, colour, anchor)`；字库只有大写字母、数字和 `: . - / >`
- `stage(name)` 存一张当前状态的完整渲染；`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**扁平矢量 `FlatVector`**：
- 思路：矢量软件的画板，每样东西是一层。形状边缘干净、没有描边；7 种平涂色，其余颜色都是它们的 `tone` / `mix`；整幅只有一个光源，每样东西分亮面和暗面；每抬起一层，先往已有画面投一道短而柔的夜蓝色阴影（「矢量纸片」的层次），最后加极淡的纤维纹和固定细颗粒（分阶段快照的颗粒一样，动图差分小）
- 构造：`FlatVector(W, H, seed, light=(-0.7, -0.7))`，light 是指向光源的屏幕方向
- 形状：都返回 `Mask`，可以 `|` 并、`&` 交、`-` 减，`moved(dx, dy)`、`scaled(k)`，只算包围盒。有 `circle`、`ellipse(cx, cy, rx, ry, rot)`、`rect(x0, y0, x1, y1, round)`、`poly(pts, round=半径或每角半径)`、`capsule(p0, p1, r0, r1)`、`star(cx, cy, r_out, r_in, n)`、`teardrop(x, bottom, r, h, lean)` 火焰 / 水滴形、`profile(pts, bottom)`（样条顶边往下填满的地块）；`half(m, p0, p1)` 取有向直线右侧的部分
- 上色：
  - `backdrop(颜色)`；
  - `fill(m, 颜色, alpha, lift, texture, shadow)`：lift > 0 时先投层间阴影（下移 0.45 × lift，模糊 0.9 × lift，乘夜蓝紫色调），再铺色；
  - `face(m, p0, p1, 颜色)`：把直线右侧改成暗面色；
  - `glow(cx, cy, rx, ry, 颜色, rings, alpha)`：一圈圈平涂半透明光环；
  - `drop(m, lift, strength)`：只投影不铺色；
  - `tone(c, k)`：k < 0 往夜蓝墨色调，k > 0 往奶油色调；`mix(a, b, t)`
- 天空：`moon(cx, cy, r, rays, ray_colour, ray_len, halo, craters)`，月亮外一圈长短交替的三角光芒，加两圈阶梯光晕；`stars(n, box, avoid=[(x, y, r)])`；`sparkle(x, y, r)` 四角星；`shooting_star(head, tail, r)`；`cloud(cx, cy, w, colour, belly)` 平底云
- 地形：
  - `mountain(peak, left, right, 颜色, snow, ridge, lift, shade)`：折线山脊分亮面和暗面，锯齿雪顶；返回 `dict(body, shade, snow)`；
  - `land(pts, 颜色, lift, shadow)`：一层山丘或沙地；
  - `pine(x, base, h, 颜色, tiers, width)`：层层三角，从中间劈成亮暗两半；`round_tree(x, base, r, 颜色, fruit)`；
  - `dashes(box, colours, n, length, thick, horizon)`：沙地上的深浅短横，越近越长；`pebble(x, y, r, 颜色)`、`tuft(x, y, h)`
- 故事道具：
  - `trail(pts, 颜色, width, dash, gap)`：越往下越粗的虚线小路，返回遮罩，可以 `& peak['snow']` 换色；
  - `flag(x, y, h)`、`tent(x, base, w, h, 颜色, depth, inside)`：亮面正面、暗面侧顶、透光的门、掀开的门帘、拉绳和地钉；
  - `campfire(x, base, s)`；`hiker(x, base, h, facing, lamp)`：没有五官的小剪影，带背包、登山杖、头灯光束
- 色板常量 `NIGHT PLUM BERRY EMBER SAND PINE CREAM`；`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

**绘本角色动画 `Storybook`**：
- 思路：动画师的一个镜头，不是一张画。一切都是时间 t（秒）的函数：同一个场景既能逐帧出真动画（`frame(t)`、`gif()`），也能出一张「旅程总图」（`journey()`：世界全部画完，角色在关键姿态上多次曝光，配铅笔运动弧）。场景里每样东西都预先画进自己的裁切层，同时记一张「揭示图」：每个像素在这一层自己的画出过程里第几时刻被笔刷/钢笔碰到——墨线按弧长揭示（笔在走），水彩从一点晕开或横扫过去（带一道略深的湿边），小物件放大弹出（0 → 1.1 → 1）。层的进度来自时间窗 `when=(t0, t1)`，或者 `follow=lead`：画到角色已到达的最远 x 前方 lead 像素，所以山坡、花、河岸正好在角色经过时画出来。角色每帧用隐式曲面在自己的局部坐标里现画：整体做保体积的仿射挤压拉伸（沿轴 k、横向 1/√k）再滚转，`rest()` 让最低点正好落在地面上，光照固定在世界里（滚动时高光不跟着转），离地越高接触阴影越小越淡
- 构造：`Storybook(W, H, seed, actor_size=44)`：所有坐标都按 1920×1080 设计坐标给，输出任意尺寸（720×405 动图和 1920×1080 总图就是同一场景的两个实例）
- 编排：`act(t0, t1, fn)`，fn(u, t) → 姿态 dict 或 None（藏起来）。姿态键：`x, y`（坚果中心）、`rot`（度，逆时针）、`k`（>1 拉伸、<1 压扁）、`axis`（拉伸方向，度）、`scale`、`eyes`（0 闭 .. 1 睁）、`lid`（'blink' / 'sleep' / 'happy' 闭眼形状）、`look=(dx, dy)`、`brow`（'determined' / 'up' / 'worried'）、`mouth`（'smile' / 'grin' / 'o' / 'flat'）、`blush`、`shadow=(gx, gy, 宽, 浓度)`、`clip`（地面 y，以下不画：钻土）、`only='cap'`（只画帽子：树苗顶上）、`lead=False`（不推动 follow 层）、`speed=False` / `speed_min`（自动速度线）。辅助：`rest(gx, gy, rot, k, axis, normal)` 让角色立在地面点上；`anchor(px, py, local, rot, scale)` 让局部点（默认果柄尖）落在某点上（挂在枝头）；`ease(u, kind)`（in / out / inout / sine / back 回弹 / elastic）、`spring(u, cycles, damp)` 衰减抖动、`arc(p0, p1, 高, u)` 抛物线跳跃；`pose(t)`、`lead_x(t)`、`when_at(x, lead, dur)`（角色到达 x 时开始的时间窗）
- 场景：`paper()`；`wash(pts, 颜色, reveal='x'|'-x'|'radial'|'pop', origin, dashes)`；`ink(pts, 宽)` / `inks(paths)` 藏青细墨线（压力收笔、轻微手抖）；`ground(pts, ticks=True)` 地平线加「v」字小草；`land(top, 颜色, left_edge, right_edge, dashes)` 山坡（顶线样条、毛糙的崖边、蜡笔短线）；`hill(top, 颜色, outline)` 远山（只在顶上一条细灰线）；`tree(x, base, top, canopy, branch)` 秋天的橡树；`sun(cx, cy, r)`（圆盘弹出，光芒一根根画）；`cloud(cx, cy, w)` 厚涂白云带淡紫投影；`water(x0, x1, y)` 小河；`shape(polys, 填色, 描边, pop)` 带细墨边的小物件；`flower(x, y, h, kind)`、`tuft`、`cattail`、`leaf_on_ground`、`mound`（土堆，画在角色上面，能把它埋起来）。通用计时参数：`when`、`follow`、`pre=(t0, t1, upto)`（follow 层左边一段先按时间画）、`xa / xb`（follow 的起止 x）、`z`
- 道具：`sprite(polys, 填色, veins=)` 预画一个小道具；`prop(sprite, t0, t1, fn)`，fn → dict(x, y, rot, sx, sy, alpha, ghost)，每帧仿射贴上（飘落的橡叶用 sx 模拟翻面，落水后 sy=0.5 平躺）；`oak_leaf(长, 宽, lobes, base, angle)` 模块函数给橡叶轮廓
- 特效：`fx(kind, t0, x, y, ...)`：'impact' 冲击线、'dust' 白色尘团、'ripple' 水波、'specks' 土粒、'sparkle' 四角星、'confetti' 彩纸屑；速度线按速度自动加
- 手写字：`write(text, x, y, size, when, underline=((x0, x1), y), weight)`：文字遮罩 Zhang–Suen 细化成单像素骨架，像手一样走骨架（去斜体后最靠左的端点起笔、路口尽量直走、走到头抬笔跳回），每个墨像素取最近骨架点的时刻
- 输出：`frame(t)`；`gif(path, fps=15, t_end, hold)`：逐帧渲染（一次只留一帧浮点），共用一张加权调色板 + 固定 4×4 Bayer，没变的像素写成品红透明索引；`journey(times, t_world, arc, labels, prop_arcs, world_fx, final, props)` 旅程总图；`stage(name, t)` 存某时刻的关键帧，`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度
- 色板常量 `PAPER INK PENCIL GRASS MINT LAVENDER SUN WATER NUT CAP CONFETTI`


**圆珠笔涂鸦 `Ballpoint`**：
- 思路：圆珠笔墨是油性墨膏，靠滚珠压到纸上；颜色按光密度（比尔定律）叠加，描两遍、交叉、墨团都会更深更饱和（蓝色叠到深蓝紫，不会变成死黑）。每一笔：起笔头几像素滚珠是干的（细、淡、只挂在纸纹峰上）→ 压力 ±12% 漂移、线宽随之略变、手抖 → 偶尔断墨 2–9 px（墨断了，压痕还在）→ 停笔、急转弯、有时起笔处掉一个墨团 → 抬笔甩出 90–160° 的小钩。每一笔都在纸上压出凹槽，左上侧光下槽的左上壁暗、右下壁亮。彩铅是蜡，只挂在碰到的纸纹上：轻压颗粒发白，重压填进谷里；一块一块地斜向快速排线，出界、换方向，大面积浅、小面积重
- 构造：`Ballpoint(W, H, seed, ss=2, pen_width=2.5)`；`paper(tone, tooth=0.75, fibres=260, mottle, cockle=1.0, folds=[((x0, y0), (x1, y1))], vignette=0.09)` 灰米色复印纸：细纸纹、稀疏纤维、斑驳、低起伏和折痕（按左上光打光）、拍照的四角暗角
- 圆珠笔：`line(pts, pen='blue'|'red'|'black'|None, pressure, width, closed, smooth, wobble, bow, hook, gloop, skip, twice, start, clip, groove)`；`bow` 是徒手直线的侧弯（约 0.003–0.006 倍长度），`hook` / `gloop` / `skip` 是收笔小钩、墨团、断墨的几率，`twice` 是再描一遍（偏 0.6–1.6 px、只描一部分）的几率，`pen=None` 只压槽不出墨；`lines(paths, …)` 一批短笔画共用一次栅格化；`emboss(pts)` 无墨压痕
- 小件：`dot(x, y, r, pen)` 转一小圈压出的实心点；`eye(cx, cy, rx, ry, pen, look, shine)` 由外往里转圈涂实、留一个圆高光的眼睛；`face(cx, cy, size, mood='smile'|'grin'|'oh'|'dizzy'|'sleep'|'worry', pen, blush, look, rot)`；`dashes(pts, pen, dash, gap, pressure, smooth, clip)` 虚线（返回重采样后的路径，好接箭头）；`arrow(tip, direction, size, pen)`；`ring(cx, cy, rx, ry, pen, turns, rot)` 不闭合、越画越往外的随手圈
- 彩铅：`pencil(mask, colour, angle, pressure, spacing, length=(40, 90), overshoot, width=2.9, jitter, bow, cross, clip, groove)` 斜向排线（`length` 是一段手腕笔画的长度，接缝逐行错开；`overshoot` 出界像素；`cross` 再叠一层角度）；`pencil_line(pts, colour, pressure, width)` 单根彩铅线；颜色用 `PENCILS` 里的名字（leaf green lime mint teal sky blue violet lilac pink rose red orange peach yellow ochre brown tan grey cream）或 '#rrggbb'
- 圆珠笔排线：`pen_hatch(mask, pen, angle, spacing, pressure, length, overshoot, zigzag=0.85, cross, clip)` 来回不抬笔的之字排线，转折处带墨团（阴影、暗面、深色棋子）
- 手写：`write(s, x, y, size, pen, pressure, slant=7, spacing=1.04, jitter, anchor='l'|'m'|'r', rot, width, blind, hook, gloop)`，y 是基线，返回写出来的 (x0, y0, x1, y1)；字形取自细手写字体的骨架（Zhang-Suen 细化后描成笔路径，按字缓存），每个字母单独缩放、倾斜、上下浮动，有起笔、墨团、小钩；中文用细黑体骨架；`blind=True` 是上一页透过来的无墨压痕字；`strike(box, pen, passes)` 来回划掉一个词；`underline(x0, x1, y, pen, wavy)`
- 遮罩和点：`poly(pts)`、`ellipse(cx, cy, rx, ry, rot)`、`band(pts, width)`、`tube(pts, w0, w1)` 由粗到细的身体（蛇、尾巴），`Ballpoint.tube_sides(pts, w0, w1)` 它的左右两条边（一笔描下去绕过尾尖再描回来）；`circle_pts`、`star_pts`、`cloud_pts(cx, cy, w, h, bumps, seed, flat)`、`spiral_pts(cx, cy, r, turns, a0)`、`heart_pts`、`Ballpoint.resample(pts, step)`
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4；常量 `PENS PENCILS PAPER`；字体可用 `INKPAINT_FONT_BALLPOINT` / `INKPAINT_FONT_BALLPOINT_CJK` 指定（默认 macOS Noteworthy Light / 黑体-简 细体，Linux Kalam / Caveat / Noto Sans CJK，Windows Segoe Print / 微软雅黑）

**描图纸叠层 `Overlay`**：
- 思路：透光台上的分色叠片。灯箱从下面打暖白光，画面就是一路透过率相乘：底图（胶版纸）印黑线和灰调，上面每张描图纸 / 胶片只印一种油墨。油墨按网点覆盖率 c 算透过率（c ≤ 1 是平网 1 − c(1 − ink)，c > 1 是叠印加深 ink^(c−1)）；不同叠片之间正片叠底，蓝叠黄成绿、品红叠黄成红、蓝叠品红成紫；同一块版自己不叠加（取最大覆盖率）。每张纸有自己的纸色、只有背光下才看得见的云状纤维（formation）、零星纤维丝、裁切边的一道细暗线和打孔；描图纸平放时也让下面的暗部略微发灰（frost）。抬起的纸略放大、往右下投一片宽而软的暖色阴影（透过纸也看得见），而且它是离开画面的漫射片，会把下面的一切模糊掉；放下后清晰，阴影收成一条贴边细线，套准十字落在底图的十字上
- 构造：`Overlay(W, H, seed, keep_stages=True)`；`desk(colour)`、`lightbox(x0, y0, x1, y1, radius, bezel)`、`lamp(level)`（0 关灯：灰色乳白亚克力；1 开灯：暖白，中间偏左最亮；中间值又暗又偏暖）；`peg_bar(x0, x1, y0, y1, pegs=[('round', x, y, r), ('slot', x, y, w, h)])` 定位钉条（不透明的钢条，画在所有纸下面，纸上的孔里露出钉子和一圈透光缝）
- 纸：`sheet(x, y, w, h, kind='base'|'tracing'|'drafting'|'film', ink, tint, fibre, curl=('br', 70), edge)` 返回 `Sheet`。坐标一律是**纸放下时的画布坐标**，所以几张叠片用同一组点画，自动套准。`place(sheet, lift, dx, dy, rot)` 显示、抬起（lift 0–1，偏 dx / dy 像素、转 rot 度）或放下（全 0）；第一次 `place` 决定叠放顺序；`remove(sheet)`；`tape(cx, cy, w, h, rot)` 撕口的皱纹绘图胶带，压在最上面、半透光
- 在纸上印：`fill(遮罩或多边形, cover, ink)`；`line(pts, width, cover, ink, closed, smooth, dash=(实, 虚))`、`lines(paths, …)` 一批线一次栅格化；`dots`、`circle(cx, cy, r, width=None)`、`hatch(mask, spacing, angle)`、`stipple(mask, n, r)`；`text(s, x, y, size, font_kind, cover, ink, anchor, spacing, rot, halo, knock)`：halo 先清掉字周围的墨，knock 把字从墨里反白掏出（实心圆里的站点编号）；`knock(mask)`、`cross(x, y)` 套准十字、`arrow(tip, direction, size)`、`punch(x, y, r)` / `punch_slot(x, y, w, h)` 打孔
- 遮罩（画布大小）：`poly(pts, smooth)`、`circle`、`ellipse`、`rrect`、`band(pts, width)`；`edge(mask, width)` 轮廓线、`offset(mask, d)` 外扩 / 内缩、`contour(mask, d, width)` 离边 d 像素的一圈线（海岸水线）、`Overlay.inset(凸多边形, d)` 街区从街道往里缩、`circle_pts`
- 字体 `font(kind, size)`：map / map_bold / map_heavy / map_italic / map_light（Gill Sans 一族）、title（Avenir Next Heavy）、label、cjk / cjk_light（黑体），也认 core 的样式名；可用 `INKPAINT_FONT_OVERLAY_<KIND>` 指定
- 常量 `INKS`（black blue yellow magenta cyan orange green red）、`PAPERS`；`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

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

**岩画（凿刻砂岩）**

| 问题 | 改法 |
|---|---|
| 沙漠漆像木纹、像一整幅竖条窗帘 | 不用全幅竖条噪声；漆膜近乎均匀（0.86 ± 0.09），流痕是一条条独立的对象：多从顶部起、往下变窄变淡、略左右漂移，边缘 ±2.5 px |
| 流痕像条形码（硬顶的黑色矩形） | 流痕顶端 50 px 渐入、长度 30%–100% 段渐隐，不从硬边矩形源往下涂 |
| 流痕糊成一团团烟，挂在羊身下面像投影 | 不要整体 bicubic 放大成软团；只在横向留 ±2.5 px 的过渡，纵向才平滑 |
| 流痕像一根根火柴棍 / 芦苇帘 | 宽度取对数正态（中位约 18 px）、约 110 条、只把漆加厚 0.2、锰色 0.6；再加约 26 条更宽的浅色流痕（漆被水流冲薄） |
| 薄漆的「窗口」成了迷彩斑块 | 不用块状窗口，浅色也做成竖向流痕 |
| 凿点太稀，图形像撒了一层粉笔末 | 凹坑数 ≈ 3.4 × 图形面积 / 单坑面积；坑深相加后饱和（dmax ≈ 2.9 px），内部打满只留小暗缝，轮廓在一个坑的尺度上毛糙 |
| 羊身细长像腊肠，整群首尾相连成一条带 | 身体加深（-0.20 到 0.15 个身长）、颈粗；大羊一排、母羊小羊一排错开，彼此留空 |
| 剥落像贴上去的光滑椭圆，四周一圈黑 | 轮廓拆成 14–40 px 的小段、每段向内弯成小贝壳弧；AO 减弱（深度 2.4 / 7 / 22）；疤面颗粒减半、鲜橙色带铁质色带，唇口一圈浅色风化皮 |
| 地衣像绿色颜料点、像一枚枚硬币 | 低饱和橄榄色，椭圆加不规则叶状边、龟裂纹、小黑子实体、周围卫星小点，alpha 约 0.7 |
| 太阳螺旋中心成了「f」，光芒离螺旋太远像飘着 | 螺旋从 1.4 rad、10% 半径起步，中心只点一个小点；光芒从最外圈外 1.7 倍线宽处开始 |
| 蹄印像等号或乱点 | 两瓣从蹄跟到蹄尖向中线收拢成心形（尺寸 ≥ 30 px，凿点 size 0.66）；第一枚离羊蹄远一点 |
| 小孩手印糊成一团 | 手印 ≥ 约 95 px，凿点 size 0.62、density 1.2，手指才分得开 |
| 光秃砂岩像一块木板（层理像木纹、小凹坑像钉眼） | 层理振幅减半且时有时无，石色只随层理变 1–3%；凹坑改成 7–26 px 的浅碟 |
| 画面顶边、左边多出一条黑带 | 投影步进前用边缘复制把高度图 pad 一圈（越界补 0 会被当成一堵墙投下影子） |
| 岩檐只像一道裂缝 | 台阶 34 px 才有一条看得见的檐下投影；檐口折线 + 轻微倒圆 |
| 新旧凿痕只有「全新」和「鬼影」两档 | 加中间档 age 0.3（新月、计日刻痕、掷矛手）：0 新凿、0.3 几百年、0.6–0.7 几乎被漆盖回 |
| 动图里橄榄绿地衣被量化成灰 | 给偏绿像素单独留 6 个调色板位，「和上一帧相同」的占位色用品红 |

**古埃及墓室壁画**

| 问题 | 改法 |
|---|---|
| 弯腰的人还是正面宽肩，后肩翘到头顶上，横过胸前的手臂像一条绶带 | 按前倾角把肩宽往侧面收（前倾 32° 时只剩约 15%），两只手臂都从胸前出发；坐姿直接给 `turn` |
| 蹲坐的书吏把脚转 180° 后脚底朝天，两臂缠在一起 | 压在身下的脚左右镜像（`mb=True`，脚尖朝后），肘部 IK 一律朝下弯，`turn=0.45` 收窄躯干 |
| 灰泥脱落像贴上去的褐色石片，带一圈发亮的白边 | 做成真的高度图：洞深 8 px，低角度光沿高度图投影（左上内壁一道影），洞底近壁处加环境遮蔽；石膏白边只留 2–4 px 且断断续续，洞口四周的颜料按台阶剥落 |
| 底色把人物里的红稿整个盖掉，剥落处只露出黄底 | 底色绕开要上色的形状刷（`ground(around=True)`）：动画里红稿一直留到上色那一步；人物上的剥落露出灰泥上的红格和红稿（`age(zones=...)` 可以指定几处） |
| 干活的人都戴宽项圈，分不出主仆 | 只有总管和书吏戴项圈；劳工赤膊，有的剃短发（`wig='cap'`，露耳朵） |
| 象形数字 ∩‖ 读成「ΛI」：一竖藏在 ∩ 的腿后面 | 每个 ∩ 之后让 0.78 em，竖笔间距 0.3 em，字号 46 px 以上 |
| 粮袋正中那道褶像一张笑脸 | 褶线挪到袋子一侧，竖着走 |
| 无花果树冠是一格格圆点，像波点布 | 尖叶按行排、隔行错开、下一行压住上一行（像鳞片），深浅绿隔行；水囊挂在一根截断的枝上 |
| 锄地的人像在推棍子，量斗像一本书 | 锄头画成倒 V：双手握柄，柄顶绑宽木刃斜插进土，中间一道绳；量斗是上宽下窄的木桶，口上堆着粮，倾斜着倒出一股粮粒 |
| 扛东西的人手捂额头，袋子盖住了脸 | 后手举起扶住，货物压在后肩、在头后面（z 夹在躯干和举起的手臂之间）；部件细节的 z 偏移只给 +0.002，否则筐的编织纹会跳到手臂上面 |
| 埃及蓝像一层蠕虫状噪点 | 蓝、绿两色改用稀疏的亮晶粒加暗颗粒（`T_cryst`），通用颗粒压到 0.05 |
| 底色的斜向刷痕整面平铺，像雨丝 | 两个方向、按大块噪声时有时无，幅度 0.012–0.015 |
| 潮痕像一条钢笔线横穿人物 | 宽约 0.012 H 的柔和带，上沿稍清楚，往下逐渐泛褐 |
| 动图 3.7 MB（满墙颗粒让每次叠化都改掉一半像素） | 关键帧先做 1 px 高斯平滑；量化时新颜色和上一帧已显示的颜色相差不超过 10 级就沿用上一帧的索引（透明差分照样有效，自检仍逐帧比对）→ 1.85 MB |

**罗马马赛克**

| 问题 | 改法 |
|---|---|
| 石子像一个个鼓起的枕头，整幅像碎石路 | 地面是打磨过的：石面只高 1.5–2 px、倒角半径约 1.7 px，漫反射 0.45 + 0.55；切石抖动 4.5%、缺角 20%、转角 ±1.6° |
| 灰色的鱼身里混进淡蓝、粉色石子 | 取石在「亮度 + 红绿 + 黄蓝」对立色空间里比，色度权重 2.6，抖动主要加在亮度上（已处理） |
| 轮廓那一排又宽又长（约 13 px 深而不是 8 px），第二排轮廓铺不出来 | 判断「里面还有没有下一排」用的脊线最大值滤波半径小于一排间距，每排都以为自己是最后一排、往里加宽：半径取 2 × 排距（已修） |
| 波浪纹边框整圈不见了，只剩白排 | 局部坐标的周期被带高乘了两次，波浪画到几千像素外：周期 / (1.5 × 带高) 再乘带高 |
| 边框的浪是一条条细 S 线，像卷草不像浪 | 浪身是从黑框边长出来的实心块，浪尖沿一条渐细的粗线卷回去，中间留一个白「眼」 |
| 收起挂在帆桁上的帆像一把伞 | 改成从帆桁垂下、向一侧鼓起的方帆，竖向缩帆索用浅色石子 |
| 小海鸥外面套两圈背景光环，像装在泡泡里 | 所有东西先一圈光环；第二圈只给大图形（船、灯塔、铭牌、网、章鱼），量距离时把第一圈也算进去 |
| 网里的鱼被网线切成碎块，看不出是鱼 | 网里的鱼先铺（眼、鳃线、轮廓、填满），网线后铺，碰到鱼自动断开 |
| 被偷的那条鱼太小、贴着网，看不出章鱼在偷 | 鱼放大到约 150 px、拖到网外，章鱼最长的那条腕绕住鱼尾 |
| 天空里的脱落像一个灰色加号 | 脱落放在边框和海里、靠着裂缝；旧灰浆床压暗偏暖，留下石子方坑 |
| 铭牌燕尾耳尖上散着红色碎屑，小字像虚线 | 耳朵填完只补大于半块的洞（`tuck(small=0.55)`）；字的石子边长取字高 / 5.6，不小于 5.6 px |
| 动图 3.2 MB：最后一次叠化整幅都在变 | 阶段快照和收尾帧都按 `stage_ss` 渲染（分辨率一致）；积灰只成片出现、不整幅压暗；和屏上颜色差 ≤ 10/255 的像素按「没变」透明 → 1.57 MB |
| 动图里金色火焰、光芒变成粉橙色 | 调色板分两份：饱和像素按 12 个色相区等量抽样，单独中值切分 48 色，其余 207 色 |
| 峰值内存 2.6 GB | 2× 渲染按 96 行条带做，起稿、噪声、裂缝图留在 1× 逐条放大；paint / shade / sinopia 只在遮罩外接框里算 → 1.35 GB |

**彩色玻璃花窗**

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

**泥金手抄本**

| 问题 | 改法 |
|---|---|
| 羊皮纸像拉毛墙、灰泥墙 | 封皮的细颗粒起伏误铺到了书页底下：封皮起伏只加在露出的封皮上；皮面起伏只用低频（尺度约 240 px、振幅约 6 px，靠近页边加倍） |
| 正文溢出压进圆图；首行红字标题被挤成两行 | 动笔前用 `text_width` 量：x 高 18 px 时一行约 45 个字符，标题写短；正文按行数算好再定图的位置 |
| 首字母旁窄栏两端对齐后，词距大得像空洞 | 拉伸上限 2.2 个词距；放不下就按拉丁音节加连字号断词（已处理），还不行就左对齐 |
| 打磨金箔像一块黄颜料，带横向稻草纹 | 金是镜子，颜色就是它映出的房间：让平面的反射落在窗光的斜坡上（窗方向 z≈0.8），给石膏底加打磨留下的大尺度起伏（尺度约 60 px、±2 px），才映得出明暗带；拉丝纹振幅压到 0.04，金箔接缝 0.12 |
| 同样的金，在跨页一边亮、另一边发橄榄黑 | 相机放远（z≈6000，接近正交），明暗只看表面法线，不随画面位置漂移 |
| 星盘的网架金色太粗，盖住盘面，看不出是星盘 | 网架变细（黄道环 0.06R、横梁 0.017R、星指针 0.024R），盘面加方位圈（过天顶和天底的圆，只画地平线以上），墨线 0.75 px、不透明度 0.85 |
| 圆图里的行星名字摞成一竖排 | 每个名字沿自己的环写，角度错开成阶梯（150° → 36°） |
| 恒星天里的金星被群青盖掉 | 先贴金后上色，颜料遮罩要乘 (1 − 金)，绕开已贴金的地方 |
| 常春藤叶子像金色小铃铛，压到正文和边框条上 | 叶形要有两侧尖角和深缺口；叶、花、金珠放下前先检查：叶尖和两侧角离正文至少 9 px，离边框条至少「叶长 + 3」px；卷须不能弯回去穿过边框条 |
| 首字母上的白色短划像随手画的加号 | 去掉短划，只留沿笔画中线的白线和三点一组的白点 |
| 次级首字母的红色卷须压进红字标题，像鱼骨 | 卷须放在字左侧 16 px 外；钩子只朝页边一侧，长短交替，末端打卷 |
| 背面透过来的字太重，像渲染错误 | 透印不透明度 0.03，模糊 1.6 px |
| 动图里玫瑰色和金色被量化成褐色 | 调色板取样时，饱和像素算 5 倍 |

**达·芬奇手稿**

| 问题 | 改法 |
|---|---|
| 排线像一团卷毛、像波浪 | 不要把一条长排线切成一串各自弯曲的短笔首尾相接；手是一排一排地排线：同一层排线共用一组带轻微错位的「排界」，长线只在排界处断开，留 0–2 px 的空隙或交叠；手抖 jitter 降到 0.1，所有笔画朝同一边微弯 |
| 蒙皮整片涂黑，像一幅幅窗帘 | 每片蒙皮用 `between()` 取「从前一根肋到后一根肋」的 0→1 场，明暗取 t²：靠前那根肋留白、靠后那根肋才排线、最深处才交叉，蒙皮才会鼓起来 |
| 翼后缘一段段往外鼓 | 蝙蝠翼蒙皮在两个肋尖之间往里凹；镜像到左翼时法线方向会反，弯曲方向按「朝翼内某一点」决定，不按左右写死 |
| 翼形又钝又圆，像一面帆 | 指骨肋从腕点呈扇形散开，翼尖收成尖角，越往外翼弦越短 |
| 红粉笔鸟翼像梳子、像流苏 | 羽毛不画完整轮廓：只画宽羽片的外缘、圆的羽尖和窄羽片的尾段（`overlapped=True`），一片压一片；羽尖要圆不要尖；初级飞羽比次级飞羽长，外侧几根张开约 7° 成「指」；宽羽片靠外缘处排线（被下一根羽毛压出的影子），覆羽画成成排的小圆弧再揉开 |
| 单根羽毛像一片带叶脉的叶子 | 羽枝每 2.6 px 一根、很细很轻，朝羽尖斜；加一段光秃的羽管和两处羽枝分叉的缺口 |
| 扇形排线时有时无，一块一块 | 明暗值不要正好压在排线阈值上（噪声会让它一半过线一半不过），整片均匀的排线 shade 给得比阈值高一截 |
| 尖笔辅助线横穿整页、像划痕 | 圆规只在需要的地方刻一小段弧（翼尖 ±12°），中心线、肩线可以长；刻痕没有颜色，只靠侧光的明暗 |
| 曲柄看起来像个 L 形铁片 | 曲柄臂在轴端加一个套轴的凸台，木把手更长更粗，并用点划线示意它沿轴滑上去 |
| 分解图的零件和机翼撞在一起 | 先算好投影：相机方位角改为 +22°，轴往左下伸，轴缩短到 250，曲柄落在空白处 |
| 旧纸太干净、像新打印纸 | 除了霉斑还要大片柔和的泛黄云斑（纸的施胶老化不均）；霉斑要有清楚的小核，不能只是一团模糊的晕 |
| 霉斑的晕被切成小方块 | 每个斑点的计算框要按晕的半径（约 7 倍斑点半径）开，不能按斑点本身 |
| 墨色发灰 | 铁胆墨水偏暖：淡处琥珀褐、浓处深赭，叠处更深；纸纤维把墨线轻轻打散 |
| 飞鸟序列只是一串「V」 | 每只鸟加身体、尾羽、腕部转折和翼尖张开的初级飞羽，按 `phase` 走完一次上扑下扑 |

**剪影**

| 问题 | 改法 |
|---|---|
| 垂卷用一串椭圆叠成，像一串葡萄 | `ringlet()`：一条左右摆动、每圈鼓一下、越往下越细的长条（约 5 圈），金粉只在每圈上画一笔短斜线 |
| 头发的金粉画成随机小弧，像一串气泡；改成 10 条等距平行线，又像条纹头盔 | 只画 6 条左右长短不一的发丝，顺着发团从额头梳向脑后，线宽约 2 个设计单位 |
| 帽檐是等粗的直条，像一根签子插穿了头 | 帽檐沿一条 S 形中线 `snip`：靠帽冠处最厚（约 22），两头收到 3，前沿上翘，后沿下垂 |
| 帽冠的褶纹全汇到一点，像顶帐篷 | 褶纹画成互不相交的短弧；帽冠上沿用 `scallop` 鼓出一排小圆，做出抽褶感 |
| 蝴蝶结是两个圆环加圆洞，像眼镜，还被帽檐挡掉一半 | 环拉长成椭圆，中间剪一道窄缝（宽约 0.12 倍）；放在帽檐上方、背后是底卡的地方 |
| 猫又高又窄、头很小，像保龄球瓶 | `sheet(warp=)` 只改比例、不重敲坐标：头放大 1.12 倍并下移，身体朝垫子压到 0.62，臀部加宽；再剪出眼睛和前后腿之间的空隙 |
| 船的两面三角帆互相重叠、又压着前桅帆；主帆和后纵帆连成一大块黑 | 第二面三角帆整个放在第一面后缘的右边；主桅最下面的大横帆收起（帆桁下一排小圆）；后纵帆缩到主上桅帆下面；上下横帆之间至少留 14 个设计单位；三角帆保留尖角，只让后缘鼓 |
| 侧框外圈的红色底漆磨成一大片一大片棕斑 | 底漆只在棱顶露出：噪声尺度 5 px（2× 采样再 ×2），阈值 0.66–0.80，强度 0.6 |
| 名字和小字贴到黑色描边带上 | 椭圆越往下越窄：先按 hw = rx·√(1−(dy/ry)²) 算那一行的半宽再定字号；名字 32 px，小字不超过 25 个字符 |
| 墙纸条纹笔直清晰，像现代印刷 | 印版遮罩加约 ±0.9 px 的横向漂移，奶白色墨不透明度 0.66，每幅纸单独印、各自错位和对花，再加一层泛黄 |
| 动图里深红丝绳被量化成棕色，玻璃反光下的黑纸出现一块块色阶 | 调色板样本加权：饱和像素 ×5、深红 ×15、被反光抬亮的黑（亮度 0.075–0.28）×7，再叠同一张 4×4 Bayer（约 ±2.4 级） |
| 峰值内存 1.1 GB：整幅 `blur` 和细尺度 `noise2d` 产生大量 float64 中间数组 | 挂镜线、护墙线的阴影只和 y 有关，按一维算；整幅细噪声换成白噪声加 3×3 均值；2× 金框按 192 行一带分带渲染（重叠 24 行），降到约 0.6 GB |

**凸版印刷海报**

| 问题 | 改法 |
|---|---|
| 大面积实地满是白点，像加了噪点滤镜，木刻黑块发灰 | 漏白（salt）只出现在实地内部，纸齿阈值 0.975 以上，约占 1%–5%；边缘积墨处几乎不漏；木活字凹坑软斑浓度降到 0.15–0.35 |
| 大象前腿斜着伸到老远的鼓上，像撑地的肘 | 以髋为轴把身体整体抬起（约 22°），四条腿都竖直向下；鼓放在前肩正下方，鼓顶 = 前肩高度 + 前腿长（腿比后腿短 4%） |
| 大象像秃头圆球加一根水管，耳朵像第二个头、像垂耳狗、像兜帽 | 象鼻根部宽约一个头高（104→26 渐细），并进前额；耳朵是扇形：前缘弧形贴在眼后，顶端低于头顶让圆顶露出来，后缘波浪、下端收尖；加小象牙和张开的嘴 |
| 腿根在身体里画出一圈圆头轮廓，像插上去的柱子 | 先刻远侧两条腿；近侧身体、头、鼻、近侧腿、尾巴合成一个剪影只刻一圈外轮廓，内部只补大腿、肘几笔短轮廓线 |
| 排线整片一样密，大象像条纹木桶 | 排线线宽跟随明暗（`hatch` 的 tone），lo 约 0.3：背上最亮处线条自然收尖消失；身体用绕远处圆心的弧线，腿用竖线，鼻子斜线加横向皱纹 |
| 鼓上的条纹印成一整块红色楔形 | 条纹相位 = arcsin(u)·9 − y/9，一圈正面看到 4–5 条斜纹，上下各留出箍 |
| 象头上的小帽画成红色贝雷帽、像一颗樱桃 | 非斯帽用直边多边形 `poly`（不用平滑闭合曲线），流苏从帽顶垂到后面 |
| 象鼻尖碰到钢丝，看着像要去抓钢丝 | 鼻尖离钢丝留约 70 px，卷向演员 |
| 画面偏右，桅杆和大象之间空出一大片 | 大象放在两根桅杆正中；背后加雕版衬线：横向细线、椭圆向外渐隐，每样东西周围先 blur 出一圈白再清掉 |
| 舞者的站立腿是两根细线，平衡杆横穿胸口 | 腿加粗（17→9 px）、加黑色舞鞋；手肘弯下，杆放到腰的高度 |
| 马戏圈的圈沿伸出画面右边；锯末和地面投影太黑，像污渍 | 圈的半宽按两根桅杆间距算；锯末密度 0.0035、只在脚边，投影用横向排线（tone 0.55） |
| 纸边的小缺口是一颗颗黑点，像墨团 | 缺口只留 3 个、3–7 px |
| 峰值内存 1.5 GB | `press` 按 240 行一带处理；木刻印完就释放整页遮罩（1.19 GB） |

**苏联构成主义**

| 问题 | 改法 |
|---|---|
| 网格塔印成网点后是一根实心的点状锥体，看不出格子 | 每节每组杆件从 24 根减到 16 → 8 根（越往上越少），杆件加粗（0.55 m 往上收到约 0.27 m）；远侧半圈的杆件反照率最多 ×6.5，显得浅；雾的距离从 520 m 改到 2600 m（否则全塔被雾冲成均匀的中灰）；塔照片加网前的模糊从 0.3 格降到 0.12 格（`soften=0.12`），塔顶的横担才分得开 |
| 收音机照片认不出：喇叭正对镜头成了一个黑球，电子管是白疙瘩 | 喇叭口轴线与视线约成 60°，侧面看得到外扩的喇叭口和口内暗面；黄铜反照率 0.45、金属度 0.5，底座改黑漆；玻璃管反照率 0.42，加一道内部阳极暗带 |
| 收音机面板像照相机（两个一样大的象牙色刻度盘像镜头） | 改成一个黑色胶木大刻度盘（镍圈 + 白刻线）加两个小旋钮、接线柱、铭牌，机顶加蜂巢线圈，喇叭到机身拉一根软线；照片放大到 1.16 倍，网点格从 6.5 px 改成 5.5 px |
| 编号方块里的数字不见了 | 黑色电波弧压在了标注上，黑上加黑挖不出空。电波只占楔形 ±9° 的范围、到喇叭口为止，标注都放在电波范围外 |
| 电波弧铺满半张纸，像梳子、像肋骨 | 波前只画在楔形附近，从塔尖画到喇叭口；线宽随半径变细（`grow=-0.045`）；上沿只到 +6.5°，别碰到标题 |
| 斜排的标注里，数字跑到方块外面 | 方块和数字都用 `along()` 从同一个左下角算；不要一个绕自身中心转、一个绕角点转 |
| 剪下的照片放在纸色上，剪刀留的白边看不出来 | 让照片压在红块、黑条或楔形上：收音机后面垫一块从黑条升起的大红块，楔形一直伸到喇叭口下面 |
| 红块只从照片缝里露出几条细缝，像渲染错误 | 红块要比照片大一圈（高 410 px），从黑条一直顶到标题下面；剪刀剪不进的窄缝用 `close=` 桥接，被照片围住的洞自动填平（剪刀只能绕着外轮廓剪） |
| 楔形末端的直边在喇叭口旁边露出一个红角 | 楔形只伸到喇叭口再多 20 px，半角 5.6°，宽度和喇叭口差不多，末端整个藏在剪下的照片下面 |
| 折痕太弱，像画上去的一根细线 | 折痕处墨层断断续续地裂开（约 2–3 px 宽），两侧约 ±3 px 的磨损带墨最多淡 22%，再加一亮一暗的折棱和一道污渍带 |
| 图钉孔像一个黑点 | 孔周围加一圈偏向一侧的锈色晕 |
| 红版套印错位后，画面右边缘露出 2 px 纸白 | 错位前先把版用边缘复制 pad 8 px：成品是印完再裁切的，边上不会露白 |
| 填洞后剪下的照片反而整片印满底色网点 | `ImageDraw.floodfill` 对 `Image.fromarray()` 得到的图不起作用（不报错），要先 `.copy()` 再填 |

**装饰艺术**

| 问题 | 改法 |
|---|---|
| 车鼻前下方一圈圈指纹状条纹，法线乱跳 | 「把截面朝一个点缩放」得到的不是合格的距离场（命中点残差 0.19 m）；改成竖直核心线段膨胀 R 的精确截面（直侧壁、圆车顶、底部平切），车鼻只沿轨道方向拉伸（只会低估距离，步进安全），残差降到 0.008 m |
| 车头竖直，像电车 | 核心前缘做成斜线（`rake` 约 2.2 m），车鼻向前下方倾斜 |
| 头灯飘在车头前面；奶油窗带在车鼻上被一刀竖直切断 | 斜车头实际伸出的长度比 nose_len 长得多（垂直斜边膨胀）：用二分法实测车鼻表面，头灯、条纹收拢、车鼻素色端头都以实测车尖为准；条纹在最后 14% 前停下，窗带收成尖头 |
| 车身只有几道细金线，远看是一整块红 | 加奶油色窗带（1.95–3.15 m）和上下金线；腰线在车鼻上按截面坐标向车鼻收拢，成为速度线 |
| 钟和扇形冠顶浮在楼顶上面，戳进标题 | 钟画在顶层楼身上（`top_windows=False` 把这层的窗空出来），冠顶从顶层上沿起；近景楼顶都压在副标题下方 |
| 副标题两侧的金线穿过副标题文字 | 先画副标题拿到宽度，金线从标题两端画到副标题外侧 28 px |
| 头灯是一大团白光，像一只眼睛 | 灯球半径 0.3 m、铬圈 0.47 m，光晕 80 / 10 px，自发光 0.85 |
| 头灯光束指回车身 | 光束终点取 60 m 前方会跑到相机后面、投影翻转；终点改为 min(60, 0.6·Z/dz) |
| 头灯照亮前方铁轨，但画面里看不见 | 护栏 0.56 m 高、相机只比轨面高 1.4 m，桥面被护栏挡住；护栏降到 0.25 m、相机抬到轨面上 2 m；掠射角的朗伯项只有约 0.1，改成包裹式（×5 封顶），铁轨成了从左下引进画面的两道亮线 |
| 喷枪颗粒太粗，光束和射线像撒了沙 | 颗粒 = 固定噪声 × 0.2 × d(1−d)：只在薄涂处有，实涂和空白处没有；射线的颗粒 0.45 |
| 河面倒影是一块块迷彩斑 | 波纹按压缩后的深度坐标取噪声，横向拉长约 90 倍、只用两层：近处长而稀、远处细而密 |
| 月亮倒影太弱，黑天空和月亮反射得一样多 | 镜像按亮度加权（0.45 + 1.3·smoothstep(0.35, 0.85, 亮度)），月亮和窗灯拉出一条光路 |
| 车窗倒影成了高架下面一串孤立亮点 | 范例里关掉（`lights(r, reflect=False)`）；要用就把拉伸调长 |
| 月海是脏兮兮的斑点 | 月海用 smoothstep 柔边、浓度 0.13、颗粒 0.25 |
| 动图里红色车身被量化成棕色色块，天空出色带 | 加权调色板（饱和像素 ×5、亮像素 ×2）+ 每帧同一张 4×4 Bayer（约 ±2.4 级）；量化只用 255 个真实颜色，占位透明色用品红，否则最暗的像素被当成透明（自检 9 帧对不上） |

**黄金时代漫画**

| 问题 | 改法 |
|---|---|
| 羽状排线像一排梳齿、像尺子刻度：等长、等距、完全平行 | 长度跟着两层慢噪声起伏（0.25–1.15 倍），间距 ±30%，每根略弯、偏离平行约 4°；起笔压在阴影边上，越往亮处越短 |
| 羽状排线穿过白色色环上的字，RS-1 被看成 RS-T | 排线的 clip 去掉文字所在的区域 |
| C40 M70 Y100 的棕色（头盔、山体暗面）在 11 px 粗网下花成发绿的斑 | 棕色不用蓝版：M70 Y100 + 黑 40% / 70%（`BROWN` / `DARK_BROWN`） |
| 天空七条等宽色带像一面旗；中间几档两版都挂网，花点太闹，压住人物 | 色带用 `edges=` 指定不等宽；过渡档尽量只挂一个版（蓝 40%、蓝 20%、黄 40%），两版叠网只留在顶部一两档 |
| 月亮光晕的同心色环盖过所有色带，在橙色带里切出一个蓝色圆盘 | 去掉光晕；`rings()` 只用在单一色带里 |
| 顺风飘的围巾正好盖住后座小狗的头，小狗只剩一团白 | 围巾往后上方飘（漫画夸张），小狗后移；先画后座再画前座；狗脸用纯白（不挂网）配黑耳、黑鼻、金色护目镜 |
| 护目镜比脸还大，像第二个头；挡风玻璃像两颗牙、像多出来的尾翼 | 护目镜只露一只镜片推在额头上；去掉挡风玻璃，只留座舱口沿 |
| 座舱里的人画在船体之后，下半身露在船体外面 | 先画人，再画船体：`part` 会擦掉被挡住的墨线和颜色，最后补座舱口沿 |
| 尾喷管是一块挂网灰方盒；火焰外层深橙和橙色天空同色，又被下尾翼和烟挡掉 | 喷管涂黑加银色口沿；火焰由外到内红、深橙、橙、黄、白五层，烟只吞掉火焰末端，下尾翼缩小，去掉横穿舷窗的中间尾翼 |
| 烟团是锯齿星形、挂橙色网，像一堆石头 | 烟团用近圆形加轻微起伏，白底；只在右下月牙挂黑 20%，靠火焰的一侧挂黄 40% |
| 右边台地看不出是悬崖：斜面、羽线、暗面混成一团，暗面花成墨绿 | 平顶加竖直崖壁：崖顶下一道黑影，裂缝从黑影往下用 `feather(along=(0, 1))`；崖脚另起一道碎石坡，换一种颜色 |
| 地平线正好穿过 Sparky 的头；他在画面里太小，故事的笑点看不见 | 地平线下移到胸口；人物放大 1.15 倍，飞走的帽子挪开、别压在手上 |
| 动图超过 2 MB（2.34 MB），网点缩小后成了摩尔纹 | 缩到 720 宽时用 BOX 不用 LANCZOS：1.79 MB，网点仍隐约可见 |
| 内存峰值 1.25 GB | 网点阈值图等缓存改成 float16；印刷按 180 行一带处理；刊名只在自己的裁切区里算；做旧效果只作用在各自区域：峰值约 0.85 GB |

**波普丝网**

| 问题 | 改法 |
|---|---|
| 好几格里多出贯穿整格的黑斜线 | 闭眼弧线的粗细用 `sin(πt) ** 0.7`，末端 sin 是 −1e-16，幂运算得 NaN，多边形就连到了窗口原点。`stroke()` 里已把宽度 `nan_to_num` 并截到 ≥ 0；自己写 `profile` 时先 `clip(sin, 0, 1)` |
| 底色上一道道白色横纹，像划痕 | 底色 `dry=0`，`streak` 约 0.012；笔触纹拉长（长约 140 px、宽约 7 px）；干笔拖痕只出现在形状边缘一圈 |
| 缺墨时黑块里露出规整的方格编织纹，像数码图案 | 布纹对墨膜的影响降到 0.035；露底主要来自顺刮板方向的条纹、约 5 px 的团块噪声和一块干版斑 |
| 闭眼的 ∩ 太细，下面又垫一块椭圆眼影，读成「眉毛 + 睁着的眼」 | 闭眼弧线宽约 0.10 单位，两端收细；开心那格不垫眼影，改用腮红；困那格的眼影做成闭合的眼皮形状，只在闭眼线上方 |
| density 0.84 的缺墨格，脸几乎印不出来 | 0.92–0.95 是「缺墨但认得出」，1.0 正常，1.1–1.15 墨多；flood 超过约 0.5 会糊掉半张脸 |
| 墨多那格，远侧耳朵糊成一顶黑礼帽；耳朵压平后，耳背描边和头顶虎斑纹交叉成一个 X | 耳朵外转超过 40° 时，耳窝只印网点、只描上沿；被耳朵挡住的那道头顶虎斑纹不印 |
| 远侧耳朵的阴影和耳背描边分成两块：描边像一根飘着的棍子，耳毛像羽毛球 | 远侧整只耳朵做成一块暗面，一直到外缘；耳毛 4 根，宽约 0.026 单位 |
| 吐舌头只是嘴下面一团红点 | 舌头色块伸出嘴外（下沿到约 0.74 单位）；黑版给舌尖描 U 形轮廓和一道中线 |
| 每格边缘一圈浅色细线，像内描边 | 漆脊的 relief 从 0.9 降到 0.35 |
| 左肩上的长弧形虎斑纹像几道「翅膀」 | 受光一侧的胸前斑纹不印实线，只印成网点带（tone 约 0.38） |
| 峰值内存 1.08 GB | 脚本把 60 多张整窗遮罩放进列表再 `np.stack`；`canvas()` 和合成时又整幅算临时数组。改成用 `np.maximum` 就地累积遮罩，颜色层按格现算，布纹和合成按 180 行一带计算，降到约 0.46 GB（改遮罩累积这一步前后，成品逐字节相同） |
| 动图里黑网点和六套配色的混合色量化错（p99 误差 100） | 调色板样本里，已上黑版的后半关键帧 ×3，再用 `kmeans=4` 精修：p99 降到 39，误差大于 70 的像素从 3.7% 降到 0.03%，体积不变 |

**ASCII 字符画（行式打印机）**

| 问题 | 改法 |
|---|---|
| 箭身和烟用 I H M N 之类字母铺调子，远看像一行行单词「IMM」「HNM」 | 填色字符只用符号：箭身 `. : + % # #@`，烟 `. : % @ # #@`；字母只留给真正的文字 |
| 按形状相关度给线条挑字，桁架塔变成一串 `<> <>`、`^V` | 改成按方向和位置选：方向在真实像素里量（格子是瘦高的），陡的 \| / \\，平的按在格里的高低选 `' - . _`，两条线交叉才用 X / + |
| 斜线、竖线同时压到左右两格，到处是 `//`、`\\`、`)\|` | 同一条线、同一方向的相邻两格只留笔画更多的那格（非极大值抑制；斜线还要求字符相同，免得吃掉尖顶的 /\\） |
| 桁架斜撑交点落在四格交角，中间成了 `\_/`、`/-\`，没有 X | 斜撑按「一列一行」走、过格心：塔宽取 6 列（中间 5 格），交点正好落在格心出 X；横撑放在行中心，压在行界上会被两行平分、谁也不到阈值 |
| 箭身和黑色滚转标记、尾焰之间也描出一圈轮廓，箭身里横七竖八的 \| 和 ---- | 角色分组（`group='rocket'`）：同组之间不描边，只有对外的剪影描边 |
| 烟云每个云团都描边、调子又加误差扩散，底下一片乱码 | 云团用 `edge='all'` 但 `inner_max=0.5`：只在亮的云顶画 ( ) 和 .-'，暗部只靠调子；光从上方来、云底再加一层自身阴影（`lift`），抖动降到 0.2；云团改成少而大（半径 5.5–10 列） |
| 字太干净，像激光打印或屏幕截图 | 字模先按墨的洇开模糊约 0.5 px，再和色带织纹、纸面齿纹一起过阈值：力度够就满铺，力度弱就变细、断开、起麻点，而不是变灰；改用粗体字模 |
| 火焰内部加了一根根 ' ! 的条纹，像引号和珠串；内焰锥画成一串 () | 尾焰从箭身底部直接长出来、和箭身同组，不用随机抖动 |
| 尾焰只剩两条 ( ) 竖线围出的空白，读不出是在点火 | 尾焰做成从喷口往下变宽的亮柱：外层 `plume` 角色按离轴距离 u 从 . 过渡到 % @ # 的烟套（u>0.45 起变暗），内层 `core` 角色是几道从喷口散开、沿长度明暗闪动的条纹（! \| 在喷口、往下变成 : . '），两层都不加随机抖动才对称 |
| 下面两团前排烟云从两侧压住亮柱，形成往下收窄的漏斗，看着像火焰变细 | 前排烟团外移（离轴 13.5 列），亮柱两侧各放一个小烟团接住烟套，中间那团的云顶 ____ 正好接住柱底 |
| 头锥用平滑闭合曲线，肩部鼓出一块，又一版太钝像圆顶 | 头锥按弹头曲线 半宽 = R·(2s − s²) 逐点算多边形，不用样条 |
| 左边天空加一层随机点「晨雾」，像纸上的脏点，还在第 94 列切出一条竖边 | 去掉；空的天空留白，右侧大空位放一座远处水塔平衡构图 |
| 表头「RUN … PAGE」和参考图的格式太像 | 换成 JOB 4471 / SHEET 2 这类自编字段 |
| 最底下一行烟云被画面下边切掉半行字 | 改用 8½ 英寸深的连续纸（`page_in=8.5`，51 行一页），`ppi` 调小让整张纸连同上下两道撕线都在画面里，左右露出桌面；画面在 `page_rows − 2` 行 `erase` 掉，留两行页边再到撕线；横向撕线和折痕加深 |
| 太阳只是一圈线加几根离得很远的光芒，鸟东一只西一只，像随手的符号 | 太阳盘面用 . : 填出边缘发暗（中间 .、边上 :），光芒贴着盘面、8 根等长；鸟排成一队人字形往太阳方向飞 |
| 动图里红圆珠笔被量化成灰色 | 红色像素太少，加权也抢不到颜色：调色板单独给红色留 14 格 |
| 峰值内存约 1 GB | 纸张按通道就地合成、成图分 480 行一带合成，降到约 0.7 GB |

**低多边形**

| 问题 | 改法 |
|---|---|
| 悬崖上满是竖向的绿条纹，平台上反而是横向岩层 | 材质错位一格：每个面的材质取剖面里靠内侧的那个点（两端下标取小的），悬崖才贴岩层、平台才贴灌丛 |
| 河床三角形一块块从水面里戳出来 | 画家排序按平均深度，埋在水下的河床有时算得比水面「更近」：完全在水下的面干脆不生成（`canyon(buried=)`），水面带 −2 的排序偏置，像贴花一样后画 |
| 水面一片发白的青色 | 涟漪短划减到 16 条、颜色压暗，水面 spec 0.35；逆光看水本来就亮，别再加 |
| 构图照搬参考图：飞机在正下方、大环正居中、后面的环一个个叠在环里 | 赛道改成右转弯，相机放到飞机右后方，用 `aim()` 把飞机放到左下三分点，金环沿对角线往右上排开 |
| 外弯的岩壁把天空整个挡住，太阳和光晕都没了 | 峡谷整体压低（`height=0.75`），相机降到飞机上方约 2.6 m，视场 52°，留出约两成天空 |
| 从正后方追尾看，飞机只剩一个「十」字，还被画面底边切掉 | 相机放在右后上方，能看到机翼上表面；飞机离镜头约 11 m |
| 一级台阶和相机差不多高，被看成一道发亮的裂缝 | 相机高度避开台阶高度（台阶约 11.8 / 20 m，相机约 16.6 m） |
| 金环又细又发橄榄色，看不出多面体 | 管径 0.6（半径 3.4）、12×5 个面、暖金 #ffaa1a、glow 0.28、spec 2.0、shine 4：暗面偏橙、亮面发黄、迎光的面闪白 |
| 逆光下飞机和金环发灰发闷 | 着色光和画里的太阳分开设：`light(lift=26)` 把着色光抬高 26°（当年的游戏也这么做） |
| 光晕里的空心圆像多出来的金环，正中的绿色六边形像一块石头 | 光晕只用小圆点和实心六边形；画面中心附近只放 2 px 的小点，大六边形放到远端并调淡 |
| 「"」加粗后两撇连成一道横线，「1'07"42」读成「1'07-42」 | 两撇之间空两列（`'#  #'`）；零不加斜杠，斜体时才不像 8 |
| 螺旋桨盘几乎看不见，像一块灰斑 | 半透明盘 alpha 0.36，再加一圈更亮的桨尖圆环 |
| 杜松在逆光里成了黑剪影 | 树带 glow 0.3，叶色提亮 |
| 动图 2.08 MB，金色 HUD 偏棕 | 缩小用 BOX 而不是 LANCZOS（像素硬边不出振铃噪点），调色板样本里饱和像素 ×5：1.63 MB |

**喷漆模板涂鸦**

| 问题 | 改法 |
|---|---|
| 每张模板四周都有一圈带麻点的大方框（风筝、燕子、字周围最明显），一开始还是贴着卡纸边的几条细直线 | 喷的区域按 2.5 倍喷幅往外扩，卡纸外的漆才落得到墙上；扫过卡纸边的「卡纸残影」系数降到 0.0035；扫到头折返时只减速到 0.55，不再在边上积一大团 |
| 所有边缘都是 6–8 像素的毛刺，像发霉，清晰核心没了 | 卡纸翘起量不再按「离胶带越远越高」涨到 1：平贴为主（0.15 + 0.35 × 离胶带距离 + 0.5 × 局部鼓起）；底下渗漆只用 1.8 像素模糊、权重 0.2 + 0.5 × 翘起量；外溢雾化 7 / 24 像素两层，强度 0.022 / 0.012 |
| 滴痕到处都是：白漆滴痕从围巾一路流过外套和裤子，每座桥上面都往下滴 | 只从真正的下边缘起滴（往下 7 和 12 像素都是空的，桥不算）；数量按 amount × min(26, 2 + 过量/40) 封顶，白版 0.06、灰版 0.2、黑版 0.7；滴痕的凸起降到 0.45 + 0.25 × 宽度/3，否则被后面几版盖住了还以白色棱线透出来 |
| 三版叠起来灰糊糊：灰版跟黑版几乎一样深，白版喷不匀一片麻点，黑版只剩细边 | 灰改 #7b7c79；白漆遮盖力 2.0、喷 3 层；黑版阴影加深（躯干 34、腿 18 / 44 像素），`shade_side(wobble=)` 让阴影边像手刻的 |
| 燕子像喷气式飞机 | 弯月形后掠翅（一上一下）、细身子、长长的分叉尾 |
| 围巾先像面条，再像「VAV」字母，最后像一只举起来带手指的条纹胳膊 | 从脖子前一个结里分出两条长短不一的窄尾巴，往前稍往上飘；只画横条纹，尾巴上不加阴影月牙；流苏扇形散开、互不相碰（碰上了会围出孤岛被桥切成方框） |
| 帽檐压住眼睛，下巴下的黑阴影像小胡子 | 帽檐整体上移 6 个单位，眼睛放大、鼻头往前凸、嘴是轮廓上的一个缺口；下巴阴影改进灰版、变细 |
| 小孩像在往前走，躯干像一只蛋 | 上半身绕髋部再后仰 9°，前腿伸直、脚跟着地脚尖翘起，后腿弯着撑住；羽绒服缩短到胯部、收窄 |
| 黑版快照里卡纸整张喷成黑的，看不出刻了什么 | 卡纸上的漆按「粉尘」画（0.82 × (1 − e^−0.55D)，透出牛皮纸），切口边按卡纸厚度一侧亮一侧暗 |
| 墙像木板墙，木纹太清楚；裂缝像画上去的黑线；泛碱像一条白色虚线 | 木纹起伏减半，只在一块块区域里压出来；加水泥色斑和浮浆；裂缝变细变淡；泛碱用噪声断开 |
| 市政灰漆像一块模糊的圆角方块 | 改成一道道竖着的滚筒：每道起止高度不同（上下边缘成台阶）、两头发干拉丝、相邻两道重叠处颜色深一点，底下的旧签名透一点出来 |
| 动图里红风筝变成砖红色、粉色签名没了 | 调色板样本加权：红 ×12、其他饱和色 ×5、黑 ×3，再叠同一张 4×4 Bayer（约 ±2.4 级）；透明占位色用品红，不用黑 |

**刺绣徽章**

| 问题 | 改法 |
|---|---|
| 牛仔布像印出来的 45° 斜条纹，白纬又亮又粗 | 经纱比纬纱密（1.5 × 2.5 px），斜纹约 60°；纬纱只露一小点、每点露多少随机；经纱加竹节纱的染色起伏和磨白；2× 渲染再缩小 |
| 缎面边框像条形码，黑白条太硬 | 缎面线截面压扁（起伏 ×0.6），线与线之间的暗沟只降到 0.74 |
| 填充绣满片像砖墙 | 针孔凹陷只暗 30%；每行起针位置加 ±6% 的漂移 |
| 缎面平平的，看不出「线的光泽渐变」 | 缎面长线按衬垫拱起（拱高约 0.11 × 线长，最多 3.2 px），一根线上就有从亮到暗的过渡 |
| 深色线被高光冲淡，指南针每个尖角的明暗两半分不出来 | 高光整体 ×0.62；亮半边别用太亮的颜色（亮红 #cf4637 / 暗红 #721a14） |
| 雪峰亮面太白，雪顶糊进山里 | 山的亮面用中灰蓝，白只留给缎面雪顶；阴面明显更暗 |
| 火焰用竖向缎面，长线被拆成交错短针，看着像填充绣 | 针向横着走（约 ±15°），maxlen 放到 90；外焰、中焰、内焰一层压一层 |
| 湖面波纹穿过帐篷，还伸出徽章压到边框和牛仔布上 | 细节针按层次排在压在它上面的东西之前画；`run(clip=徽章遮罩)`，路径留在边框以内 |
| 异形章圆角的缎面边框出现放射状摩尔纹 | 按相位梯度算每处针距，小于约 2 px 时把单根线的起伏淡掉；圆角半径至少是边框宽度的两倍（34 px 对 17 px） |
| 锁边上周期性的暗条和小黑点，底下的颜色从里面透出来 | 两个原因：2.6 px 的绕线和像素网格拍频，改成按 (s, d) 4 次子采样再平均；PIL 粗折线画的带状区域有针眼大的洞，再做一次 5×5 最大值滤波 |
| 弧形条章的字挤到两头的锁边上 | 字号 42、跨角 98°，字间距 0.05 倍字号 |
| 整组徽章太小，画面上方三成空着 | 设计坐标统一乘 1.14 再上移；针单独按画布坐标摆，别跟着放大推出画面 |
| 动图里金色锁边和营火被量化成橙褐色 | 调色板样本里暖色饱和像素 ×5、亮色 ×2（暖色平均误差 9.5 → 5.6） |

**蓝图工程图**

| 问题 | 改法 |
|---|---|
| 细字和细线在大片区域里糊掉，像对不上焦，备注、标题栏、引出文字整段看不清 | `core.blur` 会把亚像素 sigma 量化成 0 或约 1.4 像素，「压框接触不良」的区域整片被糊了 1.4 像素：改用库里自带的真高斯 `_gauss`，接触好 0.55、接触差 0.9；单笔画字的笔宽至少 1 像素 |
| 「断墨」噪声被做成一大片，一行字的后半截淡掉 | 只在 3 像素尺度细噪声的 0.84–0.96 峰值上断墨，再乘一个 90 像素尺度的门控；断墨只减 45% 墨量 |
| 小数点不见了：17.90 印成 1790 | 句点是 0.08 个单位长的线段，圆头只剩 1 像素：短于 0.2 单位的笔画一律画成实心圆点 |
| 标题栏里的仿宋中文印不出来；加粗后又糊成一团 | 仿宋笔画太细，晒图的 S 曲线把它当成浅铅笔线：先压窄（0.82），再 3×3 最大值滤波、灰度 ×1.35 实化；别用 5×5，会糊 |
| 剖面里的螺旋楼梯像一层层楼板 | 被剖到的踏步是一条条实心白条，远半边只有 fine 线：远半边的踏步前沿、贴墙的踏面—踢面锯齿改用 thin，加一条贴墙的螺旋底面线；被剖到的踏步只留 0.13 m 厚 |
| 剖面墙上的窗洞像裂缝或墙体错位 | 窗洞改成内大外小的八字口（外口 ±0.38 m、内口 ±0.55 m），窗扇退进墙面 0.25 m，画一粗一细两道 |
| 尺寸数字压在剖面线上读不出来 | `dim()` 默认 `clear=True`：写数字前先把它后面的剖面线刮掉——制图员本来就这么做 |
| 比例尺刻度乱了，有一截白条跑到别处 | 把「每格像素」当成了「每单位像素」：接口改成 `scale_bar(x, y, px_per_unit, units)`，刻度用真实数值 |
| 透镜详图里的棱镜像一串叠在一起的飞刀和箭头 | 棱镜画太大了（进光面很长）：光路缩短到 L1 0.1 m、L2 0.03 m，棱镜里加 30° 的细剖面线表示玻璃 |
| 详图里的灯室檐口和窗台画成两块大白方块，还盖住了说明文字；穹顶弧线一直伸到图框 | 改成细线框加金属交叉剖面线；穹顶只画起拱的一小段，下面用折断线截断；光束说明挪到详图上方 |
| 平面图的 UP 箭头画成了整整一圈，看不出是箭头，跟铅笔辅助圆混在一起 | 只画约 205° 的弧，起点一个圆点、终点箭头，UP 写在起点；去掉同心的铅笔圆 |
| A–A 剖切符号撞上剖面右侧的引出文字；低处标高（±0.00、−1.80）压在岩石和海浪线上 | 剖切线缩到墙外 0.56 m，两张图整体左移、引出文字列从 806 起；低处两个标高挪到剖面右边，海浪线在标高前截断 |
| 水渍像一块灰色圆饼 | 按「水洇开再分两次干」建模：两道干燥前沿各留一条清晰的褐色潮线，里面只淡化约三成、带斑驳 |
| 折痕交叉点像一颗亮星 | 交叉处磨损半径 7 像素、只淡化 38%，折痕磨白只混 0.2 |
| 动图里红铅笔变成灰蓝色 | 调色板先对全部关键帧中值切分 238 色，再从红铅笔像素里单独切 17 色补上（`claude_drawing/blueprint_work/make_gif_bp.py`） |

**儿童蜡笔画**

| 问题 | 改法 |
|---|---|
| 第一版色块像一层均匀的砂纸，看不出来回涂的笔道，和彩铅、喷砂分不开 | 纸纹先沿笔道方向拖着平均一遍（双线性取样 ±6 px，与原纸纹 0.35 : 0.65 混合）再重新均衡，露白的小坑被拉成顺着笔道的短条；笔道间距 = 笔宽 × (2.3 − 1.6 × density)，每道压力 = pressure × (0.84 + 0.36 × 慢噪声)；纸纹改细（1.7 / 3.8 / 14 px 三层） |
| 蜡块像橡皮泥浮雕，空白纸像拉毛墙 | 打光时蜡的高度 1.35 → 0.55（再模糊 1.6），纸纹浮雕 1.1 → 0.65 |
| 山坡线从人脸、裙子上横穿过去 | `line(..., avoid=c.grow(OBJ, 10))`：线走到东西背后就停；所有东西的内部遮罩先收进 OBJ |
| 后画的郁金香、蝴蝶、签名压在草地上，红 + 绿发褐、紫字看不清 | 蜡笔是半透明的乘性混色，盖不住底色：东西先勾线，大片（天空、山坡、草地）`avoid=U(OBJ, c.drawn())` 绕着涂（孩子本来就是这么涂的），最后在白纸上给东西上色 |
| 胳膊、手、狗腿、花茎被草地涂没 | avoid 里加上 `drawn()`（已经画过的线）；狗腿在身体上完色后再用 17 px 重压一遍，脚加一个圆点 |
| 天空绕着标题涂，蓝笔道还是扫进字里（红字发紫、橙字发绿） | 绕开处的转折要「小心」：停在边界内 0.45 × 笔宽、不过冲；被绕开的东西覆盖率 × (1 − 0.9 × 遮罩)；比 0.7 × 笔宽窄的空隙不进笔 |
| 标题像粗黑体，「我」糊成一团、右半边丢了 | 细字体字形先 Zhang–Suen 细化成单像素中心线，再用圆头蜡笔膨胀（默认字号 × 0.068，标题指定 11.5 px）；手抖扰动 0.045 × 字号、尺度 0.55 × 字号；字距按字形实际宽度算（西文才不会散开） |
| 签名夹在郁金香的茎叶之间看不清 | 挪到花下面的空处，草地给名字留一圈 18 px 的空白（`c.grow(名字的蜡, 18)`） |
| 纸上的蜡笔：包装纸像理发店转灯 / 条形码，蜡像塑料，第三根竖着像立在纸上 | 包装纸：两头各两道细线 + 一段波浪纹 + 中间浅色标签上一行伪文字（无商标）；蜡改哑光（高光指数 12、强度 0.13），断面略亮；半径 22 px（直径约 7 mm，接近真蜡笔放在 1920 px 宽的 A4 上的比例），只放两根：一根用秃的、一根撕了半截纸的断蜡笔 |
| 蝴蝶翅膀圈涂太满，糊成两团还压住身子 | 翅膀离身体 7 px、改来回涂、加黄点；身子和带圆头的触角最后画 |
| 墨镜只是一块灰黑，看不出是玻璃 | `burnish()` 把黑蜡压进纸坑：白点合上、和下面的黄混成深橄榄、带一点蜡光；皮球同样处理 |
| 烟囱的烟是等半径螺旋，像一根弹簧 | 圈越往上越大（9 → 33 px）、往右上飘，灰色轻压 |
| 动图最后一帧 EOFError | 最后一个 `stage()` 和成品相同会被合并：`save()` 前不再调 `stage()`（第四节已有这条） |
| 动图里小面积的紫、粉发灰 | 调色板样本加权：饱和像素 ×5、亮色 ×2（1.47 → 1.33 MB，0 帧对不上） |

**绿屏终端 CRT（荧光字符画）**

| 问题 | 改法 |
|---|---|
| 桶形畸变用的是归一化坐标里的交叉项（u·v²）；宽屏下，角上的字被剪切成斜体 | 改成真实像素里的径向畸变 src = p·(1 + k·\|p\|²/hw²)，k = 0.065；字不再歪，四边照样外鼓 |
| 反白的 YES 和状态栏里的黑字看不清：点拉伸和视频带宽把 1 个点宽的暗笔画吃掉了 | 点拉伸改在半点分辨率上做，而且放在反白之前；状态栏改用 `dim+rev` |
| 云的内部用 - = + 这类像线的字，远看是一团 `/=-\` 乱码 | 云用 `outline='cloud'`：斜坡一律打 ( )，平顶、平底打 _ . - '。内部只用 . :，亮部靠 dim → normal → bold 提亮，不换更花的字 |
| 剪影成对出现 `//`、`((`，两个格子都当了边 | 剪影只留一格厚：相邻两格是同一个字时，留覆盖率最接近 0.5 的那格，另一格按覆盖率归入里面或外面 |
| 云底是一排扇贝 `(...)(....)` | `puffs(base=整数行)`：底部 `flat` 行内按云的宽度补满，并闭合泡泡之间的小缝；整条云底打成一根 `_` |
| 细线勾的月牙在 5×7 字里像 S 或 < | 月牙不描边，用 bold 的 % # @ 填满（`outline=None`）。内圆半径约等于外圆，向右偏约 0.45r |
| 太阳像六角蜂箱，往下的光芒像腿 | 太阳用 `cloud` 轮廓加径向渐变 . : + * % # @；光芒只画地平线以上那 9 根 |
| 瘦高格子里拿覆盖重心的方向当法线，斜边的字选偏 | 法线按格子尺寸反比换算：nx = −mx/cw，ny = −my/ch |
| 光晕把整屏蒙成灰绿，失去黑底 | 中、远两层光晕只对 L² 做（bold 发光，dim 不发光）；亮度底（brightness）降到 0.016 |
| 房子比天气还抢眼；光标块贴着反白的 YES，连成一个框 | 墙和屋顶改 dim，只有夜里的窗户用 bold #；提示符后面打了半条命令 `forecast --tomorrow`，光标停在命令末尾 |
| 动图里挡圈边上振铃出一圈亮边，暗玻璃和窗户倒影出色带 | 缩到 720 宽用 BOX，量化前每帧叠同一张 4×4 Bayer（约 ±2.4），调色板样本里绿色像素 ×4、亮像素 ×2 |
| 峰值内存 834 MB | 拨轮、LED、压纹图标改在局部窗口里算；机壳斜面朝向屏幕的程度缓存起来；不再每次渲染都建整幅 int64 网格。降到约 0.73 GB |

**热成像**

| 问题 | 改法 |
|---|---|
| 地面被底部色标栏挡住，猫只露半身，脚印看不见 | 相机再往下俯（灭点 y 150 → 100，焦距 1900 → 1750），地面留出约 200 px；底栏压到 78 px |
| 自动直方图均衡把 20–24 °C 的房间拉成一大片品红，猫和墙同色 | 改用手调色调曲线 `camera(curve=)`：冰箱内 0–0.05、房间 0.23–0.29、脚印 0.35–0.5、猫 0.6–0.72、锅 0.9、只有火圈到白；直方图均衡只混 0.22，留一点局部对比 |
| 锅和水壶饱和成两个白块，锅像个大马克杯 | 曲线把 100 °C 放在 0.91；锅改宽矮，加卷边和两侧环形把手；抛光锅盖 `emissivity=0.55`，读数比锅身低一档，盖子自己显出来；锅身、壶身、面包加 `limb=`，轮廓处变凉、有体积 |
| 烤箱门是画面正中一块巨大的橙色长方形，抢焦点，还和猫同色 | 烤箱降温（门框 23–26.5 °C、玻璃 26.5–31.5 °C，只有顶部门封 46 °C）；把手上搭一条湿抹布（17.5–20 °C，蒸发降温），把大块面打断 |
| 灶后墙面的热晕像一根发光的柱子一直通到画面顶 | `soak` 只取锅后到油烟机下沿这一块，reach 38、strength 0.4，`onto` 限在油烟机下沿以下、挖掉锅壶罩 |
| 冰箱冷坑在地上看不出来：8–18 °C 都挤在色板最暗的一段 | 铁红色板低端提亮（0.14 → #1f0e6e，0.24 → #3d1192），曲线给 2–19 °C 留出 0–0.23；冷坑芯部降到 6.5 °C |
| 冷坑用噪声阈值做边，成了一片迷彩斑块 | `pool()` 改成从源头分出的几条软冷舌：按地面透视压扁、沿舌头衰减、再模糊 |
| 冰箱里一片死黑，格板和瓶子都看不见 | 格板前沿画成 10.5 °C 的细亮线，瓶罐比内壁高 6–8 °C；冷冻抽屉面板改回接近室温（它有保温层），顺着它往下淌的冷气才显得出来 |
| 冰箱侧板压到下柜前面，多出一条斜边 | 侧板只画台面以上那段和下柜前沿以内的 10 cm |
| 冰箱底的压缩机格栅是一道粉色横杠，挨着黑色冷坑像故障 | 删掉 |
| 猫像一块平涂剪影；Sp3 十字盖住了眼睛 | 加 `limb=`（掠射角发射率下降、毛尖更凉），胸口薄毛加 1.4 °C，后腿折线压暗；眼睛 38.6 °C 并把曲线 35–39 °C 段拉陡；Sp3 挪到胸口 |
| 后腿椭圆的轮廓变凉一圈，看着像一盘蚊香 | 后腿的 limb 降到 1.2 °C |
| 线剖面插图的曲线是暗紫色画在暗底上 | 曲线画成白线加黑描边，下面另画一条按色板着色的色带 |
| L1 虚线压在脚印上 | 虚线改成 1 px |
| 动图里蒸汽和墙面热晕出一圈圈色带，OSD 白字被量化成淡黄 | 调色板取样时饱和色 ×5、亮色 ×2，每帧叠同一张 4×4 Bayer（约 ±2.4 级）；强制留出纯白、纯黑、REC 红、最冷标记蓝和两级灰 6 个色位 |

**代尔夫特蓝瓷砖**

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

**洞穴壁画（赭石颜料）**

| 问题 | 改法 |
|---|---|
| 颜料发灰，像褪色的水彩 | 喷涂内部只剩一半覆盖（rim 0.35 × 斑驳 × 0.32 的烟）：主色 density 0.95–0.97、rim ≤ 0.2，空气里的烟降到 0.16，指数色调曲线之后再加对比度 1.18、饱和度 1.18 |
| 岩面像绗缝被、一团团棉花云 | 溶蚀扇贝纹单元 70 px、深 6 px 太规整：放大到 110 px、深 1.8 px、只在一片片区域出现；大起伏用光滑噪声会像云和烟，叠一层脊状噪声 (1−\|2n−1\|)² × 10 px 做岩脊（3 次方、振幅 22 会变成一块块台地） |
| 岩面像砂纸 / 揉皱的纸 | 低角度火光会把逐像素颗粒放大：高度颗粒从 0.55 降到 0.12，40 px 中尺度起伏只给 1.1 px，albedo 颗粒 0.022 |
| 满墙小黑点像波点，改浅后又成了白色亮点 | 小溶蚀坑减到 60 个、深度 0.3 × 半径，坑里 albedo 压暗 30%（积了泥），掠射光下就不会只剩亮边 |
| 墙上一团团「脏影子」 | 是油灯的掠射光把 80 px 的大起伏拉出长影：大起伏降到 46 px，油灯不算投影、只有篝火算，投影最多压暗 70%、soft 5 px |
| 鼓包在火堆对面投下黑团，像污渍 | 小鼓包（18 px）在掠射光下只剩投影：只给要画动物的地方放鼓包、高 26–38 px，而且让动物盖住它的背光面 |
| 折痕末端多出一道刮痕 | 有符号距离在折线末端沿最后一段的延长线翻号：按弧长在两端 220 px 内淡出 |
| 手印喷绘像红色描边的椭圆、甜甜圈 | 用「整只手模糊一次」做喷雾，细手指周围几乎没有颜料、外沿一刀切：改成 11 口气，每口一个高斯团、瞄准指尖和手侧（2/3 瞄上半部），叠加后 1 − exp(−1.8·c)，边缘自然淡出，外围撒雾点；前臂只挡一半 |
| 手印被烟熏成灰手套 | 烟熏 0.22、烟柱窄（spread 0.22），手印 density 0.95、spread 26 |
| 后半身两团黑大腿 | 腿的笔画从髋部 0.13 个身长宽起笔，涂黑时把整条大腿涂了：`legs` 部件 = 腿 × (1 − 身体)，只剩身体轮廓以下的部分 |
| 野牛头和隆肉糊成一大团黑，看不出脸 | 隆肉吹黑，头用深红 0.62；眼睛先点一个浅色杏仁（kaolin）再点黑瞳 |
| 野牛像长方箱子配桌腿 | 重画轮廓：前高后低的背线、肩上高耸的隆肉、深胸和须、腹线往后收、小屁股、短细腿 |
| 马鬃和脖子之间漏一条白缝；区域（头、腹）漏到腿上 | 鬃毛笔画压在颈脊线上；各区域只和 `body` 求交，不和整个剪影求交 |
| 鹿角像一把小梳子 | 鹿角放大、主干向后扫，5 个分叉，宽 0.04 → 0.012 个身长 |
| 裂缝像吊着的细绳、像小树枝（让上面那匹马像挂在绳上） | 改成细的之字形窄缝：两端收尖、宽度随机、深 4 px、最多一条短分叉；别从动物身上穿过 |
| 篝火是一团白光 | 火焰发光降一半，每条火舌按 2× 超采样画、只糊 1.3 px，15 条，外橙内黄，中心光斑 0.55；篝火功率 1.6、衰减距离 1150 |
| 火堆石头像骨头两头的圆钮、柴像哑铃 | 16 块小石头（11 点不规则轮廓、深色、圆顶幂 0.85）排在火堆两侧和后面；柴从火心朝观者方向辐射，按圆柱打光（顶部被火照亮）加发光裂纹 |
| 研磨好的颜料堆像平的色块 | 堆高 1.3 × 半径、颜色边缘放软，低角度火光才照得出一面亮一面暗 |
| 掉色的小片像彩色纸屑、像白灰尘 | 12 点圆滑小片、1.5–4 px、只掉在覆盖 > 0.6 的地方、28 片；露出的石面 × 0.93，不加高差（否则掠射光给每片一圈亮边） |
| 炭条起稿在动图里看不见 | 起稿线是一条约 2.6 px 宽的带（先按线宽糊一下再取 0.12–0.88 的等值带），强度 0.7，画两遍 |
| 炭笔轮廓像一串珠子 | 覆盖 = 线带 × (0.5 + 0.5 × 抓附)，不要全靠岩面「牙口」 |
| 野牛尾巴尖像棒棒糖、火星像雨丝 | 尾尖改成一笔短而粗的黑色笔触；火星减到 11 颗、2–6 px、只在火舌上方 |

**1-bit 早期画图软件**

| 问题 | 改法 |
|---|---|
| 写一行 Shadow 样式的字，整张画被擦成白的 | `Image.fromarray()` 出来的图是只读的，`ImageDraw.floodfill` 在只读图上静默不做事，找字腔的泛填就把整张画都当成了字腔；先 `.copy()` 再填（油漆桶 `bucket` 用的是同一个泛填） |
| 蝴蝶放在格子布窗帘和云前面完全看不见；套索的行军蚁把背后的窗帘图案也框进去，一团乱 | 小东西放到最空的底上（天空的白带）；蝴蝶改成白翅膀 + 黑翅尖 + 黑点，1-bit 里白底黑边最好认；成品的选区用矩形选框，套索只在纯白底上用，或把物体自己的遮罩传给 `select(lasso=)` |
| 窗台下的喷枪阴影像一条脏草地，花盆脚边和云底的喷点像乱涂 | 喷枪只在窗台下沿浅喷一道（半径 8、密度 0.22），上面先垫一条 50% 灰图案；花盆投影改成灰图案小椭圆；云底不喷 |
| 窗外的山、草地、栅栏全是图案，花盆糊进背景 | 删栅栏，草地换最稀的 `dots`，山用 25%；花盆加深（盆身 50%、背光侧 75%），盆沿最浅 |
| 天空顶带用 12.5% 太密，窗户反而不比墙亮 | 天空 `mist → faint → 白` 三条带，墙纸用 `sprigs`：窗户（光源）是全画最亮的地方 |
| 窗外的圆树正好在苗或向日葵后面，像花上长了根棒棒糖；窗户竖棂正好在第 14 天那盆苗后面，像插了根支架 | 远景小物不要和前景植物重叠（删了树）；盆往旁边挪，避开竖棂 |
| 右边窗帘的坐标没镜像，下半截藏在黑猫后面 | 只画左窗帘，`copy(rect, to, flip=True, mask=窗帘遮罩)` 翻转复制到右边（当年的 Flip Horizontal）；带遮罩，背后的墙纸不跟着走；猫挪出窗帘 |
| 正面坐的黑猫是一团，胡子画在窗帘上 | 改成侧面：椭圆臀、斜椭圆胸、前腿、头、口鼻、两只三角耳拼成剪影，再用白线勾腿和臀的分界、项圈、耳内和眼；胡子用 XOR（`invert`），在黑脸上是白、出了脸是黑 |
| 喷壶嘴和水滴压在格子布窗帘上读不出来 | 喷壶挪进窗洞，壶嘴尖对准第 2 天那盆的盆沿，只留一滴水；左边窗台改放种子袋，标签行补上 day 0 |
| 两盆挪近后 day 2 和 day 14 的标签撞在一起 | 标签中心不跟盆走，单独给一组坐标 |
| 放大镜窗压在主窗口标题栏上 | 放在这一阶段还没画的日历位置；放大范围框住眼睛、耳尖和一点墙纸，才看得出「一格一格」 |

**古希腊黑绘陶瓶**

| 问题 | 改法 |
|---|---|
| 马像趴在地线上游泳：肚皮离地只有 0.1 个马高，四条腿水平伸着 | 身体抬高（肚皮 0.43、鬐甲 0.93 个马高）；近前腿高高折起、远前腿向前下够地、两条后腿向后下蹬，蹄子落在地线上 |
| 驾车人比马背还矮，像个小玩偶 | 车厢抬到轮轴上方，车夫身高 0.9 个马高、前倾 0.24，头和马耳平齐；胸墙挡住白袍下半截 |
| 白马夹在马队中间，只露几条白腿 | 白马放在最远的一匹，头抬得最高（颈部弯折 0.2），并且给瓶子正面中央的那辆车 |
| 颈部棕榈叶饰像一排电线塔：花瓣是直刺，卷须竖着往上走 | 9 瓣圆头扇形（中间长两边短），红色掌心描一道刻线；卷须改成垂花弧，从掌心下方荡到莲花挂点；莲花一长瓣加两瓣外卷 |
| 左边马队上一大片白雾，像多了一匹白马 | 那是大柔光箱在黑釉上的反射：箱子收窄成一条竖光（反射方位角 -0.90..-0.76）、强度 9 → 6，另加一层很弱的大面积柔光 |
| 圈足正中一个白三角 | 是环境里「天花板」方框光源在圈足顶面的反射，改成一层很柔的穹顶光 |
| 做旧过头：结壳成片白云，根痕太亮，加白剥成斑点狗 | 结壳只在下半身、阈值提高、强度 0.7；根痕透明度 35–75；加白只按大块剥掉约 20%，剥处留 20% 和一层哑光残影 |
| 修补填料是一个太规整的浅米色椭圆，缺口是白色小三角 | 填料轮廓加 0.42 的 fbm 抖动、调成偏暗的赭橙，黑色部分补成灰黑，外面几道胶合裂缝；缺口用 24 点 fbm 轮廓，露出的胎色改成暗橙 #c98a60 |
| 圈足的黑釉像木纹 | 薄釉发红的横向条纹噪声太强：釉厚底数提到 0.78、条纹权重降到 0.08；未烧泥釉的条纹也一起减弱 |
| 把手像两根铁丝；粘土上拉坯横纹太显 | 管径 0.046R → 0.072R；拉坯纹的法线扰动 0.018 → 0.009，只在反光里隐约看得见 |
| 动图里暗墙聚光灯和素坯出一圈圈色带 | 调色板从所有关键帧加权取样（饱和色 ×5、亮色 ×2）再中值切分，每帧量化前叠同一张 4×4 Bayer（约 ±2.4 级），透明占位色用品红 |

**铅笔素描**

| 问题 | 改法 |
|---|---|
| 轮廓线几乎看不见，整幅发白 | 1.5 px 的细线抗锯齿后每个像素覆盖只有一半，纸纹阈值又按覆盖算，线被吃成稀疏的颗粒：笔尖能压进纸纹多深按 √覆盖 算（按压力，不按像素覆盖）；勾线的石墨量 ×2（`gain`），散笔 ×1.6，顺形排线 ×1.3 |
| 纸像粗纹水彩纸，满屏一块块斑 | 纸纹以约 1.6 px 的细颗粒为主（细的一层 σ 0.3 倍，粗的一层 σ 1.3 倍），毛毡纹只占 0.05，浮雕光 0.07；细颗粒 σ 到 0.7 就成了砂纸 |
| 侧锋铺调一条条斜带、一块块云斑 | 三遍、每遍角度差 11°，行距 0.42 倍笔宽，压力只抖 ±10%，笔锋边缘柔化 0.22 倍笔宽；侧锋笔画按 8 px 重采样（连同栅格化提速，大面积侧锋快约 3.6 倍） |
| 排线块与块之间的接缝成了一道道亮带 | 收笔渐细只占笔长的 20%（原来 32%），每笔在接缝处多出或缩回 ±3 px，接缝每行漂移一点 |
| 边缘「只剩线稿」像喷枪渐隐 | 调子按 finish^0.6 衰减之外，排线和侧锋按笔画中点的 finish 整笔整笔地丢，越往外越稀；线条在纸边保留 35% 压力 |
| 纸擦笔把画面边上的灰抹到对面去、顶边出黑团 | 拖抹不能用 `np.roll`（会卷绕），改成边缘延伸的平移 |
| 车身周围一圈白边 | 擦笔在遮罩里做归一化模糊（`contain=True`）：只匀开遮罩内的石墨，不把车身那块空白「抹」进墙 |
| 墙上的车影像一辆糊掉的幽灵车 | 影子不带辐条，边只模糊 1 px，只用排线不用侧锋铺底，灰泥墙晕染时绕开影子，调子降到 0.4，车本身先被读到 |
| 转角侧墙成了一块奇怪的灰色楔子 | 楼太矮（顶边只到 y −60，相当于 1.6 m 高），顶边斜着落进画面：顶点放到 y −1400（三层楼），侧墙远端用噪声参差地收掉，招牌处挖空 |
| 车架是一条白色剪影，只有两根细线 | 车架当成深色漆管：沿管子顺形排线，越往背光侧越重，最外缘留一点反光，再用纸擦笔顺着管子匀一遍，最后橡皮擦出一道清楚的高光 |
| 法棍几乎全白 | 先侧锋铺一层面包皮的底色，再沿面包长轴两遍交错的顺形排线，下沿压一条 4B；刀口用可塑橡皮提亮，下唇再描一道深线 |
| 门是一整块深灰，抢了车 | 门降到 0.42，做成四块凹板：上沿和左沿一条暗边、下沿和右沿用橡皮擦出亮线；最深的只留门洞左壁和顶 |
| 页边笔记压在石子路上读不出 | 笔记和色阶两块区域不画石子轮廓，也不排线 |
| 色阶下面的 2H–8B 看不清 | 字号 22、用 2B、压力 0.95 |
| 出图 40 秒、峰值 1 GB | 栅格化时每段的宽度和灰度先整体算成列表；遮罩（多边形、粗线）只在包围盒里画；坐标用广播的行列向量而不是满幅 mgrid；纸纹用 float32 的小核卷积；用完的满幅遮罩及时 `del`：11 秒、约 0.72 GB |
| 动图 2.07 MB | 纸纹颗粒每次叠化都整片重编码：叠化帧里和屏上已显示颜色只差 ≤ 7/255 的像素沿用上一帧（透明），1.26 MB |

**X 光片**

| 问题 | 改法 |
|---|---|
| 恐龙骨架是全画的主角，却又淡又小，头骨被箱子圆角切掉一块 | 骨头半径和厚度都 ×1.6（铸的玩具骨头本来就粗），整体放大到 1.02 倍；脖子放低、头骨下移 22 px、后移 6 px，整副骨架挪到圆角以内 |
| 整幅画太暗，物体像沉在墨水里 | 显示曲线满白点从 A=11 降到 8.5、拐点 0.32 → 0.30；荧光辉光 0.35 → 0.5 |
| 毛衣和牛仔裤看着像比空箱子还暗的「黑垫子」 | 量了一下其实比空箱子亮（红通道 35 对 19），是被亮的折边衬暗了；密度提高（毛衣 0.33 → 0.5、牛仔裤 0.9 → 1.15），加针织 / 斜纹纹理，折边才显得是布 |
| 材料伪彩视图整片橙色：橡胶传送带也算有机物 | 真机做空气校准时传送带就在里面：`belt()` 记下自己的衰减，伪彩视图先减掉它，空处才是白的 |
| 骨架里穿的钢销把 Zeff 读数拉高 | 读数先用物体外一圈的中位数扣掉背景，再取逐像素 A_lo/A_hi 比值的中位数（不用总和之比），石膏读 14.4、水读 6.9 |
| 图例「INORGANIC」挤进了 METAL 色块 | 图例按字宽排，不按等分 |
| 结论表的字跑出侧栏 | 每行压到 40 字符以内（16 px 等宽） |
| 放大插图写着「×0.8」：框的是整副骨架，其实是缩小 | 只框头骨和胸腔，放大约 1.4 倍 |
| 1 号标签压在箱子亮边和密码锁上，看不清 | 标签文字下垫深色底板；读数和标签放同一行 |
| 八根伞骨偏移量正负对称，两两重合，看着只有四根棍子；伞面几乎看不见 | 伞骨绕伞杆的相位错开 0.3 格；伞面 14 层、密度 1.3，加弧形折痕 |
| 传送带接头（一列钢钩）挨着侧栏，像一条拉链 | 挪到画面最左边 |
| 动图用一张调色板时，伪彩插图里的绿骨架变成灰蓝，CLEAR / REMOVE 发白 | 调色板分两段切：蓝色胶片像素切 186 色，彩色像素（橙、绿、红、琥珀）切 69 色；每帧叠同一张 4×4 Bayer（约 ±2.4 级） |
| 峰值内存 0.86 GB | 散射雾在 1/4 分辨率上算；模糊改用切片视图（不用 `np.take` 复制）；OSD 辉光改用 Pillow 的 uint8 模糊；暗角用广播不用 `mgrid` |

**1930 年代黑白橡皮管动画**

| 问题 | 改法 |
|---|---|
| 画面太干净，像矢量插画套了个滤镜 | 镜头柔焦 0.85 px、四角再糊一档；颗粒 0.07、按 √(v(1−v)) 在中间调最重，再叠一层半分辨率的团粒；黑位抬到 0.075、白位压到 0.93，再加片门晃动和圆角片门 |
| 太阳的拳头像带盖的玻璃罐、盐瓶 | 拳头 = 手掌椭圆 + 顶上一排 4 个小圆（卷起的手指，成扇贝边）+ 指缝短线 + 横在前面的拇指；袖口缩短到 0.36 |
| 睡帽帽檐是一个扁椭圆，横在枕头上像一圈光环 | 帽子扣在枕头右上角，帽身从角上长出来往右下耷拉，帽檐改成沿帽口的一条宽带；角色头顶不要放任何扁椭圆 |
| 枕头像方盒子、像吐司 | 超椭圆指数 0.5 → 0.72，四边中点往里收 13%、四角往外顶（枕头角），不倾斜，四角加折痕短线 |
| 拖鞋像礼帽、像汉堡 | 稍微俯视来画：长椭圆鞋底 + 后半开口露出鞋里（浅色鞋口、中灰内底）+ 只盖住前半的毛绒鞋头 + 绒球，眼睛画在鞋头上 |
| 太阳一圈尖三角像参考帧里的太阳（也像皇冠）；改成细波浪线又像睫毛、小虫 | 扇贝边光晕 + 每个凹口一道粗短的放射短线（长短交替、两端略收） |
| 「RRRING!」字母挤在一起 | 字距 0.78 → 0.9 倍字宽；单双号字反向倾斜 ±10°、上下错开 0.12 倍字号 |
| 踢腿的速度线贴着床头柜像裂缝，跳起的拖鞋下面的竖线像钉子 | 去掉贴着家具的速度线，在踮脚的鞋尖外画三道放射短线（敲桌面）；跳起的拖鞋下面画两道「︶」弧线 |
| 绗缝被的棋盘格太抢眼 | 深格只压暗 0.17（原来 0.3） |
| 地板一大片空 | 窗户投下一块梯形阳光（软边 9 px、提亮 0.45）和一道窗横档的影子，拖鞋就在阳光里跳 |
| 动图里铅笔稿几乎看不见 | 铅笔画两遍（1.7 px / 1.1 px），强度 0.8 |
| 动图 2.34 MB | 胶片颗粒让每次叠化都改掉大半像素：和屏上已显示的颜色相差 ≤ 8/255 的像素沿用上一帧（记成透明），自检按实际显示的帧比对，1.54 MB |

**黑白麻胶版画**

| 问题 | 改法 |
|---|---|
| 天上的白色风痕又多又宽，夜空成了一片灰白，大块黑白对比没了 | 风痕从 520 条减到 300 条，宽度从 2–6.5 px 改成 1.6–5 px；只在两条斜云带里刻密，月亮 215 px 以内不刻；天空保持六七成是黑的 |
| 月亮上刻的三个黑斑像一张笑脸 | 去掉月海，只在背光一侧留 5 条同心弧做明暗（V 刀，宽 2.2 → 4.2 px，越靠边越粗）；光环每段 0.35–1.2 rad、缺口 0.15–0.6 rad，否则像靶心 |
| 炊烟飘过白色雪坡就看不见，只剩两根黑线；改成一串圆团后，又像一串珍珠、像毛毛虫 | 烟是一串互相压住的团：按弧长累计「半径 × 0.8」排开，越往上越大，铺满整条路径；穿过白色的地方留一圈 2 px 黑边（`outline(cut=False)`）；每三团留一道黑色卷纹；两股烟的控制点各加随机偏移，免得一模一样 |
| 烟囱像一架梯子 | 不再刻一排横缝，只刻两道短灰缝，顶上加一顶白雪帽 |
| 老树根部是一大块黑三角 | 根部外扩从 1.9 倍干宽降到 1.05 倍 |
| 树梢一截截平头，像修剪过 | 末梢一级的宽度收到 0.5 px（`brush` 的 `end`），高处的分叉改成 1–2 枝 |
| 人物站在黑房子前，头和墙糊成一片；脸挖成一个白圆，像幽灵；雪花刻在脸上，像一颗星 | 人物挪到雪地上（头顶低于雪野边缘）；脸改成朝左的侧脸剪影（额头、鼻尖、嘴、下巴），留一个黑点做眼睛；`speckle(region=)` 避开人物、狗、柴堆和灯笼 |
| 雪橇上的柴像长凳、像木箱 | 改成稍从后方看的柴垛：六根原木的截面排成 3-2-1，白色截面上留年轮和一道裂纹；木身是黑的，顺长刻两道树皮缝 |
| 黑版像压了浮雕，每道白刀痕都有一亮一暗的斜边 | 压印凹凸只留一点：法线明暗 × 0.3，限幅 ±3.5% |
| 套色像机器印的，平得发假 | 套色版加 mottle 0.25：浅色油墨更显纸纹和墨层不匀 |
| 清底的残刀印像头发丝、像铅笔划痕 | 改成顺下刀方向的直短线，1–3 条一组平行（相邻几刀之间的刀脊），数量减到原来的约 2/3 |
| 门前的光先是一个规整的梯形，后来又成了靴子形 | 远端用正弦加随机做成参差边，左右都往外张成扇形；套色版上横着用 U 刀挖几道，黑版的雪脊线照样从光上穿过 |
| 动图里的灯黄被量化成米色 | 中值切分 238 色，再从饱和像素（饱和度 > 0.28）里单独切 16 色补进调色板；透明占位色用品红 |

**VHS 家庭录像**

| 问题 | 改法 |
|---|---|
| 落地灯那一列从画面顶到底一整条白，墙面也被冲白 | CCD 竖向拖影改成按列累加「远超满阱」的溢出（阈值 2.2，只有烛焰这种点光源够得上），不再取每列最大值；灯罩墙上的光晕从 0.9 / 0.45 降到 0.38 / 0.2；泛光阈值 0.85 → 1.0、拖尾阈值 0.95 → 1.2 |
| 被烛光照亮的白奶油也越过阈值，拉出一根宽宽的橙色光柱 | 烛光 0.42 → 0.3、半径 300 → 280；拖影只认 2.2 以上的溢出 |
| 灯罩是一块灰白的平方块，被小彩旗压住，看不出是灯 | 灯罩下移 60 px，避开彩旗；自发光带左右明暗，上下加黄铜边、顶上加灯头和顶珠，外面再加一圈暖色辉光 |
| 前景孩子的上身是一块和墙纸同色的芥末黄长方块 | 换青绿色 ringer T 恤，和满屋的橙撞开；轮廓重画：头大、肩斜，上臂单独画到手肘，前臂伸向桌子，肘和身子之间露出背景；加肩胛骨暗线、发旋放射的发丝、两只耳朵、朝蛋糕一侧的暖色轮廓光 |
| 派对帽太小，蓝白条纹被墙纸吃掉 | 帽子放大到头半径的 1.75 倍，红黄螺旋条纹，朝蛋糕歪 24°，顶上一团锡箔绒球，帽子在头上投一点影 |
| 刚吹灭的蜡烛冒出的烟像几根发光的白棍，过了录像带像又多出几根火苗 | 烟改成灰色、不发光：从细到粗、越往上越淡、带卷曲的一缕；另外「烟量 1.0」和「点着」用的是同一个数，蜡烛状态改成 `'lit'` / 0–1 烟量 |
| OSD 的 0 看成 8，W 看成 U / H，PM 看成 PN | 字符发生器把每个点向右加粗，1 点宽的缝会被填死：0 去掉斜线，W、M 改成 7 点宽 |
| 变焦条的刻度和细边框在录像带上糊成一团 | 用和字体同一套点阵画：外框 + 实心填充 + 一根游标，不画刻度 |
| 泰迪熊坐在锈红沙发上，同色看不见 | 沙发改牛油果绿丝绒，熊改蜂蜜色 |
| 圆环墙纸对比太强，满墙抢戏 | `contrast=0.72` 把图案色往底色收；加纸幅接缝和几像素的错位，看着是贴上去的墙纸 |
| 电视屏幕中间一团橙色反光，像屏幕上破了个洞 | 改成窗户在屏幕左上角的一块冷色反光 |
| 黄色小旗上的白字看不见 | 按旗色亮度自动换字色：浅色旗用深棕字 |
| 掉磁白点一样长，满屏像下雨 | 数量 45 → 24，长度按指数分布：多数是一两个采样点，偶尔一长条 |
| 不存阶段快照时 `stage()` 也做一遍完整合成，出图 13 秒；峰值内存 1.15 GB | `keep_stages=False` 时 `stage()` 什么都不做（范例按有没有 `--stages` 设）；泛光的两个大半径在 1/4 分辨率上做；大彩色图的模糊逐通道做：6 秒、0.85 GB |

**扁平矢量**

| 问题 | 改法 |
|---|---|
| 旧版「周末书店」被用户否掉：东西堆满一整面墙，无五官的「企业扁平风」人偶比例别扭，满屏单一蓝色显得压抑 | 重做成风景：几层大形状（三角山、波浪丘、圆月）加大片留白的天空；人物只留一个 70 px 的剪影；夜蓝、紫的冷色对橙、黄沙的暖色，一共 7 色 |
| 层内纹理像木纹，月亮和云上一道道竖纹 | 纤维纹幅度 1.6% → 0.8%，条纹改短改细（14 × 2 px 网格），每层取不同偏移；全画颗粒 1.1% |
| 云像一条面包：底座是粗圆角矩形，下面一整条深色底带 | 三四个大小不一的圆坐在同一条平底线上，下面垫一条薄药丸；暗面 = 云减去朝光源挪动后的自己，只剩右下一道月牙 |
| 半透明烟柱压在紫山和品红山丘上，又灰又脏 | 删掉烟；半透明形状只放在单一底色上（沙地上的光圈、头灯光束） |
| 火焰底部被平切，像蜡烛；木柴藏在火后面；围石是突兀的蓝紫色 | 火焰用 `teardrop()`（圆 + 两条切线收成尖），外层加两条侧舌，三层套叠；木柴交叉压在火脚前面，锯口画一圈浅色；石头改成淡紫灰 |
| 背包客的橙色背包、帐篷的橙色尖顶贴着橙色山丘带，就看不见了（没有描边） | 把人和帐篷整个挪到黄沙上，让轮廓四周只有一种对比色 |
| 小路走到雪线就断了：奶油色虚线落在雪顶上看不见 | `trail()` 返回遮罩，把 `path & peak['snow']` 改成紫灰色，路一直通到山顶小旗 |
| 篝火光圈看不见；火星飘到山丘带上，看不出和火有关 | 光圈 4 层，每层 alpha 0.2，颜色 `tone(SAND, 0.5)`；火星只出现在火焰上方 120–190 px |
| 动图里，大块图层交接（夜蓝 → 橙 → 沙）的叠化帧满是粗杂点 | 调色板样本里加上 1/3、2/3 两张叠化帧；叠化帧只在两张关键帧不同的地方叠一张固定的 4×4 Bayer。整帧都叠是 1.5 MB；改用 Floyd–Steinberg 有 1.97 MB，还会抖到品红透明占位色，5 帧对不上 |

**绘本角色动画**

| 问题 | 改法 |
|---|---|
| 远山又高又满，压掉大半天空；两岸之间、水面上面露出一条米色纸缝 | 远山顶线压到 470–660，薄荷远山的底伸到画面底边（藏在两岸后面），淡紫远山的底停在 760（藏在薄荷后面）；淡紫的「提前量」比薄荷小（300 对 360），动画里淡紫的下沿永远不会露出来 |
| 总图里关键姿态挤成一团：落地压扁和预备动作在同一个点叠在一起，钻土的残影躲在小树苗后面，终点那片橡叶和漂流时的橡叶重叠成两片 | 只留沿路分得开的六个姿态（下落拉伸、落地压扁、滚动、飞跃、漂流、空翻）；终点的发芽用「最后一帧」本身（`final=True` 画出树苗顶上的橡果帽）；`props=False` 不画道具终点位置，只画和角色同一时刻的橡叶残影 |
| 落地压扁那一帧头顶冒出几根竖直速度线 | 速度线按前一帧的速度自动加，落地帧前一帧还在高速下落：冲击帧的姿态写 `speed=False` |
| 蜡笔短线一根都没画上 | 「内部」判断写成 blur(a) > 0.97，而水彩层不透明度只有 0.96–0.97：改成相对阈值 0.97 × a.max() |
| 蜡笔短线一出来就碎成麻点，像一行行小字 | 1920 宽时纸纹太细，按纸纹断线就成了点：改用 3.5 px 的粗颗粒，断得少；短线减少、加长加粗（44 × 5 px），透明度 0.55 |
| 河面上的白色反光像潦草的字 | 改成 16 根 80 px 长、略往上拱的白色长笔触，越靠近水面越密（top_bias），再加 9 根往下弯的深蓝波纹 |
| 树冠上的点缀先像圆点病斑，后像迷彩方块 | 换成三十几片小橡叶形「印」上去（两种秋色、半透明），树冠右下的暗面月牙加宽（偏移 40, 46 px） |
| 挂橡果的树枝被树冠盖住，看着像橡果悬在空中 | 缩小右边那团树冠，让树枝梢和挂果的小枝伸出树冠；树干、树枝的层放在树冠下面 |
| 手写字顺序不对：「little」先写了后半截，开头的 l 最后才出现 | 起笔点选「去斜体后最靠左」的端点：键值从 x − 0.3y 改成 x + 0.35y（向右上斜的字母，顶端比底部靠右）；720 宽时发丝线断掉，文字遮罩加 1.6 设计像素的笔宽 |
| 跟着角色画出来的远山、山坡，前沿是 120 px 宽的一团雾 | 柔边写成层宽的比例（0.06 × 2000 px）：改成最多 14 设计像素，前沿成了一道干脆的湿边 |
| 开场 0.2 秒整块绿色山坡就画出来了，右边一道竖直的「悬崖」挨着树 | 开头只画树和墨线地平线；山坡的绿色和远山放到「看树叶」那一秒（1.95–2.9 秒）先画左边一段（`pre=`），其余跟着角色滚下去再画（`follow=`） |
| 钻土时溅起的土粒一直掉到草地里去 | 土粒落回地面以下就不画 |
| 钻土的头一两帧，橡果被地面裁出一道笔直的横边 | 土堆在钻土开始 0.1 秒就弹出来，把裁切边盖住 |
| 彩纸屑又小又全压在字上 | 纸屑放大（10–19 px），从字下方炸开、横向散得更开（spread 1500、起点宽 640） |
| 12.5 fps 时滚动一帧转四五十度，有点跳 | 改成 15 fps；GIF 延时只能写厘秒，按累计取整写成 7、7、6 厘秒交替，平均正好 15 fps |

**圆珠笔涂鸦**

| 问题 | 改法 |
|---|---|
| 蛇太细像蚯蚓，棋子小得读不出 | 蛇头宽 54 / 44 / 38 px（约半格到六成格），头比脖子宽；蜗牛、云放大 1.1–1.3 倍，云的脸 84 px |
| 梯子横档和格线从蜗牛、云身上穿过去 | 先画棋子，后画的蛇、梯子、格线都用棋子遮罩 `clip` 掉（笔走到已经画好的东西前就停住）；格子上色也绕开蛇和棋子 |
| 跳格的红虚线像一串锯齿 V | 每跳一格用一条 14 点的抛物线弧（高 24 px）配箭头，不用三点样条 |
| 跳格的计数 1–4 压在格子编号上，「1」落在竖格线上整个看不见 | 弧的起止放到格子下部 0.4 格，数字放在弧顶、往右偏 13 px，离开格线 |
| 「+24!」被竖格线劈开、「nooo~」被汗滴和云挤住 | 标注整块放进一个空格子里；云只留一颗汗滴放在侧面，去掉两只手 |
| 折痕成了贯穿全画的一道亮白线 | 折痕的谷只深 0.1、宽 3 px，沿线加一点摆动，主要靠两侧纸面坡度不同带出的明暗 |
| 上一页透过来的无墨压痕字像白色浮雕字 | 盲压的槽深 ×0.55，只在侧光下隐约可见 |
| 手写字母互相撞（slow 看成 dow） | 每个字母的步进按它自己抖动后的字号算，字距默认 1.04，步进抖动降到 2% |
| 冒号、i 和 ! 的点丢了 | 字形骨架里小于 0.11 字号的连通块全部当「点」画，单像素的也算 |
| 格子编号末尾的墨团像小数点 | 小号数字的 gloop 降到 0.15 |
| 蛇头背后缺一段轮廓；鼻孔和嘴像多出来的眼睛 | 头的弧画到 ±148°，身体两侧从路径第 4 个点开始；去掉鼻孔和嘴，只留墨眼、彩铅腮红和红舌头 |
| 红笔沿梯子的虚线箭头从蜗牛壳上穿过去 | 箭头放到梯子没有棋子的那一侧（+40 px），再用棋子遮罩 `clip` |
| 墨线旁边的压痕亮边太抢、像浮雕 | 压痕打光增益 0.16 → 0.13，上限 ±0.1 |
| 动图里蛇和格子的彩铅颜色被量化成土褐色 | 两段调色板：150 色从「有色像素 ×5」的样本里中值切分，另外 104 色只从有色像素（饱和度 > 0.12）里切；49 帧约 0.6 MB |

**描图纸叠层**

| 问题 | 改法 |
|---|---|
| 三张描图纸叠在一起，整张图发灰发脏，背光纤维像大理石纹 | 描图纸透过率 0.955 → 0.98，云纹幅度 5% → 2%、尺度改细（6 / 22 px）；底图纸的云纹只留 1% |
| 抬起的纸下面糊成一片、整块发暗 | 漫射模糊 σ 5.5 → 2.8 px（描图纸），阴影不透明度 0.30 → 0.22，落在纸下面的那部分阴影再减半（室内光还能透过纸照下来） |
| 胶带像一块灰色塑料片 | 胶带是皱纹纸：一半透光、一半反射室内光（I·T·0.58 + T·0.36），颜色用暖奶油 `#f7ebcf`，皱纹和纤维只压暗 3–4% |
| 胶带贴在黄色公园上，成了一块橄榄色斑 | 胶带别贴在色块上：挪到纸边经过街区的地方，或者换个角 |
| 卷角成了一条灰色斜带，像脏印子 | 阴影带收窄（0.11R、只暗 7%），加一道折痕高光；卷角只放在空白页边，蓝片那个落在叠层最密处的卷角干脆不要 |
| 站点圆里的反白数字看不清 | 反白就是「露出下面一层」：站点压在深色地标（车站、集市楼、城堡、灯塔）上，数字就变成深灰。把站点挪到浅色街道、公园或水面上 |
| 步行路线和电车线在同一条路上叠成一条紫黑线 | 同一条路上分道走：电车偏左 4 px，步行偏右 6 px |
| 电车线从路名「STATION ROAD」上穿过去 | 把路名放到别的路上，或者删掉 |
| 公园和马路之间剩下 8–15 px 的细条街区，像一串虚线 | 递归切分的叶子块，按短轴厚度（3.46 × 短轴标准差）小于 12 px 就丢掉，留成空地 |
| 动图 5.1 MB：每落下一张纸，整片带纹理的区域都重新编码 | 见第四节：只重发明显变化的像素，开灯的叠化帧不加抖动；1.9 MB |
| 跳过小变化以后，灯箱渐变和海面上出现一圈圈等高线似的色斑 | 差值拆成平滑分量（模糊 2 px）和细节残差分开判断；停 900 毫秒的关键帧把平滑分量追到 3 级以内；开灯那几帧逐像素精确发送 |

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
- 后来新增的十六种（岩画到刺绣徽章）动图又反复用到几条通用做法；改版的动图脚本放在各画风自己的工作目录（如 `claude_drawing/mosaic_work/`），没有进仓库：
  - 加权调色板：取样时饱和像素 ×5 左右、亮色 ×2；红、金、橄榄绿这类面积小的点睛色加权也抢不到颜色时，单独给它们留调色板位（先中值切分出约 240 色，再从这类像素里单独切 6–14 色补上；饱和色多的可按色相区等量抽样，单独分几十色）。
  - 大片渐变、深色上的反光出色带：量化前每帧叠同一张固定的 4×4 Bayer 抖动（约 ±2.4 级）。
  - 满屏网点或硬边像素（漫画网点、低多边形）缩到 720 宽时用 BOX 不用 LANCZOS，否则网点成摩尔纹、硬边出振铃，体积也更大。
  - 满屏细纹理（灰泥、石子、玻璃）每次叠化都会改掉大半像素：叠化帧里和屏上已显示颜色只差一点（约 10/255）的像素沿用上一帧、记成透明，自检按实际显示的帧逐帧比对；墓室壁画、马赛克、彩色玻璃花窗都是靠这一条（再加各自的小改动，见第三节）把动图从 3 MB 多压到 2 MB 以下。
- 这一批十五种（蓝图工程图到绘本角色动画）又多了几条：
  - 满屏几乎一种色调（X 光片的蓝胶片）时，补几个色位不够：按「主色调像素 / 其余彩色像素」两段分别中值切分（186 + 69 色）；OSD 里必须精确的纯白、纯黑、REC 红这类颜色直接强制占色位（热成像、VHS 家庭录像），否则白字被量化成淡黄。
  - 大块色层整片交接的叠化（扁平矢量的夜蓝 → 橙 → 沙）：调色板样本里加上 1/3、2/3 两张叠化帧，Bayer 只叠在两张关键帧不同的地方（整帧都叠更大；Floyd–Steinberg 更大，还会抖出透明占位色）。只有黑白两值的画风（1-bit 早期画图软件）缩小用 BOX、配固定灰阶调色板，不做中值切分。
- 描图纸叠层的动图（脚本在 `claude_drawing/overlay_work/make_gif_overlay.py`）：阶段是 关灯 → 灯变暖 → 开灯 → 底图 → 每张叠片「抬起、偏着」→「放下」→ 胶片图例卡 → 贴胶带。一张纸落下，会让一大片带纹理的区域整体变几级、线条由糊变清，逐帧精确差分要 3–5 MB。做法：目标和屏上已显示颜色的差值拆成平滑分量（模糊 2 px）和细节残差，平滑分量超过阈值（叠化帧 12 级、关键帧 3 级）或单点超过阈值（30 / 16 级）才重发，只有单点超阈值的孤立像素（纸纹在阈值上下翻动）不发；开灯那几帧逐像素精确发送，其中的叠化帧不加抖动（加了每帧每个像素都变）；最后一帧收紧阈值追平。73 帧约 1.9 MB，按解码结果逐帧自检。
- 绘本角色动画的动图是真动画，不是阶段叠化：`Storybook.gif()` 按时间逐帧渲染，720×405、15 fps（GIF 延时只能写厘秒，按累计取整写成 7、7、6 厘秒交替），共用一张加权调色板 + 固定 4×4 Bayer，没变的像素记成品红透明，151 帧（动作 9.95 秒 + 末帧停 1.4 秒）约 0.56 MB；范例加 `--gif out.gif` 出这张，`--stages` 的关键帧仍可喂给上面的阶段动图工具。
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
lib/petroglyph.py      岩画（凿刻砂岩：沙漠漆、锤击凹坑、磨刻、剥落）
lib/tomb.py            古埃及墓室壁画（灰泥、红格红稿、分栏、象形文字、剥落）
lib/mosaic.py          罗马马赛克（底稿取色、沿轮廓排石、光环、灰缝、铭牌、脱落）
lib/stainedglass.py    彩色玻璃花窗（玻璃切块、grisaille 彩绘与银染、铅条焊点、透光）
lib/illuminated.py     泥金手抄本（羊皮纸、宽头鹅毛笔哥特体、打磨金箔、尺规图解）
lib/codex.py           达·芬奇手稿（铁胆墨水鹅毛笔、左手排线、红粉笔、尖笔圆规、镜像手写、机械零件分解图）
lib/silhouette.py      剪影（黑纸剪影、薄金粉、椭圆金框、木版印花墙纸）
lib/letterpress.py     凸版印刷海报（木活字、红黑双色错版、木刻插图）
lib/constructivism.py  苏联构成主义（红黑两版、套印错位、网点照片拼贴、剪刀留边、折痕老化）
lib/artdeco.py         装饰艺术（Art Deco 流线型海报：喷枪渐变 + 遮片硬边、交替射线、阶梯高楼、3D 流线型列车、Deco 字母）
lib/comic.py           黄金时代漫画（毛笔墨线、Ben-Day 网点、四色错版、新闻纸）
lib/popart.py          波普丝网（沃霍尔式：手涂撞色平涂、错位的照相黑版、刮印的墨不匀）
lib/lineprinter.py     ASCII 字符画（行式打印机：绿条连续纸、按区域选字、叠打、色带渐淡）
lib/lowpoly.py         低多边形（1999 年代 3D：软件光栅化、平面着色、仿射贴图、逐顶点雾、15 位色抖动、点阵 HUD）
lib/stencil.py         喷漆模板涂鸦（清水混凝土墙、卡纸模板与桥、喷雾、滴痕）
lib/patch.py           刺绣徽章（牛仔斜纹、填充绣 / 缎面绣、锁边、热切边、手缝针线）
lib/blueprint.py       蓝图工程图（描图布墨线、单笔画字、制图规范、接触晒图、折痕水渍、红蜡笔批注）
lib/crayon.py          儿童蜡笔画（糙纸纸纹、宽头蜡笔来回涂、出界、蜡层堆积与压光、圆头蜡笔写字、纸上的真蜡笔）
lib/crt.py             绿屏终端 CRT（字符内存与 5×7 点阵字库、按材质和边选字、扫描线电子束、荧光余辉与烧屏、桶形畸变与光晕、米色机壳）
lib/thermal.py         热成像（温度场：物体温度、发射率、热晕、热气羽流、冷气舌、余温脚印、釉面反射；热像仪：低分辨率传感器、噪声与竖条纹、细节增强、手调曲线 / 直方图均衡、伪彩色板；读数 OSD）
lib/delft.py           代尔夫特蓝瓷砖（锡釉砖墙：刺孔粉印、钴蓝勾线与晕染、生坯到入窑、逐块错位、单块砖角饰、勾缝、开片、窗户倒影）
lib/cave.py            洞穴壁画（石灰岩洞壁、赭石与炭黑、吹喷与手印、借岩面起伏、篝火与油灯照明、钙华与熊爪痕）
lib/macpaint.py        1-bit 早期画图软件（640×360 黑白帧缓冲、8×8 图案、当年的绘图工具与文字样式、菜单 / 工具栏 / 图案板 / 窗口界面）
lib/blackfigure.py     古希腊黑绘陶瓶（拉坯轮廓 + 展开面、轮制饰带与纹样、泥釉剪影、刻线、加红加白、三段烧成、做旧、博物馆打光、饰带展开图）
lib/graphite.py        铅笔素描（素描纸纹、2H–8B 石墨、起形辅助线、轮廓、分层排线、侧锋铺调、纸擦笔、橡皮提亮、边缘只剩线稿、页边笔记与试笔色阶）
lib/xray.py            X 光片（双能衰减图：实心 / 壳体 / 圆棒管子 / 弹簧 / 侧看与正看的圆片 / 拉链螺钉电线 / 叠放衣物；比尔定律、散射、线阵条纹、光子噪声；胶片显示与安检伪彩、Zeff 与体积读数 OSD）
lib/rubberhose.py      1930 年代黑白橡皮管动画（灰色水粉背景、铅笔稿 → 描线 → 平灰上色的赛璐璐、橡皮管四肢 / 白手套 / 饼切眼、黑白胶片：颗粒、片门晃动、圆角片门、划痕灰尘）
lib/linocut.py         黑白麻胶版画（整版减法刻：V 口 / U 口刀痕、清底残刀、留黑线、一块套色错版、手拓发花、压印、铅笔签名编号）
lib/vhs.py             VHS 家庭录像（70 年代客厅：反照率 × 灯光 + 自发光、离焦图层；家用摄像机：手持倾斜、钨丝灯偏色、软膝、泛光、CCD 竖向拖影、拖尾、增益噪声、点阵 OSD；录像带：YIQ、亮度带宽与锐化光晕、色度带宽 / 隔行平均 / 延迟、噪声、时基抖动、跟踪噪带、磁头切换、掉磁）
lib/flatvector.py      扁平矢量（分层几何色块、七色限定色板、层间柔和投影、细颗粒）
lib/storybook.py       绘本角色动画（按时间取帧：带揭示图的场景层、follow 边走边画、隐式曲面角色挤压拉伸、动作编排、特效、按骨架笔顺手写、旅程总图）
lib/ballpoint.py       圆珠笔涂鸦（复印纸纹、纤维与折痕；圆珠笔：干起笔、压力线宽、断墨、墨团、收笔小钩、描两遍、压痕；彩铅斜向排线出界；圆珠笔之字排线；字体骨架重描的手写、划掉重写、无墨压痕字）
lib/overlay.py         描图纸叠层（灯箱发光、黑线灰调底图与单色叠片、透过率相乘的油墨、背光纤维云纹、抬起时的漫射模糊与投影、卷角、打孔与定位钉、套准十字、绘图胶带、透明胶片）
examples/*.py          范例脚本；*.jpg 成品；drawing_*.gif 逐步画出的动图
中文字体：自动找 Kaiti/Songti（macOS）、Noto CJK（Linux）、KaiTi/SimSun（Windows），或设 INKPAINT_FONT
西文字体（后来新增的画风用）：core.latin_font(style) 按 sans / sans_bold / rounded / script / hand / typewriter 等找系统字体，可用 INKPAINT_FONT_<STYLE> 指定；字体文件不要放进仓库
```
