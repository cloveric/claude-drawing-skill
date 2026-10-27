# 剪纸拼贴（papercut）

- **实现**：`lib/papercut.py` · `Collage`
- **范例**：`examples/papercut_balloons.py` 热气球小镇（条纹热气球、笑脸太阳、纸云、小房子）
- **耗时**：约 30 秒

## 何时选用

童趣、温暖、讲故事 → 剪纸拼贴；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from papercut import Collage
```

- `background(颜色, texture)`
- `piece(pts 或 mask, 颜色, texture, torn, rim, shadow)`：贴一张纸。torn 是撕边程度，rim 是撕口白边，shadow 是纸片阴影；texture 可选 paper / kraft / crayon / newsprint / notebook
- 形状遮罩：`circle_mask()`、`cloud_mask()`、`Collage.star_pts()`
- 蜡笔和光：`crayon(pts, width, 颜色)` 蜡笔线、`dot()`、`glow()`
- `face(cx, cy, r, mood='smile'|'sleep'|'dots')`：笑眼、嘴、腮红
- `text(s, x, y, size, 颜色, vertical)`

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 大面积蜡笔纹像满屏刮痕 | 大色块用 paper / kraft，蜡笔只用在点缀或小物件上 |
| 撕纸白边看不见 | 白边要宽出 5–8 像素（大半径模糊加低阈值），并且只出现在部分边缘上 |
| 画面顶边或左边多出一条阴影 | 阴影偏移不能用会首尾相接的循环平移，要用补零平移（已修） |
| 月亮画了光芒，像太阳 | 月亮用蜡笔光圈加几颗闪光，不要放射线 |
| 脸的五官太粗太凶 | 线宽约 r×0.035，腮红用 `glow` |
| 小鸟画成了一团 | 小鸟用两道细弧线（线宽约 2.6），不要用很短的粗笔 |
| 纸片被画面边缘切掉 | 云、气球这类主体要完整留在画面内，留出边距 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
