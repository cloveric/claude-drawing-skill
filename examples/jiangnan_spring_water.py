"""Example (Jiangnan garden): 春水园林 · Spring Water Garden -- a lush, finely painted spring garden in one wide view.

Seen through a frame of pink blossom and hanging willow strands: a still jade lake across the middle of the picture
with soft reflections; a zigzag stone bridge with pierced balustrades crossing it toward a whitewashed garden wall,
whose moon gate shows a glimpse of another, sunlit garden behind (bamboo, a pink tree, a rock); next to it a
waterside teahouse with a grey-tiled hip-and-gable roof and upturned flying corners, jade lattice doors and windows,
a hanging lattice frieze, a pair of red lanterns and a small plaque, 听雨 (listening to the rain); a little wooden
boat tied below a white blossom tree at the stone steps; lily pads with pink water lilies, an egret on a stepping
stone and another skimming the water; a big weeping willow on the far bank; hazy blue-green hills behind; a tiny red
seal in the corner.

Painted back to front: sky and hills -> distant trees and haze -> buildings -> the garden on the far bank -> water
and reflections -> bridge and boat -> lily pads and egrets -> foreground foliage -> the hanging frame -> details.
--stages writes those steps as snapshots for the draw-on. No image model.
python3 jiangnan_spring_water.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from jiangnan import JiangnanGarden

W, H = 1920, 1080
BRIDGE = [(-11.5, 15.0), (-5.0, 19.5), (-8.4, 24.5), (-6.6, 29.6)]


def bank_line():
    """the waterline of the far bank, per column (the teahouse platform stands a little nearer)"""
    x = np.arange(W, dtype=np.float32)
    b = 592 + 3 * np.sin(x / 61.0) + 2 * np.sin(x / 23.0 + 1.3)
    b = np.where((x > 866) & (x < 1454), 606.0, b)
    b = np.where(x >= 1454, 598 + 2 * np.sin(x / 41.0), b)
    return b.astype(np.float32)


class Garden:
    def __init__(self, g):
        self.g = g
        self.bank = bank_line()

    # ------------------------------------------------------------ 1 sky and hills
    def sky_hills(self):
        g = self.g
        g.sky(top='#7ea4c0', bottom='#cfdcd6', y1=470, clouds=0.8, seed=1)
        g.hills([(-40, 236), (180, 200), (420, 168), (640, 214), (860, 176), (1090, 150), (1320, 190), (1560, 158),
                 (1780, 196), (1960, 182)], base=500, colour='#86a6a6', far=0.66, seed=2)
        g.haze(200, 400, 520, strength=0.35, seed=3)
        g.hills([(-40, 330), (260, 288), (560, 312), (860, 266), (1180, 300), (1500, 262), (1760, 296), (1960, 282)],
                base=500, colour='#7a9a90', far=0.48, seed=4)
        g.haze(330, 460, 520, strength=0.45, seed=5)

    # ------------------------------------------------------------ 2 distant and back trees
    def far_trees(self):
        g = self.g
        r = np.random.default_rng(10)
        for i, x in enumerate(np.arange(-40, 1980, 80)):
            y = 445 + r.uniform(-16, 8)
            g.foliage(g.crown(x, y, r.uniform(110, 170), r.uniform(50, 80), n=8, seed=100 + i), 'far', leaf=(2.5, 4.5),
                      density=0.9, far=0.6, highlights=0.4, edge=0.6, seed=200 + i)
        g.haze(380, 470, 540, strength=0.35, seed=6)
        # a band of canopy behind the garden, in several depths: bluer and softer the further back
        back = [(380, 380, 'jade'), (520, 360, 'far'), (700, 390, 'jade'), (1500, 380, 'jade'), (1660, 360, 'far'),
                (1840, 380, 'jade'), (40, 380, 'jade'), (200, 360, 'far')]
        for i, (x, y, rp) in enumerate(back):
            g.foliage(g.crown(x, y, r.uniform(180, 240), r.uniform(120, 170), n=14, seed=250 + i), rp, leaf=(2.6, 4.6),
                      density=1.0, far=0.4, highlights=0.6, seed=260 + i)
        g.haze(300, 440, 560, strength=0.2, seed=8)
        # the trees right behind the wall and the teahouse: different kinds, sizes and greens
        specs = [(450, 352, 210, 150, 'jade', 0.0), (640, 318, 250, 190, 'spring', 0.05),
                 (1000, 262, 280, 230, 'spring', 0.06), (1190, 214, 320, 240, 'jade', 0.0), (1385, 262, 250, 230, 'olive', 0.04),
                 (1560, 318, 230, 190, 'jade', 0.0), (1735, 288, 270, 230, 'deep', 0.0), (1890, 318, 220, 240, 'spring', -0.03),
                 (100, 320, 260, 220, 'jade', 0.0)]
        for i, (x, y, w, h, rp, lt) in enumerate(specs):
            K = g.crown(x, y, w, h, n=24, size=(0.15, 0.34), seed=300 + i)
            g.foliage(K, rp, leaf=(3.0, 5.4), density=1.15, far=0.3, light=lt, seed=400 + i)
        g.haze(330, 470, 600, strength=0.2, seed=7)
        # a garden pine behind the wall, its flat tiers of needles
        g.pine(([(842, 430), (836, 360), (850, 290), (838, 220)], 16, 7),
               [([(840, 330), (790, 318), (752, 300)], 6, 3), ([(846, 290), (900, 270), (930, 262)], 5, 2.5),
                ([(838, 250), (812, 230), (790, 222)], 4, 2)],
               [(760, 300, 70, 26), (915, 262, 64, 24), (800, 222, 58, 22), (846, 190, 50, 22), (852, 350, 80, 30)],
               far=0.22, seed=410)

    # ------------------------------------------------------------ 3 buildings
    def glimpse(self, m):
        g = self.g
        g.fill(m, '#d9e6e2')
        g.foliage(g.crown(640, 470, 200, 90, n=8, seed=51), 'spring', leaf=(3, 6), far=0.05, light=0.18, seed=52)
        g.blossom_tree([], g.crown(690, 482, 70, 50, n=5, seed=53), 'pink', petal=(2.4, 4), light=0.15, seed=54)
        g.wall(560, 506, 730, 556, 'plaster', stains=0.2, damp=0.3, seed=55)
        g.coping(556, 734, 506, h=10, seed=56)
        yy = np.arange(H, dtype=np.float32)[:, None]
        g.fill(((yy > 553) & (yy < 580)).astype(np.float32) * np.ones((1, W), np.float32), '#cfc8b6')
        g.rock(690, 552, 13, 20, seed=57)
        for k, x in enumerate((596, 604, 611, 618)):
            g.stroke([(x, 556), (x + 2, 500), (x + 5, 456)], 2.2, 1.4, colour='#6f8f45')
        g.foliage(np.array([[600, 470, 22, 26], [612, 498, 20, 22], [596, 520, 16, 18]], np.float32), 'spring',
                  leaf=(5, 8), aspect=0.28, droop=0.9, far=0.05, light=0.12, seed=58)
        g.haze(440, 580, None, colour='#f4efe0', strength=0.12, seed=59)

    def buildings(self):
        g = self.g
        # garden wall with the moon gate and a round leak window
        g.wall(358, 423, 905, 578, 'plaster', seed=60)
        g.stonework(358, 568, 905, 580, course=(12, 12), block=(40, 80), damp=0.2, seed=61)
        g.round_window(640, 515, 62, ring=7, inside=self.glimpse, ground=571, reveal=5)
        g.round_window(805, 486, 27, ring=6, pattern='ice', cell=10, back='#dfe4dc')
        g.dapple(358, 423, 905, 572, amount=0.32, scale=22, cover=0.55, falloff=(380, 380, 330), seed=65)
        g.dapple(700, 423, 905, 572, amount=0.22, scale=18, cover=0.6, falloff=(840, 380, 200), seed=66)
        g.coping(352, 910, 423, h=22, seed=62)
        # the teahouse
        g.stonework(866, 569, 1454, 607, course=(12, 13), block=(40, 90), damp=0.5, seed=63)
        yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None]
        g.fill(((yy > 404) & (yy < 569) & (xx > 893) & (xx < 1427)).astype(np.float32), '#1c2522')
        for x0, x1 in ((907, 1061), (1259, 1413)):
            g.wall(x0, 524, x1, 569, 'plaster', stains=0.1, damp=0.6, seed=int(x0))
            g.stonework(x0, 561, x1, 569, course=(8, 8), block=(30, 60), seed=int(x0) + 1)
            xm = (x0 + x1) / 2
            g.lattice(x0, 446, xm, 524, 'lantern', cell=10, bar=1.9, frame=3.5, back='paper')
            g.lattice(xm, 446, x1, 524, 'lantern', cell=10, bar=1.9, frame=3.5, back='paper')
        for i in range(4):
            a = 1075 + i * 42.5
            g.lattice(a, 444, a + 42.5, 569, 'grid', cell=9, bar=1.7, frame=3.2, kind='door', seed=70 + i)
        for x0, x1 in ((907, 1061), (1075, 1245), (1259, 1413)):
            g.fretwork(x0, x1, 424, h=16, cell=7)
        g.beam(893, 1427, 408, 424)
        for x in (900, 1068, 1252, 1420):
            g.column(x, 408, 569, 13)
        g.roof(1160, 292, 398, 360, 668, upturn=50, flare=32, rows=52, courses=15, ridge_h=18, soffit=10, shadow=46, seed=64)
        g.plaque(1160, 432, 92, 28, '听雨')
        for x in (1036, 1284):
            g.lantern(x, 404, h=36, cord=12)

    # ------------------------------------------------------------ 4 the garden on the far bank
    def garden(self):
        g = self.g
        b = self.bank
        # the far bank behind the big willow, then the willow
        for i, (x, y, w, h) in enumerate(((60, 540, 200, 110), (230, 560, 180, 70))):
            g.foliage(g.crown(x, y, w, h, n=10, seed=520 + i), 'jade', leaf=(3.5, 6), far=0.18, seed=530 + i)
        trunk = ([(246, 600), (258, 530), (284, 440), (300, 360)], 36, 18)
        boughs = [([(298, 370), (240, 310), (150, 285), (40, 300)], 10, 3), ([(300, 360), (340, 305), (430, 280), (520, 305)], 10, 3),
                  ([(296, 380), (210, 340), (110, 345), (10, 375)], 8, 3), ([(300, 350), (300, 295), (270, 258), (200, 250)], 8, 3),
                  ([(302, 360), (380, 330), (460, 340), (500, 375)], 7, 3)]
        crown = g.crown(270, 280, 470, 150, n=14, seed=80)
        g.willow(trunk, boughs, strands=1100, length=(120, 300), ramp_='willow', leaf=(3.0, 5.2), far=0.1, sway=0.3,
                 tips=590, crown=crown, gap=2.3, splay=(0.06, 0.3), crown_anchor=0.3, seed=81)
        # the far banks left of the wall and right of the teahouse: shrubs and small trees down to the water
        for i, (x, y, w, h, rp) in enumerate(((1530, 520, 220, 130, 'jade'), (1700, 505, 260, 150, 'deep'), (1880, 515, 230, 150, 'jade'),
                                              (1470, 560, 120, 60, 'spring'), (1800, 565, 200, 60, 'spring'))):
            g.foliage(g.crown(x, y, w, h, n=12, size=(0.2, 0.42), seed=500 + i), rp, leaf=(3.5, 6), far=0.16, seed=510 + i)
        # bank stones and low planting
        r = np.random.default_rng(90)
        for x in (372, 430, 520, 780, 840):
            g.rock(x + r.uniform(-8, 8), b[int(x)] - 6, r.uniform(16, 26), r.uniform(9, 13), seed=int(x))
        g.foliage(np.array([[400, 566, 40, 22], [455, 572, 34, 18], [530, 570, 30, 16], [770, 568, 36, 20], [845, 566, 40, 22]], np.float32),
                  'deep', leaf=(4, 7), far=0.08, seed=91)
        g.blossom_tree([], np.array([[420, 560, 26, 14], [790, 562, 22, 12]], np.float32), 'azalea', petal=(2.4, 4.0), leaves=0.3, seed=92)
        g.reeds(860, 905, lambda x: b[x.astype(int)] - 2, n=26, height=(16, 34), seed=93)
        # potted plants on the platform
        for x, col, kind in ((935, 'porcelain', 'deep'), (1232, 'terracotta', 'azalea'), (1300, 'terracotta', 'spring'), (1440, 'porcelain', 'deep')):
            rx, ry = g.pot(x, 569, 22, 18, col, band='#5a7fa8' if col == 'porcelain' else None)
            if kind == 'azalea':
                g.foliage(np.array([[rx, ry - 9, 15, 10]], np.float32), 'deep', leaf=(3, 5), seed=int(x))
                g.blossom_tree([], np.array([[rx, ry - 10, 14, 8]], np.float32), 'azalea', petal=(2, 3.4), leaves=0.2, seed=int(x) + 1)
            else:
                g.foliage(np.array([[rx - 5, ry - 10, 11, 10], [rx + 6, ry - 12, 11, 11], [rx, ry - 20, 9, 9]], np.float32), kind, leaf=(3, 6), seed=int(x))
        # steps down to the water and the white blossom tree with its bank
        g.stonework(1454, 590, 1920, 600, course=(10, 10), block=(40, 70), damp=0.4, seed=94)
        g.steps(1462, 1520, 569, n=4, rise=6.0, tread=3.4, grow=2.5, seed=95)
        g.foliage(np.array([[1560, 578, 40, 20], [1640, 582, 50, 18], [1760, 578, 46, 22], [1880, 576, 52, 24]], np.float32),
                  'deep', leaf=(4, 7), far=0.06, seed=96)
        branches = [([(1612, 598), (1606, 520), (1590, 450), (1560, 380)], 16, 6), ([(1606, 520), (1660, 450), (1720, 400)], 10, 4),
                    ([(1595, 470), (1520, 420), (1480, 380)], 8, 3), ([(1590, 450), (1610, 360), (1640, 310)], 7, 3)]
        g.blossom_tree(branches, g.crown(1630, 400, 380, 250, n=16, seed=97), 'white', petal=(3.2, 5.6), density=1.0, far=0.06, seed=98)
        g.reeds(1530, 1600, lambda x: b[x.astype(int)] - 1, n=24, height=(18, 36), seed=99)
        g.dapple(1300, 560, 1520, 608, amount=0.3, scale=14, cover=0.5, falloff=(1560, 560, 260), seed=100)

    # ------------------------------------------------------------ 5 water
    def water(self):
        g = self.g
        b = self.bank
        src = g.C.copy()
        g.lake(int(b.min()) - 2, H, bank=b, seed=110)
        g.reflect(b, strength=0.82, blur=(2.0, 8.0), ripple=2.4, src=src, seed=111)
        g.ripples((0, int(b.min()), W, H), n=900, light='#dcebe6', dark='#2f6358', alpha=0.28, seed=112)

    # ------------------------------------------------------------ 6 bridge and boat
    def bridge_boat(self):
        g = self.g
        g.bridge(BRIDGE, width=1.5, deck=0.32, rail=0.5, post=1.9, reflection=True, rails='rear', seed=120)
        before = g.layer()
        g.bridge(BRIDGE, width=1.5, deck=0.32, rail=0.5, post=1.9, rails='rear', seed=121)
        on_bridge = (np.abs(g.C - before).max(-1) > 0.01).astype(np.float32)
        g.dapple(0, 560, 560, 760, amount=0.3, scale=16, cover=0.55, falloff=(220, 560, 400), mask=on_bridge, seed=124)
        before = g.layer()
        g.boat(1478, 1748, 629, h=22, seed=122)
        g.reflect_layer(before, 629, (1460, 560, 1770, 629), strength=0.7, seed=123)
        g.stroke([(1488, 612), (1500, 596), (1506, 588)], 1.4, 1.2, colour='#6b5a40')

    # ------------------------------------------------------------ 7 lily pads, lotus, egrets
    def pads_egrets(self):
        g = self.g
        r = np.random.default_rng(130)
        pads = []
        for cx_, cz, n in ((0.6, 8.6, 16), (2.6, 9.6, 13), (3.9, 8.0, 9), (-0.9, 11.2, 8), (1.6, 12.6, 7), (4.4, 11.6, 6)):
            for _ in range(n):
                pads.append((cx_ + r.normal(0, 0.55), cz + r.normal(0, 0.8), r.uniform(0.12, 0.27)))
        flowers = [(0.2, 9.0, 0.22), (1.6, 8.0, 0.26), (2.9, 10.5, 0.2), (3.8, 8.6, 0.24), (-0.8, 11.5, 0.18), (1.0, 12.4, 0.17)]
        g.lily_pads(pads, flowers=flowers, seed=131)
        # an egret on a stepping stone, and one skimming the water
        x, y = g.project(3.2, 0.0, 15.0)
        g.rock(float(x), float(y) - 4, 22, 9, seed=132)
        before = g.layer()
        g.egret(float(x) - 2, float(y) - 9, s=78, pose='stand', facing=-1, seed=133)
        g.reflect_layer(before, float(y) - 2, (x - 60, y - 100, x + 60, y - 2), strength=0.6, seed=134)
        g.egret(770, 300, s=58, pose='fly', facing=1, seed=135)
        g.petals((300, 640, 1500, 1060), n=160, kind='white', size=(2.5, 4.5), water=True, seed=136)

    # ------------------------------------------------------------ 8 foreground foliage
    def foreground(self):
        g = self.g
        K = np.array([[60, 980, 160, 110], [250, 1010, 170, 100], [430, 1040, 140, 90], [-20, 880, 120, 140],
                      [140, 900, 120, 90], [330, 950, 120, 80], [560, 1070, 120, 60]], np.float32)
        g.foliage(K, 'deep', leaf=(10, 18), density=1.0, droop=0.3, veins=True, seed=140)
        g.blossom_tree([], np.array([[150, 905, 70, 40], [300, 960, 60, 34], [40, 860, 50, 40]], np.float32), 'white',
                       petal=(4, 6.5), density=0.8, leaves=0.25, gaps=0.5, seed=143)
        g.reeds(380, 660, lambda x: 1084 - 0.0 * x, n=34, height=(70, 170), ramp_='deep', lean=0.32, width=0.07, seed=144)
        K2 = np.array([[1660, 900, 130, 110], [1820, 860, 140, 140], [1960, 940, 140, 160], [1560, 1000, 140, 100],
                       [1760, 1010, 160, 100], [1920, 1050, 120, 80]], np.float32)
        g.foliage(K2, 'deep', leaf=(10, 18), density=1.0, droop=0.3, veins=True, seed=141)
        g.blossom_tree([], np.array([[1700, 880, 90, 60], [1830, 830, 100, 70], [1640, 960, 80, 50], [1880, 940, 90, 70]], np.float32),
                       'pink', petal=(5, 9), density=0.9, leaves=0.2, seed=142)

    # ------------------------------------------------------------ 9 the hanging frame
    def frame(self):
        g = self.g
        boughs = [([(-60, -40), (80, -24), (220, -20), (360, -44)], 10, 4), ([(-60, -30), (40, -16), (140, -22)], 7, 3)]
        g.willow(None, boughs, strands=34, length=(240, 660), ramp_='willow', leaf=(12, 19), far=0.0, sway=0.2,
                 light=-0.2, gap=6.5, stem=1.3, bundle=(1, 3), spread=14, splay=(0.18, 0.5), aspect=0.22, seed=150)
        g.blossom_branch([(1960, 150), (1820, 110), (1660, 140), (1520, 100), (1360, 128), (1250, 112)], 20, 4, 'pink', flowers=120,
                         spread=32, size=(14, 23), twigs=9, seed=151)
        g.blossom_branch([(1940, -20), (1840, 40), (1760, 30)], 10, 3, 'pink', flowers=26, spread=24, size=(13, 19), seed=152)
        g.petals((1000, 0, 1920, 760), n=80, kind='pink', size=(4, 8), seed=153)

    def details(self):
        g = self.g
        g.seal(1858, 990, 24, 44, '春水')
        g.grain(1.0)


PHASES = ('sky_hills', 'far_trees', 'buildings', 'garden', 'water', 'bridge_boat', 'pads_egrets', 'foreground', 'frame')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'jiangnan_spring_water.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:12s} {time.time() - T0:5.1f}s')) if os.environ.get('JN_TIMING') else (lambda n: None)
    g = JiangnanGarden(W, H, seed=8, keep_stages=bool(stages), stages_dir=stages)
    g.camera(horizon=450, eye=3.0, focal=1400)
    sc = Garden(g)
    for ph in PHASES:
        getattr(sc, ph)()
        tick(ph)
        g.stage(ph)
    sc.details()
    g.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out)


if __name__ == '__main__':
    main()
