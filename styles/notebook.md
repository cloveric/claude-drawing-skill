# 实验笔记本（notebook）

- **实现**：`lib/notebook.py` · `Notebook`
- **范例**：`examples/notebook_brewing.py` 咖啡萃取实验（线圈方格笔记本、铅笔表格与折线图、排线标出最佳区间、荧光笔、没闭合的红笔圈、便利贴结论、模切贴纸、标签机日期、桌上的六棱铅笔）
- **耗时**：约 3 秒

## 何时选用

实验记录、数据对比、复盘笔记、讲解片里的「算账 / 结论」页 → 实验笔记本 · 贴纸；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from notebook import Notebook
```

- 场景：`desk()` 石墨蓝灰桌面；`notebook(x0, y0, x1, y1, tabs, stack, ear, margin, header, grid, major)` 一整本笔记本（硬封底、分隔标签、错开的页边、青色方格纸、红色双边线、打孔、折角）；`binding()` 线圈（按金属管打光，带投影）
- 铅笔：`pencil(pts, width, pressure, jitter)` 手绘一笔（样条平滑、手抖、起笔轻收笔提）；`pencils([...])`；`rule(x0, y0, x1, y1)` 靠尺直线；`hatch(mask, angle, spacing, pressure)` 排线；`checkbox(x, y, size, checked)`；`arrowhead(tip, 方向)`；`axes(x0, y0, x1, y1, xlim, ylim, xticks, yticks, xlabels, ylabels)` 返回 `to_px(x, y)`
- 石墨只挂在纸纹凸起上：pressure 小是颗粒状浅灰，大才填满；线宽约 2–3.5 px
- 荧光笔 `highlight(x0, x1, y, h, tilt, alpha)`：正片叠底，斜切起笔并积墨、边缘毛、纵向纤维条纹、尾部断续，两遍重叠处更深
- 红笔：`pen(pts, width)`、`pen_loop(cx, cy, rx, ry, rot, turns=1.12)` 不闭合的圈、`pen_arrow(pts, head)`、`pen_underline(x0, x1, y, double)`
- 文字 `text(s, x, y, size, colour, font, anchor, rot, spacing, weight, medium)`：font 用 sans / sans_bold / typewriter / cjk_sans（中英混排自动换字体），medium 可选 ink、print、typed（打字机，每字浓淡和基线略不同）、pencil、opaque；`text_width()` 量宽度
- 纸片：`sticky(cx, cy, w, h, rot, colour)` 便利贴（上端平贴、下端翘起投影），返回 Frame，用 `f.pt(lx, ly)` 和 `rot=f.rot` 往上写字；`sticker(cx, cy, w, h, rot, colour, shape='rrect'|'circle', lines=[...])` 模切贴纸；`label_tape(s, x, y, size, rot)` 标签机胶带；`stain(cx, cy, r)` 咖啡杯印
- 道具：`pencil_prop(x, y, angle, length, width, label, end='eraser'|'plain')` 六棱铅笔
- 角度：`rot` 逆时针为正（同 PIL）；`angle`（铅笔、箭头方向）是屏幕角度，顺时针为正。常用色：`INK SOFT LEAD RED HI MINT MINTD`

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 铅笔线像干净的矢量墨线：细、匀、太黑 | 手绘线宽约 3 px、抖动约 1.6；石墨只挂在纸纹凸起上，重压也保留一点颗粒 |
| 轻压的排线、表格横线断成一串点点 | 覆盖率保留约四成连续的浅灰，颗粒只调制剩下的部分（`_graphite` 已处理） |
| 折线图数据点画成小圆圈，像字母 o、c | 用压实的小铅笔点（很小的螺旋，pressure 1） |
| 曲线一笔画成，太完美 | 分两笔画，接头处稍错开、稍重叠 |
| 标注字压在曲线上，单位和刻度撞在一起 | 标注放到曲线下方空白处，用铅笔小箭头指过去；单位放到轴端上方 |
| 贴纸孤零零浮在图下面，看不出指什么 | 从最佳点画铅笔虚线到横轴，贴纸贴在同一个 x 上 |
| 标签机胶带两端剪成 V 形缺口，像彩带横幅 | 两端直剪、略斜、小圆角 |
| 咖啡渍像肥皂泡或透镜 | 外缘一圈细而深的水痕线，内部几乎均匀的淡色；圈有断口、一侧更深 |
| 红笔箭头被后贴的便利贴盖住 | 箭头停在便利贴边缘外，或先贴便利贴再画箭头 |
| 标题上的荧光笔起笔压到了前一个字 | 起点按字宽算，落在目标字的左边缘 |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
