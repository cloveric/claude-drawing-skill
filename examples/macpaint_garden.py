"""Example (1-bit paint program / 1-bit 早期画图软件): 窗台花园 · Windowsill Garden — a picture being made in a
1984-style black-and-white paint program, interface and all.

On the canvas: a four-pane window with gingham curtains tied back (the right one is the left one copied and flipped);
outside, a sky in bands of patterns, a sun, clouds, hills and little houses. On the sill, a seed packet and three
terracotta pots tell forty days of a sunflower: a sprout (day 2), a leafy seedling (day 14) and the full flower
(day 40), labelled underneath with tags and arrows (day 0 -> 2 -> 14 -> 40). The watering can's spout is still over
the day-2 pot, a drop falling in; at the other end a black cat sits on the sill, watching a white butterfly that has
looped in from the flower. A calendar on the wall has the days crossed off.
Draw-on stages follow the tools: frame -> sky -> town -> room -> pots -> can -> cat (with a zoom window on the eye) ->
spray -> type menu -> final (marquee round the butterfly, document saved under its name).
Every pixel is black or white; tone is patterns only.
python3 macpaint_garden.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from macpaint import MacPaint

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'macpaint_garden.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

m = MacPaint(seed=7, title='untitled')
W, H = m.W, m.H                                          # 554 x 246 document pixels
m.use('pencil', 'black', 1)
m.cursor('arrow', 300, 120)
m.stage('blank')

# ---- 1. window frame, sill and rod with the rectangle tool --------------------------------------------------
WX0, WY0, WX1, WY1 = 92, 16, 412, 172                     # window opening (outer frame)
GX0, GY0, GX1, GY1 = WX0 + 7, WY0 + 7, WX1 - 7, WY1      # glass
MX, MY = (WX0 + WX1) // 2, 94                            # mullion / transom centres
SILL_T, SILL_F, SILL_B = 168, 175, 186                   # sill top surface, front face, bottom
m.rect(WX0, WY0, WX1, WY1 + 2, fill='white', line=1)
m.rect(GX0 - 1, GY0 - 1, GX1 + 1, GY1 + 1, fill='white', line=1)
m.use('rect', 'white', 1)
m.cursor('cross', GX1, GY0)
m.stage('frame')

# ---- 2. sky: bands of patterns, a sun with rays, clouds, two birds ---------------------------------------
glass = m.mask_rect(GX0, GY0, GX1, GY1)
m.bands(glass, ['mist', 'faint', 'white'], GY0, GY0 + 84, seed=3)
sx, sy = 140, 50
m.oval(sx, sy, 14, 14, fill='white', line=2)
for k in range(12):
    a = k * np.pi / 6 + 0.13
    r1 = 29 if k % 2 == 0 else 24
    m.line((sx + 18 * np.cos(a), sy + 18 * np.sin(a)), (sx + r1 * np.cos(a), sy + r1 * np.sin(a)), 2)


def cloud(cx, cy, s=1.0):
    blobs = [(-22, 4, 14, 9), (-8, -4, 15, 12), (10, -2, 14, 11), (24, 4, 12, 8), (0, 6, 26, 8)]
    mask = np.zeros((H, W), np.uint8)
    for dx, dy, rx, ry in blobs:
        mask |= m.mask_oval(cx + dx * s, cy + dy * s, rx * s, ry * s)
    mask &= glass
    m.paint(mask, 'white')
    m.paint(m.border(mask, 1) & (m.YY < GY1 - 1) & (m.XX > GX0) & (m.XX < GX1 - 1), 'black')
    return mask


c1 = cloud(214, 46, 1.0)
c2 = cloud(281, 34, 0.7)
c3 = cloud(388, 30, 0.55)
for bx, by in [(186, 70), (200, 64)]:
    m.pencil([(bx - 5, by - 2), (bx - 2, by), (bx, by + 1), (bx + 2, by), (bx + 5, by - 3)])
m.use('bucket', 'mist', 1)
m.cursor('bucket', 120, 30)
m.stage('sky')

# ---- 3. outside: hills with a few distant houses, a meadow -----------------------------------------------
HZ = 118                                                                             # horizon line
hill = m.mask_poly([(GX0, HZ + 6), (130, HZ - 4), (170, HZ - 10), (215, HZ - 2), (250, HZ - 6), (300, HZ - 16),
                    (350, HZ - 8), (390, HZ - 12), (GX1, HZ - 6), (GX1, GY1), (GX0, GY1)], smooth=True) & glass
m.paint(hill, 'light')
m.paint(m.border(hill, 1) & (m.YY < HZ + 14) & (m.XX > GX0) & (m.XX < GX1 - 1), 'black')
meadow = m.mask_poly([(GX0, HZ + 18), (200, HZ + 12), (300, HZ + 16), (GX1, HZ + 10), (GX1, GY1), (GX0, GY1)], smooth=True) & glass
m.paint(meadow, 'dots')
m.paint(m.border(meadow, 1) & (m.YY < HZ + 24) & (m.XX > GX0) & (m.XX < GX1 - 1), 'black')


def house(x, y, w, h, roof_h, chimney=None):
    body = m.mask_rect(x, y, x + w, y + h) & glass
    m.paint(body, 'white'); m.paint(m.border(body, 1), 'black')
    rf = m.mask_poly([(x - 3, y + 1), (x + w // 2, y - roof_h), (x + w + 3, y + 1)]) & glass
    m.paint(rf, 'shingles'); m.paint(m.border(rf, 1), 'black')
    if chimney:
        cx = x + int(w * chimney)
        m.rect(cx, y - roof_h + 1, cx + 4, y - roof_h + 8, fill='black', line=1)
        m.spray([(cx + 2, y - roof_h - 2), (cx + 6, y - roof_h - 10), (cx + 1, y - roof_h - 18), (cx + 8, y - roof_h - 26)],
                radius=3, density=0.3, seed=11)
    for wx in range(x + 4, x + w - 5, 9):
        m.rect(wx, y + 4, wx + 4, y + 9, fill='black', line=0)


house(118, HZ - 8, 22, 14, 10, chimney=0.7)
house(150, HZ - 10, 18, 12, 8)
house(352, HZ - 16, 26, 14, 11, chimney=0.25)
m.use('ffree', 'shingles', 1)
m.cursor('cross', 210, 128)
m.stage('town')

# ---- 4. the room: mullions, wallpaper, gingham curtains on a rod, the sill ------------------------------------
m.rect(MX - 3, GY0, MX + 3, GY1, fill='white', line=1)
m.rect(GX0, MY - 3, GX1, MY + 3, fill='white', line=1)
for gx, gy in [(GX0 + 10, GY0 + 22), (MX + 10, MY + 12)]:                 # glass glints
    m.line((gx, gy), (gx + 9, gy - 9), 1); m.line((gx + 4, gy + 1), (gx + 11, gy - 6), 1)
wall = 1 - m.mask_rect(WX0, WY0, WX1, WY1 + 2)
m.paint(wall, 'sprigs')
m.rect(WX0, WY0, WX1, WY1 + 2, fill=None, line=1)


CURTAIN = 'gingham'


def curtain(xo=64, xi=126, tie_y=108):
    """the left curtain: gingham freeform hanging from the rod (outer edge xo, inner edge xi), folds, a tie-back"""
    pts = [(xo, 9), (xi, 9), (xi - 6, 40), (xi - 18, 80), (xo + 34, 106), (xo + 30, 120),
           (xo + 36, 150), (xo + 44, 168), (xo + 4, 168), (xo, 120), (xo - 1, 60)]
    msk = m.shape(pts, fill=CURTAIN, line=1)
    for xx in [xo + 10, xo + 20]:                                                # folds
        m.pencil([(xx, 12), (xx + 4, 60), (xx + 9, tie_y - 2)], smooth=True)
        m.pencil([(xx + 9, tie_y + 6), (xx + 10, 140), (xx + 14, 166)], smooth=True)
    tie = m.mask_rect(xo - 2, tie_y - 3, xo + 42, tie_y + 4, radius=3)
    m.paint(tie & m.pen(msk, 3), 'black')
    return msk


cl = curtain()
m.copy((56, 4, 136, SILL_T + 1), to=(2 * 252 - 136 + 1, 4), flip=True, mask=m.pen(cl, 5))  # right one: copy, Flip Horizontal
m.rect(52, 4, 452, 8, fill='black', line=0)                                   # rod
m.oval(52, 6, 5, 5, fill='black', line=0); m.oval(452, 6, 5, 5, fill='black', line=0)
for x in range(66, 128, 10): m.oval(x, 9, 3, 3, fill='white', line=1)          # rings
for x in range(380, 442, 10): m.oval(x, 9, 3, 3, fill='white', line=1)
# sill: lit top, wood front, dark underside
m.rect(10, SILL_T, W - 10, SILL_F + 1, fill='lighter', line=1)
m.rect(6, SILL_F, W - 6, SILL_B, fill='wood', line=1)
m.rect(16, SILL_B - 1, W - 16, SILL_B + 3, fill='gray', line=1)
m.use('bucket', 'gingham', 1)
m.cursor('bucket', 80, 70)
m.stage('room')


# ---- 5. three pots: day 2, day 14, day 40 ----------------------------------------------------------------
def pot(cx, top_w, bot_w, h, rim_h=6):
    y1 = SILL_T + 3
    y0 = y1 - h
    m.oval(cx + bot_w // 2 + 2, y1 - 1, bot_w // 2 + 2, 2, fill='gray', line=0)          # cast shadow on the sill
    body = m.mask_poly([(cx - top_w // 2 + 2, y0 + rim_h), (cx + top_w // 2 - 2, y0 + rim_h),
                        (cx + bot_w // 2, y1), (cx - bot_w // 2, y1)])
    m.paint(body, 'gray')
    shade = body & (m.XX > cx + top_w // 6)
    m.paint(shade, 'dark')
    m.paint(m.border(body, 1), 'black')
    m.rect(cx - top_w // 2, y0, cx + top_w // 2 + 1, y0 + rim_h + 1, fill='lighter', line=1)
    m.rect(cx + top_w // 4, y0 + 1, cx + top_w // 2, y0 + rim_h, fill='light', line=0)
    m.oval(cx, y0 + 1, top_w // 2 - 2, 2, fill='black', line=0)            # soil
    return y0


def leaf(base, tip, width, fill='black', vein=True):
    b, t = np.array(base, float), np.array(tip, float)
    d = t - b; n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
    pts = [b, b + d * 0.3 + n * width, b + d * 0.7 + n * width * 0.8, t, b + d * 0.7 - n * width * 0.8, b + d * 0.3 - n * width]
    m.shape(pts, fill=fill, line=1)
    if vein: m.pencil([b + d * 0.12, b + d * 0.5 + n * 0.6, t - d * 0.12], pat='white' if fill == 'black' else 'black')


P1, P2, P3 = 172, 227, 330
top1 = pot(P1, 30, 22, 24)
m.brush([(P1, top1), (P1 - 1, top1 - 8), (P1 + 1, top1 - 15)], size=2, shape='square')
leaf((P1 + 1, top1 - 15), (P1 - 12, top1 - 22), 4)
leaf((P1 + 1, top1 - 15), (P1 + 13, top1 - 21), 4)
m.oval(P1 + 14, top1 - 22, 3, 2, fill='light', line=1)                                    # seed husk on a leaf

top2 = pot(P2, 34, 26, 28)
m.brush([(P2, top2), (P2 + 2, top2 - 20), (P2 - 1, top2 - 40), (P2 + 1, top2 - 56)], size=2, shape='square')
for (bx, by), (tx, ty) in [((P2 + 1, top2 - 12), (P2 - 18, top2 - 20)), ((P2 + 2, top2 - 22), (P2 + 21, top2 - 31)),
                           ((P2, top2 - 36), (P2 - 17, top2 - 47)), ((P2, top2 - 46), (P2 + 15, top2 - 58)),
                           ((P2 + 1, top2 - 56), (P2 - 7, top2 - 66))]:
    leaf((bx, by), (tx, ty), 5, fill='gray')

top3 = pot(P3, 42, 30, 34)
FX, FY = P3 - 6, 54                                                                     # flower head
m.brush([(P3, top3), (P3 + 3, top3 - 30), (P3 - 1, top3 - 60), (FX + 2, FY + 18)], size=3, shape='square')
for (bx, by), (tx, ty), wd in [((P3 + 1, top3 - 10), (P3 - 26, top3 - 22), 9), ((P3 + 2, top3 - 26), (P3 + 30, top3 - 40), 9),
                               ((P3, top3 - 48), (P3 - 24, top3 - 64), 8), ((P3, top3 - 64), (P3 + 22, top3 - 78), 7)]:
    leaf((bx, by), (tx, ty), wd, fill='black')
for k in range(16):                                                                     # petals
    a = k * 2 * np.pi / 16 + 0.1
    base = (FX + 10 * np.cos(a), FY + 10 * np.sin(a) * 0.95)
    tip = (FX + 25 * np.cos(a), FY + 24 * np.sin(a) * 0.95)
    leaf(base, tip, 4.2, fill='white', vein=False)
m.oval(FX, FY, 12, 12, fill='black', line=1)
m.oval(FX, FY, 9, 9, fill='pebbles', line=1)
m.use('frrect', 'gray', 2)
m.cursor('brush', P2 + 1, top2 - 56)
m.stage('pots')

# ---- 6. the watering can, still dripping into the day-2 pot; the seed packet it all came from ------------------
A, CB = 108, SILL_T + 2                                                                      # can: left edge, base
m.brush([(A + 2, 144), (A - 8, 148), (A - 9, 159), (A - 4, 166), (A + 2, 166)], size=3, shape='round')     # back handle
m.brush([(A + 6, 138), (A + 11, 127), (A + 24, 125), (A + 31, 131), (A + 32, 138)], size=3, shape='round') # top handle
s0, s1 = np.array([A + 33.0, 161.0]), np.array([P1 - 15.0, top1 - 4.0])                   # spout centre line, tip at the rim
d = (s1 - s0) / np.linalg.norm(s1 - s0); n = np.array([-d[1], d[0]])
m.shape([s0 + n * 4, s1 + n * 2, s1 - n * 2, s0 - n * 4], fill='white', line=1, smooth=False)
can = m.rect(A, 136, A + 35, CB, fill='white', line=2, radius=3)
for xa, xb, pat in [(A + 2, A + 6, 'light'), (A + 25, A + 29, 'light'), (A + 29, A + 33, 'gray')]:  # cylinder bands
    m.paint(can & (m.XX >= xa) & (m.XX < xb) & (m.YY > 137) & (m.YY < CB - 2), pat)
m.paint(m.border(can, 2), 'black')
m.rect(A, 142, A + 35, 145, fill='black', line=0)                                            # hoops
m.rect(A, CB - 7, A + 35, CB - 4, fill='black', line=0)
rc = s1 + d * 2                                                                               # the rose, face-on to the spout
t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
m.shape([rc + n * 8 * np.cos(a) + d * 3 * np.sin(a) for a in t], fill='white', line=1, smooth=False)
for k in (-5, -2, 1, 4):
    m.line(rc + n * k + d, rc + n * k + d, 1)
for (dx, dy) in [(P1 - 7, top1 - 3)]:                                                      # a drip falling into the pot
    m.shape([(dx, dy - 5), (dx + 2, dy), (dx + 1, dy + 2), (dx - 1, dy + 2), (dx - 2, dy)], fill='black', line=0, smooth=False)
# seed packet with a crimped top, a flower on the front and a few spilled seeds
pk = m.shape([(16, 128), (20, 124), (24, 128), (28, 124), (32, 128), (36, 124), (40, 128), (44, 124), (48, 128), (52, 124),
              (56, 128), (58, CB), (14, CB)], fill='white', line=1, smooth=False)
m.line((16, 131), (56, 131), 1)
for k in range(8):
    a = k * np.pi / 4
    m.oval(36 + 7 * np.cos(a), 143 + 7 * np.sin(a), 3, 3, fill='white', line=1)
m.oval(36, 143, 4, 4, fill='black', line=0)
m.text('seeds', 36, 164, anchor='m')
for sx_, sy_ in [(63, CB - 1), (68, CB), (72, CB - 1)]:
    m.oval(sx_, sy_, 2, 1, fill='black', line=0)
m.use('frrect', 'white', 2)
m.cursor('cross', A + 35, CB)
m.stage('can')

# ---- 7. the cat on the sill, and the butterfly it is watching --------------------------------------------
KX = 8                                                                                        # the cat sits clear of the curtain


def K(*pts):
    """cat coordinates -> document (the cat was laid out with its front paw at x = 455)"""
    return [(x + KX, y) for x, y in pts]


cat = np.zeros((H, W), np.uint8)
cat |= m.mask_oval(497 + KX, 150, 23, 21) & (m.YY <= SILL_T + 2)                           # haunch
th = np.linspace(0, 2 * np.pi, 40, endpoint=False)
cat |= m.mask_poly(K(*[(477 + 17 * np.cos(a) * 0.94 - 26 * np.sin(a) * 0.34, 133 + 17 * np.cos(a) * 0.34 + 26 * np.sin(a) * 0.94)
                       for a in th]))                                                       # chest, leaning forward
cat |= m.mask_poly(K((453, 136), (465, 138), (464, SILL_T + 2), (452, SILL_T + 2)))         # front leg
cat |= m.mask_oval(455 + KX, SILL_T + 1, 7, 3)                                              # paw
cat |= m.mask_poly(K((458, 104), (478, 98), (486, 116), (462, 122)))                         # neck
cat |= m.mask_oval(463 + KX, 96, 14, 12)                                                    # head
cat |= m.mask_oval(452 + KX, 101, 7, 6)                                                     # muzzle
cat |= m.mask_poly(K((451, 90), (455, 72), (464, 87)))                                      # near ear
cat |= m.mask_poly(K((466, 86), (475, 72), (478, 92)))                                      # far ear
m.paint(cat, 'black')
m.brush(K((516, 166), (528, 170), (532, 182), (529, 197), (521, 204), (516, 198)), size=5, shape='round')  # tail
m.pencil(K((455, 86), (456, 79), (459, 84)), pat='white')                                                    # inner ear
m.pencil(K((464, 140), (464, SILL_T)), pat='white')                                                          # leg against chest
m.pencil(K((471, SILL_T), (472, 152), (480, 139), (495, 132)), smooth=True, pat='white')                     # haunch
m.brush(K((458, 113), (478, 107)), size=3, shape='square', pat='white')                                      # collar
m.oval(460 + KX, 118, 3, 3, fill='white', line=1)                                                             # bell
m.shape(K((453, 94), (457, 91), (462, 92), (459, 96)), fill='white', line=0, smooth=False)                   # eye, looking up-left
m.line((455 + KX, 92), (455 + KX, 94), 1)
for wy in (97, 101, 105):                                                                                     # whiskers (XOR)
    m.pencil(K((452, 102), (440, wy)), mode='invert')

# butterfly, out in the sky between the flower and the cat: a white with black wing tips
BX, BY = 371, 74
bfly = np.zeros((H, W), np.uint8)
for s in (-1, 1):
    bfly |= m.shape([(BX, BY + 1), (BX + s * 10, BY + 1), (BX + s * 13, BY + 7), (BX + s * 9, BY + 13), (BX + s * 2, BY + 8)],
                    fill='white', line=1, smooth=False)
    up = m.shape([(BX, BY - 1), (BX + s * 4, BY - 12), (BX + s * 12, BY - 17), (BX + s * 19, BY - 14), (BX + s * 17, BY - 4),
                  (BX + s * 3, BY + 1)], fill='white', line=1, smooth=False)
    bfly |= up
    m.paint(up & (m.mask_oval(BX + s * 17, BY - 15, 7, 6)), 'black')                     # black tip
    m.oval(BX + s * 9, BY - 6, 2, 2, fill='black', line=0)                                # spot
    m.oval(BX + s * 7, BY + 6, 1, 1, fill='black', line=0)
    bfly |= m.pencil([(BX, BY - 6), (BX + s * 3, BY - 13), (BX + s * 6, BY - 17), (BX + s * 8, BY - 16)], smooth=True)
bfly |= m.rect(BX - 1, BY - 6, BX + 2, BY + 9, fill='black', line=0)
m.dotted([(FX + 27, FY - 2), (FX + 33, FY - 14), (FX + 42, FY - 14), (FX + 42, FY - 4), (FX + 35, FY - 4),
          (FX + 36, FY + 6), (BX - 16, BY + 8)], gap=5, size=2)
m.zoom(449 + KX, 83, 18, 15, at=(70, 48), fat=6, title='zoom')                              # fat bits round the eye
m.use('pencil', 'black', 1)
m.cursor('pencil', 455 + KX, 94)
m.stage('cat')
m.zoom(None)

# ---- 8. spray can: the shadow under the sill and the cat's shadow on the wall -------------------------
under = m.mask_rect(0, SILL_B + 4, W, SILL_B + 14)
m.spray([(12, SILL_B + 3), (W - 12, SILL_B + 3)], radius=8, density=0.22, clip=under, seed=5)
behind = (1 - m.pen(cat, 3)) & (m.YY < SILL_T + 3) & (m.XX > 470)                     # the cat's soft shadow on the wall
m.spray([(500 + KX, 104), (522 + KX, 124), (533 + KX, 150), (535 + KX, 168)], radius=6, density=0.3, clip=behind, seed=9)
m.use('spray', 'black', 1)
m.cursor('spray', 300, SILL_B + 10)
m.stage('spray')

# ---- 9. labels: tags and arrows under the sill; a calendar with the days crossed off -------------------------
TAGS = [36, P1 - 10, P2 + 10, P3]                                                           # tag centres (under their pots)
for cx, label in zip(TAGS, ['day 0', 'day 2', 'day 14', 'day 40']):
    tw = len(label) * 7
    m.rect(cx - tw // 2 - 6, 202, cx + tw // 2 + 6, 220, fill='white', line=1, radius=4)
    m.text(label, cx, 215, anchor='m')
for xa, xb in [(TAGS[0] + 26, TAGS[1] - 26), (TAGS[1] + 26, TAGS[2] - 29), (TAGS[2] + 29, TAGS[3] - 29)]:
    m.rect(xa - 2, 207, xb + 2, 216, fill='white', line=0)
    m.line((xa, 211), (xb - 4, 211), 2)
    m.shape([(xb - 6, 206), (xb, 211), (xb - 6, 216)], fill='black', line=0, smooth=False)
CX0, CY0 = 3, 22
m.rect(CX0, CY0, CX0 + 59, CY0 + 52, fill='white', line=1)
m.rect(CX0, CY0, CX0 + 59, CY0 + 10, fill='black', line=0)
for rx in (CX0 + 12, CX0 + 45): m.rect(rx, CY0 - 4, rx + 3, CY0 + 3, fill='white', line=1)
for i in range(35):
    r, c = divmod(i, 7)
    x, y = CX0 + 2 + c * 8, CY0 + 13 + r * 8
    if i < 33:
        m.line((x + 1, y + 1), (x + 5, y + 5), 1); m.line((x + 5, y + 1), (x + 1, y + 5), 1)
    elif i == 33:
        m.oval(x + 3, y + 3, 5, 4, fill=None, line=1)
m.use('text', 'black', 1)
m.menu('Type', ['Plain', 'Bold', 'Italic', 'Underline', 'Outline', 'Shadow'], checked={'Plain'}, hilite='Shadow', styled=True)
m.cursor('arrow', 262, 66)
m.stage('type')

# ---- final: shadow-style title, marquee round the butterfly, saved ---------------------------------------------
m.menu(None)
m.text('watch it grow!', 444, 238, size=19, font='serif', style=('bold', 'shadow'), anchor='m', opaque=True)
m.select(rect=(BX - 23, BY - 22, BX + 23, BY + 17))                                       # marquee round the butterfly
m.use('marquee', 'black', 1)
m.cursor('arrow', BX + 17, BY + 12)
m.retitle('sill garden')

img = m.save(out, stages)
print(f'{out}  {time.time() - t0:.1f}s')
