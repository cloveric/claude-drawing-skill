# 描图纸叠层（overlay）

- **实现**：`lib/overlay.py` · `Overlay`
- **范例**：`examples/overlay_city_map.py` 海港步行图 · Larkhaven on Foot（暖白灯箱上，定位钉挂着一张黑线灰调的海边小城底图：递归切出的街区、沿街一圈房屋和分户墙、深色地标、海岸与防波堤、铁路、城堡山和岬角的等高线；三张单色叠片对着套准十字落下——蓝片（沿岸一圈圈水线、河、港湾、渡轮航线、2 路电车）、黄片（公园、集市广场、海滩）、品红片（六站步行路线，坐渡轮去灯塔）；不同叠片的油墨正片叠底：植物园的池塘叠成绿、路线压过公园成红、压过海面成紫；描图纸背光下的纤维云纹、卷角、打孔、绘图胶带，旁边一张透明胶片上的图例卡）
- **耗时**：约 7 秒
- **内部构成**：描图纸叠层（灯箱发光、黑线灰调底图与单色叠片、透过率相乘的油墨、背光纤维云纹、抬起时的漫射模糊与投影、卷角、打孔与定位钉、套准十字、绘图胶带、透明胶片）

## 何时选用

地图、路线与导览、城市 / 园区 / 校园平面图，「一层一层把信息加上去」的图解（底图 → 水系 → 绿地 → 路线），设计稿或方案的分层、叠加与对照，讲解片里「把几层信息叠起来看」的页 → 描图纸叠层（要正等轴的微缩模型用等轴 2.5D；要剖面、尺寸和施工说明用蓝图工程图；要三原色丝网海报用包豪斯几何）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from overlay import Overlay
```

- 思路：透光台上的分色叠片。灯箱从下面打暖白光，画面就是一路透过率相乘：底图（胶版纸）印黑线和灰调，上面每张描图纸 / 胶片只印一种油墨。油墨按网点覆盖率 c 算透过率（c ≤ 1 是平网 1 − c(1 − ink)，c > 1 是叠印加深 ink^(c−1)）；不同叠片之间正片叠底，蓝叠黄成绿、品红叠黄成红、蓝叠品红成紫；同一块版自己不叠加（取最大覆盖率）。每张纸有自己的纸色、只有背光下才看得见的云状纤维（formation）、零星纤维丝、裁切边的一道细暗线和打孔；描图纸平放时也让下面的暗部略微发灰（frost）。抬起的纸略放大、往右下投一片宽而软的暖色阴影（透过纸也看得见），而且它是离开画面的漫射片，会把下面的一切模糊掉；放下后清晰，阴影收成一条贴边细线，套准十字落在底图的十字上
- 构造：`Overlay(W, H, seed, keep_stages=True)`；`desk(colour)`、`lightbox(x0, y0, x1, y1, radius, bezel)`、`lamp(level)`（0 关灯：灰色乳白亚克力；1 开灯：暖白，中间偏左最亮；中间值又暗又偏暖）；`peg_bar(x0, x1, y0, y1, pegs=[('round', x, y, r), ('slot', x, y, w, h)])` 定位钉条（不透明的钢条，画在所有纸下面，纸上的孔里露出钉子和一圈透光缝）
- 纸：`sheet(x, y, w, h, kind='base'|'tracing'|'drafting'|'film', ink, tint, fibre, curl=('br', 70), edge)` 返回 `Sheet`。坐标一律是**纸放下时的画布坐标**，所以几张叠片用同一组点画，自动套准。`place(sheet, lift, dx, dy, rot)` 显示、抬起（lift 0–1，偏 dx / dy 像素、转 rot 度）或放下（全 0）；第一次 `place` 决定叠放顺序；`remove(sheet)`；`tape(cx, cy, w, h, rot)` 撕口的皱纹绘图胶带，压在最上面、半透光
- 在纸上印：`fill(遮罩或多边形, cover, ink)`；`line(pts, width, cover, ink, closed, smooth, dash=(实, 虚))`、`lines(paths, …)` 一批线一次栅格化；`dots`、`circle(cx, cy, r, width=None)`、`hatch(mask, spacing, angle)`、`stipple(mask, n, r)`；`text(s, x, y, size, font_kind, cover, ink, anchor, spacing, rot, halo, knock)`：halo 先清掉字周围的墨，knock 把字从墨里反白掏出（实心圆里的站点编号）；`knock(mask)`、`cross(x, y)` 套准十字、`arrow(tip, direction, size)`、`punch(x, y, r)` / `punch_slot(x, y, w, h)` 打孔
- 遮罩（画布大小）：`poly(pts, smooth)`、`circle`、`ellipse`、`rrect`、`band(pts, width)`；`edge(mask, width)` 轮廓线、`offset(mask, d)` 外扩 / 内缩、`contour(mask, d, width)` 离边 d 像素的一圈线（海岸水线）、`Overlay.inset(凸多边形, d)` 街区从街道往里缩、`circle_pts`
- 字体 `font(kind, size)`：map / map_bold / map_heavy / map_italic / map_light（Gill Sans 一族）、title（Avenir Next Heavy）、label、cjk / cjk_light（黑体），也认 core 的样式名；可用 `INKPAINT_FONT_OVERLAY_<KIND>` 指定
- 常量 `INKS`（black blue yellow magenta cyan orange green red）、`PAPERS`；`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 三张描图纸叠在一起，整张图发灰发脏，背光纤维像大理石纹 | 描图纸透过率 0.955 → 0.98，云纹幅度 5% → 2%、尺度改细（6 / 22 px）；底图纸的云纹只留 1% |
| 抬起的纸下面糊成一片、整块发暗 | 漫射模糊 σ 5.5 → 2.8 px（描图纸），阴影不透明度 0.30 → 0.22，落在纸下面的那部分阴影再减半（室内光还能透过纸照下来） |
| 胶带像一块灰色塑料片 | 胶带是皱纹纸：一半透光、一半反射室内光（I·T·0.58 + T·0.36），颜色用暖奶油 `#f7ebcf`，皱纹和纤维只压暗 3–4% |
| 胶带贴在黄色公园上，成了一块橄榄色斑 | 胶带别贴在色块上：挪到纸边经过街区的地方，或者换个角 |
| 卷角成了一条灰色斜带，像脏印子 | 阴影带收窄（0.11R、只暗 7%），加一道折痕高光；卷角只放在空白页边，蓝片那个落在叠层最密处的卷角干脆不要 |
| 站点圆里的反白数字看不清 | 反白就是「露出下面一层」：站点压在深色地标（车站、集市楼、城堡、灯塔）上，数字就变成深灰。把站点挪到浅色街道、公园或水面上 |
| 步行路线和电车线在同一条路上叠成一条紫黑线 | 同一条路上分道走：电车偏左 4 px，步行偏右 6 px |
| 电车线从路名「STATION ROAD」上穿过去 | 把路名放到别的路上，或者删掉 |
| 公园和马路之间剩下 8–15 px 的细条街区，像一串虚线 | 递归切分的叶子块，按短轴厚度（3.46 × 短轴标准差）小于 12 px 就丢掉，留成空地 |
| 动图 5.1 MB：每落下一张纸，整片带纹理的区域都重新编码 | 见第四节：只重发明显变化的像素，开灯的叠化帧不加抖动；1.9 MB |
| 跳过小变化以后，灯箱渐变和海面上出现一圈圈等高线似的色斑 | 差值拆成平滑分量（模糊 2 px）和细节残差分开判断；停 900 毫秒的关键帧把平滑分量追到 3 级以内；开灯那几帧逐像素精确发送 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
