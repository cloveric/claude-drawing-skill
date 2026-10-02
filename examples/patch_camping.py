"""Example (embroidered patches / 刺绣徽章): 三晚露营 · Three Nights Out — the back of a denim jacket that keeps a
camping trip: one patch per night, joined by a sashiko trail. Night 1, a die-cut arch with a hot-cut satin border:
a tent with its lantern lit on a lake shore at sunset. Night 2, a round merrowed badge: high camp, a campfire under
a two-tone peak with snowcaps, moon and stars, lettering on the ring. Night 3, the way home: a compass rose on cream
twill, still being sewn on -- whip stitches have gone two-thirds of the way round and the needle lies on the denim
with the thread running back to the last stitch. A curved rocker over the middle badge reads THREE NIGHTS OUT; a
felled yoke seam with double topstitching runs across the top.
Draw-on stages: denim -> blanks -> background fills -> scenery -> satin -> details -> lettering -> edges -> trail
-> sewing. No image model.
python3 patch_camping.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from patch import Patch

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'patch_camping.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

CREAM, GOLD, NAVY = '#f1e5c6', '#d89c33', '#24325a'
K = 1.14                                         # the patches are drawn in design units around (960, 660)


def T(*pts):
    """design units -> canvas pixels"""
    return [((x - 960) * K + 960, (y - 660) * K + 612) for x, y in pts]


def P1(x, y):
    return T((x, y))[0]


p = Patch(1920, 1080, seed=7)

# ---- 0. the denim: a jacket back with a felled yoke seam
p.denim()
p.seam([(-30, 132), (480, 146), (960, 158), (1440, 146), (1950, 132)])
p.stage('denim')

# ---- 1. the cut blanks
AX, AY = P1(960, 660); AR = 238 * K               # night 2: round badge
BX, BTOP = P1(430, 455); BW, BH = 330 * K, 400 * K   # night 1: die-cut arch
CX, CY = P1(1500, 612); CR = 172 * K              # night 3: compass, being sewn on
rocker = p.blank(p.rocker_pts(AX, AY, 266 * K, 334 * K, span=98), '#a8322a')
bA = p.blank(p.circle_pts(AX, AY, AR), '#1a2346')
bB = p.blank(p.arch_pts(BX, BTOP, BW, BH, corner=34), '#2e3a6e')
bC = p.blank(p.circle_pts(CX, CY, CR), '#ece2c9')
p.stage('blanks')

# ---- 2. background fills (tatami)
p.fill(rocker.mask, '#ad3328', angle=8)
p.fill(bA.mask, '#1a2346', angle=32)
scene = p.circle(AX, AY, 176 * K)
p.fill(scene * p.poly(T((760, 470), (1160, 470), (1160, 640), (1060, 628), (960, 642), (860, 630), (760, 645))),
       '#22336a', angle=-24)
p.fill(scene * p.poly(T((760, 645), (860, 630), (960, 642), (1060, 628), (1160, 640), (1160, 860), (760, 860))),
       '#34508a', angle=-24)
archm = bB.mask
bands = [('#2e3a6e', 455, 585), ('#7b4a86', 585, 640), ('#d0566a', 640, 680), ('#f08a48', 680, 712)]
edges = {585: [(250, 590), (330, 580), (430, 592), (530, 578), (610, 588)],
         640: [(250, 636), (340, 646), (440, 634), (540, 646), (610, 638)],
         680: [(250, 682), (350, 676), (450, 684), (550, 676), (610, 682)]}
for col, ya, yb in bands:
    top = edges.get(ya, [(250, ya), (610, ya)])
    bot = edges.get(yb, [(250, yb), (610, yb)])
    p.fill(archm * p.poly(T(*top, *bot[::-1])), col, angle=0, length=14)
p.stage('fills')

# ---- 3. scenery: hills, lake, shore (night 1); peaks, ground (night 2)
p.fill(archm * p.circle(*P1(470, 712), 44 * K) * p.poly(T((400, 640), (540, 640), (540, 712), (400, 712))), '#f7c84a',
       angle=90, kind='satin', maxlen=40)
hills = [(250, 712), (250, 690), (290, 682), (330, 694), (380, 678), (430, 690), (520, 676), (570, 690), (610, 684), (610, 712)]
p.fill(archm * p.poly(T(*hills)), '#30574a', angle=15, length=12)
p.fill(archm * p.poly(T((250, 710), (610, 710), (610, 790), (250, 790))), '#3b74a8', angle=0, length=16)
shore = [(250, 790), (330, 784), (420, 792), (520, 780), (610, 786), (610, 860), (250, 860)]
p.fill(archm * p.poly(T(*shore)), '#557c3a', angle=12, length=13)

# night 2: a far ridge, the back peak, the main peak (lit side / shade side), the ground
p.fill(scene * p.poly(T((760, 800), (760, 700), (800, 690), (830, 712), (1080, 700), (1120, 676), (1160, 690), (1160, 800))),
       '#2b3f6e', angle=20, length=12)
p.fill(scene * p.poly(T((790, 800), (872, 612), (912, 690), (900, 800))), '#7d93ba', angle=62)
p.fill(scene * p.poly(T((872, 612), (912, 690), (972, 760), (960, 800), (900, 800), (905, 700), (884, 650))),
       '#4a5e88', angle=-60)
lit = [(842, 800), (925, 650), (944, 662), (985, 548), (994, 606), (976, 662), (1003, 724), (990, 800)]
shade = [(985, 548), (1046, 640), (1062, 630), (1130, 800), (990, 800), (1003, 724), (976, 662), (994, 606)]
p.fill(scene * p.poly(T(*lit)), '#9fb4d4', angle=60)
p.fill(scene * p.poly(T(*shade)), '#4b6089', angle=-55)
ground = [(760, 800), (820, 786), (900, 795), (960, 788), (1020, 796), (1100, 784), (1160, 794), (1160, 860), (760, 860)]
p.fill(scene * p.poly(T(*ground)), '#26472e', angle=10, length=13)
p.stage('scenery')

# ---- 4. satin: snowcaps, tent, sun glints, campfire, moon, compass rose
p.fill(scene * p.poly(T((985, 548), (994, 606), (984, 598), (976, 612), (966, 600), (957, 606), (964, 585))), '#f6f3ec',
       angle=-58, kind='satin')
p.fill(scene * p.poly(T((985, 548), (1018, 597), (1006, 592), (996, 604), (994, 606))), '#aebbd3', angle=58, kind='satin')
p.fill(scene * p.poly(T((925, 650), (944, 662), (930, 664), (921, 676), (912, 668))), '#e9edf3', angle=-60, kind='satin')
p.fill(scene * p.poly(T((872, 612), (888, 642), (879, 638), (872, 650), (864, 640), (858, 645))), '#e9edf3', angle=-62, kind='satin')
# the tent: front panel lit, side panel in shade, the door glowing from the lantern inside
p.fill(archm * p.poly(T((352, 702), (300, 800), (404, 800))), '#ec7a30', angle=-28, kind='satin')
p.fill(archm * p.poly(T((352, 702), (404, 800), (470, 792), (418, 700))), '#a9441f', angle=30, kind='satin')
p.fill(archm * p.poly(T((352, 734), (333, 800), (371, 800))), '#f8c24a', angle=90, kind='satin')
p.column(T((352, 698), (352, 800)), '#6b3418', width=3.4)
for i, (x, w) in enumerate([(470, 46), (462, 34), (474, 24), (468, 14)]):
    y = 724 + i * 15
    p.column(T((x - w / 2, y), (x + w / 2, y)), '#f7c84a' if i % 2 == 0 else '#f3a24a', width=4.6)
# campfire: crossed logs, then three flames, outer to inner
p.column(T((912, 826), (1006, 802)), '#7a4a2a', width=11)
p.column(T((914, 801), (1008, 826)), '#5e3820', width=11)
flame = lambda cx, by, w, h, lean: T((cx - w, by), (cx - w * 0.9, by - h * 0.35), (cx - w * 0.35, by - h * 0.7),
                                     (cx + lean, by - h), (cx + w * 0.45, by - h * 0.62), (cx + w * 0.95, by - h * 0.3), (cx + w, by))
p.fill(scene * p.poly(flame(960, 814, 34, 100, 5), smooth=2), '#d8432c', angle=14, kind='satin', maxlen=90)
p.fill(scene * p.poly(flame(961, 814, 23, 72, -4), smooth=2), '#f08a24', angle=-16, kind='satin', maxlen=90)
p.fill(scene * p.poly(flame(962, 814, 12, 42, 2), smooth=2), '#fadb68', angle=10, kind='satin')
# the moon: a crescent
mx, my = P1(1052, 548)
moon = p.circle(mx, my, 25 * K) * (1 - p.circle(mx + 12 * K, my - 8 * K, 21 * K))
p.fill(moon, '#f3e7bd', angle=-40, kind='satin')


# compass rose: four cardinal points split light / dark, four gold diagonals behind
def kite(ang, length, half, light, dark):
    a = np.deg2rad(ang)
    tip = (CX + length * np.cos(a), CY - length * np.sin(a))
    l = (CX + half * np.cos(a + np.pi / 2), CY - half * np.sin(a + np.pi / 2))
    r = (CX + half * np.cos(a - np.pi / 2), CY - half * np.sin(a - np.pi / 2))
    p.fill(p.poly([(CX, CY), l, tip]), light, angle=ang + 90, kind='satin', pitch=2.1)
    p.fill(p.poly([(CX, CY), tip, r]), dark, angle=ang + 90, kind='satin', pitch=2.1)


for ang in (45, 135, 225, 315):
    kite(ang, 82 * K, 16 * K, '#eab04a', '#9c6a1a')
kite(90, 112 * K, 24 * K, '#cf4637', '#721a14')
for ang in (0, 180, 270):
    kite(ang, 112 * K, 24 * K, '#6f8bc2', '#1f2b52')
p.stage('satin')

# ---- 5. details: rings, ticks, stars, sparks, ripples, trees
p.column(p.circle_pts(AX, AY, 179 * K), GOLD, width=11, closed=True)                # ring separator, night 2
p.column(p.circle_pts(CX, CY, 140 * K), NAVY, width=5.5, closed=True)               # compass ring
for k in range(36):
    a = np.deg2rad(k * 10)
    r0, r1 = ((144 * K, 157 * K) if k % 3 == 0 else (145 * K, 151 * K))
    p.run([(CX + r0 * np.cos(a), CY - r0 * np.sin(a)), (CX + r1 * np.cos(a), CY - r1 * np.sin(a))], NAVY,
          stitch=1e6, gap=0, width=2.6, smooth=False, shadow=0.3)
p.knot(CX, CY, CREAM, r=8)


def pine(x, base, h, w, col):
    tiers = 4
    zig_l, zig_r = [], []
    for i in range(tiers):
        y = base - h * i / tiers; ww = w * 0.5 * (1 - i / tiers)
        zig_l += [(x - ww, y), (x - ww * 0.45, y - h / tiers * 0.55)]
        zig_r += [(x + ww * 0.45, y - h / tiers * 0.55), (x + ww, y)]
    outline = zig_l + [(x, base - h)] + zig_r[::-1]
    p.fill(scene * p.poly(T(*outline)), col, angle=0, kind='satin', pitch=2.0)
    p.column(T((x, base + 6), (x, base - 2)), '#4a2e1c', width=3.2)


for x, h, w, c in [(812, 58, 30, '#1d4632'), (838, 76, 36, '#2b5e41'), (866, 52, 28, '#1d4632'), (892, 64, 30, '#2b5e41'),
                   (1032, 60, 30, '#2b5e41'), (1060, 80, 38, '#1d4632'), (1090, 56, 28, '#2b5e41'), (1114, 44, 24, '#1d4632')]:
    pine(x, 806, h, w, c)
for x, y, r in [(870, 532, 10), (912, 506, 7), (1118, 604, 8), (838, 586, 6), (1006, 506, 6)]:
    p.star(*P1(x, y), r * K, CREAM, angle=12)
for x, y in [(944, 700), (982, 688), (962, 672)]:
    p.knot(*P1(x, y), '#fadb68', r=2.4)
for x, y, r in [(300, 552, 6), (380, 560, 5), (476, 548, 7), (566, 566, 5), (330, 578, 4)]:
    p.star(*P1(x, y), r * K, CREAM, angle=0)
for y, xa, xb in [(732, 504, 572), (748, 520, 578), (764, 262, 300), (776, 486, 566), (742, 262, 288)]:
    p.run(T((xa, y), ((xa + xb) / 2, y - 3), (xb, y)), '#bcd6ec', stitch=12, gap=5, width=2.3, shadow=0.25, clip=archm)
p.run(T((300, 800), (276, 822)), '#d9d2c2', stitch=1e6, gap=0, width=1.9, smooth=False)        # guy lines
p.run(T((470, 792), (500, 815)), '#d9d2c2', stitch=1e6, gap=0, width=1.9, smooth=False)
p.stage('details')

# ---- 6. lettering
p.arc_text('THREE NIGHTS OUT', AX, AY, 300 * K, size=42, colour=CREAM, spacing=0.05)
p.arc_text('HIGH CAMP', AX, AY, 205 * K, size=42, colour=CREAM)
p.arc_text('NIGHT 2', AX, AY, 207 * K, size=38, colour=CREAM, centre=270, bottom=True)
p.star(AX - 205 * K, AY, 9, GOLD); p.star(AX + 205 * K, AY, 9, GOLD)
p.arc_text('NIGHT 1', BX, BTOP + BW / 2, 132 * K, size=34, colour=CREAM, spacing=0.12)
for ch, ang in (('N', 90), ('E', 0), ('S', 270), ('W', 180)):
    a = np.deg2rad(ang)
    p.text(ch, CX + 124 * K * np.cos(a), CY - 124 * K * np.sin(a), 34, '#c63a2c' if ch == 'N' else NAVY)
p.stage('lettering')

# ---- 7. edges: merrow round the round ones, hot-cut satin round the die-cut arch
p.merrow(rocker, GOLD, width=19)
p.merrow(bA, GOLD, width=20)
p.satin_border(bB, CREAM, width=17)
p.merrow(bC, NAVY, width=20)
p.stage('edges')

# ---- 8. the sashiko trail: night 1 -> night 2 -> night 3
p.run(T((606, 868), (650, 910), (720, 936), (800, 918), (840, 884)), '#ebe5d6', stitch=15, gap=9, width=4.2,
      twist=1.0, sheen=0.35, shadow=0.45)
p.run(T((1080, 884), (1150, 930), (1250, 938), (1340, 884), (1390, 800)), '#ebe5d6', stitch=15, gap=9, width=4.2,
      twist=1.0, sheen=0.35, shadow=0.45, start=5)
p.stage('trail')

# ---- 9. sewing night 3 on: whip stitches two-thirds of the way round, needle and thread left on the denim
last = p.whip(bC, '#efe6d2', frm=0.28, to=0.86, spacing=21, reach=(6, 19), lean=8, width=2.6)
eye, tip = np.array([1716.0, 806.0]), np.array([1842.0, 990.0])
u = (tip - eye) / np.linalg.norm(tip - eye); nrm = np.array([-u[1], u[0]])
e = eye + u * 18
p.thread([last, last + (18, 34), (1700, 790), e - nrm * 13, e, e + nrm * 13, (1680, 846), (1672, 876), (1686, 904)],
         '#efe6d2', width=2.8, lift=1.2)
p.needle(tuple(eye), tuple(tip), radius=3.7)

img = p.save(out, stages)
print(f'{out}  {time.time() - t0:.1f}s')
