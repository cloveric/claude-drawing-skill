"""Example (impasto oil): Swirling Sky over the Wheat Field / 麦田星空 — thousands of directional
strokes following a flow field (swirling sky, sweeping wheat, flame-like cypress), with lit paint relief.
Pure code, no image model.
python3 oil_wheatfield.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from oilpaint import OilPainting, hexc
from core import smoothstep, noise2d, polygon_mask, spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'oil_wheatfield.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

o = OilPainting(1920, 1080, seed=1889)
W, H = o.W, o.H
X, Y = o.XX, o.YY
HOR = 600
n1 = noise2d(H, W, 120, 3, 1); n2 = noise2d(H, W, 40, 3, 2)

# ---------------------------------------------------------------- reference colours + flow field
sky = Y < HOR
ref = np.zeros((H, W, 3), np.float32)
ang = np.zeros((H, W), np.float32)

# sky: deep blue with swirling lighter bands around two vortices, a blazing moon
t = np.clip(Y / HOR, 0, 1)[..., None]
ref[:] = hexc('#1c3a8a') * (1 - t) + hexc('#3f71c4') * t
ang[:] = 0.25 * np.sin(X / 210 + Y / 95) + 0.15 * (n1 - 0.5)
for (vx, vy, R, turns) in [(720, 270, 260, 1), (1230, 360, 190, -1)]:
    dxv, dyv = X - vx, Y - vy
    r = np.hypot(dxv, dyv) + 1e-3
    wgt = np.exp(-(r / (R * 1.4)) ** 2)
    tang = np.arctan2(dyv, dxv) + turns * np.pi / 2
    ang = np.arctan2(np.sin(ang) * (1 - wgt) + np.sin(tang) * wgt, np.cos(ang) * (1 - wgt) + np.cos(tang) * wgt)
    band = (0.5 + 0.5 * np.sin(r / 22 + np.arctan2(dyv, dxv) * 2 * turns)) * np.exp(-(r / R) ** 2)
    ref = ref * (1 - 0.8 * band[..., None]) + (hexc('#9cc0ea') * (1 - n2[..., None]) + hexc('#e8eef2') * n2[..., None]) * 0.8 * band[..., None]
MX, MY = 1560, 170
rm = np.hypot(X - MX, Y - MY)
halo = (0.5 + 0.5 * np.cos(rm / 14)) * np.exp(-(rm / 190) ** 2) * (rm > 62)
ref = ref * (1 - 0.85 * halo[..., None]) + hexc('#f3e27a') * 0.85 * halo[..., None]
moon = rm < 62
ref[moon] = hexc('#f7d23e') * (1 - 0.25 * (rm[moon] / 62))[..., None] + hexc('#fff6c8') * 0.25 * (1 - rm[moon] / 62)[..., None]
tang_m = np.arctan2(Y - MY, X - MX) + np.pi / 2
wm = np.exp(-(rm / 230) ** 2)
ang = np.where(rm < 240, np.arctan2(np.sin(ang) * (1 - wm) + np.sin(tang_m) * wm, np.cos(ang) * (1 - wm) + np.cos(tang_m) * wm), ang)
for (sx, sy, sr) in [(300, 120, 26), (1010, 90, 22), (1760, 420, 20), (420, 430, 18), (1330, 120, 16)]:   # smaller stars
    rs = np.hypot(X - sx, Y - sy)
    st = np.exp(-(rs / sr) ** 2)
    ref = ref * (1 - st[..., None]) + hexc('#f6ea9a') * st[..., None]

# distant blue-violet hills on the horizon
hill_y = HOR - 30 - 35 * np.sin(X / 260 + 1.2) - 18 * np.sin(X / 90)
hills = (Y > hill_y) & (Y < HOR + 30)
ref[hills] = (hexc('#4a4f8c') * 0.6 + hexc('#6d5f9e') * 0.4)
ang[hills] = 0.05 * np.sin(X[hills] / 80)

# wheat field: gold with orange and green streaks, strokes sweeping in waves
field = Y >= HOR + 10
f_t = np.clip((Y - HOR) / (H - HOR), 0, 1)
gold = hexc('#e4b93e') * (1 - n1[..., None]) + hexc('#cf8f2a') * n1[..., None]
gold = gold * (1 - 0.35 * (n2[..., None] > 0.7)) + hexc('#7e8f3a') * 0.35 * (n2[..., None] > 0.7)
ref[field] = gold[field] * (0.85 + 0.25 * f_t[field])[..., None]
ang[field] = (-0.35 - 0.55 * np.sin(X[field] / 170 + Y[field] / 60)) * (0.5 + f_t[field])
# a winding dirt path to the horizon
path_x = 980 + 260 * (1 - f_t) ** 0 * np.sin(f_t * 3.2) * f_t + 30 * np.sin(Y / 70) * f_t
path_w = 12 + 190 * f_t ** 1.4
path = field & (np.abs(X - path_x) < path_w)
ref[path] = hexc('#d7b98a') * (0.9 + 0.2 * n2[path])[..., None]
ang[path] = np.arctan2(1.0, 0.25 * np.cos(f_t[path] * 3.2))                                  # strokes run along the path

# a flame-like cypress on the left
cyp_center = 330 + 30 * np.sin(Y / 55)
half = np.clip((Y - 150) / 930, 0, 1) ** 0.7 * 150 * (1 + 0.25 * np.sin(Y / 23))
cyp = (np.abs(X - cyp_center) < half) & (Y > 150)
ref[cyp] = hexc('#1d4b33') * (1 - n2[cyp])[..., None] + hexc('#3a7a45') * n2[cyp][..., None]
ref[cyp & (X > cyp_center + half * 0.2)] = ref[cyp & (X > cyp_center + half * 0.2)] * 0.8 + hexc('#6f9a4a') * 0.2
ang[cyp] = -np.pi / 2 + 0.45 * np.sin(Y[cyp] / 28 + X[cyp] / 40)

# ---------------------------------------------------------------- paint: big -> small strokes
o.layer(ref, ang, length=(60, 110), width=(22, 32), density=2.2, value_jitter=0.05)
o.stage('underpainting')
o.layer(ref, ang, length=(34, 64), width=(11, 17), density=1.9, value_jitter=0.07)
o.stage('strokes')
detail = ((rm < 260) | (np.hypot(X - 720, Y - 270) < 300) | (np.hypot(X - 1230, Y - 360) < 220) | cyp).astype(np.float32)
o.layer(ref, ang, length=(18, 36), width=(6, 10), density=1.6, value_jitter=0.08, mask=detail)
o.stage('detail')
# crows over the field: two short dark strokes each
for (bx, by, sc) in [(1150, 690, 1.0), (1290, 655, 0.8), (1060, 745, 0.75), (1410, 720, 0.9), (1225, 790, 0.65)]:
    o.stroke_at(bx - 17 * sc, by, -0.45, 38 * sc, 9 * sc, '#1b1b24', 1.3)
    o.stroke_at(bx + 17 * sc, by, 0.45, 38 * sc, 9 * sc, '#1b1b24', 1.3)

o.save(out, stages_dir=stages)
print('saved', out)
