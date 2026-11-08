"""Example (sunlit greenery): 溪边石阶 · Steps Down to the Stream -- a clear forest stream in summer light.

A 9:16 phone wallpaper in the anime background-painting / digital gouache manner: two leafy trees frame a window of
clean blue sky with a small cumulus; under them a flight of pale stone steps climbs a green bank between sunlit
bushes, dappled with leaf shadows; in front a clear stream -- a pebbled bed seen through transparent teal, the trees,
the sky and the stones mirrored in broken horizontal strokes -- with sun-bleached white boulders standing in it,
warm cream on top and cool blue-grey in the shade, moss on their crowns and a ripple line where they meet the water;
a branch of big leaves leans in from the right. No outlines, no image model: every leaf is a flat painted shape.
--layout page (1152 x 2048, the wallpaper) or wide (1920 x 1080: the same place laid out 16:9, for the draw-on GIF
and for video); --stages DIR writes a snapshot after each step (blank, sky, far woods, the bank and steps, bushes
and grass, trunks and canopy, the water, the boulders -- then the final with the near branch).
python3 sunlitgreen_stream_steps.py [out.jpg] [--layout page|wide] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from sunlitgreen import SunlitGreen

# Every layout: canvas, the waterline, the sky (bottom y), the cloud, two rows of far woods, the bank outline, the
# steps (bottom centre, top centre, widths, count), bushes on either side, bank rocks, trunks and limbs, the canopy
# clumps overhead, the boulders in the stream and the near branch.
LAYOUTS = {
    'page': dict(
        size=(1152, 2048), line=1260, sky_y1=1000, cloud=(560, 560, 280, 120),
        far=[dict(y=760, dy=120, x0=-40, step=80, n=16, r=(90, 110), far=0.42, leaf=8),
             dict(y=950, dy=80, x0=-40, step=95, n=13, r=(100, 110), far=0.25, leaf=9)],
        bank=[(-10, 860), (180, 800), (380, 740), (560, 760), (760, 860), (1160, 900)],
        steps=dict(n=10, x0=520, x1=310, w0=330, w1=140, rise=480),
        bush_l=[(60, 900, 170, 120, 0.05), (220, 1010, 120, 80, 0.06), (130, 1130, 170, 100, 0.08), (300, 1190, 90, 60, 0.1),
                (330, 870, 70, 50, 0.04), (300, 770, 90, 50, 0.03)],
        bush_r=[(700, 980, 120, 90, 0.04), (870, 940, 190, 130, 0.02), (1060, 1000, 170, 130, 0.04), (760, 1150, 140, 90, 0.08),
                (1000, 1170, 170, 90, 0.1), (560, 830, 60, 45, 0.02)],
        grass=[(250, 760, -6, 46, 420), (0, 1152, 4, 38, 800)],
        bank_rocks=[(150, -8, 160, 62), (930, -6, 200, 72), (690, -2, 80, 30)],
        trunks=[([(70, 1270), (90, 900), (60, 500), (90, 0)], 120, 80, '#5f6460', '#a3a49a'),
                ([(980, 1180), (1000, 800), (960, 400), (990, 0)], 60, 40, '#6a6c66', '#acab9f')],
        limbs=[([(80, 520), (260, 380), (420, 300)], 30, 12, '#5f6460', '#a3a49a'),
               ([(985, 600), (840, 470), (720, 420)], 24, 10, '#6a6c66', '#acab9f')],
        canopy=[(80, 120, 260, 200, 0.05), (300, 60, 230, 150, 0.0), (180, 330, 200, 140, 0.08), (420, 260, 140, 100, 0.04),
                (1000, 120, 240, 200, 0.02), (840, 60, 200, 130, 0.0), (1040, 400, 180, 160, 0.06), (860, 330, 150, 110, 0.05),
                (40, 560, 150, 160, 0.1), (1110, 650, 120, 140, 0.12)],
        water=dict(pebbles=320, pebble_size=34, stroke=(150, 10)),
        boulders=[(300, 1430, 160, 70), (820, 1520, 190, 85), (160, 1860, 230, 120), (1010, 1930, 200, 120), (600, 1700, 120, 50)],
        branch=[[(1190, 760), (1080, 820), (960, 900), (860, 990)], [(1190, 760), (1110, 900), (1050, 1010)],
                [(1190, 690), (1050, 680), (930, 720)], [(1190, 860), (1120, 1000), (1100, 1120)]], branch_leaf=88),
    'wide': dict(
        size=(1920, 1080), line=690, sky_y1=560, cloud=(1120, 250, 260, 110),
        far=[dict(y=420, dy=70, x0=-40, step=90, n=24, r=(90, 80), far=0.42, leaf=7),
             dict(y=530, dy=50, x0=-40, step=105, n=20, r=(100, 70), far=0.25, leaf=8)],
        bank=[(-10, 520), (500, 470), (760, 420), (980, 440), (1300, 500), (1930, 520)],
        steps=dict(n=8, x0=900, x1=780, w0=260, w1=120, rise=235),
        bush_l=[(560, 520, 150, 90, 0.05), (690, 590, 100, 60, 0.06), (600, 660, 150, 60, 0.08), (430, 600, 140, 80, 0.06),
                (760, 470, 60, 40, 0.03), (790, 440, 70, 40, 0.03)],
        bush_r=[(1040, 560, 110, 70, 0.04), (1180, 530, 170, 100, 0.02), (1350, 580, 160, 90, 0.04), (1120, 660, 130, 50, 0.08),
                (960, 450, 50, 35, 0.02)],
        grass=[(680, 1100, -4, 34, 300), (0, 1920, 3, 30, 1100)],
        bank_rocks=[(440, -6, 150, 52), (1300, -5, 180, 60), (1060, -2, 70, 26)],
        trunks=[([(330, 700), (345, 500), (320, 250), (340, 0)], 90, 66, '#5f6460', '#a3a49a'),
                ([(1560, 650), (1575, 450), (1545, 220), (1565, 0)], 56, 40, '#6a6c66', '#acab9f')],
        limbs=[([(335, 260), (480, 170), (620, 120)], 24, 10, '#5f6460', '#a3a49a'),
               ([(1560, 300), (1430, 210), (1320, 180)], 20, 8, '#6a6c66', '#acab9f')],
        canopy=[(330, 90, 300, 150, 0.05), (590, 40, 240, 110, 0.0), (180, 260, 220, 120, 0.08), (520, 200, 140, 80, 0.04),
                (60, 120, 160, 160, 0.04), (1560, 90, 300, 150, 0.02), (1330, 40, 240, 100, 0.0), (1720, 260, 220, 130, 0.06),
                (1400, 210, 150, 80, 0.05), (1870, 120, 140, 150, 0.04), (90, 420, 140, 130, 0.1), (1840, 470, 120, 120, 0.12)],
        water=dict(pebbles=420, pebble_size=28, stroke=(150, 8)),
        boulders=[(640, 780, 150, 56), (1250, 820, 170, 66), (300, 960, 210, 90), (1560, 990, 190, 90), (920, 920, 110, 40)],
        branch=[[(1960, 380), (1850, 430), (1740, 490), (1650, 560)], [(1960, 380), (1880, 500), (1830, 600)],
                [(1960, 320), (1830, 310), (1720, 340)], [(1960, 460), (1900, 580), (1890, 680)]], branch_leaf=78),
}


def scene(g, L, stage):
    W, H = g.W, g.H
    LINE = L['line']
    r = np.random.default_rng(4)
    # ---- sky and the far woods
    g.sky(top='#2470d0', mid='#4a93e0', bottom='#b0d6f0', y0=0, y1=L['sky_y1'], mid_at=0.45)
    cx, cy, cw, ch = L['cloud']
    g.cloud(cx, cy, cw, ch, seed=6)
    stage('sky')
    for j, F in enumerate(L['far']):
        cl = [(F['x0'] + i * F['step'] + r.random() * 30, F['y'] + r.random() * F['dy'], F['r'][0] + r.random() * 40,
               F['r'][1] + r.random() * 30, 0.03 + 0.02 * j) for i in range(F['n'])]
        g.canopy(cl, leaf=F['leaf'], far=F['far'], seed=5 + 3 * j, holes=0.45 - 0.15 * j, fill=1.0)
    stage('far_woods')
    # ---- the far bank: a green slope with stone steps set into it
    slope = g.face(L['bank'] + [(W + 10, LINE + 6), (-10, LINE + 6)], '#6b9e55', wobble=2)
    g.gradient(slope, '#5e9450', '#86b45c', axis=0, p0=min(p[1] for p in L['bank']), p1=LINE)
    g.strokes(slope, n=int(300 * W * H / 2.36e6), size=40, var=0.06, angle=-20, seed=13)
    S = L['steps']
    n = S['n']
    stp = np.zeros((H, W), np.float32)
    sc = g.k / 1.152
    for i in reversed(range(n)):
        t = i / (n - 1)
        f = t ** 0.85
        cx_ = S['x0'] + (S['x1'] - S['x0']) * f + 18 * sc * np.sin(i * 1.7)
        wd = S['w0'] + (S['w1'] - S['w0']) * f
        yb = LINE - 6 - S['rise'] * (1 - (1 - t) ** 1.3)
        rh, td = (28 - 15 * f) * sc, (34 - 21 * f) * sc
        sk = (r.random() - 0.5) * 8 * sc
        riser = [(cx_ - wd / 2, yb - rh + sk), (cx_ + wd / 2, yb - rh - sk), (cx_ + wd / 2 - 3, yb), (cx_ - wd / 2 + 3, yb)]
        tread = [(cx_ - wd / 2 + 6, yb - rh - td + sk * 0.6), (cx_ + wd / 2 - 6, yb - rh - td - sk * 0.6),
                 (cx_ + wd / 2, yb - rh - sk), (cx_ - wd / 2, yb - rh + sk)]
        g.face([(cx_ - wd / 2 - 4, yb - 2), (cx_ + wd / 2 + 4, yb - 2), (cx_ + wd / 2, yb + 5), (cx_ - wd / 2, yb + 5)],
               '#3f6e46', alpha=0.6)
        f_, t_, _ = g.box(front=riser, top=tread, tones=('#d9c3ad', 'stone_sun', 'stone_shade'), wobble=1.6, seed=40 + i)
        stp = np.maximum(stp, np.maximum(f_, t_))
    g.dapple(stp, cover=0.42, leaf=15, squash=0.55, scale=4, seed=12)
    g.dapple(slope * (1 - stp), cover=0.5, leaf=15, squash=0.55, scale=4, seed=14, tint=(0.6, 0.72, 0.84))
    stage('steps')
    # ---- bushes along both sides of the steps, grass, rocks on the bank
    for j, side in enumerate(('bush_l', 'bush_r')):
        g.canopy(L[side], leaf=13, seed=21 + j, holes=0.15, fill=0.6, glint=0.5, hole_colour='#3e7a52')
    for (x0, x1, dy, h, nn) in L['grass']:
        g.grass(x0, x1, LINE + dy, h, n=nn, seed=23 + int(x0))
    for i, (x, dy, rx, ry) in enumerate(L['bank_rocks']):
        g.rock(x, LINE + dy, rx, ry, seed=60 + i, moss=0.5)
    stage('bushes')
    # ---- trunks and the canopy overhead, with sky holes
    for i, (path, w0, w1, c, lt) in enumerate(L['trunks']):
        g.limb(path, w0, w1, colour=c, lit=lt, bark=0.8, seed=71 + i)
    for path, w0, w1, c, lt in L['limbs']:
        g.limb(path, w0, w1, colour=c, lit=lt)
    g.canopy(L['canopy'], leaf=21, seed=26, holes=1.0, fill=0.15, sub=2.6, glint=0.6, mottle=0.3, twigs=12, airy=1.0,
             levels=(0.0, 0.36, 0.5, 0.63, 0.76))
    stage('canopy')
    # ---- the stream: pebbled bed, transparent teal, broken reflections
    g.water((0, LINE, W, H), line=LINE, seed=9, ripple=5, reflect=0.9, near_reflect=0.32, reflect_scale=1.4, density=1.0,
            **L['water'])
    stage('water')
    rocks = np.zeros((H, W), np.float32)
    for i, (x, y, rx, ry) in enumerate(L['boulders']):
        rocks = np.maximum(rocks, g.rock(x, y, rx, ry, seed=80 + i, moss=0.25 if i % 2 else 0.0, wet='water'))
    g.dapple(rocks, cover=0.4, leaf=20, scale=5, seed=88)
    stage('boulders')
    # ---- a branch of big leaves leaning in over the water
    g.spray(L['branch'], leaf=L['branch_leaf'], width=0.42, rosette=(5, 7), along=0.42, seed=91, bend=0.06)


def main():
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    layout, stages = opt('--layout', 'page'), opt('--stages', None)
    name = 'sunlitgreen_stream_steps' + ('' if layout == 'page' else '_wide')
    out = a[0] if a and not a[0].startswith('--') else name + '.jpg'
    L = LAYOUTS[layout]
    T0 = time.time()
    W, H = L['size']
    g = SunlitGreen(W, H, seed=33, keep_stages=bool(stages), stages_dir=stages, light=(-0.5, -0.75, 0.45))
    g.finish()
    g.stage('blank')
    scene(g, L, g.stage)
    g.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s')


if __name__ == '__main__':
    main()
