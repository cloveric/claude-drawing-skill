# 洞穴壁画（cave）

- **实现**：`lib/cave.py` · `CavePainting`
- **范例**：`examples/cave_hunt.py` 篝火旁的岩洞（只靠篝火和石油灯照亮的石灰岩洞壁讲一次狩猎：野牛画在岩壁天然的鼓包上，背插两支矛，转身对着两个红色猎人；马、雄鹿和母鹿往反方向跑，上方一匹只起了炭稿的马；火堆上方四只吹喷手印，墙脚一排掌印红点；地上放着三堆研磨赭石和炭条的石板、一根吹颜料的骨管；钟乳石帘、钙华薄膜、零星掉色、熊爪抓痕、熏黑的顶壁）
- **耗时**：约 7 秒
- **内部构成**：洞穴壁画（石灰岩洞壁、赭石与炭黑、吹喷与手印、借岩面起伏、篝火与油灯照明、钙华与熊爪痕）

## 何时选用

史前、人类起源、「最早的艺术 / 人类最早怎么画画」、狩猎与动物群、火与夜晚、讲解片里的「艺术的起源 / 远古的一个夜晚」页 → 洞穴壁画（赭石颜料）（要在日晒岩面上凿出来的符号用岩画；要分栏叙事、有文字的古文明壁画用古埃及墓室壁画）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from cave import CavePainting
```

- 思路：颜料是涂上去的，不是凿出来的（和岩画相反）：浅色石灰岩高度图 + 一层层颜料覆盖场（乘进 albedo，石头的斑驳透出来），最后只用地上的篝火和油灯照：每盏都是点光源，半 Lambert 明暗 + 平方反比衰减 + 逐像素沿光线步进的投影（掠射光让每个鼓包都显形）、湿钙华上的高光、凹处一点冷色环境光；再叠火焰发光、泛光、烟和色调曲线。光照缓存，只有高度图变了才重算
- 构造：`CavePainting(W, H, seed)`
- 洞壁：`wall(colour, relief, scallops, grain)` 石灰岩（大起伏、岩脊、溶蚀扇贝纹、颗粒、小坑、赭色和灰色斑、凸处钙华皮）；`boss(x, y, rx, ry, height, rot)` 鼓包（把野牛的肚子、马的侧腹画在上面）；`fold(pts, height, soft, side)` 岩面转折；`flowstone(x0, x1, top, length)` 钟乳石帘（橙色条纹、湿亮）；`crack(pts, width, depth, branches)`；`floor(y, tilt)` 朝观者倾斜的泥地；`floor_h(x, y)` 地面高度
- 火与道具：`fire(x, y, size)` 篝火（石圈、灰、辐射状的柴、火舌、火星、烟柱 + 主光源）；`lamp(x, y, size)` 红砂岩油灯（碗、柄、油面、灯芯小火 + 第二光源）；`stone(pts, colour, height)` 石板 / 石子；`heap(x, y, r, pigment)` 研磨颜料堆；`stick(p0, p1, width, colour, hollow, tip)` 炭条 / 空心骨管（hollow=True，tip 是管口的颜料）
- 起稿（单位坐标，facing 1 朝右 / −1 朝左，size 是身长）：`bison(x, y, size, facing, head_drop)`、`horse(…, gait='run'|'gallop'|'stand')`、`deer(…, kind='stag'|'hind', gait='leap'|'stand')`、`hunter(x, 脚底y, 身高, facing, pose='throw'|'run')`（`anchors['grip']`、`['spear_dir']` 挂矛）、`spear(p0, p1, width)`、`hand(x, y, size, rot, side, spread, fold=(3, 4))`（腕部为原点、手指朝上，fold 是弯下去的手指）、`shape(...)` 自定义；返回 `Figure`：部件 body / legs（只算身体轮廓以下）/ tail / horns / antlers / mane / ears，区域 head / hump / belly / back / front；`fig.sel('head', 'mane')` 取一部分，`fig.anchors['eye']` 等
- 上色（都接受 Figure 或 `fig.sel(...)`）：
  - `sketch(fig, width, passes, strength)` 炭条找形线（每遍沿略微游移的轮廓）；
  - `blow(t, 颜料, density, edge, halo, speckle, rim, gradient, relief, clip, exclude)` 吹喷：软边、晕、雾点、不匀；rim 靠轮廓更浓，gradient 背上更深，relief 在背向火光的岩面上更浓（借岩面起伏），clip 不出界，exclude 留出浅色肚子；
  - `daub(t, 颜料)` 毛皮垫拍涂；`paint(fig, 颜料, kind)` 把猎人、矛整形涂实；`line(pts, width, 颜料, kind='charcoal'|'finger'|'brush')`；
  - `outline(fig, 颜料, width, top, gaps, kind='charcoal'|'blow')` 收边：轮廓内侧一条带，背上和上沿粗、肚子细、有断笔；
  - `dots(pts, r, 颜料)` 掌印点；`stencil(hand, 颜料, spread, puffs)` 吹喷负手印；`handprint(hand, 颜料)` 正手印
- 颜料：`PIGMENTS` 的 red 赤铁矿红赭 / darkred / orange / yellow 针铁矿黄赭 / brown / black 炭黑 / manganese 锰黑 / white 高岭土，或 '#rrggbb'
- 岁月：`calcite(x, y, rx, ry, amount)` 钙华乳白薄膜（盖在画上）；`flake(n, size, min_load)` 零星掉色；`claws(x, y, angle, n, length, spread)` 洞熊爪痕（新鲜浅色沟，划穿颜料）；`soot(x, y, amount, drift, spread)` 篝火熏出的烟柱和顶壁
- 顺序：wall → boss / fold / flowstone / crack → floor → fire / lamp / 道具 → sketch → 红、黄（blow / daub）→ 黑（blow / outline / line）→ 猎人、手印、点 → calcite / flake / claws / soot
- `stage(name)` 立即合成快照，`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 颜料发灰，像褪色的水彩 | 喷涂内部只剩一半覆盖（rim 0.35 × 斑驳 × 0.32 的烟）：主色 density 0.95–0.97、rim ≤ 0.2，空气里的烟降到 0.16，指数色调曲线之后再加对比度 1.18、饱和度 1.18 |
| 岩面像绗缝被、一团团棉花云 | 溶蚀扇贝纹单元 70 px、深 6 px 太规整：放大到 110 px、深 1.8 px、只在一片片区域出现；大起伏用光滑噪声会像云和烟，叠一层脊状噪声 (1−\|2n−1\|)² × 10 px 做岩脊（3 次方、振幅 22 会变成一块块台地） |
| 岩面像砂纸 / 揉皱的纸 | 低角度火光会把逐像素颗粒放大：高度颗粒从 0.55 降到 0.12，40 px 中尺度起伏只给 1.1 px，albedo 颗粒 0.022 |
| 满墙小黑点像波点，改浅后又成了白色亮点 | 小溶蚀坑减到 60 个、深度 0.3 × 半径，坑里 albedo 压暗 30%（积了泥），掠射光下就不会只剩亮边 |
| 墙上一团团「脏影子」 | 是油灯的掠射光把 80 px 的大起伏拉出长影：大起伏降到 46 px，油灯不算投影、只有篝火算，投影最多压暗 70%、soft 5 px |
| 鼓包在火堆对面投下黑团，像污渍 | 小鼓包（18 px）在掠射光下只剩投影：只给要画动物的地方放鼓包、高 26–38 px，而且让动物盖住它的背光面 |
| 折痕末端多出一道刮痕 | 有符号距离在折线末端沿最后一段的延长线翻号：按弧长在两端 220 px 内淡出 |
| 手印喷绘像红色描边的椭圆、甜甜圈 | 用「整只手模糊一次」做喷雾，细手指周围几乎没有颜料、外沿一刀切：改成 11 口气，每口一个高斯团、瞄准指尖和手侧（2/3 瞄上半部），叠加后 1 − exp(−1.8·c)，边缘自然淡出，外围撒雾点；前臂只挡一半 |
| 手印被烟熏成灰手套 | 烟熏 0.22、烟柱窄（spread 0.22），手印 density 0.95、spread 26 |
| 后半身两团黑大腿 | 腿的笔画从髋部 0.13 个身长宽起笔，涂黑时把整条大腿涂了：`legs` 部件 = 腿 × (1 − 身体)，只剩身体轮廓以下的部分 |
| 野牛头和隆肉糊成一大团黑，看不出脸 | 隆肉吹黑，头用深红 0.62；眼睛先点一个浅色杏仁（kaolin）再点黑瞳 |
| 野牛像长方箱子配桌腿 | 重画轮廓：前高后低的背线、肩上高耸的隆肉、深胸和须、腹线往后收、小屁股、短细腿 |
| 马鬃和脖子之间漏一条白缝；区域（头、腹）漏到腿上 | 鬃毛笔画压在颈脊线上；各区域只和 `body` 求交，不和整个剪影求交 |
| 鹿角像一把小梳子 | 鹿角放大、主干向后扫，5 个分叉，宽 0.04 → 0.012 个身长 |
| 裂缝像吊着的细绳、像小树枝（让上面那匹马像挂在绳上） | 改成细的之字形窄缝：两端收尖、宽度随机、深 4 px、最多一条短分叉；别从动物身上穿过 |
| 篝火是一团白光 | 火焰发光降一半，每条火舌按 2× 超采样画、只糊 1.3 px，15 条，外橙内黄，中心光斑 0.55；篝火功率 1.6、衰减距离 1150 |
| 火堆石头像骨头两头的圆钮、柴像哑铃 | 16 块小石头（11 点不规则轮廓、深色、圆顶幂 0.85）排在火堆两侧和后面；柴从火心朝观者方向辐射，按圆柱打光（顶部被火照亮）加发光裂纹 |
| 研磨好的颜料堆像平的色块 | 堆高 1.3 × 半径、颜色边缘放软，低角度火光才照得出一面亮一面暗 |
| 掉色的小片像彩色纸屑、像白灰尘 | 12 点圆滑小片、1.5–4 px、只掉在覆盖 > 0.6 的地方、28 片；露出的石面 × 0.93，不加高差（否则掠射光给每片一圈亮边） |
| 炭条起稿在动图里看不见 | 起稿线是一条约 2.6 px 宽的带（先按线宽糊一下再取 0.12–0.88 的等值带），强度 0.7，画两遍 |
| 炭笔轮廓像一串珠子 | 覆盖 = 线带 × (0.5 + 0.5 × 抓附)，不要全靠岩面「牙口」 |
| 野牛尾巴尖像棒棒糖、火星像雨丝 | 尾尖改成一笔短而粗的黑色笔触；火星减到 11 颗、2–6 px、只在火舌上方 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
