"""Example (ukiyo-e woodblock print): Fuji at Dawn / 富士曙 — bokashi sky, snow-capped Fuji, stylised
cloud bands, a seigaiha-patterned sea with sailboats, a pine on a cliff, title cartouche and seal.
Pure code, no image model.
python3 ukiyoe_fuji.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from ukiyoe import Ukiyoe
from core import spline, curve

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'ukiyoe_fuji.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

u = Ukiyoe(1920, 1080, seed=1831)
W, H = u.W, u.H
HOR = 640

# ---- sky: Prussian blue wiped down from the top, dawn red rising from the horizon
sky = u.rect(0, 0, W, HOR + 2)
u.bokashi(sky, '#27487f', 0, 340)
u.bokashi(sky, '#e0723b', HOR, 420, strength=0.85)
u.stage('sky')

# ---- Mount Fuji: concave slopes, snow cap with long fingers, darker bokashi at the summit
AX, AY = 1180, 190
ts = np.linspace(0, 1, 40)
left = [(AX - 20 - 450 * t ** 1.6, AY + (HOR - AY) * t) for t in ts]
right = [(AX + 20 + 470 * t ** 1.6, AY + (HOR - AY) * t) for t in ts]
fuji = left[::-1] + [(AX - 20, AY), (AX + 20, AY)] + right
u.block(u.poly(fuji), '#4d6f8f')
u.bokashi(u.poly(fuji), '#2d4a68', AY, 470)
snow_y = lambda x: AY + 150 + 30 * np.sin(x / 13) * np.clip(1 - np.abs(x - AX) / 260, 0, 1) + 18 * np.sin(x / 5.3)
snow = u.poly(fuji) * (u.YY < snow_y(u.XX))
u.block(snow, '#f6f1e3')
u.key(fuji[:40][::-1], 3.5); u.key(fuji[40:], 3.5)
xs = np.linspace(AX - 230, AX + 240, 60)
u.key([(x, snow_y(x)) for x in xs if abs(x - AX) < 20 + 450 * (((snow_y(x) - AY) / (HOR - AY)) ** 1.6) + 5], 2.2)
# distant low islands on the horizon
for (x0, x1, h) in [(0, 420, 26), (1560, 1920, 20)]:
    isl = [(x0, HOR + 4)] + [(x, HOR - h * np.sin(np.pi * (x - x0) / (x1 - x0)) ** 0.6) for x in np.linspace(x0, x1, 30)] + [(x1, HOR + 4)]
    u.block(u.poly(isl), '#56786a'); u.key(isl[1:-1], 2.2)
# stylised mist bands crossing the mountain
for (x0, x1, y, h) in [(560, 1480, 470, 44), (950, 1880, 548, 38), (60, 760, 170, 38), (1260, 1690, 300, 30)]:
    u.cloud_band(x0, x1, y, h, glow='#f0a27a' if y > 400 else None)
u.stage('fuji')

# ---- the sea: deep blue bokashi from the foreground, seigaiha waves, sailboats
sea = u.rect(0, HOR, W, H)
u.block(sea, '#2c5d9c')
u.bokashi(sea, '#15356a', H, 720)
u.seigaiha(sea * (u.YY > 690), '#8db3de', r=30, width=2.2)
for (bx, by, s) in [(820, 735, 1.0), (1040, 700, 0.7), (1480, 760, 1.2), (620, 690, 0.55)]:
    hull = [(bx - 46 * s, by), (bx + 46 * s, by), (bx + 32 * s, by + 14 * s), (bx - 32 * s, by + 14 * s)]
    sail = [(bx - 22 * s, by - 6 * s), (bx + 18 * s, by - 6 * s), (bx + 14 * s, by - 74 * s), (bx - 20 * s, by - 70 * s)]
    u.block(u.poly(sail), '#f4ead2'); u.key(sail, 2.2, closed=True)
    for k in range(1, 4):
        u.key([(bx - 21 * s + k, by - 6 * s - 17 * k * s), (bx + 17 * s - k, by - 6 * s - 17 * k * s)], 1.4)
    u.block(u.poly(hull), '#3a2a22'); u.key(hull, 2.2, closed=True)
u.stage('sea')

# ---- a pine leaning out from a cliff in the left foreground
cliff = [(0, H), (0, 720), (120, 690), (250, 725), (360, 820), (430, 960), (410, H)]
u.block(u.poly(cliff), '#80603e')
u.bokashi(u.poly(cliff), '#4f3a26', H, 780)
u.key(cliff[1:-1], 4)
for (a, b) in [((60, 760), (140, 850)), ((200, 780), (260, 900)), ((110, 900), (230, 1000))]:
    u.key(spline([a, ((a[0] + b[0]) / 2 + 12, (a[1] + b[1]) / 2), b], 8), 2.2)            # rock cracks
trunk = spline([(170, 715), (210, 620), (190, 540), (260, 470), (380, 430), (470, 380)], 14)
u.key(trunk, 22, colour='#4a3121'); u.key(trunk, 3)
for (a, b) in [((215, 600), (330, 560)), ((200, 545), (95, 470)), ((300, 455), (330, 360))]:
    u.key(spline([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 10), b], 8), 9, colour='#4a3121')
for (cx, cy, w) in [(480, 372, 170), (345, 552, 150), (95, 462, 130), (330, 352, 120), (590, 405, 110)]:
    top = [(cx + w * np.cos(t) / 2, cy + (w * 0.32) * np.sin(t)) for t in np.linspace(np.pi, 2 * np.pi, 24)]
    umb = top + [(cx + w / 2, cy + 8), (cx - w / 2, cy + 8)]
    u.block(u.poly(umb), '#2d5b3d')
    u.block(u.poly(umb) * (u.YY < cy - w * 0.12), '#5d8f4f')
    u.key(umb, 2.6, closed=True)
    for k in range(-3, 4):
        u.key([(cx + k * w / 8, cy - 2), (cx + k * w / 7.2, cy - w * 0.22)], 1.4)
u.stage('pine')

# ---- birds, title cartouche and seal
for (bx, by, s) in [(1480, 250, 1.0), (1530, 272, 0.8), (1440, 285, 0.7), (1575, 240, 0.6)]:
    u.key(spline([(bx - 18 * s, by), (bx - 7 * s, by - 8 * s), (bx, by)], 6), 2.2)
    u.key(spline([(bx, by), (bx + 7 * s, by - 8 * s), (bx + 18 * s, by)], 6), 2.2)
u.cartouche(1740, 60, 100, 330, '富士曙')
u.seal(1756, 420, 66, '春')
u.save(out, stages_dir=stages)
print('saved', out)
