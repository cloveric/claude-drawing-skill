# 古埃及墓室壁画（tomb）

- **实现**：`lib/tomb.py` · `TombPainting`
- **范例**：`examples/tomb_harvest.py` 尼罗河丰收（底比斯墓室的一面墙，三栏讲一件事：犁地播种（并轭的牛、扶犁人、撒种人、挥锄人），割二粒小麦（弯腰的割麦人、拾穗的女人、挂水囊的无花果树），书吏点数粮袋（蹲坐的书吏、堆成 5-4-3 的 12 袋粮和上方的象形数字 12、用量斗倒粮的人）；按身份放大的庄园总管、伪象形文字栏、凯凯尔饰带、墙脚的尼罗河；剥落处露出红格和红稿，灰泥脱落、裂缝、潮痕、烟熏）
- **耗时**：约 4 秒
- **内部构成**：古埃及墓室壁画（灰泥、红格红稿、分栏、象形文字、剥落）

## 何时选用

古代文明、历史与考古、农业和劳动场面、「一步一步」的工序或流程讲成分栏连环画、讲解片里的「最早的记录 / 起源 / 古人怎么做」页 → 古埃及墓室壁画；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from tomb import TombPainting
```

- 思路：先「声明」整面墙上的东西，再按古代画工的工序一遍遍画：`wall()` 草筋泥上抹一层石膏灰泥 → `grid(box, cell, base)` 红赭石弹线的比例格（一格是人物的一个比例单位，脚底到发际 18 格）、`guide(p0, p1)` 分栏线 → `sketch()` 红稿 → `ground(颜色)` 绕开人物刷底色 → `colour([颜料…])` 一罐颜料画一遍、`ink()` 最后勾线 → `colour(layer='text')`、`ink(layer='text')` 写字 → `age()`。每一层都留在内存里，剥落时按层露出来
- 部件：`part(pts 或 [多边形…], 颜料, paths=, ink=, width=, z=, alpha=, clip=, layer=)`；颜料名见 `PIGMENTS`（skin 男子红赭、skin_f 女子黄赭、linen、white、yellow 雌黄、blue 埃及蓝、lblue、green、dkgreen、lgreen、red、brown、ochre、black）；按逐像素 z 图叠放，所以按颜料分批画也不会叠错；勾线被上层遮住的部分自动不画
- 人物：`figure(x, 地线y, 身高, pose, facing, sex='m'|'f', wig='short'|'long'|'woman'|'cap', dress='kilt'|'long'|'loin'|'dress', collar)`；`POSES` 有 stand / walk / staff / plough / reap / sow / hoe / glean / carry / hold / scoop / squat，任一关键字都可覆盖（髋 hip、前倾 lean、膝 kf/kb、踝 af/ab、腕 wf/wb、肘弯向 bf/bb、手型 hf/hb、`turn`、脚镜像 `mb`）；返回手、腕、肩、耳的画面坐标和 z（`hand_f`、`z_hand_b`…），`S((x, y))` 把比例单位换成画面坐标，用来挂道具
- 道具：`staff()`、`sickle()`、`hoe(fig)`、`rod()`、`basket(full=)`、`sack(lean=)`、`heap()`、`measure(tilt=)`、`grain_stream()`、`scoop()`、`papyrus()`、`palette()`；拿在手里的东西 z 给 `fig['z_hand_x'] - 0.01`（从拳头后面穿过）
- 动植物：`ox(x, 地线, 长度, facing, colour, patches)` 长角牛（远侧两条腿错开一步，四条腿都看得见），返回 `poll`（架轭处）；`wheat(x0, x1, 地线, 顶, stubble=[(xa, xb)], grab=[(拳x, 拳y, (xa, xb))])` 麦田、留茬和被攥住的麦秆；`sheaf()`、`tree(waterskin=(dx, 长))`、`papyrus_clump()`
- 边饰：`block_border()` 色块边框、`kheker()` 凯凯尔饰带、`band(x0, x1, y, [(颜料, 高), ('rule', 2), …])` 分栏底带、`river()` 尼罗河
- 文字：`column(x0, y0, x1, y1, facing, n, seed)` 按方块（quadrat）排一栏伪象形文字（高窄的并排、扁的上下叠）；`glyph(名字, x, y, 字号, facing)` 单个符号（`SIGNS` 里 23 个，另有 hoe、stroke、heel、coil）；`numerals(12, x, y, 字号)` 象形数字
- 岁月：`age(losses=[(x, y, rx, ry)], zones=[(x, y, r)], cracks, flake, soot, fade, salt, tide, wear_amt)`：成簇剥落（蓝色和裂缝边先掉）、剥到灰泥露出红格红稿、颜料磨薄、灰泥脱落到草筋泥（断续白边、台阶、投影）、裂缝、埃及蓝发灰绿、顶部烟熏、墙脚潮痕和盐霜、蝇斑、灯光暗角
- `stage(name)`、`save(path, stages_dir)`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 弯腰的人还是正面宽肩，后肩翘到头顶上，横过胸前的手臂像一条绶带 | 按前倾角把肩宽往侧面收（前倾 32° 时只剩约 15%），两只手臂都从胸前出发；坐姿直接给 `turn` |
| 蹲坐的书吏把脚转 180° 后脚底朝天，两臂缠在一起 | 压在身下的脚左右镜像（`mb=True`，脚尖朝后），肘部 IK 一律朝下弯，`turn=0.45` 收窄躯干 |
| 灰泥脱落像贴上去的褐色石片，带一圈发亮的白边 | 做成真的高度图：洞深 8 px，低角度光沿高度图投影（左上内壁一道影），洞底近壁处加环境遮蔽；石膏白边只留 2–4 px 且断断续续，洞口四周的颜料按台阶剥落 |
| 底色把人物里的红稿整个盖掉，剥落处只露出黄底 | 底色绕开要上色的形状刷（`ground(around=True)`）：动画里红稿一直留到上色那一步；人物上的剥落露出灰泥上的红格和红稿（`age(zones=...)` 可以指定几处） |
| 干活的人都戴宽项圈，分不出主仆 | 只有总管和书吏戴项圈；劳工赤膊，有的剃短发（`wig='cap'`，露耳朵） |
| 象形数字 ∩‖ 读成「ΛI」：一竖藏在 ∩ 的腿后面 | 每个 ∩ 之后让 0.78 em，竖笔间距 0.3 em，字号 46 px 以上 |
| 粮袋正中那道褶像一张笑脸 | 褶线挪到袋子一侧，竖着走 |
| 无花果树冠是一格格圆点，像波点布 | 尖叶按行排、隔行错开、下一行压住上一行（像鳞片），深浅绿隔行；水囊挂在一根截断的枝上 |
| 锄地的人像在推棍子，量斗像一本书 | 锄头画成倒 V：双手握柄，柄顶绑宽木刃斜插进土，中间一道绳；量斗是上宽下窄的木桶，口上堆着粮，倾斜着倒出一股粮粒 |
| 扛东西的人手捂额头，袋子盖住了脸 | 后手举起扶住，货物压在后肩、在头后面（z 夹在躯干和举起的手臂之间）；部件细节的 z 偏移只给 +0.002，否则筐的编织纹会跳到手臂上面 |
| 埃及蓝像一层蠕虫状噪点 | 蓝、绿两色改用稀疏的亮晶粒加暗颗粒（`T_cryst`），通用颗粒压到 0.05 |
| 底色的斜向刷痕整面平铺，像雨丝 | 两个方向、按大块噪声时有时无，幅度 0.012–0.015 |
| 潮痕像一条钢笔线横穿人物 | 宽约 0.012 H 的柔和带，上沿稍清楚，往下逐渐泛褐 |
| 动图 3.7 MB（满墙颗粒让每次叠化都改掉一半像素） | 关键帧先做 1 px 高斯平滑；量化时新颜色和上一帧已显示的颜色相差不超过 10 级就沿用上一帧的索引（透明差分照样有效，自检仍逐帧比对）→ 1.85 MB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
