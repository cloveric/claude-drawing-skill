"""Example (linocut / 黑白麻胶版画): 雪夜归途 · Homeward, First Snow -- a two-block linocut of a village on the
first night of snow. Someone is hauling a sled of firewood home by lantern light; their footprints and the sled
runners trail back out of the picture, the snow ahead of them is still untouched. At the cottage the door stands
open, warm light spills onto the snow and the dog has run out to meet them (its paw prints lead back to the
door). Chimney smoke leans with the wind, snow falls across a black sky cut with long wind streaks and a carved
moon with broken rings; a bare tree frames the left side, a spruce wood runs behind the houses.
Key block in black; one spot-colour block (lamp ochre) prints the lit windows, the door, the spill of light and
the lantern glow, slightly out of register. Pencil edition number, title and signature in the margin; blind chop.
Draw-on stages: paper -> inked block -> blocking out -> sky -> hills and wood -> village -> snow field ->
figures -> colour block -> pencil. No image model.
python3 linocut_snowy_village.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from linocut import Linocut
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'linocut_snowy_village.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

BX0, BY0, BX1, BY1 = 100, 56, 1820, 918
L = Linocut(1920, 1080, block=(BX0, BY0, BX1, BY1), seed=11)
rng = np.random.default_rng(5)
lamp = L.colour_block('#e8a33a', offset=(4, -3))
KEY = [L.key]


def line(ctrl, x0=BX0 - 10, x1=BX1 + 10):
    P = spline(ctrl, 16)
    xs = np.arange(x0, x1 + 1, 4, dtype=np.float32)
    return xs, np.interp(xs, P[:, 0], P[:, 1]).astype(np.float32)


RX, RY = line([(BX0 - 10, 520), (260, 478), (470, 505), (700, 452), (930, 492), (1180, 438), (1420, 470), (1640, 430), (BX1 + 10, 455)])
FX, FY = line([(BX0 - 10, 596), (380, 588), (700, 606), (1000, 590), (1300, 604), (1600, 586), (BX1 + 10, 598)])
GX, GY = line([(BX0 - 10, 652), (300, 640), (620, 664), (900, 650), (1250, 662), (1560, 646), (BX1 + 10, 656)])
ridge = lambda x: np.interp(x, RX, RY)
wood = lambda x: np.interp(x, FX, FY)
ground = lambda x: np.interp(x, GX, GY)

sky = [(BX0 - 10, BY0 - 10), (BX1 + 10, BY0 - 10)] + list(zip(RX[::-1], RY[::-1]))
hills = list(zip(RX, RY)) + list(zip(FX[::-1], FY[::-1]))
field = list(zip(GX, GY)) + [(BX1 + 10, BY1 + 10), (BX0 - 10, BY1 + 10)]
above_field = [(BX0 - 10, BY0 - 10), (BX1 + 10, BY0 - 10)] + list(zip(GX[::-1], GY[::-1]))
MX, MY, MR = 1532, 196, 74

L.stage('paper', blocks=[])
L.stage('inked', blocks=KEY)

# ---- 1. blocking out: the big whites are cut away first
L.clear(L.poly(hills), chatter=0.35, angle=4)
L.clear(L.poly(field), chatter=0.5, angle=-6)
L.clear(L.disc(MX, MY, MR), chatter=0.2, angle=-30)
L.stage('blocking', blocks=KEY)

# ---- 2. sky: wind streaks with the V-gouge, the moon and its rings, snow clouds
moon_d = lambda x, y: np.hypot(x - MX, y - MY)


def streak_density(x, y):
    band = max(np.exp(-((y - 150 - 0.05 * (x - 900)) / 40) ** 2), np.exp(-((y - 345 + 0.04 * (x - 900)) / 50) ** 2))
    return (0.12 + 0.88 * band) * np.clip((moon_d(x, y) - 215) / 60, 0, 1)


L.flow(sky, lambda x, y: 171 + 5 * np.sin(x / 230 + y / 95), n=300, length=(40, 320), width=(1.6, 5.0),
       step=3.0, density=streak_density)
L.moon(MX, MY, MR, rings=(1.42, 1.72, 2.05, 2.42))
L.stage('sky', blocks=KEY)

# ---- 3. hills: drift contours left standing parallel to the ridge, darker on the flanks facing away from the moon
slope = np.gradient(RY) / 4.0


def hill_density(x, y):
    s = float(np.interp(x, RX, slope))
    depth = (y - ridge(x)) / max(wood(x) - ridge(x), 1)
    return np.clip(0.12 + 2.2 * max(-s, 0) + 0.55 * depth ** 2, 0, 0.95)


L.hatch(hills, angle=0, spacing=9, width=2.6, dash=(25, 140), gap=(8, 60), cut=False,
        bend=lambda x, y: ridge(x) - ridge(1000), density=hill_density)
# the spruce wood: a black band behind the houses with trees rising out of it
for x in np.arange(BX0 + 12, BX1 - 8, 26.0):
    x = x + rng.uniform(-10, 10)
    h = rng.uniform(55, 120) * (0.85 + 0.3 * np.sin(x / 140) ** 2)
    L.pine(x, wood(x) + 30, h, tiers=int(h / 22) + 2, snow=0.7, halo=2.0, region=L.poly(above_field))
for x, h in ((560, 150), (1180, 165), (1420, 140), (1700, 175)):
    L.pine(x, ground(x) + 14, h, snow=0.85, halo=2.5, region=L.poly(above_field))
L.leave(L.poly(list(zip(FX, FY + 6)) + list(zip(GX[::-1], GY[::-1] + 2))))      # the wood's dark foot
L.stage('hills', blocks=KEY)

# ---- 4. the village: cottages with snow-heavy roofs; lit windows go on the colour block
L.cottage(430, 640, 118, 74, 66, side=104, windows=[(36, 26, 22, 26)], side_windows=[(40, 22, 22, 26)],
          chimney=(0.7, 16, 34), lit=lamp)
home = L.cottage(650, 676, 196, 118, 112, side=176, rise=0.1, windows=[], side_windows=[(36, 40, 34, 40), (106, 40, 34, 40)],
                 door=(70, 54, 84, True), chimney=(0.55, 22, 46), lit=lamp, attic=False)
L.cottage(1050, 652, 150, 96, 88, side=130, windows=[(30, 40, 28, 32), (92, 40, 28, 32)], side_windows=[(54, 34, 26, 30)],
          chimney=(0.35, 18, 38), lit=None)
c4 = L.cottage(1290, 634, 108, 70, 64, side=92, windows=[(40, 22, 26, 28)], chimney=(0.6, 14, 30), lit=lamp)
L.smoke(*home['chimney'], rise=190, drift=-200, width=13)
L.smoke(*c4['chimney'], rise=120, drift=-190, width=10)
L.stage('village', blocks=KEY)

# ---- 5. the snow field: drift ridges, the trodden path, a fence going down to the road
path = [(home['door'][0] + 27, 690), (820, 712), (980, 744), (1150, 796), (1290, 860), (1400, 900), (1460, 930)]
P = spline(path, 20)


def path_dist(x, y):
    return float(np.min(np.hypot(P[:, 0] - x, P[:, 1] - y)))


def field_density(x, y):
    lowness = max(0.0, (y - ground(x)) / (BY1 - ground(x)))
    tree_shade = np.exp(-((x - 300) / 260) ** 2)
    nearpath = np.clip(1 - path_dist(x, y) / 60, 0, 1)
    return np.clip(0.18 + 0.55 * lowness ** 1.5 + 0.5 * tree_shade - 0.6 * nearpath, 0.02, 0.95)


L.hatch(field, angle=-2, spacing=12, width=3.0, dash=(40, 240), gap=(10, 90), cut=False,
        bend=lambda x, y: 16 * np.sin(x / 150 + y / 41) + 9 * np.sin(x / 61 - y / 23),
        density=field_density)
# the path: a soft trough; its far edge is a broken ridge, its near side holds a little shadow
tg = np.gradient(P, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True); nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
halfw = np.linspace(12, 34, len(P))[:, None]
L.clear(L.poly(list(P - nr * halfw) + list((P + nr * halfw)[::-1])), chatter=0.25, angle=20)
for a, b in ((0.04, 0.3), (0.36, 0.62), (0.68, 0.98)):
    i0, i1 = int(a * len(P)), int(b * len(P))
    L.gouge(P[i0:i1:3] - nr[i0:i1:3] * (halfw[i0:i1:3] + 2), 2.6, 'v', cut=False, smooth=False)
L.hatch(L.poly(list(P + nr * (halfw * 0.35)) + list((P + nr * halfw)[::-1])), angle=24, spacing=7, width=2.0,
        dash=(6, 16), gap=(5, 18), cut=False, density=lambda x, y: 0.55)


def post(x, y, h, lean=0.0):
    w = 7 + h * 0.06
    pts = [(x - w / 2, y), (x - w / 2 + lean, y - h), (x + w / 2 + lean, y - h), (x + w / 2, y)]
    L.leave(pts)
    L.clear(L.poly([(x - w / 2 + lean + 1.5, y - h + 1), (x + lean, y - h - 6), (x + w / 2 + lean - 1.5, y - h + 1),
                    (x + w / 2 + lean - 1.5, y - h + 5), (x - w / 2 + lean + 1.5, y - h + 5)]), chatter=0)
    L.gouge([(x - w / 2 + lean - 1, y - h + 1), (x + lean, y - h - 7), (x + w / 2 + lean + 1, y - h + 1)], 1.8, 'knife', cut=False)
    # moon shadow falls to the lower left
    L.hatch([(x - w / 2, y), (x + w / 2, y), (x - h * 0.9, y + h * 0.22), (x - h * 0.9 - w, y + h * 0.2)], angle=-14,
            spacing=4.5, width=2.0, dash=(8, 30), gap=(2, 6), cut=False)


posts = [(1760, 792, 70), (1650, 764, 62), (1548, 740, 55), (1452, 720, 49), (1362, 704, 43), (1280, 692, 38), (1204, 682, 34)]
for (x, y, h), (x2, y2, h2) in zip(posts[:-1], posts[1:]):
    for f in (0.35, 0.7):
        L.gouge(spline([(x, y - h * f), ((x + x2) / 2, (y - h * f + y2 - h2 * f) / 2 + 4), (x2, y2 - h2 * f)], 6), 2.6, 'brush',
                end=2.2, cut=False, smooth=False)
for x, y, h in posts:
    post(x, y, h, lean=rng.uniform(-3, 3))
L.stage('field', blocks=KEY)

# ---- 6. the bare tree, the walker with sled and lantern, the dog; prints in the snow; falling snow
L.bare_tree(262, 912, 730, lean=-0.07, spread=0.95, width=50, depth=6, halo=3.0, seed=7)
L.hatch([(225, 912), (300, 912), (170, 940), (90, 940)], angle=-10, spacing=5, width=2.2, dash=(10, 40), gap=(2, 8),
        cut=False)                                                          # the trunk's moon shadow

# tracks first, so the sled and walker stand on them: runner tracks and boot prints come in from the lower right
trk = [(1556, 902), (1610, 914), (1660, 930)]
TP = spline(trk, 20); tt = np.gradient(TP, axis=0); tt /= np.linalg.norm(tt, axis=1, keepdims=True); tn = np.stack([-tt[:, 1], tt[:, 0]], 1)
for side in (-10, 10):
    L.gouge(TP + tn * side, 2.4, 'brush', end=3.4, cut=False, smooth=False)
L.footprints([(1236, 868), (1320, 884), (1400, 900), (1460, 930)], step=27, size=7.5, side=7, start=0.12)

# the sled, seen a little from behind: a pile of split logs whose cut ends face us
sx0, sx1, sy = 1400, 1550, 898
L.outline(L.mask_of([L.stroke([(sx1 + 6, sy), (sx0 + 12, sy), (sx0 - 6, sy - 6), (sx0 - 10, sy - 20), (sx0 - 2, sy - 26)], 4.5, 'brush', end=3.5)]), 2.0)
L.gouge([(sx1 + 6, sy), (sx0 + 12, sy), (sx0 - 6, sy - 6), (sx0 - 10, sy - 20), (sx0 - 2, sy - 26)], 4.5, 'brush', end=3.5, cut=False)
for xx in (sx0 + 22, sx0 + 70, sx1 - 14):
    L.gouge([(xx, sy), (xx + 1, sy - 13)], 5.0, 'knife', cut=False, smooth=False)
L.leave([(sx0 + 2, sy - 19), (sx1 + 8, sy - 19), (sx1 + 8, sy - 12), (sx0 + 2, sy - 12)])
R = 13.0
ends = [(sx1 - 52, sy - 32), (sx1 - 26, sy - 32), (sx1, sy - 32), (sx1 - 39, sy - 54), (sx1 - 13, sy - 54), (sx1 - 26, sy - 76)]
bodies = [L.stroke([(cx - 104 + 6 * (cy < sy - 60), cy), (cx, cy)], 2 * R, 'knife') for cx, cy in ends]
ovals = [np.array([(ex + R * 0.82 * np.cos(t), ey + R * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 28)], np.float32) for ex, ey in ends]
pile = L.mask_of(bodies + ovals)
L.outline(pile, 2.4)
L.leave(pile)
for cx, cy in ends:                                                         # bark: long V cuts along the logs
    for f in (-0.45, 0.1):
        a = cx - 100 + rng.uniform(0, 26); b = cx - rng.uniform(16, 40)
        L.gouge([(a, cy + f * R), (b, cy + f * R + rng.uniform(-1.5, 1.5))], 1.8, 'v', smooth=False)
for cx, cy in ends:                                                         # end grain: rings and a check
    L.clear(L.poly([(cx + (R - 2.4) * 0.82 * np.cos(t), cy + (R - 2.4) * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 28)]), chatter=0)
    L.rings(cx + 0.5, cy, [R * 0.28, R * 0.55], width=1.5, cut=False, arc=(1.6, 3.4), gap=(0.15, 0.5), squash=1.2)
    a = rng.uniform(0, 2 * np.pi)
    L.gouge([(cx, cy), (cx + np.cos(a) * R * 0.66, cy + np.sin(a) * R * 0.8)], 1.5, 'knife', cut=False, smooth=False)
L.gouge(spline([(sx0 + 40, sy - 92), (sx0 + 60, sy - 50), (sx0 + 74, sy - 16)], 8), 2.4, 'knife', cut=False)  # lashing

# the walker: hooded coat, leaning into the pull; lantern held out ahead, rope in the back hand
wx, wy, K = 1236, 872, 1.1
F = lambda pts: [(wx + x * K, wy + y * K) for x, y in pts]
coat = F([(-20, -176), (-6, -186), (10, -184), (20, -170), (20, -152), (24, -128), (32, -80), (44, -30), (24, -24), (0, -22),
          (-22, -24), (-40, -30), (-30, -80), (-24, -128), (-26, -150), (-28, -164)])
legs = [F([(-10, -30), (-22, -14), (-32, -2)]), F([(14, -30), (22, -14), (32, -4)])]
arm_f = F([(-12, -146), (-34, -124), (-56, -112)])
arm_b = F([(12, -144), (26, -118), (38, -98)])
parts = [np.array(spline(coat + [coat[0]], 6), np.float32)]
parts += [L.stroke(lg, 12 * K, 'brush', end=10 * K) for lg in legs]
parts += [L.stroke(arm_f, 12 * K, 'brush', end=9 * K), L.stroke(arm_b, 12 * K, 'brush', end=9 * K)]
parts += [np.array(F([(-48, 0), (-24, 0), (-24, -10), (-38, -10)]), np.float32), np.array(F([(22, -1), (44, 0), (40, -11), (26, -12)]), np.float32)]
scarf = F([(-12, -150), (-30, -154), (-48, -150), (-64, -156)])
parts.append(L.stroke(scarf, 13 * K, 'brush', end=8 * K))
wm = L.mask_of(parts)
L.outline(wm, 2.6)
L.leave(wm)
L.clear(L.poly(F([(-11, -177), (-20, -177), (-24, -171), (-29, -166), (-24, -163), (-23, -159), (-18, -156), (-11, -158)])), chatter=0)  # face in the hood
L.leave(L.disc(*F([(-19, -170)])[0], 1.8))                                                                     # eye
L.gouge(F([(-6, -182), (8, -170), (12, -150)]), 2.8, 'v', smooth=True)                                    # hood seam
for u in (-30, -42, -54):                                                                                # scarf stripes
    L.gouge(F([(u + 2, -160), (u - 1, -146)]), 3.2, 'v', smooth=False, taper=(0.2, 0.2))
for u in (-60, -64, -68):                                                                                # fringe
    L.gouge(F([(-62, -156), (u - 10, -160 + (u + 64) * 0.9)]), 2.0, 'brush', end=1.0, cut=False, smooth=False)
L.gouge(F([(-24, -100), (24, -98)]), 3.0, 'u', smooth=False, taper=(0, 0.15))                              # belt
for k, (a, b) in enumerate((((-16, -92), (-30, -32)), ((-2, -92), (-6, -30)), ((12, -92), (24, -34)), ((22, -128), (14, -104)))):
    L.gouge(F([a, b]), 2.4, 'v', smooth=False)
# lantern on a short bail from the front hand
lx, ly = wx - 58 * K, wy - 80 * K
L.gouge([F([(-56, -112)])[0], (lx, ly - 22)], 2.0, 'knife', cut=False, smooth=False)
lant = [(lx - 10, ly - 18), (lx + 10, ly - 18), (lx + 8, ly + 16), (lx - 8, ly + 16)]
L.outline(L.poly(lant), 2.4)
L.leave(lant)
L.leave([(lx - 5, ly - 24), (lx + 5, ly - 24), (lx + 10, ly - 18), (lx - 10, ly - 18)])
L.clear(L.rect(lx - 6, ly - 13, lx - 1, ly + 11), chatter=0); L.clear(L.rect(lx + 1, ly - 13, lx + 6, ly + 11), chatter=0)
# rope from the back hand to the sled's nose
L.gouge(spline([F([(38, -98)])[0], (wx + 70, wy - 60), (sx0 - 18, sy - 34), (sx0 - 2, sy - 26)], 10), 2.2, 'knife', cut=False)
# shadows on the snow, thrown down-left by the moon
L.hatch([(wx - 44, wy), (wx + 44, wy), (wx - 160, wy + 36), (wx - 230, wy + 32)], angle=-12, spacing=4.5, width=2.0,
        dash=(10, 40), gap=(2, 7), cut=False)
L.hatch([(sx0, sy + 2), (sx1 + 8, sy + 2), (sx1 - 60, sy + 28), (sx0 - 90, sy + 26)], angle=-12, spacing=4.5, width=2.0,
        dash=(10, 40), gap=(2, 7), cut=False)

# the dog, run out from the open door to meet them; paw prints lead back to the door
dx, dy = 1030, 752
dog = [(dx - 30, dy - 22), (dx - 10, dy - 27), (dx + 14, dy - 26), (dx + 24, dy - 32), (dx + 30, dy - 42), (dx + 38, dy - 38),
       (dx + 44, dy - 32), (dx + 52, dy - 28), (dx + 46, dy - 22), (dx + 34, dy - 20), (dx + 24, dy - 10), (dx + 4, dy - 9),
       (dx - 20, dy - 9), (dx - 32, dy - 14)]
dparts = [np.array(spline(dog + [dog[0]], 5), np.float32)]
dparts += [L.stroke(p, 5.5, 'brush', end=4.5) for p in ([(dx + 22, dy - 12), (dx + 34, dy - 4), (dx + 44, dy - 2)],
                                                       [(dx + 14, dy - 12), (dx + 18, dy + 2)],
                                                       [(dx - 18, dy - 12), (dx - 34, dy - 2), (dx - 44, dy + 2)],
                                                       [(dx - 24, dy - 12), (dx - 22, dy + 3)],
                                                       [(dx - 30, dy - 20), (dx - 44, dy - 32), (dx - 46, dy - 44)])]
dparts.append(np.array([(dx + 32, dy - 40), (dx + 30, dy - 52), (dx + 38, dy - 42)], np.float32))     # ear up
L.leave(L.mask_of(dparts))
L.jab(dx + 36, dy - 34, 2.4, angle=0)
L.hatch([(dx - 34, dy), (dx + 40, dy), (dx - 40, dy + 16), (dx - 100, dy + 14)], angle=-12, spacing=4.5, width=2.0,
        dash=(10, 30), gap=(2, 7), cut=False)
L.footprints([(home['door'][0] + 27, 700), (860, 718), (960, 740), (1000, 752)], step=20, size=3.6, side=4, paws=True, start=0.05, stop=0.95)

# falling snow over everything still black
busy = np.clip(wm + pile + L.mask_of(dparts) + L.disc(lx, ly, 26), 0, 1)                # keep flakes off faces and props
L.speckle(np.clip(L.rect(BX0, BY0, BX1, BY1) - (busy > 0.01), 0, 1), n=1700, size=(1.8, 4.6),
          angle=205, stars=0.012)
L.stage('figures', blocks=KEY)

# ---- 7. the colour block: lantern glow, the spill of light from the door (windows were left on it already)
glow = L.disc(lx, ly, 58)
L.leave(glow, on=lamp)
for k in range(18):
    a = 2 * np.pi * k / 18 + rng.uniform(-0.05, 0.05)
    L.gouge([(lx + np.cos(a) * 18, ly + np.sin(a) * 18), (lx + np.cos(a) * 62, ly + np.sin(a) * 62)], 4.5, 'v',
            on=lamp, smooth=False)
d0, dtop, d1, dbase = home['door']
far = [(d1 + 64 - (d1 - d0 + 120) * f, dbase + 96 + 8 * np.sin(f * 9) + rng.uniform(-5, 5)) for f in np.linspace(0, 1, 9)]
L.leave(L.poly([(d0 + 2, dbase), (d1 - 2, dbase)] + far), on=lamp)
L.hatch([(d0 - 70, dbase + 30), (d1 + 90, dbase + 30), (d1 + 90, dbase + 112), (d0 - 70, dbase + 112)], angle=-4, spacing=11,
        width=4.5, dash=(14, 50), gap=(16, 50), tool='u', on=lamp, density=lambda x, y: np.clip((y - 700) / 70, 0.15, 1))
L.stage('colour')

# ---- 8. pencil and chop
L.sign('7/30', 'Homeward, First Snow', 'E. Vintersol  2026', y=BY1 + 54)
L.chop(BX1 - 18, BY1 + 92, size=30, seed=4)

img = L.save(out, stages)
print(f'{out}  {time.time() - t0:.1f}s')
