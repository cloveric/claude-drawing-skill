"""Example (overlay sheets): Larkhaven on Foot / 海港步行图 — a coastal town plan built as separations on a light
box. The base sheet hangs on a peg bar: the town in black linework with grey flat tones (blocks cut out by
recursive street splits, buildings round each block with party walls, landmarks in a darker tone, the coast,
breakwaters, a railway, contours on Castle Hill and the headland). Three translucent sheets, one ink each, come
down on their registration crosses: blue (the sea water-lined round the coast, the river, the harbour, the ferry
across the bay and tram line 2), yellow (the parks, the market squares, the beach) and magenta (a walking route
with six numbered stops that takes the ferry to the lighthouse). The inks multiply where they cross: the pond in
the botanic garden turns green, the route goes red across the parks and violet across the water. A legend card on
clear film sits beside the map. No image model.
python3 overlay_city_map.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from overlay import Overlay
from core import spline, blur, blob_pts

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'overlay_city_map.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
T0 = time.time()
tick = lambda name: print(f'{name:16s} {time.time() - T0:5.1f}s') if os.environ.get('OVERLAY_TIMING') else None

W, H = 1920, 1080
o = Overlay(W, H, seed=11, keep_stages=bool(stages))
rng = np.random.default_rng(5)
o.desk()
o.lightbox(34, 24, 1886, 1056)

# ===================================================================== layout
SX0, SY0, SW, SH = 86, 86, 1180, 905                  # base sheet (laid down)
FX0, FY0, FX1, FY1 = 136, 140, 1216, 922              # map frame
PEG_Y = 98
PEGS = [('round', 476, PEG_Y, 8), ('slot', 676, PEG_Y, 60, 14), ('round', 876, PEG_Y, 8)]
CROSS = dict(L1=(111, 250), L2=(111, 800), R1=(1241, 250), R2=(1241, 800), B1=(330, 958), B2=(1020, 958))
o.peg_bar(436, 916, 56, 86, PEGS)
frame = o.rrect(FX0, FY0, FX1, FY1)


def S(pts, per=10):
    return spline(np.asarray(pts, np.float32), per)


def tube(pts, w0, w1, per=12):
    """a mask of varying width along a spline (the river)"""
    P = S(pts, per)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1], 1.5)
    x, y = np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])
    r = (w0 + (w1 - w0) * t / s[-1]) / 2
    m = np.zeros((H, W), np.float32)
    for xi, yi, ri in zip(x, y, r):
        x0, x1, y0, y1 = int(xi - ri - 2), int(xi + ri + 3), int(yi - ri - 2), int(yi + ri + 3)
        Y, X = np.mgrid[y0:y1, x0:x1]
        np.maximum(m[y0:y1, x0:x1], np.clip(ri - np.hypot(X - xi, Y - yi) + 0.5, 0, 1), out=m[y0:y1, x0:x1])
    return m, P


# ===================================================================== geography
COAST = [(FX0 - 4, 762), (190, 774), (262, 790), (330, 786), (392, 764), (436, 740), (468, 706), (482, 660), (500, 634),
         (548, 626), (612, 624), (668, 630), (704, 648), (716, 690), (742, 736), (800, 752), (880, 744), (948, 724),
         (996, 706), (1008, 752), (1026, 816), (1056, 862), (1094, 864), (1118, 826), (1128, 760), (1152, 708),
         (1186, 680), (FX1 + 4, 668)]
coast = S(COAST, 8)
land = o.poly(np.vstack([[(FX0 - 4, FY0 - 4), (FX1 + 4, FY0 - 4)], coast[::-1]]))
breakw = np.maximum(o.band(S([(450, 724), (480, 768), (528, 798), (588, 810)]), 13),
                    o.band(S([(744, 738), (724, 782), (686, 806), (640, 812)]), 13))
jetty = o.band([(1006, 792), (968, 812)], 9)
land = np.maximum(land, np.maximum(breakw, jetty)) * frame
river, RIV = tube([(566, FY0 - 6), (586, 206), (566, 264), (534, 322), (526, 382), (552, 442), (594, 500), (590, 560),
                   (562, 604), (552, 640)], 15, 30)
river *= frame
land = np.clip(land - river, 0, 1)
sea = np.clip(frame - land - river, 0, 1)
water = np.clip(sea + river, 0, 1)
tick('geography')

# ---- main roads (white bands carved out of the blocks), parks and squares
ROADS = dict(
    station_rd=([(772, 214), (770, 300), (766, 380), (762, 428), (742, 500), (712, 566), (700, 612)], 16),
    high_st=([(526, 384), (612, 394), (700, 412), (770, 428), (858, 414), (960, 394), (1060, 386), (FX1 + 6, 378)], 16),
    west_rd=([(526, 384), (468, 404), (410, 448), (330, 494), (240, 516), (FX0 - 6, 528)], 15),
    mill_rd=([(FX0 - 6, 262), (260, 266), (400, 252), (520, 236), (586, 232), (680, 236), (770, 236)], 14),
    quay_rd=([(478, 612), (560, 610), (640, 612), (716, 618)], 14),
    west_quay=([(478, 612), (470, 650), (458, 690), (446, 724)], 11),
    east_quay=([(716, 618), (722, 668), (738, 714), (750, 734)], 11),
    promenade=([(748, 728), (820, 730), (900, 716), (960, 700), (1000, 688), (1040, 640), (1092, 560), (1150, 512), (FX1 + 6, 486)], 14),
    north_rd=([(860, 414), (880, 330), (930, 250), (1000, 196), (1060, FY0 - 6)], 13),
    east_rd=([(1060, 386), (1080, 470), (1100, 552)], 12),
    castle_rd=([(410, 448), (430, 360), (470, 300), (520, 236)], 11),
    lane_lh=([(1004, 694), (1022, 760), (1046, 820), (1060, 848)], 8),
)
road = np.zeros((H, W), np.float32)
for pts, w in ROADS.values():
    road = np.maximum(road, o.band(S(pts), w))
RAIL = S([(836, 186), (930, 176), (1040, 164), (1140, 152), (FX1 + 6, 146)])
rail = o.band(RAIL, 13)
CASTLE_HILL = blob_pts(300, 392, 116, 84, rough=0.07, seed=3)
park_castle = o.poly(CASTLE_HILL, smooth=True)
park_botanic = o.poly([(170, 160), (420, 158), (436, 186), (430, 236), (300, 244), (172, 240)], smooth=True)
park_river = o.poly([(604, 452), (628, 470), (636, 520), (622, 556), (600, 548), (604, 506), (588, 470)], smooth=True)
park_head = o.poly([(1006, 712), (1046, 700), (1104, 694), (1124, 760), (1100, 840), (1062, 850), (1030, 800)], smooth=True) * land
sq_market = o.poly([(732, 446), (812, 440), (820, 498), (740, 508)])
sq_church = o.poly([(880, 432), (928, 428), (934, 470), (884, 474)])
beach = np.clip(o.offset(sea, 20) - sea, 0, 1) * land * (o.poly([(744, 700), (1000, 680), (1000, 800), (744, 800)]))
open_space = np.clip(park_castle + park_botanic + park_river + park_head + sq_market + sq_church + beach, 0, 1)
tick('roads/parks')

# ---- blocks: recursive street splits inside each district
def subdivide(m, oy, ox, gaps, max_area, jitter, depth, blocks, splits):
    area = float(m.sum())
    if area < 160: return
    ys, xs = np.nonzero(m > 0.5)
    if len(xs) < 20: return
    cx, cy = xs.mean(), ys.mean()
    ev, V = np.linalg.eigh(np.cov(np.stack([xs, ys])))
    if 3.46 * np.sqrt(max(ev[0], 0)) < 12: return                # a sliver between a street and a park: leave it open
    if area < max_area * rng.uniform(0.6, 1.4) or depth > 10:
        blocks.append((m, oy, ox)); return
    ax = V[:, 1]
    a = np.arctan2(ax[1], ax[0]) + rng.normal(0, jitter)
    ax = np.array([np.cos(a), np.sin(a)])
    proj = (xs - cx) * ax[0] + (ys - cy) * ax[1]
    t = np.quantile(proj, rng.uniform(0.38, 0.62))
    px, py = cx + ax[0] * t, cy + ax[1] * t
    Y, X = np.mgrid[0:m.shape[0], 0:m.shape[1]].astype(np.float32)
    sd = (X - px) * ax[0] + (Y - py) * ax[1]
    g = gaps[min(depth, len(gaps) - 1)]
    splits.append((ox + px, oy + py, -ax[1], ax[0], g, m.shape, oy, ox))
    for part in (m * np.clip(sd - g / 2 + 0.5, 0, 1), m * np.clip(-sd - g / 2 + 0.5, 0, 1)):
        yy, xx = np.nonzero(part > 0.02)
        if not len(xx): continue
        y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
        subdivide(part[y0:y1, x0:x1], oy + y0, ox + x0, gaps, max_area, jitter, depth + 1, blocks, splits)


buildable = land * (1 - np.clip(road + rail + open_space + o.offset(river, 7) - river, 0, 1))
buildable = np.clip(buildable - np.clip(o.offset(water, 9) - water, 0, 1), 0, 1)          # a quay / embankment strip along the water
DISTRICTS = [   # polygon, street gaps by depth, max block area, angle jitter
    ([(586, 236), (770, 236), (860, 414), (1060, 386), (1100, 552), (1000, 688), (716, 618), (560, 610), (600, 500), (560, 400)], (11, 9, 7, 6), 3600, 0.20),
    ([(FX0, 262), (526, 236), (526, 384), (468, 404), (330, 494), (FX0, 528)], (10, 8, 6), 4200, 0.12),
    ([(FX0, 528), (330, 494), (468, 404), (526, 384), (560, 400), (560, 610), (446, 724), (FX0, 770)], (10, 8, 7, 6), 3600, 0.18),
    ([(586, 236), (770, 236), (770, FY0), (586, FY0)], (10, 8), 5200, 0.1),
    ([(770, 236), (860, 414), (1060, 386), (FX1, 378), (FX1, FY0), (770, FY0)], (11, 9, 7), 5600, 0.10),
    ([(1100, 552), (1060, 386), (FX1, 378), (FX1, 486), (1150, 512)], (9, 7), 4200, 0.12),
    ([(1040, 640), (1092, 560), (1150, 512), (FX1, 486), (FX1, 668), (1152, 708), (1128, 712), (1104, 690), (1050, 700)], (9, 7), 3000, 0.15),
]
blocks, splits = [], []
for poly, gaps, amax, jit in DISTRICTS:
    dm = buildable * o.poly(poly)
    yy, xx = np.nonzero(dm > 0.02)
    if not len(xx): continue
    y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    subdivide(dm[y0:y1, x0:x1], y0, x0, gaps, amax, jit, 0, blocks, splits)
B = np.zeros((H, W), np.float32)
for m, oy, ox in blocks:
    np.maximum(B[oy:oy + m.shape[0], ox:ox + m.shape[1]], m, out=B[oy:oy + m.shape[0], ox:ox + m.shape[1]])
inner = o.offset(B, -13)
band_b = np.clip(B - inner, 0, 1)
tick('blocks')

# party walls: short ticks across the building band, square to every street edge
ticks = []
for (x, y, dx, dy, g, shp, oy, ox) in splits:
    nx, ny = dy, -dx
    L = np.hypot(*shp) / 2 + 4
    s = -L
    while s < L:
        s += rng.uniform(10, 22)
        bx, by = x + dx * s, y + dy * s
        for sg in (1, -1):
            a = (bx + nx * sg * (g / 2 - 1), by + ny * sg * (g / 2 - 1))
            b = (bx + nx * sg * (g / 2 + 15), by + ny * sg * (g / 2 + 15))
            ticks.append([a, b])
for pts, w in list(ROADS.values()):
    P = S(pts)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cs = np.concatenate([[0], np.cumsum(seg)])
    s = 0.0
    while s < cs[-1]:
        s += rng.uniform(10, 22)
        i = min(np.searchsorted(cs, s), len(P) - 1)
        d = P[i] - P[max(i - 1, 0)]; d = d / (np.linalg.norm(d) + 1e-6); n = np.array([-d[1], d[0]])
        bx, by = np.interp(s, cs, P[:, 0]), np.interp(s, cs, P[:, 1])
        for sg in (1, -1):
            ticks.append([(bx + n[0] * sg * (w / 2 - 1), by + n[1] * sg * (w / 2 - 1)), (bx + n[0] * sg * (w / 2 + 15), by + n[1] * sg * (w / 2 + 15))])
tick('party walls')

# landmarks (darker tone)
LANDMARKS = dict(
    station=[(728, 160), (842, 160), (842, 204), (728, 204)],
    market_hall=[(762, 464), (792, 462), (794, 490), (764, 492)],
    church=[(892, 476), (930, 472), (931, 486), (950, 485), (951, 498), (932, 499), (934, 520), (897, 523), (895, 502), (878, 503), (877, 490), (894, 489)],
    fish_market=[(480, 650), (498, 650), (494, 716), (472, 714)],
    customs=[(626, 590), (676, 590), (676, 604), (626, 604)],
)
castle = blob_pts(300, 384, 30, 24, rough=0.02, n=10, seed=1)
castle = np.array([(300 + (x - 300) * (1.0 if i % 2 == 0 else 0.62), 384 + (y - 384) * (1.0 if i % 2 == 0 else 0.62)) for i, (x, y) in enumerate(castle)])
LANDMARKS['castle'] = castle.tolist()

# ===================================================================== the base sheet (K): black linework, grey tones
base = o.sheet(SX0, SY0, SW, SH, 'base', ink='black')
base.punch(476, PEG_Y, 10.5); base.punch_slot(676, PEG_Y, 70, 20); base.punch(876, PEG_Y, 10.5)
base.fill(band_b, 0.20)
base.fill(inner * B, 0.06)
base.lines(ticks, 0.8, 0.5)
base.knock(np.clip(1 - band_b * 1.2, 0, 1) * (1 - B))       # ticks only inside the building band
base.fill(o.edge(B, 1.1), 1.0)
base.fill(o.edge(inner * B, 0.7) * B, 0.45)
for k, pts in LANDMARKS.items():
    m = o.poly(pts)
    base.fill(m, 0.62); base.fill(o.edge(m, 1.2), 1.0)
# coast, quays, breakwaters, river banks stay white: their lines are on the blue sheet; the land edge is printed here
base.fill(o.edge(np.clip(land + river, 0, 1), 1.8), 1.0)
for pm in (park_castle, park_botanic, park_river, sq_market, sq_church):
    base.fill(o.edge(pm, 1.0), 0.8)
# parks: tree symbols and paths
for pm, n, seed in ((park_castle, 34, 1), (park_botanic, 26, 2), (park_head, 16, 3), (park_river, 6, 4)):
    ys, xs = np.nonzero(o.offset(pm, -9) > 0.9)
    if not len(xs): continue
    r2 = np.random.default_rng(seed)
    pick = r2.choice(len(xs), size=min(n, len(xs)), replace=False)
    for i in pick:
        rr = r2.uniform(4, 6.5)
        base.line(o.circle_pts(xs[i], ys[i], rr), 1.0, 0.75, closed=True)
base.line(S([(196, 236), (240, 206), (300, 214), (360, 186), (414, 200)]), 1.2, 0.8, dash=(5, 4))
base.line(S([(214, 448), (260, 430), (300, 412)]), 1.2, 0.8, dash=(5, 4))
base.line(S([(392, 446), (350, 420), (318, 406)]), 1.2, 0.8, dash=(5, 4))
# contours: Castle Hill and the headland
for k, f in enumerate([1.05, 0.86, 0.68, 0.5]):
    base.line(blob_pts(298, 390, 116 * f, 84 * f, rough=0.06, seed=10 + k), 0.9, 0.42, closed=True, smooth=False)
for k, f in enumerate([0.9, 0.62, 0.36]):
    base.line(blob_pts(1074, 778, 54 * f, 70 * f, rough=0.08, seed=20 + k, rot=0.3), 0.9, 0.42, closed=True)
base.text('38', 334, 432, 13, 'map_italic', 0.8)
base.text('21', 1092, 742, 13, 'map_italic', 0.8)
# railway: line with cross ticks; platforms
base.line(RAIL, 3.0, 1.0)
P = RAIL; seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cs = np.concatenate([[0], np.cumsum(seg)])
rt = []
for s in np.arange(6, cs[-1], 12):
    x, y = np.interp(s, cs, P[:, 0]), np.interp(s, cs, P[:, 1])
    i = min(np.searchsorted(cs, s), len(P) - 1); d = P[i] - P[i - 1]; d /= np.linalg.norm(d); n = (-d[1], d[0])
    rt.append([(x - n[0] * 5, y - n[1] * 5), (x + n[0] * 5, y + n[1] * 5)])
base.lines(rt, 1.2, 1.0)
base.lines([[(842, 172), (840, 172)], [(728, 212), (842, 212)]], 1.0, 0.8)
# bridges over the river: parapets
for (bx, by, ang, ln) in [(526, 384, 8, 30), (586, 233, -4, 28), (560, 611, 0, 36)]:
    a = np.deg2rad(ang); d = np.array([np.cos(a), np.sin(a)]); n = np.array([-d[1], d[0]])
    for sg in (1, -1):
        c = np.array([bx, by]) + n * sg * 8
        base.line([c - d * ln / 2, c + d * ln / 2], 1.6, 1.0)
# moored boats in the harbour
for (bx, by, a) in [(500, 690, 80), (504, 742, 76), (700, 680, 100), (698, 724, 104), (560, 660, 0), (604, 662, 0)]:
    base.line(o.circle_pts(0, 0, 9, 3.4) @ np.array([[np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))], [-np.sin(np.deg2rad(a)), np.cos(np.deg2rad(a))]]) + (bx, by), 1.0, 0.85, closed=True)
# lighthouse
base.circle(1062, 852, 6.5); base.line(o.circle_pts(1062, 852, 11), 1.1, 1.0, closed=True)
for a in range(0, 360, 45):
    t = np.deg2rad(a); base.line([(1062 + np.cos(t) * 14, 852 + np.sin(t) * 14), (1062 + np.cos(t) * 20, 852 + np.sin(t) * 20)], 1.0, 0.9)
# beach stipple
base.stipple(beach, 170, 0.8, 0.6, seed=4)
tick('base drawing')

# labels
LAB = dict(halo=3.5)
base.text('OLD TOWN', 880, 560, 21, 'map_bold', 0.62, spacing=7, **LAB)
base.text('WEST BANK', 250, 640, 21, 'map_bold', 0.62, spacing=7, **LAB)
base.text('NORTH QUARTER', 1010, 300, 19, 'map_bold', 0.62, spacing=6, **LAB)
base.text('Castle Hill', 300, 452, 16, 'map_italic', 0.95, **LAB)
base.text('Botanic Garden', 236, 186, 16, 'map_italic', 0.95, **LAB)
base.text('Station', 785, 150, 15, 'map_italic', 0.95, anchor='mb', **LAB)
base.text('Market', 776, 520, 14, 'map_italic', 0.95, **LAB)
base.text("St Bride's", 958, 530, 14, 'map_italic', 0.95, **LAB)
base.text('Fish Market', 454, 690, 13, 'map_italic', 0.95, rot=86, **LAB)
base.text('Lighthouse', 1062, 886, 14, 'map_italic', 0.95, **LAB)
base.text('HIGH STREET', 980, 391, 12, 'map', 0.95, spacing=2.5, rot=6, **LAB)
base.text('MILL ROAD', 330, 260, 12, 'map', 0.95, spacing=2.5, rot=2, **LAB)
base.text('WEST ROAD', 230, 517, 12, 'map', 0.95, spacing=2.5, rot=7, **LAB)
base.text('QUAY STREET', 600, 611, 11, 'map', 0.95, spacing=2.2, **LAB)
# frame, margins, plate marks
base.line([(FX0, FY0), (FX1, FY0), (FX1, FY1), (FX0, FY1)], 2.2, 1.0, closed=True, cap=False)
base.line([(FX0 - 7, FY0 - 7), (FX1 + 7, FY0 - 7), (FX1 + 7, FY1 + 7), (FX0 - 7, FY1 + 7)], 0.9, 1.0, closed=True, cap=False)
base.text('LARKHAVEN  ·  TOWN PLAN  ·  1 : 5 000', FX0 - 7, 118, 14, 'map_bold', 0.9, anchor='lm', spacing=2.6)
base.text('PLATE K  —  BASE', FX1 + 7, 118, 14, 'map_bold', 0.9, anchor='rm', spacing=2.6)
base.text('K', 352, 958, 15, 'map_bold', 0.9, anchor='lm')
for c in CROSS.values():
    base.cross(*c, size=17, r=9.5)
tick('base done')

# ===================================================================== blue sheet (C): water, ferry, tram -- on the pegs
blue = o.sheet(90, SY0, 1172, 890, 'tracing', ink='blue')
blue.punch(476, PEG_Y, 10.5); blue.punch_slot(676, PEG_Y, 70, 20); blue.punch(876, PEG_Y, 10.5)
near = np.clip(blur(1 - sea, 13) * 1.6, 0, 1) * sea
blue.fill(sea * (0.16 + 0.22 * near))
harbour = o.poly([(466, 616), (724, 616), (750, 742), (644, 818), (584, 816), (446, 728)])
for k, d in enumerate([5, 10, 16, 23, 31, 41]):
    keep = sea * frame * (1 - harbour * (k >= 2))
    blue.fill(o.contour(np.clip(1 - sea, 0, 1), d, 1.05 - 0.06 * k) * keep, 0.95 - 0.1 * k)
blue.fill(river, 0.40)
blue.fill(o.edge(river, 1.3) * frame * (1 - sea), 1.0)
for (bx, by, ang, ln) in [(526, 384, 8, 30), (586, 233, -4, 28), (560, 611, 0, 36)]:      # bridge decks cover the water
    a = np.deg2rad(ang); d = np.array([np.cos(a), np.sin(a)]); n = np.array([-d[1], d[0]])
    c = np.array([bx, by])
    blue.knock(o.poly([c - d * ln / 2 - n * 8, c + d * ln / 2 - n * 8, c + d * ln / 2 + n * 8, c - d * ln / 2 + n * 8]))
pond = o.ellipse(332, 204, 30, 12, rot=-6)
blue.fill(pond, 0.42); blue.fill(o.edge(pond, 1.2), 1.0)
# ferry across the bay, with the boat on its way
FERRY = S([(512, 700), (560, 760), (612, 806), (700, 846), (820, 862), (930, 840), (972, 812)])
blue.line(FERRY, 2.4, 1.0, dash=(11, 7))
fx, fy, fa = 790, 860, np.deg2rad(6)
hull = np.array([(-17, -5), (12, -5), (19, 0), (12, 5), (-17, 5)], np.float32)
R = np.array([[np.cos(fa), np.sin(fa)], [-np.sin(fa), np.cos(fa)]], np.float32)
blue.fill(hull @ R + (fx, fy), 1.0)
blue.fill(np.array([(-8, -3), (4, -3), (4, 3), (-8, 3)], np.float32) @ R + (fx, fy - 7), 1.0)
blue.text('FERRY  ·  EVERY 20 MIN', 846, 892, 13, 'map_bold', 1.0, spacing=2.4, rot=-2, halo=3)
# tram line 2
TRAM = S([(768, 222), (766, 300), (762, 380), (758, 428), (738, 500), (708, 566), (702, 604), (718, 640), (736, 700), (760, 728),
          (840, 728), (920, 711), (990, 690), (1036, 644), (1090, 562), (1150, 514), (FX1, 488)])
blue.line(TRAM, 4.2, 1.0)
for (sx, sy) in [(768, 226), (760, 424), (704, 600), (880, 720), (1064, 604)]:      # stops: station, market, harbour, beach, headland
    blue.circle(sx, sy, 8.5)
    blue.knock(o.circle(sx, sy, 4.6))
blue.text('TRAM 2', 1132, 506, 13, 'map_bold', 1.0, spacing=2.4, rot=39, halo=3)
# water names
blue.text('S A L T    S O U N D', 300, 868, 30, 'map_italic', 1.0, spacing=2, halo=5)
blue.text('THE HARBOUR', 604, 724, 14, 'map_bold', 1.0, spacing=3.2, halo=4)
blue.text('Lark River', 616, 296, 19, 'map_italic', 1.0, rot=-66, halo=3)
for c in CROSS.values():
    blue.cross(*c, size=17, r=9.5)
blue.text('C', 1042, 958, 15, 'map_bold', 1.0, anchor='lm')
tick('blue')

# ===================================================================== yellow sheet (Y): parks, squares, the beach
yel = o.sheet(96, 140, 914, 840, 'drafting', ink='yellow', curl=('br', 66))
yel.punch(108, 470, 7.5); yel.punch(108, 530, 7.5)
for pm in (park_castle, park_botanic, park_river):
    yel.fill(pm, 0.52)
    yel.fill(o.edge(pm, 2.6), 1.5)
for sq in (sq_market, sq_church):
    yel.fill(sq, 1.0)
    yel.fill(o.edge(sq, 2.0), 1.8)
yel.fill(beach, 0.42)
yel.stipple(beach, 110, 1.0, 1.6, seed=9)
for (sx, sy, r) in [(214, 372, 13), (402, 216, 11), (650, 522, 10)]:                     # the sunniest benches
    yel.circle(sx, sy, r * 0.45, cover=1.8)
    for a in range(0, 360, 45):
        t = np.deg2rad(a)
        yel.line([(sx + np.cos(t) * r * 0.7, sy + np.sin(t) * r * 0.7), (sx + np.cos(t) * r, sy + np.sin(t) * r)], 1.6, 1.8)
for c in ('L1', 'L2', 'B1'):
    yel.cross(*CROSS[c], size=17, r=9.5)
yel.text('Y', 111, 828, 15, 'map_bold', 1.6, anchor='mm')
tick('yellow')

# ===================================================================== magenta sheet (M): the walk, six stops
mag = o.sheet(200, 196, 1058, 784, 'tracing', ink='magenta', curl=('bl', 70))
mag.punch(1246, 480, 7.5); mag.punch(1246, 540, 7.5)
STOPS = [(806, 226), (808, 450), (526, 384), (352, 404), (486, 622), (1056, 812)]
WALK = [
    S([(792, 238), (778, 258), (776, 330), (771, 400), (772, 426), (790, 440)]),
    S([(792, 438), (770, 428), (700, 412), (612, 394), (542, 386)]),
    S([(510, 388), (468, 404), (430, 430), (394, 442), (370, 418)]),
    S([(348, 422), (338, 466), (334, 494), (380, 520), (420, 560), (450, 598), (470, 616)]),
]
for seg in WALK:
    mag.line(seg, 5.0, 1.0, dash=(15, 8))
    P = seg; cs = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    sm = cs[-1] * 0.55; i = np.searchsorted(cs, sm)
    mag.arrow((np.interp(sm, cs, P[:, 0]), np.interp(sm, cs, P[:, 1])), P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)], 15)
ferry_walk = FERRY
cs = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(ferry_walk, axis=0), axis=1))])
dots = [(np.interp(s, cs, ferry_walk[:, 0]), np.interp(s, cs, ferry_walk[:, 1])) for s in np.arange(10, cs[-1] - 6, 13)]
mag.dots(dots, 3.2)
mag.line(S([(486, 640), (496, 664), (510, 690)]), 5.0, 1.0, dash=(10, 7))
mag.line(S([(976, 808), (1006, 796), (1036, 806)]), 5.0, 1.0, dash=(15, 8))
for k, (sx, sy) in enumerate(STOPS):
    mag.circle(sx, sy, 16.5)
    mag.text(str(k + 1), sx, sy + 1, 21, 'map_bold', knock=True)
mag.text('start', 830, 226, 16, 'map_italic', 1.0, anchor='lm', halo=3)
mag.text('best view', 386, 380, 15, 'map_italic', 1.0, anchor='lm', halo=3)
mag.text('lunch', 462, 604, 15, 'map_italic', 1.0, anchor='rm', halo=3)
mag.text('take the ferry', 700, 826, 15, 'map_italic', 1.0, anchor='mm', rot=-10, halo=3)
mag.text('finish', 1080, 806, 16, 'map_italic', 1.0, anchor='lm', halo=3)
for c in ('R1', 'R2', 'B2', 'B1'):
    mag.cross(*CROSS[c], size=17, r=9.5)
mag.text('M', 1241, 828, 15, 'map_bold', 1.0, anchor='mm')
tick('magenta')

# ===================================================================== legend card on clear film
LX0, LY0, LX1, LY1 = 1312, 112, 1832, 952
film = o.sheet(LX0, LY0, LX1 - LX0, LY1 - LY0, 'film', ink='black', curl=('br', 60))
x = LX0 + 46
film.text('A HARBOUR WALK  ·  FOUR SHEETS', x, 168, 15, 'map_bold', 0.75, anchor='lm', spacing=3)
film.text('Larkhaven', x - 4, 236, 86, 'title', 1.0, anchor='lm')
film.text('海港小城 · 步行地图', x, 318, 40, 'cjk', 1.0, anchor='lm')
film.text('six stops, one ferry, about two hours', x, 366, 22, 'map_italic', 0.85, anchor='lm')
film.line([(x, 400), (LX1 - 46, 400)], 2.0, 1.0, cap=False)
rows = [('black', 0.9, 'Base', 'streets, blocks, coast', '底图'), ('blue', 1.0, 'Water', 'sea, river, ferry, tram', '水系'),
        ('yellow', 1.0, 'Parks', 'gardens, squares, beach', '公园'), ('magenta', 1.0, 'Route', 'the walk, six stops', '路线')]
for i, (ink, cv, a, b, zh) in enumerate(rows):
    y = 444 + i * 50
    film.fill(o.rrect(x, y - 13, x + 26, y + 13, 2), cv, ink=ink)
    film.text(a, x + 44, y, 23, 'map_bold', 1.0, anchor='lm')
    film.text(b, x + 122, y, 20, 'map', 0.8, anchor='lm')
    film.text(zh, LX1 - 46, y, 20, 'cjk', 0.75, anchor='rm')
    film.line([(x, y + 25), (LX1 - 46, y + 25)], 1.0, 0.25, cap=False)
names = [('Station', '车站'), ('Market Square', '集市广场'), ('Old Bridge', '老桥'), ('Castle Hill', '城堡山'), ('Fish Market', '鱼市'), ('Lighthouse', '灯塔')]
for i, (en, zh) in enumerate(names):
    y = 672 + i * 34
    film.circle(x + 13, y, 12.5, ink='magenta')
    film.text(str(i + 1), x + 13, y + 1, 16, 'map_bold', knock=True, halo_inks=['magenta'])
    film.text(en, x + 40, y, 21, 'map', 1.0, anchor='lm')
    film.text(zh, LX1 - 46, y, 19, 'cjk', 0.7, anchor='rm')
# scale bar and north arrow
sy = 898
for k in range(4):
    m = o.rrect(x + k * 50, sy - 4, x + (k + 1) * 50, sy + 4)
    film.fill(m, 1.0 if k % 2 == 0 else 0.0)
film.line([(x, sy - 4), (x + 200, sy - 4), (x + 200, sy + 4), (x, sy + 4)], 1.0, 1.0, closed=True, cap=False)
for k, lab in enumerate(['0', '100', '200', '300', '400 m']):
    film.text(lab, x + k * 50, sy - 18, 14, 'map', 0.9, anchor='mm')
nx, ny = LX1 - 72, 886
film.fill([(nx, ny - 30), (nx + 11, ny + 10), (nx, ny + 3)], 1.0)
film.line([(nx, ny - 30), (nx - 11, ny + 10), (nx, ny + 3)], 1.2, 1.0, closed=True)
film.text('N', nx, ny + 26, 16, 'map_bold', 1.0)
tick('film')

# ===================================================================== on the light box, stage by stage
o.lamp(0.0); o.stage('lamp_off')
o.lamp(0.5); o.stage('lamp_warm')
o.lamp(1.0); o.stage('lamp_on')
o.place(base); o.stage('base')
o.place(blue, lift=1.0, dx=8, dy=-22, rot=0.7); o.stage('blue_lifted')
o.place(blue); o.stage('blue_down')
o.place(yel, lift=1.0, dx=-34, dy=-26, rot=-1.5); o.stage('yellow_lifted')
o.place(yel); o.stage('yellow_down')
o.place(mag, lift=1.0, dx=34, dy=-30, rot=1.4); o.stage('magenta_lifted')
o.place(mag); o.stage('magenta_down')
o.place(film, lift=1.0, dx=-16, dy=-30, rot=2.2); o.stage('film_lifted')
o.place(film); o.stage('film_down')
for (cx, cy, rot) in [(94, 972, 40), (1258, 972, -40), (1008, 144, 40), (660, 198, 4), (1254, 200, 40), (1316, 116, -38), (1828, 116, 38)]:
    o.tape(cx, cy, rot=rot)
img = o.save(out, stages_dir=stages)
tick('saved')
print('saved', out)
