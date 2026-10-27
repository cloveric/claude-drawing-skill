# 扁平矢量（flatvector）

- **实现**：`lib/flatvector.py` · `FlatVector`
- **范例**：`examples/flatvector_night_camp.py` 山间夜营（七色限定色板，无描边的大块几何形一层层叠起来，层与层之间一道柔和投影，加极细颗粒；夜蓝天空里一轮带橙色光芒的月亮，紫色雪山分出亮面和折线暗面，品红、橙色两种山丘带，黄沙地；下午插在山顶的小旗下，一条虚线小路走之字形下山、穿过山丘，尽头是戴头灯走最后一段路的小小背包客；营地已经亮了：橙色 A 字帐篷门口透出光，篝火的光在沙地上铺成一圈圈平涂光环；几何松树、圆冠树、两朵平底云、一颗流星）
- **耗时**：约 1 秒
- **内部构成**：扁平矢量（分层几何色块、七色限定色板、层间柔和投影、细颗粒）

## 何时选用

风景、户外、旅行与露营、MG 动画式的场景背景和转场、讲解片的「场景 / 旅程 / 夜晚」页、要干净现代又有层次的插画 → 扁平矢量（要撕纸边和蜡笔的手作感用剪纸拼贴；要正等轴的微缩模型用等轴 2.5D；要 80 年代霓虹用复古 Synthwave）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from flatvector import FlatVector
```

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

## 毛病清单（都真实出现过）

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

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
