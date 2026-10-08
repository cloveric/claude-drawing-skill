"""Example (pen & wash): 街角速写 · Sketchbook Neighbours — four little fineliner-and-watercolour cards of the
people on one street corner, photographed lying on an oak table next to the pen and the water brush.

  1  the postman, whistling, cap and jacket in cobalt; his satchel is so overstuffed that two letters have
     escaped behind him and are flapping away;
  2  a granny with huge round glasses waters her flowerpot -- but the cat has climbed into it, and the drops
     land on its head (eyes squeezed shut, paws on the rim) while the actual flower waits to the side;
  3  a kid kicks along on a scooter, the cobalt helmet (coral stripe) two sizes too big, down to the eyebrows,
     tongue out in concentration, a plaster on one knee, speed lines and dust puffs behind;
  4  a round baker in a tall white toque proudly holds a baguette longer than he is; it pokes out of the inked
     frame at the top, where a sparrow has landed on the end and is pecking at it.

Each card: quick fineliner lines (wobble, overshooting corners, open gaps, a doubled stroke here and there), then
loose washes slipped off the lines, a dried darker rim, granulation in the paper tooth, cheeks dropped wet into
wet, a flat background block that does not fill the card, white gouache glints last.
--stages writes the draw-on: the bare table, the four blank cards laid down, the ink on cards 1-2 and 3-4, the
first washes, the second washes, the background blocks, the details (glints, drops), then the fineliner and the
water brush are put down on the table for the photo.
No image model.
python3 penwash_neighbours.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from penwash import PenWash

O, S, T, B = PenWash.oval, PenWash.smooth, PenWash.turn, PenWash.box


# ------------------------------------------------------------------ shared little props
def envelope(pw, cx, cy, w, h, rot, z, airmail=False):
    """a letter: a box with its flap V; returns the part (and the airmail border dashes if any)"""
    P = B(cx, cy, w, h, rot)
    e = pw.part(P, z=z, corners=True, smooth=False)
    V = T([(cx - w / 2 + 2, cy - h / 2 + 2), (cx, cy + h * 0.08), (cx + w / 2 - 2, cy - h / 2 + 2)], cx, cy, rot)
    pw.stroke(V, z=z + 0.01, width=pw.width * 0.8, smooth=False, double=0)
    dashes = []
    if airmail:      # the striped border of an airmail envelope, as little slanted dashes along both long edges
        dashes = [T(B(cx + (t - 0.5) * w * 0.86, cy + sy * (h / 2 - 2.6), 5.5, 3.0, 35), cx, cy, rot)
                  for t in np.linspace(0.04, 0.96, 8) for sy in (-1, 1)]
    return e, dashes


def note(pw, x, y, s=1.0, z=1e9):
    """a music note: a filled oval head, a stem and a flag"""
    pw.dot(x, y, 4.6 * s)
    pw.stroke([(x + 4 * s, y - 1 * s), (x + 5 * s, y - 26 * s)], z=z, double=0, over=(0, 1))
    pw.stroke([(x + 5 * s, y - 26 * s), (x + 12 * s, y - 19 * s), (x + 13 * s, y - 12 * s)], z=z, double=0, over=(0, 1))


# ================================================================== card 1: the postman
def postman(pw):
    P = {}
    P['hair'] = pw.part([(156, 150), (178, 150), (180, 176), (172, 202), (157, 194), (151, 170)], z=11)
    P['ear'] = pw.part(O(160, 197, 12, 16), z=9)
    P['head'] = pw.part(O(228, 180, 66, 72, egg=0.06), z=10)
    P['crown'] = pw.part(S([(160, 146), (168, 112), (204, 92), (252, 89), (288, 104), (300, 132), (298, 147), (228, 152)], closed=True), z=14)
    P['band'] = pw.part([(160, 140), (300, 134), (302, 152), (162, 158)], z=15, corners=True, smooth=False)
    P['visor'] = pw.part(S([(286, 146), (322, 148), (338, 156), (320, 162), (290, 160)], closed=True), z=16)
    P['badge'] = pw.part(B(268, 145, 16, 11, -3), z=17, corners=True, smooth=False)
    pw.stroke([(261, 141), (268, 146), (276, 140)], z=17.1, width=2.0, smooth=False, double=0)
    pw.brows([[(229, 158), (238, 153), (248, 156)], [(266, 153), (275, 149), (284, 152)]], z=13)
    pw.dot(239, 175, 4.0, z=13); pw.dot(275, 172, 4.0, z=13)
    P['nose'] = pw.part(O(298, 197, 17, 15, rot=-8), z=13)
    P['stache'] = pw.part(S([(258, 212), (281, 208), (300, 213), (322, 209), (332, 220), (318, 233), (298, 229),
                             (280, 238), (260, 232), (249, 222)], closed=True), z=14)
    pw.lines([[(272, 220), (279, 230)], [(292, 219), (298, 228)], [(312, 219), (316, 227)]], z=14.1, width=2.2, double=0)
    note(pw, 352, 136, 0.9); note(pw, 376, 104, 0.7)
    # body, strap, bag and its letters
    P['legB'] = pw.limb([(212, 382), (196, 430), (182, 470)], 30, 24, z=3)
    P['legF'] = pw.limb([(258, 382), (276, 428), (292, 466)], 30, 24, z=3)
    P['shoeB'] = pw.part(O(176, 478, 22, 10, rot=-12), z=3.5)
    P['shoeF'] = pw.part(O(300, 474, 23, 11, rot=6), z=3.5)
    P['coat'] = pw.part(S([(178, 252), (215, 238), (262, 240), (284, 262), (294, 330), (300, 392), (240, 400),
                           (170, 394), (166, 330)], closed=True), z=5)
    pw.stroke([(222, 241), (238, 262), (255, 241)], z=5.2, smooth=False)
    for (x, y) in ((270, 300), (274, 342)): pw.dot(x, y, 2.6, z=5.3)
    P['strap'] = pw.limb([(264, 246), (226, 300), (186, 352)], 12, 12, z=7, caps=(False, False))
    P['letters'] = []
    for (cx, cy, rot, air) in ((118, 301, -20, True), (148, 290, 6, False), (178, 297, 24, False)):
        e, d = envelope(pw, cx, cy, 40, 27, rot, z=7.5, airmail=air)
        P['letters'].append(e)
        if d: P['air1'] = d
    P['parcel'] = pw.part(B(196, 312, 30, 26, 32), z=7.6, corners=True, smooth=False)
    pw.stroke(T([(196, 299), (196, 325)], 196, 312, 32), z=7.61, width=2.0, double=0)
    P['bag'] = pw.part([(100, 316), (196, 308), (204, 402), (108, 410)], z=8, corners=True, smooth=False)
    pw.stroke([(100, 318), (122, 344), (176, 342), (198, 312)], z=8.1, smooth=True)     # the flap that won't close
    pw.dot(150, 352, 3.0, z=8.2)
    P['arm'] = pw.limb([(268, 262), (296, 300), (316, 330)], 30, 26, z=9)
    P['held'], _ = envelope(pw, 342, 356, 38, 26, 18, z=9.5)
    hand, det = PenWash.hand(318, 334, 62, 28, 'fist')
    P['hand'] = pw.part(hand, z=10)
    pw.lines(det, z=10.1, width=2.2, double=0)
    # escaped letters, flapping away
    P['fly'] = []
    for (cx, cy, rot) in ((92, 226, -24), (64, 146, 16)):
        e, _ = envelope(pw, cx, cy, 36, 25, rot, z=20)
        P['fly'].append(e)
    pw.lines([[(108, 248), (120, 262), (136, 268)], [(118, 238), (132, 250), (146, 254)]], width=2.4, double=0)
    pw.lines([[(84, 166), (100, 176), (114, 178)], [(74, 172), (86, 186), (100, 192)]], width=2.4, double=0)
    pw.ground(120, 345, 490)
    pw.signature(388, 506, 7)
    return P


def postman_wash(pw, P, phase):
    if phase == 1:
        pw.wash(P['head'], 'skin'); pw.wash(P['ear'], 'skin'); pw.wash(P['hand'], 'skin')
        pw.bleed(P['head'], 252, 206, 16, 'rose', 0.65); pw.bleed(P['head'], 196, 214, 14, 'rose', 0.45)
        pw.wash([P['crown'], P['band']], 'cobalt', angle=10)
        pw.wash(P['coat'], 'cobalt', angle=80); pw.wash(P['arm'], 'cobalt', angle=60)
        pw.wash([P['legB'], P['legF']], 'grey', 0.95)
        pw.wash(P['bag'], 'tan', 1.05, angle=95); pw.wash(P['strap'], 'brown', 0.9)
    elif phase == 2:
        pw.wash(P['nose'], 'coral', 1.05)
        pw.wash(P['visor'], 'black', 1.1)
        pw.wash([P['shoeB'], P['shoeF']], 'black', 1.1)
        pw.wash(P['hair'], 'warmgrey', 0.7)
        pw.wash(P['stache'], 'bluegrey', 0.16, gaps=0, edge=0.6)
        pw.bleed(P['stache'], 292, 236, 22, 'bluegrey', 0.35)
        pw.wash(P['parcel'], 'ochre', 0.95)
        for d in P.get('air1', []): pw.wash(d, 'coral', 1.0, slip=(0.3, 0.8), soft=0.6, warp=0.3, gaps=0)
        pw.bleed(P['bag'], 186, 392, 30, 'brown', 0.5)
        pw.wash(O(236, 492, 112, 9), 'sage', 0.8, edge=0.6)
    elif phase == 3:
        pw.background_block(54, 76, 336, 318, 'yellow', 0.6, rough=6, angle=88)
    elif phase == 4:
        pw.glint(292, 190, 3.4); pw.glint(255, 98, 2.2)
        pw.spatter('yellow', 4, (36, 330, 120, 420), (1.4, 3.2), 0.8)


# ================================================================== card 2: granny, a flowerpot and the wrong customer
def granny(pw):
    P = {}
    P['bun'] = pw.part(O(152, 110, 25, 22), z=10.6)
    P['ear'] = pw.part(O(99, 208, 11, 15), z=9)
    P['pearl'] = pw.part(O(99, 229, 3.6, 3.6), z=9.5)
    P['head'] = pw.part(O(160, 194, 64, 68, egg=0.1), z=10)
    P['hair'] = pw.part(S([(97, 196), (98, 154), (124, 128), (160, 120), (200, 124), (222, 142), (226, 166), (204, 152),
                           (174, 146), (146, 154), (122, 172), (113, 202)], closed=True), z=11)
    pw.lines([[(130, 140), (150, 136), (168, 140)], [(186, 136), (204, 142)], [(108, 176), (116, 160)]], z=11.1, width=2.2, double=0)
    la, lb = pw.glasses(170, 198, 24, gap=54, z=12, temple=(108, 196))
    P['lenses'] = [la, lb]
    pw.brows([[(160, 165), (172, 161), (183, 164)], [(214, 162), (226, 159), (236, 163)]], z=13)
    pw.dot(176, 201, 4.0, z=13); pw.dot(229, 199, 4.0, z=13)
    P['nose'] = pw.part(O(207, 228, 10, 9), z=13)
    pw.stroke([(188, 247), (200, 253), (213, 247)], z=13, double=0)
    # body
    P['legB'] = pw.limb([(140, 440), (138, 474)], 15, 13, z=3)
    P['legF'] = pw.limb([(196, 440), (200, 474)], 15, 13, z=3)
    P['shoeB'] = pw.part(O(133, 480, 16, 8), z=3.5)
    P['shoeF'] = pw.part(O(207, 480, 16, 8, rot=6), z=3.5)
    P['skirt'] = pw.part(S([(106, 386), (232, 384), (250, 446), (90, 448)], closed=True, per=4), z=4)
    P['coat'] = pw.part(S([(110, 270), (150, 254), (196, 255), (222, 280), (232, 340), (238, 392), (160, 400),
                           (96, 392), (100, 330)], closed=True), z=5)
    pw.stroke([(196, 262), (206, 330), (212, 392)], z=5.2)
    for y in (300, 336, 370): pw.stroke(O(207 + (y - 300) * 0.08, y, 3.6, 3.4), z=5.3, closed=True, width=2.2, double=0)
    P['collar'] = pw.part(S([(146, 251), (172, 264), (199, 252), (192, 270), (172, 275), (152, 268)], closed=True), z=6)
    # the watering can, tipped forward to pour; she holds it by the top handle
    cx, cy, rot = 268, 334, 14
    P['can'] = pw.part(T(PenWash.rrect(236, 304, 300, 364, 7), cx, cy, rot), z=7, smooth=False)
    pw.stroke(T([(237, 318), (299, 318)], cx, cy, rot), z=7.1, width=2.4, double=0)
    P['mouth'] = pw.part(T(O(254, 304, 13, 4), cx, cy, rot), z=7.2, width=2.4)
    P['spout'] = pw.limb([tuple(T([(294, 352)], cx, cy, rot)[0]), (316, 318), (342, 294)], 10, 7, z=6.9, caps=(False, False))
    P['rose'] = pw.part(S([(336, 286), (350, 278), (362, 290), (354, 304), (342, 300)], closed=True, per=4), z=7.4)
    for (x, y) in ((352, 288), (356, 295), (349, 295)): pw.dot(x, y, 1.3, z=7.5)
    P['handle'] = pw.limb([tuple(T([(242, 306)], cx, cy, rot)[0]), (244, 276), (270, 264), (292, 280),
                           tuple(T([(294, 306)], cx, cy, rot)[0])], 7, 7, z=6.8, caps=(False, False))
    P['arm'] = pw.limb([(212, 272), (234, 284), (258, 274)], 28, 24, z=8)
    hand, det = PenWash.hand(258, 274, -14, 26, 'fist')
    P['hand'] = pw.part(hand, z=10)
    pw.lines(det, z=10.1, width=2.2, double=0)
    P['drops'] = []
    for (x, y, s) in ((356, 312, 1.0), (346, 322, 0.9), (362, 326, 0.85), (350, 335, 0.8), (342, 346, 0.75)):
        dp = [(x, y - 7 * s), (x + 4 * s, y + 1 * s), (x, y + 5 * s), (x - 4 * s, y + 1 * s)]
        P['drops'].append(pw.part(S(dp, closed=True, per=4), z=21, width=2.4))
    # the pot, the cat in it, the flower nobody is watering
    P['stem'] = pw.limb([(392, 410), (398, 372), (402, 346)], 5, 4, z=5.8, caps=(False, False))
    P['leaf'] = pw.part(S([(398, 384), (416, 370), (424, 376), (408, 388)], closed=True, per=4), z=5.9)
    petals = [O(402 + 11 * np.cos(a), 336 + 11 * np.sin(a), 8, 6, rot=np.degrees(a)) for a in np.linspace(0, 2 * np.pi, 6)[:-1] + 0.3]
    P['petals'] = [pw.part(p, z=6.4, width=2.4) for p in petals]
    P['bud'] = pw.part(O(402, 336, 5, 5), z=6.5, width=2.4)
    P['earL'] = pw.part([(314, 372), (318, 340), (338, 360)], z=4.4, corners=True, smooth=False)
    P['earR'] = pw.part([(350, 358), (370, 342), (374, 370)], z=4.4, corners=True, smooth=False)
    P['cat'] = pw.part(O(343, 388, 35, 32), z=4.5)
    pw.lines([[(326, 380), (335, 385), (326, 390)], [(362, 379), (353, 384), (362, 389)]], z=4.6, width=2.6, double=0, over=(0, 1))
    pw.lines([[(338, 397), (343, 400), (348, 397)], [(312, 394), (296, 391)], [(313, 400), (297, 403)],
              [(373, 393), (390, 389)], [(372, 399), (389, 402)]], z=4.6, width=2.0, double=0)
    pw.lines([[(318, 352), (322, 346)], [(366, 350), (370, 345)]], z=4.6, width=2.0, double=0)
    P['pot'] = pw.part([(296, 422), (396, 422), (384, 488), (308, 488)], z=5, corners=True, smooth=False)
    P['rim'] = pw.part([(286, 404), (406, 403), (407, 424), (285, 425)], z=6, corners=True, smooth=False)
    P['paws'] = [pw.part(O(322, 408, 10, 7), z=6.5, width=2.6), pw.part(O(364, 407, 10, 7), z=6.5, width=2.6)]
    pw.ground(70, 420, 488)
    pw.signature(412, 508, 7)
    return P


def granny_wash(pw, P, phase):
    if phase == 1:
        pw.wash(P['head'], 'skin'); pw.wash(P['ear'], 'skin'); pw.wash(P['hand'], 'skin')
        pw.bleed(P['head'], 132, 226, 15, 'rose', 0.7); pw.bleed(P['head'], 214, 222, 12, 'rose', 0.55)
        pw.wash(P['coat'], 'coral', angle=75); pw.wash(P['arm'], 'coral', angle=40)
        pw.wash(P['skirt'], 'teal', 0.95, angle=95)
        pw.wash(P['can'], 'sky', 1.05, angle=20); pw.wash([P['spout'], P['rose'], P['handle']], 'sky', 1.0)
        pw.wash(P['mouth'], 'cobalt', 0.6, slip=(0.5, 1.0))
        pw.wash(P['cat'], 'ochre'); pw.wash([P['earL'], P['earR']], 'ochre'); pw.wash(P['paws'], 'ochre')
        pw.wash([P['pot'], P['rim']], 'terracotta', 0.95, angle=92)
    elif phase == 2:
        pw.wash([P['hair'], P['bun']], 'bluegrey', 0.55)
        pw.wash(P['nose'], 'rose', 0.9)
        pw.wash([P['legB'], P['legF']], 'tan', 0.8)
        pw.wash([P['shoeB'], P['shoeF']], 'black', 1.1)
        pw.wash(P['drops'], 'cobalt', 0.8, slip=(0.5, 1.5), gaps=0.5)
        pw.wash(P['petals'], 'red', 1.0); pw.wash(P['bud'], 'yellow', 1.0)
        pw.wash([P['stem'], P['leaf']], 'green', 0.9)
        pw.bleed(P['cat'], 352, 404, 14, 'peach', 0.5)
        pw.bleed(P['pot'], 300, 470, 26, 'brown', 0.45)
        pw.wash(O(250, 490, 140, 8), 'sage', 0.75, edge=0.6)
    elif phase == 3:
        pw.background_block(52, 64, 338, 296, 'sky', 0.72, rough=6, angle=94)
    elif phase == 4:
        for (x, y) in ((162, 190), (216, 188)): pw.highlight([(x - 7, y + 3), (x - 3, y - 6)], 2.4, 0.85)
        pw.glint(203, 224, 2.0); pw.glint(248, 322, 2.4)
        pw.highlight([(250, 340), (254, 362)], 2.4, 0.6)


# ================================================================== card 3: a kid on a scooter, helmet two sizes too big
def scooter(pw):
    P = {}
    # scooter
    P['wheelB'] = pw.part(O(130, 392, 16, 16), z=7)
    P['wheelF'] = pw.part(O(362, 392, 16, 16), z=7)
    for x in (130, 362): pw.dot(x, 392, 3.0, z=7.1)
    P['deck'] = pw.part(S([(112, 368), (330, 366), (338, 380), (112, 382)], closed=True, per=3), z=8, nseg=2)
    P['fork'] = pw.part([(346, 372), (360, 374), (368, 394), (356, 396)], z=8.5, corners=True, smooth=False)
    P['stem'] = pw.limb([(354, 380), (350, 300), (344, 212)], 10, 9, z=9, caps=(False, False))
    P['bar'] = pw.limb([(330, 206), (346, 212), (360, 220)], 8, 8, z=12)
    P['grip'] = pw.part(O(330, 205, 7, 6), z=12.2, width=2.4)
    # kid
    P['legB'] = pw.limb([(232, 334), (198, 352), (166, 344)], 18, 15, z=7.5)
    P['shoeB'] = pw.part(O(154, 342, 18, 10, rot=-14), z=7.6)
    P['legF'] = pw.limb([(262, 334), (264, 350), (268, 362)], 18, 16, z=8.6)
    P['plaster'] = pw.part(B(265, 350, 16, 8, 14), z=8.7, corners=True, smooth=False, width=2.2)
    P['shoeF'] = pw.part(O(276, 365, 19, 9, rot=3), z=8.8)
    pw.stroke([(260, 366), (292, 366)], z=8.9, width=2.0, double=0)
    P['shorts'] = pw.part(S([(214, 306), (282, 302), (288, 340), (256, 345), (248, 332), (220, 342)], closed=True, per=4), z=9)
    P['shirt'] = pw.part(S([(206, 250), (254, 238), (284, 256), (284, 310), (220, 316), (206, 290)], closed=True), z=10)
    P['arm'] = pw.limb([(266, 260), (302, 254), (330, 214)], 13, 12, z=11)
    P['sleeve'] = pw.part(S([(252, 250), (276, 242), (286, 262), (266, 272)], closed=True, per=4), z=11.5)
    hand, det = PenWash.hand(330, 216, -64, 18, 'fist')
    P['hand'] = pw.part(hand, z=13)
    P['ear'] = pw.part(O(188, 216, 10, 12), z=11.5)
    P['head'] = pw.part(O(240, 204, 56, 48), z=12)
    P['helmet'] = pw.part(S([(144, 206), (146, 150), (180, 106), (232, 86), (286, 96), (318, 128), (328, 164),
                             (344, 184), (330, 198), (292, 202), (248, 206), (190, 216)], closed=True), z=14)
    P['stripe'] = pw.part(S([(178, 112), (228, 90), (258, 92), (234, 110), (198, 130), (166, 154), (158, 140)], closed=True), z=15, ink=False)
    P['vents'] = [pw.part(O(x, y, 11, 4.2, rot=a), z=15.1, width=2.4) for (x, y, a) in ((256, 116, 20), (282, 132, 36), (300, 156, 54))]
    pw.stroke([(206, 210), (226, 236), (256, 252)], z=13.5, width=2.4, double=0)
    pw.tufts(176, 216, n=3, length=11, spread=50, angle=160, z=11.8)
    pw.dot(256, 216, 3.9, z=13); pw.dot(282, 214, 3.9, z=13)
    P['nose'] = pw.part(O(297, 225, 7, 6), z=13, width=2.6)
    pw.stroke([(264, 239), (278, 237)], z=13, width=2.6, double=0)
    P['tongue'] = pw.part(O(280, 243, 5.5, 5, rot=20), z=13.2, width=2.4)
    # speed lines and dust
    pw.lines([[(44, 246), (104, 244)], [(30, 280), (86, 278)], [(54, 314), (110, 312)], [(80, 224), (112, 223)]], width=2.6, double=0)
    for (x, y, r) in ((92, 384, 13), (68, 374, 10), (50, 388, 8)):
        pw.stroke(O(x, y, r, r * 0.8, wob=0.25, seed=int(x)), closed=True, width=2.4)
    pw.ground(60, 420, 410)
    pw.signature(440, 426, 7)
    return P


def scooter_wash(pw, P, phase):
    if phase == 1:
        pw.wash(P['head'], 'skin'); pw.wash(P['ear'], 'skin'); pw.wash(P['hand'], 'skin')
        pw.wash([P['legB'], P['legF'], P['arm']], 'skin')
        pw.bleed(P['head'], 250, 234, 13, 'rose', 0.7)
        pw.wash(P['helmet'], 'cobalt', 1.0, angle=30)
        pw.wash([P['shirt'], P['sleeve']], 'yellow', 1.0, angle=70)
        pw.wash(P['shorts'], 'coral', 1.0)
        pw.wash([P['deck'], P['stem'], P['fork'], P['bar']], 'teal', 1.0, angle=5)
        pw.wash(P['stripe'], 'coral', 0.95, slip=(1, 2))
    elif phase == 2:
        pw.wash([P['wheelB'], P['wheelF']], 'grey', 1.0)
        pw.wash([P['shoeB'], P['shoeF']], 'black', 0.9)
        pw.wash(P['vents'] + [P['grip']], 'black', 1.2, slip=(0.3, 0.8))
        pw.wash(P['tongue'], 'coral', 1.0, slip=(0.4, 1.0), gaps=0.4); pw.wash(P['nose'], 'rose', 0.9, slip=(0.4, 1.0), gaps=0.4)
        pw.bleed(P['helmet'], 300, 176, 30, 'cobalt', 0.45)
        pw.wash(O(226, 408, 140, 8), 'warmgrey', 0.7, edge=0.6)
    elif phase == 3:
        pw.background_block(36, 80, 352, 352, 'sage', 0.85, rough=7, angle=0)
    elif phase == 4:
        pw.glint(204, 120, 2.6); pw.glint(295, 222, 1.6)


# ================================================================== card 4: the baker's baguette (and its first customer)
def baker(pw):
    P = {}
    pw.frame(42, 124, 380, 506)
    P['ear'] = pw.part(O(258, 240, 12, 15), z=9)
    P['head'] = pw.part(O(190, 236, 68, 66, egg=0.12), z=10)
    P['toque'] = pw.part(S([(130, 170), (112, 140), (120, 104), (148, 92), (162, 70), (192, 62), (216, 74), (242, 72),
                            (264, 94), (264, 128), (252, 162)], closed=True), z=14)
    pw.lines([[(160, 100), (166, 130)], [(208, 96), (212, 132)]], z=14.1, width=2.2, double=0)
    P['band'] = pw.part([(126, 158), (254, 152), (256, 178), (128, 184)], z=15, corners=True, smooth=False)
    la, lb = pw.glasses(156, 232, 22, gap=48, z=12, temple=(252, 230))
    P['lenses'] = [la, lb]
    pw.brows([[(146, 200), (158, 196), (168, 199)], [(194, 198), (206, 194), (216, 197)]], z=13)
    pw.dot(158, 235, 3.9, z=13); pw.dot(205, 233, 3.9, z=13)
    P['nose'] = pw.part(O(181, 260, 16, 14), z=13)
    P['stacheL'] = pw.limb([(178, 274), (156, 278), (138, 270), (134, 258)], 11, 3, z=14)
    P['stacheR'] = pw.limb([(184, 274), (206, 278), (224, 270), (229, 258)], 11, 3, z=14)
    pw.stroke([(168, 290), (181, 296), (194, 290)], z=13, double=0)
    # body: a round cobalt shirt, a white bib apron, short legs under it
    P['shoeL'] = pw.part(O(152, 500, 22, 9), z=2)
    P['shoeR'] = pw.part(O(240, 500, 22, 9), z=2)
    P['body'] = pw.part(O(198, 404, 104, 98, egg=0.08), z=5)
    for y in (330, 356): pw.dot(150, y, 2.6, z=5.1); pw.dot(248, y + 2, 2.6, z=5.1)
    P['apron'] = pw.part([(166, 326), (230, 324), (232, 372), (264, 384), (268, 488), (130, 490), (132, 386), (164, 374)],
                         z=6, corners=True, smooth=False)
    pw.lines([[(166, 328), (176, 302)], [(230, 326), (220, 302)], [(132, 386), (110, 392)], [(264, 384), (288, 390)]], z=6.1, width=2.4)
    pw.stroke([(182, 430), (180, 462), (224, 462), (226, 430)], z=6.2, width=2.6, smooth=False, corners=True)
    P['scarf'] = pw.part(S([(166, 298), (214, 298), (200, 318), (190, 312), (182, 320)], closed=True, per=4), z=8)
    P['armL'] = pw.limb([(110, 352), (108, 420), (128, 452)], 30, 26, z=9)
    P['armR'] = pw.limb([(288, 342), (292, 372), (244, 378)], 28, 24, z=9)
    # the baguette, hugged diagonally and poking out of the frame; a sparrow on the end
    a0, a1 = np.array([140.0, 490.0]), np.array([356.0, 104.0])
    P['loaf'] = pw.limb([tuple(a0), tuple((a0 + a1) / 2), tuple(a1)], 36, 32, z=12, caps=(True, True))
    cuts = []
    for t in np.linspace(0.10, 0.86, 7):
        cx, cy = a0 + (a1 - a0) * t
        cuts.append([(cx - 13, cy + 4), (cx + 2, cy - 7), (cx + 13, cy - 12)])
    P['cuts'] = cuts
    pw.lines(cuts, z=12.1, width=2.4, double=0, over=(0, 1))
    hl, d1 = PenWash.hand(128, 452, -6, 30, 'fist')
    hr, d2 = PenWash.hand(244, 378, 186, 30, 'fist', flip=True)
    P['hands'] = [pw.part(hl, z=13), pw.part(hr, z=13)]
    pw.lines(d1 + d2, z=13.1, width=2.2, double=0)
    P['tail'] = pw.part([(384, 70), (406, 56), (404, 70)], z=19.5, corners=True, smooth=False, width=2.6)
    P['bird'] = pw.part(S([(352, 76), (362, 64), (382, 64), (394, 76), (384, 88), (360, 90)], closed=True), z=20)
    P['bhead'] = pw.part(O(350, 76, 11, 10), z=20.5)
    P['beak'] = pw.part([(340, 80), (343, 92), (348, 84)], z=20.6, corners=True, smooth=False, width=2.2)
    pw.dot(348, 73, 2.2, z=21)
    pw.stroke([(368, 72), (382, 74), (388, 82)], z=20.6, width=2.2, double=0)
    pw.lines([[(366, 90), (364, 96)], [(374, 90), (374, 96)]], z=19, width=2.0, double=0)
    P['crumbs'] = [pw.part(O(x, y, 2.6, 2.2), z=21, width=1.8) for (x, y) in ((316, 116), (306, 132), (304, 150))]
    pw.signature(392, 528, 7)
    return P


def baker_wash(pw, P, phase):
    if phase == 1:
        pw.wash(P['head'], 'skin'); pw.wash(P['ear'], 'skin'); pw.wash(P['hands'], 'skin')
        pw.bleed(P['head'], 140, 262, 16, 'rose', 0.65); pw.bleed(P['head'], 226, 258, 14, 'rose', 0.55)
        pw.wash(P['apron'], 'cobalt', 0.95, angle=80)
        pw.wash(P['loaf'], 'ochre', 1.05, angle=62)
    elif phase == 2:
        pw.wash(P['nose'], 'coral', 1.05)
        pw.wash([P['stacheL'], P['stacheR']], 'black', 0.9, slip=(0.5, 1.2))
        pw.wash(P['scarf'], 'coral', 1.0)
        pw.wash([P['shoeL'], P['shoeR']], 'black', 1.0)
        pw.bleed(P['loaf'], 318, 150, 60, 'brown', 0.55); pw.bleed(P['loaf'], 150, 450, 40, 'brown', 0.4)
        pw.wash([P['bird'], P['bhead'], P['tail']], 'brown', 0.75); pw.wash(P['beak'], 'yellow', 1.0)
        pw.bleed(P['bird'], 364, 62, 9, 'warmgrey', 0.8)
        pw.wash(P['crumbs'], 'ochre', 1.0, slip=(0.3, 0.8))
        pw.wash([P['toque'], P['band']], 'bluegrey', 0.20, gaps=0, edge=0.5)
        pw.bleed(P['toque'], 250, 120, 30, 'bluegrey', 0.4)
        pw.wash([P['body'], P['armL'], P['armR']], 'bluegrey', 0.13, gaps=0, edge=0.6)
        pw.bleed(P['body'], 286, 420, 40, 'bluegrey', 0.4); pw.bleed(P['armR'], 292, 380, 20, 'bluegrey', 0.4)
    elif phase == 3:
        pw.background_block(46, 128, 376, 502, 'teal', 0.8, rough=4, corner=6, halo=3.5, angle=92)
    elif phase == 4:
        for c in P['cuts']: pw.highlight([(x + 2, y + 3) for (x, y) in c], 2.2, 0.8)
        pw.glint(174, 254, 3.0)
        for k in range(3): pw.highlight([(200 + 9 * k, 400 + 4 * k), (206 + 9 * k, 420 + 3 * k)], 3.4, 0.55)
        for (x, y) in ((150, 224), (198, 222)): pw.highlight([(x - 6, y + 2), (x - 2, y - 6)], 2.2, 0.85)
        pw.spatter('coral', 4, (300, 440, 410, 540), (0.8, 2.0))


# ================================================================== the photo
CARDS = [  # (cx, cy, w, h, rot, corner, draw, wash)
    (250, 424, 420, 540, -4.0, 3.0, postman, postman_wash),
    (706, 494, 440, 530, 2.6, 9.0, granny, granny_wash),
    (1172, 404, 470, 450, -2.2, 14.0, scooter, scooter_wash),
    (1652, 470, 420, 550, 3.4, 4.0, baker, baker_wash),
]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'penwash_neighbours.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:16s} {time.time() - T0:5.1f}s')) if os.environ.get('PW_TIMING') else (lambda name: None)
    pw = PenWash(1920, 1080, seed=21, keep_stages=bool(stages), stages_dir=stages)
    pw.table('oak')
    pw.stage('table')
    cards, parts = [], []
    for k, (cx, cy, w, h, rot, corner, draw, _) in enumerate(CARDS):
        cards.append(pw.card(cx, cy, w, h, rot=rot, corner=corner, seed=100 + k))
    pw.stage('cards')
    for k, c in enumerate(cards):
        pw.use(c)
        parts.append(CARDS[k][6](pw))
        pw.ink()
        tick(f'ink {k}')
        if k in (1, 3): pw.stage(f'ink_{k - 1}{k}')
    for phase, name in ((1, 'washes'), (2, 'more_washes'), (3, 'background'), (4, 'details')):
        for k, c in enumerate(cards):
            pw.use(c)
            CARDS[k][7](pw, parts[k], phase)
        tick(name)
        pw.stage(name)
    pw.pen(706, 868, 166, length=640, r=16)
    pw.water_brush(1052, 744, 19, length=600, r=24, cap=(1700, 960, -14))
    tick('tools')
    img = pw.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out)


if __name__ == '__main__':
    main()
