"""Example (colour town): 雨后的节日台阶街 · Festival Steps After the Rain -- a dense, cheerful hill town in gouache
and fine ink.

Morning, just after a shower, on a festival day. A lane of stone steps climbs from a wet little square, passes under
a mint-green house that bridges the lane on an archway, and goes on up the hill. Tall narrow houses in tomato red,
mustard, teal, mint, coral and cream are piled up the slope behind it, row above row, under blue-grey slate mansard
roofs with dormers, chimney pots and TV aerials; a white clock tower with an onion dome stands on top of the hill
on the left, and the sky is pale blue with creamy clouds. On the left the street is a canyon wall that runs away
toward the vanishing point; on the right a tall house with a cafe stands close to us. Strings of bunting cross the
street at four depths. Red roses climb the walls, window boxes overflow, there are iron balconies, a flower shop and
a bakery, a lamp post, hanging signs, a cat on the steps, and a few people out early -- one with an umbrella, a child
with a red balloon. The square is still wet and mirrors all of it.

Gouache and ink: every surface is flat opaque colour with a little brush texture (walls in vertical strokes, the sky
and the paving in horizontal ones), and almost everything has a fine, slightly shaky dark-brown ink line; slates are
laid one by one, windows are each a little different, pennants have a darker fold.

Painted back to front, the way an illustrator works: paper -> sky -> far town and clock tower -> the upper rows ->
the bridge-house, the steps and the houses on the square -> the canyon walls -> roses, flowers and signs -> the near
bunting -> the wet square and its reflections -> people, the lamp and the last glints.
--stages writes those steps as snapshots for the draw-on. No image model.
python3 colortown_festival_steps.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from colortown import ColorTown, _homography

W, H = 1500, 2000
VP = (700, 1180)                       # vanishing point (eye level)
PLAZA = 1640                           # where the houses on the square stand
NEAR_R = 1900                          # foot of the near house on the right
# the canyon wall on the left: a flat layout of 900 x 2200 laid onto this quad (near edge off-canvas)
CANYON_SRC = (0, 0, 900, 2200)
CANYON_DST = [(-80, -358), (300, 391), (300, 1650), (-80, 2096)]
CH = _homography([(0, 0), (900, 0), (900, 2200), (0, 2200)], CANYON_DST)


def canyon(x, y):
    q = CH @ np.array([x, y, 1.0])
    return q[0] / q[2], q[1] / q[2]


def base_line():
    """the line each column's reflection is mirrored about"""
    xs = np.arange(W, dtype=np.float32)
    b = np.full(W, PLAZA, np.float32)
    b[xs < 300] = 1650 + 1.175 * (300 - xs[xs < 300])
    b[xs >= 1180] = NEAR_R
    return b


class Scene:
    def __init__(self, t):
        self.t = t

    # ------------------------------------------------------------------ sky
    def sky(self):
        t = self.t
        t.sky(y1=1150)
        t.clouds([(960, 300, 520, 170), (640, 150, 300, 95), (1200, 140, 260, 80), (300, 560, 260, 80)])
        t.birds((760, 380, 980, 470), n=4, size=(6, 10))

    # ------------------------------------------------------------------ far town and the clock tower
    def row(self, x0, x1, base, wr, hr, fl, seed, slope=0.0, jitter=20, boxes=0.5, palette=None, tiles=0.15,
            pointy=0.22, tower=0.12, chimneys=True):
        """a storybook-irregular row of houses climbing the hill: widths, heights, bases and roofs all vary"""
        t = self.t
        r = np.random.default_rng(seed)
        pal = palette or ('tomato', 'white', 'mustard', 'teal', 'cream', 'coral', 'mint', 'butter', 'cerulean',
                          'ivory', 'salmon', 'jade', 'yellow', 'pink', 'powder', 'white')
        x, prev = x0, None
        while x < x1 - 12:
            narrow = r.random() < tower
            w = r.uniform(wr[0] * 0.62, wr[0] * 0.8) if narrow else r.uniform(*wr)
            if x1 - (x + w) < wr[0] * 0.55: w = x1 - x
            b = base + slope * (x - x0) + r.uniform(-jitter, jitter * 0.5)
            h = r.uniform(*hr) * (1.25 if narrow else 1.0)
            c = prev
            while c == prev: c = pal[r.integers(0, len(pal))]
            prev = c
            u = r.random()
            if narrow or u < pointy:
                rf, rh = 'gable', w * r.uniform(0.75, 1.0)
            else:
                rf = ('mansard', 'mansard', 'hip', 'side', 'gable')[r.integers(0, 5)]
                rh = w * (0.42 if rf != 'gable' else 0.6)
            light = c in ('white', 'cream', 'ivory', 'butter', 'pale_yellow')
            sh = ('cobalt', 'jade', 'tomato', 'cerulean', 'mint')[r.integers(0, 5)] if (light and r.random() < 0.7) else None
            t.house(x, b, w, h, c, roof=rf, roof_h=rh, floors=max(3, int(round(h / fl))),
                    cols=max(1 if narrow else 2, int(round(w / (fl * 1.0)))), boxes=boxes, shutters=sh,
                    chimneys=(1 + (w > wr[1] * 0.8)) if chimneys else 0, aerials=0.6, ground=None,
                    roof_col='tile' if r.random() < tiles else 'slate', stones=2 if light and r.random() < 0.5 else 0,
                    bands=r.random() < 0.7, seed=int(r.integers(1 << 30)),
                    top_window=('round', 'round', 'std', 'arch')[r.integers(0, 4)])
            x += w

    def far(self):
        t = self.t
        with t.depth(0.42):
            t.lw = 0.8
            self.row(300, 600, 905, (62, 92), (140, 200), 34, seed=201, boxes=0.3)
            self.row(600, 1190, 830, (80, 115), (220, 300), 36, seed=202, slope=-0.2, boxes=0.3)
        t.lw = 1.25
        with t.depth(0.12):
            self.tower = t.clock_tower(432, 960, 112, 660, time=(9, 4), seed=5, dome='verdigris')
        with t.depth(0.3):
            t.lw = 0.95
            self.row(300, 520, 1010, (82, 112), (170, 230), 48, seed=207, boxes=0.45, pointy=0.0, tower=0.0)
            self.row(520, 1190, 975, (82, 122), (230, 330), 48, seed=203, slope=-0.14, boxes=0.45)
            t.bunting((470, 760), (905, 690), sag=40, size=11, seed=3)
            t.bunting((600, 860), (1180, 780), sag=46, size=11, seed=4)

    # ------------------------------------------------------------------ the upper rows and the trees
    def upper(self):
        t = self.t
        with t.depth(0.16):
            t.lw = 1.1
            self.row(300, 1190, 1150, (100, 148), (280, 440), 60, seed=204, slope=-0.08, boxes=0.55)
        with t.depth(0.06):
            t.lw = 1.25
            self.row(300, 562, 1305, (118, 145), (320, 400), 70, seed=205, boxes=0.6, tower=0.0)
            self.row(858, 1190, 1295, (125, 175), (340, 440), 70, seed=206, boxes=0.6, tower=0.0)
        t.lw = 1.4
        t.tree(396, 1330, 520, 138, seed=22, clumps=13, lean=0.02)
        t.tree(1108, 1300, 525, 112, seed=21, clumps=11, lean=-0.02)
        t.lw = 1.25
        t.bunting((310, 1010), (1180, 930), sag=70, size=17, seed=6)

    # ------------------------------------------------------------------ the bridge-house, the steps, the square
    def steps(self):
        t = self.t
        # the glimpse through the archway: more steps going on up, a sunny wall, a pot, someone climbing
        t.lw = 1.0
        t.fill([(640, 1270), (780, 1270), (780, 1420), (640, 1420)], 'butter', tex=0.9)
        t.flush()
        t.stairs((648, 772, 1412), (686, 734, 1330), n=9, seed=31)
        t.pot(752, 1372, 14, 12, plant='flowers', flowers='red', seed=32)
        t.person(700, 1352, 26, coat='tomato', reflect=False, seed=33)
        # the bridge-house over the lane
        t.lw = 1.4
        self.bridge = t.house(560, 1412, 300, 400, 'mint', roof='mansard', roof_h=78, floors=5, cols=4, win_w=0.34,
                              boxes=0.7, flowers='red', shutters=None, ground='arch', arch_w=0.42, chimneys=2,
                              aerials=1.0, seed=34, frame='white', balconies=[(2, 1), (2, 2)])
        # the side walls of the houses flanking the lane, receding toward the vanishing point
        for (xa, xb, ya, yb, c) in ((600, 648, 1180, 1412, 'tomato'), (820, 772, 1150, 1412, 'yellow')):
            t.fill([(xa, ya), (xb, ya + (xb - xa) * 0.1), (xb, yb), (xa, PLAZA)], c, tex=0.9)
            t.fill([(xa, ya), (xb, ya + (xb - xa) * 0.1), (xb, yb), (xa, PLAZA)], '#2a2a40', alpha=0.25, tex=0)
            t.ink([(xb, ya + (xb - xa) * 0.1), (xb, yb)], 1.2)
        t.flush()
        t.lw = 1.5
        t.stairs((602, 818, PLAZA), (648, 772, 1412), n=15, seed=35, ratio=1.07)
        # low stone parapets along the steps, with iron rails on top
        t.parapet([(588, 1572), (640, 1370)], [(600, PLAZA), (648, 1412)], seed=36, course=10)
        t.parapet([(780, 1370), (832, 1572)], [(772, 1412), (820, PLAZA)], seed=37, course=10)
        t.railing([(594, 1566), (644, 1368)], 34, seed=38)
        t.railing([(776, 1368), (826, 1566)], 34, seed=39)
        t.cat(806, 1556, 26, seed=40)
        # the houses on the square
        t.lw = 1.6
        t.house(298, PLAZA, 158, 560, 'teal', roof='mansard', roof_h=72, floors=5, cols=2, win_w=0.46, boxes=0.6,
                ground='shop', shop='cream', sign='FLEURS', letters='teal_deep', awning=('teal_deep', 'ivory'), shutters=None, frame='cream',
                chimneys=1, seed=41, balconies=[(2, 0)])
        t.house(456, PLAZA, 146, 440, 'tomato', roof='gable', roof_h=130, floors=4, cols=2, win_w=0.44, boxes=0.6,
                ground='door', door_col='teal', shutters='mint', chimneys=1, seed=42, top_window='round')
        t.house(820, PLAZA, 156, 470, 'yellow', roof='hip', roof_h=66, floors=4, cols=2, win_w=0.44, boxes=0.65,
                ground='door', door_col='cobalt', shutters='cobalt', chimneys=1, seed=43, frame='white')
        t.house(976, PLAZA, 230, 600, 'coral', roof='mansard', roof_h=84, floors=5, cols=3, win_w=0.42, boxes=0.6,
                ground='shop', shop='cobalt', sign='PAIN', awning=('tomato', 'cream'), chimneys=2, seed=44,
                balconies=[(3, -1)], frame='cream')
        t.lw = 1.4
        t.bunting((456, 1170), (976, 1110), sag=78, size=24, seed=7)
        t.bunting((300, 1320), (600, 1395), sag=30, size=20, seed=8)

    # ------------------------------------------------------------------ the canyon walls
    def canyon(self):
        t = self.t
        t.lw = 2.0
        with t.plane(CANYON_SRC, CANYON_DST):
            t.house(0, 2200, 345, 2070, 'blush', roof=None, floors=8, cols=2, win_w=0.42, boxes=0.6, shutters=None,
                    ground='door', door_col='teal', stones=5, chimneys=0, aerials=0, seed=51, balconies=[(3, 0), (5, 1)])
            t.house(345, 2200, 300, 1880, 'white', roof='mansard', roof_h=170, floors=7, cols=2, win_w=0.44,
                    boxes=0.6, shutters='jade', ground='door', door_col='tomato', chimneys=2, aerials=1.0, seed=52,
                    dormers=1, chimney_col='brick', stones=4)
            t.house(645, 2200, 255, 1760, 'pale_yellow', roof='mansard', roof_h=170, floors=7, cols=2, win_w=0.44, boxes=0.55,
                    ground='shop', shop='teal_deep', chimneys=1, aerials=1.0, seed=53, dormers=1, chimney_col='cream')
            for i, (sx, sy, c) in enumerate(((150, 1930, 'butter'), (215, 1965, 'tomato'), (420, 1950, 'mint'),
                                             (470, 1915, 'pink'), (560, 1975, 'cerulean'))):
                t.poster(sx, sy, sx + 48, sy + 66, c, seed=55 + i)
        # the near house on the right, close to us
        t.lw = 2.1
        self.right = t.house(1180, NEAR_R, 380, 1830, 'ivory', roof='mansard', roof_h=150, floors=8, cols=3,
                             win_w=0.42, boxes=0.65, shutters='powder', shutter_p=0.3, ground='shop', shop='teal_deep', sign='CAFÉ',
                             awning=('teal', 'ivory'), stones=6, chimneys=1, seed=61, balconies=[(2, 0), (2, 1), (5, 0)],
                             curtains=0.5)

    # ------------------------------------------------------------------ roses, flowers, signs
    def flowers(self):
        t = self.t
        t.lw = 1.6
        # roses climbing the canyon wall, the corner by the steps, the near house and the bridge-house
        P = [canyon(x, y) for x, y in ((250, 2190), (268, 1900), (240, 1600), (275, 1300), (250, 1000), (280, 760))]
        t.roses(P, n=60, size=11, seed=71, colour='rose_pink', dark='rose_pink_dark', light='blossom_white')
        P = [canyon(x, y) for x, y in ((660, 2190), (680, 1950), (655, 1700), (690, 1500))]
        t.roses(P, n=30, size=6.5, seed=72, colour='rose_pink', dark='rose_pink_dark', light='blossom_white')
        t.roses([(826, 1630), (832, 1500), (826, 1380), (836, 1250)], n=34, size=7, seed=73)
        t.roses([(1196, 1890), (1205, 1700), (1196, 1500), (1210, 1300), (1200, 1120)], n=55, size=11, seed=74)
        t.roses([(566, 1410), (576, 1300), (566, 1190), (578, 1090)], n=22, size=5.5, seed=75)
        # the flower shop's buckets and pots along the square
        for i, x in enumerate((318, 344, 370, 396, 422)):
            t.pot(x, PLAZA + 6, 22, 20, plant='flowers', flowers=('pink', 'red', 'sunny', 'violet', 'white')[i], seed=80 + i)
        t.pot(600, PLAZA + 2, 30, 28, plant='bush', seed=86)
        t.pot(950, PLAZA + 4, 26, 24, plant='tall', seed=87)
        t.pot(1460, NEAR_R + 6, 34, 32, plant='bush', seed=89)
        for i, sx in enumerate((150, 320, 470, 600, 780)):
            x, y = canyon(sx, 2200)
            t.pot(x + 14, y - 4, 40 - i * 4, 36 - i * 4, plant=('flowers', 'bush', 'tall', 'flowers', 'bush')[i],
                  flowers=('red', 'pink', 'sunny', 'violet', 'red')[i], seed=95 + i)
        # hanging signs and a wall lamp
        t.lw = 1.8
        t.sign(1180, 1560, 30, 'tomato', icon='cup', side=-1, seed=90)
        x, y = canyon(330, 1700)
        t.sign(x, y, 26, 'jade', icon='key', side=1, seed=91)
        x, y = canyon(640, 1830)
        t.sign(x, y, 20, 'mustard', icon='loaf', side=1, seed=92)
        x, y = canyon(345, 1400)
        t.lamp(x + 46, y + 10, 40, wall=x, seed=93)

    # ------------------------------------------------------------------ the near bunting
    def bunting(self):
        t = self.t
        t.lw = 2.0
        t.bunting(canyon(250, 1000), (1190, 760), sag=170, size=40, seed=11)
        t.bunting(canyon(120, 760), (1190, 380), sag=200, size=50, seed=12)
        t.bunting(canyon(500, 1500), (1190, 1330), sag=90, size=32, seed=13)
        t.bunting(canyon(20, 1500), (1180, 1500), sag=150, size=56, seed=14)

    # ------------------------------------------------------------------ the wet square
    def street(self):
        t = self.t
        src = t.C.copy()
        poly = np.array([(1, 2000), (300, 1650), (300, PLAZA), (1180, PLAZA), (1180, NEAR_R), (1500, NEAR_R),
                         (1500, 2000)], np.float32)
        t.street(PLAZA, VP, poly=poly, seed=101)
        region = t.mask(poly, soft=0.8)
        t.reflect(src, base_line(), PLAZA, strength=0.58, region=region, seed=102)
        t.joints(alpha=0.28, seed=104)
        t.glints(PLAZA + 10, 2000, n=45, seed=103, region=region)

    # ------------------------------------------------------------------ people and the lamp post
    def people(self):
        t = self.t
        t.lw = 1.5
        with t.mirror(1800, 1080, 1160, 1430, strength=0.5):
            t.lamp(1120, 1800, 300, seed=110)
        with t.mirror(PLAZA + 30, 980, 1060, 1580, strength=0.45):
            t.bistro(1020, PLAZA + 30, 40, seed=115)
        for bx in (1240, 1450):
            t.bistro(bx, 1988, 60, seed=int(bx))
        with t.mirror(1700, 520, 640, 1600, strength=0.4):
            t.person(560, 1700, 82, coat='tomato', seed=116, facing=1, legs='#33384a')
            t.person(590, 1702, 76, coat='cream', seed=117, facing=1, hair='hair_light')
        with t.mirror(1830, 400, 560, 1580, strength=0.4):
            t.person(470, 1830, 104, coat='mustard', legs='#2f3c55', balloon='rose', seed=111, facing=1)
        with t.mirror(1760, 800, 980, 1600, strength=0.4):
            t.person(890, 1760, 120, coat='cobalt', umbrella='tomato', seed=112, facing=-1)
        with t.mirror(1958, 1260, 1440, 1780, strength=0.35):
            t.person(1348, 1958, 140, coat='jade', basket='red', seed=113, facing=-1, legs='#3a3340')
        t.person(690, 1610, 62, coat='coral', seed=114, facing=1)


PHASES = (('sky', 'sky'), ('far', 'far'), ('upper', 'upper'), ('steps', 'steps'), ('canyon', 'canyon'),
          ('flowers', 'flowers'), ('bunting', 'bunting'), ('street', 'street'), ('people', 'people'))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'colortown_festival_steps.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:10s} {time.time() - T0:5.1f}s')) if os.environ.get('CT_TIMING') else (lambda n: None)
    t = ColorTown(W, H, seed=12, keep_stages=bool(stages), stages_dir=stages)
    t.finish()
    t.paper()
    t.stage('paper')
    sc = Scene(t)
    tick('setup')
    for name, ph in PHASES[:-1]:
        getattr(sc, ph)()
        tick(name)
        t.stage(name)
    getattr(sc, PHASES[-1][1])()
    tick(PHASES[-1][0])
    t.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s', t.n_fills, 'fills', t.n_lines, 'lines')


if __name__ == '__main__':
    main()
