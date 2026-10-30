# 低多边形（lowpoly）

- **实现**：`lib/lowpoly.py` · `LowPoly`
- **范例**：`examples/lowpoly_canyon.py` 峡谷飞行 · Canyon Run（一帧虚构的 1999 年飞行游戏：小特技飞机在沙漠峡谷的右弯处压坡度，对准九个金环里的第五个，第六个挂在天然石拱下；阶梯状分层岩壁、起伏小面的河、十字插片杜松、雾里化开的方山；半透明螺旋桨盘、金环闪光、镜头光晕；384×216 帧缓冲、15 位色 4×4 有序抖动、无平滑放大 5 倍；HUD：金环计数 04/09、单圈时间、阶梯速度条、赛道小地图）
- **耗时**：约 0.2 秒
- **内部构成**：低多边形（1999 年代 3D：软件光栅化、平面着色、仿射贴图、逐顶点雾、15 位色抖动、点阵 HUD）

## 何时选用

游戏感、复古 3D、「90 年代末 / 千禧年」怀旧、飞行 / 赛车 / 闯关、带 HUD 的「关卡 / 进度 / 任务」页、讲解片里的「早期 3D 图形是怎么画出来的」（线框 → 平面着色 → 贴图 → 雾）→ 低多边形（要 2D 小尺寸游戏感用像素风，要柔和现代的 3D 渲染用柔光 3D，要正交微缩模型用等轴 2.5D）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from lowpoly import LowPoly
```

- 思路：一个只用 numpy 写的软件光栅化器，照 1999 年代主机的做法画：小帧缓冲（默认 384×216）、顶点吸附到整像素、背面剔除、整个场景的三角形按平均深度排成一张表从远到近画（画家算法 / ordering table）、近平面裁剪；每个三角形一个颜色（平面着色），贴图仿射插值、不做透视校正，逐顶点雾；最后 15 位色加 4×4 有序抖动，最近邻放大。调用顺序不影响遮挡
- 构造：`LowPoly(W, H, scale=5, seed, record=True, zbuffer=False, near=0.6, far=260)`；世界坐标 X 右、Y 上、Z 向前，单位米；`zbuffer=True` 是 N64 式逐像素深度
- 相机：`camera(eye, target 或 yaw=, pitch=, fov, roll)`；`aim(世界点, at=(fx, fy))` 转动相机让这个点落在画面的指定比例位置（构图用）；`project(p)`、`ray(sx, sy)`
- 天与光：`sky(zenith, horizon, glow, bands)` 按仰角渐变、太阳周围暖光晕、可选细条云；`sun(screen=(fx, fy) 或 direction=)` 画太阳并定光照方向；`light(lift=度)` 着色光单独抬高；`ambient(sky, ground)` 半球环境光；`fog(near, far)` 逐顶点雾，颜色默认等于地平线
- 地形：`path([(x, z), ...])` 中心线，`along(path, s, u, y)` 取点、`heading(path, s)` 取方向；`canyon(path, step, height, width, wobble, strata, buried)` 沿中心线放样的峡谷（河床、沙岸、碎石坡、两级悬崖和台阶、崖顶、台地；岩壁按高度贴岩层，平面俯贴沙地 / 灌丛）；`river(path, half, ripple, spec)` 起伏小面的河；`mesa(x, z, r, h, base)` 方山；`arch(path, s, span, rise, base)` 天然石拱；`boulder(x, y, z, r)`；`tree(x, y, z, height)` 十字插片杜松（贴图 alpha 硬裁切）
- 物件：`ring(centre, facing, radius, tube)` 多面金环；`aircraft(pos, heading, roll, pitch, size, body, trim, canopy, spinner)` 约 230 个三角形的小特技飞机加半透明螺旋桨盘；`torus()`；`mesh(V, F, colour, uv, tex, lit, spec, shine, blend, alpha, two_sided, fog, bias, cutout, glow)` 任意网格：blend 用 'opaque' | 'half' | 'add' | 'sub' | 'quarter'（当年的四种半透明模式），bias 是排序偏置（负数后画），glow 把面往全亮拉（拾取物）
- 特效：`shadow(x, z, y, radius)` 正下方的圆斑影子（'sub' 混合）；`sparkle(p, size)` 加色四角星；`flare()` 屏幕空间镜头光晕（太阳被挡住就不画）
- 贴图：`texture('strata'|'ledge'|'sand'|'water'|'rock'|'juniper'|'spark')` 32–64 像素的程序贴图，最近邻取样
- HUD（帧缓冲像素坐标）：`text(s, x, y, scale, fill=颜色或自上而下的渐变列表, italic, anchor)` 5×7 点阵字（加粗、斜切、1 px 黑描边加投影）；`counter(label, value, x, y, icon, anchor)` 小标签加大号斜体数字；`icon('ring'|'plane'|'clock')`；`gauge(x, y, value, number, unit)` 阶梯速度条；`panel()` 半透明框；`minimap(x0, y0, x1, y1, path, s0, s1, rings, done, plane, heading, finish, title)` 转到机头朝上的赛道小地图
- 动画：`stage(name)`；`stage(name, wire=True)` 隐藏线线框；`stage(name, fog=False, textures=False)` 平面着色预览（每个面取中心那个纹素）
- 颜色常量 `GOLD WHITE BLACK HUD_YELLOW HUD_ORANGE HUD_RED HUD_GREEN HUD_CYAN`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 悬崖上满是竖向的绿条纹，平台上反而是横向岩层 | 材质错位一格：每个面的材质取剖面里靠内侧的那个点（两端下标取小的），悬崖才贴岩层、平台才贴灌丛 |
| 河床三角形一块块从水面里戳出来 | 画家排序按平均深度，埋在水下的河床有时算得比水面「更近」：完全在水下的面干脆不生成（`canyon(buried=)`），水面带 −2 的排序偏置，像贴花一样后画 |
| 水面一片发白的青色 | 涟漪短划减到 16 条、颜色压暗，水面 spec 0.35；逆光看水本来就亮，别再加 |
| 构图照搬参考图：飞机在正下方、大环正居中、后面的环一个个叠在环里 | 赛道改成右转弯，相机放到飞机右后方，用 `aim()` 把飞机放到左下三分点，金环沿对角线往右上排开 |
| 外弯的岩壁把天空整个挡住，太阳和光晕都没了 | 峡谷整体压低（`height=0.75`），相机降到飞机上方约 2.6 m，视场 52°，留出约两成天空 |
| 从正后方追尾看，飞机只剩一个「十」字，还被画面底边切掉 | 相机放在右后上方，能看到机翼上表面；飞机离镜头约 11 m |
| 一级台阶和相机差不多高，被看成一道发亮的裂缝 | 相机高度避开台阶高度（台阶约 11.8 / 20 m，相机约 16.6 m） |
| 金环又细又发橄榄色，看不出多面体 | 管径 0.6（半径 3.4）、12×5 个面、暖金 #ffaa1a、glow 0.28、spec 2.0、shine 4：暗面偏橙、亮面发黄、迎光的面闪白 |
| 逆光下飞机和金环发灰发闷 | 着色光和画里的太阳分开设：`light(lift=26)` 把着色光抬高 26°（当年的游戏也这么做） |
| 光晕里的空心圆像多出来的金环，正中的绿色六边形像一块石头 | 光晕只用小圆点和实心六边形；画面中心附近只放 2 px 的小点，大六边形放到远端并调淡 |
| 「"」加粗后两撇连成一道横线，「1'07"42」读成「1'07-42」 | 两撇之间空两列（`'#  #'`）；零不加斜杠，斜体时才不像 8 |
| 螺旋桨盘几乎看不见，像一块灰斑 | 半透明盘 alpha 0.36，再加一圈更亮的桨尖圆环 |
| 杜松在逆光里成了黑剪影 | 树带 glow 0.3，叶色提亮 |
| 动图 2.08 MB，金色 HUD 偏棕 | 缩小用 BOX 而不是 LANCZOS（像素硬边不出振铃噪点），调色板样本里饱和像素 ×5：1.63 MB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
