"""Example (hand-drawn cartoon, frame by frame): 早安吐司 / Good Morning, Toast — how a toaster makes breakfast,
told as one drawing from a hand-drawn cartoon: a mint toaster with a happy face; two slices of toast shooting out
of its glowing slots, arms up, one delighted and one surprised; a "叮!" starburst; a pat of butter dozing on a plate
waiting for them; a morning window with the sun coming up over the hills. Numbered notes on the left follow the
toast up through the machine: ① press the lever, ② the coils glow red for three minutes, ③ ding, up it pops.
Brush-pen ink that boils, flat colour a little off the lines, one or two cel-shadow tones, crayon sky and toast,
screentone cabinet, blue-pencil rough left under everything. No image model.
python3 cartoon_toaster.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from cartoon import Cartoon, WHITE, RED, YELLOW
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'cartoon_toaster.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

W, H = 1920, 1080
c = Cartoon(W, H, seed=12, boil=2.0)
E, R, P = Cartoon.ellipse_pts, Cartoon.rrect_pts, Cartoon.place

MINT, MINT_L, MINT_D, MINT_DD = '#86cdbf', '#b4e4d9', '#5ba99d', '#3f877f'
CHROME, CHROME_D = '#e3e5e0', '#a9b2af'
CRUST, CRUST_D = '#b8692e', '#8d4b21'
CRUMB, CRUMB_D, TOASTED = '#f6ca76', '#e3a553', '#d68735'
BUTTER, BUTTER_L, BUTTER_D = '#ffdf7e', '#fff0b4', '#ecbb4b'
GLASS, SKY, SUN = '#d6ecf3', '#8cc6de', '#ffc93f'
HILL, HILL_D = '#a2d08a', '#7cb56a'
FRAME, FRAME_D = '#f8f0e1', '#dccdb4'
WOOD, WOOD_D, WOOD_DD = '#efd3a0', '#d9a96b', '#b67f47'
CAB, CAB_D = '#8fb4d2', '#6c93b5'
PLATE, PLATE_D, PLATE_B = '#fbf6ec', '#d9d3cb', '#9ccbdc'
SLOT, COIL = '#3a2620', '#ff7a33'
DX = 30                                                                  # the toaster group sits a little right of centre

# ---------------------------------------------------------------- back wall: tiles
for y in (712, 762):
    c.line([(0, y), (700, y + 1)], 2.4, taper=(0, 30), jitter=1.2)
    c.line([(1180, y), (W, y - 1)], 2.4, taper=(30, 0), jitter=1.2)
rt = np.random.default_rng(4)
for row, (ya, yb) in enumerate([(712, 762), (762, 812)]):
    for x in np.arange(40 + 60 * (row % 2), W, 120):
        if rt.random() < 0.3 or 560 < x < 1260: continue
        c.line([(x, ya + 3), (x + 1, yb - 3)], 2.2, taper=(4, 6), jitter=0.5)

# ---------------------------------------------------------------- the window: arch, sky, sun over the hills, clouds
WX, WY, WR = 1100, 330, 290                                              # arch centre and radius
def arch(inset):
    r = WR - inset
    top = [(WX + r * np.cos(t), WY + r * np.sin(t)) for t in np.linspace(np.pi, 2 * np.pi, 60)]
    return np.array(top + [(WX + r, 612 - inset)] + [(WX - r, 612 - inset)], np.float32)
outer, glass = arch(0), arch(26)
c.fill(outer, FRAME)
Fg = c.fill(glass, GLASS, slop=0, knock=True)
gm = c.mask(glass)
c.crayon(glass, SKY, pressure=np.clip((600 - c.YY) / 520, 0.12, 0.8) * 0.95, angle=20, clip=gm)
sun = E(1250, 574, 92, 92)
c.fill(c.mask(sun) * gm, SUN, slop=2)
c.crayon(E(1250, 574, 150, 150), '#ffe79a', pressure=0.42, angle=-30, clip=gm * (1 - c.mask(sun)))
c.line(E(1250, 574, 92, 92, a0=186, a1=354), 6, taper=(0, 0))
for a in np.linspace(38, 142, 6):
    t = np.deg2rad(a)
    c.line([(1250 + np.cos(t) * 112, 574 - np.sin(t) * 112), (1250 + np.cos(t) * 138, 574 - np.sin(t) * 138)], 5, (4, 6), smooth=False)
hx = np.linspace(WX - WR + 20, WX + WR - 20, 30)
hills = np.array([(x, 548 - 22 * np.sin((x - 820) / 95) - 10 * np.cos((x - 820) / 41)) for x in hx] + [(WX + WR, 640), (WX - WR, 640)], np.float32)
Fh = c.fill(c.mask(hills) * gm, HILL, slop=2)
c.shade(c.mask(hills) * gm, HILL_D, (0, -12), clip=Fh)
c.line(hills[:30], 5, taper=(0, 0))
for x0, x1, y0, y1 in [(WX - 13, WX + 13, WY - WR, 598), (WX - WR + 20, WX + WR - 20, 318, 342)]:
    bar = R(x0, y0, x1, y1, 3)
    c.shape(bar, FRAME, shade=(FRAME_D, 6, 6), width=4.5, slop=1.5)
c.outline(glass, 5)
c.outline(outer, 7.5)
sill = R(WX - WR - 34, 598, WX + WR + 34, 632, 8)
c.shape(sill, FRAME, shade=(FRAME_D, 0, 10), width=6)

# ---------------------------------------------------------------- a wall clock: seven o'clock
KX, KY = 1712, 468
c.shade(E(KX + 9, KY + 11, 82, 82), '#e0d3bb', None)
rim = E(KX, KY, 80, 80)
Fk = c.fill(rim, MINT)
c.shade(rim, MINT_D, (14, 14), clip=Fk)
dialk = E(KX, KY, 61, 61)
Fd = c.fill(dialk, PLATE, slop=2, knock=False)
c.shade(dialk, PLATE_D, (-8, -8), clip=Fd)
c.outline(rim, 7.5, 0.4)
c.outline(dialk, 4, 0.2)
for k in range(12):
    t = np.deg2rad(90 - k * 30)
    r0 = 44 if k % 3 == 0 else 49
    c.line([(KX + np.cos(t) * r0, KY - np.sin(t) * r0), (KX + np.cos(t) * 55, KY - np.sin(t) * 55)], 4.2 if k % 3 == 0 else 2.8, (2, 2), smooth=False)
for ang, L, w in [(90 - 7 * 30, 30, 7), (90, 44, 5)]:
    t = np.deg2rad(ang)
    c.line([(KX, KY), (KX + np.cos(t) * L, KY - np.sin(t) * L)], w, (2, 6), smooth=False)
c.dot(KX, KY, 5)
c.glint([(KX - 58, KY - 28), (KX - 44, KY - 52)], 6)

# ---------------------------------------------------------------- the counter and the cabinet below it
top = np.array([(-20, 812), (W + 20, 812), (W + 20, 948), (-20, 948)], np.float32)
Ft = c.fill(top, WOOD, slop=0)
c.line([(-10, 812), (W + 10, 812)], 5, taper=(0, 0))
rg = np.random.default_rng(7)
for y in (838, 866, 902, 930):
    xs = np.sort(rg.uniform(0, W, 6))
    for xa, xb in zip(xs[::2], xs[1::2]):
        c.line([(xa, y), ((xa + xb) / 2, y + rg.uniform(-3, 3)), (xb, y + rg.uniform(-2, 2))], 2.2, (20, 30), jitter=0.8)
edge = np.array([(-20, 948), (W + 20, 948), (W + 20, 984), (-20, 984)], np.float32)
c.shape(edge, WOOD_D, shade=(WOOD_DD, 0, 12), width=6, slop=1.5)
cab = np.array([(-20, 984), (W + 20, 984), (W + 20, H + 20), (-20, H + 20)], np.float32)
Fc = c.fill(cab, CAB, slop=0)
c.shade(np.array([(-20, 984), (W + 20, 984), (W + 20, 1010), (-20, 1010)], np.float32), CAB_D, None, clip=Fc)
c.tone(cab, '#46698c', cell=10, angle=45, amount=np.clip((1080 - c.YY) / 96, 0, 1) * 0.16 + 0.04)
for x in (330, 800, 1270, 1740):
    c.line([(x, 988), (x + 1, H + 10)], 4.5, taper=(0, 0))
    for sx in (-1, 1):
        k = E(x + sx * 34, 1032, 9, 9)
        c.shape(k, CHROME, shade=(CHROME_D, 3, 3), width=3.5, slop=1)

# contact shadows on the counter (hatched)
for cx, cy, rx, ry in [(900 + DX, 856, 300, 24), (1590, 912, 232, 26)]:
    sh = E(cx, cy, rx, ry)
    c.shade(sh, WOOD_D, None, clip=Ft)
    c.hatch(E(cx + 10, cy + 4, rx * 0.92, ry * 0.7), angle=-60, spacing=13, width=2.6)

# ---------------------------------------------------------------- the cord and its plug
cord = [(660 + DX, 820), (600, 846), (548, 880), (560, 912), (612, 904), (604, 874), (540, 868), (450, 896), (372, 906)]
c.line(cord, 7.5, taper=(2, 2), press=0.05)
plug = R(300, 889, 368, 925, 12)
c.shape(plug, CHROME, shade=(CHROME_D, 6, 6), width=5)
for y in (898, 916):
    c.line([(300, y), (270, y)], 5, (1, 1), smooth=False)

# ---------------------------------------------------------------- the toaster
for fx0 in (690 + DX, 1020 + DX):
    c.shape(R(fx0, 836, fx0 + 62, 866, 9), '#4d3c35', width=5, slop=1)
body = R(640 + DX, 512, 1130 + DX, 848, (105, 105, 36, 36))
Fb = c.fill(body, MINT)
fe = spline([(642 + DX, 600), (720 + DX, 584), (885 + DX, 577), (1050 + DX, 584), (1128 + DX, 600)], per=10)
topm = c.mask(body) * c.mask(np.vstack([fe, [(1150 + DX, 470), (620 + DX, 470)]]))
c.fill(topm, MINT_L, slop=2, knock=False)
c.shade(body, MINT_D, (40, 12), clip=Fb)
c.shade(body, MINT_DD, (13, 5), clip=Fb)
skirt = R(646 + DX, 804, 1124 + DX, 848, (4, 4, 34, 34))
Fs = c.fill(skirt, CHROME, slop=2, knock=False)
c.shade(skirt, CHROME_D, (20, 10), clip=Fs)
c.glint([(690 + DX, 816), (760 + DX, 815)], 6)
c.glint([(682 + DX, 596), (690 + DX, 560), (722 + DX, 530)], 11)
c.glint([(752 + DX, 528), (760 + DX, 526)], 9, taper=(3, 3))
c.glint([(760 + DX, 622), (755 + DX, 700)], 9)
c.outline(body, 9.5, 0.45)
c.line(fe, 5, taper=(6, 6))
c.line([(650 + DX, 804), (1120 + DX, 804)], 4.5, taper=(6, 6))
for sx0 in (700 + DX, 902 + DX):
    slot = R(sx0, 535, sx0 + 168, 561, 12)
    c.fill(slot, SLOT, slop=1, knock=False)
    c.glint([(sx0 + 14, 553), (sx0 + 154, 553)], 5, COIL, taper=(10, 10))
    c.glint([(sx0 + 30, 546), (sx0 + 138, 546)], 2.5, '#ffb070', taper=(10, 10))
    c.outline(slot, 4.5, 0.2)
# lever (up: the toast has just popped) and the timer dial
track = R(664 + DX, 614, 682 + DX, 744, 8)
c.fill(track, SLOT, slop=1, knock=False); c.outline(track, 3.5, 0)
knob = R(612 + DX, 604, 712 + DX, 640, 15)
c.shape(knob, RED, shade=('#b3342a', 8, 7), width=6.5, slop=2)
c.glint([(626 + DX, 614), (660 + DX, 612)], 5)
dial = E(700 + DX, 772, 26, 26)
c.shape(dial, CHROME, shade=(CHROME_D, 6, 6), width=5, slop=1.5)
for a in np.linspace(-20, 200, 6):
    t = np.deg2rad(a)
    c.line([(700 + DX + np.cos(t) * 33, 772 - np.sin(t) * 33), (700 + DX + np.cos(t) * 41, 772 - np.sin(t) * 41)], 3.2, (2, 2), smooth=False)
c.line([(700 + DX, 772), (700 + DX + 15, 772 - 15)], 4.5, (3, 3), smooth=False)
c.face(900 + DX, 690, 150, 'happy')

# ---------------------------------------------------------------- the toast, popping
SL = [(-0.40, 0.52), (0.0, 0.545), (0.40, 0.52), (0.43, 0.10), (0.41, -0.16), (0.50, -0.30), (0.49, -0.47), (0.33, -0.60),
      (0.0, -0.64), (-0.33, -0.60), (-0.49, -0.47), (-0.50, -0.30), (-0.41, -0.16), (-0.43, 0.10)]
CR = [(x * 0.8, y * 0.8 + 0.01) for x, y in SL]


def toast(cx, cy, s, rot, mood, arms, seed):
    for sh, hd, bend, th in arms:                                        # arms first: the slice sits in front of them
        c.arm(P([sh], cx, cy, s, rot)[0], hd, bend, width=6, hand=24, thumb=th)
    crust = P(SL, cx, cy, s, rot)
    Fc_ = c.fill(crust, CRUST)
    c.shade(crust, CRUST_D, (14, 8), clip=Fc_)
    crumb = P(CR, cx, cy, s, rot)
    Fi = c.fill(crumb, CRUMB, slop=2.5)
    inset = P([(x * 0.66, y * 0.64 + 0.03) for x, y in SL], cx, cy, s, rot)
    c.crayon(c.mask(crumb) * (1 - c.mask(inset)), TOASTED, pressure=0.5, angle=rot + 30, soft=5, clip=Fi)   # toasted edges
    c.shade(crumb, CRUMB_D, (12, 10), clip=Fi)
    c.outline(crust, 8, 0.4)
    c.outline(crumb, 3.4, 0.2, gaps=2)
    rr = np.random.default_rng(seed)
    for _ in range(7):
        q = P([(rr.uniform(-0.27, 0.27), rr.uniform(0.22, 0.4) if rr.random() < 0.6 else rr.uniform(-0.45, -0.3))], cx, cy, s, rot)[0]
        c.dot(q[0], q[1], rr.uniform(1.6, 2.6))
    f = P([(0, 0.0)], cx, cy, s, rot)[0]
    c.face(f[0], f[1], 108, mood, rot=rot)


toast(790 + DX, 300, 205, 12, 'happy', [((-0.45, 0.12), (636, 232), -0.38, -1)], 3)       # each slice throws its outer arm up
toast(1010 + DX, 276, 205, -10, 'wow', [((0.45, 0.12), (1214, 210), 0.38, 1)], 8)
slices = c.mask(P(SL, 790 + DX, 300, 225, 12)) + c.mask(P(SL, 1010 + DX, 276, 225, -10))

# ---------------------------------------------------------------- plate, a dozing pat of butter, a knife
plate = E(1590, 885, 216, 50)
Fp = c.fill(plate, PLATE_B)
c.fill(E(1590, 883, 198, 44), PLATE, slop=1.5, knock=False)
c.shade(plate, PLATE_D, (0, 9), clip=Fp)
well = E(1590, 880, 150, 31)
c.shade(well, PLATE_D, (0, -7))
c.outline(plate, 7, 0.4)
c.outline(well, 3.4, 0.1, gaps=1)
puddle = E(1522, 895, 36, 7.5)
c.shape(puddle, BUTTER, shade=(BUTTER_D, 5, 3), width=3.6, slop=1)
bt = Cartoon.densify([(1500, 838), (1524, 806), (1664, 806), (1664, 852), (1642, 878), (1500, 878)], 6)
Fbt = c.fill(bt, BUTTER)
c.fill(np.array([(1500, 838), (1524, 806), (1664, 806), (1642, 838)], np.float32), BUTTER_L, slop=1.5, knock=False)
c.fill(np.array([(1642, 838), (1664, 806), (1664, 852), (1642, 878)], np.float32), BUTTER_D, slop=1.5, knock=False)
c.outline(bt, 7, 0.4, smooth=False)
c.line([(1502, 838), (1642, 838), (1662, 808)], 3.6, (6, 6), smooth=False)
c.line([(1642, 840), (1642, 874)], 3.6, (6, 6), smooth=False)
drip = [(1497, 842), (1512, 840), (1518, 856), (1520, 880), (1527, 893), (1520, 899), (1511, 893), (1509, 874), (1500, 862), (1494, 852)]
Fdr = c.fill(drip, BUTTER, slop=1)                                      # melting over the front edge into the puddle
c.shade(drip, BUTTER_D, (5, 3), clip=Fdr)
c.outline(drip, 3.8, 0.3)
c.glint([(1502, 848), (1506, 858)], 3.5, taper=(2, 2))
c.face(1578, 851, 76, 'sleepy', width=5.0)
knife_rot = 17.5
blade = P(R(-72, -9, 72, 9, (9, 2, 2, 9)), 1714, 886, 1, knife_rot)
c.shape(blade, CHROME, shade=(CHROME_D, 0, 6), width=5, slop=1)
c.glint(P([(-55, -2), (40, -2)], 1714, 886, 1, knife_rot), 3.5)
handle = P(R(-50, -12, 50, 12, 12), 1835, 848, 1, knife_rot)
c.shape(handle, RED, shade=('#b3342a', 4, 6), width=5.5, slop=1.5)
for u in (-26, 22):
    q = P([(u, 0)], 1835, 848, 1, knife_rot)[0]
    c.dot(q[0], q[1], 3.2)

# ---------------------------------------------------------------- effects: whoosh, puffs, crumbs, the ding
c.speed_lines((716 + DX, 506), (852 + DX, 500), angle=98, n=4, length=(46, 84), width=4.2)
c.speed_lines((918 + DX, 500), (1058 + DX, 506), angle=83, n=4, length=(46, 84), width=4.2)
c.puff(724 + DX, 522, 34, bumps=5, squash=0.62, rot=10)
c.puff(1066 + DX, 518, 36, bumps=5, squash=0.62, rot=-20)
c.crumbs(900 + DX, 270, n=10, spread=(300, 190), size=(5, 9), avoid=slices)
c.pop_lines(1040 + DX, 116, 34, 62, [64, 90, 116], width=5)
bx, by = 1430, 236
c.burst(bx, by, 170, 122, RED, spikes=13, depth=0.3, rot=8, shade='#b3342a')
for x, y, r in [(760, 84, 18), (1110, 60, 12), (640, 470, 18), (1790, 640, 18), (1820, 604, 10), (1590, 470, 14)]:
    c.sparkle(x, y, r)

# ---------------------------------------------------------------- lettering and the numbered notes
c.sketch([(86, 204), (600, 202)], width=1.6)
c.sketch([(86, 100), (600, 99)], width=1.6)
c.letter('早安吐司', 92, 200, 116, YELLOW, depth=(6, 8), depth_colour=MINT_DD, spacing=4)
c.note('GOOD MORNING, TOAST!', 98, 262, 35, spacing=1)
c.note('z', 1684, 800, 26, rot=8)
c.note('Z', 1712, 770, 36, rot=12)
c.letter('叮!', bx - 6, by + 36, 104, YELLOW, depth=(5, 6), depth_colour='#8d2a22', anchor='m', rot=6)
steps = [(3, 404, '弹起来！', 'POP', [(420, 392), (560, 386), (726, 372)]),
         (2, 528, '电热丝烧红 3 分钟', 'HEAT · 3 MIN', [(556, 520), (640, 530), (694 + DX, 548)]),
         (1, 652, '按下拉杆', 'PRESS', [(392, 640), (500, 636), (598 + DX, 624)])]
for n, y, zh, en, arr in steps:
    c.badge(128, y - 12, 25, str(n), YELLOW)
    c.note(zh, 168, y, 36)
    c.note(en, 170, y + 36, 24, '#6b5a4c', spacing=2)
    c.arrow(arr, 4.2, head=18)
c.pencil_note('TOAST · A-07', 1846, 50, 26, anchor='r')

# ---------------------------------------------------------------- the drawing, replayed the way it was made
c.stage('paper', show=[])
c.stage('rough', show=['rough'], rough=0.9)
c.stage('ink', show=['rough', 'ink'], rough=0.55)
c.stage('flat', show=['rough', 'ink', 'flat'])
c.stage('shade', show=['rough', 'ink', 'flat', 'shade', 'texture'])
c.stage('fx', show=['rough', 'ink', 'flat', 'shade', 'texture', 'fx'])
c.save(out, stages_dir=stages)
print('saved', out)
