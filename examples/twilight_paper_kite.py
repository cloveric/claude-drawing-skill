"""Example (twilight storybook): 夜的边上 · The Kite at the Edge of Night -- one dreamy dusk picture-book page.

A small hooded wanderer in a blue felt cloak sits on the crest of a wildflower hill at dusk, flying a paper kite
toward the place where the sky turns to night. Left: a big pastel dusk (lavender, rose, peach, gold) with soft cloud
bands, thin streaks of light, a low pale sun sinking behind misty mauve ranges, a flock of birds and drifting
dandelion seeds. Right: the night has already come -- a field of stars, the Milky Way with its dark rift, a crescent
moon, a shooting star, one lit window in a cottage on the far hill. Between them, patchwork hills in pastel stripes
with tiny round trees, and in front a meadow of thousands of wildflowers that turns moonlit-blue on the night side.
A jar of fireflies glows beside the wanderer; fireflies drift up toward the dark. A circular "detail a" inset shows
the kite's lashed spar crossing and bridle knot as a fine technical drawing (hatching, a dimension, labels, a scale),
and two tiny lowercase captions: "the evening waits for us." and "just a little further."

Painted in order: dusk sky -> night -> hills -> meadow -> figures and kite -> lights -> the plate overlay and captions.
--stages writes those steps as snapshots for the draw-on. No image model.
python3 twilight_paper_kite.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from twilight import TwilightStorybook, hexc

W, H = 2000, 1100
HORIZON = 700
CREST = [(-20, 838), (300, 816), (650, 792), (950, 765), (1150, 750), (1255, 746), (1370, 751), (1600, 773),
         (1850, 797), (2020, 808)]
SEAT = (1255, 748)
KITE = (1436, 292)
KITE_SIZE, KITE_TILT = 120, 0.34
INSET = (930, 322, 132)


class Page:
    def __init__(self, t):
        self.t = t
        self.r = np.random.default_rng(5)

    # ------------------------------------------------------------ 1 the dusk sky
    def sky(self):
        t = self.t
        t.dusk_sky(horizon=HORIZON, seed=1)
        clouds = [(-60, 520, 104, 46, 'cloud', 0.62), (600, 1150, 70, 34, 'cloud', 0.55), (60, 700, 262, 30, 'cloud', 0.55),
                  (840, 1250, 228, 24, 'cloud', 0.5), (-40, 380, 392, 22, 'cloud_low', 0.5), (480, 980, 432, 24, 'cloud_low', 0.5),
                  (120, 640, 548, 14, 'cloud_low', 0.42), (780, 1180, 586, 12, 'cloud_low', 0.38)]
        for i, (x0, x1, y, h, c, a) in enumerate(clouds):
            t.cloud(x0, x1, y, h, c, a, seed=10 + i)
        for i, (x0, x1, y) in enumerate([(130, 470, 432), (610, 740, 436), (470, 650, 514), (60, 310, 562), (760, 1010, 590),
                                         (300, 540, 612), (900, 1060, 470)]):
            t.streak(x0, x1, y, seed=30 + i)
        t.sun(470, 674, 36)
        r = self.r
        flock = [(650 + 18 * i + r.normal(0, 6), 300 - 6 * i + r.normal(0, 5)) for i in range(7)]
        t.birds(flock + [(300, 212), (322, 204), (338, 216)], size=6.5, seed=40)
        seeds = [(r.uniform(140, 1150), r.uniform(470, 660)) for _ in range(12)] + [(1170, 640), (1205, 610), (1140, 700)]
        t.seeds(seeds, size=8.5, seed=41)

    # ------------------------------------------------------------ 2 night comes in from the right
    def night(self):
        t = self.t
        t.night_split([(1200, -60), (1330, 120), (1440, 300), (1530, 520), (1575, 720), (1590, 1100)], soft=185, ground=0.88, seed=50)
        t.night_sky(seed=51)
        t.milky_way((1575, -70), (2060, 640), width=150, bend=-40, stars=3800, seed=52)
        t.stars(2300, sparkles=6, dusk=0.025, seed=53)
        t.moon(1838, 196, 25, phase=0.27, tilt=-0.4)
        t.shooting_star((1988, 318), (1878, 372))

    # ------------------------------------------------------------ 3 hills
    def hills(self):
        t = self.t
        t.hills([(-20, 676), (220, 660), (470, 668), (720, 650), (980, 664), (1240, 646), (1520, 662), (1780, 648), (2020, 660)],
                colour='#c9b1a8', base=780, fade=0.45, seed=60)
        t.hills([(-20, 700), (180, 684), (400, 694), (650, 676), (900, 690), (1150, 678), (1420, 690), (1700, 672), (2020, 688)],
                colour='mauve_dark', base=800, fade=0.4, rim='rim', rim_alpha=0.25, seed=61)
        t.mist(652, 698, 760, 'haze', 0.3, seed=62)
        info = t.striped_hill([(-20, 748), (230, 722), (470, 740), (720, 712), (980, 734), (1200, 708), (1440, 726), (1660, 704),
                               (1900, 728), (2020, 716)], base=H, fade=0.35, hedge=0.45, seed=63)
        # tiny round trees along the field edges, a few standing alone
        r = self.r
        ry, b = info['ridge'], info['bounds']
        pts = []
        for k in range(1, 6):
            for x in r.uniform(0, W, 9 - k):
                pts.append((x, ry[int(x)] + b[k] + r.uniform(-1, 2)))
        for x in (120, 182, 420, 455, 760, 1040, 1080, 1610, 1835, 1870):
            pts.append((x, ry[x] + r.uniform(4, 10)))
        t.trees(pts, size=6.0, seed=64)
        self.cottage(1702, ry[1702] + 9)

    def cottage(self, x, y):
        """a tiny cottage on the night-side hill with one lit window"""
        t = self.t
        w, h = 16, 10
        t.shapes([np.array([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)])], '#d8c9bb', 1)
        t.shapes([np.array([(x - w / 2 - 2, y - h), (x + w / 2 + 2, y - h), (x + 2, y - h - 8), (x - 2, y - h - 8)])], '#8a5a52', 1)
        t.shapes([np.array([(x + 4, y - h - 4), (x + 6.5, y - h - 4), (x + 6.5, y - h - 10), (x + 4, y - h - 10)])], '#6e5f5c', 1)
        with t.unlit():
            t.shapes([np.array([(x - 4, y - 3), (x - 0.5, y - 3), (x - 0.5, y - 7), (x - 4, y - 7)])], '#ffd98a', 1)
            t.glow(x - 2.2, y - 5, 9, 'lantern', 0.35)

    # ------------------------------------------------------------ 4 the meadow
    def meadow(self):
        t = self.t
        info = t.meadow(CREST, density=1.0, grass=1.0, seed=70)
        crest = info['crest']
        t.grass_heads(1060, 1240, lambda x: crest[x.astype(int)], n=16, height=(26, 58), lean=0.12, seed=73)
        t.grass_heads(1330, 1520, lambda x: crest[x.astype(int)], n=18, height=(26, 62), lean=0.18, seed=74)
        t.grass_heads(600, 900, lambda x: crest[x.astype(int)], n=10, height=(14, 30), lean=0.1, width=0.7, seed=75)
        t.butterfly(420, 905, 9, '#e99a3d', angle=0.25, seed=71)
        t.butterfly(790, 958, 8, '#f2d67a', tip='#7c6a3c', angle=-0.35, open_=0.8, seed=72)
        t.butterfly(1120, 880, 7, '#a9c4ef', tip='#3f4f7a', angle=0.1, seed=76)
        t.dragonfly(612, 872, 22, angle=0.18)
        t.dragonfly(1010, 1000, 26, angle=-0.25)

    # ------------------------------------------------------------ 5 the wanderer, the lantern, the kite
    def figures(self):
        t = self.t
        sx, sy = SEAT
        shoulder = np.array([sx + 0.2 * 88, sy - 0.36 * 88])
        reach = np.array(KITE) - shoulder
        t.jar_lantern(1322, 752, 30, seed=80)
        self.hand = t.wanderer(sx, sy, 88, facing=1, reach=reach, seed=81)
        self.knot = t.kite(KITE[0], KITE[1], KITE_SIZE, KITE_TILT, seed=82)
        t.kite_string(self.hand, self.knot, sag=46)

    # ------------------------------------------------------------ 6 lights: fireflies, the lantern pool
    def lights(self):
        t = self.t
        r = self.r
        pts = []
        for _ in range(46):
            pts.append((r.normal(1450, 230), r.normal(840, 110)))
        for _ in range(14):
            pts.append((r.uniform(1250, 1760), r.uniform(430, 700)))
        for _ in range(8):
            pts.append((r.normal(1320, 50), r.normal(720, 40)))
        for _ in range(7):
            pts.append((r.uniform(200, 1150), r.uniform(820, 1060)))
        pts = [(x, y) for x, y in pts if 0 < x < W and 380 < y < H - 30]
        t.fireflies(pts, size=1.0, trails=4, seed=90)

    # ------------------------------------------------------------ 7 the plate: detail a, captions
    def plate(self):
        t = self.t
        cx, cy, R = INSET
        t.inset(cx, cy, R, draw=draw_knot, target=KITE, label='detail a', sub='not to scale', size=26, leader_colour='#3d383f')
        t.caption(112, 162, 'the evening waits for us.', 34, 'caption', 0.9, seed=100)
        t.caption(1892, 94, 'just a little further.', 27, '#d9d1d4', 0.85, anchor='r', seed=101)


def draw_knot(t, cx, cy, r):
    """detail a: the lashed spar crossing and the bridle knot, as a fine technical drawing at the kite's tilt"""
    a = -0.38
    ca, sa = np.cos(a), np.sin(a)
    K = np.array([cx + 4, cy - 10], np.float32)                        # where the spars cross
    L = lambda u, v: K + np.array([u * ca - v * sa, u * sa + v * ca], np.float32)
    poly = lambda *uv: np.array([L(u, v) for u, v in uv], np.float32)
    ink, wood, cordc = '#4a4248', '#6b4f3a', '#f1e8d4'
    big = r + 70
    deg = np.degrees(a)
    # the paper sail behind: four panels in faint washes; the coral ones hatched like a plate
    quads = [poly((0, 0), (-big, 0), (-big, -big), (0, -big)), poly((0, 0), (0, -big), (big, -big), (big, 0)),
             poly((0, 0), (big, 0), (big, big), (0, big)), poly((0, 0), (0, big), (-big, big), (-big, 0))]
    for q, c in zip(quads, ('#f2e1c4', '#eca58f', '#e8d6b9', '#e6957f')):
        t.wash(q, c, alpha=0.45, seed=200)
    for i, q in ((1, quads[1]), (3, quads[3])):
        t.hatch(q, angle=deg + 45, spacing=6.5, width=0.5, colour='#9a5a50', alpha=0.38, seed=201 + i)
    t.hatch(quads[3], angle=deg - 45, spacing=9, width=0.45, colour='#9a5a50', alpha=0.22, seed=205)
    # a dowel: tan wash, outline, a few axis-parallel shading lines on the shadow flank, faint grain
    def dowel(along_v, half, lines_at):
        if along_v:
            body = poly((-half, -big), (half, -big), (half, big), (-half, big))
            edge = [poly((-half, -big), (-half, big)), poly((half, -big), (half, big))]
            shade = [poly((o, -big), (o, big)) for o in lines_at]
            grain = [poly((-half * 0.5 + k * half * 0.45, -big), (-half * 0.45 + k * half * 0.45, big)) for k in range(2)]
        else:
            body = poly((-big, -half), (big, -half), (big, half), (-big, half))
            edge = [poly((-big, -half), (big, -half)), poly((-big, half), (big, half))]
            shade = [poly((-big, o), (big, o)) for o in lines_at]
            grain = [poly((-big, -half * 0.4 + k * half * 0.5), (big, -half * 0.45 + k * half * 0.5)) for k in range(2)]
        t.wash(body, '#dcbb8f', alpha=0.9, edge=0.2, seed=210 + int(along_v))
        t.lines(grain, 0.45, '#8a6a4e', 0.4, wobble=0.9)
        t.lines(shade, 0.55, wood, 0.6, wobble=0.15)
        t.lines(edge, 1.15, ink, 0.9, wobble=0.25)
    dowel(True, 7.5, (3.6, 5.0, 6.0, 6.7))
    dowel(False, 6.5, (2.8, 4.1, 5.0, 5.7))
    # the lashing: four wraps each way across the crossing, each a cord with twist ticks
    def cord(p0, p1, w=4.0, ticks=True):
        p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
        u = (p1 - p0) / (np.linalg.norm(p1 - p0) + 1e-6); n = np.array([-u[1], u[0]], np.float32)
        t.shapes([np.array([p0 + n * w / 2, p1 + n * w / 2, p1 - n * w / 2, p0 - n * w / 2], np.float32)], cordc, 1, lit=False)
        t.lines([[p0 + n * w / 2, p1 + n * w / 2], [p0 - n * w / 2, p1 - n * w / 2]], 0.7, ink, 0.85)
        if ticks:
            Ln = float(np.linalg.norm(p1 - p0))
            t.lines([[p0 + u * s_ - n * w * 0.42 - u * 1.1, p0 + u * s_ + n * w * 0.42 + u * 1.1] for s_ in np.arange(2.4, Ln - 1, 2.9)],
                    0.42, ink, 0.5)
    for k in (-1.5, -0.5, 0.5, 1.5):
        cord(L(-15 + k * 4.2, -13 - k * 4.2), L(15 + k * 4.2, 13 - k * 4.2))
    for k in (-1.5, -0.5, 0.5, 1.5):
        cord(L(-15 + k * 4.2, 13 + k * 4.2), L(15 + k * 4.2, -13 + k * 4.2))
    # the finishing knot: two small loops and the cut tails
    kn = L(19, 17)
    for ang in (0.5, -0.9):
        th = np.linspace(0, 2 * np.pi, 30)
        lp_ = np.stack([kn[0] + np.cos(th) * 5.5 * np.cos(ang) - np.sin(th) * 3 * np.sin(ang),
                        kn[1] + np.cos(th) * 5.5 * np.sin(ang) + np.sin(th) * 3 * np.cos(ang)], 1)
        t.lines([lp_], 2.6, ink, 0.85); t.lines([lp_], 1.2, cordc, 1.0)
    cord(kn + (3, 4), kn + (10, 16), w=3.2); cord(kn + (5, 1), kn + (17, 6), w=3.2)
    # the bridle: a leg from the crossing to a lark's-head loop; the flying line leaves toward the flyer
    lp = L(-46, 74)
    cord(L(-3, 9), lp + np.array([5, -7], np.float32), w=3.2)
    th = np.linspace(0, 2 * np.pi, 40)
    loop = np.stack([lp[0] + np.cos(th) * 10 * np.cos(1.0) - np.sin(th) * 5 * np.sin(1.0),
                     lp[1] + np.cos(th) * 10 * np.sin(1.0) + np.sin(th) * 5 * np.cos(1.0)], 1)
    t.lines([loop], 3.0, ink, 0.85)
    t.lines([loop], 1.4, cordc, 1.0)
    cord(lp + np.array([-4, 8], np.float32), lp + np.array([-70, 130], np.float32), w=3.2)
    # labels, a diameter callout, a dimension and a scale, like a plate
    s_ = L(7.5, -84)
    t.lines([[s_ + (2, -1), s_ + (22, -14)]], 0.6, ink, 0.8)
    t.caption(float(s_[0] + 25), float(s_[1] - 12), 'spar', 16, ink, 0.9, seed=220)
    q = L(15, -14)
    t.lines([[q + (2, -3), (cx + 22, cy - 52)]], 0.6, ink, 0.8)
    t.caption(cx + 24, cy - 52, 'lashing, ×4', 16, ink, 0.9, seed=221)
    t.dimension(L(-7.5, -60), L(7.5, -60), 'ø 6', tick=4.4, colour=ink, width=0.65, size=15, across=True, lead=26)
    t.lines([[lp + (-9, -2), (cx - 36, cy + 56)]], 0.6, ink, 0.8)
    t.caption(cx - 38, cy + 61, 'bridle knot', 15, ink, 0.9, anchor='r', seed=222)
    t.ruler(cx + 22, cy + r * 0.5, cx + 70, h=8, step=4, colour=ink, labels=[(0, '0'), (10, '1 cm')], size=12)


PHASES = ('sky', 'night', 'hills', 'meadow', 'figures', 'lights', 'plate')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'twilight_paper_kite.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:10s} {time.time() - T0:5.1f}s')) if os.environ.get('TW_TIMING') else (lambda n: None)
    t = TwilightStorybook(W, H, seed=12, keep_stages=bool(stages), stages_dir=stages)
    t.finish(grain=1.0, vignette=1.0, bloom=0.8, edge=14)          # applied at render, so every snapshot matches
    pg = Page(t)
    for ph in PHASES:
        getattr(pg, ph)()
        tick(ph)
        if ph != PHASES[-1]: t.stage(ph)
    t.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out)


if __name__ == '__main__':
    main()
