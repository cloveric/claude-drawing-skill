"""Example (golden-age comic cover / 黄金时代漫画): 火箭小队 · Rocket Squad No. 3 -- a newsstand comic cover of about
1940, inked with a brush, coloured with Ben-Day tints on the three process plates and printed slightly out of
register on newsprint that has gone tan.
The story on the cover: at sunset the Rocket Squad blasts off for the moon. Captain June stands in the front
cockpit pointing the way ("NEXT STOP -- THE MOON!"), Pip the dog rides behind her in flying goggles, ears and tongue
flapping -- and Sparky the mechanic, who was still tightening a bolt, hangs from the rope ladder under the belly,
wrench in hand, cap flying off, yelling "HEY!! WAIT FOR ME!!". Below: the launch tower and its beacon, billowing
smoke, a desert of mesas and, on a butte, the squad's observatory with its telescope trained on the rocket; above:
a banded twilight sky, stars and a big cratered moon. Cover furniture: the perspective block logo ROCKET SQUAD with
its COMICS ribbon, a price box (No. 3, 10 cents, MAY), a caption, a sound effect. All characters, names and the title
are invented for this example.
Draw-on stages: newsprint -> key plate (setting) -> key plate (rocket) -> key plate (the squad) -> key plate
(lettering) -> progressive proofs: yellow -> + red -> + blue -> the cover decades on (browned edges, spine ticks,
staples, rubbed corner, crease, foxing). No image model.
python3 comic_rocket.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from comic import (ComicCover, WHITE, CREAM, PALE, YELLOW, GOLD, ORANGE, DEEP_ORANGE, RED, PINK, SKIN, TAN, BROWN,
                   DARK_BROWN, LIGHT_BLUE, BLUE, NAVY, LIGHT_GREY, SILVER)
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'comic_rocket.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

c = ComicCover(1920, 1080, seed=40, screen=11.0, misreg=4.6, slop=1.6)
W, H = c.W, c.H
rng = np.random.default_rng(7)
c.paper()
c.stage('newsprint', plates='')

tube, smooth, ell = c.tube_pts, c.smooth, c.ellipse_pts
HORIZON = 940

# ================================================================ frames
# the rocket's own frame: u runs along the axis from the tail to the nose, v across it toward the belly (px)
T0 = np.array([600.0, 790.0], np.float32)
TH = np.deg2rad(26)
D = np.array([np.cos(TH), -np.sin(TH)], np.float32)
NRM = np.array([np.sin(TH), np.cos(TH)], np.float32)


def R(pts):
    P = np.asarray(pts, np.float32).reshape(-1, 2)
    return T0 + P[:, :1] * D + P[:, 1:] * NRM


def R1(u, v):
    return tuple(float(t) for t in R([(u, v)])[0])


_prof = spline([(45, 80), (120, 95), (260, 102), (470, 100), (620, 86), (740, 58), (820, 28), (866, 0)], 14)


def rad(u):
    return float(np.interp(u, _prof[:, 0], _prof[:, 1]))


def frame(u0, v0, rot=0.0, s=1.0):
    """a figure's own frame (x toward the nose, y down) set into the rocket at (u0, v0), tilted rot deg"""
    cr, sr = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))

    def f(pts):
        P = np.asarray(pts, np.float32).reshape(-1, 2) * s
        return R(np.stack([P[:, 0] * cr + P[:, 1] * sr + u0, -P[:, 0] * sr + P[:, 1] * cr + v0], 1))
    return f


def sheet_frame(x0, y0, rot=0.0, s=1.0):
    cr, sr = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))

    def f(pts):
        P = np.asarray(pts, np.float32).reshape(-1, 2) * s
        return np.stack([P[:, 0] * cr + P[:, 1] * sr + x0, -P[:, 0] * sr + P[:, 1] * cr + y0], 1).astype(np.float32)
    return f


def feather_shape(pts, mask, length, **kw):
    P, N = c.edge_normals(pts)
    c.feather(P, N, length=length, clip=mask, **kw)


# ================================================================ sky, stars, moon
# twilight in stepped Ben-Day bands: night blue at the top, through pale, to the yellow-orange glow at the horizon
TWILIGHT = [(1, .4, 0, 0), (.7, .2, 0, 0), (.4, 0, 0, 0), (.2, 0, 0, 0), (0, 0, .4, 0), YELLOW, GOLD, ORANGE]
c.graded(None, TWILIGHT, (0, -10), (0, HORIZON + 10), edges=[0.15, 0.28, 0.40, 0.50, 0.57, 0.70, 0.84], wave=9)
MX, MY, MR = 1702, 250, 166
for i in range(80):
    x, y = rng.uniform(20, W - 20), rng.uniform(12, 470)
    if np.hypot(x - MX, y - MY) < MR + 16: continue
    s = rng.uniform(4, 9) if rng.random() < 0.6 else rng.uniform(10, 17)
    star = c.mask(c.burst_pts(x, y, s, s, 4, 0.72, int(rng.integers(1 << 30)), rot=rng.uniform(-10, 10)))
    c.flat(star, WHITE if (rng.random() < 0.5 or y > 330) else YELLOW)
for i in range(90):
    x, y = rng.uniform(10, W - 10), rng.uniform(10, 380)
    c.flat(c.circle(x, y, rng.uniform(1.6, 3.0)), WHITE)

moon = c.part(ell(MX, MY, MR, MR), CREAM, width=6.5, heavy=1.1)
c.flat(moon * np.clip(1 - c.circle(MX - 46, MY - 40, MR + 6), 0, 1), (0, 0, .4, .2))      # the night side
for (cx, cy, rr, rot) in [(1650, 190, 34, 10), (1745, 166, 20, -5), (1772, 290, 40, 15), (1675, 318, 22, 0),
                          (1612, 258, 14, 0), (1730, 224, 11, 0), (1800, 216, 13, 0)]:
    cr_ = c.mask(ell(cx, cy, rr, rr * 0.82, rot))
    c.flat(cr_ * moon, (0, 0, .4, .2))
    c.edge(ell(cx, cy, rr, rr * 0.82, rot, 30, 220), width=2.6 + rr * 0.05, heavy=0.4, taper=(0.2, 0.3))
mP, mN = c.edge_normals(ell(MX, MY, MR, MR))
c.feather(mP, mN, length=44, width=3.2, spacing=8, clip=moon, curl=0.1)

# ================================================================ desert: mesas, plain, the butte with the HQ
mesas = [(-20, 150, 70), (300, 520, 96)]
for k, (xa, xb, hgt) in enumerate(mesas):
    top = HORIZON - hgt
    xs = np.linspace(xa + 34, xb - 30, 9)
    ys = top + np.concatenate([[0], np.cumsum(rng.normal(0, 1.6, 8))])
    rim = [(xa, HORIZON + 4), (xa + 12, top + hgt * 0.45), (xa + 30, top + 4)] + list(zip(xs, ys)) + \
          [(xb - 24, top + 6), (xb - 10, top + hgt * 0.5), (xb + 2, HORIZON + 4)]
    m = c.part(rim, (.4, .7, .2, 0), width=0, line=False)
    shade = [(xb - 30, top + 5), (xb - 24, top + 6), (xb - 10, top + hgt * 0.5), (xb + 2, HORIZON + 4),
             (xb - 46, HORIZON + 4), (xb - 40, top + hgt * 0.5)]
    c.flat(c.mask(shade) * m, (.7, .7, .2, 0))
    c.edge(rim[1:-1], width=3.2, heavy=0.6, taper=(0.05, 0.05), smooth=False)
    for j in range(3):
        yy = top + hgt * (0.35 + 0.2 * j)
        c.brush([(xa + 22 + j * 6, yy), (xb - 48, yy + rng.normal(0, 2))], 2.0, taper=(0.3, 0.5), clip=m)
plain = [(-10, HORIZON), (W + 10, HORIZON), (W + 10, H + 10), (-10, H + 10)]
pm = c.part(plain, None, width=0, line=False)
c.graded(pm, [(0, .4, .7, 0), (0, .4, 1, 0), (0, .7, 1, 0)], (0, HORIZON), (0, H + 10), wave=5)
c.brush([(-5, HORIZON + 1), (W * 0.5, HORIZON + 2), (W + 5, HORIZON)], 3.0, taper=(0, 0), swell=0)
for i in range(18):
    x, y = rng.uniform(1000, 1560), rng.uniform(HORIZON + 14, H - 16)
    L = rng.uniform(30, 110) * (0.5 + (y - HORIZON) / 260)
    c.brush([(x, y), (x + L * 0.5, y + rng.normal(0, 1.5)), (x + L, y + rng.normal(0, 2))], 2.0 + (y - HORIZON) / 80,
            taper=(0.3, 0.5), swell=0.3)

# the butte: a flat top, a tall cliff with a black shadow under its rim and cracks running down, a talus slope
rim_x = np.linspace(1606, 1945, 40)
rim_y = 735 + np.cumsum(rng.normal(0, 0.9, 40)) * 0.6
butte = [(1488, H + 10), (1500, 984), (1540, 930), (1584, 886), (1588, 840), (1592, 790), (1598, 760)] + \
        list(zip(rim_x, rim_y)) + [(1945, H + 10)]
bm_ = c.part(butte, (0, .7, 1, 0), width=5.5, heavy=1.0)
toe = spline([(1584, 886), (1660, 902), (1760, 914), (1860, 908), (1950, 912)], 10)
talus = np.vstack([[(1470, H + 10), (1500, 984), (1540, 930)], toe, [(1960, H + 10)]])
tm = c.mask(talus) * bm_
c.flat(tm, TAN)
c.edge(toe, width=3.6, heavy=0.4, taper=(0.05, 0.3), smooth=False)
under = list(zip(rim_x, rim_y + 4)) + list(zip(rim_x[::-1], rim_y[::-1] + 15 + 6 * np.sin(rim_x[::-1] / 37)))
c.ink(c.mask(under) * bm_)
rimP = np.array(spline(np.stack([rim_x[2:-1], rim_y[2:-1] + 17 + 6 * np.sin(rim_x[2:-1] / 37)], 1), 4))
c.feather(rimP, np.tile([[0.0, -1.0]], (len(rimP), 1)), length=128, width=3.8, spacing=12, clip=bm_ * (1 - tm),
          toward=(0.0, -1.0), along=(0.0, 1.0), curl=0.04)
c.brush([(1596, 772), (1603, 830), (1598, 876)], 2.6, taper=(0.2, 0.5))
for (x, y, r_) in [(1540, 1010, 16), (1606, 950, 11), (1700, 990, 20), (1830, 1000, 14), (1650, 1050, 22), (1880, 1060, 18)]:
    rk = c.part(smooth([(x - r_, y + r_ * 0.4), (x - r_ * 0.6, y - r_ * 0.5), (x + r_ * 0.4, y - r_ * 0.6), (x + r_, y + r_ * 0.4)], 6),
                (0, .7, 1, 0), width=3.2)
    c.ink(c.mask(smooth([(x + r_ * 0.1, y - r_ * 0.5), (x + r_ * 0.5, y - r_ * 0.45), (x + r_, y + r_ * 0.4), (x, y + r_ * 0.4)], 6)) * rk)

HX, HY = 1790, 736                                            # observatory on the butte
c.part([(HX - 84, HY - 56), (HX + 84, HY - 56), (HX + 86, HY + 4), (HX - 86, HY + 4)], CREAM, width=4.5)
c.flat(c.mask([(HX + 38, HY - 56), (HX + 84, HY - 56), (HX + 86, HY + 4), (HX + 38, HY + 4)]), (0, .2, .4, .2))
c.part([(HX - 70, HY - 40), (HX - 46, HY - 40), (HX - 46, HY + 4), (HX - 70, HY + 4)], RED, width=3.5)
c.dot(HX - 50, HY - 16, 2.4)
c.letter('R.S. H.Q.', HX + 4, HY - 26, 20, face='bold')
dome = ell(HX, HY - 56, 92, 76, 0, 0, 180)
dm = c.part(np.vstack([dome, [(HX - 92, HY - 56)]]), SILVER, width=5)
c.flat(c.mask(ell(HX + 32, HY - 70, 52, 50)) * dm, (.2, 0, 0, .2))
c.flat(c.mask(ell(HX - 36, HY - 98, 18, 11, 30)) * dm, WHITE)
slot = [(HX - 16, HY - 130), (HX + 8, HY - 130), (HX + 10, HY - 58), (HX - 18, HY - 58)]
c.ink(c.mask(slot))
c.part(tube([(HX - 4, HY - 100), (HX - 82, HY - 166)], [26, 32], caps=False), NAVY, width=4)
c.part(ell(HX - 84, HY - 168, 11, 18, 40), CREAM, width=3.5)
c.ink(c.mask([(HX - 86, HY - 3), (HX + 86, HY - 3), (HX + 88, HY + 4), (HX - 88, HY + 4)]))

# ================================================================ the launch tower
LX0, LX1, LTOP = (176, 302), (214, 264), 530


def leg_x(side, y):
    a, b = (LX0[0], LX1[0]) if side == 0 else (LX0[1], LX1[1])
    return a + (b - a) * (H + 10 - y) / (H + 10 - LTOP)


ys = np.arange(H - 20, LTOP + 30, -64.0)
for y0, y1 in zip(ys[:-1], ys[1:]):
    c.pen([(leg_x(0, y0), y0), (leg_x(1, y1), y1)], 3.0, smooth=False)
    c.pen([(leg_x(1, y0), y0), (leg_x(0, y1), y1)], 3.0, smooth=False)
for y in ys:
    c.part([(leg_x(0, y) - 2, y - 5), (leg_x(1, y) + 2, y - 5), (leg_x(1, y) + 2, y + 5), (leg_x(0, y) - 2, y + 5)], RED, width=3)
for side in (0, 1):
    c.part(tube([(leg_x(side, H + 10), H + 10), (leg_x(side, LTOP), LTOP)], [18, 13], caps=False), RED, width=4.2)
arm = [(leg_x(1, 640) - 4, 632), (420, 600), (424, 616), (leg_x(1, 650) - 4, 652)]
c.part(arm, RED, width=3.8)
for k in range(5):
    xk = 280 + k * 28
    c.pen([(xk, 634 - k * 6.5), (xk + 14, 648 - k * 6.5)], 2.2, smooth=False)
c.pen([(414, 614), (416, 666)], 2.2, smooth=False)
c.part(ell(416, 674, 9, 9), SILVER, width=3)
c.part([(LX1[0] - 22, LTOP - 4), (LX1[1] + 22, LTOP - 4), (LX1[1] + 22, LTOP + 10), (LX1[0] - 22, LTOP + 10)], RED, width=3.8)
for x in np.linspace(LX1[0] - 18, LX1[1] + 18, 6):
    c.pen([(x, LTOP - 4), (x, LTOP - 30)], 2.4, smooth=False)
c.pen([(LX1[0] - 20, LTOP - 30), (LX1[1] + 20, LTOP - 30)], 2.6, smooth=False)
BX, BY = (LX1[0] + LX1[1]) / 2, LTOP - 44
c.part(ell(BX, BY, 14, 14), RED, width=4)
c.flat(c.circle(BX - 4, BY - 5, 4), WHITE)
for a in np.deg2rad(np.arange(0, 360, 36) + 18):
    c.brush([(BX + np.cos(a) * 22, BY + np.sin(a) * 22), (BX + np.cos(a) * 40, BY + np.sin(a) * 40)], 3.0, taper=(0.1, 0.6))
c.stage('key_setting', plates='K')

# ================================================================ speed lines and the flame
c.speed(R1(-40, -165), -D, n=6, length=300, spread=90, width=4.2, seed=3)
c.speed(R1(120, -150), -D, n=3, length=180, spread=40, width=3.4, seed=4)


def flame_pts(length, width, tongues, seed, u0=-6):
    """a flame from the nozzle backwards: swelling body, ragged tongues at the far end"""
    r = np.random.default_rng(seed)
    n = 60
    t = np.linspace(0, 1, n)
    half = width * 0.5 * np.sin(np.pi * np.clip(t * 0.85 + 0.12, 0, 1)) ** 0.8 * (1 - 0.25 * t)
    top = [(u0 - length * tt, -hw) for tt, hw in zip(t, half)]
    bot = [(u0 - length * tt, hw) for tt, hw in zip(t, half)]
    tips = []
    for k in range(tongues):
        f = (k + 0.5) / tongues
        tips.append((u0 - length * (1.0 + 0.18 * r.random() + 0.12 * np.sin(np.pi * f)), (f - 0.5) * width * 0.9))
    tail_pts = []
    for k, (tu, tv) in enumerate(tips):
        tail_pts.append((tu, tv))
        if k < len(tips) - 1:
            nu, nv = tips[k + 1]
            tail_pts.append(((tu + nu) / 2 + length * 0.16, (tv + nv) / 2))
    return R(np.asarray(top[:-2] + tail_pts + bot[:-2][::-1], np.float32))


fm = c.part(flame_pts(430, 196, 5, 11), RED, width=4.5, heavy=0.6)
c.part(flame_pts(350, 146, 4, 12), DEEP_ORANGE, width=0, line=False)
c.part(flame_pts(300, 118, 3, 15), ORANGE, width=0, line=False)
c.part(flame_pts(270, 96, 3, 13), YELLOW, width=0, line=False)
c.part(flame_pts(160, 46, 2, 14), WHITE, width=0, line=False)
for k in range(5):
    v = (k - 2) * 26
    c.brush([R1(-190, v), R1(-250 - 24 * (k % 2), v * 1.25), R1(-310 - 34 * (k % 2), v * 1.5)], 2.8, taper=(0.3, 0.6), clip=fm)

# ================================================================ Captain June and Pip (drawn before the hull, which hides
# everything below the cockpit rims)
def june():
    f = frame(565, -rad(565) + 14, rot=9)
    scarf = [(-4, -104), (-40, -136), (-80, -150), (-116, -180), (-150, -190), (-184, -220)]
    sm = c.part(f(tube(scarf, [24, 28, 24, 20, 14, 8])), RED, width=4.2)
    for (x, y) in [(-30, -128), (-62, -148), (-96, -158), (-126, -186), (-160, -200), (-48, -136), (-108, -172)]:
        c.flat(c.circle(*f([(x, y)])[0], 4.2) * sm, WHITE)
    torso_pts = [(-36, 40), (-40, -36), (-30, -82), (-6, -98), (22, -94), (36, -56), (38, 40)]
    torso = c.part(f(smooth(torso_pts, 8)), BLUE, width=5)
    c.flat(c.mask(f(smooth([(12, -70), (36, -56), (38, 40), (18, 40)], 6))) * torso, NAVY)
    c.part(f([(-20, -94), (-2, -78), (16, -92), (2, -104), (-10, -104)]), YELLOW, width=3.2)
    star = c.part(f(c.burst_pts(-8, -48, 14, 14, 5, 0.55, 3, rot=-90)), YELLOW, width=2.8, heavy=0.3)
    c.part(f(tube([(-4, -96), (0, -114)], [17, 17], caps=False)), SKIN, width=3)
    hx, hy = 6, -146
    S = lambda pts: f([(hx + x, hy + y) for x, y in pts])
    head = [(-36, -4), (-28, -30), (-2, -42), (26, -34), (38, -18), (40, -8), (51, 4), (42, 10), (43, 17), (38, 23),
            (38, 31), (26, 38), (8, 36), (-8, 28), (-26, 18)]
    hm = c.part(S(smooth(head, 8)), SKIN, width=4.4)
    for (x, y, r) in [(-34, 18, 9), (-24, 26, 8), (-38, 6, 8)]:
        c.part(S(ell(x, y, r, r)), DEEP_ORANGE, width=3)
    helmet = [(30, -30), (18, -44), (-6, -50), (-30, -42), (-44, -20), (-42, 2), (-28, 12), (-14, 16), (-6, 8),
              (-10, -4), (-4, -16), (14, -26)]
    hel = c.part(S(smooth(helmet, 8)), BROWN, width=4.4)
    c.flat(c.mask(S(smooth([(-30, -34), (-8, -45), (16, -40), (-12, -34), (-36, -14)], 6))) * hel, TAN)
    c.part(S(smooth([(-16, 10), (-6, 6), (-2, 22), (-10, 30), (-18, 24)], 6)), BROWN, width=3.4)
    c.brush(S([(-6, 26), (10, 36), (24, 38)]), 2.6, taper=(0.1, 0.3))
    c.ink(c.mask(S(tube([(-42, -18), (-16, -36), (8, -42)], [8, 8, 8]))))
    g = c.part(S(ell(14, -40, 11, 9, 20)), GOLD, width=5)
    c.flat(c.circle(*S([(10, -43)])[0], 3.0) * g, WHITE)
    c.part(S(smooth([(22, -8), (30, -12), (36, -8), (30, -4)], 6)), WHITE, width=2.4)
    c.ink(c.circle(*S([(31, -8)])[0], 3.2))
    c.brush(S([(20, -11), (27, -14), (35, -12), (39, -14)]), 2.6, taper=(0.2, 0.2))
    c.brush(S([(20, -20), (29, -24), (38, -21)]), 3.0, taper=(0.3, 0.4))
    mouth = c.mask(S(smooth([(43, 15), (34, 16), (28, 20), (36, 26), (42, 21)], 6)))
    c.ink(mouth)
    c.flat(c.mask(S(ell(38, 17, 5, 2.4))), WHITE); c.erase(c.mask(S(ell(38, 17, 5, 2.4))) * mouth)
    c.brush(S([(26, 15), (30, 11)]), 2.0, taper=(0.2, 0.2))
    c.flat(c.circle(*S([(18, 8)])[0], 7) * hm, PINK)
    c.brush(S([(2, 2), (6, 12)]), 2.0, taper=(0.3, 0.3))
    arm = [(14, -84), (58, -68), (100, -50)]
    c.part(f(tube(arm, [27, 24, 20])), BLUE, width=4.5)
    c.part(f(tube([(96, -52), (110, -46)], [24, 22])), YELLOW, width=3.5)
    c.part(f(smooth([(108, -60), (126, -58), (134, -44), (124, -32), (110, -36)], 6)), BROWN, width=3.8)
    c.part(f(tube([(126, -56), (160, -46)], [10, 8])), BROWN, width=3.4)
    c.brush(f([(114, -50), (126, -48)]), 2.0, taper=(0.2, 0.2))
    c.brush(f([(114, -42), (124, -40)]), 2.0, taper=(0.2, 0.2))
    return S


def pip():
    f = frame(378, -rad(378) + 16, rot=2)
    c.part(f(smooth([(-30, 30), (-32, -36), (-12, -62), (20, -60), (34, -28), (32, 30)], 8)), WHITE, width=4.5)
    c.part(f(tube([(-24, -54), (30, -52)], [14, 12])), RED, width=3.4)
    c.part(f(c.burst_pts(8, -40, 7, 7, 4, 0.35, 2)), YELLOW, width=2.4)
    for x in (6, 28):
        c.part(f(smooth([(x - 10, -2), (x - 8, -16), (x + 8, -18), (x + 13, -4)], 6)), WHITE, width=3.4)
        c.brush(f([(x + 1, -12), (x + 2, -4)]), 1.8, taper=(0.2, 0.2))
    tongue = [(48, -72), (30, -62), (8, -60), (-10, -50)]
    c.part(f(tube(tongue, [12, 13, 11, 7])), PINK, width=3.2)
    head = [(-24, -78), (-26, -102), (-8, -120), (18, -120), (34, -108), (48, -100), (72, -98), (90, -94), (92, -84),
            (80, -76), (54, -74), (30, -66), (6, -62), (-14, -66)]
    hm = c.part(f(smooth(head, 8)), WHITE, width=4.5)
    c.ink(c.mask(f(smooth([(-18, -96), (-10, -112), (4, -110), (2, -94), (-10, -86)], 6))) * hm)
    c.ink(c.mask(f(smooth([(80, -100), (95, -96), (96, -84), (82, -84)], 6))))
    c.flat(c.circle(*f([(85, -96)])[0], 2.6), WHITE); c.erase(c.circle(*f([(85, -96)])[0], 2.6))
    c.brush(f([(90, -82), (72, -78), (52, -76)]), 3.0, taper=(0.2, 0.3))
    c.brush(f([(44, -102), (64, -100)]), 2.0, taper=(0.3, 0.4))
    ear = [(-6, -112), (-36, -128), (-66, -118), (-90, -130)]
    em = c.part(f(tube(ear, [24, 26, 18, 8])), None, width=0, line=False)
    c.ink(em)
    c.erase(c.mask(f(tube([(-28, -130), (-58, -124), (-80, -132)], [3, 4, 2]))) * em)
    c.ink(c.mask(f(tube([(-22, -104), (10, -112)], [7, 7]))))
    g = c.part(f(ell(22, -100, 14, 13)), GOLD, width=5.5)
    c.flat(c.circle(*f([(17, -105)])[0], 3.6) * g, WHITE)
    c.ink(c.circle(*f([(26, -98)])[0], 4.2) * g)
    return f


pip()
S_june = june()

# ================================================================ the rocket
fin_top = [(215, -96), (110, -160), (18, -236), (-16, -236), (-2, -170), (30, -110), (60, -84)]
fin_bot = [(215, 96), (120, 140), (34, 196), (4, 198), (8, 150), (34, 104), (60, 84)]
for fp, side in ((fin_top, -1.0), (fin_bot, 1.0)):
    fmk = c.part(R(smooth(fp, 8)), YELLOW, width=5)
    c.flat(c.mask(R(smooth([(fp[2][0] + 2, fp[2][1] * 0.97), (fp[3][0] + 10, fp[3][1] * 0.95), (fp[4][0] + 14, fp[4][1]),
                            (fp[5][0] + 20, fp[5][1] * 1.02)], 6))) * fmk, RED)
    c.ink(c.mask(R(smooth([(70, side * 90), (40, side * 116), (16, side * 150), (8, side * 116), (40, side * 86)], 6))) * fmk)
bell = [(50, -50), (50, 50), (8, 62), (-10, 76), (-10, -76), (8, -62)]
bmk = c.part(R(bell), None, width=5)
c.ink(bmk)
c.part(R([(-10, -76), (2, -70), (2, 70), (-10, 76)]), SILVER, width=3.4)
c.flat(c.mask(R(tube([(40, -40), (12, -56)], [6, 4]))), WHITE); c.erase(c.mask(R(tube([(40, -40), (12, -56)], [6, 4]))))

us = np.linspace(45, 866, 90)
BODY = R([(u, -rad(u)) for u in us] + [(u, rad(u)) for u in us[::-1]])
bm = c.part(BODY, RED, width=6.5, heavy=1.0)
NOSE_U = 690
c.flat(c.mask(R([(u, -rad(u) - 4) for u in np.linspace(NOSE_U, 870, 30)] + [(u, rad(u) + 4) for u in np.linspace(870, NOSE_U, 30)])) * bm, YELLOW)
c.pen(R([(NOSE_U, -rad(NOSE_U)), (NOSE_U + 6, 0), (NOSE_U, rad(NOSE_U))]), 3.4)
c.flat(c.mask(R([(u, -rad(u) - 4) for u in np.linspace(828, 870, 12)] + [(u, rad(u) + 4) for u in np.linspace(870, 828, 12)])) * bm, RED)
c.pen(R([(828, -rad(828)), (831, 0), (828, rad(828))]), 3.0)
BAND = (590, 640)
c.flat(c.mask(R([(BAND[0], -110), (BAND[1], -110), (BAND[1], 110), (BAND[0], 110)])) * bm, WHITE)
for u in BAND:
    c.pen(R([(u, -rad(u)), (u + 5, 0), (u, rad(u))]), 3.2)
c.letter('RS-1', *R1(615, 4), 30, face='slab', rot=-64, jitter=0.3)
c.flat(c.mask(R(tube([(110, -64), (330, -76), (560, -68)], [7, 18, 6]))) * bm, WHITE)
c.flat(c.mask(R(tube([(150, -44), (330, -52), (500, -48)], [3, 7, 2]))) * bm, (0, .4, .4, 0))
shadow_band = [(60, 62), (200, 70), (400, 68), (560, 58), (700, 40), (800, 18), (850, 2), (850, rad(850) + 6),
               (700, rad(700) + 6), (400, rad(400) + 6), (200, rad(200) + 6), (60, rad(60) + 6)]
c.ink(c.mask(R(smooth(shadow_band, 8))) * bm)
fe = np.array([(u, 60 - 6 * np.sin((u - 60) / 800 * np.pi) - max(0, (u - 560)) * 0.16) for u in np.linspace(70, 830, 140)], np.float32)
band_m = c.mask(R([(BAND[0] - 3, -110), (BAND[1] + 3, -110), (BAND[1] + 3, 110), (BAND[0] - 3, 110)]))
c.feather(R(fe), np.tile(NRM, (len(fe), 1)), length=46, width=3.2, spacing=10, clip=bm * (1 - band_m), toward=NRM, along=-NRM,
          curl=-0.12)
for u in (160, 470, 760):
    for v in np.linspace(-rad(u) + 12, rad(u) - 30, 7):
        c.dot(*R1(u + 2 * (1 - (v / rad(u)) ** 2), v), 2.0)
for (u, v) in [(200, -8), (290, -8)]:
    c.part(R(ell(u, v, 22, 22)), SILVER, width=5)
    c.part(R(ell(u, v, 14, 14)), LIGHT_BLUE, width=3)
    c.flat(c.circle(*R1(u - 5, v - 6), 4.0), WHITE)

for u0 in (378, 565):
    lip = [(u0 - 52, -rad(u0 - 52) + 2), (u0, -rad(u0) + 16), (u0 + 46, -rad(u0 + 46) + 4)]
    c.brush(R(lip), 4.4, taper=(0.15, 0.15))

# the hatch and the rope ladder, swinging back in the slipstream
HU = 362
c.ink(c.mask(R(ell(HU, rad(HU) - 6, 26, 9))))
LB = np.array([898.0, 836.0])
A0, B0 = np.array(R1(HU - 16, rad(HU) - 6)), np.array(R1(HU + 16, rad(HU) - 6))
A1, B1 = LB + np.array([-19.0, -4.0]), LB + np.array([19.0, 4.0])
railA = spline([A0, (A0 + A1) / 2 + np.array([9, 0]), A1], 10)
railB = spline([B0, (B0 + B1) / 2 + np.array([9, 0]), B1], 10)
for k in range(1, 6):
    t = k / 5.0
    pa = railA[int(t * (len(railA) - 1))]; pb = railB[int(t * (len(railB) - 1))]
    dv = (pb - pa) / np.linalg.norm(pb - pa)
    nv = np.array([-dv[1], dv[0]])
    c.part([pa - dv * 6 - nv * 5, pb + dv * 6 - nv * 5, pb + dv * 6 + nv * 5, pa - dv * 6 + nv * 5], TAN, width=3)
for rail in (railA, railB):
    c.part(tube(rail[::3], [7, 7, 7, 7], caps=True), (0, .2, .7, 0), width=2.8)
c.stage('key_rocket_and_crew', plates='K')


# ================================================================ smoke billowing round the pad
puffs = [(70, 905, 72), (180, 900, 70), (300, 950, 90), (140, 975, 104), (470, 985, 96), (620, 1000, 78),
         (720, 1030, 64), (40, 1050, 120), (230, 1056, 126), (420, 1060, 118), (590, 1070, 96), (770, 1080, 70)]
flame_tip = np.array(R1(-430, 0))
for (x, y, r) in puffs:
    pts = c.ellipse_pts(x, y, r, r * 0.9, rng.uniform(0, 180), n=72)
    pts = pts + (pts - (x, y)) * (0.035 * np.sin(np.linspace(0, 2 * np.pi, 72, endpoint=False) * rng.integers(5, 8)
                                             + rng.uniform(0, 6)))[:, None]
    m = c.part(pts, WHITE, width=4.6, heavy=0.8)
    c.flat(m * np.clip(1 - c.circle(x - r * 0.2, y - r * 0.22, r * 0.98), 0, 1), LIGHT_GREY)
    near = np.hypot(x - flame_tip[0], y - flame_tip[1])
    if near < 300:
        c.flat(m * c.circle(x - r * 0.2, y - r * 0.32, r * 0.55), PALE)
    P_, N_ = c.edge_normals(pts)
    c.feather(P_, N_, length=r * 0.4, width=3.0, spacing=9, clip=m, curl=0.2)


# ================================================================ Sparky on the ladder
def sparky():
    f = sheet_frame(LB[0], LB[1] + 2, rot=-6, s=1.15)
    leg_l = [(22, 128), (2, 166), (-24, 160)]
    leg_r = [(46, 128), (74, 160), (98, 146)]
    for leg, foot, ang in ((leg_l, (-34, 156), 20), (leg_r, (106, 140), -30)):
        c.part(f(tube(leg, [30, 26, 22])), BLUE, width=4.5)
        c.part(f(tube([leg[-1], (foot[0] * 0.6 + leg[-1][0] * 0.4, foot[1] * 0.6 + leg[-1][1] * 0.4)], [22, 20])), (0, 0, .4, 0), width=3)
        c.part(f(ell(foot[0], foot[1], 18, 11, ang)), BROWN, width=4)
    tp = [(4, 62), (20, 54), (52, 58), (66, 76), (62, 132), (36, 142), (10, 136), (2, 100)]
    torso = c.part(f(smooth(tp, 8)), BLUE, width=5)
    c.part(f(smooth([(8, 60), (22, 52), (54, 56), (62, 70), (50, 80), (30, 84), (14, 80)], 6)), (0, .4, 1, 0), width=3.6)
    c.part(f([(14, 78), (24, 74), (26, 112), (16, 114)]), BLUE, width=3)
    c.part(f([(44, 76), (54, 80), (50, 114), (40, 112)]), BLUE, width=3)
    for (x, y) in [(20, 82), (48, 84)]:
        c.part(f(ell(x, y, 4.5, 4.5)), YELLOW, width=2.2)
    c.part(f(smooth([(20, 102), (46, 102), (46, 124), (20, 124)], 4)), (1, .7, 0, .2), width=3)
    c.brush(f([(24, 140), (36, 136), (60, 128)]), 2.4, taper=(0.3, 0.3))
    feather_shape(f(smooth(tp, 8)), torso, 22, width=3.0, spacing=8)
    c.part(f(tube([(-2, 14), (4, 38), (10, 64)], [17, 19, 22])), (0, .4, 1, 0), width=4.2)
    c.part(f(smooth([(-14, -6), (-2, -14), (14, -10), (16, 6), (6, 14), (-10, 10)], 6)), CREAM, width=4)
    c.brush(f([(-8, -2), (8, -4)]), 2.0, taper=(0.2, 0.2))
    c.part(f(tube([(56, 80), (86, 76), (108, 52)], [20, 18, 16])), (0, .4, 1, 0), width=4.2)
    c.part(f(tube([(116, 52), (130, 4)], [11, 10], caps=False)), SILVER, width=3.6)
    c.part(f(smooth([(118, 4), (122, -18), (134, -22), (146, -10), (140, 0), (132, -6), (128, 6)], 6)), SILVER, width=3.6)
    c.part(f(smooth([(102, 48), (114, 40), (124, 50), (118, 62), (106, 60)], 6)), CREAM, width=3.6)
    hx, hy = 40, 30
    c.part(f(smooth([(hx - 26, hy + 4), (hx - 22, hy - 20), (hx, hy - 30), (hx + 24, hy - 22), (hx + 30, hy + 2),
                     (hx + 22, hy + 26), (hx, hy + 32), (hx - 18, hy + 24)], 8)), SKIN, width=4.5)
    c.part(f(ell(hx - 26, hy + 4, 7, 10)), SKIN, width=3.4)
    hair = [(hx - 26, hy - 6), (hx - 30, hy - 26), (hx - 14, hy - 22), (hx - 12, hy - 42), (hx + 2, hy - 28), (hx + 10, hy - 46),
            (hx + 16, hy - 26), (hx + 30, hy - 34), (hx + 26, hy - 16), (hx + 6, hy - 22), (hx - 12, hy - 14)]
    c.part(f(hair), DARK_BROWN, width=3.8)
    for ex in (hx + 4, hx + 20):
        c.part(f(ell(ex, hy - 6, 6.5, 9)), WHITE, width=3)
        c.ink(c.circle(*f([(ex + 2.5, hy - 10)])[0], 3.2))
    c.brush(f([(hx - 2, hy - 20), (hx + 6, hy - 24), (hx + 12, hy - 22)]), 2.6, taper=(0.2, 0.3))
    c.brush(f([(hx + 16, hy - 22), (hx + 22, hy - 25), (hx + 28, hy - 21)]), 2.6, taper=(0.2, 0.3))
    c.brush(f([(hx + 13, hy - 2), (hx + 17, hy + 5), (hx + 12, hy + 7)]), 2.4, taper=(0.2, 0.3))
    mouth = c.mask(f(smooth([(hx + 6, hy + 12), (hx + 16, hy + 9), (hx + 24, hy + 13), (hx + 18, hy + 24), (hx + 9, hy + 22)], 6)))
    c.ink(mouth)
    tongue = c.mask(f(ell(hx + 15, hy + 20, 6, 3.5))) * mouth
    c.flat(tongue, RED); c.erase(tongue)
    for (x, y) in [(hx - 4, hy + 4), (hx + 1, hy + 8), (hx + 27, hy + 4), (hx - 8, hy + 9)]:
        c.dot(*f([(x, y)])[0], 1.6)
    cap = [(-22, 0), (-18, -16), (0, -22), (18, -14), (22, 0)]
    cf = sheet_frame(LB[0] + 150, LB[1] - 62, rot=-34, s=1.15)
    c.part(cf(np.vstack([spline(cap, 8), [(30, 4), (34, 8), (-22, 4)]])), RED, width=4)
    c.part(cf(ell(0, -20, 5, 3)), RED, width=2.6)
    for k, (a0, a1) in enumerate([(200, 250), (210, 260)]):
        c.edge(ell(LB[0] + 150, LB[1] - 62, 52 + k * 15, 46 + k * 13, 0, a0, a1), width=2.8, heavy=0, taper=(0.2, 0.4))
    for (x0, y0, x1, y1) in [(-58, 150, -76, 132), (-52, 172, -76, 170), (122, 128, 140, 110), (126, 150, 148, 146)]:
        c.brush(f([(x0, y0), (x1, y1)]), 3.0, taper=(0.3, 0.7))
    for (x, y, rr) in [(hx - 34, hy - 20, 6), (hx + 38, hy - 28, 5)]:
        c.part(f(smooth([(x, y - rr * 1.6), (x + rr, y), (x, y + rr), (x - rr, y)], 6)), WHITE, width=2.4)
    return f


S_sparky = sparky()
c.stage('key_smoke_and_sparky', plates='K')

# ================================================================ cover furniture and lettering
c.logo('ROCKET SQUAD', [(232, 62), (1150, 28), (1150, 208), (232, 184)], vp=(690, 2600), depth=26,
       colours=(YELLOW, GOLD, ORANGE), shade=RED, shadow=NAVY, shadow_off=(9, 11), outline=8.5, inner=3.4, glints=4)
rib = [(256, 228), (568, 214), (552, 240), (570, 266), (258, 280), (276, 254)]
c.part(rib, BLUE, width=4.2)
c.letter('COMICS', 414, 247, 34, face='bold', colour=WHITE, rot=2.5, jitter=0, tracking=0.18)
c.part([(28, 26), (206, 22), (210, 240), (30, 244)], WHITE, width=5.5)
c.letter('No.', 64, 66, 26, face='slab', jitter=0.3)
c.letter('3', 112, 66, 58, face='heavy', jitter=0)
c.brush([(40, 106), (198, 104)], 3.4, taper=(0.05, 0.05), swell=0)
c.letter('10¢', 118, 158, 70, face='heavy', jitter=0)
c.letter('MAY', 118, 214, 26, face='bold', jitter=0.3, tracking=0.2)
c.caption(36, 318, 566, 470, 'COUNTDOWN COMPLETE! THE\nROCKET SQUAD BLASTS OFF\nFOR THE MOON -- BUT ONE\nMEMBER IS RUNNING LATE!', 27,
          colour=YELLOW, width=4.2)
mouth = S_june([(44, 18)])[0]
c.balloon('NEXT STOP --\nTHE MOON!', 1352, 136, 38, tail=(mouth[0] + 26, mouth[1] - 22), seed=2)
c.balloon('HEY!! WAIT\nFOR ME!!', 1240, 960, 46, tail=tuple(S_sparky([(70, 50)])[0]), kind='yell', seed=5)
c.sfx('WHOOOSH!', 380, 1006, 104, colour=YELLOW, rot=7, width=6.5, shade=RED, shade_off=(7, 7))
c.stage('key_lettering', plates='K')

# ================================================================ progressive proofs, then decades on a shelf
c.stage('proof_yellow', plates='YK')
c.stage('proof_red', plates='YMK')
c.stage('proof_blue', plates='CMYK')
c.brown_edges(width=55, amount=0.9)
c.spine(x=0, ticks=80, staples=(0.27, 0.73))
c.corner('br', radius=80)
c.corner('tr', radius=46, fold=False)
c.crease((1560, 1080), (1920, 820), strength=0.8)
c.foxing(46)
print(f'drawn in {time.time() - t0:.1f}s')
c.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s')
