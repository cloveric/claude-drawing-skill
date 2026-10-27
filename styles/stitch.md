# 十字绣（stitch）

- **实现**：`lib/stitch.py` · `Stitch`
- **范例**：`examples/stitch_sampler.py` 家（H♥ME 字母、缎面绣爱心、小屋、苹果树、松树、花边、缝上的布标）
- **耗时**：约 20 秒

## 何时选用

家、温馨、手作礼物、贺卡、名字和字母 → 十字绣；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from stitch import Stitch
```

- 一切都在布孔的格子上（`cell` 像素一格）。`cells(mask)` 把像素遮罩变成格子，`at(gx, gy)` 取格子中心
- 针法：`cross(格子, 颜色)` 十字绣、`half(格子, 颜色)` 半针（天空、云、烟）、`back(pts, 颜色, step)` 回针（路径吸附到孔上，一针约 step 格）、`running(pts)` 平针虚线、`satin(mask, 颜色, angle)` 缎面绣（鼓起、有光泽）、`satin_text(s, x, y, size)`、`knot(x, y, 颜色)` 法式结
- 图样：`chart(['..#..', '.###.'], gx, gy, {'#': 颜色})` 按字符图绣；`letters('HOME', gx, gy, 颜色, scale)` 5×7 字母
- `label(x0, y0, x1, y1, 'EST. 2026')` 缝上去的织标

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 斜向的短线（太阳光芒）被吸附成一串 L 形台阶 | 短斜线就绣一针，从孔到孔（`step` 设大） |
| 半针叠在十字绣上，像贴了一层纹理 | 真实绣法不会这样叠：亮部直接换浅一号的线绣十字 |
| 烟囱被屋顶整个盖住、烟线穿过标题 | 先算好屋顶轮廓再定烟囱高度；烟用半针小烟团，往留白处飘 |
| 布面格子太黑，像方格纸 | 布孔暗度约 0.34，布块起伏约 0.065 |
| 花朵和松树重叠 | 摆放前按格子算好每样东西占的列 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
