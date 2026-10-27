# 干刷色块（drybrush）

- **实现**：`lib/drybrush.py` · `DryBrushBlocks`
- **范例**：`examples/drybrush_noodle_counter.py` 面馆 · Noodle Counter（一张 4:3 的 mid-century 海报：小面馆柜台前，一位白色平头、粗黑框眼镜、白胡子的老人，穿藏青工装，一手用筷子从碗里挑起面，一手扶着碗；外套亮的一半是青蓝、暗的一半近黑，两半朝不同方向刷，袖子顺着胳膊刷；头是几块肤色平面：亮面、本色、暗面，更暗的鼻侧和暖色鼻头、腮红、暖色的耳朵；手是从拇指一侧看的几条手指，手腕露一截米色袖口；碗里是面、一块红油和葱花；身后一大块滚筒刷的鼠尾草绿色板，右边柜台上一个醋瓶、一个酱油瓶和一杯茶，衬着一块青蓝色块；米白纸上大片留白，右下一个小朱红方块；照参考海报的做法画：纸 → 大色块 → 几块面的外套和袖子 → 头 → 眼镜、胡子、筷子、近处的手 → 静物 → 红方块 → 印刷；`--stages` 出 7 个阶段加成品：纸、色块、外套、头、细节、静物、红方块）
- **耗时**：约 5 秒
- **内部构成**：干刷色块（笔刷坐标系：遮罩转到笔触方向再算、再转回；周期的鬃毛条纹 / 干笔齿 / 滚筒细点 / 梳齿边 / 笔道 / 斑驳纹理；一道道平行的笔或打断的短笔：起笔饱满、收笔干枯、梳齿般的两端、近直的两侧、皴擦、顺笔两侧的干擦边、多遍覆盖、同笔混色、蘸满的笔；滚筒大色板和细刮痕；部分撕口带纤维边的纸片；沿路径的干笔和散撒的短干笔；几块面拼的人物：头、眼镜、白胡子、外套、袖子、手；瓶、碗、杯；朱红小方块；胶印收尾：柔化、纸纹、暗部白点、细尘）

## 何时选用

人物和日常小场景（吃一碗面、喝茶、做手艺、街坊小店）、杂志 / 书籍 / 唱片的复古封面、餐饮和饮品海报，要「色少而准、有手感、有态度」的编辑插画和 mid-century 海报感，讲解片里「这个人 / 这家店 / 这一口」的特写页 → 干刷色块（要剪刀剪的彩纸童趣用剪纸拼贴；要不透明水粉一层层塑形的大头像用复古水粉；要 Riso 网点和套色错版用编辑风手绘；要三原色几何的丝网海报用包豪斯几何；要干净、没有笔触的矢量色块用扁平矢量）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from drybrush import DryBrushBlocks
```

- 思路：照参考海报的做法，先铺最大的色块，再用几块面拼出人物，最后是细节和一个小红方块；不勾线、不做渐变，形体全靠色块的边和叠压。
  - 笔刷坐标系：每块颜色在自己的坐标系里刷：把遮罩（Pillow）旋转到笔触方向沿 +u，在里面用横平竖直的数组算覆盖率、明暗和混色，再转回去，所以鬃毛纹、笔道和干笔收尾永远顺着笔走。
  - 纹理：每张画布只生成一次几张周期纹理，每块颜色取随机位置的一窗：鬃毛条纹（沿笔长约 40 px、横向 1–3 px）；干笔齿（鬃毛条纹 + 更粗的拖痕 + 纸纹，直方图均衡到 0..1，于是「齿 > 1 − 接触压力的地方上色」直接把压力变成覆盖率）；滚筒齿（成簇的各向同性细点）；梳齿边的噪声；笔道明暗；拉长的斑驳。噪声都是白噪声按方向模糊（循环边界）得来的，不是放大粗网格。
  - 笔道：大色块是一道道平行的宽笔或滚筒（`lane` 宽，每道略宽略窄），每道起笔饱满、往收笔越来越干，各干各的（`dry`、`dry_from`）；`stroke_len` 把每道打断成长短不一、各有明暗和干尾的短笔；`passes=2` 再盖一层，块身合拢、两端仍是毛的；`direction` 定走向（+1 / −1 同向、0 随机、2 来回）。
  - 边：横向只稍微柔化（`side`，两侧是略抖的直边），顺笔方向柔化很多（`fringe`），再拿鬃毛纹阈值化：两侧近乎直，两端梳成长短不一的毛齿，干的一端更长（`tines`），毛齿只从柔化带里长出来。
  - 皴擦：斑驳高的地方接触压力下降（`scumble`），颜料只挂在纸纹的齿上，露出纸色或下层颜色；`edge` 是沿轮廓几段干擦的边，只放在顺笔的两侧。`load` 大于 1 是蘸满的笔，快干的地方也照样实（瓷碗）。
  - 叠色：默认不透明水粉（新 = 旧 + (颜色 − 旧) × 覆盖率），干笔扫过另一块颜色时下层从缝里透出来；`mode='multiply'` 像丝网油墨套印（玻璃杯、茶）；`mix=(颜色, 比例)` 让同一支笔里带第二种颜色的条纹。
  - 收尾 `printed()`：像这幅画的胶印：轻微柔化、细纸纹、暗部零星的纸色白点、纸上零星的灰尘（在 render 里加）。
- 构造：`DryBrushBlocks(W, H, seed, keep_stages=True, stages_dir=None)`（总像素不超过 4096²）；`paper(tone)` 铺米白纸并生成纹理。画布坐标是像素，角度是度（0 向右、90 向下）。
- 形状（画布大小的浮点遮罩）：`rect(x0, y0, x1, y1, rot)`、`poly(pts, smooth)`、`ellipse(cx, cy, rx, ry, rot)`、`tube(path, w0, w1)`、`quad(pts)`。
- 色块：`slab(shape, colour, angle, load, dry, lane, fringe, side, tines, scumble, streak, vary, direction, passes, seam, edge, stagger, dry_from, stroke_len, tooth='brush'|'roller', mix, mode, alpha, avoid, clip)` 返回覆盖率，shape 可以是遮罩、(x0, y0, x1, y1) 或多边形点；`piece(shape, colour, torn, cut, rim, …)` 撕 / 剪的纸片：只有一部分轮廓是撕口（`cut` 是留作直切的比例），撕口可带一圈浅色纤维边；`backdrop(box, colour, angle, rough, scratches)` 主体背后的滚筒大色板（几乎平涂、成簇细点、起笔边干净、干的两侧、几道细刮痕）；`accent(x, y, size, colour, rot)` 小方块（x, y 是左上角）；`scratches(mask, colour, n, length, width)`。
- 笔：`stroke(path, width, colour, load, dry, taper, wobble, square, mode, alpha, clip)` 沿路径的一笔干刷（每个像素都知道自己的弧长和横向偏移，纹理顺着曲线走，扁笔头、越画越干）；`scumble(mask, colour, n, length, width, angle, spread, load, dry)` 在遮罩里撒短干笔（胡子、头发、高光），angle 可以是函数 f(x, y)。
- 人物：`head(cx, cy, w, h, tilt, turn, light, skin, lit, shade, warm, ear, hair, crown)` 返回锚点字典（眼睛、鼻子、嘴、下巴和遮罩）；`glasses(head, colour, lens, frame)`；`beard(head, colour, shade, length, width)`；`jacket(neck, shoulders, bottom, lit, shade, dark, shirt, collar, light)`；`sleeve(path, w0, w1, colour)`；`hand(x, y, size, angle, grip, cuff)`。都在局部单位坐标里（中心、大小、倾斜），一个姿势就是几个数；`light=-1` 是光从观者左边来。
- 器物：`bottle(x, base, w, h, colour, shoulder, neck, neck_w, dark, light, label, label2, cap, glass)`；`bowl(cx, rim_y, w, h, colour, band, inside, shade)` 返回（碗身, 碗口里面）；`cup(cx, base, w, h, colour, glass, level, tea)`。
- 收尾：`printed(amount)`；`render()`、`composite()`、`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度。
- 颜色用 `PAINTS` 里的名字（paper cream bone white ink black forest green slab sage leaf ash celadon mint khaki teal lagoon tealblue navy deep sky ice vermilion tomato coral blush ochre tan skin skin_light terracotta umber brown mustard）或 '#rrggbb'。

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 色块里全是垂直于笔触的「梯子横档」，像蜡笔排线，不像干笔 | 各向异性噪声原来是把粗网格放大，格点对齐的列一阈值化就成横档：改成白噪声按方向模糊（沿笔方向在 1/f 分辨率上做再拉回去）；干笔齿改成鬃毛条纹 + 粗拖痕 + 纸纹的混合，干掉的地方才是成簇、宽窄不一的点，不是发丝线 |
| 某些位置空出一整列 | 一维模糊用补零边界，纹理块边缘变暗，色块或绕回的笔触碰到边缘就空一列：纹理改用循环边界 |
| 弯的笔触上还是有横档 | Pillow 的粗线 `line()` 把线段方向量化了，约六成像素记到了错的线段上：改成每段一个垂直于线段的浮点四边形加圆形接头，再修半像素偏移（中位偏差 −0.7 px） |
| 笔触末端一圈圈同心环 | 末端的纹理坐标被钉死：让纹理沿弧长一直延伸过笔端；干笔开始得更晚（`dry_from`），起笔更钝、更饱满 |
| 毛齿伸得太远，拖出一根根长尾巴 | 毛齿只从柔化带里长出来，块身的皴擦也减轻 |
| 外套是一条条整齐的平行条纹，近看像排线 | 每道笔打断成长短不一、各有明暗的短笔（`stroke_len`）；暗的一半几乎实色（`load` 1.02），暗半边上拖过的藏青笔 4 → 3 笔；亮暗两半朝不同方向刷 |
| 第一版有一块颜色是 NaN | 酱油瓶传了 `dark=None`，混色时拿它去算：没有 dark 就不混 |
| 帽子像毛线帽，胡子像巫师的山羊胡，碗又小又扁 | 换成平头白发（顶上和鬓角干笔皴擦，暗侧另一种颜色）、更宽更短的白胡子、更大更深的碗 |
| 白发太高，像一顶发套 | 头发轮廓的顶往下压（−1.12 → −1.06）；交付时白发仍有一点发套感 |
| 热气是一根根细铁丝，改成皴擦带后又是一团灰雾 | 低压力的笔只碰到几行长齿，所以成了线；最后去掉热气 |
| 背景大色板像在下雨，满是竖向条纹 | 两遍原来共用同一窗纹理，缝对着缝：每一遍取自己的一窗；参考图那块是滚筒的平涂细点，不是鬃毛条纹：加 `tooth='roller'` 和 `scratches()`，`backdrop()` 默认用滚筒 |
| 背景色板干的细点落在起笔的顶边上 | 干擦的边按方向加权，只放在顺笔的两侧，起笔边保持干净 |
| 眼镜像墨镜 | 镜片里的暗色 0.45 → 0.22 |
| 近处的胳膊和外套混成一片 | 袖子改用藏青、混一点青蓝，和外套亮的那半分开 |
| 手先像面包、又像软木塞 | 改成从拇指一侧看：亮的手背、四条明暗交替的手指（最下面一条在暗部）、指间暗线、上面一根拇指、指节一笔干高光，手腕加一截米色袖口和袖子分开；交付时手仍是最弱的地方 |
| 碗边的干笔毛齿像速度线 | 碗身毛齿 14 → 5 px，色带 16 → 6 px |
| 瓷碗上有深色条纹，透出后面的黑外套 | 接触压力约 0.97 时纹理窗口的起伏留下约 7% 的空隙，压在深色上很显眼：`load` 允许大于 1（上限 1.08），碗身用 1.05 |
| 鼻子看不见，鼻头像嘴 | 脸颊暗面的边界往外推（0.18 → 0.34），鼻侧用更深的褐色，加一笔亮的鼻梁、更小的暖色鼻头和鼻下阴影 |
| 青蓝色块里的皴擦太花 | 皴擦 0.2 → 0.07，干笔推迟到每道的后段（`dry_from` 0.72–0.95） |
| `jacket(light=+1)` 直接报错 | 暗半边那几笔的 x 范围上下限写反了：改成按光的方向取暗半边 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
