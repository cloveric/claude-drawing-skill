# 浮世绘木版画（ukiyoe）

- **实现**：`lib/ukiyoe.py` · `Ukiyoe`
- **范例**：`examples/ukiyoe_fuji.py` 富士曙（晕色天空、富士、云带、青海波、帆船、崖松）
- **耗时**：约 7 秒

## 何时选用

日式古典、海浪、富士、东方装饰感 → 浮世绘；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from ukiyoe import Ukiyoe
```

- `block(mask, 颜色)`：印一块平涂色版，带木纹和套印偏移
- `bokashi(mask, 颜色, y_strong, y_fade)`：晕色，从某一边浓到另一边消失，用于天空和海面
- `key(pts, width)`：墨色主版勾线
- 物件：`cloud_band(x0, x1, y, h, glow)` 不透明云带、`seigaiha(mask, 颜色, r)` 青海波纹
- 标题签和朱印：`cartouche(x, y, w, h, '标题')`、`seal()`
- 形状：`poly()`、`rect()`、`circle()`

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 云带半透明，透出后面的轮廓线 | 云带用不透明的色版（strength 超过 1，确保完全盖住） |
| 标题签和云带、主体撞在一起 | 标题签放在天空的空白处，其他元素给它让位 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
