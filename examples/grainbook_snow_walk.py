"""Example (grainy picture book): 雪夜遛狗 · The Evening Walk -- a child walking a little dog home in the snow.

A full-bleed picture-book page on a snowy blue evening: a cobalt sky stepped from navy at the top to bright cobalt at
the hills, falling snow; a red cottage on the rise with lit windows, its chimney smoking, feathery pines around it and
small blue firs along the far ridge; on the peach snow in front, a child in a bright blue coat, a red knitted hat and
a mustard scarf walks a ginger dog on a red lead along a trodden path, footprints behind them, flat mauve shadows
under them and the windows' light lying on the snow. Every shape is laid with a dry, chalky, grainy brush; no ink
outlines -- only a few dark crayon accents (window bars, the lead, the mouth).

Drawn back to front; --stages writes a snapshot after each group (sky, ridge, cottage and pines, the ground, the
child, the dog, the lead and shadows, the falling snow). --layout wide arranges the same page as a 1920 x 1080
spread (used for the draw-on GIF). No image model.
python3 grainbook_snow_walk.py [out.jpg] [--stages DIR] [--layout page|wide]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from grainbook import GrainBook

LAYOUTS = {
    # canvas, horizon of the far ridge, cottage (x, ground, w, h, depth), pines [(x, ground, h, w)], far firs band,
    # child (x, ground, h), dog (x, ground, size), path control points
    'page': dict(size=(1600, 2000), sky=[300, 620, 900], ridge=1120, rise=1260,
                 house=(1010, 1230, 300, 260, 260), pines=[(1470, 1290, 980, 520), (720, 1250, 560, 300),
                                                          (110, 1420, 1100, 560)],
                 firs=(0, 1600, 1105, 95), child=(540, 1860, 800), dog=(1010, 1890, 330),
                 moon=(330, 250, 70),
                 bushes=[(1500, 2010, 230, 330), (60, 2015, 190, 260)]),
    'wide': dict(size=(1920, 1080), sky=[150, 330, 500], ridge=600, rise=690,
                 house=(1260, 680, 230, 200, 210), pines=[(1700, 760, 720, 400), (1040, 700, 400, 220),
                                                         (130, 840, 780, 420)],
                 firs=(0, 1920, 590, 66), child=(690, 990, 470), dog=(990, 1010, 200),
                 moon=(420, 130, 46),
                 bushes=[(1860, 1090, 170, 240), (360, 1095, 120, 170)]),
}


def scene(g, L, stage):
    W, H = g.W, g.H
    k = g.k
    r = np.random.default_rng(11)
    # ------------------------------------------------------------ the sky: stepped navy -> bright cobalt
    sky = g.full()
    g.bands(sky, ['navy', 'cobalt_deep', 'cobalt', 'cobalt_bright'], L['sky'], angle=-12, streak=0.3, dry=0.35,
            edge=1.8, soft=2.4, wave=46 * k, period=360 * k)
    g.mottle(g.above(*g.wavy(-20, W + 20, L['sky'][1], 30 * k, 500 * k)), 'cobalt_deep', scale=160 * k, cover=0.3,
             angle=-12, streak=0.35, alpha=0.75)
    g.mottle(g.below(*g.wavy(-20, W + 20, L['sky'][1], 30 * k, 500 * k)), 'cobalt', scale=170 * k, cover=0.25,
             angle=-10, streak=0.35, alpha=0.7)
    mx, my, mr = L['moon']
    g.moon(mx, my, mr, 'cream', halo=0, crescent=0.42)
    stage('sky')
    # ------------------------------------------------------------ the far ridge and its little firs
    xs, ys = g.wavy(-20, W + 20, L['ridge'], 22 * k, 900 * k, seed=5)
    ridge = g.below(xs, ys)
    g.fill(ridge, 'snow_shade', angle=-5, streak=0.4, dry=0.3)
    x0, x1, yb, fh = L['firs']
    for x in np.sort(r.uniform(x0, x1, 22)):
        yy = np.interp(x, xs, ys) + 6 * k
        hh = fh * r.uniform(0.6, 1.15)
        g.fir_far(x, yy, hh, colour='dusty_dark' if r.random() < 0.5 else 'dusty', seed=int(r.integers(1 << 30)))
    xs2, ys2 = g.wavy(-20, W + 20, L['rise'], 34 * k, 1300 * k, seed=8, slope=-0.04)
    rise = g.below(xs2, ys2)
    stage('ridge')
    # ------------------------------------------------------------ the cottage and the pines behind / beside it
    hx, hy, hw, hh, hd = L['house']
    pines = L['pines']
    px, py, ph, pw = pines[0]
    g.pine(px, py, ph, pw, colour='pine', light='pine_mid', snow='snow_light', seed=21)
    px, py, ph, pw = pines[1]
    g.pine(px, py, ph, pw, colour='pine_mid', light='green', snow='snow_light', seed=22)
    g.fill(rise, 'snow', angle=-6, streak=0.45, dry=0.3, mottle=0.2)
    g.scumble(rise, 'snow_light', angle=-6, cover=0.36)
    H_ = g.house(hx, hy, hw, hh, depth=hd, seed=31)
    g.smoke(*H_['chimney'], 260 * k, colour='ice', n=3, drift=0.35, alpha=0.6, seed=3)
    px, py, ph, pw = pines[2]
    g.pine(px, py, ph, pw, colour='pine', light='pine_mid', snow='snow_light', seed=23)
    stage('cottage')
    # ------------------------------------------------------------ the near snow and the trodden path
    xs3, ys3 = g.wavy(-20, W + 20, L['rise'] + 0.18 * (H - L['rise']), 30 * k, 1100 * k, seed=9, slope=0.05)
    near = g.below(xs3, ys3)
    g.fill(near, 'snow', angle=-4, streak=0.45, dry=0.3, mottle=0.25)
    g.scumble(near, 'snow_light', angle=-4, cover=0.42)
    # the snow is uneven: loose, slightly darker patches lying across it
    g.mottle(near, '#e9a9a0', scale=230 * k, cover=0.28, angle=-4, streak=0.3, alpha=0.55, seed=60)
    for (bx, by, bh, bw) in L['bushes']:
        g.shrub(bx, by, bh, bw, 'pine', light='pine_mid', snow='snow_light', seed=int(bx))
    stage('ground')
    # ------------------------------------------------------------ the child, walking the dog home
    cx, cy, ch = L['child']
    dx, dy, ds = L['dog']
    # footprints behind them
    fp = [(cx - ch * (0.22 + 0.17 * i), cy + ch * (0.02 + 0.03 * i) + (8 * k if i % 2 else -8 * k)) for i in range(6)]
    g.footprints(fp, 0.035 * ch, depth=0.6)
    g.footprints([(dx - ds * (0.7 + 0.28 * i), dy + ds * 0.02 * i + (5 * k if i % 2 else -5 * k)) for i in range(5)],
                 0.035 * ds, depth=0.5)
    g.shadow(g.blob(cx - 0.06 * ch, cy + 0.01 * ch, 0.27 * ch, 0.035 * ch, rough=0.1), 'shadow', depth=0.9,
             angle=0, edge=1.2)
    J = g.child(cx, cy, ch, facing=1, pose='walk',
                outfit=dict(coat='cobalt_bright', sleeve='#1668bd', legs='navy', boots='brick', hair_style='bob',
                            hat='mustard', hat_band='cream', scarf='vermilion', mittens='vermilion', eyes='dot',
                            turn=0.45, look=(0.5, 0.0), buttons='cream'),
                el_n=(0.2, -0.55), wr_n=(0.29, -0.47))
    stage('child')
    g.shadow(g.blob(dx - 0.05 * ds, dy + 0.01 * ds, 0.45 * ds, 0.05 * ds, rough=0.1), 'shadow', depth=0.9,
             angle=0, edge=1.2)
    D = g.dog(dx, dy, ds, facing=1, colour='orange', patch='cream', collar='vermilion')
    stage('dog')
    # ------------------------------------------------------------ the lead, sagging between hand and collar
    a = np.array(J['wr_n']) + (0.012 * ch, 0.01 * ch)
    b = np.array(D['collar'])
    t = np.linspace(0, 1, 20)[:, None]
    lead = a * (1 - t) + b * t + np.array([0, 1]) * (np.sin(np.pi * t) * 0.07 * ch)
    g.crayon(lead, 4.5 * k, 'vermilion', taper=(0.05, 0.05), wobble=0.5)
    stage('lead')
    # ------------------------------------------------------------ falling snow over everything
    face = J['face']['head']
    g.snow(0, 0, W, H, int(0.00006 * W * H), r=(2.4 * k, 5.2 * k), colour='cream', avoid=face, seed=41)
    g.snow(0, 0, W, H * 0.6, int(0.000012 * W * H), r=(5 * k, 7 * k), colour='white', alpha=0.85, avoid=face,
           seed=42)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'grainbook_snow_walk.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    layout = sys.argv[sys.argv.index('--layout') + 1] if '--layout' in sys.argv else 'page'
    T0 = time.time()
    L = LAYOUTS[layout]
    W, H = L['size']
    g = GrainBook(W, H, seed=7, keep_stages=bool(stages), stages_dir=stages)
    g.finish()
    g.paper()
    g.stage('paper')
    scene(g, L, g.stage)
    g.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s')


if __name__ == '__main__':
    main()
