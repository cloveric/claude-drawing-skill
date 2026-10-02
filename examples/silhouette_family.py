"""Example (cut-paper silhouette / 剪影): 剪影小像 · Shades of the Wren Household — three oval gilt frames hung from a
picture rail on a block-printed Regency stripe wallpaper, c. 1791. In the middle Mrs. Hannah Wren, cut in black
paper in a wide-brimmed hat with ostrich plumes, frizzed hair and ringlets, a puffed fichu; she looks to the right,
toward the brig Dove coming home under full sail past the lighthouse; on the left her tabby Tibbs sits on a
tasselled cushion and looks at her. Loose snips for plume barbs, lashes, whiskers, ribbon ends and rigging;
thin shell-gold bronzing over the black; iron-gall captions; verre eglomise mounts and convex glass.
All three sitters are invented. Draw-on stages: wall -> frames -> lady -> cat -> ship -> bronzing -> captions ->
glass. No image model.
python3 silhouette_family.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from silhouette import Silhouette, smooth

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'silhouette_family.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

s = Silhouette(1920, 1080, seed=11)
rng = np.random.default_rng(5)
s.wallpaper(ground='#7d95a0', ink='#ebe0c4')
s.picture_rail(0, 42)
s.chair_rail(1004, 26)
s.stage('wall')

FL = s.frame(440, 604, 158, 204, width=50, hook=True, spread=30)
FC = s.frame(960, 566, 222, 286, width=62, hook=True, spread=34, twist=1.0)
FR = s.frame(1480, 604, 158, 204, width=50, hook=True, spread=30)
s.stage('frames')


def ellipse(cx, cy, rx, ry, rot=0.0, n=36):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c, si = np.cos(np.radians(rot)), np.sin(np.radians(rot))
    x, y = rx * np.cos(t), ry * np.sin(t)
    return np.stack([cx + x * c - y * si, cy + x * si + y * c], 1)


def arc(cx, cy, r, a0, a1, n=12, ry=None):
    t = np.radians(np.linspace(a0, a1, n))
    return np.stack([cx + r * np.cos(t), cy + (ry or r) * np.sin(t)], 1)


# ==================================================================== Mrs. Hannah Wren (faces right)
L = s.sheet(FC, at=(722, 268), scale=0.5)
body = [(515, 330), (540, 352), (552, 384), (558, 410), (554, 428), (563, 452), (576, 474), (585, 488), (580, 497),
        (568, 500), (558, 504), (562, 514), (566, 520), (557, 526), (561, 532), (556, 542), (549, 550), (555, 565),
        (550, 578), (530, 586), (508, 592), (498, 610), (497, 640),
        (505, 652), (535, 668), (572, 696), (598, 735), (606, 778), (598, 815), (584, 842), (576, 862), (586, 880),
        (566, 896), (510, 906), (430, 910), (350, 903), (298, 888), (276, 866),
        (283, 830), (298, 782), (318, 734), (350, 692), (392, 658), (412, 622), (412, 570), (406, 510), (414, 440),
        (440, 375), (478, 340)]
L.shape(smooth(body, 6))
frizz = [(552, 350), (566, 336), (578, 318), (582, 300), (540, 296), (470, 304), (400, 316), (340, 336), (306, 372),
         (300, 420), (314, 466), (348, 500), (392, 516), (430, 505), (470, 450), (520, 380)]
L.shape(smooth(frizz, 6))
L.scallop(smooth([(394, 518), (350, 502), (316, 468), (300, 420), (306, 372), (334, 338)], 8, closed=False), r=(9, 14), outset=0.25)
L.scallop(smooth([(576, 312), (568, 330), (556, 346)], 6, closed=False), r=(6, 8), outset=0.2)
for k in range(9):                                                                    # a few loose wisps
    a0 = np.radians(150 + k * 14); x0, y0 = 440 + 128 * np.cos(a0), 410 + 100 * np.sin(a0)
    L.snip(smooth([(x0, y0), (x0 - 10 + rng.normal(0, 3), y0 + 4), (x0 - 16, y0 + 14 + rng.normal(0, 3))], 4, closed=False), 2.6, 0.3)
# hat: a wide brim seen almost edge-on (thick at the crown, tapering, front turned up, back drooping),
# a low ruched crown, a ribbon bow with long loops, two streamers, three ostrich plumes
u = np.linspace(0, 1, 60)
brim_c = smooth([(232, 362), (300, 342), (380, 320), (470, 302), (560, 288), (640, 277), (694, 266), (722, 252), (732, 240)], 6, closed=False)
L.snip(brim_c, 3 + 19 * np.sin(np.pi * np.clip(u * 1.08 - 0.04, 0, 1)) ** 0.8 + 2 * u, loose=False)
crown = [(388, 316), (372, 286), (376, 250), (398, 222), (440, 202), (495, 195), (548, 202), (588, 224), (604, 254),
         (598, 284), (588, 300)]
L.shape(smooth(crown, 6))
L.scallop(smooth([(374, 262), (384, 234), (412, 210), (452, 198), (500, 193), (548, 200), (586, 222), (604, 250)], 8, closed=False),
          r=(6, 8), outset=0.1, step=1.15)
knot = np.array([378.0, 262.0])
for (ang, ln, wd) in [(-142, 50, 18), (-178, 44, 15)]:
    d_ = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
    c_ = knot + d_ * ln * 0.55
    L.shape(ellipse(c_[0], c_[1], ln * 0.6, wd * 0.62, ang, 30))
    L.hole(ellipse(c_[0] + d_[0] * 4, c_[1] + d_[1] * 4, ln * 0.36, wd * 0.12, ang, 20))      # the slit inside the loop
L.disc(knot[0], knot[1], 11)
streamers = []
for k, (x0, ln, ph) in enumerate([(366, 300, 0.0), (376, 250, 1.6)]):
    p = np.stack([x0 - 66 * u - 8 * u ** 2 + 12 * np.sin(2 * np.pi * 1.2 * u + ph), 290 + ln * u], 1)
    L.snip(p, 16 * (0.25 + 0.75 * np.abs(np.cos(np.pi * 1.5 * u + ph))) + 2)
    e = p[-1]; streamers.append(p)
    L.snip([e - (0, 8), e + (-8, 14)], 8, 0); L.snip([e - (0, 8), e + (7, 13)], 8, 0)
# ostrich plumes: a tapering rachis with long curly barbs both sides
plumes = [[(468, 198), (452, 142), (412, 106), (360, 96), (320, 112), (298, 144), (302, 178)],
          [(510, 194), (526, 142), (560, 106), (606, 98), (640, 116), (646, 148)],
          [(432, 206), (394, 186), (350, 190), (318, 214), (302, 252)]]
for k, pl in enumerate(plumes):
    c = smooth(pl, 10, closed=False)
    L.snip(c, 14, 3, loose=False)
    L.fringe(c, 120 if k < 2 else 80, (46, 18), angle=55, width=3.4, side=(1, -1), bend=0.55, jitter=0.3, start=0.04)
# corkscrew ringlets falling behind the neck
rings = [L.ringlet(x, y, ln, 19, 5, 5, lean=-0.06) for (x, y, ln) in [(380, 500, 200), (402, 508, 176), (358, 492, 150)]]
# lashes, a lace frill at the neckline
for (x, y, dx, dy) in [(549, 431, 16, 3), (550, 433, 15, 7), (551, 435, 12, 10)]:
    L.snip([(x, y), (x + dx * 0.6, y + dy * 0.3), (x + dx, y + dy)], 2.4, 0.3)
L.lace(smooth([(497, 640), (512, 656), (534, 668), (558, 684)], 6, closed=False), depth=8, step=7)
s.paste(L)
s.stage('lady')

# ==================================================================== Tibbs the cat (faces right, toward her)
def cat_warp(P):
    """re-proportion the cat: head 1.12x and lowered, body squashed toward the cushion, haunch a little fuller"""
    x, y = P[:, 0], P[:, 1]
    hx, hy = 640 + (x - 640) * 1.12, 340 + (y - 340) * 1.12 + 151
    by = 855 - (855 - y) * 0.62
    bx = x - 16 * np.clip((y - 560) / 200, 0, 1) * np.clip((640 - x) / 80, 0, 1)
    w = np.clip((y - 390) / 80, 0, 1); w = w * w * (3 - 2 * w)
    return np.stack([hx * (1 - w) + bx * w, hy * (1 - w) + by * w], 1)


C = s.sheet(FL, at=(206, 342), scale=0.42, warp=cat_warp)
cushion = [(330, 872), (350, 852), (460, 846), (600, 846), (740, 850), (776, 862), (786, 884), (760, 912),
           (640, 922), (460, 922), (350, 914), (326, 894)]
C.shape(smooth(cushion, 6))
for (tx, ty, sg) in [(330, 878, -1), (786, 872, 1)]:
    C.disc(tx + sg * 6, ty + 4, 10)
    for j in range(11):
        x = tx + sg * 6 + (j - 5) * 2.4
        C.snip([(x, ty + 8), (x + (j - 5) * 1.3, ty + 28), (x + (j - 5) * 2.0 + rng.normal(0, 1), ty + 48 + rng.normal(0, 3))], 3.4, 1.2)
cat = [(708, 350), (700, 335), (690, 318), (676, 302), (662, 292),                    # nose, bridge, forehead
       (652, 286), (646, 262), (640, 238),                                           # near ear: front edge to tip
       (628, 256), (614, 278),                                                       # back edge of the ear
       (600, 290), (584, 306), (574, 330), (564, 362),                               # skull, nape
       (548, 404), (524, 462), (498, 530), (474, 596), (456, 662), (450, 730), (458, 790), (478, 828), (506, 848),   # back, haunch
       (560, 854), (640, 855), (692, 855), (708, 850), (706, 840), (694, 834),          # base, front paw
       (688, 800), (684, 740), (684, 690),                                           # front leg
       (690, 630), (698, 566), (704, 510), (700, 466),                               # chest
       (692, 436), (688, 414), (694, 398), (704, 388), (710, 376), (712, 364)]       # throat, chin, muzzle
C.shape(smooth(cat, 6))
C.shape(smooth([(600, 290), (606, 256), (616, 230), (628, 262), (626, 284)], 4))      # the far ear, just behind
tail = smooth([(486, 842), (540, 858), (620, 862), (700, 860), (742, 846), (764, 822), (766, 798), (754, 784)], 8, closed=False)
C.snip(tail, np.linspace(30, 16, 20), loose=False)
C.disc(754, 786, 8)
C.hole(smooth([(670, 838), (668, 796), (656, 772), (638, 778), (628, 808), (632, 838)], 5))   # gap between the legs
C.hole(ellipse(672, 330, 10, 5, rot=-12, n=24))                                              # the eye
C.shape(ellipse(673, 330, 1.9, 4.4, n=12))                                                    # its slit pupil
for w in [[(706, 368), (752, 358), (806, 354)], [(706, 372), (754, 374), (808, 382)], [(704, 376), (746, 390), (790, 408)],
          [(702, 366), (744, 352), (786, 334)], [(680, 312), (698, 290), (712, 268)], [(675, 310), (688, 286), (694, 262)]]:
    C.snip(smooth(w, 8, closed=False), 2.8, 0.3)
C.fringe(smooth([(700, 470), (702, 520), (696, 570), (690, 620)], 6, closed=False), 18, (18, 12), angle=55, width=4, side=(1,), bend=0.3)
C.fringe(smooth([(564, 362), (552, 396), (538, 430)], 6, closed=False), 8, 13, angle=60, width=4, side=(1,), bend=0.3)
for (x, y) in [(646, 268), (644, 256)]:
    C.snip([(x, y), (x + 9, y - 6), (x + 15, y - 14)], 2.4, 0.3)
for (bx, by, rot) in [(712, 418, -30), (710, 436, 25)]:                          # ribbon bow at the throat
    C.shape(ellipse(bx, by, 14, 7.5, rot, n=20), loose=True)
    C.hole(ellipse(bx + 2, by, 6.5, 2.8, rot, n=16))
C.disc(698, 426, 6.5)
s.paste(C)
s.stage('cat')

# ==================================================================== the brig Dove, homeward (sails left)
R = s.sheet(FR, at=(1322, 400), scale=0.39)
sea_y = lambda x: 756 + 5 * np.sin(x / 26.0) + 4 * np.sin(x / 61.0 + 1.3)
top = [(x, sea_y(x)) for x in np.arange(14, 797, 8)]
bot = [(x, 784 + 3 * np.sin(x / 40.0)) for x in np.arange(790, 20, -10)]
R.shape(np.array(top + [(800, 772)] + bot + [(10, 772)]))
crests = np.arange(40, 790, 64) + rng.uniform(-8, 8, 12)
for x0 in crests:                                                           # crests curling forward (left)
    y0 = sea_y(x0)
    R.snip(smooth([(x0 + 26, y0 + 2), (x0 + 8, y0 - 9), (x0 - 6, y0 - 9), (x0 - 12, y0 - 2), (x0 - 7, y0 + 1)], 6, closed=False), 7, 1.5)
hull = [(236, 676), (250, 692), (264, 714), (284, 738), (308, 754), (360, 762), (500, 766), (640, 764), (690, 756),
        (712, 740), (722, 716), (726, 690), (730, 668), (714, 663), (692, 668), (640, 672), (560, 680), (460, 684),
        (360, 684), (300, 680), (262, 672), (244, 666)]
R.shape(smooth(hull, 5))
for (x, y) in [(712, 680), (712, 696)]:
    R.hole([(x - 3, y - 4), (x + 4, y - 4), (x + 4, y + 3), (x - 3, y + 3)])        # stern windows
R.snip([(380, 686), (380, 300), (380, 258)], 8, 3, loose=False)                     # foremast
R.snip([(560, 682), (560, 262), (560, 218)], 9, 3, loose=False)                     # mainmast
R.snip([(266, 672), (150, 622), (110, 604)], 8, 3, loose=False)                     # bowsprit + jib-boom
R.line([(566, 636), (722, 646)], 4); R.line([(566, 552), (672, 518)], 4)         # boom, gaff
TIERS = [(380, [(322, 374, 30), (388, 452, 40), (466, 544, 52), (558, 646, 62)]),
         (560, [(276, 334, 40), (348, 424, 52), (438, 526, 64)])]


def sail(xt0, xt1, yt, xb0, xb1, yb, roach=6):
    left = smooth([(xt0, yt), (xt0 - 4 - (xt0 - xb0) * 0.5, (yt + yb) / 2), (xb0, yb)], 5, closed=False)
    foot = smooth([(xb0, yb), ((xb0 + xb1) / 2, yb - roach), (xb1, yb)], 5, closed=False)
    right = smooth([(xb1, yb), (xt1 + 4 + (xb1 - xt1) * 0.5, (yt + yb) / 2), (xt1, yt)], 5, closed=False)
    R.shape(np.vstack([left, foot, right]))
    R.line([(xt0 - 8, yt - 1), (xt1 + 8, yt - 1)], 4.5)                                # the yard


for (mx, tiers) in TIERS:
    for i, (yt, yb, hw) in enumerate(tiers):
        sail(mx - hw, mx + hw, yt, mx - hw - 7, mx + hw + 7, yb, roach=8 + i * 3)
R.line([(478, 539), (642, 539)], 4.5)                                                  # main course furled on its yard
R.scallop(smooth([(486, 541), (530, 545), (560, 546), (600, 545), (636, 541)], 6, closed=False), r=(5, 7), outset=-0.5, step=1.2)
for tri in [[(378, 318), (122, 600), (200, 602)], [(308, 470), (216, 612), (266, 614)]]:      # jibs
    h_, t_, c_ = (np.array(v, float) for v in tri)                                         # sharp corners, bellied leech
    foot = smooth([t_, (t_ + c_) / 2 + (0, 4), c_], 5, closed=False)
    leech = smooth([c_, (c_ + h_) / 2 + (10, 2), h_], 6, closed=False)
    R.shape(np.vstack([[h_, t_], foot[1:], leech[1:]]))
R.shape(smooth([(570, 552), (664, 524), (688, 576), (708, 628), (570, 630)], 4))      # spanker
for (a_, b_) in [((380, 258), (112, 604)), ((380, 360), (166, 624)), ((380, 500), (252, 668)), ((560, 218), (382, 296)),
                 ((560, 340), (382, 410)), ((380, 300), (420, 682)), ((560, 262), (640, 674)), ((560, 218), (712, 666)),
                 ((150, 622), (256, 704)), ((380, 500), (352, 682)), ((380, 500), (366, 682)), ((560, 480), (534, 680)),
                 ((560, 480), (548, 680)), ((672, 518), (722, 646))]:
    R.line([a_, b_], 2.2)
for (x, y, ln) in [(380, 258, 90), (560, 218, 110)]:                                  # pennants streaming forward
    p = np.array([(x - u * ln, y - 2 + 6 * np.sin(u * 7) * u) for u in np.linspace(0, 1, 14)])
    R.snip(p, 9, 0.5)
# the lighthouse on its rock, far off to the left: home
R.shape(smooth([(60, 764), (72, 744), (96, 732), (128, 728), (158, 734), (180, 750), (190, 766)], 5))
R.shape([(118, 734), (122, 668), (142, 668), (146, 734)])
R.shape([(114, 662), (150, 662), (150, 668), (114, 668)])
R.shape([(120, 640), (144, 640), (144, 662), (120, 662)])
R.shape([(116, 640), (132, 626), (148, 640)])
R.hole([(124, 645), (130, 645), (130, 657), (124, 657)]); R.hole([(134, 645), (140, 645), (140, 657), (134, 657)])
for (gx, gy, k) in [(232, 432, 1.1), (200, 468, 0.85)]:
    R.snip(smooth([(gx - 16 * k, gy - 2), (gx - 8 * k, gy - 8 * k), (gx, gy), (gx + 8 * k, gy - 8 * k), (gx + 16 * k, gy - 2)], 4, closed=False), 3.4, 1.2)
s.paste(R)
s.stage('ship')

# ==================================================================== bronzing: thin shell gold on the black
hair = [smooth([(568, 318), (520, 316), (468, 326), (420, 346), (380, 380)], 8, closed=False),
        smooth([(560, 336), (512, 342), (470, 362), (436, 398)], 8, closed=False),
        smooth([(548, 350), (506, 372), (478, 408), (466, 446)], 8, closed=False),
        smooth([(470, 318), (420, 334), (368, 362), (336, 404), (330, 446)], 8, closed=False),
        smooth([(430, 380), (392, 410), (366, 452), (362, 488)], 8, closed=False),
        smooth([(520, 400), (500, 432), (494, 462)], 6, closed=False)]
s.bronze(L, hair, width=2.2)
s.bronze(L, [np.array([c_[i] + (-4, 0), c_[i + 3] + (3, 4)]) for c_ in rings for i in range(8, 100, 20)], width=2.4)
s.bronze(L, [brim_c[8:-4] + (0, -5), smooth([(382, 276), (440, 268), (520, 266), (598, 272)], 6, closed=False),
             smooth([(388, 298), (450, 292), (530, 290), (594, 292)], 6, closed=False)], width=2.6)
s.bronze(L, [smooth([(420 + dx, 214), (430 + dx * 1.15, 240), (436 + dx * 1.2, 262)], 5, closed=False) for dx in (0, 46, 92, 138)], width=1.8, bright=0.7)
s.bronze(L, [p[44:-4] + (3, 0) for p in streamers], width=1.8, bright=0.85)
s.bronze(L, [ellipse(knot[0] + np.cos(np.radians(a_)) * l_ * 0.55, knot[1] + np.sin(np.radians(a_)) * l_ * 0.55, l_ * 0.5, 4, a_, 16)[2:7]
             for (a_, l_) in [(-142, 50), (-178, 44)]], width=1.8)
s.bronze(L, [smooth(p, 10, closed=False) for p in plumes], width=2.2)
s.bronze(L, [smooth([(512, 664), (546, 694), (572, 736)], 5, closed=False), smooth([(518, 694), (556, 734), (578, 784)], 5, closed=False),
             smooth([(530, 742), (562, 786), (574, 828)], 5, closed=False), smooth([(380, 682), (396, 760), (420, 860)], 5, closed=False),
             smooth([(420, 680), (452, 700), (470, 740)], 5, closed=False)], width=2.8)
beads = smooth([(497, 626), (470, 618), (440, 610), (418, 604)], 6, closed=False)
s.bronze(L, [[p, p + (2.5, 0.5)] for p in beads[::2]], width=3.2)
# cat: fur combed along the back and haunch, ear, collar, cushion piping and buttons
back = np.array([(572, 340), (560, 372), (545, 410), (520, 470), (495, 540), (470, 600), (452, 680), (450, 750), (462, 805)])
fur = []
for k in range(22):
    i = rng.integers(0, len(back) - 2); off = rng.uniform(14, 60)
    seg_ = back[i:i + 2] + np.array([off, rng.uniform(-6, 6)])
    seg_ = seg_[0] + (seg_[1] - seg_[0]) * np.linspace(0, rng.uniform(0.5, 0.9), 4)[:, None]
    fur.append(seg_)
s.bronze(C, fur, width=2.2)
s.bronze(C, [smooth([(632, 252), (626, 268), (622, 286)], 4, closed=False),
             smooth([(694, 420), (650, 404), (604, 382), (566, 364)], 6, closed=False),
             smooth([(692, 434), (648, 418), (600, 396), (562, 378)], 6, closed=False)], width=2.6)
s.bronze(C, [smooth([(334, 870), (356, 856), (420, 849), (470, 847)], 5, closed=False), smooth([(756, 852), (778, 862)], 4, closed=False),
             smooth([(330, 888), (360, 900), (460, 904), (640, 904), (760, 896), (784, 882)], 6, closed=False)], width=3.0)
# ship: gunport band, sail cloths, a glint on every crest, the lighthouse lamp
band = smooth([(268, 700), (360, 708), (500, 711), (640, 709), (712, 700)], 10, closed=False)
s.bronze(R, [band[i:i + 3] for i in range(0, len(band) - 3, 4)], width=6.0, tip=6.0)
s.bronze(R, [smooth([(250, 690), (360, 694), (500, 696), (640, 694), (720, 682)], 8, closed=False)], width=2.2)
cloth = []
for (mx, tiers) in TIERS:
    for (yt, yb, hw) in tiers:
        for q in (-0.5, 0.0, 0.5):
            cloth.append([(mx + q * hw, yt + 4), (mx + q * hw * 1.08, (yt + yb) / 2), (mx + q * (hw + 7), yb - 8)])
s.bronze(R, cloth, width=1.6, bright=0.8)
s.bronze(R, [smooth([(x0 + 20, sea_y(x0) - 1), (x0 + 4, sea_y(x0) - 7), (x0 - 8, sea_y(x0) - 5)], 4, closed=False) for x0 in crests], width=2.4)
s.stage('bronze')

# ==================================================================== captions in iron-gall ink
s.caption(FC, 'Mrs. Hannah Wren', 960, 768, 32)
s.caption(FC, 'cut in the parlour · 1791', 960, 798, 18, style='italic', alpha=0.86)
s.caption(FL, 'Tibbs', 440, 752, 32)
s.caption(FL, 'who kept the hearth', 440, 776, 16, style='italic', alpha=0.86)
s.caption(FR, 'the Brig Dove', 1480, 752, 30)
s.caption(FR, 'homeward bound · 1792', 1480, 776, 16, style='italic', alpha=0.86)
s.stage('captions')

s.glaze()
s.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
