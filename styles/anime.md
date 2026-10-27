# 日本动漫（anime）

- **实现**：`lib/anime.py` · `Anime`
- **范例**：`examples/anime_summer.py` 夏空（积雨云、乡间公路、电线杆、草帽女孩背影）
- **耗时**：约 30 秒

## 何时选用

青春、夏日、天空、背景美术 → 日本动漫；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from anime import Anime
```

- `sky(top, mid, horizon_col, horizon)`：天空渐变
- `cumulus(cx, base_y, w, h, light)`：积雨云。许多不规则团块从后往前叠，每团的暗面是「团块减去朝光源偏移的自身」形成的月牙形硬边
- `sun_flare(x, y)`：光晕、光束、镜头光斑；`sparkles()`；最后加 `bloom()` 泛光和 `vignette()` 暗角
- `field(top_y, colours)`：平涂分带的田野；`pole()` 电线杆、`wire(p0, p1, sag)` 下垂电线
- 平涂和线稿：`fill(mask, 颜色)`、`gradient()`、`screen()`；`lines(pts, width, 颜色)` 画干净线稿；`poly()`、`circle()`
- 角色：平涂两色（亮色和阴影色）加深色描边

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 云是一个个正圆泡泡，明暗交界是斜直线 | 用不规则团块，数量多、大小不一；暗面用「团块减去偏移的自身」做成月牙形 |
| 人物腿太长 | 裙摆到膝盖附近，露出的腿约为身高的三分之一 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
