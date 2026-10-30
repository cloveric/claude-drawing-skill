# 像素风（pixelart）

- **实现**：`lib/pixelart.py` · `PixelArt`
- **范例**：`examples/pixel_rainy_cafe.py` 雨夜咖啡店（霓虹、路灯、雨、倒影、猫）
- **耗时**：约 0.1 秒

## 何时选用

复古游戏、夜景霓虹、小尺寸动画 → 像素风；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from pixelart import PixelArt
```

- 在低分辨率上画（默认 320×180，放大 6 倍）。坐标都是整数像素
- 画形状：`rect()`、`poly()`、`circle()`、`line()`（Bresenham 直线）、`outline(mask)`、`put(x, y)`
- 抖动：`gradient(x0, y0, x1, y1, c0, c1, steps)` 分带渐变，带与带之间用抖动过渡；`dither(mask, 颜色, alpha)` 按 Bayer 矩阵抖动上色；`glow(cx, cy, r, 颜色)` 抖动光晕
- 其他：`text('CAFE', x, y, 颜色, size)` 3×5 像素字、`rain()` 雨丝
- 交付用 PNG（无损），像素才清晰

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 背景底部露出一条黑带 | 天空渐变和楼群都要铺到地面线，不留缝 |
| 光晕变成一大块方形点阵 | 光晕半径要小（约 20 像素）、强度约 0.4–0.5；霓虹光晕压扁一些 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
