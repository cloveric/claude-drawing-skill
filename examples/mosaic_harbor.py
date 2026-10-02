"""Example (Roman floor mosaic): The Day's Catch / 港口渔获 — a harbour panel set in stone and glass tesserae.
A lighthouse burns on its mole, a fishing boat with an eye on its bow has hauled its net out on a pole, and an
octopus has reached up and pulled one fish back out through the mesh while three more escape below.
Gulls overhead. A tabula ansata reads CAPTVRA · DIEI / ET POLYPVS FVR ("the day's catch -- and the octopus,
a thief"). Black-and-white running-wave border with red corner diamonds. Figures in opus vermiculatum (rows
follow every outline and ring every eye), the ground in opus tessellatum with a halo round each figure, the sea
in wavy rows; then time: lost patches showing the sockets in the old bed, a settling crack, dirt in the joints.
No image model.
python3 mosaic_harbor.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from mosaic import Mosaic
from core import spline, blob_pts, blur

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'mosaic_harbor.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

W, H = 1920, 1080
m = Mosaic(W, H, seed=11, tile=13)
rng = m.rng
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

# ------------------------------------------------------------------ layout
BT = 10.0                                   # border stone
BP = BT + m.gap                             # border row pitch
F0 = 12 * BP                                # the field starts 12 border rows in
FX0, FY0, FX1, FY1 = F0, F0, W - F0, H - F0
field = m.rect(FX0, FY0, FX1, FY1)


def waterline(x):
    return 598 + 5 * np.sin(x / 52.0) + 3 * np.sin(x / 23.0 + 1.3)


sea = field * (YY >= waterline(XX))
sky = field * (YY < waterline(XX))
FIG = 7.5                                   # figure stones are smaller (vermiculatum)


def tf(pts, cx, cy, ang=0.0, flip=False):
    """local -> canvas: rotate (deg, ccw), optional mirror, translate"""
    P = np.asarray(pts, np.float32).copy()
    if flip: P[:, 0] = -P[:, 0]
    a = np.radians(ang); c, s = np.cos(a), np.sin(a)
    return np.stack([cx + P[:, 0] * c + P[:, 1] * s, cy - P[:, 0] * s + P[:, 1] * c], 1)


# ------------------------------------------------------------------ the cartoon: what the stones will copy
m.paint(np.ones((H, W), np.float32), 'white')
m.shade(sky, '#e6decb', '#ece5d4', (0, FY0), (0, 600))
m.shade(sea, 'sky', 'blue', (0, 600), (0, FY1), gamma=0.8)

# border: two outer white rows, two black, a band of running waves, one black row
yy_d = np.minimum(np.minimum(XX + 0.5, W - XX - 0.5), np.minimum(YY + 0.5, H - YY - 0.5))
m.paint((yy_d >= 2 * BP) & (yy_d < 4 * BP), 'black')
m.paint((yy_d >= 11 * BP) & (yy_d < 12 * BP), 'black')
WB0, WBH = 4 * BP, 7 * BP                   # wave band: offset from the edge and height
waves = []


def wave_parts(u0, period):
    """one running wave in band coordinates (u along the travel direction, v inward from the outer fillet, unit =
    band height): a solid body rising from the fillet, and a crest that curls forward round a white eye"""
    k = period / (1.5 * WBH)
    body = [(0.0, -0.12), (0.2, 0.04), (0.42, 0.26), (0.6, 0.55), (0.76, 0.74), (0.86, 0.66), (0.86, 0.44),
            (0.9, 0.22), (1.0, 0.06), (1.12, -0.12)]
    curl = [(0.62, 0.62), (0.8, 0.8), (1.0, 0.84), (1.16, 0.72), (1.22, 0.52), (1.14, 0.34), (1.0, 0.3),
            (0.92, 0.4), (0.96, 0.54), (1.06, 0.56)]
    f = lambda pts: [(u0 + x * k * WBH, y * WBH) for x, y in pts]
    return f(body), f(curl)


def band_to_canvas(side, u, v):
    if side == 0: return WB0 + WBH + u, WB0 + v                        # top, travelling right
    if side == 1: return W - WB0 - v, WB0 + WBH + u                    # right, travelling down
    if side == 2: return W - WB0 - WBH - u, H - WB0 - v                # bottom, travelling left
    return WB0 + v, H - WB0 - WBH - u                                  # left, travelling up


for side in range(4):
    length = (W if side % 2 == 0 else H) - 2 * (WB0 + WBH)
    n = int(round(length / (1.5 * WBH)))
    per = length / n
    for i in range(n):
        body, curl = wave_parts(i * per, per)
        body = [band_to_canvas(side, u, v) for u, v in body]
        curl = spline([band_to_canvas(side, u, v) for u, v in curl], 8)
        waves.append((body, curl))
corner_d = []
for cx, cy in ((WB0 + WBH / 2, WB0 + WBH / 2), (W - WB0 - WBH / 2, WB0 + WBH / 2),
               (W - WB0 - WBH / 2, H - WB0 - WBH / 2), (WB0 + WBH / 2, H - WB0 - WBH / 2)):
    r = WBH * 0.45
    corner_d.append(((cx, cy), m.poly_mask([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)])))
wave_mask = lambda w: np.clip(m.poly_mask(spline(w[0] + [w[0][0]], 5)) + m.band(w[1], WBH * 0.2, WBH * 0.12), 0, 1)
all_waves = np.zeros((H, W), np.float32)
for w in waves: all_waves = np.maximum(all_waves, wave_mask(w))
m.paint(all_waves, 'black')
for (cx, cy), dm in corner_d:
    m.paint(dm, 'red')

# --- lighthouse on its mole (left)
rocks = m.poly_mask(spline([(158, 652), (172, 612), (204, 590), (242, 576), (282, 569), (330, 565), (374, 572),
                            (412, 589), (440, 612), (452, 642), (428, 664), (370, 672), (290, 674), (210, 668), (158, 652)], 6))
m.shade(rocks, 'grey', 'slate', (300, 565), (300, 672))
tier1 = m.poly_mask([(232, 578), (368, 578), (359, 447), (241, 447)])
corn1 = m.poly_mask([(226, 449), (374, 449), (374, 434), (226, 434)])
tier2 = m.poly_mask([(250, 436), (350, 436), (344, 348), (256, 348)])
corn2 = m.poly_mask([(244, 350), (356, 350), (356, 336), (244, 336)])
tier3 = m.poly_mask([(264, 338), (336, 338), (332, 276), (268, 276)])
deck = m.poly_mask([(254, 278), (346, 278), (346, 264), (254, 264)])
flame = m.poly_mask(spline([(264, 266), (258, 236), (266, 212), (276, 226), (282, 196), (294, 168), (304, 194),
                            (314, 214), (324, 200), (338, 228), (336, 266)], 6))
inner_flame = m.poly_mask(spline([(282, 266), (280, 242), (290, 222), (298, 202), (306, 224), (318, 244), (318, 266)], 6))
tower = np.clip(tier1 + tier2 + tier3, 0, 1)
m.shade(tower, 'white', 'buff', (230, 0), (372, 0), gamma=1.6)
for c_ in (corn1, corn2, deck):
    m.shade(c_, 'ochre', 'brown', (230, 0), (372, 0))
m.shade(flame, 'gold', 'scarlet', (300, 266), (300, 180))
m.paint(inner_flame, 'gold')

# --- boat
hull_top = [(612, 530), (700, 541), (800, 547), (900, 547), (1000, 543), (1100, 535), (1176, 524)]
hull_bot = [(1196, 546), (1183, 580), (1150, 609), (1050, 631), (900, 640), (760, 632), (672, 612), (632, 586), (612, 556)]
hull = m.poly_mask(spline(hull_top + hull_bot + [hull_top[0]], 6))
m.shade(hull, 'brown', 'umber', (0, 535), (0, 640))
wale = m.band(spline([(618, 547), (700, 556), (800, 562), (900, 562), (1000, 558), (1100, 551), (1182, 541)], 6), 13)
m.paint(wale * hull, 'red')
stern = spline([(626, 548), (603, 506), (594, 462), (604, 426), (628, 410), (648, 420), (644, 442), (627, 442)], 8)
stern_m = m.band(stern, 22, 11)
m.shade(stern_m, 'brown', 'umber', (600, 400), (600, 550))
blade = m.ellipse(578, 664, 12, 30, rot=-28)
m.shade(blade, 'ochre', 'brown', (560, 640), (600, 690))
sail = m.poly_mask(spline([(770, 344), (880, 337), (992, 341), (1010, 382), (1012, 428), (996, 470), (940, 466),
                           (880, 470), (820, 474), (780, 476), (786, 430), (776, 386), (770, 344)], 5))
m.shade(sail, 'white', 'buff', (790, 0), (1012, 0), gamma=1.5)

# --- net on its pole, with fish piled in it
bag = m.poly_mask(spline([(1242, 495), (1222, 560), (1212, 630), (1224, 704), (1258, 758), (1302, 770), (1338, 742),
                          (1352, 690), (1346, 610), (1328, 530), (1302, 470), (1270, 482), (1242, 495)], 6))

FISH = {   # back, belly, fin colours; stripe; dark bars
    'bream': ('slate', 'white', 'grey', None, False),
    'mullet': ('red', 'rose', 'pink', 'yellow', False),
    'mackerel': ('teal', 'white', 'sky', None, True),
}


def fish(cx, cy, L, ang=0.0, kind='bream', flip=False, hh=0.36):
    """a fish in local coordinates (snout toward +x); returns its parts already painted into the cartoon"""
    Hh = L * hh
    t = np.linspace(0, 1, 36)
    xb = -0.32 * L + t * 0.82 * L
    hb = Hh / 2 * np.sin(np.pi * np.clip(t, 0, 1) ** 0.85) ** 0.7
    body_l = list(zip(xb, -hb)) + list(zip(xb[::-1], 0.9 * hb[::-1]))
    tail_l = [(-0.29 * L, -0.08 * Hh), (-0.5 * L, -0.46 * Hh), (-0.44 * L, 0.0), (-0.5 * L, 0.46 * Hh), (-0.29 * L, 0.08 * Hh)]
    dors_l = [(-0.1 * L, -0.36 * Hh), (0.0, -0.66 * Hh), (0.16 * L, -0.7 * Hh), (0.22 * L, -0.4 * Hh)]
    anal_l = [(-0.16 * L, 0.32 * Hh), (-0.08 * L, 0.58 * Hh), (0.06 * L, 0.36 * Hh)]
    back, belly, fin, stripe, bars = FISH[kind]
    tr = lambda p: tf(p, cx, cy, ang, flip)
    body = m.poly_mask(tr(body_l)); tail = m.poly_mask(tr(tail_l))
    fins = np.clip(m.poly_mask(tr(dors_l)) + m.poly_mask(tr(anal_l)) + tail, 0, 1)
    m.paint(fins, fin)
    p0, p1 = tr([(0, -0.5 * Hh)])[0], tr([(0, 0.48 * Hh)])[0]
    m.shade(body, back, belly, p0, p1, gamma=0.9)
    whole = np.clip(body + fins, 0, 1)
    eye = tr([(0.36 * L, -0.08 * Hh)])[0]
    gill = tr([(0.25 * L, -0.3 * Hh), (0.2 * L, -0.05 * Hh), (0.22 * L, 0.2 * Hh), (0.27 * L, 0.32 * Hh)])
    lines = []
    if stripe: lines.append((tr([(-0.26 * L, 0.0), (0.0, -0.02 * Hh), (0.24 * L, 0.02 * Hh)]), stripe))
    if bars:
        for bx in (-0.18, -0.06, 0.06):
            lines.append((tr([(bx * L, -0.42 * Hh), (bx * L + 0.04 * L, -0.12 * Hh)]), 'navy'))
    return dict(mask=whole, eye=eye, gill=gill, lines=lines, size=L)


net_fish = [fish(1284, 726, 118, 8, 'bream'), fish(1282, 652, 112, -18, 'mullet', flip=True)]
stolen = fish(1436, 680, 150, 22, 'mullet', flip=True)                  # pulled out through the mesh
free_fish = [fish(470, 790, 190, 4, 'mullet', flip=True), fish(760, 868, 160, -6, 'mackerel', flip=True),
             fish(276, 872, 150, 8, 'bream', flip=True)]

# --- the octopus: mantle, eyes, eight arms; the long one has wrapped round the stolen fish's tail
OX, OY = 1606, 736
mantle = m.ellipse(OX, OY, 54, 70, rot=-24)
m.shade(mantle, 'red', 'brick', (OX + 28, OY - 66), (OX - 22, OY + 64))
arms_p = [[(OX + x, OY + y) for x, y in a] for a in [
    [(-44, 56), (-78, 44), (-100, 16), (-110, -22), (-104, -56), (-90, -82), (-72, -88), (-66, -72), (-80, -64)],
    [(-40, 70), (-78, 104), (-100, 146), (-92, 174), (-66, 178), (-58, 158)],
    [(-14, 78), (-14, 128), (4, 164), (38, 172), (54, 154), (40, 142)],
    [(12, 72), (52, 104), (100, 118), (136, 102), (140, 76), (120, 72)],
    [(28, 56), (74, 58), (118, 38), (144, 6), (136, -22), (116, -18)],
    [(-56, 62), (-112, 76), (-150, 106), (-164, 146), (-142, 166), (-124, 150)],
    [(-26, 76), (-44, 122), (-40, 160), (-22, 182)],
]]
arms = []
for i, p in enumerate(arms_p):
    path = spline(p, 10)
    a = m.band(path, 22 if i == 0 else 20, 5)
    arms.append((path, a))
    m.shade(a, 'brick', 'pink', tuple(path[0]), tuple(path[-1]))
octo = np.clip(mantle + sum(a for _, a in arms), 0, 1)

# --- gulls
gulls = [(530, 300, 66, 6), (668, 236, 52, -8), (1530, 412, 58, 4)]


def gull_strokes(cx, cy, w, ang):
    L_ = tf([(-w / 2, -w * 0.05), (-w * 0.3, -w * 0.2), (-w * 0.1, -w * 0.12), (0, 0)], cx, cy, ang)
    R_ = tf([(0, 0), (w * 0.1, -w * 0.13), (w * 0.3, -w * 0.21), (w / 2, -w * 0.06)], cx, cy, ang)
    return [L_, R_]


# --- tabula ansata (top right)
TX0, TY0, TX1, TY1 = 1088, 172, 1614, 318

# ------------------------------------------------------------------ 1. sinopia: the design brushed on the wet bed
for msk in [rocks, tower, flame, hull, stern_m, sail, bag, mantle, blade] + [f['mask'] for f in net_fish + free_fish + [stolen]] + [a for _, a in arms]:
    m.sinopia(msk, width=3.2)
for w in waves[::2]: m.sinopia(pts=w[1][::4], width=3.0, strength=0.55)
m.sinopia(pts=[(880, 546), (880, 300)], width=3.0)
m.sinopia(pts=[(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1), (TX0, TY0)], width=2.6, strength=0.6)
m.sinopia(pts=[(FX0, 600), (FX1, 600)], width=2.4, strength=0.45)
for x in (FX0, FX1):
    m.sinopia(pts=[(x, FY0), (x, FY1)], width=2.4, strength=0.5)
for y in (FY0, FY1):
    m.sinopia(pts=[(FX0, y), (FX1, y)], width=2.4, strength=0.5)
m.stage('sinopia')

# ------------------------------------------------------------------ 2. the border
for w in waves:
    wm = wave_mask(w)
    m.line(w[1], 'black', BT * 0.9)
    m.outline(wm, 'black', 1, BT * 0.9)
    m.fill(wm, BT * 0.9, colour='black')
for (cx, cy), dm in corner_d:
    m.point(cx, cy, 'white', BT * 0.9, 'square', angle=45)
    m.outline(dm, 'black', 1, BT * 0.9)
    m.fill(dm, BT * 0.9, stones=['red', 'brick'])
band = ((yy_d >= WB0) & (yy_d < WB0 + WBH)).astype(np.float32)
m.halo(band, rows=1, size=BT, stones=['white', 'bone'], around=np.clip(all_waves + sum(d for _, d in corner_d), 0, 1))
m.frame(0, 0, W, H, 12 * BP, size=BT, stones=['white', 'bone', 'black'])
m.stage('border')

# ------------------------------------------------------------------ 3. eyes, details and outlines
def eye(x, y, s=FIG):
    m.point(x, y, 'black', s * 0.85, 'round')
    ring = m.ellipse(x, y, s * 1.6, s * 1.6)
    m.halo(ring, rows=1, size=s * 0.75, colour='white', around=m.ellipse(x, y, s * 0.5, s * 0.5))


# lighthouse: door, windows, masonry courses, flame tongues
m.line([(300, 576), (300, 540)], 'black', 9, across=16)
for wy in (488, 392, 306):
    m.line([(300, wy - 12), (300, wy + 12)], 'black', 8, across=10)
for y_ in (552, 526, 500, 474):
    m.line([(240, y_), (362, y_)], 'buff', 7, across=4.5, keep=0.6)
for y_ in (412, 384, 360):
    m.line([(256, y_), (346, y_)], 'buff', 7, across=4.5, keep=0.6)
for a_ in (28, 62, 118, 152):
    r0, r1 = 66, 104
    m.line([(300 + r0 * np.cos(np.radians(a_)), 222 - r0 * np.sin(np.radians(a_))),
            (300 + r1 * np.cos(np.radians(a_)), 222 - r1 * np.sin(np.radians(a_)))], 'gold', 8)
for p in ([(176, 646), (206, 616), (244, 606), (262, 630), (250, 662)], [(262, 630), (300, 618), (340, 628), (356, 664)],
          [(340, 628), (372, 600), (412, 604), (436, 630)], [(244, 606), (262, 580)], [(372, 600), (360, 574)]):
    m.line(p, 'black', 6, across=5)

# boat: oculus, planks, mast, yard, rigging, steering oar
eye(1124, 564, 8)
for off in (36, 62):
    pl = [(x_, y_ + off) for x_, y_ in [(640, 548), (720, 556), (820, 561), (920, 561), (1020, 557), (1110, 549), (1160, 543)]]
    m.line(pl, 'umber', 7, across=5)
m.line([(880, 548), (880, 302)], 'umber', 10, across=11)
m.line([(758, 340), (880, 330), (1002, 336)], 'umber', 9, across=9)
for x_, b_ in ((812, 4), (846, 8), (916, 12), (954, 14)):
    m.line([(x_, 350), (x_ + b_, 410), (x_ + b_ * 0.6, 464)], 'buff', 6, across=4.5)
m.line([(880, 306), (1170, 524)], 'slate', 6, across=5)
m.line([(880, 306), (640, 418)], 'slate', 6, across=5)
m.line([(652, 522), (616, 586), (590, 636)], 'brown', 8, across=9)
m.line(stern, None, 8)                                                    # spine row of the stern post
m.line([(1160, 532), (1230, 500), (1310, 466)], 'umber', 9, across=9)    # net pole

# net: the fish in it are set first and whole; the cords run between them and over the water behind
for f in net_fish:
    eye(*f['eye'], 6)
    m.line(f['gill'], 'umber', 5, across=4)
    for p, c in f['lines']: m.line(p, c, 5, across=4)
    m.outline(f['mask'], 'black', 1, 6)
    m.fill(f['mask'], 6.5)
bag_d = (bag > 0.5)
for k in range(-5, 7):
    for sgn in (1, -1):
        x_a = 1280 + k * 40
        p = np.array([(x_a + sgn * t_ * 0.75, 460 + t_) for t_ in np.linspace(0, 330, 120)])
        inside = bag_d[np.clip(p[:, 1].astype(int), 0, H - 1), np.clip(p[:, 0].astype(int), 0, W - 1)]
        if inside.sum() < 6: continue
        idx = np.nonzero(inside)[0]
        m.line(p[idx[0]:idx[-1] + 1], 'black', 5.5, across=3.8, smooth=False, keep=0.45)
bag_edge = spline([(1242, 495), (1222, 560), (1212, 630), (1224, 704), (1258, 758), (1302, 770), (1338, 742),
                   (1352, 690), (1346, 610), (1328, 530), (1302, 470)], 6)
m.line(bag_edge, 'umber', 6, across=6)

# octopus: eyes, suckers, spine rows of the arms, outline
eye(OX - 30, OY + 40, 9); eye(OX + 14, OY + 52, 9)
for i, (path, a) in enumerate(arms):
    n_ = len(path)
    for j in range(int(n_ * 0.08), int(n_ * 0.7), 5):
        p, q = path[j], path[min(j + 2, n_ - 1)]
        d = q - p; d /= np.linalg.norm(d) + 1e-6
        w_ = (22 - 17 * j / n_) * 0.28
        m.point(p[0] - d[1] * w_, p[1] + d[0] * w_, 'rose', 5.5, 'round')
    m.line(path, None, 6.5, stones=['brick', 'pink', 'red', 'rose'])
m.outline(octo, 'umber', 1, 6.5)
for sx, sy in ((OX + 16, OY - 40), (OX - 12, OY - 14), (OX + 28, OY + 2), (OX + 4, OY - 62)):
    m.point(sx, sy, 'umber', 6, 'round')

# free fish (and the stolen one), rocks, tower, hull, stern, sail, blade
for f in free_fish + [stolen]:
    eye(*f['eye'], 7)
    m.line(f['gill'], 'umber', 6, across=4.5)
    for p, c in f['lines']: m.line(p, c, 6, across=4.5)
    m.outline(f['mask'], 'black', 1, FIG * 0.95)
for msk, c in ((rocks, 'black'), (tower, 'umber'), (corn1, 'umber'), (corn2, 'umber'), (deck, 'umber'),
               (flame, 'red'), (hull, 'black'), (stern_m, 'black'), (blade, 'umber')):
    m.outline(msk, c, 1, FIG)
m.outline(sail, 'brown', 1, 6)
for gx, gy, gw, ga in gulls:
    for p in gull_strokes(gx, gy, gw, ga):
        m.line(p, 'slate', 6.5, across=6)
m.stage('outlines')

# ------------------------------------------------------------------ 4. fill the figures (colours from the cartoon)
for f in free_fish + [stolen]:
    m.fill(f['mask'], FIG)
m.fill(mantle * (1 - m.everything()), 7)
m.fill(octo, 6.5)
m.fill(inner_flame, 6, stones=['gold', 'yellow'])
for msk in (flame, corn1, corn2, deck, tower, rocks, sail, blade, stern_m, hull):
    m.fill(msk, FIG)
m.stage('figures')

# ------------------------------------------------------------------ 5. the inscription
m.tabula(TX0, TY0, TX1, TY1, [('CAPTVRA · DIEI', 44, 'black'), ('ET POLYPVS FVR', 31, 'red')], ear=58, size=8)
m.stage('inscription')

# ------------------------------------------------------------------ 6. halo, ground, sea
big = np.clip(rocks + tower + flame + hull + stern_m + sail + mantle + bag + m.poly_mask([(TX0 - 60, TY0), (TX1 + 60, TY0), (TX1 + 60, TY1), (TX0 - 60, TY1)]), 0, 1)
m.halo(sky, rows=1, size=11, stones=['white', 'bone'])
m.halo(sea, rows=1, size=11, stones=['pale', 'sky', 'blue'])
near_big = (blur(big, 9) > 0.08) * m.everything()                         # the big figures and their first ring
m.halo(sky, rows=1, size=11, stones=['white', 'bone'], around=near_big)
m.halo(sea, rows=1, size=11, stones=['pale', 'sky', 'blue'], around=near_big)
m.stage('halo')
m.rows(sky, size=12.5, wobble=6, stones=['white', 'bone', 'cream'])
m.stage('ground')
# water: dark wave strokes and white crests, then wavy rows
for wy in range(650, 930, 46):
    for k in range(9):
        x_ = FX0 + 60 + k * 190 + (wy * 7) % 120 + rng.uniform(-30, 30)
        pts = [(x_ + t_, wy + rng.uniform(-6, 6) + 7 * np.sin(t_ / 22.0)) for t_ in np.linspace(0, 120, 10)]
        if x_ + 130 > FX1: continue
        m.line(pts, 'navy', 8, across=6, keep=0.6)
for k in range(14):
    x_ = FX0 + 20 + k * 118 + rng.uniform(-10, 10)
    pts = [(x_ + t_, waterline(x_ + t_) + 13 + 4 * np.sin(t_ / 14.0)) for t_ in np.linspace(0, 70, 8)]
    if x_ + 80 > FX1: continue
    m.line(pts, 'white', 7, across=6, keep=0.6)
wav = YY - 7 * np.sin(XX / 38.0 + YY / 60.0)
m.rows(sea, size=11, field=wav, stones=['pale', 'sky', 'blue', 'navy', 'teal'])
m.stage('sea')

# ------------------------------------------------------------------ 7. two thousand years
m.lacuna(m.poly_mask(blob_pts(176, 984, 84, 52, rough=0.3, seed=4)))
m.lacuna(m.poly_mask(blob_pts(1912, 640, 40, 70, rough=0.3, seed=8)))
m.lacuna(m.poly_mask(blob_pts(1030, 900, 52, 30, rough=0.3, seed=9, rot=0.3)))
m.crack([(1004, 1080), (1012, 1010), (1046, 950), (1040, 890), (1078, 830), (1120, 790), (1136, 744)])
m.crack([(1920, 210), (1862, 236), (1808, 232), (1760, 262)])
m.patina(1.0)

print('laid', len(m.poly), 'stones in', round(time.time() - t0, 1), 's')
m.save(out, stages_dir=stages)
print('done', round(time.time() - t0, 1), 's')
