"""Example (Art Deco / Streamline poster): NIGHT EXPRESS — a 1930s airbrushed railway poster for a (fictional)
overnight train from the city to the coast. It tells one small thing: the night express pulls out at 23:40 -- the
clock on the tallest tower says twenty to twelve -- and runs out of the lit city over the river viaduct toward
the coast, sleeping-car blinds already half drawn. A full moon rises over the stepped skyline inside a sunburst of
alternating rays, searchlights sweep the sky, the river mirrors it all in ripple dashes; the streamlined
locomotive (bullet nose, gold speed stripes that converge on the nose) comes at us with its headlamp beam.
Every surface is a sprayed gradient through a cut frisket -- no outlines anywhere. No image model.
python3 artdeco_express.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from artdeco import ArtDeco, GOLD, IVORY

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'artdeco_express.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

a = ArtDeco(1920, 1080, seed=1938)
W, H = a.W, a.H
HZ = 690                                   # horizon row (the camera is level)
MX, MY, MR = 1190, 432, 100                # the moon

# ---- 1. the sky: one long airbrushed fade, midnight blue down to the green glow over the city
a.sky([(0, '#060d24'), (0.38, '#0d1f3f'), (0.72, '#1b4a5c'), (1, '#4c9488')], bottom=HZ)
a.stage('sky')

# ---- 2. moonburst: alternating rays, then the moon and its halo
a.burst(MX, MY, rays=40, contrast=0.13, reach=1300, colour='#cfeadb', glow=0.55, phase=4.5, bottom=HZ)
a.moon(MX, MY, MR)
a.stage('moonburst')

# ---- 3. the far city in the haze, searchlights behind it
for x, ang, ln in ((1560, 116, 900), (840, 62, 820), (1720, 98, 700)):
    a.searchlight(x, HZ - 210, ang, ln, spread=1.7, strength=0.2)
far = [(640, 70, 150), (700, 60, 210), (760, 80, 120), (905, 70, 230), (990, 64, 170), (1060, 76, 220),
       (1300, 70, 200), (1370, 60, 250), (1590, 80, 230), (1680, 60, 280), (1760, 90, 190), (1850, 70, 250)]
for x, w, h in far:
    a.tower(x, HZ, [(w, h * 0.6), (w * 0.72, h * 0.28), (w * 0.45, h * 0.12)], far=0.72, flutes=3, windows=0.12,
            light=-1 if x < MX else 1, ledge=2)
a.stage('far_city')

# ---- 4. the near towers: set-backs, fluting, lit windows; the clock tower says 11:40
a.tower(820, HZ, [(120, 140), (92, 70), (60, 50)], flutes=4, windows=0.4, light=-1, spire=110, spire_w=22,
        far=0.25)
a.tower(985, HZ, [(110, 190), (80, 80), (52, 46)], flutes=5, slits=4, light=-1, spire=60, far=0.2)
a.tower(1290, HZ, [(96, 120), (70, 70)], flutes=4, windows=0.3, light=1, far=0.35)
cx, cy = a.tower(1470, HZ, [(170, 170), (132, 80), (100, 64)], flutes=6, windows=0.45, light=1, ledge=3,
                 top_windows=False)
a.clock(cx, cy + 33, 23, 11, 40)                      # departure time: twenty to twelve
top = a.crown(cx, cy, 100, steps=3)
a.tower(cx, top + 3, [(6, 3)], mast=22, ledge=0)
a.tower(1665, HZ, [(150, 160), (110, 110), (70, 56)], flutes=5, slits=5, light=1, spire=90, spire_w=20, far=0.15)
a.tower(1835, HZ, [(140, 240), (96, 80)], flutes=4, windows=0.35, light=1, far=0.3)
a.stage('towers')

# ---- 5. the river: mirrors the sky and the city in ripple dashes
a.water(HZ, stops=((0, '#1f5560'), (0.35, '#0f2c40'), (1, '#050b1d')), reflect=0.7)
a.stage('river')

# ---- 6-8. the streamliner on its viaduct: friskets, modelling, lights
a.camera(f=1500, cx=960, horizon=HZ, height=12.0)
r = a.express(nose=(-6.9, 23.8), vp_x=1180, cars=9, moon=(MX, MY))
a.frisket(r)
a.stage('friskets')
a.model(r)
a.stage('modelling')
a.lights(r, beam_len=760, reflect=False)
a.stage('lights')

# ---- 9. lettering, small print, gilt border
title = 'NIGHT EXPRESS'
cap = 124
wt = a.deco_width(title, cap, track=0.16)
a.lettering(title, W / 2, 228, cap, track=0.16, anchor='m', shadow=(6, 6))
sw = a.caption('OVERNIGHT  ·  FROM THE CITY TO THE COAST', W / 2, 286, 25, colour='#e9dcbc', track=0.42,
               anchor='ms')
a.rule(W / 2 - wt / 2, W / 2 - sw / 2 - 28, 277, 2, GOLD)
a.rule(W / 2 + sw / 2 + 28, W / 2 + wt / 2, 277, 2, GOLD)
a.caption('DEPARTS 23:40', 1880 - 60, 1000, 30, colour=IVORY, track=0.36, anchor='rs')
a.caption('SLEEPING CARS  ·  DINING CAR  ·  ARRIVES AT DAWN', 1880 - 60, 1036, 19, colour='#d8c9a4', track=0.38,
          anchor='rs')
a.border()
a.stage('lettering')

# ---- the print
a.finish()
a.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s')
