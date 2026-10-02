"""Example (spray-paint stencil): 放风筝 · Hold On — a kid flying a kite, sprayed on a board-marked concrete wall.

The wind comes from the right. A small kid in a puffer jacket, beanie and knitted scarf leans back against the pull,
front heel dug in, holding a round kite reel; the two tails of the scarf and a few leaves fly ahead of him toward
the kite. The string (sprayed freehand with a skinny cap) sags up across the wall to a red diamond kite high on the
left, its bow tail streaming downwind; three swallows from one little stencil ride the same wind. HOLD ON is sprayed
in stencil letters with bridged counters. The wall had a past: a grey council buff over an old blue tag that still
ghosts through, and a pink tag half taken off by a pressure washer.

How it was made, in order: the wall -> old graffiti -> the kid in three cards, light -> grey -> black (each card
a few px off, every island held by bridges) -> the kite in red, then dark red -> string and tail freehand; bows,
swallows and leaves from small reusable cards turned to fit -> lettering. No image model.
python3 stencil_kite.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from stencil import Stencil, shade_side, BLACK, WHITE, GREY, RED
from core import spline

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'stencil_kite.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

GROUND = 1000
KID = (1420, GROUND - 6)                  # the kid's feet, wall px
KS = 1.36                                 # the kid's design units -> px
LIGHT = (-1.0, -0.9)                      # the photo the stencil was cut from was lit from the upper left


def kid_design(c):
    """the kid, facing left, leaning back on the string. Returns the three tone plates (masks) and where the
    string leaves the reel. Parts are drawn back to front; each plate only gets what is visible."""
    U = np.maximum
    PIV, LEAN, DROP = (30.0, -172.0), np.radians(9), 14.0       # the upper body leans back about the hips

    def R(*pts):
        out = []
        for x, y in pts:
            dx, dy = x - PIV[0], y - PIV[1]
            out.append((PIV[0] + dx * np.cos(LEAN) - dy * np.sin(LEAN), PIV[1] + dx * np.sin(LEAN) + dy * np.cos(LEAN) + DROP))
        return out if len(out) > 1 else out[0]

    def above(p0, p1):
        """the side of line p0 -> p1 that is up (screen y smaller)"""
        (a, b) = c.P([p0, p1])
        d = b - a
        cr = (d[0] * (c.YY - a[1]) - d[1] * (c.XX - a[0])) / (np.hypot(*d) + 1e-6)
        return np.clip(-cr + 0.5, 0, 1).astype(np.float32)

    def hide(part, *front):
        v = part.copy()
        for f in front: v *= 1 - f
        return v

    # --- legs: front leg braced straight forward, rear leg bent under the weight
    leg_f = U(c.capsule((14, -176), (-28, -102), 22, 17), c.capsule((-28, -102), (-68, -32), 17, 14))
    leg_r = U(c.capsule((42, -180), (82, -104), 23, 18), c.capsule((82, -104), (54, -32), 18, 14))
    leg_f = U(leg_f, c.ellipse((-68, -34), 16, 10, rot=-35))
    leg_r = U(leg_r, c.ellipse((54, -32), 16, 9, rot=15))
    # --- sneakers: front one on its heel with the toe up; rear one flat, pushing
    shoe_f = c.poly([(-56, -2), (-54, -22), (-64, -36), (-86, -44), (-110, -50), (-124, -44), (-122, -30),
                     (-102, -18), (-76, -4)], smooth=True)
    shoe_r = c.poly([(78, -2), (78, -22), (66, -32), (46, -34), (26, -26), (8, -16), (6, -4), (36, 0)], smooth=True)
    sole_f = c.stroke([(-56, -4), (-80, -8), (-106, -22), (-124, -36)], 7, 6) * shoe_f
    sole_r = c.stroke([(78, -3), (40, -2), (6, -3)], 7, 7) * shoe_r
    shoes = U(shoe_f, shoe_r)
    # --- the upper body
    torso = c.poly(R((-4, -184), (-9, -226), (-3, -266), (22, -304), (58, -316), (84, -300), (90, -256),
                     (86, -214), (76, -180), (36, -170)), smooth=True)
    sleeve_f = U(c.capsule(*R((66, -298), (30, -268)), 17, 15), c.capsule(*R((30, -268), (-16, -292)), 15, 13))
    sleeve_n = U(c.capsule(*R((58, -292), (14, -254)), 19, 17), c.capsule(*R((14, -254), (-24, -272)), 17, 15))
    hand_f = c.ellipse(R((-28, -296)), 11, 10)
    hand_n = c.ellipse(R((-36, -276)), 12, 11)
    neck = c.capsule(*R((54, -318), (60, -336)), 12)
    skull = c.ellipse(R((64, -366)), 37, 36)
    face = c.ellipse(R((44, -352)), 25, 21, rot=-25 - 9)
    nose = c.ellipse(R((15, -361)), 7, 5.5)
    chin = c.ellipse(R((40, -336)), 12, 9)
    head = U(U(skull, face), U(U(nose, chin), neck))
    ear = c.ellipse(R((72, -360)), 8, 10, rot=-15 - 9)
    # beanie: a dome above the brim line, a ribbed turn-up, a pom-pom
    b0, b1 = R((24, -398)), R((108, -374))
    dome = c.ellipse(R((70, -394)), 41, 33, rot=-14 - 9) * above(b0, b1)
    band = c.stroke(R((22, -394), (64, -384), (110, -370)), 15, 15) * c.ellipse(R((66, -384)), 47, 42)
    pc = R((100, -422))
    pom = c.poly([(pc[0] + 15 * (1 + 0.2 * (i % 2)) * np.cos(a), pc[1] + 15 * (1 + 0.2 * (i % 2)) * np.sin(a))
                  for i, a in enumerate(np.linspace(0, 2 * np.pi, 22, endpoint=False))], facet=0.5)
    hat = U(dome, band)
    hair = U(c.poly(R((98, -360), (112, -348), (101, -347), (108, -336), (93, -342), (88, -352))),
             c.poly(R((24, -384), (14, -376), (26, -378))))
    # --- scarf: wound round the neck, two tails streaming forward on the wind (they do not lean with the body)
    wrap = c.stroke(R((30, -320), (52, -330), (82, -324)), 24, 22)
    n0 = R((36, -324))
    tails = [([(0, 0), (-20, -14), (-42, -10), (-64, -24), (-86, -20), (-108, -34), (-126, -30)],
              [15, 12, 15, 11, 14, 11, 13]),
             ([(-2, 4), (-20, 6), (-40, 0), (-58, 8), (-76, 4)], [13, 10, 13, 10, 11])]
    tail1 = np.zeros_like(wrap); fringe = np.zeros_like(wrap); stripes = np.zeros_like(wrap)
    for pts, widths in tails:
        path = [(n0[0] + dx, n0[1] + dy) for dx, dy in pts]
        sp = spline(np.array(path, np.float32), 12)
        wv = np.interp(np.linspace(0, len(widths) - 1, len(sp)), np.arange(len(widths)), widths)
        band = np.zeros_like(wrap)
        for i in range(len(sp) - 1):
            band = U(band, c.capsule(sp[i], sp[i + 1], wv[i] / 2, wv[i + 1] / 2))
        tail1 = U(tail1, band)
        e = path[-1]
        for k in range(4):                                          # fringe: strands fanning out, not touching
            ang = np.radians(160 + k * 14)
            fringe = U(fringe, c.stroke([(e[0] + 2, e[1] - 3 + k * 2.2),
                                         (e[0] + 2 + 14 * np.cos(ang), e[1] - 3 + k * 2.2 - 14 * np.sin(ang))], 2.4, 1.5,
                                        smooth=False))
        Ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])
        for d in np.arange(26, Ls[-1] - 10, 22):                    # knitted stripes across the tail
            i = int(np.searchsorted(Ls, d)); t = sp[min(i + 1, len(sp) - 1)] - sp[max(i - 1, 0)]
            t = t / (np.hypot(*t) + 1e-6); nx, ny = -t[1], t[0]
            q = sp[i]
            stripes = U(stripes, c.stroke([(q[0] - nx * 12, q[1] - ny * 12), (q[0] + nx * 12, q[1] + ny * 12)], 6,
                                          smooth=False) * band)
    scarf = U(U(wrap, tail1), fringe)
    # --- the reel in the near hand: a ring with six spokes (the gaps between them need bridges)
    RC = R((-64, -286)); RR = 25
    reel = c.ring(RC, RR, RR - 6)
    for a in np.radians(np.arange(15, 375, 60)):
        reel = U(reel, c.capsule(RC, (RC[0] + RR * np.cos(a), RC[1] + RR * np.sin(a)), 2.6))
    reel = U(reel, c.ellipse(RC, 7))
    reel = U(reel, c.capsule(RC, R((-38, -276)), 4))                         # the handle, into the fist

    # visibility, back to front: far arm, rear leg, front leg, shoes, torso, head, hat, near arm, scarf, reel
    v_sleeve_f = hide(sleeve_f, torso, sleeve_n, hand_n, scarf, reel)
    v_hand_f = hide(hand_f, sleeve_n, hand_n, reel, scarf)
    v_leg_r = hide(leg_r, leg_f, shoes, torso)
    v_leg_f = hide(leg_f, shoes, torso)
    v_torso = hide(torso, sleeve_n, scarf)
    v_head = hide(head, hat, scarf)
    v_hat = hide(U(hat, pom), scarf)
    v_sleeve_n = hide(sleeve_n, hand_n, reel)
    v_hand_n = hide(hand_n, reel)
    v_scarf = hide(scarf, reel)
    legs = U(v_leg_f, v_leg_r)
    jacket = U(v_torso, U(v_sleeve_n, v_sleeve_f))
    body = U(U(U(leg_f, leg_r), shoes), U(U(torso, sleeve_n), U(sleeve_f, U(hand_n, hand_f))))
    body = U(body, U(U(head, hat), U(pom, U(scarf, hair))))

    # ---------------- plate 1: light -- the whole figure, so the busy wall drops out behind it
    light = body
    # ---------------- plate 2: grey -- jacket (its lit rim stays light), hat, trousers, shadow sides
    grey = jacket * (1 - shade_side(torso, (-LIGHT[0], -LIGHT[1]), 6, soft=1.2))
    grey = U(grey, v_hat * (1 - pom))
    grey = U(grey, legs)
    grey = U(grey, shade_side(head, LIGHT, 20, soft=2, wobble=0.4, seed=1) * v_head)
    grey = U(grey, shade_side(U(hand_n, hand_f), LIGHT, 7) * U(v_hand_n, v_hand_f))
    grey = U(grey, shade_side(wrap, LIGHT, 8, soft=1.5, wobble=0.5, seed=2) * v_scarf * (1 - tail1))
    grey = U(grey, stripes * v_scarf)
    grey = U(grey, c.stroke(R((40, -326), (66, -334), (86, -326)), 4) * wrap)          # a fold in the wrap
    grey = U(grey, ear * v_head)
    grey = U(grey, shade_side(shoes, LIGHT, 10))
    grey = U(grey, shade_side(pom, LIGHT, 9) * v_hat)
    # ---------------- plate 3: black -- the deep shadows, seams, features, the reel
    black = shade_side(torso, LIGHT, 34, soft=3.0, wobble=0.35, seed=3) * v_torso
    black = U(black, shade_side(sleeve_f, LIGHT, 40) * v_sleeve_f)              # the far arm is in shadow
    black = U(black, shade_side(sleeve_n, LIGHT, 9, soft=1.5) * v_sleeve_n)
    seams = np.zeros_like(torso)
    for k in range(4):                                                          # puffer quilting
        y = -202 - k * 27
        seams = U(seams, c.stroke(R((-14, y + 6), (30, y - 2), (104, y - 12)), 3.2))
    black = U(black, seams * v_torso)
    black = U(black, c.stroke(R((52, -286), (14, -248), (-20, -262)), 3.0) * v_sleeve_n)   # elbow crease
    black = U(black, shade_side(leg_f, LIGHT, 18, soft=2.0) * v_leg_f)
    black = U(black, shade_side(leg_r, LIGHT, 44, soft=2.0) * v_leg_r)
    black = U(black, U(sole_f, sole_r))
    black = U(black, c.stroke([(-84, -42), (-92, -30)], 2.6) * shoe_f)                # laces
    black = U(black, c.stroke([(-96, -46), (-104, -34)], 2.6) * shoe_f)
    black = U(black, c.stroke([(40, -30), (46, -20)], 2.6) * shoe_r)
    black = U(black, shade_side(hat, LIGHT, 18, soft=2.0, wobble=0.3, seed=5) * v_hat * (1 - pom))
    for k in range(10):                                                         # ribbing of the turn-up
        q0 = R((28 + k * 8.2, -390 + k * 8.2 * 0.29 + 6)); q1 = R((30 + k * 8.2, -390 + k * 8.2 * 0.29 - 7))
        black = U(black, c.stroke([q0, q1], 2.0, smooth=False) * band * v_hat)
    black = U(black, hair)
    black = U(black, c.ellipse(R((33, -366)), 4.0, 5.4, rot=-20) * v_head)     # eye, looking up at the kite
    black = U(black, c.stroke(R((26, -377), (34, -380), (43, -378)), 2.6) * v_head)      # brow
    black = U(black, c.poly(R((21, -347), (34, -343), (28, -337))) * v_head)  # open mouth
    black = U(black, c.ellipse(R((17, -356)), 2.0, 1.4) * v_head)              # nostril
    black = U(black, c.stroke(R((72, -366), (76, -360), (72, -354)), 2.4) * ear * v_head)
    black = U(black, shade_side(head, LIGHT, 7, soft=1.0) * v_head)
    grey = U(grey, c.stroke(R((46, -330), (70, -334), (92, -324)), 5) * wrap * v_scarf)    # under the chin
    black = U(black, reel)
    black = U(black, c.stroke(R((-42, -282), (-32, -286)), 2.2) * v_hand_n)    # knuckles
    black = U(black, shade_side(pom, LIGHT, 3) * v_hat)
    string_from = (RC[0] - RR * 0.7, RC[1] - RR * 0.7)
    return dict(light=light, grey=grey, black=black, string_from=string_from)


def kite_design(c):
    """a diamond kite: four panels between two spars; the spars are the bridges of the red card"""
    T, Lf, R, B = (0, -150), (-92, -46), (92, -46), (0, 120)
    body = c.poly([T, R, B, Lf], facet=0.35)
    spar = np.maximum(c.capsule(T, B, 3.4), c.capsule(Lf, R, 3.4))
    red = body * (1 - spar)
    # the right-hand panels in shade (the kite bows into the wind)
    shade = np.clip(c.poly([T, R, B, (4, -46)]) - spar * 1.4, 0, 1) * body
    return dict(red=red, shade=shade, cross=(0, -46), tail=B)


def bow_design(c):
    """one little bow for the tail (reused)"""
    return np.maximum(np.maximum(c.poly([(0, 0), (-16, -9), (-16, 9)]), c.poly([(0, 0), (16, -9), (16, 9)])),
                      c.ellipse((0, 0), 4.5))


def leaf_design(c):
    """a small leaf on the wind; its midrib is a bridge that runs right through it"""
    blade = c.poly([(-15, 0), (-7, -6.5), (6, -6), (14, 0), (6, 6), (-7, 6.5)], smooth=True)
    stem = c.stroke([(13, 0), (21, 3)], 2.2, 1.6, smooth=False)
    m = np.maximum(blade, stem)
    return m * (1 - c.stroke([(-20, 0), (16, 0)], 1.8, smooth=False))


def bird_design(c):
    """a swallow heading left: slim body, swept-back crescent wings (one up, one down), long forked tail"""
    U = np.maximum
    body = c.poly([(-30, 0), (-23, -4), (-8, -5), (10, -3), (16, 0), (10, 4), (-8, 5), (-23, 4)], smooth=True)
    tail = c.poly([(8, -2), (44, -10), (24, 0), (46, 12), (8, 3)])
    up = c.poly([(-7, -3), (-3, -18), (5, -32), (21, -44), (13, -29), (9, -15), (5, -2)], smooth=True)
    down = c.poly([(-5, 3), (1, 13), (13, 24), (8, 12), (5, 3)], smooth=True)
    return U(U(body, tail), U(up, down))


s = Stencil(1920, 1080, seed=23)

# ---- the wall: board-marked concrete, tie holes, weather; the pavement
s.wall(ground=GROUND)
s.pavement()
s.stage('wall')

# ---- what was here before: a faded tag washed half off, a roller buff over another
s.freehand([(96, 668), (110, 600), (140, 655), (150, 610), (180, 650), (196, 596), (214, 660), (232, 616),
            (268, 640), (300, 606), (322, 652), (360, 628)], '#b98293', width=11, coats=1.3, wash=0.7, per=12)
s.freehand([(120, 690), (220, 682), (340, 694)], '#b98293', width=7, coats=1.1, wash=0.7)
s.freehand([(1430, 160), (1470, 110), (1500, 190), (1540, 120), (1590, 200), (1640, 130), (1700, 170)],
           '#3d6fa8', width=14, coats=2.0, drips=0.0)
s.buff(1390, 96, 1770, 290)
s.stage('history')

# ---- the kid: three cards, light -> grey -> black
box = (KID[0] - 200 * KS, KID[1] - 480 * KS, KID[0] + 175 * KS, KID[1] + 4)
cards = {}
for name in ('light', 'grey', 'black'):
    cards[name] = s.card(*box, origin=KID, scale=KS, tape=[(0, 0), (1, 0), (0, 1), (1, 1)])
plates = kid_design(cards['light'])
for name in ('light', 'grey', 'black'):
    cards[name].cut(plates[name]).bridges(width=3.0)
s.spray(cards['light'], WHITE, coats=3.0, misreg=0.0, drips=0.06)
s.stage('card_light', card=cards['light'])
s.stage('light')
s.spray(cards['grey'], GREY, coats=2.0, misreg=2.0, drips=0.2)
s.stage('grey')
s.spray(cards['black'], BLACK, coats=2.0, misreg=2.0, drips=0.7)
s.stage('card_black', card=cards['black'])
s.stage('kid')

# ---- the kite: red, then the shaded panels in dark red
KITE, KK = (560, 260), 0.85
kc = s.card(KITE[0] - 150, KITE[1] - 200, KITE[0] + 150, KITE[1] + 170, origin=KITE, scale=KK)
kd = kite_design(kc)
kc.cut(kd['red'])
ks = s.card(KITE[0] - 150, KITE[1] - 200, KITE[0] + 150, KITE[1] + 170, origin=KITE, scale=KK)
ks.cut(kd['shade'])
s.spray(kc, RED, coats=2.0, misreg=0.0, drips=0.8, angle=-30)
s.spray(ks, '#8c1c16', coats=1.6, misreg=1.5, drips=0.4)
s.stage('kite')

# ---- string and tail, freehand with a skinny cap; bows and birds from little reusable cards
sf = plates['string_from']
x0, y0 = KID[0] + sf[0] * KS, KID[1] + sf[1] * KS
x1, y1 = KITE[0] + kd['cross'][0] * KK, KITE[1] + kd['cross'][1] * KK
sag = [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 90 * 4 * t * (1 - t) * (1 - 0.3 * t)) for t in np.linspace(0, 1, 9)]
s.freehand(sag, BLACK, width=2.8, coats=1.9, speed=[0.6, 1.2, 1.4, 1.4, 1.3, 1.2, 1.2, 1.0, 0.8], drips=0.8)
tb = (KITE[0] + kd['tail'][0] * KK, KITE[1] + kd['tail'][1] * KK)
tail = [tb, (tb[0] - 20, tb[1] + 60), (tb[0] - 70, tb[1] + 100), (tb[0] - 110, tb[1] + 90),
        (tb[0] - 160, tb[1] + 130), (tb[0] - 200, tb[1] + 200)]
s.freehand(tail, BLACK, width=2.6, coats=1.6, drips=0.3, spits=1)
bow = s.card(-60, -50, 60, 50, origin=(0, 0))
bow.cut(bow_design(bow))
tp = spline(np.array(tail, np.float32), 20)
for k, idx in enumerate(np.linspace(0.18, 0.95, 5) * (len(tp) - 1)):
    i = int(idx)
    tx, ty = tp[min(i + 2, len(tp) - 1)] - tp[max(i - 2, 0)]
    s.spray(bow, RED, coats=1.8, cone=10, at=(tp[i][0], tp[i][1]), rot=np.degrees(np.arctan2(-ty, tx)) + 90,
            misreg=0.5, drips=0.2)
bird = s.card(-80, -80, 80, 80, origin=(0, 0))
bird.cut(bird_design(bird))
for bx, by, br in [(860, 160, 6), (960, 236, -4), (790, 318, 12)]:
    s.spray(bird, BLACK, coats=1.8, cone=12, at=(bx, by), rot=br, misreg=0.5, drips=0.2)
leaf = s.card(-50, -40, 50, 40, origin=(0, 0))
leaf.cut(leaf_design(leaf))
for lx, ly, lr in [(1150, 470, 30), (1040, 610, -20), (1210, 790, 70), (930, 520, 110)]:
    s.spray(leaf, BLACK, coats=2.0, cone=10, at=(lx, ly), rot=lr, misreg=0.5, drips=0.0)
s.stage('string')

# ---- lettering under it all
tc = s.card(80, 800, 640, 960, origin=(80, 800))
tc.cut(tc.text('HOLD ON', 280, 130, 118, anchor='ms', spacing=6))
s.spray(tc, BLACK, coats=2.0, misreg=0.0, drips=1.0, wet=2.2)

s.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
