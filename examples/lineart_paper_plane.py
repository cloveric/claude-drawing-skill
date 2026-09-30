"""Example (continuous line art): 从这扇窗到那扇窗 / From Window to Window — one unbroken gold line on a night-blue
card. It comes in along a hill, draws a round tree and a small house, and leaves through the house's window as
the flight path of a paper plane: a long climb, one loop-the-loop at the top, a glide down, then the plane
itself, which flies straight on through the wall into the window of a second house across the gap. That window
is the only colour in the picture: it lights up once the line has finished the second house and run out along
the far hill. The flight path is drawn with a lighter hand than the houses. Letter-spaced title underneath.
No image model.
python3 lineart_paper_plane.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from lineart import LineArt, AMBER, GOLD

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'lineart_paper_plane.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

la = LineArt(1920, 1080, seed=11)
la.backdrop('night')
S, P, back = LineArt.smooth, LineArt.poly, LineArt.retrace

# ---- left hill: fade in, a round tree, house A
ground_in = S([(160, 718), (190, 716), (218, 713), (236, 712)])
crown = LineArt.scallop(247, 606, 42, 104, 436, bumps=7, depth=0.13)
tree = np.vstack([S([(236, 712), (237, 686), tuple(crown[0])]), crown, S([tuple(crown[-1]), (257, 686), (260, 712)])])
lane = S([(260, 712), (284, 711), (310, 709), (330, 708)])
AX0, AX1, AY0, AY1, AAP = 330, 454, 616, 708, 540              # walls, eaves height, ground, apex
WA = (386, 428, 626, 668)                                       # window A: x0, x1, y0, y1 (near the right wall)
YA = 647                                                        # where the flight leaves through the wall
house_a = np.vstack([
    P([(AX0, AY1), (AX0, AY0), (AX0 - 14, AY0), ((AX0 + AX1) / 2, AAP), (AX1 + 14, AY0), (AX1, AY0), (AX1, AY1)], r=4, sharp=(3,)),
    back(S([(AX1, AY1), (478, 710), (506, 715), (528, 721)])),                     # hill shoulder, and back
    P([(AX1, AY1), (AX1, YA), (WA[1], YA)], r=0),                                   # back up the wall, in to the window
    P([(WA[1], YA), (WA[1], WA[3]), (WA[0], WA[3]), (WA[0], WA[2]), (WA[1], WA[2]), (WA[1], YA)], r=2),
    P([(WA[1], YA), (AX1, YA)], r=0)])                                              # out through the wall
# ---- the paper plane, seen three-quarter from above (local frame: nose at 0,0 pointing +x): near wing N-T-K,
# far wing N-K-B (foreshortened), crease N-K. The pen enters at the rear notch K and leaves at the nose.
N, T, K, B = (0, 0), (-150, -62), (-116, 2), (-130, 42)
PLANE_AT, PLANE_ANG, PLANE_SIZE = (1390, 622), 16, 0.86
place = lambda pts: LineArt.place(pts, PLANE_AT, PLANE_ANG, PLANE_SIZE)
KW = tuple(place([K])[0])
plane = place(P([K, B, N, K, T, N], r=2 / PLANE_SIZE, sharp=(1, 2, 3, 4)))
# ---- the flight: out through the wall and straight up into a long climb, one loop-the-loop at the top, then the
# glide down into the plane's tail. The hand eases off along it (see `pressure` below), so the flight path is
# lighter than the things it connects and never reads as a hill.
flight = S([(AX1, YA), (486, 641), (524, 624), (580, 588), (648, 530), (724, 466), (804, 412), (884, 374),
            (962, 350), (1036, 344), (1104, 360), (1156, 404), (1196, 468), (1232, 532), (1262, 574), KW])
flight = LineArt.curl(flight, LineArt.locate(flight, (1000, 346)), 62, span=96, aspect=1.2)
# ---- house B: the line flies on from the nose, in through the left wall to the window, then builds the house
BX0, BX1, BY0, BY1, BAP = 1424, 1600, 610, 709, 520
WB = (1450, 1506, 616, 668)
YB = 640
slope = (BY0 - BAP) / (BX1 + 14 - (BX0 + BX1) / 2)
cy = lambda x: BAP + (x - (BX0 + BX1) / 2) * slope
NX, NY = plane[-1]
JB = (BX0, NY + (YB - NY) * (BX0 - NX) / (WB[0] - NX))              # where the arrival crosses the left wall
arrive = P([(NX, NY), (WB[0], YB)], r=0)
house_b = np.vstack([
    P([(WB[0], YB), (WB[0], WB[2]), (WB[1], WB[2]), (WB[1], WB[3]), (WB[0], WB[3]), (WB[0], YB)], r=2),
    P([(WB[0], YB), JB, (BX0, BY1)], r=0),
    back(S([(BX0, BY1), (1400, 711), (1374, 716), (1352, 721)])),                  # hill shoulder, and back
    P([(BX0, BY1), (BX0, BY0), (BX0 - 14, BY0), ((BX0 + BX1) / 2, BAP), (1546, cy(1546)), (1546, 512), (1570, 512),
       (1570, cy(1570)), (BX1 + 14, BY0), (BX1, BY0), (BX1, BY1)], r=4, sharp=(3,))])
bush = LineArt.scallop(1672, 708, 22, 180, 360, bumps=3, depth=0.2, squash=0.9)
ground_out = np.vstack([S([(BX1, BY1), (1628, 710), tuple(bush[0])]), bush,
                        S([tuple(bush[-1]), (1712, 712), (1740, 715), (1772, 718), (1800, 721)])])

path, marks = la.chain([('ground', ground_in), ('tree', tree), ('lane', lane), ('house_a', house_a),
                        ('flight', flight), ('plane', plane), ('arrive', arrive), ('house_b', house_b), ('end', ground_out)])
DY = -56                                                        # lift the whole drawing above the title
path = path + np.float32([0, DY])
la.line(path, width=3.3, pressure=[(marks['house_a'], marks['flight'], 0.62), (marks['plane'], marks['arrive'], 0.7)])

window_b = 2 * ((WB[1] - WB[0]) + (WB[3] - WB[2]))                   # perimeter of the far window
steps = [('tree', marks['tree']), ('house_a', marks['house_a']), ('climb', marks['house_a'] + 400),
         ('loop', marks['house_a'] + 1000), ('glide', marks['flight']), ('plane', marks['plane']),
         ('window', marks['arrive'] + window_b), ('end', marks['end'])]
for name, s in steps:
    la.draw_to(s); la.stage(name)

# ---- the one accent: the far window lights up (four panes, glazing bars left dark)
wx0, wx1, wy0, wy1 = WB[0] + 5, WB[1] - 5, WB[2] + 5 + DY, WB[3] - 5 + DY
xm, ym = (wx0 + wx1) / 2, (wy0 + wy1) / 2
win = la.rect(wx0, wy0, wx1, wy1, r=1.5) * (1 - la.rect(xm - 1.6, wy0, xm + 1.6, wy1)) * (1 - la.rect(wx0, ym - 1.6, wx1, ym + 1.6))
la.accent(win, AMBER)
la.stage('light')

# ---- title
la.text('FROM WINDOW TO WINDOW', 960, 832, 38, GOLD, 'display', spacing=10)
cap = '一架纸飞机，一笔没有断开'
la.text(cap, 960, 886, 24, '#b9ab8a', 'display', spacing=7)
wc = la.text_width(cap, 24, 'display', spacing=7) / 2
la.hairline(960 - wc - 86, 878, 960 - wc - 26, 878, colour='#8d7f63')
la.hairline(960 + wc + 26, 878, 960 + wc + 86, 878, colour='#8d7f63')
la.save(out, stages)
print('saved', out)
