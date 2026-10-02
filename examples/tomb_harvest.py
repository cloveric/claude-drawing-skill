"""Example (Egyptian tomb painting): Harvest on the Nile / 尼罗河丰收 -- a wall in a Theban tomb chapel, three
registers read as one story: ploughing and sowing after the flood, reaping the emmer, and the scribe counting the
sacks of grain (twelve sacks in the stack, written ∩|| above it).  An estate overseer at hierarchical scale stands
on the main ground line and watches, under columns of (pseudo-)hieroglyphs.  Kheker frieze, block border, striped
register bands, the river with fish and lotus at the foot of the wall.  Painted the way it was done: plaster,
red squaring grid, red sketch, ground wash, one pigment at a time, black outlines, the text -- then 3,300 years.
No image model.
python3 tomb_harvest.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from tomb import TombPainting

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'tomb_harvest.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

W, H = 1920, 1080
tp = TombPainting(W, H, seed=11)
tp.wall()
tp.stage('plaster')

# ---------------------------------------------------------------- layout
BL, BR = 22, W - 22                     # block border inside edges
TOP = 105                               # top of the scene area (under the kheker frieze and its band)
REG = [(TOP, 375), (387, 657), (669, 940)]   # registers: (top, ground line)
XR = 432                                # registers start right of the overseer
HF = 212                                # worker height (sole to top of wig)
U = HF / 19.6
OV_H, OV_X = 548, 178                   # overseer height and hip x
RIV = (952, 1014)

# ---- red cords first: register guides and squaring grids (one canon unit per cell)
for (t, b) in REG:
    tp.grid((XR, t + 4, BR, b), cell=U, base=b)
tp.grid((BL + 8, 395, XR - 10, REG[2][1]), cell=OV_H / 19.6, base=REG[2][1])
for y in (TOP, RIV[0], RIV[1]) + tuple(b for _, b in REG):
    tp.guide((BL, y), (BR, y))
tp.guide((XR - 6, TOP), (XR - 6, REG[2][1]))
tp.stage('grid')

# ---------------------------------------------------------------- declare the frame
tp.block_border(0, 0, W, BL)
tp.block_border(0, H - BL, W, H)
tp.block_border(0, BL, BL, H - BL)
tp.block_border(BR, BL, W, H - BL)
tp.kheker(BL, BR, BL + 2, 86)
tp.band(BL, BR, 86, [('rule', 2), ('blue', 8), ('rule', 2), ('yellow', 5), ('rule', 2)])
for (t, b) in REG[:2]:
    tp.band(XR, BR, b, [('rule', 2), ('red', 7), ('rule', 2)])
tp.band(BL, BR, REG[2][1], [('rule', 2), ('red', 8), ('rule', 2)])
tp.river(BL, RIV[0], BR, RIV[1], fish=6, lotus=9, seed=4)
tp.band(BL, BR, RIV[1], [('rule', 2), ('yellow', 6), ('rule', 2), ('red', 9), ('rule', 2), ('black', 13)])
tp.part(None, None, paths=[np.array([[XR - 6, TOP], [XR - 6, REG[2][1]]])], width=2.2, sketch=False)

# ---------------------------------------------------------------- the overseer and his titles
ov = tp.figure(OV_X, REG[2][1], OV_H, 'staff', facing=1, wig='long', dress='long')
tp.staff(ov['hand_f'], OV_H * 0.98, facing=1, z=ov['z_hand_f'] - 0.01, lw=ov['lw'])
cl = ov['hand_b']                                            # a folded linen cloth hangs from the other fist
cloth = np.array([[cl[0] - 7, cl[1] - 4], [cl[0] + 7, cl[1] - 4], [cl[0] + 9, cl[1] + 62], [cl[0] + 6, cl[1] + 72],
                  [cl[0] - 4, cl[1] + 73], [cl[0] - 8, cl[1] + 64]], np.float32)
tp.part(cloth, 'white', z=ov['z_hand_b'] - 0.01, width=ov['lw'] * 0.8)
tp.part(None, None, paths=[np.array([[cl[0] - 1, cl[1] + 8], [cl[0] + 1, cl[1] + 70]]),
                           np.array([[cl[0] + 4, cl[1] + 8], [cl[0] + 6, cl[1] + 68]])], ink='#b9a58c', width=1.6,
        z=ov['z_hand_b'] - 0.005)
cols = np.linspace(BL + 22, XR - 22, 6)
for i in range(5):
    tp.column(cols[i], TOP + 10, cols[i + 1], 372, facing=1, n=20, seed=100 + i, rules=(i == 0))
    tp.part(None, None, paths=[np.array([[cols[i + 1], TOP + 10], [cols[i + 1], 372]])], width=1.6, layer='text')

# ---------------------------------------------------------------- register 1: ploughing and sowing after the flood
t1, g1 = REG[0]
soil = np.array([[XR + 4, g1], [1460, g1], [1460, g1 - 7], [XR + 4, g1 - 5]], np.float32)
tp.part(soil, 'black', outline=False, rag=0.8)
far = tp.ox(1010, g1, 252, facing=-1, colour='brown', patches=None, seed=3)
pole_z = tp._z; tp._z += 1
near = tp.ox(1040, g1, 252, facing=-1, colour='white', patches='black', seed=8)
pm = tp.figure(1225, g1, HF, 'plough', facing=-1, wig='cap', collar=False)
share = np.array([1092, g1 - 3], np.float32)
heel = np.array([1112, g1 - 16], np.float32)
tp.rod(heel, pm['hand_f'] + (0, -4), 6, 'ochre', z=pm['z_hand_f'] - 0.01)
tp.rod(heel + (6, 0), pm['hand_b'] + (0, -4), 6, 'ochre', z=pm['z0'] - 0.5)
tp.part(np.array([share, heel + (-4, -6), heel + (12, -2), heel + (8, 10)]), 'brown', z=pm['z0'] - 0.4)
tp.rod(heel + (-2, -4), near['poll'] + (14, 6), 7, 'ochre', z=pole_z)
yoke0, yoke1 = far['poll'] + (-14, -2), near['poll'] + (16, 4)
tp.rod(yoke0, yoke1, 9, 'ochre', z=near['z'] + 0.5)
for p in (far['poll'], near['poll']):
    tp.part(None, None, paths=[np.array([p + (-6, -10), p + (6, 8)]), np.array([p + (-1, -11), p + (10, 6)])], width=2.2,
            z=near['z'] + 0.6, ink='#6b5a3a')
sw = tp.figure(560, g1, HF, 'sow', facing=-1, collar=False)
tp.basket(sw['wrist_b'][0] + 4, sw['wrist_b'][1] + 6, 46, 30, z=sw['z_hand_b'] - 0.02, full='yellow')
tp.grain_stream(sw['hand_f'] + (-14, 6), sw['hand_f'] + (-60, 96), n=34, spread=7, colour='brown')
for x in (1395, 1545):
    hm = tp.figure(x, g1, HF, 'hoe', facing=-1, wig='cap' if x > 1400 else 'short', collar=False)
    tp.hoe(hm)
# the canal at the end of the field: a pool seen from above, with lotus and papyrus
px0, px1 = 1640, BR - 22
tp.part(np.array([[px0, g1 - 108], [px1, g1 - 108], [px1, g1], [px0, g1]], np.float32), 'blue', rag=0.4)
rows = []
for k, yy in enumerate(np.arange(g1 - 92, g1 - 8, 18.0)):
    xs = np.arange(px0 + 8 + (k % 2) * 7, px1 - 6, 14.0)
    rows.append(np.stack([np.repeat(xs, 2)[:-1] + np.tile([0, 7], len(xs))[:-1], np.tile([yy - 4, yy + 4], len(xs))[:-1]], 1))
tp.part(None, None, paths=rows, width=1.4, sketch=False)
for i, x in enumerate(np.linspace(px0 + 30, px1 - 30, 4)):
    tp.papyrus_clump(x, g1 - 106, 112 - 14 * (i % 2), n=3, seed=60 + i)
for k, (cx, cy) in enumerate([(700, t1 + 8), (1300, t1 + 8)]):
    for j in range(4):
        tp.column(cx + j * 34, cy, cx + (j + 1) * 34, cy + 74, facing=-1, n=6, seed=200 + 10 * k + j, rules=False, lw=1.4)
    for j in range(5):
        tp.part(None, None, paths=[np.array([[cx + j * 34, cy], [cx + j * 34, cy + 74]])], width=1.4, layer='text')

# ---------------------------------------------------------------- register 2: reaping the emmer
t2, g2 = REG[1]
reapers = [650, 840, 1030]
grabs, stub = [], []
for x in reapers:
    grabs.append((x - 79 * U / 10.7 * 0 - 7.4 * U, g2 - 9.0 * U, (x - 7.4 * U - 34, x - 7.4 * U + 6)))
    stub.append((x - 7.4 * U + 10, x + 50))
tp.wheat(XR + 30, reapers[-1] + 60, g2, t2 + 62, every=8.5, stubble=stub, grab=grabs, seed=5)
for i, x in enumerate(reapers):
    rp = tp.figure(x, g2, HF, 'reap', facing=-1, wig='short' if i != 1 else 'cap', collar=False)
    tp.sickle(rp['hand_b'], 34, facing=-1, angle=-20, z=rp['z_hand_b'] - 0.01)
for x in (1110, 1150):
    tp.sheaf(x, g2, 46, 92)
gl = tp.figure(1265, g2, HF * 0.95, 'glean', facing=-1, sex='f', wig='woman', dress='dress')
tp.basket(1195, g2 - 30, 52, 30, z=gl['z0'] - 0.5, full='yellow')
tr = tp.tree(1470, g2, 250, 196, waterskin=(-62, 58))
cr = tp.figure(1700, g2, HF, 'carry', facing=1, collar=False)
bc = cr['S']((-3.0, 17.2))                                    # the basket rides on the back shoulder, behind the head
tp.basket(bc[0], bc[1], 72, 40, z=cr['z_hand_b'] - 0.05, full='yellow')
for k, (cx, cy) in enumerate([(560, t2 + 6), (1180, t2 + 8)]):
    for j in range(3):
        tp.column(cx + j * 34, cy, cx + (j + 1) * 34, cy + 72, facing=-1, n=6, seed=300 + 10 * k + j, rules=False)
    for j in range(4):
        tp.part(None, None, paths=[np.array([[cx + j * 34, cy], [cx + j * 34, cy + 72]])], width=1.4, layer='text')

# ---------------------------------------------------------------- register 3: the scribe counts the sacks
t3, g3 = REG[2]
sc = tp.figure(520, g3, HF, 'squat', facing=1, wig='short')
tp.papyrus(sc['hand_b'] + (-6, 4), sc['hand_f'] + (6, -4), 13, z=sc['z_hand_b'] - 0.05)
tp.part(None, None, paths=[np.array([sc['hand_b'], sc['hand_b'] + (14, -16)])], ink='#3a2a22', width=1.6,
        z=sc['z_hand_b'] + 0.5)
ear = sc['ear']
tp.part(None, None, paths=[np.array([ear + (8, -2), ear + (-24, 6)])], ink='#7b4a2c', width=2.0, z=sc['z_top'] + 0.5)
tp.palette(478, g3 - 7, 60, angle=0.0)
# the stack: twelve sacks (5 + 4 + 3)
sw_, sh_ = 40, 50
stack_x = 640
for row, n in enumerate((5, 4, 3)):
    for i in range(n):
        tp.sack(stack_x + (i + row * 0.5) * (sw_ + 2), g3 - row * (sh_ - 6), sw_, sh_)
tp.numerals(12, stack_x + 58, g3 - 3 * sh_ - 58, 46, facing=1)
po = tp.figure(930, g3, HF, 'carry', facing=-1, wig='cap', collar=False)
sb = po['S']((-0.4, 15.9))                                    # the sack lies across the back shoulder
tp.sack(sb[0], sb[1], 48, 72, lean=-1.2, z=po['z_hand_b'] - 0.05)
ho = tp.figure(1030, g3, HF, 'hold', facing=1, collar=False, wf=(5.6, 9.6), wb=(4.6, 9.3))
tp.sack(1098, g3, 50, 112, z=ho['z_hand_f'] - 0.5)
scp = tp.figure(1250, g3, HF, 'scoop', facing=-1, collar=False, wf=(7.2, 12.4), wb=(6.2, 10.9), lean=28)
mq = scp['hand_f']
tp.measure(mq[0] - 14, mq[1] + 16, 38, 40, z=scp['z_hand_f'] - 0.01, tilt=-0.8)
tp.grain_stream((mq[0] - 34, mq[1] + 2), (1100, g3 - 108), n=26, spread=2.5)
tp.heap(1450, g3, 250, 150)
wn = tp.figure(1680, g3, HF * 0.95, 'walk', facing=-1, sex='f', wig='woman', dress='dress', wf=(4.6, 16.4), wb=(2.6, 17.3),
               hf='fist', hb='fist', bf=-1, bb=-1, cross=True, collar=False)
tp.scoop(wn['hand_f'], 30, angle=30, facing=-1, z=wn['z_hand_f'] - 0.01)
tp.scoop(wn['hand_b'], 30, angle=55, facing=-1, z=wn['z_hand_b'] - 0.01)
tp.grain_stream(wn['hand_f'] + (-40, -40), wn['hand_f'] + (-60, 150), n=40, spread=9, chaff=14)
tp.heap(1800, g3, 120, 70)
for k, (cx, cy) in enumerate([(800, t3 + 6), (1300, t3 + 8)]):
    for j in range(3):
        tp.column(cx + j * 34, cy, cx + (j + 1) * 34, cy + 72, facing=-1 if k else 1, n=6, seed=400 + 10 * k + j, rules=False)
    for j in range(4):
        tp.part(None, None, paths=[np.array([[cx + j * 34, cy], [cx + j * 34, cy + 72]])], width=1.4, layer='text')

# ---------------------------------------------------------------- paint it, pot by pot
tp.sketch()
tp.stage('sketch')
tp.ground('#d9bf86')
tp.stage('ground')
tp.colour(['skin', 'skin_f', 'red', 'brown', 'ochre'])
tp.stage('reds')
tp.colour(['linen', 'white', 'yellow'])
tp.stage('whites')
tp.colour(['blue', 'lblue', 'green', 'lgreen', 'dkgreen'])
tp.stage('blues')
tp.colour()
tp.ink()
tp.stage('outlines')
tp.colour(layer='text')
tp.ink(layer='text')
tp.stage('text')
tp.age(losses=[(1902, 560, 40, 92), (250, 1052, 80, 26), (1250, 30, 48, 24), (18, 330, 24, 62), (1560, 620, 26, 18)],
       zones=[(176, 868, 34), (958, 296, 22), (1338, 512, 18), (742, 610, 16)], cracks=9, seed=2)
tp.save(out, stages_dir=stages)
print('saved', out)
