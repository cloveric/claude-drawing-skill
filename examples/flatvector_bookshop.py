"""Example (flat vector): 周末书店 / The Weekend Bookshop — a Saturday at dusk in a small bookshop, drawn as a
modern flat illustration: no outlines, seven flat colours, volume from overlapping colour blocks, a whisper of
grain. The one small story: the only coral book has just come down from the top poetry shelf. A bookseller on
the rolling ladder hangs on to the rail with one hand and lowers it with the other; a silver-haired customer in a
mustard coat reaches up for it; a dashed coral trail marks its drop from the gap it left (the neighbour has
already tipped over into the space). Beside the arched window -- an OPEN sign on strings, the sun setting behind
the street -- a reader sits in a lounge chair under a pendant lamp's beam, a mug steaming on the side table; the
shop cat watches the street from the sill; a crate of second-hand books waits on the floor.
No image model.
python3 flatvector_bookshop.py [out.jpg] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from flatvector import FlatVector, Mask, INK, BLUE, CORAL, MUSTARD, TEAL, PEACH, CREAM

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'flatvector_bookshop.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

W, H = 1920, 1080
fv = FlatVector(W, H, seed=5, light=(0.8, -0.6))
T = fv.tone
FLOOR_Y = 905
WOOD = T(MUSTARD, -0.12)

# ---------------------------------------------------------------- wall and floor
fv.backdrop(BLUE)
floor = fv.rect(0, FLOOR_Y, W, H)
fv.fill(floor, T(MUSTARD, -0.3))
for y in (938, 984, 1046):                                                   # plank joints, wider apart toward us
    fv.fill(fv.rect(0, y, W, y + 5), T(MUSTARD, -0.38))
fv.fill(fv.rect(0, 738, W, FLOOR_Y), T(BLUE, -0.08))                        # wainscot below the sill line
fv.fill(fv.rect(0, 732, W, 744), T(BLUE, 0.12))                               # dado rail
fv.fill(fv.rect(0, FLOOR_Y - 22, W, FLOOR_Y), T(BLUE, -0.3))                 # skirting board
fv.stage('wall')

# ---------------------------------------------------------------- the arched window, sunset outside
WX0, WX1, WY0, WY1 = 1150, 1560, 170, 716
wr = (WX1 - WX0) / 2
opening = fv.rrect(WX0, WY0, WX1, WY1, (wr, wr, 0, 0))
glass = fv.rrect(WX0 + 24, WY0 + 24, WX1 - 24, WY1, (wr - 24, wr - 24, 0, 0))
fv.fill(opening, CREAM)
sky = [(WY0, T(PEACH, 0.45)), (330, T(PEACH, 0.2)), (440, PEACH), (540, T(CORAL, 0.3))]
for y, c in sky:
    fv.fill(glass & fv.rect(WX0, y, WX1, WY1), c)
fv.fill(glass & fv.circle(1405, 560, 74), MUSTARD)                            # the low sun
fv.fill(glass & fv.circle(1405, 560, 74) & fv.rect(0, 560, W, H), T(MUSTARD, 0.25))
far = [(1150, 560), (1215, 505), (1262, 585), (1330, 540), (1470, 598), (1512, 520)]
for x, y in far:                                                              # far blocks, brick-red
    fv.fill(glass & fv.rect(x, y, x + 64, WY1), T(CORAL, -0.28))
near = [(1150, 610, 110), (1262, 640, 70), (1335, 596, 96), (1432, 650, 70), (1500, 612, 80)]
for x, y, w in near:                                                          # near blocks with lit windows
    b = glass & fv.rect(x, y, x + w, WY1)
    fv.fill(b, T(BLUE, -0.42))
    for wy in range(y + 16, WY1 - 10, 30):
        for wx in range(x + 12, x + w - 12, 24):
            if (wx * 7 + wy * 3) % 5 < 2:
                fv.fill(glass & fv.rect(wx, wy, wx + 10, wy + 14), MUSTARD)
fv.fill(glass & fv.rect(WX0, 686, WX1, WY1), T(BLUE, -0.55))                  # the street wall opposite
mull = fv.rect(1350, WY0, 1360, WY1) | fv.rect(WX0, 440, WX1, 450)
fv.fill(mull & opening, CREAM)
fv.fill(fv.rect(WX0 + 24, WY0, WX0 + 36, WY1) & glass, T(CREAM, -0.14))       # reveal: inner side of the frame
# a little OPEN sign hanging inside the glass on two strings
SX, SY = 1264, 322
for dx in (-44, 44):
    fv.fill(fv.capsule((SX, 250), (SX + dx, SY - 20), 1.6), T(INK, 0.2))
fv.fill(fv.circle(SX, 250, 5), T(INK, 0.2))
sign = fv.rrect(SX - 64, SY - 22, SX + 64, SY + 44, 10)
fv.fill(sign, TEAL); fv.shade(sign, 0.0, 6, colour=T(TEAL, -0.2))
fv.text('OPEN', SX, SY + 8, 25, CREAM, anchor='ms', spacing=4)
fv.text('10:00 — 22:00', SX, SY + 31, 14, T(TEAL, 0.6), anchor='ms', spacing=1, font_style='geo_medium')
sill = fv.rrect(WX0 - 28, WY1 - 6, WX1 + 28, WY1 + 22, 6)
fv.cast(sill, 0, 14, 0.28)
fv.fill(sill, CREAM)
fv.fill(fv.rect(WX0 - 28, WY1 + 14, WX1 + 28, WY1 + 22) & sill, T(CREAM, -0.14))
# the low sun lays a patch of light across the floor, falling toward us and to the left
patch = fv.poly([(1190, FLOOR_Y), (1520, FLOOR_Y), (1300, H), (820, H)])
fv.fill(patch, T(PEACH, 0.2), 0.2, grain=0.5)
fv.stage('window')

# ---------------------------------------------------------------- the bookcase
BX0, BX1, BY0 = 70, 1010, 66
case = fv.rect(BX0, BY0, BX1, FLOOR_Y)
fv.cast(case, 22, 0, 0.3, clip=fv.rect(0, 0, W, FLOOR_Y))                     # hard shadow on the wall
fv.fill(case, CREAM)
fv.shade(case, 0.0, 14, colour=T(CREAM, -0.12))
fv.fill(fv.rect(BX0 - 16, BY0 - 14, BX1 + 16, BY0 + 12), T(CREAM, -0.06))     # top cap
fv.text('周末书店', 120, 142, 60, INK, cjk='cjk')
x_dot = 120 + fv.text_width('周末书店', 60, cjk='cjk') + 22
fv.fill(fv.circle(x_dot, 124, 6), CORAL)
fv.text('WEEKEND BOOKS', x_dot + 22, 136, 30, T(BLUE, -0.1), spacing=6)
rows = [(172, 316), (330, 474), (488, 632), (646, 790)]                       # (top, board) per row
bays = [(BX0 + 22, 372), (390, 690), (708, BX1 - 22)]
back = Mask(np.zeros((0, 0)))
for (y0, y1) in rows:
    for (a, b) in bays:
        back = back | fv.rect(a, y0, b, y1)
back = back | fv.rect(BX0 + 22, 804, BX1 - 22, 856)
fv.fill(back, T(BLUE, -0.3))
fv.darken(back & fv.rect(0, 0, W, 186) | back & fv.rect(0, 330, W, 344) | back & fv.rect(0, 488, W, 502)
          | back & fv.rect(0, 646, W, 660), 0.18)                               # under each board, a flat shadow
fv.fill(fv.rect(BX0 + 22, 856, BX1 - 22, 872), CREAM)
# the ladder rail runs along under the top cap
fv.fill(fv.capsule((BX0 + 10, 162), (BX1 - 10, 162), 7), INK)
for x in (BX0 + 30, 540, BX1 - 30):
    fv.fill(fv.rrect(x - 7, 150, x + 7, 176, 3), T(INK, 0.2))
fv.stage('bookcase')

# ---------------------------------------------------------------- books
cols = [INK, CREAM, TEAL, MUSTARD, PEACH, T(BLUE, 0.45), T(TEAL, -0.3)]
for ri, (y0, y1) in enumerate(rows):
    for bi, (a, b) in enumerate(bays):
        gap = (842, 40) if (ri, bi) == (0, 2) else (None, 0)
        stack = {(1, 0): 250, (2, 1): 560, (3, 2): 900, (0, 0): None}.get((ri, bi))
        fv.books(a + 4, b - 2, y1, (y1 - y0) * 0.9, cols, seed=100 + ri * 10 + bi, gap_at=gap[0], gap_w=gap[1],
                 stack_at=stack, back=back)
fv.books(BX0 + 26, BX1 - 24, 856, 48, [T(INK, 0.1), T(TEAL, -0.2), T(BLUE, 0.3)], seed=77, w_range=(0.9, 1.6), title=False)
# category tabs hanging from the boards
for (x, y, s) in [(918, 316, '诗歌 POETRY'), (240, 474, '小说 FICTION'), (470, 632, '旅行 TRAVEL')]:
    w = fv.text_width(s, 17, spacing=1.5) + 30
    tab = fv.rrect(x - w / 2, y + 2, x + w / 2, y + 34, (0, 0, 8, 8))
    fv.fill(tab, MUSTARD)
    fv.text(s, x, y + 25, 17, INK, anchor='ms', spacing=1.5)
fv.stage('books')

# ---------------------------------------------------------------- furniture: ladder, plant, table, chair, lamp
# rolling ladder: hooks on the rail, stiles splay toward the wheels on the floor
LT, LB = 162, 932
stiles = [((598, LT), (578, LB)), ((724, LT), (744, LB))]
for (p0, p1) in stiles:
    fv.cast(fv.capsule(p0, p1, 9), -10, 0, 0.25, clip=back | case)
for yr in range(236, 900, 74):
    t = (yr - LT) / (LB - LT)
    xa, xb = 598 + (578 - 598) * t, 724 + (744 - 724) * t
    fv.fill(fv.rrect(xa, yr - 7, xb, yr + 7, 4), T(WOOD, -0.12))
for (p0, p1) in stiles:
    s = fv.capsule(p0, p1, 11)
    fv.fill(s, WOOD); fv.shade(s, 0.0, 7, colour=T(WOOD, -0.2))
fv.fill(fv.circle(598, LT, 13) | fv.circle(724, LT, 13), INK)                 # hooks over the rail
fv.darken(fv.ellipse(661, LB + 14, 120, 10), 0.3)
for x in (578, 744):
    fv.fill(fv.circle(x, LB, 15), INK); fv.fill(fv.circle(x, LB, 5), T(INK, 0.4))

fv.stage('ladder')

# tall plant between the bookcase and the window
fv.darken(fv.ellipse(1090, 928, 80, 9), 0.3)
fv.plant(1090, 928, 430, pot=CREAM, leaf=TEAL, kind='leafy', seed=8, n=9)

# rug, lounge chair (facing left), side table
rug = fv.rrect(1260, 912, 1880, 968, 28)
fv.fill(rug, T(TEAL, -0.42))
for x in range(1296, 1860, 44):
    fv.fill(fv.rect(x, 912, x + 14, 968) & rug, T(TEAL, -0.28))
CH = T(TEAL, 0.0)
for (p0, p1, k) in [((1560, 850), (1548, 928), -0.3), ((1790, 850), (1806, 928), -0.3)]:
    fv.fill(fv.capsule(p0, p1, 7, 5), T(WOOD, k))                              # far legs
fv.darken(fv.ellipse(1680, 934, 150, 10), 0.3)
backrest = fv.rrect(1742, 590, 1836, 850, (46, 46, 30, 30), rot=-10)
fv.cast(backrest, -26, 0, 0.22, clip=fv.rect(0, 0, W, FLOOR_Y - 22))
fv.fill(backrest, CH); fv.shade(backrest, 0.0, 26, colour=T(CH, -0.2))
fv.fill(fv.rrect(1760, 610, 1800, 720, 20, rot=-10), T(CH, 0.14))            # the button tuft band
seat = fv.rrect(1530, 792, 1800, 850, 24)
fv.fill(seat, CH); fv.shade(seat, 0.0, 18, colour=T(CH, -0.2))
fv.fill(fv.rect(1540, 846, 1806, 862), WOOD)
for (p0, p1) in [((1580, 860), (1568, 930)), ((1772, 860), (1788, 930))]:
    fv.fill(fv.capsule(p0, p1, 8, 6), WOOD)
# side table with two books and a mug of tea
TT = 816
fv.darken(fv.ellipse(1390, 932, 70, 8), 0.3)
fv.fill(fv.capsule((1390, TT), (1390, 924), 7), T(INK, 0.15))
fv.fill(fv.rrect(1344, 918, 1436, 930, 6), T(INK, 0.15))
top = fv.rrect(1316, TT, 1464, TT + 16, 8)
fv.fill(top, WOOD); fv.shade(top, 0.0, 6, colour=T(WOOD, -0.2))
yb = TT
for (x, w, h, c) in [(1334, 116, 18, INK), (1344, 100, 16, T(BLUE, 0.45))]:
    bk = fv.rrect(x, yb - h, x + w, yb, 3)
    fv.fill(bk, c); fv.fill(fv.rect(x + w - 10, yb - h, x + w, yb) & bk, T(c, -0.2))
    fv.fill(fv.rect(x, yb - h * 0.6, x + w - 12, yb - h * 0.4), T(c, 0.5))
    yb -= h
MX = 1398
mug = fv.rrect(MX, yb - 44, MX + 40, yb, (4, 4, 10, 10))
fv.fill(fv.arc(MX + 40, yb - 23, 8, 15, -90, 90), CREAM)
fv.fill(mug, CREAM); fv.shade(mug, 0.0, 10, colour=T(CREAM, -0.14))
fv.fill(fv.rect(MX, yb - 33, MX + 40, yb - 25), CORAL)
MUG_TOP = yb - 44
# pendant lamp over the chair (its beam comes later)
LX, LY = 1655, 346
fv.pendant(LX, 0, LY, 56, shade=INK, bulb=CREAM)
# a crate of second-hand books on the floor, bottom left
fv.darken(fv.ellipse(290, 1010, 200, 12), 0.3)
fv.books(150, 430, 948, 118, [CREAM, T(BLUE, 0.45), TEAL, MUSTARD, PEACH, INK], seed=31, w_range=(0.16, 0.3), title=False)
crate = fv.rrect(128, 930, 452, 1010, 6)
fv.fill(crate, WOOD); fv.shade(crate, 0.0, 16, colour=T(WOOD, -0.2))
for y in (955, 983):
    fv.fill(fv.rect(128, y, 452, y + 4), T(WOOD, -0.28))
fv.fill(fv.rrect(250, 944, 330, 996, 6), CREAM)                             # a card pinned on the front
fv.text('¥10', 290, 980, 26, INK, anchor='ms')
fv.stage('furniture')

# ---------------------------------------------------------------- people
# the customer in front of the bookcase, reaching up for the book, head tipped back to look at it
fv.darken(fv.ellipse(912, 962, 78, 9), 0.32)
BOOK = (786, 372)
B = fv.person((908, 748), 400, facing=-1, lean=-5, head_tilt=-20, hand_far_to=(826, 458), arm=(-6, 4),
              leg=(-3, 0), leg_far=(5, 0), top=MUSTARD, bottom=INK, coat=True, hair=T(CREAM, -0.2), hair_style='bob',
              bag=CREAM)
# the bookseller on the ladder: near foot on a rung, far foot one rung up, far hand on the rail, the near hand
# lowering the book
RUNG = lambda y: (y - 7)
A = fv.person((652, 404), 372, facing=1, lean=8, head_tilt=12, hand_to=(BOOK[0] - 14, BOOK[1] + 6),
              hand_far_to=(742, 166), foot_to=(648, RUNG(606) - 15), foot_far_to=(682, RUNG(532) - 15),
              top=CREAM, bottom=T(INK, 0.1), apron=TEAL, hair=T(MUSTARD, -0.62), hair_style='bun', draw_near_arm=False)
fv.book(*BOOK, 66, 88, rot=-16, colour=CORAL)
fv.near_arm()
fv.stage('handoff')
# the reader in the lounge chair, a book open in both hands, head bowed over it
C = fv.person((1692, 790), 372, facing=-1, sit=True, lean=-6, head_tilt=18, hand_to=(1612, 716), hand_far_to=(1598, 728),
              foot_to=(1560, 884), foot_far_to=(1600, 892), top=CREAM, bottom=INK, shoes=CREAM, hair=T(CORAL, -0.6),
              hair_style='bob', draw_near_arm=False)
fv.book(1600, 712, 104, 66, rot=-22, colour=MUSTARD, open=True)
fv.near_arm()
# the shop cat on the sill, watching the street
fv.cat(1296, WY1 - 6, 78, T(MUSTARD, -0.12), facing=1, tail_down=WY1 + 80)
fv.stage('reader')

# ---------------------------------------------------------------- light and the story marks
fv.fill(fv.poly([(LX - 40, LY), (LX + 40, LY), (1800, 912), (1500, 912)]), T(CREAM, 0.3), 0.12, grain=0.4)
fv.fill(fv.circle(LX, LY + 3, 17), T(CREAM, 0.5))
# a dashed trail from the empty slot on the top shelf down to the book in the bookseller's hand
fv.dashes([(862, 262), (850, 318), (818, 338)], width=6, dash=14, gap=11, colour=CORAL)
for (x, y, r, c) in [(884, 236, 15, MUSTARD), (744, 326, 10, CREAM), (824, 300, 8, CREAM)]:
    fv.sparkle(x, y, r, c)
# steam off the mug
for dx, h in ((-7, 48), (7, 36)):
    y0 = MUG_TOP - 8
    fv.fill(fv.tube([(MX + 20 + dx, y0), (MX + 26 + dx, y0 - h * 0.35), (MX + 16 + dx, y0 - h * 0.7), (MX + 21 + dx, y0 - h)],
                    [3.2, 3, 2.2, 1.2]), CREAM, 0.75)
img = fv.save(out, stages_dir=stages)                                          # the final frame is the 'light' stage
print('saved', out)
