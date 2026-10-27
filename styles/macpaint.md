# 1-bit 早期画图软件（macpaint）

- **实现**：`lib/macpaint.py` · `MacPaint`
- **范例**：`examples/macpaint_garden.py` 窗台花园 · Windowsill Garden（一台 1984 年式黑白画图软件的整屏：菜单栏、工具栏、图案板、条纹标题栏窗口；画布上一扇窗，格子布窗帘画好左边再翻转复制出右边，窗外是图案分带的天空和山坡小屋；窗台上种子袋和三盆向日葵讲 40 天：发芽、长叶、开花，喷壶还对着第 2 天那盆滴水；黑猫盯着一只被选框行军蚁框住的白蝴蝶；Shadow 样式标题 watch it grow!；全画只有黑白两值，色调全靠 8×8 图案）
- **耗时**：约 0.4 秒
- **内部构成**：1-bit 早期画图软件（640×360 黑白帧缓冲、8×8 图案、当年的绘图工具与文字样式、菜单 / 工具栏 / 图案板 / 窗口界面）

## 何时选用

复古电脑、「第一代图形界面 / 早期个人电脑」怀旧、黑白像素插画、软件和工具的「界面 / 操作步骤」图解、讲解片里的「当年的电脑怎么画画」页 → 1-bit 早期画图软件（要彩色的低分辨率游戏感用像素风；要打印纸上的字符画用 ASCII 字符画）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from macpaint import MacPaint
```

- 思路：画的不是「像素风插画」，是一台 1984 年式黑白画图软件的整屏。640×360 帧缓冲只有黑白两值，×3 最近邻放大到 1920×1080。文档位图 `doc`（1 = 黑）里的一切都按当年工具的规矩画：8×8 图案贴着文档原点平铺（同一图案的两块天然对缝，图案不随形状弯）；线是方笔头 Bresenham；形状 = 图案填充 + 画在轮廓内侧的边框；油漆桶是 4 连通泛填；文字关掉抗锯齿，样式是对字形遮罩做位运算。界面在渲染时才画，所以每个 `stage()` 都能换工具、图案、光标、菜单
- 构造：`MacPaint(seed, title='untitled', menus=(...), screen=(640, 360), scale=3, ink, paper, doc=None, scroll=(0, 0))`；文档坐标原点是窗口内容区左上角，默认 554×246
- 图案：`PATTERNS` 共 41 种（white / black / gray 50% / light 25% / lighter 12.5% / mist / faint / dark / darker，dots、polka、hlines、vlines、diag、rdiag、thick_diag、grid、xhatch、bricks、scales、weave、basket、diamonds、shingles、waves、zigzag、stars、sprigs、checker、gingham、hstripes、vstripes、wood、grass、pebbles、circles……），图案板显示其中 `PALETTE` 38 种；`paint(mask, 图案, mode='opaque'|'or'|'erase'|'invert')`；`bands(mask, [图案…], y0, y1)` 用几条图案带做「渐变」，接缝处交错打散
- 形状工具（都返回遮罩）：`rect(x0, y0, x1, y1, fill, line, radius)`、`oval(cx, cy, rx, ry, fill, line)`、`shape(点, fill, line, smooth)` 自由形 / 多边形；`line(p0, p1, width)`、`pencil(点, mode)`、`brush(点, size, shape='round'|'square'|'slash'|'backslash'|'bar'|'vbar'|'dot', pat)`、`spray(点, radius, density, pat, clip)`、`bucket(x, y, 图案)`、`dotted(点, gap, size)`；遮罩：`mask_rect / mask_oval / mask_poly / mask_path`、`border(mask, w)` 内侧边框、`pen(mask, w)` 方笔加粗
- 编辑：`copy(rect, to, flip, mask)` 选取 + 拖动复制（flip 是左右翻转，mask 相当于套索选取，背景不跟着走）、`invert(rect 或 mask)` XOR、`erase(rect 或 mask)`
- 文字：`text(s, x, y, size, font='system'|core 字体风格, style=('bold', 'italic', 'underline', 'outline', 'shadow'), anchor='l'|'m'|'r', opaque)`；'system' 是自带的粗体点阵字（大写 9 px 高、2 px 竖笔，只有拉丁字母、数字和少量符号），其他字体走 `core.load_font` 并关掉抗锯齿；outline / shadow 是空心字
- 界面状态（下一次 `stage()` 生效）：`use(tool, pattern, line)` 反白工具（`MacPaint.TOOLS` 里 20 个名字）、当前图案、线宽打勾；`cursor(kind, x, y)`（arrow / cross / ibeam / bucket / spray / brush / pencil，kind=None 隐藏）；`select(rect=…)` 或 `select(lasso=mask)` 行军蚁；`menu(名字, items, checked, hilite, styled)` 下拉菜单，styled=True 时每项按自己的样式写，`menu(None)` 收起；`zoom(x, y, w, h, at, fat)` 放大镜窗，`zoom(None)` 关掉；`retitle(标题)` 存盘改名
- `render()` 返回 640×360 的 0/1 屏幕，`image()` 放大后的 PIL 图；`stage(name)`、`save(path, stages_dir)`（JPG 默认 quality 88，纯黑白时存灰度）
- 动图：帧是纯黑白，缩到 720 宽用 BOX、配固定灰阶调色板（不要用默认的 LANCZOS + 中值切分）

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 写一行 Shadow 样式的字，整张画被擦成白的 | `Image.fromarray()` 出来的图是只读的，`ImageDraw.floodfill` 在只读图上静默不做事，找字腔的泛填就把整张画都当成了字腔；先 `.copy()` 再填（油漆桶 `bucket` 用的是同一个泛填） |
| 蝴蝶放在格子布窗帘和云前面完全看不见；套索的行军蚁把背后的窗帘图案也框进去，一团乱 | 小东西放到最空的底上（天空的白带）；蝴蝶改成白翅膀 + 黑翅尖 + 黑点，1-bit 里白底黑边最好认；成品的选区用矩形选框，套索只在纯白底上用，或把物体自己的遮罩传给 `select(lasso=)` |
| 窗台下的喷枪阴影像一条脏草地，花盆脚边和云底的喷点像乱涂 | 喷枪只在窗台下沿浅喷一道（半径 8、密度 0.22），上面先垫一条 50% 灰图案；花盆投影改成灰图案小椭圆；云底不喷 |
| 窗外的山、草地、栅栏全是图案，花盆糊进背景 | 删栅栏，草地换最稀的 `dots`，山用 25%；花盆加深（盆身 50%、背光侧 75%），盆沿最浅 |
| 天空顶带用 12.5% 太密，窗户反而不比墙亮 | 天空 `mist → faint → 白` 三条带，墙纸用 `sprigs`：窗户（光源）是全画最亮的地方 |
| 窗外的圆树正好在苗或向日葵后面，像花上长了根棒棒糖；窗户竖棂正好在第 14 天那盆苗后面，像插了根支架 | 远景小物不要和前景植物重叠（删了树）；盆往旁边挪，避开竖棂 |
| 右边窗帘的坐标没镜像，下半截藏在黑猫后面 | 只画左窗帘，`copy(rect, to, flip=True, mask=窗帘遮罩)` 翻转复制到右边（当年的 Flip Horizontal）；带遮罩，背后的墙纸不跟着走；猫挪出窗帘 |
| 正面坐的黑猫是一团，胡子画在窗帘上 | 改成侧面：椭圆臀、斜椭圆胸、前腿、头、口鼻、两只三角耳拼成剪影，再用白线勾腿和臀的分界、项圈、耳内和眼；胡子用 XOR（`invert`），在黑脸上是白、出了脸是黑 |
| 喷壶嘴和水滴压在格子布窗帘上读不出来 | 喷壶挪进窗洞，壶嘴尖对准第 2 天那盆的盆沿，只留一滴水；左边窗台改放种子袋，标签行补上 day 0 |
| 两盆挪近后 day 2 和 day 14 的标签撞在一起 | 标签中心不跟盆走，单独给一组坐标 |
| 放大镜窗压在主窗口标题栏上 | 放在这一阶段还没画的日历位置；放大范围框住眼睛、耳尖和一点墙纸，才看得出「一格一格」 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
