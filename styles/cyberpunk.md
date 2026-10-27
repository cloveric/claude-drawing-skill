# 赛博朋克（cyberpunk）

- **实现**：`lib/cyberpunk.py` · `Cyberpunk`
- **范例**：`examples/cyberpunk_neon_street.py` 霓虹不夜城 · Neon District（雨夜街道峡谷、真玻璃管霓虹竖招牌（坏管与闪烁管）、背光灯箱、过街天桥「不夜城」、全息海月水母广告、电线、飞车光轨、井盖蒸汽、透明伞背影、湿路面与水洼倒影、胶片颗粒与一道撕裂扫描线）
- **耗时**：约 10 秒

## 何时选用

夜景、城市、雨、霓虹、电影感氛围、讲解片的「未来 / 科技 / 城市」封面 → 赛博朋克（要复古小尺寸或像素动画仍用像素风）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from cyberpunk import Cyberpunk
```

- 思路：一台水平的针孔相机看向街道深处，世界坐标 X 右、Y 上、Z 向前，单位是米。所有东西写进 HDR 缓冲（反照率、自发光、z-buffer 深度、倒影镜像行），调用顺序不影响遮挡；`render` 时统一算光：环境光 + 光源外溢照明、深度雾（雾色是城市光的散射）、地面倒影、蒸汽、雨、胶片
- 构造：`Cyberpunk(W, H, seed, focal=1150, vp=(x, y), eye=1.7, fog=125, wall=9.5, road=6, record=True)`；`record=False` 时 `stage()` 不出快照，渲染更快。相机工具：`project(X, Y, Z)`、`ground_row(Z)`、`near_z(side)`
- 远景：`sky()` 被街灯从下面照亮的低云；`skyline(z, x_range, heights, widths)` 远处塔楼剪影、针点窗光、红色航空灯；`light(x, y, r, 颜色, z)` 小点光源
- 楼：`building(side, z0, z1, height, wall, colour, lit, shops=(亮店, 卷帘门, 暗店, 自动售货机))` 透视楼块，正面加沿街立面贴图（窗格、空调外机、雨痕、底商、招牌字，右侧立面的字会自动镜像）
- 霓虹：`blade_sign(side, z, Y0, Y1, '字', 颜色, reach, border=颜色, latin='BAR', dead=[序号], flicker=[序号], kind='neon'|'box', text_colour, level)` 伸向街心、面向镜头的竖招牌；`sign(z, X0, X1, Y0, Y1, ..., vertical=False)` 横招牌或立式灯箱；`neon_text(s, x, y, size, 颜色, z, vertical, dead, flicker)`、`neon_path(点列, 颜色, z)` 任意灯管
- 全息：`hologram(z, X0, X1, Y0, Y1, '海月', 'SEA MOON', level, jelly=(x, y), sub_y)` 半透明投影广告（海月水母、竖排明朝标题、扫描线、撕裂切片、色边、投影边框），只加光，还会照亮雾和墙
- 街道：`street(crossing=(z, 宽), puddles)` 湿沥青、路缘、铺砖、斑马线、积水；`puddle(X, Z, rx, rz)` 指定水洼（放在近处招牌的倒影位置上，能倒映出整块招牌）；`grate(X, Z)` 井盖格栅
- 空中：`walkway(z, Y, thick, deep, windows=None)` 过街天桥（正面可再挂 `neon_text`）；`cables(n, z=(近, 远), Y=(低, 高))` 电线；`light_trail(三维控制点, 颜色, pair, strobe, fade)` 飞车光轨（左行交通：尾灯红、头灯暖白）
- 氛围：`steam(X, Z, height, width, drift, density)` 井盖蒸汽；`mist()` 只躺在远处街面的薄雾；`figure(X, Z, umbrella='clear'|'dark'|None)` 打伞背影（两侧霓虹轮廓光，无脸）；`rain(far, mid, near, slant, rings)` 三层雨和溅落圈；`glitch(y, h, shift, split)` 一道撕裂扫描线，只在成片里出现，用一次就够
- 颜色常量 `MAGENTA CYAN AMBER RED WHITE`；`save('x.jpg')` 默认 quality 88、4:4:4 色度，霓虹边缘不糊

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 倒影按一条地平线整体翻转，位置全错；被近处天桥挡住的远景在倒影里成了黑洞 | 每个物体按自己的着地行（mirror row）翻转，最近者优先；被挡住的空洞用对应行的雾色填 |
| 一楼店面发光太亮太大，近处成了过曝的纯色墙，货物画成色块像霉斑或柱状图 | 店内亮度 0.2–0.45，从天花板往下衰减、两侧变暗，加货架侧影和人影；最近的街区多放卷帘门和自动售货机 |
| 雨丝统一提亮成满屏灰帘，溅落圈太大像气泡 | 每根雨丝按周围光照上色，只在霓虹附近看得见；溅落圈半径 3–11 厘米，只在水洼里亮 |
| 蒸汽用背后的暗画面照亮，完全看不见 | 蒸汽按光源外溢光照明（像一块浅色表面），再加前向散射 |
| 光轨沿街飞，全都汇向灭点，像激光或钢丝 | 让飞车横穿街道：从一侧墙后出现，拱形掠过，消失在另一侧墙后；加频闪点 |
| 全息水母的 1 像素线被雾和扫描线吃掉；C 形生殖腺像数字「93」，后排两个像一双眼睛（成了脸） | 线宽至少 2 像素；生殖腺放在伞内的水平面上，侧视压成一条柔和的粉带；副标用 Light 字重，撕裂切片别落在字上 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
