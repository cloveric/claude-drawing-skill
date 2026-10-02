"""Example (picture-book character animation / 绘本角色动画): 小橡果的秋天 · An Acorn's Autumn.
A sleepy acorn hangs from an oak branch, wakes as the twig snaps, falls (stretch), lands (squash, impact lines,
dust), bounces, blinks and watches a red oak leaf drift away towards the stream. It gathers itself (anticipation:
squash and lean back), rolls down the hillside -- the hill, its ink horizon, flowers, grass and the far hills are
drawn in just as it passes --, leaps onto the leaf that has landed on the water, floats across while the sun and
clouds are painted in, bumps the far bank, somersaults ashore, wiggles itself into the soil and sprouts into a little
oak that still wears its cap. Then "hello, little oak" writes itself in the sky and confetti flies.
The JPG is the journey poster: the whole world, the acorn multiply-exposed at six key poses on a pencil motion arc.
python3 storybook_acorn.py [out.jpg] [--stages DIR] [--gif out.gif]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from core import spline
from storybook import Storybook, oak_leaf, MINT, LAVENDER, GRASS

argv = sys.argv[1:]
out = argv[0] if argv and not argv[0].startswith('--') else 'storybook_acorn.jpg'
stages = argv[argv.index('--stages') + 1] if '--stages' in argv else None
gif = argv[argv.index('--gif') + 1] if '--gif' in argv else None
t_start = time.time()

U = 44                                          # half-width of the nut, design px
LEFT = [(-40, 604), (140, 598), (330, 594), (480, 592), (575, 598), (660, 620), (750, 660), (840, 716), (915, 774),
        (968, 822), (994, 846)]
LEFT_EDGE = [(1004, 880), (994, 950), (1006, 1020), (998, 1120)]
RIGHT = [(1440, 850), (1490, 823), (1560, 801), (1650, 789), (1760, 791), (1860, 798), (1960, 806)]
RIGHT_EDGE = [(1432, 900), (1444, 980), (1434, 1060), (1442, 1120)]
WATER_Y = 846
LQ, RQ = spline(np.array(LEFT, np.float32), 16), spline(np.array(RIGHT, np.float32), 16)
gy = lambda x: float(np.interp(x, LQ[:, 0], LQ[:, 1])) if x < 1200 else float(np.interp(x, RQ[:, 0], RQ[:, 1]))
slope = lambda x: (gy(x + 2) - gy(x - 2)) / 4

PIVOT = (468, 262)                               # where the acorn's stem hangs from the twig
X0 = 461                                         # where it lands
SPOT = 1650                                      # where it plants itself
STEM = [(1650, 776), (1640, 728), (1656, 672), (1665, 612)]

T_POP, T_SNAP, T_FALL, T_HIT, T_UP, T_HIT2, T_SET = 0.28, 0.58, 0.78, 1.16, 1.28, 1.62, 1.70
T_LOOK, T_ANT, T_ROLL, T_JUMP, T_LEAF, T_FLOAT = 1.90, 2.96, 3.30, 4.46, 4.84, 5.06
T_BUMP, T_HOP, T_LAND, T_DIG, T_GONE, T_SPROUT, T_WRITE, T_END = 6.40, 6.62, 7.00, 7.24, 7.94, 8.00, 8.70, 9.95
LEAF_T0, LEAF_T1, LEAF_X0, LEAF_X1 = 1.90, 4.22, 1150, 1352


def leaf_pose(t):
    """the red oak leaf: drifts down from the oak in swinging arcs, lands on the stream, gets ridden across"""
    if t < LEAF_T0: return None
    if t < LEAF_T1:
        u = (t - LEAF_T0) / (LEAF_T1 - LEAF_T0)
        ph = 2 * np.pi * 2.3 * u
        x = 418 + (LEAF_X0 - 418) * (u ** 1.15) + 80 * np.sin(ph) * (1 - u)
        y = 300 + (WATER_Y - 4 - 300) * u - 16 * np.abs(np.sin(ph)) * (1 - u)
        land = Storybook.ease((u - 0.86) / 0.14, 'out') if u > 0.86 else 0.0
        rot = 32 * np.cos(ph) * (1 - land)
        sx = (0.55 + 0.45 * abs(np.cos(ph * 0.5 + 0.6))) * (1 - land) + land
        sy = 0.8 * (1 - land) + 0.5 * land
        return dict(x=x, y=y, rot=rot, sx=sx, sy=sy)
    bob = 3.0 * np.sin(2 * np.pi * 1.1 * (t - LEAF_T1))
    rot = 2.2 * np.sin(2 * np.pi * 0.85 * (t - LEAF_T1) + 0.4)
    x = LEAF_X0
    if t >= T_FLOAT:
        u = min(1.0, (t - T_FLOAT) / (T_BUMP - T_FLOAT))
        x = LEAF_X0 + (LEAF_X1 - LEAF_X0) * Storybook.ease(u, 'sine')
    if t >= T_BUMP:
        x = LEAF_X1 - 7 * max(0.0, np.sin(np.pi * min(1, (t - T_BUMP) / 0.35)))
    dip = 0.0
    if T_LEAF <= t: dip += 9 * Storybook.spring((t - T_LEAF) / 0.6, 1.3, 3.2)
    if T_HOP <= t: dip += 7 * Storybook.spring((t - T_HOP) / 0.6, 1.3, 3.2)
    return dict(x=x, y=WATER_Y - 4 + bob + dip, rot=rot, sx=1.0, sy=0.5, ghost=T_LEAF <= t <= T_BUMP)


def on_leaf(t):
    p = leaf_pose(t)
    return p['x'] + 4, p['y'] - 9


def shadow_at(x, gyv, height):
    h = np.clip(height / 220, 0, 1)
    return (x, gyv + 2, U * (1.05 - 0.45 * h), 0.24 * (1 - 0.8 * h))


def build(W, H, seed=21):
    sb = Storybook(W, H, seed=seed, actor_size=U)
    E = sb.ease

    # ---------------------------------------------------------------- choreography
    def hang(u, t):
        sc = E((t - T_POP) / 0.25, 'back') if t < T_POP + 0.25 else 1.0
        if t < T_POP: return None
        rot = 6 * np.sin(2 * np.pi * 0.8 * (t - T_POP))
        if t > T_SNAP:
            rot += 13 * np.sin(2 * np.pi * 6 * (t - T_SNAP)) * min(1, (t - T_SNAP) / 0.08)
        x, y = sb.anchor(*PIVOT, rot=rot, scale=sc)
        return dict(x=x, y=y, rot=rot, scale=sc, eyes=0, lid='sleep', mouth='smile', lead=False)

    hx, hy = sb.anchor(*PIVOT)
    yg_end = sb.rest(X0, gy(X0), k=1.36)[1]

    def fall(u, t):
        y = hy + (yg_end - hy) * u * u
        k = 1 + 0.36 * u ** 1.5
        x = hx + (X0 - hx) * u
        o = 0.0 if u < 0.12 else 1.0
        return dict(x=x, y=y, k=k, eyes=o, lid='sleep', mouth='o' if u > 0.12 else 'smile', brow='up' if u > 0.12 else None,
                    look=(0, 0.6), shadow=shadow_at(X0, gy(X0), yg_end - y), lead=False, speed=False)

    def hit(u, t):
        k = 0.62 + (1.12 - 0.62) * E(u, 'out') if u > 0.45 else 0.62
        x, y = sb.rest(X0, gy(X0), k=k)
        return dict(x=x, y=y, k=k, eyes=0.1, lid='blink', mouth='o', shadow=shadow_at(X0, gy(X0), 0), lead=False,
                    speed=False)

    def bounce(u, t):
        k = 1 + 0.14 * abs(1 - 2 * u) ** 2
        x, y0 = sb.rest(X0, gy(X0), k=k)
        h = 72 * 4 * u * (1 - u)
        return dict(x=x, y=y0 - h, k=k, eyes=1, mouth='o', brow='up', look=(0, -0.3),
                    shadow=shadow_at(X0, gy(X0), h), lead=False)

    def settle(u, t):
        k = 1 - 0.2 * Storybook.spring(u, 1.4, 4.0) if t < T_SET else 1 - 0.08 * Storybook.spring(u, 1.2, 3.0)
        x, y = sb.rest(X0, gy(X0), k=k)
        return dict(x=x, y=y, k=k, eyes=1 if u > 0.15 else 0.15, mouth='flat', shadow=shadow_at(X0, gy(X0), 0), lead=False)

    def look(u, t):
        x, y = sb.rest(X0, gy(X0))
        lp = leaf_pose(t)
        ex, ey = lp['x'] - x, lp['y'] - (y - 10)
        n = np.hypot(ex, ey) + 1e-6
        lk = (ex / n, ey / n)
        blink = 1.0
        for tb in (2.02, 2.62):
            if tb <= t < tb + 0.14: blink = abs(np.cos(np.pi * (t - tb) / 0.14))
        rot = -5 * lk[0]
        k = 1 + 0.03 * np.sin(2 * np.pi * 1.5 * (t - T_LOOK))
        x, y = sb.rest(X0, gy(X0), rot=rot, k=k)
        return dict(x=x, y=y, rot=rot, k=k, eyes=blink, look=lk, brow='up', mouth='flat' if t < 2.45 else 'o',
                    shadow=shadow_at(X0, gy(X0), 0), lead=False)

    def anticipate(u, t):
        a = E(min(1, u / 0.62), 'out')
        k = 1 - 0.24 * a
        rot = 13 * a
        jit = 1.3 * np.sin(t * 90) if u > 0.62 else 0.0
        x, y = sb.rest(X0 - 10 * a + jit, gy(X0), rot=rot, k=k)
        return dict(x=x, y=y, rot=rot, k=k, eyes=0.85, look=(1, 0.15), brow='determined', mouth='flat',
                    shadow=shadow_at(X0, gy(X0), 0), lead=False)

    XR0, XR1 = X0 - 10, 966

    def roll_at(u):
        f = 0.3 * u + 0.7 * u * u
        x = XR0 + (XR1 - XR0) * f
        m = slope(x)
        n = np.array([m, -1.0]); n /= np.linalg.norm(n)
        rot = 13 - (x - XR0) / U * 57.2958 * 0.7
        sp = (0.3 + 1.4 * u) / 1.7
        k = 1 + 0.12 * sp
        axis = -np.degrees(np.arctan(m))
        cx, cy = sb.rest(x, gy(x), rot=rot, k=k, axis=axis, normal=n)
        return cx, cy, rot, k, axis, x

    def roll(u, t):
        cx, cy, rot, k, axis, x = roll_at(u)
        return dict(x=cx, y=cy, rot=rot, k=k, axis=axis, eyes=1, mouth='grin', brow='up', look=(1, 0.2),
                    shadow=shadow_at(x, gy(x), 0), speed_min=420)

    p0 = roll_at(1.0)
    rot0 = p0[2]
    rot_up = -360.0 * np.ceil(-rot0 / 360.0)
    land_leaf = sb.rest(*on_leaf(T_LEAF))

    def leap(u, t):
        x, y = Storybook.arc(p0[:2], land_leaf, 70, u)
        xa, ya = Storybook.arc(p0[:2], land_leaf, 70, max(0, u - 0.03))
        xb, yb = Storybook.arc(p0[:2], land_leaf, 70, min(1, u + 0.03))
        axis = np.degrees(np.arctan2(-(yb - ya), xb - xa))
        k = 1 + 0.2 * abs(1 - 2 * u) ** 1.5
        rot = rot0 + (rot_up - rot0) * E(u, 'out')
        return dict(x=x, y=y, rot=rot, k=k, axis=axis, eyes=1, mouth='grin', brow='up', look=(1, 0.5),
                    speed_min=420)

    def ride(u, t):
        lp = leaf_pose(t)
        lp_lag = leaf_pose(t - 0.12)
        if t < T_FLOAT:
            uu = (t - T_LEAF) / (T_FLOAT - T_LEAF)
            k = 1 - 0.3 * Storybook.spring(uu, 1.1, 3.5)
            eyes, mouth = (0.1, 'grin') if uu < 0.35 else (1, 'smile')
        else:
            k = 1 + 0.025 * np.sin(2 * np.pi * 1.1 * (t - T_FLOAT))
            eyes, mouth = 1, 'smile'
        rot = (lp_lag['rot'] if lp_lag else 0) * 1.6
        blink = 1.0
        for tb in (5.55, 6.15):
            if tb <= t < tb + 0.14: blink = abs(np.cos(np.pi * (t - tb) / 0.14))
        x, y = sb.rest(*on_leaf(t), rot=rot, k=k)
        look = (0.55, -0.7) if t > 5.3 else (0.2, 0.3)
        return dict(x=x, y=y, rot=rot, k=k, eyes=eyes * blink, lid='happy', mouth=mouth, look=look, speed=False)

    def bump(u, t):
        if t < T_BUMP + 0.1:
            k = 1 - 0.15 * np.sin(np.pi * u * 2.2)
            rot = -6 * np.sin(np.pi * u * 2.2)
        else:
            a = E((t - T_BUMP - 0.1) / (T_HOP - T_BUMP - 0.1), 'out')
            k = 1 - 0.2 * a; rot = 8 * a
        x, y = sb.rest(*on_leaf(t), rot=rot, k=k)
        return dict(x=x, y=y, rot=rot, k=k, eyes=1, look=(1, -0.2), brow='determined', mouth='flat', speed=False)

    hop0 = sb.rest(*on_leaf(T_HOP), rot=8, k=0.8)
    hop1 = sb.rest(SPOT, gy(SPOT), k=1.2)

    def hop(u, t):
        x, y = Storybook.arc(hop0, hop1, 135, u)
        xa, ya = Storybook.arc(hop0, hop1, 135, max(0, u - 0.03))
        xb, yb = Storybook.arc(hop0, hop1, 135, min(1, u + 0.03))
        axis = np.degrees(np.arctan2(-(yb - ya), xb - xa))
        k = 1 + 0.22 * abs(1 - 2 * u) ** 1.5
        rot = 8 - 368 * E(u, 'inout')
        return dict(x=x, y=y, rot=rot, k=k, axis=axis, eyes=0.1 if 0.2 < u < 0.8 else 1, lid='happy', mouth='grin',
                    brow='up', shadow=shadow_at(x, gy(x), gy(x) - y - U * 1.2), speed_min=500)

    def land(u, t):
        k = 1 - 0.34 * Storybook.spring(u, 1.2, 3.2)
        x, y = sb.rest(SPOT, gy(SPOT), k=k)
        return dict(x=x, y=y, k=k, eyes=0.1 if u < 0.25 else 1, lid='happy', mouth='grin' if u < 0.5 else 'smile',
                    shadow=shadow_at(SPOT, gy(SPOT), 0), speed=False)

    def dig(u, t):
        tt = t - T_DIG
        if tt < 0.16:
            x, y = sb.rest(SPOT, gy(SPOT))
            return dict(x=x, y=y, eyes=1, look=(0, 1), mouth='smile', shadow=shadow_at(SPOT, gy(SPOT), 0), speed=False)
        v = (tt - 0.16) / (T_GONE - T_DIG - 0.16)
        rot = 15 * np.sin(2 * np.pi * 6.5 * (tt - 0.16)) * (1 - 0.4 * v)
        x, y = sb.rest(SPOT, gy(SPOT), rot=rot)
        return dict(x=x, y=y + 2.95 * U * E(v, 'in2'), rot=rot, eyes=0, lid='happy', mouth='smile',
                    clip=gy(SPOT) + 3, speed=False)

    SQ = spline(np.array(STEM, np.float32), 16)
    seg = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(SQ, axis=0).T))])

    def stem_at(p):
        s_ = p * seg[-1]
        return float(np.interp(s_, seg, SQ[:, 0])), float(np.interp(s_, seg, SQ[:, 1]))

    def sprout(u, t):
        p = min(1.0, (t - T_SPROUT) / 0.55)
        tx, ty = stem_at(max(p, 0.02))
        rot = 14 + 9 * Storybook.spring(max(0, t - T_SPROUT - 0.5) / 0.8, 1.5, 3.0) * (t > T_SPROUT + 0.5)
        x, y = sb.anchor(tx, ty + 2, local=(0.0, -0.2), rot=rot, scale=0.62)
        return dict(x=x, y=y, rot=rot, scale=0.62, only='cap', clip=gy(SPOT) - 4 if p < 0.2 else None, speed=False)

    sb.act(0.0, T_FALL, hang)
    sb.act(T_FALL, T_HIT, fall)
    sb.act(T_HIT, T_UP, hit)
    sb.act(T_UP, T_HIT2, bounce)
    sb.act(T_HIT2, T_LOOK, settle)
    sb.act(T_LOOK, T_ANT, look)
    sb.act(T_ANT, T_ROLL, anticipate)
    sb.act(T_ROLL, T_JUMP, roll)
    sb.act(T_JUMP, T_LEAF, leap)
    sb.act(T_LEAF, T_BUMP, ride)
    sb.act(T_BUMP, T_HOP, bump)
    sb.act(T_HOP, T_LAND, hop)
    sb.act(T_LAND, T_DIG, land)
    sb.act(T_DIG, T_GONE, dig)
    sb.act(T_GONE, T_SPROUT, lambda u, t: None)
    sb.act(T_SPROUT, T_END, sprout)

    # ---------------------------------------------------------------- the world, painted in as it is reached
    LEAD = 150
    sb.hill([(-40, 492), (220, 466), (460, 494), (700, 472), (950, 514), (1200, 482), (1460, 510), (1720, 470),
             (1960, 494)], LAVENDER, bottom=760, z=2, follow=300, xa=-40, xb=1960, pre=(1.95, 2.85, 0.3))
    sb.hill([(-40, 560), (260, 544), (540, 574), (800, 626), (1040, 662), (1260, 652), (1480, 624), (1720, 612),
             (1960, 632)], MINT, bottom=1120, z=3, follow=360, xa=-40, xb=1960, pre=(1.95, 2.85, 0.3))
    sb.tree(226, 600, 250, [(160, 190, 125), (285, 150, 118), (368, 202, 76), (105, 290, 92), (250, 262, 108)],
            branch=[[(232, 372), (300, 332), (380, 292), (440, 262), (494, 243)], [(456, 252), (468, 264)],
                    [(220, 430), (172, 392), (140, 350)]], when=(0.0, 0.55), z=7.0, trunk=15)
    sb.water(975, 1455, WATER_Y, when=(3.7, 5.3), z=8.5)
    sb.land(LEFT, GRASS, z=12, follow=60, xa=-40, xb=1000, pre=(1.95, 2.9, 0.58), right_edge=LEFT_EDGE, dashes=70)
    sb.ground(LEFT, z=20, follow=LEAD, xa=-40, xb=1000, pre=(0.05, 0.5, 0.6))
    sb.land(RIGHT, GRASS, z=12, follow=230, xa=1430, xb=1960, left_edge=RIGHT_EDGE, dashes=40)
    sb.ground(RIGHT, z=20, follow=300, xa=1430, xb=1960)
    sb.sun(1705, 205, 62, when=(5.2, 5.95))
    sb.cloud(705, 150, 190, when=(3.75, 4.1))
    sb.cloud(1452, 118, 250, when=(5.55, 5.95))
    sb.cloud(1080, 168, 150, when=(4.6, 4.95))
    # little things along the way (the plateau ones while the acorn looks around)
    sb.tuft(355, gy(355) + 2, when=(2.1, 2.35))
    sb.leaf_on_ground(300, gy(300) - 2, 24, '#d9603a', when=(2.25, 2.5))
    sb.tuft(120, gy(120) + 2, when=(2.35, 2.6))
    for x, kind in [(640, 'aster'), (795, 'daisy')]:
        w0 = sb.when_at(x, 40, 0.42)
        sb.flower(x, gy(x) + 2, 80 if kind == 'aster' else 66, kind, '#b48ae0' if kind == 'aster' else '#fdfbf6',
                  when=w0, lean=0.06)
    for x in (585, 705, 880):
        sb.tuft(x, gy(x) + 2, when=sb.when_at(x, 50, 0.22))
    for x, c in [(560, '#d9603a'), (858, '#e89a3a')]:
        sb.leaf_on_ground(x, gy(x) - 2, 24, c, when=sb.when_at(x, 40, 0.25))
    sb.cattail(950, gy(950) + 2, 150, when=sb.when_at(900, 0, 0.45), lean=0.1)
    sb.cattail(1482, gy(1482) + 2, 175, when=(5.9, 6.4), lean=-0.06)
    sb.cattail(1515, gy(1515) + 2, 128, when=(6.05, 6.5), lean=0.05)
    sb.tuft(1575, gy(1575) + 2, when=(6.3, 6.5))
    sb.flower(1800, gy(1800) + 2, 74, 'aster', '#e8739b', when=(6.4, 6.85), lean=-0.05)
    sb.tuft(1888, gy(1888) + 2, when=(6.55, 6.8))
    sb.leaf_on_ground(1745, gy(1745) - 2, 24, '#d9603a', when=(6.6, 6.85))
    # the planting
    sb.mound(SPOT, gy(SPOT) + 3, 122, 30, when=(T_DIG + 0.1, T_DIG + 0.4), z=55)
    sb.ink(STEM, 5.2, '#2f5a3c', z=56, when=(T_SPROUT, T_SPROUT + 0.55), taper=(0.0, 0.08), tremor=0.3,
           name='sapling')
    for p, ang, ln in [(0.36, 162, 56), (0.52, 20, 62), (0.72, 152, 52), (0.88, 32, 46)]:
        bx, by = stem_at(p)
        lf, mid = oak_leaf(ln, ln * 0.5, 2, (bx, by), ang, curl=0.05, seed=int(p * 100))
        tl = T_SPROUT + p * 0.55
        sb.shape([lf], '#7cc36a', '#2c4a33', 2.2, z=56.5, when=(tl, tl + 0.28), pop=(bx, by), dark='#4f9a4c',
                 name='sapling_leaf')
    # the leaf boat
    out_l, mid_l = oak_leaf(150, 64, 3, (-75, 0), 0, curl=0.04, seed=4)
    veins = [mid_l] + [[(mid_l[i][0], mid_l[i][1]), (mid_l[i][0] + 16, mid_l[i][1] + sgn * 20)]
                       for i, sgn in [(25, -1), (40, 1), (55, -1), (68, 1)]]
    veins.append([(-75, 0), (-92, 4)])
    leaf_sp = sb.sprite([out_l], '#e0703a', '#2a1d16', 2.8, veins=veins, dark='#b8452a')
    sb.prop(leaf_sp, LEAF_T0, T_END, lambda u, t: leaf_pose(t), z=45)
    # FX
    sb.fx('impact', T_HIT, X0, gy(X0), r=62, n=7)
    sb.fx('dust', T_HIT, X0, gy(X0), n=6, spread=60)
    sb.fx('dust', T_HIT2, X0, gy(X0), n=4, spread=34, size=8)
    for tt in (T_ROLL, T_ROLL + 0.3, T_ROLL + 0.58, T_ROLL + 0.84):
        x = roll_at((tt - T_ROLL) / (T_JUMP - T_ROLL))[5]
        sb.fx('dust', tt, x - 20, gy(x - 20), n=4, spread=46, size=9, dirs=(-1,))
    sb.fx('ripple', T_LEAF, on_leaf(T_LEAF)[0], WATER_Y + 4, r=110, n=3)
    sb.fx('ripple', LEAF_T1 - 0.05, LEAF_X0, WATER_Y + 2, r=60, n=1, life=0.7)
    for tt in np.arange(T_FLOAT + 0.25, T_BUMP, 0.42):
        sb.fx('ripple', tt, leaf_pose(tt)['x'] - 70, WATER_Y + 6, r=50, n=1, life=0.7)
    sb.fx('ripple', T_HOP, on_leaf(T_HOP)[0], WATER_Y + 4, r=80, n=2)
    sb.fx('impact', T_LAND, SPOT, gy(SPOT), r=60, n=7)
    sb.fx('dust', T_LAND, SPOT, gy(SPOT), n=6, spread=60)
    for tt in (T_DIG + 0.25, T_DIG + 0.45, T_DIG + 0.62):
        sb.fx('specks', tt, SPOT, gy(SPOT) - 4, n=7)
    sb.fx('sparkle', T_SPROUT + 0.5, 1600, 618, r=18)
    sb.fx('sparkle', T_SPROUT + 0.6, 1726, 676, r=14, colour='#ee8a3c')
    sb.fx('sparkle', T_SPROUT + 0.7, 1712, 580, r=12)
    sb.fx('confetti', T_WRITE + 0.6, 1000, 470, n=120, spread=1500, up=1100, life=2.6, stagger=0.3, wide=640)
    sb.write('hello, little oak', 1000, 318, 138, when=(T_WRITE, T_WRITE + 1.0), underline=((700, 1290), 400))
    return sb, stem_at


if __name__ == '__main__':
    sb, _ = build(1920, 1080)
    if stages:
        for name, t in [('tree', 0.55), ('fall', 1.02), ('squash', 1.18), ('watch_leaf', 2.5), ('ready', 3.2),
                        ('roll', 3.95), ('float', 5.7), ('hop', 6.82), ('dig', 7.7), ('sprout', 8.75), ('write', 9.95)]:
            sb.stage(name, t)
    sb.journey([1.0, T_HIT + 0.02, 4.06, 4.66, 5.78, 6.83], t_world=T_END, arc=(0.8, 7.62),
               labels=[('whoa!', 105, -10), ('plop!', -95, -70), ('wheee!', 70, -95), ('hop!', 20, -105),
                       ('la la', 0, -110), ('up we go', 0, -118)],
               prop_arcs=[(LEAF_T0, LEAF_T1, lambda u, t: leaf_pose(t))], world_fx=True, props=False)
    sb.save(out, stages)
    print(f'{out}  {time.time() - t_start:.1f}s')
    if gif:
        t1 = time.time()
        del sb
        g, _ = build(720, 405)
        n = g.gif(gif, fps=15, t_end=T_END, hold=1.4)
        print(f'{gif}  {n} frames  {os.path.getsize(gif) / 1e6:.2f} MB  {time.time() - t1:.1f}s')
