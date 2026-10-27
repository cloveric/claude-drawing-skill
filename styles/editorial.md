# 编辑风手绘（editorial）

- **实现**：`lib/editorial.py` · `Editorial`
- **范例**：`examples/editorial_ideas.py` 灵感生长（浇水长出灯泡的概念插画）
- **耗时**：约 11 秒

## 何时选用

观点、概念、商业文章配图 → 编辑风手绘；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from editorial import Editorial
```

- 形状：`circle()`、`ellipse()`、`rrect()` 圆角矩形、`blob()`、`poly()`
- `fill(mask, 专色)`：印一层专色油墨，带颗粒、浓淡不匀、套色错位，并**叠印**（重叠处颜色相乘）
- `halftone(mask, 专色, cell, angle, amount)`：半调网点做明暗
- `line(pts, 墨色, width, wobble, breaks)`：歪扭的手绘墨线；`dashes()` 虚线；`stars()` 小十字星
- 专色控制在 4–5 种，并刻意让它们互相重叠，叠出第三种颜色

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 色块死板，像电脑矢量图 | 每层专色都要有颗粒、浓淡不匀和几像素的套色错位 |
| 颜色太多太杂 | 4–5 种专色，靠叠印得到其他颜色（比如青叠黄出绿） |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
