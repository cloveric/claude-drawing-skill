"""范例（水彩）：「一花一世界」— 清晨荷塘。纯代码水彩：湿画天空、罩染荷叶、水痕边、颗粒、水渍花、提白叶脉。
python3 watercolor_lotus.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from watercolor import Watercolor, hexc
from core import blob_pts, spline, curve

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'watercolor_lotus.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

p = Watercolor(1920, 1080, seed=108)
p.paper()
p.stage('纸')
rng = p.rng

# ---- sky: wet-in-wet from cool blue to dawn peach
p.gradient_wash(0, 520, top=hexc('#8fb0cf'), bottom=hexc('#f2cfae'), strength=0.55)
# ---- far bank: soft blue-grey trees melting into the sky
far = [(0, 560)] + [(x, 520 - 40 * np.sin(x / 190) - 25 * np.sin(x / 67 + 1) - rng.uniform(0, 18)) for x in np.linspace(0, 1920, 40)] + [(1920, 560)]
p.glaze(p.shape(far, soft=14, ragged=0.35), hexc('#7d93a8'), 0.5, edge=0.25, gran=0.4)
p.stage('天空')

# ---- water: pale teal, darker toward the viewer, with horizontal dry-brush streaks
water = [(0, 545), (1920, 545), (1920, 1080), (0, 1080)]
wm = p.shape(water, soft=6, ragged=0.1) * np.clip((p.YY - 545) / 500, 0.35, 1)
p.glaze(wm, hexc('#9cc3bf'), 0.55, edge=0.1, gran=0.45, variation=0.35)
for _ in range(26):
    y = rng.uniform(580, 1060); x = rng.uniform(-100, 1700); ln = rng.uniform(200, 520)
    p.stroke(spline([(x, y), (x + ln / 2, y + rng.normal(0, 2)), (x + ln, y)], 10), rng.uniform(3, 7), hexc('#5f8f93'), 0.35, dry=0.7)
p.stage('水面')

# ---- lotus leaves (back to front): base glaze, darker second glaze, bloom, lifted veins, stem
def leaf(cx, cy, rx, ry, rot, dark=0.55, hue='#a9c46b'):
    pts = blob_pts(cx, cy, rx, ry, rough=0.11, n=140, seed=int(cx), rot=rot)
    m = p.shape(pts, soft=2.5, ragged=0.22)
    # stem first, visible only below the leaf
    vx0, vy0 = cx + rx * 0.08, cy - ry * 0.05
    p.glaze(p.band([(vx0, cy + ry * 0.6), (vx0 - 6, cy + ry + 60)], 7, soft=2) * (1 - m), hexc('#6f8a4a'), 0.4, edge=0.2)
    p.glaze(m, hexc(hue), 0.75, edge=0.55, gran=0.35)
    # shadow glaze pooled on one side (wet-in-wet, soft), not a centred ring
    side = p.shape(blob_pts(cx - rx * 0.28, cy + ry * 0.18, rx * 0.72, ry * 0.7, rough=0.2, n=100, seed=int(cy), rot=rot), soft=16, ragged=0.45)
    p.glaze(side * m, hexc('#4a7a45'), dark, edge=0.25, gran=0.45, bloom=1)
    vx, vy = cx + rx * 0.08, cy - ry * 0.05
    veins = np.zeros((p.H, p.W), np.float32)
    for a in np.linspace(0, 2 * np.pi, 13, endpoint=False):
        ex, ey = vx + np.cos(a + rot) * rx * 0.9, vy + np.sin(a + rot) * ry * 0.9
        veins = np.maximum(veins, p.band(spline([(vx, vy), ((vx + ex) / 2 + rng.normal(0, 5), (vy + ey) / 2), (ex, ey)], 8), 3, soft=1.2))
    p.lift(veins * m, 0.32)

for (cx, cy, rx, ry, rot, dk, hue) in [(300, 640, 170, 55, -0.05, 0.45, '#b3c877'), (1560, 620, 150, 48, 0.08, 0.45, '#a3c27a'),
                                        (980, 700, 200, 70, 0.04, 0.5, '#9fc06a'), (1750, 820, 230, 90, -0.1, 0.55, '#8fb873'),
                                        (160, 900, 260, 110, 0.12, 0.6, '#a9c46b'), (620, 960, 240, 95, -0.06, 0.6, '#98bd6e')]:
    leaf(cx, cy, rx, ry, rot, dk, hue)
p.stage('荷叶')

# ---- lotus flowers: stems, petals (pink with deeper tips), seed pod
def flower(bx, by, scale=1.0, open_=True):
    p.glaze(p.band(spline([(bx, by + 20), (bx + 8, by + 180), (bx + 2, by + 330)], 10), 9 * scale, soft=2), hexc('#7a9650'), 0.7, edge=0.4)
    angles = np.linspace(-150, -30, 7) if open_ else np.linspace(-110, -70, 3)
    for k, a in enumerate(angles):
        ang = np.radians(a + rng.normal(0, 4))
        L = (150 if open_ else 175) * scale * (0.85 + 0.3 * np.sin(np.pi * k / max(1, len(angles) - 1)))
        Wd = (46 if open_ else 42) * scale
        pts = Watercolor.petal_pts(bx, by, ang, L, Wd, curl=rng.normal(0, 0.05))
        m = p.shape(pts, soft=2, ragged=0.15)
        p.glaze(m, hexc('#f0a3b3'), 0.55, edge=0.6, gran=0.25)
        tip = Watercolor.petal_pts(bx + np.cos(ang) * L * 0.45, by + np.sin(ang) * L * 0.45, ang, L * 0.55, Wd * 0.75)
        p.glaze(p.shape(tip, soft=7, ragged=0.3) * m, hexc('#c94f73'), 0.55, edge=0.3)
        p.line(spline([(bx, by), (bx + np.cos(ang) * L * 0.9, by + np.sin(ang) * L * 0.9)], 6), 1.0, hexc('#b0506a'), 0.25)
    if open_:
        pod = p.shape(blob_pts(bx, by - 30 * scale, 34 * scale, 18 * scale, rough=0.05, seed=int(bx)), soft=2)
        p.glaze(pod, hexc('#e3bf4d'), 0.8, edge=0.6, gran=0.3)
        for _ in range(7):
            p.splatter(hexc('#9a7a2a'), 1, box=(bx - 22 * scale, by - 40 * scale, bx + 22 * scale, by - 24 * scale), size=(2, 3.5), strength=0.8)
    # soft reflection in the water
    ref = p.shape([(bx - 40 * scale, by + 340), (bx + 40 * scale, by + 340), (bx + 20, by + 470), (bx - 20, by + 470)], soft=20, ragged=0.4)
    p.glaze(ref * (p.YY > 545), hexc('#e7a3b2'), 0.25, edge=0.1)

flower(1150, 430, 1.05, True)
flower(560, 470, 0.85, False)
p.stage('荷花')

# ---- a dragonfly and a few flicked droplets
dx, dy = 1450, 300
p.line(spline([(dx - 70, dy + 10), (dx, dy), (dx + 30, dy - 4)], 8), 3.2, hexc('#4b3b36'), 0.8)
for (a, L) in [(-100, 95), (-70, 88), (100, 90), (70, 84)]:
    ang = np.radians(a)
    wp = Watercolor.petal_pts(dx - 8, dy, ang, L, 16)
    p.glaze(p.shape(wp, soft=1.5, ragged=0.1), hexc('#b9d4e6'), 0.35, edge=0.7, gran=0.1)
p.splatter(hexc('#6f9a5b'), 30, box=(0, 560, 1920, 1080), size=(1.5, 4.5), strength=0.5)
p.splatter(hexc('#e38fa6'), 14, box=(900, 250, 1400, 700), size=(1.2, 3.5), strength=0.45)

p.title_vertical('一花一世界', 150, 140, 80)
p.seal('清净', 250, 160, 34)
p.save(out, stages_dir=stages)
print('saved', out)
