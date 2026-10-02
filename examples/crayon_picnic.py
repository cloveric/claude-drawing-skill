"""Example (children's crayon drawing / 儿童蜡笔画): 我的周末 · My Weekend — a six-year-old's crayon picture of a
family picnic, on rough drawing paper. A sun in sunglasses in the corner, the title written in four colours, a kite,
a rainbow coming out from behind the hill, clouds the sky was coloured around; the house with curly chimney smoke
and an apple tree on the hill; Dad (with a tie), Mum (polka-dot dress) and me (pigtails, holding the kite string)
standing hand in hand behind a red gingham blanket with a basket, sandwiches, juice and watermelon; the dog leaping
for a ball; tulips, daisies, a butterfly and the artist's name. Two real crayons (one snapped, its sleeve torn) and
some wax crumbs lie on the paper. Everything is outlined first and the big areas are coloured round what is already
there, the way a child does it.
Draw-on stages: paper -> outlines -> sun, title & name -> rainbow, kite & sky -> hills & meadow -> house & tree ->
family -> picnic & dog -> flowers & kite string -> the crayons (final). No image model.
python3 crayon_picnic.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from crayon import Crayon
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'crayon_picnic.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

c = Crayon(1920, 1080, seed=11)
C = c.C
rng = c.rng
c.paper()
c.stage('paper')


def arc(cx, cy, rx, ry, a0, a1, n=40):
    """points on an ellipse arc; angles in degrees, 0 = right, 90 = up"""
    t = np.radians(np.linspace(a0, a1, n))
    return np.stack([cx + rx * np.cos(t), cy - ry * np.sin(t)], 1)


def U(*ms):
    return np.maximum.reduce([np.asarray(m, np.float32) for m in ms])


def cloud_pts(cx, cy, w, h, bumps=5):
    """a child's cloud: scallops along the top, a flatter bottom"""
    t = np.linspace(0, 2 * np.pi, 220, endpoint=False)
    top = np.sin(t) > 0
    r = 1 + np.where(top, 0.2 * np.abs(np.sin(t * bumps / 2 + 0.3)), 0.06 * np.abs(np.sin(t * bumps)))
    return np.stack([cx + w * np.cos(t) * r, cy - h * np.sin(t) * r * np.where(top, 1.0, 0.55)], 1)


def hand(x, y, r=12, colour=C['black'], spread=(200, 340)):
    """a hand: a little circle with a rake of fingers"""
    c.line(c.circle(x, y, r, lumpy=0.05, amp=1), colour, width=7, closed=True)
    for a in np.linspace(*spread, 5):
        a = np.radians(a)
        c.line([(x + r * np.cos(a), y - r * np.sin(a)), (x + (r + 13) * np.cos(a), y - (r + 13) * np.sin(a))],
               colour, width=6)


objects = []          # interiors of everything sketched, so the big fills can colour around them

# ===================================================================== 1. outlines
SX, SY, SR = 190, 172, 98
sun = c.circle(SX, SY, SR, lumpy=0.03)
c.line(sun, C['orange'], width=10, closed=True)

# house on the hill
house = c.rect(150, 482, 430, 690, skew=5)
roof = c.poly([(120, 494), (290, 360), (460, 494)])
chim = c.poly([(365, 425), (366, 384), (399, 386), (399, 450)])
door = c.rect(262, 598, 318, 690, skew=2)
win1, win2 = c.rect(172, 520, 238, 576, skew=3), c.rect(345, 518, 411, 576, skew=3)
for p in (chim, roof, house, door, win1, win2):
    c.line(p, C['black'], width=9, closed=True)
objects += [c.mask(p) for p in (house, roof, chim)]

# apple tree
trunk = c.poly([(570, 488), (602, 488), (608, 700), (622, 716), (556, 716), (566, 700)])
crown = c.circle(588, 418, 112, 96, lumpy=0.12)
c.line(trunk, C['brown'], width=9, closed=True)
c.line(crown, C['darkgreen'], width=10, closed=True)
objects += [c.mask(trunk), c.mask(crown)]

# hills and the meadow line
hillL = spline([(-30, 600), (180, 478), (420, 440), (640, 486), (880, 590), (1010, 668)], 12)
hillR = spline([(740, 676), (1000, 566), (1300, 522), (1620, 534), (1960, 586)], 12)
meadow = spline([(-30, 694), (420, 676), (900, 684), (1400, 664), (1960, 690)], 12)

# the family, hand in hand: Dad, Mum, me
DAD, MUM, ME = 745, 905, 1062
dad_head = c.circle(DAD, 468, 48, lumpy=0.04)
dad_shirt = c.rect(697, 522, 793, 666, skew=4)
dad_legs = [c.rect(704, 664, 738, 790, skew=2), c.rect(752, 664, 786, 790, skew=2)]
mum_head = c.circle(MUM, 486, 45, lumpy=0.04)
mum_hair = c.poly(list(arc(MUM, 492, 64, 66, -12, 192, 30)) + [(MUM - 66, 580), (MUM - 40, 572), (MUM + 40, 572), (MUM + 66, 580)], amp=2.5)
mum_dress = c.poly([(MUM - 16, 532), (MUM + 16, 532), (MUM + 74, 722), (MUM - 74, 722)])
me_head = c.circle(ME, 560, 42, lumpy=0.04)
me_shirt = c.rect(1030, 604, 1094, 676, skew=3)
me_skirt = c.poly([(1028, 672), (1096, 672), (1112, 720), (1012, 720)])
for p in [mum_hair]:
    c.line(p, C['brown'], width=8, closed=True)
for p in [dad_head, dad_shirt, *dad_legs, mum_head, mum_dress, me_head, me_shirt, me_skirt]:
    c.line(p, C['black'], width=8, closed=True)
# arms and hands (holding hands: one round hand between two people)
c.line(spline([(700, 540), (676, 590), (650, 628)], 8), C['black'], width=9)
hand(642, 636, spread=(150, 300))
c.line(spline([(790, 540), (812, 580), (826, 612)], 8), C['black'], width=9)
c.line(spline([(MUM - 26, 566), (MUM - 50, 594), (MUM - 64, 614)], 8), C['black'], width=9)
hand(836, 616, r=13, spread=(250, 290))
c.line(spline([(MUM + 26, 566), (MUM + 52, 600), (MUM + 76, 624)], 8), C['black'], width=9)
c.line(spline([(1034, 620), (1012, 628), (1000, 630)], 8), C['black'], width=9)
hand(990, 630, r=13, spread=(250, 290))
c.line(spline([(1092, 618), (1106, 596), (1114, 574)], 8), C['black'], width=9)
hand(1118, 562, r=12, spread=(20, 160))
for x0, x1, y in [(MUM - 22, MUM - 24, 722), (MUM + 22, MUM + 24, 722), (1048, 1046, 720), (1076, 1078, 720)]:
    c.line([(x0, y), (x1, y + 72)], C['black'], width=9)
objects += [c.mask(p) for p in [dad_head, dad_shirt, *dad_legs, mum_head, mum_hair, mum_dress, me_head, me_shirt, me_skirt]]
objects += [c.mask(c.rect(MUM - 40, 715, MUM + 40, 805, 0)), c.mask(c.rect(1035, 715, 1090, 805, 0)),
            c.mask(c.rect(630, 530, 830, 650, 0)), c.mask(c.rect(975, 550, 1135, 645, 0))]

# the picnic blanket (a child's perspective: wider at the front) and what is on it
TL, TR, BR, BL = np.array([565, 830.]), np.array([1225, 830.]), np.array([1292, 1006.]), np.array([498, 1006.])
blanket = c.poly([TL, TR, BR, BL], amp=2.5)
c.line(blanket, C['red'], width=10, closed=True)
basket = c.poly([(598, 852), (748, 852), (732, 944), (614, 944)])
handle = arc(673, 856, 62, 70, 180, 0, 30)
plate = c.circle(888, 925, 92, 30, lumpy=0.02)
sand1 = c.poly([(828, 920), (880, 866), (902, 928)])
sand2 = c.poly([(904, 924), (934, 864), (962, 916)])
glass = c.poly([(1004, 858), (1046, 858), (1040, 946), (1010, 946)])
mel1 = c.poly(list(arc(1124, 912, 56, 52, 180, 360, 30)))
mel2 = c.poly(list(arc(1206, 940, 46, 42, 170, 350, 26)))
for p, col in [(basket, C['brown']), (plate, C['sky']), (sand1, C['tan']), (sand2, C['tan']), (glass, C['blue']),
               (mel1, C['darkgreen']), (mel2, C['darkgreen'])]:
    c.line(p, col, width=8, closed=True)
c.line(handle, C['brown'], width=11)
objects += [c.mask(blanket)]

# the dog, leaping for the ball
dog_body = c.circle(1446, 862, 90, 40, rot=-0.2, lumpy=0.04)
dog_head = c.circle(1548, 806, 42, lumpy=0.04)
dog_snout = c.circle(1590, 820, 24, 17, lumpy=0.03)
dog_ear = c.circle(1526, 806, 15, 32, rot=0.35, lumpy=0.05)
for p in (dog_body, dog_head, dog_snout):
    c.line(p, C['brown'], width=9, closed=True)
legs = [[(1502, 872), (1532, 888), (1562, 898)], [(1486, 884), (1514, 902), (1540, 918)],
        [(1390, 884), (1364, 902), (1334, 914)], [(1404, 892), (1384, 914), (1364, 934)]]
for lg in legs:
    c.line(spline(lg, 8), C['brown'], width=15)
tail = spline([(1360, 846), (1336, 822), (1322, 792)], 8)
c.line(tail, C['brown'], width=12)
ball = c.circle(1668, 752, 27, lumpy=0.03)
c.line(ball, C['red'], width=8, closed=True)
objects += [c.mask(p) for p in (dog_body, dog_head, dog_snout, ball)]

# the kite and the clouds
KC = np.array([1300, 172.])
KT, KR, KB, KL = KC + (0, -92), KC + (90, -8), KC + (0, 138), KC + (-90, -8)
kite = c.poly([KT, KR, KB, KL], amp=1.5)
c.line(kite, C['black'], width=8, closed=True)
cl1 = c.wobble(cloud_pts(1712, 108, 118, 52, 5), 1.5)
cl2 = c.wobble(cloud_pts(712, 262, 84, 38, 4), 1.5)
for p in (cl1, cl2):
    c.line(p, C['blue'], width=8, closed=True)
objects += [c.mask(kite), c.mask(cl1), c.mask(cl2)]

# flowers and a butterfly in the grass
tulips = []
for (x, y, col) in [(84, 872, 'red'), (190, 900, 'pink'), (300, 868, 'orange'), (1360, 984, 'magenta')]:
    c.line([(x, y), (x + rng.normal(0, 4), y + 96)], C['darkgreen'], width=8)
    leaves = [c.poly([(x, y + 80), (x + s * 30, y + 40), (x + s * 8, y + 62)], amp=0.6) for s in (-1, 1)]
    head = c.poly([(x - 26, y - 4), (x - 28, y - 48), (x - 12, y - 30), (x, y - 54), (x + 12, y - 30), (x + 28, y - 48),
                   (x + 26, y - 4), (x, y + 10)], amp=1.0)
    for lf in leaves:
        c.line(lf, C['darkgreen'], width=6, closed=True)
    c.line(head, C[col], width=7, closed=True)
    tulips.append((head, leaves, col))
    objects += [c.mask(head)] + [c.mask(lf) for lf in leaves]
daisies = [(1440, 1046), (1250, 1052), (432, 1000)]
for (x, y) in daisies:
    for k in range(8):
        a = k * np.pi / 4 + 0.2
        pt = c.circle(x + 20 * np.cos(a), y - 20 * np.sin(a), 11, 7, rot=-a, lumpy=0.02, amp=0.5)
        c.line(pt, C['grey'], width=4, closed=True, pressure=0.6)
    objects += [c.mask(c.circle(x, y, 34))]
BX, BY = 500, 780
wings = []
for s in (-1, 1):
    for (dy, rx, ry, col) in [(-17, 32, 25, 'pink'), (17, 24, 19, 'violet')]:
        w = c.circle(BX + s * (rx + 7), BY + dy, rx, ry, rot=s * 0.45)
        c.line(w, C['purple'], width=6, closed=True)
        wings.append((w, col))
        objects += [c.mask(w)]
# the ball's motion lines, the dog's wag lines
for k in range(3):
    y = 736 + k * 16
    c.line([(1602 - k * 6, y), (1630 - k * 4, y - 2)], C['grey'], width=5, pressure=0.7)
for r in (22, 34):
    c.line(arc(1320, 790, r, r, 100, 190, 10), C['brown'], width=5, pressure=0.7)

OBJ = U(*objects)
LINES0 = c.drawn()                          # every line drawn so far (arms, legs, stems, strings)
c.line(hillL, C['darkgreen'], width=9, avoid=c.grow(OBJ, 10))
c.line(hillR, C['green'], width=9, avoid=c.grow(OBJ, 10))
c.line(meadow, C['darkgreen'], width=8, pressure=0.75, avoid=c.grow(OBJ, 10))
c.stage('outlines')

# ===================================================================== 2. sun and title
c.loops(c.mask(sun), C['yellow'], r=20, width=12, density=0.62, pressure=0.85)
c.scribble(c.mask(sun) * (c.YY > SY + 30) * (c.XX > SX - 20), C['orange'], angle=-30, width=14, density=0.35,
           pressure=0.55, reach=None, mess=0.2)
for k in range(12):
    a = np.radians(k * 30 + 8)
    r0, r1 = SR + 20, SR + (88 if k % 2 else 52)
    c.line([(SX + r0 * np.cos(a), SY - r0 * np.sin(a)), (SX + r1 * np.cos(a), SY - r1 * np.sin(a))],
           C['orange'] if k % 2 else C['yellow'], width=12, pressure=0.95)
# sunglasses, smile, cheeks
lens1 = c.rect(SX - 64, SY - 34, SX - 12, SY + 4, skew=2)
lens2 = c.rect(SX + 12, SY - 34, SX + 64, SY + 4, skew=2)
for p in (lens1, lens2):
    c.line(p, C['black'], width=7, closed=True)
    c.scribble(c.mask(p), C['black'], angle=20, width=10, density=0.9, pressure=0.95, reach=None, mess=0.1)
    c.burnish(c.mask(p), 0.75)
c.line([(SX - 12, SY - 22), (SX + 12, SY - 22)], C['black'], width=7)
c.line(arc(SX, SY + 18, 42, 30, 205, 335, 20), C['red'], width=10)
for dx in (-62, 62):
    c.dab(SX + dx, SY + 26, 11, C['pink'], pressure=0.6)
c.write('我的周末!', 840, 116, 132, [C['red'], C['orange'], C['green'], C['blue'], C['violet']], width=11.5, tilt=8, jumble=0.1)
w0 = c.wax.copy()
c.write('朵朵 6岁', 196, 1032, 64, [C['violet']], width=8, tilt=5, jumble=0.08, spacing=0.95)
NAME = c.grow((c.wax - w0) > 0.05, 18)               # the grass will leave a clear patch round my name
c.stage('sun_title')

# ===================================================================== 3. rainbow, kite, sky
RCX, RCY = 1722, 690
for i, col in enumerate(['red', 'orange', 'yellow', 'green', 'blue', 'violet']):
    R = 318 - i * 25
    pts = arc(RCX, RCY, R, R, 8, 172, 160)
    hy = np.interp(pts[:, 0], hillR[:, 0], hillR[:, 1])
    pts = pts[pts[:, 1] < hy - 6]
    if len(pts) > 3:
        c.follow(pts, C[col], width=27, passes=2, crayon=14, pressure=0.9)
quads = [(KT, KR, KC), (KR, KB, KC), (KB, KL, KC), (KL, KT, KC)]
for q, col, ang in zip(quads, ['yellow', 'green', 'blue', 'red'], [30, -40, 60, -20]):
    c.scribble(c.mask(c.poly(q, amp=0.5)), C[col], angle=ang, width=14, density=0.8, pressure=0.9, reach=None, mess=0.35)
c.line([KT, KB], C['black'], width=7)
c.line([KL, KR], C['black'], width=7)
tailp = spline([KB, KB + (38, 44), KB + (90, 34), KB + (140, 72), KB + (192, 62)], 10)
c.line(tailp, C['black'], width=7, pressure=0.95)
for k, col in zip([12, 26, 40], ['magenta', 'orange', 'violet']):
    x, y = tailp[k]
    for s in (-1, 1):
        bow = c.poly([(x, y), (x + s * 22, y - 13), (x + s * 22, y + 13)], amp=0.6)
        c.line(bow, C[col], width=6, closed=True)
        c.scribble(c.mask(bow), C[col], angle=90, width=9, density=0.9, pressure=0.9, reach=None, mess=0.3)
sky = c.mask(c.rect(-40, -40, 1960, 470, 0))
c.scribble(sky, C['sky'], angle=6, width=22, density=0.55, pressure=0.78, reach=300, mess=0.5,
           avoid=U(OBJ, c.drawn()), halo=13, fade=(170, 450))
c.stage('sky')

# ===================================================================== 4. hills and meadow
def below(curve, pad=0):
    return (c.YY > np.interp(c.XX, curve[:, 0], curve[:, 1]) + pad).astype(np.float32)


mR = below(hillR) * (1 - below(meadow))
mL = below(hillL) * (1 - below(meadow)) * (1 - mR)
mM = below(meadow)
keep_off = U(c.grow(OBJ, 8), LINES0)
c.scribble(mL, C['green'], angle=28, width=22, density=0.62, pressure=0.82, reach=280, mess=0.5, avoid=keep_off, halo=6)
c.scribble(mR, C['yellowgreen'], angle=-24, width=22, density=0.62, pressure=0.85, reach=280, mess=0.5, avoid=keep_off, halo=6)
c.scribble(mM, C['green'], angle=78, width=22, density=0.6, pressure=0.85, reach=240, mess=0.5,
           avoid=U(c.grow(OBJ, 8), c.drawn(), NAME), halo=6, angle_jitter=12)
c.stage('land')

# ===================================================================== 5. house and tree
c.scribble(c.mask(house), C['yellow'], angle=35, width=18, density=0.72, pressure=0.9, reach=None, mess=0.6,
           avoid=U(c.mask(door), c.mask(win1), c.mask(win2)), halo=4)
c.scribble(c.mask(roof), C['red'], angle=-18, width=18, density=0.8, pressure=0.92, reach=None, mess=0.6)
c.scribble(c.mask(chim), C['brown'], angle=80, width=14, density=0.8, pressure=0.9, reach=None, mess=0.4)
c.scribble(c.mask(door), C['brown'], angle=95, width=14, density=0.85, pressure=0.9, reach=None, mess=0.3)
c.dab(306, 646, 6, C['yellow'])
for w in (win1, win2):
    c.scribble(c.mask(w), C['sky'], angle=-30, width=14, density=0.75, pressure=0.85, reach=None, mess=0.3)
for (x0, y0, x1, y1) in [(205, 520, 205, 576), (172, 548, 238, 548), (378, 518, 378, 576), (345, 547, 411, 547)]:
    c.line([(x0, y0), (x1, y1)], C['black'], width=7)
tt = np.linspace(0, 1, 260)
rr = 9 + 24 * tt                                  # a curly line of smoke, its loops growing as it rises
smoke = np.stack([382 + 80 * tt + rr * np.sin(tt * 4.5 * 2 * np.pi), 376 - 150 * tt - rr * (1 - np.cos(tt * 4.5 * 2 * np.pi)) * 0.8], 1)
c.line(smoke, C['grey'], width=7, pressure=0.7)
c.scribble(c.mask(trunk), C['brown'], angle=88, width=14, density=0.8, pressure=0.9, reach=None, mess=0.4)
c.loops(c.mask(crown), C['green'], r=22, width=11, density=0.55, pressure=0.85)
for (x, y) in [(540, 392), (612, 372), (640, 440), (560, 460), (604, 486), (520, 430), (660, 400)]:
    c.dab(x, y, 12, C['red'], pressure=1.0)
c.stage('house_tree')

# ===================================================================== 6. the family
for hx, hy, r in [(DAD, 468, 48), (MUM, 486, 45), (ME, 560, 42)]:
    c.scribble(c.mask(c.circle(hx, hy, r - 3)), C['peach'], angle=20, width=14, density=0.7, pressure=0.6, reach=None, mess=0.2)
# Dad: spiky hair, blue shirt, red tie, brown trousers, black shoes
dad_hair = c.poly(list(arc(DAD, 468, 50, 50, 12, 168, 18)) + [(DAD - 34, 446), (DAD, 452), (DAD + 34, 446)], amp=1.5)
c.scribble(c.mask(dad_hair), C['brown'], angle=80, width=12, density=0.85, pressure=0.95, reach=None, mess=0.5)
for k in range(7):
    a = np.radians(25 + k * 22)
    c.line([(DAD + 48 * np.cos(a), 468 - 48 * np.sin(a)), (DAD + 64 * np.cos(a + 0.08), 468 - 64 * np.sin(a + 0.08))],
           C['brown'], width=9)
c.scribble(c.mask(dad_shirt), C['blue'], angle=-35, width=18, density=0.72, pressure=0.9, reach=None, mess=0.6)
tie = c.poly([(DAD - 8, 526), (DAD + 8, 526), (DAD + 12, 590), (DAD, 606), (DAD - 12, 590)], amp=0.8)
c.line(tie, C['red'], width=6, closed=True)
c.scribble(c.mask(tie), C['red'], angle=90, width=10, density=0.9, pressure=1.0, reach=None, mess=0.2)
for lg in dad_legs:
    c.scribble(c.mask(lg), C['brown'], angle=95, width=14, density=0.78, pressure=0.85, reach=None, mess=0.5)
for x in (712, 778):
    sh = c.circle(x, 798, 26, 12, lumpy=0.03)
    c.line(sh, C['black'], width=7, closed=True)
    c.scribble(c.mask(sh), C['black'], angle=0, width=10, density=0.9, pressure=0.95, reach=None, mess=0.2)
# Mum: long hair, pink polka-dot dress, red shoes
c.scribble(c.mask(mum_hair) * (1 - c.mask(c.circle(MUM, 486, 47))), C['orange'], angle=75, width=13, density=0.8,
           pressure=0.9, reach=None, mess=0.3)
c.scribble(c.mask(mum_dress), C['pink'], angle=55, width=18, density=0.75, pressure=0.9, reach=None, mess=0.6)
for (x, y) in [(MUM - 20, 600), (MUM + 18, 588), (MUM + 2, 640), (MUM - 38, 676), (MUM + 34, 672), (MUM - 4, 700)]:
    c.dab(x, y, 8, C['magenta'])
for x in (MUM - 30, MUM + 30):
    sh = c.circle(x, 800, 22, 11)
    c.line(sh, C['red'], width=6, closed=True)
    c.scribble(c.mask(sh), C['red'], angle=0, width=10, density=0.9, pressure=0.95, reach=None, mess=0.2)
# me: pigtails with red bows, yellow T-shirt with a star, violet skirt, blue shoes
for s in (-1, 1):
    pg = c.circle(ME + s * 52, 540, 18, 22)
    c.line(pg, C['brown'], width=7, closed=True)
    c.scribble(c.mask(pg), C['brown'], angle=70, width=10, density=0.85, pressure=0.9, reach=None, mess=0.3)
    bx, by = ME + s * 40, 516
    for t in (-1, 1):
        bow = c.poly([(bx, by), (bx + t * 18, by - 11), (bx + t * 18, by + 11)], amp=0.5)
        c.scribble(c.mask(bow), C['red'], angle=90, width=9, density=0.95, pressure=1.0, reach=None, mess=0.2)
fringe = c.poly(list(arc(ME, 560, 44, 44, 20, 160, 16)) + [(ME - 20, 534), (ME + 6, 540), (ME + 30, 532)], amp=1.2)
c.scribble(c.mask(fringe), C['brown'], angle=-60, width=11, density=0.85, pressure=0.95, reach=None, mess=0.4)
c.scribble(c.mask(me_shirt), C['yellow'], angle=40, width=16, density=0.8, pressure=0.95, reach=None, mess=0.5)
star = [(ME + 22 * np.sin(a) * (1 if k % 2 == 0 else 0.45), 638 - 22 * np.cos(a) * (1 if k % 2 == 0 else 0.45))
        for k, a in enumerate(np.linspace(0, 2 * np.pi, 10, endpoint=False))]
c.line(c.poly(star, amp=0.5), C['orange'], width=6, closed=True)
c.scribble(c.mask(me_skirt), C['violet'], angle=-20, width=14, density=0.8, pressure=0.9, reach=None, mess=0.5)
for x in (1040, 1084):
    sh = c.circle(x, 800, 20, 11)
    c.line(sh, C['blue'], width=6, closed=True)
    c.scribble(c.mask(sh), C['blue'], angle=0, width=10, density=0.9, pressure=0.95, reach=None, mess=0.2)
# faces
for hx, hy, r, lashes in [(DAD, 468, 48, False), (MUM, 486, 45, True), (ME, 560, 42, False)]:
    for s in (-1, 1):
        c.dab(hx + s * r * 0.36, hy - r * 0.08, 6.5, C['black'])
        if lashes:
            for a in (60, 90, 120):
                ex, ey = hx + s * r * 0.36, hy - r * 0.08
                c.line([(ex + 9 * np.cos(np.radians(a)), ey - 9 * np.sin(np.radians(a))),
                        (ex + 17 * np.cos(np.radians(a)), ey - 17 * np.sin(np.radians(a)))], C['black'], width=4)
        c.dab(hx + s * r * 0.58, hy + r * 0.3, 9, C['pink'], pressure=0.55)
    c.line(arc(hx, hy + r * 0.12, r * 0.42, r * 0.36, 200, 340, 16), C['red'], width=7)
c.stage('family')

# ===================================================================== 7. picnic and dog
P = lambda u, v: (1 - v) * ((1 - u) * TL + u * TR) + v * ((1 - u) * BL + u * BR)
food = U(*[c.mask(p) for p in (basket, plate, glass, mel1, mel2)])
stripes = []
for i in range(7):
    u0 = (2 * i + 0.5) / 14; u1 = u0 + 1 / 14
    stripes.append((c.poly([P(u0, 0), P(u1, 0), P(u1, 1), P(u0, 1)], amp=1.0), 90 - (u0 - 0.5) * 22))
for j in range(4):
    v0 = (2 * j + 0.5) / 8; v1 = v0 + 1 / 8
    stripes.append((c.poly([P(0, v0), P(1, v0), P(1, v1), P(0, v1)], amp=1.0), 3))
for q, ang in stripes:
    c.scribble(c.mask(q) * c.mask(blanket), C['red'], angle=ang, width=16, density=0.72, pressure=0.7, reach=260,
               mess=0.3, avoid=food, halo=7)
c.scribble(c.mask(basket), C['tan'], angle=20, width=16, density=0.75, pressure=0.85, reach=None, mess=0.4)
for k in range(5):
    x = 612 + k * 30
    c.line([(x, 856), (x + 10, 940)], C['brown'], width=6)
for y in (878, 908, 934):
    c.line([(604, y), (742, y)], C['brown'], width=6)
for p in (sand1, sand2):
    c.scribble(c.mask(p), C['tan'], angle=0, width=12, density=0.75, pressure=0.85, reach=None, mess=0.3)
c.line([(834, 912), (884, 878), (898, 916)], C['yellowgreen'], width=7)
c.line([(910, 914), (936, 876), (956, 910)], C['yellow'], width=7)
c.scribble(c.mask(glass) * (c.YY > 880), C['orange'], angle=0, width=14, density=0.85, pressure=0.95, reach=None, mess=0.2)
c.line([(1028, 900), (1040, 832), (1060, 820)], C['magenta'], width=7)
for m, (cx, cy, r) in [(mel1, (1124, 912, 56)), (mel2, (1206, 940, 46))]:
    c.scribble(c.mask(m), C['red'], angle=0, width=14, density=0.85, pressure=0.95, reach=None, mess=0.3)
mm1 = arc(1124, 912, 49, 45, 186, 354, 30)
c.line(mm1, C['green'], width=9)
c.line(arc(1206, 940, 40, 36, 174, 346, 26), C['green'], width=8)
for (x, y) in [(1100, 930), (1124, 938), (1146, 928), (1112, 950), (1138, 952), (1190, 954), (1212, 962), (1226, 948)]:
    c.dab(x, y, 4.5, C['black'])
# the dog
c.scribble(U(c.mask(dog_body), c.mask(dog_head), c.mask(dog_snout)), C['tan'], angle=-30, width=16, density=0.75,
           pressure=0.88, reach=None, mess=0.5)
c.scribble(c.mask(dog_ear), C['brown'], angle=70, width=12, density=0.9, pressure=0.95, reach=None, mess=0.3)
c.line(dog_ear, C['brown'], width=7, closed=True)
for (x, y, r) in [(1420, 848, 15), (1470, 872, 11), (1392, 866, 9)]:
    c.loops(c.mask(c.circle(x, y, r, r * 0.8)), C['brown'], r=6, width=8, density=0.9, pressure=0.95)
for lg in legs:                                   # legs pressed in hard over the body colour
    c.line(spline(lg, 8), C['brown'], width=17, pressure=1.0)
for lg in legs:
    c.dab(lg[-1][0] + 4, lg[-1][1] + 2, 8, C['brown'])
c.dab(1556, 794, 7, C['black'])
c.dab(1610, 814, 9, C['black'])
tongue = c.poly([(1584, 832), (1600, 832), (1602, 856), (1590, 862), (1582, 852)], amp=0.6)
c.scribble(c.mask(tongue), C['pink'], angle=90, width=9, density=0.95, pressure=0.95, reach=None, mess=0.3)
c.line(spline([(1518, 822), (1522, 840), (1530, 850)], 8), C['red'], width=11)
c.dab(1532, 858, 7, C['yellow'])
c.loops(c.mask(ball), C['red'], r=10, width=10, density=0.8, pressure=0.95)
c.burnish(c.mask(ball), 0.7)
c.line(arc(1668, 752, 27, 27, 120, 250, 14) + (14, 0), C['yellow'], width=7)
c.stage('picnic')

# ===================================================================== 8. flowers, butterfly, kite string
for head, leaves, col in tulips:
    for s, lf in zip((-1, 1), leaves):
        c.scribble(c.mask(lf), C['darkgreen'], angle=60 * s, width=9, density=0.95, pressure=0.95, reach=None, mess=0.2)
    c.scribble(c.mask(head), C[col], angle=80, width=12, density=0.85, pressure=0.95, reach=None, mess=0.4)
for (x, y) in daisies:
    c.dab(x, y, 10, C['yellow'])
for w, col in wings:
    c.scribble(c.mask(w), C[col], angle=50, width=12, density=0.7, pressure=0.85, reach=None, mess=0.3)
for s in (-1, 1):
    c.dab(BX + s * 42, BY - 20, 7, C['yellow'])
c.line([(BX, BY - 28), (BX + 1, BY + 32)], C['black'], width=11, pressure=1.0)
for s in (-1, 1):
    c.line(spline([(BX, BY - 26), (BX + s * 10, BY - 48), (BX + s * 22, BY - 60)], 6), C['black'], width=5)
    c.dab(BX + s * 23, BY - 62, 5, C['black'])
# kite string, last of all, from the kite to my hand
c.line(spline([KB, (1250, 380), (1180, 470), (1124, 552)], 14), C['black'], width=4, pressure=0.8)
c.stage('flowers')

# ===================================================================== 9. the crayons are still lying on the paper
c.crumbs(1470, 940, 1640, 1040, [C['red'], C['green']], n=22, size=(2, 5))
c.crumbs(1660, 820, 1760, 900, [C['blue']], n=10, size=(2, 4))
c.stick(1712, 1002, 164, C['red'], length=380, radius=23, tip='worn')
c.stick(1790, 890, -28, C['blue'], length=170, radius=23, tip='broken', peel=0.55)

img = c.save(out, stages)
print(f'{out}  {time.time() - t0:.1f}s')
