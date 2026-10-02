"""Example (1930s black-and-white rubber-hose cartoon): Seven O'Clock / 早晨的闹钟 — a frame from an old cartoon
short, printed on worn film. Seven o'clock in a little bedroom: the twin-bell alarm clock has leapt up on the
nightstand to ring, one shoe on tiptoe and one kicked out, waving a white glove and pointing at the bed; the
striker smears between the bells and "RRRING!" bounces overhead. In the bed a pillow in a striped night-cap snores
on and holds up a glove -- five more minutes. The sun, yawning, stretches its arms over the hills outside the
window, and a pair of slippers on the braided rug is already dancing. Grey gouache background, inked and painted
cels, pie-cut eyes, rubber-hose limbs; then lens softness, grain, gate weave, a rounded gate, scratches, dust and
a hair in the gate. No image model.
python3 rubberhose_morning.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from rubberhose import RubberHose, ellipse_pts, WHITE, LIGHT, BLACK

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'rubberhose_morning.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

rh = RubberHose(1920, 1080, seed=11)

# ---- background: painted once on board, in grey gouache
FLOOR = 720
rh.wall(FLOOR)
rh.floor(FLOOR)
win = rh.window(120, 110, 600, 590, valley=372, horizon=528)
rh.valance(84, 636, 92, 146)
rh.curtain(66, 236, 104, 660, 404, 'left')
rh.curtain(484, 654, 104, 660, 404, 'right')
beam = [(178, 736), (566, 736), (742, 1080), (40, 1080)]           # the sunbeam through the window
rh.light(beam, 0.45, 9)
rh.light([(170, 812), (600, 812), (612, 834), (160, 834)], -0.2, 4)  # shadow of the sash rail across it
rh.rug(420, 960, 300, 70)
stand_top = rh.nightstand(770, 1090, 640, 830, 862)
bed = rh.bed(1300, 1820, 330, 600, 860, 940)
rh.sampler(1450, 140, 1680, 278, ['RISE &', 'SHINE'])
rh.stage('layout', view='layout')
rh.stage('background', view='background')

# ---- the actors, roughed out in pencil (back to front)
rh.sun(372, 482, 78, clip='window',
       arms=[dict(side=-1, at=(282, 372), bend=-30, pose='fist'), dict(side=1, at=(466, 366), bend=30, pose='fist')])

rh.pillow(1556, 592, 320, 146, tilt=0.0, clip='bed',
          arm=dict(at=(1392, 528), bend=-26, pose='palm', angle=-2.1, flip=-1))

clock = rh.alarm_clock(
    935, 412, 125, tilt=0.1, look=(0.75, -0.15), time=(7, 0),
    legs=[dict(side=1, at=(990, 590), bend=-18, facing=1, tilt=0.55),
          dict(side=-1, at=(735, 560), bend=34, facing=-1, tilt=-0.35)],
    arms=[dict(side=-1, at=(706, 262), bend=-40, pose='open', angle=-2.3),
          dict(side=1, at=(1176, 372), bend=-26, pose='point', angle=0.05)])

rh.slipper(318, 908, 118, facing=1, tilt=-0.22)
rh.slipper(500, 978, 118, facing=1, tilt=0.06)
rh.stage('pencil')
rh.ink()
rh.stage('ink')
rh.paint()
rh.stage('paint')

# ---- effects: shake, ring, snore, hop
for bc, a in rh.bells:
    out_ang = -np.pi / 2 + a + 0.1
    rh.vibration(bc[0], bc[1], 125 * 0.42, out_ang - 0.55, out_ang + 0.55, n=3, gap=15)
for sgn in (-1, 1):
    p = clock.p(1.18 * sgn, 0.42)
    for k in range(2):
        rh.stroke([(p[0] + sgn * 12 * k, p[1] - 22 + 10 * k), (p[0] + sgn * (12 * k + 16), p[1] + 6 + 10 * k)], 5,
                  (0.3, 0.3), effect=True)
rh.star(790, 236, 17, rot=0.2)
rh.star(1088, 226, 14, rot=-0.3)
rh.star(1040, 160, 9, rot=0.5)
rh.lettering('RRRING!', [(690, 150), (935, 92), (1185, 140)], 86)
rh.zzz(1735, 470, 30)
for a in (-0.9, -0.35, 0.2):                                         # tap, tap on the tabletop
    rh.stroke([(1062 + 30 * np.cos(a), 650 + 30 * np.sin(a)), (1062 + 54 * np.cos(a), 650 + 54 * np.sin(a))], 4.5,
              (0.2, 0.5), effect=True)
for k in range(2):                                                  # the hop
    rh.stroke([(276 - 8 * k, 968 + 14 * k), (318, 978 + 16 * k), (362 + 8 * k, 968 + 14 * k)], 4.5, (0.35, 0.35),
              effect=True)
rh.shadow(955, 632, 110, 8, 0.5)
rh.shadow(320, 984, 54, 8, 0.4)
rh.shadow(504, 1000, 62, 9, 0.5)
rh.stage('effects')

# ---- shot on black-and-white film, then a hundred runs through the projector
rh.film()
rh.stage('film')
rh.age()
rh.save(out, stages_dir=stages)
print('saved', out)
