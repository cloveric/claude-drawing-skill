# 韩国彩铅（colorpencil）

- **实现**：`lib/colorpencil.py` · `ColorPencil`
- **范例**：`examples/colorpencil_dessert.py` 午后甜点（草莓蛋糕、红茶、草莓）
- **耗时**：约 17 秒

## 何时选用

甜点、小物、日常可爱 → 韩国彩铅；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from colorpencil import ColorPencil
```

- `paper()`：细纸纹
- 遮罩：`mask_poly(pts)`、`mask_blob()`、`mask_ellipse()`
- `hatch(mask, 颜色, pressure, angle)`：短排线铺色。蜡只挂在纸纹凸起上，pressure 越大越能压进凹处；边缘自动变淡
- `shade(mask, 颜色, angle=另一个角度)`：交叉排线加阴影
- `outline(pts, '#8a6a5a')`：浅褐色铅笔勾线；`line(pts)` 用于不闭合的线
- `sparkle(x, y, r)` 白色高光笔；`dots(mask, 颜色)` 草莓籽、糖粒之类
- 白色物体不要用白色画（白纸上看不见）：用暖奶白色，配淡紫灰或淡蓝灰阴影

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 颜色淡得几乎看不见 | 排线要够密（叠加后趋于饱和）；颗粒阈值不要卡太狠，用 pressure 控制能压进多少纸纹 |
| 奶油、白瓷等白色物体消失 | 用暖奶白色铺底，配淡紫灰或淡蓝灰阴影，再加一点白色高光 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
