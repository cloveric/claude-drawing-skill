"""Example (sketchbook doodle): 放风筝 · Kite Day -- a wide sketchbook page (16:9, for explainer videos).

A small boy in a striped top and mustard shorts stands near the left of a big empty page, one arm up with the spool,
head tipped back, smiling up at his kite. The kite -- a diamond quartered in red, yellow, teal and blue, with a long
wavy tail of little bows -- flies high on the right, and the string, one hair-fine line, crosses the whole page to it.
Behind him two thin trees drawn in red and green lines (pink blossom dots on the green one), a little yellow tree far
off on the right, a few tufts of grass, two leaves blown along on the wind. No ground, no sky: the paper is the sky.

Drawn in the order a sketchbook illustrator works: the paper -> the ink line drawing of the boy -> his hair -> the
stripes -> the other colour (shorts, socks, shoes, the spool) -> his face -> the trees and the grass -> the kite and
its string -> the tail, the leaves on the wind. --stages writes those steps as snapshots for the draw-on. No image
model.
python3 sketchbook_kite_day.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from sketchbook import Sketchbook

W, H = 1920, 1080
HEAD = np.array([566.0, 598.0])          # centre of his face
TILT = -12.0                             # head tipped back, looking up at the kite


def rot(pts, deg=TILT, c=HEAD):
    a = np.deg2rad(deg); cs, sn = np.cos(a), np.sin(a)
    P = np.asarray(pts, np.float32) - c
    return np.stack([P[:, 0] * cs - P[:, 1] * sn, P[:, 0] * sn + P[:, 1] * cs], 1) + c


class Scene:
    def __init__(self, p):
        self.p = p
        self.M = {}
        self.plan()

    def put(self, k, m):
        self.M[k] = np.round(np.clip(m, 0, 1) * 255).astype(np.uint8)

    def m(self, *ks):
        out = None
        for k in ks:
            a = self.M[k].astype(np.float32) * np.float32(1 / 255)
            out = a if out is None else np.maximum(out, a)
        return out

    def grow(self, *ks, px=2.5):
        return self.p.grow(self.m(*ks), px)

    # ------------------------------------------------------------------ shapes
    def plan(self):
        p = self.p
        # head (three-quarter view to the right, tipped back), ear, neck
        self.face_pts = rot([(560, 548), (596, 556), (612, 590), (609, 626), (590, 648), (562, 652), (536, 640),
                             (522, 612), (524, 578), (536, 556)])
        self.put('face', p.poly(self.face_pts, smooth=True))
        self.ear = rot([(526, 600), (514, 594), (510, 610), (516, 624), (528, 624)])
        self.put('ear', p.poly(self.ear, smooth=True))
        self.put('neck', p.poly([(548, 640), (572, 644), (572, 668), (546, 668)]))
        # short tousled hair: a mop from the crown -- a fringe combed forward to the brow, the rest down the back
        c = (548, 538)
        self.mop = [rot(g) for g in (
            [c, (526, 556), (512, 584), (507, 610)],          # the nape
            [c, (524, 542), (507, 566), (503, 592)],          # the back
            [c, (532, 528), (515, 540), (505, 562)],
            [c, (552, 524), (572, 526), (590, 536)],          # over the top (a cowlick where they part)
            [c, (572, 532), (597, 546), (613, 572)],
            [c, (566, 546), (586, 558), (599, 578)])]         # the fringe, combed forward to the brow
        hm = self.p.poly(rot([(616, 578), (608, 552), (590, 534), (560, 524), (530, 530), (510, 548), (502, 580),
                              (504, 610), (518, 616), (522, 594), (532, 576), (556, 568), (590, 574)]), smooth=True)
        self.put('hair', hm)
        self.put('face_vis', self.m('face') * (1 - hm))
        # striped top, the near arm raised with the spool, the far arm down
        self.body_pts = [(522, 668), (556, 660), (590, 664), (606, 684), (610, 740), (612, 792), (562, 798),
                         (512, 792), (512, 740), (514, 692)]
        self.put('body', p.poly(self.body_pts, smooth=True))
        self.arm_up = [(596, 680), (624, 652), (642, 618), (652, 596)]
        self.arm_down = [(522, 682), (510, 724), (508, 760), (514, 780)]
        self.sl_up = p.tube_pts(self.arm_up, [34, 31, 28, 26])
        self.sl_down = p.tube_pts(self.arm_down, [34, 31, 28, 26])
        self.put('sl_up', p.poly(self.sl_up)); self.put('sl_down', p.poly(self.sl_down))
        self.hand_up = [(644, 594), (650, 578), (662, 574), (670, 584), (666, 600), (652, 604)]
        self.hand_down = [(506, 778), (522, 778), (524, 794), (514, 802), (504, 794)]
        self.put('hands', np.maximum(p.poly(self.hand_up, smooth=True), p.poly(self.hand_down, smooth=True)))
        self.spool = [(654, 566), (676, 562), (680, 582), (658, 586)]
        self.put('spool', p.poly(self.spool))
        # shorts, legs (the near one stepping forward), socks, shoes
        self.shorts = [(512, 786), (612, 786), (620, 842), (574, 846), (564, 820), (552, 846), (506, 842)]
        self.put('shorts', p.poly(self.shorts))
        self.leg_far = [(530, 840), (529, 880), (527, 920)]
        self.leg_near = [(594, 840), (600, 880), (608, 916)]
        self.put('legs', np.maximum(p.tube(self.leg_far, [20, 17, 15]), p.tube(self.leg_near, [20, 17, 15])))
        self.shoe_far = [(516, 914), (536, 914), (548, 922), (546, 932), (514, 932)]
        self.shoe_near = [(598, 910), (618, 908), (634, 916), (632, 928), (598, 928)]
        self.put('shoes', np.maximum(p.poly(self.shoe_far, smooth=True), p.poly(self.shoe_near, smooth=True)))
        # the kite
        self.kite_pts = [(1492, 108), (1586, 214), (1472, 346), (1394, 222)]
        self.kite_c = (1484, 226)

    # ------------------------------------------------------------------ 1. the boy in ink
    def lines(self):
        p = self.p
        fp = p.closed_pts(self.face_pts)
        n = len(fp)
        av = self.grow('hair', 'ear', px=1.2)
        p.ink(fp[int(0.05 * n):int(0.75 * n)], 1.9, 'ink_soft', avoid=av, seed=11)
        p.contour(self.ear, pieces=1, width=1.7, avoid=self.grow('hair', px=1.0), seed=12)
        p.ink(rot([(519, 606), (523, 614)]), 1.4, seed=13)
        p.inks([[(550, 646), (549, 662)], [(570, 648), (571, 662)]], 1.8, avoid=self.grow('face'), seed=14)
        fr = self.grow('sl_up', 'sl_down', 'hands', 'shorts')
        p.contour(self.body_pts, pieces=(2, 3), width=2.0, avoid=self.grow('sl_up', 'sl_down', 'hands'), seed=15)
        p.inks([[(538, 663), (556, 670), (576, 666)]], 1.6, seed=16)
        for k, (pts, s_) in enumerate(((self.sl_up, 20), (self.sl_down, 22))):
            p.ink(pts, 2.0, smooth=False, avoid=self.grow('hands', 'spool', px=1.5), gaps=0.5, seed=s_)
        p.contour(self.hand_up, pieces=1, width=1.8, avoid=self.grow('spool', px=1.2), seed=24)
        p.contour(self.hand_down, pieces=1, width=1.8, seed=25)
        p.contour(self.spool, pieces=2, width=1.8, smooth=False, seed=26)
        p.contour(self.shorts, pieces=(2, 3), width=1.9, smooth=False, avoid=self.grow('body', 'sl_down', 'hands'),
                  seed=27)
        fl = self.grow('shorts', 'shoes', px=1.5)
        for k, (leg, w) in enumerate(((self.leg_far, [20, 17, 15]), (self.leg_near, [20, 17, 15]))):
            o = p.tube_pts(leg, w)
            m = len(o) // 2
            p.inks([o[:m], o[m:]], 1.8, avoid=fl, seed=30 + k)
        for k, sh in enumerate((self.shoe_far, self.shoe_near)):
            p.contour(sh, pieces=(1, 2), width=1.9, seed=34 + k)

    # ------------------------------------------------------------------ 2. hair
    def hair(self):
        p = self.p
        av = self.grow('face_vis', px=1.0)
        p.hair(self.mop, n=74, width=2.0, wave=(2.0, 44), wave_root=0.2, length=(0.74, 1.0), start=(0.0, 0.1),
               taper=(3, 16), stray=0.06, cohere=1.5, avoid=av, seed=40)

    # ------------------------------------------------------------------ 3. stripes
    def stripes(self):
        p = self.p
        cols = ['red', 'navy', 'yellow', 'navy', 'turquoise', 'navy']
        fr = self.m('sl_up', 'sl_down', 'hands')
        p.stripes(self.m('body'), cols, across=88, bend=4, widths=[11, 6, 11, 6, 11, 6], gap=(5, 8), start=8,
                  avoid=fr, seed=50)
        p.stripes(self.m('sl_up'), cols, path=self.arm_up, widths=[10, 5, 10, 5, 10, 5], gap=(5, 7), start=4,
                  avoid=self.m('hands', 'spool'), seed=51)
        p.stripes(self.m('sl_down'), cols, path=self.arm_down, widths=[10, 5, 10, 5, 10, 5], gap=(5, 7), start=4,
                  avoid=self.m('hands'), seed=52)

    # ------------------------------------------------------------------ 4. other colour
    def colour(self):
        p = self.p
        p.tint(self.m('shorts'), 'mustard', 75, 0.85, 0.55, 0.5, 0.9, hatch=0.25, spacing=6,
               avoid=self.m('body', 'sl_down', 'hands'), shift=(2, 1), seed=60)
        p.tint(self.m('shoes'), 'blue', 10, 0.9, 0.25, overrun=1.5, shift=(1, -1), seed=61)
        p.tint(self.m('spool'), 'wood', 80, 0.8, 0.5, seed=62)
        for k, leg in enumerate((self.leg_far, self.leg_near)):
            x, y = leg[-1]
            sock = p.poly([(x - 9, y - 26), (x + 9, y - 26), (x + 9, y - 2), (x - 9, y - 2)]) * self.m('legs')
            p.stripes(sock, ['red'], across=90, band=(4, 5), gap=(4, 5), overrun=1.0, seed=63 + k)

    # ------------------------------------------------------------------ 5. the face
    def face(self):
        p = self.p
        e1, e2 = rot([(576, 590), (601, 587)])
        p.eye_dot(e1[0], e1[1], 3.5); p.eye_dot(e2[0], e2[1], 3.2)
        p.inks([rot([(568, 578), (576, 574), (584, 577)]), rot([(595, 574), (602, 571), (608, 574)])], 1.4,
               taper=(2, 3), seed=70)
        p.ink(rot([(613, 597), (619, 606), (611, 610)]), 1.6, taper=(2, 3), seed=71)
        b1, b2 = rot([(566, 610), (606, 607)])
        p.blush(b1[0], b1[1], 8.0, seed=72); p.blush(b2[0], b2[1], 6.5, seed=73)
        # an open smile: a little red under a curved line
        sm = rot([(584, 622), (593, 630), (603, 621)])
        p.tint(p.poly(np.vstack([sm, rot([(594, 623)])])), 'lip', 0, 0.85, 0.2, overrun=0.6, edge=0.2, seed=74)
        p.ink(rot([(582, 621), (593, 623), (605, 619)]), 1.5, taper=(2, 2), seed=75)
        p.ink(sm, 1.5, taper=(2, 3), seed=76)

    # ------------------------------------------------------------------ 6. trees and grass
    def trees(self):
        p = self.p
        p.tree(250, 965, 560, 'red', lines=5, branches=8, lean=0.02, width=1.8, seed=80)
        p.tree(372, 975, 420, 'forest', lines=4, branches=7, lean=-0.03, width=1.7, blossoms='pink', n_blossom=14,
               seed=81)
        p.tree(1738, 960, 300, 'gold', lines=3, branches=6, lean=0.02, width=1.7, seed=82)
        for k, (x, y, w) in enumerate(((250, 965, 60), (372, 975, 50), (566, 936, 90), (1738, 960, 50),
                                       (1640, 968, 30))):
            p.ticks(p.ellipse(x, y - 4, w, 8), int(w / 4), (8, 16), -90, 22, 1.4, 'leaf', 0.85, seed=90 + k)

    # ------------------------------------------------------------------ 7. kite and string
    def kite(self):
        p = self.p
        K = np.asarray(self.kite_pts, np.float32); c = np.asarray(self.kite_c, np.float32)
        cols = ['red', 'yellow', 'teal', 'blue']
        for i in range(4):
            tri = [K[i], K[(i + 1) % 4], c]
            p.tint(p.poly(tri), cols[i], 30 + 40 * i, 0.88, 0.5, 0.5, 0.9, overrun=2.0, shift=(2, 1),
                   seed=100 + i)
        p.contour(self.kite_pts, pieces=2, width=2.0, smooth=False, seed=104)
        p.inks([[K[0], K[2]], [K[1], K[3]]], 1.6, seed=105)
        p.ink([(660, 580), (900, 468), (1160, 380), (1412, 300), (1478, 262)], 1.1, 'ink_soft', alpha=0.85,
              wobble=0.6, wscale=120, taper=(4, 4), seed=106)

    # ------------------------------------------------------------------ 8. tail and wind
    def last(self):
        p = self.p
        t = np.linspace(0, 1, 9)
        tail = np.stack([1472 + 70 * t + 22 * np.sin(2 * np.pi * 1.4 * t), 346 + 250 * t], 1)
        p.ink(tail, 1.4, seed=110)
        cols = ['red', 'gold', 'teal', 'magenta', 'blue']
        for i, tt in enumerate((0.18, 0.36, 0.54, 0.72, 0.9)):
            j = tt * 8; k = int(j); f = j - k
            x, y = tail[k] * (1 - f) + tail[min(8, k + 1)] * f
            for sd in (-1, 1):
                bow = [(x, y), (x + sd * 13, y - 7), (x + sd * 13, y + 7)]
                p.tint(p.poly(bow), cols[i], 0, 0.9, 0.4, overrun=1.0, seed=111 + 2 * i + (sd > 0))
                p.contour(bow, pieces=1, width=1.3, smooth=False, seed=121 + 2 * i + (sd > 0))
        # two light wind doodles, each ending in a little curl
        for k, (x, y, L) in enumerate(((900, 640, 150), (1250, 690, 120))):
            t = np.linspace(0, 1, 30)
            xs = x + L * t; ys = y - 10 * np.sin(np.pi * t) - 6 * t
            th = np.linspace(-np.pi / 2, np.pi * 1.1, 14)
            cx, cy = xs[-1], ys[-1] + 9
            P = np.vstack([np.stack([xs, ys], 1), np.stack([cx + 9 * np.cos(th), cy + 9 * np.sin(th)], 1)])
            p.ink(P, 1.3, 'graphite', alpha=0.55, taper=(10, 8), smooth=False, seed=133 + k)
        p.leaf((1010, 700), (1056, 676), 20, fill='olive', line='ink', veins=3, lw=1.4, seed=130)
        p.leaf((1196, 600), (1228, 568), 16, fill='coral', line='ink', veins=2, lw=1.3, seed=131)


PHASES = ('lines', 'hair', 'stripes', 'colour', 'face', 'trees', 'kite', 'last')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'sketchbook_kite_day.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    p = Sketchbook(W, H, seed=12, keep_stages=bool(stages), stages_dir=stages)
    p.finish()
    p.paper()
    p.stage('paper')
    sc = Scene(p)
    for name in PHASES[:-1]:
        getattr(sc, name)()
        p.stage(name)
    getattr(sc, PHASES[-1])()
    p.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s', p.n_lines, 'lines')


if __name__ == '__main__':
    main()
