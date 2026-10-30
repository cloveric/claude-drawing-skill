# 色粉小像（pastelvignette）

- **实现**：`lib/pastelvignette.py` · `PastelVignette`
- **范例**：`examples/pastelvignette_marmalade_scarf.py` 橘猫围巾 · The Marmalade Scarf（1920×1080 的白底角色小像，软色粉加一点水粉：冷天的早上，一个年轻女人把她的大橘猫当围巾围在脖子上——猫头和两只前爪从她一边肩上垂下来，一只后爪和带深色环纹的尾巴从另一边垂在大衣前面；她朝猫歪着头、斜眼看它、抿着嘴笑，猫用一双圆圆的琥珀色眼睛抬头看她；蓝黑色的长波浪发，侧分的刘海斜过额头，大圆眼、深棕虹膜和白高光，两大圈腮红，红鼻尖，小嘴；浅粉蓝的大衣看得见顺着衣褶和袖子的干笔，大衣下摆在白纸上干笔散开，里面是奶油色的罗纹毛衣；猫毛先铺一层宽的软笔触，再一簇簇细毛、受光处的浅色毛尖、额头几道深色虎纹，轮廓蓬松地融进后面的头发和大衣，奶白的嘴套和爪子、粉色的耳朵里、白胡子；背后左边一枝桉树叶（夹几片赭黄的），右边一层很淡的铅笔小镇（几栋房子和一座圆顶塔），其余都是白纸；照色粉插画师的顺序画：空纸 → 铅笔起稿 → 桉树枝和铅笔小镇 → 平涂大块 → 塑形（揉开的脸、大衣的干笔）→ 猫毛 → 一绺绺的头发 → 五官 → 干笔高光和飞出来的几根头发；`--stages` 出 8 个阶段加成品）
- **耗时**：约 9 秒

## 何时选用

一两个讨喜的角色的小像：一个人和他的小动物（猫、狗、狐狸）、温柔的一刻（抱着、依偎、对视）、人设卡和头像，要一眼就是「绘本里的色粉加一点水粉」——白纸上不画背景，画到边上就干笔散开，大圆眼、大腮红、红鼻尖，一根根的发丝和蓬松的毛，柔和的粉彩色里只有一种暖橙，讲解片里「这个人 / 这只宠物 / 陪伴」的页，小红书头像和封面 → 色粉小像（要复古童书味、背后刷一块单色、看得见毛衣针脚的大头像用复古水粉；要满画面彩铅叠涂、有天空有场景的黄昏绘本页用暖调彩铅绘本；要软蓝限色、乱线墨线的绘本跨页用蓝调绘本；要针管笔线稿加淡彩的速写小卡用钢笔淡彩；要明亮可爱的彩铅甜品小物用韩国彩铅）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from pastelvignette import PastelVignette
```

**色粉小像 `PastelVignette`**：
- 思路：照色粉插画师的顺序画一张白底小像（空纸 → 铅笔起稿 → 背景的一枝叶子和很淡的铅笔小镇 → 平涂大块 → 塑形 → 毛 → 头发 → 五官 → 干笔高光和飞丝），画到边上就停：没有背景色块、没有边框，颜色在边上干笔散进白纸。
  - 纸：白纸，直方图均衡过的纸纹 `T`（0–1 均匀分布），所以「色粉挂在纸纹高于 1 − 压力的地方」直接就是覆盖率；预先算好沿 8 个方向拖开的纸纹（存成 uint8），每一笔按自己的方向取，漏掉的纸坑顺着笔拉成短道。颜料缓冲 `F` 记录纸坑里已经有多少色粉，后面的层能压得深一点。空白纸上的纸纹只差 0.6%，白纸才干净。
  - 一笔：中心线在方向场里积分出来（方向按 mod π 处理），带一点手腕的弧度。几万笔一次画完：Pillow 把每一笔的每一段按各自的序号画进 2 倍超采样的整数 id 图（每段略微加长，转弯处不缺口），numpy 对被盖住的子像素查回这一段，算出沿笔的位置（落笔重、收笔挑的压力曲线，两头收圆，不是尺子画的方头）和横向位置（两侧软边，加几道鬃毛条纹——笔越用越干，条纹越开），压力够得着的纸纹才挂上色粉，再用 bincount 汇回像素。同一批里最上面那笔说了算，层次靠多遍叠；一批太大就按 y 分成几条带（省内存）。
  - 颜料：色粉近乎不透明：新 = 旧 + 覆盖 ×（目标 − 旧），目标 =（1 − opacity）× 旧 × 颜色 / 纸色 + opacity × 颜色。所以浅色的干笔能压在深色上（粉蓝上的白笔触），薄的一层只是染一下。
  - 揉开：`wash()` 是用手指揉开的色粉（或一层薄水粉）：平滑、不透明，颜色可以是一张场（按受光查色阶），最深的纸坑留一点浅，边缘在软边里按纸纹断开，不是矢量边；`model()` 给形状一个软穹顶光，按光把色阶揉上去（脸、毛的底色、大衣）。
  - 散开：小像没有边框。大衣的揉色用一张平滑的渐隐场收掉（不要在边上断成纸纹白点），干笔在它下面再走一段，按渐隐场（`fade`）逐像素减压、变干，停在不同的地方；`ragged()` 给一块颜色一条低频游走的边（只在原形状附近游走，不会在远处长出孤岛）。
  - 头发和毛：`strands()` 沿流向场画几百到几千根细丝，每根有自己的偏移和稳定的弯（`curl`），按光泽场从暗到亮分档，暗的先画；`lock=(根数, 宽)` 把它们分成一绺绺（同一绺共用起点区域、偏移、弯曲和明暗），头发才是卷成绺的，不是梳过的直线；少数不裁切、飞出轮廓。`fur()` 是一簇簇的毛：根部散开、尖端聚拢，背光一侧暗一点。`fluff()` 在轮廓里侧种短丝、往外长，颜色取它里面几 px 的颜料（受光一侧提亮一点），所以毛茸茸的边融进后面的东西。
  - 五官：`eye()` 大圆眼：米白眼球、上眼皮下一层灰蓝的影子、深色虹膜（下半亮、外圈暗、有放射细纹）、瞳孔、上眼皮盖住一点虹膜、一道深色的软眼线在外眼角挑出去、很淡的双眼皮和下眼线、两点白高光；`blush()` 一大圈粉状腮红，越往外越只挂在纸纹上；`nose()` 鼻梁背光一侧一道软影子加红鼻尖和一点高光；`mouth()` 小嘴；`brow()` 一条软的色粉带加几根细毛。
  - 收尾：`finish()` 只记参数、在 render 里加（每张阶段快照都和成品一致，要在画第一笔之前调用）：轻微柔化、细颗粒、上了色的地方一点暖色，白纸不变。
- 构造：`PastelVignette(W, H, seed, keep_stages=True, stages_dir=None)`（总像素不超过 4096²），先 `finish()` 再 `paper(tone, tooth)`。坐标是整张画布的像素；给方向场传一个数就是角度（度，0 向右、90 向下），方向场数组是弧度；`LIGHT` 是默认光（左上、略朝前）。
- 遮罩：`poly(pts, smooth)`、`ellipse(cx, cy, rx, ry, rot)`、`blob(cx, cy, rx, ry, rough)`、`tube(path, w0, w1)`（`w0` 可以是一串沿路径的宽度；`tube_pts()` 给轮廓点）、`rect(x0, y0, x1, y1)`、`below(xs, ys, invert)` 返回画布大小的浮点遮罩；`ragged(mask, amp, scale, edge)` 给一块颜色一条没画完的干边。
- 方向场：`flow(角度, 扰动, 尺度)`、`field(f(x, y) → 度)`、`radial(cx, cy, offset)`、`contour(mask, sigma, offset, fallback)`（只在形状附近算）、`blend(f1, f2, w)`（双倍角混合）、`rotate()`；`value(top, bottom, y0, y1)` 竖向的 0–1 场；`shading(mask, light, sigma, wrap)` 软穹顶的受光。
- 笔触：`strokes(region, field, colour, length, width, density, pressure, opacity, alpha, streak, soft, taper, passes, clip, avoid, fade)`。`region` 是落笔概率遮罩或 (x0, y0, x1, y1)；`colour` 给颜料、一串颜料（随机取）、(色阶, 场或 f(x, y)) 或 f(x, y) → (N, 3)；`streak` 鬃毛条纹的强弱，`soft` 两侧软边占半宽的比例；`fade` 默认是区域^0.65，区域淡出的地方笔触变干、断开。`lines(paths, …)` 画给定的折线；`pencil(path, colour, width, alpha)` 很淡的铅笔线（几笔叠成、有的断开）。
- 色层：`wash(mask, colour, alpha, grain, edge, dry, clip, opacity)`；`model(mask, colours, light, lit, sigma, wrap, gamma, lo, hi)` 返回受光场；`glaze(mask, colour, alpha, mode)`（multiply / screen / normal）；`dab(x, y, r, colour, alpha, soft)` 一小点（高光）；`line(path, width, colour, alpha, taper, dry)` 平滑的细圆笔线（眼线、胡子、软轮廓）。
- 头发和毛：`strands(region, flow, colours 暗→亮, n, length, width, curl, jitter, shade, spread, alpha, clip, roots, lock)`（`flow` 是度数、弧度场或 f(x, y) → 度）；`fur(region, field, colour, length, width, density, tuft, spread, curl, converge, side, light)`；`fluff(mask, length, n, width, out, field, alpha, lift, light)`。
- 五官：`eye(cx, cy, rx, ry, iris, iris_light, iris_r, look, lid, lid_skin, line_colour, line_w, flick, lashes, crease, lower, rot, side)`（`side` 是外眼角朝哪边，`look` 取 -1..1）；`brow(path, width, colour)`；`blush(cx, cy, rx, ry, colour, strength)`；`nose(x, y, size, side, tip, bridge, shade)`；`mouth(x, y, w, smile, colour, dark)`。
- 植物：`leaf(base, tip, width, colours, bend)` 一片叶子（受光一侧浅、浅色叶脉、几笔干笔）；`sprig(path, n, size, colours, width, round_, spread, fade)` 一枝带叶的枝条（`fade(y)` 让叶子往根部淡下去）。
- 收尾：`finish(soft, grain, warmth)`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。
- 颜色用 `PAINTS` 里的名字（paper white chalk pencil pencil_light graphite；skin skin_light skin_pale skin_shade skin_deep blush nose lip lip_dark lid brow crease；eye_white eye_shade iris iris_light pupil amber amber_light olive_eye；hair_black hair_dark hair hair_blue hair_grey hair_light；powder_deep powder_shade powder powder_light powder_pale cream cream_shade cream_deep ivory；ginger_deep ginger_dark ginger orange tangerine apricot peach butter mustard fur_cream fur_white ear_pink；eucalyptus_deep eucalyptus eucalyptus_light sage olive ochre stem mist umber）或 '#rrggbb'；色阶用 `RAMPS` 里的名字（skin neck powder cream ginger hair eucalyptus ochre mist，都是暗 → 亮）或自己给一串颜色。
- 范例的场景脚本先把所有形状的遮罩算好（`plan()`），再按从前往后的遮挡算出每块「看得见的部分」（刘海 > 猫 > 脸 > 脖子 > 猫身后的那绺头发 > 毛衣 > 大衣 > 后面的头发），每一层只往自己看得见的部分上画；留着的 37 张画布大小的遮罩和受光场存成 float16。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 大衣上的笔触是一粒粒米、一道道雨：短、窄、一样宽，方头 | 笔的两头按沿笔位置收窄（落笔圆、收笔挑），宽度 18–34 px、长 70–180 px，两侧软边占半宽的 0.6，颜色只在受光色阶上下浮动（加一张 46 px 尺度的噪声），不是一深一浅地跳 |
| `ragged()` 在大衣外面远处长出一个个蓝色孤岛 | 原来是把噪声加到模糊遮罩上再取阈值，遮罩是 0 的地方也会过线：改成阈值本身在 0.14–0.86 之间游走，边只在原形状附近摆动 |
| 大衣下摆是一条撕纸边；改成渐隐后又成了一条白点的霜带；再把笔触往下拖，成了一道道往下流的颜料 | 揉开的底色用一张平滑的渐隐场收掉，边上少断成纸纹白点（平涂那层 `edge` 0.9 → 0.15，塑形那层 0.5）；干笔的落笔区比底色多走约 45 px，按同一张渐隐场逐像素减压变干；下摆的笔触按衣摆的褶往中线斜（左半边从左上到右下、右半边从右上到左下，最多偏 32°），不再垂直往下 |
| 大衣的深色笔触像一道道抓痕：亮的鬃毛条纹在深色上特别显 | 深色笔触加宽到 20–34 px、拉长到 90–180 px，软边 0.85，条纹 0.2，alpha 0.45 |
| 猫身在她脖子前面是一块没有毛的橙色平涂 | 平涂、塑形、画毛用的遮罩不一致（平涂包括脖子那段，后面两步把它扣掉了）：先按从前往后的遮挡把每块「看得见的部分」一次算好，每一层都只用它 |
| 猫趴在她肩上像一条均匀的橙色长管（羽毛围巾），脖子是一根长长的粉色柱子 | 猫身改成从前面绕过她脖子：靠猫头的胸口和另一头的胯部粗（130 px），中间的肚子细（88 px）、往下垂；另一边加一只垂下来的后腿和爪子，和尾巴一起垂在大衣前面；脖子只露下巴下面一小段 |
| 猫毛像刺猬：满身又亮又硬的细刺，轮廓一圈硬毛 | 先按受光色阶铺一层宽的软笔触（5–10 px、alpha 0.55），主体的细毛簇 alpha 0.5–0.55、密度 0.45–0.6；轮廓的 `fluff()` 定数量（头 900 根、身子 900 根）、alpha 0.45–0.5，颜色取它里面几 px 的颜料 |
| 猫的眼睛上沿被一条橙色眼皮压平，像在生气；尾巴尖是平切的管子口 | 猫眼 `lid=0`，只留深色的眼眶；尾巴末端加一个圆，再铺奶白的毛尖 |
| 头发是一顶头盔，中分；右半边额头一直秃到头顶 | 侧分：分缝右边补一片从分缝扫到太阳穴的头发；头发外轮廓按低频起伏推出去（振幅 12 px），下面是一绺绺的波浪 |
| 刘海的下沿顺着脸的轮廓走，露出来的额头还是一个完整的蛋形 | 刘海的下沿横过额头：分缝那头高、远侧那头低，在眉毛上方 20–30 px 处斜着收过去 |
| 头发是一根根梳过的平行细线 | `strands(lock=(14, 10))`：每 14 根一绺，共用起点区域、偏移、弯曲和明暗，下摆的流向按 sin 起伏 ±24° |
| 头顶飞出来一把长直线，像划痕 | 头发边上的飞丝只留 50 根（刘海另 14 根），弯曲 2.0、偏移 20°、alpha 0.6 |
| 睫毛是一把梳子；眼白一圈包着虹膜，像在瞪眼 | 不画单根睫毛，眼线在外眼角挑出去（`flick` 0.32–0.38）；上眼皮盖住虹膜上沿（`lid` 0.12 → 0.2） |
| 眉毛又细又碎、内高外低，一脸担心 | 眉毛先铺一条软的色粉带（宽 1.25 倍、alpha 0.35），再一条 0.7 倍宽的（alpha 0.55），细毛 40 → 24 根、alpha 0.7 → 0.45；眉峰放中间，内端不抬高 |
| 腮红太淡太小，不是参考图那种「一大圈」 | 半径加到 60–76 px，强度 0.6 → 0.72 |
| 她看起来像个小孩 | 眼睛放在圆脸里偏下就是小孩的比例：眼线挪到头的正中间（脸的局部坐标 v 20 → 2），下巴收窄变尖，眼睛小一圈，鼻子拉长；单靠变小眼睛不够 |
| 鼻子只是一个红点 | `nose()` 加 `shade`：鼻梁背光一侧那道软影子从 0.28 加到 0.5，再加红鼻尖 |
| 背后的铅笔小镇是一块灰色的污渍 | 灰色的揉色只留 0.16，往下、往两边淡掉，大部分只是铅笔线 |
| 第二枝桉树枝和主枝交叉成一个 X；叶子排成一架梯子 | 去掉第二枝；叶子沿枝条的位置随机错开 ±0.3 个间距，角度的随机偏差 8° → 14°，大小 56–108 px |
| 峰值内存 0.92 GB | 光栅化的子像素数组从 int64 / float64 改成 int32 / float32，一批笔的包围盒超过 250 万个子像素就按 y 分带；8 个方向的纸纹存成 uint8（66 MB → 17 MB）；`contour()` 只在形状附近算；场景里留着的 37 张画布大小的遮罩和受光场一赋值就转成 float16：0.74–0.77 GB；和改之前的成品比，p99 差 0 级，只有猫头附近 1141 个像素差 10 级以上，看不出来 |
