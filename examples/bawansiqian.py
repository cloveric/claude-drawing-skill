"""范例：「八万四千法门」— 很多条路，同一个山顶。纯代码水墨，约 3 秒出图。
python3 bawansiqian.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from inkpaint import Painting

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'bawansiqian.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

p = Painting(1920, 1080, seed=84000)
p.paper()
p.stage('宣纸')

# far -> near: each wash occludes what is behind it
far = p.ridge(560, peaks=[(420, 150, 330), (1650, 110, 260)], rough=26, rough_scale=220, seed=11)
p.wash(far, dens=0.16, decay=170, tex=140, edge=0.25, mist_y=700, mist_h=110, seed=21)
mid = p.ridge(690, peaks=[(700, 120, 260), (1580, 150, 300)], rough=30, rough_scale=160, seed=12)
p.wash(mid, dens=0.26, decay=150, tex=110, edge=0.3, mist_y=800, mist_h=90, seed=31)
p.stage('远山')

SX, SY = 1130, 252
main = p.peak(SX, SY, height=560, left_w=360, right_w=470, shoulders=[(SX + 250, 70, 90), (SX - 300, 45, 110)], seed=13)
p.wash(main, dens=0.46, decay=240, tex=90, edge=0.45, mist_y=920, mist_h=80, seed=41)
p.cun(main, SX - 600, SX + 600, n=150, shadow_x=SX, max_y=960)
p.moss(main, SX - 600, SX + 620, n=70)
p.ridge_line(main, SX - 680, SX + 640)
p.stage('主峰')

paths = p.trails(main, (SX, SY), n=16, red_index=7, seed=5)
p.mist(960, 70, 0.8)
p.mist(760, 45, 0.55)
for (i, t) in [(3, 0.45), (9, 0.35), (12, 0.6), (5, 0.3), (7, 0.62)]:
    q = paths[i][int(t * (len(paths[i]) - 1))]
    p.traveller(q[0], q[1])
p.pagoda(SX, SY)
p.stage('小路')

rock = 800 + 280 * ((p.xs / 640) ** 1.6) + 30 * __import__('inkpaint').fbm1d(1920, 70, 4, 91)
rock[p.xs > 640] = 2000
p.rock(rock)
p.pine((250, 1000), (330, 600), bend=70,
       branches=[((304, 760), (480, 705), -34), ((318, 690), (170, 648), 28), ((326, 640), (455, 588), -22), ((292, 830), (150, 808), 22)],
       extra_tufts=[(335, 590), (395, 612)])
p.stage('松石')

p.sun(1500, 190, 46)
p.birds([(1330, 300, 1.0), (1370, 322, 0.8), (1300, 334, 0.7)])
p.title_vertical('八万四千', 150, 150, 92)
p.seal('法门', 262, 176, 40)
p.save(out, stages_dir=stages)
print('saved', out)
