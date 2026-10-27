# 卡通手绘（cartoon）

- **实现**：`lib/cartoon.py` · `Cartoon`
- **范例**：`examples/cartoon_toaster.py` 早安吐司（薄荷绿吐司机笑着弹出两片举手的吐司、「叮！」爆炸框、盘子上打瞌睡的化黄油、窗外日出、墙上 7 点的钟；左侧 ①按下拉杆 ②电热丝烧红 3 分钟 ③弹起来 的图解；蓝铅笔稿留底、毛笔线、错位平涂、赛璐璐阴影、蜡笔天空与烤边、网点橱柜、抖线）
- **耗时**：约 4 秒
- **内部构成**：卡通手绘（逐帧手绘）

## 何时选用

可爱的拟人小物件、日常小事讲故事、带表情的角色、讲解片里轻松的「步骤 / 原理」图解、要逐帧抖线的动画 → 卡通手绘（要立体手作感用黏土定格，要纸片感用剪纸拼贴）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from cartoon import Cartoon
```

- 思路：照动画师画一张原画的顺序——蓝铅笔起稿 → 勾线 → 平涂 → 赛璐璐阴影 → 蜡笔/网点 → 特效 → 字。每一笔按种类落进一个「组」：`rough` 铅笔、`ink` 墨线、`flat` 平涂、`shade` 阴影/高光/腮红、`texture` 蜡笔/网点/排线、`fx` 特效、`type` 字。`stage(name, show=[组...], rough=强度)` 只显示这些组，画完的一张图可以按作画顺序回放；`with c.group(ink='ink_bg'):` 把某一类改投到别的组，`with c.group('fx'):` 全部改投
- 遮挡：东西不透明，`fill` 会挖掉身后已画的墨线和颜色（隐藏线自动去掉），所以先远后近；`fx`、`type` 是最后叠上去的覆盖层，它们的挖空只在显示时生效，阶段快照不会出现空洞
- 墨线：`line(pts, width, taper)` 毛笔线（落笔细、中段粗、收笔尖，有手抖和压力起伏）；`outline(pts, width, weight, gaps)` 一笔画完的闭合轮廓，首尾两个尖头交叠，背光的右下侧按 weight 加粗，`gaps=n` 留几处小断口；`ink_fill()` 实心墨块、`dot()` 墨点。每条墨线会自动先起一遍蓝铅笔稿（`rough=False` 关掉），`sketch()` 只画铅笔辅助线
- 颜色：`fill(pts|mask, 颜色, slop)` 平涂，整体错开 slop 像素、边缘游走，返回 `Mask`，可作 clip；`shade(形状, 颜色, offset=(dx, dy), clip)` 硬边赛璐璐阴影（形状减去朝光源挪过的自己，得到背光侧的月牙），offset=None 时直接用给的形状；`glint(pts, width)` 白色高光笔；`shape(pts, 颜色, shade=(颜色, dx, dy), shade2=...)` 一次做完平涂、两层阴影和描边；`darker(颜色)` 取阴影色
- 质感：`crayon(形状, 颜色, pressure, angle)` 蜡笔（只挂在纸纹凸起上，顺着涂的方向有条纹，毛边；pressure 可以是整幅数组，做渐变）；`tone(形状, 颜色, cell, angle, amount)` 网点纸；`hatch(形状, angle, spacing)` 墨线排线（接触阴影）；`blush()` 腮红
- 角色：`face(cx, cy, size, mood, rot)`，mood 可选 happy（^ ^ 眼加张嘴吐舌）、wow（圆眼加 o 嘴）、sleepy、smile、wink，自带腮红；`arm(肩, 手, bend, hand, thumb)` 橡皮管手臂加带拇指的白手套（先画手臂再画身体）
- 特效（默认进 fx 覆盖层，`fx=False` 当普通物件画）：`sparkle()` 四角闪光星、`speed_lines(p0, p1, angle)` 速度线、`steam()` 热气、`puff()` 扇贝边烟团、`burst()` 爆炸星形框、`crumbs(..., avoid=遮罩)` 飞溅碎屑、`pop_lines()` 强调短线
- 字（默认进 type 覆盖层）：`letter(s, x, y, size, fill, depth, depth_colour)` 大标题字（中文圆体加漫画西文，每个字微转、上下跳，带挤出阴影、左上白边和粗墨描边）；`note()` 手写注释；`arrow()` 手绘箭头；`badge(x, y, r, '1')` 编号圆标；`pencil_note()` 纸角的蓝铅笔编号；`text_width()` 量宽度
- 形状：`Cartoon.rrect_pts(x0, y0, x1, y1, r 或 (左上, 右上, 右下, 左下))`、`ellipse_pts(cx, cy, rx, ry, rot, a0, a1)`（给 a0/a1 就是一段弧）、`densify()` 保留尖角的折线、`place(局部点, cx, cy, scale, rot)` 摆放在局部坐标里画好的物件；`mask(pts)` 整幅遮罩，可以用 numpy 相乘相减
- 抖线：`Cartoon(..., boil=2.0)`，每次 `stage()` 用一张新的平滑位移场重描墨线（1–2 像素），颜色和铅笔稿不动；`save()` 用第 0 次描线
- 角度都是逆时针为正（同 PIL）；颜色常量 `INK PAPER PENCIL WHITE RED YELLOW PINK ORANGE`

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 窗外的太阳画到了墙上 | 窗里的东西都乘玻璃遮罩；被挡住的轮廓只画露出来的那段弧（`ellipse_pts` 给 a0/a1） |
| 手臂从头顶直直伸出、末端一个圆球，像触角或棒棒糖 | 肩膀放在身体侧面中部，先画手臂再画身体；bend 的正负让手肘朝外弯；手套加拇指、袖口和两道指缝 |
| 两个角色挨得太近，一个的手套落到另一个脸上 | 只画外侧那只手臂，内侧的藏在身后 |
| 烤色蜡笔涂在面包中间，像脸上的脏污 | 烤色只涂面包芯内缘一圈（轮廓遮罩减去内缩的轮廓），脸所在的中间保持干净 |
| 纸纹太粗，色块上像砂纸 | 纸纹受光约 0.026，颜料盖住的地方纹理减半（已处理） |
| 闪光星像菱形 | 用指数约 3 的星形线，竖向拉长（已处理） |
| 白字写在米色纸上看不见；白云、手套、烟团都是白色小圆团，挤在一起分不清 | 浅色字只写在深色块上；白色圆团之间拉开距离，背景里不放白云 |
| 飞溅的碎屑落到脸上 | `crumbs(..., avoid=角色遮罩)` |
| 动图 2.3 MB：铅笔稿每阶段换强度又跟着抖，网点和蜡笔也跟着抖，每次叠化都整片重编码 | 只抖墨线，颜色和铅笔稿留在纸上不动；铅笔稿强度在勾线之后固定；阴影和质感合成一个阶段（1.9 MB） |
| 黄油的嘴压在底边线上；滴落太小，水洼像一根黄条 | 脸按物件正面的高度缩放、上移；滴落画成从前沿挂下来连到水洼的一道，最后画，压在轮廓线上 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
