# 贴纸拼贴·小票（sticker）

- **实现**：`lib/sticker.py` · `Sticker`
- **范例**：`examples/sticker_market.py` 周末市集（热敏小票、模切贴纸：酸种面包/传家番茄/郁金香花束/咖啡豆、贴纸大字、波浪边促销贴、麻绳吊牌、和纸胶带、「已付」橡皮章）
- **耗时**：约 3 秒

## 何时选用

清单、账单、价格、购物、市集、活动海报、轻松但成熟的讲解片封面 → 贴纸拼贴 · 小票；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from sticker import Sticker
```

- 思路：每样东西先在自己的透明小画纸 `Art` 上画成平面矢量图，再决定材质：`stick()` 做成模切贴纸，`lay()` 当纸平放
- `board(颜色, kind='cream'|'kraft')`：奶油色或浅牛皮纸底板，带纸纹、斑驳、纤维和杂点
- `art(w, h)` 返回 `Art`：遮罩 `circle/ring/ellipse/rrect/poly/blob/line/text`（中西文混排，`stroke` 加粗）；上色 `fill(mask, 颜色, alpha, clip)`、`gradient()`、`radial()`；`crescent(mask, dx, dy)` 明暗月牙；`speckle()` 撒面粉、籽粒；`cut()` 打孔；`texture('kraft')` 牛皮纸纹
- `stick(art, cx, cy, rot, border=14, peel='tr'|'tl'|'br'|'bl', peel_size, lift, gloss)`：模切贴纸。白边按圆角外扩，有切口厚度、覆膜高光和斜向反光，贴地阴影加柔和投影；`peel` 翻起一角，露出浅色背面和它自己的影子
- `lay(art, cx, cy, rot, curl, lift)`：纸张平放（小票、吊牌），两端微翘、翘起处影子更长；返回局部→画面坐标映射 `T(x, y)`，用来在纸上落笔、盖章
- `receipt(w, h)` 返回 `Receipt`：锯齿撕边、热敏灰字（断针竖纹、走纸浓淡、小掉点）；`centre()` 居中打印、`row(y, 名称, 金额, was='旧价')` 带点线引导和删除线、`rule('dash'|'stars'|'double')`、`barcode()`、`crease(y)` 折痕
- `tape(cx, cy, 长, rot, 颜色, pattern='stripe'|'dot'|'grid'|'plain')` 半透明和纸胶带，两头手撕锯齿；`tag_art(w, h, 颜色, 金属扣颜色)` 吊牌（`.hole` 是孔位），`twine(点列)` 双色面包师麻绳
- `stamp(cx, cy, r, 环形字, 中心字, 小字, 颜色, rot)` 圆形橡皮章（油墨半透明、压力不匀、字边积墨、漏印小坑）；`pen(点列, 颜色, width)` 红色圆珠笔（打勾、圈总价、划掉）
- 现成贴纸：`lettering_art([(文字, 颜色), ...], size)` 大字、`label_art()` 胶囊标签、`badge_art(r, 颜色, '-20%', top, bottom)` 波浪边促销贴

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 面包只有一道长割口，像红薯或叶脉 | 三道斜向交叠的割口：浅色裂口加深色翘边，再撒面粉 |
| 花束的花用同心圆画，像靶心或棒棒糖 | 侧面郁金香：两片带尖的外瓣，前面一片浅色瓣 |
| 印章小字压在内圈线上 | 中心字上移，分隔线放在 +0.16r，小字写短，全部收在内圈以内 |
| 小票字太黑，像打字机不像热敏纸 | 灰色油墨 #4f525a、浓度约 0.8、边缘微糊，加断针竖纹和走纸浓淡 |
| 小票右半边整条发灰 | 横向卷曲压到很小，只让长边两端翘起 |
| 纸边的贴地阴影像描了一圈黑线 | 纸张接触阴影降到约 0.26 |
| 印章盖在条码上看不清 | 盖在金额和星号一带的稀疏处，只压一点字，更像真的 |
| 印章墨色太匀，像电脑填色 | 加压力倾斜、大块浓淡和漏印小坑 |
| 标签上的字溢出圆标 | 文字改短、字号调小 |
| 右下角空出一大块 | 加摊位号圆贴纸，第二个吊牌用长绳垂下来 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
