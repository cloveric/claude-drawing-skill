"""运河小镇 · 一阵风 (De Windvlaag) — a Delft tile wall: an 11 x 7 tile picture set among single tiles.

One gust from the west crosses a canal town and everything answers it: the mill's sails turn, the sail barge
loaded with flour sacks runs before it with its pennant streaming, chimney smoke and the washing on the line
blow to the right, the tulips bow, and a man's hat flies off over the water while his dog leaps for it.
The weathervane on the step gable points into the wind.

    python3 examples/delft_canal.py out.jpg [--stages DIR]
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from delft import DelftTile, arc, ellipse_pts, _normals, _resample  # noqa: E402
from core import spline  # noqa: E402


def limb(t, pts, r0, r1, width=1.7, dens=1.0, tone=None):
    """a limb or sleeve as two outlines that taper from r0 to r1 (px); returns its polygon"""
    P, _ = _resample(spline(np.asarray(pts, np.float32), 8), 2.0)
    nr = _normals(P)
    rr = np.linspace(r0, r1, len(P))[:, None]
    L, R = P + nr * rr, P - nr * rr
    t.trek(L, width, dens, taper=(0.05, 0.2))
    t.trek(R, width, dens, taper=(0.05, 0.2))
    poly = np.vstack([L, R[::-1]])
    if tone: t.wash(poly, tone, slip=0.4, pool=0.5)
    return poly


def man(t, fx, fy, h):
    """a man in a long coat running to the right, reaching up after his hat; surprised open mouth,
    hair and coat skirts blown forward by the gust"""
    s = h / 100.0
    def P(u, v): return (fx + u * s, fy - v * s)
    w = 1.8
    hx, hy = P(16, 91)
    head = ellipse_pts(hx, hy, 6.4 * s, 7.2 * s, 0.15, 28)
    face = [P(10.5, 96), P(14, 98.5), P(19, 98.4), P(22, 95), P(22.6, 92.5), P(24.4, 90.6), P(22.6, 89.6), P(22.6, 87.5),
            P(20, 84.3), P(15, 84.2), P(10.6, 87.5), P(9.6, 92)]
    t.trek(face + [face[0]], w)
    hair = [P(9.4, 92), P(10.4, 96.6), P(14, 99), P(19.5, 98.8), P(17, 96.5), P(13.5, 95), P(12.4, 91), P(11.6, 87.8), P(9.8, 88.6)]
    t.trek(hair + [hair[0]], 1.3)
    t.wash(hair, 0.55, slip=0.3, pool=0.3)
    t.trek([P(14, 99), P(21, 102.5), P(28, 101.5)], 1.3, taper=(0.1, 0.8))            # strands blown forward
    t.trek([P(17, 98.8), P(24, 100), P(30, 98)], 1.1, 0.85, taper=(0.1, 0.8), pounce=False)
    t.dot(*P(19.6, 93), r=1.3)
    t.trek([P(17.5, 95.5), P(20.5, 96)], 1.1, smooth=False, pounce=False)                 # raised brow
    t.closed(ellipse_pts(*P(20.6, 87.6), 1.3 * s, 1.5 * s, 0, 10), 1.2)                  # 'oh!'
    t.trek(arc(*P(13.2, 90.5), 1.6 * s, 2.2 * s, -1.2, 1.6, 8), 1.1, pounce=False)       # ear
    t.wash(face, 0.05, slip=0.3)
    t.occlude(face + [P(28, 101.5)])
    # raised front arm with a turned-back cuff and an open hand
    hand = [P(35.5, 101.5), P(37, 106.5), P(38.6, 110.5), P(40, 107), P(41.3, 111), P(42.4, 106.6), P(44.5, 108.8), P(44.4, 104.6),
            P(46.6, 104), P(43.2, 100.5), P(39.4, 99)]
    t.trek(hand + [hand[0]], 1.3)
    t.wash(hand, 0.05, slip=0.2)
    t.occlude(hand)
    cuff = [P(31, 94), P(37.6, 98.6), P(35, 103), P(28.4, 98.6)]
    t.trek(cuff + [cuff[0]], 1.5, smooth=False)
    t.wash(cuff, 0.5, slip=0.2)
    t.occlude(cuff)
    arm = limb(t, [P(18, 79), P(25, 88), P(32, 98)], 4.2 * s, 3.6 * s, w, tone=0.3)
    t.occlude(arm)
    # coat: leaning forward, skirts blown ahead
    coat = [P(8, 83), P(21, 81), P(24, 66), P(25, 54), P(37, 36), P(30, 32.5), P(20, 34.5), P(10, 31), P(-3, 34.5), P(3, 50), P(4.5, 70)]
    t.trek(coat + [coat[0]], w)
    t.trek([P(14.5, 80), P(16, 66), P(17.5, 52), P(21, 35)], 1.2, 0.85, pounce=False)
    for v in (75, 68, 61, 54):
        t.dot(*P(16 + (80 - v) * 0.06, v), r=1.3)
    t.trek([P(3.5, 55), P(24.5, 56)], 1.5, smooth=False)
    t.trek([P(5, 50), P(-1, 40)], 1.0, 0.7, pounce=False)
    t.trek([P(24, 50), P(31, 40)], 1.0, 0.7, pounce=False)
    cravat = [P(17, 83.5), P(22, 82), P(21, 76), P(18, 74.5), P(16.5, 79)]
    t.trek(cravat + [cravat[0]], 1.2)
    t.wash(coat, 0.34, angle=-1.3, slip=0.8, pool=0.6, holes=[cravat])
    t.hatch([P(-3, 34.5), P(3, 50), P(10, 49), P(10, 31)], angle=-1.2, spacing=3.2, width=0.8, dens=0.7)
    t.occlude(coat)
    # back arm swinging behind
    hb = [P(-8.5, 63.5), P(-12.6, 61.5), P(-14.6, 57.6), P(-12, 55.6), P(-8.4, 57.8)]
    t.trek(hb + [hb[0]], 1.3)
    t.occlude(hb)
    cb = [P(-2.5, 67.5), P(-8.5, 64.5), P(-6, 58), P(0.5, 61.5)]
    t.trek(cb + [cb[0]], 1.4, smooth=False)
    t.wash(cb, 0.5, slip=0.2)
    t.occlude(cb)
    limb(t, [P(7, 78), P(3, 70), P(-1, 63)], 3.8 * s, 3.4 * s, w * 0.95, tone=0.3)
    # legs: breeches to the knee, pale stockings, buckled shoes; the back leg kicked up
    for (pts, shoe) in (([P(18, 34), P(23, 22), P(25, 7)], [P(21.5, 7.5), P(28, 7.5), P(35.5, 3.6), P(33, -0.4), P(21.5, -0.4)]),
                        ([P(7, 34), P(0, 23), P(-9, 14)], [P(-7.4, 16.2), P(-12.2, 18.8), P(-20, 13.6), P(-18.6, 9.4), P(-9.6, 11)])):
        t.trek(shoe + [shoe[0]], 1.5)
        t.wash(shoe, 0.6, slip=0.1, pool=0.2)
        t.occlude(shoe)
        knee = pts[1]
        br = limb(t, [pts[0], ((pts[0][0] + knee[0]) / 2, (pts[0][1] + knee[1]) / 2), knee], 4.4 * s, 3.4 * s, w, tone=0.45)
        t.occlude(br)
        limb(t, [knee, ((knee[0] + pts[2][0]) / 2, (knee[1] + pts[2][1]) / 2), pts[2]], 2.9 * s, 2.2 * s, w * 0.9)


def hat(t, x, y, r):
    """a broad-brimmed hat tumbling through the air"""
    rot = -0.45
    brim = ellipse_pts(x, y, r, r * 0.34, rot, 30)
    t.closed(brim, 1.8)
    c, s = np.cos(rot), np.sin(rot)
    def R(u, v): return (x + u * c - v * s, y + u * s + v * c)
    crown = [R(-r * 0.52, -r * 0.08), R(-r * 0.55, -r * 0.55), R(-r * 0.3, -r * 0.85), R(r * 0.3, -r * 0.85), R(r * 0.55, -r * 0.55), R(r * 0.52, -r * 0.08)]
    t.trek(crown, 1.8)
    t.trek([R(-r * 0.53, -r * 0.25), R(0, -r * 0.33), R(r * 0.53, -r * 0.25)], 2.6, 0.95)
    t.wash(crown + [R(0, r * 0.1)], 0.42, slip=0.4)
    t.wash(brim, 0.22, slip=0.4)
    t.occlude(np.vstack([brim, crown]))


def dog(t, x, y, s=1.0, facing=1, tilt=0.0):
    """a small dog in a flying leap (all four feet off the ground), ears and tail streaming back;
    facing=-1 leaps to the left; tilt (radians) aims the leap upward"""
    c, sn = np.cos(tilt), np.sin(tilt)
    def P(u, v):
        u, v = u * c - (v - 30) * sn, u * sn + (v - 30) * c + 30
        return (x + facing * u * s, y - v * s)
    w = 1.8
    head = [P(23, 52), P(27, 57.5), P(34, 58.5), P(41, 55.5), P(47.5, 53.5), P(49, 50), P(45, 48.5), P(47, 45.5), P(41, 44.5), P(34, 45), P(27, 46)]
    t.trek(head + [head[0]], w)
    t.dot(*P(37, 53), r=1.6)
    t.dot(*P(48.4, 51.6), r=1.8)
    t.trek([P(45.5, 48.5), P(41, 48)], 1.1, smooth=False, pounce=False)
    ear = [P(28, 56.5), P(20, 57.5), P(12, 55), P(15, 50.5), P(23, 51)]
    t.trek(ear + [ear[0]], w * 0.9)
    t.wash(ear, 0.5, slip=0.3, pool=0.4)
    t.wash(head, 0.08, slip=0.3)
    t.occlude(head + ear)
    for leg in ([P(19, 34), P(31, 30), P(43, 28.5)], [P(16, 31), P(27, 24), P(37, 20)]):
        lp = limb(t, leg, 2.7 * s, 2.0 * s, w * 0.85)
        t.occlude(lp)
    body = [P(-22, 31), P(-14, 38.5), P(-2, 41), P(12, 42.5), P(21, 41), P(26, 36), P(21, 29.5), P(7, 26.5), P(-8, 25.5), P(-19, 26.5)]
    t.trek(body + [body[0]], w)
    patch = [P(-12, 38.5), P(2, 41), P(8, 35), P(-4, 31), P(-14, 33)]
    t.wash(body, 0.1, slip=0.6, holes=[patch])
    t.wash(patch, 0.5, slip=0.3, pool=0.4)
    t.occlude(body)
    for leg in ([P(-15, 29), P(-27, 22), P(-39, 19)], [P(-12, 27), P(-21, 16), P(-31, 10)]):
        limb(t, leg, 3.0 * s, 2.0 * s, w * 0.85)
    t.trek([P(-22, 33), P(-33, 38), P(-42, 44), P(-46, 50)], w * 1.4, taper=(0.05, 0.8))


def laundry(t, x0, x1, y, sag=10):
    """a washing line between two posts; the gust lifts the washing almost level, streaming to the right"""
    t.trek([(x0, y - 3), (x0 - 1, y + 66)], 2.2, smooth=False)
    t.trek([(x1, y - 3), (x1 + 1, y + 66)], 2.2, smooth=False)
    xs = np.linspace(x0, x1, 14)
    yl = lambda x: y + sag * np.sin(np.pi * (x - x0) / (x1 - x0))
    items = [(0.08, 0.3, 40, 'sheet'), (0.42, 0.6, 30, 'shirt'), (0.7, 0.86, 24, 'cloth')]
    for (u0, u1, hh, kind) in items:
        a = (x0 + (x1 - x0) * u0, yl(x0 + (x1 - x0) * u0))
        b = (x0 + (x1 - x0) * u1, yl(x0 + (x1 - x0) * u1))
        wdt = b[0] - a[0]
        if kind == 'shirt':
            q = [a, b, (b[0] + 10, b[1] + 4), (b[0] + 22, b[1] + 10), (b[0] + 18, b[1] + 15), (b[0] + 14, b[1] + 12),
                 (b[0] + 20, b[1] + hh * 0.7), (a[0] + wdt * 0.45 + 18, a[1] + hh * 0.9), (a[0] + 12, a[1] + hh * 0.75),
                 (a[0] + 6, a[1] + 14), (a[0] - 4, a[1] + 15), (a[0] - 2, a[1] + 8)]
        else:
            k = np.linspace(0, 1, 6)
            hem = [(a[0] + 10 + (b[0] + hh * 0.55 - a[0] - 10) * u, a[1] + hh * (0.72 + 0.12 * np.sin(u * 7.5)) - u * hh * 0.25) for u in k]
            q = [a, (a[0] + wdt * 0.5, a[1] - 3), b, (b[0] + hh * 0.35, b[1] + hh * 0.18), (b[0] + hh * 0.6, b[1] + hh * 0.28)] + hem[::-1]
        t.trek(q + [q[0]], 1.4)
        t.trek([(a[0] + wdt * 0.3, a[1] + 4), (a[0] + wdt * 0.5 + hh * 0.2, a[1] + hh * 0.45)], 0.9, 0.6, pounce=False)
        t.wash(q, 0.12, slip=0.6, angle=0.3, pool=0.7)
        for pc in (a, b):
            t.trek([(pc[0], pc[1] + 2), (pc[0], pc[1] - 5)], 1.8, smooth=False, pounce=False)
        t.occlude(q)
    t.trek(np.stack([xs, yl(xs)], 1), 1.1, 0.9)


def main(out, stages=None):
    t0 = time.time()
    t = DelftTile(1920, 1080, tile=128, joint=3.6, origin=(0, -36), seed=11)
    R = t.tableau(2, 1, 13, 8)                    # 11 x 7 tiles: x 256..1664, y 92..988
    # canal edges
    def far_edge(x): return 592 - (x - 299) * 0.008
    def near_edge(x): return 734 - (x - 299) * 0.02

    # ------------------------------------------------------------ the picture, front to back
    t.layer('picture')
    # cartouche reserve at the bottom (kept white, text later)
    cart = [(800, 924), (1120, 924), (1134, 934), (1140, 951), (1134, 968), (1120, 978), (800, 978), (786, 968), (780, 951), (786, 934)]
    t.occlude(cart, grow=0.5)
    man(t, 826, 906, 166)
    hat(t, 958, 690, 22)
    dog(t, 1092, 880, 1.45, facing=-1, tilt=0.3)
    laundry(t, 1250, 1450, 764, sag=12)
    # tulips: a bed on the left, two rows on the right, all bowing to the right
    rng = np.random.default_rng(5)
    for row, (y, x0, x1, hh, n) in enumerate([(940, 316, 704, 56, 12), (904, 334, 690, 46, 12), (934, 1168, 1604, 54, 12), (898, 1186, 1592, 44, 12)]):
        xs = np.linspace(x0, x1, n) + rng.normal(0, 7, n)
        for j, x in enumerate(xs):
            if rng.random() < 0.1: continue                      # a gap in the row
            t.tulip(x, y + rng.normal(0, 4), hh * rng.uniform(0.78, 1.15), lean=0.3 + rng.normal(0, 0.08), width=1.5,
                    tone=0.2 + 0.08 * (row % 2) + rng.normal(0, 0.03), leaves=2 if rng.random() < 0.8 else 1)
    # ground shadows under the running figures
    for (x0, x1, y) in ((786, 868, 910), (1040, 1100, 908)):
        t.trek([(x0, y), ((x0 + x1) / 2, y + 1.5), (x1, y)], 2.2, 0.6, pounce=False, taper=(0.3, 0.3))
        t.trek([(x0 + 8, y + 4), (x1 - 10, y + 4.5)], 1.2, 0.45, pounce=False, taper=(0.3, 0.3))
    # a low post-and-rail fence behind the left bed, leaning a little
    for x in np.arange(318, 720, 46):
        t.trek([(x, 868), (x + 2, 826)], 2.0, smooth=False)
    t.trek([(310, 838), (515, 836), (722, 839)], 1.7)
    t.trek([(310, 856), (515, 853), (722, 857)], 1.5)
    t.grass(310, 760, 870, n=10, h=11, lean=0.5)
    t.grass(1140, 1610, 860, n=10, h=11, lean=0.5)
    t.grass(320, 1600, 790, n=22, h=9, lean=0.5, yspread=20)
    # near bank: boarding along the canal, a path
    xs = np.linspace(299, 1621, 40)
    t.trek(np.stack([xs, near_edge(xs)], 1), 2.2, taper=(0.02, 0.02))
    t.trek(np.stack([xs, near_edge(xs) + 9], 1), 1.3, 0.8, taper=(0.02, 0.02), pounce=False)
    for x in np.arange(312, 1621, 34) + rng.normal(0, 2, 39):
        y = near_edge(x)
        t.trek([(x, y - 3), (x, y + 13)], 1.6, smooth=False, bead=0.05)
    t.wash([(299, near_edge(299)), (1621, near_edge(1621)), (1621, near_edge(1621) + 9), (299, near_edge(299) + 9)], 0.22, slip=0.5)
    for (x0, x1, y) in ((330, 760, 828), (420, 700, 846), (900, 1240, 838), (1470, 1600, 832), (1180, 1260, 852)):
        t.trek([(x0, y), ((x0 + x1) / 2, y - 2), (x1, y + 1)], 1.0, 0.55, pounce=False, taper=(0.3, 0.4))
    for (x, y) in ((760, 820), (1188, 836), (1520, 846), (704, 858)):
        st = ellipse_pts(x, y, 7, 3.5, 0.1, 14)
        t.trek(st[7:], 1.2, 0.8, pounce=False)
        t.wash(st, 0.15, slip=0.3)
    t.occlude([(299, near_edge(299) - 2), (1621, near_edge(1621) - 2), (1621, 945), (299, 945)])
    # the barge, then the water round it
    hull = t.sailboat(636, 676, 300, facing=1, belly=0.5, cargo=7)
    t.occlude(hull)
    for (x, w) in ((1255, 90), (1350, 80), (1452, 96), (1560, 100)):
        t.reflection(x, far_edge(x) + 2, w * 0.8, 70, step=6, width=1.3, dens=0.6)
    t.reflection(470, far_edge(470) + 2, 70, 55, step=6, width=1.3, dens=0.55)
    t.reflection(790, 680, 250, 34, step=5.5, width=1.5, dens=0.75)
    t.water(299, 1621, far_edge(299) + 6, near_edge(1000) - 4, width=1.5, dens=0.8, far=4.2, near=10, avoid=t.occ)
    t.wash([(299, far_edge(299)), (1621, far_edge(1621)), (1621, near_edge(1621)), (299, near_edge(299))], 0.07, angle=0.0, pool=0.3,
           grad=((960, far_edge(960)), (960, near_edge(960)), 1.4, 0.5))
    t.occlude([(299, far_edge(299) + 1), (1621, far_edge(1621) + 1), (1621, near_edge(1621)), (299, near_edge(299))], grow=0)
    # far bank line
    xs = np.linspace(299, 1621, 40)
    t.trek(np.stack([xs, far_edge(xs)], 1), 1.8, taper=(0.02, 0.02))
    t.trek(np.stack([xs, far_edge(xs) - 5], 1), 1.0, 0.7, taper=(0.05, 0.05), pounce=False)
    # houses on the far bank (front to back = left to right is fine, they don't overlap)
    hb = far_edge(1300) - 4
    t.house(1196, 1296, hb, 172, gable='step', gable_h=88, floors=3, chimney=1262, smoke=(70, -18), vane=-1, shade='right')
    t.house(1296, 1392, hb, 146, gable='bell', gable_h=84, floors=3, shade='right')
    t.house(1392, 1500, hb, 186, gable='neck', gable_h=98, floors=3, chimney=1478, smoke=(64, -14), shade='right')
    t.house(1500, 1625, hb, 158, gable='step', gable_h=92, floors=3, shade='right')
    # trees between the barge and the houses
    t.tree(1150, far_edge(1150) - 4, 150, w=104, lean=0.35, clumps=6, seed=3)
    t.tree(1050, far_edge(1050) - 4, 196, w=126, lean=0.4, clumps=8, seed=4)
    # the mill on its dike
    dike = [(299, far_edge(299) - 1), (318, 566), (360, 556), (560, 556), (640, 572), (700, far_edge(700) - 1)]
    t.windmill(455, 560, 232, sails=0.42, squash=0.6, cloth=(1, 3))
    t.trek(dike, 1.8, taper=(0.02, 0.1))
    t.wash(dike + [(299, far_edge(299))], 0.1, angle=0.0, pool=0.5)
    t.grass(320, 690, 566, n=12, h=9, lean=0.6, yspread=6)
    t.occlude(dike + [(700, far_edge(700) + 2), (299, far_edge(299) + 2)])
    # ground on the far bank and the low polder beyond
    t.grass(700, 1040, far_edge(800) - 4, n=8, h=8, lean=0.6)
    t.trek([(560, 538), (760, 534), (1000, 536), (1200, 532)], 1.0, 0.65, pounce=False)
    for (x, hgt) in ((600, 26), (980, 22)):
        t.windmill(x, 512, hgt, sails=0.6, squash=0.7, width=1.1, tone=0.14, gallery=False, door=False, cloth=())
    t.bushes(640, 1190, 511, h=16, gap=[(965, 995)], seed=12)
    t.bushes(304, 340, 511, h=12, seed=13)
    t.trek([(299, 512), (520, 511), (900, 513), (1200, 511)], 1.3, 0.85)
    # sky: clouds and birds
    t.cloud(1000, 215, 430, 120, lean=0.35, seed=8)
    t.cloud(1450, 196, 270, 80, lean=0.35, seed=9)
    t.cloud(690, 196, 180, 60, lean=0.35, seed=10)
    t.birds([(1290, 285), (1318, 270), (1345, 292), (1372, 262), (1400, 280)], size=9, tilt=0.25)
    t.clear_occlusion()
    # inscription in the cartouche
    t.letters('DE WINDVLAAG', 960, 951, 26, font='serif', dens=1.05, spacing=3)

    # ------------------------------------------------------------ the painted frame and the single tiles
    t.layer('frame')
    t.border(R, band=34, inset=9, reserve=[cart])
    t.closed(cart, 2.2)
    for sx in (-1, 1):
        cxs = 960 + sx * 168
        t.trek(arc(cxs, 951, 12, 16, -np.pi / 2, np.pi / 2, 12) if sx > 0 else arc(cxs, 951, 12, 16, np.pi / 2, 3 * np.pi / 2, 12), 1.6)
        t.dot(cxs + sx * 4, 951, 2.4)
    t.layer('single')
    t.field(corners='spin', width=1.35)

    # ------------------------------------------------------------ stages: replay the workshop
    if stages:
        t.stage('tiles', hide=('*',))
        t.stage('pounce', hide=('trek', 'wash'))
        t.stage('outline', hide=('wash', 'frame', 'single'))
        t.stage('wash', hide=('frame', 'single'))
        t.stage('singles')
    t.fire()
    if stages: t.stage('fired')
    t.set_wall()
    if stages: t.stage('set')
    t.age(craze=1.0, chips=12, cracks=[[(1360, 640), (1395, 676), (1440, 700), (1470, 738)]])
    t.light(window=(1488, 178, 112, 150), strength=0.65, soft=6.0)   # window glare over the right cloud
    t.save(out, stages_dir=stages)
    print(f'{out}  {time.time() - t0:.1f}s')


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'delft_canal.jpg'
    st = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    main(out, st)
