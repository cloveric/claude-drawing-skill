"""Example (cross-stitch embroidery): Home Sampler / 十字绣样本 — a classic sampler on Aida cloth: a stitched
border of diamonds, "H♥ME" in the cross-stitch alphabet with a satin-stitch heart for the O, a cottage with
back-stitched window panes and a satin door, an apple tree with French-knot apples, a pine, a satin sun,
half-stitch clouds, a row of flowers, and a woven label sewn on with running stitch. No image model.
python3 stitch_sampler.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from stitch import Stitch
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'stitch_sampler.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

s = Stitch(1920, 1080, cell=12, seed=7, cloth='#f0e8d6')
rng = s.rng
C = s.cell
GW, GH = s.gw, s.gh                                      # 160 x 90 cells
NAVY, RED, CORAL, MUSTARD = '#2e3f66', '#c0423a', '#e0654a', '#e3a53a'
GREEN, DKGREEN, LTGREEN, BROWN = '#5f8f4e', '#3f6b45', '#9cbf6b', '#7a4e33'
SKY, PINK, WALL, ROOF, GREY = '#9cc0dc', '#e58f9f', '#f1d08a', '#b5523b', '#a4a8ae'


def box(gx0, gy0, gx1, gy1):
    g = np.zeros((GH, GW), bool); g[gy0:gy1, gx0:gx1] = True; return g


# ---- border: two framing lines and a band of alternating diamonds, flowers at the corners
frame = box(4, 4, GW - 4, GH - 4) & ~box(5, 5, GW - 5, GH - 5)
inner = box(12, 12, GW - 12, GH - 12) & ~box(13, 13, GW - 13, GH - 13)
s.cross(frame, DKGREEN)
s.cross(inner, DKGREEN)
diamond = ['..#..', '.###.', '#####', '.###.', '..#..']
k = 0
for gx in range(15, GW - 18, 8):
    for gy in (6, GH - 11):
        s.chart(diamond, gx, gy, {'#': RED if k % 2 == 0 else MUSTARD})
    k += 1
k = 0
for gy in range(15, GH - 18, 8):
    for gx in (6, GW - 11):
        s.chart(diamond, gx, gy, {'#': RED if k % 2 == 0 else MUSTARD})
    k += 1
corner = ['.#.#.', '#####', '#####', '.###.', '..#..']          # little hearts at the corners
for (gx, gy) in [(6, 6), (GW - 11, 6), (6, GH - 11), (GW - 11, GH - 11)]:
    s.chart(corner, gx, gy, {'#': CORAL})
s.stage('border')

# ---- "H♥ME": cross-stitch alphabet, with a padded satin heart in place of the O
TW = Stitch.letters_width('HOME', scale=2)
TX = (GW - TW) // 2
s.letters('H', TX, 16, NAVY, scale=2)
s.letters('ME', TX + 24, 16, NAVY, scale=2)
hx, hy = (TX + 12 + 5) * C, (16 + 7) * C
t = np.linspace(0, 2 * np.pi, 200)
heart = np.stack([hx + 16 * np.sin(t) ** 3 * 4.6, hy - (13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)) * 4.6 - 4], 1)
s.satin(s.poly(heart), RED, angle=0.85)
s.stage('title')

# ---- sky: satin sun with back-stitched rays, half-stitch clouds, back-stitched birds
SX, SY = 30 * C, 25 * C
s.satin(s.circle(SX, SY, 52), MUSTARD, angle=0.3)
for a in np.linspace(0, 2 * np.pi, 10, endpoint=False):
    s.back([(SX + np.cos(a) * 70, SY + np.sin(a) * 70), (SX + np.cos(a) * 112, SY + np.sin(a) * 112)], MUSTARD, step=6, smooth=False)   # one long stitch per ray
for (cx, cy, w) in [(130, 23, 15), (46, 34, 8)]:
    cloud = np.maximum.reduce([s.circle((cx + dx) * C, (cy + dy) * C, r * C) for dx, dy, r in
                               [(-w * 0.45, 1, w * 0.3), (0, -0.5, w * 0.38), (w * 0.42, 1, w * 0.28)]])
    cloud = np.maximum(cloud, s.rect((cx - w * 0.72) * C, cy * C, (cx + w * 0.7) * C, (cy + w * 0.22) * C))
    s.half(s.cells(cloud), SKY)
for (bx, by, sc) in [(134, 34, 1.0), (141, 31, 0.8)]:
    s.back([(bx * C - 26 * sc, by * C - 6 * sc), (bx * C - 12 * sc, by * C - 14 * sc), (bx * C, by * C)], NAVY, smooth=False)
    s.back([(bx * C, by * C), (bx * C + 12 * sc, by * C - 14 * sc), (bx * C + 26 * sc, by * C - 6 * sc)], NAVY, smooth=False)
s.stage('sky')

# ---- cottage: walls, stepped roof, chimney with half-stitch puffs of smoke, back-stitched windows, satin door
HX0, HX1, HY0, HY1 = 64, 97, 52, 72                         # wall cells
s.cross(box(HX0, HY0, HX1, HY1), WALL)
roof = np.zeros((GH, GW), bool)
for r in range(14):
    roof[HY0 - 1 - r, HX0 - 4 + r:HX1 + 4 - r] = True
s.cross(roof, ROOF)
s.cross(box(92, 37, 96, 48) & ~roof, '#9a4a38')
s.cross(box(91, 36, 97, 37), '#7e3a2c')
for (px_, py_, pr) in [(98.5, 34, 1.2), (102.5, 31.8, 1.6), (107.5, 29.6, 2.0)]:        # puffs of smoke drifting away
    s.half(s.cells(s.circle(px_ * C, py_ * C, pr * C), 0.35), '#d6d9de')
for (wx0, wy0) in [(67, 56), (86, 56)]:
    s.cross(box(wx0, wy0, wx0 + 8, wy0 + 7), SKY)
    x0, y0, x1, y1 = wx0 * C, wy0 * C, (wx0 + 8) * C, (wy0 + 7) * C
    s.back([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], NAVY, smooth=False)
    s.back([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], NAVY, smooth=False)
    s.back([(x0, (y0 + y1) / 2 + 6), (x1, (y0 + y1) / 2 + 6)], NAVY, smooth=False)
    s.cross(box(wx0 - 1, wy0 + 7, wx0 + 9, wy0 + 8), BROWN)                     # window boxes
    for q in range(4):
        s.knot((wx0 + 0.8 + q * 2.2) * C, (wy0 + 7) * C - 2, [PINK, CORAL][q % 2])
door = s.rect(77 * C + 2, 61 * C, 84 * C - 2, HY1 * C) * (1 - (1 - s.circle(80.5 * C, 64.5 * C, 3.5 * C)) * (s.YY < 64.5 * C))
s.satin(door, RED, angle=1.45)
s.knot(82.6 * C, 67 * C, MUSTARD, r=4)
s.back([(HX0 * C, HY0 * C), (HX1 * C, HY0 * C), (HX1 * C, HY1 * C), (HX0 * C, HY1 * C), (HX0 * C, HY0 * C)], BROWN, smooth=False)
s.stage('cottage')

# ---- apple tree (left), pine (right), ground, path, flowers
TX0, TY0 = 38, 49
s.cross(box(TX0 - 1, TY0 + 6, TX0 + 2, 72), BROWN)
crown = s.cells(s.circle((TX0 + 0.5) * C, TY0 * C, 11.5 * C))
light = s.cells(s.circle((TX0 - 2.5) * C, (TY0 - 3) * C, 6 * C)) & crown         # the lit side in a lighter floss
s.cross(crown & ~light, GREEN)
s.cross(light, LTGREEN)
for (dx, dy) in [(-6, -4), (4, -6), (-2, 3), (6, 2), (-7, 4), (1, -1), (7, -2)]:
    s.knot((TX0 + 0.5 + dx) * C, (TY0 + dy) * C, RED, r=C * 0.5)
PX = 122
pine = np.zeros((GH, GW), bool)
for tier, (top, h, w) in enumerate([(40, 11, 9), (47, 11, 12), (54, 12, 15)]):
    for r in range(h):
        half_w = int(1 + (w - 1) * r / (h - 1))
        pine[top + r, PX - half_w:PX + half_w + 1] = True
s.cross(box(PX - 1, 66, PX + 2, 72), BROWN)
left = pine & (np.arange(GW)[None, :] < PX)
s.cross(pine & ~left, DKGREEN)
s.cross(left, GREEN)
ground = box(13, 72, GW - 13, 75)
path = np.zeros((GH, GW), bool)
for r in range(72, 77):
    w = 3 + (r - 72)
    path[r, 80 - w:81 + w] = True
s.cross(ground & ~path, GREEN)
s.cross(path, '#d9b98a')
s.half(box(13, 75, GW - 13, 77) & ~path, LTGREEN)
flowers = [(19, PINK), (26, MUSTARD), (49, CORAL), (56, PINK), (102, MUSTARD), (142, PINK), (147, CORAL)]
for (fx, col) in flowers:
    s.back([(fx * C + C / 2, 72 * C), (fx * C + C / 2 - 4, 68 * C), (fx * C + C / 2, 65 * C)], DKGREEN, step=1)
    s.chart(['.#.', '#o#', '.#.'], fx - 1, 62, {'#': col})
    s.knot(fx * C + C / 2, 63.5 * C, MUSTARD if col != MUSTARD else CORAL, r=C * 0.45)
    s.chart(['l.', '.l'], fx - 2, 67, {'l': LTGREEN})
s.stage('garden')

# ---- a woven label sewn on over the corner of the border
s.label(1540, 944, 1856, 1040, 'EST. 2026', size=34)

s.save(out, stages_dir=stages)
print('saved', out)
