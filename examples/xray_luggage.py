"""Example (X-ray / X 光片): 行李安检 · Bag 0417 — a hard-shell suitcase on the belt of a dual-energy baggage
scanner, seen from the top. Everything in it is built as real material along the beam and shot through with
Beer-Lambert, so the case's walls glow at its outline, the aluminium trolley rails show four edges each (two
nested tubes), the wheels show their ball bearings and the axle bolts seen end-on, and everything overlaps
additively. Inside: a compact umbrella (telescopic shaft, eight folded ribs, wrapped canopy, push-button spring),
a travel hairdryer (motor windings, magnets, a coiled-coil heating element on a mica cross, switch, mains cord
and plug), a camera lying on its back (lens barrel rings seen end-on, glass elements, aperture iris, battery, BGA
chips), a key ring with a car fob (coin cell), coins, a folded sweater and jeans (rivets, button, fly zip), a
rolled T-shirt, a bottle of water -- and a toy dinosaur skeleton: a plaster fossil kit with a steel pin through
its spine on a display stand. The scanner flags the skeleton as bone-like and the bottle as a liquid; the side
panel shows the same bag in the material (pseudo-colour) display, a zoom on object 1, and the operator's verdict:
1 is a toy (clear), 2 is over 100 ml (remove). Zeff and volume are measured off the picture.
Draw-on stages: belt -> suitcase -> clothes -> umbrella -> hairdryer -> camera and keys -> skeleton and bottle ->
flags -> material view -> verdict. No image model.
python3 xray_luggage.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from xray import XRay, AMBER, GREEN, RED, CYAN

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'xray_luggage.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

x = XRay(1920, 1080, px_cm=17, seed=417)
CX, CY, ROT = 742.0, 548.0, -1.2            # the case on the belt (case coords u, v: px from its centre)


def K(P, ox=0.0, oy=0.0, rot=0.0, s=1.0):
    """local points -> case coords (move, rotate, scale) -> canvas"""
    return XRay.poly(XRay.poly(np.asarray(P, np.float32)[:, :2], ox, oy, rot, s), CX, CY, ROT)


def k(u, v):
    return K([(u, v)])[0]


def R(u, v, w, h, r=0.0, rot=0.0):
    return K(XRay.rrect(0, 0, w, h, r, rot), u, v)


def E(u, v, rx, ry, rot=0.0, n=72):
    return K(XRay.ellipse(0, 0, rx, ry, rot, n), u, v)


def loop(P):
    return np.vstack([P, P[:1]])


# =========================================================== 1. the belt
x.belt(118, 978, lacing=34)
x.status(['XR-160 DV  ·  LANE 3', 'BAG 0417    VIEW A / TOP    140 kV   0.8 mA'],
         ['07:42:18', '2026-10-02    BELT 0.20 m/s'])
x.stage('belt')

# =========================================================== 2. the suitcase
x.shell(R(0, 0, 1210, 726, 100), 'organic', 425, 5, edge=68, density=1.2)          # 25 cm deep polycarbonate
for v in (-300, -235, 235, 300):                                                    # moulded ridges in both faces
    x.rod(K([(-520, v), (520, v)]), 'organic', 7, flat=5, density=1.2)
x.rod(loop(R(0, 0, 1194, 710, 92)), 'organic', 3.2, flat=15, ribs=(0.55, 3.4))     # nylon coil zip round the rim
for su in (318, 372):                                                               # zip sliders + pull tabs
    x.slab(R(su, -355, 46, 13, 5), 'zinc', 22, edge=5)
    x.slab(R(su + (14 if su > 340 else -14), -347, 40, 4, 2), 'zinc', 40, edge=2)
# TSA-style combination lock in the top wall
x.slab(R(470, -358, 120, 28, 8), 'zinc', 60, edge=10, holes=[R(470, -358, 70, 10, 4)])
for du in (-24, 0, 24):
    x.slab(R(470 + du, -358, 7, 22, 3), 'brass', 22, edge=8)
x.coil(k(420, -352), k(452, -352), 4, 6, 'steel', 0.9)
x.rod(K([(492, -350), (512, -350), (512, -340)]), 'steel', 1.8)
# trolley: two nested aluminium tube stages per rail, lock rods, return springs, rivets, end blocks
for sv in (-1, 1):
    v = sv * 195
    x.shell(R(18, v, 1128, 38, 4), 'aluminium', 22, 2.2, edge=3)
    x.shell(R(42, v, 1106, 29, 3), 'aluminium', 16, 1.8, edge=3)
    x.rod(K([(-520, v), (566, v)]), 'steel', 2.0)
    x.coil(k(-548, v), k(-480, v), 6, 9, 'steel', 1.0)
    for uu in (-530, -40, 548):
        x.disc(*k(uu, v + sv * 26), 5.5, 'steel', 13, rim=(1.5, 3))
    x.slab(R(-538, v, 52, 74, 10), 'organic', 32, edge=8, density=1.1)
# grip at the handle end: plastic shell, push-button spring, release cables to the lock rods
x.shell(R(588, 0, 40, 470, 14), 'organic', 55, 3.5, edge=14, density=1.1)
x.coil(k(588, -34), k(588, 34), 7, 7, 'steel', 1.0)
for sv in (-1, 1):
    x.rod(K([(588, sv * 30), (580, sv * 110), (570, sv * 175), (566, sv * 195)]), 'steel', 1.0)
# top carry handle and its screws (seen from the side)
x.shell(R(60, -378, 260, 32, 16), 'organic', 40, 3, edge=16, density=1.1)
for su in (-48, 168):
    x.slab(R(su, -352, 44, 8, 2), 'steel', 26, edge=3)
    x.screw(k(su, -392), k(su, -347), 3.2, head=(15, 5))
# spinner wheels at the bottom end: front and back units nearly overlap in this view
for sv in (-1, 1):
    x.shell(R(-597, sv * 298, 92, 116, 30), 'organic', 90, 4, edge=28, density=1.1)
    x.slab(R(-612, sv * 298, 70, 96, 22), 'steel', 2.6, edge=1)                      # fork plates
    for b in range(8):
        x.ball(*k(-585, sv * 298 - 26 + b * 7.4), 2.6, 'steel')                     # swivel bearing, edge-on
    for (du, dv) in ((0, 0), (6, -sv * 15)):
        c = k(-628 + du, sv * 298 + dv)
        x.disc(*c, 36, 'rubber', 34, hole=22)
        x.disc(*c, 22, 'organic', 28, hole=11, density=1.1)
        x.disc(*c, 11, 'steel', 7, hole=8.6)
        for b in range(7):
            a = 2 * np.pi * b / 7
            x.ball(c[0] + 7.1 * np.cos(a), c[1] + 7.1 * np.sin(a), 1.9, 'steel')
        x.disc(*c, 5.0, 'steel', 7, hole=3.2)
        x.disc(*c, 3.0, 'steel', 70)                                                 # axle bolt end-on
x.stage('suitcase')

# =========================================================== 3. clothes
x.fabric(R(300, -175, 560, 320, 50, 1.5), 140, layers=8, sheet=4, density=0.5, weave='knit', scale=7,
         angle=ROT + 1.5, creases=[K([(40, -178), (560, -172)]), K([(140, -320), (146, -30)]),
                                   K([(462, -322), (458, -28)])])
x.fabric(R(312, 180, 590, 290, 30, -2), 100, layers=8, sheet=2.4, density=1.15, weave='twill', scale=5,
         angle=ROT - 2, creases=[K([(30, 182), (600, 168)]), K([(200, 40), (196, 322)])])
for (u, v) in ((70, 70), (98, 300), (540, 64), (575, 292), (330, 46), (330, 316)):
    x.disc(*k(u, v), 4.2, 'copper', 6, dome=3)                                       # jeans rivets
x.disc(*k(150, 120), 9.5, 'brass', 7, hole=2.4, rim=(2.2, 2.5))                       # jeans button
x.zipper(K([(170, 150), (320, 158)]), 'brass', tooth=(7, 4.4), depth=3, tape=11)      # fly zip
x.slab(R(520, 118, 64, 40, 4, -2), 'organic', 5, edge=1, density=1.0)                 # leather patch
# rolled T-shirt: a soft cylinder with the spiral of its layers showing at the ends
x.slab(R(-345, 130, 280, 118, 50, 4), 'organic', 118, density=0.28, texture=x.weave('plain', 4, ROT + 4, 0.2))
for j in range(4):
    x.rod(K([(-480 + 6 * j, 80 + 4 * j), (-484 + 6 * j, 180 - 4 * j)]), 'organic', 2.4, density=0.7)
    x.rod(K([(-210 - 6 * j, 80 + 4 * j), (-206 - 6 * j, 180 - 4 * j)]), 'organic', 2.4, density=0.7)
x.stage('clothes')

# =========================================================== 4. the umbrella (compact, folded)
UA, UB = np.array(k(-575, 305)), np.array(k(-78, 148))
ue = (UB - UA) / np.linalg.norm(UB - UA)
un = np.array([-ue[1], ue[0]])
UL = float(np.linalg.norm(UB - UA))


def U(s, o=0.0):
    return UA + ue * s + un * o


x.rod(np.stack([U(0), U(112)]), 'organic', 21, density=1.15)                         # handle
x.coil(U(18), U(66), 6, 8, 'steel', 1.1)                                             # auto-open button spring
x.rod(np.stack([U(4, -9), U(30, -9)]), 'steel', 1.6)                                 # catch
for (s0, s1, r) in ((70, 300, 6.8), (100, 410, 5.6), (150, 478, 4.5)):               # telescopic shaft
    x.tube(np.stack([U(s0), U(s1)]), 'steel', r, 0.75)
x.rod(np.stack([U(250), U(292)]), 'organic', 11, density=1.1)                        # runner
x.rod(np.stack([U(458), U(492)]), 'organic', 9, density=1.1)                         # top notch
x.rod(np.stack([U(490), U(UL + 8)]), 'steel', 3.0)                                   # ferrule
offs = [16 * np.cos(2 * np.pi * (j + 0.3) / 8) for j in range(8)]               # ribs bundled round the shaft
for j, o in enumerate(offs):
    o1, o2, o3 = o, o * 1.25 + 1.5, o * 1.5 - 1.5
    rib = [U(470, o1), U(262, o1 * 1.05)]
    x.rod(np.stack(rib), 'steel', 1.2)                                               # main rib
    x.rod(np.stack([U(262, o2), U(440, o2)]), 'steel', 1.05)                         # second section
    x.rod(np.stack([U(440, o3), U(300, o3)]), 'steel', 0.95)                         # tip section
    x.rod(np.stack([U(285, o * 0.6), U(372, o * 1.0)]), 'steel', 0.8)                # stretcher
    for (s, oo) in ((262, (o1 + o2) / 2), (440, (o2 + o3) / 2)):
        x.disc(*U(s, oo), 2.3, 'steel', 5)                                            # joint rivets
    x.ball(*U(300, o3), 2.4, 'organic', density=1.2)                                 # rib tip caps
spindle = np.vstack([U(s, h) for s, h in zip(np.linspace(232, 495, 14), 34 * np.sin(np.linspace(0, np.pi, 14)) ** 0.7 + 7)] +
                    [U(s, -h) for s, h in zip(np.linspace(495, 232, 14), 34 * np.sin(np.linspace(np.pi, 0, 14)) ** 0.7 + 7)])
x.fabric(XRay.closed(spindle, 4), 60, layers=14, sheet=1.2, density=1.3, weave=None,
         creases=[x.path([U(244 + 32 * j, -30), U(266 + 32 * j, 0), U(292 + 32 * j, 30)], 6) for j in range(7)])
x.rod(np.stack([U(372, -44), U(372, 44)]), 'organic', 15, flat=5, density=1.0)       # strap
x.disc(*U(372, 40), 7, 'brass', 3, hole=2.5, rim=(1.5, 1.5))                          # snap
x.stage('umbrella')

# =========================================================== 5. the hairdryer (side view, nozzle to the right)
HO, HR = (-555, -262), 0.0


def H(P):
    return K(P, *HO, HR)


def h(a, b):
    return H([(a, b)])[0]


x.shell(H(XRay.rrect(150, 0, 300, 118, 26)), 'organic', 118, 4, edge=59, density=1.3)   # barrel
x.shell(H([(296, -56), (352, -36), (352, 36), (296, 56)]), 'organic', 70, 3, edge=24, density=1.2)  # nozzle
x.edgeon(h(10, -54), h(10, 54), 9, 'organic', density=0.7)                           # intake grille
x.edgeon(h(20, -52), h(20, 52), 1.6, 'steel', density=0.35)                          # filter mesh
for j in range(7):
    x.edgeon(h(300 + 7 * j, -50 + 2 * j), h(300 + 7 * j, 50 - 2 * j), 1.6, 'organic', density=1.0)  # outlet slots
# motor: steel can, ferrite magnets, copper windings, shaft, fan
x.shell(H(XRay.rrect(78, 0, 72, 58, 6)), 'steel', 58, 1.1, edge=29)
for sv in (-1, 1):
    x.slab(H(XRay.rrect(78, sv * 21, 54, 8, 2)), 'ferrite', 42, edge=6)
x.slab(H(XRay.rrect(78, 0, 46, 30, 6)), 'copper', 30, edge=10, density=0.5)
x.rod(H([(34, 0), (152, 0)]), 'steel', 2.3)
x.slab(H(XRay.rrect(122, 0, 10, 22, 2)), 'copper', 22, edge=8, density=0.8)          # commutator
x.edgeon(h(150, -50), h(150, 50), 14, 'organic', density=0.6)                        # fan (edge-on)
for j in range(6):
    x.rod(H([(143 + 2 * j, -46 + 18 * j), (157 - 2 * j, -38 + 18 * j)]), 'organic', 1.5, density=1.2)
# heating element: mica cross (one plate edge-on, one face-on) with a coiled-coil nichrome wire
x.rod(H([(176, 0), (284, 0)]), 'mica', 0.8, flat=96)
x.slab(H(XRay.rrect(230, 0, 108, 96, 2)), 'mica', 1.0, edge=0)
x.coil(h(180, 0), h(282, 0), 44, 7, 'steel', 2.4, ribs=(0.6, 2.7))
x.rod(H([(282, 30), (286, 46), (250, 52), (180, 50), (120, 54), (112, 66)]), 'copper', 1.1)   # leads
# handle: shell, switch with brass contacts and spring, rectifier board, strain relief, hanging loop
HG = XRay.rrect(0, 0, 56, 196, 26)
x.shell(K(HG, *np.array(HO) + (118, 156), -8), 'organic', 66, 3, edge=26, density=1.2)
x.slab(H(XRay.rrect(116, 96, 26, 50, 4)), 'organic', 30, edge=4, density=1.1)
for (a, b) in ((106, 80), (126, 80), (106, 112), (126, 112)):
    x.slab(H(XRay.rrect(a, b, 9, 14, 1)), 'brass', 10, edge=2)
x.coil(h(116, 120), h(116, 140), 4, 5, 'steel', 0.8)
x.slab(H(XRay.rrect(126, 172, 34, 24, 2, -8)), 'pcb', 2.6, edge=0)
for (a, b) in ((116, 166), (130, 166), (116, 178), (130, 178)):
    x.disc(*h(a, b), 2.6, 'tin', 2.4)
x.rod(H([(124, 70), (110, 130), (128, 230)]), 'copper', 1.0)
x.rod(H([(132, 70), (132, 130), (138, 230)]), 'copper', 1.0)
x.rod(H([(134, 228), (138, 262)]), 'rubber', np.array([8, 6.5], np.float32), ribs=(0.18, 4.0))
x.rod(loop(H(XRay.ellipse(150, 260, 14, 9, -8))), 'organic', 2.6, density=1.1)
# mains cord and plug
cord = x.path(K([(-417, -2), (-440, 50), (-500, 92), (-548, 70), (-530, 10), (-470, -12), (-392, 40),
                 (-300, 90), (-236, 70), (-210, 30)]), 14)
x.cable(cord, 6.0, 2, 1.25)
pl = np.array(k(-208, 2))
x.slab(R(-208, -10, 38, 60, 10), 'organic', 32, edge=10, density=1.15)
for du in (-10, 10):
    x.rod(K([(-208 + du, -40), (-208 + du, -78)]), 'brass', 2.4)
x.stage('hairdryer')

# =========================================================== 6. the camera (on its back, lens up), keys, coins
CC = (-128, -100)


def cam(u, v):
    return k(CC[0] + u, CC[1] + v)


x.shell(R(CC[0], CC[1], 208, 124, 16), 'magnesium', 68, 2.4, edge=12)
x.slab(R(CC[0] + 82, CC[1], 46, 118, 16), 'rubber', 40, edge=12, density=0.9)       # grip
bat = R(CC[0] + 82, CC[1] + 4, 26, 92, 4)
x.shell(bat, 'steel', 64, 0.6, edge=2)
x.slab(R(CC[0] + 82, CC[1] + 4, 24, 90, 3), 'copper', 62, edge=2, density=0.075)
for j in range(1, 4):
    x.rod(loop(R(CC[0] + 82, CC[1] + 4, 24 - 6 * j, 90 - 6 * j, 3)), 'copper', 0.6, flat=40)
x.slab(R(CC[0] - 10, CC[1] + 6, 150, 96, 6), 'pcb', 2.8, edge=0)                     # main board
for (du, dv, w, hh) in ((-58, -22, 26, 26), (-58, 26, 22, 16), (40, -26, 30, 30), (36, 26, 20, 20)):
    x.slab(R(CC[0] + du, CC[1] + dv, w, hh, 1), 'glass', 2.0, edge=0)
    n = int(w // 5)
    for a in range(n):
        for b in range(int(hh // 5)):
            x.disc(*cam(du - w / 2 + 2.5 + a * 5, dv - hh / 2 + 2.5 + b * 5), 1.5, 'tin', 2.6)     # BGA balls
x.slab(R(CC[0] - 22, CC[1], 60, 42, 3), 'glass', 4, edge=0)                          # sensor package
x.slab(R(CC[0] - 4, CC[1] + 2, 140, 92, 4), 'glass', 4.5, edge=0)                    # rear screen
for (du, dv) in ((-96, -52), (-96, 52), (70, -54), (60, 56)):
    x.disc(*cam(du, dv), 2.3, 'steel', 9)                                            # body screws end-on
x.disc(*cam(-22, 50), 6, 'brass', 10, hole=3.2)                                      # tripod socket
x.slab(R(CC[0] - 22, CC[1] - 60, 40, 10, 2), 'steel', 3.4, edge=1)                   # hot shoe
for du in (-34, -10):
    x.coil(cam(du, -66), cam(du + 6, -66), 2.5, 4, 'steel', 0.6)
for su in (-1, 1):                                                                   # strap lugs
    c = cam(su * 108, -42)
    x.rod(loop(np.array([c + (-6, 6), c + (6, 6), c + (0, -6)], np.float32)), 'steel', 1.6)
strap = x.path(K([(-236, -144), (-272, -106), (-286, -40), (-262, 16), (-206, 36), (-150, 40)]), 14)
x.rod(strap, 'organic', 17, flat=5, density=0.9)
# lens: barrel rings seen end-on, glass elements, iris, mount
LC = cam(-22, 0)
x.disc(*LC, 56, 'rubber', 26, hole=51.5, density=0.9)                                # focus ring
x.disc(*LC, 51, 'aluminium', 86, hole=48.6)                                          # outer barrel
x.disc(*LC, 43, 'aluminium', 70, hole=41.0)                                          # inner barrel
x.disc(*LC, 47, 'steel', 7, hole=38)                                                 # bayonet mount
for a in range(3):
    th = np.radians(30 + 120 * a)
    x.disc(LC[0] + 44 * np.cos(th), LC[1] + 44 * np.sin(th), 2.4, 'steel', 9)        # mount screws
x.disc(*LC, 40, 'glass', 4, dome=14)                                                 # front element
x.disc(*LC, 30, 'glass', 5, dome=10)
x.disc(*LC, 30, 'glass', 8, dome=-5)                                                 # doublet
x.disc(*LC, 23, 'glass', 4, dome=8)
iris_hole = XRay.poly([(14 * np.cos(np.radians(a)), 14 * np.sin(np.radians(a))) for a in np.arange(0, 360, 360 / 7) + 9], *LC)
x.slab(XRay.ellipse(*LC, 34, 34, n=80), 'steel', 1.4, edge=0, holes=[iris_hole])
# key ring: split ring (two turns), two brass keys, a car fob with a coin cell
KR = np.array(k(-40, 58))
for rr in (24, 26.2):
    x.rod(loop(XRay.ellipse(*KR, rr, rr, n=90)), 'steel', 1.15)
KEY = [(0, -26), (20, -24), (30, -12), (34, -9), (150, -9), (152, -7), (160, 0), (156, 7), (148, 9), (142, 9),
       (138, 5), (132, 9), (124, 4), (116, 9), (108, 5), (100, 9), (92, 3), (84, 9), (34, 9), (30, 12), (20, 24),
       (0, 26), (-14, 16), (-18, 0), (-14, -16)]
for ang, mat in ((52, 'brass'), (78, 'brass')):
    kc = KR + 24 * np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
    x.slab(XRay.poly(KEY, *kc, ang), mat, 3.4, edge=1.0, holes=[XRay.poly(XRay.ellipse(-2, 0, 6.5, 6.5, n=30), *kc, ang)])
    for gy in (-3.5, 3.0):                                                           # milled grooves
        x.slab(XRay.poly(XRay.rrect(94, gy, 108, 2.2, 1), *kc, ang), mat, 1.4, edge=0, density=-1.0)
fob_c = KR + 30 * np.array([np.cos(np.radians(150)), np.sin(np.radians(150))])
FA = 150
x.shell(XRay.poly(XRay.rrect(-46, 0, 92, 52, 22), *fob_c, FA), 'organic', 26, 2.4, edge=10, density=1.2)
x.slab(XRay.poly(XRay.rrect(-50, 0, 60, 34, 3), *fob_c, FA), 'pcb', 2.4, edge=0)
x.disc(*XRay.poly([(-56, 0)], *fob_c, FA)[0], 10, 'steel', 5.4, rim=(1.0, 0.6))     # CR2032 coin cell
x.slab(XRay.poly(XRay.rrect(-26, 0, 8, 6, 1), *fob_c, FA), 'glass', 3, edge=0)
x.slab(XRay.poly(XRay.rrect(-120, 2, 60, 12, 3), *fob_c, FA), 'steel', 3, edge=1)  # folded blade
for (u, v, r, m) in ((150, 30, 13, 'brass'), (186, 62, 11.5, 'steel'), (128, 78, 12.5, 'brass')):
    x.disc(*k(u, v), r, m, 3.2, rim=(2.0, 1.2), density=0.85 if m == 'steel' else 1.0)
x.stage('camera_keys')

# =========================================================== 7. the toy dinosaur skeleton and the bottle
DO, DR, DS = (208, -212), -3.0, 1.02
BF = 1.6                                    # cast bones are chunky


def D(P):
    return K(P, *DO, DR, DS)


def d(a, b):
    return D([(a, b)])[0]


SP = [(-250, 34), (-205, 16), (-160, 0), (-115, -12), (-70, -22), (-30, -28), (0, -30), (40, -32), (80, -30),
      (118, -26), (148, -22), (170, -26), (186, -36), (198, -48), (206, -58)]
sp = XRay.path(SP, 16)
segl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])
pos, s = [], 6.0
while s < segl[-1] - 4:
    u_ = np.interp(s, segl, sp[:, 0])
    pos.append(s)
    s += 7 + 6 * float(np.clip((u_ + 250) / 200, 0, 1))
for s in pos:
    c = np.array([np.interp(s, segl, sp[:, 0]), np.interp(s, segl, sp[:, 1])])
    j = min(np.searchsorted(segl, s), len(sp) - 1)
    t = sp[j] - sp[max(j - 1, 0)]
    t = t / (np.linalg.norm(t) + 1e-6)
    n = np.array([t[1], -t[0]])                       # up
    u_ = c[0]
    r = 3 + 6 * np.clip((u_ + 250) / 220, 0, 1) - (1.5 if u_ > 160 else 0)
    ang = np.degrees(np.arctan2(t[1], t[0]))
    gap = 7 + 6 * float(np.clip((u_ + 250) / 200, 0, 1))
    x.slab(D(XRay.rrect(c[0], c[1], gap * 0.78, 2 * r, r * 0.55, ang)), 'plaster', 2.2 * r * DS * BF, tag='dino')
    hs = (26 if -40 < u_ < 150 else 18 if u_ <= -40 else 9) * (0.4 + 0.6 * np.clip((u_ + 250) / 120, 0, 1))
    x.rod(D([c + n * r * 0.7, c + n * (r + hs) - t * hs * 0.25]), 'plaster', np.array([r * 0.36, r * 0.24]) * DS * BF,
          tag='dino')
    if u_ < -15:
        hc = 15 * np.clip((u_ + 250) / 200, 0.25, 1)
        x.rod(D([c - n * r * 0.7, c - n * (r + hc) - t * hc * 0.4]), 'plaster',
              np.array([r * 0.3, r * 0.18]) * DS * BF, tag='dino')
x.rod(D([tuple(p) for p in sp[(sp[:, 0] > -180) & (sp[:, 0] < 200)]]), 'steel', 1.1)   # steel pin in the spine
SK = np.array([-6, 22], np.float32)                 # skull offset from the original sketch
skull = XRay.closed(np.array([(206, -94), (226, -108), (256, -112), (292, -106), (320, -97), (335, -86), (333, -74),
                              (300, -70), (262, -68), (230, -66), (210, -72)]) + SK, 8)
holes = [XRay.ellipse(*(np.array(c) + SK), *rr_) for c, rr_ in (((241, -96), (9, 8)), ((274, -88), (15, 7, -4)),
                                                                ((218, -86), (6, 9, 10)), ((312, -88), (4, 3)))]
x.slab(D(skull), 'plaster', 54 * DS, edge=18 * DS, holes=[D(hh) for hh in holes], tag='dino')
jaw = XRay.closed(np.array([(220, -63), (262, -60), (300, -61), (327, -69), (324, -58), (292, -50), (252, -48),
                            (222, -53)]) + SK, 8)
x.slab(D(jaw), 'plaster', 34 * DS, edge=11 * DS, holes=[D(XRay.ellipse(240, -33, 9, 3))], tag='dino')
for i in range(9):
    a = 232 + i * 11
    ln = 9 - i * 0.35
    yu = -68 - (i * 0.5)
    x.slab(D(np.array([(a - 3, yu), (a + 3, yu), (a + 0.5, yu + ln)]) + SK), 'plaster', 7 * DS, edge=2, tag='dino')
    x.slab(D(np.array([(a + 1, -61 + i * -0.6), (a + 6, -61 + i * -0.6), (a + 3.5, -61 - ln * 0.8)]) + SK),
           'plaster', 6 * DS, edge=2, tag='dino')
for i, u_ in enumerate(np.linspace(30, 150, 9)):                                     # ribs
    v0 = float(np.interp(u_, sp[:, 0], sp[:, 1]))
    L = 58 + 26 * np.sin(np.pi * (u_ - 30) / 120)
    rib = XRay.path([(u_, v0 + 5), (u_ - 4, v0 + 26), (u_ - 13, v0 + L * 0.75), (u_ - 22, v0 + L)], 8)
    x.rod(D(rib), 'plaster', (np.linspace(4.2, 1.8, len(rib)) * DS) * BF, tag='dino')
for i, u_ in enumerate(np.linspace(42, 138, 6)):                                     # gastralia
    x.rod(D(XRay.path([(u_ - 10, 50), (u_, 56), (u_ + 10, 50)], 6)), 'plaster', (1.3 * DS) * BF, tag='dino')
x.slab(D(XRay.ellipse(5, -46, 44, 13, -3)), 'plaster', 22 * DS, edge=8 * DS, tag='dino')        # ilium
x.rod(D([(8, -30), (38, 44)]), 'plaster', (np.array([5.5, 4.0]) * DS) * BF, tag='dino')                 # pubis
x.slab(D(XRay.ellipse(40, 49, 20, 6, 10)), 'plaster', 12 * DS, tag='dino')
x.rod(D([(-6, -30), (-32, 22)]), 'plaster', (np.array([5.0, 2.4]) * DS) * BF, tag='dino')               # ischium
x.slab(D(XRay.ellipse(150, -12, 22, 6, 62)), 'plaster', 12 * DS, tag='dino')                     # scapula
for (hip, knee, ankle, ball, toe) in (((0, -28), (30, 48), (10, 118), (34, 145), (60, 151)),
                                      ((-4, -28), (-26, 50), (-52, 112), (-40, 143), (-16, 150))):
    x.rod(D([hip, knee]), 'plaster', (np.array([7.5, 6.0]) * DS) * BF, tag='dino')
    for p in (hip, knee):
        x.slab(D(XRay.ellipse(p[0], p[1], 8.5, 7.5)), 'plaster', 15 * DS, tag='dino')
    x.rod(D([knee, ankle]), 'plaster', (np.array([5.8, 4.4]) * DS) * BF, tag='dino')
    x.rod(D([(knee[0] + 6, knee[1] + 6), (ankle[0] + 6, ankle[1] - 4)]), 'plaster', (1.8 * DS) * BF, tag='dino')
    for dd in (-4, 0, 4):
        x.rod(D([ankle, (ball[0] + dd * 0.6, ball[1] + dd * 0.4)]), 'plaster', (2.7 * DS) * BF, tag='dino')
    for dd in (-4, 0, 3):
        p1 = (ball[0] + 12, ball[1] + 3 + dd)
        x.rod(D([ball, p1, (toe[0], toe[1] + dd * 0.8)]), 'plaster', (np.array([2.4, 2.0, 1.4]) * DS) * BF, tag='dino')
        x.slab(D([(toe[0], toe[1] + dd * 0.8 - 3), (toe[0] + 9, toe[1] + dd * 0.8 + 2), (toe[0], toe[1] + dd * 0.8 + 3)]),
               'plaster', 5 * DS, edge=1.5, tag='dino')
x.rod(D([(150, -6), (164, 16)]), 'plaster', (3.0 * DS) * BF, tag='dino')                                # arm
x.rod(D([(164, 16), (176, 26)]), 'plaster', (2.0 * DS) * BF, tag='dino')
x.rod(D([(176, 26), (184, 30)]), 'plaster', (1.3 * DS) * BF, tag='dino')
x.rod(D([(176, 26), (181, 35)]), 'plaster', (1.3 * DS) * BF, tag='dino')
# display stand: steel rod, clamp, wooden base, brass plate, screw
x.rod(D([(5, 4), (5, 176)]), 'steel', 2.6 * DS)
x.slab(D(XRay.rrect(5, 4, 16, 9, 2)), 'steel', 8 * DS, edge=2)
x.slab(D(XRay.rrect(0, 186, 230, 18, 4)), 'organic', 50 * DS, edge=6, density=0.65)
x.slab(D(XRay.rrect(-60, 186, 70, 10, 2)), 'brass', 1.0, edge=0)
x.screw(d(5, 178), d(5, 194), 2.6 * DS, head=(10 * DS, 3))
# bottle of water lying on its side: PET wall with moulded rings, water inside, ribbed cap
BC, BR = (250, 278), -4.0
body = [(-178, -40), (-168, -55), (120, -55), (130, -48), (140, -55), (150, -55), (165, -40), (176, -22),
        (186, -16), (205, -16), (205, 16), (186, 16), (176, 22), (165, 40), (150, 55), (140, 55), (130, 48),
        (120, 55), (-168, 55), (-178, 40)]
x.shell(K(XRay.closed(body, 6), *BC, BR), 'organic', 110, 1.0, edge=50, density=1.35, tag='bottle')
water = [(-174, -38), (-165, -51), (118, -51), (128, -45), (140, -51), (148, -51), (162, -38), (170, -24),
         (170, 24), (162, 38), (148, 51), (140, 51), (128, 45), (118, 51), (-165, 51), (-174, 38)]
x.slab(K(XRay.closed(water, 6), *BC, BR), 'water', 102, edge=50, tag='bottle')
for uu in (-120, -60, 0, 60):
    x.rod(K([(uu, -55), (uu, 55)], *BC, BR), 'organic', 3, flat=5, density=1.3)
x.slab(K(XRay.rrect(214, 0, 22, 40, 4), *BC, BR), 'organic', 40, edge=10, density=1.1,
       texture=x.weave('plain', 3.2, BR, 0.25))
x.stage('skeleton_bottle')

# =========================================================== 8. flags on the picture
dino_pts = np.vstack([D(skull), D(SP), D([(-60, 160), (60, 160), (60, 195)])])
fx0, fy0 = dino_pts.min(0) - (14, 14)
fx1, fy1 = dino_pts.max(0) + (14, 10)
x.flag(fx0, fy0, fx1, fy1, 1, 'BONE-LIKE', 'Zeff {dino.z:.1f}')
bp = K(XRay.closed(body, 6), *BC, BR)
bx0, by0 = bp.min(0) - (12, 12)
bx1, by1 = bp.max(0) + (12, 12)
x.flag(bx0, by0, bx1, by1, 2, 'LIQUID', '{bottle.ml:.0f} ml', side='bottom')
x.stage('flags')

# =========================================================== 9. the side panel: material view, zoom on object 1
x.panel(1452, 76, 1900, 1000, 'MATERIAL VIEW  ·  DUAL ENERGY')
x.inset((96, 150, 1400, 948), (1472, 128, 1880, 378), 'material')
x.legend(1472, 392, 408, 15)
zp = D([(60, -100), (335, -100), (335, 80), (60, 80)])
zx0, zy0 = int(zp[:, 0].min()), int(zp[:, 1].min())
zw = int(zp[:, 0].max() - zx0)
zh = int(zw * 230 / 408)
zy0 = int(zp[:, 1].mean() - zh / 2)
x.inset((zx0, zy0, zx0 + zw, zy0 + zh), (1472, 468, 1880, 698), 'material', 'ZOOM  ×%.1f  ·  OBJ 1' % (408 / zw))
x.line([(zx0 + zw, zy0), (1452, 468)], AMBER, 1, dash=7)
x.line([(zx0 + zw, zy0 + zh), (1452, 698)], AMBER, 1, dash=7)
x.stage('material')

# =========================================================== 10. readouts and the verdict
x.text('#  CLASS       Zeff   NOTE', 1472, 726, 16, '#7fa9c2')
x.text('1  BONE-LIKE   {dino.z:4.1f}   PLASTER CAST', 1472, 754, 16, AMBER)
x.text('   TOY FOSSIL KIT', 1472, 780, 16, CYAN)
x.text('CLEAR', 1872, 780, 16, GREEN, 'ra', True, box=GREEN)
x.text('2  LIQUID      {bottle.z:4.1f}   {bottle.ml:.0f} ml', 1472, 818, 16, AMBER)
x.text('   OVER 100 ml', 1472, 844, 16, CYAN)
x.text('REMOVE', 1872, 844, 16, RED, 'ra', True, box=RED)
x.scale(1472, 934, 1880, 950, [('Al 2', 'aluminium', 3.4), ('Al 10 mm', 'aluminium', 17), ('Fe 1', 'steel', 1.7),
                                ('Fe 3', 'steel', 5.1), ('Cu 10 mm', 'copper', 17)], 14, 'ATTENUATION  →')
x.footer([('F1 ORG', '#6f93a8'), ('F2 INORG', '#6f93a8'), ('F3 HI-PEN', '#6f93a8'), ('F4 EDGE+', CYAN),
          ('F5 ZOOM', CYAN)],
         [('0416  CLEAR', '#6f93a8'), ('0417  SECONDARY CHECK', AMBER), ('0418 …', '#6f93a8')])
x.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s', {kk: (round(v.z, 2), round(v.ml)) for kk, v in x.readings.items()})
