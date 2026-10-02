"""Example (thermal camera / 热成像): 厨房里的温度 · Kitchen Heat Map — a kitchen at dinner time through a thermal
camera. A stock pot boils on the back burner and its steam rolls up into the cooker hood (its polished lid reads
cooler than it is); a kettle on the front burner shoots a jet of steam out of its spout; the oven is still warm and
leaks hot air along its top seal, a damp tea towel hangs cold on its handle; two loaves fresh from the oven steam on
a wire rack next to a cold butter dish. On the left the fridge door has been left open: a black-cold cave of
shelves, and its cold air pours down the freezer drawer and spreads across the floor in tongues. The cat went to the
fridge, walked through the cold puddle and back to the warm tiles in front of the oven -- its paw prints are still on
the floor, fading the older they are. The window is cold night glass. Spot meters, an area box, a line profile along
the paw trail (cold puddle -> warm tiles, one bump per print) and hottest / coldest markers read the temperatures off
the picture.
Draw-on stages: room -> fridge -> stove -> bread -> heat soak -> steam -> cat -> measurements. No image model.
python3 thermal_kitchen.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from thermal import Thermal
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'thermal_kitchen.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

# ---- one-point perspective: camera 1.6 m up, looking at the back wall 4.5 m away, pitched down (shifted VP)
F, VX, VY, EYE = 1750.0, 960.0, 100.0, 1.6


def P(X, Y, Z):
    return (VX + F * X / Z, VY + F * (EYE - Y) / Z)


def face(x0, x1, y0, y1, Z):
    """front face (constant depth Z) -> canvas quad"""
    return [P(x0, y1, Z), P(x1, y1, Z), P(x1, y0, Z), P(x0, y0, Z)]


def top(x0, x1, z0, z1, Y):
    """horizontal face at height Y between depths z0 (front) and z1 (back)"""
    return [P(x0, Y, z1), P(x1, Y, z1), P(x1, Y, z0), P(x0, Y, z0)]


def ell(X, Y, Z, rx, rz, n=40):
    """horizontal circle (radius rx across, rz in depth) at (X, Y, Z) -> canvas outline"""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return [P(X + rx * np.cos(t), Y, Z + rz * np.sin(t)) for t in a]


t = Thermal(1920, 1080, sensor=(480, 270), ss=2, seed=12, ambient=21.0)
# hand-set tone curve: the fridge black, the room deep violet, warm bodies red-orange, the stove yellow, flames white
t.camera(palette='iron', agc=0.22, plateau=2.0, netd=0.24, fpn=0.1, dde=1.6, pixel=0.4,
         curve=[(2, 0.0), (7, 0.05), (12, 0.11), (16, 0.17), (19, 0.23), (22, 0.29), (26, 0.43), (30, 0.59), (35, 0.71),
                (39, 0.78), (60, 0.82), (80, 0.86), (100, 0.91), (160, 1.0)])
WALL, ZC, ZF = 4.5, 3.9, 3.97                      # back wall, cabinet fronts, toe kick

# =========================================================== 0. the room at room temperature
t.room(top=24.5, bottom=20.0, y_top=0, y_bottom=900)
floor = t.poly([(0, P(0, 0, ZF)[1]), (1920, P(0, 0, ZF)[1]), (1920, 1080), (0, 1080)])
fy = P(0, 0, ZF)[1]
t.surface(floor, t.ramp((0, fy), 18.6, (0, 1080), 19.4), grain=0.25, grain_scale=60)
for Z in (3.3, 3.6, 3.9):                           # floor tiles: grout lines
    t.seam([P(-3, 0, Z), P(3, 0, Z)], -0.45, 2.5)
for X in np.arange(-2.1, 2.2, 0.3):
    t.seam([P(X, 0, ZF), P(X, 0, 3.2)], -0.45, 2.5)
# splashback tiles on the back wall between counter and wall cabinets
for Y in np.arange(0.92, 1.62, 0.075):
    t.seam([P(-1.3, Y, WALL), P(1.4, Y, WALL)], -0.22, 1.6)
for i, Y in enumerate(np.arange(0.92, 1.55, 0.075)):
    for X in np.arange(-1.3 + (0.075 if i % 2 else 0), 1.4, 0.15):
        t.seam([P(X, Y, WALL), P(X, Y + 0.075, WALL)], -0.22, 1.6)
# window (cold night glass, glass is opaque to long-wave IR so nothing outside shows)
wx0, wx1, wy0, wy1 = 1.40, 2.40, 1.02, 2.20
t.surface(t.poly(face(wx0 - 0.05, wx1 + 0.05, wy0 - 0.05, wy1 + 0.05, WALL)), 16.2, grain=0.2)
for (a, b) in ((wx0, 1.82), (1.88, wx1)):
    for (c, d) in ((wy0, 1.57), (1.63, wy1)):
        g = t.poly(face(a, b, c, d, WALL))
        t.surface(g, t.ramp(P(0, d, WALL), 12.6, P(0, c, WALL), 8.2), grain=0.25, grain_scale=40)
        t.surface(t.poly(face(a, a + 0.06, c, c + 0.08, WALL)) * g, 6.8, soft=4)   # cold corners at the spacer
        t.surface(t.poly(face(b - 0.06, b, c, c + 0.08, WALL)) * g, 6.8, soft=4)
t.surface(t.poly(top(wx0 - 0.08, wx1 + 0.1, 4.40, WALL, wy0 - 0.05)), 17.6)        # sill
# wall cabinets
ZU = 4.15
for (a, b, split) in ((-1.22, -0.45, -0.835), (0.45, 1.30, 0.875)):
    m = t.poly(face(a, b, 1.45, 2.6, ZU))
    t.surface(m, t.ramp((0, 0), 24.0, P(0, 1.45, ZU), 22.0), grain=0.25, grain_scale=30)
    t.seam([P(split, 1.45, ZU), P(split, 2.6, ZU)], -0.9, 3)
    for X in (a, b): t.seam([P(X, 1.45, ZU), P(X, 2.6, ZU)], -0.5, 3)
    t.seam([P(a, 1.45, ZU), P(b, 1.45, ZU)], -0.6, 3)
    for X in (split - 0.05, split + 0.05):
        t.surface(t.rect(P(X, 1.52, ZU)[0] - 4, P(X, 1.6, ZU)[1], P(X, 1.52, ZU)[0] + 4, P(X, 1.52, ZU)[1]), 19.5,
                  emissivity=0.4)                 # brushed-steel handles read cooler than the doors
# base cabinets: left run (sink side) and right run
for (a, b, splits) in ((-1.25, -0.40, (-0.83,)), (0.40, 2.4, (0.98, 1.56))):
    m = t.poly(face(a, b, 0.10, 0.88, ZC))
    t.surface(m, t.ramp(P(0, 0.88, ZC), 21.4, P(0, 0.1, ZC), 19.6), grain=0.25, grain_scale=30)
    t.surface(t.poly(face(a, b, 0.0, 0.10, ZF)), 18.2)                                    # toe kick shadow
    t.seam([P(a, 0.72, ZC), P(b, 0.72, ZC)], -0.9, 3)                                     # drawer line
    for X in (a,) + splits + (b,):
        t.seam([P(X, 0.1, ZC), P(X, 0.88, ZC)], -0.9, 3)
    for X0, X1 in zip((a,) + splits, splits + (b,)):
        cx = (X0 + X1) / 2
        hx, hy = P(cx, 0.80, ZC)
        t.surface(t.rect(hx - 26, hy - 3, hx + 26, hy + 3, r=3), 19.4, emissivity=0.4)
# the stone counter top and its front edge
t.surface(t.poly(top(-1.25, 2.4, 3.88, WALL, 0.92)), 20.2, grain=0.35, grain_scale=24)     # stone: thermal mass, runs cool
t.surface(t.poly(face(-1.25, 2.4, 0.88, 0.92, 3.88)), 19.4)
t.seam([P(-1.25, 0.92, 3.88), P(2.4, 0.92, 3.88)], 1.2, 2)
# the range body (cold until stage 2) and the hood
rng_front = t.poly(face(-0.40, 0.38, 0.0, 0.92, 3.88))
t.surface(rng_front, 21.0)
hood = t.poly([P(-0.42, 1.50, 4.0), P(0.38, 1.50, 4.0), P(0.26, 1.66, 4.15), P(-0.30, 1.66, 4.15)])
chim = t.poly(face(-0.14, 0.12, 1.64, 2.7, 4.4))
t.surface(chim, 24.0, emissivity=0.6)
t.surface(hood, 22.5, emissivity=0.6)
t.seam([P(-0.42, 1.50, 4.0), P(0.38, 1.50, 4.0)], -0.5, 3)
# outlet on the splashback
ox, oy = P(-1.05, 1.15, WALL)
t.surface(t.rect(ox - 18, oy - 26, ox + 18, oy + 26, r=3), 21.0)
t.statusbar(rec='00:04:51', date='2026-11-14', clock='18:42:07', battery=0.75, emissivity=0.96, mode='MAN', height=50, reflected=21)
t.scalebar(560, 1030, 1360, 1044, height=78)
t.stage('room')

# =========================================================== 1. the fridge, door left open
FZ = 3.80
fr_side = t.poly([P(-1.25, 1.85, FZ), P(-1.25, 1.85, WALL), P(-1.25, 0.92, WALL), P(-1.25, 0.92, 3.88),
                   P(-1.25, 0.0, ZC), P(-1.25, 0.0, FZ)])
t.surface(fr_side, 21.2)
t.surface(t.poly(face(-2.2, -1.25, 0.0, 1.85, FZ)), 20.6, grain=0.2)             # carcass front
# the open compartment: gasket frame (anti-sweat heater) then the cold inside
t.surface(t.poly(face(-2.2, -1.27, 0.64, 1.82, FZ)), 27.5)
op = t.poly(face(-2.2, -1.31, 0.68, 1.78, FZ))
back = t.poly(face(-2.2, -1.31, 0.70, 1.76, 4.42)) * op
t.surface(op, t.ramp(P(0, 1.78, FZ), 6.4, P(0, 0.68, FZ), 4.2))
t.surface(back, t.ramp(P(0, 1.76, 4.42), 4.0, P(0, 0.7, 4.42), 2.4), grain=0.2)
for Y in (0.98, 1.28, 1.55):                                                       # glass shelves
    t.surface(t.poly(top(-2.2, -1.31, 3.84, 4.42, Y)) * op, 6.0)
    t.surface(t.line([P(-2.2, Y, 3.84), P(-1.31, Y, 3.84)], 5) * op, 10.5)
t.surface(t.poly(face(-2.2, -1.31, 0.70, 0.95, 3.86)) * op, 7.5)                  # crisper drawers
t.seam([P(-1.75, 0.70, 3.86), P(-1.75, 0.95, 3.86)], 1.0, 3)
items = [  # (X, Y, Z, half width, height, temp): bottles, jars, a bowl, a carton
    (-1.50, 1.28, 4.15, 0.040, 0.24, 9.0), (-1.62, 1.28, 4.25, 0.035, 0.20, 8.2), (-1.95, 1.28, 4.2, 0.06, 0.12, 10.0),
    (-1.80, 0.98, 4.10, 0.09, 0.09, 9.5), (-1.45, 0.98, 4.20, 0.05, 0.16, 8.6), (-2.05, 1.55, 4.2, 0.05, 0.14, 9.0),
    (-1.60, 1.55, 4.2, 0.12, 0.08, 10.5)]
for X, Y, Z, hw, h, Tm in items:
    m = t.shape([P(X - hw, Y, Z), P(X - hw, Y + h * 0.75, Z), P(X - hw * 0.6, Y + h, Z), P(X + hw * 0.6, Y + h, Z),
                 P(X + hw, Y + h * 0.75, Z), P(X + hw, Y, Z)]) * op
    t.surface(m, Tm + 2.5, grain=0.4)
lx, ly = P(-2.1, 1.74, 4.3)
t.surface(t.ellipse(lx + 30, ly + 4, 20, 7), 27.0, soft=2)                          # the inside lamp
# freezer drawer (closed)
fd = t.poly(face(-2.2, -1.25, 0.06, 0.62, FZ))
t.surface(fd, t.ramp(P(0, 0.62, FZ), 19.6, P(0, 0.06, FZ), 18.8), grain=0.2)
t.seam([P(-2.2, 0.62, FZ), P(-1.25, 0.62, FZ)], -1.5, 4)
t.seam([P(-2.0, 0.56, FZ - 0.02), P(-1.45, 0.56, FZ - 0.02)], -1.0, 6)            # handle recess
# its cold air pours down the drawer front and spreads over the floor
t.plume([P(-1.75, 0.68, FZ - 0.01), P(-1.74, 0.45, FZ - 0.02), P(-1.71, 0.2, FZ - 0.03), P(-1.66, 0.02, 3.7)],
        5.0, w0=190, w1=250, opacity=0.8, cool=0.5, eddy=0.55, wisp=0.35, puffs=0.15, seed=5, fade_out=0.04)
for i, X in enumerate((-1.98, -1.55)):
    t.plume([P(X, 0.66, FZ - 0.01), P(X + 0.03, 0.4, FZ - 0.02), P(X + 0.06, 0.1, FZ - 0.03), P(X + 0.1, 0.01, 3.7)],
            4.0, w0=30, w1=70, opacity=0.7, cool=0.5, eddy=0.7, wisp=0.4, puffs=0.3, seed=6 + i, fade_out=0.05)
px_, py_ = P(-1.68, 0, 3.78)
t.pool(px_, py_, 6.5, reach=560, spread=(-15, 150), tongues=9, squash=0.36, width=0.22, soft=10, seed=8)
# a milk bottle and a glass of iced water on the counter
mx, my = P(-1.05, 0.92, 4.25); s = F / 4.25
milk = t.shape([(mx - 0.04 * s, my), (mx - 0.042 * s, my - 0.15 * s), (mx - 0.022 * s, my - 0.20 * s),
                (mx - 0.018 * s, my - 0.24 * s), (mx + 0.018 * s, my - 0.24 * s), (mx + 0.022 * s, my - 0.20 * s),
                (mx + 0.042 * s, my - 0.15 * s), (mx + 0.04 * s, my)])
t.surface(milk, t.ramp((0, my - 0.24 * s), 9.0, (0, my), 6.5))
gx, gy = P(-0.70, 0.92, 4.0); s = F / 4.0
glass = t.poly([(gx - 0.036 * s, gy - 0.125 * s), (gx + 0.036 * s, gy - 0.125 * s), (gx + 0.03 * s, gy), (gx - 0.03 * s, gy)])
t.soak(glass, 4.0, reach=10, strength=0.5, onto=t.poly(top(-1.25, -0.4, 3.88, WALL, 0.92)))
t.surface(glass, t.ramp((0, gy - 0.125 * s), 5.5, (0, gy), 2.2), grain=0.3)
t.surface(t.ellipse(gx, gy - 0.118 * s, 0.033 * s, 5), 1.0)                        # ice at the top
t.stage('fridge')

# =========================================================== 2. the stove: burners, a stock pot, a kettle, the oven
ZP, ZK = 4.28, 4.02
for X, Z in ((-0.2, ZP), (0.18, ZK)):                                             # lit burners
    t.surface(t.poly(ell(X, 0.93, Z, 0.11, 0.11)), 140.0, soft=2)
for X, Z in ((0.18, 4.3), (-0.2, 4.05)):                                           # cold burners
    t.seam([*ell(X, 0.93, Z, 0.09, 0.09), ell(X, 0.93, Z, 0.09, 0.09)[0]], 1.2, 3)
# stock pot: enamelled, hottest low where the flames lick it
px0, py0 = P(-0.2, 0.95, ZP - 0.16)                                                  # base, front
R = 0.175 * F / ZP
rim = P(-0.2, 0.95 + 0.20, ZP)[1]
for sx in (-1, 1):                                                                    # loop handles at the rim
    hx0 = px0 + sx * (R - 4)
    t.surface(t.line([(hx0, rim + 10), (hx0 + sx * 22, rim + 8), (hx0 + sx * 24, rim + 20), (hx0, rim + 24)], 7), 68.0)
pot = t.poly([(px0 - R, rim), (px0 - R, py0 - 6), (px0 - R + 6, py0), (px0 + R - 6, py0), (px0 + R, py0 - 6), (px0 + R, rim)])
t.surface(pot, t.ramp((0, py0), 104.0, (0, rim), 91.0, ease=0.6), grain=0.6, limb=6, limb_px=14)
t.seam([(px0 - R, rim + 6), (px0 + R, rim + 6)], -4.0, 3)                           # rolled rim
lid = t.poly(ell(-0.2, 1.16, ZP, 0.172, 0.172))
t.surface(lid, t.ramp((px0 - R, 0), 92.0, (px0 + R, 0), 99.0), emissivity=0.55, grain=0.5)   # polished lid: reads cooler
t.seam(ell(-0.2, 1.165, ZP, 0.15, 0.15) + [ell(-0.2, 1.165, ZP, 0.15, 0.15)[0]], -3.0, 2)
kx, ky = P(-0.2, 1.18, ZP)
t.surface(t.ellipse(kx, ky - 3, 15, 7), 52.0)                                       # bakelite knob, cooler
t.surface(t.poly(ell(-0.2, 0.95, ZP, 0.15, 0.06)) * (1 - pot), 260.0, soft=3)   # flame ring under the pot
# kettle on the front burner: a dome with the spout to the right and a handle over the top
qx, qy = P(0.18, 0.95, ZK - 0.10)
s = F / ZK
kettle = t.shape([(qx - 0.115 * s, qy - 6), (qx - 0.112 * s, qy - 0.07 * s), (qx - 0.08 * s, qy - 0.15 * s),
                  (qx - 0.03 * s, qy - 0.185 * s), (qx + 0.03 * s, qy - 0.185 * s), (qx + 0.08 * s, qy - 0.15 * s),
                  (qx + 0.112 * s, qy - 0.07 * s), (qx + 0.115 * s, qy - 6), (qx, qy + 2)], per=8)
spout = t.line([(qx + 0.09 * s, qy - 0.06 * s), (qx + 0.15 * s, qy - 0.11 * s), (qx + 0.19 * s, qy - 0.17 * s)], 0.026 * s)
t.surface(spout, t.ramp((qx + 0.09 * s, 0), 90.0, (qx + 0.19 * s, 0), 80.0))
t.surface(kettle, t.ramp((0, qy), 97.0, (0, qy - 0.185 * s), 86.0), grain=0.5, limb=8, limb_px=12)
handle = t.line([(qx - 0.07 * s, qy - 0.16 * s), (qx - 0.06 * s, qy - 0.25 * s), (qx + 0.06 * s, qy - 0.25 * s), (qx + 0.07 * s, qy - 0.16 * s)], 0.022 * s)
t.surface(handle * (1 - kettle), 41.0)
t.surface(t.ellipse(qx, qy - 0.19 * s, 0.022 * s, 0.012 * s), 62.0)
t.surface(t.poly(ell(0.18, 0.95, ZK, 0.13, 0.05)) * (1 - kettle), 240.0, soft=3)
# oven: control strip, door with its glass, handle, warming drawer; hot air leaks along the top seal
t.surface(t.poly(face(-0.40, 0.38, 0.80, 0.92, 3.88)), t.ramp(P(0, 0.92, 3.88), 25.0, P(0, 0.8, 3.88), 27.5), grain=0.4)
for X in (-0.3, -0.2, -0.1, 0.1, 0.2, 0.3):
    cx, cy = P(X, 0.86, 3.86)
    t.surface(t.ellipse(cx, cy, 10, 10), 22.5)
door = t.poly(face(-0.38, 0.36, 0.14, 0.78, 3.86))
t.surface(door, t.ramp(P(0, 0.78, 3.86), 26.5, P(0, 0.14, 3.86), 23.0), grain=0.5)
win = t.poly(face(-0.28, 0.26, 0.30, 0.66, 3.86))
t.surface(win, t.ramp(P(0, 0.66, 3.86), 31.5, P(0, 0.30, 3.86), 26.5), grain=0.6, soft=3)
t.surface(t.poly(face(-0.38, 0.36, 0.76, 0.79, 3.86)), 46.0, soft=2)               # leaking top seal
hy = P(0, 0.72, 3.80)[1]
t.surface(t.rect(P(-0.32, 0, 3.8)[0], hy - 6, P(0.30, 0, 3.8)[0], hy + 6, r=6), 26.0, emissivity=0.7)
t.surface(t.poly(face(-0.38, 0.36, 0.02, 0.12, 3.86)), 23.0)
# a damp tea towel over the handle: evaporation keeps it below room temperature
tw0, tw1 = P(0.10, 0, 3.79)[0], P(0.24, 0, 3.79)[0]
towel = t.shape([(tw0, hy - 8), (tw1, hy - 9), (tw1 + 4, hy + 60), (tw1 + 8, hy + 150), (tw1 - 10, hy + 158),
                 ((tw0 + tw1) / 2, hy + 150), (tw0 + 6, hy + 156), (tw0 - 8, hy + 148), (tw0 - 4, hy + 60)], per=8)
t.surface(towel, t.ramp((0, hy), 20.0, (0, hy + 150), 17.5), grain=0.6, grain_scale=8)
t.seam([((tw0 + tw1) / 2 + 4, hy + 4), ((tw0 + tw1) / 2 + 10, hy + 150)], -1.2, 3)
t.stage('stove')

# =========================================================== 3. bread on a wire rack, cold butter
ZB = 4.2
t.surface(t.poly(top(0.50, 1.20, 4.05, 4.36, 0.955)), 38.0, soft=1)               # rack (wire, warm)
for X in np.arange(0.52, 1.2, 0.045):
    t.seam([P(X, 0.955, 4.05), P(X, 0.955, 4.36)], 4.0, 2)
bx, by = P(0.68, 0.96, ZB); s = F / ZB
boule = t.shape([(bx - 0.14 * s, by), (bx - 0.135 * s, by - 0.05 * s), (bx - 0.09 * s, by - 0.11 * s),
                 (bx, by - 0.13 * s), (bx + 0.09 * s, by - 0.11 * s), (bx + 0.135 * s, by - 0.05 * s), (bx + 0.14 * s, by)])
t.surface(boule, t.radial(bx, by - 0.07 * s, 0.14 * s, 0.07 * s, 82.0, 63.0), grain=1.5, grain_scale=10, soft=1, limb=8, limb_px=14)
for k in (-1, 0, 1):                                                               # scoring: thin crust, hotter
    t.seam([(bx - 0.07 * s + k * 0.03 * s, by - 0.09 * s + abs(k) * 0.01 * s),
            (bx + 0.06 * s + k * 0.03 * s, by - 0.105 * s + abs(k) * 0.01 * s)], 9.0, 4)
cx, cy = P(1.02, 0.96, ZB)
batard = t.shape([(cx - 0.16 * s, cy), (cx - 0.15 * s, cy - 0.05 * s), (cx - 0.08 * s, cy - 0.085 * s),
                  (cx + 0.08 * s, cy - 0.085 * s), (cx + 0.15 * s, cy - 0.05 * s), (cx + 0.16 * s, cy)])
t.surface(batard, t.radial(cx, cy - 0.045 * s, 0.16 * s, 0.05 * s, 78.0, 58.0), grain=1.5, grain_scale=10, soft=1, limb=8, limb_px=12)
for k in range(3):
    x = cx - 0.09 * s + k * 0.08 * s
    t.seam([(x - 0.03 * s, cy - 0.06 * s), (x + 0.03 * s, cy - 0.075 * s)], 8.0, 4)
dx, dy = P(1.40, 0.92, 4.08); s2 = F / 4.08
t.surface(t.poly([(dx - 0.09 * s2, dy), (dx + 0.09 * s2, dy), (dx + 0.08 * s2, dy - 0.02 * s2), (dx - 0.08 * s2, dy - 0.02 * s2)]), 12.0)
t.surface(t.rect(dx - 0.055 * s2, dy - 0.055 * s2, dx + 0.055 * s2, dy - 0.02 * s2, r=3), t.ramp((0, dy - 0.055 * s2), 10.0, (0, dy), 7.5))
# a herb pot on the sill: leaves run cooler than the room (they evaporate water)
hx, hy = P(1.72, 0.92, 4.32); s3 = F / 4.32
t.surface(t.poly([(hx - 0.06 * s3, hy - 0.11 * s3), (hx + 0.06 * s3, hy - 0.11 * s3), (hx + 0.045 * s3, hy), (hx - 0.045 * s3, hy)]), 19.0)
for i in range(16):
    a = np.radians(-150 + i * 8 + (i % 3) * 5)
    L = (0.12 + 0.09 * ((i * 7) % 5) / 4) * s3
    ex, ey = hx + np.cos(a) * L * 0.8, hy - 0.11 * s3 + np.sin(a) * L
    t.surface(t.ellipse(ex, ey, 9, 5, np.degrees(a)), 16.5, soft=1)
    t.surface(t.line([(hx, hy - 0.11 * s3), (ex, ey)], 2.5), 17.0)
t.stage('bread')

# =========================================================== 4. heat soaks into what is around it
behind = t.poly([P(-0.30, 0.93, WALL), P(0.28, 0.93, WALL), P(0.22, 1.40, WALL), P(-0.24, 1.40, WALL)])
occ = np.clip(pot + lid + kettle + handle + spout + hood + chim, 0, 1)
t.soak(behind, 60.0, reach=38, strength=0.4, onto=(1 - occ) * t.poly([P(-1.25, 0.92, WALL), P(1.4, 0.92, WALL), P(1.4, 1.50, WALL), P(-1.25, 1.50, WALL)]))
t.surface(hood, t.ramp((0, P(0, 1.50, 4.0)[1]), 38.0, (0, P(0, 1.66, 4.15)[1]), 28.0), emissivity=0.8, grain=0.4)
t.surface(chim, t.ramp((0, P(0, 1.66, 4.4)[1]), 25.0, (0, 0), 23.5), emissivity=0.8)
t.seam([P(-0.42, 1.50, 4.0), P(0.38, 1.50, 4.0)], 3.0, 3)
# the cabinets either side of the range and the counter round the hob warm up
oven_face = t.poly(face(-0.40, 0.38, 0.0, 0.92, 3.88))
t.soak(oven_face, 28.0, reach=20, strength=0.35, onto=t.poly(face(-1.25, 2.4, 0.0, 0.92, ZC)) * (1 - oven_face))
t.soak(t.poly(top(-0.40, 0.38, 3.9, WALL, 0.92)), 70.0, reach=22, strength=0.35, onto=t.poly(top(-1.25, 2.4, 3.88, WALL, 0.92)) * (1 - occ - oven_face).clip(0, 1))
# under the bread rack the counter is warm
t.soak(t.poly(top(0.50, 1.20, 4.05, 4.36, 0.93)), 60.0, reach=10, strength=0.6, onto=t.poly(top(0.4, 1.3, 3.88, WALL, 0.92)) * (1 - boule - batard).clip(0, 1))
# the warm patch on the tiles in front of the oven (it radiates onto the floor)
t.warm(floor * t.radial(*P(0.15, 0, 3.5), 420, 90, 1.0, 0.0, power=1.4), 5.5)
# glazed tiles mirror the oven door, faintly
t.reflect(floor * t.ramp(P(-1.2, 0, 3.9), 0.0, P(-0.5, 0, 3.9), 1.0), P(0, 0, ZF)[1], strength=0.22, blur_px=10, fade=70)
t.stage('soak')

# =========================================================== 5. steam and rising air
hood_y = P(0, 1.50, 4.0)[1]
lid_y = P(-0.2, 1.16, ZP)[1]
t.plume([(px0 + R * 0.55, lid_y + 2), (px0 + R * 0.6, lid_y - 40), (px0 + R * 0.3, lid_y - 90), (px0 + R * 0.45, lid_y - 130), (px0 + R * 0.2, hood_y + 4)],
        99.0, w0=12, w1=70, opacity=0.95, cool=1.1, eddy=0.85, wisp=0.55, puffs=0.35, seed=21, fade_out=0.04)
t.plume([(px0 - R * 0.35, lid_y + 4), (px0 - R * 0.5, lid_y - 50), (px0 - R * 0.2, lid_y - 110), (px0 - R * 0.35, hood_y + 4)],
        97.0, w0=7, w1=48, opacity=0.8, cool=1.3, eddy=0.85, wisp=0.6, puffs=0.4, seed=22, fade_out=0.04)
# the steam hits the hood and runs along under its lip; some spills out over the front edge
t.plume([(px0 + R * 0.25, hood_y + 6), (px0 - 60, hood_y + 10), (px0 - 160, hood_y + 4)], 62.0, w0=16, w1=24, opacity=0.7, cool=0.8, eddy=0.6, seed=23)
t.plume([(px0 + R * 0.25, hood_y + 6), (px0 + 130, hood_y + 10), (px0 + 250, hood_y + 2)], 60.0, w0=16, w1=24, opacity=0.7, cool=0.8, eddy=0.6, seed=24)
t.plume(t.rise(P(0.36, 1.50, 4.0)[0] - 10, hood_y - 4, 120, sway=22, lean=0.12, seed=25), 40.0, w0=14, w1=60, opacity=0.3, cool=1.4, eddy=0.9, seed=25)
# the kettle's jet: fast and narrow out of the spout, then it turns upward and billows under the wall cabinet
sx, sy = qx + 0.19 * F / ZK, qy - 0.17 * F / ZK
cab_y = P(0, 1.45, ZU)[1]
t.plume([(sx + 2, sy - 2), (sx + 30, sy - 26), (sx + 52, sy - 58), (sx + 62, sy - 100), (sx + 80, cab_y + 30), (sx + 110, cab_y + 8)],
        100.0, w0=5, w1=58, opacity=0.95, cool=1.2, eddy=0.85, wisp=0.5, puffs=0.3, seed=31, fade_out=0.06)
t.plume([(sx + 100, cab_y + 10), (sx + 180, cab_y + 14), (sx + 260, cab_y + 8)], 50.0, w0=20, w1=26, opacity=0.6, cool=0.9, eddy=0.7, seed=32)
# bread breathes a soft warm haze; the oven's top seal sends a sheet of hot air up the controls
t.plume(t.rise(bx, by - 0.13 * s, 150, sway=18, lean=-0.05, seed=41), 44.0, w0=40, w1=90, opacity=0.45, cool=1.2, eddy=0.9, seed=41)
t.plume(t.rise(cx, cy - 0.085 * s, 140, sway=16, lean=0.08, seed=42), 42.0, w0=50, w1=90, opacity=0.4, cool=1.2, eddy=0.9, seed=42)
t.plume([P(-0.02, 0.79, 3.84), P(-0.02, 0.86, 3.84), P(-0.02, 0.93, 3.88)], 45.0, w0=150, w1=170, opacity=0.35, cool=0.6, eddy=0.7, seed=43)
# the window drops a sheet of cold air onto the counter
t.plume([P(1.9, 1.0, 4.42), P(1.9, 0.94, 4.35), P(1.9, 0.92, 4.1)], 13.0, w0=150, w1=180, opacity=0.5, cool=0.6, eddy=0.4, seed=51)
t.stage('steam')

# =========================================================== 6. the cat, and how it got there
CX, CZ = 0.62, 3.22
cfx, cfy = P(CX, 0, CZ); u = 0.37 * F / CZ                  # canvas px per cat-height


def C(a, b):
    """cat coordinates: a to the right (towards the tail), b up, in cat heights; it faces left, to the oven"""
    return (cfx + a * u, cfy - b * u)


body = t.shape([C(-0.20, 0.62), C(-0.25, 0.42), C(-0.24, 0.12), C(-0.22, 0.0), C(0.05, 0.0), C(0.30, 0.0),
                C(0.38, 0.12), C(0.36, 0.32), C(0.24, 0.54), C(0.08, 0.70), C(-0.08, 0.72)], per=12)
head = t.shape([C(-0.36, 0.80), C(-0.33, 0.70), C(-0.24, 0.64), C(-0.10, 0.66), C(0.01, 0.76), C(0.0, 0.88),
                C(-0.06, 0.95), C(-0.20, 0.97), C(-0.32, 0.90)], per=10)
ear_far = t.poly([C(-0.27, 0.93), C(-0.30, 1.08), C(-0.17, 0.97)])
ear_near = t.poly([C(-0.13, 0.95), C(-0.06, 1.10), C(0.0, 0.90)])
ear_in = t.poly([C(-0.115, 0.955), C(-0.065, 1.06), C(-0.025, 0.925)])
legs = t.shape([C(-0.23, 0.36), C(-0.10, 0.36), C(-0.09, 0.03), C(-0.04, 0.0), C(-0.26, 0.0), C(-0.24, 0.05)], per=6)
haunch = t.ellipse(*C(0.18, 0.20), 0.17 * u, 0.20 * u, rot=-10)
tail_pts = [C(0.33, 0.04), C(0.30, -0.03), C(0.12, -0.06), C(-0.08, -0.06), C(-0.26, -0.035), C(-0.34, 0.02)]
tail = t.line(spline(tail_pts, 8), 0.075 * u)
cat_all = np.clip(body + head + ear_far + ear_near + legs + haunch + tail, 0, 1)
# paw prints first (they lie under the cat): from the cold puddle by the fridge to the warm tiles
steps = []                                          # (x, y, heading, scale, age)
path = np.array([(-1.62, 3.50), (-1.2, 3.40), (-0.7, 3.32), (-0.2, 3.28), (0.15, 3.24), (0.42, 3.22)])
dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(path, axis=0).T))])
n_steps = 18
for i in range(n_steps):
    dd = dist[-1] * i / (n_steps - 1)
    X = np.interp(dd, dist, path[:, 0]); Z = np.interp(dd, dist, path[:, 1])
    Z += 0.035 * (1 if i % 2 else -1)
    xx, yy = P(X, 0, Z)
    age = 0.88 * (1 - i / (n_steps - 1)) ** 0.85 + 0.04
    steps.append((xx, yy, 0, F / Z / 560, age))
t.prints(steps, 33.0, size=32, squash=0.42, spread=0.8)
# the cat: fur insulates, so the coat reads well below body temperature; where the fur is thin (face, inner ear,
# chest, armpit) it runs warmer, the flank facing the oven is warmer, and every rounded edge cools towards the outline
t.surface(tail, t.ramp(C(0.33, 0), 29.5, C(-0.34, 0), 25.0), fuzz=0.5, fuzz_scale=3, limb=1.5, limb_px=5)
t.surface(body, t.ramp(C(-0.25, 0.3), 33.6, C(0.36, 0.55), 28.0), fuzz=0.6, fuzz_scale=4, grain=0.5, grain_scale=7,
          limb=3.0, limb_px=16)
t.surface(haunch, t.ramp(C(-0.05, 0.12), 32.0, C(0.36, 0.32), 27.6), fuzz=0.6, fuzz_scale=4, grain=0.5, grain_scale=7,
          limb=1.2, limb_px=10)
t.seam([C(0.02, 0.05), C(0.05, 0.2), C(0.14, 0.34), C(0.30, 0.38)], -1.6, 4)         # where the haunch folds
t.warm(t.ellipse(*C(-0.17, 0.47), 0.06 * u, 0.15 * u) * body, 1.4)    # thin fur on the chest
t.surface(legs, t.ramp(C(0, 0.3), 31.5, C(0, 0.0), 27.5), fuzz=0.5, fuzz_scale=3, limb=1.5, limb_px=6)
t.seam([C(-0.165, 0.30), C(-0.16, 0.02)], -1.6, 3)
t.surface(ear_far, 27.5, fuzz=0.3, fuzz_scale=2)
t.surface(head, t.ramp(C(-0.34, 0.8), 35.0, C(0.0, 0.85), 31.5), fuzz=0.45, fuzz_scale=3, grain=0.3, grain_scale=6,
          limb=2.0, limb_px=10)
t.surface(ear_near, 28.5, fuzz=0.3, fuzz_scale=2)
t.surface(ear_in, 34.5, soft=1)
t.surface(t.ellipse(*C(-0.215, 0.84), 0.036 * u, 0.028 * u), 38.6, soft=1)        # eye: the hottest spot
t.surface(t.ellipse(*C(-0.355, 0.78), 0.024 * u, 0.02 * u), 26.0, soft=1)          # cold nose
t.surface(t.ellipse(*C(-0.29, 0.69), 0.05 * u, 0.025 * u), 35.5, soft=1)           # mouth corner
t.reflect(floor * (1 - cat_all) * t.radial(cfx, cfy, 1.2 * u, 0.6 * u, 1.0, 0.0), cfy, strength=0.3, blur_px=6, fade=50)
t.stage('cat')

# =========================================================== 7. measurements
t.spot(px0 - R * 0.35, (rim + py0) / 2 + 6, 'Sp1', name='pot')
t.spot(*P(-1.72, 1.13, 4.42), 'Sp2', name='fridge', side='ne')
t.spot(*C(-0.12, 0.45), 'Sp3', name='cat', side='ne', r=11)
t.box(bx - 0.15 * F / ZB, by - 0.15 * F / ZB, cx + 0.17 * F / ZB, by + 6, 'Bx1', name='bread')
p_a, p_b = P(-1.65, 0, 3.47), P(0.40, 0, 3.22)
t.profile(p_a, p_b, inset=(1500, 452, 390, 170), label='L1', name='floor')
t.hottest()
t.coldest()
t.results(1550, 66, width=350)
t.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s')
