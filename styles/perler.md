# 拼豆（perler）

- **实现**：`lib/perler.py` · `Perler`
- **范例**：`examples/perler_strawberry_coaster.py` 草莓杯垫（方格图纸上的草莓图样与图例，铅笔勾掉已摆的颜色；透明方钉板上摆到一半：草莓摆完、天蓝底色一行行往下铺，镊子夹着下一颗悬在空钉上，旁边散豆；九格分色收纳盒；熨平的圆杯垫：豆子熔成一片蜡质平面、孔缩小、外沿扇贝形，压着揭下的熨烫纸）
- **耗时**：约 9 秒
- **内部构成**：拼豆（钉板、熔珠小管、熨烫融合）

## 何时选用

手作、DIY 教程、「从图纸到成品」的步骤图、把像素图案做成可爱实物（杯垫、挂件、冰箱贴）、讲解片里的「动手做」页 → 拼豆（要屏幕上的像素游戏感用像素风，要布上的针线用十字绣）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from perler import Perler
```

- 思路：整张桌面是高度图，每样东西都是实体（豆是带孔短管、钉板带钉子、纸有厚度），相机略向后仰：每个屏幕像素沿自己那一列找最近的表面，所以豆子露一条侧壁、缝里露出后排侧面、孔里看得到内壁和钉子。光是左上一个大灯箱：局部点光、沿高度图步进的软阴影、天光 AO，镜面反射里看得到灯箱（亮面上是锐利的弧，熔化后变成蜡质光泽）；线性空间着色，`ss` 倍超采样
- 构造：`Perler(W, H, seed, pitch=22, tilt=0.32, ss=2, light=(x, y, z))`；pitch 是珠距（像素），tilt 是后仰量
- 桌面与纸：`desk(颜色, kind='wood'|'mat')`；`chart(rows, key, cx, cy, cell, angle, title, subtitle, number, names, done)` 印好的图纸（格子、符号、行列号、每 5 格粗线、图例带颗数），返回对象的 `.done.update('RD')` 用铅笔勾掉已摆的颜色；`tape(字, cx, cy, angle, size, sub, badge='1')` 美纹纸标签；`sheet(draw, cx, cy, angle, thick, translucency, drape, cut, curl, bump)` 任意薄片
- 钉板与豆：`pegboard(cx, cy, cols, rows, shape='square'|'circle'|'hexagon', colour='clear'|'white'|颜色, angle)` 返回 `Board`（钉子都在方格点上，`xy(row, col)` 取钉子位置）；`place(board, rows, key, at=(行, 列), only='RDP', keep=lambda r, c: ...)` 按文字图样插豆，可按颜色、按区域分批；key 的值用 `BEADS` 色名（含 `pearl` 珠光、`clear` 透明、`glow` 夜光）或 '#rrggbb'
- 熨烫：`ironing_paper(cx, cy, w, h, angle, cut=((x, y), (nx, ny)), curl, wrinkle)` 盖在豆上的半透明熨烫纸，cut 表示揭开一半（卷边），wrinkle 是热皱；`iron(board, melt, where)`：0.4 半熔，0.7 成品，0.8 全平；`lift_off(board)` 取下成品
- 道具：`tray(cx, cy, [[色, ...], ...], cell, angle, fill)` 分色收纳盒（每格一堆豆）；`spill(cx, cy, colours, n, spread, standing)` 散豆；`bead(x, y, 颜色, pose='stand'|'side', angle, tilt)`；`tweezers(tip, angle, length, lift, rise, holding='sky', grip)` 悬空的镊子，尖端夹一颗豆，自带投影
- 层次与动画：`on_top(*objs)` 提到最上层，`remove(obj)` 拿走；`stage(name)` 只存快照，`save(path, stages_dir)` 时才按 1× 渲染各阶段
- 颜色常量 `BEADS`；角度逆时针为正；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 钉板四周出现一整块深灰方框 | 豆子高度只写在豆子覆盖处（其余设 -1e3），别把整个窗口抬到板面高度 |
| 熨过的豆还是一颗颗分开的甜甜圈，和没熨的差不多 | melt 同时控制：外半径 +22%、smooth-min 融合宽度增到 0.55 倍珠距、孔缩 74%、高度降 40%，外沿和孔口分开倒圆；0.4 是半熔（孔在、珠粘、留菱形缝），0.7 是成品 |
| 熨平的杯垫像一块块六角螺母，表面像糖霜 | 接缝沟只在半熔时有（×(1 − m/0.7)²），顶面只留 5% 的枕形起伏，熨烫纸细纹 0.08 px |
| 收纳盒里的豆堆成一根根塔 | 散豆落在下面的东西上，但限高约一层豆（`cap`）；每格约 20 颗，按抖动网格铺开 |
| 镊子像两根筷子、像白纸条 | 两腿成 V 形，尾部合拢、尖端张开一颗豆宽，腿宽 1.5→4.9 px；钢色偏暗，靠拉丝纹和窄的灯箱反射显出金属；悬空层单独投影 |
| 白豆侧壁出现竖条纹、钟乳石状锯齿 | 侧壁的 AO 和阴影改从平滑图上、在墙脚和墙顶内侧取样；墙顶取最近几行的最大高度；太陡的抗锯齿斜坡按侧壁着色 |
| 熨烫纸（缓坡）上出现发丝状细线 | 朝镜头的缓坡会把一行拉成约 1.1 屏幕行，超过 1.5 行才算侧壁 |
| 高光要么看不见，要么每颗豆一圈白光环 | 用灯箱反射：镜面方向落在主光方向 8° 内（越粗糙越宽）才亮，得到左上沿和孔内远侧唇口两道弧；菲涅尔权重压到 0.08 |
| 熨烫纸盖住标签，字变半透明 | 后放的会盖住先放的，用 `on_top()` 把标签、杯垫提到最上层 |
| 图例铅笔勾挤到前一栏数量上；深绿、叶绿都印成 G | 勾直接打在豆子图标上；符号原样印，不转大写 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
