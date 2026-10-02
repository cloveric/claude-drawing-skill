"""Example (pop silkscreen, after the 1960s Factory method): 猫的六种心情 · Six Moods of a Cat -- one tabby cat,
one photographic key screen, six panels on one canvas. Read in order, the panels tell a small story: the cat is
curious (something smells good on the table), craves it (tongue out), is happy (got it), is startled (caught!),
angry (hissing, ears flat) and finally sleepy. Each panel is hand-painted first -- a loud flat background, the cat,
then a muzzle and bib, inner ears, nose, eyes, collar and tag -- in its own colour scheme, loosely traced and
drifting off the photograph; then the same black key (shadow masses, tabby stripes, the features of that mood) is
pulled through it, each time placed a little differently and with a different ink load: one flooded, one starved
with a dry patch, one printed twice. No image model.
python3 popart_cat_moods.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from popart import (PopSilkscreen, turn, mirror, HOT_PINK, PINK, BLUSH, RED, ORANGE, LEMON, YELLOW, CREAM, LIME,
                    TURQUOISE, SKY, BLUE, ULTRA, WHITE)

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'popart_cat_moods.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

ps = PopSilkscreen(1920, 1080, seed=15)
ps.canvas()
panels = ps.grid(3, 2, gap=12, margin=14, origin=(0.5, 0.53), unit=0.285)
ps.stage('canvas')

# ---------------------------------------------------------------- six moods, one cat
# ear: outward rotation (deg) and length; eye: openness, pupil ('round' r | 'slit' w | 'happy' | 'sleepy');
# gaze: pupil offset; tilt: head rotation about the neck (deg ccw); mouth; whisk: whisker sweep (+ forward, - back)
MOODS = [
    dict(name='curious', ear=(-6, 1.06), eye=1.12, pupil=('round', 0.118), gaze=(0.0, -0.01), tilt=9, mouth='closed', whisk=0.10,
         bg=TURQUOISE, cat=LEMON, muzzle=CREAM, accent=HOT_PINK, iris='#3ddc6e', collar=ORANGE, tag=HOT_PINK),
    dict(name='craving', ear=(0, 1.0), eye=1.0, pupil=('round', 0.100), gaze=(-0.03, -0.035), tilt=-4, mouth='lick', whisk=0.05,
         bg=ORANGE, cat='#ff74b4', muzzle=BLUSH, accent=RED, iris=LEMON, collar=BLUE, tag=LEMON),
    dict(name='happy', ear=(10, 0.98), eye=1.0, pupil=('happy',), gaze=(0, 0), tilt=4, mouth='smile', whisk=0.0,
         bg=HOT_PINK, cat=YELLOW, muzzle=LEMON, accent=RED, iris=TURQUOISE, collar=TURQUOISE, tag=LEMON, blush=RED),
    dict(name='startled', ear=(-2, 1.12), eye=1.34, pupil=('round', 0.042), gaze=(0, 0), tilt=0, mouth='o', whisk=0.2,
         bg=LIME, cat=WHITE, muzzle=BLUSH, accent=HOT_PINK, iris=SKY, collar=RED, tag=YELLOW),
    dict(name='angry', ear=(60, 0.74), eye=0.62, pupil=('slit', 0.026), gaze=(0, 0.0), tilt=0, mouth='hiss', whisk=-0.25,
         bg=RED, cat='#2ccf74', muzzle=LEMON, accent=PINK, iris='#f3ff3a', collar=ULTRA, tag=LIME, brows=True),
    dict(name='sleepy', ear=(16, 0.96), eye=1.0, pupil=('sleepy',), gaze=(0, 0), tilt=-11, mouth='closed', whisk=-0.08,
         bg=ULTRA, cat=PINK, muzzle=WHITE, accent=HOT_PINK, iris=LIME, collar=LEMON, tag=TURQUOISE),
]
# how each panel was painted and printed: tracing drift (px), key shift (px), key rotation, ink load ...
PRINT = [
    dict(drift=(9, -5), key=(-8, 6), rot=0.5, density=1.02, flood=0.25, starve=0.0, nicks=1, pull=90),
    dict(drift=(-8, 6), key=(7, -5), rot=-0.4, density=1.14, flood=0.6, starve=0.0, nicks=0, pull=90),
    dict(drift=(6, 9), key=(-5, -8), rot=0.3, density=0.95, flood=0.1, starve=0.24, nicks=2, pull=0),
    dict(drift=(-7, -7), key=(10, 7), rot=-0.6, density=1.0, flood=0.2, starve=0.0, nicks=1, pull=90, ghost=(15, -10, 0.38)),
    dict(drift=(10, 4), key=(-11, -4), rot=0.9, density=1.1, flood=0.38, starve=0.0, nicks=1, pull=90),
    dict(drift=(-5, 10), key=(6, 9), rot=-0.7, density=0.94, flood=0.05, starve=0.3, nicks=1, pull=90),
]
PIVOT = (0.0, 0.80)                       # the head turns about the neck


class Cat:
    """unit geometry of the cat for one mood (head centre at 0, 0; light from the upper left)"""

    def __init__(self, m):
        self.m = m
        self.tilt = m['tilt']
        rot, ln = m['ear']
        b_in, b_out = np.array([0.22, -0.86]), np.array([0.94, -0.47])
        mid = (b_in + b_out) / 2

        def ear_tf(P, keep_base=False):
            P = np.asarray(P, np.float32)
            Q = mid + (P - mid) * ln
            if keep_base:
                Q[0], Q[-1] = P[0], P[-1]
            return turn(Q, -rot, mid)                     # outward = clockwise for the right ear
        self.ear_r = ear_tf([b_in, (0.38, -1.16), (0.62, -1.45), (0.73, -1.54), (0.81, -1.42), (0.92, -1.02), b_out], True)
        self.cav_r = ear_tf([(0.34, -0.87), (0.47, -1.13), (0.66, -1.39), (0.74, -1.42), (0.80, -1.12), (0.82, -0.72), (0.60, -0.70)])
        self.dark_r = ear_tf([(0.36, -0.86), (0.47, -1.12), (0.64, -1.40), (0.735, -1.50), (0.82, -1.40), (0.93, -1.0),
                              (0.95, -0.55), (0.80, -0.62), (0.60, -0.70)])          # the far ear, in shadow
        self.cavl_r = ear_tf([(0.33, -0.88), (0.45, -1.12), (0.62, -1.34), (0.66, -1.30), (0.58, -1.08), (0.50, -0.84)])
        self.tufts_r = [ear_tf(P) for P in ([(0.40, -0.84), (0.46, -0.98), (0.56, -1.12)],
                                             [(0.50, -0.80), (0.55, -0.97), (0.63, -1.16)],
                                             [(0.62, -0.78), (0.65, -0.95), (0.70, -1.12)],
                                             [(0.74, -0.76), (0.75, -0.90), (0.77, -1.02)])]
        cheek = [(1.00, -0.22), (1.07, 0.10), (1.03, 0.34), (0.88, 0.56), (0.62, 0.74), (0.30, 0.84)]
        right = np.concatenate([[(0.0, -0.93)], self.ear_r, cheek], 0)
        left = mirror(right[1:])[::-1]
        self.head = self.T(np.concatenate([right, [(0.0, 0.87)], left], 0))
        self.cheek_r = np.asarray(cheek, np.float32)

    def T(self, P):
        return turn(P, self.tilt, PIVOT)


BODY = [(-0.80, 0.40), (-0.96, 0.86), (-1.36, 1.20), (-1.86, 1.58), (-2.22, 2.02), (-2.45, 2.7),
        (2.45, 2.7), (2.22, 2.02), (1.86, 1.58), (1.36, 1.20), (0.96, 0.86), (0.80, 0.40)]
COLLAR = [(-0.88, 0.80), (-0.46, 0.95), (0.0, 1.0), (0.46, 0.95), (0.88, 0.80)]
TAG = (0.05, 1.17, 0.105)
TONGUE = [(-0.02, 0.48), (-0.22, 0.48), (-0.26, 0.60), (-0.20, 0.71), (-0.11, 0.74), (-0.04, 0.68), (-0.02, 0.58)]


def eye_pts(cx, cy, ew, eh, side, slant=7.0):
    P = np.array([(-ew, 0.0), (-0.55 * ew, -0.86 * eh), (0, -eh), (0.55 * ew, -0.9 * eh), (ew, -0.02 * eh),
                  (0.55 * ew, 0.84 * eh), (0, 0.95 * eh), (-0.55 * ew, 0.82 * eh)], np.float32)
    return turn(P, slant * side, (0, 0)) + np.array([cx, cy], np.float32)


def tracing(P, rng, jit=0.022, grow=1.02, about=(0.0, 0.0)):
    """the painter's loose tracing of an outline: slightly enlarged and wobbled"""
    P = np.asarray(P, np.float32)
    a = np.asarray(about, np.float32)
    return a + (P - a) * grow + rng.normal(0, jit, P.shape).astype(np.float32)


def colour_layers(p, c, m, rng):
    """the hand-painted shapes for one panel, as (name, mask, colour) in painting order"""
    T = c.T
    head = p.shape(tracing(c.head, rng, 0.02, 1.025, (0, 0)))
    body = p.shape(tracing(BODY, rng, 0.03, 1.0))
    cat = np.maximum(head, body)
    muzzle = p.shape(T(tracing([(-0.40, 0.30), (-0.16, 0.18), (0, 0.21), (0.16, 0.18), (0.40, 0.30), (0.36, 0.56),
                                (0.18, 0.74), (0, 0.79), (-0.18, 0.74), (-0.36, 0.56)], rng, 0.02)))
    bib = p.shape(tracing([(-0.50, 1.06), (0, 1.0), (0.50, 1.06), (0.62, 1.55), (0.42, 2.1), (0, 2.5),
                           (-0.42, 2.1), (-0.62, 1.55)], rng, 0.03))
    ears = np.maximum(p.shape(T(tracing(c.cav_r, rng, 0.02, 0.92, c.cav_r.mean(0)))),
                      p.shape(T(mirror(tracing(c.cav_r, rng, 0.02, 0.92, c.cav_r.mean(0))))))
    nose = p.shape(T(tracing([(-0.14, 0.215), (0, 0.235), (0.14, 0.215), (0.02, 0.37), (-0.02, 0.37)], rng, 0.012)))
    L = [('cat', cat, m['cat']), ('muzzle', muzzle, m['muzzle']), ('bib', bib, m['muzzle']),
         ('ears', ears, m['accent']), ('nose', nose, m['accent'])]
    kind = m['pupil'][0]
    if kind == 'sleepy':                                  # closed lids: a pop "eyeshadow" patch above the line
        lid = [(-0.25, -0.02), (-0.16, -0.17), (0.0, -0.21), (0.16, -0.17), (0.25, -0.02), (0.1, 0.05), (-0.1, 0.05)]
        lids = np.maximum(p.shape(T(np.array(lid) + [0.41, -0.11])), p.shape(T(np.array(lid) + [-0.41, -0.11])))
        L.append(('lids', lids, m['iris']))
    elif kind == 'happy':
        pass
    else:
        e = m['eye']
        irises = np.maximum(p.ellipse(*T([(0.41, -0.11)])[0], 0.25, 0.17 * e + 0.02, rot=7),
                            p.ellipse(*T([(-0.41, -0.11)])[0], 0.25, 0.17 * e + 0.02, rot=-7))
        L.append(('irises', irises, m['iris']))
    if m['mouth'] == 'lick':
        L.append(('tongue', p.shape(T(TONGUE)), m['accent']))
    if m['mouth'] == 'hiss':
        L.append(('tongue', p.ellipse(*T([(0.0, 0.66)])[0], 0.15, 0.08), m['accent']))
    if m.get('blush'):
        L.append(('blush', np.maximum(p.ellipse(*T([(0.62, 0.24)])[0], 0.17, 0.11),
                                      p.ellipse(*T([(-0.62, 0.24)])[0], 0.17, 0.11)), m['blush']))
    collar = p.stroke(tracing(COLLAR, rng, 0.012), 0.13, 0.13)
    L.append(('collar', collar, m['collar']))
    L.append(('tag', p.ellipse(TAG[0], TAG[1], TAG[2] * 1.08), m['tag']))
    return L


class Union:
    """running union of masks (keeps memory flat: no list of full-size masks)"""

    def __init__(self, p):
        self.a = p.blank()

    def append(self, m):
        np.maximum(self.a, m, out=self.a)


class Tones(Union):
    def append(self, item):
        m, level = item
        np.maximum(self.a, self.p.soft(m, 0.05) * level, out=self.a)

    def __init__(self, p):
        super().__init__(p)
        self.p = p


def key_masks(p, c, m):
    """the photographic shadow masses and features of this mood -> (solid, tone)"""
    T = c.T
    S = Union(p)                                           # solid masses
    tone = Tones(p)                                        # (mask, level) -> halftone areas
    st = lambda pts, w0, w1=None, **k: p.stroke(T(pts), w0, w1, **k)
    # --- shadow side of the head (light from the upper left): a crescent down the far cheek and jaw
    outer = [(0.96, -0.40), (1.03, -0.20), (1.10, 0.10), (1.06, 0.36), (0.90, 0.60), (0.62, 0.79), (0.28, 0.89)]
    inner = [(0.30, 0.76), (0.60, 0.62), (0.80, 0.40), (0.88, 0.12), (0.86, -0.16), (0.84, -0.38)]
    cres = p.shape(T(outer + inner))
    S.append(cres)
    tone.append((p.shape(T(outer + [(0.10, 0.80), (0.42, 0.52), (0.66, 0.28), (0.70, -0.02), (0.72, -0.40)])), 0.38))
    # fur tufts along the shadowed cheek ruff and the chin
    for k, t in enumerate(np.linspace(0.05, 0.95, 9)):
        P = c.cheek_r
        i = t * (len(P) - 1); j = int(i); f = i - j
        a = P[j] * (1 - f) + P[min(j + 1, len(P) - 1)] * f
        n = np.array([a[0] - 0.25, a[1] - 0.05]); n /= np.linalg.norm(n)
        L = 0.11 + 0.05 * np.sin(k * 2.3)
        S.append(st([a - n * 0.04, a + n * L * 0.6 + np.array([0, 0.02]), a + n * L + np.array([0, 0.05])], 0.07, 0.0))
    # --- under the chin, on the neck above the collar
    chin = [(-0.62, 0.74), (-0.30, 0.86), (0.0, 0.90), (0.30, 0.87), (0.66, 0.76), (0.80, 0.80), (0.50, 0.95),
            (0.0, 1.0), (-0.48, 0.95)]
    chin_m = p.shape(T(chin))
    S.append(chin_m * (p.XX > p.at(-0.25, 0)[0]))
    tone.append((chin_m, 0.55))
    # --- ears: the far one is a dark cavity, the near one only shadowed along its inner edge; light fur tufts
    cav = p.shape(T(c.dark_r if m['ear'][0] < 40 else c.cav_r))
    cavl = p.shape(T(mirror(c.cavl_r)))
    tufts = p.blank()
    for P in c.tufts_r:
        tufts = np.maximum(tufts, st(P, 0.026, 0.0))
        tufts = np.maximum(tufts, st(mirror(P), 0.026, 0.0))
    if m['ear'][0] > 40:                                   # ears pinned back: we see their backs, not the cavity
        tone.append((cav, 0.5))
        S.append(st([c.ear_r[1], c.ear_r[2], c.ear_r[3]], 0.03, 0.07))
    else:
        S.append(np.clip(cav - tufts * 0.9, 0, 1))
    S.append(np.clip(cavl - tufts * 0.9, 0, 1))
    tone.append((p.shape(T(mirror(c.cav_r))), 0.35))
    # --- forehead: the tabby "M"
    for P, w in [([(0, -0.92), (0.0, -0.72), (0.0, -0.50)], 0.075),
                 ([(0.18, -0.90), (0.18, -0.70), (0.12, -0.47)], 0.062),
                 ([(-0.18, -0.90), (-0.18, -0.70), (-0.12, -0.47)], 0.062),
                 ([(0.42, -0.82), (0.40, -0.60), (0.31, -0.40)], 0.06),
                 ([(-0.42, -0.82), (-0.40, -0.60), (-0.31, -0.40)], 0.05)]:
        S.append(st(P, w, 0.012))
    # stripes running back over the top of the head (hidden under the ear when it is pinned back)
    if m['ear'][0] < 40:
        S.append(st([(0.55, -0.62), (0.70, -0.50), (0.86, -0.42)], 0.05, 0.02))
    # --- eyes
    e, kind = m['eye'], m['pupil'][0]
    for side in (1, -1):
        cx, cy = 0.41 * side, -0.11
        if kind in ('happy', 'sleepy'):
            if kind == 'happy':
                P = [(cx - 0.20, cy + 0.07), (cx - 0.11, cy - 0.04), (cx, cy - 0.075), (cx + 0.11, cy - 0.04), (cx + 0.20, cy + 0.07)]
                S.append(st(P, 0.10, profile=lambda t: 0.35 + 0.65 * np.clip(np.sin(np.pi * t), 0, 1) ** 0.7))
            else:
                P = [(cx - 0.23, cy - 0.03), (cx - 0.11, cy + 0.045), (cx, cy + 0.06), (cx + 0.11, cy + 0.045), (cx + 0.23, cy - 0.02)]
                S.append(st(P, 0.095, profile=lambda t: 0.4 + 0.6 * np.clip(np.sin(np.pi * t), 0, 1) ** 0.6))
                S.append(st([(cx - 0.17, cy - 0.10), (cx, cy - 0.075), (cx + 0.17, cy - 0.09)], 0.03, 0.008))
            continue
        ew, eh = 0.215, 0.135 * e
        inner = p.shape(T(eye_pts(cx, cy, ew, eh, side)))
        outer = p.shape(T(eye_pts(cx, cy - 0.016, ew + 0.05, eh + 0.07, side)))
        S.append(np.clip(outer - inner, 0, 1))
        gx, gy = m['gaze']
        if kind == 'round':
            r = m['pupil'][1]
            pc = (cx + gx, cy + gy)
            pupil = p.ellipse(*T([pc])[0], r, r * 1.04) * inner
            hole = p.ellipse(*T([(pc[0] - r * 0.35 - 0.02, pc[1] - r * 0.4 - 0.02)])[0], max(0.028, r * 0.26))
            S.append(np.clip(pupil - hole, 0, 1))
        else:
            w = m['pupil'][1]
            lens = p.shape(T([(cx, cy - eh * 1.1), (cx + w, cy), (cx, cy + eh * 1.1), (cx - w, cy)])) * inner
            S.append(lens)
        tone.append((p.shape(T(eye_pts(cx, cy - eh * 0.45, ew * 0.9, eh * 0.5, side))) * inner, 0.42))   # upper-lid shade
        if m.get('brows'):
            S.append(st([(cx - 0.18 * side, cy - 0.15), (cx + 0.02 * side, cy - 0.24), (cx + 0.24 * side, cy - 0.33)], 0.10, 0.03))
    # tabby lines from the outer corners of the eyes, and under the eyes
    for side in (1, -1):
        S.append(st([(0.63 * side, -0.10), (0.78 * side, -0.07), (0.94 * side, -0.01)], 0.05, 0.01))
        S.append(st([(0.56 * side, 0.04), (0.72 * side, 0.09), (0.88 * side, 0.16)], 0.04 if side < 0 else 0.05, 0.008))
    # cheek stripes: bold in the shadow, thin and broken in the light
    S.append(st([(0.68, 0.22), (0.84, 0.21), (1.02, 0.25)], 0.06, 0.02))
    S.append(st([(0.64, 0.38), (0.80, 0.40), (0.96, 0.46)], 0.055, 0.02))
    S.append(st([(-0.70, 0.22), (-0.84, 0.21), (-0.98, 0.25)], 0.035, 0.006))
    S.append(st([(-0.68, 0.39), (-0.80, 0.41), (-0.92, 0.46)], 0.03, 0.004))
    # --- nose: bridge shadow on the far side, nostrils, the shadow under the leather
    S.append(st([(0.09, -0.04), (0.12, 0.10), (0.14, 0.21)], 0.025, 0.06))
    tone.append((st([(0.06, -0.10), (0.11, 0.08), (0.16, 0.22)], 0.12, 0.16), 0.45))
    for side in (1, -1):
        S.append(st([(0.085 * side, 0.27), (0.06 * side, 0.305), (0.03 * side, 0.315)], 0.045, 0.02))
    S.append(st([(0.14, 0.22), (0.08, 0.30), (0.02, 0.37)], 0.04, 0.03))
    if m.get('brows'):                                     # a wrinkled nose
        for k in range(3):
            S.append(st([(-0.10, 0.02 + 0.06 * k), (0.0, 0.0 + 0.06 * k), (0.10, 0.02 + 0.06 * k)], 0.024, 0.024))
    # --- mouth
    mo = m['mouth']
    if mo != 'hiss':
        S.append(st([(0, 0.36), (0, 0.42), (0, 0.46)], 0.032, 0.03))
    if mo in ('closed', 'lick', 'smile', 'o'):
        up = 0.05 if mo == 'smile' else 0.0
        for side in (1, -1):
            S.append(st([(0, 0.45), (0.08 * side, 0.505), (0.16 * side, 0.50 - up * 0.4), (0.23 * side, 0.45 - up)],
                        0.034, 0.012))
    if mo == 'o':
        S.append(p.ellipse(*T([(0.0, 0.565)])[0], 0.062, 0.075))
    if mo == 'lick':
        S.append(st([(-0.07, 0.49), (-0.10, 0.57), (-0.12, 0.64)], 0.026, 0.004))            # the groove
        S.append(st([(-0.04, 0.50), (-0.02, 0.60), (-0.07, 0.69), (-0.15, 0.725), (-0.23, 0.69), (-0.25, 0.58),
                     (-0.22, 0.50)], 0.022, 0.04))                                          # the tip's outline
    if mo == 'hiss':
        mouth = p.shape(T([(-0.29, 0.47), (-0.13, 0.42), (0, 0.45), (0.13, 0.42), (0.29, 0.47), (0.24, 0.63),
                           (0.11, 0.74), (0, 0.76), (-0.11, 0.74), (-0.24, 0.63)]))
        fangs = p.blank()
        for side in (1, -1):
            fangs = np.maximum(fangs, p.shape(T([(0.125 * side, 0.445), (0.195 * side, 0.465), (0.16 * side, 0.585)]), smooth=False))
            fangs = np.maximum(fangs, p.shape(T([(0.085 * side, 0.735), (0.14 * side, 0.715), (0.115 * side, 0.645)]), smooth=False))
        tongue = p.ellipse(*T([(0.0, 0.675)])[0], 0.12, 0.055)
        S.append(np.clip(mouth - fangs - tongue * 0.95, 0, 1))
        S.append(st([(0, 0.34), (0, 0.40), (0, 0.45)], 0.032, 0.03))
    # --- whisker pads and whiskers
    spots = []
    for side in (1, -1):
        for row in range(3):
            for k in range(4):
                u = side * (0.12 + 0.055 * k + 0.025 * (row % 2))
                spots.append((u, 0.405 + 0.045 * row + 0.008 * k, 0.0145 if side > 0 else 0.012))
    pads = p.blank()
    for u, v, r in spots:
        x, y = T([(u, v)])[0]
        pads = np.maximum(pads, p.ellipse(x, y, r))
    S.append(pads)
    wk = m['whisk']
    for side in (1, -1):
        for k in range(3):
            a = (0.31 * side, 0.43 + 0.045 * k)
            spread = (k - 1) * (0.16 + 0.12 * wk)
            b = (1.55 * side * (1 - 0.1 * (wk < 0) * abs(wk) * 2), 0.36 + spread - 0.12 * wk + 0.06)
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 0.05 + 0.02 * k)
            S.append(st([a, mid, b], 0.024, 0.005, caps=False))
    # --- body: far shoulder in shadow, tabby rings round the chest (broken over the light bib), collar shadow
    S.append(p.shape([(0.82, 0.78), (1.00, 0.92), (1.40, 1.22), (1.90, 1.60), (2.25, 2.05), (2.5, 2.7), (1.62, 2.7),
                      (1.45, 2.0), (1.24, 1.55), (1.0, 1.22)]))
    tone.append((p.shape([(0.82, 0.78), (1.40, 1.22), (1.90, 1.60), (2.5, 2.7), (1.1, 2.7), (0.9, 1.7), (0.7, 1.15)]), 0.4))
    for v, sw in ((1.36, 0.075), (1.70, 0.085), (2.05, 0.09)):
        tone.append((p.stroke([(-1.7, v + 0.26), (-1.3, v + 0.04), (-0.86, v - 0.02)], sw * 1.3, 0.02), 0.38))
        S.append(p.stroke([(0.62, v - 0.04), (1.2, v + 0.02), (1.75, v + 0.30)], 0.02, sw))
    S.append(p.stroke([(-0.30, 1.04), (0.2, 1.06), (0.6, 1.0), (0.86, 0.90)], 0.018, 0.05))       # under the collar
    tag = p.ellipse(TAG[0], TAG[1], TAG[2]) - p.ellipse(TAG[0] - 0.012, TAG[1] - 0.012, TAG[2] * 0.82)
    S.append(np.clip(tag, 0, 1) * (p.XX > p.at(TAG[0] - 0.02, 0)[0]))
    S.append(p.ellipse(TAG[0], TAG[1] - TAG[2] - 0.02, 0.03) - p.ellipse(TAG[0], TAG[1] - TAG[2] - 0.02, 0.016))
    return np.clip(S.a, 0, 1), tone.a


# ---------------------------------------------------------------- 1. backgrounds, up to the tape
for p, m in zip(panels, MOODS):
    ps.ground(p, m['bg'], direction=float(np.random.default_rng(p.index).uniform(-8, 8)))
ps.stage('grounds')

# ---------------------------------------------------------------- 2. the cat, then the loose colour shapes
cats = [Cat(m) for m in MOODS]
layers = lambda p: colour_layers(p, cats[p.index], MOODS[p.index], np.random.default_rng(40 + p.index))
for p, pr in zip(panels, PRINT):
    name, mask, col = layers(p)[0]
    ps.paint(p, mask, col, drift=pr['drift'], wobble=3.0)
ps.stage('cats')
for p, pr in zip(panels, PRINT):
    r = np.random.default_rng(70 + p.index)
    for name, mask, col in layers(p)[1:]:
        d = (pr['drift'][0] + r.uniform(-6, 6), pr['drift'][1] + r.uniform(-6, 6))
        ps.paint(p, mask, col, drift=d, wobble=2.2 if name in ('nose', 'irises', 'tag') else 3.0)
ps.stage('shapes')

# ---------------------------------------------------------------- 3. the black key, pulled panel by panel
for p, c, m, pr in zip(panels, cats, MOODS, PRINT):
    solid, tone = key_masks(p, c, m)
    ps.key(p, solid, tone=tone, shift=pr['key'], rot=pr['rot'], density=pr['density'], flood=pr['flood'],
           starve=pr['starve'], nicks=pr['nicks'], pull=pr['pull'], ghost=pr.get('ghost'))
    if p.index < 5:
        ps.stage(f'key_{p.index + 1}')

ps.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
