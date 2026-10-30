# 热成像（thermal）

- **实现**：`lib/thermal.py` · `Thermal`
- **范例**：`examples/thermal_kitchen.py` 厨房里的温度 · Kitchen Heat Map（晚饭时分厨房的热像仪画面：汤锅的蒸汽卷进抽油烟机，抛光锅盖因发射率低读数低一档；水壶喷出一道蒸汽；烤箱门封漏热，把手上的湿抹布比室温还凉；刚出炉的面包冒热气；冰箱门没关，冷气顺着抽屉淌到地砖上铺成冷舌；猫踩过冷坑又回到暖砖上，留下一串越早越淡的暖脚印；点测温、区域框、沿脚印的线剖面，读数全从画面上读出来；480×270 传感器、噪声与竖条纹、铁红色板）
- **耗时**：约 2 秒
- **内部构成**：热成像（温度场：物体温度、发射率、热晕、热气羽流、冷气舌、余温脚印、釉面反射；热像仪：低分辨率传感器、噪声与竖条纹、细节增强、手调曲线 / 直方图均衡、伪彩色板；读数 OSD）

## 何时选用

温度、冷热、保温与漏热、散热、能耗，「看不见的东西」的可视化（热量、气流、体温、余温留下的痕迹），夜视 / 侦测 / 检测报告感，讲解片里的「数据告诉你哪里热、哪里漏」页 → 热成像（要霓虹夜景氛围用赛博朋克；要手写的实验数据与图表用实验笔记本；要复古仪表盘用复古仪器面板）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from thermal import Thermal
```

- 思路：热像仪看不见颜色和光，只看见每个表面有多热，所以不画 RGB，分三步：先画一张温度场（°C，传感器分辨率的 2 倍）；再让它经过一台非制冷热像仪（镜头模糊、按像元采样、噪声和竖条纹、中心偏凉、细节增强、自动增益）；最后用伪彩色板上色，叠清晰的 OSD。坐标都用画布像素，温度用摄氏度
- 构造：`Thermal(W, H, sensor=(640, 360), ss=2, seed, ambient=21)`；sensor 越小越有热像仪的糊，范例用 480×270
- 形状 → 遮罩：`poly(pts)`、`shape(pts)` 闭合样条、`rect(x0, y0, x1, y1, r)`、`ellipse(cx, cy, rx, ry, rot)`、`blob()`、`line(pts, width)`；用 `*`、`1 - m`、`np.clip(a + b, 0, 1)` 组合
- 温度场：`ramp(p0, t0, p1, t1, ease)` 线性渐变、`radial(cx, cy, rx, ry, t0, t1, power)`、`texture(scale, seed)` 噪声；`room(top, bottom, y_top, y_bottom)` 背景空气分层（上暖下凉）
- 物体：`surface(mask, temp, emissivity, reflected, grain, soft, fuzz, limb, limb_px)`：temp 可以是数或 ramp / radial 场；emissivity < 1 的抛光金属读数被拉向反射温度（默认室温）；grain 材料不匀（°C）；fuzz 毛边；limb 圆形物体在轮廓处变凉。`warm(mask, dT)` 加减热；`seam(pts, dT, width)` 门缝、砖缝、折线
- 热往外走：
  - `soak(mask, temp, reach, strength, onto)`：热晕渗进周围表面（先 soak 再画物体本身，onto 限定承受的表面）
  - `plume(path, temp, w0, w1, opacity, cool, eddy, wisp, puffs, seed, fade_out)`：沿路径的热气 / 蒸汽 / 冷气，越走越宽、越凉、越碎；temp 低于室温就是冷气（路径朝下）；`rise(x, y, height, sway, lean)` 生成一条往上飘的路径
  - `pool(x, y, temp, reach, spread, tongues, squash, width)`：落到地上铺开的冷（暖）气舌，spread 是地面上的方向范围（0 = 向右，90 = 朝镜头）
  - `prints(steps, temp, size, squash, spread)`：余温脚印，steps = [(x, y, 朝向°, 比例, 年龄 0 新 .. 1 没了)]，越旧越淡越散；`paw()` 单个爪印遮罩
  - `reflect(region, axis_y, strength, blur_px, fade)`：釉面地砖倒映上方更热的东西
- 相机：`camera(palette, span, agc, plateau, curve, netd, fpn, optics, dde, dde_clip, narcissus, pixel, saturate)`
  - palette：iron / rainbow / white_hot / black_hot / arctic；span=None 时按画面自动定上下限
  - agc：直方图均衡（平台限幅）占的比例；curve=[(°C, 0..1), ...] 是手调色调曲线，替代线性 span，要让房间、猫、灶台各占一段颜色时用它
  - netd、fpn：时间噪声和竖条纹（°C）；optics：镜头模糊；dde：细节增强（只放大小温差）；narcissus：中心偏凉；pixel：保留多少传感器像素格
- OSD（调用时记下，出图时按该阶段的传感器图像读数，数字和颜色永远对得上）：
  - `statusbar(rec, date, clock, battery, emissivity, mode, height, reflected)`
  - `scalebar(x0, y0, x1, y1, ticks, height)`：宽 > 高是横向；刻度按增益曲线的非线性位置放，挤在一起的自动跳过；给 height 时底部加半透明条
  - `spot(x, y, label, name, side, r)`、`box(x0, y0, x1, y1, label, name)`、`hottest(region)`、`coldest(region)`、`profile(p0, p1, inset=(x, y, w, h), label, name)` 线剖面 + 插图、`results(x, y, width)` 读数表、`reticle()`、`text()`
- `level(v)` 某个温度落在色板的哪个位置；`stage(name)` 只存温度场和 OSD 条数，`save(path, stages_dir)` 统一用最终的增益出所有快照，颜色不会在阶段之间跳；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 地面被底部色标栏挡住，猫只露半身，脚印看不见 | 相机再往下俯（灭点 y 150 → 100，焦距 1900 → 1750），地面留出约 200 px；底栏压到 78 px |
| 自动直方图均衡把 20–24 °C 的房间拉成一大片品红，猫和墙同色 | 改用手调色调曲线 `camera(curve=)`：冰箱内 0–0.05、房间 0.23–0.29、脚印 0.35–0.5、猫 0.6–0.72、锅 0.9、只有火圈到白；直方图均衡只混 0.22，留一点局部对比 |
| 锅和水壶饱和成两个白块，锅像个大马克杯 | 曲线把 100 °C 放在 0.91；锅改宽矮，加卷边和两侧环形把手；抛光锅盖 `emissivity=0.55`，读数比锅身低一档，盖子自己显出来；锅身、壶身、面包加 `limb=`，轮廓处变凉、有体积 |
| 烤箱门是画面正中一块巨大的橙色长方形，抢焦点，还和猫同色 | 烤箱降温（门框 23–26.5 °C、玻璃 26.5–31.5 °C，只有顶部门封 46 °C）；把手上搭一条湿抹布（17.5–20 °C，蒸发降温），把大块面打断 |
| 灶后墙面的热晕像一根发光的柱子一直通到画面顶 | `soak` 只取锅后到油烟机下沿这一块，reach 38、strength 0.4，`onto` 限在油烟机下沿以下、挖掉锅壶罩 |
| 冰箱冷坑在地上看不出来：8–18 °C 都挤在色板最暗的一段 | 铁红色板低端提亮（0.14 → #1f0e6e，0.24 → #3d1192），曲线给 2–19 °C 留出 0–0.23；冷坑芯部降到 6.5 °C |
| 冷坑用噪声阈值做边，成了一片迷彩斑块 | `pool()` 改成从源头分出的几条软冷舌：按地面透视压扁、沿舌头衰减、再模糊 |
| 冰箱里一片死黑，格板和瓶子都看不见 | 格板前沿画成 10.5 °C 的细亮线，瓶罐比内壁高 6–8 °C；冷冻抽屉面板改回接近室温（它有保温层），顺着它往下淌的冷气才显得出来 |
| 冰箱侧板压到下柜前面，多出一条斜边 | 侧板只画台面以上那段和下柜前沿以内的 10 cm |
| 冰箱底的压缩机格栅是一道粉色横杠，挨着黑色冷坑像故障 | 删掉 |
| 猫像一块平涂剪影；Sp3 十字盖住了眼睛 | 加 `limb=`（掠射角发射率下降、毛尖更凉），胸口薄毛加 1.4 °C，后腿折线压暗；眼睛 38.6 °C 并把曲线 35–39 °C 段拉陡；Sp3 挪到胸口 |
| 后腿椭圆的轮廓变凉一圈，看着像一盘蚊香 | 后腿的 limb 降到 1.2 °C |
| 线剖面插图的曲线是暗紫色画在暗底上 | 曲线画成白线加黑描边，下面另画一条按色板着色的色带 |
| L1 虚线压在脚印上 | 虚线改成 1 px |
| 动图里蒸汽和墙面热晕出一圈圈色带，OSD 白字被量化成淡黄 | 调色板取样时饱和色 ×5、亮色 ×2，每帧叠同一张 4×4 Bayer（约 ±2.4 级）；强制留出纯白、纯黑、REC 红、最冷标记蓝和两级灰 6 个色位 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
