# 蓝晒（cyanotype）

- **实现**：`lib/cyanotype.py` · `Cyanotype`
- **范例**：`examples/cyanotype_botanicals.py` 蓝晒植物（蕨叶、银杏、蒲公英、飘散的种子、白色手写标注）
- **耗时**：约 6 秒

## 何时选用

植物、标本、自然科学、复古工艺感的蓝色海报 → 蓝晒；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from cyanotype import Cyanotype
```

- 思路是「挡紫外线」而不是「上颜料」：放上去的东西按不透明度挡光，透过率相乘；最后显影成普鲁士蓝
- `coat(x0, y0, x1, y1)` 刷涂药水：一笔笔横刷，笔尾是干刷的断续刷丝，边上会甩几滴药水
- `place(mask, opacity, lift, texture)`：opacity 薄叶约 0.85、叶脉 1.0、绒毛约 0.3；lift 是离纸的高度（0 压平清晰，1–3 柔和半影）；texture 是叶肉的不均匀
- 批量画遮罩：`shapes([轮廓...])` 一次画很多片叶子，`lines([折线...], width, taper)` 一次画很多茎、叶脉、绒毛；`Cyanotype.leaf_pts(x, y, 角度, 长, 宽, tip, blunt)` 叶片轮廓
- 文字：`label()` 白色手写字（写在透明片上一起晒）、`pencil()` 晒完后写在纸边的铅笔字

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 蕨叶像一串箭头或锯齿（鱼骨状） | 每片羽片做成一整片带圆齿边的叶片，加淡色小叶脉；不要一颗颗分开的小叶 |
| 小叶改成椭圆后又像含羞草 | 同上，蕨类的羽片是连在一起的 |
| 蒲公英绒毛几乎看不见 | 细丝不透明度约 0.3、lift 约 1；抬得太高会被半影模糊掉 |
| 刷涂边缘像毛刺、撕纸或动态模糊 | 按一笔笔横刷建模：每根刷毛在自己的位置干净利落地停住，干刷的断续用横向拉长的噪声（已修） |
| 茎穿过白色题字 | 题字放在留白处，茎的走向给题字让路 |
| 飘散的种子被涂布边缘裁掉，只剩一根线 | 小物件要完整落在涂布区域以内 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
