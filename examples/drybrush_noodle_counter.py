"""Example (dry-brush blocks): 面馆 · Noodle Counter -- a mid-century poster / gouache-collage illustration.

An old man with cropped white hair, rough black glasses and a white beard, in a navy work jacket, bent over a bowl
of noodles at a small eatery counter: one hand lifts the noodles with chopsticks, the other steadies the bowl.
Behind him a big sage-green roller slab; to his right, on the same counter, a vinegar bottle, a soy-sauce bottle and
a glass of tea in front of a teal block. A small vermilion square sits off to the side on the cream paper.

Painted the way the reference works: cream paper -> big slabs (green backdrop, teal block) -> the figure in a few
planes (jacket halves, sleeves) -> the head (skin planes, nose, cheek, ear, hair) -> details (glasses, beard,
chopsticks, the near hand) -> the still life (counter, bowl, noodles, the other hand, bottles, glass) -> the red
accent -> printed.
--stages writes those steps as snapshots for the draw-on. No image model.
python3 drybrush_noodle_counter.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from drybrush import DryBrushBlocks

W, H = 1600, 1200
COUNTER = 846                          # y of the counter top


class Scene:
    def __init__(self, d):
        self.d = d

    # ------------------------------------------------------------ 1 the big slabs
    def slabs(self):
        d = self.d
        d.backdrop((190, 78, 1132, 860), 'slab', seed=11)
        d.piece((1078, 372, 1336, 852), 'tealblue', torn=5, cut=0.7, angle=-90, load=1.0, dry=0.3, lane=60,
                scumble=0.07, direction=1, dry_from=(0.72, 0.95), seed=12)

    # ------------------------------------------------------------ 2 the figure in planes
    def figure(self):
        d = self.d
        self.J = d.jacket(neck=(640, 470), shoulders=(292, 528, 994, 540), bottom=COUNTER + 8, lit='tealblue',
                          shade='navy', dark='ink', shirt='cream', collar='navy', light=-1, lapel=0.18, open_=0.07, seed=21)
        # near arm (viewer's left): shoulder -> elbow on the counter -> hand up at the chopsticks
        d.sleeve([(350, 580), (300, 730), (330, 818), (420, 742), (458, 660)], 136, 96, 'navy', angle=-65,
                 mix=('tealblue', 0.22), stroke_len=120, passes=2, seed=22)
        # far arm (viewer's right): shoulder -> elbow -> forearm along the counter to the bowl
        d.sleeve([(946, 590), (1000, 750), (986, 826), (900, 834)], 130, 100, 'ink', angle=-112, mix=('navy', 0.3),
                 stroke_len=110, passes=2, seed=23)

    def head(self):
        d = self.d
        self.Hd = d.head(640, 300, 250, 300, tilt=3, turn=0.16, light=-1, skin='tan', lit='skin_light', shade='umber',
                         warm='tomato', ear='terracotta', hair='bone', hair_shade='ash', seed=31)

    def details(self):
        d = self.d
        d.glasses(self.Hd, colour='ink', lens=(0.34, 0.19), frame=0.07, seed=41)
        d.beard(self.Hd, colour='white', shade='bone', length=0.12, width=0.96, seed=42)
        # chopsticks from the near hand down into the bowl, then the hand over them
        d.stroke([(432, 628), (700, 752)], 9, 'bone', load=0.97, dry=0.2, square=0.9, seed=43)
        d.stroke([(450, 656), (708, 760)], 8, 'cream', load=0.97, dry=0.2, square=0.9, seed=44)
        d.hand(506, 680, 120, angle=30, cuff='cream', seed=45)

    # ------------------------------------------------------------ 3 the still life
    def still_life(self):
        d = self.d
        # counter top
        d.slab(d.poly([(140, COUNTER - 6), (1480, COUNTER - 10), (1482, COUNTER + 24), (138, COUNTER + 26)]), 'celadon',
               0, load=0.985, dry=0.5, lane=14, fringe=40, side=2, scumble=0.3, seed=51)
        d.slab(d.poly([(150, COUNTER + 24), (1470, COUNTER + 22), (1468, COUNTER + 32), (152, COUNTER + 34)]), 'ink', 0,
               load=0.9, dry=0.6, lane=8, fringe=50, side=1.5, scumble=0.4, alpha=0.85, seed=52)
        # the bowl, noodles, chili oil, scallion
        body, inner = d.bowl(716, 736, 344, 116, colour='white', band='teal', inside='ochre', shade='bone', seed=53)
        r = np.random.default_rng(54)
        for k in range(11):
            x = 600 + k * 22 + r.normal(0, 4)
            d.stroke([(x, 744 + r.normal(0, 3)), (x + r.normal(0, 22), 730), (x + 34 + r.normal(0, 10), 742)], 8,
                     'cream', load=0.92, dry=0.4, seed=55 + k)
        d.piece(d.poly([(668, 732), (740, 724), (786, 736), (730, 748), (660, 744)], smooth=True), 'vermilion', torn=5,
                cut=0.2, seed=66)
        for (x, y) in [(632, 734), (652, 742), (760, 730), (800, 738), (706, 728), (590, 740)]:
            d.accent(x, y - 4, 11, 'leaf', rot=r.uniform(-30, 30), h=8, seed=x)
        d.hand(860, 800, 104, angle=188, grip=False, seed=46)              # the other hand steadies the bowl
        # noodles hanging from the chopsticks
        for k, dx in enumerate((-8, -2, 4, 10)):
            d.stroke([(694 + dx, 744), (698 + dx + k, 730), (700 + dx, 714)], 5, 'cream', load=0.95, dry=0.3,
                     seed=70 + k)
        # bottles and a glass of tea in front of the teal block
        d.bottle(1152, COUNTER, 94, 372, 'forest', shoulder=0.4, neck=0.3, neck_w=0.36, dark='ink', light='sage',
                 label=('cream', 0.22, 0.5), label2=('vermilion', 0.18, 0.48, 0.18, 0.62), cap='ink', seed=80)
        d.bottle(1262, COUNTER, 84, 300, 'ink', shoulder=0.38, neck=0.3, neck_w=0.36, dark=None, light='teal',
                 label=('bone', 0.2, 0.42), label2=('vermilion', 0.55, 0.85, 0.2, 0.8), cap='vermilion', seed=81)
        d.cup(1378, COUNTER, 84, 164, 'celadon', glass=True, level=0.6, tea='khaki', seed=82)

    # ------------------------------------------------------------ 4 the accent
    def accents(self):
        d = self.d
        d.accent(1406, 950, 62, 'vermilion', seed=95)

    def finish(self):
        self.d.printed(1.0)


PHASES = ('slabs', 'figure', 'head', 'details', 'still_life', 'accents')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'drybrush_noodle_counter.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:12s} {time.time() - T0:5.1f}s')) if os.environ.get('DB_TIMING') else (lambda n: None)
    d = DryBrushBlocks(W, H, seed=7, keep_stages=bool(stages), stages_dir=stages)
    d.paper()
    d.stage('paper')
    sc = Scene(d)
    tick('setup')
    for ph in PHASES:
        getattr(sc, ph)()
        tick(ph)
        d.stage(ph)
    sc.finish()
    d.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out)


if __name__ == '__main__':
    main()
