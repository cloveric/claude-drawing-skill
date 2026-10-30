# 彩色小镇（colortown）

- **实现**：`lib/colortown.py` · `ColorTown`
- **范例**：`examples/colortown_festival_steps.py` 雨后的节日台阶街 · Festival Steps After the Rain（1500×2000 的竖幅童话街景，不透明水粉平涂加细细的深棕墨线：节日的早晨，刚下过一阵雨，一条石头台阶从湿漉漉的小广场爬上山，从一栋薄荷绿房子底下的拱门里穿过去，接着往上走；番茄红、芥末黄、青绿、薄荷、珊瑚、奶白、天蓝的房子一排压一排堆上山坡，越往上越小、越淡，有尖尖的山墙、窄窄的塔楼式房子和几片赤陶瓦，深蓝灰的石板曼莎屋顶一片片错缝铺出来，带老虎窗、烟囱和赤陶烟囱帽、电视天线；山顶左边一座白色钟楼，铜绿洋葱顶、三扇木百叶钟楼开口、指着九点零几分的钟面、顶上一面红旗；淡蓝的天，奶白的云，几只小鸟；左边是一面往消失点收的峡谷墙（浅粉、白、浅黄三栋，整面墙按透视单应贴上去），右边是一栋离我们很近的白房子，有几扇浅蓝百叶窗、铁艺阳台、窗台花箱，底层是青绿色的咖啡馆，条纹遮阳篷，外面摆两张小咖啡桌；三角彩旗挂在四个深度上：远处山上两串很小的，上排房子前一串，广场上两串，最近四串大的斜穿过整个画面，每面旗有一道深一点的折痕，绳子从钟面下面过；红玫瑰和粉玫瑰爬满墙角，窗台花箱里花叶溢出来，还有花店 FLEURS 门口一排花桶、面包店 PAIN、吊挂的咖啡杯和钥匙店招、壁灯、墙脚的海报和盆栽、台阶两侧的石墙和铁栏杆、台阶上一只猫、两棵圆圆的绿树；广场是湿的，把房子、彩旗和人倒映成一道道竖向的笔触，石板缝淡淡地透出来；几个很小、不画脸的人：打红伞的、牵红气球的孩子、一对并肩走的、提一篮花的；照插画师的顺序画：空纸 → 天空和云 → 远处的小镇和钟楼 → 上面两排房子和树 → 拱门房子、台阶和广场边的房子 → 两侧的峡谷墙 → 玫瑰、花盆和店招 → 近处的彩旗 → 湿广场和倒影 → 行人、路灯和咖啡桌；`--stages` 出 9 个阶段加成品）
- **耗时**：约 7 秒

## 何时选用

治愈、明亮、「细节多到看不完」的童话街景：一座彩色的欧洲小镇、节日的街道、雨后的广场、钟楼和台阶，满街彩旗、玫瑰、花箱和阳台，要一眼就是「手画的水粉插画加细细的描线」，竖幅海报、小红书封面、旅行 / 城市 / 节日 / 「理想的生活」的配图，讲解片里「一个地方 / 一个社区 / 很多人一起生活」的页 → 彩色小镇（要中式园林、古镇和春水用江南园林；要锡釉蓝砖上的运河小镇用代尔夫特蓝瓷砖；要彩纸剪出来的小镇用剪纸拼贴；要系统的微缩模型用等轴 2.5D；要针管笔速写加淡彩的小卡用钢笔淡彩；要没有描线的几何色块用扁平矢量；要彩铅叠涂的黄昏小镇用暖调彩铅绘本）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from colortown import ColorTown
```

**彩色小镇 `ColorTown`**：
- 思路：照水粉插画师的顺序从远往近画一条街（空纸 → 天空和云 → 远处的小镇和钟楼 → 一排排往近的房子 → 台阶和广场边的房子 → 两侧近处的墙 → 玫瑰、花和招牌 → 近处的彩旗 → 湿街和倒影 → 人），每块颜色都是不透明的平涂，几乎每样东西都有一道细细的、微微抖的深棕墨线。
  - 色块：每块是一个多边形，后上的盖住先上的。几万块一次画完：Pillow 把每块按序号填进 2 倍超采样的整数 id 图（序号就是画的先后），numpy 对每个 id 查一张表（颜色、不透明度、纹理权重），再 box 平均回 1 倍，所以边是抗锯齿的，一块只要几微秒。整张画布预先算好三张纹理场——竖向笔刷条纹、横向笔刷条纹、各向同性的擦笔（scumble）——再加一层低频斑驳，每块按自己的权重取，明度只差百分之几：墙用 `PLASTER`（擦笔 0.7 加一点竖向笔刷 0.5），天空和铺地偏横向，屋顶、树叶和花用擦笔。浅色的纹理和斑驳按亮度减到约 45%，白墙才干净、不发灰。多边形的边每隔几 px 重采样一次，再沿法线推一点平滑的随机抖动，长边就是手画的直，不是尺子画的直，颜色和描线也不会严丝合缝。
  - 墨线：深暖棕色，每组颜色画完再画这一组的线（`flush()`）。每条线在 3 倍 id 图里有自己的序号（Pillow 画带圆角接头的折线），交叉处不会叠出墨珠。长线分成几段、粗细各差一点；每条都重采样、加一点低频的手抖；方框的四条边分开画，约三成的转角出头 0.3–1.3 px。墨是半透明的：60% 墨色加 40% 墨色乘底色，所以压在奶油色上是深棕，红墙上是深红棕，玻璃上近乎黑。
  - 远近：`depth(far)`（0 近 … 1 很远，可以当上下文，也可以当参数）把颜色往天空的淡蓝灰拉、降一点饱和度，线变细、变淡；其余的远近靠尺度（近处的窗几十 px，远处的不到十 px）和从后往前画的遮挡。
  - 透视墙：`plane(src, dst)` 设一个单应，把一块平摊的矩形布局贴到一个四边形上，整面立面（窗、花箱、阳台、玫瑰）就能按一点透视往消失点收；墨线粗细跟着局部尺度变。
  - 房子：`house()` 用几个数就搭出一栋窄高的联排房子。墙是带裸石斑块的灰泥（几块石头描了边），还有层间腰线、檐口，墙脚有一层很薄的乘色罩染，檐口下有一道淡阴影。底层可以是门、店面（招牌上写字、壁柱、小方格橱窗、条纹遮阳篷）或拱门。楼上的窗格子每扇都略有不同：奶油色窗框，深青绿的玻璃上一道斜的浅色反光，窗棂、窗台，部分窗户有带横条的百叶窗（`shutter_p`），部分挂窗帘，还有圆窗和拱窗。窗台花箱里是一堆叶子，上面是花点，前面垂下藤；铁艺阳台后面摆着花盆。屋顶的石板一片片错缝铺上去，每片蓝灰各不相同，裁进屋顶的轮廓，缝再描出来；有曼莎、四坡、侧山墙、尖山墙几种，还有老虎窗、带赤陶帽的烟囱、电视天线。返回窗户、屋顶线、烟囱顶的坐标，方便挂彩旗、牵玫瑰。
  - 植物：玫瑰是沿路径弯弯绕绕往上爬的茎，带侧枝和成对的小叶；花是不规则的杯形，花心深一点，三道深色花瓣弧线，上沿一道混色的浅边，越往上越多、三两成簇。树是树干和枝（墨线），树冠是一团团叶片，每团按左上来光当穹顶打光：下面的团先画，浅色只落在受光的尖上，叶子溢出深色底，轮廓才是叶子边。
  - 彩旗：绳子在两点之间按抛物线下垂，三角旗按等距挂在绳上，顺着绳子的斜度，比绳的法线更往下垂；每面旗半边深一点（折痕），颜色按一串欢快的颜色轮着取，描线。远处的小、近处的大，在好几个深度上各画一串。
  - 湿街：先按透视铺石板，缝朝消失点；再把画街之前的画面按每一列的墙脚线镜像下来，加涟漪横推、按列的平滑偏移，离墙脚越远竖向拖得越长，压暗、混进石板色，乘上竖向笔刷条纹；最后把石板缝淡淡地重描一遍，加几道横向反光。之后画的东西（人、路灯、咖啡桌）用 `mirror()` 包起来：里面画出来的像素自动镜像到地面上，竖向拖尾、往下渐淡。
  - 收尾：`finish()` 只记参数、在 render 里加（每张阶段快照都和成品一致，要在画第一笔之前调用）：轻微柔化、细颗粒、一点暖色、很淡的暗角。
- 构造：`ColorTown(W, H, seed, keep_stages=True, stages_dir=None)`（总像素不超过 4096²），先 `finish()` 再 `paper(tone)`。坐标是整张画布的像素；`t.lw` 是默认墨线粗细，画远处的东西前调小。
- 底层：`fill(pts, colour, tex, dir, mot, hand, alpha, vary)`（`dir` 是 0 竖 / 1 横 / 2 擦笔，或者一个三元权重，如 `PLASTER`）、`ink(pts, width, closed, alpha, colour, hand, corners, over)`、`box(x0, y0, x1, y1, colour)`、`flush(clip)`（`clip` 是裁切多边形）、`dab(x, y, r, colour)`、`leaf(x, y, length, width, angle, colour)`、`glaze(P, colour, top, bottom)`、`mask(P, soft)`、`paint_mask(mask, colour, alpha, tex, dir, sl)`、`text(cx, cy, s, size, colour)`；上下文 `depth(far)`、`plane(src, dst)`；形状函数 `rect()`、`arch()`、`ellipse_pts()`、`leaf_pts()`。
- 天空：`sky(top, mid, bottom, y1)`、`clouds([(cx, cy, w, h), …])`、`birds(region, n)`。
- 房子：`house(x, base, w, h, wall, roof, roof_h, roof_col, floors, cols, frame, glass, shutters, shutter_p, curtains, boxes, flowers, balconies, ground, door_col, shop, sign, letters, awning, stones, boards, bands, chimneys, chimney_col, dormers, aerials, win_kind, win_w, win_h, arch_top, arch_w, top_window, cornice, lw, far, seed)` 返回 windows / roof / ridge / chimneys 等（`ground` 取 'door' | 'shop' | 'arch' | None，`roof` 取 'mansard' | 'hip' | 'side' | 'gable' | 'pyramid' | 'flat' | None，`roof_col='tile'` 是赤陶瓦，`balconies` 是 (楼层, 列) 的列表，列写 -1 表示整层）。部件：`window(x0, y0, x1, y1, kind, frame, glass, panes, shutters, curtains, sill, lintel)`（kind 取 std / arch / round）、`door(…, kind, panels, fanlight, step)`、`shopfront(…, text, letters, door, goods)`、`awning(x0, x1, y, depth, colours)`、`balcony(x0, x1, y, h, pots, style)`、`flowerbox(x0, x1, y, h, box, flowers, mound, trail)`（花色见 `FLOWER_SETS`：pink red sunny violet white）、`roof(kind, x0, x1, y, h, colour, dormers)`、`dormer()`、`slates(P, tile, ramp)`、`chimney()`、`aerial()`、`vane()`、`patches()`。
- 钟楼和台阶：`clock_tower(cx, base, w, h, body, quoins, dome, time, flag)`（dome 取 'slate' 或 'verdigris'）；`stairs(bottom, top, n, ratio)`（bottom / top 各是 (左 x, 右 x, y)，越往上台阶越小）；`parapet(top 折线, bottom 折线, course)`；`railing(path, h)`。
- 街：`street(y0, vp, poly)`；`reflect(src, base, y0, strength, smear, ripple, darken, region)`（`src` 传画街之前的画布，`base` 可以是逐列的数组）；`joints(alpha)`；`mirror(base, x0, x1, top, strength)` 上下文；`glints(y0, y1, n, region)`。
- 植物和小物：`roses(path, n, colour, dark, light, size)`、`tree(x, base, h, rad, clumps, leaf)`、`pot(x, base, w, h, plant, flowers)`（plant 取 bush / tall / flowers）、`bunting(p0, p1, sag, size, colours)`、`lamp(x, base, h, wall)`、`sign(wall_x, y, r, colour, icon, side)`（icon 取 cup / key / loaf / flower）、`person(x, base, h, coat, legs, hair, umbrella, balloon, basket, facing)`、`cat(x, base, s)`、`bistro(x, base, s)`、`poster(x0, y0, x1, y1, colour)`。
- 收尾：`finish(soft, grain, warmth, vignette)`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。
- 颜色用 `PAINTS` 里的名字（paper ink ink_soft iron；sky_top sky sky_low haze cloud cloud_shade；tomato red brick coral salmon pink blush rose_wall mustard ochre yellow butter pale_yellow orange apricot teal teal_deep jade mint pale_mint aqua turquoise blue cobalt powder cerulean green sage lavender cream ivory white stone stone_mid stone_dark warmgrey；slate slate_dark slate_light slate_blue tile tile_dark verdigris copper；glass glass_light glass_dark curtain wood wood_dark gold；leaf_dark leaf leaf_mid leaf_light leaf_pale trunk rose rose_dark rose_light rose_pink rose_pink_dark blossom_white blossom_yellow blossom_orange blossom_purple blossom_pink terracotta pot_dark；street cobble cobble_dark wet；skin hair hair_light）或 '#rrggbb'；彩旗的颜色是 `BUNTING`，石板和瓦是 `SLATE_RAMP`、`TILE_RAMP`。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 天空的横向笔刷条纹太显，像拉丝金属 | 天空以擦笔纹理为主（0.35），横向条纹只另叠半透明的一层（0.25） |
| 云是一团带颗粒的灰，脏 | 云的纹理 0.8 → 0.22，下沿只往暖灰过渡，不加颗粒 |
| 窗框四角像描了两遍，线乱 | 方框转角出头的概率 0.5 → 0.28，出头长度 0–1.8 → 0.3–1.3 px，不出头时只差 −0.4–0.3 px |
| 窗台花箱是一条细带，几粒花点，不像「溢出来」 | 花箱上面堆一个叶丛（高 2.4 倍箱高）：叶子由外往里、由深到浅，花点画在叶子上，大的加一点浅色花心，前面垂下几串藤 |
| 玫瑰是一串红点；粉玫瑰带亮白高光，像一串泡泡 | 花是不规则的杯形（半径带 4–5 瓣的起伏），花心深一点，三道深色花瓣弧线，上沿一道和底色混出来的浅边（不用白），每朵旁边塞两片叶子；粉玫瑰放在浅墙上，白墙上用红玫瑰 |
| 百叶窗横条又密又黑，像条纹卷帘，整面墙很花 | 横条间距 2.6 → 3.6 倍线宽，不透明度 0.45 → 0.32；百叶窗只给一部分窗户（`shutter_p`），近处的白墙 0.3 |
| 钟楼上两个深色的拱形开口在钟面上方，像一双眼睛 | 改成三个窄的木百叶开口（浅木色横条） |
| 两棵树几乎看不见，被前排的屋顶盖住 | 树画在上排房子之后、广场边的房子之前，树冠中心抬高 |
| 树冠是一片均匀的浅绿印花，轮廓是光滑的一团 | 每团按穹顶打光，下面的团先画，浅色只落在受光的尖上（ramp 去掉最浅的黄绿）；深色底缩到 0.9 倍，叶子撒到 1.06 倍，轮廓才是叶子边 |
| 白墙发灰、发脏 | 浅色的纹理和斑驳按亮度减（亮度 0.72–0.95 之间减到约 45%），墙脚的罩染 0.13 → 0.1 |
| 墙像一块块木板，竖向笔刷太重 | 墙用 `PLASTER` 权重：擦笔 0.7 加竖向 0.5，斑驳 1.2 |
| 倒影的竖边被推成一级级台阶，底下一片照片式的灰模糊，铺地上一道道横线像扫描线 | 涟漪尺度 6 → 18 px、随距离增长得更慢，加按列的平滑偏移，远处拖成竖条；铺地改用擦笔纹理；倒影之后再淡淡地重描石板缝 |
| 每个人脚下有一个深色的圆球（镜像出来的头） | 不再自己画镜像的人形：用 `mirror()` 把实际画出来的像素镜像下来，竖向拖尾、往下渐淡、强度 0.35–0.5 |
| 最大的一串近景彩旗正好挂在钟面上 | 先算出绳子在钟楼那几列的高度，再挪端点，让它从钟下面过（约 y 684，钟面外圈下沿约 616） |
| 花店招牌是奶油色的字写在奶油色的底上，看不见 | `house()` 加 `letters` 参数，花店用深青绿字 |
| 颜色太满，近处的墙和中间一样饱和，眼睛没处歇 | 左边的峡谷墙改成浅粉、白、浅黄，右边是白墙，饱和的房子集中在中间那一堆；中间每排也混进白和奶油色的房子 |
| 山上的房子一排排一样的盒子，像货架 | 行生成器：宽、高、地基都随机错开，约两成是尖山墙，一成是窄的塔楼式房子，一成五是赤陶瓦，阁楼窗在圆、方、拱里随机取 |
| 换了一个参数，行生成器的随机序列整个变了，一栋房子正好挡住钟楼下半截 | 钟楼前面那一段（x 300–520）单独一行，压低高度、不出尖山墙 |
| 清理代码时修掉了一个把石块整体推出画面的坐标错误，石块露出来，每块明暗差 7%，在倒影下面成了棋盘格 | 石块明暗差 7% → 2.5%，缝的颜色接近石色（#a29f98），倒影下面才是一片湿石板 |
