"""Example (soft 3D): 浮出 · Rise — the word "rise" pushes up through a sea of 84,000 mint candy balls (about
20,000 in view). The balls it shoved aside are heaped around its feet, a few rode up on its shoulders, others
rolled off onto the sea; the dot of the i is a butter-yellow ball. Studio sky dome, a big soft key light,
a pink rim light, ambient occlusion in every crevice, soft shadows, subsurface tint and a shallow depth of field.
No image model.
python3 soft3d_rise.py [out.jpg] [--stages DIR] [--scale 0.5]
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from soft3d import Soft3D

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'soft3d_rise.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
scale = float(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 1.0
t0 = time.time()

# the set is laid out facing the camera, then turned YAW degrees so the rows of the sea run diagonally
YAW = 30.0
c, n = np.cos(np.radians(YAW)), np.sin(np.radians(YAW))
def turn(x, z, ox=0.1, oz=0.5):
    """a point of the layout -> the turned set (rotation about the word's centre)"""
    return ox + (x - ox) * c + (z - oz) * n, oz - (x - ox) * n + (z - oz) * c
ex, ez = turn(-0.9, -6.4); tx, tz = turn(0.15, 0.4)
s = Soft3D(int(1920 * scale), int(1080 * scale), seed=11, eye=(ex, 2.05, ez), target=(tx, 0.74, tz), fov=29,
           record=stages is not None)
s.lens(focus=(0.1, 0.8, 0.5), aperture=0.0085)       # focus on where the word will stand (the turn's pivot)

# ---- the sea: mint balls on a floor, a few pale accents mixed in
MINT = ['#c3ecdc', '#b7e6d2', '#cdf1e3', '#bde9dc']
s.floor('#b9e3d2')
s.ball_field(-30, 30, -14, 52, r=0.1, gap=0.016, colours=MINT + ['#f7f3ea', '#ffd6e2'],
             weights=[30, 30, 20, 20, 1.2, 0.8])
s.stage('ball_sea')

# ---- the word rises through it; the balls it pushed aside heap up around its feet
word = s.text('rise', at=(0.1, 0.0, 0.5), size=2.3, depth=0.46, colour='#ff6d8c', mat='candy', yaw=-7 + YAW,
              spacing=0.03, bob=[0.02, 0.06, 0.24, 0.2], roll=[3, -2, 2.5, -4], turn=[4, 0, -3, 2],
              dot='#ffd45e')
moved = s.part(heap=0.05, reach=0.5, pile=10, pile_top=0.3)   # a low heap: s and e stay legible
s.stage('letters')

# ---- balls that rode up on the letters, and balls that rolled off
for x, z in [(-1.05, 0.52), (0.62, 0.45), (1.38, 0.5)]:
    s.drop(*turn(x, z), 0.1, MINT[0], roll=0)
for x, z, col in [(-1.9, -0.35, '#c7b6f6'), (1.9, 0.1, '#ffd45e'), (-0.4, -0.6, MINT[1]), (0.9, -0.9, '#ffb3c8'),
                  (2.6, -0.8, '#c7b6f6'), (-2.7, 0.9, '#ffd45e'), (-3.4, -1.4, '#ffb3c8'), (3.3, 1.8, '#a9d3ff'),
                  (-1.2, 2.6, '#c7b6f6'), (0.2, -1.8, '#a9d3ff'), (4.2, -1.2, '#ffd45e')]:
    s.drop(*turn(x, z), 0.1, col, roll=30)
s.stage('loose_balls')

# ---- light it
s.sky(top='#b6a3ee', horizon='#e9cbe9', strength=1.22, haze=42, haze_start=9)
s.stage('sky_light')
s.key(azimuth=-62, elevation=44, colour='#fff4ea', strength=1.62, size=12)
s.rim(azimuth=150, elevation=22, colour='#ffd0e0', strength=1.8)
s.softbox(azimuth=30, elevation=35, width=26, height=10, strength=0.72)
s.stage('key_and_rim')
s.film(bloom=0.25, vignette=0.2, grain=0.006)
print('balls pushed aside:', moved, ' loose balls:', len(s.br))

s.save(out, stages_dir=stages)
print('saved', out, f'{time.time() - t0:.1f}s')
