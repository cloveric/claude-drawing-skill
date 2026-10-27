# 复古仪器面板（panel）

- **实现**：`lib/panel.py` · `Panel`
- **范例**：`examples/panel_radio.py` Aurora 64 收音机（柚木机壳、喇叭布、背光刻度窗、琴键、魔眼管、拨杆、旋钮）
- **耗时**：约 7 秒

## 何时选用

设备、仪表、音响收音机、复古科技与产品感 → 复古仪器面板；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from panel import Panel
```

- 所有部件都由同一盏左上方的主光照亮：朝光的边亮、背光的边暗、凸起的部件向右下投影
- 材质：`surface(mask, 材质, 颜色, height)`，材质可选 wood（柚木）、brushed（拉丝铝）、plastic、painted、fabric（喇叭布，`lurex=` 金丝）；`recess(mask, 材质, 颜色, depth)` 下凹的窗口；`background()`、`paint()`、`glow()`、`drop_shadow()`
- 控件：`knob(x, y, r, angle)` 车削旋钮、`button()` 琴键（`pressed=True` 按下）、`toggle()` 拨杆开关、`lamp()` 宝石指示灯、`magic_eye()` 绿色魔眼调谐管、`meter()` 指针表、`screw()` 螺丝、`grille()` 冲孔网、`badge()` 镀铬草书铭牌
- 印刷：`text(s, x, y, size, spacing=)` 丝印字、`scale_arc()` 圆弧刻度、`scale_linear()` 直尺刻度、`glass(mask)` 玻璃反光

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 喇叭布上的金丝像一排点点，看着像冲孔板 | 金丝纬线要长浮（压过三根经线再钻下一根），闪光沿线缓慢变化 |
| 刻度单位和最后一个数字挤在一起 | 单位放到刻度末端外侧，或者直接写完整数值（530…1600 kHz） |
| 浅色字印在浅色喇叭布上看不见 | 丝印颜色要和底材拉开明度 |
| 一大片喇叭布太平、太假 | 布是半透明的：把后面喇叭的圆形暗影淡淡透出来 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
