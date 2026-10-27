# 岩画（petroglyph）

- **实现**：`lib/petroglyph.py` · `Petroglyph`
- **范例**：`examples/petroglyph_migration.py` 迁徙季（带沙漠漆的砂岩岩面：一群大角羊朝同一方向往上走，一串偶蹄印通向同心圆水源，弓手和举投矛器的猎人等在后面；新月和一个月的计日刻痕、螺旋太阳、岩檐下一大一小两只手印；新、中、旧三档凿痕，几乎被漆盖回的旧符号；渗漆的裂缝、鲜橙色剥落疤、壳状地衣；左上低角度侧光）
- **耗时**：约 10 秒
- **内部构成**：岩画（凿刻砂岩：沙漠漆、锤击凹坑、磨刻、剥落）

## 何时选用

远古、史前、起源、「人类最早的记录」、狩猎与迁徙、动物群、天文与历法、讲解片里的「历史开端 / 最早怎么记事」页 → 岩画（凿刻砂岩）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from petroglyph import Petroglyph
```

- 思路：岩画不是画上去的，是把岩面的深色皮（沙漠漆）敲掉。一切都是高度（px）和颜色场，最后用左上一盏低角度侧光照亮：法线明暗、沿光线步进的投影（每个凹坑左上壁暗、右下壁亮）、凹处的 AO
- 构造：`Petroglyph(W, H, seed, light=(-0.62, -0.5, 0.6))`
- 岩石：
  - `rock(colour, relief, bedding, grain)`：砂岩高度图（大起伏、时有时无的层理、砂粒、浅凹坑）和漆下的石色；
  - `ledge(y, drop=34)`：一道折线岩檐，下面的岩面退后一个台阶、漆更薄；
  - `varnish(strength, streaks, top, scour, patches)`：沙漠漆，近乎均匀的深色漆膜 + 清晰的蓝黑流痕 + 浅色流痕，顶部更厚、近地面被风沙磨薄；
  - `fracture(pts, width, depth, seep, branches)`：裂缝，锯齿窄槽、圆肩、分叉，往下渗出深色漆痕
- 起稿：`draft()` 返回 `Draft`（`stroke(pts, w, end_w)`、`fill(pts)`、`dot`、`ring`、`add(mask)`）；现成图形都返回 Draft，可用 `into=` 合成一个：
  - `bighorn(x, y, size, facing, kind='ram'|'ewe'|'lamb', gait, rot)` 大角羊（扭转透视的角）；
  - `hunter(x, y, size, facing, weapon='bow'|'atlatl')` 拉弓 / 举投矛器的猎人；
  - `sun_spiral(x, y, r, turns, rays)`、`crescent(x, y, r, thick, rot)`、`concentric(x, y, r, rings)` 水源；
  - `hand(x, y, size, rot, outline, spread)`、`hoofprints(pts, size, every)` 偶蹄印、`meander(pts, width, smooth)` 任意线
- 凿与磨：
  - `peck(glyph, density, size, depth, age, scatter)`：用成百上千个不规则凹坑把图形敲出来，打穿漆层、碾白砂粒；
  - `abrade(pts, width, depth, age)`：磨出 V 形槽（比凿点光滑、发亮，带顺向擦痕）；
  - `abrade_tally(x, y, counts, gap, length, width, row_gap, slant, age, strike_every)`：成排计日刻痕
- 年代：`age` 0 新凿（亮、锐），0.3 几百年，0.6–0.8 几乎被漆重新盖住；新图凿在旧图上自然更亮、更深
- 风化：`spall(pts, depth, impact, age)` 剥落（小贝壳弧唇口、台阶投影、贝壳状波纹、鲜橙石面，带走上面的图）；`lichen(x, y, r, kind='green'|'orange'|'grey', n)` 壳状地衣
- 顺序：rock → ledge → varnish → fracture → 旧图（age 大）→ 新图 → spall → lichen
- 颜色常量 `STONE SCAR CRUSH VARNISH_FE VARNISH_MN LICHEN`；`stage(name)` 立即合成快照；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 沙漠漆像木纹、像一整幅竖条窗帘 | 不用全幅竖条噪声；漆膜近乎均匀（0.86 ± 0.09），流痕是一条条独立的对象：多从顶部起、往下变窄变淡、略左右漂移，边缘 ±2.5 px |
| 流痕像条形码（硬顶的黑色矩形） | 流痕顶端 50 px 渐入、长度 30%–100% 段渐隐，不从硬边矩形源往下涂 |
| 流痕糊成一团团烟，挂在羊身下面像投影 | 不要整体 bicubic 放大成软团；只在横向留 ±2.5 px 的过渡，纵向才平滑 |
| 流痕像一根根火柴棍 / 芦苇帘 | 宽度取对数正态（中位约 18 px）、约 110 条、只把漆加厚 0.2、锰色 0.6；再加约 26 条更宽的浅色流痕（漆被水流冲薄） |
| 薄漆的「窗口」成了迷彩斑块 | 不用块状窗口，浅色也做成竖向流痕 |
| 凿点太稀，图形像撒了一层粉笔末 | 凹坑数 ≈ 3.4 × 图形面积 / 单坑面积；坑深相加后饱和（dmax ≈ 2.9 px），内部打满只留小暗缝，轮廓在一个坑的尺度上毛糙 |
| 羊身细长像腊肠，整群首尾相连成一条带 | 身体加深（-0.20 到 0.15 个身长）、颈粗；大羊一排、母羊小羊一排错开，彼此留空 |
| 剥落像贴上去的光滑椭圆，四周一圈黑 | 轮廓拆成 14–40 px 的小段、每段向内弯成小贝壳弧；AO 减弱（深度 2.4 / 7 / 22）；疤面颗粒减半、鲜橙色带铁质色带，唇口一圈浅色风化皮 |
| 地衣像绿色颜料点、像一枚枚硬币 | 低饱和橄榄色，椭圆加不规则叶状边、龟裂纹、小黑子实体、周围卫星小点，alpha 约 0.7 |
| 太阳螺旋中心成了「f」，光芒离螺旋太远像飘着 | 螺旋从 1.4 rad、10% 半径起步，中心只点一个小点；光芒从最外圈外 1.7 倍线宽处开始 |
| 蹄印像等号或乱点 | 两瓣从蹄跟到蹄尖向中线收拢成心形（尺寸 ≥ 30 px，凿点 size 0.66）；第一枚离羊蹄远一点 |
| 小孩手印糊成一团 | 手印 ≥ 约 95 px，凿点 size 0.62、density 1.2，手指才分得开 |
| 光秃砂岩像一块木板（层理像木纹、小凹坑像钉眼） | 层理振幅减半且时有时无，石色只随层理变 1–3%；凹坑改成 7–26 px 的浅碟 |
| 画面顶边、左边多出一条黑带 | 投影步进前用边缘复制把高度图 pad 一圈（越界补 0 会被当成一堵墙投下影子） |
| 岩檐只像一道裂缝 | 台阶 34 px 才有一条看得见的檐下投影；檐口折线 + 轻微倒圆 |
| 新旧凿痕只有「全新」和「鬼影」两档 | 加中间档 age 0.3（新月、计日刻痕、掷矛手）：0 新凿、0.3 几百年、0.6–0.7 几乎被漆盖回 |
| 动图里橄榄绿地衣被量化成灰 | 给偏绿像素单独留 6 个调色板位，「和上一帧相同」的占位色用品红 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
