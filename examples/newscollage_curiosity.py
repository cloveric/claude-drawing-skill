"""Example (newspaper collage): 好奇心周刊 · 拆开看看 / Curiosity Weekly · Take It Apart -- the cover of a made-up
weekly, cut and pasted on kraft board. A halftone photograph of a twin-bell alarm clock has been cut in two with
scissors and the top half hinged open; out of the gap fly the parts that make it tick, each its own halftone
clipping with a typed label and an inked leader line: wheels (齿轮), the mainspring (发条), the balance wheel
(摆轮, printed in red) and screws (螺丝). Behind it a scissor-cut disc of red paper; on the left a torn page of old
newsprint (generated pseudo-text), the masthead, ransom-note letters 拆开看看？ and WHAT MAKES IT TICK; masking
tape, a black postmark, a red 附零件图 (parts inside) stamp, and a typed strip that says how a clock works:
mainspring -> wheels -> balance -> hands. Every photograph is rendered from a height field, no image model.
python3 newscollage_curiosity.py [out.jpg] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from newscollage import NewsCollage, Photo, RED, INK, PAPER, MUSTARD

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'newscollage_curiosity.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

nc = NewsCollage(1920, 1080, seed=42)
CHROME = dict(albedo=0.95, metal=1.0, gloss=0.5)


# ------------------------------------------------------------ things to photograph
def alarm_clock(R=205):
    k = R / 250
    P = Photo(640, 690, seed=5, backdrop=(0.96, 0.84), lift=34)
    cx, cy = 318, 360
    for s in (-1, 1):                                                    # legs and ball feet, behind the case
        a = np.deg2rad(90 + s * 38)
        p0 = (cx + np.cos(a) * (R - 60 * k), cy + np.sin(a) * (R - 60 * k)); p1 = (cx + np.cos(a) * (R + 58 * k), cy + np.sin(a) * (R + 58 * k))
        P.rod(p0, p1, 11 * k, **CHROME)
        P.dome(p1[0], p1[1] + 4 * k, 22 * k, 20 * k, height=18 * k, **CHROME)
    P.rod((cx, cy - R + 20 * k), (cx, cy - R - 64 * k), 7 * k, **CHROME)      # hammer between the bells
    P.rod((cx - 22 * k, cy - R - 64 * k), (cx + 22 * k, cy - R - 64 * k), 9 * k, **CHROME)
    for s in (-1, 1):                                                    # bells on their posts, tilted outward
        a = np.deg2rad(-90 + s * 42)
        bx, by = cx + np.cos(a) * (R + 62 * k), cy + np.sin(a) * (R + 62 * k)
        P.rod((cx + np.cos(a) * (R - 30 * k), cy + np.sin(a) * (R - 30 * k)), (bx, by), 8 * k, **CHROME)
        P.dome(bx, by, 112 * k, 96 * k, height=70 * k, rot=-s * 42, cut=0.3, **CHROME)
        t = np.deg2rad(-s * 42); lx, ly = 112 * k * 0.95, 96 * k * 0.3
        ends = [(bx + u * np.cos(t) + ly * np.sin(t), by - u * np.sin(t) + ly * np.cos(t)) for u in (-lx * 0.97, lx * 0.97)]
        P.rod(ends[0], ends[1], 6 * k, z=6 * k, **CHROME)
    P.disc(cx, cy, R, height=20 * k, bevel=14 * k, albedo=0.55, metal=0.9, gloss=0.4)   # case, dial, bezel
    P.disc(cx, cy, R - 34 * k, z=6 * k, height=6 * k, bevel=2, albedo=0.95, metal=0.0, gloss=0.25)
    P.ring(cx, cy, R - 40 * k, R - 4 * k, z=4 * k, height=26 * k, **CHROME)
    ticks = []
    for i in range(60):
        a = np.deg2rad(i * 6 - 90)
        r0 = R - (74 if i % 5 == 0 else 62) * k
        ticks.append([(cx + np.cos(a) * r0, cy + np.sin(a) * r0), (cx + np.cos(a) * (R - 50 * k), cy + np.sin(a) * (R - 50 * k))])
    P.lines(ticks[::5], 5 * k, 0.08)
    P.lines([p for i, p in enumerate(ticks) if i % 5], 2.4 * k, 0.12)
    for i in range(1, 13):
        a = np.deg2rad(i * 30 - 90)
        P.text(str(i), cx + np.cos(a) * (R - 108 * k), cy + np.sin(a) * (R - 108 * k), 46 * k, 'didone', 0.08, 'mm')

    def hand(angle, L, W, tail, z):
        a = np.deg2rad(angle - 90); ux, uy = np.cos(a), np.sin(a); nx, ny = -uy, ux
        pts = [(-tail, -W * 0.5), (L * 0.62, -W * 0.5), (L * 0.72, -W * 1.5), (L, 0), (L * 0.72, W * 1.5), (L * 0.62, W * 0.5), (-tail, W * 0.5)]
        P.poly([(cx + ux * u + nx * v, cy + uy * u + ny * v) for u, v in pts], z=z, height=4, bevel=1.5, albedo=0.12, metal=0.4, gloss=0.5)
    hand(-58, 118 * k, 9 * k, 20 * k, 12 * k)                           # ten past ten
    hand(52, 172 * k, 7 * k, 26 * k, 16 * k)
    a = np.deg2rad(150 - 90)
    P.rod((cx - np.cos(a) * 40 * k, cy - np.sin(a) * 40 * k), (cx + np.cos(a) * 190 * k, cy + np.sin(a) * 190 * k), 2.2 * k, z=20 * k, albedo=0.15, metal=0.3)
    P.dome(cx, cy, 15 * k, z=22 * k, height=8 * k, **CHROME)
    P.glare(cx, cy, 150 * k, 205 * k, 195, 255, 0.45)                   # the glass crystal
    P.glare(cx, cy, 60 * k, 90 * k, 20, 50, 0.2)
    return P, (cx, cy)


def wheel(r, teeth, spokes=5, pinion=None, rot=0.0, seed=1):
    n = int(2 * r + 60)
    P = Photo(n, n, seed=seed, backdrop=(0.96, 0.86), lift=8)
    P.gear(r + 20, r + 20, r, teeth=teeth, spokes=spokes, pinion=pinion, rot=rot, albedo=0.56, metal=0.32,
           depth=r * 0.11, rim=r * 0.15)
    return P, (r + 20, r + 20)


def balance_wheel(r=62, seed=7):
    n = int(2 * r + 70)
    P = Photo(n, n, seed=seed, backdrop=(0.96, 0.86), lift=8)
    c = r + 22
    P.ring(c, c, r - 11, r, height=6, albedo=0.42, metal=0.35, gloss=0.5)
    P.rod((c - r + 6, c), (c + r - 6, c), 4.5, albedo=0.45, metal=0.4)
    for i in range(10):                                                  # timing screws round the rim
        a = np.deg2rad(i * 36 + 18)
        P.dome(c + np.cos(a) * (r + 3), c + np.sin(a) * (r + 3), 5, height=5, albedo=0.8, metal=0.8, gloss=0.5)
    P.spiral(c, c, 7, r * 0.52, turns=7, width=1.8, z=8, height=1.5, albedo=0.35, metal=0.7)
    P.disc(c, c, 7, z=6, height=6, albedo=0.7, metal=0.9)
    return P, (c, c)


def mainspring(r=80, seed=9):
    n = int(2 * r + 70)
    P = Photo(n, n, seed=seed, backdrop=(0.96, 0.86), lift=8)
    c = r + 22
    P.spiral(c, c, 12, r, turns=4.5, width=6.5, height=3, albedo=0.45, metal=0.5, rot=30, flare=1.6)
    P.disc(c, c, 10, height=5, albedo=0.6, metal=0.8, hole=3)
    return P, (c, c)


def screw_photo(length=96, r=10, seed=11):
    P = Photo(int(length + 70), int(4 * r + 60), seed=seed, backdrop=(0.96, 0.86), lift=8)
    P.screw(22, 2 * r + 20, length, r, rot=0)
    return P, (22 + length / 2, 2 * r + 20)


def clip_photo(P, c, cell, margin=9, ink=INK, shadow=0.35):
    s = nc.print_photo(P, cell=cell, ink=ink, shadow=shadow)
    return s.cutout(margin, centre=c)


def place(sheet, local, canvas, rot):
    """paste so that the sheet's local point `local` lands on `canvas`"""
    u, v = local[0] - sheet.w / 2, local[1] - sheet.h / 2
    t = np.deg2rad(rot)
    cx = canvas[0] - (u * np.cos(t) + v * np.sin(t)); cy = canvas[1] - (-u * np.sin(t) + v * np.cos(t))
    return nc.paste(sheet, cx, cy, rot)


# ------------------------------------------------------------ kraft board
nc.board()
nc.stage('board')

# ------------------------------------------------------------ old newspaper, torn by hand
s = nc.newsprint(660, 1080, columns=3, size=10.5)
s.tear('rtb', depth=11, rim=8)
s.wrinkle(0.7)
nc.paste(s, 250, 548, rot=-2.2)
s = nc.newsprint(560, 430, columns=3, size=10, headline=1, picture=False)
s.tear('lt', depth=10, rim=7)
nc.paste(s, 1700, 935, rot=3.5)
nc.stage('newsprint')

# ------------------------------------------------------------ red paper disc
nc.disc(1104, 500, 318, RED)
nc.stage('red_disc')

# ------------------------------------------------------------ the clock, cut in two; the top half hinged open
P, C = alarm_clock()
cs = clip_photo(P, C, 6.2, margin=14, shadow=0.55)
ang = np.deg2rad(18)
d = np.array([np.cos(ang), -np.sin(ang)])
top, bottom = cs.split(np.array(C) - d * 420, np.array(C) + d * 420, kinks=4, jag=3)
CX, CY = 1066, 548                                                       # dial centre on the board
place(bottom, C, (CX, CY), 0)
pivot_l = np.array(C) - d * 222                                          # hinge: where the cut leaves the case
pivot = (CX + pivot_l[0] - C[0], CY + pivot_l[1] - C[1])
place(top, pivot_l, pivot, 11)
nc.stage('clock')

# ------------------------------------------------------------ the parts that make it tick, flying out of the gap
for p0, p1, bend in [((1282, 440), (1470, 330), -40), ((1276, 428), (1650, 190), -90), ((1288, 456), (1790, 350), -60),
                     ((1270, 478), (1610, 560), 50)]:                       # flight paths out of the gap
    p0 = np.array(p0, float); p1 = np.array(p1, float); mid = (p0 + p1) / 2
    nrm = np.array([-(p1 - p0)[1], (p1 - p0)[0]]) / np.hypot(*(p1 - p0))
    nc.pen([p0, mid + nrm * bend, p1], 2.0, INK, 0.7, dash=(9, 9))
parts = {}
p, c = screw_photo(); parts['screw1'] = place(clip_photo(p, c, 5.2, 10), c, (1346, 420), 28)
p, c = wheel(108, 36, 5, pinion=24, rot=4, seed=21); parts['gear1'] = place(clip_photo(p, c, 5.8), c, (1478, 318), 12)
p, c = wheel(70, 26, 4, pinion=16, rot=9, seed=22); parts['gear2'] = place(clip_photo(p, c, 5.4), c, (1660, 170), -8)
p, c = wheel(46, 16, 4, pinion=11, seed=23); parts['gear3'] = place(clip_photo(p, c, 5.0), c, (1392, 156), 0)
p, c = balance_wheel(); parts['balance'] = place(clip_photo(p, c, 5.0, ink=RED), c, (1802, 350), 0)
p, c = mainspring(); parts['spring'] = place(clip_photo(p, c, 5.6), c, (1618, 560), 0)
p, c = screw_photo(80, 9, seed=12); parts['screw2'] = place(clip_photo(p, c, 5.0, 10), c, (1826, 598), -62)
nc.stage('parts')

# ------------------------------------------------------------ typed labels and inked leader lines
nc.label('齿轮 GEAR', 1520, 470, 25, 'typewriter', rot=2)
nc.pen([(1560, 452), (1540, 425), (1515, 395)], 2.2, dot=3.5)
nc.label('摆轮 BALANCE', 1700, 470, 25, 'typewriter', rot=-3)
nc.pen([(1800, 448), (1806, 430), (1806, 418)], 2.2, dot=3.5)
nc.label('发条 MAINSPRING', 1430, 680, 25, 'typewriter', rot=-1.5)
nc.pen([(1600, 662), (1608, 640), (1612, 622)], 2.2, dot=3.5)
nc.label('螺丝 SCREW', 1268, 300, 22, 'typewriter', rot=4)
nc.pen([(1318, 318), (1328, 360), (1338, 398)], 2.2, dot=3.5)
nc.stage('labels')

# ------------------------------------------------------------ masthead
m = nc.sheet(660, 214, PAPER)
tm = m.text_mask('CURIOSITY WEEKLY  ·  No.42  ·  2026 AUTUMN', 330, 190, 22, 'grotesk', 'ms', spacing=3)
m.block(0, 162, 660, 214, RED, minus=tm)
m.text('好奇心周刊', 330, 138, 122, 'cjk_song', INK, 'ms')
m.tear('b', depth=6, rim=5)
m.cut_rect(1, 2)
nc.paste(m, 372, 128, rot=-1.6, lift=0.8)
nc.stage('masthead')

# ------------------------------------------------------------ ransom-note title
CL = nc.CLIPPINGS
title = nc.ransom('拆开看看', 54, 806, 116, rot=1.5, faces=['cjk_song', 'cjk_hei', 'cjk_kai', 'cjk_round'],
                  styles=[CL[2], (PAPER, None, INK, ''), CL[3], CL[1]], seed=4)
last = title[-1][0]
q = nc.clipping('？', 124, 'cjk_song', MUSTARD, None, INK)
nc.paste(q, *last.pt(last.w + q.w * 0.5 - 4, last.h * 0.5 + 40), rot=-9)
nc.ransom('WHAT MAKES IT TICK', 70, 972, 54, rot=0.5, seed=8)
nc.stage('title')

# ------------------------------------------------------------ how it works, stamps, tape
nc.label('发条上劲 → 齿轮传动 → 摆轮定速 → 指针走动', 1432, 846, 21, 'typewriter', rot=-1.2)
nc.stamp(1210, 960, [('附零件图', 40), ('PARTS INSIDE', 22)], rot=7, colour=RED, face='slab', pressure=200)
nc.stamp(690, 262, [('10·01', 34)], shape='round', r=88, ring='好奇心周刊 · CURIOSITY WEEKLY ·', colour=INK,
         face='typewriter_bold', ring_face='cjk_hei', ring_size=18, alpha=0.82, rot=-12)
nc.tape(56, 44, 150, rot=-40)
nc.tape(600, 34, 150, rot=24)
nc.tape(1462, 730, 150, rot=-32, width=42)
nc.tape(848, 744, 110, rot=58, width=38)

nc.save(out, stages_dir=stages)
print('saved', out)
