"""Example (chalkboard): 为什么天空是蓝的 · Why is the sky blue? — a physics lesson on a classroom chalkboard: the
title with 蓝 written in blue chalk, a diagram (the sun's white light entering the atmosphere, an air molecule
sending short blue waves off in every direction while the long red wave carries straight on, an eye on the ground
seeing blue), Rayleigh's law 散射 ∝ 1/λ⁴ with the key term looped, a worked comparison of blue and red, a small
spectrum bar with the 1/λ⁴ curve drawn over it, a boxed 小结, and a question for next time. Behind it all, the
half-erased ghosts of the previous lesson (a prism and Snell's law), eraser swipes and chalk dust; a wooden frame
and a ledge with chalk and a felt eraser. No image model.
python3 chalk_lesson.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from chalk import Chalkboard, WHITE, YELLOW, PINK, BLUE, RED, ORANGE, GREEN, VIOLET
from core import polygon_mask

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'chalk_lesson.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

cb = Chalkboard(1920, 1080, seed=11)
W, H = cb.W, cb.H

# ---- the board as the class found it: last lesson's prism, wiped off but not washed; eraser swipes; dust
cb.slate()
with cb.erased(keep=0.34, angle=2):
    cb.text('光的色散 Dispersion', 1296, 250, 46)
    cb.stroke([(1000, 322), (1060, 212), (1120, 322), (1000, 322)], smooth=False, width=4)
    cb.line(930, 300, 1036, 272)
    for k, c in enumerate((RED, ORANGE, YELLOW, GREEN, BLUE, VIOLET)):
        cb.line(1092, 272 + k * 3, 1236, 268 + k * 15, c, width=3.6)
    cb.text('棱镜', 1138, 226, 36)
with cb.erased(keep=0.3, angle=-3):
    cb.text('n₁ sin θ₁ = n₂ sin θ₂', 44, 700, 36)
    cb.text('作业  P.42  第 1–6 题', 1060, 64, 36)
with cb.erased(keep=0.26, angle=4):
    cb.text('v = λ f', 60, 782, 48)
    cb.text('c = 3 × 10⁸ m/s', 936, 1002, 36)
    cb.text('红 橙 黄 绿 蓝 靛 紫', 560, 300, 36)
for pts, w, st in [([(40, 330), (700, 300), (1300, 322), (1880, 290)], 150, 0.5),
                   ([(40, 560), (800, 540), (1880, 590)], 140, 0.45),
                   ([(60, 790), (900, 810), (1880, 760)], 150, 0.5),
                   ([(1160, 140), (1500, 160), (1880, 130)], 110, 0.6)]:
    cb.swipe(pts, w, st, haze=0.05)
cb.smudge(1640, 860, 220, 90, rot=12, strength=0.5)
cb.smudge(300, 640, 180, 80, rot=-8, strength=0.5)
cb.dust()
cb.stage('slate')

# ---- frame, ledge, chalk and the eraser
cb.frame()
TY = cb.tray_y
cb.crumbs(160, 1820, 16)
cb.chalk_stick(262, TY, 94, WHITE, rot=-1.2)
cb.chalk_stick(372, TY, 58, YELLOW, rot=1.6, worn='left')
cb.chalk_stick(462, TY, 78, PINK, rot=-0.5)
cb.chalk_stick(545, TY, 34, BLUE, rot=4, worn=None)
cb.eraser(1670, TY + 2)
cb.stage('frame')

# ---- title
x = 104
for seg, col in [('为什么天空是', WHITE), ('蓝', BLUE), ('的？', WHITE)]:
    cb.text(seg, x, 164, 90, col)
    x += cb.text_width(seg, 90)
cb.text('Why is the sky blue?', 938, 160, 42, BLUE)
cb.underline(106, 858, 192, YELLOW, width=5.5, double=True)
cb.text('9月30日  星期三', 1846, 94, 32, WHITE, anchor='rs', pressure=0.9)
cb.text('物理 · 光学', 1770, 158, 28, PINK, anchor='ms')
cb.box(1690, 124, 1850, 174, PINK, width=3.0, pressure=0.8)
cb.stage('title')

# ---- the sun and its white light
SX, SY, SR = 196, 432, 58
yy, xx = np.mgrid[0:H, 0:W]
cb.shade(((xx - SX) ** 2 + (yy - SY) ** 2 < (SR - 4) ** 2).astype(np.float32), YELLOW, angle=12, stick=30, pressure=0.5)
cb.circle(SX, SY, SR, YELLOW, width=4.4)
rays = []
for k in range(12):
    a = np.deg2rad(k * 30 + 8)
    r0, r1 = SR + 14, SR + (38 if k % 2 == 0 else 26)
    rays.append([(SX + np.cos(a) * r0, SY + np.sin(a) * r0), (SX + np.cos(a) * r1, SY + np.sin(a) * r1)])
cb.strokes(rays, YELLOW, 4.2, 0.85, 0.3, smooth=False)
cb.text('太阳', SX, 562, 32, YELLOW, anchor='ms')
cb.text('Sun', SX, 596, 24, WHITE, anchor='ms', pressure=0.8)
cb.arrow([(300, 452), (470, 460), (628, 470)], WHITE, width=5.0, head=20)
cb.text('白光（七色混合）', 318, 432, 26, WHITE, pressure=0.85)
cb.stage('sun')

# ---- the atmosphere over the curved ground; air molecules
GX, RG = 820, 2600.0                                                    # Earth: centre far below, radius RG
ground = lambda x: 716 + RG - np.sqrt(RG ** 2 - (x - GX) ** 2)
top = lambda x: 716 - 372 + (RG + 372) - np.sqrt((RG + 372) ** 2 - (x - GX) ** 2)
xs = np.linspace(440, 1210, 40)
air = polygon_mask(H, W, [(x, top(x) + 10) for x in xs] + [(x, ground(x) - 8) for x in xs[::-1]], 2)
thick = (0.25 + 0.75 * np.clip((yy - 380) / 330.0, 0, 1) ** 1.4) * np.clip((xx - 436) / 190, 0, 1) ** 1.5 * np.clip((1214 - xx) / 120, 0, 1) ** 1.5
cb.shade(air, BLUE, angle=3, stick=44, pressure=0.34, overlap=0.1, strength=0.62, weight=thick)   # denser air near the ground
cb.stroke([(x, ground(x)) for x in np.linspace(430, 1216, 9)], WHITE, 4.6, 0.9)
cb.strokes([[(x, ground(x) + 4), (x - 13, ground(x) + 21)] for x in np.arange(452, 1212, 17)], WHITE, 2.6, 0.62, 0.2, smooth=False)
cb.dashed([(x, top(x)) for x in np.linspace(436, 1214, 9)], WHITE, 20, 13, 3.4, 0.78)
cb.text('大气层', 1070, top(1070) + 46, 28, WHITE, pressure=0.9)
cb.text('atmosphere', 1070, top(1070) + 74, 22, BLUE, pressure=0.85)
MOL = [(548, 392), (498, 548), (724, 636), (884, 436), (1016, 608), (1150, 630), (792, 688)]
for mx, my in MOL:
    cb.circle(mx, my, 7.5, WHITE, width=3.0, pressure=0.8)
MX, MY = 646, 474
cb.circle(MX, MY, 11, WHITE, width=3.6)
cb.dot(MX, MY, 4.2)
cb.circle(466, 694, 7.5, WHITE, width=3.0, pressure=0.8)
cb.text('= 空气分子 N₂, O₂', 482, 703, 25, WHITE, pressure=0.9)
cb.stage('atmosphere')

# ---- the waves: long red carries straight on, short blue scatters every way; the eye on the ground
cb.wave((666, 476), (1196, 500), 58, 12, RED, width=4.4, head=18)
cb.text('红光 λ 长 → 几乎直穿', 944, 552, 26, RED)
for p1 in [(604, 382), (770, 386), (530, 618), (846, 640)]:
    cb.wave((MX + (p1[0] - MX) * 0.1, MY + (p1[1] - MY) * 0.1), p1, 17, 6.5, BLUE, width=3.8, head=14)
cb.text('蓝光 λ 短 → 四处散射', 784, 394, 26, BLUE)
EX, EY = 904, 668                                                       # the eye, looking up to the left
cb.stroke([(EX - 58, EY + 3), (EX - 22, EY - 26), (EX + 26, EY - 24), (EX + 58, EY + 1)], WHITE, 4.2, 0.92)
cb.stroke([(EX - 58, EY + 3), (EX - 16, EY + 24), (EX + 28, EY + 20), (EX + 58, EY + 1)], WHITE, 3.8, 0.88)
ring = (((xx - (EX - 8)) ** 2 + (yy - (EY - 3)) ** 2 < 17 ** 2) & ((xx - (EX - 10)) ** 2 + (yy - (EY - 5)) ** 2 > 7 ** 2)).astype(np.float32)
cb.shade(ring, BLUE, angle=35, stick=20, pressure=0.8, overlap=0.2, ragged=0.4)
cb.circle(EX - 8, EY - 3, 17, BLUE, width=3.2)
cb.dot(EX - 14, EY - 10, 3.0, WHITE)
lash = [[(EX + dx, EY + dy), (EX + dx * 1.18, EY + dy - 13)] for dx, dy in ((-40, -16), (-20, -24), (2, -26), (24, -23))]
cb.strokes(lash, WHITE, 2.8, 0.8, 0.2, smooth=False)
cb.text('眼睛：满天都是蓝光', 978, 700, 25, WHITE, pressure=0.92)
cb.stage('waves')

# ---- Rayleigh's law
cb.line(1252, 262, 1256, 800, WHITE, width=2.6, pressure=0.45)
cb.text('瑞利散射', 1296, 312, 44, YELLOW)
cb.text('Rayleigh scattering', 1296 + cb.text_width('瑞利散射', 44) + 18, 310, 26, BLUE)
cb.text('散射', 1300, 448, 76)
pw = cb.propto(1300 + cb.text_width('散射', 76) + 22, 448, 76)
FX = 1300 + cb.text_width('散射', 76) + 22 + pw + 72
cb.text('1', FX, 410, 58, anchor='ms')
cb.rule(FX - 50, 428, FX + 54, 430, WHITE, width=4.6, pressure=0.9)
cb.text('λ', FX - 10, 500, 62, anchor='ms')
cb.text('4', FX + 22, 472, 36, anchor='ms')
cb.stage('formula')

# ---- the key point, looped; a worked comparison
cb.loop(FX + 2, 452, 84, 76, YELLOW, width=4.6, rot=-4)
cb.arrow([(FX + 88, 488), (FX + 112, 506), (FX + 132, 510)], YELLOW, width=3.8, head=13)
cb.text('波长越短', FX + 140, 500, 26, YELLOW)
cb.text('散得越多', FX + 140, 532, 26, YELLOW)
cb.text('蓝 450 nm  vs  红 700 nm', 1300, 590, 28, WHITE, pressure=0.9)
cb.text('(700 ÷ 450)⁴ ≈ 5.9', 1300, 646, 36, WHITE)
cb.text('蓝光多散射约 6 倍', 1636, 644, 26, BLUE)
cb.stage('key')

# ---- spectrum bar with the 1/λ⁴ curve over it
BX0, BX1, BY0, BY1 = 1322, 1800, 892, 930
px_of = lambda l: BX0 + (l - 400) / 300 * (BX1 - BX0)
cols = [(400, 435, VIOLET), (435, 485, BLUE), (485, 520, '#a6e3dc'), (520, 565, GREEN), (565, 590, YELLOW), (590, 625, ORANGE), (625, 700, RED)]
for l0, l1, c in cols:
    m = polygon_mask(H, W, [(px_of(l0) - 5, BY0), (px_of(l1) + 5, BY0), (px_of(l1) + 5, BY1), (px_of(l0) - 5, BY1)], 1)
    cb.shade(m, c, angle=0, stick=42, pressure=0.95, overlap=0.0, overshoot=3, ragged=0.5, strength=1.0)
cb.rule(BX0 - 16, 878, BX0 - 16, 700, WHITE, width=3.2, pressure=0.8)
cb.arrow([(BX0 - 16, 706), (BX0 - 16, 682)], WHITE, width=3.2, head=12)
cb.text('散射强度', BX0 + 2, 704, 22, WHITE, pressure=0.85)
ls = np.linspace(400, 700, 30)
cb.stroke([(px_of(l), 878 - 164 * (400 / l) ** 4) for l in ls], WHITE, 4.0, 0.9)
for l, c, s in ((450, BLUE, '蓝'), (700, RED, '红')):
    cb.dot(px_of(l), 878 - 164 * (400 / l) ** 4, 8.0, c)
    cb.text(s, px_of(l) + (12 if l < 700 else -2), 878 - 164 * (400 / l) ** 4 - 16, 24, c, anchor='ls' if l < 700 else 'rs')
cb.strokes([[(px_of(l), BY1 + 3), (px_of(l), BY1 + 17)] for l in (400, 500, 600, 700)], WHITE, 3.2, 0.95, 0.1, smooth=False)
for l in (400, 500, 600, 700):
    cb.text(str(l), px_of(l), BY1 + 40, 22, WHITE, anchor='ms', pressure=0.9)
cb.text('λ / nm', BX1 + 16, BY1 - 10, 20, WHITE, pressure=0.9)
cb.stage('spectrum')

# ---- 小结 box and a question for next time
cb.box(92, 806, 880, 994, WHITE, width=3.8, gap=(128, 232))
cb.text('小结', 180, 818, 36, YELLOW, anchor='ms')
for i, s in enumerate(['① 阳光是七色光的混合（白光）', '② 空气分子散射短波长光最强：散射 ∝ 1/λ⁴',
                       '③ 蓝光被散向四面八方 → 满天都是蓝色']):
    cb.text(s, 124, 872 + i * 50, 29, WHITE)
cb.text('想一想：', 930, 874, 30, PINK)
cb.text('夕阳为什么是红的？', 930, 924, 30, PINK)
cb.underline(930, 1196, 940, PINK, width=3.4, sag=1.5)

cb.save(out, stages_dir=stages)
print('saved', out)
