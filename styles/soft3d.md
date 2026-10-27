# 柔光 3D（soft3d）

- **实现**：`lib/soft3d.py` · `Soft3D`
- **范例**：`examples/soft3d_rise.py` 浮出（糖果色小球海里顶出鼓鼓的软字 rise：被挤开的球堆在字脚、几颗骑在字肩上、几颗滚落，i 的点是一颗黄球；天光穹顶、柔光箱主光、粉色轮廓光、环境光遮蔽、软阴影、次表面色调、景深）
- **耗时**：约 46 秒

## 何时选用

产品感、软萌立体、糖果色、MG 片头大字、「3D 渲染」、讲解片封面的立体标题 → 柔光 3D（要手作、捏泥的质感仍用黏土定格）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from soft3d import Soft3D
```

- 真 3D：`Soft3D(W, H, seed, eye, target, fov)` 针孔相机，世界坐标 X 右、Y 上、Z 远离镜头；每个像素一条光线，numpy 在 CPU 上算
- 球海 `ball_field(x0, x1, z0, z1, r, gap, colours, weights, mat)`：方格上成千上万颗球，光线逐格查找（DDA），每格只测一颗球，十万颗也不慢；`tint_balls(x, z, radius, colours, chance)` 局部换色；`floor(颜色)` 球缝里看到的地板
- 主体（有向距离场，只在自己的包围盒里步进）：`text(s, at, size, depth, colour, mat, yaw, spacing, bob, roll, turn, dot)` 鼓鼓的挤出字（字形→精确距离变换→挤出、整圈倒圆、再吹胀；`dot=颜色` 把 i/j 的点换成一颗球；返回 {'heroes', 'dots', 'centre'}）；`rbox()` 圆角盒、`capsule()` 胶囊、`cylinder()` 圆角圆柱、`torus()` 圆环
- `part(heap, reach, pile, pile_top)`：主体从球海里顶出来，被挤开的球落进最近的空窝、堆在脚边（pile 是被挤开球数的倍数，pile_top 是堆的最高高度，别让它挡住字的下半截），周围的球海微微隆起
- 散球：`ball(x, y, z, r, 颜色)` 指定位置；`drop(x, z, r, 颜色, roll)` 从上方落下碰到东西为止，再往低处滚进窝里（roll=0 停在落点，比如骑在字肩上）
- 灯光：`sky(top, horizon, strength, haze, haze_start)` 天光穹顶（背景渐变、地面反光、远处雾）；`key(azimuth, elevation, strength, size)` 大柔光箱主光，size 越大影子越软；`rim()` 轮廓光；`softbox()` 只出现在反光里的灯片。方位角从镜头算：0 从相机身后，−90 左，+90 右，180 主体背后
- 材质 `mat=`：candy（清漆糖果，锐利灯片高光）、satin（缎面小球）、jelly、matte、pearl；缝隙和阴影变深变饱和而不发灰
- `lens(focus, aperture)` 景深（focus 可传 text() 的返回值或一个点，最好和相机一起先设）；`film(bloom, vignette, grain)`
- `save(path, stages_dir, ss=1.5)` 成片超采样；`stage(name)` 是当前场景的真实预览渲染，还没调用 sky() 时是灰色白模

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 掉下去的球悬在字上方，字面上有莫名的暗斑 | AO、阴影、落球这类查询在包围盒外用了盒子距离，球停在了看不见的盒子上；字形距离网格覆盖的范围内一律用精确距离（已修） |
| 字脚一圈球发黑，字的下半侧有黑带 | 球海距离场只查 2×2 格、封顶半格，清空的格子旁边 AO 以为贴着球；改查 3×3 格、封顶一整格，AO 半径 0.3、强度 1.25、留 0.1 的底（已修） |
| 字从球海冒出来，脚下一圈空槽露出黑地板，像抠图 | 被挤开的球不删，按「落进最近的空窝、层层叠、要有三点支撑」堆到字脚：`part(pile=10, pile_top=0.3)` |
| 字埋得太深，s 只露出上半截像 c，整词读成 rice | s、e 用 bob 单独抬高，让它的下半弯露出来；part() 加 pile_top=0.3，只堆一层，堆起的球不能高过字母下半部 |
| 阴影里的薄荷球发青灰、发脏 | 淡紫天光乘薄荷色会发灰：阴影加按材质自身色调的次表面补光，天光调强、主光调弱 |
| 球排成直行一直通到远方，像条纹墙纸 | 整个场景转 30°，行列斜着走 |
| 清晰的字边有锯齿，高光一节一节 | 成片 1.5 倍超采样再 Lanczos 缩小；字形距离场模糊 2 像素，法线差分步长 2.5 个格（已处理） |
| 上三分之一一片惨白，远处和背景之间有一道硬地平线 | 雾色等于背景地平线色，雾距约 42；镜头稍抬，露出天空渐变 |
| 动图 3.4 MB，小黄球被量化成一块平色片 | 景深跟相机一起先设好（每个阶段都柔），曝光并进灯光强度，主光和轮廓光合成一个阶段；调色板样本里彩色像素 ×5 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
