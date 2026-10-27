# 黑板板书（chalk）

- **实现**：`lib/chalk.py` · `Chalkboard`
- **范例**：`examples/chalk_lesson.py` 为什么天空是蓝的（墨绿石板、半擦掉的上节课残影与板擦痕、越往下越厚的粉笔灰；白黄粉蓝粉笔写的标题、太阳→大气层→眼睛示意图、长短波浪线、手写 ∝ 与圈出的 1/λ⁴、光谱条与散射曲线、带缺口的「小结」框；木框和粉笔槽里的粉笔、板擦）
- **耗时**：约 5 秒

## 何时选用

讲课、知识点、公式推导、原理示意图、讲解片里的「板书 / 课堂」页 → 黑板板书；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from chalk import Chalkboard
```

- 分层：石板漆 → 粉笔层（预乘颜色 + 透明度，板擦能擦掉）→ 板前物件（木框、粉笔槽、粉笔、板擦及其投影）→ 室内光与暗角
- 板面：`slate()` 云状不匀的墨绿石板漆；`dust(amount, specks, haze)` 沉降的粉笔灰，越往下越厚；`frame(rail, top, ledge)` 斜接木框加粉笔槽，会设置写字区 `area` 和槽面高度 `tray_y`。默认尺寸构造时就已知，dust 和擦痕可以先于画框画
- 板擦：`swipe(pts, width, strength, haze, smear, keep)` 沿路径擦一遍：带走粉笔、顺擦向拖出残迹、毡面梳出细纹、毡面两端积灰；`smudge(cx, cy, w, h, rot)` 短擦一下；`with cb.erased(keep, angle, smear):` 块里画的一切都变成擦过没洗的旧课残影
- 笔尖：`stroke(pts, colour, width, pressure, jitter)` / `strokes([...])`；`line()` 徒手直线、`rule()` 靠尺直线；`box(x0, y0, x1, y1, gap=(xa, xb))` 四边出头，上边可留缺口写标签；`loop(cx, cy, rx, ry, rot, turns)` 不闭合的圈、`circle()`；`arrow(pts, head)` 两笔箭头在尖端叠厚；`underline(x0, x1, y, double)`；`wave(p0, p1, wavelength, amplitude)` 光波曲线带箭头；`dashed()` 一段段画的虚线；`dot()`；`hatch(mask, angle, spacing)` 排线；`propto(x, y, size)` 手写 ∝，返回宽度
- 侧锋：`side(p0, p1, stick, pressure)` 粉笔横躺拖一笔；`shade(mask, colour, angle, stick, pressure, overlap, weight)` 侧锋铺色，weight 是全画布 0–1 的压力图，可做渐变
- 粉笔只挂在板面「齿」的凸起上：pressure 0.2–0.4 颗粒稀疏（铺色），0.8–0.95 写字画线
- 文字 `text(s, x, y, size, colour, font, anchor, pressure, weight, rot, spacing, hand, grain)`：font 用 sans / sans_bold / cjk_sans，某套字体缺字自动换另一套；每个字各自微转、错位、轻重不一（hand=0 为排版体）；`text_width()` 量宽度
- 道具：`chalk_stick(x, cb.tray_y, length, colour, rot, worn='right'|'left'|None)` 粉笔，一端磨斜；`eraser(x, cb.tray_y + 2)` 板擦；`crumbs(x0, x1, n)` 碎粉笔
- 颜色：`WHITE YELLOW PINK BLUE` 为主，`RED ORANGE GREEN VIOLET` 用于光谱和彩色粉笔，另有 `DUST`；所有 angle 和 rot 都是逆时针为正

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 粉笔线像干净的矢量线：满压几乎实心、边缘光滑 | 满压也要留约 15% 的坑点（阈值 0.98 − 0.86 × 压力）；笔尖接触面按线宽的 0.26 倍模糊，边缘才会毛、才会断 |
| 中文（黑体）比 Helvetica Bold 细一截；加粗后 30 px 的复杂字糊成一团 | 中文按字号加粗，小字加粗减弱；40 px 以下自动加压、减轻颗粒和边缘扭曲（已处理） |
| 字体的粗体 ∝ 被粉笔加粗后闭合，看着像 ∞ | 用 `propto()` 手写一笔：双纽线的左瓣加两条向右的尾巴 |
| 大气层用侧锋铺色，成了一整块发闷的矩形，压住上面的波浪和标注 | 压力约 0.3、strength 约 0.6，用 `weight` 做渐变（近地面浓、往上淡），左右两端长距离渐隐 |
| 上节课的残影被后来的大擦痕又擦没了，或者压在新板书下面影响阅读 | 残影 keep 取 0.26–0.34，大擦痕 strength 不超过 0.6；残影放在空白处（上沿、角落、标题和图之间） |
| 动图调色板只取最后一帧，满屏绿色吃掉色位，粉彩粉笔、光谱条发灰 | 调色板用加权像素样本做中值切分（彩色像素 ×5、亮色 ×2），所有帧仍共用这一张 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
