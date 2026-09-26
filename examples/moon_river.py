"""范例：「月印万川」— 烘云托月、孤舟、芦苇。纯代码水墨。
python3 moon_river.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from inkpaint import Painting, spline, curve, blur

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'moon_river.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

p = Painting(1920, 1080, seed=2026)
p.paper()
p.stage('宣纸')
YY, XX, rng = p.YY, p.XX, p.rng

# ---- night sky wash that leaves the moon as bare paper (烘云托月)
MX, MY, MR = 1360, 250, 74
horizon = 610
dist = np.hypot(XX - MX, YY - MY)
sky = 0.30 * np.clip(1 - YY / horizon, 0, 1) ** 0.8 * (0.6 + 0.4 * p.noise2d(220, 4, 3))
sky *= np.clip((horizon - YY) / 140, 0, 1) ** 0.7                              # fades out toward the water line
moon = np.clip((MR - dist) / 3, 0, 1)
halo = np.exp(-((dist - MR) / 60) ** 2) * (dist > MR)
sky = sky * (1 - moon) * (1 - 0.55 * np.exp(-(np.clip(dist - MR, 0, None) / 90)))   # lighter glow near the moon
sky += 0.06 * halo * (0.6 + 0.4 * p.noise2d(40, 3, 4))
p.over(p.D, sky)
p.stage('夜空')

# ---- distant hills, very pale, sitting on the water line
# hills are bumps rising from below the water line, so the open water under the moon stays clean
far = p.ridge(horizon + 60, peaks=[(260, 150, 260), (640, 110, 200), (1760, 120, 230)], rough=12, rough_scale=200, seed=21)
p.wash(far, dens=0.2, decay=45, tex=90, edge=0.35, seed=22)
np.multiply(p.D, 1 - np.clip((YY - horizon) / 5, 0, 1), out=p.D)              # everything stops at the water line
p.stage('远山')

# ---- water: moon reflection (broken pale strokes) and sparse ripples
for i in range(14):
    y = horizon + 30 + i * 22 + rng.normal(0, 3)
    half = 70 * (1 - i / 16) + rng.uniform(-10, 10)
    x0 = MX - half + rng.normal(0, 12)
    p.stroke(spline([(x0, y), (MX + rng.normal(0, 10), y + rng.normal(0, 1.5)), (MX + half, y)], 10), 1.6, 0.16, dry=0.55, taper=(0.3, 0.3))
for _ in range(40):
    x = rng.uniform(80, 1840); y = rng.uniform(horizon + 40, 1000)
    if abs(x - MX) < 150: continue
    ln = rng.uniform(40, 140) * (0.6 + (y - horizon) / 500)
    p.stroke(spline([(x, y), (x + ln / 2, y + rng.normal(0, 1.2)), (x + ln, y)], 8), 1.3, 0.13 + 0.1 * (y - horizon) / 470, dry=0.6, taper=(0.3, 0.3))
p.stage('江面')

# ---- lone boat with a fisherman
BX, BY = 760, 742
hull = spline([(BX - 120, BY - 8), (BX - 60, BY + 12), (BX + 40, BY + 14), (BX + 118, BY - 14)], 12)
p.stroke(hull, 7, 0.85, dry=0.25, taper=(0.1, 0.2))
p.stroke(spline([(BX - 108, BY - 4), (BX, BY + 6), (BX + 104, BY - 10)], 10), 2.2, 0.5, dry=0.4)
cover = spline([(BX + 10, BY - 4), (BX + 38, BY - 38), (BX + 78, BY - 36), (BX + 96, BY - 8)], 10)   # woven canopy
p.stroke(cover, 4, 0.7, dry=0.35)
for k in range(5):
    x = BX + 22 + k * 15
    p.stroke([(x, BY - 34 + abs(k - 2) * 2), (x + 2, BY - 6)], 1.2, 0.45, dry=0.4)
FX, FY = BX - 58, BY - 10                                                    # the fisherman
p.stroke(spline([(FX - 10, FY), (FX - 4, FY - 22), (FX + 4, FY - 32)], 8), 6, 0.8, dry=0.2, taper=(0.1, 0.3))
p.stroke(spline([(FX - 18, FY - 34), (FX + 3, FY - 50), (FX + 22, FY - 33)], 8), 3, 0.85, dry=0.15, taper=(0.1, 0.1))   # straw hat
p.stroke(spline([(FX + 2, FY - 22), (FX - 80, FY - 120), (FX - 210, FY - 170)], 14), 1.4, 0.7, dry=0.2, taper=(0.05, 0.6))  # rod
p.stroke(spline([(FX - 210, FY - 170), (FX - 214, FY - 60), (FX - 212, FY + 30)], 12), 0.8, 0.35, dry=0.3, taper=(0.05, 0.05))  # line
for r_ in (10, 20):
    p.stroke(spline([(FX - 212 - r_ * 2, FY + 34), (FX - 212, FY + 34 + r_ * 0.25), (FX - 212 + r_ * 2, FY + 34)], 8), 1.1, 0.25, dry=0.5)
p.stroke(spline([(BX - 150, BY + 22), (BX, BY + 30), (BX + 150, BY + 20)], 10), 1.4, 0.18, dry=0.6)   # boat's shadow ripple
p.stage('孤舟')

# ---- reeds in the lower-right foreground
for i in range(22):
    back = i < 8                                                                # paler reeds behind for depth
    x0 = rng.uniform(1500, 1900); y0 = 1085
    h = rng.uniform(220, 420)
    lean = rng.uniform(-70, 40)
    top = (x0 + lean, y0 - h)
    stem = spline([(x0, y0), (x0 + lean * 0.35 + rng.normal(0, 6), y0 - h * 0.5), top], 12)
    p.stroke(stem, rng.uniform(1.4, 2.4), rng.uniform(0.18, 0.3) if back else rng.uniform(0.45, 0.72), dry=0.4, taper=(0.02, 0.7))
    for _ in range(int(rng.integers(1, 3))):                                    # blade leaves
        k = int(rng.integers(8, 20)); q = stem[k]
        side = rng.choice([-1, 1]); ln = rng.uniform(60, 130)
        p.stroke(spline([tuple(q), (q[0] + side * ln * 0.5, q[1] - ln * 0.35), (q[0] + side * ln, q[1] - ln * 0.1)], 8),
                 rng.uniform(3, 5), rng.uniform(0.15, 0.25) if back else rng.uniform(0.4, 0.65), dry=0.45, taper=(0.05, 0.9))
    if rng.random() < 0.55:                                                     # plume
        for _ in range(7):
            p.stroke([top, (top[0] + rng.normal(-14, 8), top[1] + rng.uniform(18, 34))], 1.1, 0.35, dry=0.5, taper=(0.1, 0.8))
p.mist(1000, 60, 0.45)
p.stage('芦苇')

p.birds([(560, 330, 0.8), (600, 348, 0.6)])
p.title_vertical('月印万川', 150, 150, 92)
p.seal('禅心', 262, 176, 40)
p.save(out, stages_dir=stages)
print('saved', out)
