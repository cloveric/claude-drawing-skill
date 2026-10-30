# 绿屏终端 CRT（crt）

- **实现**：`lib/crt.py` · `CRTTerminal`
- **范例**：`examples/crt_weather.py` 今天带伞吗 · Bring an Umbrella?（80 年代米色机壳的视频终端上敲了一条 forecast 命令，回来一屏绿色 P1 荧光字符画：一整天从左到右画成一条——清晨的太阳、积云、14:00–17:30 在小镇上下雨的雷暴云（闪电、带余辉的雨丝）、雨后碎云、夜里的月牙和灯塔光；下面同一条时间轴上的扫描线气温曲线、八分块雨量柱和反白的「umbrella? YES」；双倍高标题、方框线、烧着旧字的状态栏；扫描线、光晕、桶形畸变，机壳斜面映着绿光）
- **耗时**：约 7 秒
- **内部构成**：绿屏终端 CRT（字符内存与 5×7 点阵字库、按材质和边选字、扫描线电子束、荧光余辉与烧屏、桶形畸变与光晕、米色机壳）

## 何时选用

终端、命令行、黑客 / 程序员向、老电脑屏幕、「敲一条命令得到结果」、复古版的数据面板，讲解片里的「查询 / 运行结果 / 系统状态」页 → 绿屏终端 CRT（荧光字符画）（要打印在纸上的日志和报表用 ASCII 字符画（行式打印机）；要低分辨率的游戏画面用像素风；要 80 年代霓虹用复古 Synthwave）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from crt import CRTTerminal
```

- 思路：重做一台字符终端，不在屏幕上「画图」：
  - 屏幕上的一切都是字符内存里的字：每格带亮度属性（dim / normal / bold）、反白、下划线，行可以是双倍宽或双倍高；
  - 字库 ROM 是 7×10 点阵格里的 5×7 字，小写字母带两行下伸部；另有一套图形字符：框线 ─│┌┐└┘├┤┬┴┼、画曲线用的五档扫描线横条 ⎺⎻─⎼⎽（`SCAN`）、八分块 ▁▂▃▄▅▆▇█（`EIGHTHS`）、░▒▓、° ·、▲▼◆、箭头；
  - 字符画先画进一张隐藏的「材质 + 调子」图（每格 7×10 个采样），`compose()` 逐格选字：里面的格子按材质的阶梯和调子选字，同组之内做误差扩散；剪影穿过的格子按边的方向和位置选 _ . - ' / \ ( ) |；笔画格子按笔画方向选字。屏幕上「密 = 亮」：暗的东西要稀、要 dim；
  - 电子束每行字扫 10 条扫描线：点拉伸半个点，视频放大器有拖尾，光斑随电流变粗（bold 时扫描线之间的缝被填满）；
  - P1 荧光粉亮到饱和时发白；之后依次是余辉、烧屏、桶形畸变、边缘变暗、玻璃里的光晕，以及房间的倒影
- 构造：`CRTTerminal(W, H, seed, cols=120, rows=36, phosphor='green'|'amber'|'white', opening=(88, 60, 1832, 958), radius=62, raster=(0.955, 0.93), curve=0.065)`；opening 是机壳开口，raster 是未畸变的光栅占开口的比例，curve 是桶形强度；`cw`、`ch` 是一格的像素宽高
- 字符内存：`write(col, row, s, attr)`，attr 取 `'dim'`、`'normal'` 或 `'bold'`，可加 `'+rev'` 反白、`'+ul'` 下划线；`big(col, row, s)` 双倍高双倍宽，占 row 和 row+1 两行（这两行只能放大字，每个字占两列）；`wide()` 双倍宽；`box(c0, r0, c1, r1, attr, title)`、`hline()`、`vline()`；`cursor(col, row, 'block'|'ul')`；`clear()`；`listing(path)` 存成纯文本
- 字符画（隐藏图）：
  - `material(name, ramp, attrs, outline, group, edge, dither)`：ramp 从暗到亮，如 `' .:+*%#@'`；attrs 每档一个亮度，提亮优先靠它，不靠更花的字；outline 取 `'cloud'`（斜坡一律 ( )）、`'round'`、`'straight'` 或 `None`（只按调子，不描边）；group 相同的材质之间不描边；edge 固定轮廓字的亮度
  - 形状：`circle(col, row, r)`（r 按列数，自动按格子比例变圆）、`ellipse()`、`poly()`、`shape()`（平滑闭合）、`rect()`；调子：`sphere_tone()`、`radial_tone()`、`ramp_tone()`
  - 作画：`fill(mask, 材质, tone)`、`erase(mask)`、`stroke(点列, 材质, width, glyph)`；`puffs([(col, row, r), ...], 材质, light, amb, base, flat, base_dark)` 一朵云，base 用整数行，平底打成一根 _
  - `compose(region)` 选字，`reveal(r0, r1)` 把选好的字一段段放进屏幕；`put(col, row, s, attr)`、`sprite(col, row, 行列表, attr, attrs, swap)` 手摆的小件（星、雨、房子、灯塔、开灯的窗），sprite 行内的空格不透明
- 图表：`plot(col, row, w, h, xs, ys, xlim, ylim, attr)` 每列一个扫描线横条、每行 5 档高度，返回 `at(x, y)` 把数据坐标换成格子坐标，方便标注；`bars(col, row, h, values, vmax, attr)` 八分块柱
- 显像管：`trail(col, row, s, level)` 余辉（前一帧约 0.32、再前一帧约 0.10）；`burn(col, row, s, depth)` 烧屏，放在反白条的空白处最好认；`tear(row, dx, lines)` 行同步错位；`power(on)` 关机时只剩玻璃和倒影；`brightness` 光栅底亮
- 动图阶段：关机 → 开机光栅 → 敲命令 → 标题 → 字符画一段段出来 → 曲线 → 柱和轴 → 结论；`stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度
- 常量 `LEVELS PHOSPHORS SCAN EIGHTHS PUTTY ROM_CHARS`

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 桶形畸变用的是归一化坐标里的交叉项（u·v²）；宽屏下，角上的字被剪切成斜体 | 改成真实像素里的径向畸变 src = p·(1 + k·\|p\|²/hw²)，k = 0.065；字不再歪，四边照样外鼓 |
| 反白的 YES 和状态栏里的黑字看不清：点拉伸和视频带宽把 1 个点宽的暗笔画吃掉了 | 点拉伸改在半点分辨率上做，而且放在反白之前；状态栏改用 `dim+rev` |
| 云的内部用 - = + 这类像线的字，远看是一团 `/=-\` 乱码 | 云用 `outline='cloud'`：斜坡一律打 ( )，平顶、平底打 _ . - '。内部只用 . :，亮部靠 dim → normal → bold 提亮，不换更花的字 |
| 剪影成对出现 `//`、`((`，两个格子都当了边 | 剪影只留一格厚：相邻两格是同一个字时，留覆盖率最接近 0.5 的那格，另一格按覆盖率归入里面或外面 |
| 云底是一排扇贝 `(...)(....)` | `puffs(base=整数行)`：底部 `flat` 行内按云的宽度补满，并闭合泡泡之间的小缝；整条云底打成一根 `_` |
| 细线勾的月牙在 5×7 字里像 S 或 < | 月牙不描边，用 bold 的 % # @ 填满（`outline=None`）。内圆半径约等于外圆，向右偏约 0.45r |
| 太阳像六角蜂箱，往下的光芒像腿 | 太阳用 `cloud` 轮廓加径向渐变 . : + * % # @；光芒只画地平线以上那 9 根 |
| 瘦高格子里拿覆盖重心的方向当法线，斜边的字选偏 | 法线按格子尺寸反比换算：nx = −mx/cw，ny = −my/ch |
| 光晕把整屏蒙成灰绿，失去黑底 | 中、远两层光晕只对 L² 做（bold 发光，dim 不发光）；亮度底（brightness）降到 0.016 |
| 房子比天气还抢眼；光标块贴着反白的 YES，连成一个框 | 墙和屋顶改 dim，只有夜里的窗户用 bold #；提示符后面打了半条命令 `forecast --tomorrow`，光标停在命令末尾 |
| 动图里挡圈边上振铃出一圈亮边，暗玻璃和窗户倒影出色带 | 缩到 720 宽用 BOX，量化前每帧叠同一张 4×4 Bayer（约 ±2.4），调色板样本里绿色像素 ×4、亮像素 ×2 |
| 峰值内存 834 MB | 拨轮、LED、压纹图标改在局部窗口里算；机壳斜面朝向屏幕的程度缓存起来；不再每次渲染都建整幅 int64 网格。降到约 0.73 GB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
