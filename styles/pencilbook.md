# 暖调彩铅绘本（pencilbook）

- **实现**：`lib/pencilbook.py` · `PencilStorybook`
- **范例**：`examples/pencilbook_tortoise_crossing.py` 大龟过河 · The Tortoise Crossing（一页暖调彩铅绘本：黄昏，一只很老、很大的乌龟慢慢蹚过一条浅浅的小溪，背上长着一座小花园——一圈连成片的苔藓垫，垂下一绺绺长苔藓，里面几丛草和野花、一棵秋天金黄的小树、一根弯木杆上挂着一盏纸灯笼；它低下头，用一双老而温和的眼睛看着身旁踏脚石上的小孩：黄色雨衣、帽子放下、短短的波波头、红靴子，也提着一盏灯笼，仰头看它；龟壳一块块盾片都是低低的穹顶，绕着生长纹排线，沟是断续的深褐线，受光的左侧被落下的太阳镶一道暖边，右边背光面叠一层冷紫；脖子横着几道松弛的褶，腿上一片片小鳞，前腿往前迈、后腿往后蹬，肚子底下的水压在阴影里；背后是从软蓝到蜜桃、奶油黄的天空和留白的云，太阳刚落到远山后面，山坡上几栋小房子亮了灯；水里是一笔笔横排线画出的倒影：天、窗灯、龟腿和小孩；近岸两丛开小花的灌木框住画面；所有面都是顺形体的细彩铅线一层层叠出来的，纸齿透出细白点，没有墨线和黑色；照绘本画家的顺序画：空纸、天空（先把龟、树和灯杆留白）、远山和小镇、溪流、龟的浅色底层、塑形、背上的花园、踏脚石和小孩、倒影和涟漪，最后是灯光和近岸；`--stages` 出 9 个阶段加成品）
- **耗时**：约 40 秒
- **内部构成**：暖调彩铅绘本（以 1 px 细颗粒为主的直方图均衡纸纹与沿 8 个方向拖开的纸纹，纸坑里留的一点蜡和越叠越深的蜡层缓冲；在方向场里积分出中心线、带手腕弧度的铅笔笔触；id 图光栅化：Pillow 按序号画折线、2 倍超采样，numpy 只对被盖住的子像素查回这一笔，算出沿笔位置和压力曲线，蜡只落在压力够得着的纸纹上，bincount 汇回像素；抖动网格落笔、逐像素压力的平滑过渡、留白（avoid）；半透明的蜡混色与压光；软穹顶受光和照彩铅画家顺序的分层塑形：浅色底、固有色、同色系暗部、最深处、暖色和冷色罩染、交叉角度；漂移、等值线、放射方向场与双倍角混合；根部散开尖端聚拢、有亮面暗面的毛绺，整张毛皮，散开的草丛，树冠的叶簇；顺着表面的暖色发光笔触与带纸纹的提亮，亮灯的窗，提亮；镜像取样的横排线倒影、断开的涟漪圈；分别打光的团块树冠、小房子、石头、鳞片、野花、纸灯笼、雨衣小孩、点点眼和腮红；很淡的同色轮廓、几笔叠成的软线；轻微柔化、细颗粒、暖色暗角）

## 何时选用

温暖、怀旧、像翻开一本童书的一页：一只大而温柔的生物陪着一个小小的孩子（巨龟、大熊、温柔的怪兽陪孩子过河、等车、看日落），午后和黄昏的暖光、亮灯的窗和灯笼、草地、小溪和小镇，要满画面看得见彩色铅笔的笔触和纸齿，讲解片里「温柔的陪伴 / 慢慢来 / 一起走一段」的页，童书封面和插页 → 暖调彩铅绘本（要明亮可爱的彩铅甜品小物用韩国彩铅；要软蓝限色、乱线墨线的绘本跨页用蓝调绘本；要粉彩黄昏转入星空、满坡野花用暮色微缩绘本；要黑白石墨写生用铅笔素描；要不透明水粉的特写大头像用复古水粉）。

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from pencilbook import PencilStorybook
```

- 思路：照彩铅绘本画家的顺序画一页（空纸 → 先把主体留白、铺天空 → 远景 → 水 → 主体的浅色底层 → 塑形 → 细节和毛发 → 人物 → 倒影 → 灯光和近景），每一块面都是顺着形体走向的细铅笔线一层层叠出来的，没有墨线、没有黑色。
  - 纸：直方图均衡过的纸纹 `T`（0–1 均匀分布，以 1 px 的细颗粒为主），所以「蜡挂在纸纹高于 1 − 压力的地方」直接就是覆盖率；预先算好沿 8 个方向拖开的纸纹，每一笔按自己的方向取，漏掉的纸坑顺着笔拉成很短的道。纸坑里也留一点蜡（`floor` 0.34）；另有一张蜡层缓冲 `F`，叠得越多，后面的笔越能压进纸坑——所以同一批纸坑一层层都透出细白点（越来越带色），压得重、叠得多的地方才慢慢合上。
  - 一笔：中心线在方向场里积分出来（方向按 mod π 处理，中途不会掉头），带一点手腕的弧度。几万笔一次画完：Pillow 把每一笔当折线按序号画进 2 倍超采样的整数 id 图，numpy 只对被盖住的子像素查回这一笔的颜色、起点、方向、长度、压力和收笔，算出沿笔的位置，得到压力曲线（落笔重、收笔轻挑），蜡只落在压力够得着的（同方向拖开的）纸纹上，再用 bincount 汇回像素。同一批里最上面那笔说了算，层次靠多遍（`passes`）叠。
  - 落笔位置用抖动网格（排线均匀，不会一团一团）；区域既是落笔概率，也是逐像素的压力（`fade`），所以暗部是平滑的过渡，不是散落的深色短线；`avoid` 是后面要画的东西：铺天空时先把龟、树和灯杆留白，颜色才不会和蓝色混在一起。
  - 蜡的混色：新 = 旧 + 覆盖 ×（目标 − 旧），目标 =（1 − opacity）× 旧 × 颜色 / 纸色 + opacity × 颜色。盖在白纸上就是本色，黄盖在蓝上变绿，同色越叠越深；浅色（白、奶油、黄）盖在深色上要调高 `opacity`（压光）。
  - 塑形：`shading()` 把轮廓鼓成一个软穹顶（几层模糊相加），按法线和光的方向（默认左上）给出 0–1 的受光；`form()` 照彩铅画家的塑形：整块铺一层浅色底、固有色、背光处同色系的深色、核心暗部最深的颜色，再在受光一侧罩一层暖色、阴影里罩一层冷色，每层绕着形体自己的方向场错开 ±`cross` 度，笔触交叉。
  - 方向场：`flow(角度, 扰动, 尺度)` 缓缓漂移的方向（天空、水面）；`contour(遮罩)` 顺着形状的等值线（绕着穹顶、石头、每块盾片的生长纹）；`radial()` 从一点放射；`blend()` 双倍角混合（0 和 π 是同一个方向）；`rotate()`。
  - 毛发：`fur()` 一绺一绺地画：每绺 4–12 根细线，根部在绺里散开、尖端聚拢，朝同一边微弯，落笔重、收笔挑，顺着毛向；每绺背光一侧的几根暗一点（`side`），所以每绺都有亮面和暗面。`pelt()` 是整张毛皮：浅色底层、背光处暗而短的毛绺、固有色、受光处的浅色毛尖。`grass()` 反过来，草叶从根部往上散开；`leaves()` 是树冠里一簇簇短弯的叶片笔触。
  - 光：`glow()` 是一层层顺着周围表面走的暖色笔触（靠近光源黄白、往外橙色、越往外越稀，不放射成星芒），下面垫一层带纸纹的提亮（不是一团平滑光晕）；`window()` 亮灯的窗（窗框附近橙、中间奶油黄、几根窗棂）；`lift()` 可塑橡皮 / 白色铅笔提亮。
  - 水：`reflect()` 在水面铺横向笔触，颜色取水线以上画面的镜像（被涟漪横推、模糊、混进水色），倒影也是一笔一笔的；`ripples()` 是立在水里的东西周围断开的椭圆圈。
  - 绘本部件：`tree()` 树干、几根枝和一团团分别打光的树冠（`tree_plan()` 先给出遮罩，好让背景留白）；`cottage()` 小房子（墙竖着排线、屋顶顺着坡、亮灯的窗、门、烟囱）；`stone()` 顶面略平、绕着形体排线的石头，可带苔藓；`scales()` 错开排列的小鳞片，背光一侧一道褶；`flowers()` 野花，圆头花瓣笔触围着花心，可带茎。
  - 人物：`child()` 几百像素高的绘本小孩：帽子放下的雨衣、靴子、一绺绺顺下来的波波头、点点眼、腮红、一只手往前提灯笼（`paint=False` 只给遮罩，同一个 seed 画出来是同一个孩子）；`lantern()` 圆圆的纸灯笼；`eye()` 带高光的软点眼；`blush()` 腮红。
  - 收尾：`finish()` 只记参数、在 render 里加（每张阶段快照都和成品一致，要在画第一笔之前调用）：轻微柔化、细颗粒、很淡的暖色暗角。
- 构造：`PencilStorybook(W, H, seed, keep_stages=True, stages_dir=None)`（总像素不超过 4096²），先 `finish()` 再 `paper(tone, tooth, mottle, fibres)`。坐标是整张画布的像素；给方向场传一个数就是角度（度，0 向右、90 向下），方向场数组是弧度；`LIGHT` 是默认光（左上、略朝前）。
- 遮罩：`poly(pts, smooth)`、`ellipse(cx, cy, rx, ry, rot)`、`blob(cx, cy, rx, ry, rough)`、`tube(path, w0, w1)`、`below(xs, ys, invert)`、`rect(x0, y0, x1, y1)` 返回画布大小的浮点遮罩；`line_y(xs, ys)` 是样条线在每一列的 y；`value(top, bottom, y0, y1, mottle)` 竖向的 0–1 场。
- 笔触：`hatch(region, field, colour, length, width, density, pressure, opacity, alpha, jitter, bend, value, hue, taper, passes, clip, avoid, fade)`。`region` 是落笔概率遮罩或 (x0, y0, x1, y1)；`density` 约等于把区域铺几遍；`length` / `width` 给 (最小, 最大)、一个数或 f(x, y)；`colour` 给颜料、一串颜料（随机取）、(色阶, 场或 f(x, y)) 或 f(x, y) → (N, 3)。`strokes(paths, …)` 画给定的折线；`line(path, colour, width, pressure, seg, wobble, clip, gaps)` 几笔叠成的软铅笔线；`edge(mask, colour, …, where)` 很淡、断续的同色轮廓。
- 塑形：`shading(mask, light, sigma, wrap, flat)`；`form(mask, colours=(浅, 固有, 暗[, 最深]), field, light, cross, length, width, density, pressure, warm, cool, edge, lit, avoid)` 返回受光场。
- 毛发和草木：`fur(region, field, colour, length, width, density, tuft, spread, curl, converge, pressure, side, light)`（`converge` 1 尖端聚拢、−1 散开）；`pelt(mask, colours, field, light, length, density, lit)`；`grass(region, colour, height, lean, sway, density, tuft, fan)`；`leaves(region, colour, size, density, field)`；`tree(x, y, h, r, colours, trunk, clumps, leaf, light, lean, seed)`、`tree_plan(x, y, h, r, clumps, lean, seed)`；`flowers(region, kinds, n, size, stems)`（花种见 `FLOWERS`：daisy buttercup poppy forgetmenot pink clover cornflower marigold）。
- 物件：`cottage(x, y, w, h, wall, roof, windows, door, chimney, roof_h, light, glow, avoid)`；`stone(cx, cy, rx, ry, colours, moss, flat, light, warm, cool, avoid)`；`scales(mask, size, colours, groove, field, light, lit)`；`dots(region, colours, n, size)`。
- 光和水：`glow(x, y, r, colours, strength, density, halo, squash, clip, field)`；`window(x0, y0, x1, y1, panes, frame, light, sill, glow)`；`lift(mask, colour, amount)`；`reflect(waterline, region, src, ripple, stretch, darken, tint, mixw, soft, length, width, density, field)`（`src` 传画水之前的画布，`waterline` 可以是逐列的数组）；`ripples(cx, cy, rx, ry, rings, colour, grow)`。
- 人物：`child(x, y, h, facing, coat, hair, boots, legs, skin, look, light, arm, paint, seed)` 返回 hand / head / eye / mask；`lantern(x, y, size, body, ribs, cap, handle, glow)` 返回灯笼中心；`eye(x, y, r, colour, lid, look, glint)`；`blush(x, y, r, colour, amount)`。
- 收尾：`finish(soft, grain, vignette, warmth)`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。
- 颜色用 `PAINTS` 里的名字（paper white cream ivory；sky_top cobalt sky cornflower sky_pale powder periwinkle lavender mauve violet ultramarine indigo slate teal aqua；lemon butter sun apricot peach glow lantern flame orange tangerine；meadow yellowgreen grass leaf sage moss olive forest pine lichen；ochre gold amber sienna brown umber sepia tan sand stone warmgrey pebble；terracotta brick rose coral vermilion red cheek pink；skin skin_shade hair hair_light raincoat raincoat_shade raincoat_deep denim boot eye）或 '#rrggbb'；色阶用 `RAMPS` 里的名字（dusk_sky day_sky glow water meadow hills shell skin stone autumn）或自己给一串颜色。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 第一版满画面大白点，像粗纸上的蜡笔，不像彩铅 | 纸纹里中、大尺度的成分太多，每笔覆盖又太少：纸纹以 1 px 细颗粒为主（1 px 0.6 → 0.8，2 px 0.45 → 0.38，6 px 0.25 → 0.12，22 px 0.12 → 0.05），默认压力 0.62 → 0.74，纸坑里也留一点蜡（`floor`，最后定在 0.34），每笔轻一点（alpha 0.9 → 0.62）、多叠几遍，白点才是细的、带色的 |
| 塑形的暗部是一道道散落的深色短线，像在下雨 | 暗部只靠落笔概率：区域同时当作逐像素的压力（`fade` = 区域^0.65），落笔概率用它的平方根，暗部才是平滑过渡 |
| 先画的山坡透过后画的龟壳，壳的下半截发绿 | 彩铅半透明，后上的颜色和底下的混：先算好前景（龟、树、灯杆、小孩、石头）的遮罩，铺天空、山坡和水时 `avoid` 留白，像画家先把主体空出来 |
| 苔藓盖住半个龟壳，像一块草坪，下沿是一排三角形的齿 | 只留壳顶一带，改成几十个互相叠着、各自打光的圆垫；下沿再加一圈小垫和几团散落的小垫，挂下来的是一绺绺长苔藓 |
| 改成圆垫以后，壳上是一块块绿色的霉斑 | 主带的圆垫要密到连成一片：每个位置两排、半径 26–42 |
| 盾片之间的沟是浅色的线，两边描深 | 沟是盾片之间没上色的缝：直接沿 (u, v) 边界画深褐色的线（两遍、断续），下沿再补一道浅金色的亮边 |
| 盾片的分界是一根根直线，壳像拼起来的木板 | 肋盾之间的分界在中间往外鼓一点，每块盾片单独按穹顶打光（亮的一侧奶油黄、背光一侧赭红） |
| 四条腿是直柱子，龟像一张桌子 | 前腿往前迈、后腿往后蹬，脚到水面变宽；远侧两条腿躲到近侧的腿后面、压得很暗；肚子底下的水加一层冷色阴影；龟整体下移 34 px，露出的腿短一些 |
| 脖子是一块方方的、竖条纹的硬纸板 | 脖子改成上沿平、下沿下垂的形状（喉下松弛的皮），褶皱是往前弯的弧，间距不等，喉下再加三道横褶 |
| 小孩太小、脸看不清，头发像爆炸头 | 高 172 → 206 px；头发从头顶上方一点往下散开，长簇、几乎不卷（卷曲 0.1 → 0.03）、尖端半收拢，才是波波头；腮红半径 0.3 → 0.2 倍头的半径 |
| 小孩的脸融进身后的浅色水面 | 肤色加深一级（浅色底层从奶油色换成浅粉），脸加一圈很淡的同色轮廓；腿改成矢车菊蓝 / 牛仔蓝的裤袜，不用粉蓝 |
| 灯笼的光是一圈放射线，像星芒 | 光笔触改成顺着周围表面的随机流向（不放射），密度 1.3 → 1.0–1.1 |
| 杆上的灯笼外面一圈纸白的圆环 | 铺天空时留白用的灯笼遮罩比灯笼大：灯笼自己的颜色够实，不用留白 |
| 云底的暖色是一条细线，像给云描了边 | 只取云下沿 26 px 宽的带子再模糊，去掉玫瑰色 |
| 边光画在了背光的那一侧 | 受光的一侧是遮罩梯度朝光的地方：side = 0.82·gx + 0.45·gy，原来符号反了 |
| 龟壳的暖色边光画到了苔藓上，苔藓里出现一道浅色弧线 | 边光只画在光秃的壳上（减去苔藓、挂下来的苔藓、树冠和灯杆） |
| 灯杆上横着一道道条纹，像拐杖糖 | 细长的东西不要交叉排线：笔触顺着杆走（`contour()`），交叉角 26° → 8° |
| 树冠是一团黄色的海绵 | 团块更小、更分开（离中心 0.42–0.7 r，半径 0.3–0.44 r），每团单独打光，暗部用赭红，团与团之间才有缝 |
| 动图 1.58 MB，超了 | 普通叠化每帧都把整片天空、整条溪流改一点，细铅笔纹理每次都要重发：每个像素只在 5 帧里的约 2 帧完成过渡（先后由柔和的噪声加从左到右的扫过决定，像下一层彩铅一片片铺上去），0.99 MB；去掉 Bayer 反而更大（1.67 MB） |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
