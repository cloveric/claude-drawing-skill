"""Example (sketchbook doodle): 读书的午后 · The Reading Hour -- a page from an illustrator's sketchbook.

A girl sits on a little wooden stool and reads, the book held up in both hands, her head bowed over it, eyes
closed in that way of someone deep in a story. Long wavy dark hair parted in the middle, a rainbow-striped jumper with
a red ribbed neck and mustard cuffs, a blue pleated skirt, white socks and red shoes. Her grey tabby is curled up
asleep on the floor beside a mug whose steam curls up into the empty page; on the other side a potted plant puts out
a few leaves (one inked with herringbone veins, one blue with its veins left white) and a red bud; a single leaf
drifts down. Everything floats on a big warm page: no ground, no background.

Drawn in the order a sketchbook illustrator works: the paper -> the fine ink line drawing (face, neck, jumper and
sleeves, the book and the fingers on it, skirt, legs, shoes, the stool behind) -> the hair, strand by strand -> the
stripes in colour pencil and marker -> the other colour (skirt, cuffs and neck, the book cover, shoes, the stool) ->
the cat -> the plant -> the mug and its steam -> the face (closed eyes, nose, blush, mouth) -> a drifting leaf and a
little doodle. --stages writes those steps as snapshots for the draw-on. No image model.
python3 sketchbook_reading_hour.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from sketchbook import Sketchbook

W, H = 1600, 1600
HEAD = np.array([800.0, 610.0])          # centre of the face
TILT = -5.0                              # the head leans a little toward her right shoulder
BOOK_TILT = -4.0                         # the book is held a little crooked


def rot(pts, deg=TILT, c=HEAD):
    """turn points about the face centre (the head's tilt)"""
    a = np.deg2rad(deg); cs, sn = np.cos(a), np.sin(a)
    P = np.asarray(pts, np.float32) - c
    return np.stack([P[:, 0] * cs - P[:, 1] * sn, P[:, 0] * sn + P[:, 1] * cs], 1) + c


def mirror(pts, x=800.0):
    P = np.asarray(pts, np.float32).copy(); P[:, 0] = 2 * x - P[:, 0]
    return P


class Scene:
    def __init__(self, p):
        self.p = p
        self.M = {}
        self.plan()

    # masks are kept as uint8 (a quarter of the memory of float32)
    def put(self, k, m):
        self.M[k] = np.round(np.clip(m, 0, 1) * 255).astype(np.uint8)

    def m(self, *ks):
        out = None
        for k in ks:
            a = self.M[k].astype(np.float32) * np.float32(1 / 255)
            out = a if out is None else np.maximum(out, a)
        return out

    def grow(self, *ks, px=2.5):
        """the union of some masks grown by a few px (a line stops just short of what is in front of it)"""
        return self.p.grow(self.m(*ks), px)

    # ------------------------------------------------------------------ shapes
    def plan(self):
        p = self.p
        # the head: face, neck, the hair's two locks (from the parting, the hairline sweeping over the forehead)
        self.face_pts = rot([(800, 534), (840, 541), (864, 572), (868, 615), (860, 655), (836, 686), (800, 698),
                             (764, 686), (740, 655), (732, 615), (736, 572), (760, 541)])
        self.put('face', p.poly(self.face_pts, smooth=True))
        self.put('neck', p.poly([(786, 680), (814, 680), (815, 742), (785, 742)]))
        apex = (806, 548)                # where the parting meets the forehead
        rg = [[apex, (815, 568), (832, 592), (854, 612), (867, 640), (872, 676), (878, 716), (888, 758), (899, 800)],
              [(806, 530), (832, 534), (860, 556), (882, 592), (895, 636), (899, 690), (907, 746), (920, 792),
               (932, 826)],
              [(808, 516), (848, 511), (884, 528), (907, 564), (918, 620), (922, 682), (930, 742), (944, 794),
               (958, 830)]]
        self.lock_r = [rot(g) for g in rg]
        self.lock_l = [rot(mirror(g, 806)) for g in rg]
        hr = np.vstack([self.lock_r[0], self.lock_r[-1][::-1]])
        hl = np.vstack([self.lock_l[0], self.lock_l[-1][::-1]])
        self.put('hair', np.maximum(p.poly(hr, smooth=False), p.poly(hl, smooth=False)))
        # the face you see: the oval below the hairline
        below = np.vstack([self.lock_r[0][:8], [(900, 900), (712, 900)], self.lock_l[0][:8][::-1]])
        self.put('face_vis', self.m('face') * p.poly(below))
        # the jumper: body, two sleeves bent to hold the book, a ribbed neck, cuffs
        self.body_pts = [(772, 735), (742, 742), (712, 754), (705, 800), (703, 900), (700, 986), (800, 994),
                         (900, 986), (897, 900), (895, 800), (888, 754), (858, 742), (828, 735)]
        self.put('body', p.poly(self.body_pts, smooth=True))
        self.arm_l = [(718, 768), (697, 836), (690, 884), (708, 908), (746, 916)]
        self.arm_r = [(882, 768), (904, 832), (913, 878), (894, 902), (856, 909)]
        self.sleeve_l = p.tube_pts(self.arm_l, [62, 58, 54, 50, 46])
        self.sleeve_r = p.tube_pts(self.arm_r, [62, 58, 54, 50, 46])
        self.put('sleeve_l', p.poly(self.sleeve_l)); self.put('sleeve_r', p.poly(self.sleeve_r))
        # the open book held up (a little crooked) in front of her, its covers toward us; three fingers on each cover
        book = lambda pts: rot(pts, BOOK_TILT, (800, 905))
        self.book = book
        self.cover_l = book([(724, 846), (800, 857), (800, 962), (728, 953)])
        self.cover_r = book(mirror([(724, 846), (800, 857), (800, 962), (728, 953)]))
        self.put('book', np.maximum(p.poly(self.cover_l), p.poly(self.cover_r)))
        self.fingers = []
        for side in (-1, 1):
            for i, (fy, fl) in enumerate(((889, 13), (900, 15), (911, 13))):
                x0 = 800 + side * 77
                x1 = x0 - side * fl
                pts = [(x0, fy - 4.6), (x1 + side * 2.5, fy - 4.8), (x1, fy), (x1 + side * 2.5, fy + 4.8), (x0, fy + 4.6)]
                self.fingers.append(book(pts))
        fm = np.zeros((H, W), np.float32)
        for f in self.fingers: fm = np.maximum(fm, p.poly(f, smooth=True))
        self.put('fingers', fm)
        # skirt, legs, shoes
        self.skirt_pts = [(708, 968), (800, 974), (892, 968), (904, 1020), (914, 1066), (858, 1072), (800, 1068),
                          (742, 1072), (686, 1066), (696, 1020)]
        self.put('skirt', p.poly(self.skirt_pts, smooth=False))
        self.leg_l = [(779, 1060), (778, 1150), (777, 1220), (777, 1294)]
        self.leg_r = [(821, 1060), (825, 1146), (831, 1212), (839, 1278)]
        self.legw = [27, 26, 22, 18]
        self.put('legs', np.maximum(p.tube(self.leg_l, self.legw), p.tube(self.leg_r, self.legw)))
        self.shoe_l = [(766, 1288), (786, 1288), (800, 1296), (806, 1306), (796, 1314), (770, 1314), (762, 1302)]
        self.shoe_r = rot([(830, 1270), (850, 1270), (856, 1284), (850, 1297), (826, 1298), (814, 1292), (818, 1280)],
                          8, (838, 1284))
        self.put('shoes', np.maximum(p.poly(self.shoe_l, smooth=True), p.poly(self.shoe_r, smooth=True)))
        # the stool behind her: a round seat, two splayed legs, a rung (a third leg between hers read as a third leg)
        self.seat = p.ellipse_pts(800, 1050, 130, 19)
        self.put('seat', np.maximum(p.ellipse(800, 1050, 130, 19), p.poly([(670, 1050), (930, 1050), (928, 1066),
                                                                             (672, 1066)])))
        self.stool_legs = [[(696, 1062), (668, 1326)], [(904, 1062), (932, 1326)]]
        self.put('stool_legs', np.maximum.reduce([p.tube(l, 13, 11) for l in self.stool_legs]))
        self.rung = [(680, 1220), (920, 1220)]
        self.put('rung', p.tube(self.rung, 9))

    # ------------------------------------------------------------------ 1. the ink line drawing
    def lines(self):
        p = self.p
        front_of_face = self.grow('hair', px=1.5)
        # face: only the cheeks and the chin, a lighter line, open at the top (the hair frames it)
        fp = p.closed_pts(self.face_pts)
        n = len(fp)
        p.ink(fp[int(0.18 * n):int(0.47 * n)], 1.9, 'ink_soft', avoid=front_of_face, seed=11)
        p.ink(fp[int(0.53 * n):int(0.83 * n)], 1.9, 'ink_soft', avoid=front_of_face, seed=12)
        # neck
        p.inks([[(788, 692), (787, 716), (786, 736)], [(812, 692), (813, 716), (814, 736)]], 1.9, 'ink',
               avoid=self.grow('face'), seed=13)
        fr_body = self.grow('sleeve_l', 'sleeve_r', 'book', 'fingers', 'hair')
        p.contour(self.body_pts, pieces=(2, 3), width=2.1, avoid=fr_body, seed=14)
        # a ribbed crew neck
        nb_top = [(771, 735), (800, 741), (829, 735)]
        nb_bot = [(764, 748), (800, 756), (836, 748)]
        p.inks([nb_top, nb_bot], 1.8, seed=15)
        # sleeves (the near forearm passes in front of the body), cuffs
        fr_sl = self.grow('book', 'fingers', 'hair')
        for k, (pts, arm) in enumerate(((self.sleeve_l, self.arm_l), (self.sleeve_r, self.arm_r))):
            p.ink(pts, 2.1, avoid=fr_sl, smooth=False, gaps=0.6, seed=20 + k)
            # the elbow crease
            a = np.asarray(arm, np.float32)
            p.ink([a[2] + (8 if k == 0 else -8, -4), a[2] + (14 if k == 0 else -14, 8)], 1.6, seed=22 + k)
        # the book: two covers in a shallow V, the page block's top edges, the spine
        bk = self.grow('fingers', px=1.2)
        for k, cv in enumerate((self.cover_l, self.cover_r)):
            p.contour(cv, pieces=(2, 3), width=2.0, smooth=False, avoid=bk, seed=30 + k)
        for i, dy in enumerate((5, 9, 13)):
            p.ink(self.book([(731, 846 - dy * 0.6), (764, 848 - dy), (797, 856 - dy)]), 1.3, alpha=0.8, seed=33 + i)
            p.ink(self.book([(869, 846 - dy * 0.6), (836, 848 - dy), (803, 856 - dy)]), 1.3, alpha=0.8, seed=36 + i)
        for k, f in enumerate(self.fingers):
            p.contour(f, pieces=1, width=1.7, p_gap=1.0, gap=(2, 5), seed=40 + k)
        # skirt and its pleats
        fr_sk = self.grow('body', 'sleeve_l', 'sleeve_r', 'book')
        p.contour(self.skirt_pts, pieces=(2, 3), width=2.0, smooth=False, avoid=fr_sk, seed=50)
        for i, x in enumerate((736, 770, 832, 866)):
            p.ink([(x + (x - 800) * 0.02, 990), (x + (x - 800) * 0.12, 1066)], 1.4, alpha=0.75, avoid=fr_sk,
                  seed=51 + i)
        # legs (only their sides), socks, shoes with a strap
        fr_leg = self.grow('skirt', 'shoes', px=1.5)
        for k, leg in enumerate((self.leg_l, self.leg_r)):
            o = p.tube_pts(leg, self.legw)
            m = len(o) // 2
            p.inks([o[:m], o[m:]], 1.9, avoid=fr_leg, seed=60 + k)
            sx, sy = np.asarray(leg)[-1]
            cy = sy - 30
            p.ink([(sx - 11, cy), (sx, cy + 3), (sx + 11, cy)], 1.6, avoid=fr_leg, seed=62 + k)
            p.inks([[(sx + d, cy + 4), (sx + d * 0.95, cy + 20)] for d in (-6, -1, 4, 8)], 1.0, alpha=0.6,
                   avoid=fr_leg, seed=64 + k)
        for k, sh in enumerate((self.shoe_l, self.shoe_r)):
            p.contour(sh, pieces=(1, 2), width=2.0, seed=66 + k)
        p.inks([[(772, 1300), (782, 1297), (792, 1300)], rot([(828, 1284), (838, 1281), (848, 1283)], 8, (838, 1284))],
               1.5, seed=68)
        # the stool, behind everything
        fr_st = self.grow('skirt', 'legs', 'shoes', 'body', 'sleeve_l', 'sleeve_r', px=2.0)
        p.contour(self.seat, pieces=2, width=1.9, avoid=fr_st, smooth=False, seed=70)
        p.inks([[(670, 1051), (672, 1066)], [(930, 1051), (928, 1066)], [(672, 1066), (800, 1072), (928, 1066)]],
               1.8, avoid=fr_st, seed=71)
        for k, lg in enumerate(self.stool_legs):
            o = p.tube_pts(lg, 13, 11)
            m = len(o) // 2
            p.inks([o[:m], o[m:]], 1.7, avoid=fr_st, seed=72 + k)
        ro = p.tube_pts(self.rung, 9)
        m = len(ro) // 2
        p.inks([ro[:m], ro[m:]], 1.5, avoid=self.grow('legs', 'stool_legs', px=1.5), seed=76)

    # ------------------------------------------------------------------ 2. hair
    def hair(self):
        p = self.p
        self.clip_c = rot([(886, 600)])[0]
        cm = p.ellipse(self.clip_c[0], self.clip_c[1], 12, 12)
        av = np.maximum(self.grow('face_vis', px=1.0), cm)
        p.hair(self.lock_r, n=34, width=2.2, wave=(5.0, 110), wave_root=0.0, cohere=0.6, avoid=av, seed=80)
        p.hair(self.lock_l, n=34, width=2.2, wave=(5.0, 110), wave_root=0.0, cohere=0.6, avoid=av, seed=81)

        # a little daisy clip, the hair parted round it
        c = self.clip_c
        p.flower(c[0], c[1], 10, 'orange', 'daisy', lw=1.7, seed=84)

    # ------------------------------------------------------------------ 3. stripes
    def stripes(self):
        p = self.p
        front = self.m('sleeve_l', 'sleeve_r', 'book', 'fingers', 'hair')
        rainbow = ['red', 'yellow', 'teal', 'orange', 'magenta', 'gold', 'turquoise', 'red', 'yellow', 'blue']
        p.stripes(self.m('body'), rainbow, across=90, bend=7, band=(13, 22), gap=(6, 12), avoid=front, start=22,
                  seed=90)
        fr = self.m('book', 'fingers', 'hair')
        for k, arm in enumerate((self.arm_l, self.arm_r)):
            m = self.m('sleeve_l' if k == 0 else 'sleeve_r')
            cuff = p.tube(np.asarray(arm)[-2:].tolist(), 52, 48)
            p.stripes(m * (1 - cuff), ['yellow', 'red', 'teal', 'orange', 'magenta', 'turquoise'], path=arm,
                      band=(11, 18), gap=(6, 10), avoid=fr, start=14, seed=91 + k)

    # ------------------------------------------------------------------ 4. the other colour
    def colour(self):
        p = self.p
        # ribbed neck in red, mustard cuffs, both with rib lines
        nb = p.poly([(771, 735), (800, 741), (829, 735), (836, 748), (800, 756), (764, 748)], smooth=False)
        p.tint(nb, 'red', 0, 0.9, 0.45, overrun=1.5, seed=100)
        p.inks([[(770 + i * 6.5, 737 + 0.5 * abs(i - 4.5)), (766 + i * 7.3, 749 + 0.6 * abs(i - 4.5))]
                for i in range(1, 10)], 1.0, alpha=0.7, seed=101)
        fr = self.m('book', 'fingers')
        for k, arm in enumerate((self.arm_l, self.arm_r)):
            a = np.asarray(arm, np.float32)
            cuff = p.tube(a[-2:].tolist(), 52, 48) * self.m('sleeve_l' if k == 0 else 'sleeve_r')
            p.tint(cuff, 'gold', 0, 0.92, 0.4, avoid=fr, overrun=1.5, seed=102 + k)
            d = a[-1] - a[-2]; d /= np.linalg.norm(d); nrm = np.array([-d[1], d[0]])
            ribs = [[a[-2] + d * t + nrm * 22, a[-2] + d * t - nrm * 22] for t in np.linspace(4, 34, 7)]
            p.inks(ribs, 1.0, alpha=0.7, avoid=self.grow('book', 'fingers', px=1.0), seed=104 + k)
        # the skirt: blue pencil laid in vertical strokes
        p.tint(self.m('skirt'), 'cobalt', 88, 0.82, 0.6, 0.6, 0.85, hatch=0.35, spacing=6.0,
               avoid=self.m('body', 'sleeve_l', 'sleeve_r', 'book'), shift=(2, 2), seed=106)
        # the book cover in teal with a little sun drawn on it
        sx, sy = self.book([(838, 900)])[0]
        sun = p.ellipse(sx, sy, 12, 12)
        p.tint(self.m('book'), 'teal', -40, 0.85, 0.55, 0.5, 0.88, avoid=np.maximum(self.m('fingers'), sun),
               shift=(-2, 1), seed=107)
        p.dots([(sx, sy)], 9, 'yellow', 0.95)
        p.inks([[(sx + 13 * np.cos(a), sy + 13 * np.sin(a)), (sx + 19 * np.cos(a), sy + 19 * np.sin(a))]
                for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)], 1.3, 'gold', seed=108)
        # red shoes in marker
        p.tint(self.m('shoes'), 'red', 10, 0.92, 0.2, 0.4, 0.95, overrun=1.5, shift=(1, -1), seed=109)
        # the stool: wood pencil on the seat edge and the legs
        st = self.m('seat', 'stool_legs', 'rung') * (1 - self.m('skirt', 'legs', 'shoes', 'body'))
        p.tint(st, 'wood', 80, 0.65, 0.65, 0.5, 0.8, seed=110)

    # ------------------------------------------------------------------ 5. the cat, asleep
    def cat(self):
        p = self.p
        body = [(410, 1302), (418, 1266), (452, 1244), (510, 1238), (562, 1246), (596, 1266), (606, 1300),
                (590, 1324), (540, 1334), (470, 1334), (428, 1324)]
        head_c = (588, 1288)
        head = p.ellipse_pts(head_c[0], head_c[1], 37, 31, -8)
        ears = [[(560, 1272), (565, 1246), (583, 1262)], [(596, 1259), (614, 1240), (619, 1268)]]
        tail = [(418, 1318), (446, 1338), (510, 1346), (566, 1338)]
        hm = np.maximum(p.poly(head), np.maximum(p.poly(ears[0]), p.poly(ears[1])))
        tm = p.tube(tail, 20, 14)
        bm = p.poly(body, smooth=True)
        p.tint(np.maximum.reduce([bm, hm, tm]), 'stone', 30, 0.45, 0.55, 0.5, 0.8, overrun=2.0, shift=(2, -2),
               seed=120)
        p.contour(body, pieces=(2, 3), width=1.9, avoid=p.grow(np.maximum(hm, tm)), seed=121)
        p.contour(head, pieces=2, width=1.9, smooth=False, avoid=p.grow(tm), seed=122)
        p.inks(ears, 1.9, smooth=False, seed=123)
        p.contour(p.tube_pts(tail, 20, 14), pieces=2, width=1.8, smooth=True, seed=124)
        # tabby stripes over the back, a few on the tail, fur ticks
        stripes = [[(462 + 26 * i, 1246 + 2 * abs(i - 2)), (458 + 26 * i, 1262 + 2 * abs(i - 2)),
                    (466 + 26 * i, 1276)] for i in range(5)]
        p.inks(stripes, 2.6, 'graphite', 0.8, taper=(3, 8), clip=bm, seed=125)
        p.inks([[(470 + 22 * i, 1336), (474 + 22 * i, 1346)] for i in range(4)], 2.4, 'graphite', 0.8, clip=tm,
               seed=126)
        p.ticks(bm * (1 - p.grow(hm)), 26, (5, 9), 75, 30, 1.0, 'ink', 0.55, seed=127)
        # the sleeping face
        p.eye_closed(574, 1292, 13, 3.0, lashes=0, rot=-8, width=1.6, seed=128)
        p.eye_closed(600, 1289, 13, 3.0, lashes=0, rot=-8, width=1.6, seed=129)
        p.inks([[(585, 1302), (588, 1305), (591, 1302)]], 1.6, seed=130)
        p.dots([(588, 1300)], 2.4, 'pink', 0.9)
        p.inks([[(568, 1302), (538, 1298)], [(568, 1306), (540, 1310)], [(610, 1300), (640, 1294)],
                [(610, 1305), (638, 1308)]], 1.1, alpha=0.75, seed=131)
        p.blush(566, 1300, 5, 'pink', 0.6); p.blush(610, 1297, 5, 'pink', 0.6)

    # ------------------------------------------------------------------ 6. the plant
    def plant(self):
        p = self.p
        pot = [(1048, 1252), (1142, 1252), (1131, 1328), (1059, 1328)]
        rim = [(1040, 1236), (1150, 1236), (1147, 1256), (1043, 1256)]
        pm, rm = p.poly(pot), p.poly(rim)
        p.tint(np.maximum(pm, rm), 'terracotta', 70, 0.72, 0.6, 0.55, 0.85, hatch=0.25, spacing=6, shift=(2, 2),
               seed=140)
        p.contour(rim, pieces=2, width=1.9, smooth=False, seed=141)
        p.contour(pot, pieces=2, width=1.9, smooth=False, avoid=p.grow(rm, 1.5), seed=142)
        # three stems
        stems = [[(1082, 1238), (1074, 1120), (1058, 1000), (1046, 948)],
                 [(1096, 1238), (1100, 1100), (1106, 960), (1112, 872)],
                 [(1110, 1238), (1128, 1130), (1152, 1040), (1174, 990)]]
        p.inks(stems, 2.0, 'forest', 0.95, grain=0.3, taper=(3, 10), seed=143)
        S = [np.asarray(s, np.float32) for s in stems]

        def at(si, t):
            s = S[si]; i = t * (len(s) - 1); k = min(int(i), len(s) - 2); f = i - k
            return s[k] * (1 - f) + s[k + 1] * f
        leaves = [  # (stem, t, angle, length, width, fill, line, veins, vein)
            (0, 0.35, -150, 86, 34, 'olive', 'ink', 5, 'line'),
            (0, 0.75, -40, 74, 30, 'sage', 'forest', 4, 'line'),
            (0, 0.98, -120, 64, 28, None, 'ink', 9, 'line'),
            (1, 0.45, -32, 90, 36, 'cobalt', None, 7, 'white'),
            (1, 0.78, -140, 70, 30, 'teal', 'forest', 4, 'line'),
            (2, 0.4, -20, 78, 32, 'leaf', 'forest', 4, 'line'),
            (2, 0.97, -60, 66, 28, 'olive', 'ink', 5, 'line'),
        ]
        for i, (si, t, ang, ln, wd, fill, line, nv, vein) in enumerate(leaves):
            b = at(si, t)
            tip = b + ln * np.array([np.cos(np.deg2rad(ang)), np.sin(np.deg2rad(ang))])
            p.leaf(b, tip, wd, fill=fill, line=line, veins=nv, vein=vein, bend=0.07 * (1 if i % 2 else -1),
                   fill_shift=(0, 0) if vein == 'white' else (3, -2), seed=150 + i)
        p.flower(1112, 858, 15, 'red', 'tulip', seed=160)

    # ------------------------------------------------------------------ 7. the mug and its steam
    def mug(self):
        p = self.p
        body = [(328, 1270), (378, 1270), (376, 1318), (370, 1326), (334, 1326), (328, 1318)]
        bm = p.poly(body)
        band = bm * p.poly([(320, 1290), (390, 1290), (390, 1304), (320, 1304)])
        p.tint(band, 'turquoise', 0, 0.9, 0.35, overrun=1.0, seed=170)
        top = p.ellipse_pts(353, 1270, 25, 6)
        p.tint(p.ellipse(353, 1271, 21, 4), 'sepia', 0, 0.75, 0.3, seed=171)
        p.ink(top, 1.8, closed=False, seed=172)
        p.inks([[(328, 1271), (330, 1318), (336, 1326), (368, 1326), (374, 1318), (378, 1271)]], 1.9, seed=173)
        p.ink([(328, 1282), (312, 1280), (308, 1296), (314, 1310), (329, 1310)], 1.8, seed=174)
        p.steam(350, 1258, 380, 'graphite', sway=26, curl=0.85, width=1.5, alpha=0.7, strands=2, lean=0.06, seed=175)

    # ------------------------------------------------------------------ 8. the face
    def face(self):
        p = self.p
        el, er = rot([(775, 630), (826, 630)])
        p.eye_closed(el[0], el[1], 24, 6.0, lashes=3, side=-1, rot=TILT, width=1.9, seed=180)
        p.eye_closed(er[0], er[1], 24, 6.0, lashes=3, side=1, rot=TILT, width=1.9, seed=181)
        p.ink(rot([(802, 640), (799, 657), (804, 660)]), 1.6, taper=(2, 3), seed=182)
        bl, br = rot([(764, 655), (838, 655)])
        p.blush(bl[0], bl[1], 11.5, seed=183); p.blush(br[0], br[1], 11.5, seed=184)
        mc = rot([(801, 675)])[0]
        p.mouth(mc[0], mc[1], 12, 5, rot=TILT, seed=185)

    # ------------------------------------------------------------------ 9. last touches
    def last(self):
        p = self.p
        p.leaf((1238, 652), (1286, 606), 30, fill='gold', line='ink', veins=4, lw=1.6, seed=190)
        p.squiggle(486, 668, 22, 'graphite', 'spiral', alpha=0.55, seed=191)


PHASES = ('lines', 'hair', 'stripes', 'colour', 'cat', 'plant', 'mug', 'face', 'last')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'sketchbook_reading_hour.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:10s} {time.time() - T0:5.1f}s')) if os.environ.get('SB_TIMING') else (lambda n: None)
    p = Sketchbook(W, H, seed=5, keep_stages=bool(stages), stages_dir=stages)
    p.finish()
    p.paper()
    p.stage('paper')
    sc = Scene(p)
    tick('setup')
    for name in PHASES[:-1]:
        getattr(sc, name)()
        tick(name)
        p.stage(name)
    getattr(sc, PHASES[-1])()
    tick(PHASES[-1])
    p.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s', p.n_lines, 'lines')


if __name__ == '__main__':
    main()
