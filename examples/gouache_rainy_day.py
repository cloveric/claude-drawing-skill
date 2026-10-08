"""Example (retro gouache): 雨天三人像 · Rainy-Day Portraits — a picture-book triptych of three close-up portraits
painted in opaque gouache, side by side on a cream board, each with its own scumbled background.

  1  an old sea-fisherman in a yellow sou'wester still beaded with rain (one drop about to fall off the brim): an
     enormous red nose, white bushy brows,
     big ears, a white chin-curtain beard and a navy cable-knit sweater -- and a small fish poking its head out of
     his felt chest pocket, which he is squinting down at (pale sea-glass background);
  2  a little kid buried in a huge mustard bobble hat and a striped scarf, holding a steaming cocoa mug in two
     mittens, going cross-eyed at the marshmallow floating in it (green background);
  3  a tall lady with a towering orange updo of ringlets, blue eyeshadow, pearl drops, a vermilion turtleneck and a
     cobalt coat with wide teal felt lapels, side-eyeing the snail that has climbed onto her shoulder, its slime
     trail still shining on the coat behind it (blue-to-yellow background).

The painting order is the gouache one, dark to light, big to small: toned ground, umber underdrawing, background
scrubbed round the figures, flat masses, value steps that model each form, textures (cable knit, ribbing, hair and
brow strands, beard, felt, curls), features (blush, noses, eyes, pocket and fish, mug, snail), highlights (rain
drops, steam, catchlights), then the printed-page grain.
--stages writes those steps as snapshots for the draw-on.
No image model.
python3 gouache_rainy_day.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from gouache import GouachePortrait, ramp
from core import blur, shift, smoothstep, spline

PW, PH = 620, 1050
PANELS = [(15, 15), (650, 15), (1285, 15)]
SKIN = ['#c0705d', '#d98d76', '#efbb98', '#f6d0b2', '#fbe3cc']
RUDDY = ['#b8604f', '#d27c66', '#e9a888', '#f2c3a6', '#f8dcc6']


def rrect(cx, cy, w, h, r=10.0, rot=0.0, n=5):
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + qx * (w / 2 - r), cy + qy * (h / 2 - r)
        for a in np.linspace(a0, a0 + 90, n):
            pts.append((ox + r * np.cos(np.deg2rad(a)), oy + r * np.sin(np.deg2rad(a))))
    P = np.array(pts, np.float32)
    if rot:
        a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
        d = P - [cx, cy]
        P = np.stack([cx + d[:, 0] * c - d[:, 1] * s, cy + d[:, 0] * s + d[:, 1] * c], 1)
    return P


def dashes(g, pts, colour, width=2.2, dash=9, gap=7, alpha=0.85):
    """running stitches along a closed outline"""
    P = np.vstack([pts, pts[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = 0.0
    while t + dash < s[-1]:
        u = np.linspace(t, t + dash, 4)
        q = np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1)
        g.line(q, width, colour, alpha, taper=(0.3, 0.3), smooth=False)
        t += dash + gap


def raindrop(g, x, y, r):
    """a bead of water on yellow oilskin: a soft amber shadow under it, the yellow seen through it a little
    brighter, a darker amber rim at the top (refraction) and a sharp white highlight"""
    drop = g.ellipse(x, y, r, r * 0.92)
    g.glaze(g.ellipse(x + r * 0.4, y + r * 0.6, r * 1.05, r * 0.8) * (1 - drop), '#a86a12', 0.55, soft=r * 0.3)
    g.glaze(drop, '#e8a020', 0.45)
    g.glaze(g.ellipse(x + r * 0.15, y + r * 0.42, r * 0.6, r * 0.32) * drop, '#fff3b0', 0.65, mode='screen', soft=1)
    g.dab(x - r * 0.38, y - r * 0.38, max(1.2, r * 0.17), '#fffdf6', 0.95, dry=0.0)


# ================================================================== 1: the sea-fisherman
class Fisherman:
    def __init__(self, g, p):
        self.g, self.p = g, p
        g.use(p)
        S = self.S = {}
        S['sweater'] = g.poly([(14, 1062), (22, 950), (60, 872), (140, 812), (220, 786), (400, 786), (480, 812),
                               (560, 872), (598, 950), (606, 1062)])
        self.collar_path = [(150, 806), (230, 830), (310, 838), (390, 830), (470, 806)]
        S['collar'] = g.band(self.collar_path, 46) * S['sweater']
        S['earL'] = g.blob(100, 512, 46, 64, 0.04, 1, -8)
        S['earR'] = g.blob(520, 512, 46, 64, 0.04, 2, 8)
        S['face'] = g.poly([(150, 330), (310, 316), (470, 330), (512, 430), (520, 540), (502, 640), (452, 712),
                            (380, 752), (310, 762), (240, 752), (168, 712), (118, 640), (100, 540), (108, 430)])
        S['beard'] = g.poly([(104, 548), (106, 640), (146, 728), (226, 786), (310, 806), (394, 786), (474, 728),
                             (514, 640), (516, 548), (486, 600), (456, 666), (392, 702), (310, 712), (228, 702),
                             (164, 666), (134, 600)])
        S['crown'] = g.poly([(158, 372), (160, 300), (188, 236), (240, 194), (310, 180), (380, 194), (432, 236),
                             (460, 300), (462, 372)])
        S['brim'] = g.poly([(20, 496), (30, 432), (96, 376), (200, 348), (310, 342), (420, 348), (524, 376),
                            (590, 432), (600, 496), (572, 500), (540, 470), (500, 446), (412, 422), (310, 414),
                            (208, 422), (120, 446), (80, 470), (48, 500)])

        S['hat'] = np.maximum(S['crown'], S['brim'])
        S['browL'] = g.blob(220, 438, 74, 27, 0.14, 11, -9)
        S['browR'] = g.blob(400, 438, 74, 27, 0.14, 12, 9)
        S['pocket'] = g.poly(rrect(186, 952, 146, 128, 16, -4), smooth=False)
        S['fish'] = g.blob(176, 842, 92, 34, 0.03, 21, 62)
        self.fig = np.maximum.reduce([S['sweater'], S['earL'], S['earR'], S['face'], S['beard'], S['hat'],
                                      S['browL'], S['browR']])

    def sketch(self):
        g, S = self.g, self.S
        for k in ('sweater', 'collar', 'earL', 'earR', 'face', 'beard', 'crown', 'brim', 'browL', 'browR', 'pocket'):
            g.sketch(S[k])
        g.sketch(g.ellipse(312, 540, 92, 80))
        g.sketch(g.ellipse(226, 474, 17, 16)); g.sketch(g.ellipse(394, 474, 17, 16))

    def background(self):
        self.g.scumble_background('#74b6b1', bottom='#93c9bf', avoid=self.fig, angle=-32, seed=101)

    def block_in(self):
        g, S = self.g, self.S
        g.block_in(S['sweater'], 'navy', angle=80)
        g.block_in(S['collar'], '#2b4278', angle=0, length=(20, 40), width=(8, 14))
        for k in ('earL', 'earR'): g.block_in(S[k], '#e49c7e', length=(14, 30), width=(7, 12))
        g.block_in(S['face'], '#e9a888', length=(24, 56), width=(10, 20))
        g.block_in(S['beard'], '#c9c6c0', angle=90, length=(20, 46), width=(8, 16))
        g.block_in(S['crown'], 'yellow', angle=95)
        g.block_in(S['brim'], 'yellow', angle=0)

    def form(self):
        g, S = self.g, self.S
        g.model_form(S['sweater'], ramp('navy', deep=0.55, shadow=0.75, light=0.22, pale=0.4), steps=3,
                     length=(24, 54), width=(9, 18), alpha=0.85)
        g.model_form(S['collar'], ramp('#2b4278', light=0.2, pale=0.35), steps=3, round_=0.5, length=(10, 20), width=(5, 9))
        for k in ('earL', 'earR'):
            g.model_form(S[k], ramp('#e49c7e', cool='#7a1d2a'), steps=3, length=(10, 22), width=(5, 10))
        g.model_form(S['face'], RUDDY, steps=4, length=(18, 40), width=(8, 15), relief=0.5)
        # the brim's core shadow across the forehead and the ears; the beard's shadow on the collar and sweater
        g.cast_shadow(S['hat'], 4, 26, soft=10, alpha=0.5, colour='#8d4d4a', on=np.maximum(S['face'], np.maximum(S['earL'], S['earR'])))
        g.cast_shadow(S['beard'], 6, 22, soft=12, alpha=0.55, colour='#3a3550', on=S['sweater'])
        g.model_form(S['beard'], ['#7f7d84', '#a9a6a6', '#d6d2ca', '#ece7dd', '#faf6ee'], steps=4, angle=90,
                     length=(16, 34), width=(6, 12), relief=0.5)
        yr = ramp('yellow', deep=0.5, shadow=0.72, cool='#6a3a10', light=0.3, pale=0.6)
        g.model_form(S['crown'], yr, steps=4, length=(26, 54), width=(10, 20), relief=0.6)
        # the brim is a flat sheet: lit evenly on top, turning away at the drooping sides, its underside a dark rim
        X = self.p.XX
        tilt = np.abs(X - 310) / 300
        g.model_form(S['brim'], yr, steps=3, height=np.zeros_like(X), angle=lambda x, y: 8 * np.sign(x - 310),
                     length=(40, 90), width=(10, 18), bias=-0.05)
        g.glaze(S['brim'] * smoothstep(0.35, 1.0, tilt), '#c8892a', 0.45)
        under = S['brim'] * (1 - shift(S['brim'], 0, -16))
        g.glaze(blur(under, 2), '#9a6418', 0.7)
        g.cast_shadow(S['crown'], 0, 14, soft=8, alpha=0.3, colour='#a77a2a', on=S['brim'])
        rimline = [(30, 440), (96, 380), (200, 351), (310, 345), (420, 351), (524, 380), (590, 440)]
        g.line(rimline, 4.0, '#fde89a', 0.7, dry=0.35)

    def texture(self):
        g, S = self.g, self.S
        g.knit(S['sweater'], stitch=(14, 10), origin=(310, 0), curve=0.5,
               cables=[(310, 66), (196, 46), (424, 46), (88, 40), (532, 40)], strength=0.8, highlight=0.3, seed=7)
        g.rib(S['collar'], self.collar_path, period=8.5, strength=0.8, seed=8)
        # a soft crease where the crown meets the brim, and a row of stitching round the brim
        g.line([(170, 366), (240, 352), (310, 348), (380, 352), (450, 366)], 3.0, '#b07a18', 0.55, dry=0.3)
        brim_line = [(46, 484), (90, 456), (130, 436), (210, 412), (310, 405), (410, 412), (490, 436), (530, 456), (574, 484)]
        q = spline(np.array(brim_line, np.float32), 12)
        for i in range(0, len(q) - 3, 5):
            g.line(q[i:i + 3], 2.0, '#9e6c12', 0.75, taper=(0.3, 0.3))
        # brows and beard: dark mass first, then strands, dark to light, following the hair's growth
        for k, sgn, cx in (('browL', -1, 220), ('browR', 1, 400)):
            m = S[k]
            g.block_in(m, '#b9b5ae', length=(10, 22), width=(5, 9))
            lam = g.form_light(m, relief=0.6)[0]
            g.hair_strands(m, (lambda x, y, sgn=sgn, cx=cx: (180 if sgn < 0 else 0) - sgn * 14 + (y - 438) * 0.9 * sgn
                               + (x - cx) * 0.08), ['#77736f', '#a8a39d', '#d4cec4', '#ece6db', '#fffbf2'], n=520,
                           length=(14, 42), width=(1.0, 2.4), shade=lam, curl=1.2, spread=0.28, seed=40 + sgn)
        lam = g.form_light(S['beard'], relief=0.5)[0]

        def beard_flow(x, y):
            a = np.degrees(np.arctan2(y - 600, x - 310))
            return 90 + (a - 90) * 0.55
        g.hair_strands(S['beard'], beard_flow, ['#6f6c73', '#9c9a9c', '#c9c5be', '#e6e1d7', '#fbf8f0'], n=2600,
                       length=(16, 46), width=(1.0, 2.3), shade=lam, curl=1.5, spread=0.25, pad=6, seed=44)

    def features(self):
        g, S = self.g, self.S
        face = S['face']
        g.blush(170, 584, 60, 54, 'blush', 0.5, mask=face)
        g.blush(452, 584, 60, 54, 'blush', 0.5, mask=face)
        # little smile under the nose, and crow's feet
        g.line([(278, 650), (296, 660), (318, 662), (340, 654)], 4.2, '#8a3a32', 0.85, taper=(0.3, 0.3))
        g.line([(286, 667), (312, 672), (334, 667)], 2.0, '#c97764', 0.5, taper=(0.4, 0.4))
        for sgn, cx in ((-1, 226), (1, 394)):
            for dy, ln in ((-6, 16), (4, 18), (14, 13)):
                x0 = cx + sgn * 26
                g.line([(x0, 474 + dy * 0.5), (x0 + sgn * ln, 474 + dy)], 1.8, '#b0634f', 0.55, taper=(0.2, 0.8))
        # eyes: small and squinting down at the fish
        for cx in (226, 394):
            g.eye(cx, 476, 17, 15, iris='#1b2226', iris_r=0.62, look=(-0.45, 0.5), lid=0.36, lid_colour='#d98c72',
                  lower=0.3)
        g.nose(312, 544, 94, 82, 'nose', on=np.maximum(face, S['beard']))

        # the fish, then the felt pocket over its tail
        fish = S['fish']
        g.cast_shadow(fish, 7, 10, soft=7, alpha=0.5, colour='#141830', on=S['sweater'])
        fin = g.poly([(196, 806), (226, 792), (224, 830), (204, 846)])
        g.block_in(fin, '#ef8040', length=(6, 14), width=(3, 6))
        g.line([(204, 812), (220, 800)], 1.4, '#a8401a', 0.6); g.line([(206, 826), (222, 818)], 1.4, '#a8401a', 0.6)
        g.block_in(fish, '#a9c9d9', length=(12, 28), width=(5, 10))
        g.model_form(fish, ['#3d6688', '#5f8db0', '#a9c9d9', '#d6e7ee', '#f4f9f8'], steps=4, length=(10, 24),
                     width=(4, 8), relief=0.7, bias=0.05)
        for t in np.linspace(0.42, 0.8, 4):                                  # scales: little arcs down the body
            cx, cy = 140 + (214 - 140) * t, 776 + (916 - 776) * t
            for k in (-1, 0, 1):
                ox, oy = cx + k * 11 * 0.88, cy - k * 11 * 0.47
                g.line([(ox - 5, oy - 4), (ox + 1, oy + 1), (ox + 6, oy - 2)], 1.5, '#4f7899', 0.55, taper=(0.3, 0.3))
        g.line([(140, 812), (154, 818), (164, 834)], 2.6, '#33587a', 0.75)               # gill
        g.eye(154, 800, 12, iris='#141418', iris_r=0.6, look=(0.3, -0.3), lid=0.0, lower=0, catch=(-0.4, -0.45))
        # a gasping 'o' at the tip of the snout, with a pale lip round it
        g.glaze(g.ellipse(139, 772, 9.5, 8.5, 62), '#e9eef0', 0.9, mode='normal')
        mouth = g.ellipse(139, 772, 6.5, 5.5, 62)
        g.block_in(mouth, '#4a1a24', length=(4, 8), width=(3, 5), edge=0.3)
        g.dab(137, 769, 1.4, '#c0707a', 0.7)
        pk = S['pocket']
        g.cast_shadow(pk, 5, 7, soft=5, alpha=0.45, colour='#1a1d34', on=S['sweater'])
        g.block_in(pk, '#d9532e', length=(20, 40), width=(8, 14))
        g.model_form(pk, ramp('#d9532e', cool='#4a1020'), steps=3, round_=0.4, relief=0.35, length=(16, 30), width=(6, 10))
        g.felt(pk, 0.8, seed=12)
        g.glaze(g.poly(rrect(186, 896, 134, 16, 6, -4), smooth=False) * pk, '#5a1a12', 0.55, soft=2)
        dashes(g, rrect(186, 952, 124, 106, 11, -4), '#f6dfb0', 2.2, 8, 6)

    def highlights(self):
        g, S = self.g, self.S
        g.dry_highlight(S['crown'], '#fff0a8', above=0.7, angle='fall', length=(26, 56), width=(5, 12), density=0.45,
                        relief=0.6, seed=61)
        g.dry_highlight(S['brim'], '#fff0a8', above=0.0, height=np.zeros_like(self.p.XX),
                        angle=lambda x, y: 8 * np.sign(x - 310), length=(40, 90), width=(5, 10), density=0.25,
                        alpha=0.55, seed=62)
        g.dry_highlight(S['face'] * (self.p.YY < 520), '#fbe0c8', above=0.72, length=(20, 44), width=(5, 10),
                        density=0.4, alpha=0.45, relief=0.5, seed=63)
        for (x, y), r in zip(((252, 378), (152, 420), (494, 404), (352, 228), (204, 280), (420, 262), (318, 312),
                              (566, 448), (262, 206)), (8, 6, 9, 7, 6, 8, 5, 5, 4)):
            raindrop(g, x, y, r)
        g.line([(214, 214), (196, 250), (188, 300)], 6, '#fff3c4', 0.5, dry=0.4)
        # a drop about to fall off the tip of the brim
        for x, y, r in ((30, 518, 6.5),):
            m = g.poly([(x, y - r * 2.2), (x + r, y - r * 0.2), (x + r * 0.7, y + r * 0.8), (x, y + r),
                        (x - r * 0.7, y + r * 0.8), (x - r, y - r * 0.2)])
            g.glaze(m, '#e9f3f0', 0.75, mode='normal')
            g.glaze(m * g.ellipse(x + r * 0.2, y + r * 0.3, r * 0.7, r * 0.6), '#5f9e98', 0.45)
            g.dab(x - r * 0.3, y - r * 0.4, max(1.2, r * 0.22), '#ffffff', 0.95, dry=0.0)


# ================================================================== 2: the kid with cocoa
class Kid:
    def __init__(self, g, p):
        self.g, self.p = g, p
        g.use(p)
        S = self.S = {}
        S['coat'] = g.poly([(28, 1062), (40, 960), (84, 885), (170, 842), (250, 828), (370, 828), (450, 842),
                            (536, 885), (580, 960), (592, 1062)])
        S['sleeveL'] = g.band([(52, 1080), (104, 1004), (162, 930)], 112, 96)
        S['sleeveR'] = g.band([(568, 1080), (516, 1004), (458, 930)], 112, 96)
        S['face'] = g.ellipse(310, 590, 186, 162)
        S['dome'] = g.poly([(62, 452), (58, 350), (84, 252), (150, 178), (240, 136), (310, 128), (380, 136),
                            (470, 178), (536, 252), (562, 350), (558, 452)])
        S['pom'] = g.blob(312, 112, 98, 92, 0.12, 31)
        self.brim_path = [(34, 466), (170, 456), (310, 451), (450, 456), (586, 466)]
        S['brim'] = g.poly([(38, 420), (120, 406), (310, 398), (500, 406), (582, 420), (592, 468), (582, 520),
                            (500, 506), (310, 500), (120, 506), (38, 520), (28, 468)])
        S['hat'] = np.maximum(S['dome'], S['brim'])
        # the scarf is wound twice: an upper roll over the chin and a lower roll on the collarbone
        self.roll1_path = [(132, 712), (220, 694), (310, 690), (400, 694), (488, 712)]
        self.roll2_path = [(112, 800), (210, 786), (310, 782), (410, 786), (508, 800)]
        S['roll1'] = g.poly([(128, 690), (180, 662), (250, 648), (310, 650), (370, 648), (440, 662), (492, 690),
                             (500, 730), (470, 756), (400, 744), (310, 740), (220, 744), (150, 756), (120, 730)])
        S['roll2'] = g.poly([(104, 772), (170, 748), (250, 740), (310, 742), (370, 740), (450, 748), (516, 772),
                             (524, 820), (490, 850), (400, 834), (310, 830), (220, 834), (130, 850), (96, 820)])
        S['wrap'] = np.maximum(S['roll1'], S['roll2'])
        self.tail_path = [(190, 800), (180, 900), (168, 1004)]
        S['tail'] = g.band(self.tail_path, 108, 100)
        S['mug'] = g.poly(rrect(310, 880, 178, 176, 30), smooth=False)
        S['cocoa'] = g.ellipse(310, 796, 80, 17)
        S['rim'] = g.ellipse(310, 794, 89, 21)
        S['mitL'] = np.maximum(g.blob(212, 892, 54, 66, 0.05, 41, 14), g.blob(248, 852, 19, 30, 0.05, 42, 28))
        S['mitR'] = np.maximum(g.blob(408, 892, 54, 66, 0.05, 43, -14), g.blob(372, 852, 19, 30, 0.05, 44, -28))
        S['mallow'] = g.poly(rrect(334, 784, 50, 38, 11, 12), smooth=False)
        S['mallow2'] = g.poly(rrect(284, 792, 36, 28, 9, -18), smooth=False)
        self.fig = np.maximum.reduce([S['coat'], S['face'], S['hat'], S['pom'], S['wrap'], S['tail'],
                                      S['sleeveL'], S['sleeveR']])

    def sketch(self):
        g, S = self.g, self.S
        for k in ('coat', 'sleeveL', 'sleeveR', 'face', 'dome', 'pom', 'brim', 'roll1', 'roll2', 'tail', 'mug', 'mitL', 'mitR'):
            g.sketch(S[k])
        g.sketch(g.ellipse(236, 556, 40)); g.sketch(g.ellipse(384, 556, 40))

    def background(self):
        self.g.scumble_background('#4f9a5c', bottom='#5aa565', avoid=self.fig, angle=-40, seed=202)

    def block_in(self):
        g, S = self.g, self.S
        g.block_in(S['coat'], 'cobalt', angle=80)
        for k in ('sleeveL', 'sleeveR'): g.block_in(S[k], 'cobalt', angle=60)
        g.block_in(S['face'], 'peach', length=(24, 50), width=(10, 18))
        g.block_in(S['tail'], 'vermilion', angle=95)
        g.block_in(S['roll2'], 'vermilion', angle=0)
        g.block_in(S['roll1'], 'vermilion', angle=0)
        g.block_in(S['dome'], 'mustard', angle=90)
        g.block_in(S['brim'], 'mustard', angle=0)
        g.block_in(S['pom'], '#e05a2a', length=(16, 34), width=(8, 14))

    def form(self):
        g, S = self.g, self.S
        coat_r = ramp('cobalt', deep=0.5, shadow=0.72, light=0.2, pale=0.38)
        g.model_form(S['coat'], coat_r, steps=3, length=(26, 56), width=(9, 18))
        for k in ('sleeveL', 'sleeveR'):
            g.model_form(S[k], coat_r, steps=3, angle='fall', length=(20, 44), width=(8, 14), relief=0.3, bias=0.08)
        g.cast_shadow(np.maximum(S['sleeveL'], S['sleeveR']), 8, 10, soft=10, alpha=0.4, colour='#1a1a40', on=S['coat'])
        g.model_form(S['face'], SKIN, steps=4, length=(18, 40), width=(8, 15), relief=0.45)
        g.cast_shadow(S['hat'], 2, 24, soft=10, alpha=0.5, colour='#9a5048', on=S['face'])
        g.cast_shadow(S['wrap'], 0, -10, soft=8, alpha=0.3, colour='#9a5048', on=S['face'])
        stripe = lambda m, ph, per, along: m * (np.cos((along + ph) * 2 * np.pi / per) > 0.55)
        red = ramp('vermilion', cool='#3a0a20', light=0.24, pale=0.45)
        cream = ramp('cream', deep=0.55, shadow=0.8, cool='#5a3020', light=0.2, pale=0.4)
        lamt, Ht, _ = g.form_light(S['tail'], relief=0.6)
        st_ = stripe(S['tail'], 30, 92, self.p.YY)
        g.model_form(S['tail'] * (1 - st_), red, steps=4, height=Ht, angle=90, length=(18, 40), width=(7, 13))
        g.model_form(st_, cream, steps=4, height=Ht, angle=90, length=(14, 30), width=(6, 11))
        g.cast_shadow(S['tail'], 10, 8, soft=10, alpha=0.45, colour='#1a1a40', on=S['coat'])
        g.cast_shadow(S['wrap'], 4, 18, soft=12, alpha=0.5, colour='#1a1a40', on=S['coat'])
        g.cast_shadow(S['roll2'], 0, 22, soft=10, alpha=0.5, colour='#3a1a20', on=S['tail'])
        for k, ph in (('roll2', 52), ('roll1', 20)):
            lamw, Hw, _ = g.form_light(S[k], relief=0.75, round_=0.45)
            sw_ = stripe(S[k], ph, 84, self.p.XX)
            g.model_form(S[k] * (1 - sw_), red, steps=4, height=Hw, angle=0, length=(18, 40), width=(7, 13))
            g.model_form(sw_, cream, steps=4, height=Hw, angle=0, length=(14, 30), width=(6, 11))
            if k == 'roll2':
                g.cast_shadow(S['roll1'], 0, 16, soft=8, alpha=0.55, colour='#3a1020', on=S['roll2'])
        hat_r = ramp('mustard', deep=0.5, shadow=0.72, cool='#5a2a10', light=0.28, pale=0.55)
        g.model_form(S['dome'], hat_r, steps=4, length=(26, 56), width=(10, 20), relief=0.65)
        g.cast_shadow(S['brim'], 0, -16, soft=8, alpha=0.4, colour='#7a4a20', on=S['dome'])
        g.model_form(S['brim'], hat_r, steps=3, round_=0.45, relief=0.45, angle=0, length=(30, 60), width=(10, 18))
        g.cast_shadow(S['pom'], 10, 22, soft=12, alpha=0.5, colour='#6a3a10', on=S['dome'])
        g.sphere_shade(312, 112, 98, 92, ramp('#e05a2a', cool='#3a0a1a', light=0.26, pale=0.5), steps=4, mask=S['pom'],
                       length=(12, 30), width=(6, 12))

    def texture(self):
        g, S = self.g, self.S
        g.knit(S['dome'], stitch=(17, 12), origin=(310, 0), curve=-0.9, strength=0.75, seed=9)
        g.rib(S['brim'], self.brim_path, period=10, strength=0.8, seed=10)
        g.knit(S['roll2'], stitch=(14, 11), path=self.roll2_path, strength=0.65, seed=11)
        g.knit(S['roll1'], stitch=(14, 11), path=self.roll1_path, strength=0.65, seed=16)
        g.knit(S['tail'], stitch=(14, 11), path=self.tail_path, strength=0.65, seed=12)
        # fringe at the end of the scarf
        for x in np.linspace(126, 220, 13):
            g.line([(x, 1046), (x - 2, 1062), (x - 3, 1080)], 5.0, '#f0e0c0' if int(x) % 2 else '#d84a2a', 0.95, taper=(0.1, 0.6))
        lam = g.form_light(S['pom'], relief=0.9)[0]
        g.hair_strands(S['pom'], lambda x, y: np.degrees(np.arctan2(y - 112, x - 312)),
                       ['#7a2412', '#b8401c', '#e2622c', '#f2884a', '#fbb47a'], n=1700, length=(10, 30), width=(1.2, 2.6),
                       shade=lam, curl=4, jitter=22, spread=0.22, pad=8, seed=45)
        g.felt(S['coat'], 0.6, fibres=0.4, fuzz=0.0, seed=13)
        for k in ('sleeveL', 'sleeveR'): g.felt(S[k], 0.6, fibres=0.4, fuzz=0.0)

    def features(self):
        g, S = self.g, self.S
        face = S['face']
        g.blush(176, 622, 60, 52, 'blush', 0.55, mask=face)
        g.blush(444, 622, 60, 52, 'blush', 0.55, mask=face)
        for cx, lk in ((236, (0.72, 0.62)), (384, (-0.72, 0.62))):
            g.eye(cx, 556, 40, iris='#18343a', iris_r=0.5, look=lk, lid=0.1, lid_colour='#e8a48a', ring='#6e9d52',
                  lower=0.35, iris_light='#3f8f8a')
        g.nose(310, 612, 34, 29, 'rose', on=face)
        # the mug: a cream cylinder with vermilion dots, cocoa, a marshmallow; mittens round it
        mug = S['mug']
        g.cast_shadow(mug, 10, 16, soft=12, alpha=0.5, colour='#141436', on=np.maximum(S['coat'], S['tail']))
        g.block_in(mug, 'cream', angle=90, length=(20, 44), width=(8, 16))
        cyl = np.sqrt(np.clip(1 - ((self.p.XX - 310) / 89) ** 2, 0, 1)) * 60
        g.model_form(mug, ramp('cream', deep=0.55, shadow=0.78, cool='#40305a', light=0.2, pale=0.4), steps=4,
                     height=cyl, angle=90, length=(16, 40), width=(6, 12))
        for (x, y, r) in ((262, 852, 13), (318, 838, 12), (356, 884, 13), (292, 912, 12), (340, 940, 10), (248, 936, 9),
                          (380, 836, 9)):
            sq = np.cos(np.arcsin(np.clip((x - 310) / 89, -0.95, 0.95)))
            g.block_in(g.ellipse(x, y, r * sq, r) * mug, '#d9482c', length=(4, 10), width=(3, 6), edge=0.5)
        g.glaze(g.ellipse(310, 800, 84, 20) * (1 - g.ellipse(310, 798, 80, 17)), '#7a6a6a', 0.4)
        g.block_in(S['rim'], '#efe4cf', length=(10, 20), width=(4, 8))
        g.block_in(S['cocoa'], 'cocoa', angle=0, length=(10, 30), width=(4, 8))
        g.glaze(g.ellipse(298, 800, 64, 11) * S['cocoa'], '#a06a46', 0.6, mode='normal', soft=2)
        for k in ('mallow2', 'mallow'):
            g.cast_shadow(S[k], 4, 7, soft=3, alpha=0.6, colour='#2a1408', on=S['cocoa'])
            g.block_in(S[k], '#f7e8e6', length=(8, 18), width=(4, 8))
            g.model_form(S[k], ['#b58a96', '#d9b2b8', '#f5e4e2', '#fbf1ee', '#fffaf6'], steps=3, round_=0.4,
                         relief=0.6, length=(6, 14), width=(3, 6))
        for k, sgn in (('mitL', -1), ('mitR', 1)):
            m = S[k]
            g.cast_shadow(m, 6, 10, soft=8, alpha=0.45, colour='#2a2040', on=mug)
            g.block_in(m, 'mustard', length=(14, 30), width=(6, 12))
            g.model_form(m, ramp('mustard', cool='#5a2a10', light=0.28, pale=0.5), steps=3, relief=0.7,
                         length=(12, 26), width=(5, 10))
            g.knit(m, stitch=(10, 8), origin=(212 if sgn < 0 else 408, 0), angle=-14 * sgn, strength=0.6)

    def highlights(self):
        g, S = self.g, self.S
        # steam: two soft curls leaning away from the face, fading out over the scarf
        for x0, lean, top, w in ((268, -1, 690, 22), (358, 1, 700, 20)):
            ys = np.linspace(774, top, 14)
            u = (774 - ys) / (774 - top)
            xs = x0 + lean * 40 * u ** 1.4 + 13 * np.sin(u * 2.4 * np.pi) * (0.4 + u)
            path = np.stack([xs, ys], 1)
            g.dry_brush(path, w, '#fbf6ec', dry=0.45, alpha=0.4, streak=0.4, pickup=0.25, taper=(0.35, 0.6))
            g.dry_brush(path + [lean * 3, 4], w * 0.32, '#ffffff', dry=0.55, alpha=0.4, streak=0.6, taper=(0.3, 0.7))
        g.dab(258, 834, 5, '#fff7e8', 0.8)
        front = np.maximum.reduce([S['tail'], S['wrap'], S['mug'], S['mitL'], S['mitR'], S['sleeveL'], S['sleeveR']])
        g.dry_highlight(S['coat'] * (1 - front), '#6f9be0', above=0.66, length=(30, 70), width=(7, 14), density=0.5,
                        alpha=0.6, seed=64)
        g.dry_highlight(S['face'] * (self.p.YY < 600), '#fbe4cf', above=0.74, length=(18, 40), width=(5, 9),
                        density=0.4, alpha=0.4, seed=65)
        g.dab(312, 777, 3, '#ffffff', 0.9)
        g.line([(240, 820), (238, 870), (242, 918)], 5, '#fffaf0', 0.55, dry=0.35)


# ================================================================== 3: the lady and the snail
class Lady:
    def __init__(self, g, p):
        self.g, self.p = g, p
        g.use(p)
        S = self.S = {}
        r = np.random.default_rng(77)
        S['coat'] = g.poly([(20, 1062), (32, 968), (80, 904), (170, 866), (244, 856), (376, 856), (450, 866),
                            (540, 904), (588, 968), (600, 1062)])
        S['neck'] = g.poly([(228, 690), (392, 690), (396, 872), (224, 872)], smooth=False)
        self.turtle_path = [(214, 838), (310, 852), (406, 838)]
        S['neckband'] = g.poly([(214, 800), (310, 812), (406, 800), (414, 878), (310, 892), (206, 878)])
        S['vee'] = g.poly([(236, 860), (384, 860), (350, 1070), (270, 1070)], smooth=False)
        S['turtle'] = np.maximum(S['neckband'], S['vee'])
        # wide notched lapels of the coat collar, felt
        lap = [(232, 846), (164, 866), (118, 902), (150, 928), (100, 972), (214, 1070), (290, 1070), (300, 980),
               (296, 900), (268, 860)]
        S['collarL'] = g.poly(lap, smooth=False)
        S['collarR'] = g.poly([(620 - x, y) for x, y in lap], smooth=False)
        S['earL'] = g.blob(164, 606, 30, 44, 0.04, 51, -6)
        S['earR'] = g.blob(456, 606, 30, 44, 0.04, 52, 6)
        S['face'] = g.poly([(310, 412), (412, 440), (456, 530), (452, 640), (418, 716), (360, 760), (310, 770),
                            (260, 760), (202, 716), (168, 640), (164, 530), (208, 440)])
        # the updo: a hair cap over the head, side swoops, and a tower of curls
        cap = g.poly([(150, 560), (148, 470), (186, 400), (250, 362), (310, 352), (370, 362), (434, 400), (472, 470),
                      (470, 560), (446, 520), (420, 480), (360, 452), (310, 448), (260, 452), (200, 480), (174, 520)])
        swL = g.blob(160, 520, 48, 78, 0.08, 53, 8)
        swR = g.blob(460, 520, 48, 78, 0.08, 54, -8)
        tower = [(310, 366, 138), (292, 270, 120), (330, 186, 104), (300, 112, 88), (326, 52, 64)]
        S['tower'] = np.maximum.reduce([g.blob(x, y, rr, rr * 0.92, 0.10, 60 + i) for i, (x, y, rr) in enumerate(tower)])
        S['hair'] = np.maximum.reduce([cap, swL, swR, S['tower']])
        # curl centres scattered over the mass
        cs = []
        hm = S['hair']
        for _ in range(6000):
            x, y = r.uniform(110, 510), r.uniform(10, 560)
            if hm[int(y), int(x)] > 0.5 and all((x - a) ** 2 + (y - b) ** 2 > 60 ** 2 for a, b, _ in cs):
                cs.append((x, y, r.uniform(34, 60)))
        self.curls = np.array(cs, np.float32)
        S['shell'] = g.ellipse(472, 852, 50, 47)
        S['snail'] = g.poly([(366, 902), (374, 878), (398, 864), (430, 870), (500, 884), (556, 900), (574, 918),
                             (538, 924), (450, 920), (388, 916)])
        self.fig = np.maximum.reduce([S['coat'], S['neck'], S['face'], S['hair'], S['earL'], S['earR'],
                                      S['collarL'], S['collarR'], S['turtle']])

    def curl_fields(self):
        """nearest curl centre for every pixel -> a flow round it and a little bump of height"""
        P = self.p
        X, Y = P.XX, P.YY
        best = np.full(X.shape, 1e9, np.float32); flow = np.zeros_like(X); bump = np.zeros_like(X)
        for x, y, rr in self.curls:
            d2 = (X - x) ** 2 + (Y - y) ** 2
            m = d2 < best
            best = np.where(m, d2, best)
            d = np.sqrt(d2)
            flow = np.where(m, np.degrees(np.arctan2(Y - y, X - x)) + 90 + 14, flow)
            # a ringlet seen end-on: a rolled loop of hair round a dark hollow
            ring = np.sqrt(np.clip(1 - ((d - 0.5 * rr) / (0.62 * rr)) ** 2, 0, 1))
            bump = np.where(m, ring * rr * 0.75, bump)
        return flow, bump

    def sketch(self):
        g, S = self.g, self.S
        for k in ('coat', 'neck', 'turtle', 'collarL', 'collarR', 'face', 'hair', 'earL', 'earR', 'shell', 'snail'):
            g.sketch(S[k])

    def background(self):
        self.g.scumble_background('#4a95cc', bottom='#f2c84a', avoid=self.fig, angle=-25, blend=(0.3, 0.92), seed=303)

    def block_in(self):
        g, S = self.g, self.S
        g.block_in(S['coat'], 'cobalt', angle=80)
        g.block_in(S['neck'], '#ecb592', angle=90, length=(20, 40), width=(8, 14))
        g.block_in(S['turtle'], '#d8452e', angle=0, length=(16, 36), width=(6, 12))
        for k in ('collarL', 'collarR'): g.block_in(S[k], 'teal', length=(20, 44), width=(8, 16))
        for k in ('earL', 'earR'): g.block_in(S[k], '#eaa98a', length=(10, 22), width=(5, 10))
        g.block_in(S['face'], '#f2c3a0', length=(24, 50), width=(10, 18))
        g.block_in(S['hair'], '#c9561c', length=(20, 44), width=(8, 16))

    def form(self):
        g, S = self.g, self.S
        g.model_form(S['coat'], ramp('cobalt', deep=0.5, shadow=0.72, light=0.2, pale=0.38), steps=3,
                     length=(26, 56), width=(9, 18))
        neck_r = ['#b46553', '#cf8670', '#ecb592', '#f3cba9', '#f8dcc2']
        g.model_form(S['neck'], neck_r, steps=3, angle=90, length=(16, 34), width=(6, 12), relief=0.5, bias=-0.1)
        g.cast_shadow(S['face'], 0, 26, soft=10, alpha=0.55, colour='#8a4048', on=S['neck'])
        g.model_form(S['turtle'], ramp('#d8452e', cool='#3a0a20', light=0.2, pale=0.4), steps=3,
                     angle=0, length=(14, 30), width=(5, 10))
        for k in ('collarL', 'collarR'):
            g.cast_shadow(S[k], 6, 12, soft=10, alpha=0.5, colour='#141436', on=np.maximum(S['coat'], S['turtle']))
            g.model_form(S[k], ramp('teal', deep=0.5, shadow=0.72, cool='#10203a', light=0.24, pale=0.45), steps=3,
                         length=(18, 40), width=(7, 14), relief=0.25, round_=0.25)
        for k in ('earL', 'earR'):
            g.model_form(S[k], ramp('#eaa98a', cool='#7a1d2a'), steps=3, length=(8, 18), width=(4, 8))
        g.model_form(S['face'], SKIN, steps=4, length=(18, 40), width=(8, 15), relief=0.45)
        g.cast_shadow(S['hair'], 4, 20, soft=10, alpha=0.5, colour='#9a4a40', on=np.maximum(S['face'], np.maximum(S['earL'], S['earR'])))
        flow, bump = self.curl_fields()
        lam0, H0, _ = g.form_light(S['hair'], relief=0.6, round_=0.35)
        g.model_form(S['hair'], ramp('#e2702a', deep=0.42, shadow=0.68, cool='#3a0a10', light=0.26, pale=0.5),
                     steps=4, height=H0 * 0.6 + bump, angle=flow, length=(14, 30), width=(6, 11))

    def texture(self):
        g, S = self.g, self.S
        lapels = np.maximum(S['collarL'], S['collarR'])
        g.rib(S['neckband'] * (1 - lapels), self.turtle_path, period=8, strength=0.7, highlight=0.25)
        for k in ('collarL', 'collarR'):                                  # the pressed edge of the lapel
            g.sketch(S[k], colour='#0f4a44', width=1.6, alpha=0.7, breaks=0.12)
        g.knit(S['vee'] * (1 - S['neckband']) * (1 - lapels), stitch=(11, 8), origin=(310, 0), curve=0.4, strength=0.55)
        flow, bump = self.curl_fields()
        lam_t, H0, _ = g.form_light(S['hair'], relief=0.6, round_=0.35)
        lam = g.form_light(S['hair'], height=H0 * 0.6 + bump)[0]
        g.hair_strands(S['hair'], flow, ['#5e1a08', '#9a3510', '#d0581c', '#ec7d32', '#f8a85a', '#fdd08e'], n=4600,
                       length=(24, 64), width=(1.0, 2.4), shade=lam, curl=1.6, jitter=7, spread=0.18, pad=5, seed=46)
        # long locks swept up the tower over the curls, so they read as one hairdo, and a few flyaways
        sweep = lambda x, y: -90 + np.clip((310 - x) * 0.35, -40, 40) + 12 * np.sin(y / 40.0)
        g.hair_strands(S['tower'], sweep, ['#d0601e', '#ee8538', '#f8a85a', '#fcc77e'], n=300, length=(50, 120),
                       width=(0.9, 1.8), shade=lam_t, curl=1.0, jitter=6, spread=0.22, alpha=0.6, seed=47)
        edge = S['hair'] * (blur(S['hair'], 6) < 0.85)                  # a band just inside the silhouette
        g.hair_strands(S['hair'], sweep, ['#c24e18', '#f2a050'], n=90, roots=edge, length=(20, 46), width=(0.8, 1.4),
                       curl=4, jitter=25, alpha=0.8, clip=False, seed=48)
        for k in ('collarL', 'collarR'): g.felt(S[k], 0.55, seed=14)
        g.felt(S['coat'], 0.6, fibres=0.4, fuzz=0.0, seed=15)

    def features(self):
        g, S = self.g, self.S
        face = S['face']
        g.blush(226, 652, 46, 40, 'blush', 0.5, mask=face)
        g.blush(398, 652, 46, 40, 'blush', 0.5, mask=face)
        # thin arched brows
        g.line([(214, 520), (238, 506), (268, 506), (288, 516)], 4.2, '#a2401a', 0.9, taper=(0.3, 0.6))
        g.line([(334, 514), (356, 503), (386, 504), (410, 518)], 4.2, '#a2401a', 0.9, taper=(0.6, 0.3))
        for cx, ld in ((252, -1), (370, 1)):
            g.eye(cx, 566, 30, 27, iris='#1c5f62', iris_r=0.56, look=(0.62, 0.45), lid=0.5, lid_colour='#6d9bd6',
                  lashes=3, lash_dir=ld, lower=0.25, iris_light='#4aa39a')
        g.nose(318, 634, 36, 46, 'rose', on=face, cast=(0.3, 0.46, 0.38))
        lips = g.poly([(290, 698), (302, 690), (314, 694), (326, 690), (338, 698), (326, 710), (302, 710)])
        g.block_in(lips, '#cf3b2c', length=(6, 14), width=(3, 6), edge=0.4)
        g.model_form(lips, ramp('#cf3b2c', cool='#3a0a1a'), steps=3, relief=0.7, length=(6, 12), width=(3, 5))
        g.line([(292, 699), (314, 700), (336, 699)], 1.8, '#6a1218', 0.85, taper=(0.3, 0.3))
        g.dab(305, 693, 2.2, '#ffd9c8', 0.8)
        # pearl drops
        for x in (162, 458):
            g.cast_shadow(g.ellipse(x, 664, 12), 3, 5, soft=3, alpha=0.4, colour='#7a3a40')
            g.line([(x, 640), (x, 652)], 2.0, '#d9b45a', 0.9)
            g.sphere_shade(x, 664, 12, 12, ['#8a8a9a', '#b8b6bf', '#ece6dc', '#f8f4ec', '#ffffff'], steps=4,
                           length=(4, 8), width=(2, 4))
        # the snail on her shoulder
        g.cast_shadow(np.maximum(S['snail'], S['shell']), 6, 10, soft=7, alpha=0.5, colour='#0c2030',
                      on=np.maximum(S['collarR'], S['coat']))
        g.block_in(S['snail'], '#9da36e', angle=0, length=(10, 24), width=(4, 9))
        g.model_form(S['snail'], ['#56603a', '#7a8452', '#a7ad78', '#c8cc9c', '#e6e8c6'], steps=3, relief=0.7,
                     length=(8, 18), width=(3, 7))
        for (x0, y0), (x1, y1) in (((386, 874), (360, 822)), ((400, 868), (394, 818))):
            g.line([(x0, y0), ((x0 + x1) / 2 - 3, (y0 + y1) / 2), (x1, y1)], 5.0, '#8f9860', 0.95, taper=(0.05, 0.05))
            g.dab(x1, y1, 6.0, '#8f9860', 0.95)
            g.dab(x1 + 1.5, y1 + 1, 3.2, '#22240f', 0.95, dry=0.0)
            g.dab(x1, y1 - 0.5, 1.2, '#fffff0', 0.95, dry=0.0)
        g.line([(372, 896), (381, 902), (392, 899)], 2.2, '#3a4224', 0.85, taper=(0.3, 0.3))     # a contented smile
        g.blush(380, 890, 7, 5, '#e08a70', 0.45, grain=0.3)
        g.block_in(S['shell'], '#e79a4a', length=(10, 22), width=(5, 9))
        g.sphere_shade(472, 852, 50, 47, ramp('#e79a4a', cool='#5a1020', light=0.3, pale=0.55), steps=4, mask=S['shell'],
                       length=(8, 20), width=(4, 9))
        th = np.linspace(0, 3.3 * np.pi, 70)
        rr = 43 * (1 - th / (3.6 * np.pi))
        spiral = np.stack([477 + rr * np.cos(th + 2.6), 855 + rr * 0.95 * np.sin(th + 2.6)], 1)
        g.line(spiral, 3.6, '#8a3a1c', 0.85, taper=(0.1, 0.6))
        g.line(spiral + [-2.5, -2.5], 1.6, '#ffd09a', 0.5, taper=(0.1, 0.6), dry=0.3)

    def highlights(self):
        g, S = self.g, self.S
        # the slime trail: a wet sheen on the felt behind the snail -- darker where the felt is wet, a broken
        # white gloss along it
        trail = [(566, 918), (580, 934), (588, 954), (592, 976), (602, 1000), (612, 1022)]
        wet = g.band(trail, 20, 14) * S['coat']
        g.glaze(wet, '#14205a', 0.4, soft=2)
        g.dry_brush(trail, 15, '#c9d8ea', dry=0.45, alpha=0.6, streak=0.8, taper=(0.05, 0.3))
        g.line(np.array(trail) + [-3, -1], 2.4, '#ffffff', 0.85, taper=(0.1, 0.4), dry=0.5)
        for x, y in ((582, 938), (594, 972), (606, 1006)):
            g.dab(x - 2, y, 2.2, '#ffffff', 0.9, dry=0.0)
        g.dab(450, 828, 7, '#fff3dc', 0.85)
        front = np.maximum.reduce([S['collarL'], S['collarR'], S['turtle'], S['snail'], S['shell'], S['neck']])
        g.dry_highlight(S['coat'] * (1 - g.rough(front, 0.3)), '#6f9be0', above=0.66, length=(30, 70), width=(7, 14),
                        density=0.5, alpha=0.6, seed=66)
        for k in ('collarL', 'collarR'):
            g.dry_highlight(S[k], '#5fc0b0', above=0.6, length=(24, 50), width=(5, 10), density=0.5, alpha=0.5,
                            relief=0.25, seed=67)
        g.dry_highlight(S['face'] * (self.p.YY < 600), '#fbe4cf', above=0.74, length=(18, 40), width=(5, 9),
                        density=0.4, alpha=0.4, seed=68)
        g.dab(330, 602, 4, '#fff6ea', 0.7)
        g.line([(326, 40), (304, 84), (300, 120)], 4.5, '#ffe0a8', 0.5, dry=0.4)


PHASES = ('sketch', 'background', 'block_in', 'form', 'texture', 'features', 'highlights')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'gouache_rainy_day.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:12s} {time.time() - T0:5.1f}s')) if os.environ.get('GP_TIMING') else (lambda n: None)
    g = GouachePortrait(1920, 1080, seed=11, keep_stages=bool(stages), stages_dir=stages)
    ps = [g.panel(x, y, PW, PH) for x, y in PANELS]
    g.ground('#c88f5a', alpha=0.5)
    g.stage('ground')
    chars = [Fisherman(g, ps[0]), Kid(g, ps[1]), Lady(g, ps[2])]
    tick('setup')
    for ph in PHASES:
        for c in chars:
            g.use(c.p)
            getattr(c, ph)()
        tick(ph)
        g.stage(ph)
    g.grain(1.0)
    g.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out)


if __name__ == '__main__':
    main()
