"""Example (low poly): 峡谷飞行 · Canyon Run — one frame of an imaginary 1999 flying game, rendered by a tiny
software rasterizer: a small white-and-teal stunt plane banks into a right-hand bend of a desert canyon, lining up
the fifth of nine gold hoops; the sixth hangs under a natural stone arch and the rest swing round the bend toward
the finish. Stepped strata walls (one in sun, one in lavender shade), a river of uneven facets, billboard junipers,
boulders, buttes dissolving in the per-vertex fog; a half-transparent propeller disc, a lens flare; everything
crushed to 15-bit colour through the 4x4 dither and blown up x5 with no smoothing.
HUD: hoop counter, lap time, stepped speed bar, altitude, course minimap. No image model.
python3 lowpoly_canyon.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from lowpoly import LowPoly, HUD_GREEN

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'lowpoly_canyon.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

g = LowPoly(1920, 1080, scale=5, seed=1999, record=stages is not None, far=270)
path = g.path([(0, -60), (0, -20), (0, 10), (4, 35), (16, 58), (36, 76), (60, 88), (88, 96), (120, 102),
               (150, 110), (175, 128), (190, 155), (196, 190), (194, 240), (186, 300)])

# ---- the shot: a chase camera at the right-rear of the plane, the plane on the lower-left third
S_PLANE = 70.0
plane = g.along(path, S_PLANE, u=-1.5, y=14.0)
fwd = g.heading(path, S_PLANE); right = np.array([fwd[2], 0, -fwd[0]])
g.camera(eye=plane - fwd * 11 + right * 4.0 + [0, 2.6, 0], target=plane, fov=52, roll=-3)
g.aim(plane, at=(0.35, 0.68))

g.sky('#33509e', '#c4bedd', glow='#fff2cc')
g.sun(screen=(0.4, 0.1))
g.light(lift=26)                       # shade as if the sun stood higher, as games of the era did
g.stage('sky')

# ---- the canyon, the river, buttes on the plateau, the arch over the sixth hoop
g.canyon(path, s0=0, s1=330, step=7.0, height=0.75)
g.river(path, s0=0, s1=330, step=7.0)
for s, u, rad, h in ((150, -70, 14, 24), (200, -55, 11, 30), (250, 60, 18, 20), (280, -45, 15, 26), (120, 70, 9, 18)):
    p = g.along(path, s, u=u)
    g.mesa(p[0], p[2], rad, h, base=29.5)
g.arch(path, 121, span=44, rise=10, base=21)
g.stage('wireframe', wire=True)
g.stage('flat', fog=False, textures=False)
g.stage('textures', fog=False)

# ---- junipers on the banks and ledges, boulders in the river
r = np.random.default_rng(7)
for s in np.arange(60, 240, 8.0):
    for side in (-1, 1):
        if r.random() < 0.55:
            k = r.choice(3, p=[0.5, 0.3, 0.2])
            u, y = [(9.2, 0.9), (15.8, 11.8), (20.6, 20.0)][k]
            p = g.along(path, s + r.uniform(-3, 3), u=side * (u + r.uniform(-0.6, 0.8)), y=y - 0.2)
            g.tree(*p, height=r.uniform(3.0, 4.6))
for s, u in ((78, -4.5), (96, 5.2), (131, -5.0), (150, 3.5), (171, -2.5)):
    p = g.along(path, s, u=u)
    g.boulder(p[0], -0.1, p[2], r=r.uniform(0.9, 1.5))
g.fog(55, 250)
g.stage('fog')

# ---- the course: nine hoops (four already flown), the plane lining up the fifth
course = [(0, 0.0, 12.0), (15, 1.5, 11.0), (30, -1.0, 13.0), (45, 0.5, 12.0),
          (90, 1.0, 14.0), (121, 1.0, 16.0), (147, -1.0, 18.0), (178, 2.0, 15.0), (210, 0.0, 19.0)]
hoops = []
for s, u, y in course:
    c = g.along(path, s, u=u, y=y)
    hoops.append(c)
    g.ring(c, g.heading(path, s), radius=3.4)
g.stage('hoops')

aim = hoops[4] - plane
g.aircraft(plane, aim, roll=34, pitch=3)
g.stage('plane')

# ---- sparkles on the next hoop, the lens flare
for k in (2, 6):
    a = np.radians(110 + k * 28)
    g.sparkle(hoops[4] + np.array([np.cos(a) * 3.4, np.sin(a) * 3.4, -0.7]), size=2.6)
g.flare()
g.stage('effects')

# ---- HUD
g.counter('HOOPS', '04/09', 8, 6, icon='ring')
g.counter('LAP 2/3', "1'07\"42", 376, 6, anchor='r')
g.gauge(8, 196, 0.72, label='SPD', number='214', unit='KM/H')
g.text('ALT 014 M', 8, 170, 1, HUD_GREEN)
g.minimap(306, 136, 378, 208, path, 0, 225, hoops, done=4, plane=plane, heading=aim, finish=g.along(path, 214),
          title='MESA RUN')

g.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s')
