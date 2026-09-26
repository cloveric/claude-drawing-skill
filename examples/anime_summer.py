"""Example (Japanese anime background): Summer Sky / 夏空 — towering cel-shaded cumulus, sun bloom and
lens flare, a country road with power lines, and a girl in a straw hat seen from behind.
Pure code, no image model.
python3 anime_summer.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from anime import Anime, hexc
from core import spline, fbm1d, blur

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'anime_summer.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

a = Anime(1920, 1080, seed=720)
rng = a.rng
HOR = 640
VX, VY = 1000, HOR                     # vanishing point

# ---- sky, high wisps, towering clouds lit from the upper left
a.sky('#1a4fb8', '#4c9be6', '#d3efff', horizon=HOR)
for (x, y, w) in [(300, 120, 520), (820, 70, 380), (1650, 110, 300)]:
    wisp = a.poly(spline([(x - w / 2, y + 10), (x - w / 4, y - 8), (x + w / 3, y - 4), (x + w / 2, y + 6), (x, y + 16), (x - w / 2, y + 10)], 10))
    a.fill(blur(wisp, 6), '#ffffff', 0.45)
a.cumulus(1330, HOR - 20, 980, 560, seed=3)
a.cumulus(330, HOR - 10, 640, 240, seed=4)
a.cumulus(760, HOR - 5, 360, 130, seed=5)
a.stage('sky')

# ---- distant hills and fields
hills = [(0, HOR + 12)] + [(x, HOR - 22 - 26 * np.sin(x / 210 + 0.5) - 12 * fbm1d(40, 8, 3, 9)[i]) for i, x in enumerate(np.linspace(0, 1920, 40))] + [(1920, HOR + 12)]
a.fill(a.poly(hills), '#5f8fae')
a.fill(a.poly(hills) * (a.YY > HOR - 30), '#4d7c9c', 0.8)
a.field(HOR, colours=('#86cf5e', '#62b54f'), bands=9)
# rice-paddy rows converging on the vanishing point (thin darker lines)
for k in range(-18, 19):
    if k == 0: continue
    x_bottom = VX + k * 160
    a.lines([(VX + k * 3, VY + 2), (x_bottom, 1080)], 1.6, '#4f9a44', 0.5)
a.stage('fields')

# ---- the road
road = [(VX - 6, VY), (VX + 6, VY), (1260, 1080), (620, 1080)]
a.fill(a.poly(road), '#cfc6b2')
a.fill(a.poly([(VX, VY), (VX + 6, VY), (1260, 1080), (1000, 1080)]), '#b9b09b', 0.7)       # shaded half
for side in (-1, 1):
    x_b = 1260 if side > 0 else 620
    a.lines([(VX + side * 5, VY), (x_b - side * 26, 1080)], 5, '#f4f1e8', 0.9)
# power poles in perspective along the right side, with sagging wires
tops = []
for i in range(7):
    t = (0.82 ** (i * 1.6))
    x = VX + 40 + (1640 - VX - 40) * t
    base = VY + (1040 - VY) * t
    hgt = 30 + 560 * t
    tops.append(a.pole(x, base, hgt, width=max(2, 12 * t)))
for i in range(len(tops) - 1):
    for dy in (0, 12):
        a.wire((tops[i][0] - 30 * (0.82 ** (i * 1.6)), tops[i][1] + dy), (tops[i + 1][0], tops[i + 1][1] + dy * 0.8), sag=40 * (0.82 ** (i * 1.6)), width=1.8)
a.wire((tops[0][0], tops[0][1]), (1920 + 40, tops[0][1] - 120), sag=60, width=2.2)
a.wire((tops[0][0], tops[0][1] + 12), (1920 + 40, tops[0][1] - 90), sag=60, width=2.2)
a.stage('road')

# ---- tall grass in the foreground corners
for (x0, x1) in [(0, 480), (1500, 1920)]:
    for _ in range(90):
        x = rng.uniform(x0, x1); h = rng.uniform(80, 200)
        lean = rng.normal(0, 30)
        blade = [(x - 7, 1085), (x + lean, 1085 - h), (x + 7, 1085)]
        a.fill(a.poly(blade), rng.choice(['#3f8f3c', '#4ea447', '#2f7331']))

# ---- girl in a straw hat, seen from behind (clean line art + two-tone cel shading)
GX, GY = 880, 950                       # feet
INK = '#3b2d3c'
legs = [[(GX - 24, GY - 110), (GX - 22, GY)], [(GX + 20, GY - 110), (GX + 22, GY)]]
for L in legs:
    a.lines(L, 22, '#f2cfb4'); a.lines(L, 22, '#e3b393', 0.35)
a.fill(a.poly([(GX - 60, GY - 4), (GX + 64, GY - 4), (GX + 60, GY + 10), (GX - 58, GY + 10)]), '#000000', 0.12)   # ground shadow
dress = [(GX - 48, GY - 330), (GX + 48, GY - 330), (GX + 100, GY - 96), (GX - 100, GY - 96)]
a.fill(a.poly(dress), '#fbfbff')
a.fill(a.poly([(GX + 10, GY - 330), (GX + 48, GY - 330), (GX + 100, GY - 96), (GX + 22, GY - 96)]), '#c9d6f2')   # shadow side
for fx in (-40, 0, 38):
    a.lines([(GX + fx * 0.4, GY - 240), (GX + fx, GY - 98)], 1.8, '#9fb2dc')
a.lines(dress, 3, INK, closed=True)
for side in (-1, 1):                    # arms
    arm = [(GX + side * 46, GY - 322), (GX + side * 64, GY - 250), (GX + side * 70, GY - 185)]
    a.lines(arm, 16, '#f2cfb4'); a.lines(arm, 16, '#e3b393', 0.3 if side < 0 else 0.0)
hair = spline([(GX - 40, GY - 360), (GX - 60, GY - 300), (GX - 56, GY - 230), (GX - 30, GY - 205), (GX, GY - 214), (GX + 30, GY - 205), (GX + 56, GY - 230), (GX + 60, GY - 300), (GX + 40, GY - 360)], 10).tolist()
a.fill(a.poly(hair + [(GX, GY - 400)]), '#5a3b2e')
for hx in (-26, -8, 12, 30):
    a.lines(spline([(GX + hx * 0.6, GY - 350), (GX + hx, GY - 300), (GX + hx * 1.1, GY - 250)], 6), 2, '#8a5a44', 0.8)
a.lines(hair, 3, INK)
# straw hat: crown, brim (cel shaded), red ribbon
brim = [(GX + 118 * np.cos(t), GY - 372 + 34 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 80, endpoint=False)]
a.fill(a.poly(brim), '#eed094')
a.fill(a.poly(brim) * (a.YY > GY - 372), '#d9b36e', 0.9)
crown = spline([(GX - 58, GY - 380), (GX - 52, GY - 430), (GX, GY - 448), (GX + 52, GY - 430), (GX + 58, GY - 380)], 10).tolist()
a.fill(a.poly(crown + [(GX, GY - 372)]), '#f3da9f')
a.fill(a.poly([(GX - 58, GY - 392), (GX + 58, GY - 392), (GX + 58, GY - 376), (GX - 58, GY - 376)]), '#d64553')
a.lines(brim, 3, INK, closed=True); a.lines(crown, 3, INK)
a.stage('girl')

# ---- light: sun behind the upper left, bloom, sparkles, vignette
a.sun_flare(470, 110, strength=1.0)
a.sparkles(28, box=(250, 40, 900, 420))
a.bloom(0.86, 20, 0.35)
a.vignette(0.2)
a.save(out, stages_dir=stages)
print('saved', out)
