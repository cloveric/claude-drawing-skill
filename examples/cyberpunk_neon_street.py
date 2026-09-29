"""Example (cyberpunk): 霓虹不夜城 · Neon District — a rain-soaked street canyon at night seen from the kerb:
perspective towers with window grids, blade signs of real neon tubes (a dead tube, a flickering one), backlit
lightboxes, a footbridge gate over the street, a holographic jellyfish ad glowing through the haze, cables,
flying-car light trails, steam from the grates, a lone figure under a clear umbrella, and the whole street
mirrored in wet asphalt and puddles; finished with bloom, halation, grain and a single torn scanline.
No image model.
python3 cyberpunk_neon_street.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from cyberpunk import Cyberpunk, MAGENTA, CYAN, AMBER, RED

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'cyberpunk_neon_street.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

c = Cyberpunk(1920, 1080, seed=2077, focal=1150, vp=(940, 560), eye=1.7, fog=125, wall=9.5, road=6.0,
              record=stages is not None)

# ---- sky and the far city beyond the end of the street
c.sky()
c.skyline(z=900, x_range=(-760, 760), heights=(140, 460), widths=(30, 90), colour='#1b1d36')
c.skyline(z=460, x_range=(-320, 320), heights=(70, 250), widths=(18, 50), colour='#151830')
c.stage('sky')

# ---- the canyon: blocks on both sides, near to far (z0, z1, height, wall, colour, lit)
left = [(6, 22, 42, 9.5, '#2b2f3c', 0.30), (22, 34, 30, 9.8, '#30303a', 0.35), (34, 52, 58, 9.3, '#272c38', 0.28),
        (52, 70, 34, 9.6, '#2e2c36', 0.35), (70, 95, 64, 9.4, '#282d3a', 0.3), (95, 130, 46, 9.7, '#2c2e38', 0.35),
        (130, 185, 82, 9.5, '#272b36', 0.3), (185, 270, 56, 9.5, '#2a2d38', 0.3)]
right = [(6, 18, 36, 9.5, '#2e2f3a', 0.3), (18, 36, 72, 9.3, '#282c38', 0.3), (36, 50, 26, 9.6, '#302f38', 0.35),
         (50, 72, 60, 9.4, '#2a2e3a', 0.3), (72, 100, 42, 9.8, '#2d2f39', 0.35), (100, 140, 74, 9.5, '#282c37', 0.3),
         (140, 200, 58, 9.6, '#2b2e38', 0.3), (200, 290, 92, 9.5, '#272a35', 0.3)]
for i, (z0, z1, h, w, col, lit) in enumerate(left):                   # the nearest block: shutters and vending machines
    c.building(-1, z0, z1, h, wall=w, colour=col, lit=lit, shops=(0.2, 0.35, 0.15, 0.3) if i == 0 else (0.45, 0.35, 0.2, 0.0))
for z0, z1, h, w, col, lit in right:
    c.building(+1, z0, z1, h, wall=w, colour=col, lit=lit)
c.stage('canyon')

# ---- the wet street
c.street(crossing=(12.5, 4.0), puddles=0.55)
for X, Z in [(2.8, 11.5), (-3.6, 23.0), (4.4, 37.0)]:
    c.grate(X, Z)
c.puddle(-2.6, 4.6, 2.2, 1.6)                                           # mirrors the near signs
c.puddle(2.4, 5.2, 1.2, 1.1)
c.puddle(-0.6, 19.5, 2.0, 2.5)
c.stage('street')

# ---- blade signs (neon tubes and lightboxes), near to far
c.blade_sign(-1, 14, 2.9, 8.3, '夜市', MAGENTA, reach=2.6, border=CYAN, latin='NIGHT MARKET')
c.blade_sign(-1, 23, 3.3, 10.4, '拉麺', '#fff1e2', reach=2.0, kind='box', latin='RAMEN', text_colour=RED, level=0.8)
c.blade_sign(-1, 32, 4.2, 12.2, '旅館', CYAN, reach=2.3, latin='HOTEL', flicker=[1])   # caught mid-flicker
c.blade_sign(-1, 45, 3.6, 8.6, '酒', MAGENTA, reach=1.8, border=AMBER)
c.blade_sign(-1, 60, 4.5, 14.5, '質屋', AMBER, reach=2.2, dead=[0])        # a dead tube
c.blade_sign(-1, 80, 4.0, 12.0, '時計', MAGENTA, reach=2.0, kind='box', text_colour='#1a0610', level=0.8)
c.blade_sign(-1, 110, 5.0, 16.0, '薬', CYAN, reach=2.0)
c.blade_sign(+1, 17, 3.0, 9.8, '雨宿', CYAN, reach=2.6, border=MAGENTA, latin='BAR', dead=[1])
c.blade_sign(+1, 27, 3.5, 11.6, '喫茶', AMBER, reach=2.1, kind='box', latin='COFFEE', text_colour='#2a1406', level=0.75)
c.blade_sign(+1, 39, 4.0, 13.0, '電器', CYAN, reach=2.2, border=AMBER)
c.blade_sign(+1, 54, 3.8, 10.0, '麻雀', MAGENTA, reach=1.9, flicker=[0])
c.blade_sign(+1, 72, 4.5, 15.0, '書店', '#eaf6ff', reach=2.0, kind='box', text_colour='#1478ff', level=0.8)
c.blade_sign(+1, 100, 5.0, 17.0, '湯', MAGENTA, reach=2.0)
c.sign(19.5, 4.2, 7.4, 3.0, 3.9, 'NOODLES', MAGENTA, vertical=False, box=0.2)
c.sign(15.5, -8.9, -8.2, 0.25, 1.95, '営業中', '#fff4e6', kind='box', text_colour='#e0303a', level=0.7, box=0.25)   # a standing sidewalk sign
c.stage('neon')

# ---- the gate over the street and the hologram glowing beyond it
c.walkway(50, 8.2, thick=2.6, deep=4.0, windows=None)
gx, gy = c.project(0, 9.5, 49.9)
c.neon_text('不夜城', gx, gy - 4, 36, MAGENTA, 49.9, spacing=0.3)
c.neon_text('NEON DISTRICT', gx, gy + 24, 12, CYAN, 49.9, spacing=0.35, flicker=[5])
c.hologram(74, -8.3, 9.2, 9.0, 34.5, '海月', 'SEA MOON', level=2.2, jelly=(0.4, 0.3), sub_y=0.7)
c.stage('hologram')

# ---- cables and light trails
c.cables(22, z=(12, 40), Y=(11, 22))
c.light_trail([(-16, 20.5, 42), (-6, 22.8, 45.5), (4, 23.2, 49), (16, 21.0, 53)], '#ffe6c0', level=2.0, pair=1.2, strobe=7,
              fade=(0.12, 0.25))                                          # a car crossing the street overhead
c.light_trail([(16, 25.5, 66), (5, 27.2, 62), (-5, 26.8, 59.5), (-16, 25.0, 57)], RED, level=1.7, pair=1.4, fade=(0.12, 0.3))
c.stage('wires')

# ---- steam, mist and the lone figure
c.steam(2.8, 11.5, height=6.5, width=0.55, drift=1.8, density=1.5)
c.steam(-3.6, 23.0, height=7.0, width=0.8, drift=2.2, density=1.3)
c.steam(4.4, 37.0, height=8.0, width=1.0, drift=2.5, density=1.1)
c.mist()
c.figure(-1.0, 19.5)
c.stage('figure')

# ---- rain, and one torn scanline in the finished frame
c.rain()
c.glitch(236, 7, 9, 2)
c.save(out, stages_dir=stages)
print('saved', out, f'{time.time() - t0:.1f}s')
