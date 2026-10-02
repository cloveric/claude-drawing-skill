"""Example (blueprint / 蓝图工程图): 灯塔剖面 · Halvard Rock Light — sheet 3 of 7 of a (fictional) 1911 lighthouse
contract set, inked on tracing linen and printed as a blueprint. Left: the south elevation (granite courses, the
cylinder shaded with denser lines toward its edge, a bronze ladder up to the entrance, two railed galleries, the lantern
with helical astragals and the lens seen through the glass) and section A-A on the same levels (dovetailed walls
thinning as they rise, a cistern in the base, 120 cantilevered stone steps winding round a hollow newel that is also
the tube for the clockwork weight, the watch room with the clockwork, the lantern with the lens on its rotating table).
Right: plan B-B through the stair at +6.50 with a north point, detail 1 that tells the small story of the drawing --
the lamp flame sits at the focal point, every prism bends its ray level, and the lens sends out one parallel beam --
general notes, graphic scales, revision and title blocks. Then the sheet's life: folded in six, the outside panel
faded and handled, an alkaline water stain, drawing-pin holes, and a site engineer's red pencil: he counted the steps.
Draw-on stages: sheet -> layout -> elevation -> section -> hatching -> plan -> detail -> dimensions -> lettering ->
folded and filed -> red pencil. No image model.
python3 blueprint_lighthouse.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from blueprint import Blueprint
from core import spline as _spl

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'blueprint_lighthouse.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

bp = Blueprint(1920, 1080, seed=11)

# ------------------------------------------------------------------ the tower, in metres
S, G = 19.0, 900.0                         # 1:200 -> 19 px per metre; rock datum +-0.00 at y = 900
EX, SX = 276.0, 682.0                      # axis of the elevation / of section A-A
Y = lambda h: G - h * S
RISE, PER_TURN, R_NEWEL, R_TUBE = 0.23, 14, 0.36, 0.26
BANDS = [(2.5, 9.0, 2.55), (9.0, 16.0, 2.40), (16.0, 23.0, 2.25), (23.0, 30.0, 2.05)]   # inner radius per band
WIN_R, WIN_L, WIN_FRONT = [6.5, 19.4], [12.9, 25.8], [9.7, 16.1, 22.6]


def Rs(h):                                 # shaft outer radius (straight taper)
    return 4.0 - 1.35 * (h - 2.5) / 26.1


def Rc(h):                                 # corbel under the gallery
    return 2.65 + 1.1 * ((h - 28.6) / 1.4) ** 2


def Rout(h):
    return Rs(h) if h <= 28.6 else Rc(min(h, 30.0))


def Rin(h):
    for a, b, r in BANDS:
        if a <= h < b: return r
    return BANDS[-1][2]


def profile():
    """right-hand silhouette (R, h), bottom to the ventilator neck"""
    pts = [(4.6, 0.0), (4.6, 2.2), (4.75, 2.2), (4.75, 2.5), (4.0, 2.5), (2.65, 28.6)]
    pts += [(Rc(h), h) for h in np.linspace(28.6, 30.0, 9)[1:]]
    pts += [(3.75, 30.35), (2.3, 30.35), (2.3, 33.0), (2.75, 33.0), (2.75, 33.3), (1.95, 33.3), (1.95, 37.0),
            (2.12, 37.0), (2.12, 37.25), (1.95, 37.25)]
    te = np.arccos(0.28 / 1.95)
    pts += [(1.95 * np.cos(t), 37.25 + 1.7 * np.sin(t)) for t in np.linspace(0, te, 16)[1:]]
    return pts + [(0.28, 39.05)]


def P(ax, pts, flip=False):
    return [(ax + (-r if flip else r) * S, Y(h)) for r, h in pts]


def silhouette(ax):
    pr = profile()
    return P(ax, pr) + P(ax, pr[::-1], flip=True)


def arch(ax, h, w=0.7, sill=0.55, spring=0.2):
    """arched window outline (screen pts), centred on the axis"""
    a = bp.arc_pts(ax, Y(h + spring), w / 2 * S, 180, 0)
    return [(ax - w / 2 * S, Y(h - sill))] + [tuple(p) for p in a] + [(ax + w / 2 * S, Y(h - sill))]


def densify(pts, step=0.04):
    out = []
    for (x0, h0), (x1, h1) in zip(pts[:-1], pts[1:]):
        n = max(1, int(max(abs(h1 - h0), abs(x1 - x0)) / step))
        for t in np.arange(n) / n: out.append((x0 + (x1 - x0) * t, h0 + (h1 - h0) * t))
    return out + [pts[-1]]


def split_h(pts, gaps):
    """polyline (r, h), monotone in h -> pieces outside the h-gaps"""
    res, cur = [], []
    for r, h in densify(pts):
        if any(a < h < b for a, b in gaps):
            if len(cur) > 1: res.append(cur)
            cur = []
        else:
            cur.append((r, h))
    if len(cur) > 1: res.append(cur)
    return res


def steps():
    dth = 2 * np.pi / PER_TURN
    th0 = np.pi + dth * 0.5
    k, out = 0, []
    while True:
        h = 2.5 + (k + 1) * RISE
        if h > 29.95: break
        out.append((k, h, th0 + k * dth))
        k += 1
    return out, dth


STEPS, DTH = steps()

# ================================================================== 1. the sheet: border, zones, empty blocks
bp.border(56, 30, 1890, 1050)
TB = bp.table(1452, 846, [100, 110, 108, 120], [26, 58, 30, 44, 46], pen='thin', outer='thick')
RB = bp.table(1452, 770, [40, 248, 80, 70], [20, 28, 28], pen='thin', outer='medium')
bp.stage('sheet')

# ================================================================== 2. layout in pencil + centre lines, ground, rock, sea
for h in (0.0, 2.5, 30.0, 33.3, 35.7, 41.2):
    bp.pencil([(70, Y(h)), (950, Y(h))], 0.8)
bp.pencil([(EX, 100), (EX, 975)], 0.8); bp.pencil([(SX, 100), (SX, 975)], 0.8)
for ax in (EX, SX):
    bp.centerline([(ax, Y(41.9)), (ax, Y(-3.6))])
SEA = -1.8


def rock(ax, seed):
    r = np.random.default_rng(seed)
    top_l = [(ax - 4.9 * S, Y(0.0))] + [(ax - (4.9 + t) * S, Y(-1.8 * (t / 4.0) ** 1.4 + r.normal(0, 0.12)))
                                        for t in np.linspace(0.6, 4.0, 7)]
    top_r = [(ax + 4.9 * S, Y(0.0))] + [(ax + (4.9 + t) * S, Y(-1.8 * (t / 3.6) ** 1.3 + r.normal(0, 0.12)))
                                        for t in np.linspace(0.6, 3.6, 7)]
    return top_l[::-1] + top_r, (ax - 8.9 * S, ax + 8.5 * S)


ROCK = {}
for ax, sd in ((EX, 4), (SX, 4)):
    top, (xl, xr) = rock(ax, sd)
    bot = Y(-3.25)
    poly = top + [(xr, bot), (xl, bot)]
    ROCK[ax] = (top, poly, bot)
    bp.ground(top, depth=8, every=17)
    bp.breakline((xl - 6, bot), (xr + 6, bot))
    bp.line([top[0], (xl, bot)], 'thin'); bp.line([top[-1], (xr, bot)], 'thin')
# the sea at high water and the wave lines under it
for x0, x1 in ((66, ROCK[EX][1][0][0] - 4), (ROCK[EX][1][-4][0] + 4, ROCK[SX][1][0][0] - 4), (ROCK[SX][1][-4][0] + 4, 870)):
    if x1 - x0 < 20: continue
    bp.line([(x0, Y(SEA)), (x1, Y(SEA))], 'thin', pool=False)
    for j, hh in enumerate((-2.25, -2.7)):
        xs = np.arange(x0 + 8 + j * 9, x1 - 10, 26)
        for x in xs: bp.line([(x, Y(hh)), (min(x + 12 - j * 4, x1), Y(hh))], 'fine', pool=False)
bp.stage('layout')

# ================================================================== 3. south elevation
bp.line(silhouette(EX), 'thick', closed=True)
bp.line([(EX - 4.75 * S, Y(2.2)), (EX + 4.75 * S, Y(2.2))], 'medium')
bp.line([(EX - 4.0 * S, Y(2.5)), (EX + 4.0 * S, Y(2.5))], 'medium')
bp.line([(EX - Rc(28.6 + 1e-3) * S, Y(28.6)), (EX + 2.65 * S, Y(28.6))], 'thin')
bp.line([(EX - 3.75 * S, Y(30.0)), (EX + 3.75 * S, Y(30.0))], 'medium')
# plinth ashlar: three courses, joints at equal angles -> crowd toward the edges
for c in range(3):
    h0, h1 = c * 0.733, (c + 1) * 0.733
    if c: bp.line([(EX - 4.6 * S, Y(h0)), (EX + 4.6 * S, Y(h0))], 'fine', pool=False)
    for ph in np.radians(np.arange(-78.75 + (c % 2) * 11.25, 80, 22.5)):
        x = EX + 4.6 * S * np.sin(ph)
        bp.line([(x, Y(h0)), (x, Y(h1))], 'fine', pool=False)
# shaft courses, broken at the windows and the door
win_e = [(h - 0.62, h + 0.62) for h in WIN_FRONT] + [(2.5, 4.75)]
for h in np.arange(2.5 + 0.62, 28.55, 0.62):
    xl, xr = EX - Rs(h) * S, EX + Rs(h) * S
    if any(a < h < b for a, b in win_e):
        bp.line([(xl, Y(h)), (EX - 0.55 * S, Y(h))], 'fine', pool=False)
        bp.line([(EX + 0.55 * S, Y(h)), (xr, Y(h))], 'fine', pool=False)
    else:
        bp.line([(xl, Y(h)), (xr, Y(h))], 'fine', pool=False)
# a round tower: shading lines on the shadow side, closer together toward the edge
for al in (58, 66, 72.5, 77.5, 81.5, 84.5, 87):
    sa = np.sin(np.radians(al))
    bp.line([(EX + 4.0 * S * sa, Y(2.55)), (EX + 2.65 * S * sa, Y(28.55))], 'fine', pool=False)
# door, ladder, windows
bp.line(arch(EX, 3.95, 1.1, 1.45, 0.1), 'medium', closed=True)
bp.arc(EX, Y(4.05), 0.78 * S, 180, 0, 'thin')
bp.line([(EX, Y(2.5)), (EX, Y(4.05))], 'fine', pool=False)
for sx in (-0.32, 0.32):
    bp.line([(EX + sx * S, Y(0.0)), (EX + sx * S, Y(2.55))], 'thin')
for h in np.arange(0.3, 2.5, 0.3):
    bp.line([(EX - 0.32 * S, Y(h)), (EX + 0.32 * S, Y(h))], 'fine', pool=False)
for h in WIN_FRONT:
    bp.line(arch(EX, h), 'medium', closed=True)
    bp.line([(EX - 0.5 * S, Y(h - 0.6)), (EX + 0.5 * S, Y(h - 0.6))], 'thin')
    bp.line([(EX, Y(h - 0.55)), (EX, Y(h + 0.55))], 'fine', pool=False)
    bp.line([(EX - 0.35 * S, Y(h)), (EX + 0.35 * S, Y(h))], 'fine', pool=False)
# galleries and railings (posts at equal angles round the gallery)
for (R, h0, h1, rails, step_deg) in ((3.6, 30.35, 31.6, 3, 15), (2.7, 33.3, 34.25, 2, 20)):
    for ph in np.radians(np.arange(step_deg / 2, 180, step_deg)):
        x = EX + R * S * np.cos(ph)
        bp.line([(x, Y(h0)), (x, Y(h1))], 'fine', pool=False)
    for i in range(1, rails + 1):
        hh = h0 + (h1 - h0) * i / rails
        bp.line([(EX - R * S, Y(hh)), (EX + R * S, Y(hh))], 'medium' if i == rails else 'thin')
    bp.line([(EX - R * S, Y(h0)), (EX - R * S, Y(h1))], 'thin'); bp.line([(EX + R * S, Y(h0)), (EX + R * S, Y(h1))], 'thin')
# watch room portholes (foreshortened toward the sides)
for ph in (90, 38, 142):
    c = np.cos(np.radians(ph)); s_ = np.sin(np.radians(ph))
    bp.circle(EX + 2.3 * S * c, Y(32.1), 0.3 * S * s_, 'thin', ry=0.3 * S)
# lantern pedestal panels and vents
for ph in np.radians(np.arange(30, 180, 30)):
    x = EX + 1.95 * S * np.cos(ph)
    bp.line([(x, Y(33.3)), (x, Y(34.3))], 'fine', pool=False)
bp.line([(EX - 1.95 * S, Y(34.3)), (EX + 1.95 * S, Y(34.3))], 'medium')
for ph in np.radians(np.arange(45, 180, 30)):
    bp.circle(EX + 1.95 * S * np.cos(ph), Y(33.8), 0.12 * S * np.sin(ph) + 0.6, 'fine', ry=0.12 * S)
# the lens seen through the glass (beehive outline and prism rings)
LENS = [(0.60, 34.6), (0.80, 34.9), (0.88, 35.3), (0.92, 35.35), (0.92, 36.05), (0.88, 36.1), (0.82, 36.5), (0.72, 36.8), (0.55, 37.0)]
bp.line(P(EX, LENS) + P(EX, LENS[::-1], True), 'fine', closed=True)
for h in list(np.linspace(34.75, 35.25, 3)) + list(np.linspace(35.45, 35.95, 4)) + list(np.linspace(36.2, 36.9, 4)):
    r = np.interp(h, [p[1] for p in LENS], [p[0] for p in LENS])
    bp.line([(EX - r * S, Y(h)), (EX + r * S, Y(h))], 'fine', pool=False)
# helical astragals: two families of bars winding round the glass, only the near half drawn
for fam in (1, -1):
    for j in range(12):
        hs = np.linspace(34.3, 37.0, 40)
        ph = np.radians(j * 30 + fam * 70 * (hs - 34.3) / 2.7)
        vis = np.sin(ph) > 0
        seg = []
        for h, p_, v in zip(hs, ph, vis):
            if v: seg.append((EX + 1.95 * S * np.cos(p_), Y(h)))
            elif len(seg) > 1: bp.line(seg, 'thin', pool=False); seg = []
            else: seg = []
        if len(seg) > 1: bp.line(seg, 'thin', pool=False)
# dome ribs, ventilator ball, conductor and vane
te = np.arccos(0.28 / 1.95)
for ph in np.radians((35, 62, 90, 118, 145)):
    t = np.linspace(0, te, 16)
    bp.line([(EX + 1.95 * np.cos(tt) * np.cos(ph) * S, Y(37.25 + 1.7 * np.sin(tt))) for tt in t], 'fine', pool=False)
bp.circle(EX, Y(39.42), 0.38 * S, 'medium')
bp.line([(EX, Y(39.8)), (EX, Y(41.2))], 'medium')
bp.line([(EX - 0.95 * S, Y(40.55)), (EX + 0.95 * S, Y(40.55))], 'thin')
bp.arrowhead((EX - 1.05 * S, Y(40.55)), (-1, 0), 9)
bp.fill([(EX + 0.55 * S, Y(40.55)), (EX + 0.95 * S, Y(40.85)), (EX + 0.95 * S, Y(40.25))])
bp.stage('elevation')

# ================================================================== 4. section A-A
WO, WI = 0.38, 0.55                        # half-height of a window opening outside / inside (splayed)
gR = [(h - WO, h + WO) for h in WIN_R]; gL = [(h - WO, h + WO) for h in WIN_L]
giR = [(h - WI, h + WI) for h in WIN_R]; giL = [(h - WI, h + WI) for h in WIN_L]
outer = [(Rout(h), h) for h in np.linspace(2.5, 30.0, 120)]
inner = []
for a, b, r in BANDS:
    inner += [(r, a), (r, b)]
for side, go, gi in ((1, gR, giR), (-1, gL, giL)):
    for seg in split_h(outer, go): bp.line([(SX + side * r * S, Y(h)) for r, h in seg], 'thick')
    for seg in split_h(inner, gi): bp.line([(SX + side * r * S, Y(h)) for r, h in seg], 'thick')
    for hc in [g[0] + WO for g in go]:
        xo, xi = SX + side * Rs(hc) * S, SX + side * Rin(hc) * S
        bp.line([(xo, Y(hc + WO)), (xi, Y(hc + WI))], 'thick'); bp.line([(xo, Y(hc - WO)), (xi, Y(hc - WI))], 'thick')
        xg = SX + side * (Rs(hc) - 0.25) * S                                   # the sash, set back from the face
        bp.line([(xg, Y(hc - WO - 0.03)), (xg, Y(hc + WO + 0.03))], 'medium')
        bp.line([(xg - side * 2.5, Y(hc - WO - 0.02)), (xg - side * 2.5, Y(hc + WO + 0.02))], 'fine', pool=False)
# base with the cistern
bp.line([(SX - 4.6 * S, Y(0)), (SX - 4.6 * S, Y(2.2)), (SX - 4.75 * S, Y(2.2)), (SX - 4.75 * S, Y(2.5)), (SX - 2.55 * S, Y(2.5))], 'thick')
bp.line([(SX + 4.6 * S, Y(0)), (SX + 4.6 * S, Y(2.2)), (SX + 4.75 * S, Y(2.2)), (SX + 4.75 * S, Y(2.5)), (SX + 2.55 * S, Y(2.5))], 'thick')
bp.line([(SX - 2.55 * S, Y(2.5)), (SX + 2.55 * S, Y(2.5))], 'thick')
CIS = [(SX - 1.7 * S, Y(0.45)), (SX + 1.7 * S, Y(0.45)), (SX + 1.7 * S, Y(2.05)), (SX - 1.7 * S, Y(2.05))]
bp.line(CIS, 'medium', closed=True)
bp.dashed([(SX - 1.7 * S + 3, Y(1.55)), (SX + 1.7 * S - 3, Y(1.55))], 'fine', (6, 4))
for x in np.arange(SX - 1.45 * S, SX + 1.5 * S, 0.5 * S):
    bp.line([(x, Y(1.32)), (x + 7, Y(1.32))], 'fine', pool=False)
# gallery slab, watch room, lantern floor, pedestal, glazing, cornice, dome
SLAB = [(SX - 3.75 * S, Y(30.0)), (SX + 3.75 * S, Y(30.0)), (SX + 3.75 * S, Y(30.35)), (SX - 3.75 * S, Y(30.35))]
bp.line(SLAB, 'thick', closed=True)
for side in (1, -1):
    bp.line([(SX + side * 2.3 * S, Y(30.35)), (SX + side * 2.3 * S, Y(33.0))], 'thick')
    bp.line([(SX + side * 1.95 * S, Y(30.35 if side > 0 else 32.4)), (SX + side * 1.95 * S, Y(33.0))], 'thick')
bp.line([(SX - 2.3 * S, Y(32.4)), (SX - 1.95 * S, Y(32.4))], 'thick')
bp.line([(SX - 2.3 * S, Y(30.35)), (SX - 2.3 * S, Y(32.4))], 'medium')
bp.line([(SX - 1.95 * S, Y(30.35)), (SX - 1.55 * S, Y(32.2))], 'thin')                 # door leaf, open
FLOOR = [(SX - 2.75 * S, Y(33.0)), (SX + 2.75 * S, Y(33.0)), (SX + 2.75 * S, Y(33.3)), (SX - 2.75 * S, Y(33.3))]
bp.line(FLOOR, 'thick', closed=True)
for side in (1, -1):
    bp.fill([(SX + side * 1.85 * S, Y(33.3)), (SX + side * 1.97 * S, Y(33.3)), (SX + side * 1.97 * S, Y(34.3)), (SX + side * 1.85 * S, Y(34.3))])
    bp.line([(SX + side * 1.92 * S, Y(34.3)), (SX + side * 1.92 * S, Y(37.0))], 'thin')
    bp.line([(SX + side * 1.98 * S, Y(34.3)), (SX + side * 1.98 * S, Y(37.0))], 'fine', pool=False)
    for hh in (35.0, 35.9, 36.6):
        bp.fill([(SX + side * 1.88 * S, Y(hh - 0.08)), (SX + side * 2.02 * S, Y(hh - 0.08)), (SX + side * 2.02 * S, Y(hh + 0.08)), (SX + side * 1.88 * S, Y(hh + 0.08))])
    bp.fill([(SX + side * 1.85 * S, Y(37.0)), (SX + side * 2.12 * S, Y(37.0)), (SX + side * 2.12 * S, Y(37.25)), (SX + side * 1.85 * S, Y(37.25))])
    for ph in (1, 2):                                                     # railings in section
        R = 3.6 if ph == 1 else 2.7
        h0, h1 = (30.35, 31.6) if ph == 1 else (33.3, 34.25)
        bp.line([(SX + side * R * S, Y(h0)), (SX + side * R * S, Y(h1))], 'medium')
        bp.line([(SX + side * (R - 0.15) * S, Y(h1)), (SX + side * (R + 0.05) * S, Y(h1))], 'medium')
dome_o = [(1.95 * np.cos(t), 37.25 + 1.7 * np.sin(t)) for t in np.linspace(0, te, 16)]
dome_i = [(1.85 * np.cos(t), 37.25 + 1.6 * np.sin(t)) for t in np.linspace(0, np.arccos(0.28 / 1.85), 16)]
for side in (1, -1):
    bp.fill(P(SX, dome_o, side < 0) + P(SX, dome_i[::-1], side < 0))
bp.circle(SX, Y(39.42), 0.38 * S, 'medium')
bp.line([(SX, Y(39.8)), (SX, Y(41.2))], 'medium')
bp.line([(SX - 0.28 * S, Y(39.05)), (SX + 0.28 * S, Y(39.05))], 'thin')
# the newel = weight tube, the weight on its cable, the clockwork above
for side in (1, -1):
    bp.fill([(SX + side * R_TUBE * S, Y(2.5)), (SX + side * R_NEWEL * S, Y(2.5)), (SX + side * R_NEWEL * S, Y(30.0)), (SX + side * R_TUBE * S, Y(30.0))])
bp.box(SX - 0.19 * S, Y(15.3), SX + 0.19 * S, Y(14.0), 'thin')
bp.line([(SX - 0.19 * S, Y(14.0)), (SX + 0.19 * S, Y(15.3))], 'fine', pool=False)
bp.line([(SX + 0.19 * S, Y(14.0)), (SX - 0.19 * S, Y(15.3))], 'fine', pool=False)
bp.line([(SX, Y(15.3)), (SX, Y(30.62))], 'fine', pool=False)
bp.box(SX - 0.75 * S, Y(31.6), SX + 0.75 * S, Y(30.35), 'thin')
bp.circle(SX - 0.32 * S, Y(31.08), 0.32 * S, 'thin'); bp.circle(SX + 0.3 * S, Y(31.2), 0.14 * S, 'fine')
bp.circle(SX, Y(30.72), 0.16 * S, 'fine')
bp.line([(SX + 0.75 * S, Y(30.9)), (SX + 1.05 * S, Y(30.9)), (SX + 1.05 * S, Y(30.7))], 'thin')
for side in (1, -1):                                                       # drive column + governor
    bp.line([(SX + side * 0.07 * S, Y(31.6)), (SX + side * 0.07 * S, Y(34.3))], 'thin')
bp.line([(SX + 0.5 * S, Y(31.6)), (SX + 0.5 * S, Y(32.2))], 'fine'); bp.dot(SX + 0.36 * S, Y(32.05), 2.0); bp.dot(SX + 0.64 * S, Y(32.05), 2.0)
# lens on its rotating table, lamp at the focal point
bp.fill([(SX - 0.98 * S, Y(34.3)), (SX + 0.98 * S, Y(34.3)), (SX + 0.98 * S, Y(34.45)), (SX - 0.98 * S, Y(34.45))])
for side in (1, -1):
    bp.line(P(SX, LENS, side < 0), 'thin')
    for h in list(np.linspace(34.75, 35.25, 3)) + list(np.linspace(36.2, 36.9, 4)):
        r = np.interp(h, [p[1] for p in LENS], [p[0] for p in LENS])
        bp.fill([(SX + side * (r - 0.02) * S, Y(h + 0.07)), (SX + side * (r + 0.1) * S, Y(h)), (SX + side * (r - 0.02) * S, Y(h - 0.07))])
for h in list(np.linspace(34.75, 35.25, 3)) + list(np.linspace(35.45, 35.95, 4)) + list(np.linspace(36.2, 36.9, 4)):
    r = np.interp(h, [p[1] for p in LENS], [p[0] for p in LENS])
    bp.line([(SX - r * S + 2, Y(h)), (SX + r * S - 2, Y(h))], 'fine', pool=False)
bp.line([(SX - 0.05 * S, Y(34.45)), (SX - 0.05 * S, Y(35.55))], 'fine'); bp.line([(SX + 0.05 * S, Y(34.45)), (SX + 0.05 * S, Y(35.55))], 'fine')
# the stair: the far half seen beyond the cut (nosings, the tread-and-riser zig-zag along the wall, the helical
# soffit under the steps); the steps the cutting plane passes through are inked solid
for k, h, th in STEPS:
    ro = Rin(h) - 0.02
    c0, s0 = np.cos(th), np.sin(th)
    if s0 > 0.02:
        xa, xb = R_NEWEL * np.sign(c0), ro * c0
        if abs(xb) > R_NEWEL + 0.05:
            bp.line([(SX + xa * S, Y(h)), (SX + xb * S, Y(h))], 'thin', pool=False)
            bp.line([(SX + xb * S, Y(h - RISE)), (SX + xb * S, Y(h))], 'thin', pool=False)
        t1 = min(th + DTH, np.ceil(th / np.pi) * np.pi)
        x2 = ro * np.cos(t1)
        bp.line([(SX + xb * S, Y(h)), (SX + x2 * S, Y(h))], 'thin', pool=False)
    a = th % (2 * np.pi)
    for ang, side in ((0.0, 1), (2 * np.pi, 1), (np.pi, -1)):
        if a <= ang <= a + DTH:
            bp.fill([(SX + side * R_NEWEL * S, Y(h)), (SX + side * ro * S, Y(h)), (SX + side * ro * S, Y(h - 0.13)), (SX + side * R_NEWEL * S, Y(h - 0.13))])
th_all = np.linspace(STEPS[0][2], STEPS[-1][2], 4000)
h_all = 2.5 + RISE + (th_all - STEPS[0][2]) / DTH * RISE - 0.42
seg = []
for th, h in zip(th_all, h_all):
    vis = np.sin(th) > 0 and h > 2.55
    x = (Rin(h + 0.42) - 0.02) * np.cos(th)
    if vis: seg.append((SX + x * S, Y(h)))
    elif len(seg) > 1: bp.line(seg, 'thin', pool=False); seg = []
    else: seg = []
if len(seg) > 1: bp.line(seg, 'thin', pool=False)
bp.stage('section')

# ================================================================== 5. hatching: granite, rock, cut iron, glass
HS = 5.0
for side, gi in ((1, giR), (-1, giL)):
    wall = [(SX + side * Rout(h) * S, Y(h)) for h in np.linspace(2.5, 30.0, 120)]
    wall += [(SX + side * r * S, Y(h)) for r, h in inner[::-1]]
    holes = []
    for hc in [g[0] + WI for g in gi]:
        holes.append([(SX + side * (Rs(hc) + 0.3) * S, Y(hc + WO)), (SX + side * Rin(hc) * S, Y(hc + WI)),
                      (SX + side * Rin(hc) * S, Y(hc - WI)), (SX + side * (Rs(hc) + 0.3) * S, Y(hc - WO))])
    bp.hatch([wall], 45, HS, holes=holes)
base = [(SX - 4.6 * S, Y(0)), (SX + 4.6 * S, Y(0)), (SX + 4.6 * S, Y(2.2)), (SX + 4.75 * S, Y(2.2)), (SX + 4.75 * S, Y(2.5)),
        (SX - 4.75 * S, Y(2.5)), (SX - 4.75 * S, Y(2.2)), (SX - 4.6 * S, Y(2.2))]
bp.hatch([base], 45, HS, holes=[CIS])
bp.hatch([SLAB], 45, HS)
for side in (1, -1):
    bp.hatch([[(SX + side * 1.95 * S, Y(30.35 if side > 0 else 32.4)), (SX + side * 2.3 * S, Y(30.35 if side > 0 else 32.4)),
               (SX + side * 2.3 * S, Y(33.0)), (SX + side * 1.95 * S, Y(33.0))]], 45, HS)
bp.hatch([FLOOR], 45, 3.2, kind='cross')
for ax in (EX, SX):
    top, poly, bot = ROCK[ax]
    bp.hatch([poly], kind='rock', spacing=9 if ax == SX else 13, pen='fine')
bp.stage('hatching')

# ================================================================== 6. plan B-B at +6.50 (1:100)
PX, PY, K = 1110.0, 300.0, 38.0
Ro, Ri = Rs(6.5), Rin(6.5)
pp = lambda r, th: (PX + r * np.cos(th) * K, PY - r * np.sin(th) * K)
bp.centerline([(PX - 200, PY), (PX + 200, PY)]); bp.centerline([(PX, PY - 200), (PX, PY + 200)])
ring_o = [pp(Ro, t) for t in np.linspace(0, 2 * np.pi, 200)]
ring_i = [pp(Ri, t) for t in np.linspace(0, 2 * np.pi, 160)]
win = [pp(Ro + 0.3, -0.105), pp(Ro + 0.3, 0.105), pp(Ri - 0.05, 0.27), pp(Ri - 0.05, -0.27)]
bp.hatch([ring_o], 45, 4.0, holes=[ring_i, win])
for r0, r1 in ((Ro, Ri),):
    a_o, a_i = 0.093, 0.235
    bp.line([pp(r0, t) for t in np.linspace(a_o, 2 * np.pi - a_o, 220)], 'thick')
    bp.line([pp(r1, t) for t in np.linspace(a_i, 2 * np.pi - a_i, 180)], 'thick')
    for sg in (1, -1):
        bp.line([pp(r0, sg * a_o), pp(r1, sg * a_i)], 'thick')
bp.line([pp(Ro - 0.25, -0.1), pp(Ro - 0.25, 0.1)], 'thin'); bp.line([pp(Ro - 0.35, -0.11), pp(Ro - 0.35, 0.11)], 'fine')
bp.hatch([[pp(R_NEWEL, t) for t in np.linspace(0, 2 * np.pi, 60)]], kind='solid', holes=[[pp(R_TUBE, t) for t in np.linspace(0, 2 * np.pi, 50)]])
bp.dot(PX, PY, 1.4)
kc = max(k for k, h, th in STEPS if h <= 6.5)
thc = STEPS[kc][2]
for k, h, th in STEPS[kc - 13:kc + 1]:
    bp.line([pp(R_NEWEL, th), pp(Ri - 0.02, th)], 'thin', pool=False)
for k, h, th in STEPS[kc + 1:kc + 6]:
    bp.dashed([pp(R_NEWEL + 0.1, th), pp(Ri - 0.1, th)], 'fine', (5, 4))
tb = thc + DTH * 0.55
bp.breakline(pp(R_NEWEL + 0.05, tb), pp(Ri + 0.02, tb), 'thin', zig=6)
rm = (R_NEWEL + Ri) / 2 + 0.15
arc_up = [pp(rm, t) for t in np.linspace(thc - 3.55, thc + DTH * 0.1, 70)]
bp.line(arc_up, 'thin')
bp.arrowhead(arc_up[-1], np.subtract(arc_up[-1], arc_up[-4]), 9)
bp.dot(*arc_up[0], 2.2)
bp.stage('plan')

# ================================================================== 7. detail 1: lens and lamp (1:30)
DX, FY, KD = 1440.0, 290.0, 126.0
yd = lambda h: FY - (h - 35.7) * KD
bp.centerline([(DX, yd(37.45)), (DX, yd(34.1))])
bp.centerline([(1330, FY), (1712, FY)], pattern=(22, 4, 4, 4))
F = np.array([DX, FY])


def isect(p, d, q, e):
    A = np.array([[d[0], -e[0]], [d[1], -e[1]]], np.float64)
    t = np.linalg.solve(A, np.subtract(q, p))
    return np.asarray(p) + np.asarray(d) * t[0]


prisms, rays = [], []
for al, xe, L1, L2 in [(31, 0.80, 0.10, 0.03), (39, 0.785, 0.10, 0.03), (47, 0.765, 0.095, 0.03), (55, 0.735, 0.09, 0.028), (62, 0.70, 0.085, 0.026),
                       (-31, 0.80, 0.10, 0.03), (-39, 0.785, 0.10, 0.03), (-47, 0.765, 0.095, 0.03), (-54, 0.74, 0.09, 0.028)]:
    r = np.array([np.cos(np.radians(al)), -np.sin(np.radians(al))])
    E = F + r * (xe / np.cos(np.radians(al))) * KD
    M = E + r * L1 * KD
    Xp = M + np.array([L2 * KD, 0])
    m = (np.array([1.0, 0]) - r); m /= np.linalg.norm(m)
    t_m = np.array([-m[1], m[0]]); t_e = np.array([r[1], -r[0]])
    V1 = isect(E, t_e, M, t_m); V2 = isect(M, t_m, Xp, [0, 1]); V3 = isect(Xp, [0, 1], E, t_e)
    prisms.append([V1, V2, V3]); rays.append([F, E, M, Xp])
belt_top, belt_bot = yd(36.1), yd(35.3)
xi, xo = DX + 0.80 * KD, DX + 0.92 * KD
teeth = np.linspace(belt_top, belt_bot, 8)
belt = [(xi, belt_top), (xi, belt_bot)]
for j in range(len(teeth) - 1, 0, -1):
    ya, yb = teeth[j], teeth[j - 1]
    t = ((ya + yb) / 2 - FY) / (belt_bot - FY)
    if abs(t) < 0.2:
        belt += [(xo - 3, ya)] + [(xo + 2 - 5 * abs(s) ** 2, (ya + yb) / 2 + s * (yb - ya) / 2) for s in np.linspace(1, -1, 7)] + [(xo - 3, yb)]
    elif t > 0:
        belt += [(xo - 4, ya), (xo + 1, yb + 2), (xo - 4, yb)]
    else:
        belt += [(xo - 4, ya), (xo + 1, ya - 2), (xo - 4, yb)]
for h in np.linspace(35.3 + 0.8 / 7 * 0.5, 36.1, 7)[:-1]:
    rays.append([F, (xi, yd(h)), (xo, yd(h))])
for pr in prisms:
    bp.hatch([pr], 30, 2.6, kind='lines', pen=0.7)                         # cut glass
    bp.line(pr, 'thin', closed=True)
bp.hatch([belt], 30, 2.6, kind='lines', pen=0.7)
bp.line(belt, 'thin', closed=True)
# bronze frame: rings holding the prisms, the uprights
frame_o = sorted([max(pr, key=lambda v: v[0]) for pr in prisms], key=lambda v: v[1])
bp.line([(frame_o[0][0] + 3, frame_o[0][1] - 4)] + [(v[0] + 3, v[1]) for v in frame_o[:5]] + [(xo + 4, belt_top - 4)], 'fine')
bp.line([(xo + 4, belt_bot + 4)] + [(v[0] + 3, v[1]) for v in frame_o[5:]], 'fine')
# mirrored outline of the far half, dashed (half section)
ys_o = [v[1] for v in frame_o]; xs_o = [v[0] for v in frame_o]
half = sorted(list(zip(ys_o, xs_o)) + [(belt_top, xo + 1), (belt_bot, xo + 1)])
LH = _spl([(2 * DX - x - 2, y) for y, x in half], 8)                     # left half: the lens seen from outside
bp.line([(DX, LH[0][1])] + [tuple(p) for p in LH] + [(DX, LH[-1][1])], 'thin')
for y in sorted(ys_o + list(teeth)):
    xl = np.interp(y, LH[:, 1], LH[:, 0])
    bp.line([(xl + 2, y), (DX - 2, y)], 'fine', pool=False)
for ph in (0.38, 0.72):                                                    # bronze uprights of the frame
    bp.line([(DX - (DX - x) * np.sin(np.pi / 2 * ph * 1.0) , y) for x, y in LH], 'fine', pool=False)
# lamp and table
TABLE = [(DX - 1.0 * KD, yd(34.3)), (DX + 1.0 * KD, yd(34.3)), (DX + 1.0 * KD, yd(34.43)), (DX - 1.0 * KD, yd(34.43))]
bp.hatch([TABLE], 45, 3.2, kind='cross'); bp.line(TABLE, 'thin', closed=True)
for xr_ in (-0.75, -0.4, 0.4, 0.75):
    bp.circle(DX + xr_ * KD, yd(34.3) + 5, 4.2, 'thin')
bp.line([(DX - 0.95 * KD, yd(34.3) + 9.5), (DX + 0.95 * KD, yd(34.3) + 9.5)], 'medium')
for side in (-1, 1):
    bp.line([(DX + side * 7, yd(34.43)), (DX + side * 7, FY + 12)], 'thin')
bp.line([(DX - 11, FY + 12), (DX + 11, FY + 12)], 'medium')
flame = [(DX, FY - 24), (DX + 5, FY - 10), (DX + 7, FY + 1), (DX + 4, FY + 8), (DX, FY + 10), (DX - 4, FY + 8), (DX - 7, FY + 1), (DX - 5, FY - 10)]
bp.line(_spl(flame + [flame[0]], 6), 'thin', closed=True)
bp.line(_spl([(DX, FY - 12), (DX + 3, FY - 2), (DX, FY + 5), (DX - 3, FY - 2), (DX, FY - 12)], 5), 'fine')
# lantern glass, astragal, cornice, the start of the dome, and the break
XG = DX + 1.95 * KD
bp.line([(XG - 2, yd(37.0)), (XG - 2, yd(34.3))], 'thin'); bp.line([(XG + 2, yd(37.0)), (XG + 2, yd(34.3))], 'thin')
bp.hatch([[(XG - 2, yd(36.3)), (XG + 2, yd(36.3)), (XG + 2, yd(34.9)), (XG - 2, yd(34.9))]], 60, 4, kind='glass')
for hh in (35.0, 36.25):                                                   # astragals cut through
    bp.fill([(XG - 4, yd(hh) - 4), (XG + 4, yd(hh) - 4), (XG + 4, yd(hh) + 4), (XG - 4, yd(hh) + 4)])
CORN = [(XG - 8, yd(37.0)), (XG + 16, yd(37.0)), (XG + 16, yd(37.25)), (XG - 8, yd(37.25))]
bp.hatch([CORN], 45, 3.2, kind='cross'); bp.line(CORN, 'thin', closed=True)
SILL = [(XG - 8, yd(34.3)), (XG + 10, yd(34.3)), (XG + 10, yd(34.3) + 14), (XG - 8, yd(34.3) + 14)]
bp.hatch([SILL], 45, 3.2, kind='cross'); bp.line(SILL, 'thin', closed=True)
bp.breakline((1318, yd(34.3) + 34), (1730, yd(34.3) + 34))
# rays: from the flame through each prism, then out level as one beam
XE = 1758
for ry in rays:
    pts = [tuple(p) for p in ry] + [(XE, ry[-1][1])]
    bp.line(pts, 'fine', pool=False)
    bp.arrowhead((XE + 1, ry[-1][1]), (1, 0), 8)
bp.stage('detail')

# ================================================================== 8. dimensions, levels, cut marks, leaders
def ext(x0, y, x1):
    bp.line([(x0, y), (x1, y)], 'fine', pool=False)


CH = [0.0, 2.5, 30.0, 33.3, 41.2]
for h, xo_ in zip(CH, [EX - 4.6 * S, EX - 4.75 * S, EX - 3.75 * S, EX - 2.75 * S, EX - 0.2 * S]):
    ext(xo_ - 4, Y(h), 118 if h in (0.0, 41.2) else 146)
for a, b in zip(CH[:-1], CH[1:]):
    bp.dim((150, Y(a)), (150, Y(b)), 0, f'{b - a:.2f}', size=10)
bp.dim((122, Y(0.0)), (122, Y(41.2)), 0, '41.20', size=11)
# levels between the elevation and the section
LV = [(2.5, '+2.50', 'ENTRANCE'), (30.0, '+30.00', 'GALLERY'), (33.3, '+33.30', 'LANTERN FLOOR'),
      (35.7, '+35.70', 'FOCAL PLANE'), (41.2, '+41.20', '')]
for h, t, name in LV:
    xr = SX - (Rout(h) if 0 < h <= 30.0 else {33.3: 2.75, 35.7: 1.95, 41.2: 0.1}.get(h, 4.75)) * S - 6
    bp.level(xr, Y(h), t, size=10, length=xr - 470, side='left', mark_at=548)
    if name: bp.text(name, 528, Y(h) + 13, 7, 'rs')
for h, t, name, x0 in ((0.0, '±0.00', 'ROCK DATUM', SX + 4.95 * S), (SEA, '-1.80', 'HIGH WATER', SX + 8.6 * S)):
    bp.level(x0 + 4, Y(h), t, size=10, length=902 - x0, side='right', mark_at=878)
    bp.text(name, 888, Y(h) + 13, 7, 'ls')
# section B-B on the section, section A-A on the plan
bp.cut_mark((SX - 5.2 * S, Y(6.5)), (SX + 5.2 * S, Y(6.5)), 'B', (0, 1), size=13, through=False, arm=18)
bp.cut_mark((PX - 4.35 * K, PY), (PX + 4.35 * K, PY), 'A', (0, -1), size=14, through=False, arm=18)
# wall thickness and plan dimensions
bp.dim((SX - 4.0 * S, Y(3.4)), (SX - 2.55 * S, Y(3.4)), 0, '1.45', size=9, text_off=4)
bp.dim((SX + 2.05 * S, Y(27.2)), (SX + Rs(27.2) * S, Y(27.2)), 0, '0.68', size=9, text_off=4)
bp.dim(pp(Ro, np.pi), pp(Ro, 0), Ro * K + 30, f'Ø{2 * Ro:.2f}', size=11)
bp.dim(pp(Ro, np.radians(212)), pp(Ri, np.radians(212)), 0, f'{Ro - Ri:.2f}', size=9, text_off=4)
bp.text('UP', *pp(rm - 0.42, thc - 3.45), 9, 'mm')
bp.text('120 STEPS', PX, PY + 1.05 * K, 8, 'mm', clear=True)
# leaders on the section
bp.circle(SX, Y(35.75), 2.55 * S, 'thin', dash=(7, 4))
bp.line([(SX + 2.55 * S * 0.72, Y(35.75) - 2.55 * S * 0.69), (858, 214)], 'fine', pool=False)
bp.bubble(872, 205, 15, '1', '3', size=12)
L = 806
bp.leader([(SX + 2, Y(40.4)), (L - 14, Y(40.9))], 'LIGHTNING CONDUCTOR', 8)
bp.leader([(SX + 0.4 * S, Y(39.42)), (L - 14, Y(39.42))], 'VENTILATOR', 8, end='dot')
bp.leader([(SX + 1.95 * S, Y(36.6)), (L - 34, Y(37.9)), (L - 14, Y(37.9))], 'HELICAL ASTRAGALS', 8, end='dot')
bp.leader([(SX + 0.85 * S, Y(31.0)), (L - 14, Y(31.9))], 'CLOCKWORK,\nWIND EVERY 4 H', 8, end='dot')
bp.leader([(SX + 0.2 * S, Y(22.0)), (L - 14, Y(22.6))], 'WEIGHT TUBE\n(HOLLOW NEWEL)', 8, end='dot')
bp.leader([(SX + 0.12 * S, Y(14.6)), (L - 14, Y(15.4))], 'WEIGHT 180 KG,\nFALLS 22 M IN 4 H', 8, end='dot')
bp.leader([(SX + 1.6 * S, Y(10.47)), (L - 14, Y(10.6))], 'STONE STAIR,\n120 STEPS', 8, end='dot')
bp.leader([(SX + 3.3 * S, Y(4.6)), (L - 14, Y(4.9))], 'GRANITE, DOVETAILED\nCOURSES', 8, end='dot')
bp.leader([(SX - 0.9 * S, Y(1.0)), (566, Y(1.0))], 'CISTERN', 8, end='dot')
bp.revision(SX - 3.6 * S - 16, Y(31.2), 'B', 10)
bp.revision(EX - 3.6 * S - 16, Y(31.2), 'B', 10)
# detail labels
def brace(y0, y1, x, label):
    bp.line([(x - 5, y0), (x, y0), (x, y1), (x - 5, y1)], 'fine', pool=False)
    bp.line([(x, (y0 + y1) / 2), (x + 6, (y0 + y1) / 2)], 'fine', pool=False)
    bp.text(label, x + 11, (y0 + y1) / 2, 8, 'lm')


up_y = [r[-1][1] for r in rays[:5]]; lo_y = [r[-1][1] for r in rays[5:9]]; be_y = [r[-1][1] for r in rays[9:]]
brace(min(up_y) - 3, max(up_y) + 3, 1772, 'CATADIOPTRIC\nPRISMS:\nREFLECT')
brace(min(be_y) - 3, max(be_y) + 3, 1772, 'DIOPTRIC\nBELT:\nREFRACT')
brace(min(lo_y) - 3, max(lo_y) + 3, 1772, 'CATADIOPTRIC\nPRISMS:\nREFLECT')
bp.leader([(DX - 3, FY - 4), (1318, 236)], 'F', 10, end='dot')
bp.leader([(DX - 7, FY + 66), (1318, FY + 104)], 'LAMP', 8, end='dot')
bp.leader([(DX - 0.75 * KD, yd(34.3) + 5), (1318, yd(34.3) + 5)], 'ROLLERS', 8, end='dot')
bp.leader([(XG + 2, yd(34.75)), (XG + 26, yd(34.3) + 2), (XG + 36, yd(34.3) + 2)], 'LANTERN GLASS', 8, end='dot')
bp.text('PARALLEL BEAM · FL.(2) EVERY 10 S · 19 NM', 1860, 76, 8, 'rs')
bp.stage('dimensions')

# ================================================================== 9. lettering: titles, notes, scales, blocks
bp.view_title(EX, 1004, 'SOUTH ELEVATION', '1:200', 15)
bp.view_title(SX, 1004, 'SECTION A–A', '1:200', 15)
bp.view_title(PX, 505, 'PLAN B–B AT +6.50', '1:100', 13)
bp.view_title(1600, 538, 'DETAIL 1 — LENS AND LAMP', '1:30', 13, bubble=('1', '3'))
bp.north(994, 452, 17)
NX, NY = 994, 600
bp.text('GENERAL NOTES', NX, NY, 12, 'ls', pen=1.3)
bp.line([(NX, NY + 5), (NX + bp.text_width('GENERAL NOTES', 12), NY + 5)], 'thin')
NOTES = ['1. DIMENSIONS ARE IN METRES; LEVELS ARE TAKEN FROM ROCK DATUM.',
         '2. TOWER OF DOVETAILED GRANITE COURSES IN LIME MORTAR.',
         '3. STAIR: 120 CANTILEVERED STONE STEPS, RISE 0.23,',
         '   WOUND ROUND A HOLLOW NEWEL.',
         '4. THE NEWEL IS THE WEIGHT TUBE. THE CLOCKWORK WEIGHT',
         '   FALLS 22 M IN 4 H AND TURNS THE LENS ONCE IN 20 S.',
         '5. THE KEEPER WINDS THE CLOCKWORK EVERY 4 HOURS.',
         '6. LIGHT: FIRST ORDER LENS, FOCAL PLANE +35.70,',
         '   FL.(2) EVERY 10 S, RANGE 19 NAUTICAL MILES.',
         '7. LANTERN AND LENS: DETAIL 1, THIS SHEET.']
for i, s in enumerate(NOTES):
    bp.text(s, NX, NY + 28 + i * 19, 8, 'ls', guide=True, spacing=0.2)
bp.scale_bar(1050, 846, S, (0, 2, 4, 6, 8, 10), label='ELEVATION AND SECTION 1:200 — METRES', size=9)
bp.scale_bar(1050, 912, K, (0, 1, 2, 3, 4, 5), label='PLAN 1:100 — METRES', size=9)
bp.scale_bar(1050, 978, KD, (0, 0.5, 1, 1.5), label='DETAIL 1:30 — METRES', size=9)
# revision block
for (x0, y0, x1, y1), t in zip(RB[0], ('REV', 'DESCRIPTION', 'DATE', 'BY')):
    bp.text(t, (x0 + x1) / 2, (y0 + y1) / 2, 7, 'mm')
for row, vals in zip(RB[1:], (('A', 'ISSUED FOR TENDER', '02.1911', 'J.K.'), ('B', 'GALLERY RAIL RAISED TO 1.25', '05.1911', 'R.T.'))):
    for (x0, y0, x1, y1), t in zip(row, vals):
        bp.text(t, (x0 + x1) / 2 if t in vals[:1] + vals[2:] else x0 + 8, (y0 + y1) / 2, 9, 'mm' if t in vals[:1] + vals[2:] else 'lm')
# title block
(x0, y0, x1, y1) = (TB[0][0][0], TB[0][0][1], TB[0][-1][2], TB[0][0][3])
bp.text('COASTAL WORKS OFFICE — LIGHTS DIVISION', (x0 + x1) / 2, (y0 + y1) / 2, 9, 'mm')
(x0, y0, x1, y1) = (TB[1][0][0], TB[1][0][1], TB[1][-1][2], TB[1][0][3])
bp.text('HALVARD ROCK LIGHT', (x0 + x1) / 2, y0 + 30, 21, 'ms', pen=2.0, spacing=0.26)
bp.text('TOWER: ELEVATION, SECTION, PLAN AND LENS DETAIL', (x0 + x1) / 2, y0 + 49, 8, 'ms')
(x0, y0, x1, y1) = (TB[2][0][0], TB[2][0][1], TB[2][-1][2], TB[2][0][3])
bp.cjk('灯塔  立面 · 剖面 · 平面及透镜详图', (x0 + x1) / 2, y1 - 6, 16, 'ms', condense=0.82)
for (cx0, cy0, cx1, cy1), lab, val in zip(TB[3], ('DRAWN', 'TRACED', 'CHECKED', 'APPROVED'), ('J.K.', 'M.O.', 'R.T.', 'H. LUND')):
    bp.text(lab, cx0 + 5, cy0 + 11, 6, 'ls')
    bp.text(val, (cx0 + cx1) / 2, cy1 - 10, 11, 'ms', slant=0.22)
for (cx0, cy0, cx1, cy1), lab, val in zip(TB[4], ('SCALE', 'DATE', 'SHEET', 'DRAWING NO.'), ('AS SHOWN', 'MARCH 1911', '3 OF 7', 'LH-117-03 B')):
    bp.text(lab, cx0 + 5, cy0 + 11, 6, 'ls')
    bp.text(val, (cx0 + cx1) / 2, cy1 - 11, 11 if len(val) < 10 else 10, 'ms')
bp.stage('lettering')

# ================================================================== 10. the sheet's life: folded, filed, handled
bp.fold(xs=[640, 1280], ys=[540])
bp.fade(1280, 540, 1920, 1080, 0.13)
bp.grime(1280, 540, 1920, 1080, 0.9)
bp.fade(0, 0, 640, 540, 0.05)
bp.stain(92, 1012, 62)
for x, y in ((24, 16), (1896, 16), (24, 1064), (1896, 1064)): bp.tack(x, y)
bp.tear(640, 0, (0, 1), 9); bp.tear(1280, 1079, (0, -1), 7); bp.tear(0, 540, (1, 0), 6)
bp.stage('folded')

# ================================================================== 11. the site engineer's red pencil
bp.cloud([(797, Y(10.6) - 23), (915, Y(10.6) - 23), (915, Y(10.6) + 22), (797, Y(10.6) + 22)], bump=19)
bp.red_text('counted:', 836, Y(10.6) + 60, 19, rot=4)
bp.red_text('119 + landing', 826, Y(10.6) + 84, 19, rot=4)
bp.red([(951, Y(10.6) + 70), (957, Y(10.6) + 79), (972, Y(10.6) + 56)], 2.4, smooth=False)
c = TB[3][2]
bp.red([(c[0] + 66, c[1] + 22), (c[0] + 72, c[1] + 30), (c[0] + 90, c[1] + 8)], 2.6, smooth=False)

img = bp.save(out, stages)
print(f'{out}  {time.time() - t0:.1f}s')
