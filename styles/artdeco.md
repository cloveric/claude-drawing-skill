# 装饰艺术（artdeco）

- **实现**：`lib/artdeco.py` · `ArtDeco`
- **范例**：`examples/artdeco_express.py` 夜行快车 · Night Express（1930 年代喷枪流线型铁路海报：午夜蓝长渐变天空、满月外一圈交替射线、探照灯；雾中远城和阶梯退台高楼，钟楼的钟停在 11:40；河面把城市和月亮反射成横向波纹；栗红流线型列车从城里驶上拱桥迎面而来，金色速度线收拢在车鼻上，头灯照亮铁轨；Deco 金字 NIGHT EXPRESS、阶梯角双金线边框；全画没有一根描边，形体全靠明暗）
- **耗时**：约 12 秒
- **内部构成**：装饰艺术（Art Deco 流线型海报：喷枪渐变 + 遮片硬边、交替射线、阶梯高楼、3D 流线型列车、Deco 字母）

## 何时选用

旅行、交通、城市主题海报，复古而有高级感的主视觉（开业、晚会、发布会、酒店、邮轮、列车），「速度 / 现代 / 黄金年代」主题，讲解片里「历史上的未来 / 1930 年代」的封面 → 装饰艺术（要 80 年代霓虹复古用复古 Synthwave，要几何构成和三原色用包豪斯几何）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from artdeco import ArtDeco
```

- 思路：画家不画线。每个形状都是一张用刀刻出来的遮片（frisket），盖在板上用喷枪喷色，所以边缘锐利、里面是一段平滑渐变；形体只靠明暗：楼是一张平剪影、一侧喷暗一侧喷亮，圆柱体上肩一道高光、下腹一条反光
- 喷枪：`spray(mask, 颜色或整幅颜色场, density, grain, blend='paint'|'screen'|'add')` 一次喷涂；薄涂处有雾滴颗粒（固定噪声 × d(1−d)），实涂处没有；`fade(mask, stops, p0, p1)` 线性渐变，`glow(cx, cy, r, 颜色)` 径向光晕；遮片 `rect()`、`poly()`、`disc()`（都抗锯齿）；`ramp(t, stops)` 色阶
- 天空：`sky(stops, top, bottom)` 长渐变；`burst(cx, cy, rays, contrast, reach, colour, dark, glow, phase, taper, bottom)` 明暗交替射线（亮楔靠近中心略宽，对比随距离衰减，bottom 处截止）；`moon(cx, cy, r)` 偏心径向渐变的球形月亮、光晕、柔边月海；`searchlight(x, y, angle, length, spread)` 探照灯光束
- 城市：`tower(x, base, [(宽, 高), ...], body, rim, light=±1, flutes, windows, slits, far, spire, spire_w, mast, ledge, top_windows)` 阶梯退台高楼，返回顶层顶部中心；`far` 0..1 推进雾里（变浅变蓝变平）；`crown(x, y, w, steps)` 扇形阶梯冠顶（放射窗），返回顶点 y；`clock(cx, cy, r, 时, 分)` 钟面
- 河：`water(horizon, stops, reflect)` 先喷河面渐变，再把地平线以上已经画好的东西镜像进来，打碎成横向波纹，亮的东西反射更强
- 3D 列车：`camera(f, cx, horizon, height)` 水平针孔相机；`express(nose=(X, Z), vp_x, deck, cars, loco, car, gap, nose_len, rake, light, moon)` 在拱桥上渲染流线型列车（距离场 + numpy 球面步进，只对边缘像素 3×3 超采样），返回分层结果 `r`；按画家的顺序叠上去：`frisket(r)` 遮片平涂底色 → `model(r)` 明暗塑形（半朗伯色阶、上肩喷枪高光带、月光轮廓光、下腹反光、远处雾色）→ `lights(r, beam, beam_len, bloom, reflect)` 车窗（卧铺窗帘拉下一半）、头灯、光束、辉光、灯照铁轨、可选的河面倒影；`project(X, Y, Z)` 世界坐标转像素
- 字：`lettering(s, x, base, cap, fill, track, shadow, anchor)` 库内自建的 Deco 展示字母 A–Z（粗竖笔、发丝横笔、高腰线、椭圆字碗），金属渐变填色（中线一道硬分界），可加块状投影；`deco_width()` 量宽度；`caption(s, x, y, size, colour, track, anchor)` 宽字距几何无衬线小字（返回宽度）；`rule()` 金线；`border(inset, gap, width, step)` 阶梯角双金线边框
- 印刷：`finish(paper, tooth, warm, vignette)` 纸纹、微颗粒、暖色偏、轻微暗角
- 颜色常量 `NAVY MIDNIGHT TEAL JADE GOLD BRASS IVORY CREAM MAROON CRIMSON WARM`；坐标像素、y 向下，3D 世界单位米、y 向上；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 车鼻前下方一圈圈指纹状条纹，法线乱跳 | 「把截面朝一个点缩放」得到的不是合格的距离场（命中点残差 0.19 m）；改成竖直核心线段膨胀 R 的精确截面（直侧壁、圆车顶、底部平切），车鼻只沿轨道方向拉伸（只会低估距离，步进安全），残差降到 0.008 m |
| 车头竖直，像电车 | 核心前缘做成斜线（`rake` 约 2.2 m），车鼻向前下方倾斜 |
| 头灯飘在车头前面；奶油窗带在车鼻上被一刀竖直切断 | 斜车头实际伸出的长度比 nose_len 长得多（垂直斜边膨胀）：用二分法实测车鼻表面，头灯、条纹收拢、车鼻素色端头都以实测车尖为准；条纹在最后 14% 前停下，窗带收成尖头 |
| 车身只有几道细金线，远看是一整块红 | 加奶油色窗带（1.95–3.15 m）和上下金线；腰线在车鼻上按截面坐标向车鼻收拢，成为速度线 |
| 钟和扇形冠顶浮在楼顶上面，戳进标题 | 钟画在顶层楼身上（`top_windows=False` 把这层的窗空出来），冠顶从顶层上沿起；近景楼顶都压在副标题下方 |
| 副标题两侧的金线穿过副标题文字 | 先画副标题拿到宽度，金线从标题两端画到副标题外侧 28 px |
| 头灯是一大团白光，像一只眼睛 | 灯球半径 0.3 m、铬圈 0.47 m，光晕 80 / 10 px，自发光 0.85 |
| 头灯光束指回车身 | 光束终点取 60 m 前方会跑到相机后面、投影翻转；终点改为 min(60, 0.6·Z/dz) |
| 头灯照亮前方铁轨，但画面里看不见 | 护栏 0.56 m 高、相机只比轨面高 1.4 m，桥面被护栏挡住；护栏降到 0.25 m、相机抬到轨面上 2 m；掠射角的朗伯项只有约 0.1，改成包裹式（×5 封顶），铁轨成了从左下引进画面的两道亮线 |
| 喷枪颗粒太粗，光束和射线像撒了沙 | 颗粒 = 固定噪声 × 0.2 × d(1−d)：只在薄涂处有，实涂和空白处没有；射线的颗粒 0.45 |
| 河面倒影是一块块迷彩斑 | 波纹按压缩后的深度坐标取噪声，横向拉长约 90 倍、只用两层：近处长而稀、远处细而密 |
| 月亮倒影太弱，黑天空和月亮反射得一样多 | 镜像按亮度加权（0.45 + 1.3·smoothstep(0.35, 0.85, 亮度)），月亮和窗灯拉出一条光路 |
| 车窗倒影成了高架下面一串孤立亮点 | 范例里关掉（`lights(r, reflect=False)`）；要用就把拉伸调长 |
| 月海是脏兮兮的斑点 | 月海用 smoothstep 柔边、浓度 0.13、颗粒 0.25 |
| 动图里红色车身被量化成棕色色块，天空出色带 | 加权调色板（饱和像素 ×5、亮像素 ×2）+ 每帧同一张 4×4 Bayer（约 ±2.4 级）；量化只用 255 个真实颜色，占位透明色用品红，否则最暗的像素被当成透明（自检 9 帧对不上） |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
