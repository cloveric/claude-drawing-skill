# 报刊拼贴（newscollage）

- **实现**：`lib/newscollage.py` · `NewsCollage`
- **范例**：`examples/newscollage_curiosity.py` 好奇心周刊 · 拆开看看（牛皮纸底、手撕旧报纸（程序生成的假文字栏）、被剪刀剪开并掀起上半的网点印刷闹钟照片、飞出的齿轮 / 发条 / 红色网点摆轮 / 螺丝各自剪下并配打字标签和引线、大红纸圆、勒索信拼贴字「拆开看看？」和 WHAT MAKES IT TICK、刊头、黑色邮戳、红色「附零件图」印章、美纹纸胶带）
- **耗时**：约 3 秒

## 何时选用

杂志封面、观点海报、达达 / 复古拼贴、「拆开看看 / 里面有什么」类讲解页、需要老照片质感又不能用真人照片 → 报刊拼贴（要童趣温暖的彩纸拼贴仍用剪纸拼贴）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from newscollage import NewsCollage
```

- 思路：每样东西都是「先印好、再撕或剪、最后粘上去」的一张纸 `Sheet`；老照片不是贴图，而是 `Photo` 用高度图布光渲染出来，再印成网点
- 底板：`board()` 牛皮纸（云状纸浆、深浅短纤维、树皮碎屑）
- 纸片：`sheet(w, h, 颜色)` 返回 `Sheet`，可用 `text()`、`block(…, minus=文字遮罩)` 反白字、`ink()`、`rule()`；`tear('rtb', depth, rim)` 手撕（边线游走、露出白色纸芯、飞出纤维），其余边算剪刀剪；`cut_rect()` 歪一点的剪刀四边形；`cut(pts)`；`wrinkle()` 浆糊起皱；`age()` 泛黄和霉斑
- 报纸：`newsprint(w, h, columns, size, headline, picture, ad)` 返回一整版假报纸（伪词栏、刊头线、大标题、导语、小标题、栏线、框线广告、网点小照片、背面透印），接着 `tear()`
- 老照片：在 `Photo(w, h)` 上搭物件：`disc()`、`dome(…, rot, cut)`（钟铃、球）、`ring()`（表圈）、`rod()`、`poly()`（指针）、`gear(r, teeth, spokes, pinion)`、`spiral(r0, r1, turns, flare)`（发条、游丝）、`screw()`；`text()` / `lines()` 印在表面的字和刻度；`glare()` 玻璃反光。z 是底座高度，height 是自身厚度，albedo / metal / gloss 是材质
- 印成网点：`print_photo(photo, cell, angle, ink)` 显影并印成网点，返回 Sheet；`s.cutout(margin, centre)` 沿轮廓用剪刀剪下；`s.split(p0, p1)` 一剪两半
- 粘贴：`paste(sheet, cx, cy, rot, lift)` 返回 Frame，`f.pt(lx, ly)` 把局部坐标换成画面坐标；`disc(cx, cy, r, 颜色)` 剪刀剪的色纸圆
- 字：`ransom('拆开看看', x, y, size, faces=[…], styles=[…])` 勒索信拼贴字，返回 [(Frame, 字)]；`clipping(字, size, face, paper, block, fg, extra)` 单个剪字，extra 可选 'text'（带邻字）或 'tint'（网点底）；`label(文字, x, y, size, face, fg, bg, block)` 剪下的一条印刷字
- 其他：`tape(cx, cy, 长, rot)` 美纹纸胶带；`stamp(cx, cy, [(字, 字号)], shape='box'|'round', ring=环形字)` 橡皮章；`pen(pts, dash=(实, 虚), dot)` 墨线引线
- 字体：news / news_bold / news_italic / serif_bold / slab / clarendon / didone / poster / futura / grotesk / typewriter(_bold) / cjk_song / cjk_hei / cjk_round / cjk_kai；缺字自动换中文黑体
- 颜色常量 `INK BLACK RED MUSTARD KRAFT NEWS PAPER TAPE`；rot 逆时针为正

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 齿轮像一块灰饼：齿面和背景一样亮，窗口被投影压灰，齿比网点还细 | 齿面反照率约 0.56、metal 约 0.3，加车床纹的「领结」反光；抬起高度约 8，背景投影 0.35；齿距至少约 4 个网点（r=108 用 36 齿），剪边约 9 px |
| 发条画成一圈圈同心圆，像靶子 | 圈数 4–5，`flare` 约 1.6：里圈密、外圈松，才看得出是螺旋 |
| 打字机字体没有「→」，出现豆腐块 | 逐字检查字形，缺字自动换中文黑体（已处理） |
| 问号纸片压住主体表盘的数字 | 用上一个字的 Frame 算位置，整排标题缩小；主体整体右移给标题让位 |
| 红章盖在密密的报纸字上认不出 | 章盖在牛皮纸的空处 |
| 邮戳环形小字断成「CUR:OSTI」 | 环形字至少 18 px；橡皮漏印改成部分漏墨（0.3 + 0.7 × keep），细笔画不断（已处理） |
| 剪下的照片白边处处一样宽，像模切贴纸 | 白边宽度沿周长慢慢变宽变窄（`wander` 约 0.45），但永远不剪进物体（已处理） |
| 散落的零件看不出是从闹钟里飞出来的 | 先从缺口画几条虚线弧再贴零件，起点错开别汇成尖点；离缺口最近放一颗螺丝 |
| 带邻字的报纸剪字，邻字太大太黑，抢了主字 | 邻字字号约 0.075 倍、浓度 0.62，主字周围留一圈空 |
| 报纸透印太重，镜像标题像渲染错误 | 透印浓度约 0.045，模糊 1.4 px |
| 牛皮纸纤维太长太黑，像裂纹或头发 | 纤维 4–20 px，深色浓度 0.2 |
| 动图调色板被牛皮纸和报纸占满，芥末黄纸片变成土黄 | 调色板取样时高饱和像素算 5 倍（色差 24 → 2.7 / 255） |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
