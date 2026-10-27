# 达·芬奇手稿（codex）

- **实现**：`lib/codex.py` · `Codex`
- **范例**：`examples/codex_ornithopter.py` 扑翼机（裱在卡纸上、缺一角的泛黄帘纹纸；一串飞鸟画出一次振翅，红粉笔鸢翼写生和一根大羽毛；中间是蝙蝠翼扑翼机仰视图：右翼用左手「\」排线画完，左翼只起了头、露着铅笔稿；尖笔圆规画的比例圆，曲柄、灯笼齿轮、冠齿轮、滑轮的传动分解图，腕关节特写，划掉的废稿；右到左的镜像伪文笔记、墨点、霉斑、水渍）
- **耗时**：约 8 秒
- **内部构成**：达·芬奇手稿（铁胆墨水鹅毛笔、左手排线、红粉笔、尖笔圆规、镜像手写、机械零件分解图）

## 何时选用

发明、机械原理、「这东西是怎么动的」、从自然到设计（仿生）、工程手稿感的讲解页、「草图 / 构思 / 研究笔记」页、复古科学插图 → 达·芬奇手稿（要现代实验记录用实验笔记本，要讲课推导用黑板板书）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from codex import Codex
```

- 纸：`sheet(tone, mount, margin, laid, chain, lost_corner='br', fold=x, stains=[(x, y, r)], foxing, edges, age)`：裱在卡纸上的帘纹碎布纸（帘纹、链线、纤维、纸齿），自带边缘氧化、缺角、泛黄云斑、霉斑、水渍潮线、可选旧折痕、手翻处的污渍；`show_through(x, y, width, lines)` 背面的字透过纸，左右反过来（所以是正着读的）
- 铁胆墨水和鹅毛笔：`quill(pts, width, ink)` / `quills([...])`，笔宽随宽笔尖方向变、落笔重收笔尖；笔里的墨会用完：越画越淡，再蘸一次又变浓，偶尔在落笔处积一个小墨珠；`contour(pts, searching=2)` 先轻轻找两三遍再定线（修改痕）；`ruled(p0, p1)` 靠尺直线；`dotted(pts, dot_dash=True)` 虚线 / 点划线（轴线）；`arrow(pts)`
- 排线：`hatch(mask, shade, angle=55, spacing, levels=(…), cross=0.76, cross_angle=-38, length, origin, medium='ink'|'chalk')`。55° 是左撇子的「\」；shade 0 亮 1 暗，每多一级 level 就在两线之间再插一层，超过 cross 加一层「/」交叉；按「排」下笔。明暗场：`between(a0, a1, b0, b1)`（从一条线到另一条线 0→1，蒙皮、圆杆）、`radial_shade(cx, cy, r)`；遮罩：`poly_mask(pts)`、`disc_mask(cx, cy, r)`、`Codex.arc(cx, cy, r, a0, a1)` 取弧上的点
- 红粉笔和铅笔：`sanguine(pts, width, pressure)` / `sanguines([...])` 只挂在纸齿上，`rub(mask, amount)` 用手指揉开；`leadpoint(pts)` 淡灰的铅笔起稿
- 尖笔和圆规：`incise(pts)` 无色的刻痕（侧光下一边亮一边暗），`compass(cx, cy, r, a0, a1)` 刻圆弧并在圆心留针孔，`prick(x, y)`
- 常画的东西：`cane(p0, p1, w0, w1, bend, lashings)` 两条线画的藤杆 / 木杆加绑绳，返回轮廓用来挖掉排线；`feather(base, angle, length, width, medium, side, overlapped)` 羽毛（返回轮廓、羽轴、宽羽片外缘）；`bird(x, y, size, phase)` 背视的小飞鸟，phase 从 π/2（翅膀最高）到 −π/2（最低）
- 镜像手写：`write(文本或行列表, x, y, width, size, mirror=True, max_lines)`，mirror 时 x 是右边距、每行从右往左写、左边参差；`prose(n)` 生成意大利语伪文；`label('a', x, y)` 字母标注（`mirror=False` 写正字，如收藏者的页码）
- 意外：`blot(x, y, r)` 带深色潮线和小溅点的墨点、`spatter(x, y, n)`、`strike(x0, y0, x1, y1)` 划掉废稿
- 机械零件（笔绘渲染）：`Camera(cx, cy, scale, azim, elev)` 正交相机；零件 `gear(r, teeth, depth, h, hub)`、`lantern(r, h, staves)` 灯笼齿轮、`crown(r, h, teeth)` 冠齿轮、`crank(arm, r_axle, handle_len, handle_r)`、`pulley(r, h)`、`cylinder()`、`box()`、`extrude()`；`.place(origin, axis, spin)` 摆放、`.named('wheel')` 命名表面组、`merge(...)` 合成一个网格；`solid(mesh, cam, hatch=dict(...), hatch_groups={'wheel.face': dict(...) 或 None})`：z-buffer 去掉被挡住的线、先擦掉身后的墨、按每个面背光的程度排线、只描轮廓 / 折边 / 开口边并连成长笔画；分解图就是把零件沿轴拉开再画点划线
- 颜色常量 `INK_DARK INK_LIGHT SANGUINE LEADPOINT PAPER MOUNT`；字体自动找 Apple Chancery / URW Chancery（Linux）/ Segoe Script（Windows），可用 `INKPAINT_FONT_CHANCERY` 指定；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 排线像一团卷毛、像波浪 | 不要把一条长排线切成一串各自弯曲的短笔首尾相接；手是一排一排地排线：同一层排线共用一组带轻微错位的「排界」，长线只在排界处断开，留 0–2 px 的空隙或交叠；手抖 jitter 降到 0.1，所有笔画朝同一边微弯 |
| 蒙皮整片涂黑，像一幅幅窗帘 | 每片蒙皮用 `between()` 取「从前一根肋到后一根肋」的 0→1 场，明暗取 t²：靠前那根肋留白、靠后那根肋才排线、最深处才交叉，蒙皮才会鼓起来 |
| 翼后缘一段段往外鼓 | 蝙蝠翼蒙皮在两个肋尖之间往里凹；镜像到左翼时法线方向会反，弯曲方向按「朝翼内某一点」决定，不按左右写死 |
| 翼形又钝又圆，像一面帆 | 指骨肋从腕点呈扇形散开，翼尖收成尖角，越往外翼弦越短 |
| 红粉笔鸟翼像梳子、像流苏 | 羽毛不画完整轮廓：只画宽羽片的外缘、圆的羽尖和窄羽片的尾段（`overlapped=True`），一片压一片；羽尖要圆不要尖；初级飞羽比次级飞羽长，外侧几根张开约 7° 成「指」；宽羽片靠外缘处排线（被下一根羽毛压出的影子），覆羽画成成排的小圆弧再揉开 |
| 单根羽毛像一片带叶脉的叶子 | 羽枝每 2.6 px 一根、很细很轻，朝羽尖斜；加一段光秃的羽管和两处羽枝分叉的缺口 |
| 扇形排线时有时无，一块一块 | 明暗值不要正好压在排线阈值上（噪声会让它一半过线一半不过），整片均匀的排线 shade 给得比阈值高一截 |
| 尖笔辅助线横穿整页、像划痕 | 圆规只在需要的地方刻一小段弧（翼尖 ±12°），中心线、肩线可以长；刻痕没有颜色，只靠侧光的明暗 |
| 曲柄看起来像个 L 形铁片 | 曲柄臂在轴端加一个套轴的凸台，木把手更长更粗，并用点划线示意它沿轴滑上去 |
| 分解图的零件和机翼撞在一起 | 先算好投影：相机方位角改为 +22°，轴往左下伸，轴缩短到 250，曲柄落在空白处 |
| 旧纸太干净、像新打印纸 | 除了霉斑还要大片柔和的泛黄云斑（纸的施胶老化不均）；霉斑要有清楚的小核，不能只是一团模糊的晕 |
| 霉斑的晕被切成小方块 | 每个斑点的计算框要按晕的半径（约 7 倍斑点半径）开，不能按斑点本身 |
| 墨色发灰 | 铁胆墨水偏暖：淡处琥珀褐、浓处深赭，叠处更深；纸纤维把墨线轻轻打散 |
| 飞鸟序列只是一串「V」 | 每只鸟加身体、尾羽、腕部转折和翼尖张开的初级飞羽，按 `phase` 走完一次上扑下扑 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
