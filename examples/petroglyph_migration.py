"""Example (petroglyph, pecked sandstone): Migration Season / 迁徙季 -- a panel of rock art hammered through desert
varnish. A herd of bighorn sheep (rams, ewes, two lambs) walks one way along the rock toward a spring; hoofprints run
ahead of the lead ram to the concentric rings of the waterhole, where a bowman waits; a second hunter with a raised
atlatl follows the herd. Up top a spiral sun and a crescent moon with two rows of ground tally marks (a month of days).
Two hands are pecked on the lower face under the ledge. Older work shows through, re-varnished almost to a ghost: a
wavy river line and a large rake. The rock has cracks that bleed darker varnish streaks, spalls that took part of the
older work with them, and lichen. No image model.
python3 petroglyph_migration.py [out.jpg] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from petroglyph import Petroglyph

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'petroglyph_migration.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

pg = Petroglyph(1920, 1080, seed=11)

# ---- the sandstone face, a ledge, desert varnish, cracks
pg.rock()
pg.ledge(912, drop=34)
pg.stage('sandstone')
pg.varnish()
pg.fracture([(1010, -10), (985, 120), (948, 260), (930, 340)], width=3.2, depth=10, seep=0.7, branches=2)
pg.fracture([(1930, 610), (1840, 700), (1760, 800), (1716, 912)], width=3.6, depth=11, seep=0.6, branches=1)
pg.fracture([(560, 1090), (600, 1000), (640, 930)], width=2.6, depth=8, seep=0.0, branches=1)
pg.stage('varnish')

# ---- older work, re-varnished almost to a ghost: a wavy river line and a big rake
river = [(380, 846), (520, 806), (660, 856), (800, 816), (940, 862), (1080, 822), (1220, 858), (1330, 828)]
pg.peck(pg.meander(river, 16), age=0.66, density=0.8)
rake = pg.meander([(700, 410), (1010, 392)], 14, smooth=False)
for i in range(7):
    x = 712 + i * 49
    pg.meander([(x, 400 - i * 2.6), (x + 4, 462 - i * 2.6)], 12, into=rake, smooth=False)
pg.peck(rake, age=0.6, density=0.85)
pg.stage('old_marks')

# ---- sky: spiral sun, crescent moon and a month of ground tally marks
pg.peck(pg.sun_spiral(1590, 215, 100, turns=3.0, rays=13, width=13))
pg.peck(pg.crescent(150, 168, 62, thick=0.45, rot=-20), age=0.32)                 # the day count is older
pg.abrade_tally(250, 112, [15, 14], gap=27, length=58, width=8.5, row_gap=86, slant=5, age=0.3)
pg.stage('sun_and_days')

# ---- the herd, walking right (uphill) toward the spring: big animals in the upper file, ewes and lambs below
herd = [(330, 712, 132, 'ewe', 0.6), (500, 608, 160, 'ram', -0.5), (520, 770, 92, 'lamb', -0.8),
        (720, 590, 142, 'ewe', 0.7), (870, 716, 128, 'ewe', -0.3), (935, 566, 166, 'ram', -0.7),
        (1035, 742, 94, 'lamb', 0.4), (1135, 548, 146, 'ewe', 0.5), (1330, 520, 192, 'ram', 0.6)]
for i, (x, y, s, kind, g) in enumerate(herd):
    pg.peck(pg.bighorn(x, y, s, facing=1, kind=kind, gait=g, rot=4))
    if i == 4: pg.stage('herd_rear')
pg.stage('herd')

# ---- hoofprints from the lead ram down to the waterhole; the bowman waiting beyond it; a hunter following
pg.peck(pg.hoofprints([(1468, 628), (1520, 656), (1572, 680)], size=34, every=50, stagger=10), size=0.66)
pg.peck(pg.concentric(1672, 724, 78, rings=3, width=11))
pg.peck(pg.hunter(1815, 560, 236, facing=-1, weapon='bow'))
pg.peck(pg.hunter(140, 600, 214, facing=1, weapon='atlatl'), age=0.3)
pg.stage('hunt')

# ---- two hands on the lower face, under the ledge: a grown-up's and a child's
pg.peck(pg.hand(1330, 1004, 132, rot=-8))
pg.peck(pg.hand(1462, 1012, 98, rot=12, spread=1.15), size=0.62, density=1.2)
pg.stage('hands')

# ---- time: spalls take part of the old work, lichen in the shade of the ledge and along cracks
pg.spall([(292, 1080), (300, 1030), (338, 984), (372, 960), (430, 928), (488, 918), (540, 934), (552, 972),
          (526, 1010), (506, 1048), (480, 1080)], depth=9, impact=(440, 1000))
pg.spall([(1920, 0), (1920, 156), (1884, 140), (1850, 118), (1828, 84), (1812, 40), (1800, 0)], depth=7, impact=(1900, 26), age=0.12)
pg.spall([(1236, 806), (1262, 786), (1300, 780), (1338, 792), (1356, 818), (1344, 846), (1306, 856), (1268, 850), (1246, 832)],
         depth=5, impact=(1300, 815), age=0.3)
pg.lichen(1010, 992, 50, 'green', n=7)
pg.lichen(1790, 952, 38, 'orange', n=6)
pg.lichen(968, 152, 30, 'green', n=4)

pg.save(out, stages_dir=stages)
print('saved', out)
