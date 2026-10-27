# 复古 Synthwave（synthwave）

- **实现**：`lib/synthwave.py` · `Synthwave`
- **范例**：`examples/synthwave_coastline.py` 海岸线 1987（横条切口的渐变落日沉入海面、倒影碎成一条条光带、线框小岛与线框山脉、霓虹网格地面、霓虹边线的海岸公路、灭点处亮灯的小城、带落日轮廓光的棕榈剪影、驶向城市的尾灯、镀铬大字 COASTLINE 与霓虹手写 Last Sunset、录像机 PLAY 与日期屏显、色度渗色、跟踪噪带和扫描线）
- **耗时**：约 4 秒

## 何时选用

80 年代复古未来、怀旧、夏夜公路与海边、音乐和歌单封面、讲解片的「复古科技 / 回到过去」封面 → 复古 Synthwave（要雨夜城市用赛博朋克，要低分辨率游戏感用像素风）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from synthwave import Synthwave
```

- 思路：
  - 一台水平针孔相机看向无限平地（X 右、Y 上、Z 向前，单位米），颜色缓冲从远到近画；
  - 会发光的东西同时写进发光缓冲，后画的不透明物会挡掉身后的光；
  - 最后四个半径泛光，过曝的通道溢向白色，成片再「过一遍录像带」
- 构造：`Synthwave(W, H, seed, horizon=610, vp_x=1060, focal=1100, eye=3.5, record=True)`；相机工具 `project(X, Y, Z)`、`ground_row(Z)`
- 天空：`sky(stops, ground)` 暮色渐变，地平线下先铺没点亮的地面；`stars(n, bright)` 越近地平线越稀，最亮的带四角星芒；`streaks([(y, x0, x1, 厚)])` 底边被照亮的细条云
- `sun(x, y, r, bands=8, band_top, gaps=(0.2, 0.7), level, gain)`：黄→橙→粉渐变落日，横条切口越往下越厚，切口是真缺口；在地平线处截断
- 远景：
  - `mountains(x0, x1, z0, z1, height, cell, taper, edge=(MAGENTA, CYAN))`：世界坐标里的抖动网格高度场，三角面暗色平涂，边线从山脚品红渐变到山脊青色；
  - `skyline(X0, X1, Z, heights, widths, tall=(X, 高), windows)`：远处小城剪影、窗光、航空红灯
- 地面：
  - `floor(colour, spacing, width, fog, scroll, x_range)`：霓虹网格，逐像素解析线宽，远处换成平均值防摩尔纹，带粉色地雾和太阳光带；
  - `sea(coast, bar, spread, sky, glitter, stretch)`：X < coast 一侧的海，倒影碎成一条条光带；
  - `road(x0, x1, dash)`：光滑路面加霓虹边线和中心虚线；
  - `neon_line(X, colour, width, dash)`：地上任意一条纵向霓虹线（海岸线）
- 物件：
  - `palm(X, Z, height, lean, fronds)`：棕榈剪影，环节树干、仰角不一的叶柄、下垂小叶、椰子、朝太阳一侧的轮廓光；
  - `car(X, Z)`：背影跑车，整条尾灯和路面上的红色倒影
- 字：
  - `chrome_text(s, x, y, size, depth, glints=(字序号...))`：镀铬大字，深色描边、阶梯挤出、发光浅边，上映天空、下映地面，中间一道锐利地平线，左上打光的倒角和四角星闪；
  - `glint(x, y, length)`：单独一个四角星闪；
  - `neon_script(s, x, y, size, colour, rot)`：霓虹手写体；
  - `caption(s, x, y, size, colour, rules)`：字距拉开的小字加两侧细线
- 录像带：
  - `osd(s, x, y, px, anchor)`：5×7 块字的录像机屏显（PLAY ▶、日期）；
  - `vhs(bleed, shift_px, jitter, noise, scan, tracking, head)`：只作用于成片，包括 YIQ 色度模糊右移、重影振铃、逐行抖动、一条跟踪噪带、底部磁头噪声、掉磁白线、扫描线、黑位抬升；阶段快照保持干净
- 颜色常量 `MAGENTA CYAN VIOLET ORANGE YELLOW PINK RED WHITE`；字体用 `synth_font('chrome'|'script'|'caption', size)` 找系统字体（Avenir Next Heavy Italic / Brush Script / 冬青黑体），可用 `INKPAINT_FONT_CHROME` 等指定；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 太阳被泛光冲成一团白，横条切口被光晕填平 | 太阳底色先压到约 0.72、发光 level 约 0.4，让泛光提回来；切口厚度从条距的 0.2 递增到 0.7 |
| 横穿太阳的细条云像多出来的切口 | 有切口的太阳前面不加 `streaks`，细条云只放在太阳外 |
| 海面倒影是一团糊的圆，像水下还有一个太阳 | 按世界深度把水面切成横带，每带横移、以太阳所在列为中心随机拉伸或压缩（越近越乱），再用短划调制；光源的倒影比天空强约 2.4 倍 |
| 远处网格变成一大片平的橘色雾带 | 雾距 150 m，雾色压暗、偏品红；网格线按屏幕像素距离算覆盖，格子小于几个像素就换成平均值，不出摩尔纹 |
| 录像带噪点像画布纹理，线条满屏抖动打折 | 噪点约 0.014、横向拉长；逐行抖动约 0.35 像素，只留一条跟踪噪带和底部磁头噪声 |
| 霓虹手写字白芯太粗，整句像白字；随机断管像渲染错误 | 白芯只取笔画最中间，core 约 0.5；断管默认不加 |
| 棕榈冠像冷杉，改了又像平顶伞 | 叶柄仰角从陡到平均匀分配，加两片下垂枯叶；小叶在 3D 里朝叶尖前扫、向两侧展开再下垂后投影，不要一律竖直挂下 |
| 城市摆在线框山前面，暗对暗，高楼像幽灵 | 城市放在灭点旁、背靠落日余晖，山脉从城市右边才开始 |
| 小岛挡住太阳正下方，吃掉最亮的一段倒影 | 小岛只和太阳左缘略微相交 |
| 阶段快照里地平线下是整块橘色，太阳下半截露在地上 | `sky()` 先铺一层没点亮的暗色地面；太阳在地平线处截断 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
