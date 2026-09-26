---
name: claude绘图
description: Claude 绘图 / Claude Drawing —— 不借助任何生图模型，由 Claude 用代码一笔一笔「画」出图片（程序化绘画）。内置三种画风：中国水墨（宣纸、层层远山与雾、飞白、皴擦、苔点、松、孤舟、烘云托月、题字印章）、水彩（湿画渐变、透明罩染、水痕边、颜料颗粒、水渍花、提白）、剪纸拼贴（撕纸白边、纸片阴影、彩纸/牛皮纸/报纸/笔记本纸、蜡笔、腮红圆脸的可爱小人）。用户说「claude绘图」「用代码画」「你自己画」「不用生图模型画」「程序化绘画」「代码水墨/水彩/剪纸」，或 "draw it yourself", "paint with code", "procedural painting", "ink wash / watercolor / paper collage without an image model" 时使用；也用于需要逐步画出（draw-on）动画的插画。
---

# Claude 绘图

用 Python（只依赖 numpy + Pillow，系统自带的 `python3` 就能跑）按笔、墨、颜料、纸的物理规律「画」图，不调用任何生图模型。
- **构图可控**：每一笔都是算出来的，构图、留白、点睛色的位置都精确可控。
- **结果可复现**：固定随机种子，每次画出同一幅画。
- **适合做动画**：可以输出分阶段快照，做成「一幅画被逐步画出来」的动画；生图模型只能给一整张画。

## 画风与范例（质量基准）

| 画风 | 库 | 范例 | 耗时 |
|---|---|---|---|
| 水墨 | `lib/inkpaint.py` · `Painting` | `examples/bawansiqian.py` 八万四千法门、`examples/moon_river.py` 月印万川 | 2–4 秒 |
| 水彩 | `lib/watercolor.py` · `Watercolor` | `examples/watercolor_lotus.py` 一花一世界（清晨荷塘） | 约 17 秒 |
| 剪纸拼贴 | `lib/papercut.py` · `Collage` | `examples/papercut_moon.py` 小沙弥看月亮 | 约 20 秒 |

三种画风共用 `lib/core.py` 里的底层工具：噪声、模糊、样条曲线、多边形遮罩、有机轮廓 `blob_pts`、毛笔 `bristle_stroke`、中文字体查找。

**用户没有指定画风时怎么选**：禅意、古典、山水题材用水墨；清新、花卉、风景、带颜色的题材用水彩；童趣、温暖、故事感、角色类题材用剪纸拼贴。

## 一、流程（每幅画都照做）

1. **定构图**，动笔前先想清楚这几项：
   - 层次：远 → 中 → 主体 → 前景；
   - 视觉焦点在哪里；
   - 留白够不够：水墨至少四成，水彩和剪纸也要有呼吸感；
   - 点睛色只用一两处：水墨用朱红，剪纸用一个亮色主角；
   - 题字或纸条放在哪里。
   - **画面要图解内容本身**，而不是随便一幅风景。
2. **写场景脚本**：复制最接近的范例改写。
3. **渲染并自己看图**：`python3 scene.py out.png`。
   - 用 Read 打开 PNG，对照第三节该画风的毛病清单逐条自查；
   - 一般改 2–4 轮，每轮只改最显眼的问题，旧版存成 `_v1/_v2` 以便对比。
4. **交付**：转成 JPG（quality 92），用当前对话渠道支持的方式发图。
   - 要做动画时加 `--stages DIR`，按 `stage('名字')` 输出各阶段快照。

## 二、接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask
```

**水墨 `Painting`**：
- `paper()`、`ridge(base, peaks=[(x,h,w)])`、`peak(SX, SY, shoulders=...)`
- `wash(ridge, dens, decay, tex, edge, mist_y)`：墨染山体，上浓下淡、带水痕边，会遮挡后面的层
- `cun()` 皴擦、`moss()` 苔点、`ridge_line()` 淡山脊线、`trails(ridge, summit, red_index)` 汇顶小路、`mist(y, h)` 雾带
- 毛笔 `stroke(pts, width, ink, dry, taper, red)`
- 物件：`pine()`、`rock()`、`sun()`、`birds()`、`pagoda()`、`traveller()`、`dot()`
- 题字印章：`title_vertical()`、`seal()`

**水彩 `Watercolor`**：
- `paper()`：冷压水彩纸纹理
- 遮罩：`shape(pts, soft, ragged)`，soft 取 1–4 是清晰的水痕边，15–40 是湿画晕开；`band(pts, width)` 是粗笔带状遮罩
- `glaze(mask, 颜色, strength, edge, gran, bloom, variation)`：透明罩染，叠加会像真颜料一样变深、混色
- `gradient_wash(y0, y1, top, bottom)`：湿画渐变天空
- 笔触：`stroke()` 彩色干笔、`line()` 细线勾勒、`lift(mask)` 提白、`splatter()` 甩点
- `Watercolor.petal_pts(x, y, 角度, 长, 宽)`：花瓣或叶片轮廓；`hexc('#rrggbb')` 转颜色

**剪纸 `Collage`**：
- `background(颜色, texture)`
- `piece(pts 或 mask, 颜色, texture, torn, rim, shadow)`：贴一张纸。torn 是撕边程度，rim 是撕口白边，shadow 是纸片阴影；texture 可选 paper / kraft / crayon / newsprint / notebook
- 形状遮罩：`circle_mask()`、`cloud_mask()`、`Collage.star_pts()`
- 蜡笔和光：`crayon(pts, width, 颜色)` 蜡笔线、`dot()`、`glow()`
- `face(cx, cy, r, mood='smile'|'sleep'|'dots')`：笑眼、嘴、腮红
- `text(s, x, y, size, 颜色, vertical)`

**顺序**：都是先远后近、先大后小，文字最后叠加。水墨的雾要画在它该吞没的东西之后；水彩的叶梗要先画，并且只画在叶子外面。

## 三、毛病清单（都真实出现过）

**水墨**

| 问题 | 改法 |
|---|---|
| 后面的远山透过主峰 | 先远后近，`wash` 默认会遮挡身后 |
| 笔画像梯子或串珠 | 落笔间距跟笔毛挂钩（`bristle_stroke` 已处理） |
| 小路像头发丝，或是折线像裂缝 | 16 条左右，用 `spline` 平滑，只画在山体上，从雾里伸出来 |
| 皴擦像撒逗号 | 约 150 笔，长而顺坡，集中在阴面 |
| 山脊像卡通描边 | 山脊线用淡墨（0.3）加飞白，边缘靠水痕 |
| 松针像海胆 | 扇形松针，下面垫一团淡墨晕 |
| 主峰像锥子 | 左右坡宽度不同，加山肩和起伏 |
| 远山被挖出方块、断边生硬 | 用「从水线以下升起的山包」来留出水面，不要直接挖空一段 |

**水彩**

| 问题 | 改法 |
|---|---|
| 纸纹像砂纸或拉毛墙 | 纸纹受光强度约 0.3，纸纹要细 |
| 叶子中间一圈深色像靶心 | 第二层深色用湿画（soft 约 16）偏向一侧积色，不要同心 |
| 叶梗画到了叶面上 | 先画梗，用 `*(1 - 叶遮罩)` 限制只在叶外 |
| 颜色发脏 | 同一处罩染不超过三层；亮部留白或用 `lift` 提白 |

**剪纸拼贴**

| 问题 | 改法 |
|---|---|
| 大面积蜡笔纹像满屏刮痕 | 大色块用 paper / kraft，蜡笔只用在点缀或小物件上 |
| 撕纸白边看不见 | 白边要宽出 5–8 像素（大半径模糊加低阈值），并且只出现在部分边缘上 |
| 画面顶边或左边多出一条阴影 | 阴影偏移不能用会首尾相接的循环平移，要用补零平移（已修） |
| 月亮画了光芒，像太阳 | 月亮用蜡笔光圈加几颗闪光，不要放射线 |
| 脸的五官太粗太凶 | 线宽约 r×0.035，腮红用 `glow` |

## 四、做成动画

- 各画风都有 `stage(name)` 和 `save(path, stages_dir)`，按阶段依次淡入叠化，就是「一幅画被逐步画出来」。README 里的四张动图就是这样做的。
- 更细的逐笔动画：把一组笔画单独画到透明层上导出，再用 Motion Canvas 遮罩按顺序显现。这个还没做成现成接口。

## 五、文件

```
lib/core.py            公共底层（噪声、模糊、样条、遮罩、毛笔、字体）
lib/inkpaint.py        水墨
lib/watercolor.py      水彩
lib/papercut.py        剪纸拼贴
examples/*.py          范例脚本；*.jpg 成品；drawing_*.gif 逐步画出的动图
中文字体：自动找 Kaiti/Songti（macOS）、Noto CJK（Linux）、KaiTi/SimSun（Windows），或设 INKPAINT_FONT
```
