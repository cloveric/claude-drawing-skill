"""Example (editorial illustration, risograph feel): Growing Ideas / 灵感生长 — a figure waters a plant
that grows into a light bulb. Limited spot palette, overprinting inks, halftone shading,
mis-registration, wobbly hand-drawn line. Pure code, no image model.
python3 editorial_ideas.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from editorial import Editorial
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'editorial_ideas.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

YEL, COR, TEA, PNK, NAV = '#ffc857', '#ff6b57', '#1b9aaa', '#f7a8b8', '#26335c'
e = Editorial(1920, 1080, seed=2027)
rng = e.rng

# ---- big simple backdrop shapes (overprinting where they meet)
BX, BY = 1360, 360
e.fill(e.circle(BX, BY - 20, 330), YEL)
e.halftone(e.circle(BX, BY - 20, 330) * np.clip((e.XX - BX + (e.YY - BY)) / 420, 0, 1), COR, cell=12, angle=0.6, amount=0.55)
arch = np.maximum(e.rrect(170, 250, 640, 1000, 30) * (e.YY > 480), e.circle(405, 480, 235))
e.fill(arch, PNK)
e.fill(e.poly([(0, 905), (1920, 890), (1920, 1080), (0, 1080)]), TEA)
e.halftone(e.poly([(0, 905), (1920, 890), (1920, 1080), (0, 1080)]) * np.clip((e.YY - 900) / 180, 0, 1), NAV, cell=10, angle=0.3, amount=0.5)
e.stage('shapes')

# ---- the plant that grows into a light bulb
PX = 1360
pot = [(PX - 110, 760), (PX + 110, 760), (PX + 80, 920), (PX - 80, 920)]
e.fill(e.poly(pot), COR)
e.halftone(e.poly(pot) * np.clip((e.XX - PX) / 110, 0, 1), NAV, cell=9, angle=0.8, amount=0.55)
e.fill(e.rrect(PX - 125, 738, PX + 125, 778, 8), COR)
e.line(pot, NAV, 4, closed=True); e.line([(PX - 125, 740), (PX + 125, 740), (PX + 125, 778), (PX - 125, 778), (PX - 125, 740)], NAV, 4)
stem = spline([(PX, 740), (PX - 30, 640), (PX + 20, 560), (PX, 470)], 16)
e.line(stem, NAV, 6)
for (t, side, L) in [(0.25, -1, 150), (0.45, 1, 170), (0.65, -1, 130)]:
    q = stem[int(t * (len(stem) - 1))]
    tip = (q[0] + side * L, q[1] - L * 0.45)
    leaf = spline([tuple(q), (q[0] + side * L * 0.45, q[1] - L * 0.62), tip, (q[0] + side * L * 0.55, q[1] - L * 0.05), tuple(q)], 10)
    e.fill(e.poly(leaf), TEA)
    e.line(leaf, NAV, 3.5, closed=True)
    e.line([tuple(q), (q[0] + side * L * 0.75, q[1] - L * 0.35)], NAV, 2.5)
# bulb: glass left as paper, glowing rays, coral filament, navy screw base
glass = spline([(PX - 40, 470), (PX - 60, 420), (PX - 120, 350), (PX - 110, 250), (PX, 190), (PX + 110, 250), (PX + 120, 350), (PX + 60, 420), (PX + 40, 470)], 12)
e.fill(e.poly(glass), '#fff6dd', density=0.98)
e.halftone(e.poly(glass) * np.clip((e.XX - PX + 60) / 180, 0, 1), YEL, cell=8, angle=0.4, amount=0.7)
e.line(glass, NAV, 5)
e.line(spline([(PX - 34, 440), (PX - 24, 360), (PX - 8, 330), (PX + 8, 360), (PX + 24, 330), (PX + 34, 440)], 10), COR, 4)
for k in range(3):
    e.fill(e.rrect(PX - 44 + k * 3, 470 + k * 16, PX + 44 - k * 3, 482 + k * 16, 5), NAV)
for a in np.linspace(-2.9, -0.25, 7):
    r0, r1 = 160, 215
    e.line([(PX + np.cos(a) * r0, 320 + np.sin(a) * r0), (PX + np.cos(a) * r1, 320 + np.sin(a) * r1)], NAV, 5, wobble=0.5)
e.stage('plant')

# ---- the gardener: stylised figure with a watering can
HX, HY = 520, 640                                       # hips
for (fx, fy) in [(470, 890), (600, 895)]:               # legs + shoes
    e.line(spline([(HX + (fx - HX) * 0.2, HY), ((HX + fx) / 2, (HY + fy) / 2 + 10), (fx, fy)], 10), NAV, 34, wobble=0.6)
    e.fill(e.ellipse(fx + 22, fy + 8, 40, 16), COR)
torso = spline([(HX - 70, HY), (HX - 80, 540), (HX - 40, 470), (HX + 50, 462), (HX + 90, 520), (HX + 80, HY), (HX - 70, HY)], 12)
e.fill(e.poly(torso), COR)
e.halftone(e.poly(torso) * np.clip((HX - e.XX) / 90, 0, 1), NAV, cell=8, angle=0.8, amount=0.5)
e.line(torso, NAV, 4)
e.fill(e.rrect(HX - 14, 420, HX + 16, 470, 10), '#f2c4a8')                    # neck
e.fill(e.circle(HX + 10, 385, 52), '#f2c4a8')                                   # head
hair = spline([(HX - 44, 420), (HX - 50, 360), (HX - 10, 322), (HX + 40, 326), (HX + 62, 360), (HX + 40, 352), (HX - 10, 360), (HX - 30, 420)], 10)
e.fill(e.poly(hair), NAV)
e.line([(HX + 36, 392), (HX + 46, 396)], NAV, 3, wobble=0.2)                     # closed eye
arm = spline([(HX + 60, 480), (HX + 150, 540), (HX + 250, 560), (HX + 300, 548)], 12)
e.line(arm, COR, 30, wobble=0.5); e.line(arm, NAV, 3, wobble=0.8)
e.fill(e.circle(HX + 305, 548, 20), '#f2c4a8')                                  # hand
CX, CY = HX + 380, 560                                                           # watering can
e.fill(e.rrect(CX - 70, CY - 55, CX + 70, CY + 55, 18), TEA)
e.halftone(e.rrect(CX - 70, CY - 55, CX + 70, CY + 55, 18) * np.clip((e.YY - CY) / 60, 0, 1), NAV, cell=8, angle=0.5, amount=0.55)
e.line([(CX - 70, CY - 37), (CX - 70, CY + 55), (CX + 70, CY + 55), (CX + 70, CY - 37), (CX - 52, CY - 55), (CX - 70, CY - 37)], NAV, 4)
e.line(spline([(CX - 60, CY - 50), (CX - 10, CY - 110), (CX + 50, CY - 55)], 10), NAV, 6)
spout = [(CX + 70, CY + 10), (CX + 190, CY - 40), (CX + 200, CY - 26), (CX + 70, CY + 34)]
e.fill(e.poly(spout), TEA); e.line(spout, NAV, 3.5, closed=True)
for k in range(9):                                                               # water drops arcing to the pot
    t = k / 8
    x = CX + 205 + t * 240; y = CY - 30 + t * t * 170 - 40 * np.sin(np.pi * t)
    e.fill(e.ellipse(x, y, 7, 11), TEA)
e.stage('figure')

# ---- small marks: dotted path, sparkles, floating dots
e.dashes([(700, 250), (900, 180), (1080, 210)], NAV, 3, dash=16, gap=12)
e.stars([(1640, 170, 16), (1060, 150, 12), (1710, 560, 12), (250, 170, 14)])
for (x, y, r, c) in [(1760, 360, 18, COR), (160, 780, 14, YEL), (980, 820, 10, PNK), (1620, 760, 12, YEL)]:
    e.fill(e.circle(x, y, r), c)

e.save(out, stages_dir=stages)
print('saved', out)
