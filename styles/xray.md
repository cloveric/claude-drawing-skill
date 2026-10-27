# X 光片（xray）

- **实现**：`lib/xray.py` · `XRay`
- **范例**：`examples/xray_luggage.py` 行李安检 · Security Check（双能 X 光安检机俯视图：传送带上的硬壳拉杆箱，箱壳轮廓发亮、铝拉杆是两层套管；箱里一把折叠伞、一个旅行吹风机（电机、双重螺旋电热丝）、一台仰面躺着的相机、钥匙和硬币、叠好的衣服、一瓶水，还有一副脊柱里穿着钢销的石膏恐龙骨架玩具；侧栏是同一只包的材料伪彩视图和 1 号物体放大，操作员结论：1 是玩具放行，2 超过 100 ml 要取出；Zeff 和毫升数都是从画面上量出来的）
- **耗时**：约 2 秒
- **内部构成**：X 光片（双能衰减图：实心 / 壳体 / 圆棒管子 / 弹簧 / 侧看与正看的圆片 / 拉链螺钉电线 / 叠放衣物；比尔定律、散射、线阵条纹、光子噪声；胶片显示与安检伪彩、Zeff 与体积读数 OSD）

## 何时选用

「里面有什么」「看穿」「拆开看结构」、透视 / 内部构造 / 原理图解（电器、工具、机械里面长什么样），安检、体检、检测、质检、排查问题，讲解片里的「真相 / 揭秘 / 一眼看穿」页 → X 光片（要手绘的机械分解图用达·芬奇手稿；要「拆开看看」的剪报拼贴用报刊拼贴；要冷热分布用热成像）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from xray import XRay
```

- 思路：不画物体的样子，只建「沿射线方向有多厚的什么材料」。每样东西往两张衰减图里累加 μ(材料, 能量) × 密度 × 沿射线的长度（双能：低能约 60 keV、高能约 120 keV），没有先后遮挡，重叠就相加；再按比尔定律 I = e^(−A) 让射线穿过去，经过探测器（散射雾、焦点模糊、线阵探测器逐行增益条纹和每 64 行的模块缝、光子噪声），最后进显示（胶片：越密越亮；或安检伪彩：按 Zeff 分有机橙 / 无机绿 / 金属蓝 / 穿不透黑）。轮廓发光不是画上去的：空心壳体在轮廓处被射线沿侧壁穿过，路径最长
- 构造：`XRay(W, H, px_cm=17, seed)`；所有长度都是画布像素，包括沿射线的深度，`px_cm` 定物理比例。材料表 `MATERIALS`：organic、water、rubber、pvc、pcb、magnesium、mica、glass、aluminium、bone、plaster、ferrite、zinc、steel、brass、copper、tin、lead
- 轮廓：`rrect(cx, cy, w, h, r, rot)`、`ellipse(cx, cy, rx, ry, rot)`、`poly(pts, cx, cy, rot, scale)`（局部坐标搬到画布）、`closed(ctrl)` 闭合样条、`path(ctrl)` 开放样条（点可带第三维深度 z）、`offset(P, d)` 侧移
- 物体：
  - `slab(outline, material, depth, edge, holes, density, tag, texture)`：实心，边缘按半径 edge 倒圆（默认 depth/2 像卵石，0 是锯切边）；holes 打穿的孔；density 可以为负（钥匙上铣出的槽）
  - `shell(outline, material, depth, wall, edge)`：空心壳（箱子、吹风机外壳、相机机身），轮廓发亮、中间淡
  - `rod(P, material, r, wall, ribs, flat)`：沿路径的圆线 / 圆棒，r 可逐点渐变；wall 变管子（两边亮中间暗）；P 带 z 时沿射线潜下去的段更亮；ribs=(幅度, 周期) 螺纹、双重螺旋、绞合线的起伏；flat 扁带（可以是弧长的函数）。`tube(P, m, r, wall)` 同上
  - `coil(p0, p1, R, turns, material, r_wire)` 弹簧 / 电热丝（侧看：转折点亮、前后两半成之字）；`edgeon(p0, p1, thick, material)` 侧看的圆片（风扇、格栅、滤网）；`disc(cx, cy, r, material, depth, hole, rim, dome)` 正看的圆片（硬币带凸边、垫圈、镜片 dome>0 中厚、镜筒圆环正对射线全是壁）；`ball()` 滚珠
  - `zipper(P, material, tooth, pitch, depth, tape)`、`screw(p0, p1, r, head, pitch)`、`cable(P, r, cores, core_r)`
  - `fabric(outline, depth, layers, sheet, density, weave, scale, angle, creases)`：叠好的衣服，折边处布翻过去成软亮边；`weave('plain' | 'twill' | 'knit', scale, angle, amount)` 也可单独给 `slab(texture=)`
  - `belt(y0, y1, lacing=x)`：传送带（纵向帘线纹）、两侧钢导轨和螺栓、钢钩接头；它的衰减记作空气校准，伪彩视图里自动扣掉
- 探测器和显示：`scan(kv, ma, flux=(低能, 高能光子数), scatter, scatter_px, focal, streak, module)`；`film(a0, amax, mix, edge=(细, 粗), glow, vignette, stops)`；`detect()` → (A'_lo, A'_hi)，`show_film(Lo, Hi)`、`show_material(Lo, Hi)`、`zeff(Lo, Hi)` 可单独用
- OSD：`status(left_lines, right_lines)` 顶栏；`footer(left, right)` 底栏（(文字, 颜色)，琥珀 / 绿 / 红自动加底色块）；`flag(x0, y0, x1, y1, n, label, note, side)` 编号报警框；`panel(x0, y0, x1, y1, title)`；`inset(src, dst, 'material' | 'film', title)` 任意区域的插图；`legend(x, y, w)`；`scale(x0, y0, x1, y1, [(标签, 材料, 厚度px)], title)` 衰减标尺（刻度按同一条显示曲线算）；`text()`、`line(pts, dash=)`
- 读数：给物体加 `tag='名字'`，OSD 文字里写 `{名字.z:.1f}`（Zeff）、`{名字.ml:.0f}`（按水折算的体积）、`{名字.cm2}`；出图时从该阶段的探测器图像上量（物体外一圈扣背景），数字和画面永远对得上；`x.readings` 留着最后一次的读数
- `stage(name)` 存 float16 的两张衰减图和 OSD 条数；`save(path, stages_dir)` 每个阶段用同一张噪声出图，阶段之间只有新加的东西在变；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 恐龙骨架是全画的主角，却又淡又小，头骨被箱子圆角切掉一块 | 骨头半径和厚度都 ×1.6（铸的玩具骨头本来就粗），整体放大到 1.02 倍；脖子放低、头骨下移 22 px、后移 6 px，整副骨架挪到圆角以内 |
| 整幅画太暗，物体像沉在墨水里 | 显示曲线满白点从 A=11 降到 8.5、拐点 0.32 → 0.30；荧光辉光 0.35 → 0.5 |
| 毛衣和牛仔裤看着像比空箱子还暗的「黑垫子」 | 量了一下其实比空箱子亮（红通道 35 对 19），是被亮的折边衬暗了；密度提高（毛衣 0.33 → 0.5、牛仔裤 0.9 → 1.15），加针织 / 斜纹纹理，折边才显得是布 |
| 材料伪彩视图整片橙色：橡胶传送带也算有机物 | 真机做空气校准时传送带就在里面：`belt()` 记下自己的衰减，伪彩视图先减掉它，空处才是白的 |
| 骨架里穿的钢销把 Zeff 读数拉高 | 读数先用物体外一圈的中位数扣掉背景，再取逐像素 A_lo/A_hi 比值的中位数（不用总和之比），石膏读 14.4、水读 6.9 |
| 图例「INORGANIC」挤进了 METAL 色块 | 图例按字宽排，不按等分 |
| 结论表的字跑出侧栏 | 每行压到 40 字符以内（16 px 等宽） |
| 放大插图写着「×0.8」：框的是整副骨架，其实是缩小 | 只框头骨和胸腔，放大约 1.4 倍 |
| 1 号标签压在箱子亮边和密码锁上，看不清 | 标签文字下垫深色底板；读数和标签放同一行 |
| 八根伞骨偏移量正负对称，两两重合，看着只有四根棍子；伞面几乎看不见 | 伞骨绕伞杆的相位错开 0.3 格；伞面 14 层、密度 1.3，加弧形折痕 |
| 传送带接头（一列钢钩）挨着侧栏，像一条拉链 | 挪到画面最左边 |
| 动图用一张调色板时，伪彩插图里的绿骨架变成灰蓝，CLEAR / REMOVE 发白 | 调色板分两段切：蓝色胶片像素切 186 色，彩色像素（橙、绿、红、琥珀）切 69 色；每帧叠同一张 4×4 Bayer（约 ±2.4 级） |
| 峰值内存 0.86 GB | 散射雾在 1/4 分辨率上算；模糊改用切片视图（不用 `np.take` 复制）；OSD 辉光改用 Pillow 的 uint8 模糊；暗角用广播不用 `mgrid` |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
