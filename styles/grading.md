# 阅卷批改（grading）

- **实现**：`lib/grading.py` · `Grading`
- **范例**：`examples/grading_math_quiz.py` 数学单元测验 · Unit Test, Graded（深绿毛毡桌上一张米色答题卡，下面还压着两张：左边一排定位黑块、角标、粗黑标题、姓名班级栏、考号格和涂好的涂卡圆泡、得分 / 阅卷人表格、填涂示例；一题三道计算，二题应用题（灰底题目框 + 浅方格横线作答区 + 斜纹阅卷栏）；左边长尾夹夹着深蓝页眉的标准答案卡，下面一张评分小纸条。考生用蓝黑墨水逐行作答；两个朱红橡皮章盖进阅卷栏（书写工整 ✓、列式正确 ✓）；红笔给三道计算打勾，在 128 ÷ 16 = 6（天）下画波浪线、圈出「6（天）」、引线拉到阅卷栏写「应为 8 天」再打叉，答句里的 6 划一道，标准答案卡上 ① 打勾、② 打叉，最后在得分格写 75 并圈起来，笔放在得分格旁；印章一头发干、边缘飞白、轻微歪斜，红墨有浓淡和晕染，纸纹和灯光不均；`--stages` 出 113 个阶段，含纸落下、章落下压一下抬起、红笔边走边写的中间帧）
- **耗时**：约 1 秒（成品）/ 约 35 秒（含阶段）
- **内部构成**：阅卷批改（绿毛毡桌、带位姿和投影的纸与卡片、答题卡部件与装订齿孔、长尾夹、带进度和时间图的红笔 / 批注 / 作答 / 印章、比尔定律红墨、立体红笔与木章道具）

## 何时选用

考试、作业、批改与打分，「对照标准答案逐条检查」的过程（评测、验收、审核、评分规则、哪里错了、为什么扣分），讲解片里的「怎么判对错 / 评分标准 / 检查结果」页 → 阅卷批改（要草稿纸上的随手推演用圆珠笔涂鸦；要实验记录、红笔圈和便利贴用实验笔记本；要明亮的产品界面里打 ✓ / ✗ 用粉彩界面）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from grading import Grading
```

- 思路：深绿毛毡桌上的一张答题卡被批改。每张纸是带位姿的对象：`Paper` 在自己的坐标系里存纸色（斑驳云纹、纤维、轻微起伏、零星纤维丝）、alpha（打孔处镂空）和所有印刷；坐标一律按**纸没转动时的画布坐标**给，纸自己的 `rot` 和 `place()` 的位姿在合成时才套上。抬起的纸略放大、投一片宽软偏移的影，放下后收成贴边细影。印刷是立即的（油墨乘进纸色；反白字用 `mode='knock'` 露出纸本身）。印刷之后写上去的一切都是保留对象 `Mark`，带 `progress`（0–1，写到第几成，可以来回设）：每个 Mark 存一块密度图（比尔定律：纸色 × exp(−密度 × 油墨吸光度)，叠在印刷和别的墨上自然加深）和一张时间图（每个像素第几成时被写到），所以阶段快照能画出写到一半的笔画。最后整幅乘一盏左上暖灯的衰减、暗角和细颗粒，桌面、纸和笔受同样的光照不均
- 构造：`Grading(W, H, seed, keep_stages=True, stages_dir=None)`（给了 `stages_dir`，`stage()` 当场写 PNG，不留在内存里）；`desk(colour=FELT, nap)` 毛毡：大小两级斑驳、细绒、零星绒毛
- 纸：`sheet(x, y, w, h, tint, rot, stack=2)` 答题卡（下面再压 stack 张，错开几像素、略暗）；`card(x, y, w, h, tint, rot)` 卡片 / 小纸条（四周留 110 px，给竖起来的夹子把手）；`place(paper, lift, dx, dy, rot)` 放下（全 0）或抬起（第一次 place 决定叠放顺序）、`remove(paper)`；`paper.to_canvas(x, y)` 纸上坐标 → 当前位姿下的画布坐标；`paper.width(s, size, kind)` 量字宽
- 印刷：`text(s, x, y, size, kind='body', colour, anchor='ls', spacing, alpha, rot, mode='ink'|'knock'|'over')`（返回结尾 x）、`rect(x0, y0, x1, y1, fill, line, width, radius)`、`line(pts, width, colour, alpha, dash=(实, 虚))`、`ellipse`、`hatch` 斜纹、`grid` 浅方格、`rules(x0, x1, ys)` 作答横线、`band` 色带、`checkbox`、`circled(n, cx, cy)` 圆圈数字
- 答题卡部件：`timing_track(x, y0, y1, step=30)` 一排定位黑块、`corner_mark`、`holes(x, y0, y1, step, r)` 装订齿孔（真的镂空，露出桌面和纸影）、`title(s, x, y, size, sub)` 粗黑标题 + 字距拉开的西文副标题、`field(label, value, x, y, x1)` 灰色栏名 + 粗体内容 + 下划线、`ticket(x, y, digits)` 考号格 + 每位一列 0–9 涂卡圆泡（对应的那个涂黑）、`score_box(x, y, w, h, split, head, titles, note, lines)` 得分 / 阅卷人表格（返回得分格中心）、`fill_example(x, y)` 填涂示例、`section(x, y, num, title, sub, meta, x1)` 「一 题目」分节头（深色方块里反白序号）、`question(x0, y0, x1, y1, s)` 灰底题目框加左边竖条、`answer_frame(x0, y0, x1, y1, col, rows=[(栏名, y, 分隔线 y 或 None)], lines)` 作答框：左边浅方格加横线，x ≥ col 是斜纹阅卷栏（表头「阅卷栏 · 考生勿填」、虚线分行）；`clip(x, y, w, handle)` 黑色长尾夹：夹在纸边上的亮黑钢夹，两根竖起的银色钢丝把手各横跨整个夹子（后面那根略低、在阴影里），在纸上和桌上都有投影
- 写上去的东西（返回 Mark 或 Group，都有 `progress` 和 `tip(p)`）：
  - 红笔：`stroke(pts, width, colour, pressure, blob, feather, smooth, density)` 任意笔画（中性笔：落笔一颗墨珠，压力沿线漂移，拐弯处笔走慢、积墨更深，边缘略深，往纤维里洇一点，纸纹凸起处略淡）；`wave(x0, x1, y, amp, period)` 周期和幅度都在漂的波浪线；`ring(cx, cy, rx, ry, tilt, a0, a1, grow)` 手画椭圆圈（越过起点再画一截、越画越大一点）；`leader(p0, p1, bend)` 弧形引线；`underline`；`cross(cx, cy, s)` 两笔叉；`check(cx, cy, s)` 勾；`digits(s, x, y, h)` 按笔画骨架写数字（0–9，倾斜、略不规则）；`score(s, cx, cy, h, ring=True)` 分数：先写数字再圈起来
  - `note(s, x, y, size, kind='bold', jitter)` 批注：粗黑体（不用手写体），每个字略歪、略错位，按红墨处理（字内浓淡、边缘积墨、淡淡洇开），逐字揭开
  - `answer(s, x, y, size)` 考生的蓝黑墨水作答，逐字出现
  - `stamp(cx, cy, label, w=None, h=64, rot, size, check=True, press=(0.64, 1.0))` 朱红橡皮章印：双线圆角框、粗黑字、✓；位移出的毛边、成簇的针孔空白、一头压得轻（细框在那头断开飞白）、边缘积墨、刚盖下的湿晕（`mark.wet` 0–1）、轻微歪斜、章周围纸面压出的一圈凹痕；盖下之前 progress = 0
- 道具：`pen(x, y, lift, angle=28)` 红笔，笔尖落在画布 (x, y)，按圆柱打光：金属锥头和笔珠、带横纹的橡胶握把、镀铬环、上漆笔杆和一道窗光高光、笔夹和铆钉；投影从笔尖起沿笔身越拉越开、越来越软（笔尾被手抬着）；`pen(None)` 收走。`write(mark, progress, lift)` 设进度并把笔尖放到书写前沿（动图逐帧用）。`stamper(mark, height)` 印章悬在印痕上方 height（0–1）：上漆榉木章身（顺长木纹、倒角）、车出来的木把手（旋纹、高光），投影随高度变宽变软；height 0 就是压下去，印痕出现、带湿晕；`stamper(None)` 拿走
- 字体 `font(kind, size)`：heavy（兰亭黑 Heavy：标题、印章）、bold / medium / body / light（苹方）、latin / latin_heavy（Avenir Next）、digits（DIN）、mono（Menlo：考号）；兰亭黑和苹方是 macOS 按需下载的字体，没有时退到冬青黑体、华文黑体，Linux 用 Noto Sans CJK，Windows 用微软雅黑；可用 `INKPAINT_FONT_GRADING_<KIND>` 指定
- 色板常量 `INK GRAY RULE ANSWER PEN STAMP NAVY FELT PAPERS SHADOW`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 红圈从「=」上压过去 | 「6（天）」前只有一个空格（约 11 px），放不下 3 px 宽的圈和两边的空白：让考生在「=」后空两格（约 23 px），圈的左边离「6」12 px、离「=」11 px，右边留 18 px |
| 引线斜着穿过整个作答区，又长又乱 | 阅卷栏里把「批注」排在第一行，和出错那一行同高，引线变成一道平缓的弧 |
| 印章压住阅卷栏的栏名 | 每行留出约 104 px，章高 60、字号 28，章心放在栏名基线下约 42 px |
| 印章一头太淡，「书写」两个字读不出来 | 轻的那头压力 0.52 → 0.58 → 0.64：还是一头发干、细框断开，但字认得出 |
| 红墨像电脑字，看不出浓淡 | 红色在绿、蓝通道吸收很强，密度 0.8 以上只是略微变深：让密度在 0.74 上下浮动（压力 ±0.20、两级斑驳、拐弯积墨最多 +0.26，实测约 0.4–1.2），边缘加深 0.18，洇开的软边模糊 1.7 px；批注字的斑驳按字号的 0.7 倍取尺度，一个字里就有浓有淡 |
| 波浪线像一条正弦曲线 | 周期和幅度都用 1D 噪声漂移，整条往下坡斜一点 |
| 长尾夹的把手像两根发卡 | 真夹子每根钢丝把手都横跨整个夹子：两腿插在夹子两端、顶上一根横梁；画两根，后面那根略矮、在阴影里 |
| 印章木块像一块饼干，把手像巧克力球 | 木纹方向反了（沿长边是高频）：改成跨章身方向高频、沿长边低频再加一点扭曲；把手用同色系的木头，加车旋纹和根部一圈暗环 |
| 章压下去时纸上一圈青边 | 阴影色原来按毛毡调成偏绿，乘在米色纸上发青：改成近中性的 (0.15, 0.14, 0.12)，毛毡上的影照样是绿的 |
| 分数外的圈压到「7」的头 | 圈的纵半径 0.66h → 0.70h，横向多留 0.30h，从左上方 −118° 起笔 |
| 113 张 1920×1080 阶段快照 | 给 `stages_dir`，`stage()` 当场写 PNG（compress_level=1），峰值内存约 0.78 GB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
