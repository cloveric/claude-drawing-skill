"""Example (Leonardo-style codex page / 达·芬奇手稿): 扑翼机 · The Ornithopter — one leaf of an engineer's notebook
working out how a machine could beat its wings like a bird. Upper left, the idea: little birds drawn in flight
through one wing-beat, and a red-chalk study of a bird's wing from below (bones along the leading edge, fanned
primaries, coverts). Centre, the answer: a bat-winged flying machine seen from below -- the right wing fully
worked (cane spars with lashings, hinged elbow and wrist, finger ribs, cords over a pulley, a membrane hatched
'\\' by a left hand so that each panel billows), the left wing left half-done over its leadpoint underdrawing.
Upper right, the geometry: a compass-scored proportion circle, the front view of the stroke -- wings up and down,
the swept sector hatched, the short lever arm that is a quarter of the wing. Lower right, an exploded view of
the drive: crank, lantern pinion, crown wheel and the pulley that winds the cord. A close-up of the wrist joint,
a rejected wing struck out, mirror-written pseudo-Italian notes, blots, foxing, a water stain.
Draw-on stages: the blank leaf -> stylus & leadpoint construction -> the bird -> the frame -> hatching ->
the proportion circle -> the drive & joint -> the notes -> corrections and blots. No image model.
python3 codex_ornithopter.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from codex import Codex, Camera, crown, lantern, crank, cylinder, pulley, merge
from core import curve, spline, blur

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'codex_ornithopter.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

c = Codex(1920, 1080, seed=7)
c.sheet(stains=[(170, 985, 205)], lost_corner='br')
c.show_through(1080, 590, 560, lines=6, size=21)        # the verso's writing, seen through the leaf
c.stage('carta')

MX = 960                                                  # the machine's centre line
mir = lambda p: (2 * MX - p[0], p[1])

# ------------------------------------------------------------------ geometry of the machine (right wing)
S, E, WR, T = (1004, 300), (1146, 248), (1272, 234), (1470, 286)             # shoulder, elbow, wrist, tip
TIPS = [T, (1436, 382), (1356, 452), (1252, 500), (1128, 520), (996, 500)]     # rib tips along the trailing edge
RIBS = [(WR, TIPS[1]), (WR, TIPS[2]), (WR, TIPS[3]), (E, TIPS[4])]
BODY_R = [(MX, 166), (976, 200), (988, 262), (992, 332), (989, 432), (980, 522), (970, 582), (MX, 604)]
BODY = BODY_R + [mir(p) for p in BODY_R[-2:0:-1]]
HUB = (MX, 412)
TAIL = (MX, 604)
TAIL_TIPS = [(MX + np.cos(np.deg2rad(a)) * L, 604 + np.sin(np.deg2rad(a)) * L)
             for a, L in zip(np.linspace(58, 122, 7), [100, 112, 120, 122, 120, 112, 100])]


def scallop(p, q, k=0.12, toward=None):
    """membrane edge between two rib tips: sags in toward the wing (toward a point inside it)"""
    p, q = np.asarray(p, np.float32), np.asarray(q, np.float32)
    d = q - p
    L = float(np.hypot(*d))
    nrm = np.array([-d[1], d[0]]) / (L + 1e-6)
    inside = np.asarray(toward if toward is not None else ((WR if p[0] > MX else mir(WR))), np.float32)
    sgn = 1.0 if np.dot(inside - (p + q) / 2, nrm) > 0 else -1.0
    return curve(p, q, sgn * L * k, 26)


def leading_edge(mirror=False):
    P = spline([S, (1074, 262), E, (1210, 232), WR, (1372, 248), T], 10)
    return np.array([mir(p) for p in P]) if mirror else P


# ------------------------------------------------------------------ 1. construction: stylus, compass, leadpoint
c.incise([(MX, 140), (MX, 740)], 0.9, smooth=False)                       # the centre line
c.incise([(470, 300), (1470, 300)], 0.8, smooth=False)                    # the shoulder line
for sgn in (1, -1):
    sx = MX + sgn * 46
    c.compass(sx, 300, 466, -13 if sgn > 0 else 167, 11 if sgn > 0 else 193, 0.7)   # the wing's reach
O, R, r_lever = (1690, 292), 148, 37
c.compass(*O, R)
c.compass(*O, r_lever, prick=False)
c.incise([(1515, 292), (1866, 292)], 0.9, smooth=False)
c.incise([(1690, 120), (1690, 470)], 0.7, smooth=False)
# leadpoint: the whole machine searched out lightly before the pen
for m in (False, True):
    f = (lambda p: mir(p)) if m else (lambda p: p)
    c.leadpoint(leading_edge(m) + c.rng.normal(0, 1.5, 2), 1.1, 0.55)
    for a, b in RIBS: c.leadpoint(curve(f(a), f(b), 10, 16) + c.rng.normal(0, 2, 2), 1.0, 0.5)
    for p, q in zip(TIPS[:-1], TIPS[1:]): c.leadpoint(scallop(f(p), f(q)) + c.rng.normal(0, 2.5, 2), 1.0, 0.5)
c.leadpoint(np.vstack([BODY, BODY[:1]]) + 2, 1.0, 0.5, smooth=True)
c.stage('costruzione')

# ------------------------------------------------------------------ 2. the bird: flight sequence + red-chalk wing
path = [(92, 128), (190, 108), (290, 132), (392, 112), (500, 126)]
for (x, y), ph in zip(path, [np.pi / 2, np.pi / 7, -np.pi / 3, -np.pi / 2, np.pi / 4]):
    c.bird(x, y, 30, ph, 0.85)
c.dotted(spline([(70, 150), (190, 136), (290, 158), (392, 138), (540, 150)], 10), 4, 7, 1.1, 0.55)
c.arrow([(548, 146), (575, 140), (604, 134)], 1.6, 0.85, 10)


def bird_wing(ox, oy, k):
    """red-chalk study of a kite's wing seen from below, pointing left: bones along the leading edge, primaries
    fanned from the hand, secondaries from the forearm, two rows of coverts; nominal geometry scaled by k"""
    T_ = lambda p: (ox + p[0] * k, oy + p[1] * k)
    Sh, El, Wb, Ht = (0, 0), (-80, -34), (-178, -28), (-270, 8)
    lerp = lambda p, q, u, dy=0: (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u + dy)
    spec = [(lerp(Sh, El, i / 3, 6), 84 + 4 * i, 128 + 8 * i, 30, 0.45) for i in range(3)]
    spec += [(lerp(El, Wb, i / 7, 5), 96 + 1.6 * i, 166 + 1.5 * i, 30, 0.45) for i in range(8)]
    lens = [186, 204, 220, 232, 238, 234, 220, 198, 166]          # the outer primaries splay into 'fingers'
    spec += [(lerp(Wb, Ht, 0.05 + 0.95 * i / 8), 116 + 7 * i, lens[i], 26 - 0.8 * i, 0.34) for i in range(9)]
    shade_m = np.zeros((c.H, c.W), np.float32)
    shade_v = np.zeros((c.H, c.W), np.float32)
    for b, ang, L, wd, ld in spec:
        ang += c.rng.normal(0, 1.6); L *= c.rng.uniform(0.96, 1.04)
        poly, rach, edge = c.feather(T_(b), ang, L * k, wd * k, curl=0.05, lead=ld, pressure=c.rng.uniform(0.62, 0.8), side=-1,
                                     overlapped=True)
        pm = c.poly_mask(poly)
        t = c.between(rach[0], rach[-1], edge[len(edge) // 3], edge[2 * len(edge) // 3])
        upd = pm > shade_m
        shade_v[upd] = t[upd]; shade_m = np.maximum(shade_m, pm)
    # tone: the broad vane darkens toward its edge, where the next feather shades it
    c.hatch(shade_m, np.clip(shade_v * 1.15 - 0.15, 0, 1) * 0.9, angle=55, spacing=4.6, levels=(0.42, 0.66), cross=None,
            width=1.6, ink=0.6, length=(14, 28), medium='chalk')
    # coverts: rows of short rounded feathers, only their lower edges drawn, rubbed into a soft band
    cov = np.zeros((c.H, c.W), np.float32)
    for L, wd, off, n in [(70, 15, 16, 13), (40, 11, 4, 15)]:
        for i in range(n):
            u = i / (n - 1)
            b = lerp(Sh, Wb, u / 0.45, off) if u < 0.45 else lerp(Wb, Ht, (u - 0.45) / 0.55, off)
            ang = np.deg2rad(86 + 18 * min(1, u / 0.45) + (40 * (u - 0.45) / 0.55 if u >= 0.45 else 0))
            d, nv = np.array([np.cos(ang), np.sin(ang)]), np.array([-np.sin(ang), np.cos(ang)])
            bb = np.array(T_(b)); Lk, wk = L * k, wd * k
            u_pts = [bb + d * Lk * 0.45 - nv * wk, bb + d * Lk * 0.92 - nv * wk * 0.55, bb + d * Lk, bb + d * Lk * 0.92 + nv * wk * 0.55,
                     bb + d * Lk * 0.45 + nv * wk]
            c.sanguine(u_pts, 2.0, 0.6)
            cov = np.maximum(cov, c.poly_mask([bb - nv * wk, *u_pts, bb + nv * wk]))
    c.rub(cov, 0.2, 3.0)
    c.hatch(cov, 0.5, angle=55, spacing=5.0, levels=(0.3,), cross=None, width=1.5, ink=0.45, length=(10, 20), medium='chalk')
    for i in range(3):                                    # the alula at the wrist
        c.feather(T_((Wb[0] - 2, Wb[1] - 4)), 196 + 9 * i, (52 - 8 * i) * k, 8 * k, curl=-0.05, pressure=0.7, line=2.0, rachis=False)
    arm = spline([T_(Sh), T_((-40, -22)), T_(El), T_((-130, -36)), T_(Wb), T_((-226, -16)), T_(Ht)], 10)
    c.sanguine(arm, 4.4, 0.95)
    c.sanguine(arm + [0, 4], 2.6, 0.6)


def feather_study(x0, y0, length, width):
    """one primary feather, large, pointing left: the bare quill, rachis, both vanes with their barbs drawn as
    fine chalk lines, a couple of splits where the barbs have parted"""
    poly, rach, edge = c.feather((x0, y0), 186, length, width, curl=0.05, lead=0.4, pressure=0.85, side=-1, line=2.4)
    a = np.deg2rad(6)
    c.sanguine([(x0, y0), (x0 + np.cos(a) * 46, y0 + np.sin(a) * 46)], 2.6, 0.9)          # the bare quill (calamus)
    idx = np.linspace(0, len(rach) - 1, int(length / 2.6)).astype(int)        # a barb every ~2.6 px
    tg = np.gradient(rach, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
    nv = np.stack([-tg[:, 1], tg[:, 0]], 1) * -1
    n = len(idx)
    gaps = set(range(int(n * 0.40), int(n * 0.43))) | set(range(int(n * 0.66), int(n * 0.68)))   # where barbs have parted
    strokes = []
    for k, i in enumerate(idx[2:-3]):
        u = k / n
        for sgn, wf in ((1, 1.0), (-1, 0.4)):
            if sgn == 1 and k in gaps: continue
            w_ = np.linalg.norm(edge[i] - rach[i]) * wf * c.rng.uniform(0.86, 0.98)
            p0 = rach[i]; p1 = p0 + nv[i] * sgn * w_ + tg[i] * w_ * (0.75 - 0.3 * u)
            strokes.append([p0, (p0 + p1) / 2 + nv[i] * sgn * 1.5 - tg[i] * 1.2, p1])
    c.sanguines(strokes, 0.95, 0.44, True, 0.15)


bird_wing(402, 230, 0.82)
feather_study(392, 482, 320, 40)
c.stage('uccello')

# ------------------------------------------------------------------ 3. the frame of the machine
# body: an almond-shaped cradle with cross bars, the crank housing in the middle
c.contour(np.vstack([BODY, BODY[:2]]), 2.4, 1.0, searching=1)
bars = []
for y, hw in [(236, 22), (300, 44), (488, 24), (560, 12)]:
    bars.append(c.cane((MX - hw, y), (MX + hw, y), 7, 7, 0, (), 1.5, 0.95, cap=False))
c.quill(c.arc(*HUB, 31), 2.2, 1.0, False, 0.2)
gear_pts = []
for k in range(48):
    a = 2 * np.pi * k / 48
    rr = 25 if (k // 2) % 2 == 0 else 20
    gear_pts.append((HUB[0] + np.cos(a) * rr, HUB[1] + np.sin(a) * rr))
c.quill(np.vstack([gear_pts, gear_pts[:1]]), 1.4, 0.9, False, 0.15)
c.quill(c.arc(*HUB, 6), 1.6, 1.0, False, 0.1)
for sgn in (1, -1):                                       # the pilot's crank handles
    c.cane((MX + sgn * 30, HUB[1] + 6), (MX + sgn * 64, HUB[1] + 34), 6, 5, 0, (), 1.4, 0.9)

# right wing: spars, finger ribs, hinges, the membrane's scalloped edge
spars = [c.cane(S, E, 10, 8, -10, (0.5,), 1.9), c.cane(E, WR, 8, 7, -6, (0.5,), 1.9), c.cane(WR, T, 7, 3, -10, (0.45,), 1.8)]
ribs = [c.cane(a, b, 6, 2.4, 12, (0.35,), 1.6) for a, b in RIBS]
edge = [scallop(p, q) for p, q in zip(TIPS[:-1], TIPS[1:])]
for e in edge: c.contour(e, 1.7, 0.95, searching=1, spread=1.6)
c.quill([S, TIPS[-1]], 1.6, 0.9)
for p, rr in [(S, 8), (E, 7), (WR, 7)]:
    c.quill(c.arc(p[0], p[1], rr), 1.8, 1.0, False, 0.15)
    c.blot(p[0], p[1], 1.6, 0.9, 0)
c.quill(c.arc(WR[0] - 2, WR[1] + 18, 13), 1.7, 1.0, False, 0.2)        # the pulley under the wrist
c.quill(c.arc(WR[0] - 2, WR[1] + 18, 8), 1.2, 0.8, False, 0.2)
# cords: from the crank housing over the shoulder, along the spar, round the pulley to each finger
cord = spline([HUB, (985, 360), (S[0] + 4, S[1] + 14), (1090, 270), (E[0] + 4, E[1] + 16), (1250, 258), (WR[0] - 14, WR[1] + 22)], 10)
c.quill(cord, 1.1, 0.8, True, 0.3)
for a, b in RIBS[:3]:
    m_ = (a[0] * 0.45 + b[0] * 0.55, a[1] * 0.45 + b[1] * 0.55)
    c.quill([(WR[0] + 8, WR[1] + 26), ((WR[0] + m_[0]) / 2 + 4, (WR[1] + m_[1]) / 2 + 8), m_], 1.0, 0.75, True, 0.3)

# tail: a fan of ribs with a scalloped edge
for tp in TAIL_TIPS: c.cane(TAIL, tp, 4, 1.8, 0, (), 1.3, 0.85, cap=False)
for p, q in zip(TAIL_TIPS[:-1], TAIL_TIPS[1:]): c.quill(scallop(p, q, 0.16, TAIL), 1.4, 0.85)

# left wing: only begun -- single light lines over the leadpoint, edge half drawn
c.quill(leading_edge(True), 1.7, 0.6)
for a, b in RIBS: c.quill(curve(mir(a), mir(b), -12, 16), 1.3, 0.5)
for i, (p, q) in enumerate(zip(TIPS[:-1], TIPS[1:])):
    if i in (0, 3, 4): c.quill(scallop(mir(p), mir(q)), 1.3, 0.5)
for p in (S, E, WR): c.quill(c.arc(mir(p)[0], mir(p)[1], 6), 1.4, 0.6, False, 0.2)
# a scale of braccia under the right wing
c.ruled((1112, 596), (1412, 596), 1.5, 0.85)
for i in range(7):
    x = 1112 + i * 50
    c.quill([(x, 590), (x, 603 if i % 2 == 0 else 599)], 1.3, 0.85, False, 0.05)
c.hatch(c.poly_mask([(1112, 593), (1162, 593), (1162, 599), (1112, 599)]), 0.8, spacing=2.6, levels=(0.3,), cross=None, ink=0.8,
        length=(6, 8))
c.stage('telaio')

# ------------------------------------------------------------------ 4. hatching: the membrane billows between ribs
canes = np.zeros((c.H, c.W), np.float32)
for p in spars + ribs + bars: canes = np.maximum(canes, c.poly_mask(p))
canes = np.clip(blur(canes, 1.5) * 3, 0, 1)
panels = [np.vstack([curve(WR, T, -10, 20), edge[0], curve(TIPS[1], WR, -12, 20)]),
          np.vstack([curve(WR, TIPS[1], 12, 20), edge[1], curve(TIPS[2], WR, -12, 20)]),
          np.vstack([curve(WR, TIPS[2], 12, 20), edge[2], curve(TIPS[3], WR, -12, 20)]),
          np.vstack([curve(WR, TIPS[3], 12, 20), edge[3], curve(TIPS[4], E, -12, 20), curve(E, WR, -6, 12)]),
          np.vstack([curve(E, TIPS[4], 12, 20), edge[4], [S], curve(S, E, -10, 16)])]
pairs = [((WR, T), RIBS[0]), (RIBS[0], RIBS[1]), (RIBS[1], RIBS[2]), (RIBS[2], RIBS[3]), (RIBS[3], (S, TIPS[-1]))]
for poly, (ra, rb) in zip(panels, pairs):
    m = c.poly_mask(poly) * (1 - canes)
    t = c.between(ra[0], ra[1], rb[0], rb[1])
    sh = np.clip(0.92 * t ** 2.0, 0, 1)
    c.hatch(m, sh, spacing=5.0, levels=(0.3, 0.56), cross=0.84, ink=0.72)
# body: rounded, darker toward the right
bm = c.poly_mask(BODY) * (1 - canes) * (1 - c.disc_mask(*HUB, 33))
c.hatch(bm, np.clip(0.12 + 0.75 * c.between((MX - 40, 0), (MX - 40, 1), (MX + 40, 0), (MX + 40, 1)) ** 1.3, 0, 1), spacing=4.6,
        levels=(0.3, 0.55), cross=0.82, ink=0.7)
# tail membrane, lightly
tm = c.poly_mask(np.vstack([[TAIL], np.vstack([scallop(p, q, 0.16, TAIL) for p, q in zip(TAIL_TIPS[:-1], TAIL_TIPS[1:])])]))
c.hatch(tm, 0.4, spacing=5.5, levels=(0.3,), cross=None, ink=0.6)
# left wing: a patch of hatching begun near the body and abandoned
YY, XX = np.mgrid[0:c.H, 0:c.W].astype(np.float32)
lm = c.poly_mask([mir(p) for p in panels[4]]) * ((YY < 420) & (XX > MX - 150))
c.hatch(lm, np.clip(0.95 - (MX - 30 - XX) / 150 - np.clip(YY - 330, 0, 99) / 140, 0, 1), spacing=5.2, levels=(0.4,), cross=None,
        ink=0.62, length=(18, 30))
c.stage('tratteggio')

# ------------------------------------------------------------------ 5. the proportion circle: the stroke seen from the front
ox, oy = O
c.quill(c.arc(ox, oy, R, -150, 30, step=2), 1.9, 0.95, False, 0.12)
c.quill(c.arc(ox, oy, R, 28, 212, step=2), 1.9, 0.9, False, 0.12)
c.quill(c.arc(ox, oy, r_lever, 0, 362, step=1.5), 1.4, 0.85, False, 0.1)
c.ruled((1522, oy), (1862, oy), 1.1, 0.6)
c.ruled((ox, 132), (ox, 458), 1.0, 0.5)
UP, DN = -36, 22
P_ = lambda ang, rad: (ox + np.cos(np.deg2rad(ang)) * rad, oy + np.sin(np.deg2rad(ang)) * rad)
sector = np.vstack([[O], c.arc(ox, oy, R, UP, DN)])
c.hatch(c.poly_mask(sector) * (1 - c.disc_mask(ox, oy, r_lever + 3)), 0.5, spacing=6, levels=(0.3,), cross=None, ink=0.55)
for ang in (DN, 180 - DN):                                 # wings down: drawn as canes (front view of the spar)
    c.cane(P_(ang, 10), P_(ang, R), 8, 3, 0, (0.5,), 1.7)
for ang in (UP, 180 - UP):                                 # wings up: a lighter, dashed position
    c.dotted([P_(ang, 12), P_(ang, R)], 9, 6, 1.5, 0.8)
for ang in (DN + 180, UP + 180):                           # the short lever beyond the pivot
    c.quill([O, P_(ang, r_lever)], 3.0, 1.0, False, 0.1)
    c.blot(*P_(ang, r_lever), 2.0, 0.9, 0)
for i in range(1, 4):                                      # the wing divided into four lever-lengths
    p = P_(DN, r_lever * i); n_ = np.deg2rad(DN + 90)
    c.quill([(p[0] - np.cos(n_) * 6, p[1] - np.sin(n_) * 6), (p[0] + np.cos(n_) * 6, p[1] + np.sin(n_) * 6)], 1.3, 0.9, False, 0.1)
for a in range(-40, 31, 6):                                # degree ticks on the rim
    p0, p1 = P_(a, R + 2), P_(a, R + (9 if a % 30 == 0 else 5))
    c.quill([p0, p1], 1.1, 0.8, False, 0.05)
c.arrow(c.arc(ox, oy, R + 18, UP + 3, DN - 3)[::-1], 1.5, 0.9, 9)
c.arrow(c.arc(ox, oy, R + 18, UP + 3, DN - 3), 1.5, 0.9, 9)
c.prick(ox, oy, 1.4)
c.stage('cerchio')

# ------------------------------------------------------------------ 6. the drive, exploded; the wrist joint close up
cam = Camera(1520, 818, 1.0, azim=22, elev=29)
wheel = crown(104, 14, teeth=18, tooth_h=19, tooth_w=13)
axle_v = cylinder(8, 112, 16, 'axle_end', 'axle', -112)
pul = pulley(28, 32).place((0, 0, -164))
pinion = lantern(30, 60, 8).place((-30, 92, 126), axis=(1, 0, 0))
shaft = cylinder(6.5, 250, 16, 'shaft_end', 'shaft').place((-206, 92, 126), axis=(1, 0, 0))
handle = crank(58, 6.5, 60, 9.0).place((-262, 92, 126), axis=(-1, 0, 0), spin=90)
drive = merge(wheel.named('wheel'), axle_v.named('axle'), pul.named('pulley'), pinion.named('pinion'), shaft.named('shaft'),
              handle.named('crank'))
c.solid(drive, cam, width=2.0, hatch=dict(spacing=4.4, levels=(0.3, 0.56), cross=0.84),
        hatch_groups={'pinion.disc': dict(levels=(0.45,)), 'wheel.face': dict(levels=(0.5,), cross=None)})
pr = lambda p: cam.project(np.array([p], np.float32))[0][0]
c.dotted([pr((-254, 92, 126)), pr((-212, 92, 126))], 7, 5, 1.2, 0.7, dot_dash=True)       # the crank slides onto the shaft
c.dotted([pr((50, 92, 126)), pr((120, 92, 126))], 9, 5, 1.2, 0.7, dot_dash=True)
c.dotted([pr((0, 92, 94)), pr((0, 92, 38))], 6, 5, 1.2, 0.7, dot_dash=True)              # the pinion drops onto the pegs
c.dotted([pr((0, 0, -116)), pr((0, 0, -130))], 5, 4, 1.2, 0.7, dot_dash=True)            # the pulley slides up the axle
# the cord leaves the pulley toward the wings
p0 = pr((-28, 0, -150))
CORD_END = (p0[0] - 150, p0[1] - 34)
c.quill([p0, (p0[0] - 70, p0[1] - 4), CORD_END], 1.1, 0.8)

# close-up of the wrist joint in a circle
J = (768, 884)
c.quill(c.arc(*J, 104, -80, 275, step=2), 1.4, 0.7, False, 0.3)
jc = [c.cane((686, 916), (752, 890), 18, 16, 3, (0.35,), 1.8)]
for b, bend in [((846, 818), 6), ((862, 892), 4), ((826, 960), -4)]:
    jc.append(c.cane((J[0] + 6, J[1] - 2), b, 15, 10, bend, (0.55,), 1.8))
for rr, w in [(23, 2.0), (16, 1.4)]:
    c.quill(c.arc(J[0], J[1] - 1, rr), w, 1.0, False, 0.15)
c.blot(J[0], J[1] - 1, 3.2, 1.0, 0)
c.quill(spline([(690, 856), (730, 862), (J[0] - 4, J[1] - 24), (J[0] + 18, J[1] - 16)], 10), 1.2, 0.85)
c.quill(spline([(694, 866), (732, 870), (J[0] - 10, J[1] - 22)], 10), 1.0, 0.75)
for p in jc:
    pm = c.poly_mask(p)
    q = p[: len(p) // 2]
    t = c.between(q[0], q[-1], p[-1], p[len(p) // 2])
    c.hatch(pm * (1 - c.disc_mask(J[0], J[1] - 1, 25)), np.clip(t * 1.1 - 0.1, 0, 1), spacing=3.8, levels=(0.4, 0.66), cross=None,
            ink=0.75, length=(10, 20))
# a rejected idea: a wing of hinged boards (louvres), struck out later
REJ = (936, 806)
c.quill([(REJ[0], REJ[1] + 44), (REJ[0] + 128, REJ[1])], 2.0, 0.95)
c.quill([(REJ[0] + 4, REJ[1] + 82), (REJ[0] + 126, REJ[1] + 50)], 1.6, 0.9)
lv = []
for i in range(6):
    x = REJ[0] + 10 + i * 20; y = REJ[1] + 41 - i * 6.6
    c.quill([(x, y), (x + 9, y + 36 - i * 1.2)], 1.5, 0.9)
    lv.append([(x, y), (x + 9, y + 36 - i * 1.2), (x + 20, y + 30 - i * 1.2), (x + 11, y - 6.6)])
for q in lv[1::2]: c.hatch(c.poly_mask(q), 0.6, spacing=3.6, levels=(0.3,), cross=None, ink=0.7, length=(8, 14))
c.stage('ingranaggi')

# ------------------------------------------------------------------ 7. the notes, mirror-written right to left
c.write(['Dell ala che batte e del suo moto'], 1452, 104, size=29, ink=1.0)
c.write(c.prose(14), 1452, 140, width=470, size=19, max_lines=1)
c.write(c.prose(70), 566, 586, width=486, size=20, max_lines=7)
c.write(c.prose(40), 1866, 512, width=392, size=19, max_lines=4)
c.write(c.prose(100), 616, 812, width=548, size=20, max_lines=9)
c.write(c.prose(60), 1868, 676, width=196, size=19, max_lines=14)
for s_, p in [('a', (S[0] + 8, S[1] - 18)), ('b', (E[0] + 2, E[1] - 20)), ('c', (WR[0] + 4, WR[1] - 18)), ('d', (T[0] + 16, T[1] + 4)),
              ('n', (1060, 286)), ('m', (MX + 46, HUB[1] - 18))]:
    c.label(s_, *p, size=22)
for s_, p in [('a', (ox - 14, oy - 8)), ('b', P_(UP, R + 34)), ('c', P_(DN, R + 34)), ('d', P_(UP + 180, r_lever + 16)), ('1', P_(DN, r_lever - 2)),
              ('4', P_(DN, R - 18))]:
    c.label(s_, p[0], p[1] + 7, size=21)
for s_, p in [('e', pr((-262, 92, 200))), ('f', pr((-30, 92, 186))), ('g', pr((112, -70, 20))), ('h', pr((46, 0, -160)))]:
    c.label(s_, p[0], p[1], size=22)
c.label('c', J[0] - 96, J[1] - 70, size=24)
c.label('n', CORD_END[0] - 12, CORD_END[1] + 4, size=22)
for i, n_ in enumerate(['0', '2', '4', '6']):
    c.label(n_, 1112 + i * 100, 624, size=18)
c.label('37', 1842, 72, size=22, ink=0.55, mirror=False)                    # a later collector's folio number
c.stage('note')

# ------------------------------------------------------------------ 8. corrections and accidents
c.strike(REJ[0] - 4, REJ[1] - 4, REJ[0] + 132, REJ[1] + 86, n=3, width=1.9)
c.blot(1212, 132, 6.5, 1.3, 6)
c.blot(642, 742, 3.5, 1.2, 3)
c.spatter(1500, 470, 8, 18, 0.9)
c.spatter(330, 590, 5, 14, 0.8)

c.save(out, stages)
print(f'{out}  {time.time() - t0:.1f}s')
