"""Example (ballpoint doodle): Snakes & Ladders, Round 7 / 蛇梯棋大冒险 — a snakes-and-ladders board drawn with
ballpoint pens on a sheet of copy paper during a lunch break, coloured in with pencils, and a game in progress:
the die has just been thrown (it bounced across the margin and came up 4); the snail hopped four squares from 10
to 14, landed on the foot of the long ladder and is climbing it to 38 (red hops counted 1-2-3-4, a red ring, a
dashed arrow up the ladder, +24!); the cloud, who was on 47, is sliding down the green snake to 18; the dice
monster waits on 51 and looks worried. Margin doodles (bunting, a sun, a tic-tac-toe game, a paper plane, a house
on a hill, a flower pot, stars), a note complaining about the snake, the score card, a word crossed out and
written again, the conclusion in red -- and the ghost of a shopping list pressed through from the sheet above.
No image model.
python3 ballpoint_board_game.py [out.png] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from ballpoint import Ballpoint
from core import spline, blur, smoothstep

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'ballpoint_board_game.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
T0 = time.time()
tick = lambda name: print(f'{name:16s} {time.time() - T0:5.1f}s') if os.environ.get('BALLPOINT_TIMING') else None

W, H = 1920, 1080
b = Ballpoint(W, H, seed=7)
rng = b.rng
b.paper(folds=[((-40, 548), (1960, 530))], cockle=1.0)
tick('paper')

# ===================================================================== the board: geometry
CS, N = 94.0, 8
BX0, BY1 = 584.0, 898.0                      # left edge, bottom edge
CX, CY = BX0 + CS * 4, BY1 - CS * 4
ROT = np.deg2rad(-0.8)
jx = rng.normal(0, 1.8, N + 1); jy = rng.normal(0, 1.8, N + 1)


def B(u, v):
    """board coordinates (u columns from the left, v rows from the bottom; cell centres at k + 0.5) -> canvas"""
    u, v = np.asarray(u, np.float32), np.asarray(v, np.float32)
    x = BX0 + CS * u + np.interp(u, np.arange(N + 1), jx)
    y = BY1 - CS * v + np.interp(v, np.arange(N + 1), jy)
    dx, dy = x - CX, y - CY
    return np.stack([CX + dx * np.cos(ROT) - dy * np.sin(ROT), CY + dx * np.sin(ROT) + dy * np.cos(ROT)], -1)


def cell(n):
    r = (n - 1) // N; k = (n - 1) % N
    c = k if r % 2 == 0 else N - 1 - k
    return c, r


def ctr(n, du=0.0, dv=0.0):
    c, r = cell(n)
    return B(c + 0.5 + du, r + 0.5 + dv)


def uvpath(ctrl, per=12):
    return spline(B([p[0] for p in ctrl], [p[1] for p in ctrl]), per)


def xf(pts, cx, cy, s=1.0, rot=0.0):
    """local doodle coordinates -> canvas"""
    P = np.asarray(pts, np.float32) * s
    a = np.deg2rad(rot); c, sn = np.cos(a), np.sin(a)
    return np.stack([cx + P[:, 0] * c - P[:, 1] * sn, cy + P[:, 0] * sn + P[:, 1] * c], 1)


# ---- snakes: (control points head -> tail in board units, head width, body pencil, band pencil)
SNAKES = [
    ([(1.5, 5.4), (0.62, 4.98), (0.52, 4.25), (1.3, 3.78), (2.25, 3.42), (2.38, 2.88), (1.75, 2.58), (1.45, 2.45)], 54, 'green', 'yellow'),
    ([(2.6, 7.42), (3.42, 7.18), (3.66, 6.58), (3.25, 6.08), (3.8, 5.7), (4.45, 5.5)], 44, 'orange', 'rose'),
    ([(7.42, 7.45), (6.82, 7.02), (7.02, 6.42), (6.55, 5.98), (6.5, 5.55)], 38, 'lilac', 'violet'),
]
# ---- ladders: (from square, to square)
LADDERS = [(14, 38), (23, 41)]


def snake_geom(ctrl, w0):
    P = Ballpoint.resample(uvpath(ctrl, 12), 3.0)
    hd = P[0] - P[7]; hd /= np.linalg.norm(hd)
    k0 = 4
    L, R = Ballpoint.tube_sides(P[k0:], w0 * 0.8, 6.0, smooth=False)
    hc = P[0] + hd * 4
    return dict(P=P, hd=hd, hc=hc, L=L, R=R, rx=w0 * 0.66, ry=w0 * 0.58, w0=w0)


SG = [snake_geom(c, w) for c, w, _, _ in SNAKES]


def snake_mask(g):
    m = b.tube(g['P'][4:], g['w0'] * 0.8, 6.0)
    ang = np.degrees(np.arctan2(g['hd'][1], g['hd'][0]))
    return np.clip(m + b.ellipse(g['hc'][0], g['hc'][1], g['rx'], g['ry'], rot=ang), 0, 1)


# ---- pieces
LAD = (ctr(14), ctr(38))
SNAIL = (LAD[0] + (LAD[1] - LAD[0]) * 0.55 + np.array([2, -12]), 1.1, -38.0)        # (centre, scale, rotation)
CLOUD = (B(1.78, 3.66) + np.array([0, -30]), 1.3, 16.0)
DICEM = (ctr(51, 0.0, 0.02), 1.12)
DIE = (np.array([1520.0, 652.0]), 1.0)

SNAIL_BODY = [(-56, 12), (-30, 17), (0, 19), (28, 18), (46, 12), (54, -4), (53, -24), (43, -37), (31, -33), (26, -17),
              (12, -7), (-14, -3), (-40, 3), (-58, 9)]
SNAIL_SHELL = (-7, -27, 30)


def snail_masks():
    (c, s, rot) = SNAIL
    body = b.poly(xf(spline(np.vstack([SNAIL_BODY, SNAIL_BODY[:1]]), 8), c[0], c[1], s, rot))
    sc = xf([SNAIL_SHELL[:2]], c[0], c[1], s, rot)[0]
    shell = b.ellipse(sc[0], sc[1], SNAIL_SHELL[2] * s, SNAIL_SHELL[2] * s * 0.96)
    return body, shell


def cloud_pts():
    (c, s, rot) = CLOUD
    P = Ballpoint.cloud_pts(0, 0, 104, 66, bumps=7, seed=5)
    return xf(P, c[0], c[1], s, rot)


def cube_pts(cx, cy, a, dx, dy):
    """front square (side a, centred) plus the top and right faces of a cube seen from the upper right"""
    x0, y0, x1, y1 = cx - a / 2, cy - a / 2, cx + a / 2, cy + a / 2
    front = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], np.float32)
    top = np.array([(x0, y0), (x0 + dx, y0 - dy), (x1 + dx, y0 - dy), (x1, y0)], np.float32)
    side = np.array([(x1, y0), (x1 + dx, y0 - dy), (x1 + dx, y1 - dy), (x1, y1)], np.float32)
    return front, top, side


def face_pt(q, u, v):
    """a point on a cube face given as 4 corners (u along the last edge, v along the first)"""
    return q[0] + (q[1] - q[0]) * v + (q[3] - q[0]) * u


def dicem_geom():
    (c, s) = DICEM
    return cube_pts(c[0] - 6, c[1] + 6, 48 * s, 16 * s, 15 * s)


# exclusion: where the grid lines stop and the squares are not coloured
smasks = [snake_mask(g) for g in SG]
sn_body, sn_shell = snail_masks()
cl_mask = b.poly(cloud_pts())
f_, t_, s_ = dicem_geom()
dm_mask = np.clip(b.poly(f_) + b.poly(t_) + b.poly(s_), 0, 1)
EX = np.clip(sum(smasks) + sn_body + sn_shell + cl_mask + dm_mask, 0, 1)
EXC = 1 - smoothstep(0.03, 0.3, blur(EX, 3.0))
PIECEC = 1 - smoothstep(0.03, 0.3, blur(np.clip(sn_body + sn_shell + cl_mask + dm_mask, 0, 1), 2.0))
tick('geometry')

# ===================================================================== 1. pen: the pieces and the die (drawn first, the board goes round them)
# -- snail climbing the ladder
(c, s, rot) = SNAIL
sc = xf([SNAIL_SHELL[:2]], c[0], c[1], s, rot)[0]
b.line(b.circle_pts(sc[0], sc[1], SNAIL_SHELL[2] * s, SNAIL_SHELL[2] * s * 0.96, a0=-100, a1=255), 'black', 0.85, hook=0.3, twice=0.5)
b.line(b.spiral_pts(sc[0] + 2, sc[1] + 1, SNAIL_SHELL[2] * s * 0.74, turns=2.1, a0=rot + 180), 'black', 0.8, smooth=False, hook=0.2)
body_pts = xf(spline(SNAIL_BODY, 8), c[0], c[1], s, rot)
b.line(body_pts, 'black', 0.82, clip=1 - smoothstep(0.2, 0.8, blur(sn_shell, 1.0)), hook=0.2)
for (p0, p1) in [((33, -34), (27, -55)), ((46, -33), (53, -53))]:
    q = xf([p0, p1], c[0], c[1], s, rot)
    b.line(q, 'black', 0.8, smooth=False, hook=0)
    b.dot(q[1][0], q[1][1], 3.6, 'black')
fc = xf([(41, -17)], c[0], c[1], s, rot)[0]
b.face(fc[0], fc[1], 44, 'grin', 'black', blush=None, rot=rot * 0.4)
for k in range(3):                                          # little slime marks on the rung below
    q = xf([(-62 - k * 9, 20 + k * 3), (-68 - k * 9, 22 + k * 3)], c[0], c[1], s, rot)
    b.line(q, 'black', 0.6, smooth=False, hook=0, gloop=0.1)

# -- cloud sliding down the green snake
(c, s, rot) = CLOUD
b.line(cloud_pts(), 'blue', 0.85, closed=True, twice=0.6, hook=0.3)
b.face(c[0] + 2, c[1] + 4, 84, 'dizzy', 'blue', blush=None, rot=rot)
for (dx, dy) in [(62, -32)]:                                         # a sweat drop
    q = xf([(dx, dy)], c[0], c[1], s, rot)[0]
    drop = [(q[0], q[1] - 9), (q[0] + 4.5, q[1] - 1), (q[0] + 4, q[1] + 4), (q[0], q[1] + 6), (q[0] - 4, q[1] + 4), (q[0] - 4.5, q[1] - 1)]
    b.line(drop, 'blue', 0.75, closed=True, hook=0)
g1 = SG[0]['P']                                                      # its slide, dashed down the snake's back
j = int(np.argmin(np.hypot(*(g1 - c).T)))
P = b.dashes(g1[14:max(16, j - 30)], 'blue', 8, 6, 0.72, smooth=False)
b.arrow(P[-1], P[-1] - P[-6], 10, 'blue', 0.8)

# -- dice monster on 51, worried
front, top, side = dicem_geom()
(c, s) = DICEM
b.line(front, 'blue', 0.85, closed=True, smooth=False, twice=0.5)
b.line([top[0], top[1], top[2], top[3]], 'blue', 0.82, smooth=False, hook=0.2)
b.line([side[1], side[2], side[3]], 'blue', 0.82, smooth=False, hook=0.2)
fcx, fcy = front[:, 0].mean(), front[:, 1].mean()
b.face(fcx, fcy + 2, 46, 'worry', 'blue', blush=None)
for (u, v) in [(0.3, 0.3), (0.7, 0.7)]:
    p = face_pt(top, u, v); b.dot(p[0], p[1], 2.6, 'blue')
for (u, v) in [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)]:
    p = face_pt(np.array([side[0], side[3], side[2], side[1]]), v, u); b.dot(p[0], p[1], 2.4, 'blue')
for sx in (-11, 11):                                                 # legs and feet
    b.line([(fcx + sx, front[2, 1]), (fcx + sx + sx * 0.15, front[2, 1] + 11)], 'blue', 0.8, smooth=False, hook=0)
    b.line(b.circle_pts(fcx + sx * 1.3, front[2, 1] + 14, 6, 3.5), 'blue', 0.75, closed=True, hook=0)
b.line([(front[0, 0], fcy + 4), (front[0, 0] - 12, fcy - 6), (front[0, 0] - 15, fcy - 18)], 'blue', 0.8, hook=0.2)   # hands to cheeks
b.line([(side[2, 0] - 2, fcy + 6), (side[2, 0] + 10, fcy - 2), (side[2, 0] + 14, fcy - 14)], 'blue', 0.8, hook=0.2)
b.write('!?', front[0, 0] - 22, front[0, 1] - 2, 30, 'blue', 0.85, anchor='r', rot=-8)

# -- the die, just thrown, in the right margin
(c, s) = DIE
front_d, top_d, side_d = cube_pts(c[0], c[1], 62, 24, 22)
b.line(front_d, 'black', 0.85, closed=True, smooth=False, twice=0.6)
b.line([top_d[0], top_d[1], top_d[2], top_d[3]], 'black', 0.85, smooth=False, hook=0.2)
b.line([side_d[1], side_d[2], side_d[3]], 'black', 0.85, smooth=False, hook=0.2)
for (u, v) in [(0.27, 0.27), (0.73, 0.27), (0.27, 0.73), (0.73, 0.73)]:          # four on top
    p = face_pt(top_d, u, v); b.dot(p[0], p[1], 3.4, 'black')
fc_ = front_d.mean(0)
for (u, v) in [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]:                   # five in front
    b.dot(fc_[0] + u * 17, fc_[1] + v * 17, 3.6, 'black')
scc = side_d.mean(0)
b.dot(scc[0], scc[1], 4.6, 'red')                                             # the one, in red
b.stage('pen_pieces')
tick('pieces')

# ===================================================================== 2. pen: snakes and ladders (they stop at the pieces)
for g, (ctrl, w0, col, band) in zip(SG, SNAKES):
    ang = np.degrees(np.arctan2(g['hd'][1], g['hd'][0]))
    # head: from one side of the neck round the snout to the other
    head = b.circle_pts(g['hc'][0], g['hc'][1], g['rx'], g['ry'], a0=148, a1=-148, rot=ang)
    b.line(head[::-1], 'blue', 0.85, smooth=True, hook=0.2, twice=0.5, clip=PIECEC)
    # one stroke down the left side, round the tail tip, back up the right side
    tip = g['P'][-1] + (g['P'][-1] - g['P'][-3]) / 2.0
    body = np.vstack([g['L'], [tip], g['R'][::-1]])
    b.line(body, 'blue', 0.82, smooth=True, hook=0.3, twice=0.55, clip=PIECEC)
    # eyes and tongue
    hd, nv = g['hd'], np.array([-g['hd'][1], g['hd'][0]])
    for sg in (-1, 1):
        e = g['hc'] + hd * g['rx'] * 0.12 + nv * sg * g['ry'] * 0.46
        b.eye(e[0], e[1], g['w0'] * 0.13, g['w0'] * 0.15, 'black', look=(hd[0], hd[1]))
    t0 = g['hc'] + hd * (g['rx'] + 1)
    t1 = t0 + hd * 14
    b.line([t0, t1], 'red', 0.85, smooth=False, hook=0, gloop=0.2)
    for sg in (-1, 1):
        b.line([t1, t1 + hd * 7 + nv * sg * 5], 'red', 0.8, smooth=False, hook=0, gloop=0.2)

LG = []
for (n0, n1) in LADDERS:
    A, Bp = ctr(n0, 0.0, -0.1), ctr(n1, 0.0, 0.12)
    d = (Bp - A) / np.linalg.norm(Bp - A); nv = np.array([-d[1], d[0]])
    L_ = np.linalg.norm(Bp - A)
    half = 15.0
    rails = [(A + nv * sg * half - d * 6, Bp + nv * sg * half + d * 8) for sg in (-1, 1)]
    for r0, r1 in rails:
        b.line([r0, r1], 'black', 0.82, bow=0.004, hook=0.2, twice=0.5, clip=PIECEC)
    rungs = []
    for s in np.arange(16, L_ - 6, 25):
        p = A + d * (s + rng.normal(0, 1.2))
        rungs.append([p + nv * (half + rng.uniform(-1, 2)), p - nv * (half + rng.uniform(-1, 2.5)) + d * rng.normal(0, 1.2)])
    b.lines(rungs, 'black', 0.8, smooth=False, hook=0.15, gloop=0.35, clip=PIECEC)
    LG.append(dict(A=A, B=Bp, d=d, nv=nv, half=half, L=L_, rungs=rungs))
b.stage('pen_snakes_ladders')
tick('snakes')

# ===================================================================== 3. pen: the grid, numbers, the way round
for i in range(N + 1):
    for horiz in (False, True):
        e0, e1 = -rng.uniform(0.02, 0.1), N + rng.uniform(0.02, 0.12)
        P = B([i, i], [e0, e1]) if not horiz else B([e0, e1], [i, i])
        outer = i in (0, N)
        if rng.random() < 0.35 and not outer:             # a long line drawn in two goes
            m = rng.uniform(0.4, 0.6)
            Q = P[0] + (P[1] - P[0]) * m
            b.line([P[0], Q + (P[1] - P[0]) * 0.01], 'black', 0.84, bow=0.004, clip=EXC, hook=0.25, twice=0.2)
            b.line([Q - (P[1] - P[0]) * 0.012 + rng.normal(0, 0.8, 2), P[1]], 'black', 0.84, bow=0.004, clip=EXC, hook=0.25, twice=0.2)
        else:
            b.line(P, 'black', 0.86 if outer else 0.84, bow=0.004, clip=EXC, hook=0.25, twice=0.9 if outer else 0.3)
for n in range(1, 65):
    c_, r_ = cell(n)
    for (du, dv, anc) in [(0.1, 0.72, 'l'), (0.9, 0.72, 'r'), (0.1, 0.12, 'l'), (0.9, 0.12, 'r')]:
        p = B(c_ + du, r_ + dv)
        ok = EX[int(p[1]) - 14:int(p[1]) + 4, int(p[0]) - (0 if anc == 'l' else 26):int(p[0]) + (26 if anc == 'l' else 0)].max() < 0.05
        if ok:
            b.write(str(n), p[0], p[1], 19, 'red' if n % 10 == 0 else 'blue', 0.78, slant=4, jitter=0.7, anchor=anc, hook=0.15,
                    gloop=0.15)
            break
# U-turn arrows at the row ends: the counting snakes back and forth
for r_ in range(N - 1):
    right = (r_ % 2 == 0)
    u = N + 0.18 if right else -0.18
    P = [B(u - (0.02 if right else -0.02), r_ + 0.5), B(u + (0.2 if right else -0.2), r_ + 0.75), B(u + (0.2 if right else -0.2), r_ + 1.25),
         B(u - (0.02 if right else -0.02), r_ + 1.5)]
    Q = spline(P, 10)
    b.line(Q, 'blue', 0.7, smooth=False, hook=0, gloop=0.3)
    b.arrow(Q[-1], Q[-1] - Q[-4], 9, 'blue', 0.75)
# 64: a little flag
fl = ctr(64, 0.05, -0.05)
b.line([fl + (-8, 30), fl + (-8, -28)], 'black', 0.85, smooth=False, hook=0)
b.line([fl + (-8, -28), fl + (22, -18), fl + (-8, -8)], 'black', 0.85, smooth=False, hook=0.2)
b.stage('pen_grid')
tick('grid')

# ===================================================================== 4. pencil: the board, the snakes, the ladders
ROW_COLS = ['lime', 'lime', 'yellow', 'yellow', 'sky', 'sky', 'pink', 'pink']
for n in range(1, 65):
    c_, r_ = cell(n)
    if (c_ + r_) % 2: continue
    m = b.poly(B([c_, c_ + 1, c_ + 1, c_], [r_, r_, r_ + 1, r_ + 1]))
    b.pencil(m * EXC, ROW_COLS[r_], angle=58 + rng.normal(0, 7), pressure=0.42 if ROW_COLS[r_] != 'yellow' else 0.5,
             spacing=4.6, length=(40, 85), overshoot=5.5)
for g, m, (ctrl, w0, col, band) in zip(SG, smasks, SNAKES):
    m = m * PIECEC
    b.pencil(m, col, angle=rng.uniform(30, 70), pressure=0.62, spacing=3.8, length=(30, 60), overshoot=3.5)
    Lb, Rb = g['L'], g['R']                                  # bands across the back, heavier
    for i in range(6, len(Lb) - 8, 12):
        poly = np.vstack([Lb[i:i + 5], Rb[i:i + 5][::-1]])
        b.pencil(b.poly(poly) * m, band, angle=rng.uniform(20, 160), pressure=0.85, spacing=2.8, length=(10, 20), overshoot=2.0)
    spine = g['P'][4:]
    shade_band = b.poly(np.vstack([Rb, (Rb + (spine[:len(Rb)] - Rb) * 0.42)[::-1]])) * m
    b.pen_hatch(shade_band, 'blue', rng.uniform(30, 60), spacing=3.4, pressure=0.5, length=(10, 22), zigzag=0.7)
    b.pencil(b.ellipse(g['hc'][0], g['hc'][1], g['rx'] * 0.95, g['ry'] * 0.95, rot=np.degrees(np.arctan2(g['hd'][1], g['hd'][0]))) * m,
             col, angle=rng.uniform(100, 140), pressure=0.55, spacing=3.4, length=(20, 40), overshoot=2)
    hd, nv = g['hd'], np.array([-g['hd'][1], g['hd'][0]])
    for sg in (-1, 1):
        e = g['hc'] + hd * g['rx'] * 0.42 + nv * sg * g['ry'] * 0.66
        b.pencil(b.ellipse(e[0], e[1], g['w0'] * 0.1, g['w0'] * 0.07, rot=np.degrees(np.arctan2(hd[1], hd[0]))), 'rose', angle=60,
                 pressure=0.8, spacing=2.4, length=(6, 12), overshoot=1)
for lg in LG:
    for sg in (-1, 1):
        r0 = lg['A'] + lg['nv'] * sg * lg['half'] - lg['d'] * 6
        r1 = lg['B'] + lg['nv'] * sg * lg['half'] + lg['d'] * 8
        b.pencil_line([r0 - lg['nv'] * sg * 3, r1 - lg['nv'] * sg * 3], 'ochre', 0.85, width=4.2, clip=PIECEC)
        b.pencil_line([r0 + lg['nv'] * sg * 1.5, r1 + lg['nv'] * sg * 1.5], 'brown', 0.55, width=2.6, clip=PIECEC)
    for rg in lg['rungs']:
        b.pencil_line(rg, 'tan', 0.8, width=3.6, smooth=False, clip=PIECEC)
b.stage('pencil_board')
tick('pencil board')

# ===================================================================== 5. pencil: the pieces
b.pencil(sn_shell, 'orange', angle=50, pressure=0.75, spacing=3.2, length=(16, 34), overshoot=2.5)
(c, s, rot) = SNAIL
b.pencil_line(b.spiral_pts(sc[0] + 2, sc[1] + 1, SNAIL_SHELL[2] * s * 0.6, turns=1.6, a0=rot + 200), 'yellow', 0.9, width=5)
b.pencil(sn_body * (1 - sn_shell), 'peach', angle=120, pressure=0.6, spacing=3.4, length=(16, 34), overshoot=2.5)
b.pencil(b.ellipse(fc[0] - 2, fc[1] + 6, 6, 4), 'pink', angle=60, pressure=0.7, spacing=2.4, length=(6, 10), overshoot=1)
b.pencil(cl_mask, 'sky', angle=62, pressure=0.42, spacing=4.0, length=(20, 46), overshoot=3.5)
cc = CLOUD[0]
YY = np.broadcast_to(np.arange(H, dtype=np.float32)[:, None], (H, W))
b.pen_hatch(cl_mask * smoothstep(cc[1] + 26, cc[1] + 46, YY), 'blue', 40, spacing=3.4, pressure=0.6, length=(14, 26))
del YY
f_, t_, s_ = dicem_geom()
b.pencil(b.poly(f_), 'lilac', angle=55, pressure=0.48, spacing=3.6, length=(18, 40), overshoot=2.5)
b.pencil(b.poly(t_), 'lilac', angle=15, pressure=0.3, spacing=3.6, length=(18, 40), overshoot=2.0)
b.pencil(b.poly(s_), 'violet', angle=80, pressure=0.55, spacing=3.2, length=(18, 40), overshoot=2.0)
b.pen_hatch(b.ellipse(fcx + 4, front[2, 1] + 16, 34, 5.5) * (1 - dm_mask), 'blue', 20, spacing=3.0, pressure=0.45, length=(14, 30))
for sx in (-1, 1):
    b.pencil(b.ellipse(fcx + sx * 14, fcy + 9, 5.5, 3.2), 'pink', angle=60, pressure=0.75, spacing=2.4, length=(6, 10), overshoot=1)
b.pencil(b.poly(side_d), 'grey', angle=75, pressure=0.42, spacing=3.4, length=(20, 40), overshoot=2.5)
b.pencil(b.poly(front_d), 'grey', angle=40, pressure=0.16, spacing=4.4, length=(20, 40), overshoot=2.5)
b.pencil(b.ellipse(DIE[0][0] + 8, DIE[0][1] + 40, 52, 9), 'grey', angle=10, pressure=0.32, spacing=3.6, length=(20, 50), overshoot=3)
b.stage('pencil_pieces')
tick('pencil pieces')

# ===================================================================== 6. margin doodles
# -- bunting across the top
P0, P1 = np.array([640.0, 44.0]), np.array([1300.0, 56.0])
xs_ = np.linspace(0, 1, 60)
string = np.stack([P0[0] + (P1[0] - P0[0]) * xs_, P0[1] + (P1[1] - P0[1]) * xs_ + 34 * 4 * xs_ * (1 - xs_)], 1)
b.line(string, 'blue', 0.8, smooth=False, hook=0.3)
b.line(b.circle_pts(P0[0], P0[1], 5, 5), 'blue', 0.85, closed=True, hook=0)
b.line(b.circle_pts(P1[0], P1[1], 5, 5), 'blue', 0.85, closed=True, hook=0)
FLAGC = ['yellow', 'sky', 'pink', 'lime']
for k in range(11):
    t0 = 0.05 + k * 0.083; t1 = t0 + 0.06
    a = string[int(t0 * 59)]; c2 = string[int(t1 * 59)]
    mid = (a + c2) / 2; nrm = np.array([-(c2 - a)[1], (c2 - a)[0]]); nrm /= np.linalg.norm(nrm)
    if nrm[1] < 0: nrm = -nrm
    tip = mid + nrm * 42
    tri = [a, tip, c2]
    b.line(tri, 'blue', 0.82, smooth=False, hook=0.25)
    b.pencil(b.poly(tri), FLAGC[k % 4], angle=rng.uniform(40, 80), pressure=0.6, spacing=3.4, length=(14, 30), overshoot=3)
    if k % 3 == 1:
        st = b.star_pts(mid[0] + nrm[0] * 15, mid[1] + nrm[1] * 15, 7)
        b.line(st, 'blue', 0.75, smooth=False, hook=0)

# -- the sun, top right
SX, SY, SR = 1736.0, 112.0, 50.0
b.line(b.circle_pts(SX, SY, SR, SR * 0.97), 'blue', 0.85, closed=True, twice=0.5)
b.pencil(b.ellipse(SX, SY, SR, SR * 0.97), 'yellow', angle=60, pressure=0.62, spacing=3.6, length=(20, 50), overshoot=4)
b.face(SX, SY + 4, 70, 'sleep', 'blue', blush='peach')
rays = []
for k in range(14):
    a = np.deg2rad(k * 360 / 14 + rng.normal(0, 3))
    r0, r1 = SR + 9, SR + (30 if k % 2 == 0 else 19) + rng.normal(0, 2)
    rays.append([(SX + np.cos(a) * r0, SY + np.sin(a) * r0), (SX + np.cos(a) * r1, SY + np.sin(a) * r1)])
b.lines(rays, 'blue', 0.8, smooth=False, hook=0.2)
for rr in rays[::2]:
    b.pencil_line(rr, 'orange', 0.7, width=3.4, smooth=False)
for (bx, by, bs) in [(1560, 70, 15), (1600, 102, 11), (1530, 118, 9)]:
    b.line([(bx - bs, by - bs * 0.3), (bx - bs * 0.45, by - bs * 0.55), (bx, by), (bx + bs * 0.45, by - bs * 0.6), (bx + bs, by - bs * 0.25)],
           'blue', 0.75, hook=0.1)

# -- note card on the left (text comes later)
NX0, NY0, NX1, NY1 = 70.0, 236.0, 452.0, 370.0
card = [(NX0, NY0), (NX1, NY0 + 3), (NX1 + 2, NY1 - 26), (NX1 - 24, NY1 + 1), (NX0 + 2, NY1)]
b.line(card, 'blue', 0.82, closed=True, smooth=False, twice=0.4)
b.line([(NX1 + 2, NY1 - 26), (NX1 - 20, NY1 - 22), (NX1 - 24, NY1 + 1)], 'blue', 0.78, smooth=False, hook=0)   # the folded corner
b.pencil(b.poly([(NX1 + 2, NY1 - 26), (NX1 - 20, NY1 - 22), (NX1 - 24, NY1 + 1)]), 'grey', 60, 0.35, 2.8, (6, 14), 1)
b.line(b.circle_pts(NX0 + 18, NY0 + 18, 5, 5), 'blue', 0.85, closed=True, hook=0)
b.dot(NX0 + 18, NY0 + 18, 2.0, 'blue')
# dashed arrow from the card to the long snake
arr = np.array([(NX1 + 10, 330), (520, 380), (565, 420), B(0.35, 4.55)], np.float32)
P = b.dashes(arr, 'blue', 10, 7, 0.8)
b.arrow(P[-1], P[-1] - P[-12], 13, 'blue', 0.8)

# -- tic-tac-toe, left middle
TX, TY, TS = 92.0, 452.0, 52.0
for k in (1, 2):
    b.line([(TX + k * TS + rng.normal(0, 2), TY - 6), (TX + k * TS + rng.normal(0, 2), TY + 3 * TS + 6)], 'blue', 0.8, bow=0.01, hook=0.2)
    b.line([(TX - 6, TY + k * TS + rng.normal(0, 2)), (TX + 3 * TS + 6, TY + k * TS + rng.normal(0, 2))], 'blue', 0.8, bow=0.01, hook=0.2)
for (i, j, m) in [(0, 0, 'x'), (1, 1, 'x'), (2, 0, 'o'), (0, 2, 'o'), (2, 2, 'x'), (1, 0, 'o')]:
    cx_, cy_ = TX + (i + 0.5) * TS, TY + (j + 0.5) * TS
    if m == 'x':
        b.line([(cx_ - 14, cy_ - 14), (cx_ + 14, cy_ + 13)], 'blue', 0.8, smooth=False, hook=0.2)
        b.line([(cx_ + 14, cy_ - 14), (cx_ - 13, cy_ + 14)], 'blue', 0.8, smooth=False, hook=0.2)
    else:
        b.line(b.circle_pts(cx_, cy_, 15, 14), 'blue', 0.8, closed=True)
b.line([(TX + 8, TY + 6), (TX + 3 * TS - 6, TY + 3 * TS - 8)], 'red', 0.85, bow=0.01, hook=0.3)

# -- paper plane with its looping dashed flight
PX, PY = 400.0, 486.0
plane = [(PX - 34, PY + 8), (PX + 32, PY - 12), (PX - 16, PY + 22), (PX - 34, PY + 8)]
b.line(plane, 'blue', 0.82, smooth=False, hook=0)
b.line([(PX + 32, PY - 12), (PX - 8, PY + 12), (PX - 12, PY + 32), (PX - 16, PY + 22)], 'blue', 0.8, smooth=False, hook=0.2)
b.pencil(b.poly(plane), 'sky', 60, 0.35, 3.4, (10, 24), 2)
loop = [(PX - 40, PY + 14), (PX - 90, PY + 40), (PX - 120, PY + 90), (PX - 80, PY + 130), (PX - 40, PY + 96), (PX - 70, PY + 60),
        (PX - 140, PY + 80), (PX - 200, PY + 150)]
b.dashes(loop, 'blue', 8, 7, 0.7)

# -- house on a hill, bottom left
hill = [(20, 1020), (120, 930), (250, 898), (390, 918), (520, 990)]
b.line(hill, 'blue', 0.82, hook=0.2)
HX, HY = 168.0, 900.0
house = [(HX, HY - 4), (HX, HY - 74), (HX + 92, HY - 74), (HX + 92, HY + 2)]
b.line(house, 'blue', 0.84, smooth=False, hook=0.2)
roof = [(HX - 12, HY - 70), (HX + 46, HY - 122), (HX + 104, HY - 70), (HX - 12, HY - 70)]
b.line(roof, 'blue', 0.84, smooth=False, hook=0.2)
b.line([(HX + 70, HY - 101), (HX + 70, HY - 130), (HX + 84, HY - 130), (HX + 84, HY - 88)], 'blue', 0.8, smooth=False, hook=0.1)  # chimney
b.line(spline([(HX + 78, HY - 138), (HX + 70, HY - 152), (HX + 84, HY - 166), (HX + 74, HY - 184), (HX + 92, HY - 198),
               (HX + 82, HY - 218)], 8), 'blue', 0.7, hook=0.3)
b.line([(HX + 34, HY), (HX + 34, HY - 40), (HX + 56, HY - 40), (HX + 56, HY)], 'blue', 0.8, smooth=False, hook=0.1)  # door
b.dot(HX + 51, HY - 20, 1.8, 'blue')
b.line([(HX + 10, HY - 60), (HX + 28, HY - 60), (HX + 28, HY - 44), (HX + 10, HY - 44), (HX + 10, HY - 60)], 'blue', 0.8, smooth=False, hook=0)
b.line([(HX + 64, HY - 60), (HX + 82, HY - 60), (HX + 82, HY - 44), (HX + 64, HY - 44), (HX + 64, HY - 60)], 'blue', 0.8, smooth=False, hook=0)
b.pencil(b.poly(roof), 'red', 50, 0.66, 3.2, (14, 30), 3)
b.pencil(b.poly(house + [(HX, HY - 4)]), 'cream', 70, 0.5, 3.6, (14, 30), 3)
b.pencil(b.poly([(HX + 10, HY - 60), (HX + 28, HY - 60), (HX + 28, HY - 44), (HX + 10, HY - 44)]), 'yellow', 30, 0.8, 2.6, (6, 12), 1)
b.pencil(b.poly([(HX + 64, HY - 60), (HX + 82, HY - 60), (HX + 82, HY - 44), (HX + 64, HY - 44)]), 'yellow', 30, 0.8, 2.6, (6, 12), 1)
TRX, TRY = 360.0, 838.0
crown = Ballpoint.cloud_pts(TRX, TRY, 96, 80, bumps=8, seed=11, flat=False)
b.line(crown, 'blue', 0.82, closed=True, hook=0.2)
b.line([(TRX - 7, TRY + 34), (TRX - 9, TRY + 78)], 'blue', 0.82, smooth=False, hook=0)
b.line([(TRX + 8, TRY + 34), (TRX + 10, TRY + 80)], 'blue', 0.82, smooth=False, hook=0)
b.pencil(b.poly(crown), 'green', 55, 0.6, 3.4, (16, 36), 3)
b.pencil(b.poly([(TRX - 7, TRY + 30), (TRX + 8, TRY + 30), (TRX + 10, TRY + 80), (TRX - 9, TRY + 78)]), 'brown', 80, 0.7, 3.0, (10, 20), 1.5)
for (ax, ay) in [(TRX - 22, TRY - 8), (TRX + 18, TRY - 16), (TRX + 4, TRY + 10)]:
    b.line(b.circle_pts(ax, ay, 6, 6), 'red', 0.8, closed=True, hook=0)
    b.pencil(b.ellipse(ax, ay, 6, 6), 'red', 50, 0.85, 2.4, (6, 12), 1)
hm = b.poly(np.vstack([np.array(hill, np.float32), [(520, 1080), (20, 1080)]]))
b.pencil(hm * smoothstep(0.0, 1.0, 1 - b.poly([(HX - 2, HY - 76), (HX + 94, HY - 76), (HX + 94, HY + 4), (HX - 2, HY + 4)])), 'lime', 62,
         0.32, 5.0, (30, 60), 4)
grass = []
for k in range(26):
    gx = rng.uniform(40, 500); t_ = np.interp(gx, [h[0] for h in hill], [h[1] for h in hill])
    gy = t_ + rng.uniform(6, 60)
    for j in range(3):
        grass.append([(gx + j * 4, gy), (gx + j * 4 + rng.uniform(-6, 6), gy - rng.uniform(8, 16))])
b.lines(grass[:30], 'blue', 0.6, smooth=False, hook=0.1, gloop=0.2)
for gr in grass[30:]:
    b.pencil_line(gr, 'leaf', 0.7, width=2.6, smooth=False)

# -- stars here and there
for (x_, y_, r_) in [(560, 66, 13), (520, 150, 8), (40, 410, 10), (1880, 330, 10), (1390, 120, 12), (1380, 860, 9), (60, 820, 9)]:
    st = b.star_pts(x_, y_, r_, rot=rng.uniform(-110, -70))
    b.line(st, 'blue', 0.8, smooth=False, hook=0.1)
    b.pencil(b.poly(st), 'yellow', 60, 0.7, 2.6, (8, 16), 1.5)
b.line(b.spiral_pts(52, 700, 22, turns=3.0, a0=40), 'blue', 0.75, smooth=False, hook=0.3)
# a string of stars hung between two pins
s0, s1 = np.array([292.0, 662.0]), np.array([540.0, 650.0])
tt = np.linspace(0, 1, 40)[:, None]
thread = s0 + (s1 - s0) * tt + np.array([0, 1.0]) * 4 * tt * (1 - tt) * 34
b.line(thread, 'blue', 0.78, smooth=False, hook=0.2)
for p_ in (s0, s1):
    b.dot(p_[0], p_[1], 3.6, 'blue')
for k, (t_, hang, r_) in enumerate([(0.16, 22, 12), (0.38, 38, 14), (0.6, 26, 12), (0.82, 40, 13)]):
    q = thread[int(t_ * 39)]
    b.line([q, q + np.array([rng.normal(0, 1.5), hang])], 'blue', 0.7, smooth=False, hook=0, gloop=0.2)
    st = b.star_pts(q[0], q[1] + hang + r_ * 0.9, r_, rot=rng.uniform(-100, -80))
    b.line(st, 'blue', 0.8, smooth=False, hook=0.1)
    b.pencil(b.poly(st), 'yellow', rng.uniform(40, 80), 0.75, 2.6, (8, 16), 1.5)

# -- score card box, right (text comes later)
SCX0, SCY0, SCX1, SCY1 = 1420.0, 228.0, 1852.0, 458.0
b.line([(SCX0, SCY0), (SCX1, SCY0 + 2)], 'blue', 0.84, bow=0.004, hook=0.2)
b.line([(SCX1, SCY0 + 2), (SCX1 + 2, SCY1)], 'blue', 0.84, bow=0.004, hook=0.2)
b.line([(SCX1 + 2, SCY1), (SCX0 - 2, SCY1 - 1)], 'blue', 0.84, bow=0.004, hook=0.2)
b.line([(SCX0 - 2, SCY1 - 1), (SCX0, SCY0)], 'blue', 0.84, bow=0.004, hook=0.2)
b.line([(SCX0 + 4, SCY0 + 58), (SCX1 - 4, SCY0 + 60)], 'blue', 0.8, bow=0.004, hook=0.2)
b.line([(SCX0 + 190, SCY0 + 62), (SCX0 + 192, SCY1 - 6)], 'blue', 0.8, bow=0.004, hook=0.2)
# tiny icons
ix = SCX0 + 34
b.line(b.spiral_pts(ix, SCY0 + 92, 12, 2.0, 0), 'black', 0.8, smooth=False, hook=0)
b.line([(ix - 18, SCY0 + 104), (ix + 20, SCY0 + 104), (ix + 24, SCY0 + 92)], 'black', 0.8, hook=0)
b.pencil(b.ellipse(ix, SCY0 + 92, 12, 12), 'orange', 50, 0.65, 2.8, (8, 16), 1.5)
cl_i = Ballpoint.cloud_pts(ix, SCY0 + 148, 40, 26, bumps=6, seed=2)
b.line(cl_i, 'blue', 0.8, closed=True, hook=0)
b.pencil(b.poly(cl_i), 'sky', 60, 0.5, 3.0, (8, 16), 1.5)
fq, tq, sq = cube_pts(ix - 4, SCY0 + 202, 24, 8, 7)
b.line(fq, 'blue', 0.8, closed=True, smooth=False, hook=0)
b.line([tq[0], tq[1], tq[2], sq[2], sq[3]], 'blue', 0.8, smooth=False, hook=0)
b.pencil(b.poly(fq), 'lilac', 50, 0.55, 2.8, (8, 16), 1.5)

# -- the die's bounce across the margin
traj = [(1880, 492), (1800, 456), (1730, 520), (1700, 590), (1660, 548), (1610, 560), (1585, 612)]
P = b.dashes(traj, 'black', 9, 7, 0.7)
b.lines([[(1694, 604), (1688, 616)], [(1702, 606), (1708, 618)], [(1698, 608), (1698, 621)]], 'black', 0.7, smooth=False, hook=0)
b.lines([[(1462, 650), (1446, 646)], [(1464, 670), (1447, 676)], [(1478, 700), (1468, 712)]], 'black', 0.75, smooth=False, hook=0)

# -- flower pot, bottom right
FX, FY = 1800.0, 1000.0
pot = [(FX - 34, FY - 40), (FX + 34, FY - 40), (FX + 26, FY + 22), (FX - 26, FY + 22), (FX - 34, FY - 40)]
b.line(pot, 'blue', 0.82, smooth=False, hook=0.1)
b.line([(FX - 38, FY - 40), (FX + 38, FY - 40), (FX + 38, FY - 28), (FX - 36, FY - 28), (FX - 38, FY - 40)], 'blue', 0.8, smooth=False, hook=0)
b.pencil(b.poly(pot), 'orange', 70, 0.55, 3.2, (14, 30), 2.5)
b.line([(FX, FY - 42), (FX - 4, FY - 100), (FX + 2, FY - 150)], 'blue', 0.8, hook=0.1)
b.pencil_line([(FX, FY - 42), (FX - 4, FY - 100), (FX + 2, FY - 150)], 'leaf', 0.8, width=3.4)
for sg in (-1, 1):
    leaf = [(FX - 3, FY - 80), (FX - 3 + sg * 22, FY - 104), (FX - 3 + sg * 36, FY - 96), (FX - 3 + sg * 20, FY - 84), (FX - 3, FY - 80)]
    b.line(leaf, 'blue', 0.8, hook=0)
    b.pencil(b.poly(spline(leaf, 6)), 'green', 40, 0.65, 2.8, (8, 18), 1.5)
for k in range(5):
    a = np.deg2rad(k * 72 - 90)
    pc = (FX + 2 + np.cos(a) * 14, FY - 160 + np.sin(a) * 14)
    pe = b.circle_pts(pc[0], pc[1], 11, 7, rot=np.degrees(a))
    b.line(pe, 'blue', 0.8, closed=True, hook=0)
    b.pencil(b.ellipse(pc[0], pc[1], 11, 7, rot=np.degrees(a)), 'pink', 60, 0.7, 2.6, (8, 14), 1.5)
b.line(b.circle_pts(FX + 2, FY - 160, 6, 6), 'blue', 0.85, closed=True, hook=0)
b.pencil(b.ellipse(FX + 2, FY - 160, 6, 6), 'yellow', 60, 0.9, 2.4, (6, 10), 1)
# a little cube doodle and a heart
qf, qt, qs = cube_pts(1440, 960, 40, 14, 12)
b.line(qf, 'blue', 0.8, closed=True, smooth=False, hook=0)
b.line([qt[0], qt[1], qt[2], qt[3]], 'blue', 0.8, smooth=False, hook=0)
b.line([qs[1], qs[2], qs[3]], 'blue', 0.8, smooth=False, hook=0)
b.pen_hatch(b.poly(qs), 'blue', 70, spacing=3.2, pressure=0.6, length=(10, 20))
ht = b.heart_pts(1560, 1010, 30, rot=-12)
b.line(ht, 'red', 0.82, closed=True, hook=0.2)
b.pencil(b.poly(ht), 'rose', 55, 0.6, 3.0, (10, 20), 2)
b.stage('doodles')
tick('doodles')

# ===================================================================== 7. red pen: this move
# where the snail was (10): a dotted ghost ring
p10 = ctr(10)
for k in range(12):
    a = np.deg2rad(k * 30)
    b.dot(p10[0] + np.cos(a) * 24, p10[1] + 6 + np.sin(a) * 18, 1.9, 'red')
# four hops: 10 -> 11 -> 12 -> 13 -> 14, counted
for k, (n0, n1) in enumerate([(10, 11), (11, 12), (12, 13), (13, 14)]):
    a, c2 = ctr(n0, -0.1, -0.4), ctr(n1, 0.1, -0.4)
    tt = np.linspace(0, 1, 14)[:, None]
    arc = a + (c2 - a) * tt + np.array([0.0, -1.0]) * (4 * tt * (1 - tt)) * 24
    P = b.dashes(arc, 'red', 7, 5, 0.85, smooth=False)
    b.arrow(P[-1], P[-1] - P[-6], 9, 'red', 0.85)
    top_ = (a + c2) / 2 + np.array([13, -24])                  # beside the grid line, not on it
    b.write(str(k + 1), top_[0], top_[1] - 5, 19, 'red', 0.85, anchor='m', hook=0.2, gloop=0.1)
# up the ladder
lg = LG[0]
side = lg['nv'] * 40                                        # on the free side of the ladder
P = b.dashes([lg['A'] + side + lg['d'] * 30, lg['A'] + side + lg['d'] * (lg['L'] * 0.5), lg['B'] + side - lg['d'] * 10],
             'red', 13, 8, 0.85, clip=PIECEC)
b.arrow(P[-1], P[-1] - P[-14], 15, 'red', 0.88)
b.ring(SNAIL[0][0] - 4, SNAIL[0][1] - 10, 74, 58, 'red', 0.88, rot=-38)
p43 = B(5.1, 4.98)
b.write('+24!', p43[0], p43[1], 34, 'red', 0.88, anchor='l', rot=-6)
b.ring(DIE[0][0] + 6, DIE[0][1] - 2, 66, 60, 'red', 0.8)
b.write('4!', DIE[0][0] + 84, DIE[0][1] - 60, 40, 'red', 0.9, anchor='l')
b.stage('red_pen')
tick('red pen')

# ===================================================================== 8. notes, labels, the score
b.write('snakes & ladders', 64, 104, 62, 'blue', 0.84, slant=6)
b.write('lunch break - round 7', 72, 160, 30, 'red', 0.82, slant=6)
b.underline(66, 520, 120, 'blue', 0.8)
b.write('who drew this', NX0 + 40, NY0 + 58, 34, 'blue', 0.82)
b.write('snake so LONG?!', NX0 + 40, NY0 + 104, 34, 'blue', 0.82)
pn = B(3.0, 4.26)
b.write('nooo~', pn[0], pn[1], 28, 'blue', 0.8, rot=-8)
b.write('start', B(-0.05, -0.42)[0], B(-0.05, -0.42)[1] + 6, 26, 'blue', 0.8)
st0 = B(0.62, -0.32)
b.line([st0, st0 + np.array([10, -30])], 'blue', 0.8, smooth=False, hook=0)
b.arrow(st0 + np.array([10, -30]), (0.3, -1), 9, 'blue')
b.write('home', B(0.5, 8.1)[0], B(0.5, 8.1)[1] - 8, 22, 'blue', 0.8)
# score card
b.write('round 7', SCX0 + 22, SCY0 + 42, 34, 'red', 0.85)
b.write('where?', SCX0 + 214, SCY0 + 42, 30, 'blue', 0.8)
rows = [('snail', '10', '38'), ('cloud', '47', '18'), ('dice', '51', None)]
for k, (nm, a_, z_) in enumerate(rows):
    yb = SCY0 + 102 + k * 54
    b.write(nm, SCX0 + 62, yb, 30, 'blue', 0.8)
    bx_ = b.write(a_, SCX0 + 214, yb, 30, 'blue', 0.8)
    if z_:
        y_m = yb - 10
        b.line([(bx_[2] + 10, y_m), (bx_[2] + 46, y_m - 1)], 'blue', 0.8, smooth=False, hook=0)
        b.arrow((bx_[2] + 46, y_m - 1), (1, 0), 9, 'blue')
        b.write(z_, bx_[2] + 56, yb, 30, 'red' if k == 0 else 'blue', 0.82)
        b.write('ladder' if k == 0 else 'snake', bx_[2] + 104, yb, 20, 'blue', 0.7)
# the die note, with a word crossed out
bx1 = b.write('rolled a', 1416, 784, 32, 'blue', 0.82)
bx2 = b.write('three', bx1[2] + 14, 784, 32, 'blue', 0.82)
b.strike(bx2, 'blue', 0.85, passes=4)
b.write('four!', bx2[2] + 14, 784, 32, 'blue', 0.84)
b.write('(the snail asked for 4)', 1430, 828, 22, 'blue', 0.72)
# ghost of a shopping list pressed through from the sheet above
b.write('milk', 1606, 914, 34, None, 0.9, blind=True)
b.write('eggs x6', 1606, 958, 34, None, 0.9, blind=True)
b.write('glue stick', 1606, 1002, 34, None, 0.9, blind=True)
b.stage('notes')
tick('notes')

# ===================================================================== 9. the conclusion
cb = b.write('slow snail, fast ladder!', 960, 1004, 58, 'red', 0.88, anchor='m', slant=6)
b.underline(cb[0] - 6, cb[2] + 10, cb[3] + 12, 'red', 0.85, wavy=True)
b.write('next: dice', 1268, 1050, 26, 'blue', 0.8)
tick('conclusion')

img = b.save(out, stages_dir=stages)
tick('saved')
print('saved', out)
