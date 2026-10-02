"""Example (letterpress poster / 凸版印刷海报): 马戏团来了 · The Circus Is Coming — a two-colour show bill of the
1890s kind, set from wood type and printed red, then black, a hair out of register. Left: the bill's type, every
line set to full measure in a different face (gothic, a shaded red Clarendon, Chinese wood type), brass rules, a
starred list of the acts with leaders, the parade line in red. Right: the woodcut -- a high wire strung between
two masts, the wire walker in mid-crossing with her balance pole, and below her the elephant, front feet up on a
striped drum, raising its trunk to her; a dimension line on the mast gives the height. The red block (pennants,
blanket, cap, drum stripes, ring curb, costume) was cut loose of the black key. Afterwards the bill was folded in
thirds, a date strip pasted on, tacked up and left to brown and fox.
Draw-on stages: stock -> red forme (type) -> red forme (woodcut tint) -> black wood type -> black key lines ->
black hatching -> small type and rules -> folds and age -> date strip and tacks. No image model.
python3 letterpress_circus.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from letterpress import Letterpress, RED, BLACK
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'letterpress_circus.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

lp = Letterpress(1920, 1080, seed=11, misreg=3.4)
lp.register(BLACK, 0, 0, 0)
lp.register(RED, 3.4, -2.2, 0.05)            # the second pass landed a little up and to the right
W, H = lp.W, lp.H
XX, YY = lp.XX, lp.YY
lp.paper(tone=0.55)
lp.stage('stock')

# ================================================================ geometry of the picture
G = 905                                       # floor of the ring
POLE_L, POLE_R, POLE_TOP = 958, 1786, 170
WIRE_Y = 228
WX = 1262                                     # where the walker stands on the wire


def wire_y(x):
    """the wire sags a little, and dips under the walker's weight"""
    x = np.asarray(x, np.float32)
    u = (x - POLE_L) / (POLE_R - POLE_L)
    return WIRE_Y + 6 * np.sin(np.pi * u) + 10 * np.exp(-((x - WX) / 110) ** 2)


# ---- the elephant: drawn in its own frame (facing left, origin at the near hip, y down, units before scaling),
#      then tilted up so that its front feet stand on the drum
TILT, S = np.deg2rad(22), 0.74
LEG = 300.0                                   # hip to ground in the elephant's own units
HIP = np.array([1540.0, G - LEG * S])


def E(pts):
    P = np.asarray(pts, np.float32) * S
    c, s = np.cos(TILT), np.sin(TILT)
    x, y = P[:, 0], P[:, 1]
    return np.stack([HIP[0] + x * c - y * s, HIP[1] + x * s + y * c], 1)


def E1(x, y):
    return tuple(float(v) for v in E([(x, y)])[0])


body_pts = [(-380, -205), (-300, -232), (-150, -238), (-10, -218), (52, -170), (78, -92), (70, -10), (22, 42),
            (-150, 66), (-300, 52), (-385, 8), (-410, -72)]
head_pts = [(-350, -204), (-390, -258), (-458, -280), (-526, -250), (-562, -174), (-556, -96), (-532, -46),
            (-486, -20), (-428, -28), (-378, -64)]
ear_pts = [(-448, -214), (-404, -236), (-352, -232), (-308, -204), (-288, -152), (-298, -104), (-284, -58),
           (-302, -12), (-334, 24), (-374, 50), (-408, 54), (-424, 20), (-440, -40), (-456, -110), (-462, -170)]
trunk_path = [(-536, -120), (-578, -150), (-606, -205), (-612, -268), (-596, -322), (-566, -346), (-540, -342),
              (-530, -322)]
trunk_w = [104, 80, 62, 50, 41, 33, 28, 26]
SH_N, SH_F, HP_N, HP_F = E1(-322, 0), E1(-282, 12), E1(0, 0), E1(-44, 12)
DRUM_TOP = SH_N[1] + LEG * S * 0.96          # the front legs are a little shorter
DRUM_C, DRUM_RX, DRUM_RY = SH_N[0] + 22, 100.0, 22.0


def leg(top, foot_y, w0, w1, lean=0.0):
    foot = (top[0] + lean, foot_y)
    mid = ((top[0] + foot[0]) / 2 + 3, (top[1] + foot_y) / 2)
    m = lp.tube([top, mid, foot], widths=[w0 * S, (w0 * 0.55 + w1 * 0.45) * S, w1 * S]) * (YY <= foot_y)
    return np.maximum(m, lp.ellipse(foot[0], foot_y - 9 * S, w1 * S * 0.6, 12 * S) * (YY <= foot_y))


m_body = lp.shape(E(body_pts))
m_head = lp.shape(E(head_pts))
m_ear = lp.shape(E(ear_pts))
m_trunk = lp.tube(E(trunk_path), widths=np.array(trunk_w) * S)
m_nh = leg((HP_N[0], HP_N[1] - 40), G, 120, 86, -6)
m_fh = leg((HP_F[0], HP_F[1] - 40), G - 10, 104, 80, -4)
m_nf = leg((SH_N[0], SH_N[1] - 30), DRUM_TOP + 6, 112, 84, -4)
m_ff = leg((SH_F[0], SH_F[1] - 30), DRUM_TOP - 6, 100, 78, 2)
m_tail = lp.tube(E([(66, -150), (86, -92), (94, -26), (88, 22)]), widths=[13, 9, 7, 6])
tip = E1(88, 22)
m_tuft = lp.shape([(tip[0] - 6, tip[1] - 6), (tip[0] + 7, tip[1] - 4), (tip[0] + 9, tip[1] + 22),
                   (tip[0] - 1, tip[1] + 30), (tip[0] - 8, tip[1] + 18)])
m_tusk = lp.tube(E([(-512, -66), (-546, -52), (-576, -54), (-596, -70)]), widths=np.array([20, 16, 10, 4]) * S)
m_mouth = lp.shape(E([(-532, -78), (-508, -60), (-486, -48), (-500, -36), (-524, -50)]))
near = np.maximum.reduce([m_body, m_head, m_trunk, m_nh, m_nf, m_tail])
m_eleph = np.maximum.reduce([near, m_ear, m_ff, m_fh])
m_blanket = lp.shape(E([(-300, -238), (-200, -248), (-90, -242), (-36, -226), (-28, -130), (-38, -18),
                        (-120, -4), (-230, -6), (-302, -22), (-320, -130)])) * m_body
m_inner = lp.shape(E([(-286, -226), (-200, -234), (-96, -230), (-50, -214), (-42, -130), (-52, -34),
                      (-122, -20), (-230, -22), (-288, -36), (-304, -130)])) * m_body
m_cap = lp.poly(E([(-478, -258), (-462, -322), (-418, -326), (-400, -268), (-440, -252)]))


def star_mask(cx, cy, r, inner=0.4, rot=90.0):
    t = np.deg2rad(rot) + np.arange(10) * np.pi / 5
    rr = np.where(np.arange(10) % 2 == 0, r, r * inner)
    return lp.poly(np.stack([cx + np.cos(t) * rr, cy - np.sin(t) * rr], 1))


sc = E1(-170, -124)
m_star = star_mask(sc[0], sc[1], 34, rot=90 + np.rad2deg(TILT) * 0)

# ---- the drum
dtop = lp.ellipse(DRUM_C, DRUM_TOP, DRUM_RX, DRUM_RY)
dside = np.clip(np.maximum(lp.rect(DRUM_C - DRUM_RX, DRUM_TOP, DRUM_C + DRUM_RX, G - 4),
                           lp.ellipse(DRUM_C, G - 4, DRUM_RX, DRUM_RY)) - dtop, 0, 1)
u = np.clip((XX - DRUM_C) / DRUM_RX, -1, 1)
stripes = (np.sin(np.arcsin(u) * 9.0 - (YY - DRUM_TOP) / 9.0) > 0.1).astype(np.float32)

# ---- the ring: curb (front arc) and floor
RC, RRX, RRY = (1372.0, 938.0), 462.0, 56.0
ring_out = lp.ellipse(RC[0], RC[1], RRX, RRY)
ring_in = lp.ellipse(RC[0], RC[1] - 3, RRX - 20, RRY - 8)
curb_top = np.clip(ring_out - ring_in, 0, 1) * (YY > RC[1] - 6)
curb_face = np.clip(lp.ellipse(RC[0], RC[1] + 20, RRX, RRY) - ring_out, 0, 1) * (YY > RC[1])

# ---- masts and pennants
m_poleL = lp.tube([(POLE_L - 1, G + 2), (POLE_L, POLE_TOP)], 17, 11)
m_poleR = lp.tube([(POLE_R + 1, G + 2), (POLE_R, POLE_TOP)], 17, 11)


def pennant(x, d):
    return lp.shape([(x, POLE_TOP - 6), (x + d * 40, POLE_TOP - 24), (x + d * 88, POLE_TOP - 30),
                     (x + d * 62, POLE_TOP - 12), (x + d * 80, POLE_TOP + 6), (x + d * 38, POLE_TOP + 4),
                     (x, POLE_TOP + 14)])


m_penL, m_penR = pennant(POLE_L, -1), pennant(POLE_R, 1)

# ---- the walker (her feet on the wire at the origin, y up is negative), a little arabesque
WY = float(wire_y(WX))
K = 1.15


def Wk(pts):
    P = np.asarray(pts, np.float32) * K
    return np.stack([WX + P[:, 0], WY + P[:, 1]], 1)


w_leg_s = lp.tube(Wk([(-2, -80), (-4, -44), (0, -4)]), widths=np.array([17, 13, 9]) * K)
w_foot = lp.poly(Wk([(-5, -10), (5, -10), (3, 1), (-2, 1)]))
w_leg_l = lp.tube(Wk([(6, -80), (34, -71), (64, -78)]), widths=np.array([16, 11, 6]) * K)
w_torso = lp.shape(Wk([(-11, -80), (-12, -100), (-15, -120), (-8, -127), (8, -127), (15, -120), (12, -100), (11, -80)]))
w_skirt = lp.shape(Wk([(-12, -88), (-30, -78), (-42, -68), (-28, -65), (-15, -69), (0, -65), (15, -69), (28, -65),
                       (42, -68), (30, -78), (12, -88)]))
w_arm_l = lp.tube(Wk([(-12, -121), (-34, -108), (-50, -96)]), widths=np.array([7, 6, 5]) * K)
w_arm_r = lp.tube(Wk([(12, -121), (34, -108), (50, -96)]), widths=np.array([7, 6, 5]) * K)
w_head = lp.ellipse(WX, WY - 139 * K, 11.5 * K, 12.5 * K)
w_hair = lp.shape(Wk([(-12, -140), (-10, -150), (0, -153), (10, -150), (12, -140), (6, -146), (-6, -146)]))
w_bun = lp.ellipse(WX + 1, WY - 156 * K, 6 * K, 5 * K)
w_pole = lp.tube(Wk([(-190, -72), (-100, -91), (0, -97), (100, -91), (190, -72)]), widths=[4.5, 5, 5.5, 5, 4.5])

# ================================================================ red forme: wood type
X0, X1 = 96, 846
lp.type_line('CIRCUS', X0, X1, 382, 196, face='clarendon', ink=RED, shade=(10, 9, BLACK, 3))
for y in (664, 714, 764):
    lp.star(X0 + 14, y - 13, 15, RED)
lp.type_line('GRAND STREET PARADE AT TEN', X0, X1, 862, 50, face='gothic', ink=RED)
lp.press(RED)
lp.stage('red_type')

# ================================================================ red forme: the colour block of the woodcut
lp.tint(np.clip(m_blanket - m_star, 0, 1))
lp.tint(m_cap)
lp.tint(m_penL)
lp.tint(m_penR)
lp.tint(dside * stripes * (YY > DRUM_TOP + 16) * (YY < G - 20))
lp.tint(curb_face)
lp.tint(np.maximum(w_torso, w_skirt), loose=1.0, grow=1)
lp.press(RED)
lp.stage('red_block')

# ================================================================ black forme: wood type
lp.type_line('THE GRAND TRAVELLING', X0, X1, 150, 58, face='gothic', ink=BLACK)
lp.type_line('马戏团来了', X0 + 4, X1 - 4, 566, 136, face='cjk', ink=BLACK)
lp.press(BLACK)
lp.stage('black_type')


# ================================================================ black forme: the woodcut, back to front
def part(mask, key=(3.4, 7.0), tone=None, angle=None, centre=None, aspect=1.0, spacing=8.0, lo=0.14, gain=1.0,
         clear=True):
    """cut one piece of the block: clear what is behind it, key line ('key' layer), hatching ('hatch' layer)"""
    if clear: lp.clear(mask)
    if key:
        with lp.layer('key'):
            lp.key(mask, *key)
    if angle is not None or centre is not None:
        with lp.layer('hatch'):
            lp.hatch(mask, angle=angle or 0, centre=centre, aspect=aspect, spacing=spacing, tone=tone, lo=lo, gain=gain)


def wrinkle(p, q, bow, width=2.4, layer='hatch'):
    p, q = np.array(p, np.float32), np.array(q, np.float32)
    m = (p + q) / 2
    d = q - p
    n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
    with lp.layer(layer):
        lp.line([p, m + n * bow, q], width, taper=(0.35, 0.35))


# ---- masts, platforms, pennants, wire, guy ropes, ladder
for x, m in ((POLE_L, m_poleL), (POLE_R, m_poleR)):
    part(m, key=(2.2, 4.2), angle=90, spacing=6, tone=lp.ramp((x - 8, 0), (x + 8, 0)) * m, lo=0.3)
    with lp.layer('key'):
        lp.solid(lp.ellipse(x, POLE_TOP - 6, 9, 9))                             # finial
        plat = lp.rect(x - 34, WIRE_Y - 18, x + 34, WIRE_Y - 9)
        lp.clear(plat)
        lp.key(plat, 2.0, 3.6)
        lp.line([(x - 26, WIRE_Y - 9), (x - 3, WIRE_Y + 30)], 3, taper=(0.1, 0.1))
        lp.line([(x + 26, WIRE_Y - 9), (x + 3, WIRE_Y + 30)], 3, taper=(0.1, 0.1))
for x, d, m in ((POLE_L, -1, m_penL), (POLE_R, 1, m_penR)):
    part(m, key=(2.2, 4.0), angle=-12 * d, spacing=6, tone=lp.ramp((x + d * 30, 0), (x + d * 88, 0)) * 0.7 * m, lo=0.3)
xs = np.linspace(POLE_L + 6, POLE_R - 6, 48)
with lp.layer('key'):
    lp.line(np.stack([xs, wire_y(xs)], 1), 3.4, taper=(0.0, 0.0))
    lp.line([(POLE_L, POLE_TOP + 22), (POLE_L - 62, G - 2)], 2.2, taper=(0.02, 0.02))
    lp.line([(POLE_R, POLE_TOP + 22), (POLE_R + 62, G - 2)], 2.2, taper=(0.02, 0.02))
    for x in (POLE_L - 62, POLE_R + 62):                                        # stakes
        lp.solid(lp.poly([(x - 4, G - 10), (x + 4, G - 10), (x + 1, G + 8), (x - 1, G + 8)]))
    lx0, lx1 = POLE_L + 22, POLE_L + 44                                         # rope ladder up the left mast
    lp.line([(lx0, WIRE_Y - 6), (lx0 + 2, G - 2)], 2.2, taper=(0.02, 0.02))
    lp.line([(lx1, WIRE_Y - 6), (lx1 + 4, G - 2)], 2.2, taper=(0.02, 0.02))
    for y in np.arange(WIRE_Y + 22, G - 10, 30):
        lp.line([(lx0, y), (lx1 + 2, y + 2)], 2.6, taper=(0.05, 0.05))

# ---- engraver's tint lines behind the scene: ruled across, fading out to the edges, cleared round every figure
things = np.maximum.reduce([m_eleph, m_tuft, dside, dtop, m_poleL, m_poleR, w_pole, w_head, w_skirt, w_torso,
                            w_leg_l, w_leg_s, w_arm_l, w_arm_r, w_hair, w_bun])
halo = lp.ellipse(1372, 610, 400, 300)
from core import blur as _blur
vign = np.clip(_blur(halo, 60) * 1.4 - 0.25, 0, 1) * (YY < G - 30)
with lp.layer('hatch'):
    lp.hatch(np.clip(vign - np.clip(_blur(things, 3) * 6, 0, 1), 0, 1), angle=0, spacing=7,
             tone=0.30 * vign, lo=0.08, wobble=0.4)

# ---- the ring: sawdust, cast shadows, curb
with lp.layer('hatch'):
    floor = np.clip(ring_in - m_eleph - dside - dtop, 0, 1) * (YY > G - 40)
    lp.stipple(floor, 0.0035, (0.6, 1.4), tone=np.clip((YY - (G - 44)) / 70, 0, 1))
    sh = np.clip(lp.ellipse(1660, G + 4, 110, 12) + lp.ellipse(DRUM_C + 70, G + 2, 110, 11), 0, 1)
    sh = sh * (1 - m_eleph) * (1 - dside)
    lp.hatch(sh, angle=0, spacing=6, tone=0.55 * sh, lo=0.1)
part(curb_top, key=(2.0, 3.0))
part(curb_face, key=(2.4, 4.0), angle=90, spacing=7,
     tone=(0.35 + 0.45 * lp.ramp((RC[0] - 100, 0), (RC[0] + RRX, 0))) * curb_face, lo=0.3)
with lp.layer('key'):
    for k in np.linspace(-0.9, 0.9, 13):                                        # joints between the curb boards
        x = RC[0] + k * RRX
        y = RC[1] + RRY * np.sqrt(max(0.0, 1 - k * k))
        lp.line([(x, y + 1), (x, y + 19)], 2.2, taper=(0.05, 0.05))

# ---- the drum: shaded side, hoops, light top
part(dside, key=(3.0, 6.0), angle=90, spacing=7,
     tone=np.clip(0.05 + 0.8 * lp.ramp((DRUM_C - 10, 0), (DRUM_C + DRUM_RX, 0)), 0, 1) * dside, lo=0.3)
with lp.layer('key'):
    for yb in (DRUM_TOP + 12, G - 14):
        hoop = np.clip(lp.ellipse(DRUM_C, yb, DRUM_RX + 1, DRUM_RY) - lp.ellipse(DRUM_C, yb - 8, DRUM_RX + 1, DRUM_RY), 0, 1)
        lp.solid(hoop * dside)
part(dtop, key=(3.0, 5.0))

# ---- the elephant: far legs, then the near silhouette, internal contours, ear, details
for m in (m_ff, m_fh):
    part(m, key=(3.0, 5.5), angle=90, spacing=8, tone=np.clip(0.5 + 0.55 * lp.form_tone(m), 0, 1) * m)
belly = lp.ramp(E1(-150, -120), E1(-150, 70))
tone_n = np.clip(lp.form_tone(near, soft=40) * 0.8 + 0.3 * belly - 0.05, 0, 1)
lp.clear(near)
with lp.layer('key'):
    lp.key(near, 4.0, 8.5)
with lp.layer('hatch'):
    body_only = np.clip(m_body - m_nh - m_nf, 0, 1)
    lp.hatch(np.clip(body_only - m_inner, 0, 1), centre=E1(-160, -1000), spacing=8.5, tone=tone_n, lo=0.32)
    for m in (m_nh, m_nf):
        lp.hatch(m, angle=92, spacing=8, tone=np.clip(lp.form_tone(m, soft=16) + 0.1, 0, 1), lo=0.2)
    lp.hatch(np.clip(m_head - m_trunk, 0, 1), centre=E1(-470, -470), spacing=8,
             tone=np.clip(lp.form_tone(m_head, soft=30) * 0.9 + 0.2 * lp.ramp(E1(-470, -200), E1(-470, -30)), 0, 1), lo=0.22)
    lp.hatch(m_trunk, angle=-70, spacing=7, tone=np.clip(lp.form_tone(m_trunk, soft=10) * 0.9 + 0.05, 0, 1), lo=0.3)
with lp.layer('key'):
    lp.solid(m_tuft)
    lp.line([E1(-60, -40), E1(-48, 10), E1(-60, 60)], 3.0, taper=(0.5, 0.1))       # thigh
    lp.line([E1(-262, -30), E1(-256, 20), E1(-268, 62)], 3.0, taper=(0.5, 0.1))    # elbow
# the blanket over the back: cut clear of the body hatching, border line, studs, fringe, shading over the red
lp.clear(m_blanket)
with lp.layer('key'):
    lp.key(m_blanket, 3.0, 5.5)
    lp.key(m_inner, 1.8, 2.6)
    for t in np.linspace(0.05, 0.95, 11):
        a = E1(-296 + t * 252, -14 + 6 * np.sin(t * np.pi))
        lp.solid(lp.ellipse(a[0], a[1], 3.6, 3.6))
    for t in np.linspace(0.02, 0.98, 26):
        a = E1(-298 + t * 262, -4 + 8 * np.sin(t * np.pi))
        lp.line([a, (a[0] + 1, a[1] + 13)], 2.0, taper=(0.1, 0.5))
with lp.layer('hatch'):
    lp.hatch(np.clip(m_inner - m_star, 0, 1), angle=-70, spacing=8, tone=np.clip(tone_n - 0.1, 0, 1) * m_inner, lo=0.42)
# the ear and its shadow on the neck
ear_tone = np.clip(lp.form_tone(m_ear, soft=20) * 0.6 + 0.5 * lp.ramp(E1(-440, -100), E1(-300, -100)), 0, 1)
part(m_ear, key=(3.6, 7.5), centre=E1(-470, -110), spacing=7.5, tone=ear_tone, lo=0.2)
with lp.layer('hatch'):
    sh = lp.cast(m_ear, 12, 10, np.clip(near - m_ear - m_blanket, 0, 1), 1.5)
    lp.hatch(sh, angle=95, spacing=7.5, tone=0.8 * sh, lo=0.1)
# cap, tusk, mouth, eye
part(m_cap, key=(2.4, 4.0), angle=-60, spacing=6, tone=lp.ramp(E1(-470, -290), E1(-396, -290)) * 0.7 * m_cap, lo=0.35)
cap_top = E1(-440, -324)
with lp.layer('key'):                                                           # the fez's tassel hangs off the back
    lp.line([cap_top, E1(-404, -316), E1(-392, -290)], 2.4, taper=(0.05, 0.05))
    t = E1(-390, -282)
    lp.solid(lp.poly([(t[0] - 4, t[1] - 6), (t[0] + 5, t[1] - 6), (t[0] + 8, t[1] + 12), (t[0] - 6, t[1] + 12)]))
part(m_tusk, key=(2.4, 4.0))
with lp.layer('key'):
    lp.solid(np.clip(m_mouth - m_tusk, 0, 1))
    eye = E1(-498, -170)
    lp.solid(lp.ellipse(eye[0], eye[1], 7.0, 4.4, rot=-30))
    lp.line([E1(-518, -192), E1(-498, -198), E1(-476, -188)], 2.6)
# trunk rings, toenails, knee wrinkles
path = spline(E(trunk_path), 10)
dd = np.gradient(path, axis=0)
dd /= np.linalg.norm(dd, axis=1, keepdims=True) + 1e-6
nrm = np.stack([-dd[:, 1], dd[:, 0]], 1)
wd = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(trunk_w)), np.array(trunk_w) * S)
for i in range(8, len(path) - 6, 3):
    p, n, w = path[i], nrm[i], wd[i]
    s = 0.40 if i % 2 else 0.28
    wrinkle(p + n * w * s, p - n * w * 0.44, w * 0.10, 2.0)
for top, foot_y, lean in ((SH_N, DRUM_TOP + 6, -4), (HP_N, G, -6), (HP_F, G - 10, -4)):
    fx = top[0] + lean
    for k in (-0.5, -0.1, 0.3):
        nx = fx + k * 28
        with lp.layer('key'):
            lp.line([(nx - 6, foot_y - 2), (nx, foot_y - 8), (nx + 6, foot_y - 2)], 2.2, taper=(0.2, 0.2))
    for yy in (foot_y - 38, foot_y - 50):
        wrinkle((fx - 22, yy), (fx + 20, yy + 2), 4, 2.0)

# ---- the walker, last: she is in front of the wire
for m in (w_leg_l, w_leg_s):
    part(m, key=(2.0, 3.4), angle=80, spacing=5, tone=0.75 * lp.form_tone(m, soft=4) * m, lo=0.3)
with lp.layer('key'):
    lp.solid(w_foot)
part(w_skirt, key=(2.0, 3.0), angle=-60, spacing=5,
     tone=0.5 * lp.ramp(Wk([(0, -88)])[0], Wk([(0, -65)])[0]) * w_skirt, lo=0.25)
part(w_torso, key=(2.0, 3.0))
part(w_head, key=(1.8, 3.0))
with lp.layer('key'):
    lp.solid(w_hair)
    lp.solid(w_bun)
    lp.solid(lp.ellipse(WX - 4 * K, WY - 138 * K, 1.4, 1.6))
    lp.solid(lp.ellipse(WX + 4 * K, WY - 138 * K, 1.4, 1.6))
for m in (w_arm_l, w_arm_r):
    part(m, key=(1.8, 2.8))
part(w_pole, key=(2.6, 2.6))
with lp.layer('key'):
    for s in (-1, 1):
        lp.solid(lp.ellipse(WX + s * 50 * K, WY - 95 * K, 4.5, 4.5))            # hands on the pole

# ---- dimension line beside the right mast: how high the wire is
DX = POLE_R - 40
with lp.layer('key'):
    y0, y1 = float(wire_y(DX)) + 10, G - 8
    lp.line([(DX, y0 + 14), (DX, 548)], 2.0, taper=(0.0, 0.0))
    lp.line([(DX, 640), (DX, y1 - 14)], 2.0, taper=(0.0, 0.0))
    lp.solid(lp.poly([(DX, y0), (DX - 7, y0 + 18), (DX + 7, y0 + 18)]))
    lp.solid(lp.poly([(DX, y1), (DX - 7, y1 - 18), (DX + 7, y1 - 18)]))
    lp.rule(DX - 10, DX + 10, y0 - 1, 'single', BLACK, 2)
    lp.rule(DX - 10, DX + 10, y1 + 1, 'single', BLACK, 2)
    lp.text('40 FT.', DX + 9, 594, 26, 'roman_bold', anchor='mm', rot=90)

lp.press(BLACK, only=['key'])
lp.stage('key_lines')
lp.press(BLACK, only=['hatch'])
lp.stage('hatching')
# the block is printed: let go of the woodcut's full-sheet masks before the rest of the run
for _k in [k for k, v in list(globals().items()) if isinstance(v, np.ndarray) and v.shape == (H, W) and k not in ('XX', 'YY')]:
    del globals()[_k]

# ================================================================ small type, rules, border
lp.border(36, 30, 1884, 1050, BLACK, 4.0)
lp.rule(X0, X1, 604, 'thick_thin', BLACK, 4)
acts = [('THE HIGH WIRE', 'forty feet above the ring'), ('THE ELEPHANT', 'dances upon a drum'),
        ('CLOWNS & PONIES', 'and a brass band')]
for (name, note), y in zip(acts, (664, 714, 764)):
    w1 = lp.text(name, X0 + 40, y, 34, 'antique')
    w2 = lp.text_width(note, 30, 'italic')
    lp.text(note, X1, y, 30, 'italic', anchor='rs')
    lp.leaders(X0 + 40 + w1 + 14, X1 - w2 - 14, y - 6, 3.6, 12)
lp.rule(X0, X1, 796, 'double', BLACK, 3)
lp.text('— will exhibit at —', (X0 + X1) / 2, 906, 26, 'italic', anchor='ms')
lp.text('RIVERSIDE SHOW PRINT, No. 27', 1844, 1032, 15, 'roman', anchor='rs', spacing=1.5)
lp.press(BLACK)
lp.stage('small_type')

# ================================================================ the life of the bill
lp.fold('v', 640, 1.0)
lp.fold('v', 1281, 0.9)
lp.fold('h', 541, 0.8)
lp.tone_edges(1.0)
lp.foxing(170)
lp.stain(250, 1000, 230, 90, 0.08)
lp.stage('folded_aged')


def date(s):
    s.type_line('SATURDAY · MAY 17', 36, s.W - 36, 74, 44, face='clarendon', ink=BLACK, wear=0.2)
    s.text('ON THE RIVER MEADOW  ·  RAIN OR SHINE', s.W / 2, 104, 17, 'roman_bold', anchor='ms', spacing=2.5)


lp.strip(140, 922, 802, 1022, rot=-0.7, draw=date)
lp.tack(66, 58)
lp.tack(1858, 62)
lp.tack(70, 1022)
lp.tack(1852, 1018)
lp.nicks(3, (3, 7))

lp.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
