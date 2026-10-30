"""Example (pastel vignette): 橘猫围巾 · The Marmalade Scarf -- a whimsical picture-book vignette in soft chalk pastel
and a little gouache on white paper.

A cold morning. A young woman in a powder-blue coat over a cream sweater wears her big fluffy ginger cat like a
scarf: it lies round her neck, its head and front paws hanging over one shoulder, a hind paw and its striped tail
down the other side of her coat. She has tilted her head toward it and looks at it sideways, smiling; the cat looks
back up at her with round amber eyes. Long, dark blue-black wavy hair with a side-swept
fringe, big round eyes, very rosy cheeks, a red-tipped nose. Behind them only a sprig of eucalyptus on one side and
a faint pencil sketch of rooftops on the other; everything else is white paper, and the coat simply dissolves into
it in dry strokes.

Painted the way a pastel illustrator works: paper -> a light pencil sketch -> the sprig and the faint rooftops ->
flat colour blocked in -> soft modelling (blended faces, dry directional strokes in the coat) -> the cat's fur ->
the hair, lock by lock -> faces (eyes, cheeks, nose, mouth, whiskers) -> pale dry highlights and a few loose
hairs. --stages writes those steps as snapshots for the draw-on. No image model.
python3 pastelvignette_marmalade_scarf.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from core import blur, smoothstep, noise2d, fbm1d
from pastelvignette import PastelVignette

W, H = 1920, 1080
HC = np.array([1000.0, 392.0])          # centre of her face
TILT = np.deg2rad(-7.0)                  # head tilted toward the cat
CS, SN = np.cos(TILT), np.sin(TILT)
NOSE_C = (770.0, 640.0)                  # the cat's nose: its fur grows away from here


def F(u, v):
    """face-local (u right, v down, before the tilt) -> canvas"""
    return (HC[0] + u * CS - v * SN, HC[1] + u * SN + v * CS)


def FL(pts):
    return [F(u, v) for u, v in pts]


def to_local(x, y):
    dx, dy = x - HC[0], y - HC[1]
    return dx * CS + dy * SN, -dx * SN + dy * CS


def wavy(pts, amp, wl=6, seed=0):
    """a closed outline resampled and pushed in and out a little (hair, fur masses are never smooth ovals)"""
    P = np.asarray(pts, np.float32)
    Q = np.vstack([P, P[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    s = np.linspace(0, d[-1], 240, endpoint=False)
    R = np.stack([np.interp(s, d, Q[:, 0]), np.interp(s, d, Q[:, 1])], 1)
    Tg = np.roll(R, -1, 0) - np.roll(R, 1, 0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-6
    Nn = np.stack([Tg[:, 1], -Tg[:, 0]], 1)
    return R + Nn * (amp * fbm1d(240, 240 / wl, 3, seed))[:, None]


class Scene:
    def __init__(self, p):
        self.p = p
        self.plan()

    def __setattr__(self, k, v):
        # some forty canvas-sized masks and light fields are kept: float16 is plenty for 0..1 coverage and halves
        # them, which keeps the peak well under 1 GB
        if isinstance(v, np.ndarray) and v.dtype == np.float32 and v.shape == (H, W):
            v = v.astype(np.float16)
        object.__setattr__(self, k, v)

    # ------------------------------------------------------------------ shapes, planned before any paint
    def plan(self):
        p = self.p
        # adult proportions: the eye line near the middle of the head, a narrower jaw and a small pointed chin
        self.face = p.poly(FL([(-8, -176), (-80, -162), (-126, -122), (-146, -58), (-146, 8), (-134, 62), (-110, 112),
                               (-76, 152), (-40, 176), (-6, 186), (28, 178), (72, 152), (112, 108), (142, 46),
                               (152, -24), (146, -96), (108, -150), (52, -174)]), smooth=True)
        self.neck = p.tube([F(-10, 140), (996, 600), (998, 700)], [96, 104, 116])
        crown = FL([(-196, 40), (-200, -50), (-178, -132), (-118, -196), (-36, -224), (52, -222), (124, -198),
                    (174, -140), (194, -60), (198, 40)])
        falls = [(1214, 470), (1236, 516), (1226, 562), (1250, 612), (1270, 652), (1254, 700), (1262, 738), (1222, 772),
                 (1180, 752), (1140, 700), (1090, 650),
                 (1000, 628), (910, 640), (856, 640), (826, 590), (812, 520)]
        self.hairm = p.poly(wavy(crown + falls, 12, 11, seed=3))
        # a side-swept fringe: from the parting it crosses the forehead, lower on the far side
        self.fringe = p.poly(wavy(FL([(48, -218), (-30, -218), (-104, -194), (-160, -134), (-188, -52), (-184, 30),
                                       (-160, 76), (-150, 12), (-128, -26), (-94, -54), (-46, -72), (6, -86),
                                       (58, -104), (104, -124), (136, -150), (104, -194), (66, -212)]), 5, 9, seed=4))
        self.temple = np.maximum(
            p.tube(FL([(60, -206), (122, -178), (162, -110), (176, -30), (172, 50)]), [44, 52, 50, 44, 30]),
            p.poly(wavy(FL([(40, -224), (112, -208), (166, -162), (188, -80), (182, 4), (162, -32), (148, -92),
                            (116, -128), (72, -142), (42, -152)]), 3, 6, seed=5)))
        self.lock = p.tube([(1176, 470), (1200, 560), (1190, 640), (1204, 700)], [62, 66, 60, 56])
        # the cat: head with a cheek ruff, ears, the body wrapped round the front of her neck (thick at the chest
        # and the haunch, a narrower sagging belly), front legs on one side, a hind leg and the tail on the other
        hd = p.poly(wavy([(768 + 116 * np.cos(t), 604 + 98 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 40,
                                                                                            endpoint=False)], 4, 8, 5))
        ruff = np.maximum(p.ellipse(700, 652, 74, 52, -14), p.ellipse(838, 652, 74, 52, 14))
        self.cat_head = np.maximum(hd, ruff)
        self.ears = np.maximum(p.poly([(672, 548), (664, 482), (680, 452), (708, 470), (742, 518)], smooth=True),
                               p.poly([(796, 514), (836, 466), (862, 452), (874, 484), (864, 548)], smooth=True))
        self.inner_ears = np.maximum(p.poly([(686, 530), (682, 486), (692, 470), (712, 490), (726, 518)], smooth=True),
                                     p.poly([(814, 510), (840, 480), (855, 472), (860, 494), (850, 530)], smooth=True))
        self.cat_body = p.poly(wavy(p.tube_pts([(716, 690), (850, 712), (970, 724), (1070, 714), (1160, 690),
                                                (1222, 668)], [130, 104, 88, 92, 118, 130]), 6, 16, seed=7))
        self.haunch = p.poly(wavy([(1130, 640), (1186, 606), (1250, 618), (1290, 664), (1282, 716), (1220, 728),
                                   (1150, 712)], 5, 6, seed=6), smooth=False)
        self.legs = np.maximum.reduce([p.tube([(732, 690), (738, 760), (744, 824)], [54, 48, 46]),
                                       p.tube([(806, 698), (812, 772), (816, 834)], [54, 48, 46]),
                                       p.tube([(1170, 700), (1176, 770), (1180, 818)], [62, 48, 44])])
        self.paws = np.maximum.reduce([p.ellipse(745, 834, 29, 21), p.ellipse(817, 842, 29, 21),
                                       p.ellipse(1182, 828, 28, 20)])
        self.tail_path = [(1240, 700), (1268, 780), (1258, 866), (1230, 940), (1240, 1006)]
        self.tail = np.maximum(p.tube(self.tail_path, [66, 64, 60, 56, 44]), p.ellipse(1240, 1004, 22, 24))
        self.muzzle = np.maximum(np.maximum(p.ellipse(752, 652, 30, 22), p.ellipse(790, 652, 30, 22)),
                                 p.ellipse(771, 676, 28, 18))
        self.cat_front = np.clip(np.maximum.reduce([self.cat_head, self.ears, self.legs, self.paws]), 0, 1)
        self.cat = np.clip(np.maximum.reduce([self.cat_front, self.cat_body, self.haunch, self.tail]), 0, 1)
        # clothes: a torso and two sleeves; the coat fades out toward the bottom in dry strokes
        torso = p.poly([(950, 640), (870, 660), (790, 700), (760, 760), (750, 1100), (1290, 1100), (1278, 760),
                        (1240, 700), (1150, 664), (1050, 640)], smooth=False)
        arm_l = p.tube([(782, 706), (734, 830), (716, 960), (712, 1100)], [120, 150, 156, 160])
        arm_r = p.tube([(1250, 702), (1300, 830), (1318, 960), (1324, 1100)], [120, 150, 156, 160])
        self.arms = np.maximum(arm_l, arm_r)
        coat = np.clip(np.maximum.reduce([torso, arm_l, arm_r]), 0, 1)
        self.coat_raw = coat
        xs = np.arange(W, dtype=np.float32)
        edge_y = 950 + 44 * fbm1d(W, 260, 3, 11) + 0.04 * np.abs(xs - 1010)
        self.fade_b = smoothstep(edge_y[None] + 80, edge_y[None] - 70, p.YY).astype(np.float32)
        self.fade_w = smoothstep(edge_y[None] + 30, edge_y[None] - 110, p.YY).astype(np.float32)
        self.coat = blur(coat, 2.5) * self.fade_w
        self.sweater = p.poly([(950, 650), (1054, 650), (1084, 704), (1062, 840), (1030, 1000), (990, 1000),
                               (952, 840), (924, 704)], smooth=True) * self.fade_w
        # visible parts (front to back): the fringe, the cat, the face, the neck, the lock of hair behind the cat,
        # the sweater, the coat, the hair behind
        self.v_cat = self.cat * (1 - self.fringe)
        self.v_face = self.face * (1 - self.fringe) * (1 - self.temple)
        self.v_neck = self.neck * (1 - self.face) * (1 - self.cat)
        self.v_lock = self.lock * (1 - self.cat) * (1 - self.face)
        self.v_sweater = self.sweater * (1 - self.cat) * (1 - self.neck)
        self.v_coat = self.coat * (1 - self.cat) * (1 - self.sweater) * (1 - self.neck)
        self.v_hair = self.hairm * (1 - self.face) * (1 - self.neck) * (1 - self.cat) * (1 - coat) * (1 - self.lock)
        self.front_hair = np.clip(self.fringe + self.temple, 0, 1)

    # ------------------------------------------------------------------ hair flow (degrees)
    def hair_flow(self, x, y):
        x = np.asarray(x, np.float32); y = np.asarray(y, np.float32)
        u, v = to_local(x, y)
        cu, cv = 30.0, 40.0                                   # centre of the sweep, below the parting
        ru, rv = u - cu, v - cv
        left = np.arctan2(-ru, rv)                            # tangent (rv, -ru): sweeping to the left and down
        right = np.arctan2(ru, -rv)                           # tangent (-rv, ru): to the right and down
        w = smoothstep(30.0, 66.0, u)
        a_sweep = 0.5 * np.arctan2((1 - w) * np.sin(2 * left) + w * np.sin(2 * right),
                                   (1 - w) * np.cos(2 * left) + w * np.cos(2 * right)) + TILT
        fall = np.deg2rad(90 + 24 * np.sin((y - 420) / 40.0 + x / 60.0) + 0.05 * (x - 1000))
        g = np.clip(smoothstep(380, 480, y) * smoothstep(120, 165, np.abs(u)) + smoothstep(560, 620, y), 0, 1)
        c = (1 - g) * np.cos(2 * a_sweep) + g * np.cos(2 * fall)
        s = (1 - g) * np.sin(2 * a_sweep) + g * np.sin(2 * fall)
        a = 0.5 * np.arctan2(s, c)
        # keep the direction pointing along the sweep / downward (not flipped by the doubled-angle blend)
        ref = np.where(g > 0.5, fall, np.where(w > 0.5, right, left) + TILT)
        flip = np.cos(a - ref) < 0
        return np.degrees(np.where(flip, a + np.pi, a))

    # ------------------------------------------------------------------ 1. pencil sketch
    def sketch(self):
        p = self.p
        r = np.random.default_rng(5)
        pl = lambda pts, w=1.5, a=0.5, **kw: p.pencil(pts, 'pencil_light', w, a, seed=int(r.integers(1 << 30)), **kw)
        # faint rooftops on the right
        for (x0, x1, yb, h, roof) in [(1380, 1462, 780, 150, 'gable'), (1470, 1530, 790, 220, 'flat'),
                                      (1630, 1712, 776, 170, 'gable'), (1712, 1768, 786, 110, 'flat')]:
            yt = yb - h
            pl([(x0, yb + 10), (x0, yt)]); pl([(x1, yb + 6), (x1, yt)])
            if roof == 'gable':
                pl([(x0 - 8, yt + 4), ((x0 + x1) / 2, yt - 42), (x1 + 8, yt + 4)], smooth=False)
                pl([(x0 + 12, yt - 10), (x0 + 12, yt - 34), (x0 + 22, yt - 34), (x0 + 22, yt - 18)], 1.2, 0.4,
                   smooth=False)
            else:
                pl([(x0 - 6, yt), (x1 + 6, yt)])
            for wy in np.arange(yt + 22, yb - 26, 36):
                for wx in np.linspace(x0 + 14, x1 - 28, max(1, int((x1 - x0) / 38))):
                    if r.random() < 0.6:
                        pl([(wx, wy), (wx + 12, wy), (wx + 12, wy + 18), (wx, wy + 18), (wx, wy)], 1.2, 0.38,
                           smooth=False, gaps=0.3, seg=(18, 36), wobble=0.4)
        tx = 1580
        pl([(tx - 38, 790), (tx - 38, 540)]); pl([(tx + 38, 790), (tx + 38, 540)])
        pl([(tx - 46, 540), (tx - 38, 494), (tx - 18, 466), (tx, 458), (tx + 18, 466), (tx + 38, 494), (tx + 46, 540)])
        pl([(tx, 458), (tx, 424)], 1.3, 0.45)
        for wy in (590, 650, 710):
            pl([(tx - 9, wy), (tx - 9, wy - 24), (tx, wy - 32), (tx + 9, wy - 24), (tx + 9, wy)], 1.2, 0.4)
        pl([(1360, 800), (1500, 806), (1640, 798), (1790, 804)], 1.4, 0.4)
        # the figure, very lightly (most of it is painted over)
        for path in (FL([(-146, 8), (-134, 62), (-110, 112), (-76, 152), (-40, 176), (-6, 186), (28, 178),
                         (72, 152), (112, 108), (142, 46), (152, -24)]),
                     [(770, 712), (730, 830), (708, 960)], [(1262, 708), (1306, 830), (1326, 960)],
                     [(680, 600), (664, 482), (680, 452), (708, 470), (742, 518), (800, 512), (836, 466),
                      (862, 452), (874, 484), (864, 548), (884, 620)],
                     FL([(-196, 40), (-200, -50), (-178, -132), (-118, -196), (-36, -224), (52, -222), (124, -198),
                         (174, -140), (194, -60), (198, 40)])):
            p.pencil(path, 'pencil', 1.5, 0.35, seed=int(r.integers(1 << 30)))

    # ------------------------------------------------------------------ 2. background
    def background(self):
        p = self.p
        # a breath of grey behind the rooftops, fading downward and to the sides
        city = np.maximum.reduce([p.rect(1380, 640, 1462, 790), p.rect(1470, 570, 1530, 800), p.rect(1542, 470, 1618, 800),
                                  p.rect(1630, 610, 1712, 786)])
        fade = smoothstep(830, 660, p.YY) * smoothstep(1780, 1660, p.XX) * smoothstep(1370, 1430, p.XX)
        cw = p.ragged(city, amp=18, scale=50, seed=7) * fade
        p.wash(cw, 'mist', 0.16, grain=0.7, edge=1.0, dry=0.5)
        # a sprig of eucalyptus on the left, dissolving toward its foot
        fade_y = lambda y: float(np.clip((990 - y) / 300, 0.2, 1))
        p.sprig([(690, 800), (640, 660), (590, 540), (548, 430), (520, 330), (508, 270)], n=13, size=(56, 108),
                colours=('eucalyptus', 'eucalyptus', 'ochre', 'eucalyptus'), width=5.0, round_=0.8, spread=58,
                fade=fade_y, seed=12)

    # ------------------------------------------------------------------ 3. flat colour
    def block(self):
        p = self.p
        p.wash(self.v_hair, 'hair_dark', 1.0, grain=0.2, edge=0.6)
        p.wash(self.v_coat, 'powder', 1.0, grain=0.4, edge=0.15)
        p.wash(self.v_sweater, 'cream', 1.0, grain=0.3, edge=0.6)
        p.wash(self.v_neck, 'skin', 1.0, grain=0.15, edge=0.3)
        p.wash(self.v_face, 'skin', 1.0, grain=0.15, edge=0.3)
        p.wash(self.v_cat, 'ginger', 1.0, grain=0.25, edge=0.6)
        p.wash(self.front_hair, 'hair_dark', 1.0, grain=0.2, edge=0.5)
        p.wash(self.v_lock, 'hair_dark', 1.0, grain=0.2, edge=0.6)

    # ------------------------------------------------------------------ 4. modelling
    def model(self):
        p = self.p
        # face: a blended dome, warm at the rim, pale at the centre; soft strokes that wrap round it
        self.face_lit = p.model(self.v_face, 'skin', sigma=46, lo=0.1, hi=1.0, gamma=0.85, grain=0.15, edge=0.3)
        p.strokes(self.v_face, p.contour(self.face, 20, fallback=-60), ('skin', np.clip(self.face_lit * 0.9 + 0.08, 0, 1)),
                  (24, 54), (7, 13), 0.45, pressure=0.6, opacity=0.8, alpha=0.3, streak=0.3, clip=self.v_face, seed=31)
        p.glaze(blur(self.front_hair, 12) * self.v_face, '#d89a8e', 0.4, 'multiply')
        # neck: in shadow under the chin
        p.model(self.v_neck, 'neck', sigma=24, lo=0.05, hi=0.7, grain=0.15, edge=0.3)
        sh = blur(np.roll(self.face, 26, axis=0), 12) * self.v_neck
        p.glaze(sh, '#b9786c', 0.5, 'multiply')
        # hair masses: dark, a faint sheen on the crown
        p.model(self.v_hair, 'hair', lit=p.shading(self.hairm, sigma=60), lo=0.0, hi=0.6, grain=0.2, edge=0.6)
        p.model(self.front_hair, 'hair', lit=p.shading(self.front_hair, sigma=30), lo=0.05, hi=0.75, grain=0.2, edge=0.5)
        p.model(self.v_lock, 'hair', lit=p.shading(self.lock, sigma=20), lo=0.0, hi=0.6, grain=0.2, edge=0.6)
        # coat: blended under-colour, the sleeves rounder and darker at their inner edge, broad dry strokes that
        # wrap the shoulders and fall down the sleeves and the front
        cl = np.clip(0.55 * p.shading(self.coat_raw, sigma=70) + 0.45 * p.shading(self.arms, sigma=40), 0, 1)
        self.coat_lit = cl
        p.model(self.v_coat, 'powder', lit=cl, lo=0.15, hi=0.95, grain=0.4, edge=0.5)
        # the cat and the hair cast a soft shadow on the coat and the sweater
        cast = blur(np.roll(np.roll(np.clip(self.cat + self.hairm * 0.6, 0, 1), 14, axis=0), 8, axis=1), 14)
        p.glaze(cast * (1 - self.cat) * np.clip(self.v_coat + self.v_sweater, 0, 1), '#7f93b8', 0.35, 'multiply')
        seam = blur(self.arms, 8) * (1 - blur(self.arms, 8)) * 4 * self.v_coat
        p.glaze(seam * smoothstep(690, 760, p.YY), '#8ea4c6', 0.45, 'multiply')
        drape = p.field(lambda x, y: -90 + np.clip((x - 1010) / 260, -1, 1) * 32)
        fld = p.blend(p.contour(self.coat_raw, 30, fallback=-80), p.blend(p.flow(-82, 12, 260, seed=3), drape,
                      smoothstep(820, 960, p.YY)), np.clip(smoothstep(740, 860, p.YY) + self.arms * 0.6, 0, 1))
        self.coat_field = fld
        av = np.clip(self.cat + self.sweater + self.neck + self.lock, 0, 1)
        region = self.coat_raw * self.fade_b
        var = np.clip(cl + 0.55 * (noise2d(H, W, 46, 2, 17) - 0.5), 0, 1)
        dry = np.clip(self.fade_b * 1.3, 0, 1)
        p.strokes(region, fld, ('powder', var), (70, 150), (18, 34), 0.9, pressure=0.76, alpha=0.75, streak=0.35,
                  avoid=av, fade=dry, clip=self.coat_raw, seed=41)
        p.strokes(region * smoothstep(0.5, 0.15, cl), fld, ('powder_shade', 'powder_deep'), (90, 180), (20, 34),
                  0.55, pressure=0.7, alpha=0.45, streak=0.2, soft=0.85, avoid=av, fade=dry, clip=self.coat_raw,
                  seed=42)
        # sweater: cream, ribbed
        sl = p.shading(self.sweater, sigma=24)
        p.model(self.v_sweater, 'cream', lit=sl, lo=0.12, hi=0.95, grain=0.3, edge=0.6)
        p.strokes(self.v_sweater, 90, ('cream', np.clip(sl * 0.8 + 0.1, 0, 1)), (40, 90), (6, 10), 0.8, pressure=0.7,
                  alpha=0.5, streak=0.4, seed=43)
        ribs = [[(x, 700), (x + (x - 1004) * 0.04, 840), (x + (x - 1004) * 0.1, 990)] for x in np.arange(936, 1086, 17)]
        p.lines(ribs, 'cream_shade', (4.0, 6.0), 0.55, 0.5, 0.22, clip=self.v_sweater, streak=0.5, seed=44)
        # cat: blended dome under-colour, cream muzzle and paws, pink inner ears
        self.cat_lit_head = p.model(np.clip(self.cat_head + self.ears, 0, 1) * (1 - self.fringe), 'ginger', sigma=36,
                                    lo=0.12, hi=0.9, grain=0.25, edge=0.6)
        body = np.clip(self.cat_body + self.haunch + self.legs, 0, 1) * (1 - self.cat_head) * self.v_cat
        self.cat_lit_body = p.model(body, 'ginger', sigma=30, lo=0.1, hi=0.85, grain=0.25, edge=0.6)
        self.cat_lit_tail = p.model(self.tail * self.v_cat, 'ginger', sigma=16, lo=0.12, hi=0.88, grain=0.25, edge=0.6)
        p.model(blur(self.muzzle, 4), 'cream', sigma=12, lo=0.3, hi=1.0, grain=0.2, edge=0.5)
        p.model(blur(self.paws, 3), 'cream', sigma=10, lo=0.3, hi=1.0, grain=0.2, edge=0.5)
        tip = self.tail * smoothstep(940, 990, p.YY)
        p.wash(blur(tip, 6), 'fur_cream', 0.9, grain=0.2, edge=0.5)
        p.wash(blur(self.inner_ears, 2.5), 'ear_pink', 0.85, grain=0.3, edge=0.5)

    # ------------------------------------------------------------------ 5. the cat's fur
    def fur(self):
        p = self.p
        head = self.cat_head * (1 - self.fringe)
        rad = p.radial(*NOSE_C, turb=10, scale=60, seed=51)
        lit = self.cat_lit_head
        # soft, broad fur strokes first (the pastel), then fine locks on top
        p.strokes(head * (1 - self.muzzle), rad, ('ginger', np.clip(lit, 0, 1)), (16, 34), (5, 9), 1.0,
                  pressure=0.7, alpha=0.55, streak=0.5, taper=(0.7, 0.05), seed=50)
        p.fur(head * smoothstep(0.5, 0.15, lit), rad, ('ginger_dark',), (14, 26), (1.4, 2.0), 0.55, alpha=0.5,
              seed=52)
        p.fur(head * (1 - self.muzzle), rad, ('ginger', 'orange', 'tangerine'), (14, 28), (1.2, 1.9), 0.6, alpha=0.55,
              seed=53)
        p.fur(head * smoothstep(0.5, 0.85, lit) * (1 - self.muzzle), rad, ('apricot', 'peach'), (12, 22), (1.1, 1.6),
              0.5, alpha=0.55, seed=54)
        # forehead stripes: a few darker tufts
        for (sx, sy, a) in [(752, 552, 100), (771, 546, 90), (790, 552, 80), (730, 564, 118), (812, 564, 62)]:
            p.fur(p.ellipse(sx, sy, 6, 20, a), a, 'ginger_deep', (14, 22), (1.6, 2.2), 1.6, tuft=(4, 8), alpha=0.6,
                  seed=int(sx + sy))
        p.fur(self.muzzle, rad, ('fur_cream', 'fur_white'), (8, 16), (1.0, 1.5), 0.8, alpha=0.6, seed=55)
        ef = p.flow(-90, 20, 40, seed=56)
        p.fur(self.ears * (1 - self.inner_ears), ef, ('ginger', 'tangerine'), (10, 18), (1.2, 1.8), 0.8, alpha=0.6,
              seed=57)
        p.strands(self.inner_ears, lambda x, y: -90 + (x - 770) * 0.6, ('fur_cream', 'fur_white'), n=50,
                  length=(12, 26), width=(0.9, 1.3), clip=False, alpha=0.7, seed=58)
        # body across her shoulders, legs, haunch: fur follows the body, then the legs down
        body = np.clip(self.cat_body + self.haunch + self.legs, 0, 1) * (1 - self.cat_head) * self.v_cat
        bf = p.blend(p.flow(178, 15, 120, seed=59), p.flow(95, 8, 80, seed=60), np.clip(self.legs, 0, 1))
        bl = self.cat_lit_body
        p.strokes(body, bf, ('ginger', np.clip(bl, 0, 1)), (20, 44), (5, 10), 1.0, pressure=0.7, alpha=0.55,
                  streak=0.5, taper=(0.7, 0.05), seed=60)
        p.fur(body * smoothstep(0.5, 0.15, bl), bf, ('ginger_dark',), (16, 30), (1.4, 2.0), 0.55, alpha=0.5, seed=61)
        p.fur(body, bf, ('ginger', 'orange', 'tangerine'), (16, 32), (1.2, 1.9), 0.6, alpha=0.55, seed=62)
        p.fur(body * smoothstep(0.5, 0.85, bl), bf, ('apricot', 'peach'), (14, 26), (1.1, 1.6), 0.5, alpha=0.55, seed=63)
        p.fur(self.paws, 90, ('fur_cream', 'fur_white'), (8, 14), (1.0, 1.5), 1.0, alpha=0.6, seed=64)
        for (x, y) in [(736, 846), (752, 848), (808, 854), (824, 856)]:
            p.line([(x, y - 9), (x + 1, y + 2)], 1.5, 'cream_deep', 0.5, taper=(0.4, 0.4))
        # tail: fur along it, darker rings, a cream tip
        tl = self.tail * self.v_cat
        tfield = p.field(lambda x, y: 95 + 12 * np.sin(y / 60.0))
        p.strokes(tl * (1 - smoothstep(940, 990, p.YY)), tfield, ('ginger', np.clip(self.cat_lit_tail, 0, 1)), (20, 40),
                  (5, 10), 1.0, pressure=0.7, alpha=0.55, streak=0.5, taper=(0.7, 0.05), seed=64)
        for yb in (752, 826, 898):
            ring = tl * smoothstep(yb - 14, yb, p.YY) * smoothstep(yb + 24, yb + 6, p.YY)
            p.strokes(ring, tfield, 'ginger_dark', (16, 28), (5, 8), 1.4, pressure=0.7, alpha=0.5, streak=0.5, seed=yb)
            p.fur(ring, tfield, ('ginger_dark', 'ginger_deep'), (14, 24), (1.3, 1.9), 0.9, alpha=0.5, seed=yb + 1)
        p.fur(tl * (1 - smoothstep(940, 990, p.YY)), tfield, ('ginger', 'orange', 'tangerine'), (16, 30), (1.2, 1.8),
              0.6, alpha=0.5, seed=65)
        p.fur(tl * smoothstep(0.5, 0.85, self.cat_lit_tail), tfield, ('apricot', 'peach'), (12, 24), (1.1, 1.6), 0.45,
              alpha=0.5, seed=66)
        p.fur(tl * smoothstep(950, 985, p.YY), tfield, ('fur_cream', 'fur_white'), (12, 22), (1.1, 1.6), 1.0, alpha=0.6,
              seed=67)
        # a fluffy silhouette everywhere the cat meets something else
        light = p.LIGHT
        bm = np.clip(self.cat_body + self.haunch, 0, 1) * (1 - self.cat_head) * self.v_cat
        p.fluff(head, (10, 24), n=900, width=(1.1, 1.7), out=0.75, field=rad, light=light, alpha=0.5, curl=8, seed=68)
        p.fluff(bm, (10, 22), n=900, width=(1.0, 1.6), out=0.55, field=bf, light=light, alpha=0.45, curl=8, seed=69)
        p.fluff(tl, (10, 22), n=520, width=(1.0, 1.6), out=0.55, field=tfield, light=light, alpha=0.5, curl=8, seed=70)
        p.fluff(self.legs * (1 - self.cat_head), (8, 14), n=300, width=(1.0, 1.4), out=0.5, field=90, light=light,
                alpha=0.45, curl=8, seed=71)

    # ------------------------------------------------------------------ 6. her hair
    def hair(self):
        p = self.p
        fl = self.hair_flow
        cols = ('hair_black', 'hair_dark', 'hair', 'hair_blue', 'hair_grey')
        sheen = np.clip(p.shading(self.hairm, sigma=60) * 0.85 + 0.05, 0, 1)
        p.strands(self.v_hair, fl, cols[:3], n=1600, length=(70, 220), width=(1.6, 2.8), shade=sheen, spread=0.3,
                  curl=0.4, jitter=5, alpha=0.8, lock=(14, 10), seed=81)
        p.strands(self.v_hair, fl, cols[2:], n=700, length=(60, 180), width=(1.0, 1.8), shade=sheen, spread=0.22,
                  curl=0.4, jitter=5, alpha=0.7, lock=(10, 7), seed=82)
        ls = np.clip(p.shading(self.lock, sigma=18) * 0.9 + 0.05, 0, 1)
        p.strands(self.v_lock, fl, cols[:4], n=520, length=(60, 180), width=(1.3, 2.4), shade=ls, spread=0.3,
                  curl=0.3, jitter=4, alpha=0.85, lock=(12, 8), seed=83)
        fs = np.clip(p.shading(self.front_hair, sigma=30) * 0.9 + 0.05, 0, 1)
        p.strands(self.front_hair, fl, cols[:3], n=1100, length=(70, 240), width=(1.4, 2.6), shade=fs, spread=0.3,
                  curl=0.2, jitter=4, alpha=0.85, lock=(14, 9), seed=84)
        p.strands(self.front_hair, fl, cols[2:], n=460, length=(70, 220), width=(1.0, 1.7), shade=fs, spread=0.22,
                  curl=0.2, jitter=4, alpha=0.75, lock=(10, 6), seed=85)

    # ------------------------------------------------------------------ 7. faces
    def faces(self):
        p = self.p
        # a soft warm contour on the shadow side of her face and under the chin
        p.line(FL([(150, -20), (144, 40), (120, 100), (80, 148), (32, 178), (-6, 188), (-44, 178)]), 2.4, 'skin_deep',
               0.35, taper=(0.5, 0.5), dry=0.4)
        p.brow(FL([(-106, -46), (-82, -57), (-50, -54)]), 10, 'brow', 0.9, seed=91)
        p.brow(FL([(14, -52), (52, -62), (90, -53)]), 11, 'brow', 0.9, seed=92)
        look = (-0.6, 0.12)
        p.eye(*F(-70, 2), 28, 33, look=look, iris_r=0.72, lid=0.2, rot=-7, side=-1, lashes=0, flick=0.32)
        p.eye(*F(46, 2), 34, 37, look=look, iris_r=0.72, lid=0.2, rot=-7, side=1, lashes=0, flick=0.38)
        p.blush(*F(-94, 78), 60, 50, 'blush', 0.72)
        p.blush(*F(70, 80), 76, 62, 'blush', 0.72)
        p.nose(*F(-26, 80), 17, side=1, alpha=1.1, bridge=78, shade=0.5)
        p.mouth(*F(-18, 128), 34, 0.6)
        # the cat's face
        look_c = (0.38, -0.3)
        for (x, y, sd) in ((726, 598, -1), (812, 596, 1)):
            p.eye(x, y, 23, 24, iris='amber', iris_light='amber_light', iris_r=0.78, look=look_c, lid=0.0,
                  lid_skin='ginger', line_colour='#5a2a16', line_w=3.2, flick=0.0, lashes=0, crease=0, lower=0.3,
                  side=sd)
        nose = p.poly([(758, 632), (782, 632), (770, 646)], smooth=True)
        p.wash(blur(nose, 1.2), '#d77d78', 0.95, grain=0.1, edge=0.2)
        p.line([(770, 646), (770, 656)], 1.8, '#7a3a2c', 0.7)
        p.line([(770, 656), (762, 662), (754, 660)], 1.8, '#7a3a2c', 0.6, taper=(0.3, 0.5))
        p.line([(770, 656), (778, 662), (786, 660)], 1.8, '#7a3a2c', 0.6, taper=(0.3, 0.5))
        p.blush(742, 652, 22, 16, 'blush', 0.22)
        p.blush(800, 652, 22, 16, 'blush', 0.22)
        r = np.random.default_rng(93)
        for sgn, x0 in ((-1, 742), (1, 798)):
            for k in range(3):
                y0 = 652 + k * 7
                L = r.uniform(60, 86)
                ang = np.deg2rad((180 if sgn < 0 else 0) + sgn * (8 - k * 10))
                pts = [(x0, y0), (x0 + np.cos(ang) * L * 0.5, y0 + np.sin(ang) * L * 0.5 + 2),
                       (x0 + np.cos(ang) * L, y0 + np.sin(ang) * L + 8)]
                p.line(pts, 1.4, 'fur_white', 0.7, taper=(0.1, 0.9))

    # ------------------------------------------------------------------ 8. last touches
    def highlights(self):
        p = self.p
        av = np.clip(self.cat + self.sweater + self.neck + self.lock, 0, 1)
        p.strokes(self.coat_raw * self.fade_b * smoothstep(0.55, 0.85, self.coat_lit), self.coat_field,
                  ('powder_pale', 'white'), (60, 130), (8, 18), 0.45, pressure=0.66, opacity=0.95, alpha=0.75,
                  streak=0.75, avoid=av, seed=101)
        # loose hairs: a few fly out of the silhouette
        rim = blur(self.hairm, 3)
        roots = (smoothstep(0.3, 0.5, rim) * smoothstep(0.9, 0.7, rim)) * (1 - self.cat) * smoothstep(640, 600, p.YY)
        p.strands(self.hairm, self.hair_flow, ('hair_dark', 'hair', 'hair_blue'), n=50, length=(50, 140),
                  width=(0.8, 1.2), roots=roots, curl=2.0, jitter=20, alpha=0.6, clip=False, seed=102)
        p.strands(self.fringe, self.hair_flow, ('hair_dark', 'hair_blue'), n=14, length=(60, 160), width=(0.8, 1.1),
                  curl=1.4, jitter=12, alpha=0.55, clip=False, seed=103)
        head = self.cat_head * (1 - self.fringe)
        p.strands(head * smoothstep(0.6, 0.9, self.cat_lit_head), p.radial(*NOSE_C, seed=104), ('peach', 'fur_white'),
                  n=50, length=(10, 22), width=(0.8, 1.2), alpha=0.55, clip=True, seed=105)


PHASES = ('sketch', 'background', 'block', 'model', 'fur', 'hair', 'faces', 'highlights')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'pastelvignette_marmalade_scarf.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:10s} {time.time() - T0:5.1f}s')) if os.environ.get('PV_TIMING') else (lambda n: None)
    p = PastelVignette(W, H, seed=7, keep_stages=bool(stages), stages_dir=stages)
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
    print('saved', out, f'{time.time() - T0:.1f}s', p.n_strokes, 'strokes')


if __name__ == '__main__':
    main()
