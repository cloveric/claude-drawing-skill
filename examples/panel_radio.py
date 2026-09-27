"""Example (vintage industrial panel): Aurora 64 / 六十年代收音机 — the front of a 1960s tabletop radio:
teak cabinet, woven grille cloth with lurex threads and a chrome script badge, a backlit FM/AM dial behind
glass with a red needle, piano-key band buttons, a green magic-eye tuning tube, a toggle switch, a jewel
lamp, three machined knobs with printed scales, slotted screws. No image model.
python3 panel_radio.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from panel import Panel
from core import blur

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'panel_radio.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

p = Panel(1920, 1080, seed=64)
W, H = p.W, p.H
INK, RED, CREAM = '#2b2a27', '#c8452e', '#f3e5c2'

# ---- wall, sideboard, teak cabinet
p.background('#a9bcb0', 'painted')
p.img *= (0.9 + 0.16 * np.exp(-(((p.XX - 960) / 900) ** 2 + ((p.YY - 380) / 600) ** 2)))[..., None]   # soft room light
top = p.rrect(-20, 968, W + 20, H + 40, 0)
p.surface(top, 'wood', '#c79d6c', height=0, dark='#8d6440', light='#e0bd8c', ring_scale=0.05)
p.paint(p.rrect(-20, 966, W + 20, 972, 0), '#f0d9b4', 0.5)
for fx in (230, 1690):
    p.surface(p.rrect(fx - 50, 930, fx + 50, 982, 6), 'painted', '#2a211b', height=4, shadow=0.5)
cab = p.rrect(80, 92, 1840, 956, 46)
p.drop_shadow(cab, dist=26, soft=26, strength=0.5)
p.surface(cab, 'wood', '#8a5230', height=16, soft=14)
p.recess(p.rrect(128, 140, 1792, 908, 24), 'painted', '#221c17', depth=10)
p.stage('cabinet')

# ---- speaker: brass trim, recessed grille cloth, chrome script badge
p.surface(p.rrect(150, 162, 908, 886, 18), 'brushed', '#c9a55c', height=6, soft=3, shadow=0.4)
cloth = p.rrect(164, 176, 894, 872, 12)
p.recess(cloth, 'fabric', '#d6c6a3', depth=6, pitch=4.0, lurex='#c89e45', lurex_every=6)
cone = blur(p.circle(529, 470, 250), 40) - 0.55 * blur(p.circle(529, 470, 70), 20)   # the speaker behind the thin cloth
p.img *= (1 - 0.1 * cone * cloth)[..., None]
p.badge('Aurora', 700, 790, 96, 'script', '#e2dfd6')
p.text('SIXTY-FOUR', 704, 846, 19, '#5a4630', 'sans_bold', spacing=7)
p.stage('grille')

# ---- control panel: brushed aluminium plate, backlit dial behind glass
p.surface(p.rrect(930, 162, 1770, 886, 18), 'brushed', '#cfcfca', height=6, soft=3, shadow=0.4, band=0.35)
DX0, DY0, DX1, DY1 = 972, 202, 1728, 474
p.recess(p.rrect(DX0, DY0, DX1, DY1, 12), 'painted', '#1d1a17', depth=8)
face = p.rrect(DX0 + 14, DY0 + 14, DX1 - 14, DY1 - 14, 6)
p.surface(face, 'painted', CREAM, height=0)
p.img *= (1 + 0.12 * face * np.exp(-(((p.XX - 1350) / 420) ** 2 + ((p.YY - 330) / 160) ** 2)) - 0.1 * face * (p.YY < DY0 + 60) * (1 - (p.YY - DY0 - 14) / 46))[..., None]
X0, X1 = 1060, 1650
p.text('FM', 1018, 282, 26, RED, 'sans_bold')
p.scale_linear(X0, X1, 300, 41, major=4, length=20, colour=INK, labels=[str(v) for v in range(88, 110, 2)], size=19, label_gap=12)
p.text('MHz', 1686, 282, 17, INK, 'sans_bold')
p.paint(p.line_mask([(X0, 301), (X1, 301)], 1.6), INK)
p.text('AM', 1018, 372, 26, RED, 'sans_bold')
p.scale_linear(X0, X1, 356, 36, major=5, length=16, colour=INK, labels=['530', '600', '700', '800', '1000', '1200', '1400', '1600'], size=17, up=False, label_gap=12)
p.paint(p.line_mask([(X0, 355), (X1, 355)], 1.6), INK)
p.text('kHz', 1690, 386, 17, INK, 'sans_bold')
for i, city in enumerate(['LONDON', 'PARIS', 'ROMA', 'WIEN', 'OSLO', 'PRAHA', 'LISBOA']):
    p.text(city, X0 + 30 + i * (X1 - X0 - 60) / 6, 426, 15, '#7a6f5e', 'sans_bold', spacing=2.5)
NX = 1402
p.glow(NX, 330, 26, '#ff6a3d', 0.25)
p.paint(p.line_mask([(NX, DY0 + 22), (NX, DY1 - 22)], 3.2), RED)
p.glass(p.rrect(DX0 + 8, DY0 + 8, DX1 - 8, DY1 - 8, 8), streak=0.1)
p.stage('dial')

# ---- piano keys, magic eye, toggle switch, jewel lamp
labels = ['OFF', 'PH', 'AM', 'FM', 'SW']
for i, lab in enumerate(labels):
    x0 = 978 + i * 86
    p.button(x0, 516, x0 + 78, 612, '#efe9dc', pressed=(lab == 'FM'), label=lab, size=19)
p.magic_eye(1500, 560, 30, tuned=0.82)
p.text('TUNING', 1500, 628, 15, INK, 'sans_bold', spacing=3)
p.toggle(1612, 572, up=True, length=54)
p.text('STEREO', 1612, 500, 15, INK, 'sans_bold', spacing=3)
p.text('MONO', 1612, 628, 15, INK, 'sans_bold', spacing=3)
p.lamp(1706, 560, 13, '#ffae3b', on=True)
p.text('ON', 1706, 628, 15, INK, 'sans_bold', spacing=3)
p.stage('controls')

# ---- three knobs with printed scales, legends, screws
for (kx, lab, ang, labs) in [(1072, 'VOLUME', 38, ['0', '5', '10']), (1350, 'TONE', -30, ['BASS', 'TREBLE']), (1628, 'TUNING', 64, None)]:
    ky = 752
    p.scale_arc(kx, ky, 86, 98, -135, 135, 21 if labs != ['BASS', 'TREBLE'] else 11, 5, INK, labels=labs, label_r=118, size=16, width=1.8)
    p.knob(kx, ky, 58, angle=ang, face='#d6d6d1', skirt='#24221e', indicator=RED, skirt_w=13)
    p.text(lab, kx, 862, 17, INK, 'sans_bold', spacing=5)
for (sx, sy) in [(952, 184), (1748, 184), (952, 864), (1748, 864)]:
    p.screw(sx, sy, 8)

p.save(out, stages_dir=stages)
print('saved', out)
