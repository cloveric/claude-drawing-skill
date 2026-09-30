"""Example (synthwave): 海岸线 1987 · Coastline 1987 — a home video of the last sunset of summer 1987, played back
off a worn tape: a striped sun sinking into the sea behind a low wireframe island, its reflection broken into
glowing bars on the water; a coast road with neon edges running to a small lit city at the vanishing point; a
magenta grid across the land, wireframe mountains beyond; palm silhouettes rimmed by the sunset; one car's
tail lights heading for the city; chrome COASTLINE with a neon-script "Last Sunset"; VCR on-screen display
(PLAY, date and time), chroma bleed, a tracking band and scanlines. No image model.
python3 synthwave_coastline.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from synthwave import Synthwave, MAGENTA, CYAN, PINK

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'synthwave_coastline.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

s = Synthwave(1920, 1080, seed=1987, horizon=610, vp_x=1060, focal=1100, eye=3.5, record=stages is not None)

# ---- dusk sky and stars
s.sky()
s.stars(n=1700, bright=16)
s.stage('sky')

# ---- the striped sun sinking into the sea
s.sun(560, 585, 255, bands=8, band_top=0.36)
s.stage('sun')

# ---- far shore: a low wireframe island in front of the sun, mountains beyond the land, the city at the road's end
s.mountains(-2700, -1250, 1650, 2300, 60, cell=(70, 120), level=0.7)
s.mountains(230, 1500, 900, 1750, 210, cell=(52, 85), taper=(True, False))
s.skyline(5, 175, 780, heights=(14, 60), widths=(10, 24), tall=(112, 100), windows=0.22)
s.stage('far')

# ---- the neon grid, the sea, the coast road
s.floor(MAGENTA, spacing=(2.4, 2.4), width=0.07)
s.stage('grid')
s.sea(coast=-9.0)
s.neon_line(-9.0, CYAN, width=0.16, level=1.0)
s.road(-7.0, -2.0)
s.stage('sea')

# ---- palms along the beach and the roadside, one car heading for the city
for X, Z, h, lean in ((-8.3, 29, 11.5, -0.07), (-8.4, 47, 10.5, 0.09), (-8.2, 82, 10.0, -0.05)):
    s.palm(X, Z, h, lean)
for X, Z, h, lean in ((-0.9, 104, 11.0, -0.04), (-0.9, 73, 10.0, 0.06),
                      (-0.9, 52, 11.5, -0.03), (-0.9, 36, 10.5, 0.05)):
    s.palm(X, Z, h, lean)
s.car(-3.4, 31)
s.stage('palms')

# ---- lettering
s.caption('海岸线 1987 · 夏天的最后一次日落', 1450, 96, 27, CYAN, rules=(70, 20))
s.chrome_text('COASTLINE', 1450, 215, 150)
s.neon_script('Last Sunset', 1575, 352, 112, PINK, rot=7)
s.stage('title')

# ---- played back off tape
s.osd('PLAY ▶', 84, 70, px=6)
s.osd('PM 7:42', 1836, 960, px=5, anchor='rb')
s.osd('AUG.31 1987', 1836, 1010, px=5, anchor='rb')
s.vhs()
s.save(out, stages_dir=stages)
print('saved', out, f'{time.time() - t0:.1f}s')
