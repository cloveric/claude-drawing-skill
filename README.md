# Claude Drawing · Claude 绘图

**Claude paints with code — no image model.**
**不用生图模型，Claude 用代码一笔一笔作画。**

[English](#english) · [中文](#中文)

<p align="center">
  <img src="examples/drawing_bawansiqian.gif" width="720" alt="The painting being drawn stage by stage">
</p>

| 八万四千法门 · *Many paths, one summit* | 月印万川 · *One moon in ten thousand rivers* |
|---|---|
| ![bawansiqian](examples/bawansiqian.jpg) | ![moon_river](examples/moon_river.jpg) |

Every mark above is computed: the rice-paper fibres, the layered mist mountains, the dry-brush strokes, the moss dots, the pine, the reeds and the vermilion sun. No diffusion model, no API, no stock art. Each 1920×1080 painting renders in **about 2–4 seconds on a CPU** from a few dozen lines of Python.

---

## English

### What it is

A [Claude Code](https://claude.com/claude-code) skill plus a small painting library, `lib/inkpaint.py`, which needs only **numpy + Pillow**. Ask Claude to *"draw it yourself"*, *"paint this with code"* or *"claude绘图"*. Claude then does the following:

1. Plans a composition: far → near layers, a focal point, generous empty space, and one vermilion accent.
2. Writes a short scene script using the library.
3. Renders it, **looks at the result**, and fixes what is wrong using a built-in pitfall checklist, usually over 2–4 rounds.

The first built-in style is **Chinese ink wash (水墨)**.

### Why paint with code instead of an image model?

- **Composition you can direct**: placement, empty space and colour accents are exact, not sampled.
- **Reproducible**: the same seed gives the same painting.
- **Animatable**: `stage()` snapshots let a video show the painting *being painted* (distant hills → peak → paths → pine → sun), which a single generated bitmap can't do. See the GIFs.
- **Runs anywhere**: offline, on a CPU, with no GPU, API key or quota.

### Install

```bash
git clone https://github.com/cloveric/claude-drawing-skill.git ~/.claude/skills/claude-drawing
pip install -r ~/.claude/skills/claude-drawing/requirements.txt   # numpy, Pillow
```

Titles and seals need a CJK font. macOS Kaiti/Songti, Linux Noto CJK and Windows KaiTi/SimSun are found automatically. You can also set `INKPAINT_FONT=/path/to/font.ttf`.

### Quick start

```python
import sys; sys.path.insert(0, "lib")
from inkpaint import Painting

p = Painting(1920, 1080, seed=7)
p.paper()                                                   # rice paper
far = p.ridge(560, peaks=[(420, 150, 330), (1650, 110, 260)])
p.wash(far, dens=0.16, decay=170, mist_y=700)              # pale distant range
main = p.peak(1130, 252, shoulders=[(1380, 70, 90)])
p.wash(main, dens=0.46, decay=240, mist_y=920)              # the main peak (occludes what's behind)
p.cun(main, 530, 1730, shadow_x=1130)                       # dry texture strokes on the shadow side
p.trails(main, (1130, 252), n=16, red_index=7)              # winding paths to one summit
p.mist(960, 70, 0.8)
p.sun(1500, 190, 46)
p.save("out.png")
```

Or run the examples:

```bash
python3 examples/bawansiqian.py out.png --stages stages/    # also writes the draw-on stage snapshots
python3 examples/moon_river.py  moon.png
```

### Toolkit

| Call | What it paints |
|---|---|
| `paper()` | rice paper: mottled tone, grain, fibres |
| `ridge()`, `peak()` | ridgelines: soft ranges, or an asymmetric main peak with shoulders |
| `wash()` | an ink-wash mass under a ridge: dark edge fading down, texture, wet rim, mist, **occlusion** |
| `stroke()` | the core brush: bristles, pressure taper, flying-white (飞白) dry breaks, wobble; ink or vermilion |
| `cun()`, `moss()`, `ridge_line()` | texture strokes (皴), moss dots (苔点), a light broken ridge accent |
| `trails()`, `mist()` | switchback paths to a summit; mist bands that swallow what's beneath |
| `pine()`, `rock()`, `sun()`, `birds()`, `pagoda()`, `traveller()`, `dot()` | motifs |
| `title_vertical()`, `seal()` | vertical calligraphy title and a vermilion seal |
| `stage(name)`, `save(path, stages_dir)` | snapshots for draw-on animation, and the final output |

Under the hood, every mark adds density to an ink buffer using pigment-style compositing, `D = 1 − (1−D)(1−a)`. The final image is the paper multiplied by the ink. Brushes are stamped bristle by bristle, with dab spacing tied to bristle size, so strokes never look beaded.

### The pitfall checklist (what Claude checks before showing you)

Things that went wrong while building this, and how they are fixed:

- **Background ridges show through the peak** → paint far to near, and let each wash occlude what is behind it.
- **Strokes look like ladders or beads** → dab spacing is tied to bristle size.
- **Paths look like hair** → use fewer paths, smooth them with a Catmull-Rom spline, and keep them on the mountain so they emerge from the mist.
- **Texture strokes look like scattered commas** → use fewer, longer strokes that follow the slope, mostly on the shadow side.
- **The ridge reads as a cartoon outline** → keep the ridge line light and broken, and let the wash's wet rim carry the edge.
- **Pine needles look like sea urchins** → use fan-shaped tufts over a soft wash.
- **The image feels heavy** → keep at least 40% empty space and use vermilion only once or twice.

### Roadmap

- More styles on the same brush/paper/wash core: watercolour, and torn-paper collage.
- Per-stroke layer export, for stroke-by-stroke animation in Motion Canvas or Remotion.

---

## 中文

### 这是什么

一个 [Claude Code](https://claude.com/claude-code) skill，加上一个小巧的绘图库 `lib/inkpaint.py`，只依赖 numpy + Pillow。对 Claude 说「claude绘图」「你自己画」「用代码画」，它会：
1. **先定构图**：远中近层次、视觉焦点、大片留白、一处朱红点睛；
2. **写一段场景脚本**，调用绘图库；
3. **渲染并自己看图**，对照内置的毛病清单挑问题，一般改 2–4 轮。

目前内置并打磨过的画风是**中国水墨**。

### 为什么用代码画，而不用生图模型

- **构图可控**：位置、留白、朱红点在哪里都精确可控，不靠抽卡。
- **可复现**：同一个随机种子，画出同一幅画。
- **能做「作画过程」动画**：用 `stage()` 按「远山 → 主峰 → 小路 → 松石 → 朱日」存下每一步，视频里就能看到画被一步步画出来（见上面的动图）。生图模型只能给一整张画。
- **哪里都能跑**：离线、只用 CPU，不需要显卡、API Key 或额度；一张 1920×1080 只要 2–4 秒。

### 安装

```bash
git clone https://github.com/cloveric/claude-drawing-skill.git ~/.claude/skills/claude-drawing
pip install -r ~/.claude/skills/claude-drawing/requirements.txt   # numpy、Pillow
```

题字和印章需要中文字体。macOS 的楷体/宋体、Linux 的 Noto CJK、Windows 的楷体/宋体都会自动找到，也可以用 `INKPAINT_FONT=字体路径` 指定。

### 快速上手

见上方英文部分的代码示例，或直接运行两个范例：

```bash
python3 examples/bawansiqian.py out.png --stages stages/   # 八万四千法门，同时输出分阶段快照
python3 examples/moon_river.py  moon.png                   # 月印万川
```

### 工具箱

| 调用 | 画什么 |
|---|---|
| `paper()` | 宣纸：底色斑驳、颗粒、纤维 |
| `ridge()` / `peak()` | 山脊线：远山起伏，或不对称、带山肩的主峰 |
| `wash()` | 墨染山体：上浓下淡、纹理、水痕边、雾气，并**遮挡身后的层** |
| `stroke()` | 核心毛笔：分笔毛、提按粗细、飞白、抖动；可用墨色或朱红 |
| `cun()` / `moss()` / `ridge_line()` | 皴擦、苔点、淡而断续的山脊线 |
| `trails()` / `mist()` | 汇向山顶的蜿蜒小路；雾带（会吞没下方已画的东西） |
| `pine()` / `rock()` / `sun()` / `birds()` / `pagoda()` / `traveller()` / `dot()` | 松、石、日、飞鸟、小塔、行人、点 |
| `title_vertical()` / `seal()` | 竖排题字、朱红印章 |
| `stage(名字)` / `save(路径, stages_dir)` | 分阶段快照（做动画用）、输出成品 |

原理：每一笔都往「墨量」缓冲里叠加，叠加方式模拟颜料，`D = 1 − (1−D)(1−a)`，最后用宣纸底色乘上墨色得到画面。毛笔按一根根笔毛盖章式落墨，落笔间距跟笔毛粗细挂钩，所以笔画不会一节一节的。

### 毛病清单（Claude 交图前逐条自查）

- 后面的远山透过主峰 → 先远后近，每层墨染都遮挡身后的层
- 笔画像梯子、像串珠 → 落笔间距跟笔毛粗细挂钩
- 小路像头发丝 → 条数少一些，用样条曲线平滑，只画在山体上，从雾里伸出来
- 皴擦像撒了一片逗号 → 少而长，顺着坡向，集中在阴面
- 山脊像卡通描边 → 山脊线要淡而断续，边缘主要靠墨染的水痕
- 松针像海胆 → 扇形松针，下面垫一团淡墨
- 画面发闷 → 留白至少四成，朱红最多一两处

### 计划

- 在同一套笔刷、纸纹、墨染的底层上扩展更多画风：水彩、撕纸拼贴。
- 按笔画分层导出，方便在 Motion Canvas / Remotion 里做逐笔动画。

---

MIT License · Made by Claude (Opus 5.5) with [@cloveric](https://github.com/cloveric)
