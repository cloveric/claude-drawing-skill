"""Example (grainy picture book): 喂鸭子 · Feeding the Ducks -- a girl on a jetty at dusk, ducks paddling over.

A full-bleed 16:9 picture-book spread at dusk: a sky stepped from cobalt through a pale band to apricot and orange,
a tomato sun sinking behind the dark trees of the far bank, its light lying on the water in broken orange strokes;
on the left a wooden jetty runs out into a dusty-blue pond, and at its end a girl with long black hair, big round
black-and-white eyes and rosy cheeks sits with her legs dangling over the water, a paper bag on her lap, tossing
crumbs; three ducks paddle toward her, ripples spreading behind them; lily pads and reeds in the near corner, two
birds flying home. Every shape is laid with a dry, chalky, grainy brush; no ink outlines.

Drawn back to front; --stages writes a snapshot after each group (sky, far bank, water, jetty, girl, ducks,
reeds and lily pads, crumbs and birds). No image model.
python3 grainbook_duck_pond.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from grainbook import GrainBook


def scene(g, stage):
    W, H = g.W, g.H
    k = g.k
    r = np.random.default_rng(5)
    horizon = 452
    # ------------------------------------------------------------ dusk: cobalt -> pale -> apricot -> orange
    g.bands(g.full(), ['cobalt_deep', 'cobalt', 'dusty_light', 'apricot', 'orange_light'], [120, 215, 300, 370],
            angle=-8, streak=0.3, dry=0.35, edge=1.8, soft=2.4, wave=26 * k, period=300 * k, blend=46 * k)
    g.scumble(g.below(*g.wavy(-20, W + 20, 330, 14 * k, 400 * k)), 'orange_light', angle=-6, cover=0.35, alpha=0.7)
    g.stars(0, 0, W, 170, 12, colour='cream')
    sx, sy, sr = 1480, 398, 92
    g.fill(g.ellipse(sx, sy, sr), 'tomato', angle=0, streak=0.25, dry=0.15, dry_px=10 * k)
    stage('sky')
    # ------------------------------------------------------------ the far bank: dark trees against the glow
    xs, ys = g.wavy(-20, W + 20, horizon, 6 * k, 900 * k, seed=3)
    for x in np.arange(-40, W + 60, 64):
        hh = r.uniform(40, 95) * k * (1.4 if 1000 < x < 1350 or x < 300 else 1.0)
        g.fill(g.blob(x + r.uniform(-20, 20), horizon - hh * 0.3, r.uniform(48, 80) * k, hh * 0.55, rough=0.12),
               'pine_mid' if r.random() < 0.55 else 'pine', angle=-60, streak=0.25, dry=0.3, dry_px=8 * k)
    g.round_tree(250, horizon + 10, 190 * k * 0.75, 160 * k * 0.75, crown='green', light='moss', seed=4)
    g.round_tree(1160, horizon + 8, 220 * k * 0.75, 170 * k * 0.75, crown='pine_mid', light='green', seed=6)
    g.round_tree(1760, horizon + 8, 170 * k * 0.75, 140 * k * 0.75, crown='green', light='moss', seed=7)
    stage('far_bank')
    # ------------------------------------------------------------ the pond
    water = g.below(xs, ys + 4)
    g.bands(water, ['teal', 'dusty', 'dusty_light'], [570, 790], angle=0, streak=0.45, dry=0.3, edge=1.6, soft=2.0,
            wave=14 * k, period=260 * k, blend=60 * k)
    g.fill(water - g.below(*g.wavy(-20, W + 20, horizon + 40 * k, 8 * k, 200 * k, seed=12)), 'pine', angle=0,
           streak=0.4, dry=0.5, edge=1.4, alpha=0.7)                                                # the bank's reflection
    y = horizon + 26
    for i in range(10):                                                    # the sun lying on the water
        w = (190 - i * 13) * k * r.uniform(0.7, 1.1)
        x0 = sx + r.uniform(-30, 30) * k
        n = 1 if (i < 3 or r.random() < 0.5) else 2
        for part in range(n):
            xa = x0 if n == 1 else x0 + (part - 0.5) * w * 0.75
            ww = w if n == 1 else w * 0.55
            g.brush([(xa - ww / 2, y), (xa + ww / 2, y + r.uniform(-2, 2))], (7 + i * 0.45) * k,
                    'orange_light' if i % 3 else 'apricot', taper=(0.45, 0.45), dry=0.45, alpha=0.85)
        y += (22 + i * 5) * k * r.uniform(0.85, 1.15)
    stage('water')
    # ------------------------------------------------------------ the jetty, running in from the left
    top_y, front = 700, 742
    end = 760
    for px in (90, 330, 570, 735):                                        # posts and their wobbling reflections
        g.fill(g.rect(px - 13, front - 8, px + 13, front + 120), 'wood_dark', angle=90, dry=0.1, dry_px=4 * k)
        for j in range(4):
            yy = front + 130 + j * 26
            g.brush([(px - 14 + 6 * (-1) ** j, yy), (px + 14 + 6 * (-1) ** j, yy)], 9 * k, 'teal', taper=(0.2, 0.2),
                    dry=0.3, alpha=0.8)
    g.fill(g.poly([(-30, top_y + 6), (end, top_y), (end + 12, front), (-30, front + 8)]), 'wood_dark', angle=0,
           streak=0.4, dry=0.15)
    g.fill(g.poly([(-30, top_y - 30), (end - 22, top_y - 20), (end, top_y), (-30, top_y + 6)]), 'wood', angle=0,
           streak=0.45, dry=0.15)
    for x in np.arange(70, end, 95):                                       # plank seams
        g.crayon([(x, top_y - 22), (x + 6, top_y + 3)], 3.2 * k, 'wood_dark', taper=(0.1, 0.1), alpha=0.7)
    stage('jetty')
    # ------------------------------------------------------------ the girl at the end, legs over the water
    gx, gy, gh = 600, top_y - 6, 640
    g.shadow(g.ellipse(gx - 10, gy + 4, 130, 14), 'wood_dark', depth=0.5, edge=0.8)
    J = g.child(gx, gy, gh, facing=1, pose='sit',
                outfit=dict(coat='vermilion', legs='cream', boots='black', hair_style='long', hair='hair', hair_len=0.75,
                            scarf=None, mittens=None, eyes='big', turn=0.32, look=(0.7, 0.45), mouth='smile',
                            nose='button', brows=True, buttons='cream', collar='cream', eye_size=1.15),
                el_n=(0.24, -0.3), wr_n=(0.36, -0.34),
                hooks=dict(behind=lambda: g.bag(gx - 0.27 * gh, gy + 0.005 * gh, 0.13 * gh, 0.16 * gh, 'kraft')))
    # an open hand, palm up, just letting go of the crumbs: a small flat skin oval tipped forward
    hx, hy = J['wr_n']
    g.fill(g.blob(hx + 0.026 * gh, hy + 0.002 * gh, 0.036 * gh, 0.018 * gh, rough=0.04, rot=np.deg2rad(-12)), 'skin',
           angle=0, dry=0, edge=0.6)
    stage('girl')
    # ------------------------------------------------------------ the ducks paddling over
    for (x, y, s, f, c, wing) in ((1040, 860, 190, -1, 'cream', None), (1290, 800, 160, -1, 'cream', None),
                                  (1210, 940, 120, -1, 'brown_light', 'brown')):
        g.ripples(x + 0.25 * s, y + 0.04 * s, 1.2 * s, n=3, colour='ice', alpha=0.75)
        g.shadow(g.ellipse(x + 0.02 * s, y + 0.02 * s, 0.48 * s, 0.05 * s), 'teal', depth=0.6, edge=0.8)
        g.duck(x, y, s, f, colour=c, wing=wing)
    stage('ducks')
    # ------------------------------------------------------------ the near corner: lily pads and reeds
    for (x, y, rr) in ((1560, 1010, 70), (1690, 960, 52), (1450, 1060, 58), (1800, 1040, 62)):
        pad = g.ellipse(x, y, rr * k * 0.8, rr * k * 0.28) - g.poly([(x, y), (x + rr * k, y - rr * k * 0.12),
                                                                 (x + rr * k, y + rr * k * 0.12)])
        g.fill(pad, 'moss', angle=0, streak=0.35, dry=0.2, dry_px=4 * k)
    g.dots([(1580, 995)], 9 * k, 'cream')
    g.dots([(1580, 995)], 4 * k, 'mustard')
    g.reeds(1860, 1090, 420 * k * 0.75, n=6, colour='pine_mid', head='brown', spread=150, seed=9)
    g.reeds(60, 1095, 300 * k * 0.75, n=4, colour='pine', head='brown', spread=90, seed=10)
    stage('reeds')
    # ------------------------------------------------------------ crumbs in the air and two birds flying home
    t = np.linspace(0.15, 1, 9)
    ax, ay = hx + 0.03 * gh, hy - 0.02 * gh
    crumbs = np.stack([ax + t * 330 + r.uniform(-12, 12, 9), ay - 70 * np.sin(np.pi * t * 0.8) + t * 170 +
                       r.uniform(-10, 10, 9)], 1)
    g.dots(crumbs, r.uniform(3.5, 6, 9) * k, 'cream')
    g.ripples(ax + 340, ay + 190, 70, n=2, colour='ice', alpha=0.7)
    for (bx, by, bs) in ((820, 120, 26), (900, 160, 20)):
        g.crayon([(bx - bs, by - 0.25 * bs), (bx - bs * 0.45, by - 0.45 * bs), (bx, by)], 3.4 * k, 'navy',
                 taper=(0.2, 0.1))
        g.crayon([(bx, by), (bx + bs * 0.45, by - 0.45 * bs), (bx + bs, by - 0.25 * bs)], 3.4 * k, 'navy',
                 taper=(0.1, 0.2))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'grainbook_duck_pond.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    g = GrainBook(1920, 1080, seed=12, keep_stages=bool(stages), stages_dir=stages)
    g.finish()
    g.paper()
    g.stage('paper')
    scene(g, g.stage)
    g.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s')


if __name__ == '__main__':
    main()
