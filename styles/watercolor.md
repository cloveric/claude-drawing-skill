# 水彩（watercolor）

- **实现**：`lib/watercolor.py` · `Watercolor`
- **范例**：`examples/watercolor_autumn.py` 秋日湖畔（秋树罩染、湖面倒影、红色小舟）；`examples/watercolor_washes.py` 水彩底纹（大片定向晕染、干边、回流水渍、颗粒、飞溅，中间留白，给讲解片当背景、上面叠界面卡片）
- **耗时**：约 15 秒 / 4 秒

## 何时选用

清新风景、花卉 → 水彩；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from watercolor import Watercolor
```

- `paper()`：冷压水彩纸纹理
- 遮罩：`shape(pts, soft, ragged)`，soft 取 1–4 是清晰的水痕边，15–40 是湿画晕开；`band(pts, width)` 是粗笔带状遮罩
- `glaze(mask, 颜色, strength, edge, gran, bloom, variation)`：透明罩染，叠加会像真颜料一样变深、混色
- `gradient_wash(y0, y1, top, bottom)`：湿画渐变天空
- 笔触：`stroke()` 彩色干笔、`line()` 细线勾勒、`lift(mask)` 提白、`splatter()` 甩点
- `soften(mask)` 任意遮罩水彩化边缘；`blobs([(cx, cy, rx, ry)])` 一组团块合成一片（树冠、灌木、云）；`mirror(mask, 水线y)` 水面倒影（带波纹断续）
- `Watercolor.petal_pts(x, y, 角度, 长, 宽)`：花瓣或叶片轮廓；`hexc('#rrggbb')` 转颜色

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 纸纹像砂纸或拉毛墙 | 纸纹受光强度约 0.3，纸纹要细 |
| 叶子中间一圈深色像靶心 | 第二层深色用湿画（soft 约 16）偏向一侧积色，不要同心 |
| 叶梗画到了叶面上 | 先画梗，用 `*(1 - 叶遮罩)` 限制只在叶外 |
| 颜色发脏 | 同一处罩染不超过三层；亮部留白或用 `lift` 提白 |
| 深色团块漂到树冠外，成了孤立的圆点 | 后几层罩染乘以第一层树冠遮罩（稍微扩一点），深色只积在冠内 |
| 树枝乱成一团 | 只画 3–5 根，从树干向上向外伸进树冠，长度按树冠大小算 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
