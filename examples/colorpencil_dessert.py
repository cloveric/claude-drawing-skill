"""Example (Korean-style coloured pencil): Afternoon Dessert / 午后甜点 — strawberry shortcake,
a cup of tea, strawberries; soft layered hatching, grainy wax on paper tooth, brown pencil
outlines, white gel-pen sparkles. Pure code, no image model.
python3 colorpencil_dessert.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from colorpencil import ColorPencil, hexc
from core import spline, blob_pts, blur

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'colorpencil_dessert.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

p = ColorPencil(1920, 1080, seed=327)
p.paper()
rng = p.rng
BROWN = '#8a6a5a'
p.stage('paper')

# ---- soft backdrop circle and a table band
p.hatch(p.mask_ellipse(960, 540, 470, 430, feather=40), '#fbe7ad', pressure=0.35, angle=0.8, spacing=6, edge_fade=60)
table = p.mask_poly([(0, 760), (1920, 740), (1920, 1080), (0, 1080)], feather=6) * np.clip((p.YY - 740) / 200, 0.4, 1)
p.hatch(table, '#f2cdbf', pressure=0.4, angle=0.15, spacing=6, length=(60, 160), edge_fade=0)
p.line(spline([(0, 762), (960, 752), (1920, 742)], 20), BROWN, 2.0, 0.35)
p.stage('backdrop')

# ---- plate
PX, PY = 820, 780
plate = p.mask_ellipse(PX, PY, 360, 92)
p.hatch(plate, '#e3ebf1', pressure=0.5, angle=0.3)
inner = p.mask_ellipse(PX, PY - 6, 285, 66)
p.hatch(plate * (1 - inner), '#a9bccd', pressure=0.5, angle=2.4)
ell = lambda cx, cy, rx, ry, n=80: [(cx + rx * np.cos(t), cy + ry * np.sin(t)) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]
p.outline(ell(PX, PY, 360, 92), BROWN, 2.2, 0.55)
p.outline(ell(PX, PY - 6, 285, 66), BROWN, 1.6, 0.3)

# ---- strawberry shortcake slice (cut face with layers, cream top, crust side)
TT, TB = (560, 610), (560, 680)            # tip top / bottom
BT, BB = (960, 520), (960, 720)            # back edge of the cut face
RT, RB = (1060, 548), (1060, 736)          # far edge of the round side
cut = [TT, BT, BB, TB]
side = [BT, RT, RB, BB]
top = [TT, (740, 520), (1000, 470), RT, BT]
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def band(f0, f1):
    return p.mask_poly([lerp(TT, TB, f0), lerp(BT, BB, f0), lerp(BT, BB, f1), lerp(TT, TB, f1)], feather=1.2)
p.hatch(p.mask_poly(side), '#f7e6c4', pressure=0.5, angle=1.4)
p.shade(p.mask_poly(side), '#e2b98a', pressure=0.35, angle=2.6)
for (f0, f1, col, pr) in [(0.0, 0.12, '#fbe9d2', 0.5), (0.12, 0.42, '#f3c36b', 0.7), (0.42, 0.58, '#fbe4dc', 0.5),
                          (0.58, 0.9, '#f3c36b', 0.7), (0.9, 1.0, '#dfa45a', 0.75)]:
    p.hatch(band(f0, f1), col, pressure=pr, angle=0.35)
for k in range(5):                         # strawberry slices in the cream layer
    t = 0.12 + k * 0.19
    cx, cy = lerp(lerp(TT, TB, 0.5), lerp(BT, BB, 0.5), t)
    r = 18 + 22 * t
    m = p.mask_ellipse(cx, cy, r, r * 0.55)
    p.hatch(m, '#ef6f7f', pressure=0.75, angle=0.8, spacing=4)
    p.hatch(p.mask_ellipse(cx, cy, r * 0.5, r * 0.28), '#ffd0d6', pressure=0.4, angle=2.0)
p.shade(band(0.12, 1.0) * np.clip((p.XX - 560) / 400, 0, 1) ** 2, '#d9a35f', pressure=0.35, angle=2.4)
p.hatch(p.mask_poly(top), '#f7e4cb', pressure=0.62, angle=0.6)
p.shade(p.mask_poly(top) * np.clip((p.YY - 470) / 140, 0, 1), '#d8c6d6', pressure=0.45, angle=2.2)
for poly in (cut, side, top):
    p.outline(poly, BROWN, 2.0, 0.55)
for k in range(4):                         # layer lines on the cut face
    f = [0.12, 0.42, 0.58, 0.9][k]
    p.line([lerp(TT, TB, f), lerp(BT, BB, f)], BROWN, 1.3, 0.25)
# cream dollops and a whole strawberry on top
for (cx, cy, r) in [(700, 520, 34), (820, 500, 38), (930, 482, 32)]:
    pts = blob_pts(cx, cy, r, r * 0.8, rough=0.12, n=60, seed=int(cx))
    p.hatch(p.mask_poly(pts), '#f8e2c4', pressure=0.65, angle=0.6)
    p.shade(p.mask_poly(pts) * np.clip((p.YY - cy + r * 0.3) / r, 0, 1), '#c9b3d1', pressure=0.7, angle=2.2)
    p.outline(pts, BROWN, 1.6, 0.4)
    p.line(spline([(cx - r * 0.5, cy - r * 0.1), (cx, cy - r * 0.45), (cx + r * 0.4, cy - r * 0.1)], 8), BROWN, 1.2, 0.25)
SB = [(826, 470), (786, 430), (790, 395), (826, 385), (862, 395), (866, 430)]
sb = spline(SB + [SB[0]], 10)
p.hatch(p.mask_poly(sb), '#ea4f62', pressure=0.8, angle=0.9, spacing=4)
p.shade(p.mask_poly(sb) * np.clip((p.XX - 820) / 50, 0, 1), '#b8324a', pressure=0.5, angle=2.3)
p.outline(sb, '#8a3a44', 1.8, 0.6)
for (lx, ly, a) in [(812, 384, -2.4), (826, 380, -1.57), (840, 384, -0.7)]:
    leaf = [(lx, ly), (lx + np.cos(a - 0.4) * 22, ly + np.sin(a - 0.4) * 22), (lx + np.cos(a) * 34, ly + np.sin(a) * 34), (lx + np.cos(a + 0.4) * 22, ly + np.sin(a + 0.4) * 22)]
    p.hatch(p.mask_poly(leaf), '#6fae5a', pressure=0.75, angle=1.2, spacing=4)
    p.outline(leaf, '#4e7a3c', 1.4, 0.5)
p.dots(p.mask_poly(sb), '#fbe3a0', n=16, r=(1.6, 2.6))
p.stage('cake')

# ---- teacup and saucer with steam
CX, CY = 1390, 640
p.hatch(p.mask_ellipse(CX, 760, 200, 52), '#dfe8ef', pressure=0.55, angle=0.3)
p.shade(p.mask_ellipse(CX, 760, 200, 52) * (1 - p.mask_ellipse(CX, 752, 150, 34)), '#a9bccd', pressure=0.5, angle=2.3)
p.outline(ell(CX, 760, 200, 52), BROWN, 2.0, 0.5)
body = spline([(CX - 130, CY), (CX - 118, CY + 70), (CX - 60, CY + 120), (CX + 60, CY + 120), (CX + 118, CY + 70), (CX + 130, CY)], 12).tolist()
cup = body + [(CX + 130, CY), (CX - 130, CY)]
p.hatch(p.mask_poly(cup), '#f1eef0', pressure=0.5, angle=0.5)
p.shade(p.mask_poly(cup) * np.clip((p.XX - CX + 20) / 120, 0, 1), '#aebfd0', pressure=0.55, angle=2.3)
p.hatch(p.mask_poly(cup) * (np.abs(p.YY - (CY + 55)) < 14), '#f2a7b4', pressure=0.65, angle=0.2)      # pink band
for fx in (CX - 70, CX - 10, CX + 50):                                                                  # little flowers
    for a in np.linspace(0, 2 * np.pi, 5, endpoint=False):
        p.hatch(p.mask_ellipse(fx + np.cos(a) * 7, CY + 95 + np.sin(a) * 7, 5.5, 5.5), '#f08aa0', pressure=0.8, spacing=3, length=(6, 12), edge_fade=0)
handle = [(CX + 118, CY + 22), (CX + 178, CY + 18), (CX + 190, CY + 60), (CX + 150, CY + 92), (CX + 108, CY + 80)]
p.line(spline(handle, 10), BROWN, 9, 0.35)
p.line(spline(handle, 10), BROWN, 2.0, 0.55)
p.outline(cup, BROWN, 2.0, 0.55)
p.hatch(p.mask_ellipse(CX, CY, 124, 30), '#c9824a', pressure=0.65, angle=0.3)
p.hatch(p.mask_ellipse(CX - 30, CY - 6, 50, 10), '#e9b27a', pressure=0.4, angle=0.3)
p.outline(ell(CX, CY, 130, 34), BROWN, 2.0, 0.55)
for k in range(3):
    x0 = CX - 50 + k * 50
    p.line(spline([(x0, CY - 50), (x0 - 18, CY - 100), (x0 + 12, CY - 150), (x0 - 10, CY - 200)], 10), '#b7aaa4', 2.2, 0.4)
p.stage('tea')

# ---- a few strawberries on the table, sparkles
def berry(x, y, s, rot):
    pts = spline([(x, y + 40 * s), (x - 34 * s, y), (x - 26 * s, y - 30 * s), (x, y - 36 * s), (x + 26 * s, y - 30 * s), (x + 34 * s, y), (x, y + 40 * s)], 10)
    c, si = np.cos(rot), np.sin(rot)
    pts = np.stack([x + (pts[:, 0] - x) * c - (pts[:, 1] - y) * si, y + (pts[:, 0] - x) * si + (pts[:, 1] - y) * c], 1)
    m = p.mask_poly(pts)
    p.hatch(m, '#ea4f62', pressure=0.8, angle=0.9, spacing=4)
    p.shade(m * np.clip((p.XX - x) / (30 * s), 0, 1), '#b8324a', pressure=0.5, angle=2.3)
    p.outline(pts, '#8a3a44', 1.6, 0.55)
    p.dots(m, '#fbe3a0', n=12, r=(1.4, 2.4))
    cx, cy = x + np.sin(-rot) * 36 * s, y - np.cos(rot) * 36 * s
    for a in (-2.5, -1.57, -0.64):
        leaf = [(cx, cy), (cx + np.cos(a + rot - 0.4) * 16 * s, cy + np.sin(a + rot - 0.4) * 16 * s), (cx + np.cos(a + rot) * 26 * s, cy + np.sin(a + rot) * 26 * s), (cx + np.cos(a + rot + 0.4) * 16 * s, cy + np.sin(a + rot + 0.4) * 16 * s)]
        p.hatch(p.mask_poly(leaf), '#6fae5a', pressure=0.7, angle=1.2, spacing=4)
    p.sparkle(x - 12 * s, y - 14 * s, 7 * s)
berry(1180, 900, 1.0, 0.4)
berry(1290, 950, 0.85, -0.5)
berry(470, 920, 0.95, -0.2)
for (x, y, r) in [(814, 404, 8), (1335, 612, 7), (560, 700, 6), (1160, 460, 10), (640, 380, 7), (1520, 470, 9)]:
    p.sparkle(x, y, r)

p.save(out, stages_dir=stages)
print('saved', out)
