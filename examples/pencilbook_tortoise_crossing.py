"""Example (warm pencil storybook): 大龟过河 · The Tortoise Crossing -- a picture-book page in soft, layered
coloured pencil on warm toothy paper.

Dusk. A very old, very large tortoise wades slowly across a shallow stream. On its back it carries a little garden:
a mossy cap with tufts of grass and wildflowers, a small tree in autumn gold, and a paper lantern hanging from a
crooked post. Beside it, on the stepping stones, walks a small child in a yellow raincoat with a lantern of their
own, looking up at the tortoise, which has lowered its head to look back. Behind them the sky goes from soft blue to
peach and butter over the hills, the sun is just down behind the far ridge, and a few cottages on the hillside have
lit their windows. The water carries the warm sky, the cottages' lights and the tortoise's legs.

Everything is coloured pencil: every surface is many fine strokes that follow its form (the sky in long horizontals,
the hills along their slopes, the shell round each scute's growth rings, the neck across its wrinkles, the coat down
its folds, moss and hair in tufts), laid in layers -- light under-layer, local colour, the shadow of the same family,
a warm glaze in the light and a cool one in the shade -- with the tooth of the warm paper showing through as fine
specks. No ink lines, no black.

Painted in the order an illustrator works: paper -> sky -> hills and village -> stream -> the tortoise's first layer
-> modelling the tortoise -> the garden on its back -> the child and the stepping stones -> reflections and ripples
-> lights (lanterns, windows, the warm rim of the low sun) and the near bank.
--stages writes those steps as snapshots for the draw-on. No image model.
python3 pencilbook_tortoise_crossing.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from pencilbook import PencilStorybook, hexc
from core import blur, spline, smoothstep, noise2d

W, H = 1920, 1080
LIGHT = (-0.82, -0.45, 0.42)            # the sun just down behind the left-hand ridge
SUN = (300, 512)

# the tortoise (side view, walking left); the shell's upper outline and its lower rim, front end -> back end
TOP = [(846, 646), (868, 534), (920, 434), (1000, 352), (1110, 296), (1250, 270), (1400, 280), (1530, 326),
       (1625, 406), (1688, 504), (1712, 594), (1714, 674)]
RIM = [(846, 646), (880, 684), (960, 718), (1080, 734), (1240, 742), (1400, 740), (1540, 730), (1640, 714),
       (1714, 674)]
WATER_T = 846                           # where the tortoise's legs meet the water
HEAD = [(774, 610), (736, 584), (690, 574), (640, 580), (604, 600), (582, 627), (582, 652), (598, 673),
        (636, 690), (690, 698), (746, 694), (788, 676)]
EYE = (650, 621)
NECK = [(936, 640), (872, 630), (812, 618), (772, 612), (758, 648), (770, 690), (806, 716), (858, 736), (936, 748)]
CHILD = dict(x=440, y=869, h=206)
STONES = [(444, 882, 76, 26), (296, 960, 84, 29), (566, 814, 52, 18), (650, 764, 42, 15)]
TREE = dict(x=1374, y=290, h=122, r=118, clumps=11, lean=-0.03, seed=77)
POST = [(1090, 308), (1086, 250), (1081, 196), (1068, 174), (1046, 168)]
LANTERN = (1044, 178, 38)
COTTAGES = [  # x, ground y, w, wall h, wall, roof, seed
    (64, 566, 72, 50, ('cream', 'ivory', 'sand', 'tan'), ('peach', 'terracotta', 'brick', 'sienna'), 11),
    (182, 552, 60, 44, ('powder', 'sky_pale', 'cornflower', 'slate'), ('peach', 'coral', 'brick', 'sienna'), 12),
    (300, 560, 82, 54, ('cream', 'sun', 'apricot', 'amber'), ('lavender', 'slate', 'indigo', 'violet'), 13),
    (440, 572, 58, 42, ('cream', 'pink', 'rose', 'brick'), ('peach', 'terracotta', 'brick', 'sienna'), 14),
    (1768, 566, 70, 46, ('cream', 'ivory', 'sand', 'tan'), ('lavender', 'slate', 'indigo', 'violet'), 15),
]


def curve(pts, n):
    """n points along a spline through pts, evenly by arc length"""
    P = spline(pts, 16)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, d[-1], n)
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)


class Scene:
    def __init__(self, p):
        self.p = p
        self.r = np.random.default_rng(5)
        self.plan()

    def sd(self):
        return int(self.r.integers(1 << 30))

    # ------------------------------------------------------------------ masks first (colour round them)
    def plan(self):
        p = self.p
        self.T = curve(TOP, 240); self.B = curve(RIM, 240)
        self.shell = p.poly(np.vstack([self.T, self.B[::-1]]))
        under = self.B.copy()
        under[:, 1] += 46 * np.sin(np.linspace(0, np.pi, len(under))) ** 0.7
        self.plastron = p.poly(np.vstack([self.B, under[::-1]])) * (1 - self.shell)
        self.neck = p.poly(NECK, smooth=True)
        self.head = p.poly(HEAD, smooth=True)
        wl = smoothstep(WATER_T + 2, WATER_T - 2, p.YY)
        self.legs = dict(
            front=p.poly([(950, 700), (1082, 698), (1100, 748), (1084, 800), (1066, 866), (880, 866), (894, 800),
                          (918, 748)], smooth=True) * wl,
            back=p.poly([(1494, 718), (1638, 710), (1668, 760), (1692, 820), (1708, 866), (1524, 866), (1514, 810),
                         (1488, 768)], smooth=True) * wl,
            far_front=p.poly([(1086, 736), (1178, 736), (1196, 866), (1090, 866)], smooth=True) * wl,
            far_back=p.poly([(1418, 740), (1502, 740), (1500, 866), (1406, 866)], smooth=True) * wl)
        near = np.maximum(self.legs['front'], self.legs['back'])
        far = np.maximum(self.legs['far_front'], self.legs['far_back']) * (1 - near)
        self.far_legs = far * (1 - self.shell) * (1 - self.plastron)
        self.near_legs = near * (1 - self.shell)
        self.tort = np.clip(self.shell + self.plastron + self.neck + self.head + near + far, 0, 1)
        # the tree and the lantern post on its back, planned now so the sky is coloured round them
        self.crown, self.trunk, _, _ = p.tree_plan(TREE['x'], TREE['y'], TREE['h'], TREE['r'], TREE['clumps'],
                                                   TREE['lean'], TREE['seed'])
        self.postm = p.tube(POST, 13, 7)
        # the child and the stones
        c = p.child(CHILD['x'], CHILD['y'], CHILD['h'], 1, look=(0.6, -0.8), light=LIGHT, paint=False, seed=21)
        self.child_info = c
        self.childm = blur(c['mask'], 0.8)
        self.child_lantern = p.ellipse(c['hand'][0], c['hand'][1] + 22, 18, 20)
        self.stones = np.zeros((H, W), np.float32)
        for (cx, cy, rx, ry) in STONES:
            self.stones = np.maximum(self.stones, p.ellipse(cx, cy, rx * 1.02, ry * 1.1))
        self.fg = np.clip(self.tort + self.crown + self.trunk + self.postm, 0, 1)
        # land, water
        self.far_ridge = ([0, 200, 420, 700, 950, 1200, 1500, 1750, 1920], [522, 497, 512, 470, 500, 482, 506, 472, 492])
        self.near_ridge = ([0, 250, 520, 800, 1100, 1400, 1650, 1920], [548, 530, 556, 566, 568, 560, 544, 552])
        self.bank_y = p.line_y([0, 500, 1000, 1500, 1920], [642, 630, 634, 628, 638])
        self.water = (p.YY > self.bank_y[None]).astype(np.float32)
        NB = ([0, 240, 560, 900, 1250, 1560, 1920], [944, 976, 1000, 1006, 998, 982, 948])
        self.nearbank = p.below(*NB)
        self.water = self.water * (1 - self.nearbank)

    # ------------------------------------------------------------------ 1 sky
    def cloud(self, cx, cy, w, h, bumps=4):
        """a soft storybook cloud bank: a flat-bottomed lens with a few rounded bumps on top"""
        p = self.p
        m = p.ellipse(cx, cy, w * 0.5, h * 0.42)
        for k in range(bumps):
            t = (k + 0.5) / bumps - 0.5 + self.r.normal(0, 0.05)
            bw = w * self.r.uniform(0.16, 0.26)
            m = np.maximum(m, p.ellipse(cx + t * w * 0.8, cy - h * self.r.uniform(0.15, 0.45), bw, bw * self.r.uniform(0.55, 0.8)))
        m = m * (p.YY < cy + h * 0.3) + m * (p.YY >= cy + h * 0.3) * smoothstep(cy + h * 0.45, cy + h * 0.3, p.YY)
        return blur(m, 3)

    def sky_phase(self):
        p = self.p
        sky = p.below(self.far_ridge[0], np.asarray(self.far_ridge[1]) + 30, invert=True)
        clouds = np.zeros((H, W), np.float32)
        for (cx, cy, w, h, nb) in [(330, 196, 420, 70, 5), (640, 150, 260, 44, 3), (120, 318, 230, 40, 3),
                                   (1530, 120, 400, 62, 5), (1820, 230, 240, 42, 3), (760, 330, 300, 34, 4),
                                   (1180, 380, 230, 30, 3)]:
            clouds = np.maximum(clouds, self.cloud(cx, cy, w, h, nb))
        sun = np.exp(-(((p.XX - SUN[0]) / 560) ** 2 + ((p.YY - SUN[1]) / 280) ** 2))
        v = np.clip(p.value(0.0, 1.0, 0, 560, 0.03) * (1 - 0.15 * sun) + 0.2 * sun, 0, 1)
        keep = sky * (1 - 0.9 * clouds)
        f = p.flow(-2, 4, 400)
        p.hatch(keep, f, ('dusk_sky', v), length=(70, 160), width=(1.8, 2.7), density=1.7, pressure=0.78,
                avoid=self.fg, seed=self.sd())
        p.hatch(keep, p.rotate(f, -7), ('dusk_sky', np.clip(v + 0.05, 0, 1)), length=(60, 140), width=(1.8, 2.6),
                density=1.3, pressure=0.76, avoid=self.fg, seed=self.sd())
        p.hatch(keep, p.rotate(f, 5), ('dusk_sky', np.clip(v - 0.04, 0, 1)), length=(40, 100), width=(1.7, 2.4),
                density=1.0, pressure=0.7, alpha=0.5, avoid=self.fg, seed=self.sd())
        p.hatch(sky * sun * 0.9 * (1 - 0.6 * clouds), p.rotate(f, 4), ('glow', np.clip(1 - sun, 0, 1)), length=(60, 140),
                width=(1.8, 2.6), density=1.2, pressure=0.72, opacity=0.5, avoid=self.fg, seed=self.sd())
        # clouds: the paper left almost white, a cream top, lavender in the core, warm peach underneath (the sun
        # is below them), strokes running along the cloud
        cf = p.blend(f, p.contour(clouds, 6), 0.4)
        under = blur(clouds * (1 - np.roll(clouds, -26, 0)), 9) * clouds
        top = blur(clouds * (1 - np.roll(clouds, 18, 0)), 7) * clouds
        core = clouds * smoothstep(0.55, 0.95, blur(clouds, 6))
        p.hatch(clouds, cf, ('cream', 'white', 'ivory'), (40, 100), (1.6, 2.4), 1.0, 0.7, opacity=0.6, alpha=0.6,
                avoid=self.fg, seed=self.sd())
        p.hatch(core * 0.7, cf, ('lavender', 'mauve', 'powder'), (40, 100), (1.6, 2.4), 0.9, 0.7, alpha=0.5,
                avoid=self.fg, seed=self.sd())
        p.hatch(np.clip(under * 1.3, 0, 1), cf, ('peach', 'apricot', 'butter'), (40, 100), (1.6, 2.4), 1.0, 0.72,
                opacity=0.45, alpha=0.55, avoid=self.fg, seed=self.sd())
        p.hatch(np.clip(top * 1.2, 0, 1) * (1 - 0.5 * sun), cf, ('sun', 'butter', 'cream'), (30, 80), (1.5, 2.2), 0.8,
                0.66, opacity=0.6, alpha=0.5, avoid=self.fg, seed=self.sd())
        # the sun just gone: a pale disc half behind the ridge
        disc = p.ellipse(SUN[0], SUN[1] - 6, 40, 40)
        p.lift(disc, 'sun', 0.8, 0.2)
        p.hatch(disc, 0, 'butter', (12, 30), (1.6, 2.2), 1.6, 0.7, 0.6, seed=self.sd())

    # ------------------------------------------------------------------ 2 hills, village, far bank
    def land_phase(self):
        p = self.p
        avoid = self.fg
        far = p.below(self.far_ridge[0], self.far_ridge[1]) * (1 - p.below(None, 600))
        far_l = p.shading(far, LIGHT, 60, flat=0.4)
        p.form(far, ('lavender', 'periwinkle', 'violet', 'indigo'), p.flow(-6, 14, 200), LIGHT,
               length=(30, 70), width=(1.6, 2.4), density=1.2, lit=far_l * 0.7 + 0.2, warm='peach', avoid=avoid,
               seed=self.sd())
        near = p.below(self.near_ridge[0], self.near_ridge[1]) * (p.YY < self.bank_y[None] + 2)
        hill_f = p.blend(p.flow(-10, 16, 220), p.contour(near, 30, 0), 0.35)
        lit = p.shading(near, LIGHT, 80, flat=0.3)
        p.form(near, ('meadow', 'yellowgreen', 'grass', 'moss'), hill_f, LIGHT, length=(26, 60), width=(1.6, 2.4),
               density=1.3, lit=lit, warm='butter', cool='lavender', avoid=avoid, seed=self.sd())
        # hedgerows and a few far trees along the hill
        for (tx, ty, th, tr) in [(140, 560, 30, 22), (262, 548, 36, 26), (395, 566, 34, 24), (540, 576, 40, 28),
                                 (1700, 562, 34, 26), (1880, 570, 44, 32), (860, 580, 26, 20)]:
            p.tree(tx, ty, th, tr, ('meadow', 'yellowgreen', 'moss', 'forest'), clumps=5, leaf=(4, 8), light=LIGHT,
                   avoid=avoid, seed=self.sd())
        for (x, y, w, h, wall, roof, s) in COTTAGES:
            p.cottage(x, y, w, h, wall, roof, light=LIGHT, glow=0.0, avoid=avoid, seed=s)
        # the far bank: a strip of grass and reeds at the water's edge
        bank = (p.YY > self.bank_y[None] - 26) * (p.YY < self.bank_y[None] + 2)
        bank = blur(bank.astype(np.float32), 2)
        p.hatch(bank, p.flow(-4, 10), ('grass', 'moss', 'olive'), (24, 60), (1.6, 2.2), 1.4, 0.76, avoid=avoid,
                seed=self.sd())
        p.grass(bank * smoothstep(0.2, 0.8, noise2d(H, W, 60, 2, self.sd())), ('moss', 'olive', 'grass', 'forest'),
                height=(12, 30), density=0.6, avoid=avoid, seed=self.sd())

    # ------------------------------------------------------------------ 3 the stream
    def water_phase(self):
        p = self.p
        av = np.clip(self.fg + self.childm + self.stones, 0, 1)
        src = p.C.copy()
        depth = np.clip((p.YY - self.bank_y[None]) / 340, 0, 1)
        p.reflect(self.bank_y, self.water, src=src, ripple=7, stretch=0.9, darken=0.08, tint='cornflower',
                  mixw=0.16, length=(40, 110), width=(1.7, 2.5), density=1.8, pressure=0.76, opacity=0.38,
                  field=p.flow(0, 3, 300), seed=self.sd())
        # the stream's own body: a cooler blue-green laid deeper toward us, and darker ripple bands
        p.hatch(self.water * (0.25 + 0.5 * depth) * (1 - av), p.flow(0, 3), ('aqua', 'teal', 'cornflower'),
                (40, 120), (1.6, 2.4), 0.9, 0.66, opacity=0.3, alpha=0.5, seed=self.sd())
        bands = smoothstep(0.55, 0.8, noise2d(H, W, 14, 2, self.sd()) * 0.7 + 0.3 * noise2d(H, W, 50, 2, self.sd()))
        bands = bands * np.clip(1 - np.abs(np.sin(p.YY / 9.0)) * 0.3, 0, 1)
        p.hatch(self.water * bands * 0.8 * (1 - av), p.flow(0, 2), ('cobalt', 'slate', 'teal'), (30, 90), (1.4, 2.0),
                0.8, 0.7, alpha=0.55, seed=self.sd())
        light_bands = smoothstep(0.62, 0.85, noise2d(H, W, 18, 2, self.sd()))
        p.hatch(self.water * light_bands * 0.7 * (1 - av), p.flow(0, 2), ('sun', 'peach', 'cream'), (30, 90),
                (1.4, 2.0), 0.6, 0.66, opacity=0.5, alpha=0.5, seed=self.sd())
        # the sunset's warm path on the water below the sun
        path_ = np.exp(-((p.XX - SUN[0]) / (60 + 0.5 * np.maximum(0, p.YY - 640))) ** 2) * smoothstep(900, 650, p.YY)
        p.hatch(self.water * path_ * (1 - av) * (0.45 + 0.55 * smoothstep(0.4, 0.6, noise2d(H, W, 10, 2, self.sd()))),
                p.flow(0, 2), ('sun', 'glow', 'apricot', 'butter'), (20, 70), (1.5, 2.2), 1.7, 0.76, opacity=0.72,
                alpha=0.75, seed=self.sd())
        # warm reflections of the lit cottage windows, broken into horizontal strokes
        for (x, y, w, h, *_rest) in COTTAGES:
            wx = x + w * 0.36
            yy = 2 * self.bank_y[int(min(W - 1, wx))] - (y - h * 0.5)
            m = p.ellipse(wx, yy + 14, w * 0.2, 30) * self.water * (1 - av)
            p.hatch(m, 0, ('lantern', 'glow', 'flame'), (8, 22), (1.5, 2.1), 1.0, 0.72, opacity=0.7, alpha=0.7,
                    seed=self.sd())

    # ------------------------------------------------------------------ 4 the tortoise: first layer
    def tortoise_base(self):
        p = self.p
        self.shell_lit = p.shading(self.shell, LIGHT, 120)
        p.hatch(self.shell, p.contour(self.shell, 30, fallback=-30), ('sand', 'gold', 'tan'), (24, 54), (1.7, 2.4),
                1.4, 0.7, seed=self.sd())
        skin = np.clip(self.neck + self.head + self.near_legs, 0, 1) * (1 - self.shell)
        self.skin = skin
        p.hatch(skin, p.contour(skin, 12, 90, fallback=80), ('lichen', 'sand'), (14, 34), (1.6, 2.2), 1.4, 0.7,
                seed=self.sd())
        p.hatch(self.far_legs + self.plastron, 80, ('sage', 'tan'), (14, 30), (1.6, 2.2), 1.3, 0.7, seed=self.sd())

    # ------------------------------------------------------------------ 5 modelling the tortoise
    def P(self, u, v):
        """shell coordinates -> canvas: u along the shell (front 0 .. back 1), v from the rim (0) to the top (1)"""
        u = np.clip(np.asarray(u, np.float32), 0, 1); v = np.asarray(v, np.float32)
        i = u * (len(self.T) - 1)
        i0 = np.minimum(i.astype(int), len(self.T) - 2); f = (i - i0)[..., None]
        Tp = self.T[i0] * (1 - f) + self.T[i0 + 1] * f
        Bp = self.B[i0] * (1 - f) + self.B[i0 + 1] * f
        return Bp * (1 - v[..., None]) + Tp * v[..., None]

    def tortoise_model(self):
        p = self.p
        sd = self.sd
        P = self.P
        # far legs and the underside, in shadow and cool
        p.form(self.far_legs, ('olive', 'umber', 'sepia', 'indigo'), 85, LIGHT, length=(14, 30), density=1.5,
               lit=p.shading(self.far_legs, LIGHT) * 0.3, cool='violet', seed=sd())
        p.form(self.plastron, ('tan', 'olive', 'umber', 'sepia'), 4, LIGHT, length=(18, 40), density=1.4,
               lit=np.full((H, W), 0.3, np.float32), cool='violet', seed=sd())
        # the shell, all over: amber and ochre, lit from the low sun on the left
        sl = self.shell_lit
        p.form(self.shell, ('gold', 'ochre', 'amber', 'sienna'), p.contour(self.shell, 40, fallback=-30), LIGHT,
               length=(22, 50), width=(1.6, 2.4), density=1.3, lit=sl, warm='butter', cool='lavender', seed=sd())
        # the scutes: each a low dome with growth rings, laid out in (u, v)
        ub = np.linspace(0.015, 0.985, 13) + np.r_[0, self.r.normal(0, 0.004, 11), 0]
        cu = [0.04, 0.27, 0.49, 0.71, 0.95]
        tl = [0.3, 0.13, 0.0, -0.13, -0.3]
        vu = [0.17, 0.39, 0.61, 0.83]
        V0, V1 = 0.165, 0.625

        def cell(u0, u1, v0, v1, t0=0.0, t1=0.0, n=16):
            us = np.linspace(u0, u1, n); vs = np.linspace(v0, v1, n)
            bow = (lambda vv: 0.05 * (vv - V0) * (V1 - vv) / 0.05) if v0 >= V0 - 1e-3 and v1 <= V1 + 1e-3 else (lambda vv: 0.0)
            sh = lambda uu, vv, t: uu + t * (vv - 0.4) + bow(vv)
            tt = np.interp(us, [u0, u1], [t0, t1])
            pts = np.vstack([P(sh(us, v0, tt), np.full(n, v0)), P(sh(u1, vs, t1), vs),
                             P(sh(us[::-1], v1, tt[::-1]), np.full(n, v1)), P(sh(u0, vs[::-1], t0), vs[::-1])])
            return smoothstep(0.4, 0.75, blur(p.poly(pts), 4.0)) * self.shell

        cells = [('m', cell(ub[k], ub[k + 1], 0.0, V0)) for k in range(12)]
        cells += [('c', cell(cu[k], cu[k + 1], V0, V1, tl[k], tl[k + 1])) for k in range(4)]
        cells += [('v', cell(vu[k], vu[k + 1], V1, 1.0)) for k in range(3)]
        for kind, m in cells:
            d = blur(m, 5 if kind == 'm' else 11)
            f = p.contour(m, 4 if kind == 'm' else 9, fallback=-30)
            loc = p.shading(m, LIGHT, 14 if kind == 'm' else 34)
            lo = m * smoothstep(0.55, 0.9, loc) * (0.5 + 0.5 * sl)
            p.hatch(lo, f, ('butter', 'gold', 'sun'), (10, 26), (1.4, 2.0), 1.2, 0.72, opacity=0.55, alpha=0.6,
                    seed=sd())
            p.hatch(m * smoothstep(0.45, 0.9, 1 - loc), f, ('sienna', 'amber', 'brown'), (10, 26), (1.4, 2.0), 1.1,
                    0.76, alpha=0.6, seed=sd())
            ring = m * smoothstep(0.8, 0.3, d)
            p.hatch(ring, f, ('sienna', 'brown', 'amber'), (10, 26), (1.4, 2.0), 1.2, 0.76, alpha=0.6, seed=sd())
            for lev in ((0.5, 0.72, 0.9) if kind != 'm' else (0.6,)):
                band = m * smoothstep(0.06, 0.0, np.abs(d - lev))
                p.hatch(band, f, ('brown', 'sienna'), (12, 30), (1.2, 1.6), 1.0, 0.72, alpha=0.5, seed=sd())
        # grooves between the scutes: soft dark pencil lines along the boundaries
        lines = [[P(np.linspace(0.015, 0.985, 60), np.full(60, V0))],
                 [P(np.linspace(cu[0] + tl[0] * 0.2, cu[-1] + tl[-1] * 0.2, 60), np.full(60, V1))]]
        lines = [l[0] for l in lines]
        for k in range(1, 12):
            lines.append(P(np.full(8, ub[k]), np.linspace(0.0, V0, 8)))
        for k in range(1, 4):
            vs = np.linspace(V0, V1, 12)
            lines.append(P(cu[k] + tl[k] * (vs - 0.4) + 0.05 * (vs - V0) * (V1 - vs) / 0.05, vs))
        for k in range(1, 3):
            vs = np.linspace(V1, 1.0, 10)
            lines.append(P(np.full(10, vu[k]), vs))
        for ln in lines:
            p.line(ln, 'sepia', 2.7, 0.8, 0.62, 0.3, seg=(40, 90), wobble=0.9, clip=self.shell, gaps=0.08, seed=sd())
            p.line(ln, 'umber', 1.8, 0.78, 0.55, 0.3, seg=(30, 70), wobble=1.3, clip=self.shell, gaps=0.15, seed=sd())
            p.line(ln + np.array([2.5, 2.5], np.float32), 'gold', 1.6, 0.66, 0.4, 0.55, seg=(30, 70), wobble=1.0,
                   clip=self.shell, gaps=0.3, seed=sd())            # a catch of light on the lip of each plate
        # the dome's shadow side: deeper and cooler
        p.hatch(self.shell * smoothstep(0.4, 0.95, 1 - sl), p.contour(self.shell, 40, fallback=-30),
                ('umber', 'sienna', 'violet'), (20, 46), (1.6, 2.3), 1.1, 0.78, alpha=0.55, seed=sd())
        p.hatch(self.shell * smoothstep(0.55, 1.0, 1 - sl) * 0.8, -30, ('violet', 'indigo', 'periwinkle'), (20, 46),
                (1.6, 2.3), 0.8, 0.74, alpha=0.45, seed=sd())
        # the rim of the shell overhangs: a band of shadow just inside the lower edge
        rimband = self.shell * smoothstep(0.08, 0.0, self.v_of_shell())
        p.hatch(rimband, 0, ('umber', 'sepia'), (14, 30), (1.5, 2.0), 1.2, 0.8, alpha=0.6, seed=sd())
        p.edge(self.shell, 'brown', density=0.7, where=0.4 + 0.6 * smoothstep(0.3, 0.8, 1 - sl), seed=sd())

        # the skin: neck across its wrinkles, the head round its form, legs with scales
        sk = ('lichen', 'sage', 'olive', 'umber')
        neck = self.neck * (1 - self.shell) * (1 - self.head)
        neckf = p.blend(np.full((H, W), np.deg2rad(86), np.float32), p.contour(self.neck, 8), 0.25)
        nl = p.shading(self.neck, LIGHT, 34)
        p.form(neck, sk, neckf, LIGHT, length=(12, 30), width=(1.5, 2.1), density=1.4, lit=nl, warm='butter',
               cool='lavender', seed=sd())
        xs = np.cumsum(self.r.uniform(13, 24, 9)) + 778
        for k, x0 in enumerate(xs):                                # loose folds across the neck, bowing forward
            if x0 > 930: break
            ty = np.interp(x0, [772, 812, 872, 936], [612, 618, 630, 640])
            by = np.interp(x0, [770, 806, 858, 936], [690, 716, 736, 748])
            bow = self.r.uniform(7, 13)
            top_y = ty + self.r.uniform(4, 16)
            pts = [(x0 + 3, top_y), (x0 - bow, (top_y + by) / 2), (x0 + 2, by - self.r.uniform(2, 10))]
            p.line(pts, 'umber', 1.9, 0.72, 0.62, 0.3, seg=(40, 90), wobble=0.5, clip=neck, seed=sd())
            p.line([(q[0] + 4.5, q[1]) for q in pts], 'cream', 1.5, 0.66, 0.4, 0.6, seg=(40, 90), clip=neck, seed=sd())
        for k in range(3):                                         # loose skin under the throat
            yy = 700 + 12 * k
            p.line([(784, yy - 8), (830, yy + 10), (880, yy + 16), (930, yy + 18)], 'umber', 1.5, 0.66, 0.5, 0.3,
                   seg=(40, 80), clip=neck, seed=sd())
        p.hatch(neck * smoothstep(690, 740, p.YY), 0, ('umber', 'violet'), (14, 30), (1.4, 2.0), 1.1, 0.78, alpha=0.6,
                seed=sd())
        hl = p.shading(self.head, LIGHT, 42)
        p.form(self.head, sk, p.contour(self.head, 14, fallback=10), LIGHT, length=(10, 26), width=(1.4, 2.0),
               density=1.5, lit=hl, warm='butter', cool='lavender', seed=sd())
        # the face: an old, gentle eye under a soft lid, a long closed smile, a nostril, warmth in the cheek
        ex, ey = EYE
        p.blush(ex - 10, ey + 34, 16, 'peach', 0.6, seed=sd())
        socket = p.ellipse(ex + 1, ey, 13, 11)
        p.hatch(socket * (1 - p.ellipse(ex, ey, 7, 7.5)), 30, ('olive', 'umber'), (5, 11), (1.2, 1.6), 1.2, 0.74,
                alpha=0.45, seed=sd())
        p.eye(ex, ey, 6.8, 'sepia', look=(-1.6, 1.4), seed=sd())
        p.line([(ex - 12, ey - 3), (ex - 4, ey - 9), (ex + 6, ey - 10), (ex + 15, ey - 5)], 'umber', 1.9, 0.74, 0.8,
               0.3, seg=(50, 60), wobble=0.2, seed=sd())                   # the lid
        p.line([(ex - 10, ey - 15), (ex + 2, ey - 19), (ex + 16, ey - 14)], 'olive', 1.4, 0.62, 0.6, 0.3,
               seg=(40, 50), wobble=0.3, seed=sd())                        # the brow fold above it
        p.line([(ex - 8, ey + 9), (ex + 3, ey + 12), (ex + 13, ey + 9)], 'olive', 1.3, 0.62, 0.6, 0.3, seg=(30, 40),
               wobble=0.2, seed=sd())
        p.line([(604, 670), (632, 682), (672, 688), (712, 684), (734, 676)], 'umber', 1.9, 0.74, 0.78, 0.3,
               seg=(40, 80), wobble=0.4, seed=sd())                        # mouth: a long, closed, slightly upturned line
        p.line([(734, 676), (742, 668)], 'umber', 1.5, 0.7, 0.6, 0.3, seg=(20, 30), seed=sd())
        p.hatch(p.ellipse(594, 634, 3.6, 2.6), 0, 'sepia', (3, 6), (1.3, 1.6), 3, 0.9, 0.5, seed=sd())
        for k in range(3):                                         # a few wrinkles under the eye and on the cheek
            p.line([(ex + 18 + 6 * k, ey + 14 + 3 * k), (ex + 30 + 6 * k, ey + 22 + 4 * k)], 'olive', 1.2, 0.6, 0.5,
                   0.3, seg=(20, 30), seed=sd())
        p.edge(self.head, 'umber', density=0.6, where=0.4 + 0.6 * smoothstep(0.3, 0.8, 1 - hl), seed=sd())
        # legs: scales, skin folds at the top where they come out from under the shell, wet near the water
        legs = self.near_legs
        ll = p.shading(legs, LIGHT, 40)
        p.form(legs, sk, 88, LIGHT, length=(14, 32), width=(1.5, 2.1), density=1.4, lit=ll, warm='butter',
               cool='lavender', seed=sd())
        p.scales(legs * smoothstep(WATER_T - 6, WATER_T - 36, p.YY), 20, ('olive', 'sage', 'lichen'), 'umber', 0,
                 LIGHT[:2], lit=ll, seed=sd())
        for (lx0, lx1, ly) in [(924, 1090, 708), (1494, 1652, 722)]:
            for k in range(3):
                yy = ly + 10 + 13 * k
                p.line([(lx0 + 10, yy + 6), ((lx0 + lx1) / 2, yy + 12 + self.r.normal(0, 2)), (lx1 - 8, yy + 4)],
                       'umber', 1.6, 0.66, 0.55, 0.3, seg=(40, 80), clip=legs, seed=sd())
        p.hatch(legs * smoothstep(WATER_T - 50, WATER_T, p.YY), 0, ('umber', 'teal'), (14, 30), (1.4, 2.0), 1.1, 0.76,
                alpha=0.55, seed=sd())
        p.edge(legs, 'umber', density=0.6, seed=sd())
        # the shell's shadow on the neck, legs and the plastron
        sh = blur(np.roll(self.shell, 14, 0), 22)
        shadow = np.clip(sh * 1.6, 0, 1) * (1 - self.shell) * np.clip(self.skin + self.plastron, 0, 1)
        p.hatch(shadow, 0, ('violet', 'umber', 'indigo'), (14, 30), (1.4, 2.0), 1.4, 0.78, alpha=0.62, seed=sd())

    def v_of_shell(self):
        """an approximate v (0 at the rim .. 1 at the top) for every pixel of the shell"""
        if not hasattr(self, '_v'):
            p = self.p
            ty = np.interp(p.XX[0], self.T[:, 0], self.T[:, 1])[None].repeat(H, 0)
            by = np.interp(p.XX[0], self.B[:, 0], self.B[:, 1])[None].repeat(H, 0)
            self._v = np.clip((by - p.YY) / np.maximum(1, by - ty), 0, 1).astype(np.float32)
        return self._v

    # ------------------------------------------------------------------ 6 the garden on its back
    def garden_phase(self):
        p = self.p
        sd = self.sd
        P = self.P
        # a mossy cap of rounded cushions along the top of the shell
        cush = []
        for k, u in enumerate(np.linspace(0.2, 0.82, 34)):          # the main band, overlapping
            for v, rr in ((self.r.uniform(0.95, 1.01), self.r.uniform(30, 42)), (self.r.uniform(0.86, 0.92), self.r.uniform(26, 38))):
                c = P(np.array([u + self.r.normal(0, 0.006)]), np.array([v]))[0]
                cush.append((c[0], c[1] - 4, rr, rr * self.r.uniform(0.6, 0.78), sd()))
        for k in range(26):                                          # a lumpy lower edge
            u = self.r.uniform(0.22, 0.8)
            c = P(np.array([u]), np.array([self.r.uniform(0.76, 0.84)]))[0]
            rr = self.r.uniform(14, 26)
            cush.append((c[0], c[1], rr, rr * self.r.uniform(0.6, 0.8), sd()))
        for k in range(9):                                           # a few loose ones further down
            u = self.r.uniform(0.25, 0.78)
            c = P(np.array([u]), np.array([self.r.uniform(0.62, 0.72)]))[0]
            rr = self.r.uniform(9, 16)
            cush.append((c[0], c[1], rr, rr * 0.7, sd()))
        cap = np.zeros((H, W), np.float32); clit = np.zeros_like(cap)
        for (cx, cy, rx, ry, s_) in sorted(cush, key=lambda c: c[1]):
            m = p.blob(cx, cy, rx, ry, 0.18, seed=s_)
            clit = clit * (1 - m) + p.shading(m, LIGHT, rx * 0.5) * m
            cap = np.maximum(cap, m)
        self.cap = cap
        glob_lit = p.shading(cap, LIGHT, 60)
        lit = np.clip(0.55 * clit + 0.45 * glob_lit, 0, 1)
        mf = p.blend(p.radial(1280, 560, 0, 12, 30), p.flow(-90, 30, 40), 0.3)
        p.pelt(cap, ('meadow', 'yellowgreen', 'moss', 'forest'), mf, LIGHT, length=(7, 15), density=1.2, lit=lit,
               seed=sd())
        # a few long locks of moss hanging over the shell below the cap
        locks = np.zeros((H, W), np.float32)
        for u in np.linspace(0.23, 0.8, 26) + self.r.normal(0, 0.006, 26):
            c = P(np.array([u]), np.array([self.r.uniform(0.74, 0.8)]))[0]
            locks = np.maximum(locks, p.ellipse(c[0], c[1] + 20, self.r.uniform(8, 12), self.r.uniform(18, 30)))
        locks = blur(locks, 2) * self.shell * (1 - cap * 0.6)
        self.locks = locks
        hf = p.flow(94, 8, 60)
        llit = p.shading(locks, LIGHT, 8)
        kw = dict(light=LIGHT[:2], spread=0.26, curl=0.08)
        p.fur(locks, hf, ('forest', 'pine', 'olive'), (20, 36), (1.0, 1.4), 1.0, (5, 9), pressure=0.82, seed=sd(), **kw)
        p.fur(locks, hf, ('moss', 'olive', 'grass'), (22, 40), (1.0, 1.4), 1.1, (5, 9), pressure=0.78, seed=sd(), **kw)
        p.fur(locks * smoothstep(0.4, 0.9, llit), hf, ('yellowgreen', 'meadow'), (14, 28), (1.0, 1.3), 0.8, (3, 6),
              opacity=0.5, seed=sd(), **kw)
        # the tree, the crooked lantern post, tufts of grass and wildflowers
        p.tree(TREE['x'], TREE['y'], TREE['h'], TREE['r'], ('lemon', 'gold', 'amber', 'sienna'), ('tan', 'brown', 'umber'),
               TREE['clumps'], (8, 16), LIGHT, TREE['lean'], seed=TREE['seed'])
        p.form(self.postm, ('brown', 'umber', 'sepia', 'sepia'), p.contour(self.postm, 2.5, fallback=90), LIGHT,
               cross=8, length=(10, 22), width=(1.3, 1.8), density=1.7, warm='ochre', seed=sd())
        for (kx, ky) in [(1085, 262), (1082, 218)]:                  # knots on the stick
            p.hatch(p.ellipse(kx, ky, 3.5, 2.5), 0, 'sepia', (3, 6), (1.2, 1.5), 3, 0.9, 0.5, seed=sd())
        tufts = cap * smoothstep(0.55, 0.75, noise2d(H, W, 26, 2, sd())) * smoothstep(0.3, 0.8, blur(cap, 6))
        p.grass(tufts, ('grass', 'yellowgreen', 'moss', 'meadow'), height=(14, 34), density=0.9, sway=20, seed=sd())
        for (u, n) in [(0.28, 9), (0.4, 7), (0.55, 10), (0.66, 8), (0.76, 6)]:
            c = P(np.array([u]), np.array([0.93]))[0]
            p.flowers(p.ellipse(c[0], c[1] - 10, 46, 18) * cap, ('daisy', 'buttercup', 'poppy', 'forgetmenot', 'pink'),
                      n=n, size=(5.0, 8.5), stems='moss', seed=sd())
        lx, ly, ls = LANTERN
        p.line([(POST[-1][0], POST[-1][1]), (lx, ly)], 'umber', 1.5, 0.75, 0.85, 0.4, seg=(30, 40))
        self.lantern_c = p.lantern(lx, ly, ls, seed=sd())

    # ------------------------------------------------------------------ 7 the child and the stepping stones
    def child_phase(self):
        p = self.p
        sd = self.sd
        for (cx, cy, rx, ry) in sorted(STONES, key=lambda s: s[1]):
            p.stone(cx, cy, rx, ry, moss=('moss', 'olive', 'grass') if rx > 45 else None, light=LIGHT,
                    avoid=self.childm if cy < CHILD['y'] + 20 else None, seed=sd())
        c = p.child(CHILD['x'], CHILD['y'], CHILD['h'], 1, look=(0.6, -0.8), light=LIGHT, seed=21)
        self.child_info = c
        hx, hy = c['hand']
        p.line([(hx, hy - 4), (hx + 2, hy + 8)], 'umber', 1.4, 0.7, 0.8, 0.4, seg=(30, 40))
        self.child_lc = p.lantern(hx + 2, hy + 8, 30, seed=sd())

    # ------------------------------------------------------------------ 8 reflections and ripples
    def reflection_phase(self):
        p = self.p
        sd = self.sd
        src = p.C.copy()
        av = np.clip(self.fg + self.childm + self.stones, 0, 1)
        # the tortoise's legs and underside, mirrored at the waterline
        reg = self.water * (p.YY > WATER_T) * (p.XX > 880) * (p.XX < 1700) * (1 - av)
        wl = np.full(W, float(WATER_T), np.float32)
        ys = np.clip(2 * WATER_T - p.YY, 0, H - 1).astype(int)
        refl_mask = self.tort[ys, p.XX.astype(int)] * reg
        refl_mask = blur(refl_mask, 3) * smoothstep(WATER_T + 150, WATER_T + 10, p.YY)
        p.reflect(wl, refl_mask, src=src, ripple=6, stretch=1.0, darken=0.3, tint='teal', mixw=0.22,
                  length=(20, 60), width=(1.6, 2.3), density=1.9, pressure=0.78, opacity=0.45, seed=sd())
        gap = (self.water * (p.XX > 1040) * (p.XX < 1560) * (p.YY > 760) * (p.YY < WATER_T + 70)).astype(np.float32)
        gap = blur(gap, 6) * (1 - self.tort) * (1 - av)
        dark = gap * smoothstep(WATER_T + 70, 790, p.YY)
        p.hatch(dark, p.flow(0, 3), ('slate', 'teal', 'indigo', 'violet'), (24, 60), (1.6, 2.3), 1.6, 0.8, alpha=0.7,
                seed=sd())
        p.hatch(dark * smoothstep(860, 790, p.YY), p.flow(0, 3), ('indigo', 'umber', 'violet'), (24, 60), (1.6, 2.3),
                1.2, 0.82, alpha=0.65, seed=sd())
        # the child and their stone
        cw = float(CHILD['y'] + 16)
        reg = self.water * (p.YY > cw) * (1 - av)
        ys = np.clip(2 * cw - p.YY, 0, H - 1).astype(int)
        cm = np.clip(self.childm + self.child_lantern, 0, 1)[ys, p.XX.astype(int)] * reg
        cm = blur(cm, 2.5) * smoothstep(cw + 120, cw + 5, p.YY)
        p.reflect(np.full(W, cw, np.float32), cm, src=src, ripple=5, stretch=1.0, darken=0.15, tint='teal', mixw=0.2,
                  length=(14, 40), width=(1.5, 2.1), density=1.6, pressure=0.74, opacity=0.45, seed=sd())
        # ripples where the legs meet the water and round the stones
        for (cx, rx) in [(996, 92), (1584, 86), (1206, 60), (1437, 54)]:
            p.ripples(cx, WATER_T + 4, rx, 11, 3, 'cream', 1.8, opacity=0.7, seed=sd())
            p.ripples(cx, WATER_T + 7, rx * 1.05, 12, 2, 'slate', 1.5, opacity=0.35, seed=sd())
        for (cx, cy, rx, ry) in STONES:
            p.ripples(cx, cy + ry * 0.55, rx * 1.12, ry * 0.5, 2, 'cream', 1.5, opacity=0.6, grow=1.25, seed=sd())

    # ------------------------------------------------------------------ 9 the lights and the near bank
    def lights_phase(self):
        p = self.p
        sd = self.sd
        # the low sun's warm rim on the left of the tortoise, the child and the tree
        bare = 1 - np.clip(self.cap + self.locks + self.crown + self.postm, 0, 1)
        for m, w in ((self.shell * bare, 18), (self.head, 10), (self.neck * (1 - self.shell), 10), (self.near_legs, 8),
                     (self.crown, 12), (self.cap, 8), (self.childm, 5)):
            inner = m * smoothstep(0.85, 0.3, blur(m, w))
            gy, gx = np.gradient(blur(m, w))
            side = smoothstep(0.0, 1.0, (0.82 * gx + 0.45 * gy) * w * 2.4)
            p.hatch(inner * side, p.contour(m, 4), ('glow', 'apricot', 'butter'), (10, 26), (1.4, 2.0), 1.2, 0.72,
                    opacity=0.62, alpha=0.75, seed=sd())
        # lanterns and windows
        lx, ly = self.lantern_c
        p.glow(lx, ly, 76, strength=0.8, halo=0.3, density=1.1, seed=sd())
        near = np.exp(-(((p.XX - lx) / 110) ** 2 + ((p.YY - ly - 90) / 70) ** 2))
        p.hatch(np.clip(self.cap + self.postm, 0, 1) * near, p.flow(-80, 30, 30), ('butter', 'glow', 'lemon'), (8, 18),
                (1.2, 1.7), 1.2, 0.72, opacity=0.55, alpha=0.7, seed=sd())
        cx, cy = self.child_lc
        p.glow(cx, cy, 60, strength=0.8, halo=0.3, density=1.1, seed=sd())
        # its light on the child's coat and on the stone and water below
        near = np.exp(-(((p.XX - cx) / 60) ** 2 + ((p.YY - cy) / 60) ** 2))
        p.hatch(self.childm * near, 90, ('glow', 'lemon'), (6, 14), (1.2, 1.6), 1.2, 0.72, opacity=0.6, alpha=0.7,
                seed=sd())
        m = p.ellipse(cx, 2 * (CHILD['y'] + 16) - cy, 14, 34) * self.water * (1 - self.stones)
        p.hatch(m, 0, ('lantern', 'glow', 'flame'), (6, 18), (1.5, 2.0), 1.4, 0.74, opacity=0.7, alpha=0.75, seed=sd())
        for (x, y, w, h, *_rest) in COTTAGES:
            p.glow(x + w * 0.36, y - h * 0.5, 34, strength=0.45, halo=0.22, density=0.8, length=(5, 12),
                   width=(1.2, 1.7), clip=1 - self.fg, seed=sd())
        # the near bank: grass, a few reeds, wildflowers
        bank = self.nearbank
        p.form(bank, ('meadow', 'yellowgreen', 'grass', 'moss'), p.flow(-8, 20, 120), LIGHT, length=(24, 54),
               density=1.3, lit=np.full((H, W), 0.55, np.float32) * (0.8 + 0.2 * noise2d(H, W, 150, 2, sd())),
               warm='butter', seed=sd())
        lump = smoothstep(0.35, 0.75, noise2d(H, W, 90, 2, sd()))
        p.grass(bank * (0.35 + 0.65 * lump), ('grass', 'leaf', 'yellowgreen', 'moss'), height=(24, 60), density=0.9,
                sway=18, seed=sd())
        p.grass(bank * lump, ('forest', 'moss', 'olive', 'leaf'), height=(40, 96), density=0.55, sway=22, seed=sd())
        corners = bank * np.clip(smoothstep(260, 0, p.XX) + smoothstep(1560, 1920, p.XX), 0, 1)
        p.grass(corners, ('moss', 'olive', 'yellowgreen', 'meadow'), height=(70, 150), density=0.45, sway=16,
                tuft=(3, 6), seed=sd())
        p.flowers(bank * smoothstep(0.3, 0.7, noise2d(H, W, 60, 2, sd())), ('daisy', 'buttercup', 'poppy',
                  'forgetmenot', 'daisy', 'pink'), n=90, size=(6.0, 11.0), stems='leaf', seed=sd())
        for (bx, by, br, s_) in [(70, 1030, 120, 401), (1858, 1010, 130, 402)]:
            crown = p.tree(bx, by + 40, 30, br, ('meadow', 'yellowgreen', 'grass', 'forest'), ('olive', 'umber', 'sepia'),
                           7, (8, 15), LIGHT, 0.0, branches=False, seed=s_)
            p.flowers(crown * smoothstep(0.4, 0.9, blur(crown, 10)), ('daisy', 'pink', 'buttercup', 'daisy'), n=26,
                      size=(5.0, 8.0), seed=sd())


PHASES = (('sky', 'sky_phase'), ('land', 'land_phase'), ('stream', 'water_phase'), ('tortoise', 'tortoise_base'),
          ('modelling', 'tortoise_model'), ('garden', 'garden_phase'), ('child', 'child_phase'),
          ('reflections', 'reflection_phase'), ('lights', 'lights_phase'))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'pencilbook_tortoise_crossing.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:12s} {time.time() - T0:5.1f}s')) if os.environ.get('PB_TIMING') else (lambda n: None)
    p = PencilStorybook(W, H, seed=8, keep_stages=bool(stages), stages_dir=stages)
    p.finish()
    p.paper()
    p.stage('paper')
    sc = Scene(p)
    tick('setup')
    for name, ph in PHASES[:-1]:
        getattr(sc, ph)()
        tick(name)
        p.stage(name)
    getattr(sc, PHASES[-1][1])()
    tick(PHASES[-1][0])
    p.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out, f'{time.time() - T0:.1f}s', p.n_strokes, 'strokes')


if __name__ == '__main__':
    main()
