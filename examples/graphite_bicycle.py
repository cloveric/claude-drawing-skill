"""Example (graphite pencil drawing): The Bread Run / 老街角的自行车 — a step-through town bicycle leaning against
a plastered wall at an old street corner, a baguette and a paper cone of tulips in its front basket; a bakery's
hanging sign (a loaf, no words) over the side street, a street plate, a bare patch of brick, a deep doorway,
cobbles. Drawn the way a pencil drawing is made: light construction lines (horizon, lines to the vanishing point,
wheel ellipses with their axes), contours, side-of-the-lead tone, hatching built up in layers, the darks pressed
in, a stump to blend, erasers to pull out the light (rims, tube highlights, the lit corner), details last. Only
the middle is finished: toward the edges of the sheet the tone thins out and the drawing is left as bare lines.
Margin notes, the pencil swatches the artist tried, a thumbprint. No image model.
python3 graphite_bicycle.py [out.png] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from PIL import Image, ImageDraw
from graphite import Graphite
from core import spline, blur, shift, smoothstep, noise2d

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'graphite_bicycle.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
T0 = time.time()
tick = lambda name: print(f'{name:12s} {time.time() - T0:5.1f}s') if os.environ.get('GRAPHITE_TIMING') else None

W, H = 1920, 1080
g = Graphite(W, H, seed=11)
rng = g.rng
g.paper()
g.focus(820, 580, 700, 440, soft=0.45, rough=0.22)

HZ, VP = 410.0, np.array([1640.0, 410.0])       # eye level and the vanishing point of the side street
GY, CURB, CX = 790.0, 872.0, 1250.0              # wall base, curb edge, building corner
LIGHT = np.array([-0.6, -0.8])                   # towards the sun: upper left


def toward_vp(p, s):
    p = np.asarray(p, np.float32)
    return p + (VP - p) * s


def offset(P, d):
    P = spline(P, 10) if len(P) > 2 else np.asarray(P, np.float32)
    t = np.gradient(P, axis=0); t /= (np.linalg.norm(t, axis=1, keepdims=True) + 1e-6)
    n = np.stack([-t[:, 1], t[:, 0]], 1)
    return P + n * d


def shadow_sign(P):
    """+1 if the left-hand normal of the path points away from the light"""
    P = np.asarray(P, np.float32)
    t = P[-1] - P[0]; n = np.array([-t[1], t[0]])
    return 1.0 if n @ LIGHT < 0 else -1.0


def angle_field(c):
    yy, xx = np.arange(H, dtype=np.float32)[:, None], np.arange(W, dtype=np.float32)[None, :]
    return np.arctan2(yy - np.float32(c[1]), xx - np.float32(c[0]))


L = lambda pts, grade='HB', p=0.62, **k: g.line(pts, grade, p, **k)

# ===================================================================== geometry
RH, FH = np.array([520.0, 668.0]), np.array([1060.0, 668.0])     # hubs
RT, RR, RI = 176.0, 160.0, 150.0                                   # tyre outer, rim outer, rim inner
BB = np.array([745.0, 700.0])
SC = np.array([690.0, 452.0])
HT, HB = np.array([990.0, 444.0]), np.array([1004.0, 506.0])
FRAME_TUBES = {   # painted frame: name -> (points, width)
    'main': ([(996, 468), (950, 500), (870, 568), (800, 640), (756, 690)], 17),
    'seat': ([(BB[0] - 4, BB[1] - 8), (718, 580), SC], 15),
    'chainstay': ([BB, (630, 686), RH], 9),
    'seatstay': ([(SC[0] + 2, SC[1] + 22), (610, 560), RH], 8),
    'head': ([HT, HB], 19),
    'fork': ([(HB[0], HB[1] - 4), (1016, 570), (1040, 630), FH], 11),
}
CHROME_TUBES = {  # bright parts: seat post, stem, bars, rack, crank
    'post': ([SC, (682, 414)], 10),
    'stem': ([HT, (993, 404)], 10),
    'bar': ([(993, 404), (1012, 396), (990, 386), (950, 388), (918, 394)], 8),
    'rack': ([(445, 472), (560, 469), (700, 466)], 7),
    'rackstrut1': ([(452, 474), (500, 560), RH], 5),
    'rackstrut2': ([(585, 470), (552, 560), RH], 5),
    'crank': ([BB, (788, 774)], 12),
}
TUBES = {**FRAME_TUBES, **CHROME_TUBES}
SADDLE = [(612, 392), (640, 383), (690, 384), (728, 392), (744, 402), (728, 408), (690, 412), (650, 418), (618, 414)]
BASKET = [(1016, 398), (1192, 392), (1182, 506), (1030, 508)]
BAGUETTE = [(1030, 430), (1268, 306)]
CONE = [(1084, 394), (1170, 384), (1128, 478)]
GRIP = ([(944, 389), (906, 396)], 13)
FLOWERS = [(1094, 346, -14), (1128, 326, 3), (1162, 350, 18)]
FENDERS = [(RH, 160, 302), (FH, 212, 352)]
fend = lambda P0, a0, a1: g.circle_pts(P0[0], P0[1], 188, None, a0, a1)

# opaque silhouette of the bicycle (what hides the wall behind it; spokes are see-through)
opq = np.zeros((H, W), np.float32)
for P0 in (RH, FH):
    np.maximum(opq, g.ring(P0[0], P0[1], RI, RT + 0.5), out=opq)
    np.maximum(opq, g.ellipse(P0[0], P0[1], 18, 18), out=opq)
for name, (P, w) in TUBES.items():
    np.maximum(opq, g.band(P, w), out=opq)
for P0, a0, a1 in FENDERS:
    np.maximum(opq, g.band(fend(P0, a0, a1), 12, smooth=False), out=opq)
for m in (g.poly(SADDLE), g.band(*GRIP), g.poly(BASKET), g.band(BAGUETTE, 34), g.poly(CONE),
          g.ellipse(BB[0], BB[1], 48, 48), g.rect(768, 768, 814, 782)):
    np.maximum(opq, m, out=opq)
for fx, fy, rot in FLOWERS:
    np.maximum(opq, g.ellipse(fx, fy, 17, 23, rot), out=opq)
open_ = 1 - opq

# the hanging sign in front of the side wall
SIGN = (1372, 236, 66, 50)
sign_m = np.maximum(g.ellipse(*SIGN), g.band([(CX + 8, 140), (1446, 140)], 6))

# building masks
front_wall = g.rect(-5, -5, CX, GY, 0.6)
top_c, base_c = np.array([CX, -1400.0]), np.array([CX, GY])     # the building is three storeys tall
SIDE_END = 0.72
side_far = smoothstep(1545, 1360, np.arange(W, dtype=np.float32)[None, :] + 90 * (noise2d(H, W, 70, 2, 5) - 0.5))   # tone stops short, raggedly
side_wall = g.poly([top_c, toward_vp(top_c, SIDE_END), toward_vp(base_c, SIDE_END), base_c]) * (1 - sign_m)
DOOR = (150, 205, 372, GY)                                           # door leaf
FRAME = (118, 172, 404, GY)                                          # stone surround
plaster = front_wall * (1 - g.rect(*FRAME))
tick('geometry')

# ===================================================================== 1. construction
g.guide((0, HZ), (W, HZ), '2H', 0.42, (0, 0))
for p in [(CX, -60), (CX, GY), (CX, CURB), (1318, CURB + 2), (FRAME[2], FRAME[1]), (-200, GY + 40), (1930, 30), (1930, 660)]:
    g.guide(p, VP, '2H', 0.4, (0, 20))
g.guide((CX, 0), (CX, 1000), '2H', 0.4, (0, 0))
for P0 in (RH, FH):
    g.guide_ellipse(P0[0], P0[1], RT, RT, 0, loops=2, pressure=0.42)
g.guide(RH, BB, '2H', 0.4, (8, 20)); g.guide(BB, SC, '2H', 0.4, (8, 30)); g.guide(SC, HT, '2H', 0.36, (10, 30))
g.guide(HT, FH, '2H', 0.4, (10, 20)); g.guide((440, RH[1] + RT), (1140, FH[1] + RT), '2H', 0.38)
g.guide((FRAME[0], FRAME[1]), (FRAME[0], 860), '2H', 0.36)
g.stage('construction')
tick('construction')

# ===================================================================== 2. contours
# corner, wall base, sidewalk, curb
L([(CX, -10), (CX, GY)], 'HB', 0.7, smooth=False, lost=0.15)
L([(-10, GY), (CX, GY)], 'HB', 0.6, smooth=False, lost=0.25)
L([base_c, toward_vp(base_c, SIDE_END)], 'HB', 0.55, smooth=False)
L([toward_vp(top_c, SIDE_END), toward_vp(base_c, SIDE_END)], 'H', 0.45, smooth=False)
L([(-10, CURB), (1270, CURB), (1300, CURB - 8)], 'HB', 0.6)
L([(-10, CURB + 16), (1275, CURB + 16), (1318, CURB + 2)], 'H', 0.5)
L([(1300, CURB - 8), toward_vp((1300, CURB - 8), 0.55)], 'H', 0.45, smooth=False)
L([(1318, CURB + 2), toward_vp((1318, CURB + 2), 0.55)], 'H', 0.45, smooth=False)
# door, frame, step
L([(FRAME[0], GY), (FRAME[0], FRAME[1]), (FRAME[2], FRAME[1]), (FRAME[2], GY)], 'HB', 0.6, smooth=False, searching=1)
L([(DOOR[0], GY), (DOOR[0], DOOR[1]), (DOOR[2], DOOR[1]), (DOOR[2], GY)], 'HB', 0.55, smooth=False)
L([(FRAME[0] - 14, GY + 2), (FRAME[2] + 14, GY + 2), (FRAME[2] + 20, GY + 24), (FRAME[0] - 20, GY + 24)], 'HB', 0.55, smooth=False, closed=True)
PANELS = [(x0, y0, x1, y1) for (y0, y1) in [(236, 470), (520, 760)] for (x0, x1) in [(170, 252), (270, 352)]]
for (x0, y0, x1, y1) in PANELS:                                             # door panels
    L([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'HB', 0.55, smooth=False, closed=True)
# window above the door (left unfinished: lines only)
L([(150, -10), (150, 110), (372, 110), (372, -10)], 'H', 0.5, smooth=False)
L([(140, 118), (382, 118), (386, 130), (136, 130)], 'H', 0.45, smooth=False, closed=True)
L([(261, -10), (261, 110)], 'H', 0.4, smooth=False)
# a first-floor window with open louvred shutters above the bike (bare lines toward the top of the sheet)
L([(690, -10), (690, 112), (880, 112), (880, -10)], 'HB', 0.55, smooth=False)
L([(676, 114), (894, 114), (900, 128), (670, 128)], 'HB', 0.6, smooth=False, closed=True)
L([(785, -10), (785, 112)], 'H', 0.45, smooth=False)
for (x0, x1) in [(628, 686), (884, 942)]:
    L([(x0, -10), (x0, 110), (x1, 110), (x1, -10)], 'H', 0.5, smooth=False)
    g.strokes([[(x0 + 4, y), (x1 - 4, y + 3)] for y in np.arange(4, 106, 9)], 'H', 0.45, width=1.2, taper=(0.1, 0.1), fade=0.3)
# quoins on the corner
QUOINS = []
for k, y in enumerate(np.arange(-40, GY - 20, 52)):
    x0 = 1168 if k % 2 == 0 else 1198
    QUOINS.append((x0, y))
    L([(x0, y + 2), (x0, y + 50), (CX, y + 50)], 'H', 0.5, smooth=False, lost=0.3)
# side facade: shop window, door, windows above
sw = [toward_vp((CX, 360), 0.10), toward_vp((CX, 360), 0.30), toward_vp((CX, 720), 0.30), toward_vp((CX, 720), 0.10)]
L(sw + [sw[0]], 'HB', 0.55, smooth=False)
sd = [toward_vp((CX, 420), 0.38), toward_vp((CX, 420), 0.47), toward_vp((CX, GY), 0.47), toward_vp((CX, GY), 0.38)]
L(sd, 'H', 0.5, smooth=False)
for s0, s1 in [(0.08, 0.22), (0.30, 0.42), (0.50, 0.60)]:
    win = [toward_vp((CX, 40), s0), toward_vp((CX, 40), s1), toward_vp((CX, 230), s1), toward_vp((CX, 230), s0)]
    L(win + [win[0]], 'H', 0.5, smooth=False)
# the far buildings beyond the side street (bare lines)
L([(1930, 30), toward_vp((1930, 30), 0.86)], 'H', 0.45, smooth=False)
L([(1930, 660), toward_vp((1930, 660), 0.86)], 'H', 0.45, smooth=False)
for s in (0.18, 0.42, 0.62, 0.78):
    L([toward_vp((1930, 30), s), toward_vp((1930, 660), s)], 'H', 0.45, smooth=False, lost=0.2)
for s0, s1 in [(0.05, 0.14), (0.25, 0.33), (0.48, 0.55)]:
    for (ya, yb) in [(120, 250), (340, 470)]:
        win = [toward_vp((1930, ya), s0), toward_vp((1930, ya), s1), toward_vp((1930, yb), s1), toward_vp((1930, yb), s0)]
        L(win + [win[0]], 'H', 0.4, smooth=False, lost=0.25)
L([(1700, 300), (1700, 240), (1712, 224), (1724, 240), (1724, 300)], 'H', 0.45, smooth=False)    # far bell turret
L([(1690, 300), (1734, 300)], 'H', 0.4, smooth=False)
# the hanging bakery sign: iron bracket from the side wall, oval board, a loaf on it
L([(CX + 8, 140), (1446, 140)], '2B', 0.8, smooth=False)
L([(CX + 8, 196), (1290, 170), (1330, 150), (1360, 142)], 'HB', 0.65)
L(g.circle_pts(1300, 166, 15, 15, 180, 520), 'HB', 0.6)
for x in (1336, 1408):
    L([(x, 141), (x, 187)], 'HB', 0.65, smooth=False)
L(g.circle_pts(*SIGN[:2], SIGN[2], SIGN[3]), '2B', 0.75, closed=True)
L(g.circle_pts(*SIGN[:2], SIGN[2] - 7, SIGN[3] - 7), 'H', 0.55, closed=True)
L(g.circle_pts(1372, 238, 40, 17, 0, 360, rot=-8), 'HB', 0.7, closed=True)
# street plate
PLATE = (1022, 206, 1160, 254)
L([(PLATE[0], PLATE[1]), (PLATE[2], PLATE[1]), (PLATE[2], PLATE[3]), (PLATE[0], PLATE[3])], 'HB', 0.6, smooth=False, closed=True)
# bare brick patch: broken plaster edge
patch_pts = np.array([(430, 214), (470, 182), (540, 176), (600, 190), (668, 178), (724, 210), (742, 262),
                      (716, 318), (650, 336), (580, 326), (520, 344), (462, 318), (438, 270)], np.float32)
patch = g.poly(spline(np.vstack([patch_pts, patch_pts[:1]]), 8), 0.8)
L(np.vstack([patch_pts, patch_pts[:1]]), 'HB', 0.6, lost=0.1)
# the bicycle: tyres, rims, fenders, frame, saddle, basket and its load
for P0 in (RH, FH):
    L(g.circle_pts(P0[0], P0[1], RT, RT, 0, 360), '2B', 0.75, closed=True, searching=1)
    L(g.circle_pts(P0[0], P0[1], RR, RR, 0, 360), 'HB', 0.6, closed=True)
    L(g.circle_pts(P0[0], P0[1], RI, RI, 0, 360), 'HB', 0.55, closed=True)
for P0, a0, a1 in FENDERS:
    L(g.circle_pts(P0[0], P0[1], 182, 182, a0, a1), 'HB', 0.6)
    L(g.circle_pts(P0[0], P0[1], 194, 194, a0, a1), 'HB', 0.6)
tube_edges = {}
for name, (P, w) in TUBES.items():
    s = shadow_sign(P)
    lit_e, dark_e = offset(P, -s * w / 2), offset(P, s * w / 2)
    tube_edges[name] = (lit_e, dark_e, s)
    L(lit_e, 'HB', 0.55, lost=0.3, smooth=False)
    L(dark_e, '2B', 0.7, smooth=False)
L(np.vstack([SADDLE, SADDLE[:1]]), '2B', 0.7)
L(np.vstack([BASKET, BASKET[:1]]), 'HB', 0.6)
L(offset(BAGUETTE, -17), 'HB', 0.6, lost=0.2); L(offset(BAGUETTE, 17), '2B', 0.65)
for e, c0 in ((BAGUETTE[0], 160), (BAGUETTE[1], -20)):
    L(g.circle_pts(e[0], e[1], 17, 17, c0 - 62, c0 + 118), 'HB', 0.6)
L(np.vstack([CONE, CONE[:1]]), 'HB', 0.6)
L(g.circle_pts(BB[0], BB[1], 46, 46, 0, 360), 'HB', 0.6, closed=True)
L(g.circle_pts(RH[0], RH[1], 20, 20, 0, 360), 'HB', 0.6, closed=True)
L([(768, 768), (814, 768), (814, 782), (768, 782)], '2B', 0.6, smooth=False, closed=True)
g.stage('contours')
tick('contours')

# ===================================================================== 3. block-in: side of the lead
sh_off = (78, 30)                                                   # cast shadow of the bike on the wall
spokes_lines = []
for P0, rot0 in ((RH, 3.0), (FH, 8.0)):
    for i in range(32):
        a = np.deg2rad(rot0 + i * 360 / 32)
        sgn = 1 if i % 2 else -1
        h0 = P0 + 21 * np.array([np.cos(a), np.sin(a)])
        b = a + sgn * np.deg2rad(26)
        spokes_lines.append(np.array([h0, P0 + RI * np.array([np.cos(b), np.sin(b)])], np.float32))
spk = g.lines_mask(spokes_lines, 1.5, 0.6)
cast = blur(shift(opq, *sh_off), 1.0)
cast_wall = cast * front_wall * open_
del spk, cast
cast_ground = blur(g.poly([(RH[0] - 40, RH[1] + RT - 2), (RH[0] + 260, RH[1] + RT - 6), (FH[0] + 40, FH[1] + RT - 2),
                           (FH[0] + 150, GY + 4), (RH[0] + 70, GY + 4)]), 5) * open_ * (1 - front_wall)
xramp = np.clip((np.arange(W, dtype=np.float32) - CX) / 260, 0, 1)[None, :]
side_tone = (0.46 + 0.1 * xramp) * np.ones((H, 1), np.float32)
g.shade(side_wall * open_ * side_far, side_tone, angle=80, grade='4B', width=10, pressure=0.34)
wall_light = g.linear((300, 100), (1200, 760))
g.shade(plaster * open_, 0.12 + 0.12 * wall_light, angle=12, grade='2B', width=11, pressure=0.22)
dampband = g.poly([(-10, 690), (200, 702), (420, 684), (700, 708), (980, 690), (CX, 702), (CX, GY), (-10, GY)], 14)
g.shade(dampband * plaster * open_, 0.42, angle=8, grade='4B', width=10, pressure=0.3)
door_m = g.rect(DOOR[0], DOOR[1], DOOR[2], GY) * open_
g.shade(door_m, 0.4, angle=88, grade='4B', width=9, pressure=0.3)
for P0 in (RH, FH):
    g.shade(g.ring(P0[0], P0[1], RR, RT), 0.85, angle=30, grade='6B', width=7, pressure=0.45, finish=False)
for name, (P, w) in FRAME_TUBES.items():
    g.shade(g.band(P, w), 0.6, angle=np.degrees(np.arctan2(P[-1][1] - P[0][1], P[-1][0] - P[0][0])), grade='4B', width=6, pressure=0.4, finish=False, passes=2)
g.shade(g.poly(SADDLE), 0.7, angle=10, grade='6B', width=7, pressure=0.4, finish=False)
g.shade(cast_ground, 0.55, angle=5, grade='4B', width=10, pressure=0.33)
sidewalk = g.rect(-5, GY, 1330, CURB, 0.6)
g.shade(sidewalk * open_, 0.16 + 0.12 * g.linear((0, GY), (0, CURB)), angle=4, grade='2B', width=12, pressure=0.22)
g.stage('block_in')
tick('block_in')

# ===================================================================== 4. hatching: middle values
g.hatch(side_wall * open_ * side_far, side_tone, angle=86, grade='2B', spacing=4.0, length=(50, 90), layers=(0, 0, 25))
g.hatch(cast_wall, 0.4, angle=58, grade='2B', spacing=4.0, length=(34, 70), layers=(0, 0, -62))
g.hatch(cast_ground, 0.6, angle=4, grade='2B', spacing=3.6, length=(40, 80), layers=(0, 0, 55))
# plaster: a breath of hatching where the wall turns away from the light, darker near the corner and the damp
g.hatch(plaster * open_ * (1 - patch), 0.2 * wall_light + 0.16 * dampband, angle=62,
        grade='HB', spacing=4.6, length=(40, 80), layers=(0, 0))
cracks = [[(744, 250), (790, 262), (812, 298), (860, 306)], [(812, 298), (820, 340)], [(438, 300), (400, 330), (384, 380)],
          [(1100, 560), (1124, 600), (1118, 640)], [(60, 420), (84, 452), (80, 500), (104, 520)]]
for c in cracks:
    L(c, 'HB', 0.5, lost=0.2)
# bricks in the patch: course by course, each brick its own value; mortar left light
bricks = np.zeros((H, W), np.float32); brick_tone = np.zeros((H, W), np.float32)
for row, y in enumerate(np.arange(160, 360, 39)):
    x = 400 - (59 if row % 2 else 0)
    while x < 760:
        bw = 118 + rng.normal(0, 3)
        m = g.poly([(x + 4 + rng.normal(0, 1), y + 4), (x + bw - 4, y + 4 + rng.normal(0, 1)), (x + bw - 5, y + 35), (x + 5, y + 35 + rng.normal(0, 1))], 0.8)
        np.maximum(bricks, m, out=bricks)
        np.maximum(brick_tone, m * rng.uniform(0.38, 0.66), out=brick_tone)
        x += bw
bricks *= patch; brick_tone *= patch
under_edge = blur(patch * (1 - shift(patch, 6, 8)), 3) * patch                 # the plaster lip casts a shadow inside
g.hatch(bricks * open_, brick_tone + 0.25 * under_edge, angle=-22, grade='2B', spacing=3.6, length=(30, 60), layers=(0, 0, 70))
g.hatch(patch * (1 - bricks) * open_, 0.22 + 0.4 * under_edge, angle=40, grade='HB', spacing=3.4, length=(20, 40), layers=(0,))
del bricks, brick_tone
# door: vertical planks, darker toward the recess
g.hatch(door_m, 0.42 + 0.18 * g.linear((DOOR[2], 0), (DOOR[0], 0)), angle=90, grade='2B', spacing=4.0, length=(70, 140), layers=(0, 0, 20))
jamb = g.poly([(DOOR[0] - 26, DOOR[1] - 26), (DOOR[0], DOOR[1]), (DOOR[0], GY), (DOOR[0] - 26, GY)]) * open_
soffit = g.poly([(DOOR[0] - 26, DOOR[1] - 26), (DOOR[2] + 4, DOOR[1] - 26), (DOOR[2], DOOR[1]), (DOOR[0], DOOR[1])])
recess = np.maximum(jamb, soffit)
g.hatch(recess, 0.8, angle=70, grade='4B', spacing=3.4, length=(40, 80))
g.hatch(g.poly([(670, 129), (900, 129), (894, 142), (676, 142)]), 0.7, 20, '2B', 3.2, (20, 40), (0, 0))     # under the sill
for (x0, y0, x1, y1) in PANELS:
    lip = np.maximum(g.rect(x0, y0, x1, y0 + 7), g.rect(x0, y0, x0 + 7, y1))
    g.hatch(lip, 0.85, 45, '4B', 3.0, (8, 16), (0, 0))
    L([(x0 + 2, y1 - 2), (x1 - 2, y1 - 2), (x1 - 2, y0 + 2)], 'HB', 0.4, smooth=False)
# shop window on the shaded side wall: dark glass
swm = g.poly(sw) * open_
g.hatch(swm * side_far, 0.85, angle=84, grade='4B', spacing=3.4, length=(40, 90))
# sidewalk slabs: joints toward the vanishing point, light hatching, curb face
for x in np.arange(-140, 1320, 170):
    p0 = np.array([x, CURB]); p1 = p0 + (VP - p0) * ((CURB - GY) / (CURB - HZ))
    L([p0, p1], 'HB', 0.5, smooth=False, lost=0.25)
L([(-10, 828), (1262, 828)], 'H', 0.45, smooth=False, lost=0.35)
g.hatch(sidewalk * open_ * (1 - cast_ground), 0.2, angle=2, grade='HB', spacing=5, length=(60, 120), layers=(0,))
g.hatch(g.rect(-5, CURB, 1290, CURB + 16), 0.55, angle=88, grade='2B', spacing=3.6, length=(14, 18), layers=(0, 0))
# tyres: strokes that run around the wheel; rims and fenders
for P0 in (RH, FH):
    arcs = []
    for r_ in np.arange(RR + 1.5, RT, 2.6):
        a = rng.uniform(0, 360)
        while a < 720:
            da = rng.uniform(28, 55)
            arcs.append(g.circle_pts(P0[0], P0[1], r_, r_, a, a + da))
            a += da + rng.uniform(-3, 4)
    lit = np.clip(np.cos(angle_field(P0) - np.deg2rad(-125)), 0, 1)
    g.contour_hatch(arcs, g.ring(P0[0], P0[1], RR, RT), 0.95 - 0.35 * lit ** 2, '6B', 0.75, finish=False)
    g.contour_hatch([g.circle_pts(P0[0], P0[1], r_, r_, a0, a0 + 70) for r_ in (152, 155.5, 158.5) for a0 in np.arange(0, 360, 66)],
                    g.ring(P0[0], P0[1], RI, RR), 0.25 + 0.45 * (1 - lit), 'HB', 0.6, finish=False)
    del lit
for P0, a0, a1 in FENDERS:
    fm = g.band(fend(P0, a0, a1), 12, smooth=False)
    g.contour_hatch([g.circle_pts(P0[0], P0[1], r_, r_, a0, a1) for r_ in (184, 187, 190, 193)], fm, 0.4, '2B', 0.5, finish=False)
    g.contour_hatch([g.circle_pts(P0[0], P0[1], r_, r_, a0, a1) for r_ in (190.5, 192.5)], fm, 0.9, '4B', 0.7, finish=False)
# frame tubes: strokes along the tube, pressing harder toward the side away from the light
for name, (P, w) in TUBES.items():
    lit_e, dark_e, s = tube_edges[name]
    dark = name in FRAME_TUBES
    for f in np.linspace(-0.42, 0.42, max(3, int(w / 2.6))):
        k = smoothstep(-0.35, 0.3, f) * (1 - 0.35 * smoothstep(0.32, 0.45, f))      # reflected light at the far edge
        pr = (0.32 + 0.55 * k) if dark else (0.08 + 0.55 * k ** 2)
        g.strokes([offset(P, s * w * f)], '4B' if dark else '2B', pr, width=2.0, taper=(0.03, 0.06), wobble=0.15, smooth=False, gain=1.2)
g.stage('hatching')
del wall_light, under_edge, swm, jamb, soffit, xramp
tick('hatching')

# ===================================================================== 5. darks
g.hatch(cast_wall * blur(shift(opq, 30, 12), 3), 0.4, angle=-30, grade='2B', spacing=3.8, length=(30, 60), layers=(0, 0))
g.hatch(recess, 0.95, angle=-20, grade='6B', spacing=3.2, length=(40, 80), layers=(0, 0))
contact = np.maximum(g.ellipse(RH[0] + 12, RH[1] + RT - 2, 46, 6, feather=4), g.ellipse(FH[0] + 12, FH[1] + RT - 2, 46, 6, feather=4))
g.shade(contact * open_, 0.9, angle=0, grade='8B', width=6, pressure=0.6, finish=False)
for P0 in (RH, FH):
    g.contour_hatch([g.circle_pts(P0[0], P0[1], r_, r_, 300, 480) for r_ in np.arange(RR + 3, RT - 1, 3)],
                    g.ring(P0[0], P0[1], RR, RT), 1.0, '8B', 0.7, finish=False)
g.shade(g.poly(SADDLE) * g.linear((0, 384), (0, 416)), 0.9, angle=8, grade='8B', width=6, pressure=0.5, finish=False)
g.strokes([GRIP[0]], '8B', 0.95, width=11, taper=(0.02, 0.02), wobble=0.2)
for name in ('main', 'seat', 'fork', 'head'):
    P, w = FRAME_TUBES[name]; s = tube_edges[name][2]
    g.strokes([offset(P, s * w * 0.36)], '6B', 0.7, width=2.6, taper=(0.04, 0.08), wobble=0.15, smooth=False)
# the corner: the shaded side wall darkest right at the edge (value contrast against the lit front)
edge_dark = g.poly([top_c, toward_vp(top_c, 0.06), toward_vp(base_c, 0.06), base_c]) * open_ * (1 - sign_m)
g.hatch(edge_dark, 0.85, angle=80, grade='4B', spacing=3.4, length=(60, 120), layers=(0, 0, 30))
g.stage('darks')
del contact, edge_dark
tick('darks')

# ===================================================================== 6. blend with the stump
g.smudge(side_wall * open_ * side_far, 0.7, radius=3.5, direction=86, length=10)
g.smudge(plaster * open_ * (1 - patch) * (cast_wall < 0.05), 0.85, radius=6, direction=10, length=16)
g.smudge(cast_wall, 0.3, radius=1.5)
for name, (P, w) in TUBES.items():
    g.smudge(g.band(P, w * 0.9), 0.6, radius=1.2, finish=False)
g.smudge(cast_ground, 0.7, radius=4, direction=0, length=14)
g.smudge(sidewalk * open_, 0.6, radius=5, direction=0, length=20)
for P0 in (RH, FH):
    g.smudge(g.ring(P0[0], P0[1], RR + 1, RT - 1, feather=1.5), 0.5, radius=2, finish=False)
g.smudge(door_m, 0.45, radius=3, direction=90, length=14)
for (x0, y0, x1, y1) in PANELS:
    g.erase([(x0 + 3, y1 + 3), (x1 + 3, y1 + 3), (x1 + 3, y0 + 3)], 1.8, 0.6)
g.stage('blend')
del side_tone, dampband, cast_ground, sidewalk, door_m, side_wall, side_far, plaster, recess
tick('blend')

# ===================================================================== 7. erasers: pull out the light
for P0 in (RH, FH):
    g.erase(g.circle_pts(P0[0], P0[1], RT - 4.5, RT - 4.5, 196, 262), 2.4, 0.75, soft=0.7)       # tyre glint
    g.erase(g.circle_pts(P0[0], P0[1], RR - 4, RR - 4, 180, 300), 2.0, 0.8, soft=0.5)           # rim chrome
    g.erase(g.circle_pts(P0[0], P0[1], RR - 4, RR - 4, 20, 60), 1.6, 0.6, soft=0.5)
for P0, a0, a1 in FENDERS:
    g.erase(g.circle_pts(P0[0], P0[1], 186, 186, max(a0, 200), min(a1, 285)), 2.4, 0.85, soft=0.6)
for name, (P, w) in TUBES.items():
    lit_e, dark_e, s = tube_edges[name]
    if w >= 8: g.erase(offset(P, -s * w * 0.2), max(1.6, w * 0.14), 0.85, soft=0.5)
g.lift(g.ellipse(560, 600, 150, 70, rot=-30, feather=40) * front_wall * open_, 0.3)               # light on the wall
g.erase([(CX - 2, 60), (CX - 2, 780)], 1.8, 0.7)                                                # lit edge of the corner
for (a0, a1, w_) in [((0.12, 470), (0.2, 380), 5), ((0.16, 600), (0.27, 450), 3), ((0.21, 650), (0.28, 560), 2)]:  # glints on the shop glass
    g.erase([toward_vp((CX, a0[1]), a0[0]), toward_vp((CX, a1[1]), a1[0])], w_, 0.7, soft=1.0)
lip = blur(shift(patch, -5, -6) * (1 - patch), 1.0)                                              # the broken plaster's lit edge
g.lift(lip * g.linear((560, 180), (700, 330)), 0.8)
for (x0, y) in QUOINS:                                                                           # quoin tops catch light
    g.erase([(x0 + 3, y + 3), (CX - 4, y + 3)], 1.4, 0.5)
g.stage('lift')
del patch, front_wall, cast_wall, lip
tick('lift')

# ===================================================================== 8. details
spk_clip = 1 - np.clip(sum(g.band(TUBES[n][0], TUBES[n][1]) for n in ('chainstay', 'seatstay', 'fork', 'rackstrut1', 'rackstrut2')) + g.ellipse(BB[0], BB[1], 48, 48), 0, 1)
g.strokes(spokes_lines, 'HB', 0.75, width=1.2, taper=(0.02, 0.05), wobble=0.08, clip=spk_clip, smooth=False)
del spk_clip
for P0 in (RH, FH):
    hub = g.ellipse(P0[0], P0[1], 18, 18)
    g.hatch(hub, 0.6 * g.linear((P0[0] - 15, P0[1] - 15), (P0[0] + 15, P0[1] + 15)) + 0.2, 60, '2B', 3, (10, 20), finish=False)
    L(g.circle_pts(P0[0], P0[1], 18, 18), '2B', 0.7, closed=True)
    L(g.circle_pts(P0[0], P0[1], 6, 6), '4B', 0.8, closed=True)
    ticks = []
    for i in range(0, 360, 6):
        a = np.deg2rad(i); u = np.array([np.cos(a), np.sin(a)])
        ticks.append([P0 + (RT - 1) * u, P0 + (RT - 5) * u])
    g.strokes(ticks, '6B', 0.5, width=1.4, taper=(0, 0), wobble=0, smooth=False)
# chainring with teeth and spider; chain; cranks; pedal
g.hatch(g.ring(BB[0], BB[1], 30, 46), 0.55, 40, '2B', 3.2, (14, 26), (0, 0, 70), finish=False)
teeth = []
for i in range(44):
    a = np.deg2rad(i * 360 / 44)
    teeth.append([BB + 45 * np.array([np.cos(a), np.sin(a)]), BB + 49 * np.array([np.cos(a + 0.05), np.sin(a + 0.05)])])
g.strokes(teeth, '4B', 0.6, width=2, taper=(0, 0), wobble=0, smooth=False)
for i in range(5):
    a = np.deg2rad(18 + i * 72)
    L([BB + 8 * np.array([np.cos(a), np.sin(a)]), BB + 32 * np.array([np.cos(a), np.sin(a)])], '2B', 0.6, smooth=False)
L(g.circle_pts(BB[0], BB[1], 30, 30), 'HB', 0.55, closed=True)
L(g.circle_pts(BB[0], BB[1], 9, 9), '4B', 0.7, closed=True)
for (pa, pb) in [((BB[0], BB[1] - 47), (RH[0], RH[1] - 18)), ((BB[0], BB[1] + 47), (RH[0], RH[1] + 18))]:
    pa, pb = np.array(pa), np.array(pb); n = int(np.linalg.norm(pb - pa) / 7)
    links = [[pa + (pb - pa) * (k / n), pa + (pb - pa) * ((k + 0.65) / n)] for k in range(n)]
    g.strokes(links, '4B', 0.75, width=3.2, taper=(0.1, 0.1), wobble=0.1, smooth=False)
L(g.circle_pts(RH[0], RH[1], 18, 18), '2B', 0.7, closed=True)
g.strokes([[(703, 626), (BB[0] - 4, BB[1] - 6)]], 'HB', 0.45, width=8, taper=(0.1, 0.1))                          # far crank, faint
g.hatch(g.rect(768, 768, 814, 782), 0.8, 0, '4B', 2.6, (20, 40), finish=False)
# saddle springs and rails
for x0 in (628, 652):
    coil = [(x0 + 6 * np.cos(t * 10 * np.pi), 418 + t * 26 + 2.5 * np.sin(t * 10 * np.pi)) for t in np.linspace(0, 1, 60)]
    g.strokes([coil], '4B', 0.75, width=2.2, smooth=False, taper=(0.02, 0.02), wobble=0.1)
L([(626, 444), (700, 420), (726, 410)], '2B', 0.6)
# basket: wicker stakes and weavers going over and under
bk = g.poly(BASKET)
g.shade(bk, 0.32, 0, '2B', 8, pressure=0.24, finish=False)
stakes = []
for k in range(15):
    t = k / 14
    stakes.append([np.array(BASKET[0]) + (np.array(BASKET[1]) - BASKET[0]) * t, np.array(BASKET[3]) + (np.array(BASKET[2]) - BASKET[3]) * t])
g.strokes(stakes, '2B', 0.6, width=1.8, taper=(0.04, 0.04), wobble=0.2, smooth=False)
weav = []
for j, y in enumerate(np.arange(410, 505, 8.5)):
    xs = np.linspace(1020 + (y - 398) * 0.13, 1190 - (y - 398) * 0.09, 15)
    for i in range(len(xs) - 1):
        up = (i + j) % 2
        weav.append([(xs[i], y), ((xs[i] + xs[i + 1]) / 2, y + (-2.5 if up else 2.5)), (xs[i + 1], y)])
g.strokes(weav, '2B', 0.6, width=2.0, taper=(0.15, 0.15), wobble=0.2)
g.hatch(bk * g.linear((1100, 400), (1185, 500)), 0.7, 70, '4B', 3.4, (16, 30), (0, 30), finish=False)
g.strokes([offset([BASKET[0], BASKET[1]], 3)], '4B', 0.8, width=6, taper=(0.05, 0.05))                         # rolled rim
del bk
# baguette: crust tone built in two passes along the loaf, darker underside, ends browner, pale scoring slashes
bm = g.band(BAGUETTE, 34)
crust = 0.38 + 0.5 * g.linear(offset(BAGUETTE, -17)[0], offset(BAGUETTE, 17)[0])
g.shade(bm, crust * 0.8, angle=-27, grade='2B', width=6, pressure=0.32, finish=False)
for f0 in (0.0, 1.3):
    g.contour_hatch([offset(BAGUETTE, f) for f in np.arange(-15.5 + f0, 16, 2.6)], bm, crust, '2B', 0.85, finish=False, taper=(0.05, 0.08))
g.smudge(bm, 0.5, 1.5, finish=False)
for k in range(5):
    t = 0.2 + k * 0.155
    c = np.array(BAGUETTE[0]) + (np.array(BAGUETTE[1]) - BAGUETTE[0]) * t
    g.lift(g.ellipse(c[0] - 2, c[1] - 1, 19, 5, rot=-62, feather=1.5), 0.8)
    L(g.circle_pts(c[0], c[1], 20, 5.5, 20, 160, rot=-62), '4B', 0.75)
L(offset(BAGUETTE, 16.5), '4B', 0.7, smooth=False)
del bm, crust
# flowers: paper cone with folds, three tulips, stems and leaves
g.hatch(g.poly(CONE), 0.3 * g.linear((1090, 400), (1160, 470)) + 0.05, 64, 'HB', 4, (20, 40), (0,), finish=False)
L([(1108, 394), (1124, 472)], 'H', 0.55); L([(1142, 390), (1128, 470)], 'H', 0.5)
for (fx, fy, rot) in FLOWERS:
    a = np.deg2rad(rot); up = np.array([np.sin(a), -np.cos(a)]); rt = np.array([np.cos(a), np.sin(a)])
    c = np.array([fx, fy])
    L([c - up * 20, c - up * 30 + rt * (1126 - fx) * 0.2, np.array([fx + (1126 - fx) * 0.6, 392])], '2B', 0.6)
    head = g.ellipse(fx, fy, 16, 22, rot)
    g.hatch(head, 0.3 + 0.45 * g.linear(c - rt * 14 - up * 10, c + rt * 14 + up * 10), 70 + rot, '2B', 3.0, (12, 24), (0, 0, 60), finish=False)
    petal = [c - rt * 16 - up * 2, c - rt * 11 + up * 22, c - rt * 4 + up * 12, c + up * 24, c + rt * 4 + up * 12, c + rt * 11 + up * 22, c + rt * 16 - up * 2]
    L(petal, '2B', 0.7)
    L([c - rt * 16 - up * 2, c - up * 16 - rt * 8, c - up * 22, c - up * 16 + rt * 8, c + rt * 16 - up * 2], '2B', 0.7)
    L([c - rt * 4 + up * 12, c - rt * 2 - up * 10], 'HB', 0.5)
for lf in ([(1102, 396), (1070, 344), (1080, 296)], [(1150, 392), (1190, 338), (1184, 296)]):
    L(lf, 'HB', 0.6)
    L([lf[0], ((lf[1][0] + lf[2][0]) / 2 + 10 * np.sign(lf[1][0] - 1126), lf[1][1] + 6), lf[2]], 'HB', 0.5)
# bell
g.hatch(g.ellipse(962, 380, 11, 8), 0.5, 50, '2B', 3, (10, 18), finish=False)
L(g.circle_pts(962, 380, 11, 8, 180, 360), '2B', 0.7)
L([(951, 381), (973, 381)], '2B', 0.7, smooth=False)
# sign, plate and house-number lettering
g.hatch(g.ellipse(*SIGN) * (1 - g.ellipse(1372, 238, 40, 17, -8)), 0.28, 60, 'HB', 3.6, (20, 40), (0, 0), finish=False)
g.hatch(g.ellipse(1372, 238, 40, 17, -8), 0.5 + 0.35 * g.linear((1372, 222), (1372, 256)), 0, '2B', 3.0, (20, 40), finish=False)
for k in range(3):
    cxk = 1352 + k * 20
    g.erase([(cxk - 7, 241), (cxk + 7, 232)], 2.6, 0.8)
g.hatch(g.rect(PLATE[0] + 4, PLATE[3] + 1, PLATE[2] + 6, PLATE[3] + 7), 0.7, 0, '2B', 2.8, (30, 60))
L([(PLATE[0] + 6, PLATE[1] + 6), (PLATE[2] - 6, PLATE[1] + 6), (PLATE[2] - 6, PLATE[3] - 6), (PLATE[0] + 6, PLATE[3] - 6)], 'H', 0.5, smooth=False, closed=True)
g.write('VIA DEL MULINO', (PLATE[0] + PLATE[2]) / 2, (PLATE[1] + PLATE[3]) / 2 + 1, 17, '2B', 0.75, font='serif', anchor='mm')
L(g.circle_pts(312, 488, 16, 20), 'HB', 0.6, closed=True)
g.write('7', 312, 489, 24, '2B', 0.8, font='serif', anchor='mm')
L(g.circle_pts(172, 500, 7, 7), '2B', 0.75, closed=True)                                                # door knob
# cobbles: irregular rows of rounded stones, a tone on each, dark joints, lit tops
cob = np.zeros((H, W), np.float32)
outlines = []
for row, y in enumerate([896, 924, 956, 994, 1038]):
    hgt = 25 + row * 8; x = -30 - rng.uniform(0, 40)
    while x < W + 20:
        wdt = hgt * rng.uniform(1.25, 2.0)
        cx_, cy_ = x + wdt / 2, y + hgt / 2 + rng.normal(0, 2)
        tt = np.linspace(0, 2 * np.pi, 10)[:-1]
        sq = np.sign(np.cos(tt)) * np.abs(np.cos(tt)) ** 0.7, np.sign(np.sin(tt)) * np.abs(np.sin(tt)) ** 0.7   # squarish
        q = np.stack([cx_ + wdt * 0.47 * sq[0] * (1 + 0.07 * rng.normal(size=9)), cy_ + hgt * 0.44 * sq[1] * (1 + 0.07 * rng.normal(size=9))], 1)
        pts = spline(np.vstack([q, q[:1]]), 6)
        if not ((cx_ < 700 or cx_ > 1450) and cy_ > 965):           # keep the margin clear for notes and swatches
            outlines.append(pts)
        x += wdt + rng.uniform(3, 11)
im = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(im)
for pts in outlines: dr.polygon([tuple(map(float, p)) for p in pts], fill=255)
cob = blur(np.asarray(im, np.float32) / 255, 0.8)
del im, dr
street = g.rect(-5, CURB + 18, W + 5, H + 5) * (1 - g.rect(-5, 968, 720, H + 5, 18)) * (1 - g.rect(1450, 968, W + 5, H + 5, 18))
low_r = blur(shift(1 - cob, -9, -7), 4) * cob                     # the lower right of each stone turns from the light
g.shade(cob * street, 0.22 + 0.5 * low_r, angle=-15, grade='2B', width=8, pressure=0.26)
g.hatch(cob * street, 0.15 + 0.55 * low_r, -25, 'HB', 3.8, (14, 26), (0, 0, 60))
g.hatch((1 - cob) * street, 0.62, 40, '2B', 3.4, (12, 24), (0, 0, -50))
for pts in outlines:
    L(pts, 'HB', 0.5, lost=0.25, fade=0.12)
g.lift(blur(shift(cob, 4, 4) * (1 - shift(cob, 7, 7)) * cob, 1.5) * street, 0.5)   # top-left rims catch the light
del cob, low_r
# a sparrow on the sidewalk has found the crumbs that fell from the baguette
SP, K = np.array([1302.0, 838.0]), 1.4
sp = lambda dx, dy: SP + K * np.array([dx, dy], np.float32)
body = g.ellipse(*sp(0, 0), 24 * K, 14 * K, rot=-12)
head = g.ellipse(*sp(-22, -12), 10 * K, 9 * K)
tail = g.poly([sp(18, -6), sp(44, -16), sp(46, -8), sp(20, 6)])
bird = np.clip(body + head + tail, 0, 1)
g.hatch(bird, 0.35 + 0.45 * g.linear(sp(-10, -14), sp(10, 14)), 30, '2B', 3.0, (10, 20), (0, 0, 70), finish=False)
del bird, body, head, tail
g.hatch(g.ellipse(*sp(4, -3), 15 * K, 8 * K, rot=-18), 0.85, -20, '4B', 2.8, (8, 14), (0, 0), finish=False)   # wing
g.strokes([[sp(-4 + 5 * k, -8), sp(10 + 5 * k, -2)] for k in range(4)], '6B', 0.7, width=1.6)                # wing bars
g.lift(g.ellipse(*sp(-8, 7), 13 * K, 5 * K, rot=-10, feather=3), 0.6)                                        # pale breast
g.hatch(g.ellipse(*sp(-22, -16), 8 * K, 5 * K), 0.8, 10, '4B', 2.6, (6, 12), (0, 0), finish=False)          # dark cap
L(np.vstack([g.circle_pts(*sp(-22, -12), 10 * K, 9 * K, 150, 330), [sp(8, -14)], [sp(44, -16)], [sp(46, -8)],
             [sp(20, 8)], [sp(-6, 12)], [sp(-24, -4)]]), '2B', 0.75)
L([sp(-31, -14), sp(-40, -11), sp(-31, -8)], '4B', 0.85, smooth=False)                                      # beak
g.strokes([[sp(-24, -14)]], '8B', 1.0, width=4.0)                                                             # eye
for dx in (-4, 6):
    L([sp(dx, 12), sp(dx - 3, 24), sp(dx - 9, 26)], '4B', 0.75, smooth=False)
g.shade(g.ellipse(*sp(4, 27), 30 * K, 4 * K, feather=3) * open_, 0.6, 0, '4B', 5, pressure=0.35, finish=False)
for (cx_, cy_, r_) in [(1240, 866, 3.2), (1229, 860, 2.4), (1254, 872, 2.8), (1217, 868, 2)]:
    L(g.circle_pts(cx_, cy_, r_ * 1.3, r_), 'HB', 0.65, closed=True)
g.stage('details')
tick('details')

# ===================================================================== 9. margins
g.write('Via del Mulino, 8:10 - the bread run', 64, 990, 30, 'HB', 0.75)
g.write('2 . X', 66, 1034, 26, 'HB', 0.65)
g.value_scale(1478, 980, w=56, h=34, gap=8, label_size=22)
g.fingerprint(1852, 64, 25, rot=-30, amount=0.3)                        # where the sheet was held
g.smear([(1400, 1070), (1700, 1052), (1900, 1062)], 70, 0.05)
tick('margins')

g.save(out, stages_dir=stages)
tick('saved')
print('saved', out)
