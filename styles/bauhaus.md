# 包豪斯几何（bauhaus）

- **实现**：`lib/bauhaus.py` · `Bauhaus`
- **范例**：`examples/bauhaus_form_colour.py` 形与色 · Form & Colour（奶油色纸上的丝网印刷讲座海报：黄三角、红方、蓝圆站在粗黑地线上，60° 弧、直角框、挖空的圆心和半径，下面大字角数 3 / 4 / 0；「形与色」大标题、挖空字的黑条论点「角越尖，色越亮」；构成网格、套准十字、裁切线、色标条、铅笔版号）
- **耗时**：约 2 秒
- **内部构成**：包豪斯几何（丝网印刷海报）

## 何时选用

设计感海报、讲座 / 展览 / 活动海报、概念图解（形状、比例、对比、原则）、讲解片里的「定义 / 原理」页 → 包豪斯几何；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from bauhaus import Bauhaus
```

- 思路：画面是一张丝网印刷的印张，每种颜色一块网版，先浅后深逐版刮印；同一色版上的所有东西共享这块版的套准误差（平移加极小旋转），所以色块和黑线相接处会露出一丝纸白或压出一道深边
- 纸：`paper(colour, margin, module)` 奶油色未涂布纸（云状纸浆、短纤维、纸屑、纸齿、微微不平的受光），同时设定设计区和网格模数；`at(col, row)` 网格坐标转像素；`grid()` 用浅灰色版印构成网格
- 遮罩（全画布、抗锯齿，可以相加相减）：`circle()`、`ring()`、`sector(cx, cy, r, a0, a1)` 半圆和四分之一圆、`arc()`、`rect(x0, y0, x1, y1, rot)`、`bar(x0, y0, x1, y1, width, cap='butt'|'square'|'round')` 粗黑条和细线、`poly()`、`triangle(x0, x1, base_y)`（默认正三角）
- 印刷：`pull(mask, ink, knock, edge, density, opacity)` 刮一版：墨膜顺刮板方向有条纹、行程末端变薄，薄处露出纸齿坑点，网版灰尘留针孔，版边有网目锯齿、边缘略积墨；墨半透明（黄最透、黑最不透），叠印变深。`knock` 是挖空遮罩，`edge=0` 让细线保持干净
- 文字：`text(s, x, y, size, ink, font, anchor, spacing, rot, weight)` 直接印；`text_mask()` 取遮罩用来挖空；font 用 geo（Futura Bold）、geo_book、geo_cond（窄体特粗）、cjk（粗黑体）、cjk_book，中西文逐字换字体；`text_width()` 量宽度
- 印刷标记：`marks(targets, crop, bar, inks, overprints)` 套准十字、四角裁切线、色标条。登记后每块色版第一次刮印时自动印上自己那一份，所以十字会叠成几色错开的样子
- 印完之后：`pencil(s, x, y, size)` 页边铅笔版号，石墨只挂在纸齿凸起上
- 颜色常量 `YELLOW RED BLUE BLACK`，纸色 `PAPER`，网格色 `TINT`；角度逆时针为正，0° 指 3 点钟；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

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

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
