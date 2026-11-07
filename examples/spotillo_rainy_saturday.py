"""Example (flat spot illustration): 雨天的星期六 · A Rainy Saturday -- five small everyday vignettes on white.

Two people's rainy Saturday, told as Japanese-style spot illustrations floating on a white sheet: going out under a
red umbrella with a leek in the tote bag and stepping into a puddle; stirring soup in a red pot, steam curling up;
crouching to set down a red bowl for a black cat that has just noticed; reading in an armchair with a red mug
steaming on the stool; and an afternoon nap on the sofa, red socks up on the armrest, the book tented on the chest,
the cat curled up below. Flat opaque shapes with hand-cut edges and a faint print grain, a restrained palette (navy,
powder blue, mustard, green, olive, greys, near-black hair) with one red thing in every vignette, white folds cut
into the clothes, faces left as paper with a profile line and a dot eye, little hand marks for steam, rain, z's and
surprise. No ground, no background.

Drawn vignette by vignette, the little hand marks (rain, steam, '!', z's) last; --stages writes a snapshot after
each vignette and after the marks. --layout wide lays the same five vignettes out on a 1920 x 1080 sheet (used for
the draw-on GIF). No image model.
python3 spotillo_rainy_saturday.py [out.jpg] [--stages DIR] [--layout sheet|wide]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from spotillo import SpotIllustration

P1 = dict(hair_style='bob', strands=2)                 # the one with the bob
P2 = dict(hair_style='short', strands=2)               # the one with short hair
MARKS = []                                             # the little hand marks, drawn last


def at(x, y, u, f=1):
    return lambda a, b: np.array([x + a * u * f, y + b * u])


# ---------------------------------------------------------------- 1. out under the red umbrella
def going_out(s, x, y, u):
    P = at(x, y, u)
    s.shape(s.ellipse(*P(0.95, 0.03), 0.95 * u, 0.13 * u), 'powder_light', wobble=1.6)       # the puddle
    hand = P(0.66, -3.66)
    tilt = 6.0
    d = np.array([-np.sin(np.deg2rad(tilt)), np.cos(np.deg2rad(tilt))])
    top = hand + np.array([0.27 * u, 0]) - d * 2.95 * u
    R = 1.5 * u
    canopy = {}

    def tote():
        sh = P(-0.22, -4.3)
        bag_c = P(-0.72, -2.1)
        # what sticks out of the bag first: a baguette and a leek (white stalk, green leaves)
        bt = bag_c + np.array([0.3 * u, -0.6 * u])
        Bq = s.shape(s.tube([bt, bt + np.array([0.28 * u, -1.25 * u])], 0.26 * u, ('flat', 'round'), smooth=False),
                     'wood_light', wobble=0.6)
        for t in (0.35, 0.6, 0.85):
            c = bt + np.array([0.28 * u, -1.25 * u]) * t
            s.line([c + np.array([-0.08 * u, 0.02 * u]), c + np.array([0.09 * u, -0.04 * u])], 2.2 * s.k, 'wood', clip=Bq)
        lk = bag_c + np.array([-0.08 * u, -0.7 * u])
        top_w = lk + np.array([-0.16 * u, -0.85 * u])
        for a, L, col in ((-0.55, 0.85, 'green'), (-0.2, 1.0, 'olive'), (0.15, 0.75, 'green')):
            tip = top_w + np.array([np.sin(a), -np.cos(a)]) * L * u
            s.shape(s.tube([top_w, (top_w + tip) / 2 + np.array([-0.05 * u, 0]), tip], [0.17 * u, 0.15 * u, 0.03 * u],
                           ('round', 'round')), col, wobble=0.6)
        s.shape(s.tube([lk, top_w], [0.22 * u, 0.18 * u], ('flat', 'round'), smooth=False), 'paper', wobble=0.4)
        s.line([lk + np.array([-0.08 * u, -0.1 * u]), top_w + np.array([-0.05 * u, 0.2 * u])], 1.8 * s.k, 'sage', taper=0.3)
        Bg = s.bag(bag_c[0], bag_c[1] + 0.55 * u, 1.0 * u, 1.15 * u, 'cream', handles=False)
        s.fold([bag_c + np.array([-0.3 * u, 0.35 * u]), bag_c + np.array([-0.18 * u, 0.12 * u])], 2.2 * s.k, clip=Bg)

    def umbrella():
        # the tote's strap over the shoulder, behind the arm and down to the bag
        s.line([P(-0.02, -4.46), P(-0.32, -4.2), P(-0.5, -3.6), P(-0.55, -3.05)], 0.1 * u, 'cream', taper=0.0, wobble=0.4)
        canopy['P'] = s.umbrella(top[0], top[1], R, tilt, 'red', handle_len=(2.95 * u + 0.5 * u) / R)

    s.person(x, y, u, 1, 'walk', dict(P1, top='navy', bottom='grey', shoes='paper', hand_f=None, hand_n=('grip', -6)),
             hooks=dict(arm_near=tote, hand_near=umbrella),
             rel=dict(hem_b=(-0.6, -1.95), hem_f=(0.66, -1.98), elbow_n=(0.06, -3.25), wrist_n=hand_rel(hand, x, y, u),
                      elbow_f=(0.55, -3.5), wrist_f=(0.6, -2.7), head=(0.24, -5.18)))
    s.fold([P(0.18, -2.5), P(0.25, -2.15)], 2.4 * s.k)

    def marks():
        left = top[0] - R * 1.02; right = top[0] + R * 1.02; rim = top[1] + R * 0.45
        r = np.random.default_rng(7)
        for _ in range(60):
            px, py = r.uniform(x - 2.1 * u, x + 3.9 * u), r.uniform(y - 8.0 * u, y - 0.1 * u)
            if left - 0.1 * u < px < right + 0.25 * u and py > top[1] - R * 0.5: continue
            if x - 1.5 * u < px < x + 0.2 * u and py > y - 5.4 * u: continue          # the bag, the leek, the legs
            if abs(px - top[0]) < R * 1.2 and abs(py - (top[1] - R * 0.1)) < R * 0.6: continue
            L = 0.32 * u * r.uniform(0.6, 1.25)
            s.line([(px, py), (px - 0.28 * L, py + L)], 2.6 * s.k, 'slate', taper=0.3, wobble=0.1, smooth=False)
        for a in (-150, -120, -60, -30):
            q = P(0.95, -0.05) + np.array([np.cos(np.deg2rad(a)) * 0.75 * u, np.sin(np.deg2rad(a)) * 0.32 * u])
            q2 = q + np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))]) * 0.22 * u
            s.line([q, q2], 2.6 * s.k, 'slate', taper=0.2, wobble=0.1, smooth=False)
    MARKS.append(marks)


def hand_rel(hand, x, y, u, f=1):
    return ((hand[0] - x) / (u * f), (hand[1] - y) / u)


# ---------------------------------------------------------------- 2. soup on the stove
def soup(s, x, y, u):
    P = at(x, y, u)
    s.stove(*P(0.62, 0)[:1], P(3.1, 0)[0], y, 2.85 * u, 'grey_light')
    s.shape(s.rrect(*P(2.45, -3.35), *P(2.85, -2.85), 0.05 * u), 'paper', wobble=0.5)            # a jar
    J = s.shape(s.rrect(*P(2.45, -3.35), *P(2.85, -2.85), 0.05 * u), 'powder', wobble=0.5)
    s.shape(s.rrect(*P(2.42, -3.5), *P(2.88, -3.32), 0.04 * u), 'navy', wobble=0.4)
    s.line([P(1.18, -3.95), P(1.5, -3.25)], 0.07 * u, 'wood', taper=0.0, wobble=0.3)               # the ladle
    s.pot(*P(1.62, -2.85), 1.2 * u, 'red')
    s.person(x, y, u, 1, 'stand', dict(P2, top='green', bottom='navy', apron='cream', hand_n=('grip', -55),
                                         hand_f=('flat', 8)),
             rel=dict(elbow_n=(0.18, -3.35), wrist_n=(0.98, -3.78), elbow_f=(0.62, -3.55), wrist_f=(0.98, -3.02),
                      head=(0.2, -5.2)))
    MARKS.append(lambda: s.steam(*P(1.62, -3.7), 0.95 * u, n=3, colour='red_line'))


# ---------------------------------------------------------------- 3. dinner for the cat
def cat_dinner(s, x, y, u):
    P = at(x, y, u)
    cat = s.cat_sit(*P(2.75, 0.02), 1.15 * u, facing=-1, head_down=0.25)
    bowl = {}

    def put_bowl():
        bowl['P'] = s.bowl(*P(1.72, 0.02), 0.95 * u, colour='red', fill='wood_light')
        r = np.random.default_rng(3)
        for _ in range(9):
            bx, by = P(1.72 + r.uniform(-0.3, 0.3), -0.42 + r.uniform(-0.04, 0.04))
            s.dot(bx, by, 0.045 * u, 'wood')
    s.person(x, y, u, 1, 'crouch', dict(P1, top='powder', bottom='navy', hood=True, hand_n=('grip', 35),
                                          hand_f=('flat', 30)),
             hooks=dict(hand_near=put_bowl),
             rel=dict(wrist_n=(1.2, -0.62), elbow_n=(0.78, -1.5), elbow_f=(0.95, -2.0), wrist_f=(1.0, -1.5)))
    MARKS.append(lambda: s.bang(*P(2.86, -1.45), 0.2 * u, -90, 'red_line'))


# ---------------------------------------------------------------- 4. a book and a mug
def reading(s, x, y, u):
    P = at(x, y, u)
    ch = s.armchair(*P(0.1, 0), 2.2 * u, 3.9 * u, 1, 'olive')
    s.stool(*P(2.55, 0), 0.9 * u, 1.75 * u, 'wood')
    s.mug(*P(2.55, -1.82), 0.5 * u, 'red', facing=-1)
    book = {}

    def open_book():
        ch['arm']()
        book['P'] = s.book(*P(0.95, -3.35), 0.95 * u, angle=-58, colour='blue')
    s.person(x, y, u, 1, 'sit', dict(P2, top='mustard', bottom='grey', shoes='grey_light', laces=False, eye='down',
                                       hand_n=('grip', -70), hand_f=('grip', -80), tilt=8),
             hooks=dict(arm_near=open_book),
             rel=dict(hip_n=(0.0, -1.75), hip_f=(0.15, -1.75), knee_n=(1.15, -1.95), knee_f=(1.2, -1.9),
                      ankle_n=(1.1, -0.24), ankle_f=(1.3, -0.24), hem_b=(-0.5, -1.9), hem_f=(0.55, -1.9),
                      sh_b=(-0.38, -3.62), sh_f=(0.44, -3.65), neck=(0.12, -3.86), head=(0.3, -4.32),
                      elbow_n=(0.1, -2.6), wrist_n=(0.82, -3.05), elbow_f=(0.62, -2.75), wrist_f=(1.1, -3.2)))
    MARKS.append(lambda: s.steam(*P(2.55, -2.45), 0.75 * u, n=2, colour='red_line'))


# ---------------------------------------------------------------- 5. the nap
def nap(s, x, y, u):
    P = at(x, y, u)
    sofa = s.sofa(*P(-3.7, 0)[:1], P(3.4, 0)[0], y, 2.3 * u, 'grey_light')
    s.shape(s.blob(*P(-2.95, -1.55), 0.55 * u, 0.42 * u, rough=0.06, rot=-20), 'powder', wobble=1.0)   # cushion
    s.person(*P(2.65, -1.62), u, 1, 'stand', dict(P1, top='blue', bottom='grey', socks='red', shoes=None, eye='closed',
                                                 hand_n=('flat', 0), hand_f=None),
             rot=-90,
             rel=dict(knee_n=(0.5, -1.5), ankle_n=(0.15, -0.3), knee_f=(0.35, -1.45), ankle_f=(0.0, -0.25),
                      elbow_n=(-0.05, -3.3), wrist_n=(0.55, -3.0), head=(0.1, -5.2)),
             hooks=dict(arm_near=lambda: s.book(*P(-1.2, -2.02), 1.05 * u, angle=0, colour='mustard', open_='tent')))
    s.cat_curl(*P(1.6, 0.05), 1.15 * u)
    MARKS.append(lambda: s.zzz(*P(-2.6, -3.4), 0.32 * u, colour='navy'))


LAYOUTS = {
    # name: canvas, [(vignette, x, y, u)]
    'sheet': ((1500, 2000), [(going_out, 330, 860, 100), (soup, 860, 800, 100), (nap, 790, 1330, 100),
                             (cat_dinner, 210, 1880, 100), (reading, 940, 1895, 100)]),
    'wide': ((1920, 1080), [(going_out, 340, 860, 84), (soup, 810, 530, 84), (reading, 1440, 530, 84),
                            (cat_dinner, 770, 1010, 84), (nap, 1500, 1010, 84)]),
}
NAMES = {going_out: 'going_out', soup: 'soup', cat_dinner: 'cat_dinner', reading: 'reading', nap: 'nap'}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'spotillo_rainy_saturday.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    layout = sys.argv[sys.argv.index('--layout') + 1] if '--layout' in sys.argv else 'sheet'
    T0 = time.time()
    (W, H), items = LAYOUTS[layout]
    s = SpotIllustration(W, H, seed=5, keep_stages=bool(stages), stages_dir=stages)
    s.finish()
    s.paper()
    s.stage('paper')
    MARKS.clear()
    for fn, x, y, u in items:
        fn(s, x, y, u)
        s.stage(NAMES[fn])
    for m in MARKS: m()
    s.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s')


if __name__ == '__main__':
    main()
