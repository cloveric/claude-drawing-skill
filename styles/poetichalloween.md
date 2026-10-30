# 诗意万圣夜（poetichalloween）

- **实现**：`lib/poetichalloween.py` · `PoeticHalloween`
- **范例**：`examples/poetichalloween_ghost_jar.py` 罐子里的小幽灵 · The Ghost in the Jar（1920×1080 的秋夜绘本肖像，暗色画板上的水粉加细排线：十月的最后一夜，一个苍白的孩子站在深色的树丛里，戴一顶软塌的粗麻钟形帽（帽檐垂着松开的麻线，一圈麻绳打了个小蝴蝶结），乌黑的齐耳波波头、刀切一样平的齐刘海，整块头发上一道柔和的光泽；瓷白的脸，眼睛一圈、鼻梁和脸颊泛着红晕（平滑的红加细密的红斑点），厚眼皮半闭、往外眼角垂，低头看着手里的罐子，虹膜里映着一点暖光，红鼻尖，不笑的小嘴；深红的粗针织围巾围到下巴，一头垂在胸前，深色格子呢外套（藏青、墨绿加细的锈红和赭黄线，斜纹织出来，格子随衣褶起伏），两颗牛角扣；一双深红针织手套从两边扶着一个玻璃罐，罐口蒙着粗麻布、用麻绳扎住，罐子里一个床单小幽灵发着光，暖光照亮手套、玻璃边和她的下巴；树丛里和星空中还有五个小幽灵（银色细丝的身子，琥珀色发光的眼睛，衣摆每个尖一颗光珠），身边的叶子被照成橄榄色和橙色，其余的叶子几乎是黑绿的，每片都往后面投一块影子；靛蓝夜空里有细的斜笔触和星星；照在暗色画板上作画的顺序画：画板 → 粉笔起稿 → 夜空和星星 → 深色叶丛 → 平涂大块 → 极简的体积 → 织物 → 五官 → 小幽灵和它们的暖光 → 前景叶子和最后几笔；`--stages` 出 9 个阶段加成品）
- **耗时**：约 10 秒

## 何时选用

秋天和万圣节的夜晚、忧郁又有点超现实的一刻：一个苍白的孩子或年轻人独自站在夜里，手里捧着一点光或一个发光的小东西，身边有几个发光的小幽灵，要一眼就是「诗意的万圣节绘本」——瓷白的脸上一圈红晕、半闭的厚眼皮、刀切的黑色波波头，摸得着的粗麻帽子、粗针织围巾、格子呢外套，暗沉的靛蓝夜空和深色叶丛里只有一处暖光，讲解片里「孤独 / 守护 / 秋天 / 夜晚」的页，万圣节海报、头像和小红书封面 → 诗意万圣夜（要白纸上不画背景、粉粉的温柔角色小像用色粉小像；要背后刷一块单色、看得见毛衣针脚的复古童书大头像用复古水粉；要深蓝夜色里只有一个暖光、满画面短排线的小版画用排线夜景；要粉彩黄昏转入星空、满坡小野花的微缩风景用暮色微缩绘本；要满画面彩铅叠涂、温暖治愈的黄昏童书页用暖调彩铅绘本）。

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from poetichalloween import PoeticHalloween
```

**诗意万圣夜 `PoeticHalloween`**：
- 思路：照插画师在暗色画板上的顺序画一张忧郁的秋夜绘本肖像（画板 → 粉笔起稿 → 夜空和星星 → 深色叶丛 → 平涂大块 → 极简的体积（瓷白的脸、一整块的波波头和光泽）→ 织物（粗麻、格子呢、针织）→ 五官（红晕、眼睛、鼻子、嘴）→ 小幽灵和它们的暖光 → 前景叶子和最后几笔）；满画面暗，只让一处发光。
  - 画板：暗色画板，直方图均衡过的纸纹 `T`（0–1 均匀分布），所以「颜料挂在纸纹高于 1 − 压力的地方」直接就是覆盖率；预先算好沿 8 个方向拖开的纸纹（存成 uint8），干笔按自己的方向取。另有一张单像素的细点子纹 `ST`（uint8），专给红晕的斑点用；印刷颗粒和较粗的印刷纸纹在 `ground()` 里先算好（那时内存还低），`render()` 只取用。
  - 笔触：和色粉小像同一套按段编号的 id 图光栅化（Pillow 把每一笔的每一段按序号画进 2 倍超采样的整数 id 图，numpy 查回这一段，算出沿笔的压力曲线、两侧软边和越干越开的鬃毛条纹，压力够得着纸纹才上色，bincount 汇回像素）：宽的是不透明水粉的干笔，细而长就是彩铅排线。`colour='canvas'` 让每一笔取它中心下面画布的颜色——在算出来的底子（格子呢、塑形过的脸、夜空）上「用手再画一遍」，颜色不变、多了笔触。混色用以白为参照的乘：目标 =（1 − opacity）× 旧 × 颜色 + opacity × 颜色，暗底上也成立。一批太大就按 y 分成小带（每带 `band_px` 个子像素，省内存）。
  - 体积：`wash()` 平滑的一层不透明色（颜色可以按场取色阶；按行分带算，整张铺色也不建整张的 RGB 临时数组），最深的纸坑留一点浅，边缘按纸纹断开；`model()` 用软穹顶光把暗 → 亮的色阶揉上去——参考图那种极简的体积就是这样来的。`soften()` 只在形状附近做模糊。
  - 头发：波波头是一整块：先按整块头发（刘海、远侧那片、后面的）同一张受光揉色阶（近黑 → 板岩蓝）；`sheen()` 只在受光落在一条窄带（lo, peak, hi）里的地方铺一层柔和的光泽，再顺着发流画几笔又细又长、很淡的笔触，光泽沿头发拉开、整块不碎成发丝；`strands()` 只用很低的对比度画一点发丝；刀切的刘海就是遮罩的直边，加几根细发梢。
  - 脸：`eye()` 重眼皮的忧郁眼睛：杏仁形的米白眼球，上眼皮盖住约一半虹膜、往外眼角垂（`droop`），眼皮是一块揉成粉红的鼓起的皮肤，深色眼线，下眼睑一道湿红的边（`rim`），上面一道淡的双眼皮，一点白色高光；`reflect` 再在虹膜下半点一点暖色（她低头看的那盏光映在眼里）。`flush()` 是红晕：平滑的一层红加一层单像素的细斑点，红晕越浓斑点越密；`spot()`、`ring()` 给它软的场（脸颊、眼睛一圈、下半圈更浓）。`nose()` 长而简化的鼻子自成一个小体积：按光塑形，背光一侧一块柔和的紫灰，鼻尖往下投一小块影子，越往下越红、红鼻尖，一点鼻孔，鼻梁一道淡的亮线；`mouth()` 闭着、不笑的小嘴，嘴角往下。
  - 织物：`burlap()` 粗麻的平纹：每一行、每一列线各自粗细，沿线有疙瘩，行列略有游走，一上一下地交织，当高度场打光后乘到原来的颜色上，线之间是黑的孔，表面有松出来的纤维、轮廓上有毛边；`coords=(U, V)` 让织纹顺着形状走（`along(path, mask)` 给出顺着管子弯的坐标，帽檐就沿着它的弧线织）。`knit()` 粗针织的 V 形针脚（`path` 让针脚列顺着围巾走），`rib()` 罗纹。`tartan()` 格子呢：半个 sett 镜像成对称的循环，2/2 斜纹决定每一格露经线还是纬线、每根线略圆，再乘上衣褶的受光，`coords` 让格子随衣褶起伏。`fuzz()` 从轮廓里侧往外长纤维，颜色取它里面几 px 的颜料。
  - 叶丛：`leaf()` 掌状、重锯齿的叶子（醋栗 / 枫叶那样宽的裂片、浅的缺刻），随机压扁（侧着看），每片裂片沿中脉对折、一边亮，越往叶尖越亮，有斑驳和浅色叶脉，先往右下投一块软影子——树丛的前后层次就是这样来的；`foliage()` 从后往前撒几百片，越远越小越暗；`lit` 让叶子按光照图被照亮（小幽灵旁边的叶子变暖）。
  - 光：`light()` 登记暖色点光源（衰减 1 /（1 +（d / r）²）²，很陡，小幽灵只照亮身边）；`illuminate()` 按光照图照亮已经画好的东西：C ← 1 −（1 − C）· exp(−L × 接受度 ×（base + albedo × C）)，所以浅色的毛线和瓷白的脸变暖很多，暗的叶子在小幽灵旁边变成橄榄橙，黑头发几乎不变；接受度是一张场（叶子全接、天空一点、脸只有朝下的部分）。`emit()` 写进发光缓冲，`render()` 把它分三档模糊后叠成光晕。
  - 小幽灵：`ghost()` 半透明的圆顶钟形床单，由几百根银色细丝组成，像头发一样从头顶往外、往下披到一圈一绺绺的衣摆；一对发光的眼睛（奶白芯、琥珀色圈、光晕），每一绺末端一颗拉长的暖光珠，衣摆被暖光照亮，整块床单有一层很淡的光晕。
  - 收尾：`finish()` 只记参数、在 render 里加（每张阶段快照都和成品一致，要在画第一笔之前调用）：轻微柔化、发光的光晕、细的印刷颗粒加一层在暗部更显的粗纸纹、黑色微微提亮；按行分带算。
- 构造：`PoeticHalloween(W, H, seed, keep_stages=True, stages_dir=None)`（总像素不超过 4096²），先 `finish()` 再 `ground(tone, tooth)`。坐标是整张画布的像素；给方向场传一个数就是角度（度，0 向右、90 向下），方向场数组是弧度，也可以直接传 f(x, y) → 度（只在用到的点上求值）；`LIGHT` 是默认光（左上、略朝前）。
- 遮罩：`poly(pts, smooth)`、`ellipse(cx, cy, rx, ry, rot)`、`blob(cx, cy, rx, ry, rough)`、`tube(path, w0, w1)`（`w0` 可以是一串沿路径的宽度）、`rect(x0, y0, x1, y1)`、`below(xs, ys, invert)` 返回画布大小的浮点遮罩；`spot(cx, cy, rx, ry, rot, solid)`、`ring(cx, cy, rx, ry, width, rot, below)` 软的场；`soften(mask, sigma)` 只在形状附近模糊。
- 方向场：`flow(角度, 扰动, 尺度)`、`field(f(x, y) → 度)`、`radial(cx, cy, offset)`、`contour(mask, sigma, offset, fallback)`、`blend(f1, f2, w)`、`rotate()`；`value(top, bottom, y0, y1)` 竖向的 0–1 场；`shading(mask, light, sigma, wrap)` 软穹顶的受光。
- 笔触：`strokes(region, field, colour, length, width, density, pressure, opacity, alpha, streak, soft, taper, passes, clip, avoid, fade)`（`colour='canvas'` 取画布上的颜色）；`lines(paths, …)`；`sketch(path, colour, width, alpha)` 暗底上很淡的粉笔起稿线（几笔叠成、有的断开）。
- 色层：`wash(mask, colour, alpha, grain, edge, dry, clip, opacity)`；`model(mask, colours, light, lit, sigma, wrap, gamma, lo, hi)` 返回受光场；`glaze(mask, colour, alpha, mode, soft)`（multiply / screen / normal）；`dab(x, y, r, colour, alpha, soft, ry, rot)` 一小点（高光、发光的眼睛）；`line(path, width, colour, alpha, taper, dry, clip)` 平滑的细圆笔线（眼线、湿红的下眼睑、叶脉、麻绳）。
- 头发：`strands(region, flow, colours 暗→亮, n, length, width, curl, jitter, shade, spread, alpha, clip, roots, lock)`；`sheen(mask, flow, lit, band, colour, alpha, strokes)`。
- 五官：`eye(cx, cy, rx, ry, iris, iris_light, iris_r, look, lid, lower, droop, fold, rim, crease, reflect, rot, side, clip)`（`side` 是外眼角朝哪边，`look` 取 -1..1，dy > 0 往下看）；`flush(field, colour, strength, speckle, clip)`；`nose(path, width, tip_r, side, shade, tip, tip_strength, clip)`；`mouth(x, y, w, droop, colour, rot)`。
- 织物：`burlap(mask, angle, period, coords, thread, slub, holes, rust, fibres, fuzz)`；`knit(mask, stitch, angle, path, origin, curve)`；`rib(mask, path, period)`；`tartan(mask, sett, scale, angle, coords, lit, lo, hi)`；`fuzz(mask, length, n, width, out, field, lift)`；`along(path, mask)` → (S, T)。
- 叶丛：`leaf(x, y, size, angle, colours, value, fold, lit, veins, lobes, squash, shadow)`；`foliage(region, n, size, colours, value, angle, fold, lit, veins, squash, shadow)`。
- 光和小幽灵：`light(x, y, r, colour, power, squash, fall)`、`lightmap()`、`illuminate(receptivity, gain, base, albedo)`、`emit(x, y, r, power, ry)`；`ghost(cx, top, w, h, look, tips, strands, glow, lean, eye_r, body_alpha, sheet, clip)`；`stars(region, n, size, bright, warm)`。
- 收尾：`finish(soft, grain, tooth, bloom, lift, warmth)`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。
- 颜色用 `PAINTS` 里的名字（board chalk chalk_warm；night_deep night indigo dusk haze star warmstar；porcelain porcelain_light porcelain_shade porcelain_deep flush flush_light flush_deep rim lip lip_dark lid_line crease；eye_white eye_shade iris iris_light pupil；jet hair_black hair_dark hair hair_sheen hair_shine silver silver_light；burlap_dark burlap burlap_light burlap_hi burlap_rust oxblood_deep oxblood_dark oxblood oxblood_light oxblood_pale navy bottle tar rust ochre mustard；leaf_black leaf_deep leaf leaf_olive leaf_moss leaf_maroon leaf_rust leaf_orange；ghost_dark ghost ghost_light ghost_white glow glow_core glow_ring ember）或 '#rrggbb'；色阶用 `RAMPS` 里的名字（night porcelain hair silver burlap oxblood leaf leaf_olive leaf_maroon leaf_rust ghost glow，都是暗 → 亮）或自己给一串颜色。
- 范例的场景脚本先把所有形状的遮罩算好（`plan()`），再按从前往后的遮挡算出每块「看得见的部分」（手套和袖口 > 罐子和盖布 > 袖子 > 围巾 > 外套；帽子 > 刘海 > 远侧那片头发 > 脸 > 后面的头发），每一层只往自己看得见的部分上画；留着的画布大小的遮罩一赋值就转成 float16。


## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 小幽灵的光把整片树丛照成亮绿和亮橙，夜晚成了下午，「只有一处发光」也没了；树丛上沿多出一条半透明的亮带 | 点光源的衰减从 1/(1+(d/r)²)^1.2 改成 ^2，小幽灵的光半径从 2.2 倍身宽降到 1.15 倍，`illuminate()` 的 base 0.3 → 0.15；接受度用模糊过的树丛遮罩，不用硬边 |
| 叶子是一颗颗海星：裂片又细又尖、都正对着看，每片沿中脉一半亮一半暗，树丛平得像剪贴画 | 裂片加宽、缺刻变浅（到半径的 0.42–0.56），加重锯齿；每片随机压扁到 0.55–1 倍（侧着看），对折的明暗差 0.22 → 0.16；每片先往右下投一块软影子（偏移约 0.1 个叶长、模糊 0.06 个叶长），叶丛才有前后 |
| 红晕像一片疹子：眼睛下面两块粗的红斑点 | 斑点改用单像素的细点子纹 `ST`，平滑的一层红占大头；红晕的场改成一条绕着眼睛（下半圈更浓）、跨过鼻梁的带子，脸颊上另铺一层很淡、几乎只有斑点的红 |
| 鼻子只是一个红点 | `nose()` 把鼻子当成一个小体积：沿鼻梁的管子加圆鼻尖，按光塑形，背光一侧一块紫灰（0.55），鼻尖往下投影，越往下越红 |
| 脸是一张平的白面具 | 塑形的穹顶光尺度 44 → 84，光从更左边来、色阶最低取到 0；四周一圈软的紫灰、眼窝一点灰、近侧脸颊下面一点影子、两颊一层很淡的暖粉；脸的下半截缩短、下巴变圆 |
| 脖子是一块白色的长方块 | 围巾围到下巴，脖子藏起来 |
| 帽子三次都不对：尖顶巫师帽像精灵帽；顶上加一截软管当耷拉的帽尖，像犀牛角、像茶壶把 | 改成一顶软塌的粗麻钟形帽：低圆顶、往下翻的短帽檐（织纹沿帽檐的弧线走）、帽檐边垂下松开的麻线、一圈麻绳打个小蝴蝶结 |
| 粗麻上一根根贯穿的锈色线像缝线、像格子 | `burlap(rust=…)` 默认 0 |
| 远侧那片头发像一只耳机；刘海是一条黑色的护目镜 | 整块头发按同一张受光揉色阶；那片头发的暗边只留在挨着脸的内侧（乘一张脸附近的遮罩）；刘海上半部单独一条光泽带，再加一层对比度低的细发丝 |
| 捧在一起的手套像一只螃蟹、两个面包；换成玻璃罐后，手套把罐子整个挡住 | 手套小一点、从两边扶着罐子下半截，拇指搭在前面；罐子加大到宽 148、高 204 px |
| 围巾和手套的红比小幽灵的光还抢眼 | 毛线色阶的上限 0.85 → 0.68–0.7，围巾的受光接受度 0.8 → 0.45 |
| 袖子在下角多出一圈发白的轮廓 | 袖子顶上那道亮只留在前臂（乘两块前臂附近的软斑） |
| 峰值内存 1.07 GB | 整张的 `wash()` 按行分带算；方向场传函数时只在用到的点上求值；`soften()` 只在形状附近模糊（场景里和库里的遮罩模糊都换成它）；render 按行分带；印刷颗粒在 `ground()` 里先算好；光栅化每带 80 万子像素：0.71–0.81 GB，耗时也从 12.4 秒降到约 10 秒 |
