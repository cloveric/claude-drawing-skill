# VHS 家庭录像（vhs）

- **实现**：`lib/vhs.py` · `VHSCamcorder`
- **范例**：`examples/vhs_birthday.py` 吹蜡烛 · Blow Out the Candles（一家人生日录像里的一帧：70 年代客厅的圆环墙纸、胡桃木护墙板、兔耳天线电视、牛油果绿丝绒沙发、长毛地毯；彩带、HAPPY BIRTHDAY 三角小旗、戴派对帽的泰迪熊；茶几上的蛋糕四根蜡烛刚吹灭冒着烟、两根还亮着，过生日的孩子戴着尖帽从背后凑近、离镜头太近而虚焦；白平衡停在「室外」拍钨丝灯、烛焰过曝和 CCD 竖向拖影、点阵 OSD；录像带的色度渗色、跟踪噪带、磁头切换噪声、掉磁白点）
- **耗时**：约 6 秒
- **内部构成**：VHS 家庭录像（70 年代客厅：反照率 × 灯光 + 自发光、离焦图层；家用摄像机：手持倾斜、钨丝灯偏色、软膝、泛光、CCD 竖向拖影、拖尾、增益噪声、点阵 OSD；录像带：YIQ、亮度带宽与锐化光晕、色度带宽 / 隔行平均 / 延迟、噪声、时基抖动、跟踪噪带、磁头切换、掉磁）

## 何时选用

家庭回忆、怀旧、「当年的那一天」（生日、过年、毕业、第一次……）、童年和老房子、found footage 式的悬念开场、讲解片里的「回到 80 年代 / 那时候的家 / 老录像里的证据」页 → VHS 家庭录像（要霓虹落日的 80 年代复古未来用复古 Synthwave；要老照片和剪报用报刊拼贴；要屏幕上的字符用 ASCII 字符画）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from vhs import VHSCamcorder
```

- 思路：不是在画面上盖一层「复古滤镜」（Synthwave 的录像带质感就是这么做的），而是照家庭录像真实的三步出图，每种瑕疵都来自其中一步：
  1. 房间：颜色画进反照率缓冲，灯罩、烛焰、窗外天空画进自发光缓冲；出图时反照率乘上房间的光（暖色环境光 + 点光源 + 画上去的光斑）再加自发光；镜头前太近的东西画在离焦图层上
  2. 摄像机：手持微倾和变焦、白平衡停在「室外」拍钨丝灯、软膝高光、泛光、CCD 竖向拖影、拖尾、镜头柔化、暗角、暗处增益噪声；摄像机的字符发生器在这里把 OSD 混进信号，所以 OSD 也跟着上带、跟着糊
  3. 录像带：降到 480 行 × 760 采样点，分成亮度 Y 和色度 I/Q；亮度低通再加回放锐化（一边亮一边暗的光晕），色度约 6 倍宽的低通、隔行平均、往右延迟（红色往右渗）；回放再加条状亮度噪声、横向色度噪声、逐行时基抖动、顶部偏摆、跟踪噪带、磁头切换噪声、掉磁白点、抬高的黑电平，最后放大回输出尺寸
- 构造：`VHSCamcorder(W, H, seed, lines=480, samples=760, ss=2, keep_stages=True)`；`keep_stages=False` 时 `stage()` 不出快照（快）
- 形状 → 遮罩：`poly(pts)`、`shape(pts)` 闭合样条、`rect(x0, y0, x1, y1, r)`、`ellipse(cx, cy, rx, ry, rot)`、`line(pts, width)`、`text(s, x, y, size, style, anchor, rot)`；颜色场 `lin(p0, c0, p1, c1)`、`rad(cx, cy, rx, ry, c0, c1)`
- 上色与光：
  - `paint(mask, colour, alpha, form, form_r, light)`：colour 可以是颜色场；form > 0 把形状打圆（边缘暗、迎光一侧亮）
  - `emit(mask, colour, level)` 自发光（不受房间光影响）；`glow(mask, colour, level)` 落在表面上的光斑（乘反照率）；`shadow(mask, strength, soft, dx, dy)`；`rim(mask, toward, colour, level, width)` 朝光源一侧的轮廓光
  - `ambient(colour, level)`、`light(x, y, radius, colour, power)` 点光源，1 / (1 + (d/r)²) 衰减
  - `with v.layer(defocus=4.5): ...` 里画的东西整体虚焦（离镜头太近的前景）
- 70 年代客厅：`wallpaper(mask, tile, contrast)` 圆环墙纸带纸幅接缝、`paneling(mask, grooves)` 胡桃木护墙板、`ceiling()` 喷涂天花板、`shag()` 长毛地毯、`window(x0, y0, x1, y1)` 黄昏的窗（剪影、对面一扇亮窗）、`rod()` + `curtain(x0, x1, y0, y1, folds)` 花朵窗帘、`console_tv()` 落地电视柜、`rabbit_ears()`、`floor_lamp(x, y_floor, y_shade)`（自带灯光和墙上的光斑）、`sofa(x0, x1, y_back, y_seat, y_front, y_floor, colour)`
- 派对：`streamer(p0, p1, sag, colour, twists)` 扭转的皱纹纸彩带、`pennants(p0, p1, sag, letters, colours, size)` 字母三角旗（浅色旗自动换深色字）、`balloon(x, y, r, colour, string_to)`、`coffee_table(quad, thick, legs, gloss)`、`cake(cx, cy, rx, ry, h, candles, sprinkles, lean)`（candles = [(角度, 颜色, 'lit' 或 0–1 烟量)]，返回火苗位置，每个放一盏 `light`）、`smoke()`、`present()`、`cup()`、`plates()`、`blower()`、`confetti()`、`teddy()`；`child_back(hx, hy, s, lean, glow_from)` 背影的孩子（尖帽、发旋、耳朵、肘），画在离焦图层里
- 三步开关（调用之后的每个阶段都生效）：
  - `camera(tilt, zoom, white_balance, exposure, knee, bloom, smear, lag, soft, vignette, gain_noise)`：white_balance 是 RGB 增益，默认 (1.08, 0.94, 0.70) 即「室外档拍钨丝灯」；smear 只对远超满阱的点光源起作用；lag = (dx, dy, 强度) 是高光身后的拖尾
  - `record(luma, chroma, chroma_v, delay, sharpen, sharp_r, saturation)`：亮度 / 色度带宽（采样点 σ）、色度延迟、锐化光晕
  - `wear(noise, chroma_noise, jitter, flagging, tracking=(中心比例, 高度比例), head_switch, dropouts, black, lines)`
- OSD（点阵字、黑边，混进信号上带）：`rec(x, y)` 红点 + REC、`battery(x, y, level, of)`、`counter(s, x, y)`、`datestamp(时间, 日期, x, y)`、`zoom_bar(x, y, pos, width)`、`osd_text(s, x, y, px, colour, anchor)`；字库只有大写字母、数字和 `: . - / >`
- `stage(name)` 存一张当前状态的完整渲染；`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 落地灯那一列从画面顶到底一整条白，墙面也被冲白 | CCD 竖向拖影改成按列累加「远超满阱」的溢出（阈值 2.2，只有烛焰这种点光源够得上），不再取每列最大值；灯罩墙上的光晕从 0.9 / 0.45 降到 0.38 / 0.2；泛光阈值 0.85 → 1.0、拖尾阈值 0.95 → 1.2 |
| 被烛光照亮的白奶油也越过阈值，拉出一根宽宽的橙色光柱 | 烛光 0.42 → 0.3、半径 300 → 280；拖影只认 2.2 以上的溢出 |
| 灯罩是一块灰白的平方块，被小彩旗压住，看不出是灯 | 灯罩下移 60 px，避开彩旗；自发光带左右明暗，上下加黄铜边、顶上加灯头和顶珠，外面再加一圈暖色辉光 |
| 前景孩子的上身是一块和墙纸同色的芥末黄长方块 | 换青绿色 ringer T 恤，和满屋的橙撞开；轮廓重画：头大、肩斜，上臂单独画到手肘，前臂伸向桌子，肘和身子之间露出背景；加肩胛骨暗线、发旋放射的发丝、两只耳朵、朝蛋糕一侧的暖色轮廓光 |
| 派对帽太小，蓝白条纹被墙纸吃掉 | 帽子放大到头半径的 1.75 倍，红黄螺旋条纹，朝蛋糕歪 24°，顶上一团锡箔绒球，帽子在头上投一点影 |
| 刚吹灭的蜡烛冒出的烟像几根发光的白棍，过了录像带像又多出几根火苗 | 烟改成灰色、不发光：从细到粗、越往上越淡、带卷曲的一缕；另外「烟量 1.0」和「点着」用的是同一个数，蜡烛状态改成 `'lit'` / 0–1 烟量 |
| OSD 的 0 看成 8，W 看成 U / H，PM 看成 PN | 字符发生器把每个点向右加粗，1 点宽的缝会被填死：0 去掉斜线，W、M 改成 7 点宽 |
| 变焦条的刻度和细边框在录像带上糊成一团 | 用和字体同一套点阵画：外框 + 实心填充 + 一根游标，不画刻度 |
| 泰迪熊坐在锈红沙发上，同色看不见 | 沙发改牛油果绿丝绒，熊改蜂蜜色 |
| 圆环墙纸对比太强，满墙抢戏 | `contrast=0.72` 把图案色往底色收；加纸幅接缝和几像素的错位，看着是贴上去的墙纸 |
| 电视屏幕中间一团橙色反光，像屏幕上破了个洞 | 改成窗户在屏幕左上角的一块冷色反光 |
| 黄色小旗上的白字看不见 | 按旗色亮度自动换字色：浅色旗用深棕字 |
| 掉磁白点一样长，满屏像下雨 | 数量 45 → 24，长度按指数分布：多数是一两个采样点，偶尔一长条 |
| 不存阶段快照时 `stage()` 也做一遍完整合成，出图 13 秒；峰值内存 1.15 GB | `keep_stages=False` 时 `stage()` 什么都不做（范例按有没有 `--stages` 设）；泛光的两个大半径在 1/4 分辨率上做；大彩色图的模糊逐通道做：6 秒、0.85 GB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
