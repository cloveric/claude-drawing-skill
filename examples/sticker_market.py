"""Example (sticker collage x receipt): 周末市集 / Weekend Market — a market haul as a flat-lay on a cream
board: a folded thermal receipt taped down (grey thermal print, dotted leaders, a struck-through old price,
a barcode, red-pen ticks and a circled total), die-cut vinyl stickers of a sourdough loaf, heirloom
tomatoes, a tulip bouquet and a bag of coffee beans (three with a peeled corner), bold sticker lettering, a
scalloped sale badge, a stall-number sticker, two price tags hanging on baker's twine, washi tape, and a
round PAID / 已付 rubber stamp. No image model.
python3 sticker_market.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from sticker import Sticker, measure, _resample
from core import blob_pts, spline, blur, smoothstep

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'sticker_market.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

s = Sticker(1920, 1080, seed=26)
TOMATO, MUSTARD, MINT, MINTD = '#E04A2F', '#E8AC2C', '#8FD2B5', '#2F8F6C'
NAVY, NAVY2, KRAFT, CREAM, PEN = '#1B2745', '#26355C', '#D9C7A3', '#FBF3E4', '#C9302A'

# ---- board
s.board('#EFE5D1', 'cream')
s.stage('board')

# ---- the receipt
r = s.receipt(480, 960, margin=36)
r.centre(78, 'WEEKEND MARKET', 30, bold=True, spacing=2)
r.centre(116, '周末市集 · STALL 12', 21, font='typewriter')
r.centre(146, 'SAT 26 SEP 2026   09:42', 19)
r.rule(172, 'dash')
ITEMS = [(222, 'SOURDOUGH LOAF', '38.00', None), (262, 'HEIRLOOM TOMATO', '', None),
         (292, '  1.2 kg @ 22.00', '26.40', None), (334, 'FLOWERS, BOUQUET', '45.00', None),
         (376, 'COFFEE BEANS 250g', '54.40', '68.00'), (406, '  WEEKEND SALE -20%', '', None)]
for y, name, amt, was in ITEMS:
    r.row(y, name, amt, 21 if not name.startswith('  ') else 19, was=was)
r.rule(436, 'dash')
r.row(486, 'TOTAL', '¥163.80', 30, bold=True, leader=False)
r.row(528, 'CASH', '170.00', 20)
r.row(558, 'CHANGE', '6.20', 20)
r.rule(592, 'stars')
r.centre(646, '4 ITEMS  ·  THANK YOU', 19)
r.centre(676, 'SEE YOU NEXT SATURDAY', 19)
r.barcode(712, 74, seed=5)
r.centre(812, '0926  0942  0012', 17, spacing=2)
r.crease(505, 498)
RX, RY, RR = 345, 548, -2.2
T = s.lay(r, RX, RY, RR, curl=0.8)
s.stage('receipt')

# ---- washi tape holding it down
s.tape(*T(240, 8), 230, rot=RR + 5, colour=MUSTARD, width=46, pattern='stripe', alpha=0.82)
s.tape(*T(462, 948), 150, rot=RR - 42, colour=MINT, width=40, pattern='dot', alpha=0.8)
s.stage('tape')


# ---- produce stickers (flat vector on transparent sheets, then die-cut)
def lens_score(a, P, up_w, lo_w, clip_to):
    """a slash scored into the crust that opened in the oven: pale lens under a dark raised ear"""
    P = np.asarray(P, np.float32)
    d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    nrm = np.stack([d[:, 1], -d[:, 0]], 1)
    w = np.sin(np.pi * np.linspace(0, 1, len(P))) ** 0.7
    up, lo = P + nrm * (up_w * w)[:, None], P - nrm * (lo_w * w)[:, None]
    lens = a.poly(np.vstack([up, lo[::-1]])) * clip_to
    a.gradient(lens, '#F6DDA8', '#DDA964', P[0] - nrm[0] * 30, P[0] + nrm[0] * 10, clip=True)
    a.fill(a.line(up, 4.0) * clip_to, '#5E2E10', 0.9, clip=True)
    a.fill(a.line(up + nrm * 4.5, 2.2) * clip_to, '#F4C98A', 0.8, clip=True)


def bread():
    a = s.art(450, 250)
    cx, cy = 225, 126
    pts = blob_pts(cx, cy, 205, 86, rough=0.02, n=160, seed=5, rot=np.deg2rad(-5))
    pts[:, 1] = np.minimum(pts[:, 1], cy + 68)                 # the loaf sits flat on its base
    body = a.poly(pts)
    a.gradient(body, '#D8913F', '#99521F', (cx, cy - 90), (cx, cy + 75))
    a.fill(a.crescent(body, -8, -22), '#723912', 0.8, clip=True)
    a.fill(a.crescent(body, 10, 15), '#EFB66C', 0.6, clip=True)
    a.fill(a.blob(cx - 10, cy - 34, 170, 44, 0.25, seed=9) * body, '#FFF6E6', 0.22, clip=True)   # flour dust
    for x0 in (70, 170, 270):                                    # three overlapping slashes along the loaf
        lens_score(a, spline([(x0, cy + 22), (x0 + 55, cy - 6), (x0 + 118, cy - 26)], 20), 4, 17, body)
    a.speckle(body * (a.YY < cy + 20), '#FFF9EE', 260, (0.7, 1.7), (0.35, 0.8), seed=3)
    a.speckle(body, '#5E2E10', 30, (1.0, 2.0), (0.3, 0.55), seed=4)
    return a


def tomato(a, cx, cy, R, base, dark, light, ph):
    t = np.linspace(0, 2 * np.pi, 260, endpoint=False)
    rr = R * (1 + 0.035 * np.cos(6 * t + ph) + 0.015 * np.cos(10 * t + 2 * ph))
    dt = ((t + np.pi / 2 + np.pi) % (2 * np.pi)) - np.pi
    rr = rr - R * 0.12 * np.exp(-(dt / 0.42) ** 2)
    body = a.poly(np.stack([cx + np.cos(t) * rr * 1.07, cy + np.sin(t) * rr * 0.87], 1))
    a.radial(body, light, base, cx - R * 0.4, cy - R * 0.35, R * 1.35)
    a.fill(a.crescent(body, -R * 0.14, -R * 0.15), dark, 0.8, clip=True)
    for k in (-0.8, -0.38, 0.38, 0.8):
        rib = a.line([(cx + k * R * 0.08, cy - R * 0.6), (cx + k * R * 0.6, cy - R * 0.36), (cx + k * R * 1.0, cy + R * 0.2)], R * 0.035, smooth=True)
        a.fill(rib * body, dark, 0.35, clip=True)
    a.fill(a.ellipse(cx - R * 0.5, cy - R * 0.36, R * 0.24, R * 0.11, -28), '#FFFFFF', 0.25, clip=True)
    a.fill(a.ellipse(cx - R * 0.52, cy - R * 0.4, R * 0.13, R * 0.05, -28), '#FFFFFF', 0.85, clip=True)
    sx, sy = cx, cy - R * 0.64                                  # star-shaped calyx seen from the side
    for i, ang in enumerate(np.linspace(0, 2 * np.pi, 6, endpoint=False) + ph):
        L = R * (0.46 + 0.08 * np.cos(i * 2.3))
        tip = (sx + np.cos(ang) * L, sy + np.sin(ang) * L * 0.42 + R * 0.05)
        side = np.array([-np.sin(ang), np.cos(ang) * 0.42]) * R * 0.075
        leaf = [(sx + side[0], sy + side[1]), ((sx + tip[0]) / 2 + side[0] * 0.6, (sy + tip[1]) / 2 + side[1] * 0.6 - R * 0.03),
                tip, ((sx + tip[0]) / 2 - side[0] * 0.6, (sy + tip[1]) / 2 - side[1] * 0.6 - R * 0.03), (sx - side[0], sy - side[1])]
        a.fill(a.poly(leaf), '#3D7A46' if np.sin(ang) > -0.2 else '#4F9152')
    a.fill(a.line([(sx, sy), (sx + R * 0.03, sy - R * 0.2), (sx + R * 0.11, sy - R * 0.27)], R * 0.07, smooth=True), '#4A7A3C')


def tomatoes():
    a = s.art(380, 270)
    tomato(a, 262, 158, 80, MUSTARD, '#C27F17', '#F6CD6A', 1.1)
    tomato(a, 148, 146, 104, TOMATO, '#B3321D', '#F0775A', 0.3)
    return a


def closed(pts, per=12):
    """smooth closed outline through pts"""
    P = [pts[-1]] + list(pts) + [pts[0], pts[1]]
    return spline(P, per)[per:-per]


def tulip(a, x, y, r, col, dark, tilt=0.0):
    """side view: two outer petals with pointed tips, a front petal in the lighter colour"""
    t = np.deg2rad(tilt); c, sn = np.cos(t), np.sin(t)
    tr = lambda P: [(x + (px * c - py * sn) * r, y + (px * sn + py * c) * r) for px, py in P]
    a.fill(a.line(tr([(0, 0.6), (0.05, 1.6), (0.1, 3.4)]), 3.4), '#4F7F68')
    back = [(-0.6, -0.98), (-0.72, -0.3), (-0.56, 0.3), (-0.24, 0.62), (0.24, 0.62), (0.56, 0.3), (0.72, -0.3), (0.6, -0.98), (0.3, -0.6), (0, -0.7), (-0.3, -0.6)]
    a.fill(a.poly(closed(tr(back))), dark)
    front = [(0, -1.06), (-0.3, -0.5), (-0.44, 0.08), (-0.3, 0.5), (0, 0.63), (0.3, 0.5), (0.44, 0.08), (0.3, -0.5)]
    fm = a.poly(closed(tr(front)))
    a.fill(fm, col)
    a.fill(a.crescent(fm, r * 0.1 * c, -r * 0.1 * sn) * fm, '#FFFFFF', 0.22, clip=True)


def daisy(a, x, y, r, petal, centre, n=13, rot=0.0):
    for ang in np.linspace(0, 360, n, endpoint=False) + rot:
        t = np.deg2rad(ang)
        a.fill(a.ellipse(x + np.cos(t) * r * 0.55, y + np.sin(t) * r * 0.55, r * 0.46, r * 0.15, ang), petal)
    a.fill(a.circle(x, y, r * 0.27), centre)
    a.fill(a.crescent(a.circle(x, y, r * 0.27), -2, -3), '#9A6410', 0.6, clip=True)


def bouquet():
    a = s.art(390, 530)
    a.fill(a.poly([(46, 230), (118, 138), (268, 118), (344, 200), (212, 505), (178, 505)]), '#CDB48A')
    rng = np.random.default_rng(11)
    for (p1, p2, p3) in [((190, 300), (120, 180), (58, 96)), ((200, 300), (262, 170), (318, 78)),
                         ((210, 310), (300, 230), (362, 176)), ((180, 310), (90, 250), (30, 196)), ((196, 300), (190, 160), (196, 40))]:
        P = spline([p1, p2, p3], 30)
        a.fill(a.line(P, 3.2), '#4F7F68')
        x, y, *_ = _resample(P, 21)
        for i, (lx, ly) in enumerate(zip(x[3:], y[3:])):
            side = 1 if i % 2 else -1
            j = min(i + 4, len(x) - 1)
            ang = np.degrees(np.arctan2(y[j] - y[j - 1], x[j] - x[j - 1])) + 90 * side
            o = np.deg2rad(ang)
            a.fill(a.ellipse(lx + np.cos(o) * 10, ly + np.sin(o) * 10, 11.5, 9, ang), MINT if rng.random() < 0.6 else '#6DB597')
    for (x, y) in [(172, 92), (320, 122), (86, 150)]:                 # billy buttons on thin stems
        a.fill(a.line([(x, y), (x + (190 - x) * 0.4, y + 120)], 2.4), '#4F7F68')
        a.fill(a.circle(x, y, 15), MUSTARD)
        a.speckle(a.circle(x, y, 14), '#B97C12', 26, (1.0, 1.6), (0.5, 0.8), seed=int(x))
        a.fill(a.circle(x - 5, y - 5, 5), '#FFFFFF', 0.25, clip=True)
    tulip(a, 196, 118, 50, '#F08A6C', '#C9573A', 2)
    tulip(a, 118, 170, 48, TOMATO, '#A82D1A', -16)
    tulip(a, 276, 166, 46, TOMATO, '#A82D1A', 14)
    daisy(a, 318, 240, 38, CREAM, MUSTARD, 13, 8)
    daisy(a, 72, 258, 34, CREAM, MUSTARD, 12, 0)
    tulip(a, 200, 222, 44, '#F08A6C', '#C9573A', -4)
    cone = a.poly([(20, 262), (358, 232), (214, 508), (176, 510)])
    a.gradient(cone, '#E6D5AF', '#C6AB7C', (40, 250), (330, 330))
    a.fill(a.poly([(20, 262), (150, 251), (196, 508), (176, 510)]), '#EFE3C6', 0.9, clip=True)
    a.fill(a.line([(20, 262), (358, 232)], 3), '#B8996A', 0.9)
    a.fill(a.poly([(96, 392), (290, 382), (282, 404), (104, 414)]), NAVY)          # ribbon band and bow
    for sgn in (-1, 1):
        a.fill(a.ellipse(194 + sgn * 34, 386, 34, 15, sgn * 16), NAVY)
        a.fill(a.ellipse(194 + sgn * 32, 386, 18, 6, sgn * 16), '#0F1830', 0.9)
        a.fill(a.poly([(194, 398), (194 + sgn * 18, 402), (194 + sgn * 44, 470), (194 + sgn * 30, 474)]), NAVY)
    a.fill(a.circle(194, 393, 12), NAVY2)
    return a


def coffee():
    a = s.art(300, 390)
    body = smoothstep(0.3, 0.7, blur(a.poly([(42, 76), (258, 76), (270, 368), (30, 368)]), 3))
    a.gradient(body, NAVY2, NAVY, (42, 76), (258, 368))
    a.fill(a.poly([(42, 76), (70, 76), (62, 368), (30, 368)]), '#3A4D82', 0.55, clip=True)   # lit side gusset
    a.fill(a.poly([(230, 76), (258, 76), (270, 368), (238, 368)]), '#0E1528', 0.55, clip=True)
    a.fill(a.crescent(body, 0, -14), '#0B1122', 0.5, clip=True)
    zz = [(38 + i * 7.5, 34 if i % 2 else 40) for i in range(30)]
    top = a.poly(zz + [(261, 40), (262, 80), (38, 80)])
    a.fill(top, '#33477C')
    for x in np.arange(44, 256, 6.0):
        a.fill(a.line([(x, 44), (x, 62)], 1.4), '#5A6FA8', 0.5, clip=True)
    a.fill(a.rrect(24, 78, 276, 92, 5), '#D8B869')                                   # tin tie
    a.fill(a.rrect(26, 79, 274, 83, 2), '#F3DD9E', 0.8)
    a.fill(a.rrect(24, 88, 276, 92, 3), '#9C7B32', 0.8)
    a.fill(a.circle(218, 124, 10), '#101830'); a.fill(a.ring(218, 124, 10, 3), '#4A5C92')   # one-way valve
    lab = a.circle(150, 226, 80)
    a.fill(lab, MUSTARD)
    a.fill(a.ring(150, 226, 70, 2.2), NAVY)
    a.fill(a.ellipse(150, 196, 25, 17, -28), NAVY)
    a.fill(a.line(spline([(131, 206), (146, 196), (154, 197), (169, 186)], 10), 3.2), MUSTARD)
    a.fill(a.text('COFFEE', 150, 244, 22, 'sans_bold', 'mm', spacing=4), NAVY)
    a.fill(a.text('250 g · 中烘', 150, 272, 15, 'sans_bold', 'mm', spacing=1), NAVY)
    a.fill(a.line([(88, 110), (82, 340)], 12) * body, '#FFFFFF', 0.07, clip=True)
    return a


s.stick(bread(), 860, 478, rot=-5, border=15, peel='bl', peel_size=34)
s.stick(tomatoes(), 1248, 452, rot=6, border=15)
s.stage('produce')
s.stick(coffee(), 900, 808, rot=-4, border=15)
s.stick(bouquet(), 1405, 772, rot=5, border=15, peel='tr', peel_size=38)
s.stage('bouquet_coffee')

# ---- price tags on baker's twine, taped to the top edge
tags = []
for (cx, cy, rot, w, h, colour, grom, en, zh, price, ink) in [
        (1592, 318, 5, 170, 290, KRAFT, '#C9A55C', 'SOURDOUGH', '酸种面包', '¥38', TOMATO),
        (1796, 668, -4, 150, 262, MUSTARD, '#C8C8C3', 'FLOWERS', '鲜花一束', '¥45', NAVY)]:
    t = s.tag_art(w, h, colour, grom)
    t.fill(t.text(en, w / 2, h * 0.43, 17, 'sans_bold', 'mm', spacing=2.5), NAVY, 0.92)
    t.fill(t.text(zh, w / 2, h * 0.54, 23, 'sans_bold', 'mm'), NAVY, 0.92)
    dots = np.maximum.reduce([t.circle(x, h * 0.63, 1.5) for x in np.arange(22, w - 20, 9.0)])
    t.fill(dots, NAVY, 0.6)
    t.fill(t.text(price, w / 2, h * 0.8, 76 if w > 160 else 68, 'condensed', 'mm'), ink, 0.95)
    Tt = s.lay(t, cx, cy, rot, curl=0.15, lift=2.2)
    tags.append((Tt(*t.hole), cx))
for (hx, hy), cx in tags:
    top = (hx + (6 if cx < 1700 else -8), 26)
    s.twine([top, ((top[0] + hx) / 2 + (9 if cx < 1700 else -12), (top[1] + hy) / 2), (hx, hy - 2)], width=4.2)
s.tape(1690, 30, 420, rot=-1.5, colour=MINT, width=48, pattern='stripe', alpha=0.8)
s.stage('tags')

# ---- lettering
s.stick(s.lettering_art([('周末', NAVY), ('市集', TOMATO)], 150, 'cjk_sans', weight=4), 1000, 148, rot=-2, border=20, gloss=0.8)
s.stick(s.label_art('WEEKEND MARKET  ·  SAT 26 SEP', 25, NAVY, CREAM, dot=MINT, spacing=1.5), 940, 272, rot=1.5, border=10)
s.stage('title')

# ---- sale badge and a small label
s.stick(s.badge_art(118, TOMATO, '-20%', top='SALE', bottom='咖啡豆', big_size=62), 1148, 930, rot=-9, border=14, peel='br', peel_size=30)
s.stick(s.label_art('FRESH · 新鲜', 24, MINT, '#17503C', spacing=1), 1342, 318, rot=8, border=10)
stall = s.art(190, 190)
stall.radial(stall.circle(95, 95, 92), NAVY2, NAVY, 60, 55, 140)
stall.fill(stall.ring(95, 95, 80, 2), MUSTARD, 0.8)
stall.fill(stall.text('STALL', 95, 52, 17, 'sans_bold', 'mm', spacing=4), CREAM)
stall.fill(stall.text('12', 95, 100, 70, 'condensed', 'mm'), MUSTARD)
stall.fill(stall.text('摊位', 95, 146, 19, 'sans_bold', 'mm', spacing=4), CREAM)
s.stick(stall, 1742, 952, rot=10, border=12)
s.stage('sale')

# ---- rubber stamp and red pen on the receipt
s.stamp(*T(352, 626), 96, 'WEEKEND MARKET · 周末市集 · 26.09.2026 · ', '已付', 'PAID', TOMATO, rot=-14, strength=0.85)
for y, name, amt, was in ITEMS:
    if amt and not name.startswith('  ') or name.startswith('HEIRLOOM'):
        x0, yy = 16, y - 6
        s.pen([T(x0 - 6, yy - 6), T(x0, yy + 1), T(x0 + 12, yy - 16)], PEN, 2.6, smooth=False)
wt = measure('¥163.80', 30, 'typewriter') + 6
cxl, cyl = 480 - 36 - wt / 2, 476
rng = np.random.default_rng(3)
loop = [(cxl + np.cos(a) * (wt / 2 + 20) * (1 + rng.normal(0, .02)), cyl + np.sin(a) * 30 * (1 + rng.normal(0, .03)) - 3 * np.sin(a / 2))
        for a in np.linspace(-2.6, -2.6 + 2 * np.pi + 0.55, 16)]
s.pen([T(x, y) for x, y in loop], PEN, 2.8)

s.save(out, stages_dir=stages)
print('saved', out)
