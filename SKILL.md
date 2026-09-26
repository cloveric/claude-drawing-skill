---
name: claude绘图
description: Claude 绘图 / Claude Drawing —— 不借助任何生图模型，由 Claude 用代码一笔一笔「画」出图片（程序化绘画）。当前内置并验证过的画风是中国水墨：宣纸纹理、层层远山与雾气、飞白笔触、皴擦、苔点、松、芦苇、孤舟、烘云托月、朱红日、题字与印章。用户说「claude绘图」「用代码画」「你自己画」「不用生图模型画」「程序化绘画」「代码水墨」，或 "draw it yourself", "paint with code", "procedural painting", "ink wash painting without an image model" 时使用；也用于需要可逐步画出（draw-on）动画的插画。几秒出一张 1920×1080。
---

# Claude 绘图

用 Python（只依赖 numpy + Pillow，系统自带的 `python3` 就能跑）按笔画和墨色的物理规律「画」图，不调用任何生图模型。
- **画面**：每一笔都是算出来的，可以精确控制构图、留白、朱红点缀的位置。
- **结果可复现**：固定随机种子后，同一段代码每次画出同一幅画。
- **适合做动画**：可以按「先远山、再主峰、再小路……」的顺序出分阶段快照，做成逐步画出的动画；生图模型只能给一整张画。

`examples/bawansiqian.jpg`（八万四千法门）和 `examples/moon_river.jpg`（月印万川）是水墨风的质量基准。

## 一、流程（每幅画都照做）

1. **定构图**，动笔前先想清楚这几项：
   - 层次：远景 → 中景 → 主体 → 前景；
   - 视觉焦点在哪里；
   - 留白至少四成；
   - 朱红只点一处或两处（日、印章、一条关键的路）；
   - 题字位置（竖排，放在留白处）。
   - 画面必须图解内容本身。比如「八万四千法门」就画很多条路汇向同一个山顶，而不是随便一幅山水。
2. **写场景脚本**：复制 `examples/bawansiqian.py` 改写，用 `lib/inkpaint.py` 的接口组合。
3. **渲染并自己看图**：`python3 scene.py out.png`，大约 3–5 秒。
   - 用 Read 打开 PNG，**对照第三节的毛病清单逐条自查**；
   - 通常要改 2–4 轮，每轮只改最显眼的问题，把前一版存成 `_v1/_v2` 以便对比。
4. **交付**：转成 JPG（quality 92，约 400KB），用当前对话渠道支持的方式发图。
   - 需要动画时加 `--stages DIR`，按 `p.stage('名字')` 输出每个阶段的快照。

## 二、接口速查（`lib/inkpaint.py`）

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from inkpaint import Painting, spline, curve, fbm1d, blur
p = Painting(1920, 1080, seed=7)       # 固定种子 = 可复现
p.paper()                                # 宣纸：底色斑驳 + 颗粒 + 纤维
ridge = p.ridge(base_y, peaks=[(x, 高, 宽), ...], rough=26)          # 山脊线 y(x)
main = p.peak(SX, SY, height=560, left_w=360, right_w=470, shoulders=[(x, h, w)])  # 主峰（不对称，带山肩）
p.wash(ridge, dens, decay, tex, edge, mist_y, mist_h)   # 墨染山体：上浓下淡、有水痕边、会遮挡后面的层
p.cun(main, x0, x1, n=150, shadow_x=SX)   # 皴擦：阴面多而深
p.moss(main, x0, x1, n=70)                # 苔点
p.ridge_line(main, x0, x1)                # 淡而断续的山脊线
paths = p.trails(main, (SX, SY), n=16, red_index=7)   # 蜿蜒小路汇向山顶，其中一条朱红
p.mist(y, h, strength)                    # 雾带：盖住它之前画的东西
p.rock(ridge); p.pine(root, top, bend, branches=[(起点, 终点, 弯度)], extra_tufts=[...])
p.sun(x, y, r); p.birds([(x, y, s)]); p.pagoda(x, y); p.traveller(x, y); p.dot(x, y, r)
p.stroke(points, width, ink, dry=0.35, taper=(0.25, 0.35), red=False)  # 通用毛笔：飞白、按压粗细、抖动
p.title_vertical('八万四千', x, y, 92); p.seal('法门', x, y, 40)       # 楷体题字 + 朱印（最后叠加）
p.stage('远山')                           # 动画用阶段快照
p.save('out.png', stages_dir=None)
```

**顺序很重要**：先远后近（`wash` 会遮挡前面已画的层），雾要画在它该吞没的东西之后，题字和印章最后叠加。

## 三、毛病清单（都真实出现过，自查时逐条过）

| 看到的问题 | 原因 | 改法 |
|---|---|---|
| 后面的远山线条透过前面的主峰 | 层与层直接叠加，没有遮挡 | `wash(occlude=True)`（默认），并且先远后近 |
| 笔画像梯子或一串珠子 | 笔毛太细、落笔点间距太大 | 库里已经按笔毛大小自动算间距；自己写笔刷时也要这样 |
| 小路像头发丝、像根须 | 线太多、太弯、跑出山体 | 16 条左右，用样条平滑，起点在山脚雾里，只画在山体上 |
| 路是折线，像裂缝或图表 | 用直线段连接转折点 | 一律用 `spline()` 连接控制点 |
| 皴擦像撒了一片逗号 | 短笔太多、太匀、方向乱 | 减到约 150 笔，加长，顺着坡向，集中在阴面 |
| 山像卡通描边 | 山脊线太重太连续 | 山脊线用淡墨（0.3）加飞白，主要靠墨染的水痕边和苔点 |
| 松针像海胆 | 放射状的针太黑太满 | 扇形松针（上半圈）加底下一团淡墨晕 |
| 主峰像规整的锥子 | 左右对称、没有起伏 | 左右坡宽度不同，加山肩，加分形起伏 |
| 画面发闷 | 留白不够、朱红太多 | 留白至少四成，朱红最多一两处 |

## 四、做成动画

- **简单做法**：用 `p.stage()` 分阶段快照（远山 → 主峰 → 小路 → 松石 → 日与题字），在视频里依次淡入叠化，看起来就是一幅画被逐步画出来。
- **更细的做法**：把某一组笔画单独画到透明层上导出，在 Motion Canvas 里用遮罩按笔画顺序显现。这需要给笔画分组，还没做成现成接口，用到时再加。

## 五、扩展到别的画风

笔刷、纸纹、墨染这套底层可以改造成水彩（彩色墨染 + 水痕边 + 颗粒）或剪纸拼贴（撕纸毛边 = 噪声扰动多边形边缘 + 纸纹）。

**目前只有水墨风做过并经用户认可**，别的画风第一次做时先出一张给用户看。

## 六、文件

```
lib/inkpaint.py                     绘图库（Painting 类 + 辅助函数，只依赖 numpy + Pillow）
examples/bawansiqian.py             范例「八万四千法门」：层层远山、主峰、小路汇顶、松石、朱日（约 3.6 秒）
examples/moon_river.py              范例「月印万川」：烘云托月、孤舟垂钓、芦苇、水面月影（约 2 秒）
examples/*.jpg / drawing_*.gif      成品与逐步画出的动图
中文字体：自动找 Kaiti/Songti（macOS）、Noto CJK（Linux）、KaiTi/SimSun（Windows），或设 INKPAINT_FONT
```
