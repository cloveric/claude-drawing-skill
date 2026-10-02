"""Example (flat vector): 山间夜营 · Night Camp — the last stretch back to camp after a day on the mountain.

A layered flat landscape at night. The moon, crowned with orange rays, hangs over the left; the big snowy peak on
the right still has the little orange flag planted on its summit this afternoon. A dashed trail runs from that
flag down the switchbacks, across the magenta hills and out onto the sand, where one tiny hiker with a head torch
is walking the last few hundred metres. The camp is already lit: an orange A-frame tent with a glowing door and a
campfire whose flat rings of light spread over the sand. Big shapes, seven colours, lots of empty sky.

How it was made, in order: night sky and halo -> moon, rays, stars -> mountain ranges (lit / shade faces, snow
caps) -> clouds -> hill bands -> sand -> trees -> trail and summit flag -> camp (tent, fire, light, smoke) ->
hiker and a shooting star. No image model.
python3 flatvector_night_camp.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from flatvector import FlatVector, tone, mix, NIGHT, PLUM, BERRY, EMBER, SAND, PINE, CREAM

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'flatvector_night_camp.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

W, H = 1920, 1080
MOON = (400, 255, 112)
SUMMIT = (1390, 300)
HORIZON = 772
HIKER = (812, 856)
TENT = (1310, 952)
FIRE = (1040, 962)

fv = FlatVector(W, H, seed=11)

# ---------------------------------------------------------------- 1 sky
fv.backdrop(NIGHT)
fv.stage('sky')

# ---------------------------------------------------------------- 2 moon and stars
fv.moon(*MOON, rays=18)
fv.stars(120, box=(0, 0, W, 560), avoid=[(MOON[0], MOON[1], 265), (1660, 175, 190)])
for x, y, r in ((1010, 110, 9), (1560, 330, 7), (180, 120, 8), (760, 420, 6), (1840, 470, 6)):
    fv.sparkle(x, y, r)
fv.stage('moon_stars')

# ---------------------------------------------------------------- 3 mountains
far = tone(PLUM, -0.3)
fv.mountain((690, 500), (380, 800), (1010, 800), far, lift=5, shade=-0.16, seed=1)
fv.mountain((1080, 470), (780, 800), (1380, 800), far, lift=5, shade=-0.16, seed=2)
fv.mountain((1800, 455), (1540, 800), (2080, 800), far, lift=5, shade=-0.16, seed=3)
fv.mountain((1730, 400), (1390, 800), (2140, 800), PLUM, snow=0.2, lift=8, seed=4)
peak = fv.mountain(SUMMIT, (860, 800), (1930, 800), PLUM, snow=0.22, lift=9, seed=5,
            ridge=[(1418, 390), (1396, 470), (1440, 560), (1425, 820)])
fv.mountain((175, 470), (-260, 800), (600, 800), PLUM, snow=0.2, lift=8, seed=6)
fv.mountain((470, 545), (250, 800), (760, 800), tone(PLUM, 0.06), snow=0.18, lift=8, seed=7)
fv.stage('mountains')

# ---------------------------------------------------------------- 4 clouds
fv.cloud(1660, 172, 330, seed=1)
fv.cloud(860, 230, 190, seed=2)
fv.stage('clouds')

# ---------------------------------------------------------------- 5 hills
fv.land([(-60, 642), (330, 612), (760, 655), (1150, 628), (1560, 664), (1980, 632)], tone(BERRY, -0.18), lift=9)
fv.land([(-60, 694), (420, 668), (880, 704), (1320, 684), (1720, 706), (1980, 690)], BERRY, lift=10)
for x, b, h in ((1490, 694, 70), (1528, 700, 52), (1610, 708, 62), (95, 676, 64), (132, 684, 48)):
    fv.pine(x, b, h, tone(PINE, -0.12), tiers=2, lift=3)
fv.land([(-60, 738), (520, 726), (1180, 744), (1980, 730)], EMBER, lift=10)
fv.stage('hills')

# ---------------------------------------------------------------- 6 sand
fv.land([(-60, HORIZON), (700, HORIZON - 4), (1400, HORIZON + 3), (1980, HORIZON - 2)], SAND, lift=12, shadow=0.42)
fv.dashes((0, HORIZON + 30, W, H - 60), [tone(SAND, 0.3), tone(SAND, -0.16)], n=16, seed=3, horizon=HORIZON)
for x, y, r in ((620, 980, 11), (1610, 1010, 9), (300, 830, 6), (1830, 850, 7)):
    fv.pebble(x, y, r, tone(SAND, -0.25))
for x, y, h in ((520, 1030, 30), (1480, 990, 24), (760, 860, 16), (1720, 905, 18)):
    fv.tuft(x, y, h, tone(PINE, 0.05))
fv.stage('sand')

# ---------------------------------------------------------------- 7 trees
fv.round_tree(255, 915, 92, tone(PINE, 0.1), seed=1)
fv.pine(85, 985, 360, tiers=3)
fv.pine(395, 940, 210, tiers=3)
fv.pine(1700, 965, 300, tiers=3)
fv.pine(1855, 1020, 520, tiers=3)
fv.land([(-60, 1012), (380, 1040), (960, 1060), (1520, 1044), (1980, 1018)], tone(SAND, -0.1), lift=8, shadow=0.3)
fv.stage('trees')

# ---------------------------------------------------------------- 8 trail and flag
path = fv.trail([(SUMMIT[0] - 2, SUMMIT[1] + 14), (1372, 340), (1338, 372), (1432, 420), (1318, 488), (1410, 548), (1262, 612),
          (1080, 650), (860, 680), (680, 708), (668, 760), (730, 818), HIKER])
fv.fill(path & peak['snow'], mix(PLUM, CREAM, 0.25), texture=0)     # on the snow the dashes go violet
fv.flag(SUMMIT[0] + 2, SUMMIT[1] + 4, 46)
fv.stage('trail')

# ---------------------------------------------------------------- 9 camp
fv.glow(FIRE[0], FIRE[1] + 6, 400, 118, tone(SAND, 0.5), rings=4, alpha=0.2)
fv.glow(TENT[0] + 4, TENT[1] + 6, 150, 30, tone(SAND, 0.6), rings=3, alpha=0.3)
fv.tent(*TENT, 262, 172)
fv.campfire(*FIRE, s=0.9)
fv.stage('camp')

# ---------------------------------------------------------------- 10 hiker, meteor
fv.hiker(*HIKER, 72, facing=1)
fv.shooting_star((1150, 150), (1360, 62), r=3)

fv.save(out, stages)
print(f'{out}  {time.time() - t0:.1f}s')
