"""Example (blue picture book): 借伞 · The Shared Umbrella -- one spread of a soft-blue modern picture book.

Soft blue rain at a tiny bus stop. The shelter is far too small for a huge, shy, fluffy white bear, so a small
girl in a blue raincoat stretches both arms as high as they will go and holds her coral-red umbrella over him.
It covers exactly one thing: his nose. The rain runs off his ears and the top of his head, it lands on
her own coral hair too, and she does not mind -- she is looking up at him, very pleased. He looks down at his paws,
blushing. Under the empty shelter a snail has the whole dry bench to itself; in the big puddle by the lamppost a
duck and two ducklings are having the best day of their lives.

Drawn the way the illustrator works: blank paper -> blue colour blocks (sky block that stops short of the page edge,
misty trees, bushes, coat, shelter, puddles) -> loose ink line -> dark scribbled masses -> coral accents and cheeks
-> chalky whites -> rain, splashes and speckle -> printed on the page (gutter fold, page numbers).
--stages writes those steps as snapshots for the draw-on. No image model.
python3 bluebook_shared_umbrella.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from bluebook import BlueBook, INK
from core import blur, smoothstep, noise2d

W, H = 1920, 1080
GUTTER = 960
RAIN_ANG = 80.0                     # falling a little to the right
SLANT = 1 / np.tan(np.deg2rad(RAIN_ANG))


def base_y(x):
    """the wavy line where the bushes meet the pavement"""
    return 906 + 7 * np.sin(np.asarray(x, np.float32) / 53.0) + 4 * np.sin(np.asarray(x, np.float32) / 17.0 + 1)

# ---------------------------------------------------------------- the umbrella, tilted toward the bear
TILT = np.deg2rad(25)
AX = np.array([np.sin(TILT), -np.cos(TILT)])          # shaft axis, handle -> tip
PX = np.array([np.cos(TILT), np.sin(TILT)])           # across the canopy
RC = np.array([1300.0, 420.0])                        # centre of the rim
CAN_R, CAN_H = 134.0, 94.0


def at(u, w):
    """umbrella frame -> canvas: u across the canopy, w up the shaft"""
    return RC + PX * u + AX * w


def canopy_pts():
    th = np.linspace(0, np.pi, 40)
    dome = [at(CAN_R * np.cos(t), CAN_H * np.sin(t) ** 0.9) for t in th]          # right rim -> tip -> left rim
    us = np.linspace(-CAN_R, CAN_R, 6)
    rim = []
    for a, b in zip(us[:-1], us[1:]):
        for t in np.linspace(0, 1, 7)[1:]:
            rim.append(at(a + (b - a) * t, -9 * np.sin(np.pi * t)))
    return np.array(dome + rim, np.float32)


def rib(ui):
    t = np.linspace(0, 1, 12)
    return np.array([at(ui * np.sin(x * np.pi / 2), CAN_H * np.cos(x * np.pi / 2) ** 0.9) for x in t], np.float32)


class Spread:
    def __init__(self, b):
        self.b = b
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.shapes()

    # ============================================================ shapes
    def shapes(self):
        b, X, Y = self.b, self.XX, self.YY
        S = self.S = {}
        # --- the bear: sitting, head tipped down-left, nose under the umbrella
        S['b_body'] = b.poly([(1430, 700), (1500, 600), (1640, 568), (1780, 610), (1858, 760), (1872, 900),
                              (1820, 975), (1640, 990), (1470, 975), (1410, 880)])
        S['b_head'] = b.ellipse(1585, 492, 168, 146, rot=-8)
        S['b_muz'] = b.ellipse(1416, 566, 92, 56, rot=-10)
        S['b_earL'] = b.ellipse(1492, 370, 40, 38); S['b_earR'] = b.ellipse(1690, 384, 38, 36)
        S['b_pawL'] = b.ellipse(1506, 742, 44, 34, rot=-25); S['b_pawR'] = b.ellipse(1556, 760, 40, 31, rot=18)
        S['b_footL'] = b.ellipse(1522, 962, 64, 30, rot=-6); S['b_footR'] = b.ellipse(1772, 968, 56, 27, rot=8)
        S['bear'] = np.maximum.reduce([S['b_body'], S['b_head'], S['b_muz'], S['b_earL'], S['b_earR'],
                                       S['b_footL'], S['b_footR']])
        # --- the kid
        S['k_head'] = b.ellipse(1100, 652, 74, 70)
        S['k_ear'] = b.ellipse(1028, 668, 14, 16)
        S['k_hair'] = np.clip(S['k_head'] * smoothstep(636, 610, Y + 10 * np.sin((X - 1030) / 12.0)) +
                              b.ellipse(1032, 618, 24, 19, rot=-30) + b.ellipse(1170, 610, 23, 18, rot=25), 0, 1)
        S['k_bunL'] = b.ellipse(1012, 596, 23, 17, rot=-35); S['k_bunR'] = b.ellipse(1190, 588, 22, 16, rot=30)
        S['k_coat'] = b.poly([(1078, 728), (1134, 728), (1150, 760), (1180, 884), (1106, 892), (1030, 884), (1060, 760)])
        S['k_armR'] = b.band([(1146, 752), (1186, 690), (1212, 622)], 24, 19)       # far arm, lower hand
        S['k_armL'] = b.band([(1128, 748), (1184, 664), (1226, 590)], 25, 19)       # near arm, upper hand
        S['k_bootL'] = b.poly([(1066, 920), (1086, 920), (1090, 948), (1094, 958), (1048, 960), (1046, 948), (1064, 940)])
        S['k_bootR'] = b.poly([(1112, 918), (1132, 918), (1134, 946), (1150, 952), (1150, 962), (1110, 962)])
        S['kid'] = np.maximum.reduce([S['k_head'], S['k_ear'], S['k_hair'], S['k_bunL'], S['k_bunR'], S['k_coat'],
                                      S['k_armR'], S['k_armL'], b.band([(1080, 880), (1076, 930)], 12),
                                      b.band([(1118, 884), (1124, 930)], 12), S['k_bootL'], S['k_bootR']])
        # --- the umbrella
        S['canopy'] = b.poly(canopy_pts(), smooth=False)
        # --- the bus stop, the lamp, the sign
        S['roof'] = b.poly([(512, 534), (908, 506), (914, 542), (508, 572)], smooth=False)
        S['seat'] = b.poly([(584, 796), (838, 792), (840, 812), (582, 816)], smooth=False)
        S['glass'] = b.poly([(572, 566), (864, 548), (866, 792), (570, 796)], smooth=False)
        S['bench'] = S['seat']
        S['sign'] = b.ellipse(455, 398, 46, 46)
        S['lamp'] = b.poly([(152, 158), (198, 158), (206, 214), (144, 214)], smooth=False)
        # --- snail and ducks
        S['shell'] = b.ellipse(712, 762, 27, 25)
        S['slug'] = b.band([(668, 788), (700, 789), (740, 787), (762, 776), (770, 766)], 13, 17)
        S['snail'] = np.maximum(S['shell'], S['slug'])
        self.ducks = [(290, 978, 1.3), (436, 988, 0.74), (522, 996, 0.66)]       # (x, y, size)
        S['ducks'] = np.zeros((H, W), np.float32)
        S['duck_parts'] = []
        for (x, y, s) in self.ducks:
            body = b.poly([(x - 46 * s, y - 2 * s), (x - 30 * s, y - 24 * s), (x + 10 * s, y - 22 * s), (x + 36 * s, y - 10 * s),
                           (x + 52 * s, y - 30 * s), (x + 44 * s, y + 4 * s), (x + 20 * s, y + 14 * s), (x - 30 * s, y + 12 * s)])
            head = b.ellipse(x - 34 * s, y - 40 * s, 19 * s, 18 * s)
            bill = b.poly([(x - 50 * s, y - 42 * s), (x - 72 * s, y - 38 * s), (x - 70 * s, y - 31 * s), (x - 48 * s, y - 33 * s)])
            S['duck_parts'].append((body, head, bill))
            S['ducks'] = np.maximum.reduce([S['ducks'], body, head, bill])
        # --- puddles
        self.puddles = [(330, 990, 262, 40, 3), (1300, 1006, 250, 36, 4), (770, 948, 112, 17, 5), (1840, 1016, 70, 14, 6)]
        S['puddles'] = np.maximum.reduce([b.blob(x, y, rx, ry, 0.06, sd) for x, y, rx, ry, sd in self.puddles])
        # --- the rain shadow under the canopy (rain falls along RAIN_ANG)
        E1, E2 = at(-CAN_R, 0), at(CAN_R, 0)
        drop = lambda p: (p[0] + (975 - p[1]) * SLANT, 975)
        S['dry'] = np.maximum(b.poly([tuple(E1), tuple(E2), drop(E2), drop(E1)], smooth=False), S['canopy'])
        # --- bushes along the back
        self.bush_list = [(150, 820, 150, 92, 'blue', 11), (360, 800, 170, 108, 'teal', 12), (560, 832, 140, 76, 'blue', 13),
                          (760, 812, 180, 100, 'teal', 14), (990, 826, 160, 90, 'blue', 15), (1190, 808, 190, 112, 'teal', 16),
                          (1420, 830, 160, 84, 'blue', 17), (1620, 806, 190, 112, 'teal', 18), (1790, 830, 120, 84, 'blue', 19),
                          (260, 868, 210, 56, 'teal', 20), (900, 872, 230, 52, 'teal', 21), (1500, 874, 260, 50, 'teal', 22)]
        S['bushes'] = []
        for (x, y, rx, ry, col, sd) in self.bush_list:
            top = b.blob(x, y, rx, ry, 0.13, sd)
            base = (Y < base_y(X)) * (Y > y - ry * 0.2) * (np.abs(X - x) < rx * 0.92)
            S['bushes'].append((np.maximum(top, base.astype(np.float32)), col, sd))
        S['front'] = np.maximum.reduce([S['bear'], S['kid'], S['canopy'], S['bench'], S['ducks'], S['snail'], S['glass']])
        self.N = noise2d(H, W, 70, 3, 77)

    # ============================================================ 2 blue colour blocks
    def blue(self):
        b, S, X, Y = self.b, self.S, self.XX, self.YY
        keep_white = np.maximum.reduce([S['bear'], S['k_head'], S['k_hair'], S['k_bunL'], S['k_bunR'], S['k_ear'],
                                        S['canopy'], S['lamp'], S['ducks']])
        b.block((62, 50, 1860, 906), 'powder', rough=10, corner=30, avoid=keep_white, halo=3, seed=31)
        # misty trees far behind
        trees = [(262, 600, 92, 118), (370, 650, 62, 80), (800, 560, 96, 130), (905, 640, 58, 76), (1760, 600, 86, 110)]
        far = np.zeros((H, W), np.float32)
        for i, (x, y, rx, ry) in enumerate(trees):
            far = np.maximum(far, b.blob(x, y, rx, ry, 0.22, 40 + i))
            far = np.maximum(far, b.blob(x + rx * 0.35, y + ry * 0.25, rx * 0.6, ry * 0.55, 0.25, 60 + i))
            far = np.maximum(far, b.band([(x + 4, y + ry * 0.5), (x - 2, 880)], 12, 20))
        b.fill(far, '#a3c1e2', pressure=0.94, angle=-80, slip=0, loose=3, edge=9, dry_edge=0.65, mottle=0.12, streak=0.8,
               avoid=keep_white, halo=3, seed=41)
        for i, (x, y, rx, ry) in enumerate(trees):
            b.crayon([[(x - rx * 0.5 + k * rx * 0.33, y - ry * 0.4 + 16 * (k % 2)), (x - rx * 0.46 + k * rx * 0.35, y + ry * 0.55)]
                      for k in range(4)], 'cornflower', width=7, pressure=0.55, dry=0.6, seed=50 + i)
            b.crayon([[(x + 2, y + ry * 0.2), (x - 1, 880)]], 'slate', width=8, pressure=0.6, dry=0.4, seed=55 + i)
        # bushes: one colour each, overlapping
        front = S['front']
        for (m, col, sd) in S['bushes']:
            b.fill(m * (Y < base_y(X) + 4), col, pressure=0.95, angle=float(np.random.default_rng(sd).uniform(-75, -55)), loose=4,
                   edge=10, dry_edge=0.6, mottle=0.12, avoid=front, halo=3, seed=sd)
        # shelter, sign, coat
        b.fill(S['glass'], '#cfe0f0', pressure=0.95, angle=80, slip=0, loose=2, edge=6, medium='gouache', alpha=0.82,
               seed=59)
        b.fill(S['roof'], 'teal', pressure=0.95, angle=-4, seed=60)
        b.fill(S['bench'] * (1 - S['snail']), 'cornflower', pressure=0.92, angle=-2, seed=61)
        b.fill(S['sign'], 'cobalt', pressure=0.95, angle=-30, seed=62)
        coat = np.maximum.reduce([S['k_coat'], S['k_armR'], S['k_armL']])
        b.fill(coat, 'cobalt', pressure=0.95, angle=72, mottle=0.14, seed=63)
        b.fill(coat * smoothstep(1110, 1160, X + (Y - 760) * 0.3), 'deep', pressure=0.85, angle=70, slip=0, seed=64)
        # the bear's shadow side, pale and scratchy
        shade = S['bear'] * smoothstep(1740, 1830, X + 0.25 * (Y - 500) + 30 * np.sin(Y / 50))
        b.fill(shade, 'mist', pressure=0.7, angle=60, loose=6, edge=20, dry_edge=0.85, slip=0, seed=65)
        under = S['bear'] * (blur(S['b_head'], 12) > 0.02) * (1 - S['b_head']) * (Y > 560) * (Y < 650)
        b.fill(under, 'mist', pressure=0.75, angle=10, loose=6, edge=12, dry_edge=0.8, slip=0, seed=66)
        b.fill(S['b_footL'] * (Y > 962) + S['b_footR'] * (Y > 966), 'mist', pressure=0.8, angle=0, seed=67)
        # puddles and the wet pavement
        b.fill(S['puddles'], 'blue', pressure=0.95, angle=4, loose=3, edge=10, dry_edge=0.6, avoid=S['ducks'], halo=2,
               slip=0, seed=70)
        for i, (x, y, rx, ry, sd) in enumerate(self.puddles):
            b.fill(b.blob(x - rx * 0.1, y + ry * 0.25, rx * 0.75, ry * 0.45, 0.1, sd + 9) * (1 - S['ducks']), 'deep',
                   pressure=0.7, angle=2, slip=0, loose=3, seed=71 + i)
        r = np.random.default_rng(9)
        wet = []
        for _ in range(26):
            x, y = r.uniform(80, 1840), r.uniform(925, 1050)
            L = r.uniform(40, 160)
            wet.append([(x, y), (x + L, y + r.uniform(-3, 3))])
        b.crayon(wet, 'powder', width=7, pressure=0.6, dry=0.6, seed=72)

    # ============================================================ 3 the ink line
    def ink(self):
        b, S, X, Y = self.b, self.S, self.XX, self.YY
        # bear: fur silhouette in scalloped tufts, muzzle smooth
        b.fluff(S['b_head'] * (1 - S['b_muz']), 'ink', length=(18, 34), curl=0.55, width=4.2, seed=101)
        b.fluff(S['b_body'], 'ink', length=(20, 38), curl=0.5, width=4.2,
                avoid=np.maximum.reduce([blur(S['b_head'], 3) > 0.3, S['b_pawL'], S['b_pawR'],
                                         S['b_footL'] > 0.5, S['b_footR'] > 0.5, S['kid'] > 0.5]).astype(np.float32), seed=102)
        for e, (ex, ey, er) in ((S['b_earL'], (1492, 370, 40)), (S['b_earR'], (1690, 384, 38))):
            t = np.linspace(np.deg2rad(150), np.deg2rad(400), 30)
            b.ink(np.stack([ex + np.cos(t) * er, ey + np.sin(t) * er], 1), 4.4, seed=int(ex))
            t = np.linspace(np.deg2rad(190), np.deg2rad(350), 14)
            b.ink(np.stack([ex + np.cos(t) * er * 0.55, ey + 4 + np.sin(t) * er * 0.5], 1), 2.6, seed=int(ex) + 1)
        t = np.linspace(np.deg2rad(95), np.deg2rad(335), 40)
        mx = 1416 + np.cos(t) * 92 * np.cos(np.deg2rad(-10)) - np.sin(t) * 56 * np.sin(np.deg2rad(-10))
        my = 566 + np.cos(t) * 92 * np.sin(np.deg2rad(-10)) + np.sin(t) * 56 * np.cos(np.deg2rad(-10))
        b.ink(np.stack([mx, my], 1), 4.4, swell=0.35, seed=103)
        b.dot(1340, 550, 21, 15, seed=104)                                  # the dry nose
        b.ink([(1350, 565), (1356, 584), (1378, 594), (1398, 584)], 2.8, seed=105)
        b.eyes([(1474, 494), (1559, 489)], r=8.0, look=(-1.0, 1.0), seed=106)
        b.ink([(1462, 466), (1476, 460), (1492, 463)], 2.6, seed=107)       # worried little brows
        b.ink([(1549, 459), (1564, 455), (1579, 459)], 2.6, seed=108)
        b.fluff(S['b_pawL'], 'ink', length=(14, 22), curl=0.4, width=3.0, gaps=0.2, seed=109)
        b.fluff(S['b_pawR'] * (1 - S['b_pawL']), 'ink', length=(14, 22), curl=0.4, width=3.0, gaps=0.2, seed=110)
        b.ink([(1475, 610), (1462, 660), (1474, 712)], 3.0, seed=111)        # arm against the chest
        b.ink([(1610, 640), (1600, 700), (1580, 738)], 3.0, seed=112)
        for f, sd in ((S['b_footL'], 113), (S['b_footR'], 114)):
            b.fluff(f, 'ink', length=(16, 26), curl=0.4, width=3.0, gaps=0.15, seed=sd)
        for (x, y) in ((1500, 960), (1520, 956), (1540, 958), (1752, 966), (1770, 962), (1788, 965)):
            b.dot(x, y - 10, 4.5, 4.0, colour='slate', medium='crayon', seed=x)
        # kid
        b.head(1100, 652, 74, 70, width=5.2, ears=[(1028, 668, 14)], seed=120)
        b.eyes([(1082, 660), (1126, 654)], r=7.2, look=(0.8, -0.6), seed=121)
        b.smile(1108, 690, 18, 6, 2.8, tilt=-6, seed=122)
        b.ink([(1101, 668), (1097, 677), (1104, 679)], 2.3, seed=123)       # a little nose
        b.outline([(1078, 728), (1134, 728), (1150, 760), (1180, 884), (1106, 892), (1030, 884), (1060, 760)], 4.6,
                  smooth=False, open_=0.6, seed=124)
        b.ink([(1092, 730), (1102, 748), (1120, 730)], 3.0, seed=125)        # collar
        for (x, y) in ((1106, 776), (1110, 812), (1113, 848)):
            b.dot(x, y, 3.6, seed=int(y))
        b.ink([(1158, 764), (1198, 698), (1222, 630)], 4.2, swell=0.35, seed=127)
        b.ink([(1116, 742), (1172, 662), (1214, 596)], 4.2, swell=0.35, seed=128)
        b.ink([(1140, 760), (1176, 700)], 3.0, seed=129)
        for (x, y) in ((1214, 618), (1228, 584)):                           # mitten hands on the shaft
            b.outline(np.array([(x + 13 * np.cos(t), y + 11 * np.sin(t)) for t in np.linspace(0, 6.2, 12)]), 3.0,
                      open_=0.3, seed=int(x + y))
        b.ink([(1084, 884), (1080, 922)], 6.0, dry=0.1, seed=130)           # stick legs
        b.ink([(1118, 888), (1124, 922)], 6.0, dry=0.1, seed=131)
        # umbrella
        b.outline(canopy_pts(), 4.8, smooth=False, open_=0.5, seed=140)
        for ui in (-66, 0, 66):
            b.ink(rib(ui), 2.8, seed=141 + ui)
        tip = at(0, CAN_H + 18)
        b.ink([at(0, CAN_H - 2), tip], 4.4, seed=142)
        hook = [at(0, -10), at(0, -150), at(0, -232), at(-6, -250), at(-20, -254), at(-30, -244)]
        b.ink(hook, 5.0, dry=0.15, seed=143)
        # bus stop
        b.outline([(512, 534), (908, 506), (914, 542), (508, 572)], 4.6, smooth=False, seed=150)
        b.ink([(560, 566), (556, 930)], 6.4, swell=0.3, seed=151); b.ink([(872, 540), (876, 930)], 6.4, swell=0.3, seed=152)
        b.outline([(584, 796), (838, 792), (840, 812), (582, 816)], 3.2, smooth=False, seed=153)
        b.ink([(574, 568), (570, 796)], 2.4, seed=154); b.ink([(862, 550), (866, 792)], 2.4, seed=155)
        for x in (604, 816):
            b.ink([(x, 816), (x + 4, 912)], 3.6, seed=x + 1)
        b.outline([(455 + 46 * np.cos(t), 398 + 46 * np.sin(t)) for t in np.linspace(0, 6.1, 24)], 3.6, seed=155)
        b.ink([(455, 444), (458, 930)], 5.0, seed=156)
        # snail, content on its dry bench
        t = np.linspace(0.3, 4.6 * np.pi, 60)
        rr = 26 * (1 - t / (5.2 * np.pi))
        b.ink(np.stack([712 + rr * np.cos(t), 766 + rr * np.sin(t)], 1), 2.8, seed=157)
        b.ink([(664, 792), (690, 795), (736, 794), (764, 786), (778, 770), (772, 758), (760, 760)], 3.0, seed=158)
        b.ink([(768, 760), (760, 734)], 2.2, seed=159); b.ink([(776, 762), (786, 738)], 2.2, seed=160)
        b.dot(759, 731, 3.2); b.dot(787, 735, 3.2)
        b.smile(772, 774, 8, 3, 2.0, tilt=-20, seed=161)
        # lamppost
        b.outline([(152, 158), (198, 158), (206, 214), (144, 214)], 3.4, smooth=False, seed=161)
        b.ink([(140, 160), (175, 136), (210, 160)], 3.6, seed=162)
        b.ink([(175, 214), (173, 560), (176, 920)], 10.0, dry=0.35, swell=0.35, seed=163)
        b.ink([(160, 920), (192, 920)], 8.0, seed=164)
        # ducks
        for (x, y, s) in self.ducks:
            b.outline([(x - 46 * s, y - 2 * s), (x - 30 * s, y - 24 * s), (x + 10 * s, y - 22 * s), (x + 36 * s, y - 10 * s),
                       (x + 52 * s, y - 30 * s), (x + 44 * s, y + 4 * s), (x + 20 * s, y + 14 * s), (x - 30 * s, y + 12 * s)],
                      3.0 * max(s, 0.7), open_=0.5, seed=int(x))
            t = np.linspace(np.deg2rad(-30), np.deg2rad(250), 24)
            b.ink(np.stack([x - 34 * s + np.cos(t) * 19 * s, y - 40 * s + np.sin(t) * 18 * s], 1), 2.8 * max(s, 0.7), seed=int(x) + 1)
            b.dot(x - 38 * s, y - 44 * s, 3.2 * max(s, 0.6))
            b.ink([(x - 6 * s, y - 8 * s), (x + 12 * s, y - 2 * s), (x + 24 * s, y - 10 * s)], 2.4 * max(s, 0.7), seed=int(x) + 2)
        # puddle lips and the ground line
        for (x, y, rx, ry, sd) in self.puddles:
            t = np.linspace(np.deg2rad(10), np.deg2rad(170), 30)
            b.ink(np.stack([x + np.cos(t) * rx * 0.98, y + np.sin(t) * ry * 0.95], 1), 3.0, dry=0.3, seed=sd + 200)
        r = np.random.default_rng(5)
        for _ in range(40):
            x, y = r.uniform(80, 1840), r.uniform(915, 1060)
            if S['puddles'][int(y), int(x)] > 0.3 or S['front'][int(y), int(x)] > 0.3: continue
            L = r.uniform(8, 26)
            b.ink([(x, y), (x + L, y + r.uniform(-2, 2))], r.uniform(1.8, 3.2), dry=0.4, seed=int(x * 7))

    # ============================================================ 4 dark scribbled masses
    def dark(self):
        b, S, X, Y = self.b, self.S, self.XX, self.YY
        front = S['front']
        for i, (m, col, sd) in enumerate(S['bushes']):
            r = np.random.default_rng(sd + 500)
            rows = np.flatnonzero(m.max(1) > 0.5)
            y0, y1 = rows[0], rows[-1]
            g = (Y - y0) / max(1, y1 - y0) + 0.9 * (self.N - 0.5) + 0.06 * np.sin(X / 9.0 + sd)
            dark = m * (g > (0.66 if col == 'teal' else 0.9)) * (1 - front) * (Y < base_y(X) + 4)
            b.scribble(dark.astype(np.float32), width=5.2, spacing=4.6 if col == 'teal' else 6.0,
                       angle=r.uniform(68, 82) * r.choice([-1, 1]) % 180, colour=INK if col == 'teal' else 'navy',
                       dry=0.5, overshoot=10, clip=1 - front, seed=sd + 1)
            xs = np.flatnonzero(m.max(0) > 0.5)
            b.blades(xs[0] + 10, xs[-1] - 10, lambda x: float(base_y(x)) + 8, n=int(len(xs) / 24), height=(40, 120 if col == 'teal' else 80),
                     lean=r.uniform(-8, 8), width=4.6, dry=0.3, clip=1 - front, seed=sd + 2)
        b.blades(70, 1850, lambda x: float(base_y(x)) + 6, n=24, height=(20, 60), width=3.4, clip=1 - front, seed=520)
        # shelter roof underside, boots
        b.scribble(S['roof'] * (Y > 542 - (X - 508) * 0.07), width=3.6, spacing=4.0, angle=-6, dry=0.4, seed=530)
        for k in ('k_bootL', 'k_bootR'):
            b.fill(S[k], '#22232b', pressure=0.95, angle=10, slip=0, loose=1.5, edge=3, lanes=0, medium='gouache', seed=533)
            b.scribble(S[k], width=4.0, spacing=3.6, angle=20, dry=0.5, overshoot=2, seed=531 if k[-1] == 'L' else 532)
        # hatch: coat shadow, bench shadow, bear fur shadow
        b.hatch(S['k_coat'] * smoothstep(1120, 1150, X + (Y - 760) * 0.25), angle=74, spacing=7, length=(16, 34),
                width=2.2, dry=0.4, seed=540)
        b.hatch(S['seat'] * (X > 700) * (1 - S['snail']), angle=-80, spacing=9, length=(8, 12), width=2.0, seed=541)
        fur = S['bear'] * smoothstep(1730, 1800, X + 0.3 * (Y - 600)) * (1 - S['b_footR'])
        b.hatch(fur, angle=-70, spacing=16, length=(16, 30), width=3.0, colour='cornflower', medium='crayon',
                dry=0.55, bend=0.25, density=0.7, seed=542)
        b.hatch(S['b_body'] * (Y > 900) * (1 - np.maximum(S['b_footL'], S['b_footR'])), angle=-20, spacing=16,
                length=(16, 28), width=3.0, colour='cornflower', medium='crayon', dry=0.55, bend=0.25, density=0.6, seed=543)
        b.hatch(S['b_head'] * smoothstep(1700, 1745, X), angle=-60, spacing=14, length=(12, 22), width=2.6,
                colour='cornflower', medium='crayon', dry=0.55, bend=0.3, density=0.7, seed=544)

    # ============================================================ 5 coral accents and cheeks
    def accents(self):
        b, S, X, Y = self.b, self.S, self.XX, self.YY
        b.fill(S['canopy'], 'coral', pressure=0.96, angle=-30, loose=3, mottle=0.12, medium='crayon', seed=600)
        rshade = S['canopy'] * smoothstep(40, 110, (X - RC[0]) * PX[0] + (Y - RC[1]) * PX[1])
        b.hatch(rshade, angle=60, spacing=6, length=(14, 30), width=3.0, colour='tomato', medium='crayon', dry=0.4, seed=601)
        hair = np.maximum.reduce([S['k_hair'], S['k_bunL'], S['k_bunR']])
        b.fill(hair, 'coral', pressure=0.95, angle=20, loose=2.5, seed=602)
        b.crayon([[(1036 + k * 15, 596 + 6 * (k % 3)), (1042 + k * 15, 626 + 4 * (k % 2))] for k in range(10)],
                 'tomato', width=4, pressure=0.85, dry=0.3, seed=603)
        for (x, y) in ((1012, 596), (1190, 588)):                           # the bunches
            b.crayon([[(x - 12, y - 6 + k * 5), (x + 12, y - 4 + k * 5)] for k in range(3)], 'tomato', width=3,
                     pressure=0.8, seed=int(x))
        b.ink([(1036, 626), (1052, 612), (1080, 604), (1110, 598), (1140, 600), (1166, 614)], 2.6, dry=0.3, seed=604)
        b.ink([(1012, 584), (996, 594), (1004, 610)], 2.4, seed=605); b.ink([(1188, 576), (1206, 588), (1196, 602)], 2.4, seed=606)
        b.fill(S['k_head'] * (1 - hair) * (Y > 612), 'flesh', pressure=0.5, angle=30, loose=2, edge=6, dry_edge=0.5,
               lanes=0, seed=607)
        b.blush(1060, 686, 16, seed=608); b.blush(1144, 678, 15, seed=609)
        b.freckles(1101, 672, 4, 13, seed=610)
        b.blush(1503, 533, 24, seed=611); b.blush(1636, 522, 22, seed=612)
        b.blush(1336, 598, 9, seed=613, density=0.6)
        # flowers in the bushes, duck bills, snail shell, lamp glow
        r = np.random.default_rng(620)
        for (fx, fy, k) in ((120, 812, 3), (395, 770, 2), (690, 842, 2), (1000, 800, 3), (1340, 836, 2)):
            for j in range(k):
                x, y = fx + r.uniform(-28, 28), fy + r.uniform(-18, 18)
                if S['front'][int(y), int(x)] > 0.2: continue
                b.ink([(x, y + 4), (x + r.uniform(-6, 6), y + r.uniform(30, 50))], 2.2, seed=int(x) + j)
                b.flower(x, y, r.uniform(7.5, 10.5), 'coral', seed=int(x * 3) + j)
        for (body, head, bill) in S['duck_parts']:
            b.fill(bill, 'mustard', pressure=0.95, slip=0, loose=1, edge=3, lanes=0, medium='gouache', seed=630)
        b.fill(S['shell'], 'mustard', pressure=0.9, angle=40, loose=2, seed=631)
        b.fill(S['lamp'], 'butter', pressure=0.9, angle=0, loose=2, seed=632)
        b.crayon([[(175 + np.cos(a) * 44, 186 + np.sin(a) * 44), (175 + np.cos(a) * 64, 186 + np.sin(a) * 64)]
                  for a in np.deg2rad([200, 235, 270, 305, 340])], 'mustard', width=5, pressure=0.8, seed=633)

    # ============================================================ 6 chalky whites
    def chalk(self):
        b, S, X, Y = self.b, self.S, self.XX, self.YY
        for i, (x, y, w, h) in enumerate([(380, 160, 300, 110), (1120, 128, 250, 92), (1690, 178, 240, 92)]):
            b.chalk(b.cloud(x, y, w, h, 5, seed=700 + i), pressure=0.82, angle=-6, seed=700 + i)
            b.chalk([[(x - w * 0.35, y + h * 0.3), (x + w * 0.3, y + h * 0.32)]], width=8, pressure=0.6, seed=710 + i)
        b.fluff(S['bear'] * (1 - S['kid']) * (1 - S['canopy']), 'chalk', length=(18, 30), width=5.5, reach=(0.35, 0.75),
                seed=720)
        b.chalk([[(1222, 380), (1262, 352), (1300, 338)], [(1240, 404), (1272, 384)]], width=6, pressure=0.75, seed=721)
        b.chalk([[(1384, 600), (1410, 596)]], width=4, pressure=0.8, seed=722)
        for (x, y, rx, ry, sd) in self.puddles:
            r = np.random.default_rng(sd)
            for k in range(2 if rx < 120 else 4):
                cx, cy = x + r.uniform(-0.6, 0.6) * rx, y + r.uniform(-0.3, 0.2) * ry
                if S['ducks'][int(cy), int(cx)] > 0.3: continue
                b.ripples(cx, cy, r.uniform(14, 30), r.uniform(4, 6), rings=2, width=2.6, seed=sd * 10 + k)
        for (x, y, s) in self.ducks:
            b.ripples(x, y + 14 * s, 60 * s, 9 * s, rings=2, width=2.6, seed=int(x) + 3)
        b.chalk([[(620, 600), (660, 560)], [(640, 640), (700, 580)], [(780, 620), (820, 580)]], width=5,
                pressure=0.55, seed=730)                                       # glass glints in the shelter
        # a tiny white bus on the round sign
        b.chalk(b.poly([(428, 382), (478, 382), (484, 408), (426, 410)], smooth=False), pressure=0.95, angle=0,
                edge=2, dry_edge=0.3, loose=1, seed=731)
        b.dot(440, 412, 4.6, colour='navy', medium='gouache'); b.dot(470, 412, 4.6, colour='navy', medium='gouache')
        for x in (436, 452, 468):
            b.dot(x, 391, 4.0, 3.4, colour='cobalt', medium='gouache')
        b.chalk([[(1092, 762), (1088, 860)]], width=6, pressure=0.6, seed=732)          # coat sheen
        b.chalk([[(1200, 960), (1260, 962)], [(1330, 1000), (1420, 1002)]], width=5, pressure=0.6, seed=733)

    # ============================================================ 7 rain, splashes, speckle
    def rain(self):
        b, S, X, Y = self.b, self.S, self.XX, self.YY
        sky = (b.rect(70, 60, 1850, 1060, rough=6, seed=31) > 0.5).astype(np.float32)
        dry = np.maximum(S['dry'], S['canopy'])
        b.rain(sky * (Y < 905), n=560, angle=RAIN_ANG, length=(10, 40), width=(1.6, 3.0), colour='deep', avoid=dry, seed=800)
        b.rain(sky * (Y < 905), n=260, angle=RAIN_ANG, length=(10, 30), width=(1.6, 2.6), colour='cornflower', avoid=dry, seed=804)
        b.rain(sky * (Y < 905), n=240, angle=RAIN_ANG, length=(12, 28), width=(1.8, 3.0), colour='chalk', avoid=dry, seed=801)
        b.rain(S['bear'] * (1 - S['dry']), n=45, angle=RAIN_ANG, length=(12, 24), width=(1.6, 2.4), colour='powder',
               avoid=dry, seed=802)
        b.rain((80, 905, 1840, 1050), n=140, angle=RAIN_ANG, length=(10, 22), width=(1.5, 2.4), colour='cornflower',
               avoid=dry, seed=803)
        r = np.random.default_rng(810)
        for (x, y) in [(1060, 592), (1100, 584), (1140, 590), (1010, 580), (1192, 572), (1080, 588)]:   # on her hair
            b.splash(x, y, 15, 'chalk', n=5, width=2.6, seed=int(x))
        for (x, y) in [(1004, 612), (1200, 604), (1036, 640)]:                                  # drips off her bunches
            b.ink([(x, y), (x + 1, y + 12)], 3.0, colour='deep', dry=0.2, seed=int(x) + 3)
            b.dot(x + 2, y + 24, 2.6, 3.5, colour='deep', medium='crayon')
        for (x, y) in [(1520, 352), (1600, 344), (1680, 360), (1470, 360), (1700, 372), (1750, 420)]:   # bear's head
            b.splash(x, y, 13, 'deep', n=4, width=2.2, seed=int(x) + 1)
        for u in (-110, -60, -10, 40, 90):                                                  # on the canopy
            p = at(u, CAN_H * np.sqrt(max(0.05, 1 - (u / CAN_R) ** 2)) + 2)
            b.splash(p[0], p[1], 12, 'chalk', n=4, width=2.4, up=-90 + np.degrees(TILT) * 0.6, seed=int(u) + 900)
        for u in (-130, -80, 30, 82, 130):                                                  # drips off the rim
            p = at(u, -10)
            b.ink([(p[0], p[1] + 6), (p[0] + 1.5, p[1] + 16)], 3.2, colour='deep', dry=0.2, seed=int(u) + 950)
            b.dot(p[0] + 3, p[1] + 28, 2.6, 3.4, colour='deep', medium='crayon')
        for (x, y) in [(1692, 336), (1500, 335), (1066, 668), (1150, 696)]:                  # drops on ear tips and cheeks
            b.dot(x, y + 18, 3.0, 4.2, colour='deep', medium='crayon')
            b.dot(x - 1, y + 16, 1.0, colour='chalk', medium='chalk')
        for (x, y, rx, ry, sd) in self.puddles:
            for k in range(3):
                xx = x + r.uniform(-0.7, 0.7) * rx
                b.splash(xx, y + r.uniform(-0.3, 0.3) * ry, 9, 'chalk', n=3, width=2.0, seed=sd * 7 + k)
        # coral reflection of the umbrella in the puddle
        refl = []
        for j, (y, x0, x1) in enumerate([(990, 1222, 1392), (998, 1236, 1380), (1006, 1258, 1362), (1014, 1282, 1338)]):
            cuts = np.sort(r.uniform(x0, x1, 2))
            for a, c in ((x0, cuts[0] - 5), (cuts[0] + 4, cuts[1] - 5), (cuts[1] + 4, x1)):
                if c - a > 8: refl.append([(a, y + r.uniform(-1, 1)), (c, y + r.uniform(-1, 1))])
        b.crayon(refl, 'coral', width=6, pressure=0.8, dry=0.45, alpha=0.8, medium='gouache', seed=820)
        b.crayon([[(1300, 1016), (1300, 1034)]], 'ink', width=3, pressure=0.6, dry=0.5, seed=821)
        b.spatter(sky, 'ink', n=55, size=(0.8, 3.6), avoid=np.maximum(S['bear'], S['kid']), seed=830)
        b.spatter(sky, 'chalk', n=160, size=(0.8, 3.2), avoid=np.maximum(S['bear'], S['canopy']), seed=831)
        b.speckle(sky, 'chalk', n=1400, size=(0.5, 1.4), seed=832)
        b.speckle((60, 900, 1860, 1070), 'cornflower', n=500, size=(0.5, 1.5), seed=833)
        b.speckle(sky * (Y > 700), 'navy', n=500, size=(0.5, 1.3), seed=834)

    def finish(self):
        b = self.b
        b.folio(104, 1046, '14', 19); b.folio(1816, 1046, '15', 19)
        b.printed(1.0, gutter=GUTTER)


PHASES = ('blue', 'ink', 'dark', 'accents', 'chalk', 'rain')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'bluebook_shared_umbrella.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:10s} {time.time() - T0:5.1f}s')) if os.environ.get('BB_TIMING') else (lambda n: None)
    b = BlueBook(W, H, seed=21, keep_stages=bool(stages), stages_dir=stages)
    b.paper()
    b.stage('paper')
    sp = Spread(b)
    tick('setup')
    for ph in PHASES:
        getattr(sp, ph)()
        tick(ph)
        b.stage(ph)
    sp.finish()
    b.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out)


if __name__ == '__main__':
    main()
