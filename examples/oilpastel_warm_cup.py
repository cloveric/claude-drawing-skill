"""Example (oil-pastel portrait): 捧着一杯热的 · Something Warm to Hold -- a winter-morning portrait in oil pastel.

A cold morning at an outdoor market. A young woman with her black hair pulled back into a loose bun holds a paper
cup up in both hands and looks down into it; the steam curls up past her face. Her cheeks, the tip of her nose and
her ear are red with the cold. A chunky saffron scarf, striped in navy, is wound twice round her neck up to the
chin, one end hanging in front; a navy wool coat; cool-blue fingerless gloves, the bare fingers of one hand wrapped
round the kraft sleeve of the cup, the thumb of the other on top; a black plastic lid. She floats on white paper as
a vignette: the coat runs out in dry streaks below, there is no background.

Drawn in the order an illustrator works with oil pastels: white paper -> the navy coat and sleeves laid in with
long parallel dry strokes -> the saffron scarf -> the black hair -> the skin (peach on the shadow side, the neck,
the ear, the fingers) -> the cup and the gloves -> the stripes and ribs as short bold dashes -> the black crayon
accents -> the face (eyes, brows, nose, blush, lips) -> steam and the last flyaway strokes. --stages writes those
steps as snapshots for the draw-on. No image model.
python3 oilpastel_warm_cup.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from oilpastel import OilPastel

W, H = 1600, 1600
HC = np.array([800.0, 512.0])            # centre of her face (between the eyes)
S = 1.25                                 # face-local units -> canvas px
TILT = np.deg2rad(-5.0)                  # head leaning a little toward the cup
CS, SN = np.cos(TILT), np.sin(TILT)
CUP = dict(cx=660.0, top=1088.0, bot=1392.0, wt=112.0, wb=88.0)     # half-widths at the rim and the base
KRAFT = (1180.0, 1320.0)
FINGERS = ((1198, 690), (1233, 676), (1268, 682), (1302, 698))      # (y, x of the tip) of the near hand's fingers


def F(u, v):
    """face-local (u right, v down, before the tilt) -> canvas"""
    u, v = u * S, v * S
    return (HC[0] + u * CS - v * SN, HC[1] + u * SN + v * CS)


def FL(pts):
    return [F(u, v) for u, v in pts]


def cup_x(y, side):
    """the cup's silhouette: x of its left (side=-1) or right (+1) edge at height y"""
    c = CUP
    t = np.clip((y - c['top']) / (c['bot'] - c['top']), 0, 1)
    return c['cx'] + side * (c['wt'] + (c['wb'] - c['wt']) * t)


class Scene:
    def __init__(self, p):
        self.p = p
        self.plan()

    def __setattr__(self, k, v):
        # the canvas-sized masks are kept as uint8 (0..255): plenty for coverage, a quarter of the memory
        if isinstance(v, np.ndarray) and v.dtype != np.uint8 and v.ndim == 2 and v.shape == (H, W):
            v = np.round(np.clip(v, 0, 1) * 255).astype(np.uint8)
        object.__setattr__(self, k, v)

    def m(self, name):
        return getattr(self, name).astype(np.float32) * np.float32(1 / 255)

    # ------------------------------------------------------------------ shapes
    def plan(self):
        p = self.p
        # head: face, ear, neck, hair, bun
        self.face = p.poly(FL([(-104, -100), (-110, -48), (-100, -10), (-107, 36), (-101, 86), (-84, 140), (-52, 186),
                               (-12, 208), (36, 198), (86, 166), (126, 116), (148, 58), (152, 0), (146, -62),
                               (124, -122), (60, -164), (-30, -170), (-88, -146)]), smooth=True)
        self.ear = p.poly(FL([(150, -10), (172, -26), (194, -10), (198, 30), (188, 64), (166, 74), (154, 54)]),
                          smooth=True)
        self.neck = p.poly(FL([(60, 150), (150, 56), (200, 70), (212, 236), (40, 246)]))
        hair = p.poly(FL([(-104, -92), (-114, -140), (-94, -200), (-40, -242), (40, -262), (140, -242), (210, -186),
                          (244, -110), (252, -30), (246, 50), (230, 118), (204, 146), (198, 80), (200, 20),
                          (190, -36), (150, -72), (120, -124), (60, -150), (-30, -156), (-88, -136)]), smooth=True)
        self.bun_c = F(192, -242)
        self.bun = p.blob(self.bun_c[0], self.bun_c[1], 62 * S, 54 * S, 0.12, seed=4)
        self.hair = np.clip(hair + self.m('bun'), 0, 1)
        # scarf: two rolls round the neck, one end hanging in front
        self.r1 = p.poly([(560, 800), (620, 760), (700, 772), (790, 780), (870, 762), (940, 728), (1010, 708),
                          (1084, 716), (1132, 776), (1112, 874), (1010, 908), (880, 922), (760, 918), (640, 900),
                          (575, 866)], smooth=True)
        self.r2 = p.poly([(530, 898), (620, 890), (760, 916), (900, 918), (1030, 898), (1150, 906), (1180, 962),
                          (1120, 1016), (940, 1032), (770, 1026), (630, 1008), (540, 964)], smooth=True)
        self.end_path = [(1010, 924), (1030, 1040), (1044, 1160), (1052, 1270)]
        self.end = p.tube(self.end_path, [140, 138, 134, 130])
        # coat and sleeves
        self.coat = p.poly([(290, 1466), (254, 1440), (258, 1340), (272, 1190), (304, 1090), (372, 1022), (500, 978),
                            (640, 960), (900, 960), (1090, 972), (1228, 1012), (1314, 1080), (1346, 1200),
                            (1356, 1360), (1360, 1440), (1330, 1466), (800, 1470)], smooth=True)
        self.sl_far_path = [(350, 1450), (410, 1416), (476, 1376), (540, 1346)]
        self.sl_far = p.tube(self.sl_far_path, [168, 160, 152, 144]) * self.m('coat')
        self.sl_near_path = [(1290, 1450), (1170, 1424), (1040, 1390), (904, 1360)]
        self.sl_near = p.tube(self.sl_near_path, [194, 188, 178, 166]) * self.m('coat')
        # cup, lid, kraft sleeve
        c = CUP
        ys = np.linspace(c['top'], c['bot'], 12)
        self.cup = p.poly([(cup_x(y, -1), y) for y in ys] + [(cup_x(y, 1), y) for y in ys[::-1]])
        self.lid = p.poly([(c['cx'] - c['wt'] - 10, c['top'] + 6), (c['cx'] - c['wt'] + 2, c['top'] - 26),
                           (c['cx'] + c['wt'] - 2, c['top'] - 26), (c['cx'] + c['wt'] + 10, c['top'] + 6),
                           (c['cx'] + c['wt'] + 8, c['top'] + 20), (c['cx'] - c['wt'] - 8, c['top'] + 20)])
        y0, y1 = KRAFT
        self.kraft = p.poly([(cup_x(y0, -1) - 3, y0), (cup_x(y0, 1) + 3, y0), (cup_x(y1, 1) + 3, y1),
                             (cup_x(y1, -1) - 3, y1)])
        # hands: the near glove on the right of the cup, four bare fingers across its front; the far glove on the
        # left, its thumb across the front above the fingers
        self.glove_n = p.poly([(782, 1178), (812, 1170), (850, 1182), (886, 1226), (912, 1290), (922, 1350),
                               (902, 1388), (852, 1392), (814, 1356), (788, 1306)], smooth=True)
        self.finger_paths, fing = [], []
        for y, tip in FINGERS:
            path = [(800, y + 3), (740, y), (tip, y + 3)]
            self.finger_paths.append(path)
            fing.append(p.tube(path, [33, 32, 29]) + p.ellipse(tip + 2, y + 3, 14.5, 14.5))
        self.fing_each = [np.round(np.clip(f, 0, 1) * 255).astype(np.uint8) for f in fing]
        self.fingers = np.clip(sum(fing), 0, 1)
        self.glove_f = p.poly([(524, 1176), (566, 1156), (598, 1166), (604, 1246), (594, 1316), (566, 1356),
                               (530, 1352), (512, 1290), (510, 1226)], smooth=True)
        self.thumb_path = [(568, 1168), (612, 1156), (654, 1150)]
        self.thumb = np.clip(p.tube(self.thumb_path, [36, 32, 28]) + p.ellipse(656, 1151, 14, 14), 0, 1)
        # visible parts, front to back
        order = ['fingers', 'glove_n', 'thumb', 'cup', 'lid', 'glove_f', 'sl_near', 'sl_far', 'end', 'r1', 'r2',
                 'face', 'ear', 'neck', 'hair', 'coat']
        front = np.zeros((H, W), np.float32)
        for name in order:
            if name == 'coat': self.front_coat = front.copy()
            if name == 'sl_near': self.front_sleeves = front.copy()
            mm = self.m(name)
            setattr(self, name + '_v', np.clip(mm - front, 0, 1))
            front = np.clip(front + mm, 0, 1)
        del front
        # only the visible parts are needed from here on (and a few whole shapes for fields and boxes)
        for k in ('face', 'ear', 'neck', 'end', 'sl_far', 'sl_near', 'cup', 'glove_n', 'glove_f', 'thumb', 'fingers'):
            delattr(self, k)

    # ------------------------------------------------------------------ 1. the coat
    def coat_(self):
        p = self.p
        cv = self.m('coat_v')
        # long parallel strokes, a little slanted, running out in streaks at the bottom
        fc = self.m('front_coat')
        body = cv * p.soften(p.below(None, 1390, invert=True), 30)
        p.fill(body, p.flow(-96, 5, 300, seed=11), {'navy': 6, 'navy_deep': 2, 'black': 1}, length=(160, 320),
               width=(40, 62), density=3.0, pressure=0.97, dry=0.24, streak=0.3, edge=0.45, avoid=fc, seed=12)
        low = cv * p.soften(p.below(None, 1330), 30)
        p.fill(low, p.flow(-94, 5, 300, seed=18), {'navy': 5, 'navy_deep': 3}, length=(140, 260),
               width=(38, 58), density=2.4, pressure=0.88, dry=0.42, streak=0.45, spill=(0, 70), edge=0.6, avoid=fc,
               seed=19)
        # her near side, away from the light, and the lower coat: deeper navy and black
        shade = cv * p.spot(1250, 1260, 200, 360, solid=0.1)
        p.fill(shade, -95, {'navy_deep': 3, 'black': 1}, length=(130, 260), width=(34, 52), density=1.3,
               pressure=0.9, dry=0.4, avoid=fc, seed=13)
        # shoulders: strokes following the slope; the light catching the far shoulder
        sh = cv * p.soften(p.below(None, 1110, invert=True), 30)
        p.fill(sh, p.contour(self.m('coat'), 40, 0, -95), {'navy': 3, 'navy_light': 2}, length=(110, 220),
               width=(32, 46), density=1.3, pressure=0.86, dry=0.35, seed=14)
        p.fill(cv * p.spot(380, 1110, 130, 150, solid=0.2), -100, {'cobalt': 2, 'navy_light': 2}, length=(100, 200),
               width=(24, 36), density=1.0, pressure=0.78, dry=0.45, seed=15)
        # sleeves: along the forearm, lighter along the top
        for name, path, seed in (('sl_far_v', self.sl_far_path, 16), ('sl_near_v', self.sl_near_path, 17)):
            mm = self.m(name)
            a = np.rad2deg(np.arctan2(path[-1][1] - path[0][1], path[-1][0] - path[0][0]))
            p.fill(mm, a, {'navy': 5, 'navy_deep': 2}, length=(130, 240), width=(34, 50), density=3.0,
                   pressure=0.96, dry=0.28, edge=0.4, spill=(0, 60), avoid=self.m('front_sleeves'), seed=seed)
            xs = [q[0] for q in path]; ys = [q[1] - 62 for q in path]
            o = np.argsort(xs)
            top = mm * p.soften(p.below(list(np.array(xs)[o]), list(np.array(ys)[o]), invert=True), 18)
            p.fill(top, a, {'navy_light': 2, 'cobalt': 1}, length=(90, 180), width=(20, 30), density=1.0,
                   pressure=0.78, dry=0.45, seed=seed + 20)

    # ------------------------------------------------------------------ 2. the scarf
    def scarf(self):
        p = self.p
        for name, seed in (('r2', 21), ('r1', 22)):
            mm = self.m(name + '_v')
            fld = p.flow(-86 if name == 'r1' else -90, 7, 200, seed=seed + 40)
            p.fill(mm, fld, {'saffron': 5, 'marigold': 2, 'saffron_deep': 1}, length=(60, 130), width=(30, 44),
                   density=3.0, pressure=0.93, dry=0.28, mix=('yellow', 0.1), edge=0.5, seed=seed)
            bb = p._bbox(self.m(name))
            # the top of each roll in the light, the underside in shadow
            top = mm * p.soften(p.below(None, bb[1] + 46, invert=True), 10)
            p.fill(top, fld, {'marigold': 2, 'yellow': 1}, length=(40, 80), width=(18, 26), density=1.2,
                   pressure=0.8, dry=0.4, seed=seed + 3)
            under = mm * p.soften(p.below(None, bb[3] - 40), 10)
            p.fill(under, fld, {'saffron_deep': 2, 'orange': 1}, length=(40, 80), width=(20, 30), density=1.5,
                   pressure=0.86, dry=0.35, seed=seed + 5)
        ev = self.m('end_v')
        p.fill(ev, -92, {'saffron': 5, 'marigold': 2, 'saffron_deep': 1}, length=(80, 160), width=(30, 42),
               density=3.0, pressure=0.93, dry=0.3, mix=('yellow', 0.1), edge=0.45, seed=23)
        p.fill(ev * p.soften(p.rect(1040, 900, 1140, 1300), 12), -92, {'saffron_deep': 2, 'orange': 1},
               length=(60, 130), width=(20, 30), density=1.2, pressure=0.84, dry=0.4, seed=24)
        # where the end comes out from under the rolls
        p.fill(ev * p.spot(1012, 935, 90, 40, solid=0.2), 0, {'saffron_deep': 1, 'orange': 1}, length=(40, 80),
               width=(14, 22), density=1.4, pressure=0.84, seed=25)

    # ------------------------------------------------------------------ 3. the hair
    def hair_(self):
        p = self.p
        hv = self.m('hair_v')
        bc = self.bun_c
        tx, ty = bc[0] - 70, bc[1] - 90                     # swept up and back: aim a little above the bun
        fld = lambda x, y: np.rad2deg(np.arctan2(ty - y, tx - x))
        # an open base, swept back from the hairline toward the bun
        p.fill(hv * (1 - self.m('bun')), fld, {'black': 5, 'charcoal': 1, 'navy_deep': 1}, length=(110, 220),
               width=(18, 28), density=1.8, pressure=0.92, dry=0.45, streak=0.5, edge=0.85, seed=31)
        # the strands: long strokes from the hairline back to the bun, over the edge of the mass
        line = p.poly(FL([(-108, -100), (-92, -146), (-30, -164), (60, -158), (122, -128), (152, -76), (160, -40),
                          (150, -60), (116, -116), (58, -146), (-30, -152), (-86, -134)]))
        hclip = p._edge_clip(np.clip(p.soften(self.m('hair'), 6) * 1.6, 0, 1), 0.8)
        p.hair(None, fld, ('black', 'black', 'charcoal'), 70, (160, 320), (9, 16), bend=0.035, pressure=0.92,
               roots=line, dry=0.45, taper=0.65, clip=hclip, seed=32)
        nape = p.poly(FL([(196, -40), (246, -40), (240, 110), (204, 130)]))
        p.hair(None, fld, ('black', 'charcoal'), 14, (100, 200), (9, 14), bend=0.03, pressure=0.88, roots=nape,
               taper=0.6, seed=33)
        # the bun: scribbled round and round
        bm = self.m('bun') * hv
        p.fill(bm, p.contour(self.m('bun'), 14, 0), {'black': 4, 'navy_deep': 1}, length=(70, 140), width=(16, 24),
               density=2.4, pressure=0.9, dry=0.4, edge=0.7, seed=34)
        r = np.random.default_rng(35)
        for i in range(5):
            t = np.linspace(0, 2 * np.pi * r.uniform(0.7, 1.1), 30) + r.uniform(0, 6.3)
            rr = (r.uniform(0.45, 0.95) * 62 * S)
            pts = [(bc[0] + rr * np.cos(a) * 1.1, bc[1] + rr * np.sin(a) * 0.92) for a in t]
            p.crayon(pts, r.uniform(7, 11), 'black', 0.9, wobble=2.0, seed=36 + i)
        # the light on the crown: a few navy strokes
        crown = hv * p.spot(*F(0, -200), 110 * S, 50 * S, solid=0.1)
        p.fill(crown, fld, 'navy_light', length=(90, 170), width=(6, 10), density=0.2, pressure=0.7, dry=0.5,
               seed=41)

    # ------------------------------------------------------------------ 4. skin
    def skin(self):
        p = self.p
        fv = self.m('face_v')
        # the face is the paper; peach only on the shadow side: the side plane from the temple to the jaw
        side = fv * p.soften(p.poly(FL([(104, -112), (148, -64), (152, 54), (128, 112), (92, 156), (100, 110),
                                        (120, 40), (118, -40)]), smooth=True), 10)
        p.fill(side, -68, {'peach': 2, 'peach_light': 3}, length=(50, 110), width=(12, 20), density=1.0,
               pressure=0.74, dry=0.45, seed=51)
        # under the chin and along the jaw, the far contour, the temple
        jaw = fv * p.soften(p.poly(FL([(-70, 150), (-30, 190), (40, 180), (100, 146), (112, 166), (40, 210),
                                       (-16, 216), (-64, 192)]), smooth=True), 6)
        p.fill(jaw, -12, {'peach': 2, 'peach_deep': 1}, length=(50, 100), width=(14, 22), density=1.7, pressure=0.84,
               dry=0.35, seed=52)
        p.crayon(FL([(-102, -70), (-106, -30), (-100, -6), (-106, 36), (-100, 84), (-86, 132), (-56, 178)]), 9,
                 'peach', 0.8, wobble=1.4, gap=0.15, seed=53)
        p.crayon(FL([(-56, 182), (-14, 204), (30, 196), (80, 170), (118, 126), (142, 70)]), 8, 'peach_deep', 0.82,
                 gap=0.15, seed=54)
        # the eye sockets, the nose's shadow side and its underside
        p.fill(fv * p.spot(*F(52, -20), 56 * S, 24 * S, solid=0.2), -15, 'peach_light', length=(30, 70),
               width=(12, 18), density=1.4, pressure=0.68, dry=0.4, seed=55)
        p.fill(fv * p.spot(*F(-72, -16), 30 * S, 18 * S, solid=0.2), -15, 'peach_light', length=(20, 50),
               width=(10, 16), density=1.2, pressure=0.64, dry=0.4, seed=56)
        p.lines([FL([(-14, -8), (-12, 30), (-20, 62)])], 'peach', 15, 0.78, dry=0.4, seed=57)
        p.lines([FL([(-46, 88), (-26, 94), (-4, 86)])], 'peach', 11, 0.74, dry=0.3, seed=58)
        # the neck under the jaw, in shadow
        nv = self.m('neck_v')
        p.fill(nv, -100, {'peach_light': 2, 'peach': 2}, length=(60, 120), width=(16, 24), density=1.8,
               pressure=0.8, dry=0.4, edge=0.5, seed=59)
        p.fill(nv * p.soften(p.poly(FL([(60, 150), (150, 56), (170, 80), (90, 190)])), 8), -20, 'peach_deep',
               length=(40, 80), width=(12, 18), density=1.4, pressure=0.8, dry=0.4, seed=60)
        # the ear: red with cold
        ev = self.m('ear_v')
        p.fill(ev, -80, {'blush': 2, 'peach': 1}, length=(40, 80), width=(14, 20), density=2.6, pressure=0.88,
               edge=0.4, seed=50)
        # bare fingers and thumb: paper, peach along the underside and at the knuckle end
        for i, (path, fm) in enumerate(zip(self.finger_paths, self.fing_each)):
            fm = fm.astype(np.float32) * np.float32(1 / 255)
            p.fill(fm, 180, {'peach_light': 2, 'skin_pale': 1}, length=(50, 90), width=(14, 20), density=2.6,
                   pressure=0.84, dry=0.3, clip=p._edge_clip(fm, 0.2), seed=61 + i)
            q = [(x, y + 9) for x, y in path]
            p.lines([q], {'peach': 2, 'peach_deep': 1}, 12, 0.88, dry=0.3, clip=fm, seed=65 + i)
            tip = path[-1]
            p.lines([[(tip[0] + 18, tip[1] - 4), (tip[0] - 4, tip[1] + 2), (tip[0] + 10, tip[1] + 12)]], 'peach_deep',
                    9, 0.8, dry=0.3, clip=fm, seed=69 + i)
        tv = self.m('thumb_v')
        p.fill(tv, -14, {'peach_light': 2, 'skin_pale': 1}, length=(50, 90), width=(14, 20), density=2.6,
               pressure=0.84, dry=0.3, clip=p._edge_clip(tv, 0.2), seed=73)
        p.lines([[(x, y + 9) for x, y in self.thumb_path]], 'peach', 12, 0.86, dry=0.3, clip=tv, seed=74)

    # ------------------------------------------------------------------ 5. cup and gloves
    def cup_(self):
        p = self.p
        c = CUP
        cv = self.m('cup_v')
        kr = self.m('kraft') * cv
        p.fill(kr, -2, {'kraft': 3, 'kraft_dark': 1}, length=(70, 140), width=(20, 30), density=3.0, pressure=0.92,
               dry=0.28, edge=0.3, seed=71)
        # the paper cup: white, a cool shadow down its right side, a warm-grey contour
        body = cv * (1 - self.m('kraft')) * (1 - self.m('lid'))
        shadow = body * p.soften(p.rect(c['cx'] + 40, c['top'], c['cx'] + 130, c['bot']), 16)
        p.fill(shadow, -92, {'mist': 2, 'cool_light': 1}, length=(50, 110), width=(16, 24), density=1.6,
               pressure=0.74, dry=0.35, seed=72)
        p.crayon([(cup_x(y, 1) - 2, y) for y in np.linspace(c['top'] + 22, c['bot'], 8)], 6, 'warmgrey', 0.82,
                 clip=cv, seed=73)
        p.crayon([(cup_x(y, -1) + 2, y) for y in np.linspace(c['top'] + 22, KRAFT[0] - 20, 4)], 5, 'warmgrey', 0.7,
                 clip=cv, seed=74)
        p.crayon([(cup_x(c['bot'] - 4, -1) + 8, c['bot'] - 6), (c['cx'], c['bot'] + 2),
                  (cup_x(c['bot'] - 4, 1) - 6, c['bot'] - 6)], 6, 'warmgrey', 0.8, clip=cv, seed=75)
        # the lid
        lv = self.m('lid_v')
        p.fill(lv, 0, {'black': 3, 'charcoal': 1}, length=(60, 120), width=(16, 22), density=3.0, pressure=0.94,
               dry=0.2, edge=0.3, seed=76)
        p.lines([[(c['cx'] - c['wt'] + 16, c['top'] - 18), (c['cx'] + c['wt'] - 16, c['top'] - 18)]], 'grey', 5,
                0.62, dry=0.3, seed=77)
        # gloves: cool blue knit, darker on their shadow side
        for name, seed, dark in (('glove_f_v', 78, (520, 1300)), ('glove_n_v', 79, (900, 1320))):
            gm = self.m(name)
            p.fill(gm, -70, {'cool': 2, 'cool_deep': 2}, length=(50, 100), width=(18, 26),
                   density=3.2, pressure=0.97, dry=0.2, streak=0.3, edge=0.35, seed=seed)
            p.fill(gm * p.spot(dark[0], dark[1], 70, 80, solid=0.2), -78, {'cool_deep': 2, 'navy': 1},
                   length=(40, 80), width=(14, 22), density=1.4, pressure=0.86, dry=0.35, seed=seed + 10)

    # ------------------------------------------------------------------ 6. stripes and ribs
    def stripes(self):
        p = self.p
        # navy stripes across each roll of the scarf
        p.dashes([(586, 846), (680, 836), (790, 848), (900, 842), (1010, 818), (1100, 818)], 'navy', 74,
                 (70, 112), (20, 30), 90, jitter=11, clip=self.m('r1_v'), seed=81)
        p.dashes([(556, 952), (670, 954), (800, 970), (940, 970), (1080, 956), (1150, 950)], 'navy', 78,
                 (60, 98), (20, 30), 90, jitter=11, clip=self.m('r2_v'), seed=82)
        # on the hanging end the stripes are bands across it
        for y in (1010, 1100, 1190):
            x = np.interp(y, [924, 1040, 1160, 1270], [1010, 1030, 1044, 1052])
            p.dashes([(x - 64, y), (x + 64, y + 2)], 'navy', 40, (48, 64), (22, 28), 0, jitter=4,
                     clip=self.m('end_v'), seed=83 + int(y))
        # the fringe: short dashes hanging under the end
        p.dashes([(992, 1286), (1112, 1290)], {'saffron': 2, 'saffron_deep': 1}, 13, (34, 50), (8, 11), 90,
                 jitter=9, along=0.45, seed=89)
        # ribbed cuffs on the gloves, the rolled edge where the fingers come out
        p.dashes([(808, 1370), (870, 1386), (930, 1356)], 'cool_deep', 14, (26, 34), (7, 9), 90, along=-0.2,
                 clip=self.m('glove_n_v'), seed=90)
        p.dashes([(520, 1310), (556, 1346), (596, 1326)], 'cool_deep', 14, (26, 34), (7, 9), 90, along=-0.2,
                 clip=self.m('glove_f_v'), seed=91)
        p.crayon([(792, 1180), (788, 1240), (792, 1300), (804, 1344)], 11, 'cool_light', 0.88,
                 clip=self.m('glove_n_v'), seed=92)
        # knit rows over the backs of the gloves: short light dashes
        rows = (((800, 1214), (880, 1236)), ((806, 1254), (896, 1282)), ((814, 1296), (906, 1326)),
                ((526, 1206), (594, 1196)), ((524, 1246), (598, 1238)), ((528, 1286), (594, 1280)))
        for i, (a, b) in enumerate(rows):
            p.dashes([a, b], 'cool_light', 15, (14, 20), (6, 8), 70, jitter=10, pressure=0.8,
                     clip=self.m('glove_n_v' if i < 3 else 'glove_f_v'), seed=93 + i)

    # ------------------------------------------------------------------ 7. black accents
    def accents(self):
        p = self.p
        # coat: the arms against the body, the folds of the sleeves, the shadow under the scarf
        p.crayon([(372, 1060), (340, 1180), (328, 1310), (334, 1400)], 9, seed=101)
        p.crayon([(1236, 1050), (1262, 1170), (1266, 1300)], 9, seed=102)
        p.crayon([(330, 1470), (420, 1420), (500, 1394)], 8, seed=103)
        p.crayon([(1236, 1376), (1120, 1344), (1010, 1316)], 8, pressure=0.86, seed=104)
        p.crayon([(1100, 1400), (1130, 1372)], 7, seed=105)
        p.crayon([(600, 1030), (740, 1044), (880, 1040)], 8, pressure=0.84, seed=106)
        # sleeve ends against the gloves
        p.crayon([(526, 1318), (548, 1364), (594, 1352)], 7, pressure=0.86, seed=107)
        p.crayon([(906, 1350), (878, 1392), (820, 1386)], 7, pressure=0.86, seed=108)
        # the gloves' outer contours
        p.crayon([(876, 1206), (906, 1262), (920, 1330)], 6, pressure=0.84, gap=0.2, seed=120)
        p.crayon([(530, 1172), (512, 1226), (514, 1300)], 6, pressure=0.84, gap=0.2, seed=121)
        # where one roll of the scarf tucks under the other
        p.crayon([(590, 892), (700, 906), (840, 918), (980, 908), (1080, 888)], 7, 'saffron_deep', 0.92, seed=109)
        # fingers: under each finger, and the gap above the first
        for i, path in enumerate(self.finger_paths):
            q = [(x, y + 15) for x, y in path[:2]] + [(path[2][0] + 6, path[2][1] + 13)]
            p.crayon(q, 5, 'black', 0.88, wobble=0.6, gap=0.2, seed=110 + i)
        p.crayon([(x, y - 15) for x, y in self.finger_paths[0][:2]] + [(FINGERS[0][1] + 10, FINGERS[0][0] - 10)], 4.5,
                 'black', 0.82, gap=0.3, seed=115)
        p.crayon([(x, y + 15) for x, y in self.thumb_path], 4.5, 'black', 0.82, seed=116)
        # the lid's rim
        c = CUP
        p.crayon([(c['cx'] - c['wt'] - 8, c['top'] + 18), (c['cx'], c['top'] + 22),
                  (c['cx'] + c['wt'] + 8, c['top'] + 18)], 6, seed=117)
        # the ear's curl, the line of the jaw into the neck
        p.crayon(FL([(178, -12), (190, 14), (184, 46), (170, 60)]), 6, 'black', 0.86, seed=118)
        p.crayon(FL([(96, 160), (126, 118), (146, 64)]), 5, 'peach_deep', 0.8, seed=119)

    # ------------------------------------------------------------------ 8. the face
    def features(self):
        p = self.p
        # blush: the near cheek big, the far cheek smaller; the cold red tip of the nose
        p.blush(*F(58, 66), 48 * S, 34 * S, 'blush', -60, 0.92, seed=121)
        p.blush(*F(-88, 56), 20 * S, 30 * S, 'blush', -70, 0.85, clip=self.m('face_v'), seed=122)
        p.blush(*F(-36, 72), 14 * S, 10 * S, 'vermilion', -40, 0.6, seed=123)
        # eyes looking down into the cup, the far one narrower and a little higher
        p.eye(*F(44, 2), 72 * S, 33 * S, look=(-0.45, 0.7), lid=0.6, side=1, rot=-6, seed=124)
        p.eye(*F(-70, -2), 48 * S, 28 * S, look=(-0.55, 0.7), lid=0.6, side=-1, rot=-10, lash=0.3, seed=125)
        p.brow(FL([(6, -44), (44, -56), (86, -49)]), 19, seed=126)
        p.brow(FL([(-98, -41), (-76, -52), (-46, -50)]), 17, seed=127)
        # nose: the far contour, a nostril
        p.crayon(FL([(-30, 20), (-42, 50), (-52, 72), (-44, 84)]), 6, 'black', 0.9, seed=128)
        p.crayon(FL([(-26, 88), (-12, 86)]), 7, 'black', 0.92, seed=129)
        # lips: small, closed, a hint of a smile
        p.lips(*F(-26, 128), 70 * S, 28 * S, smile=0.25, rot=-6, side=-1, seed=130)

    # ------------------------------------------------------------------ 9. steam and last touches
    def last(self):
        p = self.p
        c = CUP
        for i, (x, h, sw, col) in enumerate(((618, 380, 26, 'cool_light'), (652, 470, 34, 'mist'),
                                              (592, 300, 20, 'cool_light'))):
            p.wisp(x, c['top'] - 40, h, sw, col, 15, 0.9, seed=131 + i)
        # loose hair: strands escaping at the far temple and over the ear, flyaways off the bun
        p.stroke(FL([(-40, -160), (-80, -130), (-104, -80), (-110, -20), (-100, 30)]), 11, 'black', pressure=0.92,
                 dry=0.5, taper=0.75, seed=135)
        p.stroke(FL([(-20, -160), (-66, -128), (-88, -80), (-92, -36)]), 7, 'black', pressure=0.86, dry=0.5,
                 taper=0.8, seed=136)
        p.stroke(FL([(132, -96), (152, -56), (160, -18)]), 7, 'black', pressure=0.88, dry=0.5, taper=0.75, seed=137)
        bc = self.bun_c
        p.hair(p.spot(bc[0], bc[1], 76, 66, solid=0.3), p.radial(bc[0], bc[1], 35), ('black', 'black', 'charcoal'),
               9, (90, 170), (4, 7), bend=0.12, pressure=0.86, seed=138)


PHASES = ('coat_', 'scarf', 'hair_', 'skin', 'cup_', 'stripes', 'accents', 'features', 'last')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'oilpastel_warm_cup.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:12s} {time.time() - T0:5.1f}s')) if os.environ.get('OP_TIMING') else (lambda n: None)
    p = OilPastel(W, H, seed=8, keep_stages=bool(stages), stages_dir=stages)
    p.finish()
    p.paper()
    p.stage('paper')
    sc = Scene(p)
    tick('setup')
    for name in PHASES[:-1]:
        getattr(sc, name)()
        tick(name)
        p.stage(name.strip('_'))
    getattr(sc, PHASES[-1])()
    tick(PHASES[-1])
    p.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s', p.n_strokes, 'strokes')


if __name__ == '__main__':
    main()
