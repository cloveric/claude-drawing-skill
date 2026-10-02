"""Example (cave painting, ochre and charcoal by firelight): The Hunt by the Fire / 篝火旁的岩洞 -- a limestone cave
wall painted in red and yellow ochre and charcoal, lit only by a campfire on the floor and a stone fat lamp.
The wall tells one hunt: a great bison, painted on a natural bulge of the rock so the stone gives it its belly and
hump, has turned to face two red hunters running at it with raised spears; two spears already hang in its back. The rest
of the herd runs the other way -- a horse with a black mane, a stag and a hind -- and a second horse above them was
only sketched in charcoal and never coloured. The painters signed with blown hand stencils over the fire (three
red, one black with two fingers bent down); a row of palm dots and a grid sign sit low on the wall. On the floor lie their tools: a flat stone with heaps of ground
ochre, charcoal sticks and a hollow bone for blowing paint. Time: calcite veils, flaked paint, a cave bear's claw
marks and the soot of many fires. No image model.
python3 cave_hunt.py [out.jpg] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from cave import CavePainting

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'cave_hunt.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

cv = CavePainting(1920, 1080, seed=7)

# ---- the wall: limestone, the bulge the bison will stand on, flowstone, cracks, the floor, fire and lamp
cv.wall()
cv.boss(1430, 440, 250, 165, 38)                    # the bison's bulge
cv.boss(880, 540, 190, 120, 26)                     # the horse's flank
cv.fold([(-20, 690), (300, 640), (620, 700), (980, 760), (1240, 700)], height=11, soft=26, side=-1)
cv.flowstone(1830, 1935, top=0, length=430)
cv.crack([(1948, 300), (1905, 335), (1890, 380)], width=2.2, depth=7, branches=0)
cv.floor(966, tilt=1.3)
cv.fire(236, 1032, 262)
cv.lamp(1700, 1004, 128)
cv.stone([(540, 996), (660, 984), (780, 992), (812, 1024), (730, 1050), (580, 1048), (522, 1022)], colour='#8c7a66', height=12)
cv.heap(592, 1010, 30, 'red'); cv.heap(668, 1002, 26, 'yellow'); cv.heap(738, 1016, 20, 'darkred')
cv.stick((598, 1036), (676, 1031), 11, 'black'); cv.stick((690, 1040), (752, 1030), 10, 'black')
cv.stick((850, 1052), (1000, 1020), 16, '#d6c9ad', hollow=True, tip='red')
rng = np.random.default_rng(5)
for x in rng.uniform(380, 1880, 26):                                     # rubble along the foot of the wall
    y = 972 + rng.uniform(0, 26); r = rng.uniform(5, 13)
    if 500 < x < 1020 or 1590 < x < 1800: continue
    cv.stone([(x + np.cos(t) * r * rng.uniform(0.8, 1.2), y + np.sin(t) * r * 0.6) for t in np.linspace(0, 6.28, 8, endpoint=False)],
             colour='#7a6a5a', height=r * 0.6, rough=1.2)
cv.stage('firelit_wall')

# ---- draft the animals and sketch them in charcoal
bison = cv.bison(1440, 482, 440, facing=1, head_drop=0.02)
horse = cv.horse(862, 560, 330, facing=-1, gait='run')
ghost = cv.horse(1085, 232, 262, facing=-1, gait='stand')
stag = cv.deer(470, 500, 230, facing=-1, kind='stag', gait='leap')
hind = cv.deer(522, 762, 190, facing=-1, kind='hind', gait='leap')
for f in (bison, horse, stag, hind):
    cv.sketch(f)
cv.sketch(ghost, strength=0.9, passes=3)
cv.stage('charcoal_sketch')

# ---- red ochre: the bison's body (pale belly left bare), the deer
cv.blow(bison.sel('body'), 'red', density=0.97, rim=0.2, gradient=0.15, relief=0.2, exclude=bison.sel('belly'))
cv.blow(bison.sel('belly'), 'orange', density=0.35, edge=6, halo=8, speckle=0.3)
cv.blow(stag.sel('body', 'ears', 'tail', 'legs'), 'red', density=0.95, rim=0.18, gradient=0.15, exclude=stag.sel('belly'))
cv.blow(hind.sel('body', 'ears', 'tail', 'legs'), 'orange', density=0.85, rim=0.15)
cv.stage('red_ochre')

# ---- yellow ochre: the horse, darker along the back
cv.blow(horse.sel('body'), 'yellow', density=0.97, rim=0.15, exclude=horse.sel('belly'), relief=0.2)
cv.blow(horse.sel('back'), 'orange', density=0.6, edge=8, halo=10, speckle=0.4, clip=horse)
cv.stage('yellow_ochre')

# ---- charcoal and manganese black: heads, manes, humps, legs
cv.blow(horse.sel('head', 'mane', 'ears'), 'black', density=0.97, edge=3, clip=horse, soft_clip=1.5)
cv.blow(horse.sel('legs', 'tail'), 'black', density=0.95, edge=1.6, halo=6, halo_amt=0.1, exclude=horse.sel('body'))
cv.blow(bison.sel('head'), 'darkred', density=0.62, edge=6, halo=8, clip=bison)
cv.blow(bison.sel('hump'), 'black', density=0.95, edge=9, halo=12, relief=0.25, clip=bison)
cv.blow(bison.sel('legs', 'horns', 'tail'), 'black', density=0.95, edge=1.6, halo=6, halo_amt=0.1, exclude=bison.sel('body'))
cv.blow(stag.sel('head'), 'darkred', density=0.7, edge=6, clip=stag)
cv.stage('black')

# ---- the contours and details
cv.outline(bison, 'black', width=7.5, top=0.8, gaps=0.1)
cv.outline(horse, 'black', width=5.5, top=0.7, gaps=0.14)
cv.outline(stag, 'manganese', width=4.0, top=0.6, gaps=0.16)
cv.blow(stag.sel('antlers'), 'black', density=0.9, edge=1.2, halo=6)
cv.outline(hind, 'darkred', width=3.5, gaps=0.2, kind='blow')
cv.outline(ghost, 'black', width=4.5, top=0.9, gaps=0.3, strength=0.9)          # the horse nobody finished
cv.dots([bison.anchors['eye']], r=9, pigment='white', strength=0.9)          # the bison's eye: a pale almond
for f, r in ((bison, 4.5), (horse, 5), (stag, 4), (hind, 3.5)):
    cv.dots([f.anchors['eye']], r=r, pigment='black', strength=0.95)
cv.stage('contours')

# ---- the hunters, their spears, and the spears already in the bison
h1 = cv.hunter(1800, 704, 156, facing=-1, pose='throw')
h2 = cv.hunter(1858, 884, 138, facing=-1, pose='run')
for h in (h1, h2):
    cv.paint(h, 'red', kind='finger')
    g, d = h.anchors['grip'], h.anchors['spear_dir']
    cv.paint(cv.spear(g - d * 70, g + d * 130, 4.0), 'black', kind='charcoal')
cv.paint(cv.spear((1590, 206), (1488, 420), 4.6), 'black', kind='charcoal')
cv.paint(cv.spear((1500, 196), (1432, 404), 4.6), 'black', kind='charcoal')
cv.stage('hunters')

# ---- the painters' hands, palm dots and a grid sign
for (x, y, s, rot, side, pig, fold) in ((104, 372, 124, 16, 'right', 'red', ()), (250, 250, 132, 0, 'left', 'red', ()),
                                         (128, 168, 108, 10, 'right', 'black', (3, 4)), (118, 590, 112, 24, 'left', 'red', ())):
    cv.stencil(cv.hand(x, y, s, rot=rot, side=side, fold=fold), pig, density=0.95, spread=26)
cv.dots([(610 + i * 54, 872 + 6 * np.sin(i * 0.9)) for i in range(8)], r=13, pigment='red')
g = [(1200, 822), (1246, 816), (1292, 819), (1294, 850), (1290, 880), (1244, 884), (1203, 879), (1199, 850), (1200, 822)]
cv.line(g, 5, 'red', kind='finger')
for k in range(1, 4):
    xk = 1200 + k * 23
    cv.line([(xk, 818), (xk + 2, 850), (xk - 1, 882)], 4, 'red', kind='finger')
cv.stage('hands_and_signs')

# ---- time: calcite veils, flakes, a cave bear's claws, soot of many fires
cv.calcite(1236, 600, 100, 66, amount=0.42)
cv.calcite(660, 830, 80, 52, amount=0.35)
cv.flake(28, size=(1.5, 3.5), min_load=0.6)
cv.claws(1790, 120, angle=-100, n=4, length=190, spread=19)
cv.claws(1715, 760, angle=-80, n=3, length=120, spread=16, depth=2.6, width=5)
cv.soot(236, 820, amount=0.22, drift=0.3, spread=0.22)

cv.save(out, stages)
