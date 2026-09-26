"""Example (watercolour): Autumn Lake / 秋日湖畔 — wet-in-wet sky, glazed foliage with blooms,
mirrored reflections, lifted ripples, a red canoe. Pure code, no image model.
python3 watercolor_autumn.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from watercolor import Watercolor, hexc
from core import blob_pts, spline, curve

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'watercolor_autumn.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

p = Watercolor(1920, 1080, seed=1017)
p.paper()
p.stage('paper')
rng = p.rng
Y0 = 640                                                    # waterline

# ---- sky and distant hills (wet-in-wet)
p.gradient_wash(0, Y0, top=hexc('#94b6d6'), bottom=hexc('#f6e2c2'), strength=0.5, soft_bottom=30)
hills = [(0, Y0 + 5)] + [(x, 560 - 55 * np.sin(x / 240 + 0.8) - 30 * np.sin(x / 95) - rng.uniform(0, 12)) for x in np.linspace(0, 1920, 44)] + [(1920, Y0 + 5)]
p.glaze(p.shape(hills, soft=12, ragged=0.35), hexc('#8d95b6'), 0.42, edge=0.25, gran=0.45)
far_trees = p.blobs([(x, Y0 - rng.uniform(12, 30), rng.uniform(26, 48), rng.uniform(18, 34)) for x in np.linspace(560, 1360, 22)], rough=0.3, soft=5)
p.glaze(far_trees * (p.YY < Y0 + 2) * np.clip((Y0 + 2 - p.YY) / 40, 0.45, 1), hexc('#b39a58'), 0.38, edge=0.35, gran=0.45)
p.stage('sky')

# ---- the lake: sky colour near the horizon deepening toward us
water = np.clip((p.YY - Y0) / 3, 0, 1)
p.glaze(water * np.clip(0.35 + (p.YY - Y0) / 520, 0, 1), hexc('#6e9db0'), 0.6, edge=0.05, gran=0.35, variation=0.3)
p.glaze(p.mirror(p.shape(hills, soft=12, ragged=0.35), Y0, soft=6, breakup=0.3), hexc('#8d95b6'), 0.25, edge=0.1)
p.stage('lake')

# ---- trees: trunks, then three glazes (yellow -> orange -> red), each with blooms
def tree(tx, ty, root_y, spread, colours, seed):
    r = np.random.default_rng(seed)
    sx, sy = spread
    trunk_w = max(7, sx * 0.07)
    p.stroke(curve((tx + r.normal(0, 6), root_y), (tx, ty + sy * 0.15), r.normal(0, sx * 0.08), 20, wig=4, seed=seed), trunk_w, hexc('#6b4a32'), 0.85, dry=0.3, taper=(0.02, 0.55))
    for k in range(4):                                          # a few branches reaching up and out into the crown
        side = -1 if k % 2 == 0 else 1
        by = ty + sy * r.uniform(0.2, 0.6)
        ex, ey = tx + side * sx * r.uniform(0.35, 0.65), by - sy * r.uniform(0.35, 0.7)
        p.stroke(curve((tx, by), (ex, ey), side * sx * 0.06, 12), trunk_w * 0.4, hexc('#6b4a32'), 0.7, dry=0.35, taper=(0.05, 0.7))
    masks = []; base = None
    for i, (col, frac, strength) in enumerate(colours):
        items = []
        for _ in range(int(22 * frac) + 6):
            ang = r.uniform(0, 2 * np.pi); rad = r.uniform(0, 1) ** 0.7
            ox, oy = np.cos(ang) * sx * rad, np.sin(ang) * sy * rad
            if i > 0: ox += sx * 0.12 * i; oy += sy * 0.15 * i            # later glazes pool lower-right (shadow side)
            items.append((tx + ox, ty + oy, sx * r.uniform(0.2, 0.34) * (1 - 0.2 * i), sy * r.uniform(0.2, 0.34) * (1 - 0.2 * i)))
        m = p.blobs(items, rough=0.35, soft=4, ragged=0.45)
        if base is None: base = m
        else: m = m * np.clip(base * 1.3, 0, 1)                    # darker glazes stay inside the crown
        p.glaze(m, hexc(col), strength, edge=0.5, gran=0.45, bloom=2 if i == 0 else 1)
        masks.append((m, col))
    return masks

refl = []
refl += tree(360, 330, Y0 + 20, (230, 170), [('#f1c34a', 1.0, 0.75), ('#e48a38', 0.6, 0.6), ('#c64a31', 0.3, 0.5)], 1)
refl += tree(1590, 360, Y0 + 20, (210, 160), [('#f0a93f', 1.0, 0.75), ('#d9642f', 0.7, 0.6), ('#a83a2c', 0.35, 0.55)], 2)
refl += tree(1230, 500, Y0 + 12, (110, 80), [('#eecb5a', 1.0, 0.7), ('#e0943c', 0.5, 0.55)], 3)
refl += tree(820, 540, Y0 + 8, (70, 55), [('#d9b25a', 1.0, 0.6), ('#b7773a', 0.5, 0.5)], 4)
p.stage('trees')

# ---- reflections of the foliage, then lifted ripple lines
for (m, col) in refl:
    p.glaze(p.mirror(m * (p.YY < Y0), Y0, soft=9, breakup=0.55), hexc(col), 0.35, edge=0.1, gran=0.3)
rip = np.zeros((p.H, p.W), np.float32)
for _ in range(34):
    y = rng.uniform(Y0 + 15, 1060); x = rng.uniform(-50, 1800); ln = rng.uniform(120, 420)
    rip = np.maximum(rip, p.band([(x, y), (x + ln, y + rng.normal(0, 1.5))], rng.uniform(2, 4), soft=1.2))
p.lift(rip, 0.5)
p.stage('reflections')

# ---- a red canoe with a paddler, and its reflection
CX, CY = 1010, 770
hull = spline([(CX - 130, CY - 14), (CX - 70, CY + 14), (CX + 70, CY + 14), (CX + 135, CY - 16), (CX + 60, CY - 6), (CX - 60, CY - 6), (CX - 130, CY - 14)], 10)
hm = p.shape(hull, soft=1.2, ragged=0.1)
p.glaze(hm, hexc('#b8382c'), 0.95, edge=0.5, gran=0.2)
p.stroke(spline([(CX - 8, CY - 6), (CX - 4, CY - 38)], 6), 16, hexc('#2f4a6b'), 0.9, dry=0.2, taper=(0.1, 0.2))   # paddler
p.glaze(p.shape(blob_pts(CX - 3, CY - 48, 11, 12, rough=0.05, seed=9), soft=1), hexc('#e8b48f'), 0.9, edge=0.3)
p.stroke(spline([(CX - 34, CY - 52), (CX + 14, CY - 20), (CX + 52, CY + 16)], 8), 3.2, hexc('#6b4a32'), 0.85, dry=0.2)  # paddle
p.glaze(p.mirror(hm, CY + 10, soft=5, breakup=0.5), hexc('#b8382c'), 0.35, edge=0.1)
p.stage('canoe')

# ---- foreground bank with dry-brush grass, falling leaves
bank = [(0, 1080), (0, 930), (220, 905), (520, 950), (760, 1020), (820, 1080)]
p.glaze(p.shape(bank, soft=4, ragged=0.35), hexc('#8e8a45'), 0.7, edge=0.5, gran=0.5, bloom=1)
for _ in range(70):
    x = rng.uniform(0, 780); y = rng.uniform(930, 1075)
    if y < 905 + (x / 780) * 120: continue
    p.stroke([(x, y), (x + rng.normal(4, 8), y - rng.uniform(25, 60))], rng.uniform(2, 3.5), hexc('#5d6a32'), 0.7, dry=0.5, taper=(0.05, 0.8))
for _ in range(18):
    x, y = rng.uniform(250, 1750), rng.uniform(120, 620)
    lm = p.shape(Watercolor.petal_pts(x, y, rng.uniform(0, 6.28), rng.uniform(16, 26), rng.uniform(6, 9)), soft=1, ragged=0.1)
    p.glaze(lm, hexc(rng.choice(['#e48a38', '#c64a31', '#f1c34a'])), 0.8, edge=0.5)
p.splatter(hexc('#d9642f'), 26, box=(120, 150, 1800, 700), size=(1.5, 4), strength=0.55)

p.save(out, stages_dir=stages)
print('saved', out)
