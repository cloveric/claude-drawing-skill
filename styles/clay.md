# 黏土定格（clay）

- **实现**：`lib/clay.py` · `Clay`
- **范例**：`examples/clay_lighthouse.py` 灯塔岛（手指抹开的天空、条纹灯塔、喷水的鲸鱼、搓条浪花、小帆船）
- **耗时**：约 6 秒

## 何时选用

童趣立体、讲故事、手作感、定格动画 → 黏土定格；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from clay import Clay
```

- 同时维护高度图（像素为单位）和颜色图，最后用影棚光一次性打光。部件默认「铺」在下面的东西上（`base=None`），先远后近、后铺的在上
- `backdrop(颜色)` 底板；`gradient(top, bottom, y0, y1)` 生成颜色场，可传给 `pad`/`smear`
- 部件：`pad(mask, 颜色, height, round)` 压平的一片（round 小是硬边薄片，大是鼓鼓的枕头形）、`ball(x, y, r)` 小球、`snake(pts, r, taper=(起, 止))` 搓条（线条、浪花、嘴、茎）、`text(s, x, y, size)` 鼓起的黏土字
- 工具痕：`groove(pts, width, depth)` 刻线、`poke(x, y, r, depth)` 戳洞；`smear(mask, 颜色场)` 手指抹开的一大片（会把相邻颜色拖混，留下柔和的指痕脊）
- `marble=('#颜色', 0.25)` 两色没揉匀的纹路；表面自动带小疙瘩和指纹
- 遮罩：`circle()`、`ellipse()`、`poly()`、`blob()`、`rrect()`

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 手指抹开的天空像揉皱的锡纸 | 指痕要宽（40–70 像素）、数量适中（200–350 笔）、脊线柔和低矮（`smear` 的 height 约 4）；先铺几种颜色再抹，拖色才看得出来 |
| 天空里出现笔直的矩形色块边 | 不可平铺的噪声不能取模循环平移，要在噪声图内部取窗口（已修） |
| 预先铺的色块边缘太硬，抹完还是一块一块 | 色块之间用 smoothstep 柔和过渡，再用手指抹 |
| 浪花像一排排一模一样的墙纸花纹 | 每朵浪的长短、高低、间距都随机；只排两三行，近大远小 |
| 鲸鱼像一条面包，尾鳍像两根分开的香肠 | 头要圆、身体向后收窄入水；尾鳍用一整片带中间缺口的翼形轮廓 |
| 前景水面在藏在下面的尾柄处鼓起一个包 | 部件默认顺着下面的高度铺；被遮住的部分别伸进水面太深，或在水线处用泡沫盖住 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
