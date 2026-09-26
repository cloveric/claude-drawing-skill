"""范例（剪纸拼贴）：「小沙弥看月亮」— 撕纸毛边、纸片阴影、蜡笔质感、报纸云、笔记本纸条、可爱小人。
python3 papercut_moon.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from papercut import Collage
from core import blob_pts, spline, fbm1d

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'papercut_moon.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

c = Collage(1920, 1080, seed=15)
rng = c.rng
W, H = c.W, c.H

# ---- night sky in navy crayon, stars
c.background('#232d66', texture='kraft')
for _ in range(40):
    c.dot(rng.uniform(30, W - 30), rng.uniform(20, 560), rng.uniform(1.5, 3.2), '#f6e7a8')
for (x, y, r) in [(260, 150, 22), (880, 110, 16), (1040, 360, 14), (1750, 140, 20), (150, 430, 14), (1650, 480, 12)]:
    c.piece(Collage.star_pts(x, y, r), '#f4cf5e', texture='crayon', torn=0.15, rim=0.3, shadow=0.25)
c.stage('夜空')

# ---- the moon: soft glow, torn paper disc with a sleepy smile, crayon rays
MX, MY, MR = 1360, 300, 150
c.glow(MX, MY, 260, '#f7d98a', 0.18)
c.piece(mask=c.circle_mask(MX, MY, MR), colour='#f6d77a', texture='crayon', torn=0.5, rim=0.9, shadow=0.35, angle=0.9)
c.face(MX, MY + 10, MR * 0.85, mood='sleep')
halo = [(MX + np.cos(a) * (MR + 38 + 6 * np.sin(5 * a)), MY + np.sin(a) * (MR + 38 + 6 * np.sin(5 * a))) for a in np.linspace(-2.2, 2.6, 40)]
c.crayon(spline(halo, 4), 5, '#f2c94c', 0.75)                                       # a hand-drawn crayon halo, not sun rays
for a in (-2.6, -0.3, 0.6, 2.9):
    x, y = MX + np.cos(a) * (MR + 90), MY + np.sin(a) * (MR + 90)
    c.crayon([(x - 12, y), (x + 12, y)], 4, '#f6e7a8'); c.crayon([(x, y - 12), (x, y + 12)], 4, '#f6e7a8')   # twinkles
c.stage('月亮')

# ---- a newspaper cloud drifting across
c.piece(mask=c.cloud_mask(560, 250, 380, 170, puffs=5, seed=3), colour='#e9e3d6', texture='newsprint', torn=0.7, rim=0.9, shadow=0.35)
c.stage('报纸云')

# ---- torn-paper hills, far to near
xs = np.linspace(-20, W + 20, 60)
far = [(x, 640 - 70 * np.sin(x / 260 + 0.5) - 30 * fbm1d(60, 12, 3, 1)[i]) for i, x in enumerate(xs)]
c.piece(far + [(W + 20, H + 20), (-20, H + 20)], '#3b3f86', texture='paper', torn=0.8, rim=0.9, shadow=0.4)
mid = [(x, 760 - 90 * np.sin(x / 330 + 2.2) - 25 * fbm1d(60, 12, 3, 2)[i]) for i, x in enumerate(xs)]
c.piece(mid + [(W + 20, H + 20), (-20, H + 20)], '#2e6275', texture='paper', torn=0.8, rim=0.9, shadow=0.4)
# a little pagoda with a lit window on the middle hill
PX, PY = 1560, 700
for k, (wid, hgt) in enumerate([(120, 26), (96, 24), (72, 22)]):
    y = PY - k * 58
    c.piece([(PX - 30 + k * 4, y), (PX + 30 - k * 4, y), (PX + 30 - k * 4, y - 34), (PX - 30 + k * 4, y - 34)], '#6b3b36', torn=0.2, rim=0.3, shadow=0.3)
    c.piece([(PX - wid / 2, y - 30), (PX + wid / 2, y - 30), (PX + wid * 0.28, y - 30 - hgt), (PX - wid * 0.28, y - 30 - hgt)], '#3a2433', torn=0.25, rim=0.4, shadow=0.3)
c.dot(PX, PY - 16, 9, '#ffd66b'); c.glow(PX, PY - 16, 28, '#ffd66b', 0.35)
c.crayon([(PX, PY - 180), (PX, PY - 206)], 5, '#3a2433')
near = [(x, 880 - 120 * np.exp(-((x - 620) / 520) ** 2) - 20 * fbm1d(60, 10, 3, 3)[i]) for i, x in enumerate(xs)]
c.piece(near + [(W + 20, H + 20), (-20, H + 20)], '#4f8a4f', texture='paper', torn=0.7, rim=0.9, shadow=0.45)
for _ in range(60):                                   # crayon grass tufts
    x = rng.uniform(40, W - 40); y = 880 - 120 * np.exp(-((x - 620) / 520) ** 2) + rng.uniform(20, 170)
    for k in range(3):
        c.crayon([(x + k * 7, y), (x + k * 7 + rng.normal(0, 4), y - rng.uniform(14, 28))], 3.2, '#2f6a3a', 0.9)
c.stage('山丘')

# ---- a small monk sitting on the hill, looking up at the moon
BX, BY = 640, 770
robe = spline([(BX - 95, BY + 70), (BX - 80, BY - 10), (BX - 40, BY - 55), (BX + 40, BY - 55), (BX + 80, BY - 10), (BX + 95, BY + 70)], 10)
c.piece(np.vstack([robe, [(BX + 95, BY + 78), (BX - 95, BY + 78)]]), '#e0873b', texture='paper', torn=0.35, rim=0.6, shadow=0.45)
c.piece([(BX - 45, BY - 50), (BX - 10, BY - 50), (BX + 70, BY + 60), (BX + 35, BY + 66)], '#b8512e', texture='paper', torn=0.3, rim=0.5, shadow=0.3)
c.piece(mask=c.circle_mask(BX + 30, BY + 20, 20), colour='#f3cda6', torn=0.2, rim=0.4, shadow=0.3)      # hands in lap
c.piece(mask=c.circle_mask(BX, BY - 110, 62), colour='#f3cda6', texture='paper', torn=0.3, rim=0.7, shadow=0.4)
for sx in (-1, 1):
    c.piece(mask=c.circle_mask(BX + sx * 60, BY - 106, 13), colour='#eebf95', torn=0.15, rim=0.3, shadow=0.2)
c.face(BX + 6, BY - 118, 56, mood='smile')
for (dx, dy) in [(-20, -150), (0, -156), (20, -150)]:                                                   # three dots on the shaved head
    c.dot(BX + dx, BY + dy, 3.5, '#c98e6d')
c.stage('小沙弥')

# ---- a torn notebook scrap with a note, and fireflies
note = [(1440, 820), (1780, 800), (1790, 960), (1452, 985)]
c.piece(note, '#fbf8ef', texture='notebook', torn=0.6, rim=0.5, shadow=0.45)
c.text('心中有月', 1490, 850, 64, '#3a5fa8')
c.crayon(spline([(1500, 940), (1600, 952), (1720, 930)], 8), 4, '#d9534f', 0.85)
for _ in range(14):
    x, y = rng.uniform(200, 1400), rng.uniform(640, 1000)
    c.glow(x, y, 16, '#fff0a0', 0.45); c.dot(x, y, 3, '#fff6c0')

c.save(out, stages_dir=stages)
print('saved', out)
