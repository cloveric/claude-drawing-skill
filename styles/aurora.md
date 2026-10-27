# 弥散玻璃（aurora）

- **实现**：`lib/aurora.py` · `Aurora`
- **范例**：`examples/aurora_morning.py` 晨间计划（日出色弥散渐变与极光光带、光泽小球；磨砂玻璃卡片层叠：晨间计划时间线（3/5 完成，进行中那一行是玻璃叠玻璃）、专注倒计时圆环、光泽太阳躲在玻璃云后的天气卡、勿扰开关与白噪音滑块、近 7 天专注柱状图、9:00 站会提醒胶囊）
- **耗时**：约 2 秒
- **内部构成**：弥散玻璃（弥散渐变 · 玻璃拟态）

## 何时选用

产品界面、App / 小组件展示、效率工具与数据面板、明亮通透的科技感、讲解片的「功能 / 界面」页 → 弥散玻璃（要暗夜霓虹氛围仍用赛博朋克）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from aurora import Aurora
```

- 思路：一块明亮的「光屏」（弥散渐变）上面悬着几片真的磨砂玻璃。透过玻璃看到的是它下面**真实像素**的高斯模糊（背景、小球、后面的卡片和字都算），再蒙一层白纱，界面印在玻璃上。先画的在后面，后画的卡片会把前面画好的卡片连字一起模糊
- 背景：`backdrop(base, blobs=[(x, y, rx, ry, 颜色, 强度)], ribbons=[(点列, 宽, 颜色, 强度)], warp, grain)` 网格渐变：色团按权重在 OKLab 里混色，坐标扭曲成不规则形状，光带沿样条走，自带细颗粒；`sparkles(n)` 零星光点；`orb(cx, cy, r, (亮, 中, 暗))` 光泽小球：虹彩色阶、菲涅尔边缘映出背景色、高光、落在背景上的彩色投影
- 玻璃：`glass(x0, y0, x1, y1, radius, blur, tint, sat, shadow, elevation, bevel, rim, sheen)` 返回 `Card`（x0 y0 x1 y1 w h cx cy r）。blur 是磨砂程度（约 20–30）；tint 是白纱（约 0.24，近光源一侧厚）；sat 是透过来的颜色饱和度（约 1.5）；bevel 是边缘斜面，向外折射，各色通道偏移不同，带很淡的色散；rim 是朝光边的高光描边；阴影只落在卡片外，颜色取自下面的背景。`pill()` 是小玻璃胶囊（按钮、提醒、高亮行，玻璃叠玻璃），`cloud(cx, cy, w)` 是玻璃云
- 形状（带符号距离场，1 px 解析抗锯齿）：`rrect()`、`circle(ring=线宽)`、`line(点列, smooth)`，都可以传 `grad=色阶, angle=`；`divider()` 是蚀刻细线
- 控件：`toggle(x, y, on)`、`slider(x0, x1, y, value)`、`knob()`、`ring(cx, cy, r, width, frac)`（从 12 点顺时针，锥形渐变、圆头、光晕、末端白点）、`check(cx, cy, r, 'done'|'now'|'todo')`、`bars(x0, y0, x1, y1, values, labels=, highlight=)`、`spark(x0, y0, x1, y1, values, dots=)`（返回各点坐标）、`sun()`、`app_icon(x, y, size, grad, glyph)`
- 文字 `text(s, x, y, size, fill, weight='light'|'regular'|'medium'|'semibold'|'bold', anchor, alpha, spacing, grad)`：西文用 SF（按字号调光学尺寸），中文用苹方，自动分段；anchor 第二个字母 s 基线、m 居中、t 顶、b 底；`text_width()` 量宽度
- 颜色：`INK` 深靛文字；渐变色阶 `WARM`（杏→粉→紫）、`COOL`（天蓝→长春花→紫）、`MINT`；`ramp(t, stops)`、`mix()` 在 OKLab 里插值。一种渐变只代表一件事
- `save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 前面的卡片压住后面卡片的字（「周三」「60%」被切掉一半） | 卡片只在对方的内边距里重叠（不超过内边距），文字离重叠区远一点 |
| 列表最后一行和底部按钮撞在一起 | 先按行距（约 84）算好列表总高，按钮从卡片底边往上放，不够就加高卡片 |
| 玻璃太「奶」，像磨砂塑料，后面的东西透不出来 | 白纱 tint 约 0.24（近光源一侧厚、另一侧薄），saturate 约 1.5；背景色团之间要有足够的色相差 |
| 小球刚好顶在卡片边上，像放在卡片上面 | 让小球三到四成真正压在玻璃后面，模糊的那一半才读得出「透过玻璃」；小球也别和卡片边相切 |
| 背景的色团和光带几乎全被卡片挡住 | 光带穿过卡片之间的空隙走，色团饱和度提一点 |
| 折线图的面积填充在末端成了一团紫雾 | 填充 alpha 约 0.16，两端各 22 px 渐隐（已处理） |
| 柱状图柱子太细，满高的空槽像幽灵柱，「一」看着像减号 | 柱宽取间距的一半，空槽 alpha 0.1；横轴用日期加「今天」 |
| 动图调色板被浅色背景占满，渐变控件量化成灰，小球出现等高线色带 | 调色板样本给饱和像素加权（×6 / ×3，暗色 ×4），每帧叠同一张 4×4 Bayer 抖动（约 ±2.4 级）：逐帧不变，「和上一帧相同」的透明差分照样有效 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
