# 形变动画（morph）

- **实现**：`lib/morph.py` · `Morph`
- **范例**：`examples/morph_water_cycle.py` 一滴水的旅程（一条 256 点轮廓线依次变成水滴→云→雪花→雪山→河→海浪，六块纯色背景随之切换；洋葱皮残影、挤压拉伸、虚线运动轨迹、中间帧标出对应点、缓动曲线时间轴）
- **耗时**：约 1 秒

## 何时选用

过程、变化、循环、「从 A 变成 B」的小故事，讲解片的转场、片头和「演变」页 → 形变动画（要真的动起来，用 `Morph.at` 逐帧出图）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from morph import Morph
```

- 思路：每样东西都是**一条**闭合轮廓；两条轮廓重采样成同样点数（默认 `Morph.N = 256`）、统一绕向、对齐起点，再逐点插值，就是形变；背景色和形状颜色跟着切换
- 形状库 `shape(name, cx, cy, size, rot, flip, stretch)`：`SHAPES` 有 circle / square / triangle / star / heart / drop / cloud / snowflake / mountain / river / wave / sun / moon / leaf / bird / fish / pin / house；`union([('circle', x, y, r), ('line', 点列, 宽), ('poly', 点列), ('sub', 图元)], cx, cy, size)` 用图元拼出自己的形状，自动描出外轮廓
- 几何：`resample(P, n)` 按弧长等距重采样；`normalise(P)` 顺时针、从正上方起；`align(A, B)` 统一绕向并用 FFT 找最佳起点；`chain([...])` 整串依次对齐；`ease(t, 'inout'|'sine'|'quad'|'in'|'out'|'back'|'expo'|'linear')`；`tween(A, B, s, at=, stretch=, direction=, spin=, scale=)` 轮廓绕质心插值、质心单独走运动路径，stretch 是沿运动方向的挤压拉伸；`at(keys, T)` 整串关键帧在全局时间 T 的轮廓（逐帧做真动画用）；`mix(c0, c1, t)` 在 OKLab 里混色（蓝到黄不发灰）
- 背景：`paper(颜色)`；`panel(x0, y0, x1, y1, 颜色, ink=)` 一块纯色面板，ink 是画在这块面板上的残影和线条默认用的颜色；`wipe(cx, cy, r, 颜色, ink, clip_box)` 定格的圆形转场
- 形状层：`fill(P, 颜色, alpha, clip=另一轮廓, half=((x0, y0), (x1, y1)))`，half 只填直线右侧，用来做两色折面；`outline(P, 颜色, width, dash=(实, 虚))`；`stroke(点列, 颜色, width)` 圆头线（高光、水纹、热气）；`dot()`
- 定格动画：`ghost(P, fill, fill_alpha, line_alpha, width)` 洋葱皮残影，线色为 None 时取下面面板的 ink，跨面板自动换色；`points(P, every)` 标出对应点；`links(A, B, every)` 对应点连线；`path(点列)` 过质心的平滑路径，`along(路径, u)` 取点和方向；`trail(路径, dash=)` 运动轨迹；`chevron()` 方向箭头；`streaks()` 速度线
- 时间轴：`diamond(x, y, r, fill)` 关键帧菱形；`ease_curve(x0, y0, x1, y1, kind, ticks=帧时间)` 一段缓动曲线，带帧点和虚线投影
- 文字 `text(s, x, y, size, 颜色, font='sans'|'display'|'mono'|'mono_bold'|'cjk'|'cjk_bold', anchor='l'|'m'|'r', spacing, alpha)`：y 是基线，中西文自动换字体，返回宽度；`text_width()` 量宽度
- 坐标都是像素、y 向下；角度逆时针为正

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 起点、绕向没对齐，中间帧塌成一条条碎片 | 先 `normalise`（同样点数、顺时针、从正上方起），再 `align`（FFT 互相关找最佳起点）；一串关键帧用 `chain` 依次对齐 |
| 每段 5 个残影、关键帧又太大，雪花和云的花边残影叠成一片噪点 | 关键帧约占面板宽的六成；每段只画 3 个残影，中间那帧填色约 0.42，两侧只留细线和约 0.14 的淡填色 |
| 运动轨迹画成圆点，和中间帧上的对应点混在一起，看着像轨迹绕了个圈 | 轨迹用虚线（`trail(dash=)`），圆点只用来标对应点，图例里分开写 |
| 速度线等长等距，像梯子，落在河边还被当成水流线 | 海报里不画速度线，靠挤压拉伸和残影间距表现速度 |
| 纸纹把奶白色的云也盖成了砂纸 | 形状保持纯平：纸纹只加在露出的纸面上（`tooth` 遮罩），面板和形状只有极轻的印刷颗粒 |
| 闭合样条在直角处过冲，海浪底角鼓出一个包；太阳的细光芒是断开的小棍 | 只对曲线部分做样条，底边用直线接；光芒用楔形加圆头，和圆盘连成一体再描外轮廓 |
| 后一段的残影线压在前一个关键帧上；标签重复画了两遍，颜色变深 | 画完残影后重画前一个关键帧（只重画形状内的细节）；文字和形状外的点缀只画一次 |
| 「↺」在所用中文黑体里没有字形，显示成方框 | 循环箭头用 `outline` 画圆弧再加 `chevron`，方向取圆弧终点的切线 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
