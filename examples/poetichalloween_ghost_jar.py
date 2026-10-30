"""Example (poetic halloween): 罐子里的小幽灵 · The Ghost in the Jar -- a melancholic, surreal picture-book portrait
for an autumn night.

The last night of October. A pale child with a blunt jet-black bob and a dead-straight fringe, under a slouchy
burlap cloche with a frayed brim and a twine band, stands in a dark hedge of leaves. In her oxblood mittens she
holds a glass jar tied with a burlap cover; inside it a tiny sheet-ghost glows, and she looks down at it with heavy,
half-closed eyes that mirror its light. Its glow warms the wool, the glass and the underside of her face. More little
ghosts peer out of the hedge and float in the starry indigo sky, watching. Porcelain skin flushed red round the eyes,
on the nose and the cheeks; a chunky knit scarf up to the chin, a dark tartan coat with two horn buttons, a fine
printed grain over everything.

Painted in the order an illustrator works on a dark board: the board -> a chalk underdrawing -> the night sky and
stars -> the dark hedge -> flat colour -> simplified volumes (the porcelain face, the sculpted bob and its sheen) ->
the textiles (burlap, tartan, knit) -> the face (eyes, flush, nose, mouth) -> the jar and the ghosts, whose light
then warms everything near them -> the leaves in front, loose fibres and the last touches. --stages writes those
steps as snapshots for the draw-on. No image model.
python3 poetichalloween_ghost_jar.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from core import blur, smoothstep, noise2d
from poetichalloween import PoeticHalloween

W, H = 1920, 1080
HC = np.array([880.0, 500.0])            # centre of her face (between the eyes)
TILT_D = -5.0                            # head tilted toward her right shoulder, looking down
TILT = np.deg2rad(TILT_D)
CS, SN = np.cos(TILT), np.sin(TILT)
JAR = dict(cx=884.0, top=726.0, bot=930.0, neck=56.0, half=74.0)
GHOST = dict(cx=884.0, top=782.0, w=96.0, h=118.0)            # the one in the jar
OTHERS = [dict(cx=1490.0, top=318.0, w=122.0, h=168.0, look=(-1.0, 0.2), lean=4.0),
          dict(cx=1716.0, top=176.0, w=78.0, h=108.0, look=(-0.8, 0.4), lean=-3.0),
          dict(cx=1296.0, top=566.0, w=92.0, h=126.0, look=(-1.0, -0.2), lean=0.0),
          dict(cx=326.0, top=366.0, w=96.0, h=132.0, look=(1.0, 0.3), lean=-4.0),
          dict(cx=118.0, top=616.0, w=72.0, h=98.0, look=(1.0, 0.0), lean=3.0)]


def F(u, v):
    """face-local (u right, v down, before the tilt) -> canvas"""
    return (HC[0] + u * CS - v * SN, HC[1] + u * SN + v * CS)


def FL(pts):
    return [F(u, v) for u, v in pts]


def to_local(x, y):
    dx, dy = x - HC[0], y - HC[1]
    return dx * CS + dy * SN, -dx * SN + dy * CS


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
        # the face: a child's soft oval turned a little to the viewer's left (features shifted, chin off-centre)
        self.face_pts = [(-106, -140), (-116, -80), (-120, -20), (-117, 34), (-106, 80), (-86, 116), (-56, 141),
                         (-20, 152), (18, 149), (56, 134), (92, 104), (116, 60), (128, 4), (129, -70), (120, -140)]
        self.face = p.poly(FL(self.face_pts), smooth=True)
        # the bob: one solid mass from under the hat to a blunt cut at the jaw; the far-side curtain falls in
        # front of the far cheek, the near side shows behind the near cheek
        self.bob = p.poly(FL([(-176, -150), (-186, -70), (-190, 0), (-184, 64), (-172, 108), (-158, 134),
                              (-126, 142), (-96, 138), (-60, 156), (60, 160), (110, 152), (150, 154), (178, 140),
                              (192, 90), (198, 20), (196, -60), (188, -150)]), smooth=True)
        self.curtain_l = p.poly(FL([(-160, -60), (-186, -40), (-190, 0), (-184, 64), (-172, 108), (-158, 134),
                                    (-126, 142), (-96, 138), (-86, 120), (-96, 86), (-106, 40), (-110, 0),
                                    (-112, -36), (-140, -48)]), smooth=True)
        # the fringe: dead straight across, just above the eyes
        self.fringe = p.poly(FL([(-172, -160), (178, -160), (188, -100), (172, -36), (-124, -36), (-176, -80)]))
        # the hat: a slouchy burlap cloche pulled down to the fringe -- a soft lopsided crown, a short brim that
        # turns down and frays at its edge, a twine band
        self.brim_pts = [(-216, -80), (-202, -110), (-150, -126), (-60, -134), (40, -134), (140, -126), (204, -110),
                         (226, -78), (212, -68), (150, -82), (60, -90), (-40, -90), (-140, -82), (-202, -68)]
        self.brim = p.poly(FL(self.brim_pts), smooth=True)
        self.brim_path = FL([(-206, -88), (-150, -104), (-50, -112), (50, -112), (150, -104), (214, -88)])
        self.crown_pts = [(-172, -112), (-178, -164), (-166, -216), (-134, -258), (-84, -284), (-24, -290),
                          (30, -284), (86, -270), (132, -244), (162, -204), (176, -158), (178, -112)]
        self.crown = p.poly(FL(self.crown_pts), smooth=True)
        self.band_path = FL([(-176, -128), (-120, -138), (-40, -142), (40, -142), (120, -138), (178, -128)])
        self.hat = np.clip(self.brim + self.crown, 0, 1)
        # the coat: a child's narrow shoulders, two sleeves that bend in to the jar
        coat = p.poly([(784, 700), (706, 718), (634, 752), (594, 808), (572, 900), (562, 1080), (1200, 1080),
                       (1190, 900), (1168, 808), (1128, 752), (1056, 718), (978, 700)])
        sw = [136, 140, 132, 112, 92]
        self.sleeves = np.clip(p.tube([(606, 808), (612, 914), (660, 976), (730, 966), (788, 942)], sw) +
                               p.tube([(1160, 808), (1154, 914), (1108, 976), (1038, 966), (980, 942)], sw), 0, 1)
        self.coat = np.clip(coat + self.sleeves, 0, 1)
        # the scarf: a thick roll up to the chin, one end hanging down the front
        self.scarf_path = [(744, 676), (806, 706), (880, 718), (956, 706), (1018, 676)]
        self.scarf_roll = p.tube(self.scarf_path, [70, 80, 86, 80, 70])
        self.end_path = [(808, 712), (792, 790), (778, 870), (772, 940)]
        self.scarf_end = p.tube(self.end_path, [80, 78, 76, 74])
        self.scarf = np.clip(self.scarf_roll + self.scarf_end, 0, 1)
        # the jar: a neck, round shoulders, a straight body; a burlap cover tied over its mouth
        j = JAR
        cx, t, b, nk, hf = j['cx'], j['top'], j['bot'], j['neck'], j['half']
        self.jar = p.poly([(cx - nk, t + 2), (cx + nk, t + 2), (cx + nk + 2, t + 20), (cx + hf - 4, t + 34),
                           (cx + hf, t + 50), (cx + hf, b - 18), (cx + hf - 8, b - 4), (cx, b), (cx - hf + 8, b - 4),
                           (cx - hf, b - 18), (cx - hf, t + 50), (cx - hf + 4, t + 34), (cx - nk - 2, t + 20)],
                          smooth=True)
        r = np.random.default_rng(3)
        hem = [(cx + 62 - k * 124 / 10, t + 28 + (6 if k % 2 else 0) + r.uniform(-3, 3)) for k in range(11)]
        self.cover = p.poly([(cx - 62, t + 22), (cx - 58, t - 4), (cx - 34, t - 20), (cx, t - 26), (cx + 34, t - 20),
                             (cx + 58, t - 4), (cx + 62, t + 22)] + hem, smooth=False)
        self.cover = p.soften(self.cover, 0.8)
        # mittens holding the jar from the sides, thumbs over the front; ribbed cuffs at the wrists
        self.mitt_l = np.maximum(p.ellipse(816, 884, 34, 50, 12), p.ellipse(840, 852, 11, 21, 35))
        self.mitt_r = np.maximum(p.ellipse(952, 884, 34, 50, -12), p.ellipse(928, 852, 11, 21, -35))
        self.mittens = np.clip(self.mitt_l + self.mitt_r, 0, 1)
        self.cuff_l = p.tube([(804, 926), (784, 948)], 46) * (1 - self.mittens)
        self.cuff_r = p.tube([(964, 926), (984, 948)], 46) * (1 - self.mittens)
        self.cuffs = np.clip(self.cuff_l + self.cuff_r, 0, 1)
        # the hedge behind her
        self.hedge_line = ([0, 160, 330, 470, 600, 760, 1000, 1180, 1300, 1450, 1620, 1780, 1920],
                           [520, 470, 500, 560, 610, 640, 650, 600, 520, 470, 430, 452, 470])
        self.hedge = p.below(*self.hedge_line)
        # visible parts (front to back)
        hands = np.clip(self.mittens + self.cuffs, 0, 1)
        self.v_hands = hands
        self.v_jar = self.jar * (1 - hands)
        self.v_cover = self.cover * (1 - hands)
        jar_all = np.clip(self.jar + self.cover, 0, 1)
        self.v_sleeves = self.sleeves * (1 - hands)
        self.v_scarf = self.scarf * (1 - hands) * (1 - self.sleeves) * (1 - jar_all)
        self.v_coat = self.coat * (1 - self.scarf) * (1 - hands) * (1 - self.sleeves) * (1 - jar_all)
        self.v_fringe = self.fringe * (1 - self.hat)
        self.v_face = self.face * (1 - self.fringe) * (1 - self.curtain_l) * (1 - self.hat) * (1 - self.scarf)
        self.v_curtain = self.curtain_l * (1 - self.hat) * (1 - self.fringe) * (1 - self.scarf)
        self.v_bob = self.bob * (1 - self.face) * (1 - self.hat) * (1 - self.fringe) * (1 - self.curtain_l) * \
            (1 - self.scarf) * (1 - self.coat)
        self.hair = np.clip(self.v_bob + self.v_curtain + self.v_fringe, 0, 1)
        self.figure = np.clip(self.hat + self.bob + self.face + self.coat + self.scarf + hands + jar_all, 0, 1)

    # ------------------------------------------------------------------ hair flow (degrees)
    def hair_flow(self, x, y):
        x = np.asarray(x, np.float32); y = np.asarray(y, np.float32)
        u, v = to_local(x, y)
        turn = 22 * smoothstep(70, 150, v) * np.where(u < 0, -1, 1)       # ends turned under, toward the neck
        fringe = (v > -160) & (v < -30) & (np.abs(u) < 172)
        a = np.where(fringe, 90.0, 90 + turn + 6 * np.clip(u / 180, -1, 1))
        return a + TILT_D

    # ------------------------------------------------------------------ 1. chalk underdrawing
    def sketch(self):
        p = self.p
        r = np.random.default_rng(5)
        sk = lambda pts, a=0.42, w=2.0, **kw: p.sketch(pts, 'chalk', w, a, seed=int(r.integers(1 << 30)), **kw)
        sk(FL(self.face_pts[1:-1]))
        sk(FL([(-176, -150), (-190, 0), (-172, 108), (-126, 142), (-86, 112)]))
        sk(FL([(188, -150), (198, 20), (178, 140), (110, 152)]))
        sk(FL([(-124, -36), (172, -36)]), smooth=False)
        sk(FL(self.brim_pts[:8]))
        sk(FL(self.crown_pts))
        sk(FL([(-54 - 32, 6), (-54 + 32, 2)]), 0.28, smooth=False)
        sk(FL([(46 - 36, 4), (46 + 36, 0)]), 0.28, smooth=False)
        sk(FL([(-4, -4), (-8, 28), (-14, 54), (-22, 76)]), 0.25)
        sk([(634, 752), (594, 808), (572, 900), (562, 1080)]); sk([(1128, 752), (1168, 808), (1190, 900), (1200, 1080)])
        sk(self.scarf_path, 0.28); sk([(788, 942), (660, 976), (612, 914)]); sk([(980, 942), (1108, 976), (1154, 914)])
        j = JAR
        sk([(j['cx'] - j['neck'], j['top']), (j['cx'] - j['half'], j['top'] + 50), (j['cx'] - j['half'], j['bot'] - 18),
            (j['cx'], j['bot']), (j['cx'] + j['half'], j['bot'] - 18), (j['cx'] + j['half'], j['top'] + 50),
            (j['cx'] + j['neck'], j['top'])], 0.3)
        for (cx, cy, rx, ry, rot) in ((816, 884, 34, 50, 12), (952, 884, 34, 50, -12)):
            t = np.linspace(0, 2 * np.pi, 30)
            c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
            sk([(cx + rx * np.cos(a) * c - ry * np.sin(a) * s, cy + rx * np.cos(a) * s + ry * np.sin(a) * c)
                for a in t], 0.25)
        for g in [GHOST] + OTHERS:
            cx, top, w, h = g['cx'], g['top'], g['w'], g['h']
            R = w / 2
            t = np.linspace(np.pi, 2 * np.pi, 14)
            sk([(cx - R * 1.08, top + h * 0.95)] + [(cx + R * np.cos(a), top + R + R * np.sin(a)) for a in t] +
               [(cx + R * 1.08, top + h * 0.95)], 0.22, 1.3)
        xs, ys = self.hedge_line
        sk(list(zip(xs[:5], ys[:5])), 0.18); sk(list(zip(xs[7:], ys[7:])), 0.18)

    # ------------------------------------------------------------------ 2. night sky
    def sky(self):
        p = self.p
        val = p.value(0.15, 0.85, 0, 760, mottle=0.06, scale=260, seed=21)
        p.wash(p.rect(0, 0, W, H), ('night', val), 1.0, grain=0.3, edge=0)
        # a faint haze low over the hedge on the right, a hint of violet on the left
        p.glaze(p.spot(1500, 380, 700, 260, solid=0.0), 'haze', 0.22, 'screen')
        p.glaze(p.spot(300, 360, 520, 220, solid=0.0), 'dusk', 0.18, 'screen')
        # the painterly hand: fine diagonal strokes over the whole sky, colours from the sky under them
        fl = p.flow(-14, 8, 300, seed=22)
        p.strokes(p.rect(0, 0, W, 760), fl, 'canvas', (50, 120), (2.5, 4.5), 1.1, pressure=0.7, alpha=0.55,
                  value=0.07, hue=0.03, streak=0.4, soft=0.6, seed=23)
        p.strokes(p.rect(0, 0, W, 760), fl, ('night', val * 1.1 + 0.05), (30, 80), (1.5, 2.5), 0.5, pressure=0.6,
                  alpha=0.3, value=0.1, seed=24)
        keep = 1 - p.soften(self.figure, 12)
        p.stars(p.rect(0, 0, W, 560) * keep * smoothstep(620, 360, p.YY), 260, (0.5, 1.4), bright=0.07, seed=25)
        # a thin drift of small stars across the upper right
        band = np.exp(-((p.YY - (40 + 0.26 * (p.XX - 1000))) / 70.0) ** 2) * (p.XX > 1050)
        p.stars(band * keep, 220, (0.4, 0.9), bright=0.02, seed=26)

    # ------------------------------------------------------------------ 3. the dark hedge
    def hedge_leaves(self):
        p = self.p
        hm = self.hedge
        p.wash(hm, ('leaf', p.value(0.25, 0.05, 420, 1080, seed=31)), 1.0, grain=0.3, edge=0.6)
        reg = blur(hm, 18) * (1 - 0.92 * p.soften(self.figure, 4))
        greens = ('leaf', 'leaf', 'leaf_olive', 'leaf')
        p.foliage(reg, 270, (70, 130), greens, (0.04, 0.3), veins=0.28, seed=32)
        p.foliage(reg, 240, (80, 140), greens + greens + ('leaf_maroon', 'leaf_rust'), (0.08, 0.42), veins=0.32,
                  seed=33)
        # the leaves along the top edge of the hedge, against the sky
        xs, ys = self.hedge_line
        yl = np.interp(np.arange(W, dtype=np.float32), xs, ys)
        top = smoothstep(60, 0, np.abs(p.YY - yl[None])) * (1 - p.soften(self.figure, 6))
        p.foliage(top, 90, (70, 120), greens, (0.14, 0.45), veins=0.32, seed=34)
        # a painterly pass: short strokes in the colour under them
        p.strokes(hm * (1 - self.figure), p.flow(60, 60, 90, seed=35), 'canvas', (16, 36), (2.0, 3.5), 0.6,
                  pressure=0.66, alpha=0.4, value=0.1, hue=0.04, seed=36)

    # ------------------------------------------------------------------ 4. flat colour
    def block(self):
        p = self.p
        p.wash(self.v_coat + self.v_sleeves, 'navy', 1.0, grain=0.3, edge=0.3)
        p.wash(self.hair, 'hair_black', 1.0, grain=0.15, edge=0.3)
        p.wash(self.v_face, 'porcelain', 1.0, grain=0.15, edge=0.3)
        p.wash(self.v_scarf, 'oxblood', 1.0, grain=0.25, edge=0.5)
        p.wash(self.v_hands, 'oxblood', 1.0, grain=0.25, edge=0.5)
        p.wash(self.v_jar, '#1d2a33', 0.55, grain=0.2, edge=0.3)
        p.wash(self.v_cover, 'burlap', 1.0, grain=0.3, edge=0.6)
        p.wash(self.hat, 'burlap_dark', 1.0, grain=0.3, edge=0.6)

    # ------------------------------------------------------------------ 5. simplified volumes
    def model(self):
        p = self.p
        # porcelain face: a soft dome, cool grey-mauve on the shadow side, the fringe's shadow on the brow
        face_r = ('#9c8790', '#bca9ae', '#d8cac8', '#ece2dd', '#f8f2ee')
        self.face_lit = p.model(self.v_face, face_r, light=(-0.8, -0.4, 0.45), sigma=84, lo=0.0, hi=1.0,
                                gamma=0.9, grain=0.12, edge=0.3, mottle=0.04)
        p.glaze(np.maximum(p.spot(*F(60, 58), 84, 60, TILT_D, solid=0.0), p.spot(*F(-78, 54), 48, 54, TILT_D, solid=0.0))
                * self.v_face, '#f0c9bd', 0.35, 'multiply')
        p.glaze(p.soften(self.fringe, 10) * self.v_face, '#b39fa8', 0.5, 'multiply')
        rim = (1 - smoothstep(0.35, 0.95, p.soften(self.face, 16))) * self.v_face
        p.glaze(rim, '#c2adb5', 0.6, 'multiply')
        sockets = np.maximum(p.spot(*F(-54, -6), 52, 32, TILT_D, solid=0.1), p.spot(*F(46, -8), 58, 34, TILT_D, solid=0.1))
        p.glaze(sockets * self.v_face, '#cbb6bd', 0.5, 'multiply')
        p.glaze(p.spot(*F(78, 66), 52, 46, TILT_D, solid=0.0) * self.v_face, '#d0bfc4', 0.35, 'multiply')
        p.glaze(p.spot(*F(-20, 132), 34, 14, TILT_D, solid=0.0) * self.v_face, '#bfa8b1', 0.4, 'multiply')
        p.glaze(p.spot(*F(-70, 40), 40, 30, TILT_D, solid=0.0) * self.v_face, '#ffffff', 0.25, 'screen')
        p.glaze(p.soften(self.scarf, 9) * self.v_face * (1 - self.scarf), '#7a6470', 0.5, 'multiply')
        p.strokes(self.v_face, p.contour(self.face, 24, fallback=80), 'canvas', (24, 50), (3, 5), 0.6,
                  pressure=0.6, opacity=0.95, alpha=0.35, value=0.03, streak=0.3, clip=self.v_face, seed=41)
        # the bob: one sculpted mass lit as a whole, a sheen band, a whisper of strands
        hm = np.clip(self.bob + self.fringe + self.curtain_l, 0, 1)
        lit = p.shading(hm, sigma=80)
        self.hair_lit = lit
        p.model(self.hair, 'hair', lit=lit, lo=0.0, hi=0.66, grain=0.15, edge=0.3)
        # where the far curtain turns away along the cheek, and the hat's shadow on the hair
        inner = p.soften(self.curtain_l, 7) * (1 - p.soften(self.curtain_l, 7)) * 4 * self.v_curtain * \
            smoothstep(0.02, 0.2, p.soften(self.face, 14))
        p.glaze(inner, '#000000', 0.5, 'normal')
        p.glaze(p.soften(self.hat, 14) * self.hair * (1 - self.hat), '#000000', 0.5, 'normal')
        fld = self.hair_flow
        p.sheen(self.hair, fld, lit, band=(0.5, 0.66, 0.8), colour='hair_sheen', alpha=0.45, strokes=0.25, seed=42)
        # the fringe curves forward under the hat: a soft band of sheen across its upper part
        u_, v_ = to_local(p.XX, p.YY)
        fb = self.v_fringe * smoothstep(-84, -66, v_) * smoothstep(-36, -58, v_)
        p.sheen(self.v_fringe, fld, 0.5 + 0.3 * fb, band=(0.55, 0.8, 0.95), colour='hair_shine', alpha=0.45,
                strokes=0.4, seed=47)
        del u_, v_
        cols = ('jet', 'hair_black', 'hair_dark', 'hair')
        p.strands(np.clip(self.v_bob + self.v_curtain, 0, 1), fld, cols, n=500, length=(60, 160), width=(1.0, 1.6),
                  shade=lit, spread=0.25, alpha=0.3, lock=(10, 6), seed=45)
        p.strands(self.v_fringe, fld, ('jet', 'hair_dark', 'hair', 'hair_sheen'), n=320, length=(30, 70),
                  width=(0.9, 1.4), shade=0.25 + 0.5 * fb, spread=0.3, alpha=0.4, seed=46)
        # the coat and sleeves: a dark under-colour lit from the upper left (the tartan goes on in the next step)
        self.coat_lit = np.clip(p.shading(self.coat, sigma=80) * (1 - self.sleeves) +
                                p.shading(self.sleeves, sigma=30) * self.sleeves, 0, 1)
        p.model(self.v_coat + self.v_sleeves, ('#0b0e19', '#141a2c', '#1d2539', '#2a3349', '#3a4459'),
                lit=self.coat_lit, grain=0.3, edge=0.3)
        # wool: oxblood, rounded
        p.model(self.v_scarf, 'oxblood', sigma=22, lo=0.05, hi=0.68, grain=0.25, edge=0.5)
        p.model(self.mitt_l, 'oxblood', sigma=18, lo=0.05, hi=0.7, grain=0.25, edge=0.5)
        p.model(self.mitt_r * (1 - self.mitt_l), 'oxblood', sigma=18, lo=0.05, hi=0.7, grain=0.25, edge=0.5)
        p.model(self.cuffs, 'oxblood', sigma=10, lo=0.05, hi=0.7, grain=0.25, edge=0.5)
        # burlap hat: a modelled crown, the brim darker underneath, the brim's shadow on the crown; the jar's cover
        hat_r = ('#0d0b0b', '#171312', '#221c19', '#2f2722', '#43372f')
        p.model(self.crown * (1 - self.brim), hat_r, sigma=50, lo=0.08, hi=1.0, grain=0.3, edge=0.5)
        p.model(self.brim, hat_r, sigma=14, lo=0.05, hi=0.85, grain=0.3, edge=0.5)
        p.model(self.v_cover, 'burlap', sigma=14, lo=0.15, hi=1.0, grain=0.3, edge=0.5)

    # ------------------------------------------------------------------ 6. textiles
    def cloth(self):
        p = self.p
        # burlap on the hat (the brim woven along its curve) and on the jar's cover
        p.burlap(self.crown * (1 - self.brim), angle=TILT_D - 3, period=6.4, strength=0.8, seed=51)
        bs, bt = p.along(self.brim_path, self.brim)
        p.burlap(self.brim, coords=(bs, bt), period=6.0, strength=0.8, seed=53)
        del bs, bt
        p.burlap(self.v_cover, angle=4, period=5.0, strength=0.8, seed=54)
        # a soft dent and two creases in the crown, a twine band with a small bow on the side
        for pts in ([(-100, -262), (-40, -270), (10, -266)], [(-130, -170), (-112, -224)], [(96, -180), (118, -236)]):
            p.line(FL(pts), 3.0, '#060505', 0.4, taper=(0.5, 0.5))
        p.line(self.band_path, 4.0, '#9a8060', 0.95, taper=(0.05, 0.05))
        p.line([(x, y + 5) for x, y in self.band_path], 3.4, '#6f5a42', 0.9, taper=(0.05, 0.05))
        bx, by = F(128, -134)
        for sg in (-1, 1):
            p.line([(bx, by), (bx + sg * 16, by - 12), (bx + sg * 26, by - 4), (bx + sg * 14, by + 3), (bx, by)], 3.0,
                   '#9a8060', 0.95, taper=(0.2, 0.2))
        p.line([(bx, by), (bx + 4, by + 22), (bx + 2, by + 38)], 2.8, '#87704f', 0.9, taper=(0.1, 0.6))
        p.line([(bx, by), (bx + 12, by + 18), (bx + 16, by + 32)], 2.8, '#87704f', 0.9, taper=(0.1, 0.6))
        # the frayed edge of the brim: loose threads hanging from it
        edge = np.zeros((H, W), np.float32)
        for uu in np.linspace(-200, 210, 240):
            x, y = F(uu, -72 - 12 * (1 - (uu / 215) ** 2))
            edge[int(y) - 1:int(y) + 2, int(x) - 1:int(x) + 2] = 1
        p.strands(self.brim, 90 + TILT_D, ('burlap', 'burlap_light', 'burlap_hi'), n=260, length=(6, 20),
                  width=(0.7, 1.2), roots=edge, clip=False, curl=3, jitter=14, alpha=0.75, seed=57)
        del edge
        p.fuzz(self.hat, (5, 16), n=900, width=(0.7, 1.1), out=0.65, alpha=0.6, lift=0.4, curl=20, seed=55)
        p.fuzz(self.v_cover, (3, 9), n=240, width=(0.6, 1.0), out=0.6, alpha=0.6, lift=0.3, curl=20, seed=56)
        # tartan coat: a dark sett with thin rust and ochre lines, checks wobbling with the folds
        sett = [('navy', 14), ('tar', 3), ('bottle', 12), ('tar', 2), ('#6a2c1c', 2), ('tar', 2), ('bottle', 12),
                ('tar', 3), ('#806232', 1)]
        nu = (noise2d(H, W, 140, 3, 61) - 0.5) * 16; nv = (noise2d(H, W, 140, 3, 62) - 0.5) * 16
        U = p.XX + nu; V = p.YY + nv + 0.05 * (p.XX - 880) ** 2 / 40
        p.tartan(self.v_coat, sett, 2.6, coords=(U, V), lit=self.coat_lit, lo=0.28, hi=1.15, seed=63)
        for (sm, ang) in ((self.v_sleeves * (p.XX < 880), -34), (self.v_sleeves * (p.XX >= 880), 34)):
            a = np.deg2rad(ang)
            Us = (p.XX * np.cos(a) + p.YY * np.sin(a)) + nu; Vs = (-p.XX * np.sin(a) + p.YY * np.cos(a)) + nv
            p.tartan(sm, sett, 2.6, coords=(Us, Vs), lit=self.coat_lit, lo=0.22, hi=1.2, seed=64)
        del nu, nv, U, V
        # folds and shadows: the crease inside each elbow, the scarf's and the sleeves' shadow on the coat
        folds = np.maximum.reduce([p.tube([(640, 904), (676, 944), (722, 938)], 16),
                                   p.tube([(1124, 904), (1090, 944), (1044, 938)], 16)])
        p.glaze(p.soften(folds, 8) * self.coat, '#05060a', 0.5, 'normal')
        p.glaze(p.soften(np.roll(self.scarf, 18, axis=0), 14) * self.v_coat, '#05060a', 0.45, 'normal')
        # the arms in front of the body: the coat darkens round them, each sleeve darkens at its edges and catches
        # a little light along its top
        edge = p.soften(self.sleeves, 13)
        p.glaze(np.clip(edge * 2.2, 0, 1) * (1 - self.sleeves) * self.v_coat, '#04050a', 0.62, 'normal')
        p.glaze((1 - smoothstep(0.55, 0.97, p.soften(self.sleeves, 7))) * self.v_sleeves, '#04050a', 0.5, 'normal')
        top = self.v_sleeves * (1 - smoothstep(0.0, 1.0, np.clip(np.roll(p.soften(self.sleeves, 6), -16, axis=0), 0, 1)))
        forearms = np.maximum(p.spot(724, 948, 90, 50, solid=0.4), p.spot(1044, 948, 90, 50, solid=0.4))
        p.glaze(top * forearms, '#6c7894', 0.45, 'screen')
        # the coat's front edge and two horn buttons below the jar
        p.line([(904, 940), (910, 1000), (914, 1080)], 3.0, '#05060a', 0.7, taper=(0.1, 0.1))
        p.glaze(p.soften(p.tube([(916, 940), (922, 1080)], 10), 4) * self.v_coat, '#05060a', 0.35, 'normal')
        for (bx, by) in ((928, 978), (932, 1042)):
            p.dab(bx + 1, by + 4, 17, '#05050a', 0.5, soft=0.8)
            p.dab(bx, by, 15, '#3a281f', 1.0, soft=0.2)
            p.dab(bx - 1, by - 1, 11, '#58402f', 0.9, soft=0.5)
            p.dab(bx - 6, by - 6, 3.2, '#c0a185', 0.8, soft=0.4)
            for dx, dy in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
                p.dab(bx + dx, by + dy, 1.8, '#140d0a', 0.9, soft=0.3)
        fld = p.blend(p.flow(92, 8, 200, seed=65), p.contour(self.sleeves, 26, fallback=90), self.sleeves)
        p.strokes(self.v_coat + self.v_sleeves, fld, 'canvas', (30, 70), (2.0, 3.2), 0.7, pressure=0.62, alpha=0.35,
                  value=0.08, hue=0.03, streak=0.4, seed=66)
        # chunky knit: the scarf roll along its path, the hanging end down its own, mittens; ribbed cuffs
        p.knit(self.scarf_roll * self.v_scarf, (17, 12), path=self.scarf_path, strength=0.85, seed=67)
        p.knit(self.scarf_end * (1 - self.scarf_roll) * self.v_scarf, (17, 12), angle=-8, origin=(790, 800),
               strength=0.85, seed=68)
        p.knit(self.mitt_l, (13, 10), angle=14, origin=(826, 848), curve=0.5, strength=0.85, seed=69)
        p.knit(self.mitt_r * (1 - self.mitt_l), (13, 10), angle=-14, origin=(942, 848), curve=0.5, strength=0.85,
               seed=70)
        p.rib(self.cuff_l, [(780, 922), (806, 898)], 7.0)
        p.rib(self.cuff_r, [(962, 898), (988, 922)], 7.0)
        p.glaze(p.soften(np.roll(self.scarf_roll, 10, axis=0), 6) * self.scarf_end * (1 - self.scarf_roll), '#160406', 0.45,
                'normal')
        p.fuzz(self.v_scarf, (5, 12), n=800, width=(0.7, 1.1), out=0.6, alpha=0.55, lift=0.18, seed=71)
        p.fuzz(self.mittens, (4, 10), n=420, width=(0.7, 1.1), out=0.6, alpha=0.55, lift=0.18, seed=72)

    # ------------------------------------------------------------------ 7. the face
    def features(self):
        p = self.p
        vf = self.v_face
        # the red flush: a band under and round the eyes running over the bridge, the cheeks, a little on the chin
        core = np.maximum.reduce([
            p.spot(*F(-54, 24), 44, 24, TILT_D, solid=0.25), p.spot(*F(46, 22), 52, 26, TILT_D, solid=0.25),
            p.spot(*F(-4, 20), 26, 16, TILT_D, solid=0.0) * 0.7,
            p.ring(*F(-54, 4), 34, 21, 16, TILT_D, below=0.5) * 0.85,
            p.ring(*F(46, 2), 39, 23, 18, TILT_D, below=0.5) * 0.85])
        p.flush(core * vf, 'flush', 0.62, speckle=0.3)
        wide = np.maximum.reduce([p.spot(*F(60, 56), 76, 56, TILT_D, solid=0.0),
                                  p.spot(*F(-80, 56), 44, 52, TILT_D, solid=0.0),
                                  p.spot(*F(-14, 140), 30, 14, TILT_D, solid=0.0) * 0.6])
        p.flush(wide * vf, 'flush_light', 0.4, speckle=0.85)
        # eyes: heavy, half closed, looking down at the jar
        look = (-0.1, 0.9)
        p.eye(*F(-54, 4), 36, 22, look=look, lid=0.52, lower=0.08, droop=0.45, rot=TILT_D - 4, side=-1, iris_r=0.68,
              fold='#e3a39b', reflect='#f7b45e', clip=vf)
        p.eye(*F(46, 2), 43, 25, look=look, lid=0.52, lower=0.08, droop=0.45, rot=TILT_D + 3, side=1, iris_r=0.68,
              fold='#e3a39b', reflect='#f7b45e', clip=vf)
        # the long nose with a red tip; the small unsmiling mouth; a soft contour on the shadow side
        p.nose(FL([(-4, -4), (-8, 28), (-14, 54), (-22, 76)]), 26, tip_r=14, side=1, shade=0.55, tip_strength=0.85,
               clip=vf)
        p.mouth(*F(-12, 112), 34, droop=0.25, rot=TILT_D)
        p.line(FL([(125, -10), (118, 50), (96, 92), (60, 124), (24, 144), (-14, 152), (-48, 140)]), 2.2,
               '#8f7480', 0.3, taper=(0.5, 0.5), dry=0.3, clip=vf)
        p.glaze(p.soften(self.curtain_l, 8) * vf * (1 - self.curtain_l), '#6e5a66', 0.4, 'multiply')

    # ------------------------------------------------------------------ 8. the jar, the ghosts and their light
    def ghosts(self):
        p = self.p
        g, j = GHOST, JAR
        p.light(g['cx'], g['top'] + g['h'] * 0.6, 140, power=1.35, squash=0.9)
        for o in OTHERS:
            p.light(o['cx'], o['top'] + o['h'] * 0.6, o['w'] * 1.15, power=0.7)
        # what catches the light: leaves fully, the sky a little (air), wool and porcelain facing down strongly
        rec = 0.12 + 0.88 * p.soften(self.hedge.astype(np.float32), 40)
        under = p.shading(self.face, light=(0.1, 0.9, 0.45), sigma=40)
        rec = rec * (1 - self.figure) + self.figure * 0.3
        rec = np.where(self.v_face > 0.5, 0.25 + 0.8 * under, rec)
        rec = np.where(self.v_hands > 0.5, 1.0, rec)
        rec = np.where(self.v_scarf > 0.5, 0.45, rec)
        rec = np.where((self.v_coat + self.v_sleeves) > 0.5, 0.7, rec)
        rec = np.where(self.v_cover > 0.5, 0.6, rec)
        p.illuminate(rec.astype(np.float32), gain=1.0, base=0.15, albedo=1.4)
        del rec, under
        for i, o in enumerate(OTHERS):
            p.ghost(o['cx'], o['top'], o['w'], o['h'], look=o['look'], lean=o['lean'], tips=6 if o['w'] < 90 else 7,
                    seed=81 + i)
        # the jar: the coat seen through grey-green glass, the ghost inside, warm air filling the glass
        inside = self.v_jar * (1 - self.cover)
        p.glaze(inside, '#8fa3a6', 0.3, 'multiply')
        p.ghost(g['cx'], g['top'], g['w'], g['h'], look=(-0.6, -0.8), tips=6, glow=1.25, clip=inside, seed=80)
        p.glaze(p.spot(g['cx'], g['top'] + g['h'] * 0.6, 90, 110, solid=0.0) * inside, 'glow', 0.5, 'screen')
        # the glass itself: a band of light just inside its edge (cool on the left, warm on the right), a white
        # streak down the left, the thick base and the shoulders catching the glow
        cx, t, b, hf = j['cx'], j['top'], j['bot'], j['half']
        keep = 1 - self.mittens
        rim = self.jar * (1 - smoothstep(0.55, 0.95, p.soften(self.jar, 5))) * keep * (1 - self.cover)
        p.glaze(rim * (p.XX < cx), '#cdd8da', 0.35, 'screen')
        p.glaze(rim * (p.XX >= cx), 'glow', 0.45, 'screen')
        p.line([(cx - hf + 9, t + 58), (cx - hf + 8, t + 120), (cx - hf + 10, b - 30)], 3.0, '#f2efe6', 0.65,
               taper=(0.4, 0.5), clip=keep)
        p.line([(cx - hf + 22, t + 64), (cx - hf + 21, t + 110)], 7.0, '#e9eee9', 0.16, taper=(0.5, 0.5), clip=keep)
        p.line([(cx + hf - 7, t + 60), (cx + hf - 6, b - 34)], 2.4, 'glow', 0.6, taper=(0.4, 0.4), clip=keep)
        p.line([(cx - hf + 14, b - 12), (cx - 24, b - 2), (cx + 24, b - 2), (cx + hf - 14, b - 12)], 3.4, 'glow', 0.8,
               taper=(0.4, 0.4), clip=keep)
        p.line([(cx - hf + 18, b - 20), (cx, b - 12), (cx + hf - 18, b - 20)], 2.0, 'glow_core', 0.45,
               taper=(0.4, 0.4), clip=keep)
        p.line([(cx - j['neck'] - 2, t + 26), (cx - hf + 8, t + 42)], 2.2, '#f2efe6', 0.5, taper=(0.4, 0.4))
        p.line([(cx + j['neck'] + 2, t + 26), (cx + hf - 8, t + 42)], 2.2, 'glow', 0.5, taper=(0.4, 0.4))
        p.emit(cx, g['top'] + g['h'] * 0.6, 50, 0.3, ry=70)
        # twine round the neck of the jar, a small bow
        tw = [(cx - 60, t + 18), (cx - 30, t + 23), (cx, t + 24), (cx + 30, t + 23), (cx + 60, t + 18)]
        p.line(tw, 3.0, '#a08562', 0.95, taper=(0.1, 0.1))
        p.line([(x, y + 4) for x, y in tw], 2.6, '#7c6448', 0.9, taper=(0.1, 0.1))
        bx, by = cx - 22, t + 24
        for sg in (-1, 1):
            p.line([(bx, by), (bx + sg * 14, by - 10), (bx + sg * 22, by - 4), (bx + sg * 12, by + 2), (bx, by)], 2.6,
                   '#a08562', 0.95, taper=(0.2, 0.2))
        p.line([(bx, by), (bx - 6, by + 18), (bx - 9, by + 30)], 2.4, '#8f7656', 0.9, taper=(0.1, 0.6))
        p.line([(bx, by), (bx + 5, by + 16), (bx + 4, by + 26)], 2.4, '#8f7656', 0.9, taper=(0.1, 0.6))

    # ------------------------------------------------------------------ 9. last touches
    def last(self):
        p = self.p
        # leaves in front: over the lower corners of her coat and round the ghosts in the hedge, lit by them
        front = np.maximum.reduce([p.spot(560, 1060, 220, 140, solid=0.3), p.spot(1240, 1070, 240, 130, solid=0.3),
                                   p.spot(1296, 700, 90, 50, solid=0.2), p.spot(118, 720, 80, 40, solid=0.2),
                                   p.spot(1500, 500, 120, 40, solid=0.2), p.spot(330, 512, 90, 30, solid=0.2)])
        p.foliage(front, 46, (80, 130), ('leaf', 'leaf_olive', 'leaf', 'leaf_maroon', 'leaf_rust'), (0.2, 0.5),
                  lit=1.0, veins=0.4, seed=91)
        # the blunt cut: a few fine tips just below the fringe
        edge = np.zeros((H, W), np.float32)
        for uu in np.linspace(-120, 168, 140):
            x, y = F(uu, -37)
            xi, yi = int(x), int(y)
            edge[yi - 1:yi + 1, xi - 1:xi + 1] = 1
        p.strands(self.fringe, self.hair_flow, ('jet', 'hair_black', 'hair_dark'), n=60, length=(4, 9),
                  width=(0.7, 1.0), roots=edge, clip=False, alpha=0.5, jitter=8, seed=92)
        # loose burlap fibres catching the light at the hat's edge
        b2 = p.soften(self.hat, 2)
        p.strands(self.hat, 0.0, ('burlap_hi', '#8a7462'), n=70, length=(8, 22), width=(0.6, 0.9),
                  roots=((b2 > 0.4) & (b2 < 0.6)).astype(np.float32), curl=20, jitter=80, clip=False, alpha=0.5,
                  seed=93)
        # a faint warm breath in the air round the jar
        p.glaze(p.spot(884, 820, 220, 180, solid=0.0) * (1 - self.v_face) * (1 - self.jar), 'glow', 0.07, 'screen')


PHASES = ('sketch', 'sky', 'hedge_leaves', 'block', 'model', 'cloth', 'features', 'ghosts', 'last')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'poetichalloween_ghost_jar.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:12s} {time.time() - T0:5.1f}s')) if os.environ.get('PH_TIMING') else (lambda n: None)
    p = PoeticHalloween(W, H, seed=11, keep_stages=bool(stages), stages_dir=stages)
    p.finish()
    p.ground()
    p.stage('board')
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
