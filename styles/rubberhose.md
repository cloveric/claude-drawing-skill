# 黑白橡皮管动画（rubberhose）

- **实现**：`lib/rubberhose.py` · `RubberHose`
- **范例**：`examples/rubberhose_morning.py` 早晨的闹钟（7 点整的小卧室：双铃闹钟蹦上床头柜摇铃，一只鞋踮着脚，挥着白手套指着床，「RRRING!」在头顶蹦跳；戴条纹睡帽的枕头还在打呼，举起手套「再睡五分钟」；窗外的太阳在两座山之间打哈欠伸懒腰，阳光落在地毯上，一双拖鞋已经跳起舞；灰色水粉背景、描线上色的赛璐璐、饼切眼、橡皮管四肢，拍成老胶片：柔焦、颗粒、片门晃动、圆角片门、划痕、灰尘和片门里的一根头发）
- **耗时**：约 3 秒
- **内部构成**：1930 年代黑白橡皮管动画（灰色水粉背景、铅笔稿 → 描线 → 平灰上色的赛璐璐、橡皮管四肢 / 白手套 / 饼切眼、黑白胶片：颗粒、片门晃动、圆角片门、划痕灰尘）

## 何时选用

复古动画、老电影 / 默片 / 黑白卡通的感觉、拟人的日常物件又唱又跳、起床 / 闹钟 / 上班这类节奏感强的小场面、讲解片里的「很久以前 / 第一代动画 / 老片头」页 → 1930 年代黑白橡皮管动画（要彩色、蓝铅笔稿的现代手绘卡通用卡通手绘；要网点和对白框的漫画书用黄金时代漫画）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from rubberhose import RubberHose
```

- 思路：照 1930 年代动画厂做一格画面的方式：背景师在板上用灰色水粉画一次背景（平涂 + 干笔刷纹、喷枪光斑和接触阴影，背景线细而灰）；动画师铅笔起稿（两遍、略错开，带结构圆、十字线和动势线）；描线员用黑墨描到赛璐璐上（粗而均匀，压力略有起伏）；上色员在背面涂几档平灰（白、浅、中、深、黑，赛璐璐上不画明暗）；叠在背景上用黑白胶片拍下、印成拷贝、放映很多遍。赛璐璐不透明、从后往前画，后画的挡住先画的；角色要从「后面」经过的背景部分（窗外近山、窗横档、窗帘、被子）存成 clip 遮罩
- 构造：`RubberHose(W, H, seed, ss=2, ink_w=5.5)`（内部 2 倍超采样）；灰阶常量 `WHITE LIGHT PALE MID DARK BLACK INK`
- 背景（画在板上）：`wash(pts, value, value2, axis, tex, line, dark)` 平涂 / 渐变水粉 + 细灰轮廓；`blob(circles, value)` 圆的并集（云、树冠），只描外轮廓；`line(pts, width, dark)`；`airbrush(cx, cy, rx, ry, amount)` 喷枪光斑（正提亮、负压暗）；`light(pts, amount, soft)` 软边光块（地上的阳光、窗档影子）；`pattern(pts, draw_fn, dark)` 小花样（壁纸、波点；dark < 0 提亮）
- 房间：`wall(y1)` 渐变墙纸 + 竖条 + 小枝花 + 踢脚板；`floor(y0, board, vp)` 透视地板、接缝、木纹；`window(x0, y0, x1, y1, bars='sash'|'cross', horizon, valley)` 窗外的早晨（天空、云、远山、树、近山；近山和窗档进 'window' clip），返回几何；`curtain(...)`、`valance(...)` 窗帘和帘头（也从 clip 里减掉）；`nightstand(x0, x1, top, bottom, floor_y)` 返回桌面 y；`bed(x0, x1, head_top, sheet_y, front_y, floor_y)` 从床尾看的床（拱形床头、球形柱头、绗缝被、垂下的被边；被子进 'bed' clip）；`rug(cx, cy, rx, ry)` 编织地毯；`sampler(x0, y0, x1, y1, lines)` 挂墙的格言框
- clip：`clip(name, add, sub, full)` 建遮罩；角色方法的 `clip=`，或 `using(name)` … `using(None)` 把之后的赛璐璐都放进某个 clip
- 赛璐璐基本件：`shape(pts, fill, ow)`（墨线只在填色外侧；fill=None 只描线）；`union(subs, fill, ow)` 几块拼成一块、中间不出线（`('poly', pts)` / `('cap', pts, r)`）；`hose(pts, width)` 等粗、没有肘和膝的橡皮管；`stroke(pts, width, taper)`；`text(s, x, y, size, fill, ow, rot)`；`shadow(cx, cy, rx, ry, amount)` 角色脚下的灰影；`guide(pts)` 只出现在铅笔稿里的结构线
- 橡皮管词汇：`hose_path(p0, p1, bend, bend2)` C 形 / S 形四肢；`glove(x, y, angle, size, pose='open'|'point'|'fist'|'palm', flip)` 四指白手套（三道缝线、外翻袖口；(x, y) 是手腕，angle 是手指方向）；`shoe(x, y, size, facing, tilt)` 大圆鞋（白高光、灰鞋底）；`pie_eye(cx, cy, rx, ry, look, wedge, lid)` 白眼眶 + 切掉一角的黑瞳，lid 是半闭的眼皮；`grin(F, x0, x1, y_top, y_bot)` 张大的笑嘴带舌头；`star()`；`Frame(x, y, s, rot, flip)` 局部坐标
- 角色：`alarm_clock(cx, cy, r, tilt, look, time=(7, 0), arms=[...], legs=[...])` 双铃闹钟（黑表壳、白表盘上的脸、指针、两只铃和甩动的铃锤；arms / legs 给手腕 / 脚踝位置和 bend、pose、facing、tilt），返回局部 Frame，`rh.bells` 是两只铃的位置；`sun(cx, cy, r, arms, ray_style='wavy'|'spiky', clip)` 半睁眼打哈欠、伸懒腰的太阳；`pillow(cx, cy, w, h, arm, clip)` 戴条纹睡帽打呼、举起手套的枕头；`slipper(x, y, size, facing, tilt)` 跳舞的拖鞋
- 特效：`vibration(cx, cy, r, a0, a1, n)` 同心震动弧；`speed_lines([pts])`；`lettering(s, path, size)` 沿曲线蹦跳的粗衬线字（白字黑边，单双号反向倾斜、上下错开）；`zzz(x, y, size)`；`slab_font(size)` 找 Superclarendon / Rockwell 这类粗衬线字体（可用 `INKPAINT_FONT_SLAB` 指定）
- 顺序与快照：背景 → `stage('layout', view='layout')`（纸上的背景铅笔稿）→ `stage('background', view='background')` → 画角色（此时是铅笔稿）→ `stage('pencil')` → `ink()` → `stage('ink')` → `paint()` → `stage('paint')` → 特效 → `film(grain, soft, halation, tone='silver'|'sepia'|'neutral', vignette, weave, gate)` → `age(scratches, dust, specks, fibres, hair, stains, flicker)` → `save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 画面太干净，像矢量插画套了个滤镜 | 镜头柔焦 0.85 px、四角再糊一档；颗粒 0.07、按 √(v(1−v)) 在中间调最重，再叠一层半分辨率的团粒；黑位抬到 0.075、白位压到 0.93，再加片门晃动和圆角片门 |
| 太阳的拳头像带盖的玻璃罐、盐瓶 | 拳头 = 手掌椭圆 + 顶上一排 4 个小圆（卷起的手指，成扇贝边）+ 指缝短线 + 横在前面的拇指；袖口缩短到 0.36 |
| 睡帽帽檐是一个扁椭圆，横在枕头上像一圈光环 | 帽子扣在枕头右上角，帽身从角上长出来往右下耷拉，帽檐改成沿帽口的一条宽带；角色头顶不要放任何扁椭圆 |
| 枕头像方盒子、像吐司 | 超椭圆指数 0.5 → 0.72，四边中点往里收 13%、四角往外顶（枕头角），不倾斜，四角加折痕短线 |
| 拖鞋像礼帽、像汉堡 | 稍微俯视来画：长椭圆鞋底 + 后半开口露出鞋里（浅色鞋口、中灰内底）+ 只盖住前半的毛绒鞋头 + 绒球，眼睛画在鞋头上 |
| 太阳一圈尖三角像参考帧里的太阳（也像皇冠）；改成细波浪线又像睫毛、小虫 | 扇贝边光晕 + 每个凹口一道粗短的放射短线（长短交替、两端略收） |
| 「RRRING!」字母挤在一起 | 字距 0.78 → 0.9 倍字宽；单双号字反向倾斜 ±10°、上下错开 0.12 倍字号 |
| 踢腿的速度线贴着床头柜像裂缝，跳起的拖鞋下面的竖线像钉子 | 去掉贴着家具的速度线，在踮脚的鞋尖外画三道放射短线（敲桌面）；跳起的拖鞋下面画两道「︶」弧线 |
| 绗缝被的棋盘格太抢眼 | 深格只压暗 0.17（原来 0.3） |
| 地板一大片空 | 窗户投下一块梯形阳光（软边 9 px、提亮 0.45）和一道窗横档的影子，拖鞋就在阳光里跳 |
| 动图里铅笔稿几乎看不见 | 铅笔画两遍（1.7 px / 1.1 px），强度 0.8 |
| 动图 2.34 MB | 胶片颗粒让每次叠化都改掉大半像素：和屏上已显示的颜色相差 ≤ 8/255 的像素沿用上一帧（记成透明），自检按实际显示的帧比对，1.54 MB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
