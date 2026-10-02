"""blackfigure -- an Attic black-figure vase: thrown, painted, incised, fired, aged and photographed
(numpy + Pillow only).

The pot is made the way a 6th-century BC Athenian workshop made it, and then shown the way a museum shows it:
on a plinth under a spotlight, with the painted friezes unrolled flat on a panel beside it.

Model:
  pot       a surface of revolution thrown on the wheel: a profile r(y) (lip, neck, shoulder, belly, foot) and two
            round handles.  Everything painted lives on an *unrolled* surface (angle round the pot x height), so the
            same painting is wrapped onto the curved pot and laid flat in the rollout -- they always agree.
            Coordinates: `y` is px from the top of the lip; along a frieze, `x` is arc length in px at that frieze's
            own radius (the painter worked at real size, so figures keep their proportions on the belly and on the
            narrower lower body).
  clay      Attic clay is iron-rich: matte buff-tan when dry, orange when fired.  It is burnished, so it keeps a
            soft satin sheen.  Faint throwing rings ripple the surface (they show up in the reflections).
  slip      the "black" is a refined clay slip.  Painted on, it is a dull dark brown; only the three-stage firing
            (oxidise - reduce - re-oxidise) turns it into the glossy blue-black glaze.  Where it went on thin (brush
            edges, streaks) it fires reddish brown.  Wheel bands are painted while the pot spins: dead level, with
            a tiny lap where the brush came off.
  figures   silhouettes painted in slip; overlapping parts are told apart only by *incision*: a sharp point
            scratched through the slip before firing shows the orange clay as a hair-thin line (eye, hair line,
            muscles, the outline of a nearer limb or horse over a farther one).  Added colours go on last, matte,
            over the black: purple-red (manes, fillets, beards, tongues) and white (charioteers' robes, a white
            horse).  Every figure part is z-ordered: a nearer black shape covers farther added colour and
            incisions, then cuts its own contour -- so a four-horse team reads as four horses.
  ornament  the canonical bands: lip and foot in black, palmette-lotus chain on the neck, alternating black/red
            tongues on the shoulder, a running meander, rays above the foot.
  text      archaic Greek letters painted in slip with a fine brush (kalos inscriptions, labels, nonsense
            inscriptions), left-to-right or retrograde.
  fire      switches every material from its raw look to the fired one.
  age       2,500 years: added white flakes off (leaving a dull ghost on the glaze), added red fades, calcareous
            encrustation and root marks, chips on lip and foot (pale fabric), a mended break with a toned plaster
            fill, a misfired patch where the black stayed reddish.
  photo     the pot is lit like a museum photograph: a tall softbox upper left and a strip light right reflect as
            long highlights in the glaze, the clay gets a broad satin sheen, the pale plinth reflects in the lower
            glaze.  A slight perspective bends every band into an arc.  Rollouts are flat and evenly lit.

    from blackfigure import BlackFigure
    bf = BlackFigure(1920, 1080, seed=1)
    bf.museum()
    pot = bf.throw(cx=470, foot=985, height=930)
    pot.paint_handles(); pot.band(0, 60)                    # wheel-painted lip
    z = pot.zone(300, 530)                                   # a frieze between two y's
    z.runner(200, phase=0); z.quadriga(700)                  # figures are declared ...
    pot.paint(); pot.incise(); pot.add_colour(); pot.fire()  # ... and painted pass by pass
    bf.save('out.png')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font, text_mask


def _hex(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _lin(c):
    return np.power(np.clip(c, 0, 1), 2.2).astype(np.float32)


def _srgb(c):
    return np.power(np.clip(c, 0, 1), 1 / 2.2).astype(np.float32)


COLOURS = {
    'clay_raw': '#bb9878', 'slip_raw': '#4f3628', 'red_raw': '#7b3c34', 'white_raw': '#d8d0bf',
    'clay': '#c96e3c', 'black': '#110e0f', 'thin': '#5c2a17', 'red': '#86303a', 'white': '#ebe1c8',
    'fabric': '#c98a60', 'fill_clay': '#c27b52', 'fill_black': '#3f3836', 'crust': '#d4cbb8',
    'misfire': '#6e341f',
}

# profiles: (y, r) as fractions of height / max radius, top of lip -> resting surface
SHAPES = {
    'neck_amphora': dict(
        profile=[(0.000, 0.372), (0.006, 0.404), (0.020, 0.421), (0.040, 0.418), (0.054, 0.398), (0.062, 0.352),
                 (0.074, 0.318), (0.120, 0.300), (0.180, 0.301), (0.212, 0.313), (0.226, 0.333), (0.236, 0.338),
                 (0.246, 0.368), (0.270, 0.520), (0.300, 0.680), (0.340, 0.820), (0.390, 0.930), (0.440, 0.985),
                 (0.480, 1.000), (0.530, 0.990), (0.580, 0.950), (0.640, 0.870), (0.700, 0.760), (0.760, 0.630),
                 (0.820, 0.490), (0.870, 0.370), (0.900, 0.300), (0.915, 0.272), (0.925, 0.268), (0.932, 0.302),
                 (0.940, 0.362), (0.960, 0.415), (0.980, 0.426), (0.993, 0.416), (1.000, 0.398)],
        handle=[(0.300, 0.094), (0.400, 0.092), (0.520, 0.106), (0.600, 0.148), (0.640, 0.205), (0.655, 0.255),
                (0.642, 0.302)],
        handle_w=0.072),
}

# archaic Attic letters as brush strokes in a 0.7 x 1 box (y down)
_O = [(0.35 + 0.33 * np.cos(a), 0.5 + 0.42 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 17)]
GLYPHS = {
    'Α': [[(0, 1), (0.35, 0), (0.7, 1)], [(0.14, 0.62), (0.56, 0.54)]],
    'Β': [[(0, 1), (0, 0), (0.42, 0.04), (0.5, 0.24), (0.06, 0.48), (0.55, 0.64), (0.52, 0.92), (0, 1)]],
    'Γ': [[(0, 1), (0, 0), (0.55, 0.05)]],
    'Δ': [[(0, 1), (0.35, 0), (0.7, 1), (0, 1)]],
    'Ε': [[(0.6, 0), (0, 0), (0, 1), (0.6, 1)], [(0, 0.5), (0.45, 0.5)]],
    'Η': [[(0, 0), (0, 1)], [(0.6, 0), (0.6, 1)], [(0, 0.5), (0.6, 0.5)]],
    'Θ': [_O, [(0.15, 0.5), (0.55, 0.5)], [(0.35, 0.28), (0.35, 0.72)]],
    'Ι': [[(0.1, 0), (0.1, 1)]],
    'Κ': [[(0, 0), (0, 1)], [(0.6, 0), (0.03, 0.5), (0.6, 1)]],
    'Λ': [[(0, 1), (0.35, 0), (0.7, 1)]],
    'Μ': [[(0, 1), (0, 0), (0.35, 0.55), (0.7, 0), (0.7, 1)]],
    'Ν': [[(0, 1), (0, 0), (0.6, 1), (0.6, 0)]],
    'Ο': [_O],
    'Π': [[(0, 1), (0, 0), (0.6, 0), (0.6, 1)]],
    'Ρ': [[(0, 1), (0, 0), (0.45, 0.04), (0.55, 0.22), (0.45, 0.42), (0, 0.47)]],
    'Σ': [[(0.6, 0), (0, 0), (0.35, 0.5), (0, 1), (0.6, 1)]],
    'Τ': [[(0, 0), (0.7, 0)], [(0.35, 0), (0.35, 1)]],
    'Υ': [[(0, 0), (0.35, 0.5), (0.7, 0)], [(0.35, 0.5), (0.35, 1)]],
    'Φ': [[(0.35 + 0.3 * np.cos(a), 0.5 + 0.25 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 15)],
          [(0.35, 0), (0.35, 1)]],
    'Χ': [[(0, 0), (0.7, 1)], [(0.7, 0), (0, 1)]],
}


# ---------------------------------------------------------------- geometry helpers
def _closed(pts, per=6):
    """closed Catmull-Rom through pts"""
    P = np.asarray(pts, np.float32)
    n = len(P)
    E = np.vstack([P[-1:], P, P[:2]])
    t = np.linspace(0, 1, per, endpoint=False)[:, None]
    t2, t3 = t * t, t * t * t
    out = []
    for i in range(1, n + 1):
        p0, p1, p2, p3 = E[i - 1], E[i], E[i + 1], E[i + 2]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.vstack(out).astype(np.float32)


def _open(pts, per=6):
    P = np.asarray(pts, np.float32)
    if len(P) == 2:
        return np.linspace(P[0], P[1], per + 1).astype(np.float32)
    return spline(P, per)


def _ribbon(pts, widths, per=6, caps=True, smooth=True):
    """polygon of a stroke along pts with a width per control point (limbs, tails, tendrils, incisions)"""
    P = _open(pts, per) if smooth else np.asarray(pts, np.float32)
    m = len(pts)
    w = np.interp(np.linspace(0, m - 1, len(P)), np.arange(m), np.broadcast_to(np.asarray(widths, np.float32), (m,)))
    d = np.gradient(P, axis=0)
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    L, R = P + nrm * w[:, None] / 2, P - nrm * w[:, None] / 2
    parts = [L]
    a = np.linspace(0, np.pi, 7)[1:-1, None]
    if caps:
        parts.append(P[-1] + (w[-1] / 2) * (np.cos(a) * nrm[-1] + np.sin(a) * d[-1]))
    parts.append(R[::-1])
    if caps:
        parts.append(P[0] + (w[0] / 2) * (np.cos(a) * (-nrm[0]) - np.sin(a) * d[0]))
    return np.vstack(parts).astype(np.float32)


def _circle(cx, cy, r, n=24, ry=None):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(a), cy + (ry or r) * np.sin(a)], 1).astype(np.float32)


def _arc(cx, cy, r, a0, a1, n=10):
    a = np.linspace(a0, a1, n)
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], 1).astype(np.float32)


def _rot(P, c, ang):
    P = np.asarray(P, np.float32)
    s, k = np.sin(ang), np.cos(ang)
    d = P - c
    return np.stack([c[0] + d[:, 0] * k - d[:, 1] * s, c[1] + d[:, 0] * s + d[:, 1] * k], 1)


def _bilinear(img, u, v):
    """sample img (H, W[, C]) at float coords, wrapping in u (round the pot)"""
    H, W = img.shape[:2]
    u0f = np.floor(u)
    fu = (u - u0f).astype(np.float32)
    u0 = u0f.astype(np.int64) % W
    u1 = (u0 + 1) % W
    v = np.clip(v, 0, H - 1.001)
    v0 = np.floor(v).astype(np.int64)
    fv = (v - v0).astype(np.float32)
    v1 = np.minimum(v0 + 1, H - 1)
    if img.ndim == 3:
        fu, fv = fu[:, None], fv[:, None]
    return (img[v0, u0] * (1 - fu) * (1 - fv) + img[v0, u1] * fu * (1 - fv) +
            img[v1, u0] * (1 - fu) * fv + img[v1, u1] * fu * fv)


# ---------------------------------------------------------------- figure builder (local units)
class _Fig:
    """a figure as an ordered list of painting operations in local units (feet at (0, 0), facing +x, y down).
    polygons scale with the figure; line widths are in pixels (a brush or a graver has a fixed width)."""

    def __init__(self):
        self.ops = []

    def slip(self, poly, occlude=True):
        self.ops.append(('poly', 'slip', np.asarray(poly, np.float32), occlude))

    def red(self, poly):
        self.ops.append(('poly', 'red', np.asarray(poly, np.float32), False))

    def white(self, poly):
        self.ops.append(('poly', 'white', np.asarray(poly, np.float32), False))

    def reserve(self, poly):
        """a patch scraped / left free of slip inside a black shape"""
        self.ops.append(('poly', 'inc', np.asarray(poly, np.float32), False))

    def cut(self, pts, w=1.15, closed=False):
        """incision: a sharp point through the slip, tapering in and out"""
        self.ops.append(('line', 'inc', np.asarray(pts, np.float32), w, closed, True))

    def line(self, pts, w=1.4, layer='slip', taper=False, closed=False):
        """a painted line (reins, staff, tendrils, letters)"""
        self.ops.append(('line', layer, np.asarray(pts, np.float32), w, closed, taper))


def _head(f, cx, cy, r, beard=False, hair='long', fillet=True, red_beard=False, detail=True):
    """archaic profile head facing +x, skull centre (cx, cy), skull radius r"""
    back = ([(-0.30, 1.6), (-0.45, 2.05), (-1.0, 1.95), (-1.18, 0.9), (-1.08, 0.0), (-0.58, -0.88)] if hair == 'long'
            else [(-0.35, 1.6), (-0.70, 0.75), (-1.0, 0.0), (-0.55, -0.85)])
    face = [(0.1, -1.02), (0.75, -0.65), (0.95, -0.22), (0.98, -0.05), (1.30, 0.30), (1.08, 0.42), (1.12, 0.55),
            (1.02, 0.62), (1.10, 0.70)]
    chin = ([(1.10, 1.05), (1.02, 1.48), (0.70, 1.48), (0.38, 1.30), (0.40, 1.6)] if beard else
            [(1.02, 0.95), (0.75, 1.10), (0.30, 1.05), (0.40, 1.6)])
    P = np.array(back + face + chin, np.float32)
    f.slip(np.stack([cx + P[:, 0] * r, cy + P[:, 1] * r], 1))
    S = lambda pts: np.stack([cx + np.asarray(pts)[:, 0] * r, cy + np.asarray(pts)[:, 1] * r], 1)
    hl = [(0.72, -0.62), (0.38, -0.48), (0.18, -0.12), (0.12, 0.30), (-0.18, 0.72), (-0.36, 1.35)]
    f.cut(S(hl if hair == 'long' else hl[:5]))
    if detail:
        f.cut(_circle(cx + 0.60 * r, cy - 0.15 * r, 0.17 * r, 12), closed=True, w=1.0)
        f.cut(S([(0.12, 0.05), (-0.12, 0.10), (-0.14, 0.38), (0.06, 0.42)]), w=0.9)
    else:
        f.cut(S([(0.56, -0.17), (0.66, -0.13)]), w=1.1)
    if beard:
        f.cut(S([(0.28, 0.42), (0.62, 0.62), (0.94, 0.78)]))
        if red_beard:
            f.red(S([(0.30, 0.48), (0.62, 0.68), (1.05, 0.78), (1.05, 1.42), (0.70, 1.44), (0.40, 1.25)]))
    if hair == 'long' and detail:
        for k in range(3):
            f.cut(S([(-0.55 - 0.15 * k, 0.6), (-0.65 - 0.12 * k, 1.1), (-0.62 - 0.1 * k, 1.75)]), w=0.9)
    if fillet:
        f.red(_ribbon(S([(0.74, -0.60), (0.30, -0.90), (-0.30, -0.88), (-0.82, -0.45)]), 0.17 * r))


def _foot(f, ankle, toe, s=1.0):
    a, t = np.asarray(ankle, np.float32), np.asarray(toe, np.float32)
    mid = a + (t - a) * 0.45 + np.array([0, 0.012 * s])
    f.slip(_ribbon([a, mid, t], [0.036 * s, 0.032 * s, 0.013 * s], per=4))
    f.slip(_circle(a[0] - 0.008 * s, a[1] + 0.008 * s, 0.02 * s, 10))


def _runner(f, phase=0, var=0.0, beard=False, back_arm='up', rng=None):
    """an archaic sprinter in full stride, chest frontal, head and legs in profile; unit = standing height"""
    rng = rng or np.random.default_rng(0)
    j = lambda p: np.asarray(p, np.float32) + rng.normal(0, 0.008, 2) * var
    fwd = [j((0.06, -0.47)), j((0.235, -0.375)), j((0.215, -0.15))]
    bck = [j((0.00, -0.47)), j((-0.075, -0.255)), j((-0.235, -0.11))]
    fwd_toe, bck_toe = (0.31, -0.118), (-0.165, -0.004)
    legs = [(bck, bck_toe), (fwd, fwd_toe)] if phase == 0 else [(fwd, fwd_toe), (bck, bck_toe)]
    lw = [0.108, 0.07, 0.058, 0.066, 0.032]

    def leg(L, toe, near):
        hip, knee, ank = L
        calf = knee + (ank - knee) * 0.35 + np.array([-0.008, 0], np.float32)
        thigh = hip + (knee - hip) * 0.5
        pts = [hip, thigh, knee, calf, ank]
        poly = _ribbon(pts, lw, per=5)
        f.slip(poly)
        _foot(f, ank, toe)
        if near:
            f.cut(poly[: len(poly) // 2 - 3])            # contour of the near leg over the far one
            f.cut(poly[len(poly) // 2 + 3:])
        f.cut([knee + (-0.02, -0.012), knee + (0.004, 0.006), knee + (0.024, -0.008)], w=1.0)

    leg(*legs[0], near=False)
    torso = [(0.10, -0.79), (0.135, -0.768), (0.168, -0.735), (0.152, -0.69), (0.14, -0.65), (0.105, -0.595),
             (0.085, -0.55), (0.10, -0.50), (0.105, -0.462), (0.06, -0.432), (0.02, -0.428), (-0.035, -0.44),
             (-0.066, -0.48), (-0.05, -0.53), (-0.025, -0.57), (-0.05, -0.64), (-0.078, -0.70), (-0.084, -0.745),
             (-0.05, -0.772), (0.05, -0.79)]
    f.slip(_closed(torso, 4))
    leg(*legs[1], near=True)
    # arms: one flung forward with an open hand, one swung back
    a1 = [j((0.135, -0.745)), j((0.255, -0.685)), j((0.33, -0.772)), j((0.362, -0.812))]
    a2 = ([j((-0.055, -0.75)), j((-0.175, -0.655)), j((-0.262, -0.71)), j((-0.29, -0.742))] if back_arm == 'up' else
          [j((-0.055, -0.75)), j((-0.16, -0.64)), j((-0.262, -0.585)), j((-0.30, -0.57))])
    for arm in (a2, a1):
        poly = _ribbon(arm, [0.058, 0.043, 0.032, 0.022], per=5)
        f.slip(poly)
        f.cut(poly[2:len(poly) // 2 - 6], w=1.0)
    _head(f, 0.115, -0.885, 0.058, beard=beard, hair='long', detail=False)
    for p in ([(-0.03, -0.745), (0.04, -0.722), (0.12, -0.745)], [(-0.04, -0.70), (0.0, -0.664), (0.05, -0.672)],
              [(0.06, -0.672), (0.10, -0.664), (0.142, -0.69)], [(0.0, -0.607), (0.05, -0.59), (0.095, -0.607)],
              [(0.052, -0.655), (0.05, -0.55)], [(0.095, -0.50), (0.06, -0.448)]):
        f.cut(p, w=1.0)


# horse, galloping, facing +x; unit = withers height; ground y = 0
_H_BODY = [(0.42, -0.70), (0.36, -0.52), (0.20, -0.45), (-0.05, -0.43), (-0.28, -0.46), (-0.40, -0.50), (-0.50, -0.56),
           (-0.60, -0.66), (-0.64, -0.76), (-0.56, -0.87), (-0.36, -0.885), (-0.15, -0.86), (0.10, -0.93),
           (0.23, -1.03), (0.34, -1.16), (0.43, -1.28), (0.53, -1.29), (0.62, -1.17), (0.70, -1.06), (0.722, -1.02),
           (0.70, -0.99), (0.655, -0.995), (0.60, -1.03), (0.545, -1.05), (0.49, -1.10), (0.47, -0.96), (0.45, -0.82)]
# flying gallop: near foreleg folded high, far foreleg reaching for the ground, hind legs driving back
_H_LEGS = {'nf': ([(0.33, -0.66), (0.37, -0.56), (0.55, -0.56), (0.565, -0.39), (0.62, -0.335)], [0.13, 0.10, 0.056, 0.042, 0.05]),
           'ff': ([(0.30, -0.66), (0.34, -0.54), (0.49, -0.37), (0.65, -0.13), (0.71, -0.07)], [0.12, 0.095, 0.052, 0.04, 0.048]),
           'nh': ([(-0.47, -0.67), (-0.50, -0.53), (-0.70, -0.38), (-0.86, -0.14), (-0.92, -0.065)], [0.22, 0.135, 0.06, 0.042, 0.05]),
           'fh': ([(-0.45, -0.65), (-0.46, -0.51), (-0.60, -0.37), (-0.62, -0.13), (-0.575, -0.06)], [0.20, 0.125, 0.056, 0.04, 0.048])}
_H_ROOTS = {'nf': (0.33, -0.66), 'ff': (0.30, -0.66), 'nh': (-0.47, -0.67), 'fh': (-0.45, -0.65)}
_H_TAIL = ([(-0.60, -0.84), (-0.75, -0.865), (-0.89, -0.78), (-0.99, -0.62)], [0.08, 0.072, 0.05, 0.02])


def _horse_tf(dx, dy, bend):
    """offset + neck bend about the withers (head raised for bend > 0)"""
    c = np.array([0.10, -0.93], np.float32)

    def tf(P):
        P = np.asarray(P, np.float32)
        w = smoothstep(0.12, 0.42, P[:, 0])
        d = P - c
        a = -bend * w
        s, k = np.sin(a), np.cos(a)
        Q = np.stack([c[0] + d[:, 0] * k - d[:, 1] * s, c[1] + d[:, 0] * s + d[:, 1] * k], 1)
        return Q + (dx, dy)
    return tf


def _horse(f, dx=0.0, dy=0.0, bend=0.0, legs=(0, 0, 0, 0), colour=None, outline=True):
    """one galloping chariot horse (unit = withers height, ground y = 0).
    colour: None (black), 'white' (a white trace horse in added white) or 'red_mane'. Returns the mouth point."""
    tf = _horse_tf(dx, dy, bend)
    far = [_ribbon(tf(_rot(_H_LEGS[k][0], np.array(_H_ROOTS[k]), a)), _H_LEGS[k][1], per=5)
           for k, a in (('ff', legs[1]), ('fh', legs[3]))]
    near = [_ribbon(tf(_rot(_H_LEGS[k][0], np.array(_H_ROOTS[k]), a)), _H_LEGS[k][1], per=5)
            for k, a in (('nf', legs[0]), ('nh', legs[2]))]
    tail = _ribbon(tf(_H_TAIL[0]), _H_TAIL[1], per=6)
    body = _closed(tf(_H_BODY), 5)
    ears = [tf([(0.405, -1.265), (0.412, -1.37), (0.447, -1.28)]), tf([(0.43, -1.28), (0.447, -1.395), (0.482, -1.29)])]
    allp = far + [tail, body] + ears + near
    for p in allp:
        f.slip(p)
    if colour == 'white':
        for p in allp:
            f.white(p)
    if outline:
        f.cut(body, closed=True)
    for p in near:
        n = len(p)
        f.cut(p[1:n // 2 - 4]); f.cut(p[n // 2 + 4:-1])
    f.cut(_circle(*tf([(0.535, -1.205)])[0], 0.022, 12), closed=True, w=1.0)       # eye and brow
    f.cut(tf([(0.505, -1.24), (0.535, -1.25), (0.565, -1.232)]), w=0.9)
    f.cut(tf([(0.48, -1.14), (0.52, -1.08), (0.585, -1.04)]))                     # jaw
    f.cut(tf([(0.718, -1.006), (0.662, -1.0)]), w=1.0)                            # mouth
    f.cut(tf([(0.683, -1.062), (0.70, -1.047), (0.69, -1.031)]), w=0.9)           # nostril
    f.cut(tf([(0.632, -1.105), (0.672, -1.03)]), w=1.0)                           # noseband
    f.cut(tf([(0.49, -1.235), (0.535, -1.15), (0.635, -1.095)]), w=1.0)           # cheekpiece
    inner = tf([(0.41, -1.23), (0.32, -1.11), (0.22, -0.99), (0.13, -0.905)])
    crest = tf([(0.10, -0.93), (0.23, -1.03), (0.34, -1.16), (0.43, -1.28)])
    f.cut(inner)                                                                    # mane edge
    for t in np.linspace(0.1, 0.9, 7):                                              # mane hair
        a = crest[0] + (crest[-1] - crest[0]) * t
        b = inner[-1] + (inner[0] - inner[-1]) * t
        f.cut([a + (b - a) * 0.15, b], w=0.8)
    f.cut(tf([(0.20, -0.94), (0.31, -0.80), (0.36, -0.64)]))                      # shoulder
    f.cut(tf([(-0.42, -0.86), (-0.36, -0.72), (-0.45, -0.56)]))                   # haunch
    f.cut(tf([(0.43, -0.78), (0.33, -0.90), (0.22, -0.96)]), w=1.0)               # breastband
    f.cut(tf([(-0.64, -0.82), (-0.78, -0.835), (-0.90, -0.75)]), w=0.9)           # tail hair
    f.cut(tf([(-0.10, -0.45), (0.12, -0.46)]), w=0.9)                             # girth
    if colour == 'red_mane':
        f.red(_closed(np.vstack([crest, inner]), 3))
    return tf([(0.70, -1.0)])[0]


def _charioteer(f, X, Y, s, lean=0.24):
    """standing charioteer in a long white chiton, leaning into the race. (X, Y): feet; s: height.
    returns (rein hand, goad hand)"""
    def T(P):
        P = np.asarray(P, np.float32)
        return np.stack([X + (P[:, 0] - lean * P[:, 1]) * s, Y + P[:, 1] * s], 1)
    robe = [(-0.06, -0.80), (0.05, -0.83), (0.11, -0.78), (0.12, -0.66), (0.10, -0.50), (0.11, -0.25), (0.12, 0.0),
            (-0.11, 0.0), (-0.10, -0.30), (-0.09, -0.55), (-0.10, -0.72)]
    farm = T([(0.0, -0.77), (0.12, -0.69), (0.27, -0.70)])
    f.slip(_ribbon(farm, [0.065 * s, 0.05 * s, 0.042 * s], per=4))
    rp = _closed(T(robe), 4)
    f.slip(rp)
    f.white(rp)
    hx, hy = T([(0.025, -0.905)])[0]
    _head(f, hx, hy, 0.072 * s, beard=False, hair='long', fillet=True)
    narm = T([(0.035, -0.765), (0.145, -0.655), (0.29, -0.66)])
    poly = _ribbon(narm, [0.07 * s, 0.055 * s, 0.045 * s], per=4)
    f.slip(poly)
    f.cut(poly[2:len(poly) // 2 - 3], w=1.0)
    for x in (-0.06, -0.02, 0.025, 0.07):
        f.cut(T([(x, -0.74), (x + 0.012, -0.45), (x - 0.004, -0.08)]), w=1.0)
    f.cut(T([(-0.095, -0.58), (0.11, -0.60)]), w=1.1)
    f.red(_ribbon(T([(-0.095, -0.58), (0.11, -0.60)]), 0.028 * s, smooth=False))
    f.cut(T([(-0.04, -0.79), (0.04, -0.765), (0.09, -0.79)]), w=1.0)
    return T([(0.30, -0.662)])[0], T([(0.27, -0.70)])[0]


class Zone:
    """a frieze between two heights of the pot. x = arc length (px) round the pot at this zone's radius,
    0 at the left handle; the visible front runs 0 .. C/2, the back C/2 .. C."""

    def __init__(self, pot, y0, y1):
        self.pot, self.y0, self.y1 = pot, float(y0), float(y1)
        self.r = float(pot.radius((y0 + y1) / 2))
        self.C = 2 * np.pi * self.r
        self.k = pot.R / self.r
        self.rng = np.random.default_rng(pot._seed())

    def tex(self, Q):
        Q = np.asarray(Q, np.float32)
        return np.stack([Q[:, 0] * self.k * self.pot.ls, Q[:, 1] * self.pot.ls], 1)

    def emit(self, fig, X, G=None, s=1.0, facing=1, jitter=0.22):
        """place a _Fig: local (lx, ly) -> (X + facing * lx * s, G + ly * s)"""
        G = self.y1 if G is None else G
        for op in fig.ops:
            P = op[2]
            Q = np.stack([X + facing * P[:, 0] * s, G + P[:, 1] * s], 1)
            if op[0] == 'poly':
                Q = Q + self.rng.normal(0, jitter, Q.shape).astype(np.float32)
                self.pot.ops.append((op[1], self.tex(Q), op[3]))
            else:
                _, layer, _, w, closed, taper = op
                if closed:
                    Q = np.vstack([Q, Q[:1]])
                Q = Q + self.rng.normal(0, 0.18, Q.shape).astype(np.float32)
                wid = np.full(len(Q), w, np.float32)
                if taper and len(Q) >= 2 and not closed:
                    wid[0] *= 0.35; wid[-1] *= 0.35
                self.pot.ops.append((layer, self.tex(_ribbon(Q, wid, per=4)), layer == 'slip'))

    # ------------------------------------------------------------ figures
    def runner(self, x, height=None, phase=0, beard=False, back_arm='up', ground=None):
        h = height or (self.y1 - self.y0) * 0.86
        f = _Fig()
        _runner(f, phase, 1.0, beard, back_arm, self.rng)
        self.emit(f, x, ground, h)

    def quadriga(self, x, hw=None, white_horse=None, red_manes=(3,), bends=(0.13, -0.05, 0.08, -0.09), ground=None):
        """a racing four-horse chariot heading +x. x = girth of the nearest horse; hw = withers height px.
        Drawn back to front: pole, charioteer, breastwork and rail, wheel, the team far -> near, reins, goad."""
        hw = hw or (self.y1 - self.y0) * 0.6
        f = _Fig()
        f.slip(_ribbon([(-1.05, -0.585), (-0.60, -0.62), (-0.20, -0.75), (0.10, -0.92)], 0.032, per=5))
        hand, hand2 = _charioteer(f, -1.33, -0.60, 0.90)
        cx0 = -1.04                                                     # front of the car
        f.slip([(cx0, -0.585), (cx0 - 0.01, -0.80), (cx0 - 0.07, -0.845), (cx0 - 0.27, -0.80), (cx0 - 0.30, -0.585)])
        f.slip(_ribbon([(cx0, -0.60), (cx0 + 0.015, -0.80), (cx0 - 0.06, -0.92), (cx0 - 0.20, -0.93),
                        (cx0 - 0.33, -0.84), (cx0 - 0.38, -0.66)], 0.034, per=4))
        f.slip([(cx0 - 0.46, -0.555), (cx0 + 0.02, -0.555), (cx0 + 0.02, -0.61), (cx0 - 0.46, -0.61)])
        f.cut([(cx0 - 0.02, -0.59), (cx0 - 0.28, -0.59)], w=1.0)
        f.cut([(cx0 - 0.03, -0.78), (cx0 - 0.09, -0.83), (cx0 - 0.25, -0.79)], w=1.0)
        f.red(_ribbon([(cx0 - 0.01, -0.66), (cx0 - 0.28, -0.66)], 0.04, smooth=False))
        wc = np.array([cx0 - 0.22, -0.345], np.float32)
        rim = _circle(wc[0], wc[1], 0.32, 40)
        f.slip(_ribbon(np.vstack([rim, rim[:2]]), 0.055, per=2, caps=False))
        for a in (0.35, 0.35 + np.pi / 2):
            d = np.array([np.cos(a), np.sin(a)], np.float32) * 0.31
            f.slip(_ribbon([wc - d, wc + d], 0.03, per=2))
        f.slip(_circle(wc[0], wc[1], 0.07, 14))
        f.cut(_circle(wc[0], wc[1], 0.30, 30), closed=True, w=1.0)
        f.cut(_circle(wc[0], wc[1], 0.045, 10), closed=True, w=0.9)
        mouths = []
        legsets = [(0.10, -0.08, -0.06, 0.07), (-0.06, 0.07, 0.05, -0.05), (0.05, -0.03, -0.03, 0.04), (0, 0, 0, 0)]
        for i in range(4):
            colour = 'white' if i == white_horse else ('red_mane' if i in red_manes else None)
            mouths.append(_horse(f, dx=(3 - i) * 0.06, dy=-(3 - i) * 0.022, bend=bends[i], legs=legsets[i],
                                 colour=colour, outline=i > 0))
        for i, m in enumerate(mouths):                                    # reins, painted with a fine brush
            p0 = hand + np.array([0, 0.006 * i], np.float32)
            mid = (p0 + m) / 2 + np.array([0, 0.05 + 0.015 * i], np.float32)
            f.line([p0, mid, m], w=1.1)
        f.line([hand2, hand2 + np.array([0.24, -0.32], np.float32)], w=1.5, taper=True)   # goad
        self.emit(f, x, ground, hw)

    def column(self, x, height=None, ground=None, red=True):
        """a Doric column (turning post / finish post)"""
        h = height or (self.y1 - self.y0) * 0.86
        f = _Fig()
        f.slip([(-0.11, -0.035), (0.11, -0.035), (0.11, 0.0), (-0.11, 0.0)])
        f.slip([(-0.075, -0.03), (0.075, -0.03), (0.062, -0.865), (-0.062, -0.865)])
        f.slip([(-0.062, -0.86), (-0.10, -0.895), (-0.105, -0.91), (0.105, -0.91), (0.10, -0.895), (0.062, -0.86)])
        f.slip([(-0.115, -0.905), (0.115, -0.905), (0.115, -0.955), (-0.115, -0.955)])
        for dx in (-0.038, 0.0, 0.038):
            f.cut([(dx * 1.1, -0.06), (dx, -0.84)], w=1.0)
        f.cut([(-0.065, -0.85), (0.065, -0.85)], w=1.0)
        f.cut([(-0.11, -0.906), (0.11, -0.906)], w=1.0)
        if red:
            f.red([(-0.112, -0.912), (0.112, -0.912), (0.112, -0.95), (-0.112, -0.95)])
        self.emit(f, x, ground, h)

    def judge(self, x, height=None, facing=-1, holds='wreath', ground=None):
        """a bearded official in a himation; holds a wreath (prize) or a forked rod (umpire)"""
        h = height or (self.y1 - self.y0) * 0.88
        f = _Fig()
        f.slip(_ribbon([(-0.15, -1.02), (-0.14, 0.0)], 0.022, per=2))                 # staff behind
        if holds == 'rod':
            f.slip(_ribbon([(-0.15, -1.02), (-0.19, -1.10)], 0.018, per=2))
            f.slip(_ribbon([(-0.15, -1.02), (-0.11, -1.10)], 0.018, per=2))
        cloak = [(0.0, -0.85), (0.10, -0.84), (0.125, -0.75), (0.135, -0.55), (0.12, -0.30), (0.15, -0.05),
                 (-0.11, -0.05), (-0.115, -0.30), (-0.10, -0.60), (-0.09, -0.78)]
        cp = _closed(cloak, 4)
        f.slip(cp)
        _foot(f, (0.10, -0.035), (0.20, -0.004))
        _foot(f, (-0.06, -0.035), (0.04, -0.004))
        _head(f, 0.06, -0.92, 0.058, beard=True, hair='long', fillet=False, red_beard=True, detail=h > 120)
        arm = _ribbon([(0.08, -0.70), (0.20, -0.665), (0.30, -0.70)], [0.055, 0.042, 0.034], per=4)
        f.slip(arm)
        f.cut(arm[2:len(arm) // 2 - 3], w=1.0)
        f.slip(_circle(-0.13, -0.62, 0.035, 10))                                         # hand on the staff
        for p in ([(0.11, -0.80), (-0.03, -0.55), (-0.10, -0.33)], [(0.13, -0.62), (0.02, -0.38), (-0.04, -0.12)],
                  [(0.12, -0.42), (0.08, -0.08)], [(-0.07, -0.30), (-0.08, -0.07)], [(0.02, -0.25), (0.02, -0.07)]):
            f.cut(p, w=1.0)
        f.red(_ribbon([(0.12, -0.80), (-0.02, -0.56), (-0.10, -0.36)], 0.045, per=4))
        f.red(_ribbon([(-0.11, -0.075), (0.15, -0.075)], 0.03, smooth=False))
        for cx, cy in ((0.05, -0.68), (-0.04, -0.45), (0.07, -0.30), (-0.02, -0.18)):
            for a in (0, 2.1, 4.2):
                f.white(_circle(cx + 0.013 * np.cos(a), cy + 0.013 * np.sin(a), 0.0075, 6))
        if holds == 'wreath':
            ring = np.vstack([_circle(0.35, -0.72, 0.055, 20), _circle(0.35, -0.72, 0.055, 20)[:1]])
            f.slip(_ribbon(ring, 0.012, per=2, caps=False))
            f.red(_ribbon(ring, 0.014, per=2, caps=False))
            for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
                c = np.array([0.35 + 0.055 * np.cos(a), -0.72 + 0.055 * np.sin(a)])
                d = np.array([np.cos(a + 0.9), np.sin(a + 0.9)]) * 0.016
                f.red(_ribbon([c - d, c + d], 0.012, per=2))
        self.emit(f, x, ground, h, facing)

    def tripod(self, x, height=None, ground=None):
        """a bronze tripod cauldron -- the prize"""
        h = height or (self.y1 - self.y0) * 0.62
        f = _Fig()
        for leg in ([(-0.19, -0.62), (-0.25, -0.30), (-0.30, -0.02)], [(0.19, -0.62), (0.25, -0.30), (0.30, -0.02)],
                    [(0.0, -0.58), (0.0, -0.30), (0.0, -0.02)]):
            f.slip(_ribbon(leg, [0.05, 0.04, 0.036], per=4))
            f.slip(_circle(leg[-1][0], -0.02, 0.035, 10, ry=0.022))
        a = np.linspace(0, np.pi, 18)
        bowl = np.vstack([np.stack([0.27 * np.cos(a), -0.70 + 0.19 * np.sin(a)], 1)[::-1], [(-0.27, -0.70)]])
        bowl = np.vstack([[(0.29, -0.76), (0.29, -0.70)], bowl[1:], [(-0.29, -0.70), (-0.29, -0.76)]])
        f.slip(bowl)
        for cx in (-0.14, 0.14):
            ring = np.vstack([_circle(cx, -0.90, 0.085, 24), _circle(cx, -0.90, 0.085, 24)[:1]])
            f.slip(_ribbon(ring, 0.03, per=2, caps=False))
            f.slip(_ribbon([(cx, -0.815), (cx * 1.2, -0.75)], 0.03, per=2))
        f.cut([(-0.28, -0.70), (0.28, -0.70)], w=1.0)
        f.cut([(-0.24, -0.62), (-0.12, -0.56), (0.0, -0.545), (0.12, -0.56), (0.24, -0.62)], w=1.0)
        zz = [(-0.20 + 0.04 * i, -0.665 + (0.025 if i % 2 else 0)) for i in range(11)]
        f.cut(zz, w=0.9)
        f.red([(-0.285, -0.758), (0.285, -0.758), (0.285, -0.72), (-0.285, -0.72)])
        self.emit(f, x, ground, h)

    def prize_table(self, x, height=None, ground=None):
        """a small table with the prize: a miniature amphora and an olive wreath"""
        h = height or (self.y1 - self.y0) * 0.86
        f = _Fig()
        f.slip([(-0.20, -0.36), (0.20, -0.36), (0.20, -0.33), (-0.20, -0.33)])
        for lx in (-0.16, 0.16):
            f.slip(_ribbon([(lx, -0.34), (lx * 1.06, -0.15), (lx * 1.1, -0.01)], [0.03, 0.022, 0.03], per=3))
        f.slip(_ribbon([(-0.17, -0.12), (0.17, -0.12)], 0.014, smooth=False))
        pro = np.array(SHAPES['neck_amphora']['profile'], np.float32)
        ah, ar = 0.36, 0.36 * 0.31
        side = np.stack([pro[:, 1] * ar, -0.36 - ah + pro[:, 0] * ah], 1)
        f.slip(np.vstack([side, side[::-1] * (-1, 1)]) + (-0.06, 0))
        for sgn in (-1, 1):
            hp = np.array(SHAPES['neck_amphora']['handle'], np.float32)
            f.slip(_ribbon(np.stack([-0.06 + sgn * hp[:, 0] * ar, -0.36 - ah + hp[:, 1] * ah], 1), 0.016, per=3))
        f.reserve([(-0.06 - 0.05, -0.36 - ah * 0.62), (-0.06 + 0.05, -0.36 - ah * 0.62),
                   (-0.06 + 0.05, -0.36 - ah * 0.40), (-0.06 - 0.05, -0.36 - ah * 0.40)])
        ring = np.vstack([_circle(0.12, -0.395, 0.045, 18), _circle(0.12, -0.395, 0.045, 18)[:1]])
        f.red(_ribbon(ring, 0.016, per=2, caps=False))
        f.slip(_ribbon(ring, 0.006, per=2, caps=False), occlude=False)
        self.emit(f, x, ground, h)

    def bird(self, x, y, size=30, facing=1, flap=0.0):
        """a swallow-like bird in flight (filler)"""
        f = _Fig()
        f.slip(_closed([(0.5, 0.0), (0.3, -0.07), (-0.1, -0.06), (-0.45, -0.02), (-0.1, 0.07), (0.3, 0.06)], 4))
        f.slip([(-0.38, 0.0), (-0.72, -0.18), (-0.55, 0.0), (-0.72, 0.16)])
        f.slip(_ribbon([(0.1, -0.03), (-0.05, -0.35 - flap), (-0.30, -0.55 - flap)], [0.18, 0.12, 0.02], per=4))
        f.slip(_ribbon([(0.15, 0.0), (0.05, -0.25 - flap * 0.6), (-0.12, -0.42 - flap)], [0.14, 0.09, 0.02], per=4))
        f.cut([(0.30, -0.02), (0.36, -0.01)], w=1.0)
        f.cut([(0.1, -0.02), (-0.05, -0.30 - flap)], w=0.9)
        f.red(_ribbon([(0.25, 0.04), (0.0, 0.05)], 0.05, smooth=False))
        self.emit(f, x, y, size, facing)

    def letters(self, text, x, y, size=12, vertical=False, retro=False, w=None):
        """archaic Greek letters painted with a fine brush, starting at (x, y)"""
        f = _Fig()
        pen = 0.0
        for ch in text:
            if ch == ' ':
                pen += 0.6
                continue
            g = GLYPHS.get(ch)
            if g is None:
                continue
            gw = 0.3 if ch == 'Ι' else 0.7
            for stroke in g:
                P = np.asarray(stroke, np.float32)
                if retro:
                    P = np.stack([gw - P[:, 0], P[:, 1]], 1)            # mirrored letters, written leftwards
                if vertical:
                    P = np.stack([P[:, 0], P[:, 1] + pen], 1)
                else:
                    P = np.stack([P[:, 0] + (-(pen + gw) if retro else pen), P[:, 1]], 1)
                f.line(P, w=w or max(1.1, size * 0.11), taper=False)
            pen += (1.25 if vertical else gw + 0.32)
        self.emit(f, x, y, size, 1, jitter=0.0)


class Pot:
    """a thrown pot: profile, handles and the unrolled painting surface (2x supersampled layers)"""

    def __init__(self, cx, foot, height, rmax=None, shape='neck_amphora', seed=0, eye=0.42, persp=0.11):
        sh = SHAPES[shape]
        self.shape = sh
        self.cx, self.H = float(cx), int(height)
        self.R = float(rmax or height * 0.315)
        self.top = float(foot) - self.H
        self.eye, self.persp = eye * self.H, persp
        P = np.array(sh['profile'], np.float32)
        d = spline(P, 14)
        self._py = np.maximum.accumulate(d[:, 0]) * self.H
        self._pr = np.clip(d[:, 1], 0.05, None) * self.R
        self.TW, self.TH, self.ls = int(round(2 * np.pi * self.R)), self.H, 2
        size = (self.TW * self.ls, self.TH * self.ls)
        self.layers = {k: Image.new('L', size, 0) for k in ('slip', 'red', 'white', 'inc')}
        self.draw = {k: ImageDraw.Draw(v) for k, v in self.layers.items()}
        self.ops, self._painted = [], 0
        self.rng = np.random.default_rng(seed)
        self.fired = self.aged = self.handles_painted = False
        self._geo = None
        self._noise = None
        self._agemaps = None
        self._ver, self._mat = 0, None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def radius(self, y):
        return np.interp(y, self._py, self._pr).astype(np.float32)

    def zone(self, y0, y1):
        return Zone(self, y0, y1)

    # ------------------------------------------------------------ raw drawing on the unrolled layers
    def _fill(self, layer, poly, val):
        W = self.TW * self.ls
        P = np.asarray(poly, np.float32)
        lo, hi = P[:, 0].min(), P[:, 0].max()
        offs = [0] + ([W] if lo < 0 else []) + ([-W] if hi > W else [])
        self._ver += 1
        for o in offs:
            self.draw[layer].polygon([(float(x) + o, float(y)) for x, y in P], fill=val)

    def _wob(self, amp, seed):
        """periodic wobble round the pot (a hand-held brush on the spinning wheel)"""
        r = np.random.default_rng(seed)
        u = np.linspace(0, 1, 361)
        out = np.zeros_like(u)
        for k in (1, 2, 3, 5):
            out += r.normal(0, amp / k) * np.sin(2 * np.pi * k * u + r.uniform(0, 6.3))
        return u, out

    def band(self, y0, y1, layer='slip'):
        """a band painted while the pot spins: level, with a small lap where the brush lifted off"""
        u, w0 = self._wob(0.35, self._seed())
        _, w1 = self._wob(0.35, self._seed())
        lap = np.exp(-((u - self.rng.uniform(0.55, 0.95)) / 0.012) ** 2) * 0.9
        x = u * self.TW * self.ls
        top = (y0 + w0 - lap * 0.4) * self.ls
        bot = (y1 + w1 + lap) * self.ls
        poly = np.vstack([np.stack([x, top], 1), np.stack([x[::-1], bot[::-1]], 1)])
        self._ver += 1
        self.draw[layer].polygon([(float(a), float(b)) for a, b in poly], fill=255)

    def paint_handles(self):
        self.handles_painted = True

    def tongues(self, y0, y1, n=None, red_every=2):
        """shoulder tongues hanging from the neck: black, every other one overpainted red"""
        z = Zone(self, y0, y1)
        n = n or int(round(z.C / 26))
        P = z.C / n
        h = y1 - y0
        f = _Fig()
        for i in range(n):
            x = i * P
            g = P * 0.09
            a = np.linspace(0, np.pi, 10)
            bottom = np.stack([x + P / 2 + (P / 2 - g) * np.cos(a), y1 - (P / 2 - g) * 0.9 + (P / 2 - g) * 0.9 * np.sin(a)], 1)
            poly = np.vstack([[(x + g, y0), (x + P - g, y0)], bottom])
            f.slip(poly)
            if red_every and i % red_every == 1:
                f.red(poly)
        z.emit(f, 0, 0, 1.0, jitter=0.15)

    def meander(self, y0, y1, n=None):
        """a running key: up, across, down, back, down and on to the next"""
        z = Zone(self, y0, y1)
        h = y1 - y0
        g = h / 4.6
        n = n or int(round(z.C / (g * 5)))
        P = z.C / n
        g = P / 5
        f = _Fig()
        key = [(0, 4), (0, 0), (3, 0), (3, 2), (1, 2), (1, 4), (5, 4)]
        for i in range(n):
            pts = [(i * P + gx * g, y0 + 0.3 * g + gy * g * (h - 0.6 * g) / (4 * g)) for gx, gy in key]
            for a, b in zip(pts[:-1], pts[1:]):
                a, b = np.array(a, np.float32), np.array(b, np.float32)
                d = (b - a) / (np.linalg.norm(b - a) + 1e-6) * g * 0.31          # square joins: overrun by w/2
                f.slip(_ribbon([a - d, b + d], g * 0.62, per=1, caps=False, smooth=False))
        z.emit(f, 0, 0, 1.0, jitter=0.12)

    def rays(self, y0, y1, n=None):
        """tall black rays rising from the foot"""
        z = Zone(self, y0, y1)
        n = n or int(round(z.C / 30))
        P = z.C / n
        f = _Fig()
        for i in range(n):
            x = i * P + P / 2
            f.slip([(x - P * 0.40, y1), (x - P * 0.05, y0 + 2), (x + P * 0.05, y0 + 2), (x + P * 0.40, y1)])
        z.emit(f, 0, 0, 1.0, jitter=0.2)

    def palmettes(self, y0, y1, n=5):
        """neck: upright palmettes sitting in the loops of a festoon, lotus flowers hanging at the joins"""
        z = Zone(self, y0, y1)
        P = z.C / n
        h = y1 - y0
        f = _Fig()
        for i in range(n):
            x = i * P + P * 0.25
            yb = y1 - h * 0.17
            xj, yj = x + P / 2, y0 + h * 0.20                                  # festoon join (lotus)
            for sgn in (-1, 1):                                                 # festoon arcs
                f.line([(x, yb + h * 0.075), (x + sgn * P * 0.22, yb + h * 0.035), (x + sgn * P * 0.40, y0 + h * 0.42),
                        (x + sgn * P * 0.5, yj)], w=1.7)
            for a in np.linspace(-0.98, 0.98, 9):                               # fan of petals
                L = h * (0.60 - 0.24 * (a / 0.98) ** 2)
                d = np.array([np.sin(a), -np.cos(a)])
                base = np.array([x, yb]) + d * h * 0.12
                f.slip(_ribbon([base, base + d * L * 0.62, base + d * L], [h * 0.018, h * 0.07, h * 0.062], per=4))
            heart = np.vstack([_arc(x, yb, h * 0.115, np.pi, 2 * np.pi, 14), [(x + h * 0.115, yb + h * 0.05),
                                                                            (x - h * 0.115, yb + h * 0.05)]])
            f.slip(heart)
            f.red(heart)
            f.cut(_arc(x, yb, h * 0.115, np.pi, 2 * np.pi, 12), w=1.0)
            # hanging lotus: calyx, a long central petal and two petals curling outwards
            f.slip([(xj - h * 0.055, y0 + h * 0.06), (xj + h * 0.055, y0 + h * 0.06), (xj + h * 0.045, yj + h * 0.06),
                    (xj - h * 0.045, yj + h * 0.06)])
            f.slip(_ribbon([(xj, yj + h * 0.04), (xj, yj + h * 0.30), (xj, yj + h * 0.47)], [h * 0.07, h * 0.075, h * 0.012], per=4))
            for sgn in (-1, 1):
                f.slip(_ribbon([(xj + sgn * h * 0.03, yj + h * 0.05), (xj + sgn * h * 0.14, yj + h * 0.20),
                                (xj + sgn * h * 0.24, yj + h * 0.28), (xj + sgn * h * 0.30, yj + h * 0.25)],
                               [h * 0.055, h * 0.05, h * 0.03, h * 0.012], per=4))
            f.red([(xj - h * 0.05, y0 + h * 0.10), (xj + h * 0.05, y0 + h * 0.10), (xj + h * 0.047, yj),
                   (xj - h * 0.047, yj)])
            f.cut([(xj - h * 0.05, yj + h * 0.02), (xj + h * 0.05, yj + h * 0.02)], w=1.0)
        z.emit(f, 0, 0, 1.0, jitter=0.12)

    # ------------------------------------------------------------ the three painting passes
    def paint(self):
        """brush on the slip for every figure declared since the last call"""
        for layer, poly, occ in self.ops[self._painted:]:
            if layer == 'slip':
                self._fill('slip', poly, 255)
        self._painted = len(self.ops)

    def incise(self):
        """scratch the details through the slip (replayed in depth order: nearer black hides farther lines)"""
        self.draw['inc'].rectangle([0, 0, self.TW * self.ls, self.TH * self.ls], fill=0)
        for layer, poly, occ in self.ops:
            if layer == 'slip' and occ:
                self._fill('inc', poly, 0)
            elif layer == 'inc':
                self._fill('inc', poly, 255)

    def add_colour(self):
        """added red and white over the black, last, in depth order"""
        for k in ('red', 'white'):
            self.draw[k].rectangle([0, 0, self.TW * self.ls, self.TH * self.ls], fill=0)
        for layer, poly, occ in self.ops:
            if layer == 'slip' and occ:
                self._fill('red', poly, 0); self._fill('white', poly, 0)
            elif layer in ('red', 'white'):
                self._fill(layer, poly, 255)

    def fire(self):
        self.fired = True

    def age(self, mend=None, misfire=None, chips=7, roots=14, seed=None):
        """mend: (u, v, rx, ry) restored loss in unrolled px; misfire: (u, v, r)"""
        self.aged = True
        self._age = dict(mend=mend, misfire=misfire, chips=chips, roots=roots, seed=seed or self._seed())
        self._agemaps = None

    # ------------------------------------------------------------ materials on the unrolled surface (1x)
    def _layer(self, k):
        return np.asarray(self.layers[k].resize((self.TW, self.TH), Image.BOX), np.float32) / 255

    def _noises(self):
        if self._noise is None:
            TH, TW = self.TH, self.TW
            r = np.random.default_rng(self._seed())
            streak = np.asarray(Image.fromarray(r.random((TH // 2, TW // 24)).astype(np.float32)).resize((TW, TH), Image.BICUBIC))
            self._noise = dict(lo=noise2d(TH, TW, 160, 3, self._seed()), mid=noise2d(TH, TW, 30, 3, self._seed()),
                               fine=r.random((TH, TW)).astype(np.float32), streak=np.clip(streak, 0, 1))
        return self._noise

    def _age_maps(self):
        if self._agemaps is not None:
            return self._agemaps
        TH, TW = self.TH, self.TW
        a = self._age
        r = np.random.default_rng(a['seed'])
        N = self._noises()
        m = {}
        m['flake'] = smoothstep(0.60, 0.66, noise2d(TH, TW, 5, 3, a['seed'] + 1)) * smoothstep(0.35, 0.6, noise2d(TH, TW, 40, 2, a['seed'] + 4))
        V = np.arange(TH, dtype=np.float32)[:, None] / TH
        cn = noise2d(TH, TW, 14, 3, a['seed'] + 2) * 0.6 + noise2d(TH, TW, 60, 2, a['seed'] + 3) * 0.4
        m['crust'] = smoothstep(0.70, 0.84, cn) * (0.08 + 0.92 * smoothstep(0.55, 1.0, V)) * 0.7
        m['crust'] = np.maximum(m['crust'], (N['fine'] > 0.999).astype(np.float32) * 0.45 * V)
        im = Image.new('L', (TW, TH), 0)
        d = ImageDraw.Draw(im)
        for i in range(a['roots']):                                     # root marks: thin wandering lines
            x, y = r.uniform(0, TW), r.uniform(TH * 0.3, TH * 0.95)
            ang = r.uniform(0, 2 * np.pi)
            pts = []
            for s in range(int(r.uniform(30, 90))):
                ang += r.normal(0, 0.35)
                x += np.cos(ang) * 3; y += np.sin(ang) * 3
                pts.append((x % TW, y))
            for p0, p1 in zip(pts[:-1], pts[1:]):
                if abs(p0[0] - p1[0]) < 10:
                    d.line([p0, p1], fill=int(r.uniform(35, 75)), width=1)
        m['roots'] = np.asarray(im, np.float32) / 255
        im = Image.new('L', (TW * 2, TH * 2), 0)                         # chips on the lip and the foot
        d = ImageDraw.Draw(im)
        for i in range(a['chips']):
            u = r.uniform(0, TW)
            v = r.choice([r.uniform(0, 3), r.uniform(TH - 4, TH)]) if i > 1 else (1.0 if i == 0 else TH - 1.5)
            rr = r.uniform(3.0, 7.0)
            ang = np.linspace(0, 2 * np.pi, 24, endpoint=False)
            k = 1 + 0.35 * fbm1d(24, 5, 2, int(r.integers(1 << 30)))
            pts = [((u + np.cos(t) * rr * q * 1.7) * 2, (v + np.sin(t) * rr * q) * 2) for t, q in zip(ang, k)]
            d.polygon(pts, fill=255)
        m['chip'] = np.asarray(im.resize((TW, TH), Image.BOX), np.float32) / 255
        m['fill'] = np.zeros((TH, TW), np.float32)
        m['crack'] = np.zeros((TH, TW), np.float32)
        if a['mend']:
            u, v, rx, ry = a['mend']
            ang = np.linspace(0, 2 * np.pi, 60, endpoint=False)
            k = 1 + 0.42 * fbm1d(60, 10, 4, a['seed'] + 5)
            pts = [((u + np.cos(t) * rx * q) * 2, (v + np.sin(t) * ry * q) * 2) for t, q in zip(ang, k)]
            im = Image.new('L', (TW * 2, TH * 2), 0)
            ImageDraw.Draw(im).polygon(pts, fill=255)
            m['fill'] = np.asarray(im.resize((TW, TH), Image.BOX), np.float32) / 255
            im = Image.new('L', (TW * 2, TH * 2), 0)
            d = ImageDraw.Draw(im)
            d.line(pts + pts[:1], fill=255, width=2)
            for j in range(4):                                         # glued cracks running off the loss
                t = r.uniform(0, 2 * np.pi)
                x, y = u + np.cos(t) * rx, v + np.sin(t) * ry
                ang2 = t
                seg = [(x * 2, y * 2)]
                for s in range(int(r.uniform(14, 34))):
                    ang2 += r.normal(0, 0.28)
                    x += np.cos(ang2) * 5; y += np.sin(ang2) * 5
                    seg.append((x * 2, y * 2))
                d.line(seg, fill=255, width=2)
            m['crack'] = np.asarray(im.resize((TW, TH), Image.BOX), np.float32) / 255
        m['misfire'] = np.zeros((TH, TW), np.float32)
        if a['misfire']:
            u, v, rr = a['misfire']
            U, Vv = np.meshgrid(np.arange(TW, dtype=np.float32), np.arange(TH, dtype=np.float32))
            du = (U - u + TW / 2) % TW - TW / 2
            m['misfire'] = np.exp(-(du ** 2 / (2 * (rr * 1.6) ** 2) + (Vv - v) ** 2 / (2 * rr ** 2))) * \
                (0.6 + 0.4 * N['mid'])
            del U, Vv, du
        self._agemaps = m
        return m

    def materials(self):
        """-> albedo (TH, TW, 3) sRGB, gloss (TH, TW), satin (0..1) for the current state of the pot"""
        key = (self._ver, self.fired, self.aged)
        if self._mat is None or self._mat[0] != key:
            self._mat = (key, self._materials())
        return self._mat[1]

    def _materials(self):
        s, rd, wh, inc = (self._layer(k) for k in ('slip', 'red', 'white', 'inc'))
        N = self._noises()
        se = s * (1 - inc)
        fired = self.fired
        clay = _hex(COLOURS['clay' if fired else 'clay_raw'])
        alb = np.empty((self.TH, self.TW, 3), np.float32)
        var = (0.955 + 0.07 * N['lo'] + 0.03 * N['mid'] + 0.025 * (N['fine'] - 0.5))
        alb[:] = clay * var[..., None]
        if fired:
            thick = np.clip(0.78 + 0.45 * (N['mid'] - 0.5) + 0.08 * (N['streak'] - 0.5), 0, 1)
            thick *= smoothstep(0.25, 0.95, blur(s, 1.2))
            black = _hex(COLOURS['thin']) * (1 - thick[..., None] ** 0.5) + _hex(COLOURS['black']) * thick[..., None] ** 0.5
        else:
            black = _hex(COLOURS['slip_raw']) * (0.94 + 0.04 * N['streak'] + 0.08 * N['mid'])[..., None]
        alb = alb * (1 - se[..., None]) + black * se[..., None]
        gloss = (se * (0.82 + 0.18 * N['streak'])) if fired else np.zeros_like(se)
        if self.aged:
            A = self._age_maps()
            wh = wh * (1 - 0.8 * A['flake'])
            rd = rd * (0.78 + 0.22 * N['mid'])
            ghost = (self._layer('white') - wh) * se
            alb = alb * (1 - 0.35 * ghost[..., None]) + _hex('#3b3633') * 0.35 * ghost[..., None]
            gloss = gloss * (1 - 0.8 * ghost)
        red = _hex(COLOURS['red' if fired else 'red_raw'])
        white = _hex(COLOURS['white' if fired else 'white_raw'])
        rv = (rd * (1 - 0.55 * inc))[..., None]
        wv = (wh * (1 - 0.35 * inc))[..., None]
        alb = alb * (1 - rv) + red * (0.92 + 0.12 * N['mid'])[..., None] * rv
        alb = alb * (1 - wv) + white * (0.93 + 0.08 * N['mid'])[..., None] * wv
        alb = alb * (1 - (wh * inc * 0.3)[..., None])
        gloss = gloss * (1 - np.clip(rd + wh, 0, 1) * 0.92)
        if self.aged:
            A = self._age_maps()
            mf = (A['misfire'] * se)[..., None]
            alb = alb * (1 - 0.6 * mf) + _hex(COLOURS['misfire']) * 0.6 * mf
            fl = A['fill'][..., None]
            dark = se[..., None]
            toned = _hex(COLOURS['fill_clay']) * (1 - dark) + _hex(COLOURS['fill_black']) * dark
            toned = toned * (1 - rv * 0.7) + _hex('#8b5a52') * rv * 0.7
            alb = alb * (1 - fl) + toned * (0.97 + 0.04 * N['fine'][..., None]) * fl
            gloss = gloss * (1 - A['fill'] * 0.9)
            ck = A['crack'][..., None]
            alb = alb * (1 - 0.75 * ck) + (_hex('#2a1810') * (1 - dark) + _hex('#6a5a50') * dark) * 0.75 * ck
            ch = A['chip'][..., None]
            alb = alb * (1 - ch) + _hex(COLOURS['fabric']) * (0.92 + 0.12 * N['fine'][..., None]) * ch
            gloss = gloss * (1 - A['chip'])
            cr = np.clip(A['crust'] * 0.5 + A['roots'] * 0.5, 0, 1)
            alb = alb * (1 - cr[..., None]) + _hex(COLOURS['crust']) * cr[..., None]
            gloss = gloss * (1 - cr) * (0.9 + 0.1 * N['lo'])
        return alb, gloss, (0.55 if fired else 0.12)


class BlackFigure:
    def __init__(self, W=1920, H=1080, seed=0):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.pots, self.overlays, self.stages = [], [], []
        self._base = None
        self.img = np.zeros((H, W, 3), np.float32)
        self.museum()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ the room
    def museum(self, wall='#1c2427', plinth='#cbc2b4', spot=None, plinth_x=None):
        self._room = dict(wall=wall, plinth=plinth, spot=spot, plinth_x=plinth_x)
        self._base = None

    def throw(self, cx, foot, height, rmax=None, shape='neck_amphora', eye=0.42):
        """throw a pot standing on the plinth at screen (cx, foot)"""
        p = Pot(cx, foot, height, rmax, shape, self._seed(), eye=eye)
        self.pots.append(p)
        self._base = None
        return p

    def _build_base(self):
        H, W = self.H, self.W
        rm = self._room
        Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
        p = self.pots[0] if self.pots else None
        sx, sy = rm['spot'] or ((p.cx, p.top + p.H * 0.42) if p else (W / 2, H / 2))
        spot = np.exp(-((X - sx) ** 2 / (2 * 560 ** 2) + (Y - sy) ** 2 / (2 * 470 ** 2)))
        wall = _hex(rm['wall'])
        img = wall * (0.62 + 0.62 * spot[..., None]) * (1 + 0.05 * (noise2d(H, W, 220, 3, self._seed()) - 0.5))[..., None]
        img += np.array([0.035, 0.022, 0.008], np.float32) * spot[..., None] ** 2
        img *= (1 + 0.03 * (noise2d(H, W, 3, 2, self._seed()) - 0.5))[..., None]
        if p:
            foot = p.top + p.H
            rf = float(p.radius(p.H - 1))
            dfront = p.persp * (p.H - p.eye) * rf / p.R
            x0, x1 = rm['plinth_x'] or (p.cx - 330, p.cx + 330)
            t0, t1 = foot - 38, foot + dfront + 34
            pl = _hex(rm['plinth'])
            top = (Y >= t0) & (Y < t1) & (X >= x0) & (X < x1)
            front = (Y >= t1) & (X >= x0) & (X < x1)
            tshade = (0.58 + 0.30 * smoothstep(t0, t1, Y)) * (0.80 + 0.26 * spot)
            fshade = (0.55 - 0.18 * smoothstep(t1, H, Y)) * (0.8 + 0.3 * spot)
            grain = 1 + 0.035 * (noise2d(H, W, 2.5, 2, self._seed()) - 0.5)
            img = np.where(top[..., None], pl * (tshade * grain)[..., None], img)
            img = np.where(front[..., None], pl * (fshade * grain)[..., None], img)
            edge = np.exp(-((Y - t1) / 1.2) ** 2) * ((X >= x0) & (X < x1))
            img += 0.08 * edge[..., None]
            # contact shadow + a soft cast shadow of the pot on the plinth top
            cs = np.exp(-(((X - p.cx) / (rf * 1.08)) ** 2 + ((Y - foot - dfront * 0.35) / (dfront * 1.2 + 8)) ** 2) ** 2)
            cs = blur(np.clip(cs, 0, 1), 4)
            ss = blur(np.exp(-(((X - p.cx - 95) / 300) ** 2 + ((Y - foot - 6) / 22) ** 2)), 6)
            m = top | front
            img *= (1 - (0.75 * cs + 0.38 * ss) * m)[..., None]
        vig = 1 - 0.38 * smoothstep(0.55, 1.25, np.hypot((X - W / 2) / (W / 2), (Y - H / 2) / (H / 2)))
        img *= vig[..., None]
        self._base = np.clip(img, 0, 1)

    # ------------------------------------------------------------ the photograph of the pot
    def _geometry(self, p, ss=2):
        x0, x1 = int(p.cx - p.R * 1.02) - 4, int(p.cx + p.R * 1.02) + 4
        y0, y1 = int(p.top - 30), int(p.top + p.H + 40)
        Hs, Ws = (y1 - y0) * ss, (x1 - x0) * ss
        Ys = ((np.arange(Hs, dtype=np.float32) + 0.5) / ss + y0 - p.top)[:, None]
        Xr = ((np.arange(Ws, dtype=np.float32) + 0.5) / ss + x0 - p.cx)[None, :]
        c, ye = p.persp, p.eye
        yl = np.broadcast_to(Ys, (Hs, Ws)).copy()
        for _ in range(5):
            r = p.radius(yl)
            z = np.sqrt(np.clip(r * r - Xr * Xr, 0, None))
            yl = (Ys + c * ye * z / p.R) / (1 + c * z / p.R)
        r = p.radius(yl)
        inside = (r * r - Xr * Xr > 0) & (yl >= 0) & (yl <= p.H)
        idx = np.flatnonzero(inside)
        yv = yl.ravel()[idx]
        rv = r.ravel()[idx]
        xv = Xr[0, idx % Ws]
        del yl, r, z
        sn = np.clip(xv / rv, -1, 1)
        th = np.arcsin(sn)
        cs = np.cos(th)
        dr = (p.radius(yv + 0.75) - p.radius(yv - 0.75)) / 1.5
        dr = dr + 0.009 * np.sin(2 * np.pi * yv / 8.5 + 2.0 * fbm1d(4096, 300, 3, 7)[np.clip(yv * 3.5, 0, 4095).astype(int)])
        n = np.stack([sn, -dr, cs], 1)
        n /= np.linalg.norm(n, axis=1, keepdims=True)
        g = dict(x0=x0, y0=y0, Hs=Hs, Ws=Ws, ss=ss, idx=idx, tu=(th + np.pi / 2) / (2 * np.pi) * p.TW, tv=yv,
                 cmp=1 / np.maximum(cs, 0.05))
        g.update(self._shade(n))
        # ambient occlusion under the overhanging lip
        occ = np.zeros_like(yv)
        for dy in (3, 6, 10, 16, 24):
            occ = np.maximum(occ, (p.radius(yv - dy) - rv) / (dy + 6))
        g['D'] *= 1 - 0.55 * np.clip(occ, 0, 1)
        return g

    def _shade(self, n):
        """lighting terms that depend only on the surface normal"""
        nx, ny, nz = n[:, 0], n[:, 1], n[:, 2]
        Lk = np.array([-0.60, -0.48, 0.64]); Lk /= np.linalg.norm(Lk)
        Lf = np.array([0.75, -0.15, 0.64]); Lf /= np.linalg.norm(Lf)
        D = 0.95 * np.clip(nx * Lk[0] + ny * Lk[1] + nz * Lk[2], 0, 1) + 0.22 * np.clip(nx * Lf[0] + ny * Lf[1] + nz * Lf[2], 0, 1) \
            + 0.10 + 0.06 * np.clip(-ny, 0, 1)
        Rx, Ry, Rz = 2 * nz * nx, 2 * nz * ny, 2 * nz * nz - 1
        az = np.arctan2(Rx, Rz)
        el = np.arcsin(np.clip(-Ry, -1, 1))

        def box(a0, a1, e0, e1, s):
            return (smoothstep(a0 - s, a0 + s, az) * (1 - smoothstep(a1 - s, a1 + s, az)) *
                    smoothstep(e0 - s, e0 + s, el) * (1 - smoothstep(e1 - s, e1 + s, el)))

        def env(s):
            return (0.03 + 6.0 * box(-0.90, -0.76, -0.45, 1.0, s) + 0.5 * box(-1.3, -0.3, -0.2, 0.9, s * 3) + 3.0 * box(0.98, 1.08, -0.25, 0.80, s * 0.6)
                    + 0.25 * smoothstep(0.75, 1.35, el) + 0.30 * smoothstep(-0.12, -0.45, el))
        F = 0.045 + 0.955 * (1 - np.clip(nz, 0, 1)) ** 5
        return dict(D=D.astype(np.float32), Es=env(0.035).astype(np.float32), Eb=env(0.45).astype(np.float32),
                    F=F.astype(np.float32))

    def _handles(self, p, ss=2):
        """the two round handles as glazed tubes standing at the silhouette"""
        hp = np.array(p.shape['handle'], np.float32)
        rt = p.shape['handle_w'] * p.R / 2
        out = []
        for sgn in (-1, 1):
            C = spline(np.stack([p.cx + sgn * hp[:, 0] * p.R, p.top + hp[:, 1] * p.H], 1), 10)
            x0, x1 = int(C[:, 0].min() - rt - 3), int(C[:, 0].max() + rt + 3)
            y0, y1 = int(C[:, 1].min() - rt - 3), int(C[:, 1].max() + rt + 3)
            Hs, Ws = (y1 - y0) * ss, (x1 - x0) * ss
            Y, X = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
            Y = Y / ss + y0 + 0.5 / ss; X = X / ss + x0 + 0.5 / ss
            best = np.full(Y.shape, 1e9, np.float32)
            vx = np.zeros_like(Y); vy = np.zeros_like(Y); tpar = np.zeros_like(Y)
            for i in range(len(C) - 1):
                a, b = C[i], C[i + 1]
                ab = b - a
                t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / (ab @ ab + 1e-9), 0, 1)
                dx, dy = X - (a[0] + ab[0] * t), Y - (a[1] + ab[1] * t)
                dd = dx * dx + dy * dy
                m = dd < best
                best = np.where(m, dd, best); vx = np.where(m, dx, vx); vy = np.where(m, dy, vy)
                tpar = np.where(m, (i + t) / (len(C) - 1), tpar)
            d = np.sqrt(best)
            a = np.clip(d / rt, 0, 1)
            inside = d < rt
            rr = np.maximum(d, 1e-6)
            n = np.stack([vx / rr * a, vy / rr * a, np.sqrt(1 - a * a)], -1)[inside]
            out.append(dict(x0=x0, y0=y0, Hs=Hs, Ws=Ws, ss=ss, idx=np.flatnonzero(inside), **self._shade(n)))
        return out

    def _composite(self, img, g, col):
        """col: linear colour per inside sample -> anti-aliased paste"""
        ss, Hs, Ws = g['ss'], g['Hs'], g['Ws']
        buf = np.zeros((Hs * Ws, 3), np.float32)
        buf[g['idx']] = col
        al = np.zeros(Hs * Ws, np.float32)
        al[g['idx']] = 1
        h, w = Hs // ss, Ws // ss
        buf = buf.reshape(h, ss, w, ss, 3).mean((1, 3))
        al = al.reshape(h, ss, w, ss).mean((1, 3))
        c = _srgb(buf / np.maximum(al, 1e-6)[..., None])
        y0, x0 = g['y0'], g['x0']
        ya, xa = max(0, -y0), max(0, -x0)
        yb, xb = min(h, self.H - y0), min(w, self.W - x0)
        sl = img[y0 + ya:y0 + yb, x0 + xa:x0 + xb]
        a = al[ya:yb, xa:xb, None]
        img[y0 + ya:y0 + yb, x0 + xa:x0 + xb] = sl * (1 - a) + c[ya:yb, xa:xb] * a

    def _render_pot(self, img, p):
        if p._geo is None:
            p._geo = (self._geometry(p), self._handles(p))
        g, hs = p._geo
        alb, gloss, satin = p.materials()
        alb_l = _lin(alb)
        soft_l = blur_h(alb_l, 2.0)                      # pre-filtered copy for the foreshortened flanks
        n = len(g['idx'])
        col = np.empty((n, 3), np.float32)
        for c0 in range(0, n, 300000):                    # in chunks: keeps the temporaries small
            sl = slice(c0, min(n, c0 + 300000))
            tu, tv = g['tu'][sl], g['tv'][sl]
            wm = smoothstep(1.8, 4.5, g['cmp'][sl])[:, None]
            a = _bilinear(alb_l, tu, tv) * (1 - wm) + _bilinear(soft_l, tu, tv) * wm
            gl = _bilinear(gloss, tu, tv)
            F, D = g['F'][sl], g['D'][sl]
            col[sl] = a * D[:, None] + (gl * F * g['Es'][sl])[:, None] + ((1 - gl) * satin * 0.6 * F * g['Eb'][sl])[:, None]
        del alb_l, soft_l
        self._composite(img, g, col)
        for h in hs:
            if p.handles_painted:
                ab = _lin(_hex(COLOURS['black'] if p.fired else COLOURS['slip_raw']))
                gh = 0.9 if p.fired else 0.0
            else:
                ab = _lin(_hex(COLOURS['clay'] if p.fired else COLOURS['clay_raw']))
                gh = 0.0
            col = ab[None, :] * h['D'][:, None] + (gh * h['F'] * h['Es'])[:, None] + \
                ((1 - gh) * satin * 0.6 * h['F'] * h['Eb'])[:, None]
            self._composite(img, h, col)

    # ------------------------------------------------------------ the rollout panel
    def panel(self, box, title='', subtitle='', english='', greek='', board='#232b2f'):
        """a dark display board on the wall with a title block"""
        def draw(img, box=box):
            x0, y0, x1, y1 = box
            sh = np.zeros((self.H, self.W), np.float32)
            sh[y0 + 8:y1 + 8, x0 + 6:x1 + 6] = 1
            img *= (1 - 0.45 * blur(sh, 9))[..., None]
            b = _hex(board)
            img[y0:y1, x0:x1] = b * (1 + 0.03 * (noise2d(y1 - y0, x1 - x0, 3, 2, 5) - 0.5))[..., None]
            img[y0:y0 + 1, x0:x1] += 0.05; img[y0:y1, x0:x0 + 1] += 0.04
            cream = _hex('#eadcc0')
            if title:
                self._text(img, title, (x0 + 40, y0 + 70), 'songti', 50, cream)
            if greek:
                self._text(img, greek, (x1 - 40, y0 + 64), 'serif', 17, _hex('#c98a5e'), anchor='rs', spacing=3)
            if subtitle:
                self._text(img, subtitle, (x0 + 42, y0 + 106), 'songti', 21, cream * 0.88)
            if english:
                self._text(img, english, (x0 + 42, y0 + 132), 'serif', 16, cream * 0.62)
            img[y0 + 148:y0 + 149, x0 + 40:x1 - 40] = cream * 0.35
        self.overlays.append(draw)

    def _text(self, img, s, xy, font, size, col, anchor='ls', spacing=0.0):
        if font == 'songti':
            path = '/System/Library/Fonts/Supplemental/Songti.ttc'
            from PIL import ImageFont
            f = ImageFont.truetype(path, size, index=6) if os.path.exists(path) else load_font('cjk', size)
        else:
            f = load_font(font, size)
        m = text_mask(self.H, self.W, s, f, xy, anchor=anchor, spacing=spacing)
        img[:] = img * (1 - m[..., None]) + np.asarray(col, np.float32) * m[..., None]

    def rollout(self, pot, bands, x, y, scale=0.86, half=0, caption='', ticks=('0°', '180°')):
        """the friezes between the y's in `bands` unrolled flat (one row per band, each at its own
        circumference), stacked and centred under each other. half: 0 = front (A), 1 = back (B)."""
        def draw(img):
            al, gl, _ = pot.materials()
            yy = y
            widths = []
            for (b0, b1) in bands:
                z = Zone(pot, b0, b1)
                w, h = int(z.C / 2 * scale), int(round((b1 - b0) * scale))
                widths.append(w)
                jj, ii = np.meshgrid(np.arange(w, dtype=np.float32) + 0.5, np.arange(h, dtype=np.float32) + 0.5)
                u = (jj / scale + half * z.C / 2) * z.k
                v = b0 + ii / scale
                col = _bilinear(al, u.ravel(), v.ravel()).reshape(h, w, 3)
                gs = _bilinear(gl, u.ravel(), v.ravel()).reshape(h, w)
                col = col * 0.97 + 0.05 * gs[..., None] * (0.8 + 0.4 * jj / w)[..., None]
                x0 = int(x - w / 2)
                img[yy:yy + h, x0:x0 + w] = np.clip(col, 0, 1)
                yy += h
            wmax = max(widths)
            x0 = int(x - wmax / 2)
            sh = np.zeros((self.H, self.W), np.float32)
            yy = y
            for w, (b0, b1) in zip(widths, bands):
                h = int(round((b1 - b0) * scale))
                sh[yy:yy + h, int(x - w / 2):int(x - w / 2) + w] = 1
                yy += h
            edge = np.clip(blur(sh, 2.5) - sh, 0, 1)
            img *= (1 - 0.6 * edge)[..., None]
            cream = _hex('#eadcc0')
            if caption:
                self._text(img, caption, (x0, y - 12), 'songti', 18, cream * 0.85)
            if ticks:
                self._text(img, ticks[0], (x0, yy + 22), 'serif', 14, cream * 0.6)
                self._text(img, ticks[1], (x0 + wmax, yy + 22), 'serif', 14, cream * 0.6, anchor='rs')
                img[yy + 4:yy + 9, x0:x0 + 1] = cream * 0.5
                img[yy + 4:yy + 9, x0 + wmax - 1:x0 + wmax] = cream * 0.5
        self.overlays.append(draw)

    def legend(self, x, y, items):
        """technique swatches: [(label, kind)] with kind in clay / black / incision / red / white"""
        def draw(img):
            cream = _hex('#eadcc0')
            xx = x
            for label, kind in items:
                sw = np.zeros((18, 30, 3), np.float32)
                base = _hex(COLOURS['clay']) if kind == 'clay' else _hex(COLOURS['black'])
                sw[:] = base
                if kind == 'incision':
                    for k in range(30):
                        yk = int(9 + 4 * np.sin(k / 4.0))
                        sw[yk, k] = _hex(COLOURS['clay'])
                if kind == 'red':
                    sw[:] = _hex(COLOURS['red'])
                if kind == 'white':
                    sw[:] = _hex(COLOURS['white'])
                if kind == 'black':
                    sw[3:6, :] += 0.18
                img[y - 15:y + 3, xx:xx + 30] = sw
                self._text(img, label, (xx + 40, y), 'songti', 17, cream * 0.8)
                f = load_font('cjk', 17)
                from PIL import ImageFont
                path = '/System/Library/Fonts/Supplemental/Songti.ttc'
                if os.path.exists(path):
                    f = ImageFont.truetype(path, 17, index=6)
                xx += 40 + int(f.getlength(label)) + 36
        self.overlays.append(draw)

    # ------------------------------------------------------------ output
    def render(self):
        if self._base is None:
            self._build_base()
        img = self._base.copy()
        for p in self.pots:
            self._render_pot(img, p)
        for o in self.overlays:
            o(img)
        self.img = img
        return img

    def stage(self, name):
        self.stages.append((name, self.image(self.render())))

    def image(self, img=None):
        img = self.render() if img is None else img
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def save(self, path, stages_dir=None, quality=88):
        img = self.image()
        if str(path).lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img


def blur_h(a, r):
    """horizontal box blur (wrapping) -- the far side of the pot is seen foreshortened"""
    k = int(max(1, r))
    out = a.copy()
    for d in range(1, k + 1):
        out += np.roll(a, d, axis=1) + np.roll(a, -d, axis=1)
    return out / (2 * k + 1)
