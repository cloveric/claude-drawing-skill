"""Example (paper collage): Balloon Day / 热气球小镇 — torn-paper hills with white rims, striped
hot-air balloons, a notebook-paper cloud and a newsprint cloud, a smiling crayon sun, little houses,
a waving kid, a paper plane. Pure code, no image model.
python3 papercut_balloons.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from papercut import Collage
from core import spline, fbm1d, polygon_mask

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'papercut_balloons.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

c = Collage(1920, 1080, seed=42)
rng = c.rng
W, H = c.W, c.H

# ---- sky, sun with crayon rays, clouds of different papers
c.background('#8cc6e7', texture='paper')
SX, SY, SR = 250, 200, 92
for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
    c.crayon([(SX + np.cos(a) * (SR + 22), SY + np.sin(a) * (SR + 22)), (SX + np.cos(a) * (SR + 70), SY + np.sin(a) * (SR + 70))], 7, '#f39c34', 0.9)
c.piece(mask=c.circle_mask(SX, SY, SR), colour='#f7c948', texture='crayon', torn=0.4, rim=0.8, shadow=0.3, angle=0.8)
c.face(SX, SY + 6, SR * 0.85, mood='smile')
c.piece(mask=c.cloud_mask(700, 190, 320, 130, puffs=4, seed=5), colour='#fbf8ef', texture='notebook', torn=0.7, rim=0.8, shadow=0.35)
c.piece(mask=c.cloud_mask(1560, 190, 330, 130, puffs=5, seed=6), colour='#e9e3d6', texture='newsprint', torn=0.7, rim=0.9, shadow=0.35)
c.piece(mask=c.cloud_mask(1090, 330, 200, 80, puffs=3, seed=7), colour='#fbfbf6', texture='paper', torn=0.6, rim=0.6, shadow=0.3)
c.stage('sky')

# ---- hills and a little town
xs = np.linspace(-20, W + 20, 60)
far = [(x, 700 - 60 * np.sin(x / 300 + 1.0) - 20 * fbm1d(60, 12, 3, 1)[i]) for i, x in enumerate(xs)]
c.piece(far + [(W + 20, H + 20), (-20, H + 20)], '#a6d47f', texture='paper', torn=0.8, rim=0.9, shadow=0.35)
mid = [(x, 800 - 80 * np.sin(x / 360 + 2.6) - 20 * fbm1d(60, 12, 3, 2)[i]) for i, x in enumerate(xs)]
c.piece(mid + [(W + 20, H + 20), (-20, H + 20)], '#6fb56b', texture='paper', torn=0.8, rim=0.9, shadow=0.4)

def house(x, base_y, w, h, body, roof, seed):
    r = np.random.default_rng(seed)
    c.piece([(x - w / 2, base_y), (x + w / 2, base_y), (x + w / 2, base_y - h), (x - w / 2, base_y - h)], body, torn=0.2, rim=0.4, shadow=0.35)
    c.piece([(x - w / 2 - 10, base_y - h + 4), (x + w / 2 + 10, base_y - h + 4), (x, base_y - h - w * 0.55)], roof, torn=0.25, rim=0.5, shadow=0.35)
    c.piece([(x - 9, base_y), (x + 9, base_y), (x + 9, base_y - 28), (x - 9, base_y - 28)], '#6b4a3a', torn=0.1, rim=0.2, shadow=0.2)
    for wx in (-w * 0.28, w * 0.28):
        c.piece([(x + wx - 9, base_y - h * 0.62), (x + wx + 9, base_y - h * 0.62), (x + wx + 9, base_y - h * 0.62 - 18), (x + wx - 9, base_y - h * 0.62 - 18)], '#ffe08a', torn=0.05, rim=0.1, shadow=0.15)

def lolly_tree(x, base_y, r_):
    c.piece([(x - 6, base_y), (x + 6, base_y), (x + 5, base_y - r_ * 1.5), (x - 5, base_y - r_ * 1.5)], '#7a5236', torn=0.1, rim=0.2, shadow=0.25)
    c.piece(mask=c.circle_mask(x, base_y - r_ * 1.6, r_), colour='#3f8f55', texture='crayon', torn=0.5, rim=0.7, shadow=0.35, angle=1.2)

mid_y = lambda x: 800 - 80 * np.sin(x / 360 + 2.6)
for (x, w, h, body, roof) in [(560, 90, 70, '#f6e7c8', '#d9534f'), (680, 70, 58, '#f4b6c2', '#8e5a44'), (1500, 96, 74, '#bfe0f2', '#e07a3c'),
                              (1620, 76, 60, '#f6e7c8', '#b8452f'), (1750, 84, 66, '#ffd9a8', '#5b7fb5')]:
    house(x, mid_y(x) + 30, w, h, body, roof, int(x))
for (x, r_) in [(440, 34), (800, 28), (1390, 32), (1860, 30)]:
    lolly_tree(x, mid_y(x) + 32, r_)
near = [(x, 930 - 70 * np.exp(-((x - 1300) / 600) ** 2) - 15 * fbm1d(60, 10, 3, 3)[i]) for i, x in enumerate(xs)]
c.piece(near + [(W + 20, H + 20), (-20, H + 20)], '#3f8f55', texture='paper', torn=0.7, rim=0.9, shadow=0.45)
for _ in range(50):
    x = rng.uniform(30, W - 30); y = 930 - 70 * np.exp(-((x - 1300) / 600) ** 2) + rng.uniform(25, 140)
    for k in range(3):
        c.crayon([(x + k * 7, y), (x + k * 7 + rng.normal(0, 4), y - rng.uniform(14, 26))], 3.2, '#2c6b3e', 0.9)
for (x, y) in [(260, 1000), (330, 1020), (1100, 1010), (1640, 1030)]:        # a few crayon flowers
    for a in np.linspace(0, 2 * np.pi, 5, endpoint=False):
        c.dot(x + np.cos(a) * 9, y + np.sin(a) * 9, 7, '#f7f1e4')
    c.dot(x, y, 6, '#f7c948')
c.stage('town')

# ---- hot-air balloons: striped envelope, ropes, kraft basket
def balloon(cx, cy, r, cols, n_stripes=6, kid=False):
    neck_y, neck_w = cy + r * 1.35, r * 0.42
    top = [(cx + r * np.cos(t), cy + r * np.sin(t)) for t in np.linspace(np.pi, 2 * np.pi, 40)]
    right = spline([(cx + r, cy), (cx + r * 0.86, cy + r * 0.62), (cx + neck_w / 2, neck_y)], 14).tolist()
    left = spline([(cx - neck_w / 2, neck_y), (cx - r * 0.86, cy + r * 0.62), (cx - r, cy)], 14).tolist()
    env = polygon_mask(H, W, top + right + left, ss=2)
    c.piece(mask=env, colour=cols[0], texture='paper', torn=0.25, rim=0.6, shadow=0.4)
    # stripes follow the envelope's width row by row (like gores on a real balloon)
    on = env > 0.5
    left_x = np.where(on.any(1), on.argmax(1), 0).astype(np.float32)
    right_x = np.where(on.any(1), W - 1 - on[:, ::-1].argmax(1), 0).astype(np.float32)
    ctr = (left_x + right_x) / 2; hw = np.maximum((right_x - left_x) / 2, 1)
    u = (c.XX - ctr[:, None]) / hw[:, None]
    k = np.floor((u + 1) / 2 * n_stripes)
    stripe = ((k % 2) == 1).astype(np.float32) * env
    c.piece(mask=stripe, colour=cols[1], texture='paper', torn=0.0, rim=0.0, shadow=0.0)
    by = neck_y + r * 0.45; bw = r * 0.5
    for (x0, x1) in [(cx - neck_w / 2, cx - bw / 2), (cx + neck_w / 2, cx + bw / 2)]:
        c.crayon([(x0, neck_y), (x1, by)], 3, '#5b4636', 0.9)
    if kid:
        hx, hy, hr = cx - bw * 0.1, by - r * 0.16, r * 0.17
        c.crayon([(hx + hr * 0.9, hy + hr * 0.6), (hx + hr * 2.1, hy - hr * 0.9)], 6, '#f3cda6', 1.0)   # waving arm
        c.dot(hx + hr * 2.2, hy - hr * 1.05, hr * 0.32, '#f3cda6')
        c.piece(mask=c.circle_mask(hx, hy, hr), colour='#f3cda6', torn=0.15, rim=0.4, shadow=0.3)
        c.piece([(hx - hr, hy - hr * 0.35), (hx + hr, hy - hr * 0.35), (hx + hr * 0.7, hy - hr * 1.15), (hx - hr * 0.7, hy - hr * 1.15)], '#3a2f5c', torn=0.2, rim=0.3, shadow=0.2)  # little cap
        c.face(hx, hy + hr * 0.1, hr * 0.95, mood='dots')
    c.piece([(cx - bw / 2, by), (cx + bw / 2, by), (cx + bw * 0.42, by + r * 0.34), (cx - bw * 0.42, by + r * 0.34)], '#c8955c', texture='kraft', torn=0.3, rim=0.6, shadow=0.4)
    for j in range(1, 4):
        c.crayon([(cx - bw * 0.46, by + r * 0.085 * j), (cx + bw * 0.46, by + r * 0.085 * j)], 2.2, '#8a5d34', 0.8)

balloon(1700, 330, 72, ('#35a7a0', '#f6e7c8'), 6)
balloon(830, 470, 58, ('#f28aa0', '#fbf8ef'), 6)
balloon(1250, 360, 165, ('#e4572e', '#f3c13a'), 8, kid=True)
c.stage('balloons')

# ---- a paper plane with a crayon trail, and birds
PX, PY = 470, 420
trail = spline([(90, 560), (200, 500), (300, 520), (400, 450)], 12)
for i in range(0, len(trail) - 1, 2):
    c.crayon([tuple(trail[i]), tuple(trail[i + 1])], 3.2, '#ffffff', 0.9)
c.piece([(PX - 60, PY + 26), (PX + 70, PY - 30), (PX - 20, PY + 4)], '#fbfbf6', torn=0.0, rim=0.0, shadow=0.35)
c.piece([(PX - 20, PY + 4), (PX + 70, PY - 30), (PX - 30, PY + 40)], '#e6e2d6', torn=0.0, rim=0.0, shadow=0.3)
for (bx, by, s) in [(975, 150, 1.0), (1045, 182, 0.8), (925, 196, 0.7)]:        # crayon birds: two thin arcs
    c.crayon(spline([(bx - 34 * s, by + 4 * s), (bx - 16 * s, by - 14 * s), (bx, by)], 8), 2.6, '#2f3e5c', 0.95)
    c.crayon(spline([(bx, by), (bx + 16 * s, by - 14 * s), (bx + 34 * s, by + 4 * s)], 8), 2.6, '#2f3e5c', 0.95)

c.save(out, stages_dir=stages)
print('saved', out)
