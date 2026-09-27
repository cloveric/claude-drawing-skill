"""Example (stop-motion clay): Lighthouse Island / 灯塔岛 — a plasticine relief: finger-smeared sky,
pillowy clouds, a striped lighthouse and cottage on a little island, a smiling whale spouting water,
a sailboat, rolled-coil waves. Everything is a height map lit like a photo of a set. No image model.
python3 clay_lighthouse.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from clay import Clay, hexc
from core import spline, fbm1d, noise2d, smoothstep

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'clay_lighthouse.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

c = Clay(1920, 1080, seed=11)
rng = c.rng
W, H = c.W, c.H
HORIZON = 600
NAVY, RED, CREAM, FOAM = '#2f3b63', '#d8453a', '#fbfaf5', '#eef8fb'

# ---- sky: bands of blue, pale blue and warm cream, then smeared together with fingertips
c.backdrop('#cfe6ee')
sky_col = c.gradient('#5fa8d8', '#f6e3bd', 0, HORIZON)
bands = noise2d(H, W, 260, 3, 3)[..., None]
hi = smoothstep(0.56, 0.72, bands) * 0.4                     # soft patches of pale blue ...
sky_col = sky_col * (1 - hi) + hexc('#a6d4ee') * hi
low = smoothstep(0.44, 0.3, bands) * smoothstep(HORIZON - 260, HORIZON - 120, c.YY)[..., None] * 0.35
sky_col = sky_col * (1 - low) + hexc('#f7cfb8') * low        # ... and peach near the horizon, for the fingers to drag around
sky = c.rrect(-40, -40, W + 40, HORIZON + 30, 10)
c.smear(sky, sky_col, strokes=340, angle=0.08, spread=0.3, height=4)
SX, SY = 1640, 180
for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
    c.snake([(SX + np.cos(a) * 106, SY + np.sin(a) * 106), (SX + np.cos(a) * 150, SY + np.sin(a) * 150)], 9, '#f7b33b', taper=(1.0, 0.6))
c.pad(c.circle(SX, SY, 86), '#fbc94a', height=22, round=18)
c.groove(spline([(SX - 40, SY + 18), (SX, SY + 44), (SX + 40, SY + 18)]), 7, 4)        # sleepy sun smile
for sx in (-1, 1):
    c.groove(spline([(SX + sx * 36 - 16, SY - 14), (SX + sx * 36, SY - 24), (SX + sx * 36 + 16, SY - 14)]), 6, 3)
    c.pad(c.circle(SX + sx * 56, SY + 18, 13), '#f59a72', height=2, round=4)


def cloud(cx, cy, w, h, n):
    m = np.zeros((H, W), np.float32)
    for i in range(n):
        x = cx - w / 2 + w * (i + 0.5) / n
        r = h * (0.5 + 0.45 * np.sin(np.pi * (i + 0.5) / n)) * rng.uniform(0.85, 1.1)
        m = np.maximum(m, c.circle(x, cy + h * 0.3 - r * 0.7, r))
    m = np.maximum(m, c.rrect(cx - w / 2, cy - h * 0.1, cx + w / 2, cy + h * 0.32, h * 0.2))
    c.pad(m, CREAM, height=26, round=16)


cloud(930, 150, 320, 116, 4)
cloud(1290, 330, 220, 82, 3)
cloud(150, 330, 190, 74, 3)
for (bx, by, s) in [(620, 300, 1.0), (690, 266, 0.8), (560, 250, 0.7)]:
    c.snake([(bx - 30 * s, by + 4 * s), (bx - 15 * s, by - 12 * s), (bx, by)], 4.2 * s, CREAM, taper=(0.6, 1))
    c.snake([(bx, by), (bx + 15 * s, by - 12 * s), (bx + 30 * s, by + 4 * s)], 4.2 * s, CREAM, taper=(1, 0.6))
c.stage('sky')

# ---- sea: a deep slab, lighter towards the horizon, tool-grooved ripples
sea = c.rrect(-40, HORIZON - 6, W + 40, H + 40, 8)
c.pad(sea, c.gradient('#7cc3d6', '#2c6f98', HORIZON, H), height=12, round=4)
for k in range(12):
    y = HORIZON + 26 + k ** 1.5 * 9
    for _ in range(3 + k // 3):
        x = rng.uniform(40, W - 200); L = rng.uniform(80, 200) * (0.6 + k / 16)
        c.groove([(x, y + rng.normal(0, 4)), (x + L / 2, y - 3), (x + L, y + rng.normal(0, 4))], 3 + k * 0.3, 1.6)
c.stage('sea')

# ---- island: sandy base, grassy hill, rocks, lighthouse, cottage, tree
IX = 470
c.pad(c.blob(IX, HORIZON + 58, 330, 62, rough=0.05), '#e8cf99', height=20, round=10)
c.pad(c.blob(IX - 20, HORIZON + 22, 270, 70, rough=0.06), '#7db65a', height=24, round=18, marble=('#9ccd6c', 0.25))
for (x, y, r) in [(210, HORIZON + 70, 30), (250, HORIZON + 84, 20), (736, HORIZON + 76, 26), (700, HORIZON + 90, 16)]:
    c.pad(c.blob(x, y, r, r * 0.75, rough=0.12), '#9aa1a8', height=r * 0.7, round=r * 0.5)

LX, LB, LT = 400, HORIZON + 10, 250                           # lighthouse: centre x, base y, top y


def lh_x(y, side):                                            # tapered tower edge
    t = (LB - y) / (LB - LT)
    return LX + side * (62 - 22 * t)


tower = c.poly([(lh_x(LB, -1), LB), (lh_x(LB, 1), LB), (lh_x(LT, 1), LT), (lh_x(LT, -1), LT)])
c.pad(tower, '#f5efe4', height=40, round=16)
for (y0, y1) in [(LB - 70, LB - 20), (LB - 180, LB - 130), (LB - 290, LB - 240)]:
    band = c.poly([(lh_x(y1, -1) - 3, y1), (lh_x(y1, 1) + 3, y1), (lh_x(y0, 1) + 3, y0), (lh_x(y0, -1) - 3, y0)])
    c.pad(band, RED, height=4, round=3)
c.pad(c.rrect(LX - 20, LB - 64, LX + 20, LB + 2, 18), NAVY, height=5, round=4)       # door
c.pad(c.circle(LX, LB - 205, 13), NAVY, height=4, round=3)                           # little window
c.pad(c.rrect(LX - 66, LT - 16, LX + 66, LT + 6, 8), NAVY, height=12, round=4)       # gallery
c.pad(c.rrect(LX - 38, LT - 84, LX + 38, LT - 14, 6), '#ffd45e', height=14, round=6) # lamp room
for dx in (-13, 13):
    c.snake([(LX + dx, LT - 82), (LX + dx, LT - 16)], 3, NAVY, smooth=False)
c.snake([(LX - 64, LT - 38), (LX + 64, LT - 38)], 3.2, NAVY, smooth=False)          # rail
for dx in (-58, -30, 30, 58):
    c.snake([(LX + dx, LT - 38), (LX + dx, LT - 14)], 2.6, NAVY, smooth=False)
c.pad(c.poly([(LX - 54, LT - 80), (LX + 54, LT - 80), (LX, LT - 142)]), RED, height=20, round=10)
c.ball(LX, LT - 146, 10, NAVY)
for side in (-1, 1):                                          # the lamp's shine, pressed as little rays
    for a in (-0.32, 0.0, 0.32):
        x0, y0 = LX + side * 60, LT - 50 + a * 50
        c.snake([(x0, y0), (x0 + side * 46, y0 + a * 80)], 4.5, '#ffe28a', taper=(1, 0.45))

HX = 590                                                      # cottage
c.pad(c.rrect(HX - 62, HORIZON - 50, HX + 62, HORIZON + 34, 6), '#f3e7d2', height=26, round=8)
c.pad(c.poly([(HX - 78, HORIZON - 44), (HX + 78, HORIZON - 44), (HX, HORIZON - 116)]), '#3f6fb0', height=18, round=8)
c.pad(c.rrect(HX + 12, HORIZON - 14, HX + 42, HORIZON + 34, 12), '#8a5a3c', height=4, round=3)
c.pad(c.rrect(HX - 44, HORIZON - 22, HX - 12, HORIZON + 6, 4), '#ffd45e', height=4, round=3)
c.snake([(HX - 28, HORIZON - 22), (HX - 28, HORIZON + 6)], 2.4, '#8a5a3c', smooth=False)
c.snake([(HX - 44, HORIZON - 8), (HX - 12, HORIZON - 8)], 2.4, '#8a5a3c', smooth=False)
c.snake([(220, HORIZON + 30), (226, HORIZON - 40)], 9, '#8a5a3c', taper=(1.1, 0.8))  # tree
tree = np.maximum.reduce([c.circle(226, HORIZON - 96, 58), c.circle(190, HORIZON - 66, 40), c.circle(262, HORIZON - 64, 44)])
c.pad(tree, '#4f9a4e', height=30, round=22, marble=('#6db55e', 0.2))
for (x, y) in [(200, HORIZON - 110), (248, HORIZON - 84), (214, HORIZON - 58)]:
    c.ball(x, y, 7, '#e2503f')
c.stage('island')

# ---- whale: big round head, body tapering right into the water, pale grooved throat, eye, smile, spout
WX, WY = 1150, 700
WATER = 772                                                   # the front water line
body = c.poly(spline([(WX - 300, WY + 40), (WX - 296, WY - 60), (WX - 230, WY - 150), (WX - 110, WY - 190), (WX + 40, WY - 176),
                      (WX + 180, WY - 120), (WX + 300, WY - 50), (WX + 380, WY + 10), (WX + 360, WY + 60), (WX - 300, WY + 60)], 16))
c.pad(body, '#4a7fc1', height=62, round=50)
throat = c.poly(spline([(WX - 300, WY + 2), (WX - 200, WY + 12), (WX - 60, WY + 22), (WX + 90, WY + 50), (WX + 90, WY + 90), (WX - 300, WY + 90)], 12))
c.pad(throat * (body > 0.5), '#d7e8f2', height=5, round=6)
for k in range(3):
    y0 = WY + 30 + k * 15
    c.groove([(WX - 262, y0 - 4), (WX - 120, y0 + 4), (WX + 50, y0 + 22)], 3.5, 2.2)
c.ball(WX - 170, WY - 76, 19, CREAM)
c.ball(WX - 167, WY - 73, 11, '#232838')
c.ball(WX - 172, WY - 79, 4, '#ffffff')
c.groove(spline([(WX - 290, WY - 20), (WX - 230, WY - 4), (WX - 150, WY - 16)]), 6, 5)
c.pad(c.ellipse(WX - 214, WY - 38, 20, 12), '#f29aa3', height=3, round=4)
c.pad(c.poly(spline([(WX - 30, WY + 6), (WX + 20, WY + 54), (WX + 96, WY + 76), (WX + 60, WY + 20)], 8)), '#3d6daa', height=16, round=10)
for dx in (-60, -20, 20, 60):                                 # pale spots on the back
    c.pad(c.circle(WX + dx, WY - 150 + abs(dx) * 0.35, 8), '#6d9ad0', height=2, round=3)
SPX, SPY = WX - 120, WY - 190                                  # spout: three curling plumes and droplets
for side, reach in [(-1, 1.0), (0, 0.0), (1, 1.0)]:
    pts = [(SPX, SPY), (SPX + side * 16, SPY - 80), (SPX + side * 70 * reach, SPY - 140 - (1 - reach) * 40), (SPX + side * 118 * reach, SPY - 118 - (1 - reach) * 50)]
    c.snake(pts, 13, '#e3f2fa', taper=(1.2, 0.6))
for (x, y, r) in [(SPX - 132, SPY - 92, 9), (SPX + 136, SPY - 94, 8), (SPX - 70, SPY - 176, 7), (SPX + 64, SPY - 182, 7), (SPX, SPY - 214, 9), (SPX - 158, SPY - 56, 6), (SPX + 160, SPY - 60, 6)]:
    c.ball(x, y, r, '#e3f2fa')
FX, FY = 1660, 690                                            # tail fluke rising further out
c.snake([(FX - 56, WATER - 6), (FX - 20, FY + 40), (FX, FY - 6)], 26, '#4a7fc1', taper=(1.3, 0.6))
fluke = c.poly(spline([(FX, FY + 18), (FX - 56, FY - 4), (FX - 112, FY - 40), (FX - 156, FY - 80), (FX - 96, FY - 58), (FX - 36, FY - 40),
                       (FX, FY - 26), (FX + 36, FY - 40), (FX + 96, FY - 60), (FX + 152, FY - 86), (FX + 110, FY - 42), (FX + 56, FY - 6), (FX, FY + 18)], 6))
c.pad(fluke, '#4a7fc1', height=28, round=14)
c.stage('whale')

# ---- water in front: a wavy slab over the whale's lower half, irregular curling wave coils, foam, a sailboat
wob = fbm1d(90, 12, 3, 5)
xs = np.linspace(-40, W + 40, 90)
front_top = [(x, WATER + 12 * np.sin(x / 64) + 10 * wob[i]) for i, x in enumerate(xs)]
front = c.poly(front_top + [(W + 40, H + 40), (-40, H + 40)])
c.pad(front, c.gradient('#4f9cc0', '#2a6690', WATER, H), height=14, round=6)


def wave(x, y, L, r, col):
    """one rolled coil: a long low crest that curls over at the front"""
    curl = [(x, y + 6), (x + L * 0.3, y - L * 0.08), (x + L * 0.62, y - L * 0.14), (x + L * 0.84, y - L * 0.07),
            (x + L * 0.84, y + L * 0.02), (x + L * 0.74, y + L * 0.03), (x + L * 0.72, y - L * 0.03)]
    c.snake(curl, r, col, taper=(0.35, 1.0))


for (x, y) in [(xs[i], front_top[i][1]) for i in range(2, 88, 7)]:                  # small crests along the top edge
    wave(x - 30, y + 6, rng.uniform(90, 130), 5.5, '#8fd0e0')
rows = [(WATER + 110, 170, 7.5), (WATER + 200, 210, 9), (WATER + 290, 250, 10.5)]
for (y, L0, r) in rows:
    x = -rng.uniform(40, 160)
    while x < W + 40:
        L = L0 * rng.uniform(0.75, 1.3)
        yy = y + rng.normal(0, 10)
        wave(x, yy, L, r * rng.uniform(0.85, 1.1), '#8fd0e0' if rng.random() < 0.75 else '#a9dde8')
        if rng.random() < 0.7:
            c.ball(x + L * 0.78, yy - L * 0.02, r * 0.7, FOAM)
        x += L * rng.uniform(1.1, 1.8)
for k in range(34):                                           # foam at the whale's and the tail's waterline
    x = rng.uniform(WX - 300, WX + 380) if k < 24 else rng.uniform(FX - 110, FX + 20)
    c.ball(x, WATER + 6 + 12 * np.sin(x / 64) + rng.normal(0, 4), rng.uniform(4, 8), FOAM)
BX, BY = 640, 900                                             # sailboat in the foreground
c.pad(c.poly(spline([(BX - 120, BY - 34), (BX + 130, BY - 34), (BX + 86, BY + 22), (BX - 86, BY + 22)], 4)), '#e2503f', height=22, round=10)
c.snake([(BX - 108, BY - 14), (BX + 118, BY - 14)], 3.4, CREAM, smooth=False)
c.snake([(BX - 6, BY - 34), (BX - 6, BY - 250)], 5.5, '#8a5a3c', smooth=False)
c.pad(c.poly([(BX + 6, BY - 240), (BX + 6, BY - 50), (BX + 132, BY - 50)]), CREAM, height=12, round=8)
c.pad(c.poly([(BX - 18, BY - 210), (BX - 18, BY - 56), (BX - 104, BY - 56)]), '#f2d27a', height=10, round=7)
c.pad(c.poly([(BX - 4, BY - 252), (BX - 4, BY - 226), (BX + 36, BY - 239)]), '#3f6fb0', height=6, round=3)
for dx in (-64, 0, 64):
    c.poke(BX + dx, BY + 2, 6, 3)
wave(BX - 190, BY + 30, 150, 8, '#a9dde8')
wave(BX + 110, BY + 36, 130, 7, '#a9dde8')

c.save(out, stages_dir=stages)
print('saved', out)
