"""Example (stained glass / 彩色玻璃花窗): 四季之窗 · Window of the Seasons — four Gothic lancets in a stone wall,
lit by daylight from behind. Every light shows the same tree (the same trunk and boughs) in one season, and the
sun stands at a different height in each: highest in summer, level at the two equinoxes, low behind bare
branches in winter. The birds tell the year: swallows arrive in spring, a nest of chicks in summer, geese leave
in a V in autumn, a robin stays through the snow. Latin names in the label bands (VER, AESTAS, AVTVMNVS, HIEMS).
Pot-metal glass with streaks and seeds, grisaille trace lines and stippled matt, leaves scratched out of the
matt, silver stain, lead came with soldered joints, saddle bars, a mended crack, coloured light on the reveals
and the sill.
Draw-on stages: stone -> cutline cartoon -> glass -> trace -> matt and stain -> lead -> iron -> daylight.
No image model.
python3 stainedglass_seasons.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from stainedglass import StainedGlass

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'stainedglass_seasons.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

g = StainedGlass(1920, 1080, seed=4, record=bool(stages), ambient=0.08)
rng = np.random.default_rng(12)
g.wall('#8e8474', '#6b6358')

TOP, BOT, WID = 64, 930, 330
CX = [342, 754, 1166, 1578]
lights = [g.lancet(cx, TOP, BOT, WID, splay=28, sill=44, hood=14) for cx in CX]
g.string_course(BOT + 44, 24)
g.stage('stone')

BORDER, FILLET = 30, 42                               # sdf bands: border 0..30, white fillet 30..42, field beyond
LABEL_Y = (770, 824)                                  # label band (local y)
GROUND_Y = 700

SEASONS = [
    dict(name='VER', sky=['#6f9ed6', '#5c8ccc', '#7aa8dc'], sun=(-46, 250, 26), border=['#4e9a3c', '#e6e0cc'],
         ground=['#6aae3e', '#7cbc48', '#5a9a36'], crown=['#a6d05a', '#8fc24c', '#bcd96e', '#9ccd52'], lobe=0.8),
    dict(name='AESTAS', sky=['#2456b0', '#1d4aa0', '#2b61bd'], sun=(0, 150, 30), border=['#b3182c', '#f2c230'],
         ground=['#3c8a34', '#2f7a2e', '#4a9a3a'], crown=['#2f8a3c', '#3f9c45', '#257034', '#4aa040'], lobe=1.0),
    dict(name='AVTVMNVS', sky=['#3a4fa2', '#33459a', '#4558ae'], sun=(46, 250, 26), border=['#e0922a', '#7a2c5c'],
         ground=['#9a6a2a', '#8a5a24', '#a87a34'], crown=['#e0922a', '#d0601e', '#e8b830', '#b8401e'], lobe=0.92),
    dict(name='HIEMS', sky=['#8fa9cc', '#9db4d4', '#839fc6'], sun=(-52, 404, 24), border=['#3a64b0', '#e8ecef'],
         ground=['#eef1f2', '#dfe8ef', '#cddcea'], crown=None, lobe=0),
]

# the one tree, in local coordinates (ly down from the apex), shared by all four lights.
# Glass can only be cut so thin: the trunk and main boughs are cut glass, everything thinner is painted.
TRUNK = [(0, 730), (-4, 682), (2, 634), (-2, 594)]
CUT_BOUGHS = [([(-4, 604), (-30, 572), (-54, 548), (-80, 530), (-100, 506)], 27, 16),     # left
              ([(4, 600), (32, 566), (62, 546), (86, 518), (98, 492)], 26, 16),           # right
              ([(-2, 598), (-9, 548), (-4, 500), (4, 462)], 23, 16)]                      # leader
PAINTED = [([(-100, 506), (-110, 486), (-114, 462)], 9, 3),
           ([(98, 492), (106, 468), (108, 440)], 9, 3),
           ([(4, 462), (8, 430), (2, 396), (-4, 372)], 10, 3),
           ([(-7, 528), (-30, 496), (-50, 462), (-60, 424)], 10, 3),
           ([(0, 486), (24, 458), (44, 428), (52, 394)], 9, 3),
           ([(-40, 556), (-64, 576), (-92, 586)], 7, 2.5),
           ([(48, 554), (78, 568), (104, 570)], 7, 2.5)]
NEST = [(18, 432), (82, 432), (74, 452), (50, 460), (26, 452)]
CHICKS = [(24, 433), (26, 420), (34, 414), (42, 420), (46, 414), (54, 410), (62, 416), (68, 414), (76, 420), (78, 433)]
LOBES = [(-84, 476, 46), (-46, 420, 54), (14, 392, 56), (70, 420, 50), (90, 486, 36), (-62, 536, 44),
         (56, 528, 46), (-4, 470, 56)]


def twigs(p, ang, length, width, depth, out):
    """a little recursive tree of painted twigs"""
    q = (p[0] + np.cos(ang) * length, p[1] + np.sin(ang) * length)
    mid = ((p[0] + q[0]) / 2 + rng.normal(0, length * 0.07), (p[1] + q[1]) / 2 + rng.normal(0, length * 0.07))
    out.append(([p, mid, q], width))
    if depth > 0:
        for da in (-0.5, 0.45):
            twigs(q, ang + da + rng.normal(0, 0.18), length * rng.uniform(0.58, 0.74), width * 0.66, depth - 1, out)


def _place(L, pts, x, y, s, flip, rot):
    P = np.asarray(pts, np.float32) * s
    if flip: P[:, 0] *= -1
    c, sn = np.cos(rot), np.sin(rot)
    return L.P(P @ np.array([[c, sn], [-sn, c]], np.float32) + [x, y])


def swallow(L, x, y, s=1.0, flip=False, rot=0.0):
    """a swallow seen from below: scythe-curved wings swept back, short body, deeply forked tail"""
    from core import spline as sp
    up = [(6, -3), (3, -12), (-4, -24), (-16, -36), (-32, -46), (-22, -32), (-14, -20), (-9, -9), (-8, -3)]
    lo = [(px, -py) for px, py in up[::-1]]
    body = [(20, 0), (17, -4), (8, -5), (-8, -4), (-14, -3), (-36, -14), (-24, 0), (-36, 14), (-14, 3), (-8, 4), (8, 5), (17, 4)]
    m = 0
    for part in (up, body, lo):
        P = sp(part + [part[0]], 6) if part is not body else np.asarray(part, np.float32)
        m = m + g.poly(_place(L, P, x, y, s, flip, rot))
    return np.clip(m, 0, 1)


def leaf_pts(cx, cy, ang, ln, wd, n=30):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    u = np.cos(t) * ln / 2
    v = np.sin(t) * wd / 2 * (1 - 0.35 * np.cos(t))         # a pointed tip
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([cx + u * c - v * s, cy + u * s + v * c], 1)


def lobe_masks(L, lobes, field):
    return [g.blob(*L.pt(x, y), r, r * 0.93, rough=0.1, seed=sd) * field for (x, y, r, sd) in lobes]


def wood_mask(L, field):
    m = g.branch(L.P(TRUNK), 46, 30) + g.poly(L.P([(-32, 731), (-18, 700), (18, 700), (32, 731), (0, 737)]))
    for pts, w0, w1 in CUT_BOUGHS:
        m = np.maximum(m, g.branch(L.P(pts), w0, w1))
    return np.clip(m, 0, 1) * field


paint = []                                           # painting jobs, done after all the glass is cut
for L, S in zip(lights, SEASONS):
    field = L.inner(FILLET)
    # ---- sky: a mosaic of blues
    g.glass(field, S['sky'], cell=46, streak=0.6)
    sx, sy, sr = S['sun']
    scx, scy = L.pt(sx, sy)
    # ---- the sun: a disc of yellow with cut rays of gold and amber
    nr = 12
    for k in range(nr):
        a = k * 2 * np.pi / nr + 0.13
        tip = sr * (2.05 if k % 2 == 0 else 1.62)
        ray = [(scx + np.cos(a - 0.21) * sr * 0.9, scy + np.sin(a - 0.21) * sr * 0.9), (scx + np.cos(a) * tip, scy + np.sin(a) * tip),
               (scx + np.cos(a + 0.21) * sr * 0.9, scy + np.sin(a + 0.21) * sr * 0.9)]
        g.glass(g.poly(ray) * field, '#f0b02a' if k % 2 == 0 else '#f6d24a', streak=0.4)
    g.glass(g.circle(scx, scy, sr) * field, '#f3cf4a' if S['name'] != 'HIEMS' else '#f4e3a0', streak=0.3, seeds=0.6)
    # ---- ground: a wavy band of pieces
    gx = np.linspace(-130, 130, 9)
    gy = GROUND_Y + 10 * np.sin(gx / 40 + CX.index(L.cx)) - 6 * np.cos(gx / 23)
    ground = g.poly(L.P(np.vstack([np.stack([gx, gy], 1), [(130, LABEL_Y[0]), (-130, LABEL_Y[0])]]))) * field
    g.glass(ground, S['ground'], cell=42, streak=0.5, aspect=1.6)
    if S['name'] == 'HIEMS':                         # snow drifts: blue shadows lying in the hollows
        for (dx, dy, rx, ry) in [(-84, 748, 46, 13), (74, 744, 52, 12), (0, 763, 66, 8)]:
            g.glass(g.ellipse(*L.pt(dx, dy), rx, ry) * ground, '#b9cde4', streak=0.3)
    # ---- trunk and main boughs, cut in brown glass
    wood = wood_mask(L, field)
    g.glass(wood, ['#6e4526', '#7a4e2c', '#62401f'], cell=62, aspect=1.8, angle=np.pi / 2, streak=0.5, streak_dir=np.pi / 2)
    if S['name'] == 'HIEMS':                         # snow lying on the upper half of the two side boughs
        for pts, w0, w1 in CUT_BOUGHS[:2]:
            P = np.asarray(pts, np.float32)
            up = g.branch(L.P(P[1:] + [0, -6]), w0 * 0.9, w1 * 0.9)          # snow bulges a little above the bough
            down = g.branch(L.P(P[1:] + [0, 8]), w0 * 0.9, w1)
            g.glass(np.clip(up - down, 0, 1) * field, '#f1f2ee', streak=0.3)
    # ---- crown: one area of mixed greens (or golds), cut into small pieces; lobes are modelled in paint later
    lobes = []
    if S['crown']:
        keep = range(len(LOBES)) if S['name'] != 'AVTVMNVS' else [0, 1, 2, 3, 5, 6, 7]
        for i in sorted(keep, key=lambda i: LOBES[i][1]):          # back (high) to front (low)
            x, y, r = LOBES[i]
            r *= S['lobe']
            lobes.append((x, y, r, 500 + 10 * len(lobes) + CX.index(L.cx)))      # keep the seed, rebuild the mask later
        crown = np.clip(sum(lobe_masks(L, lobes, field)), 0, 1)
        g.glass(crown, S['crown'], cell=30, streak=0.5, vary=1.2)
    # ---- the season's birds and fruit, in glass
    details = []
    if S['name'] == 'VER':
        blossom = [(-80, 446), (-44, 400), (-10, 432), (24, 386), (60, 410), (84, 470), (-90, 500), (-52, 470),
                   (18, 470), (50, 500), (-24, 520), (-66, 548), (64, 540), (0, 396), (40, 440), (-30, 452)]
        for k, (x, y) in enumerate(blossom):
            g.glass(g.circle(*L.pt(x, y), 11) * field, '#ef9ab8' if k % 3 else '#f2ece0', streak=0.2, seeds=0.4)
            details.append(('blossom', x, y))
        for (x, y, s, fl, rt) in [(38, 156, 1.1, False, -0.25), (64, 334, 0.85, False, -0.1)]:
            g.glass(swallow(L, x, y, s, fl, rt) * field, '#1c2a58', streak=0.3)
            details.append(('swallow', x, y, s, fl, rt))
        for x in (-96, -40, 30, 92):                 # daisies in the grass
            y = 742 + (x % 3) * 6
            g.glass(g.circle(*L.pt(x, y), 9) * field, '#f2ece0', streak=0.2)
            details.append(('flower', x, y))
    if S['name'] == 'AESTAS':
        for (x, y) in [(-80, 452), (-40, 516), (-8, 420), (36, 454), (80, 494), (-92, 530), (16, 540), (56, 396), (-52, 410)]:
            g.glass(g.circle(*L.pt(x, y), 11) * field, '#b3182c', streak=0.6, flashed=True)
            details.append(('apple', x, y))
        nest = g.poly(L.P(NEST)) * field
        chicks = g.poly(L.P(CHICKS)) * field
        g.glass(chicks, '#e9dfb8', streak=0.2)
        g.glass(nest, '#7a4a24', streak=0.6, streak_dir=0.0)
        g.glass(swallow(L, 84, 350, 0.85, True, 0.3) * field, '#1c2a58', streak=0.3)   # a parent flying back to the nest
        details.append(('nest',))
    if S['name'] == 'AVTVMNVS':
        falling = [(-96, 614, 0.6), (-60, 654, -0.9), (86, 622, 1.2), (98, 352, 0.3), (-96, 364, -0.5), (60, 672, 0.4)]
        pile = [(-72, 716, 0.2), (-46, 724, -0.5), (-20, 716, 0.9), (36, 720, -0.2), (64, 712, 0.6), (90, 724, -0.8),
                (-98, 728, 0.4)]
        for k, (x, y, a) in enumerate(falling + pile):
            col = ['#e0922a', '#d0601e', '#e8b830', '#b8401e'][k % 4]
            g.glass(g.poly(leaf_pts(*L.pt(x, y), a, 30, 15)) * field, col, streak=0.4)
            details.append(('leaf', x, y, a))
    if S['name'] == 'HIEMS':
        rx_, ry_ = 50, 522                           # a robin perched on the right bough
        body = g.blob(*L.pt(rx_, ry_), 24, 17, rough=0.04) + g.circle(*L.pt(rx_ + 19, ry_ - 13), 12) \
            + g.poly(L.P([(rx_ - 18, ry_ - 2), (rx_ - 44, ry_ + 8), (rx_ - 40, ry_ + 16), (rx_ - 14, ry_ + 11)]))
        body = np.clip(body, 0, 1) * field
        g.glass(body, '#7a5434', streak=0.4)
        g.glass(g.blob(*L.pt(rx_ + 16, ry_ - 1), 14, 15, rough=0.04) * body, '#d4502a', streak=0.4)
        details.append(('robin', rx_, ry_))
    # ---- label band (white glass, stained gold later, painted letters)
    band = g.poly(L.P([(-200, LABEL_Y[0]), (200, LABEL_Y[0]), (200, LABEL_Y[1] + 30), (-200, LABEL_Y[1] + 30)])) * field
    g.glass(band, '#ece6d2', streak=0.3)
    # ---- white fillet and the border
    g.glass(L.band(BORDER, FILLET), '#efeadb', sites=L.outline((BORDER + FILLET) / 2, 140), streak=0.3)
    bsites = L.outline(BORDER / 2 + 2, 40)
    g.glass(L.band(-2, BORDER), S['border'], sites=bsites, streak=0.5, flashed=S['border'][0] == '#b3182c')
    paint.append((L, S, lobes, details, bsites))

g.stage('cartoon', cartoon=True)
g.stage('glass')

# ================================================================== trace lines
for L, S, lobes, details, bsites in paint:
    lm = lobe_masks(L, lobes, L.inner(FILLET))
    sx, sy, sr = S['sun']
    scx, scy = L.pt(sx, sy)
    t = np.linspace(0, 2 * np.pi, 40)
    g.trace(np.stack([scx + (sr - 7) * np.cos(t), scy + (sr - 7) * np.sin(t)], 1), 2.2, taper=(0, 0))
    # bark: long wavering lines up the trunk and along the boughs
    for k in range(5):
        off = -15 + k * 7.5
        g.trace(L.P([(off * 0.95, 722), (off * 0.8 - 2, 672), (off * 0.62 + 1, 626), (off * 0.5, 596)]), 2.0, taper=(0.3, 0.4))
    for pts, w0, w1 in CUT_BOUGHS:
        g.trace(L.P(np.asarray(pts, np.float32) + [1, 3]), 1.8, taper=(0.3, 0.5))
    # painted branches and twigs, too thin to cut in glass (seen in full in winter, through gaps otherwise)
    if S['name'] in ('HIEMS', 'AVTVMNVS'):
        tw = []
        depth = 3 if S['name'] == 'HIEMS' else 2
        sky_clip = None if not lobes else 1 - np.clip(sum(lm), 0, 1)    # autumn: twigs only where the sky shows
        for pts, w0, w1 in PAINTED:
            P = np.asarray(pts, np.float32)
            g.trace(L.P(P), w0, taper=(0.02, 0.7), clip=sky_clip)
            d = P[-1] - P[-2]; a = np.arctan2(d[1], d[0])
            twigs(tuple(P[-1]), a, 22, w1 * 1.2, depth, tw)
            for j in range(1, len(P) - 1):
                twigs(tuple(P[j]), a + (0.9 if j % 2 else -0.9), 20, w1 * 1.3, depth - 1, tw)
        for p, w in tw:
            g.trace(L.P(p), max(w, 1.2), taper=(0.05, 0.9), clip=sky_clip)
    # crown: a scalloped line of leaf tips along the lower, shaded rim of every lobe that is in front
    for i, (x, y, r, _) in enumerate(lobes):
        later = np.clip(sum(lm[i + 1:]), 0, 1) if i + 1 < len(lobes) else 0
        th = np.linspace(-0.5, np.pi + 0.3, int(r * 3.6))
        rr = r * (0.96 + 0.07 * np.abs(np.sin(th * r / 7)))
        P = np.stack([x + rr * np.cos(th), y + rr * np.sin(th) * 0.93], 1)
        Q = L.P(P)
        vis = [(0 <= int(q[1]) < g.H and 0 <= int(q[0]) < g.W and (np.isscalar(later) or later[int(q[1]), int(q[0])] < 0.5)) for q in Q]
        run = []
        for q, v in zip(Q, vis):
            if v: run.append(q)
            elif len(run) > 3: g.trace(np.array(run), 2.2, taper=(0.3, 0.3), smooth=False, wobble=0); run = []
            else: run = []
        if len(run) > 3: g.trace(np.array(run), 2.2, taper=(0.3, 0.3), smooth=False, wobble=0)
        # a few painted leaves with midribs in the shadowed lower half
        for k in range(int(r / 9)):
            a = rng.uniform(0.2, 2.6); d = r * rng.uniform(0.45, 0.8)
            lx, ly = x + d * np.cos(a), y + d * np.sin(a) * 0.93
            if not np.isscalar(later) and later[int(L.pt(lx, ly)[1]), int(L.pt(lx, ly)[0])] > 0.5: continue
            ang = a + rng.normal(0, 0.5)
            Pl = leaf_pts(*L.pt(lx, ly), ang, 24, 11, 24)
            np.maximum(g.trace_a, g.poly(Pl) * 0.8, out=g.trace_a)
            c, s_ = np.cos(ang), np.sin(ang)
            g.scratch([L.pt(lx - 10 * c, ly - 10 * s_), L.pt(lx + 9 * c, ly + 9 * s_)], 1.3)
    for d in details:
        if d[0] == 'blossom':
            cx_, cy_ = L.pt(d[1], d[2])
            for k in range(5):
                a = k * 2 * np.pi / 5 + 0.3
                g.trace(np.array([(cx_ + 3 * np.cos(a), cy_ + 3 * np.sin(a)), (cx_ + 8 * np.cos(a), cy_ + 8 * np.sin(a))]), 1.5)
        elif d[0] == 'flower':
            cx_, cy_ = L.pt(d[1], d[2])
            g.trace(np.array([(cx_, cy_ + 8), (cx_ + 1, cy_ + 24)]), 2.2, taper=(0.1, 0.6))
            for k in range(6):
                a = k * 2 * np.pi / 6
                g.trace(np.array([(cx_ + 2.5 * np.cos(a), cy_ + 2.5 * np.sin(a)), (cx_ + 7 * np.cos(a), cy_ + 7 * np.sin(a))]), 1.3)
        elif d[0] == 'swallow':
            pass
        elif d[0] == 'apple':
            cx_, cy_ = L.pt(d[1], d[2])
            g.trace(np.array([(cx_ + 1, cy_ - 9), (cx_ + 4, cy_ - 17)]), 2.4, taper=(0.1, 0.5))
        elif d[0] == 'leaf':
            _, x, y, a = d
            c, s_ = np.cos(a), np.sin(a)
            cx_, cy_ = L.pt(x, y)
            g.trace(np.array([(cx_ - 14 * c, cy_ - 14 * s_), (cx_ + 12 * c, cy_ + 12 * s_)]), 1.8, taper=(0.1, 0.6))
            for j in (-1, 1):
                for u in (-5, 2):
                    g.trace(np.array([(cx_ + u * c, cy_ + u * s_), (cx_ + (u + 5) * c - j * 5 * s_, cy_ + (u + 5) * s_ + j * 5 * c)]), 1.1)
        elif d[0] == 'nest':
            for k in range(6):
                y0 = 436 + k * 4
                g.trace(L.P([(22 + k * 2, y0), (50, y0 + 3 + rng.normal(0, 1)), (78 - k * 2, y0)]), 1.4, taper=(0.2, 0.2))
            for (x, y) in [(34, 418), (54, 414), (70, 418)]:          # open beaks and eyes
                cx_, cy_ = L.pt(x, y)
                g.trace(np.array([(cx_ - 4, cy_ - 2), (cx_, cy_ - 9), (cx_ + 4, cy_ - 2)]), 1.6, smooth=False)
                g.trace(np.array([(cx_ - 3, cy_ + 3), (cx_ - 2.5, cy_ + 3.5)]), 2.6)
        elif d[0] == 'robin':
            _, x, y = d
            ex, ey = L.pt(x + 23, y - 16)
            g.trace(np.array([(ex, ey), (ex + 0.5, ey + 0.5)]), 3.8)
            g.trace(L.P([(x + 30, y - 15), (x + 39, y - 12), (x + 30, y - 9)]), 2.0, smooth=False)       # beak
            g.trace(L.P([(x - 16, y - 7), (x - 4, y - 11), (x + 6, y - 7)]), 1.7)                        # wing
            g.trace(L.P([(x - 14, y + 1), (x - 4, y - 2), (x + 4, y + 1)]), 1.4)
            for lx_ in (x - 2, x + 7):                                                                   # legs
                g.trace(L.P([(lx_, y + 15), (lx_ + 1, y + 24)]), 1.8, taper=(0.1, 0.1))
    if S['name'] == 'AVTVMNVS':                      # geese leaving in a V, painted on the sky
        for k in range(7):
            i = (k + 1) // 2
            side = 1 if k % 2 else -1
            x, y = -46 + i * 25, 112 + side * i * 17 + i * 17
            cx_, cy_ = L.pt(x, y)
            flap = 1 if k % 3 else -0.4
            g.trace(np.array([(cx_ - 15, cy_ - 8 * flap), (cx_ - 6, cy_ - 1), (cx_, cy_ + 1.5), (cx_ + 6, cy_ - 1),
                              (cx_ + 15, cy_ - 8 * flap)]), 2.8, taper=(0.3, 0.3))
            g.trace(np.array([(cx_ - 5, cy_ + 2), (cx_ + 5, cy_ + 0.5)]), 4.4, taper=(0.4, 0.2))
    # border: a painted lozenge with a dot on every piece
    ctr = np.array(L.pt(0, 520))
    for (x, y) in bsites:
        n_ = ctr - [x, y]; n_ /= np.linalg.norm(n_) + 1e-6
        p_ = np.array([-n_[1], n_[0]])
        c_ = np.array([x, y]) + n_ * 2
        lz = np.array([c_ + p_ * 9, c_ + n_ * 6, c_ - p_ * 9, c_ - n_ * 6, c_ + p_ * 9])
        g.trace(lz, 1.6, taper=(0, 0), smooth=False, wobble=0)
        g.trace(np.array([c_, c_ + 0.4]), 3.4)
    lx, ly = L.pt(0, (LABEL_Y[0] + LABEL_Y[1]) / 2 + 1)
    g.inscribe(S['name'], lx, ly, 34 if len(S['name']) < 7 else 29, spacing=1.0)
g.stage('trace')

# ================================================================== matt, sticklight, silver stain
for L, S, lobes, details, bsites in paint:
    field = L.inner(FILLET)
    sx, sy, sr = S['sun']
    scx, scy = L.pt(sx, sy)
    g.shade(wood_mask(L, field), offset=(10, 3), strength=0.6, soft=3)
    # crown: an overall matt, every lobe shaded toward the lower right, leaves scratched out on the lit side
    lm = lobe_masks(L, lobes, field)
    for i, (x, y, r, _) in enumerate(lobes):
        m = lm[i]
        later = np.clip(sum(lm[i + 1:]), 0, 1) if i + 1 < len(lobes) else 0
        vis = m * (1 - later)
        g.matt(vis, 0.3, soft=2)
        g.shade(m, offset=(r * 0.3, r * 0.36), strength=0.5, soft=6, clip=vis)
        for k in range(int(r * r / 150)):
            a = rng.uniform(np.pi * 0.9, np.pi * 1.85); d = r * np.sqrt(rng.uniform(0.05, 0.75))
            lx, ly = x + d * np.cos(a), y + d * np.sin(a)
            Pl = leaf_pts(*L.pt(lx, ly), a + rng.normal(0, 0.6), rng.uniform(13, 19), rng.uniform(6, 8), 16)
            g.scratch_mask(g.poly(Pl) * vis)
    # sky: a light matt badgered toward the edges of each light, so the middle reads brighter
    edge = np.clip(1 - g.circle(*L.pt(0, 470), 210), 0, 1)
    g.matt(field * edge, 0.16, soft=30)
    if S['name'] == 'HIEMS':                         # snowflakes scratched out of a thin matt on the sky
        sky_only = field * (1 - g.circle(scx, scy, sr * 2.2)) * (g.YY < L.top + GROUND_Y - 10) * (1 - wood_mask(L, field))
        g.diaper(sky_only, spacing=34, motif='flake', size=3.6, paint=0.22, jitter=1.0, width=1.5)
    if S['name'] == 'AESTAS':                        # a faint diaper of crosses on the summer sky
        sky_only = field * (1 - g.circle(scx, scy, sr * 2.2)) * (g.YY < L.top + 330)
        g.diaper(sky_only, spacing=30, motif='cross', size=3.4, paint=0.16, width=1.5)
    g.stain(g.circle(scx, scy, sr) * (1 - g.circle(scx, scy, sr * 0.55) * 0.6), 0.9 if S['name'] != 'HIEMS' else 0.45)
    for d in details:
        if d[0] == 'apple':
            cx_, cy_ = L.pt(d[1], d[2])
            g.matt(g.circle(cx_ + 3, cy_ + 3, 10), 0.45, soft=2)
            g.scratch([(cx_ - 6, cy_ - 2), (cx_ - 3, cy_ - 6)], 2.4)
        elif d[0] in ('blossom', 'flower'):
            g.stain(g.circle(*L.pt(d[1], d[2]), 3.2), 1.3)
        elif d[0] == 'robin':
            g.shade(g.blob(*L.pt(d[1], d[2]), 24, 17, rough=0.04), offset=(0, 9), strength=0.5, soft=3)
        elif d[0] == 'nest':
            g.matt(g.poly(L.P([(18, 444), (82, 444), (74, 452), (50, 460), (26, 452)])), 0.5, soft=2)
            g.stain(g.poly(L.P(CHICKS)), 0.5)
    # ground: darker toward the bottom; grass blades scratched out in spring and summer
    gm = field * (g.YY > L.top + GROUND_Y - 16) * (g.YY < L.top + LABEL_Y[0])
    g.matt(gm * np.clip((g.YY - (L.top + GROUND_Y)) / 70, 0, 1), 0.35, soft=4)
    if S['name'] in ('VER', 'AESTAS'):
        for k in range(26):
            x = rng.uniform(-118, 118); y = rng.uniform(GROUND_Y + 14, LABEL_Y[0] - 8)
            g.scratch(L.P([(x, y), (x + rng.normal(0, 2), y - rng.uniform(7, 13))]), 1.6)
    # label band: stained gold, a painted rule above and below the letters
    lb = g.poly(L.P([(-200, LABEL_Y[0]), (200, LABEL_Y[0]), (200, LABEL_Y[1]), (-200, LABEL_Y[1])])) * field
    g.stain(lb, 0.9)
    for yy in (LABEL_Y[0] + 7, LABEL_Y[1] - 7):
        g.trace(L.P([(-118, yy), (118, yy)]), 1.6, taper=(0.02, 0.02), smooth=False)
    # border: matt toward the outer edge, so the colours deepen into the stone
    g.matt(L.band(-2, BORDER) * np.clip(1 - (L.sdf() - 8) / 24, 0, 1), 0.3, soft=2)
g.stage('matt')

# ================================================================== lead, iron, a mended crack
w4 = lights[3]
g.crack([w4.pt(30, 236), w4.pt(52, 262), w4.pt(70, 300), w4.pt(84, 322)], mend=True)
g.lead(width=6.0, rim=9.0)
g.stage('lead')
for L in lights:
    for y in (286, 490, 694):
        g.saddle_bar(L, L.top + y, width=9)
g.stage('iron')
g.weather(grime=0.55, pits=0.6)
g.daylight(strength=1.0, spill=1.0, halation=1.0)
g.save(out, stages)
print('saved', out, f'{time.time() - t0:.1f}s')
