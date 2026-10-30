# 黄金时代漫画（comic）

- **实现**：`lib/comic.py` · `ComicCover`
- **范例**：`examples/comic_rocket.py` 火箭小队 No. 3（1940 年前后的报摊漫画封面：朝灭点挤出的立体刊名 ROCKET SQUAD、价格框和黄色旁白框；暮色天空分档网点、大月亮；红色火箭起飞，June 舰长指着月亮喊「NEXT STOP -- THE MOON!」，后座小狗 Pip 戴着护目镜；没赶上的机修工 Sparky 吊在绳梯上喊「HEY!! WAIT FOR ME!!」；拟声字 WHOOOSH!；毛笔墨线与羽状排线、Ben-Day 网点、三色版错位、泛黄新闻纸、书脊裂纹和生锈订书钉）
- **耗时**：约 5 秒
- **内部构成**：黄金时代漫画（毛笔墨线、Ben-Day 网点、四色错版、新闻纸）

## 何时选用

复古漫画、冒险故事的「出发 / 登场 / 大事件」、怀旧玩具与少儿读物感、讲解片的「故事开场 / 角色介绍」封面、需要对白框和拟声字的画面 → 黄金时代漫画（要现代日漫用日本动漫，要拟人小物件的轻松图解用卡通手绘，要红黑两色木刻海报用凸版印刷海报）；

## 接口速查

```python
import sys; sys.path.insert(0, "<本skill>/lib")
from core import spline, curve, blob_pts, fbm1d, blur, polygon_mask  # 公共工具，按需取用
from comic import ComicCover
```

- 思路：先按当年的分工把封面「做」出来，再按当年的印法「印」出来。墨线师在黑版上勾 key 线；上色师在色稿上给每块区域指定三原色的 Ben-Day 网点比例（0 / 20 / 40 / 70 / 100%），整张封面只有几十种颜色；印刷时每版按自己的角度加网、各自错开几像素，新闻纸吸墨让网点变毛、小点丢失、实地发花；油墨透明相乘。网点和错版都不手画
- 构造：`ComicCover(W, H, seed, screen=11, misreg=4, slop=1.6, light=(-0.6, -0.8))`：screen 是网点间距（px），misreg 是各色版的错位量，slop 是手绘分色的游走量；`register(plate, dx, dy, rot)` 手动指定某版的落点
- 纸：`paper(colour, tone, fibres, flecks)` 泛黄新闻纸（云状纸浆、深浅短纤维、树皮屑、不吃墨的纸坑）
- 形状（整页抗锯齿遮罩，可加减乘）：`mask(pts, smooth)`、`circle()`；静态方法 `ellipse_pts()`、`smooth()`（闭合样条）、`tube_pts(路径, 宽度列表)`（四肢、绳子、围巾、耳朵）、`burst_pts()`（星星、爆炸框）、`edge_normals(pts)`（轮廓点和外法线，给 `feather` 用）；`grow()` / `shrink()`
- 色稿：`flat(shape, 颜色)`，颜色是 (蓝, 红, 黄, 黑) 四个网点比例；`graded(shape, [颜色…], p0, p1, edges=[…])` 沿手裁波浪边分档的色带；`rings()` 同心色环；`knock()` 挖白
- 黑版：`part(pts, 颜色, width, heavy)` 是放前景物件的标准做法：擦掉身后的墨线和颜色、铺色、勾一圈背光侧加粗的轮廓；`brush(pts, width, taper, swell)` 两头尖、中段鼓的毛笔线；`pen()` 细笔；`outline()` / `edge()` 闭合 / 开放轮廓；`ink()` 实黑块；`erase()`；`mask_outline(mask, width, heavy)` 给任意遮罩（圆的并集、字）描边；`feather(P, N, length, width, spacing, clip, along, toward, curl)` 从阴影边长出来的羽状排线；`hatch()` 平行排线；`speed()` 速度线；`dot()`
- 字：`letter(text, x, y, size, face, colour)` 手写字，逐字微转、微跳（face：letter 漫画手写体 / logo 窄粗体 / bold / slab / heavy）；`text_mask()`；`balloon(text, x, y, size, tail, kind='speech'|'yell'|'thought')` 对白框 / 喊叫爆炸框 / 想法云；`caption(x0, y0, x1, y1, text, colour)` 旁白框；`sfx(text, x, y, size, colour, rot, shade)` 拟声字；`logo(text, quad, vp, depth, colours, shade, shadow, glints)` 透视立体刊名：四个角点定透视，朝灭点挤出 depth 像素，正面上浅下深分档，加挤出面、投影、粗黑外框和高光斜纹
- 做旧（印完以后再加，只作用在各自区域）：`brown_edges()` 边缘泛黄；`spine(ticks, staples)` 书脊折痕、白色应力裂纹、两枚生锈订书钉；`corner('br', radius)` 角上磨掉油墨、折角；`crease(p0, p1)` 折痕处油墨裂开露白；`foxing(n)` 霉斑
- 阶段：`stage(name, plates='CMYK')` 记下当时的各版，出图时只印列出的版：先用 'K' 出黑版线稿，再依次 'YK'、'YMK'、'CMYK'，就是印刷厂的「渐进打样」
- 颜色常量（色稿比例）：`WHITE CREAM PALE YELLOW GOLD ORANGE DEEP_ORANGE RED CRIMSON PINK SKIN TAN BROWN DARK_BROWN SKY LIGHT_BLUE BLUE NAVY VIOLET MAUVE LILAC GREEN LIME GREY LIGHT_GREY SILVER`；油墨颜色 `INK`；`save('x.jpg')` 默认 quality 88、4:4:4 色度

## 毛病清单（都真实出现过）

| 问题 | 改法 |
|---|---|
| 羽状排线像一排梳齿、像尺子刻度：等长、等距、完全平行 | 长度跟着两层慢噪声起伏（0.25–1.15 倍），间距 ±30%，每根略弯、偏离平行约 4°；起笔压在阴影边上，越往亮处越短 |
| 羽状排线穿过白色色环上的字，RS-1 被看成 RS-T | 排线的 clip 去掉文字所在的区域 |
| C40 M70 Y100 的棕色（头盔、山体暗面）在 11 px 粗网下花成发绿的斑 | 棕色不用蓝版：M70 Y100 + 黑 40% / 70%（`BROWN` / `DARK_BROWN`） |
| 天空七条等宽色带像一面旗；中间几档两版都挂网，花点太闹，压住人物 | 色带用 `edges=` 指定不等宽；过渡档尽量只挂一个版（蓝 40%、蓝 20%、黄 40%），两版叠网只留在顶部一两档 |
| 月亮光晕的同心色环盖过所有色带，在橙色带里切出一个蓝色圆盘 | 去掉光晕；`rings()` 只用在单一色带里 |
| 顺风飘的围巾正好盖住后座小狗的头，小狗只剩一团白 | 围巾往后上方飘（漫画夸张），小狗后移；先画后座再画前座；狗脸用纯白（不挂网）配黑耳、黑鼻、金色护目镜 |
| 护目镜比脸还大，像第二个头；挡风玻璃像两颗牙、像多出来的尾翼 | 护目镜只露一只镜片推在额头上；去掉挡风玻璃，只留座舱口沿 |
| 座舱里的人画在船体之后，下半身露在船体外面 | 先画人，再画船体：`part` 会擦掉被挡住的墨线和颜色，最后补座舱口沿 |
| 尾喷管是一块挂网灰方盒；火焰外层深橙和橙色天空同色，又被下尾翼和烟挡掉 | 喷管涂黑加银色口沿；火焰由外到内红、深橙、橙、黄、白五层，烟只吞掉火焰末端，下尾翼缩小，去掉横穿舷窗的中间尾翼 |
| 烟团是锯齿星形、挂橙色网，像一堆石头 | 烟团用近圆形加轻微起伏，白底；只在右下月牙挂黑 20%，靠火焰的一侧挂黄 40% |
| 右边台地看不出是悬崖：斜面、羽线、暗面混成一团，暗面花成墨绿 | 平顶加竖直崖壁：崖顶下一道黑影，裂缝从黑影往下用 `feather(along=(0, 1))`；崖脚另起一道碎石坡，换一种颜色 |
| 地平线正好穿过 Sparky 的头；他在画面里太小，故事的笑点看不见 | 地平线下移到胸口；人物放大 1.15 倍，飞走的帽子挪开、别压在手上 |
| 动图超过 2 MB（2.34 MB），网点缩小后成了摩尔纹 | 缩到 720 宽时用 BOX 不用 LANCZOS：1.79 MB，网点仍隐约可见 |
| 内存峰值 1.25 GB | 网点阈值图等缓存改成 float16；印刷按 180 行一带处理；刊名只在自己的裁切区里算；做旧效果只作用在各自区域：峰值约 0.85 GB |

---

通用流程、全局约束与动画规格见 `SKILL.md` 和 `references/animation.md`。
