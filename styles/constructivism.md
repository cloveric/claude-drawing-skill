# 苏联构成主义（constructivism）

- **实现**：`lib/constructivism.py` · `Constructivism`
- **范例**：`examples/constructivism_radio.py` 无线电 · РАДИО（虚构的 1920 年代无线电爱好者杂志封面，红黑两版：仰拍的双曲面网格广播塔印成网点、叠在红色圆盘上，塔尖射出红色楔形和越传越细的黑色波前，送进剪刀剪下的网点照片——带号角喇叭的电子管收音机；黑色斜条里反白 СЛУШАЙТЕ ВЕСЬ МИР（收听全世界），粗体压缩西里尔大字 РАДИО，三个编号标注；对折两次的折痕裂墨、霉斑、水渍潮线、图钉锈孔）
- **耗时**：约 6 秒
- **内部构成**：苏联构成主义（红黑两版、套印错位、网点照片拼贴、剪刀留边、折痕老化）

## 何时选用

工业、技术、发明史，「从 A 传到 B」的原理图解（广播、电报、铁路、流水线），强对角线的海报和杂志封面，讲解片里的「年代 / 历史 / 先驱」页，需要老照片质感又不能用真人照片 → 苏联构成主义（不写政治口号；要三原色几何讲座海报用包豪斯几何，要剪报和勒索信字用报刊拼贴）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from constructivism import Constructivism
```

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

## 毛病清单（都真实出现过）

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

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
