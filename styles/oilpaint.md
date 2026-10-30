# 油画厚涂（oilpaint）

- **实现**：`lib/oilpaint.py` · `OilPainting`
- **范例**：`examples/oil_wheatfield.py` 麦田星空（旋转的星空、麦田、柏树、乌鸦）
- **耗时**：约 2 秒

## 何时选用

浓烈、有笔触质感、名画感 → 油画厚涂；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from oilpaint import OilPainting
```

- 先准备两张图：参考色 `ref`（H×W×3，画面要画成什么颜色）和流向图 `ang`（H×W，每个像素上笔触的角度，比如天空打旋、麦田横扫、树木向上）
- `layer(ref, ang, length, width, density, mask)`：铺一层笔触。先大笔铺底，再中笔，最后只在要紧处（`mask`）加细节笔
- `stroke_at(x, y, angle, length, width, 颜色)`：在指定位置画一笔（乌鸦、签名、点睛）
- `render()` 自动打光：颜料平顶鼓边、有笔毛沟，落笔处更厚

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 笔触像一根根塑料管、橡皮泥 | 凸起要克制：平顶鼓边的截面，高光约 0.1，打光范围约 0.8–1.18 |
| 笔触之间大量露底 | 铺底笔加密（density 约 2），宽笔铺满后再上细笔 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
