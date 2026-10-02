"""Example (watercolour): Wash backgrounds / 水彩底纹 — broad directional washes (graded density, hard dried rims,
back-run blooms, granulation, splatters) in indigo / ochre-to-burnt-sienna / sage / teal on white cold-press paper,
leaving open paper in the middle. Made as backgrounds for an explainer video: crisp UI cards sit on top of the paint
(Opus 5.5 cost explainer, 2026-09). Two layouts; change the seed, or mirror / rotate the image, for more variants.
Pure code, no image model.
python3 watercolor_washes.py [out.png] [--layout cover|bill] [--seed N] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from watercolor import Watercolor, hexc
from core import blob_pts, spline, fbm1d

INDIGO, INDIGO_D = hexc('#3a4c9a'), hexc('#232d66')
TEAL = hexc('#2b8a8a')
OCHRE, SIENNA = hexc('#dca448'), hexc('#ad4c28')
SAGE = hexc('#86a883')


def blob(p, cx, cy, rx, ry, rot=0.0, rough=0.25, soft=3.0, ragged=0.3):
    return p.shape(blob_pts(cx, cy, rx, ry, rough=rough, n=140, seed=p._seed(), rot=rot), soft=soft, ragged=ragged)


def sweep(p, ctrl, w0, w1, rough=0.22, soft=3.0, ragged=0.35):
    """one broad flat-brush pass along a spline; width w0 -> w1, wobbly rims, rounded ends"""
    c = spline(ctrl, 24)
    n = len(c)
    t = np.linspace(0, 1, n)
    w = (w0 + (w1 - w0) * t) * np.sin(np.pi * t) ** 0.45
    d = np.gradient(c, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1) / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-6)
    a = 1 + rough * fbm1d(n, n / 5, 4, p._seed())
    b = 1 + rough * fbm1d(n, n / 5, 4, p._seed())
    pts = np.vstack([c + nrm * (w * a)[:, None], (c - nrm * (w * b)[:, None])[::-1]])
    return p.shape(pts, soft=soft, ragged=ragged)


def grade(p, x0, y0, x1, y1, lo=0.35, hi=1.0):
    """density ramp: `hi` at (x0, y0) fading to `lo` at (x1, y1) — pigment pooled toward one end"""
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((p.XX - x0) * dx + (p.YY - y0) * dy) / (dx * dx + dy * dy), 0, 1)
    return hi + (lo - hi) * t


def cover(seed=5302):
    p = Watercolor(1920, 1080, seed=seed, paper_tone='#fdfbf6')
    p.paper()
    p.stage('paper')
    # thin ochre pass across the top-left, fading to the right (just a warm breath above the title card)
    p.glaze(sweep(p, [(-120, 150), (300, 70), (760, 40), (1060, 60)], 150, 50) * grade(p, 0, 100, 1060, 60, 0.2, 1), OCHRE, 0.5, edge=0.8, gran=0.5)
    p.stage('ochre_breath')
    # ochre -> burnt sienna pool, bottom-left, sienna dropped in wet
    och = sweep(p, [(-160, 690), (220, 780), (560, 960), (820, 1160)], 300, 230)
    p.glaze(och * grade(p, 0, 1000, 700, 700, 0.55, 1), OCHRE, 0.72, edge=0.8, gran=0.55, bloom=2)
    p.glaze(blob(p, 120, 1000, 380, 190, rough=0.3, soft=26, ragged=0.5) * np.clip(och * 1.2, 0, 1), SIENNA, 0.62, edge=0.2, gran=0.6)
    p.stage('ochre_sienna')
    # sage band along the bottom, overlapping the ochre (mixes to olive where they cross)
    p.glaze(sweep(p, [(1560, 1160), (1150, 980), (760, 920), (420, 960)], 190, 120), SAGE, 0.66, edge=0.75, gran=0.45, bloom=1)
    p.stage('sage')
    # the big indigo sweep from the top-right corner diagonally down (ultramarine granulates hard)
    ind = sweep(p, [(2120, -120), (1760, 170), (1420, 400), (1100, 560)], 470, 190, rough=0.2)
    p.glaze(ind * grade(p, 1920, 0, 1150, 560, 0.5, 1), INDIGO, 0.85, edge=0.8, gran=0.8, bloom=3, variation=0.35)
    p.glaze(blob(p, 1860, 80, 470, 300, rough=0.3, soft=38, ragged=0.5) * np.clip(ind * 1.3, 0, 1), INDIGO_D, 0.55, edge=0.1, gran=0.65)
    p.stage('indigo')
    # teal pass along the lower rim of the indigo -> deep blue-green overlap
    p.glaze(sweep(p, [(2050, 560), (1700, 690), (1330, 770), (1000, 800)], 150, 90) * grade(p, 1920, 600, 1000, 800, 0.5, 1), TEAL, 0.7, edge=0.8, gran=0.55, bloom=1)
    # sage echo near the top, ochre spark inside the indigo (complementary glint)
    p.glaze(blob(p, 1190, 95, 170, 80, rot=0.35, rough=0.35, soft=3), SAGE, 0.5, edge=0.7, gran=0.4)
    p.glaze(blob(p, 1560, 620, 90, 55, rot=-0.3, rough=0.35, soft=10, ragged=0.45), OCHRE, 0.55, edge=0.4, gran=0.5)
    p.stage('teal_accents')
    # splatters
    p.splatter(INDIGO, n=44, box=(980, 0, 1900, 760), size=(1.5, 6), strength=0.75)
    p.splatter(INDIGO, n=7, box=(1050, 30, 1850, 700), size=(8, 14), strength=0.55)
    p.splatter(SIENNA, n=30, box=(20, 680, 900, 1060), size=(1.5, 5.5), strength=0.75)
    p.splatter(TEAL, n=16, box=(1100, 640, 1800, 1000), size=(1.5, 5), strength=0.6)
    p.splatter(OCHRE, n=10, box=(40, 20, 900, 150), size=(1.5, 4), strength=0.6)
    return p


def bill(seed=7708):
    p = Watercolor(1920, 1080, seed=seed, paper_tone='#fdfbf6')
    p.paper()
    # sage pass behind the receipt (left), teal dropped in wet at the bottom
    sg = sweep(p, [(-160, 330), (240, 470), (640, 690), (980, 1150)], 330, 260)
    p.glaze(sg * grade(p, 0, 900, 900, 380, 0.5, 1), SAGE, 0.72, edge=0.8, gran=0.5, bloom=2)
    p.glaze(blob(p, 250, 900, 420, 230, rough=0.3, soft=28, ragged=0.5) * np.clip(sg * 1.2, 0, 1), TEAL, 0.55, edge=0.15, gran=0.55)
    # indigo sweep top-right, where the -31% stamp lands
    ind = sweep(p, [(2120, 470), (1760, 300), (1380, 170), (980, -40)], 330, 210, rough=0.2)
    p.glaze(ind * grade(p, 1920, 380, 1000, 0, 0.5, 1), INDIGO, 0.85, edge=0.8, gran=0.8, bloom=3, variation=0.35)
    p.glaze(blob(p, 1850, 260, 400, 240, rough=0.3, soft=36, ragged=0.5) * np.clip(ind * 1.3, 0, 1), INDIGO_D, 0.5, edge=0.1, gran=0.65)
    # ochre -> sienna pass bottom-right, under the bar chart
    och = sweep(p, [(820, 1180), (1220, 980), (1640, 860), (2100, 840)], 210, 280)
    p.glaze(och * grade(p, 1900, 900, 900, 1080, 0.55, 1), OCHRE, 0.72, edge=0.8, gran=0.55, bloom=2)
    p.glaze(blob(p, 1760, 980, 360, 170, rough=0.3, soft=26, ragged=0.5) * np.clip(och * 1.2, 0, 1), SIENNA, 0.6, edge=0.2, gran=0.6)
    # teal accent where the indigo and ochre nearly meet
    p.glaze(blob(p, 1020, 470, 95, 52, rot=-0.25, rough=0.35, soft=3), TEAL, 0.6, edge=0.8, gran=0.5)
    # stamp impact splash (the stamp just slammed down)
    p.splatter(SIENNA, n=34, box=(1230, 90, 1860, 480), size=(1.5, 6), strength=0.8)
    p.splatter(SIENNA, n=6, box=(1280, 120, 1820, 460), size=(7, 12), strength=0.6)
    p.splatter(INDIGO, n=30, box=(980, 0, 1900, 620), size=(1.5, 5), strength=0.7)
    p.splatter(TEAL, n=22, box=(40, 330, 900, 1060), size=(1.5, 5), strength=0.65)
    return p



if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    out = args[0] if args and not args[0].startswith('--') else 'watercolor_washes.png'
    layout = args[args.index('--layout') + 1] if '--layout' in args else 'cover'
    seed = int(args[args.index('--seed') + 1]) if '--seed' in args else None
    fn = cover if layout == 'cover' else bill
    p = fn(seed) if seed is not None else fn()
    stages = args[args.index('--stages') + 1] if '--stages' in args else None
    p.save(out, stages_dir=stages)
    print('saved', out)
