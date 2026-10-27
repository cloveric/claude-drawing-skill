# 复古水粉（gouache）

- **实现**：`lib/gouache.py` · `GouachePortrait`
- **范例**：`examples/gouache_rainy_day.py` 雨天三人像 · Rainy-Day Portraits（米色画板上并排三幅竖长的绘本大头像，每幅一块刷出来的单色背景：浅海玻璃绿底上的老渔夫，黄色防水雨帽上还挂着雨珠、帽檐尖上吊着一滴水，巨大的红鼻子、白色浓眉、大耳朵、一圈白色下巴胡子，藏青麻花毛衣配罗纹领，胸前毛毡口袋里探出一条银色小鱼、张着「O」字嘴，他眯着眼往下看它；绿底上被一顶巨大的芥末黄毛线帽和红白条纹围巾埋住的小孩，橙色大绒球，两只毛线手套捧着一杯冒热气的可可，杯里漂着两块棉花糖，他盯着棉花糖看成了斗鸡眼；蓝到黄渐变底上的高个女士，橙色小卷堆成一座高塔发型，蓝眼影、珍珠耳坠、红色高领、钴蓝大衣配青绿毛毡翻领，斜眼瞟着爬上她肩膀的蜗牛，蜗牛身后的大衣上还有一道发亮的黏液；不透明水粉从暗到亮：托底色、赭色起稿、背景干笔皴擦、平涂大块、几阶色值塑形（鼻子、脸颊、帽子）、帽檐和鼻子下的软投影、粉状腮红、V 字平针与麻花、罗纹、一根根发丝和胡子、毛毡、受光处的干笔高光，最后是印刷书页的纸纹；`--stages` 出 8 个阶段：托底色、起稿、背景、平涂、塑形、质感、五官与道具、高光）
- **耗时**：约 7 秒（成品）/ 约 8 秒（含阶段）
- **内部构成**：复古水粉（托底色的画板与纸纹；不透明水粉：鬃毛条纹、越用越干、挂在纸纹上的干笔，湿笔带起底色；毛边；穹顶光照的几阶色值塑形与球体塑形；软投影、粉状腮红、干笔高光；圆眼、大鼻子、大耳朵；V 字平针、麻花、罗纹；顺着流向的发丝、胡子、绒球、卷发；毛毡；印刷书页的颗粒）

## 何时选用

人物大头像、角色特写、一组人设的「封面像」、温暖怀旧的复古童书 / 绘本插画，要有摸得着的手感（毛衣针脚、毛线帽、胡子和卷发、毛毡），讲解片里「这个人登场」的特写页 → 复古水粉（要线稿加淡彩、「一个人在做一件小事」的速写小卡用钢笔淡彩；要真的动起来的扁平小角色用绘本角色动画；要梵高式厚涂的风景用油画厚涂；要撞色多格的头像用波普丝网）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from gouache import GouachePortrait
```

- 思路：不透明水粉一层盖一层，从暗到亮、从大到小（托底色 → 赭色起稿 → 背景 → 平涂 → 色值塑形 → 质感 → 五官 → 高光 → 印刷颗粒）。
  - 颜料：每一笔都替换下面的颜色（C ← C + (色 − C)·A），湿笔会带起一点底层的颜色（`pickup`）。
  - 纸纹：画板有一张纸纹高度场 `G`。
  - 一笔：扁笔沿短弧拖过去。横向每根鬃毛含色不同，所以顺着笔有条纹、颜色略有深浅；纵向颜料越用越少。含色高时全覆盖，变少后只落在含色多的鬃毛经过纸纹凸起的地方，所以笔尾断成干笔丝和点；两侧毛边，落笔处圆头。
  - 边缘：形状先模糊一像素，再按低频摆动和纸纹重新取阈值，利落但不是矢量边。
  - 塑形：遮罩模糊后按内缘归一化、再开方当穹顶高度（也可以给 `height`；球体用精确椭球）。一盏左上偏正面的光，受光量化成 3–5 个软台阶，映射到五色阶（暗部偏紫红，亮部偏暖白）。先湿铺一遍，再用顺着形体的短笔（等高线方向、顺坡或绕球心）按落点取色盖上去。
  - 针织：每针一个 V（两条斜椭圆、圆柱截面的纱线，带捻股斜纹，相邻行交叠，谷底遮蔽），按光照乘到已有颜料上，大的明暗保留。行可以拱、垂、旋转或沿路径走；麻花是两股交替在前的圆管；罗纹是凸起的正针列和凹下的反针列，每列上有小的人字针。
  - 头发：先画暗色的发团，再沿流向场画成百上千根锥形细线，按受光场从暗到亮分档，暗的先画，少数飞出轮廓。
  - 毛毡：两种尺度的斑驳，加短纤维和轮廓外的绒毛。
  - 最后 `grain()` 叠印刷书页的感觉：纸纹颗粒、亮部的暖纸色、墨色到不了纯黑、饱和度略收。
- 构造：`GouachePortrait(W, H, seed, keep_stages=True, stages_dir=None)`（总像素不超过 4096²）。
  - `panel(x0, y0, w, h)` 新建一块画面并设为当前；之后的坐标都是这块画面里的局部像素。`use(p)` 切换。
  - `ground(tone='#c88f5a', paper, alpha=0.5)` 画米色画板，每块画面刷一层薄的暖色托底。
  - `sketch(mask, colour, width=2.2, alpha=0.8, breaks)` 用稀释的赭色勾出遮罩轮廓，即起稿，会被后面的颜色盖住。
- 形状：返回画面大小的浮点遮罩，用 `np.maximum`、相乘、`1 −` 组合。
  - `ellipse(cx, cy, rx, ry, rot)`、`poly(pts, smooth=True)`、`blob(cx, cy, rx, ry, rough, seed, rot)`
  - `band(path, w0, w1)` 粗路径；`GouachePortrait.tube(path, w0, w1)` 给轮廓点。
  - `rough(mask, amount)` 画出来的毛边。
- 笔：角度一律是度，0 向右，90 向下。
  - `stroke(x, y, angle, length, width, colour, bend, dry, alpha)` 一笔。
  - `strokes(mask, colour 或颜色场, angle 或角度场或 f(x, y), length, width, density, dry, alpha, clip, load)` 在遮罩里撒很多笔，每笔在落点取颜色和方向。`load` < 1 是落笔就半干的皴擦。
  - `dry_brush(path, width, colour, dry, alpha, taper)` 沿折线拖一长笔（热气、长扫）。
- 画：
  - `scumble_background(colour, bottom=None, avoid=人物遮罩, angle, light, dark, scratches, flecks, blend)` 单色或上下渐变的背景：满载的长笔铺底，再用半干的亮、暗两遍皴擦，加短的浅色刮痕和溅点，绕开人物。
  - `block_in(mask, colour, angle)` 平涂一块，返回毛边遮罩。
  - `model_form(mask, colours 五色阶, steps=4, height=None, angle='contour'|'fall'|数|场|函数, relief=0.55, round_=0.5, bias, ambient=0.08)` 几阶色值塑形，返回受光场。
  - `form_light(mask, height, relief)` → (受光 0–1, 高度, 梯度)。
  - `sphere_shade(cx, cy, rx, ry, colours, mask, rot)` 球形塑形：笔触绕球心，下缘有反光。
  - `glaze(mask, colour, alpha, mode='multiply'|'screen'|'normal', soft)` 罩一层。
  - `cast_shadow(caster, dx, dy, soft, alpha, colour, on)` 帽檐、鼻子、胡子下的软投影，只落在 `on` 上。
  - `dry_highlight(mask, colour, above=0.62, angle)` 受光处的干笔高光，穹顶用 `'fall'`。
  - `blush(cx, cy, rx, ry, colour, strength)` 粉状腮红。
  - `dab(x, y, r, colour)` 一小点（高光、扣子）。
  - `line(path, width, colour, alpha, taper, dry)` 小圆笔画线。
  - `spatter(mask, colour, n, size)` 溅点。
- 脸：
  - `eye(cx, cy, r, ry, iris, iris_r, look=(dx, dy), lid, lid_colour, lashes, lash_dir, ring, lower, iris_light)` 圆眼：米白眼球、眼皮下的阴影、深色或青色虹膜（下半亮）、黑瞳孔、白色高光、眼皮和眼皮线、细的暖色外框。`look` 取 1 是贴边，两只眼往里、往下就是斗鸡眼。
  - `nose(cx, cy, rx, ry, colour, on, cast)` 大鼻子：脸上的软投影、球体塑形、下缘反光、鼻孔、柔和的粉白高光加一点白。
  - `ear(cx, cy, rx, ry, colour, side)` 大耳朵。
- 质感：
  - `knit(mask, stitch=(宽, 高), origin, curve, angle, path, cables=[(x, 宽)], strength, highlight)` V 字平针。`curve` > 0 行往下垂，< 0 往上拱；给 `path` 时沿围巾走。
  - `rib(mask, path, period)` 罗纹（领口、袖口、帽檐翻边）。
  - `hair_strands(mask, flow, colours 暗→亮, n, length, width, shade, curl, jitter, roots, clip)` 发丝、眉毛、胡子、绒球、卷发。
  - `felt(mask, strength, fibres, fuzz)` 毛毡。
- 颜色与常量：
  - 颜色用 `PAINTS` 里的名字（vermilion red orange mustard yellow ochre cobalt cerulean navy teal seaglass green olive peach skin ruddy nose rose blush pink umber sienna cream white grey ink brown cocoa）或 '#rrggbb'。
  - `ramp(base, deep, shadow, light, pale, cool, warm)` 给五色阶；皮肤记得给暖的 `cool`。
  - 常量 `PAINTS PAPER LIGHT`；`grain(amount)`、`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 背景像一根根香肠，圆头，颜色一块一块地跳 | 每笔都满载落笔才会这样：底层的长笔触几乎同色（vj 0.012），只在笔尾变干；上面亮、暗两遍落笔就半干（load 0.72–0.74，dry 约 0.5），只挂在纸纹凸起上，断成一道道；托底色先薄铺一层平的，再加笔触 |
| 帽子和脸像扁盘子，亮的是轮廓边而不是面 | 「模糊遮罩开方」的枕头中间平、边缘陡，光又太偏侧：高度改成按遮罩内缘的值归一化、再开方的穹顶，光加正面分量 (-0.44, -0.56, 0.70)，relief 默认 0.55（脸 0.45–0.5） |
| 皮肤暗部发紫发灰，一块一块的 | `ramp()` 默认的冷色偏紫，只适合衣服：皮肤用暖的五阶（#c0705d → #fbe3cc）或 `ramp(..., cool='#a02a3a')`；`model_form` 默认 ambient 0.08，遮罩边缘就不会取到最深一阶，同色的袖子边上也不再冒出孤立的深色短笔 |
| 大红鼻子像迷彩 | 大笔触不透明地铺几阶颜色造成的：`sphere_shade` 改用小笔触、alpha 0.55、密度 3.2、湿底 0.9、色阶交界 soft 0.3 |
| 防水雨帽读成遮阳盔，帽檐像游泳圈，雨珠像铆钉和珍珠，系带像两根筷子 | 去掉冠上的缝线和系带，冠压低变圆；帽檐不按枕头塑形，height 全 0 平涂，下垂的两侧罩暗，底下一条深边，顶面一道亮边；雨珠是透明的：比帽子更饱和的黄、右下一块琥珀色投影、反侧一小块焦散亮斑、很小的白高光，位置打散，不排成一行 |
| 小鱼读成鸟头 | 嘴画在头外面成了一个黑球，眼珠贴边像翻白眼：嘴放进吻端、加一圈浅色唇，眼珠只略偏；鱼身放大，用亮银色压在藏青毛衣上 |
| 围巾像颈枕或香肠，热气从鼻子连到杯子像鼻涕 | 一个 U 形环、两端圆头悬在肩外：改成绕两圈，下卷压在肩上，上卷在下卷上投影，垂下的那一端先画（在两卷后面）；热气两缕从杯口往两边歪，停在围巾上，不碰鼻子 |
| 一塔卷发像一盘肉桂卷 | 每个卷中心最亮、笔触同心：卷改成「环」，中心是暗的空洞，鼓起在 0.5 r 处；卷减到约 30 个，半径 34–60 不等；再加几百根往上梳的长发和少量飞丝，把卷连成一个发型（这一遍不用最深的颜色，深色长线像划痕） |
| 衣领两片像两个靠垫 | 两片圆鼓鼓的领子改成带缺口的平西装领（relief 0.25），领口下露出红高领的 V 区 |
| 质感跑到前面的部件上（高领的罗纹画到翻领上，外套的高光画到杯子上） | `knit`、`rib`、`dry_highlight` 是对遮罩里已有的颜料做乘法或加笔：遮罩先乘 (1 − 前面的部件) |
| 帽子和外套大块干净，像塑料 | 少了最后的干笔高光：`dry_highlight` 只在受光 > 0.62–0.7 的地方拖半干的浅色；穹顶用 `angle='fall'`（顺坡），用 `'contour'` 会画成一个漩涡 |
| 动图里瞳孔和眼皮线发蓝 | 中值切分出来最深的一色是毛衣的藏青：强制放进三个深中性色，另外 9 色只从末帧误差最大（> 18 级）的像素里切 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
